# Harmony Recipe Book Designer: package v0.2.0

A capability of **Harmony** (PHG's single user-facing AI) that turns recipes users enter in the PHG app, plus menu themes, into complete, designed and costed recipe books.

## Contents
```
AGENT_PROMPT.md                         system prompt for the agent
skills/recipe-intake/SKILL.md           pull + normalise recipes, preps, ingredients, themes (read-only)
skills/batch-engineering/SKILL.md       CocktailCalc-style balance, dilution, batches, ml/g
skills/batch-engineering/scripts/phg_bar_math.py   deterministic calculator (preview / what-if)
skills/fat-washing/SKILL.md             fat-wash prep pages, ratios, yield, safety
skills/acid-adjusting/SKILL.md          TA targeting, acid-adjusted juice, solutions, super juice
skills/recipe-costing/SKILL.md          engine-only costing, cost cards, Cost Input Sheet, analysis
skills/recipe-book-design/SKILL.md      theme board, templates, typography, render pipeline
skills/recipe-book-qa-publish/SKILL.md  QA checklist + proposal/approval/verify flow
CHANGELOG.md
```

## Install
1. Use `AGENT_PROMPT.md` as the agent's system prompt.
2. Copy `skills/` into the agent's skills directory, e.g. `/workspace/skills/`. Each skill folder must keep its `SKILL.md`.
3. The agent needs **read** access to Supabase project `lqjtwabzmgjcufftuqvu` through the existing read paths (`phg-execute-readonly`, named RPCs, `phg-costing`, `phg-cocktail-studio`). It needs no service-role key and no write access beyond the approved Edge Function actions.
4. Quick test: `python3 skills/batch-engineering/scripts/phg_bar_math.py demo`

## Not changed
No Supabase data, functions, migrations or app files were modified while building this package.
