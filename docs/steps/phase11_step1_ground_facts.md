# Phase 11 Step 1 - matplotlib ground facts

21/09/2026. Baseline 58996e5. Measured before starting: `uv run pytest -q` 1665 passed;
test_phase8.py 99/0/2; test_phase9.py 19/0/0; test_phase10.py 35/0/1.

## What the guide asks for

Guide line 943: `uv add matplotlib`, PNG into the workspace, and eight kinds -- line, bar,
grouped bar, scatter, histogram, box, heatmap, waterfall (the last for `mix_shift`). Per Rule 4
(guide line 563) `render_chart` returns the path **plus a text description and key values**,
because the agent cannot see the PNG. The stated trap: set the backend to `Agg` explicitly, or a
GUI backend can hang the server on macOS.

## The constraint that shapes this phase

matplotlib depends on numpy, and this project does not import numpy in `src/` or `tests/`. The
ban is on our imports, not on a library's internals, so matplotlib is a legitimate direct
dependency and every value handed to it must be a plain Python list. That is also what the
engine produces: an analysis returns `Output(headers, rows, summary, label)` and the rows are
lists of scalars read with `fetchall`. So the facts below are measured on lists, exactly as
tests/test_stats_facts.py measured scipy on lists, and for the same reason -- testing a calling
convention this engine does not use would measure nothing.

## Predictions, before running

Written down so the run is a measurement rather than a transcript.

1. `uv add matplotlib` installs 3.10.x and pulls no new top-level dependency beyond matplotlib's
   own (numpy is already present via statsmodels).
2. After `matplotlib.use("Agg")`, `get_backend()` returns `"agg"` lowercase -- newer matplotlib
   normalises the case.
3. `savefig` writes a file beginning with the PNG magic bytes `\x89PNG\r\n\x1a\n`.
4. Plain Python lists plot without conversion, for every one of the eight kinds.
5. A `None` inside a line series produces a gap rather than an exception; a `None` inside a bar
   series raises.
6. Strings on the x axis are treated as categories, in the order given rather than sorted.
7. Figures accumulate until closed: `plt.get_fignums()` grows, and this is the leak that matters
   in a long-running MCP server.
8. Two saves of identical data produce byte-identical PNGs -- matplotlib writes no timestamp by
   default.

Predictions 5, 7 and 8 are the ones I would bet least on, and they are the ones that change the
design: 5 decides whether the chart layer screens nulls or matplotlib does, 7 decides whether
every render is wrapped in a close, and 8 decides whether a test can assert on a digest.

## Commands

1. `uv add matplotlib`, then record version and what the lock gained.
2. Write `tests/test_matplotlib_facts.py` measuring the eight predictions. Assert the structural
   claims, print the version-dependent ones, and say in the file which is which.
3. Run it with `-s` and read every printed line.
4. Record the measurements in docs/decisions.md as P11-D1 onward, with the printed values.

## Outputs

**1. `uv add matplotlib`.** matplotlib 3.11.2, plus contourpy 1.4.0, cycler 0.12.1, fonttools
4.65.0, kiwisolver 1.5.1, pillow 12.3.0, pyparsing 3.3.3. numpy 2.5.3 already present.
**Prediction 1 was wrong twice**: the version is 3.11.2 not 3.10.x, and seven packages arrived
rather than the one the wording implied.

**2-3. tests/test_matplotlib_facts.py, 7 passed.** Printed:

    matplotlib.__version__            3.11.2
    get_backend()                     'Agg'
    GUI toolkits imported             none
    first 8 bytes                     b'\x89PNG\r\n\x1a\n'
    file size (bytes)                 21677
    line / bar / grouped_bar          23111 / 6007 / 6074
    scatter / histogram / box         12396 / 12090 / 5865
    heatmap / waterfall               9224 / 9168
    plot() with a None                drew, a gap where the None was
    bar() with a None                 TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'
    x tick labels as drawn            ['south', 'north', 'east', 'west']
    fignums before / during / after    0 / 3 / 0
    two saves byte-identical          True
    sizes                             21677 / 21677

**Predictions 2 through 8, scored.** 2 wrong in its detail: `get_backend()` returns `'Agg'`
capitalised, not lowercase, so an equality test against "agg" would fail on a correctly
configured server. 3, 4, 5, 6, 7 and 8 all held. The three I said I would bet least on -- the
None behaviour, the figure leak, and byte-determinism -- were the three that came out exactly as
predicted, and the one that caught me was the trivial one.

**What each fact decides.** D4 puts null screening in the chart layer, because matplotlib's
TypeError names no column and a caller cannot act on it. D6 puts every render in a
try/finally that closes its figure. D7 means a chart can be asserted by digest rather than only
by shape, which is what makes Step 2 testable.

**4. Recorded** as P11-D1 to P11-D7 in docs/decisions.md. Full suite 1665 -> 1672; acceptance
unchanged at 99/0/2, 19/0/0, 35/0/1.
