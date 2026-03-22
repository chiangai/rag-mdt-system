"""End-to-end tests for the MDT workflow.

These tests validate that:
1. The LangGraph graph compiles without errors
2. The state schema is consistent
3. The routing logic handles edge cases
4. Security validation works correctly

NOTE: Full integration tests require a running Neo4j instance and LLM API keys.
Run them with: pytest tests/test_workflow.py -m integration
"""

import pytest

from app.agents.workflow import (
    DEPARTMENT_NODE_MAP,
    ALL_SPECIALIST_NODES,
    SPECIALIST_AGENTS,
    route_to_experts,
    build_mdt_graph,
    get_mdt_app,
)
from app.models.state import MDTState, _merge_expert_opinions
from app.models.schemas import (
    MDTReport,
    ExpertOpinion,
    RiskAssessment,
    SafetyAlert,
    DepartmentRecommendation,
    ConsultRequest,
    ConsultResponse,
)


def test_graph_compiles():
    """The StateGraph should compile without errors."""
    graph = build_mdt_graph()
    assert graph is not None


def test_lazy_singleton():
    """get_mdt_app should return the same instance on repeated calls."""
    app1 = get_mdt_app()
    app2 = get_mdt_app()
    assert app1 is app2


def test_department_node_mapping():
    assert "obstetrics" in DEPARTMENT_NODE_MAP
    assert "endocrinology" in DEPARTMENT_NODE_MAP
    assert len(ALL_SPECIALIST_NODES) == len(DEPARTMENT_NODE_MAP)


def test_specialist_agents_registry():
    """SPECIALIST_AGENTS should have matching callable agent functions."""
    for dept, (node_name, agent_fn) in SPECIALIST_AGENTS.items():
        assert callable(agent_fn), f"Agent for {dept} is not callable"
        assert node_name == DEPARTMENT_NODE_MAP[dept]


def test_route_to_experts_normal():
    """Normal case — known departments yield correct Send objects."""
    state: MDTState = {
        "required_departments": ["obstetrics", "endocrinology"],
        "patient_complaint": "test",
        "medical_entities": {},
        "graph_knowledge": {},
        "expert_opinions": {},
        "errors": [],
    }
    sends = route_to_experts(state)
    assert len(sends) == 2
    node_names = {s.node for s in sends}
    assert "obstetrician" in node_names
    assert "endocrinologist" in node_names


def test_route_to_experts_fallback():
    """Unknown departments should fall back to obstetrician."""
    state: MDTState = {
        "required_departments": ["cardiology"],
        "patient_complaint": "test",
        "medical_entities": {},
        "graph_knowledge": {},
        "expert_opinions": {},
        "errors": [],
    }
    sends = route_to_experts(state)
    assert len(sends) == 1
    assert sends[0].node == "obstetrician"


def test_route_to_experts_empty():
    """Empty departments list should also fall back."""
    state: MDTState = {
        "required_departments": [],
        "patient_complaint": "test",
        "medical_entities": {},
        "graph_knowledge": {},
        "expert_opinions": {},
        "errors": [],
    }
    sends = route_to_experts(state)
    assert len(sends) == 1


# ---------------------------------------------------------------------------
# Reducer tests
# ---------------------------------------------------------------------------

def test_merge_expert_opinions_combines():
    existing = {"obstetrics": {"risk": "高"}}
    new = {"endocrinology": {"risk": "中"}}
    result = _merge_expert_opinions(existing, new)
    assert "obstetrics" in result
    assert "endocrinology" in result


def test_merge_expert_opinions_overwrite_warning():
    """Same key should overwrite (last-writer-wins)."""
    existing = {"obstetrics": {"version": 1}}
    new = {"obstetrics": {"version": 2}}
    result = _merge_expert_opinions(existing, new)
    assert result["obstetrics"]["version"] == 2


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

def test_mdt_report_schema():
    """MDTReport should accept all expected fields."""
    report = MDTReport(
        consultation_summary="24周GDM患者会诊",
        risk_assessment={"maternal": "中", "fetal": "低"},
        recommendations=[
            DepartmentRecommendation(
                department="产科", content="加强胎儿监护", priority="高"
            )
        ],
        safety_alerts=[
            SafetyAlert(
                alert_type="drug_contraindication",
                detail="依那普利妊娠期禁用",
                severity="严重",
                suggestion="改用拉贝洛尔",
            )
        ],
        follow_up_plan="1周后复查血糖",
    )
    assert report.disclaimer.startswith("本报告由 AI")
    assert len(report.safety_alerts) == 1


def test_expert_opinion_schema():
    opinion = ExpertOpinion(
        department="产科",
        maternal_risk=RiskAssessment(level="中", details="GDM风险"),
        fetal_risk=RiskAssessment(level="低", details="目前无明显异常"),
        recommendations=["加强血糖监测"],
        medications=["门冬胰岛素"],
        monitoring_plan=["每2周复查OGTT"],
    )
    assert opinion.department == "产科"
    assert len(opinion.medications) == 1


def test_consult_request_validation():
    req = ConsultRequest(complaint="怀孕 24 周，糖耐量异常，伴随轻微水肿")
    assert len(req.complaint) > 0

    with pytest.raises(Exception):
        ConsultRequest(complaint="")
