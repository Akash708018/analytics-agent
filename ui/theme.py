"""The look: a warm sunset over dusk, and ink that writes itself onto parchment.

Everything visual lives here -- colours, fonts, the global stylesheet and the ink animation -- so
a screen module only ever says `theme.apply()` and uses the class names below. No screen writes
its own CSS.

The ink effect: new content does not pop in, it surfaces -- blurred, spaced and transparent, then
drawing together into sharp text, the way writing appears on an enchanted page. It is CSS only
(no JavaScript), so it works in `st.html`, costs nothing on rerun, and is switched off for anyone
whose system asks for reduced motion.
"""

from __future__ import annotations

import re

import streamlit as st

# Sunset palette. Dusk at the top of the sky, fire at the horizon, parchment for reading.
DUSK = "#1c1226"          # page background, deepest
DUSK_2 = "#2a1a35"        # raised surfaces
PLUM = "#5b2a55"          # borders, quiet accents
ROSE = "#d6547a"          # sunset magenta
EMBER = "#ff7e5f"         # primary: coral ember
PEACH = "#feb47b"         # secondary warm
GOLD = "#ffd48a"          # highlights, headings
PARCHMENT = "#f6e7d0"     # body text on dusk
PARCHMENT_DIM = "#cdb59a"  # muted text
INK = "#3a2314"           # ink on parchment
PAPER = "#f3e3c3"         # parchment panel

SUNSET = f"linear-gradient(120deg, {ROSE} 0%, {EMBER} 45%, {PEACH} 75%, {GOLD} 100%)"

_FONTS = (
    "https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700"
    "&family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500"
    "&family=Inter:wght@400;500;600&display=swap"
)

_CSS = f"""
<style>
@import url('{_FONTS}');

:root {{
  --dusk: {DUSK}; --dusk-2: {DUSK_2}; --plum: {PLUM}; --rose: {ROSE}; --ember: {EMBER};
  --peach: {PEACH}; --gold: {GOLD}; --parchment: {PARCHMENT}; --parchment-dim: {PARCHMENT_DIM};
  --ink: {INK}; --paper: {PAPER}; --sunset: {SUNSET};
}}

/* The sky: dusk overhead, the last of the sun low on the horizon. */
.stApp {{
  background:
    radial-gradient(120% 60% at 50% 115%, rgba(255,126,95,.28) 0%, rgba(214,84,122,.14) 35%,
                    rgba(28,18,38,0) 70%),
    radial-gradient(80% 50% at 85% -10%, rgba(91,42,85,.55) 0%, rgba(28,18,38,0) 60%),
    var(--dusk);
  background-attachment: fixed;
  color: var(--parchment);
  font-family: 'Inter', system-ui, sans-serif;
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #24162e 0%, #1a1022 100%);
  border-right: 1px solid rgba(255,126,95,.18);
}}

h1, h2, h3, .aa-title {{
  font-family: 'Cinzel', Georgia, serif !important;
  letter-spacing: .04em;
  color: var(--gold) !important;
}}
h1 {{
  background: var(--sunset); -webkit-background-clip: text; background-clip: text;
  color: transparent !important;
}}
p, li, label, .stMarkdown {{ color: var(--parchment); }}
.aa-muted {{ color: var(--parchment-dim); }}

/* Buttons: the horizon. */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  background: var(--sunset); color: #2a130c; border: 0; border-radius: 999px;
  font-weight: 600; letter-spacing: .02em; box-shadow: 0 6px 22px rgba(255,126,95,.25);
  transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  transform: translateY(-1px); filter: brightness(1.06);
  box-shadow: 0 10px 28px rgba(255,126,95,.38); color: #2a130c;
}}
.stButton > button:disabled {{ filter: grayscale(.7) brightness(.7); box-shadow: none; }}
.stButton > button[kind="secondary"] {{
  background: transparent; color: var(--peach); border: 1px solid rgba(254,180,123,.45);
  box-shadow: none;
}}

/* Inputs and cards sit on a warm glass. */
[data-testid="stExpander"], [data-testid="stForm"], .aa-card {{
  background: rgba(42,26,53,.72); border: 1px solid rgba(255,126,95,.18); border-radius: 16px;
  backdrop-filter: blur(6px);
}}
.aa-card {{ padding: 1rem 1.2rem; margin: .4rem 0 1rem; }}
[data-testid="stChatMessage"] {{
  background: rgba(42,26,53,.6); border: 1px solid rgba(255,126,95,.14); border-radius: 16px;
}}
[data-baseweb="tab-list"] button[aria-selected="true"] {{ color: var(--ember); }}

/* Every new block surfaces like ink rather than appearing. */
@keyframes aa-ink-in {{
  0%   {{ opacity: 0; filter: blur(5px); transform: translateY(6px); }}
  60%  {{ opacity: .85; filter: blur(.8px); }}
  100% {{ opacity: 1; filter: none; transform: none; }}
}}
.stMainBlockContainer [data-testid="stVerticalBlock"] > div {{
  animation: aa-ink-in .8s ease-out both;
}}

/* Stage and note pills. */
.aa-pill {{
  display: inline-block; padding: .12rem .6rem; border-radius: 999px; font-size: .78rem;
  font-weight: 600; letter-spacing: .02em; margin-right: .35rem;
}}
.aa-pill.ready {{ background: rgba(255,212,138,.18); color: var(--gold); }}
.aa-pill.todo {{ background: rgba(214,84,122,.18); color: #ff9db8; }}
.aa-pill.blocked {{ background: rgba(255,90,70,.22); color: #ffb3a6; }}
.aa-subset {{
  border-left: 3px solid var(--ember); background: rgba(255,126,95,.1);
  padding: .5rem .7rem; border-radius: 0 10px 10px 0; font-size: .86rem; margin: .35rem 0;
}}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}
</style>
"""


def apply(*page_css: str) -> None:
    """Inject the stylesheet -- the theme plus any page's own rules -- as ONE st.html call.

    st.html sanitises with DOMPurify, which DISCARDS A WHOLE <style> ELEMENT whose text holds
    a "<" followed by a letter or "/" -- a CSS comment mentioning <p>, an unencoded SVG data URI.
    Measured in the browser 22/09/2026: every rule vanished, the theme's included, the moment
    one such character entered the block. It first looked like a race between two blocks; it
    was not. So the rules are checked here and a violation raises rather than silently
    un-theming the app. Call once per render, before anything else.
    """
    extra = "".join(_inner(css) for css in page_css)
    rules = _inner(_CSS) + extra
    bad = _TAG_LIKE.search(rules)
    if bad:
        raise ValueError(f"stylesheet contains {bad.group()!r}, which makes st.html drop it; "
                         f"reword the comment or percent-encode the data URI")
    st.html(f"<style>{rules}\n</style>")


_TAG_LIKE = re.compile(r"<[A-Za-z/!]")


def _inner(css: str) -> str:
    """A stylesheet's rules without its <style> wrapper."""
    return css.replace("<style>", "").replace("</style>", "")


def pill(text: str, kind: str = "ready") -> str:
    """A small rounded label. kind: ready | todo | blocked."""
    return f'<span class="aa-pill {kind}">{text}</span>'


def stage_kind(stage: str) -> str:
    """Which pill a DatasetSummary.stage wears. Display only -- the stage itself is the
    engine's word and is shown verbatim."""
    if "BLOCKED" in stage:
        return "blocked"
    if "ready" in stage:
        return "ready"
    return "todo"
