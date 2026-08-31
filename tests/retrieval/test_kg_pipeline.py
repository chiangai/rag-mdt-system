from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.kg.audit import build_manifest, resolve_source_dir
from scripts.kg.import_neo4j import AuditWriter, ImportStats, import_dataset


FIXTURE = Path(__file__).parent / "fixtures" / "kg_small.json"


class RecordingSink:
    def __init__(self) -> None:
        self.nodes: list[dict] = []
        self.edges: list[dict] = []

    def write_nodes(self, dataset_id: str, records: list[dict]) -> None:
        assert dataset_id == "fixture-v1"
        self.nodes.extend(records)

    def write_edges(self, dataset_id: str, records: list[dict]) -> None:
        assert dataset_id == "fixture-v1"
        self.edges.extend(records)


def test_source_directory_must_be_absolute(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="absolute"):
        resolve_source_dir("relative/assets")
    assert resolve_source_dir(str(tmp_path)) == tmp_path.resolve()


def test_manifest_hashes_assets_without_modifying_them(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    asset = source / "graph.json"
    asset.write_bytes(b'{"nodes": []}\n')
    before = asset.stat().st_mtime_ns

    manifest = build_manifest(source, [asset])

    assert manifest["files"] == [
        {
            "relative_path": "graph.json",
            "size_bytes": 14,
            "sha256": hashlib.sha256(b'{"nodes": []}\n').hexdigest(),
        }
    ]
    assert asset.stat().st_mtime_ns == before


def test_import_rejects_duplicate_nodes_and_dangling_edges(tmp_path: Path) -> None:
    sink = RecordingSink()
    audit_path = tmp_path / "rejects.jsonl"

    with AuditWriter(audit_path) as audit:
        stats = import_dataset(FIXTURE, "fixture-v1", sink, audit, batch_size=2)

    assert stats == ImportStats(nodes_written=3, edges_written=2, duplicates_rejected=1, dangling_rejected=1)
    assert [node["id"] for node in sink.nodes] == ["n1", "n2", "n3"]
    assert {(edge["source"], edge["target"]) for edge in sink.edges} == {("n1", "n2"), ("n2", "n3")}
    rejects = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert [item["reason"] for item in rejects] == ["duplicate_node_id", "dangling_edge"]
    assert rejects[0]["dataset_id"] == "fixture-v1"


def test_importer_never_issues_a_delete_query() -> None:
    from scripts.kg.import_neo4j import EDGE_UPSERT_QUERY, NODE_UPSERT_QUERY

    combined = f"{NODE_UPSERT_QUERY}\n{EDGE_UPSERT_QUERY}".upper()
    assert "DELETE" not in combined
    assert "DETACH" not in combined
    assert "DATASET_ID" in combined
