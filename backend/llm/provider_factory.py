from config.settings import get_settings
from errors.base import LLMProviderError


def get_provider(provider_name: str | None = None):
    settings = get_settings()
    name = provider_name or settings.LLM_PROVIDER

    providers = {
        "claude": "llm.providers.claude.ClaudeProvider",
        "openai": "llm.providers.openai.OpenAIProvider",
        "qwen": "llm.providers.qwen.QwenProvider",
        "deepseek": "llm.providers.deepseek.DeepSeekProvider",
        "zhipu": "llm.providers.zhipu.ZhipuProvider",
        "gemini": "llm.providers.gemini.GeminiProvider",
        "agnes": "llm.providers.agnes.AgnesProvider",
    }

    if name not in providers:
        raise LLMProviderError(name, f"Unknown provider '{name}'. Available: {list(providers.keys())}")

    module_path, class_name = providers[name].rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    provider_class = getattr(module, class_name)
    return provider_class(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
