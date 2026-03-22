"""Centralized LLM construction so every agent shares the same config pattern."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from config.settings import settings


def build_llm(model_name: str, temperature: float | None = None) -> ChatOpenAI:
    """Build a ChatOpenAI-compatible LLM instance.

    DeepSeek / Qwen / any OpenAI-compatible endpoint can be used by
    configuring ``base_url`` and ``api_key`` in the environment.
    """
    return ChatOpenAI(
        model=model_name,
        api_key=settings.llm.api_key,
        base_url=settings.llm.base_url,
        temperature=temperature if temperature is not None else settings.llm.temperature,
        max_tokens=8192,
        max_retries=3,
        request_timeout=180,
    )
