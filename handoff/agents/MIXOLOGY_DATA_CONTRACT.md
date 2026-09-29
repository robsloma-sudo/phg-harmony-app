# PHG Mixology Knowledge Base: data contract

The single format every mixology research agent writes, and the shape of the Supabase tables it loads into
(draft migration `supabase/migration_drafts/08_mixology_knowledge.sql`). Agents write JSON Lines files to
`data/mixology/<batch>.jsonl`, one object per line. Nothing is written to the database by an agent: files are
reviewed, de-duplicated and loaded by the lead developer.

## Rules for every record

1. **Facts, not prose.** A recipe's ingredients, amounts, ratios, method steps, glass and garnish are facts: record
   them. Never copy a book's or article's sentences, headnotes, stories or tasting prose. Write method steps and
   notes in your own words, briefly.
2. **Every record has at least one source** (`sources[]`), with the exact page URL (or book title, edition, page when
   known) and the source key from the source registry (`src_*`). No source, no record.
3. **Tier every source** (see below). A recipe seen in several sources keeps all of them; conflicts are recorded as
   `variants`, never silently merged.
4. **Units.** Store amounts as numbers in the unit the source used, plus `ml` when it converts cleanly
   (1 oz = 30 ml for bar specs, as PHG does). Dashes, barspoons, drops, sprays, grams, percent (w/w) stay as given.
5. **No guessing.** Unknown = null. A number you could not confirm in a source is not written.
6. **Respect access.** Only use pages that are publicly readable without logging in. Do not scrape Instagram or
   TikTok; for social creators use their own public websites, YouTube video pages/descriptions, or articles that
   quote their recipes. Books are catalogued from publisher pages, reviews and articles that describe them; do not
   reproduce their contents beyond individual recipe specs that are already published openly online.
7. `confidence`: `high` (2+ tier-1/2 sources agree), `medium` (one tier-1/2 source), `low` (only tier 3-4).

## Source tiers

| tier | kind | examples |
|---|---|---|
| 1 | canon book / reference work | The Cocktail Codex, Death & Co, Liquid Intelligence (Dave Arnold), Meehan's Bartender Manual, The Savoy Cocktail Book, Imbibe! (Wondrich), The Flavor Bible, The Flavor Matrix, The Drunken Botanist |
| 2 | professional reference site / publication | Difford's Guide, PUNCH, Imbibe Magazine, Kindred Cocktails, Serious Eats, Liquor.com, Tales of the Cocktail, Cocktail Wonk, Educated Barfly (site) |
| 3 | professional bartender / bar (named person or bar publishing their own spec) | Jeffrey Morgenthaler, Death & Co bar, Dante NYC, Tony Conigliaro, Ryan Chetiyawardana |
| 4 | social / influencer creator | Kevin Kos, Anders Erickson, Cara Devine (Behind the Bar), Steve the Bartender, How to Drink (Greg), Educated Barfly (Leandro DiMonriva), Cocktail Chemistry |
| 5 | brand / producer marketing recipe | a spirit brand's own recipe page |

## Record types (`type` field)

### `source`
`{type:"source", key:"src_cocktail_codex", title, kind:"book|site|publication|bartender|creator|brand|academic|database",
tier:1-5, authors:[..], publisher, year, url, platforms:[{name:"youtube",url}], focus:[..], notable_for, access:
"open|paywalled|print_only|login", rights_note, recipe_count_estimate}`

### `creator` (a person)
`{type:"creator", key:"cr_kevin_kos", name, role:"bartender|author|creator|scientist|chef", affiliations:[..],
tier, home_url, platforms:[{name,url}], known_for:[..], signature_drinks:[..], techniques:[..]}`

### `recipe` (a drink)
`{type:"recipe", key:"rx_daiquiri_classic", name, aka:[..], family:"old_fashioned|martini|daiquiri|sidecar|highball|flip|other",
subfamily, style_tags:[..], base_spirits:[..], era:"pre-prohibition|prohibition|tiki|disco|modern_classic|contemporary",
year_created, creator_key, origin_bar, origin_city,
lines:[{ingredient, amount, unit, ml, prep_key|null, note}],
method:"shake|stir|build|throw|swizzle|blend|dry_shake|whip|clarified|carbonated",
steps:[own words], dilution_target_pct|null, glass, ice, garnish, abv_est|null,
variants:[{name, change, source_key}], sources:[{source_key, url, locator, tier}], confidence}`

