from __future__ import annotations

from app.runtime.harness import Harness
from app.runtime.fakes import FakeRetriever
from app.storage.database import Base, build_engine, build_session_factory


class CountingProvider:
    def __init__(self, *, fail: bool = False):
        self.calls = 0
        self.fail = fail

    def generate(self, *, route, message, context, memory):
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider unavailable")
        return f"{route}: {message}"


def make_harness(tmp_path, *, retriever=None, provider=None):
    engine = build_engine(f"sqlite:///{(tmp_path / 'harness.db').as_posix()}")
    Base.metadata.create_all(engine)
    return Harness(build_session_factory(engine), retriever=retriever, provider=provider)


def test_red_flag_short_circuits_retrieval_and_model(tmp_path) -> None:
    retriever = FakeRetriever()
    provider = CountingProvider()
    harness = make_harness(tmp_path, retriever=retriever, provider=provider)

    result = harness.run(message="我突然大量出血而且快晕倒了", idempotency_key="urgent-1")

    assert result.route == "safety"
    assert result.safety_alert is not None
    assert "立即" in result.text
    assert retriever.calls == []
    assert provider.calls == 0


def test_health_route_uses_controlled_retrieval_and_replays_idempotently(tmp_path) -> None:
    retriever = FakeRetriever(results=[{"title": "孕期头痛", "snippet": "持续头痛应联系产科医生", "source": "demo-guideline"}])
    provider = CountingProvider()
    harness = make_harness(tmp_path, retriever=retriever, provider=provider)

    first = harness.run(message="孕期头痛怎么办", conversation_id="conv-1", idempotency_key="same")
    second = harness.run(message="different text", conversation_id="conv-1", idempotency_key="same")

    assert first.route == "health"
    assert retriever.calls[0]["allowed_collections"] == ("hercare_medical",)
    assert second.text == first.text
    assert second.trace_id == first.trace_id
    assert second.replayed is True
    assert provider.calls == 1


def test_provider_failure_returns_safe_degraded_answer(tmp_path) -> None:
    harness = make_harness(tmp_path, retriever=FakeRetriever(), provider=CountingProvider(fail=True))

    result = harness.run(message="你好", idempotency_key="degrade-1")

    assert result.degraded is True
    assert "暂时" in result.text
    assert result.trace_id
