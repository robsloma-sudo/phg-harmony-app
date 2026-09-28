# TEST-1 explore-J3 "Horizon", round 3 (checkpoints: ../explore-J2, ../explore-J)

## Thesis
**At dusk on the Iowa prairie, a grain elevator stands against a stepped Mexican glow, and the menu is set in its shadow.**

Concept words: horizon · dusk · elevator · escalonado · screen-print · flat · still

Avoid-list: sun/moon discs, agave, cacti, glasses or any drawn scene; gradients or glow blur; boxes, cards, rules, leaders,
price ornaments; tracked caps longer than 3 words; taglines; a second display word; centred-plus-flush-left mixed
alignment; texture or colour behind reading text.

The one gesture: a flat screen-printed dusk. The indigo sky is cut on the right by an amber glow that rises in
escalonado steps (the Mexican stepped parapet, abstracted into the light itself). In front of the glow stands a plum Iowa
grain elevator: a gabled headhouse, a windowed gallery and a three-bin cluster. The elevator stands on the page bottom and
runs up the right trim beside the menu columns, crosses the horizon, and bleeds off the top, right and bottom.
Substitution test: the image fuses the Mexican stepped form with the Iowa elevator, so it names this cantina in
Iowa City. It cannot be dropped onto another bar's menu.

The one display word: CANTINA, flush left on the text edge.

## Round-2 critique → J3 fixes
| # | Fix | Done |
|---|---|---|
| 1 | Legible silhouette | Plum `#5A2B4F` now stands against amber (4.0:1) and paper (9.4:1), never against indigo alone: the stepped glow wraps up behind the whole tower. The elevator is redrawn with a gabled headhouse, a gallery with 6 window cut-outs and 3 bins with 7 px seams. The pointer steps are removed. |
| 2 | Art enters the reading area | The elevator runs from the page bottom up the right trim (x 648 → bleed) beside Cocktails and the three columns. The text frame ends at x 620, a 28 css px (7.4 mm) safe inset. The horizon is no longer a single hard seam: the tower crosses it. |
| 3 | One alignment system | Everything is flush left on one grid edge at x 60: the wordmark ink edge (59.5), the sub-line (60.5), every head, name and description. The centred cocktail column is gone. |
| 4 | Measured failures | Margins: left 60, top 60 (wordmark ink top 59.5), bottom 60 (last line box 996, identical in all three columns). All within 0.5 css px (0.13 mm). The right side is the art bleed, with the 28 px safe inset. Wordmark and sub-line sit on the text edge. All three columns end at y 996. |
| 5 | Materiality | Two-pass screen-print misregistration: an indigo underprint of the elevator offset 3 px down-right, showing as a thin indigo edge at the bin seams, gallery windows and gable. It is confined to the art; no reading text touches it. (Paper tooth was tried and removed in the subtraction pass.) |
| 6 | Reading layer | Lower tier: Spirits → Draft Beer + Cider → Wine. Agave leads because the brief's section-5 order puts Spirits/Agave before Wine and agave is the cantina's category; beer and cider are grouped and moved ahead of wine. Multi-word ingredients use non-breaking spaces (lines break only after the middots). The Margarita reads "… lime wheel. Bright and citrus-forward", joined into one run, with the sentence kept together. Prices are plum Fraunces 400 (9.5:1), distinct from both the ink names and the muted DM Sans descriptions. Description content is unchanged from J2. |

Row alignment in the lower tier: the Brandy / Cider / Sparkling groups share one row. Cognac VSOP, Dry Cider and Brut Rosé
sit on the same baseline, and every line-height is a multiple of 8 px (16/24).

## Content (unchanged from J2; all from ../build/draft_doc.json + garnish from phg.recipe_versions, cited in ../round-17/proposal.md)
| Group | Item | Price | Description |
|---|---|---|---|
| Cocktails / Classics | Margarita | 15 | Tequila blanco · fresh lime juice · orange liqueur · agave syrup · lime wheel. Bright and citrus-forward |
| Cocktails / Classics | Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry (bitters hidden) |
| Cocktails / House Originals | House Daiquiri | 14 | White rum · fresh lime juice · demerara syrup · lime coin |
| Cocktails / House Originals | Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel (names only) |
| Spirits / Agave | Blanco Tequila | 12 | Blanco tequila pour |
| Spirits / Agave | Añejo Tequila | 16 | Añejo tequila pour |
| Spirits / Brandy | Cognac VSOP | 18 | VSOP Cognac pour |
| Beer / Draft ("Draft Beer") | Czech Pilsner | 7 | Crisp pale lager |
| Beer / Draft | Dry-Hopped IPA | 8 | Hop-forward draft IPA |
| Beer / Draft | Amber Lager | 7 | Toasty amber lager |
| Cider | Dry Cider | 8 | Dry sparkling cider |
| Wine / By the Glass | Malbec | 12 | Dry red wine |
| Wine / By the Glass | Pinot Grigio | 11 | Dry white wine |
| Wine / Sparkling | Brut Rosé | 13 | Dry sparkling rosé |
Still waiting on Rob: producer, region and ABV for wine, beer and cider; brand and pour size for spirits.

