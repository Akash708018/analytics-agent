# Phase 12 Step 1 - what each mandatory section can be built from

21/09/2026. Baseline 8f20394. Measured before starting: 1714 passed; test_phase8.py 99/0/2;
test_phase9.py 19/0/0; test_phase10.py 35/0/1; test_phase11.py 26/0/0.

## What the guide asks for

Guide line 949. Nine mandatory sections: the question asked; dataset and grain; a data quality
summary; **the cleaning ledger**; validation results; findings with charts; method notes;
caveats and exclusions; and a reproduction appendix listing exact tool calls. Markdown first.
Files: `report/assemble.py` and `report/templates/`. The Done-When is one end-to-end run on
`merged_multiheader.xlsx` producing a complete document, and that fixture is on disk
(12,024 bytes).

`build_report` returns the report path plus a table of contents and key findings inline, which
is Rule 4 again: a report the agent cannot read back is a path it will describe from its title.

## Why this step builds nothing

A report is an assembly of records other phases wrote. Whether it can be written at all depends
on whether those records exist and what they hold, and that is a question about the repository
rather than about a template. Every phase here has opened by measuring; this one measures what
is on disk and in the workspace catalog rather than what a library does.

## Predictions

Written before the run. 6 and 7 are the ones that decide the phase's shape.

1. The cleaning ledger is complete. `clean/ledger.py` has `record_action`, `entries`, `count`
   and `describe`, so the section is a formatting job.
2. Validation results are recoverable from `validate/runs.py`, which stores runs rather than
   summarising them in place.
3. The profile is recoverable from `profile/runs.py` the same way, and is the data quality
   summary.
4. Dataset and grain come from the confirmed contract via `contract/store.py`, which is the only
   place a grain is agreed.
5. Caveats and exclusions come from the contract's excluded columns and the gate's caveats, both
   already rendered for analyses.
6. Findings are recoverable as far as *which* analyses ran and what they produced -- the result
   files are in `workspace/<id>/results/` and the charts in `charts/` -- but **not** their
   arguments. `write_result` takes label, headers, rows, summary and dataset_name, and no
   parameters, so nothing on disk says a result came from `top_n(dimension="region",
   measure="revenue", n=3)` rather than from some other call to top_n.
7. The reproduction appendix therefore cannot be written exactly from what exists. This is the
   gap I expect to find, and the phase's real design question: either the appendix is
   reconstructed approximately from durable artifacts and says so, or something has to start
   recording calls.
8. The question asked is stored nowhere and has to be an argument to `build_report`.

## Commands

1. Inventory the cleaning ledger: what `LedgerEntry` holds.
2. Inventory validation and profile runs: what is stored and whether it is queryable per dataset.
3. Inventory the result envelope: whether anything on disk names the call that produced it.
4. Inventory the workspace: what a finished run actually leaves behind.
5. Record as P12-D1 onward, and open an item for whatever the appendix cannot reach.

## Outputs

**1-2. Predictions 1 to 5 held, and the records are richer than predicted.** `LedgerEntry`
carries applied_at, dataset_name, plan_id, action_id, kind, column, rows_before, rows_after,
history_table and **the SQL statement itself**, with a `line()` that already renders one.
`validate/runs.py` has ValidationRun with latest/history/state_notes per dataset;
`profile/runs.py` the same with all_latest; `contract/store.py` has current/history/all_current
plus history_text and summarise. Five of the nine sections are a formatting job.

**3. Predictions 6 and 7 held.** `list_results` returns CSV paths and nothing else. A written
result is 121 bytes for a 3x4 table -- `write_result` writes the header row and the data rows,
and that is all: the `summary` it is handed goes into the returned `Result` object, which is
transient. So neither the parameters nor the method note nor the findings prose survive the
call. Nothing on disk says `top_n_20260921-124920.csv` came from
`top_n(dimension="region", measure="revenue", n=3)` rather than from any other call to top_n.

**4. The workspace after one analysis** holds `results/top_n_...csv` and `session.duckdb`. No
chart directory, because none was drawn.

**5. The pattern the analysis tier does not follow.** `ensure_table` appears in five modules --
validate/runs, contract/store, clean/plan, clean/ledger, profile/runs -- each recording its own
runs in the workspace catalog. Analyses and charts record nothing. That is the gap, and it is
not a missing feature so much as one tier declining a convention the other five keep.
