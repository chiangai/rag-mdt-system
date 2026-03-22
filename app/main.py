"""FastAPI application entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.graph_db.connection import Neo4jConnection
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Starting MDT consultation service")
    if await Neo4jConnection.verify_connectivity():
        logger.info("Neo4j connection OK")
    else:
        logger.warning("Neo4j connection failed — graph queries will error")
    yield
    await Neo4jConnection.close()
    logger.info("MDT consultation service stopped")


app = FastAPI(
    title="妇产科 AI 虚拟 MDT 会诊系统",
    description="基于知识图谱 + 多智能体的妇产科多学科会诊 API",
    version="0.2.0",
    lifespan=lifespan,
)

_allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router)


@app.get("/health")
async def health_check():
    neo4j_ok = await Neo4jConnection.verify_connectivity()
    return {"status": "ok" if neo4j_ok else "degraded", "neo4j": neo4j_ok}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=True,
    )
