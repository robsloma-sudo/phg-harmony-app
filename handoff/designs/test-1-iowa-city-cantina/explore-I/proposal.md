# TEST-1 explore-I: Night Field (thesis written before any render)

**Thesis:** One gold agave, drawn like a line engraving, rises out of the lower-right corner of a bottle-green night, and everything else stays quiet so that single drawing and the word CANTINA are all you see across the bar.

**Concept words:** night, field, engraved, precise, quiet, gold.

**Avoid-list:** boxes or cards, leaders, price ornaments, tables, icons, a second drawing, stars or moons, cactus or other stamps, papel picado or rótulo costume, taglines about roots or tradition, tracked caps on long labels, hairline serifs at small sizes on the dark ground, a dead lower field.

**The one gesture:** a geometric agave rosette. It is built as radiating, tapered leaf outlines from a single base point below the trim, in one stroke weight and in gold, and cropped by the bottom and right trim.

The thesis, concept words and avoid-list above were written before the first render and have not changed.

## Content (all from `../build/draft_doc.json`; `build.py` asserts every item id and exact price is present)
| Item | Price | Description on the page | Source |
|---|---|---|---|
| Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry | components; Aromatic Bitters hidden (`public_components` false) |
| Margarita | 15 | Tequila blanco · lime · orange liqueur · agave | draft desc, ingredient words only ("Bright and citrus-forward" dropped for the one-line rule) |
| House Daiquiri | 14 | White rum · lime · demerara syrup | draft desc |
| Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon · demerara · bitters | draft desc; `house_recipe=false`, so ingredient names only, no quantities |
| Czech Pilsner | 7 | Crisp pale lager | draft desc |
| Dry-Hopped IPA | 8 | Hop-forward | draft desc minus the echo "draft IPA" |
| Amber Lager | 7 | Toasty | draft desc minus the echo "amber lager" |
| Malbec | 12 | Dry red | draft desc minus "wine" (the section head) |
| Pinot Grigio | 11 | Dry white | same |
| Brut Rosé | 13 | none | "Dry sparkling rosé" only echoes Brut + Sparkling + Rosé, so dropped |
| Blanco Tequila, Añejo Tequila, Cognac VSOP | 12, 16, 18 | none | "... pour." echoes, so dropped |
| Dry Cider | 8 | Sparkling | draft desc minus the echo "dry ... cider" |

`build.py` also asserts that every word of a reduced desc exists in the draft desc, so nothing can be added by hand.

Heads come from the draft: Cocktails (Classics, House Originals), Wine (By the Glass, Sparkling), Spirits (Agave, Brandy) and Cider. Beer's single sub "Draft" is merged into its head as "Draft Beer" (2 words). The only tagline is the neutral "Good drinks / Good people". There is no "Traditional roots" line.

## Layout geometry (letter, 8.5 x 11 in, CSS px at 96/in, rendered at 3.125x to 2550 x 3300 = 300 dpi)
- **Page:** 816 x 1056, flat ground #10291F, no frame.
- **Margins:** 64 px (0.67 in) left and right. Text is inside x 64 to 752 and y 68 to 990, so every line is at least 0.66 in from trim; the nearest is the bottom of the signature, 66 px (0.69 in) from the bottom. Only the agave crosses the trim, with its base point at (664, 1122), 66 px below the bottom trim, and its leaves also run out past the right trim.
- **Grid:** 2 columns x 320 px with a 48 px gutter. The left column is at x 64 to 384 and y 292 to 896: Cocktails, then Draft Beer, then Cider. The right column is at x 432 to 752 and y 292 to 699: Wine, then Spirits. The right column is deliberately shorter, so the agave owns the lower-right field (x 460 to 816+, y about 725 to 1056+). The signature sits at (64, 948) to (181, 990) and balances the agave in the lower-left.
- **Header:** centred, y 78 to 226. "CANTINA" is at y 78 to 170, with "& Cocktail Bar" and "Iowa City, Iowa" below it as two tracked-caps lines of 3 words or fewer.
- **Palette (3 inks plus a tint):**
  - Ground #10291F, bottle green.
  - Reading ink #EFE6D2, ivory.
  - Secondary ink #C9C2AF, ivory tint, for descriptions, sub-labels and the signature.
  - Accent #C8A765, muted gold. It is used only for the wordmark, the 5 section heads and the agave line.
- **Type:**
  - Wordmark: Cormorant Garamond 500, 92 px, tracking .34em, gold.
  - Sub-line: DM Sans 500, 12 px, tracked caps .34em.
  - Section heads: DM Sans 600, 14 px, tracked caps .30em, gold.
  - Sub-labels: DM Sans 500, 11 px, tracked caps .26em.
  - Item names and prices: Source Serif 4 500, 17.5 px (13.1 pt, 55 px at 300 dpi). Prices use tabular lining figures and sit at the right edge of the 320 px column, so the hop is short.
  - Descriptions: Source Serif 4 400, 13 px (9.75 pt), on one line (checked: no overflow).
  - For reverse type there are no italics and no hairline serifs at text sizes. Medium weights are used throughout.
- **Gesture:**
  - 4 rings of tapered lanceolate leaves (3 + 6 + 7 + 4 = 20). Half-width follows t^0.42 (1-t)^1.05, widest at 29% of length. The centreline bends outward by bend·L·t².
  - Each ring is offset half a step from the ring behind it.
  - Every leaf is filled with the ground colour, so front leaves occlude back ones as an engraving would.
  - Each leaf has one midrib, from 6% to 86% of its length.
  - One stroke weight: 1.7 CSS px (5.3 px at 300 dpi, 0.4 pt), gold, round joins.
