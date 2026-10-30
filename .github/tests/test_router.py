import copy
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) > 2 else Path("/opt/router")
sys.path.insert(0, str(ROOT / "assist_ai_router"))
from app.catalog import DEFAULTS, PROVIDER_DEFAULTS
from app.ledger import Ledger, boundaries
from app.router import GatewayError, Router, estimate
from app.settings import Settings


def profile(pid, **options):
    return {**PROVIDER_DEFAULTS, "id": pid, "name": pid, "preset": "groq",
            "model": "groq/example", "api_key": "key-" + pid, "free_only": True, **options}


def response(tokens=10):
    return dict(id="chatcmpl-test", object="chat.completion", created=1, model="actual",
                choices=[dict(index=0, message=dict(role="assistant", content="OK"), finish_reason="stop")],
                usage=dict(prompt_tokens=tokens - 2, completion_tokens=2, total_tokens=tokens))


class UpstreamError(Exception):
    def __init__(self, status, headers=None):
        self.status_code = status
        self.response = type("Response", (), {"headers": headers or {}})()


class Routing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(self.tmp.name)
        self.ledger = Ledger(Path(self.tmp.name) / "usage.sqlite")
        self.configure([profile("a"), profile("b")])

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def configure(self, providers, **settings):
        cfg = {**copy.deepcopy(DEFAULTS), "providers": providers, **settings}
        self.settings.save(cfg, self.settings.revision())

    def run_request(self, call=None, **payload):
        return Router(self.settings, self.ledger, call or (lambda *a: response())).run(
            dict(model="assist-auto", messages=[dict(role="user", content="Hello")], **payload))

    def test_readme_rule_examples_match_first_rule_and_global_priority(self):
        rules = [
            dict(name="Devices", alias="assist-auto", require_tools=True, provider_ids="local,groq"),
            dict(name="Text", alias="assist-auto", require_tools=False, provider_ids="groq,gemini"),
            dict(name="Private", alias="assist-private", require_tools=False, provider_ids="local"),
            dict(name="Cloud", alias="assist-cloud", require_tools=False, provider_ids="gemini,groq"),
            dict(name="Catch all", alias="*", require_tools=False, provider_ids="groq,gemini")]
        self.configure([profile("local", local=True), profile("groq"), profile("gemini")], rules=rules)
        router = Router(self.settings, self.ledger)
        cfg = self.settings.snapshot()
        for alias, tools, expected in [("assist-auto", [{}], ["local", "groq"]),
                                       ("assist-auto", [], ["groq", "gemini"]),
                                       ("assist-private", [{}], ["local"]),
                                       ("assist-cloud", [], ["groq", "gemini"])]:
            payload = dict(model=alias, tools=tools, max_tokens=8, messages=[dict(role="user", content="Hi")])
            self.assertEqual([p["id"] for p in router.candidates(cfg, payload, 0)], expected)
        with self.assertRaisesRegex(GatewayError, "unknown_model"):
            router.candidates(cfg, dict(model="not-defined", tools=[], messages=[]), 0)

    def test_priority_and_actual_usage(self):
        result, meta = self.run_request()
        self.assertEqual(meta["provider"], "a")
        self.assertEqual(result["model"], "assist-auto")
        self.assertEqual(self.ledger.recent()[0]["tokens"], 10)
        self.assertEqual(self.ledger.recent()[0]["estimated"], 0)

    def test_paused_profiles_are_skipped_by_policies_rules_and_explicit_models(self):
        rules = [dict(name="Selected", alias="assist-selected", require_tools=False, provider_ids="a,b")]
        for policy in ("priority", "quota", "round_robin", "local_first"):
            self.configure([profile("a", enabled=False, local=True), profile("b")], routing=policy, rules=rules)
            called = []
            def call(p, *_):
                called.append(p["id"])
                return response()
            router = Router(self.settings, self.ledger, call)
            for alias in ("assist-auto", "assist-selected"):
                router.run(dict(model=alias, messages=[dict(role="user", content="Hi")]))
            self.assertEqual(called, ["b", "b"])
            self.assertNotIn("provider:a", router.models())
            with self.assertRaises(GatewayError):
                router.run(dict(model="provider:a", messages=[dict(role="user", content="Hi")]))

    def test_rate_limit_falls_back_and_honors_retry_after(self):
        called = []
        def call(p, *_):
            called.append(p["id"])
            if p["id"] == "a":
                raise UpstreamError(429, {"retry-after": "120"})
            return response()
        result, meta = self.run_request(call)
        self.assertEqual(called, ["a", "b"])
        self.assertEqual(meta["attempts"][0]["reason"], "rate_limited")
        self.assertGreaterEqual(self.ledger.health(profile("a"))["until"] - self.ledger.clock(), 119)
        self.run_request(call)
        self.assertEqual(called, ["a", "b", "b"])
        self.assertEqual(self.ledger.recent()[1]["request_id"], self.ledger.recent()[2]["request_id"])

    def test_shared_account_cooldown_survives_restart(self):
        profiles = [profile("a", api_key="shared"), profile("b", api_key="shared"), profile("c")]
        self.configure(profiles)
        called = []
        def call(p, *_):
            called.append(p["id"])
            if p["id"] == "a":
                raise UpstreamError(429)
            return response()
        _, meta = self.run_request(call)
        self.assertEqual(called, ["a", "c"])
        self.ledger.close()
        self.ledger = Ledger(Path(self.tmp.name) / "usage.sqlite")
        self.run_request(call)
        self.assertEqual(called, ["a", "c", "c"])

    def test_server_error_and_auth_error_fall_back(self):
        for code in (401, 403, 404, 500, 503):
            with self.subTest(code=code):
                self.ledger.set_health(profile("a"), "untested")
                _, meta = self.run_request(lambda p, *_: (_ for _ in ()).throw(UpstreamError(code)) if p["id"] == "a" else response())
                self.assertEqual(meta["provider"], "b")

    def test_invalid_request_is_not_retried_across_accounts(self):
        called = []
        def call(p, *_):
            called.append(p["id"])
            raise UpstreamError(400)
        with self.assertRaises(GatewayError) as raised:
            self.run_request(call)
        self.assertEqual(raised.exception.status, 400)
        self.assertEqual(called, ["a"])

    def test_tool_and_vision_capabilities_are_filtered_without_dropping_tools(self):
        self.configure([profile("a", supports_tools=False), profile("b", supports_vision=True)])
        tools = [dict(type="function", function=dict(name="HassTurnOn", parameters=dict(type="object")))]
        captured = []
        def call(p, payload, timeout):
            captured.append(payload)
            return response()
        _, meta = self.run_request(call, tools=tools)
        self.assertEqual(meta["provider"], "b")
        self.assertEqual(captured[0]["tools"], tools)
        payload = dict(model="assist-auto", messages=[dict(role="user", content=[dict(type="image_url", image_url={"url": "data:image/png;base64,AAA"})])])
        self.assertEqual(Router(self.settings, self.ledger, call).run(payload)[1]["provider"], "b")

    def test_context_window_output_cap_and_local_first(self):
        self.configure([profile("a", context_tokens=1), profile("b", local=True)], routing="local_first", max_output_tokens=16)
        def call(p, body, timeout):
            self.assertEqual(body["max_tokens"], 16)
            self.assertLessEqual(timeout, 12)
            return response()
        self.assertEqual(self.run_request(call, max_completion_tokens=1000)[1]["provider"], "b")

    def test_paid_profiles_are_opt_in(self):
        self.configure([profile("a", free_only=False), profile("b")])
        self.assertEqual(self.run_request()[1]["provider"], "b")
        self.configure([profile("a", free_only=False)], allow_paid=True)
        self.assertEqual(self.run_request()[1]["provider"], "a")

    def test_rule_alias_restricts_targets(self):
        self.configure([profile("a"), profile("b")], rules=[dict(name="Fast", alias="assist-fast", require_tools=False, provider_ids="b")])
        router = Router(self.settings, self.ledger, lambda *a: response())
        self.assertIn("assist-fast", router.models())
        self.assertEqual(router.run(dict(model="assist-fast", messages=[dict(role="user", content="Hi")]))[1]["provider"], "b")
        with self.assertRaises(GatewayError):
            router.run(dict(model="unknown", messages=[dict(role="user", content="Hi")]))

    def test_provider_alias_never_silently_switches_models(self):
        router = Router(self.settings, self.ledger, lambda *a: (_ for _ in ()).throw(UpstreamError(429)))
        with self.assertRaises(GatewayError):
            router.run(dict(model="provider:a", messages=[dict(role="user", content="Hi")]))
        self.assertEqual(len(self.ledger.recent()), 1)

    def test_conditional_alias_cannot_escape_its_rule(self):
        self.configure([profile("a"), profile("b")], rules=[dict(name="Tools", alias="assist-tools", require_tools=True, provider_ids="b")])
        router = Router(self.settings, self.ledger, lambda *a: self.fail("Must not use unrestricted providers"))
        with self.assertRaises(GatewayError):
            router.run(dict(model="assist-tools", messages=[dict(role="user", content="Hi")]))

    def test_profile_reordering_also_changes_priority_within_rules(self):
        rules = [dict(name="Selected", alias="assist-auto", require_tools=False, provider_ids="a,b")]
        self.configure([profile("b"), profile("a")], rules=rules)
        self.assertEqual(self.run_request()[1]["provider"], "b")

    def test_round_robin_and_quota_selection(self):
        self.configure([profile("a"), profile("b")], routing="round_robin")
        router = Router(self.settings, self.ledger, lambda *a: response())
        body = dict(model="assist-auto", messages=[dict(role="user", content="Hi")])
        self.assertEqual([router.run(body)[1]["provider"] for _ in range(3)], ["a", "b", "a"])
        self.configure([profile("a", daily_tokens=100000), profile("b", daily_tokens=100000)], routing="quota")
        self.assertEqual(self.run_request()[1]["provider"], "b")

    def test_maximum_attempts_is_enforced(self):
        self.configure([profile("a"), profile("b")], max_attempts=1)
        with self.assertRaises(GatewayError):
            self.run_request(lambda *a: (_ for _ in ()).throw(UpstreamError(503)))
        self.assertEqual(len(self.ledger.recent()), 1)

    def test_output_hidden_upstream_fields_are_removed(self):
        def call(*_):
            return {**response(), "_hidden_params": {"api_key": "DO-NOT-LEAK"}}
        result, _ = self.run_request(call)
        self.assertNotIn("DO-NOT-LEAK", json.dumps(result))

    def test_invalid_payloads_are_rejected_before_provider_calls(self):
        router = Router(self.settings, self.ledger, lambda *a: self.fail("Must not call provider"))
        for body in (None, [], {}, {"messages": []}, {"messages": [1]}, {"messages": [{"role": "bad"}]},
                     {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": -1}):
            with self.subTest(body=body), self.assertRaises(GatewayError):
                router.run(body)

    def test_atomic_reservation_allows_only_one_parallel_request(self):
        p = profile("a", daily_requests=1)
        self.configure([p], reserve_percent=0)
        barrier = threading.Barrier(8)
        answers = []
        def reserve():
            barrier.wait()
            answers.append(self.ledger.reserve(p, "parallel", 10, 20, 0)[0])
        threads = [threading.Thread(target=reserve) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sum(value is not None for value in answers), 1)

    def test_shared_quota_group_blocks_second_key_and_survives_crash(self):
        a, b = profile("a", quota_group="account", tpm=100), profile("b", quota_group="account", tpm=100)
        self.assertIsNotNone(self.ledger.reserve(a, "1", 60, 10, 0)[0])
        self.assertEqual(self.ledger.reserve(b, "2", 60, 10, 0)[1], "tpm")
        self.ledger.close()
        self.ledger = Ledger(Path(self.tmp.name) / "usage.sqlite")
        self.assertEqual(self.ledger.recent()[0]["status"], "interrupted")
        self.assertEqual(self.ledger.usage(b)["minute"]["tokens"], 70)

    def test_monthly_budget_is_reserved_before_call(self):
        p = profile("a", monthly_budget=0.001, input_price=100, output_price=100)
        self.assertEqual(self.ledger.reserve(p, "1", 100, 100, 0)[1], "monthly_budget")

    def test_daily_rollover_and_history_never_remove_current_month_quota(self):
        clock = [1792530000.0]
        self.ledger.clock = lambda: clock[0]
        p = profile("a")
        self.ledger.reserve(p, "1", 10, 20, 0)
        clock[0] += 86400 * 3
        self.assertEqual(self.ledger.usage(p)["day"]["tokens"], 0)
        self.assertEqual(self.ledger.usage(p)["month"]["tokens"], 30)
        self.ledger.prune(1)
        self.assertEqual(self.ledger.usage(p)["month"]["tokens"], 30)

    def test_estimate_includes_tools_and_unicode(self):
        base = dict(messages=[dict(role="user", content="Hallo")])
        self.assertGreater(estimate({**base, "tools": [{"large": "ä" * 1000}]}), estimate(base))


if __name__ == "__main__":
    unittest.main()
