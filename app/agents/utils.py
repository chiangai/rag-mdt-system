"""Shared utilities for agent modules — eliminates code duplication."""

from __future__ import annotations

import re


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


import json
from pydantic import BaseModel
from typing import TypeVar, Type

T = TypeVar("T", bound=BaseModel)

async def robust_structured_invoke(llm: Any, schema: Type[T], messages: list[Any]) -> T:
    """Robustly extract JSON from LLM outputs, specially handling Thinking models.
    Directly prompts for JSON and extracts via regex to avoid duplicate LLM calls
    that cause timeouts with slow reasoning models.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    import copy
    fallback_messages = copy.deepcopy(messages)
    if hasattr(fallback_messages[-1], "content"):
        fallback_prompt = (
            f"\n\n请务必严格按照以下 JSON Schema 输出内容，输出必须是纯净的合法 JSON，"
            f"如果有思考过程请全部放在 <think></think> 标签内，真正的结果切勿包含任何多余文本或错误引号："
            f"\n{schema.schema_json()}"
        )
        if isinstance(fallback_messages[-1].content, str):
            fallback_messages[-1].content += fallback_prompt
    
    response = await llm.ainvoke(fallback_messages)
    content = response.content
    
    # Strip <think> tags if present
    think_end = content.find("</think>")
    if think_end != -1:
        content = content[think_end + 8:]
        
    # Try to find JSON block
    import re
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(1)
    else:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            json_str = content[start:end+1]
        else:
            json_str = content
            
    try:
        from pydantic_core import from_json
        data = json.loads(json_str)
        return schema(**data)
    except Exception as inner_e:
        logger.error("Robust extraction failed: %s. Content was: %s", inner_e, content[:200])
        raise inner_e
