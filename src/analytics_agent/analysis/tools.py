"""The layer the analysis MCP tool calls. Strings in, strings out.

Everything below this returns objects and raises exceptions; everything above
is FastMCP, where a raised exception becomes a traceback and a traceback is not
an instruction. The agent reads it, learns nothing actionable, and retries the
same call. So this is where `ContractRefused`, `UnknownAnalysis` and the
`ValueError`s nine analyses raise stop being exceptions and become text with a
reason code and a next call in it. That is `profile/tools.py`'s shape, for
`profile/tools.py`'s reason.

**The Scope is built here, once, and handed in.** Every analysis takes a scope
its caller built and none of them rebuilds one -- an analysis that computed its
own would be free to disagree with the method note printed above its own table.
This is that caller.

**Four reason codes, because they have four recoveries.** The eval counts
recovery per reason, so a single ANALYSIS_FAILED would average a name the agent
can fix by reading a list against a contract the user has to re-confirm.
NOT_FOUND is answered by the catalogue, PARAMS_INVALID by fixing the call,
NOT_POSSIBLE usually by the contract, and RESULT_UNSOUND by nobody -- it means
the arithmetic disagreed with the scope and is our defect, not a call to fix.

**The method note is verified, not trusted.** All nine analyses put
`scope.method_note()` first in `summary`, and nothing enforced it. A result
whose first line is not the note is a result that may have been computed over
rows it did not describe, so it is refused as UNSOUND rather than written.
"""

from __future__ import annotations

import re

from analytics_agent.contract import ContractRefused
from analytics_agent.contract.refusals import Reason, Refusal
from analytics_agent.state import require_contract
from analytics_agent.util import results
from analytics_agent.util.sql_guard import UnsafeSQL

from .base import LostRows, ParamsInvalid, ScopeError, scope_for
from . import runs
from .registry import UnknownAnalysis, catalogue, get


def _catalogue_text() -> str:
    """Every analysis, by tier then name, as one line each."""
    return "; ".join(f"{name} (tier {tier})" for name, tier, _ in catalogue())


def _example_call(dataset_name: str) -> str:
    """A call that works, with arguments filled in.

    8.2: a refusal names the exact call, not an intention. summary_stats is the
    one analysis that takes no parameters beyond the dataset, so it is the one
    that can be offered without guessing which column the caller meant.
    """
    return (
        f'compute_analysis(dataset_name="{dataset_name}", '
        f'analysis_type="summary_stats")'
    )


# Python's TypeError for a missing or unexpected keyword, which used to be the whole WHY:
# "top_n() missing 1 required positional argument: 'measure'" (P14-O12, B13).
_MISSING_ARGS = re.compile(r"missing \d+ required (?:positional |keyword-only )?arguments?: (.+)$")
_UNEXPECTED_ARG = re.compile(r"unexpected keyword argument '(\w+)'")
# What each argument names, so the example can be filled from the contract.
_MEASURE_ARGS = ("measure", "against")
_DIMENSION_ARGS = ("dimension", "rows", "columns", "column", "second_dimension", "entity")
_PLACEHOLDER = {"period": "YYYY-MM", "baseline": "YYYY-MM", "before_start": "YYYY-MM-DD",
                "before_end": "YYYY-MM-DD", "after_start": "YYYY-MM-DD", "after_end": "YYYY-MM-DD"}


