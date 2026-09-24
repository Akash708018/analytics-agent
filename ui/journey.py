"""The Journey page: the project's story, inscribed chapter by chapter in the portfolio's ink.

Every date is the day a phase's first commit landed (`git log`), and every figure is one a command
printed -- the repository's rule that nothing is recorded without its output applies to what the
product says about itself too. Figures are as of 24/09/2026; update STATS when they change.
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
    icon: str = "bot"  # a Lucide icon in ui/static


CHAPTERS: tuple[Chapter, ...] = (
    Chapter("Phase 1", "27/08/2026", "A voice in the dark",
            "A tiny server learns to answer Claude Desktop -- ping, and a way to start clean.",
            "ping · reset_workspace", "bot"),
    Chapter("Phase 2", "28/08/2026", "Doors that open safely",
            "CSV, Excel and Postgres come in through a size gate that speaks before it loads. "
            "Every user gets their own DuckDB file, so no one reads another's tables.",
            "one workspace, one file", "database"),
    Chapter("Phase 3", "30/08/2026", "Reading the unreadable",
            "Stacked headers, merged cells, notes under the data. The file is described by an "
            "Ingest Spec a person reads and agrees to before a single row moves.",
            "merge fill bounded by real ranges", "layers-3"),
    Chapter("Phase 4", "31/08/2026", "The contract",
            "No number without an agreement: what one row is, what each measure means, which "
            "rows were left out on purpose. Nothing is computed without it.",
            "no contract, no analysis", "workflow"),
    Chapter("Phase 5", "02/09/2026", "Counting everything, changing nothing",
            "Nulls, duplicates and distributions, measured and reported. A column that looks "
            "like dates is said to look like dates -- and left alone.",
            "profiling is read-only", "search"),
    Chapter("Phase 6", "03/09/2026", "The cleaning gate",
            "Every fix is proposed with its exact SQL and exact counts, applied only when "
            "approved, and written into a ledger that remembers.",
            "nothing cleaned without a yes", "funnel"),
    Chapter("Phase 7", "06/09/2026", "Checking the promise",
            "The data is tested against its own contract, and every disagreement is reported "
            "rather than the first.",
            "validate_dataset", "shield-check"),
    Chapter("Phase 8", "08/09/2026", "The first numbers",
            "Nine analyses behind one gate -- summaries, distributions, rankings, Pareto. A "
            "result states what it was computed over and what it left out.",
            "9 analyses", "chart-no-axes-combined"),
    Chapter("Phase 9", "14/09/2026", "Time, relations and surprises",
            "Trends that name their missing months, seasonality, drivers, mix shifts, "
            "outliers and changepoints.",
            "21 analyses", "route"),
    Chapter("Phase 10", "19/09/2026", "Is it real?",
            "Hypothesis tests, confidence intervals, effect sizes, sample adequacy, cohorts and "
            "repeat behaviour -- each naming the test it ran and why.",
            "27 analyses", "lightbulb"),
    Chapter("Phase 11", "21/09/2026", "Pictures that describe themselves",
            "Eight kinds of chart. The agent cannot see an image, so every chart tells it, in "
            "numbers, exactly what was drawn.",
            "8 chart kinds", "message-circle"),
    Chapter("Phase 12", "21/09/2026", "The report",
            "Nine sections, always nine. Every number traced back to the exact call that made "
            "it, so anyone can repeat the work.",
            "9 mandatory sections", "file-text"),
    Chapter("Phase 13", "21/09/2026", "Keeping score",
            "Forty gold questions whose answers were worked out without the tool, and a "
            "refusal is only good if its own advice fixes it.",
            "eval 76 / 76", "target"),
    Chapter("Audit", "21/09/2026", "Looking back before going on",
            "The code checked against itself, not its notes. A chart hint that pointed the wrong "
            "way, exports that could overwrite each other, a subset reported as a whole, a "
            "column type that went nowhere -- found, measured and fixed.",
            "cleanup steps 4-7", "list-checks"),
    Chapter("Phase 14", "22/09/2026", "A door for everyone",
            "The same engine, opened to the browser -- measured first: locks, threads and "
            "sessions, before a single screen. You are reading its first page.",
            "7 screens", "bot"),
    Chapter("Stress", "24/09/2026", "Ninety-five kinds of bad data",
            "Every tool driven over files built to break it: Windows exports, pasted headers, "
            "totals rows, two-digit years, merged cells, twenty-digit ids. Each round's bugs "
            "fixed and the round run again, until a round found nothing.",
            "95 datasets · 0 crashes", "shield-check"),
)

STATS: tuple[tuple[str, str], ...] = (
    ("29", "tools"), ("27", "analyses"), ("1,949", "tests passing"), ("76/76", "eval score"),
    ("101", "self-corrections logged"), ("95", "stress datasets"),
)

# The portfolio's own vocabulary for this project (its formula-map.js, chapter "#agent"), plus
# the three code-native diagrams it draws with. Illustrative marks, not results.
FIELD: tuple[str, ...] = (
    "raw → profile → validate", "icon:shield-check", "diagram:neural-network",
    "{ contract: confirmed }", "icon:workflow", "propose → approve → apply",
    "diagram:normal-distribution", "schema ✓", "icon:database",
    "input → tools → checked output", "diagram:regression-scatter", "no contract, no analysis",
)

STATIC = "/app/static"


# SVGs inside CSS are percent-encoded: a literal tag in a stylesheet makes st.html's sanitiser
# drop the whole block (C97; theme.apply refuses one).
def _svg_uri(svg: str) -> str:
    return "data:image/svg+xml," + quote(svg, safe=" =:/'.,-")


_FOOT_URI = _svg_uri(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 34'>"
    "<ellipse cx='10' cy='22' rx='6.5' ry='10' fill='#a25934'/>"
    "<ellipse cx='10' cy='7' rx='4.5' ry='5' fill='#a25934'/></svg>"
)

_CSS = """
<style>
.aa-j { position: relative; isolation: isolate; max-width: 1040px; margin: 0 auto; }
.aa-j > .aa-j-hero, .aa-j > .aa-j-rail, .aa-j > .aa-j-stats, .aa-j > .aa-j-close {
  position: relative; z-index: 1; }

