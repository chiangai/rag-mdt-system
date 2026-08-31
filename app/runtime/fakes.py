from __future__ import annotations


class FakeRetriever:
    def __init__(self, results: list[dict] | None = None, *, fail: bool = False):
        self.results = results or []
        self.fail = fail
        self.calls: list[dict] = []

    def search(self, query: str, *, allowed_collections: tuple[str, ...], limit: int) -> list[dict]:
        self.calls.append({"query": query, "allowed_collections": allowed_collections, "limit": limit})
        if self.fail:
            raise RuntimeError("retrieval unavailable")
        return self.results[:limit]
