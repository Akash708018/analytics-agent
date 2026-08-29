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
