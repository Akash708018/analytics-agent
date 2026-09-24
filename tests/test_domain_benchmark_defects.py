"""The defects the cross-domain benchmark found (Phase 14 Step 13), one test each.

D1 an analysis over a text measure (count_distinct on a VARCHAR column, averaged by mix_shift)
   raised DuckDB's BinderException out of compute_analysis;
D2 hypothesis_test with two zero-variance groups raised ZeroDivisionError;
D3 a contract accepted a text column as a sum measure, and every analysis over it then raised;
D4 threads first using one workspace raced to create a log table (TransactionException);
D5 the Mann-Whitney tie term overflowed INT64 at 5M rows.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_agent import server, workspace  # noqa: E402
from analytics_agent.analysis import inferential  # noqa: E402
from analytics_agent.contract import store  # noqa: E402


def _block(text: str) -> str:
    return text.split("```json", 1)[1].split("```", 1)[0]


def _load(tmp_path, ws, name, header, rows):
    p = tmp_path / f"{name}.csv"
    p.write_text(header + "\n" + "\n".join(rows) + "\n")
    out = server.confirm_ingest_spec(spec_json=_block(server.propose_ingest_spec(
        path=str(p), dataset_name=name)), workspace_id=ws)
    assert out.startswith("Loaded"), out[:200]


def _contract(ws, name, **kw):
    out = server.propose_dataset_contract(dataset_name=name, workspace_id=ws, **kw)
    if out.startswith("BLOCKED"):
        return out
    return server.confirm_dataset_contract(contract_json=_block(out), workspace_id=ws)


@pytest.fixture()
def ws(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "EXPORT_DIR", tmp_path / "contracts")
    wid = "defects"
    workspace.reset(wid)
    yield wid
    workspace.reset(wid)
    workspace.workspace_dir(wid).rmdir()


ROWS = [f"r{i},2024-{1 + i % 12:02d}-05,{'ab'[i % 2]},c{i % 7},{i % 5}" for i in range(120)]


def test_d1_a_text_measure_in_mix_shift_is_a_refusal(tmp_path, ws):
    _load(tmp_path, ws, "t", "id,d,g,cust,v", ROWS)
    _contract(ws, "t", grain="row", primary_key=["id"], date_column="d",
              measures=["v", "cust"], dimensions=["g"],
              aggregations={"v": "sum", "cust": "count_distinct"},
              measure_definitions={"v": "v", "cust": "customers"},
              analysis_window_start="2024-01-01", analysis_window_end="2024-12-31")
    out = server.compute_analysis(dataset_name="t", analysis_type="mix_shift", measure="cust",
                                  dimension="g", period="2024-12", baseline="2024-11",
                                  workspace_id=ws)
    assert out.startswith("BLOCKED") and "cust is VARCHAR" in out
    assert "reason: ANALYSIS_NOT_POSSIBLE" in out


def test_d2_zero_variance_groups_get_a_stated_no_test(tmp_path, ws):
    rows = [f"r{i},2024-01-05,{'ab'[i % 2]},{3 if i % 2 else 5}" for i in range(20)]
    _load(tmp_path, ws, "z", "id,d,g,v", rows)
    _contract(ws, "z", grain="row", primary_key=["id"], date_column="d", measures=["v"],
              dimensions=["g"], aggregations={"v": "sum"}, measure_definitions={"v": "v"},
              analysis_window_start="2024-01-01", analysis_window_end="2024-12-31")
    for analysis in ("hypothesis_test", "effect_size"):
        out = server.compute_analysis(dataset_name="z", analysis_type=analysis, dimension="g",
                                      measure="v", workspace_id=ws)
        assert not out.startswith("BLOCKED"), out[:300]
        assert "zero variance" in out or "constant" in out, out[:600]
    rank = server.compute_analysis(dataset_name="z", analysis_type="hypothesis_test",
                                   dimension="g", measure="v", method="rank", workspace_id=ws)
    assert "Mann-Whitney" in rank or "No test" in rank


def test_d3_a_text_column_cannot_be_a_sum_measure(tmp_path, ws):
    rows = [f"r{i},2024-01-05,x,,{i}" for i in range(20)]       # v is empty: it loads as VARCHAR
    _load(tmp_path, ws, "n", "id,d,g,v,w", rows)
    out = _contract(ws, "n", grain="row", primary_key=["id"], date_column="d",
                    measures=["v", "w"], dimensions=["g"], aggregations={"v": "sum", "w": "sum"},
                    measure_definitions={"v": "v", "w": "w"},
                    analysis_window_start="2024-01-01", analysis_window_end="2024-12-31")
    assert out.startswith("BLOCKED") and "v is declared a measure with agg='sum'" in out
    assert "propose_cleaning_plan" in out
    ok = _contract(ws, "n", grain="row", primary_key=["id"], date_column="d",
                   measures=["v", "w"], dimensions=["g"],
                   aggregations={"v": "count", "w": "sum"},
                   measure_definitions={"v": "v", "w": "w"},
                   analysis_window_start="2024-01-01", analysis_window_end="2024-12-31")
    assert "Contract stored" in ok, ok[:300]


def test_d4_a_concurrent_creator_does_not_make_the_create_raise(tmp_path):
    """Measured: while one connection's CREATE TABLE IF NOT EXISTS is uncommitted, a second
    connection's raises "Catalog write-write conflict" -- what ten threads hit in the benchmark.
    The first transaction commits 50 ms later; create_if_missing retries and gets through."""
    from analytics_agent.util import db

    a = duckdb.connect(str(tmp_path / "x.duckdb"))
    b = a.cursor()
    ddl = "CREATE TABLE IF NOT EXISTS t (x INT)"
    a.execute("BEGIN")
    a.execute(ddl)
    with pytest.raises(duckdb.TransactionException):
        b.execute(ddl)                                   # the defect, as measured
    timer = threading.Timer(0.05, lambda: a.execute("COMMIT"))
    a.execute("ROLLBACK")
    a.execute("BEGIN")
    a.execute(ddl)
    timer.start()
    db.create_if_missing(b, ddl)                         # retries until the creator commits
    timer.join()
    assert b.execute("SELECT count(*) FROM t").fetchone() == (0,)


def test_d5_the_tie_term_does_not_overflow_at_millions_of_ties():
    con = duckdb.connect()
    con.execute("CREATE TABLE t AS SELECT CASE WHEN i % 2 = 0 THEN 'a' ELSE 'b' END AS g, "
                "CASE WHEN i < 2200000 THEN 0.0 ELSE i::DOUBLE END AS v "
                "FROM range(2300000) r(i)")
    scope = SimpleNamespace(dataset_name="t", where="TRUE")
    result = inferential.mann_whitney(con, scope, "g", "v", "a", "b")
    assert 0.0 <= result.p <= 1.0


# --- next steps the benchmark could not run (Step 13 warnings: 64 unexecutable) -------------


def test_d6_a_key_repeated_only_by_duplicate_rows_points_to_the_cleaning_plan(tmp_path, ws):
    rows = ROWS + ROWS[:3]                                   # three exact duplicate rows
    _load(tmp_path, ws, "t", "id,d,g,cust,v", rows)
    out = _contract(ws, "t", grain="row", primary_key=["id"], date_column="d", measures=["v"],
                    dimensions=["g"], aggregations={"v": "sum"}, measure_definitions={"v": "v"},
                    analysis_window_start="2024-01-01", analysis_window_end="2024-12-31")
    assert out.startswith("BLOCKED") and "KEY_NOT_UNIQUE" in out
    assert 'NEXT STEP: call propose_cleaning_plan(dataset_name="t")' in out, out
    assert "3 row(s) repeat another row in every column" in out


def test_d6_a_key_repeated_by_distinct_rows_keeps_the_contract_call(tmp_path, ws):
    rows = ROWS + [ROWS[0].replace(",0", ",9", 1)[:-1] + "4"]  # same id, different values
    _load(tmp_path, ws, "t", "id,d,g,cust,v", rows)
    out = _contract(ws, "t", grain="row", primary_key=["id"], date_column="d", measures=["v"],
                    dimensions=["g"], aggregations={"v": "sum"}, measure_definitions={"v": "v"},
                    analysis_window_start="2024-01-01", analysis_window_end="2024-12-31")
    assert "KEY_NOT_UNIQUE" in out and "primary_key=[...]" in out, out


def test_d7_correlation_with_one_declared_measure_names_the_contract(tmp_path, ws):
    _load(tmp_path, ws, "t", "id,d,g,cust,v", ROWS)
    _contract(ws, "t", grain="row", primary_key=["id"], date_column="d", measures=["v"],
              dimensions=["g"],
              aggregations={"v": "sum"}, measure_definitions={"v": "v"},
              analysis_window_start="2024-01-01", analysis_window_end="2024-12-31")
    out = server.compute_analysis(dataset_name="t", analysis_type="correlation", measure="v",
                                  workspace_id=ws)
    assert out.startswith("BLOCKED") and 'against="..."' not in out, out
    assert 'propose_dataset_contract(dataset_name="t")' in out


def test_d8_a_corrupt_workbook_is_not_sent_back_through_the_same_file(tmp_path):
    from analytics_agent.ingest import excel
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"PK\x03\x04 not really a workbook")
    with pytest.raises(excel.LoadRefused) as e:
        excel.load_excel(duckdb.connect(), bad, "bad")
    assert f'propose_ingest_spec(path="{bad}")' not in str(e.value)
    assert "save it again as .xlsx" in str(e.value)


def test_d9_the_only_result_file_is_named_as_a_runnable_path(tmp_path, ws):
    from analytics_agent.util import results
    d = results.results_dir(ws)
    d.mkdir(parents=True, exist_ok=True)
    (d / "only.csv").write_text("a\n1\n")
    out = server.read_result_file(path="/etc/passwd", workspace_id=ws)
    assert f'read_result_file(path="{d / "only.csv"}")' in out, out
