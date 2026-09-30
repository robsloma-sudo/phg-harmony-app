# TEST-2 round 1: Coa Cantina Iowa City drinks menu

Task: TEST-2, round 1, from the Coordinator on behalf of Rob, 2026-09-28. Internal showcase only; not for publication.
Venue: COA CANTINA IOWA CITY, account `ACC-IA-LIC-LC0049193`, ZIP 52240. Mexican restaurant and cocktail bar.
Menu type: drinks only. Food sections are out of scope and not used.

**needs_input = true.** The design is complete and print-ready. Six questions (section 7) need the venue's answers
before any real print run. The main gaps are cocktail specs, beer style and ABV, and one missing price.

**confidence = 0.8**

**risk_flags:** `missing_prices` (Maker's Mark), `missing_ingredients` (4 cocktails, 2 frozen drinks, all beer and seltzer style/ABV), `source_price_anomalies_unverified`, `category_placement_per_source`, `venue_page_images_not_viewable`

## Files

| File | What it is |
|---|---|
| `menu.html` | Self-contained HTML (fonts embedded as base64). Print size **US Legal 8.5 × 14 in (215.9 × 355.6 mm), portrait, 2 pages, duplex**, 0.5 in (12.7 mm) margins, no bleed |
| `preview-page-1.png`, `preview-page-2.png` | 2550 × 4200 px each (300 dpi at print size), rendered by Playwright/Chromium |
| `preview-phone.png` | 390 CSS px viewport at device scale 3 (1170 px wide), full-length responsive single-column layout |
| `doc.json` | Menu Studio document, 197 items (199 source rows; 2 upgrade-note rows merged into their cocktails) |
| `layout.json` | Page, margins, 12-column grid, palette, type scale, 400+ elements with x/y/w/h in mm and pt (measured from the rendered DOM, not estimated), plus `measured_checks` |

## 1. Format choice: US Legal, 2 pages (front and back of one sheet)

The source has 199 drinks rows, including 127 tequila pours.
- **Letter (8.5 × 11 in).** I built this first and measured it. Fitting page 2 took 12 pt rows and 8–9 pt type across the whole agave page, and page 1 needed 8.5 pt descriptions. That is too small for a dimly lit cantina.
- **11 × 17 in.** Unwieldy on a small cantina table, and it would leave half a page empty.
- **Legal (8.5 × 14 in).** The standard restaurant menu size, and it fits stock menu covers. Everything fits at 9–12.5 pt with 12.7 mm margins on all sides:
  - **Page 1, Drinks:** Margaritas, Cocktails, Frozen, Alcohol Free, then Beer, Seltzer & Cider.
  - **Page 2, Agave & Spirits:** the tequila grid, then Vodka, Gin, Rum, Whiskey, Scotch and Otros.

This follows the Coordinator's suggested split (mixed drinks and beer on one side, the agave list on the other). One change: the other spirits sit with the agave page, so every by-the-glass spirit is on one page.

## 2. Tone, audience and layout reasoning

Census for ZCTA 52240 (`phg_census_zcta`, ACS 2020–2024):
- median age 28.6
- 29.9% aged 21–34
- median household income $52,960
- 26.1% of households earning $100k+
- 47.6% with a bachelor's degree or higher
- 11% Hispanic/Latino

This is a university crowd: young, educated and price-aware, with a real premium tail. What that shaped:
- **Prices are big and easy to scan:** teal, bold, tabular figures, whole dollars, no `$`, all right-aligned in one column. A guest on a budget can find a $6 Espolòn as fast as a guest after a $200 Clase Azul Añejo.
- **The palette is warm, festive and uncluttered:** a papel-picado banner, an agave ornament, terracotta, marigold and agave teal on cream paper. It reads as cantina, not fine dining, and not a dive.
- **English first**, with Spanish kickers ("Bebidas"), matching the venue's own English headings.

Eye path and placement:
- The house signatures, **Coa Margarita** (top left) and **Coa Paloma** (top right, the prime spot), each open their column. They get a terracotta name, a 14 pt size and a marigold rule.
- The two cocktails with priced upgrades (Coa Paloma +4 to Don Julio Blanco; Ranch Water +2 to DeLeón Platinum) sit highest in the Cocktails list, where the upsell is seen.
- Margaritas run house → mezcal → premium (Cucumber Jalapeño 13, Mango 14) → the $12 fruit set.
- Spirits lists are laddered by price. Beer runs draft → bottles & cans → seltzer & cider.
- No cost or sales data exists for this venue (no Menu Studio draft or menu engineering snapshot), so margin placement follows house items and price, not measured margin.

The tequila list is a **brand × expression price grid**, not paragraphs:
- 65 brand rows, with columns Blanco / Reposado / Añejo, in two halves.
- Rows are merged **only when the venue's name is identical after spelling correction** (for example Don Julio 12 / 12 / 13).
- **Cristalino** (5) and **Extra Añejo** (4) are separate groups, because the product names say so. Each keeps its price in the column the venue listed it under.
- Zebra tint and dot placeholders make the grid easy to scan.

## 3. References (library documents studied)

| Doc ID | Venue | What I took from it |
|---|---|---|
| **8861** | Del Fuego (11780) | Tequila as a brand × expression grid (the same brands across Blanco / Reposado / Añejo / Family), plus a separate "Extra Añejo & Select Barrels" group. This is the model for the grid and the Extra group |
| **208** | Alta Calidad (11238) | Premium agave list with a dedicated price column (1 oz / 2 oz), an "Agave Adjacent" side group, and zero-proof given its own heading. Informed the price-column discipline and giving Alcohol Free its own section |
| **2995** | Tipsy Taco Bar (10549) | Tequila split by Blanco / Reposado / Añejo, with extra añejos inside Añejo, then vodka/gin/rum/whiskey after. Informed the section order |
| **2072** | Frontera Tacos & Tequila (10940) | 58-pour single tequila list next to a margarita-led cocktail page. The counter-example: a long unsorted list is hard to scan, which is why I used the grid |
| **1041** | 3 Victorias (80433) | Margaritas, then cocktails, then beer, then tequila, then mezcal flow, and a cristalino shown as its own expression. Informed the page 1 order |

Picked from `phg_menu_doc_class` (menu_kind = beverage, tags include tequila, ranked by tequila count).

## 4. Item sourcing

Every item and price comes from `public.staging_menu_extract` where `account_id = 'ACC-IA-LIC-LC0049193'` and `superseded_at is null`.
- There are 199 drinks rows across 17 sections.
- I checked my transcription against the database in one read-only query. All 199 ids, names and prices match.
- The only difference found was an escaped `\|` inside the two note rows, which is text escaping, not data.

`doc.json` item ids are `sme_<staging id>`. Each item's `meta` holds `source_id`, `source_section` and `source_name`, plus `name_normalised_from`, `merged_from`, `missing_ingredients` and `placement_note` where they apply. Each price has `source: staging_menu_extract` and its own id, `p_sme_<id>`.

Page images and text: documents **572** and **340** (the venue's drinks page) have page images (`document/572/page-001.jpg`, 1400 × 6542), but `phg_page_text` holds no text for them. The storage host is blocked by the egress policy here, so I could not view the images. The notes column was the only venue-description source.

### Description source per cocktail (marked here only, not on the printed menu)

| Item | Printed description | Source |
|---|---|---|
| Coa Paloma (10, upgrade +4) | Blanco tequila, fresh lime, grapefruit, Aperol, grapefruit soda, salted rim | **venue** (row 184680) |
| Ranch Water (11, upgrade +2) | Blanco tequila, fresh lime juice, Topo Chico sparkling water | **venue** (row 184681) |
| Coa Margarita (11) | Blanco tequila, lime, orange liqueur | venue: blanco tequila. **standard**: lime, orange liqueur (`cocktail_reference` Margarita) |
| Coa Mezcal Margarita (12) | Banhez mezcal, lime, orange liqueur | venue: Banhez mezcal. **standard**: rest (Margarita spec; `cocktail_specs` Mezcal Margarita is a spirit swap) |
| Cucumber Jalapeño (13), Mango (14), Blackberry, Peach, Pineapple, Strawberry (12 each) | Blanco tequila, lime, orange liqueur + the fruit or flavour named | venue: blanco tequila. **standard**: Margarita base. The flavour comes from the item name |
| Bloody Maria (8) | Blanco tequila, tomato juice, lemon, Worcestershire, hot sauce, celery salt | venue: blanco tequila. **standard**: Bloody Mary spec (`cocktail_specs` marks Bloody Maria as a tequila spirit swap) |
| Michelada (8) | Made with Dos Equis | venue: Dos Equis. No standard spec beyond the beer base |
| Cantaritos (12) | Blanco tequila | venue only. **Missing** everything else |
| Mexican Ashtray (7) | Tequila | venue only. **Missing** everything else |
| Frozen Mango Margarita (12), Frozen Strawberry Margarita (10) | Blanco tequila, lime, orange liqueur, mango / strawberry | venue: blanco tequila. **standard**: Margarita base. Frozen comes from the section |
| Tropical Twist Margarita (11), Fro Po (10) | Blanco tequila, frozen | venue only. **Missing** flavours. I did not guess that "Fro Po" is a frozen Paloma |
| Ritual Alternative Zero Proof (7) | Zero-proof alternatives to tequila, gin or whiskey | venue (notes: "Tequila, Gin, Whiskey") |

Other descriptions:
- **Vodka flavours** (Ketel One Botanical; Smirnoff) come from the venue's notes.
- **Otros:** Café Patrón is described as "Coffee liqueur" and Clase Azul Gold as "Tequila".
- **Beer styles known from data** are kept in `doc.json` only: Bud Light and Coors Light "American light lager", Corona "International pale lager" (all from `brand_products.declared_style`), and Exile Swarm Golden Ale and Clockhouse Witch Slap IPA (style stated in the name).
- The catalogue (`products`) has **no ABV** for any of these, so no ABV is printed.

## 5. Conflicts and duplicates resolved (every one)

1. **Coa Paloma appears twice.**
   - Row 173918 is in Cocktails at $10.
   - Row 184680 has the description as its item name and $4 as its "price". That $4 is the Don Julio Blanco upgrade.
   - Merged into one item, `sme_173918`, with prices `[10, "Upgrade to Don Julio Blanco" 4]` and `merged_from: [184680]`.
2. **Ranch Water appears twice.**
   - Row 173921 is in Cocktails at $11.
   - Row 184681 is typed spirit_pour in a "Ranch Water" section, with the description as its name and $2 as the DeLeón Platinum upgrade.
   - Merged into `sme_173921` with prices `[11, "Upgrade to DeLeón Platinum" 2]`.
3. **Busch Light** is on draft (173929, $4) and in bottles & cans (173935, $4). Both are kept as different formats, each under its own subheader.
4. **Mango** and **Strawberry** appear in both Margaritas ($14, $12) and Frozen Drinks ($12, $10). They are different serves, so both are kept, separated by the Frozen heading. The frozen ones keep the venue's names, "Mango Margarita" and "Strawberry Margarita".
5. **Teremana** appears three ways: "Tremana" in Blanco ($7) and Reposado ($7), "Teremana" in Añejo ($10). Normalised to Teremana and merged into one grid row, 7 / 7 / 10.
6. **Corralejo** appears three ways: "Corallejo" in Blanco and Reposado, "Corralejo" in Añejo. Normalised and merged into one row, 6 / 7 / 8.
7. **Cristalino and Extra in the Añejo and Reposado sections.**
   - Casamigos Cristalino and Gran Coramino Cristalino are listed under Reposado.
   - Espolòn, Herradura and Komos Cristalino are listed under Añejo.
   - Corralejo Extra, Corralejo Extra 1821, Don Julio Real Extra and Patrón Extra are listed under Añejo.
   - All are shown in their own **Cristalino** and **Extra Añejo** groups, because the names say so. Each price stays in the column the venue used. Each item's `meta.placement_note` records the venue section.
8. **Row names that differ only by a qualifier stay separate rows** (no guessing that they are the same line):
   - DeLeón Platinum (blanco 9) and DeLeón (reposado 14)
   - José Cuervo de la Familia Platino (blanco 11) and José Cuervo Reserva de la Familia (añejo 40)
   - Hussong's (reposado 12) and Hussong's Platinum (añejo 12)
   - Gran Coramino (añejo 35) and Gran Coramino Cristalino (reposado 15)
9. **Astral Blanco** is shown as "Astral" in the Blanco column, because the column already says Blanco.
10. **Clase Azul Gold ($125)** is listed by the venue under "Misc". It is kept in **Otros** (the venue's Misc) with Café Patrón, not moved into the tequila grid, because the data does not give it an expression.
11. **Items the data files under Añejo, although the names suggest another class.** Kept where the data puts them, and asked in question 4:
    - Don Julio 70 (an añejo cristalino)
    - Herradura Selección Suprema and José Cuervo Reserva de la Familia (extra añejos)
    - Hussong's Platinum
12. **Bottles & Cans split.** The venue's single Bottles & Cans list (20 rows) is shown as **Bottles & Cans** (10 beers) plus **Seltzer & Cider** (High Noon ×7, White Claw ×2, Angry Orchard). The brief treats cider & seltzer as its own list. `meta.placement_note` records the venue section.
13. **Spelling normalised on the printed menu.** The original is kept in `meta.name_normalised_from`:
    - **Misspellings corrected:**
      - Codico Rosa → Código Rosa
      - Corallejo → Corralejo
      - Tremana → Teremana
      - Komos Cristalnio → Komos Cristalino
      - Fleche Azul → Flecha Azul
      - Angry Orchad → Angry Orchard
      - Johnny Walker Red → Johnnie Walker Red
    - **Punctuation, accents and capitals:**
      - Hussongs → Hussong's
      - Ja Ja → JAJA
      - Deleon → DeLeón
      - Titos → Tito's
      - Jack Daniels → Jack Daniel's
      - Avion → Avión
      - Codigo → Código
      - Corazon → Corazón (and its Blanton's, E.H. Taylor, Weller and Eagle Rare lines)
      - Espolon → Espolòn
      - Exotico → Exótico
      - Patron → Patrón (and its Barrel Select, Sherry Cask, Extra and Roca lines)
      - Café Patron → Café Patrón
      - Tapatio → Tapatío
      - Jose Cuervo → José Cuervo
      - Seleccion → Selección
      - Asombroso Rose → Asombroso Rosé
      - Cucumber Jalapeno → Cucumber Jalapeño
      - Tres Generaciones la Colonial → Tres Generaciones La Colonial
    - **Shortened:** House Infused Jalapeno Tequila → House-Infused Jalapeño (it sits in the Blanco column of the tequila grid)
    - **Left as the venue wrote them:** "Ultra" and "High Life". I did not expand them to Michelob Ultra and Miller High Life.
14. **Source price oddities, printed exactly as given and flagged, not changed:**
    - Tequila Ocho: blanco 15 > reposado 12 < añejo 14
    - Flecha Azul: blanco 15 > reposado 13
    - Hacienda Vieja: reposado 9 > añejo 7
    - Casamigos: reposado 11 < blanco 12
    - Clase Azul Añejo: 200
15. **Maker's Mark (173971) has no price in the source.** It is printed with "—" in the price column and `meta.needs_price = true`. It is kept, not dropped, and no price is invented.

## 6. missing_ingredients

- **Cantaritos (173917):** everything except blanco tequila (citrus, soda, salt/chile rim, served in clay?)
- **Mexican Ashtray (173919):** everything except tequila
- **Michelada (173920):** mix and seasonings, citrus, rim, garnish (beer = Dos Equis is known)
- **Fro Po (173922):** flavours and mixers
- **Tropical Twist Margarita (173925):** which fruits, and the mix
- **Frozen Mango and Frozen Strawberry Margarita (173923, 173924):** the frozen base or mix (the standard margarita base is printed)
- **All fruit margaritas:** the form of the fruit (purée, syrup, fresh). The printed text names only the fruit.
- **Ranch Water and Bloody Maria:** garnish
- **All 26 beers, seltzers and ciders:** ABV. Style is also missing except the 5 listed in section 4.
- **Whiskey, rum, gin, vodka:** no age or type beyond the category. The list headers serve as the descriptor.

## 7. Questions for the venue (needs_input)

1. What is the Maker's Mark price?
2. What are the specs for Cantaritos, Mexican Ashtray, Michelada (mix), Fro Po and Tropical Twist? Also, do the house margaritas use orange liqueur? If not, the "standard" line changes.
3. Can we have ABV and style for the drafts and cans? (Or may we use brewery-published figures?)
4. Should Don Julio 70, Herradura Selección Suprema, Reserva de la Familia and Hussong's Platinum stay under Añejo as listed, or move to Cristalino / Extra Añejo?
5. Please confirm the five unusual tequila prices in item 14 of section 5 (Tequila Ocho, Flecha Azul, Hacienda Vieja, Casamigos, Clase Azul Añejo 200).
6. Pour size for the tequila and spirit prices (1.5 oz? 2 oz?). It is not in the data, so none is printed. Also: any legal lines to add (gratuity, "please drink responsibly", ID policy)? None were supplied, so none are printed.

## 8. Changes from the source menu

- New two-page Legal layout.
- Duplicate Paloma and Ranch Water rows merged, with the upgrades turned into priced add-ons.
- Tequila rebuilt as an expression grid with Cristalino and Extra Añejo groups.
- Bottles & Cans split into Bottles & Cans plus Seltzer & Cider.
- Misc renamed **Otros**.
- Spirits ordered by price.
- Spelling normalised.
- Descriptions added, from venue notes first and standard specs second.

## 9. Layout geometry (summary; full data in layout.json)

- **Page:** 215.9 × 355.6 mm (612 × 1008 pt). Margins 12.7 mm on all four sides. No bleed.
- **Grid:** 12 columns of 28.5 pt with 18 pt (6.35 mm) gutters.
  - Halves: 6 columns = 261 pt
  - Thirds: 4 columns = 168 pt
  - Quarters: 3 columns = 121.5 pt
- **Rhythm:** each text role has one constant leading everywhere it appears (1 pt grid):
  - cocktail name 16 pt, cocktail description 12 pt, 12 pt between cocktails
  - list rows 14 pt, grid rows 13 pt, 21 pt between sections
- **Palette:**

| Role | Hex |
|---|---|
| Paper | `#F5EEDF` |
| Ink | `#1F1B18` |
| Terracotta (headers, wordmark, featured names) | `#A8361F` |
| Agave teal (prices, subheaders) | `#135651` |
| Muted text | `#57504A` |
| Marigold (ornaments and rules only, never text) | `#E3A33B` |
| Grid zebra tint | `#EEE3CD` |

- **Type:**

| Role | Face and size |
|---|---|
| Wordmark | Fraunces 900, 40 pt |
| Page title | Fraunces 600 italic, 20 pt |
| Level-1 header | Fraunces 800, 18 pt, terracotta, with a hairline to the column edge |
| Level-2 header | DM Sans 800 caps, 8 pt, +0.18 em tracking, teal, underlined |
| Cocktail names | Fraunces 650, 12.5 pt (featured 14 pt) |
| List and grid names | DM Sans 500, 9.5 / 9 pt |
| Descriptions | DM Sans 400, 9 / 8 pt, muted |
| Prices | DM Sans 700 tabular lining figures, 12 / 9.5 / 9 pt, teal |

- **Elements:**
  - A papel-picado banner (15 flags, three palette colours).
  - A double rule (marigold and ink) under the masthead.
  - An agave-leaf divider balancing the left column of page 1, and a small agave in the footer.
  - Dotted leaders from each name to its price.
- **Footer:** "Coa Cantina · Iowa City" and "coacantinaiowacity.com · n/2". The website comes from the venue's menu URL.

## 10. Self-check against the scorecard (measured on layout.json)

| Measured check (scorecard section 4) | Result |
|---|---|
| Margins (min distance to each edge) | Page 1: 12.70 / 12.70 / 12.70 / 12.70 mm. Page 2: 12.70 / 12.70 / 12.70 / 12.70 mm. Equal on all sides |
| Item-name left edges per column (±0.3 mm) | Spread **0.00 mm** in all 11 columns |
| Price right edges per column (±0.3 mm) | Spread **≤ 0.01 mm** in every column. The tequila grid's Blanco, Reposado and Añejo columns each align at 0.00 mm. Upgrade prices share the main price edge |
| Headers: one size and one x per level per column | L1: all 18 pt, x spread 0.00. L2: all 8 pt, x spread 0.00. Space below L1: 3.17–3.18 mm. Space below L2: 1.58–1.59 mm |
| Gap between consecutive items (±0.5 mm) | Cocktail columns 4.24 mm (spread ≤ 0.01). List and grid columns 0.00 mm (row pitch constant, spread ≤ 0.01). No outliers |
| Contrast (WCAG) | Ink 14.8:1, muted 6.86:1, terracotta 5.66:1, teal 7.34:1 on paper. On the zebra tint: ink 13.44:1, teal 6.66:1. Marigold is used only for non-text ornaments |
| Every item has a description element | All 19 cocktail, frozen and Alcohol Free items have one. 121 list and grid rows (tequila, spirits, beer) have no description line: their descriptor is the grid column label or the list header, recorded as `described_by` in layout.json |
| Cocktail descriptions name the spirit plus 2 more ingredients | Yes for 13 of 18. No for Michelada, Cantaritos, Mexican Ashtray, Fro Po and Tropical Twist (source data missing; flagged in section 6) |
| Prices | 198 of 199 source prices in doc.json; 0 mismatches (checked in a script). Maker's Mark has no price in the source (flagged) |
| Overflow | Both pages fit exactly (scrollHeight = clientHeight). No truncated names (an earlier ellipsis was removed by resizing the grid) |

My scores (honest, not inflated):

| # | Criterion | Score | Note |
|---|---|---|---|
| 1 | Alignment and grid | 90 | Measured edges are exact. Leading is constant per text role, but the two halves of page 1 do not share baselines row by row |
| 2 | Headers and subheaders | 91 | Two levels, one style each, measured consistent. The grid column labels are a deliberate third style (6.5 pt) |
| 3 | Price alignment and format | 93 | One format everywhere (whole dollars, no $). Grid price columns are exact |
| 4 | Palette and numbers | 88 | Four colours plus neutrals, all text ≥ 5.66:1. Prices in bold teal |
| 5 | Layout and flow | 84 | Logical order and house items in prime spots. Page 1 has about a 23 mm open band above the beer section; page 2 is dense (65-row grid at 9 pt) |
| 6 | Margins and spacing | 92 | Margins exact, gutters constant, gaps constant |
| 7 | Design elements | 86 | Papel picado, agave marks, leaders and zebra rows all fit the venue. No photography |
| 8 | Items, descriptions and ingredients | 62 | Nothing invented, and every gap is flagged. But 5 drinks are thin, beer has no style or ABV, and spirits rely on headers. This comes from the missing source data |
| 9 | Prices match | 97 | Exact. One price missing in the source (flagged) |
| 10 | Coherence | 89 | One type system, palette and rhythm across both pages and the phone layout |

- **Critic average** (criteria 1, 2, 3, 4, 5, 6, 7, 10): **89.1**
- **Content average** (criteria 3, 5, 8, 9, 10): **85.0**

Both are above 80. Criterion 8 is the weak one and can only be fixed with the venue's answers to questions 2 and 3.

## 11. Evidence

- `evidence_document_ids`: 8861, 208, 2995, 2072, 1041, plus the venue's own 572 and 340.
- All reads went through `public.phg_designer_query`, read-only. Nothing was written to the database.
