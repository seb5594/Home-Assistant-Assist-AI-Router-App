"""Supervisor is the source of truth. Never replace a secret reference with its resolved value."""
import copy
import hashlib
import json
import os
import re
import threading
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from .catalog import DEFAULTS, PROVIDER_DEFAULTS, catalog


class ConfigError(Exception):
    pass


def validate_url(value):
    if not value:
        return
    parsed = urlsplit(value)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ConfigError("invalid_url")
    if parsed.hostname.lower() in ("supervisor", "169.254.169.254", "metadata.google.internal"):
        raise ConfigError("invalid_url")


def normalize(raw):
    if not isinstance(raw, dict) or set(raw) - set(DEFAULTS):
        raise ConfigError("invalid_settings")
    cfg = {**copy.deepcopy(DEFAULTS), **copy.deepcopy(raw)}
    if cfg["language"] not in ("de", "en") or cfg["routing"] not in ("priority", "quota", "round_robin", "local_first"):
        raise ConfigError("invalid_settings")
    for key, lo, hi in (("max_output_tokens", 1, 32768), ("request_timeout", 5, 120),
                        ("attempt_timeout", 1, 60), ("max_attempts", 1, 20),
                        ("cooldown_seconds", 1, 86400), ("reserve_percent", 0, 90), ("history_days", 1, 365)):
        if type(cfg[key]) is not int or not lo <= cfg[key] <= hi:
            raise ConfigError("invalid_" + key)
    if type(cfg["allow_paid"]) is not bool or not isinstance(cfg["gateway_url"], str):
        raise ConfigError("invalid_settings")
    validate_url(cfg["gateway_url"])
    if not isinstance(cfg["providers"], list) or len(cfg["providers"]) > 100:
        raise ConfigError("invalid_providers")
    ids = set()
    normalized = []
    for source in cfg["providers"]:
        if not isinstance(source, dict) or set(source) - (set(PROVIDER_DEFAULTS) | {"id"}):
            raise ConfigError("invalid_provider")
        p = {**PROVIDER_DEFAULTS, **source}
        if not isinstance(p.get("id"), str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", p["id"]) or p["id"] in ids:
            raise ConfigError("invalid_provider_id")
        ids.add(p["id"])
        for key in ("name", "preset", "model", "api_key", "api_base", "api_version", "quota_group"):
            if not isinstance(p[key], str) or len(p[key]) > (8192 if key == "api_key" else 512):
                raise ConfigError("invalid_provider")
        if not p["name"] or "/" not in p["model"] or len(p["model"]) < 3:
            raise ConfigError("invalid_model")
        # Provider credentials must be literal or a Supervisor !secret reference, never SDK env lookups.
        if p["api_key"].startswith(("os.environ/", "os.getenv/")):
            raise ConfigError("invalid_api_key")
        for key in ("enabled", "free_only", "local", "supports_tools", "supports_vision"):
            if type(p[key]) is not bool:
                raise ConfigError("invalid_provider")
        for key in ("rpm", "tpm", "daily_tokens", "daily_requests", "monthly_tokens", "context_tokens"):
            if type(p[key]) is not int or not 0 <= p[key] <= 10**12:
                raise ConfigError("invalid_limits")
        for key in ("input_price", "output_price", "monthly_budget"):
            if type(p[key]) not in (int, float) or not 0 <= p[key] <= 10**9:
                raise ConfigError("invalid_prices")
        validate_url(p["api_base"])
        if p["model"].startswith(("openai/", "azure/", "ollama_chat/")) and not p["api_base"] and p["preset"] in ("openai_compatible", "azure", "ollama_chat"):
            raise ConfigError("api_base_required")
        normalized.append(p)
    cfg["providers"] = normalized
    if not isinstance(cfg["rules"], list) or len(cfg["rules"]) > 100:
        raise ConfigError("invalid_rules")
    for rule in cfg["rules"]:
        if (not isinstance(rule, dict) or set(rule) != {"name", "alias", "require_tools", "provider_ids"}
                or not isinstance(rule["name"], str) or not rule["name"] or len(rule["name"]) > 128
                or not isinstance(rule["alias"], str) or not re.fullmatch(r"[a-zA-Z0-9_.*-]{1,64}", rule["alias"])
                or type(rule["require_tools"]) is not bool or not isinstance(rule["provider_ids"], str)
                or not rule["provider_ids"] or any(i.strip() not in ids for i in rule["provider_ids"].split(","))):
            raise ConfigError("invalid_rules")
    return cfg


class Supervisor:
    def __init__(self, token):
        self.token = token

    def request(self, path, data=None):
        req = urllib.request.Request("http://supervisor" + path,
                                     data=None if data is None else json.dumps(data).encode(),
                                     headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                payload = json.load(response)
            if payload.get("result") != "ok":
                raise ConfigError("supervisor_unavailable")
            return payload["data"]
        except Exception:
            # Supervisor errors can include submitted credentials. Never echo them.
            raise ConfigError("supervisor_unavailable") from None

    def read(self):
        info = self.request("/addons/self/info")
        return info["options"], self.request("/addons/self/options/config"), info.get("hostname", "")

    def save(self, raw):
        self.request("/addons/self/options", {"options": raw})


class Settings:
    def __init__(self, folder, supervisor=None):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.supervisor = supervisor
        self.lock = threading.RLock()
        self.raw, self.resolved, self.hostname = {}, {}, "localhost"
        self.reload()

    def reload(self):
        with self.lock:
            if self.supervisor:
                raw, resolved, hostname = self.supervisor.read()
            else:
                path = self.folder / "options.json"
                raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else DEFAULTS
                resolved, hostname = raw, "localhost"
            next_raw, next_resolved = normalize(raw), normalize(resolved)
            if any(p["api_key"].startswith("!secret ") for p in next_resolved["providers"]):
                raise ConfigError("unresolved_secret")
            self.raw, self.resolved = next_raw, next_resolved
            self.hostname = hostname or "localhost"

    def revision(self):
        return hashlib.sha256(json.dumps(self.raw, sort_keys=True).encode()).hexdigest()

    def view(self):
        with self.lock:
            raw = copy.deepcopy(self.raw)
            for p in raw["providers"]:
                key = p.pop("api_key")
                p["api_key_set"] = bool(key)
                p["api_key_reference"] = key if key.startswith("!secret ") else ""
            return dict(options=raw, revision=self.revision(), supervisor=bool(self.supervisor))

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.resolved)

    def discovery_profile(self, draft):
        """Use draft credentials before saving; keep saved secrets bound to their destination."""
        if not isinstance(draft, dict) or set(draft) - {"id", "preset", "api_base", "api_key"}:
            raise ConfigError("invalid_provider")
        pid = draft.get("id", "")
        if not isinstance(pid, str) or (pid and not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", pid)):
            raise ConfigError("invalid_provider_id")
        with self.lock:
            self.reload()
            previous = next((p for p in self.raw["providers"] if p["id"] == pid), None)
            preset = draft.get("preset", previous["preset"] if previous else "openai_compatible")
            template = next((p for p in catalog() if p["id"] == preset), None)
            if template is None:
                raise ConfigError("invalid_provider")
            base = draft.get("api_base", previous["api_base"] if previous else "")
            key = draft.get("api_key")
            if not isinstance(base, str) or len(base) > 512 or (key is not None and (not isinstance(key, str) or len(key) > 8192)):
                raise ConfigError("invalid_provider")
            validate_url(base)
            if key is None or key.startswith("!secret "):
                if not previous:
                    if key:
                        raise ConfigError("model_discovery_save_secret")
                    key = ""
                else:
                    if preset != previous["preset"] or base.rstrip("/") != previous["api_base"].rstrip("/"):
                        raise ConfigError("model_discovery_reenter_key")
                    if key is not None and key != previous["api_key"]:
                        raise ConfigError("model_discovery_save_secret")
                    key = next(p["api_key"] for p in self.resolved["providers"] if p["id"] == pid)
            if key.startswith(("os.environ/", "os.getenv/")) or "\r" in key or "\n" in key:
                raise ConfigError("invalid_api_key")
            return dict(preset=preset, prefix=template["prefix"], api_key=key, api_base=base)

    def save(self, incoming, revision):
        with self.lock:
            self.reload()  # Detect edits from the HA Configuration tab and preserve raw !secret values.
            if revision != self.revision():
                raise ConfigError("config_conflict")
            incoming = copy.deepcopy(incoming)
            previous = {p["id"]: p for p in self.raw["providers"]}
            if not isinstance(incoming, dict) or not isinstance(incoming.get("providers"), list):
                raise ConfigError("invalid_settings")
            for p in incoming["providers"]:
                if isinstance(p, dict) and "api_key" not in p:
                    p["api_key"] = previous.get(p.get("id"), {}).get("api_key", "")
            incoming = normalize(incoming)
            if self.supervisor:
                self.supervisor.save(incoming)
                self.reload()  # Use newly rendered secrets immediately, without an app restart.
            else:
                if any(p["api_key"].startswith("!secret ") for p in incoming["providers"]):
                    raise ConfigError("unresolved_secret")
                path = self.folder / "options.json"
                temp = path.with_suffix(".tmp")
                temp.write_text(json.dumps(incoming, indent=2), encoding="utf-8")
                os.chmod(temp, 0o600)
                os.replace(temp, path)
                self.raw = incoming
                self.resolved = copy.deepcopy(incoming)
            return self.view()
