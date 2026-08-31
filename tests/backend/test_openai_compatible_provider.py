from __future__ import annotations

import json

import httpx
import pytest

from app.providers.openai_compatible import OpenAICompatibleProvider, ProviderConfigurationError


def test_provider_reads_key_only_in_server_request() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization")
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "后端模型回复"}}]})

    provider = OpenAICompatibleProvider(
        api_key="server-only-test-key",
        base_url="https://model.example/v1",
        model="demo-model",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    answer = provider.generate(route="health", message="我很疲惫", context=[], memory=[])

    assert answer == "后端模型回复"
    assert seen["authorization"] == "Bearer server-only-test-key"
    assert "server-only-test-key" not in str(seen["payload"])


def test_provider_rejects_missing_server_key() -> None:
    with pytest.raises(ProviderConfigurationError):
        OpenAICompatibleProvider(api_key="", base_url="https://model.example/v1", model="demo-model")
