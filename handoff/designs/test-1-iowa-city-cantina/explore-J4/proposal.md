# TEST-1 explore-J4 "Horizon", round 4 (checkpoint: ../explore-J3)

## Thesis
**A navy prairie dusk, with the last light cut in Mexican escalonado steps. One Iowa grain elevator stands in that light
and comes down to the ground line the menu is set on.**

Concept words: horizon · dusk · elevator · escalonado · ground line · flat

Avoid-list: sun/moon, agave, cacti, glasses; gradients; colonnade/seam rhythm or window dots on the building; church or barn
gables; boxes, cards, rules, leaders, price ornaments; tracked caps over 3 words; taglines; a second display word;
any ink beyond navy, amber and paper (dark amber is the same amber, darkened for text).

The one gesture, in three flat inks:
- **Sky:** navy.
- **Glow:** amber, whose left edge descends in six escalonado steps from the top of the page to the horizon (y 204).
- **Elevator:** one navy grain-elevator silhouette. A tall headhouse whose roofline steps up once for the leg housing.
  From its left end runs a wide slip-form bin block, whose top is the row of three bin crowns. The elevator rises out
  of the glow, crosses the horizon and comes down beside Cocktails to the ground line G (y 634). The lower tier hangs
  from G.

Substitution test: Mexico is in the stepped light, and Iowa City is in the grain elevator standing in it. The same
stepped form also shapes the elevator's own roofline, so the fusion is in the form rather than in a caption.

## Round-3 critique → J4 fixes
| # | Fix | Done |
|---|---|---|
| 1 | One unmistakable elevator | Redrawn as a single profile. The headhouse is 74 x 570 css px, with a 44 x 30 leg-housing step on its roofline, and rises 236 px above the bin block. The bin block is 186 px wide to the right trim, plus bleed, and 334 px tall, with 3 bin crowns (the only curves; no seams, no window dots). Ablation showed the crowns are what make it read: without them it is an L-shaped slab. Phone: the same profile at 0.5 scale reads as a building, 36 + 84 px wide. |
| 2 | Underprint removed | Gone. |
| 3 | Word and image integrated | The horizon (y 204) is the top structural edge: Cocktails hangs one rhythm unit (32 px) below it at x 60, and the glow's lowest step lands on the same line. The elevator's base, the ground line G = 634, is the second edge. The last cocktail line ends 24 px above G (y 610) and the lower-tier H2s start 24 px below it (y 658). Both edges run the full width. |
| 4 | Dead band removed | Cocktails sits on columns 1-2 (x 60-516) of the same three-column grid. Column 3 beside it is the elevator. The Cocktails → lower-tier gap is 48 px, split 24/24 around G, which equals the grid's 24 px unit and matches the sub-group rhythm (26 px). |
| 5 | Lower-tier rows | Beer & Cider carries the H3s Draft and Cider (Cider demoted from H2). Agave, Draft and By the Glass share y 694, and the first items share y 726. Brandy and Sparkling sit directly under their parents (y 858, no auto margins). Column bottoms are 934 / 996 / 934, the natural lengths (Beer & Cider has one more item). |
| 6 | Prices by value | Prices are Fraunces 400 in muted `#5B5058` (6.6:1); names are Fraunces 500 in ink `#221C22` (14.4:1). They differ in weight and value, a 0.75 em gap apart. |
| 7 | Palette | Navy `#1E2147`, amber `#D98A2E` (with its text-safe dark form `#8F4F10` for the six heads, 5.48:1), paper, plus ink and muted for text. Plum is gone. |
| 8 | Content | Unchanged from J3. The Margarita keeps "… lime wheel. Bright and citrus-forward" inline, with the sentence kept together, and appears the same way on letter and phone. |

Heading note: the brief suggested "Draft Beer" (H2) with H3 "Draft", which would read "Draft Beer / Draft". I set the
H2 as **"Beer & Cider"** (3 words, tracked caps allowed) with the draft's own sub heads "Draft" and "Cider". Every
item stays in its draft group, and the column name is honest about holding the cider. If the Coordinator prefers the
literal wording, it is a one-word change in `beer_cider_html()`.

