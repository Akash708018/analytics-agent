# Automated Analytics Agent (MCP Server)

An autonomous, human-in-the-loop analytics engine built on the **Model Context Protocol (MCP)**, **DuckDB**, and **PostgreSQL**. Designed for Apple Silicon (`arm64`), this agent connects AI clients (Claude Desktop, Streamlit) to structured databases and complex spreadsheets without silent data corruption, memory exhaustion, or hallucinated mutations.

Unlike standard "chat with your CSV" wrappers, this system enforces a **strict two-step human approval gate**, a **declared data contract (grain & keys)**, **isolated workspace catalogs**, and an **append-only cleaning ledger**.

## Architectural Overview

```mermaid
flowchart TD
    Clients[<b>AI CLIENTS</b><br>Track A: Claude Desktop<br>Track B: Streamlit / Web API] -->|MCP Protocol<br>stdio / HTTP| Server

    subgraph Server [<b>FAST_MCP SERVER Python</b>]
        direction TB
        L1[L1: Ingest & Streaming]
        L2[L2: Structure Resolution]
        L3[L3: Dataset Contract]
        L4[L4: Out-of-Core Profiling]
        L5[L5: 2-Step Cleaning Gate]
        L6[L6: Grain & Rule Validation]
        L7[L7: Multi-Tier Analytics]
        L8[L8: Visualizations]
        L9[L9: Report Assembly]
    end

    Server --> DuckDB[(<b>DUCKDB IN-PROCESS ENGINE</b><br>Session/Workspace Scoped)]
    
    DuckDB --> PG[(<b>PostgreSQL</b><br>ATTACH READ_ONLY)]
    DuckDB --> Files[<b>Excel / CSV</b><br>Streamed]
```

## Run it

```bash
uv sync --all-groups
ANALYTICS_UI_BACKEND=real uv run --group ui streamlit run ui/app.py   # the web app, on the engine
uv run pytest -q                                                      # the engine's suite
uv run python scripts/stress_matrix.py --round all                    # 95 files built to break it
```

The web app runs Upload & read → Clean → Contract → Explore / Ask → Files. Nothing loads, changes
or gets computed without a person's approval at each gate. The walkthrough, with what to say at
each screen, is in [`docs/DEMO.md`](docs/DEMO.md); screenshots are in `docs/demo/screens/`.
