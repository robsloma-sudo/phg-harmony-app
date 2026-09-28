# Explore H2: "Sun & Furrow" (TEST-1, Iowa City cantina bar menu; round 2 of direction H)

Checkpoint kept untouched: `../explore-H/` (round 1, scored 61.1; all three reviewers failed the price-association gate).
Binding doctrine: `DESIGN_THEORY_BRIEF.md`, sections 1-5; section 5 was re-read before this round.
Reference bar: `references/rob-2026-09-28/ref-02-3acf255d.png`. H2 deliberately leaves panel 2's structure: there is no stair block and no corner stamp.

## 1. Thesis (written before code)
**Creative thesis:** One plough line draws an Iowa hillside, where contour furrows curve over the land and turn at the headland in a squared Mesoamerican step-fret. A terracotta sun sets behind the first furrow, so Mexico and Iowa City share one horizon drawn with one line.

Why it passes the substitution test: the gesture is not "a sun" or "a stair". It is a plough path whose turns are grecas. Another bar's menu could not borrow it without also borrowing both halves of the idea: contour ploughing, which is specific to Iowa (the Loess Hills and Iowa's soil-conservation farming), and the step-fret, which is specific to Mesoamerica.

**Concept words:** plough line, contour, greca, horizon, sunset, boustrophedon.

**Avoid-list:**
- agave, cactus, moon, bottles, glasses, sombrero, papel picado, corn cobs
- stair blocks or corner stamps
- gradients or texture
- boxes, rules, leaders, tables or price ornaments
- borrowed taglines
- a second accent colour
- tracked caps on labels longer than 3 words
- any description text that is not in the draft or the recipes

## 2. The gesture, precisely
- **One continuous single-weight line** (2.2 css px = 0.58 mm, ink) ploughs six furrows in boustrophedon order.
  - Furrow k follows `y_k(x) = 272 + 13k - 62*exp(-((x-650)/250)^2)`, a hill whose crest sits under the sun.
  - The line runs right to left, turns at the left headland, then runs left to right. It turns again 24 px beyond the right trim (bleed), so it enters and leaves through the right edge as one path.
- **Greca headlands:** each left turn is a squared hairpin. The three hairpins step outward (x = 88, 64, 40 css px), forming the stepped-fret profile, which also reads as terraces.
- **One horizon:** the sun (terracotta disc, r 200 at (650, 100), cropped by the top and right trims) is clipped by the first furrow. It sets behind the land, and the line and the disc share one silhouette.
- **Rhythm:** the furrow pitch U = 13 px is the layout unit of the reading layer. Item gap = U, sub-head gap = U, and section gap = 4U, so the page's vertical rhythm is the furrow rhythm.
- **Wordmark as structure:** CANTINA is set in **Chango** (Fontstage, OFL). The face is based on letters drawn by the Mexican illustrator and caricaturist Ernesto "Chango" García Cabral, per the Google Fonts description.
  - It is fitted to the full 688 px measure (106 px, `textLength` spacing) with its cap top on the 64 px top margin.
  - The sun's edge crosses the T's right arm at about x 450, clear of the T's stem by about 14 px. From there, T-arm, I, N and A knock out to cream.
  - The collision is pushed from one letter-foot (round 1) to three and a half letters. The wordmark and the sun now squint as one mass.

## 3. Layout geometry (letter 8.5 x 11 in = 816 x 1056 css px; PNG x3.125 = 2550 x 3300)
| Element | Position / size |
|---|---|
| Margins (text) | 64 px = 0.667 in = 16.9 mm on all four sides. Wordmark cap top at y 64; left and right text edges at 64 / 752; the last text line ends at y 983 (73 px from trim) |
| Sun | circle (650, 100) r 200; visible area limited by the top trim, right trim and hill crest (crest y 210 at x 650) |
| Plough line | from y 210 (crest) to y 337 (lowest headland); headlands at x 88 / 64 / 40; bleed 24 px past the right trim |
| Wordmark | Chango 106 px, x 64-752, baseline ~142; knock-out = SVG clipPath of the sun circle |
| Sub-line | "& cocktail bar · Iowa City, Iowa", EB Garamond 500 caps 13 px, tracking .28em, x 64, y ~170 (two 3-word labels) |
| Column 1 | x 64, y 376, w 322: Cocktails (Classics: Margarita, Manhattan; House Originals: House Daiquiri, Brown Butter Old Fashioned), then Beer (Draft) |
| Column 2 | x 430, y 376, w 322: Spirits (Agave, Brandy), then Wine (By the Glass, Sparkling), then Cider |
| Section heads | EB Garamond 500 caps, **18 px = 13.5 pt**, tracking .16em, terracotta `#A6472A` |
| Sub heads | EB Garamond 500 caps 11.5 px, tracking .22em, ink-2 `#5B5149` |
| Names | EB Garamond 500, 17.5 px = 13.1 pt (55 px in the PNG), title case, ink `#1E1A17` |
| Prices | inline, 0.9 em (15.8 px) after the name; same size, **weight 400 in ink-2**, lining and tabular figures |
| Descriptions | EB Garamond italic 13.25 px = 9.9 pt, ink-2; every middot is kept at the end of the line it closes (no line starts with "·") |
| Palette | cream `#F3EBDD`, ink `#1E1A17`, ink-2 `#5B5149` (a lighter value of the ink), one accent terracotta `#A6472A` (sun and section heads only) |