#### Versions: one drink, many full recipes (Rob 2026-09-29)
A drink (Margarita) has many complete recipes: classic, traditional, Tommy's, Cadillac, frozen, skinny, spicy, happy hour,
house... Each version is its own `recipe` record (own lines, method, sources) that names its drink:
`drink:{key:"dk_margarita", name:"Margarita", aka:[..], family, parent_key|null}` (or `drink_key` when the drink exists),
`version_type`: original | classic | modern_standard | traditional | regional | house | happy_hour | premium | frozen |
flavored | spicy | skinny | batch | zero_proof | bartender_signature | brand | style | spirit_swap | other,
`version_label` (short: "Cadillac", "Tommy's", "Frozen", "Happy hour (well tequila, sour mix)", "Perfect"),
`serve`: up | rocks | frozen | neat | highball | collins | hot | punch | other,
`price_tier`: well | call | premium | top_shelf (only when the spec says what grade of spirit),
`is_reference`: true for the one spec Harmony gives when no version is asked for (usually the classic).
**Three levels: drink -> style -> recipes.** A style (Cadillac, Frozen, Tommy's, Happy hour...) can hold hundreds of
recipes: every bar's, bartender's, book's and brand's version of that style is its own recipe record with its own
sources. Give `style` (the style's name, e.g. "Cadillac") when the version label carries more than the style name,
`style_description` (what makes it that style, own words) the first time a style appears, and `is_style_reference`
true only for the one spec that should stand for the style. Two recipes for the same style from different sources are
two records (keys like rx_margarita_cadillac_diffords, rx_margarita_cadillac_punch), never merged.
Use `variants` only for one-line tweaks of a spec; any version with its own measurements is a separate recipe.
A named riff that is its own drink (Black Manhattan, Oaxaca Old Fashioned, Paloma) gets its own drink with
`parent_key` pointing to the drink it comes from. Existing drink keys: `dk_` + the recipe key without `rx_` (e.g.
dk_margarita, dk_daiquiri, dk_old_fashioned, dk_manhattan, dk_martini, dk_whiskey_sour, dk_negroni, dk_mojito).

### `prep` (syrups, cordials, infusions, shrubs, tinctures, oleo saccharum, fat-washes, clarified juices, foams, gels)
`{type:"prep", key:"pr_rich_simple_syrup", name, category:"syrup|rich_syrup|flavored_syrup|cordial|infusion|shrub|oleo|tincture|bitters|fat_wash|milk_punch|clarified_juice|acid_blend|super_juice|foam|gel|air|caviar|brine|salt_solution|other",
yield:{amount,unit}, lines:[{ingredient, amount, unit, note}], ratio_note, process:[own words],
params:{temp_c, time_min, pressure, ph, brix, percent_ww}, equipment:[..], shelf_life_days, storage,
used_in:[recipe keys], sources:[..], confidence}`

### `technique`
`{type:"technique", key:"tq_milk_clarification", name, category:"classic|dilution|clarification|infusion|carbonation|temperature|texture|spherification|fermentation|acid_adjustment|distillation|aroma",
what_it_does, when_to_use, steps:[own words], params:{..}, equipment:[..], safety:[..], pitfalls:[..],
example_recipes:[keys], sources:[..], confidence}`

### `pairing` (flavor pairing claim; loads into phg_flavor.pairing_assertions + members + evidence)
`{type:"pairing", key:"pa_pineapple_cinnamon", members:[{subject:"pineapple", kind:"ingredient"},{subject:"cinnamon",kind:"ingredient"}],
relationship:"classic_pairing|complementary|contrasting|bridge|shared_compounds|regional_tradition",
context:{drink_type, note}, rationale (own words, one line), sources:[..], confidence}`

## Taxonomy anchor

Families follow The Cocktail Codex's six root templates (Old Fashioned, Martini, Daiquiri, Sidecar, Whisky Highball,
Flip), with `other` for drinks that fit none (punches, tiki builds, juleps and smashes can be mapped with subfamily).
