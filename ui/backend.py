"""Which Backend the UI talks to. The only place that knows there is more than one.

    ANALYTICS_UI_BACKEND=fake   (default) ui.fake_backend.FakeBackend, in memory
    ANALYTICS_UI_BACKEND=real   analytics_agent.webapp.real_backend.RealBackend, the engine

One instance per server process, shared by every browser session: st.cache_resource. Sessions are
kept apart by workspace id, which every call carries.
"""

from __future__ import annotations

import os

import streamlit as st

from analytics_agent.webapp.contract import Backend


@st.cache_resource
def get_backend() -> Backend:
    choice = os.environ.get("ANALYTICS_UI_BACKEND", "fake").strip().lower()
    if choice == "real":
        from analytics_agent.webapp.real_backend import RealBackend  # written engine-side
        return RealBackend()
    if choice != "fake":
        raise ValueError(f"ANALYTICS_UI_BACKEND={choice!r}; expected 'fake' or 'real'")
    from ui.fake_backend import FakeBackend
    return FakeBackend()