## Content (unchanged; ../build/draft_doc.json + garnish from phg.recipe_versions, cited in ../round-17/proposal.md)
| Group | Item | Price | Description |
|---|---|---|---|
| Cocktails / Classics | Margarita | 15 | Tequila blanco · fresh lime juice · orange liqueur · agave syrup · lime wheel. Bright and citrus-forward |
| Cocktails / Classics | Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry |
| Cocktails / House Originals | House Daiquiri | 14 | White rum · fresh lime juice · demerara syrup · lime coin |
| Cocktails / House Originals | Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel |
| Spirits / Agave | Blanco Tequila | 12 | Blanco tequila pour |
| Spirits / Agave | Añejo Tequila | 16 | Añejo tequila pour |
| Spirits / Brandy | Cognac VSOP | 18 | VSOP Cognac pour |
| Beer & Cider / Draft | Czech Pilsner | 7 | Crisp pale lager |
| Beer & Cider / Draft | Dry-Hopped IPA | 8 | Hop-forward draft IPA |
| Beer & Cider / Draft | Amber Lager | 7 | Toasty amber lager |
| Beer & Cider / Cider | Dry Cider | 8 | Dry sparkling cider |
| Wine / By the Glass | Malbec | 12 | Dry red wine |
| Wine / By the Glass | Pinot Grigio | 11 | Dry white wine |
| Wine / Sparkling | Brut Rosé | 13 | Dry sparkling rosé |
Still waiting on Rob: producer, region and ABV for wine, beer and cider; brand and pour size for spirits.

## Layout geometry (letter 816 x 1056 css px = 2550 x 3300 px at 300 dpi; 1 css px = 0.265 mm)
- **Grid:** margins 60 on the left, top and bottom. Wordmark ink top is 60.2, the Beer & Cider column ends at 996, and names/heads start at x 60. The frame is x 60-756 with three 216-px columns at x 60 / 300 / 540 and 24-px gutters. Measured margins agree within 0.5 px (0.13 mm).
- **ART (inline SVG, text-free, bleeds 12 px past the top, left and right trim):**
  - Navy sky: y 0-204.
  - Amber glow: left edge in 6 steps, from x 520 at the top to x 440 at the horizon (16-px run per step).
  - Elevator (navy): headhouse x 556-630, roof y 64, leg step x 556-600 to y 34. Bin block x 630 → bleed, bin crowns at y 300 (3 arcs, 16 deep). Base G = 634.
- **Wordmark:** CANTINA in Fraunces 430, 76 px (57 pt), tracking 0.14em, paper colour. Ink box 59.2-431.7 x 60.2-116.2.
- **Sub-line:** DM Sans 12.5 px (9.4 pt), tracking 0.2em. Ink starts at x 60.5, y 148.8.
- **Cocktails:** x 60-516, y 236-610. Column 3 alongside it holds the elevator, with 40 px between the text measure and the headhouse.
- **Lower tier:** y 658 onward. H2s at 658, H3s at 694, first items at 726, Brandy and Sparkling at 858, Cider at 920. Bottoms 934 / 996 / 934.
- **Type:**
  - Section heads: DM Sans 600, 12.5 px, tracking 0.3em, caps, `#8F4F10`.
  - Sub heads: Fraunces italic 15.5 px (11.6 pt), muted.
  - Names: Fraunces 500, 18.5 px (13.9 pt), ink.
  - Prices: Fraunces 400, 18.5 px, muted, tabular figures.
  - Descriptions: DM Sans 13.5 px (10.1 pt), muted.
  - Line heights 16 / 18 / 26.
- **Phone (390 css → 1170 x 5220 px):**
  - Field 0-250, with the same glow and elevator at about 0.5 scale on the right (headhouse x 284-320, bins 320 → bleed).
  - Text frame x 24-366, stacked in the order Cocktails, Spirits, Beer & Cider, Wine.
- Per-element boxes and measured ink boxes: geometry.json. Per-run contrast: contrast.json.

## Device inventory and subtraction log
Revision hypothesis: J3 lost points because its elevator did not read as an elevator (a colonnade), not because it
had too few devices. Rebuild the art as one legible profile with fewer parts, tie it to the type by two full-width edges
(horizon and ground line), and subtract everything that was only ornament.

| # | Device (J4 before) | After | Evidence |
|---|---|---|---|
| 1 | Navy sky | kept | ground for the wordmark |
| 2 | Escalonado amber glow | kept | the Mexican half, and the value backing for the elevator's roofline |
| 3 | Thin full-width amber horizon band | **removed** | it restored the "banner" seam; the glow's lowest step already marks the horizon |
| 4 | Headhouse | kept | primary elevator cue |
| 5 | Headhouse leg-housing step | kept | ablation: without it the headhouse reads as a chimney or tower |
| 6 | Bin crowns on the bin block | kept | ablation: without them the building reads as an abstract L-slab |
| 7 | Navy ground rule under Cocktails (continuing G to x 60) | **removed** | it read as a table rule; the elevator base and the H2 row already carry the line |
| 8 | Wordmark | kept | the one display word |
| 9 | Sub-line | kept | venue and city |
| 10 | Dark-amber section heads | kept | the single accent role in text |
| 11 | Italic sub heads | kept | the draft's groups |
| 12 | Middot ingredient separators | kept | editorial format |

