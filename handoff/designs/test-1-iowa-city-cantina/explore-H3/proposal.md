# Explore H3: "Sun & Furrow", round 3 (TEST-1, Iowa City cantina bar menu)

Checkpoint kept untouched: `../explore-H2/`. H2 scored 67.8, with all gates passing. The critic's complaint was "1970s retro sunset with racing stripes; hairpins don't read as greca or furrows".
Doctrine: `DESIGN_THEORY_BRIEF.md`, sections 1-5. Descriptions are unchanged from H2 by instruction; the missing data is waiting on Rob.

## 1. Thesis
**Creative thesis:** The menu is a ploughed field. One continuous line ploughs furrows down the page at the baseline pitch, turning at every headland in a squared Mesoamerican step-fret, while the furrows bend with the Iowa land. Every row of the list sits on a furrow, and the sun sets on the first one.

**Concept words:** plough line, baseline grid, greca, contour, horizon, headland.

**Avoid-list:**
- a stripe band between the masthead and the list
- agave, cactus, moon, bottles, glasses or papel picado
- gradients, texture, boxes, rules, leaders or tables
- taglines
- a second accent colour
- tracked caps on labels longer than 3 words
- any change to description content

## 2. What changed against the round-3 brief
| # | Brief | H3 |
|---|---|---|
| 1 | The furrow becomes the structure | The field runs down the right side from the horizon to the bottom trim (bleed). Furrow pitch = U = 13 px = the row grid of both columns. The headlands are nested, squared greca hooks: each unit of 6 furrows is three hairpins, outer, middle and inner, 13 px apart, so the line returns inward. Successive hooks step 13 px inward and then reset, which gives the stair of the step-fret. Section heads sit on the field's rhythm: all 5 head baselines land on a hook's top furrow or its inner-return furrow (3U phase), checked in the browser (`heads_on_unit_tops` 2/2 and 3/3). The stripe band between masthead and list is gone |
| 2 | Wordmark / sun collision | Measured by pixel scan: T ink ends at x 460.5, I ink starts at 479.0. The sun (r 220) is centred on the cap middle, so its edge stays at x 468.2-471.3 over the whole cap height. That is 7.7 px clear of the T and 7.7 px clear of the I; no glyph is cut. CANT reads ink and INA reads cream. Tracking was opened to 8% to widen the gap |
| 3 | Bottom margin, column feet, baseline grid | Last ink in both columns at y 992.5 (bottom margin 63.5 px = 16.8 mm). Both column feet are identical: line box 998 in each, difference 0 mm. Heads, sub heads and names sit on the 13 px grid (26 baselines, maximum error 0.0 px). Descriptions sit on the grid's half-line (14 lines, maximum error 0.0 px), which gives name-to-description spacing of 1.5U and description line spacing of 1U. Rows register across the columns: Cocktails and Cider share a baseline, as do Beer and Wine |
| 4 | Hierarchy | Section heads are 26 px (19.5 pt) EB Garamond 500 caps in terracotta, in a 3U box. That is 1.5x the item names |
| 5 | Dead space | Asymmetric grid: column 1 is 240 px wide (x 64-304), column 2 is 200 px (x 328-528), and the land takes x 552 to the trim. The empty right half of each column in H2 now holds the field |
| 6 | Reading layer | Multi-word ingredients are joined with non-breaking spaces, and each middot stays at the end of the line it closes. The Margarita's "Bright and citrus-forward." runs on in the same paragraph. Cider sits directly after Beer in reading order (bottom of column 1, then top of column 2). Description content is unchanged |

## 3. Layout geometry (letter 816 x 1056 css px = 8.5 x 11 in; PNG x3.125 = 2550 x 3300)
| Element | Geometry |
|---|---|
| Margins | top 64 (wordmark cap top), left 64, right 64 (wordmark end 752), bottom 63.5 to the last ink |
| Wordmark | Chango 101.1 px, fitted to 688 px with 8% tracking; cap band y 64-137.8 |
| Sun | circle (688.2, 100.9) r 220, clipped at the horizon y 215; its edge sits in the T/I gap |
| Horizon | the first furrow, y 215, starting exactly where the sun's edge meets it and running to the right trim |
| Field | 6-furrow units from y 228 to below the bottom trim. Hooks at x 552 + (0, 13, 26) plus stair offsets (0, 13, 26). Furrows flat until x 604, then bend as contours (amplitude 14 px, wavelength 260 px). Stroke 1.5 px (0.4 mm), ink. Off-page turns sit 39 px beyond the right trim |
| Sub-line | "& cocktail bar · Iowa City, Iowa", 13 px caps, tracking .26em, x 64, y 168 |
| Columns | top 205; column 1 x 64 w 240: Cocktails (Classics, House Originals), Beer (Draft). Column 2 x 328 w 200: Cider, Spirits (Agave, Brandy), Wine (By the Glass, Sparkling) |
| Type | heads 26 px on 39; sub heads 11.5 px caps on 13; names 17 px on 26; prices inline 0.9 em after the name, 17 px, weight 400, ink-2, tabular; descriptions 12 px italic (9 pt) on 13 |
| Balancing | spare units (10 in column 1, 6 in column 2) are allocated by search: every head on the field rhythm first, then the most even item gaps |
| Palette | cream `#F3EBDD`, ink `#1E1A17`, ink-2 `#5B5149`, one accent terracotta `#A6472A` (sun and heads only) |

