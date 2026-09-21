# Cleanup Step 6: a narrowed Postgres load says it is narrowed, everywhere its numbers go

Raised while evaluating the user's proposal of 21/09/2026: close P9-O4's feature half by
decision, treating the 750,000-row copy limit as enough for this project and in-place analysis
as a future scaling item. That is only sound if a table narrowed to fit the limit is never
reported as the whole table. It was measured before being assumed, and it is.

## Measured, before any change

A scratch workspace, `load_postgres_table(alias="olist", table="geolocation", limit=1000)`, a
contract, `compute_analysis(frequency, column="geolocation_state")`, `build_report`. The source
has 1,000,163 rows; the unnarrowed load is refused at 750,000, as it should be. Then:

- list_datasets, describe_dataset, get_workflow_state, propose, confirm, compute_analysis and
  build_report: none says the table is a subset.
- The report file: "bound to 1,000 row(s)", "1,000 of 1,000 row(s) analysed", and
  "1 distinct value(s) of geolocation_state; all shown". A LIMIT with no ORDER BY took the first
  thousand rows Postgres returned, all in one state. The report reads as "every location in
  Brazil is in one state".

`where` and `limit` were recorded -- `db.register_dataset(notes="where=-, limit=1000")` -- and
read by nothing.

## The fix

1. postgres.load_table records the source's row count too: `notes` gains `source_rows=<n>`.
2. `db.DatasetRecord.narrowing()` returns one sentence when the load was narrowed, None
   otherwise: which rows of how many, from where, under what filter, and -- when a limit was
   applied -- that the rows are whichever Postgres returned first, not a random sample. A
   limit at or above the source size is not a narrowing. A record written before source_rows
   existed still parses, and says the source size was not recorded.
3. `Gate` carries it and puts it first in `caveats`. Every analysis already copies
   gate.caveats into its summary, so it reaches compute_analysis, render_chart and the
   report's findings with no change to the 27 analyses.
4. The report's Caveats and exclusions section leads with it, with or without a contract.
5. get_workflow_state lists it among the dataset's notes.

## Commands and outputs

1. Falsify: tests/test_narrowed_load.py -- the sentence for limit, for where, for both, for a
   limit that did not narrow, for an old record; the gate's first caveat; frequency's summary;
   the report's caveats section; workflow state. Run on the unfixed tree.
   Expected: every test fails (no narrowing(), no Gate field).
2. Apply. Expected: pytest 1766 -> 1766 + the new file's count, all passing.
3. Re-run the Olist probe above. Expected: the subset sentence, with "1,000 of 1,000,163", in
   compute_analysis, get_workflow_state and the report file.
4. Acceptance scripts unchanged: 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. Eval 76/76. Tree clean.
5. Records: C95, CL6-D1; P9-O4 decided with the user. Commit and push.

## Results

1. Falsify. First run: 7 failed, 5 errors -- the errors were the test's own (the fixture's
   contract had no analysis window, so it came back PROVISIONAL with no JSON block; and a
   frozen DatasetRecord was assigned to). 1.1: both fixed; re-run `12 failed`, every one on
   the missing feature. As expected after the fix.
2. Apply. `1778 passed` (1766 + 12). As expected.
3. Olist probe: the sentence with "1,000 of 1,000,163" in get_workflow_state, compute_analysis
   and the report file. As expected.
4. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76; tree clean. As expected.
5. Records: C95, CL6-D1, P9-O4 closed by the user's decision.
