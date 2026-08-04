"""Google Gemini LLM Provider for WorldLens AI.

Supports Gemini 2.5 Flash and other models via Google Generative Language API.

Provider name: "gemini"
Required env var: LLM_API_KEY (Google API Key)
Documentation: https://ai.google.dev/gemini-api/docs
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

import httpx

from llm.base import LLMProvider, LLMResponse, ModelInfo
from llm.retry import with_retry
from errors.base import LLMProviderError, LLMRateLimitError

logger = logging.getLogger(__name__)


@dataclass
class GeminiContent:
    parts: list[Dict[str, Any]]
    role: str = "user"  # "user" or "model"


@dataclass
class GeminiRequest:
    contents: list[GeminiContent]
    safety_settings: list[Dict[str, Any]] = None  # Omitted for simplicity


class GeminiProvider(LLMProvider):
    """Google Gemini implementation following LLMProvider protocol.

    Uses the GenerateContent API at https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.client = httpx.AsyncClient(
            params={"key": api_key},
            timeout=httpx.Timeout(30.0),
        )

    async def complete(self, prompt: str, system: str, params: Dict[str, Any]) -> LLMResponse:
        """Generate a raw text completion."""

        request_body = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": params.get("temperature", 0.3),
                "maxOutputTokens": params.get("max_tokens", 1000),
            },
        }

        if system:
            # Prepend system message by embedding it in the prompt prefix
            prompt_prefix = f"System: {system}\\n\\nUser: {prompt}"
            request_body["contents"][0]["parts"][0]["text"] = prompt_prefix

        try:
            response = await with_retry(
                lambda: self.client.post(
                    f"{self.base_url}/models/{self.model}:generateContent", json=request_body
                )
            )
            response.raise_for_status()

            result = response.json()
            if "candidates" not in result or not result["candidates"]:
                raise LLMProviderError("gemini", "No candidates returned in response")

            content = result["candidates"][0]["content"]["parts"][0]["text"]
            # Token count is not directly returned by Gemini API in the simple version; track separately if needed
            return LLMResponse(
                content=content,
                parsed=None,
                model=self.model,
                tokens_used=0,  # Gemini doesn't easily expose token count in this endpoint
                provider="gemini",
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError("gemini") from e
            raise LLMProviderError("gemini", f"HTTP {e.response.status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            raise LLMProviderError("gemini", f"Network error: {e}") from e
        except Exception as e:
            raise LLMProviderError("gemini", f"Unexpected error: {e}") from e

    async def complete_structured(
        self, prompt: str, system: str, schema: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured JSON output matching the provided schema.

        Gemini supports JSON mode via response_format when using certain models.
        We attempt the structured approach first, falling back to raw generation + parse.
        """
        # Build system instruction that requests JSON output
        if system:
            instruction = f"Follow these guidelines: {system}\\n"
        else:
            instruction = ""

        instruction += "Respond ONLY as a valid JSON object matching the requested schema. No markdown, no extra text."

        request_body = {
            "contents": [
                {
                    "parts": [{"text": instruction + prompt}],
                }
            ],
            "generationConfig": {
                "temperature": params.get("temperature", 0.3),
                "maxOutputTokens": params.get("max_tokens", 1000),
                # Gemini's JSON response format is supported on some models
                "response_format": {"type": "application/json"},
            },
        }

        try:
            response = await with_retry(
                lambda: self.client.post(
                    f"{self.base_url}/models/{self.model}:generateContent", json=request_body
                )
            )
            response.raise_for_status()

            result = response.json()
            if "candidates" not in result or not result["candidates"]:
                raise LLMProviderError("gemini", "No candidates returned in response")

            content = result["candidates"][0]["content"]["parts"][0]["text"]
            try:
                parsed = json.loads(content)
                return parsed
            except json.JSONDecodeError:
                logger.warning(f"Gemini structured response not valid JSON, extracting from text")
                # Try to extract JSON block
                import re
                match = re.search(r"\{[^{}]*\}", content)
                if match:
                    try:
                        return json.loads(match.group())
                    except json.JSONDecodeError:
                        pass
                raise LLMProviderError("gemini", "Could not parse JSON from Gemini response")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError("gemini") from e
            raise LLMProviderError("gemini", f"HTTP {e.response.status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            raise LLMProviderError("gemini", f"Network error: {e}") from e
        except Exception as e:
            # Fallback: try without structured mode
            logger.info(f"Structured mode failed ({e}), retrying with raw prompt + post-parsing")
            return await self._fallback_complete_structured(prompt, system, schema, params)

    async def _fallback_complete_structured(
        self, prompt: str, system: str, schema: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback: generate raw text and try to parse JSON after."""
        # Create prompt that asks for JSON explicitly
        prompt_text = f"Respond ONLY as valid JSON. No extra text.\n\n{prompt}"
        response = await self.complete(prompt_text, system, params)
        import re
        match = re.search(r"\{[^{}]*\}", response.content)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise LLMProviderError("gemini", "Could not extract JSON from Gemini response in fallback mode")

    def validate_connection(self) -> bool:
        """Test if the API key is valid."""
        if not self.api_key:
            return False
        try:
            response = httpx.get(
                f"{self.base_url}/models/{self.model}",
                params={"key": self.api_key},
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> ModelInfo:
        """Return info about the configured model."""
        # Gemini 2.5 Flash supports structured output
        return ModelInfo(
            provider="gemini",
            model=self.model,
            max_tokens=32768,
            supports_structured_output=True,
        )

    def __del__(self):
        """Close the HTTP client on cleanup."""
        try:
            self.client.close()
        except Exception:
            pass
