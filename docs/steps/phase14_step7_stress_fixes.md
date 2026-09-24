# Phase 14 Step 7: fixing the stress matrix's fourteen bugs (P14-O3 to O12)

Opened 24/09/2026. Asked for: "use that file to fix all the issue" -- docs/stress/REPORT.md.

## Causes, read from the code before any change

- B1 (CSV total row). preview.draft_spec runs count_trailing_junk only for Excel; for a CSV it
  appends "the end was not examined ... not worth doing on a large file". The premise is wrong:
  reading the last few KB is a seek, the same cost on 10 KB and on 2.5 GB. load_csv already
  honours footer_skip_rows -- only the draft never proposes one. count_trailing_junk also misses a
  total row filled in half its columns or more.
- B2 (leading zeros). clean/detect.proposed_type checks rounding and booleans, not leading zeros;
  convert_type counts a value as lost only when TRY_CAST fails, and '00311' casts.
- B3 (formulas). Every load_workbook call omits data_only=True, so openpyxl returns the formula
  text rather than the value Excel cached.
- B4 (Infinity). stats.stat_exprs, summary_stats, outlier_detection and table_profile aggregate
  raw DOUBLEs; stddev over inf raises. inferential.FINITE already exists (P10-O2) and is used only
  by the tier-6 tests.
- B5 (empty first sheet). draft_for_path reads the ACTIVE sheet even when empty; preview raises
  ValueError, which RealBackend.draft_ingest does not catch (only LoadRefused).
- B6 (blank Excel rows). load_excel streams every row; an all-blank row becomes an all-NULL row.
- B7 (Latin-1). load_csv never passes an encoding; the names check (detect_column_count) runs
  outside the try that converts DuckDB errors, so server.confirm_ingest_spec's generic branch
  prints DuckDB's raw text, which carries the absolute path.
- B8, B9, B12. proposed_type knows only TRY_CAST to one type, so '214,93', '$1,234.56', '12.5%'
  and a column of five date formats have no conversion.
- B10 (header only). The names check reads a zero-row file as one column ('column0').
- B11 (repeated header). Nothing detects rows that repeat the column names.
- B13. analysis/tools passes str(TypeError) straight into WHY.
- B14. suggest_role's small-distinct rule fires for fractional DOUBLEs; one row makes every
  column "constant".

## Decisions

1. B1: the CSV draft reads the file's last 64 KB (a seek) and runs count_trailing_junk on the last
   FOOTER_SCAN_ROWS rows, as Excel does. count_trailing_junk also counts a row whose first
   non-blank cell is a totals label (Total, Grand total, Subtotal, Sum, Totals) however full.
2. B2: a numeric conversion counts a value with a leading zero ('0' followed by a digit) as lost,
   so it is lossy, carries the zeros as its sample, and is never suggested.
3. B3: data_only=True wherever cell values are read. A formula saved without a value then reads
   empty, so the draft says which columns hold formulas with no saved result.
4. B4: derived statistics (mean, median, stddev, quantiles) are taken over finite values, and the
   result says how many non-finite values were set aside. Cleaning offers NULL_NON_FINITE.
5. B5: with no sheet named, the draft reads the first sheet holding data and says so; a named
   empty sheet is a refusal listing the sheets that hold data. The backend catches ValueError.
6. B6: all-blank rows inside Excel data are skipped and counted in the load's notes.
7. B7: the encoding is sniffed from the first 64 KB (UTF-8, else Latin-1); load_csv passes it to
   DuckDB and retries once as Latin-1 on DuckDB's invalid-unicode error, noting it. The preview
   decodes the same way. DuckDB errors shown to a person have the workspace path removed.
8. B8/B9/B12: a conversion may carry its own expression: decimal comma, currency/thousands
   separators and percent to DOUBLE; mixed date formats to DATE/TIMESTAMP via COALESCE of
   TRY_STRPTIME, day-first or month-first decided by values that settle it (none settle it: not
   proposed). Losses are counted from the same expression, as for any conversion.
9. B10: a zero-data-row CSV is refused as "a header and no data rows".
10. B11: DROP_HEADER_ROWS removes rows whose values equal the column names in at least half the
   columns (at least two). Lossless: a copy of the header carries no data.
