# TEST-1 explore-K1: HILERAS (the field survey)

## Thesis
**Iowa corn and Jalisco agave are both row crops. The menu is one field seen from the air, and every drink is planted in its row.**

- **Concept words:** aerial survey · contour ploughing · hilera · furrow · baseline · oak age · legend.
- **Avoid-list:** cacti, sombreros, papel picado, sun motifs, painted scenes, taglines, boxes and cards, leaders, price ornaments, gradients, texture behind reading text, tracked caps longer than 3 words.
- **The one gesture:** a single aerial field across the top of the front page. Iowa contour strips wrap a knoll and a draw, relax as they come down the page, and lock into straight agave hileras on red Jalisco earth.

## How the structure encodes the concept
### One terrain function makes all the art
`h(x, y) = -y + w(y)·B(x, y)` in `build.py`:
- `-y` is a plane falling down the page.
- `B` is two knolls and one draw.
- `w(y)` fades the relief to zero by y = 150 pt.

Every drawn line is a level line of `h`, extracted with contourpy and written as SVG paths:
- **Strip edges.** Each is one level. Far from the knolls they are straight; near them they bend or close into rings, which is how contour ploughing behaves.
- **Furrows.** The fine lines inside each strip are more levels of the same `h` (5–6 per strip), so they follow the land exactly.
- **Agave hileras.** Rosettes are planted by arc length along the centre level line of every red-earth strip. The upper earth strips are still bent, so their rows ride the contour. Where `w = 0` the same rows run dead straight. That is the "lock": a planted row starts on the Iowa contour and ends as a Jalisco hilera.
- **Palette as system.** Iowa black loam (`#3A2F28`), corn-stubble straw (`#C2A46F`) and a blue-green sod strip sit on the Iowa side. Red Jalisco earth (`#8E4B2F`) carries the blue-green agave. Survey red (`#B3261E`) is used only for prices and the scale bar.

### The ruling of the field is the typographic grid
- Below the hero the furrows continue as straight rules. Each one is drawn at the measured baseline of a row of names: a small script reads the baseline markers after the fonts load.
- **Names sit on the furrow.** The words mask the line, as a label halo does on a map.
- **The wordmark sits on the first furrow.**
- **Each hilera of the front holds three drinks side by side.** Sections are paper strips (fallow ground) separated by a narrow planted hilera (red earth with one row of agave) that runs bleed to bleed. So "every drink is planted in its row" is literal geometry, not a metaphor painted beside a list.

### The back is the spirits survey table
- **It is a Tufte table of the 25 pours.** Columns are class, NOM and region, then an inline oak-age mark on a 0–36 month axis, then the price in a right-aligned column.
- **Each row is a hilera.** It sits on its own furrow rule, and that rule is the guide for the price column.
- **Age marks sit on the furrow**, like plants on the row:
  - blanco and unaged mezcal: a dot at 0;
  - reposado: a bar from 2 to 12;
  - añejo: a bar from 12 to 36;
  - Cognac VSOP (4+ years): an off-scale arrow past 36;
  - mezcal with no age stated: a short dash.
- **The class ranges come from the manifest's own sensory lines** ("2–12 months oak", "1–3 years oak", "4+ years oak", "Unaged"). No age is invented per brand.
- **Gridlines** at 12, 24 and 36 months are hairlines.
- **The class sensory line is printed once** in the group head when it is shared, and on its own line under the row when it differs (the House pours and Ilegal Joven).
- **Head band.** The back opens with the field straightened into hileras: Jalisco rows between Iowa stubble strips.

### Map furniture
- **Front legend:** north arrow; "Contour strips · Iowa"; "Agave hileras · Jalisco"; the proposal key.
- **Back legend:** north arrow; a survey-red scale bar that is the key to the oak axis ("0 12 24 36 months in oak (NOM class)"); unaged dot; "age not stated" dash; the proposal key.
- **Proposal key:** "◦ proposed — pending approval". The mark is a 0.6 pt hairline ring hung in the gutter left of each proposed name, sitting on its furrow like an unplanted site marker. It marks every row whose status is `PROPOSED_needs_rob_approval` or `rob_reference_image`. `approved_db` rows carry no ring.

### Reading layer (item stack, binding)
1. **Name + price.** Newsreader 600, 12 pt. The price is IBM Plex Sans Condensed 500, 11 pt, survey red, tabular figures, about 0.5 em after the name on the same line.
2. **Sensory line.** Newsreader italic, 10.5 pt, warm grey.
3. **Ingredients.** Plex Sans Condensed, 9.5 pt, in exactly the manifest order (which is role order), joined by " · ".
4. **Garnish · glass.** Plex Sans Condensed, 9 pt, led by a glass glyph.

**Glass glyphs** are a coded family drawn only from the manifest's `glass` and `garnish` fields:
- **Glass:** rocks, highball or coupe. Rocks and highball carry an ice cue; the coupe is served up.
- **Garnish cues:** lime wheel, wedge or coin; salt rim (dotted rim); orange peel (curl); cherry; candied ginger on a pick. No garnish means no cue.
- **Liquid colour** only where the ingredients make it obvious:
  - Campari → red (Mezcal Negroni);
  - espresso → dark (Carajillo);
  - Mexican cola → dark (Batanga);
  - rye + sweet vermouth / bourbon → amber (Manhattan, Brown Butter Old Fashioned);
  - every other drink gets a neutral tint.

### Other formats
- **Phone** (1170 px wide, one scroll): its own hero is computed from the same terrain function on a 390 × 262 frame, followed by the wordmark on its furrow. Every drink gets its own full-width furrow. On spirit rows the class, NOM and region form a second line and the oak mark is right-aligned. There is no horizontal scroll.
- **Typography:** two families only, Newsreader (text serif with optical sizes) and IBM Plex Sans Condensed (data). "Cantina" at 64 pt is the only display type. Its sub-line "& Cocktail Bar · Iowa City, Iowa" completes the venue line. There are no taglines.

