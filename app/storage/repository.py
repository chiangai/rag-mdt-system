from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.models import AgentRun, CarePlanItem, CheckIn, Conversation, Message, Product, Profile, TimelineEvent, TraceRecord
from app.storage.seed import utcnow


def iso(value: datetime | None) -> str | None:
    return value.isoformat() + "Z" if value else None


class HerCareRepository:
    def __init__(self, session: Session):
        self.session = session

    def profile(self) -> dict:
        row = self.session.scalar(select(Profile).limit(1))
        if row is None:
            raise LookupError("profile not found")
        return {"id": row.id, "name": row.name, "pregnancy_week": row.pregnancy_week, "due_date": row.due_date, "concerns": row.concerns}

    def timeline(self) -> list[dict]:
        rows = self.session.scalars(select(TimelineEvent).order_by(TimelineEvent.occurred_at.desc())).all()
        return [{"id": row.id, "kind": row.kind, "title": row.title, "detail": row.detail, "occurred_at": iso(row.occurred_at), "check_in_id": row.check_in_id} for row in rows]

    def care_plan(self) -> list[dict]:
        return [self._care_plan_dict(row) for row in self.session.scalars(select(CarePlanItem).order_by(CarePlanItem.id)).all()]

    def products(self) -> list[dict]:
        rows = self.session.scalars(select(Product).order_by(Product.id)).all()
        return [{"id": row.id, "name": row.name, "category": row.category, "summary": row.summary, "disclaimer": row.disclaimer} for row in rows]

    def create_check_in(self, *, idempotency_key: str, data: dict) -> tuple[dict, bool]:
        existing = self.session.scalar(select(CheckIn).where(CheckIn.idempotency_key == idempotency_key))
        if existing:
            return self._check_in_dict(existing), False
        created = CheckIn(id=f"checkin-{uuid4().hex}", idempotency_key=idempotency_key, metric_type=data["metric_type"], value=data["value"], unit=data.get("unit"), note=data.get("note"), created_at=utcnow())
        self.session.add(created)
        self.session.flush()
        self.session.add(TimelineEvent(id=f"timeline-{uuid4().hex}", kind="check_in", title=f"记录 {created.metric_type}", detail=f"{created.value}{(' ' + created.unit) if created.unit else ''}", occurred_at=created.created_at, check_in_id=created.id))
        self.session.commit()
        return self._check_in_dict(created), True

    def update_care_plan(self, item_id: str, completed: bool) -> dict:
        row = self.session.get(CarePlanItem, item_id)
        if row is None:
            raise LookupError(item_id)
        if row.completed != completed:
            row.completed = completed
            row.completed_at = utcnow() if completed else None
            self.session.commit()
        return self._care_plan_dict(row)

    def conversation(self, conversation_id: str) -> dict:
        row = self.session.get(Conversation, conversation_id)
        if row is None:
            raise LookupError(conversation_id)
        return {"id": row.id, "created_at": iso(row.created_at), "updated_at": iso(row.updated_at), "messages": [{"id": item.id, "role": item.role, "content": item.content, "created_at": iso(item.created_at)} for item in row.messages]}

    def memory(self, conversation_id: str, limit: int = 8) -> list[dict]:
        rows = self.session.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit)).all()
        return [{"role": row.role, "content": row.content} for row in reversed(rows)]

    def find_run(self, conversation_id: str, idempotency_key: str) -> AgentRun | None:
        return self.session.scalar(select(AgentRun).where(AgentRun.conversation_id == conversation_id, AgentRun.idempotency_key == idempotency_key))

    def persist_run(self, *, conversation_id: str, idempotency_key: str, trace_id: str, route: str, status: str, spans: list[dict], user_text: str, assistant_text: str, response_json: dict) -> None:
        now = utcnow()
        conversation = self.session.get(Conversation, conversation_id)
        if conversation is None:
            conversation = Conversation(id=conversation_id, created_at=now, updated_at=now)
            self.session.add(conversation)
        conversation.updated_at = now
        self.session.add_all([
            Message(id=f"message-{uuid4().hex}", conversation_id=conversation_id, role="user", content=user_text, created_at=now),
            Message(id=f"message-{uuid4().hex}", conversation_id=conversation_id, role="assistant", content=assistant_text, created_at=now),
            TraceRecord(id=trace_id, conversation_id=conversation_id, route=route, status=status, spans=spans, created_at=now),
            AgentRun(id=f"run-{uuid4().hex}", conversation_id=conversation_id, idempotency_key=idempotency_key, trace_id=trace_id, response_json=response_json, created_at=now),
        ])
        self.session.commit()

    def trace(self, trace_id: str) -> dict:
        row = self.session.get(TraceRecord, trace_id)
        if row is None:
            raise LookupError(trace_id)
        return {"id": row.id, "conversation_id": row.conversation_id, "route": row.route, "status": row.status, "spans": row.spans, "created_at": iso(row.created_at)}

    @staticmethod
    def _care_plan_dict(row: CarePlanItem) -> dict:
        return {"id": row.id, "title": row.title, "description": row.description, "cadence": row.cadence, "completed": row.completed, "completed_at": iso(row.completed_at)}

    @staticmethod
    def _check_in_dict(row: CheckIn) -> dict:
        return {"id": row.id, "metric_type": row.metric_type, "value": row.value, "unit": row.unit, "note": row.note, "created_at": iso(row.created_at)}
