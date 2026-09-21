"""The Journey page: the project's story, written onto parchment in ink that surfaces line by line.

Every date is the day a phase's first commit landed (`git log`), and every figure is one a command
printed -- the repository's rule that nothing is recorded without its output applies to what the
product says about itself too. Figures are as of 22/09/2026; update STATS when they change.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from urllib.parse import quote

import streamlit as st


@dataclass(frozen=True)
class Chapter:
    label: str   # "Phase 3"
    date: str    # dd/mm/yyyy, first commit
    title: str
    story: str
    mark: str    # one measured figure or artefact


CHAPTERS: tuple[Chapter, ...] = (
    Chapter("Phase 1", "27/08/2026", "A voice in the dark",
            "A tiny server learns to answer Claude Desktop -- ping, and a way to start clean.",
            "ping · reset_workspace"),
    Chapter("Phase 2", "28/08/2026", "Doors that open safely",
            "CSV, Excel and Postgres come in through a size gate that speaks before it loads. "
            "Every user gets their own DuckDB file, so no one reads another's tables.",
            "one workspace, one file"),
    Chapter("Phase 3", "30/08/2026", "Reading the unreadable",
            "Stacked headers, merged cells, notes under the data. The file is described by an "
            "Ingest Spec a person reads and agrees to before a single row moves.",
            "merge fill bounded by real ranges"),
    Chapter("Phase 4", "31/08/2026", "The contract",
            "No number without an agreement: what one row is, what each measure means, which "
            "rows were left out on purpose. Nothing is computed without it.",
            "no contract, no analysis"),
    Chapter("Phase 5", "02/09/2026", "Counting everything, changing nothing",
            "Nulls, duplicates and distributions, measured and reported. A column that looks "
            "like dates is said to look like dates -- and left alone.",
            "profiling is read-only"),
    Chapter("Phase 6", "03/09/2026", "The cleaning gate",
            "Every fix is proposed with its exact SQL and exact counts, applied only when "
            "approved, and written into a ledger that remembers.",
            "nothing cleaned without a yes"),
    Chapter("Phase 7", "06/09/2026", "Checking the promise",
            "The data is tested against its own contract, and every disagreement is reported "
            "rather than the first.",
            "validate_dataset"),
    Chapter("Phase 8", "08/09/2026", "The first numbers",
            "Nine analyses behind one gate -- summaries, distributions, rankings, Pareto. A "
            "result states what it was computed over and what it left out.",
            "9 analyses"),
    Chapter("Phase 9", "14/09/2026", "Time, relations and surprises",
            "Trends that name their missing months, seasonality, drivers, mix shifts, "
            "outliers and changepoints.",
            "21 analyses"),
    Chapter("Phase 10", "19/09/2026", "Is it real?",
            "Hypothesis tests, confidence intervals, effect sizes, sample adequacy, cohorts and "
            "repeat behaviour -- each naming the test it ran and why.",
            "27 analyses"),
    Chapter("Phase 11", "21/09/2026", "Pictures that describe themselves",
            "Eight kinds of chart. The agent cannot see an image, so every chart tells it, in "
            "numbers, exactly what was drawn.",
            "8 chart kinds"),
    Chapter("Phase 12", "21/09/2026", "The report",
            "Nine sections, always nine. Every number traced back to the exact call that made "
            "it, so anyone can repeat the work.",
            "9 mandatory sections"),
    Chapter("Phase 13", "21/09/2026", "Keeping score",
            "Forty gold questions whose answers were worked out without the tool, and a "
            "refusal is only good if its own advice fixes it.",
            "eval 76 / 76"),
    Chapter("Audit", "21/09/2026", "Looking back before going on",
            "The code checked against itself, not its notes. A chart hint that pointed the wrong "
            "way, exports that could overwrite each other, a subset reported as a whole, a "
            "column type that went nowhere -- found, measured and fixed.",
            "cleanup steps 4-7"),
    Chapter("Phase 14", "22/09/2026", "A door for everyone",
            "The same engine, opened to the browser -- measured first: locks, threads and "
            "sessions, before a single screen. You are reading its first page.",
            "in progress"),
)

STATS: tuple[tuple[str, str], ...] = (
    ("29", "tools"), ("27", "analyses"), ("1,787", "tests passing"), ("76/76", "eval score"),
    ("96", "self-corrections logged"), ("140", "commits"),
)

# Streamlit's HTML sanitiser strips inline <svg> and drops a <style> block sent together with
# markup (measured in the browser, 22/09/2026). Classes and style attributes survive, so the
# stylesheet goes in its own st.html call and the footprint is a CSS background image.
# The SVGs are percent-encoded because st.html's sanitiser (DOMPurify) discards a whole <style>
# element whose text contains a tag-like "<" -- see theme.apply, which now refuses one.
def _svg_uri(svg: str) -> str:
    return "data:image/svg+xml," + quote(svg, safe=" =:/'.,-")


_FOOT_URI = _svg_uri(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 34'>"
    "<ellipse cx='10' cy='22' rx='6.5' ry='10' fill='#3a2314'/>"
    "<ellipse cx='10' cy='7' rx='4.5' ry='5' fill='#3a2314'/></svg>"
)
_GRAIN_URI = _svg_uri(
    "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'>"
    "<feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2'/>"
    "<feColorMatrix values='0 0 0 0 .35  0 0 0 0 .22  0 0 0 0 .1  0 0 0 .09 0'/></filter>"
    "<rect width='100%' height='100%' filter='url(#n)'/></svg>"
)

_CSS = """
<style>
.aa-j { max-width: 860px; margin: 0 auto; }
.aa-j-hero { text-align: center; padding: 1.2rem 0 1.6rem; }
.aa-j-hero .aa-j-kicker {
  font-family: 'Cinzel', serif; letter-spacing: .5em; font-size: .78rem; color: var(--peach);
  opacity: 0; animation: aa-write 1.6s ease-out .2s forwards;
}
.aa-j-hero h1 {
  font-family: 'Cinzel', serif; font-size: clamp(2rem, 5vw, 3.3rem); margin: .4rem 0 .2rem;
  background: var(--sunset); -webkit-background-clip: text; background-clip: text;
  color: transparent; opacity: 0; animation: aa-write 2.2s ease-out .6s forwards;
}
.aa-j-hero p {
  font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 1.25rem;
  color: var(--parchment-dim); opacity: 0; animation: aa-write 2s ease-out 1.6s forwards;
}

