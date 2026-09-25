# Cleanup Step 12: the retail run's quick fixes -- gates in real GB, silent nulls said, codes not cast, currency read, empty months named

First of the fix steps after the retail fixture run (docs/steps/retail_fixture_run.md). This one
closes RF-O2, RF-O3, RF-O4, RF-O5 and the A3 finding. Steps 13-16: validation rules (RF-O7);
analysis options (RF-O6, RF-O8, G1, H1/H6); the measure model (RF-O1, G3, C6, J1); the re-run.

## What was established before this document

- RF-O2. config.SIZE_GATES is built from `_MIB`/`_GIB` and printed by human_bytes as "MB"/"GB":
  csv_refuse_bytes = 2,684,354,560 (2.5 GiB). The key's 2,595,199,347-byte file is 2.60 GB as macOS
  Finder and `ls` report it, and was warned about as "2.4 GB ... Loading will work". The warn
  message names no threshold.
- RF-O4. csv_loader passes nullstr=DEFAULT_NA_VALUES ("", NA, N/A, -, --, null, NULL, None) to
  read_csv; the load reply says nothing about what it nulled. rating lost 8,069 'NA' and 5,353 '-'.
- RF-O5. clean/detect.proposed_type returns BIGINT for sku ('000001'..'000500'); `_cast_ok` in the
  profile lets '007' read as an integer, deliberately. Neither counts the leading zeros a number
  drops, so C003 was offered as discarding nothing and recommended.
- A3. list_price_display ('₹10,846.00') is text; neither the profile nor detection tries it with
  the currency sign and thousands separators removed.
- RF-O3. period_compare and growth_decomposition print "{a} covers N days ... sets N days of data
  against M" from calendar length. The retail 2024 "covers 366 days" with September empty.

## The fix

A. Gates in decimal units. SIZE_GATES from 10^6 / 10^9 bytes (the halving on small machines kept);
   human_bytes decimal (KB = 1,000). RAM stays GiB. The WARN message names its threshold and the
   refuse limit.
B. The load reply names the tokens it read as NULL: per column, per token, counted in one extra
   pass over the file read as text. Blank is not listed (an empty field is null in every reader).
C. No numeric type is proposed for a column where a value has a leading zero before another digit;
   the profile says "N have leading zeros a number would drop".
D. Currency text: a column whose values parse as a number once [₹$€£¥,] and spaces are removed (90%
   share, and at least one value holding such a character) is named by the profile and offered as
   CONVERT_TYPE with that removal in its SQL; losses counted as for any conversion.
E. Empty months inside a compared quarter or year are named by period_compare and
   growth_decomposition ("2024 holds no rows in 2024-09, so this sets 11 of its 12 months against
   12 of 12"); "days of data" becomes "calendar days" -- a day count was never a count of data.

## Commands

1. Baseline `uv run pytest -q`. Expected 1899.
2. Falsify: tests for A-E. Expected all fail on the unfixed tree; two existing tests pin "28 days of
   data against 31" and are updated with E, recorded here.
3. Apply. Expected: new pass, suite 1899 + new.
4. Live on the retail fixture: check_file of a 2,595,199,347-byte sparse file -> REFUSE "2.6 GB";
   load reply names rating 'NA' 8,069 and '-' 5,353; plan offers no CONVERT_TYPE on sku and one on
   list_price_display; period_compare 2024 vs 2025 names 2024-09.
5. Acceptance, eval, UI. Expected unchanged: 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; 76/76; 37.
6. Records, commit.

## Results

1. Baseline. 1899 (measured at the end of the retail run, tree unchanged).
2. Falsify. 13 new tests: `12 failed`; the one that passed is
   test_a_file_over_the_limit_is_refused_naming_the_limit -- a refusal named its limit before too;
   it guards the change rather than testing it.
3. Apply.
   3.1. test_a_currency_column_is_offered_with_the_symbols_removed failed on
        `AttributeError: 'CleaningAction' object has no attribute 'rendering'` -- the TEST was wrong;
        an action carries its statement as `sql`. It now runs that statement, as a person approving
        it would, and reads the column back: [1234.0, 990.0, 10846.5, 58.0].
   3.2. E rewords "days of data" to "calendar days". Two tests pinned "28 days of data against 31"
        (period_compare, growth_decomposition) -- false even there: February 2017 holds one row. They
        now pin "28 calendar days against 31"; period_compare's negative guard follows the string.
   Suite `1912 passed` (1899 + 13).
4. Live on the retail fixture:
     L2  "[REFUSE] BLOCKED: size_refuse_sparse.csv is 2.6 GB, over the 2.5 GB limit."
     A5  "NOTE: 13,422 value(s) matched a missing-value token and were read as NULL: rating ('NA'
         8,069, '-' 5,353). ..."
     A2  no CONVERT_TYPE on sku.
     A3  "C003 CONVERT_TYPE on list_price_display: read list_price_display as DECIMAL(18,2), removing
         the currency sign and thousands separators first (currency text)".
     E3  "2024 holds no rows in 2024-09 (11 of its 12 months hold rows), so its total reads low for
         the missing months alone and the change mixes the business with the gap." and "366 calendar
         days against 365".
   All as expected.
5. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76; UI 37. As expected.

MEASURED VALIDATION line and digests: docs/decisions.md, section Cleanup Step 12.
