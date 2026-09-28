# TEST-1 round 1: "Cantina & Cocktail Bar", Iowa City (proposal v1)

- Task: TEST-1, round 1 (Coordinator, requested by Rob 2026-09-28)
- Base: Menu Studio draft "Bar menu", project `ddc4bb5b-70e6-4581-8aae-1b4042cd75ef`, `editor_state.doc` revision 3
- Format: US Letter portrait, one page, two columns, print plus phone (same HTML, responsive)
- needs_input: **true** (non-blocking: the design is complete; the questions are below)
- confidence: 0.82
- risk_flags: `venue_name_placeholder`, `missing_abv`, `missing_pour_sizes`, `missing_producers_regions`, `no_non_alcoholic_list_in_draft`, `reference_images_not_viewed` (storage egress blocked; references studied from extracted text and structure)

## Files

| File | What it is |
|---|---|
| `menu.html` | Self-contained print menu. Fonts (Fraunces, DM Sans, from Google Fonts, OFL) are embedded as base64, so it has no network dependencies. Uses a phone layout at 600 px wide or less. |
| `menu.pdf` | Chromium print of `menu.html` at 8.5 x 11 in, 0 printer margin, with backgrounds |
| `preview-letter.png` | 2550 x 3300 px (300 dpi at letter size), full resolution |
| `preview-phone.png` | 390 css px at device scale 3, so 1170 px wide, full page |
| `doc.json` | Menu Studio document (all 14 items, original ids, original `prices` arrays, `phg` sync block kept) |
| `layout.json` | Page, margins, grid, palette, type scale, every element (x/y/w/h in pt and mm) and the measured checks |

## Changes from the draft

1. Title changed from "Bar menu" to **"Cantina & Cocktail Bar"** (placeholder). The subtitle "PHG Publishing Beta · Test Content" becomes **"Iowa City, Iowa"**.
2. Section order changed from Cocktails, Beer, Wine, Spirits, Cider to **Cocktails, Spirits (Agave first), Beer, Cider, Wine**, so the agave and cocktail story leads. Subsection ids and names are unchanged.
3. Item order within subsections:
   - Classics: Margarita now comes before Manhattan, which puts the Margarita in the top-left prime slot.
   - House Originals: Brown Butter Old Fashioned (16) now comes before House Daiquiri (14).
4. Descriptions were rewritten from venue recipes and category data only (see the sourcing table). No item was added, dropped or renamed, and no price was changed. `build.py` asserts that the ids, names and `prices` match the draft exactly.
5. Nothing else in the items was touched (`phg`, `meta`, `components`, `badges`, `origin`).

## Reasoning

**Demographics (ZIP 52240, ACS 2020-2024, `phg_census_zcta`)**
- Median age 28.6; 29.9% of residents are aged 21-34.
- Median household income is $52,960; 26.1% of households earn $100k or more.
- 47.6% hold a bachelor's degree or higher.
- 11.0% are Hispanic/Latino.

This is a young, educated college-town crowd with moderate income. That points to a **mid price tier, casual but crafted** tone: lively colour and folk ornament rather than luxury restraint, but set with editorial typography so the $14-18 cocktails read as considered.

The draft's prices ($7-18) already sit in the local band. Coa Cantina Iowa City charges $11-14 for margaritas, $4-8 for draft beer and $6-30 for most blanco pours, so no price concerns need flagging.

**Layout**
- Two equal 258 pt columns with a 24 pt gutter, split by a marigold dotted rule.
- The left column holds the agave-forward story: Cocktails, then Spirits (Agave, then Brandy).
- The right column holds the lighter pours: Beer, then Cider, then Wine.
- The Margarita takes the prime top-left slot. The highest-priced items (Old Fashioned 16, Añejo 16, Cognac 18) each lead or anchor their groups, so the eye meets the margin-carrying items first.
- The columns end within 24 pt of each other (700 pt and 676 pt), and the footer ornament closes the page.
- Prices are right-aligned whole numbers with no "$", as in most craft cantina lists in the references. They are terracotta and bold so they are easy to find without shouting.

**Design elements**
- A papel picado banner in three flag colours, cut out in cream.
- Spanish kickers (Cócteles, Agave y Destilados, Cerveza, Sidra, Vino) set right on each header's baseline. These are decorative translations of the section names, not item text.
- Agave-green small-caps subheaders with hairline rules.
- An agave-leaf and "¡Salud!" footer.

**Palette:** papel cream #F6EEDF, obsidian ink #231B16, terracotta #B4441F, agave green #2F5D50, marigold #E3A018 (ornaments only), adobe brown #5A4A3F (descriptions). This is 3 accents plus neutrals, and all of it is CMYK-safe.

**Type:** Fraunces (a warm, soft display serif) for the title, headers and item names; DM Sans for descriptions, subheaders and prices. The smallest print size is 8 pt, used only for the letter-spaced kickers; descriptions are 9 pt on 12 pt leading.

