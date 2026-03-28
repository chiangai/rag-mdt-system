import asyncio

import pytest
from pydantic import BaseModel

from app.agents.utils import robust_structured_invoke


class DemoSchema(BaseModel):
    name: str
    score: int


class _Response:
    def __init__(self, content: str):
        self.content = content


class _StructuredLLM:
    def __init__(self, result=None, error: Exception | None = None):
        self._result = result
        self._error = error

    async def ainvoke(self, messages):
        if self._error:
            raise self._error
        return self._result


class _LLM:
    def __init__(self, structured=None, fallback_contents=None, structured_error=None):
        self._structured = structured
        self._structured_error = structured_error
        self._fallback_contents = fallback_contents or []
        self._idx = 0

    def with_structured_output(self, schema):
        if self._structured_error:
            raise self._structured_error
        return _StructuredLLM(result=self._structured)

    async def ainvoke(self, messages):
        content = self._fallback_contents[min(self._idx, len(self._fallback_contents) - 1)]
        self._idx += 1
        return _Response(content)


def test_structured_path_success():
    llm = _LLM(structured=DemoSchema(name="alice", score=95))
    out = asyncio.run(
        robust_structured_invoke(llm, DemoSchema, [{"role": "user", "content": "x"}])
    )
    assert out.name == "alice"
    assert out.score == 95


def test_fallback_parses_fenced_json():
    llm = _LLM(
        structured_error=RuntimeError("structured failed"),
        fallback_contents=['```json\n{"name":"bob","score":88}\n```'],
    )
    out = asyncio.run(
        robust_structured_invoke(llm, DemoSchema, [{"role": "user", "content": "x"}])
    )
    assert out == DemoSchema(name="bob", score=88)


def test_fallback_parses_think_wrapped_json():
    llm = _LLM(
        structured_error=RuntimeError("structured failed"),
        fallback_contents=['<think>analysis</think>{"name":"carol","score":77}'],
    )
    out = asyncio.run(
        robust_structured_invoke(llm, DemoSchema, [{"role": "user", "content": "x"}])
    )
    assert out == DemoSchema(name="carol", score=77)


def test_fallback_raises_after_two_failures():
    llm = _LLM(
        structured_error=RuntimeError("structured failed"),
        fallback_contents=["not json", "still not json"],
    )
    with pytest.raises(ValueError):
        asyncio.run(
            robust_structured_invoke(llm, DemoSchema, [{"role": "user", "content": "x"}])
        )
