# ui/static -- where each file came from

Copied 22/09/2026 from the author's portfolio (akash-portfolio, `dist/assets/`, HEAD d89ac19), so
the product and the portfolio share one visual system ("warm data studio").

- `*.svg` except the three below: official Lucide icons, unmodified, commit
  58ef6830c6fdf6374b751ab28b147a921bd31b34 (see the portfolio's ICON-SOURCES.json and
  AMBIENT-ICON-SOURCES.json). ISC licence: `LUCIDE-LICENSE`.
- `neural-network.svg`, `normal-distribution.svg`, `regression-scatter.svg`: code-native diagrams
  made for the portfolio (its ARTWORK.md). Illustrative concepts, not results.
- `clay-texture.jpg`, `observatory-hero.jpg`: the portfolio's generated artwork (prompts in its
  ARTWORK.md), re-encoded from PNG to JPEG with macOS `sips` (quality 78 and 82) to keep the
  repository small: 3.65 MB -> 0.79 MB and 2.28 MB -> 0.35 MB.

Served by Streamlit at /app/static/<name> (`server.enableStaticServing`, .streamlit/config.toml).
