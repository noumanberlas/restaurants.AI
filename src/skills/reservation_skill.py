from __future__ import annotations

from agent_framework import ClassSkill, SkillFrontmatter


class ReservationSkill(ClassSkill):
    def __init__(self) -> None:
        super().__init__(
            frontmatter=SkillFrontmatter(
                name="reservation-skill",
                description="Business rules and status lifecycle for table reservations",
            )
        )

    @property
    def instructions(self) -> str:
        return """
You manage restaurant table reservations. Follow these rules strictly:

BUSINESS RULES
- Party size must be between 1 and 20.
- Reservations must be at least 1 hour in the future.
- Only PENDING or CONFIRMED reservations can be modified.
- Only PENDING or CONFIRMED reservations can be cancelled.
- Always ask for customer name, party size, and date/time if not provided.
- Confirm the reservation details before saving.

WORKFLOW
1. Check existing reservations for the requested date (list_reservations with date filter).
2. Confirm availability before booking.
3. After creating, read back the reservation ID and date/time to the customer.
4. When cancelling, confirm the customer name and reservation ID first.
"""

    @ClassSkill.resource(name="schema", description="Reservation field definitions")
    def schema(self) -> str:
        return """
ReservationDB schema:
  id            : UUID string (auto-generated)
  customer_name : string, required
  party_size    : integer, 1–20
  date_time     : ISO 8601 datetime, must be >= now + 1 hour
  table_number  : integer, nullable (assigned by host at seating)
  status        : enum (see status-lifecycle)
  notes         : string, optional (dietary requirements, special occasions)
"""

    @ClassSkill.resource(name="status-lifecycle", description="Allowed reservation status transitions")
    def status_lifecycle(self) -> str:
        return """
Reservation status lifecycle:
  pending → confirmed → seated → completed
  pending or confirmed → cancelled

Status meanings:
  pending    : booking received, not yet confirmed by staff
  confirmed  : staff has confirmed the booking
  seated     : guests have arrived and been seated
  completed  : dining finished, table cleared
  cancelled  : reservation was cancelled (terminal state)
"""
