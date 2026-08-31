from __future__ import annotations

from typing import Protocol, Sequence

from app.retrieval.models import GraphCandidate, GraphPath, VectorCandidate


class GraphAdapter(Protocol):
    def exact_or_alias(
        self, query: str, dataset_version: str, limit: int
    ) -> Sequence[GraphCandidate]: ...

    def expand(
        self,
        node_ids: list[str],
        dataset_version: str,
        max_hops: int,
        limit: int,
    ) -> Sequence[GraphPath]: ...


class VectorAdapter(Protocol):
    def search(self, query: str, dataset_version: str, limit: int) -> Sequence[VectorCandidate]: ...