**Phone** (390 css px x3 = 1170 x 5517):
- U is 15 px.
- The wordmark is refitted to 342 px, and its sun edge sits in the measured T/I gap (221.0-230.3; edge 224.9-226.4).
- The horizon sits under the wordmark, with the sub-line below it.
- There is one column (x 24, w 246) in the order Cocktails, Beer, Cider, Spirits, Wine, with the field on the right (hooks at x 286, 8 px hook pitch).
- Grid registration is exact, as on letter.

## 4. Price association and legibility
- **Name-to-price gap:** 15.3 px on every row (1.9% of the width on letter).
- **Name start to price end:** worst is 27.7% on letter and 57.9% on phone, for "Brown Butter Old Fashioned 16", where the name itself is long.
- **Contrast** (worst pixel, letter and phone):

| Text | Contrast |
|---|---|
| Names | 14.6:1 |
| Prices, descriptions, sub heads, sub-line | 6.53:1 |
| Section heads | 4.99:1 |

- **Sizes:** names 12.75 pt and descriptions 9 pt, both at or above the minimums.

## 5. Device inventory (final)
1. Terracotta sun, clipped by the horizon
2. One continuous plough line: horizon, furrows, stepped greca hooks and contour bend. It is also the baseline grid
3. CANTINA in Chango
4. Cream knock-out of INA inside the sun
5. Sub-line
6. Section heads (accent)
7. Sub heads
8. Italic descriptions
9. Inline muted prices

Budget: 1 gesture, 1 display word, 1 accent colour; 0 boxes, rules, leaders, tables, icons or taglines.

## 6. Revision log, subtraction and before/after
**Before = H2.** The comparison is by squint-test regions, primary area, primary-to-secondary ratio and accent share:

| Round | Hypothesis / change | Regions | Primary % | Pri:Sec | Accent % | Verdict |
|---|---|---|---|---|---|---|
| **H2 (before)** | stripe band + hairpins, sun cut through the T | 1 | 11.41 | n/a | 7.39 | the critic read retro sunset with racing stripes |
| H3 v1 | the field runs down the right; 13 px grid; greca units with a 1-furrow gap between them; columns 240/240 | 2 | 10.35 | 268 | 6.76 | name-to-description spacing of 1U was cramped (descenders touched); units read as separate blocks; gaps ballooned |
| v2 | continuous units; name-to-description 2U; 8% wordmark tracking | 5 | 8.05 | 10.0 | 6.90 | descriptions floated away from the names |
| v3 | descriptions on the half-grid (1.5U); stepped hooks (stair); column 2 at 200 px, field from x 552 | 5 | 8.02 | 10.1 | 6.90 | the step-fret reads; kept |
| v4 | column top lowered to 280 to cut padding | 5 | 10.60 | 13.4 | **9.55** | **reverted**: accent over budget, empty band under the masthead |
| v5 | heads in a 3U box at 26 px | 5 | 8.03 | 10.1 | 6.92 | kept |
| v6 | field phase from the first head; heads forced onto unit tops | 5 | 8.48 | 10.7 | 7.43 | 5/5 heads aligned, but Beer's items were forced apart (+5U) |
| v7 | alignment allowed on the unit's top or inner-return furrow (3U phase) | 5 | 8.49 | 10.7 | 7.43 | 5/5 aligned with even gaps; kept |
| ablation | contour bend removed | 4 | 8.48 | 10.7 | 7.44 | **reverted**: pure greca, the Iowa half disappears |
| **H3 (after)** | bottom margin measured to the last ink (64 px) | **4** | **8.19** | **10.3** | **7.14** | final |

**Subtraction against the H2 device list** (9 devices):
- Removed: the stripe band (the six-furrow strip parked under the masthead) and the curved hill crest that clipped the sun (now a straight horizon).
- The line no longer sits as ornament: it is the grid.
- That is 2 of 9 devices removed (22%), and no device was added.
- Tested and kept: the knock-out, because without it INA would be ink on terracotta at 2.9:1. The contour bend was tested and reverted (above).

**Dominance:** one clearly dominant region, the wordmark and sun, at 8.2% of the page. That is 10.3 times the next region, the densest band of hooks. Accent area is 7.14%, under the 8% budget.

## 7. visual_tests.json (final)
```json
{"file": "preview-letter.png", "squint_salient_regions": 4, "primary_area_pct": 8.19,
 "primary_to_secondary": 10.32, "accent_area_pct": 7.14}
```
The full output, including value range and centroid, is in `visual_tests.json`.

## 8. Files
- `build.py`: 3-pass render.
  1. Fit the wordmark.
  2. Pixel-measure the T/I gap and the baseline offsets.
  3. Draw the field in phase with the first head, then balance with the search.
- `menu.html`
- `preview-letter.png` (2550 x 3300)
- `preview-phone.png` (1170 x 5517)
- `visual_tests.json`
- `contrast.json`
- `layout.json`: grid registration, feet, gap, sun edge, eye travel
- `fonts/`: Chango, EB Garamond (OFL)

## 9. Open points
- The garnishes still need confirmation against `phg.recipe_versions` (carried over from H2).
- The descriptions wait on Rob's missing data, as instructed.
