"""Central settings. Every limit lives here, not scattered in code."""
from pathlib import Path

SERVER_NAME = "analytics-agent"
SERVER_VERSION = "0.1.0"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"

DEFAULT_WORKSPACE_ID = "local"

# Size gates -- set from your RAM (Phase 0, Part 9).
MAX_EXCEL_MB = 100
WARN_CSV_MB = 250

# Postgres source used for testing.
TEST_PG_DSN = "dbname=testdb"   