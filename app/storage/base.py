"""Storage interfaces for consultation records."""

from __future__ import annotations

from typing import Any, Protocol


class ConsultationStore(Protocol):
    async def init(self) -> None:
        """Initialize storage backend resources."""

    async def save(
        self,
        consultation_id: str,
        request_data: dict[str, Any],
        state_data: dict[str, Any],
        response_data: dict[str, Any],
    ) -> None:
        """Persist a full consultation snapshot."""

    async def get_response(self, consultation_id: str) -> dict[str, Any] | None:
        """Fetch API response payload for consultation id."""

    async def get_state(self, consultation_id: str) -> dict[str, Any] | None:
        """Fetch internal state payload for consultation id."""
