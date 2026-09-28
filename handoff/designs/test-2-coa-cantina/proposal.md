# TEST-2 round 2: Coa Cantina Iowa City drinks menu

Task: TEST-2, round 2, from the Coordinator on behalf of Rob, 2026-09-28. Internal showcase only; not for publication.
Venue: COA CANTINA IOWA CITY, account `ACC-IA-LIC-LC0049193`, ZIP 52240. Mexican restaurant and cocktail bar.
Round 1 failed the gate (Critic 66.6, Content 80.0, Accuracy 76.4); see `REVIEW_LOG.md`. The round-1 files are archived unchanged in `round-1/`.

**needs_input = true.** The design is complete; the venue still owes the answers in section 7 before a real print run.

**confidence = 0.8**

**risk_flags:** `missing_prices` (Maker's Mark, not printed), `missing_ingredients`, `source_spelling_printed_as_is`, `source_price_anomalies_unverified`, `spirits_column_spread_16.7mm`, `venue_page_images_not_viewable`

## Files

| File | What it is |
|---|---|
| `menu.html` | Self-contained HTML with fonts embedded. Print size **US Legal 8.5 × 14 in (215.9 × 355.6 mm), portrait, 2 pages, duplex**, 0.5 in (12.7 mm) margins, no bleed |
| `preview-page-1.png`, `preview-page-2.png` | 2550 × 4200 px each (300 dpi at print size) |
| `preview-phone.png` | 390 CSS px at device scale 3 (1170 × 17070 px). One masthead, one footer, phone reading order |
| `doc.json` | Menu Studio document, 197 items (199 source rows; 2 upgrade-note rows merged). Maker's Mark is kept with `meta.print = false` |
| `layout.json` | Page, margins, 12-column grid, palette, type scale, every rendered element with x/y/w/h in mm and pt (from the DOM), and `measured_checks` |
| `build/` | Scripts, CSS and fonts. The one-line `README.md` explains how to re-render |
| `round-1/` | Round-1 deliverables, unchanged |

## Round 2 changes

Numbered to match the Coordinator's list.

1. **Dead band removed.**
   - `#page-1 .body{justify-content:space-between}` is gone.
   - Every level-1 header now has exactly **21 pt (7.41 mm)** above it. Measured: 7.40–7.41 mm for all 7 L1 headers.
   - The freed space went to rhythm:
     - Cocktail names 13 / 17 pt; descriptions 9.5 / 13 pt.
     - Cocktail item gap **15 pt**. The Cocktails column uses a constant **22.1 pt**, explained under item 2.
     - List rows **16 pt**.
   - The space between the last content and the footer rule is now 9.5 mm (page 1) and 10.0 mm (page 2), of which 6.35 mm is the fixed footer margin.
2. **Column holes closed.**
   - **Page 1 top.** Margaritas and Cocktails now end on the same line (0.02 mm spread).
     - The Cocktails items carry 2–3 line descriptions, so that column uses one constant 22.1 pt item gap.
     - I chose this over a filler ornament. The agave divider is removed.
   - **Frozen band.** Both halves end on one line (0.00 mm).
   - **Alcohol Free** is now a band at the end of page 1, so it no longer leaves a hole in a column.
   - **Beer.** Cider moved under Draft and Seltzer has its own column. Bottoms: 291.65 / 296.14 / 290.50 mm, a spread of 5.64 mm (exactly one 16 pt row).
   - **Page 2 spirits.** The four quarter columns end at 325.90 / 326.34 / 322.10 / 309.66 mm, a spread of 16.7 mm.
     - This is the floor unless a list is split across columns. The fixed list heights are Vodka 162 pt, Gin 84, Rum 84, Whiskey 116 (6 printed rows, Maker's Mark removed), Scotch 52 and Otros 64.
     - Vodka alone sets a 162 pt minimum. Whiskey cannot pair with any other list and stay under that, so the Whiskey column ends about 46 pt (16 mm) short in every arrangement.
     - I did not split a list across columns. Round 1's spread was 17.9 mm.
3. **Tequila grid.**
   - All extra añejos stay in the Añejo column (see item 11), so the only group is **Cristalino**.
   - Its L2 header has margin 0: the rule runs the full column width, at x = 111.12 mm (the right half).
   - The Blanco / Reposado / Añejo labels are now in L2 style (DM Sans 800 caps, 7.5 pt, teal) and are repeated above the Cristalino group.
   - Price columns were widened to 33 / 47 / 33 pt so the labels never touch. Measured label widths are 31.3 / 40.6 / 25.3 pt, leaving at least 6.4 pt between labels.
   - The A–Z halves end 0.97 mm apart.
4. **"Orange liqueur" removed** from all 12 margarita and frozen descriptions.
   - Margaritas get one intro line: *"Made with blanco tequila, except the Coa Mezcal Margarita."*
   - No venue row mentions lime for the margaritas, so lime is not printed. The flavour is the item name.
   - Coa Mezcal Margarita prints "Made with Banhez mezcal" (from its venue row).
   - Frozen gets the intro *"Made with blanco tequila."*
   - Bloody Maria prints no description: the venue row gives only blanco tequila. The standard spec is kept here in section 4.
5. **Unsourced text removed.**
   - Café Patron "Coffee liqueur" is gone.
   - Exotico and Asombroso Rose are back to the venue spelling.
   - **Rule applied everywhere:** print the venue's spelling; change it only when a `public.brands` or `public.products` row supports the change, and add accents only with such a row. The full list is in section 5.
6. **Bare descriptions removed.** No item prints "Tequila", "Blanco tequila" or "frozen" as its whole description.
   - Printed now: Michelada "Made with Dos Equis". Mexican Ashtray, Cantaritos, Fro Po and Tropical Twist print name and price only.
   - All five stay in missing_ingredients.
7. **Maker's Mark** is not printed on paper or phone. It stays in `doc.json` with `meta.needs_price = true`, `meta.print = false` and a `print_note`.
8. **Spanish kickers** sit on the L1 headers: Margaritas · Cócteles · Congelados · Cervezas · Sin Alcohol · Licores (Fraunces italic 11 pt, teal).
   - Page 2's title is now **Tequila & Spirits**, and its masthead line reads "Iowa City · Tequila y Licores".
   - Tequila has no kicker: the Spanish word is the same.
9. **Alcohol Free is last in the flow.** It is the final band on page 1 and the final section on the phone.
10. **Phone.**
    - One masthead and one footer (page numbers hidden).
    - Order: Margaritas, Cocktails, Frozen, Beer (Draft, Bottles & Cans), Seltzer & Cider (Seltzer, Cider), Tequila, Spirits, Sin Alcohol. Checked by measuring header positions in a 390 px viewport.
    - The tequila list is one continuous A–Z table. Its Blanco / Reposado / Añejo labels are `position: sticky` (verified: they stay at viewport top 0 when scrolled). Cristalino follows the A–Z list.
    - No filler ornaments on the phone.
11. **Extra añejos are treated alike.** Only 2 of the 6 candidates have product rows declaring the class:
    - Patron Extra: `products` 9a28ff7a, "Patron Extra Anejo", class extra_anejo
    - Corralejo Extra: `products` 2f16596f, "Corralejo Extra Anejo", class extra_anejo

    Don Julio Real Extra, Corralejo Extra 1821, Herradura Selección Suprema and Jose Cuervo Reserva de la Familia have no class row. So **all of them stay in the Añejo column**, as the venue lists them, until the venue answers question 4. The two cites are stored in `meta.class_cite`.
12. **Corralejo Extra at 15** is added to the price-confirmation question.

## 1. Format: US Legal, 2 pages (front and back of one sheet)

Same reasoning as round 1:
- **Letter** forced 8–9 pt type on 12 pt rows for 127 tequila pours.
- **11 × 17** is oversized for a cantina table and would leave half a page empty.

Legal gives 9–13 pt type with 12.7 mm margins.
- **Page 1, "Drinks":** Margaritas | Cocktails, then Frozen, then Beer, Seltzer & Cider, then Alcohol Free.
- **Page 2, "Tequila & Spirits":** the tequila grid, then Spirits in quarters.

## 2. Tone, audience and layout reasoning

Census for ZCTA 52240:
- median age 28.6
- 29.9% aged 21–34
- median household income $52,960
- 26.1% of households earning $100k+
- 47.6% with a bachelor's degree or higher
- 11% Hispanic/Latino

That means a young, price-aware university crowd with a premium tail. What that shaped:
- **Big bold teal prices** (whole dollars, no `$`), all right-aligned in one column.
- **A warm cantina palette:** papel picado, terracotta, marigold and agave teal on cream.
- **English first with Spanish kickers.** The venue itself uses English headings; the kickers give the cantina voice without misusing Spanish.

Eye path:
- House signatures Coa Margarita (top left) and Coa Paloma (top right) open their columns, in terracotta with a marigold rule.
- The two priced upgrades sit high in Cocktails.
- Margaritas run house → mezcal → premium (Cucumber Jalapeno 13, Mango 14) → the $12 fruit set.
- Spirits lists run by price.

There is no cost or sales data for this venue, so placement follows house items and price, not measured margin.

## 3. References (library documents)

| Doc ID | Venue | What I took from it |
|---|---|---|
| **8861** | Del Fuego (11780) | Brand × expression tequila grid, the model for page 2 |
| **208** | Alta Calidad (11238) | Price-column discipline; zero-proof given its own heading |
| **2995** | Tipsy Taco Bar (10549) | Tequila by Blanco / Reposado / Añejo with extra añejos inside Añejo (as now), then vodka/gin/rum/whiskey |
| **2072** | Frontera Tacos & Tequila (10940) | Counter-example: a long flat tequila list is hard to scan |
| **1041** | 3 Victorias (80433) | Margaritas → cocktails → beer → tequila flow; cristalino as its own expression |

## 4. Item sourcing

- **Items and prices:** `public.staging_menu_extract`, account `ACC-IA-LIC-LC0049193`, `superseded_at is null`.
  - 199 drinks rows, all checked against the database.
  - `doc.json`: 197 items and 198 prices, **0 mismatches**.
  - HTML: 325 printed price elements, **0 mismatches**.
  - The only price missing is Maker's Mark, which has none in the source.
- **Venue page images:** documents 572 and 340 have images but no text in `phg_page_text`, and the storage host is blocked by the egress policy here.

### What each cocktail prints, and where it comes from

| Item | Printed | Source | Kept here only (not printed) |
|---|---|---|---|
| Coa Paloma 10 (+4 Don Julio Blanco) | Blanco tequila, fresh lime, grapefruit, Aperol, grapefruit soda, salted rim | venue row 184680 | |
| Ranch Water 11 (+2 Deleon Platinum) | Blanco tequila, fresh lime juice, Topo Chico sparkling water | venue row 184681 | |
| Margaritas (8) | Section intro "Made with blanco tequila, except the Coa Mezcal Margarita."; Coa Mezcal Margarita "Made with Banhez mezcal" | venue rows 173908–173915 (blanco tequila / Banhez mezcal) | **standard:** blanco tequila, lime, orange liqueur (`cocktail_reference` Margarita) |
| Frozen (4) | Section intro "Made with blanco tequila." | venue rows 173922–173925 | **standard:** frozen margarita = Margarita spec, blended |
| Bloody Maria 8 | name and price only | venue row: blanco tequila | **standard:** tomato juice, lemon, Worcestershire, hot sauce, celery salt (`cocktail_reference` Bloody Mary; `cocktail_specs` marks Bloody Maria as a tequila spirit swap) |
| Michelada 8 | Made with Dos Equis | venue row 173920 | no standard spec beyond the beer base |
| Cantaritos 12, Mexican Ashtray 7, Fro Po 10, Tropical Twist 11 | name and price only | venue rows (blanco tequila / tequila) | none |
| Ritual Alternative Zero Proof 7 | Zero-proof alternatives to tequila, gin or whiskey | venue notes "Tequila, Gin, Whiskey" | |

Other printed descriptions:
- **Vodka flavours** (Ketel One Botanical, Smirnoff) come from the venue notes.
- **Clase Azul Gold** prints "Joven tequila", from `products` d760d665 ("Ha Clase Azul Gold Tequila", class joven).
- **Beer styles known from data** stay in `doc.json` only: Bud Light and Coors Light "American light lager", Corona "International pale lager", Exile Swarm Golden Ale "Golden ale", Clockhouse Witch Slap IPA "IPA". The catalogue has no ABV for any of them.

## 5. Conflicts and duplicates resolved (every one)

1. **Coa Paloma appears twice:**
   - Row 173918 is in Cocktails at 10.
   - Row 184680 has the description as its name and 4 as its price: the Don Julio Blanco upgrade.
   - Merged into `sme_173918` with prices `[10, "Upgrade to Don Julio Blanco" 4]`.
2. **Ranch Water appears twice:**
   - Row 173921 is in Cocktails at 11.
   - Row 184681 has the description as its name and 2 as its price: the Deleon Platinum upgrade.
   - Merged into `sme_173921` with prices `[11, "Upgrade to Deleon Platinum" 2]`.
3. **Busch Light** is on draft (4) and in bottles & cans (4). Both kept, as different formats.
4. **Mango and Strawberry** are margaritas (14, 12) and frozen drinks (12, 10). Both kept as different serves.
5. **Teremana:** "Tremana" (blanco 7, reposado 7) and "Teremana" (añejo 10) are merged into one grid row. Cite: `brands` ff00b87a "Teremana".
6. **Corralejo:** "Corallejo" (blanco 6, reposado 7) and "Corralejo" (añejo 8) are merged into one row. Cite: `brands` 1a7a2d92.
7. **Cristalino group** (5 rows), shown in the column the venue used.
   - Casamigos Cristalino and Gran Coramino Cristalino are listed under Reposado.
   - Espolon, Herradura and Komos Cristalino are listed under Añejo.
   - All five names say Cristalino. Casamigos, Espolon and Gran Coramino also have product rows with class cristalino (`meta.class_cite`).
8. **Extra añejos:** all kept in the Añejo column (see round 2 change 11).
9. **Different qualifiers stay separate rows:**
   - Deleon Platinum and Deleon
   - Jose Cuervo de la Familia Platino and Jose Cuervo Reserva de la Familia
   - Hussongs and Hussongs Platinum
   - Gran Coramino and Gran Coramino Cristalino
10. **Clase Azul Gold** (venue section "Misc") stays in **Otros** with Café Patron.
11. **Bottles & Cans (20 rows)** is shown as:
    - Bottles & Cans: 10 beers
    - Seltzer: High Noon ×7, White Claw ×2
    - Cider: Angry Orchad Green Apple

    `meta.placement_note` records the venue section.
12. **Spelling rule.** Print the venue's spelling. Change it only with a catalogue row. Add accents only with a catalogue row.

    Changed, with cites (stored in `meta.name_normalisation_cite`):

    | Venue spelling | Printed | Cite |
    |---|---|---|
    | Codico Rosa | Codigo Rosa | `brands` 13226856 "Codigo 1530" |
    | Corallejo | Corralejo | `brands` 1a7a2d92 |
    | Tremana | Teremana | `brands` ff00b87a |
    | Komos Cristalnio | Komos Cristalino | `brands` 677b30fe "Komos" + `beverage_categories` cristalino |
    | Fleche Azul | Flecha Azul | `brands` 5b6902fd |
    | Ja Ja | Jaja | `brands` 0bb1bf79 |
    | Herradura Seleccion Suprema | Herradura Selección Suprema | `brands` df036bdd "Herradura Selección Suprema de Herradura" (the only accent printed) |

    **Printed as the venue spells them.** The catalogue spells these without accents too:
    - Avion
    - Codigo
    - Corazon
    - Deleon
    - Espolon
    - Exotico
    - Hussongs
    - Jose Cuervo
    - Patron
    - Tapatio

    **Printed as the venue spells them, with no catalogue row either way:**
    - Asombroso Rose
    - Astral Blanco
    - Corazon Blantons
    - House Infused Jalapeno Tequila
    - Tres Generaciones la Colonial
    - Cucumber Jalapeno
    - Café Patron

    **Likely typos printed as the venue spells them.** No catalogue row exists, so these are question 5:
    - Angry Orchad Green Apple
    - Johnny Walker Red
    - Titos
    - Jack Daniels
13. **Source price oddities**, printed exactly as given and flagged:
    - Tequila Ocho: blanco 15, reposado 12, añejo 14
    - Flecha Azul: blanco 15, reposado 13
    - Hacienda Vieja: reposado 9, añejo 7
    - Casamigos: reposado 11, blanco 12
    - Clase Azul Añejo 200
    - **Corralejo Extra 15**, against Corralejo Extra 1821 at 40
14. **Maker's Mark (173971)** has no price. It is not printed and stays in `doc.json` (round 2 change 7).

## 6. missing_ingredients

- **Cantaritos (173917):** everything but blanco tequila
- **Mexican Ashtray (173919):** everything but tequila
- **Michelada (173920):** mix, seasonings, citrus, rim, garnish
- **Fro Po (173922):** flavours and mixers
- **Tropical Twist (173925):** which fruits, and the frozen mix
- **Bloody Maria (173916):** everything but blanco tequila
- **Coa Margarita and the 6 fruit margaritas:** citrus, sweetener or liqueur, rim, and the form of the fruit
- **Frozen Mango and Strawberry:** the frozen base
- **Ranch Water:** garnish
- **All 26 beers, seltzers and ciders:** ABV. Style is also missing except for the 5 listed in section 4.
- **Spirits:** type and age beyond the list headers

## 7. Questions for the venue (needs_input)

1. What is the Maker's Mark price?
2. What are the specs for the margaritas (lime? orange liqueur? rim?), Bloody Maria, Cantaritos, Mexican Ashtray, Michelada mix, Fro Po and Tropical Twist?
3. What are the beer and seltzer styles and ABV (or may we use producer figures)?
4. Should Don Julio Real Extra, Corralejo Extra, Corralejo Extra 1821, Patron Extra, Herradura Selección Suprema and Jose Cuervo Reserva de la Familia move to an Extra Añejo group? Should Don Julio 70 and Hussongs Platinum stay under Añejo?
5. May we correct these spellings: Angry Orchard, Johnnie Walker, Tito's, Jack Daniel's? What about the accents Avión, Patrón, Espolòn, Código, Corazón, José Cuervo, Tapatío?
6. Please confirm these prices: Tequila Ocho, Flecha Azul, Hacienda Vieja, Casamigos, Clase Azul Añejo 200 and **Corralejo Extra 15**.
7. What is the pour size, and are there any legal lines to add (gratuity, ID, drink responsibly)? None were supplied, so none are printed.

## 8. Layout geometry (full data in layout.json)

- **Page:** 215.9 × 355.6 mm, margins 12.7 mm on all sides.
- **Grid:** 12 columns of 28.5 pt, 18 pt gutters.
  - Halves: 261 pt
  - Thirds: 168 pt
  - Quarters: 121.5 pt
- **Rhythm:**
  - 21 pt above every L1 header
  - cocktail name 17 pt, description 13 pt
  - cocktail item gap 15 pt (Cocktails column 22.1 pt)
  - list rows 16 pt, grid rows 13 pt
  - 4.5 pt from an L2 header to its first row
  - 15 pt between L2 lists
- **Palette:**

  | Role | Hex |
  |---|---|
  | Paper | `#F5EEDF` |
  | Ink | `#1F1B18` |
  | Terracotta | `#A8361F` |
  | Agave teal | `#135651` |
  | Muted | `#57504A` |
  | Marigold (ornaments only) | `#E3A33B` |
  | Zebra tint | `#EEE3CD` |

- **Type:**

  | Role | Face and size |
  |---|---|
  | Wordmark | Fraunces 900, 40 pt |
  | L1 header | Fraunces 800, 18 pt, with a Fraunces italic 11 pt Spanish kicker |
  | L2 header | DM Sans 800 caps, 8 pt |
  | Grid labels | DM Sans 800 caps, 7.5 pt |
  | Cocktail names | Fraunces 650, 13 pt (featured 14.5 pt) |
  | List names | DM Sans 500, 9.5 / 9 pt |
  | Descriptions | DM Sans 9.5 / 8 pt (intro lines italic) |
  | Prices | DM Sans 700 tabular |

## 9. Self-check (measured from layout.json)

| Check | Result |
|---|---|
| Margins | Page 1 and page 2: 12.70 / 12.70 / 12.70 / 12.70 mm |
| Space above every L1 header | 7.40–7.41 mm (all 7) |
| Item-name left edges | Spread 0.00 mm in all 14 columns |
| Price right edges | Spread ≤ 0.01 mm in every column; tequila Blanco, Reposado and Añejo columns 0.00 mm each |
| Header sizes and x | L1 all 18 pt, L2 all 8 pt; x spread 0.00 per column. Cristalino L2 at x 111.12 mm with a full-width rule |
| Space below headers | L1 → first element: 3.18 mm everywhere. L2 → first row: 1.58–1.59 mm. The exception is Cristalino at 7.58 mm, because the repeated label row sits between header and first row, as requested |
| Item gaps | Constant within every column (spread ≤ 0.01 mm): 5.29 mm (15 pt) in Margaritas / Frozen, 7.79 mm (22.1 pt) in Cocktails, 0.00 mm row pitch in lists and grid |
| Column bottoms | Page 1 top 0.02 mm; Frozen 0.00; Beer 5.64 (one row); Alcohol Free (single column, no pair). Tequila halves 0.97; Spirits 16.68 (floor, see change 2) |
| Space from last content to footer rule | 9.46 mm (page 1), 9.95 mm (page 2), including the 6.35 mm footer margin |
| Contrast | Ink 14.8, muted 6.86, terracotta 5.66, teal 7.34; on the zebra tint 13.44 and 6.66 |
| Prices | 0 mismatches in `doc.json` (198 prices) and in the printed HTML (325 price elements) |
| Unsourced text | "orange liqueur", "Coffee liqueur", "Exótico", "Rosé", "—", tomato and Worcestershire: 0 printed occurrences |
| Items without their own description line | 135, each with `described_by` (a section intro, grid column label or list header) recorded in layout.json |

My scores, honest:

| # | Criterion | Score | Note |
|---|---|---|---|
| 1 | Alignment | 90 | |
| 2 | Headers | 88 | Cristalino spacing exception |
| 3 | Price alignment | 93 | |
| 4 | Palette | 88 | |
| 5 | Layout and flow | 86 | Spirits spread at the 16.7 mm floor; Cocktails gap differs from Margaritas by design |
| 6 | Margins and spacing | 90 | |
| 7 | Design elements | 84 | Agave divider removed; papel picado, kickers, leaders, zebra rows remain |
| 8 | Items, descriptions and ingredients | 60 | Many items now carry only name and price because the venue rows are thin; all flagged |
| 9 | Prices | 97 | |
| 10 | Coherence | 89 | |
| 11 | Ingredient accuracy | 90 | Every printed fact traces to a venue row or catalogue row; venue spellings printed as-is |
| 12 | Description quality | 70 | Honest but sparse; intro lines avoid repeating names |
| 13 | Venue-type fit | 86 | |
| 14 | Descriptions and prices laid out together | 88 | |

- **Critic** (1–7, 10): **88.5**
- **Content** (3, 5, 8, 9, 10): **85.0**
- **Accuracy** (10–14): **84.6**

The limit on criteria 8 and 12 is the missing venue data (questions 2 and 3), not the layout.

## 10. Evidence

- `evidence_document_ids`: 8861, 208, 2995, 2072, 1041, plus the venue's own 572 and 340.
- Catalogue rows cited: listed in section 5 and round 2 changes 11 (`public.brands`, `public.products`, `public.beverage_categories`).
- All reads went through `public.phg_designer_query`, read-only. Nothing was written to the database.
