# TEST-1 explore-J5 "Horizon", round 5 (checkpoint: ../explore-J4)

## Thesis
**Dusk over an Iowa grain elevator, with the last light strung along the ground like the cut edge of a papel picado
banner: a cantina in Iowa City.**

Concept words: horizon · dusk · grain elevator · papel picado · screen-print · flat

Avoid-list: stepped stairs or escalonado glows (retired: they were borrowed from ref-02 panel 2); sun/moon, agave, cacti,
glasses; smokestack, boot or church silhouettes; colonnade rhythm, window dots; gradients or blur; digital-noise
filters; boxes, cards, rules, leaders, price ornaments; tracked caps over 3 words; taglines; a second display word;
texture behind reading text.

**The one gesture.** A two-ink screen print: navy and amber on paper.
- **Navy:** the dusk field, running across the top and down the right column to the ground line.
- **Elevator:** a true-profile Iowa grain elevator in unprinted paper (pale, like slip-formed concrete).
  - A headhouse with its leg housing.
  - A gallery bridge running from the headhouse across the bin crowns.
  - A row of domed cylindrical bins, cut by the right trim.
- **Amber:** the elevator stands on a ground band whose lower edge is cut like the border of a papel picado banner, with
  picos (zig-zag) and pierced rombos (diamonds). The band crosses the full width of the page as the horizon, so the lower
  tier hangs from it.

**Where the Mexican form comes from.** Papel picado is the pierced tissue-paper banner of Mexican fiestas. It is
chisel-cut through stacks of tissue with hammer and fierritos, and its best-known production centre is San Salvador
Huixcolotla, Puebla. A standard banner is framed by a cut border: a scalloped or zig-zag "picos" edge along the hem and a
line of small pierced shapes (rombos, dots, teardrops) just inside it. J5 uses only that border grammar (picos + rombos),
at banner scale, as one flat amber cut. Strung at the horizon, it is literally light seen through cut paper at dusk.

**Substitution test.** The fusion is Mexico's festive cut-paper edge as the ground under Iowa's grain elevator. It
belongs to a cantina in Iowa City. It is not a generic bar image and not the reference's stair.

## Round-4 critique → J5 fixes
| # | Fix | Done |
|---|---|---|
| 1 | True elevator | Headhouse 92 x 482 css px (x 496-588, top 128), plus a leg housing (x 508-542, rising 46 px). A gallery bridge runs from the headhouse across the bin crowns to the trim (y 249-264, resting on the crowns). Four domed bins 62 px wide (x 594 → 842; the right trim at 816 cuts the fourth) with 3 px seams, which read as cylinders rather than a colonnade because the bins are wide and the seams are hairlines. A 6 px sky gap separates the headhouse from the bins. The base stands on the amber ground band (G = 610), so there is no floating slab. Checked at thumbnail and 100%: it does not read as a smokestack (headhouse wider than the leg, with bins attached) or a boot (the bins and gallery break the L). |
| 2 | Stair replaced | The escalonado glow is gone. It is replaced by the papel-picado ground band (see above). |
| 3 | Print materiality | The art is a raster (art-letter.png, 2550x3300; art-phone.png, 1170 wide) generated in build.py at full print resolution. Navy: uniform ink mottling (coverage 90-100%, 0.9 px and 2.2 px noise scales). Amber: the same mottling. The amber pass is misregistered by 3 px right and 2 px down at 300 dpi (0.25 mm), and navy multiplies over it, so a dark trap line shows where the navy column meets the band. There are no pinholes in the navy, so the worst pixel behind the wordmark still passes (10.5:1). Checked in 1:1 crops at print resolution: it reads as a flat screen-printed ink, not a filter. |
| 4 | Rag | Descriptions are broken by the builder only between ingredients (fewest lines, most even split, no lone final ingredient where avoidable). The separator at a break is dropped, so no line ends or starts with a middot (the geometry check `line_ends_with_middot` is empty on letter and phone). The Old Fashioned now reads "Brown butter-washed bourbon / demerara syrup · aromatic bitters · orange peel", with no orphan garnish. |
| 5 | Margarita note | The ingredient list includes the lime wheel garnish, then "Bright and citrus-forward." on its own line in Fraunces italic. It is the draft-supplied tasting note (second sentence of the draft desc). Only drafts that supply a tasting note get one; the Margarita is the only one. |
| 6 | Balance | The lower tier is set in three max-content columns spread with `justify-content: space-between`. The left edge is at 60 and the widest Wine line ends exactly at 756, so the right margin equals the left (60). Column bottoms: 936 / 994 / 936, still a 58 px spread. Not solved: see below. |
| 7 | Order | Agave-forward on purpose: the Margarita (tequila) leads Cocktails, and Spirits (with Agave first) is the first lower-tier column, ahead of Beer & Cider and Wine. The cantina's category leads. "Hop-forward draft IPA" is kept as the draft text, because brief section 5 says to keep style words even where they partly echo the name. |
| 8 | Spirits lines | Taken from public.beverage_categories through the read-only gateway (phg_designer_query log ids 225 and 226, verified this round). See the table below. Every node is `proposal_status = proposed` in the taxonomy (not yet approved). Flagged. |
| 9 | Content | Otherwise unchanged. |

