from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Neo4jSettings:
    uri: str = field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    user: str = field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    password: str = field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", ""))


@dataclass
class LLMSettings:
    """Each agent can independently configure its model."""
    api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", os.getenv("OPENAI_API_KEY", "")))
    base_url: str = field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")))

    router_model: str = field(default_factory=lambda: os.getenv("ROUTER_MODEL", "deepseek-chat"))
    graph_query_model: str = field(default_factory=lambda: os.getenv("GRAPH_QUERY_MODEL", "deepseek-chat"))
    obstetrician_model: str = field(default_factory=lambda: os.getenv("OBSTETRICIAN_MODEL", "deepseek-chat"))
    endocrinologist_model: str = field(default_factory=lambda: os.getenv("ENDOCRINOLOGIST_MODEL", "deepseek-chat"))
    reviewer_model: str = field(default_factory=lambda: os.getenv("REVIEWER_MODEL", "deepseek-chat"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    embedding_dimension: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "1536")))
    ark_api_key: str = field(default_factory=lambda: os.getenv("ARK_API_KEY", ""))
    ark_embedding_model: str = field(default_factory=lambda: os.getenv("ARK_EMBEDDING_MODEL", "ep-20260322180151-gggrl"))
    ark_ssl_verify: bool = field(default_factory=lambda: _env_bool("ARK_SSL_VERIFY", True))
    ark_ca_bundle: str = field(default_factory=lambda: os.getenv("ARK_CA_BUNDLE", "").strip())

    temperature: float = 0.1


@dataclass
class AppSettings:
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    consult_db_path: str = field(default_factory=lambda: os.getenv("CONSULT_DB_PATH", "data/consultations.db"))
    consult_store_max_records: int = field(default_factory=lambda: int(os.getenv("CONSULT_STORE_MAX_RECORDS", "5000")))


@dataclass
class Settings:
    neo4j: Neo4jSettings = field(default_factory=Neo4jSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    app: AppSettings = field(default_factory=AppSettings)


settings = Settings()
