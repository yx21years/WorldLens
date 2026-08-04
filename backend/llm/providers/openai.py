"""OpenAI LLM provider — stub for future implementation."""

from llm.models import ModelInfo


class OpenAIProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(provider="openai", model=self.model, max_tokens=4096, supports_structured_output=True)
