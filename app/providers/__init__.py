"""Server-side model provider adapters. Secrets never cross this boundary."""

from app.providers.openai_compatible import OpenAICompatibleProvider, provider_from_env

__all__ = ["OpenAICompatibleProvider", "provider_from_env"]
