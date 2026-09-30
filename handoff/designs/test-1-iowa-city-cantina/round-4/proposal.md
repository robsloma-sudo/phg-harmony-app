# TEST-1 round 4: "Cantina & Cocktail Bar", Iowa City (proposal v4)

- Task: TEST-1, round 4 (Coordinator; requested by Rob 2026-09-28). This round starts from the round-3 files (score 84.1), which are archived in `round-3/`.
- needs_input: **true**. The open questions are listed below and in each item's `meta.missing_ingredients`.

## Round 4 changes

1. **Columns.** Cider is its own section again, as it is in the draft document (`sec_cider`). The left column holds Cocktails and Spirits; the right holds Beer, Cider and Wine. Every gap between sections is 36 pt, and there is no JS alignment and no filler. The column bottoms are [720.0, 720.0] pt (element slots in layout.json).
   - Limit: the content cannot end level in both columns. With 36 pt gaps, the left column ends at 720 and the right at 696. CIDER cannot sit on y384 either: Draft has 3 items and Classics has 2 two-line cocktails, so a subheader there would land at 396.
2. **Copy.** Dry Cider, Brut Rosé and IPA use the draft's fuller wording. The spirits lines go back to the draft wording because this round had no lexicon lookup. The Margarita serve line reads "Shaken, served on the rocks." The Old Fashioned prints "bitters", as its draft line does.
3. **doc.json.** Every item now has `meta.missing_ingredients` filled in. `doc.meta.designer_notes` explains the Manhattan bitters, the retired Junmai Ginjo and the Cider section.
4. **layout.json.** The round number comes from `build/spec.json`, and the type specs are parsed from the print CSS in menu.html when layout.py runs.
5. **Design.**
   - House Originals sits in a 0.75 pt terracotta frame on a light tint, with cut-paper corner ticks.
   - Section kickers are set in Fraunces italic at 12 pt (they were DM Sans caps).
   - The subheaders now carry small Spanish pairs in Fraunces italic: Clásicos, De la casa, De barril, Por copa, Espumoso. English stays the main language.
   - The dotted column rule is 0.75 pt.

## Printed copy and word sources (round 4; this matches menu.html exactly)

| Item | Price | Draft description | Printed (round 4) | Word sources | meta.missing_ingredients |
|---|---|---|---|---|---|
| Margarita | 15 | Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward. | Blanco tequila, fresh lime, orange liqueur, agave syrup; lime wheel. Shaken, served on the rocks. | Ingredients and "lime wheel" from the draft components and garnish (round-3 trace). "Shaken, served on the rocks" is the Coordinator's wording from `meta.serve_format`. The draft's "Bright and citrus-forward" would push the text to 3 lines, which overflows the left column, so it is left off. | none |
| Manhattan | 15 | Rye, sweet vermouth, aromatic bitters. | Rye whiskey, sweet vermouth; cocktail cherry. Stirred, served up in a coupe. | Components (Rye Whiskey, Sweet Vermouth), the cocktail-cherry garnish, and serve_format/glassware (round-3 trace). Aromatic bitters are hidden because `public_components` has `aromatic-bitters: false`. | none |
| Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon, demerara, bitters. | Brown butter-washed bourbon, demerara syrup, bitters; orange peel. Stirred, served over a large cube. | Components (Brown Butter-Washed Bourbon, Demerara Syrup), "bitters" as in the draft line (menu_items 0cc4e912), orange-peel garnish, and serve_format. | none |
| House Daiquiri | 14 | White rum, lime, and house demerara syrup. | White rum, fresh lime, house demerara syrup; lime coin. Shaken, served up in a coupe. | Components (White Rum, Fresh Lime, House Demerara Syrup), lime-coin garnish, and serve_format (round-3 trace). | none |
| Blanco Tequila | 12 | Blanco tequila pour. | Blanco tequila pour. | The draft wording, unchanged. There was no lexicon query this round, so no aging or D.O. claims are printed. | brand, pour_size |
| Añejo Tequila | 16 | Añejo tequila pour. | Añejo tequila pour. | The draft wording, unchanged (no lexicon query this round). | brand, pour_size |
| Cognac VSOP | 18 | VSOP Cognac pour. | VSOP Cognac pour. | The draft wording, unchanged (no lexicon query this round). | brand, pour_size |
| Czech Pilsner | 7 | Crisp pale lager. | Crisp pale lager. | The draft wording. | brewery, abv, pour_size |
| Dry-Hopped IPA | 8 | Hop-forward draft IPA. | Hop-forward IPA. | The draft wording without "draft", which the Draft subheader already says (Coordinator). | brewery, abv, pour_size |
| Amber Lager | 7 | Toasty amber lager. | Toasty amber lager. | The draft wording. | brewery, abv, pour_size |
| Dry Cider | 8 | Dry sparkling cider. | Dry sparkling cider. | The draft wording. | producer, abv |
| Malbec | 12 | Dry red wine. | Dry red wine. | The draft wording. | producer, region, vintage |
| Pinot Grigio | 11 | Dry white wine. | Dry white wine. | The draft wording. | producer, region, vintage |
| Brut Rosé | 13 | Dry sparkling rosé. | Dry sparkling rosé. | The draft wording. | producer, region, vintage, glass_or_bottle |