## References (library `menu_visual_documents.id`)

| Doc id | Venue | Why / what I borrowed |
|---|---|---|
| **572** | Coa Cantina Iowa City (ACC-IA-LIC-LC0049193), 52240 | Same ZIP; 197 beverage items, 129 of them tequila. Agave is split by class (Blanco / Reposado / Añejo), and cocktails and margaritas are headlined above spirits. I used it for the price band, the agave-first order and the class wording on the tequila lines. |
| **7923** | Coa Cantina Des Moines (ACC-IA-LIC-LC0046717) | Midwest sibling. Short cocktail list first, then draft, cans and alcohol-free. It confirmed a compact, cocktail-led flow. |
| **4969** | Blue Agave Street Tacos & Margaritas, Iowa (ACC-IA-LIC-LC0048728) | Iowa cantina with Classic / Signature / Featured cocktail tiers. I used it as the model for the Classics / House Originals subheader split. |
| **208** | Alta Calidad, Brooklyn | Craft agave list (tequila 40, mezcal 38). Categories carry the pour size in the header ("1 oz. / 2 oz."), which is what I propose for our Agave subheader once pour sizes are supplied. |
| **2585** | La Buena Vida, Fort Collins CO | Spanish/English bilingual headers ("Cocteles de la Casa", "Draft Cervezas", "Tequila Plata / Añejo"). This is the precedent for the Spanish kickers. |

The page images could not be fetched: Supabase storage returned 403 from the egress proxy (organisation policy). I studied the references through `phg_menu_doc_class` counts and `staging_menu_extract` sections, prices and notes. Visual borrowing is therefore limited to structure, not to the references' graphic styles.

## Ingredient and description sourcing per item

| Item (id) | Price | Printed description | Source |
|---|---|---|---|
| Margarita (`beta_margarita`) | 15 | Tequila blanco, fresh lime, orange liqueur, agave syrup, lime wheel. Bright and citrus-forward. | **Venue recipe** `f06abb74…` (ingredients + garnish); tasting line from the draft |
| Manhattan (`beta_manhattan`) | 15 | Rye whiskey, sweet vermouth, cocktail cherry. Stirred and served up. | **Venue recipe** `9fb77eaa…`. Aromatic bitters are omitted because `meta.public_components` sets `aromatic-bitters: false` (see question 3). "Served up" comes from the recipe's coupe glass. |
| Brown Butter Old Fashioned (`beta_old_fashioned`) | 16 | Brown butter-washed bourbon, demerara syrup, aromatic bitters, orange peel. Over a large cube. | **Venue recipe** `7095fd3d…`. Quantities are not printed because `house_recipe: false`. |
| House Daiquiri (`beta_daiquiri`) | 14 | White rum, fresh lime, house demerara syrup, lime coin. Shaken and fine-strained. | **Venue recipe** `14d45e57…` |
| Blanco Tequila | 12 | Blanco / plata class. Blue agave, D.O. Tequila. | Category `spirits.agave_spirits.tequila.blanco` (NOM-006 class; D.O. Tequila; A. tequilana Weber azul) |
| Añejo Tequila | 16 | Añejo (aged) class. Blue agave, D.O. Tequila. | Category `…tequila.anejo` (NOM-006 class) |
| Cognac VSOP | 18 | Grape brandy from Cognac, VSOP age grade. | Category `spirits.brandy_fruit_spirits.grape_brandy.cognac.vsop` |
| Czech Pilsner | 7 | Pils-style pale lager, bottom-fermented. Crisp. | Category `beer.bottom_fermented_beer.pils` + draft "Crisp pale lager" |
| Dry-Hopped IPA | 8 | India pale ale, dry-hopped. Hop-forward. | Category `…ale.india_pale_ale` + item name + draft |
| Amber Lager | 7 | Amber lager, bottom-fermented. Toasty. | Category `…lager.*amber_lager` + draft |
| Dry Cider | 8 | Dry, sparkling cider. | Draft only (category `cider.cider`) |
| Malbec | 12 | Malbec. Dry red. | Item name (grape) + draft |
| Pinot Grigio | 11 | Pinot Grigio. Dry white. | Item name (grape) + draft |
| Brut Rosé | 13 | Brut sparkling rosé. Dry. | Draft + category `wine.sparkling_wine` |

No item uses a **standard** (classic) spec: all four cocktails have venue recipes, so `cocktail_reference` was not needed.

## missing_ingredients (never invented; please supply)

