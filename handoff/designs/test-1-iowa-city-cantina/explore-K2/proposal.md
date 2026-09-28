# TEST-1 explore-K2: "EL RELOJ" (the sun clock)

Brief: `expanded-v1/CONCEPT_BRIEF.md`, direction K2. Content is `expanded-v1/manifest.json` (sha256 prefix `6bd0338296207153`). No name, price or ingredient is changed, and no item is added.

## Thesis
**A cantina runs on the sun. The menu is one evening, from 5 pm to 2 am, and every drink sits at its hour.**

- **Concept words:** evening · dial · rim · graduation · dusk · months in oak · night.
- **Avoid-list:** the Aztec sun stone (not quoted), a sun disc sticker, sombreros, cacti, papel picado, starbursts, rotated text, boxes/cards, leaders, taglines, random decorative stars.
- **The one gesture:** the rim of one great circle, with the dusk outside it.

## How the structure encodes the thesis

### Front: the evening
- **One great circle.** The circle's centre is off the left trim, at (−84, 445) pt, with a radius of 590 pt. Its rim is the only large shape on the page. Outside the rim is the dusk field. The field's colour at any height is the colour of that hour. It is interpolated in OKLab from warm paper (afternoon) to gold (5 pm), copper (7), rose (8–9), violet (11) and indigo (2 am).
- **Graduation = time.** The evening is linear down the page: one hour is 62 pt. The rim carries 109 radial ticks, one every 5 minutes from 5 pm to 2 am, with longer ticks at the quarter hours and hour ticks that cross the rim.
  - Every tick points at the circle's centre, so the hour lines fan like a dial's.
  - Hour numerals sit in the field on their hour lines.
  - The ink of each numeral (ink or paper) is chosen by the field colour under it.
- **Clusters sit at their hour.** Each cocktail cluster's name row sits on its hour line, and the gold inner tick points at it.
  - Each block is pushed against the rim at its own height: block left = rim x at that hour, minus the 28 pt gap, minus the block width.
  - As the rim bows outward toward 9–10 pm and back, the blocks step right, then left: 36 → 66 → 88 → 103 → 110 → 106 → 94 pt.
  - So the reading path is the arc of the evening.
  - All text is horizontal.
- **Zero proof** hangs from the midnight line (reason below). The key and a one-line note sit at 2 am.
- **Glass glyphs** are a coded family drawn only from the manifest's glass and garnish fields:
  - **Glasses:** rocks, highball and coupe.
  - **Ice cue:** cubes in rocks and highball glasses. A coupe has none (served up).
  - **Garnish cues:** wheel, wedge, salt dots, peel twist, cherry, coin, and a ginger cube on a pick.
  - **Liquid colour** appears only where the ingredient makes it obvious: Campari (red), espresso and Mexican cola (dark). Everything else is a neutral tint.

### Back: the night
- **The page is the night.** The ground runs from dusk indigo at the top to near-black at the bottom.
- **The ladder.** A gold ruler of **months in oak on a log scale**, ln(1+m), with a tick for every month from 0 to 48 and labels at 0, 1, 2, 3, 6, 12, 24, 36 and 48.
  - The scale is logarithmic for two reasons. The classes differ by ratio (2, 12, 36, 48 months). And a linear scale would crush the 0–2 month class, which holds 12 of the 25 pours.
  - Star magnitudes are logarithmic too, which fits the chart.
- **Class ranges from the manifest sensory lines:**

  | Class | Mark | Age |
  |---|---|---|
  | Blanco | a point | 0 ("Unaged") |
  | Reposado | a bar | 2–12 months |
  | Añejo | a bar | 12–36 months |
  | Cognac VSOP | open-ended below its rung | 48 months ("4+ years") |
- **Rungs.** Each class sits on the rung at its minimum age, so blanco is at dusk (top) and añejo and cognac are deep in the night.
- **Stars = Iowa.** Star area is proportional to the manifest's `iowa_accounts`, the number of Iowa accounts pouring the brand.
  - "+" means the brand graph has no count.
  - An outline square marks a house pour (no brand).
  - The second line of each pour row is its star-catalogue designation: NOM number and region, only where the manifest has them.
- **Class sensory** prints once per class in the head. Ilegal Joven has its own sensory line, which is printed under its row.
- **Beer, cider and wine** sit below the chart, off the oak axis, separated by a rule.

### Phone (1170 px, one scroll)
- **Hero:** the same rim and gradient, cropped to the top-right corner behind the wordmark.
- **Evening:** the arc is unrolled into a rail. Each hour row carries its own slice of the dusk gradient and its numeral, with the cluster to the right.
- **Night:** the same classes on a dark ground, each with its month range in gold, then beer, cider and wine.

## Hours: PHG-inferred service suggestion (not manifest data)
The hours are PHG's suggestion of when each drink suits best. They are not a schedule. The menu says so in one line: "Each drink is set at the hour it suits: a suggestion, not a schedule."

