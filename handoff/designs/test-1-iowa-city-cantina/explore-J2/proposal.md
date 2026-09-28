# TEST-1 explore-J2 "Horizon", round 2 (checkpoint: ../explore-J)

## Thesis
**Where the adobe cantina meets the Iowa skyline at dusk: one flat horizon, and one silhouette in which a stepped
Mexican parapet climbs into a grain elevator.**

Concept words: horizon · dusk · adobe · elevator · flat · still

Avoid-list: sun/moon discs, agave, cacti, drawn glasses or any multi-object scene; smooth gradients or glow; boxes,
cards, rules, leaders and price ornaments; tracked caps on labels longer than 3 words; taglines; a second display word;
accent colour below the horizon in any role other than the section heads.

Gesture (one): the dusk field, made of an indigo sky, an amber horizon glow and one flat plum silhouette that breaks the
horizon line and bleeds off the right edge. From left to right the silhouette is (a) three descending parapet steps whose lowest
step lands just right of the page axis above COCKTAILS (the pointer), (b) an adobe block with a stepped escalonado crown,
and (c) the same wall line rising into a grain-elevator headhouse and three domed silos cropped by the right trim.
Substitution test: the image is specific to a Mexican cantina in Iowa City, because it fuses the adobe parapet with the
Iowa grain elevator. A generic bar's menu could not reuse it.

Display word (one): CANTINA, reversed out of the indigo, flush left.

## Round-1 critique → fixes
| Coordinator fix | Done |
|---|---|
| 1 Prices lighter/muted, clearer gap | Fraunces 400 in muted ink `#5B5058` (6.6:1), 1 em after the name, same size as the name (13.9 pt), tabular lining figures. "Cognac VSOP" and "18" now differ in weight and colour. Longest name-to-price row: Brown Butter Old Fashioned, about 286 css px (35% of the page width, under the 40% limit); lower-tier rows ≤ 180 px (22%). |
| 2 Full descriptions | draft desc text in full; cocktails use the full component names plus the recipe_versions garnish (table below) |
| 3 Order | Margarita first; lower tier reads Spirits (Agave, Brandy) → Wine → Draft Beer + Cider; column heights 240 / 240 / 280 css px (was 182 / 245 / 289) |
| 4 Horizon as art | plum band dropped; one silhouette as described above |
| 5 Accent | amber darkened to `#8F4F10` (5.48:1 on paper) and used below the horizon ONLY for the 6 section heads |
| 6 Columns | lower tier flush-left on a 3-column grid with 40 px gutters and an 8 px baseline unit (all line-heights 16/24 px); Spirits and Wine share every baseline. The cocktail column stays centred: that single centred axis under the horizon is still the structural contrast to the two-column lists in G, H and I, and the parapet steps point at it. |

## Content (all from ../build/draft_doc.json; garnish from phg.recipe_versions as cited in ../round-17/proposal.md)
| Group | Item | Price | Printed description |
|---|---|---|---|
| Cocktails / Classics | Margarita | 15 | Tequila blanco · fresh lime juice · orange liqueur · agave syrup · lime wheel / Bright and citrus-forward (rv f06abb74) |
| Cocktails / Classics | Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry (aromatic bitters hidden; rv 9fb77eaa) |
| Cocktails / House Originals | House Daiquiri | 14 | White rum · fresh lime juice · demerara syrup · lime coin (rv 14d45e57) |
| Cocktails / House Originals | Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel (house_recipe=false: names only; rv 7095fd3d) |
| Spirits / Agave | Blanco Tequila | 12 | Blanco tequila pour |
| Spirits / Agave | Añejo Tequila | 16 | Añejo tequila pour |
| Spirits / Brandy | Cognac VSOP | 18 | VSOP Cognac pour |
| Wine / By the Glass | Malbec | 12 | Dry red wine |
| Wine / By the Glass | Pinot Grigio | 11 | Dry white wine |
| Wine / Sparkling | Brut Rosé | 13 | Dry sparkling rosé |
| Beer / Draft (head "Draft Beer") | Czech Pilsner | 7 | Crisp pale lager |
| Beer / Draft | Dry-Hopped IPA | 8 | Hop-forward draft IPA |
| Beer / Draft | Amber Lager | 7 | Toasty amber lager |
| Cider | Dry Cider | 8 | Dry sparkling cider |
There are no quantities anywhere. The Beer section's only sub, "Draft", is merged into the head "Draft Beer". Open gaps for the Coordinator: no
producer, region or ABV for the wine, beer and cider; no pour size or brand for the spirits.

