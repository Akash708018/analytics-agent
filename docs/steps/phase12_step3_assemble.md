# Phase 12 Step 3 - assembling the report

21/09/2026. Baseline be86ffa. Measured before starting: 1732 passed; test_phase8.py 99/0/2;
test_phase9.py 19/0/0; test_phase10.py 35/0/1; test_phase11.py 26/0/0.

## Where the nine sections come from, now that all nine have one

Guide line 949, in order, with the record each reads:

1. **The question asked** -- an argument. P12-D2: nothing in the workspace records why a dataset
   was loaded, and the question belongs to the person rather than to the data.
2. **Dataset and grain** -- `contract/store.current()`, the only place a grain is agreed.
3. **Data quality summary** -- `profile/runs.latest()`: rows, columns, duplicates, columns with
   missing values.
4. **The cleaning ledger** -- `clean/ledger.entries()` and `describe()`, which already renders
   one entry per line with the SQL it ran.
5. **Validation results** -- `validate/runs.latest()`: checks total, failed, not run, against a
   contract version.
6. **Findings, with charts** -- `analysis/runs.history()` and `charts()`, from Step 2. This is
   the section that could not be written a day ago.
7. **Method notes** -- the method note each run stored, which is the sentence saying what the
   numbers were computed over.
8. **Caveats and exclusions** -- the contract's `caveats`, `known_exclusions`,
   `excluded_columns` and `missing_values`.
9. **Reproduction appendix** -- `AnalysisRun.call()` per run, in the order they happened.

## The decision this step turns on

A section with no record must still appear and say so. A report that silently drops "cleaning
ledger" because nothing was cleaned reads as a report of a dataset that needed no cleaning, and
those are different claims. `clean/ledger.describe()` already works this way -- "Nothing has been
cleaned. Every table is as it was" -- and the assembler follows it for all nine.

## Predictions

1. Every section renders from the records above plus the question, with no new computation.
2. A dataset that was never cleaned and never validated produces a report with all nine sections
   present, two of them saying nothing happened -- not a report with seven sections.
3. The appendix renders one line per analysis run in the order they ran, each retypeable.
4. `Report.to_text()` carries the path, a table of contents and the key findings inline, per
   Rule 4, and there is no accessor returning a bare path -- the same promise `Result` and
   `Chart` make.
5. Reports land in `workspace/<id>/reports/`, beside `results/` and `charts/`.
6. Nothing existing changes: no module imports report/, so the suite moves only by the new tests.

## Commands

1. Write `src/analytics_agent/report/assemble.py`.
2. Unit tests: each section present, the empty-record case, the appendix, Rule 4.
3. Full suite and all four acceptance scripts.
4. Record as P12-D11 onward, commit. The MCP tool `build_report` is Step 4, and the end-to-end
   Done-When run on merged_multiheader.xlsx is Step 5.

## Outputs

**1. report/assemble.py**, 344 lines. First write measured 107 characters wide against the
repository's 105; three lines wrapped, now 97. Digest
`8d3df2aee0ca8e9d2d260a58be171619c20cb0ea42c9bce41e83c102bace07ce`.

**A real report, rendered before any test was written**, on a workspace that had loaded a
dataset, confirmed a contract, run one analysis and drawn one chart, and done nothing else:

    clean_sales, 9 section(s), 2 analysis run(s), 1 chart(s).
    Contents: 1..9, all nine headings
    Key findings:
      - top_n: 500 of 500 row(s) analysed.
      - frequency: 500 of 500 row(s) analysed.
    Sections present with nothing to report, which is a finding of its own:
      - Data quality
      - Cleaning ledger
      - Validation results
      - Caveats and exclusions

and in the file, the appendix:

    compute_analysis(dataset_name="clean_sales", analysis_type="top_n",
                     dimension="region", measure="revenue", n=3)
    render_chart(dataset_name="clean_sales", analysis_type="frequency",
                 chart="bar", column="region")

2,865 bytes. Four sections reported nothing and all four appeared.

**2-3.** tests/test_report_assemble.py, 16 tests. Suite 1732 -> 1748. Acceptance unchanged at
99/0/2, 19/0/0, 35/0/1, 26/0/0.

**Predictions: all six held.** Worth noting against Step 2, where prediction 5 was wrong: the
questions here were about code being written rather than about how existing code would react,
and a prediction about what you are about to write is cheaper and tells you less.
