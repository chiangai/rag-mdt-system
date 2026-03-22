"""LangGraph shared state definition for the MDT workflow."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


def _merge_expert_opinions(
    existing: dict[str, Any],
    new: dict[str, Any],
) -> dict[str, Any]:
    """Reducer that merges new expert opinions into existing ones."""
    merged = {**existing}
    merged.update(new)
    return merged


class MDTState(TypedDict, total=False):
    """Shared state that flows through the entire MDT consultation graph.

    Fields use LangGraph reducers so that parallel specialist nodes can
    independently write their opinions and the results are merged
    automatically when the graph converges at the reviewer node.
    """

    consultation_id: str
    patient_complaint: str

    # Router agent output
    medical_entities: dict[str, Any]
    required_departments: list[str]
    urgency: str

    # Graph Query agent output
    graph_knowledge: dict[str, Any]

    # Specialist agents output (merged via reducer)
    expert_opinions: Annotated[dict[str, Any], _merge_expert_opinions]

    # Reviewer agent output
    drug_contraindications: list[dict[str, Any]]
    safety_alerts: list[dict[str, Any]]
    final_report: dict[str, Any]

    # Error tracking
    errors: Annotated[list[str], operator.add]
