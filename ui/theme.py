"""The look: the author's portfolio's "warm data studio", carried into the product.

Tokens, type and motion come from akash-portfolio (dist/styles.css, studio.css, formula-map.css):
sandstone paper with a clay texture, dark-brown ink, terracotta and copper accents; Manrope for
reading, DM Serif Display italic for the one emphasised word, IBM Plex Mono for labels and
figures; and copper "field notes" -- formulas and icons that inscribe left to right, hold, and
dissolve. The product and the portfolio should read as one hand.

Everything visual lives here; a screen calls `theme.apply()` once and uses these class names.
The motion switch in the sidebar and a system reduced-motion preference both stop animation.
"""

from __future__ import annotations

import re

import streamlit as st

# Portfolio tokens.
BG = "#f1e3d0"         # sandstone page
PANEL = "#fbf4e9"      # cards
TEXT = "#37271f"       # ink
MUTED = "#756052"
LINE = "#d6bea8"
ACCENT = "#9d472c"     # terracotta
SUNSET = "#c87948"
COPPER = "#a25934"
STUDIO_INK = "#563722"

STATIC = "/app/static"

_FONTS = (
    "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700"
    "&family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Mono:wght@400;500&display=swap"
)

_CSS = f"""
<style>
@import url('{_FONTS}');

:root {{
  --bg: {BG}; --panel: {PANEL}; --text: {TEXT}; --muted: {MUTED}; --line: {LINE};
  --accent: {ACCENT}; --sunset: {SUNSET}; --copper: {COPPER}; --studio-ink: {STUDIO_INK};
  --font: 'Manrope', Arial, sans-serif;
  --serif: 'DM Serif Display', Georgia, serif;
  --mono: 'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace;
}}

/* Sandstone paper, the portfolio's clay texture multiplied faintly over it. */
.stApp {{ background: var(--bg); color: var(--text); font: 400 1rem/1.6 var(--font); }}
.stApp::before {{
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background: url('{STATIC}/clay-texture.jpg') repeat; background-size: 630px;
  opacity: .16; mix-blend-mode: multiply;
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{
  background: linear-gradient(#f5e8d6, #efdfc9); border-right: 1px solid var(--line);
}}
::selection {{ color: #fff5e8; background: #a85132; }}

/* Editorial headings: tight Manrope, one italic serif word in terracotta (markdown em). */
h1, h2, h3 {{ font-family: var(--font) !important; color: var(--text) !important;
  font-weight: 500 !important; letter-spacing: -.045em; }}
h1 {{ font-size: clamp(2.4rem, 4.6vw, 3.6rem) !important; line-height: 1.05 !important; }}
h1 em, h2 em, h3 em, .aa-em {{
  font-family: var(--serif); font-style: italic; font-weight: 400; color: var(--accent);
  letter-spacing: -.02em;
}}
p, li, label {{ color: var(--text); }}
[data-testid="stCaptionContainer"], .aa-muted {{ color: var(--muted) !important; }}

/* The mono eyebrow with its thin leading rule. */
.aa-eyebrow {{
  /* line-height 1.5 and no negative margin: at 1 the glyphs were clipped by the html box. */
  display: flex; align-items: center; gap: 13px; margin: .2rem 0 0; padding: .1rem 0;
  font: 500 .75rem/1.5 var(--mono); letter-spacing: .13em; text-transform: uppercase;
  color: var(--studio-ink);
}}
.aa-eyebrow::before {{ content: ""; width: 28px; height: 1px; background: var(--accent); }}

/* Buttons: terracotta for the action, bordered sandstone for everything else. */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  background: var(--accent); color: #fff6e8; border: 1px solid var(--accent);
  border-radius: 6px; font-weight: 600; letter-spacing: .01em;
  box-shadow: 0 8px 18px #9d472c28; transition: transform .25s, background .25s;
}}
.stButton > button:hover, .stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {{
  background: #86391f; color: #fff6e8; transform: translateY(-1px);
}}
.stButton > button[kind="secondary"] {{
  background: #faedda85; color: #725039; border: 1px solid #ba957674; box-shadow: none;
}}
.stButton > button[kind="secondary"]:hover {{ background: #fcecd4; border-color: #aa7c55;
  color: #725039; }}
.stButton > button:disabled {{ opacity: .45; box-shadow: none; transform: none; }}

/* Cards: warm panel, fine copper-sand border, soft lift. */
[data-testid="stExpander"], [data-testid="stForm"], .aa-card {{
  background: #fbf4e9ee; border: 1px solid #cdae938c; border-radius: 9px;
  box-shadow: 0 15px 40px #7141240b, inset 0 1px 0 #fff9;
}}
.aa-card {{ padding: .9rem 1.1rem; margin: .4rem 0 .9rem; }}
[data-testid="stChatMessage"] {{
  background: #fbf4e9d9; border: 1px solid #cdae938c; border-radius: 9px;
}}
code {{ font-family: var(--mono) !important; color: #7a2e1e !important;
  background: #f3e3cc !important; }}

/* Pills: stage and chips, mono like the portfolio's labels. */
.aa-pill {{
  display: inline-block; padding: .1rem .55rem; border-radius: 5px;
  font: 500 .72rem/1.6 var(--mono); letter-spacing: .03em; border: 1px solid #cdae93;
}}
.aa-pill.ready {{ background: #e9d3b4; color: #5a3a24; }}
.aa-pill.todo {{ background: #f4dfcf; color: #8a3f26; border-color: #d9a88c; }}
.aa-pill.blocked {{ background: #9d472c; color: #fff6e8; border-color: #9d472c; }}
.aa-subset {{
  border-left: 2px solid var(--accent); background: #f6e3cf; color: #5a3a24;
  padding: .5rem .7rem; border-radius: 0 6px 6px 0; font-size: .84rem; margin: .35rem 0;
}}
.aa-icon {{ width: 18px; height: 18px; vertical-align: -3px; margin-right: 6px;
  filter: invert(30%) sepia(24%) saturate(950%) hue-rotate(342deg) brightness(93%); }}

/* New blocks inscribe rather than appear: the portfolio's ink, applied once. */
@keyframes aa-inscribe {{
  0% {{ opacity: 0; clip-path: inset(0 100% 0 0); transform: translate3d(0, 4px, 0); }}
  100% {{ opacity: 1; clip-path: inset(0 0 0 0); transform: none; }}
}}
.stMainBlockContainer [data-testid="stVerticalBlock"] > div {{
  animation: aa-inscribe .7s cubic-bezier(.2, .7, .2, 1) both;
}}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}
</style>
"""

