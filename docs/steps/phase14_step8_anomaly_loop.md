# Phase 14 Step 8: the remaining issues, then new anomalies in a loop

Opened 24/09/2026. Asked for: "fix whatever issue remains, after that go for different test case
in loop, check the result, fix the bug, use different type of data anomalies".

## Part A -- what remained after Step 7 (stated to the user, not yet registered)

R1. A non-UTF-8 file is read as Latin-1: right for accented letters, wrong for the Windows-1252
    characters Windows exports carry (the euro sign, curly quotes, dashes become C1 control
    characters). Fix: sniff cp1252 before Latin-1; DuckDB reads only UTF-8/UTF-16/Latin-1 without
    an extension, so a non-UTF-8 file is transcoded to a temporary UTF-8 copy by Python, streamed.
R2. A real last data row whose label is "Total" would be taken for a footer. Fix: the totals-label
    rule fires only when the label does not occur in the data rows of the tail too.
R3. Excel error messages give the wrong row number once blank rows have been skipped. Fix: keep the
    sheet row number of every emitted row.
R4. A number column whose every value reads both ways ('1,234') gets no conversion. Fix: offer both
    readings as two conversions, never suggested, refused together.
R5. The CSV tail probe could start inside a quoted multi-line field. Fix: parse the tail only from a
    line where the probe's quote count is even (a boundary outside any quoted field).
R6. The profile prints "range -inf to nan" for a float column holding NaN. Fix: the range of a
    float column is over its finite values, with the count of the others beside it.

## Part B -- the loop

Round n: add a set of datasets built around anomalies no earlier round had, each with plain-Python
ground truth (scripts/stress_matrix.py, `--round n`); run; triage every non-OK line into bug /
correct refusal / harness error; fix the bugs with a test each; re-run every round so far. Stop
when a round finds no new bug.

## Commands and results

### Part A

A.1 Measured first: DuckDB read_csv with encoding 'windows-1252' or 'cp1252' -> "does not support
the encoding"; with 'latin-1' on a file holding 0x80 (the euro sign) -> "File is not latin-1
encoded". Predicted: the euro sign becomes a control character. WRONG -- worse: such a file did
not load at all. Hence the transcoded UTF-8 copy. UTF-16 (Excel "Unicode text") is recognised by
its byte-order mark and goes the same way.
A.2 R1-R6 fixed, 7 tests. test_b7's note check updated: a Latin-1 file whose letters are the same
bytes in cp1252 now reads as cp1252. R5's test also passes on the old logic (re-created: it
mis-parses mid-probe, rows 2 and 3 wide, and recovers by the last record) -- so it proves the new
code, not the old failure; recorded as that, not as a falsification. Suite: 1881 passed.

### Part B -- the loop

Round 2 (25 datasets). Predicted: trailing delimiter, ragged rows, case-only header clash,
accounting negatives, vertical merges, comment lines and huge integers fail.

    25 datasets, 963 records in 66.2s: CRASH 1, WRONG 7, SUSPECT 0, REFUSED 91, OK 864

The case-only header clash was WRONG as a prediction: 'Region' loads as region_2. Found:
TIMESTAMPTZ crashed describe_dataset (pytz); ragged rows refused with the false "9 names, 1 column"
message; a trailing delimiter added an empty column_10; accounting negatives, Excel error cells
and vertical merges gave no usable column; '#' comment lines and mixed line endings failed to
load (one cause: mixed CRLF/LF, which DuckDB's strict parser refuses); a header of years read as
"headerless". The 20-digit integers looked right only because the harness compared in floats:
the engine's sum was 1e+21 against 1000000000000000034650. Not bugs: the duplicate key (the
engine suggested a unique composite key, and order_id alone is refused KEY_NOT_UNIQUE).
B.2.1 DuckDB accepts no HUGEINT sniff candidate ("not accepted as a valid input", measured); a
post-load check at 2^53 reloads whole-number columns as HUGEINT.
B.2.2 Harness: exact Decimal sums; after-clean checks whenever the load was wrong; a draft that
asks for the header is answered. 10 tests. Re-run:

    25 datasets, 1137 records in 85.4s: CRASH 0, WRONG 3, SUSPECT 0, REFUSED 97, OK 1037

(the 3 are load-time text, each corrected by the suggested cleaning).

Round 3 (18 datasets). Predicted: two-digit years, SAP minus, zero dates, the accented file name,
rowid and a million rows.

    18 datasets, 786 records in 61.1s: CRASH 0, WRONG 13, SUSPECT 0, REFUSED 54, OK 719

rowid and the million rows (7.0 s) were fine -- predictions WRONG. Found: two-digit years loaded
as a valid DATE read YEAR first (31/12/24 -> 2031-12-24), in silence; a header cell holding a
line break gave the false column-count refusal (skip counts lines, not records); the accented
file name was refused; SAP 1234.56- and MySQL 0000-00-00 had no safe conversion. Harness: date
truths with a time compared 'T' against ' '. By design: 'nil' is not declared missing, so its
conversion is lossy and waits for a person.
B.3.1 Measured: strptime '%Y' reads '24' as the year 0024, '%y' refuses '2024'; 69 -> 1969,
68 -> 2068. The first fix still converted to 0001-01-24 -- twice: the plain TRY_CAST read the
column first, then '%Y/%m/%d' in the general format list. Both closed: two-digit-year columns skip
the plain cast, and the settled day/month formats, two-digit first, come before the general list.
5 tests. Re-run: WRONG 9, all load-time except 'nil' (by design).

Round 4 (12 datasets: zero variance, empty and "" groups, 1800/2999 dates, an extreme outlier,
all-negative measures, two rows, three stacked Excel headers, a unicode sheet name, an all-null
measure, a key with nulls, tiny decimals, clock times). Predicted: zero variance breaks the tests.

    12 datasets, 546 records in 57.2s: CRASH 0, WRONG 0, SUSPECT 0, REFUSED 23, OK 523

The prediction was WRONG: nothing broke. Every refusal read and correct (no share of a negative
total; no second period in two rows; no date column for tiny_decimals). correlated_shift took
11.4 s over a 14,400-month calendar (1800-2999). No new bug: the loop stops.

### Checks

    1896 passed in 106.01s (0:01:46)
    43 passed in 11.38s -> 43 passed in 12.21s
    phase6: 36/0/0  phase8: 55/0/3  phase9: 0/0/1  phase10: 0/0/1  phase11: 26/0/0  phase12: 36/0/0
    SCORE: 76/76 (100%)

All four rounds on the final code:

    round 1: 40 datasets, 1778 records: CRASH 0, WRONG 10, SUSPECT 1, REFUSED 118, OK 1649
    round 2: 25 datasets, 1137 records: CRASH 0, WRONG 3, SUSPECT 0, REFUSED 97, OK 1037
    round 3: 18 datasets, 875 records: CRASH 0, WRONG 8, SUSPECT 0, REFUSED 40, OK 827
    round 4: 12 datasets, 546 records: CRASH 0, WRONG 0, SUSPECT 0, REFUSED 23, OK 523

after_clean not OK: xlsx_formulas_no_cache (no values in the file) and null_words_in_numbers
('nil', by design). 0 ws_ directories left.
