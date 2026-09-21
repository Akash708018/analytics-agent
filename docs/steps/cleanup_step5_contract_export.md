# Cleanup Step 5: contract exports anchored to the repository and kept apart per workspace

Decided with the user on 21/09/2026, before Phase 14: namespace per workspace.

## The defect

`contract/store.py:57` sets `EXPORT_DIR = Path("docs/contracts")`, relative to the working
directory, and every workspace exports `<dataset>.yaml` into it. Two consequences:

1. The export lands wherever the process was started. Claude Desktop launches the server with
   `uv --directory <repo>`, so today it is the repository -- by the launcher's choice, not the
   code's. config.py:74 already records why a path must never come from the working directory
   and derives PROJECT_ROOT from `__file__`; EXPORT_DIR is the one path that does not.
2. Two workspaces confirming a contract for a dataset of the same name overwrite one another's
   export. Track A has one workspace and never sees it; Track B has one per session and would.
   F2's reasoning (guide line 795: isolate now, not in Phase 14) applies to this file too.

## The fix

1. `EXPORT_DIR = PROJECT_ROOT / "docs" / "contracts"`.
2. `contract_tools.confirm` takes `workspace_id`. With no explicit `export_root`, the default
   workspace exports to `EXPORT_DIR/<dataset>.yaml`, as today, and any other workspace to
   `EXPORT_DIR/<workspace_id>/<dataset>.yaml`. An explicit `export_root` is used exactly as
   given -- the tests that pass one are asserting where a file lands.
3. server.confirm_dataset_contract passes the resolved workspace id, and its docstring says
   where the copy goes.
4. The eval and the acceptance scripts redirect `store.EXPORT_DIR` into their own workspace
   (P13-O2) and call with non-default workspace ids, so their exports move one directory down,
   still inside their own workspace. Nothing outside is written; the tree stays clean.

## Commands and outputs

1. Falsify: add four tests to tests/test_contract_tools.py -- EXPORT_DIR is absolute and under
   PROJECT_ROOT; the default workspace exports flat; another workspace exports under its id;
   two workspaces with one dataset name do not overwrite each other. Run them on the unfixed
   tree. Expected: 4 failed (the first on the relative path, the other three on the unexpected
   keyword `workspace_id`).
2. Apply the fix. Expected: pytest 1762 -> 1766 passed.
3. Acceptance scripts. Expected unchanged: 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; tree clean.
4. Eval. Expected: SCORE 76/76; tree clean.
5. Records: C94 and CL5-D1 in decisions.md; CLAUDE.md tallies. Commit and push.

## Results

1. Falsify: `4 failed, 27 passed`. As expected.
2. Fix: `1766 passed`. As expected. One slip caught before running: the first draft named the
   helper `export_root`, the same as confirm's parameter, and called a third name at the call
   site; renamed to `workspace_export_root` before any test ran.
3. Acceptance: 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0. Unchanged; tree clean.
4. Eval: `SCORE: 76/76 (100%)`. Tree clean; docs/contracts holds clean_sales.yaml only.
5. Records: C94, CL5-D1.
