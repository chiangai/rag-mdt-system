"""Shared utilities for agent modules — eliminates code duplication."""

from __future__ import annotations

import copy
import json
import logging
import re
from typing import Any, Type, TypeVar

from pydantic import BaseModel


def format_knowledge(knowledge: dict, max_items_per_key: int | None = None) -> str:
    """Flatten the graph_knowledge dict into a readable string for the LLM."""
    parts: list[str] = []
    for key, value in knowledge.items():
        parts.append(f"### {key}")
        if isinstance(value, list):
            items = value[:max_items_per_key] if max_items_per_key else value
            for item in items:
                parts.append(str(item))
        else:
            parts.append(str(value))
    return "\n".join(parts) if parts else "暂无相关知识图谱数据"


_INPUT_SANITIZE_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
MAX_COMPLAINT_LENGTH = 2000


def sanitize_complaint(complaint: str) -> str:
    """Basic sanitization of patient complaint text.

    Strips control characters and truncates excessively long inputs to
    limit token consumption and reduce prompt injection surface.
    """
    cleaned = _INPUT_SANITIZE_PATTERN.sub("", complaint)
    if len(cleaned) > MAX_COMPLAINT_LENGTH:
        cleaned = cleaned[:MAX_COMPLAINT_LENGTH] + "…（输入过长已截断）"
    return cleaned.strip()


T = TypeVar("T", bound=BaseModel)

def _strip_think_tags(content: str) -> str:
    think_end = content.find("</think>")
    if think_end != -1:
        return content[think_end + len("</think>"):].strip()
    return content.strip()


def _extract_json_candidate(content: str) -> str:
    content = _strip_think_tags(content)
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end >= start:
        return content[start:end + 1].strip()
    return content.strip()


def _build_fallback_messages(
    messages: list[Any],
    schema: Type[T],
    stronger: bool = False,
) -> list[Any]:
    fallback_messages = copy.deepcopy(messages)
    schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
    extra = (
        "\n\n请严格输出一个合法 JSON 对象，不要包含任何额外解释文本。"
        "如果必须输出思考过程，请放入 <think></think>，最终答案只保留 JSON。"
        f"\nJSON Schema:\n{schema_json}"
    )
    if stronger:
        extra += "\n再次强调：不要输出 Markdown 代码块，不要输出前后缀文本，只输出 JSON。"

    if fallback_messages and hasattr(fallback_messages[-1], "content"):
        content = getattr(fallback_messages[-1], "content", "")
        if isinstance(content, str):
            fallback_messages[-1].content = content + extra
            return fallback_messages

    class _InlinePrompt:
        def __init__(self, content: str):
            self.content = content

    fallback_messages.append(_InlinePrompt(extra))
    return fallback_messages


async def robust_structured_invoke(llm: Any, schema: Type[T], messages: list[Any]) -> T:
    """Invoke LLM and robustly parse structured output with fallback retries."""
    logger = logging.getLogger(__name__)

    try:
        structured_llm = llm.with_structured_output(schema)
        return await structured_llm.ainvoke(messages)
    except Exception as e:
        logger.warning("Structured output path failed, falling back to JSON extraction: %s", e)

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            fallback_messages = _build_fallback_messages(
                messages, schema, stronger=(attempt > 0)
            )
            response = await llm.ainvoke(fallback_messages)
            content = response.content if hasattr(response, "content") else str(response)
            data = json.loads(_extract_json_candidate(content))
            return schema.model_validate(data)
        except Exception as e:
            last_error = e
            logger.warning(
                "Fallback structured parse attempt %d failed: %s | content preview: %s",
                attempt + 1,
                e,
                (content[:200] if "content" in locals() else "<no content>"),
            )

    raise ValueError(
        f"Unable to produce valid structured output for schema {schema.__name__}: {last_error}"
    )
