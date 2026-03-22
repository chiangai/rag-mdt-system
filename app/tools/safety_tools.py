"""Safety-specific async tools for the Reviewer Agent to cross-validate drug info."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import tool

from app.graph_db.connection import Neo4jConnection
from app.graph_db.templates import CYPHER_TEMPLATES

logger = logging.getLogger(__name__)


@tool
async def check_drug_contraindications(drug_names: list[str]) -> str:
    """Batch-check contraindications for a list of drug names.

    Args:
        drug_names: List of drug names to check.

    Returns:
        Contraindication information for each drug.
    """
    if not drug_names:
        return "未提供药物名称"

    template = CYPHER_TEMPLATES["drug_contraindications_batch"]
    try:
        records = await Neo4jConnection.execute_read(
            template["query"],
            {"drug_names": drug_names},
        )
        if not records:
            return "未查到相关药物禁忌信息"
        return str(records)
    except Exception as e:
        logger.error("Contraindication check failed: %s", e)
        return f"药物禁忌查询失败: {e}"


@tool
async def check_drug_interactions(drug_names: list[str]) -> str:
    """Check pair-wise interactions among a list of drugs.

    Args:
        drug_names: List of drug names to check interactions between.

    Returns:
        Drug interaction information.
    """
    if len(drug_names) < 2:
        return "至少需要 2 种药物才能检查相互作用"

    template = CYPHER_TEMPLATES["drug_interactions_check"]
    try:
        records = await Neo4jConnection.execute_read(
            template["query"],
            {"drug_names": drug_names},
        )
        if not records:
            return "未发现药物间相互作用"
        return str(records)
    except Exception as e:
        logger.error("Interaction check failed: %s", e)
        return f"药物相互作用查询失败: {e}"


@tool
async def check_fda_pregnancy_category(drug_names: list[str]) -> str:
    """Look up the FDA pregnancy category for a list of drugs.

    Args:
        drug_names: List of drug names to look up.

    Returns:
        FDA category information for each drug.
    """
    if not drug_names:
        return "未提供药物名称"

    query = """
        UNWIND $drug_names AS dn
        MATCH (d:Drug)
        WHERE d.name CONTAINS dn
        RETURN d.name AS name, d.generic_name AS generic_name,
               d.fda_category AS fda_category
    """
    try:
        records = await Neo4jConnection.execute_read(query, {"drug_names": drug_names})
        if not records:
            return "未查到相关药物 FDA 分级信息"
        return str(records)
    except Exception as e:
        logger.error("FDA category lookup failed: %s", e)
        return f"FDA 分级查询失败: {e}"
