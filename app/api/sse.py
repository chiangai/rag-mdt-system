from __future__ import annotations

import json

from app.runtime.harness import RunResult


ALLOWED_SSE_EVENTS = frozenset({"message.start", "message.delta", "safety.escalation", "message.completed", "error"})


def encode_event(event: str, data: dict) -> str:
    if event not in ALLOWED_SSE_EVENTS:
        raise ValueError(f"event is not allowed: {event}")
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def result_events(result: RunResult):
    yield encode_event("message.start", {"conversation_id": result.conversation_id, "trace_id": result.trace_id, "route": result.route})
    if result.safety_alert:
        yield encode_event("safety.escalation", result.safety_alert)
    yield encode_event("message.delta", {"text": result.text})
    yield encode_event("message.completed", {"conversation_id": result.conversation_id, "trace_id": result.trace_id, "answer": result.text, "citations": result.citations, "status": "degraded" if result.degraded else "completed"})
