# TEST-1 explore-I3: Night Field, round 3 (thesis written before any render)

**Thesis:** A gold-engraved agave rises out of an Iowa contour-strip field at night. It is one engraving, and the landform, not a label, is what makes it this cantina in Iowa City.

**Concept words:** rooted, contour, strip-cropped, engraved, night, horizon.

**Avoid-list:**
- field forms that read as foliage (no tapering, no teeth, no leaf shapes in the field)
- a second drawing, stamps, barns, corn cobs, suns or stars
- boxes, leaders, price ornaments
- taglines
- equal-pitch barcode stripes
- solid gold fills
- text within 6 mm of the art
- ragged column ends
- one-word widows

**The one gesture:** a single engraving at one stroke weight.
- A straight horizon line crosses the page.
- Below it, curved contour strips alternate between rows that follow the contour and furrows that run toward a vanishing point on the horizon. The strips widen toward the viewer.
- The agave is planted in the right-hand strips. Near strips pass in front of its base, so it visibly grows out of the field, and its cone rises into the upper right.
- The agave has swelling and tapering contour hatch, made by varying the spacing, with teeth, spines and a twisting cone.

The thesis, concept words, avoid-list and gesture above were written before the first render. I2 stays unchanged as the checkpoint (72.1, all gates passing).

## Round 3 fixes
| # | Fix | Result (from `render_report.json` / `visual_tests.json`) |
|---|---|---|
| 1 | The Iowa field reads within a second | See "The field" below. There is no taper, no teeth and no leaf shape anywhere in the field. |
| 2 | Engraving craft | Cross-contour hatch (see "The agave"). The vertical parallel stripes in the cone and back leaves are gone. |
| 3 | Dead top-right field | The cone and back leaves now rise to y 176, filling x 610-816 from y 176 down. The agave's clearance loop keeps every leaf at least 23 px (6 mm) from every text line; 4 leaves were shortened (to 94%, 85%, 94% and 79%). |
| 3 | Column ends | Both text columns end at y 808.0 (0 mm difference). |
| 3 | Top margin | The wordmark's text box starts at y 64, the same as the 64 px left margin. |
| 4 | Col 1 descriptions | At most 2 lines. |
| 4 | Baseline grid | One 8 px increment across both columns. All 14 row tops are multiples of 8, and Spirits and Wine heads align at y 608. |
| 4 | No widows | Multi-word ingredients are joined with non-breaking spaces, and line breaks only fall after a "·". Hyphenated words and the Margarita's sentence never split. No one-word widows on letter or phone. |
| 4 | Margarita | "… lime wheel. Bright and citrus-forward." now runs on in the same text, not as a separate line. |
| 4 | Sub-labels | 10.5 px DM Sans, #B3B09E, contrast 7.08. |
| 4 | Prices | Ivory #EFE6D2 at weight 400: stronger than the descriptions (#C9C2AF, 12.5 px) and lighter than the names (500). Inline 0.9 em after the name; eye travel 4% (col 1), 9% (col 2), 5% (phone). |
| 5 | Order | Cocktails (Margarita first), Spirits (Agave, Brandy), then Draft Beer, Cider directly under it, then Wine. Agave spirits still come before wine. |
| 6 | Content | Identical to I2. Nothing is added. The missing ABV, region and brand data is still waiting on Rob. |

## The field (the Iowa half of the thesis)
- **Horizon:** a straight line across the full page at y 847, 39 px below the end of the text.
- **Strips:** 8 contour strips below the horizon.
  - Their boundaries roll with two sine waves (amplitude 60 px, times depth^1.3).
  - Strip depth grows as p^1.75, so the strips widen toward the viewer.
- **Alternating textures (strip cropping):**
  - Contour rows follow the curve, at about 5.5 px pitch.
  - Every second strip from the fourth on (strips 4, 6 and 8) is furrows instead: rays toward a vanishing point on the horizon at x 408, 11 px apart along the page bottom.
  - Rays are dropped per ray, using their true perpendicular spacing, so they never pack solid.
  - The three far strips are all rows, so no sun-like fan forms at the vanishing point.
- **No boundary lines:** texture changes alone define the strips, as in an engraving.
- **Agave planting:** strips nearer than the agave's ground point (x 760, y 945) are drawn after the agave and pass in front of its base, so it visibly rises out of the field.

