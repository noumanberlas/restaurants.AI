from __future__ import annotations

from agent_framework import ClassSkill, SkillFrontmatter


class MenuSkill(ClassSkill):
    def __init__(self) -> None:
        super().__init__(
            frontmatter=SkillFrontmatter(
                name="menu-skill",
                description="Business rules and schema for restaurant menu management",
            )
        )

    @property
    def instructions(self) -> str:
        return """
You manage the restaurant menu. Follow these rules strictly:

BUSINESS RULES
- Price must always be greater than 0.
- Mark items as unavailable (available=false) instead of deleting them when they run out.
- Category must be one of: starter, main, dessert, drink.
- Only delete an item if explicitly asked to remove it permanently, and confirm
  with the user in the same turn you ask (do not end the turn waiting for a reply).

NEVER ask for confirmation before adding or updating an item, even implicitly
("shall I proceed?", "confirm if you'd like me to continue"). If name, price, and
category are present, call add_menu_item in this same turn and report the result
as a completed fact ("Added X to the menu."), not a proposal.

WORKFLOW
1. Use get_menu to check what already exists before adding new items.
2. When adding: if name, price, and category are all present, call add_menu_item
   right now, in this turn, without asking the user anything first. Only ask a
   question if one of those three fields is actually missing from the request.
3. If an item with the same exact name already exists, do not add a duplicate —
   tell the user it exists and ask whether to update it instead.
4. When marking unavailable, tell the user the item will be hidden from customers
   (state it, don't ask permission first).
"""

    @ClassSkill.resource(name="schema", description="Menu item field definitions")
    def schema(self) -> str:
        return """
MenuItemDB schema:
  id          : UUID string (auto-generated)
  name        : string, required
  description : string, optional
  price       : float, must be > 0
  category    : enum — starter | main | dessert | drink
  available   : boolean, default true
"""

    @ClassSkill.resource(name="categories", description="Valid menu item categories")
    def categories(self) -> str:
        return "starter | main | dessert | drink"
