# Cleanup Step 8: what the bunty_babli run found -- a keyless contract that hid duplicates, no trend split, a chart that would not default

Found by the user's graded run of the Ask screen on 22/09/2026 (workspace ws_f1704c182539,
test_orders.csv loaded as bunty_babli, 604 rows). The question asked for a deduplicated monthly
trend of order_value, split by channel, charted, with the peak explained. Every figure the agent
gave matched SQL over the RAW table; the key wanted the deduplicated one.

## What was established before this document (read, not run here)

- The confirmed v1 contract has `primary_key: []` and `grain: 'grain: [order_id]'`. The person
  typed the key into the grain field on the Contract screen; nothing noticed.
- Measured on a copy of the session database: 604 rows, 600 distinct order_id, 4 exact duplicate
  rows (ORD-00098, 00254, 00456, 00552 each twice).
- The gate re-verifies a STATED key before every analysis (state.py `_key_verdict`), and propose
  refuses a stated key that fails. A keyless contract is legal by design -- "a coarser grain than
  one row" -- so with no key there is nothing to verify and 604 rows went through.
- Evidence found no unique column and said only "No column or pair identifies a row uniquely".
  It did not say order_id is 600/604 -- and the Phase 4 decision is explicit that the size of the
  repeat is the whole diagnosis: "400 duplicates across 20 values says the grain is wrong; two
  duplicates says the data is dirty." At proposal time, with no key, that sentence was never
  produced.
- The web assistant cannot clean (webapp/agent.py ALLOWED; P14-O2), so "deduplicated" could not
  be satisfied from the browser at all. It should have been SAID.
- No analysis gives a measure per period split by a dimension. trend takes measure and grain;
  cross_tab takes two declared dimensions; growth_decomposition and mix_shift split two named
  periods only; scope is the contract's, not the caller's.
- render_chart(trend, bar, measure="order_value") refused because trend's result offers
  `order_value (sum)` and `rows`. P11-D13 forbids the renderer picking a measure nobody named;
  here the caller named it.

## The fix, in three parts

A. Keys (contract/propose.py, state.py).
   A1. With no usable key, the proposal reports each identifier-shaped column that repeats, with
       its KeyVerdict sentence, and the number of exact duplicate rows. When the exact duplicates
       account for every repeat of that column, it says so and names the cleaning step. These
       are counts, not guesses: D2's "restate what the data says" rule.
   A2. When no key is stated and a stated grain names a table column as a whole word, the
       proposal verifies that column as a key and says what it found, pointing at
       primary_key=[...]. The grain is the person's sentence; the verdict is arithmetic.
   A3. The gate, for a keyless contract, counts exact duplicate rows in the table and, when there
       are any, every result carries a caveat saying so. Silent when there are none (a gate that
       fires when it need not teaches skimming -- Phase 4). Cost is measured first (command 2).
B. trend takes an optional `dimension` (analysis/trend.py). Wide result: period, one column per
   member (NULL as `(null)`), `(all)`, rows. A member with no rows in a period is blank, not zero.
   Capped like cross_tab's columns. Still 27 analyses: this is trend's split, not a new one.
C. Charts (charts/render.py, analysis/tools.py). With y unset:
   C1. a roll-up COLUMN -- `(all)`, `(total)` -- is left out when other series remain, as C98
       leaves out the roll-up row;
   C2. when the analysis was given `measure`, the one series whose header is that measure
       (`order_value` or `order_value (...)`) is drawn, if exactly one is; otherwise `rows` is
       left out when other series remain. Anything still ambiguous refuses as before (P11-D13).

## Commands and outputs

1. Baseline. `uv run pytest -q`.
   Expected: 1839 passed.
2. Ground facts, tests/test_duplicate_facts.py: DuckDB's DISTINCT treats NULLs as equal (two
   rows (1, NULL) are one distinct row -- unlike count(DISTINCT (a,b)), measured in Phase 4 NOT
   to drop nulls, this is about collapsing); the exact-duplicate count on test_orders.csv is 4;
   and the cost of `count(*) - (SELECT count(*) FROM (SELECT DISTINCT * FROM t))` on 5M rows x 8
   columns, printed not asserted.
   Expected: NULLs collapse (1 distinct row); 4 duplicates; 5M rows in 0.5-1.5s. If slower than
   the analysis it gates, A3 moves to proposal time only.
3. Falsify. Write the tests for A, B and C first and run them against the unfixed src/.
   Expected: every new test fails, each for its own reason.
4. Apply A, B, C. Run the new tests, then the suite.
   Expected: new tests pass; suite 1839 + new, 0 failed.
5. Live check on the real file through server.py: load test_orders.csv, propose (evidence names
   order_id 600/604 and 4 exact duplicates), confirm keyless, compute trend -> caveat present;
   trend by channel -> 2025-11 Online + Store = 254,506.43 raw; render_chart(trend, bar,
   measure=order_value) -> draws. Then clean exact duplicates, re-propose with
   primary_key=["order_id"] -> holds; trend 2025-11 = 246,412.22, July blank.
6. The five acceptance scripts. Expected unchanged: 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0.
7. The eval. Expected: SCORE 76/76 (100%).
8. UI tests. Expected: 37 passed.
9. Records: CL8-D entries and MEASURED VALIDATION in decisions.md, CLAUDE.md tallies. Commit.

## Results

1. Baseline. `1839 passed in 44.24s`. As expected.

