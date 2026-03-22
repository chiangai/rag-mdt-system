"""LangGraph StateGraph workflow — the core MDT orchestration engine.

Flow:
  START -> router -> graph_query -> [specialists in parallel] -> reviewer -> END

The conditional fan-out after graph_query dynamically routes to specialist
agents based on the ``required_departments`` list produced by the router.
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import StateGraph, END, START
from langgraph.types import Send

from app.agents.router_agent import router_agent
from app.agents.graph_query_agent import graph_query_agent
from app.agents.obstetrician_agent import obstetrician_agent
from app.agents.endocrinologist_agent import endocrinologist_agent
from app.agents.reviewer_agent import reviewer_agent
from app.models.state import MDTState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Department -> (node_name, agent_fn) registry
# To add a new specialist: just add an entry here + create the agent file.
# ---------------------------------------------------------------------------

SPECIALIST_AGENTS: dict[str, tuple[str, Any]] = {
    "obstetrics": ("obstetrician", obstetrician_agent),
    "endocrinology": ("endocrinologist", endocrinologist_agent),
}

DEPARTMENT_NODE_MAP: dict[str, str] = {
    dept: node_name for dept, (node_name, _) in SPECIALIST_AGENTS.items()
}

ALL_SPECIALIST_NODES = list(DEPARTMENT_NODE_MAP.values())


# ---------------------------------------------------------------------------
# Conditional routing function
# ---------------------------------------------------------------------------

def route_to_experts(state: MDTState) -> list[Send]:
    """Determine which specialist agents to activate based on Router output.

    Returns a list of ``Send`` objects so that LangGraph fans out to
    multiple specialist nodes in parallel.
    """
    departments = state.get("required_departments", [])
    sends: list[Send] = []

    for dept in departments:
        node = DEPARTMENT_NODE_MAP.get(dept)
        if node:
            sends.append(Send(node, state))
            logger.info("Routing to specialist: %s (%s)", node, dept)

    if not sends:
        logger.warning(
            "No matching specialists for departments %s — defaulting to obstetrician",
            departments,
        )
        sends.append(Send("obstetrician", state))

    return sends


# ---------------------------------------------------------------------------
# Build the graph (lazy initialization)
# ---------------------------------------------------------------------------

_compiled_graph = None


def build_mdt_graph():
    """Construct and compile the MDT consultation StateGraph."""

    workflow = StateGraph(MDTState)

    workflow.add_node("router", router_agent)
    workflow.add_node("graph_query", graph_query_agent)
    workflow.add_node("reviewer", reviewer_agent)

    for dept, (node_name, agent_fn) in SPECIALIST_AGENTS.items():
        workflow.add_node(node_name, agent_fn)
        workflow.add_edge(node_name, "reviewer")

    workflow.add_edge(START, "router")
    workflow.add_edge("router", "graph_query")
    workflow.add_conditional_edges("graph_query", route_to_experts)
    workflow.add_edge("reviewer", END)

    return workflow.compile()


def get_mdt_app():
    """Lazy singleton — compiles the graph on first call."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_mdt_graph()
    return _compiled_graph
