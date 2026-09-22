# Cleanup Step 14a: one definition each of reference_checks and domain_checks

Closes the finding Cleanup Step 13 flagged and left: "validate/rules.py defines reference_checks
and domain_checks twice." Numbered 14a because Step 14's document already assigns "Step 15" to the
per-order effect size.

## What was established before this document

Read, not run:
- src/analytics_agent/validate/rules.py (904 lines) has `def reference_checks` at 475 and 645, and
  `def domain_checks` at 571 and 769. A module keeps the last binding of a name, so 645 and 769 are
  what `validate_dataset` calls; 475 and 571 are dead.
- The dead copies call `_table_columns` (lines 496, 505, 580). grep finds no definition of it
  anywhere in src/, so the dead copies would raise NameError if anything ever called them.
- tests/test_duckdb_validation_facts.py mentions `NOT IN` -- the likely pin for P7-D3.

## The fix

Delete lines 475-644 (the two dead copies and the blank lines after them), so the live
reference_checks directly follows row_count_check. Carry over the dead docstrings' sentences that the
live ones lack and that are still true:
- reference_checks, P7-D3: "so an orphan check written that way reports a clean pass over a table
  full of orphans" -- what NOT IN's zero rows means for this check. True if command 7's pinned fact
  holds.
- reference_checks, nulls: "Counting them together produces a number nobody can act on" -- why the
  live code keeps nulls and orphans apart, which it still does.
- domain_checks: "with different fixes" -- why absence and an outside value are separate findings.
  The dead copy's cross-reference ("for the reason the reference check counts them apart") is not
  carried: the live paragraph gives that reason in its own words.
No code in the live definitions changes. Command 9 checks that by comparing their syntax trees,
docstrings removed, before and after.

## Commands

1. Baseline: `uv run pytest -q | tail -1`. Expected `1925 passed`.
2. Line ranges from the parser, and which objects the module exports:
   `uv run python -c` with ast over rules.py, plus `co_firstlineno` of the imported functions.
   Expected: reference_checks 475-568, domain_checks 571-642, reference_checks 645-766,
   domain_checks 769-843; live first lines 645 and 769.
3. Diff each pair, bodies cut to scratchpad by those ranges. Expected: both diffs non-empty (exit 1).
   The differences I expect: the live reference_checks takes `loaded=`; check ids `reference.<cols>`
   and `value.<col>` (dead) against `reference.integrity[i]` and `value.domain[col]` (live); dead
   existence checks through `_table_columns`, live through `_column_type` and information_schema;
   dead domain_checks goes through the dict in its own order, live sorts it; the live domain subject
   wraps the set in braces; the docstrings differ.
4. `grep -rn "def _table_columns" src/` -- expected no output, exit 1.
   `grep -rn "_table_columns" src/` -- expected exactly the 3 lines above, all inside the dead range.
5. Nothing depends on the dead check-id forms:
   `grep -rnE '"(reference|value)\.[a-z_+]+"' src tests eval ui` -- expected no output.
   `grep -rlE 'reference\.integrity\[|value\.domain\[' src tests eval ui` -- expected at least one
   test file (the live forms are the ones that are pinned).
6. History:
   `git log -S"def domain_checks" --oneline -- src/analytics_agent/validate/rules.py` and the same
   for `def reference_checks`. Expected: 50bf16f only, for both.
   Occurrence counts at 50bf16f^ and 50bf16f (`git show <rev>:<path> | grep -c`). Expected 0 then 2
   for each name, since a single -S hit means the count changed once. (If rules.py does not exist at
   50bf16f^, the first `git show` fails with "exists on disk, but not in" -- the same finding.)
   `git log -S"_table_columns" --oneline -- src/` -- expected 50bf16f only: introduced as a call and
   never defined.
   `git show --stat 50bf16f`, and the step document that commit records, grepped for
   reference_checks. Expected: a Phase 7 validation commit.
7. P7-D3's fact is pinned: `grep -n "NOT IN" tests/test_duckdb_validation_facts.py`. Expected a test
   asserting that NOT IN returns zero rows when the parent column holds a NULL.
8. Apply with a guarded script (below) through `uv run python`. It asserts two of each definition at
   475/571/645/769, removes 475-644, replaces each of the three docstring passages after checking it
   matches exactly once, re-parses, and asserts one definition of each and no `_table_columns`.
   Expected `ok`. Then `shasum -a 256` and `wc -l`: expected 737 lines (904 - 170 + 3; each docstring
   passage gains one line).
9. The live definitions are unchanged: compare `ast.dump` of each function, docstring removed,
   between `git show HEAD:<path>` and the working tree. Expected `reference_checks identical`,
   `domain_checks identical`.
