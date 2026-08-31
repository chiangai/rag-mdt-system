from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Protocol, TextIO

from scripts.kg.audit import SOURCE_ENV, resolve_source_dir


NODE_UPSERT_QUERY = """
UNWIND $records AS record
MERGE (node:KGEntity {dataset_id: $dataset_id, kg_node_id: record.id})
SET node += record.properties
"""

EDGE_UPSERT_QUERY = """
UNWIND $records AS record
MATCH (source:KGEntity {dataset_id: $dataset_id, kg_node_id: record.source})
MATCH (target:KGEntity {dataset_id: $dataset_id, kg_node_id: record.target})
MERGE (source)-[edge:KG_RELATION {dataset_id: $dataset_id, edge_key: record.edge_key}]->(target)
SET edge += record.properties
"""


class GraphSink(Protocol):
    def write_nodes(self, dataset_id: str, records: list[dict]) -> None: ...

    def write_edges(self, dataset_id: str, records: list[dict]) -> None: ...


@dataclass(frozen=True)
class ImportStats:
    nodes_written: int = 0
    edges_written: int = 0
    duplicates_rejected: int = 0
    dangling_rejected: int = 0


class AuditWriter:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._handle: TextIO | None = None

    def __enter__(self) -> "AuditWriter":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w", encoding="utf-8", newline="\n")
        return self

    def reject(self, reason: str, dataset_id: str, record: dict) -> None:
        if self._handle is None:
            raise RuntimeError("AuditWriter must be used as a context manager")
        payload = {"reason": reason, "dataset_id": dataset_id, "record": record}
        self._handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")

    def __exit__(self, *_: object) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


def _iter_json_array(path: Path, key: str, chunk_size: int = 64 * 1024) -> Iterator[dict]:
    """Incrementally decode one top-level array without materializing the document."""
    decoder = json.JSONDecoder()
    marker = json.dumps(key) + ":"
    with path.open("r", encoding="utf-8") as handle:
        buffer = ""
        found = False
        eof = False
        while not found:
            chunk = handle.read(chunk_size)
            if not chunk:
                raise ValueError(f"missing top-level array {key!r} in {path}")
            buffer += chunk
            compact = "".join(buffer.split())
            marker_index = compact.find(marker)
            if marker_index >= 0:
                # Whitespace removal loses offsets, so find the key in the original buffer.
                key_index = buffer.find(json.dumps(key))
                bracket_index = buffer.find("[", key_index + len(key) + 2)
                if bracket_index >= 0:
                    buffer = buffer[bracket_index + 1 :]
                    found = True
                    break
            buffer = buffer[-(len(marker) + 8) :]

        while True:
            buffer = buffer.lstrip()
            if buffer.startswith("]"):
                return
            if buffer.startswith(","):
                buffer = buffer[1:].lstrip()
            while True:
                try:
                    value, end = decoder.raw_decode(buffer)
                    break
                except json.JSONDecodeError:
                    chunk = handle.read(chunk_size)
                    if not chunk:
                        eof = True
                        break
                    buffer += chunk
            if eof:
                raise ValueError(f"truncated array {key!r} in {path}")
            if not isinstance(value, dict):
                raise ValueError(f"{key!r} items must be JSON objects")
            yield value
            buffer = buffer[end:]


def _batches(records: Iterable[dict], size: int) -> Iterator[list[dict]]:
    if size < 1:
        raise ValueError("batch_size must be positive")
    batch: list[dict] = []
    for record in records:
        batch.append(record)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def _node_record(node: dict) -> dict:
    node_id = str(node.get("id", "")).strip()
    properties = {key: value for key, value in node.items() if key != "id"}
    properties["name"] = str(node.get("name") or node_id)
    properties["aliases"] = list(node.get("aliases") or [])
    properties["source_names"] = list(node.get("sources") or [])
    return {"id": node_id, "properties": properties}


