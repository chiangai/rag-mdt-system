"""SQLite-backed consultation persistence."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SQLiteConsultationStore:
    def __init__(self, db_path: str, max_records: int = 5000):
        self._db_path = Path(db_path)
        self._max_records = max_records

    async def init(self) -> None:
        await asyncio.to_thread(self._init_sync)

    async def save(
        self,
        consultation_id: str,
        request_data: dict[str, Any],
        state_data: dict[str, Any],
        response_data: dict[str, Any],
    ) -> None:
        await asyncio.to_thread(
            self._save_sync,
            consultation_id,
            request_data,
            state_data,
            response_data,
        )

    async def get_response(self, consultation_id: str) -> dict[str, Any] | None:
        raw = await asyncio.to_thread(
            self._get_column_sync, consultation_id, "response_json"
        )
        return json.loads(raw) if raw else None

    async def get_state(self, consultation_id: str) -> dict[str, Any] | None:
        raw = await asyncio.to_thread(self._get_column_sync, consultation_id, "state_json")
        return json.loads(raw) if raw else None

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_sync(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consultations (
                    consultation_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    response_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consultations_created_at
                ON consultations(created_at DESC)
                """
            )
            conn.commit()

    def _save_sync(
        self,
        consultation_id: str,
        request_data: dict[str, Any],
        state_data: dict[str, Any],
        response_data: dict[str, Any],
    ) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO consultations (
                    consultation_id, created_at, request_json, state_json, response_json
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(consultation_id) DO UPDATE SET
                    created_at = excluded.created_at,
                    request_json = excluded.request_json,
                    state_json = excluded.state_json,
                    response_json = excluded.response_json
                """,
                (
                    consultation_id,
                    created_at,
                    json.dumps(request_data, ensure_ascii=False),
                    json.dumps(state_data, ensure_ascii=False),
                    json.dumps(response_data, ensure_ascii=False),
                ),
            )
            if self._max_records > 0:
                conn.execute(
                    """
                    DELETE FROM consultations
                    WHERE consultation_id NOT IN (
                        SELECT consultation_id
                        FROM consultations
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                    """,
                    (self._max_records,),
                )
            conn.commit()

    def _get_column_sync(self, consultation_id: str, column: str) -> str | None:
        if column not in {"response_json", "state_json"}:
            raise ValueError(f"Unsupported column: {column}")

        with self._connect() as conn:
            row = conn.execute(
                f"SELECT {column} FROM consultations WHERE consultation_id = ?",
                (consultation_id,),
            ).fetchone()
            return row[0] if row else None

    async def list_recent(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """Return lightweight consultation summaries (no full state/response JSON)."""
        return await asyncio.to_thread(self._list_recent_sync, limit, offset)

    def _list_recent_sync(self, limit: int, offset: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT consultation_id, created_at, request_json
                FROM consultations
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        results = []
        for consultation_id, created_at, request_json in rows:
            try:
                req = json.loads(request_json)
            except Exception:
                req = {}
            results.append({
                "consultation_id": consultation_id,
                "created_at": created_at,
                "complaint": req.get("complaint", ""),
            })
        return results
