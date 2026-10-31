# Assist AI Router

**Multiple AI providers. One endpoint for Home Assistant Assist.**

[Deutsch](README.md) · [Detailed configuration](assist_ai_router/DOCS.en.md) · [MCP Assist](assist_ai_router/MCP_ASSIST.en.md) · [Changelog](assist_ai_router/CHANGELOG.md)

Assist AI Router combines cloud providers and local models behind an authenticated OpenAI-compatible endpoint. The app uses the included **LiteLLM SDK** for model requests and adds its own routing, usage accounting and ingress interface. Manage profiles, keys, models, priorities and limits in your browser. Saving writes to the app configuration and applies changes immediately.

**App v1.0.2 · LiteLLM 1.106.4 · Home Assistant 2026.8+ · amd64 / aarch64.** This release switches to `MAJOR.MINOR.PATCH` versioning. Previous calendar releases remain in the changelog.

## Features

- Up to **100 provider profiles**, each with a model, credential, endpoint and limits; multiple profiles per provider are supported.
- **Numbered vertical lists** on Overview and Providers. Reorder using the ⠿ drag handle or ↑/↓ buttons; changes save immediately.
- **Pause/resume** without losing keys, position, rules or usage.
- Automatically loaded model suggestions directly in the **LLM model** field, with SDK suggestions and manual entry as fallbacks.
- Four routing presets, custom alias/tool rules, provider fallback and persistent cooldowns.
- Local quota enforcement with reservations for concurrent requests, shared quota groups and a safety reserve.
- Input/output/total tokens, status, duration and request ID per API attempt, plus CSV export.
- Guided setup for the native **LiteLLM integration** or **HACS MCP Assist**.
- German/English interface, a pinned LiteLLM image tag/digest and an optional stable-release check.

This app exposes the settings documented here. It does not expose every feature of the full LiteLLM proxy administration system: teams, LiteLLM virtual keys, external billing and all SDK/proxy parameters are not available as app options.

## Installation and quick start

1. Open the [Home Assistant app repository link](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fseb5594%2FHome-Assistant-Apps), or add `https://github.com/seb5594/Home-Assistant-Apps` in the app store repository settings. A Home Assistant installation with Supervisor/app support is required.
2. Install/start **Assist AI Router** and open its web UI. LiteLLM is included; no separate proxy installation is necessary.
3. Under **Providers**, select a template and name the profile. Enter a key or existing `!secret` reference; custom/local servers also need a reachable API base URL.
4. Choose an **LLM model** suggestion or enter the full model name with its LiteLLM provider prefix. Save and test.
5. Add independent fallback providers, sort them, and choose a **Routing** preset. **Fixed priority** is the default.
6. Follow **Connect Assist** and use **`assist-auto`** for normal Assist requests.

**Test connection** sends a short real model request. It can consume tokens, request allowances and potentially money. A text response does not prove tool-calling quality or device-control reliability.

## Provider templates and models

| Template | LiteLLM prefix | Direct model listing |
| --- | --- | --- |
| Google AI Studio / Gemini | `gemini/` | Yes |
| Groq | `groq/` | Yes |
| Cerebras | `cerebras/` | Yes |
| OpenRouter | `openrouter/` | Yes |
| Mistral / La Plateforme | `mistral/` | Yes |
| Hugging Face Inference | `huggingface/` | Yes |
| GitHub Models | `github/` | SDK / manual |
| SambaNova | `sambanova/` | Yes |
| Together AI | `together_ai/` | Yes |
| Fireworks AI | `fireworks_ai/` | SDK / manual |
| Cohere | `cohere_chat/` | Yes |
| Cloudflare Workers AI | `cloudflare/` | SDK / manual |
| NVIDIA NIM | `nvidia_nim/` | Yes |
| OpenAI | `openai/` | Yes |
| Anthropic | `anthropic/` | Yes |
| DeepSeek | `deepseek/` | Yes |
| xAI | `xai/` | Yes |
| Perplexity | `perplexity/` | SDK / manual |
| Azure OpenAI | `azure/` | SDK / manual; check deployment/API version |
| Ollama | `ollama_chat/` | Yes, from the local server |
| OpenAI-compatible / vLLM / llama.cpp | `openai/` | If the server provides a model endpoint |

