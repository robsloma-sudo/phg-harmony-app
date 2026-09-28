# PHG Menu Designer: toolkit

Turns a Harmony voice note, or a `phg.menu_design_tasks` row, into finished menu designs in about 5 seconds:
Menu Studio files, 300 dpi page PNGs, trim and print PDFs, a phone preview, measured scorecard geometry, a
self-check, and the `phg_design_proposal_submit` arguments for the Coordinator.

Read first: the brief (`../MENU_DESIGNER_BRIEF.md`) for boundaries, and `PLAYBOOK.md` for the design craft.

```
Harmony mic ─► phg-speech-transcribe ─► phg-language-interpreter ─► (suggested S9) handoff.requestDesignPayload()
   ─► phg-menu-design {action:'request_design'} ─► phg_design_task_create ─► phg.menu_design_tasks (base_doc = the draft)
                                                                                   │ read via phg_designer_query
   tools/handoff.taskToRequest ─► tools/draft.mjs (keeps ids/recipe links, merges voice items & edits, recipe-based
   descriptions) or design.mjs buildDoc (fresh) ─► standards.mjs (classic specs, labelled) ─► design.mjs fit/compose
   (Menu Studio flow port: tools/layout.mjs) ─► render.mjs (300 dpi PNG, PDFs, phone, measured p_layout)
   ─► selfcheck.mjs (scorecard §4 + content + local phg_design_doc_check) ─► submit.json / submit.sql
   ─► Coordinator: phg_design_proposal_submit(… p_layout) ─► Design Critic + Menu Content Reviewer (each avg > 80)
   ─► approve ─► app Designer panel "Apply to draft" (Sync PHG)
```

## Run it

```bash
cd handoff/agents/menu-designer/tools
node test.mjs                                   # regression tests (must all pass)

# Voice note (user side): writes request_design.json (the task the app would create) + the proposal for it
node run.mjs --transcript-file ../examples/casa-luna.voice.txt --venue-type latin_cantina --city Denver --state CO \
  --zip 80205 --demographics ../examples/denver-80205.census.json --comparables ../examples/denver-cantina.refs.json \
  --standards ../examples/classic-specs.json --out ../out/casa-luna

# Voice edit on the venue's existing draft
node run.mjs --transcript-file ../examples/live-draft.voice.txt --base-doc ../examples/live-draft-ddc4bb5b.base_doc.json \
  --venue-type cocktail_lounge --out ../out/live-draft

# A real task row (read through phg_designer_query)
node run.mjs --task-row task.json --demographics census.json --comparables refs.json --standards specs.json --out ../out/<task>

# Proof against the real app, and a stand-alone self-check
node studio-check.cjs ../out/casa-luna/option-A/menu.menu.json ../out/casa-luna/option-A/studio.png
node selfcheck.mjs ../out/casa-luna/option-A/layout.json ../out/casa-luna/option-A/menu.menu.json
```

Output: `SUMMARY.md` (read first), `request_design.json` (voice), `request.json`, `submit.json` + `submit.sql`
(`phg_design_proposal_submit` arguments with `p_layout`, for the Coordinator), and per option `option-X/`:
`menu.menu.json`, `page-N.png` (300 dpi), `menu.pdf`, `menu-print.pdf`, `phone.png`, `layout.json`, `selfcheck.json`,
`render.json`. `out/` is git-ignored. Nothing contains the project sync token (`stripSecrets`).

## Files

| File | What it is |
|---|---|
| `tools/parse-voice.mjs` | Spoken menu → structured items. Number words, list intros, serve subsections, glass/bottle, ABV, flags, follow-on remarks, happy-hour times, page directions. Asks instead of guessing. |
| `tools/lexicon.mjs` | Vocabulary: every drinks list plus food sections, flags, formats, tone and colour words, venue types. |
| `tools/design.mjs` | Look ranking (venue × voice tone × census), section order, promotions, badges, brand colours and fonts, contrast, fit and compose. |
| `tools/layout.mjs` | Port of Menu Studio's page flow (`mdcDraw`, `mdcCursorFit`, `mdcSectionHeight`…). Keep in step with `index.html`. |
| `tools/render.mjs` | Full-resolution previews and PDFs from a `.menu.json`; measures lines wider than their column. |
| `tools/studio-check.cjs` | Loads the design into the real Menu Studio headlessly and exports its canvas. |
| `tools/proposal.mjs` | Proposal content: status (`needs_input` when content is missing), confidence, risk flags, reasoning, evidence. |
| `tools/handoff.mjs` | Voice → `request_design` body; task row → request; proposal → `phg_design_proposal_submit` args; `stripSecrets`; local `docCheck` (same rules as `phg_design_doc_check`). |
| `tools/draft.mjs` | Designing from the venue's draft: keeps item objects, merges voice items/edits, recipe-component descriptions (visibility-aware), category-specific content questions. |
| `tools/standards.mjs` | Classic-spec descriptions for items without one (labelled `standard`, confirmation asked). |
| `tools/selfcheck.mjs` | Scorecard §4 measured checks + content rules + local automatic check. |
| `SUGGESTIONS_FOR_LEAD_DEV.md` | App changes the designer needs (proposals only, relayed by Rob). |
| `SKILLS_LOG.md` | Running log of skills, work and learning, for the next agent. |
| `knowledge/` | 53-source evidence base: menu theory, typography/grids/colour, branding/lists/formats/legal. |
| `styles/looks.mjs` | Ten house looks built only from Menu Studio's fonts, levels and page options. |
| `styles/fonts/` | Stand-ins (OFL) for Georgia, Avenir and Trebuchet in previews. Palatino, Helvetica, Times, Courier and Century Gothic use the URW metric clones (`apt-get install fonts-urw-base35`). |
| `styles/calibrate.mjs` | Re-measures per-font character widths for the fit estimate after a font change. |
| `references.sql` | Read-only census, library, benchmark and classic-spec queries (always wrapped in `phg_designer_query`). |
| `examples/` | Sample Harmony transcripts, census rows and reference sets. |

## Environment notes

- Needs Node 22 and Playwright with Chromium (`PLAYWRIGHT_PATH` to override the global install).
- This sandbox's proxy blocks `*.supabase.co`, so census and library data come through the Supabase connector
  (`references.sql`) and are passed in as JSON. In the Coordinator's environment the same queries run directly.
- The designer never uploads previews to storage, never writes to Supabase and never changes the app. The Coordinator
  files proposals; the app applies approved ones. App changes are only ever suggestions (`SUGGESTIONS_FOR_LEAD_DEV.md`).
