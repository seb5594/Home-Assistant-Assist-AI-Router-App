"""Live metadata-only model discovery; credentials never enter URLs, logs or responses."""
import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlencode

from .router import GatewayError
from .settings import validate_url

# OpenAI-compatible provider metadata APIs. A custom api_base overrides the default.
BASES = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "cerebras": "https://api.cerebras.ai/public/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "mistral": "https://api.mistral.ai/v1",
    "huggingface": "https://router.huggingface.co/v1",
    "sambanova": "https://api.sambanova.ai/v1",
    "together_ai": "https://api.together.xyz/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "xai": "https://api.x.ai/v1",
    "nvidia_nim": "https://integrate.api.nvidia.com/v1",
    "openai_compatible": "",
}
SPECIAL = {"gemini", "anthropic", "cohere_chat", "ollama_chat"}
OPTIONAL_KEY = {"openrouter", "huggingface", "nvidia_nim", "openai_compatible", "ollama_chat"}
MAX_BYTES, MAX_MODELS, MAX_PAGES = 2_097_152, 2000, 5


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # urllib otherwise forwards Authorization to redirected hosts.
        raise urllib.error.HTTPError(req.full_url, code, "redirect_blocked", headers, fp)


def read_json(url, headers, timeout):
    request = urllib.request.Request(url, headers=headers)
    # Ignore ambient proxy configuration: it must not redirect private credentials.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise GatewayError("model_discovery_invalid_response", 502)
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError()
        return data
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 498):
            code, status = "model_discovery_auth_error", 400
        elif exc.code == 429:
            code, status = "model_discovery_rate_limited", 429
        elif exc.code in (404, 405, 501):
            code, status = "model_discovery_unsupported", 400
        else:
            code, status = "model_discovery_unavailable", 502
        exc.close()
        raise GatewayError(code, status) from None
    except GatewayError:
        raise
    except (ValueError, UnicodeError):
        raise GatewayError("model_discovery_invalid_response", 502) from None
    except Exception:
        raise GatewayError("model_discovery_unavailable", 502) from None


def endpoint(profile):
    preset, key = profile["preset"], profile["api_key"]
    if preset not in BASES and preset not in SPECIAL:
        raise GatewayError("model_discovery_unsupported", 400)
    if not key and preset not in OPTIONAL_KEY:
        raise GatewayError("model_discovery_key_required", 400)
    base = profile["api_base"].rstrip("/")
    headers = {"Accept": "application/json", "User-Agent": "Assist-AI-Router"}
    if preset == "gemini":
        base = base or "https://generativelanguage.googleapis.com/v1beta"
        if not base.endswith(("/v1", "/v1beta")):
            base += "/v1beta"
        headers["x-goog-api-key"] = key
        return base + "/models", headers, {"pageSize": "100"}, "models", "name"
    if preset == "anthropic":
        base = base or "https://api.anthropic.com/v1"
        if not base.endswith("/v1"):
            base += "/v1"
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
        return base + "/models", headers, {"limit": "100"}, "data", "id"
    if key:
        headers["Authorization"] = "Bearer " + key
    if preset == "ollama_chat":
        if not base:
            raise GatewayError("api_base_required", 400)
        return base.removesuffix("/v1") + "/api/tags", headers, {}, "models", "name"
    if preset == "cohere_chat":
        base = base or "https://api.cohere.com/v1"
        base = base.removesuffix("/v2").removesuffix("/v1") + "/v1"
        return base + "/models", headers, {"endpoint": "chat", "page_size": "100"}, "models", "name"
    base = base or BASES[preset]
    if not base:
        raise GatewayError("api_base_required", 400)
    # api_base is a versioned API root (same value the SDK uses for completions).
    return base + "/models", headers, {}, "data", "id"


def discover(profile, fetch=read_json):
    url, headers, query, list_key, id_key = endpoint(profile)
    validate_url(url)
    deadline = time.monotonic() + 12
    names, visited = set(), set()
    complete = False
    for _ in range(MAX_PAGES):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        page_url = url + ("?" + urlencode(query) if query else "")
        if page_url in visited:
            break
        visited.add(page_url)
        data = fetch(page_url, headers, min(8, remaining))
        rows = data.get(list_key)
        if not isinstance(rows, list):
            raise GatewayError("model_discovery_invalid_response", 502)
        for item in rows:
            if not isinstance(item, dict) or item.get("active") is False or item.get("is_deprecated") is True:
                continue
            if profile["preset"] == "gemini" and "generateContent" not in item.get("supportedGenerationMethods", []):
                continue
            name = item.get(id_key)
            if not isinstance(name, str) or not 0 < len(name) <= 512 or any(ord(c) < 32 or ord(c) == 127 for c in name):
                continue
            if profile["preset"] == "gemini":
                name = name.removeprefix("models/")
            names.add(profile["prefix"] + "/" + name)
        if len(names) >= MAX_MODELS:
            break
        next_page = data.get("nextPageToken") or data.get("next_page_token")
        if next_page:
            if not isinstance(next_page, str) or len(next_page) > 2048:
                raise GatewayError("model_discovery_invalid_response", 502)
            query["pageToken" if profile["preset"] == "gemini" else "page_token"] = next_page
        elif profile["preset"] == "anthropic" and data.get("has_more"):
            cursor = data.get("last_id")
            if not isinstance(cursor, str) or not cursor or len(cursor) > 512:
                raise GatewayError("model_discovery_invalid_response", 502)
            query["after_id"] = cursor
        else:
            complete = not bool(data.get("has_more"))
            break
    if not names:
        raise GatewayError("model_discovery_empty", 400)
    return dict(models=sorted(names, key=str.casefold)[:MAX_MODELS], source="provider",
                complete=complete, fetched_at=int(time.time()))
