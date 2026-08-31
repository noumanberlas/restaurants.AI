from __future__ import annotations

"""Azure Table Storage persistence layer — used in place of SQLite when
MODEL_PROVIDER=foundry and TABLE_STORAGE_CONNECTION_STRING is configured.

Table names must be alphanumeric only (no underscores), per Azure Table
Storage naming rules, hence "menuitems" / "orderitems" / "inventoryitems".
"""

import json
from functools import lru_cache
from typing import Any, Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableClient, TableServiceClient

_PARTITION = "restaurant"


def _entity_to_dict(entity: dict[str, Any]) -> dict[str, Any]:
    result = dict(entity)
    result["id"] = result.pop("RowKey")
    result.pop("PartitionKey", None)
    result.pop("etag", None)
    result.pop("Timestamp", None)
    return result


class TableStorage:
    """Low-level CRUD wrapper shared by all entity repositories."""

    def __init__(self, connection_string: str) -> None:
        self._service = TableServiceClient.from_connection_string(connection_string)
        self._clients: dict[str, TableClient] = {}

    def client(self, table_name: str) -> TableClient:
        if table_name not in self._clients:
            self._clients[table_name] = self._service.create_table_if_not_exists(table_name)
        return self._clients[table_name]

    def list_all(self, table_name: str) -> list[dict[str, Any]]:
        return [_entity_to_dict(e) for e in self.client(table_name).list_entities()]

    def get(self, table_name: str, item_id: str) -> Optional[dict[str, Any]]:
        try:
            entity = self.client(table_name).get_entity(_PARTITION, item_id)
        except ResourceNotFoundError:
            return None
        return _entity_to_dict(entity)

    def create(self, table_name: str, item_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        entity = {"PartitionKey": _PARTITION, "RowKey": item_id, **fields}
        self.client(table_name).create_entity(entity)
        return _entity_to_dict(entity)

    def update(self, table_name: str, item_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        entity = {"PartitionKey": _PARTITION, "RowKey": item_id, **fields}
        self.client(table_name).update_entity(entity, mode="merge")
        result = self.get(table_name, item_id)
        if result is None:
            raise KeyError(item_id)
        return result

    def delete(self, table_name: str, item_id: str) -> None:
        self.client(table_name).delete_entity(_PARTITION, item_id)


@lru_cache(maxsize=1)
def _get_storage(connection_string: str) -> TableStorage:
    return TableStorage(connection_string)


def get_table_storage(connection_string: str) -> TableStorage:
    return _get_storage(connection_string)


# ── Menu ─────────────────────────────────────────────────────────────────────

class MenuTableRepository:
    TABLE = "menuitems"

    def __init__(self, storage: TableStorage) -> None:
        self._storage = storage

    def list(self, category: Optional[str] = None) -> list[dict]:
        rows = self._storage.list_all(self.TABLE)
        if category:
            rows = [r for r in rows if r.get("category") == category]
        return rows

    def create(self, item_id: str, name: str, price: float, category: str, description: str = "") -> dict:
        return self._storage.create(
            self.TABLE,
            item_id,
            {"name": name, "description": description, "price": price, "category": category, "available": True},
        )

    def set_availability(self, item_id: str, available: bool) -> dict:
        return self._storage.update(self.TABLE, item_id, {"available": available})

    def delete(self, item_id: str) -> None:
        self._storage.delete(self.TABLE, item_id)


# ── Orders (items serialized as JSON — Table Storage has no nested lists) ────

class OrderTableRepository:
    TABLE = "orders"

    def __init__(self, storage: TableStorage) -> None:
        self._storage = storage

    @staticmethod
    def _deserialize(row: dict) -> dict:
        row = dict(row)
        row["items"] = json.loads(row.pop("items_json", "[]"))
        return row

    def create(self, order_id: str, table_number: int, status: str, created_at: str, items: list[dict]) -> dict:
        row = self._storage.create(
            self.TABLE,
            order_id,
            {
                "table_number": table_number,
                "status": status,
                "created_at": created_at,
                "total": 0.0,
                "items_json": json.dumps(items),
            },
        )
        return self._deserialize(row)

    def get(self, order_id: str) -> Optional[dict]:
        row = self._storage.get(self.TABLE, order_id)
        return self._deserialize(row) if row else None

    def list(self, status: Optional[str] = None) -> list[dict]:
        rows = self._storage.list_all(self.TABLE)
        if status:
            rows = [r for r in rows if r.get("status") == status]
        return [self._deserialize(r) for r in rows]

    def set_status(self, order_id: str, status: str) -> dict:
        row = self._storage.update(self.TABLE, order_id, {"status": status})
        return self._deserialize(row)


# ── Reservations ─────────────────────────────────────────────────────────────

class ReservationTableRepository:
    TABLE = "reservations"

    def __init__(self, storage: TableStorage) -> None:
        self._storage = storage

    def create(
        self, reservation_id: str, customer_name: str, party_size: int, date_time: str,
        status: str, notes: str = "",
    ) -> dict:
        return self._storage.create(
            self.TABLE,
            reservation_id,
            {
                "customer_name": customer_name,
                "party_size": party_size,
                "date_time": date_time,
                "table_number": None,
                "status": status,
                "notes": notes,
            },
        )

    def get(self, reservation_id: str) -> Optional[dict]:
        return self._storage.get(self.TABLE, reservation_id)

    def list(self, date: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        rows = self._storage.list_all(self.TABLE)
        if date:
            rows = [r for r in rows if str(r.get("date_time", "")).startswith(date)]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        return rows

    def update(self, reservation_id: str, **fields: Any) -> dict:
        updates = {k: v for k, v in fields.items() if v is not None}
        return self._storage.update(self.TABLE, reservation_id, updates)


# ── Inventory ────────────────────────────────────────────────────────────────

class InventoryTableRepository:
    TABLE = "inventoryitems"

    def __init__(self, storage: TableStorage) -> None:
        self._storage = storage

    def list(self) -> list[dict]:
        return self._storage.list_all(self.TABLE)

    def list_low_stock(self) -> list[dict]:
        return [r for r in self.list() if r["quantity"] <= r["reorder_threshold"]]

    def create(self, item_id: str, name: str, quantity: float, unit: str, reorder_threshold: float = 0.0) -> dict:
        return self._storage.create(
            self.TABLE,
            item_id,
            {"name": name, "quantity": quantity, "unit": unit, "reorder_threshold": reorder_threshold},
        )

    def update_quantity(self, item_id: str, quantity: float) -> dict:
        return self._storage.update(self.TABLE, item_id, {"quantity": quantity})


def ensure_tables(connection_string: str) -> None:
    """Eagerly create all tables at startup (mirrors Base.metadata.create_all for SQL)."""
    storage = get_table_storage(connection_string)
    for table_name in (
        MenuTableRepository.TABLE,
        OrderTableRepository.TABLE,
        ReservationTableRepository.TABLE,
        InventoryTableRepository.TABLE,
    ):
        storage.client(table_name)
