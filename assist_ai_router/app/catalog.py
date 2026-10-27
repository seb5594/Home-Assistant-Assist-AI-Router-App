"""Starter profiles. Availability and free allowances belong to each account, never inferred."""
VERSION = "2026-10-27"
LITELLM_VERSION = "1.106.4"

# Prefixes are LiteLLM SDK providers; model suggestions are editable examples, not free-tier claims.
CATALOG = [
    ("gemini", "Google AI Studio", "gemini", "gemini-2.5-flash", "https://aistudio.google.com/api-keys", "https://aistudio.google.com/usage"),
    ("groq", "Groq", "groq", "llama-3.3-70b-versatile", "https://console.groq.com/keys", "https://console.groq.com/settings/limits"),
    ("cerebras", "Cerebras", "cerebras", "", "https://cloud.cerebras.ai/", "https://cloud.cerebras.ai/"),
    ("openrouter", "OpenRouter", "openrouter", "openrouter/free", "https://openrouter.ai/settings/keys", "https://openrouter.ai/activity"),
    ("mistral", "Mistral / La Plateforme", "mistral", "mistral-small-latest", "https://console.mistral.ai/", "https://console.mistral.ai/"),
    ("huggingface", "Hugging Face Inference", "huggingface", "", "https://huggingface.co/settings/tokens", "https://huggingface.co/settings/billing"),
    ("github", "GitHub Models", "github", "", "https://github.com/settings/tokens", "https://github.com/settings/billing"),
    ("sambanova", "SambaNova", "sambanova", "", "https://cloud.sambanova.ai/", "https://cloud.sambanova.ai/"),
    ("together_ai", "Together AI", "together_ai", "", "https://api.together.ai/", "https://api.together.ai/"),
    ("fireworks_ai", "Fireworks AI", "fireworks_ai", "", "https://fireworks.ai/account/api-keys", "https://fireworks.ai/account"),
    ("cohere_chat", "Cohere", "cohere_chat", "command-a-03-2025", "https://dashboard.cohere.com/api-keys", "https://dashboard.cohere.com/"),
    ("cloudflare", "Cloudflare Workers AI", "cloudflare", "", "https://dash.cloudflare.com/", "https://dash.cloudflare.com/"),
    ("nvidia_nim", "NVIDIA NIM", "nvidia_nim", "", "https://build.nvidia.com/", "https://build.nvidia.com/"),
    ("openai", "OpenAI", "openai", "gpt-4o-mini", "https://platform.openai.com/api-keys", "https://platform.openai.com/usage"),
    ("anthropic", "Anthropic", "anthropic", "", "https://console.anthropic.com/", "https://console.anthropic.com/"),
    ("deepseek", "DeepSeek", "deepseek", "deepseek-chat", "https://platform.deepseek.com/", "https://platform.deepseek.com/usage"),
    ("xai", "xAI", "xai", "", "https://console.x.ai/", "https://console.x.ai/"),
    ("perplexity", "Perplexity", "perplexity", "sonar", "https://www.perplexity.ai/settings/api", "https://www.perplexity.ai/settings/api"),
    ("azure", "Azure OpenAI", "azure", "", "https://ai.azure.com/", "https://portal.azure.com/"),
    ("ollama_chat", "Ollama (local)", "ollama_chat", "llama3.2", "https://ollama.com/", "https://ollama.com/"),
    ("openai_compatible", "OpenAI-compatible / vLLM / llama.cpp", "openai", "", "https://docs.litellm.ai/docs/providers/openai_compatible", "https://docs.litellm.ai/docs/providers/openai_compatible"),
]


def catalog():
    return [dict(id=i, name=n, prefix=p, example_model=m, setup_url=s, usage_url=u,
                 local=i == "ollama_chat") for i, n, p, m, s, u in CATALOG]


DEFAULTS = dict(language="de", routing="priority", providers=[], rules=[],
                max_output_tokens=512, request_timeout=45, attempt_timeout=12,
                max_attempts=4, cooldown_seconds=60, reserve_percent=5,
                allow_paid=False, history_days=30, gateway_url="")

PROVIDER_DEFAULTS = dict(name="", preset="openai_compatible", model="", api_key="",
                         api_base="", api_version="", enabled=True, free_only=False,
                         local=False, supports_tools=True, supports_vision=False,
                         rpm=0, tpm=0, daily_tokens=0, daily_requests=0,
                         monthly_tokens=0, context_tokens=0, input_price=0.0,
                         output_price=0.0, monthly_budget=0.0, quota_group="")
