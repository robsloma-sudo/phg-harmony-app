# TEST-1 explore-I2: Night Field, round 2 (thesis written before any render)

**Thesis:** A Jalisco agave, engraved in gold, is rooted in Iowa ground. Its lowest leaves flatten into the curved rows of a contour-ploughed field and run off the page, so the one drawing belongs only to a cantina in Iowa City.

**Concept words:** rooted, engraved, contour, night, field, precise.

**Avoid-list:**
- a second drawing, and no stamps (cactus, sun, star, corn cob, barn)
- boxes, leaders, price ornaments, tables
- taglines of any kind
- tracked caps on labels of more than 3 words
- hairline serifs at small sizes on the dark ground
- a symmetric vector starburst (round 1's failure)
- solid gold fills
- text within 6 mm of the drawing

**The one gesture:** a single agave engraving, drawn to a hard crop at the right and bottom trim, covering about half the page. It has:
- thick, channelled leaves with fine marginal teeth and terminal spines
- a heavily hatched central cone
- shading from hatching only, at one stroke weight throughout
- lowest leaves whose hatch lines become the field's furrows, converging on the plant as rows converge on a vanishing point

The Iowa half of the idea lives inside the drawing, not in a label.

The thesis, concept words and avoid-list above were written before the first render. explore-I stays unchanged as the round-1 checkpoint.

## Round 2 fixes (from the review, and DESIGN_THEORY_BRIEF section 5)
| Fix | What I did | Measured |
|---|---|---|
| 1 Prices | Each price is inline, 0.9 em after the name, in Source Serif 400 and muted ivory #C9C2AF (names are 500 ivory), with tabular figures | Gap is 15 px on letter and 16 px on phone. Eye travel is 6-8% of the column on letter and 5% on phone; every row is under the 40% limit and on the name's line. |
| 2 Descriptions | Full draft text, including the style words; full component names; garnish from phg.recipe_versions; "Bright and citrus-forward" kept; spirits print "pour" | See the content table |
| 3 Order | Classics runs Margarita, then Manhattan. The reading order is Cocktails, Spirits (Agave, Brandy), Wine, Draft Beer, Cider | |
| 4 Tagline | Removed. The page has no tagline at all | |
| 5 Agave | Redrawn as an engraving (see Gesture) and set to a hard crop | Squint primary region 12.4% of the page, 79x the next region |
| 6 Iowa City | The lowest leaves become contour-ploughed furrow strips that run off the left trim and converge on the plant | The drawing is still one piece, in one stroke weight |
| 7 Sub-labels | DM Sans 9.5 px, tracking .24em, #A8A796. They are smaller and quieter than the 13.5 px gold heads | Contrast 6.35:1 |

## Content (`build.py` asserts every id and price, the hidden bitters and the verbatim Margarita tail)
| Item | Price | Description | Source |
|---|---|---|---|
| Margarita | 15 | Tequila blanco · fresh lime juice · orange liqueur · agave syrup · lime wheel / Bright and citrus-forward | components; garnish rv f06abb74; tail from the draft desc |
| Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry | components; Aromatic Bitters hidden (public_components false); garnish rv 9fb77eaa (already a component) |
| House Daiquiri | 14 | White rum · fresh lime juice · demerara syrup · lime coin | components; garnish rv 14d45e57 |
| Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel | components (house_recipe=false: names only, no quantities); garnish rv 7095fd3d |
| Blanco Tequila / Añejo Tequila | 12 / 16 | Blanco tequila pour / Añejo tequila pour | draft desc |
| Cognac VSOP | 18 | VSOP Cognac pour | draft desc |
| Malbec / Pinot Grigio | 12 / 11 | Dry red wine / Dry white wine | draft desc |
| Brut Rosé | 13 | Dry sparkling rosé | draft desc |
| Czech Pilsner / Dry-Hopped IPA / Amber Lager | 7 / 8 / 7 | Crisp pale lager / Hop-forward draft IPA / Toasty amber lager | draft desc |
| Dry Cider | 8 | Dry sparkling cider | draft desc |

On letter, the Old Fashioned's price sits on the name line and its description is two lines below it, so the description never touches the price.

## Layout geometry (letter, CSS px at 96/in, rendered x3.125 = 2550 x 3300 at 300 dpi)
- **Page:** 816 x 1056, flat #10291F. No frame, rules, boxes or tagline.
- **Header:** centred, y 58 to 192.
  - "CANTINA" in Cormorant Garamond 500, 82 px, tracking .34em, gold #C8A765, at y 58 to 140.
  - "& Cocktail Bar" and "Iowa City, Iowa" below it in DM Sans 500, 11.5 px, tracking .34em, #C9C2AF.
- **Columns:** the reading layer takes the left two-thirds so the drawing can own the right third and the bottom.
  - Col 1 is at x 64 to 332 (268 wide) and y 246 to 816: Cocktails, then Spirits.
  - Col 2 is at x 362 to 558 (196 wide) and y 246 to 745: Wine, Draft Beer, Cider.
  - Section gap 34 px, item gap 10 px.
- **Text extent:** x 64 to 705, y 49 to 816. All text is at least 0.5 in inside the trim.
- **Type:**
  - Section heads (H2): DM Sans 600, 13.5 px, tracking .30em, gold.
  - Sub-labels (H3): DM Sans 500, 9.5 px, #A8A796.
  - Names: Source Serif 4 500, 16.5 px (12.4 pt, 52 px at 300 dpi), #EFE6D2.
  - Prices: Source Serif 4 400, 16.5 px, #C9C2AF, inline.
  - Descriptions: Source Serif 4 400, 12.5 px (9.4 pt), #C9C2AF.
  - There are no italics and no hairline serifs.
- **Gesture:**
  - The base point is at (772, 1100). The tallest leaf is S = 860 px, and the cone rises to about y 245.
  - The drawing is cropped by the right and bottom trim, and its furrow strips cross the left trim.
  - Footprint: the drawing's bounding box covers x 0 to 816, y 260 to 1056. Its filled silhouette covers 30.6% of the page. It holds the right third from y 260 down and the full width below y 890.
  - Clearance: pass 1 records every text line box, and pass 2 shortens any leaf that would come within 23 px (6 mm) of one. Two leaves were shortened (to 88% and 82%). No text sits on the drawing.
- **Phone (1170 x 5472, 390 CSS px at 3x):** one column with 34 px padding and the same reading order. Names and prices are 18 px, descriptions 13.5 px. The same engraving, recomputed at S = 520 in a 390 x 500 box, closes the page and is cropped at the right and bottom.

### Gesture construction (one stroke weight: 1.25 CSS px = 3.9 px at 300 dpi)
- **Leaves:** 22 channelled leaves in back, middle and front rings. Angles and lengths are jittered deterministically (seeded, ±7%), and each leaf has its own droop and tip curl, so the rosette is asymmetric.
  - The half-width follows t^0.28 (1-t)^1.0: thick, and widest near the base.
  - Each leaf has a channel crease.
  - Marginal teeth are hooked 2.6 px outward and 2.2 px toward the tip, every ~9 px along both edges.
  - The terminal spine is 7 to 16 px long along the tip tangent.
- **Shading:** the light comes from the upper left.
  - Hatch lines run along the shaded half of each leaf at a 2.8 px pitch, and are longest near the edge, so the leaf reads as rolling away.
  - The heart of the rosette is in deep shadow, so the lit half is also hatched for the first ~70% of the length.
  - Lines are dropped as the leaf narrows (engraver's line dropping, staggered so no bands form), so tone stays even and never fills solid.
- **Central cone:** a heavy wrapped spike, 0.98 S tall and 0.10 S wide, hatched densely across its shaded two-thirds.
- **Furrows:** the 3 lowest leaves are strips that stop tapering. Their hatch lines are the ploughed rows, rolling gently and converging on the plant.
- **Occlusion:** every shape is filled with the ground colour, so front leaves hide back leaves.
- **Colour:** the drawing uses no second colour and no solid fills.

## Contrast (worst pixel behind each text box; letter and phone are the same)
| Role | Min contrast |
|---|---|
| Names | 12.45 |
| Prices, descriptions, sub-line | 8.70 |
| Gold heads and wordmark | 6.75 |
| Sub-labels | 6.35 |

Every role passes 4.5:1.

## Iterations, with the hypothesis for each (best-so-far kept)
1. **Hypothesis:** thick leaves plus teeth plus hatching make it read as an agave. The first render had real anatomy, but the top furrow was clamped (a cut plank), the leaves were needle-thin, and the cone had a stepped tip.
2. **Wider leaves, lower furrows.** The furrows read as a field. The cone's hatch then ended in a flat edge.
3. **Hatching regraded to hug the shaded edge.** The leaves gained volume. With the cone lines converged, the tip became a solid gold block: primary 5.5%, ratio 2.4. **Rejected,** because solid fill is not engraving.
4. **Engraver's line dropping.** The craft was right, but the dominance collapsed: primary 0.7%, ratio 1.0.
5. **Heart shading, a tighter pitch and a higher base.** Primary 11.6%, ratio 57.7, but the top furrow was clamped again.
6. **Staggered drop points (no banding) and lower furrow angles.** Primary 12.43%, ratio 77.6, no clamps. **This is the checkpoint, and the "before" for the subtraction pass.**

## Device inventory and subtraction log
| # | Device | Decision | Evidence |
|---|---|---|---|
| 1 | CANTINA wordmark | keep | The one display word |
| 2 | Two-line tracked sub-line | keep | Venue identity; each line is 3 words or fewer |
| 3 | Gold section heads | keep | The accent's only job outside the art |
| 4 | Quiet sub-labels | keep | The draft's groups (Classics, Agave, Brandy, ...) |
| 5 | Muted inline prices | keep | The price-association fix |
| 6 | Leaf outlines with ground-fill occlusion | keep | The drawing |
| 7 | Marginal teeth | keep | Anatomy asked for by the critic |
| 8 | Terminal spines | keep | Anatomy |
| 9 | Channel crease | keep | Ablation: without it, primary falls from 12.4% to 8.7% and the ratio from 79 to 2.2, and the leaves go flat |
| 10 | Shaded-edge hatching | keep | Volume and mass |
| 11 | Heart shading (lit half near the base) | keep | Ablation (heart=0): primary 7.3%, ratio 2.5; the dominant region breaks up |
| 12 | Hatched central cone | keep | Anatomy and mass |
| 13 | Furrow strips | keep | The Iowa half of the thesis |
| 14 | Seeded asymmetry | keep | It answers "symmetric starburst" |
| 15 | Spiral wrap lines across the cone | **removed** | They read as cracks. Ablation: primary 12.43 to 12.40, ratio 77.6 to 79.3, so it costs nothing |
| 16 | Outlines around the furrow strips | **removed** | They read as planks, not field. The rows now run continuously. No change to the metric |
| 17 | Marginal teeth on the furrow strips | **removed** | A field has no teeth. It confused the leaf and field reading |
| 18 | "Good drinks / Good people" tagline (from round 1) | **removed** | The critic's call and brief section 5 |
| 19 | "Draft" sub-label under Beer (merged into "Draft Beer") | **removed** | Carried over from round 1 |

5 of 19 devices removed (26%). All were tested on the render. The two that looked removable, the crease and the heart shading, were kept because their ablations broke the dominant region.

## visual_tests (before = iteration-6 checkpoint; after = final)
```json
{"file": "preview-letter-before.png", "squint_salient_regions": 4, "primary_area_pct": 12.43, "primary_to_secondary": 77.6, "ground_luminance": 0.161, "value_range_p5_p95": [0.129, 0.468], "accent_area_pct": 1.96, "visual_centroid": [0.615, 0.666]}
{"file": "preview-letter.png", "squint_salient_regions": 4, "primary_area_pct": 12.4, "primary_to_secondary": 79.32, "ground_luminance": 0.161, "value_range_p5_p95": [0.129, 0.467], "accent_area_pct": 1.9, "visual_centroid": [0.617, 0.665]}
```
For comparison, round 1 (explore-I) had primary 0.03%, ratio 1.07, accent 1.01%. The accent is now 1.9%, well under 8%, because the hatching mixes gold with the ground rather than filling solid.

## References
- ref-02 panel 3 (`handoff/designs/references/rob-2026-09-28/ref-02-3acf255d.png`) for the grammar: green ground, gold line art, short columns, gold tracked heads. The engraving, the crop, the furrows and the reading layer are new.
- I used no PHG library documents, so there are no document IDs to cite.
- Garnish citations come from `../round-17/proposal.md` (phg.recipe_versions f06abb74, 14d45e57, 7095fd3d, 9fb77eaa).

## Open items for the Coordinator
- The silhouette covers 30.6% of the page, not the requested 45-50%. The bounding box spans the right third from y 260 down and the full width below y 890. Growing it further would push the drawing within 6 mm of col 2 or the wordmark.
- Wine has no producer or region and only glass prices, so the `producer · region` / `glass | bottle` format is not used.
