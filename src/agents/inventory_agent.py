from __future__ import annotations

from agent_framework import SkillsProvider

from src.agents.base_agent import BaseRestaurantAgent
from src.skills.inventory_skill import InventorySkill
from src.tools.inventory_tools import (
    add_stock,
    get_inventory,
    get_low_stock_items,
    update_stock,
)


class InventoryAgent(BaseRestaurantAgent):
    """Tracks ingredient and supply inventory; raises low-stock alerts."""

    agent_name = "inventory_agent"

    def _system_prompt(self) -> str:
        return (
            "You are the Inventory Manager for a restaurant. "
            "You track stock levels for all ingredients and supplies. "
            "Load the inventory-skill for alert rules and units before acting."
        )

    def _tools(self) -> list:
        return [get_inventory, get_low_stock_items, add_stock, update_stock]

    def _middleware(self) -> list:
        return [SkillsProvider([InventorySkill()])]

