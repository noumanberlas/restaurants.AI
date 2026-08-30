from __future__ import annotations

import logging

from agent_framework import Agent, WorkflowEvent
from agent_framework.orchestrations import HandoffBuilder

from src.agents.base_agent import BaseRestaurantAgent, build_client
from src.agents.inventory_agent import InventoryAgent
from src.agents.menu_agent import MenuAgent
from src.agents.order_agent import OrderAgent
from src.agents.reservation_agent import ReservationAgent
from src.config import get_settings

logger = logging.getLogger(__name__)


# ── Subclass that ALSO overrides __init__ (constructor chaining)
# Because we build the workflow here, we can't call super().__init__() first
# — we need the specialists ready before building self._agent
class HostAgent(BaseRestaurantAgent):
    """Orchestrator built with HandoffBuilder — the correct AF orchestration primitive."""

    agent_name = "host_agent"

    def __init__(self) -> None:
        # Instantiate each specialist — C# equivalent: new MenuAgent()
        # self._ prefix = private field convention (no access modifier keyword)
        self._menu = MenuAgent()
        self._order = OrderAgent()
        self._reservation = ReservationAgent()
        self._inventory = InventoryAgent()

        settings = get_settings()
        model = settings.get_model_for_agent(self.agent_name)
        client = build_client(settings, model)

        # Triage/coordinator agent — no domain tools, only routes
        self._agent = Agent(
            client=client,
            name=self.agent_name,
            instructions=self._system_prompt(),
            require_per_service_call_history_persistence=True,
        )

        # Build the handoff workflow using the AF orchestration builder
        self._workflow = (
            HandoffBuilder(
                name="restaurant_management_handoff",
                participants=[
                    self._agent,
                    self._menu._agent,
                    self._order._agent,
                    self._reservation._agent,
                    self._inventory._agent,
                ],
            )
            .with_start_agent(self._agent)
            .add_handoff(self._agent, [
                self._menu._agent,
                self._order._agent,
                self._reservation._agent,
                self._inventory._agent,
            ])
            # Specialists hand back to the coordinator after completing their task
            .add_handoff(self._menu._agent, [self._agent])
            .add_handoff(self._order._agent, [self._agent])
            .add_handoff(self._reservation._agent, [self._agent])
            .add_handoff(self._inventory._agent, [self._agent])
            .build()
        )

        logger.info(
            "HostAgent + HandoffBuilder ready | provider=%s | model=%s",
            settings.model_provider.value,
            model,
        )

    def _system_prompt(self) -> str:
        return (
            "You are the central coordinator for a restaurant management system. "
            "Route each request to the correct specialist agent:\n"
            "  • menu_agent        — menu items, prices, and availability\n"
            "  • order_agent       — placing and tracking orders\n"
            "  • reservation_agent — table bookings and seating\n"
            "  • inventory_agent   — stock levels and low-stock alerts\n\n"
            "Hand off immediately; do not answer domain questions yourself. "
            "When the specialist finishes, they will hand control back to you."
        )

    def _tools(self) -> list:
        return []

    async def route(self, message: str) -> str:
        """Run the handoff workflow and return the final text output."""
        output_text: list[str] = []
        current_author: str | None = None

        def add_output(author: str, text: str) -> None:
            nonlocal current_author
            if not text:
                return
            if author != current_author:
                if output_text:
                    output_text.append("\n")
                output_text.append(f"[{author}]: ")
                current_author = author
            output_text.append(text)

        async for event in self._workflow.run(message, stream=True):
            event_type = event.type  # type: ignore[attr-defined]

            if event_type == "output":
                data = event.data  # type: ignore[attr-defined]
                # AgentResponse carries .messages; each has a .text attribute
                if hasattr(data, "messages"):
                    for msg in data.messages:
                        if getattr(msg, "text", None):
                            add_output(msg.author_name or msg.role, msg.text)
                elif hasattr(data, "contents"):
                    for content in data.contents:
                        if getattr(content, "text", None):
                            add_output(data.author_name or data.role, content.text)
                elif isinstance(data, str):
                    add_output("assistant", data)

            elif event_type == "handoff_sent":
                data = event.data  # type: ignore[attr-defined]
                logger.info("Handoff: %s → %s", data.source, data.target)

            elif event_type == "executor_invoked":
                data = event.data  # type: ignore[attr-defined]
                logger.debug("Executor invoked: %s", getattr(data, "executor_id", data))

            elif event_type == "executor_completed":
                data = event.data  # type: ignore[attr-defined]
                logger.debug("Executor completed: %s", getattr(data, "executor_id", data))

        return "".join(output_text)