10. `uv run pytest -q`. Expected `1925 passed`.
11. `uv run python tests/test_phase8.py` .. `test_phase12.py`. Expected 99/0/2, 19/0/0, 35/0/1,
    26/0/0, 36/0/0.
12. `uv run python eval/run_eval.py`. Expected `SCORE: 76/76 (100%)`.
13. `uv run --group ui pytest ui/tests -q`. Expected `37 passed`.
14. Records: C103 and CL14a-D1 with MEASURED VALIDATION in docs/decisions.md; CLAUDE.md's "Cleanup
    Steps 4-14" and "at Cleanup Step 14" become 14a (same figures). The guide's ledger does not list
    cleanup steps and no phase changes state, so it stays as it is. Commit.

The script for command 8:

```python
import ast, pathlib
p = pathlib.Path("src/analytics_agent/validate/rules.py")
src = p.read_text()
starts = [(n.name, n.lineno) for n in ast.parse(src).body
          if isinstance(n, ast.FunctionDef) and n.name in ("reference_checks", "domain_checks")]
assert starts == [("reference_checks", 475), ("domain_checks", 571),
                  ("reference_checks", 645), ("domain_checks", 769)], starts
lines = src.splitlines(keepends=True)
assert lines[474].startswith("def reference_checks(con, dataset_name: str, foreign_keys)")
assert lines[644] == "def reference_checks(\n"
assert lines[642] == lines[643] == "\n"
src = "".join(lines[:474] + lines[644:])

edits = [
    ("    column holds a single NULL -- Step 1 measured it, and `region_lookup.csv`\n"
     "    carries a blank row so a regression here shows up as 7 orphans becoming 0\n"
     "    rather than as nothing at all.\n",
     "    column holds a single NULL, so an orphan check written that way reports a\n"
     "    clean pass over a table full of orphans. Step 1 measured it, and\n"
     "    `region_lookup.csv` carries a blank row so a regression here shows up as 7\n"
     "    orphans becoming 0 rather than as nothing at all.\n"),
    ("    at nothing on purpose, optional by design in most schemas. So a null is\n"
     "    `not_checked` -- it was never comparable -- and an orphan is `failed`.\n",
     "    at nothing on purpose, optional by design in most schemas. Counting them\n"
     "    together produces a number nobody can act on, so a null is `not_checked`\n"
     "    -- it was never comparable -- and an orphan is `failed`.\n"),
    ("    findings, and Step 1 measured that a `NOT IN` predicate reports only the\n"
     "    first: a NULL comparison is UNKNOWN, so nulls are invisible to it. They are\n"
     "    counted separately here, as `not_checked` -- a row with no value did not\n"
     "    break the vocabulary, it simply has nothing to check against it.\n",
     "    findings with different fixes, and Step 1 measured that a `NOT IN`\n"
     "    predicate reports only the first: a NULL comparison is UNKNOWN, so nulls\n"
     "    are invisible to it. They are counted separately here, as `not_checked` --\n"
     "    a row with no value did not break the vocabulary, it simply has nothing to\n"
     "    check against it.\n"),
]
for old, new in edits:
    assert src.count(old) == 1, old[:60]
    src = src.replace(old, new)

names = [n.name for n in ast.parse(src).body if isinstance(n, ast.FunctionDef)]
assert names.count("reference_checks") == 1 and names.count("domain_checks") == 1, names
assert "_table_columns" not in src
p.write_text(src)
print("ok")
```

## Results

1. As expected: `1925 passed in 62.83s (0:01:02)`.
2. As expected: `reference_checks 475 568`, `domain_checks 571 642`, `reference_checks 645 766`,
   `domain_checks 769 843`; `live 645 769`.
