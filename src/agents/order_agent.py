from __future__ import annotations

from agent_framework import SkillsProvider

from src.agents.base_agent import BaseRestaurantAgent
from src.skills.order_skill import OrderSkill
from src.tools.order_tools import (
    cancel_order,
    create_order,
    get_order,
    list_orders,
    update_order_status,
)


class OrderAgent(BaseRestaurantAgent):
    """Handles order creation, updates, and fulfilment tracking."""

    agent_name = "order_agent"

    def _system_prompt(self) -> str:
        return (
            "You are the Order Manager for a restaurant. "
            "You take new orders, update their status, and handle cancellations. "
            "Load the order-skill for status lifecycle rules before acting."
        )

    def _tools(self) -> list:
        return [create_order, get_order, list_orders, update_order_status, cancel_order]

    def _context_providers(self) -> list:
        return [
            SkillsProvider(
                [OrderSkill()],
                disable_load_skill_approval=True,
                disable_read_skill_resource_approval=True,
            )
        ]

