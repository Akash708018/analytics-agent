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

from analytics_agent.contract import ContractRefused
from analytics_agent.contract.refusals import Reason, Refusal
from analytics_agent.state import require_contract
from analytics_agent.util import results
from analytics_agent.util.sql_guard import UnsafeSQL

from .base import LostRows, ParamsInvalid, ScopeError, scope_for
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
        gate = require_contract(con, dataset_name)
    except ContractRefused as exc:
        return str(exc)

    # The MCP wrapper declares every parameter any of the twenty-one takes,
    # because FastMCP builds the JSON schema from the signature and
    # **params exposes nothing -- the agent would see a tool it cannot pass
    # a column to. So it passes all of them and the ones nobody gave arrive
    # as None. Dropping them here rather than there keeps server.py's rule
    # that a tool calls one function and returns what it gets back, and
    # lets each analysis apply its own default instead of a second copy of
    # that default living upstream.
    params = {k: v for k, v in params.items() if v is not None}

    try:
        analysis = get(analysis_type)
    except UnknownAnalysis as exc:
        return Refusal(
            reason=Reason.ANALYSIS_NOT_FOUND,
            what=str(exc),
            why=(
                "an analysis is looked up by name, and a name nobody "
                "registered cannot be guessed at -- running something adjacent "
                "would answer a question that was not asked."
            ),
            state=f"available: {_catalogue_text()}",
            next_call=_example_call(dataset_name),
        ).to_text()

    try:
        scope = scope_for(con, gate)
        output = analysis.run(con, gate, scope, **params)
    except LostRows as exc:
        return _unsound(dataset_name, str(exc))
    except ScopeError as exc:
        return Refusal(
            reason=Reason.ANALYSIS_NOT_POSSIBLE,
            what=f"the rows {analysis_type} would run over cannot be selected.",
            why=str(exc),
            state=f"contract v{gate.version} for {dataset_name}",
            next_call=f'validate_dataset(dataset_name="{dataset_name}")',
        ).to_text()
    except UnsafeSQL as exc:
        return Refusal(
            reason=Reason.ANALYSIS_NOT_POSSIBLE,
            what=f"{analysis_type} could not be run against {dataset_name}.",
            why=str(exc),
            state=f"contract v{gate.version} for {dataset_name}",
            next_call=f'propose_dataset_contract(dataset_name="{dataset_name}")',
        ).to_text()
    except (TypeError, ParamsInvalid) as exc:
        return Refusal(
            reason=Reason.ANALYSIS_PARAMS_INVALID,
            what=f"{analysis_type} was called with arguments it cannot take.",
            why=str(exc),
            state=f"{analysis_type}: {get(analysis_type).summary}",
            next_call=_example_call(dataset_name),
        ).to_text()
    except ValueError as exc:
        return Refusal(
            reason=Reason.ANALYSIS_NOT_POSSIBLE,
            what=f"{analysis_type} cannot answer that under this contract.",
            why=str(exc),
            state=f"contract v{gate.version} for {dataset_name}",
            next_call=f'propose_dataset_contract(dataset_name="{dataset_name}")',
        ).to_text()

    note = scope.method_note()
    if not output.summary or output.summary[0] != note:
        return _unsound(
            dataset_name,
            f"{analysis_type} returned a result whose first summary line is "
            f"not the method note for the scope it was given. Nothing says "
            f"what these numbers were computed over.",
        )

    result = results.write_result(
        workspace_id,
        label=output.label,
        headers=output.headers,
        rows=output.rows,
        summary=output.summary,
        dataset_name=dataset_name,
    )
    return f"{gate.header()}\n\n{result.to_text()}"


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


__all__ = ["compute_analysis"]
