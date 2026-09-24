# Phase 14 Step 10: behaviour under test -- lifecycles, hostile input, every tool fuzzed

Opened 24/09/2026. Asked for: "a master tester and planner: first build the test cases and
execute; from the setbacks research and plan the fixes; then fix."

The stress rounds (Steps 6-8) fed the engine bad DATA and walked the happy path once. What no
round has touched is BEHAVIOUR: what a person or an agent does to a workspace over time, and what
a hostile or careless caller sends.

## The matrix (scripts/scenario_matrix.py)

Each check states its expectation in code; outcomes are CRASH (an exception escaped), WRONG (the
expectation failed), OK. Four families:

- L (lifecycle, web backend): re-uploading a file whose dataset has a contract, with the same
  and with a different structure; cleaning after the contract (a type change is structural
  drift); two datasets in one workspace; reset in the middle; Explore on the dataset without a
  contract; the sidebar stage after each.
- H (hostile input, web backend): tampered ingest specs (a path into another workspace, a column
  renamed to an injection string, a duplicate or empty name, a forced type that cannot hold the
  data); read_artifact traversal; analysis params carrying SQL, absurd numbers and wrong names;
  a report question carrying markup; corrupt and mislabelled files; odd file names; invalid
  workspace ids.
- T (MCP tools, server.py): every tool called with missing, wrong-typed and absurd arguments must
  answer with text -- a result or a refusal -- and never raise.
- C (concurrency): two workspaces loading and analysing on threads; one workspace hammered by
  parallel reads while a load runs.

Expected, stated before the first run: some tampered specs and absurd params raise instead of
refusing (the web layer was tested on honest input); drift after cleaning is caught (the engine
has a fingerprint); MCP tools with wrong types raise TypeError somewhere.

## Commands

1. Build the matrix; run it. 2. Triage every non-OK. 3. Research causes; the plan below the
results, before any fix. 4. Fix with a test each; re-run the matrix to zero; all checks; commit.

## Results

### 1. Built and run -- 30 checks

    30 checks: CRASH 3, WRONG 4, OK 23

Predictions: tampered specs and absurd params raise -- half right (unknown params raise; every
tampered spec was refused cleanly); drift after cleaning is caught -- right (CONTRACT_STALE,
"contract v1, BLOCKED", and for a different file re-uploaded under the same name too); MCP
wrong types raise TypeError -- WRONG: FastMCP validates first and answers with its own
ValidationError, the tool never runs.

### 2. Triage

Harness errors (expectation wrong, corrected in the matrix with the reason written there):
top_n with n=10**12 returns every group (5); pareto threshold=7 is read as 7% and says so;
FastMCP's schema check raises fastmcp.exceptions.ValidationError (measured), a clean error
result for the client.

A check that passed and should not have: "a confirmed contract survives a re-draft" accepted any
draft. Tightened to what the Contract screen needs, it fails (S1).

Bugs, with reproductions in the matrix:

| # | Check | What happens |
|---|---|---|
| S1 | a confirmed contract re-drafts as itself | draft_contract with no answers -- what the Contract screen asks in a fresh session, i.e. after any page reload -- ignores the stored contract: the form comes back blank, PROVISIONAL, "Still needed: Grain ..." under a contract that is in force |
| S2 | unknown parameters are refusals | run_analysis(..., {"colour": "red"}) raises TypeError out of RealBackend (server.compute_analysis's signature rejects it before the engine can) |
| S3 | markup in the report question | the question is written into the report verbatim: `<script>`, `onerror=`, `](javascript:` survive into the .md a person downloads and opens elsewhere |
| S4 | a corrupt .xlsx / a CSV renamed .xlsx | BadZipFile raised from excel.list_sheets through RealBackend.draft_ingest: the Upload screen crashes (the MCP path already refuses) |
| S5 | every tool answers hostile strings | check_file and preview_file raise OSError on a 5,000-character path; read_result_file raises ValueError on a NUL byte |

### 3. Research and plan

- S1. RealBackend.draft_contract passes the answers straight to propose_contract, and with none
  the proposal is built from the evidence alone. Fix: when no answer is given and a contract is
  in force, draft from the stored contract's own fields (grain, key, date, measures with their
  agg and definition, dimensions, window, caveats) and say "contract vN is in force". If that
  draft is refused -- the table has drifted so the stored names no longer fit -- fall back to the
  evidence-only draft, as today.
- S2. The backend is the boundary: check the parameter names against compute_analysis's own
  signature before calling, and return ANALYSIS_PARAMS_INVALID naming the accepted ones.
- S3. Neutralise at the one place the report is written (assemble, before write_text): a `<`
  that opens a tag (followed by a letter, `/`, `!` or `?`) becomes `&lt;`, and a markdown link
  target starting `javascript:` loses its scheme. The question keeps its words -- the report's
  own rule is "do not paraphrase the user" -- only its power to execute goes. Column names and
  values from a hostile file pass the same filter.
- S4. draft_for_path: an Excel branch that meets BadZipFile / InvalidFileException / KeyError /
  OSError raises LoadRefused ("not a readable .xlsx workbook"), and RealBackend.draft_ingest
  turns any other exception into a refusal too, so no file can crash the Upload screen.
- S5. A path guard at the top of every MCP tool that takes a path (check_file, preview_file,
  propose_ingest_spec, load_csv, load_excel, read_result_file): NUL bytes and OS-rejected names
  answer "BLOCKED: that is not a usable path" with a NEXT STEP.

### 4. Fixes, each with a test (tests/test_scenarios.py, 10; a UI test for S1)

S1 RealBackend._draft_in_force: no answers and a contract in force -> the draft is the stored
contract's own fields, "Contract vN is in force, as shown"; after drift or with no contract, the
evidence-only draft as before. S2 parameter names checked against compute_analysis's signature at
the boundary. S3 report/assemble.defang at the one write: tag-opening '<' -> '&lt;', javascript:
links lose the scheme; ordinary markdown, "p < 0.05" and blockquotes unchanged (tested). S4
draft_for_path refuses a non-workbook; RealBackend.draft_ingest turns any exception into a
refusal. S5 server._unusable_path at the top of the six path-taking tools.

The first re-run held one WRONG: the markup check flagged "onerror=" as text behind an escaped
'<' -- my check, too literal; it now looks for tags that can open. Re-run:

    30 checks: CRASH 0, WRONG 0, OK 30

### 5. Checks

    1910 passed in 110.56s (0:01:50)
    50 passed in 13.74s
    phase6: 36/0/0  phase8: 55/0/3  phase9: 0/0/1  phase10: 0/0/1  phase11: 26/0/0  phase12: 36/0/0
    SCORE: 76/76 (100%)
    stress rounds 1-4: identical to Step 8 (CRASH 0; WRONG 10/3/8/0, all load-time)
    browser walk: 11 screens, 0 exception boxes, 0 findings