## KB principle keys used
- `creative_thesis_required`, `concept_before_decoration`: the thesis generated the terrain function, the furrow grid and the table.
- Structure is the concept (handoff §6.4): items sit on the field's own rules; name, price, sensory and ingredients never separate.
- Information design as aesthetic (Tufte: data-ink, micro/macro): the page reads as one aerial image at arm's length, and as exact rows and an oak axis at reading distance.
- `focal_dominance_relative`, `hierarchy_not_everything_loud`, `contrast_is_finite_resource`: one field; everything else is quiet paper and hairlines.
- `accent_requires_scarcity`: saturated colour is concentrated in the field. The reading layer uses ink plus survey red for prices.
- `style_not_costume`, `abstraction_reduces_cliche`, `literal_motif_budget`:
  - Mexico and Iowa appear as systems: agriculture (row crops), geology (loam vs red earth), measurement (survey plate, NOM, oak months).
  - The one literal motif is the agave rosette in plan view, used only as a planting pattern.
- `menu_item_is_unit`, `price_association`, `description_supports_choice`, `case_has_cost` (tracked caps only on labels of 3 words or fewer), `enclosure_strong_grouping` (no boxes), `menu_sections_need_transition` (a planted hilera between bands).

## Precedents (principle only; nothing copied)
- **USGS/USDA aerial survey plates:** the page as a plate with legend, north arrow and scale bar. No plate layout, symbol set or lettering is reproduced.
- **Swiss topographic maps (Imhof):** relief read through ordered level lines and label halos (words mask the lines under them). A quantised hill-shade layer was built and then switched off in the subtraction pass because it muddied the strips; the code keeps it behind a flag (`relief`).
- **Tufte's small multiples and sparkline-style inline data:** the oak-age marks. No specific chart is copied.

## Hard gates (measured; `gates.json`, `_measure.json`)
| Gate | Result |
|---|---|
| Names, prices, ingredients vs manifest.json (DOM text diff) | **PASS**. 50/50 items on letter and 50/50 on phone. No extra or missing items. Prices, sensory lines, ingredient strings, garnish, glass, class, NOM, region and oak class all match exactly. The proposal ring appears on exactly the non-`approved_db` rows. Manifest sha256 prefix `6bd0338296207153`. |
| Price within 1 em on the same line, or an aligned column with a guide | **PASS**. The 25 inline rows on letter have a maximum gap of 0.544 em (Czech Pilsner), all on the same line. On phone the maximum is 0.444 em. The 25 table rows have a right-edge spread of 0.00 px, each with a furrow guide. |
| WCAG contrast at the worst pixel, at least 4.5 | **PASS**. The minimum is 5.70 on the front (80 text elements), the back (190) and the phone (260). In each case it is the survey-red price on paper. The wordmark is included. Method: text-free render, ink box +2 px, every pixel. |
| Legibility at actual size | **PASS**. The smallest letter text is 8.5 pt (legend and table heads). Body text is 9–12 pt. The smallest phone text is 13 px. |
| Ingredients in role order; garnish separate | **PASS**. Ingredients print in manifest order. The garnish is its own element on the serve line and never sits inside the ingredient line. |
| No taglines or banned filler | **PASS**. There are 0 hits against the banned list. The non-item strings are only the section heads, the wordmark, the venue sub-line, the legend and the table heads. |
| Text inside the 0.5 in safe area | **PASS**. Text ink margins are 36.72 L / 36.24 R / 37.92 B pt on both pages; the top ink is at 206.6 pt (front) and 82.1 pt (back). The menu clears the legend by 17 pt (front) and 8 pt (back). |
| Bleed PDF, 3.175 mm | **PASS**. 2 pages, each 666 × 846 pt: trim + 9 pt bleed + 18 pt slug, with crop marks. The art and the paper fill the bleed band (100% non-white on both pages). |
| Formats | Front and back are 2550 × 3300 each. The phone render is 1170 × 15342, with a scroll width of 390 css px. |

The proposal rings are non-text key marks. They hang 9.5 pt left of the names, which puts them 27.5 pt from trim: inside trim, but outside the text margin.

## visual_tests.json
| Page | Primary area | Primary : secondary | Accent | Salient regions |
|---|---|---|---|---|
| Front | 26.3% | **13.6** | **12.1%** (inside the field) | 8 |
| Back | 9.3% | n/a (one region only) | 6.1% | 1 |

- **Front** sits inside the 11–17 target band of Glass Garden / Solstice. Its accent is in the gesture, not the reading layer.
- **Back** is the data page. The top hilera band is its only salient region, and the table stays quiet.
- **Silhouette correlation.** Front against back is 0.54. Against the interim explore-K2 renders it is −0.22 (front) and −0.33 (back).

## Open questions and caveats
- **Proposals.** Every ring-marked row still needs Rob's approval. The four mezcal prices are placeholders in the manifest, and the manifest's `note` fields are not printed.
- **Oak marks** encode NOM-006 class ranges, not per-brand ageing. The legend says "(NOM class)".
- **Pour size.** The manifest says the 1.5 oz pour is "proposed … not established", so it is not printed.
- **Print vs screen wrapping.** The PDF lays out text marginally wider than the screen renders do. The column ratio was set so that no name wraps and prices stay on the name line in both. A few ingredient lines break at a different word in the PDF.
- **Dependencies.** `build.py` needs `contourpy`, `pymupdf` (for the PDF bleed check) and Playwright/Chromium. The fonts (Newsreader, IBM Plex Sans Condensed; OFL) are local in `fonts/`.