def _params_refusal(analysis_type: str, dataset_name: str, exc: Exception, gate) -> Refusal:
    """A wrong argument set, in the engine's words, with a call that names declared columns."""
    text = str(exc)
    measures = [m.name for m in gate.contract.measures]
    dims = list(gate.contract.dimensions)
    declared = (f"declared measures: {', '.join(measures) or '(none)'}; declared "
                f"dimensions: {', '.join(dims) or '(none)'}")
    missing = _MISSING_ARGS.search(text)
    unexpected = _UNEXPECTED_ARG.search(text)
    if missing:
        names = re.findall(r"'(\w+)'", missing.group(1))
        why = (f"{analysis_type} needs {', '.join(names)}, and "
               f"{'it was' if len(names) == 1 else 'they were'} not given.")
        short = ([n for n in names if n in _MEASURE_ARGS and not measures]
                 + [n for n in names if n in _DIMENSION_ARGS and not dims])
        if short:
            why += (f" The contract declares no "
                    f"{'measure' if short[0] in _MEASURE_ARGS else 'dimension'} to pass as "
                    f"{short[0]}, so the contract is what has to change.")
            return Refusal(
                reason=Reason.ANALYSIS_PARAMS_INVALID,
                what=f"{analysis_type} was called without {', '.join(names)}.",
                why=why, state=declared,
                next_call=f'propose_dataset_contract(dataset_name="{dataset_name}")')
        pool = {"measure": iter(measures), "dimension": iter(dims)}
        args = []
        for n in names:
            kind = "measure" if n in _MEASURE_ARGS else "dimension" if n in _DIMENSION_ARGS else None
            value = next(pool[kind], None) if kind else _PLACEHOLDER.get(n)
            args.append(f'{n}="{value or "..."}"')
        return Refusal(
            reason=Reason.ANALYSIS_PARAMS_INVALID,
            what=f"{analysis_type} was called without {', '.join(names)}.",
            why=why, state=declared,
            next_call=(f'compute_analysis(dataset_name="{dataset_name}", '
                       f'analysis_type="{analysis_type}", {", ".join(args)})'))
    if unexpected:
        why = (f"{analysis_type} does not take {unexpected.group(1)}. "
               f"{get(analysis_type).summary}")
    else:
        why = text
    return Refusal(
        reason=Reason.ANALYSIS_PARAMS_INVALID,
        what=f"{analysis_type} was called with arguments it cannot take.",
        why=why,
        state=f"{analysis_type}: {get(analysis_type).summary}",
        next_call=_example_call(dataset_name),
    )


class _Refused(Exception):
    """A refusal already rendered, carried out of the shared path.

    compute_analysis and render_chart share every step up to the Output -- the
    gate, the lookup, the scope, the run, and the check that the result says
    what it was computed over -- and each of those steps has its own refusal
    text. Two copies of that ladder is two copies of one ruling, which P9-O6
    records drifting apart, so the ladder lives once and raises what it would
    otherwise have returned.
    """

    def __init__(self, text: str):
        self.text = text
        super().__init__(text)


def _as_call(tool: str, dataset_name: str, analysis_type: str, params: dict) -> str:
    """A call a caller can retype, with the arguments that were actually used.

    The same shape analysis/runs.AnalysisRun.call() renders for the reproduction appendix, and
    for the same reason: a call naming only the analysis is one that fails the moment the
    analysis takes a parameter.
    """
    from .runs import _literal

    parts = [f'dataset_name="{dataset_name}"', f'analysis_type="{analysis_type}"']
    parts += [f"{k}={_literal(v)}" for k in sorted(params) for v in (params[k],)]
    return f"{tool}({', '.join(parts)})"


