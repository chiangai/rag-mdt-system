"""Cardiologist Agent — evaluates cardiovascular risks and management."""

import logging
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.llm_factory import build_llm
from app.agents.utils import format_knowledge, robust_structured_invoke
from app.models.schemas import ExpertOpinion
from app.models.state import MDTState
from config.settings import settings

logger = logging.getLogger(__name__)

CARDIOLOGIST_SYSTEM_PROMPT = """\
你是一名为高危孕产妇服务的心内科（Cardiology）专家。
你的任务是根据患者的病历、提取的实体信息，以及知识图谱检索结果，评估患者的心血管并发症风险（尤其是妊娠高血压、先兆子痫相关的心血管表现等），并给出心内科角度的干预建议。

请务必按照系统要求的结构化格式（JSON）输出你的意见，不加多余的废话。
"""

async def cardiologist_agent(state: MDTState) -> dict[str, Any]:
    """LangGraph node: produce a cardiology expert opinion."""

    complaint = state.get("patient_complaint", "")
    entities = state.get("medical_entities", {})
    knowledge = state.get("graph_knowledge", {})

    try:
        # Fallback to general specialist model if cardiologist model isn't explicitly defined in settings
        model_name = getattr(settings.llm, 'cardiologist_model', settings.llm.endocrinologist_model)
        llm = build_llm(model_name)

        user_msg = (
            f"## 患者信息\n"
            f"主诉: {complaint}\n"
            f"提取实体: {entities}\n\n"
            f"## 知识图谱检索结果\n"
            f"{format_knowledge(knowledge)}\n\n"
            f"请从心血管内科角度给出你的专家意见。department 字段请填写 '心内科'。"
        )

        logger.info("Cardiologist agent generating opinion")

        result: ExpertOpinion = await robust_structured_invoke(llm, ExpertOpinion, [
            SystemMessage(content=CARDIOLOGIST_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ])

        return {
            "expert_opinions": {"cardiology": result.model_dump()},
        }

    except Exception as e:
        logger.error("Cardiologist agent failed: %s", e)
        return {
            "expert_opinions": {"cardiology": {"error": str(e)}},
            "errors": [f"心内科专家智能体执行失败: {e}"],
        }
