# TEST-1 explore-I7: Night Field, round 7 (from I5; I5 and I6 kept as checkpoints)

**Thesis:** A Mexican agave, engraved in blue-green, grows out of a rolling rise of Iowa loam. The wordmark stands on the same horizon, so the name, the plant and the soil are one landscape.

**Concept words:** rooted, loam, horizon, engraved, bilingual, quiet.

**Avoid-list:**
- marginal teeth and whiskers
- even vector fans
- confetti crumbs and sunburst root fans
- water-like continuous strata
- a second drawing
- boxes, leaders, taglines
- taxonomy copy
- off-grid lines

## Fixes 1-16
| # | Fix | Result |
|---|---|---|
| 1 | Teeth | Removed on every leaf (`teeth=0`). |
| 2 | Hatch | Back and mid leaves: longitudinal lines swell toward the shaded edge (width factor 0.4 to 1.0) and thin toward the lit side; line dropping keeps the pitch ≥ 1.8 px. Front leaves: cross-contour arcs, packed tight at the heart (pitch × (0.75 + 0.6 t^1.4)) and shortening toward the tip and lit edge. Cone: inclined spiral arcs (the wrapped young leaves), with alternate arcs stopping at the axis. There is no even fan anywhere. |
| 3 | Iowa loam | The soil surface is level under the list (y 896) and rises in one smooth low mound under the rosette (to y 808). Below it, the loam is engraved as a soil profile in the leaf's tapered-line grammar, following the surface contour: an A horizon of close level strata, a B horizon of short tilted lenses, and a C horizon of sparse long lenses. It is drawn at lower contrast (accent mixed 55% toward the ground). 4 roots in the same grammar reach down; there are no crumbs and no fan. The loam holds 26.4% of the art's height under the rosette and 17.1% under the list. |
| 4 | Wordmark | CANTINA is flush left at x 64, tracking .26em, cap top 64. The horizon rule starts at x 64 exactly on CANTINA's baseline (y 118) and runs to the right bleed; the tallest leaves rise to it. The sub-line reads "Cantina & cocktail bar · Iowa City, Iowa" in Source Serif italic 15 px. There is no leading-ampersand line, and it no longer duplicates the H3 style. |
| 5 | Axis | The header is flush left at x 64, matching the list's left axis. |
| 6 | Baseline | H2 tops at 240. Every letter row top is a multiple of 8 (all 14). Description leading is 16 px. The H3-to-name gap is now 8 px (H3 margin-bottom 8). Serve labels no longer inflate the line box. |
| 7 | Column ends | **Not met.** Col 1 ends at 864 and col 2 at 704, a 160 px difference. The new order (item 11) puts 8 items plus 2 multi-line cocktails in col 1 against 6 one-line items in col 2. The rosette fills the field under col 2 and Spirits (soil mound top at 808, leaves 6 mm clear), so the right column's end meets the drawing rather than empty ground. Balancing to within 8 px would need a different split (e.g. Cider into col 2), which contradicts item 11. |
| 8 | Warm accent | Terracotta #D98E6A on the H2s only (DM Sans 700, 14.5 px). Contrast 6.91:1. The drawing stays blue-green. Accent share by colour match: blue-green 1.36% + terracotta 0.78% (≤ 8%); visual_tests reports 0.21%. |
| 9 | Sub-labels | H3 at 11.5 px in #C4B9A6, contrast 9.33:1. H2 now at weight 700 against 500 names. |
| 10 | Phone | Soil line 34 px below the last text line (y 1368; the old 93 px gap is cut). The tallest leaves rise beside Wine and Spirits at the right edge, clamped 6 mm clear. Loam band 190 px deep, about 38% of the phone art height. |
| 11 | Order | Col 1: Cocktails, then Beer & Cider (Draft, then Cider). Col 2: Wine, then Spirits (Agave, then Brandy). |
| 12 | Subheads | "Clásicos · Classics", "De la Casa · House Originals", "De Barril · Draft", "Sidra · Cider", "Por Copa · By the Glass", "Espumoso · Sparkling", "Agave", "Brandy". The H2s are in English. |
| 13 | Spirits | Descriptions are the draft wording minus the serve word: "Blanco tequila", "Añejo tequila", "VSOP Cognac". "pour" is a small-caps serve label before the price ("POUR 12"). The build asserts each draft desc ends in "pour". |
| 14 | Serve facts | From phg.recipe_versions (gateway log 241): Manhattan, glassware Coupe (9fb77eaa); House Daiquiri, Coupe (14d45e57); Old Fashioned, method "…strain over a large cube" (7095fd3d); Margarita, method "…strain over fresh ice" (f06abb74). They are set as the last item of each list, in small caps. The Daiquiri keeps "house demerara syrup". The Margarita's draft-supplied tasting note "Bright and citrus-forward." is roman and inline in the same flow (kept unbroken). No other cocktail has a tasting note in the source. |
| 15 | Title | Now "Cantina & cocktail bar, Iowa City: bar menu". |
| 16 | Content | Nothing invented. Every id and price is asserted. |

