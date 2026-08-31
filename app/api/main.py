from __future__ import annotations

from collections.abc import Iterator

from fastapi import FastAPI
from dotenv import load_dotenv

from app.api.chat_routes import build_chat_router
from app.api.fixed_routes import build_fixed_router
from app.application.ports import ModelProvider, Retriever
from app.providers import provider_from_env
from app.runtime.harness import Harness
from app.storage.database import Base, build_engine, build_session_factory
from app.storage.repository import HerCareRepository
from app.storage.seed import seed_demo

load_dotenv()


def create_app(*, database_url: str = "sqlite:///./hercare.db", retriever: Retriever | None = None, provider: ModelProvider | None = None) -> FastAPI:
    engine = build_engine(database_url)
    session_factory = build_session_factory(engine)
    Base.metadata.create_all(engine)
    with session_factory() as session:
        seed_demo(session)
    app = FastAPI(title="HerCare API", version="1.0.0")
    app.state.session_factory = session_factory
    app.state.harness = Harness(session_factory, retriever=retriever, provider=provider if provider is not None else provider_from_env())

    def repository() -> Iterator[HerCareRepository]:
        with session_factory() as session:
            yield HerCareRepository(session)

    app.include_router(build_fixed_router(repository))
    app.include_router(build_chat_router(app.state.harness, repository))
    return app


app = create_app()
