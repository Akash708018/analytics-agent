# Cleanup Step 3 - the column-paging skip, which the ledger had already closed

21/09/2026. Baseline 2f6395c. Found by asking whether everything was fixed and counting the
skips instead of repeating the answer: phase8 reported 3 and phase10 1, four in all, while
CLAUDE.md said "three" and named a set that omitted column paging.

## What was wrong, in two places

**1. A skip the ledger had closed kept firing.** decisions.md records "CLOSED. The column-paging
skip, 19/09/2026 ... Olist's customer_state has twenty-seven values, so clause 5 pages on real
data." The skip was never removed from tests/test_phase8.py and printed on every acceptance run
for two more days. This is the role-trap failure in a second place, and it was closed the same
way: a fixture that cannot reach a branch is not an outstanding clause, so it became a check
stating the real reason rather than a skip implying work remains.

**2. The closure overstated what the code did.** The Olist clause checked that the result was
wider than the preview window and that it named its file. Neither reads past the twelfth column.
"Pages on real data" described work nothing performed -- width was proven, paging was not. The
sentence was true of the data and false of the test.

## Measured

    cross_tab on Olist, payment_type by customer_state
      page 1          rows 1 to 6 of 6, columns 1 to 12 of 29
      start_col=13    rows 1 to 6 of 6, columns 13 to 24 of 29

29 columns, not the 27 the ledger's reasoning implied from customer_state's value count -- the
result carries a row-label column and the grid, so the count is not the cardinality. Paging works
on real data, which is what the 19/09 closure asserted without checking.

## Commands and outputs

1. Convert the `else` skip to a check naming the fixture's real width, convert the no-result
   guard from a skip to a failing check, and read past column 12 on the Olist result.
   Expected: 96/0/3 -> 99/0/2, or a FAIL on the paging check if the closure was wrong.
   Result: `99 passed, 0 failed, 2 skipped`, both new checks PASS. Reproduced on a second run.
2. Unit suite unchanged at 1665 -- this step touches one acceptance script only.
3. Records: ledger entry and C80; CLAUDE.md's skip sentence; the guide's Phase 8 row.

## Two skips remain, both permanent

ANALYSIS_RESULT_UNSOUND (no real analysis can be made to lose rows on demand; P10-D36 made every
one report what it drops) and the rendered MCP schema (FastMCP builds it from the signature and
no script reads what a client displays). Phase 10 keeps its one, the non-finite screen. Three
skips in all, and now CLAUDE.md's count is one measured rather than carried over.
