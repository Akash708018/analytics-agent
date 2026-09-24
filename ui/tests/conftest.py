"""UI suite guards."""

import pytest


@pytest.fixture(autouse=True)
def no_workspace_expiry(monkeypatch):
    """The real backend sweeps idle web workspaces when it mints an id (P14-O1); never the
    developer's real workspace/ directory from a test."""
    monkeypatch.setenv("ANALYTICS_WORKSPACE_TTL_HOURS", "0")