# The motion switch off: like the portfolio's "Pause motion", nothing moves and the ambient
# field keeps two faint static marks.
_PAUSED = """
*, *::before, *::after { animation: none !important; transition: none !important; }
.aa-field .aa-ink { opacity: 0 !important; clip-path: none !important; }
.aa-field .aa-ink.s1, .aa-field .aa-ink.s2 { opacity: .12 !important; }
"""

# st.html sanitises with DOMPurify, which discards a WHOLE style element whose text holds "<"
# followed by a letter, "/" or "!" (C97). Checked before sending rather than found in a browser.
_TAG_LIKE = re.compile(r"<[A-Za-z/!]")


def _inner(css: str) -> str:
    """A stylesheet's rules without its style wrapper."""
    return css.replace("<style>", "").replace("</style>", "")


def motion_on() -> bool:
    return st.session_state.get("motion", True)


def apply(*page_css: str) -> None:
    """Send the theme plus every page's own rules as ONE checked st.html call. Call once per
    render, before anything else. Honours the sidebar motion switch (P14-D10, C97)."""
    rules = _inner(_CSS) + "".join(_inner(css) for css in page_css)
    if not motion_on():
        rules += _PAUSED
    bad = _TAG_LIKE.search(rules)
    if bad:
        raise ValueError(f"stylesheet contains {bad.group()!r}, which makes st.html drop it; "
                         f"reword the comment or percent-encode the data URI")
    st.html(f"<style>{rules}\n</style>")


def eyebrow(text: str) -> None:
    """The portfolio's mono label with its leading rule, above a title."""
    st.html(f'<div class="aa-eyebrow">{text}</div>')


def icon(name: str) -> str:
    """A Lucide icon from ui/static, tinted copper, inline."""
    return f'<img class="aa-icon" src="{STATIC}/{name}.svg" alt="">'


def pill(text: str, kind: str = "ready") -> str:
    """A small mono label. kind: ready | todo | blocked."""
    return f'<span class="aa-pill {kind}">{text}</span>'


def stage_kind(stage: str) -> str:
    """Which pill a DatasetSummary.stage wears. Display only -- the stage text is the engine's
    and is shown verbatim."""
    if "BLOCKED" in stage:
        return "blocked"
    if "ready" in stage:
        return "ready"
    return "todo"
