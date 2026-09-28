# Fast review protocol (Rob, 2026-09-28: every round, creation to review, within 5 minutes)

You have **90 seconds and at most 6 tool calls**. Do not re-render; do not run Playwright; do not browse the web.

1. Read handoff/agents/MENU_DESIGN_SCORECARD.md (criteria table + bands only).
2. Open the round folder's preview PNG(s) with Read, and read layout.json (its `measured_checks` come from the
   render script, not from the designer's opinion), doc.json and proposal.md as needed for your lens.
3. Accuracy reviewers only: at most 2 gateway queries (`select public.phg_designer_query($q$...$q$)`,
   ToolSearch "select:mcp__Supabase__execute_sql", project_id `lqjtwabzmgjcufftuqvu`) to verify the facts your lens
   targets. Garnish / glass / method live in phg.recipe_versions (columns garnish, glassware, method) for the
   menu_items.current_recipe_version_id of each item; component rows alone are not the whole recipe.
4. Score ONLY your criteria, 0-100, strictly and absolutely by the bands (95+ = portfolio-grade a top agency would
   sign). Do not ask what earlier rounds scored.
5. Reply with ONLY this JSON (no prose before or after), fixes one sentence each, max 5, ranked by score impact:
   {"reviewer":"critic|content|accuracy","lens":"...","scores":{"<criterion>":n,...},"top_problem":"...","fixes":["..."]}

Criteria: critic 1,2,3,4,5,6,7,10 | content 3,5,8,9,10 | accuracy 10,11,12,13,14. Do not edit any file.