- **Beer (all three drafts):** brewery/brand, ABV, and pour size (e.g. 16 oz). The scorecard expects beer lines to show style and ABV. Style is printed; ABV is missing.
- **Dry Cider:** producer, fruit (apple/pear), ABV, and format (draft/can).
- **Malbec, Pinot Grigio:** producer, region/country, vintage.
- **Brut Rosé:** producer, grapes, region, and whether 13 is the glass or the bottle price (the `label` is empty).
- **Blanco Tequila, Añejo Tequila, Cognac VSOP:** brand (the `brand` field is empty) and pour size (Coa and Alta Calidad list 1 oz / 2 oz).
- Allergens: none recorded for any item. Brown butter (dairy) in the Old Fashioned is an obvious candidate for an allergen note if the venue wants one.

## needs_input (questions for Rob, via the Coordinator)

1. **Venue name.** "Cantina & Cocktail Bar" is a placeholder title. Please give the real name and any logo or brand colours.
2. **Retired item.** `phg.menu_items` also has **Junmai Ginjo, $12, section "Sake", status `retired`**, which is not in the draft document. I left it out. Please confirm it should stay off.
3. **Manhattan bitters.** The draft description says "aromatic bitters", but the item's `public_components` hides `aromatic-bitters`. I followed the visibility flag. Should the bitters be printed?
4. **Non-alcoholic list.** The draft has no NA or zero-proof items. Every Iowa cantina reference offers them (e.g. Coa's N/A Margarita and N/A Paloma). Do you want to add some? You would need to supply names and prices.
5. **Legal lines.** No ABV, allergen, gratuity or consumer-advisory text was supplied, and none is printed. Is any required for this venue?
6. The pour sizes and ABVs listed under missing_ingredients.

## Self-check against the scorecard (measured from the Chromium render; full data in `layout.json.measured_checks`)

| # | Criterion | Measurement | Self-score |
|---|---|---|---|
| 1 | Alignment and grid | Item names share one left x per column (36.00 pt and 318.00 pt; spread 0.00 mm). Descriptions share the same x. On the 6 pt baseline grid, each text class is on a single phase: headers +0, subheaders +0, item names +2.25 across every item. The name/price baseline delta is 0.00 pt. | 92 |
| 2 | Headers and subheaders | One style per level. The section headers' x equals the column x. Cocktails and Beer share the baseline at 201.25 pt. Each Spanish kicker's baseline equals its header's baseline (delta 0.00 pt for all 5), and each kicker's right edge equals the column's price edge (294 / 576 pt). Space above each section header is always 24.0 pt; subheader to first item is always 9.75 pt (text box). | 90 |
| 3 | Price alignment and format | One right edge per column: 294.00 pt and 576.00 pt, spread 0.00 mm. Every price uses one format (whole number, no $, tabular numerals, terracotta bold). There are no glass/bottle columns because the draft has single prices. | 92 |
| 4 | Colour palette and numbers | Contrast on cream: ink 14.69:1, terracotta 4.81:1, agave 6.50:1, adobe 7.33:1. Marigold (1.96:1) is used only for non-text ornaments. | 90 |
| 5 | Layout and flow | Agave and cocktails lead; Margarita is in the prime slot; the premium items anchor their groups. Column bottoms are 700 pt and 676 pt, with the footer at 738 pt. The weak spot is that the NA list is absent from the draft (flagged). | 86 |
| 6 | Margins and spacing | Measured outer margins are L 36.00 / T 36.00 / R 36.00 / B 36.00 pt (12.7 mm; max deviation 0.00 mm). The gutter is 24 pt. The gap between items is always 12.0 pt (spread 0.00). The section gap is always 24 pt. | 94 |
| 7 | Design elements | Papel picado banner, Spanish kickers with marigold diamonds, subheader hairlines, dotted column divider, agave "¡Salud!" footer. All are on theme and none crowds the content. | 88 |
| 8 | Items, descriptions, ingredients | All 14 have descriptions. Each cocktail names its spirit plus at least 3 ingredients and a garnish. Beer lists style; wine lists grape; spirits list type/class. Missing: ABV, producers, regions and pour sizes, all flagged in missing_ingredients and never invented. | 80 |
| 9 | Prices match | All 14 printed prices equal `doc.json`, which equals the draft (asserted in code and in the render check). | 100 |
| 10 | Coherence | One type system, one palette and one spacing scale across print and phone. The phone layout is one column: title balanced over 2 lines, 14 px descriptions, no horizontal scroll (scrollWidth 390). | 90 |

**Averages:**
- Critic (criteria 1-7 and 10): (92+90+92+90+86+94+88+90) / 8 = **90.3**
- Content (criteria 3, 5, 8, 9, 10): (92+86+80+100+90) / 5 = **89.6**

The main content risk is criterion 8. Beer ABV, wine regions and producers are unknown and are flagged rather than printed; supplying them would lift it.

## Reproducibility

The generator scripts are in the session scratchpad:
- `build.py` produces doc.json and menu.html from the verbatim draft, and asserts that ids, names and prices are unchanged.
- `render.py` produces the PNGs and the PDF.
- `layout.py` produces layout.json and the checks.

The data was read only through `public.phg_designer_query`. Nothing was written to the database.
