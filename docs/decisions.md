# Decisions

Machine-local and implementation choices that are easy to forget six months later. Product locks stay in the build guide (Section 13). This file is the “why did we do *that*?” log.

---

## 2026-08-28 — One Homebrew PostgreSQL 17 cluster for `olist` and `testdb`

**Status:** Done (Step 0.5)

**Context.** Port 5432 had two competing clusters. Postgres.app’s PostgreSQL 18 data directory held the real `olist` warehouse. Homebrew’s PostgreSQL 17 (the version the build guide allows: 16 or 17) was serving `testdb` from Phase 1 and was otherwise empty. Whoever bound 5432 first won; the other looked “down” or empty depending on which postmaster was listening.

**Decision.** Rebuild `olist` from the original CSVs into the Homebrew PG 17 cluster. Do not dump-and-restore 18 → 17 (major-version downgrade). Then retire Postgres.app and delete its cluster.

**Why CSV rebuild, not a dump.** `pg_dump` from 18 is not a supported restore target for 17. Recreating the schema and loading the public Olist CSVs is the faithful path, and it is independently checkable against known warehouse totals.

**Sequence (this order mattered).**

1. Load CSVs into Homebrew PG 17 `olist`.
2. Gate: checksum against the old cluster — `SUM(payment_value)` = **15371741.09**, exact match.
3. Quit / remove Postgres.app so it cannot grab 5432 again.
4. Re-verify on the remaining postmaster: **99,441** orders in `olist`.
5. Delete Postgres.app’s leftover data directory (`var-18`, **418 MB**).

**Outcome.** Postgres.app is gone, `var-18` is gone, and a single PostgreSQL 17 cluster on 5432 serves both `olist` and `testdb`. Source alias `olist` in `~/.analytics-agent/sources.yaml` stays `host=localhost port=5432 dbname=olist`.

- openpyxl merged_cells.ranges is unavailable in read_only=True mode.
  Phase 3 bounded fill must open the workbook twice: normally for merge
  ranges from the header block, read-only for streaming the data.
- DuckDB does not error when read_csv gets FEWER names than the file has
  columns; it silently appends 'columnN'. Loaders count columns first.
- DuckDB parameter binding measured ~3,000 rows/s on this Mac versus
  ~900,000 for staging through a temp CSV and one read_csv. Bulk inserts
  stage; they do not bind.
- Postgres sources attach under their own alias, never a shared "pg".
  A shared name silently reused the first attachment and queried the
  wrong database with no error.

  - Sheet-to-part resolution in the .xlsx zip goes via r:id ->
  xl/_rels/workbook.xml.rels -> Target, never via position in <sheets>.
  Build guide 6.6 used position. On a workbook whose tabs had been
  reordered that returned a different sheet's merge ranges, with no
  error. Rel Targets appear both absolute ("/xl/worksheets/sheet1.xml")
  and relative to xl/ ("worksheets/sheet1.xml"); handle both.
- ET.iterparse must clear on <row>, not on <sheetData>. Rows are
  children of sheetData, so clearing at sheetData's end event frees them
  only after the whole tree is built. On a 200k-row sheet (32 MB of
  XML): 440 MB peak vs 16 MB, and 16.4s vs 7.8s.
- <mergeCells> is written after </sheetData> in OOXML, so the merge scan
  cannot early-exit; every row is streamed past regardless of sheet
  size. That is why the clear-tag choice above matters at all.
- fill_bounded pads rows shorter than the merge extent rather than
  raising IndexError. openpyxl pads to the sheet's declared dimension,
  which tool-generated files can under-report.
- Peak memory is not asserted in the test suite; it is machine-dependent
  and would be flaky. tests/bench_merges.py is run by hand.
- Sheet-to-part resolution in the .xlsx zip goes via r:id ->
  xl/_rels/workbook.xml.rels -> Target, never via position in <sheets>.
  Build guide 6.6 used position. On a workbook whose tabs had been
  reordered that returned a different sheet's merge ranges, with no
  error. Rel Targets appear both absolute ("/xl/worksheets/sheet1.xml")
  and relative to xl/ ("worksheets/sheet1.xml"); handle both.
