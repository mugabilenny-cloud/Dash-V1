"""Catalog access. All menu content lives in data/vendors.json (single source of truth)."""
from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "vendors.json"
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@lru_cache(maxsize=1)
def _load() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def currency() -> str:
    return _load()["currency"]


def vendors() -> list[dict]:
    return _load()["vendors"]


def get_vendor(vendor_id: str) -> dict:
    for v in vendors():
        if v["id"] == vendor_id:
            return v
    raise KeyError(vendor_id)


def get_item(vendor: dict, item_id: str) -> dict:
    for cat in vendor["categories"]:
        for it in cat["items"]:
            if it["id"] == item_id:
                return it
    raise KeyError(item_id)


def get_option(item: dict, option_id: str) -> dict:
    for op in item["options"]:
        if op["id"] == option_id:
            return op
    raise KeyError(option_id)


def get_zone(vendor: dict, zone_id: str) -> dict:
    for z in vendor["delivery_zones"]:
        if z["id"] == zone_id:
            return z
    raise KeyError(zone_id)


def todays_special(vendor: dict, now: datetime) -> str | None:
    return vendor.get("weekly_specials", {}).get(DAYS[now.weekday()])


def open_status(vendor: dict, now: datetime) -> tuple[bool | None, str]:
    """(is_open, label). is_open is None when the vendor has no fixed hours."""
    hours = vendor.get("hours")
    if not hours:
        return None, vendor["hours_label"]
    hh, mm = map(int, hours["open"].split(":"))
    ch, cm = map(int, hours["close"].split(":"))
    t = now.hour * 60 + now.minute
    is_open = hh * 60 + mm <= t < ch * 60 + cm
    return is_open, ("Open now" if is_open else "Closed now") + f" · {vendor['hours_label']}"


def money(n: int | float) -> str:
    return f"{currency()} {int(n):,}"
