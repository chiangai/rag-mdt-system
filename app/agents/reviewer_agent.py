"""Reviewer / Safety Agent — cross-validates expert opinions and generates the final MDT report."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.llm_factory import build_llm
from app.agents.utils import format_knowledge, robust_structured_invoke
from app.models.schemas import MDTReport
from app.models.state import MDTState
from app.tools.safety_tools import (
    check_drug_contraindications,
    check_drug_interactions,
    check_fda_pregnancy_category,
)
from config.prompts.reviewer import REVIEWER_SYSTEM_PROMPT
from config.settings import settings

logger = logging.getLogger(__name__)

_TOOLS = [check_drug_contraindications, check_drug_interactions, check_fda_pregnancy_category]


async def reviewer_agent(state: MDTState) -> dict[str, Any]:
    """LangGraph node: review all expert opinions, run safety checks, produce final report."""

    expert_opinions = state.get("expert_opinions", {})
    knowledge = state.get("graph_knowledge", {})
    complaint = state.get("patient_complaint", "")
    entities = state.get("medical_entities", {})

    all_medications = _collect_medications(expert_opinions)

    logger.info(
        "Reviewer agent — %d expert opinions, %d drugs to check",
        len(expert_opinions),
        len(all_medications),
    )

    # --- Phase 1: tool-based safety checks with degradation tracking ---
    safety_data: list[str] = []
    safety_failures = 0

    if all_medications:
        async def _run_tool(tool_fn):
            try:
                result = await tool_fn.ainvoke({"drug_names": all_medications})
                return tool_fn.name, result, None
            except Exception as e:
                return tool_fn.name, None, e

        results = await asyncio.gather(*[_run_tool(t) for t in _TOOLS])
        for name, result, err in results:
            if err is not None:
                safety_failures += 1
                logger.warning("Safety tool %s failed: %s", name, err)
                safety_data.append(f"[{name}] 查询失败: {err}")
            else:
                safety_data.append(f"[{name}] {result}")

        if safety_failures > 0:
            degradation_warning = (
                f"⚠️ 严重警告：{safety_failures}/{len(_TOOLS)} 项药物安全检查未能完成，"
                "报告中的药物安全信息可能不完整，所有药物建议必须经人工复核！"
            )
            safety_data.append(degradation_warning)
            logger.error("Safety check degraded: %d/%d tools failed", safety_failures, len(_TOOLS))

    # Check for failed expert opinions
    expert_failures = [
        dept for dept, opinion in expert_opinions.items()
        if isinstance(opinion, dict) and "error" in opinion
    ]
    if expert_failures:
        safety_data.append(
            f"⚠️ 警告：以下科室专家智能体执行失败，意见缺失: {', '.join(expert_failures)}"
        )

    # --- Phase 2: LLM-based review and report generation ---
    try:
        llm = build_llm(settings.llm.reviewer_model)

        user_msg = (
            f"## 患者信息\n"
            f"主诉: {complaint}\n"
            f"提取实体: {entities}\n\n"
            f"## 各科室专家意见\n"
            f"{_format_opinions(expert_opinions)}\n\n"
            f"## 药物安全性数据（来自知识图谱）\n"
            f"{chr(10).join(safety_data) if safety_data else '无药物安全数据'}\n\n"
            f"## 知识图谱参考\n"
            f"{format_knowledge(knowledge, max_items_per_key=3)}\n\n"
            f"请执行三道安全关卡审查，并生成最终 MDT 会诊报告。"
        )

        report: MDTReport = await robust_structured_invoke(llm, MDTReport, [
            SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ])

        if safety_failures > 0:
            from app.models.schemas import SafetyAlert
            report.safety_alerts.insert(0, SafetyAlert(
                alert_type="system_degradation",
                detail=f"{safety_failures}/{len(_TOOLS)} 项药物安全检查未完成",
                severity="严重",
                suggestion="所有药物建议必须经临床药师人工复核",
            ))

        logger.info(
            "Reviewer produced report with %d alerts", len(report.safety_alerts)
        )

        return {
            "safety_alerts": [a.model_dump() for a in report.safety_alerts],
            "final_report": report.model_dump(),
        }

    except Exception as e:
        logger.error("Reviewer agent failed: %s", e)
        return {
            "final_report": {
                "consultation_summary": "会诊报告生成失败",
                "risk_assessment": {"maternal": "未知", "fetal": "未知"},
                "recommendations": [],
                "safety_alerts": [{"alert_type": "system_error", "detail": str(e), "severity": "严重", "suggestion": "请人工会诊"}],
                "follow_up_plan": "系统异常，请联系技术支持并安排人工会诊",
                "disclaimer": "本报告由 AI 辅助生成，仅供临床参考，不替代医生诊断。系统运行出现异常，结果可能不完整。",
            },
            "errors": [f"安全审查智能体执行失败: {e}"],
        }


def _collect_medications(opinions: dict[str, Any]) -> list[str]:
    """Gather all drug names mentioned across expert opinions."""
    meds: set[str] = set()
    for opinion in opinions.values():
        if isinstance(opinion, dict):
            for med in opinion.get("medications", []):
                meds.add(med)
    return list(meds)


def _format_opinions(opinions: dict[str, Any]) -> str:
    parts: list[str] = []
    for dept, opinion in opinions.items():
        parts.append(f"### {dept}")
        if isinstance(opinion, dict):
            if "error" in opinion:
                parts.append(f"- ⚠️ 该科室智能体执行失败: {opinion['error']}")
            else:
                for key, val in opinion.items():
                    parts.append(f"- {key}: {val}")
        else:
            parts.append(str(opinion))
    return "\n".join(parts) if parts else "暂无专家意见"