**Column spread (item 6).** Ten items over three columns leaves Beer & Cider exactly one item longer (58 px). Every
option I tested breaks a rule set in an earlier round:
- Pushing the second group down in the short columns is the J3 `margin-top:auto` look, which was rejected.
- Evenly opening the gaps in the short columns adds about 20 px to each of their gaps, so the rhythm differs between columns.
- Dropping the Draft H3 cuts the spread to about 26 px, but breaks the shared first-item row asked for in round 4.

The short | long | short profile is symmetric about the middle column. The longest column ends on the bottom margin
(994 of 996). The Coordinator should choose one of the three options above if the spread must go.

## Content
| Group | Item | Price | Description (line breaks as set on letter) | Source |
|---|---|---|---|---|
| Cocktails / Classics | Margarita | 15 | Tequila blanco · fresh lime juice / orange liqueur · agave syrup · lime wheel / *Bright and citrus-forward.* | components + rv f06abb74 garnish + draft desc sentence 2 |
| Cocktails / Classics | Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry | components (bitters hidden) + rv 9fb77eaa |
| Cocktails / House Originals | House Daiquiri | 14 | White rum · fresh lime juice · demerara syrup · lime coin | components + rv 14d45e57 |
| Cocktails / House Originals | Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon / demerara syrup · aromatic bitters · orange peel | components (names only) + rv 7095fd3d |
| Spirits / Agave | Blanco Tequila | 12 | Blanco-class agave spirit · pour | beverage_categories `spirits.agave_spirits.tequila.blanco` ("Blanco / plata", NOM-006-SCFI-2012 §5 clase); parent `spirits.agave_spirits` ("Agave & desert spirits"); "pour" from the draft desc |
| Spirits / Agave | Añejo Tequila | 16 | Añejo-class agave spirit · pour | `spirits.agave_spirits.tequila.anejo` ("Añejo", NOM-006-SCFI-2012 §5 clase) |
| Spirits / Brandy | Cognac VSOP | 18 | Grape brandy from Cognac · pour | `spirits.brandy_fruit_spirits.grape_brandy.cognac.vsop` (Grape brandy › Cognac › VSOP) |
| Beer & Cider / Draft | Czech Pilsner | 7 | Crisp pale lager | draft desc |
| Beer & Cider / Draft | Dry-Hopped IPA | 8 | Hop-forward draft IPA | draft desc (kept per brief §5) |
| Beer & Cider / Draft | Amber Lager | 7 | Toasty amber lager | draft desc |
| Beer & Cider / Cider | Dry Cider | 8 | Dry sparkling cider | draft desc |
| Wine / By the Glass | Malbec | 12 | Dry red wine | draft desc |
| Wine / By the Glass | Pinot Grigio | 11 | Dry white wine | draft desc |
| Wine / Sparkling | Brut Rosé | 13 | Dry sparkling rosé | draft desc |

No aging years, brands or "100% agave" claims appear. The taxonomy has a `tequila_100_agave` node, but nothing links
these items to it. Still waiting on Rob: producer, region and ABV for wine, beer and cider; brand and pour size for spirits.

