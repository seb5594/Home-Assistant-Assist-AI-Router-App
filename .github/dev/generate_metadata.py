"""Regenerate Supervisor schema and DE/EN form labels from runtime settings and UI dictionary."""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "assist_ai_router"))
from app.catalog import DEFAULTS, PROVIDER_DEFAULTS, VERSION  # noqa: E402


def schema(value):
    if type(value) is bool:
        return "bool"
    if type(value) is int:
        return "int(0,)"
    if type(value) is float:
        return "float(0,)"
    return "str"


def main():
    app = ROOT / "assist_ai_router"
    provider_schema = {"id": "str", **{k: schema(v) + "?" for k, v in PROVIDER_DEFAULTS.items()}}
    for key in ("name", "model", "preset"):
        provider_schema[key] = "str"
    provider_schema["api_key"] = "password?"
    rules = dict(name="str", alias="str", require_tools="bool", provider_ids="str")
    options_schema = {key: schema(value) for key, value in DEFAULTS.items()}
    options_schema.update(language="list(de|en)", routing="list(priority|quota|round_robin|local_first)",
                          providers=[provider_schema], rules=[rules])
    cfg = dict(name="Assist AI Router", version=VERSION, slug="assist_ai_router",
               description="Multi-provider AI gateway for Home Assistant Assist, powered by LiteLLM.",
               url="https://github.com/seb5594/Home-Assistant-Assist-AI-Router-App",
               arch=["amd64", "aarch64"], homeassistant="2026.8.0", stage="stable",
               startup="application", boot="auto", init=True, ingress=True, ingress_port=8099,
               panel_icon="mdi:routes", panel_title="Assist AI Router", ports={"8000/tcp": None},
               ports_description={"8000/tcp": "Optional authenticated OpenAI-compatible API (internal access works without publishing)"},
               options=DEFAULTS, schema=options_schema)
    (app / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    words = json.loads((app / "app/static/i18n.json").read_text(encoding="utf-8"))
    extra = {"de": {"language": "Sprache", "providers": "Anbieterprofile", "rules": "Eigene Routingregeln", "id": "Eindeutige Profil-ID", "provider_ids": "Erlaubte Profil-IDs, durch Komma getrennt"},
             "en": {"language": "Language", "providers": "Provider profiles", "rules": "Custom routing rules", "id": "Unique profile ID", "provider_ids": "Allowed profile IDs, comma separated"}}
    for lang, labels in words.items():
        labels = {**labels, **extra[lang]}
        def fields(mapping):
            result = {}
            for k, v in mapping.items():
                item = dict(name=labels.get(k, k))
                nested = v[0] if isinstance(v, list) else v
                if isinstance(nested, dict):
                    item["fields"] = fields(nested)
                result[k] = item
            return result
        translations = dict(configuration=fields(options_schema), network={"8000/tcp": dict(name=labels["base_url"])})
        (app / "translations").mkdir(exist_ok=True)
        (app / "translations" / f"{lang}.yaml").write_text(yaml.safe_dump(translations, sort_keys=False, allow_unicode=True), encoding="utf-8")


if __name__ == "__main__":
    main()
