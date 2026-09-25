"""UI suite guards."""

import pytest


@pytest.fixture(autouse=True)
def no_workspace_expiry(monkeypatch):
    """The real backend sweeps idle web workspaces when it mints an id (P14-O1); never the
    developer's real workspace/ directory from a test."""
    monkeypatch.setenv("ANALYTICS_WORKSPACE_TTL_HOURS", "0")


@pytest.fixture(autouse=True)
def no_model_autofill(monkeypatch):
    """A drafted contract is never filled by a model in a test: webapp/autofill.py is on only in
    the web app. The filter it feeds is tested with scripted answers (tests/test_llm_filter.py)."""
    monkeypatch.setenv("ANALYTICS_AUTOFILL", "off")
