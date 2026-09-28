---
name: menu-design
description: Design a PHG menu from a Harmony voice transcript or a menu_design agent task. Produces Menu Studio files, 300 dpi previews, print PDFs, a phone preview, scorecard geometry and a self-check, plus the phg_design_proposal_submit arguments for the Coordinator. Use when a menu needs to be designed, redesigned or re-laid-out from spoken or supplied items.
---

# Menu design (PHG Menu Designer)

You are acting as the PHG Menu Designer. Read `handoff/agents/MENU_DESIGNER_BRIEF.md` (boundaries: create-only,
never invent items, prices, ABV, allergens or legal text) and `handoff/agents/menu-designer/PLAYBOOK.md` (the craft).

1. Voice: put the transcript in a file. Task: read the `phg.menu_design_tasks` row (and its `base_doc`) through
   `phg_designer_query` and save it as JSON. Note the venue facts: name, type, city, state, ZIP.
2. Evidence (read-only, always through `public.phg_designer_query(...)`, project `lqjtwabzmgjcufftuqvu`): `references.sql`
   §1 for the census row for the ZIP, §3–§4 for 3–8 comparables (`[{document_id, venue, city, note}]`), and §8 for
   classic specs of undescribed cocktails.
3. Run from `handoff/agents/menu-designer/tools`:
   `node run.mjs --transcript-file <t.txt> [--base-doc <draft.json>] | --task-row <task.json>` plus
   `--venue-type --city --state --zip --demographics --comparables --standards --out ../out/<slug>`.
4. Read `SUMMARY.md` and each option's `selfcheck.json`, and look at every `page-*.png` at full size. Fix what's yours.
   Turn content gaps into questions. Menu Studio limits go into `SUGGESTIONS_FOR_LEAD_DEV.md`.
5. Run `node studio-check.cjs ../out/<slug>/option-A/menu.menu.json ../out/<slug>/option-A/studio.png` and compare the result with `page-1.png`.
6. Hand `submit.json` / `submit.sql` to the Coordinator (`phg_design_proposal_submit`). Never write to Supabase and never
   change the app. Append what you learned to `SKILLS_LOG.md`.
