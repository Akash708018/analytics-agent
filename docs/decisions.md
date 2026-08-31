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