Contrast note: the wordmark's worst-pixel reading is 1.00 only because the horizon rule (the same colour) runs through the bottom of its text box. The letters themselves are 9.37:1 against the ground.

## missing_ingredients (what the draft lacks; ask Rob)
| Item | Missing |
|---|---|
| Czech Pilsner | brewery, ABV, pour size |
| Dry-Hopped IPA | brewery, ABV, pour size |
| Amber Lager | brewery, ABV, pour size |
| Dry Cider | producer, ABV, format (draft, can or bottle) |
| Malbec | producer, region, vintage, pour size |
| Pinot Grigio | producer, region, vintage, pour size |
| Brut Rosé | producer, region, vintage; is 13 a glass or a bottle price? |
| Blanco Tequila | brand, pour size (age: n/a for blanco) |
| Añejo Tequila | brand, age statement, pour size |
| Cognac VSOP | house or brand, pour size |
| Brown Butter Old Fashioned | dairy allergen confirmation (brown butter fat-wash) |
| Margarita, Manhattan, House Daiquiri | none (components, garnish and serve are sourced) |

## Geometry (CSS px at 96/in; trim 816 x 1056; bleed 12; safe inset 48)
- **Header:** x 64, CANTINA 82 px, cap top 64, baseline 118 (horizon rule). Sub-line baseline about 150.
- **Col 1:** x 64 to 408 (344). **Col 2:** x 440 to 640 (200, its real measure). Gutter 32.
- **Art:**
  - Soil surface level at y 896, rising to y 808 between x 380 and 816.
  - Rosette base x 730, S sized to reach the horizon.
  - The 6 mm clamp shortens leaves near the text (see `render_report.json`).
  - Silhouette 18.3% of the page.
- **Palette:**
  - Ground #1B1510.
  - Drawing and wordmark #9CC3B5.
  - Loam ink is #9CC3B5 mixed 55% toward the ground.
  - H2 #D98E6A.
  - Text #EEE4D1 / #C4B9A6.
- **Outputs:**
  - `preview-letter.png` 2550 x 3300
  - `preview-letter-bleed.png` 2625 x 3375
  - `preview-phone.png` 1170 x 4674

## Iteration log (measured)
| Step | Primary | Ratio | Kept? |
|---|---|---|---|
| I5 reference | 7.30% | 9.06 | |
| Flat soil, first cross-contour pass | 2.84% | 2.12 | no |
| Steep mound (top 760) | shrank the plant | | no |
| Gentle mound (xa 380, top 808) + tighter arcs (swell 0.8) | 4.94% | 19.2 | improving |
| + swell 0.6, cone swell 0.8 | 5.53% | 18.4 | **checkpoint (before)** |

The primary area is below I5's 7.30% (the teeth, heart slab and even fans are gone, as asked), but the ratio is much higher (22 vs 9): one clear dominant region.

## Device inventory and subtraction log
| Device | Decision |
|---|---|
| Wordmark on horizon rule | keep |
| Italic sub-line | keep |
| Terracotta H2 | keep |
| Bilingual H3 | keep |
| Muted prices | keep |
| Small-caps serve labels | keep |
| Soil surface / mound | keep |
| Loam A/B/C horizons | keep |
| 4 roots | keep |
| Rosette outlines | keep |
| Modulated longitudinal hatch | keep |
| Cross-contour front leaves | keep |
| Spiral cone arcs | keep |
| **Marginal teeth** | **removed**; ablation: ratio 18.4 rose to 22.4, primary unchanged |
| **Heart slab** | **removed** (in I5) |
| **Tip whiskers** | **removed** (in I5) |
| **Crumbs, root fan and water strata (I6)** | **not carried over** |
| **Centred header and duplicate uppercase sub-lines** | **removed** |

5 of 20 removed (25%).

## visual_tests (before = checkpoint with teeth; after = final)
```json
{"file": "preview-letter-before.png", "squint_salient_regions": 5, "primary_area_pct": 5.53, "primary_to_secondary": 18.38, "ground_luminance": 0.109, "value_range_p5_p95": [0.078, 0.433], "accent_area_pct": 0.21, "visual_centroid": [0.62, 0.541]}
{"file": "preview-letter.png", "squint_salient_regions": 4, "primary_area_pct": 5.53, "primary_to_secondary": 22.37, "ground_luminance": 0.109, "value_range_p5_p95": [0.078, 0.431], "accent_area_pct": 0.21, "visual_centroid": [0.617, 0.537]}
```

## Open items
- Column ends differ by 160 px (see fix 7).
- Phone rows use 18 px description leading, so phone row tops are not all on the 8 px grid.
- The data in the missing_ingredients table above.
- "CANTINA" is still a placeholder word.
