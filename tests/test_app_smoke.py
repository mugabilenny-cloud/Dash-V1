from pathlib import Path

import pytest

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402


def test_app_runs_and_adds_to_cart():
    at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=20).run()
    assert not at.exception
    at.radio(key="order_vendor").set_value("ji").run()
    at.button(key="add_ji_chips_plain").click().run()
    assert not at.exception
    assert at.session_state.cart[0]["item_id"] == "chips_plain"
