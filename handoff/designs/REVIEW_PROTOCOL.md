# Fast review protocol (Rob, 2026-09-28: every round, creation to review, within 5 minutes)

You have **90 seconds and at most 6 tool calls**, plus **one extra Read for a reference image** (critics). Do not
re-render; do not run Playwright; do not browse the web.

1. Read handoff/agents/MENU_DESIGN_SCORECARD.md (criteria table, hard gates 1a, restraint check 1c, bands).
2. Open the round folder's preview PNG(s) with Read, and read layout.json (its `measured_checks` come from the
   render script, not from the designer's opinion), doc.json and proposal.md as needed for your lens.
   Critics: also open two PNGs from handoff/designs/references/rob-2026-09-28/ (for example ref-01 and one of ref-04..09)
   (the extra Read covers one; fit the other in the 6 calls) and compare against them. They are the quality bar: 90+
   means the design stands beside them.
3. Accuracy reviewers only: at most 2 gateway queries (`select public.phg_designer_query($q$...$q$)`,
   ToolSearch "select:mcp__Supabase__execute_sql", project_id `lqjtwabzmgjcufftuqvu`) to verify the facts your lens
   targets. Garnish / glass / method live in phg.recipe_versions (columns garnish, glassware, method) for the
   menu_items.current_recipe_version_id of each item (join: phg.menu_items.current_recipe_version_id = phg.recipe_versions.id; a failed or empty lookup is NOT evidence that a fact is unsourced); component rows alone are not the whole recipe.
4. Score ONLY your criteria, 0-100. **Be Roger-Ebert tough (Rob, 2026-09-28): the critics were too soft.**
   Calibration anchors - use them, do not drift upward:
   - 90-94: stands beside Rob's reference boards (handoff/designs/references/rob-2026-09-28/).
   - 95-100: award-winning, the best bar menus in the country (Dead Rabbit, Death & Co, Pujol, Pentagram / Mucca /
     Studio Newwork-level craft). Almost nothing earns this.
   - 85-89: a top agency would put it in its portfolio: a clear, memorable concept executed flawlessly.
   - 75-84: strong professional work, but you have seen it before.
   - 60-74: competent and clean but safe, template-like, forgettable. **"Measures correctly" alone lands here.**
   - below 60: amateur or broken.
   Start every criterion at 60 and make the design EARN each point above it. Correct alignment, even margins and
   matching prices are the price of entry, not a reason for a high score. Penalise safe, incremental polish.
   Do not ask what earlier rounds scored.
   Critic reviewers ALSO score criterion "15" (Design concept): is there a bold, ownable big idea - a visual
   narrative or system rooted in this venue and its culture - that makes the menu unforgettable? A tidy two-column
   list with festive trim is 60-65. Name the single boldest idea the design is missing in your top_problem.
   Critics ALSO score criterion "16" (Art direction and image system): creative thesis, one illustration grammar and
   image treatment, word-image integration, intentional crop, bleed, texture at size, materiality. And name at least one
   device to REMOVE (restraint check, scorecard 1c): boldness is not accumulation.
   Criterion 5 is focal order and reading path by hierarchy and grouping; never reward "sweet spot" placement.
   Every reviewer reports each hard gate in its lens as "pass" or "fail" (scorecard 1a). A failed gate blocks approval
   regardless of scores: content_integrity, legibility, accessibility (contrast at the worst pixel over the art),
   menu_item_association, environmental_legibility.
5. Reply with ONLY this JSON (no prose before or after), fixes one sentence each, max 5, ranked by score impact:
   {"reviewer":"critic|content|accuracy","lens":"...","scores":{"<criterion>":n,...},"gates":{"<gate_key>":"pass|fail",...},"top_problem":"...","fixes":["..."]}

Criteria: critic 1,2,3,4,5,6,7,10,15,16 | content 3,5,8,9,10 | accuracy 10,11,12,13,14.
Gates: critic legibility, accessibility, menu_item_association, environmental_legibility | content content_integrity,
menu_item_association | accuracy content_integrity, menu_item_association. Do not edit any file.
