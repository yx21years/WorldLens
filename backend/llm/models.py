from dataclasses import dataclass
from typing import Any


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
