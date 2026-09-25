"""Track B: the browser front door to the analytics engine. Run from the repository root:

    uv run --group ui streamlit run ui/app.py

ANALYTICS_UI_BACKEND=fake (the default) runs every screen on in-memory data; =real runs the engine.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# The web app is where a model fills a new dataset's contract form (webapp/autofill.py); tests
# and scripts leave it off. ANALYTICS_AUTOFILL=off in the environment turns it off here too.
os.environ.setdefault("ANALYTICS_AUTOFILL", "on")

# `streamlit run ui/app.py` puts ui/ on the path, not the repository root; the ui package needs it.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from ui import components, journey, theme  # noqa: E402
from ui.screens import chat, clean, contract, explore, files, ingest  # noqa: E402

st.set_page_config(page_title="Analytics Agent", page_icon=":material/insights:", layout="wide")
# One stylesheet per render, every page's rules included: see theme.apply.
theme.apply(journey.stylesheet(), ingest.stylesheet())

pages = [
    # One outline icon family throughout, as the portfolio does with Lucide.
    st.Page(journey.render, title="Journey", icon=":material/route:", url_path="journey",
            default=True),
    st.Page(ingest.render, title="Upload & read", icon=":material/upload_file:", url_path="upload"),
    st.Page(clean.render, title="Clean", icon=":material/cleaning_services:", url_path="clean"),
    st.Page(contract.render, title="Contract", icon=":material/verified:", url_path="contract"),
    st.Page(explore.render, title="Explore", icon=":material/query_stats:", url_path="explore"),
    st.Page(chat.render, title="Ask", icon=":material/forum:", url_path="ask"),
    st.Page(files.render, title="Files", icon=":material/folder_open:", url_path="files"),
]
page = st.navigation(pages)
components.sidebar()
page.run()
