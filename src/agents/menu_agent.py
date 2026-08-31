from __future__ import annotations

from agent_framework import SkillsProvider

from src.agents.base_agent import BaseRestaurantAgent
from src.skills.menu_skill import MenuSkill
from src.tools.menu_tools import (
    add_menu_item,
    get_menu,
    remove_menu_item,
    update_menu_item_availability,
)


# ── Subclass (child) — C# equivalent: public class MenuAgent : BaseRestaurantAgent
class MenuAgent(BaseRestaurantAgent):
    """Manages the restaurant menu — items, prices, and availability."""

    # Class-level field — shared by all instances, like a static readonly in C#
    # BaseRestaurantAgent reads this in its __init__ to name the agent
    agent_name = "menu_agent"

    # ── Override — no 'override' keyword in Python; just define the same method name
    # C# equivalent: public override string GetSystemPrompt() { ... }
    def _system_prompt(self) -> str:
        # Parentheses around a multi-line string concatenate automatically (no + needed)
        return (
            "You are the Menu Manager for a restaurant. "
            "You help staff add, update, remove, and query menu items. "
            "Load the menu-skill for full business rules before acting.\n\n"
            "Do not ask the user to confirm an add or update when they already gave "
            "you the required fields (name, price, category for adds). Call the tool "
            "immediately in the same turn and report what you did as a completed fact. "
            "Only ask a question when a required field is actually missing, or when "
            "permanently deleting an item."
        )

    def _tools(self) -> list:
        # A list literal [ ] — C# equivalent: new List<Func<...>> { ... }
        # These are plain function references (no parentheses = passing the function itself,
        # not calling it). AF inspects their signatures to build the JSON tool schema.
        return [get_menu, add_menu_item, update_menu_item_availability, remove_menu_item]

    def _context_providers(self) -> list:
        # SkillsProvider wraps the skill and injects it into the agent's context
        return [
            SkillsProvider(
                [MenuSkill()],
                disable_load_skill_approval=True,
                disable_read_skill_resource_approval=True,
            )
        ]
