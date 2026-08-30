from __future__ import annotations

"""Menu tools — persisted via SQLAlchemy."""

from typing import Annotated, Optional
from uuid import uuid4

from pydantic import Field

from src.database import MenuItemDB, get_session
from src.models import MenuItemCategory


def _row_to_dict(row: MenuItemDB) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "price": row.price,
        "category": row.category,
        "available": row.available,
    }


def get_menu(
    category: Annotated[
        Optional[str],
        Field(description="Filter by category: starter, main, dessert, drink"),
    ] = None,
) -> list[dict]:
    """Retrieve all current menu items, optionally filtered by category."""
    with get_session() as session:
        query = session.query(MenuItemDB)
        if category:
            query = query.filter(MenuItemDB.category == category)
        return [_row_to_dict(row) for row in query.all()]


def add_menu_item(
    name: Annotated[str, Field(description="Name of the menu item")],
    price: Annotated[float, Field(description="Price in local currency")],
    category: Annotated[str, Field(description="Category: starter, main, dessert, drink")],
    description: Annotated[str, Field(description="Short description")] = "",
) -> dict:
    """Add a new item to the menu."""
    MenuItemCategory(category)  # validate
    row = MenuItemDB(
        id=str(uuid4()),
        name=name,
        description=description,
        price=price,
        category=category,
        available=True,
    )
    with get_session() as session:
        session.add(row)
    return _row_to_dict(row)


def update_menu_item_availability(
    item_id: Annotated[str, Field(description="UUID of the menu item")],
    available: Annotated[bool, Field(description="True to make available, False to hide")],
) -> dict:
    """Toggle a menu item's availability (e.g. mark as sold out)."""
    with get_session() as session:
        row = session.get(MenuItemDB, item_id)
        if not row:
            raise KeyError(item_id)
        row.available = available
        return _row_to_dict(row)


def remove_menu_item(
    item_id: Annotated[str, Field(description="UUID of the menu item to remove")],
) -> dict:
    """Permanently remove a menu item."""
    with get_session() as session:
        row = session.get(MenuItemDB, item_id)
        if not row:
            raise KeyError(item_id)
        session.delete(row)
        return {"removed": item_id}
