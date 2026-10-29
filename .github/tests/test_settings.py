import copy
import json
import tempfile
import unittest
from unittest.mock import patch

from test_router import DEFAULTS, Settings, profile
from app.settings import ConfigError, Supervisor, normalize


class FakeSupervisor:
    def __init__(self):
        self.raw = {**copy.deepcopy(DEFAULTS), "providers": [profile("a", api_key="!secret groq_key")]}
        self.saved = None
        self.fail = False

    def read(self):
        resolved = copy.deepcopy(self.raw)
        for p in resolved["providers"]:
            if p["api_key"].startswith("!secret "):
                p["api_key"] = "RESOLVED-PRIVATE-KEY"
        return copy.deepcopy(self.raw), resolved, "router-internal"

    def save(self, raw):
        if self.fail:
            raise ConfigError("supervisor_unavailable")
        self.saved = copy.deepcopy(raw)
        self.raw = copy.deepcopy(raw)


class Configuration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.supervisor = FakeSupervisor()
        self.settings = Settings(self.tmp.name, self.supervisor)

    def tearDown(self):
        self.tmp.cleanup()

    def editable(self):
        cfg = self.settings.view()["options"]
        for p in cfg["providers"]:
            p.pop("api_key_set")
            p.pop("api_key_reference")
        return cfg

    def test_secret_is_never_exposed_to_ui_and_reference_survives_edit(self):
        view = self.settings.view()
        self.assertNotIn("RESOLVED-PRIVATE-KEY", json.dumps(view))
        self.assertEqual(view["options"]["providers"][0]["api_key_reference"], "!secret groq_key")
        cfg = self.editable()
        cfg["providers"][0]["name"] = "Changed name"
        self.settings.save(cfg, view["revision"])
        self.assertEqual(self.supervisor.saved["providers"][0]["api_key"], "!secret groq_key")
        self.assertEqual(self.settings.snapshot()["providers"][0]["api_key"], "RESOLVED-PRIVATE-KEY")

    def test_pausing_preserves_supervisor_secret_reference_and_rules(self):
        self.supervisor.raw["rules"] = [dict(name="Selected", alias="assist-selected", require_tools=False, provider_ids="a")]
        self.settings.reload()
        for enabled in (False, True):
            cfg = self.editable()
            cfg["providers"][0]["enabled"] = enabled
            self.settings.save(cfg, self.settings.revision())
            self.settings.reload()
            self.assertEqual(self.supervisor.saved["providers"][0]["api_key"], "!secret groq_key")
            self.assertEqual(self.settings.snapshot()["providers"][0]["enabled"], enabled)
            self.assertEqual(self.settings.snapshot()["rules"], cfg["rules"])

    def test_literal_key_is_masked_and_blank_omission_preserves_it(self):
        self.supervisor.raw["providers"][0]["api_key"] = "LITERAL-PRIVATE"
        self.settings.reload()
        self.assertNotIn("LITERAL-PRIVATE", json.dumps(self.settings.view()))
        cfg = self.editable()
        self.settings.save(cfg, self.settings.revision())
        self.assertEqual(self.supervisor.saved["providers"][0]["api_key"], "LITERAL-PRIVATE")

    def test_explicit_key_clear_and_key_replacement(self):
        for key in ("", "new-key", "!secret another_key"):
            cfg = self.editable()
            cfg["providers"][0]["api_key"] = key
            self.settings.save(cfg, self.settings.revision())
            self.assertEqual(self.supervisor.saved["providers"][0]["api_key"], key)

    def test_ha_form_edits_cause_conflict_instead_of_lost_update(self):
        revision = self.settings.revision()
        cfg = self.editable()
        self.supervisor.raw["routing"] = "quota"
        with self.assertRaisesRegex(ConfigError, "config_conflict"):
            self.settings.save(cfg, revision)
        self.assertEqual(self.settings.snapshot()["routing"], "quota")

    def test_supervisor_save_failure_does_not_activate_unsaved_config(self):
        cfg = self.editable()
        cfg["routing"] = "round_robin"
        self.supervisor.fail = True
        with self.assertRaises(ConfigError):
            self.settings.save(cfg, self.settings.revision())
        self.assertEqual(self.settings.snapshot()["routing"], "priority")

    def test_raw_and_resolved_supervisor_endpoints_and_payload(self):
        client = Supervisor("fake-token")
        calls = []
        def request(path, data=None):
            calls.append((path, data))
            return {"options": {"language": "en"}, "hostname": "test"} if path.endswith("info") else {"language": "en"}
        with patch.object(client, "request", request):
            client.read()
            client.save({"language": "en"})
        self.assertEqual(calls[0][0], "/addons/self/info")
        self.assertEqual(calls[1][0], "/addons/self/options/config")
        self.assertEqual(calls[2], ("/addons/self/options", {"options": {"language": "en"}}))

    def test_supervisor_errors_are_redacted(self):
        with patch("urllib.request.urlopen", side_effect=ValueError("secret in error")):
            with self.assertRaisesRegex(ConfigError, "^supervisor_unavailable$"):
                Supervisor("secret").read()

    def test_validation_blocks_invalid_types_urls_and_reserved_metadata(self):
        samples = [dict(max_attempts=True), dict(request_timeout=0), dict(allow_paid="yes"),
                   dict(providers=[profile("a"), profile("a")]), dict(providers=[profile("a", api_key="os.environ/SECRET")]),
                   dict(providers=[profile("a", api_base="http://supervisor")]),
                   dict(providers=[profile("a", api_base="https://user:pass@example.com")]),
                   dict(providers=[profile("a", api_base="file:///etc/passwd")]), dict(unrecognized="value")]
        for changes in samples:
            with self.subTest(changes=changes), self.assertRaises(ConfigError):
                normalize({**copy.deepcopy(DEFAULTS), **changes})

    def test_local_dev_refuses_unresolved_secrets(self):
        local = Settings(self.tmp.name)
        with self.assertRaisesRegex(ConfigError, "unresolved_secret"):
            local.save(self.supervisor.raw, local.revision())

    def test_local_config_roundtrip_is_immediate_and_durable(self):
        local = Settings(self.tmp.name)
        local.save({**copy.deepcopy(DEFAULTS), "providers": [profile("a")]}, local.revision())
        self.assertEqual(Settings(self.tmp.name).snapshot()["providers"][0]["api_key"], "key-a")

    def test_failed_secret_reload_preserves_active_config(self):
        previous = self.settings.snapshot()
        raw = copy.deepcopy(self.supervisor.raw)
        with patch.object(self.supervisor, "read", return_value=(raw, raw, "test-host")):
            with self.assertRaisesRegex(ConfigError, "unresolved_secret"):
                self.settings.reload()
        self.assertEqual(self.settings.snapshot(), previous)


if __name__ == "__main__":
    unittest.main()