Removed 2 of 12 (17%), below the 25% target. The two further candidates, the leg step and the bin crowns, were ablated
and rendered. Both made the image worse, so they are kept: this is the "keep only those whose removal hurts" rule, and
the gap is recorded rather than filled with a cosmetic cut. Retired since J3: the plum ink, the misregistration
underprint, the gallery windows and the bin seams. Relative to J3's device set, 4 of 16 are gone.

## visual_tests: before / after
- **Accent share outside the art** (reading-area crop): **0.14% before → 0.14% after**. This is the dark-amber heads only; prices are no longer an accent. J3 was 0.17%.
- **Whole page** (the art is the colour field): 29.49% → 29.49%. J3 was 35.53%.
- **Squint test:** one dominant region, 30.98% → 31.32% of the page (the sky, glow and elevator as one mass), with no competing region.
- **Visual centroid:** (0.585, 0.277) → (0.582, 0.274).
- **Silhouette correlation:** J4 vs J3 is 0.638, a structural change. Before vs after is 0.999.
- The reading-area crop reports 24 small salient specks at 0.15% (the text lines at crop scale). There is no large competing region.

```json
[
 {
  "file": "J4 after (preview-letter.png)",
  "squint_salient_regions": 1,
  "primary_area_pct": 31.32,
  "primary_to_secondary": null,
  "ground_luminance": 0.901,
  "value_range_p5_p95": [
   0.138,
   0.932
  ],
  "accent_area_pct": 29.49,
  "visual_centroid": [
   0.582,
   0.274
  ]
 },
 {
  "file": "J4 before (before/preview-letter.png)",
  "squint_salient_regions": 1,
  "primary_area_pct": 30.98,
  "primary_to_secondary": null,
  "ground_luminance": 0.897,
  "value_range_p5_p95": [
   0.138,
   0.932
  ],
  "accent_area_pct": 29.49,
  "visual_centroid": [
   0.585,
   0.277
  ]
 },
 {
  "file": "J3 checkpoint",
  "squint_salient_regions": 1,
  "primary_area_pct": 38.93,
  "primary_to_secondary": null,
  "ground_luminance": 0.876,
  "value_range_p5_p95": [
   0.138,
   0.932
  ],
  "accent_area_pct": 35.53,
  "visual_centroid": [
   0.612,
   0.342
  ]
 },
 {
  "file": "J4 after: reading-area crop (below horizon, x<540 css)",
  "squint_salient_regions": 24,
  "primary_area_pct": 0.15,
  "primary_to_secondary": 1.13,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.761,
   0.932
  ],
  "accent_area_pct": 0.14,
  "visual_centroid": [
   0.402,
   0.506
  ]
 },
 {
  "file": "J4 before: reading-area crop",
  "squint_salient_regions": 24,
  "primary_area_pct": 0.15,
  "primary_to_secondary": 1.13,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.737,
   0.932
  ],
  "accent_area_pct": 0.14,
  "visual_centroid": [
   0.41,
   0.506
  ]
 }
]
```

## Contrast and legibility (contrast.json, worst pixel)
Letter:
- Section heads: 5.48:1.
- Sub heads, descriptions and prices: 6.6:1.
- Names: 14.4:1.
- Sub-line: 11.9:1. Wordmark: 13.2:1.

Sizes: names and prices 13.9 pt, descriptions 10.1 pt. Phone: same ratios; names 13.1 pt; sub-line 7.9 pt.

## References
- ref-02-3acf255d.png: panel 2 (flat stepped form plus a single object as the only art) and panels 1 and 5 (art occupying a side column beside the list, text in the safe inset).
- ref-03-ffe03c52.png: panels 2 and 5 (posterised dusk, cut shapes, no line work).

No new menu_visual_documents queries were made this round. The Coordinator should attach the round-17 comparables.

## Files
- build.py: run `python3 build.py [before|after]`. `J4_ABL=setback,bin_arcs,...` renders ablations.
- menu.html
- preview-letter.png (2550x3300)
- preview-phone.png (1170x5220)
- before/
- visual_tests.json
- contrast.json
- geometry.json
