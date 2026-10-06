# CHANGELOG — Harmony Recipe Book Designer

## v0.2.0 (2026-10-06)

**Changed (owner decisions)**
- **House ounce = 30 ml** across the prompt, skills and `phg_bar_math.py`. The script output field `oz_us` was renamed `oz`.
- Added `floz_us` (29.5735 ml), used only for purchase package sizes printed in US fl oz, so invoice costs stay exact (a 12 fl oz can = 355 ml).
- **Prices come from invoices (automatic) and manual entry/edits.** Both are documented in recipe-costing §3 with precedence rules.
- **New principle: automated by default, human-editable everywhere.** Human edits are stored as overrides, always win, and are never overwritten by re-runs.
- Dilution constants marked low priority (owner: negligible for now). The formula stays as is.

**Database:** not changed. The migration to set `phg.units.oz` = 30 and add `floz_us` was blocked by tool permission. Every unit-using table is empty, so the change is safe once it's allowed.

**Pending proposal:** update the `phg-invoice-intake` parser to output `floz_us` for container sizes in fl oz (its unit list currently only offers `oz`). Needs approval; deploy after the unit migration.

## v0.1.0 (2026-10-06)

**Added**
- `AGENT_PROMPT.md` and seven skills: recipe-intake, batch-engineering, fat-washing, acid-adjusting, recipe-costing, recipe-book-design, recipe-book-qa-publish.
- `phg_bar_math.py`: deterministic calculator for balance, dilution, batches, fat washes, acid adjustment and a cost preview. Standard library only.
- Recipes are built CocktailCalc-style: Liquid Intelligence dilution → final ABV / volume / TA / Brix → style corridor → batch by quantity or volume.

**Tests**
- Daiquiri 60/22.5/22.5 → 51.9% dilution, 15.0% ABV, 8.9 g sugar/100 ml, 0.85% TA.
- 750 ml bottle fill → 1 bottle.
- Brown-butter wash 113 g/750 ml → 15.1% w/v.
- OJ → lime 50 g/L (Arnold publishes 52).

**Known findings**
- `purchase_costs`, `prep_recipes`, invoice lines and inventory are empty.
- `pr_champagne_acid` has no lines.
- dash/drop have no ml standard.
- `send_to_menu_studio` is not built yet.