## Layout geometry (letter 816 x 1056 css px = 2550 x 3300 px at 300 dpi; 1 css px = 0.75 pt)
- ART layer (inline SVG, text-free, one flat-ink grammar): indigo `#1E2147` y 0-224; amber `#D98A2E` y 224-300;
  horizon = y 300 (937 px). Silhouette plum `#5A2B4F` on the horizon from x 430 to the right edge. Pointer steps: 3 × (22 w, 14 h).
  Crown: 3 steps up and 3 down (12 w, 10 h). Headhouse: x 588-648, top y 34. Silos: x 648 → right edge + 12 bleed, top y 104.
  The rects extend 12 css px (≥ 3 mm) past the top, left and right trim for print bleed.
- Wordmark CANTINA: Fraunces 430, opsz 144, 92 px (69 pt), tracking 0.14em, paper, x 68, top y 74 (glyph right edge ≈ 520, 68 px
  clear of the headhouse). Sub-line: DM Sans 400, 12.5 px (9.4 pt), tracking 0.2em, mixed case, y 186.
- Reading area: x 72-744, y 372-1004 (0.75 in sides, 0.54 in bottom). Cocktails: centred column x 108-708, y 372-684.
  Lower tier: y 724-1004. Columns at x 72 / 309 / 547, each 197 wide with 40 gutters, top-aligned; heights 240 / 240 / 280.
- Type: section heads DM Sans 600, 12.5 px, tracked 0.3em caps, `#8F4F10`. Sub heads Fraunces italic 400, 15 px, `#5B5058`.
  Names Fraunces 500, 18.5 px (13.9 pt), `#221C22`. Prices Fraunces 400, 18.5 px, `#5B5058`, tabular, 1 em gap.
  Descriptions DM Sans 400, 13 px (9.75 pt), `#5B5058`. Line-heights 16/24 (8 px baseline unit).
- Phone (390 css → 1170 px): field 212 high (indigo 0-164, amber 164-212), silhouette scaled 0.62 from x 196; wordmark 44 px;
  cocktails centred, then Spirits, Wine, Draft Beer and Cider stacked flush left at 28 px margins.
- Per-element boxes: geometry.json. Per-run contrast and sizes: contrast.json.

## Device inventory and subtraction log
Revision hypothesis (round 2): J lost on distinctiveness, not on order. Putting all of the distinctiveness into ONE ownable
silhouette, and keeping the reading layer exactly as quiet as before, should raise the critic score without adding noise.
Then subtract anything decorative that the render does not need.

| # | Device (J2 before) | After | Evidence |
|---|---|---|---|
| 1 | Dusk field: indigo + amber flat bands | kept | the ground of the gesture |
| 2 | Silhouette: descending parapet steps (pointer) | kept | required to point into Cocktails; ties the field to the centred axis |
| 3 | Silhouette: stepped adobe crown | kept | ablation: without it the Mexico half disappears and the headhouse slides left, 30 px from the wordmark |
| 4 | Silhouette: headhouse cupola | **removed** | ablation: the elevator still reads (tall box + domed silos); the cupola was a second, fussier top note |
| 5 | Silhouette: domed silo tops | kept | the domes are what make it read as a grain elevator rather than an office block |
| 6 | Wordmark CANTINA | kept | the one display word |
| 7 | Tracked mixed-case sub-line | kept | venue and city |
| 8 | Dark-amber section heads | kept | the single accent role below the horizon |
| 9 | Italic sub heads | kept | carry the draft's Classics / House Originals / Agave / Brandy / By the Glass / Sparkling groups |
| 10 | Em-dash ornaments around the cocktail sub heads | **removed** | ornament; a second use of the accent colour |
| 11 | Hairline rule between the two tiers | **removed** | space already separates the tiers, and the rule read as a table edge |
| 12 | Middot ingredient separators | kept | the editorial ingredient format (brief G.d) |

