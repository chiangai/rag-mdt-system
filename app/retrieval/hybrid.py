from __future__ import annotations

import hashlib
from collections.abc import Sequence

from app.retrieval.models import EvidenceItem, GraphCandidate, GraphPath
from app.retrieval.ports import GraphAdapter, VectorAdapter


class HybridRetriever:
    """Controlled hybrid retrieval: lexical/vector seeds, then one or two graph hops."""

    def __init__(self, graph: GraphAdapter, vector: VectorAdapter):
        self._graph = graph
        self._vector = vector

    def retrieve(
        self,
        query: str,
        dataset_version: str,
        top_k: int = 8,
        max_hops: int = 1,
    ) -> list[EvidenceItem]:
        query = query.strip()
        if not query:
            return []
        if not dataset_version.strip():
            raise ValueError("dataset_version must not be empty")
        if top_k < 1:
            raise ValueError("top_k must be positive")
        if max_hops not in (1, 2):
            raise ValueError("max_hops must be 1 or 2")

        lexical = list(self._graph.exact_or_alias(query, dataset_version, top_k))
        vectors = list(self._vector.search(query, dataset_version, top_k))
        seed_scores: dict[str, float] = {}
        candidates: dict[str, GraphCandidate] = {}
        seed_order: list[str] = []

        for candidate in lexical:
            if candidate.node_id not in seed_scores:
                seed_order.append(candidate.node_id)
            lexical_score = 1.0 if candidate.match_kind == "exact" else 0.95
            seed_scores[candidate.node_id] = max(seed_scores.get(candidate.node_id, 0.0), lexical_score)
            candidates[candidate.node_id] = candidate
        for candidate in vectors:
            if candidate.node_id not in seed_scores:
                seed_order.append(candidate.node_id)
            vector_score = max(0.0, min(1.0, float(candidate.score))) * 0.85
            seed_scores[candidate.node_id] = max(seed_scores.get(candidate.node_id, 0.0), vector_score)

        if not seed_order:
            return []
        paths = list(self._graph.expand(seed_order, dataset_version, max_hops, top_k * 3))
        evidence_by_node: dict[str, EvidenceItem] = {}
        for path in paths:
            hops = max(0, len(path.node_ids) - 1)
            seed_id = path.node_ids[0] if path.node_ids else path.node_id
            score = max(0.0, seed_scores.get(seed_id, seed_scores.get(path.node_id, 0.0)) - 0.08 * hops)
            item = self._to_evidence(path, score, dataset_version)
            current = evidence_by_node.get(path.node_id)
            if current is None or item.retrieval_score > current.retrieval_score:
                evidence_by_node[path.node_id] = item

        for node_id in seed_order:
            if node_id in evidence_by_node:
                continue
            candidate = candidates.get(node_id)
            path = GraphPath(
                node_id=node_id,
                name=candidate.name if candidate else node_id,
                node_ids=(node_id,),
                relations=(),
                source_names=candidate.source_names if candidate else (),
            )
            evidence_by_node[node_id] = self._to_evidence(path, seed_scores[node_id], dataset_version)

        ranked = sorted(
            evidence_by_node.values(),
            key=lambda item: (-item.retrieval_score, item.kg_node_id),
        )
        return ranked[:top_k]

    @staticmethod
    def _to_evidence(path: GraphPath, score: float, dataset_version: str) -> EvidenceItem:
        graph_path = path.flattened() or [path.node_id]
        identity = "\0".join([dataset_version, path.node_id, *graph_path])
        evidence_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        return EvidenceItem(
            evidence_id=evidence_id,
            kg_node_id=path.node_id,
            source_name=path.source_names[0] if path.source_names else "unknown_source",
            graph_path=graph_path,
            retrieval_score=round(score, 6),
            dataset_version=dataset_version,
        )