- ET.iterparse must clear on <row>, not on <sheetData>. Rows are
  children of sheetData, so clearing at sheetData's end event frees them
  only after the whole tree is built. On a 200k-row sheet (32 MB of
  XML): 440 MB peak vs 16 MB, and 16.4s vs 7.8s.
- <mergeCells> is written after </sheetData> in OOXML, so the merge scan
  cannot early-exit; every row is streamed past regardless of sheet
  size. That is why the clear-tag choice above matters at all.
- fill_bounded pads rows shorter than the merge extent rather than
  raising IndexError. openpyxl pads to the sheet's declared dimension,
  which tool-generated files can under-report.
- Peak memory is not asserted in the test suite; it is machine-dependent
  and would be flaky. tests/bench_merges.py is run by hand.
- Fixture shapes: merged_multiheader.xlsx is one sheet 'Sales', 8 cols
  A-H, header block rows 1-2, merges A1:B1 C1:E1 F1:H1.
  messy_headers.xlsx is one sheet 'Report' with no merges at all.
- zsh history expansion rewrites !r inside double quotes. All python -c
  one-liners containing f-string !r conversions use the <<'PY' heredoc
  form instead.

- Header naming conventions, Phase 3 Step 2. Blank columns are named
  column_N by 1-indexed position. Repeated names take _2, _3 with the
  first occurrence keeping the bare name; DuckDB's own _1-on-the-second
  convention reads as though a _0 exists. Target names are lowercase
  snake_case with %->pct, #->num, &->and, and a col_ prefix when the
  name starts with a digit.
- assemble_names refuses merge_refs when source_type='csv' rather than
  ignoring them. There is no argument combination that fills a CSV
  header, so no later step can quietly enable it.
- The merged-cell NOTE counts blanks in the header row as read, not
  after filling. After filling that count is always zero, which would
  make the note useless.
- Dedup skips a suffix that is already taken: 'units', 'units_2',
  'units' yields 'units_3', not a second 'units_2'.

- Sheet-to-part resolution in the .xlsx zip goes via r:id ->
  xl/_rels/workbook.xml.rels -> Target, never via position in <sheets>.
  Build guide 6.6 used position. On a workbook whose tabs had been
  reordered that returned a different sheet's merge ranges, with no
  error. Rel Targets appear both absolute ("/xl/worksheets/sheet1.xml")
  and relative to xl/ ("worksheets/sheet1.xml"); handle both.
- ET.iterparse must clear on <row>, not on <sheetData>. Rows are
  children of sheetData, so clearing at sheetData's end event frees them
  only after the whole tree is built. On a 200k-row sheet (32 MB of
  XML): 440 MB peak vs 16 MB, and 16.4s vs 7.8s.
- <mergeCells> is written after </sheetData> in OOXML, so the merge scan
  cannot early-exit; every row is streamed past regardless of sheet
  size. That is why the clear-tag choice above matters at all.
- fill_bounded pads rows shorter than the merge extent rather than
  raising IndexError. openpyxl pads to the sheet's declared dimension,
  which tool-generated files can under-report.
- Peak memory is not asserted in the test suite; it is machine-dependent
  and would be flaky. tests/bench_merges.py is run by hand.
- Fixture shapes: merged_multiheader.xlsx is one sheet 'Sales', 8 cols
  A-H, header block rows 1-2, merges A1:B1 C1:E1 F1:H1.
  messy_headers.xlsx is one sheet 'Report' with no merges at all.
- zsh history expansion rewrites !r inside double quotes. All python -c
  one-liners containing f-string !r conversions use the <<'PY' heredoc
  form instead.

- Header naming conventions, Phase 3 Step 2. Blank columns are named
  column_N by 1-indexed position. Repeated names take _2, _3 with the
  first occurrence keeping the bare name; DuckDB's own _1-on-the-second
  convention reads as though a _0 exists. Target names are lowercase
  snake_case with %->pct, #->num, &->and, and a col_ prefix when the
  name starts with a digit.
