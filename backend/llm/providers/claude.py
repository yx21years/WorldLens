"""Claude (Anthropic) LLM provider — stub for Phase 1, full implementation in Phase 2."""

from llm.models import LLMResponse, ModelInfo


class ClaudeProvider:
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        self.api_key = api_key
        self.model = model

    async def complete(self, prompt: str, system: str, params: dict) -> LLMResponse:
        raise NotImplementedError("Claude provider implementation coming in Phase 2")

    async def complete_structured(self, prompt: str, system: str, schema: dict, params: dict) -> dict:
        raise NotImplementedError("Claude provider implementation coming in Phase 2")

    def validate_connection(self) -> bool:
        return bool(self.api_key)

    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            provider="claude",
            model=self.model,
            max_tokens=8192,
            supports_structured_output=True,
        )
