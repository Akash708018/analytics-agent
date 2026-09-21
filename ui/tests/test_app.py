"""The app, run headless with streamlit's AppTest, on the fake backend.

AppTest cannot drive st.file_uploader, so the ingest tests seed the session exactly as a finished
upload leaves it; everything after that goes through the real widgets.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ui.fake_backend import FakeBackend  # noqa: E402

APP = str(ROOT / "ui" / "app.py")
SCREENS = {"upload": "ui.screens.ingest", "contract": "ui.screens.contract",
           "ask": "ui.screens.chat", "files": "ui.screens.files"}


def _render(root: str, module: str) -> None:
    """One screen with the app's own theme and sidebar. AppTest.switch_page resolves pages as
    files and app.py's pages are functions routed by url_path, so a screen is run this way;
    test_the_app_itself_starts covers app.py and its navigation."""
    import importlib
    import sys
    sys.path.insert(0, root)
    from ui import components, journey, theme
    from ui.screens import ingest
    theme.apply(journey.stylesheet(), ingest.stylesheet())
    components.sidebar()
    importlib.import_module(module).render()


def screen(name: str) -> AppTest:
    return AppTest.from_function(_render, args=(str(ROOT), SCREENS[name]), default_timeout=30)


def _text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown] + [m.value for m in at.caption]
    parts += [e.value for e in at.error] + [w.value for w in at.warning] + [s.value for s in at.success]
    return "\n".join(str(p) for p in parts)


def test_the_app_itself_starts():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception, at.exception


@pytest.mark.parametrize("name", list(SCREENS))
def test_every_screen_renders_without_an_exception(name):
    at = screen(name).run()
    assert not at.exception, at.exception


def test_the_journey_is_written_and_the_stylesheet_is_one_block():
    at = AppTest.from_file(APP, default_timeout=30).run()
    htmls = [h.proto.body for h in at.get("html")]
    page = next(h for h in htmls if "aa-j-rail" in h)
    assert "How this engine <em>was made.</em>" in page
    assert page.count('class="aa-j-ch"') == 15  # every chapter
    # The portfolio's field notes for this project, in its own words.
    assert "{ contract: confirmed }" in page and "propose → approve → apply" in page
    styles = [h for h in htmls if h.lstrip().startswith("<style>")]
    assert len(styles) == 1  # one checked block: theme.apply, C97
    assert "aa-field" in styles[0] and "aa-inscribe" in styles[0] and "--accent: #9d472c" in styles[0]


def _style(at: AppTest) -> str:
    return next(h.proto.body for h in at.get("html") if h.proto.body.lstrip().startswith("<style>"))


def test_the_motion_switch_stops_every_animation():
    """Compares on with off. The first version looked for "animation: none" after the last
    reduced-motion query -- text the Journey's own query already holds -- and passed with the
    switch disconnected (P14-D14)."""
    from ui import theme
    at = AppTest.from_file(APP, default_timeout=30).run()
    on = _style(at)
    at.sidebar.toggle[0].set_value(False).run()
    assert not at.exception, at.exception
    off = _style(at)
    assert theme._PAUSED not in on
    assert theme._PAUSED in off and off.replace(theme._PAUSED, "") == on


def test_the_sidebar_shows_the_subset_warning_in_full():
    at = AppTest.from_file(APP, default_timeout=30).run()
    htmls = " ".join(h.proto.body for h in at.get("html"))
    assert "1,000 of 1,000,163 rows" in htmls and "not a random sample" in htmls


def test_reset_is_disabled_until_confirmed():
    at = AppTest.from_file(APP, default_timeout=30).run()
    reset = [b for b in at.sidebar.button if b.label == "Reset workspace"][0]
    assert reset.disabled
    at.sidebar.checkbox[0].check().run()
    reset = [b for b in at.sidebar.button if b.label == "Reset workspace"][0]
    assert not reset.disabled


def _seed_ingest(at: AppTest, header_rows=None):
    """Leave the session as a finished upload of sales.csv does."""
    at.run()
    from ui.backend import get_backend
    be = get_backend()
    ws = at.session_state["workspace_id"]
    path = be.save_upload(ws, "sales.csv", b"x").path
    args = {"header_rows": header_rows} if header_rows else {}
    at.session_state["ingest"] = {"token": ("sales.csv", 1), "path": path, "args": args,
                                  "draft": be.draft_ingest(ws, path, **args)}
    return at


def test_confirm_is_disabled_while_the_ingest_draft_is_provisional():
    at = _seed_ingest(screen("upload"))
    at.run()
    assert not at.exception, at.exception
    confirm = [b for b in at.button if b.label == "Confirm and load"][0]
    assert confirm.disabled
    assert "Row 2 sits under the merged label" in _text(at)


def test_answering_the_header_enables_confirm_and_loading_reaches_the_sidebar():
    at = _seed_ingest(screen("upload"), header_rows=[1, 2])
    at.run()
    confirm = [b for b in at.button if b.label == "Confirm and load"][0]
    assert not confirm.disabled
    confirm.click().run()
    assert not at.exception, at.exception
    assert "Loaded **sales**" in _text(at)
    sidebar = " ".join(h.proto.body for h in at.sidebar.get("html"))
    assert "<b>sales</b>" in sidebar  # redrawn after the click


def test_confirm_is_always_available_and_reports_what_is_still_missing_freshly():
    """P14-D30: Confirm was disabled on a stale draft until "Update draft" was clicked. Now it
    checks the form as it is; with the grain and window typed in, only the measures remain."""
    import datetime as dt
    at = screen("contract").run()
    assert not at.exception, at.exception
    confirm = [b for b in at.button if b.label == "Confirm contract"][0]
    assert not confirm.disabled
    at.text_input[0].input("one row = one location sample")
    at.date_input[0].set_value(dt.date(2016, 1, 1))
    at.date_input[1].set_value(dt.date(2018, 12, 31))
    [b for b in at.button if b.label == "Confirm contract"][0].click().run()
    missing = " ".join(w.value for w in at.warning)
    assert "geolocation_lat" in missing          # still missing: the measures' answers
    assert "grain" not in missing.lower() and "window" not in missing.lower()  # typed ones went
    assert not at.success                        # nothing stored


def test_submit_confirms_the_form_as_it_is_now_on_the_real_engine():
    """The one-click path, and what is stored is what is on screen -- not an earlier draft."""
    from analytics_agent import workspace
    from analytics_agent.webapp.real_backend import RealBackend
    from ui.screens.contract import submit
    be = RealBackend()
    ws = be.new_workspace_id()
    try:
        path = be.save_upload(ws, "clean_sales.csv",
                              (ROOT / "tests/fixtures/clean_sales.csv").read_bytes()).path
        assert be.confirm_ingest(ws, be.draft_ingest(ws, path).spec).ok
        answers = dict(grain="one row = one order", primary_key=["order_id"],
                       date_column="order_date", measures=["units", "unit_price", "revenue"],
                       dimensions=["region", "product", "channel"],
                       aggregations={"units": "sum", "unit_price": "none", "revenue": "sum"},
                       measure_definitions={"units": "items", "unit_price": "one item's price",
                                            "revenue": "units x unit_price"},
                       analysis_window_start="2024-01-01", analysis_window_end="2024-12-31",
                       caveats=[])
        earlier, _ = submit(be, ws, "clean_sales", answers, confirm=False)  # a check first
        assert earlier.provisional == []
        edited = {**answers, "grain": "one row = one order line, as edited after the check"}
        fresh, result = submit(be, ws, "clean_sales", edited, confirm=True)
        assert result is not None and result.ok, result
        stored = (workspace.workspace_dir(ws) / "contracts" / "clean_sales.yaml").read_text()
        assert "as edited after the check" in stored   # the form now, not the earlier draft
    finally:
        workspace.reset(ws)
        workspace.workspace_dir(ws).rmdir()


def test_form_answers_reads_roles_and_ignores_blank_definitions():
    import datetime as dt
    from ui.screens.contract import form_answers, plain
    rows = [{"column": "id", "role": "key"}, {"column": "d", "role": "date"},
            {"column": "rev", "role": "measure"}, {"column": "qty", "role": "measure"},
            {"column": "reg", "role": "dimension"}, {"column": "junk", "role": "ignore"}]
    a = form_answers(rows, "  one row = one sale ", dt.date(2024, 1, 1), None, "x\n\n y ",
                     {"rev": "sum", "qty": None, "junk": "sum"},
                     {"rev": " money ", "qty": "  ", "junk": "ignored: not a measure"})
    assert a["primary_key"] == ["id"] and a["date_column"] == "d"
    assert a["measures"] == ["rev", "qty"] and a["dimensions"] == ["reg"]
    assert a["aggregations"] == {"rev": "sum"} and a["measure_definitions"] == {"rev": "money"}
    assert a["grain"] == "one row = one sale" and a["analysis_window_end"] is None
    assert a["caveats"] == ["x", "y"]
    assert plain("measures[rev].agg") == "rev: aggregation" and "window" in plain("analysis_window")


def test_a_refusal_shows_its_next_step():
    at = screen("contract").run()
    from ui.backend import get_backend
    ws = at.session_state["workspace_id"]
    at.session_state["contract_result"] = (
        "geolocation", get_backend().confirm_contract(
            ws, get_backend().draft_contract(ws, "geolocation")))
    at.run()
    text = _text(at)
    assert "still PROVISIONAL" in text and "Next step:" in text


def test_asking_for_a_chart_shows_the_image_and_its_description():
    at = screen("ask").run()
    at.chat_input[0].set_value("show me a chart").run()
    assert not at.exception, at.exception
    assert len(at.get("image")) == 1
    assert "highest 15,873 at East" in _text(at)


def test_a_failed_turn_is_shown_and_the_conversation_survives():
    at = screen("ask").run()
    at.chat_input[0].set_value("fail").run()
    assert "did not answer in time" in _text(at)
    at.chat_input[0].set_value("hello").run()
    assert "Try *show me a chart*" in _text(at)


def test_the_fake_is_the_default_backend(monkeypatch):
    monkeypatch.delenv("ANALYTICS_UI_BACKEND", raising=False)
    from ui import backend
    backend.get_backend.clear()
    assert isinstance(backend.get_backend(), FakeBackend)


def test_the_app_runs_on_the_real_backend(monkeypatch):
    """ANALYTICS_UI_BACKEND=real: every screen renders against the engine, on a fresh workspace."""
    monkeypatch.setenv("ANALYTICS_UI_BACKEND", "real")
    from analytics_agent import workspace
    from analytics_agent.webapp.real_backend import RealBackend
    from ui import backend
    backend.get_backend.clear()
    try:
        assert isinstance(backend.get_backend(), RealBackend)
        at = AppTest.from_file(APP, default_timeout=60).run()
        assert not at.exception, at.exception
        ws = at.session_state["workspace_id"]
        assert ws.startswith("ws_")
        assert any("Nothing loaded yet" in c.value for c in at.sidebar.caption)
        for name in SCREENS:
            s = screen(name)
            s.session_state["workspace_id"] = ws
            assert not s.run().exception, name
    finally:
        backend.get_backend.clear()
        if "ws" in locals():
            workspace.reset(ws)
            workspace.workspace_dir(ws).rmdir()


def test_a_reload_keeps_the_workspace_through_the_url():
    """P14-D20: a reload is a new session; the ws query parameter carries the workspace over."""
    first = AppTest.from_file(APP, default_timeout=30).run()
    ws = first.session_state["workspace_id"]
    assert first.query_params["ws"] == [ws] or first.query_params["ws"] == ws
    reload = AppTest.from_file(APP, default_timeout=30)
    reload.query_params["ws"] = ws
    reload.run()
    assert reload.session_state["workspace_id"] == ws


@pytest.mark.parametrize("bad", ["local", "../etc", "ws_XYZ", "ws_0123456789abcdef"])
def test_a_url_cannot_name_claude_desktops_workspace_or_a_path(bad):
    at = AppTest.from_file(APP, default_timeout=30)
    at.query_params["ws"] = bad
    at.run()
    assert at.session_state["workspace_id"] != bad
    assert at.session_state["workspace_id"].startswith("ws_")


def test_a_window_older_than_ten_years_can_be_set():
    """P14-D31: Streamlit's default date range starts ten years before today, and an earlier
    date was dropped silently -- the window could never be filled for older data."""
    import datetime as dt
    at = screen("contract").run()
    at.date_input(key="c_from_geolocation").set_value(dt.date(2001, 3, 4))
    at.run()
    assert at.date_input(key="c_from_geolocation").value == dt.date(2001, 3, 4)



def test_a_fully_filled_form_confirms_in_one_click():
    """P14-D35: each measure's aggregation and definition are their own fields, so the whole
    form -- and the one-click confirm the user could not reach -- is driven here end to end."""
    import datetime as dt
    at = screen("contract").run()
    at.text_input(key="c_grain_geolocation").input("one row = one location sample")
    at.date_input(key="c_from_geolocation").set_value(dt.date(2016, 9, 1))
    at.date_input(key="c_to_geolocation").set_value(dt.date(2018, 10, 31))
    for m, meaning in (("geolocation_lat", "latitude"), ("geolocation_lng", "longitude")):
        at.selectbox(key=f"c_agg_geolocation_{m}").set_value("none")
        at.text_input(key=f"c_def_geolocation_{m}").input(meaning)
    [b for b in at.button if b.label == "Confirm contract"][0].click().run()
    assert not at.exception, at.exception
    assert not at.warning, [w.value for w in at.warning]
    assert any("Contract **v2** for **geolocation** confirmed" in s.value for s in at.success)


def test_the_measure_fields_offer_no_default():
    at = screen("contract").run()
    agg = at.selectbox(key="c_agg_geolocation_geolocation_lat")
    assert agg.value is None and "none" in agg.options
