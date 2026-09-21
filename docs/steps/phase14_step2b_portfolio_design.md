# Phase 14 Step 2b: the UI carried onto the portfolio's design system

The user asked for the design of akash-portfolio to be reviewed and implemented in the UI. The
portfolio is where the original brief came from -- its README calls the palette "warm sunset" and
its formula-map "staggered ink reveals" -- so the UI moves onto its system rather than beside it.

## The review (akash-portfolio, HEAD d89ac19, read only)

- Tokens (styles.css): light sandstone #f1e3d0, panel #fbf4e9, ink #37271f, muted #756052, line
  #d6bea8, terracotta #9d472c, sunset #c87948, copper #a25934, studio ink #563722; a clay texture
  multiplied over the page at .16.
- Type: Manrope body; DM Serif Display italic for the one emphasised word in a heading
  ("Data, with *purpose.*"); IBM Plex Mono for eyebrows, labels and figures.
- Components: mono eyebrow led by a 28px terracotta rule; cards with a fine sand border, 9px
  radius and soft lift; icon tiles; mono chips; WHAT/WHY/HOW labels.
- Motion (formula-map.css/js): copper field notes that inscribe (clip-path left to right), hold at
  about .3-.4 opacity and dissolve on an 11-13s loop with spread phases; the Agent chapter's
  vocabulary is "raw -> profile -> validate", "{ contract: confirmed }", "propose -> approve ->
  apply", "schema", "input -> tools -> checked output". A "Pause motion" control and reduced
  motion both stop it, leaving two faint marks.
- Icons: one Lucide outline family, tinted copper.
- Found, not changed: the portfolio's Analytics Agent section describes the repository as of
  08/09/2026 -- Phases 0-7 done, 8-14 not started, 26 tools, run_analysis computing nothing.
  All false now. The portfolio has uncommitted work of the user's, so it was not touched.

## What changed in ui/

- theme.py on the portfolio's tokens, fonts, cards, eyebrow, buttons and pills; the one-shot
  inscribe for new blocks; a motion switch in the sidebar (the portfolio's Pause motion).
- journey.py: editorial hero over the portfolio's sunset histogram artwork, masked on both axes;
  chapters as portfolio cards with copper Lucide tiles, still written in one after another; the
  ambient copper field in the Agent's own vocabulary, drawn over content softened in the middle as
  the portfolio's reading view does.
- Screens: eyebrows and an italic terracotta word per title, light sheet grid, Material outline
  icons in navigation instead of emoji, chart palette in terracotta/copper/sand.
- ui/static: 14 Lucide icons (ISC), 3 portfolio diagrams, the clay texture and the hero artwork
  re-encoded to JPEG (3.65 MB -> 0.79 MB, 2.28 MB -> 0.35 MB); provenance in ui/static/SOURCES.md.

## Findings, in order

1. Static assets: 200 for all four probed (enableStaticServing needs a restart to take effect).
2. Hero art showed hard top and right edges: one horizontal mask only. 2.1: two masks,
   intersected. Still hard: the element bled past its box and Streamlit clipped the box edge
   mid-fade. 2.2: art kept inside its box, faded on all four sides. The computed style confirmed
   the mask; the remaining straight line is the pillar and disc in the artwork's own crop.
3. The field was invisible below the hero -- behind opaque cards. 3.1: drawn over the content at
   .3, softened through the middle; measured marks cycling at .24.
4. The eyebrow was clipped at line-height 1. 4.1: 1.5, no negative margin.
5. The new motion test passed with the switch disconnected: it searched for text the Journey's
   own reduced-motion query already contains (P14-D14). 5.1: compares the stylesheet with motion
   on and off; fails when disconnected, passes connected.