Removed 3 of 12 devices (25%). Nothing regressed against the J checkpoint, so nothing was reverted. Contrast minimum is 5.48:1
(was 6.6:1 in J; the new floor is the dark-amber heads, above the 4.5:1 gate). Names and prices are unchanged at 13.9 pt,
and the items still end on the bottom margin (y 1004).

## visual_tests: before / after
Accent share **excluding the field** (crop below the horizon): **0.10% before → 0.10% after**. This is the dark-amber
section heads; J had 0.00% because its heads were indigo. The em-dashes were below the tool's detection size.
Whole page (the field is the colour): 27.16% → 27.16%. J checkpoint: 27.44%. Squint test: one dominant region, 28.55% of
the page (the field with the silhouette), with no secondary region. Visual centroid moved right from 0.497 to 0.510 because of the
silhouette's weight on the right.
Silhouette correlation with the J checkpoint is 0.979: the page structure is intentionally the same direction, and the change is inside the field.

```json
[
 {
  "file": "J2 after (preview-letter.png)",
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
  "file": "J2 before (before/preview-letter.png)",
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
  "file": "J checkpoint (../explore-J/preview-letter.png)",
  "squint_salient_regions": 1,
  "primary_area_pct": 28.57,
  "primary_to_secondary": null,
  "ground_luminance": 0.924,
  "value_range_p5_p95": [
   0.138,
   0.932
  ],
  "accent_area_pct": 27.44,
  "visual_centroid": [
   0.497,
   0.17
  ]
 },
 {
  "file": "J2 after, below-horizon crop",
  "squint_salient_regions": 0,
  "primary_area_pct": 0.0,
  "primary_to_secondary": null,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.769,
   0.932
  ],
  "accent_area_pct": 0.1,
  "visual_centroid": [
   0.476,
   0.57
  ]
 },
 {
  "file": "J2 before, below-horizon crop",
  "squint_salient_regions": 0,
  "primary_area_pct": 0.0,
  "primary_to_secondary": null,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.768,
   0.932
  ],
  "accent_area_pct": 0.1,
  "visual_centroid": [
   0.477,
   0.569
  ]
 }
]
```

## Contrast and legibility (contrast.json, worst pixel behind each text run)
Letter:
- Section heads: 5.48:1.
- Sub heads, descriptions and prices: 6.6:1.
- Names: 14.4:1.
- Sub-line: 11.9:1. Wordmark: 13.2:1.

Phone: same ratios. The Margarita and Old Fashioned descriptions wrap to two centred lines. The phone sub-line is 7.9 pt.

## References
Rob's quality bar: references/rob-2026-09-28/ref-03-ffe03c52.png (panels 2 and 5: flat posterised dusk fields and a stepped
silhouette as the only art, with a quiet list below) and ref-02-3acf255d.png (panel 2: flat sun + stair gesture, tracked serif
CANTINA, section heads as the only accent). No new menu_visual_documents queries were made this round. The Coordinator
should attach the library comparables (round-17 set) when filing.

## Files
build.py (`python3 build.py [before|after]`; ablation env J2_CROWN / J2_CUPOLA), menu.html, preview-letter.png (2550x3300),
preview-phone.png (1170 wide), before/ (pre-subtraction renders and contrast), visual_tests.json, contrast.json, geometry.json.
