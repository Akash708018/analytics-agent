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

- An ambiguous file now yields a PROVISIONAL spec rather than nothing.
  It carries questions and an `unresolved` list; is_confirmable is False
  while that list is non-empty and confirm_ingest_spec refuses it. The
  guarantee is structural, not a docstring.
- That needed override parameters on propose_ingest_spec after all
  (header_rows, header_join, authorised_fill). A provisional spec's
  columns are DERIVED from its header rows, so editing header_rows in
  the JSON would leave names that disagree with it. The answer has to
  come back the way the question went out. C makes it safe, A makes it
  usable; neither works alone.
- assemble_names gains authorised_fill for CSV. Locked decision 8 bans
  filling a CSV header on the FILE's say-so, because the file cannot
  distinguish a spanning label from an empty column. It does not ban
  filling on a human's, which is the point of having asked. Excel plus
  authorised_fill raises, and the note names who authorised it.
- An authorised fill defaults header_join to space. propose_join reads
  the raw rows, where the bottom row is unique, so it would propose
  bottom_only -- discarding the labels the authorisation was given to
  keep.
- na_values=[] built nullstr=[], which DuckDB rejects outright. An empty
  list means the option is omitted. gaps_and_dupes.csv now carries a
  literal 'N/A'; before that no CSV fixture had a sentinel, so nothing
  in the suite exercised na_values on the CSV path at all.
- The Excel loader's dtypes accepts DATE as well as TIMESTAMP, parses an
  ISO string, and leaves a blank cell NULL. Prefer DATE for a date-only
  column: TIMESTAMP invents a midnight component that shows up in every
  later group-by. Both were true before Step 8; only the docstring was
  missing, and two live conversations hedged for want of it.
- Fixture note: SEED 20260829 draws blank regions at about 6.4%, not the
  4% the comment in _sales_rows implies. Every fixture shares one seed
  and one call sequence, so they run high together.

- An ambiguous file now yields a PROVISIONAL spec rather than nothing.
  It carries questions and an `unresolved` list; is_confirmable is False
  while that list is non-empty and confirm_ingest_spec refuses it. The
  guarantee is structural, not a docstring.
- That needed override parameters on propose_ingest_spec after all
  (header_rows, header_join, authorised_fill). A provisional spec's
  columns are DERIVED from its header rows, so editing header_rows in
  the JSON would leave names that disagree with it. The answer has to
  come back the way the question went out. C makes it safe, A makes it
  usable; neither works alone.
- assemble_names gains authorised_fill for CSV. Locked decision 8 bans
  filling a CSV header on the FILE's say-so, because the file cannot
  distinguish a spanning label from an empty column. It does not ban
  filling on a human's, which is the point of having asked. Excel plus
  authorised_fill raises, and the note names who authorised it.
- An authorised fill defaults header_join to space. propose_join reads
  the raw rows, where the bottom row is unique, so it would propose
  bottom_only -- discarding the labels the authorisation was given to
  keep.
- na_values=[] built nullstr=[], which DuckDB rejects outright. An empty
  list means the option is omitted. gaps_and_dupes.csv now carries a
  literal 'N/A'; before that no CSV fixture had a sentinel, so nothing
  in the suite exercised na_values on the CSV path at all.
- The Excel loader's dtypes accepts DATE as well as TIMESTAMP, parses an
  ISO string, and leaves a blank cell NULL. Prefer DATE for a date-only
  column: TIMESTAMP invents a midnight component that shows up in every
  later group-by. Both were true before Step 8; only the docstring was
  missing, and two live conversations hedged for want of it.
- Fixture note: SEED 20260829 draws blank regions at about 6.4%, not the
  4% the comment in _sales_rows implies. Every fixture shares one seed
  and one call sequence, so they run high together.

- Phase 4 splits the contract in two. contract/evidence.py does only what can
  be checked against the data; everything a person has to state (grain,
  measure definitions, exclusions, the analysis window) belongs to the
  proposal layer in Step 3. The split means the evidence can be read without
  being shown a conclusion first.
- count(DISTINCT c) drops nulls; count(DISTINCT (a,b)) does not. So a single
  column is tested against count(*), and a composite can pass uniqueness
  while one of its columns is entirely NULL. Verified on DuckDB 1.5.5: rows
  (1,NULL),(2,NULL) give distinct=2=row count. Unique and usable are separate
  properties and are reported separately.
- Pair search is pruned three ways: a column already unique on its own is
  dropped (a key with a spare column is not a key), a pair needs
  d_a * d_b >= row_count to be possible at all, and what survives is ranked
  and capped at 200 probes with the remainder counted and reported. On a
  200k x 14 table: 91 probes 1.85s -> 25 -> 12 probes 0.52s, and the 22
  "unique pairs" the naive version reported became 9.
- Columns whose suggested role is measure or free_text are excluded from pair
  search. On clean_sales.csv, where unit_price holds 498 distinct values in
  500 rows, 10 of 11 candidates were a near-continuous number paired with
  something irrelevant. A unique measure is still reported as a single, with
  the reason it is unconvincing attached.
- Roles are suggested from counts and names, never asserted: an identifier-
  shaped name outranks cardinality (customer_id repeating 90 ways is still a
  foreign key, and summing it is meaningless), and a numeric column with 12 or
  fewer distinct values is offered as a dimension rather than a measure --
  Olist review scores are 1-5 and J-shaped.
- Known hole, closed in Step 3: a sequence column that is numeric, has more
  than 12 distinct values and is not identifier-named reads as a measure and
  is excluded from pair search, so its composite key is missed. The fix is
  verify_key() -- a stated key is checked, not searched for -- which follows
  Phase 3's rule that the answer comes back the way the question went out.

- D1 locked: a contract is keyed on dataset_name (locked decision 13) and
  bound to a STRUCTURE -- ordered column names and types -- with row count
  and load time recorded beside it. The fingerprint covers structure only:
  a table that gained rows is the same table, one that lost a column is not.
- Drift is classified, not compared: identical / additive / neutral /
  destructive, after schema-registry compatibility modes. Destructive
  (a named column gone or retyped) refuses with CONTRACT_STALE, because the
  SQL cannot run. Neutral (row count moved) proceeds with a caveat on every
  result. Step 3 implements it.
- The fingerprint is a CACHE KEY, not a truth claim. The industrial pattern
  (Great Expectations checkpoints, dbt tests) is to re-run the cheap
  invariants -- is the key still unique, do the measure columns still exist
  -- and skip that work only on a fingerprint hit. Comparing a stored row
  count answers "did something change" and never "is the agreement still
  true".
- D2 locked, and split. Grain is GUESSED mechanically from the key candidate,
  in the table's own column names ("one row = one (order_id, order_item_id)"),
  and marked unresolved. A measure definition is left BLANK and marked
  unresolved, because no derivation of "net of tax, excludes cancelled"
  exists. A guessed grain that reaches for business words is worse than a
  blank one: people nod along to a plausible grain in a way they never did
  to a guessed header row.
- unresolved holds FIELD PATHS, not field names: "grain",
  "measures[price].definition". Definitions are missing per-measure.
- Blank values are legal only while declared. A contract whose grain is empty
  and which does not list "grain" in unresolved will not construct. This
  closes the hole Phase 3 left: an IngestSpec could be confirmed by
  hand-deleting the unresolved entry, because the ban lived in a docstring.
- Every refusal carries a stable reason code on its last line
  (reason: NO_CONTRACT), after RFC 7807 and Google's ErrorInfo. Tests and the
  Phase 13 eval assert on the code; the prose stays free to be rewritten.
  Refusal.__post_init__ rejects a next_call without parentheses -- an
  instruction the agent cannot execute is what F1 is.
- A contract with bound_to=None is valid on purpose. Reading one back from
  storage must not require the table to be loaded.
- D3 locked: SCD2. D4 locked as a gate-only stub, with the post-contract
  return still to be decided at Step 7 -- a state report, or one real
  analysis. A stub that refuses twice is the apology loop the Done-When is
  meant to catch.

- Drift is classified against the columns the CONTRACT NAMES, not against the
  table. Dropping a column no contract mentions is ADDITIVE, not destructive.
  A gate that fires when it does not have to teaches the reader to skim past
  it, which is F1's mechanism rather than merely bad manners.
- ADDITIVE also covers an unnamed column being dropped and a column reorder.
  Neither is additive literally; both are non-breaking for a contract that
  refers to columns by name, and a fifth class would mean branching on
  something no caller acts on differently. The name is inherited from
  schema-registry vocabulary and is kept for that reason alone.
- A reorder is non-breaking at the contract layer and breaking at the ingest
  layer, because IngestSpec carries `names` positionally. Same event, two
  correct and opposite answers. Both are tested in their own files.
- caveat() lost a fact when two kinds of drift happened at once: a table that
  had dropped an unnamed column AND gained 30 rows reported only the column.
  The classes are exclusive, the sentences must not be. Found by walking one
  table through all four classes; every unit test changed one thing at a time
  and all of them passed.
- verify_key checks a key a person STATED instead of searching for one, and it
  is the more important half. On a 420-row invoices table, search returned
  ['amount'] -- a DOUBLE that happens not to repeat -- and missed
  invoice_ref + line entirely, because `line` is numeric with 21 distinct
  values and is not identifier-named. Verification found it in one query.
  Phase 3's rule at another layer: the answer comes back the way the question
  went out.
- A failing key reports HOW MANY rows repeat, not just that it is not unique.
  400 duplicates across 20 values says the grain is wrong; two duplicates says
  the data is dirty. The refusal offers both repairs.
- Known inconsistency, scheduled for Step 7: contract/evidence.py raises
  ContractRefused with a plain BLOCKED string and no reason code, because it
  was written before refusals.py existed. Every refusal path gets audited when
  server.py wires the tools and test_tool_docs.py pins them.

- A proposal may restate what the data says and may never state what only a
  person can. Grain is DERIVED from the key in the table's own column names
  ("one row = one (order_id, order_item_id)") and still marked unresolved.
  A grain in business words ("one order line item") is invented, and it is
  worse than a blank because people nod along to it.
- The analysis window is reported, never proposed. A date column's span is a
  fact and the window is a different question: on olist,
  shipping_limit_date runs to 2020-04-09, past the end of the order data, so
  a window taken from the span would look defensible and include a tail
  nobody wants.
- One temporal column is taken silently; more than one is offered and marked
  unresolved. Which date a trend runs on changes the numbers.
- Known exclusions are never invented. The test fixture carries a status
  column with a literal 'cancelled' so that a future version inventing one
  fails a test rather than passing quietly.
- Key candidates are ranked by ROLE before position. Evidence returns unique
  singles before pairs in column order, so taking the first produced
  "one row = one order_date" on a fixture where order_date happened to hold
  300 distinct values in 300 rows -- the same coincidental uniqueness the
  200k probe found, arriving through the front door. Candidates whose columns
  all read as identifiers rank first, and the losers are listed rather than
  dropped.
- Repeating identifiers ARE dimensions. Excluding every identifier left one
  groupable column on a seven-column table, which is not a description anyone
  would recognise -- seller_id is a foreign key and grouping by it is the
  normal thing to do. Columns that are IN the key stay out: grouping by the
  key returns the table.
- DatasetContract.to_text() no longer renders `questions`. The contract body
  and the proposal render both had a list, so a first-turn proposal printed
  all four questions twice in one tool result -- Phase 3 Step 8's duplicated
  assumptions, exactly. Questions belong to the conversation, and the
  conversation puts them at the bottom, where an answer gets given.
- A stated primary_key is verified before it reaches the contract, so a key
  that does not hold is refused at proposal time rather than at the gate
  three steps later.

- Contracts are stored SCD2 in _agent_contracts: a new confirmation writes a
  new version and closes the previous one with valid_to, rather than
  overwriting it. Exactly one row per dataset is is_current. Locked decision
  18 wants the ledger inside every report, and an in-place edit makes "what
  did we agree, and when did it change" unanswerable.
- Confirming an unchanged contract is idempotent -- it returns the version in
  force and writes nothing. Versions are for changes; a history half made of
  re-confirmations is one nobody reads twice.
- The database is authoritative and docs/contracts/<name>.yaml is an export:
  regenerated on every confirm, never read back, carrying a DO-NOT-EDIT
  header. Definitions belong in version control because that is what makes a
  number in a report reviewable in a pull request -- the semantic-layer
  convention (dbt MetricFlow, Cube, LookML).
- A contract may EXIST unbound so it can be read back on a machine that never
  loaded the table; it may not be CONFIRMED unbound, because Step 3 would then
  have nothing to compare the table against.
- store.py creates _agent_contracts lazily rather than in db.connect(). The
  ingest layer should not have to know contracts exist. Cost is one CREATE
  TABLE IF NOT EXISTS per call, answered from DuckDB's catalog.
- changed_fields() and history_text() were written after reading a rendered
  history and finding it useless: two versions differing only in a measure
  definition printed identical lines apart from timestamps, because line()
  showed grain and fingerprint and neither had moved. The differences are
  reported as field paths, the same paths unresolved uses.
- PyYAML is imported inside write_export, not at module top, so nothing on the
  ingest path acquires the dependency because the contract layer wanted it.
- The confirm/supersede pair runs inside an explicit BEGIN/COMMIT with a
  rollback on failure. Without it a crash between the UPDATE and the INSERT
  leaves a dataset with no current contract at all, which reads as "never
  agreed" rather than as "half written".

- require_contract runs four checks in order -- loaded, contract in force,
  structure not broken, key still holding -- and the last two are EXECUTED
  against the live table rather than compared against stored values. A stored
  hash says something changed; only running the count says the agreement
  still holds.
- The fingerprint is used in exactly one place: when structure AND row count
  both match, the key re-check is skipped. Everywhere else it is inert. That
  is what "cache key, not a truth claim" means in code.
- Demonstrated: ten duplicated rows produce identical columns, identical
  types and no drift of any kind, and the primary key stops holding. Every
  structural check passes it. Only verify_key catches it, and without that
  check every later group-by double-counts with nothing saying so.
- A passed gate carries caveats, not just permission: the drift caveat, the
  contract's own caveats, and one line per known exclusion with its row
  count. A total computed with 100 rows deliberately removed is a different
  number wearing the same name.
- dataset_states filters underscore-prefixed tables itself as well as relying
  on db.user_tables. _agent_contracts did not exist when that filter was
  written, so whether it is excluded depends on whether it tests one known
  name or the convention. Listing the contract log as a dataset with no
  contract would be absurd in the one tool whose job is saying where you are.
- get_workflow_state lists every dataset with its load time, its stage and the
  exact next call. There is no fix for F13 -- the server cannot see chat
  boundaries -- so the mitigation is that a leftover reads as
  "Loaded 3 hour(s) ago" rather than as something fresh.
- A table with no load record (a view, something hand-made) is still listed,
  marked as not created by a loader. Hiding it would make get_workflow_state
  lie about the contents of the workspace.
- state.py lives at src/analytics_agent/state.py, not under contract/. The
  gate belongs to the workflow, not to the contract, and Section 10 puts it
  there.

- tests/test_contract_tool_docs.py distinguishes three states, not two: none
  of the four contract tools present is a SKIP (not wired yet), SOME present
  is a FAIL naming what is missing (wired, and something was lost), all four
  present runs everything. A blanket skip would hide the middle case, which
  is the silent damage the guard exists to catch.
- The first version skipped only when server.py was ABSENT, so on a real repo
  it failed 25 times instead of skipping. A step guide that leaves the suite
  red between its own parts teaches you to ignore a red suite.

- DEFAULT_AGG stays "sum" for every measure, including prices. The live run
  pushed back on it correctly -- summing a unit price is meaningless -- and
  the question attached to each measure asks about the aggregation for exactly
  that reason. What protects the contract is that the definition is
  unresolved, so a wrong agg cannot be STORED without a person answering: the
  bad default is visible and blocked, not quiet. Choosing 'mean' for anything
  named price is the name-heuristic trap that nearly lost order_item_id in
  Step 1. A dumb default plus a mandatory question beats a clever default that
  is confidently wrong.
- Live run, Step 7b: gate refused with NO_CONTRACT, agent called
  propose_dataset_contract unprompted, read the PROVISIONAL draft back
  accurately, and said it would re-propose with the answers rather than edit
  the JSON. Two Done-When behaviours observed before Step 8 formally tests
  them.
- server.py was merged into, not retyped. Three anchors -- the module
  docstring, the import line, the point before main() -- and then a line-level
  diff against the original: exactly one line differs (the docstring line that
  was deliberately rewritten), no function lost, four added. Reconstructing a
  548-line file from a copy inside a step guide would have had no such check.
- tests/test_contract_tool_docs.py distinguishes three states rather than two:
  none of the four tools present is a SKIP (the block has not been added),
  some present is a FAIL naming what is missing (the block was added and
  something was lost), all present runs everything. A blanket skip would hide
  the middle case, which is the failure the file exists to catch.
- Step 7a claimed the guard would report 40 skipped before wiring. It reported
  25 failed, because the skip only fired when server.py was ABSENT and the
  file exists. A step guide that leaves the suite red between its own parts
  teaches you to ignore a red suite, which is worse than having none.

- CORRECTION to the Step 7b entry: a wrong aggregation CAN be stored. Only
  measures[x].definition is unresolved; agg is not. A person can answer every
  definition, never mention aggregation, confirm, and store unit_price with
  agg="sum". The question asks about it; nothing enforces it. Two independent
  live runs flagged the sum default, the second describing it as "the kind of
  thing that gets confirmed without being read". The recommended fix is to add
  measures[x].agg to unresolved -- smallest change, no new question, and it
  puts the block where the prose already points. Deferred to a Step 9 rather
  than slipped into the close of Phase 4.
- Live run 2 confirmed three behaviours beyond the clause: the evidence notes
  (measure exclusion from key probing, minimality pruning) were read back
  accurately by something that had never seen the code; the agent set
  expectations that run_analysis returns no number, from the docstring
  sentence pinned by test_run_analysis_is_honest_about_phase_8; and it tied a
  null in `region` to known_exclusions unprompted.
- Twice now, a contract-layer test has asserted on wording owned by
  util/db.py: Step 6 hard-coded a `loaded_at` column name, and the Phase 4
  acceptance script counted the literal word "Loaded" in a report. Both passed
  locally and failed on the real repository. The rule: assert that another
  module's output REACHES yours, never what it says. age_phrase()'s wording is
  util/db.py's business.
- The agent does not see all nineteen tools at once -- it calls tool_search
  and matches on descriptions. A docstring's first line therefore does double
  duty: it instructs, and it is what a search has to match. A tool that cannot
  be found fails before its gate ever runs, and the failure looks like a gate
  problem. Every tool Phase 5 adds needs a first line that reads as a search
  target as well as an instruction.
- Live run 3: the agent declined to call confirm_dataset_contract on a
  PROVISIONAL draft WITHOUT being refused -- "nothing to confirm, the draft is
  PROVISIONAL and would be refused". The docstring said what would happen and
  it was believed. A refusal never issued is better than one recovered from,
  and it is the one behaviour test_phase4.py cannot assert.
- The live runs went to load_csv directly rather than propose_ingest_spec,
  correctly: clean_sales.csv is a plain one-header table and load_csv's
  docstring says to use it directly when the shape is known. Phase 3's
  two-step is therefore NOT exercised by the Phase 4 live run; multiheader.csv
  is the fixture that forces it.
- GAP for Phase 5: a column can be left out of `measures`, and nothing
  records why. known_exclusions covers ROWS only (rule, reason, row_count).
  Omitting a column is the same kind of decision as excluding rows and is
  currently as silent as the load-time drop it was chosen to avoid --
  "deliberately excluded" and "nobody got round to it" are indistinguishable
  in a stored contract. Fix is a scope on Exclusion (row|column) or a separate
  excluded_columns list. Not patched in Phase 4.
- Live run 4 assessed load_csv as capable of silently mislabelling columns if
  a short `names` list were passed. Not true on this repo: load_csv counts the
  file's columns first and refuses a mismatch, naming both counts -- the Phase
  2 Step 5 guard added for exactly that trap. The agent described raw DuckDB
  behaviour rather than the loader's. Its conclusion (there is no column
  selection parameter, do not invent one) was right anyway.
- Rejected suggestion: that the evidence block distinguish columns present in
  the table from columns admitted as measures. Evidence describes the TABLE,
  deliberately; folding contract state into it collapses the separation Step 1
  was built on. If the output reads confusingly, the fix belongs in the
  contract's rendering.
- revenue in clean_sales.csv is derived -- units * unit_price, verified on two
  rows. The contract has no derived_measures concept, so excluding revenue
  makes revenue-by-region a computed expression. Phase 8's problem, worth
  recording now.
- Phase 4 acceptance adds a check the Done-When does not name: every refusal's
  NEXT STEP must name a tool that is actually registered in server.py. A
  refusal instructing the agent to call something that does not exist looks
  well-formed, passes every wording check, and is unrecoverable. The refusal
  strings and the tool registry are written in different files by different
  steps, so being careful in each separately still leaves you wrong.
- Clause 3 is asserted in two halves: the script checks everything the
  recovery DEPENDS on -- reason code, a call with arguments, that call
  existing -- and the live run checks whether the model acts on it. If the
  machinery passes and the agent still loops, the problem is wording; if the
  machinery fails, the wording never had a chance.
- The SCD2 span assertion is that v1.valid_to == v2.valid_from exactly, not
  merely that history was kept. Contiguous windows are what make "which
  definition produced this number" answerable for a number computed last
  Tuesday.

- CORRECTION to the Step 7b entry: a wrong aggregation CAN be stored. Only
  measures[x].definition is unresolved; agg is not. A person can answer every
  definition, never mention aggregation, confirm, and store unit_price with
  agg="sum". The question asks about it; nothing enforces it. Two independent
  live runs flagged the sum default, the second describing it as "the kind of
  thing that gets confirmed without being read". The recommended fix is to add
  measures[x].agg to unresolved -- smallest change, no new question, and it
  puts the block where the prose already points. Deferred to a Step 9 rather
  than slipped into the close of Phase 4.
- Live run 2 confirmed three behaviours beyond the clause: the evidence notes
  (measure exclusion from key probing, minimality pruning) were read back
  accurately by something that had never seen the code; the agent set
  expectations that run_analysis returns no number, from the docstring
  sentence pinned by test_run_analysis_is_honest_about_phase_8; and it tied a
  null in `region` to known_exclusions unprompted.
- Twice now, a contract-layer test has asserted on wording owned by
  util/db.py: Step 6 hard-coded a `loaded_at` column name, and the Phase 4
  acceptance script counted the literal word "Loaded" in a report. Both passed
  locally and failed on the real repository. The rule: assert that another
  module's output REACHES yours, never what it says. age_phrase()'s wording is
  util/db.py's business.
- The agent does not see all nineteen tools at once -- it calls tool_search
  and matches on descriptions. A docstring's first line therefore does double
  duty: it instructs, and it is what a search has to match. A tool that cannot
  be found fails before its gate ever runs, and the failure looks like a gate
  problem. Every tool Phase 5 adds needs a first line that reads as a search
  target as well as an instruction.
- Live run 3: the agent declined to call confirm_dataset_contract on a
  PROVISIONAL draft WITHOUT being refused -- "nothing to confirm, the draft is
  PROVISIONAL and would be refused". The docstring said what would happen and
  it was believed. A refusal never issued is better than one recovered from,
  and it is the one behaviour test_phase4.py cannot assert.
- The live runs went to load_csv directly rather than propose_ingest_spec,
  correctly: clean_sales.csv is a plain one-header table and load_csv's
  docstring says to use it directly when the shape is known. Phase 3's
  two-step is therefore NOT exercised by the Phase 4 live run; multiheader.csv
  is the fixture that forces it.
- GAP for Phase 5: a column can be left out of `measures`, and nothing
  records why. known_exclusions covers ROWS only (rule, reason, row_count).
  Omitting a column is the same kind of decision as excluding rows and is
  currently as silent as the load-time drop it was chosen to avoid --
  "deliberately excluded" and "nobody got round to it" are indistinguishable
  in a stored contract. Fix is a scope on Exclusion (row|column) or a separate
  excluded_columns list. Not patched in Phase 4.
- Live run 4 assessed load_csv as capable of silently mislabelling columns if
  a short `names` list were passed. Not true on this repo: load_csv counts the
  file's columns first and refuses a mismatch, naming both counts -- the Phase
  2 Step 5 guard added for exactly that trap. The agent described raw DuckDB
  behaviour rather than the loader's. Its conclusion (there is no column
  selection parameter, do not invent one) was right anyway.
- Rejected suggestion: that the evidence block distinguish columns present in
  the table from columns admitted as measures. Evidence describes the TABLE,
  deliberately; folding contract state into it collapses the separation Step 1
  was built on. If the output reads confusingly, the fix belongs in the
  contract's rendering.
- revenue in clean_sales.csv is derived -- units * unit_price, verified on two
  rows. The contract has no derived_measures concept, so excluding revenue
  makes revenue-by-region a computed expression. Phase 8's problem, worth
  recording now.
- Phase 4 acceptance adds a check the Done-When does not name: every refusal's
  NEXT STEP must name a tool that is actually registered in server.py. A
  refusal instructing the agent to call something that does not exist looks
  well-formed, passes every wording check, and is unrecoverable. The refusal
  strings and the tool registry are written in different files by different
  steps, so being careful in each separately still leaves you wrong.
- Clause 3 is asserted in two halves: the script checks everything the
  recovery DEPENDS on -- reason code, a call with arguments, that call
  existing -- and the live run checks whether the model acts on it. If the
  machinery passes and the agent still loops, the problem is wording; if the
  machinery fails, the wording never had a chance.
- The SCD2 span assertion is that v1.valid_to == v2.valid_from exactly, not
  merely that history was kept. Contiguous windows are what make "which
  definition produced this number" answerable for a number computed last
  Tuesday.

- A measure's aggregation has NO DEFAULT. Every production semantic layer
  requires it -- LookML `type:`, Cube `type`, dbt MetricFlow `agg` -- and none
  of them guesses, because the guess that gets guessed is sum and summing a
  price, a rate or a balance is wrong in a way nothing downstream can detect.
  A NULL propagates; a wrong total does not.
- This supersedes the Step 7b entry claiming a wrong agg could not be stored.
  It could: only measures[x].definition was unresolved. A person could answer
  every definition, never mention aggregation, and confirm unit_price with
  agg="sum". Two independent live runs flagged it, the second describing it as
  "the plausible-looking default is the kind of thing that gets confirmed
  without being read".
- agg="none" is a STATEMENT that a column must not be combined, not an
  absence. It is the right answer for a unit price -- not mean, which averages
  across orders of different sizes and is its own quiet mistake. Only a stated
  value confirms; None does not.
- One question settles both measures[x].definition and measures[x].agg. They
  are the same question about the same column, and the question now lists the
  allowed aggregations so an answer needs no guessing at the vocabulary.
- Removing a default touched seven files. That is the cost of having had one,
  and the reason to check what the reference implementations do BEFORE
  reasoning from first principles: I offered three options and recommended the
  middle one, and the industry answer was a fourth that none of them was.

- A measure's aggregation has NO DEFAULT. Every production semantic layer
  requires it -- LookML `type:`, Cube `type`, dbt MetricFlow `agg` -- and none
  of them guesses, because the guess that gets guessed is sum and summing a
  price, a rate or a balance is wrong in a way nothing downstream can detect.
  A NULL propagates; a wrong total does not.
- This supersedes the Step 7b entry claiming a wrong agg could not be stored.
  It could: only measures[x].definition was unresolved. A person could answer
  every definition, never mention aggregation, and confirm unit_price with
  agg="sum". Two independent live runs flagged it, the second describing it as
  "the plausible-looking default is the kind of thing that gets confirmed
  without being read".
- agg="none" is a STATEMENT that a column must not be combined, not an
  absence. It is the right answer for a unit price -- not mean, which averages
  across orders of different sizes and is its own quiet mistake. Only a stated
  value confirms; None does not.
- One question settles both measures[x].definition and measures[x].agg. They
  are the same question about the same column, and the question now lists the
  allowed aggregations so an answer needs no guessing at the vocabulary.
- Removing a default touched seven files. That is the cost of having had one,
  and the reason to check what the reference implementations do BEFORE
  reasoning from first principles: I offered three options and recommended the
  middle one, and the industry answer was a fourth that none of them was.

## Phase 5, Step 1 — util/results.py

- P5-D4 answered. Result files are CSV, under workspace/<id>/results/, named
  <label>_<YYYYMMDD-HHMMSS>.csv with a counter on collision, never overwritten,
  never auto-deleted. reset_workspace is the only thing that removes them, and
  that is only true because the directory is INSIDE the workspace directory --
  verified with a canary file before the code was written, not assumed.
- A path is never returned on its own. write_result returns a Result, and there
  is deliberately no accessor that yields just the path as a string: the one
  that exists is the one that gets used. F7 is the agent reporting on data it
  never opened, and it leaves no trace in the transcript.
- results.py slices the preview to 20 rows and 12 columns BEFORE calling
  format_table, which caps at 50 and 50. If the cap did the truncating, the cap
  would decide what the model sees and nothing would say a cap had happened.
  Truncating first also means format_table's behaviour at its own limits stops
  mattering to this phase. Asserted directly: PREVIEW_ROWS < MAX_ROWS.
- A page past the end of a file is NOT a refusal. It carries no reason code and
  names the page that does exist. Asking for row 500 of a 30-row file is a wrong
  guess, not a broken call, and an agent handed a BLOCKED there starts
  apologising -- the Phase 4 D4 reasoning, one layer down.
- start=0 IS refused rather than nudged to 1. An off-by-one that silently
  becomes row 1 returns a page that does not begin where it was asked to and
  says nothing about it.
- Two Reason members added: RESULT_NOT_FOUND, RESULT_OUT_OF_SCOPE. Additive, so
  every Phase 4 test still passes. refusals.py lives under contract/ for
  historical reasons and is now imported by util/ -- if a later phase wants it
  under util/, that is a move, not a rewrite.
- read_result_file is a function in Step 1 and a registered MCP tool in Step 6.
  The refusals here name it, and the Phase 5 acceptance test asserts every call
  a refusal names is registered -- so forgetting Step 6 fails loudly at Step 9.

## Phase 5, Step 2 — profile/table_profile.py

- P5-D1 answered: profiling depends on evidence.column_stats, NOT on
  evidence.gather. gather() also runs the key search (up to 200 pair probes)
  and appends contract-flavoured notes that have no business in a profile.
  column_stats is public, already batches four aggregates per column into one
  SELECT, and is the whole of what profiling needs. The arrow points
  profile -> evidence and never back; Phase 4 gains no dependency.
- A null count is not a missing-data count. gaps_and_dupes.csv holds 'N/A' in a
  column with zero nulls, so "0% null" is true and misleading. Blanks and
  standard tokens are counted separately, reported beside the nulls, and never
  rewritten.
- The missing-value vocabulary is the pandas 3.0.2 / pyarrow 25.0.1
  INTERSECTION, upper-cased, minus the empty string. Verified by running both.
  Where they disagree (None, <NA>) both are excluded -- that is the edge of
  consensus, and 'None' can be a real payment type.
- My own first list included unknown, missing, none, nil, -, --, ?. None of
  those is in any reference implementation, and including them reported a
  six-row fixture as 83% missing when 67% was defensible. A tool built to stop
  confidently wrong numbers produced one on its first run. Check the reference
  implementations BEFORE reasoning from first principles -- the same lesson as
  Phase 4 Step 9, learned again.
- The failure modes are asymmetric and that is the argument. Over-detection
  puts a wrong number in a headline; under-detection leaves the value in a
  frequency table where a person rules on it. Tune toward the recoverable one.
- Ownership follows Frictionless Table Schema: missingValues is a DECLARED
  property, default [''], and [] disables conversion entirely rather than
  meaning "use the default". So missing_values is a parameter here, [] really
  does switch detection off, and Step 8 puts it on the contract so Phase 6 and
  Phase 8 read one declared list instead of re-deriving one each.
- Matching is case-insensitive. One deliberate widening: pandas ships 'NA',
  'n/a' and 'nan' as separate entries, implying exact matching, so 'Null' slips
  through it. This widens case and never vocabulary.
- Duplicate rows use SELECT DISTINCT *, the THIRD null rule in this codebase.
  count(DISTINCT c) drops nulls; count(DISTINCT (a,b)) does not; DISTINCT *
  does not either, and two rows identical INCLUDING their nulls collapse to
  one. Verified on 1.5.5: five rows with one exact NULL-bearing duplicate
  return four. Here that is the behaviour we want, so it is used deliberately
  and said out loud.
- The try/except around the duplicate count has never fired. LIST, MAP and
  UNION all survive DISTINCT * on 1.5.5 -- I could not find a type that breaks
  it. It stays because one uncomputable number should not cost the other
  thirty, and the test that covers it induces the failure rather than
  pretending a type does.
- quantile_cont INTERPOLATES; it does not return an observed value.
  quantile_cont over [2829.54, 5841.66] at 0.25 gives 3582.57, not 2829.54 --
  quantile_disc gives the latter. cont matches numpy's and pandas' default and
  is the right choice for fences, but it means q1 and q3 are computed positions
  rather than rows that exist. Step 3's IQR fences inherit that, and the effect
  is largest on columns with few distinct values.
- All-null and single-row columns return None for mean/stddev/quantiles, not
  zero. A zero would be a number nobody computed sitting in a table looking
  exactly like a real one.
- HEADERS puts the missing-data story in the first twelve columns because the
  envelope previews twelve inline. The numeric summary is in the file, behind
  it. That ordering is a decision, not an accident of how it was typed.

## Phase 5, Step 2 — profile/table_profile.py

- P5-D1 answered: profiling depends on evidence.column_stats, NOT on
  evidence.gather. gather() also runs the key search (up to 200 pair probes)
  and appends contract-flavoured notes that have no business in a profile.
  column_stats is public, already batches four aggregates per column into one
  SELECT, and is the whole of what profiling needs. The arrow points
  profile -> evidence and never back; Phase 4 gains no dependency.
- A null count is not a missing-data count. gaps_and_dupes.csv holds 'N/A' in a
  column with zero nulls, so "0% null" is true and misleading. Blanks and
  standard tokens are counted separately, reported beside the nulls, and never
  rewritten.
- The missing-value vocabulary is the pandas 3.0.2 / pyarrow 25.0.1
  INTERSECTION, upper-cased, minus the empty string. Verified by running both.
  Where they disagree (None, <NA>) both are excluded -- that is the edge of
  consensus, and 'None' can be a real payment type.
- My own first list included unknown, missing, none, nil, -, --, ?. None of
  those is in any reference implementation, and including them reported a
  six-row fixture as 83% missing when 67% was defensible. A tool built to stop
  confidently wrong numbers produced one on its first run. Check the reference
  implementations BEFORE reasoning from first principles -- the same lesson as
  Phase 4 Step 9, learned again.
- The failure modes are asymmetric and that is the argument. Over-detection
  puts a wrong number in a headline; under-detection leaves the value in a
  frequency table where a person rules on it. Tune toward the recoverable one.
- Ownership follows Frictionless Table Schema: missingValues is a DECLARED
  property, default [''], and [] disables conversion entirely rather than
  meaning "use the default". So missing_values is a parameter here, [] really
  does switch detection off, and Step 8 puts it on the contract so Phase 6 and
  Phase 8 read one declared list instead of re-deriving one each.
- Matching is case-insensitive. One deliberate widening: pandas ships 'NA',
  'n/a' and 'nan' as separate entries, implying exact matching, so 'Null' slips
  through it. This widens case and never vocabulary.
- Duplicate rows use SELECT DISTINCT *, the THIRD null rule in this codebase.
  count(DISTINCT c) drops nulls; count(DISTINCT (a,b)) does not; DISTINCT *
  does not either, and two rows identical INCLUDING their nulls collapse to
  one. Verified on 1.5.5: five rows with one exact NULL-bearing duplicate
  return four. Here that is the behaviour we want, so it is used deliberately
  and said out loud.
- The try/except around the duplicate count has never fired. LIST, MAP and
  UNION all survive DISTINCT * on 1.5.5 -- I could not find a type that breaks
  it. It stays because one uncomputable number should not cost the other
  thirty, and the test that covers it induces the failure rather than
  pretending a type does.
- quantile_cont INTERPOLATES; it does not return an observed value.
  quantile_cont over [2829.54, 5841.66] at 0.25 gives 3582.57, not 2829.54 --
  quantile_disc gives the latter. cont matches numpy's and pandas' default and
  is the right choice for fences, but it means q1 and q3 are computed positions
  rather than rows that exist. Step 3's IQR fences inherit that, and the effect
  is largest on columns with few distinct values.
- All-null and single-row columns return None for mean/stddev/quantiles, not
  zero. A zero would be a number nobody computed sitting in a table looking
  exactly like a real one.
- HEADERS puts the missing-data story in the first twelve columns because the
  envelope previews twelve inline. The numeric summary is in the file, behind
  it. That ordering is a decision, not an accident of how it was typed.

## Phase 5, Step 3 — type readings and outliers

- TRY_CAST CONVERTS rather than refusing where it can. TRY_CAST('4.5' AS
  BIGINT) is 5; TRY_CAST('2024-01-01 10:30:00' AS DATE) is 2024-01-01. Both
  succeed and both lose information, so an unguarded test reports a decimal
  column as integer and a timestamp column as date -- and Phase 6 would then
  propose a lossy conversion off a finding that looked solid.
- The guard is one shape for both: a narrower type is claimed only when the
  wider one round-trips it. BIGINT must equal its DOUBLE; DATE must equal its
  TIMESTAMP. '007', ' 7 ' and '1e3' still read as integers, '4.5' does not; a
  midnight timestamp still reads as a date, 10:30 does not.
- CAST_CANDIDATES is ordered narrowest first and ties go to the earlier entry.
  A column of 1s and 0s parses as both BIGINT and BOOLEAN; BIGINT wins because
  it assumes less about intent.
- The cast denominator excludes nulls, blanks and the Step 2 missing tokens.
  'N/A' is already reported as missing; counting it again as a parse failure
  describes one problem twice and understates the ratio.
- pandas, DuckDB's sniffer and Frictionless infer types ALL-OR-NOTHING because
  they must choose a storage type. They are answering a different question. A
  profile reports, and the interesting case is the one they stay silent about
  -- 95% numeric with one piece of junk. So their rule does not transfer.
- TYPE_MISMATCH_SHARE = 0.9 is a DISPLAY threshold governing the summary only.
  Every text column's ratio is computed and lands in the table regardless. Same
  status as MOSTLY_MISSING. "Every value parses" is worded differently from
  "most values parse" because only the first is a claim anyone should act on.
- OUTLIER_K = 1.5 is Tukey's constant and matplotlib 3.10.8's
  boxplot.whiskers default, verified by reading rcParams rather than recalled.
- A ZERO IQR SUPPRESSES THE COUNT. On a column that is 95% one value the
  quartiles coincide, the fences collapse to a point, and every other row is
  outside them: measured, 5 of 100 flagged, and the five were the values 1, 2
  and 3. Tukey says that and nobody should act on it. The reason is reported so
  a silence cannot read as a clean bill.
- A suppressed count writes None into the table, never 0. A zero reads as
  "checked, none found"; nothing was checked.
- The summary names outliers only for columns whose role is measure. A rating
  of 1-5 with one 5 is not an outlier story, and evidence already classifies
  low-cardinality numerics as dimensions.
- The fences reuse q1 and q3 from Step 2, so the whole outlier analysis costs
  one extra scan for the table rather than one per column.

## Phase 5, Step 4 — rendering and the wide-table rule

- EVERY PROFILE WRITES A FILE, including a four-column one that would read
  fine inline. Skipping the file for small tables was tempting and is wrong:
  it makes the agent reason about which case it is in, and an agent that has
  learned "a profile comes with a path" produces a path when one is missing
  rather than concluding the table was small. That is F7 through the front
  door. The uniform contract costs disk; reset_workspace answers the disk.
- What changes with width is the BODY, not the envelope. At or below 20
  columns the render prints the per-column sentences; above it, the profile
  table's own 20x12 preview. Sixty prose sentences is not a readable answer
  and neither is a 24-column table in a chat window.
- INLINE_COLUMN_LIMIT is results.PREVIEW_ROWS rather than a separate constant.
  A higher threshold would promise a sentence per column while the preview had
  already truncated the rows those sentences describe. A test asserts the two
  stay equal so a later change to one fails loudly.
- The invariant is asserted against the OUTPUT, not against which function
  produced it: wherever the path appears, the shape, the findings and the
  literal next call appear with it. The narrow form composes from Result's
  parts rather than calling to_text() wholesale, and this is what stops that
  being a hole. Both forms go through the same assertion helper.
- The narrow form does NOT print the table as well as the sentences. Two
  renderings of the same four columns in one result is the Phase 3 Step 8
  shape: a reader cannot tell whether they differ, so they read both and trust
  neither.
- Notes come last in both forms. Whatever sits at the bottom is read last and
  remembered, and caveats belong below the numbers they qualify.
- No wide_table.csv fixture was added, against my own step map. Adding one
  means editing tests/fixtures/make_fixtures.py, which I have not read, and
  guessing at a file's structure produced two corrections in this phase
  already. The tests build wide tables in DuckDB. Step 9 can add the CSV if
  the acceptance test wants one on disk.

## Phase 5, Step 5 — profile_column

- This is where the Step 2 promise is kept. 'unknown', 'none', '-' and '?' are
  excluded from the missing-value vocabulary and appear in the column's
  frequency table instead, with a note telling the reader to judge that list.
  The note does NOT name candidates -- naming them is the judgement list again,
  one layer down.
- profile_column WRITES NOTHING, which is not an inconsistency with Step 4's
  "every table profile writes". A table profile is unbounded in the dimension
  that matters (one row per column, and tables have sixty). A column profile is
  bounded by construction: ten values, ten bins, a few counts. The one
  truncation ends in profile_column(..., top_n=N), which is an executable next
  step rather than a dead end -- and Step 1's rule was never "always write a
  file", it was "never leave a truncation with no way to reach the rest".
- The binning is DuckDB's: equi_width_bins(lo, hi, n, true) for rounded
  boundaries, histogram(col, bins) to fill them. Verified on 1.5.5 including
  the crashes that did not happen -- a constant column returns a single bin,
  an all-null column returns NULL rather than an empty map, nulls are excluded
  from the counts. Hand-rolled bucketing would have got the empty cases wrong.
- Bin boundaries render with six significant figures, not .4g. .4g turns 10000
  into 1e+04, which is correct and unreadable in a table of prices. Found by
  reading the output; no test would have caught it, because the value was
  right.
- A unique column gets NO frequency table. Ten rows of count 1 is noise. It
  gets a sentence and the fixed-width finding instead, which is the useful
  thing to know about an identifier -- a nine-character code that later gets
  summed is a specific kind of wrong.
- Date coverage is bucketed to whole days. A TIMESTAMP column has a distinct
  value almost every row, and "3,412 distinct timestamps" answers nothing about
  whether a week is missing. Reports days present, days missing and the longest
  unbroken gap, and says explicitly that a closed weekend and a broken feed
  look identical from here. This is the cheap ancestor of Phase 9's
  calendar_coverage (F10).
- profile_column takes an optional table= so a caller holding a TableProfile
  does not pay for a second scan. When omitted it computes one rather than
  recomputing the column's numbers with different SQL, because two views of one
  column disagreeing inside one conversation is unrecoverable for a reader.
- One Reason member added: COLUMN_NOT_FOUND. Additive, so every earlier test
  still passes.

## Phase 5, Step 6a — profile/tools.py

- The tool layer is where ContractRefused stops being an exception and becomes
  text. A raised exception inside a FastMCP tool becomes a traceback, and a
  traceback is not an instruction: the agent reads it, learns nothing it can
  act on, and retries the same call. Same split as Phase 4's contract/tools.py,
  for the same reason.
- profile_column accepts workspace_id and does not use it. A signature that
  varies by tool is a thing the agent has to remember rather than
  pattern-match, and remembering is where it invents. A test pins the first
  three parameters of both profiling tools.
- profile_column computes the TableProfile once and hands it to the column
  profiler, so the nulls and missing counts it shows are identical to
  profile_dataset's. Two views of one column disagreeing inside a single
  conversation is unrecoverable: after that, neither number can be trusted.
- The round-trip test asserts that THE CALL PRINTED IN THE ENVELOPE opens, not
  merely that some path opens. Those drift apart when one of the two strings is
  built by hand, and the result is a well-formed envelope pointing at nothing --
  F7 with a clean conscience.
- missing_values is exposed on both profiling tools as a per-call override, and
  an empty list switches detection off. Frictionless' model reaching the tool
  surface: the vocabulary is a property of the data, so a feed that writes
  'unknown' for absence is handled by declaring it rather than by widening the
  default for every other source.
- Step 6 was split. The server.py registration and the docstring guard need two
  files I had not read, and writing a registration block against a remembered
  signature is how a loaded_at column name got hard-coded into a contract test
  twice.

## Phase 5, Step 6b — the profiling docstring guard

- tests/test_profile_tool_docs.py mirrors test_contract_tool_docs.py rather
  than inventing a structure: same ast parsing instead of importing, same
  helpers, same three-state fixture. A reader who knows the Phase 4 file knows
  this one, and copying a shape that works costs nothing.
- All three states were RUN against a mock server.py rather than reasoned
  about: none registered skips (19 passed, 20 skipped), two of three fails
  naming the third, all three passes (39 passed). A partial block surfaces as
  pytest ERRORS rather than failures because pytest.fail inside a fixture is a
  setup error -- the Phase 4 file behaves identically.
- The guard caught a real gap while being verified. The drafted profile_column
  docstring said "anything that MEANS absent" and never used the word
  "missing", which is the term every other output this phase uses. A docstring
  that switches vocabulary for one concept does not connect to anything the
  agent has already read. Fixed the docstring, not the assertion -- that is the
  point of pinning prose.
- profile_dataset's docstring must NOT contain the word "error". Outside a
  Tukey fence is not wrong, and a docstring promising to find problems invites
  the agent to present findings as faults.
- All three profiling tools are READ_ONLY. Writing a result file is not a
  change to the workspace: the file IS the answer. None of them should ever
  prompt the user for confirmation.

- Registering a tool is TWO edits: server.py and EXPECTED_TOOLS in
  tests/test_tool_docs.py. The closed-set guard fired on all three profiling
  tools, which is the guard working -- it fired the same way when Phase 4 added
  four. Step 6c did one edit and the suite caught the other.
- The reference was available and unread: test_contract_tool_docs.py names
  tests/test_tool_docs.py in its opening paragraph. Reading a file that points
  at another guard is not the same as reading the guard. Before adding a tool,
  grep the tests for the tool's own name AND for any closed set it has to join.

## Phase 5, Step 7a — the profile run record

- P5-D8 answered with a ROW, not a directory listing. Result filenames carry
  timestamps, so the profiled stage could have been inferred by globbing --
  and that answers a worse question. Inferring gives "a profile exists"; a
  record gives "profiled 40 minutes ago at 500 rows, and the table now has
  530", which is F13 arriving through a door Phase 4 did not cover. A filename
  does not know what the table looked like when it was written.
- APPEND-ONLY, no versioning, deliberately unlike contract/store.py. A contract
  supersedes its predecessor so SCD2 spans are needed; a profile supersedes
  nothing. Three runs in an hour are three facts, not three drafts, and the
  newest is interesting only because it is newest.
- drift_phrase says OLD, never WRONG. Every number in a 500-row profile was
  true when taken; beside a 530-row table it is out of date. An agent told
  "stale" re-profiles, an agent told "wrong" apologises.
- The record is written AFTER the file and carries the path that was actually
  produced. A record naming a file that does not exist is worse than no record:
  the workflow state would offer a read_result_file call that refuses, and the
  agent would have been told to make it. A test asserts the round trip.
- runs.is_bookkeeping() tests the _agent_ PREFIX rather than listing names.
  _agent_contracts was once listed as a dataset because state.py's filter
  predated it; a prefix test keeps working when a fifth table arrives, a list
  of three does not.
- render.py was split: write_profile returns the Result, render_written_profile
  formats it, render_profile does both and keeps its old signature. Step 7
  needs the path and the row count it was taken at, and reconstructing either
  by parsing the rendered text would mean parsing prose that exists to be read.
  All 24 Step 4 tests passed unchanged, which is the check that the split was
  behaviour-preserving.

## Phase 5, Step 7b — the profiling stage in the workflow state

- state.py needed NO change to hide _agent_profiles. _loadable_tables filters
  on the leading underscore rather than listing names, which is the belt and
  braces someone added after _agent_contracts was listed as a dataset. A third
  bookkeeping table cost nothing. Pinned by a test anyway, because a property
  that holds by accident of an earlier fix should not depend on nobody tidying
  the filter into a list of three names.
- A LAYERING EXCEPTION, made deliberately: state.py (Phase 4) imports
  profile.runs (Phase 5). describe_workflow_state is the orientation tool, its
  job is to report every stage, and a tool that reports every stage knows about
  every stage -- it already imports contract.store for the same reason. What
  would be wrong is contract/ or evidence.py importing profile: those describe
  one layer and should not know there is another above them.
- The profile lines go in the per-dataset DETAIL block, after Source and before
  the contract line. Loaded, profiled, contracted is the order the work happens
  in, and a reader should not have to reassemble it.
- The stage COLUMN is untouched. Adding "profiled" to it would match 8.2's
  example string and would widen every row of a scannable index to carry a
  state the detail block already gives in full. 8.2's string belongs to
  require_contract's refusal, which is a different function.
- Exactly one NEXT STEP per dataset, still. Phase 4 decided what the next call
  is; this adds a line, not a competing instruction. An agent handed two NEXT
  STEPs picks one at random, which is worse than a missing suggestion.
- A stale profile WITHDRAWS the offer of its own counts and offers a re-run
  instead. Counts taken against 200 rows are not what anyone wants when 230 are
  loaded, and leaving the read call there invites the agent to fetch them
  anyway.

## Phase 5, Step 9 — acceptance

- The acceptance test asserts FIVE clauses, not three. Clause 4: the
  read_result_file call printed in the envelope is parsed back out and executed,
  because a writer and a reader in the same package drift the moment either
  builds a path by hand, and the result is a well-formed envelope pointing at
  nothing. Clause 5: the workflow state reports profiled, then stale, then the
  re-run -- and never the word "wrong".
- Clause 2 is asserted against a table built in the script with known counts,
  not against a fixture. "Correctly reports" needs ground truth, and a fixture
  is only ground truth if somebody counted it.
- SKIPS ARE NOT PASSES, and the script says so in its own summary. An Olist
  table and big_synthetic each cover something a bare run does not.
- Step 8 (excluded_columns, P5-D7) was SKIPPED deliberately. Not in the
  Done-When, touches a closed phase, and the place a column exclusion is acted
  on is Phase 6, where cleaning already has an approval gate. It belongs at the
  front of Phase 6.

## Phase 6, Step 1 — the ground facts

- THE BUILD GUIDE'S THREE DUCKDB CLAIMS WERE MEASURED, not carried forward.
  Two are wrong as written. Pinned in tests/test_duckdb_cleaning_facts.py, 14
  tests, none of which tests our code -- each is a library claim the design
  leans on, left in the suite so a version bump says which one moved.
- P6-D3 ANSWERED: `* REPLACE (expr AS col)` rather than the guide's
  `* EXCLUDE (col), expr AS col`. EXCLUDE moves the rebuilt column to the END
  of the table. Column ORDER is identity to Binding.fingerprint, so under
  EXCLUDE every value-level conversion reads downstream as structural drift.
  EXCLUDE stays for the one action that really drops a column (P6-D8).
- P6-D2 HALF ANSWERED. A genuinely read-only handle exists, but only via
  ATTACH ... (READ_ONLY) from a separate connection, and only when nothing
  else holds the file -- one handle per file per process. connect(read_only=
  True) is a configuration conflict, not a downgrade; cursor() shares the
  database and writes freely; access_mode cannot be lowered on a running
  database. So the hard requirement is achievable IF util/db.connect opens per
  call. If it caches, the choice is to change the lifecycle or to weaken the
  requirement to a code-level guard -- and weakening it must be recorded as a
  weakening, not substituted quietly.
- P6-D4 OPEN, and it is the sharp one. The guide's example CAST aborts the
  whole CTAS on one accounting-style negative, '(45.00)'. TRY_CAST converts it
  to NULL: a value that existed before the clean is absent after it and
  nothing says so, which is a silent drop. The way out is that the SAME
  expression counts the unconvertible rows read-only at PROPOSAL time. A
  conversion action that cannot say how many values it will not convert is not
  a proposal. The threshold above which the action is withheld entirely is
  decided with the fixture in hand, not now.
- P6-D1 OPEN, and it is a collision between two LOCKED decisions: 17 says
  versioned tables, 13 says state is partitioned by dataset_name. sales_v2 is
  a table the contract, the profile run and the workflow state all know
  nothing about. Verified that a self-referencing CREATE OR REPLACE TABLE
  works on 1.5.5, so versioning is a CHOICE made for auditability rather than
  a necessity -- which means the auditability has to be delivered somewhere,
  and if not in the table name then in the ledger.
- P6-D7 OPEN. apply_cleaning_plan takes approved_action_ids AND NOTHING ELSE,
  so C003 has to resolve against a stored plan, and a stored plan can go stale
  between proposal and approval exactly as a profile does. F13, third
  appearance.
- P6-D2 ANSWERED, and the hard requirement stands exactly as the build guide
  writes it. ATTACH ... (READ_ONLY) from a separate connection is the only
  route, and it is available: db.connect() does not cache, and its docstring
  already forbids caching -- "a long-lived handle holds the lock and defeats
  the isolation", written in Phase 2 for F2, which is the same reason Phase 6
  needs it. Thirteen connects, thirteen closes in server.py.
- A CRUDE COUNT NEARLY BECAME A DEFECT REPORT. `grep -c "db.connect"` returned
  14 against 13 closes, and the fourteenth is a COMMENT at server.py:735. I
  had already written the leak up as a finding before checking which lines the
  count contained. Count the calls, not the lines that mention them.
- db.connect() CANNOT BE THE PROPOSAL PATH'S OPENER. It runs
  `con.execute(_SCHEMA)` -- CREATE TABLE IF NOT EXISTS _agent_datasets -- on
  every open, and a read-only attach refuses CREATE by STATEMENT TYPE, not by
  effect: IF NOT EXISTS does not save it even when the table exists. Measured
  and pinned. Step 3 adds connect_read_only() beside connect() in util/db.py.
- P6-D1 PROPOSED, and the codebase chose it rather than an argument.
  state.py's _loadable_tables filters on the LEADING UNDERSCORE, not a name
  list, so sales_v2 is not bookkeeping and shows in get_workflow_state as a
  dataset of its own. And dataset_states labels an unregistered table
  "No load record." / "unknown - not created by a loader" -- honest and wrong,
  since the cleaner created it deliberately. So both obvious readings of locked
  decision 17 damage the orientation tool: unregistered versions lie about
  their origin, registered ones put three rows in a table whose primary key is
  dataset_name while the contract and profile stay keyed to the base name.
  THE THIRD SHAPE: clean forward under the same name, and push the superseded
  copy behind the underscore as _history_<name>_v<N>. One dataset in the
  registry and the listing, contract and profile still attached, both tables on
  disk so the ledger's source/target version pair names something real, and the
  history invisible to the tool whose job is telling someone where they are.
  Self-referencing CREATE OR REPLACE was verified in Part 1; this splits it in
  two so the prior state survives.
  I HAD LEANED THE OTHER WAY -- visible _vN names -- and the underscore filter
  plus the "not created by a loader" label is what changed it. The decision was
  available to be read out of Phase 4's code the whole time.
- Side effect worth knowing: state.py:103 builds "loaded: {available}" into
  every DATASET_NOT_LOADED refusal from _loadable_tables. Visible _vN names
  would grow that line by one entry per cleaning action, in a message whose
  purpose is to be scannable.
- db.user_tables filters `table_name NOT LIKE '\_%' ESCAPE '\'` -- the
  underscore convention, in SQL, in db.py itself. So a _history_ table is
  filtered at BOTH layers and the shape above holds. Its docstring also says
  describe_dataset COMPARES user_tables against list_datasets to surface tables
  with no metadata row, which is a second reason not to leave visible versions
  unregistered: they would be reported as discrepancies by a tool built to find
  exactly that.
- THE COST OF THE _history_ SHAPE, recorded against my own proposal: those
  tables are invisible to every tool that goes through user_tables. "Here is
  the table before" is only evidence if somebody can reach the before. There is
  no escape hatch: util/sql_guard.py DOES NOT EXIST -- run_sql is Group F,
  Phase 8, and the build guide's repository layout describes the finished tree
  rather than the disk. Second time in this step I read a document as a
  description of what is there. So a clean/ reader for the history tables is a
  NECESSITY, not a convenience, and Step 6 builds it or the version tables have
  no reader at all.
- FOR PHASE 8 TO INHERIT: when run_sql gets a table guard, the obvious
  implementation is db.user_tables -- it exists and it already excludes
  bookkeeping. If it does that, cleaning history stays unreachable through
  run_sql permanently, and by accident. Written down now while the reason is
  visible.
- P6-D6's APPEND-ONLY HALF WAS DECIDED IN PHASE 2. register_dataset's docstring:
  "This is distinct from the cleaning ledger (Phase 6), which is append-only
  because it records history rather than current state." Only the envelope
  question -- whether get_cleaning_ledger returns through util/results.py --
  is open.
- NOTHING IN THE CODEBASE CALLS .cursor(). Not one site. So the cursor test in
  test_duckdb_cleaning_facts.py is prophylactic, not a bug report: it pins the
  behaviour so nobody reaches for cursor() in Step 5 believing it isolates.
- server.py opens a FRESH CONNECTION PER TOOL CALL at all thirteen sites, and
  db.py has exactly one duckdb.connect(). No shared long-lived connection
  object, which is the shape P6-D2 needs.
- THE BOOKKEEPING TABLES ARE CREATED LAZILY ON A WRITABLE CONNECTION.
  contract/store.py:138 and profile/runs.py:113 both say so. A read-only ATTACH
  cannot create a table, so Phase 6's plan store and ledger CANNOT follow that
  pattern: either they are created eagerly on a writable connection before the
  proposal path runs, or the proposal path tolerates their absence and says so
  instructionally rather than raising. Constrains Steps 3 and 7. Found by grep,
  not by design.
- src/analytics_agent/server.py.step6.bak was an importable stale module inside
  the package -- it is why every db.connect line appeared twice in this step's
  grep. Already gone by the time the removal ran. Recorded because the grep
  output kept in this step describes a state that no longer holds.
- mixed_types.xlsx EXISTS, and the draft of this step said it probably did not,
  on the grounds that Phase 5's acceptance run reported "4 csv(s)". That run
  globs *.csv. Reading a statement about a FILTER as a statement about a
  directory -- absence from a filtered list is not absence. Cost: one wrong
  paragraph, caught by an ls that should have come first.
- THE FIXTURE WAS BUILT FOR F9, NOT FOR CLEANING. make_fixtures.py's docstring:
  bad values sit below row 5000 so inference_rows=5000 never sees them, the
  sniffer types the column BIGINT, and on_error='null' counts the failures. So
  the open question for Step 2 is whether anything text-shaped SURVIVES ingest
  -- if the junk is nulled at load, the Done-When's "a text->decimal conversion
  succeeds" has no VARCHAR column to run against. Unsettled both ways: that
  docstring describes the CSV path, and in xlsx every cell carries its own
  type. Step 2 loads it through the real ingest path and COUNTS, rather than
  reasoning from the generator's intent.
- gaps_and_dupes.csv is the only CSV carrying a literal null sentinel; every
  other one writes an empty field. Phase 5's missing-value vocabulary has met
  exactly one fixture that exercises it. Carried to P6-D5.

## Phase 6, Step 2 — the fixture, counted

- make_fixtures.py STATES mixed_types.xlsx's ground truth beside the generator:
  refusal at row 5101, {'units': 7, 'unit_price': 3} under on_error='null',
  all VARCHAR under all_text=True. That is a claim, not a count. Phase 5
  shipped a claim of the same shape -- "the DISTINCT * scan is the slow half"
  -- wrong by a factor of ten. tests/test_mixed_types_ground_truth.py counts
  the rows AND asserts the POSITIONS, because a count can be right for the
  wrong reason and a position cannot.
- THE PHASE 6 DONE-WHEN IS REACHABLE ONLY UNDER all_text=True, and nothing in
  the build guide says so. Default on_error='stop' refuses the fixture at row
  5101, so it never loads. on_error='null' converts units and unit_price at
  INGEST and nulls the bad values, so there is no text left for cleaning to
  find. Only all_text leaves six VARCHAR columns, and "a text->decimal
  conversion succeeds" needs one. This is the real story rather than a defect:
  a person meets the refusal, reaches for the documented escape hatch, and now
  holds text columns that need cleaning. Phase 6 is what happens next, and
  Step 4 detects against THAT state of the world.
- P6-D4 ANSWERED, and not with a threshold. The fixture holds two conversions
  identical in shape -- text in a numeric column, 7 of 6,000 and 3 of 6,000,
  TRY_CAST NULL for both -- and different in kind. 'n/a' in units is a DECLARED
  MISSING TOKEN (DEFAULT_NA_VALUES, case-insensitive, and region uses 'N/A' for
  exactly that purpose in this same fixture), so converting it to NULL makes an
  absence that was always there explicit and loses nothing. 'not priced' in
  unit_price is NOT declared: it says a price was withheld rather than merely
  absent, and converting it destroys the only record of the difference.
  THE RULE: a conversion may convert an unconvertible value that is already a
  declared missing token. An undeclared one is information -- the proposal
  names it, shows a sample, and states what will be lost. A percentage would
  have passed both at 0.12% and 0.05% and been silent about the difference
  that matters. Asserted in SQL against the config the loaders read, not
  against a list recalled from pandas.
- The recon's section 2 failed -- `zsh: no matches found: --include=*.py`
  needs quoting. Section 1's tree covered enough that it was not re-run.
- load_excel's na_values DEFAULTS TO NO TOKENS, not to DEFAULT_NA_VALUES. So
  region's ~300 'N/A' strings survive the load as literal text and the
  missing-token action on region is still Phase 6's to propose. It also
  narrows the P6-D4 wording: DEFAULT_NA_VALUES is the vocabulary the project
  PUBLISHES and the profiler defaults to, not one every loader applies. The
  point stands -- the proposal reads the published list rather than deriving a
  second one -- but "the loaders read it today" was too strong.
- load_excel's replace DEFAULTS TO TRUE: a second load of the same dataset
  name overwrites in silence. Same hole Phase 5's live run found in the
  profile run record, one layer further out, and Phase 6 writes tables for a
  living. Step 5 decides whether apply_cleaning_plan may overwrite an existing
  target name or must refuse.
- unit_price lands as DOUBLE, not DECIMAL, under on_error='null'. Pinned, so a
  Step 5 conversion that claims to produce a decimal has something to fail
  against.
- mixed_types.xlsx SUPPORTS FIVE CANDIDATE ACTIONS, NOT SIX. Counted: 0 exact
  duplicate rows, 0 whitespace-padded values, 0 case variants, across all six
  columns. It is a type-coercion fixture and nothing else -- the generator
  writes clean values through random.choice on fixed lists, so there was never
  a mechanism for any of them to appear. The Done-When asks to approve 3 of 6.
  Step 4 decides between: a rule fires that this inventory does not predict;
  the 6 was a round number written before the phase existed (Phase 5's
  Done-When named three clauses and the test asserted five, same cause); or a
  fixture gains a defect. IF THE THIRD, ADD A SECOND FIXTURE RATHER THAN
  EDITING THIS ONE -- mixed_types.xlsx now has ten tests pinning its counts and
  row positions, and mutating it to hit a number invalidates all of them.
- COVERAGE GAP: whitespace trimming, case normalisation and duplicate removal
  are three of the build guide's ten detection rules and none has a fixture
  proven against it here. gaps_and_dupes.csv is named for duplicates and
  probably covers one, uncounted and not asserted. Step 4's probe counts all
  three across every fixture in one pass.

## Phase 6, Step 3 — clean/plan.py

- P6-D1 DOES NOT BLOCK THIS STEP AND I SAID THREE TIMES THAT IT DID. An
  action's target is the DATASET, not a physical table: locked decision 13
  already partitions state by dataset_name, _agent_datasets is keyed on it,
  runs.py stores it. A plan that stores dataset_name and leaves physical
  naming to the layer that writes tables is correct under either answer.
  P6-D1 moves to STEP 6, where the tables are actually written -- the same
  argument Phase 5 used to push excluded_columns out of its Step 8.
- P6-D4 IS ENFORCED BY THE CONSTRUCTOR, not by a docstring. CleaningAction
  refuses to exist with values_lost > 0 and no sample: "an action that cannot
  show what it destroys is not a proposal". values_lost counts UNDECLARED
  values only -- Step 2's finding that units' 'n/a' (declared) and
  unit_price's 'not priced' (undeclared) are the same shape and different
  kinds. Six lines, and it is the one place the rule can be made impossible
  to forget.
- STALENESS CHECKS THE FINGERPRINT BEFORE THE ROW COUNT, and says so. They are
  different events: rows changing means less or more of the same table; the
  fingerprint changing means a DIFFERENT table wearing the same name, which is
  what load_excel(replace=True) produces by default and what drift_phrase in
  runs.py cannot catch when the replacement is the same size. F13, third
  appearance, answered at the start rather than found later.
- PER-PLAN ACTION IDS. C001 is read off a screen and typed back, which rules
  out a uuid, which makes ids ambiguous across plans, so resolution always
  goes through latest() and refuses on staleness rather than picking one.
- resolve() RETURNS THE UNKNOWN IDS TOO. A caller that only gets the hits
  cannot tell the person which approved id it ignored, and silently skipping
  an approved action is the worst failure this tool has available.
- ONE FLAT TABLE, denormalised on purpose: plan-level columns repeat on every
  action row. A plan is read whole and never updated, so a join buys
  normalisation nobody spends. Same call runs.py made.
- NOT IN THIS FILE: computing the fingerprint (contract/binding.py owns it and
  it has not been read, so record() takes one as a parameter), and any SQL
  (clean/sql.py renders it; a model that can BUILD SQL can build different SQL
  from the one it showed).
- STEP ORDER CORRECTED: sql.py before detect.py. The build guide requires every
  proposal to show the exact SQL that will run, so an action carries SQL from
  birth and detection cannot produce one until the renderer exists.

## Phase 6, Step 4 — clean/sql.py

- ONE EXPRESSION PER ACTION, and the statement, the affected count, the loss
  count and the sample are all built from it. The build guide says a proposal
  shows the exact SQL that will run; a proposal also shows NUMBERS, and a count
  built from a different expression than the statement is a guess about a
  statement it has never met. Phase 5's clause 4 with a write at the end.
  Asserted: the expression appears verbatim in the statement it builds.
- P6-D9: ONE STATEMENT PER ACTION, not one composed rebuild. Three approved
  actions rebuild the table three times. Composing them would be cheaper and
  would make the ledger dishonest -- a row count attributed to C002 is only
  verifiable if C002 ran alone. If the cost ever bites, the answer is to SAY
  the rebuild was batched, not to attribute a composed count to an action.
- LITERAL SQL, NOT BOUND PARAMETERS. The strings are shown to a person who then
  approves them, so what is shown has to be what runs. Values escaped, with
  tests for a quote inside a token and a space inside a column name -- Phase 3's
  header assembly produces `order date` and it is not hypothetical.
- P6-D10 OPEN, and it is a bug in Step 3 found by writing Step 4.
  CleaningAction.line() says "N value(s) will become NULL", which is true for
  CONVERT_TYPE and false for the other lossy kinds. NORMALISE_CASE nulls
  nothing and still destroys something: 'North' and 'north' merge and the
  record that the source wrote them differently is gone, so its loss is counted
  in DISTINCT VALUES. DROP_DUPLICATE_ROWS destroys multiplicity -- two identical
  rows may be two real events, which is exactly the judgement the profiler
  declines. Fix is one field, loss_unit, on the action. BELONGS AT STEP 5 where
  actions are constructed, same reason P6-D1 moved to Step 6.
- NORMALISE_MISSING IS NEVER LOSSY BY CONSTRUCTION -- the only values it touches
  are already declared to mean absent. Which is why its tokens are rendered
  into the statement in plain sight rather than looked up from config at apply
  time: widen the list to something that is not a missing token and it becomes
  a different action, and the approver can see that it has.
- The fingerprint is a PROPERTY ON THE BINDING (dataset_contract.py:198), sha256
  over "name:TYPE" joined by "|", first 12 hex; DatasetContract delegates to it.
  The proposal path builds a binding and reads the property rather than hashing
  a column list a second way. Binding.from_pairs' full signature is still
  unread -- Step 5 opens with inspect.signature on it.

## Phase 6, Step 5 — clean/detect.py

- P6-D5 RESOLVED BY P6-D2, not by preference. Detection cannot read a
  TableProfile: profile_dataset records a run in _agent_profiles, and the
  proposal path holds the workspace through ATTACH (READ_ONLY), which refuses
  INSERT and CREATE by statement type. A read-only path cannot invoke a tool
  that writes. Detection reads for itself and everything it reads is a SELECT
  -- which is better anyway, because a profile from forty minutes ago describes
  the table as it WAS and a proposal must describe it as it IS.
- THREE GUARDS, EACH AGAINST MEASURED DUCKDB BEHAVIOUR. Each has a test that
  asserts the behaviour first and the guard second, so the guard cannot be
  tidied away by someone who does not know why it is there.
    * TRY_CAST('9.50' AS BIGINT) is 10. A price column parses 100% as BIGINT
      and rounds every value. BIGINT is only proposed when
      count(*) WHERE TRY_CAST(c AS DOUBLE) <> TRY_CAST(c AS BIGINT) is 0.
      Phase 5 had already WRITTEN DOWN that TRY_CAST rounds 4.5 to 5, and it
      still nearly went into a detector. A note without a test is worth this.
    * TRY_CAST('1' AS BOOLEAN) is TRUE. An integer column of 1s and 0s parses
      perfectly as boolean, and proposing it would turn counts into flags.
      BOOLEAN requires the literal words TRUE/FALSE.
    * TRY_CAST makes a DATE from a timestamp string and drops the time.
      TIMESTAMP by default; DATE only when every value is already midnight.
    * Fourth, smaller: DECIMAL(18,2) over DOUBLE wherever every value survives
      exactly. Money in a DOUBLE is how a total ends in .9999999999998.
- P6-D10 FIXED: CleaningAction carries loss_unit. "1 distinct value(s) will be
  discarded" for a case fold, "2 row(s)" for a de-duplication, "value" for a
  conversion.
- STEP 3'S RULE CAUGHT A GAP IN STEP 4 DURING STEP 5, unlooked for.
  drop_duplicate_rows returned sample_sql=None; detection built an action with
  values_lost=2 and __post_init__ refused it -- "an action that cannot show
  what it destroys is not a proposal". The fix is a real sample: the duplicated
  rows as JSON WITH their multiplicity, since the count is what is destroyed.
- EXCLUDE_COLUMN IS NEVER DETECTED. A column that is entirely null may be the
  one that matters with a broken feed. Nothing in a table's contents can
  suggest dropping it; it comes from the contract (P6-D8) or a person.
- IDS ARE STABLE: table-level first, then columns in ordinal order, asserted
  across two runs. An id that moves between proposals is an id nobody can
  approve.
- P6-D11 OPEN, found by running detection on the real fixture. Detection
  produced SIX actions, not the five Step 2 predicted, and the sixth is the
  problem: C003 converts units to BIGINT and C004 normalises the same seven
  'n/a' values in units. One decision, two actions, because each rule fires on
  its own terms. Approving both is redundant at best; under P6-D9 each action
  is a separate statement against the previous table, so C004 meets a BIGINT
  column and MEASURED: "BinderException: No function matches the given name and
  argument types 'trim(BIGINT)'" -- after C003 has already rebuilt the table.
  The failure lands MID-APPLY. Step 6 picks between: detection not offering
  NORMALISE_MISSING on a column it also offers CONVERT_TYPE for; the plan
  recording the subsumption and the tool refusing the combination by name; or
  apply re-rendering against the table as it stands, which is OUT because the
  SQL shown would stop being the SQL run.
- Detection found NO whitespace and NO case actions on mixed_types, agreeing
  with Step 2's independent count of zero padded values and zero case variants.
  Two measurements of one fixture agreeing is worth more than either alone.
- CONVERT_MIN_SHARE = 0.90, and it is a judgement stated as one. Below that a
  column is not the wrong type, it is a MIXED column, and merging two meanings
  is a decision no threshold should make. The fixture sits far above it
  (5,993/6,000 and 5,997/6,000), so the number is not tuned to pass it.

## Phase 6, Step 6 — clean/apply.py

- P6-D1 DECIDED: clean forward under the same name, previous contents kept as
  _agent_history_<name>_v<N>. Asked four times and not answered, so decided on
  the evidence and built so overruling costs one function (history_table and
  next_version; the apply loop never sees a name it did not get from them).
  The evidence: db.user_tables filters `NOT LIKE '\_%'` IN SQL and
  state._loadable_tables filters the underscore again, so the snapshot is
  already hidden without a new filter; _agent_datasets has dataset_name as its
  PRIMARY KEY with no version column, so sales_v2 would be a second row for one
  dataset or a table reported as "unknown - not created by a loader"; the
  contract and the profile stay bound to the name they were written against;
  and both tables sit on disk, so before/after is evidence rather than a ledger
  line describing one.
- THE COST OF THAT, PAID HERE RATHER THAN PROMISED AGAIN: those snapshots are
  invisible to every tool going through user_tables, and run_sql is Phase 8. A
  before-table nobody can open is not evidence, so history_tables() and
  read_history() are part of this module.
- P6-D11 DECIDED: a CONVERT_TYPE claims its column. conflicts() refuses the
  combination and NAMES which to drop, rather than detection silently never
  offering it. The rule is about TYPE CHANGES, not columns -- trim then
  case-fold on one column is two text functions on a VARCHAR in order, both
  survive, and there is a test asserting they are allowed.
- DUCKDB'S DDL IS TRANSACTIONAL, measured: CREATE OR REPLACE inside a
  transaction rolls back, and a table created inside one disappears. So a
  failing action leaves the dataset EXACTLY as it was and the rollback takes
  the snapshot with it -- no half-cleaned table, no orphan snapshot describing
  a clean that never happened. conflicts() is still the better guard, because
  being told which id to drop beats a rollback that says nothing; the
  transaction is what makes the failure survivable when the guard misses, which
  it will, because it knows about one interaction and there will be others.
- EVERY STATEMENT MUST WRITE TO THE DATASET IT WAS PROPOSED FOR. A stored plan
  is data, and data naming its own write target is checked against the target
  the caller asked for rather than trusted. apply refuses anything not
  beginning CREATE OR REPLACE TABLE "<dataset>" AS.
- _agent_datasets IS DELIBERATELY NOT REWRITTEN. register_dataset REPLACES the
  row and resets loaded_at, which would make a cleaned dataset look freshly
  loaded and erase where it came from. Row counts there go stale for a cleaned
  dataset; state.dataset_states reads shape from db.table_shape live, so the
  listing stays correct. A choice, not an oversight.

## Phase 6, Step 7 — the ledger and the tools

- P6-D6 DECIDED, BOTH HALVES, and the first half OVERRULES THE BUILD GUIDE.
  The ledger is a TABLE, not the JSONL the guide asks for, because there is
  exactly one thing a file cannot do: be written inside the same transaction as
  the apply. Step 6 measured that DuckDB rolls DDL back. A ledger written after
  the commit can fail after it, leaving a clean nobody recorded; written before
  a rollback it records a clean that never happened. A row in the same
  transaction cannot disagree with the tables it describes, and a test rolls an
  apply back and asserts the ledger is empty. Durability across workspace.reset
  is not a counter-argument -- reset is meant to clear the workspace, and a
  ledger that outlived it would describe tables that are gone.
- NO ENVELOPE. util/results.py is for results too big to say. A ledger is
  bounded by the number of approvals, not by the size of the data. describe()
  returns inline, newest first, capped at 20 with the remainder COUNTED --
  P5-D3's principle on a different problem.
- ONE ROW PER ACTION, not per apply. The Done-When is "the ledger shows exactly
  those 3 with correct counts", which is a statement about actions. An
  apply-level row would have to summarise, and summarising is where a count
  stops being checkable.
- ACTION_NOT_IN_PLAN REFUSES THE WHOLE CALL. Approving ["C001","C099"] runs
  nothing. Running the ids it recognised and silently skipping the one it did
  not is the worst failure this tool has available; a test asserts the ledger
  stays empty.
- connect_read_only LIVES IN clean/tools.py, not util/db.py, because db.connect
  runs CREATE TABLE IF NOT EXISTS on every open and a read-only attach refuses
  CREATE by statement type. A test asserts the proposal path actually uses it
  rather than trusting the code above it.
- FIVE REASON MEMBERS ADDED BY TARGETED EDIT rather than a full re-delivery of
  refusals.py: the enum was read verbatim, the rest of the file was not, and
  delivering a whole file seen only in part is worse than an edit whose anchor
  can be quoted.
- THE FINGERPRINT IS COMPUTED BY PHASE 4'S CODE. clean/tools._fingerprint reads
  the column list and calls Binding.from_pairs(pairs, row_count).fingerprint.
  The alternative was hashing the list here, and two fingerprints of one table
  that disagree would be worse than a signature mismatch that fails loudly.
  The signature was PROBED before the file was pasted and from_pairs turned out
  to require row_count, which a memory-written call would have got wrong --
  loudly, on the first proposal, after five files had been pasted. The
  fingerprint is still taken over the columns alone: structure is identity,
  volume is not, and the binding records both.
- THE FINGERPRINT CAUGHT A STALE PLAN WITH THE ROW COUNT UNCHANGED, live, in
  the round trip: 6,000 rows before and after, 819059ecc8eb -> 6070c50fbe3a
  after three columns changed type. drift_phrase in profile/runs.py returns None
  whenever current_rows == run.row_count, which is the hole Phase 5's live run
  found; Step 3 checked the fingerprint FIRST on the argument that structure and
  volume are different events, and this is that argument being right about
  something rather than reasoned about.
- P6-D12 OPEN, found in the round trip's own output. propose_cleaning_plan's
  NEXT STEP suggests stored.actions[:3] -- the first three ids, whatever they
  are. On this fixture C001/C002/C003 happen to be compatible; on a table where
  one column yields both a conversion and a missing-token normalisation early,
  the first three would contain a conflicting pair and THE TOOL WOULD REFUSE ITS
  OWN SUGGESTED CALL. Refusal.__post_init__ already enforces that a next_call is
  a call the agent can make (it checks for parentheses); this is the same
  principle one level up and unenforced. Second problem in the same line: the
  slice takes no view on loss, so on another fixture it would nudge toward the
  action it had just warned about. Fix at Step 8: suggest the first three that
  are neither lossy nor in conflict, and say so.
- THE LIVE RUN COVERED IT ON THE SECOND ATTEMPT. The first found no cleaning
  tool: Desktop's server process predated the registration, and closing a
  window is not ending a process. The agent declined to substitute a re-load
  with dtypes -- "that is not cleaning, it is a different ingest, with no
  version history and no record of what changed" -- which is P6-D1's argument
  reached by something that has not read it.
- THE GATE WORKED. Five actions applied, unit_price WITHHELD and left VARCHAR,
  unprompted. The one action carrying a discard warning is the one that did not
  run.
- THE AGENT OUT-DESIGNED THE P6-D11 REFUSAL, and it is right. It split
  normalisation from conversion into two calls so the seven 'n/a' values would
  be attributed to a normalisation somebody named rather than to a silent cast:
  "same end state, different ledger story". conflicts() currently says "approve
  one", which loses that record. THE REFUSAL SHOULD OFFER THE TWO-CALL ORDER
  instead. Step 8.
- AN AMBIGUITY I LEFT IN THE API. The agent could not tell whether
  approved_action_ids applies in list order or plan order, so it forced the
  order with two calls rather than assume. It IS list order --
  CleaningPlan.resolve iterates the ids as given -- and nothing says so.
  apply_cleaning_plan's docstring should. Step 8.
- A PERCENTAGE ROUNDS UP THROUGH A FAILURE. The profile printed "100.0% of its
  6,000 values parse as DOUBLE" on a column where 3 do not: 5,997/6,000 is
  99.95%, rounded. A reader skimming that concludes the column is clean. Floor
  rather than round, or clamp to 99.9% when the failure count is non-zero.
  Phase 5's renderer, and the third display finding against it in two runs.
- P6-D12 CONFIRMED AND WORSE THAN RECORDED. I wrote that the canned NEXT STEP's
  first-three slice would put the lossy action inside it on ANOTHER fixture. It
  happened on THIS one, one apply later: ids renumber between proposals,
  unit_price moved C005 -> C003, and the suggestion then named it. An agent
  following the tool's own advice discards 'not priced' believing it took the
  safe option.
- P6-D13 OPEN. Ledger ids collide across proposals -- C002 and C004 each appear
  twice meaning different actions, disambiguated only by the history table
  name. Per-plan ids are right for approval (C001 is read off a screen and
  typed back, which rules out a uuid) and wrong for a permanent record. The data
  is already stored: LedgerEntry.plan_id exists and line() does not print it.
  Cheap fix, Step 8.
- TWO PHASE 5 DISPLAY FINDINGS, from that run, neither put there by this phase.
  (a) The dataset-level missing-token summary prints the matched VOCABULARY
  ENTRY rather than the stored token: region holds 'N/A' and units holds 'n/a'
  and both are reported as 'N/A'. Nothing is miscounted -- Step 2 measured the
  match is case-insensitive -- but the line names a token the data does not
  contain, and someone writing na_values=["N/A"] off it would miss all seven.
  (b) units' range line reads "1 to n/a", a min/max over text that includes a
  token. Same renderer, probably the same fix. Logged, not fixed here.
- AND ONE PIECE OF CAUTION THAT VALIDATED STEP 5. The agent declined to infer
  from 365 distinct order_date values that every value is midnight -- "a day
  carrying two distinct timestamps and another carrying zero produces the same
  count". Correct, and detect.proposed_type does not use distinct counts for
  that: it asks TRY_CAST(c AS TIMESTAMP) <> date_trunc('day', ...) directly.
  The caution was right and the guard already answered it.
- P6-D8 IS NOT IN THIS STEP. The contract is a PYDANTIC model (Measure and
  Exclusion are both BaseModel) with an SCD2 store and a propose path behind
  it, and DatasetContract's own field list has not been read. Writing a field
  into a validated model nobody has seen is the mistake this phase has logged
  four times. Step 8, after one read.

## Phase 6, Step 7 — the ledger and the tools

- P6-D6 DECIDED, BOTH HALVES, and the first half OVERRULES THE BUILD GUIDE.
  The ledger is a TABLE, not the JSONL the guide asks for, because there is
  exactly one thing a file cannot do: be written inside the same transaction as
  the apply. Step 6 measured that DuckDB rolls DDL back. A ledger written after
  the commit can fail after it, leaving a clean nobody recorded; written before
  a rollback it records a clean that never happened. A row in the same
  transaction cannot disagree with the tables it describes, and a test rolls an
  apply back and asserts the ledger is empty. Durability across workspace.reset
  is not a counter-argument -- reset is meant to clear the workspace, and a
  ledger that outlived it would describe tables that are gone.
- NO ENVELOPE. util/results.py is for results too big to say. A ledger is
  bounded by the number of approvals, not by the size of the data. describe()
  returns inline, newest first, capped at 20 with the remainder COUNTED --
  P5-D3's principle on a different problem.
- ONE ROW PER ACTION, not per apply. The Done-When is "the ledger shows exactly
  those 3 with correct counts", which is a statement about actions. An
  apply-level row would have to summarise, and summarising is where a count
  stops being checkable.
- ACTION_NOT_IN_PLAN REFUSES THE WHOLE CALL. Approving ["C001","C099"] runs
  nothing. Running the ids it recognised and silently skipping the one it did
  not is the worst failure this tool has available; a test asserts the ledger
  stays empty.
- connect_read_only LIVES IN clean/tools.py, not util/db.py, because db.connect
  runs CREATE TABLE IF NOT EXISTS on every open and a read-only attach refuses
  CREATE by statement type. A test asserts the proposal path actually uses it
  rather than trusting the code above it.
- FIVE REASON MEMBERS ADDED BY TARGETED EDIT rather than a full re-delivery of
  refusals.py: the enum was read verbatim, the rest of the file was not, and
  delivering a whole file seen only in part is worse than an edit whose anchor
  can be quoted.
- THE FINGERPRINT IS COMPUTED BY PHASE 4'S CODE. clean/tools._fingerprint reads
  the column list and calls Binding.from_pairs(pairs, row_count).fingerprint.
  The alternative was hashing the list here, and two fingerprints of one table
  that disagree would be worse than a signature mismatch that fails loudly.
  The signature was PROBED before the file was pasted and from_pairs turned out
  to require row_count, which a memory-written call would have got wrong --
  loudly, on the first proposal, after five files had been pasted. The
  fingerprint is still taken over the columns alone: structure is identity,
  volume is not, and the binding records both.
- THE FINGERPRINT CAUGHT A STALE PLAN WITH THE ROW COUNT UNCHANGED, live, in
  the round trip: 6,000 rows before and after, 819059ecc8eb -> 6070c50fbe3a
  after three columns changed type. drift_phrase in profile/runs.py returns None
  whenever current_rows == run.row_count, which is the hole Phase 5's live run
  found; Step 3 checked the fingerprint FIRST on the argument that structure and
  volume are different events, and this is that argument being right about
  something rather than reasoned about.
- P6-D12 OPEN, found in the round trip's own output. propose_cleaning_plan's
  NEXT STEP suggests stored.actions[:3] -- the first three ids, whatever they
  are. On this fixture C001/C002/C003 happen to be compatible; on a table where
  one column yields both a conversion and a missing-token normalisation early,
  the first three would contain a conflicting pair and THE TOOL WOULD REFUSE ITS
  OWN SUGGESTED CALL. Refusal.__post_init__ already enforces that a next_call is
  a call the agent can make (it checks for parentheses); this is the same
  principle one level up and unenforced. Second problem in the same line: the
  slice takes no view on loss, so on another fixture it would nudge toward the
  action it had just warned about. Fix at Step 8: suggest the first three that
  are neither lossy nor in conflict, and say so.
- THE LIVE RUN COVERED IT ON THE SECOND ATTEMPT. The first found no cleaning
  tool: Desktop's server process predated the registration, and closing a
  window is not ending a process. The agent declined to substitute a re-load
  with dtypes -- "that is not cleaning, it is a different ingest, with no
  version history and no record of what changed" -- which is P6-D1's argument
  reached by something that has not read it.
- THE GATE WORKED. Five actions applied, unit_price WITHHELD and left VARCHAR,
  unprompted. The one action carrying a discard warning is the one that did not
  run.
- THE AGENT OUT-DESIGNED THE P6-D11 REFUSAL, and it is right. It split
  normalisation from conversion into two calls so the seven 'n/a' values would
  be attributed to a normalisation somebody named rather than to a silent cast:
  "same end state, different ledger story". conflicts() currently says "approve
  one", which loses that record. THE REFUSAL SHOULD OFFER THE TWO-CALL ORDER
  instead. Step 8.
- AN AMBIGUITY I LEFT IN THE API. The agent could not tell whether
  approved_action_ids applies in list order or plan order, so it forced the
  order with two calls rather than assume. It IS list order --
  CleaningPlan.resolve iterates the ids as given -- and nothing says so.
  apply_cleaning_plan's docstring should. Step 8.
- A PERCENTAGE ROUNDS UP THROUGH A FAILURE. The profile printed "100.0% of its
  6,000 values parse as DOUBLE" on a column where 3 do not: 5,997/6,000 is
  99.95%, rounded. A reader skimming that concludes the column is clean. Floor
  rather than round, or clamp to 99.9% when the failure count is non-zero.
  Phase 5's renderer, and the third display finding against it in two runs.
- P6-D12 CONFIRMED AND WORSE THAN RECORDED. I wrote that the canned NEXT STEP's
  first-three slice would put the lossy action inside it on ANOTHER fixture. It
  happened on THIS one, one apply later: ids renumber between proposals,
  unit_price moved C005 -> C003, and the suggestion then named it. An agent
  following the tool's own advice discards 'not priced' believing it took the
  safe option.
- P6-D13 OPEN. Ledger ids collide across proposals -- C002 and C004 each appear
  twice meaning different actions, disambiguated only by the history table
  name. Per-plan ids are right for approval (C001 is read off a screen and
  typed back, which rules out a uuid) and wrong for a permanent record. The data
  is already stored: LedgerEntry.plan_id exists and line() does not print it.
  Cheap fix, Step 8.
- TWO PHASE 5 DISPLAY FINDINGS, from that run, neither put there by this phase.
  (a) The dataset-level missing-token summary prints the matched VOCABULARY
  ENTRY rather than the stored token: region holds 'N/A' and units holds 'n/a'
  and both are reported as 'N/A'. Nothing is miscounted -- Step 2 measured the
  match is case-insensitive -- but the line names a token the data does not
  contain, and someone writing na_values=["N/A"] off it would miss all seven.
  (b) units' range line reads "1 to n/a", a min/max over text that includes a
  token. Same renderer, probably the same fix. Logged, not fixed here.
- AND ONE PIECE OF CAUTION THAT VALIDATED STEP 5. The agent declined to infer
  from 365 distinct order_date values that every value is midnight -- "a day
  carrying two distinct timestamps and another carrying zero produces the same
  count". Correct, and detect.proposed_type does not use distinct counts for
  that: it asks TRY_CAST(c AS TIMESTAMP) <> date_trunc('day', ...) directly.
  The caution was right and the guard already answered it.
- P6-D8 IS NOT IN THIS STEP. The contract is a PYDANTIC model (Measure and
  Exclusion are both BaseModel) with an SCD2 store and a propose path behind
  it, and DatasetContract's own field list has not been read. Writing a field
  into a validated model nobody has seen is the mistake this phase has logged
  four times. Step 8, after one read.

## Phase 6, Step 8b — P6-D12, properly

- STEP 8'S FIX DID NOT CHANGE THE SUGGESTION. Filtering lossy and mutually
  conflicting actions still returned ['C001','C002','C003'] on the real
  fixture -- byte for byte what the broken version produced. It removed the
  reported symptom (the lossy action) and kept C003, the units conversion,
  which is the thing this module's OWN REFUSAL tells you not to do first.
- WHY IT SLIPPED: conflicts() only fires when the conversion and the
  normalisation are in the SAME call. Suggesting the conversion alone passes
  every check and still disposes of the seven declared tokens by cast rather
  than by a step somebody named. A SUGGESTION THAT CONTRADICTS THE REFUSAL IS
  NOT A SMALLER BUG THAN ONE THAT GETS REFUSED -- it is a quieter one.
- THIRD FILTER ADDED: no CONVERT_TYPE on a column that also has a
  NORMALISE_MISSING waiting. Suggestion becomes ['C001','C002','C004'] and the
  conversion comes round next proposal, which is the order the refusal
  recommends.
- DEFERRED IS NOT EXCLUDED, and a list of ids cannot tell you which. C005 is
  left out because it discards something; C003 because it should run second.
  The line now names the deferred id and says why.
- AND A TEST WRITTEN BADLY: the first version asserted the deferred id appeared
  nowhere before "Any of the others", which failed because the sentence
  explaining the deferral names it. It now checks the approved_action_ids
  bracket specifically and separately asserts the id IS in the prose. Getting
  that wrong first time is the same confusion the sentence exists to prevent.

## Phase 6, Step 9b — every NEXT STEP must agree with its own message

- THE CONFLICT REFUSAL'S WORDING WAS RIGHT AND ITS NEXT STEP CONTRADICTED IT.
  The WHY says "approve C004 on its own first"; the NEXT STEP named C003, the
  conversion, because it used found[0] -- the first approved id in list order.
  An agent that reads the refusal and follows its call does the OPPOSITE of
  what the refusal asked, and has no reason to doubt it. Worse than no
  next_call.
- P6-D12 ONE LEVEL DOWN, found twice in two steps, which is the useful part.
  Refusal.__post_init__ already checks a next_call is A CALL (it looks for
  parentheses) and nothing checks it is the RIGHT call. So this step swept all
  five refusals in the module rather than fixing the one that showed.
- TWO OF FIVE WERE WRONG. ACTIONS_CONFLICT named the conversion.
  NOTHING_APPROVED used actions[0], which on a plan whose first action is lossy
  would recommend the discard -- it had not misbehaved yet only because this
  fixture's first action is lossless.
- first_step() COMPUTES THE RECOMMENDATION THE SAME WAY THE MESSAGE IS BUILT,
  not by position: the action that is not the type change on the contested
  column. A message and its call derived from one rule cannot disagree -- the
  same argument clean/sql.py makes about a count and a statement built from one
  expression. _next_call_id() reuses _safe_suggestion so there is one
  definition of "safe to recommend" rather than two.

## Phase 6, Step 10b — the cap nobody chose

- THE LIVE RUN ANSWERED ITS QUESTION: the agent still reasons about
  'not priced' explicitly rather than following a suggestion that now excludes
  it -- "a statement about the order, not an absent number". The judgement is
  being made, not delegated. It also read the C003 deferral correctly without
  being told.
- AND IT FOUND ONE MORE. The NEXT STEP omitted C006, a boolean conversion that
  discards nothing and conflicts with nothing; the agent added it by hand and
  said the suggested set "will under-report on every clean table". Right, and
  neither of its two hypotheses was the cause: _safe_suggestion carried
  limit=3.
- WHERE THE 3 CAME FROM. The original line was stored.actions[:3], capped
  because the set was arbitrary and the line had to stay short. P6-D12 replaced
  the slice with filters and THE 3 CAME ALONG WITH IT -- a number that meant
  something when the set was "the first few" and means nothing once the set is
  defined by a property. Worse, the line says "these discard nothing and can run
  together" without saying it is a subset. A PARAMETER THAT OUTLIVED ITS REASON.
- WHY THE ACCEPTANCE TEST MISSED IT. Clause 5 asserts the suggestion EXCLUDES
  what it should and that the tool accepts it. Nothing asserted it INCLUDES what
  it should -- an easy asymmetry to write and a hard one to notice, because
  every assertion passed. The new test compares the suggested ids against
  _safe_suggestion's own output rather than a hand-written list, so the two
  cannot drift.
- THIRD DEFECT IN THIS PHASE FOUND BY AN AGENT READING THE OUTPUT rather than
  by a test reading the code, and like the other two it was a sentence
  disagreeing with a behaviour rather than a mechanism failing.

## Phase 6, Step 10c — the cleaned stage

- IT ARRIVES THE WAY PROFILING DID. describe_workflow_state already splices a
  list of lines from runs.state_notes, empty when there is nothing to say, so
  clean/ledger gained a state_notes of the same shape rather than a special
  case being carved for it.
- NOT IN DatasetState.stage. That column is about whether ANALYSIS CAN RUN
  ("contract v2, ready"); cleaning is a different axis -- a dataset can be
  cleaned with no contract, or carry a contract and never have been cleaned.
  Phase 5 put profiling in the per-dataset section for the same reason rather
  than inventing "loaded, profiled, no contract".
- THE MIDDLE LINE EXISTS BECAUSE OF P6-D1. It names the snapshot AND says no
  listing shows it, because db.user_tables filters the underscore in SQL and a
  reader who goes looking for _agent_history_mixed_v1 in list_datasets will not
  find it. Naming a table without that clause is a dead end dressed as a
  pointer.
- EMPTY, NOT "not cleaned". The renderer already writes its own line when
  profile notes come back empty; a second module inventing an absence message
  would put two voices in one section. Whether an uncleaned dataset should say
  anything stays the renderer's decision.
- THE IMPORT IS LOCAL, and the honest reason is that state.py's import block
  has not been read -- an anchored edit against imports nobody has seen is how
  this phase already burned two round trips. The secondary reason is real too:
  state.py is imported by the server at startup and clean/ledger imports
  profile/runs.

## Phase 7, Step 1 — the ground facts

- P7-D1. KEY UNIQUENESS IS ASKED WITH GROUP BY, NEVER count(DISTINCT).
  count(DISTINCT (x)) is not a row constructor -- it is count(DISTINCT x) and
  drops NULLs -- while count(DISTINCT (x,y)) IS one and treats NULLs as equal.
  So the generic form is right for every composite key it gets tested against
  and wrong for a one-column key: two rows 'a' and NULL, no duplicate, reads
  as one duplicate. GROUP BY ... HAVING count(*) > 1 is null-safe for both
  shapes AND returns the offending values rather than a count of them.
  SCOPE: this is a rule for validate/, NOT a correction to contract/.
  verify_key already documents the difference between the two forms at
  compatibility.py:419 and gathers per-column null counts because of it --
  Phase 4 got there first, and a predicted oversight turned out to be a
  recorded decision. So validate/ imports verify_key for the VERDICT and adds
  one GROUP BY query beside it for the OFFENDERS, because a count cannot name
  the rows and the reader's next question is always the values. Two
  implementations of "is this key unique" would eventually disagree with the
  gate; one implementation and one evidence query cannot.
- P7-D2. AN INCLUSIVE WINDOW'S UPPER BOUND IS < end + INTERVAL 1 DAY.
  AnalysisWindow is inclusive at both ends and date_column may be TIMESTAMP.
  dt <= DATE '2024-12-31' casts the bound to midnight and drops
  2024-12-31 23:59:59. Written the obvious way, every window on a timestamp
  column loses its last day silently.
- P7-D3. NOT IN IS BANNED IN validate/. One NULL in the parent column makes
  NOT IN return zero rows, so an orphan check reports a clean pass on a table
  full of orphans. NOT EXISTS is the form. An orphan and a NULL key are
  counted apart -- both are unmatched, only one is a broken reference.
- P7-D4. EVERY CHECK REPORTS FOUR NUMBERS THAT SUM TO THE ROW COUNT: checked,
  passed, failed, not checked. Measured on a window and on a range: a
  predicate does not see NULLs, so inside + outside != rows. P5-D3's principle
  on a new problem -- a cap with the remainder reported, never a sample with
  the shortfall unstated.
- ROW COUNT VS EXPECTATION NEEDS NO NEW FIELD. Binding.row_count is what the
  table held when the contract was confirmed, already stored beside the
  fingerprint. classify_drift computes the same difference as a caveat;
  validation renders it as a pass/fail row.
- CALENDAR COVERAGE IS NOT THIS PHASE. It is Tier 3 (Phase 9) and F10 makes it
  a precondition of TREND analysis, not of validation. A missing month is a
  caveat on a line chart, not a broken dataset.
- P7-D5 IS OPEN. Four of the guide's eight checks (null rules, ranges,
  referential integrity, category domains) have nothing in the contract to
  check against. Recommendation recorded: add foreign_keys and domains as
  optional contract fields, defaults, NOT in unresolved -- the missing_values
  argument, that unset is a default rather than a gap. Ranges and not-null
  deferred.

## Phase 7, Step 1 — the ground facts

- P7-D1. KEY UNIQUENESS IS ASKED WITH GROUP BY, NEVER count(DISTINCT).
  count(DISTINCT (x)) is not a row constructor -- it is count(DISTINCT x) and
  drops NULLs -- while count(DISTINCT (x,y)) IS one and treats NULLs as equal.
  So the generic form is right for every composite key it gets tested against
  and wrong for a one-column key: two rows 'a' and NULL, no duplicate, reads
  as one duplicate. GROUP BY ... HAVING count(*) > 1 is null-safe for both
  shapes AND returns the offending values rather than a count of them.
  SCOPE: this is a rule for validate/, NOT a correction to contract/.
  verify_key already documents the difference between the two forms at
  compatibility.py:419 and gathers per-column null counts because of it --
  Phase 4 got there first, and a predicted oversight turned out to be a
  recorded decision. verify_key returns raw counts only -- row_count, distinct,
  per-column null_counts, and a missing list whose early return carries zeroes
  -- so validate/ reads those for the VERDICT and adds one GROUP BY query
  beside it for the OFFENDERS, because a count cannot name the rows and the
  reader's next question is always the values. Two implementations of "is this
  key unique" would eventually disagree with the gate; one implementation and
  one evidence query cannot.
- AND THE ARITHMETIC DIFFERS BY KEY ARITY. One table, 'a' and NULL: as key [x]
  distinct is 1 against 2 rows; as key [x, y] the row constructor counts the
  NULL tuple and distinct is 2 against 2 rows. The same single NULL reads as a
  duplicate in one branch and as unique in the other. So a duplicate-key
  finding and a null-key finding are reported separately rather than both
  derived from one comparison -- which is what compatibility.py:421 means by
  "unique and usable are different questions".
- P7-D2. AN INCLUSIVE WINDOW'S UPPER BOUND IS < end + INTERVAL 1 DAY.
  AnalysisWindow is inclusive at both ends and date_column may be TIMESTAMP.
  dt <= DATE '2024-12-31' casts the bound to midnight and drops
  2024-12-31 23:59:59. Written the obvious way, every window on a timestamp
  column loses its last day silently.
- P7-D3. NOT IN IS BANNED IN validate/. One NULL in the parent column makes
  NOT IN return zero rows, so an orphan check reports a clean pass on a table
  full of orphans. NOT EXISTS is the form. An orphan and a NULL key are
  counted apart -- both are unmatched, only one is a broken reference.
- P7-D4. EVERY CHECK REPORTS FOUR NUMBERS THAT SUM TO THE ROW COUNT: checked,
  passed, failed, not checked. Measured on a window and on a range: a
  predicate does not see NULLs, so inside + outside != rows. P5-D3's principle
  on a new problem -- a cap with the remainder reported, never a sample with
  the shortfall unstated.
- ROW COUNT VS EXPECTATION NEEDS NO NEW FIELD. Binding.row_count is what the
  table held when the contract was confirmed, already stored beside the
  fingerprint. classify_drift computes the same difference as a caveat;
  validation renders it as a pass/fail row.
- CALENDAR COVERAGE IS NOT THIS PHASE. It is Tier 3 (Phase 9) and F10 makes it
  a precondition of TREND analysis, not of validation. A missing month is a
  caveat on a line chart, not a broken dataset.
- P7-D5 IS OPEN. Four of the guide's eight checks (null rules, ranges,
  referential integrity, category domains) have nothing in the contract to
  check against. Recommendation recorded: add foreign_keys and domains as
  optional contract fields, defaults, NOT in unresolved -- the missing_values
  argument, that unset is a default rather than a gap. Ranges and not-null
  deferred.

## Phase 7, Step 2 — the sentence the gate has been printing

- P7-D6. THE DENOMINATOR IS THE ROWS THE KEY COULD HAVE COUNTED.
  KeyVerdict.distinct comes from count(DISTINCT x) for a one-column key and
  count(DISTINCT (a,b)) for a composite. The first drops nulls, the second
  counts a null-bearing tuple, so subtracting distinct from row_count reported
  every null key as a duplicate as well as a null. Measured on the real class:
  rows ('a'),('b'),(NULL) produced "1 row(s) repeat a key that is meant to be
  unique" in the DETAIL line of a KEY_NOT_UNIQUE refusal, on a table where no
  key repeats. keyed_rows names the population; is_unique and duplicate_rows
  use it.
- NO VERDICT MOVES, AND THAT IS WHY IT COULD LAND MID-PHASE. holds requires no
  null in any key column, and with no nulls keyed_rows IS row_count. Every
  refusal the gate raised yesterday it raises today; only the explanation
  changed. Asserted across five key shapes rather than argued.
- A CLAUSE WITH NOTHING TO REPORT IS NOT PRINTED. The duplicate clause now
  fires on duplicate_rows rather than on `not is_unique`, so an all-null key
  stops announcing zero repeats, and an empty table gets its own sentence
  instead of "0 distinct combinations across 0 rows".
- SUPERSEDES P7-D1's SCOPE LINE. Step 1 recorded "this is a rule for validate/,
  NOT a correction to contract/", on the strength of a grep that reached
  verify_key's docstring and not KeyVerdict's arithmetic. verify_key was
  indeed already careful; the class consuming its counts was not. The correct
  scope is both: validate/ adds the GROUP BY evidence query, AND contract/
  gets this fix.
- THE KNOWLEDGE WAS ALREADY IN THE CODEBASE. evidence.py records both null
  rules as numbered findings (Phase 4) and table_profile.py cites them by
  number (Phase 5). KeyVerdict is in the same package as evidence.py and did
  not honour them. A rule documented in one module does not protect arithmetic
  in another, which is the reusable half of this step: the fix was not new
  knowledge, it was knowledge written down twice and not applied at the third
  site. A sweep of src/ for the same shape came back clean: the only other
  row_count - distinct is table_profile._duplicate_rows, which counts
  DISTINCT * -- null-bearing rows included, same population both sides -- and
  the two remaining subtractions take one single-column distinct from another,
  where nulls drop from both sides equally.
- THE DONE-WHEN HAS NO FIXTURE YET. gaps_and_dupes.csv writes 200 unique
  ORD-ids and has no date column; its name refers to duplicate and blank
  COLUMN NAMES, and it is a Phase 3 header fixture. Nothing in tests/fixtures
  is broken in validation's terms, so Step 3 builds one and counts it by hand
  before any rule reads it.

## Phase 7, Step 3 — a fixture that breaks on purpose

- NOTHING IN tests/fixtures WAS BROKEN IN VALIDATION'S TERMS. gaps_and_dupes
  writes 200 unique ORD- ids and has no date column (its name refers to
  duplicate and blank COLUMN NAMES); clean_sales is clean by construction;
  mixed_types breaks on coercion, which is Phase 6's subject. A rule written
  against any of them passes, and a passing rule proves nothing about a check
  whose job is to fail.
- ONE FAULT PER ROW, ENFORCED BY CONSTRUCTION. _broken_row fills every field
  with something valid and each caller overrides exactly one, so the families
  are disjoint and the totals add. A row that was both null-keyed and out of
  window would let a checker be right by accident while getting both numbers
  wrong. Asserted, not intended: test_no_row_carries_two_faults.
- A DIFFERENT COUNT PER FAMILY (3, 2, 4, 5, 6, 7, 8, 9, 10, 11). A rule that
  reads the wrong column reports a number belonging to something else and is
  caught by looking at it.
- THE COUNTS ARE DECLARED, NOT DISCOVERED. BROKEN_BREAKS is the specification;
  the ground-truth test writes the same numbers out again as literals rather
  than importing them, because a test that reads its expectations from the
  generator only asserts that the generator agrees with itself. Phase 6 Step 2
  counted mixed_types.xlsx by hand for the same reason.
- TIMESTAMPS, NOT DATES, AND A ROW IN THE LAST SECOND. P7-D2 cannot be tested
  on a DATE column. The window holds 171 rows written correctly and 170
  written `<= end`; that one row is the regression detector.
- THE LOOKUP CARRIES A BLANK ROW ON PURPOSE. One NULL in the parent column is
  what makes NOT IN return UNKNOWN for every comparison: NOT EXISTS finds 7
  orphans, NOT IN finds 0. Without it the two forms agree and P7-D3 is
  untested. It is also realistic -- the trailing empty line every spreadsheet
  export contributes to a dimension table.
- AN ORPHAN AND A NULL REFERENCE ARE COUNTED APART (7 and 8). Both are
  unmatched; only one is a broken reference.
- PHASE 5'S ACCEPTANCE COUNT IS NOT A CONSTANT. Its clause 1 is written as
  "it runs on every fixture" and loops over tests/fixtures rather than over a
  named list, so adding broken_sales.csv and region_lookup.csv moved it from
  50 to 56 with nothing edited and nothing wrong. That is the right way to
  write the clause -- a fixture nobody profiles is a fixture nobody has
  checked -- but 50 was never a number to carry forward. Current value 56, and
  it moves again the next time a fixture is added.
- DO NOT RUN make_fixtures.py WHOLE. main() rewrites every fixture. Measured:
  the CSVs come back byte-identical, every .xlsx comes back a few bytes
  different because openpyxl is not byte-stable across versions, and
  mixed_types.xlsx carries Phase 6's Done-When counts. Call the two new
  generators directly.

## Phase 7, Step 5 — the date checks and the row count

- P7-D2 IS NOW A NUMBER. The window bound is `< end + INTERVAL 1 DAY`, and
  test_the_window_bound_includes_the_last_second_of_the_last_day asserts 171.
  Written `<= end` it is 170, because the bound casts to midnight and drops
  the last day of a TIMESTAMP column. A decision in this file is one somebody
  can undo without noticing; a decision with a test under it is one they find
  out about.
- THREE DATE CHECKS, NOT ONE. date.present, date.in_window, date.not_future.
  A contract may name a date column and declare no window -- a legitimate
  state -- so in_window reports NOT RUN while the other two still answer.
  One aggregate "date sanity" check would let a missing window silence a
  question about nulls, and would have to pick one outcome for three findings.
- THE SAME SIX ROWS ARE COUNTED DIFFERENTLY BY TWO CHECKS. Undated rows are
  FAILED for date.present and NOT CHECKED for date.in_window, because a row
  that cannot be placed in time at all cannot answer where it falls. P7-D4's
  fourth column is what makes that sayable; without it the window check would
  have to call six undated rows a pass or a failure, and both are false.
- `today` IS INJECTABLE, for the reason store.confirm's `now` is. And the
  future cutoff is `>= today + INTERVAL 1 DAY` -- same shape as P7-D2, same
  reason: a row stamped this afternoon is not tomorrow's data.
- P7-D8. NOT EVERY CHECK IS ABOUT ROWS. "Agreed at 51,290 rows, holds 51,530"
  is true of the table and of no row in particular. Scope.TABLE leaves the
  four counts at zero and carries an explicit table_ok; inventing a per-row
  breakdown would put a number in the report that nothing measured, which is
  PASS-on-unrun wearing different clothes.
- P7-D9. GROWTH PASSES WITH THE DIFFERENCE STATED, LOSS FAILS. No new contract
  field: Binding.row_count is the count the contract was confirmed at and
  classify_drift already computes this difference as a caveat. The asymmetry
  is classify_drift's NEUTRAL and runs.drift_phrase's own distinction -- rows
  appearing is a reload, rows disappearing means the agreement describes rows
  that are no longer there. The alternative (fail on any difference) is
  defensible and makes every table that gained a row overnight fail
  validation.
- P7-D5 STILL OPEN, STILL NOT BLOCKING. Four checks built, none of them
  reading a field that does not exist.

## Phase 7, Step 6 — the pass/fail table

- P7-D10. THE HEADLINE COUNTS THE THREE OUTCOMES AND NEVER COLLAPSES THEM INTO
  ONE WORD. Five failed and one passed is not "FAIL"; five passed and four
  could not run is not "PASS". Both single words are available and shorter,
  and both throw away what P7-D7 exists to preserve -- the difference between
  a question answered and one never asked. A reader who skims one line is the
  reader this is for, so that line has to be true alone.
- FAILURES FIRST, AND THE DENOMINATOR ONCE. "5 of 6 failed, 1 of 6 passed,
  0 of 6 could not run" says the same thing three times, which is how a
  headline becomes something people skip. The total attaches to whichever
  count is named first.
- A THIN CONTRACT MUST NOT READ AS SUCCESS. "no check could run. All 5 say why
  below, and none of them is a pass." A contract naming no key and no date
  column is confirmable -- those fields are optional and `unresolved` is about
  blanks nobody declared -- so this report is reachable, and PASS there would
  be the most expensive sentence in the phase.
- A DASH, NEVER A ZERO, WHERE COUNTING ROWS IS NOT THE POINT. Scope.TABLE and
  NOT RUN both print "-". A zero in a "failed" column reads as "nothing
  failed", which for a check that never ran is a claim nobody made. P7-D8
  reaching the page: a table that prints 0 for those checks has quietly made
  them about rows again. The explanation line appears only when there is a
  dash to explain.
- ROWS A CHECK COULD NOT EXAMINE ARE NEVER ADDED UP. The same six undated rows
  are not_checked for date.in_window and again for date.not_future; a roll-up
  would report twelve uncheckable rows where there are six. The per-check
  column is the honest place, and the report says so rather than leaving the
  arithmetic as a trap for whoever sums the column.
- THE NEXT STEP IS SUPPLIED, NOT GUESSED. report.py does not know its
  workspace, whether a result file was written, or which tools are registered;
  Refusal refuses to construct with a next_call that is not a call for the same
  reason. And it is the wrong guess to make -- duplicate keys can mean "drop
  the duplicates" or "the declared grain is wrong", which are opposite actions.
  render() takes the line it should end with.

## Phase 7, Step 7 — validate_dataset

- P7-D11. VALIDATION DOES NOT GO THROUGH require_contract. The gate refuses a
  dataset whose key does not hold, with KEY_NOT_UNIQUE -- which is exactly
  broken_sales.csv, so routed through it the tool that exists to explain why
  the data is broken would be blocked by the data being broken. It reads
  contract.store.current directly. Not a hole in locked decision 12: nothing
  here computes a number, the handle cannot write, and no caller can turn a
  report into an analysis. The gate names the first thing that stopped it; the
  report names everything it found.
- TWO REFUSALS, AND ONLY TWO: no dataset, no contract. A STALE contract does
  NOT refuse -- a check whose column has gone reports NOT RUN and names it,
  and the rest of the report still runs, which is more information for the
  same reading. No contract DOES refuse, because that report would be a page
  of NOT RUN and P7-D10 already says a page of NOT RUN must not read as
  success.
- P7-D12. A VALIDATION FAILURE IS SETTLED IN THE CONTRACT, NOT IN THE DATA --
  with the tools this project has. Duplicate KEYS whose rows differ are not
  duplicate ROWS; a missing id cannot be invented; a date outside the window
  cannot be moved into it; rows lost since confirmation cannot be restored by
  rewriting the table. So propose_cleaning_plan is the wrong call in every
  case, and naming it would be the defect Phase 6 Step 8 corrected twice: a
  NEXT STEP contradicting the message above it. The report ends with
  propose_dataset_contract, and says looking at the rows first is the other
  option. Everything passing ends with run_analysis instead.
- connect_read_only MOVED TO util/db.py. clean/tools.py named this moment
  itself ("moving it is a one-line change if that reads better later"); a
  second package needing the handle is what "later" meant. clean/tools.py
  imports it and keeps it in __all__, so Phase 6's
  test_the_proposal_connection_cannot_write is untouched. The paragraph that
  described where it lived was rewritten in the same edit -- a docstring
  describing a function's home after it moves is the kind of sentence this
  phase keeps finding.
- NOT TAKEN, ON PURPOSE: the gate's KEY_NOT_UNIQUE refusal could name
  validate_dataset(...) as its next call, which is what a reader of that
  refusal wants next. One line in a Phase 4 file, and it belongs in a step
  that has a reason to open that file.

## Phase 7, Step 8 — the validated stage

- A TABLE BEFORE IT IS A SPLICE. get_workflow_state could say loaded, profiled
  and cleaned, and could not say whether anybody had checked a dataset against
  its contract. Validation writes no file, so there was not even a directory
  listing to infer from -- _agent_validations is the only thing that can
  answer it.
- P7-D13. THE RECORD STORES THE COUNTS, NOT A PATH. profile/runs.py stores
  result_path because a profile is expensive and its output is a CSV somebody
  pages through. A validation report is prose regenerated in one call, and
  writing it to disk would create the F7 shape ON PURPOSE: a path in a
  transcript nobody opens. "Full report: validate_dataset(...)" is a call, not
  a path.
- checks_passed IS DERIVED, NOT STORED. Three numbers that must add to the
  total; storing the fourth is a chance for them to disagree.
- THE ROW COUNT IS STORED, AND IT IS THE F13 DOOR. "validated 40 minutes ago
  at 186 rows, and the table now holds 190." A validation is a statement about
  a table at a moment, and the moment has to sit beside it or the statement
  becomes a claim about data nobody checked. Wording follows Phase 5: OLD, NOT
  WRONG -- an agent told "stale" re-runs, an agent told "wrong" apologises.
- P7-D10 REACHES THE STATE LINE. "2 of 6 passed, 4 could not run", never one
  word. The state line is read faster than the report, so it is the more
  important place for that rule rather than a place it can be relaxed.
- NOT IN DatasetState.stage. Third module, same argument, and it holds a third
  time: that column is about whether ANALYSIS CAN RUN and validation is a
  different axis again. Profiling (Phase 5), cleaning (Phase 6 Step 10c) and
  validation all splice into the per-dataset section, which is why
  describe_workflow_state has needed no new branch since Phase 5.
- THREE CONNECTIONS IN SEQUENCE: writable to read the contract, read-only to
  run the checks, writable to record that they ran. Never two at once. Only a
  report records a run -- the two refusals record nothing, because nothing was
  checked.

## Phase 7, Step 8 — the validated stage

- A TABLE BEFORE IT IS A SPLICE. get_workflow_state could say loaded, profiled
  and cleaned, and could not say whether anybody had checked a dataset against
  its contract. Validation writes no file, so there was not even a directory
  listing to infer from -- _agent_validations is the only thing that can
  answer it.
- P7-D13. THE RECORD STORES THE COUNTS, NOT A PATH. profile/runs.py stores
  result_path because a profile is expensive and its output is a CSV somebody
  pages through. A validation report is prose regenerated in one call, and
  writing it to disk would create the F7 shape ON PURPOSE: a path in a
  transcript nobody opens. "Full report: validate_dataset(...)" is a call, not
  a path.
- checks_passed IS DERIVED, NOT STORED. Three numbers that must add to the
  total; storing the fourth is a chance for them to disagree.
- THE ROW COUNT IS STORED, AND IT IS THE F13 DOOR. "validated 40 minutes ago
  at 186 rows, and the table now holds 190." A validation is a statement about
  a table at a moment, and the moment has to sit beside it or the statement
  becomes a claim about data nobody checked. Wording follows Phase 5: OLD, NOT
  WRONG -- an agent told "stale" re-runs, an agent told "wrong" apologises.
- P7-D10 REACHES THE STATE LINE. "2 of 6 passed, 4 could not run", never one
  word. The state line is read faster than the report, so it is the more
  important place for that rule rather than a place it can be relaxed.
- NOT IN DatasetState.stage. Third module, same argument, and it holds a third
  time: that column is about whether ANALYSIS CAN RUN and validation is a
  different axis again. Profiling (Phase 5), cleaning (Phase 6 Step 10c) and
  validation all splice into the per-dataset section, which is why
  describe_workflow_state has needed no new branch since Phase 5.
- THREE CONNECTIONS IN SEQUENCE: writable to read the contract, read-only to
  run the checks, writable to record that they ran. Never two at once. Only a
  report records a run -- the two refusals record nothing, because nothing was
  checked.

## Phase 7, Step 8b — a validation goes out of date two ways

- THE ROWS MOVE UNDER IT, AND THE AGREEMENT MOVES OVER IT. Step 8 shipped only
  the first. Validate at v2, confirm v3, and the section read "validated
  against contract v2" directly above "Contract v3" with nothing saying the
  check predates the agreement it was quoted against -- and drift_phrase could
  never catch it, because a table that gained no rows reads as freshly
  validated. Found by reading Step 8's own Part 5 output rather than by a test.
- ONE SENTENCE, ONE INSTRUCTION. When both are true the reasons join into a
  single "out of date" line with a single Re-run. Two re-run instructions for
  one stale run is noise and the reader acts on the first either way.
- current_version=None MEANS UNKNOWN, NOT "MATCHES". A caller that does not
  know should not assert a match by omission -- the rule missing_values=None
  already follows on a contract, where unset means use the default rather than
  there are none. state.py passes the version off the StoredContract the
  per-dataset loop already read, so it costs no query, and None where no
  contract is in force.

## Phase 7, Step 9 — the acceptance script

- BOTH CLAUSES BUILD A REAL CONFIRMED CONTRACT. Proposed values, a binding,
  store.confirm -- not the patched contract_store.current the unit tests use.
  A table rendered from a stand-in proves the renderer works and says nothing
  about the path a person takes. It exercises Phase 4 for free: if the model's
  validators or the store move, this fails at the confirm and names which.
- CLAUSE 3 IS P7-D11, ASSERTED. require_contract refuses broken_sales with
  KEY_NOT_UNIQUE and validate_dataset reports five findings on the same table,
  and both are correct at once. If validation is ever routed through the gate,
  this is the clause that notices.
- A SKIP IS NOT A PASS. The first clause 4 read `"list_datasets" in known or
  not known`, which passes when server.py cannot be found and printed
  PASS (server.py not found). A script whose green includes checks that could
  not run is what P7-D7 argues against at the row level, one layer up.
- CONFIRMING A CONTRACT DOES NOT LOOK AT THE DATA. Asserted rather than
  assumed: a contract confirms against broken_sales, whose key does not hold.
  Validation is where the data is checked, which is why P7-D12 sends a failure
  back to the contract rather than to the cleaner.
- "every row carries a order_id" -- FIXED. The article was hard-coded in front
  of a column name in two places, both in the ELSE branch of a check that
  passed, which is why 33 rule tests asserting on counts and on failure
  wording never saw it. Now "no row is missing order_id". Phase 6's closing
  note again: every defect that reaches a live agent is a sentence.

## Phase 7, Step 10b — no tool names a call the reader should not make

- THE STATE ASKS THE GATE. dataset_states computed next_call from contract
  presence and drift alone, so a dataset require_contract refuses with
  KEY_NOT_UNIQUE read as "contract v1, ready" with NEXT STEP run_analysis. dbt
  does not tell you to build a model whose upstream test failed; a status view
  that recommends a call the gate refuses is worse than one that recommends
  nothing. Fixed with verify_key and the SAME cache shortcut require_contract
  uses, so the two cannot disagree -- a second implementation would be the
  P7-D6 shape. Found by a live agent reading two tools' output side by side;
  Phase 4's clause 2 fixture is clean_sales, whose key holds, so no script
  could have caught it.
- AND A HOLE PINNED RATHER THAN CLOSED. The shortcut is a cache keyed on
  "nothing moved", and nothing establishes that the key HELD when the contract
  was confirmed -- store.confirm does not look at the data, deliberately. So a
  contract confirmed against an already-broken key is never re-checked, by the
  gate or the report. dbt has the same separation and also has a test run at
  build time, which this does not. validate_dataset uses no shortcut and
  catches it every time. Closing it properly means running the key check at
  confirm, or keying the cache on a recorded validation rather than a
  fingerprint. Phase 8 or later.
- A ROW-COUNT LOSS NAMES THE LEDGER, NOT THE CONTRACT. The note said "look at
  the rows first" and the NEXT STEP named propose_dataset_contract -- Phase 6
  Step 8's defect class, back in a different tool, and two live readers stopped
  at the same line. P7-D12 is right in direction and premature for this one
  failure: re-confirming at the count the table holds signs a number nobody can
  account for. get_cleaning_ledger is the only call that can rule out an
  approved action, and READING the ledger is not cleaning. A GROWN table keeps
  propose_dataset_contract: rows arriving is a reload, which classify_drift
  calls NEUTRAL.
- THE TIDY, WITH A REASON TO OPEN THE FILES AT LAST. Two imports orphaned when
  connect_read_only moved in Step 7, checked rather than assumed before
  removal; and EXPECTED_TOOLS deduped from 31 entries to 25. A set literal made
  the repeats harmless, which is why they waited; a list a reader checks
  against server.py is worse for holding three names three times each.

## Phase 7, Step 11 — foreign_keys and domains

- P7-D5, DECIDED, AND THE INDUSTRY DECIDED IT. dbt ships four generic tests:
  unique, not_null, accepted_values, relationships. This project already had
  the first two (key.unique, and key.complete as not_null on the key). The
  other two are exactly what Phase 7 deferred, and "table stakes in every
  comparable tool" is a better reason to build them than "the guide lists
  eight" was. Great Expectations and Soda name the same set.
- AND dbt SETTLED THE SHAPE. Those tests are declared in schema.yml beside the
  model, not passed to the command that runs them. So foreign_keys and domains
  go on the CONTRACT, where every other definition lives: an agreement in a
  call argument is not versioned, not exported to docs/contracts/, and not in
  the report.
- RANGES STAY DEFERRED. accepted_range is dbt_utils, not dbt core -- the same
  signal that put the other two above the line, read the other way.
- EMPTY IS A DEFAULT, NOT A GAP, for the third time. Neither field is in
  unresolved. Most datasets reference nothing and constrain nothing, and a
  field that counted as a gap would make every contract in the workspace
  unconfirmable the day it was added.
- A DECLARED COLUMN THE TABLE LACKS IS REFUSED; A REFERENCED DATASET THAT IS
  NOT LOADED IS NOT. bound_to makes the first checkable -- the same condition
  date_column's type check runs under. The second cannot be checked at
  declaration time and should not be: a contract must be readable on a machine
  that never loaded the table, and a foreign key pointing at an absent dataset
  is a check that reports NOT RUN, which is P7-D7 working.
- referenced_columns DEFAULTS TO THE SAME NAMES, filled in at construction so
  the stored contract says what will actually be joined rather than leaving
  the checker to guess. And the key is COMPOSITE-CAPABLE because primary_key
  is: a foreign key that could not reference a composite key could not
  reference half the tables here, order_items among them.

## Phase 7, Step 11 — foreign_keys and domains

- P7-D5, DECIDED, AND THE INDUSTRY DECIDED IT. dbt ships four generic tests:
  unique, not_null, accepted_values, relationships. This project already had
  the first two (key.unique, and key.complete as not_null on the key). The
  other two are exactly what Phase 7 deferred, and "table stakes in every
  comparable tool" is a better reason to build them than "the guide lists
  eight" was. Great Expectations and Soda name the same set.
- AND dbt SETTLED THE SHAPE. Those tests are declared in schema.yml beside the
  model, not passed to the command that runs them. So foreign_keys and domains
  go on the CONTRACT, where every other definition lives: an agreement in a
  call argument is not versioned, not exported to docs/contracts/, and not in
  the report.
- RANGES STAY DEFERRED. accepted_range is dbt_utils, not dbt core -- the same
  signal that put the other two above the line, read the other way.
- EMPTY IS A DEFAULT, NOT A GAP, for the third time. Neither field is in
  unresolved. Most datasets reference nothing and constrain nothing, and a
  field that counted as a gap would make every contract in the workspace
  unconfirmable the day it was added.
- A DECLARED COLUMN THE TABLE LACKS IS REFUSED; A REFERENCED DATASET THAT IS
  NOT LOADED IS NOT. bound_to makes the first checkable -- the same condition
  date_column's type check runs under. The second cannot be checked at
  declaration time and should not be: a contract must be readable on a machine
  that never loaded the table, and a foreign key pointing at an absent dataset
  is a check that reports NOT RUN, which is P7-D7 working.
- referenced_columns DEFAULTS TO THE SAME NAMES, filled in at construction so
  the stored contract says what will actually be joined rather than leaving
  the checker to guess. And the key is COMPOSITE-CAPABLE because primary_key
  is: a foreign key that could not reference a composite key could not
  reference half the tables here, order_items among them.

## Phase 7, Step 11 — foreign_keys and domains

- P7-D5, DECIDED, AND THE INDUSTRY DECIDED IT. dbt ships four generic tests:
  unique, not_null, accepted_values, relationships. This project already had
  the first two (key.unique, and key.complete as not_null on the key). The
  other two are exactly what Phase 7 deferred, and "table stakes in every
  comparable tool" is a better reason to build them than "the guide lists
  eight" was. Great Expectations and Soda name the same set.
- AND dbt SETTLED THE SHAPE. Those tests are declared in schema.yml beside the
  model, not passed to the command that runs them. So foreign_keys and domains
  go on the CONTRACT, where every other definition lives: an agreement in a
  call argument is not versioned, not exported to docs/contracts/, and not in
  the report.
- RANGES STAY DEFERRED. accepted_range is dbt_utils, not dbt core -- the same
  signal that put the other two above the line, read the other way.
- EMPTY IS A DEFAULT, NOT A GAP, for the third time. Neither field is in
  unresolved. Most datasets reference nothing and constrain nothing, and a
  field that counted as a gap would make every contract in the workspace
  unconfirmable the day it was added.
- A DECLARED COLUMN THE TABLE LACKS IS REFUSED; A REFERENCED DATASET THAT IS
  NOT LOADED IS NOT. bound_to makes the first checkable -- the same condition
  date_column's type check runs under. The second cannot be checked at
  declaration time and should not be: a contract must be readable on a machine
  that never loaded the table, and a foreign key pointing at an absent dataset
  is a check that reports NOT RUN, which is P7-D7 working.
- referenced_columns DEFAULTS TO THE SAME NAMES, filled in at construction so
  the stored contract says what will actually be joined rather than leaving
  the checker to guess. And the key is COMPOSITE-CAPABLE because primary_key
  is: a foreign key that could not reference a composite key could not
  reference half the tables here, order_items among them.

## Phase 7, Step 12 — reference integrity and category domains

- dbt's relationships AND accepted_values, on the fields Step 11 added. On
  broken_sales.csv: 7 orphan references over 3 distinct values with 8 nulls
  beside them, and 9 rows holding 2 values outside the channel vocabulary.
  Every number was pinned against the file in Step 3, before a rule existed to
  read it.
- P7-D3 EARNED ITS FIXTURE. The join is NOT EXISTS. region_lookup.csv carries a
  blank row so a regression is visible rather than silent: NOT EXISTS finds 7,
  NOT IN finds 0. Step 1 measured it and this is the step where the wrong form
  would have shipped.
- AN ORPHAN AND A NULL REFERENCE ARE COUNTED APART, 7 and 8. Both unmatched,
  one a broken reference. A NULL foreign key points at nothing ON PURPOSE and
  is optional by design in most schemas, so it is not_checked -- never
  comparable -- and the domain check follows the same rule for the same
  reason.
- THREE WAYS A DECLARED CHECK DOES NOT RUN, each naming what is absent: the
  referenced dataset is not loaded ("the contract is not wrong; the workspace
  is thin"), the far side has no such column (checked here rather than left to
  the engine, because a BinderException from inside a check is a traceback
  where a sentence belongs), and the declared set is empty (which would fail
  every row rather than constrain any).
- THE DOMAIN IS NEVER DERIVED FROM THE DATA. A set read off the column it
  constrains validates the column against itself and passes by construction.
  Step 13 REPORTS the distinct values and leaves the declaring to somebody who
  knows whether a fourth is legal and merely absent -- the shape propose.py
  already uses for analysis_window: reported, never proposed.
- THE EVIDENCE WORDING AND TWO CHECK TITLES WERE SETTLED BY THE TESTS. Drafted
  before the implementation and rediscovered by running them, which is the
  right way round: "Nord (3 row(s)) is not in region_lookup" says what is
  wrong, where "Nord appears 3 times" is the phrasing a DUPLICATE check needs
  and says nothing here.

## Phase 7, Step 14 — reported, never proposed

- THE PROPOSAL STATES WHAT A VOCABULARY COLUMN HOLDS AND DECLARES NOTHING.
  analysis_window's rule on a second field, and propose.py already carries the
  comment. A domain read off the column it constrains validates the column
  against itself and passes by construction, which is worse than no check
  because it looks like one.
- THE FIXTURE MAKES THE ARGUMENT. On broken_sales.csv the region note reads
  "East, Nord, North, Nrth-West, Souh, South, West" -- the three injected
  misspellings sitting beside the four real regions. Anybody who pasted that
  set back would declare the errors legal and the check would pass over all
  seven.
- A VOCABULARY IS TEXT, REPEATING, AND AT MOST TWELVE DISTINCT VALUES -- not
  `suggest_role == "dimension"`. The first version used the role and a
  five-row fixture found it immediately: five rows with five regions makes
  region unique, so suggest_role reads it as an identifier, correctly, because
  counting cannot tell a vocabulary nobody has repeated yet from a name for a
  row. The role heuristic answers a different question; asking for the shape
  directly avoids inheriting its edges.
- NUMBERS ARE LEFT OUT rather than guessed at. evidence.suggest_role already
  says an integer of 1-5 could be a rating to average or a bucket to group by
  and only a person knows which.
- A COLUMN THAT NEVER REPEATS GETS NOTHING. Five rows and five regions could
  be a vocabulary or an id, and saying so would guess in the direction of the
  more useful answer, which is the direction that gets believed.

## Phase 8, Step 1 — the ground facts

- P8-D1. A SHARE HAS A DENOMINATOR THAT CAN BE inf. ieee_floating_point_ops is
  on by default: 1/0 is inf, 0.0/0.0 is nan, both cast to VARCHAR as 'inf' and
  'nan' -- a report cell, not an error. // and % return NULL instead, so the
  rule differs by operator. Every share computes its denominator first and
  refuses on a zero or NULL total with a sentence.
- P8-D2. A SHARE OF A SIGNED TOTAL IS NOT A PROPORTION. Four rows summing to 0
  with sum(abs) 260 produced share = inf, inf, -inf, -inf and a cum_share
  ending at nan on the M1 and -nan on x86 -- the sign of a 0/0 NaN is
  unspecified and the cell is text either way, which is a reason to refuse the
  value rather than special-case it in formatting.py. pareto, concentration
  and ranking_shift count negatives before they run and say how many.
- P8-D3. THE DEFAULT WINDOW FRAME IS RANGE, AND RANGE LUMPS TIES. Four rows
  tied at 10 all read cum_default = 40. ROWS UNBOUNDED PRECEDING with the
  measure descending then the key gives 10/20/30/40.
- P8-D4. LIMIT n OVER TIES ANSWERS A DIFFERENT QUESTION. 100,000 of 300,000
  rows tied at the top; LIMIT 5 returned five of them, the same five on five
  runs at threads=8 -- stable in this measurement, which is not guaranteed and
  is not recorded as either. The defect is the word "top": a tiebreak on the
  key changes the answer entirely (k245760... -> k0...) and both are correct.
  top_n orders with an explicit tiebreak AND reports how many rows tie at the
  cut. And NULLS_LAST is the default both directions, so a column that is 90%
  NULL still returns a full top 5 with nothing saying so -- the null count goes
  in the method note.
- P8-D5. NULL IS A GROUP, AND PIVOT DROPS IT. GROUP BY keeps NULL as its own
  group; PIVOT discarded it -- table total 26, pivot total 23, the missing 3
  being the one NULL-channel row. cross_tab is built from sum(x) FILTER
  (WHERE ...) with an explicit (null) column. It could not have used PIVOT
  anyway: PIVOT ct ON ? is a parser error, so the dimension would have to be
  interpolated as an identifier.
- P8-D6. AN EXCLUSION RULE NEGATED THE OBVIOUS WAY DELETES THE NULLS. Four
  rows, one cancelled, WHERE NOT (status = 'cancelled') kept two. NOT
  coalesce(rule, false) and IS DISTINCT FROM keep three. known_exclusions is
  applied null-safely and every analysis reports four numbers that sum to the
  row count: rows, excluded by the rule, not excluded because the rule was
  NULL, analysed. P7-D4 on a third field.
- P8-D7. util/sql_guard.py IS PHASE 8's FIRST FILE, AND READ-ONLY IS NOT IT.
  con.execute("SELECT ... ; DROP TABLE ex;") dropped the table, on a string of
  exactly the shape known_exclusions[].rule carries. A read-only handle refuses
  the DROP and then still runs the second statement in the same call, and still
  reads any file the process can open -- /etc/hosts 2 rows, /etc/passwd 142
  rows through read_csv on the M1. Read-only guards the catalog, not the
  filesystem. Measured on both machines. duckdb.extract_statements returns 2 for
  the injected string and 1 for a lone statement; json_serialize_sql returns an
  error JSON, without raising, for anything that is not a single SELECT. There
  is no quote_identifier in 1.5.5 (only json_quote) and format does not quote,
  so identifiers are quoted by doubling " in Python.
- P8-D8. sum CAN ABORT AN ANALYSIS. sum(INTEGER) widens to HUGEINT and
  sum(DECIMAL(18,2)) to DECIMAL(38,2), and at the top of each promotion the
  engine raises -- OutOfRangeException and ConversionException. run_analysis
  catches it and names the measure and the type, because a traceback reaching
  the agent is the F1 shape.
- P8-D9. SPREAD ON A GROUP OF ONE IS NULL, NOT ZERO. stddev is stddev_samp; at
  n=1 it is NULL while stddev_pop is 0.0. group_compare prints "not computed
  (n=1)". P7-D10 inside a table cell.
- P8-D10. THE MEDIAN OF A DATE IS A TIMESTAMP THAT IS NOT IN THE COLUMN.
  median of 2024-01-01 and 2024-01-04 is 2024-01-02 12:00:00, typed TIMESTAMP.
  summary_stats on a date column reports quantile_disc or names which it used.
  And avg of INTEGER and of DECIMAL are both DOUBLE while median of DECIMAL
  stays DECIMAL, so two summary rows of one column disagree about type.
- P8-D11. QUANTILES ARE EXACT, BECAUSE ON THE M1 THEY ARE CHEAP. 5M rows:
  exact quantile_cont 0.237s, approx_quantile 0.032s, full summary_stats shape
  0.376s. About 7x, and a quarter of a second is not worth an approximation --
  a report that says "median" should mean median. approx_quantile is not used
  by default; if a table makes it necessary the swap is measured and the
  method_note says which was used, because an approximation nobody was told
  about is a number nobody can audit. Limits on the figure: four columns, in
  memory, no NULLs, one measure, and P5-D3 already found the 28.5M-row cost was
  dominated by TRY_CAST type readings rather than aggregates. It says quantiles
  are not the thing to optimise first, not that wide tables are fast.
- P8-D12. run_analysis ALREADY EXISTS, AND TWO CALL SITES SPELL IT OUT.
  server.py:692, under a header at server.py:22 reading "the gate. Locked
  decision 12 lives here". validate/tools.py:102 prints
  run_analysis(dataset_name="...") with no ellipsis, state.py:282 prints it
  with one, and tests/test_phase7.py:251 asserts the first string exactly. The
  moment analysis_type becomes required, validate_dataset ends by naming a call
  that will be refused for a missing argument -- Phase 6 Step 8 and Step 9's
  defect twice over, and Step 10b's rule that no tool names a call the reader
  should not make. Signature and both call sites land in one step.
- P8-D13. NOTHING BETWEEN AN inf AND THE REPORT. formatting.py matched none of
  inf, nan, round(, :, or float -- it does not special-case numbers at all, so
  P8-D1's inf and P8-D2's nan reach a table cell as the engine produced them.
  The refusal belongs in the analysis, before the value is built; teaching
  formatting.py two spellings of NaN would be repairing the wrong layer.
  results.py already carries Rule 3's 50x50 cap, PAGE_ROWS = 50 and class
  Result, which is the envelope every analysis returns through.
- P8-O1 IS CLOSED, AND THE CODE CLOSED IT. grep "role" in
  contract/dataset_contract.py returns no matches anywhere in the file, and
  evidence.suggest_role's docstring says "Nothing here is authoritative ... The
  suggestion exists so the reader has something to correct." So the guide's
  Phase 8 trap names a field that does not exist on the object analysis reads,
  and the function that does produce a role disclaims the authority the trap
  assumes. THE CONTRACT IS THE AUTHORITY: a primary_key column is never
  summarised as a measure, a numeric column absent from measures is not
  aggregated for being numeric, and the field at dataset_contract.py:299
  ("Columns never to read, distinct from known_exclusions") is honoured too.
  suggest_role may explain a choice in a method note; it decides nothing.
  Step 14's argument on a fourth field.
- P8-O2 IS OPEN. THE HOLE STEP 10b PINNED. The gate's shortcut is a cache keyed
  on "nothing moved" and store.confirm does not look at the data, so a contract
  confirmed against an already-broken key is never re-checked -- and Phase 8 is
  where something behind that gate produces figures a report carries. Close it
  by checking the key at confirm, or by keying the shortcut on a recorded
  validation, which _agent_validations can answer since Step 8. Recommendation:
  the second. Decide in Step 2, before the registry exists.
- P8-O3 IS OPEN. Recommendation: analysis_window and known_exclusions are
  always applied, never arguments, and every method_note carries the four
  numbers plus the window. A number computed outside the signed window is not
  the number the contract describes.

## Phase 8, Step 1 — the ground facts

- P8-D1. A SHARE HAS A DENOMINATOR THAT CAN BE inf. ieee_floating_point_ops is
  on by default: 1/0 is inf, 0.0/0.0 is nan, both cast to VARCHAR as 'inf' and
  'nan' -- a report cell, not an error. // and % return NULL instead, so the
  rule differs by operator. Every share computes its denominator first and
  refuses on a zero or NULL total with a sentence.
- P8-D2. A SHARE OF A SIGNED TOTAL IS NOT A PROPORTION. Four rows summing to 0
  with sum(abs) 260 produced share = inf, inf, -inf, -inf and a cum_share
  ending at nan on the M1 and -nan on x86 -- the sign of a 0/0 NaN is
  unspecified and the cell is text either way, which is a reason to refuse the
  value rather than special-case it in formatting.py. pareto, concentration
  and ranking_shift count negatives before they run and say how many.
- P8-D3. THE DEFAULT WINDOW FRAME IS RANGE, AND RANGE LUMPS TIES. Four rows
  tied at 10 all read cum_default = 40. ROWS UNBOUNDED PRECEDING with the
  measure descending then the key gives 10/20/30/40.
- P8-D4. LIMIT n OVER TIES ANSWERS A DIFFERENT QUESTION. 100,000 of 300,000
  rows tied at the top; LIMIT 5 returned five of them, the same five on five
  runs at threads=8 -- stable in this measurement, which is not guaranteed and
  is not recorded as either. The defect is the word "top": a tiebreak on the
  key changes the answer entirely (k245760... -> k0...) and both are correct.
  top_n orders with an explicit tiebreak AND reports how many rows tie at the
  cut. And NULLS_LAST is the default both directions, so a column that is 90%
  NULL still returns a full top 5 with nothing saying so -- the null count goes
  in the method note.
- P8-D5. NULL IS A GROUP, AND PIVOT DROPS IT. GROUP BY keeps NULL as its own
  group; PIVOT discarded it -- table total 26, pivot total 23, the missing 3
  being the one NULL-channel row. cross_tab is built from sum(x) FILTER
  (WHERE ...) with an explicit (null) column. It could not have used PIVOT
  anyway: PIVOT ct ON ? is a parser error, so the dimension would have to be
  interpolated as an identifier.
- P8-D6. AN EXCLUSION RULE NEGATED THE OBVIOUS WAY DELETES THE NULLS. Four
  rows, one cancelled, WHERE NOT (status = 'cancelled') kept two. NOT
  coalesce(rule, false) and IS DISTINCT FROM keep three. known_exclusions is
  applied null-safely and every analysis reports four numbers that sum to the
  row count: rows, excluded by the rule, not excluded because the rule was
  NULL, analysed. P7-D4 on a third field.
- P8-D7. util/sql_guard.py IS PHASE 8's FIRST FILE, AND READ-ONLY IS NOT IT.
  con.execute("SELECT ... ; DROP TABLE ex;") dropped the table, on a string of
  exactly the shape known_exclusions[].rule carries. A read-only handle refuses
  the DROP and then still runs the second statement in the same call, and still
  reads any file the process can open -- /etc/hosts 2 rows, /etc/passwd 142
  rows through read_csv on the M1. Read-only guards the catalog, not the
  filesystem. Measured on both machines. duckdb.extract_statements returns 2 for
  the injected string and 1 for a lone statement; json_serialize_sql returns an
  error JSON, without raising, for anything that is not a single SELECT. There
  is no quote_identifier in 1.5.5 (only json_quote) and format does not quote,
  so identifiers are quoted by doubling " in Python.
- P8-D8. sum CAN ABORT AN ANALYSIS. sum(INTEGER) widens to HUGEINT and
  sum(DECIMAL(18,2)) to DECIMAL(38,2), and at the top of each promotion the
  engine raises -- OutOfRangeException and ConversionException. run_analysis
  catches it and names the measure and the type, because a traceback reaching
  the agent is the F1 shape.
- P8-D9. SPREAD ON A GROUP OF ONE IS NULL, NOT ZERO. stddev is stddev_samp; at
  n=1 it is NULL while stddev_pop is 0.0. group_compare prints "not computed
  (n=1)". P7-D10 inside a table cell.
- P8-D10. THE MEDIAN OF A DATE IS A TIMESTAMP THAT IS NOT IN THE COLUMN.
  median of 2024-01-01 and 2024-01-04 is 2024-01-02 12:00:00, typed TIMESTAMP.
  summary_stats on a date column reports quantile_disc or names which it used.
  And avg of INTEGER and of DECIMAL are both DOUBLE while median of DECIMAL
  stays DECIMAL, so two summary rows of one column disagree about type.
- P8-D11. QUANTILES ARE EXACT, BECAUSE ON THE M1 THEY ARE CHEAP. 5M rows:
  exact quantile_cont 0.237s, approx_quantile 0.032s, full summary_stats shape
  0.376s. About 7x, and a quarter of a second is not worth an approximation --
  a report that says "median" should mean median. approx_quantile is not used
  by default; if a table makes it necessary the swap is measured and the
  method_note says which was used, because an approximation nobody was told
  about is a number nobody can audit. Limits on the figure: four columns, in
  memory, no NULLs, one measure, and P5-D3 already found the 28.5M-row cost was
  dominated by TRY_CAST type readings rather than aggregates. It says quantiles
  are not the thing to optimise first, not that wide tables are fast.
- P8-D12. run_analysis ALREADY EXISTS, AND ITS SIGNATURE MAKES THE TRAP
  OPTIONAL. server.py:692 takes (dataset_name, question=None,
  workspace_id=None) and delegates to contract_tools.analyse. Three places
  spell the call: validate/tools.py:102 with no ellipsis, state.py:282 with
  one, tests/test_phase7.py:251 asserting the first exactly. A required
  analysis_type would make validate_dataset name a call refused for a missing
  argument -- Phase 6 Step 8 and Step 9's defect twice over, and Step 10b's
  rule that no tool names a call the reader should not make. SO analysis_type
  IS OPTIONAL and the no-type call keeps doing what it does today: the tool
  already answers "the agreement in force, the caveats any result would have to
  carry, and what can be called now", and adding the registry's valid types to
  that answer is the same sentence with more in it -- which Phase 8's Done-When
  requires anyway for an unknown type. No call site changes, no test string
  changes. THE DOCSTRING IS WHAT MUST CHANGE: "The analysis library itself
  arrives in Phase 8 ... Do not report a computed answer from it -- it does not
  compute one" stops being true in the step that makes it compute one, which is
  Phase 7's closing note exactly -- a docstring that stopped describing its own
  signature. Rewritten in the same commit as the behaviour, against Phase 5
  Step 6b's guard. AND question IS ALREADY THERE, UNSPENT: Step 9 decides
  whether it selects an analysis, becomes a note in the method_note, or goes.
  It is not a second name for analysis_type.
- P8-D13. NOTHING BETWEEN AN inf AND THE REPORT. formatting.py matched none of
  inf, nan, round(, :, or float -- it does not special-case numbers at all, so
  P8-D1's inf and P8-D2's nan reach a table cell as the engine produced them.
  The refusal belongs in the analysis, before the value is built; teaching
  formatting.py two spellings of NaN would be repairing the wrong layer.
  results.py already carries Rule 3's 50x50 cap, PAGE_ROWS = 50 and class
  Result, which is the envelope every analysis returns through.
- P8-O1 IS CLOSED, AND THE CODE CLOSED IT. grep "role" in
  contract/dataset_contract.py returns no matches anywhere in the file, and
  evidence.suggest_role's docstring says "Nothing here is authoritative ... The
  suggestion exists so the reader has something to correct." So the guide's
  Phase 8 trap names a field that does not exist on the object analysis reads,
  and the function that does produce a role disclaims the authority the trap
  assumes. THE CONTRACT IS THE AUTHORITY: a primary_key column is never
  summarised as a measure, a numeric column absent from measures is not
  aggregated for being numeric, and excluded_columns ("Columns never to read.
  Distinct from known_exclusions, which is about ROWS") is honoured the way
  cleaning already honours it -- skipped, and said so, which is the field's own
  description rather than a behaviour analysis invents.
  suggest_role may explain a choice in a method note; it decides nothing.
  Step 14's argument on a fourth field.
- P8-O2 IS OPEN. THE HOLE STEP 10b PINNED. The gate's shortcut is a cache keyed
  on "nothing moved" and store.confirm does not look at the data, so a contract
  confirmed against an already-broken key is never re-checked -- and Phase 8 is
  where something behind that gate produces figures a report carries. Close it
  by checking the key at confirm, or by keying the shortcut on a recorded
  validation, which _agent_validations can answer since Step 8. Recommendation:
  the second. Decide in Step 2, before the registry exists.
- P8-O3 IS OPEN. Recommendation: analysis_window and known_exclusions are
  always applied, never arguments, and every method_note carries the four
  numbers plus the window. A number computed outside the signed window is not
  the number the contract describes.

## Phase 8, Step 2 — nothing the caller wrote reaches a connection

- P8-D14. util/sql_guard.py PARSES, IT DOES NOT EXECUTE. Four checks in cost
  order: extract_statements for a second statement, the wrapped form parsing,
  no SUBQUERY in the parse tree, and typeof() = BOOLEAN against the table. Only
  the last touches the caller's connection, and it asks the binder a question
  with LIMIT 1 rather than running the rule over the data.
- P8-D15. A SUBQUERY IS THE QUIET VERSION OF P8-D7. Measured while building:
  "1=1) OR (SELECT count(*) FROM read_csv('/etc/passwd')) > 0 AND (1=1" is ONE
  statement, parses, binds, and types as BOOLEAN -- it passes every other check
  in the file and reads the password file. A rule says which rows of THIS table
  are excluded and has no business opening a second relation, so subqueries are
  refused. The test is structural, on the parse tree: status = 'SUBQUERY'
  contains the word and is an ordinary rule, and a substring match on the
  serialized JSON refuses it.
- AND WHAT THE GUARD DOES NOT DO, RECORDED SO NOBODY ASSUMES IT. Any scalar
  function is allowed -- lower(status) = 'cancelled' has to be. The shape of
  the expression is bounded, not what a function does inside it. Nor does the
  guard know whether a rule is the RIGHT rule: status = 'canceled' against a
  table spelling it with two Ls passes everything and excludes nothing, which
  is why the analysis reports rows actually removed rather than assuming.
- P8-D16. THE WRAPPER PARENTHESISES ON PURPOSE. A rule is checked as
  SELECT 1 WHERE (rule), so a rule ending in a line comment swallows the
  closing paren and fails to parse instead of silently truncating whatever it
  was appended to. status = 'x' -- is refused for that reason.
- UnsafeSQL IS A ValueError, NOT A Refusal. util/ sits below state.py and
  importing it would invert the dependency. The caller that has a Reason to
  hand wraps the message in the instructional refusal 8.2 requires -- which
  means every message here is written to be quoted inside one.
- TWO SENTENCES FIXED BEFORE THEY SHIPPED, both found by reading Part 3's
  output rather than by a test. "this rule is a INTEGER" was Phase 7 Step 9's
  defect exactly ("every row carries a order_id"), an article hard-coded in
  front of a value; it now reads "has type INTEGER, not BOOLEAN" and no article
  is chosen. And a BinderException was being printed whole, so the refusal
  ended with the internal typeof() query and a caret under it -- a line the
  reader never wrote, offered to them as the thing to correct. _engine_message
  keeps everything up to the LINE marker, which keeps "Candidate bindings:
  status" and drops the query. Both have tests now.

## Phase 8, Step 3 — the gate checks the key every time

- P8-D17. THE SHORTCUT IS GONE. require_contract skipped verify_key when the
  fingerprint and row count matched the binding, on the ground that nothing
  could have moved. The claim was true; the inference was not. store.confirm
  does not look at the data, deliberately, so "nothing moved" meant nothing
  moved since a state nobody established -- and a contract confirmed against an
  already-broken key passed the gate forever, precisely because the table had
  sat still. Phase 7 Step 10b pinned this and said Phase 8 or later.
- MEASURED BEFORE REMOVED, and the absolute number is not what decided it. A
  key check on the M1: 0.006-0.008s at 100,000 rows, 0.077-0.179s at 5,000,000
  depending on key shape. Step 1 measured summary_stats' own aggregate shape on
  the same 5M rows at 0.376s. THE GATE'S CHECK COSTS ABOUT HALF THE ANALYSIS IT
  GATES, and 7ms on a table the size of Olist. A shortcut worth a verdict
  nobody computed is not worth that.
- TWO OPTIONS REFUSED. Checking the key at confirm would close it at the source
  and break the separation Phase 7 asserted on purpose -- confirming a contract
  does not look at the data, tested against broken_sales.csv -- and would make
  validate_dataset partly redundant. Keying the skip on a recorded validation
  in _agent_validations is correct but couples the gate to a second module's
  records, and a dataset nobody validated gets the slow path forever. An
  in-process memo was the third, and a mutable module global in a server F13
  says outlives the chat is a worse thing to own than a scan.
- A CORRECTION LOGGED WHILE DECIDING: the third option was written as "make the
  cache a memo of a check that ran", against a cache that does not exist.
  state.py has no store -- the shortcut is a boolean recomputed on every call --
  so there was nothing to un-seed and a memo would have had to be introduced.
  Reading the code changed the option, not just its wording.
- Gate.revalidated IS REMOVED. It was set from `not unchanged`, read by nothing
  but two assertions in test_state.py, and always True once the shortcut goes.
  A field that can hold one value is a question a caller will eventually think
  they asked.
- THREE TESTS WERE NAMED AFTER THE HOLE, and all three were correct about what
  the code did. test_state_gate.py's
  test_a_key_that_never_held_is_not_re_checked_and_both_agree_about_it pinned it
  deliberately -- its docstring is this decision written out a phase early,
  ending "validate_dataset uses no shortcut and catches it every time, which is
  the answer available today", and the shortcut is what stopped being true. A
  test written to pin a limitation is supposed to fail on the day it closes, and
  this one is how the step was known to have landed; it is now
  test_a_key_that_never_held_is_caught_the_first_time_the_gate_runs with its
  three assertions inverted. In test_state.py,
  test_an_unchanged_dataset_skips_the_key_recheck asserted `not
  gate.revalidated` and `gate.key is None` under a docstring of two true
  sentences and a conclusion that did not follow; it is now
  test_an_unchanged_dataset_has_its_key_checked_anyway.
  test_more_rows_revalidate_and_pass_with_a_caveat lost one line and the word
  "revalidate" from its name, since every call revalidates now. The defect was
  never code disagreeing with its tests -- it was all four agreeing on the wrong
  thing.
- ONE FUNCTION, TWO CALLERS. state.py:156 and state.py:276 both ran the
  condition; Step 10b had already fixed them once by making the status view ask
  the gate. _key_verdict is what they both call now, and dataset_states' comment
  no longer says "same cache shortcut", because there is not one.
- THE BEHAVIOUR CHANGE, STATED RATHER THAN DISCOVERED. A key that breaks AFTER
  confirmation now refuses at the next gated call rather than at the next
  structural change. A table someone appended duplicate rows to -- same
  columns, a row count classify_drift calls NEUTRAL -- is refused where it used
  to pass. The KEY_NOT_UNIQUE refusal already reads correctly, so no wording
  changed.

## Phase 8, Step 4 — the rows every analysis is allowed to see

- P8-D18. ONE MODULE DECIDES WHAT "THE DATA" MEANS. analysis_window,
  known_exclusions and excluded_columns are the contract's, so analysis/base.py
  reads them and the nine analyses read it. Nine WHERE clauses would disagree
  eventually, which is P7-D6 with nine copies instead of two. scope_for takes a
  Gate, never a dataset name: locked decision 12 says no analysis without a
  confirmed contract, and a builder that accepts a string is a way around the
  gate, so the type is the enforcement.
- P8-D19. A NULL-SAFE PREDICATE AND A NULL-SAFE COUNT WANT OPPOSITE TREATMENTS
  OF NULL, and the obvious way double-counts. Measured on a seven-row fixture
  before the module existed: excluded 2 + outside_window 2 + no_date 1 +
  analysed 3 = 8, against 7 rows. The undated row was counted twice, because
  the window count was written NOT coalesce((window), false) -- the coalesce
  turns "cannot tell" into "outside". NOT (window) leaves it NULL, FILTER does
  not count a NULL predicate, and the row lands once, in the bucket named after
  why it could not be judged. The predicate has to decide; the count has to
  refuse to. P7-D4 one layer up, where the fix for the first problem causes the
  second.
- rule_unknown IS NOT A FIFTH BUCKET. A row an exclusion cannot judge is KEPT,
  so it is already inside analysed or a window bucket; counting it again breaks
  the sum. It is a qualifier in the method note.
- Scope's CONSTRUCTOR REFUSES A SCOPE THAT LOSES ROWS. CheckResult will not let
  a check under-report; this will not let a scope lose a row. An analysis that
  quietly computed over 900 of 1,000 rows would arrive as arithmetic rather
  than as an error, which is the failure this phase is arranged against.
- P8-D20. THE WINDOW IS INTERPOLATED, THE RULES ARE GUARDED. validate/rules.py
  passes its dates as ? and is right to -- it builds and runs one query. This
  returns a fragment nine analyses paste into their own, and placeholders would
  make each of them responsible for two parameters in the right order. A date
  cannot carry SQL: these come off a validated AnalysisWindow and isoformat()
  is three integers and two hyphens. Exclusion rules ARE caller text and go
  through sql_guard. Interpolation is safe exactly where the value has a type
  that cannot express an attack.
- P8-O4 IS OPEN, AND RECORDED RATHER THAN DISCOVERED LATER. There are now two
  quoting helpers (rules.py's _q, sql_guard.quote_identifier) and two window
  clauses (rules.py's parameterised one, base.py's literal one). Both windows
  implement P7-D2 identically today and could drift apart tomorrow.
  Recommendation: do NOT merge them mid-phase -- rules.py carries 63 acceptance
  assertions and the parameterised form is right for what it does -- but pin
  their agreement with a test that runs both against one fixture and asserts
  the same rows, so a divergence fails rather than ships. Step 10b's precedent
  for waiting was "a reason to open the file"; the test does not need one.

## Phase 8, Step 5 — the registry, and the first thing in it

- P8-D21. summary_stats COVERS THE CONTRACT'S MEASURES, NOT EVERY COLUMN.
  profile_dataset already answers "what is in this table" for every column with
  no contract needed. A second walker would be a second profiler, gated and
  formatted differently, and one day the two would disagree about a number
  somebody had quoted. This answers the narrower question -- what the DECLARED
  measures come to under the contract's window and exclusions -- and names
  everything it did not summarise: key columns, excluded_columns, and numeric
  columns nobody declared. Naming them is what makes the omission a decision
  rather than a mystery. It is also why the cost question evaporated: measured
  at 1M rows x 30 columns, thirty exact quantiles took a query from 1.03s to
  3.97s, and a contract does not declare thirty measures. P8-O1 turned out to
  be a performance decision as well as a correctness one.
- P8-D22. THE DECLARED AGGREGATE IS USED, AND ITS ABSENCE IS NOT A DEFAULT.
  Measure.agg has no default because the guess that gets guessed is sum.
  agg unset -> nothing is totalled and the note names the call that fixes it.
  agg='none' -> a total is WRONG, not undeclared, and does not appear even as a
  convenience; min, max and the counts are still true and are still reported.
  An aggregate the SQL map does not know is refused by name rather than
  computed.
- P8-D23. VALUES KEEP THEIR COLUMN'S TYPE; STATISTICS ARE COMPUTED IN FLOATING
  POINT. Found by rendering the table rather than by a test: mean 15.375 beside
  median 15.37 on the same money column. DuckDB computes median of a DECIMAL at
  the column's own scale -- the median of 10.50 and 20.25 comes back as
  Decimal('15.37') -- so the median is taken as quantile_cont(CAST(col AS
  DOUBLE), 0.5) and the two agree. min and max stay Decimal, because 10.50 has
  two places since somebody declared two; a float's seventeen digits are an
  artifact and are rounded to four.
- A DEFECT THE TESTS CAUGHT: DuckDB returns a DECIMAL column as
  decimal.Decimal, which the first _number() did not handle at all, so money
  would have reached a report cell as Decimal('30.75'). format_table renders
  every cell with str() and rounds nothing, so whatever a function hands it is
  what a reader sees.
- P8-D24. AN ANALYSIS RETURNS Output; THE TOOL LAYER WRITES THE Result. This
  reverses what was said one turn earlier, when Result looked like the natural
  return type. write_result takes a workspace_id, and putting that inside nine
  analysis functions gives all nine the filesystem and makes none testable
  without a workspace. Result stays the ONLY envelope a caller sees -- locked
  decision 20 is untouched -- built in one place from what nine functions
  computed.
- P8-D25. THE REGISTRY DOES NOT CATCH THE ENGINE'S ERRORS. P8-D8's sum
  overflow has to become a refusal naming the measure and the type, but
  building a Refusal in analysis/ would put it above state.py in the import
  graph for the sake of one message. It raises; server.py translates. Same
  reason sql_guard raises UnsafeSQL.
- P8-O5 IS OPEN. table_profile.py passes n.mean straight into format_table,
  which renders with str(), so profile_dataset prints a seventeen-digit mean
  today. summary_stats rounds; the profiler does not; the same number can
  appear both ways in one session. Not fixed here because it is Phase 5 code
  with its own tests, but it is a real inconsistency and it is now written
  down.

## Phase 8, Step 6 — counting into groups, and cutting the list

- P8-D26. THE ORDER IS DETERMINISTIC AND THE TIE IS REPORTED, WHICH ARE TWO
  DIFFERENT FIXES. Every ranking orders by the value then by the group name, so
  the same data gives the same answer twice; and when something ties at the cut
  the note says how many groups shared that value and that the tiebreak, not
  the data, decided which appear. Determinism makes an answer repeatable.
  Saying so makes it honest -- P8-D4 measured that a tiebreak changes the
  answer entirely and that both orderings are correct.
- P8-D27. NULL IS A GROUP CALLED (null). P8-D5, applied: GROUP BY keeps it,
  PIVOT drops it, and '' and NULL are two values not one. A blank cell in a
  frequency table reads as the empty string, so the group is named. The count
  is also stated in the note even when the group falls below the cut -- a
  reader who saw only a truncated table would otherwise conclude the column is
  always populated.
- P8-D28. A SHARE COLUMN IS DROPPED, WITH ITS REASON, RATHER THAN COMPUTED
  WRONG. Three cases and they are not the same: a group total below zero (a
  share of a signed total is not a proportion), an aggregate that does not add
  across groups (avg of avgs has no total to be a share of), and a total of
  zero (x/0 is inf in 1.5.5, not an error, and inf renders as a cell). The
  denominator is computed first and the column is absent with a sentence naming
  which case applied.
- P8-D29. frequency AND top_n REPORT DECLARED DIMENSIONS ONLY. P8-O1 again, and
  the same division as summary_stats: profile_dataset shows the top values of
  every column with no contract; these answer the narrower question and refuse
  an undeclared column with the list of declared ones. Ranking by a measure
  with no agg, or by one declared non-additive, is refused rather than defaulted
  -- P8-D22 is not weaker in a ranking than in a total.
- number AND label MOVED TO base.py. Three analyses need the same formatting,
  and the first one to want it is not where it belongs. Mechanical, tested
  before and after.
- A FIXTURE DEFECT WORTH THE LINE: the test table's amounts were written as
  bare literals, so DuckDB typed the column DECIMAL(3,1) and the test that
  needed to write -100.0 could not -- it failed on its own setup, not on the
  code. Declared casts now. A fixture that cannot express the case it was
  built for is a test that passes for the wrong reason.

## Phase 8, Step 7a — what the contract declares has one home

- DECLARATIONS LIVE IN analysis/declared.py. The aggregate map, aggregate
  spelling, column types, and declared dimension and measure checks moved
  together before distribution and cross_tab become more callers of private
  names. require_measure returns the object the contract holds, not a copy.
  Excluded columns are refused before declaration lookup; absent or None
  excluded_columns means an empty list. No name is stripped or case-folded.
  The helpers raise ValueError and never translate an engine error.
- C7. top_n IS TIER 1. Section 9 puts it beside frequency; Step 6 registered
  it in Tier 2. A test now reads every registered entry against the guide's
  tiers, including entries the next steps will add.
- C8. top_n NOW REFUSES AN EXCLUDED DIMENSION OR MEASURE. frequency already
  checked, but top_n in the same file did not. Both now ask the shared
  declaration helpers, and the excluded-column sentence is unchanged. A real
  contract can hold a column in excluded_columns and also in dimensions or
  measures: the overlap validator checks only
  `both = sorted(set(names) & set(self.dimensions))`. The other validators
  check column existence, date types, foreign keys and domains, not overlap
  with exclusions. P5 constructed a real DatasetContract with region both
  declared as a dimension and excluded, and a defined sum measure.
- C9. A MEDIAN TOTAL USES THE SAME DOUBLE QUANTILE AS ITS MEDIAN COLUMN.
  Measured on DuckDB 1.5.5: median over DECIMAL(18,2) values 10.50 and 20.25
  returns Decimal('15.37'); quantile_cont(CAST(col AS DOUBLE), 0.5) returns
  15.375. The map now uses the latter. The rendered total and median both read
  15.375. Every map value is one aggregate call accepting FILTER (WHERE ...).
  P2 measured a NULL-only cell: sum returns None, count and count_distinct
  return 0. A report must render what the aggregate actually returned.
- INTEGER TYPES ARE EXACT NAMES, INCLUDING UHUGEINT. is_integer strips and
  uppercases the type name and tests equality against the ten signed and
  unsigned integer types. P3 measured isfinite(3::T) as True for all ten.
  Integer array types are not scalar integers. The numeric-prefix helper
  moved without changing its type set; UHUGEINT remains absent from that set.
- LostRows IS A ScopeError. An analysis whose output does not add back to the
  rows its scope allowed has a named ValueError subtype ready for 7b and 7c.
  No analysis was added in this step.
- C10. "avg" WAS A KEY NO CONTRACT CAN DECLARE. Aggregation is a Literal whose
  mean is spelled "mean"; three summary_stats tests declared "avg" through a
  FakeMeasure the real Measure rejects, and one assertion echoed it back. Four
  lines changed and were run against the unchanged module first: the total
  stayed 2.6667, so the substitution is neutral and only the label follows its
  input. The real Measure now refuses "avg" in a test. Written in the Step 5
  guide; caught by Step 7a's stop A.
- C11. Aggregation IS A Literal, NOT AN ENUM. The spec's tests and the
  aggregate helper's docstring described a shape nobody had read. Tests now
  inspect the type with get_args; agg_of reads the declared string or None,
  without an enum-value branch. Its callers do not acquire a default.
- THE CONTRACT SPELLS ITS AGGREGATES TWICE. Aggregation and AGGREGATIONS are
  two spellings of one list, now pinned equal in value and order by a test.
  AGG_SQL's keys are exactly that list minus none, with no tolerated alias.
- STOP B, ANSWERED. MAX_ROWS and MAX_COLS come from util/formatting.py.
  analysis/ never imports util/results.py, because results.py imports
  workspace. The tool layer remains responsible for writing the Result.
- P8-O8 IS OPEN. is_numeric matches by prefix. P4 measured INTEGER[] and
  DECIMAL(18,2)[] as numeric=True, integer=False; UHUGEINT as numeric=False,
  integer=True; INTEGER as numeric=True, integer=True. This move leaves the
  numeric predicate unchanged; the result is recorded rather than repaired.
- C13. THE GATE STATED AN EDIT'S SIZE BEFORE THE READ THAT MEASURED IT. r1 said
  three lines; the same dispatch's R12 covered line 145, which renders the
  aggregate's name. Stop F caught it at a cost of one round trip. A dispatch
  states an edit's extent only after the read that establishes it.
- C12 NOT RAISED. R8's single-line grep could not match a sentence split across
  two f-strings; R13 read it with context and the quoted sentence was right.
- P8-O9 IS OPEN. Is agg=None reachable behind the gate? _cross_field_checks
  allows it only while agg_path is in unresolved, and is_confirmable is `not
  unresolved`. R15 and the confirm body at contract/store.py:249 show
  `if not contract.is_confirmable: raise ContractRefused(...)`. P5 constructed
  the unresolved None-aggregate contract and printed is_confirmable=False.
  Through normal confirmation, that state cannot be stored; the missing-agg
  branches are defensive on that path. They stay. No direct catalog tampering
  or bypass path was probed, and the broader gate audit remains open.
- P8-O10 IS OPEN. The stand-ins are looser than the models, which is how C10
  survived two steps. Step 10's acceptance runs every analysis through a real
  DatasetContract and a real gate.
- MEASURED VALIDATION. Step A: 19 passed against unchanged source. The 49
  existing analysis tests passed before and after the move. The 15 new tests
  passed, and the full suite rose from 1140 to 1155 passed. The old private-name
  search is empty. The quoted-avg search has one intentional match in the new
  real-Measure rejection test; requiring that regression while expecting an
  empty search is contradictory. No source map or accepting fixture retains
  the alias. The test stays visible to the audit.

## Phase 8, Step 7b.0 — a type is read by its whole name
- P8-D30. IS_NUMERIC COMPARES THE WHOLE BASE NAME. NUMERIC_TYPES is
  INTEGER_TYPES + FLOAT, DOUBLE, DECIMAL. REAL is gone: DuckDB 1.5.5 writes REAL
  and FLOAT4 back as FLOAT. _base_type drops a trailing (...) and returns a list
  type whole, and a name containing [ is never numeric. .upper() is kept and no
  .strip() is added (R7). Step 7b.0 Part 4 printed UHUGEINT numeric=True and
  INTEGER[], DECIMAL(18,2)[], INTEGER[3] numeric=False (container; M1 reported
  match, not pasted).
- P8-O8 IS CLOSED by P8-D30.
- P8-D31. BIGNUM IS NAMED, NOT COMPUTED OVER. DuckDB writes a declared VARINT as
  BIGNUM. ARBITRARY_PRECISION_TYPES = ("BIGNUM",) and is_arbitrary_precision
  name it; is_numeric and is_integer return False for it, so no analysis that
  branches on them computes over it. The retired Codex spec called this ruling
  S7b-r1; that was never logged, and this entry replaces it.
- P8-D32. EXCLUDED_COLUMNS IS READ AS A PLAIN ATTRIBUTE. require_dimension and
  require_measure read contract.excluded_columns with no getattr and no `or []`,
  so a renamed field raises AttributeError. Refusal strings are byte-identical:
  no diff line of declared.py touches them. A real contract cannot hold None:
  dataset_contract.py:297 is list[str] with default_factory=list; src has no
  model_construct, validate_assignment or `excluded_columns = None`; its one
  model_copy (store.py:282) updates only version and confirmed_at.
  summary_stats.py:66 and base.py:246 already read the field this way.
- P8-D33. TWO 7a TESTS LOST THEIR TOLERANCE CASES.
  test_require_dimension_refuses_an_undeclared_column_with_the_list and
  test_require_measure_returns_the_measure_object asserted that None and a
  missing attribute were accepted, which P8-D32 removes. Each keeps an
  excluded_columns=[] case, and the new missing-attribute test asserts the
  refusal. Approved by Akash, 11 Sep 2026.
- P8-O11 IS OPEN. Two readers still default silently: declared.py
  dimension_names reads `getattr(contract, "dimensions", []) or []`, and
  clean/tools.py:185 reads `getattr(contract, "excluded_columns", ()) or ()`.
  Both are outside 7b.0's fence.
- P8-O12 IS OPEN. BIGNUM in the analyses. Measured on DuckDB 1.5.5 (container;
  M1 reported match, not pasted): min, sum and median return BIGNUM, which
  Python receives as str; avg, stddev_samp and quantile_cont return DOUBLE.
  10::BIGNUM::HUGEINT raises "Positive bignum too large for type", as did every
  non-zero BIGNUM cast to HUGEINT or UHUGEINT that was tried; ::BIGINT works.
- P8-O13 IS OPEN. 128-bit integers against bound parameters, to be ruled on in
  7b.1. Binding the Python int 5 against a UHUGEINT column plans CAST(u AS
  BIGINT) > 5, which errors on values above 2^63-1; the literal u > 5 and u >
  ?::UHUGEINT both work. UHUGEINT plus a bound int returns DOUBLE. sum() over
  UHUGEINT returns DOUBLE on both summary_stats paths, before and after 7b.0
  (container).
- C14. CODEX LOOP RETIRED. The architect-plus-Codex loop put two layers between
  Akash and the code, and each sub-step took three or four round trips where a
  step guide takes one. Verification came from Akash's terminal either way, so
  the loop added cost and gave nothing back. The step-guide method is restored
  from 7b.0 on. AGENTS.md (c155646) stays committed and inactive.
- C15. R6 AGAINST THE 7a TESTS. Predicted: R6 with R7 leaves every existing test
  passing, for +6. Measured: 2 of the 7a tests failed under R6 (container).
  Because: the 7b.0 scope was written from a description of the getattr read
  without reading tests/test_declared.py.
- C16. A LINE RANGE WHERE TWO LINES PRINTED. Predicted is_numeric uses at
  test_declared.py:151-153; printed 151 and 153. Because: a range was written
  for the block, and line 152 is its for line.
- C17. A BYPASS SEARCH WRITTEN FROM MEMORY. Predicted: an empty search for
  model_construct, validate_assignment and `excluded_columns = None` rules out
  None. Measured: model_copy(update=...) and setattr also skip validation
  (pydantic 2.13.4, container). Because: the bypass list was recalled, not
  measured. A second search closed it.
- C18. A RECURSIVE GREP WITHOUT --include. Predicted test file paths only;
  printed two tests/__pycache__ .pyc files as well. Because: the flag was on the
  neighbouring commands but not this one, and the mock repo had no matching file
  to expose it.
- C19. CITED ENTRIES THAT WERE NEVER LOGGED. The 7b.0 scope cited P8-O12, C15
  and S7b-r1 as logged; a search of every .md file in the repo found none.
  Because: numbers drafted in the retired Codex spec were treated as logged. The
  P8-O12 and C15 in this entry are new numbers, assigned in order.
- C20. THE C-NUMBER SEARCH READ ACTION IDS. Predicted: the next-free-C command
  prints the highest correction. Printed C099, a zero-padded cleaning action id
  (see PER-PLAN ACTION IDS); corrections are unpadded. Because: the pattern
  accepted any C followed by digits, and it was verified on a sample with no
  action ids. Replacement:
  grep -oE '(^|[^A-Za-z0-9_])C[1-9][0-9]*' docs/decisions.md | tr -dc 'C0-9\n' | sort -t C -k2 -n | uniq | tail -1
- C21. THE BUILD GUIDE'S NAME. Predicted analytics_agent_build_guide_v1_2.md;
  the file is docs/analytics_agent_build_guide_v1.2.md. Because: the name was
  copied from the working instructions without being measured.
- C22. LEDGER LINES ASSUMED. Predicted the build guide names Step 7 sub-steps; a
  search for Step 7, 7b and 7c printed nothing. Because: "progress ledger" was
  read as step-level, and line 33 says a box is ticked when a phase passes its
  Done-When test.
- MEASURED VALIDATION. test_declared.py printed 15 passed before (Akash's
  terminal). After, 21 passed and the full suite 1161 passed, reported by Akash
  as matching, output not pasted; the baseline 1155 is from the 7a entry. The
  step guide phase8_step7b0_type-predicates.md holds the container outputs.

## Phase 8, Step 7b.1 — distribution
- P8-D34. BINS ARE BOUND EDGES, NOT FLOOR DIVISION. floor((x - min) / width)
  over 0.0..1.0 in tenths filed 0.3, 0.6 and 0.7 one bin low -- 0.3/0.1 is
  2.9999999999999996 -- and put the maximum in bin 10 of 0..9. Edges are min +
  (max - min) * i / n in Python, first and last set to min and max themselves,
  bound as parameters; a value belongs to [lo, hi), the last bin to [lo, hi].
- P8-D35. A BOUND EDGE CARRIES THE COLUMN'S OWN TYPE. Closes P8-O13. A bare ?
  against a UHUGEINT column makes DuckDB cast the COLUMN: the plan reads CAST(u
  AS BIGINT) > 5, which raises ConversionException on any value above 2**63-1.
  The integer path binds CAST(? AS dtype) instead, measured working on INTEGER,
  BIGINT, HUGEINT, UHUGEINT and UTINYINT, and a UHUGEINT measure spanning
  0..2**128-1 binned correctly. Before 7b.0 this column was not numeric and
  never reached the query.
- P8-D36. A MEASURE THAT NEVER VARIES IS ONE BIN, NOT AN ERROR. (x - min) / 0.0
  is nan and floor(nan)::INT raised ConversionException, so a constant column
  aborted the query. Edges are computed in Python and lo == hi falls out as one
  bin with no division anywhere.
- P8-D37. inf AND nan ARE COUNTED, NOT BINNED. One nan made max() nan and one
  inf made p75 inf. isfinite() binds on integer, decimal and double alike; the
  non-finite count is a sentence, and neither bins nor quantiles see them.
- P8-D38. AN INTEGER MEASURE HAS WHOLE-NUMBER BINS. 1..5 in ten bins of 0.4 left
  five bins empty by construction. Width is ceil(span / bins) and the note says
  when that yields fewer bins than asked: the fixture's rating asks for 10 and
  gets 5.
- P8-D39. distribution NEEDS A DECLARED MEASURE, NOT A DECLARED AGGREGATE. It
  totals nothing, and P8-D22's refusals exist to stop a wrong total. It says so
  when agg is unset or 'none' rather than behaving differently from
  summary_stats without a word.
- P8-D40. MAX_BINS COMES FROM util/formatting.py. The Step 7 spec said
  results.py, and that read stopped the step: results.py has PREVIEW_ROWS 20,
  PREVIEW_COLS 12 and PAGE_ROWS 50 but no 50x50 constant, and it imports
  analytics_agent.workspace and contract.refusals, so analysis/ importing it
  would invert the import graph. formatting.py holds MAX_ROWS and MAX_COLS and
  has no module-level imports.
- P8-O14 IS OPEN. Two sources of truth for the inline caps. util/formatting.py
  defines MAX_ROWS and MAX_COLS; config.py defines MAX_INLINE_ROWS and
  MAX_INLINE_COLS with a comment at line 209 saying formatting.py should point
  at them. distribution reads formatting's. Whichever survives, one has to go.
- THE ENGINE'S BINS ARE NOT USED. equi_width_bins with nice rounding moved
  3..977 to 100..1000; without it the edges carry 0.10000000000000014; and
  histogram() with boundaries is upper-inclusive with an implicit inf bin. Each
  is a convention nobody here chose.
- THE MEDIAN AGREES WITH summary_stats, pinned by a test on one fixture:
  quantile_cont on DOUBLE gives 9.375 where median(DECIMAL) gives 9.37.
- LostRows IS A GUARD WITH NO TEST. distribution counts its bins and its finite
  values from the same WHERE, so a scope that under-reports cannot make them
  disagree, and the branch cannot be reached from outside. It stays as a guard
  against a future change to either query. cross_tab's LostRows, which compares
  cells against scope.analysed, is reachable and is tested in 7c.
- C23. THE LEDGER WAS LEFT SAYING NOT STARTED. Step 7b.0 ruled that the build
  guide needed no update because Phase 8 is not finished. Section 12 offers
  three states and Phase 8's row still read Not started after seven committed
  steps, so the ruling was made without reading the section. The row reads In
  progress from this step on.
- MEASURED VALIDATION. tests/test_distribution.py: 23 passed. Full suite 1161 ->
  1184. Every expected value in the spec's 3.6 reproduced in the container
  against the real base.py and registry.py before the guide was written.

## Phase 8, Step 7c — cross_tab
- P8-D41. A CELL IS AN AGGREGATE FILTERED BY A BOUND VALUE. sum(x) FILTER (WHERE
  col IS NOT DISTINCT FROM ?), the values bound. = ? found no NULL row; IS NOT
  DISTINCT FROM found it, found '', and found B's without escaping, because a
  data value never enters the SQL text. P8-D20's other half: parameters are
  right where the query is built and run in one place.
- P8-D42. A GROUP COUNT COUNTS NULL. count(DISTINCT channel) said 4 where there
  were 5 groups, so a cap checked that way admits one column too many. Counted
  as SELECT count(*) FROM (SELECT DISTINCT ...), before the table is built, and
  the cap includes the (total) row and column so the whole table fits 50 x 50:
  MAX_ROW_GROUPS is MAX_ROWS - 1 and MAX_COLUMN_GROUPS is MAX_COLS - 2, both
  from util/formatting.py per P8-D40.
- P8-D43. MARGINS ARE COMPUTED FROM ROWS, IN A SECOND QUERY. North's mean is
  18.75; the mean of its cells is 15. And GROUPING SETS returned two rows both
  called NULL -- the NULL group and the grand total -- so totals come from the
  same expression strings with no GROUP BY.
- P8-D44. A BLANK CELL AND A ZERO ARE DIFFERENT ANSWERS. count over no rows is 0
  and is shown as 0; sum over no rows is NULL and is shown blank, with a
  sentence. South x Retail is blank although a row exists: its amount is NULL.
- P8-D45. THE CELLS MUST ADD BACK TO THE SCOPE. PIVOT on this step's fixture
  summed to 112.00 of 117.00 and named the '' column after its own generated
  SQL. cross_tab reconciles the body's row counts, the totals row and
  scope.analysed, and raises LostRows rather than print a table that quietly
  lost a group. Unlike distribution's guard (7b.1), this one is reachable and is
  tested.
- P8-O15 IS OPEN. results.py previews 12 columns; a cross_tab may have 50.
  Whether read_result_file pages columns as well as rows decides whether the
  model can see the rest -- Step 9, where the tool layer writes the Result.
- P8-O16 IS OPEN. top_n gives a share only for agg='sum', but count adds across
  groups too, so a count ranking loses its share with a sentence that is not
  true of it. pareto and concentration need the same 'which aggregates add'
  answer; Step 8 decides it once, in declared.py.
- C24. A HEREDOC TERMINATOR WAS GLUED TO THE LAST LINE OF CODE. The 7b.1 guide
  was assembled with shell command substitution, which strips trailing newlines,
  so a file's last line read label="distribution")PY and the heredoc never
  closed: the shell swallowed the rest of the script into the file. Caught by
  extracting the commands back out of the finished guide and running them, which
  is what rule 3 is for. Guides are assembled in Python from now on, and every
  block is checked to end in a newline.
- C26. A BANNED-CONSTRUCT GREP MATCHED THE DOCSTRING. The 7c guide's check for
  banned imports and SQL searched for bare words -- PIVOT, contract, state --
  and the module names all of them in its docstring, explaining what it does
  instead. Printed nine lines of prose where the Check said nothing. Caught by
  extracting the command back out of the guide and running it. The pattern
  matches the SQL spellings and the import lines now, and the Check gives the
  five imports literally.
- C25. frequency.py WAS CALLED CUT SHORT. The 7b.1 guide said the upload cut
  frequency.py off at line 50 and that 7c would need to read its tail. The
  upload holds all 216 lines; only the excerpt displayed in chat stopped at 50.
  No extra read was needed.
- MEASURED VALIDATION. tests/test_cross_tab.py: 24 passed. Full suite 1184 ->
  1208. The count, sum and mean tables, the group counts and the PIVOT shortfall
  all reproduced in the container against the real base.py and registry.py
  before the guide was written.

## Phase 8, Step 8a — which aggregates add across groups
P8-D46. sum AND count ADD ACROSS GROUPS; NOTHING ELSE DOES. Every analysed row lands in exactly one group and is counted once, so the group totals sum to a total the table shares. count_distinct does not, and the Step 6 fixture proves it rather than illustrating it: 7 distinct amounts in the table, 8 when the per-group distinct counts are summed, because 20.00 is in both North and South. mean, median, min and max do not — min and max recombine, but there is no total for a group to be part of. Closes P8-O16. pareto and concentration ask declared.adds_across_groups rather than re-deciding it.
P8-D47. THE THREE SHARE REFUSALS ARE ONE FUNCTION, AND THE DENOMINATOR IS STATED. P8-D28's cases moved to base.share_basis before a third and fourth caller wrote them again, in the order non-additive, negative, zero — an aggregate that does not add is refused before its values are inspected, because their signs are not the reason. And the denominator is not always the analysed rows: AGG_SQL spells count as count(col), which skips a null measure, so a count ranking over the fixture with one null amount divides by 7 while the method note says 8. The sentence names the number and says when it differs.
P8-D48. THE INLINE CAPS LIVE IN formatting.py AND config's PAIR IS DELETED. The comment at config.py:209 asked the opposite. Measured: formatting.MAX_ROWS had four readers outside its module, config.MAX_INLINE_ROWS had one, config.MAX_INLINE_COLS had none, and config.py imports yaml and subprocess at module level where formatting.py imports nothing — so following the comment would hand every analysis/ module that graph, which is P8-D40's objection to results.py with a worse payload. run_sql's fetchmany cap and format_table's row cap both cite guide 8.1 Rule 3, so one constant is right. Closes P8-O14.
C27. A NUMBERED LIST WAS PASTED INTO A SHELL, THEN A COMMENTED ONE. A file-request block numbered its commands 1.  cd ..., giving eleven command not found; the replacement moved the numbers into # comments, which zsh does not honour interactively without interactive_comments, so # 9 config's side opened an unterminated quote and the shell swallowed the rest. Because: C24 and C26's rule — extract the commands back out and run them — was applied to guides and not to a block written in chat, and the second attempt guessed at the shell's behaviour instead of measuring it. A paste-able block carries commands only.
C28. A CHECK DEFEATED BY ITS OWN EDIT, AND A RECURSIVE GREP WITHOUT --include AGAIN. Part D deleted config's cap pair and left a comment saying so, naming MAX_INLINE_COLS; the step's own check then grepped for MAX_INLINE and printed that comment, plus two matching .pyc files. Because: the check was written against the code being removed and not against the file the edit would leave behind, which is C26 in a new place, and the --include flag was on the earlier reader-census grep but not on this one, which is C18 exactly. The comment states the ruling without spelling the deleted names, and every recursive grep in these guides carries --include='*.py'.
C29. A NESTED HEREDOC TERMINATOR CLOSED THE OUTER ONE. The script that rewrote a guide's Section 6 was itself a heredoc, and the text it inserted contained a bare terminator line of its own, so the shell ended the script there and ran the remainder of the replacement text as commands. Nothing was written: the truncated script failed to compile before reaching its write. Because: C24 fixed the terminator-glued-to-code case and was read as "check the last line" rather than "a terminator is any bare match on its own line". An assembling script uses a terminator its payload cannot contain.
C30. THE BLOCK CHECK RAN ON OUTPUT BLOCKS AND PASSED BY LUCK. The extract-and-check pass ran sh -n over every fenced block without separating commands from pasted output. 1208 passed in 28.79s and server imports clean are valid shell, so four output blocks were reported clean alongside the commands; the first output containing parentheses failed and revealed it. Because: the checker was written when every fence held commands and was not re-examined once measured output started going in. It classifies on the leading cd line now and reports the two counts separately.
MEASURED VALIDATION.
## Phase 8, Step 8b — group_compare
P8-D49. role IS A PROPOSAL-TIME HEURISTIC, NOT A CONTRACT FIELD. The Phase 8 trap says to enforce role=identifier. Measured: role appears in contract/evidence.py and contract/propose.py and never in dataset_contract.py — suggest_role decides what becomes a measure or a dimension at proposal, and the confirmed contract stores the outcome, not the reason. No analysis can ask a contract for a role. The trap's intent is met by P8-D29: an analysis reports declared columns only, and summary_stats names primary_key among what it skipped. Step 10's acceptance tests the behaviour, not the field.
P8-D50. THE STATISTICS MOVE TO analysis/stats.py. group_compare needs the seven numbers summary_stats computes. Written twice they drift, and C9 measured exactly how: median over a DECIMAL(18,2) returns Decimal('15.37') where quantile_cont(CAST(col AS DOUBLE), 0.5) returns 15.375. A group median spelled the first way disagrees with the same column's median one table up and both are correct. Not declared.py: its subject is what a contract declares, and nobody declares stddev.
P8-D51. THE BASELINE IS AN (all) ROW, NOT A NAMED GROUP. Unparameterised is what pareto and concentration reuse, and "this group against the dataset" is the question a comparison answers before "compared to North". A named baseline is a filter over one bound value — a later argument, not a different design. P8-D43 gives the mechanism: the same expressions with no GROUP BY, in a second query, never a combination of the group rows. The fixture proves it: both groups hold one value each, so every group stddev is blank, and no recombination of blanks produces the (all) row's 6.8943.
P8-D52. GROUPS ARE ORDERED BY NAME, AND THERE IS NO TIE NOTE. A comparison is read by group; a ranking is read by value. ORDER BY 1 NULLS LAST on the group name is deterministic without a tiebreak because a group name appears once, so P8-D26's tie note has nothing to report. top_n is the ranking.
P8-D53. THE TOTAL COLUMN IS NAMED FOR ITS ROLE, NOT ITS AGGREGATE. The prototype headed it {agg} ({unit}), which put mean (GBP) beside the mean statistic and, with no unit declared, produced two columns called mean. cross_tab's label check refuses exactly that collision one analysis over. It is total, as summary_stats names it, and the aggregate is named in the summary sentence.
MEASURED VALIDATION.
## Phase 8, Step 8c — pareto and concentration
P8-D54. THE BUILD GUIDE NAMES TIER 2 AND DEFINES NONE OF IT. Section 9 gives four names; mix_shift and correlated_shift get explanatory sentences and these two get nothing. So pareto is rank, share, running share and a threshold, and concentration is CRn plus HHI — chosen from standard practice, not read out of the guide. Anything Step 10 accepts against these is accepting a choice made here.
P8-D55. pareto REFUSES WHERE top_n DEGRADES. Both ask share_basis. A ranking without shares is still a ranking; a Pareto curve without shares is nothing, so the refusal is raised rather than printed beside an empty column.
P8-D56. HHI IS A NUMBER, NOT A VERDICT. Its 1,500 and 2,500 thresholds describe product markets. The output gives the index, its floor for the group count in hand, and what it sums — and names why the thresholds are withheld. Printing "highly concentrated" over a breakdown by status or warehouse would be a claim about competition nobody made.
P8-D57. THE RUNNING SHARE ACCUMULATES TOTALS. Adding printed shares adds numbers rounded for a reader. The accumulator keeps the column's type and divides once per row; the last row reading exactly 100.0% is the test.
MEASURED VALIDATION.
Phase 8, Step 8d — ranking_shift
P8-D58. TWO PERIODS ARE ARGUMENTS AND NARROW WITHIN THE SCOPE. A contract holds one AnalysisWindow, so two periods cannot come from it. Building a second Scope inside an analysis would break the agreement between a method note and the rows under it, so each period is ANDed into scope.where instead and ranked_totals grew an optional extra for it.
P8-D59. A PERIOD IS NOT THE SCOPE, AND THE REMAINDER IS REPORTED. Rows before, between or after the two periods are in scope and in neither column. The count is stated, because the two period counts do not add to the analysed total and a reader should not have to find that out by subtraction. The fixture's February row, worth more than any other, is in neither period — if either bound leaked, north would rank first instead of third.
P8-D60. ARRIVING AND LEAVING ARE LABELLED, NOT SCORED. A group present in one period only has no rank in the other. new and gone rather than a computed change: a blank treated as zero reads as stability, which is the opposite of what happened.
C31. A GUIDE'S PATCH SCRIPT CANNOT ANCHOR ON A DOCSTRING. A Part A script anchored on text containing """, and the f-string assembling the guide broke on it. The replacement anchors on a plain comment line and inserts after it. An assembling script and its payload cannot share a delimiter — C29's rule, one quote-level down.
MEASURED VALIDATION.
## Phase 8, Step 9a — compute_analysis, the tool layer
P8-D61. run_analysis IS KEPT AND A SECOND TOOL COMPUTES. It is Phase 4's gate, cited by name in state.py, validate/tools.py and six test files. Widening it would make its signature conditional; replacing it would break every citer. compute_analysis takes the conditional signature nine analyses need, and nothing that cites run_analysis changes.
P8-D62. FOUR REASON CODES, ONE PER RECOVERY. NOT_FOUND is answered by the catalogue, PARAMS_INVALID by fixing the call, NOT_POSSIBLE by the contract, RESULT_UNSOUND by nobody. The eval counts recovery per reason, so one code covering several recoveries measures none of them. COLUMN_NOT_FOUND was rejected: its comment says the table does not have the column, and an undeclared dimension usually exists in the table.
P8-D63. ParamsInvalid SEPARATES A BAD CALL FROM A BAD FIT. Measured: without it an unparseable date and an undeclared dimension both returned NOT_POSSIBLE, which tells a caller to re-confirm a contract when the fix is to retype an argument. Two of four codes had silently merged. A ValueError subclass, so no existing test moved.
P8-D64. IMPORTING analysis/ REGISTERS EVERY ANALYSIS. Measured: three of nine offered in an unknown-type refusal, because the registry fills by import side effect — and the Done-When is that an unknown type returns THE valid list. Seven modules, nine analyses: frequency.py holds frequency and top_n, pareto.py holds pareto and concentration.
P8-D65. THE METHOD NOTE IS VERIFIED BEFORE ANYTHING IS WRITTEN. Nine analyses put it first in summary by convention and nothing checked. A result that does not say what it was computed over is refused as UNSOUND, not written.
C32. A PATCH SCRIPT ASSERTED ON ITS ANCHOR AND NOT ON ITS RESULT. Part A checked that ACTIONS_CONFLICT appeared exactly once, which stays true after the insert, so re-pasting added the four codes again and Enum rejected the module at import. Measured: the block had been pasted three times. Because: every patch script in 8a through 8d guards the anchor rather than the outcome, and none had been run twice. A script asserts that its work is not already done, not merely that it knows where to put it.
C33. A REPAIR SCRIPT ASSUMED THE DAMAGE IT WAS WRITTEN FOR. The first repair hardcoded "remove the second copy" and failed its own final assertion, because there were three. Because: it asserted an expected shape rather than measuring the actual one. A repair counts before it cuts — and the final assertion is the only reason this did not become a quiet wrong state.
C34. A TEST FILE CALLED A FUNCTION THAT EXISTS ONLY IN THE HARNESS. test_analysis_tools.py used state.install, written into a container stub to make a gate injectable. The real state.py has no such function, so every test taking the con fixture errored in setup — 1 passed, 14 errors. Because: the stub was built to let the tool layer be tested, and the tests were then written against the stub's surface instead of the surface it stood in for. A stub mirrors the real signature or the tests it supports are testing the stub.
C35. AN ASSEMBLING SCRIPT AND ITS PAYLOAD SHARED A DELIMITER, ONE LEVEL UP. C31 logged that a patch script cannot anchor on a docstring; the guide assembly then built the document with a Python triple-quoted literal whose payload contained a docstring, and the literal closed early. The lesson was logged and not generalised. Payloads live in files and the guide takes placeholders only — no payload is ever inline in the assembling script.
MEASURED VALIDATION.
## Phase 8, Step 9b — compute_analysis on the MCP surface
**P8-D66. THE MCP WRAPPER DECLARES EVERY PARAMETER; params EXPOSES NONE. FastMCP builds the JSON schema from the signature, so the agent would have seen a tool with two arguments and no way to pass a column. Thirteen optional parameters, the union of nine signatures, and the Nones are dropped in analysis/tools.py so server.py keeps calling one function and each analysis's own default stays the only copy.
P8-D67. compute_analysis IS READ_ONLY BECAUSE THE ANNOTATION MEANS "DOES NOT MODIFY USER DATA". It writes a result file; so does profile_dataset, and that is READ_ONLY. Following the convention the codebase uses rather than the word's plain meaning, and recorded here because the two disagree.
P8-D68. A DISJUNCTIVE ASSERTION WAS REPLACED, NOT SATISFIED. "Phase 8" in doc or "not yet" in doc would have passed a docstring saying Phase 8's analyses run from here — green on either meaning. Phase 8 arrived, so it is pinned to computes nothing and to naming compute_analysis.
MEASURED VALIDATION.
## Phase 8, Step 9c — paging by column
P8-D69. A RESULT'S COLUMNS ARE PAGED, NOT JUST ITS ROWS. Closes P8-O15. Measured: a 50-column result returned twelve cells — the label column among them — and the other thirty-eight columns were in the file and reachable by no call. read_result_file sliced r[:PREVIEW_COLS] on every page, not only the preview. start_col and col_limit mirror start and limit: numbered from 1, capped, past-the-end is not a refusal, zero is.
P8-D70. col_limit IS CAPPED AT PREVIEW_COLS. Asking for fifty at once would hand format_table its own cap to enforce, and it does not say when it truncates. The slice stays in results.py, which is what that module's docstring says it is for.
P8-D71. RESULT_PAGE_ROWS IS DELETED. No readers, and it said 100 where results.PAGE_ROWS says 50, which is tied to formatting.MAX_ROWS so a page is what the formatter was built to render. P8-D48's shape.
P8-D72. THE LAST TWO ARGUMENT CHECKS BECAME ParamsInvalid. distribution's bins and cross_tab's dimension-against-itself. The non-numeric-measure refusal stays NOT_POSSIBLE: that one is about the contract's fit, and propose_dataset_contract is the right recovery.
MEASURED VALIDATION.
## Phase 8, Step 10 — acceptance
P8-D73. P8-O10 IS CLOSED: ACCEPTANCE RUNS THROUGH A REAL CONTRACT AND A REAL GATE. Every earlier Phase 8 test used a namespace looser than DatasetContract and a gate that could not refuse. The acceptance builds the model, confirms it through store.confirm with a real Binding, and reaches require_contract's drift classification and key verification — neither of which any test in this phase had exercised. 54 passed, 0 failed, 5 skipped.
P8-D74. THE OLIST CLAUSE IS A SKIP, NOT A PASS. No Olist data is on disk, and order_items in test_contract_tools.py is a 300-row range() generator wearing Olist's column names. The Done-When asks for both halves; the fixture half passes and the Olist half prints as outstanding on every run. Acquiring it belongs to Phase 9, whose own Done-When needs it.
P8-D75. THE role TRAP IS ACCEPTED AS BEHAVIOUR, NOT AS A FIELD. Following P8-D49: what is accepted is declared columns only, with the primary key named among what was skipped.
P8-D76. A CALL IS NOT A SCHEMA. @mcp.tool returns the plain function, so the acceptance calls the registered tool and proves its arguments are forwarded to the right names — which no other test does; the ast test asserts only that they are declared, and a crossed column=dimension would pass it. It cannot prove the JSON schema FastMCP builds, which is what the agent reads, and that stays a skip.
MEASURED VALIDATION.
Open items after Phase 8
Olist is not on disk. Phase 8's Done-When asks for it and Phase 9's needs it (calendar_coverage finding the missing month).
No live call through Claude Desktop has been made. Everything verified is ast parsing and Python-level calls; the rendered JSON schema is unseen.
ANALYSIS_RESULT_UNSOUND is only provokable with a test double. No real analysis can be made to lose rows on demand.
No fixture is wide enough to page columns at acceptance level. clean_sales has region 4, product 5, channel 3, so the widest cross_tab it can produce is 7 columns against a 12-column window; broken_sales is the same shape. P8-O15's fix is covered by nine tests in test_results.py against a synthetic 50-column result and by nothing at acceptance level. A make_fixtures.py change would close it.
## Phase 9, Step 1 - the ground facts (temporal)
P9-D1. ABSENCE CANNOT BE SELECTED FROM THE DATA. A GROUP BY over the date column returns the
periods that exist; a period with no rows has no row of its own to return. Measured: four
months and a NULL group where five months were in the span, November absent entirely rather
than present as a zero. Every Tier 3 analysis reads its periods off a generated calendar and
LEFT JOINs the table onto it. This is F10 in the Failure Mode Register, measured rather than
reasoned.
P9-D2. THE SERIES IS GENERATED FROM TRUNCATED BOUNDS, NEVER FROM THE RAW MINIMUM. Measured: a
monthly series started at 2017-01-31 walks Feb 28, Mar 28, Apr 28, May 28 -- February's clamp
sticks for every later period, and none of those days is a value date_trunc will ever produce,
so the join finds nothing and every period reads as missing.
P9-D3. generate_series IS INCLUSIVE AND range IS NOT. Measured: 4 periods against 3 on the same
arguments. On Olist that difference is October 2018, the last month in the window.
P9-D4. THE PERIOD COLUMN IS TIMESTAMP WHATEVER THE SOURCE COLUMN WAS. Measured:
date_trunc over a DATE returns TIMESTAMP. Labels come from strftime per grain, because a month
rendered 2017-03-01 00:00:00 reads as a day.
P9-D5. UNDATED ROWS ARE REPORTED, NEVER BUCKETED AND NEVER DROPPED. A NULL date is not a
missing period: the period is in the window and the row is in scope. Two numbers, two
sentences.
P9-D6. WEEKS ARE KEYED BY date_trunc('week'), NOT BY (year, weekofyear). Measured: 2016-01-01
is week 53 of isoyear 2015 and 2018-12-31 is week 1 of isoyear 2019. Weeks start Monday.
P9-D7. THE SESSION ZONE IS STATED WHEN, AND ONLY WHEN, THE COLUMN IS TZ-AWARE. Measured: one
instant truncates to 2017-03-14 under UTC and 2017-03-15 under Asia/Kolkata, and this machine
resolves to Asia/Kolkata. Measured against that: all five Olist orders timestamps are
'timestamp without time zone', and a naive TIMESTAMP does not move. A zone line over buckets it
cannot have affected is noise, and noise teaches a reader to skip the line that matters.
P9-D8. A COVERAGE ANSWER IS COUNTS, A MISSING LIST AND A LONGEST RUN, NOT THE SERIES. Measured:
761 daily periods over a two-year window against a 50-row cap. The series is a result file,
paged by the Step 9c call.
P9-D9. THE BOUNDS COME FROM analysis_window WHEN SET AND FROM THE OBSERVED SPAN WHEN NOT, AND
THE TWO ARE NEVER GIVEN THE SAME NAME. Measured in the contract: date_column and
analysis_window are both optional and the only refused combination is a window without a
column, so a column with no window is legal and is the common case. Phase 4 already ruled the
window is reported and never proposed. An observed span is a fact about the data; a window is a
decision someone made.
P9-D10. THE DATE COLUMN'S TYPE IS THE CONTRACT'S CHECK, NOT THE ANALYSIS'S. dataset_contract.py
refuses a VARCHAR date at confirm time with a reload instruction, so the engine's binder error
is unreachable through a confirmed contract and re-checking it would be a second opinion on a
settled question. P8-D29's rule, one tier up.
P9-D11. A WINDOW THAT ENDS MID-PERIOD MAKES THAT PERIOD PARTIAL, AND IT IS LABELLED. Measured
on the source: Olist orders run 2016-09-04 to 2018-10-17, so September holds 27 days and
October 17. Unlabelled, that is a ramp at one end of every Phase 11 line chart and a cliff at
the other, and neither is a movement in the business.
P9-O1 IS OPEN. The acceptance suite has no path to the Olist database. P8-D74 recorded the data
as absent; it is not -- local Postgres holds all nine tables and 99,441 orders across 25 of 26
months. What is missing is a way for a test to reach it that does not pass here and error
everywhere else.
C36. A REFLOW SPLIT STRINGS WITHOUT READING WHAT IT PRODUCED. An automated wrap cut string
literals at the first space under its budget and left the remainder as its own fragment, so the
file carried orphans reading "50-row " and "a missing list " alone on a line, and copied the f
prefix onto fragments holding no placeholder -- ruff F541. Because: the script asserted that the
concatenated string was unchanged, which stays true however ugly the split, and line length plus
a passing suite were checked instead of the artifact being read. C28 in a new place: a check
written against the property being preserved rather than the thing being produced. Every string
group is rejoined to one logical string and re-wrapped whole, with the f prefix decided per
segment by whether that segment contains a brace.
C37. A PROJECT CONVENTION WAS INFERRED FROM ONE DOCSTRING INSTEAD OF MEASURED. The Phase 7 facts
file's prose wraps near 79, so the temporal facts file was written to 79: twelve code lines were
hand-split and two test functions renamed to fit a limit this project does not use. Measured
across tests/ and analysis/: eight files run from 92 to 100 columns. C36's fragments are
downstream of the same guess -- messages that fit at 100 were being broken three ways to reach
79. A repository's style is measured across its files before it is followed.
C38. TWO COPIES OF ONE TEST MODULE INTERRUPTED COLLECTION. A stray copy at the repo root and the
real one in tests/ both claim the module name test_duckdb_temporal_facts under pytest's default
prepend import mode, so the second is refused as an import file mismatch and the whole run stops
at collection. Naming one path collects one file, which is why the standalone run passed and the
suite did not. Measured after the fact: no conftest.py exists at the root or in tests/, and
pyproject declares no testpaths, so collection walks the rootdir and a test file beside
pyproject.toml is collected as readily as one inside tests/. The stale __pycache__ entry
outlives the file it was compiled from and has to go with it.
C39. A TEST COUNT CANNOT TELL TWO PAYLOADS APART. The superseded 443-line file and the corrected
403-line file both gave 21 passed and both gave a 1325 suite, so the installed copy was the
defective one while every measurement said green. A file written by a pasted heredoc is
confirmed by its digest, not by the tests it passes.
MEASURED VALIDATION. tests/test_duckdb_temporal_facts.py: 21 passed. Full suite 1304 -> 1325.
Every fact reproduced on two machines, container and laptop, on DuckDB 1.5.5; the only
difference between the two runs was the session TimeZone, which is why the zone tests set it
explicitly.

## Phase 9, Step 2 - calendar_coverage
P9-D12. THE PERIODS COME OFF A GENERATED CALENDAR AND THE TABLE IS JOINED ONTO IT. P9-D1 as
code: generate_series between truncated bounds, LEFT JOINed to a GROUP BY of the date column, so
an absent period is a row reading 0 rather than a row that was never returned. Every later Tier
3 analysis reads its periods the same way. This is F10 in the Failure Mode Register, and the
suite asserts it twice -- once that the GROUP BY this replaces cannot return the missing month,
once that the coverage output can.
P9-D13. THE BOUNDS ARE THE WINDOW'S WHEN THERE IS ONE AND THE OBSERVED SPAN'S WHEN THERE IS NOT,
AND THE SUMMARY NAMES WHICH. P9-D9 as code. Measured in the contract model: date_column and
analysis_window are both optional and the only refused combination is a window without a column,
so a column with no window is legal and is the common case. Phase 4 already ruled the window is
reported and never proposed; an observed span is a fact about the data and a window is a
decision somebody made, and the two are never given the same name.
P9-D14. THE UNDATED ROWS ARE COUNTED HERE, BECAUSE THE SCOPE CANNOT COUNT THEM. scope_for fills
no_date only when a window exists -- with no window there is nothing to be outside of -- so a
NULL-dated row sits in analysed and would vanish between the periods. The reconciliation is
sum(period counts) + undated == scope.analysed and it raises LostRows, which is P8-D45's guard
on a new way of losing rows.
P9-D15. THE GRAIN IS AN ARGUMENT WITH FIVE VALUES AND EACH CARRIES ITS OWN LABEL. day, week,
month, quarter, year. P9-D4: date_trunc returns a TIMESTAMP whatever the column was, so a month
rendered raw reads as a day; every grain is labelled by strftime and quarter is '%Y-Q' ||
quarter(p), which has no code of its own. grain is the first fixed-value string in
compute_analysis's signature, so its five values are in the tool docstring -- the schema the
model reads -- rather than being discovered through a ParamsInvalid on the first call.
P9-D16. THE SESSION ZONE IS READ AND STATED ONLY FOR A TZ-AWARE COLUMN. P9-D7. Measured in
dataset_contract.py: _TEMPORAL_PREFIXES is a prefix tuple, so TIMESTAMP WITH TIME ZONE passes the
contract's check and a TIMESTAMPTZ date_column is legal. The branch is reachable, not defensive.
P9-D17. THE LONGEST GAP IS COMPUTED FROM THE ROWS ALREADY FETCHED. Three missing months in a row
is a feed that stopped; three scattered is a business that was quiet. A second query would be a
second answer able to disagree with the first.
P9-D18. NO TZ-AWARE VALUE IS FETCHED INTO PYTHON. DuckDB builds a TIMESTAMPTZ with pytz, which
this project does not depend on, so a bound fetched to be compared raised InvalidInputException
naming the missing module. The bounds come back as VARCHAR and every comparison between them is
made in SQL, where the types already live. A date is not carried across a language boundary to
be compared on the other side.
C40. A MEASUREMENT PASSED BECAUSE OF A PACKAGE THE PROJECT DOES NOT HAVE. pytz was installed
into the container in Step 1 to read tz-aware values out of the probe; the probe was then fixed
by casting to VARCHAR and the package was left behind, so the harness exercised the TIMESTAMPTZ
path against an undeclared dependency and reported everything green. Measured after the fact:
uninstall pytz, re-run, one failure on the tz-aware test with the same exception the repository
saw. An environment that has more in it than the project declares cannot measure the project.
C41. TWO EXPECTED VALUES IN THE NEW TESTS WERE REASONED RATHER THAN MEASURED. The week count was
written 19 and is 20, and a period count was asserted as the integer 0 where base.number()
renders it to the string "0" before it reaches a cell. Both were caught by running the tests
rather than by reading them, and both were corrected by measuring first rather than by adjusting
until green. C37's habit, one layer in.
P9-O2 IS OPEN. Everything measured so far is container fixtures and Olist, so the module is
general by construction and not yet by evidence. Olist has nine tables and three of them are
other temporal shapes for free: order_reviews has two date columns, so a proposal leaves
date_column unresolved; order_payments has none, which exercises the refusal on real data rather
than on a fixture built to be refused; order_items carries shipping_limit_date, which Phase 4
found running past the end of the order data, so its coverage table should show a tail of
periods nobody wants. The Phase 13 gold questions should span at least three tables with
different temporal shapes, including one with no date column.
P9-O3 IS OPEN. compute_analysis's docstring says an argument that does not apply is "refused
rather than ignored". True of a value: every analysis raises TypeError on an unexpected keyword.
Not true of None: tools.py strips None before dispatch, so bins=10 to calendar_coverage is
refused and bins=None is accepted silently. The behaviour is right and the sentence oversells
it.
MEASURED VALIDATION. tests/test_calendar_coverage.py: 21 passed. Full suite 1325 -> 1346. Phase
8 acceptance: NN passed, N failed, N skipped, after its registration check was changed from a
count of nine to a subset of its own nine names -- a later tier must not fail an earlier phase's
acceptance for having done its own work.

## Phase 9, Step 3 - the Olist acceptance clause
P9-D19. THE ACCEPTANCE COPIES THE TABLE IN, BECAUSE THE GATE DOES NOT KNOW ABOUT ATTACHED
CATALOGS. Querying in place was the plan: attach READ_ONLY, bind a contract, analyse
olist.public.orders without moving 99,441 rows. Measured: state._loadable_tables reads
db.user_tables, which lists what the workspace owns, so an attached catalog is not a loaded
dataset however cleanly it attaches, and all five clauses came back DATASET_NOT_LOADED. The
contract confirmed without complaint; the gate refused. load_table copies the table instead,
which is the path a person actually takes, so the acceptance proves what a person can actually
do. 99,441 rows clears ROW_REFUSE, which is SIZE_GATES.excel_refuse_rows.
P9-D20. THE CLAUSE SKIPS WITH A NAMED REASON RATHER THAN ERRORING WHEN THE DATABASE IS NOT
THERE. load_table attaches the source itself and raises LoadRefused when Postgres is down, the
alias is missing, or the table is too big to copy; mount() catches it and returns the first line
as the skip reason. A test that reaches a live local database and errors everywhere else is
worse than no test. This is what P9-O1 was asking for.
P9-D21. THE SECOND HALF OF THE DONE-WHEN SKIPS EXPLICITLY. correlated_shift is Tier 5 and is not
built. A script that asserts half a Done-When and says nothing about the other half reads as a
Done-When met, which is the same failure P8-D74 was arranged against one phase earlier.
C42. AN ATTACHMENT WAS TREATED AS A PROPERTY OF THE WORKSPACE. ATTACH binds a catalog to one
DuckDB connection; it is not written into the workspace file and the next connection knows
nothing about it. This file follows Phase 6's rule of one short-lived handle per call, so every
helper touching the source has to attach on its own handle -- attach is idempotent for exactly
that reason, and its docstring was read as "safe to call twice" rather than "expected every
time". The probe that measured the catalog resolution could not have caught it: it did its
attach and its information_schema lookup on one connection, so it measured the right fact in the
wrong shape. A measurement that shares a connection says nothing about code that does not.
P9-O1 IS CLOSED. tests/test_phase9.py, run as `uv run python tests/test_phase9.py`, copies
public.orders from the olist source and asserts that calendar_coverage returns 2016-11 across a
26-month calendar over 99,441 rows, that grain reaches the analysis through the registered MCP
tool, and that a contract with no date_column refuses as ANALYSIS_NOT_POSSIBLE naming
confirm_dataset_contract. The alias already existed in ~/.analytics-agent/sources.yaml; nothing
had to be acquired. P8-D74's "no Olist data is on disk" was wrong when it was written.
P9-O4 IS OPEN. compute_analysis cannot reach an attached source. server.py advertises querying
olist.public.orders in place, and postgres.load_table's own refusal tells a caller whose table
is too big to copy to "query it in place instead -- the table is already attached and needs no
copy". Both are true of inspection: preview_table, describe_source and row_count reach an
attached table. Neither is true of analysis, which goes through require_contract. So the advice
given at the size gate leads to a path that cannot analyse. Widening _loadable_tables would
close it and is not an acceptance script's decision: a READ_ONLY attached table could be
analysed but never cleaned, so clean/ and validate/ would have to refuse it coherently, and
locked decision 22 is the frame for that argument.
MEASURED VALIDATION. tests/test_phase9.py: 10 passed, 0 failed, 1 skipped. The skip is
correlated_shift. Full suite 1346 passed, unchanged by this file: pytest collects it and finds
no test functions, exactly as it does test_phase8.py, which is why the acceptance tally and the
suite count have never been the same number.

## Phase 9, Step 4c - trend
P9-D31. A TREND IS ONE MEASURE PER PERIOD AND NOTHING FITTED. The first and last periods holding
rows and the difference between them, stated as two endpoints. No slope, no moving average, no
percentage unless both ends are non-zero. A line fitted across the gap this analysis exists to
report would be the gap warning's own counter-example, and the arithmetic of change belongs to
growth_decomposition, which is where Step 4f put it.
P9-D32. AN ABSENT PERIOD IS BLANK, NEVER ZERO. coalesce(count, 0) is right and coalesce(sum, 0)
is a claim that the period happened and came to nothing, which is the one thing the data does
not say. P9-D1 carried into the value column rather than only the count column: the calendar
makes the absent period visible, and this decides what is written in it.
P9-D33. A MEASURE DECLARING agg='none' IS REFUSED RATHER THAN AVERAGED. A unit price summed or
averaged per month produces a number nothing downstream can detect as wrong, which is the reason
Measure.agg has no default. The refusal names frequency as the analysis that does answer for a
non-additive measure.
P9-D34. A GAP IS A CAVEAT AND NEVER FATAL. The reader decides whether a window that is half empty
is worth reading; the analysis names the gap, names the longest run, and leaves it there. Tier
5's changepoint may want a different answer and can have one.
C43. TWO EXPECTED VALUES WERE REASONED RATHER THAN MEASURED, AGAIN. base.number renders a DECIMAL
sum to two places, so a monthly sum of 10.00 reads "10.00" and not "10"; both test expectations
were written from the arithmetic rather than from a run. Caught by the tests before shipping.
C41 one step on, and Step 4c's own note calls it the fifth instance of the habit this session --
the fix that has actually held since is procedural, not resolve: values that will be asserted are
produced by a run first and copied second.
MEASURED VALIDATION. tests/test_trend.py: 15 passed. Full suite 1346 -> 1361. The 15 is not from
a standalone run: the three Tier 3 test files together measured 53, calendar_coverage's 21 is
recorded above and seasonality's 17 was measured alone, which leaves 15 and no room for it to be
anything else.

## Phase 9, Step 4d - seasonality
P9-D22. avg() OVER A DECIMAL RETURNS DOUBLE WHERE sum() DOES NOT. Measured on DuckDB 1.5.5:
typeof(avg(amount)) is DOUBLE and typeof(sum(amount)) is DECIMAL(38,2) on the same column. A
per-position mean therefore does not carry the measure's storage type the way a per-period value
does, and whatever renders it is rendering a float. The design had assumed the opposite and the
measurement killed the rationale; the SQL fold survives on its other merit, which is that avg
skipping NULLs is the absent period declining to be a zero with no Python deciding it.
P9-D23. THE POSITION IS READ OFF THE PERIOD'S OWN LABEL. seasonality wraps per_period_sql whole
as a subquery rather than rebuilding the calendar, so there is one place where a period's
identity is decided and an absent period arrives already present as a NULL. Measured: a nested
WITH inside a FROM (...) subquery is accepted by DuckDB 1.5.5.
P9-D24. A YEAR IS REFUSED A CYCLE. Seasonality is variation that comes back, and this calendar
has nothing above a year for a year to repeat inside. grain='year' raises ParamsInvalid naming
trend as the analysis that does answer at that grain. Folding twelve years onto one position and
calling the result a season is the failure this refusal exists against.
C44. THE f PREFIX WAS CARRIED ONTO A SEGMENT HOLDING NO BRACE. ruff F541, in a summary line
assembled by concatenation where the neighbouring segments were all interpolated. C36 ruled that
the f prefix is decided per segment by whether that segment contains a brace, and C36's own
remedy was not applied to the file that restated it. Found by running the linter, not by reading
the file.
P9-O5 IS OPEN. base.number() is handed a float here for the first time in this module family,
by P9-D22, where trend hands it a DECIMAL and gets "10.00". A later real run proved it does not
raise on a float, but no test in any Tier 3 file asserts how it renders one, so the decimal
places in a mean column are unasserted. If analysis/stats.py already owns a mean renderer, that
is the right home and seasonality should adopt it.
MEASURED VALIDATION. tests/test_seasonality.py: 17 passed. Full suite 1361 -> 1378. Phase 9
acceptance unchanged at 10 passed, 0 failed, 1 skipped; the skip is still correlated_shift.

## Phase 9, Step 4e - period_compare
P9-D25. BOTH PERIODS ARE NAMED AND NEITHER IS DEFAULTED. The latest period is the one most likely
to be partial, so a "latest against previous" default reaches for exactly the wrong baseline and
reports a fall that is three days of March against all of February. Phase 4's reported-never-
proposed rule, applied to a comparison: the comparison is a decision and the caller makes it. The
cost is a clunkier call and it is worth paying.
P9-D26. A LABEL THE CALENDAR LACKS AND A LABEL THE TABLE LACKS ARE DIFFERENT ANSWERS. The first
is ParamsInvalid naming the range and the vocabulary that does exist; the second is a row in the
output holding no value, with no change taken from it. Only a generated calendar can tell them
apart -- a GROUP BY has one response to both. P9-D12 used as a lookup rather than as a table.
P9-D27. A PERIOD'S LENGTH IS A PROPERTY OF THE CALENDAR AND IS REPORTED WHEN THE AGGREGATE ADDS.
Measured: date_diff('day', p, p + INTERVAL 1 MONTH) gives 28, 29 and 31 across months and 89, 90
and 92 across quarters. A sum over February against a sum over March sets 28 days of data against
31, a difference of 10.7% in length alone, before anything in the business moved. Step 8a's
additive set decides who hears about it: a sum or a count is longer for being longer and a mean
is not.
C45. A STUB INVENTED AN AGG_SQL KEY AND A TEST PASSED AGAINST THE INVENTION. The test harness
that runs a new analysis before it is pasted stubs declared.py, and its AGG_SQL was written from
what the SQL function is called -- avg -- rather than from the repository, where the keys are
count, count_distinct, max, mean, median, min and sum. So a fixture declared agg='avg', the
harness reported 16 passed, and the first real run raised ValueError from the module's own
refusal. The module was right and the test was wrong, which is the good version of this failure.
The general form is worse than the instance: everything a stub supplies -- AGG_SQL's keys,
number()'s rendering, scope_for's fields -- is unverified until a real run touches it, and a
green harness says nothing about any of it. A second edit followed from the same root: the
ADDITIVE comment read "sum and count do, the other three do not", where three was true of the
stub's five keys and false of the real seven.
P9-O6 IS OPEN. ADDITIVE = frozenset({"sum", "count"}) is restated in period_compare.py and again
in growth_decomposition.py, where Step 8a already ruled it. Two copies of one ruling is how the
two drift apart. If declared.py or stats.py exports that set, both should import it.
P9-O7 IS OPEN. tools.py strips None before dispatch (P9-O3), so a call omitting a required
parameter reaches the analysis with the argument genuinely missing and the module raises
TypeError. Whether that surfaces as a refusal a caller can act on or as a traceback out of the
MCP surface depends on an except clause below tools.py:119, which has not been read. trend and
seasonality can raise TypeError too, but only on a parameter nobody should have passed;
period_compare is the first analysis with a required parameter an agent can simply forget.
MEASURED VALIDATION. tests/test_period_compare.py: 16 passed, after one failure. Full suite
1378 -> 1394. Phase 9 acceptance unchanged at 10 passed, 0 failed, 1 skipped. The suite count
doubles as the wiring check: test_declared.py's tier map names period_compare and compares itself
against the registry, so a green suite proves the registration import took.

## Phase 9, Step 4f - growth_decomposition
P9-D28. ONLY AN ADDITIVE AGGREGATE CAN BE DECOMPOSED. sum and count split across a dimension's
members because the members' values add back to the whole; mean, median, min, max and
count_distinct do not. Per-member changes in an average do not sum to the change in the average,
and a table of them would look exactly like one that did. P9-D27's set promoted from a caveat to
a gate, because here the non-additive answer is not incomplete but wrong and undetectably so.
The refusal names period_compare, which compares a mean between two periods without splitting it.
P9-D29. AN ABSENT MEMBER IS A ZERO AND AN ABSENT PERIOD IS NOT. The calendar asserts that a
period's time existed and the data does not cover it, which is why P9-D32 leaves the cell blank.
Nothing asserts that a member existed: a member with no rows inside a period that does hold rows
really did contribute nothing, and it has to be zero or the contributions do not sum. Those
members are named as entrants and leavers so they cannot be read as ordinary movements.
P9-D30. A VALUE THAT REACHES SQL IS BOUND, NOT INTERPOLATED. quote_identifier covers identifiers,
and every earlier Tier 3 query passed only identifiers and dates DuckDB itself produced.
growth_decomposition is the first to pass a caller's string into a query, and it binds it even
though the membership check above already guarantees the string came out of DuckDB's strftime.
C46. THE f PREFIX AGAIN, THREE TIMES, ONE STEP AFTER C44. Three consecutive segments of one
summary line, none holding a brace, all carrying the prefix. Twice in three steps says the C36
rule does not survive contact with a summary.append block whose neighbours are all interpolated:
the prefix is coming from the shape of the surrounding code and not from the content of the line.
What changed is the order of operations rather than the care -- the linter now runs before the
digest is taken, so the published file is the fixed one and there is no patch step. A process fix
is the only kind that has held.
C47. THE SQL WAS SAFE BY EXECUTION ORDER BEFORE IT WAS SAFE BY DESIGN. The grouped query first
interpolated both period labels and the no-member label straight into string literals. Nothing
could exploit it, because the membership check above it guarantees those labels came out of
DuckDB's own strftime -- but that is a property of where the check sits, not of the query, and an
edit moving the check would remove the guarantee silently. Found by reading the SQL before
digesting it, not by any test; the test that probes it was written after the fix, which is the
wrong order.
P9-O8 IS OPEN. A NULL in the decomposed dimension is labelled "(no <dimension>)" and named in the
summary as a member rather than a gap. Whether Tier 2's group-wise analyses already have a label
for the NULL group has not been checked; if they do, that one wins, because two labels for one
thing is P9-O6 in a different column.
P9-O9 IS OPEN. growth_decomposition validates its dimension against contract.dimensions in its
own body rather than through a shared helper, because no require_dimension was known to exist
alongside require_measure. If declared.py exports one, this should use it and inherit whatever
refusal text the rest of the tool surface already gives.
P9-O10 IS OPEN. Two files state how many analyses exist: server.py's module docstring and a
comment at tools.py:77. They disagreed from Phase 9 Step 2 until Step 4e noticed, and Step 4f had
to bump both again one step later. A count stated in two places is a count that will be wrong in
one of them.
MEASURED VALIDATION. tests/test_growth_decomposition.py: 17 passed, including the injection probe
the pre-paste harness could only run separately. Full suite 1394 -> 1411, which also proves the
wiring landed by way of test_declared.py's tier map. Phase 9 acceptance NOT YET RE-RUN at the
time of writing; nothing in this step goes near Step 3's clauses, so it is expected to hold at 10
passed, 0 failed, 1 skipped, and expected is not measured.

## Phase 9, Step 5a - correlation
P9-D38. A CONSTANT COLUMN IS UNDEFINED AND DUCKDB SAYS SO WITH nan, NOT NULL. Measured on DuckDB
1.5.5: corr over a column taking one value returns nan, which is neither None nor equal to
itself, and reaches a cell as the string "nan" unless converted back to an absence. Both
coefficients are blank and the summary says why, because zero would claim the two columns do not
move together when one of them does not move.
P9-D39. n IS THE PAIRWISE-COMPLETE COUNT AND IS REPORTED BESIDE EVERY COEFFICIENT. corr drops a
row missing either value without saying so. Measured: 7 rows, count(x)=6, count(y)=6,
regr_count=5.
P9-D40. BELOW THREE PAIRS NO COEFFICIENT IS REPORTED. Any two points lie on a line, so Pearson is
+/-1 by construction. The pair count is still reported and the cells are blank.
P9-D41. agg IS NOT CONSULTED BY A CORRELATION. Tier 3 refuses agg='none' because a value per
period would be invented; nothing is combined here, so the constraint does not transfer and
inheriting it would refuse a legitimate question about a unit price. This ruling is reused by
bivariate, driver_analysis and mix_shift.
C48. THE ROW WAS BUILT BEFORE THE GUARD THAT BLANKS IT. Below three pairs the summary said no
coefficient was reported while the cell read +1.000, because rows were assembled from the raw
coefficients and the MIN_PAIRS check only appended prose afterwards. A cell contradicting the
sentence under it is worse than either alone: a reader trusting the table gets a fabricated
certainty and one trusting the prose learns the table lies.
C49. AN ARTICLE CHOSEN BY SENTENCE RHYTHM. "an freight". The fix is to name columns without
articles, which is also correct for a column called order_id. See C59.
MEASURED VALIDATION. tests/test_correlation.py: 14 tests, corroborated by the 1440 measured at
Step 5b (1411 + 14 + 15). Line counts and digests confirmed on the first paste: 202 and 172,
63018e10 and db459935.

## Phase 9, Step 5b - bivariate
P9-D42. A BIN IS A RANGE OF VALUES, NOT A SLICE OF ROWS. Measured: ntile(4) over ten rows holding
three distinct values puts x=1.0 in bin 1 and bin 2 and returns bins whose ranges overlap. Binning
the distinct values and joining every row onto its own value's bin does not, at the cost of uneven
row counts, which are reported because an uneven bin is a fact about the distribution.
P9-D43. MORE BINS THAN DISTINCT VALUES YIELDS FEWER BINS, AND THE NUMBER PRODUCED IS REPORTED.
Measured: ntile(9) over three distinct values gives three. Silence there is indistinguishable from
six bins having been dropped by a filter.
P9-D44. THE TURNS ARE COUNTED AND THE CURVE IS NEVER NAMED. Direction changes between consecutive
bins are reported as a count. Calling it a U or a parabola is fitting a shape, and this analysis
fits nothing -- the boundary trend drew when it refused a line. A test asserts those words absent.
C50. THE HARNESS STUB PADDED EVERY FLOAT TO TWO PLACES AND base.number() DOES NOT. A bin bound of
1.0 rendered "1.00" in the sandbox and "1.0" in the repo. Fourth step in which a stub was the
thing that was wrong.
C51. AN ASSERTION WRITTEN FROM INTENT RATHER THAN FROM OUTPUT. The test asserted the summary
contains "not a defect in the binning"; the line reads "rather than a defect in the binning". I
wrote the sentence, then wrote the assertion from what I meant it to say.
MEASURED VALIDATION. tests/test_bivariate.py: 15 passed, after one failure that was C50. Full
suite 1440 passed, printed. Suite before it, 1425, was never printed and is not claimed.

## Phase 9, Step 5c - driver_analysis
P9-D45. A SHARE OF VARIANCE IS RANKED AGAINST WHAT CHANCE WOULD GIVE. A grouping into g groups
over n rows accounts for about (g-1)/(n-1) on structureless data. Measured: id scores 1.000
against a baseline of 1.000 for an excess of exactly 0.000, region 0.995 against 0.375 for +0.620.
Without the baseline the ranking ranks cardinality and the primary key wins every time.
P9-D46. A NEGATIVE EXCESS IS REPORTED AS NEGATIVE. Measured: size scores 0.073 against 0.125.
Clamping to zero would hide that grouping by it tells you less than nothing.
P9-D47. A MEASURE THAT DOES NOT VARY HAS NO SHARES. Its total sum of squares is exactly 0.0, so
every share divides by it. No rows and a sentence, not a zero -- the ruling P9-D38 made for nan.
P9-D48. NOTHING IS CALLED A DRIVER. The tool carries the guide's name and the output says accounts
for. The summary states on every run that the top dimension may be caused by the measure, may
share a cause with it, or may be another name for it.
C52. TWO ASSERTIONS THAT COULD NOT BOTH HOLD, AND THE PROSE SIDED WITH THE WRONG ONE. One test
asserted the ranking is region, id, size; another asserted id ranks last. The module docstring
said "last by excess". id ranks second: its excess is +0.000 and size's is -0.052. The correct
numbers were printed by the measurement run before a line of the module existed -- "ranks last"
was a story about what the baseline was for, written instead of read. It surfaced only because the
two assertions contradicted each other; written alone, the wrong one would have shipped.
MEASURED VALIDATION. tests/test_driver_analysis.py: 14 passed against the harness. Full suite
1454 was not printed; it is corroborated by the 1469 measured at Step 5d (1469 - 15).

## Phase 9, Step 5d - mix_shift
P9-D49. A FLOATING-POINT DECOMPOSITION IS RECONCILED TO A TOLERANCE, NOT EXACTLY. Measured
residual 7.11e-15 on ten rows. growth_decomposition reconciles in Decimal and demands equality; a
weighted mean is DOUBLE the whole way down. The tolerance is scaled by the size of the change and
named as a constant, because an absolute epsilon is wrong at both ends of the range.
P9-D50. THE INTERACTION TERM IS REPORTED AND NEVER FOLDED. Folding it is what choosing the
baseline or the period as the weighting base does silently, and the two choices disagree by
exactly it.
P9-D51. A GROUP IN ONLY ONE PERIOD HAS NO RATE AND NO MIX. No second mean to subtract and no share
to reweight; imputing the overall mean for the missing side manufactures a rate effect out of an
arrival. Its whole effect is a contribution, named as an entry or an exit.
THIS DOES NOT BREAK P9-D29. That ruling says per-group changes in an average do not sum to the
change in the average, which is true and is not what happens here. A per-row mean is a weighted
sum, M = sum of w(g)*m(g), so this decomposes a weighted sum into its weights and its terms.
Measured: every group's mean rises -- 100 to 110 and 10 to 12 -- while the overall mean falls from
82.0 to 31.6. Rate totals +8.400 and mix totals -54.000.
C53. P9-O5 DECLARED ANSWERED AFTER MEASURING A SINGLE CASE OF IT. Step 5b's document said
base.number() "is no longer on that list" on the strength of one failure showing 1.0 rendering as
"1.0". That value was a DECIMAL(2,1) literal, not the DOUBLE assumed. The rule is by type: a
DECIMAL keeps its scale, a DOUBLE drops trailing zeros, an int is plain. Treating a measurement of
one case as a measurement of the behaviour, which is the harness mistake one level up.
C54. A TEST FOR AN EMPTY PERIOD AGAINST A CALENDAR THAT HAD NO EMPTY PERIOD. The fixture ran
January to March with rows in all three and the test asked for 2017-04. What came back was the
right refusal for the other reason -- P9-D27 distinguishes a label the calendar lacks from one the
table lacks. First time a Tier 3 ruling caught a Tier 4 test, and it did so by naming the
distinction it was drawing.
MEASURED VALIDATION. tests/test_mix_shift.py: 15 passed, after one failure that was C53. Full
suite 1468 passed and 1 failed, printed: the failure was tests/test_declared.py, whose tier map
had no mix_shift because the step's wiring had not been run. Passing alone and failing in the
suite is what that looks like -- the map is compared against catalogue(), and a test file
importing its own module registers it without the __init__ edit. After the wiring, 1469.

## Phase 9, Step 6a - outlier_detection
P9-D52. THREE METHODS, ALWAYS, WITH THEIR BOUNDS. Tukey's fence, the z-score and the median
absolute deviation return different rows rather than different opinions about the same rows, so
choosing one upstream answers a question the reader did not ask. The agreement is counted at every
level, because the interesting case on the fixture is the one flagged by two of three.
P9-D53. THE Z-SCORE MASKS, AND THE MASKING IS NAMED. Measured: ten values from 1 to 10 plus 1000
and 1010 give a standard deviation of 389.07, so three deviations reach past 1339 and the z-score
flags nothing while the other two flag both extremes. Two outliers are enough. Whenever it flags
fewer than the quantile-based methods, the summary says why.
P9-D54. A MAD OF EXACTLY 0.0 IS NO SCALE. More than half the values on the median leaves the
robust method without one. Reported as no bounds, not bounds of zero width, which would flag every
value differing from the median at all.
P9-D55. A BOUND IS RENDERED AT THE MODULE'S PRECISION, NOT THE COLUMN'S. Measured: quantile_cont
over DECIMAL(5,1) gives 3.7 where the identical values as DOUBLE give 3.75, so the fence already
moves with the storage type. Letting the rendering move too puts two kinds of drift in one cell.
C55. THE AGREEMENT SUMMARY REPORTED THE TWO ENDS AND HID THE MIDDLE. It said how many values every
method flags and how many exactly one flags. On the fixture both are 0 and the real answer -- both
extremes flagged by two of three -- appeared nowhere, while two flagged rows sat in the table
above. Found only because an unrelated assertion failed and the whole summary was printed to take
the expected string from. Written correctly the first time, the defect would have shipped behind a
green test, which is an argument for reading output when tests pass and not only when they fail.
C56. TUKEY BOUNDS TAKEN FROM A MEASUREMENT UNDER THE WRONG TYPE. -4.5 and 17.5 came from a run
where the values were DOUBLE; the fixture stores them as DECIMAL(5,1), where the fence is -4.55
and 17.45. Same shape as C53 one step later. The fix removed the dependency rather than correcting
the number: P9-D55.
MEASURED VALIDATION. tests/test_outlier_detection.py: 13 passed. Full suite 1482 passed, printed,
which is 1469 + 13 and confirms both this step's wiring and Step 5d's.

## Phase 9, Step 6b - changepoint
P9-D56. A GAP IS FATAL TO A SPLIT BESIDE IT. Step 4c ruled that a gap is a caveat and never fatal
and named this analysis as the one that may need otherwise. It does: a level shift across an
absent period is a description of the absence. A split flanked by a period holding no rows is
excluded, the exclusions are named, and a series where every candidate is excluded returns no
changepoint. The summary quotes the ruling it departs from rather than departing silently.
P9-D57. EVERY ADMISSIBLE SPLIT IS REPORTED. Any series has a best one; reporting only the winner
converts arithmetic into a finding.
P9-D58. A BREAK IS MEASURED AGAINST WITHIN-SEGMENT SPREAD, NOT AGAINST THE RUNNER-UP. Measured: a
clean step of +40 has its runner-up at +34.29, a margin of 14%, because adjacent splits share all
but one period and are correlated by construction. The within-segment comparison gives 44.7 times
for a noisy break and 0.4 for a series with none.
P9-D59. NO SIGNIFICANCE IS CLAIMED. No test and no p-value; a test needs distributional
assumptions the contract does not state, and scipy is a Phase 10 dependency.
C57. THE DISCRIMINATOR WAS BUILT OUT OF THE WRONG COMPARISON. The first draft judged the best
split by its distance from the runner-up, which sounds right and is wrong for a reason visible in
one run. The measurement said "does not stand clear" about a perfect step function with no noise
in it -- obviously wrong rather than subtly wrong, which is the only reason it was noticed instead
of shipping as a plausible rule.
C58. F541, THIRD OCCURRENCE, FIVE INSTANCES. C44 and C47 recorded the same. Every one caught by
ruff running before the digest, so none has reached a paste -- but three occurrences means the
linter is load-bearing rather than a backstop, and the ordering fixed the outcome and not the
habit.
MEASURED VALIDATION. tests/test_changepoint.py: 14 passed. Full suite 1496 was not printed; it is
corroborated by the 1510 measured at Step 6c (1510 - 14).

## Phase 9, Step 6c - correlated_shift
P9-D60. THE RATE AT WHICH UNRELATED SERIES COINCIDE IS REPORTED BESIDE THE VERDICT. Measured: 7
admissible splits and a tolerance window of 3 gives 43% on a twelve-month fixture, and 20 splits
gives 15% on Olist's twenty-six. A coincidence is evidence only to the extent it is unlikely, and
the denominator is not the reader's to guess.
P9-D61. THE TOLERANCE IS A CONSTANT, NOT A PARAMETER. A tolerance the caller can raise is one that
gets raised until something coincides. Fixing it keeps the chance rate a property of the calendar
rather than of a choice made after seeing the data.
P9-D62. A GAP COSTS TWICE. Measured: dropping one month of twelve takes admissible splits from 7
to 5 and the chance rate from 43% to 60%. An absent period blocks splits beside it and cheapens
whatever coincidence survives; both effects are reported.
P9-D63. NOTHING IS SAID TO HAVE MOVED ANYTHING. The summary names the explanation it cannot rule
out -- a third thing moving both series -- on every run, as driver_analysis does.
C59. "an volume" -- C49 REGRESSED. The Step 5a entry said to name columns without articles,
because an article chosen by sentence rhythm is wrong the moment the column is called order_id.
Ten steps later the same construction went into a fresh summary line. This is different from the
F541 repeats: those recur because ruff catches them and I have leaned on that, and this recurred
with nothing watching. A correction that lives only in a step document protects nothing -- there
is no lint rule for articles and no test asserts English.
MEASURED VALIDATION. tests/test_correlated_shift.py: 14 passed, printed. Full suite 1510 passed,
printed. tests/test_phase9.py unchanged at 10 passed, 0 failed, 1 skipped: the skip did not flip,
and its stated reason -- Tier 5 is not built -- had become false, because the clause was an
unconditional skip() with no condition to flip.

## Phase 9, Step 7 - the Done-When
P9-D64. THE ACCEPTANCE SHIFT IS INJECTED INTO THE REAL CALENDAR. Two synthetic measures are added
to the copied orders table rather than a synthetic table being built, so the gap at 2016-11 and
the twenty-six month span are the ones clause one already measured. confirm_contract gains an
optional extra-measures argument; the dataset name stays TABLE.
P9-D65. THE INJECTED MEASURES DECLARE mean. A per-period sum is value times row count and Olist's
monthly volume climbs steeply enough to swamp a step of 10 to 50, so a summed series tracks orders
per month and the clause would pass or fail for a reason unrelated to what it tests.
P9-D66. THE CLAUSE HAS A NEGATIVE CONTROL. Measured: unrelated series coincide 15% of the time on
this calendar, so a clause asserting only that a coincidence was reported passes about one time in
seven. The control moves one series' step six months and asserts it is not reported as coincident.
THE SPLIT IS REPORTED AFTER THE PERIOD BEFORE THE STEP. Measured: a step beginning 2017-10 is
reported as breaking after 2017-09, because "breaks after X" names the last period before the
change. An assertion written for the injection month fails, which is why SPLIT_AFTER exists beside
INJECTED_AT.
C60. A COUNT ESTIMATED WHERE IT COULD HAVE BEEN COUNTED. The step document predicted 15 passed;
the run printed 16. Ten existing plus six checks in clause four, not five -- a clause written in
that same document and quoted in full sixty lines above the prediction. Nothing turned on it, and
the number was available by counting.
P9-D35, P9-D36 AND P9-D37 ARE NOT ASSIGNED. Steps 5a to 6b were numbered from a draft ledger block
that was discarded before it was ever appended, when the real one turned up. The numbers are left
unused rather than reclaimed, because five shipped modules cite the range above them --
correlation.py P9-D38 to D40, bivariate.py D42 and D43, driver_analysis.py D45 to D47,
mix_shift.py D49, outlier_detection.py D52 to D55. The same choice the Step 4c entry made when it
numbered its own rulings D31 to D34 out of sequence: consistency with shipped code beats
consistency with the counter.
P9-O10 IS OPEN. Two places state how many analyses exist -- server.py's module docstring and
tools.py:77 -- and both are edited every step. They were already out of step once, tools.py
reading "nine" through three increments. Deriving the count from the registry is a small change
that gets slightly larger each step.
P9-O11 IS OPEN. test_declared.py's tier check iterates catalogue() and not the map, so it catches
an analysis with no map entry -- which is how Step 5d's unrun wiring was found -- but cannot catch
a map entry whose analysis was never registered. Had that wiring half-applied, the map would have
gained mix_shift and nothing would have noticed the missing registration.
P9-O12 IS OPEN. correlated_shift imports _within and MIN_SEGMENT from changepoint. A private name
crossing module boundaries is not lovely; the alternative is a second copy of a statistic, which
P9-O6 already records as how two copies drift apart.
MEASURED VALIDATION. tests/test_phase9.py: 16 passed, 0 failed, 0 skipped, printed. Clause four's
six checks: correlated_shift runs on Olist over 99,441 rows; both series break in the same place;
the break is found after 2017-09 where it was injected; the coincidence rate is reported; 2016-11
narrows the comparison; and a shift six months away is not reported as coincident. The closing
line "A skip is an outstanding clause, not a passing one" prints only if SKIPPED and is no longer
printing. PHASE 9 IS CLOSED: twelve analyses across Tiers 3 to 5, full suite 1510 passed.
Three risks named in the step document as unverified, all of which came good: store.confirm
accepted two further confirmations, Binding.from_pairs absorbed the two added columns rather than
reading them as drift, and the contract model accepts agg="mean".

## Phase 10, Step 1 - the ground facts (inferential)
P10-D1. THE DEFAULT ttest_ind IS STUDENT, AND ON A REAL SHAPE IT DISAGREES WITH WELCH ACROSS
THE THRESHOLD. Measured on scipy 1.18.1: n=10 against n=40 with unequal spread, default p
0.30112502826885873, byte-identical to equal_var=True; Welch 0.045678741450132024. One dataset,
two tests, "not significant" and "significant". The test's name and its variant are part of the
result, not decoration on the method note.
P10-D2. df IS REPORTED AND IT IS FRACTIONAL. Measured: 42.5604830399426, from scipy's result
object and from the Welch-Satterthwaite formula written out in the facts file, identical to
printed precision. scipy 1.18.1 carries .df on the result, so the engine reports df whether it
computed from sequences or from group statistics.
P10-D3. THE PARAMETRIC PATH NEVER LEAVES SQL. Measured through DuckDB: count, avg and stddev per
group, six numbers into ttest_ind_from_stats, p 0.045678741450131885 against 0.045678741450132024
from the sequences -- 1.39e-16 apart, and that with DuckDB's group mean arriving as
9.999999999999998 rather than 10. The 22 analysis modules read this way already: 58 fetchall
calls, no column ever materialised into Python.
P10-D4. DuckDB's stddev IS THE SAMPLE FORM. Measured: stddev and stddev_samp both
2.138089935299395, stddev_pop 2.0, statistics.stdev 2.138089935299395. analysis/stats.py already
selects stddev(col) for its seven cells, so the number a summary prints is the number from_stats
wants and no second spelling is needed. Had it been the population form, every from-stats test
would have been wrong by sqrt((n-1)/n) -- 3% at n=20 -- and nothing would have raised.
P10-D5. A NULL IS LOUD AND A NAN IS SILENT, AND ONLY ONE OF THEM IS THE DANGER. Measured:
fetchall returns [1.0, None, 3.0] and scipy raises TypeError, unsupported operand type(s) for +:
'float' and 'NoneType'. A NULL reaching a test crashes. A nan does not -- nan_policy defaults to
propagate, one nan in a hundred returns nan for statistic and p-value with no warning, and
base.number renders that nan into a cell as the text 'nan' (P8-D1 anticipated it). LostRows
cannot catch that: the row count is right and the number is not. So nulls are dropped in SQL for
the row accounting, and nan is screened separately, because the crash is the safe case.
P10-D6. THE DROPPED COUNT IS A CELL THAT ADDS BACK. Fourteen modules end by comparing their
output against scope.analysed and raising LostRows when it does not add; Scope.__post_init__
enforces the same arithmetic one level up. A test that drops nulls has fewer rows than its scope
by construction, so what it dropped is reported the way no_date is, not left as a discrepancy.
P10-D7. nan_policy='omit' IS NEVER USED. Measured: it answers, p 6.956525525151315e-111, having
used 99 of the 100 values it was passed, and reports neither the difference nor the n behind it.
P10-D8. PAIRING COMES FROM THE CONTRACT'S GRAIN, NEVER FROM THE SHAPES. Measured on one pair of
columns: paired 2.4837047041582025e-10, independent 0.46850450414327655. Neither is an error, and
the wrong one is a silent wrong answer.
P10-D9. YATES IS APPLIED BY DEFAULT ON A 2x2 AND IS STATED. Measured: 0.019041093611085063 with
the correction, 0.009180710329776822 without. It doubles the p-value and moves it across 0.01.
P10-D10. EXPECTED-COUNT SCREENING IS OURS. Measured: every expected count 2.5 and
chi2_contingency returned p 0.2059032107320647 without comment. A zero margin it does refuse,
with ValueError, so that one is translated rather than screened for.
P10-D11. THE RANK TEST'S METHOD IS PART OF ITS NAME. Measured on the same five-against-five
sample: exact 0.6904761904761905, asymptotic 0.6761033140231469.
P10-D12. MANN-WHITNEY IS NOT A TEST OF MEDIANS AND THE INTERPRETATION LINE DOES NOT SAY IT IS.
Measured: medians identical at 9.0, p 0.010202431360127625. It tests whether one draw tends to
exceed the other, and "the median differs" is a different claim that happens to be false here.
P10-D13. A p-VALUE PRINTS AGAINST A FLOOR. Measured: t -386.7177257388124 and p exactly 0.0. A
cell reading p = 0 claims a certainty no test delivers.
P10-D14. THE ASSUMPTION LINE IS SKEW, KURTOSIS AND n, NOT A NORMALITY VERDICT. Measured on one
lognormal shape, sigma 0.25: shapiro 0.4452161863401883 at n=50 and 1.8946526894357568e-20 at
n=2000, skew 0.79226039768134. Same distribution, opposite verdicts, and the variable is n. Above
5000 scipy warns that its own p-value is not accurate.
P10-D15. THE WALD INTERVAL IS NEVER THE DEFAULT HERE. Measured: proportion_confint(0, 50) returns
(0.0, 0.0) -- an interval asserting the rate is certainly zero, from fifty observations -- against
Wilson's (0.0, 0.07134759913335874).
P10-D16. THE INTERVAL AROUND A MEAN IS THE t FORM. Measured: t-width over z-width
1.1541830261381394 at n=10, 1.0012130205514738 at n=1000. It matters at the sizes a group
breakdown produces and costs nothing at the sizes it does not.
P10-D17. EFFECT SIZE IS HEDGES' g, ALWAYS. Measured: J 0.9577464788732395 at n=10 per group,
0.9962073324905183 at n=100. At zero variance d is undefined and is refused there, not returned
as inf.
P10-D18. sample_adequacy REPORTS THE DETECTABLE EFFECT, NOT OBSERVED POWER. Measured at n=30 per
group: as d runs 0.1 to 0.8 the p-value falls 0.699953 to 0.002999 and post-hoc power rises
0.066783 to 0.861423, monotone against each other. Power computed from the observed effect
restates the p-value and adds nothing. The useful number runs the other way: 63.765610588911635
per group for d=0.5 at 80% power, reported as 64, because a fractional row count is not a
recommendation.
P10-D19. COHORTS KEY ON THE PERSON, AND WHICH COLUMN THAT IS IS MEASURED RATHER THAN READ OFF THE
NAME. Measured on Olist: 99,441 orders, 99,441 distinct customer_id, 96,096 distinct
customer_unique_id. A table called customers holding one row per order is an order-to-person
mapping. Keyed on customer_id the repeat rate is 0.000% across 99,441 entities; keyed on
customer_unique_id it is 3.119%, 2,997 repeaters of 96,096, with 348 of them ordering three times
or more.
P10-D20. A KEY THAT IS DISTINCT PER FACT ROW IS REFUSED BY NAME. The guide's rule is that
cohort_retention redirects to repeat_behaviour below 5% repeat. 0.000% is below 5%, so the
redirect fires identically whether the analyst keyed on the person or on the order: a wrong key
returns a clean grid of zeros with a recommendation printed beneath it, indistinguishable from a
correct finding about a low-repeat business. The redirect is therefore not the guard.
count(DISTINCT key) = count(*) is one query and it is asked first.
P10-D21. TIER 7 EXERCISES THE COLUMN PAGING PATH BY CONSTRUCTION. PREVIEW_COLS is 12 and MAX_COLS
is 50; a cohort grid over Olist's 26-month span is 26 columns. P8's column-paging clause skips
because no fixture pairing exceeds 7 -- region 4, product 5, channel 3 -- and Tier 7 needs no
fixture built wide.
P10-D22. NUMPY AND PANDAS STAY OUT OF src/ AND tests/. Measured 18/09/2026: both arrived as
transitive dependencies of statsmodels, neither is imported anywhere in the repository, and
pyproject declares eight dependencies of which uv add wrote two. A transitive dependency is not a
licence to import it -- a statsmodels release that drops one would take the engine with it. The
facts file is written against Python lists throughout.

MEASURED VALIDATION. tests/test_stats_facts.py, 425 lines, sha256
448e7410a9d985dfaa0bd52012de349e26fe22f5d823b368dcd32e5ea62a3e78, 25 tests, 31 functions, no
duplicate names. Full suite 1510 -> 1535 in 29.18s. The post-install suite was not run separately
before the file was written; 1535 = 1510 + 25 exactly, so none of the 1510 broke under numpy
2.5.3 and pandas 3.0.5. Versions: Python 3.12.14, scipy 1.18.1, statsmodels 0.15.0, DuckDB 1.5.5
unmoved from Phase 9.

P10-O1 IS OPEN. Rank-based tests are the first thing in this codebase that would materialise a
column. mannwhitneyu wants raw values; 99,441 Olist rows into Python would break a convention 22
modules keep. The arithmetic alternative exists -- DuckDB has rank(), U is R1 - n1(n1+1)/2 from
the rank sum, and the tie correction needs only tie-group sizes -- and so does a declared row
budget with an explicit refusal above it. Not decided.
P10-O2 IS OPEN. A DuckDB DOUBLE can hold NaN, so a measure column can carry one before any test
runs. P10-D5 measured what happens next and nothing here screens for it at the source.
P10-O3 IS OPEN. tests/test_phase8.py skips its Olist clause citing data that is present: local
Postgres holds nine tables and 99,441 orders, confirmed three times this step. The fix is the
skip condition, not the string -- the path tests/test_phase9.py uses is in the repo and works.

C61. A CHECK WAS WRITTEN AGAINST A PROPERTY BOTH OUTCOMES PRESERVE. git diff --stat on a one-row
table edit reads 1 insertion(+), 1 deletion(-) whether the row carries the old note or the new
one, so the verification offered for the Phase 9 ledger row could not distinguish applied from
unapplied and was offered as if it could. C36's shape: a check on a property that survives the
failure rather than a read of the artifact. grep of the row settled it in one line.
C62. C61 WAS RESTATED ONE REPLY AFTER IT WAS WRITTEN. The follow-up check was correctly scoped in
the step document -- whether the table still parses as a table -- and described in the
accompanying message as the check the failed one should have been. It is not; a pipe count cannot
distinguish application either. C59's pattern at one reply's distance instead of ten steps, and
for the same reason: a correction recorded in prose has nothing evaluating it.
C63. EVIDENCE WAS TRUNCATED BY A DISPLAY CAP AND THE ABSENCE READ AS A RESULT. head -30 on a grep
asked to prove a module does not use a call means no match in the first thirty lines, not no
match. Written for readability, then read as exhaustive. C39's shape. The uncapped rerun found 58
calls across 22 modules and answered the question the capped one could not.
C64. THE FACTS FILE WAS WRITTEN IN THE IDIOM OF THE LIBRARY UNDER TEST, NOT THE CALLER'S. Every
input was a numpy array -- np.linspace, np.std(ddof=1), np.median -- because that is how scipy
examples read, not because anything measured said the engine hands scipy an array. It hands over
fetchall tuples, and import numpy appears nowhere in the repository. The file would have imported
a transitive dependency to measure a convention this codebase does not use, and P10-D22 was
drafted three paragraphs above the import that breaks it. C37's shape. Rewritten against Python
lists; the rewrite is what found P10-D5, because numpy coerces None where Python raises.
C65. A TOOL WAS PRESCRIBED BECAUSE THE GENRE USES IT, NOT BECAUSE THE PROJECT DOES. The step
document called uv run ruff check; ruff is in no dependency group, no lockfile and no guide, and
no test enforces a style rule -- the only declared dev dependency is pytest. The prescription was
justified by citing C36 and C37, which are conventions measured by reading the repository rather
than enforced by a tool. C64's direction, one command later. Replaced by py_compile and an AST
pass for duplicate test names, which is the failure that would have cost real coverage.

## Phase 10, Step 2 - the selector's ground facts

P10-D23. RANK TESTS COMPUTE IN SQL. P10-O1 IS CLOSED. Measured: midrank sums from a single
windowed query, rank() + (tie - 1) / 2.0 beside count(*) OVER (PARTITION BY x), give U 21.0 on an
untied pair and 4000.0 on a tied one, identical to mannwhitneyu in both. The two-sided normal
approximation with the tie correction gives 0.7014781088666139 and 0.010202431360127625, equal to
scipy's asymptotic p-value to every printed digit; the tied figure is the one P10-D12 reached
through mannwhitneyu on two Python lists, so two independent routes land on the same float. Tier 6
materialises no column and the convention all 22 analysis modules keep extends to rank tests.
Asserted against scipy and, separately, against the complement identity U_a + U_b = n_a * n_b, so
a formula and a query wrong in the same direction cannot both pass.
P10-D24. THE CONTINUITY CORRECTION IS APPLIED. Measured both ways on both samples: with
continuity matches scipy exactly, without differs in the third digit untied (0.6547208460185769)
and the fifth tied (0.010164660476580425). mannwhitneyu defaults to use_continuity=True and so
does the engine's arithmetic.
P10-D25. THE MIDRANK IS rank() + (tie - 1) / 2.0, NEVER rank() ALONE. Measured on [1, 2, 2, 2, 5]:
rank() returns 1, 2, 5 -- the minimum rank inside the tie group -- against midranks 1.0, 3.0, 5.0.
The obvious spelling is the wrong one and it fails quietly: a smaller rank sum, a smaller U, and a
p-value that is merely plausible. Nothing in DuckDB or scipy flags it.
P10-D26. ANOVA COMPUTES FROM (n, mean, var_samp) PER GROUP. Measured on three groups: F
0.02617801047120415 against f_oneway's 0.026178010471204192, p identical at 0.9742060663526558,
and recomputed from DuckDB's own aggregates the p-value difference is 0.0 exactly. scipy ships no
f_oneway_from_stats, so this is arithmetic the engine owns rather than borrows, and it agrees.
P10-D27. var_samp IS THE SAMPLE FORM, LIKE stddev. Measured: 3.5 against var_pop
2.9166666666666665 on the same six values. P10-D4's fact for the second moment. Had it been the
population form the within-group sum of squares would be wrong by (n-1)/n per group, in the
direction that makes every F larger.
P10-D28. THE CONTINGENCY TABLE IS BUILT FROM GROUP BY AND ORDERED BY BOTH DIMENSIONS. Measured:
[('north','shop',20), ('north','web',30), ('south','shop',36), ('south','web',14)] becomes
[[20, 30], [36, 14]], chi2 9.131493506493506 on 1 df. Row and column orders are the sorted
distinct values of each dimension, so the headers a reader sees and the table scipy tests come
from one ordering rather than two.
P10-D29. SCIPY'S ROLE IN TIER 6 IS SCALARS AND ONE SMALL TABLE. What remains of it after D23 and
D26: f.sf, norm.sf, chi2_contingency, ttest_ind_from_stats, proportion_confint,
tt_ind_solve_power. Every one takes numbers or a contingency table. No analysis hands scipy a
column, and the selector's four branches now differ only in which numbers SQL computes.

MEASURED VALIDATION. tests/test_stats_facts.py sha256
78da0122f350007a5296c7d1800e4b77e25bb6d8a92c60bd737b3982369a1f7a and
tests/test_selector_facts.py sha256
08ad5723f1f88720c525660eaa23a0c055519fbf3fed3a8fd9c711c1f4d80693, 32 tests between them, full
suite 1,542 in 27.80s. The per-file split was not printed separately and is not recorded here.

STEP 1'S DIGEST IS SUPERSEDED, TWICE. That entry records tests/test_stats_facts.py at 425 lines,
sha256 448e7410a9d985dfaa0bd52012de349e26fe22f5d823b368dcd32e5ea62a3e78, 25 tests. Two rank tests
were added to the file after that line was written, taking it to 511 lines and sha256
3c182a88b5dccbd7d70c6d00f1721a5d2f73e50e37069ae8b16347473719bf47, and this step's merge took it
further still. The 22 decisions in Step 1 stand: they were drawn from the first 25 tests and none
of those changed. What does not stand is the digest, which now identifies no file on disk. C39's
point cuts both ways -- a digest proves a heredoc landed intact, and a digest left beside a file
that has since moved proves something about a file that no longer exists.

P10-O2 IS OPEN. A DuckDB DOUBLE can hold NaN, so a measure column can carry one before any test
runs. P10-D5 measured what happens next -- silent propagation to a cell reading 'nan' -- and
nothing screens for it at the source. (Closed in Step 4, and the prediction in this line was wrong: var_samp, stddev, skewness and kurtosis raise OutOfRangeException rather than propagating, so an unscreened column aborts group_stats instead of printing 'nan'. See P10-D37.)
P10-O3 IS OPEN. tests/test_phase8.py skips its Olist clause citing data that is present. The fix
is the skip condition, not the string.
P10-O4 IS OPEN. Nothing measures a group of one. Welch's denominator divides by (n - 1) per group
and the pooled form by (n1 + n2 - 2), so a dimension value with a single row after null-dropping
is a division by zero somewhere, and null-dropping is exactly what P10-D6 requires. Whether that
raises, returns nan, or returns inf decides whether it is a refusal by name or a cell reading
'nan' -- and P10-D5 already showed which of those base.number produces.

C66. A STEP WAS WRITTEN TO ANSWER A QUESTION ALREADY BEING ANSWERED, AND THE EVIDENCE WAS
BISECTED INSTEAD OF READ. tests/test_selector_facts.py was built to close P10-O1; two tests
closing it were already in tests/test_stats_facts.py. The first command of the step printed 1,543
where 1,541 was expected, and the next four exchanges narrowed where the two extra tests lived --
a combined count, then per-file counts, then a collection count -- when grep -n "^def test_" on
the changed file answers it in one line and eventually did. The +2 was not a counting anomaly; it
was the answer arriving ahead of the step written to ask for it. C63's shape in a new place: there
a capped listing was read as exhaustive, here a summary count was interrogated as though it were
evidence about its own contents. The duplicate spellings were merged before they could drift,
which is the outcome C9 and P9-O6 describe wanting and rarely get.
C67. THE WORSE SQL WAS THE ONE PROPOSED. Two midrank spellings were measured against each other:
rank() + (tie - 1) / 2.0 in one window level, against avg(row_number()) OVER (PARTITION BY x)
requiring an inner query and an averaging window outside it. The second was mine and it is worse
-- two levels for one number, and it rests on row_number()'s ordering within a tie group being
immaterial, which is true and is a thing a reader must check rather than read. The proposed tests
also asserted only against scipy, where the kept ones assert the complement identity as well, so
the proposed pair could have passed with formula and query wrong in the same direction. Recorded
because the losing version was the one with a step document behind it.
## Phase 10, Step 3 - the edges, and hypothesis_test

P10-D30. P10-O4 IS CLOSED: A GROUP OF ONE IS FORCED SELECTION ON EXACTLY ONE BRANCH. Measured:
stddev and var_samp return NULL for a one-row group -- group_compare's own summary already says a
blank spread is not zero -- and of the four branches only the two-group parametric test cannot
proceed. f_oneway returns F 4.971428571428572 and p 0.08230314431604406; mannwhitneyu returns U
4.0 and p 0.5581846494226574; chi-square returns an answer worse than a refusal (P10-D32). So a
group of one is not a uniform refusal, and the selector names which branch it forced and why.
P10-D31. THE FROM-STATS PATH FAILS LOUDLY WHERE THE SEQUENCE PATH FAILS SILENTLY. Measured:
ttest_ind_from_stats raises TypeError on the None spread; ttest_ind on the same data returns t and
p as nan with df 1.0 and no warning. P10-D5 and base.number then put the text 'nan' in a cell and
LostRows does not catch it, because the row count is right. P10-D3 chose the from-stats path on
architecture; this is a second and independent reason for it.
P10-D32. A CONTINGENCY TABLE WITH ONE ROW OR ONE COLUMN IS REFUSED BY NAME. Measured:
chi2_contingency([[10, 20, 30]]) returns chi2 0.0, dof 0 and p 1.0. No error, no nan, a clean
p-value on zero degrees of freedom. A reader sees "p = 1.0, no association" where the truth is
that there is nothing to compare. scipy will not refuse this, so the engine checks the table has
at least two rows and two columns before it asks.
P10-D33. ANOVA COALESCES A MISSING VARIANCE TO ZERO, AND ONLY THERE. Measured: coalesce(var_samp,
0) over a one-row group reproduces f_oneway's F exactly. The closed form takes (n - 1) * var per
group, which is zero at n = 1, but SQL returns NULL rather than zero, so the coalesce is the
bridge. It lives in one_way_anova and nowhere else: group_stats leaves the NULL as None, because
only the caller knows whether its branch can proceed without a variance.
P10-D34. THE CALLER CHOOSES PARAMETRIC OR RANK; THE ENGINE OVERRIDES ONLY WHERE THE CHOICE DOES
NOT EXIST. method defaults to auto, which means the parametric test unless a group has one row and
therefore no variance. P10-D14 rules out the alternative: a normality test is a test of n as much
as of shape -- the same mild skew passes shapiro at n=50 and is rejected at n=2000 -- so gating on
a normality p-value would send every large group to the rank branch and call it a finding, and a
threshold on n or skew would be a number nobody in this repository measured. Forced selection
fires on a fact a reader can check, never on a constant, and is named in the summary when it does.
P10-D35. THE TIER 6 ARITHMETIC AND ITS SQL LIVE IN analysis/inferential.py. stats.py holds the
seven expressions a summary reports; these are different numbers for a different purpose -- count,
mean, var_samp, skewness, kurtosis per group -- but they carry the risk C9 measured, so they get
one home. Every Tier 6 analysis interpolates from there rather than spelling its own.
P10-D36. THE ROWS A TEST EXCLUDES ARE ROWS IN ITS TABLE. P10-D6 required it and this is the shape:
(no group) for rows with no dimension, (no value) for rows with a dimension and no measure, each
with its count, so tested + excluded equals scope.analysed and LostRows is satisfied by
construction rather than by accident. Note the divergence from group_compare, which keeps a null
dimension as a (null) group: a null group is a group somebody can read, but it is not a group
anybody chose to compare, so a test excludes it and says so.

MEASURED VALIDATION. 23 tests in tests/test_hypothesis_test.py, all passing; suite 1,549 at
the close of this step. 22 analyses registered, hypothesis_test at tier 6. Digests:
  5ffd2c39bf9004652a9e76012a201b738420322bcd0573e3104d41986c422ddd  src/analytics_agent/analysis/inferential.py
  c7b911bb5345ce112602a2fc43d304b222fa0f3dfb2aa7f9be5cd1abbcc1ac32  src/analytics_agent/analysis/hypothesis_test.py
  3b4c2b617539b5b46abbfafd8744cbcf249a9b5e658c0f3ca1c7c0c115a3fc27  tests/test_hypothesis_test.py

APPENDED OUT OF ORDER. This section was written during Step 3 and not appended, because its
MEASURED VALIDATION line carried placeholders and nothing went back for them. It sits after Step
4's section in the file's history and before it in the numbering. Step 2's section was meanwhile
appended twice and one copy removed. Both are the same failure the phase keeps recording: the
ledger describing a state the tree does not have, or not describing one it does.

P10-O5 IS OPEN. test_declared.py's tier test never opens the build guide. (Closed in Step 4.)
P10-O6 IS OPEN. Kruskal-Wallis is not built, so method='rank' refuses for more than two groups.
(Closed in Step 4.)
## Phase 10, Step 4 - the outstanding, and the two intervals

P10-D37. NaN AND INFINITY ARE SCREENED IN SQL, COUNTED, AND SHOWN. P10-O2 closed. Measured: a
DOUBLE column accepts both and IS NOT NULL excludes neither -- 3 rows not null against 2 finite.
What follows is not what P10-D5 predicted. One NaN in a column meets its aggregates three ways:
var_samp, stddev, skewness and kurtosis all raise OutOfRangeException; max and sum propagate nan;
min skips it and returns the smallest real value. So an unscreened column reports min 1.0 and max
nan, which looks corrupt while naming no row, and group_stats does not render a nan cell at all --
it aborts on var_samp with a message identifying neither the column nor the offending rows. The
screen is therefore the difference between the module working and failing uselessly, not a
tidying of a silent answer. NOT isnan(CAST(x AS DOUBLE)) works on INTEGER and DECIMAL as well as
DOUBLE, so one spelling covers every numeric type; FINITE lives in inferential.py beside the rest
of the Tier 6 SQL. Screened rows get their own table row, (not a number), because a reader who
sees them counted separately can go and fix them, and because LostRows would otherwise fire -- 
correctly -- on rows the module drops and does not report.
P10-D38. KRUSKAL-WALLIS IS BUILT AND THE RANK BRANCH NO LONGER STOPS AT TWO GROUPS. P10-O6 closed.
H = 12/(N(N+1)) * sum(R_i^2/n_i) - 3(N+1) over the tie correction, from the same midrank sums
P10-D23 measured, read against chi-square on k-1. Measured against scipy.stats.kruskal to every
printed digit: 6.201098901098902 untied, and 7.691358024691331 with a tie term of 80,910, with
p 0.045024456883389956 and 0.021371884859535267 matching in both. It needs no variance -- H is
5.142857142857142 with a one-row group among three -- so P10-D30's forced selection now extends
past two groups rather than refusing.
P10-D39. THE TIER MAP READS THE BUILD GUIDE. P10-O5 closed, and P9-O10 with it. The previous test
compared the registry against a dict typed from the guide; it caught Step 3's omission and would
have kept passing had the guide changed instead. It now parses the tier headings and the
backticked listing beneath each. It deliberately does not assert that every name in the guide is
registered: Tier 7's two and Tier 8's are legitimately unbuilt, and a test that fails for work not
yet done is one people learn to ignore. analysis/__init__.py's docstring no longer carries a
count, because a count in a docstring goes stale every phase and nothing checks it.
P10-D40. THE INTERVAL AROUND A MEAN IS THE t FORM AND THE INTERVAL AROUND A SHARE IS WILSON.
P10-D16 and P10-D15 as built. A group with fewer than two rows gets its mean and no interval,
stated rather than left blank: one row does produce a mean, it just produces no evidence about
what the next row would be. The summary spends a line on what a 95% interval means -- a property
of the procedure across repeated samples, not a probability about this interval -- because that is
the sentence readers get wrong.
P10-D41. EFFECT SIZE IS REPORTED IN COHEN'S VOCABULARY AND SAID TO BE A VOCABULARY. Hedges' g for
two groups, eta squared for more, Cramer's V for two dimensions, each banded small/medium/large
and each followed by the sentence that the bands were proposed for psychology and that what counts
as large is a question about the subject. Bands shape a word, never a refusal or a branch.
P10-D42. P10-O3 IS NARROWED, NOT CLOSED. test_phase8.py's Olist clause said "no Olist data is on
disk", which P9-O1 recorded as false and Phase 10 Step 1 confirmed false a third time. The
sentence now says the clause is unwritten rather than unreachable. Writing it -- all nine Tier 1-2
analyses against Olist through the real gate -- remains open.

MEASURED VALIDATION. Full suite 1,579, from 1,549: 23 for hypothesis_test and 7 for the
ground facts of this step. 24 analyses registered. Digests:
  5ffd2c39bf9004652a9e76012a201b738420322bcd0573e3104d41986c422ddd  src/analytics_agent/analysis/inferential.py
  c7b911bb5345ce112602a2fc43d304b222fa0f3dfb2aa7f9be5cd1abbcc1ac32  src/analytics_agent/analysis/hypothesis_test.py
  3b4c2b617539b5b46abbfafd8744cbcf249a9b5e658c0f3ca1c7c0c115a3fc27  tests/test_hypothesis_test.py
  cd83d87b20a4c30985bd902fed983c7703c95a7a86942b3f99719168bd4997fe  tests/test_nan_and_kruskal_facts.py

P10-O3 IS STILL OPEN, narrowed: the skip reason is now true, the clause is still unwritten.
P10-O7 IS OPEN. confidence_interval and effect_size have no tests.
P10-O8 IS OPEN. sample_adequacy is the fourth Tier 6 analysis and is not built. P10-D18 already
settled what it reports: the effect detectable at the observed n, not observed power.


## Phase 10, Step 5 - tests for the two intervals

P10-D43. THE LARGER GROUP IS NAMED AS THE LARGER. Found while writing the tests, not by running
the module: effect_size printed "{first} exceeds {second}" using the order SQL returned the
groups in, which is alphabetical. On a fixture where arm a means 11.5 and arm b means 22.5 it read
"a exceeds b by 11.0" -- the number right, the sentence backwards. A correct figure inside a wrong
claim reads as authoritative and is worse than either alone. The groups are now ordered by which
mean is larger before they are named.
P10-D44. A ONE-ROW GROUP GETS ITS MEAN AND A BLANK INTERVAL, NOT A ZERO-WIDTH ONE. One row does
produce a mean; it produces no evidence about what the next row would be, and a blank says that
where a zero-width interval would claim certainty. The same asymmetry from the sizing side:
effect_size refuses a magnitude entirely, because a difference between a group of one and a group
of twelve is real and has no standard deviation to be measured in -- and says so, pointing at the
rank comparison that does not need one.
P10-D45. COHEN'S BANDS ARE TESTED AS A VOCABULARY. band() is asserted on magnitude, not sign: a
large negative effect is large. The bands shape a word in a sentence and never a branch, a
refusal, or a threshold, and the summary says in its own words that they were proposed for
psychology and that what counts as large is a question about the subject.
P10-D46. THE INTERVAL TESTS ASSERT ARITHMETIC, NOT ONLY VOCABULARY. low < mean < high, the
half-width is half the span, and a 99% interval is wider than a 90% one on the same rows. A test
that only checks the module said "Wilson" would pass over an interval computed wrongly.

MEASURED VALIDATION. tests/test_confidence_interval.py sha256 0f1263c079482e29a470d7383d35ef378e7580b03a828cd7997133d2378aa2b0, 229 lines, 15
tests; tests/test_effect_size.py sha256 c27ef0475331dcd423b68f9a71c92b51dbd68ff9e3f582b1c051335439c58fd6, 237 lines, 18 tests. Full suite 1,612.
24 analyses registered, three at tier 6.

P10-O7 IS CLOSED.
P10-O8 IS OPEN. sample_adequacy is the fourth Tier 6 analysis and is not built. P10-D18 settled
what it reports: the effect detectable at the observed n, never observed power, because power
computed from the observed effect was measured monotone against the p-value across all eight
points and therefore carries nothing the p-value did not.
P10-O3 IS STILL OPEN, narrowed in Step 4: the skip reason is true, the clause is unwritten.

## Phase 10, Step 6 - sample_adequacy, and Tier 6 complete

P10-D47. sample_adequacy REPORTS THE DETECTABLE EFFECT AND REFUSES TO REPORT OBSERVED POWER.
P10-O8 closed, on P10-D18's measurement: at n=30 per group, as d ran 0.1 to 0.8 the p-value fell
0.699953 to 0.002999 and post-hoc power rose 0.066783 to 0.861423, monotone throughout. Power
computed from the effect you observed is the p-value rearranged, and printing both would look
like two findings and be one. What the reader does not already have is the other direction: the
smallest difference the rows in scope could reliably detect, reported in standard deviations and
in the measure's own units, beside the difference actually present and the rows that smaller
effects would need. The refusal is stated in the summary rather than implied by absence, because
a reader who expected observed power should learn why it is missing.
P10-D48. A NON-SIGNIFICANT RESULT IS GIVEN ITS SECOND READING. hypothesis_test says a difference
was not detectable; it cannot say whether the groups are alike or the rows were too few. When the
observed difference falls below the detectable floor, sample_adequacy says so in those words: a
statement about the row count, not about the groups. That sentence is the reason the analysis
exists and is not an aside.
P10-D49. MORE THAN TWO GROUPS IS REFUSED BY NAME, NOT APPROXIMATED. The k>2 analogue rests on
FTestAnovaPower, which nothing in this repository has measured. The same call as Kruskal-Wallis
before Step 4 built it: an unmeasured number here would be a claim about what a reader's data
could resolve, which is worse than having no answer.
P10-D50. TIER 6 IS COMPLETE. hypothesis_test, confidence_interval, effect_size, sample_adequacy --
the four the build guide names at line 619, all registered, all reading aggregates only. No
analysis in the tier materialises a column; scipy and statsmodels are used for distribution tails
and for one power solve, each taking scalars.

MEASURED VALIDATION. src/analytics_agent/analysis/sample_adequacy.py sha256 e4cd9a83b70e06a13ee9f8d8d8e67ecd1f393aec9743bfa400a9bc1bab80a917,
161 lines; tests/test_sample_adequacy.py sha256 3e99137f863196626237a42c8bae9f85f70afe75be69e7df8de41410e03ded03, 212 lines, 16 tests. 25
analyses registered, four at tier 6. Full suite 1,628.

P10-O8 IS CLOSED.
P10-O3 IS STILL OPEN, narrowed in Step 4: the skip reason is true, the clause is unwritten.

## Phase 10, Step 7 - Tier 7 ground facts, and repeat_behaviour

P10-D51. A COHORT OFFSET IS A PERIOD COUNT, SO BOTH ENDS ARE TRUNCATED BEFORE THEY ARE
SUBTRACTED. Measured: date_diff('month', ...) over truncated months gives 1 from January to
February, 0 within January, and 25 from November 2016 to December 2018. Untruncated it counts
something else, printed in the same run. Every cell of a cohort grid is an offset, so the
truncation is not tidiness -- it is the difference between a grid and a grid shifted by one.
P10-D52. A COHORT GRID CANNOT ADD BACK TO ROWS, AND KEEPS A DIFFERENT ACCOUNT. One person
occupies several rows, so LostRows' usual arithmetic does not apply. What does hold, and what is
checked: every person belongs to exactly one cohort, so cohort memberships equal distinct people.
repeat_behaviour keeps both books -- events add back to scope.analysed, people add to the distinct
key count -- and says in the summary that the people column is not a row count and is not meant
to be one.
P10-D53. A KEY DISTINCT PER ROW IS REFUSED BY NAME. Step 1 Part D measured customer_id at 99,441
distinct across 99,441 orders against customer_unique_id's 96,096, and 0.000% repeat against
3.119%. count(DISTINCT key) = count(*) is one query and repeat_behaviour asks it before anything
else. The refusal says what the column is rather than what the analysis cannot do: a key that
never repeats describes events, and reporting that nobody ever returns would be a fact about the
column, not about behaviour.
P10-D54. repeat_behaviour IS BUILT BEFORE cohort_retention BECAUSE THE REDIRECT POINTS AT IT. The
guide's rule is that cohort_retention recommends repeat_behaviour below 5% repeat. Shipping that
recommendation before the target exists is the same shape as a ledger describing a state the tree
does not have, which this phase has now recorded three times.

MEASURED VALIDATION. tests/test_cohort_facts.py sha256 1f74a70b33adb56635ba29c778c7d71ba0e66ab18411d015ac249a90e9658ce8, 198 lines, 7 tests;
src/analytics_agent/analysis/repeat_behaviour.py sha256 5953a99337c46474d2595a74fc2c88e12c8c1883bcb0e629f1c4b960a11fa03a, 173 lines. 26 analyses
registered, one at tier 7. Full suite 1,635. The digest is the one after the ::DATE
cast of section 1.1; the pre-cast file was 6a307003 and never passed.
OLIST FIGURES NOT TAKEN. Section 2 of that step was not run, so the people, cohort
and offset counts it asked for are absent rather than wrong. P10-O11 carries them.

P10-O9 IS OPEN. repeat_behaviour has no tests.
P10-O10 IS OPEN. cohort_retention is not built.
P10-O3 IS STILL OPEN, narrowed in Step 4.

## Phase 10, Step 8 - cohort_retention, and Tier 7 complete

P10-D55. A COHORT GRID SHOWS PEOPLE, NOT PERCENTAGES, WITH THE COHORT'S SIZE BESIDE ITS LABEL. A
percentage computed over three people is noise wearing a rate's clothes, and a reader cannot tell
one from a rate over three thousand once the denominator is gone. The size column restores it.
P10-D56. NO COHORT IS SUPPRESSED AND NONE IS FLAGGED AS TOO SMALL. Any cutoff would be a number
nobody in this repository measured -- the objection that ruled out a threshold-driven selector in
Step 3 -- and a suppressed cell is indistinguishable from an empty one, so suppression removes
information while looking like care. The size column is the same information without the
invention.
P10-D57. THE 5% REDIRECT IS THE GUIDE'S NUMBER AND IS APPLIED AS A WARNING, NOT A REFUSAL. The
guide's rule at line 625 is that cohort_retention warns and recommends repeat_behaviour below 5%
repeat, so the grid is still drawn and the sentence beside it says almost every cell beyond +0 is
empty and names the analysis that reports the same fact in four rows. Step 1 Part D established
why the threshold cannot be the guard on its own: it fires identically at 0.000% and at 3.119%,
so the key check (P10-D53) runs first and separately.
P10-D58. THE GRID STOPS AT THE COLUMN CAP AND SAYS THE LATER COLUMNS EXIST. MAX_COLS is 50 and
the headers are the cohort label, its size, then one column per offset, so 48 offsets fit. Olist's
26-month span is comfortably inside that and still past the 12-column preview, which is the case
Phase 8's column-paging clause skips for want of a wide enough fixture.
P10-D59. TIER 7 IS COMPLETE, AND SO IS THE ANALYSIS TIER LIST. cohort_retention and
repeat_behaviour, the two the build guide names at line 623. Twenty-seven analyses registered
across seven tiers, none of which materialises a column.

MEASURED VALIDATION. tests/test_repeat_behaviour.py sha256 2750fe15b9311cf7a41077531feb9454a0409cf8b861e26424a1297db4212c69, 165 lines, 11
tests; src/analytics_agent/analysis/cohort_retention.py sha256 bcf0a546f0e73f4d68dc28615b22633c7c1af84e9a37b445ccd7bbf9692e0d92, 171 lines;
tests/test_cohort_retention.py sha256 793a26fcc1060267b56cffe09f017a065cde0b71acd7a2c7ac6b74c364d95cb8, 220 lines, 15 tests. 27 analyses
registered, two at tier 7. Full suite 1,661.

P10-O9 IS CLOSED.
P10-O10 IS CLOSED.
P10-O3 IS STILL OPEN, narrowed in Step 4: the skip reason is true, the clause is unwritten.
P10-O11 IS OPEN. Neither Tier 7 analysis has been run against Olist. Step 1 Part D measured the
figures they should produce -- 96,096 people, 2,997 repeaters, 3.119% -- and nothing has yet
checked that the modules reproduce them.

## Phase 10, Step 9 - the Done-When, on the real database

P10-D60. THE DONE-WHEN IS PROVEN. tests/test_phase10.py, 35 passed, 0 failed, 1 skipped, against
local Postgres. hypothesis_test names Welch on two groups, one-way ANOVA on more and chi-square on
two dimensions, each reporting its variant and its df; cohort_retention warns at 3.119% and names
repeat_behaviour. Both halves of the guide's line 939, on real rows rather than a fixture.
P10-D61. P10-O11 IS CLOSED: THE MODULES REPRODUCE THE HAND MEASUREMENT. Step 1 Part D counted
96,096 people, 2,997 repeaters and 3.119% by hand in psql on 18/09/2026. repeat_behaviour through
the real gate produces the same three figures on 19/09/2026. The value of that is not the
agreement but the independence: one route was a person writing SQL against public.orders joined to
public.customers, the other was the module's own query under a confirmed contract, and a shared
mistake would have had to be made twice in two spellings.
P10-D62. THE ACCEPTANCE SCRIPT TAKES ITS TABLE AS AN ARGUMENT. Phase 9's confirm_contract, run and
mount close over a module-level TABLE. Phase 10 needs three: order_payments carries the only
numeric measure in reach (orders is three VARCHARs and five TIMESTAMPs), and the Tier 7 person key
lives on customers while the date lives on orders, so they are joined in the workspace. That is a
departure from Phase 9's shape and is stated in the docstring rather than left to be noticed.
P10-D63. installment_plan IS DERIVED, NOT INJECTED. The Welch branch needs a dimension with two
values and Olist's payment table has none -- payment_type holds four or five. payment_installments
> 1 is a real distinction computed from real rows, which is a smaller departure than Phase 9's
clause four, where two wholly synthetic measures were added to prove correlated_shift. Both are
recorded rather than hidden, on the same argument: a fixture built to make a clause pass is worth
less than a clause that says what it was built on.
P10-D64. THE DERIVED TABLES ARE VISIBLE TO THE GATE. P9-O4 records that an attached catalog is not
a loadable dataset, because state._loadable_tables reads db.user_tables. Whether a table CREATEd
in the workspace from copied ones would be visible was not known and is now: it is. Every clause
above ran against tables built that way.

MEASURED VALIDATION. tests/test_phase10.py sha256
fe22f08e8183111272fd6f539a974c30704e059bb71241870b3ad2212cbfa3ae, 391 lines, 6 clauses, 35
passed, 0 failed, 1 skipped. Unit suite unchanged at 1,661: the acceptance script defines no
test_ functions and pytest collects nothing from it, as with test_phase9.py.

P10-O11 IS CLOSED.
P10-O3 IS STILL OPEN, and is now scoped. tests/test_phase8.py has no Postgres path at all -- its
loader is load(fixture: Path, dataset_name: str) off a CSV, with no SOURCE, no load_table and no
LoadRefused -- and its CALLS dict is keyed to clean_sales' column names, so nothing transfers.
orders cannot carry all nine: one usable dimension and no numeric measure leaves cross_tab,
group_compare, pareto and concentration with nothing to compute. The shape it needs is
order_payments with the derived installment_plan, the three imports that file has never had, a
parameterised run, and a second CALLS dict beside the fixture one. That is a step, not a clause,
and it belongs to Phase 8's Done-When rather than Phase 10's.

## Open-item register - reconciled 19/09/2026

Written because the ledger could not answer "what is outstanding". Closures had been recorded two
ways -- as their own line, and folded into a decision's sentence -- so a grep for "IS CLOSED"
found six of ten. Three items were also restated in later steps and appear twice. Nothing above
is edited; this is the index the file lacked.

CLOSED. P9-O1, in Phase 9 Step 3: tests/test_phase9.py reaches local Postgres.
CLOSED. P9-O10, in Phase 10 Step 4 (P10-D39): the tier test parses the build guide.
CLOSED. P10-O1, in Phase 10 Step 2 (P10-D23): rank tests compute in SQL.
CLOSED. P10-O2, in Phase 10 Step 4 (P10-D37): non-finite values screened in SQL.
CLOSED. P10-O4, in Phase 10 Step 3 (P10-D30): a group of one is forced selection on one branch.
CLOSED. P10-O5, in Phase 10 Step 4 (P10-D39): the tier map reads the guide.
CLOSED. P10-O6, in Phase 10 Step 4 (P10-D38): Kruskal-Wallis built.
CLOSED. P10-O7, in Phase 10 Step 5: confidence_interval and effect_size have tests.
CLOSED. P10-O8, in Phase 10 Step 6 (P10-D47): sample_adequacy built.
CLOSED. P10-O9, in Phase 10 Step 8: repeat_behaviour has tests.
CLOSED. P10-O10, in Phase 10 Step 8: cohort_retention built.
CLOSED. P10-O11, in Phase 10 Step 9 (P10-D61): the modules reproduce the hand measurement.

STILL OPEN, and unverified: P9-O2, P9-O3, P9-O4, P9-O5, P9-O6, P9-O7, P9-O8, P9-O9, P9-O11,
P9-O12, P10-O3. Of these only P9-O4 and P10-O3 have been looked at since they were written. The
other nine are recorded open and nobody has checked whether they still are -- a later step may
have fixed one incidentally, the way P9-O11 may have been closed by P10-D39 rewriting the very
test it names.

SUPERSEDED 21/09/2026, and left standing rather than edited. The paragraph above records the state
as it was BEFORE the fixes that landed in the same commit that wrote it; C78 says how. The current
list is under "Cleanup Step 2" at the end of this file. Open there: P9-O4's feature half,
scoped as a design question -- one, not eleven, and each of the others checked against the code.

DUPLICATED, from being restated in a later step: P9-O10, P10-O2, P10-O3, P10-O8.

C68. AN OPEN ITEM WAS CLOSED IN PROSE RATHER THAN IN THE INDEX. Twelve items closed across Phases
9 and 10; six said so on a line of their own and six were folded into a decision's sentence, so
the ledger's own grep undercounted by half. The convention was never stated, so both spellings
looked right while they were being written. A record whose format varies cannot be queried, and a
record that cannot be queried is a diary rather than a ledger. Closures now get their own line.

C71. THE SAME QUOTE-NESTING ERROR WAS MADE THREE TIMES, AND THE THIRD ONE SHIPPED. A Python
string inside a python3 heredoc inside a bash heredoc is three levels of quoting. Attempt one
wrote multi-line strings in single quotes; attempt two ended a triple-quoted literal with
"DATE\" and produced four quote characters; both were syntax errors that wrote nothing, which is
the harmless failure. The third ended a replacement with (P9-O4)."\"" and DID write, leaving
src/analytics_agent/ingest/postgres.py unparseable and the whole suite uncollectable until it was
repaired. The rule that follows is mechanical rather than a resolution to be careful: a patch
script never ends a replacement literal on a quote character, and a file that is being rewritten
rather than patched is written whole with cat > so the nesting does not arise. Twice it cost
nothing; once it cost a broken tree, and the difference was luck.

CLOSED. P10-O3, 19/09/2026. tests/test_phase8.py now runs all nine Tier 1-2 analyses against
Olist under a real contract. It needed the Postgres path that file had never had -- load_table,
LoadRefused, a parameterised run_on, a second contract builder and a second CALLS dict -- because
its own loader reads a CSV fixture off disk. No single Olist table carries a numeric measure, a
date and a wide dimension, so order_payments, orders and customers are copied and joined, and
installment_plan is derived from payment_installments. P9-O4 is why they are copied rather than
queried in place.

CLOSED. The column-paging skip, 19/09/2026. Its reason was true when written -- region 4,
product 5, channel 3, so the widest fixture cross_tab is seven columns against a twelve-column
preview -- and Olist's customer_state has twenty-seven values, so clause 5 pages on real data.

C75. A PREDICTION MADE IN STEP 1 WAS FALSIFIED BY A DECISION TAKEN IN STEP 3, AND NOTHING
CONNECTED THEM. Phase 10 Step 1 audited Phase 8's five skips and recorded that
ANALYSIS_RESULT_UNSOUND would become provokable once Tier 6 existed, because Tier 6 drops nulls
by construction. P10-D36 then required every Tier 6 and 7 module to report what it drops as a row
that adds back, precisely so LostRows stays satisfied -- which is the right design and which makes
the skip's reason true again. So the skip stays, and the audit item that promised otherwise was
wrong from Step 3 onward without anything noticing. The stale skip reasons this cleanup keeps
finding are records that went false; this is the mirror -- a prediction that a later decision
falsified. Both are the same failure: a claim and the thing it describes, edited separately.

THE RENDERED SCHEMA SKIP IS PERMANENT AND SHOULD NOT BE REVISITED. FastMCP builds the JSON schema
from the function signature and no script reaches what a client displays. A call proves
forwarding, not the schema. Recorded here so a later audit does not count it as outstanding work.

THE ROLE TRAP IS A GUIDE CORRECTION, NOT A CODE CHANGE. The guide says summary_stats must skip
role=identifier. role is a proposal-time heuristic in evidence.py that never reaches a confirmed
contract, so the rule is unenforced -- but the protection it describes is real by another
mechanism: analyses are restricted to the contract's declared measures, so an identifier is out
of scope because nobody declared it. The guide names the wrong mechanism for a behaviour that
holds. P10-O13 carries the sentence.

P10-O13 IS OPEN. The build guide's role=identifier rule describes a protection that exists by a
different mechanism than the one it names. One sentence, in the guide.

## Cleanup Step 1 - the remaining open items, 21/09/2026

Worked from a plan (`close_remaining_items.md`, 20/09/2026) whose four defects were measured
before any of it ran; they are C77. The step document is docs/steps/cleanup_step1_close_open_items.md.

CLOSED. P9-O3, 21/09/2026, verified rather than done. server.py:750-759 already scoped the claim
to a value and named the None case, tools.py stripping it, and the bins=10 / bins=None contrast.
The fix landed in 03ea6ed; the ledger did not record it. See C77.

CLOSED. P9-O6, 21/09/2026. declared.py:39 owns ADDITIVE_AGGS and period_compare.py:51 and
growth_decomposition.py:62 both derive from it -- that half landed in 03ea6ed unrecorded. The
third copy was found in this step: NO_MEMBER = "(no {dimension})" was restated in
driver_analysis.py, growth_decomposition.py and mix_shift.py, which is the same ruling in a third
column. It now lives at base.py:42 and the three import it. One declaration remains in src/.

CLOSED. P9-O7, 21/09/2026, by reading. The item said the answer "depends on an except clause
below tools.py:119, which has not been read". Read: `except (TypeError, ParamsInvalid)` returns a
Refusal carrying ANALYSIS_PARAMS_INVALID, the analysis summary as state, and an example call. A
forgotten required parameter surfaces as a refusal a caller can act on, not a traceback out of
the MCP surface. No code change was needed; the item was an unread file, not a defect.

CLOSED. P9-O9, 21/09/2026, verified rather than done. declared.py:133 defines require_dimension
and growth_decomposition.py:108 calls it; 03ea6ed deleted the inline eight-line block. Nineteen
call sites across the tier now share one refusal text.

CLOSED. P10-O13, 21/09/2026. The build guide's line 923 said summary_stats must enforce
role=identifier. role is a proposal-time heuristic in evidence.py and never reaches a confirmed
contract, so nothing could enforce it at analysis time -- but the protection holds by a narrower
and stronger mechanism: every analysis reads only the contract's declared measures. The guide
named the wrong mechanism for a real behaviour, which is worse than naming none, because a
reader trusts it. The guide's Phase 8 row was corrected with it.

The role trap stopped being a skip. tests/test_phase8.py carried it as a skip for two phases, and
once the guide no longer said what the skip quoted, the reason went false -- the stale-skip
failure this ledger keeps recording, created by this step's own edit. It is now two checks
against Olist. The first assertion written was the wrong shape: it tested that "order_id" was
absent from the output and failed, because summary_stats names the key columns it did NOT
summarise. Measured: "Not summarised: key column(s) order_id, payment_sequential. A column is
summarised here when the contract declares it as a measure." The identifier appears because the
protection fired and said so. The check now asserts that line. Phase 8 acceptance 94/0/4 -> 96/0/3.

CLOSED. P9-O2, 21/09/2026. tests/test_phase9.py clause five reports and asserts the temporal
shape of order_reviews, order_payments and order_items from the real database, so
calendar_coverage's generality rests on evidence rather than on construction. The item's three
claims, unchecked since Phase 4, all hold: order_reviews has two date columns
(review_creation_date, review_answer_timestamp), order_payments has none, order_items has one
(shipping_limit_date). The first run reported four, none and two. load_table attaches the source,
so the table exists in two catalogs at once and a query filtered on table_name alone counts every
column twice. The clause now filters on table_catalog = current_database(). Had the printed
numbers been recorded rather than questioned, "order_reviews has four date columns" would be in
this file. Phase 9 acceptance 16/0/0 -> 19/0/0.

CLOSED. P9-O8, 21/09/2026. A null bucket is now named for the column that was empty. The item
asked which of two spellings wins and this answers it: the Tier 4 spelling, because "(no region)"
says which column was empty and "(no group)" does not. In hypothesis_test, confidence_interval,
effect_size and sample_adequacy the constant was both the displayed label and a dictionary key --
excluded[NO_GROUP] -- so the two were separated: the constants became keys that are not display
strings ("no_group"), and a _shown() helper builds the label from the column name. Ten display
sites across four modules, in three shapes, not the four uniform ones the plan assumed. The nine
test assertions on "(no group)" and "(no value)" are the map that found them.

P9-O8's helper is built one branch at a time, and the reason is measured. A dict literal of all
three labels evaluates f"(no {measure})" whichever key is asked for, and confidence_interval's
share branch has a dimension and no measure in scope. The association branches of hypothesis_test
and effect_size have two dimensions and no measure at all -- a row there is missing either of
them -- so _shown's measure spelling would name a column that is not what is absent. Those four
sites use _shown_pair(dimension, second) and render "(no arm or channel)".

C77. A PLAN AND THE TREE IT DESCRIBED WERE WRITTEN A DAY APART AND DISAGREED IN FOUR PLACES.
`close_remaining_items.md` was read before it was run, and four of its claims were false against
the repository. (1) It wrote `from .base import NO_MEMBER` into four modules on the strength of
the sentence "now homed in base.py"; base.py.__all__ did not contain it and the name existed as
three separate literals, so the import would have raised ImportError in four modules at once.
(2) It closed "P10-O12", an identifier that has never existed in this file -- the item is P9-O8,
recorded at line 3692, and closing it under an invented number would have left P9-O8 open
permanently. (3) Its section 3 said "the edits follow in one block" and no block followed, so run
alone it left every excluded.items() loop printing the raw key "no_group" as a user-visible label.
(4) Its commit message named a closure its ledger section did not write, which is C68 and C76 in
one line. The shape is the one this file keeps recording -- a claim and the thing it describes,
edited separately -- and this instance is worth naming because the claim was a plan, which is the
document most likely to be trusted without being checked.

C78. THE REGISTER RECORDED THE STATE BEFORE THE FIXES THAT LANDED IN THE SAME COMMIT. 03ea6ed is
titled "Open items: P9-O3, O6, O9 and P10-O3 closed". Its only change to this file was adding the
81-line open-item register, and that register lists P9-O3, P9-O6 and P9-O9 under STILL OPEN while
the same commit changed exactly the code those three items name. The commit message was right and
the index was wrong, which is the mirror of C76 rather than a repeat of it: there the message
promised work the tree lacked, here the tree held work the index denied. Both come of writing the
record and the thing it records in one pass and checking neither against the other. The register
was written to stop a grep undercounting closures (C68) and shipped undercounting them itself.

P9-O4's FEATURE HALF REMAINS OPEN, SCOPED 21/09/2026. _loadable_tables is one line at
state.py:197, and widening it changes what a loaded dataset means at state.py:129 where
require_contract consults it and at 233 where get_workflow_state walks it. An attached catalog's
table would need a Binding read from the attached catalog rather than the workspace, a row count
and age DatasetState expects, and an answer for what validate_dataset and the cleaning tools mean
against a table they cannot write to. That is a design question about what a dataset is, not a
filter to loosen, and it is worth less than it looks now that nothing promises it: the cost is a
capability the product lacks rather than a claim it makes falsely.

STILL OPEN after this step, and each checked against the code on 21/09/2026 rather than inherited:
P9-O4's feature half (scoped above). P9-O5: no test in any Tier 3 file asserts how base.number()
renders a float, so the decimal places in a mean column are unasserted; stats.py owns
STAT_HEADERS, stat_exprs, stat_cells and ranked_totals and no mean renderer, so the item's
suggested home does not exist as described. P9-O11: test_declared.py's tier check iterates
catalogue() and cannot catch a map entry whose analysis was never registered -- 03ea6ed's new
test is the roster check (C72), a different direction, and does not close this. P9-O12:
correlated_shift still imports _within and MIN_SEGMENT from changepoint.

MEASURED VALIDATION, 21/09/2026. Unit suite 1662 -> 1664; the two added are the association-label
tests in test_hypothesis_test.py and test_effect_size.py, which cover a branch that had none --
region and channel are non-null on all fourteen fixture rows, so `missing` was always zero and
the label was never rendered by a test until arm x channel was used. Acceptance: test_phase8.py
96 passed, 0 failed, 3 skipped (from 94/0/4); test_phase9.py 19 passed, 0 failed, 0 skipped (from
16/0/0); test_phase10.py 35 passed, 0 failed, 1 skipped, unchanged. Three skips remain, each
recorded: ANALYSIS_RESULT_UNSOUND, the rendered MCP schema (permanent), and the non-finite screen.
Digests:
  4c6e97707397904f126e6de6e92fd5eca2d6f34e6eb15f4b4e11758e5305b345  docs/analytics_agent_build_guide_v1.2.md
  6d290033ab77bee29e52993fc60d62731a6d9a32bdab1083eec89f39ddb1058b  src/analytics_agent/analysis/base.py
  f484d44159417dac51da08ce95b3d0a844d6c87c96fe62134b28b0bdc6508d49  src/analytics_agent/analysis/driver_analysis.py
  5c68533de7927338f81caf65933b47df985b589e169ab6247754a35fb11b8eff  src/analytics_agent/analysis/growth_decomposition.py
  13874f57a269d0ce631775d82e84d6f170e11cf6e2453eedc93413f1cb75e5f2  src/analytics_agent/analysis/mix_shift.py
  9b9a5d5a7acc9e92d299f5b36962d4ac476291dfb008918ed26de48d4fbd9394  src/analytics_agent/analysis/hypothesis_test.py
  845b05b070956b403517a40cd541c14c414c3533d7f03497497d1714b45f923d  src/analytics_agent/analysis/confidence_interval.py
  ca8ff94222f982a6f2428b298c9c6222528046cdcd6329beecfcfa96e6c31ce6  src/analytics_agent/analysis/effect_size.py
  6a5b957e6a66ba1692e15e9fe8b0e0fc91a31006fb8ed067cb693c2c1bbd1039  src/analytics_agent/analysis/sample_adequacy.py
  5c30e5ec987dff603f366bc7c4adfcd16649967b6358f51a92e452f3f7f68b16  tests/test_phase8.py
  f5a719c3ee829f7d49fca1912e8b60cce96a2a6ce1ddb4d1359a9ad78b278b7e  tests/test_phase9.py

## Cleanup Step 2 - the last three small items, 21/09/2026

Step document: docs/steps/cleanup_step2_last_three_items.md. P9-O4's feature half stays open by
decision and is scoped under Cleanup Step 1.

CLOSED. P9-O5, 21/09/2026. base.number() has been handed a float since P9-D22 and no test in any
Tier 3 file asserted how it renders one, so the decimal places in a mean column were unasserted.
tests/test_stats_facts.py now pins them, measured rather than recalled: 10.0 -> '10' (trailing
zeros dropped), 0.05 -> '0.05', 2.5 -> '2.5', -0.125 -> '-0.125', 1234567.89 -> '1,234,567.89',
23.583333333333332 -> '23.5833' (four places), and Decimal('10.50') -> '10.50', not rounded,
because a declared scale is a fact about the column. The item's suggested home does not exist:
stats.py exports STAT_HEADERS, MAX_GROUPS, stat_exprs, stat_cells and ranked_totals and no mean
renderer, so base.number() is the renderer and there was nothing for seasonality to adopt.

1e-07 RENDERS AS '0', AND THAT IS NOW PINNED. Rounding to four places gives 0.0000, the two
rstrips leave the empty string, and base.py:76's `text or "0"` fills the cell. The behaviour is
right -- a cell cannot be blank -- and it is invisible: a reader sees zero where the value was
not zero. Found while measuring for P9-O5 rather than looked for.

CLOSED. P9-O11, 21/09/2026, and restated first because P10-D39 changed what it refers to. The
item was written when test_declared.py's tier check compared the registry against a dict typed
out in the test; P10-D39 replaced that dict with the build guide, parsed. The direction it names
was still unasserted: the test computed `unbuilt = sorted(set(tiers) - registered)` and then
asserted `unbuilt == sorted(unbuilt)`, which is true of every list and tests nothing, so a name
the guide carries that nothing registers passed silently. It now asserts that every guide-named
analysis below Tier 8 is registered. Tier 8 is exempt because it is legitimately unbuilt (Phase
15) -- and measured: its listing is prose, "Port SARIMAX/Prophet from Mandi", with no backticked
names, so the parse finds none of it and `set(tiers) - registered` is empty today. Proved able to
fail rather than assumed: with pareto removed from REGISTRY the test raises "the build guide names
pareto below Tier 8 and nothing registers them". The assertion it replaced could not fail at all.

CLOSED. P9-O12, 21/09/2026. correlated_shift imported _within, MIN_SEGMENT and SEPARATION from
changepoint -- a private name crossing a module boundary. The alternative the item names, a second
copy of the statistic, is what P9-O6 records going wrong, so the sharing is declared instead of
removed: _within is renamed within, and changepoint's __all__ carries within, MIN_SEGMENT and
SEPARATION beside the analysis. A name another module depends on is part of this module's surface
whether or not it is spelled that way. Five sites; no _within remains in src/.

C79. A WRONG ANSWER WAS GIVEN FROM A TOOL USED WRONGLY, AND THE OUTPUT LOOKED LIKE A RESULT.
Asked whether everything was closed, the check ran `comm` over two lists sorted with `sort -V`.
comm requires both inputs in the same lexical collation, and version sort puts P10 after P9, so
comm read the files as unsorted and reported P10-O1 through P10-O13 as both "opened but never
closed" and "closed but never opened" simultaneously -- which cannot both be true and was the
tell. Re-run with plain `sort`: 24 opened, 20 closed, 4 open. The failure is the family this file
keeps recording, one step earlier than usual: not a claim edited apart from its subject, but a
measurement whose instrument was wrong while its output was shaped like an answer. Two
contradictory lists are a cheap tell; a single plausible wrong list would not have been.

STILL OPEN after this step: P9-O4's feature half, alone, and by decision rather than by omission.
24 items opened across Phases 9 and 10, 23 closed.

MEASURED VALIDATION, 21/09/2026. Unit suite 1664 -> 1665; the one added is the float-rendering
test for P9-O5. P9-O11 and P9-O12 add no tests: the first replaces an assertion that could not
fail with one that can, the second is a rename. Acceptance unchanged: test_phase8.py 96 passed,
0 failed, 3 skipped; test_phase9.py 19 passed, 0 failed, 0 skipped; test_phase10.py 35 passed,
0 failed, 1 skipped. Digests:
  c9442c76862f2f11eb470b1de4feef7fe6eaffcc2ca808bf57f1f0dc897386dd  src/analytics_agent/analysis/changepoint.py
  5eece3e4a83826c5a168c2cbe2c90b293c3b6f7677d7cc400b6ce599c1eeee79  src/analytics_agent/analysis/correlated_shift.py
  543340e6f413e18f78944603f4ba825ea1e7f44bf03dc41848ed696f048c49d2  tests/test_stats_facts.py
  b9dd0215dd6e48b25b5aa2952df2271e7f60d21d4e01d7d7fdc240622ceadae5  tests/test_declared.py

## Cleanup Step 3 - the column-paging skip, 21/09/2026

Step document: docs/steps/cleanup_step3_column_paging.md.

CLOSED. The column-paging skip, 21/09/2026, and properly this time -- the 19/09/2026 entry
below closed it in the ledger only. It was recorded closed on 19/09/2026 and kept firing on every acceptance run for two more days, because the closure was
written and the skip was not removed. tests/test_phase8.py's fixture branch is now a check
stating the real reason -- region 4, product 5, channel 3, so seven columns against a twelve-
column window -- rather than a skip implying work remains. A fixture that cannot reach a branch
is not an outstanding clause. The no-result guard beside it, also labelled "column paging",
became a failing check: a missing cross_tab result is a defect, not an outstanding clause.

C80. A CLOSURE DESCRIBED WORK THAT NOTHING PERFORMED, AND THE SKIP IT CLOSED WENT ON PRINTING.
The 19/09 entry said "Olist's customer_state has twenty-seven values, so clause 5 pages on real
data". Two things were wrong with a sentence that reads as a measurement. The clause checked that
the result was wider than the preview window and that it named its file; neither reads past the
twelfth column, so width was proven and paging was not -- the sentence was true of the data and
false of the test. And the skip the entry closed was still in the file, so the ledger and the
acceptance run disagreed on every run for two days, in opposite directions from C78: there the
index denied work the tree held, here the index claimed work the tree lacked. Both come of
writing a closure from the reasoning rather than from a command's output. The rule this project
already has would have caught it -- no claim recorded as verified without its output -- and the
entry carried no output because none was produced.

MEASURED, 21/09/2026, and this is what the 19/09 entry should have carried:

    cross_tab on Olist, payment_type by customer_state
      page 1          rows 1 to 6 of 6, columns 1 to 12 of 29
      start_col=13    rows 1 to 6 of 6, columns 13 to 24 of 29

Twenty-nine columns, not the twenty-seven the reasoning implied: customer_state's cardinality is
not the result's width, because the grid carries a row-label column and cross_tab's own columns.
A count derived from a dimension's value count is a prediction; this is the measurement, and they
differ by two. Paging does work on real data, which is the one part the closure got right.

HOW THIS WAS FOUND, because the method is the point. Asked whether everything was fixed, the
answer was not repeated from the previous turn -- the skips were counted. phase8 reported three
and phase10 one, four in all, against CLAUDE.md's "three", and the name missing from CLAUDE.md's
list was the one the ledger had already closed. A tally that disagrees with a sentence is the
cheapest defect this project has: two numbers, one command, no judgement required.

MEASURED VALIDATION, 21/09/2026. Unit suite unchanged at 1665 -- this step touches one acceptance
script. test_phase8.py 96 passed, 0 failed, 3 skipped -> 99 passed, 0 failed, 2 skipped, the
three added being the fixture-width check and the two paging reads. test_phase9.py 19/0/0 and
test_phase10.py 35/0/1, unchanged. Three skips remain in all, each permanent and recorded:
ANALYSIS_RESULT_UNSOUND, the rendered MCP schema, and the non-finite screen. Digest:
  8cb49a5da7c016fc208c8c00fa4df52a8ef92ffbbfd03e81787f446f43ba6674  tests/test_phase8.py

C81. C68 WAS REPEATED IN THE ENTRY DIRECTLY AFTER THE ONE DESCRIBING IT. The closure above was
first written as "CLOSED, PROPERLY THIS TIME. The column-paging skip" -- which reads correctly
and does not match `^CLOSED\. `, the form every other closure uses and the form C68 established
after a grep undercounted by half. It was caught in one command: the closure count printed before
and after the append, and it did not move. Nothing about the sentence looked wrong; only the
count did. That is the argument for printing a tally either side of a change rather than reading
the change -- prose hides a format error and a number cannot. The wording that made it feel like
a special case is what took it out of the format: an entry that wants to say something extra
should say it after the prefix, not instead of it.

## Phase 11, Step 1 - matplotlib ground facts, 21/09/2026

Step document: docs/steps/phase11_step1_ground_facts.md. Measured with
`uv run pytest tests/test_matplotlib_facts.py -q -s`, seven tests, all printed values below
produced by that run. Predictions were written into the step document before it ran; two were
wrong and both are recorded as such, because a prediction corrected after the fact measures
nothing.

P11-D1. MATPLOTLIB 3.11.2, NOT THE 3.10.x PREDICTED, AND SEVEN PACKAGES CAME WITH IT. `uv add
matplotlib` per guide line 943 installed matplotlib 3.11.2 and contourpy 1.4.0, cycler 0.12.1,
fonttools 4.65.0, kiwisolver 1.5.1, pillow 12.3.0 and pyparsing 3.3.3. numpy 2.5.3 was already
present as a transitive dependency of statsmodels. The step document predicted 3.10.x and "no
new top-level dependency beyond matplotlib's own", which understated a seven-package install
including an image library. Recorded because a dependency count is the kind of thing assumed
rather than read.

P11-D2. THE BACKEND IS Agg, SET BEFORE pyplot IS IMPORTED, AND get_backend() RETURNS IT
CAPITALISED. The guide names the GUI backend as the Phase 11 trap. pyplot chooses its backend at
import time, so `matplotlib.use("Agg")` after `import matplotlib.pyplot` is too late to be a
guarantee; the facts file sets it above the pyplot import and the chart layer will do the same.
Measured: `get_backend()` is `'Agg'`, with a capital A -- the prediction said 3.11 would
normalise to lowercase and it does not, so an equality test against "agg" would fail on a
correctly configured server. No GUI toolkit reaches sys.modules.

P11-D3. ALL EIGHT KINDS DRAW FROM PLAIN PYTHON LISTS, SO THE CHART LAYER OWNS NO CONVERSION.
Line, bar, grouped bar, scatter, histogram, box, heatmap and waterfall, each drawn from lists and
saved, each a real PNG. Sizes: line 23,111 bytes, bar 6,007, grouped bar 6,074, scatter 12,396,
histogram 12,090, box 5,865, heatmap 9,224, waterfall 9,168. This matters because the engine
reads every value with fetchall and no analysis materialises a column; had matplotlib needed an
array, the chart layer would have had to build one and the numpy rule would have been the first
casualty. Grouped bar and waterfall are compositions rather than artists -- two offset `bar`
calls, and one `bar` with a `bottom` list.

P11-D4. A None IS A GAP IN A LINE AND A TypeError IN A BAR, SO THE CHART LAYER SCREENS NULLS
ITSELF. Measured: `ax.plot([1,2,3,4], [1.0, None, 3.0, 4.0])` draws with a gap where the None
was; `ax.bar` on the same series raises `TypeError: unsupported operand type(s) for +: 'int' and
'NoneType'`. Every analysis here can return a None cell -- base.number() keeps None as None by
P8-D9 -- so a series reaching render_chart may hold one. The decision follows from the message
rather than from the exception: it names no column, no row and no chart, so a caller who sees it
learns nothing they can act on. render_chart screens nulls before matplotlib sees them and
refuses in this project's own words, the way every analysis reports what it drops (P10-D36).

P11-D5. CATEGORIES KEEP THE ORDER THEY ARE GIVEN. `ax.bar(["south","north","east","west"], ...)`
draws tick labels in exactly that order rather than sorted. Load-bearing: ranked_totals hands
groups back biggest first, and a chart that re-sorted them alphabetically would contradict the
table printed beside it.

P11-D6. FIGURES ACCUMULATE UNTIL CLOSED, WHICH IS THE LEAK THAT MATTERS IN A LONG-RUNNING SERVER.
Measured: `len(plt.get_fignums())` goes 0 -> 3 -> 0 across three `plt.figure()` calls and one
`plt.close("all")`. pyplot holds a reference to every figure it makes, and this server does not
exit between renders, so every render_chart closes what it opened in a finally.

P11-D7. TWO SAVES OF IDENTICAL DATA ARE BYTE-IDENTICAL, SO A CHART CAN BE ASSERTED BY DIGEST.
Measured: the same line drawn and saved twice gives two files of 21,677 bytes with equal bytes.
matplotlib writes no timestamp into the PNG by default. This is what makes a chart testable as
an artifact rather than only as a shape, and it is the prediction I would have bet least on.

MEASURED VALIDATION, 21/09/2026. tests/test_matplotlib_facts.py: 7 passed. Full suite 1665 ->
1672. Acceptance unchanged: test_phase8.py 99 passed, 0 failed, 2 skipped; test_phase9.py 19/0/0;
test_phase10.py 35/0/1. No src/ file changed in this step -- it measures and builds nothing.
Digest:
  c9cc25b93716e35c0cd90409ace493367a2919570a5f0823e762d0cc85163ab0  tests/test_matplotlib_facts.py

## Phase 11, Step 2 - the render layer, 21/09/2026

Step document: docs/steps/phase11_step2_render_layer.md. Scope agreed before building: the render
layer only. `render_chart` is wired in Step 3, where the gate and the Rule 4 envelope get their
own attention; nothing in this step is reachable from server.py, which is why all three
acceptance scripts are unchanged.

C82. THE TOOL SURFACE WAS ARGUED FOR ON A CLAIM THAT WAS ONE THIRD FALSE, AND THE CLAIM WAS
CHECKED BEFORE IT COST ANYTHING. Choosing between charting an analysis result and charting a
written CSV, the first was recommended partly because its values "stay typed" against a CSV where
base.number() has already rendered them. Measured immediately after, on a real hypothesis_test
Output: `[('a','str'), ('6','str'), ('11.5','str'), ('1.8708','str'), ('-0','str')]`. Every
analysis builds its rows with number() and label(), so an Output cell is a display string or
None and the parse back is unavoidable on either path. The two reasons that actually decided it
survive -- the gate, and Output.summary carrying Rule 4's key values -- so the choice stands and
the argument for it does not. Recorded because the failure mode is the one this file keeps
naming: a claim about a thing, written without looking at the thing. It cost nothing here only
because the look happened before the code did.

P11-D8. THE PARSE BACK LIVES IN ONE FUNCTION. `as_number` is the inverse of `base.number()` and
the only place a display string becomes a magnitude; the eight drawing branches see numbers and
nothing else. It survives what number() produces: thousands separators, four-place rounding,
trailing zeros stripped, a Decimal's own scale, None for an empty cell, and `-0` for a negative
that rounded away -- measured on a real Output, not imagined. A dimension's member is a string
that does not parse, which is also how `is_numeric_column` tells a measure column from a label
column without reaching for a contract this layer cannot see.

P11-D9. CHARTS LAND IN workspace/<id>/charts/, BESIDE results/ AND NOT INSIDE IT. Guide line 721
puts charts in the workspace next to outputs. Beside rather than inside because a PNG is not a
result file: `read_result_file` pages rows out of a CSV and can do nothing with an image, so a
chart sharing that directory would be offered to a reader who cannot open it.

P11-D10. THE CHART LAYER SCREENS NULLS AND SAYS HOW MANY IT DROPPED. P11-D4 measured `ax.bar` on
a series holding a None raising `TypeError: unsupported operand type(s) for +: 'int' and
'NoneType'` -- a message naming no column, no row and no chart. Every analysis here can return a
None cell (P8-D9), so the points are dropped before matplotlib sees them and the Chart carries
"N of M point(s) in <measure> are empty and are not drawn; the table beside this chart still
holds them." That is P10-D36's rule in a new place: an artifact that quietly holds less than its
caption claims is the failure, not the dropping.

P11-D11. A NON-FINITE VALUE IS REFUSED RATHER THAN PLOTTED. P8-D1 lets nan and inf reach a cell
as text so a reader sees them. An axis cannot show either, and a chart that silently omitted them
would be a claim about a distribution that is not the one measured. `as_number` refuses the
strings 'nan', 'inf', '-inf' and the float equivalents, naming P8-D1 in the message so a reader
knows why the value exists at all.

P11-D12. `Chart` HAS NO ACCESSOR THAT RETURNS A BARE PATH, AND A TEST ASSERTS THERE IS NONE.
Modelled on util.results.Result and for the same reason, which Rule 4 states: the accessor that
exists is the one that gets used. `to_text()` carries the path, how many of how many points were
drawn, what is on each axis, the lowest and highest value of every measure and where each falls,
the first and last, and the analysis's own summary sentences. A PNG is the one artifact in this
engine that literally cannot be read back, so the description is not a convenience.

P11-D13. THE FOUR SINGLE-MEASURE KINDS REFUSE A RESULT OFFERING MORE THAN ONE, AND NAME THE FIX.
line, bar, histogram and waterfall draw one measure. Handed a result with two, they refuse with
both names and "Name one with y" rather than picking the first, because picking would answer a
question nobody asked -- the same reasoning P8's registry uses when an unknown analysis_type
returns the valid list instead of something adjacent.

P11-D14. THE FIGURE IS CLOSED IN A `finally`, AND THE REFUSAL PATH IS THE ONE TESTED. P11-D6
measured pyplot holding a reference to every figure it makes, and this server does not exit
between renders. The happy path closing is easy; the leak that hides is a refusal raised after
the figure opens, so there is a test that provokes one and asserts `plt.get_fignums() == []`.

P11-D15. GROUPED BAR AND WATERFALL ARE COMPOSITIONS, NOT ARTISTS. P11-D3 measured both: grouped
bar is one `bar` call per measure at offset positions, waterfall is one `bar` with a running
`bottom`. Recorded because neither has a matplotlib function to look for, and a later reader
searching for one would conclude the library cannot do it.

MEASURED VALIDATION, 21/09/2026. tests/test_charts_render.py: 26 passed. Full suite 1672 -> 1698.
All eight kinds draw from a real Output shape and write a PNG whose first eight bytes are the
magic number. Two renders of the same data are byte-identical, so the determinism P11-D7 measured
is now load-bearing in a test rather than only recorded. Acceptance unchanged and expected to be:
test_phase8.py 99 passed, 0 failed, 2 skipped; test_phase9.py 19/0/0; test_phase10.py 35/0/1 --
nothing in src/ imports charts/ until Step 3. One test assertion was written wrong and caught by
its own run: it expected the lowest value of [4.0, 3.0, 2.0, 1234.56] to be 1 rather than 2, and
the corrected line spells the series out beside it. Digests:
  6bd9de77dbed7ab25baee6689c54140f16ae45b8b25b924cf9e246a4a0c569eb  src/analytics_agent/charts/render.py
  d62927aacb4d83f8080bb9a9895da80dcf874ca10435388f2087d8be4d8f25f5  tests/test_charts_render.py

## Phase 11, Step 3a - the parameters compute_analysis never passed, 21/09/2026

Step document: docs/steps/phase11_step3a_parameter_forwarding.md. Found while reading
compute_analysis to mirror its shape for render_chart, and fixed before Step 3 rather than after,
because Step 3 would otherwise have copied the pattern into a second tool.

C83. EIGHT OF TWENTY-SEVEN ANALYSES COULD NOT BE CALLED THROUGH THE TOOL AN AGENT USES, AND THE
REFUSAL BLAMED THE AGENT. Measured before any edit: compute_analysis declared 20 parameters,
forwarded 14, and some registered analysis wanted 23. Six were never declared, so FastMCP's
schema did not contain them and no caller could pass one -- alpha and power (sample_adequacy),
confidence (confidence_interval), entity (cohort_retention, repeat_behaviour, REQUIRED by both),
method (hypothesis_test), second_dimension (effect_size, hypothesis_test). Three more were
declared and dropped on the way through -- against (bivariate, correlated_shift, correlation),
baseline and period (growth_decomposition, mix_shift, period_compare, and period for
cohort_retention). Eight analyses were therefore uncallable, each missing a required argument:
bivariate, correlated_shift, correlation, growth_decomposition, mix_shift, period_compare,
repeat_behaviour, cohort_retention. Four more could not be fully used.

The failure surfaced as a lie about the caller. Proved rather than reasoned: correlation's
signature is `(con, gate, scope, measure, against, **params)`, calling it without `against`
raises `TypeError: correlation() missing 1 required positional argument: 'against'`, and
tools.py's `except (TypeError, ParamsInvalid)` turns that into ANALYSIS_PARAMS_INVALID --
"correlation was called with arguments it cannot take." The agent passed the argument; the
server dropped it; the refusal named the agent. An agent that believes that refusal stops
asking, which is worse than a traceback, because a traceback is obviously a defect and a
refusal reads as an answer.

The docstring was ahead of the signature the whole time. Lines 818 to 848 document
second_dimension, method, confidence, alpha, power and entity, every one of which the signature
did not declare -- so the tool description instructed the agent to pass fields the schema did
not contain. C72 recorded the opposite direction, analyses missing from the docstring; this is
the docstring correct and the schema behind it.

P11-D16. THE PARAMETER ROSTER IS READ FROM THE REGISTRY, NOT TYPED OUT.
test_analysis_tool_docs.py had `test_every_parameter_any_analysis_takes_is_declared`, which
compared a hand-written set of fifteen names with `<=`. A subset assertion against a stale
hand-typed roster cannot fail for the thing it exists to catch, and it passed for two phases
while six names were missing. It now derives the union from `REGISTRY` by `inspect.signature`,
and a second test asserts the other half nobody had written: every declared parameter is also
forwarded. Declaring and forwarding are two edits and they were made apart -- the same shape as
every C entry in this file. This is the third place the hand-typed-roster pattern has been
removed, after P10-D39 (the tier test) and C72 (the docstring roster).

P11-O1 IS OPEN. No acceptance script calls a Tier 3 to 7 analysis through the registered MCP
tool. P8-D76 records tests/test_phase8.py calling the registered tool and proving its arguments
reach the right names, but only for Phase 8's nine, which take none of the nine parameters C83
names. That is why three green acceptance runs and 1,698 unit tests said nothing while eight
analyses were unreachable: every one of them was exercised through the registry or the tools
layer directly, and the only path a real client takes is the one nothing walks. The unit guard
added here catches the defect class structurally; an acceptance clause that actually calls
period_compare or correlation through server.compute_analysis on Olist would catch it
behaviourally, and those are not the same thing.

MEASURED VALIDATION, 21/09/2026. The two guard tests were written before the fix and failed as
predicted, naming exactly six undeclared and three unforwarded parameters with the analyses that
want each. After the fix: tests/test_analysis_tool_docs.py 8 passed. Full suite 1698 -> 1699, the
one added being the forwarding half that had never existed. Acceptance unchanged and expected to
be -- test_phase8.py 99/0/2, test_phase9.py 19/0/0, test_phase10.py 35/0/1 -- because none of
them calls this tool, which is P11-O1. Digests:
  9f06a65dcd97af5ebc5587b551e0cb83419bf045a4a208ca11155fdce9ecf381  src/analytics_agent/server.py
  668b284220e0181092feb20953d705e70182ae3289697cc4102d6b203b9d62f2  tests/test_analysis_tool_docs.py

## Phase 11, Step 3 - render_chart, 21/09/2026

Step document: docs/steps/phase11_step3_render_chart.md.

C84. THIS STEP'S DOCUMENT WAS WRITTEN AFTER THE STEP. Steps 1, 2 and 3a each had their plan and
their predictions written before anything ran, and each recorded a prediction that turned out
wrong -- the matplotlib version, the backend's capitalisation, the claim that an Output holds
floats, the lowest value in a four-element list. Step 3 went from the design decision straight
to building, and its document was assembled afterwards from the commands that had already run.
Nothing in it is false and that is not the point: a document written afterwards cannot hold a
prediction, and the predictions are where this method earns its cost. Recorded so the deviation
is visible as a deviation rather than absorbed into a tidy-looking record, which is exactly what
C61 through C76 are about.

P11-D17. THE LADDER EVERY ANALYSIS CALL CLIMBS IS EXTRACTED, NOT COPIED. compute_analysis and
render_chart share every step up to the Output: the contract gate, the registry lookup, the
scope, the run, and the check that the result's first summary line is the method note. Each step
has its own refusal text, so a second copy would be a second copy of six refusals. `_produce`
holds them once and raises `_Refused` carrying what it would have returned; both tools catch it
and return the text. P9-O6 records what two copies of one ruling do, and this is the same ruling
six times over.

P11-D18. A CHART GOES THROUGH THE GATE A TABLE GOES THROUGH, IN THE SAME WORDS. A chart is a
claim about data, so a dataset with no confirmed contract is refused at render_chart exactly as
at compute_analysis -- same reason code, same next_call. Tested rather than asserted in prose:
render_chart on an ungated dataset returns NO_CONTRACT and names propose_dataset_contract.

P11-D19. A CHART REFUSAL SAYS THE ANALYSIS WAS FINE. ChartRefused becomes ANALYSIS_NOT_POSSIBLE,
and the detail line says "The numbers are not in question -- the analysis ran. This is about the
shape a chart needs, which is not the shape this result has. Nothing was written." The next_call
is compute_analysis for the same analysis, so a caller who wanted the answer still gets it. An
agent told only "not possible" would doubt the data, which is the wrong lesson from a refusal
about geometry.

P11-D20. matplotlib IS IMPORTED INSIDE render_chart, NOT AT MODULE SCOPE. Twenty-two analysis
modules and their tests import analytics_agent.analysis; none of them draws. A top-level import
in tools.py would pull matplotlib, and through it numpy, into every one of those imports. The
no-numpy rule is about what this engine's code imports, and the cheapest way to keep the tier
honest is for the drawing dependency to load only when something draws.

P11-D21. frequency OFFERS ONE MEASURE, BECAUSE share IS A PERCENTAGE. Measured while writing the
chart tests, having assumed otherwise and watched two of them fail. frequency's columns are
value, rows and share; share renders as a percentage string, which is not a magnitude, so
is_numeric_column rejects it and only rows is plottable. A grouped bar of frequency is refused
rather than drawn, and that is right -- two of its three columns are the same count in different
clothes, and drawing them side by side would be one number twice. summary_stats is the
multi-measure fixture instead, and the assumption is pinned in a test of its own so the next
reader does not make it again.

P11-D22. THE CLOSED TOOL ROSTER FIRED ON THE NEW TOOL, AS DESIGNED.
test_tool_docs.py's `test_the_registered_tools_are_exactly_the_expected_ones` failed when
render_chart appeared, and its own docstring says why that is the behaviour working: "Adding a
tool is therefore two edits: the tool, and this set. That is the intended friction." Recorded
beside C83, which is what happens when a roster is NOT closed: there the hand-typed parameter set
used `<=` and could not fail, and six names went missing for two phases. Same file, two rosters,
opposite outcomes, and the difference is the operator.

MEASURED VALIDATION, 21/09/2026. Full suite 1699 -> 1712; thirteen added, ten on render_chart's
behaviour and three guarding its parameter roster and its docstring. The roster guards are the
Step 3a pair applied to the second tool, written in the step that added it rather than two phases
later. Acceptance unchanged -- test_phase8.py 99 passed, 0 failed, 2 skipped; test_phase9.py
19/0/0; test_phase10.py 35/0/1 -- because no acceptance script calls render_chart, which is
P11-O1 and remains open. Digests:
  c28f458cebc1fbed8559384481df204ff583e9f8975e7718763017b790db0874  src/analytics_agent/server.py
  047cd5b50ca29ebd7076c8856705729a5ba655620ab25890dd1fa2a09e0e304a  src/analytics_agent/analysis/tools.py
  5060ce7a1547d791bc85d368675387c6b17734d028f5ba5fcbcfe7b18e8a4b05  tests/test_analysis_tools.py
  4842da5c05b6bc449abe723dde8aa564d64feb2b005238f0988935fe1fc4cb87  tests/test_analysis_tool_docs.py
  621d19b653921144cf1d4c304f0b03061fef3cd7887491732fb94d51755aab71  tests/test_tool_docs.py

## Phase 11, Step 4 - the acceptance script, 21/09/2026

Step document: docs/steps/phase11_step4_acceptance.md, written before the run with ten numbered
predictions. Two were wrong and both are recorded below as wrong.

CLOSED. P11-O1, 21/09/2026. tests/test_phase11.py calls server.compute_analysis for all nine
parameters C83 named -- against, period, baseline, entity, second_dimension, method, confidence,
alpha and power -- each on an analysis that requires it, and server.render_chart for all eight
chart kinds. Before c1826b2 every row of that table returned ANALYSIS_PARAMS_INVALID. It runs on
the clean_sales CSV fixture rather than Olist, so unlike test_phase9.py and test_phase10.py it
needs no Postgres and is portable. 26 passed, 0 failed, 0 skipped.

C85. A REFUSAL PRINTED TWO IDENTICAL NUMBERS AND CALLED THEM UNEQUAL, AND IT MEANT
growth_decomposition COULD NOT RUN ON A FLOAT MEASURE. The new acceptance clause failed on its
first run -- prediction 4, which said it would pass. Not with the parameter error the clause was
built to catch, but with ANALYSIS_RESULT_UNSOUND, and underneath it a LostRows reading: "the 5
member(s) of region contribute -1,539.88 against a change of -1,539.88 ... Parts that do not add
to the whole are not a decomposition of it." The two numbers are the same on the page. The check
was `sum(contributions.values(), zero) != change`, exact equality, with both sides rendered
through number(), which rounds to four places. Exact equality is right for a DECIMAL or integer
measure and wrong for every DOUBLE one: measured, sum(revenue) over the 500-row fixture is
1377896.8399999999. So growth_decomposition refused every float measure, and said so in a
sentence that refuted itself.

Nothing caught it because tests/test_growth_decomposition.py's fixture writes its amounts as
`20.00`, which DuckDB reads as DECIMAL. The analysis was exercised only on exact arithmetic for
two phases. Olist's payment_value is DECIMAL too, which is why Phase 9 and Phase 10 acceptance
never saw it either.

P11-D23. THE RECONCILIATION TOLERANCE LIVES IN base.py AND BOTH DECOMPOSITIONS READ IT.
mix_shift already compared a residual against `TOLERANCE * max(1.0, abs(change))` with
TOLERANCE = 1e-9 local to that module, and printed the residual in scientific notation so a
reader could see the gap. growth_decomposition compared exactly. One ruling, two
implementations, and only one of them right -- P9-O6's shape, found a third time. base.py now
owns RECONCILE_TOLERANCE, mix_shift reads it, and growth_decomposition compares a residual and
names it. A test asserts `mix_shift.TOLERANCE is RECONCILE_TOLERANCE`, so a second copy fails
rather than drifts.

P11-D24. THE ACCEPTANCE RUNS ON THE CSV FIXTURE, NOT OLIST. clean_sales declares three measures
with three different aggregates and three dimensions, which reaches every tier, and it loads
from disk. test_phase9.py and test_phase10.py both skip wholesale when Postgres is absent; this
one does not, so the surface C83 broke is checked on any machine that can run the suite. The
fixture being DOUBLE where Olist is DECIMAL is not a compromise -- it is why C85 was found.

P11-D25. THE FORWARDING CLAUSE NAMES THE PARAMETER, NOT THE ANALYSIS. Each row reads "against
reach correlation", "power and alpha reach sample_adequacy". A failure therefore says which
argument did not arrive rather than which analysis broke, which is the distinction C83 turned on:
the analysis was fine and the wrapper dropped the argument.

P11-D26. TWO PREDICTIONS WERE WRONG AND THE CHEAP ONE WAS THE HEDGE. Prediction 4 said
growth_decomposition would pass; it failed, and that failure is C85. Prediction 9 hedged that at
least one of the eight chart kinds would be wrong; all eight rendered. The hedge cost nothing and
found nothing, and the specific prediction found a bug that had survived two phases -- which is
the argument for predicting a value rather than a range.

MEASURED VALIDATION, 21/09/2026. Full suite 1712 -> 1714; the two added pin a DOUBLE measure
reconciling and the tolerance being shared. Acceptance is now four scripts, not three:
test_phase8.py 99 passed, 0 failed, 2 skipped; test_phase9.py 19/0/0; test_phase10.py 35/0/1;
test_phase11.py 26 passed, 0 failed, 0 skipped. Digests:
  6de4309a64ac331cb6b6d65c7569d59aab5afcfc80049ab5c9e099807b38fe61  src/analytics_agent/analysis/base.py
  36f3728645300ae10f84e38a2189ae923e0aee9f8f7d5efa9069f60c8c75c118  src/analytics_agent/analysis/mix_shift.py
  d451ac622453f0922e1fed37b232a20a0f039486ca6cdc4e2a52dc526fd47c32  src/analytics_agent/analysis/growth_decomposition.py
  17ef7bb62a6e5a15e87293fd36f1506ada3b65382414b28a04f100a14b8926f2  tests/test_growth_decomposition.py
  03daf6a771409ca8093720ea12d267de024d0aa649f4f30de8722303a1738481  tests/test_phase11.py

## Phase 12, Step 1 - what each mandatory section can be built from, 21/09/2026

Step document: docs/steps/phase12_step1_sources.md, written before the run with eight
predictions. All eight held, which has not happened before in this build and is itself worth
noting: the questions were about what the repository contains rather than what a library does,
and this repository is legible in a way scipy is not.

P12-D1. FIVE OF THE NINE SECTIONS ARE A FORMATTING JOB. The cleaning ledger, validation results,
the data quality summary, dataset and grain, and caveats and exclusions all read from records
that already exist and are already queryable per dataset: clean/ledger.py's LedgerEntry (which
carries the SQL statement it ran, plus plan and action ids and before/after counts, and a line()
that renders one), validate/runs.py's ValidationRun with latest and history, profile/runs.py's
ProfileRun with latest, history and all_latest, and contract/store.py's StoredContract with
current, history, history_text and summarise. Phase 12 assembles these rather than computing
anything.

P12-D2. THE QUESTION ASKED IS STORED NOWHERE AND MUST BE AN ARGUMENT. Nothing in the workspace
records why a dataset was loaded. build_report takes it from the caller, which is right -- the
question belongs to the person, not to the data -- and it is the one section with no record
behind it.

P12-D3. A WRITTEN RESULT KEEPS ITS TABLE AND LOSES EVERYTHING ELSE. Measured: write_result opens
the file, writes the header row and the data rows, and returns. The `summary` it is handed goes
into the returned Result object and not onto disk, and no parameters are stored at all. So a
result file on disk is a table and a filename: top_n_20260921-124920.csv says an analysis called
top_n ran at a time, and does not say it was called with dimension="region", measure="revenue"
and n=3, nor that 500 of 500 rows were analysed. The method note, which every analysis is
required to lead with and which tools.py refuses a result for lacking, does not survive the call
that produced it.

P12-D4. THE ANALYSIS TIER IS THE ONE TIER THAT RECORDS NOTHING. `ensure_table` appears in five
modules -- validate/runs, contract/store, clean/plan, clean/ledger, profile/runs -- each keeping
its own runs in the workspace catalog, each with latest and history per dataset. Analyses and
charts keep nothing. The convention is established five times over and the newest tier declines
it, which is why the report cannot be assembled as specified rather than why some feature is
missing.

P12-O1 IS OPEN, and it is Phase 12's real work. "A reproduction appendix listing exact tool
calls" cannot be written from what exists. The three candidate answers are not equal. Taking the
calls as an argument to build_report means the appendix records what the agent says it ran,
which is the failure this whole codebase is arranged against -- a claim and the thing it
describes, written separately, and the reproduction section is precisely where that must not
happen. Reconstructing approximately from filenames and saying so produces an appendix that
cannot be replayed, which is not an appendix. Recording analysis and chart runs the way the
other five tiers already record theirs is the answer that fits: a run row carrying dataset,
analysis_type, the parameters as given, the result path, the chart path, the summary lines and a
timestamp. It also closes the "findings with charts" section, which otherwise cannot say which
chart belongs to which finding, because nothing links a PNG to the analysis that produced it.

MEASURED VALIDATION, 21/09/2026. This step builds nothing and changes no file under src/ or
tests/, so every figure is the baseline restated after the fact: full suite 1714 passed;
test_phase8.py 99 passed, 0 failed, 2 skipped; test_phase9.py 19/0/0; test_phase10.py 35/0/1;
test_phase11.py 26 passed, 0 failed, 0 skipped. Measured before the step and again before the
commit.

## Phase 12, Step 2 - the run record, 21/09/2026

Step document: docs/steps/phase12_step2_run_record.md, written before the run with six
predictions. Five held; the sixth is P12-D10.

CLOSED. P12-O1, 21/09/2026. src/analytics_agent/analysis/runs.py records what each analysis and
each chart was called with, so the reproduction appendix can render an invocation rather than
infer one from a filename. Measured end to end before any test was written:
`compute_analysis(dataset_name="clean_sales", analysis_type="top_n", dimension="region",
measure="revenue", n=3)` and `render_chart(dataset_name="clean_sales",
analysis_type="frequency", chart="line", column="region", y="rows")`, each beside its artifact
and its method note.

P12-D5. THE SIXTH MODULE THAT KEEPS ITS OWN RUNS, AND IT LOOKS LIKE THE OTHER FIVE. ensure_table,
record, latest, history, appended and never updated, in `_agent_analysis_runs` -- the
BOOKKEEPING_PREFIX that state.py:197 filters out of the dataset list, imported from
profile/runs.py the way validate/runs, clean/plan, clean/ledger and clean/apply all import it.
Deliberately unoriginal. A sixth spelling of a convention five modules share would be the thing
this ledger keeps recording.

P12-D6. ONE TABLE FOR ANALYSES AND CHARTS, WITH THE CHART COLUMNS NULLABLE. A chart run is an
analysis run that also drew something. Two tables would need a join nobody would maintain, and
the single row is what links a PNG to the analysis that produced it -- which the report's
"findings with charts" section needs as much as the appendix needs the parameters. Nothing else
in the workspace connects the two: a chart's filename carries its analysis label and a timestamp,
and two charts of the same analysis are indistinguishable by it.

P12-D7. THE PARAMETERS ARE STORED, NOT THE RENDERED CALL. `call()` builds the line at read time
from a dict, sorted by key, so two runs of one analysis with the arguments given in different
orders produce the same appendix line -- a test asserts that, because a reader comparing two
reports should not see a difference that is not one. Storing the rendered string instead would
freeze today's spelling of a call into a permanent record.

P12-D8. RECORDING HAPPENS AFTER SUCCESS, SO A REFUSED CALL RECORDS NOTHING. The appendix lists
what ran, not what was attempted: a refusal is a sentence the caller already has, and it is not
a step in reproducing the work. Tested on all three refusal shapes -- unknown analysis, invalid
parameters, no contract -- and the count stays at zero.

P12-D9. x, y AND title ARE STORED BESIDE THE ANALYSIS PARAMETERS. They are chart arguments
rather than analysis arguments, and they belong in the record for the same reason the others do:
a chart drawn with y="rows" is not the same chart without it, and an appendix line that omits it
reproduces a different image or a refusal.

P12-D10. NOTHING ASSERTS WHAT A WORKSPACE CONTAINS AFTER AN ANALYSIS. The step document
predicted at least one existing test would notice a new table being written on every analysis
call. None did: the suite stayed at 1714 across the whole wiring and moved only when the new
tests arrived. The prediction was wrong and the reason is worth keeping -- a new bookkeeping
table, written by every analysis in the engine, is invisible to 1,714 tests and four acceptance
scripts. That is fine here and it is not nothing: the same silence would greet a table written
by mistake.

MEASURED VALIDATION, 21/09/2026. Full suite 1714 -> 1732; fifteen unit tests on the record and
the call renderer, three on the tools recording through it. One of those three failed first and
the failure was the test's: it named a column the fixture does not have, so the call was refused
and nothing was recorded, which is P12-D8 working. Acceptance unchanged: test_phase8.py 99
passed, 0 failed, 2 skipped; test_phase9.py 19/0/0; test_phase10.py 35/0/1; test_phase11.py
26/0/0. Digests:
  815ec11b216453089f79e97ea5f54a6eb4d083cd025ebd699302fab6441f9920  src/analytics_agent/analysis/runs.py
  872c2bf5ceb09dbc1863cf318dc635913347d8c2da8f663a09d15d9768f3fbcc  src/analytics_agent/analysis/tools.py
  e3b4846b6195364c90403cbaec8a27d2acc4e550dc222bc56d86f688c63a5cd3  tests/test_analysis_runs.py
  720d9ad70d88f46a7b033e127c1a79b498664fea61ae66407a3e0f78cc2b5840  tests/test_analysis_tools.py

## Phase 12, Step 3 - assembling the report, 21/09/2026

Step document: docs/steps/phase12_step3_assemble.md, written before the run with six
predictions. All six held.

P12-D11. A SECTION WITH NO RECORD STILL APPEARS, AND SAYS WHY. A report that drops "cleaning
ledger" because nothing was cleaned reads as a report of a dataset that needed no cleaning, and
those are different claims. clean/ledger.describe() already worked this way -- "Nothing has been
cleaned. Every table is as it was" -- and all nine sections follow it. Measured on a workspace
that had loaded, contracted, analysed and charted and done nothing else: nine headings written,
four of them reporting nothing.

P12-D12. WHICH SECTIONS WERE EMPTY IS CARRIED ON THE Report, NOT LEFT TO BE COUNTED. `to_text()`
prints them under "Sections present with nothing to report, which is a finding of its own",
because the caller cannot read the file either and a reader who has to count headings to notice
an absence will not notice it.

P12-D13. THE REPORT COMPUTES NOTHING. Every number in it was produced by a tool that recorded it
at the time -- profile runs, the cleaning ledger, validation runs, the stored contract, analysis
runs. A report that recalculated its own figures could disagree with the result files it cites
and a reader would have no way to tell which was wrong.

P12-D14. THE METHOD NOTES SECTION DEDUPLICATES. Ten runs of one analysis over one scope produce
ten identical method notes, and a section listing all ten says nothing the first one did not. A
test pins it, because the obvious implementation lists them all.

P12-D15. A Report HAS NO ACCESSOR RETURNING A BARE PATH, WHICH IS NOW THREE. `Result` (locked
decision 20), `Chart` (P11-D12), and this. The same sentence appears in all three docstrings on
purpose: the accessor that exists is the one that gets used, and Rule 4 is what that protects.

MEASURED VALIDATION, 21/09/2026. tests/test_report_assemble.py: 16 passed. Full suite 1732 ->
1748. The first write of assemble.py measured 107 characters wide against the repository's 105;
three lines wrapped, now 97. Acceptance unchanged -- test_phase8.py 99 passed, 0 failed, 2
skipped; test_phase9.py 19/0/0; test_phase10.py 35/0/1; test_phase11.py 26/0/0 -- because
nothing in src/ imports report/ until Step 4 registers build_report. Digests:
  8d3df2aee0ca8e9d2d260a58be171619c20cb0ea42c9bce41e83c102bace07ce  src/analytics_agent/report/assemble.py
  b7cd32afbb49eb72af2611791b9f6e03d169e88b94ce576ced21af8c39d53054  tests/test_report_assemble.py

## Phase 12, Step 4 - build_report, 21/09/2026

Step document: docs/steps/phase12_step4_build_report.md, written before the run with six
predictions. All six held.

P12-D16. A DATASET WITH NO CONTRACT IS REPORTED, NOT REFUSED, AND THIS DIVERGES FROM
validate_dataset DELIBERATELY. validate/tools.py refuses that case and its reason is good: a
validation report with nothing to test against "would be a page of NOT RUN". A report is the
opposite case. P12-D11 already decided every section appears and says why it is empty, and a
report of a dataset whose grain nobody agreed is still a report -- it says the grain was never
agreed, which is the most important thing a reader could be told about the numbers in it.
Refusing would withhold precisely that. build_report refuses one thing only: a dataset that is
not loaded, because with no table there is nothing for the contract, the profile, the ledger,
the validation runs or any analysis to refer to.

P12-D17. THE QUESTION IS THE USER'S WORDS AND THE DOCSTRING SAYS SO TWICE. "question is what the
user actually asked, in their words ... Do not invent one, and do not paraphrase the user into
something tidier than they said." P12-D2 makes this the one section with no record behind it,
which means it is the one section an agent can quietly author. The instruction is in the tool
description because that is what the model reads, and a test asserts both sentences survive an
edit.

P12-D18. THE DOCSTRING SAYS IT COMPUTES NOTHING. An agent that thinks a report is expensive
defers it, or re-runs the analyses first to be safe -- and re-running them would add duplicate
rows to the run log and a second copy of every finding. Saying "it computes nothing -- every
number in it was recorded by the tool that produced it" is cheaper than any guard against that.

P12-D19. NO FORWARDING GUARD WAS ADDED, AND THAT IS NOT AN OVERSIGHT. C83 was a roster of
twenty-plus parameters declared in one place and passed in another, and the guard that caught it
derives the roster from the registry. build_report takes three arguments. A guard for a roster
that does not exist would be ceremony, and a suite full of ceremony is one nobody reads closely
enough to notice the guard that matters.

THE CLOSED TOOL ROSTER FIRED AGAIN, ON SCHEDULE. test_tool_docs.py's
test_the_registered_tools_are_exactly_the_expected_ones failed on build_report before it was
declared, as it did on render_chart in Phase 11 Step 3. Recorded a second time because the
contrast with C83 is the useful part: the same file holds a closed roster that cannot miss a
tool and, until C83, an open one that could not catch a missing parameter. The difference was
`==` against `<=`.

MEASURED VALIDATION, 21/09/2026. tests/test_report_tools.py: 7 passed, plus 4 docstring guards
in test_tool_docs.py. Full suite 1748 -> 1759. Acceptance unchanged -- test_phase8.py 99 passed,
0 failed, 2 skipped; test_phase9.py 19/0/0; test_phase10.py 35/0/1; test_phase11.py 26/0/0 --
because nothing calls build_report from a script until Step 5, which is the guide's Done-When.
Digests:
  de0179097b453d317a12ed6e7535009d2160daeefe7f39c964d1eaff84cd8030  src/analytics_agent/report/tools.py
  a18a14eaa806d974eaca2f88b65d7eb5f3a899223ecb3f00f6f8131bb3d8a699  src/analytics_agent/server.py
  74a112986188b67ab363c0337943888162f2944f3c544d83c1895ac6a65c269b  tests/test_report_tools.py
  d5f2adf4555cb2634b5f2b27a9426ed53e51eb0dac08513179f434a69ecf6412  tests/test_tool_docs.py

## Phase 12, Step 5 - the Done-When, 21/09/2026

Step document: docs/steps/phase12_step5_done_when.md, written before the run with eight
predictions. Seven held. The eighth is P12-D23.

P12-D20. THE DONE-WHEN PASSES: 36 passed, 0 failed, 0 skipped. tests/test_phase12.py runs the
whole pipeline on merged_multiheader.xlsx in one process -- the ingest spec across a two-row
merged header, 150 rows loaded, a profile, a cleaning plan the data actually needed, a contract
somebody agreed, validation against it, seven analyses, a chart, and the report. The document is
8,748 bytes with all nine sections present in the guide's order and none of them empty.

P12-D21. THE CLEANING STEP IS NOT DECORATION, AND THE DATA CHOSE IT. order_date arrives from the
spreadsheet as VARCHAR, which is what a date in a spreadsheet is. propose_cleaning_plan offered
exactly one action -- "C001 CONVERT_TYPE on order_date: read order_date as DATE (150 row(s))" --
and without it the contract cannot be confirmed at all: the validator refuses with "date_column
'order_date' is VARCHAR, not a date. A date held as text sorts lexically and cannot carry an
analysis window." So the pipeline's order is forced by the data rather than chosen for the
script: clean before contract, or there is no contract.

P12-D22. THE ACCEPTANCE GOES THROUGH server.py FOR EVERYTHING BELOW THE LOAD. C83 is the reason:
eight analyses were uncallable through the MCP surface while every test passed, because every
test reached the analysis through the registry or the tools layer. A Done-When that did the same
would prove the pipeline works for callers who do not exist. growth_decomposition is in the
analysis list on purpose -- revenue is DOUBLE, and until C85 that analysis refused every float
measure.

P12-D23. THE PREDICTION THAT SOMETHING WOULD BREAK WAS WRONG, AND IT IS THE FIRST TIME IN THIS
BUILD THAT A WHOLE-SYSTEM STEP FOUND NOTHING. The step document said: "Something will need
adjusting. Nine phases have never run in sequence in one process. I do not know what, which is
why this prediction is worth writing down rather than leaving as a feeling." Nothing needed
adjusting. Every earlier integration step found something -- C83 in Phase 11 Step 3, C85 in
Phase 11 Step 4, P12-O1 in Phase 12 Step 1 -- so this is a fact about the codebase rather than
about the prediction being lazy: the parts had already been made to fit one at a time. Recorded
because a wrong pessimistic prediction is as much a measurement as a wrong optimistic one, and
the project has not had one of these before.

THE ONLY CHANGE AFTER THE FIRST RUN WAS TO A CHECK OF MY OWN THAT COULD NOT FAIL. "No section
had nothing to report" first looked for section names inside a slice of the reply taken after
the words "nothing to report", so a change to that wording would have made it pass without
testing anything. It now asserts directly that the phrase to_text() prints is absent. P9-O11 and
C83 were each a check that could not fail; writing a third in the step that closes the phase
would have been careless.

MEASURED VALIDATION, 21/09/2026. Acceptance is now five scripts: test_phase8.py 99 passed, 0
failed, 2 skipped; test_phase9.py 19/0/0; test_phase10.py 35/0/1; test_phase11.py 26/0/0;
test_phase12.py 36 passed, 0 failed, 0 skipped. Full suite 1759, unchanged -- test_phase12.py is
a script and pytest collects nothing from it, as with the other four. Digest:
  71694c84ab3fc6d8b4f0eab4d7a9c6bd1ba4b2457314289e2ecff853eb00c2d9  tests/test_phase12.py

C86. THE ACCEPTANCE SCRIPT LEFT A FILE IN THE REPOSITORY, AND THE FIRST COMMIT OF THIS STEP
CONTAINED IT. confirm_dataset_contract exports a YAML copy of the contract to docs/contracts/,
which is outside the workspace and is meant to be version controlled -- the tool calls it "the
copy for version control", and clean_sales.yaml has been tracked since Phase 7. That is right
for real work and wrong for a test. workspace.reset() cleans the workspace and the export is not
in it, so every run of tests/test_phase12.py left docs/contracts/merged_multiheader.yaml
modified by a timestamp. `git add -A` swept it into 0a11796 before it had been looked at.

Two things follow. The file is removed from the repository, because it is the output of a test
rather than a record of work anybody did. And the script restores what it found -- deleting the
export if there was none, rewriting the bytes if there was -- in the same `finally` that resets
its workspace. The MCP tool takes no export root and should not: a client has no business
choosing where the repository's copy goes.

The reason this is worth an entry rather than a quiet fix is what it would have cost. The rule
here is to run all six checks before committing; with this in place, running them leaves the
tree dirty, so every commit after every acceptance run would carry a one-line timestamp change
nobody intended. A discipline that reliably produces noise is one people stop reading, and the
whole value of "read all six before committing" is that somebody reads them.

MEASURED, 21/09/2026: after the fix, `uv run python tests/test_phase12.py` then
`git status --short` prints nothing. 36 passed, 0 failed, 0 skipped, unchanged.

## Phase 13, Step 1 - the eval harness, 21/09/2026

Step document: docs/steps/phase13_step1_harness.md, written before the run with five
predictions. All five held. SCORE: 27/28 (96%) -- correctness 5/5, behavioural 18/19,
regression 4/4.

P13-D1. THE EVAL REPORTS A SCORE AND EXITS ZERO ON A WRONG ANSWER. It exits non-zero only when
the harness itself could not run. An eval that fails the build on any wrong answer is a test
suite, and a test suite cannot carry a score -- the number stops being a measurement the moment
it has to be 100%. The guide's own words for this phase are "it turns 'I built an AI thing' into
'I measured whether it was right, and here is the number'", and a number that can only ever be
one number is not one. The six existing checks stay pass/fail; the eval is the seventh thing to
run and the first that answers with a figure.

P13-D2. A GOLD ANSWER IS COMPUTED WITHOUT THE TOOL UNDER TEST. Every correctness question
carries SQL run against the loaded table, and the reply must contain what that SQL returned. An
answer produced by compute_analysis would agree with compute_analysis forever, including when
both are wrong. C02 is why this matters in practice: it asserted `count(DISTINCT region)` = 4
and the tool returned 5, and the tool was right -- DISTINCT excludes NULL and P8-D5 keeps NULL
as its own group. The question was the answer to something else.

P13-D3. BEHAVIOURAL IS MEASURED WITHOUT AN AGENT, BY EXECUTING THE REFUSAL'S OWN NEXT STEP.
"Does the agent recover from a gate refusal in one retry" asks about a model, and running one
and grading it measures one model on one day. Every refusal here carries a NEXT STEP, and
`Refusal.__post_init__` already rejects one without parentheses because "an instruction the
agent cannot execute is how the apology loop starts" -- but nothing executed it. A refusal
recovers in one retry if the call it names, made verbatim, succeeds. B02 and B03 do: both name
`compute_analysis(dataset_name="clean_sales", analysis_type="summary_stats")` and both come back
with a result. That tests the property rather than a sample.

P13-D4. THE RETRY PARSES WITH ast AND DISPATCHES THROUGH AN ALLOWLIST, NEVER eval. A harness
that evaluated whatever string a refusal happened to contain would be a worse defect than any it
could find. A NEXT STEP is usable when it parses as exactly one call to a registered tool with
literal arguments and nothing after it.

P13-O1 IS OPEN. Sixteen of thirty-seven refusals name a call an agent can make verbatim. The
other twenty-one carry prose after the call (`list_datasets() to see what is already here`), a
second call (`propose_ingest_spec(path="...") then confirm_ingest_spec`), or a placeholder the
caller must fill (`primary_key=[...]`, `grain=...`). The three are not equally wrong. A
placeholder is correct -- the caller has to decide, and Refusal's own docstring uses
`confirm_dataset_contract(contract_json=...)` as its example of a good next_call. Prose glued to
a call is not: `Refusal` already has a `detail` field, and that is where the guidance belongs.
F1's entire mitigation is instructional refusals, and an instruction an agent has to parse
before following is weaker than one it can follow. B04 is the gold question that catches one.
The fix is mechanical and touches about a dozen sites; it is Step 2's work rather than a
one-line patch to whichever site the eval happened to test, which would be gaming the
measurement.

P13-O2 IS OPEN, and it is C86 repeating. confirm_dataset_contract exports a YAML copy to
docs/contracts/, outside the workspace. C86 taught tests/test_phase12.py to restore what it
found; eval/run_eval.py confirms a contract too and dirtied docs/contracts/clean_sales.yaml on
its first run, because the fix was made to one script rather than to the pattern. It now
restores as well. Two scripts doing the same bookkeeping by hand is the shape P9-O6 records, and
the answer is a shared helper -- or an export root the test path can set, which the MCP tool
still must not expose.

TWO MEASUREMENTS OF THE SAME THING DISAGREED, AND THAT IS HOW THE ROSTER'S BUG WAS FOUND. The
roster first reported 0 of 37 refusals naming a usable call. It rendered f-strings by
substituting `"x"` into literal parts that already carried quotes, producing `dataset_name=""x""`
-- a syntax error every time. Nothing about "0 of 37" looked impossible; a probe run minutes
earlier had said 22, and the disagreement is what caught it. The two surviving numbers are both
right and answer different questions: 22 of 37 NEXT STEPs *look* like a call under a regex, and
16 of 37 *are* one this process can make. `propose_dataset_contract(dataset_name="x",
primary_key=[...])` is in the gap.

MEASURED VALIDATION, 21/09/2026. `uv run python eval/run_eval.py`: 27 passed, 1 failed, 0
skipped, SCORE 27/28 (96%). The one failure is B04 and is P13-O1. Full suite 1759 and the five
acceptance scripts unchanged -- 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0 -- because nothing under
src/ changed in this step. Digests:
  ec4e0cc15c60b808cefa4593b9820ae7a6bbe3209bbeed96f5cdd8af6f656fe2  eval/run_eval.py
  3aa8ed4a233aa171aa6b350f7518f14f2e729f1444d727926a17c0bd2b99d5eb  eval/gold_questions.yaml

## Phase 13, Step 2 - closing what the harness found, 21/09/2026

Step document: docs/steps/phase13_step2_refusals.md, written before the run with four
predictions. Two held, one held exactly, one was wrong. SCORE: 31/31 (100%), from 27/28.

CLOSED. P13-O1, 21/09/2026. Twenty-six of thirty-seven refusals now name a call an agent can
make verbatim, from sixteen. Ten sites had prose glued to a complete call -- "list_datasets() to
see what is already here", "propose_dataset_contract(dataset_name="x") and confirm it" -- and
the sentence moved into `detail`, which renders as its own DETAIL line above NEXT STEP. The
eleven that remain are right as they are: five are the `(..., extra=...)` form in
contract/tools.py, meaning "call it again with what you had, plus this", and six carry a
placeholder the caller must fill. A refusal is now either a call an agent can make, or one that
explicitly marks what the caller must supply, and nothing in between.

CLOSED. P13-O2, 21/09/2026, and the item named the wrong fix. It asked for a shared helper,
because two scripts were restoring docs/contracts/*.yaml by hand after confirming a contract.
contract/tools.confirm reads `store.EXPORT_DIR` at call time, so a script can point it at its
own workspace and nothing outside is written at all. Both scripts now do that, and both are
shorter than they were with the restore. The problem was real and the proposed answer was the
second-best one; writing the fix down as part of the item is what made that visible.

P13-D5. THE FIX BROKE A GOLD QUESTION, WHICH IS THE HARNESS WORKING. B01 asserted that the
NO_CONTRACT refusal marks a decision the caller must make, and that was true until the prose
moved. state.py's refusal now names a runnable propose_dataset_contract(dataset_name="...") with
"show the draft to the user, answer its questions, then call confirm_dataset_contract once they
agree" in DETAIL. The question was updated to match, with a comment saying what it used to
assert and why. A gold question that never changes is describing a system that never improves.

C87. TEN SITES WERE EDITED ON AN ASSUMPTION THAT ONE GREP WOULD HAVE CHECKED, AND THE TREE BROKE.
The prose moved into `detail` at ten refusals, on the assumption that none of the ten already had
one. contract/compatibility.py:188 did -- a computed `detail="; ".join(detail)` -- so the edit
produced `SyntaxError: keyword argument repeated` and eighteen collection errors. The guarded
patch did its job: every replacement asserted its target matched exactly once, and every one did,
because the guard checked what I was replacing and not what I was adding beside it. A guard
proves the text you matched is there; it says nothing about the text you introduce. Both halves
need looking at, and the second half is the one that has no assertion protecting it.

PREDICTION 3 WAS WRONG IN A WAY WORTH KEEPING. I expected two to five existing tests to fail on
the changed refusal text and none did. Every test asserts on the call --
`'propose_dataset_contract(dataset_name="other")' in text` -- and the bare call was always a
substring of the prose version, so removing the prose removed nothing any assertion named. The
tests were already testing the thing that mattered rather than the sentence around it, which is
the outcome the C-series keeps asking for and rarely gets to record.

MEASURED VALIDATION, 21/09/2026. `uv run python eval/run_eval.py`: 31 passed, 0 failed, 0
skipped, SCORE 31/31 (100%) -- correctness 5/5, behavioural 22/22, regression 4/4. The refusal
roster reads 26 of 37 (70%), from 16 of 37 (43%). Full suite 1759 and the five acceptance
scripts unchanged -- 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0 -- because the refusals kept their
reason, their call and their behaviour, and moved one sentence one line up. Digests:
  83008a160a2d13fdbb9a89badb8132f9270f3111dbac4c9d137a63b9cd4c8b38  eval/run_eval.py
  b4ee344c82c5a3005dbafe01c31371d84ca78f48f623838ca1d2e07e2edab788  eval/gold_questions.yaml
  88e76039d435319b2b2aff30b0f1dff7cc2f55a7a7147619ad9995517cd3b8ae  src/analytics_agent/state.py
  abf64b98afbac5daa71d263846011a207c58e9b1451bb19e784edc1393d92a93  src/analytics_agent/validate/tools.py

## Phase 13, Step 3 - filling the question set, 21/09/2026

Step document: docs/steps/phase13_step3_questions.md, written before the run with five
predictions. Four held. SCORE 67/67 (100%) over 32 questions -- 14 correctness, 12 behavioural,
6 regression -- from 31/31 over 14.

P13-D6. A GOLD QUESTION WITH NO `reason` IS A CAVEAT RATHER THAN A REFUSAL. The guide asks for
"cases where the correct behaviour is to refuse or caveat", and a suite testing only refusals
would miss the half where the tool answers and warns. A caveat question asserts the call
succeeds and that the reply contains what the caller needs to know. B06 is the guide's own
example and it passes: calendar_coverage on a table with a month removed prints "11 month(s)
hold rows and 1 hold none: 2024-07" and "A gap is not a zero -- nothing says whether the
business stopped".

P13-D7. THE GAPPED TABLE IS CONSTRUCTED, AND SAYING SO IS THE POINT. Measured: no fixture has a
missing period. clean_sales holds all twelve months of 2024 and broken_sales all nineteen of its
span; gaps_and_dupes is named for blanks and repeats in the HEADER, not for time. So
clean_gapped is clean_sales with 2024-07 removed, written out and loaded through load_csv rather
than made with CTAS -- a table created behind the loader's back is not a loaded dataset as far
as the gate is concerned, and a gold question needing a back door would be testing one. Three
tables now, which is what P9-O2 asked for.

C88. A GOLD QUESTION ACCUSED THE PRODUCT OF A DEFECT IT DOES NOT HAVE. R09 tested that coercion
failures are counted (F9) by searching `str(result)` for the word "null", and reported the
mitigation missing. `LoadResult` carries `coercion_failures` and `coercion_total`; reading them
gives 10 failures counted per column, {'units': 7, 'unit_price': 3}. The check was looking at
the wrong surface. This is worth naming because the failure mode of an eval is not that it
misses things -- it is that it reports a defect that is not there, and a team that has been
told three times to look at something correct stops looking. A gold question is a claim about
the product and carries the same burden as any other.

The route to it was the product working. The default load raised LoadRefused at row 5101 --
"Column 'units' was read as BIGINT, but this row holds 'n/a' ... Nothing has been dropped, the
load stopped instead" -- and named the reload that counts them. The check had not expected the
refusal at all, and the crash is what sent me to read LoadResult.

C89. A REFUSAL NAMED A RECOVERY THAT WAS ITSELF REFUSED, AND I WROTE IT. Gold question B09
called render_chart with a chart kind nobody draws. The refusal was right, and its NEXT STEP was
`compute_analysis(dataset_name="clean_sales", analysis_type="frequency")` -- the analysis and
none of the parameters it had just been given. frequency without its column is refused, so the
recovery offered was one that fails. I added this in Phase 11 Step 3 and nothing caught it,
because Step 3's tests asserted `'compute_analysis(dataset_name="sales"' in text` and that
substring was present either way. The call now carries the parameters actually used, rendered
through the same `_literal` the reproduction appendix uses, so the two cannot drift. A refusal
whose recovery is itself refused is worse than no recovery: it costs the caller a turn and
teaches them the tool is unreliable.

PREDICTION 5 WAS WRONG AND THE PROJECT IS BETTER FOR IT. The step document predicted the score
would not be 100% at the end, on the grounds that finding something and fixing it in the same
step is optimistic. Both failures were fixable where they were found -- one a real defect, one a
wrong question -- and neither needed an open item. Recorded because the previous step's wrong
prediction was pessimistic too (P12-D23), and two in a row suggests I am calibrating the
codebase as more fragile than it is.

MEASURED VALIDATION, 21/09/2026. `uv run python eval/run_eval.py`: 67 passed, 0 failed, 0
skipped, SCORE 67/67 (100%) -- correctness 14/14, behavioural 47/47, regression 6/6 across six
Failure Mode Register ids (F7, F9, F11, F12, F14, F15). The refusal roster is unchanged at 26 of
37 (70%). Full suite 1759 and the five acceptance scripts unchanged -- 99/0/2, 19/0/0, 35/0/1,
26/0/0, 36/0/0 -- because the one src/ change lengthens a refusal's next_call and every existing
assertion on it names a substring that is still there. Digests:
  eval/run_eval.py, eval/gold_questions.yaml and src/analytics_agent/analysis/tools.py as
  printed in the commit.
