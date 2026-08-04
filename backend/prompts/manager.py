import json
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).parent


class PromptManager:
    def __init__(self):
        self._registry: dict[str, Any] = {}
        self._cache: dict[str, dict[str, Any]] = {}
        self._load_registry()

    def _load_registry(self):
        registry_path = PROMPTS_DIR / "registry.json"
        with open(registry_path, 'r', encoding='utf-8') as f:  # ✅ 修复
            self._registry = json.load(f)

    def get_prompt(self, prompt_id: str, version: str | None = None) -> dict[str, Any]:
        if prompt_id not in self._registry:
            raise ValueError(f"Unknown prompt ID: {prompt_id}")

        version = version or self._registry[prompt_id]["latest_version"]
        cache_key = f"{prompt_id}:{version}"

        if cache_key not in self._cache:
            prompt_path = PROMPTS_DIR / prompt_id / f"v{version}.json"
            with open(prompt_path, 'r', encoding='utf-8') as f:  # ✅ 修复
                self._cache[cache_key] = json.load(f)

        return self._cache[cache_key]

    def render_prompt(self, prompt_id: str, variables: dict[str, str], version: str | None = None) -> str:
        template = self.get_prompt(prompt_id, version)
        prompt = template["user_prompt_template"]
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{key}}}", value)
        return prompt

    def get_system_prompt(self, prompt_id: str, version: str | None = None) -> str:
        template = self.get_prompt(prompt_id, version)
        return template["system_prompt"]

    def get_output_schema(self, prompt_id: str, version: str | None = None) -> dict[str, Any]:
        template = self.get_prompt(prompt_id, version)
        return template["output_schema"]

    def get_params(self, prompt_id: str, version: str | None = None) -> dict[str, Any]:
        template = self.get_prompt(prompt_id, version)
        return template["params"]

    def list_versions(self, prompt_id: str) -> list[str]:
        prompt_dir = PROMPTS_DIR / prompt_id
        versions = []
        for f in prompt_dir.iterdir():
            if f.name.startswith("v") and f.suffix == ".json":
                versions.append(f.name[1:].removesuffix(".json"))
        return sorted(versions)

    def list_prompts(self) -> list[dict[str, Any]]:
        return [{"id": k, **v} for k, v in self._registry.items()]


prompt_manager = PromptManager()