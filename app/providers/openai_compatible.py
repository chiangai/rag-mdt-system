from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


class ProviderConfigurationError(ValueError):
    """Raised when the server has no usable model configuration."""


@dataclass
class OpenAICompatibleProvider:
    """Minimal OpenAI-compatible client kept entirely on the API server."""

    api_key: str
    base_url: str
    model: str
    timeout_seconds: float = 25.0
    client: httpx.Client | None = None

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ProviderConfigurationError("server model API key is missing")
        if not self.base_url.startswith(("https://", "http://")):
            raise ProviderConfigurationError("server model base URL is invalid")
        if not self.model.strip():
            raise ProviderConfigurationError("server model name is missing")

    def generate(self, *, route: str, message: str, context: list[dict], memory: list[dict]) -> str:
        system = "你是 HerCare 的产后健康信息助手。给出谨慎、简短的健康信息；不诊断、不处方。"
        if route == "chat":
            system = "你是 HerCare 的陪伴式产后健康助手。简短、温和地回应，不作医疗判断。"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                *[{"role": item.get("role", "user"), "content": item.get("content", "")} for item in memory[-6:]],
                {"role": "user", "content": self._contextual_message(message, context)},
            ],
            "temperature": 0.3,
        }
        client = self.client or httpx.Client(timeout=self.timeout_seconds)
        close_client = self.client is None
        try:
            response = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise RuntimeError("model returned an empty answer")
            return content.strip()
        finally:
            if close_client:
                client.close()

    @staticmethod
    def _contextual_message(message: str, context: list[dict]) -> str:
        if not context:
            return message
        sources = "\n".join(f"- {item.get('title') or item.get('name') or '知识图谱条目'}" for item in context[:4])
        return f"用户问题：{message}\n\n可参考的受控知识：\n{sources}"


def provider_from_env() -> OpenAICompatibleProvider | None:
    """Return a server-side provider when configured; otherwise retain safe fallback."""
    api_key = os.getenv("HERCARE_LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("HERCARE_LLM_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.deepseek.com"
    model = os.getenv("HERCARE_LLM_MODEL") or os.getenv("ROUTER_MODEL") or "deepseek-chat"
    return OpenAICompatibleProvider(api_key=api_key, base_url=base_url, model=model)
