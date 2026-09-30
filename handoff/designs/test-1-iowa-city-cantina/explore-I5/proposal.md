# TEST-1 explore-I5: Night Field, round 5 (from I4; I2 and I4 kept as checkpoints)

**Thesis:** An agave, engraved in its own blue-green, is rooted in Iowa's black loam. A single soil line divides the page: the plant rises above it, its roots run into the dark earth below and are cropped by the page, so Mexico and Iowa meet in one drawing.

**Concept words:** rooted, loam, engraved, blue-green, night soil, quiet.

**Avoid-list:**
- bottle green with gold (ref-02 panel 3's recipe)
- a second drawing, and field stripes that read as water
- solid slabs of hatching, and outline whiskers at the leaf tips
- boxes, leaders, price ornaments, taglines
- a middot at a line end, and a garnish alone on a line
- aging years, brands or 100%-agave claims

**The one gesture:** one engraving: soil line, rosette and roots, all in one accent colour.

## Round 5 fixes
| # | Fix | Result |
|---|---|---|
| 1 | Ownable palette and concept | Ground #1B1510 (Iowa black loam, a warm near-black brown). The one accent is #9CC3B5 (agave-leaf blue-green), used for the wordmark, section heads and the drawing. Reading inks are warm ivories #EEE4D1, #C4B9A6 and #A99F8E. The Iowa cue is inside the drawing: a single soil line across the page at y 972 (full width, into the bleed); the rosette is clipped above it, and 15 tapered roots fan into the loam below it and are cropped by the bottom trim. Accent share by colour match is 5.75% of the page (≤ 8%); `visual_tests` reports 0.0% because its saturation test (> 0.45) does not count this low-saturation accent. |
| 2 | Engraving craft | Hatch lines are now tapered filled slivers: they swell in over the first 10%, hold 1.8 CSS px (5.6 px at 300 dpi), and taper to a point over the last 35%. Tone comes from spacing (3.0 px nominal pitch, with engraver's line dropping below 2.7 px), not from stacking. The shaded half is hatched evenly (no clustering at the edge). The lit half gets every second line only (the old "heart" slab is gone). The cone is hatched only on its shaded half, and its lines fade before the tip. The minimum pitch of 2.7 CSS px is 8.4 device px at 300 dpi, so there is no moiré at print size. Terminal-spine whiskers are removed (`spines=0`); the leaf outlines close cleanly at the tip. The outline and soil line use a 1.25 px stroke. |
| 3 | Axis and margins | A true two-column grid: col 1 is at x 64 to 392 and col 2 at x 424 to 752 (328 each, 32 px gutter). Side margins are 64 and 64, so the text block's axis is x 408, the page centre, and the centred header sits on it. The asymmetry comes from the drawing alone. The wordmark's cap tops are at 64 px. |
| 4 | Rag | Each ingredient is a nowrap unit, and each "·" is bound to the ingredient before it. A script hides any separator whose next ingredient starts a new line, so no line ends in a middot. The last two ingredients are bound with an NBSP, so a garnish never sits alone: House Daiquiri now breaks "White rum · fresh lime juice / demerara syrup · lime coin". |
| 5 | Margarita | Ingredients including the garnish, then "Bright and citrus-forward." on its own line in Source Serif 4 italic. **Only drafts that supply a tasting note get one;** the Margarita is the only item whose draft description has one. |
| 6 | Spirits | Read through `phg_designer_query` (log ids 224 and 227) from `public.beverage_categories`: Blanco Tequila is "Blanco-class agave spirit · pour" (path `spirits.agave_spirits.tequila.blanco`, authority "NOM-006-SCFI-2012 §5, clase"); Añejo Tequila is "Añejo-class agave spirit · pour" (path `spirits.agave_spirits.tequila.anejo`, "NOM-006-SCFI-2012 §5, clase"); Cognac VSOP is "Grape brandy from Cognac · pour" (path `spirits.brandy_fruit_spirits.grape_brandy.cognac`, style `.cognac.vsop`). There are no ages (the VSOP node carries no age note), no brands and no 100%-agave claim. "pour" is the draft's own serve word. |
| 7 | Content | Everything else is unchanged from I4; `build.py` asserts every item id and price. |

Kept from I4:
- 12 px (3.2 mm) bleed on every side: the print file is `menu-bleed.html` / `preview-letter-bleed.png` (2625 x 3375), and the trim render is `preview-letter.png` (2550 x 3300).
- Muted inline prices (#C4B9A6, weight 400, 0.9 em after the name).
- One item pitch (8 px), one section gap (32 px) and the 8 px grid.
- 10.5 px sub-labels and non-breaking ingredients.

## Layout geometry (CSS px at 96/in; trim 816 x 1056; safe inset 48)
- **Header:** centred on x 408.
  - CANTINA: Cormorant Garamond 500, 82 px, tracking .34em, #9CC3B5, cap top at 64.
  - Sub-lines "& Cocktail Bar" and "Iowa City, Iowa": DM Sans 500, 11.5 px, #C4B9A6.
- **Col 1:** x 64 to 392, y 240 to 784: Cocktails (240 to 552), a 32 px gap, then Spirits (584 to 784).
- **Col 2:** x 424 to 752, y 240 to 728: Draft Beer (240 to 400), Cider (432 to 496), Wine (528 to 728).
- **Column ends:** col 2 ends 56 px above col 1. The rosette rises into that space under col 2 and stops 6 mm from the text. All 14 row tops are multiples of 8.
- **Type:**
  - H2: DM Sans 600, 13.5 px, tracking .30em, #9CC3B5.
  - H3: DM Sans 500, 10.5 px, #A99F8E.
  - Names: Source Serif 4 500, 16.5 px, #EEE4D1.
  - Prices: Source Serif 4 400, 16.5 px, #C4B9A6.
  - Descriptions: Source Serif 4 400, 12.5 px, #C4B9A6.
  - Tasting note: Source Serif 4 italic, 12.5 px.
- **Drawing:**
  - Soil line at y 972.
  - Rosette base (735, 988), S = 750. Twenty leaves: I2's back, mid and front leaves, fleshy profile t^0.24 (1-t)^0.95, cupped-margin line, marginal teeth, no whisker spines.
  - 15 tapered roots below the line.
  - Bounding box x 148 to 816+, y 256 to 1056+; filled silhouette 23.2% of the page.
  - The 6 mm clamp shortened 6 leaves (to 0.67-0.97).
- **Phone (1170 x 5583):** one column in the same order. The same soil line, rosette and roots close the page.

## Contrast (worst pixel; letter and phone are the same)
| Role | Min contrast |
|---|---|
| Names | 14.34 |
| Accent wordmark and heads | 9.37 |
| Prices, descriptions, sub-line | 9.33 |
| Sub-labels | 6.92 |

## Iteration log
1. **New palette, tapered hatch at I4 density** (accent #86AFA2). Hairline tapers read as nearly blank leaves: primary 0.95%, ratio 4.7.
2. **Heavier tapers at an open pitch.** Lines were still clustered at the edges, and their thick bases were hidden under front leaves.
3. **Full-body taper (tip-only fade), even spacing, sparse lit-side lines to 95% of the leaf.** It reads as line engraving: 3.27%, ratio 2.3.
4. **Accent lightened to #9CC3B5.** One clear mass: 7.27%, ratio 9.03. **Checkpoint, and the "before" of the subtraction pass.** #A9CFC0 gave 8.11% at ratio 8.75, so #9CC3B5 was kept.

## Device inventory and subtraction log
| # | Device | Decision | Evidence |
|---|---|---|---|
| 1 | CANTINA wordmark | keep | The one display word |
| 2 | Sub-line | keep | Venue and city |
| 3 | Accent section heads | keep | The only accent outside the art |
| 4 | Sub-labels | keep | The draft's groups |
| 5 | Muted inline prices | keep | Price association |
| 6 | Italic tasting note | keep | Brief item 5 |
| 7 | Soil line | keep | The Iowa cue: the rosette is rooted |
| 8 | Roots (15 tapered) | keep | The cue reads as rooted. Halving them to 8 cost 7.27 to 7.09 |
| 9 | Rootlets (branch roots) | **removed** | They tangled into a scribble. Ablation: 7.30%, ratio 9.06, no loss |
| 10 | Leaf outlines with occlusion | keep | The drawing |
| 11 | Marginal teeth | keep | Anatomy |
| 12 | Cupped-margin line | keep | Fleshy leaves (I4 fix). Ablation: 7.27 to 7.10 |
| 13 | Tapered shaded-side hatch | keep | Engraving tone |
| 14 | Sparse lit-side hatch | keep | Without it the leaves read blank (iteration 1) |
| 15 | Cone hatch (shaded half only) | keep | Anatomy, now light |
| 16 | Terminal-spine whiskers | **removed** | Critic: "overshooting whiskers" |
| 17 | Dense heart slab | **removed** | Replaced by the sparse lit-side lines |
| 18 | Channel crease | **removed** (in I4) | Duplicated the cupped-margin line |

4 of 18 removed (22%).

## visual_tests (before = iteration-4 checkpoint; after = final)
```json
{"file": "preview-letter-before.png", "squint_salient_regions": 9, "primary_area_pct": 7.27, "primary_to_secondary": 9.03, "ground_luminance": 0.101, "value_range_p5_p95": [0.079, 0.459], "accent_area_pct": 0.0, "visual_centroid": [0.627, 0.64]}
{"file": "preview-letter.png", "squint_salient_regions": 8, "primary_area_pct": 7.3, "primary_to_secondary": 9.06, "ground_luminance": 0.101, "value_range_p5_p95": [0.079, 0.459], "accent_area_pct": 0.0, "visual_centroid": [0.626, 0.638]}
```
Accent share measured by colour match is **5.75%**. The dominance ratio (9) is lower than I4's (57) because the heart slab was cut, as the brief required: the rosette is now line engraving rather than a filled mass.

## Sources
- Draft `../build/draft_doc.json`.
- Garnishes from phg.recipe_versions (f06abb74, 14d45e57, 7095fd3d, 9fb77eaa), as cited in `../round-17/proposal.md`.
- Spirits from `public.beverage_categories` (gateway log 224 and 227).
- No library documents used.

## Open items
- ABV, grape and region, and brand are still waiting on Rob.
- The draft gives Brut Rosé 13 no pour label.
- "CANTINA" is still the placeholder venue word.
