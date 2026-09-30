# TEST-1 explore-I8: Night Field, art fix (from I7; content and type unchanged)

**Thesis (unchanged):** A Mexican agave, engraved in blue-green, grows out of level Iowa loam. The wordmark stands on its own horizon rule above the list.

**Avoid-list additions:**
- a mound, waves or undulating strata (they read as sea)
- tall thin stacked leaves (they read as sails)
- a curved "hull" under the rosette
- long flowing loam strokes

## What changed (art only)
| Area | I7 | I8 |
|---|---|---|
| Soil surface | Level under the list, then a smooth mound under the rosette | A single straight, level soil line at y 896, across the full page and into the bleed |
| Loam | Long tapered strata following the mound | A soil profile, all horizontal: an A horizon of dense short dashes (5-14 px) in close rows; two broken straight horizon boundaries (38%, 74%); a B horizon of mixed short dashes and stipple with 14 clod ovals; a C horizon of sparse stipple with 9 pebble ovals. Drawn at lower contrast (accent mixed 55% toward the ground). No curves except the ovals. |
| Roots | 4 wavy roots | 5 roots going straight down from the base, tapering |
| Rosette | Sized to reach the wordmark horizon (S ≈ 780) with cross-contour "hull" arcs on the front leaves | I5's leaf table and proportions: 4 back, 6 mid and 8 front leaves plus the cone, from one base point. S = 660; base 6 px below the soil line, so the rosette sits on the line. Centre x 745, to the right of col 2, so the tall leaves rise beside Wine and Spirits rather than being clamped into slivers. Front leaves use I5's longitudinal hatch (no cross-contour arcs, which made the hull). |
| Kept from I7 | | No teeth. Modulated hatch: lines swell toward the shaded edge and thin toward the light; line dropping; heart lines. One accent colour. The 6 mm text clamp shortened back2 to 0.58, leaf0 to 0.49 and leaf1 to 0.61. |

Content, typography, order, the bilingual subheads, serve facts, POUR labels, terracotta H2s, the flush-left wordmark with its horizon rule, and the 8 px letter grid are all identical to I7. All 14 letter row tops are multiples of 8, and every item id and price is asserted.

## Thumbnail self-test (300 px wide)
- **I8 variant rejected:** a low wide rosette with heavy droop and curl read as a lotus or artichoke.
- **Final (I5 table, S 660, x 745):** at 300 px it reads as a spiky agave rosette standing on a band of soil. The soil band reads as earth (stippled, dashed, level), not water.
- **Remaining risk:** the largest front-right leaf has a broad curved outline that can still read as a bulb at 1:1. Its outline is the leaf's natural lanceolate curve, not a hull shape under the plant.

## visual_tests (before = I7 final; after = I8 final)
```json
{"file": "preview-letter-before.png", "squint_salient_regions": 4, "primary_area_pct": 5.53, "primary_to_secondary": 22.37, "ground_luminance": 0.109, "value_range_p5_p95": [0.078, 0.431], "accent_area_pct": 0.21, "visual_centroid": [0.617, 0.537]}
{"file": "preview-letter.png", "squint_salient_regions": 5, "primary_area_pct": 2.86, "primary_to_secondary": 4.56, "ground_luminance": 0.109, "value_range_p5_p95": [0.078, 0.403], "accent_area_pct": 0.21, "visual_centroid": [0.591, 0.532]}
```
**This is a regression on the squint metrics.** Primary area fell from 5.53% to 2.86% and the ratio from 22.4 to 4.6: the smaller, open-hatched I5-proportioned rosette covers less dense tone than I7's large one. The squint numbers were traded for the anatomy read the brief asked for. If the Coordinator weights the metric, the fastest recovery is a larger S with the same table, or I5's heavier heart shading.

## Contrast (worst pixel)
| Role | Min contrast |
|---|---|
| Names | 14.34 |
| Body text, H3s and serve labels | 9.33 |
| Terracotta H2s | 6.91 |

The wordmark reads 1.00 only because its same-colour horizon rule crosses its text box; the letters themselves are 9.37:1.

## Subtraction log
| Device | Decision |
|---|---|
| Soil mound | removed |
| Undulating strata | removed |
| Cross-contour front arcs (the hull) | removed |
| Wavy roots | replaced by straight ones |
| Long loam strokes | replaced by dashes and stipple |
| Clod and pebble ovals | added |

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


## Open items
- Column ends differ by 160 px (col 1 ends at 864, col 2 at 704). The rosette fills the space under col 2.
- **Phone grid still open:** phone row tops sit at mod-8 offsets 1, 3, 5 and 7 (18 px name and description leading).
- The squint regression above.
- "CANTINA" is still a placeholder word.

Outputs:
- `preview-letter.png` 2550 x 3300
- `preview-letter-bleed.png` 2625 x 3375
- `preview-phone.png` 1170 x 4674
