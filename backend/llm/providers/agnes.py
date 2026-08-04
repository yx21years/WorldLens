"""Agnes LLM Provider for WorldLens AI.

Supports Agnes 2.5 Flash via OpenAI-compatible API format.

Provider name: "agnes"
Required env var: LLM_API_KEY (Agnes API key)
"""

import json
import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict

import httpx

from llm.base import LLMProvider, LLMResponse, ModelInfo
from llm.retry import with_retry
from errors.base import LLMProviderError

logger = logging.getLogger(__name__)


@dataclass
class AgnesMessage:
    role: str  # "user", "assistant", "system"
    content: str


class AgnesProvider(LLMProvider):
    """Agnes implementation following LLMProvider protocol.

    Uses the OpenAI-compatible chat completion endpoint at https://api.agnes.ai/v1/chat/completions
    """

    def __init__(self, api_key: str, model: str = "agnes-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url ="https://apihub.agnes-ai.com/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(30.0),
        )

    async def complete(self, prompt: str, system: str, params: Dict[str, Any]) -> LLMResponse:
        """Generate a raw text completion using the OpenAI-compatible format."""

        messages: list[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        request_body: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": params.get("temperature", 0.3),
            "max_tokens": params.get("max_tokens", 1000),
            "stream": False,
        }

        try:
            response = await with_retry(lambda: self.client.post("/chat/completions", json=request_body))
            response.raise_for_status()

            result = response.json()

            if "choices" not in result or not result["choices"]:
                raise LLMProviderError("agnes", "No choices returned in response")

            content = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens", 0)

            return LLMResponse(
                content=content,
                parsed=None,
                model=self.model,
                tokens_used=tokens_used,
                provider="agnes",
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                from errors.base import LLMRateLimitError
                raise LLMProviderError("agnes", f"HTTP {e.response.status_code}: {e.response.text}") from e
            raise LLMProviderError("agnes", f"HTTP {e.response.status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            raise LLMProviderError("agnes", f"Network error: {e}") from e
        except Exception as e:
            raise LLMProviderError("agnes", f"Unexpected error: {e}") from e

    async def complete_structured(
        self, prompt: str, system: str, schema: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured JSON output matching the provided schema using OpenAI function calling style."""

        # Build system + user messages
        messages: list[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Add instruction to generate JSON
        messages.append({
            "role": "user",
            "content": f"\n\nYour task is to produce a valid JSON object matching this schema:\n{json.dumps(schema, indent=2)}. Respond ONLY with the JSON object and no additional text."
        })

        request_body: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": params.get("temperature", 0.3),
            "max_tokens": params.get("max_tokens", 1000),
            "stream": False,
        }

        try:
            response = await with_retry(lambda: self.client.post("/chat/completions", json=request_body))
            response.raise_for_status()

            result = response.json()

            if "choices" not in result or not result["choices"]:
                raise LLMProviderError("agnes", "No choices returned in response")

            content = result["choices"][0]["message"]["content"]

            try:
                # Try direct JSON parse first
                parsed = json.loads(content)
                return parsed
            except json.JSONDecodeError:
                logger.warning(f"Agnes structured response not valid JSON, extracting from text")
                # Try to extract JSON block using regex
                import re
                match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group())
                    except json.JSONDecodeError:
                        pass
                raise LLMProviderError("agnes", "Could not parse JSON from Agnes response")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                from errors.base import LLMRateLimitError
                raise LLMProviderError("agnes", f"HTTP {e.response.status_code}: {e.response.text}") from e
            raise LLMProviderError("agnes", f"HTTP {e.response.status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            raise LLMProviderError("agnes", f"Network error: {e}") from e
        except Exception as e:
            logger.info(f"Structured mode failed ({e}), retrying with raw prompt + post-parsing")
            # Fallback approach
            return await self._fallback_complete_structured(prompt, system, schema, params)

    async def _fallback_complete_structured(
        self, prompt: str, system: str, schema: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback: generate raw text and try to parse JSON after."""
        prompt_text = f"Respond ONLY as valid JSON, no extra text.\n\n{prompt}"
        response = await self.complete(prompt_text, system, params)
        import re
        match = re.search(r"\{[^{}]*\}", response.content)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise LLMProviderError("agnes", "Could not extract JSON from Agnes response in fallback mode")

    def validate_connection(self) -> bool:
        """Test if the API key is valid by making a minimal call."""
        if not self.api_key:
            return False
        try:
            response = httpx.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> ModelInfo:
        """Return info about the configured model."""
        # Agnes 2.5 Flash supports structured output
        return ModelInfo(
            provider="agnes",
            model=self.model,
            max_tokens=8192,
            supports_structured_output=True,
        )

    def __del__(self):
        """Close the HTTP client on cleanup."""
        try:
            self.client.close()
        except Exception:
            pass
