# Cleanup Step 2 - P9-O5, P9-O11 and P9-O12

21/09/2026. Baseline 42e05b4. Measured before starting: `uv run pytest -q` 1664 passed;
test_phase8.py 96/0/3; test_phase9.py 19/0/0; test_phase10.py 35/0/1.

P9-O4's feature half stays open by decision; it is scoped in decisions.md under Cleanup Step 1.

## Ground facts, measured before any edit

**base.number() on a float.** Printed, not recalled:

    number(10.0)                  -> '10'            trailing zeros dropped
    number(0.05)                  -> '0.05'
    number(1234567.89)            -> '1,234,567.89'  thousands separated
    number(23.583333333333332)    -> '23.5833'       four places
    number(2.5)                   -> '2.5'
    number(-0.125)                -> '-0.125'
    number(1e-07)                 -> '0'             a nonzero value renders as zero
    number(Decimal('10.50'))      -> '10.50'         scale kept, not rounded
    number(7)                     -> '7'

`1e-07 -> '0'` is the `text or "0"` fallback at base.py:76 doing its job: rounding to four
places gives 0.0000, rstrip("0").rstrip(".") leaves the empty string, and a cell cannot be
blank. It is correct and it is worth pinning, because a reader seeing 0 has no way to know
the value was not zero.

**P9-O5's suggested home does not exist.** The item says "If analysis/stats.py already owns a
mean renderer, that is the right home and seasonality should adopt it." stats.py exports
STAT_HEADERS, MAX_GROUPS, stat_exprs, stat_cells and ranked_totals, and no renderer.
base.number() is the renderer; there is nothing to adopt.

**P9-O11 has to be restated, because P10-D39 changed what "the map" is.** The item was written
when the tier check compared the registry against a dict typed out in the test. P10-D39 replaced
that dict with the build guide, parsed. So the map is now the guide's tier lists. Measured: the
parse finds 27 names, all 27 are registered, and Tier 8 contributes none -- its listing is prose
("Port SARIMAX/Prophet from Mandi"), not backticked names. So `set(tiers) - registered` is empty
today. The direction the item names is still unasserted: test_declared.py:227 computes `unbuilt`
and then asserts `unbuilt == sorted(unbuilt)`, which is true for every list and tests nothing.

**P9-O12.** `from .changepoint import MIN_SEGMENT, SEPARATION, _within` at correlated_shift.py:43.
Five real sites (`tests/test_results.py:110` is a false match on a test name). changepoint's
`__all__` is `["changepoint"]`, so all three shared names are outside it.

## Commands

1. P9-O5: assert the float rendering in tests/test_stats_facts.py, including the tiny-float
   case and the Decimal contrast. Expected: suite up by the number of assertions' test.
2. P9-O11: replace the no-op at test_declared.py:227 with an assertion that a guide-named
   analysis below Tier 8 must be registered. Expected: green now, and it fails if an analysis
   is de-registered while staying in the guide.
3. P9-O12: rename `_within` to `within` and declare the shared names in `__all__`, so the
   sharing is intentional rather than a private name crossing a module boundary. The alternative
   -- a second copy of the statistic -- is what P9-O6 records going wrong.
4. Ledger and guide row, then all four checks, then commit.

## Outputs

**1. P9-O5.** `float rendering asserted`. One test added to tests/test_stats_facts.py covering
the six values above, the Decimal contrast, and the 1e-07 case. Suite 1664 -> 1665.

**2. P9-O11.** `the guide -> registry direction is now asserted`. The no-op at
test_declared.py:227 is replaced by an assertion that every guide-named analysis below Tier 8 is
registered, Tier 8 exempt because it is unbuilt by design.

**2.1 Proved able to fail.** An assertion that cannot fail is what this item was about, so the
replacement was not taken on trust. With `REGISTRY.pop("pareto")` the test raises:

    AssertionError: the build guide names pareto below Tier 8 and nothing registers them.
    An analysis in the roster that no module registers ...

and passes again once pareto is restored.

**3. P9-O12.** `within is public and declared`, `correlated_shift: imports a declared name`.
`grep -rn "_within" src/` returns nothing. changepoint's `__all__` now carries within,
MIN_SEGMENT and SEPARATION beside the analysis, with the reason above it.

**4. Records.** decisions.md `CLOSED.` count 21 -> 24. Guide Phase 9 row's open list reduced to
P9-O4's feature half alone. The register's forward pointer and CLAUDE.md's suite count synced.

**5. Final.** Unit suite 1665 passed. test_phase8.py 96/0/3, test_phase9.py 19/0/0,
test_phase10.py 35/0/1 -- all three unchanged, which is what a rename and two test changes
should do.