Phone (390 css px x3 = 1170 x 4206): the top zone is scaled 0.497 into 24 px margins, with the same sun, line and knock-out. The sub-line moves below the land. The reading layer is one column in the order Cocktails, Beer, Spirits, Wine, Cider. Names are 17 px and descriptions 14 px, and prices stay inline.

## 4. Price association (the failed gate)
From `layout.json`, measured in the browser:

| | Name-end to price gap | Gap as % of page width | Name start to price end, worst row |
|---|---|---|---|
| Letter | 15.8 px on every row | 1.9% | 28.5% ("Brown Butter Old Fashioned 16") |
| Phone | 15.3 px on every row | 3.9% | 57.9% for the same row |

- The phone's 57.9% is the length of the name itself. The eye's jump from name to price is still 15 px.
- Every other phone row is 36% or less.
- The price is lighter (weight 400, ink-2), so "Cognac VSOP 18" reads as a price, not an age statement.

## 5. Content (all from the draft or the venue recipes; nothing invented)
| Item (price) | Description printed | Source |
|---|---|---|
| Margarita (15) | Tequila blanco · fresh lime juice · orange liqueur · agave syrup · lime wheel. Bright and citrus-forward. | components + garnish + draft desc sentence 2 |
| Manhattan (15) | Rye whiskey · sweet vermouth · cocktail cherry | components (aromatic bitters hidden by `public_components`) |
| House Daiquiri (14) | White rum · fresh lime juice · demerara syrup · lime coin | components + garnish |
| Brown Butter Old Fashioned (16) | Brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel | component names only (`house_recipe=false`) + garnish |
| Czech Pilsner (7) / Dry-Hopped IPA (8) / Amber Lager (7) | Crisp pale lager / Hop-forward draft IPA / Toasty amber lager | draft desc, full |
| Blanco Tequila (12) / Añejo Tequila (16) / Cognac VSOP (18) | Blanco tequila pour / Añejo tequila pour / VSOP Cognac pour | draft desc, full ("pour" = sourced serve label) |
| Malbec (12) / Pinot Grigio (11) / Brut Rosé (13) | Dry red wine / Dry white wine / Dry sparkling rosé | draft desc, full |
| Dry Cider (8) | Dry sparkling cider | draft desc, full |

- **Garnish source.** The garnishes (lime wheel, lime coin, orange peel, cocktail cherry) come from the Coordinator's round-2 brief, citing `phg.recipe_versions`. The same values appear in `explore-D/variations.md` from the earlier recipe read. I did not re-run the gateway query this round, so the Coordinator should confirm them against `phg.recipe_versions` before filing.
- **Order.** Margarita is first (the draft had Manhattan first in Classics). Spirits come before Wine. The Agave and Brandy sub heads are restored.
- **Taglines.** None.
- **Coverage.** All 14 items and prices are printed, and `build.py` asserts full coverage.

## 6. Device inventory (final)
1. Terracotta sun (clipped by the land)
2. One continuous plough line with greca headlands
3. CANTINA in Chango, full measure
4. Cream knock-out of the wordmark inside the sun
5. Sub-line (two 3-word labels)
6. Section heads in the accent (13.5 pt)
7. Sub heads (ink-2)
8. Italic description line
9. Inline muted price

