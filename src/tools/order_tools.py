from __future__ import annotations

"""Order tools — persisted via SQLAlchemy."""

from typing import Annotated, Optional
from uuid import uuid4

from pydantic import Field

from src.database import OrderDB, OrderItemDB, get_session
from src.models import OrderStatus


def _row_to_dict(row: OrderDB) -> dict:
    return {
        "id": row.id,
        "table_number": row.table_number,
        "status": row.status,
        "created_at": row.created_at.isoformat(),
        "total": row.total,
        "items": [
            {
                "id": i.id,
                "menu_item_id": i.menu_item_id,
                "quantity": i.quantity,
                "notes": i.notes,
            }
            for i in row.items
        ],
    }


def create_order(
    table_number: Annotated[int, Field(description="Table number placing the order")],
    items: Annotated[
        list[dict],
        Field(description="List of {menu_item_id, quantity, notes} objects"),
    ],
) -> dict:
    """Place a new order for a table."""
    order = OrderDB(id=str(uuid4()), table_number=table_number, status="pending", total=0.0)
    order.items = [
        OrderItemDB(
            id=str(uuid4()),
            order_id=order.id,
            menu_item_id=i["menu_item_id"],
            quantity=i.get("quantity", 1),
            notes=i.get("notes", ""),
        )
        for i in items
    ]
    with get_session() as session:
        session.add(order)
    return _row_to_dict(order)


def get_order(
    order_id: Annotated[str, Field(description="UUID of the order")],
) -> dict:
    """Retrieve an order by its ID."""
    with get_session() as session:
        row = session.get(OrderDB, order_id)
        if not row:
            raise KeyError(order_id)
        return _row_to_dict(row)


def list_orders(
    status: Annotated[
        Optional[str],
        Field(description="Filter by status: pending, confirmed, preparing, ready, delivered, cancelled"),
    ] = None,
) -> list[dict]:
    """List all orders, optionally filtered by status."""
    with get_session() as session:
        query = session.query(OrderDB)
        if status:
            query = query.filter(OrderDB.status == status)
        return [_row_to_dict(row) for row in query.all()]


def update_order_status(
    order_id: Annotated[str, Field(description="UUID of the order")],
    status: Annotated[
        str,
        Field(description="New status: confirmed, preparing, ready, delivered, cancelled"),
    ],
) -> dict:
    """Advance an order to the next status."""
    OrderStatus(status)  # validate
    with get_session() as session:
        row = session.get(OrderDB, order_id)
        if not row:
            raise KeyError(order_id)
        row.status = status
        return _row_to_dict(row)


def cancel_order(
    order_id: Annotated[str, Field(description="UUID of the order to cancel")],
) -> dict:
    """Cancel an existing order."""
    with get_session() as session:
        row = session.get(OrderDB, order_id)
        if not row:
            raise KeyError(order_id)
        row.status = OrderStatus.CANCELLED.value
        return _row_to_dict(row)
