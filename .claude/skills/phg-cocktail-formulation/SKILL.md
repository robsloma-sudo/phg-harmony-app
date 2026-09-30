---
name: phg-cocktail-formulation
description: PHG cocktail formulation and sensory balance - quantitative sugar, titratable acid (TA), sugar/acid ratio, ABV, dilution, service temperature and frozen-drink reasoning from the live phg_mix formulation tables. Use for any question or task about a drink being sweet, dry, sour, tart or unbalanced; Brix, syrup strength, sugar, acid, TA, pH, acid adjustment, cordials, refractometer readings; dilution or ABV; frozen/slush cocktails; liqueur sweetness; comparing or optimizing recipes; batching balance; or when editing the phg_mix formulation tables, profiles, aliases or recipe_balance_analysis.
---

# PHG Cocktail Formulation & Sensory Balance

Full brief (source of this skill, verified against live Supabase 2026-09-30):
`handoff/PHG_FORMULATION_HANDOFF.txt`. Read its section for a topic before answering in depth.

You are a quantitative formulation specialist. Resolve what each ingredient actually contributes,
calculate only what the data supports, keep uncertainty visible, and finish at the service condition.
Balance is a multi-variable system, not an ounce ratio.

## Data (Supabase project lqjtwabzmgjcufftuqvu, schema phg_mix, read-only)

| Object | Use |
|---|---|
| `v_recipe_balance_coverage` | FIRST: is the recipe resolved enough to calculate? |
| `v_recipe_balance_inputs` | per-line profile, composition, `resolution_state` (mapped / mapped_needs_composition / unmapped) |
| `ingredient_profiles`, `ingredient_profile_aliases` | composition (abv_pct, brix_deg, sugar_g_100ml/100g, ta_g_100ml, ph, basis, confidence, verification, notes) |
| `formulation_claims` | principles by `topic`; read `limitations`, not just `statement` |
| `formulation_evidence` join `sources` | provenance and evidence level |
| `balance_profiles` | reference builds and operating windows (sour start, frozen 13-15 Brix / 0-10% ABV, shaken -10..-5 C, stirred -7..-0.5 C, IBA builds) |
| `recipes`, `recipe_lines` | the recipe itself |
| `recipe_balance_analysis` | versioned results; EMPTY on purpose until coverage is sufficient |

All six formulation tables have RLS with a `harmony_read` SELECT policy for `phg_harmony_reader`; the views are
`security_invoker`. Harmony's registered capability is `cocktail_development` (there is no
`cocktail_balance_formulation` row; don't create one without Rob's approval).

## Read sequence

1. Identify the recipe (`recipes`, `recipe_lines`).
2. Check coverage (`v_recipe_balance_coverage`). If lines are unmapped or unresolved, name them exactly.
3. Read the line inputs (`v_recipe_balance_inputs ... order by position`).
4. Resolve ingredients through aliases. Never upgrade a generic term to a specific product.
5. Calculate only what's supported (formulas below).
6. Pull the relevant `formulation_claims` by topic and their evidence.
7. Compare against the right `balance_profiles` entry. Explain it if the style doesn't match (e.g. frozen vs shaken).
8. State assumptions and evidence level. Give a sensory reading and one lever to test. Taste at service temperature.

## Calculator (live since 2026-09-30)

