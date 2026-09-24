# Step 8 -- the residuals, then rounds 2 to 4 of new anomalies

`uv run python scripts/stress_matrix.py --round all`. Each round added anomalies no earlier round
had. Each round was run, every non-OK line triaged, each bug fixed with a test
(`tests/test_stress_fixes.py`, 46 tests), and every round re-run. The loop stopped at round 4,
the first round to find no new bug. Final code:

| round | datasets | calls | OK | refused | wrong | crash | suspect |
|---|--:|--:|--:|--:|--:|--:|--:|
| 1 | 40 | 1,778 | 1,649 | 118 | 10 | 0 | 1 |
| 2 | 25 | 1,137 | 1,037 | 97 | 3 | 0 | 0 |
| 3 | 18 | 875 | 827 | 40 | 8 | 0 | 0 |
| 4 | 12 | 546 | 523 | 23 | 0 | 0 | 0 |

Every "wrong" line is a load-time check on text the suggested cleaning then converts to the
file's exact figures. There are two exceptions, both by design: a formula file holding no values,
and `nil` in a number column, which is undeclared and so waits for a person's approval.

| # | Found in | Bug | Fix |
|---|---|---|---|
| R1 | residual | Windows-1252 file with `€` did not load at all | Encoding sniffed (UTF-16, UTF-8, cp1252, Latin-1); a streamed UTF-8 copy |
| R2 | residual | A complete last row labelled "Total" would be dropped | The label counts only if the row lacks what data rows fill |
| R3 | residual | Excel errors named the wrong row after blank rows | Sheet row numbers kept |
| R4 | residual | `1,234`-only columns got no conversion | Both readings offered, neither suggested, both together refused |
| R5 | residual | Tail probe could start inside a quoted field | Starts at a quote-balanced boundary; records counted, not lines |
| R6 | residual | Profile printed "range -inf to nan" | Float ranges over finite values |
| 2a | round 2 | Time-zone timestamps crashed `describe_dataset` (pytz) | Stored in UTC by every loader |
| 2b | round 2 | Ragged rows refused with a false column count | Short rows padded, noted |
| 2c | round 2 | Trailing delimiter added an empty `column_10` | Dropped when unnamed and empty, noted |
| 2d | round 2 | Accounting `(1,234.56)` not converted | Read as negative |
| 2e | round 2 | Excel `#DIV/0!` / `#N/A` cells made the column text | Loaded empty, counted |
| 2f | round 2 | Vertically merged cells left rows empty | Merge value filled, as displayed |
| 2g | round 2 | Mixed CRLF/LF (and so `#` comment files) failed to load | Normalised copy; `#` lines are comments |
| 2h | round 2 | A header of years read as "headerless" | Year headers recognised |
| 2i | round 2 | 20-digit integers summed off by 34,650 (DOUBLE) | Reloaded as HUGEINT |
| 3a | round 3 | **Two-digit years loaded silently wrong** (31/12/24 -> 2031-12-24) | Kept as text; cleaning reads day/month first, two-digit formats first |
| 3b | round 3 | Header cell with a line break -> false refusal | One header read as a record |
| 3c | round 3 | `Ventes 2024 (été).csv` refused at upload | Name made safe |
| 3d | round 3 | SAP `1234.56-` not converted | Read as negative |
| 3e | round 3 | `0000-00-00` made the date conversion lossy | Treated as absent |

Correct as found, not bugs: `region` beside `Region` (loads as `region_2`); a duplicate `order_id`
(the engine proposes a unique composite key and refuses `order_id` alone); a column named `rowid`;
1,000,000 rows (7 s); zero variance, all-negative measures (a share of a negative total is refused
on principle), two rows, three stacked Excel headers, 1800-2999 dates (correlated_shift 11.4 s over
14,400 months).

---

# Stress matrix report -- 24/09/2026, fixed at Phase 14 Step 7

`uv run python scripts/stress_matrix.py` runs 40 generated datasets through every tool on the web
path (upload, draft, load, describe, profile, up to three rounds of suggested cleaning, contract,
validate, 27 analyses, 3 charts, report). Every dataset's expected answers are computed by the
generator in plain Python, not by the engine. Each dataset is checked against them at load and
again after the suggested cleaning. Raw results: `docs/stress/stress_matrix.json`. Re-run one
case: `uv run python scripts/stress_matrix.py <name>`.