- assemble_names refuses merge_refs when source_type='csv' rather than
  ignoring them. There is no argument combination that fills a CSV
  header, so no later step can quietly enable it.
- The merged-cell NOTE counts blanks in the header row as read, not
  after filling. After filling that count is always zero, which would
  make the note useless.
- Dedup skips a suffix that is already taken: 'units', 'units_2',
  'units' yields 'units_3', not a second 'units_2'.

- IngestSpec stores sheet coordinates (header_rows, data_start_row as
  1-indexed row numbers); the Phase 2 loaders take a count of rows to
  skip. The conversion is data_start_row - 1 and lives only in
  IngestSpec.loader_header_rows. It is NOT len(header_rows): for
  messy_headers.xlsx that is 1 where the loader needs 4.
- to_loader_kwargs(loader) inspects the real signature and raises
  SpecNotSupported naming any field the loader cannot accept, rather
  than dropping it. A spec that promises what the loader ignores is
  worse than one that refuses, because the user confirmed terms that
  were never applied.
- Five conventions locked, industry-standard: delete the duplicate
  merged_ranges in excel.py (deferred to Step 5, same edit as the other
  loader changes); header_join bottom_only for merged_multiheader.xlsx;
  propose the join mode with reasoning rather than asking; na_values on
  both loaders for parity; footer_skip_rows yes, skip_columns dropped
  because the columns list already expresses column selection.
- Still owed to Phase 2 in Step 5: na_values and footer_skip_rows on
  load_excel and load_csv, coercion_failures: dict[str, int] on
  LoadResult for F9, and deletion of excel.merged_ranges.

- Sheet-to-part resolution in the .xlsx zip goes via r:id ->
  xl/_rels/workbook.xml.rels -> Target, never via position in <sheets>.
  Build guide 6.6 used position. On a workbook whose tabs had been
  reordered that returned a different sheet's merge ranges, with no
  error. Rel Targets appear both absolute ("/xl/worksheets/sheet1.xml")
  and relative to xl/ ("worksheets/sheet1.xml"); handle both.
- ET.iterparse must clear on <row>, not on <sheetData>. Rows are
  children of sheetData, so clearing at sheetData's end event frees them
  only after the whole tree is built. On a 200k-row sheet (32 MB of
  XML): 440 MB peak vs 16 MB, and 16.4s vs 7.8s.
- <mergeCells> is written after </sheetData> in OOXML, so the merge scan
  cannot early-exit; every row is streamed past regardless of sheet
  size. That is why the clear-tag choice above matters at all.
- fill_bounded pads rows shorter than the merge extent rather than
  raising IndexError. openpyxl pads to the sheet's declared dimension,
  which tool-generated files can under-report.
- Peak memory is not asserted in the test suite; it is machine-dependent
  and would be flaky. tests/bench_merges.py is run by hand.
- Fixture shapes: merged_multiheader.xlsx is one sheet 'Sales', 8 cols
  A-H, header block rows 1-2, merges A1:B1 C1:E1 F1:H1.
  messy_headers.xlsx is one sheet 'Report' with no merges at all.
- zsh history expansion rewrites !r inside double quotes. All python -c
  one-liners containing f-string !r conversions use the <<'PY' heredoc
  form instead.

- Header naming conventions, Phase 3 Step 2. Blank columns are named
  column_N by 1-indexed position. Repeated names take _2, _3 with the
  first occurrence keeping the bare name; DuckDB's own _1-on-the-second
  convention reads as though a _0 exists. Target names are lowercase
  snake_case with %->pct, #->num, &->and, and a col_ prefix when the
  name starts with a digit.
- assemble_names refuses merge_refs when source_type='csv' rather than
  ignoring them. There is no argument combination that fills a CSV
  header, so no later step can quietly enable it.
- The merged-cell NOTE counts blanks in the header row as read, not
  after filling. After filling that count is always zero, which would
  make the note useless.
