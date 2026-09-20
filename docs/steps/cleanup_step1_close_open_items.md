# Cleanup Step 1 - close the remaining open items

21/09/2026. Baseline 03ea6ed (+ b0b0abb, CLAUDE.md). Measured before starting:
`uv run pytest -q` 1662 passed; test_phase8.py 94/0/4; test_phase9.py 16/0/0;
test_phase10.py 35/0/1.

## What this step changes about the plan it came from

The plan `close_remaining_items.md` was read and four defects were measured before
any of it ran. They are recorded here because three of them would have broken the
tree and the fourth would have repeated C68.

- **D1. `NO_MEMBER` is not in `base.py`.** The plan's section 3 writes
  `from .base import NO_MEMBER, ...` into four modules on the strength of the
  sentence "now homed in base.py". Measured: `base.py.__all__` does not contain it,
  and the name exists as three independent literals in `driver_analysis.py:50`,
  `growth_decomposition.py:68` and `mix_shift.py:61`. The import would have raised
  ImportError in four modules at once. Fixed here by actually homing it in `base.py`
  first, which also closes the third instance of P9-O6.
- **D2. `P10-O12` does not exist.** `grep -n "P10-O12" docs/decisions.md` returns
  nothing; the highest recorded item is P10-O13. The item described -- a null group
  named for its column -- is **P9-O8**, recorded at decisions.md:3692. Closing it
  under an invented identifier would have left P9-O8 open permanently.
- **D3. Section 3 has no call-site edits.** It says "the edits follow in one block"
  and no block follows. Run alone it leaves every `excluded.items()` loop printing
  the raw key `no_group` as a user-visible label. The edits are written here.
- **D4. The commit message names a closure the ledger does not write.** Section 4
  appends CLOSED for P10-O13 and P9-O2; section 6 commits "Close P10-O13, P9-O2 and
  P10-O12". That is C68 and C76 in a single line.

Also measured, against the plan's prose: `confidence_interval` both iterates
`excluded.items()` (:108) and appends `NO_GROUP` directly (:162). The plan assigns
it only the second.

## Items this step closes, and on what evidence

Verified in code this session, before any edit:

- **P9-O3** closed. `server.py:750-759` now scopes the claim to a value and names
  the None case, `tools.py` stripping it, and the `bins=10`/`bins=None` contrast.
- **P9-O6** closed. `declared.py:39` owns `ADDITIVE_AGGS`; `period_compare.py:51`
  and `growth_decomposition.py:62` both derive from it.
- **P9-O9** closed. `declared.py:133` defines `require_dimension`;
  `growth_decomposition.py:108` calls it. 19 call sites share it.
- **P9-O7** closed by reading. The item said the answer "depends on an except clause
  below tools.py:119, which has not been read". Read: `except (TypeError,
  ParamsInvalid)` returns a `Refusal` with `ANALYSIS_PARAMS_INVALID`. A forgotten
  required parameter surfaces as an actionable refusal, not a traceback.

Closed by this step's edits: **P10-O13** (guide sentence), **P9-O2** (clause five),
**P9-O8** (the label refactor).

Confirmed still open and left open: **P9-O11** (the tier test iterates `catalogue()`
only; HEAD's new test is the roster check, a different direction), **P9-O12**
(`correlated_shift` imports `_within` and `MIN_SEGMENT` from `changepoint`),
**P9-O5** (no test asserts how `base.number()` renders a float), **P9-O4**'s feature
half (scoped, section 5).

## Commands

1. Role trap, guide line 923. Expected: `role trap corrected`, `1`.
2. Guide row 8. Expected: `row 8 updated`, `24 passed`.
3. Clause five in test_phase9.py. Expected: `clause five added`, `compiles`, and a
   run printing the real date-column shape of order_reviews, order_payments and
   order_items.
4. Home `NO_MEMBER` in `base.py`; the three Tier 4 modules import it.
   Expected: suite still 1662.
5. Separate keys from labels in the four Tier 6 modules. Expected: red suite, and
   the failure list is the map of every display site.
6. Point the call sites at `_shown`. Expected: green.
7. Ledger: closures, C77, the rewritten register, the P9-O4 scope.
8. All four checks, then commit.

## Outputs

**1. Role trap.** `role trap corrected`, then `grep -c` printed **2**, not the 1 the plan
predicted. Reason: the OLD Phase 8 row also contained "role never reaches a confirmed contract",
and the grep ran before that row was rewritten. The plan's expectation forgot its own second
copy. After step 2 the count is 1. Both edits landed; no harm.

**2. Guide row 8.** `row 8 updated`, `24 passed` (test_declared.py parses the guide, so this is
the check that the edit did not break the parse).

**3. Clause five.** `clause five added`, `compiles`. The run reported **4** date columns on
order_reviews (each name twice), 0 on order_payments, **2** on order_items (shipping_limit_date
twice). Wrong. `load_table` attaches the source, so each table exists in two catalogs and a
filter on `table_name` alone counts every column twice.

**3.1 Fix.** Filter on `table_catalog = current_database()`, take one parameter not two, and
assert a measured count rather than `True` (the original check passed unconditionally). Result:
order_reviews 2 (review_creation_date, review_answer_timestamp), order_payments 0, order_items 1
(shipping_limit_date). All three of P9-O2's claims hold. Phase 9 acceptance 16/0/0 -> 19/0/0.

**4. NO_MEMBER homed.** base.py:42 owns it; driver_analysis, growth_decomposition and mix_shift
import it. `grep -rn '^NO_MEMBER = ' src/` returns one line. Suite unchanged at 1662 -- the
collapse changed no behaviour, which is the point.

**5. Keys separated from labels.** Four modules edited, `compiles`, suite **5 failed, 1657
passed**. The five: test_confidence_interval (x2), test_effect_size, test_hypothesis_test,
test_sample_adequacy. That list is the map.

**6. Call sites.** Ten, in three shapes, not four uniform ones. Measure branches (4) take
`_shown(key, dimension, measure)`. The Wilson share branch of confidence_interval has a dimension
and no measure, so the helper was rebuilt one branch at a time -- a dict literal evaluates
`f"(no {measure})"` whichever key is asked for. The association branches of hypothesis_test and
effect_size have two dimensions and no measure, so they take `_shown_pair(dimension, second)`.
Nine test assertions renamed to `(no arm)` / `(no score)`. Suite green at 1662.

**6.1 A branch I changed blind.** Nothing failed when the association label changed, because
region and channel are non-null on all fourteen fixture rows, so `missing` was always 0 and the
label was never rendered by a test. Row 11 has no arm, so `arm x channel` reaches it. One test
added to each of the two modules, asserting `(no arm or channel)` in both a row and the summary.
Suite 1662 -> **1664**.

**7. The role-trap skip went false by this step's own edit.** Its reason quoted the guide
sentence rewritten in command 1. Converted to checks on Olist. The first assertion was the wrong
shape -- it tested that "order_id" was absent and FAILED. Probe output: `Not summarised: key
column(s) order_id, payment_sequential. A column is summarised here when the contract declares it
as a measure.` The identifier appears because the protection fired and said so. The check now
asserts that line. Phase 8 acceptance 94/0/4 -> **96/0/3**.

**8. Ledger.** decisions.md `CLOSED.` count 14 -> 21. Guide rows 8, 9 and 10 updated (5
fragments). Register given a forward pointer rather than an edit. CLAUDE.md tallies synced.