## Layout geometry (letter 816 x 1056 css px = 2550 x 3300 px at 300 dpi; 1 css px = 0.265 mm)
- **Margins:** 60 on the left, top and right (wordmark ink top 60.2, lower tier 60 → 756). The bottom margin is 62 (last line 994).
- **ART (raster, text-free, bleeds 12 css px past trim):**
  - Navy top band: y 0-180.
  - Navy right column: x 452 → bleed, down to G = 610.
  - Amber band: y 610-638, with picos 22 px wide and 12 px deep (to y 650) and one pierced rombo per pico (every 22 px) on its centre line.
  - Elevator: headhouse x 496-588 (top 128); leg x 508-542 (top 82); gallery y 249-264; bins x 594 → bleed with crowns at y 263.
- **Wordmark:** CANTINA in Fraunces 430, 76 px (57 pt), tracking 0.14em, paper colour. Ink box 59.2-431.7 x 60.2-116.2.
- **Sub-line:** DM Sans 12.5 px (9.4 pt), tracking 0.2em, ink from x 60.5.
- **Cocktails:** x 60-440 (measure 380), y 212-588. The navy column starts 12 px past the measure; the longest set line is 380.
- **Lower tier:** H2s at y 672, H3s at 704, first items at 736, Brandy and Sparkling at 860, Cider at 918.
  - Columns: Spirits x 60 (210 wide), Beer & Cider x 354 (176 wide), Wine x 615 (142 wide, ending at 756).
  - The equal gaps between columns are 84 px.
- **Type:**
  - Section heads: DM Sans 600, 12.5 px, tracking 0.3em, caps, `#8F4F10`.
  - Sub heads: Fraunces italic 15.5 px, muted `#5B5058`.
  - Names: Fraunces 500, 18.5 px (13.9 pt), ink `#221C22`.
  - Prices: Fraunces 400, 18.5 px, muted, tabular figures, 0.75 em after the name.
  - Descriptions: DM Sans 13.5 px (10.1 pt), muted.
  - Tasting note: Fraunces italic 13.5 px, muted.
- **Palette:** navy `#1E2147`, amber `#D98A2E` (its text form `#8F4F10`), paper `#F4EDE1`, ink, muted.
- **Phone (390 css → 1170 x 5484 px):** the navy field runs 0-300 with the elevator at 0.6 scale (headhouse x 236-292, bins to the trim) standing on the band (300-326 plus picos). The text frame is x 24-366, stacked in the order Cocktails, Spirits, Beer & Cider, Wine.
- Files: geometry.json (every element, plus measured ink boxes and the middot check); contrast.json.

## Device inventory and subtraction log
Revision hypothesis: J4's critique was about legibility and originality of the art, not quantity. Build the richer,
truer elevator plus one sourced Mexican form, then cut every part that does not help the elevator or the papel picado
read at thumbnail or at 100%.

| # | Device (J5 before) | After | Evidence |
|---|---|---|---|
| 1 | Navy field (top band + right column) | kept | sky; ground for the wordmark and for the paper elevator |
| 2 | Amber ground band | kept | the horizon light the elevator stands on; the structural edge the lower tier hangs from |
| 3 | Picos (zig-zag hem) | kept | the papel-picado signature |
| 4 | Pierced rombos | kept | the second papel-picado signature; without them the band reads as rickrack trim |
| 5 | Pierced dots alternating with rombos | **removed** | two piercing shapes competed; one rombo per pico reads clearer at thumbnail |
| 6 | Headhouse | kept | elevator |
| 7 | Leg housing | kept | "not a smokestack": it steps the roofline |
| 8 | Leg-housing gable cap | **removed** | 10 px detail that made the leg read as a chapel belfry |
| 9 | Gallery bridge | kept | the elevator signature asked for |
| 10 | Gallery posts to each crown | **removed** | the gallery now rests on the crowns; the posts read as fence pickets |
| 11 | Domed bin crowns | kept | the bins read as cylinders |
| 12 | Bin seams (3 px) | kept | separate the cylinders without colonnade gaps |
| 13 | Sky gap between headhouse and bins | kept | separates the two masses (no boot) |
| 14 | Navy ink mottling | kept | the print materiality |
| 15 | Amber pinholes (ink starvation) | **removed** | at 100% they read as white noise on the band |
| 16 | Low-frequency density drift | **removed** | read as a digital vignette in the thumbnail |
| 17 | Amber misregistration (0.25 mm) | kept | the trap line at the band proves two passes |
| 18 | 3 px amber rule on top of the band | **removed** | a rule; the band edge is enough |
| 19 | Wordmark | kept | display word |
| 20 | Sub-line | kept | venue and city |
| 21 | Dark-amber section heads | kept | single text accent |
| 22 | Italic sub heads + italic tasting note | kept | the draft's groups and its one note |

