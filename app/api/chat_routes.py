from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import ChatRequest
from app.api.sse import result_events
from app.runtime.harness import Harness
from app.storage.repository import HerCareRepository


def build_chat_router(harness: Harness, repository: Callable[[], HerCareRepository]) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.post("/chat/stream")
    def chat_stream(payload: ChatRequest, idempotency_key: str | None = Header(default=None, min_length=1, max_length=128)) -> StreamingResponse:
        key = idempotency_key or payload.client_turn_id
        if not key:
            raise HTTPException(status_code=400, detail="client_turn_id or Idempotency-Key is required")
        result = harness.run(message=payload.message, conversation_id=payload.conversation_id, idempotency_key=key)
        return StreamingResponse(result_events(result), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @router.get("/conversations/{conversation_id}")
    def conversation(conversation_id: str, repo: HerCareRepository = Depends(repository)) -> dict:
        try:
            return repo.conversation(conversation_id)
        except LookupError as error:
            raise HTTPException(status_code=404, detail="conversation not found") from error

    @router.get("/traces/{trace_id}")
    def trace(trace_id: str, repo: HerCareRepository = Depends(repository)) -> dict:
        try:
            return repo.trace(trace_id)
        except LookupError as error:
            raise HTTPException(status_code=404, detail="trace not found") from error

    return router