## Design concept candidates for round 5 (ranked; round 5 builds number 1)

All three use only the items, prices and draft words that are already verified. None adds a fact, a name, a date, a place or a price. The ornaments are drawn graphics, not claims.

1. **Lotería de la Cantina (chosen).** Each of the 5 sections becomes a lotería card: a bordered card with a card number, a bespoke flat-colour icon cut in the papel-picado style (agave for Spirits, coupe for Cocktails, barrel tap for Beer, apple for Cider, bottle for Wine), and the section name in the lotería banner at the foot of the card, in English with the Spanish kicker ("Cócteles", "Destilados", "Cerveza", "Sidra", "Vino"). The items sit on the card.
   - House Originals becomes the "featured card", drawn larger with the terracotta frame.
   - It is ownable because lotería is the most recognisable Mexican popular-graphic system, and it gives each list its own image while treating every list equally.
   - The card numbers are ordinals (1 to 5), not claims.
   - Risk: it can read as costume. The fix is restrained icons, a strict 12 pt grid inside each card, and the same palette.
   - Fit: the 2-column grid becomes a 2 x 3 card grid, which also answers the column-balance problem, because cards can take equal heights.
2. **Talavera tile grid.** The page becomes a grid of 12 pt-module tiles. Each section header sits on a hand-drawn talavera tile (cobalt and marigold on cream, the palette extended with one blue), and the item lists run in the tile rows.
   - Strong on system and print.
   - Weaker as an "idea": the pattern is decorative rather than narrative, and a blue has to be added to the venue palette.
3. **Mercado price ledger.** Market-stall chalk and ledger typography: items as ledger lines, prices in a stencilled price column with ruled tabs, section tabs like a vendor's price board.
   - Very legible, with an honest price focus.
   - Less culturally specific to a cantina than lotería.
   - Risk: the chalkboard cliché, and it pulls away from the cut-paper identity built in rounds 1 to 4.

Not taken: an agave-field map. It would need geography or origin facts (regions, distilleries) that the venue data does not supply, so it would invite invention.

## Notes kept
- **Manhattan bitters.** The item's `public_components` has `aromatic-bitters: false`, so they are not printed. Should they be printed? (This is also in doc.meta.designer_notes.)
- **Retired item.** The retired Junmai Ginjo ($12, section Sake) in `phg.menu_items` is left off. Please confirm. (Also in doc.meta.)

---

## Earlier rounds (history)

### TEST-1 round 2: "Cantina & Cocktail Bar", Iowa City (proposal v2)

