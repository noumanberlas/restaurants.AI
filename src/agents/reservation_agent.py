from __future__ import annotations

from agent_framework import SkillsProvider

from src.agents.base_agent import BaseRestaurantAgent
from src.skills.reservation_skill import ReservationSkill
from src.tools.reservation_tools import (
    cancel_reservation,
    create_reservation,
    get_reservation,
    list_reservations,
    update_reservation,
)


class ReservationAgent(BaseRestaurantAgent):
    """Manages table reservations and seating."""

    agent_name = "reservation_agent"

    def _system_prompt(self) -> str:
        return (
            "You are the Reservations Manager for a restaurant. "
            "You handle booking, modifying, and cancelling table reservations. "
            "Load the reservation-skill for booking rules before acting."
        )

    def _tools(self) -> list:
        return [
            create_reservation,
            get_reservation,
            list_reservations,
            update_reservation,
            cancel_reservation,
        ]

    def _middleware(self) -> list:
        return [SkillsProvider([ReservationSkill()])]

