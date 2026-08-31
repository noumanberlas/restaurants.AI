from __future__ import annotations

"""Order tools — persisted via SQLAlchemy (default) or Azure Table Storage
(when MODEL_PROVIDER=foundry and TABLE_STORAGE_CONNECTION_STRING is set)."""

from datetime import datetime
from typing import Annotated, Optional
from uuid import uuid4

from pydantic import Field

from src.config import get_settings
from src.database import OrderDB, OrderItemDB, OrderTableRepository, get_session, get_table_storage
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


def _repo() -> Optional[OrderTableRepository]:
    settings = get_settings()
    if settings.use_table_storage():
        return OrderTableRepository(get_table_storage(settings.table_storage_connection_string))
    return None


def create_order(
    table_number: Annotated[int, Field(description="Table number placing the order")],
    items: Annotated[
        list[dict],
        Field(description="List of {menu_item_id, quantity, notes} objects"),
    ],
) -> dict:
    """Place a new order for a table."""
    order_id = str(uuid4())
    repo = _repo()
    if repo:
        return repo.create(
            order_id,
            table_number=table_number,
            status="pending",
            created_at=datetime.utcnow().isoformat(),
            items=[
                {
                    "id": str(uuid4()),
                    "menu_item_id": i["menu_item_id"],
                    "quantity": i.get("quantity", 1),
                    "notes": i.get("notes", ""),
                }
                for i in items
            ],
        )
    order = OrderDB(id=order_id, table_number=table_number, status="pending", total=0.0)
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
    repo = _repo()
    if repo:
        row = repo.get(order_id)
        if not row:
            raise KeyError(order_id)
        return row
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
    repo = _repo()
    if repo:
        return repo.list(status=status)
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
    repo = _repo()
    if repo:
        return repo.set_status(order_id, status)
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
    repo = _repo()
    if repo:
        return repo.set_status(order_id, OrderStatus.CANCELLED.value)
    with get_session() as session:
        row = session.get(OrderDB, order_id)
        if not row:
            raise KeyError(order_id)
        row.status = OrderStatus.CANCELLED.value
        return _row_to_dict(row)
