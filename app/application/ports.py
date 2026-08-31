from __future__ import annotations

from typing import Protocol


class Retriever(Protocol):
    def search(self, query: str, *, allowed_collections: tuple[str, ...], limit: int) -> list[dict]: ...


class ModelProvider(Protocol):
    def generate(self, *, route: str, message: str, context: list[dict], memory: list[dict]) -> str: ...
