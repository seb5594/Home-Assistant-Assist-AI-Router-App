"""Policy routing around the pinned LiteLLM SDK; no prompts, keys or responses in the ledger."""
import copy
import json
import logging
import os
import threading
import time
import uuid
from email.utils import parsedate_to_datetime

from .ledger import scope


class GatewayError(Exception):
    def __init__(self, code, status=503, attempts=None):
        self.code, self.status, self.attempts = code, status, attempts or []
        super().__init__(code)


def sdk():
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    os.environ["LITELLM_TELEMETRY_DISABLED"] = "true"
    os.environ["DO_NOT_TRACK"] = "1"
    import litellm
    litellm.telemetry = False
    litellm.suppress_debug_info = True
    litellm.set_verbose = False
    # SDK exception/debug messages may embed credentials or prompts. Our errors use fixed codes.
    for name in ("LiteLLM", "LiteLLM Router", "LiteLLM Proxy", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    return litellm


def completion(p, payload, timeout):
    args = {k: payload[k] for k in ("messages", "tools", "tool_choice", "temperature", "top_p",
                                   "max_tokens", "response_format", "stop", "seed", "parallel_tool_calls") if k in payload}
    args.update(model=p["model"], api_key=p["api_key"] or "unused-local-key", stream=False,
                timeout=timeout, num_retries=0, drop_params=False)
    if p["api_base"]:
        args["api_base"] = p["api_base"]
    if p["api_version"]:
        args["api_version"] = p["api_version"]
    return sdk().completion(**args).model_dump(exclude_none=True)


def failure(exc, default_cooldown):
    status = getattr(exc, "status_code", None)
    name = type(exc).__name__
    cooldown = default_cooldown
    headers = getattr(getattr(exc, "response", None), "headers", {}) or {}
    retry = headers.get("retry-after")
    if retry:
        try:
            cooldown = max(cooldown, float(retry))
        except (ValueError, TypeError):
            try:
                cooldown = max(cooldown, parsedate_to_datetime(retry).timestamp() - time.time())
            except (ValueError, TypeError, OverflowError):
                pass
    cooldown = min(max(cooldown, 1), 86400)
    if status == 429:
        return "rate_limited", cooldown, True
    if status in (401, 403):
        return "auth_error", max(cooldown, 300), True
    if name == "ContextWindowExceededError":
        return "context_exceeded", 0, True
    if status == 404:
        return "model_unavailable", max(cooldown, 300), True
    if status in (408, 409) or (isinstance(status, int) and status >= 500) or "Timeout" in name or "Connection" in name:
        return "unavailable", cooldown, True
    return "request_rejected", 0, False


def estimate(payload):
    # Conservative byte estimate avoids downloading a tokenizer. Not an invoice token count.
    # Include all roles, tool definitions, tool results and image payloads; no truncation of Assist context.
    return len(json.dumps({k: payload[k] for k in ("messages", "tools") if k in payload}, ensure_ascii=False).encode()) + 64


def has_vision(messages):
    return any(isinstance(m.get("content"), list) and any(
        isinstance(part, dict) and part.get("type") in ("image_url", "input_image") for part in m["content"])
        for m in messages)


class Router:
    def __init__(self, settings, ledger, call=completion):
        self.settings, self.ledger, self.call = settings, ledger, call
        self.order_lock = threading.Lock()
        self.turn = 0
        self.slots = threading.BoundedSemaphore(8)

    def models(self):
        cfg = self.settings.snapshot()
        aliases = ["assist-auto"] + [r["alias"] for r in cfg["rules"] if r["alias"] != "*"]
        return sorted(set(aliases + ["provider:" + p["id"] for p in cfg["providers"] if p["enabled"]]))

    def candidates(self, cfg, payload, inp):
        alias = payload["model"]
        if alias not in self.models():
            raise GatewayError("unknown_model", 404)
        tools = bool(payload.get("tools"))
        vision = has_vision(payload["messages"])
        providers = cfg["providers"]
        if alias.startswith("provider:"):
            providers = [p for p in providers if p["id"] == alias.split(":", 1)[1]]
        else:
            matched = False
            for rule in cfg["rules"]:
                if rule["alias"] in (alias, "*") and (not rule["require_tools"] or tools):
                    allowed = {i.strip() for i in rule["provider_ids"].split(",")}
                    providers = [p for p in providers if p["id"] in allowed]
                    matched = True
                    break
            if alias != "assist-auto" and not matched:
                providers = []
        eligible = [p for p in providers if p["enabled"] and (cfg["allow_paid"] or p["free_only"] or p["local"])
                    and (not tools or p["supports_tools"]) and (not vision or p["supports_vision"])
                    and (not p["context_tokens"] or inp + payload["max_tokens"] <= p["context_tokens"])]
        if cfg["routing"] == "local_first":
            eligible.sort(key=lambda p: not p["local"])
        elif cfg["routing"] == "quota":
            def consumed(p):
                usage = self.ledger.usage(p)
                ratios = [usage[period][metric] / p[field] for field, period, metric in
                          (("daily_tokens", "day", "tokens"), ("monthly_tokens", "month", "tokens"),
                           ("daily_requests", "day", "requests"), ("tpm", "minute", "tokens"),
                           ("rpm", "minute", "requests")) if p[field]]
                return max(ratios) if ratios else 1.0  # Unknown quota never means unlimited.
            eligible.sort(key=consumed)
        elif cfg["routing"] == "round_robin" and eligible:
            with self.order_lock:
                offset = self.turn % len(eligible)
                self.turn += 1
            eligible = eligible[offset:] + eligible[:offset]
        return eligible

    def run(self, payload):
        if not self.slots.acquire(blocking=False):
            raise GatewayError("gateway_busy", 503)
        try:
            return self._run(payload)
        finally:
            self.slots.release()

    def _run(self, payload):
        if not isinstance(payload, dict):
            raise GatewayError("invalid_request", 400)
        payload = copy.deepcopy(payload)
        if (not isinstance(payload.get("messages"), list) or not payload["messages"]
                or any(not isinstance(m, dict) or m.get("role") not in ("system", "developer", "user", "assistant", "tool", "function") for m in payload["messages"])
                or not isinstance(payload.get("model", "assist-auto"), str)):
            raise GatewayError("invalid_request", 400)
        cfg = self.settings.snapshot()
        payload.setdefault("model", "assist-auto")
        max_tokens = payload.get("max_completion_tokens", payload.get("max_tokens", cfg["max_output_tokens"]))
        if type(max_tokens) is not int or max_tokens < 1:
            raise GatewayError("invalid_max_tokens", 400)
        payload["max_tokens"] = min(max_tokens, cfg["max_output_tokens"])
        if "tools" in payload and not isinstance(payload["tools"], list):
            raise GatewayError("invalid_tools", 400)
        inp, rid = estimate(payload), uuid.uuid4().hex
        providers = self.candidates(cfg, payload, inp)
        attempts, calls, blocked_scopes = [], 0, set()
        deadline = time.monotonic() + cfg["request_timeout"]
        self.ledger.prune(cfg["history_days"])
        for p in providers:
            if time.monotonic() >= deadline or calls >= cfg["max_attempts"]:
                break
            if scope(p) in blocked_scopes:
                attempts.append(dict(provider=p["id"], reason="shared_quota_cooldown"))
                continue
            attempt, reason = self.ledger.reserve(p, rid, inp, payload["max_tokens"], cfg["reserve_percent"])
            if attempt is None:
                attempts.append(dict(provider=p["id"], reason=reason))
                continue
            started = time.monotonic()
            calls += 1
            try:
                result = self.call(p, payload, min(cfg["attempt_timeout"], max(0.1, deadline - started)))
                if not isinstance(result, dict) or not result.get("choices"):
                    raise GatewayError("invalid_upstream_response")
            except Exception as exc:
                code, cooldown, fallback = failure(exc, cfg["cooldown_seconds"])
                self.ledger.finish(attempt, p, "error", None, int((time.monotonic() - started) * 1000), code)
                if cooldown:
                    self.ledger.set_health(p, code, cooldown)
                if code == "rate_limited":
                    blocked_scopes.add(scope(p))
                    for sibling in cfg["providers"]:
                        if scope(sibling) == scope(p):
                            self.ledger.set_health(sibling, code, cooldown)
                attempts.append(dict(provider=p["id"], reason=code))
                if not fallback:
                    raise GatewayError(code, 400, attempts) from None
                continue
            elapsed = int((time.monotonic() - started) * 1000)
            self.ledger.finish(attempt, p, "success", result.get("usage"), elapsed)
            self.ledger.set_health(p, "ready", latency_ms=elapsed)
            result["model"] = payload["model"]
            # Only OpenAI response fields leave the API. Upstream hidden fields can contain credentials.
            result = {k: result[k] for k in ("id", "object", "created", "model", "choices", "usage", "system_fingerprint") if k in result}
            return result, dict(request_id=rid, provider=p["id"], attempts=attempts, latency_ms=elapsed)
        raise GatewayError("no_provider_available", 503, attempts)
