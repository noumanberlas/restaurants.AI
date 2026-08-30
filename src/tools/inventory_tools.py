from __future__ import annotations

"""Inventory tools — persisted via SQLAlchemy."""

from typing import Annotated
from uuid import uuid4

from pydantic import Field

from src.database import InventoryItemDB, get_session


def _row_to_dict(row: InventoryItemDB) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "quantity": row.quantity,
        "unit": row.unit,
        "reorder_threshold": row.reorder_threshold,
    }


def get_inventory() -> list[dict]:
    """Retrieve the full inventory list."""
    with get_session() as session:
        return [_row_to_dict(row) for row in session.query(InventoryItemDB).all()]


def get_low_stock_items() -> list[dict]:
    """Return items whose quantity is at or below their reorder threshold."""
    with get_session() as session:
        rows = session.query(InventoryItemDB).filter(
            InventoryItemDB.quantity <= InventoryItemDB.reorder_threshold
        ).all()
        return [_row_to_dict(row) for row in rows]


def add_stock(
    name: Annotated[str, Field(description="Name of the ingredient or supply")],
    quantity: Annotated[float, Field(description="Initial quantity")],
    unit: Annotated[str, Field(description="Unit of measure, e.g. kg, litre, unit")],
    reorder_threshold: Annotated[
        float, Field(description="Alert when quantity drops to this level")
    ] = 0.0,
) -> dict:
    """Add a new item to the inventory."""
    row = InventoryItemDB(
        id=str(uuid4()),
        name=name,
        quantity=quantity,
        unit=unit,
        reorder_threshold=reorder_threshold,
    )
    with get_session() as session:
        session.add(row)
    return _row_to_dict(row)


def update_stock(
    item_id: Annotated[str, Field(description="UUID of the inventory item")],
    quantity: Annotated[float, Field(description="New quantity on hand")],
) -> dict:
    """Update the quantity of an existing inventory item."""
    with get_session() as session:
        row = session.get(InventoryItemDB, item_id)
        if not row:
            raise KeyError(item_id)
        row.quantity = quantity
        return _row_to_dict(row)
