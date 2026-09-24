"""The stress matrix's fourteen bugs (Phase 14 Step 7, P14-O3 to O12), one test each or more.

The files are the matrix's own generated cases (scripts/stress_matrix.py), so what failed there is
exactly what is tested here; each expectation is the generator's plain-Python ground truth.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stress_matrix as sm  # noqa: E402

from analytics_agent import server, workspace  # noqa: E402
from analytics_agent.util import db  # noqa: E402
from analytics_agent.webapp.real_backend import RealBackend  # noqa: E402

CASES = {c.name: c for c in sm.cases()}


@pytest.fixture()
def be():
    return RealBackend()


@pytest.fixture()
def ws(be):
    wid = be.new_workspace_id()
    yield wid
    workspace.reset(wid)
    workspace.workspace_dir(wid).rmdir()


def _upload(be, ws, name):
    c = CASES[name]
    return be.save_upload(ws, c.filename, c.data).path


def _load(be, ws, name, **draft_args):
    d = be.draft_ingest(ws, _upload(be, ws, name), **draft_args)
    assert d.refusal is None, d.refusal and d.refusal.text
    assert not d.unresolved, d.unresolved
    r = be.confirm_ingest(ws, d.spec)
    assert r.ok, r.refusal and r.refusal.text
    return d, r


def _q(ws, sql):
    con = db.connect(ws)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def _steps(be, ws, table):
    return {(s.kind, s.column): s for s in be.propose_cleaning(ws, table).steps}


# --- B1: a CSV total row -------------------------------------------------------------------------

def test_b1_a_csv_total_row_is_found_and_dropped(be, ws):
    d, r = _load(be, ws, "csv_total_row_at_bottom")
    assert d.footer_skip_rows == 1
    assert any("Total" in a for a in d.assumptions), d.assumptions
    t = CASES["csv_total_row_at_bottom"].truth
    n, units = _q(ws, "SELECT count(*), sum(units) FROM with_total")[0]
    assert (n, units) == (t.rows, t.sums["units"])


def test_b1_a_csv_without_a_footer_keeps_every_row(be, ws):
    d, _ = _load(be, ws, "baseline_csv")
    assert d.footer_skip_rows == 0
    assert _q(ws, "SELECT count(*) FROM baseline")[0][0] == 500


# --- B2: leading zeros ---------------------------------------------------------------------------

def test_b2_converting_leading_zero_ids_is_lossy_and_never_suggested(be, ws):
    _load(be, ws, "leading_zero_ids")
    steps = _steps(be, ws, "zips")
    conv = steps.get(("CONVERT_TYPE", "zip"))
    assert conv is not None and conv.lossy and not conv.suggested
    assert any(v.startswith("00") for v in conv.sample), conv.sample


# --- B3: Excel formulas --------------------------------------------------------------------------

def test_b3_formula_columns_load_excels_cached_values(be, ws):
    _load(be, ws, "xlsx_formulas_cached")
    t = CASES["xlsx_formulas_cached"].truth
    typ, total = _q(ws, "SELECT any_value(typeof(revenue)), round(sum(revenue), 2) "
                          "FROM formulas_cached")[0]
    assert typ in ("DOUBLE", "DECIMAL(18,2)") and total == t.sums["revenue"]


def test_b3_formulas_with_no_saved_value_are_named_in_the_draft(be, ws):
    d = be.draft_ingest(ws, _upload(be, ws, "xlsx_formulas_no_cache"))
    assert any("formula" in a and "revenue" in a for a in d.assumptions), d.assumptions
    assert be.confirm_ingest(ws, d.spec).ok
    assert _q(ws, "SELECT count(*) FROM formulas WHERE revenue LIKE '=%'")[0][0] == 0


# --- B4: Infinity and NaN ------------------------------------------------------------------------

@pytest.fixture()
def infinite(be, ws):
    _load(be, ws, "scientific_nan_inf")
    draft = be.draft_contract(ws, "sci", grain="one row = one reading", primary_key=["id"],
                              measures=["reading"], dimensions=[],
                              aggregations={"reading": "sum"},
                              measure_definitions={"reading": "a reading"})
    assert be.confirm_contract(ws, draft).ok
    return ws


@pytest.mark.parametrize("kind", ["summary_stats", "outlier_detection", "distribution",
                                  "confidence_interval"])
def test_b4_non_finite_values_are_set_aside_and_said(infinite, kind):
    kw = {} if kind == "summary_stats" else {"measure": "reading"}
    out = server.compute_analysis(dataset_name="sci", analysis_type=kind,
                                  workspace_id=infinite, **kw)
    assert not out.startswith("BLOCKED"), out[:400]
    assert "finite" in out, out[:1200]


def test_b4_profile_answers_on_non_finite_values(infinite):
    out = server.profile_dataset(dataset_name="sci", workspace_id=infinite)
    assert "reading" in out and "not a finite number" in out, out[:1500]


def test_b4_cleaning_offers_to_null_non_finite_values(be, infinite):
    step = _steps(be, infinite, "sci").get(("NULL_NON_FINITE", "reading"))
    assert step is not None and step.rows_affected == 75 and step.lossy
    assert be.apply_cleaning(infinite, "sci", [step.action_id]).ok
    assert _q(infinite, "SELECT count(*) FROM sci WHERE NOT isfinite(reading)")[0][0] == 0


# --- B5: an empty first sheet --------------------------------------------------------------------

def test_b5_an_empty_first_sheet_is_passed_over_and_said(be, ws):
    d = be.draft_ingest(ws, _upload(be, ws, "xlsx_empty_first_sheet"))
    assert d.refusal is None and d.grid.sheet == "Data", d.message
    assert any("Cover" in a for a in d.assumptions), d.assumptions


def test_b5_naming_an_empty_sheet_is_a_refusal_not_an_exception(be, ws):
    d = be.draft_ingest(ws, _upload(be, ws, "xlsx_empty_first_sheet"), sheet="Cover")
    assert d.refusal is not None and "Data" in d.refusal.text


# --- B6: blank Excel rows ------------------------------------------------------------------------

def test_b6_blank_rows_inside_excel_data_are_skipped_and_counted(be, ws):
    _, r = _load(be, ws, "xlsx_blank_rows_mid")
    assert _q(ws, "SELECT count(*) FROM blanks")[0][0] == 160
    assert "3 blank row" in r.message, r.message


# --- B7: Latin-1 ---------------------------------------------------------------------------------

def test_b7_a_latin1_csv_loads_with_its_text_intact(be, ws):
    _, r = _load(be, ws, "latin1_encoding")
    regions = {v for (v,) in _q(ws, "SELECT DISTINCT region FROM latin1")}
    assert {"Sünd", "Nörd"} <= regions
    assert "Latin-1" in r.message


def test_b7_a_load_failure_never_shows_the_servers_path(be, ws):
    path = be.save_upload(ws, "bad.csv", b"a,b\n1,2\n").path
    d = be.draft_ingest(ws, path)
    spec = dict(d.spec, delimiter="|", columns=d.spec["columns"])  # a wrong delimiter
    r = be.confirm_ingest(ws, spec)
    if not r.ok:
        assert str(workspace.WORKSPACE_ROOT) not in r.refusal.text


# --- B8, B9, B12: numbers and dates written as text ----------------------------------------------

def test_b8_decimal_commas_get_a_conversion(be, ws):
    _load(be, ws, "semicolon_decimal_comma")
    step = _steps(be, ws, "eu_sales").get(("CONVERT_TYPE", "revenue"))
    assert step is not None and not step.lossy and step.suggested, step
    assert be.apply_cleaning(ws, "eu_sales", [step.action_id]).ok
    t = CASES["semicolon_decimal_comma"].truth
    assert round(float(_q(ws, "SELECT sum(revenue) FROM eu_sales")[0][0]), 2) == t.sums["revenue"]


def test_b9_currency_and_thousands_separators_get_a_conversion(be, ws):
    _load(be, ws, "currency_percent_thousands")
    steps = _steps(be, ws, "currency")
    rev = steps.get(("CONVERT_TYPE", "revenue"))
    assert rev is not None and not rev.lossy and rev.suggested
    pct = steps.get(("CONVERT_TYPE", "discount"))
    assert pct is not None and not pct.lossy and "%" in pct.intent
    assert be.apply_cleaning(ws, "currency", [rev.action_id]).ok
    t = CASES["currency_percent_thousands"].truth
    assert round(float(_q(ws, "SELECT sum(revenue) FROM currency")[0][0]), 2) == t.sums["revenue"]


def test_b12_mixed_date_formats_get_a_conversion(be, ws):
    _load(be, ws, "dates_mixed_formats")
    step = _steps(be, ws, "mixdates").get(("CONVERT_TYPE", "order_date"))
    assert step is not None and not step.lossy, step
    assert be.apply_cleaning(ws, "mixdates", [step.action_id]).ok
    lo, hi = _q(ws, "SELECT min(order_date)::DATE::VARCHAR, max(order_date)::DATE::VARCHAR "
                    "FROM mixdates")[0]
    assert (lo, hi) == CASES["dates_mixed_formats"].truth.date_range


# --- B10, B11: header-only and repeated headers --------------------------------------------------

def test_b10_a_header_only_csv_says_it_has_no_data_rows(be, ws):
    d = be.draft_ingest(ws, _upload(be, ws, "header_only"), header_rows=[1])
    r = be.confirm_ingest(ws, d.spec)
    assert not r.ok and "no data rows" in r.refusal.text, r.refusal.text


def test_b11_a_repeated_header_is_found_and_dropping_it_is_free(be, ws):
    _load(be, ws, "repeated_header_mid_file")
    step = _steps(be, ws, "pasted").get(("DROP_HEADER_ROWS", None))
    assert step is not None and step.rows_affected == 1 and step.suggested and not step.lossy
    assert be.apply_cleaning(ws, "pasted", [step.action_id]).ok
    conv = _steps(be, ws, "pasted").get(("CONVERT_TYPE", "units"))
    assert conv is not None and not conv.lossy and conv.suggested


# --- B13, B14: refusal wording, role suggestions -------------------------------------------------

def test_b13_a_missing_argument_is_named_in_the_engines_words(be, ws):
    _load(be, ws, "baseline_csv")
    draft = be.draft_contract(ws, "baseline", grain="one row = one order", primary_key=["order_id"],
                              date_column="order_date", measures=["units"], dimensions=["region"],
                              aggregations={"units": "sum"}, measure_definitions={"units": "u"},
                              analysis_window_start="2023-01-01", analysis_window_end="2024-12-31")
    assert be.confirm_contract(ws, draft).ok
    out = server.compute_analysis(dataset_name="baseline", analysis_type="top_n", workspace_id=ws)
    assert "positional argument" not in out and "top_n()" not in out
    assert 'measure="units"' in out and 'dimension="region"' in out, out


def test_b14_a_fractional_column_with_few_values_is_a_measure(be, ws):
    _load(be, ws, "scientific_nan_inf")
    roles = {c.name: c.suggested_role for c in be.draft_contract(ws, "sci").columns}
    assert roles["reading"] == "measure"


def test_b14_one_row_is_not_every_column_constant(be, ws):
    d, _ = _load(be, ws, "one_row")
    roles = {c.name: c.suggested_role for c in be.draft_contract(ws, d.dataset_name).columns}
    assert roles["revenue"] == "measure" and roles["region"] == "dimension", roles
