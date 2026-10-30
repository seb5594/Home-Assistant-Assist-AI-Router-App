# Changelog

## 1.0.0

* Switch app versioning to MAJOR.MINOR.PATCH; retain the experimental stage.
* Show providers in numbered vertical lists with drag-and-drop and accessible move buttons, saving order immediately.
* Keep !secret references visible while typing their prefix; restore password masking on any mismatch.
* Automatically fetch provider models on editor opening and completed credential changes; show suggestions directly in LLM model with SDK/manual fallback, removing the separate load button and picker.
* Add navigation, provider and action icons and color the footer heart red.
* Expand German and English READMEs to cover installation, all provider templates, configuration, quotas, routing, Assist/MCP and operational limits.

* Link the updated developer credit to the project repository.
* Add a More Home Assistant Apps button beside Support my work ☕ in the ingress footer.

## 2026-10-29

* Pause and resume provider profiles directly from overview and provider cards, preserving credentials, priority, rules and usage. Paused profiles stay paused across restarts until resumed; already running requests finish normally.
* Add a German/English setup path for the HACS MCP Assist integration: HACS repository link, integration form, correctly normalized OpenAI-compatible server URL, router credential and model/timeout copy fields.
* Document MCP Assist installation, entity permissions, token-saving settings and troubleshooting without editing HA files or sending credentials through links.
* Load model lists directly from supported providers using draft API keys or saved secret references. Add a provider-result picker, bounded pagination and clearly separate SDK suggestions; never follow redirects with credentials.
* Add the requested developer credit and PayPal support link to the ingress footer.

## 2026-10-27

* First experimental Assist AI Router app, powered by LiteLLM 1.106.4.
* Ingress UI in German and English, 21 provider templates, editable models and ordered profiles.
* Priority, quota, round-robin and local-first policies; custom alias/tool rules.
* Shared-account quotas, atomic reservations, persistent cooldowns and per-attempt token usage.
* Supervisor option synchronization with preserved !secret references and conflict detection.
* Guided native Home Assistant LiteLLM/Assist and optional MCP setup.
* Separate authenticated chat API, buffered SSE and opt-in stable-release checks.
