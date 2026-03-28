"""Test bootstrap helpers."""

from __future__ import annotations

import sys
import types


def _install_neo4j_stub() -> None:
    neo4j = types.ModuleType("neo4j")

    class AsyncDriver:
        async def verify_connectivity(self):
            return None

        async def close(self):
            return None

        def session(self, database: str = "neo4j"):
            return AsyncSession()

    class AsyncSession:
        async def close(self):
            return None

        async def execute_read(self, fn, query, parameters):
            class _Tx:
                async def run(self, q, p):
                    class _Result:
                        def __aiter__(self):
                            return self

                        async def __anext__(self):
                            raise StopAsyncIteration

                    return _Result()

            return await fn(_Tx(), query, parameters)

    class AsyncGraphDatabase:
        @staticmethod
        def driver(uri: str, auth=None):
            return AsyncDriver()

    neo4j.AsyncGraphDatabase = AsyncGraphDatabase
    neo4j.AsyncDriver = AsyncDriver
    neo4j.AsyncSession = AsyncSession
    sys.modules["neo4j"] = neo4j


try:
    import neo4j  # noqa: F401
except ModuleNotFoundError:
    _install_neo4j_stub()
