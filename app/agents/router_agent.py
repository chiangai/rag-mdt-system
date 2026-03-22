"""Router / Planner Agent — triage patient complaints and decide specialist routing."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.llm_factory import build_llm
from app.agents.utils import sanitize_complaint, robust_structured_invoke
from app.models.schemas import RouterOutput
from app.models.state import MDTState
from config.prompts.router import ROUTER_SYSTEM_PROMPT
from config.settings import settings

logger = logging.getLogger(__name__)


async def router_agent(state: MDTState) -> dict[str, Any]:
    """LangGraph node: parse patient complaint -> entities + department routing."""

    complaint = sanitize_complaint(state.get("patient_complaint", ""))
    if not complaint:
        return {
            "errors": ["导诊智能体：未收到患者主诉"],
            "required_departments": ["obstetrics"],
        }

    logger.info("Router agent processing complaint: %s", complaint[:80])

    try:
        llm = build_llm(settings.llm.router_model)

        result: RouterOutput = await robust_structured_invoke(llm, RouterOutput, [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=f"患者主诉：{complaint}"),
        ])

        consultation_id = state.get("consultation_id") or str(uuid.uuid4())[:12]

        logger.info(
            "Router decision — departments: %s, urgency: %s",
            result.required_departments,
            result.urgency,
        )

        return {
            "consultation_id": consultation_id,
            "medical_entities": result.medical_entities.model_dump(),
            "required_departments": result.required_departments,
            "urgency": result.urgency,
        }
    except Exception as e:
        logger.error("Router agent failed: %s", e)
        return {
            "errors": [f"导诊智能体执行失败: {e}"],
            "required_departments": ["obstetrics"],
            "urgency": "moderate",
            "medical_entities": {},
        }
