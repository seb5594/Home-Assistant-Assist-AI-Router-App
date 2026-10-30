import json
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "assist_ai_router"
sys.path.insert(0, str(APP))


class Packaging(unittest.TestCase):
    def test_version_pin_and_stable_metadata(self):
        from app.catalog import LITELLM_VERSION, VERSION
        cfg = yaml.safe_load((APP / "config.yaml").read_text(encoding="utf-8"))
        self.assertEqual(cfg["version"], VERSION)
        self.assertEqual(cfg["stage"], "stable")
        self.assertEqual(cfg["arch"], ["amd64", "aarch64"])
        self.assertEqual(cfg["homeassistant"], "2026.8.0")
        docker = (APP / "Dockerfile").read_text()
        self.assertIn("ARG BUILD_VERSION=" + VERSION, docker)
        self.assertIn("ghcr.io/berriai/litellm:v" + LITELLM_VERSION, docker)
        self.assertEqual(cfg["ports"]["8000/tcp"], None)
        self.assertNotIn("8099/tcp", cfg["ports"])
        self.assertFalse(cfg.get("hassio_api", False))
        self.assertFalse(cfg.get("homeassistant_api", False))

    def test_translations_match_and_cover_static_js_keys(self):
        words = json.loads((APP / "app/static/i18n.json").read_text(encoding="utf-8"))
        self.assertEqual(set(words["de"]), set(words["en"]))
        script = (APP / "app/static/app.js").read_text(encoding="utf-8")
        keys = set(re.findall(r"\bt\('([a-z_]+)'\)", script))
        self.assertFalse(keys - set(words["en"]), keys - set(words["en"]))
        self.assertNotIn("innerHTML", script)
        self.assertNotIn("localStorage", script)

    def test_all_settings_have_supervisor_translations(self):
        from app.catalog import DEFAULTS, PROVIDER_DEFAULTS
        for lang in ("de", "en"):
            translated = yaml.safe_load((APP / "translations" / (lang + ".yaml")).read_text(encoding="utf-8"))["configuration"]
            self.assertEqual(set(translated), set(DEFAULTS))
            self.assertEqual(set(translated["providers"]["fields"]), set(PROVIDER_DEFAULTS) | {"id"})


if __name__ == "__main__":
    unittest.main()
