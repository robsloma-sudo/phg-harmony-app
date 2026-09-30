# TEST-1 · Direction G "Monument" (type-as-image)

Status: exploration for the Coordinator. Not submitted, not committed.
Content source: `../build/draft_doc.json` (revision 3). Build: `python3 build.py` (after) and `python3 build.py --variant before`.

## 1. Thesis (written before code)
**Thesis:** The name works as the sign. CANTINA stands the full height of the page, too big for the sheet and cropped by
its edge, so everything else (the list, the place line, the tagline) can stay small, plain and quiet beside it.

**Concept words:** monument · upright · cropped · quiet list · two inks · one red

**The one gesture:** the wordmark CANTINA, set vertically along the right edge. It reads top to bottom with the letter
tops facing the trim, runs the full page height and is cut by the trim on three sides.

**Avoid-list:** boxes or cards around sections · leaders · price ornaments, badges or starbursts · tables · icons,
agave/sun/cactus stamps or any illustration · tracked caps on anything longer than 3 words · item names in caps · a
second display word · accent colour anywhere except section heads · fake texture or grain · invented venue facts
(no "est.", no origin or process claims) · rótulo, riso or brutalist costume.

Every device below traces to the thesis. The monument is the sign. The small labels are the quiet signature beside it.
Red marks only where to start reading.

## 2. Content integrity (every item, exact prices, nothing invented)
14 items, 5 sections, all in draft order (left column: Cocktails, Beer; right column: Wine, Spirits, Cider).

| Item | Price | Description on menu | Source / rule |
|---|---|---|---|
| Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry | components; Aromatic Bitters hidden (`public_components.aromatic-bitters=false`) |
| Margarita | 15 | Tequila blanco · lime · orange liqueur · agave | existing desc ingredient terms; the tasting sentence "Bright and citrus-forward." was dropped to keep one ingredient-first line |
| House Daiquiri | 14 | White rum · lime · demerara syrup | components, named as in the existing desc |
| Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon · demerara · bitters | `house_recipe=false`: ingredient names only (the existing desc terms), no quantities |
| Czech Pilsner | 7 | Crisp pale lager | existing desc |
| Dry-Hopped IPA | 8 | Hop-forward | existing desc minus the echo "draft IPA" |
| Amber Lager | 7 | Toasty | existing desc minus the echo "amber lager" |
| Malbec | 12 | Dry red | existing desc minus "wine" (the section head already says Wine) |
| Pinot Grigio | 11 | Dry white | existing desc minus "wine" |
| Brut Rosé | 13 | (none) | "Dry sparkling rosé" only repeats the name and the Sparkling sub head, so it was dropped |
| Blanco Tequila | 12 | (none) | "Blanco tequila pour." is an echo, so it was dropped |
| Añejo Tequila | 16 | (none) | "Añejo tequila pour." is an echo, so it was dropped |
| Cognac VSOP | 18 | (none) | "VSOP Cognac pour." is an echo, so it was dropped |
| Dry Cider | 8 | Sparkling | existing desc minus the echo "dry … cider" |

Heads come from the draft: Cocktails (Classics, House Originals), Beer (Draft), Wine (By the Glass, Sparkling), Spirits
(Agave, Brandy), Cider. The only merge: Beer's single sub "Draft" rides on the Beer head line. All three beers are draft,
so every item stays in its group. The draft title "Bar menu" and subtitle "PHG Publishing Beta · Test Content" are not
printed. The wordmark, sub-line and tagline follow the direction brief.
Content question for the Coordinator: "Hop-forward", "Toasty", "Dry red", "Dry white" and "Sparkling" are trimmed
remainders of the existing descriptions. If Rob would rather have none than one-word descriptors, set them to none;
the layout re-flows automatically.

## 3. Device inventory and subtraction log

