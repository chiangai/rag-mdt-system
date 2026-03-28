import asyncio

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import routes
from app.storage.sqlite_store import SQLiteConsultationStore


class _FakeMDTApp:
    async def astream(self, initial_state, stream_mode="updates"):
        yield {"router": {"required_departments": ["obstetrics"], "medical_entities": {}}}
        yield {"reviewer": {"final_report": {
            "consultation_summary": "ok",
            "risk_assessment": {"maternal": "低", "fetal": "低"},
            "recommendations": [],
            "safety_alerts": [],
            "follow_up_plan": "复诊",
            "disclaimer": "本报告由 AI 辅助生成，仅供临床参考，不替代医生诊断。",
        }}}


def test_consult_returns_trace_and_persists(tmp_path, monkeypatch):
    store = SQLiteConsultationStore(str(tmp_path / "consults.db"), max_records=100)
    asyncio.run(store.init())
    monkeypatch.setattr(routes, "consultation_store", store)
    monkeypatch.setattr(routes, "get_mdt_app", lambda: _FakeMDTApp())

    app = FastAPI()
    app.include_router(routes.router)
    client = TestClient(app)

    resp = client.post("/api/v1/consult", json={"complaint": "怀孕24周，血糖异常"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["trace"]
    nodes = [item["node"] for item in body["trace"]]
    assert "router" in nodes
    assert "reviewer" in nodes

    cid = body["consultation_id"]
    hist = client.get(f"/api/v1/consult/{cid}")
    assert hist.status_code == 200
    assert hist.json()["trace"] == body["trace"]
