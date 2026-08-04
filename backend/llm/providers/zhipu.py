"""Zhipu AI LLM Provider for WorldLens AI.

Supports GLM-4.6V and other models via Zhipu's Chat Completion API.

API documentation: https://open.bigmodel.cn/dev/api
Provider name: "zhipu"
Required env var: LLM_API_KEY (Zhipu API key)
"""

import json
import logging
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

import httpx

from llm.base import LLMProvider, LLMResponse, ModelInfo
from llm.retry import with_retry
from errors.base import LLMProviderError, LLMRateLimitError

logger = logging.getLogger(__name__)


@dataclass
class ZhipuMessage:
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class ZhipuChatCompletionRequest:
    model: str
    messages: list[ZhipuMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stream: bool = False
    response_format: Optional[Dict[str, str]] = None  # For JSON mode


class ZhipuProvider(LLMProvider):
    """Zhipu AI implementation following LLMProvider protocol.

    Uses the Chat Completion API at https://open.bigmodel.cn/api/prompt/v1/chat/completions
    """

    def __init__(self, api_key: str, model: str = "glm-4.5-air"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(30.0),
        )

    async def complete(self, prompt: str, system: str, params: Dict[str, Any]) -> LLMResponse:
        """Generate a raw text completion."""
        messages: list[ZhipuMessage] = []
        if system:
            messages.append(ZhipuMessage(role="system", content=system))
        messages.append(ZhipuMessage(role="user", content=prompt))

        request_body = ZhipuChatCompletionRequest(
            model=self.model,
            messages=messages,
            temperature=params.get("temperature", 0.3),
            top_p=params.get("top_p", 0.9),
            response_format=None,
        )

        request_data = {
            "model": request_body.model,
            "messages": [{"role": m.role, "content": m.content} for m in request_body.messages],
        }
        if request_body.temperature is not None:
            request_data["temperature"] = request_body.temperature
        if request_body.top_p is not None:
            request_data["top_p"] = request_body.top_p
        if request_body.response_format:
            request_data["response_format"] = request_body.response_format

        try:
            response = await with_retry(
                lambda: self.client.post("/chat/completions", json=request_data)
            )
            response.raise_for_status()

            result = response.json()

            # 🔍 调试：打印完整响应
            print("=" * 60)
            print("📄 智谱 API 完整响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("=" * 60)

            if "choices" not in result or not result["choices"]:
                # 如果返回了错误信息，打印具体错误
                if "error" in result:
                    error_msg = result["error"].get("message", "Unknown error")
                    raise LLMProviderError("zhipu", f"API error: {error_msg}")
                raise LLMProviderError("zhipu", "No choices returned in response")

            content = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens", 0)

            return LLMResponse(
                content=content,
                parsed=None,
                model=self.model,
                tokens_used=tokens_used,
                provider="zhipu",
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError("zhipu") from e
            raise LLMProviderError("zhipu", f"HTTP {e.response.status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            raise LLMProviderError("zhipu", f"Network error: {e}") from e
        except Exception as e:
            raise LLMProviderError("zhipu", f"Unexpected error: {e}") from e

    async def complete_structured(
        self, prompt: str, system: str, schema: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured JSON output matching the provided schema.

        Zhipu supports JSON mode via response_format={"type": "json_object"} when the model supports it.
        We attempt structured mode first; if it fails, we fall back to raw generation + parse.
        """
        # Build messages
        messages: list[ZhipuMessage] = []
        if system:
            messages.append(ZhipuMessage(role="system", content=system))
        messages.append(ZhipuMessage(role="user", content=prompt))

        # Try structured mode first (JSON response format)
        request_data = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": params.get("temperature", 0.3),
            "top_p": params.get("top_p", 0.9),
            "response_format": {"type": "json_object"},
        }

        try:
            response = await with_retry(
                lambda: self.client.post("/chat/completions", json=request_data)
            )
            response.raise_for_status()
            result = response.json()

            if "choices" not in result or not result["choices"]:
                raise LLMProviderError("zhipu", "No choices returned in response")

            content = result["choices"][0]["message"]["content"]
            # Parse the JSON string into a dict
            try:
                parsed = json.loads(content)
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"Zhipu structured response not valid JSON: {content[:200]}, falling back to raw parse")
                # Fallthrough to raw extraction + manual parse

        except Exception as e:
            logger.info(f"Structured mode failed: {e}, will try raw approach with prompt instruction")

        # Fallback: generate raw and instruct user to parse JSON in the prompt
        response = await self.complete(prompt, system, params)
        try:
            parsed = self._extract_json(response.content)
            if parsed is not None:
                return parsed
        except Exception:
            pass

        # If all else failed, raise an error
        logger.error("Zhipu structured generation failed to produce valid JSON")
        raise LLMProviderError("zhipu", "Could not produce valid structured output")

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取 JSON 对象（支持嵌套结构）。"""
        # 尝试从 markdown 代码块中提取
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试贪婪匹配从第一个 { 到最后一个 }
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return None

    def validate_connection(self) -> bool:
        """Test if the API key is valid by making a minimal call."""
        if not self.api_key:
            return False
        try:
            response = httpx.get(
                "https://open.bigmodel.cn/api/prompt/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> ModelInfo:
        """Return info about the configured model."""
        return ModelInfo(
            provider="zhipu",
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