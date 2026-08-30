from __future__ import annotations

from agent_framework import ClassSkill, SkillFrontmatter


class InventorySkill(ClassSkill):
    def __init__(self) -> None:
        super().__init__(
            frontmatter=SkillFrontmatter(
                name="inventory-skill",
                description="Business rules and alert thresholds for restaurant inventory",
            )
        )

    @property
    def instructions(self) -> str:
        return """
You manage restaurant ingredient and supply inventory. Follow these rules strictly:

BUSINESS RULES
- Quantity must always be >= 0; never set it to a negative value.
- The reorder_threshold triggers a low-stock alert when quantity <= threshold.
- Always state the unit (kg, litre, unit, dozen, etc.) when reporting quantities.
- Alert staff proactively when any item is at or below its reorder threshold.
- Do not remove inventory items; set quantity to 0 if fully consumed.

WORKFLOW
1. Call get_low_stock_items at the start of every session to surface urgent alerts.
2. When adding a new item, ask for name, quantity, unit, and reorder threshold.
3. When updating stock, confirm the new quantity and unit before saving.
4. Group low-stock alerts by urgency: out-of-stock (0) first, then near-threshold.
"""

    @ClassSkill.resource(name="schema", description="Inventory item field definitions")
    def schema(self) -> str:
        return """
InventoryItemDB schema:
  id                 : UUID string (auto-generated)
  name               : string, required (e.g. "Chicken Breast", "Olive Oil")
  quantity           : float, >= 0
  unit               : string (e.g. kg, litre, unit, dozen, box)
  reorder_threshold  : float, default 0.0 — alert fires when quantity <= this value
"""

    @ClassSkill.resource(name="common-units", description="Standard units of measure used in this restaurant")
    def common_units(self) -> str:
        return """
Standard units used in this restaurant:
  kg       — solid ingredients (meat, vegetables, cheese)
  litre    — liquids (oil, wine, cream)
  unit     — individual items (eggs, lemons)
  dozen    — groups of 12 (eggs by the dozen)
  box      — packaged goods (pasta boxes, cereal)
  portion  — pre-portioned items (dessert slices, burger patties)
"""