/* The parchment: warm paper, a sunset glow at its edge, grain from an SVG turbulence. */
.aa-j-paper {
  position: relative; border-radius: 18px; padding: 2.4rem 2.2rem 2rem 3.6rem;
  color: var(--ink);
  background:
    url("GRAIN_URI"),
    radial-gradient(120% 90% at 50% 40%, #f8ebcf 0%, #efdcb6 55%, #d9bd8c 100%);
  box-shadow: 0 0 0 1px rgba(90,50,20,.25), 0 0 60px rgba(255,126,95,.28),
              inset 0 0 70px rgba(120,70,30,.35);
}
/* The path the footsteps walk. */
.aa-j-paper::before {
  content: ""; position: absolute; left: 1.7rem; top: 2.6rem; bottom: 2.4rem; width: 2px;
  background: repeating-linear-gradient(to bottom, rgba(58,35,20,.35) 0 6px, transparent 6px 12px);
}

.aa-j-ch { position: relative; margin: 0 0 1.55rem; }
.aa-j-ch > * { opacity: 0; animation: aa-write 1.5s ease-out forwards; }
.aa-j-date {
  font-family: 'Cinzel', serif; font-size: .72rem; letter-spacing: .28em; color: #8a4b2a;
}
.aa-j-title { font-family: 'Cinzel', serif; font-size: 1.28rem; font-weight: 700; margin: .1rem 0; }
/* Ink, explicitly: the theme colours every paragraph parchment for the dusk background,
   which on paper is cream on cream. */
.aa-j-paper, .aa-j-paper p, .aa-j-paper div { color: var(--ink); }
.aa-j-story {
  font-family: 'Cormorant Garamond', serif; font-size: 1.18rem; line-height: 1.45; margin: 0;
}
.aa-j-mark {
  display: inline-block; margin-top: .35rem; font-family: 'Inter', sans-serif; font-size: .74rem;
  font-weight: 600; color: #7a2e1e; border: 1px solid rgba(122,46,30,.35); border-radius: 999px;
  padding: .05rem .55rem;
}
/* An ink drop where each chapter begins, spreading then settling. */
.aa-j-dot {
  position: absolute; left: -2.2rem; top: .35rem; width: 11px; height: 11px; border-radius: 50%;
  background: radial-gradient(circle, #5a2d18 0 45%, rgba(90,45,24,0) 70%);
  opacity: 0; animation: aa-drop 1.2s ease-out forwards;
}
/* Footsteps between chapters: left, right, left -- appearing and fading, forever. */
.aa-j-steps { position: absolute; left: -2.05rem; top: 1.6rem; }
.aa-j-steps span {
  position: absolute; width: 11px; height: 19px; opacity: 0;
  background: url("FOOT_URI") center / contain no-repeat;
  animation: aa-step 4.8s ease-in-out infinite;
}
.aa-j-steps span:nth-child(1) { top: 0;    left: -5px; }
.aa-j-steps span:nth-child(2) { top: 18px; left: 5px;  transform: scaleX(-1); animation-delay: .6s; }
.aa-j-steps span:nth-child(3) { top: 36px; left: -5px; animation-delay: 1.2s; }

.aa-j-stats {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: .8rem;
  margin: 1.8rem 0 .6rem;
}
.aa-j-stat {
  text-align: center; padding: .9rem .4rem; border-radius: 14px;
  background: rgba(42,26,53,.75); border: 1px solid rgba(255,126,95,.25);
  opacity: 0; animation: aa-write 1.4s ease-out forwards;
}
.aa-j-stat b {
  display: block; font-family: 'Cinzel', serif; font-size: 1.55rem;
  background: var(--sunset); -webkit-background-clip: text; background-clip: text;
  color: transparent;
}
.aa-j-stat span { font-size: .78rem; color: var(--parchment-dim); letter-spacing: .04em; }
.aa-j-close {
  text-align: center; font-family: 'Cormorant Garamond', serif; font-style: italic;
  font-size: 1.3rem; color: var(--gold); opacity: 0; animation: aa-write 2s ease-out forwards;
}

/* Writing: the line arrives blurred and wide, left to right, and draws itself together. */
@keyframes aa-write {
  0%   { opacity: 0; filter: blur(7px); letter-spacing: .18em; clip-path: inset(0 100% 0 0); }
  45%  { opacity: .7; filter: blur(2.5px); clip-path: inset(0 25% 0 0); }
  100% { opacity: 1; filter: blur(0); letter-spacing: normal; clip-path: inset(0 0 0 0); }
}
@keyframes aa-drop {
  0% { opacity: 0; transform: scale(.2); } 50% { opacity: 1; transform: scale(1.8); }
  100% { opacity: .9; transform: scale(1); }
}
@keyframes aa-step { 0%, 100% { opacity: 0; } 15%, 45% { opacity: .85; } 70% { opacity: 0; } }

@media (max-width: 640px) { .aa-j-paper { padding: 1.8rem 1.2rem 1.6rem 2.8rem; } }
@media (prefers-reduced-motion: reduce) {
  .aa-j *, .aa-j *::before { animation: none !important; opacity: 1 !important;
    filter: none !important; clip-path: none !important; }
}
</style>
"""

def stylesheet() -> str:
    """The page's CSS, for theme.apply() -- which sends it with the theme in one block."""
    css = _CSS.replace("FOOT_URI", _FOOT_URI).replace("GRAIN_URI", _GRAIN_URI)
    return css


#: Seconds between one chapter starting to write and the next.
PACE = 0.75


def page_html(nonce: int = 0) -> str:
    """The page's markup (stylesheet() holds its CSS). `nonce` changes the root id, so a replay
    replaces the DOM and the animation starts over."""
    esc = html.escape
    parts = [
        f'<div class="aa-j" id="aa-j-{nonce}">',
        '<div class="aa-j-hero">',
        '<div class="aa-j-kicker">THE ANALYST\'S MAP</div>',
        "<h1>How this engine was made</h1>",
        "<p>Watch the parchment. The work writes itself in.</p>",
        "</div>",
        '<div class="aa-j-paper">',
    ]
    start = 2.6
    for i, ch in enumerate(CHAPTERS):
        t = start + i * PACE
        steps = "" if i == len(CHAPTERS) - 1 else (
            '<div class="aa-j-steps">' + "<span></span>" * 3 + "</div>")
        parts.append(
            f'<div class="aa-j-ch">'
            f'<i class="aa-j-dot" style="animation-delay:{t:.2f}s"></i>{steps}'
            f'<div class="aa-j-date" style="animation-delay:{t:.2f}s">'
            f"{esc(ch.label.upper())} · {esc(ch.date)}</div>"
            f'<div class="aa-j-title" style="animation-delay:{t + .15:.2f}s">{esc(ch.title)}</div>'
            f'<p class="aa-j-story" style="animation-delay:{t + .35:.2f}s">{esc(ch.story)}</p>'
            f'<span class="aa-j-mark" style="animation-delay:{t + .6:.2f}s">{esc(ch.mark)}</span>'
            f"</div>"
        )
    parts.append("</div>")
    end = start + len(CHAPTERS) * PACE
    parts.append('<div class="aa-j-stats">')
    for j, (value, label) in enumerate(STATS):
        parts.append(f'<div class="aa-j-stat" style="animation-delay:{end + j * .2:.2f}s">'
                     f"<b>{esc(value)}</b><span>{esc(label)}</span></div>")
    parts.append("</div>")
    parts.append(f'<div class="aa-j-close" style="animation-delay:{end + 1.6:.2f}s">'
                 "The map is still being drawn.</div>")
    parts.append("</div>")
    return "".join(parts)


def render() -> None:
    nonce = st.session_state.setdefault("journey_nonce", 0)
    st.html(page_html(nonce))
    left, mid, right = st.columns([1, 1, 1])
    with mid:
        if st.button("Write it again", use_container_width=True, type="secondary"):
            st.session_state["journey_nonce"] = nonce + 1
            st.rerun()
