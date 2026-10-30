"""Read-only provider account metadata. No inferred token balances or plan upgrades."""
import copy
import hashlib
import json
import math
import threading
import time

from .discovery import read_json
from .router import GatewayError


class Accounts:
    def __init__(self, fetch=read_json, clock=time.time):
        self.fetch, self.clock = fetch, clock
        self.cache = {}
        self.lock = threading.Lock()

    @staticmethod
    def endpoint(profile):
        base = profile["api_base"].rstrip("/")
        if profile["preset"] == "openrouter" and base in ("", "https://openrouter.ai/api/v1"):
            return "https://openrouter.ai/api/v1/key"
        if profile["preset"] == "deepseek" and base in ("", "https://api.deepseek.com", "https://api.deepseek.com/v1"):
            return "https://api.deepseek.com/user/balance"
        return None  # Never send a saved key from a custom/proxy endpoint to another host.

    def read(self, profile):
        url = self.endpoint(profile)
        if not url:
            return dict(status="unsupported", plan="unknown", values=[], checked_at=None)
        if not profile["api_key"]:
            return dict(status="key_required", plan="unknown", values=[], checked_at=None)
        identity = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
        with self.lock:
            cached = self.cache.get(identity)
            if cached and self.clock() - cached["checked_at"] < 300:
                return copy.deepcopy(cached)
            try:
                data = self.fetch(url, {"Authorization": "Bearer " + profile["api_key"]}, 8)
                if not isinstance(data, dict):
                    raise ValueError()
                result = self.parse(profile["preset"], data)
            except GatewayError as exc:
                code = "provider_account_auth_error" if exc.code == "model_discovery_auth_error" else "provider_account_unavailable"
                raise GatewayError(code, 502) from None
            except (ValueError, TypeError, KeyError, OverflowError):
                raise GatewayError("provider_account_unavailable", 502) from None
            result.update(status="available", source="provider", checked_at=int(self.clock()))
            if len(self.cache) >= 100:
                self.cache.pop(next(iter(self.cache)))
            self.cache[identity] = copy.deepcopy(result)
            return result

    @staticmethod
    def parse(preset, payload):
        result = dict(plan="unknown", values=[])
        def number(kind, value, unit="USD"):
            if value is None or isinstance(value, bool):
                return
            try:
                value = float(value)
            except (ValueError, TypeError, OverflowError):
                return
            if math.isfinite(value) and abs(value) <= 10**12:
                result["values"].append(dict(kind=kind, value=value, unit=unit))
        if preset == "openrouter":
            data = payload["data"]
            if not isinstance(data, dict):
                raise ValueError()
            free = data.get("is_free_tier")
            if type(free) is bool:
                result["plan"] = "openrouter_free_tier" if free else "openrouter_credits"
            for source, target in (("limit", "key_limit"), ("limit_remaining", "key_remaining"),
                                   ("usage_daily", "spend_day"), ("usage_monthly", "spend_month")):
                number(target, data.get(source))
            quota = data.get("free_model_daily_requests")
            if isinstance(quota, dict):
                for name in ("limit", "used", "remaining"):
                    number("free_requests_" + name, quota.get(name), "requests")
        elif preset == "deepseek":
            balances = payload["balance_infos"]
            if not isinstance(balances, list):
                raise ValueError()
            for item in balances[:2]:
                if not isinstance(item, dict) or item.get("currency") not in ("USD", "CNY"):
                    continue
                for source, target in (("total_balance", "balance"), ("granted_balance", "granted"), ("topped_up_balance", "purchased")):
                    number(target, item.get(source), item["currency"])
        return result