def _produce(con, dataset_name: str, analysis_type: str, params: dict):
    """Gate, look up, scope, run, and check the result describes itself.

    Returns `(gate, output, params)` -- the parameters as stripped, because those are what was
    actually passed to the analysis and what analysis/runs.py has to store for the reproduction
    appendix to render a call rather than guess one.

    Raises `_Refused` carrying the rendered refusal, which is the only shape this package
    produces for a caller.
    """
    try:
        gate = require_contract(con, dataset_name)
    except ContractRefused as exc:
        raise _Refused(str(exc)) from None

    # The MCP wrapper declares every parameter any analysis takes, because
    # FastMCP builds the JSON schema from the signature and **params exposes
    # nothing -- the agent would see a tool it cannot pass a column to. So it
    # passes all of them and the ones nobody gave arrive as None. Dropping
    # them here rather than there keeps server.py's rule that a tool calls one
    # function and returns what it gets back, and lets each analysis apply its
    # own default instead of a second copy of that default living upstream.
    params = {k: v for k, v in params.items() if v is not None}

    try:
        analysis = get(analysis_type)
    except UnknownAnalysis as exc:
        raise _Refused(Refusal(
            reason=Reason.ANALYSIS_NOT_FOUND,
            what=str(exc),
            why=(
                "an analysis is looked up by name, and a name nobody "
                "registered cannot be guessed at -- running something adjacent "
                "would answer a question that was not asked."
            ),
            state=f"available: {_catalogue_text()}",
            next_call=_example_call(dataset_name),
        ).to_text()) from None

    try:
        scope = scope_for(con, gate)
        output = analysis.run(con, gate, scope, **params)
    except LostRows as exc:
        raise _Refused(_unsound(dataset_name, str(exc))) from None
    except ScopeError as exc:
        raise _Refused(Refusal(
            reason=Reason.ANALYSIS_NOT_POSSIBLE,
            what=f"the rows {analysis_type} would run over cannot be selected.",
            why=str(exc),
            state=f"contract v{gate.version} for {dataset_name}",
            next_call=f'validate_dataset(dataset_name="{dataset_name}")',
        ).to_text()) from None
    except UnsafeSQL as exc:
        raise _Refused(Refusal(
            reason=Reason.ANALYSIS_NOT_POSSIBLE,
            what=f"{analysis_type} could not be run against {dataset_name}.",
            why=str(exc),
            state=f"contract v{gate.version} for {dataset_name}",
            next_call=f'propose_dataset_contract(dataset_name="{dataset_name}")',
        ).to_text()) from None
    except (TypeError, ParamsInvalid) as exc:
        raise _Refused(_params_refusal(analysis_type, dataset_name, exc, gate).to_text()) from None
    except ValueError as exc:
        raise _Refused(Refusal(
            reason=Reason.ANALYSIS_NOT_POSSIBLE,
            what=f"{analysis_type} cannot answer that under this contract.",
            why=str(exc),
            state=f"contract v{gate.version} for {dataset_name}",
            next_call=f'propose_dataset_contract(dataset_name="{dataset_name}")',
        ).to_text()) from None

    note = scope.method_note()
    if not output.summary or output.summary[0] != note:
        raise _Refused(_unsound(
            dataset_name,
            f"{analysis_type} returned a result whose first summary line is "
            f"not the method note for the scope it was given. Nothing says "
            f"what these numbers were computed over.",
        ))
    return gate, output, params


def compute_analysis(
    con,
    workspace_id: str,
    dataset_name: str,
    analysis_type: str,
    **params,
) -> str:
    """Run one analysis under the contract in force, and write what it found.

    Returns the contract header and the result envelope, or a refusal. Never a
    path on its own: `write_result` returns a `Result` and the envelope is not
    optional, which is locked decision 20.
    """
    try:
        gate, output, used = _produce(con, dataset_name, analysis_type, params)
    except _Refused as exc:
        return exc.text

    result = results.write_result(
        workspace_id,
        label=output.label,
        headers=output.headers,
        rows=output.rows,
        summary=output.summary,
        dataset_name=dataset_name,
    )
    # Recorded after the result exists, so a refused call records nothing. P12-D3 measured what
    # the file keeps -- its table, and nothing about the call that made it.
    runs.record(
        con,
        dataset_name=dataset_name,
        analysis_type=analysis_type,
        params=used,
        contract_version=getattr(gate, "version", None),
        row_count=result.row_count,
        result_path=str(result.path),
        summary=output.summary,
    )
    return f"{gate.header()}\n\n{result.to_text()}"


