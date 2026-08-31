from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.api.sse import ALLOWED_SSE_EVENTS


def parse_sse(text: str) -> list[tuple[str, dict]]:
    blocks = [block for block in text.strip().split("\n\n") if block]
    events = []
    for block in blocks:
        lines = block.splitlines()
        event = next(line[7:] for line in lines if line.startswith("event: "))
        data = next(line[6:] for line in lines if line.startswith("data: "))
        events.append((event, json.loads(data)))
    return events


def test_chat_stream_emits_whitelisted_events_and_persists_trace(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat/stream",
        json={"message": "你好", "conversation_id": "conversation-api"},
        headers={"Idempotency-Key": "chat-api-1"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    assert {name for name, _ in events} <= ALLOWED_SSE_EVENTS
    assert events[-1][0] == "done"
    trace_id = events[-1][1]["trace_id"]
    conversation = client.get("/api/v1/conversations/conversation-api")
    trace = client.get(f"/api/v1/traces/{trace_id}")
    assert [item["role"] for item in conversation.json()["messages"]] == ["user", "assistant"]
    assert trace.json()["spans"]