## The agave
- **Base and scale:** the base is at (770, 1000), hidden in the field. The tallest leaf is S = 880.
- **Leaves:** 4 back, 3 mid and 4 front leaves, with seeded asymmetric angles and lengths (±7%) and individual droop and curl. Each leaf has:
  - half-width t^0.28 (1-t)
  - a channel crease
  - hooked marginal teeth (2.6 px out, 2.2 px toward the tip, every ~9 px)
  - a terminal spine of 7-16 px
- **Cross-contour hatch:** gently bowed arcs across each leaf (bow 0.12 of the half-width) show the cupped channel.
  - Spacing along the leaf is pitch × (0.75 + 0.8 t^1.5) with pitch 2.5 px, so the hatch is dense in the shaded heart and opens toward the tip. Tone comes from spacing, not stroke width.
  - Arcs cross the whole leaf for the first 60% of its length, then only the shaded half.
- **Cone:** 1.0 S tall and 0.095 S wide. Inclined arcs spiral round it (slope 1.4). Every arc covers the shaded side, and every second one runs on across the lit side.
- **One stroke weight:** 1.25 CSS px (3.9 px at 300 dpi) for everything, including the field.
- **One colour:** gold #C8A765, with no fills other than the ground used for occlusion.
- **Footprint:** the drawing's bounding box is x 0 to 816, y 176 to 1056, and its filled silhouette covers 31.4% of the page.

## Layout geometry (letter, CSS px at 96/in, rendered x3.125 = 2550 x 3300 at 300 dpi)
- **Page:** 816 x 1056, flat #10291F.
- **Margins:** top 64 (wordmark text), left 64, bottom text end 808. The drawing owns the right and the bottom.
- **Header:** placed at top 73 so the wordmark's text box starts at y 64.
  - CANTINA: Cormorant Garamond 500, 82 px, tracking .34em, gold.
  - Sub-lines "& Cocktail Bar" and "Iowa City, Iowa": DM Sans 500, 11.5 px, tracking .34em, #C9C2AF.
- **Col 1:** x 64 to 400 (336 wide), y 240 to 808: Cocktails, then a 72 px gap, then Spirits.
- **Col 2:** x 432 to 602 (170 wide; text right edge ≤ 602), y 240 to 808: Draft Beer, a 72 px gap, Cider, a 72 px gap, Wine.
  - Gaps are chosen automatically in whole grid steps so the columns end together: 40 px extra per gap in each column.
- **Grid:** 8 px.
  - H2: 16 px line, 8 px after.
  - H3: 16 px line, 16 px before.
  - Name row: 24 px line.
  - Description: 16 px line.
  - Item gap: 8 px.
- **Type:**
  - H2: DM Sans 600, 13.5 px, tracking .30em, gold.
  - H3: DM Sans 500, 10.5 px, tracking .22em, #B3B09E.
  - Names: Source Serif 4 500, 16.5 px, #EFE6D2.
  - Prices: Source Serif 4 400, 16.5 px, #EFE6D2, tabular.
  - Descriptions: Source Serif 4 400, 12.5 px, #C9C2AF.
- **Text extent:** x 64 to 705, y 64 to 808.
- **Phone (1170 x 5589, 390 CSS px at 3x):** one column in the same order, with 34 px padding. The same field-and-agave engraving closes the page in a 390 x 560 box: horizon at 290, agave S = 520.

## Contrast (worst pixel, letter and phone)
| Role | Min contrast |
|---|---|
| Names and prices | 12.45 |
| Descriptions and sub-line | 8.70 |
| Sub-labels | 7.08 |
| Gold heads and wordmark | 6.75 |

All roles pass 4.5:1. No text sits on the drawing.