## Layout geometry (letter 816 x 1056 css px = 2550 x 3300 px at 300 dpi; 1 css px = 0.75 pt = 0.265 mm)
- **Text frame:** x 60-620, y 60-996. The top, left and bottom margins are all 60 css px (15.9 mm). The right side of the page is art, with the text 28 px clear of the elevator.
- **ART layer:** inline SVG, text-free. All shapes bleed 12 css px (3.2 mm) past trim.
  - Sky: indigo `#1E2147`, y 0-238. The horizon is y 238.
  - Stepped glow: amber `#D98A2E`, 7 steps of 20 px run, rising from (552, 238) to bleed off the top, filling to the right edge.
  - Elevator, plum `#5A2B4F`:
    - Headhouse: x 648-706, top y 58, with a gable apex at y 28.
    - Gallery: y 128-150, from x 706 to the bleed, with 8 x 8 window cut-outs every 18 px.
    - Bins: 3 bins from y 150 to the bottom bleed, each about 40 px wide with 7 px seams.
  - Underprint: indigo copy of the elevator offset (+3, +3).
- **Wordmark:** CANTINA in Fraunces 430, opsz 144, 90 px (67.5 pt), tracking 0.14em, paper colour. Ink box 59.5-500.5 x 59.5-125.4.
- **Sub-line:** DM Sans 12.5 px (9.4 pt), tracking 0.2em, mixed case. Ink starts at x 60.5, y 158.
- **Cocktails:** x 60-620, y 290-626, single flush-left column, description measure up to 560.
- **Lower tier:** y 708-996. Three columns at x 60 / 253 / 447, each 173 wide with 20 px gutters. All three are 288 tall and end at 996.
- **Type:**
  - Section heads: DM Sans 600, 12.5 px (9.4 pt), tracking 0.3em, caps, dark amber `#8F4F10` (5.48:1). This is the only accent role below the horizon.
  - Sub heads: Fraunces italic 15 px (11.25 pt), muted `#5B5058`.
  - Names: Fraunces 500, 17.5 px (13.1 pt), ink `#221C22`.
  - Prices: Fraunces 400, 17.5 px, plum, tabular figures, 0.7 em after the name, joined to the name by a non-breaking space.
  - Descriptions: DM Sans 13 px (9.75 pt), muted.
- **Phone (390 css → 1170 x 4734 px):** sky 0-190. The elevator strip runs down the right trim from x 340. Text frame is x 24-324, flush left. Order: Cocktails, Spirits, Draft Beer, Cider, Wine.
- Per-element boxes and measured ink boxes: geometry.json. Per-run contrast: contrast.json.

## Device inventory and subtraction log
Revision hypothesis: the critic's "banner on a list" came from the art stopping at the horizon, the silhouette sharing
its value with the sky, and two alignment systems. Fix these structurally, with the art entering the reading area, a
value split (plum on amber and paper) and one flush-left edge. Then subtract surface devices until only the ones that
make the elevator and the fusion read remain.

| # | Device (J3 before) | After | Evidence |
|---|---|---|---|
| 1 | Indigo sky | kept | ground for the wordmark |
| 2 | Thin full-width amber horizon band | **removed** | it re-created the "stripe banner" seam. Without it the horizon is the indigo/paper edge and the glow reads as one stepped shape |
| 3 | Escalonado stepped glow | kept | the Mexican half of the fusion, and the value backing that makes the tower legible |
| 4 | Gabled headhouse | kept | the primary grain-elevator cue |
| 5 | Headhouse gable window | **removed** | 8 px detail, noise at reading distance |
| 6 | Gallery with window cut-outs | kept | ablation: without the windows the gallery reads as a plain bar |
| 7 | Bin cluster with seams | kept | ablation: this is what turns a tower into an elevator |
| 8 | Loading spout (diagonal) | **removed** | ablation: the elevator still reads without it, and it added a second diagonal direction to a flat, orthogonal image |
| 9 | Indigo misregistration underprint | kept | the materiality the concept justifies (two-pass screen print of dusk inks); ablation looked flat and digital |
| 10 | Paper tooth on the art | **removed** | at legible strength it read as noise on the plum; the misregistration carries the materiality alone |
| 11 | Wordmark | kept | the one display word |
| 12 | Sub-line | kept | venue and city |
| 13 | Dark-amber section heads | kept | the single accent role below the horizon |
| 14 | Italic sub heads | kept | the draft's groups |
| 15 | Plum prices | kept | required: prices distinguished from descriptions by ink |
| 16 | Middot ingredient separators | kept | editorial ingredient format |

