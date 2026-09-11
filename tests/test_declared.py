"""Shared declarations, real aggregate types, and Phase 8 Step 7a regressions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from types import SimpleNamespace
from typing import get_args

import duckdb
import pytest
from pydantic import ValidationError

from analytics_agent.analysis import frequency, summary_stats
from analytics_agent.analysis.base import LostRows, ScopeError, scope_for
from analytics_agent.analysis.declared import (
    AGG_SQL,
    agg_of,
    column_types,
    dimension_names,
    is_integer,
    is_numeric,
    require_dimension,
    require_measure,
)
from analytics_agent.analysis.registry import catalogue
from analytics_agent.contract.dataset_contract import AGGREGATIONS, Aggregation, Measure


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


@pytest.fixture
def con():
    with duckdb.connect(":memory:") as connection:
        connection.execute("CREATE TABLE sales(amount DECIMAL(18,2), region VARCHAR)")
        connection.execute("INSERT INTO sales VALUES (10.50, 'North'), (20.25, 'South')")
        yield connection


def test_the_contract_spells_its_aggregates_once():
    assert get_args(Aggregation) == AGGREGATIONS


def test_sql_covers_exactly_what_a_contract_can_declare():
    assert set(AGG_SQL) == set(get_args(Aggregation)) - {"none"}
    assert "none" not in AGG_SQL


def test_a_median_total_agrees_with_its_median_column(con):
    gate = FakeGate(FakeContract(
        date_column=None,
        primary_key=[],
        measures=[FakeMeasure("amount", agg="median")],
    ))
    output = summary_stats.summary_stats(con, gate, scope_for(con, gate))
    assert len(output.rows) == 1
    row = dict(zip(output.headers, output.rows[0]))
    assert row["total"] == row["median"] == "15.375"
    assert row["total"] != "15.37"
    assert row["median"] != "15.37"


def test_agg_of_reads_the_real_measure_and_the_model_refuses_avg():
    assert agg_of(Measure(name="x", agg="mean")) == "mean"
    assert agg_of(Measure(name="x")) is None
    with pytest.raises(ValidationError):
        Measure(name="x", agg="avg")


def test_dimension_names_reads_strings_and_objects():
    contract = SimpleNamespace(dimensions=["region", SimpleNamespace(name="channel")])
    assert dimension_names(contract) == ["region", "channel"]


def test_require_dimension_refuses_an_excluded_column_before_anything_else():
    contract = FakeContract(dimensions=[], excluded_columns=["region"])
    with pytest.raises(ValueError) as exc:
        require_dimension(contract, "region")
    assert "never to read it" in str(exc.value)
    assert "Declared:" not in str(exc.value)


def test_require_dimension_refuses_an_undeclared_column_with_the_list():
    with pytest.raises(ValueError) as exc:
        require_dimension(FakeContract(), "unknown")
    assert "Declared: region, channel" in str(exc.value)
    for exclusions in [None, []]:
        contract = SimpleNamespace(dimensions=["region"], excluded_columns=exclusions)
        assert require_dimension(contract, "region") == "region"
    assert require_dimension(SimpleNamespace(dimensions=["region"]), "region") == "region"


def test_require_measure_returns_the_measure_object():
    measure = FakeMeasure("amount")
    contract = FakeContract(measures=[measure])
    assert require_measure(contract, "amount") is measure
    assert require_measure(SimpleNamespace(measures=[measure]), "amount") is measure
    contract.excluded_columns = None
    assert require_measure(contract, "amount") is measure


def test_require_measure_refuses_an_undeclared_measure_with_the_list():
    with pytest.raises(ValueError) as exc:
        require_measure(FakeContract(), "unknown")
    assert "Declared: amount" in str(exc.value)
    with pytest.raises(ValueError) as exc:
        require_measure(FakeContract(measures=[]), "unknown")
    assert "Declared: (none)" in str(exc.value)


def test_require_measure_refuses_an_excluded_measure():
    for measures in [[FakeMeasure("amount")], []]:
        with pytest.raises(ValueError) as exc:
            require_measure(FakeContract(measures=measures, excluded_columns=["amount"]), "amount")
        assert "never to read it" in str(exc.value)
        assert "Declared:" not in str(exc.value)


def test_type_names_are_read_as_duckdb_writes_them():
    for dtype in ["DECIMAL(18,2)", "DOUBLE", "BIGINT"]:
        assert is_numeric(dtype)
    for dtype in ["VARCHAR", "DATE", "TIMESTAMP", "INTERVAL"]:
        assert not is_numeric(dtype)
    for dtype in ["BIGINT", "HUGEINT", "UINTEGER", "UHUGEINT", " bigint "]:
        assert is_integer(dtype)
    for dtype in ["DECIMAL(18,2)", "DOUBLE", "INTERVAL", "INTEGER[]", "BIGINT_EXTRA"]:
        assert not is_integer(dtype)


def test_column_types_are_read_in_column_order(con):
    con.execute("CREATE TABLE ordered(z INTEGER, a DECIMAL(18,2), middle VARCHAR)")
    types = column_types(con, "ordered")
    assert list(types) == ["z", "a", "middle"]
    assert types["a"] == "DECIMAL(18,2)"


def test_top_n_refuses_an_excluded_dimension_and_an_excluded_measure(con):
    for excluded in ["region", "amount"]:
        gate = FakeGate(FakeContract(
            date_column=None,
            primary_key=[],
            excluded_columns=[excluded],
        ))
        with pytest.raises(ValueError) as exc:
            frequency.top_n(con, gate, scope_for(con, gate), dimension="region", measure="amount")
        assert "never to read it" in str(exc.value)


def test_every_registered_analysis_sits_in_its_build_guide_tier():
    tiers = {
        "summary_stats": 1, "distribution": 1, "frequency": 1,
        "cross_tab": 1, "top_n": 1, "group_compare": 2,
        "pareto": 2, "concentration": 2, "ranking_shift": 2,
    }
    entries = catalogue()
    for name, tier, summary in entries:
        assert name in tiers
        assert tier == tiers[name]
    assert dict((name, tier) for name, tier, _ in entries)["top_n"] == 1


def test_lost_rows_is_a_scope_error():
    assert issubclass(LostRows, ScopeError)
    assert issubclass(LostRows, ValueError)
