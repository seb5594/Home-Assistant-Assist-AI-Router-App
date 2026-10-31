# Assist AI Router — English

Version **1.0.3** · LiteLLM **1.106.4** · Home Assistant **2026.8+**

## Quick start

1. Install/start the app and open its ingress web interface. LiteLLM is included.
2. Select a provider template, enter its key and model, save, and test the connection. Tests send a small real request.
3. Add another independent provider and sort the numbered vertical list using the ⠿ drag handle or ↑/↓ buttons. Fixed priority tries them in that order.
4. Open **Connect Assist → Show connection details → Add LiteLLM to Home Assistant**. Copy the URL and router key into the native integration form. The router key is separate from provider keys.
5. Open the LiteLLM entry, choose **Add conversation agent**, select **assist-auto**, enable Assist tools if needed, expose the desired entities, and select the agent in your voice assistant.

Home Assistant reaches the internal app hostname on port 8000; setup obtains that hostname from Supervisor. The API's `/v1/models` returns `assist-auto`, custom rule aliases and `provider:<profile-id>`. Explicit provider aliases target exactly one profile without fallback. Use `assist-auto` for normal Assist use.

## Configuration and credentials

Use **Pause/Resume** directly on provider cards in Overview or Providers. Paused profiles remain excluded until manually resumed, including after app restarts. Credentials, priority, rules and usage are preserved. New requests skip them; already running calls may still finish. Resuming does not reset limits or cooldowns.

Saving in ingress writes the same app options as the Home Assistant Configuration tab through `/addons/self/options`, then loads resolved options and applies them immediately. Configuration-tab changes load on app restart or when refreshing router settings. Revision conflicts stop stale UI edits from overwriting newer options; Supervisor has no atomic compare-and-swap across separate editors.

The key field shows `!`, `!s`, `!se` through `!secret name` without masking while the value follows the secret prefix; any deviation restores password masking.

Enter keys directly in the form or reference an existing Home Assistant secret using `!secret name`. Supervisor resolves references; edits preserve the raw reference. Resolved secret values are never returned. Opening fetches the original entry through a dedicated ingress endpoint; literal keys can be revealed using the eye icon inside the key field. Secret references are recommended. Leave the key field blank while editing to preserve it; use **Remove saved key** to clear it. This app cannot create new entries in HA's secrets file. Direct form entry requires no text files.

### Load models directly from a provider

Enter the API key and custom API base URL if needed, then leave the edited field. Models load automatically on opening with saved credentials and after completed credential edits, directly as suggestions inside **LLM model** without a separate load button or second picker. Open ▾ or type in the field to choose another model; the LiteLLM prefix is added automatically, so no model name is required beforehand. A new literal key works before saving without persisting the profile/key. Saved keys and secret references are resolved on the server. A **new** `!secret` reference needs to be saved in a profile first, using an SDK suggestion as the initial model if needed. Changing the provider or API destination requires re-entering a saved key or explicitly saving the changed profile.

Direct adapters cover Gemini, Groq, Cerebras, OpenRouter, Mistral, Hugging Face, SambaNova, Together AI, NVIDIA NIM, OpenAI, Anthropic, DeepSeek, xAI, Cohere, Ollama and custom OpenAI-compatible model endpoints. Other providers or account-specific deployment APIs can use SDK suggestions/manual entry. Provider responses do not guarantee free pricing, individual account permission or tool support. Some APIs list non-chat models; Gemini/Cohere use known chat filters. Pagination, response sizes and processing time are bounded, and partial lists are labeled.

Discovery runs on opening the provider editor or completing credential changes and loads metadata without generating a prompt or changing token counters. Provider metadata rate limits may still apply. Credentials are sent in headers to the configured provider, never in URLs, UI responses or logs; redirects are blocked and provider error bodies are not echoed.

There are 21 templates: Google AI Studio, Groq, Cerebras, OpenRouter, Mistral, Hugging Face, GitHub Models, SambaNova, Together AI, Fireworks AI, Cohere, Cloudflare, NVIDIA NIM, OpenAI, Anthropic, DeepSeek, xAI, Perplexity, Azure, Ollama and OpenAI-compatible endpoints. Model examples are editable. The model catalog comes from the pinned SDK and does not verify account availability. Some providers need a custom account/deployment URL or API version.

Templates do not promise free access. Confirm free usage only for a model/account you have checked. Paid-marked profiles are blocked by default, but the app cannot verify your account tariff or prevent provider billing. Local models need a reachable endpoint. Text connection tests do not prove a model's tool-calling quality; enable tool support only for suitable models.

## Policies and rules

| Policy | Selection |
| --- | --- |
| Fixed priority | Your configured order |
| Preserve quotas | Lowest consumed fraction of known limits; unknown quotas last |
| Spread requests | Rotate the starting point on each request |
| Local first | Local models, then allowed cloud profiles |