| Hour | Drinks | Why |
|---|---|---|
| 5 pm | Ranch Water, Paloma | Long, carbonated, low-intensity highballs. The after-work, first-light aperitivo round. |
| 6 pm | Batanga, House Daiquiri | Still sharp and appetite-opening: a cola highball and a crisp, short sour before food. |
| 7 pm | Margarita, Spicy Pineapple Margarita | Dinner service. Acid and chile heat are built for food (brief: "dinner (Margaritas…)"). |
| 8 pm | Mezcal Negroni, Loess | Smoke and bitterness mid-dinner. The Negroni is the brief's dinner stirred drink. Loess is a honeyed smoky sour (Penicillin structure) that bridges into the evening. |
| 9 pm | Manhattan | The first spirit-forward stirred drink, after the plates are cleared. |
| 10 pm | Milpa Old Fashioned, Brown Butter Old Fashioned | Rich, stirred, sipping nightcaps (brief: "after dinner (… Old Fashioneds)"). |
| 11 pm | Carajillo | Espresso digestif: the coffee course, the last cocktail of the arc. |
| 12 am | Sin alcohol · Zero proof | The turn toward the drive home. These drinks are also on offer all evening. This is the least certain placement; the alternative is to set them off-scale. |
| 12–2 am | (the arc continues: the night is overleaf) | The spirits on the back. |

**Mezcal on the oak axis.** Mezcal is placed on the 0-month rung, which is also a PHG inference. All four pours are sold as jóvenes (unaged). The manifest states "Unaged" only for Ilegal Joven. **Verify before print.**

## KB principle keys used
- `creative_thesis_required`, `concept_before_decoration`: the thesis sets the geometry, block positions and colour.
- `structure_is_the_concept` (handoff §6.4): items sit on hour lines against the rim, and the stack never separates.
- Tufte (data-ink, micro/macro): at arm's length the page is one image; up close every mark is data (5-minute ticks, the log month ruler, star area = Iowa accounts).
- `focal_dominance_relative`, `hierarchy_not_everything_loud`, `accent_requires_scarcity`: one dominant field. Accent (gold/copper) lives in the gesture. The reading layer uses ink, one muted ink and a gold-brown price.
- `abstraction_reduces_cliche`, `literal_motif_budget` (0 literal motifs, since the sun is only colour and time), `style_not_costume`.
  - Mexico enters as a system: the NOM-006 age classes and the NOM designations.
  - Iowa enters as a system: its account counts as star magnitudes.
- `menu_item_is_unit`, `price_association`, `case_has_cost`: tracked caps are used nowhere. Prices sit 0.42 em after the name.

## Precedents (principle only; nothing copied)
- **Astronomical instruments and volvelles:** a graduated rim read against a fixed index.
- **Herbert Bayer's diagrams:** colour carries a quantity.
- **Star atlases:** magnitude drawn as dot area, and catalogue designations beside names.
- **Slide rules:** log graduation.
- **The Aztec sun stone:** used only for the idea that a calendar can be the structure. No form, glyph, ring pattern or face is quoted.

## Hard gates (measured by `build.py` → `gates.json`)

| Gate | Result |
|---|---|
| Names/prices/ingredients vs manifest (DOM diff: letter and phone) | **PASS.** 50/50 items, 0 errors, 0 missing, 0 duplicates. Garnish, glass, sensory and the proposed mark are also checked. |
| Price within 1 em, same line | **PASS.** Max gap 0.42 em, all on the name line (letter and phone). |
| WCAG worst-pixel contrast ≥ 4.5 (text-free re-render, every pixel under each text line's ink box) | **PASS.** Front min 5.04 (the "8" numeral on the rose field). Back min 6.66. Phone min 5.06. |
| Legibility | **PASS.** Letter minimum 8.5 pt (front and back). Phone minimum 12 px. |
| Ingredient role order; garnish separate | **PASS.** Printed lists equal the manifest's role-ordered lists. Garnish and glass are a separate italic slot. |
| No taglines / banned lines | **PASS.** None found. |
| 0.5 in safe area | **PASS.** Front text box 36–556 × 37.5–747 pt. Back 36–575 × 36–755 pt. |
| Bleed PDF | **PASS.** `menu-print-bleed.pdf`: 2 pages at 666 × 846 pt (trim + 9 pt / 3.175 mm bleed + 18 pt slug), with crop marks. The art is drawn 9 pt past trim on all sides. |
| Formats | Front and back PNGs are 2550 × 3300. Phone is 1170 wide with no horizontal scroll. All text is live HTML. The art is inline SVG with no raster. |
| Text overlaps / text entering the dusk field | None. |

The proposed key "◦ proposed — pending approval" is a 0.6 pt hairline ring after the price. It appears on both pages and on the phone.

## visual_tests.py

| Page | Primary area | Primary : secondary | Accent area | Squint regions |
|---|---|---|---|---|
| Front | 18.6% | 192 | 15.5% | 5 |
| Back | 0 | none | 39.9% | 0 |

- **Front:** one field wins outright. Its dominance is higher than in the Glass Garden/Solstice references (11–17). The accent sits in the gesture, not in the reading layer.
- **Back:** the dark ground *is* the median, so no region stands out at a squint.
- **Back accent (39.9%):** this is the saturated indigo ground registering as "accent". It is not accent ink; gold covers only a few percent.
- **Silhouette correlation, front vs back:** 0.27.
- **Silhouette correlation, K2 vs K1 and K3** (run on the renders present at the time): front −0.22 and −0.04, back −0.33 and −0.36. All are below 0.5.

## Open questions for Rob
1. Are the hours acceptable as a guest-facing suggestion, or should they be moved into staff notes?
2. Zero proof: keep it at midnight, or move it off the scale?
3. Mezcal: confirm the unaged class for all four pours.
4. Iowa-accounts stars: guest-facing, or staff-only?
