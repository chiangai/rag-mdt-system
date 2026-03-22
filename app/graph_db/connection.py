from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession

from config.settings import settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Manages the async Neo4j driver lifecycle and provides query helpers."""

    _driver: AsyncDriver | None = None

    @classmethod
    def get_driver(cls) -> AsyncDriver:
        if cls._driver is None:
            cfg = settings.neo4j
            cls._driver = AsyncGraphDatabase.driver(
                cfg.uri,
                auth=(cfg.user, cfg.password),
            )
            logger.info("Neo4j async driver created for %s", cfg.uri)
        return cls._driver

    @classmethod
    async def close(cls) -> None:
        if cls._driver is not None:
            await cls._driver.close()
            cls._driver = None
            logger.info("Neo4j driver closed")

    @classmethod
    @asynccontextmanager
    async def session(cls, database: str = "neo4j") -> AsyncGenerator[AsyncSession, None]:
        driver = cls.get_driver()
        session = driver.session(database=database)
        try:
            yield session
        finally:
            await session.close()

    @classmethod
    async def execute_read(
        cls,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str = "neo4j",
    ) -> list[dict[str, Any]]:
        """Execute a read-only Cypher query using a managed read transaction."""

        async def _read_tx(tx, q, p):
            result = await tx.run(q, p)
            return [record.data() async for record in result]

        async with cls.session(database=database) as session:
            records = await session.execute_read(_read_tx, query, parameters or {})
            logger.debug(
                "Cypher query returned %d records: %s",
                len(records),
                query[:120],
            )
            return records

    @classmethod
    async def verify_connectivity(cls) -> bool:
        try:
            driver = cls.get_driver()
            await driver.verify_connectivity()
            logger.info("Neo4j connectivity verified")
            return True
        except Exception as e:
            logger.error("Neo4j connectivity check failed: %s", e)
            return False
