# PROGRESS — Dash (handoff document for another model)

_Last updated: 2026-11-18. Status: **v0.1 MVP complete, tested (13 passing), not yet deployed.**_

## 1. Goal
Mobile-first Streamlit app, hosted on GitHub and deployed on Streamlit Community Cloud, that lets customers in Ishaka browse two local vendors, build a cart, and send the order to the vendor via WhatsApp. Source material: three vendor flyers supplied by the owner (Hayat Drops menu, Hayat Drops services, JI Foods menu).

## 2. Source facts (from the flyers — treat as ground truth; keep in data/vendors.json)
**Hayat Drops** — "It's life added to the glass". Weekly specials: Mon Tropical Temptation, Tue Paradise Punch, Wed Golden Elixir, Thu Velvet Sunrise, Fri Nature's Sunrise, Sat Mango Tango, Sun Pineapple Paradise.
Prices (UGX): 300 ml glass 1,000 · 1 L 3,500 · 5 L 18,000 · 10 L 35,000 · 20 L 65,000. Also stocks 2 L, 3 L and "all other quantities" (no price on flyer). Deals in every kind of juice; any fruit named is blended and delivered. Serves introduction ceremonies, Eid celebrations, Nikkah, weddings, corporate events, private parties, door-to-door deliveries, juice-making training. Operates every day; mobile, delivers door to door. WhatsApp/call: 0700 962 284 | 0762 249 091.
**JI Foods** — "Good Food, Great Moments". Chips plain 3,000 and above · Pilau plain 2,000 and above · Chips with liver or beef 6,000 · Pilau with liver or beef 5,000. Location: Abuja stage. Call/WhatsApp 0704747008. Open daily 6:30 pm, Mon–Sun. Free delivery in "evening-safe and walkable distances"; "1,000 Jaj" for the rest of Ishaka.

## 3. Architecture
```
app.py              UI only: 5 tabs (Home, Order, Cart(n), Events, Info). Callbacks mutate st.session_state.cart.
core/data.py        Loads data/vendors.json; lookups, money(), open_status(), todays_special().
core/cart.py        Pure cart logic (add/merge/set_qty/resolve/totals). No Streamlit import.
core/whatsapp.py    wa.me link + order/event message builders, phone validation.
core/theme.py       All CSS/HTML snippets (mobile-first, hides footer, full-width buttons).
data/vendors.json   Single source of truth for menu, prices, zones, hours, phones.
tests/              test_core.py (logic + flyer price checks), test_app_smoke.py (Streamlit AppTest).
.streamlit/config.toml, requirements*.txt, .github/workflows/ci.yml
```
Design rules: prices never stored in cart (resolved from catalog each render); one WhatsApp order per vendor; widget keys are `<prefix>_<vendor>_<item>`; callbacks (`on_click`/`on_change`) used so cart count in the tab label is never stale; qty 0 removes a line; MAX_QTY=50. Times use Africa/Kampala.

## 4. Done
- Catalog, cart, per-vendor checkout, delivery zones/fees, minimum-price ("from") handling, open/closed status, daily juice special, events quote form (Hayat), info tab, validation (name, phone, address unless pickup), WhatsApp deep links, tests, CI, README.

## 5. Assumptions to confirm with the owner
1. "1,000 Jaj" on the JI flyer read as **UGX 1,000**.
2. JI closing time is **not on the flyer**; `23:00` is a placeholder in `vendors.json` (`hours.close`).
3. Hayat delivery fee is not stated → shown as "agreed on WhatsApp"; total omitted until agreed.
4. Chips/Pilau "and above" are treated as **minimum prices**; totals are labelled "(minimum)".
5. Liver/beef choice is a radio stored in the cart line's `note`.
6. 2 L / 3 L Hayat sizes omitted from the cart (no price); handled via "Any fruit" notes/WhatsApp.
7. App name is **Dash** (owner decision).

## 6. Roadmap (suggested order)
1. Confirm assumptions above; add vendor logos/photos in `assets/` (reference from JSON `image` field).
2. Deploy to Streamlit Cloud; share link on vendor WhatsApp statuses.
3. Mobile Money: add a "pay on delivery / MTN MoMo / Airtel Money" selector line in the message (no gateway first); later integrate a gateway.
4. Order log: write orders to Google Sheets or Supabase (use `st.secrets`) so vendors keep a record; simple vendor admin page behind a password.
5. Out-of-stock toggle per item (`available` flag in JSON).
6. Pre-order scheduling (delivery date/time), repeat last order (browser local storage via a small component), Luganda/Runyankore labels, PWA manifest via a custom host page.
7. Analytics (privacy-respecting), rate limiting on event form.

## 7. Conventions for the next model
- Change menu data in JSON, not code. Add a test when adding a field.
- Keep `core/` free of Streamlit imports. Run `pytest -q` before committing.
- Don't add `use_container_width` (deprecated in newer Streamlit); CSS already makes buttons full width.
- Streamlit `st.link_button` cannot live inside `st.form`; that's why forms are plain widgets.
- Streamlit Cloud's filesystem is ephemeral — never persist orders to local files.
