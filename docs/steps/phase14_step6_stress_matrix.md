# Phase 14 Step 6: a stress matrix -- every tool, many shapes of data, every error written down

Opened 24/09/2026. Asked for: "a tight test case ... not prioritised to one specific problem ...
different types of data to see how the tools perform in each ... a report of all the errors."

## What it is

`scripts/stress_matrix.py`. Not a pytest file, for the reason the eval harness is not (P13-D1):
it is a measurement that reports what it finds and exits zero; a suite that must be 100% cannot
also be the place bugs are counted. It writes `docs/stress/stress_matrix.json` (every call, its
outcome and timing) and prints a table. The report is `docs/stress/REPORT.md`.

Each dataset is generated deterministically in memory (seeded) with its ground truth computed
by the generator in plain Python -- never by the engine it is checking. Every dataset goes
through the whole web path, the one a browser visitor drives (RealBackend), plus the MCP tools
the assistant calls:

    upload -> draft ingest (re-drafted once with header_rows=[1] if provisional) -> load
    -> describe -> profile -> propose cleaning -> apply the suggested steps
    -> draft contract -> answer it from the suggestions -> confirm -> validate
    -> all 27 analyses -> 3 charts -> report

Every call is classified:

- CRASH   an exception escaped a tool (a tool must answer, refusal or result, never raise)
- WRONG   a ground-truth check failed (rows, columns, a measure's sum, a date range)
- SUSPECT the reply prints nan/inf/None as a figure, or a refusal's NEXT STEP is the call that
          was just refused
- REFUSED a structured refusal; judged by hand in the report -- many are correct
- OK

Postgres is not reachable in this container, so the database door is recorded as not exercised.

## Datasets (planned: 26 across CSV and Excel)

Delimiters and encodings: baseline CSV; semicolon with decimal commas; tab; UTF-8 BOM with
accented/CJK/emoji text; Latin-1; quoted fields with commas and newlines; CRLF.
Shape: header only; one row; one column; 200 columns; 200,000 rows; all-null and constant
columns; duplicate and blank column names; SQL-hostile names (quotes, spaces, reserved words).
Values: mixed number/text; five date formats; boolean spellings; currency, percent and thousands
separators; scientific notation, NaN/Infinity text; leading-zero ids; padding, case variants and
missing tokens; exact duplicate rows; negative and zero measures; one group; all-unique
dimension; a time series with gaps.
Excel: several sheets; merged two-row header with a footer note; real Excel dates and formulas;
blank rows mid-data; an empty sheet first.

## Commands

1. `uv run python scripts/stress_matrix.py`. Expected: no prediction of counts -- this is the
   measurement. Predicted qualitatively: CSV dialects other than comma load wrong or refuse;
   Latin-1 is refused or mangled; SQL-hostile names break a later stage; the 27 analyses refuse
   often on data with no date column (correct).
2. Triage every non-OK line into: bug (with a reproduction), correct refusal, or harness error.
3. The report, docs/stress/REPORT.md, and a published copy for reading.
4. Engine suite, UI suite, acceptance, eval (nothing in src/ changes in this step).
5. Commit and push.

## Results

1. First run on the control alone: 11 REFUSED on clean data. All were the harness's own choices, not
   the engine's: it picked customer_id (60 groups) as the first dimension, over the 49-group cap
   (a correct refusal), and drew charts from results offering two series without naming y.
   1.1 Dimensions are now ordered by distinct count (fewest first, as a person picks) and each
   chart names y. The control then ran 46 of 46 OK and the unicode case 47 of 47.

2. Full run, 36 datasets:

       36 datasets, 1448 records in 98.5s: CRASH 2, WRONG 6, SUSPECT 2, REFUSED 157, OK 1281

   The qualitative predictions: other CSV dialects load wrong -- WRONG for tab (it loaded right),
   right for decimal comma and currency (text). Latin-1 refused -- right, and the refusal leaks the
   server path. SQL-hostile names break a later stage -- WRONG: they pass every stage. The
   analyses refuse without a date column -- right.

   2.1 Added three shapes the first list lacked: ambiguous day-first dates, a CSV total row, and a
   header repeated mid-file. The total row doubles every sum (B1). The ambiguous dates passed, but
   my range check could not tell the two readings apart (01/01 and 12/12 are the same either
   way). A row-by-row check: 0 of 200 wrong -- the engine reads them correctly.

   2.2 Reproduced by hand: an Excel formula column WITH cached values, built as Excel saves it.
   openpyxl data_only=True reads [2.5, 5.0, 7.5]; the engine loaded ('=B2*C2', 'VARCHAR'). So B3
   hits every real workbook with formulas, not only script-written ones. Added as
   xlsx_formulas_cached.

   2.3 The leading-zero loss happens at cleaning, after the load-time value check, so the harness
   now re-checks those values after the suggested cleaning. It records
   "BIGINT; missing ['00311', '00355', '00076']".

   Final run:

       40 datasets, 1634 records in 112.3s: CRASH 2, WRONG 15, SUSPECT 2, REFUSED 184, OK 1431

3. Triage and report: docs/stress/REPORT.md, 14 bugs (B1-B14), 5 of them High. Every REFUSED line
   was read. Those not listed as bugs are correct refusals (the cap, no date column, no measure in
   the contract, an empty file) or follow from a listed bug (semicolon's missing second measure is
   B8; zip as a measure is B2).

4. Checks. Expected: unchanged from Step 5 (no src/ or tests/ change).

       1850 passed in 77.75s (0:01:17)
       43 passed in 11.28s
       phase8: 55 passed, 0 failed, 3 skipped
       phase9: 0 passed, 0 failed, 1 skipped
       phase10: 0 passed, 0 failed, 1 skipped
       phase11: 26 passed, 0 failed, 0 skipped
       phase12: 36 passed, 0 failed, 0 skipped
       SCORE: 76/76 (100%)

   Held; 0 ws_ directories left behind by the matrix or the suites.
