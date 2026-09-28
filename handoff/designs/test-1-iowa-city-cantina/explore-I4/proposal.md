# TEST-1 explore-I4: Night Field, round 4 (built from I2; I2 and I3 kept as checkpoints)

**Thesis:** One gold-engraved agave rosette, fleshy and cupped, rises from the lower-right corner of a bottle-green night. Everything else stays quiet so the plant and the word CANTINA carry the page.

**Concept words:** night, engraved, rosette, fleshy, quiet, gold.

**Avoid-list:**
- waves or water lines, and converging ray furrows
- sail-like flat blades
- a second drawing
- boxes, leaders, price ornaments, taglines
- padded section gaps
- prices that read as age statements
- any field that does not read as farmland in under a second

**The one gesture:** I2's rosette: 21 leaves plus a hatched cone, with channels, marginal teeth and terminal spines, engraved at one stroke weight and cropped hard by the right and bottom trim, with bleed.

## Round 4 fixes
| # | Fix | Result |
|---|---|---|
| 1 | I2 rosette, fleshier | The leaf half-width profile changed from t^0.28 (1-t)^1.0 to t^0.24 (1-t)^0.95, and widths rose 14% (WF 1.8 to 2.05). Leaves have full shoulders and still taper to the spine. Each leaf has an upturned-margin line (u = 0.62 falling to 0.37 along the leaf), so its concave inner face shows (a cupped rosette leaf, not a flat blade). Mass, teeth, spines, cone and line dropping are kept from I2. The heart shading runs a little further (0.70 to 0.85 of the leaf) so the rosette reads as one mass. |
| 2 | Iowa field | **Dropped** after testing (see "Field test"). Neither restrained version read as farmland in under a second, and the brief says drop rather than ship water. |
| 3 | Bleed | Trim is 8.5 x 11 in (816 x 1056 CSS px). The art canvas is 840 x 1080 CSS px, running 12 px (0.125 in, 3.2 mm) past the trim on every side. The agave's leaves and cone run into the right and bottom bleed. Safe inset is 0.5 in (48 px); all type ink is inside it (left 64, wordmark cap top 64, right edge of text 705, bottom 768). The wordmark's line box starts at y 41, but the box above the caps is empty ascender space. Print file: `menu-bleed.html` / `preview-letter-bleed.png` (2625 x 3375). The trim preview is `preview-letter.png` (2550 x 3300). |
| 4 | Prices | Muted #C9C2AF at weight 400 (names are ivory #EFE6D2 at 500), tabular figures, 0.9 em after the name. Contrast is 8.7:1. Eye travel is 4% (col 1) and 6% (col 2). |
| 5 | Spacing | One item pitch (8 px gap on an 8 px grid) and one section gap (32 px) everywhere; there is no padding. The columns are balanced by the structure: col 2 is widened to 250 px (x 432 to 682) and ends at 728. The art rises into the space below col 2 (leaf tips stop 23 px from the Brut Rosé line), so both column ends meet the drawing. The 40 px difference (col 1 ends at 768) is taken up by the art, not by gaps. I3's settings are kept: NBSP-bound ingredients, breaks only after "·", no hyphen splits, no one-word widows on letter or phone, 10.5 px sub-labels, "… lime wheel. Bright and citrus-forward." inline, and the wordmark cap top at 64 = the left margin. |
| 6 | Order | Col 1: Cocktails (Margarita first), then Spirits (Agave, then Brandy). Col 2, one continuous path: Draft Beer, Cider, Wine, with equal 32 px section gaps. |
| 7 | Content | Unchanged from I2 and I3; `build.py` asserts every item id and price. |

## Field test (why the field was dropped)
| Variant | Build | At thumbnail | Up close | Squint |
|---|---|---|---|---|
| A: rows in alternating density bands | level horizon at y 807; near-straight rows with one broad low rise; bands deepen and pitch widens toward the viewer; no boundary lines, rays or waves | horizontal stripes: reads as sea, a sunset, or ruled paper | ruled lines | 7.88%, ratio 10.9 |
| B: patchwork of parcels | the same bands, split into parcels whose straight parallel rows change angle (-7 to 8 degrees, flattened with depth) and density; no boundaries | still horizontal texture | scratchy, like wood grain | 7.92%, ratio 11.0 |
| Dropped (final) | none | the rosette alone | | 14.39%, ratio 56.9 |

The Iowa link is left to the "Iowa City, Iowa" sub-line. That is a known gap in ownability (see open items).

## Layout geometry (letter, CSS px at 96/in, x3.125 = 2550 x 3300 at 300 dpi)
- **Page:** trim 816 x 1056, bleed 12 px on every side, ground #10291F. No frame, rules or boxes.
- **Header:** centred.
  - CANTINA: Cormorant Garamond 500, 82 px, tracking .34em, gold #C8A765. Its cap tops measure 64 px from the trim (pixel scan in pass 1).
  - Sub-lines "& Cocktail Bar" and "Iowa City, Iowa": DM Sans 500, 11.5 px, tracking .34em, #C9C2AF.
