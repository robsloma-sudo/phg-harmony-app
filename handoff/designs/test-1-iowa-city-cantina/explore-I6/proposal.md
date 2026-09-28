# TEST-1 explore-I6: Night Field, round 6 (from I5, the best so far at 73.8; I5 kept as the checkpoint)

**Thesis:** A cross-section of a Mexican agave growing out of Iowa soil. Above a single soil line the rosette is engraved in agave blue-green; below it lies a band of warmer, darker black loam, drawn in the same engraved grammar and cropped by the page.

**Concept words:** rooted, loam, cross-section, engraved, printed, quiet.

**Avoid-list:**
- waves, ripples or light glints in the soil
- root fans that read as sunbursts
- vector hairlines
- taxonomy-speak in the copy
- a second drawing
- boxes, leaders, taglines
- any change that measures worse than I5

## Round 6 changes
| # | Change | Result |
|---|---|---|
| 1 | Iowa soil | Below the soil line (y 972) is a separate band: loam #120C08 (warmer and darker than the #1B1510 ground) with plate tone. It is engraved with crumb strokes: 650 short tapered strokes at ±35° (30% of them near-vertical), densest just under the soil line and thinning with depth, plus two broken strata lines at 42% and 78% of the band depth. The same tapered-stroke grammar as the leaves. The 15-root fan is gone; 4 short roots (≈ 80 px) drop from the base and are cropped by the loam and the trim. Two earlier soil treatments were rejected on the render: long wavy strata read as water, and straight staggered dashes read as moonlight glints. |
| 2 | Wordmark lock-up | Measured by pixel scan from CANTINA's baseline to the cap top of "& COCKTAIL BAR": 36 px before (in CSS px at 96/in; the review's "~70" was probably in another unit), now **32 px** (`.sub.a` margin 20 to 16). The 4 px recovered is less than one 8 px grid step, so the list top stays at y 240, the grid is kept, and no baseline was broken. |
| 3 | Art vs column 2 | Moving the rosette 40 px right (bx 775) dropped the squint ratio from 9.06 to 5.54, and moving it down dropped it to 1.4-1.5, so both were **reverted**. Instead the art keeps a larger text clearance: 34 px (9 mm) instead of 23 px (6 mm), with the centre at bx 740. Leaf tips now stop at least 9 mm from Dry-Hopped IPA, Dry sparkling cider and the Wine lines (clamps: back2 0.79, leaf0 0.70, leaf1 0.64, leaf3 0.85, leaf10 0.94). The lowest leaf runs out to x ≈ 175, under Spirits, as a lead-in. |
| 4 | Materiality | Only the art group gets an ink-spread filter (feTurbulence 1.6, displacement 0.9 CSS px ≈ 2.8 device px), so edges break up like printed ink at 1:1. Every leaf fill and the loam band also carry plate tone: a 61 px tile of fine grain in the accent colour, alpha ≤ 30/255. None of this reaches the text: the art stays 9 mm clear, and the worst-pixel contrast is unchanged. |
| 5 | Spirits | Reverted to the draft wording: "Blanco tequila pour", "Añejo tequila pour", "VSOP Cognac pour". The public.beverage_categories citations are removed. |
| 6 | Daiquiri | "White rum · fresh lime juice · house demerara syrup · lime coin". "house demerara syrup" is taken from the draft desc and asserted in the build. |
| 7 | Wraps | A middot stays at the end of line 1 when a list wraps (the separator is bound to the ingredient before it), so a wrapped list reads as one list, e.g. "White rum · fresh lime juice · / house demerara syrup · lime coin". The last two ingredients stay together, so no garnish sits alone. |
| 8 | Margarita | Ingredients and garnish, then the italic line "Bright and citrus-forward." This tasting note is **draft-supplied** (from the Margarita's `desc`). The other cocktails have no tasting note in the source, so none is shown. |
| 9 | Sub-labels | 11 px DM Sans 500, contrast 6.92:1. |
| 10 | Content | Otherwise unchanged; the build asserts every id and price. |

## Geometry (CSS px at 96/in; trim 816 x 1056; bleed 12 px on every side; safe inset 48)
- **Header:** centred on x 408. CANTINA cap top 62 to 64, baseline 117; sub-line cap top 149.
- **Columns:** col 1 at x 64 to 392 and col 2 at x 424 to 752 (328 + 32 + 328), both starting at y 240. Col 1 ends at 784 and col 2 at 728. The grid is 8 px; one item gap (8) and one section gap (32).
- **Art:**
  - Soil line at y 972. Rosette base (740, 988), S = 750.
  - Loam band from y 972 to the bleed.
  - Bounding box x 0 to 816, y 256 to 1056; silhouette 23.1% of the page.
- **Palette:**
  - Ground #1B1510; loam #120C08.
  - One accent #9CC3B5: wordmark, heads and art.
  - Ivories #EEE4D1, #C4B9A6, #A99F8E.
  - Accent share by colour match is 6.06% (≤ 8%).
- **Outputs:**
  - `preview-letter.png` (2550 x 3300, trim)
  - `preview-letter-bleed.png` (2625 x 3375)
  - `preview-phone.png` (1170 x 5583; one column, and the same soil band, rosette and roots close the page)

## Contrast (worst pixel; letter and phone are the same)
| Role | Min contrast |
|---|---|
| Names | 14.34 |
| Accent | 9.37 |
| Prices and descriptions | 9.33 |
| Sub-labels | 6.92 |

## Measured decisions (revert rule)
| Test | Primary % | Ratio | Kept? |
|---|---|---|---|
| I5 final | 7.30 | 9.06 | reference |
| Rosette 40 px right (bx 775, clearance 23) | 6.68 | 5.54 | reverted |
| Rosette down 20-24 px | 3.8 | 1.4-1.5 | reverted |
| bx 740, clearance 34 (final placement) | 7.30 | 8.90 | kept: -1.8% ratio for 3 mm more clearance by col 2 (the brief's explicit ask) |
| No plate tone | 4.48 | 2.45 | plate tone kept |
| No ink spread | 7.31 | 8.83 | ink kept (materiality; neutral on the metric) |

## Device inventory and subtraction log
| # | Device | Decision |
|---|---|---|
| 1 | Wordmark and lock-up | keep |
| 2 | Sub-line | keep |
| 3 | Accent heads | keep |
| 4 | Sub-labels | keep |
| 5 | Muted inline prices | keep |
| 6 | Italic tasting note | keep |
| 7 | Soil line | keep |
| 8 | Loam band | keep (the Iowa material) |
| 9 | Crumb strokes | keep, **density cut 900 to 650** (it was busy at thumbnail size; no metric loss) |
| 10 | Two broken strata lines | keep |
| 11 | Roots | **cut from 15 to 4** (the fan read as a sunburst) |
| 12 | Long wavy strata | **removed** (read as water) |
| 13 | Staggered dash strata | **removed** (read as glints) |
| 14 | Rosette leaves, teeth, cupped margin | keep |
| 15 | Tapered hatch | keep |
| 16 | Plate tone | keep (ablation: ratio 8.9 falls to 2.45) |
| 17 | Ink spread | keep |
| 18 | Taxonomy spirit lines | **removed** (brief) |

3 devices removed outright and 2 cut back, of 18.

## visual_tests (before = I6 checkpoint with 900 crumbs; after = final)
```json
{"file": "preview-letter-before.png", "squint_salient_regions": 4, "primary_area_pct": 7.21, "primary_to_secondary": 8.98, "ground_luminance": 0.109, "value_range_p5_p95": [0.071, 0.462], "accent_area_pct": 0.0, "visual_centroid": [0.611, 0.63]}
{"file": "preview-letter.png", "squint_salient_regions": 5, "primary_area_pct": 7.3, "primary_to_secondary": 8.9, "ground_luminance": 0.107, "value_range_p5_p95": [0.07, 0.459], "accent_area_pct": 0.0, "visual_centroid": [0.616, 0.628]}
```
`accent_area_pct` is 0.0 because the tool's saturation threshold misses this low-saturation accent; by colour match the accent covers 6.06%.

## Sources
- `../build/draft_doc.json`.
- Garnishes: phg.recipe_versions f06abb74, 14d45e57, 7095fd3d, 9fb77eaa (see `../round-17/proposal.md`).
- No library documents and no taxonomy text.

## Open items
- ABV, region and brand are waiting on Rob.
- Brut Rosé 13 has no pour label in the draft.
- "CANTINA" is still the placeholder venue word.