- Task: TEST-1, round 2 (Coordinator; requested by Rob 2026-09-28). The round-1 files are archived in `round-1/`, and the scores are in `REVIEW_LOG.md`.
- Base: Menu Studio draft "Bar menu", project `ddc4bb5b-70e6-4581-8aae-1b4042cd75ef`, `editor_state.doc` revision 3.
- Format: US Letter portrait, one page, two columns; print and phone come from the same HTML.
- needs_input: **true**. It does not block the design; the questions are below.
- confidence: 0.85
- risk_flags:
  - `venue_name_placeholder`
  - `missing_abv`
  - `missing_pour_sizes`
  - `missing_producers_regions`
  - `no_non_alcoholic_list_in_draft`
  - `reference_images_not_viewed` (the storage egress is blocked, so I studied the references from their extracted text and structure)

## Files (this folder)

| File | What it is |
|---|---|
| `menu.html` | A self-contained print menu. The fonts are embedded as base64 (Fraunces and DM Sans, Google Fonts, OFL). At 600 px or narrower it switches to a one-column phone layout. |
| `menu.pdf` | A Chromium print at 8.5 x 11 in with backgrounds. |
| `preview-letter.png` | 2550 x 3300 px, which is 300 dpi at letter size. Full resolution. |
| `preview-phone.png` | 390 css px at device scale 3, so 1170 px wide. Full page. |
| `doc.json` | The Menu Studio document. All 14 items keep their original `id`, `name`, `prices`, `phg`, `meta` and `components`; the build asserts this. |
| `layout.json` | Page, margins, grid (`column_x_pt: [36, 318]`), palette, type, all 91 elements (with a box, a slot and a baseline for each), and the measured checks. |

## Round 1 to round 2: what changed

| # | Coordinator note | Done |
|---|---|---|
| 1 | Cider had 6 pt below its header; the others had 12 | Every section header now has exactly **12 pt** below it (slot to slot), whatever follows. The baseline distance from a header to the next line is **24 pt in all 5 sections**. On the phone, the gap below every header is **14 px**. No "Draft/Bottle" subheader was invented. |
| 2 | Garnishes were said to be invented | I re-queried recipe versions `f06abb74…`, `7095fd3d…`, `14d45e57…` and `9fb77eaa…` through the gateway (**gateway log_id 74**). Each one records a garnish in `phg.recipe_versions.garnish`: **Lime wheel**, **Orange peel**, **Lime coin** and **Cocktail cherry**. `phg.recipe_components` has **0 rows** for these versions, because the components live in `recipe_versions.ingredients`, so there are no role=Garnish component rows. The garnishes stay, now cited per row (table below). The Manhattan's "served up" is replaced by its recorded method and glass: "Stirred and strained into a coupe" (`method` "Stir with ice and strain", `glassware` "Coupe"). |
| 3 | Show the original draft descriptions | Each item's original draft line now sits next to the new one, with a source for every word. Unsupported words are dropped: "bottom-fermented", "class", "age grade", and "Crisp." as a loose add-on. |
| 4 | Shared 12 pt grid | Every slot height and every vertical gap is a multiple of 12 pt (checked, true). **All 66 text baselines**, across both columns and the masthead, sit at y = 12k + 9 pt, so lines read straight across the gutter. |
| 5 | Balance the column bottoms; end the divider at the content | Both columns end at **720.0 pt**. The dotted divider runs from **216.0 to 720.0 pt**, which is the last content line's slot. The right column closes with a 12 pt end mark (three diamonds) after the usual 12 pt gap. |
| 6 | Guest-language spirits and beer copy | The legal category definitions you supplied are used. "100%" is not printed, because the data doesn't support it. The taxonomy words are gone, and the wine lines are no longer just the item name repeated. |
| 7 | Brandy was under "Agave y Destilados" | The kicker is now **"Destilados"**. |
| 8 | Kicker contrast | All terracotta text (kickers, prices, ampersand, "¡Salud!") is now **#A63C1A**, which is **5.55:1** on cream. The flags keep #B4441F because they are graphics. |
| 9 | Prices | Prices are now set in the display face: **Fraunces 600 at 13 pt**, lining and tabular numerals, #A63C1A. |
| 10 | Papel picado | Each of the **nine flags has its own cut-out**: agave, lime wheel, star, nested diamond, sun, marigold flower, cactus, corazón, and crescent moon. Each flag also has a lace hem and a scored top line. The string's ink now starts at **36.00 pt** (ink scan). |
| 11 | `column_x_pt` | Now `[36, 318]`, matching the render. |
| 12 | Demerara wording | Both cocktails now say **"demerara syrup"**. "House" is dropped because the Old Fashioned has `house_recipe: false`. |

