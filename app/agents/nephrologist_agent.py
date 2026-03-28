"""Nephrologist Agent — evaluates renal risks and management."""

import logging
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.llm_factory import build_llm
from app.agents.utils import format_knowledge, robust_structured_invoke
from app.models.schemas import ExpertOpinion
from app.models.state import MDTState
from config.settings import settings

logger = logging.getLogger(__name__)

NEPHROLOGIST_SYSTEM_PROMPT = """\
你是一名为高危孕产妇服务的肾内科（Nephrology）专家。
你的任务是根据患者的病历、提取的实体信息，以及知识图谱检索结果，评估患者的肾脏功能损伤风险（尤其是蛋白尿、子痫前期引发的肾脏并发症等），并给出肾内科角度的干预建议。

请务必按照系统要求的结构化格式（JSON）输出你的意见，不加多余的废话。
"""

async def nephrologist_agent(state: MDTState) -> dict[str, Any]:
    """LangGraph node: produce a nephrology expert opinion."""

    complaint = state.get("patient_complaint", "")
    entities = state.get("medical_entities", {})
    knowledge = state.get("graph_knowledge", {})

    try:
        # Fallback to general specialist model if nephrologist model isn't explicitly defined in settings
        model_name = getattr(settings.llm, 'nephrologist_model', settings.llm.endocrinologist_model)
        llm = build_llm(model_name)

        user_msg = (
            f"## 患者信息\n"
            f"主诉: {complaint}\n"
            f"提取实体: {entities}\n\n"
            f"## 知识图谱检索结果\n"
            f"{format_knowledge(knowledge)}\n\n"
            f"请从肾内科角度给出你的专家意见。department 字段请填写 '肾内科'。"
        )

        logger.info("Nephrologist agent generating opinion")

        result: ExpertOpinion = await robust_structured_invoke(llm, ExpertOpinion, [
            SystemMessage(content=NEPHROLOGIST_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ])

        return {
            "expert_opinions": {"nephrology": result.model_dump()},
        }

    except Exception as e:
        logger.error("Nephrologist agent failed: %s", e)
        return {
            "expert_opinions": {"nephrology": {"error": str(e)}},
            "errors": [f"肾内科专家智能体执行失败: {e}"],
        }
