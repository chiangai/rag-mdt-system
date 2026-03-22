"""Unit tests for the Router Agent's structured output parsing."""

from app.models.schemas import RouterOutput, MedicalEntities


def test_router_output_schema():
    """Verify RouterOutput can be constructed with typical values."""
    output = RouterOutput(
        medical_entities=MedicalEntities(
            gestational_week=24,
            symptoms=["糖耐量异常", "轻微水肿"],
            conditions=["疑似妊娠期糖尿病"],
        ),
        required_departments=["obstetrics", "endocrinology"],
        urgency="moderate",
        reasoning="糖耐量异常提示GDM，水肿需排除子痫前期",
    )
    assert output.required_departments == ["obstetrics", "endocrinology"]
    assert output.urgency == "moderate"
    assert output.medical_entities.gestational_week == 24


def test_router_output_defaults():
    """Verify default values work correctly."""
    output = RouterOutput(
        medical_entities=MedicalEntities(),
        required_departments=["obstetrics"],
    )
    assert output.urgency == "moderate"
    assert output.medical_entities.symptoms == []
    assert output.medical_entities.gestational_week is None
