"""Pure cart logic (no Streamlit imports) so it is unit-testable.

A cart is a list of dicts: {vendor_id, item_id, option_id, qty, note}.
Prices are NEVER stored in the cart; they are resolved from the catalog at render time.
"""
from __future__ import annotations

from . import data

MAX_QTY = 50


def add_line(cart: list[dict], vendor_id: str, item_id: str, option_id: str,
             qty: int = 1, note: str = "") -> None:
    note = note.strip()
    for line in cart:
        if (line["vendor_id"], line["item_id"], line["option_id"], line["note"]) == (
            vendor_id, item_id, option_id, note,
        ):
            line["qty"] = min(MAX_QTY, line["qty"] + qty)
            return
    cart.append({"vendor_id": vendor_id, "item_id": item_id, "option_id": option_id,
                 "qty": min(MAX_QTY, max(1, qty)), "note": note})


def set_qty(cart: list[dict], index: int, qty: int) -> None:
    if not 0 <= index < len(cart):
        return
    if qty <= 0:
        cart.pop(index)
    else:
        cart[index]["qty"] = min(MAX_QTY, qty)


def count(cart: list[dict]) -> int:
    return sum(line["qty"] for line in cart)


def resolve(cart: list[dict]) -> list[dict]:
    """Attach names and prices. Index of the source line is kept as `idx`."""
    out = []
    for idx, line in enumerate(cart):
        v = data.get_vendor(line["vendor_id"])
        it = data.get_item(v, line["item_id"])
        op = data.get_option(it, line["option_id"])
        out.append({
            **line, "idx": idx, "item_name": it["name"], "option_label": op["label"],
            "unit_price": op["price"], "is_minimum": bool(op.get("from")),
            "line_total": op["price"] * line["qty"],
        })
    return out


def group_by_vendor(cart: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for line in resolve(cart):
        groups.setdefault(line["vendor_id"], []).append(line)
    return groups


def totals(lines: list[dict], vendor: dict, zone_id: str) -> dict:
    subtotal = sum(l["line_total"] for l in lines)
    fee = data.get_zone(vendor, zone_id)["fee"]  # None => to be agreed
    return {
        "subtotal": subtotal,
        "fee": fee,
        "total": subtotal + (fee or 0),
        "is_minimum": any(l["is_minimum"] for l in lines),
        "fee_pending": fee is None,
    }
