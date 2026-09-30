# TEST-1 explore-J "Horizon"

## Thesis (written before code)
**A cantina at dusk on a flat Iowa horizon: one line where the sky ends and the quiet reading room begins.**

Concept words: horizon · dusk · flat · still · open · measured

Avoid-list: sun/moon discs, agave, cacti or any drawn motif; smooth gradients or glow; boxes, cards, rules, leaders and
price ornaments; tracked caps on anything longer than 3 words; a second display word or a tagline banner; two-column
list look (G/H/I); accent colour below the horizon (except indigo heads).

The one gesture: the posterised dusk field (upper 29% of the page, three hard-edged flat bands). The one display word:
CANTINA, reversed out of the indigo.

## Structure (differs from G/H/I)
Page split by one horizontal line (amber band bottom edge, y = 303 css px = 947 px at 300 dpi).
Below it, one centred cadence: COCKTAILS (single centred column, measure 520 css px) → space → a quiet three-up row
(Draft Beer + Cider / Wine / Spirits). A single column cannot hold all 14 items at 11 pt+ (needs ~1060 css px vs 650
available), so the brief's two-tier fallback is used.

## Layout geometry (letter, 816 x 1056 css px = 2550 x 3300 at 300 dpi; 1 css px = 0.75 pt)
- Field (ART layer, CSS, text-free): indigo `#1E2147` y 0-236, plum `#5A2B4F` y 236-286, amber `#D98A2E` y 286-303;
  full width; in print the field bleeds 3 mm past the top, left and right trim.
- Wordmark: CANTINA, Fraunces 420, opsz 144, 104 px (78 pt), tracking 0.2em, paper `#F4EDE1`, centred, top y 74.
  Glyph extent x ≈ 135-683.
- Sub-line: "& cocktail bar · Iowa City, Iowa", DM Sans 400, 12.5 px (9.4 pt), tracking 0.24em, mixed case (6 words, so
  not caps), `#E9E1D6`, centred, y 200.
- Reading area: x 72-744 (0.75 in side margins), y 352-1004 (bottom margin 52 px = 0.54 in). Flex column, space-between.
- Cocktails: centred column x 148-668 (520 wide), y 352-655.
- Three-up row: y 715-1004; columns 224 wide at x 72 / 296 / 520 with 10 px inner padding (text boxes 204 wide at
  x 82 / 306 / 530). Column heights: 289 / 245 / 182, top-aligned.
- All text ≥ 82 css px (0.85 in) from the side trim and ≥ 52 px (0.54 in) from top/bottom text edges; wordmark 74 px from top.
- Type: section heads DM Sans 600 12.5 px (9.4 pt) tracked 0.3em caps, indigo; sub heads Fraunces italic 400 15 px
  (11.25 pt) `#5B5058`; names and prices Fraunces 500 18.5 px (13.9 pt = 58 px at 300 dpi), ink `#221C22`, tabular
  lining figures, price 0.62em after the name on the same line; descriptions DM Sans 400 13 px (9.75 pt) `#5B5058`.
- Palette: 3 dusk inks (field only) + paper + ink + muted ink; indigo reused only for the 5 section heads.
- Phone (390 css / 1170 px): same field (150/46/15), wordmark 52 px, everything stacked in one centred column, 28 px sides.
- Per-element boxes: `geometry.json`; per-text-run contrast and sizes: `contrast.json`.

## Content decisions (all from ../build/draft_doc.json; nothing invented)
| Item | Price | Description used | Source / rule |
|---|---|---|---|
| Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry | components; aromatic bitters hidden (public_components false) |
| Margarita | 15 | Tequila blanco · fresh lime juice · orange liqueur · agave syrup | components |
| House Daiquiri | 14 | White rum · fresh lime juice · demerara syrup | components |
| Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon · demerara syrup · aromatic bitters | components, names only (house_recipe=false) |
| Czech Pilsner | 7 | Crisp pale lager | desc |
| Dry-Hopped IPA | 8 | Hop-forward | desc minus name echo ("draft IPA"; sits under Draft Beer) |
| Amber Lager | 7 | Toasty | desc minus name echo |
| Malbec | 12 | Dry red wine | desc |
| Pinot Grigio | 11 | Dry white wine | desc |
| Brut Rosé | 13 | Dry sparkling | desc minus name echo |
| Blanco Tequila | 12 | (none) | desc was a pure echo, dropped |
| Añejo Tequila | 16 | (none) | pure echo, dropped |
| Cognac VSOP | 18 | (none) | pure echo, dropped |
| Dry Cider | 8 | Sparkling | desc minus name echo |

