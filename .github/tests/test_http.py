import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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
