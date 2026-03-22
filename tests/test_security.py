"""Security-focused tests — input sanitization, Cypher safety, schema validation."""

import pytest

from app.agents.utils import sanitize_complaint, format_knowledge, MAX_COMPLAINT_LENGTH


# ---------------------------------------------------------------------------
# Input sanitization
# ---------------------------------------------------------------------------

def test_sanitize_strips_control_characters():
    dirty = "正常文字\x00\x01\x08隐藏字符"
    clean = sanitize_complaint(dirty)
    assert "\x00" not in clean
    assert "\x01" not in clean
    assert "正常文字" in clean
    assert "隐藏字符" in clean


def test_sanitize_truncates_long_input():
    long_input = "孕" * (MAX_COMPLAINT_LENGTH + 500)
    result = sanitize_complaint(long_input)
    assert len(result) <= MAX_COMPLAINT_LENGTH + 20  # +20 for truncation suffix
    assert result.endswith("…（输入过长已截断）")


def test_sanitize_preserves_normal_input():
    normal = "怀孕 24 周，糖耐量异常，伴随轻微水肿"
    assert sanitize_complaint(normal) == normal


def test_sanitize_strips_whitespace():
    padded = "  怀孕 24 周  "
    assert sanitize_complaint(padded) == "怀孕 24 周"


def test_sanitize_empty_returns_empty():
    assert sanitize_complaint("") == ""
    assert sanitize_complaint("   ") == ""


# ---------------------------------------------------------------------------
# format_knowledge
# ---------------------------------------------------------------------------

def test_format_knowledge_empty():
    assert format_knowledge({}) == "暂无相关知识图谱数据"


def test_format_knowledge_with_data():
    data = {"disease_info": [{"name": "GDM"}, {"name": "PE"}]}
    result = format_knowledge(data)
    assert "disease_info" in result
    assert "GDM" in result


def test_format_knowledge_max_items():
    data = {"items": [f"item_{i}" for i in range(10)]}
    result = format_knowledge(data, max_items_per_key=3)
    assert "item_0" in result
    assert "item_2" in result
    assert "item_3" not in result