3. Both diffs non-empty, `exit 1` each, with every difference listed above. One more, which I did not
   predict: the dead reference_checks checks only that the parent has the referenced columns; the
   live one also checks that the child has its own key columns (`missing = [c for c in fk.columns if
   _column_type(con, dataset_name, c) is None]`). Excerpt (dead `<`, live `>`):
       < def reference_checks(con, dataset_name: str, foreign_keys) -> list[CheckResult]:
       > def reference_checks(
       >     con, dataset_name: str, foreign_keys, loaded: set[str] | None = None
       <         check_id = f"reference.{'+'.join(fk.columns)}"
       >         check_id = f"reference.integrity[{i}]"
       <         if not _table_columns(con, fk.references):
       >         if fk.references not in loaded:
       <     known = _table_columns(con, dataset_name)
       <     for column, allowed in (domains or {}).items():
       <         check_id = f"value.{column}"
       >     for column in sorted(domains):
       >         allowed = list(domains[column])
       >         check_id = f"value.domain[{column}]"
       <             subject=f"{column} in {', '.join(allowed)}",
       >             subject=f"{column} in {{{', '.join(allowed)}}}",
       <                 f"every row rather than testing anything",
       >                 f"every row rather than constrain any",
4. As expected. `def _table_columns`: no output, `exit 1`. `_table_columns`: exactly rules.py:496,
   :505, :580, all inside 475-642.
5. First grep as expected: no output, `exit 1`. The second prediction was WRONG: it printed only
   `src/analytics_agent/validate/rules.py`, with no test file.
   5.1. How the tests find these checks: `grep -rn "reference_checks\|domain_checks" tests src` shows
        tests/test_validate_rules.py:392-475 calling them directly and taking `[0]`, and
        validate/tools.py:176,179 as the only callers in src. No test names either check id. The
        tests reach the live copies because the name resolves to them, not because they pin the
        live id form. Noted here and not changed, since changing it is outside this step.
6. As expected. Both -S searches: `50bf16f Phase 7 Step 12: reference integrity and category
   domains`, and nothing else. Counts: `50bf16f^ reference_checks 0`, `50bf16f^ domain_checks 0`,
   `50bf16f reference_checks 2`, `50bf16f domain_checks 2`. `_table_columns`: 50bf16f only.
   `git show --stat 50bf16f` (08/09/2026): rules.py `372 ++++`, tests/test_validate_rules.py
   `113 +++`, decisions.md `33 +++`, no commit body.
   6.1. That commit's rules.py diff is a single hunk, `@@ -472,12 +472,384 @@ def row_count_check(`:
        the two pairs went in together, contiguous, the dead pair first. There is no step document to
        read: `ls docs/steps | grep -i phase7` prints nothing. Phase 7's steps predate the practice.
        The decisions.md section the commit added describes the live pair, not the dead one. It
        quotes "the contract is not wrong; the workspace is thin" (dead: "..., the workspace is
        thin") and "which would fail every row rather than constrain any" (dead: "rather than testing
        anything"), and names the far-side column check that only the live copy makes. It also says
        "Drafted before the implementation and rediscovered by running them" about the tests' wording.
        No later commit touched either definition: `git log 50bf16f..HEAD -- rules.py` shows only
        78dc834, which added expectation_checks after them.
7. As expected. tests/test_duckdb_validation_facts.py:50 `test_not_in_is_blind_to_a_null_in_the_parent`
   asserts `NOT IN` finds `0` and `NOT EXISTS` finds `2`. Its docstring gives the consequence in
   almost the same words: "an orphan check reports a clean pass on a table full of orphans". The
   carried-over sentence is a fact pinned in the suite.
8. As expected. Run as `awk` over this document's python block into the scratchpad (45 lines), then
   `uv run python`, so the script that ran is the one above. Printed `ok`.
       26d9e3abd57f9caf2f2f732cea7cf64ada78c14e81d8fd2cbdd44a02c9efe41d  src/analytics_agent/validate/rules.py
       737 src/analytics_agent/validate/rules.py
   `git diff --stat`: `1 file changed, 12 insertions(+), 179 deletions(-)` (904 - 167 = 737).
   Checked by eye in `git diff`: the three docstring passages read as planned. awk found no line over
   105 characters.
9. As expected: `reference_checks identical`, `domain_checks identical`. The comparison takes the
   last definition of each name at HEAD, as Python binds it, and the only one in the working tree.
10. As expected: `1925 passed in 32.42s`.
11. As expected: `99 passed, 0 failed, 2 skipped`, `19 passed, 0 failed, 0 skipped`, `35 passed, 0
    failed, 1 skipped`, `26 passed, 0 failed, 0 skipped`, `36 passed, 0 failed, 0 skipped`. (The
    `exit 0` lines my loop printed after each script are the status of `tail`, not the script's.
    The totals are the result.)
12. As expected: `SCORE: 76/76 (100%)`.
13. As expected: `37 passed in 10.00s`.
14. Records written as planned: C103 and CL14a-D1 in docs/decisions.md, CLAUDE.md's two "Cleanup
    Step 14" references moved to 14a. Also recorded there, not changed: no test names a reference or
    domain check id (5.1). And C73, which CLAUDE.md cites, and C74 are recorded nowhere in docs/.
    `grep -c` finds 0 of each in decisions.md and no step document names them; I found this while
    looking up C73 to cite it.

MEASURED VALIDATION line and digests: docs/decisions.md, section Cleanup Step 14a.
