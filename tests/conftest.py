"""Suite-wide guards."""

import urllib.request

import pytest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """No test reaches the internet. A leaked API key once made a test call Gemini for real
    (P14-D24); now any urlopen a test has not replaced itself raises. Tests that exercise the
    HTTP layer monkeypatch urlopen on top of this. Localhost servers (the FastMCP facts test)
    use httpx, not urllib, and are unaffected."""
    def refuse(*args, **kwargs):
        raise RuntimeError("a test tried to reach the network through urllib")
    monkeypatch.setattr(urllib.request, "urlopen", refuse)


@pytest.fixture(autouse=True)
def no_workspace_expiry(monkeypatch):
    """A RealBackend sweeps idle web workspaces when it mints an id (P14-O1). No test may sweep
    the developer's real workspace/ directory; the sweep's own tests point it at a tmp root."""
    monkeypatch.setenv("ANALYTICS_WORKSPACE_TTL_HOURS", "0")
