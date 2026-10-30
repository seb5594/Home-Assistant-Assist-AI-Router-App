"""Separate ingress administration and authenticated OpenAI-compatible data plane."""
import argparse
import hmac
import importlib.metadata
import json
import mimetypes
import os
import re
import secrets
import signal
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .catalog import VERSION, LITELLM_VERSION, catalog
from .ledger import Ledger
from .router import GatewayError, Router, sdk
from .settings import ConfigError, Settings, Supervisor
from .discovery import discover
from .accounts import Accounts

STATIC = Path(__file__).parent / "static"


def buffered_sse(result):
    """Buffer before sending: provider failover never leaves a half-written tool call at the client."""
    common = dict(id=result.get("id", "chatcmpl-router"), object="chat.completion.chunk",
                  created=result.get("created", int(time.time())), model=result["model"])
    choices = []
    for choice in result["choices"]:
        delta = dict(choice.get("message", {}))
        if delta.get("tool_calls"):
            delta["tool_calls"] = [dict(index=i, **tool) for i, tool in enumerate(delta["tool_calls"])]
        choices.append(dict(index=choice.get("index", 0), delta=delta, finish_reason=None))
    chunks = [{**common, "choices": choices},
              {**common, "choices": [dict(index=c.get("index", 0), delta={}, finish_reason=c.get("finish_reason", "stop")) for c in result["choices"]]}]
    if result.get("usage"):
        chunks.append({**common, "choices": [], "usage": result["usage"]})
    return "".join("data: " + json.dumps(c, ensure_ascii=False) + "\n\n" for c in chunks).encode() + b"data: [DONE]\n\n"


class State:
    def __init__(self, folder, supervisor=None, call=None, dev=False):
        self.settings = Settings(folder, supervisor)
        self.ledger = Ledger(Path(folder) / "usage.sqlite3")
        self.router = Router(self.settings, self.ledger, **({"call": call} if call else {}))
        path = Path(folder) / "gateway-token"
        if not path.exists():
            path.write_text(secrets.token_urlsafe(36), encoding="utf-8")
            os.chmod(path, 0o600)
        self.token = path.read_text(encoding="utf-8").strip()
        if len(self.token) < 32:
            raise ConfigError("invalid_gateway_token")
        self.dev = dev
        self.accounts = Accounts()
        self.version_lock = threading.Lock()
        self.version_result = None
        self.version_checked = 0

    def status(self):
        cfg = self.settings.snapshot()
        providers = []
        for p in cfg["providers"]:
            usage = self.ledger.usage(p)
            health = self.ledger.health(p)
            blocked = self.ledger.blocked(p, usage, cfg["reserve_percent"], 0, 0)
            status = ("disabled" if not p["enabled"] else "paid_blocked" if not cfg["allow_paid"] and not (p["free_only"] or p["local"])
                      else "cooldown" if health["until"] > time.time() else "quota_exhausted" if blocked else health["status"])
            providers.append(dict(id=p["id"], status=status, health=health, usage=usage, blocked=blocked))
        return dict(version=VERSION, litellm=importlib.metadata.version("litellm"), pinned=LITELLM_VERSION,
                    providers=providers, recent=self.ledger.recent(), models=self.router.models(),
                    synchronized=bool(self.settings.supervisor), quota_source="local_estimates_utc")

    def connection(self, integration="litellm"):
        if integration not in ("litellm", "mcp_assist"):
            raise GatewayError("invalid_integration", 400)
        cfg = self.settings.snapshot()
        base_url = cfg["gateway_url"] or f"http://{self.settings.hostname}:8000/v1"
        if integration == "mcp_assist":
            # MCP Assist's OpenAI adapter appends /v1/models and /v1/chat/completions itself.
            base_url = base_url.rstrip("/").removesuffix("/v1")
        result = dict(base_url=base_url, integration=integration,
                    model="assist-auto", api_key=self.token, streaming="buffered",
                    assist_url="https://my.home-assistant.io/redirect/config_flow_start/?domain=" + integration,
                    mcp_server_url="https://my.home-assistant.io/redirect/config_flow_start/?domain=mcp_server",
                    mcp_client_url="https://my.home-assistant.io/redirect/config_flow_start/?domain=mcp",
                    pipeline_url="https://my.home-assistant.io/redirect/voice_assistants/",
                    docs_url="https://github.com/mike-nott/mcp-assist" if integration == "mcp_assist" else "https://www.home-assistant.io/integrations/litellm/")
        if integration == "mcp_assist":
            result.update(server_type="OpenAI", request_timeout=cfg["request_timeout"] + 5,
                          hacs_url="https://my.home-assistant.io/redirect/hacs_repository/?owner=mike-nott&repository=mcp-assist&category=integration")
        return result

    def versions(self):
        with self.version_lock:
            if self.version_result and time.time() - self.version_checked < 3600:
                return self.version_result
            request = urllib.request.Request("https://api.github.com/repos/BerriAI/litellm/releases/latest",
                                             headers={"User-Agent": "Assist-AI-Router", "Accept": "application/vnd.github+json"})
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    release = json.load(response)
                version = release["tag_name"].removeprefix("v")
                if release.get("prerelease") or release.get("draft") or not re.fullmatch(r"\d+\.\d+\.\d+", version):
                    raise ValueError()
                newer = tuple(map(int, version.split("."))) > tuple(map(int, LITELLM_VERSION.split(".")))
                result = dict(pinned=LITELLM_VERSION, latest=version, update_available=newer,
                              url="https://github.com/BerriAI/litellm/releases/tag/v" + version,
                              checked=int(time.time()))
            except Exception:
                raise GatewayError("version_check_unavailable", 502) from None
            self.version_result, self.version_checked = result, time.time()
            return result


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, state, admin):
        self.state, self.admin = state, admin
        self.connections = threading.BoundedSemaphore(24)
        super().__init__(address, Handler)

    def process_request(self, request, address):
        if not self.connections.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.connections.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.connections.release()


