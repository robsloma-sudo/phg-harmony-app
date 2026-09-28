# PHG Menu Designer: toolkit

Turns a Harmony voice note (or an `agent_tasks` payload) into finished menu designs in about 5 seconds:
Menu Studio files, 300 dpi page PNGs, trim and print PDFs, a phone preview, and the `agent_proposals` row.

Read first: the brief (`../MENU_DESIGNER_BRIEF.md`) for boundaries, and `PLAYBOOK.md` for the design craft.

```
Harmony mic ──► phg-speech-transcribe ──► phg-language-interpreter ──► Coordinator ──► agent_tasks (menu_design)
                                                                                           │
             tools/parse-voice.mjs  ◄── transcript / input_payload ◄───────────────────────┘
                     │  items, prices, ABV, flags, lists, subsections, venue, look directions, questions
             tools/design.mjs  ◄── census (phg_census_zcta) + library references (phg_corpus_browse_documents)
                     │  up to 3 looks → Menu Studio doc + style (schema_version 2), section order, promotions,
                     │  contrast fixes, fit/compose using Menu Studio's own flow (tools/layout.mjs)
             tools/render.mjs  → page-N.png (300 dpi) · menu.pdf · menu-print.pdf (bleed + crop) · phone.png
             tools/studio-check.cjs → loads the file into the real Menu Studio (index.html) and exports its canvas
             tools/proposal.mjs → proposal.json + proposal.sql (the designer's only write)
```

## Run it

```bash
cd handoff/agents/menu-designer/tools

# From a voice note, with venue facts, census and references pulled via references.sql
node run.mjs --transcript-file ../examples/casa-luna.voice.txt \
  --venue-type latin_cantina --city Denver --state CO --zip 80205 \
  --demographics ../examples/denver-80205.census.json \
  --comparables ../examples/denver-cantina.refs.json \
  --out ../out/casa-luna

# From an agent_tasks row (or its input_payload, or an edited request.json)
node run.mjs --task task.json --task-id <uuid> --target-record-id <menu_project_id> --out ../out/<job>

# Options: --look noir|cantina|taproom|cellar|grand|coastal|tavern|tropic|minimal|deco
#          --options 1-3   --legal "line one | line two"   --no-render

# Proof against the real app
node studio-check.cjs ../out/casa-luna/option-A/menu.menu.json ../out/casa-luna/option-A/studio.png

# Tests (voice parsing and designer invariants)
node test.mjs
```

Output folder: `SUMMARY.md` (read this first), `request.json` (what was heard, with `heard` text per item),
`proposal.json` / `proposal.sql`, and for each option `option-X/`: `menu.menu.json`, `page-N.png`, `menu.pdf`,
`menu-print.pdf`, `phone.png`, `render.json` (measured overflow). `out/` is git-ignored.

## Files

| File | What it is |
|---|---|
| `tools/parse-voice.mjs` | Spoken menu → structured items. Number words, list intros, serve subsections, glass/bottle, ABV, flags, follow-on remarks, happy-hour times, page directions. Asks instead of guessing. |
| `tools/lexicon.mjs` | Vocabulary: every drinks list plus food sections, flags, formats, tone and colour words, venue types. |
| `tools/design.mjs` | Look ranking (venue × voice tone × census), section order, promotions, badges, brand colours and fonts, contrast, fit and compose. |
| `tools/layout.mjs` | Port of Menu Studio's page flow (`mdcDraw`, `mdcCursorFit`, `mdcSectionHeight`…). Keep in step with `index.html`. |
| `tools/render.mjs` | Full-resolution previews and PDFs from a `.menu.json`; measures lines wider than their column. |
| `tools/studio-check.cjs` | Loads the design into the real Menu Studio headlessly and exports its canvas. |
| `tools/proposal.mjs` | `agent_proposals` row (status, confidence, risk flags, reasoning, evidence) and its INSERT. |
| `styles/looks.mjs` | Ten house looks built only from Menu Studio's fonts, levels and page options. |
| `styles/fonts/` | Stand-ins (OFL) for Georgia, Avenir and Trebuchet in previews. Palatino, Helvetica, Times, Courier and Century Gothic use the URW metric clones (`apt-get install fonts-urw-base35`). |
| `styles/calibrate.mjs` | Re-measures per-font character widths for the fit estimate after a font change. |
| `references.sql` | Read-only census, library and benchmark queries. |
| `examples/` | Sample Harmony transcripts, census rows and reference sets. |

## Environment notes

- Needs Node 22 and Playwright with Chromium (`PLAYWRIGHT_PATH` to override the global install).
- This sandbox's proxy blocks `*.supabase.co`, so census and library data come through the Supabase connector
  (`references.sql`) and are passed in as JSON. In the Coordinator's environment the same queries run directly.
- The designer never uploads previews to storage and never touches the Menu Studio draft. The Coordinator does both
  after review.