The first matching custom rule restricts the provider set by requested model alias and optionally the presence of tools. The policy sorts within that set; fallbacks cannot leave it. Custom aliases appear in the integration's model picker. `*` matches routing aliases. Explicit `provider:` aliases bypass rule selection and use one profile, while still enforcing cost and capability restrictions.

429, authentication failures, missing models, network errors and server errors can trigger fallback. Cooldowns honor `Retry-After`; shared quota groups share 429 cooldowns. Invalid requests are not blindly replayed. Context-window errors may try another model; messages and Assist tools are never truncated/dropped. Per-request and per-attempt timeouts are forwarded to LiteLLM, and maximum attempts limit the search; individual network phases can affect total elapsed time.

## Usage and limits

Configure RPM, TPM, daily requests, daily/monthly tokens, context windows and monthly budgets. **0 means unknown / no local enforcement**, not unlimited free allowance. A safety reserve reduces usable quota. SQLite reserves estimated input plus maximum output before each upstream call, under a lock, so concurrent requests cannot promise the same local quota twice.

The conservative input estimate uses UTF-8 bytes including tool definitions plus a protocol allowance, not exact tokenization. This can exclude large Assist contexts from small quotas earlier than the provider would. Provider-reported token usage replaces reservations after successful responses. Missing usage remains marked **≈**. Failed/interrupted requests retain conservative reservations because a charge cannot be excluded. Request counters include failures.

Matching provider prefix, base URL and key share counters automatically. Give profiles with a shared account/project quota the same explicit quota group and identical limits. Minute counters use rolling 60-second windows; daily/monthly boundaries are **UTC**. Provider-specific reset schedules are supplemented by 429 cooldowns. Activity outside this app is unknown.

Dashboard values are local observations, not verified provider balances. Provider portals are linked. The usage page shows the latest 100 attempts, including input/output/total tokens, timing, request IDs and fallbacks. CSV adds estimated USD costs using manually entered prices. Retention is configurable; current-month rows remain until the next month to preserve quota accounting. Prompts, completions and executable tool arguments are never stored.

## MCP, operation and updates

The HACS **MCP Assist by mike-nott** integration has its own selectable path under **Connect Assist**. It opens the HACS repository and integration form and supplies the correct server root URL **without `/v1`**, the router key, `assist-auto` and a timeout suggestion. Select the **OpenAI** compatible server type in MCP Assist and replace its default cloud URL with the router URL. The [MCP Assist guide](MCP_ASSIST.en.md) covers installation, entity permissions, free-quota settings and troubleshooting. MCP Assist can replace the native LiteLLM conversation agent.

Use the native LiteLLM integration for Assist. MCP is optional: the HA MCP client adds external tools; the HA MCP server exposes HA to external clients. Setup opens official forms. Entity access, OAuth and voice-pipeline changes remain in Home Assistant; the app does not edit HA files or `.storage`.

Ingress administration listens on 8099 and accepts only Supervisor's ingress peer `172.30.32.2` in production. It is not published on the host. Port 8000 provides the authenticated chat API and no management routes. Host publication is optional and disabled by default. Use your own HTTPS reverse proxy for access over an untrusted network. Ingress administration is intended for trusted HA users.

SQLite, options and the generated router key live in `/data`; include them in app backups. Backups may contain credentials. The image uses the exact official LiteLLM release tag with upstream's frozen dependencies; startup verifies the SDK version. The full upstream image is larger than an SDK-only install. Telemetry is disabled. No periodic paid health checks, Redis or PostgreSQL are required.

The stable version check contacts GitHub only after a click, caches for one hour, and installs nothing. Updates ship in reviewed app releases. Starting with v1.0.0, semantic versions (`MAJOR.MINOR.PATCH`) replace calendar versions.

If all allowed providers are exhausted/unavailable and no local fallback is available, the API returns HTTP 503 with `no_provider_available`. Unlimited cloud answers cannot be guaranteed.

Before a stable release, test installation on real HA OS amd64/aarch64, protection mode/ingress, secret persistence/restart, the native LiteLLM setup and Assist tool calls, real multi-provider 429/Retry-After behavior and backup restore. Software tests do not replace these acceptance checks. Record visual browser verification separately.

References: [native LiteLLM integration](https://www.home-assistant.io/integrations/litellm/), [app options/secrets](https://contributors.home-assistant.io/apps/guides/options/), [Supervisor app API](https://contributors.home-assistant.io/apps/supervisor-api/apps/), [LiteLLM routing](https://docs.litellm.ai/docs/routing), [pinned release](https://github.com/BerriAI/litellm/releases/tag/v1.106.4).

## API plans and rule examples

The [English README](../README.en.md) contains concrete alias/tool/catch-all rules and a dated table of official plan/limit sources. The editor distinguishes documentation examples from OpenRouter/DeepSeek account data. Currency balances are not token limits; unknown values stay unknown. Example limits only populate the form after a click.
