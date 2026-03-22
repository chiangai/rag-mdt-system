"""Graph Query Agent — translates medical entities to Cypher and retrieves knowledge."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from app.agents.llm_factory import build_llm
from app.models.state import MDTState
from app.tools.neo4j_tools import execute_cypher, query_by_template, vector_search
from config.prompts.graph_query import GRAPH_QUERY_SYSTEM_PROMPT
from config.settings import settings

logger = logging.getLogger(__name__)

_TOOLS = [execute_cypher, query_by_template, vector_search]


async def graph_query_agent(state: MDTState) -> dict[str, Any]:
    """LangGraph node: query Neo4j knowledge graph based on extracted entities."""

    entities = state.get("medical_entities", {})
    departments = state.get("required_departments", [])

    logger.info(
        "Graph query agent — entities: %s, departments: %s",
        entities,
        departments,
    )

    try:
        llm = build_llm(settings.llm.graph_query_model)
        llm_with_tools = llm.bind_tools(_TOOLS)

        user_msg = (
            f"请根据以下医学实体从知识图谱中检索相关知识：\n"
            f"医学实体: {entities}\n"
            f"涉及科室: {departments}\n\n"
            f"请为每个涉及的科室分别检索相关的疾病、治疗方案、药物和禁忌信息。"
        )

        messages = [
            SystemMessage(content=GRAPH_QUERY_SYSTEM_PROMPT),
            HumanMessage(content=user_msg + "\n请最多只调用 2 次查询工具。不要进行过多无关的查询以节省时间。"),
        ]

        graph_knowledge: dict[str, Any] = {}
        tool_map = {t.name: t for t in _TOOLS}

        max_iterations = 2
        for iteration in range(max_iterations):
            logger.info("Graph query agent checking tools (iteration %d)", iteration)
            response = await llm_with_tools.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                tool_fn = tool_map.get(tool_name)
                if tool_fn is None:
                    tool_result = f"未知工具: {tool_name}"
                else:
                    tool_result = await tool_fn.ainvoke(tool_args)

                messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
                )

                if isinstance(tool_result, str) and "查询无结果" not in tool_result and "失败" not in tool_result:
                    _merge_knowledge(graph_knowledge, tool_name, tool_args, tool_result)
        else:
            logger.warning("Graph query agent hit max iterations (%d) — results may be incomplete", max_iterations)

        logger.info("Graph query agent retrieved knowledge for %d topics", len(graph_knowledge))
        return {"graph_knowledge": graph_knowledge}

    except Exception as e:
        logger.error("Graph query agent failed: %s", e)
        return {
            "graph_knowledge": {},
            "errors": [f"图谱查询智能体执行失败: {e}"],
        }


def _merge_knowledge(
    knowledge: dict[str, Any],
    tool_name: str,
    tool_args: dict,
    result: str,
) -> None:
    """Organize query results into a department-oriented structure."""
    if tool_name == "query_by_template":
        template = tool_args.get("template_name", "unknown")
        knowledge.setdefault(template, []).append({
            "params": tool_args.get("parameters", {}),
            "result": result,
        })
    elif tool_name == "vector_search":
        knowledge.setdefault("vector_search_results", []).append({
            "entity": tool_args.get("query", ""),
            "type": tool_args.get("entity_type", ""),
            "result": result,
        })
    else:
        knowledge.setdefault("custom_queries", []).append({
            "query": tool_args.get("query", ""),
            "result": result,
        })
