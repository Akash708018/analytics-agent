"""
Turning a profile into the thing a person reads.

`table_profile.py` counts and `results.py` writes; this decides what actually
comes back, which is a different job from either and the one where F7 gets in.

**Every profile writes a file. Without exception.** A small table could be read
inline and never written, and that was the tempting design -- fewer files, less
clutter. It is wrong for one reason: it makes the agent reason about which case
it is in. An agent that has learned "a profile comes with a path" and then meets
a profile without one does not conclude that this profile is small. It produces
a path, because a path is what belongs there. The uniform contract costs some
disk and removes a whole class of invention, and `reset_workspace` already
answers the disk.

**What changes with width is the BODY, not the envelope.** A profile has one row
per column of the table it describes, so a 60-column table produces 60 rows of
24 fields. Sixty prose sentences is not a readable answer and neither is a
24-column table in a chat window.

    <= 20 columns   the per-column sentences, which say more per line than the
                    table does and read as English
    >  20 columns   the table's own preview -- 20 rows by 12 fields, sliced by
                    results.py, with both counts stated

Twenty is `results.PREVIEW_ROWS`, reused rather than reinvented: the preview is
capped there anyway, so a threshold above it would promise sentences for rows
the envelope has already truncated.

**The invariant, which is what the tests actually assert.** Wherever the path
appears, the shape, the summary and the literal next call appear with it. That
is a property of the OUTPUT, not a rule about which function was called, so it
holds however this module is later rearranged. `render_profile` composes its
narrow form from `Result`'s parts rather than calling `to_text()` wholesale, and
the invariant is what stops that being a hole.
"""

from __future__ import annotations

from analytics_agent.profile.table_profile import TableProfile
from analytics_agent.util import results

# Above this many columns the per-column sentences stop being readable and the
# table's own preview is shown instead. One profile row per table column, so
# this is a count of the profiled table's columns. Tied to PREVIEW_ROWS because
# results.py truncates the preview there regardless.
INLINE_COLUMN_LIMIT = results.PREVIEW_ROWS


def _label(dataset_name: str) -> str:
    """A filename stem. `write_result` validates it; this keeps it valid."""
    return f"profile_{dataset_name}"


def render_profile(
    workspace_id: str,
    profile: TableProfile,
    *,
    inline_column_limit: int = INLINE_COLUMN_LIMIT,
) -> str:
    """
    Write the profile and return what the agent should read.

    The file is always written. What comes back always carries the shape, the
    findings, the path and the call that reads the rest of it -- see the module
    docstring for why that is asserted as a property of the output rather than
    trusted to whoever edits this next.
    """
    result = results.write_result(
        workspace_id,
        label=_label(profile.dataset_name),
        headers=TableProfile.HEADERS,
        rows=profile.to_rows(),
        summary=profile.summary_lines(),
        dataset_name=profile.dataset_name,
    )

    head = (
        f"Profile of {profile.dataset_name}: {profile.row_count:,} rows, "
        f"{profile.column_count} columns."
    )

    if profile.column_count > inline_column_limit:
        # Wide. The envelope's own rendering is the readable form here: it
        # states both truncations, previews 20 rows by 12 fields, and ends in
        # the call that fetches the rest.
        body = [
            "",
            f"{profile.column_count} columns is too many to describe one line "
            f"each, so what follows is the profile table itself.",
            "",
            result.to_text(),
        ]
    else:
        body = ["", "What this shows:"]
        body += [f"  - {s}" for s in profile.summary_lines()]
        body += ["", "Columns:"]
        body += [f"  - {c.sentence()}" for c in profile.columns]
        body += [
            "",
            f"Every column above, with its counts as a table "
            f"({result.row_count:,} rows x {result.column_count} fields):",
            f"  {result.path}",
            f"  {result.paging_hint(1)}",
        ]

    out = [head] + body
    if profile.notes:
        out += ["", "Notes:"] + [f"  - {n}" for n in profile.notes]
    return "\n".join(out)


__all__ = ["INLINE_COLUMN_LIMIT", "render_profile"]