### Round 1: before (`preview-letter-before.png`, variant `before`)
Devices: (1) CANTINA monument at natural tracking · (2) two-line tracked sub-line · (3) red dot mark after
"& cocktail bar" · (4) 96 px hairline rule under the sub-line · (5) red section heads · (6) grey tracked sub heads on
their own rows (7 of them, including Beer / Draft) · (7) "Bar menu" folio at the foot · (8) "Good drinks / Good people"
tagline stack.

Before that, there was a round 0 fix (a geometry bug, not a device change). The first League Gothic monument covered
the right column, hid the prices 12 and 18, and its 14% crop removed the T crossbar. The fix: switch to Oswald 700 (the
same family as the labels), whose wider set gives a narrower cap band at full page height, and reduce the crop to 7%.

### Subtraction pass (8 devices, 3 removed = 37%, plus one sub row merged)
| Device | Kept? | Why |
|---|---|---|
| Monument | kept | the thesis |
| Sub-line (2 lines ≤3 words each) | kept | required; it names the venue type and place without breaking the tracked-caps rule |
| Red dot mark | **removed** | it made a second red point competing with the section heads, and removing it cost nothing |
| Hairline rule | **removed** | it was a divider with nothing to divide; the space below the sub-line already separates |
| Section heads in red | kept | the only accent; they are the reading entry points |
| Sub heads | kept (6 rows), Beer/Draft merged onto the head line | data groups; one-item-group rows were costing vertical rhythm |
| "Bar menu" folio | **removed** | it restated the obvious and fought the tagline for the quiet corner |
| Tagline stack | kept | required signature in the quiet bottom-left corner |

### Round 2 hypothesis: the squint test sees 7 regions because each letter of the monument is its own blob
The fix was to tighten the monument's tracking so it reads as one mass at distance. Result at -0.03 em: 3 regions,
ratio 1.61. **Round 3** at -0.05 em: 2 regions, ratio 2.04, and the letters are still cleanly separated at full size.
Kept as the best checkpoint. No criterion regressed: accent, value range and contrast are unchanged.

### visual_tests numbers, before → after
| metric | before | after (final) | target |
|---|---|---|---|
| squint_salient_regions | 7 | **2** | one dominant |
| primary_area_pct | 3.84 | **16.96** | — |
| primary_to_secondary | 1.03 | **2.04** | clearly dominant |
| accent_area_pct | 0.14 | **0.13** | ≤ 8 |
| value_range_p5_p95 | 0.096–0.908 | 0.096–0.908 | — |
| visual_centroid | 0.804, 0.501 | 0.797, 0.502 | — |

`visual_tests.json` (final):
```json
{"file": "preview-letter.png", "squint_salient_regions": 2, "primary_area_pct": 16.96, "primary_to_secondary": 2.04,
 "ground_luminance": 0.897, "value_range_p5_p95": [0.096, 0.908], "accent_area_pct": 0.13, "visual_centroid": [0.797, 0.502]}
```
Final device count: 1 gesture · 1 display word · 1 accent · 0 boxes · 0 leaders · 0 price ornaments · 0 tables · 0 icons.

## 4. Layout geometry (CSS px at 96/in; x3.125 = print px at 300 dpi). Full per-element boxes are in `geometry.json`.
- **Page:** US letter 816 x 1056 (8.5 x 11 in), rendered at 2550 x 3300. Ground PAPER #EFE7D8.
- **Margins:** 56 px (0.58 in) left, top and bottom for all text. The only element past the margins is the monument.
- **Grid:** two columns, 262 px + 36 px gutter + 170 px, x = 56–318 and 354–524. The text zone ends at 524 (64% of the
  width). The monument's visible edge is at x = 557.8, a 33.8 px (0.35 in) clear channel. Both column tops sit at y = 190.
  Prices are right-aligned at each column's edge (x = 318 and 524), a short hop within a short measure.
