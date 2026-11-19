"""Builds WhatsApp deep links (wa.me). Orders are completed in WhatsApp — no payment backend."""
from __future__ import annotations

import re
from urllib.parse import quote

from . import data


def valid_phone(raw: str) -> bool:
    digits = re.sub(r"\D", "", raw or "")
    return 9 <= len(digits) <= 13


def link(number: str, text: str) -> str:
    return f"https://wa.me/{number}?text={quote(text)}"


def order_message(vendor: dict, lines: list[dict], totals: dict, zone: dict,
                  name: str, phone: str, address: str, notes: str) -> str:
    rows = [f"*New order — {vendor['name']}*", ""]
    for l in lines:
        tag = " (from)" if l["is_minimum"] else ""
        extra = f" [{l['note']}]" if l["note"] else ""
        rows.append(f"• {l['qty']} × {l['item_name']} — {l['option_label']}{extra}"
                    f" = {data.money(l['line_total'])}{tag}")
    rows.append("")
    rows.append(f"Subtotal: {data.money(totals['subtotal'])}" + (" (minimum)" if totals["is_minimum"] else ""))
    rows.append(f"Delivery: {zone['label']} — " + (
        "fee to be agreed" if totals["fee_pending"] else data.money(totals["fee"])))
    if not totals["fee_pending"]:
        rows.append(f"*Total: {data.money(totals['total'])}*" + (" (minimum)" if totals["is_minimum"] else ""))
    rows += ["", f"Name: {name}", f"Phone: {phone}"]
    if zone["id"] != "pickup":
        rows.append(f"Deliver to: {address}")
    if notes.strip():
        rows.append(f"Notes: {notes.strip()}")
    return "\n".join(rows)


def event_message(vendor: dict, name: str, phone: str, event_type: str, date_str: str,
                  litres: int, venue: str, flavours: str) -> str:
    rows = [f"*Event enquiry — {vendor['name']}*", "",
            f"Event: {event_type}", f"Date: {date_str}", f"Venue: {venue}",
            f"Approx. quantity: {litres} litres"]
    if flavours.strip():
        rows.append(f"Flavours: {flavours.strip()}")
    rows += ["", f"Name: {name}", f"Phone: {phone}", "", "Please send a quote. Thank you!"]
    return "\n".join(rows)