- **Col 1:** x 64 to 400 (336), y 240 to 768: Cocktails (240 to 536), a 32 px gap, then Spirits (568 to 768).
- **Col 2:** x 432 to 682 (250), y 240 to 728: Draft Beer (240 to 400), Cider (432 to 496), Wine (528 to 728), with 32 px gaps.
- **Grid:** 8 px. H2 has a 16 px line and 8 px after; H3 has a 16 px line and 16 px before; name rows are 24 px; descriptions are 16 px; the item gap is 8 px. All 14 row tops are multiples of 8, and Cocktails and Draft Beer share y 240.
- **Type:**
  - H2: DM Sans 600, 13.5 px, tracking .30em, gold.
  - H3: DM Sans 500, 10.5 px, tracking .22em, #B3B09E.
  - Names: Source Serif 4 500, 16.5 px, #EFE6D2.
  - Prices: Source Serif 4 400, 16.5 px, #C9C2AF, tabular.
  - Descriptions: Source Serif 4 400, 12.5 px, #C9C2AF.
- **Art:**
  - Base (772, 1100), below the trim. Scale S = 860.
  - Stroke 1.25 CSS px (3.9 px at 300 dpi), gold, one weight throughout.
  - Bounding box x 100 to 816+, y 260 to 1056+; the filled silhouette covers 25.7% of the page.
  - The clamp keeps every leaf at least 23 px (6 mm) from every text line. 3 leaves were shortened (to 85%, 70% and 85%).
- **Phone (1170 x 5469, 390 CSS px at 3x):** one column in the same order with 34 px padding. The same rosette closes the page in a 390 x 520 box, cropped by the right and bottom edges.

## Contrast (worst pixel; letter and phone are the same)
| Role | Min contrast |
|---|---|
| Names | 12.45 |
| Prices, descriptions, sub-line | 8.70 |
| Sub-labels | 7.08 |
| Gold heads and wordmark | 6.75 |

## Iteration log (hypothesis, then result)
1. **I2 rosette plus a fleshier profile (0.22 / 0.78) plus field A.** The leaves became blunt paddles (aloe, not agave), and the field was mostly hidden under the low leaves.
2. **Profile 0.24 / 0.95, low leaves shortened to 62% to show the field.** Field A at thumbnail read as stripes or water. Field B (patchwork) read as scratches. **Field dropped.**
3. **No field, low leaves at full length.** The rosette split into 2 squint masses (8.75%, ratio 2.15).
4. **Heart shading 0.85.** One mass: 14.36%, ratio 58.1. **Checkpoint, and the "before" of the subtraction pass.**

## Device inventory and subtraction log
| # | Device | Decision | Evidence |
|---|---|---|---|
| 1 | CANTINA wordmark | keep | The one display word |
| 2 | Tracked sub-line (2 lines of 3 words or fewer) | keep | Venue and city |
| 3 | Gold section heads | keep | The only accent outside the art |
| 4 | 10.5 px sub-labels | keep | The draft's groups |
| 5 | Muted inline prices | keep | Price association; not an age statement |
| 6 | Leaves with ground-fill occlusion | keep | The gesture |
| 7 | Marginal teeth | keep | Anatomy (brief) |
| 8 | Terminal spines | keep | Anatomy (brief) |
| 9 | Cupped-margin line | keep | The "fleshy, cupped" fix. Ablation: 14.36% to 14.30%, ratio 58.1 to 57.9 |
| 10 | Channel crease | **removed** | It doubled the cupped-margin line inside each leaf. Ablation: 14.39%, ratio 56.9, no visible loss |
| 11 | Shaded-edge hatching with line dropping | keep | Volume |
| 12 | Heart shading | keep | Makes one mass (ratio 2.15 without it at this setting, 58 with it) |
| 13 | Hatched central cone | keep | Anatomy |
| 14 | Iowa field (rows in bands; patchwork) | **removed** | Failed the one-second farmland test in both forms |
| 15 | I2's furrow-ribbon leaves | **removed** | They read as more leaves (I2 critic). The field was meant to replace them, and it failed too |

3 of 15 devices removed (20%). This is below the 25% target: the remaining devices are the type system and anatomy that the brief explicitly asks to keep.

## visual_tests (before = iteration-4 checkpoint; after = final)
```json
{"file": "preview-letter-before.png", "squint_salient_regions": 2, "primary_area_pct": 14.36, "primary_to_secondary": 58.1, "ground_luminance": 0.153, "value_range_p5_p95": [0.133, 0.48], "accent_area_pct": 2.68, "visual_centroid": [0.65, 0.683]}
{"file": "preview-letter.png", "squint_salient_regions": 2, "primary_area_pct": 14.39, "primary_to_secondary": 56.89, "ground_luminance": 0.15, "value_range_p5_p95": [0.133, 0.48], "accent_area_pct": 2.65, "visual_centroid": [0.653, 0.687]}
```
For comparison: I2 had primary 12.4% at ratio 79 with accent 1.9%; I3 had 7.92% at ratio 241 with accent 1.99%. Accent area here is 2.65%, under 8%.

## References and sources
- I2 (`../explore-I2`) is the base, and ref-02 panel 3 is the grammar.
- I used no PHG library documents.
- Garnish citations: `../round-17/proposal.md` (phg.recipe_versions f06abb74, 14d45e57, 7095fd3d, 9fb77eaa).

## Open items
- **Ownability:** with the field dropped, only the sub-line says Iowa City. The substitution test will likely still fail. A future round needs an Iowa cue that reads instantly without being a second drawing, or a venue-supplied mark or name to replace the placeholder word "CANTINA".
- **Missing data:** ABV, region and brand are still missing and waiting on Rob. The draft gives Brut Rosé 13 no pour label.
