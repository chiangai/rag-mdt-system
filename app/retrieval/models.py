from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidenceItem:
    """Retrieval evidence matching contracts/domain.schema.json."""

    evidence_id: str
    kg_node_id: str
    source_name: str
    graph_path: list[str]
    retrieval_score: float
    dataset_version: str
    citation_quality: str = field(default="source_name_only", init=False)


@dataclass(frozen=True)
class GraphCandidate:
    node_id: str
    name: str
    aliases: tuple[str, ...] = ()
    source_names: tuple[str, ...] = ()
    match_kind: str = "exact"


@dataclass(frozen=True)
class VectorCandidate:
    node_id: str
    score: float


@dataclass(frozen=True)
class GraphPath:
    node_id: str
    name: str
    node_ids: tuple[str, ...]
    relations: tuple[str, ...]
    source_names: tuple[str, ...] = ()

    def flattened(self) -> list[str]:
        flattened: list[str] = []
        for index, node_id in enumerate(self.node_ids):
            flattened.append(node_id)
            if index < len(self.relations):
                flattened.append(self.relations[index])
        return flattened