- Dedup skips a suffix that is already taken: 'units', 'units_2',
  'units' yields 'units_3', not a second 'units_2'.

- IngestSpec stores sheet coordinates (header_rows, data_start_row as
  1-indexed row numbers); the Phase 2 loaders take a count of rows to
  skip. The conversion is data_start_row - 1 and lives only in
  IngestSpec.loader_header_rows. It is NOT len(header_rows): for
  messy_headers.xlsx that is 1 where the loader needs 4.
- to_loader_kwargs(loader) inspects the real signature and raises
  SpecNotSupported naming any field the loader cannot accept, rather
  than dropping it. A spec that promises what the loader ignores is
  worse than one that refuses, because the user confirmed terms that
  were never applied.
- Five conventions locked, industry-standard: delete the duplicate
  merged_ranges in excel.py (deferred to Step 5, same edit as the other
  loader changes); header_join bottom_only for merged_multiheader.xlsx;
  propose the join mode with reasoning rather than asking; na_values on
  both loaders for parity; footer_skip_rows yes, skip_columns dropped
  because the columns list already expresses column selection.
- Still owed to Phase 2 in Step 5: na_values and footer_skip_rows on
  load_excel and load_csv, coercion_failures: dict[str, int] on
  LoadResult for F9, and deletion of excel.merged_ranges.

- The header-row guesser works off one signal: the first row containing a
  non-texty value marks where data starts, then walk up while rows are
  text and non-blank. A blank row stops the walk, which is what cuts a
  title away from the header below it without any special-casing.
- Blanks count as texty. A header row with gaps under merges is still a
  header row. Numeric strings do not: a CSV hands every cell over as str,
  so '10' is parsed rather than trusted, or the first data row reads as a
  header.
- A sparse top row is a spanning header if merges cover it, a title if
  they do not. On CSV neither can be established, so confidence is low,
  draft_spec returns None, and the caller asks. That is the Done-When
  clause about multiheader.csv enforced as control flow rather than as a
  thing to remember.
- headers._build_notes takes the join mode. Under bottom_only the merged
  labels never reach the names, so the note says the merges were filled
  and not used. Claiming otherwise made the assumptions list untrustworthy,
  which defeats its purpose.
- Pivot-dump detection needs 3+ period columns AND at least half of all
  columns. One period column among many is a variable, not a pivot.

- Sheet-to-part resolution in the .xlsx zip goes via r:id ->
  xl/_rels/workbook.xml.rels -> Target, never via position in <sheets>.
  Build guide 6.6 used position. On a workbook whose tabs had been
  reordered that returned a different sheet's merge ranges, with no
  error. Rel Targets appear both absolute ("/xl/worksheets/sheet1.xml")
  and relative to xl/ ("worksheets/sheet1.xml"); handle both.
- ET.iterparse must clear on <row>, not on <sheetData>. Rows are
  children of sheetData, so clearing at sheetData's end event frees them
  only after the whole tree is built. On a 200k-row sheet (32 MB of
  XML): 440 MB peak vs 16 MB, and 16.4s vs 7.8s.
- <mergeCells> is written after </sheetData> in OOXML, so the merge scan
  cannot early-exit; every row is streamed past regardless of sheet
  size. That is why the clear-tag choice above matters at all.
- fill_bounded pads rows shorter than the merge extent rather than
  raising IndexError. openpyxl pads to the sheet's declared dimension,
  which tool-generated files can under-report.
- Peak memory is not asserted in the test suite; it is machine-dependent
  and would be flaky. tests/bench_merges.py is run by hand.
- Fixture shapes: merged_multiheader.xlsx is one sheet 'Sales', 8 cols
  A-H, header block rows 1-2, merges A1:B1 C1:E1 F1:H1.
  messy_headers.xlsx is one sheet 'Report' with no merges at all.
- zsh history expansion rewrites !r inside double quotes. All python -c
  one-liners containing f-string !r conversions use the <<'PY' heredoc
  form instead.