Unchanged from round 1: the section order (Cocktails, Spirits, Beer, Cider, Wine), Margarita in the top-left slot, the palette roles, and no new items or prices.

## Reasoning (short; the full version is in `round-1/proposal.md`)

**Census for ZIP 52240 (ACS 2020-2024):**
- median age 28.6
- 29.9% of residents are aged 21-34
- median household income $52,960
- 26.1% of households earn $100k or more
- 47.6% hold a bachelor's degree or higher
- 11.0% are Hispanic/Latino

This is a young, educated college-town crowd, which points to a mid price tier with a casual but crafted tone. The draft's prices ($7-18) fall inside Coa Cantina Iowa City's band (margaritas 11-14, drafts 4-8).

**Layout:**
- Agave and cocktails lead in the left column; the lighter pours sit on the right.
- The Margarita takes the prime slot.
- The highest-priced items (Old Fashioned 16, Añejo 16, Cognac 18) each lead or anchor their groups.
- Prices are whole numbers with no "$", which is the norm for craft cantina lists in the references.

## References (library `menu_visual_documents.id`)

| Doc id | Venue | What I took from it |
|---|---|---|
| **572** | Coa Cantina Iowa City (ACC-IA-LIC-LC0049193), ZIP 52240 | Agave first, split by class. The price band. |
| **7923** | Coa Cantina Des Moines (ACC-IA-LIC-LC0046717) | A compact list led by cocktails. |
| **4969** | Blue Agave Street Tacos & Margaritas, Iowa (ACC-IA-LIC-LC0048728) | The Classic / Signature tiers, which became Classics / House Originals. |
| **208** | Alta Calidad, Brooklyn | Pour size carried in the category header, which I'll use once pour sizes are supplied. |
| **2585** | La Buena Vida, Fort Collins CO | Spanish/English headers, the precedent for the kickers. |

## Sourcing per item: original draft line, printed line, and where each word comes from

Venue recipe rows (gateway log_id 74, `phg.recipe_versions`):

| Version | Name | Garnish | Glassware | Method |
|---|---|---|---|---|
| `f06abb74-762a-4f89-81b2-76a9e4714f3c` | Margarita | Lime wheel | Rocks | Shake with ice and strain over fresh ice |
| `9fb77eaa-c5eb-477c-8e21-acbc89a0e942` | Manhattan | Cocktail cherry | Coupe | Stir with ice and strain |
| `7095fd3d-58fb-43f5-8e8f-1a0afadeafa7` | Brown Butter Old Fashioned | Orange peel | Rocks | Stir with ice and strain over a large cube |
| `14d45e57-72fa-4d23-8274-24e5c80e4b12` | House Daiquiri | Lime coin | Coupe | Shake with ice and fine strain |

The ingredients come from `recipe_versions.ingredients`, which match the draft's `components`. No item uses a **standard** (classic) spec, so `cocktail_reference` was not needed.

**Cocktails** (all from venue recipes):

