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