def render_chart(
    con,
    workspace_id: str,
    dataset_name: str,
    analysis_type: str,
    chart: str,
    x: str | None = None,
    y: str | None = None,
    title: str | None = None,
    **params,
) -> str:
    """Run one analysis and draw it, under the same contract and the same gate.

    A chart is a claim about data, so it goes through the gate a table goes
    through -- `_produce` is the same ladder `compute_analysis` climbs, and a
    dataset with no confirmed contract is refused here for the same reason and
    in the same words.

    Returns the contract header and the chart envelope, or a refusal. Never a
    path on its own: Rule 4 exists because a PNG is the one artifact in this
    engine a caller literally cannot read back.
    """
    # Imported here rather than at module scope so that importing the analysis
    # package does not import matplotlib, and through it numpy. Twenty-two
    # analysis modules and their tests import this package; none of them draws.
    from ..charts.render import ChartRefused, render

    try:
        gate, output, used = _produce(con, dataset_name, analysis_type, params)
    except _Refused as exc:
        return exc.text

    try:
        drawn = render(
            workspace_id,
            kind=chart,
            output=output,
            label=output.label,
            dataset_name=dataset_name,
            x=x,
            y=[y] if y else None,
            title=title,
        )
    except ChartRefused as exc:
        detail = (
            "The numbers are not in question -- the analysis ran. This is "
            "about the shape a chart needs, which is not the shape this "
            "result has. Nothing was written."
        )
        if exc.choices:
            # The recovery draws the chart. compute_analysis succeeded here too and handed a
            # table to a caller who asked for a chart, so B11's retry passed against a call
            # that did not recover (C93). Naming y in the call is not the renderer picking
            # (P11-D13): the choice is in plain sight beside the full list, and the caller
            # makes it by making the call.
            pick = _suggested_y(exc.choices, used.get("measure"))
            drawn_with = dict(used, chart=chart, y=pick)
            drawn_with.update({k: v for k, v in (("x", x), ("title", title)) if v is not None})
            detail += (
                f" The call below draws {pick!r}; any of "
                f"{', '.join(repr(c) for c in exc.choices)} works as y instead."
            )
            next_call = _as_call("render_chart", dataset_name, analysis_type, drawn_with)
        else:
            # No y fixes this shape, so the table is the recovery. The parameters the analysis
            # was given, not just its name: without them this named a call that fails for
            # every analysis that takes one -- a refusal whose recovery is itself refused is
            # worse than no recovery at all. Found by gold question B09 on 21/09/2026.
            next_call = _as_call("compute_analysis", dataset_name, analysis_type, used)
        return Refusal(
            reason=Reason.ANALYSIS_NOT_POSSIBLE,
            what=f"{analysis_type} was computed and cannot be drawn as a {chart!r} chart.",
            why=str(exc),
            detail=detail,
            state=f"contract v{gate.version} for {dataset_name}",
            next_call=next_call,
        ).to_text()

    # x, y and title are stored beside the analysis parameters because call() has to render an
    # invocation somebody can retype, and a chart drawn with y="rows" is not the same chart
    # without it.
    drawn_with = dict(used)
    drawn_with.update({k: v for k, v in (("x", x), ("y", y), ("title", title)) if v is not None})
    runs.record(
        con,
        dataset_name=dataset_name,
        analysis_type=analysis_type,
        params=drawn_with,
        contract_version=getattr(gate, "version", None),
        row_count=drawn.drawn_count,
        chart_kind=chart,
        chart_path=str(drawn.path),
        summary=output.summary,
    )
    return f"{gate.header()}\n\n{drawn.to_text()}"


def _suggested_y(choices: tuple[str, ...], measure: str | None) -> str:
    """The measure a recovery names as y: the first carrying the analysis's own measure in its
    name -- trend's 'revenue (sum)' over its 'rows' -- else the first offered."""
    if measure:
        for choice in choices:
            if measure in choice:
                return choice
    return choices[0]


def _unsound(dataset_name: str, why: str) -> str:
    """The one refusal that is not the caller's fault, and says so."""
    return Refusal(
        reason=Reason.ANALYSIS_RESULT_UNSOUND,
        what="the analysis produced a result that does not describe itself.",
        why=why,
        detail=(
            "Nothing was written. A result that cannot account for its own "
            "rows is worse than no result, because it reads like one."
        ),
        state=f"dataset: {dataset_name}",
        next_call=f'validate_dataset(dataset_name="{dataset_name}")',
    ).to_text()


__all__ = ["compute_analysis", "render_chart"]
