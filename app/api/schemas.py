from __future__ import annotations

from pydantic import BaseModel, Field


class CheckInRequest(BaseModel):
    metric_type: str = Field(min_length=1, max_length=50)
    value: str = Field(min_length=1, max_length=100)
    unit: str | None = Field(default=None, max_length=30)
    note: str | None = Field(default=None, max_length=1000)


class CarePlanUpdate(BaseModel):
    completed: bool


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=64)
