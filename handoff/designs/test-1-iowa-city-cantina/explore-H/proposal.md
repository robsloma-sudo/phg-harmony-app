# Explore H: "Sun & Terrace" (TEST-1, Iowa City cantina bar menu)

Status: exploration render for the Coordinator. Nothing is applied to the app. The content is the draft (`build/draft_doc.json`, revision 3), with no additions.
References: `handoff/designs/references/rob-2026-09-28/ref-02-3acf255d.png`, panel 2 (cream ground, sun disc, stair form, CANTINA wordmark, two short columns, tagline stack) is the quality bar and the structural model. Read with `DESIGN_THEORY_BRIEF.md`. No library document IDs were used; the house grammar comes from ref-02.

## 1. Thesis (written before code)
**Creative thesis:** One terracotta sun sets over one stepped ink terrace. The same flat staircase reads as adobe steps and as the contour-ploughed terraces of Iowa fields, so the cantina and its town share a single abstract horizon (`abstraction_reduces_cliche`).

**Concept words:** warm, flat, horizon, terraced, calm, bilingual-by-shape.

**Avoid-list:** agave, cactus, moon, bottles, glasses, sombrero or papel picado; gradients, grain or texture; boxes, cards, tables, leaders, rules, price badges; icons; more than one accent colour; tracked caps on labels longer than 3 words; invented descriptions, origins or claims; script faces.

**The one gesture:** a flat terracotta disc cropped by the top-right trim, plus a flat six-step ink terrace cropped by the bottom-right trim. They form one right-hand band: the sun is above and the land below. The CANTINA wordmark collides with the disc on purpose. Inside the disc the wordmark knocks out to cream (the clip-path is the disc circle), so the edge of the sun visibly cuts the final **A**. Only the A's left foot stays ink (`collision_needs_clear_intent`).

## 2. Layout geometry (letter, 8.5 x 11 in; CSS px at 96/in; PNG = x3.125 = 2550 x 3300)
| Element | Position / size | Notes |
|---|---|---|
| Page | 816 x 1056 px, cream `#F3EBDD` | No boxes or rules anywhere |
| Disc | centre (835, 100), r 210 (x 625-1045, y -110-310) | Cropped by the top and right trims; extends 2.4 in past them (bleed well over 3 mm) |
| Terrace | 6 steps, each 42 x 19 px, polygon from x 564 / y 942 to the corner, drawn 12 px (3.2 mm) past the right and bottom trims | Ink `#1E1A17`, flat |
| Wordmark | "CANTINA", Cinzel 400, 124 px, tracking .075em, x 58, top 126, width 661 | The only display type. The part inside the disc is cream |
| Sub-line | "& cocktail bar · Iowa City, Iowa", EB Garamond 500 caps, 13 px, tracking .30em, x 64 / y 276 | Two labels of 3 words each, joined by a middot |
| Column 1 | x 64, y 372, w 300 (name track 214 + price 24), ends y 898 | Cocktails (Classics, House Originals) and Beer (Draft) |
| Column 2 | x 452, y 372, w 300, ends y 882 | Wine (By the Glass, Sparkling), Spirits, Cider |
| Section heads | EB Garamond 500 caps, 14.5 px (10.9 pt), tracking .28em, terracotta `#A6472A` | The only accent outside the disc |
| Sub heads | EB Garamond 500 caps, 11.5 px, tracking .24em, ink-2 `#5B5149` | All 3 words or fewer |
| Item name / price | EB Garamond 500, 17 px = 12.75 pt (53 px in the PNG); price right-aligned in a 24 px track, lining + tabular figures (all digits measured 8.45 px wide) | Title case. Price sits 214 px right of the name start |
| Description | EB Garamond italic, 13.5 px = 10.1 pt, ink-2 | One line, ingredient-first, sentence case |
| Tagline stack | "Good drinks / Good people", 11.5 px caps, tracking .34em, x 64, bottom 62 px | In the quiet bottom-left corner, opposite the terrace |
| Text safe area | all text inside x 64-752, y 126-994 | At least 58 px (0.60 in) from every trim; 0.5 in = 48 px |

