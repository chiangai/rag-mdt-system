"""FastAPI routes for the MDT consultation system."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agents.workflow import get_mdt_app
from app.agents.utils import sanitize_complaint
from app.models.schemas import ConsultRequest, ConsultResponse, MDTReport, TraceEvent
from app.models.state import MDTState
from app.storage.sqlite_store import SQLiteConsultationStore
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

CONSULTATION_TIMEOUT = 300.0
STREAM_TIMEOUT = 400.0

consultation_store = SQLiteConsultationStore(
    settings.app.consult_db_path,
    max_records=settings.app.consult_store_max_records,
)


async def init_consultation_store() -> None:
    await consultation_store.init()


def _build_initial_state(consultation_id: str, complaint: str) -> MDTState:
    """Construct the initial LangGraph state dict (single source of truth)."""
    return {
        "consultation_id": consultation_id,
        "patient_complaint": complaint,
        "medical_entities": {},
        "required_departments": [],
        "urgency": "",
        "graph_knowledge": {},
        "expert_opinions": {},
        "drug_contraindications": [],
        "safety_alerts": [],
        "final_report": {},
        "errors": [],
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event_payload(node_name: str, node_output: dict[str, Any]) -> dict[str, Any]:
    return {
        "node": node_name,
        "timestamp": _now_iso(),
        "data": _safe_serialize(node_output),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/consult", response_model=ConsultResponse)
async def create_consultation(req: ConsultRequest) -> ConsultResponse:
    """Submit a patient complaint and run the full MDT consultation pipeline."""

    consultation_id = str(uuid.uuid4())[:12]
    complaint = sanitize_complaint(req.complaint)
    logger.info("New consultation %s: %s", consultation_id, complaint[:60])

    initial_state = _build_initial_state(consultation_id, complaint)

    accumulated_state: dict[str, Any] = {}
    trace_events: list[dict[str, Any]] = []

    async def _collect_updates() -> None:
        mdt_app = get_mdt_app()
        async for event in mdt_app.astream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                _merge_state_update(accumulated_state, node_output)
                trace_events.append(_event_payload(node_name, node_output))

    try:
        await asyncio.wait_for(_collect_updates(), timeout=CONSULTATION_TIMEOUT)
    except asyncio.TimeoutError:
        logger.error("Consultation %s timed out after %ss", consultation_id, CONSULTATION_TIMEOUT)
        raise HTTPException(status_code=504, detail="会诊超时，请稍后重试")
    except Exception as e:
        logger.error("Consultation %s failed: %s", consultation_id, e)
        raise HTTPException(status_code=500, detail="会诊流程执行失败，请稍后重试")

    report_data = accumulated_state.get("final_report", {})
    report = MDTReport(**report_data) if report_data else None

    result = ConsultResponse(
        consultation_id=consultation_id,
        status="completed",
        report=report,
        trace=[TraceEvent(**item) for item in trace_events],
        errors=accumulated_state.get("errors", []),
    )

    await consultation_store.save(
        consultation_id=consultation_id,
        request_data=req.model_dump(),
        state_data=_serialize_state(accumulated_state),
        response_data=result.model_dump(),
    )

    return result


@router.post("/consult/stream")
async def create_consultation_stream(req: ConsultRequest) -> StreamingResponse:
    """Submit a consultation and stream back agent progress via SSE."""

    consultation_id = str(uuid.uuid4())[:12]
    complaint = sanitize_complaint(req.complaint)

    initial_state = _build_initial_state(consultation_id, complaint)

    async def event_generator():
        accumulated_state: dict[str, Any] = {}
        trace_events: list[dict[str, Any]] = []
        deadline = time.monotonic() + STREAM_TIMEOUT
        try:
            mdt_app = get_mdt_app()
            async for event in mdt_app.astream(
                initial_state, stream_mode="updates"
            ):
                if time.monotonic() > deadline:
                    logger.error("Stream %s timed out after %ss", consultation_id, STREAM_TIMEOUT)
                    yield f"data: {json.dumps({'node': 'error', 'data': {'error': '会诊超时，请稍后重试'}}, ensure_ascii=False)}\n\n"
                    return

                for node_name, node_output in event.items():
                    _merge_state_update(accumulated_state, node_output)
                    payload = _event_payload(node_name, node_output)
                    trace_events.append(payload)
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            response_data = _safe_serialize({
                "consultation_id": consultation_id,
                "status": "completed",
                "report": accumulated_state.get("final_report", {}),
                "trace": trace_events,
                "errors": accumulated_state.get("errors", []),
            })
            await consultation_store.save(
                consultation_id=consultation_id,
                request_data=req.model_dump(),
                state_data=_safe_serialize(accumulated_state),
                response_data=response_data,
            )

            yield f"data: {json.dumps({'node': 'done', 'data': {'consultation_id': consultation_id}}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error("Stream failed: %s", e)
            yield f"data: {json.dumps({'node': 'error', 'data': {'error': '会诊流程异常，请稍后重试'}}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/consult/{consultation_id}")
async def get_consultation(consultation_id: str) -> dict:
    """Retrieve a previously completed consultation."""
    response = await consultation_store.get_response(consultation_id)
    if response is None:
        raise HTTPException(status_code=404, detail="会诊记录未找到")
    return response


@router.get("/consults")
async def list_consultations(limit: int = 50, offset: int = 0) -> dict:
    """List recent consultations (lightweight summaries, no full report)."""
    items = await consultation_store.list_recent(limit=limit, offset=offset)
    return {"items": items, "limit": limit, "offset": offset}


@router.get("/consult/{consultation_id}/trace")
async def get_consultation_trace(consultation_id: str) -> dict:
    """Retrieve the full internal state for debugging / transparency."""
    state = await consultation_store.get_state(consultation_id)
    if state is None:
        raise HTTPException(status_code=404, detail="会诊记录未找到")
    return state


def _merge_state_update(accumulated: dict[str, Any], delta: dict[str, Any]) -> None:
    """Merge a node output delta into accumulated state (mirrors LangGraph reducers)."""
    for key, value in delta.items():
        if key == "expert_opinions" and key in accumulated:
            accumulated[key] = {**accumulated[key], **value}
        elif key == "errors" and key in accumulated:
            accumulated[key] = accumulated[key] + value
        else:
            accumulated[key] = value


def _serialize_state(state: dict) -> dict:
    return _safe_serialize(state)


def _safe_serialize(obj: Any) -> Any:
    """Recursively convert an object into a JSON-safe form."""
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(i) for i in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return str(obj)
