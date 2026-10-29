# Connect HACS MCP Assist to Assist AI Router

[Deutsche Anleitung](MCP_ASSIST.md) · [MCP Assist project](https://github.com/mike-nott/mcp-assist)

**mike-nott's MCP Assist** is a separate conversation agent with dynamic entity discovery and MCP tools. It can replace the native LiteLLM conversation agent while Assist AI Router continues to manage your provider credentials, priorities, quotas and fallbacks.

## Prerequisites and installation

Use Home Assistant 2026.8+, HACS, the running router app, and at least one enabled, allowed and tested profile with tool support. In the router choose **Connect Assist → MCP Assist (HACS · mike-nott)** for a guided setup with the appropriate links and copy fields.

Open [MCP Assist in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=mike-nott&repository=mcp-assist&category=integration), download it and restart Home Assistant. Alternatively add `https://github.com/mike-nott/mcp-assist` as an **Integration** custom repository in HACS. Install HACS first if needed. The router does not silently install custom components or edit HA files.

## Connection settings

Choose **Show connection details** in the router's MCP Assist setup path, then [add MCP Assist](https://my.home-assistant.io/redirect/config_flow_start/?domain=mcp_assist).

| MCP Assist field | Value |
| --- | --- |
| Profile name | For example `Assist AI Router` |
| Server type | **OpenAI** |
| Server URL | The router's MCP Assist URL, **without `/v1`** |
| API key | The **router access key**, not a provider key |
| Model | **assist-auto**, or a custom routing-rule alias |
| Response Time Out | At least the router request budget plus 5 seconds; setup calculates a suggestion |

For example the native LiteLLM integration uses `http://<internal-app-host>:8000/v1`; MCP Assist needs `http://<internal-app-host>:8000`. It appends `/v1/models` and `/v1/chat/completions` itself. Copy the Supervisor-provided hostname from the router; `localhost` in HA refers to a different service.

**OpenAI** here selects the compatible protocol and configurable endpoint, not the upstream AI provider. Replace the prefilled `https://api.openai.com` address with your router's address. In the inspected source the local LM Studio/llama.cpp/vLLM adapters do not send Bearer credentials, so they are not the appropriate setup choice for this authenticated router.

MCP Assist discovers models using the router key. `assist-auto` keeps automatic fallback; a `provider:<ID>` alias targets exactly one profile. Provider keys remain in the router/Supervisor secrets. Setup links contain no credentials; copy the router key into the HA form.

## Tools and voice assistant

Enable **Control Home Assistant** in MCP Assist if desired and expose the intended entities under **Settings → Voice assistants → Expose**. Select the MCP Assist profile as your pipeline's conversation agent under [Voice assistants](https://my.home-assistant.io/redirect/voice_assistants/).

An additional native `mcp` or `mcp_server` integration is not required to use MCP Assist as a conversation agent. The native LiteLLM integration may remain installed; choose one conversation agent per pipeline. MCP Assist's default MCP port 8090 belongs to its own MCP service and is not the router's LLM endpoint on port 8000. Connecting to the router does not require another publicly exposed port.

## Free-quota starting points and verification

Try 256–512 response tokens, short history and a small tool-iteration limit such as 3–5. Keep the technical tool instructions initially. Dynamic entity discovery can avoid sending complete entity inventories in prompts, but every additional tool round still produces more model requests. Watch actual router usage and adjust limits as needed.

Start with a state query, then deliberately test a simple device action and verify its actual effect. MCP Assist executes HA tools and passes their results back to the model; the router only forwards model requests. Contract tests cover HTTP authentication, streaming tool calls and tool-result messages, not a live HA installation or real model behavior.

## Temporarily pause providers

Use **Pause** and later **Resume** on provider cards in either Overview or Providers. Pauses persist until manually resumed, including across app restarts. Credentials, ordering, rules and usage stay intact. New requests, including MCP Assist requests, skip paused profiles; already running calls may still finish. Resuming does not reset quotas or cooldowns. Resume a profile before testing its connection.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| HACS link fails | Install HACS and select the correct HA instance; alternatively add the custom repository manually. |
| MCP Assist cannot be added | Restart HA after downloading it through HACS. |
| OpenAI server type has no URL field | Update MCP Assist; older source versions may lack the required custom endpoint setting. |
| 404 or no models | Use the server root URL without `/v1`, `/models` or `/chat/completions`. |
| 401 / invalid API key | Use the router access key and your internal router URL instead of the OpenAI cloud address. |
| Timeout during fallback | Raise MCP Assist's timeout above the router request budget; check model latency and tool rounds. |
| Answers have no device effect | Verify model tool support, Control Home Assistant, exposed entities and actual tool calls. |
| No provider available | Enable at least one profile with matching capabilities, confirmed free usage and remaining quota. |

Inspected on **2026-10-29**: MCP Assist **0.17.2**, commit [`feff8d3`](https://github.com/mike-nott/mcp-assist/tree/feff8d31761fe54a3a7ca2afd1949ad6e69dd019). See the [OpenAI configuration flow](https://github.com/mike-nott/mcp-assist/blob/feff8d31761fe54a3a7ca2afd1949ad6e69dd019/custom_components/mcp_assist/config_flow.py) and [agent implementation](https://github.com/mike-nott/mcp-assist/blob/feff8d31761fe54a3a7ca2afd1949ad6e69dd019/custom_components/mcp_assist/agent.py). Your installed HACS version may differ.
