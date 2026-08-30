from __future__ import annotations

from agent_framework import ClassSkill, SkillFrontmatter


class OrderSkill(ClassSkill):
    def __init__(self) -> None:
        super().__init__(
            frontmatter=SkillFrontmatter(
                name="order-skill",
                description="Business rules and status lifecycle for restaurant orders",
            )
        )

    @property
    def instructions(self) -> str:
        return """
You manage restaurant orders. Follow these rules strictly:

BUSINESS RULES
- An order must have at least one item and a valid table number (1–50).
- Only PENDING orders can be cancelled.
- Status transitions must follow the allowed sequence (see status-lifecycle resource).
- Never skip a status step unless explicitly instructed by a manager.
- Do not modify items after an order is CONFIRMED.

WORKFLOW
1. Verify the menu item IDs exist and are available before creating an order.
2. After creating, confirm the order ID and total back to the user.
3. When updating status, state clearly what the new status means operationally.
"""

    @ClassSkill.resource(name="schema", description="Order and order item field definitions")
    def schema(self) -> str:
        return """
OrderDB schema:
  id           : UUID string (auto-generated)
  table_number : integer, 1–50
  status       : enum (see status-lifecycle)
  created_at   : datetime (auto-set)
  total        : float (calculated)
  items        : list of OrderItemDB

OrderItemDB schema:
  id           : UUID string (auto-generated)
  menu_item_id : UUID string (must reference a valid, available menu item)
  quantity     : integer, >= 1
  notes        : string, optional (e.g. "no onions")
"""

    @ClassSkill.resource(name="status-lifecycle", description="Allowed order status transitions")
    def status_lifecycle(self) -> str:
        return """
Order status lifecycle (must follow this sequence):
  pending → confirmed → preparing → ready → delivered
  Any status → cancelled   (only allowed from pending)

Status meanings:
  pending    : order received, not yet acknowledged by kitchen
  confirmed  : kitchen has acknowledged
  preparing  : actively being cooked
  ready      : food is ready for pickup/serving
  delivered  : delivered to table
  cancelled  : order was cancelled (terminal state)
"""