Heads: Cocktails (Classics, House Originals), Draft Beer (Beer's single sub "Draft" merged into the head), Cider,
Wine (By the Glass, Sparkling), Spirits (Agave, Brandy). Every item stays in its draft group. No quantities anywhere.
Open content gaps (for the Coordinator, not blocking): no producer/region/ABV for wine, beer, cider; no pour size or brand
for spirits; spirits have no sourced description.

## Device inventory and subtraction log
Revision hypothesis: the page is already structurally quiet; the risk is small ornaments creeping back in around the
reading layer and a field whose middle band reads as a flag stripe rather than a horizon. Subtract the ornaments,
re-proportion the field so the indigo sky dominates and the plum/amber sit low like a horizon.

| # | Device (before) | After | Why |
|---|---|---|---|
| 1 | Dusk field, 3 hard bands | kept, re-proportioned 214/78/25 → 236/50/17 | the gesture; plum band at 78 px read as a stripe, not a horizon |
| 2 | CANTINA wordmark | kept (moved to y 74 to sit centred in the taller indigo) | the one display word |
| 3 | Tracked mixed-case sub-line | kept | identifies venue/city; removing it leaves the wordmark unexplained |
| 4 | Indigo tracked section heads | kept | only way sections are separated (no boxes) |
| 5 | Italic serif sub heads | kept | carry the draft's sub groups; removal would mis-group Sparkling/Brandy |
| 6 | Middot ingredient separators | kept | quieter than commas at centred measure |
| 7 | Amber dash under COCKTAILS | **removed** | accent leaking below the horizon; competes with the amber band |
| 8 | Indigo hairline between tiers | **removed** | it collided with the Old Fashioned line; space does the job |
| 9 | Vertical hairlines between the three columns | **removed** | table feel; centring + gutters already separate them |
| 10 | "Good drinks · good company" footer tagline | **removed** | a second voice below the list; row now ends on the margin, so no dead field |

Removed 4 of 10 devices (40%, above the 25% target). No criterion regressed, so nothing was reverted: contrast minimum
unchanged at 6.6:1, name/price size unchanged, the page still fills to the bottom margin (items end at y 1004 vs the
1004 limit), and the tiers now have a 60 px gap instead of touching.

## visual_tests (python3 ../../tools/visual_tests.py)
The field is the art and the colour, so whole-page accent share is dominated by it. **Accent share excluding the field
(below-horizon crop): 0.00% before, 0.00% after** (the indigo heads are too small/dark to register as saturated; the removed
amber dash was also below the tool's detection size). Whole page: 28.57% before → 27.44% after (field area shrank slightly
from 30.0% to 28.7% of the page). One dominant squint region (the field): 29.73% → 28.57% of the page, no secondary region.
before/after silhouette correlation 0.996 (same structure, as intended).

```json
[
 {
  "file": "preview-letter.png",
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
  "file": "preview-letter.png",
  "squint_salient_regions": 1,
  "primary_area_pct": 29.73,
  "primary_to_secondary": null,
  "ground_luminance": 0.916,
  "value_range_p5_p95": [
   0.138,
   0.932
  ],
  "accent_area_pct": 28.57,
  "visual_centroid": [
   0.497,
   0.178
  ]
 },
 {
  "file": "after: below-horizon crop (y>=950px).png",
  "squint_salient_regions": 0,
  "primary_area_pct": 0.0,
  "primary_to_secondary": null,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.816,
   0.932
  ],
  "accent_area_pct": 0.0,
  "visual_centroid": [
   0.478,
   0.533
  ]
 },
 {
  "file": "before: below-horizon crop (y>=997px).png",
  "squint_salient_regions": 0,
  "primary_area_pct": 0.0,
  "primary_to_secondary": null,
  "ground_luminance": 0.932,
  "value_range_p5_p95": [
   0.795,
   0.932
  ],
  "accent_area_pct": 0.0,
  "visual_centroid": [
   0.479,
   0.524
  ]
 }
]
```

## Contrast and legibility (contrast.json, worst pixel behind each text run)
Letter: minimum 6.6:1 (muted descriptions and sub heads on paper); names/prices 13.9 pt; descriptions 9.75 pt; section
heads 9.4 pt; wordmark paper on indigo ≈ 13:1. Phone: minimum 6.6:1; names 17.5 css px. On the phone the two longest
cocktail descriptions wrap to two centred lines (Margarita, Old Fashioned); letter keeps every description on one line.

## References
Quality bar: handoff/designs/references/rob-2026-09-28/ref-02-3acf255d.png (panel 2: tracked serif CANTINA, quiet short
lists, section heads as the only accent) and ref-03-ffe03c52.png (panels 2 and 5: posterised dusk colour field as the art,
reading layer small and plain beneath). No new library (menu_visual_documents) queries were made in this round; cite
the comparables from the round-17 proposal if the Coordinator files this.

## Files
build.py (`python3 build.py [before|after]`), menu.html, preview-letter.png (2550x3300), preview-phone.png (1170 wide),
before/ (pre-subtraction renders + contrast), visual_tests.json, contrast.json, geometry.json.
