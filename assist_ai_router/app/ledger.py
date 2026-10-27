"""SQLite reservations protect quotas across concurrent calls and process restarts (single worker)."""
import hashlib
import sqlite3
import threading
import time
from datetime import datetime, timezone


def scope(p):
    # Explicit group lets keys/models sharing an account share the same budget.
    value = p["quota_group"] or p["model"].split("/", 1)[0] + ":" + p["api_base"] + ":" + p["api_key"]
    return hashlib.sha256(value.encode()).hexdigest()


def boundaries(now):
    dt = datetime.fromtimestamp(now, timezone.utc)
    return dict(minute=now - 60, day=dt.replace(hour=0, minute=0, second=0, microsecond=0).timestamp(),
                month=dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp())


class Ledger:
    def __init__(self, path, clock=time.time):
        self.clock = clock
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY, request_id TEXT, provider TEXT, scope TEXT, ts REAL,
                status TEXT, input_tokens INTEGER, output_tokens INTEGER, tokens INTEGER,
                estimated INTEGER, cost REAL, latency_ms INTEGER DEFAULT 0, reason TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS scope_time ON attempts(scope, ts);
            CREATE TABLE IF NOT EXISTS health (
                provider TEXT PRIMARY KEY, status TEXT, until REAL, checked REAL, latency_ms INTEGER
            );
        """)
        # A crash may have happened after a charge. Keep its conservative token reservation.
        self.db.execute("UPDATE attempts SET status='interrupted', reason='usage_unknown' WHERE status='pending'")
        self.db.commit()

    def usage(self, p, now=None):
        with self.lock:
            cuts = boundaries(self.clock() if now is None else now)
            result = {}
            for period, cutoff in cuts.items():
                row = self.db.execute("SELECT count(*) AS requests, COALESCE(sum(tokens),0) AS tokens, "
                                      "COALESCE(sum(cost),0) AS cost FROM attempts WHERE scope=? AND ts>=?",
                                      (scope(p), cutoff)).fetchone()
                result[period] = dict(row)
            return result

    def health(self, p):
        with self.lock:
            row = self.db.execute("SELECT * FROM health WHERE provider=?", (p["id"],)).fetchone()
            return dict(row) if row else dict(provider=p["id"], status="untested", until=0, checked=0, latency_ms=0)

    def set_health(self, p, status, cooldown=0, latency_ms=0):
        with self.lock, self.db:
            self.db.execute("INSERT OR REPLACE INTO health VALUES(?,?,?,?,?)",
                            (p["id"], status, self.clock() + cooldown if cooldown else 0, self.clock(), latency_ms))

    @staticmethod
    def blocked(p, usage, reserve, tokens, cost):
        for field, period, metric, amount in (("rpm", "minute", "requests", 1),
                                              ("tpm", "minute", "tokens", tokens),
                                              ("daily_requests", "day", "requests", 1),
                                              ("daily_tokens", "day", "tokens", tokens),
                                              ("monthly_tokens", "month", "tokens", tokens),
                                              ("monthly_budget", "month", "cost", cost)):
            limit = p[field]
            if limit and usage[period][metric] + amount > limit * (1 - reserve / 100):
                return field
        return ""

    def reserve(self, p, request_id, input_tokens, output_tokens, reserve):
        with self.lock, self.db:
            now = self.clock()
            if self.health(p)["until"] > now:
                return None, "cooldown"
            total = input_tokens + output_tokens
            cost = (input_tokens * p["input_price"] + output_tokens * p["output_price"]) / 1_000_000
            reason = self.blocked(p, self.usage(p, now), reserve, total, cost)
            if reason:
                return None, reason
            cursor = self.db.execute("INSERT INTO attempts(request_id,provider,scope,ts,status,input_tokens,"
                                     "output_tokens,tokens,estimated,cost) VALUES(?,?,?,?,?,?,?,?,?,?)",
                                     (request_id, p["id"], scope(p), now, "pending", input_tokens,
                                      output_tokens, total, 1, cost))
            return cursor.lastrowid, ""

    def finish(self, attempt, p, status, usage, latency, reason=""):
        with self.lock, self.db:
            if usage and isinstance(usage.get("prompt_tokens"), int) and isinstance(usage.get("completion_tokens"), int):
                inp, out = max(0, usage["prompt_tokens"]), max(0, usage["completion_tokens"])
                total = max(inp + out, int(usage.get("total_tokens") or 0))
                cost = (inp * p["input_price"] + out * p["output_price"]) / 1_000_000
                self.db.execute("UPDATE attempts SET input_tokens=?,output_tokens=?,tokens=?,estimated=0,cost=? WHERE id=?",
                                (inp, out, total, cost, attempt))
            self.db.execute("UPDATE attempts SET status=?,latency_ms=?,reason=? WHERE id=?",
                            (status, latency, reason, attempt))

    def recent(self, limit=100):
        with self.lock:
            return [dict(r) for r in self.db.execute("SELECT id,request_id,provider,ts,status,input_tokens,output_tokens,"
                                                   "tokens,estimated,cost,latency_ms,reason FROM attempts ORDER BY id DESC LIMIT ?", (limit,))]

    def prune(self, days):
        with self.lock, self.db:
            # Never delete the current month's rows: monthly accounting must survive shorter history settings.
            cutoff = min(self.clock() - days * 86400, boundaries(self.clock())["month"])
            self.db.execute("DELETE FROM attempts WHERE ts<? AND status!='pending'", (cutoff,))

    def close(self):
        self.db.close()
