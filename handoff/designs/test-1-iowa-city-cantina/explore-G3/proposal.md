# TEST-1 · Direction G3 "Monument", round 3 (letterpress pull, quiet reading layer)

Status: exploration for the Coordinator. Not submitted, not committed. `explore-G2/` stays as the round-2 checkpoint.
Build: `python3 build.py` (after) and `python3 build.py before`. Monument: `glyphs.py` (letterforms) + `press.py` (plates).
Content: `../build/draft_doc.json` rev 3. Garnishes come from `phg.recipe_versions.garnish` (gateway log_id 213).
Description content is unchanged from G2 apart from the voice fixes requested (point 7).

## 1. Thesis
**Thesis:** CANTINA is printed, not typeset. It is a wood-type pull of rótulo sign letters, with grain in the solids
and a chile plate that overprints out of register. Iowa City shows up in how the name was made (a press print, the
craft of a writing-and-printing town), and Mexico in what was cut (sign-painter letterforms). Neither is stated in words.

**Concept words:** press · wood · overprint · register slip · sign letter · quiet list

**How a guest sees Iowa City without a tagline:**
- The monument is visibly a physical print. It has wood grain in the black, an overprint where red over black goes
  darker, and a plate that is skewed rather than shadowed.
- That is the city's print culture, shown as making. The menu prints no claim about the city or the venue. The only
  place words are "Iowa City, Iowa", on the venue line at the monument's foot.

