import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from test_router import DEFAULTS, profile, response
from app.router import completion
from app.server import Server, State


class HTTP(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = State(self.tmp.name, call=lambda *a: response(), dev=True)
        self.state.settings.save({**DEFAULTS, "providers": [profile("a")]}, self.state.settings.revision())
        self.admin = Server(("127.0.0.1", 0), self.state, True)
        self.api = Server(("127.0.0.1", 0), self.state, False)
        self.threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (self.admin, self.api)]
        for thread in self.threads:
            thread.start()

    def tearDown(self):
        for server in (self.admin, self.api):
            server.shutdown()
            server.server_close()
        self.state.ledger.close()
        self.tmp.cleanup()

    def request(self, server, path, data=None, auth=False, custom=True, method=None):
        headers = {"Content-Type": "application/json"}
        if custom:
            headers["X-Requested-With"] = "AssistAIRouter"
        if auth:
            headers["Authorization"] = "Bearer " + self.state.token
        req = urllib.request.Request(f"http://127.0.0.1:{server.server_port}" + path,
                                     data=None if data is None else json.dumps(data).encode(), headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as result:
                return result.status, result.read(), result.headers
        except urllib.error.HTTPError as error:
            return error.code, error.read(), error.headers

    def test_data_plane_requires_auth_and_never_exposes_admin_endpoints(self):
        self.assertEqual(self.request(self.api, "/v1/models")[0], 401)
        code, data, _ = self.request(self.api, "/v1/models", auth=True)
        self.assertEqual(code, 200)
        self.assertIn("assist-auto", data.decode())
        for path in ("/api/settings", "/api/connection", "/index.html"):
            self.assertEqual(self.request(self.api, path, auth=True)[0], 404)

    def test_ingress_port_requires_supervisor_peer_in_production(self):
        self.state.dev = False
        self.assertEqual(self.request(self.admin, "/api/settings")[0], 403)

    def test_csrf_header_is_required_before_sending_credentials(self):
        self.assertEqual(self.request(self.admin, "/api/connection", {}, custom=False)[0], 403)
        code, data, _ = self.request(self.admin, "/api/connection", {})
        self.assertEqual(code, 200)
        connection = json.loads(data)
        self.assertEqual(connection["api_key"], self.state.token)
        self.assertIn("domain=litellm", connection["assist_url"])

    def test_settings_response_does_not_leak_keys(self):
        code, data, headers = self.request(self.admin, "/api/settings")
        self.assertEqual(code, 200)
        self.assertNotIn("key-a", data.decode())
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

    def test_original_credential_is_only_loaded_by_protected_ingress_post(self):
        body = dict(provider_id="a", revision=self.state.settings.revision())
        code, raw, headers = self.request(self.admin, "/api/provider-credential", body)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(raw), {"api_key": "key-a"})
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.request(self.admin, "/api/provider-credential", body, custom=False)[0], 403)
        self.assertEqual(self.request(self.api, "/api/provider-credential", body, auth=True)[0], 404)
        self.assertEqual(self.request(self.admin, "/api/provider-credential")[0], 404)
        body["revision"] = "stale"
        self.assertEqual(self.request(self.admin, "/api/provider-credential", body)[0], 409)

    def test_account_metadata_uses_draft_binding_and_is_ingress_only(self):
        draft = dict(id="a", preset="groq", api_base="")
        code, raw, _ = self.request(self.admin, "/api/provider-account", draft)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(raw)["status"], "unsupported")
        self.assertNotIn("key-a", raw.decode())
        self.assertEqual(self.request(self.admin, "/api/provider-account", draft, custom=False)[0], 403)
        self.assertEqual(self.request(self.api, "/api/provider-account", draft, auth=True)[0], 404)
        draft["api_base"] = "https://other.example/v1"
        self.assertEqual(self.request(self.admin, "/api/provider-account", draft)[0], 400)

    def test_live_model_discovery_is_ingress_only_and_does_not_save_credentials(self):
        draft = dict(preset="groq", api_key="draft-private-key", api_base="")
        captured = []
        def discover(profile):
            captured.append(profile)
            return dict(models=["groq/new-model"], source="provider", complete=True)
        with patch("app.server.discover", discover):
            code, raw, _ = self.request(self.admin, "/api/provider-models", draft)
            self.assertEqual(code, 200)
            self.assertEqual(json.loads(raw)["models"], ["groq/new-model"])
            self.assertNotIn("draft-private-key", raw.decode())
            self.assertEqual(captured[0]["api_key"], "draft-private-key")
            self.assertEqual(self.state.settings.snapshot()["providers"][0]["api_key"], "key-a")
            self.assertEqual(self.request(self.admin, "/api/provider-models", draft, custom=False)[0], 403)
            self.assertEqual(self.request(self.api, "/api/provider-models", draft, auth=True)[0], 404)
            self.assertEqual(len(captured), 1)

    def test_pause_and_resume_are_durable_and_keep_credentials_and_usage(self):
        self.state.router.run(dict(model="assist-auto", messages=[dict(role="user", content="Hi")]))
        original_usage = self.state.ledger.recent()
        for enabled in (False, True):
            view = json.loads(self.request(self.admin, "/api/settings")[1])
            p = view["options"]["providers"][0]
            p.pop("api_key_set")
            p.pop("api_key_reference")
            p["enabled"] = enabled
            code, _, _ = self.request(self.admin, "/api/settings", {"options": view["options"], "revision": view["revision"]}, method="PUT")
            self.assertEqual(code, 200)
            self.state.settings.reload()
            self.assertEqual(self.state.settings.snapshot()["providers"][0]["enabled"], enabled)
            self.assertEqual(self.state.settings.snapshot()["providers"][0]["api_key"], "key-a")
            self.assertEqual(self.state.ledger.recent(), original_usage)
            models = json.loads(self.request(self.api, "/v1/models", auth=True)[1])["data"]
            self.assertEqual("provider:a" in [m["id"] for m in models], enabled)
        self.assertEqual(self.state.settings.snapshot()["providers"][0]["id"], "a")

    def test_mcp_assist_connection_uses_authenticated_openai_root_url(self):
        from urllib.parse import urlsplit, parse_qs
        code, raw, _ = self.request(self.admin, "/api/connection", {"integration": "mcp_assist"})
        self.assertEqual(code, 200)
        data = json.loads(raw)
        self.assertEqual(data["base_url"], "http://localhost:8000")
        self.assertEqual(data["server_type"], "OpenAI")
        self.assertEqual(data["api_key"], self.state.token)
        self.assertEqual(data["request_timeout"], 50)
        self.assertEqual(data["model"], "assist-auto")
        self.assertEqual(parse_qs(urlsplit(data["assist_url"]).query), {"domain": ["mcp_assist"]})
        self.assertEqual(parse_qs(urlsplit(data["hacs_url"]).query), {"owner": ["mike-nott"], "repository": ["mcp-assist"], "category": ["integration"]})
        for key in ("assist_url", "hacs_url", "docs_url"):
            self.assertNotIn(self.state.token, data[key])
        for base in ("https://router.example/prefix/v1/", "https://router.example/prefix/v1", "https://router.example/prefix"):
            cfg = self.state.settings.snapshot()
            cfg["gateway_url"] = base
            self.state.settings.save(cfg, self.state.settings.revision())
            self.assertEqual(self.state.connection("mcp_assist")["base_url"], "https://router.example/prefix")
            self.assertEqual(self.state.connection()["base_url"], base)
        self.assertEqual(self.request(self.admin, "/api/connection", {"integration": "unknown"})[0], 400)
        self.assertEqual(self.request(self.admin, "/api/connection", {"integration": "mcp_assist"}, custom=False)[0], 403)

    def test_mcp_assist_style_discovery_and_streamed_tool_results(self):
        # Contract from MCP Assist 0.17.2: OpenAI adapter adds /v1 and Bearer auth,
        # then posts model/messages/temperature/max_tokens/tools/tool_choice/stream.
        data = self.state.connection("mcp_assist")
        headers = {"Authorization": "Bearer " + data["api_key"], "Content-Type": "application/json"}
        base = f"http://127.0.0.1:{self.api.server_port}"
        with urllib.request.urlopen(urllib.request.Request(base + "/v1/models", headers=headers)) as models:
            self.assertIn(data["model"], [m["id"] for m in json.load(models)["data"]])
        calls = []
        tool = dict(id="discover-1", type="function", function=dict(name="discover_entities", arguments='{"domain":"light"}'))
        def answer(p, payload, timeout):
            calls.append(payload)
            result = response()
            if len(calls) == 1:
                result["choices"][0]["message"] = dict(role="assistant", content=None, tool_calls=[tool])
                result["choices"][0]["finish_reason"] = "tool_calls"
            return result
        self.state.router.call = answer
        body = dict(model=data["model"], messages=[dict(role="user", content="Which lights are on?")],
                    temperature=0.5, max_tokens=256, stream=True, tool_choice="auto",
                    tools=[dict(type="function", function=dict(name="discover_entities", parameters=dict(type="object", properties={"domain": {"type": "string"}})))])
        req = urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(body).encode(), headers=headers)
        with urllib.request.urlopen(req) as stream:
            chunks = [json.loads(line[6:]) for line in stream.read().decode().splitlines() if line.startswith("data:") and "[DONE]" not in line]
        self.assertEqual(chunks[0]["choices"][0]["delta"]["tool_calls"][0]["id"], "discover-1")
        body["messages"].extend([dict(role="assistant", content=None, tool_calls=[tool]), dict(role="tool", tool_call_id="discover-1", content='{"entities": []}')])
        self.assertEqual(self.request(self.api, "/v1/chat/completions", body, auth=True)[0], 200)
        self.assertEqual(calls[1]["messages"][-1]["tool_call_id"], "discover-1")
        self.assertEqual(calls[1]["tools"], body["tools"])

    def test_native_integration_chat_and_tool_roundtrip(self):
        body = dict(model="assist-auto", messages=[dict(role="user", content="Lights on")],
                    tools=[dict(type="function", function=dict(name="HassTurnOn", parameters=dict(type="object")))])
        code, data, headers = self.request(self.api, "/v1/chat/completions", body, auth=True)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(data)["choices"][0]["message"]["content"], "OK")
        self.assertEqual(headers["X-Router-Provider"], "a")
        tool = dict(id="tool-1", type="function", function=dict(name="HassTurnOn", arguments='{"name":"lamp"}'))
        def answer(p, payload, timeout):
            result = response()
            result["choices"][0]["message"] = dict(role="assistant", content=None, tool_calls=[tool])
            result["choices"][0]["finish_reason"] = "tool_calls"
            return result
        self.state.router.call = answer
        code, data, _ = self.request(self.api, "/v1/chat/completions", {**body, "stream": True}, auth=True)
        self.assertEqual(code, 200)
        chunks = [json.loads(line[6:]) for line in data.decode().splitlines() if line.startswith("data:") and "[DONE]" not in line]
        self.assertEqual(chunks[0]["choices"][0]["delta"]["tool_calls"][0]["function"]["name"], "HassTurnOn")
        self.assertTrue(data.endswith(b"data: [DONE]\n\n"))

    def test_openai_client_can_discover_models_and_parse_buffered_sse(self):
        from openai import OpenAI
        with OpenAI(base_url=f"http://127.0.0.1:{self.api.server_port}/v1", api_key=self.state.token, max_retries=0) as client:
            self.assertIn("assist-auto", [m.id for m in client.models.list()])
            stream = client.chat.completions.create(model="assist-auto", messages=[dict(role="user", content="Hi")], stream=True)
            chunks = list(stream)
            self.assertEqual(chunks[0].choices[0].delta.content, "OK")
            self.assertEqual(chunks[-1].usage.total_tokens, 10)

    def test_static_paths_are_allowlisted(self):
        self.assertEqual(self.request(self.admin, "/../server.py")[0], 404)
        self.assertEqual(self.request(self.admin, "/app.js")[0], 200)
        self.assertIn(b"Assist AI Router", self.request(self.admin, "/")[1])

    def test_real_pinned_litellm_sdk_against_local_upstream(self):
        received = []
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                result = json.dumps(response()).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(result)))
                self.end_headers()
                self.wfile.write(result)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            p = profile("a", preset="openai_compatible", model="openai/test-model", api_base=f"http://127.0.0.1:{server.server_port}/v1")
            tools = [dict(type="function", function=dict(name="HassTurnOn", parameters=dict(type="object", properties={}))) ]
            result = completion(p, dict(messages=[dict(role="user", content="Hello")], tools=tools, max_tokens=8), 5)
            self.assertEqual(result["usage"]["total_tokens"], 10)
            self.assertEqual(received[0]["tools"], tools)
            self.assertFalse(received[0].get("stream", False))
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