## Iteration log (hypothesis, then result; best-so-far kept)
1. **Field of strips plus the agave planted in them.** The field read at once, but furrow strips rendered solid (rays converged). The contours were too flat and the right-hand leaves drooped into arcs.
2. **Furrow line dropping by depth, hill amplitude 60, uniform per-column gaps.** It read as rolling strip fields. Lateral rays still packed solid.
3. **Per-ray perpendicular dropping.** The furrows were clean. The squint test was weak (primary 3.5%, ratio 1.84) and the cone was still striped.
4. **Cross-contour arcs.** Arcs replaced the stripes, but they were staircased (index snapping). Fixed by interpolating along the axis. A bow of 0.35 made fish scales, so it went down to 0.12.
5. **Quieter field (rows 5.5, furrows 11), denser agave.** Ratio 1.2 to 1.7, because the agave mass was split mid-leaf.
6. **Full-width shading to 60% of each leaf.** Primary 8.07%, ratio 95. **Checkpoint, and the "before" of the subtraction pass.**
7. **Vanishing point moved behind the agave.** The furrows went near-horizontal and the strip reading was lost. **Reverted** (iterate_with_reversion). Instead, the far three strips became rows, which removes the sun-like fan.

## Device inventory and subtraction log
| # | Device | Decision | Evidence |
|---|---|---|---|
| 1 | CANTINA wordmark | keep | The one display word |
| 2 | Tracked sub-line (2 lines of 3 words or fewer) | keep | Venue |
| 3 | Gold section heads | keep | The only accent outside the art |
| 4 | Quiet sub-labels | keep | The draft's groups |
| 5 | Inline ivory prices | keep | The price-association fix |
| 6 | Horizon line | keep | Makes the field a landscape |
| 7 | Contour-row strips | keep | The field |
| 8 | Furrow strips (alternating) | keep | Strip cropping is the Iowa read |
| 9 | Agave leaves with ground-fill occlusion | keep | The plant |
| 10 | Marginal teeth | keep | Anatomy |
| 11 | Terminal spines | keep | Anatomy |
| 12 | Channel crease | keep | Ablation: ratio 95 fell to 85 and the leaves flattened |
| 13 | Cross-contour hatch | keep | The craft fix |
| 14 | Spiral cone | keep | Fills the top-right; no barcode |
| 15 | Strip boundary lines | **removed** | Ablation: the strips still read by texture, the field quieted, ratio rose 95 to 241 |
| 16 | Two shard leaves (-64°, -76°, clamped) | **removed** | Read as broken fragments. Ablation: 8.07% to 7.97%, no loss |
| 17 | Two stub leaves (-38°, -52°, clamped behind col 2) | **removed** | Same problem; no loss (7.92%, ratio 241) |
| 18 | Duplicate horizon path (drawn twice) | **removed** | Now drawn once, as strip 0's edge |
| 19 | Furrows in the far strip 2 (the "sun fan") | **removed** | It read as a rising sun (avoid-list) |

5 of 19 devices removed (26%). Every kept device either has an ablation behind it or is required by the brief.

## visual_tests (before = iteration-6 checkpoint; after = final)
```json
{"file": "preview-letter-before.png", "squint_salient_regions": 2, "primary_area_pct": 8.07, "primary_to_secondary": 95.05, "ground_luminance": 0.17, "value_range_p5_p95": [0.125, 0.458], "accent_area_pct": 2.2, "visual_centroid": [0.623, 0.604]}
{"file": "preview-letter.png", "squint_salient_regions": 2, "primary_area_pct": 7.92, "primary_to_secondary": 241.24, "ground_luminance": 0.17, "value_range_p5_p95": [0.125, 0.451], "accent_area_pct": 1.99, "visual_centroid": [0.63, 0.591]}
```
- For comparison, I2 had primary 12.4%, ratio 79, accent 1.9%.
- The primary region is now smaller because the mass sits in the agave, not in solid-looking shading, but it is far more dominant (241x the next region).
- Accent is 1.99%, well under 8%.

## References
- The ref-02 panel 3 grammar (green, gold line, short columns), which the critic says I2 re-set too closely. I3 departs from it with the landform, the cross-contour engraving and the column tiers.
- Contour-strip farming on Iowa's rolling ground is the ownable subject. It is drawn from geometry, not copied from any artwork.
- I used no PHG library documents.
- Garnish citations: `../round-17/proposal.md` (phg.recipe_versions f06abb74, 14d45e57, 7095fd3d, 9fb77eaa).

## Open items
- The descriptions still lack ABV, region and brand; this is waiting on Rob.
- Brut Rosé 13 has no pour label in the draft.
- The drawing's silhouette covers 31.4% of the page. The text layer limits it to the right third and the bottom band.