These **21 templates** do not guarantee free access. Account permissions, model IDs, pricing, API versions and tool capabilities must match. Some providers require a custom account/deployment URL. Configure separate profiles for multiple models using the same key.

### Automatic suggestions inside the model field

Opening a provider editor automatically loads its model list using saved credentials. After entering a new key or API URL, leaving that field triggers an update. Public model endpoints and local servers may work without a key. There is no separate load button or second model picker.

Results appear as suggestions **inside the LLM model field**. Use ▾ beside the model input to open all loaded models, even with an existing saved name. Typing filters the list; ↑/↓ and Enter select an entry. Escape closes the list. LiteLLM prefixes are added automatically. The existing value is not silently replaced, and manual names remain supported.

Discovery reads metadata without generating a prompt or changing token counters. Providers may rate-limit metadata requests. Pagination, response size and time are bounded; partial lists are labeled. If discovery fails, available SDK suggestions and manual entry remain. A listed model does not guarantee free pricing, account access or chat/tool support.

New literal keys work before saving. New `!secret` references must first be saved with a model name so Supervisor can resolve them. Saved keys are not reused for a changed destination until you re-enter the key or explicitly save the changed profile.

### API plans, account data and documented limit examples

The provider editor shows documented plan options and, for supported official endpoints, live account data. Checked **2026-10-30**. Documented plan options do not identify your account. A consumer chat subscription does not automatically include API usage.