- **Phone (1170 wide, 390 CSS px at 3x):** one column with 34 px side padding, in this order: Cocktails, Draft Beer, Cider, Wine, Spirits, then the signature. The same agave, recomputed for a 390 x 300 box, closes the page and is cropped at the bottom and right. Names and prices are 18 px, descriptions 13.5 px. Output is 1170 x 4944.

## Contrast (worst pixel behind each text box, text made transparent; from `render_report.json`)
| Role | Min contrast |
|---|---|
| Names and prices | 12.45 |
| Descriptions, sub-labels, sub-line, signature | 8.70 |
| Gold section heads and wordmark | 6.75 |

All roles pass 4.5:1 on both letter and phone. No text sits on the drawing.

## Device inventory and subtraction log
**Revision hypothesis (round 1 to 2):** the page's identity comes from the agave alone. A frame and a rule under the wordmark only repeat the gold and compete with it, so removing them should make the drawing read as the single gesture without leaving the page empty.

| # | Device | Decision | Why |
|---|---|---|---|
| 1 | CANTINA wordmark (the one display word) | keep | Required. It is the only large type. |
| 2 | Two-line tracked sub-line | keep | Required. Each line has 3 words or fewer. |
| 3 | Gold section heads | keep | The accent's only job outside the art. |
| 4 | Ivory sub-labels (Classics, By the Glass, ...) | keep | They carry draft groupings. Removing them would mis-group items. |
| 5 | Agave outlines (the gesture) | keep | The thesis. |
| 6 | Agave midribs | keep | Ablation render without them: the leaves go flat and read as clip-art outlines, not engraving. |
| 7 | Ground fill occlusion in the leaves | keep | Without it, back leaves show through and the drawing tangles. |
| 8 | "Good drinks / Good people" signature | keep | Ablation render without it: a dead lower-left field and a lopsided diagonal. It is neutral brand voice. |
| 9 | Gold double-rule page frame | **removed** | It repeated the gold around the whole page and boxed the composition. The page reads calmer without it. |
| 10 | Short gold rule under the wordmark | **removed** | It added nothing the spacing does not already do. |
| 11 | Engraving veins inside the leaves (2 or 4 per leaf, same weight) | **removed** (tested) | Busier, broken dashes where leaves occlude, and no change in squint salience. |
| 12 | Heavier stroke (2.0 to 2.2 px) | **removed** (tested) | It read coarser and did not change the proxy. Reverted to 1.7 px (best checkpoint). |
| 13 | Sub-label "Draft" under Beer | **removed** | Merged into "Draft Beer". |
| 14 | Descriptions on echo items (4 spirits and wine lines) | **removed** | The rule is "drop, don't rewrite". |

6 of 14 devices were removed (43%, above the 25% target). Every survivor has either an ablation render or a content rule behind it.

## visual_tests (before = with frame and wordmark rule; after = final)
```json
{"file": "preview-letter-before.png", "squint_salient_regions": 0, "primary_area_pct": 0.0, "primary_to_secondary": null, "ground_luminance": 0.142, "value_range_p5_p95": [0.125, 0.312], "accent_area_pct": 1.03, "visual_centroid": [0.483, 0.534]}
{"file": "preview-letter.png", "squint_salient_regions": 2, "primary_area_pct": 0.03, "primary_to_secondary": 1.07, "ground_luminance": 0.137, "value_range_p5_p95": [0.133, 0.309], "accent_area_pct": 1.01, "visual_centroid": [0.477, 0.549]}
```
- **Accent area:** 1.01% (target 8% or less). This is within the references' 0.4 to 6%.
- **Dominant region:** the proxy does not show one (primary 0.03%, ratio 1.07; the two tiny regions are wordmark letters). This is a known limit of the proxy for this image strategy, not a hidden pass:
  - The squint test flags only areas that differ from the ground by more than 0.18 luminance after a 1% blur.
  - A single-weight gold line on dark green covers about 10% of any patch, so it averages out.
  - Calibration: ref-02 panel 3, the reference this direction follows, cropped and upscaled to 2550 px, reports a "primary" of 2% at ratio 37.8. But that region is a 4-px column at the panel's right edge (a grid-crop artifact, located with a labelled squint). Its gold agave does not register either.
  - Making the agave register would need a solid gold mass, which breaks the brief ("one disciplined line drawing, one stroke weight") and the accent budget. I tested veins and a heavier stroke (log 11 and 12). Neither moved the proxy, and both made the drawing worse.
  - Visually, at thumbnail size, the agave is the one gesture. It occupies the lower-right third, is the only drawn element, and pairs with the wordmark on a top-centre to bottom-right diagonal. Reviewers should judge dominance on the render.

## References
- Quality bar: `handoff/designs/references/rob-2026-09-28/ref-02-3acf255d.png`, panel 3 (gold line agave on green, two short columns, gold tracked heads). I followed its grammar but not its cactus, star, top ornament, frame or "Traditional roots" tagline.
- I used no PHG library documents (menu_visual_documents) for this direction, so there are no library document IDs to cite.
- Doctrine: `handoff/designs/DESIGN_THEORY_BRIEF.md`.

## Open items for the Coordinator
- The spirits have no descriptions because the draft only echoes their names. Brand, ABV or pour size from the venue would give them a useful line.
- Wine has no producer or region and has single glass prices, so the `producer · region` / `glass | bottle` format is not used.
- The fonts are bundled in `fonts/` (Cormorant Garamond, Source Serif 4, DM Sans; all OFL). `menu.html` references them by absolute file URI.
