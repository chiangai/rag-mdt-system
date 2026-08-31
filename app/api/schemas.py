from __future__ import annotations

from pydantic import BaseModel, Field


class CheckInRequest(BaseModel):
    metric_type: str | None = Field(default=None, max_length=50)
    value: str | None = Field(default=None, max_length=100)
    week: int | None = Field(default=None, ge=0, le=52)
    mood: str | None = Field(default=None, max_length=50)
    symptoms: str | None = Field(default=None, max_length=1000)
    unit: str | None = Field(default=None, max_length=30)
    note: str | None = Field(default=None, max_length=1000)


class CarePlanUpdate(BaseModel):
    completed: bool | None = None
    complete: bool | None = None

    @property
    def resolved_completed(self) -> bool:
        return self.completed if self.completed is not None else bool(self.complete)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=64)
    client_turn_id: str | None = Field(default=None, min_length=1, max_length=128)
