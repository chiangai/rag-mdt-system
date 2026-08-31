from __future__ import annotations

import json
from pathlib import Path

from eval.run_retrieval_eval import evaluate, load_cases


class StaticRetriever:
    def retrieve(self, query: str, dataset_version: str, top_k: int):
        node_id = query.split(":", 1)[1]
        return [type("Evidence", (), {"kg_node_id": node_id})()]


def test_versioned_eval_fixture_has_exactly_fifty_cases() -> None:
    case_path = Path(__file__).parents[2] / "eval" / "retrieval" / "v1" / "cases.jsonl"
    cases = load_cases(case_path)
    assert len(cases) == 50
    assert {case.dataset_version for case in cases} == {"global-kg-v1"}
    assert len({case.case_id for case in cases}) == 50


def test_evaluate_reports_hit_rate_and_mrr(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"case_id": "a", "query": "id:n1", "expected_node_ids": ["n1"], "dataset_version": "v1"}),
                json.dumps({"case_id": "b", "query": "id:n2", "expected_node_ids": ["other"], "dataset_version": "v1"}),
            ]
        ),
        encoding="utf-8",
    )

    metrics = evaluate(StaticRetriever(), load_cases(path), top_k=5)

    assert metrics == {"case_count": 2, "hit_at_k": 0.5, "mrr": 0.5, "top_k": 5}