- **Vertical rhythm:** one unit u = 24.67 px drives item spacing. The section gap is 2.6u = 64.1 px. u was solved so
  the longer column ends 64 px above the tagline (right column ends at y = 894; the tagline starts at y = 958).
  Section heads: Cocktails y=190, Beer 601.8, Wine 190, Spirits 517.8, Cider 807.8.
- **Monument:** Oswald 700, "CANTINA", font-size 334.5 px, tracking -0.05 em, set to a text length of 1081.3 px
  (page height + 1.2% overshoot at top and bottom, y = -12.7 to 1068.7), rotated 90°. The baseline is at x = 557.8, and
  the cap height of 277.6 px is cropped 7% (19.4 px, 5.1 mm) past the right trim. Ink #1B1815.
- **Head (sub-line):** x 56, y 56–98. Oswald 500, 12 px (9 pt), tracking .34 em. "& COCKTAIL BAR" in ink, "IOWA CITY, IOWA" in INK2.
- **Tagline:** x 56, y 958–1000. Oswald 500, 12 px, .34 em, INK2. "GOOD DRINKS / GOOD PEOPLE".
- **Type:**
  - Section heads: Oswald 500, 15 px (11.25 pt), .30 em, CHILE.
  - Sub heads: Oswald 500, 12 px (9 pt), .30 em, INK2.
  - Names: Newsreader 500, 18 px (13.5 pt, 56 print px), title case, INK.
  - Prices: Newsreader 500, 18 px, lining and tabular figures, INK.
  - Descriptions: Newsreader italic, 13 px (9.75 pt), sentence case, one line, INK2.
- **Palette:** PAPER #EFE7D8 · INK #1B1815 · INK2 #4D453D (a lighter value of the same ink) · CHILE #9B2D1F (section heads only).
- **Contrast on paper (flat ground, no art behind any text):** INK 14.39:1 · INK2 7.65:1 · CHILE 6.13:1. All are ≥ 4.5:1.
  The monument never sits behind text; the build checks for any text within 24 px of it and found none.
- **Checks run by build.py:** no name row wraps, no description exceeds one line or its column, no text inside the
  0.5 in trim margin, no text near the monument. All passed (`problems: []`) for letter and phone.
- **Phone (390 css px, x3 = 1170 x 4143):** one column with 28 px side margins. The monument turns horizontal as a
  full-width CANTINA at the top (font-size 114 px), with the letter tops cropped 6% by the top trim: the same crop logic
  as the letter. Then come the sub-line, the sections in draft order (item rows capped at 300 px so prices stay near
  names; section gap 36 px) and the tagline.

## 5. Production notes
- The monument geometry already extends past the trim at the top (3.4 mm), bottom (3.4 mm) and right (5.1 mm).
  A bleed PDF only needs a wider canvas, and no art has to change. This round rendered only the trim previews.
- Fonts are local files in `fonts/` (Oswald 500/700, Newsreader 400/500/400i, SIL OFL). `menu.html` references them
  by absolute file:// URI.
- There is no raster art layer. Type-as-image needs no Canva commission.

## 6. References
- Quality bar: `references/rob-2026-09-28/ref-02-3acf255d.png` (panel 4 gives the vertical cropped CANTINA with the
  quiet two-column list; all panels give red tracked section heads and the "GOOD DRINKS / GOOD PEOPLE" corner stack)
  and `ref-01-98c65abe.png` (a giant vertical wordmark carrying the page while the list stays small).
- Library (read-only gateway, log_id 208): document **572** (COA Cantina Iowa City), **7923** (COA Cantina, Des Moines),
  **2368** (Skinny's Cantina), **2929** (Chano's Cantina). I checked these for list structure only: cocktails lead, then
  beer, then spirits. No content was taken from them.

## 7. Risk flags
- `trimmed_descriptions`: the five one-word or two-word descriptors in section 2 need the Coordinator to confirm.
- `sample_content`: the draft items are flagged `sample_content: true` (beta seed).
- `no_bleed_file_this_round`.