| Item | Price | Original draft description | Printed (round 2) | Word sources |
|---|---|---|---|---|
| Margarita | 15 | Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward. | Tequila blanco, fresh lime, orange liqueur, agave syrup; lime wheel. Bright and citrus-forward. | "Tequila blanco", "fresh lime", "orange liqueur" and "agave syrup" are from components (Tequila Blanco, Fresh Lime Juice, Orange Liqueur, Agave Syrup). "lime wheel" is from rv.garnish. "Bright and citrus-forward" is from the draft. |
| Manhattan | 15 | Rye, sweet vermouth, aromatic bitters. | Rye whiskey, sweet vermouth; cocktail cherry. Stirred and strained into a coupe. | "Rye whiskey" and "sweet vermouth" are from components. "cocktail cherry" is a draft component (role Garnish) and also rv.garnish. "Stirred and strained" is from `meta.serve_format` "Stir with ice and strain". "coupe" is from rv.glassware. Aromatic bitters are omitted because `public_components.aromatic-bitters = false` (question 3). |
| Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon, demerara, bitters. | Brown butter-washed bourbon, demerara syrup, aromatic bitters; orange peel. Over a large cube. | The spirit, syrup and bitters are from components (Brown Butter-Washed Bourbon, Demerara Syrup, Aromatic Bitters). "orange peel" is from rv.garnish. "Over a large cube" is from serve_format. Quantities are not printed (`house_recipe: false`). |
| House Daiquiri | 14 | White rum, lime, and house demerara syrup. | White rum, fresh lime, demerara syrup; lime coin. Shaken and fine-strained into a coupe. | The rum, lime and syrup are from components (White Rum, Fresh Lime Juice, Demerara Syrup). "lime coin" is from rv.garnish. "Shaken and fine-strained" is from serve_format "Shake with ice and fine strain". "coupe" is from rv.glassware. |

**Spirits** (from legal category definitions):

| Item | Price | Original draft description | Printed (round 2) | Word sources |
|---|---|---|---|---|
| Blanco Tequila | 12 | Blanco tequila pour. | Blue agave, unaged. D.O. Tequila. | "Blue agave" is from category `…tequila` (A. tequilana Weber var. azul). "unaged" is the legal definition supplied by the Coordinator. "D.O. Tequila" is from the category authority note (Denominación de Origen Tequila, NOM-006). |
| Añejo Tequila | 16 | Añejo tequila pour. | Blue agave, aged at least one year in oak. D.O. Tequila. | Category `…tequila.anejo` (NOM-006 class). The aging wording is the Coordinator-supplied legal definition. |
| Cognac VSOP | 18 | VSOP Cognac pour. | Grape brandy, aged at least four years in oak. | Category `…grape_brandy.cognac.vsop`. The aging wording is the Coordinator-supplied legal definition, consistent with the lexicon's VO/VSOP (4) age term. |