def _edge_record(edge: dict) -> dict:
    source = str(edge.get("source", "")).strip()
    target = str(edge.get("target", "")).strip()
    relation_type = str(edge.get("type", "RELATED_TO")).strip() or "RELATED_TO"
    edge_key = hashlib.sha256(f"{source}\0{relation_type}\0{target}".encode("utf-8")).hexdigest()
    properties = {key: value for key, value in edge.items() if key not in {"source", "target"}}
    properties["relation_type"] = relation_type
    properties["source_names"] = list(edge.get("docs") or [])
    return {"source": source, "target": target, "edge_key": edge_key, "properties": properties}


def import_dataset(
    path: Path,
    dataset_id: str,
    sink: GraphSink,
    audit: AuditWriter,
    batch_size: int = 500,
) -> ImportStats:
    if not dataset_id.strip():
        raise ValueError("dataset_id must not be empty")
    path = Path(path)
    node_ids: set[str] = set()
    counts = {"nodes": 0, "edges": 0, "duplicates": 0, "dangling": 0}

    def accepted_nodes() -> Iterator[dict]:
        for raw_node in _iter_json_array(path, "nodes"):
            record = _node_record(raw_node)
            if not record["id"] or record["id"] in node_ids:
                audit.reject("duplicate_node_id" if record["id"] else "missing_node_id", dataset_id, raw_node)
                counts["duplicates"] += 1
                continue
            node_ids.add(record["id"])
            counts["nodes"] += 1
            yield record

    for batch in _batches(accepted_nodes(), batch_size):
        sink.write_nodes(dataset_id, batch)

    def accepted_edges() -> Iterator[dict]:
        for raw_edge in _iter_json_array(path, "edges"):
            record = _edge_record(raw_edge)
            if record["source"] not in node_ids or record["target"] not in node_ids:
                audit.reject("dangling_edge", dataset_id, raw_edge)
                counts["dangling"] += 1
                continue
            counts["edges"] += 1
            yield record

    for batch in _batches(accepted_edges(), batch_size):
        sink.write_edges(dataset_id, batch)

    return ImportStats(counts["nodes"], counts["edges"], counts["duplicates"], counts["dangling"])


class Neo4jSink:
    def __init__(self, uri: str, username: str, password: str, database: str | None = None):
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise RuntimeError("install requirements/data.txt to use Neo4jSink") from exc
        self._driver = GraphDatabase.driver(uri, auth=(username, password))
        self._database = database

    def write_nodes(self, dataset_id: str, records: list[dict]) -> None:
        self._execute(NODE_UPSERT_QUERY, dataset_id, records)

    def write_edges(self, dataset_id: str, records: list[dict]) -> None:
        self._execute(EDGE_UPSERT_QUERY, dataset_id, records)

    def _execute(self, query: str, dataset_id: str, records: list[dict]) -> None:
        with self._driver.session(database=self._database) as session:
            session.run(query, dataset_id=dataset_id, records=records).consume()

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> "Neo4jSink":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Stream a namespaced HerCare KG dataset into Neo4j")
    parser.add_argument("--source-dir", help=f"absolute path; defaults to {SOURCE_ENV}")
    parser.add_argument("--input", default="global_kg.json", help="path relative to the source directory")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    source_dir = resolve_source_dir(args.source_dir)
    input_arg = Path(args.input)
    if input_arg.is_absolute():
        raise ValueError("--input must be relative to the absolute source directory")
    input_path = (source_dir / input_arg).resolve()
    try:
        input_path.relative_to(source_dir)
    except ValueError as exc:
        raise ValueError("--input escapes the source directory") from exc

    required = ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ValueError(f"missing Neo4j environment variables: {', '.join(missing)}")
    with Neo4jSink(
        os.environ["NEO4J_URI"],
        os.environ["NEO4J_USERNAME"],
        os.environ["NEO4J_PASSWORD"],
        os.getenv("NEO4J_DATABASE"),
    ) as sink, AuditWriter(args.audit_output) as audit:
        stats = import_dataset(input_path, args.dataset_id, sink, audit, args.batch_size)
    print(json.dumps(stats.__dict__, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
