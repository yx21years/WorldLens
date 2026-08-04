"""DeepSeek LLM provider — stub for future implementation."""

from llm.models import ModelInfo


class DeepSeekProvider:
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(provider="deepseek", model=self.model, max_tokens=4096, supports_structured_output=False)
