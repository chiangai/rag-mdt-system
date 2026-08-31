from __future__ import annotations

from app.retrieval import GraphCandidate, GraphPath, HybridRetriever, VectorCandidate


class FixtureGraph:
    def exact_or_alias(self, query: str, dataset_version: str, limit: int):
        assert dataset_version == "fixture-v1"
        if query == "先兆子痫":
            return [GraphCandidate("n1", "子痫前期", ("先兆子痫",), ("指南A",), "alias")]
        return []

    def expand(self, node_ids, dataset_version: str, max_hops: int, limit: int):
        assert max_hops in (1, 2)
        assert node_ids == ["n1", "n3"]
        return [
            GraphPath("n1", "子痫前期", ("n1", "n2"), ("HAS_SYMPTOM",), ("指南A",)),
            GraphPath("n3", "硫酸镁", ("n3",), (), ("指南B",)),
        ]


class FixtureVector:
    def search(self, query: str, dataset_version: str, limit: int):
        return [VectorCandidate("n3", 0.8)]


def test_hybrid_retrieval_merges_alias_vector_and_graph_evidence() -> None:
    retriever = HybridRetriever(FixtureGraph(), FixtureVector())

    evidence = retriever.retrieve("先兆子痫", "fixture-v1", top_k=5, max_hops=2)

    assert [item.kg_node_id for item in evidence] == ["n1", "n3"]
    assert evidence[0].source_name == "指南A"
    assert evidence[0].graph_path == ["n1", "HAS_SYMPTOM", "n2"]
    assert evidence[0].retrieval_score > evidence[1].retrieval_score
    assert all(item.dataset_version == "fixture-v1" for item in evidence)
    assert all(item.citation_quality == "source_name_only" for item in evidence)


def test_hybrid_retrieval_rejects_uncontrolled_hop_counts() -> None:
    retriever = HybridRetriever(FixtureGraph(), FixtureVector())
    for max_hops in (0, 3):
        try:
            retriever.retrieve("子痫", "fixture-v1", max_hops=max_hops)
        except ValueError as exc:
            assert "1 or 2" in str(exc)
        else:
            raise AssertionError("uncontrolled graph expansion was accepted")