Removed 6 of 22 (27%). Checked against J4 (the best-so-far), nothing regressed on the gates:
- Contrast minimum is still 5.48:1, now with the wordmark at 10.5:1 on printed navy.
- Names and prices are still 13.9 pt.
- The margins are equal left and right (60/60).

## visual_tests: before / after
- **Accent share outside the art:**
  - Cocktail band crop: 0.63% before → 0.10% after. The drop is the amber pinhole/rule noise leaving the band edge.
  - Lower-tier crop: 0.11% → 0.11% (the dark-amber heads).
- **Whole page** (the art is the colour field): 8.37% → 11.28%. Removing the amber pinholes makes the band read as solid, saturated ink. J4 was 29.49%.
- **Squint test:** 1 → 2 salient regions. The primary region (the navy field and elevator) is 24.63% → 24.46% of the page. The second region is now the solid amber band, at a 1:1056 ratio to the primary, which is negligible.
- **Visual centroid:** (0.528, 0.218) → (0.531, 0.214).
- **Silhouette correlation** vs J4: 0.538, a structural change.

```json
[
 {
  "file": "J5 after (preview-letter.png)",
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
  "file": "J5 before (before/preview-letter.png)",
  "squint_salient_regions": 1,
  "primary_area_pct": 24.63,
  "primary_to_secondary": null,
  "ground_luminance": 0.897,
  "value_range_p5_p95": [
   0.164,
   0.935
  ],
  "accent_area_pct": 8.37,
  "visual_centroid": [
   0.528,
   0.218
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
  "file": "J5 after: cocktail band crop (text only, x<452, y 186-610)",
  "squint_salient_regions": 7,
  "primary_area_pct": 0.52,
  "primary_to_secondary": 1.21,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.692,
   0.935
  ],
  "accent_area_pct": 0.1,
  "visual_centroid": [
   0.366,
   0.599
  ]
 },
 {
  "file": "J5 before: cocktail band crop",
  "squint_salient_regions": 10,
  "primary_area_pct": 0.52,
  "primary_to_secondary": 1.21,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.642,
   0.936
  ],
  "accent_area_pct": 0.63,
  "visual_centroid": [
   0.377,
   0.633
  ]
 },
 {
  "file": "J5 after: lower tier crop (y>=660)",
  "squint_salient_regions": 0,
  "primary_area_pct": 0.0,
  "primary_to_secondary": null,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.728,
   0.935
  ],
  "accent_area_pct": 0.11,
  "visual_centroid": [
   0.46,
   0.416
  ]
 },
 {
  "file": "J5 before: lower tier crop",
  "squint_salient_regions": 0,
  "primary_area_pct": 0.0,
  "primary_to_secondary": null,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.728,
   0.935
  ],
  "accent_area_pct": 0.11,
  "visual_centroid": [
   0.46,
   0.416
  ]
 }
]
```

## Contrast and legibility (contrast.json, worst pixel of the rendered art behind each run)
Letter:
- Section heads: 5.48:1.
- Sub heads, descriptions, prices and the note: 6.6:1.
- Names: 14.4:1.
- Wordmark on printed navy: 10.5:1. Sub-line: 9.4:1.

Sizes: names 13.9 pt, descriptions 10.1 pt. Phone: same ratios; the sub-line is 7.9 pt.

## References
- ref-02-3acf255d.png: panels 1 and 5 (art in a side column beside the list, text in the safe inset). The stepped stair of panel 2 is deliberately NOT used any more.
- ref-03-ffe03c52.png: panels 2 and 5 (flat posterised shapes, printed colour fields).

No new menu_visual_documents queries were made this round; the only new gateway queries were the two beverage_categories reads (log ids 225, 226).

## Files
- build.py: run `python3 build.py [before|after]`. `J5_ABL=` removes named devices for ablation. The builder writes the art rasters as well as the HTML.
- art-letter.png and art-phone.png: the text-free ART layers at full print resolution.
- menu.html (references art-letter.png)
- preview-letter.png (2550x3300)
- preview-phone.png (1170x5484)
- before/
- visual_tests.json
- contrast.json
- geometry.json
