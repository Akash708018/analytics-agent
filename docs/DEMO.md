# Demo script

An eight-minute walk through the web app on the real engine, with what to say at each screen.
Everything below was driven in a real browser (headless Chromium) on 24/09/2026. The
screenshots are in `docs/demo/screens/`, and `scripts/browser_check.py` repeats the walk.

## Before you present

```bash
uv sync --all-groups                                   # once
ANALYTICS_UI_BACKEND=real uv run --group ui streamlit run ui/app.py
```

Open http://localhost:8501. The sidebar should read "Nothing loaded yet".

- **The assistant on Ask** needs `GEMINI_API_KEY` (or `GROQ_API_KEY`) in `.env` at the repository
  root, then a restart. Without a key, everything except Ask works, and **Explore** covers
  everything Ask would compute. If the Wi-Fi or the quota fails mid-demo, switch to Explore.
- **A clean start:** tick "I want to empty this workspace", then press **Reset workspace**.
- **A rehearsal:** `uv run --group ui --with playwright python scripts/browser_check.py` walks
  every screen in a headless browser and exits 1 if any screen raises.

## The one sentence

> "It's an analytics engine that refuses to guess. A person approves how a file is read, every
> change to the data and what each column means, before a single number is computed. Every number
> it shows can be traced back to the call that made it."

## The walk (about 8 minutes)

| # | Screen | Do | Say |
|---|---|---|---|
| 1 | **Journey** | Scroll once. | "Sixteen chapters, 27/08 to 24/09. Every figure on this page was printed by a command: 27 analyses, 76/76 on the eval, 95 stress datasets, 0 crashes." |
| 2 | **Upload & read** | Click **Try the sample workbook**. | "This is a real messy sheet: two stacked header rows under merged labels. The engine proposes how to read it (header rows glow) and says why, under each assumption. Nothing has loaded yet." |
| 3 | | Click **Confirm and load**. | "Only now does it load: 150 rows. The sidebar shows the stage: loaded, no contract." |
| 4 | **Clean** | Open the SQL expander, then click **Apply 1 step(s)**. | "Every fix is proposed with its exact SQL and counts, and runs only when ticked. A fix that loses information is never pre-ticked and shows what it would lose. The old table is kept." |
| 5 | **Explore** (before the contract) | Open it. | "It refuses. No contract, no numbers. That's the gate." |
| 6 | **Contract** | Grain: `one row = one order`. Window: 2024-01-01 to 2024-12-31. Aggregations: units **sum**, unit_price **none**, revenue **sum**. Definitions: one line each. Then **Confirm contract**. | "There's no default aggregation on purpose: summing a unit price means nothing, and only a person knows that. Confirm checks the form as it is and names anything still missing." |
| 7 | **Explore** | Pick **top_n** and run it. Then **trend**. | "The same engine calls the AI assistant makes, with no model in between. Each result says what it ran over and what it left out, and the chart comes with its numbers in words." |
| 8 | | Open **Build the report** and click it. | "Nine sections, always nine. Every number is traced to the exact call that made it." |
| 9 | **Ask** (with a key) | Ask: *Which region brings in the most revenue, and is the difference real?* | "The model picks the analyses; open **What I did** to see every tool call, refusals included. It can't load, clean or confirm anything: those need a person's click." |
| 10 | **Files** | Scroll. | "Every chart, table and report, each with the engine's own account of it." |

## If they ask

- **"How do you know it's right?"** There are 1,949 automated tests (1,900 engine, 49 UI) and a 40-question eval with
  answers worked out without the tool (76/76). A stress run covered 95 generated files built to
  break it: Windows exports, pasted headers, totals rows, two-digit years, merged cells and
  20-digit ids. It found 34 bugs, all fixed, and a final round found none. `docs/stress/REPORT.md`
  has the details.
- **"What stops it from making numbers up?"** Every number comes from a tool reply. The model
  never computes anything itself, and a tool refuses without a confirmed contract.
- **"Does it work in Claude Desktop?"** Yes. That's Track A: the same engine as an MCP server with
  29 tools. The web app is Track B.
- **"What's not done?"** Public hosting (logins, deployment), and Postgres in the web app (it
  works through MCP).