**Why the red can no longer read as a drop shadow (critic's round-2 note):**
- A drop shadow is a constant offset. The G3 chile plate is rotated 0.9° about the word's centre and slipped 1.6
  units along the letter axis.
- At the head of the word the red escapes on the right of the strokes; at the foot it escapes on the left; through the
  middle it disappears under the key.
- It prints with `mix-blend-mode: multiply`, so where red lies over black the stroke goes darker, and the uncovered
  key edges print a shade lighter. That is exactly what a two-plate overprint does.

**Avoid-list:** drop shadows · stock display fonts · ink-trap notches (removed; they read as chipped corners) ·
boxes and cards · leaders · price ornaments · tables · icons and cantina clip-art · distress texture outside the
monument · taglines · tracked caps on labels longer than 3 words · invented facts.

## 2. Round-3 fixes
1. **Press reading:**
   - The chile plate is now a true multiply overprint, skewed so red appears on both sides of the strokes along the word.
   - The key plate carries wood grain: fractal noise stretched along the letter-width axis at 0.018 x 0.42 cycles per
     glyph unit, letting at most ~15% paper through, so it holds up at print size.
   - The red plate has its own, weaker grain.
   - A deboss ring was tried and then removed in the subtraction pass (section 3).
2. **Ink traps removed** (`glyphs.USE_TRAPS = False`). The chamfers stay.
3. **Quiet reading layer on one row grid:**
   - Names: Newsreader 500, 19 px (14.25 pt). Prices: 19 px, 400 weight, muted ink.
   - Descriptions: Newsreader italic, 13.5 px (10.1 pt).
   - Every line box is exactly one 22 px row, and every gap is a whole number of rows, so rows align across both
     columns. The build found 0 line boxes off the grid.
   - Section heads Cocktails/Beer share a row, as do Classics/Draft, Spirits/Wine and Brandy/Sparkling.
   - The page is filled by pacing, not stretched gaps. The rhythm is item gap 1 row : sub-head gap 3 rows : section
     gap 5 rows in both columns.
   - The list's first row aligns with the head of the monument's A (y = 122), and both columns end on the same final
     row (y = 980).
4. **Whole ingredients:**
   - Each ingredient is a no-wrap unit with non-breaking spaces ("lime wheel", "cocktail cherry", "orange liqueur",
     "demerara syrup", "agave syrup", "fresh lime juice", "brown butter-washed bourbon"). The separator dot is joined
     to the preceding ingredient with a non-breaking space, so no line starts with "·".
   - The build audits each description line and found no one-word lines.
   - The Margarita's "Bright and citrus-forward." now runs on in the same line flow.
5. **Sub heads and order:**
   - One sub-head treatment everywhere: "Draft" is its own row, like Classics and Agave.
   - Order: Cocktails, then **Spirits** (Agave, Brandy) directly under the cocktails in the first column, which keeps
     the agave pours prominent; then Beer, **Cider next to Beer**, and Wine.
   - Spirits precede Wine.
6. **Iowa City in form:** see section 1. Nothing printed asserts a fact about the venue.
7. **Descriptions:** content unchanged apart from the voice fixes above.

Printed descriptions, all sourced (line breaks as rendered on letter):

| Item | Price | Description |
|---|---|---|
| Margarita | 15 | Tequila blanco · fresh lime juice · orange liqueur · / agave syrup · lime wheel. Bright and citrus-forward. |
| Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry (bitters hidden) |
| House Daiquiri | 14 | White rum · fresh lime juice · / demerara syrup · lime coin |
| Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon · demerara syrup · / aromatic bitters · orange peel |
| Blanco Tequila | 12 | Blanco tequila pour |
| Añejo Tequila | 16 | Añejo tequila pour |
| Cognac VSOP | 18 | VSOP Cognac pour |
| Czech Pilsner | 7 | Crisp pale lager |
| Dry-Hopped IPA | 8 | Hop-forward draft IPA |
| Amber Lager | 7 | Toasty amber lager |
| Dry Cider | 8 | Dry sparkling cider |
| Malbec | 12 | Dry red wine |
| Pinot Grigio | 11 | Dry white wine |
| Brut Rosé | 13 | Dry sparkling rosé |

Missing ABV, region and brand data is waiting on Rob (risk flag `awaiting_owner_data`).

## 3. Device inventory, subtraction log and numbers
**Before** (`preview-letter-before.png`) had 11 devices:
1. drawn letterforms
2. chamfers
3. key plate wood grain
4. chile overprint plate (multiply)
5. plate skew and slip
6. deboss/impression ring
7. venue line at the foot
8. red section heads
9. inset rule under section heads
10. grey sub heads
11. muted inline prices

| Device | Decision | Reason |
|---|---|---|
| Deboss / impression ring | **removed** | Ablation showed no visible change at reading distance; at full size it only greyed the A counter. The grain and overprint already carry "press" |
| Rule under section heads | **removed** | It added a horizontal system competing with the monument and the row grid; the grid and pacing do the separating |
| Ink traps (a round-2 device) | **removed** | Per the brief: they read as chipped corners |
| Red grain | kept, weaker | Without it the red slip reads as flat vector, which undoes the press reading |
| Everything else | kept | Each is either a thesis device (letterforms, chamfers, grain, overprint, skew) or a reading-layer requirement |

That is 3 of 12 candidate devices removed (25%).

**Revision hypotheses:**
- (a) A skewed multiply plate reads as a register slip, not a shadow. Confirmed at full size: red is on opposite
  sides at the head and the foot and vanishes mid-word.
- (b) A quiet reading layer on a 22 px row grid can fill the page by pacing.
  - The first try put all leftover rows at the top, which left a 154 px dead top field. Rejected.
  - The second try aligned the list top to the head of the A and paced the remaining rows 1 : 3 : 5. Accepted: both
    columns land on the same final row with identical pacing.
- (c) The G2 split (Cocktails, Beer | Spirits, Wine, Cider) gave 37 against 34 rows. Cocktails, Spirits | Beer,
  Cider, Wine gives 35 against 34 rows and satisfies "Cider next to Beer" and "Spirits before Wine". Adopted.

| visual_tests metric | G2 (checkpoint) | G3 before | **G3 after** | target |
|---|---|---|---|---|
| squint_salient_regions | 1 | 1 | **1** | one dominant |
| primary_area_pct | 15.40 | 15.74 | **15.75** | — |
| accent_area_pct | 1.68 | 1.05 | **1.07** | ≤ 8 |
| value_range_p5_p95 | 0.096–0.912 | 0.029–0.908 | 0.029–0.908 | — |
| visual_centroid | 0.783, 0.418 | 0.810, 0.422 | 0.814, 0.421 | — |
| silhouette corr vs G2 | — | 0.970 | 0.970 | same direction (a refinement round, as intended) |

The darker p5 (0.029) comes from the overprint: red multiplied over black is the deepest value on the page.
`visual_tests.json` (final):
```json
{"file": "preview-letter.png", "squint_salient_regions": 1, "primary_area_pct": 15.75, "primary_to_secondary": null,
 "ground_luminance": 0.908, "value_range_p5_p95": [0.029, 0.908], "accent_area_pct": 1.07, "visual_centroid": [0.814, 0.421]}
```

## 4. Layout geometry (CSS px, 96/in; x3.125 = 300 dpi). Every element box is in `geometry.json`.
- **Page:** letter 816 x 1056, rendered at 2550 x 3300. PAPER #EFE7D8.
- **Margins:** 56 px (0.58 in) for all text. Only the monument crosses the trim.
- **Grid:**
  - Two columns, 282 px + 30 px gutter + 178 px (x 56–338 and 368–546).
  - Row grid 22 px: 42 rows between the margins. The list occupies rows 3–41 (y 122–980).
  - Section rows: Cocktails and Beer at y 122; Cider at 474; Spirits and Wine at 672.
  - Sub-head rows: Classics and Draft at 166; House Originals at 386; Agave and By the Glass at 716; Brandy and
    Sparkling at 914.
- **Channel:** the monument baseline is at x 618.8, and the red spill reaches at most 7.8 px past it. The channel is
  **64.9 px ≥ 2 x gutter (60)**.
- **Monument:**
  - The word is 401 units long at cap height 100. Scale 2.1438, so the cap is 214.4 px.
  - It runs from y = -12.7 (cropped by the top trim) to y = 847, rotated 90° with tops toward the trim. The tops are
    cropped 8% past the right trim (4.6 mm bleed), and the top overshoot is 3.4 mm.
  - Key INK #1B1815 with grain. Chile #9B2D1F overprint (multiply), rotated 0.9° about the word's centre, slipped 1.6
    units along the axis.
- **Foot:** Oswald 500, 12 px, .30 em, rotated 90°, on 22 px lines. Line 1 "& COCKTAIL BAR" sits on the monument
  baseline; line 2 "IOWA CITY, IOWA" is in INK2. The box is x 590.9–634.9, y 869–1000.5.
- **Type:**
  - Section heads: Oswald 500, 15 px, .30 em, CHILE.
  - Sub heads: Oswald 500, 12 px (9 pt), .30 em, INK2.
  - Names: Newsreader 500, 19 px. Prices: Newsreader 400, 19 px, INK2, tabular figures, 0.55 em plus a no-break space after the name.
  - Descriptions: Newsreader italic, 13.5 px, INK2, `text-wrap: pretty`.
  - All line heights are 22 px.
- **Measured:** maximum eye travel 7.9% on letter and 4.1% on phone (limit 40%). No name wraps.
- **Contrast on paper:** INK 14.39 · INK2 7.65 · CHILE 6.13. No texture sits behind any reading text.
- **Phone (390 css x3 = 1170 x 5172):**
  - The same pull runs horizontally across the width (scale 0.9726), with tops cropped 8% by the top trim. The venue
    line is directly under its baseline.
  - One column in the same order on a 21 px row grid, with pacing 1 : 2 : 3. Names 18 px, descriptions 13.5 px.

## 5. References
- `references/rob-2026-09-28/ref-02-3acf255d.png` (the quiet two-column grammar; red tracked heads) and
  `ref-01-98c65abe.png` (a vertical wordmark carrying the page).
- Library: documents 572 (COA Cantina Iowa City), 7923, 2368 and 2929, used for list structure only (gateway log 208).

## 6. Risks
- `awaiting_owner_data`: ABV, region and brand.
- `nbsp_in_text`: descriptions contain U+00A0 inside ingredients. Content diffing should normalise whitespace.
- There is no bleed PDF yet. The monument already extends ≥ 3 mm past the trim at the top and right.
- The grain is SVG `feTurbulence`, rendered by Chromium. A print RIP would need the rasterised PNG or a PDF from the same engine.
