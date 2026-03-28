"""Pydantic models for API request / response and structured LLM outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Router Agent structured output
# ---------------------------------------------------------------------------

class MedicalEntities(BaseModel):
    gestational_week: int | None = Field(None, description="孕周")
    symptoms: list[str] = Field(default_factory=list, description="症状列表")
    conditions: list[str] = Field(default_factory=list, description="疑似/确诊疾病")
    vitals: dict[str, str] = Field(default_factory=dict, description="生命体征")
    medical_history: list[str] = Field(default_factory=list, description="既往病史")
    current_medications: list[str] = Field(default_factory=list, description="当前用药")


class RouterOutput(BaseModel):
    medical_entities: MedicalEntities
    required_departments: list[str] = Field(
        ..., description="需要介入的科室列表，如 obstetrics, endocrinology"
    )
    urgency: str = Field(
        "moderate",
        description="紧急程度: critical / high / moderate / low",
    )
    reasoning: str = Field("", description="分诊推理过程")


# ---------------------------------------------------------------------------
# Specialist Agent structured outputs
# ---------------------------------------------------------------------------

class RiskAssessment(BaseModel):
    level: str = Field(..., description="风险等级: 低/中/高/极高")
    details: str = Field(..., description="风险详情")


class ExpertOpinion(BaseModel):
    department: str = Field(..., description="科室名称")
    maternal_risk: RiskAssessment = Field(..., description="母体风险评估")
    fetal_risk: RiskAssessment = Field(..., description="胎儿风险评估")
    recommendations: list[str] = Field(default_factory=list, description="诊疗建议")
    medications: list[str] = Field(default_factory=list, description="建议用药")
    monitoring_plan: list[str] = Field(default_factory=list, description="监测计划")
    cross_department_notes: list[str] = Field(
        default_factory=list, description="需多学科协作的事项"
    )


# ---------------------------------------------------------------------------
# Reviewer Agent structured output
# ---------------------------------------------------------------------------

class SafetyAlert(BaseModel):
    alert_type: str = Field(..., description="drug_contraindication / drug_interaction / conflict")
    detail: str
    severity: str = Field(..., description="严重 / 中等 / 轻微")
    suggestion: str = Field("", description="处理建议")


class DepartmentRecommendation(BaseModel):
    department: str
    content: str
    priority: str = Field(..., description="高 / 中 / 低")


class MDTReport(BaseModel):
    consultation_summary: str
    risk_assessment: dict[str, str] = Field(
        ..., description="{'maternal': '中', 'fetal': '低'}"
    )
    recommendations: list[DepartmentRecommendation]
    safety_alerts: list[SafetyAlert] = Field(default_factory=list)
    follow_up_plan: str
    disclaimer: str = Field(
        default="本报告由 AI 辅助生成，仅供临床参考，不替代医生诊断。"
    )


# ---------------------------------------------------------------------------
# API request / response
# ---------------------------------------------------------------------------

class ConsultRequest(BaseModel):
    complaint: str = Field(
        ...,
        min_length=2,
        description="患者主诉",
        examples=["怀孕 24 周，糖耐量异常，伴随轻微水肿"],
    )


class TraceEvent(BaseModel):
    node: str
    timestamp: str
    data: dict


class ConsultResponse(BaseModel):
    consultation_id: str
    status: str = "completed"
    report: MDTReport | None = None
    trace: list[TraceEvent] = Field(default_factory=list, description="智能体推理过程")
    errors: list[str] = Field(default_factory=list)