| Provider | Documented information | Source |
| --- | --- | --- |
| Google AI Studio | Project/model-specific RPM, TPM and RPD; check AI Studio. | [Docs](https://ai.google.dev/gemini-api/docs/rate-limits) |
| Groq | Free examples for gpt-oss-20b/120b: 30 RPM, 1,000 RPD, 8,000 TPM, 200,000 TPD. Organization limits may differ. | [Docs](https://console.groq.com/docs/rate-limits) |
| Cerebras | Trial examples gpt-oss-120b/qwen-3.8-27b: 5 RPM, 30,000 uncached TPM, 1,000,000 TPD. Separate hourly/total-token limits apply. Trial credits expire; not a permanent free tier. | [Docs](https://inference-docs.cerebras.ai/support/rate-limits) |
| OpenRouter | API key metadata can report free-tier status, credit cap and daily free-model requests; no universal token cap. | [Docs](https://openrouter.ai/docs/api_reference/limits) |
| Mistral / La Plateforme | Organization/model-specific limits; check the Limits page. Consumer subscriptions do not establish API allowance. | [Docs](https://docs.mistral.ai/admin/billing-usage/usage-limits) |
| Hugging Face Inference | Published monthly credits: Free $0.10 (subject to change), PRO $2, organizations $2/seat. Monetary credits are not fixed tokens or verified remaining balance. | [Docs](https://huggingface.co/docs/inference-providers/pricing) |
| SambaNova | Check account credits and current plan; the Free plan page asks for purchased credits before API use. No free token allowance assumed. | [Docs](https://cloud.sambanova.ai/plans) |
| Cohere | Trial: 1,000 API calls/month; selected chat models 20 RPM. Monthly requests are not tokens or daily allowance. | [Docs](https://docs.cohere.com/docs/rate-limits) |
| Cloudflare Workers AI | 10,000 Neurons/day free allocation; neurons cannot be converted into a universal token allowance. Some models require paid access. | [Docs](https://developers.cloudflare.com/workers-ai/platform/pricing/) |
| NVIDIA NIM | Developer access is for prototyping. No reliably documented universal token quota is prefilled. | [Docs](https://docs.api.nvidia.com/nim/docs/product) |
| DeepSeek | The balance endpoint reports available/granted/purchased funds, not a subscription tier or fixed token balance. | [Docs](https://api-docs.deepseek.com/api/get-user-balance/) |

Other templates retain an unknown plan where a normal API key does not expose a supported account endpoint. Keys bound to custom proxy URLs are not forwarded to another host for account checks. No login pages are scraped or probe prompts generated to identify plans.

OpenRouter can return free-tier status, remaining key spending cap and, where supplied, daily free-model requests. DeepSeek reports available, granted and purchased funds. Account metadata is cached for up to five minutes and kept separate from local router counters. Money is never converted to tokens. Local limits and cost permissions never change automatically. Matching Groq/Cerebras models offer **Apply documented limit example**: compare with your actual account, then save. Additional hourly and other unrepresented restrictions remain enforced by the provider.

## Order, pauses and credentials

Position numbers represent the **saved profile order**, including paused profiles. Drag the ⠿ handle before/after a profile or use the arrow buttons. **Fixed priority** uses this order; other presets may sort differently. Overview also displays profiles vertically.

**Pause** excludes a profile from new model requests. Already running calls may finish. Pauses survive restarts until manually resumed. Credentials, rules, position and usage remain intact; resuming does not clear limits or cooldowns. Editing a paused profile may still fetch its model metadata.

Literal API keys are initially masked and can be revealed with Show/hide. An input starting with `!` becomes visible while it follows the `!secret` marker: `!`, `!s`, `!se`, `!sec`, `!secr`, `!secre`, `!secret`, then `!secret name`. A deviation such as `!sx` or `!secretX` immediately restores password masking.

`!secret name` references an **existing** Home Assistant secret. The app cannot create entries in HA's secrets file; direct key entry requires no text file. Opening a profile fetches its original saved entry through a dedicated ingress endpoint. A `!secret` remains a reference; its resolved value is never returned. Literal keys are initially masked and can be revealed with Show/hide. Secret references are recommended. Leave the key field empty when editing to keep its current credential; **Remove saved key** clears it explicitly.

Web changes are saved through Supervisor to the app options, preserving raw secret references. Changes from HA's **Configuration** tab load when refreshing settings or restarting. Revision checking prevents a stale web view from silently overwriting newer data. Refresh after a conflict and reapply changes; avoid simultaneous editing in multiple interfaces.

## Routing and fallback

| Preset | Selection |
| --- | --- |
| Fixed priority | Eligible profiles in saved order |
| Preserve quotas | Sorts by the highest consumed fraction of known limits; unknown limits use a fraction of 1.0 |
| Spread requests | Rotates the starting point on each request |
| Local first | Local profiles before allowed cloud profiles, preserving saved order within each group |

Before an attempt, the router checks enabled state, cost permission, tool/image support, context size, local limits and cooldowns. With paid profiles disabled globally, only profiles marked free or local are eligible. These are manual permissions, not tariff checks or a guarantee against provider billing.

**Custom rules** select an allowed set of profiles by model alias and optionally the presence of tools. The first matching rule wins. The preset sorts inside that set; fallbacks cannot leave it. `*` is a catch-all for routing aliases. The order of IDs within a rule does not create a separate priority.

**`assist-auto`** is the default router alias. Custom aliases also appear in `/v1/models`. **`provider:<profile-id>`** targets exactly one active profile without fallback, while still enforcing capability, cost and quota restrictions. Use a routing alias for resilience.

429, authentication failures, missing models, network/timeouts and server errors can trigger fallback. `Retry-After` extends cooldowns; shared quota groups share 429 cooldowns. Generally rejected requests are not blindly retried. Context errors can try another eligible model. Messages and tool definitions are not truncated.

**Examples:** For free-first routing, confirm checked free access on independent accounts, enter limits and use Fixed priority. For local-first routing, add a tool-capable local server and choose Local first. For separate Assist requirements, define an alias such as `assist-home` with a tool condition and suitable profiles.

Attempts and time budgets are bounded. If all allowed providers are exhausted or unavailable, the API returns **HTTP 503 / `no_provider_available`**. A local fallback can improve availability; unlimited cloud answers cannot be guaranteed.

### Concrete rules to recreate in the UI

Assume this global profile order: **1. Local**, **2. Groq**, **3. Gemini**. Start with **Fixed priority** and enter these under **Routing → Custom rules**. Profile names refer to your actual profiles.

| Order | Rule name | Alias | Require tools | Allowed profiles | Result |
| --- | --- | --- | --- | --- | --- |
| 1 | Assist with devices | `assist-auto` | Yes | Local, Groq | Requests carrying tools try Local, then Groq. |
| 2 | Assist text | `assist-auto` | No | Groq, Gemini | Requests without tools try Groq, then Gemini. |
| 3 | Private local | `assist-private` | No | Local | Local only; unavailable local models do not cause cloud fallback. |
| 4 | Cloud text | `assist-cloud` | No | Groq, Gemini | A separate selectable model for cloud requests with fallback. |

Require tools = No means **no condition**, not “tools forbidden.” Put the tool rule before the general `assist-auto` rule. The private set prevents cloud fallback. Cost permissions still apply.

An optional **catch-all rule** with alias `*`, no tool condition and Groq/Gemini belongs last. It applies only to already known routing aliases; it does not create arbitrary model names. It cannot expand a set chosen by an earlier matching rule. Direct `provider:` models bypass rules.

Checkbox selection order does not create a separate priority. Groq precedes Gemini because of global order. Other presets can change the starting profile. Rules do not inspect prompt text, schedules or keywords; supported conditions are alias, presence of tools and allowed profile set.

## Usage and quotas

The UI displays **locally observed usage through this router**, not universally verified provider balances. Other apps' usage is unknown. Provider portals are linked.

| Profile option | Meaning |
| --- | --- |
| RPM / TPM | Requests/tokens within a rolling 60-second window |
| Requests/day, tokens/day, tokens/month | Local limits; day/month rollover at 00:00 UTC |
| Context window | Conservative input estimate plus maximum output budget |
| Input/output prices | Manually entered USD per million tokens |
| Monthly budget | Local cost limit based on entered prices |
| Quota group | Shared counters for profiles belonging to one account/project |

**0 means unknown or no local enforcement.** Budgets require meaningful prices. Profiles sharing provider prefix, API base URL and key automatically share counters. For different keys sharing one account allowance, use the same explicit quota group and identical limits.

Before each actual API attempt, SQLite reserves estimated input plus maximum output under a lock, preventing concurrent requests from promising the same local remainder twice. Input estimation uses UTF-8 bytes including tools plus a protocol allowance, not exact tokenization. Provider-reported usage replaces reservations after successful responses when available. Missing usage remains marked **≈**. Failed/interrupted attempts retain conservative reservations; request counters include failures.

**Usage** shows the latest 100 actual API attempts with profile, request ID, timestamp, tokens, duration and outcome. Fallbacks for one router request share its ID. A conversation with multiple tool steps may generate several router requests and IDs. CSV also contains estimated costs. Prompts, completions and executable tool arguments are not stored in the usage database.

## Connect Home Assistant Assist

### Native LiteLLM integration

1. Open **Connect Assist → LiteLLM → Show connection details**.
2. Copy the base URL and **router key** into the linked HA integration form. The router key is separate from provider keys.
3. Open the LiteLLM entry and add a conversation agent for **`assist-auto`** or your rule alias.
4. Enable **Control Home Assistant** if desired, expose the required entities, and select the agent in your voice assistant.

The app supplies its internal Supervisor hostname on port 8000. The native [LiteLLM integration](https://www.home-assistant.io/integrations/litellm/) connects Assist to this endpoint. Device actions are performed by the conversation agent through the HA tools you permit.

### HACS MCP Assist

Alternatively choose **MCP Assist** under **Connect Assist**. The UI opens the HACS repository and integration form and provides copyable values. You perform the download and HA restart.

Choose server type **OpenAI**, enter the router URL **without a trailing `/v1`**, the router key and `assist-auto`. MCP Assist appends the API paths. Set its timeout above the router's overall budget; the UI suggests five additional seconds. MCP port 8090 is not router API port 8000.

The [MCP Assist guide](assist_ai_router/MCP_ASSIST.en.md) covers permissions, setup and troubleshooting for the inspected 0.17.2 connection. [MCP Assist](https://github.com/mike-nott/mcp-assist) is an alternative conversation agent. The separately linked native HA MCP client/server integrations are not generally required for this connection. The app installs nothing in the background and never edits HA `.storage` files.

## Settings and operation

| Setting | Default | Effect |
| --- | --- | --- |
| Output tokens | 512 | Cap per model call, including larger client requests |
| Request budget | 45 s | Time budget for a router request |
| Attempt budget | 12 s | Timeout forwarded to LiteLLM per provider |
| Maximum attempts | 4 | Maximum actual provider calls per request |
| Cooldown | 60 s | Base for eligible errors; Retry-After can extend it |
| Reserve | 5% | Unallocated portion of configured local limits |
| History | 30 days | Retention; current-month rows remain for monthly accounting |
| Paid profiles | Off | Additional permission beyond free/local profiles |
| Custom gateway URL | Empty | Overrides the displayed address; does not configure networking |

There are no periodic paid model probes. Status reflects previous tests/requests and local restrictions; Ready is not continuous live monitoring. Visible status data refreshes every 15 seconds except during dialog editing, saving or dragging.

- **Ingress 8099:** Administration through Supervisor ingress, without publishing a host port.
- **API 8000:** `/v1/models` and `/v1/chat/completions` require the bearer router key; `/health` is a basic reachability endpoint. No management routes are exposed here. Host publication is optional and off by default.
- **Streaming:** Upstream responses are fully buffered, then returned as SSE. There is no live token-by-token output; fallback cannot occur halfway through an already transmitted tool call.
- **Backups:** Options, router key and SQLite live in `/data`. Include app data in backups; backups may contain credentials.
- **Networking:** Cloud calls transmit prompts/context to the selected provider. Local servers must be reachable from the app. Use suitable HTTPS access over untrusted networks.
- **Credentials:** The normal settings response omits keys. Only an opened editor fetches its original entry; resolved secrets are never returned. Model metadata requests send credentials in headers to the configured destination, block redirects and suppress upstream error bodies. LiteLLM telemetry is disabled.

LiteLLM remains pinned to **1.106.4** and its image digest; startup verifies the SDK version. **Version check** queries GitHub only after a click, caches for one hour and installs nothing. A newer upstream release does not automatically replace the reviewed dependency.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| No model suggestions | Complete key/URL and leave the field, clear/type in the model field, read its status; manual entry remains available. |
| New secret cannot load models | Save `!secret name` with a manual/SDK model, then reopen the profile. |
| Paid profile blocked | Confirm checked free access, mark a local profile, or explicitly allow paid profiles. |
| Limit reached earlier than expected | Account for reserve, conservative estimates, failed attempts and shared quotas. |
| Cooldown after resume | Pause does not remove rate-limit restrictions; wait until the indicated time. |
| Unexpected routing order | Check preset, rules, capabilities, local restrictions and direct provider aliases. |
| HA cannot reach router | Use the internal setup address; ingress is not the model API. |
| MCP Assist 404/401 | Check OpenAI type, URL without /v1 and router key instead of provider key. |
| All providers fail | Check account limits, network and permissions; add independent providers/local fallback. |

## Development and further documentation

[Detailed configuration](assist_ai_router/DOCS.en.md) · [MCP Assist](assist_ai_router/MCP_ASSIST.en.md) · [Development and acceptance](CONTRIBUTING.md) · [Changelog](assist_ai_router/CHANGELOG.md) · [More Home Assistant Apps](https://github.com/seb5594/Home-Assistant-Apps)

Automated tests cover routing, secrets, HTTP boundaries, metadata discovery and SDK integration. Real Home Assistant, provider-account, device-action, browser and backup-restore acceptance remains separate.

The footer links this project and other apps, includes **Support my work ☕**, and displays “Application developed by seb5594 (Sebastian Schmidt) - Made with ♥ in Germany” with a red heart.

[Support my work ☕](https://paypal.me/seb5594). Published under the [MIT License](LICENSE).

Copyright (c) 2026 seb5594 (Sebastian Schmidt). LiteLLM and other third-party components retain their respective licenses.
