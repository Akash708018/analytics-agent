# Cleanup Step 13: rules a row must satisfy, declared in the contract and counted by validation

Second fix step from the retail run. Closes RF-O7 (B1-B3).

## What was established before this document

- validate_dataset runs key, date, reference, domain and row-count checks (validate/tools.py:167).
  None can say "units must be positive", "delivery is not before the order" or "no sale after the
  rep's exit", and the retail run's 8, 13 and 37 violating rows passed as "all 6 check(s) passed".
- The contract already carries caller SQL safely: known_exclusions[].rule goes through
  util/sql_guard (one statement, no subquery -- P8-D7 measured /etc/passwd read through read_csv --
  bound against the table as BOOLEAN with LIMIT 0).
- Every check reports passed + failed + not_checked = rows (P7-D4); a rule that is NULL for a row
  did not judge it, so that row is not_checked, never passed.

## The fix

DatasetContract.expectations: [{rule, reason}] -- Great Expectations' name for "a statement about every
row". Proposed with expectations=[...]; each rule bound with sql_guard at proposal time, so a typo is
refused before it is stored. validate_dataset adds one check per rule, after domains: failed where the
rule is false, not_checked where it is NULL, evidence the failing rows' primary-key values (capped,
counted). Validation reports; nothing is blocked -- a validation failure is settled in the contract
or the data by a person (P7-D12).

## Commands

1. Baseline 1912.
2. Falsify: tests in tests/test_validate_expectations.py -- a rule counted with NULLs apart, evidence
   by key, a bad rule refused at proposal, the rule rendered in the contract and stored. Expected all
   fail.
3. Apply. Expected 1912 + new.
4. Live, retail: units > 0 -> 8 failed, the key's eight line_ids; delivery date (both formats) not
   before the order day -> 13; order_ts not after the rep's exit + 1 day -> 37 across 23 reps; a
   margin rule within 0.01 -> 0 failed (B4's negative control).
5. Acceptance, eval, UI unchanged. 6. Records, commit.

## Results

1. Baseline 1912 (the end of Step 12).
2. Falsify. `5 failed`. As expected.
3. Apply.
   3.1. Three tests failed in their own confirm() helper (IndexError): my test contract had no
        analysis window, so the proposal stayed PROVISIONAL. The TEST was incomplete; it now states
        the window. `5 passed`.
   3.2. Suite: `12 failed, 1905 passed`, all in test_validate_tools.py -- its stand-in `_Contract`
        lists "the fields validate/tools.py reads off a contract, and no more", and the tool now
        reads one more. The stand-in gained `expectations=[]`, as the step-11 test double gained
        `final=`. Suite `1917 passed` (1912 + 5).
4. Live, retail, rules proposed with the contract and validated:
     units > 0                                              FAIL 224,827 / 8 / 0 -- L0022845, ...
     delivery (both formats) >= the order's day             FAIL 157,451 / 13 / 67,371 not judged
     rep_exit_date IS NULL OR order_ts <= exit + 1 day      FAIL 224,798 / 37 / 0; 23 reps (SQL)
     |margin_pct - (rev - cost) / rev * 100| <= 0.01         PASS 224,835 / 0 / 0
   B1 8, B2 13, B3 37 across 23 reps, B4 nothing flagged -- the key's four figures. As expected.
   The 67,371 not judged are the Store rows with no delivery date, counted apart, not as passing.
5. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76; UI 37. As expected.

Also found, not changed here: validate/rules.py defines reference_checks and domain_checks twice
each (lines ~475/645, ~571/769); the later copies are live. Flagged as a separate task.

MEASURED VALIDATION line and digests: docs/decisions.md, section Cleanup Step 13.
