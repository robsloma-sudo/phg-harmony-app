# TEST-1 explore-J6 "Horizon", round 6 (checkpoint J4; art pipeline from J5)

## Thesis
**One cut-paper grain elevator at an Iowa dusk, pierced like papel picado, with CANTINA standing on its gallery.**

Concept words: dusk · grain elevator · papel picado · cut paper · gallery line · flat print

Avoid-list: separate motifs side by side (elevator + banner); stepped stairs; smokestacks, boots, colonnades, goblet
seams; digital noise or mottling; gradients; boxes, cards, rules, leaders, price ornaments; tracked caps over 3 words;
taglines; a free-floating wordmark; texture behind reading text.

**The one gesture.** A flat two-ink print: navy and amber on paper.
- **Navy:** the dusk field, running across the top and down the right column to the ground line.
- **Elevator:** ONE grain elevator cut out of it, in unprinted paper.
  - A headhouse, with a narrow leg housing offset to the right edge of its roof.
  - A gallery beam at CANTINA's baseline that runs from the left trim, through the headhouse, and across the bins.
  - A row of cylindrical bins cropped by the right trim.
- **Papel picado punched into the elevator:**
  - The bins' conical caps are the picos, the zig-zag hem of a papel picado banner.
  - A line of rombos (the banner's pierced diamonds) is cut through the bin walls.
  - The amber dusk shows through the cuts. Amber appears only there and as a 4 px ground line at the elevator's base; the separate amber band is gone.

The motif source (papel picado border grammar: picos hem plus pierced rombos, as cut in San Salvador Huixcolotla,
Puebla) is unchanged from J5. What is new is that it is punched into the Iowa object instead of placed beside it.
That fusion is the substitution test: the image is specific to a Mexican cantina in Iowa City.

**Word and image.** CANTINA stands on the gallery beam: the beam top is the wordmark's baseline (y 116.2), so the letters
sit on the elevator's conveyor like a rooftop sign. The sub-line hangs below the beam.

## Round-5 critique → J6 fixes
| # | Fix | Done |
|---|---|---|
| 1 | Fuse the motifs | The picos are the bin caps and the rombos are cut through the bin walls, with amber seen through the cuts. The band is reduced to a 4 px amber ground line under the elevator (column 3 only). |
| 2 | Bins read as cylinders | Each bin has a half-round tone in a second paper value (`#E2D6C2`) on its right 38%, and a conical cap against navy. The navy seams are gone. The leg housing is 16 px wide, 40 px tall, and offset to the right edge of the 62-px headhouse, so it reads as the elevator leg, not a chimney. |
| 3 | Clean flat navy | No mottling or pinholes anywhere. The only print artefact is the amber pass misregistered by 3 px right and 2 px down (0.25 mm) at 300 dpi: amber slivers inside the rombos, and a dark trap where the navy column meets the ground line. |
| 4 | One grid | Column lines are x 60 / 264 / 468. The third line, x = 468, is the navy column edge. Beer & Cider hangs from the elevator's ground line in column 3 at x 468. Cocktails, Spirits and Wine use columns 1-2. The wordmark, sub-line and every heading start on x 60. |
| 5 | No dead space | The lower tier is reflowed so every column ends on the bottom margin: Spirits, Wine and Beer & Cider all end at y 996. Beer & Cider, the longest column, starts 58 px higher, directly under the elevator's ground line (G = 648), and Spirits and Wine start at 732. That puts Brandy, Sparkling and Cider on one shared row (y 920) and the last items on one shared baseline. The extra height goes into the Cocktails rhythm (item and group gaps +8 px). |
| 6 | Wordmark interacts | CANTINA stands on the gallery beam, which continues into the headhouse. |
| 7 | Spirits wording | Reverted to the draft text: "Blanco tequila pour", "Añejo tequila pour", "VSOP Cognac pour". The beverage_categories citations are removed. |
| 8 | Daiquiri and wraps | "White rum · fresh lime juice / · house demerara syrup · lime coin" restores the draft's "house demerara syrup". At every description wrap the separator is kept and carried to the start of the continuation line, so no separator is lost and no line ends with one. The geometry check `lines_ending_with_middot` is empty, and `continuation_lines` lists the 3 wrapped lines. The Margarita's tasting note, "Bright and citrus-forward.", stays on its own italic line. It is **draft-supplied** (second sentence of the draft desc), and only drafts that supply a note get one. |
| 9 | Content | Otherwise unchanged. |

Order: agave-forward on purpose. The Margarita leads Cocktails, and Spirits with Agave first is the first lower column.
Beer & Cider sits in column 3 under the elevator because it is the longest list, and the art's ground line is its head.

## Content
| Group | Item | Price | Printed (letter line breaks) | Source |
|---|---|---|---|---|
| Cocktails / Classics | Margarita | 15 | Tequila blanco · fresh lime juice / · orange liqueur · agave syrup · lime wheel / *Bright and citrus-forward.* | components + rv f06abb74 garnish + draft desc (note) |
| Cocktails / Classics | Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry | components (bitters hidden) + rv 9fb77eaa |
| Cocktails / House Originals | House Daiquiri | 14 | White rum · fresh lime juice / · house demerara syrup · lime coin | draft desc + component + rv 14d45e57 |
| Cocktails / House Originals | Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon / · demerara syrup · aromatic bitters · orange peel | components (names only) + rv 7095fd3d |
| Spirits / Agave | Blanco Tequila | 12 | Blanco tequila pour | draft desc |
| Spirits / Agave | Añejo Tequila | 16 | Añejo tequila pour | draft desc |
| Spirits / Brandy | Cognac VSOP | 18 | VSOP Cognac pour | draft desc |
| Wine / By the Glass | Malbec | 12 | Dry red wine | draft desc |
| Wine / By the Glass | Pinot Grigio | 11 | Dry white wine | draft desc |
| Wine / Sparkling | Brut Rosé | 13 | Dry sparkling rosé | draft desc |
| Beer & Cider / Draft | Czech Pilsner | 7 | Crisp pale lager | draft desc |
| Beer & Cider / Draft | Dry-Hopped IPA | 8 | Hop-forward draft IPA | draft desc |
| Beer & Cider / Draft | Amber Lager | 7 | Toasty amber lager | draft desc |
| Beer & Cider / Cider | Dry Cider | 8 | Dry sparkling cider | draft desc |
Still waiting on Rob: producer, region and ABV for wine, beer and cider; brand and pour size for spirits.

## Layout geometry (letter 816 x 1056 css px = 2550 x 3300 px at 300 dpi; 1 css px = 0.265 mm)
- **Margins:** left 60 (all text), top 60 (wordmark ink top 60.2), bottom 60 (every column ends at 996). The right side is the art column; the Beer & Cider text runs from 468 to at most 648.
- **Grid:** column lines at x 60 / 264 / 468. Widths are 180 / 180 / 288, with 24-px gutters. Cocktails spans columns 1-2 (x 60-444, measure 384).
- **ART (raster art-letter.png, text-free, bleeds 12 css px):**
  - Navy top band: y 0-186.
  - Navy column: x 468 → bleed, y 0 → G = 648.
  - Headhouse: x 538-600, top 58. Leg housing: x 578-594, top 18.
  - Gallery beam: y 116.2-128.2, from the left bleed to the right bleed, passing through the headhouse.
  - Bins: x 600 → bleed, 76 wide; cone apex y 128, shoulders y 152. Half-round tone on the right 38% of each bin.
  - Rombos: one row at 22% of the bin height, 9 px half-height.
  - Ground line: amber, y 644-648, x 468 → bleed.
- **Wordmark:** CANTINA in Fraunces 430, 76 px (57 pt), tracking 0.14em, paper colour, baseline on the beam. Sub-line: DM Sans 12.5 px, ink y 148.8-160.3.
- **Vertical positions:**
  - Cocktails: y 218-662.
  - Spirits and Wine: y 732-996. Beer & Cider: y 674-996.
  - H3 rows: Agave, By the Glass 764; Draft 706; Brandy, Sparkling, Cider 920.
- **Type:**
  - Section heads: DM Sans 600, 12.5 px, tracking 0.3em, caps, `#8F4F10` (5.48:1).
  - Sub heads: Fraunces italic 15.5 px, muted.
  - Names: Fraunces 500, 18.5 px (13.9 pt), ink.
  - Prices: Fraunces 400, 18.5 px, muted `#5B5058`, tabular figures.
  - Descriptions: DM Sans 13.5 px (10.1 pt), muted.
  - Tasting note: Fraunces italic 13.5 px.
- **Palette:** navy `#1E2147`, amber `#D98A2E` (text form `#8F4F10`), paper `#F4EDE1`, second paper value `#E2D6C2` (art only), ink `#221C22`, muted `#5B5058`.
- **Phone (390 css → 1170 x 5196 px):**
  - Navy field 0-236; the elevator is 0.6 scale on the right (headhouse x 262-302), with CANTINA standing on the beam.
  - The text frame is x 24-366, stacked in the order Cocktails, Spirits, Wine, Beer & Cider.
- geometry.json has every element, measured ink boxes, block tops and bottoms, and the middot checks. contrast.json has per-run contrast.

## Device inventory and subtraction log
Revision hypothesis: J5 lost on "two motifs side by side", noise, and a loose grid. Fuse the motifs into one object, go
flat, put everything on one grid, then cut whatever makes the cut-paper elevator busier than it needs to be to read.

| # | Device (J6 before) | After | Evidence |
|---|---|---|---|
| 1 | Navy field (band + column) | kept | sky; ground for the wordmark and the paper elevator |
| 2 | Headhouse | kept | elevator |
| 3 | Leg housing (narrow, offset) | kept | makes the headhouse an elevator, not a tower |
| 4 | Gallery beam (full width, carries CANTINA) | kept | the word-image link and the elevator signature |
| 5 | Bins with conical caps (picos) | kept | cylinders plus the papel-picado hem |
| 6 | Half-round tone on the bin walls | kept | the cylinder read at thumbnail |
| 7 | Half-round tone on the cones | **removed** | at thumbnail it turned the cones into flags; the paper cones against navy read better |
| 8 | Rombo row 1 (upper bin walls) | kept | the pierced-paper read, and the only amber in the art |
| 9 | Rombo row 2 (lower bin walls) | **removed** | a second row turned the bins into patterned wallpaper |
| 10 | Rombo column in the headhouse | **removed** | read as window trim (the "Greek key" risk flagged in round 4) |
| 11 | Amber ground line | kept | the elevator stands on the ground, and Beer & Cider hangs from it |
| 12 | Amber misregistration trap | kept | the one print artefact (per the brief) |
| 13 | Wordmark on the beam | kept | display word |
| 14 | Sub-line | kept | venue and city |
| 15 | Dark-amber section heads | kept | single text accent |
| 16 | Italic sub heads and draft tasting note | kept | the draft's groups and its one note |

Removed 3 of 16 (19%). Also retired since J5: the navy mottling, the amber pinholes, the full-width papel-picado band,
the navy bin seams, the leg gable and the gallery posts. Relative to J5's 22 devices, 9 are gone (41%). Against the J4
checkpoint on the gates: contrast minimum still 5.48:1, names and prices 13.9 pt, and margins now equal on the left,
top and bottom, with no dead band.

## visual_tests: before / after
- **Accent share outside the art** (text-area crop): **0.11% before → 0.11% after** (the dark-amber heads).
- **Whole page:** 0.37% → 0.32%. Amber is now only the rombos and the ground line. J5 was 11.28% and J4 29.49%.
- **Squint test:** one dominant region, 20.51% → 20.48% of the page (the navy field with the elevator cut into it). There is no competing region.
- **Visual centroid:** (0.49, 0.206).
- **Silhouette correlation:** vs J5 0.813, vs J4 0.481.

```json
[
 {
  "file": "J6 after (preview-letter.png)",
  "squint_salient_regions": 1,
  "primary_area_pct": 20.48,
  "primary_to_secondary": null,
  "ground_luminance": 0.913,
  "value_range_p5_p95": [
   0.129,
   0.932
  ],
  "accent_area_pct": 0.32,
  "visual_centroid": [
   0.49,
   0.206
  ]
 },
 {
  "file": "J6 before (before/preview-letter.png)",
  "squint_salient_regions": 1,
  "primary_area_pct": 20.51,
  "primary_to_secondary": null,
  "ground_luminance": 0.913,
  "value_range_p5_p95": [
   0.129,
   0.932
  ],
  "accent_area_pct": 0.37,
  "visual_centroid": [
   0.49,
   0.206
  ]
 },
 {
  "file": "J5",
  "squint_salient_regions": 2,
  "primary_area_pct": 24.46,
  "primary_to_secondary": 1055.92,
  "ground_luminance": 0.899,
  "value_range_p5_p95": [
   0.156,
   0.935
  ],
  "accent_area_pct": 11.28,
  "visual_centroid": [
   0.531,
   0.214
  ]
 },
 {
  "file": "J4 checkpoint",
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
  "file": "J6 after: text area crop (x<460, y>=192)",
  "squint_salient_regions": 18,
  "primary_area_pct": 0.26,
  "primary_to_secondary": 1.34,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.759,
   0.932
  ],
  "accent_area_pct": 0.11,
  "visual_centroid": [
   0.391,
   0.537
  ]
 },
 {
  "file": "J6 before: text area crop",
  "squint_salient_regions": 18,
  "primary_area_pct": 0.26,
  "primary_to_secondary": 1.34,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.759,
   0.932
  ],
  "accent_area_pct": 0.11,
  "visual_centroid": [
   0.391,
   0.537
  ]
 }
]
```

## Contrast and legibility (contrast.json)
Letter, worst pixel behind each run:
- Section heads: 5.48:1.
- Sub heads, descriptions, prices and the note: 6.6:1.
- Names: 14.4:1.
- Sub-line: 12.3:1.

**Wordmark:** the automatic check reports 1.0:1 because the text box includes the paper beam CANTINA stands on, which is intended. Measured over the glyph area above the beam (y 41-115.5), the worst pixel is **13.7:1**.

Sizes: names 13.9 pt, descriptions 10.1 pt. Phone: same ratios; the sub-line is 7.9 pt.

## References
- ref-02-3acf255d.png: panels 1 and 5 (art in a side column beside the list, text in the safe inset).
- ref-03-ffe03c52.png: panels 2 and 5 (flat cut shapes on a dusk field).

The papel-picado grammar is sourced as above. No library queries this round.

## Files
- build.py: run `python3 build.py [before|after]`. `J6_ABL=` renders ablations. It writes the art rasters and the HTML.
- art-letter.png and art-phone.png: the text-free art at full resolution.
- menu.html
- preview-letter.png (2550x3300)
- preview-phone.png (1170x5196)
- before/
- visual_tests.json
- contrast.json
- geometry.json
