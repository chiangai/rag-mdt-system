"""Endocrinologist Agent — evaluates metabolic risks and gives glycemic control advice."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.llm_factory import build_llm
from app.agents.utils import format_knowledge, robust_structured_invoke
from app.models.schemas import ExpertOpinion
from app.models.state import MDTState
from config.prompts.endocrinologist import ENDOCRINOLOGIST_SYSTEM_PROMPT
from config.settings import settings

logger = logging.getLogger(__name__)


async def endocrinologist_agent(state: MDTState) -> dict[str, Any]:
    """LangGraph node: produce an endocrinology expert opinion."""

    complaint = state.get("patient_complaint", "")
    entities = state.get("medical_entities", {})
    knowledge = state.get("graph_knowledge", {})

    try:
        llm = build_llm(settings.llm.endocrinologist_model)

        user_msg = (
            f"## 患者信息\n"
            f"主诉: {complaint}\n"
            f"提取实体: {entities}\n\n"
            f"## 知识图谱检索结果\n"
            f"{format_knowledge(knowledge)}\n\n"
            f"请从内分泌/代谢角度给出你的专家意见。department 字段请填写 '内分泌科'。"
        )

        logger.info("Endocrinologist agent generating opinion")

        result: ExpertOpinion = await robust_structured_invoke(llm, ExpertOpinion, [
            SystemMessage(content=ENDOCRINOLOGIST_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ])

        return {
            "expert_opinions": {"endocrinology": result.model_dump()},
        }

    except Exception as e:
        logger.error("Endocrinologist agent failed: %s", e)
        return {
            "expert_opinions": {"endocrinology": {"error": str(e)}},
            "errors": [f"内分泌专家智能体执行失败: {e}"],
        }