/* Hero: the portfolio's sunset histogram, masked into the paper on the right. */
.aa-j-hero { position: relative; min-height: 420px; padding: 1.4rem 0 2.4rem; }
/* Inside its box, not bleeding out: Streamlit clips the block edge, which cut the fade hard. */
.aa-j-art { position: absolute; inset: 0 0 0 30%; z-index: -1; pointer-events: none;
  background: url('ART_URI') right center / cover no-repeat;
  /* Faded on both axes, as the portfolio's hero is: two masks, intersected. */
  -webkit-mask-image: linear-gradient(90deg, transparent 4%, #0003 34%, #000 66%, #000 86%,
    transparent), linear-gradient(transparent, #000 22%, #000 70%, transparent);
  -webkit-mask-composite: source-in;
  mask-image: linear-gradient(90deg, transparent 4%, #0003 34%, #000 66%, #000 86%,
    transparent), linear-gradient(transparent, #000 22%, #000 70%, transparent);
  mask-composite: intersect;
  animation: aa-drift 20s ease-in-out infinite; }
.aa-j-kicker { display: flex; align-items: center; gap: 13px;
  font: 500 .75rem/1 var(--mono); letter-spacing: .13em; color: var(--studio-ink);
  animation: aa-rise .9s .05s ease both; }
.aa-j-kicker::before { content: ""; width: 28px; height: 1px; background: var(--accent); }
.aa-j-h1 { margin: 1.1rem 0 .9rem; max-width: 640px; color: var(--text);
  font: 500 clamp(3rem, 7vw, 5.6rem)/1.02 var(--font); letter-spacing: -.067em;
  animation: aa-rise 1.1s .1s cubic-bezier(.2,.7,.2,1) both; }
.aa-j-h1 em { display: inline-block; color: var(--accent); font: italic 400 1.02em/1.1 var(--serif);
  letter-spacing: -.035em; animation: aa-rise 1.2s .22s cubic-bezier(.2,.7,.2,1) both; }
.aa-j-note { max-width: 420px; color: #594336; font-size: 1.05rem; line-height: 1.8;
  animation: aa-rise 1.1s .34s cubic-bezier(.2,.7,.2,1) both; }
.aa-j-meta { display: flex; gap: 1.6rem; flex-wrap: wrap; margin-top: 1.6rem; padding-top: 1rem;
  border-top: 1px solid var(--line); color: #7a604f; font: 500 .72rem/1.4 var(--mono);
  letter-spacing: .075em; animation: aa-rise 1s .46s ease both; }

/* The rail the chapters hang from, with footsteps walking down it. */
.aa-j-rail { position: relative; padding: .6rem 0 .4rem 3.2rem; }
.aa-j-rail::before { content: ""; position: absolute; left: 1.15rem; top: 1.2rem; bottom: 1.2rem;
  width: 1px; background: repeating-linear-gradient(#a2593466 0 6px, transparent 6px 12px); }

.aa-j-ch { position: relative; display: grid; grid-template-columns: 46px minmax(0, 1fr);
  gap: 16px; align-items: start; margin: 0 0 1.05rem; padding: 1.05rem 1.2rem;
  background: #fbf4e9ee; border: 1px solid #cdae938c; border-radius: 9px;
  box-shadow: 0 15px 40px #7141240b, inset 0 1px 0 #fff9;
  opacity: 0; animation: aa-write 1.3s cubic-bezier(.2,.7,.2,1) forwards; }
.aa-j-tile { display: grid; place-items: center; width: 46px; height: 46px; border-radius: 9px;
  background: linear-gradient(145deg, #eac29d, #d7a279); box-shadow: inset 0 1px 0 #fff8; }
.aa-j-tile img { width: 22px; height: 22px;
  filter: invert(22%) sepia(35%) saturate(900%) hue-rotate(340deg) brightness(80%); }
.aa-j-when { font: 500 .72rem/1.4 var(--mono); letter-spacing: .09em; color: #945836; }
.aa-j-title { margin: .15rem 0 .3rem; color: var(--text); font: 600 1.28rem/1.25 var(--font);
  letter-spacing: -.035em; }
.aa-j-story { margin: 0; color: var(--muted); font-size: .98rem; line-height: 1.6; }
.aa-j-mark { display: inline-block; margin-top: .55rem; padding: .08rem .55rem; border-radius: 5px;
  border: 1px solid #cdae93; background: #f3e2ca; color: #6e3f27;
  font: 500 .7rem/1.6 var(--mono); letter-spacing: .03em; }
/* An ink drop on the rail where each chapter begins. */
.aa-j-dot { position: absolute; left: -2.35rem; top: 1.45rem; width: 11px; height: 11px;
  border-radius: 50%; background: radial-gradient(circle, #9d472c 0 42%, #9d472c00 70%);
  opacity: 0; animation: aa-drop 1.1s ease-out forwards; }
.aa-j-steps { position: absolute; left: -2.2rem; top: 3.1rem; }
.aa-j-steps span { position: absolute; width: 9px; height: 15px; opacity: 0;
  background: url("FOOT_URI") center / contain no-repeat; animation: aa-step 5.2s ease-in-out infinite; }
.aa-j-steps span:nth-child(1) { top: 0; left: -4px; }
.aa-j-steps span:nth-child(2) { top: 15px; left: 4px; transform: scaleX(-1); animation-delay: .6s; }
.aa-j-steps span:nth-child(3) { top: 30px; left: -4px; animation-delay: 1.2s; }

.aa-j-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0; margin: 1.8rem 0 1rem; border-block: 1px solid #bc987680; background: #f5e6cf9c; }
.aa-j-stat { padding: 1rem .9rem; opacity: 0; animation: aa-rise 1s ease forwards; }
.aa-j-stat + .aa-j-stat { border-left: 1px solid #d6bea880; }
.aa-j-stat b { display: block; color: #503326; font: 400 2rem/1.15 var(--mono);
  letter-spacing: -.06em; font-variant-numeric: tabular-nums; }
.aa-j-stat span { color: var(--muted); font: 500 .7rem/1.4 var(--mono); letter-spacing: .06em;
  text-transform: uppercase; }
.aa-j-close { margin: 1.2rem 0 .4rem; text-align: center; color: var(--text);
  font: 500 1.6rem/1.3 var(--font); letter-spacing: -.04em; opacity: 0;
  animation: aa-rise 1.2s ease forwards; }
.aa-j-close em { color: var(--accent); font: italic 400 1.05em var(--serif); }

/* The field notes: copper ink that inscribes, holds and dissolves -- the portfolio's
   ink-emerge and ink-inscribe, timings and strength included. */
/* Over the content, as the portfolio's reading view draws it: the cards are opaque, so a field
   behind them was invisible below the hero. Softened through the middle; never interactive. */
.aa-field { position: absolute; inset: 0; z-index: 2; overflow: clip; pointer-events: none;
  user-select: none; --ink-strength: .3;
  -webkit-mask-image: linear-gradient(#000, #000a 14%, #0005 32%, #0005 70%, #000b 86%, #000);
  mask-image: linear-gradient(#000, #000a 14%, #0005 32%, #0005 70%, #000b 86%, #000); }
.aa-ink { position: absolute; display: block; width: max-content; max-width: 30%; opacity: 0;
  color: #805132; font: italic clamp(1rem, 1.5vw, 1.45rem)/1.5 var(--serif);
  animation: aa-emerge 12s var(--d) ease-in-out infinite both; }
.aa-ink > i { display: block; font-style: inherit; text-shadow: 0 1px 4px #fff0d6;
  animation: aa-inscribe-loop 12s var(--d) ease-in-out infinite both; }
.aa-ink img { display: block; height: auto;
  filter: invert(30%) sepia(24%) saturate(950%) hue-rotate(342deg) brightness(93%); }
.aa-ink.icon img { width: clamp(34px, 3.4vw, 52px); }
.aa-ink.diagram img { width: clamp(110px, 12vw, 170px); filter: none; }
.aa-ink.s0 { left: 46%; top: 1%; --a: -5deg; }   .aa-ink.s1 { right: 2%; top: 7%; --a: 5deg; }
.aa-ink.s2 { left: 58%; top: 20%; --a: -6deg; }  .aa-ink.s3 { right: 4%; top: 28%; --a: -3deg; }
.aa-ink.s4 { left: 1%; top: 36%; --a: -9deg; }   .aa-ink.s5 { right: 1%; top: 44%; --a: 6deg; }
.aa-ink.s6 { left: 2%; top: 52%; --a: 4deg; }    .aa-ink.s7 { right: 1%; top: 61%; --a: 10deg; }
.aa-ink.s8 { left: 1%; top: 70%; --a: -4deg; }   .aa-ink.s9 { right: 3%; top: 79%; --a: 5deg; }
.aa-ink.s10 { left: 3%; top: 87%; --a: -7deg; }  .aa-ink.s11 { right: 6%; top: 95%; --a: 4deg; }

@keyframes aa-write {
  0%   { opacity: 0; clip-path: inset(0 100% 0 0); filter: blur(3px);
         transform: translate3d(0,5px,0); }
  55%  { opacity: 1; filter: blur(.6px); }
  100% { opacity: 1; clip-path: inset(0 0 0 0); filter: none; transform: none; }
}
@keyframes aa-emerge {
  0%, 3%   { opacity: 0; transform: translate3d(0,5px,0) rotate(var(--a)); }
  14%, 49% { opacity: var(--ink-strength); transform: translate3d(0,0,0) rotate(var(--a)); }
  66%, 100% { opacity: 0; transform: translate3d(0,-4px,0) rotate(var(--a)); }
}
@keyframes aa-inscribe-loop {
  0%, 3% { clip-path: inset(0 100% 0 0); } 19%, 100% { clip-path: inset(0); } }
@keyframes aa-rise {
  from { opacity: 0; transform: translate3d(0,14px,0); } to { opacity: 1; transform: none; } }
@keyframes aa-drop { 0% { opacity: 0; transform: scale(.2); } 50% { opacity: 1; transform: scale(1.7); }
  100% { opacity: .9; transform: scale(1); } }
@keyframes aa-step { 0%, 100% { opacity: 0; } 15%, 45% { opacity: .6; } 70% { opacity: 0; } }
@keyframes aa-drift {
  0%, 100% { transform: translate3d(0,0,0); } 50% { transform: translate3d(-8px,-6px,0); } }

@media (max-width: 760px) {
  .aa-j-art { inset: -20px -20px 40% 20%; opacity: .55; }
  .aa-j-rail { padding-left: 2.4rem; }
  .aa-j-ch { grid-template-columns: 38px minmax(0, 1fr); gap: 12px; }
  .aa-j-tile { width: 38px; height: 38px; }
  .aa-field { --ink-strength: .24; }
  .aa-ink { max-width: 45%; font-size: 1rem; }
  .aa-ink.s6, .aa-ink.s7, .aa-ink.s10, .aa-ink.s11 { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .aa-j *, .aa-j *::before { animation: none !important; opacity: 1 !important;
    clip-path: none !important; filter: none !important; transform: none !important; }
  .aa-field .aa-ink { opacity: 0 !important; }
  .aa-field .aa-ink.s1, .aa-field .aa-ink.s2 { opacity: .12 !important; }
}
</style>
"""

#: Seconds between one chapter starting to write and the next.
PACE = 0.7


def stylesheet() -> str:
    """The page's CSS, for theme.apply(), which sends it with the theme as one block."""
    return (_CSS.replace("FOOT_URI", _FOOT_URI)
            .replace("ART_URI", f"{STATIC}/observatory-hero.jpg"))


def _field_html() -> str:
    esc = html.escape
    out = ['<div class="aa-field" aria-hidden="true">']
    for slot, item in enumerate(FIELD):
        delay = f"{-slot * 1.08 - 2:.2f}s"  # spread phases so a few marks are always present
        if item.startswith(("icon:", "diagram:")):
            kind, name = item.split(":", 1)
            body = f'<img src="{STATIC}/{esc(name)}.svg" alt="">'
        else:
            kind, body = "text", esc(item)
        out.append(f'<span class="aa-ink {kind} s{slot}" style="--d:{delay}"><i>{body}</i></span>')
    out.append("</div>")
    return "".join(out)


def page_html(nonce: int = 0) -> str:
    """The page's markup (stylesheet() holds its CSS). `nonce` changes the root id, so a replay
    replaces the DOM and every animation starts over."""
    esc = html.escape
    parts = [
        f'<div class="aa-j" id="aa-j-{nonce}">', _field_html(),
        '<div class="aa-j-hero"><div class="aa-j-art"></div>',
        '<div class="aa-j-kicker">ANALYTICS AGENT · THE JOURNEY</div>',
        '<div class="aa-j-h1">How this engine <em>was made.</em></div>',
        '<p class="aa-j-note">Sixteen chapters, from a server that could only say "ping" to a '
        "door anyone can open. Watch each one write itself in.</p>",
        '<div class="aa-j-meta"><span>27/08/2026 → 24/09/2026</span><span>MCP + DUCKDB</span>'
        "<span>HUMAN IN THE LOOP</span></div></div>",
        '<div class="aa-j-rail">',
    ]
    start = 1.2
    for i, ch in enumerate(CHAPTERS):
        t = start + i * PACE
        steps = "" if i == len(CHAPTERS) - 1 else (
            '<div class="aa-j-steps">' + "<span></span>" * 3 + "</div>")
        parts.append(
            f'<div class="aa-j-ch" style="animation-delay:{t:.2f}s">'
            f'<i class="aa-j-dot" style="animation-delay:{t:.2f}s"></i>{steps}'
            f'<div class="aa-j-tile"><img src="{STATIC}/{esc(ch.icon)}.svg" alt=""></div><div>'
            f'<div class="aa-j-when">{esc(ch.label.upper())} · {esc(ch.date)}</div>'
            f'<div class="aa-j-title">{esc(ch.title)}</div>'
            f'<p class="aa-j-story">{esc(ch.story)}</p>'
            f'<span class="aa-j-mark">{esc(ch.mark)}</span></div></div>'
        )
    parts.append("</div>")
    end = start + len(CHAPTERS) * PACE
    parts.append('<div class="aa-j-stats">')
    for j, (value, label) in enumerate(STATS):
        parts.append(f'<div class="aa-j-stat" style="animation-delay:{end + j * .15:.2f}s">'
                     f"<b>{esc(value)}</b><span>{esc(label)}</span></div>")
    parts.append("</div>")
    parts.append(f'<div class="aa-j-close" style="animation-delay:{end + 1.1:.2f}s">'
                 "The map is still being <em>drawn.</em></div>")
    parts.append("</div>")
    return "".join(parts)


def render() -> None:
    nonce = st.session_state.setdefault("journey_nonce", 0)
    st.html(page_html(nonce))
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if st.button("Write it again", width="stretch", type="secondary"):
            st.session_state["journey_nonce"] = nonce + 1
            st.rerun()