2. Ground facts. `4 passed`; printed `5M x 8: exact-duplicate count 0.333s, one GROUP BY 0.021s`.
   NULLs collapse (held); broken_sales has 0 exact copies across 186 rows / 181 ids (held); three
   rows copied whole count as 3 (held). THE COST PREDICTION WAS WRONG: 0.333s single run, 0.213s
   best of three -- below 0.5-1.5s. And the fallback I wrote tripped, because it named no
   analysis: best of three on the same table, summary_stats shape 0.162s, trend shape 0.058s,
   verify_key's count(DISTINCT id) 0.084s. Slower than both.
   2.1. A cheaper form, measured before deciding. `count(DISTINCT hash(COLUMNS(*)))` measured
        the wrong thing -- COLUMNS(*) expands to one hash PER COLUMN, and the query returned eight
        numbers. Listing the columns, `count(*) - count(DISTINCT hash(id,a,...,g))`: 0.119s.
        Also measured: hash(1, NULL) = hash(1, NULL) is true.
   Decision: the gate runs the hash screen, and the exact DISTINCT count only when the screen
   reports something. 0.119s is inside the 0.077-0.179s Phase 7 accepted for verify_key, which the
   gate already pays on every keyed contract and which is itself slower than the trend shape.
   A collision can only overstate the screen, never hide a copy, and the exact count settles it.

3. Falsify. 23 new tests: 18 failed, 5 passed. THE PREDICTION "every new test fails" WAS WRONG
   for the five that say nothing happens when nothing should -- no copies, a keyed contract, no
   measure named, a grain naming no column, a lone roll-up column. They cannot fail before the
   behaviour exists; they guard that the fix stays silent. Each of the 18 failed on the missing
   behaviour (absent note, absent caveat, trend's TypeError on dimension, the chart's two-series
   refusal).

4. Apply. test_propose 43 passed; test_state_gate + test_state 36; test_trend 22; charts + tools
   67. Suite `1866 passed`. As expected (1839 + 23 + 4).

5. Live check, through server.py.
   5.1. The upload was gone: `BLOCKED: no file at .../ws_f1704c182539/uploads/test_orders.csv`.
        The workspace directory existed, empty, dated 11:59 -- the signature of workspace.reset,
        which removes and recreates. Not the suite: every test that makes a ws_ id makes a fresh
        random one and removes it. The UI's Reset needs a ticked checkbox and a click. Who reset
        it was not established. The table was recovered from a copy of that workspace's
        session.duckdb taken at the start of this session (604 rows, sum(order_value)
        1,835,396.24) and exported to CSV in the scratchpad.
   Output, excerpted by the replay script:
     A1  Nearest to a key: order_id does not identify a row: 600 distinct value(s) across 604
         keyed row(s), so 4 row(s) repeat a key that is meant to be unique.
         4 row(s) of bunty_babli are exact copies of another row. Removing them would leave
         order_id unique: propose_cleaning_plan(dataset_name="bunty_babli") offers that, ...
     A2  The grain names order_id, but no primary key is stated, so nothing checks it: ...
     A3  trend on v1: 604 of 604 row(s) analysed. / 4 of 604 row(s) in bunty_babli are exact
         copies of another row, and this contract states no primary key, ...
         2025-11 | 254,506.43 | 56   (raw, as the run reported)
     B   | period | Online | Store | (all) | rows |
         | 2025-11 | 180,180.82 | 74,325.61 | 254,506.43 | 56 |      2025-07 blank across the row
     C   bar, no y: "measure order_value (sum)", 11 of 12 point(s) drawn (July blank).
         grouped_bar by channel: measures Online, Store; "(all) totals the columns shown".
     clean C001 DROP_DUPLICATE_ROWS: "604 row(s) before, 600 after".
     v2  Key as stated: order_id is unique across 600 of 600 rows, with no nulls.
         trend: 2025-02 109,073.5 | 2025-05 195,427.19 | 2025-07 blank | 2025-10 142,465.97 |
         2025-11 246,412.22. Split 2025-11: Online 172,086.61, Store 74,325.61.
         frequency channel: Online 332, Store 268.
   Every figure is the user's key. 180,180.82 - 172,086.61 = 8,094.21, ORD-00552's value, an
   Online order. (109,073.5 is base.number's rendering of a DOUBLE; the value is 109,073.50.)
   5.2. The replay found a defect: beneath "Nearest to a key: order_id ..." the grain question
        still read "there is not even a candidate to correct". A test first -- it failed on
        `AttributeError: 'Proposal' object has no attribute 'questions'`, which was the TEST
        being wrong (they are p.contract.questions), then failed against the unfixed propose.py
        (stashed) for the right reason. Fixed: _resolve_key returns the nearest verdict and the
        question names it. test_propose 44 passed. C100.

6. Acceptance. 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. As expected.
7. Eval. `SCORE: 76/76 (100%)`. As expected.
8. UI. `37 passed in 9.03s`. As expected.
   8.1. server.py's docstrings named trend's parameters as "measure, and grain" and grouped_bar
        as for cross_tab and period_compare only. Updated, with the two defaults render_chart now
        honours. Suite after: `1867 passed`.

## Deviations from the plan above, as built

- A1 reports the NEAREST identifier-shaped column, not each one that repeats. On bunty_babli
  customer_id is identifier-shaped too and repeats hundreds of times; that is a foreign key doing
  what foreign keys do, and a note per such column would bury the one near-key. Nearest = fewest
  repeated plus null rows, ties to column order.
- Command 2's count of 4 on test_orders.csv is not a committed test: workspace/ is gitignored, so
  the fact test copies three clean_sales rows whole instead. The 4 was measured on the session copy
  before this document and again in 5.
- A2 verifies every column the grain names, TOGETHER, as one key -- "one row per customer_id per
  order_date" names a composite -- rather than column by column.

MEASURED VALIDATION line and digests: docs/decisions.md, section Cleanup Step 8.