Removed 4 of 16 (25%). Nothing regressed against J2 on gates (contrast minimum still 5.48:1, all columns and margins
measured above), so nothing was reverted. Kept from the J2 checkpoint: the content set and the dark-amber heads.

## visual_tests: before / after
- **Accent share outside the art** (reading area crop, below the horizon and left of the elevator): **0.17% before → 0.17% after**. This is the dark-amber heads and the plum prices.
- **Whole-page accent** (the art is the colour field): 35.34% → 35.53%. J2 was 27.16%.
- **Squint test:** one dominant region, 38.69% → 38.93% of the page (the sky, glow and elevator as a single L-shaped mass). There is no competing region. The reading-area crop has only tiny salient specks (0.04%), which are the heads.
- **Visual centroid:** (0.611, 0.341) → (0.612, 0.342). J2 was (0.510, 0.174). The weight moved down and right, into the page.
- **Silhouette correlation:** J3 after vs J2 is 0.668, a structural change (J2 vs J was 0.979). Before vs after is 0.998.

```json
[
 {
  "file": "J3 after (preview-letter.png)",
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
  "file": "J3 before (before/preview-letter.png)",
  "squint_salient_regions": 1,
  "primary_area_pct": 38.69,
  "primary_to_secondary": null,
  "ground_luminance": 0.877,
  "value_range_p5_p95": [
   0.138,
   0.932
  ],
  "accent_area_pct": 35.34,
  "visual_centroid": [
   0.611,
   0.341
  ]
 },
 {
  "file": "J2 checkpoint",
  "squint_salient_regions": 1,
  "primary_area_pct": 28.55,
  "primary_to_secondary": null,
  "ground_luminance": 0.916,
  "value_range_p5_p95": [
   0.138,
   0.932
  ],
  "accent_area_pct": 27.16,
  "visual_centroid": [
   0.51,
   0.174
  ]
 },
 {
  "file": "J3 after: reading area crop (below horizon, x<636 css)",
  "squint_salient_regions": 5,
  "primary_area_pct": 0.04,
  "primary_to_secondary": 1.47,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.757,
   0.932
  ],
  "accent_area_pct": 0.17,
  "visual_centroid": [
   0.396,
   0.562
  ]
 },
 {
  "file": "J3 before: reading area crop",
  "squint_salient_regions": 5,
  "primary_area_pct": 0.04,
  "primary_to_secondary": 1.47,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.757,
   0.932
  ],
  "accent_area_pct": 0.17,
  "visual_centroid": [
   0.396,
   0.561
  ]
 }
]
```

## Contrast and legibility (contrast.json, worst pixel behind each run)
Letter:
- Section heads: 5.48:1.
- Sub heads and descriptions: 6.6:1.
- Prices: 9.53:1.
- Names: 14.4:1.
- Sub-line: 11.9:1. Wordmark: 13.2:1.

Minimum sizes: names and prices 13.1 pt, descriptions 9.75 pt. Phone: same ratios, names 12.75 pt.

## References
- ref-02-3acf255d.png: panel 1 (the art runs down the side of the list and the text sits in the safe inset), panel 2 (flat sun and stair: the stepped form as the only art) and panel 5 (the art rail interlocks with the columns).
- ref-03-ffe03c52.png: panels 2 and 5 (posterised dusk, flat cut shapes).

No new menu_visual_documents queries were made this round. The Coordinator should attach the round-17 comparables.

## Files
- build.py: run `python3 build.py [before|after]`. Ablation env: `J3_ABL=spout,gallery_windows,offset,...`.
- menu.html
- preview-letter.png (2550x3300)
- preview-phone.png (1170x4734)
- before/ (renders from before the subtraction pass)
- visual_tests.json
- contrast.json
- geometry.json