- The header-row guesser works off one signal: the first row containing a
  non-texty value marks where data starts, then walk up while rows are
  text and non-blank. A blank row stops the walk, which is what cuts a
  title away from the header below it without any special-casing.
- Blanks count as texty. A header row with gaps under merges is still a
  header row. Numeric strings do not: a CSV hands every cell over as str,
  so '10' is parsed rather than trusted, or the first data row reads as a
  header.
- A sparse top row is a spanning header if merges cover it, a title if
  they do not. On CSV neither can be established, so confidence is low,
  draft_spec returns None, and the caller asks. That is the Done-When
  clause about multiheader.csv enforced as control flow rather than as a
  thing to remember.
- headers._build_notes takes the join mode. Under bottom_only the merged
  labels never reach the names, so the note says the merges were filled
  and not used. Claiming otherwise made the assumptions list untrustworthy,
  which defeats its purpose.
- Pivot-dump detection needs 3+ period columns AND at least half of all
  columns. One period column among many is a variable, not a pivot.

- excel.merged_ranges is deleted. One name, one implementation:
  merges.merged_ranges streams the sheet XML at constant memory. Its
  sheet=None default meant wb.active, so merges.active_sheet_name reads
  activeTab from xl/workbook.xml to preserve that. activeTab is an index
  into <sheets> order, counts hidden sheets, and is NOT the first tab --
  verified against openpyxl on default, 2nd-active, 3rd-active,
  reordered and hidden-sheet workbooks.
- on_error='stop'|'null' on both loaders, default 'stop', so no existing
  call changes behaviour. 'null' nulls the offending CELL, keeps the
  row, and counts per column into LoadResult.coercion_failures (F9).
- DuckDB's store_rejects was rejected for that job: it drops the whole
  ROW (50 of 53 rows kept for 4 bad cells) and writes to persistent
  reject_errors/reject_scans tables that accumulate across loads.
  TRY_CAST over an all_varchar staging table does it cell-wise with no
  side tables, which also matches how the Excel path behaves.
- DuckDB type inference WIDENS rather than fails: a BIGINT column with
  one 'oops' is sniffed VARCHAR. Coercion counts are therefore only
  meaningful once types are pinned, which is what dtypes is for.
- read_csv has no skipfooter. footer_skip_rows counts rows then applies
  LIMIT, which is only correct because a scan preserves file order --
  verified exact on 20,000 rows at threads=8.
- The footer is trimmed BEFORE coercion is counted. Counting first
  reported a failure for a TOTAL row that was then discarded.
- Asymmetry to remember: the Excel loader trims the footer before type
  inference (it owns the row stream), the CSV loader cannot, so a footer
  row still drags its column to VARCHAR. Pin dtypes when a CSV has a
  footer.
- Excel na_values are applied to STRING cells only, before inference, so
  a numeric 0 is never a null token and an integer column containing
  'N/A' stays BIGINT instead of widening to VARCHAR (F5).

- The ingest spec round-trips as JSON rather than living in a
  server-side draft store. A stored draft has to be mutated when the
  user asks for a change, and from that moment what they were shown and
  what will run are two different objects. Handing the JSON out keeps
  them the same object.
- Footer detection is proposed on Excel and asked about on CSV. A sheet
  knows its own row count, so reading the last 20 rows is free; a CSV
  would have to be seeked to its last byte, which on 1.6 GB is not worth
  it to look for a totals row.
- A trailing row counts as junk when fewer than half its columns are
  filled, walking up from the bottom and stopping at the first real row.
  A record with a couple of empty fields is not junk: row 200 of
  messy_headers.xlsx has a blank region and stays.
- load_excel takes dtypes, keyed on the final column name. Without it
  there is no way to say a text column is a date, because inference maps
  a str to VARCHAR and never looks inside it. _coerce parses a string
  into a TIMESTAMP only when the column was pinned, so a bad value is
  counted like any other coercion failure rather than handed to DuckDB.
- propose_ingest_spec is annotated readOnly. Proposing is not loading,
  and Claude Desktop should not ask permission to think.
