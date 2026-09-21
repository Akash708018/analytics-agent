# Phase 14 Step 1: Track B ground facts -- concurrency, locks, and the HTTP session id

Guide Phase 14, item 2: "Verify with two concurrent browser sessions before anything else."
Before a session can be verified, what DuckDB and FastMCP do under concurrency has to be known
rather than assumed -- the convention every phase has opened with. This step builds nothing in
src/; it writes tests/test_track_b_facts.py and records what it finds.

## Why these facts

- Streamlit serves every browser session as a thread in one process. A backend imported by the
  UI therefore runs one thread per user, all in one process.
- `db.connect(workspace_id)` opens a fresh `duckdb.connect(path)` on every call and the caller
  closes it (util/db.py:118). Nothing holds a handle between calls.
- `db.connect_read_only` ATTACHes the same file READ_ONLY from an in-memory database, and its
  docstring says never to have it and `connect()` open at once in one process.
- Claude Desktop's Track A server is a separate process on workspace "local". A Track B process
  on the same machine would be a second process.
- FastMCP documents `Context.session_id` as "the session ID for StreamableHTTP transports". The
  guide's "real per-user session ID" has to come from somewhere; whether this is it is unknown.

## Predictions, committed before running

F1. Same process, two `duckdb.connect(path)` on one file, both open: both work and each sees the
    other's committed writes (DuckDB shares one database instance per file per process).
F2. Same process, `connect()` open and `connect_read_only()` on the same workspace: raises.
F3. A second process connecting to a file the first holds open: raises IOException containing
    "Could not set lock on file". This is F2 of the Failure Mode Register.
F4. The same second process after the first closes its connection: connects.
F5. Two threads, two workspaces, each 25 rounds of CREATE OR REPLACE + count through
    `db.connect`, started together: no error; each sees only its own table.
F6. One workspace, two connections, each in an explicit transaction replacing the same table,
    committed in turn: the second commit raises a transaction conflict. (Sequenced by hand so
    the fact is deterministic, not a race that sometimes happens.)
F7. FastMCP over Streamable HTTP: two clients get two different `ctx.session_id` values; one
    client calling twice gets the same one both times.

## Commands and outputs

1. Write tests/test_track_b_facts.py, one test per fact, each asserting the prediction above.
   Run it. Expected: 7 passed. Any failure is a finding, recorded here as the real behaviour.
2. Full suite 1781 -> 1788; acceptance and eval unchanged (nothing in src/ changes).
3. Record P14-D1.. with each fact's measured outcome; commit and push.

## Results

1. First run: 5 passed, 1 failed -- F7, a NameError on `Context`: the test imported it inside
   the function and FastMCP resolves string annotations at module scope. 1.1: import moved to
   module scope. Second run: F7 passed (two distinct stable 32-hex ids); F6 failed on my
   placeholder line querying the aborted connection. 1.2: probe separating every statement --
   the second writer's CREATE raises "write-write conflict", that transaction is aborted until
   ROLLBACK, the first COMMITs and its value stands. F6 rewritten to assert exactly that.
   Then `6 passed` three times running. 6 tests, not 7: F3 and F4 are one sequence.
   Predictions: F1-F5 and F7 held; F6 was wrong (raised at the write, not the commit).
2. `1787 passed`; acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76; tree clean.
3. Recorded P14-D1 to D8.
