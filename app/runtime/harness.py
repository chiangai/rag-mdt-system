from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.application.ports import ModelProvider, Retriever
from app.graph.workflow import HerCareWorkflow
from app.memory.store import ConversationMemory
from app.skills.safety import detect_red_flags, urgent_guidance
from app.storage.repository import HerCareRepository


@dataclass(frozen=True)
class RunResult:
    conversation_id: str
    trace_id: str
    route: str
    text: str
    citations: list[dict]
    safety_alert: dict | None = None
    degraded: bool = False
    replayed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class Harness:
    MEDICAL_COLLECTIONS = ("hercare_medical",)

    def __init__(self, session_factory: sessionmaker[Session], *, retriever: Retriever | None = None, provider: ModelProvider | None = None):
        self.session_factory = session_factory
        self.retriever = retriever
        self.provider = provider
        self.workflow = HerCareWorkflow()
        self.memory = ConversationMemory()

    def run(self, *, message: str, idempotency_key: str, conversation_id: str | None = None) -> RunResult:
        conversation_id = conversation_id or f"conversation-{uuid4().hex}"
        with self.session_factory() as session:
            repo = HerCareRepository(session)
            existing = repo.find_run(conversation_id, idempotency_key)
            if existing:
                return replace(RunResult(**existing.response_json), replayed=True)

            trace_id = f"trace-{uuid4().hex}"
            spans: list[dict] = [{"name": "safety_gate", "status": "ok"}]
            flags = detect_red_flags(message)
            if flags:
                spans[0] = {"name": "safety_gate", "status": "blocked", "red_flags": flags}
                result = RunResult(conversation_id=conversation_id, trace_id=trace_id, route="safety", text=urgent_guidance(), citations=[], safety_alert={"severity": "urgent", "red_flags": flags})
                self._persist(repo, result, idempotency_key, message, spans, "blocked")
                return result

            route = self.workflow.route(message)
            spans.append({"name": "master_agent", "status": "ok", "route": route})
            context: list[dict] = []
            degraded = False
            if route == "health" and self.retriever:
                try:
                    context = self.retriever.search(message, allowed_collections=self.MEDICAL_COLLECTIONS, limit=4)
                    spans.append({"name": "retriever", "status": "ok", "count": len(context)})
                except Exception:
                    degraded = True
                    spans.append({"name": "retriever", "status": "degraded"})

            history = self.memory.load(repo, conversation_id)
            if self.provider:
                try:
                    text = self.provider.generate(route=route, message=message, context=context, memory=history)
                    spans.append({"name": f"{route}_agent", "status": "ok"})
                except Exception:
                    degraded = True
                    text = "服务暂时繁忙。" + self.workflow.fallback(route, message, context)
                    spans.append({"name": f"{route}_agent", "status": "degraded"})
            else:
                text = self.workflow.fallback(route, message, context)
                spans.append({"name": f"{route}_agent", "status": "local_fallback"})

            citations = [{"title": item.get("title", "资料"), "source": item.get("source", "controlled-retriever")} for item in context]
            result = RunResult(conversation_id=conversation_id, trace_id=trace_id, route=route, text=text, citations=citations, degraded=degraded)
            self._persist(repo, result, idempotency_key, message, spans, "degraded" if degraded else "completed")
            return result

    @staticmethod
    def _persist(repo: HerCareRepository, result: RunResult, idempotency_key: str, user_text: str, spans: list[dict], status: str) -> None:
        repo.persist_run(conversation_id=result.conversation_id, idempotency_key=idempotency_key, trace_id=result.trace_id, route=result.route, status=status, spans=spans, user_text=user_text, assistant_text=result.text, response_json=result.to_dict())