Budget: 1 gesture, 1 display word, 1 accent colour. There are 0 boxes, rules, leaders, tables, icons, price ornaments and taglines.

## 7. Revision log, subtraction pass and before/after numbers
Before = explore-H (round-1 checkpoint).

| Round | Hypothesis / change | Regions | Primary % | Pri:Sec | Accent % | Verdict |
|---|---|---|---|---|---|---|
| **H (before)** | stair block + disc, Cinzel, price track | 8 | 5.93 | 2.71 | 5.55 | failed the price gate; "ref-02 traced" |
| H2 v1 | Chango wordmark; concentric furrow rings round the sun with stepped ends; inline prices; full descriptions | 2 | 8.25 | 2.65 | 7.44 | the rings read as a vinyl record or rainbow, and the art stayed a corner stamp. Lower 250 px of the page were dead. **Replaced** |
| v2 | the line becomes a hillside: six contour furrows crossing the full width, boustrophedon, greca headlands at left; the sun set behind furrow 1 | 2 | 7.62 | 2.45 | 6.83 | sun and land read as one horizon. Kept |
| v3 | raised the hill (Y0 300 to 272); U 12 to 13; names 16.5 to 17.5 px; section gap 3U to 4U to fill the dead lower field | 2 | 7.11 | 2.29 | 6.32 | text now ends 73 px from the bottom trim. Kept |
| v4 | sun r 170 to 200, moved so its edge cuts the T's arm (the round-1 cut left a thin sliver on the I, which looked accidental) | **1** | 11.34 | n/a (single region) | 7.39 | the collision is pushed further and the wordmark and sun form one dominant mass. Kept |
| ablation | six furrows cut to four | 1 | 11.34 | n/a | 7.38 | the stair profile collapses to two steps and the field stops reading as ploughed. **Reverted** |
| ablation | pitch spread over the crest (1 + 0.35·bump) removed | 1 | 11.41 | n/a | 7.39 | no visible loss. **Removed** |
| **H2 (after)** | final | **1** | **11.41** | **n/a** (one region) | **7.39** | |

Subtraction, counted against the round-1 device list (tagline stack, stair block, disc, knock-out, wordmark, sub-line, section heads, sub heads, descriptions, price track = 10):
- Removed:
  - the tagline stack
  - the stair block (replaced by the single line, which also carries the sun connection)
  - the price track (replaced by inline prices)
  - the invisible pitch-spread refinement
- The four-furrow cut was tested and reverted, because the render proved it hurt.
- That is 3 of the 10 round-1 devices removed outright (30%), with no new device added beyond the one line.

**Accent share:** 7.39% of the page, inside the 8% budget. The sun is the colour field of the gesture. About a quarter of its disc is hidden by the land and by the four cream letters, which is what keeps it under budget at r 200.

**Dominance:** squint shows exactly one salient region (the wordmark and sun, 11.4% of the page). The reading layer and the plough line stay below the salience threshold, and the visual centroid is (0.60, 0.18), top-right of centre.

## 8. visual_tests.json (final)
```json
{"file": "preview-letter.png", "squint_salient_regions": 1, "primary_area_pct": 11.41,
 "primary_to_secondary": null, "ground_luminance": 0.924, "value_range_p5_p95": [0.349, 0.928],
 "accent_area_pct": 7.39, "visual_centroid": [0.6, 0.177]}
```

## 9. Legibility (contrast.json, worst pixel under every text run, letter and phone)
| Text | Contrast |
|---|---|
| Names | 14.6:1 |
| Prices, descriptions, sub heads, sub-line | 6.53:1 |
| Section heads | 4.99:1 |
| Knocked-out wordmark letters (cream on terracotta, display text) | 4.99:1 |

Names are 13.1 pt and descriptions 9.9 pt, both above the minimums.

## 10. Files
- `build.py`: builds from `../build/draft_doc.json`, fits the wordmark, draws the line, renders, and writes the reports
- `menu.html` (letter)
- `preview-letter.png` (2550 x 3300)
- `preview-phone.png` (1170 x 4206)
- `visual_tests.json`, `contrast.json`, `layout.json` (includes `eye_travel` per row)
- `fonts/`: Chango, EB Garamond (all OFL)

## 11. Open points for the Coordinator
- Confirm the four garnishes against `phg.recipe_versions` (see section 5).
- The app needs the Chango and EB Garamond fonts, or the renders will fall back to other fonts.
