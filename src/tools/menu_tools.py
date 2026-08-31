from __future__ import annotations

"""Menu tools — persisted via SQLAlchemy (default) or Azure Table Storage
(when MODEL_PROVIDER=foundry and TABLE_STORAGE_CONNECTION_STRING is set)."""

from typing import Annotated, Optional
from uuid import uuid4

from pydantic import Field

from src.config import get_settings
from src.database import MenuItemDB, MenuTableRepository, get_session, get_table_storage
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


def _repo() -> Optional[MenuTableRepository]:
    settings = get_settings()
    if settings.use_table_storage():
        return MenuTableRepository(get_table_storage(settings.table_storage_connection_string))
    return None


def get_menu(
    category: Annotated[
        Optional[str],
        Field(description="Filter by category: starter, main, dessert, drink"),
    ] = None,
) -> list[dict]:
    """Retrieve all current menu items, optionally filtered by category."""
    repo = _repo()
    if repo:
        return repo.list(category=category)
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
    item_id = str(uuid4())
    repo = _repo()
    if repo:
        return repo.create(item_id, name=name, price=price, category=category, description=description)
    row = MenuItemDB(
        id=item_id,
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
    repo = _repo()
    if repo:
        return repo.set_availability(item_id, available)
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
    repo = _repo()
    if repo:
        repo.delete(item_id)
        return {"removed": item_id}
    with get_session() as session:
        row = session.get(MenuItemDB, item_id)
        if not row:
            raise KeyError(item_id)
        session.delete(row)
        return {"removed": item_id}
