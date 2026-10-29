import io
import json
import tempfile
import threading
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from test_router import Settings
from test_settings import FakeSupervisor
from app.discovery import discover, endpoint, read_json
from app.router import GatewayError
from app.settings import ConfigError


def profile(preset="groq", **changes):
    return dict(preset=preset, prefix=preset, api_base="", api_key="private-test-key", **changes)


class ModelDiscovery(unittest.TestCase):
    def test_live_openai_compatible_models_are_prefixed_and_sorted(self):
        calls = []
        def fetch(url, headers, timeout):
            calls.append((url, headers, timeout))
            return {"data": [{"id": "Z-model"}, {"id": "a-model"}, {"id": "a-model"}, {"id": "old", "active": False}]}
        result = discover(profile(), fetch)
        self.assertEqual(result["models"], ["groq/a-model", "groq/Z-model"])
        self.assertEqual(result["source"], "provider")
        self.assertTrue(result["complete"])
        self.assertEqual(calls[0][0], "https://api.groq.com/openai/v1/models")
        self.assertEqual(calls[0][1]["Authorization"], "Bearer private-test-key")
        self.assertNotIn("private-test-key", json.dumps(result))

    def test_gemini_uses_header_auth_filters_chat_and_follows_pages(self):
        calls = []
        def fetch(url, headers, timeout):
            calls.append((url, headers))
            if len(calls) == 1:
                return {"models": [{"name": "models/embed", "supportedGenerationMethods": ["embedContent"]}, {"name": "models/flash", "supportedGenerationMethods": ["generateContent"]}], "nextPageToken": "next/page"}
            return {"models": [{"name": "models/pro", "supportedGenerationMethods": ["generateContent"]}]}
        result = discover(profile("gemini"), fetch)
        self.assertEqual(result["models"], ["gemini/flash", "gemini/pro"])
        self.assertIn("pageToken=next%2Fpage", calls[1][0])
        self.assertEqual(calls[0][1]["x-goog-api-key"], "private-test-key")
        self.assertNotIn("private-test-key", calls[0][0])

    def test_anthropic_auth_pagination_and_cohere_chat_filter(self):
        calls = []
        def fetch(url, headers, timeout):
            calls.append((url, headers))
            return {"data": [{"id": "claude-1"}], "has_more": len(calls) == 1, "last_id": "claude-1"}
        self.assertEqual(discover(profile("anthropic"), fetch)["models"], ["anthropic/claude-1"])
        self.assertIn("after_id=claude-1", calls[1][0])
        self.assertEqual(calls[0][1]["x-api-key"], "private-test-key")
        self.assertEqual(calls[0][1]["anthropic-version"], "2023-06-01")
        seen = []
        def cohere(url, headers, timeout):
            seen.append(url)
            return {"models": [{"name": "command-a"}], "next_page_token": "again"} if len(seen) == 1 else {"models": [{"name": "command-r"}]}
        self.assertEqual(discover(profile("cohere_chat"), cohere)["models"], ["cohere_chat/command-a", "cohere_chat/command-r"])
        self.assertIn("endpoint=chat", seen[0])
        self.assertIn("page_token=again", seen[1])

    def test_ollama_and_custom_endpoints_do_not_require_a_key(self):
        p = profile("ollama_chat")
        p.update(api_base="http://localhost:11434", api_key="")
        seen = []
        def fetch(url, headers, timeout):
            seen.append((url, headers))
            return {"models": [{"name": "llama3.2:latest"}]}
        self.assertEqual(discover(p, fetch)["models"], ["ollama_chat/llama3.2:latest"])
        self.assertEqual(seen[0][0], "http://localhost:11434/api/tags")
        self.assertNotIn("Authorization", seen[0][1])
        custom = profile("openai_compatible")
        custom.update(prefix="openai", api_base="http://localhost:8000/v1/", api_key="")
        result = discover(custom, lambda url, *_: {"data": [{"id": "my-model"}]})
        self.assertEqual(result["models"], ["openai/my-model"])

    def test_openrouter_model_ids_keep_their_own_namespace(self):
        result = discover(profile("openrouter"), lambda *_: {"data": [{"id": "openrouter/free"}, {"id": "meta-llama/test"}]})
        self.assertIn("openrouter/openrouter/free", result["models"])
        self.assertIn("openrouter/meta-llama/test", result["models"])

    def test_unsupported_provider_missing_key_empty_and_invalid_responses(self):
        for preset in ("azure", "cloudflare", "github", "fireworks_ai", "perplexity"):
            with self.subTest(preset=preset), self.assertRaises(GatewayError) as error:
                discover(profile(preset), lambda *_: self.fail("No request for unsupported discovery"))
            self.assertEqual(error.exception.code, "model_discovery_unsupported")
        p = profile()
        p["api_key"] = ""
        with self.assertRaises(GatewayError) as error:
            endpoint(p)
        self.assertEqual(error.exception.code, "model_discovery_key_required")
        for response, code in (({"data": []}, "model_discovery_empty"), ({"error": "private-test-key"}, "model_discovery_invalid_response")):
            with self.assertRaises(GatewayError) as error:
                discover(profile(), lambda *_: response)
            self.assertEqual(error.exception.code, code)

    def test_repeated_cursors_and_page_caps_are_marked_partial(self):
        calls = []
        def fetch(*_):
            calls.append(1)
            return {"models": [{"name": "models/flash", "supportedGenerationMethods": ["generateContent"]}], "nextPageToken": "same"}
        self.assertFalse(discover(profile("gemini"), fetch)["complete"])
        self.assertEqual(len(calls), 2)

    def test_http_errors_never_echo_provider_messages_or_credentials(self):
        for status, code in ((401, "model_discovery_auth_error"), (403, "model_discovery_auth_error"), (429, "model_discovery_rate_limited"), (404, "model_discovery_unsupported"), (500, "model_discovery_unavailable")):
            failure = urllib.error.HTTPError("https://provider.invalid", status, "private-key", {}, io.BytesIO(b'private-key'))
            with patch("urllib.request.OpenerDirector.open", side_effect=failure), self.assertRaises(GatewayError) as error:
                read_json("https://provider.invalid/models", {"Authorization": "Bearer private-key"}, 1)
            self.assertEqual(error.exception.code, code)
            self.assertNotIn("private-key", str(error.exception))

    def test_redirects_do_not_forward_credentials(self):
        called = []
        class Redirect(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                called.append(self.path)
                self.send_response(302)
                self.send_header("Location", "/unexpected-destination")
                self.end_headers()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(GatewayError):
                read_json(f"http://127.0.0.1:{server.server_port}/models", {"Authorization": "Bearer private-key"}, 1)
            self.assertEqual(called, ["/models"])
        finally:
            server.shutdown()
            server.server_close()

    def test_actual_http_model_list_uses_the_draft_key_and_custom_base(self):
        requests = []
        class Provider(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                requests.append((self.path, self.headers.get("Authorization")))
                raw = json.dumps({"data": [{"id": "actual-model"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Provider)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            p = profile("openai_compatible")
            p.update(prefix="openai", api_base=f"http://127.0.0.1:{server.server_port}/v1")
            result = discover(p)
            self.assertEqual(result["models"], ["openai/actual-model"])
            self.assertEqual(requests, [("/v1/models", "Bearer private-test-key")])
            self.assertNotIn("private-test-key", json.dumps(result))
        finally:
            server.shutdown()
            server.server_close()

    def test_saved_secrets_are_resolved_only_for_the_saved_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            sup = FakeSupervisor()
            settings = Settings(tmp, sup)
            draft = dict(id="a", preset="groq", api_base="")
            revision = settings.revision()
            p = settings.discovery_profile(draft)
            self.assertEqual(p["api_key"], "RESOLVED-PRIVATE-KEY")
            self.assertEqual(settings.revision(), revision)
            self.assertIsNone(sup.saved)
            for changes in ({"api_base": "https://different.example/v1"}, {"preset": "openai"}):
                with self.assertRaisesRegex(ConfigError, "model_discovery_reenter_key"):
                    settings.discovery_profile({**draft, **changes})
            self.assertEqual(settings.discovery_profile({**draft, "api_key": "!secret groq_key"})["api_key"], "RESOLVED-PRIVATE-KEY")
            with self.assertRaisesRegex(ConfigError, "model_discovery_save_secret"):
                settings.discovery_profile({**draft, "api_key": "!secret new_secret"})
            self.assertEqual(settings.discovery_profile({**draft, "api_base": "https://new.example/v1", "api_key": "new-explicit-key"})["api_key"], "new-explicit-key")

    def test_unsaved_literal_credentials_work_without_saving_a_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(tmp)
            p = settings.discovery_profile(dict(id="new", preset="groq", api_key="draft-key"))
            self.assertEqual(p["api_key"], "draft-key")
            self.assertEqual(settings.snapshot()["providers"], [])
            with self.assertRaisesRegex(ConfigError, "model_discovery_save_secret"):
                settings.discovery_profile(dict(preset="groq", api_key="!secret new_key"))
            with self.assertRaises(ConfigError):
                settings.discovery_profile(dict(preset="groq", api_key="a\nb"))


if __name__ == "__main__":
    unittest.main()