class Handler(BaseHTTPRequestHandler):
    server_version = "AssistAIRouter"

    def setup(self):
        super().setup()
        self.connection.settimeout(130)

    def log_message(self, *args):
        pass  # URLs, request contents and upstream exceptions never enter console logs.

    def reply(self, code, data, content_type="application/json", extra=None):
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'self'")
        for key, value in (extra or {}).items():
            self.send_header(key, str(value))
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        if self.headers.get("Transfer-Encoding"):
            raise GatewayError("invalid_request", 400)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise GatewayError("invalid_request", 400) from None
        if not 0 < length <= 1_048_576:
            raise GatewayError("request_too_large", 413)
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            raise GatewayError("json_required", 415)
        try:
            return json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            raise GatewayError("invalid_json", 400) from None

    def authorize(self):
        if self.server.admin:
            peer = self.client_address[0]
            allowed = peer in ("127.0.0.1", "::1") if self.server.state.dev else peer == "172.30.32.2"
            if not allowed:
                raise GatewayError("ingress_required", 403)
            if self.command != "GET" and self.headers.get("X-Requested-With") != "AssistAIRouter":
                raise GatewayError("invalid_origin", 403)
        elif not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + self.server.state.token):
            raise GatewayError("unauthorized", 401)

    def do_GET(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def do_PUT(self):
        self.dispatch()

    def dispatch(self):
        try:
            self.authorize()
            self.route()
        except ConfigError as exc:
            code = str(exc)
            self.reply(409 if code == "config_conflict" else 502 if code == "supervisor_unavailable" else 400, {"error": {"code": code}})
        except GatewayError as exc:
            self.reply(exc.status, {"error": {"code": exc.code, "message": exc.code, "type": "router_error"}},
                       extra={"Retry-After": "30"} if exc.status == 503 else None)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass
        except Exception:
            self.reply(500, {"error": {"code": "internal_error"}})

    def route(self):
        state = self.server.state
        path = urlsplit(self.path).path
        method = self.command
        if not self.server.admin:
            if path == "/health" and method == "GET":
                return self.reply(200, {"status": "ok", "version": VERSION})
            if path == "/v1/models" and method == "GET":
                return self.reply(200, {"object": "list", "data": [dict(id=m, object="model", created=0, owned_by="assist-ai-router") for m in state.router.models()]})
            if path == "/v1/chat/completions" and method == "POST":
                body = self.body()
                result, meta = state.router.run(body)
                headers = {"X-Request-ID": meta["request_id"], "X-Router-Provider": meta["provider"]}
                if body.get("stream"):
                    return self.reply(200, buffered_sse(result), "text/event-stream", headers)
                return self.reply(200, result, extra=headers)
            raise GatewayError("not_found", 404)
        if method == "GET":
            if path == "/api/settings":
                state.settings.reload()
                return self.reply(200, state.settings.view())
            if path == "/api/status":
                return self.reply(200, state.status())
            if path == "/api/catalog":
                return self.reply(200, catalog())
            if path == "/api/models":
                # SDK-bundled model catalogue: no paid discovery requests, no credentials sent.
                models = {key: sorted(value) for key, value in getattr(sdk(), "models_by_provider", {}).items()}
                return self.reply(200, models)
            if path in ("/", "/index.html", "/app.js", "/style.css", "/i18n.json"):
                file = STATIC / ("index.html" if path == "/" else path[1:])
                return self.reply(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        elif method == "PUT" and path == "/api/settings":
            body = self.body()
            if not isinstance(body, dict):
                raise GatewayError("invalid_request", 400)
            return self.reply(200, state.settings.save(body.get("options"), body.get("revision")))
        elif method == "POST":
            body = self.body()
            if not isinstance(body, dict):
                raise GatewayError("invalid_request", 400)
            if path == "/api/connection":
                return self.reply(200, state.connection(body.get("integration", "litellm")))
            if path == "/api/provider-credential":
                return self.reply(200, state.settings.credential(body.get("provider_id"), body.get("revision")))
            if path == "/api/provider-account":
                return self.reply(200, state.accounts.read(state.settings.discovery_profile(body)))
            if path == "/api/provider-models":
                return self.reply(200, discover(state.settings.discovery_profile(body)))
            if path == "/api/versions":
                return self.reply(200, state.versions())
            if path == "/api/test":
                pid = body.get("provider_id")
                if pid not in [p["id"] for p in state.settings.snapshot()["providers"]]:
                    raise GatewayError("unknown_provider", 404)
                result, meta = state.router.run(dict(model="provider:" + pid, messages=[dict(role="user", content="Reply OK")], max_tokens=8))
                return self.reply(200, dict(ok=True, usage=result.get("usage"), **meta))
        raise GatewayError("not_found", 404)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="/data")
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--admin-port", type=int, default=8099)
    parser.add_argument("--api-port", type=int, default=8000)
    args = parser.parse_args()
    if importlib.metadata.version("litellm") != LITELLM_VERSION:
        raise SystemExit("LiteLLM version differs from reviewed pin")
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
    if not args.dev and not supervisor_token:
        raise SystemExit("Supervisor token required; local development requires --dev")
    state = State(args.data, Supervisor(supervisor_token) if supervisor_token and not args.dev else None, dev=args.dev)
    sdk()
    bind = "127.0.0.1" if args.dev else "0.0.0.0"
    admin, api = Server((bind, args.admin_port), state, True), Server((bind, args.api_port), state, False)
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (admin, api)]
    for thread in threads:
        thread.start()
    stopped = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stopped.set())
    print(f"Assist AI Router {VERSION} · LiteLLM {LITELLM_VERSION}", flush=True)
    stopped.wait()
    for server in (admin, api):
        server.shutdown()
        server.server_close()
    state.ledger.close()


if __name__ == "__main__":
    main()
