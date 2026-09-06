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