**Beer, cider and wine** (from the draft's own wording plus the item name):

| Item | Price | Original draft description | Printed (round 2) | Word sources |
|---|---|---|---|---|
| Czech Pilsner | 7 | Crisp pale lager. | Crisp pale lager in the Czech pils style. | "Crisp pale lager" is from the draft. "Czech" is from the name. "pils" is from category `beer.bottom_fermented_beer.pils`. |
| Dry-Hopped IPA | 8 | Hop-forward draft IPA. | Hop-forward India pale ale, dry-hopped. On draft. | "Hop-forward" and "draft" are from the draft. "India pale ale" expands IPA via category `…india_pale_ale`. "dry-hopped" is from the name. |
| Amber Lager | 7 | Toasty amber lager. | Toasty amber lager, on draft. | "Toasty amber lager" is from the draft. "on draft" is from the draft subsection "Draft". |
| Dry Cider | 8 | Dry sparkling cider. | Dry, sparkling cider. | The draft wording, with a comma added. |
| Malbec | 12 | Dry red wine. | Dry red wine from the Malbec grape. | "Dry red wine" is from the draft. The grape is from the name. |
| Pinot Grigio | 11 | Dry white wine. | Dry white wine from the Pinot Grigio grape. | "Dry white wine" is from the draft. The grape is from the name. |
| Brut Rosé | 13 | Dry sparkling rosé. | Dry sparkling rosé in the brut style. | "Dry sparkling rosé" is from the draft. "brut" is from the name. |

## missing_ingredients (never invented; please supply)

- **Beer (Czech Pilsner, Dry-Hopped IPA, Amber Lager):** brewery, ABV, pour size.
- **Dry Cider:** producer, fruit, ABV, and format (draft or can).
- **Malbec, Pinot Grigio:** producer, region or country, vintage.
- **Brut Rosé:** producer, grapes, region, and **whether 13 is the glass or the bottle price** (its `label` is empty).
- **Blanco Tequila, Añejo Tequila, Cognac VSOP:** brand (the `brand` field is empty), pour size, and whether the tequilas are 100% agave. "100%" is not printed until this is confirmed.
- **Allergens:** none are recorded. The Old Fashioned's brown butter (dairy) is a candidate for an allergen note.

## needs_input (questions for Rob, via the Coordinator)

1. **Venue name.** "Cantina & Cocktail Bar" is a placeholder.
2. **Retired item.** `phg.menu_items` has a retired **Junmai Ginjo, $12, section "Sake"** that is not in the draft document. It is left out; please confirm.
3. **Manhattan bitters.** The draft description says "aromatic bitters", but `public_components` hides them. I followed the flag. Should they be printed?
4. **Non-alcoholic list.** The draft has no NA or zero-proof items, and every Iowa cantina reference has some. Should I add some? I need names and prices.
5. **Legal lines.** Is any ABV, allergen, gratuity or consumer-advisory line required?
6. The pour sizes, ABVs and the Brut Rosé glass-or-bottle question above.

## Self-check (measured from the Chromium render; full data in `layout.json.measured_checks`)

| # | Criterion | Measurement | Self-score |
|---|---|---|---|
| 1 | Alignment and grid | Item names share one x per column: 36.00 / 318.00 pt. Descriptions use the same x. Every slot and every gap is a multiple of 12 pt (true). **66 of 66 baselines are at 12k + 9 pt** across both columns. Names and prices share a baseline to 0.00 pt. | 93 |
| 2 | Headers and subheaders | One style per level. Section headers sit at x = 36 / 318 and subheaders at 36 / 318. The space **below every section header is 12.0 pt**: Cocktails, Spirits, Beer and Wine are followed by a subheader, Cider by an item. Header baseline to next baseline is 24.0 pt in all 5 sections. Space above each header is always 36.0 pt. Kicker and header baselines differ by 0.00 pt. Kicker right edges are 294 / 576 pt, the same as the price edges. Cocktails and Beer share one baseline. | 92 |
| 3 | Price alignment and format | One right edge per column: 294.00 and 576.00 pt, spread 0.00 mm. One format throughout: Fraunces 13 pt lining tabular numerals, whole dollars, no $. | 93 |
| 4 | Colour palette and numbers | Contrast on cream: ink 14.69, terracotta #A63C1A 5.55, agave 6.50, adobe 7.33 (:1). Marigold appears only in non-text ornaments. The display-face prices stand out without shouting. | 91 |
| 5 | Layout and flow | Agave and cocktails lead; Margarita is in the prime slot; premium items anchor their groups. The columns are bottom-balanced at 720.0 / 720.0 pt, and the footer sits 12 pt below. | 88 |
| 6 | Margins and spacing | Element boxes: 36.00 on all four sides. **Printed ink: L 36.00, T 36.00, R 35.76, B 36.00 pt** (max deviation 0.08 mm; the right edge is one pixel of antialiasing on a price glyph). Gutter 24 pt. Item gap 12.0; subheader to item 12.0; items to next subheader 24.0; section gap 36.0. All are constant. | 94 |
| 7 | Design elements | Bespoke nine-motif papel picado, Spanish kickers with marigold diamonds, subheader hairlines, a dotted divider that ends on the last line, a three-diamond column end mark, and an agave "¡Salud!" footer. | 90 |
| 8 | Items, descriptions and ingredients | All 14 are described. Each cocktail names its spirit, at least 2 modifiers, and a garnish that is cited from rv.garnish. Every word is traced in the table above. Unknowns (ABV, producers, regions, pour sizes) are flagged, not invented. | 85 |
| 9 | Prices match | All 14 printed prices match `doc.json` and the draft (checked in the render and asserted in the build). Printed descriptions also match `doc.json` descriptions exactly. | 100 |
| 10 | Coherence | One type system, palette and spacing scale in print and on phone. The phone view is one column: a 14 px gap below every header, no horizontal scroll (scrollWidth 390), and no single-word orphans. | 91 |

**Averages:**
- Critic (criteria 1-7 and 10): (93+92+93+91+88+94+90+91) / 8 = **91.5**
- Content (criteria 3, 5, 8, 9 and 10): (93+88+85+100+91) / 5 = **91.4**

## Reproducibility

The generator is in the session scratchpad, under `t1r2/`:
- `build.py` produces `doc.json` and `menu.html`.
- `render.py` runs two passes (it measures the natural baselines, then applies per-class shifts: title −5.25, h2 +0.75, h3 +0.75, name/price −1.5, desc 0 pt) and produces the PNGs and the PDF.
- `measure.js` does the DOM measurement.
- `layout.py` produces `layout.json` and the checks.

I read the data only through `public.phg_designer_query`. Nothing was written to the database.

## Round 3 changes (the printed copy below replaces the "Printed (round 2)" column above)

**Layout.** Cider is folded into Beer as a **CIDER** subheader, styled like DRAFT. The one-item top-level Cider section and its "Sidra" kicker are gone. The right column's headers now line up with the left: Wine is level with Spirits (525.75 pt), By the Glass with Agave (564 pt), and Sparkling with Brandy (672 pt). Both columns end at 720 pt. All gaps are still multiples of 12 pt, with the baseline phase at 9. The three-diamond end mark, which only appeared on one side, has been removed. Prices are now Fraunces 500, 12 pt, with tabular lining numerals, in #A63C1A. The flag red is the same #A63C1A, so there is one terracotta. Subheaders and kickers are 9 pt. The papel picado has been redrawn as cut-paper lace: a scalloped hem, diamond-cut lace rows and pierced dots, and three agave-derived motifs (a side-view agave, an agave rosette seen from above, and a diamond lattice with an agave). There are no cactus, heart or moon icons. Under the title, the double rule has been replaced by a 0.5 pt hairline broken by an agave-and-diamond cluster. On the phone, a separate banner of 5 larger flags is used. Every description has a non-breaking space before its last word, so no line ends with a single word. Kickers are 12 px (9 pt) and sit on the header baseline.

**Copy (every word comes from the draft, the components, serve_format or glassware):**

| Item | Printed (round 3) | Note |
|---|---|---|
| Margarita | Blanco tequila, fresh lime, orange liqueur, agave syrup; lime wheel. Shaken, served on the rocks over fresh ice. | Serve from serve_format "Shake with ice and strain over fresh ice"; rocks from the recipe glassware. The word order is now "Blanco tequila", matching the Spirits item. "Bright and citrus-forward" was dropped so that all four cocktails follow the same two-sentence pattern (ingredients; garnish. Serve.). |
| Manhattan | Rye whiskey, sweet vermouth; cocktail cherry. Stirred, served up in a coupe. | Aromatic bitters stay **hidden** because the item's `public_components` has `aromatic-bitters: false`. The venue has chosen not to print them, and the designer does not override that flag. |
| Brown Butter Old Fashioned | Brown butter-washed bourbon, demerara syrup, aromatic bitters; orange peel. Stirred, served over a large cube. | serve_format |
| House Daiquiri | White rum, fresh lime, house demerara syrup; lime coin. Shaken, served up in a coupe. | "house" is restored from the component note "House 1:1 demerara syrup by weight." |
| Blanco Tequila | Blue agave. D.O. Tequila. | "unaged" was removed because it is legally wrong: blanco may rest for up to 2 months. |
| Czech Pilsner | Crisp pale lager. | Draft words only (no repeat of the name). |
| Dry-Hopped IPA | Hop-forward India pale ale. | "On draft" was dropped because the DRAFT subheader already says it. |
| Amber Lager | Toasty amber lager. | "on draft" was dropped. |
| Dry Cider | Sparkling. | Draft words, minus the words already in the name. |
| Malbec / Pinot Grigio | Dry red wine. / Dry white wine. | Draft words. |
| Brut Rosé | Dry and sparkling. | Draft words, minus the word already in the name. |

**Excluded:** Junmai Ginjo (sake) is **retired** in the venue data, so it is not on the menu.

**doc.json:** every item now has a `missing_ingredients` array that repeats the list above for that item (for example, Dry Cider has producer, fruit, ABV, and format). The cocktails have empty arrays, except the Old Fashioned, which has an allergen confirmation for its dairy.
