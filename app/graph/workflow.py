from __future__ import annotations

from app.agents.chat import ChatAgent
from app.agents.commerce import CommerceAgent
from app.agents.health import HealthAgent
from app.agents.master import MasterAgent


class HerCareWorkflow:
    """Small graph-compatible router with explicit agent boundaries."""

    def __init__(self) -> None:
        self.master = MasterAgent()
        self.chat = ChatAgent()
        self.health = HealthAgent()
        self.commerce = CommerceAgent()

    def route(self, message: str) -> str:
        return self.master.route(message)

    def fallback(self, route: str, message: str, context: list[dict]) -> str:
        if route == "health":
            return self.health.fallback(message, context)
        if route == "commerce":
            return self.commerce.fallback(message)
        return self.chat.fallback(message)
