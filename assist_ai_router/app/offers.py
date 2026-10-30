"""Dated provider documentation hints, never evidence of an individual account's tier."""
CHECKED = "2026-10-30"
# No auto-enforcement: examples can differ by organization, model and paid tier.
OFFERS = {
    "gemini": ("Free / Paid tiers", "https://ai.google.dev/gemini-api/docs/rate-limits", "Project/model-specific RPM, TPM and RPD; check AI Studio.", {}),
    "groq": ("Free / Developer", "https://console.groq.com/docs/rate-limits", "Free examples for gpt-oss-20b/120b: 30 RPM, 1,000 RPD, 8,000 TPM, 200,000 TPD. Organization limits may differ.", {
        "groq/openai/gpt-oss-20b": {"rpm": 30, "daily_requests": 1000, "tpm": 8000, "daily_tokens": 200000},
        "groq/openai/gpt-oss-120b": {"rpm": 30, "daily_requests": 1000, "tpm": 8000, "daily_tokens": 200000}}),
    "cerebras": ("Free Trial / Developer / Enterprise", "https://inference-docs.cerebras.ai/support/rate-limits", "Trial examples gpt-oss-120b/qwen-3.8-27b: 5 RPM, 30,000 uncached TPM, 1,000,000 TPD. Separate hourly/total-token limits apply. Trial credits expire; not a permanent free tier.", {
        "cerebras/gpt-oss-120b": {"rpm": 5, "tpm": 30000, "daily_tokens": 1000000},
        "cerebras/qwen-3.8-27b": {"rpm": 5, "tpm": 30000, "daily_tokens": 1000000}}),
    "openrouter": ("Free models / Credits", "https://openrouter.ai/docs/api_reference/limits", "API key metadata can report free-tier status, credit cap and daily free-model requests; no universal token cap.", {}),
    "mistral": ("Free / Pay-as-you-go tiers", "https://docs.mistral.ai/admin/billing-usage/usage-limits", "Organization/model-specific limits; check the Limits page. Consumer subscriptions do not establish API allowance.", {}),
    "huggingface": ("Free / PRO / Team / Enterprise", "https://huggingface.co/docs/inference-providers/pricing", "Published monthly credits: Free $0.10 (subject to change), PRO $2, organizations $2/seat. Monetary credits are not fixed tokens or verified remaining balance.", {}),
    "cohere_chat": ("Trial / Production", "https://docs.cohere.com/docs/rate-limits", "Trial: 1,000 API calls/month; selected chat models 20 RPM. Monthly requests are not tokens or daily allowance.", {}),
    "cloudflare": ("Workers Free / Paid", "https://developers.cloudflare.com/workers-ai/platform/pricing/", "10,000 Neurons/day free allocation; neurons cannot be converted into a universal token allowance. Some models require paid access.", {}),
    "nvidia_nim": ("Developer / Enterprise", "https://docs.api.nvidia.com/nim/docs/product", "Developer access is for prototyping. No reliably documented universal token quota is prefilled.", {}),
    "sambanova": ("Free / Developer / Enterprise", "https://cloud.sambanova.ai/plans", "Check account credits and current plan; the Free plan page asks for purchased credits before API use. No free token allowance assumed.", {}),
    "deepseek": ("API balance", "https://api-docs.deepseek.com/api/get-user-balance/", "The balance endpoint reports available/granted/purchased funds, not a subscription tier or fixed token balance.", {}),
}


def offer(preset):
    row = OFFERS.get(preset)
    if row is None:
        return None
    name, source, note, limits = row
    return dict(name=name, source=source, note=note, limits_by_model=limits, checked=CHECKED)
