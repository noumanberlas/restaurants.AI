from __future__ import annotations

"""Reservation tools — persisted via SQLAlchemy."""

from datetime import datetime
from typing import Annotated, Optional
from uuid import uuid4

from pydantic import Field

from src.database import ReservationDB, get_session
from src.models import ReservationStatus


def _row_to_dict(row: ReservationDB) -> dict:
    return {
        "id": row.id,
        "customer_name": row.customer_name,
        "party_size": row.party_size,
        "date_time": row.date_time.isoformat(),
        "table_number": row.table_number,
        "status": row.status,
        "notes": row.notes,
    }


def create_reservation(
    customer_name: Annotated[str, Field(description="Customer's full name")],
    party_size: Annotated[int, Field(description="Number of guests")],
    date_time: Annotated[str, Field(description="ISO 8601 datetime, e.g. 2026-09-01T19:00:00")],
    notes: Annotated[str, Field(description="Special requests or notes")] = "",
) -> dict:
    """Create a new table reservation."""
    row = ReservationDB(
        id=str(uuid4()),
        customer_name=customer_name,
        party_size=party_size,
        date_time=datetime.fromisoformat(date_time),
        status=ReservationStatus.PENDING.value,
        notes=notes,
    )
    with get_session() as session:
        session.add(row)
    return _row_to_dict(row)


def get_reservation(
    reservation_id: Annotated[str, Field(description="UUID of the reservation")],
) -> dict:
    """Look up a reservation by ID."""
    with get_session() as session:
        row = session.get(ReservationDB, reservation_id)
        if not row:
            raise KeyError(reservation_id)
        return _row_to_dict(row)


def list_reservations(
    date: Annotated[
        Optional[str], Field(description="ISO 8601 date (YYYY-MM-DD) to filter by")
    ] = None,
    status: Annotated[
        Optional[str],
        Field(description="Filter by status: pending, confirmed, seated, completed, cancelled"),
    ] = None,
) -> list[dict]:
    """List reservations, optionally filtered by date or status."""
    with get_session() as session:
        query = session.query(ReservationDB)
        if date:
            from sqlalchemy import func
            query = query.filter(func.date(ReservationDB.date_time) == date)
        if status:
            query = query.filter(ReservationDB.status == status)
        return [_row_to_dict(row) for row in query.all()]


def update_reservation(
    reservation_id: Annotated[str, Field(description="UUID of the reservation")],
    party_size: Annotated[Optional[int], Field(description="New party size")] = None,
    date_time: Annotated[Optional[str], Field(description="New ISO 8601 datetime")] = None,
    notes: Annotated[Optional[str], Field(description="Updated notes")] = None,
    status: Annotated[Optional[str], Field(description="New status")] = None,
) -> dict:
    """Modify an existing reservation."""
    with get_session() as session:
        row = session.get(ReservationDB, reservation_id)
        if not row:
            raise KeyError(reservation_id)
        if party_size is not None:
            row.party_size = party_size
        if date_time is not None:
            row.date_time = datetime.fromisoformat(date_time)
        if notes is not None:
            row.notes = notes
        if status is not None:
            ReservationStatus(status)  # validate
            row.status = status
        return _row_to_dict(row)


def cancel_reservation(
    reservation_id: Annotated[str, Field(description="UUID of the reservation to cancel")],
) -> dict:
    """Cancel a reservation."""
    with get_session() as session:
        row = session.get(ReservationDB, reservation_id)
        if not row:
            raise KeyError(reservation_id)
        row.status = ReservationStatus.CANCELLED.value
        return _row_to_dict(row)
