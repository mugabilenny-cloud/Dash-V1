"""Dash — mobile-first Streamlit ordering app (Hayat Drops + JI Foods).

Run:  streamlit run app.py
Orders are completed over WhatsApp (wa.me deep links); see PROGRESS.md.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from core import cart as cartlib
from core import data, theme, whatsapp

TZ = ZoneInfo("Africa/Kampala")

st.set_page_config(page_title="Dash", page_icon="🍹", layout="centered",
                   initial_sidebar_state="collapsed")
st.markdown(theme.CSS, unsafe_allow_html=True)
st.session_state.setdefault("cart", [])
now = datetime.now(TZ)


# ---------- callbacks (run before the script reruns, so labels/counts stay fresh) ----------
def _wkey(*parts: str) -> str:
    return "_".join(parts)


def add_to_cart(vendor_id: str, item_id: str) -> None:
    v = data.get_vendor(vendor_id)
    it = data.get_item(v, item_id)
    k = lambda p: _wkey(p, vendor_id, item_id)  # noqa: E731
    option_id = st.session_state.get(k("opt"), it["options"][0]["id"])
    qty = int(st.session_state.get(k("qty"), 1))
    note = ""
    if it.get("requires_note"):
        note = (st.session_state.get(k("note")) or "").strip()
        if not note:
            st.toast(f"Please tell us: {it.get('note_label', 'details')}", icon="⚠️")
            return
    if it.get("requires_choice"):
        note = st.session_state.get(k("choice"), it["requires_choice"][0])
    cartlib.add_line(st.session_state.cart, vendor_id, item_id, option_id, qty, note)
    st.session_state[k("qty")] = 1
    st.toast(f"Added {qty} × {it['name']}", icon="✅")


def _find(line_key: tuple) -> int | None:
    for i, l in enumerate(st.session_state.cart):
        if (l["vendor_id"], l["item_id"], l["option_id"], l["note"]) == line_key:
            return i
    return None


def change_qty(line_key: tuple, widget_key: str) -> None:
    i = _find(line_key)
    if i is None:
        return
    qty = int(st.session_state[widget_key])
    cartlib.set_qty(st.session_state.cart, i, qty)
    if qty <= 0:
        st.session_state.pop(widget_key, None)


def clear_vendor(vendor_id: str) -> None:
    st.session_state.cart = [l for l in st.session_state.cart if l["vendor_id"] != vendor_id]
    for k in [k for k in st.session_state if k.startswith("cq_" + vendor_id)]:
        st.session_state.pop(k)


# ---------- layout ----------
n = cartlib.count(st.session_state.cart)
tab_home, tab_order, tab_cart, tab_events, tab_info = st.tabs(
    ["🏠 Home", "🍽️ Order", f"🛒 Cart ({n})", "🎉 Events", "ℹ️ Info"])

# ---- Home
with tab_home:
    st.markdown(theme.hero("Dash", "Fresh juice & hot food, delivered.", "#1B7F3B"),
                unsafe_allow_html=True)
    for v in data.vendors():
        is_open, label = data.open_status(v, now)
        with st.container(border=True):
            st.markdown(f"### {v['emoji']} {v['name']}")
            st.caption(v["tagline"])
            st.markdown(theme.pill(label, is_open), unsafe_allow_html=True)
            special = data.todays_special(v, now)
            if special:
                st.markdown(f"**Today's special:** {special}")
            st.write(v["note"])
            st.caption(f"📍 {v['location']}")
    st.info("Tap **Order** to build your basket, then send it on WhatsApp from **Cart**.")

# ---- Order
with tab_order:
    vendor_id = st.radio("Order from", [v["id"] for v in data.vendors()], horizontal=True,
                         format_func=lambda i: f"{data.get_vendor(i)['emoji']} {data.get_vendor(i)['name']}",
                         key="order_vendor", label_visibility="collapsed")
    v = data.get_vendor(vendor_id)
    is_open, label = data.open_status(v, now)
    st.markdown(theme.pill(label, is_open), unsafe_allow_html=True)
    if is_open is False:
        st.warning("They're closed right now — you can still prepare an order for when they open.")
    for cat in v["categories"]:
        st.subheader(cat["name"])
        for it in cat["items"]:
            k = lambda p, it=it: _wkey(p, vendor_id, it["id"])  # noqa: E731
            with st.container(border=True):
                st.markdown(f"**{it['name']}**")
                desc = it["description"]
                if it.get("dynamic") == "daily_special":
                    desc = f"Today: **{data.todays_special(v, now)}**"
                st.caption(desc)
                ops = it["options"]
                if len(ops) > 1:
                    st.selectbox("Size", [o["id"] for o in ops], key=k("opt"),
                                 format_func=lambda oid, ops=ops: next(
                                     f"{o['label']} — {data.money(o['price'])}" for o in ops if o["id"] == oid))
                else:
                    o = ops[0]
                    st.markdown(f"<span class='price'>{'from ' if o.get('from') else ''}{data.money(o['price'])}</span>",
                                unsafe_allow_html=True)
                    st.session_state[k("opt")] = o["id"]
                if it.get("requires_choice"):
                    st.radio("Choice", it["requires_choice"], horizontal=True, key=k("choice"))
                if it.get("requires_note"):
                    st.text_input(it.get("note_label", "Details"), key=k("note"), placeholder="e.g. passion + mango")
                st.number_input("Quantity", 1, cartlib.MAX_QTY, 1, key=k("qty"))
                st.button("Add to cart", key=k("add"), type="primary",
                          on_click=add_to_cart, args=(vendor_id, it["id"]))

# ---- Cart
with tab_cart:
    if not st.session_state.cart:
        st.info("Your cart is empty. Add something from the Order tab.")
    else:
        st.subheader("Your details")
        c_name = st.text_input("Name", key="c_name")
        c_phone = st.text_input("Phone (WhatsApp)", key="c_phone", placeholder="07XX XXX XXX")
        c_addr = st.text_area("Delivery address / landmark", key="c_addr", height=80)
        c_notes = st.text_input("Notes (optional)", key="c_notes")
        for vid, lines in cartlib.group_by_vendor(st.session_state.cart).items():
            v = data.get_vendor(vid)
            with st.container(border=True):
                st.markdown(f"### {v['emoji']} {v['name']}")
                for l in lines:
                    key = (l["vendor_id"], l["item_id"], l["option_id"], l["note"])
                    wkey = "cq_" + vid + "_" + "_".join(key[1:]).replace(" ", "")
                    extra = f" · {l['note']}" if l["note"] else ""
                    st.markdown(f"**{l['item_name']}** — {l['option_label']}{extra}  \n"
                                f"{'from ' if l['is_minimum'] else ''}{data.money(l['unit_price'])} each "
                                f"→ **{data.money(l['line_total'])}**")
                    st.number_input("Qty (0 removes)", 0, cartlib.MAX_QTY, l["qty"], key=wkey,
                                    on_change=change_qty, args=(key, wkey))
                zone_id = st.selectbox("Delivery", [z["id"] for z in v["delivery_zones"]],
                                       format_func=lambda zid, v=v: data.get_zone(v, zid)["label"],
                                       key=f"zone_{vid}")
                zone = data.get_zone(v, zone_id)
                t = cartlib.totals(lines, v, zone_id)
                st.write(f"Subtotal: **{data.money(t['subtotal'])}**" + (" (minimum)" if t["is_minimum"] else ""))
                st.write("Delivery: " + ("**agreed on WhatsApp**" if t["fee_pending"] else f"**{data.money(t['fee'])}**"))
                if not t["fee_pending"]:
                    st.markdown(f"#### Total: {data.money(t['total'])}" + (" (min.)" if t["is_minimum"] else ""))
                st.caption(v["delivery_note"])
                problems = []
                if not c_name.strip():
                    problems.append("name")
                if not whatsapp.valid_phone(c_phone):
                    problems.append("valid phone")
                if zone_id != "pickup" and not c_addr.strip():
                    problems.append("delivery address")
                if problems:
                    st.caption("Add your " + ", ".join(problems) + " to continue.")
                msg = whatsapp.order_message(v, lines, t, zone, c_name, c_phone, c_addr, c_notes)
                st.link_button(f"Send order to {v['name']} on WhatsApp", whatsapp.link(v["whatsapp"], msg),
                               type="primary", disabled=bool(problems))
                st.button("Clear this order", key=f"clear_{vid}", on_click=clear_vendor, args=(vid,))
        st.caption("You'll confirm and pay the vendor directly on WhatsApp.")

# ---- Events (Hayat Drops catering)
with tab_events:
    hv = data.get_vendor("hayat")
    st.markdown(theme.hero("Events & bulk orders", "Weddings, Nikkah, Eid, corporate & private parties.",
                           hv["accent"]), unsafe_allow_html=True)
    st.write("We serve at: " + ", ".join(hv["serves"]) + ".")
    e_name = st.text_input("Your name", key="e_name")
    e_phone = st.text_input("Phone (WhatsApp)", key="e_phone")
    e_type = st.selectbox("Event type", ["Introduction ceremony", "Wedding", "Nikkah", "Eid celebration",
                                         "Corporate event", "Private party", "Juice-making training", "Other"])
    e_date = st.date_input("Event date", min_value=now.date())
    e_venue = st.text_input("Venue / location", key="e_venue")
    e_litres = st.number_input("Approx. litres needed", 1, 1000, 20, step=5)
    e_flav = st.text_input("Flavours / fruits wanted (optional)", key="e_flav")
    ok = e_name.strip() and whatsapp.valid_phone(e_phone) and e_venue.strip()
    if not ok:
        st.caption("Add your name, a valid phone and the venue to continue.")
    st.link_button("Request a quote on WhatsApp",
                   whatsapp.link(hv["whatsapp"], whatsapp.event_message(
                       hv, e_name, e_phone, e_type, e_date.strftime("%d %b %Y"), int(e_litres), e_venue, e_flav)),
                   type="primary", disabled=not ok)

# ---- Info
with tab_info:
    for v in data.vendors():
        with st.container(border=True):
            st.markdown(f"### {v['emoji']} {v['name']}")
            st.write(f"📍 {v['location']}")
            st.write(f"🕒 {v['hours_label']}")
            st.write("📞 " + " · ".join(v["phones"]))
            st.caption(v["delivery_note"])
            st.link_button("Chat on WhatsApp", f"https://wa.me/{v['whatsapp']}")
    st.caption("Tip: add this page to your phone's home screen from your browser menu for an app-like experience.")
