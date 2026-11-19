# Dash

Mobile-first Streamlit ordering app for **Hayat Drops** (fresh juice) and **JI Foods** (chips & pilau) in Ishaka, Uganda.
Customers build a basket and the order is sent to each vendor as a pre-filled **WhatsApp** message (no payment backend).

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app.py
pytest -q
```

## Deploy (GitHub → Streamlit Community Cloud)
1. Create a GitHub repo and push this folder (`git init && git add . && git commit -m "init" && git remote add origin <url> && git push -u origin main`).
2. Go to share.streamlit.io → **New app** → pick the repo, branch `main`, main file `app.py` → Deploy.
3. Open the URL on a phone → browser menu → **Add to Home screen**.
CI (`.github/workflows/ci.yml`) runs the tests on every push.

## Update the menu
Edit `data/vendors.json` only — prices, flavours, hours, delivery zones, phone numbers. No code change needed.

See `PROGRESS.md` for architecture, assumptions and roadmap.
