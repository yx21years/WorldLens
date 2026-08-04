import asyncio
from typing import Any, Protocol
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    parsed: dict[str, Any] | None = None
    model: str = ""
    tokens_used: int = 0
    provider: str = ""


@dataclass
class ModelInfo:
    provider: str
    model: str
    max_tokens: int
    supports_structured_output: bool


class LLMProvider(Protocol):
    async def complete(self, prompt: str, system: str, params: dict[str, Any]) -> LLMResponse: ...
    async def complete_structured(
        self, prompt: str, system: str, schema: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]: ...
    def validate_connection(self) -> bool: ...
    def get_model_info(self) -> ModelInfo: ...
