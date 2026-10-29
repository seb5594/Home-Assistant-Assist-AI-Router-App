# Assist AI Router

**Experimental AI provider routing for Home Assistant Assist, powered by LiteLLM.**

Version **2026-10-29** · LiteLLM **1.106.4** · amd64 / aarch64 · Home Assistant **2026.8+**

Connect multiple providers to one local OpenAI-compatible endpoint. Configure profiles in ingress, order them by priority, choose a routing preset, and inspect token usage without editing text files. Connect through Home Assistant's **native LiteLLM integration**.

* 21 provider templates, editable model catalog and support for local/OpenAI-compatible servers.
* Priority, quota-aware, round-robin and local-first policies; custom model-alias/tool rules.
* Automatic fallback, persistent cooldowns, shared-account limits and atomic token reservations.
* Input/output token counts, per-attempt history, request IDs and CSV export.
* App-option synchronization, preserved existing `!secret` references, German/English UI.
* Pause/resume providers without losing credentials, priority, rules or usage.
* Guided HACS MCP Assist setup with its correct server URL, router key and model.
* Fetch model lists directly from supported providers using entered keys or saved secrets; retain SDK suggestions as an alternative.
* Guided LiteLLM/Assist and optional MCP setup, stable-release checks and digest-pinned upstream image.

Install the app, open its web UI, add/test providers, and follow **Connect Assist**. Select **assist-auto** in the LiteLLM conversation agent, enable the desired Assist tools, and assign it to your voice assistant. No separate LiteLLM server or custom integration is needed.

Quotas shown are locally observed usage against limits you configure, not verified provider balances. Provider templates do not guarantee free access. Exhausted quotas across every available provider can still cause a failed request; a local model improves availability. Prompts and completions are not stored.

[Full English guide](assist_ai_router/DOCS.en.md) · [Deutsche Anleitung](assist_ai_router/DOCS.md) · [Development and acceptance checks](CONTRIBUTING.md)

[Connect HACS MCP Assist](assist_ai_router/MCP_ASSIST.en.md) · [MCP Assist auf Deutsch](assist_ai_router/MCP_ASSIST.md)
