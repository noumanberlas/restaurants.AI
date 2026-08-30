from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SEATED = "seated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MenuItemCategory(str, Enum):
    STARTER = "starter"
    MAIN = "main"
    DESSERT = "dessert"
    DRINK = "drink"


# ── Menu ───────────────────────────────────────────────────────────────────────

class MenuItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    price: float
    category: MenuItemCategory
    available: bool = True


# ── Order ──────────────────────────────────────────────────────────────────────

class OrderItem(BaseModel):
    menu_item_id: UUID
    quantity: int = 1
    notes: str = ""


class Order(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    table_number: int
    items: list[OrderItem] = Field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total: float = 0.0


# ── Reservation ────────────────────────────────────────────────────────────────

class Reservation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    customer_name: str
    party_size: int
    date_time: datetime
    table_number: Optional[int] = None
    status: ReservationStatus = ReservationStatus.PENDING
    notes: str = ""


# ── Inventory ──────────────────────────────────────────────────────────────────

class InventoryItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    quantity: float
    unit: str
    reorder_threshold: float = 0.0