- `select phg_mix.calc_recipe_balance('rx_...', 20)`: read-only (SECURITY INVOKER; granted to `phg_harmony_reader`).
  The second argument is an optional dilution-% scenario. It returns:
  - `complete` flags for volume, sugar, TA and ABV;
  - `blockers` and `unresolved` lists, naming the exact ingredient;
  - pre-dilution totals and concentrations, with ranges where a profile is a range (e.g. a 2:1 syrup whose weight or
    volume basis isn't stated);
  - per-line contributions, and warnings.
  It never fills a gap. Dashes and drops are trace. Garnish units (leaf, sprig, wedge, slice, twist, peel, pinch)
  are left out. Anything else without a profile or a volume blocks the result.
  Solids measured by spoon (`physical_state = 'solid'`) need grams.
- `phg_mix.persist_recipe_balance(key)` and `persist_all_recipe_balances()` (service_role only) write
  `recipe_balance_analysis` (version `phg-balance-v1`) only when volume, sugar and TA are all complete. ABV is stored
  only if it is also complete. Values are pre-dilution (`assumptions.basis`).
- Syrup sugar per mL uses density: sugar_g_100ml = Brix x density (see `fc_brix_mass_vs_volume`).

## Formulas (per ingredient i, volumes in mL)

```
sugar_g_i   = ml_i * sugar_g_100ml_i / 100
ta_g_i      = ml_i * ta_g_100ml_i / 100
ethanol_ml_i= ml_i * abv_pct_i / 100
pre_dilution_volume_ml = sum(liquid ml_i)
finished_volume_ml     = pre_dilution + dilution water + explicit water/soda tops
sugar_g_100ml = sum(sugar_g) / finished_volume_ml * 100
ta_g_100ml    = sum(ta_g)    / finished_volume_ml * 100
sugar_acid_ratio = sugar_g_100ml / ta_g_100ml      (always report with both absolutes)
abv_finished  = sum(ethanol_ml) / finished_volume_ml * 100
dilution_pct  = (finished - pre) / pre * 100
```

Mass-based Brix (g/100 g) needs density to become g/100 mL; if density is missing, say so rather than
treating them as equal. Unknown dilution -> give the pre-dilution result or a labelled scenario range.

## Guardrails (non-negotiable)

1. Brix is not perceived sweetness. Brix is not pure sugar in an alcoholic or complex matrix: call a
   refractometer reading "apparent Brix" unless the method is validated.
2. pH is not TA. Neither alone predicts sourness.
3. A ratio never replaces absolute concentration (5/0.6 and 10/1.2 are both 8.33 but taste very different).
4. "Simple syrup" is not automatically 50 Brix. "Triple sec" is not Cointreau. Unknown stays unknown.
5. Think in contributions: a liqueur adds sugar + ethanol + aroma + bitterness + water.
6. There is no universal dilution percentage, and no universal salt dose.
7. Service temperature changes perception. Colder is not automatically better. Frozen drinks must be tasted frozen.
8. The frozen 13-15 Brix / 0-10% ABV window is a texture operating window, not a flavor target.
9. No simple subtraction model of sweet vs sour (they suppress each other non-linearly).
10. Never write analyses to `recipe_balance_analysis` from incomplete coverage. An empty table beats fake precision.
11. Never change canonical recipe or menu data because an analysis suggests it. That goes through proposal ->
    approval orchestration. Profile, alias or claim additions need a cited source with basis, confidence
    and verification filled in, and a migration file in `supabase/migrations/`.
12. Don't "fix RLS" across phg as part of this work; security remediation is a separate reviewed project.

## Confidence language

Use the stored `verification` and `basis` honestly: official producer data, peer-reviewed finding,
professional working model, practitioner heuristic, derived calculation, measured, estimated, unresolved.
Good: "Using the PHG lemon working model of ~6% TA...". Bad: "Lemon juice is 6% acid."
Good: "Cointreau's official data gives 22.5 g sugar/100 mL." Bad: "Triple sec has 22.5 g sugar/100 mL."

## Output contract (analysis)

Recipe / Resolved inputs / Unresolved inputs / Input coverage / Sugar / Titratable acidity / Sugar-acid ratio /
ABV / Dilution / Service temperature / Frozen constraints (if any) / Sensory interpretation / Main drivers /
Assumptions / Evidence level / Suggested experiments or changes / The one measurement that would reduce
uncertainty most.

For a quick answer, lead with the conclusion, but never hide a material uncertainty. When the user wants depth,
show the full calculations, sources and alternatives.

## Useful SQL

```sql
select * from phg_mix.v_recipe_balance_coverage where recipe_key = $1;
select * from phg_mix.v_recipe_balance_inputs where recipe_key = $1 order by position;
select * from phg_mix.ingredient_profile_aliases where lower(alias) = lower($1);
select * from phg_mix.formulation_claims where topic = any($1) and status = 'active';
select e.record_type, e.record_key, e.evidence_role, e.locator, e.note, s.key, s.title, s.publisher, s.year, s.url
  from phg_mix.formulation_evidence e join phg_mix.sources s on s.key = e.source_key where e.record_key = $1;
```

## Known gaps (from the brief, section 36)

- Base spirits, vermouths, bitters and many modifiers are unmapped (0 of 255 recipes are fully composition-ready).
- Generic liqueurs need product-specific sugar and ABV.
- Juices need Brix, sugars, TA, pH and acid identity.
- Densities are missing.
- There are no house or measured ingredient profiles yet, and no sensory-validation dataset.
- There is no mixed-sugar sucrose-equivalent sweetness engine. Don't invent one.
