"""Controlled hybrid retrieval interfaces."""
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.models import EvidenceItem, GraphCandidate, GraphPath, VectorCandidate
from app.retrieval.neo4j_adapter import CallableVectorAdapter, Neo4jGraphAdapter
from app.retrieval.ports import GraphAdapter, VectorAdapter

__all__ = [
    "CallableVectorAdapter",
    "EvidenceItem",
    "GraphAdapter",
    "GraphCandidate",
    "GraphPath",
    "HybridRetriever",
    "Neo4jGraphAdapter",
    "VectorAdapter",
    "VectorCandidate",
]
