"""LangChain tools for querying the Neo4j medical knowledge graph (async)."""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.tools import tool

from app.graph_db.connection import Neo4jConnection
from app.graph_db.templates import CYPHER_TEMPLATES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cypher safety validation — whitelist approach
# ---------------------------------------------------------------------------

_DANGEROUS_PATTERN = re.compile(
    r"\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP|DETACH|CALL|FOREACH|LOAD\s+CSV|PERIODIC\s+COMMIT)\b",
    re.IGNORECASE,
)

_ALLOWED_CLAUSE_PATTERN = re.compile(
    r"^\s*(MATCH|OPTIONAL\s+MATCH|WHERE|WITH|RETURN|ORDER\s+BY|LIMIT|SKIP|"
    r"UNWIND|UNION|AS|DISTINCT|AND|OR|NOT|IN|IS|CONTAINS|STARTS|ENDS|"
    r"CASE|WHEN|THEN|ELSE|END|count|collect|sum|avg|min|max|size|"
    r"toInteger|toFloat|toString|coalesce|head|last|labels|type|"
    r"NULL|TRUE|FALSE|DESC|ASC|ALL|ANY|NONE|SINGLE|EXISTS|\$|//)",
    re.IGNORECASE | re.MULTILINE,
)

MAX_RESULTS = 50


def _validate_cypher(query: str) -> str | None:
    """Return an error message if the query contains dangerous operations.

    Uses a two-layer check: blacklist for known dangerous keywords,
    then verifies every statement-starting token is an allowed read clause.
    """
    match = _DANGEROUS_PATTERN.search(query)
    if match:
        return f"安全拦截：禁止执行危险操作 ({match.group()})"

    for line in query.strip().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("$"):
            continue
        if not _ALLOWED_CLAUSE_PATTERN.match(stripped):
            if not any(
                stripped.upper().startswith(kw)
                for kw in (
                    "MATCH", "OPTIONAL", "WHERE", "WITH", "RETURN", "ORDER",
                    "LIMIT", "SKIP", "UNWIND", "UNION", "//", "-", "(", ")",
                    "[", "]", "{", "}", "'", '"', "AND", "OR", "NOT",
                )
            ):
                logger.warning("Cypher line failed whitelist check: %s", stripped[:80])
                return f"安全拦截：查询包含不允许的语句 ({stripped[:40]})"
    return None


@tool
async def execute_cypher(query: str, parameters: dict[str, Any] | None = None) -> str:
    """Execute a read-only Cypher query against the Neo4j knowledge graph.

    Args:
        query: A valid Cypher READ query (MATCH/RETURN only).
        parameters: Optional query parameters dict.

    Returns:
        JSON-formatted query results or an error message.
    """
    error = _validate_cypher(query)
    if error:
        logger.warning("Cypher rejected: %s", error)
        return error

    if "LIMIT" not in query.upper():
        query = query.rstrip().rstrip(";") + f"\nLIMIT {MAX_RESULTS}"

    try:
        records = await Neo4jConnection.execute_read(query, parameters or {})
        if not records:
            return "查询无结果"
        return str(records)
    except Exception as e:
        logger.error("Cypher execution failed: %s", e)
        return f"查询执行失败: {e}"


@tool
async def query_by_template(
    template_name: str,
    parameters: dict[str, Any],
) -> str:
    """Execute a pre-defined Cypher template query (safer than raw Cypher).

    Available templates:
    - disease_full_info: params {disease_name}
    - disease_by_symptoms: params {symptom_names: [...]}
    - drug_safety_info: params {drug_name}
    - drug_contraindications_batch: params {drug_names: [...]}
    - drug_interactions_check: params {drug_names: [...]}
    - department_knowledge: params {department_name}
    - risk_factors: params {disease_name}

    Args:
        template_name: Name of the template to use.
        parameters: Parameters to fill into the template.

    Returns:
        JSON-formatted query results or an error message.
    """
    template = CYPHER_TEMPLATES.get(template_name)
    if template is None:
        available = ", ".join(CYPHER_TEMPLATES.keys())
        return f"未知模板: {template_name}。可用模板: {available}"

    try:
        records = await Neo4jConnection.execute_read(template["query"], parameters)
        if not records:
            return "查询无结果"
        return str(records)
    except Exception as e:
        logger.error("Template query %s failed: %s", template_name, e)
        return f"模板查询失败: {e}"

@tool
async def vector_search(entity_type: str, query: str) -> str:
    """Execute a semantic vector similarity search on Disease or Symptom nodes.
    Use this when template queries return no results or when the entity name is colloquial.

    Args:
        entity_type: Must be 'Disease' or 'Symptom'.
        query: The medical term, synonym, or phrase to search for.

    Returns:
        JSON-formatted list of similar node names and their similarity scores.
    """
    if entity_type not in ["Disease", "Symptom"]:
        return "错误：entity_type 必须是 'Disease' 或 'Symptom'"
        
    try:
        from app.agents.embedding import get_embedding
        vector = await get_embedding(query)
    except Exception as e:
        logger.error("Failed to get embedding for query '%s': %s", query, e)
        return f"获取向量失败: {e}"
        
    index_name = f"vector_{entity_type.lower()}_name"
    cypher = f"""
        CALL db.index.vector.queryNodes($index_name, 3, $vector)
        YIELD node, score
        WHERE score > 0.5
        RETURN node.name AS name, score
    """
    
    try:
        records = await Neo4jConnection.execute_read(cypher, {"index_name": index_name, "vector": vector})
        if not records:
            return "向量查询无相近结果"
        return str(records)
    except Exception as e:
        logger.error("Vector search failed for %s: %s", query, e)
        return f"向量查询执行失败: {e}"
