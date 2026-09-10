"""Counting rows into groups, and cutting the list.

Phase 8, Step 6. Run from the repo root:

    uv run pytest tests/test_frequency.py -q
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_agent.analysis import frequency as _  # noqa: E402,F401
from analytics_agent.analysis.base import scope_for  # noqa: E402
from analytics_agent.analysis.registry import run  # noqa: E402


@dataclass
class FakeMeasure:
    name: str
    agg: str | None = "sum"
    definition: str = "what was charged"
    unit: str | None = "GBP"


@dataclass
class FakeWindow:
    start: date
    end: date


@dataclass
class FakeContract:
    dataset_name: str = "sales"
    date_column: str | None = "ts"
    analysis_window: FakeWindow | None = None
    known_exclusions: list = field(default_factory=list)
    excluded_columns: list = field(default_factory=list)
    measures: list = field(default_factory=lambda: [FakeMeasure("amount")])
    dimensions: list = field(default_factory=lambda: ["region", "channel"])
    primary_key: list = field(default_factory=lambda: ["id"])


@dataclass
class FakeGate:
    contract: FakeContract
    caveats: list = field(default_factory=list)


# North x3, South x2, NULL x2, East x1. Every region ties with another except
# East, so a cut at 2 lands in the middle of a tie.
SALES = """SELECT * FROM (VALUES
 (1,'North', TIMESTAMP '2024-02-01', 10.00::DECIMAL(18,2)),
 (2,'North', TIMESTAMP '2024-03-01', 20.00::DECIMAL(18,2)),
 (3,'North', TIMESTAMP '2024-04-01', -5.00::DECIMAL(18,2)),
 (4,'South', TIMESTAMP '2024-05-01', 20.00::DECIMAL(18,2)),
 (5,'South', TIMESTAMP '2024-06-01', 30.00::DECIMAL(18,2)),
 (6,NULL,    TIMESTAMP '2024-07-01', 40.00::DECIMAL(18,2)),
 (7,NULL,    TIMESTAMP '2024-08-01', 15.00::DECIMAL(18,2)),
 (8,'East',  TIMESTAMP '2024-09-01', 25.00::DECIMAL(18,2))
) v(id, region, ts, amount)"""


@pytest.fixture()
def con():
    c = duckdb.connect()
    c.execute(f"CREATE TABLE sales AS {SALES}")
    yield c
    c.close()


def gate(**kw) -> FakeGate:
    caveats = kw.pop("caveats", [])
    return FakeGate(contract=FakeContract(**kw), caveats=caveats)


def out_for(con, g, kind, **params):
    return run(con, g, scope_for(con, g), kind, **params)


# --- frequency


def test_every_value_is_counted_most_frequent_first(con):
    out = out_for(con, gate(), "frequency", column="region")
    assert [r[0] for r in out.rows] == ["North", "South", "(null)", "East"]
    assert [r[1] for r in out.rows] == ["3", "2", "2", "1"]
    assert out.rows[1][0] == "South", "NULLS LAST breaks the 2-2 tie, every run"


def test_null_is_a_group_with_a_name(con):
    """P8-D5. A blank cell reads as the empty string, which Step 1 measured is
    a different value."""
    out = out_for(con, gate(), "frequency", column="region")
    assert "(null)" in [r[0] for r in out.rows]
    assert any("not the empty string" in s for s in out.summary)


def test_the_share_is_of_the_analysed_rows(con):
    out = out_for(con, gate(), "frequency", column="region")
    assert out.rows[0][2] == "37.5%"
    assert any("share is of the 8 analysed row(s)".lower() in s.lower()
               for s in out.summary)


def test_a_cut_through_a_tie_says_so(con):
    """P8-D4: LIMIT is a claim about the output, "top 2" is a claim about the
    data, and they differ exactly when something ties at the cut."""
    out = out_for(con, gate(), "frequency", column="region", limit=2)
    assert len(out.rows) == 2
    assert any("share the value at the cut" in s for s in out.summary)


def test_a_cut_that_misses_every_tie_says_nothing(con):
    out = out_for(con, gate(), "frequency", column="region", limit=4)
    assert not any("at the cut" in s for s in out.summary)


def test_an_undeclared_column_is_refused_with_the_declared_list(con):
    out = gate()
    with pytest.raises(ValueError) as e:
        out_for(con, out, "frequency", column="id")
    assert "region, channel" in str(e.value)
    assert "profile_dataset" in str(e.value)


def test_an_excluded_column_is_refused_even_if_declared(con):
    with pytest.raises(ValueError) as e:
        out_for(con, gate(excluded_columns=["region"]), "frequency", column="region")
    assert "never to read it" in str(e.value)


def test_an_empty_scope_counts_nothing_and_says_why(con):
    g = gate(analysis_window=FakeWindow(date(2030, 1, 1), date(2030, 12, 31)))
    out = out_for(con, g, "frequency", column="region")
    assert out.rows == []
    assert any("nothing to count" in s for s in out.summary)


# --- top_n


def test_groups_are_ranked_by_the_declared_aggregate(con):
    out = out_for(con, gate(), "top_n", dimension="region", measure="amount")
    # North 25, South 50, (null) 55, East 25 -- and the 25-25 tie is broken by
    # the group name, so East precedes North on every run.
    assert [r[0] for r in out.rows] == ["(null)", "South", "East", "North"]
    assert out.headers[1] == "amount (sum)"


def test_the_share_column_is_of_the_ranked_total(con):
    out = out_for(con, gate(), "top_n", dimension="region", measure="amount")
    assert out.rows[0][3] == "35.5%"  # 55 of 155


def test_a_negative_group_total_drops_the_share_column(con):
    """P8-D2: a share of a signed total is not a proportion."""
    con.execute("UPDATE sales SET amount = -100.0 WHERE id = 8")
    out = out_for(con, gate(), "top_n", dimension="region", measure="amount")
    assert all(r[3] == "" for r in out.rows)
    assert any("not a proportion" in s for s in out.summary)


def test_a_zero_total_drops_the_share_rather_than_dividing(con):
    """P8-D1: x/0 is inf in 1.5.5, not an error, and inf renders as a cell."""
    con.execute("UPDATE sales SET amount = 0.0")
    out = out_for(con, gate(), "top_n", dimension="region", measure="amount")
    assert all(r[3] == "" for r in out.rows)
    assert any("inf rather than an error" in s for s in out.summary)
    assert not any("inf" in str(r[1]) for r in out.rows)


def test_ranking_by_a_non_additive_measure_is_refused(con):
    g = gate(measures=[FakeMeasure("amount", agg="none")])
    with pytest.raises(ValueError) as e:
        out_for(con, g, "top_n", dimension="region", measure="amount")
    assert "non-additive" in str(e.value)


def test_ranking_by_a_measure_with_no_aggregate_is_refused(con):
    g = gate(measures=[FakeMeasure("amount", agg=None)])
    with pytest.raises(ValueError) as e:
        out_for(con, g, "top_n", dimension="region", measure="amount")
    assert "no declared aggregate" in str(e.value)


def test_an_undeclared_measure_is_refused_with_the_list(con):
    with pytest.raises(ValueError) as e:
        out_for(con, gate(), "top_n", dimension="region", measure="profit")
    assert "amount" in str(e.value)


def test_a_tie_at_the_cut_is_reported_for_a_ranking_too(con):
    """Flat amounts make the totals track the row counts: North 30, South 20,
    (null) 20, East 10 -- so a cut at 2 lands inside the 20-20 tie."""
    con.execute("UPDATE sales SET amount = 10.00")
    out = out_for(con, gate(), "top_n", dimension="region", measure="amount", n=2)
    assert any("share the value at the cut" in s for s in out.summary)


def test_the_method_note_and_caveats_travel(con):
    out = out_for(con, gate(caveats=["gained 30 rows since v1"]), "frequency",
                  column="region")
    assert out.summary[0].startswith("8 of 8 row(s) analysed")
    assert "gained 30 rows since v1" in out.summary
