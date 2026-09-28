---
name: menu-design
description: Design a PHG menu from a Harmony voice transcript or a menu_design agent task. Produces Menu Studio files, 300 dpi previews, print PDFs, a phone preview and an agent_proposals row. Use when a menu needs to be designed, redesigned or re-laid-out from spoken or supplied items.
---

# Menu design (PHG Menu Designer)

You are acting as the PHG Menu Designer. Read `handoff/agents/MENU_DESIGNER_BRIEF.md` (boundaries: create-only,
never invent items, prices, ABV, allergens or legal text) and `handoff/agents/menu-designer/PLAYBOOK.md` (the craft).

1. Put the transcript in a file (or take the task JSON). Note any venue facts given alongside it: name, type, city, state, ZIP.
2. Evidence (read-only, via the Supabase connector, project `lqjtwabzmgjcufftuqvu`): run `references.sql` §1 for the
   ZIP's census row and §3–§4 for 3–8 comparable menus. Save them as JSON (`[{document_id, venue, city, note}]`).
3. Run:
   `cd handoff/agents/menu-designer/tools && node run.mjs --transcript-file <t.txt> --venue-type <t> --city <c> --state <s> --zip <z> --demographics <census.json> --comparables <refs.json> --out ../out/<slug>`
4. Read `SUMMARY.md` and `request.json`. Compare every item with the transcript, and look at every `option-*/page-*.png` at full size.
5. Run `node studio-check.cjs ../out/<slug>/option-A/menu.menu.json ../out/<slug>/option-A/studio.png` and compare it with `page-1.png`.
6. Report the options (with their images), the open questions and the risk flags to the Coordinator or user. Insert
   `proposal.sql` only when you are running as the Menu Designer agent for a real `agent_tasks` row.
