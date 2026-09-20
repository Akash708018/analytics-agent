"""A change split across a dimension, with the parts adding to the whole.

Phase 9, Step 4f. Run from the repo root:

    uv run pytest tests/test_growth_decomposition.py -q

The fixture is built so that the members move further than the total does: one
member leaves between the two periods, two arrive, and the net change is a
fifth of the gross movement. A decomposition that reported only the net would
be hiding four movements behind one number.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_agent.analysis import growth_decomposition as _  # noqa: E402,F401
from analytics_agent.analysis.base import ParamsInvalid, scope_for  # noqa: E402
from analytics_agent.analysis.registry import catalogue, run  # noqa: E402


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
    measures: list = field(default_factory=lambda: [
        FakeMeasure("amount"),
        FakeMeasure("ticket", agg="mean", definition="what one order came to"),
    ])
    dimensions: list = field(default_factory=lambda: ["region"])
    primary_key: list = field(default_factory=lambda: ["id"])


@dataclass
class FakeGate:
    contract: FakeContract
    caveats: list = field(default_factory=list)


# February: north 20, south 30 -- total 50.
# March: north 50, west 10, and 5 against no region at all -- total 65.
# So the total rises 15 while 75 of movement happens underneath it: north up
# 30, south gone entirely at -30, west and the unknown region arriving at +10
# and +5.
SPLIT = """SELECT * FROM (VALUES
  (1, TIMESTAMP '2017-02-10 10:00:00', 'north', 20.00, 4.00),
  (2, TIMESTAMP '2017-02-14 10:00:00', 'south', 30.00, 4.00),
  (3, TIMESTAMP '2017-03-05 11:00:00', 'north', 50.00, 5.00),
  (4, TIMESTAMP '2017-03-20 11:00:00', 'west',  10.00, 2.00),
  (5, TIMESTAMP '2017-03-25 11:00:00', NULL,     5.00, 1.00),
  (6, TIMESTAMP '2017-05-06 09:00:00', 'north', 10.00, 3.00),
  (7, NULL, 'east', 99.00, 9.00)
) v(id, ts, region, amount, ticket)"""


@pytest.fixture()
def con():
    c = duckdb.connect(":memory:")
    c.execute(f"CREATE TABLE sales AS {SPLIT}")
    yield c
    c.close()


def split(con, **params):
    gate = FakeGate(FakeContract())
    scope = scope_for(con, gate)
    params.setdefault("measure", "amount")
    params.setdefault("dimension", "region")
    params.setdefault("baseline", "2017-02")
    params.setdefault("period", "2017-03")
    return run(con, gate, scope, "growth_decomposition", **params)


def at(out, member):
    return next(row for row in out.rows if row[0] == member)


def test_the_members_are_ordered_by_how_far_they_moved(con):
    assert [r[0] for r in split(con).rows] == [
        "north", "south", "west", "(no region)"]


def test_a_contribution_carries_its_sign(con):
    out = split(con)
    assert (at(out, "north")[3], at(out, "south")[3]) == ("30.00", "-30.00")


def test_a_share_may_exceed_the_whole_when_members_offset(con):
    out = split(con)
    assert (at(out, "north")[4], at(out, "south")[4]) == ("+200.0%", "-200.0%")


def test_a_member_missing_from_a_period_is_blank_there_and_zero_in_the_sum(con):
    out = split(con)
    assert at(out, "south")[2] == "" and at(out, "west")[1] == ""
    assert at(out, "west")[3] == "10.00", (
        "West has no February value and its whole March value is its "
        "contribution. Blank in the cell, zero in the arithmetic."
    )


def test_the_contributions_are_checked_against_the_period_totals(con):
    assert "contributions sum to 15.00" in " ".join(split(con).summary)


def test_gross_movement_is_reported_beside_the_net(con):
    text = " ".join(split(con).summary)
    assert "gross movement is 75.00 against a net 15.00" in text, (
        "A net of 15 over a gross of 75 is the case this analysis exists for; "
        "a headline of +15 hides four movements."
    )


def test_entrants_and_leavers_are_named_in_both_directions(con):
    text = " ".join(split(con).summary)
    assert "appear in 2017-03 and not in 2017-02" in text
    assert "appear in 2017-02 and not in 2017-03" in text


def test_an_aggregate_that_does_not_add_is_refused(con):
    with pytest.raises(ValueError) as excinfo:
        split(con, measure="ticket")
    assert "does not add across groups" in str(excinfo.value), (
        "Per-member changes in a mean do not sum to the change in the mean, "
        "and a table of them would look exactly like one that did."
    )


def test_a_column_nobody_declared_as_a_dimension_is_refused(con):
    with pytest.raises(ValueError) as excinfo:
        split(con, dimension="ts")
    assert "not a declared dimension" in str(excinfo.value)


def test_a_period_holding_no_rows_has_no_change_to_decompose(con):
    out = split(con, period="2017-04")
    assert out.rows == []
    assert "no change to decompose" in " ".join(out.summary)


def test_the_unknown_member_is_a_member_and_is_named_as_one(con):
    assert "(no region) is a member here" in " ".join(split(con).summary)


def test_the_two_periods_differ_in_length_and_every_share_carries_it(con):
    text = " ".join(split(con).summary)
    assert "28 days of data against 31" in text
    assert "+10.7% of length" in text


def test_an_undated_row_is_in_neither_period(con):
    assert "no ts and are in neither month" in " ".join(split(con).summary)


def test_a_period_the_calendar_does_not_have_is_refused(con):
    with pytest.raises(ParamsInvalid) as excinfo:
        split(con, period="2019-11")
    assert "is not a month" in str(excinfo.value)


def test_a_label_that_is_sql_is_refused_rather_than_run(con):
    """The labels are bound, and they never reach the query anyway."""
    with pytest.raises(ParamsInvalid) as excinfo:
        split(con, period="2017-03' OR '1'='1")
    assert "is not a month" in str(excinfo.value)


def test_the_method_note_is_the_first_summary_line(con):
    gate = FakeGate(FakeContract())
    scope = scope_for(con, gate)
    out = run(con, gate, scope, "growth_decomposition", measure="amount",
              dimension="region", baseline="2017-02", period="2017-03")
    assert out.summary[0] == scope.method_note()


def test_the_catalogue_reports_name_tier_and_a_sentence(con):
    entry = next(c for c in catalogue() if c[0] == "growth_decomposition")
    assert entry[1] == 3 and "sum" in entry[2]
