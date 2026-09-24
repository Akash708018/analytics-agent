# Stress matrix report -- 24/09/2026

`uv run python scripts/stress_matrix.py` ran 40 generated datasets through every tool on the web
path (upload, draft, load, describe, profile, clean, contract, validate, 27 analyses, 3 charts,
report): **1,634 calls in 112 s -- 1,431 OK, 184 refused, 15 wrong, 2 crashed, 2 suspect.** Every
dataset's expected answers were computed by the generator in plain Python, not by the engine.
Raw results: `docs/stress/stress_matrix.json`. Re-run one case: `uv run python
scripts/stress_matrix.py <name>`.

Not exercised here: the Postgres door (no server in this container), the live LLM (no key), and
real browser rendering (the UI was driven through Streamlit's AppTest only).

## Bugs, most severe first

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

## Results by dataset

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
