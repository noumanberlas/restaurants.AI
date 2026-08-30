from __future__ import annotations

import pytest

from src.tools.menu_tools import add_menu_item, get_menu, update_menu_item_availability
from src.tools.order_tools import create_order, get_order, update_order_status
from src.tools.reservation_tools import create_reservation, get_reservation


# ── Menu ───────────────────────────────────────────────────────────────────────

def test_add_and_get_menu_item():
    item = add_menu_item(name="Steak", price=29.99, category="main")
    menu = get_menu()
    assert any(i["id"] == item["id"] for i in menu)


def test_filter_menu_by_category():
    add_menu_item(name="Coke", price=2.50, category="drink")
    drinks = get_menu(category="drink")
    assert all(i["category"] == "drink" for i in drinks)


def test_update_availability():
    item = add_menu_item(name="Soup", price=7.00, category="starter")
    updated = update_menu_item_availability(item["id"], available=False)
    assert updated["available"] is False


# ── Order ──────────────────────────────────────────────────────────────────────

def test_create_and_get_order():
    item = add_menu_item(name="Burger", price=12.00, category="main")
    order = create_order(
        table_number=5,
        items=[{"menu_item_id": item["id"], "quantity": 2}],
    )
    fetched = get_order(order["id"])
    assert fetched["table_number"] == 5


def test_update_order_status():
    item = add_menu_item(name="Pizza", price=15.00, category="main")
    order = create_order(table_number=3, items=[{"menu_item_id": item["id"], "quantity": 1}])
    updated = update_order_status(order["id"], "confirmed")
    assert updated["status"] == "confirmed"


# ── Reservation ────────────────────────────────────────────────────────────────

def test_create_and_get_reservation():
    res = create_reservation(
        customer_name="Alice",
        party_size=4,
        date_time="2026-09-01T19:00:00",
    )
    fetched = get_reservation(res["id"])
    assert fetched["customer_name"] == "Alice"
