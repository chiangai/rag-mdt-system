import asyncio
from pathlib import Path

from app.storage.sqlite_store import SQLiteConsultationStore


def test_sqlite_store_persists_across_instances(tmp_path: Path):
    db_path = tmp_path / "consultations.db"
    consultation_id = "abc123"

    async def _run():
        store1 = SQLiteConsultationStore(str(db_path), max_records=5000)
        await store1.init()
        await store1.save(
            consultation_id=consultation_id,
            request_data={"complaint": "test"},
            state_data={"final_report": {"consultation_summary": "ok"}},
            response_data={"consultation_id": consultation_id, "status": "completed"},
        )

        store2 = SQLiteConsultationStore(str(db_path), max_records=5000)
        await store2.init()
        response = await store2.get_response(consultation_id)
        state = await store2.get_state(consultation_id)

        assert response is not None
        assert response["consultation_id"] == consultation_id
        assert state is not None
        assert "final_report" in state

    asyncio.run(_run())


def test_sqlite_store_upsert_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "consultations.db"
    consultation_id = "same-id"

    async def _run():
        store = SQLiteConsultationStore(str(db_path), max_records=5000)
        await store.init()
        await store.save(
            consultation_id=consultation_id,
            request_data={"complaint": "first"},
            state_data={"step": 1},
            response_data={"consultation_id": consultation_id, "status": "completed"},
        )
        await store.save(
            consultation_id=consultation_id,
            request_data={"complaint": "second"},
            state_data={"step": 2},
            response_data={"consultation_id": consultation_id, "status": "completed"},
        )
        state = await store.get_state(consultation_id)
        assert state == {"step": 2}

    asyncio.run(_run())