Phone (390 CSS px x3 = 1170 wide, 4158 tall): recomposed to one column. The disc is r 110 at (346, 66), and CANTINA is set at 60 px so the disc cuts through the N and A. The sub-line is at 11 px. The items run in one column with a 246 px name track, so prices stay a short hop from the names (17 px names, 14 px descriptions). The 6-step terrace (30 x 18) sits bottom-right and the tagline bottom-left.

Palette: ground `#F3EBDD`, ink `#1E1A17`, ink-2 `#5B5149` (ink at a lighter value, not a second colour), accent `#A6472A`.

## 3. Content decisions (nothing invented)
All 14 items and prices come from the draft. `build.py` asserts that every item is covered.
| Item | Description shown | Source / rule |
|---|---|---|
| Manhattan 15 | Rye whiskey · sweet vermouth · cocktail cherry | Components; Aromatic Bitters hidden (`public_components.aromatic-bitters=false`) |
| Margarita 15 | Tequila blanco · lime · orange liqueur · agave | First sentence of the draft desc; the second sentence ("Bright and citrus-forward") is dropped to keep one line |
| House Daiquiri 14 | White rum · lime · house demerara syrup | Draft desc |
| Brown Butter Old Fashioned 16 | Brown butter-washed bourbon · demerara · bitters | `house_recipe=false`: ingredient names only, no quantities |
| Czech Pilsner 7 | Crisp pale lager | Draft desc |
| Dry-Hopped IPA 8 | Hop-forward | Draft desc with the name echo ("draft IPA") deleted; nothing added |
| Amber Lager 7 | Toasty | Draft desc with the name echo ("amber lager") deleted |
| Malbec 12 / Pinot Grigio 11 | Dry red wine / Dry white wine | Draft desc |
| Brut Rosé 13 | Dry sparkling | Draft desc with the echo "rosé" deleted |
| Blanco Tequila 12, Añejo Tequila 16, Cognac VSOP 18 | (none) | The draft desc only echoes the name, so it is dropped |
| Dry Cider 8 | Sparkling | Draft desc with the echo ("dry … cider") deleted |

Wine prices are shown as a single price with the draft's empty label. No glass or bottle split is claimed beyond the draft's own "By the Glass" sub head.
Spirits sub heads "Agave" and "Brandy" are merged into SPIRITS (see the subtraction log). Items keep draft order, and all stay in Spirits.

## 4. Device inventory (final)
1. Terracotta disc (gesture, part 1)
2. Stepped ink terrace (gesture, part 2)
3. Cream knock-out where CANTINA crosses the disc (this is the collision itself)
4. CANTINA wordmark: the one display word
5. Tracked sub-line (two 3-word labels)
6. Section heads in the accent colour (5)
7. Sub heads in ink-2 (5: Classics, House Originals, Draft, By the Glass, Sparkling)
8. Italic ingredient line
9. Right-aligned tabular price track
10. Tagline stack

Budget check: 1 gesture (one right-hand band), 1 display word, 1 accent colour. There are 0 boxes, 0 leaders, 0 price ornaments, 0 tables and 0 icons. Tracked caps appear only on labels of 3 words or fewer.

