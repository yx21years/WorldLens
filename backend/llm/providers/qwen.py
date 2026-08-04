"""Qwen LLM provider — stub for future implementation."""

from llm.models import ModelInfo


class QwenProvider:
    def __init__(self, api_key: str, model: str = "qwen-max"):
        self.api_key = api_key
        self.model = model

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(provider="qwen", model=self.model, max_tokens=8192, supports_structured_output=True)