11. B13: a missing or unexpected argument is named in the engine's words with the contract's
   declared measures/dimensions, and NEXT STEP is a call to that analysis with them filled in.
12. B14: the small-distinct rule applies only to whole-number columns; with one row, "constant"
   does not apply.

## Commands

1. Tests per bug, written to fail first (tests/test_stress_fixes.py), then the code.
2. The stress matrix again. Expected: CRASH 0; WRONG only where the file's meaning is genuinely
   undecidable at load (text numbers the loader correctly keeps as text for cleaning to convert);
   each of B1-B14 either gone or answered with a refusal that states it.
3. Engine suite, UI suite, acceptance, eval. Records; commit and push.

## Results

1. tests/test_stress_fixes.py, 24 tests, written before the code.
   Expected: every one fails except where the engine already behaves.

       22 failed, 2 passed in 9.53s

   The two passes: a CSV with no footer already kept every row, and distribution already bins
   finite values only (P10-O2). Then the fixes, group by group:

   1.1 Loading (B1, B3, B5, B6, B7, B10). DuckDB measured first: encoding='latin-1' reads
   b'S\xfcnd' as 'Sünd'; blank lines are skipped, so they are no footer. Two existing tests
   pinned the old behaviour and were updated on purpose: test_draft's "a CSV draft never guesses
   at a footer" (superseded by decision 1) and "editing the footer away" (203 -> 202 rows: one
   of the three footer rows is blank, a gap now skipped). Ingest tests: 204 passed.
   1.2 My B3 test first failed on its own SQL (typeof beside an aggregate), not on the engine.
   1.3 Cleaning (B2, B8, B9, B11, B12, NULL_NON_FINITE). Two sum checks failed on Decimal vs
   float: money now converts to DECIMAL(18,2), as proposed_type already prefers. Existing
   cleaning tests 155 passed; phase 6 acceptance 36/0/0.
   1.4 Statistics (B4). FINITE moved from inferential.py into stats.py (inferential re-exports
   it). Existing analysis and profile tests: 430 passed.
   1.5 B13, B14. 24 of 24 passed.

2. Full suite: 1874 passed (1850 + 24). Then the matrix.
   Expected: no crash; WRONG only on load-time text that cleaning converts.

       40 datasets, 1728 records in 152.8s: CRASH 0, WRONG 9, SUSPECT 7, REFUSED 145, OK 1567

   Held for crashes; not the whole story. wide_201_columns went from 4.0 s to 24.3 s, a
   regression I caused: profile_dataset on 201 columns took 20.4 s.
   2.1 Measured on 200 columns x 300 rows: plain aggregates 0.07 s; with the FINITE filter on
   each, 10.06 s; with isfinite(), 0.47 s. Integers and DECIMALs cannot hold NaN or Infinity,
   so the filter is now applied to floating-point columns only, as isfinite(). Both
   datasets together: 5.9 s.
   2.2 Six of the seven SUSPECT lines were the engine's own notes naming "NaN or Infinity"; the
   harness now flags nan/inf only in a table's figure cells. The harness also applies up to
   three rounds of suggested cleaning and re-runs every ground-truth check afterwards.

       40 datasets, 1773 records in 134.0s: CRASH 0, WRONG 9, SUSPECT 1, REFUSED 118, OK 1645

   Every one of the 9 WRONG lines is a load-time check, and each dataset's after_clean checks
   (rows, sums, dates) are all OK, except xlsx_formulas_no_cache: that file holds no values to
   load, and the draft now says so. The SUSPECT line is describe_dataset's raw sample of a column
   that really holds nan and inf.

3. Checks. Expected: engine 1874, UI 43, acceptance as in this container, eval 76/76.

       1874 passed in 90.27s (0:01:30)
       43 passed in 11.38s
       phase8: 55 passed, 0 failed, 3 skipped
       phase9: 0 passed, 0 failed, 1 skipped
       phase10: 0 passed, 0 failed, 1 skipped
       phase11: 26 passed, 0 failed, 0 skipped
       phase12: 36 passed, 0 failed, 0 skipped
       phase6:   36 passed, 0 failed, 0 skipped
       SCORE: 76/76 (100%)

   Held. 0 ws_ directories left behind.
