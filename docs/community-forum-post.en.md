# [App] Assist AI Router — multiple AI providers and automatic fallback for Assist

Hi everyone,

I'm Sebastian (seb5594), and I'd like to share a Home Assistant app I've been working on: **Assist AI Router**.

I mainly use free API keys, and I kept running into the same problem: a model works well, but its quota runs out quickly. For a voice assistant, having another provider available only helps if switching between them is straightforward.

That is what I wanted to build: one endpoint for Assist, with several providers behind it, and as much configuration as possible inside Home Assistant.

The app is powered by [LiteLLM](https://github.com/BerriAI/litellm). It includes an ingress web UI where you can add provider profiles, choose models, arrange their priority and inspect usage. There is no separate LiteLLM server to install.

**What it currently does**

- Offers 21 provider templates, including Gemini, Groq, OpenRouter, Mistral, Cerebras and local Ollama/OpenAI-compatible servers such as llama.cpp or vLLM.
- Shows providers in a numbered list with drag-and-drop ordering and pause/resume controls.
- Loads available models automatically into the model field where the provider supports discovery.
- Supports existing Home Assistant `!secret` references, which I recommend, as well as directly entered keys.
- Provides fixed-priority, quota-aware, round-robin and local-first routing, plus custom model-alias/tool rules.
- Falls back on suitable provider errors and rate limits, with cooldowns and configurable local limits.
- Shows input/output token usage and individual API attempts, with CSV export.
- Includes German and English interfaces and documentation.

For Assist, you can use Home Assistant's **native LiteLLM integration** and select `assist-auto` as the model. There is also a guided setup path for [MCP Assist through HACS](https://github.com/mike-nott/mcp-assist), if you prefer that conversation agent.

One detail I want to be clear about: the quota dashboard primarily tracks requests through this app. It cannot see all usage elsewhere. OpenRouter and DeepSeek provide some account metadata; for other providers, the app includes documented plan hints and selected limit examples where available. It does not assume an unknown quota is unlimited.

And automatic fallback still needs somewhere to fall back to. If every allowed provider is exhausted or unavailable, the request can fail. A suitable local model is another option for those situations.

**Getting started**

Add my app repository, install Assist AI Router, configure and test your providers, then follow **Connect Assist** in the web UI:

https://github.com/seb5594/Home-Assistant-Apps

Project, installation details and documentation:

https://github.com/seb5594/Home-Assistant-Assist-AI-Router-App

The app supports **amd64 and aarch64** and requires **Home Assistant 2026.8 or newer** with app/Supervisor support. The current release is **v1.0.0**. The project code is licensed under **MIT**; upstream components retain their own licenses.

I'd especially appreciate feedback from people using small free quotas: which providers work well for Assist tool calls, where fallback helps, and which parts of setup still feel awkward. Bug reports and suggestions are welcome here or on GitHub.

Thanks for taking a look!

Sebastian / seb5594