| run | calls | OK | refused | wrong | crash | suspect |
|---|--:|--:|--:|--:|--:|--:|
| Step 6, before the fixes | 1,634 | 1,431 | 184 | 15 | 2 | 2 |
| Step 7, after the fixes | 1,773 | 1,645 | 118 | 9 | 0 | 1 |

**All 14 bugs are fixed** (P14-O3 to O12 closed; each has a test in `tests/test_stress_fixes.py`).
The 9 remaining "wrong" lines are load-time checks on text the loader rightly keeps as
text: decimal commas, currency, mixed date formats, a pasted header, text-typed Excel cells. For
every one of them the engine's own suggested cleaning then gives the file's exact figures
(row counts, sums, date ranges all OK under `after_clean`). The one exception is
`xlsx_formulas_no_cache`, whose file holds no computed values at all; it loads empty, and the draft
says so. The one "suspect" is `describe_dataset` showing the raw sample of a column that really
does hold `nan` and `inf`.

Not exercised: the Postgres door (no server in this container), the live LLM (no key), and real
browser rendering (the UI was driven through Streamlit's AppTest only).

## What was fixed

| # | Bug | Fix |
|---|---|---|
| B1 | CSV total row doubled every sum | The CSV draft reads its last 64 KB (a seek, the same cost at any size) and finds a footer as Excel does. A row labelled Total / Grand total / Subtotal / Sum counts as one however full it is. |
| B2 | "Lossless" conversion lost leading zeros | A numeric conversion counts a value like `00311` as lost. It is lossy, shows the zeros as its sample, and is never pre-ticked. |
| B3 | Excel formulas loaded as their text | Workbooks are read with `data_only=True`, so Excel's saved values load. A formula saved with no value is named in the draft. |
| B4 | Infinity crashed profile, summary_stats, outlier_detection | Statistics are taken over finite values, with a note of how many were set aside. Cleaning offers `NULL_NON_FINITE`. The filter applies to floating-point columns only: on all 201 columns it took a profile from 4 s to 24 s. |
| B5 | Empty first sheet crashed the Upload screen | The draft reads the first sheet holding data and says so. A named empty sheet is a refusal that lists the sheets with data. The backend never lets a ValueError reach the screen. |
| B6 | Blank Excel rows loaded as NULL rows | Skipped and counted in the load's notes. |
| B7 | Latin-1 unreadable; the refusal leaked the server path | Encoding sniffed from both ends (UTF-8, else Latin-1), with a retry on a mid-file error and a note. DuckDB errors lose paths and SQL. The web backend strips workspace paths from every refusal. |
| B8, B9 | Decimal commas, currency, thousands separators, percent stayed text | A conversion may carry its own expression. The convention is decided only by values that settle it; `1,234` alone is left for the person. |
| B10 | Header-only CSV refused with a false reason | "has a header and no data rows". |
| B11 | Repeated header mid-file unrecognised | `DROP_HEADER_ROWS`, lossless and suggested. The conversions it unblocks come on the next proposal. |
| B12 | Mixed date formats stayed text | A COALESCE of TRY_STRPTIME over the formats present. Day-first or month-first only when a value settles it. |
| B13 | Refusals quoted Python's TypeError | The missing argument is named in the engine's words. NEXT STEP fills it from the contract's declared columns, or points at the contract when it declares none. |
| B14 | Fractional DOUBLE suggested as a dimension; one row all "ignore" | The few-values rule is for whole numbers only. Distinctness rules need more than one row. |

Residual, not a bug: the profile's range line prints a float column's raw min and max, so a
column holding NaN reads "range -inf to nan". Its statistics are finite, and a note says so.

## Results by dataset, after the fixes

| dataset | what it holds | calls | OK | refused | wrong | crash | suspect |
|---|---|--:|--:|--:|--:|--:|--:|
| baseline_csv | 500 clean sales rows, comma, ISO dates -- the control | 46 | 46 | 0 | 0 | 0 | 0 |
| semicolon_decimal_comma | European export: ';' delimiter, ',' decimal mark | 54 | 53 | 0 | 1 | 0 | 0 |
| tab_separated | tab-delimited, saved with a .csv name | 46 | 46 | 0 | 0 | 0 | 0 |
| utf8_bom_unicode | UTF-8 with BOM; accented, CJK and emoji values | 47 | 47 | 0 | 0 | 0 | 0 |
| latin1_encoding | Latin-1 (cp1252-style) bytes, not UTF-8 | 47 | 47 | 0 | 0 | 0 | 0 |
| quoted_multiline | quoted fields holding commas, quotes and newlines | 46 | 46 | 0 | 0 | 0 | 0 |
| lf_line_endings | LF line endings (the others are CRLF) | 46 | 46 | 0 | 0 | 0 | 0 |
| header_only | a header and no data rows | 5 | 3 | 2 | 0 | 0 | 0 |
| empty_file | zero bytes | 1 | 0 | 1 | 0 | 0 | 0 |
| one_row | exactly one data row | 46 | 40 | 6 | 0 | 0 | 0 |
| one_column | a single numeric column | 44 | 15 | 29 | 0 | 0 | 0 |
| wide_201_columns | 300 rows x 201 columns | 45 | 22 | 23 | 0 | 0 | 0 |
| big_200k_rows | 200,000 rows (~14 MB) | 46 | 46 | 0 | 0 | 0 | 0 |
| null_and_constant_columns | one column entirely empty, one constant | 46 | 46 | 0 | 0 | 0 | 0 |
| duplicate_and_blank_headers | two columns named 'value' and one with no name | 43 | 30 | 13 | 0 | 0 | 0 |
| sql_hostile_names | column names that are SQL words or hold quotes, dots, spaces, symbols | 44 | 44 | 0 | 0 | 0 | 0 |
| mixed_number_text | a numeric column holding 'n/a', 'twelve', '', '-', '12 units' | 53 | 53 | 0 | 0 | 0 | 0 |
| dates_dd_mm_yyyy | dates written 31/12/2024 (day first) | 46 | 46 | 0 | 0 | 0 | 0 |
| dates_mm_dd_yyyy | dates written 12/31/2024 (month first) | 46 | 46 | 0 | 0 | 0 | 0 |
| dates_mixed_formats | one date column in five formats | 54 | 53 | 0 | 1 | 0 | 0 |
| dates_ambiguous_dd_mm | day-first dates whose day is always <= 12, so month-first also parses | 46 | 46 | 0 | 0 | 0 | 0 |
| csv_total_row_at_bottom | a spreadsheet-style 'Total' row under the data | 46 | 46 | 0 | 0 | 0 | 0 |
| repeated_header_mid_file | two exports concatenated, so the header line appears again mid-file | 57 | 53 | 0 | 4 | 0 | 0 |
| boolean_spellings | yes/no, Y/N, TRUE/FALSE, 1/0 columns | 46 | 46 | 0 | 0 | 0 | 0 |
| currency_percent_thousands | '$1,234.56', '12.5%', thousands separators | 54 | 53 | 0 | 1 | 0 | 0 |
| scientific_nan_inf | scientific notation and NaN / Infinity / -inf text | 44 | 18 | 25 | 0 | 0 | 1 |
| leading_zero_ids | zip codes like 00501 that must stay text | 46 | 31 | 15 | 0 | 0 | 0 |
| messy_text_and_missing_tokens | padding, case variants and N/A, -, NULL, none | 55 | 55 | 0 | 0 | 0 | 0 |
| exact_duplicate_rows | 20 rows repeated exactly | 14 | 13 | 1 | 0 | 0 | 0 |
| negative_and_zero_measures | returns as negative rows, zero rows | 46 | 46 | 0 | 0 | 0 | 0 |
| single_group | every row in one region | 46 | 46 | 0 | 0 | 0 | 0 |
| time_series_with_gaps | 2024 with March-May missing | 46 | 46 | 0 | 0 | 0 | 0 |
| five_day_span | all dates inside five days | 46 | 43 | 3 | 0 | 0 | 0 |
| xlsx_real_dates | Excel with real date cells and numbers | 46 | 46 | 0 | 0 | 0 | 0 |
| xlsx_merged_header_footer | two-row merged header and a footer note | 46 | 46 | 0 | 0 | 0 | 0 |
| xlsx_formulas_no_cache | revenue as =G2*H2 formulas with no cached value (as openpyxl/pandas write them) | 46 | 45 | 0 | 1 | 0 | 0 |
| xlsx_formulas_cached | revenue as formulas WITH cached values, as Excel saves them | 46 | 46 | 0 | 0 | 0 | 0 |
| xlsx_blank_rows_mid | three blank rows in the middle of the data | 46 | 46 | 0 | 0 | 0 | 0 |
| xlsx_empty_first_sheet | first sheet empty, data on the second | 46 | 46 | 0 | 0 | 0 | 0 |
| xlsx_numbers_as_text | a third of the units cells stored as text | 54 | 53 | 0 | 1 | 0 | 0 |

---

# The Step 6 report, as found

## Bugs, most severe first (as found at Step 6)

| # | Severity | Dataset | What goes wrong | Where |
|---|---|---|---|---|
| B1 | **High, silent** | csv_total_row_at_bottom | A "Total" row under CSV data is loaded as a data row: **every sum doubles** (units 7,530 vs 3,765; revenue 992,201 vs 496,100.50). The draft says "Ready to load"; cleaning says "Nothing to clean". The draft does say the file's end was not examined, blaming "a large file" -- this one is 10 KB. The footer check runs only for Excel. | `ingest/preview.py` ~515 |
| B2 | **High, silent** | leading_zero_ids | Cleaning proposes `CONVERT_TYPE zip` as **lossless and suggested** (pre-ticked on the Clean screen). Applying it turns `00311` into `311`: leading zeros are lost with `values_lost=0`. The contract then suggests `zip` as a **measure** (a sum of zip codes). | `clean/detect.py` type rule |
| B3 | **High, silent** | xlsx_formulas_cached, xlsx_formulas_no_cache | **Every Excel formula column loads as its formula text** (`=G2*H2`, VARCHAR) -- even when the file holds Excel's cached values (checked: openpyxl `data_only=True` reads 2.5, 5.0, 7.5 from the same file). Workbooks are opened without `data_only=True`. The measure is lost with no warning. | `ingest/excel.py`, `ingest/draft.py` (`load_workbook`) |
| B4 | High, crash | scientific_nan_inf | A column holding `Infinity`/`-inf` (DuckDB reads the text as DOUBLE inf) makes **`profile_dataset`, `summary_stats` and `outlier_detection` raise** `OutOfRangeException: STDDEV_SAMP is out of range!`. The exception escapes the MCP tool, so the user gets no answer at all. `NaN` is also loaded as a float, not as missing. | `profile/table_profile.py:725`; analysis stats |
| B5 | High, crash (web) | xlsx_empty_first_sheet | A workbook whose **first sheet is empty** makes `RealBackend.draft_ingest` raise `ValueError: No preview rows` (only `LoadRefused` is caught), so the Upload screen shows an exception. The person never sees the sheet picker. On the MCP path it is refused, but the refusal says "the file appears to be empty" -- the data is on sheet 2. With `sheet="Data"` it loads fine. | `webapp/real_backend.py` draft_ingest; `ingest/preview.py:161` |
| B6 | Medium | xlsx_blank_rows_mid | Blank rows in the middle of an Excel sheet load as **all-NULL rows** (163 rows vs 160). Row counts, means and shares are off. Profile sees them as "3 null" per column and 2 duplicates. Cleaning offers only a lossy de-duplication that would leave one blank row. | Excel loader |
| B7 | Medium | latin1_encoding | A **Latin-1 CSV cannot be loaded.** The draft succeeds, then the load fails with DuckDB's raw error, which shows the web user the **server's absolute path** (`/home/.../workspace/ws_.../uploads/latin1.csv`) and a SQL fragment. There is no NEXT STEP and no encoding option. | `ingest/csv_loader.py` |
| B8 | Medium | semicolon_decimal_comma | European exports (`;` delimiter, decimal comma `214,93`) load their decimals as **text**. Cleaning says "every column already reads as the type it holds" -- **no conversion offered**, so those columns can never be measures. | `clean/detect.py` |
| B9 | Medium | currency_percent_thousands | `$1,234.56`, `1,234.56` and `12.5%` load as text, and cleaning again offers nothing and says nothing is wrong. | `clean/detect.py` |
| B10 | Medium | header_only | A CSV with a header and no rows is refused with a **false reason**: "9 column names given but header_only.csv has 1 columns". It has 9 columns and 0 rows. | `ingest/csv_loader.py` |
| B11 | Low-Medium | repeated_header_mid_file | Two exports pasted together (the header line repeated mid-file) make every numeric and date column **text**, and add 1 row. Cleaning offers only lossy casts, and nothing names the repeated header as the cause. | ingest draft |
| B12 | Low | dates_mixed_formats | One date column in five formats stays text, with no cleaning proposal, so in the web app it can never become the date column. Conservative, but a dead end. | `clean/detect.py` |
| B13 | Low (UX) | one_row, one_column, wide, sci | A missing argument is refused with Python's own wording -- "top_n() missing 1 required positional argument: 'measure'" -- rather than the engine naming the parameter and what to pass. | `analysis/tools.py` |
| B14 | Low | scientific_nan_inf, one_row | Role suggestions: a DOUBLE column with 8 distinct values is suggested as a **dimension**. In a one-row file every non-key column is suggested "ignore". | `contract/evidence.py` suggest_role |

## Checked and correct (not bugs)

- **Loading:** day-first, month-first and *ambiguous* day-first dates (0 of 200 wrong). Tab-delimited,
  LF, CRLF, BOM with CJK and emoji, and quoted fields with commas, quotes and newlines. 200,000 rows
  in 7.9 s. 201 columns. SQL-hostile column names (`order`, `select`, `unit "price"`, `a.b`,
  `revenue ($)`). Duplicate and blank headers are renamed `value_2` / `column_4`, and the draft says
  so. Excel real dates and a merged two-row header with a footer note.
- **Cleaning:** padding is trimmed and suggested; case-folding is flagged lossy and not
  suggested; missing tokens are normalised. Exact duplicates get a lossy de-duplication that is not
  suggested, and a repeating key is refused at the contract (`KEY_NOT_UNIQUE`). Numbers stored as
  text in Excel get a lossless conversion. Booleans: `yes/no` and `TRUE/FALSE` load as BOOLEAN,
  `Y/N` as text.
- **Analyses:** negative and zero measures, a single group, a series with a three-month gap and a
  five-day span all ran.
- **Refusals that are right** (most of the 184): a 60-group dimension over the 49-group cap. Temporal
  analyses with no date column. Analyses needing a measure when the contract has none (one-row,
  one-column and wide files). An empty file refused at upload.

## Results by dataset at Step 6

| dataset | what it holds | calls | OK | refused | wrong | crash | suspect |
|---|---|--:|--:|--:|--:|--:|--:|
| baseline_csv | 500 clean sales rows, comma, ISO dates -- the control | 46 | 46 | 0 | 0 | 0 | 0 |
| semicolon_decimal_comma | European export: ';' delimiter, ',' decimal mark | 46 | 42 | 3 | 1 | 0 | 0 |
| tab_separated | tab-delimited, saved with a .csv name | 46 | 46 | 0 | 0 | 0 | 0 |
| utf8_bom_unicode | UTF-8 with BOM; accented, CJK and emoji values | 47 | 47 | 0 | 0 | 0 | 0 |
| latin1_encoding | Latin-1 (cp1252-style) bytes, not UTF-8 | 3 | 2 | 1 | 0 | 0 | 0 |
| quoted_multiline | quoted fields holding commas, quotes and newlines | 46 | 46 | 0 | 0 | 0 | 0 |
| lf_line_endings | LF line endings (the others are CRLF) | 46 | 46 | 0 | 0 | 0 | 0 |
| header_only | a header and no data rows | 5 | 3 | 2 | 0 | 0 | 0 |
| empty_file | zero bytes | 1 | 0 | 1 | 0 | 0 | 0 |
| one_row | exactly one data row | 46 | 18 | 28 | 0 | 0 | 0 |
| one_column | a single numeric column | 44 | 15 | 29 | 0 | 0 | 0 |
| wide_201_columns | 300 rows x 201 columns | 45 | 22 | 23 | 0 | 0 | 0 |
| big_200k_rows | 200,000 rows (~14 MB) | 46 | 46 | 0 | 0 | 0 | 0 |
| null_and_constant_columns | one column entirely empty, one constant | 46 | 46 | 0 | 0 | 0 | 0 |
| duplicate_and_blank_headers | two columns named 'value' and one with no name | 43 | 30 | 13 | 0 | 0 | 0 |
| sql_hostile_names | column names that are SQL words or hold quotes, dots, spaces, symbols | 44 | 44 | 0 | 0 | 0 | 0 |
| mixed_number_text | a numeric column holding 'n/a', 'twelve', '', '-', '12 units' | 47 | 47 | 0 | 0 | 0 | 0 |
| dates_dd_mm_yyyy | dates written 31/12/2024 (day first) | 46 | 46 | 0 | 0 | 0 | 0 |
| dates_mm_dd_yyyy | dates written 12/31/2024 (month first) | 46 | 46 | 0 | 0 | 0 | 0 |
| dates_mixed_formats | one date column in five formats | 46 | 33 | 12 | 1 | 0 | 0 |
| dates_ambiguous_dd_mm | day-first dates whose day is always <= 12, so month-first also parses | 46 | 46 | 0 | 0 | 0 | 0 |
| csv_total_row_at_bottom | a spreadsheet-style 'Total' row under the data | 46 | 43 | 0 | 3 | 0 | 0 |
| repeated_header_mid_file | two exports concatenated, so the header line appears again mid-file | 47 | 16 | 27 | 4 | 0 | 0 |
| boolean_spellings | yes/no, Y/N, TRUE/FALSE, 1/0 columns | 46 | 46 | 0 | 0 | 0 | 0 |
| currency_percent_thousands | '$1,234.56', '12.5%', thousands separators | 46 | 45 | 0 | 1 | 0 | 0 |
| scientific_nan_inf | scientific notation and NaN / Infinity / -inf text | 43 | 12 | 28 | 0 | 1 | 2 |
| leading_zero_ids | zip codes like 00501 that must stay text | 48 | 34 | 13 | 1 | 0 | 0 |
| messy_text_and_missing_tokens | padding, case variants and N/A, -, NULL, none | 48 | 48 | 0 | 0 | 0 | 0 |
| exact_duplicate_rows | 20 rows repeated exactly | 14 | 13 | 1 | 0 | 0 | 0 |
| negative_and_zero_measures | returns as negative rows, zero rows | 46 | 46 | 0 | 0 | 0 | 0 |
| single_group | every row in one region | 46 | 46 | 0 | 0 | 0 | 0 |
| time_series_with_gaps | 2024 with March-May missing | 46 | 46 | 0 | 0 | 0 | 0 |
| five_day_span | all dates inside five days | 46 | 43 | 3 | 0 | 0 | 0 |
| xlsx_real_dates | Excel with real date cells and numbers | 46 | 46 | 0 | 0 | 0 | 0 |
| xlsx_merged_header_footer | two-row merged header and a footer note | 46 | 46 | 0 | 0 | 0 | 0 |
| xlsx_formulas_no_cache | revenue as =G2*H2 formulas with no cached value (as openpyxl/pandas write them) | 46 | 45 | 0 | 1 | 0 | 0 |
| xlsx_formulas_cached | revenue as formulas WITH cached values, as Excel saves them | 46 | 45 | 0 | 1 | 0 | 0 |
| xlsx_blank_rows_mid | three blank rows in the middle of the data | 47 | 46 | 0 | 1 | 0 | 0 |
| xlsx_empty_first_sheet | first sheet empty, data on the second | 2 | 1 | 0 | 0 | 1 | 0 |
| xlsx_numbers_as_text | a third of the units cells stored as text | 48 | 47 | 0 | 1 | 0 | 0 |
