from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol, Sequence


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    query: str
    expected_node_ids: tuple[str, ...]
    dataset_version: str


class Retriever(Protocol):
    def retrieve(self, query: str, dataset_version: str, top_k: int) -> Sequence[object]: ...


def load_cases(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    seen: set[str] = set()
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            payload = json.loads(line)
            case = EvalCase(payload["case_id"], payload["query"], tuple(payload["expected_node_ids"]), payload["dataset_version"])
            if case.case_id in seen:
                raise ValueError(f"duplicate case_id at line {line_number}: {case.case_id}")
            if not case.expected_node_ids:
                raise ValueError(f"empty expected_node_ids at line {line_number}")
            seen.add(case.case_id)
            cases.append(case)
    return cases


def evaluate(retriever: Retriever, cases: Iterable[EvalCase], top_k: int = 5) -> dict[str, int | float]:
    case_list = list(cases)
    if not case_list:
        raise ValueError("evaluation requires at least one case")
    hits = 0
    reciprocal_rank = 0.0
    for case in case_list:
        evidence = retriever.retrieve(case.query, case.dataset_version, top_k=top_k)
        ranked_ids = [str(getattr(item, "kg_node_id")) for item in evidence[:top_k]]
        ranks = [index for index, node_id in enumerate(ranked_ids, 1) if node_id in case.expected_node_ids]
        if ranks:
            hits += 1
            reciprocal_rank += 1.0 / ranks[0]
    count = len(case_list)
    return {"case_count": count, "hit_at_k": hits / count, "mrr": reciprocal_rank / count, "top_k": top_k}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a versioned retrieval evaluation set")
    parser.add_argument("cases", type=Path)
    args = parser.parse_args()
    cases = load_cases(args.cases)
    versions = sorted({case.dataset_version for case in cases})
    print(json.dumps({"case_count": len(cases), "dataset_versions": versions}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
