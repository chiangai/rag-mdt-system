from __future__ import annotations

from collections.abc import Callable, Sequence

from app.retrieval.models import GraphCandidate, GraphPath, VectorCandidate


EXACT_ALIAS_QUERY = """
MATCH (node:KGEntity {dataset_id: $dataset_version})
WHERE toLower(node.name) = toLower($query)
   OR any(alias IN coalesce(node.aliases, []) WHERE toLower(alias) = toLower($query))
RETURN node.kg_node_id AS node_id, node.name AS name,
       coalesce(node.aliases, []) AS aliases,
       coalesce(node.source_names, []) AS source_names,
       CASE WHEN toLower(node.name) = toLower($query) THEN 'exact' ELSE 'alias' END AS match_kind
ORDER BY CASE match_kind WHEN 'exact' THEN 0 ELSE 1 END, node_id
LIMIT $limit
"""

EXPAND_ONE_HOP_QUERY = """
MATCH (seed:KGEntity {dataset_id: $dataset_version})
WHERE seed.kg_node_id IN $node_ids
MATCH path=(seed)-[relationships:KG_RELATION*0..1]-(node:KGEntity {dataset_id: $dataset_version})
RETURN node.kg_node_id AS node_id, node.name AS name,
       [item IN nodes(path) | item.kg_node_id] AS node_ids,
       [item IN relationships(path) | item.relation_type] AS relations,
       coalesce(node.source_names, []) AS source_names
ORDER BY length(path), node_id
LIMIT $limit
"""

EXPAND_TWO_HOP_QUERY = EXPAND_ONE_HOP_QUERY.replace("*0..1", "*0..2")


class Neo4jGraphAdapter:
    def __init__(self, driver: object, database: str | None = None):
        self._driver = driver
        self._database = database

    def _records(self, query: str, **parameters: object) -> list[dict]:
        with self._driver.session(database=self._database) as session:  # type: ignore[attr-defined]
            return [dict(record) for record in session.run(query, **parameters)]

    def exact_or_alias(self, query: str, dataset_version: str, limit: int) -> list[GraphCandidate]:
        return [
            GraphCandidate(
                row["node_id"],
                row["name"],
                tuple(row["aliases"]),
                tuple(row["source_names"]),
                row["match_kind"],
            )
            for row in self._records(
                EXACT_ALIAS_QUERY, query=query, dataset_version=dataset_version, limit=limit
            )
        ]

    def expand(
        self, node_ids: list[str], dataset_version: str, max_hops: int, limit: int
    ) -> list[GraphPath]:
        if max_hops not in (1, 2):
            raise ValueError("max_hops must be 1 or 2")
        query = EXPAND_ONE_HOP_QUERY if max_hops == 1 else EXPAND_TWO_HOP_QUERY
        return [
            GraphPath(
                row["node_id"],
                row["name"],
                tuple(row["node_ids"]),
                tuple(row["relations"]),
                tuple(row["source_names"]),
            )
            for row in self._records(
                query,
                node_ids=node_ids,
                dataset_version=dataset_version,
                limit=limit,
            )
        ]


class CallableVectorAdapter:
    """Small boundary adapter for any embedding/vector backend."""

    def __init__(self, search_fn: Callable[[str, str, int], Sequence[tuple[str, float]]]):
        self._search_fn = search_fn

    def search(self, query: str, dataset_version: str, limit: int) -> list[VectorCandidate]:
        return [VectorCandidate(node_id, score) for node_id, score in self._search_fn(query, dataset_version, limit)]