## 5. Subtraction log and revision hypotheses (`fix_overdecorated`, `iterate_with_reversion`)
| Round | Hypothesis / change | Primary % | Pri:Sec | Accent % | Verdict |
|---|---|---|---|---|---|
| v1 (before) | Disc r200 at (694,138) cuts I-N-A; 7-step terrace 48x26; 7 sub heads; prices left-aligned 252 px from the name | 11.51 | 2.62 | **10.80** | Accent over budget, and the price hop was too long |
| v2 | Removed the Spirits sub heads "Agave" and "Brandy": the names Tequila and Cognac already carry that grouping, and the page read quieter. Set prices right-aligned in a 24 px tabular track at 206 px. Shrank the disc to r172 | 9.42 | 2.14 | 8.67 | Kept the subtraction; accent still high |
| v3 | Disc r160 at (672,126) | 9.12 | 2.07 | 8.38 | **Reverted.** The disc bottom became nearly tangent to the baseline and half-cut the A's serifs, which read as an accident |
| v4-v5 | Disc r175 moved right so its edge cuts only the A (the N stays clear by about 25 px) | 6.87 | 1.56 | 6.44 | Collision clean. Dominance regressed because the terrace was the secondary blob |
| v6 | Terrace 7 steps to 6 (one step removed) | 6.87 | 2.32 | 6.44 | Dominance recovered |
| v7 | Lifted the wordmark group 60 px and grew the reading layer (names 16 to 17 px, descriptions 13 to 13.5 px) to close the dead top field | 5.79 | 1.95 | 5.40 | Better page fill; dominance dipped |
| v8 (after) | Disc r210 at (835,100); terrace steps thinned to 42x19 (stronger contour-furrow reading, less mass) | **5.93** | **2.71** | **5.55** | Final |

**Ablations I tried and rejected:**
- Removing the tagline stack left the bottom-left corner dead and unbalanced against the terrace.
- Removing the knock-out left ink letters on terracotta at 2.9:1, and the overlap read as a mistake.
- Removing the "Draft" sub head would drop the only mention that the beer is draft.
- Removing "By the Glass" or "Sparkling" would regroup Brut Rosé ambiguously.
- Removing the italic ingredient lines would drop the choice information (`description_supports_choice`).

Removed overall:
- 2 of 7 sub-head labels
- 1 of 7 terrace steps and about 50% of the terrace's area
- 21% of the disc's visible area
- the long price hop

**Disc share:** the disc is the art, so it is the colour field. It measures 5.55% accent area for the whole page, including the section heads, which is inside the 8% budget and inside the refs' 0.4-6% band. The squint test's primary region is the disc (5.93% of the page), 2.7x the next region, which is the terrace. Visually, the wordmark and disc read as one cluster because of the collision, so the top-right is clearly the dominant region. The visual centroid is (0.77, 0.40): upper right, where the gesture lives.

## 6. visual_tests.json (final, `preview-letter.png`)
```json
{"squint_salient_regions": 8, "primary_area_pct": 5.93, "primary_to_secondary": 2.71,
 "ground_luminance": 0.924, "value_range_p5_p95": [0.349, 0.924],
 "accent_area_pct": 5.55, "visual_centroid": [0.765, 0.396]}
```
Before (v1): regions 7, primary 11.51, pri:sec 2.62, accent **10.80**, centroid (0.768, 0.423).

## 7. Legibility and contrast (`contrast.json`, worst pixel behind every text run)
- The lowest reading-text contrast is the terracotta section heads on cream, at **4.99:1**. Descriptions, sub heads, the sub-line and the tagline, all in ink-2, are 6.53:1; names and prices are 14.6:1.
- All reading text sits on plain cream. Nothing overlaps the art except the wordmark.
- The wordmark is display text; inside the disc it is cream on terracotta at 4.99:1.
- Names and prices are 12.75 pt (53 px at 300 dpi), above the 11 pt / 46 px minimum. Descriptions are 10.1 pt, above the 9 pt minimum.

## 8. Files
- `build.py`: builds from the draft, renders both previews, and writes the contrast and layout reports
- `menu.html`: letter version; uses the local fonts in `fonts/` (Cinzel 400; EB Garamond 400, 500 and italic)
- `preview-letter.png` (2550 x 3300), `preview-phone.png` (1170 x 4158)
- `visual_tests.json`, `contrast.json`, `layout.json`

## 9. Open points for the Coordinator
- The echo-trimmed beer, rosé and cider descriptions ("Hop-forward", "Toasty", "Dry sparkling", "Sparkling") are deletions from draft text. If the owner prefers no description to a one-word one, drop them; nothing else changes.
- The fonts were fetched from Google Fonts (OFL) into `fonts/`. The app needs the same families, or the renders will fall back.
