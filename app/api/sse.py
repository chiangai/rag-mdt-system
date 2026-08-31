from __future__ import annotations

import json

from app.runtime.harness import RunResult


ALLOWED_SSE_EVENTS = frozenset({"status", "message_delta", "citation", "safety_alert", "done", "error"})


def encode_event(event: str, data: dict) -> str:
    if event not in ALLOWED_SSE_EVENTS:
        raise ValueError(f"event is not allowed: {event}")
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def result_events(result: RunResult):
    yield encode_event("status", {"route": result.route, "degraded": result.degraded, "replayed": result.replayed})
    if result.safety_alert:
        yield encode_event("safety_alert", result.safety_alert)
    yield encode_event("message_delta", {"text": result.text})
    for citation in result.citations:
        yield encode_event("citation", citation)
    yield encode_event("done", {"conversation_id": result.conversation_id, "trace_id": result.trace_id})
