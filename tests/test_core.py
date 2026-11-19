from datetime import datetime

import pytest

from core import cart as cl
from core import data, whatsapp


def test_catalog_integrity():
    ids = [v["id"] for v in data.vendors()]
    assert len(ids) == len(set(ids))
    for v in data.vendors():
        assert v["whatsapp"].startswith("256")
        zone_ids = [z["id"] for z in v["delivery_zones"]]
        assert len(zone_ids) == len(set(zone_ids))
        for cat in v["categories"]:
            for it in cat["items"]:
                oids = [o["id"] for o in it["options"]]
                assert oids and len(oids) == len(set(oids))
                assert all(isinstance(o["price"], int) and o["price"] > 0 for o in it["options"])


def test_menu_prices_match_flyers():
    h = data.get_vendor("hayat")
    prices = {o["id"]: o["price"] for o in data.get_item(h, "daily")["options"]}
    assert prices == {"300ml": 1000, "1l": 3500, "5l": 18000, "10l": 35000, "20l": 65000}
    j = data.get_vendor("ji")
    p = lambda i: data.get_item(j, i)["options"][0]["price"]  # noqa: E731
    assert (p("chips_plain"), p("chips_meat"), p("pilau_plain"), p("pilau_meat")) == (3000, 6000, 2000, 5000)


def test_merge_and_remove():
    c = []
    cl.add_line(c, "ji", "chips_plain", "std", 1)
    cl.add_line(c, "ji", "chips_plain", "std", 2)
    assert len(c) == 1 and c[0]["qty"] == 3
    cl.add_line(c, "ji", "chips_meat", "std", 1, "Liver")
    cl.add_line(c, "ji", "chips_meat", "std", 1, "Beef")
    assert len(c) == 3
    cl.set_qty(c, 0, 0)
    assert len(c) == 2 and cl.count(c) == 2


def test_qty_cap():
    c = []
    cl.add_line(c, "ji", "chips_plain", "std", 999)
    assert c[0]["qty"] == cl.MAX_QTY


def test_totals_and_fees():
    c = []
    cl.add_line(c, "ji", "pilau_meat", "std", 2, "Beef")
    ji = data.get_vendor("ji")
    lines = cl.group_by_vendor(c)["ji"]
    assert cl.totals(lines, ji, "near")["total"] == 10000
    assert cl.totals(lines, ji, "rest")["total"] == 11000
    h = data.get_vendor("hayat")
    c2 = []
    cl.add_line(c2, "hayat", "daily", "1l", 2)
    t = cl.totals(cl.group_by_vendor(c2)["hayat"], h, "town")
    assert t["fee_pending"] and t["subtotal"] == 7000


def test_minimum_flag():
    c = []
    cl.add_line(c, "ji", "chips_plain", "std", 1)
    assert cl.totals(cl.group_by_vendor(c)["ji"], data.get_vendor("ji"), "near")["is_minimum"]


def test_whatsapp_link_and_message():
    c = []
    cl.add_line(c, "ji", "chips_meat", "std", 1, "Liver")
    ji = data.get_vendor("ji")
    lines = cl.group_by_vendor(c)["ji"]
    t = cl.totals(lines, ji, "rest")
    msg = whatsapp.order_message(ji, lines, t, data.get_zone(ji, "rest"), "Amina", "0700000000", "Near market", "")
    assert "Liver" in msg and "UGX 7,000" in msg and "Near market" in msg
    url = whatsapp.link(ji["whatsapp"], msg)
    assert url.startswith("https://wa.me/256704747008?text=") and "\n" not in url


@pytest.mark.parametrize("raw,ok", [("0700 962 284", True), ("+256700962284", True), ("123", False), ("", False)])
def test_phone(raw, ok):
    assert whatsapp.valid_phone(raw) is ok


def test_open_status_and_special():
    ji = data.get_vendor("ji")
    assert data.open_status(ji, datetime(2026, 11, 18, 19, 0))[0] is True
    assert data.open_status(ji, datetime(2026, 11, 18, 12, 0))[0] is False
    assert data.open_status(data.get_vendor("hayat"), datetime(2026, 11, 18, 12, 0))[0] is None
    assert data.todays_special(data.get_vendor("hayat"), datetime(2026, 11, 18)) == "Golden Elixir"  # Wednesday
