# TEST-1 · Direction G2 "Monument", round 2 (type-as-image, drawn letterforms)

Status: exploration for the Coordinator. Not submitted, not committed. `explore-G/` stays as the round-1 checkpoint.
Build: `python3 build.py` (after) and `python3 build.py before` (pre-subtraction). Glyphs: `glyphs.py`.
Content: `../build/draft_doc.json` (rev 3). Garnishes come from `phg.recipe_versions.garnish` via the designer gateway (log_id 213).

## 1. Thesis (written before code)
**Thesis:** A cantina's name belongs on a hand-painted sign, and Iowa City is a town of print (UNESCO City of
Literature). So CANTINA is pulled like a two-plate wood-type poster cut in rótulo letterforms, and the chile plate's
slip is at once the sign painter's drop shadow and the printer's misregistration.

The "City of Literature" designation is a public fact about the city, not the venue. It lives only in this rationale,
and nothing about it is printed on the menu.

**Concept words:** sign · press · two plates · slip · upright · quiet list

**The one gesture:** the drawn CANTINA monument, run vertically up the right edge and cropped by the trim at the top
and the right. It has a black key plate over a chile plate offset toward the list, and the venue line
"& Cocktail Bar / Iowa City, Iowa" continues on the same baseline at its foot.

**Why it fails the substitution test (critic's round-1 note):**
- The letterforms are not a stock font. `glyphs.py` builds C, A, N, T, I from polygons: wood-type chamfered corners;
  V ink traps in every concave or acute joint; a flat-topped A and a spurred C taken from rótulo block lettering.
- The one red event is a register slip that doubles as a sign-painter's shadow (sombra). The Mexican sign and the
  Iowa City press are the same device, not two labels.

**Avoid-list:** stock display fonts (the round-1 Oswald) · boxes and cards · leaders · price ornaments · tables ·
icons, agave/sun/cactus stamps · papel picado or any costume surface · fake grain or distress texture (the only
materiality is the plate offset) · borrowed taglines · tracked caps on labels longer than 3 words · item names in caps ·
invented venue facts.

## 2. Content (round-2 fixes applied)
**Prices:** set inline 0.9 em after the name, in Newsreader 400 and the muted ink (INK2), the same size as the name,
with tabular figures. The name is 500 weight in INK. Eye travel is measured as the gap between name end and price
start, divided by the row width. The maximum is **10.4% on letter and 5.1% on phone** (limit 40%). Old Fashioned wraps
to two lines, and its price follows "Fashioned" on the last line.

**Order:** Cocktails (Classics: **Margarita first**, Manhattan; House Originals: Daiquiri, Old Fashioned) · Beer (Draft)
· **Spirits** (Agave, Brandy) · **Wine** (By the Glass, Sparkling) · Cider. The Agave and Brandy sub heads are kept.
The Beer section's single sub, "Draft", sits on the Beer head line (all three items are draft).

| Item | Price | Description on menu | Source |
|---|---|---|---|
| Margarita | 15 | Tequila blanco · fresh lime juice · orange liqueur · agave syrup · lime wheel / Bright and citrus-forward. | components + garnish (recipe_versions) + draft style sentence |
| Manhattan | 15 | Rye whiskey · sweet vermouth · cocktail cherry | components minus hidden Aromatic Bitters; garnish = cocktail cherry (already a component) |
| House Daiquiri | 14 | White rum · fresh lime juice · demerara syrup · lime coin | components + garnish |
| Brown Butter Old Fashioned | 16 | Brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel | house_recipe=false, so names only, no quantities; + garnish |
| Czech Pilsner | 7 | Crisp pale lager | draft desc, full |
| Dry-Hopped IPA | 8 | Hop-forward draft IPA | draft desc, full |
| Amber Lager | 7 | Toasty amber lager | draft desc, full |
| Blanco Tequila | 12 | Blanco tequila pour | draft desc, full ("pour" = sourced serve label) |
| Añejo Tequila | 16 | Añejo tequila pour | draft desc, full |
| Cognac VSOP | 18 | VSOP Cognac pour | draft desc, full |
| Malbec | 12 | Dry red wine | draft desc, full |
| Pinot Grigio | 11 | Dry white wine | draft desc, full |
| Brut Rosé | 13 | Dry sparkling rosé | draft desc, full |
| Dry Cider | 8 | Dry sparkling cider | draft desc, full |

- Trailing periods are dropped from the one-phrase descriptions.
- The Margarita's style sentence keeps its period because it is a sentence.
- Descriptions may now wrap (cocktails take 2–3 lines); every other description is one line.
- The tagline has been removed. The draft title and subtitle are not printed.

## 3. Device inventory, subtraction log, before/after numbers

**Before** (`preview-letter-before.png`) had 10 devices:
1. key plate (drawn CANTINA)
2. chamfered corners
3. ink traps
4. chile plate, offset (-3, 4) units = 5 units ≈ 10.5 px
5. venue line at the monument's foot
6. red section heads
7. hairline rule under every section head
8. grey sub heads, 7 rows, including a separate "Draft" row
9. inline muted prices
10. per-column fitted rhythm

| Device | Decision | Reason |
|---|---|---|
| Hairline under section heads | **removed** | It added a second horizontal system that competed with the monument's verticals. Space already separates sections, and ablating it cost nothing |
| Separate "Draft" sub-head row | **removed** (merged onto the Beer head line) | A one-group row costs a line of rhythm and says nothing a head line can't |
| Chile plate offset 5 units | **reduced** to (-2, 3) ≈ 3.6 units / 7.6 px | At 10 px the slip read as a deliberate drop shadow only, and the "press" half of the thesis was lost. Accent area went from 2.26 to 1.68% |
| Ink traps | kept | Ablation made the glyphs read as a generic condensed sans. The traps are what make the letters "cut" rather than "typed" |
| Chamfers | kept | Same reason as the ink traps; they are the wood-type/rótulo signature |
| Venue line at the foot | kept (required) | It joins the name and place into one unit and removes the round-1 head block |
| Red section heads | kept | The only accent in the reading layer; they are the entry points |
| Sub heads | kept (6 rows) | Draft data groups (Classics, House Originals, Agave, Brandy, By the Glass, Sparkling) |
| Inline muted prices | kept (required) | Price association gate |
| Per-column rhythm | kept | It closes the dead field under Amber Lager; the two columns' units differ by only 0.35 px (30.28 vs 30.63) |

Also removed since round 1 (G → G2): the "Good drinks / Good people" tagline and the top-left head block, which
became the foot line.
Net result: 2 devices removed and 1 reduced out of 10 in-round, plus 2 removed since G. That is 4 of 12 (33%).

**Revision hypotheses this round:**
- (a) The new order plus larger reading type would let both columns fill the page at a moderate rhythm.
  - At 18 px names, u hit the 30–34 px cap with section holes of 130–240 px, so it failed.
  - At 24 px names (18 pt) with a 252/208 grid, both columns land on the bottom margin at u ≈ 30.5 with 83–84 px
    section gaps, so it passed.
  - Moving Cider under Beer was tried and reverted: it unbalanced the columns the other way.
- (b) A smaller register slip would restore the "press" reading without losing the "sign" reading. This passed.

| visual_tests metric | G round 1 (checkpoint) | G2 before | **G2 after** | target |
|---|---|---|---|---|
| squint_salient_regions | 2 | 1 | **1** | one dominant |
| primary_area_pct | 16.96 | 15.84 | **15.40** | — |
| primary_to_secondary | 2.04 | — (single region) | **— (single region)** | clearly dominant |
| accent_area_pct | 0.13 | 2.26 | **1.68** | ≤ 8 |
| value_range_p5_p95 | 0.096–0.908 | 0.096–0.912 | 0.096–0.912 | — |
| visual_centroid | 0.797, 0.502 | 0.783, 0.419 | 0.783, 0.418 | — |
| silhouette corr vs G | — | 0.611 | **0.606** | < 0.8 = structurally different |

`visual_tests.json` (final):
```json
{"file": "preview-letter.png", "squint_salient_regions": 1, "primary_area_pct": 15.4, "primary_to_secondary": null,
 "ground_luminance": 0.9, "value_range_p5_p95": [0.096, 0.912], "accent_area_pct": 1.68, "visual_centroid": [0.783, 0.418]}
```
Device budget: 1 gesture (a two-plate monument) · 1 display word · 1 accent (chile: plate slip + section heads) ·
0 boxes · 0 leaders · 0 price ornaments · 0 tables · 0 icons · 0 taglines.

## 4. Layout geometry (CSS px at 96/in; x3.125 = 300 dpi print px). Every element box is in `geometry.json`.
- **Page:** letter 816 x 1056, rendered at 2550 x 3300. Ground PAPER #EFE7D8.
- **Margins:** 56 px (0.58 in) left, top and bottom for all text. The monument alone crosses the trim.
- **Grid:**
  - Two columns, 252 px + **32 px gutter** + 208 px (x 56–308 and 340–548).
  - The monument's baseline is at x = 622.2 and the chile plate reaches x ≈ 618. The **channel is 70 px ≥ 2 x gutter
    (64)**; the build checks this.
  - Both columns run from y = 56 to y = 1000 (the bottom margin), so there is no dead field.
- **Rhythm:** a unit u per column (col0 30.28, col1 30.63) sets item spacing, and the section gap is 2.75u (83.3 / 84.2).
- **Section heads (top y):**
  - Left column: Cocktails 56, Beer 732.4.
  - Right column: Spirits 56, Wine 476.2, Cider 896.4.
- **Monument:**
  - Drawn glyphs; the word is 401 units long at cap height 100 units. Scale 2.1064, so the cap height is 210.6 px.
  - It runs from y = -12.7 (cropped by the top trim) to y = 832, rotated 90° with letter tops facing the right trim.
  - Tops are cropped 8% (16.9 px, 4.5 mm) past the right trim, so the art bleeds ≥ 3 mm at the top and right.
  - The key plate is INK #1B1815. The chile plate is #9B2D1F, offset (-2, 3) glyph units, which puts it 6.3 px left
    of and 4.2 px above the key on the page.
- **Foot (venue line):**
  - Oswald 500, 13 px, tracking .30 em, rotated 90°, on two lines of ≤ 3 words each:
    "& COCKTAIL BAR" (INK) / "IOWA CITY, IOWA" (INK2).
  - Line 1's baseline sits on the monument baseline (x = 622.2). The box is x 597.6–637.9, y 858–1000.5, and it ends
    on the bottom margin.
- **Type:**
  - Section heads: Oswald 500, 18 px, .30 em, CHILE.
  - Sub heads: Oswald 500, 13 px, .30 em, INK2.
  - Names: Newsreader 500, 24 px (18 pt), title case, INK.
  - Prices: Newsreader 400, 24 px, INK2, tabular figures, 0.9 em after the name.
  - Descriptions: Newsreader italic, 16 px (12 pt), INK2, line height 1.32.
- **Contrast on paper (flat ground; no art behind any text):** INK 14.39:1 · INK2 7.65:1 · CHILE 6.13:1.
- **Checks in build.py:** eye travel ≤ 40%; each price on the name's last line; the channel ≥ 2 x gutter; all text
  inside the 0.5 in safe area and 24 px clear of the plates; the foot inside the safe area. All passed
  (`problems: []`, letter and phone).
- **Phone (390 css px, x3 = 1170 x 4386):**
  - The same two-plate word runs horizontally across the full width at the top (scale 0.9726, cap 97.3 px), with the
    tops cropped 8% by the top trim.
  - The venue line sits directly under the word's baseline (the foot).
  - Below that is one column: names 19 px, descriptions 14 px, sections in the same order. Maximum eye travel is 5.1%.

## 5. References
- `references/rob-2026-09-28/ref-02-3acf255d.png`: the quiet two-column grammar and red tracked heads; panel 4 is the
  vertical cropped wordmark that G2 now moves away from by drawing its own letterforms.
- `ref-01-98c65abe.png`: the vertical wordmark carrying the page.
- Library (gateway log_id 208): documents 572 (COA Cantina Iowa City), 7923, 2368 and 2929, used for list structure only.

## 6. Risk flags / questions
- `city_fact_in_rationale`: "City of Literature" appears only in the thesis, never on the menu. If the Coordinator
  prefers a rationale with no external facts, the concept still stands on "press" alone.
- `sample_content`: the draft items are beta seed content.
- No bleed PDF this round. The monument already extends ≥ 3 mm past the trim at the top and right, so a bleed file
  only needs a wider canvas.
- `menu.html` loads its fonts from `fonts/` by absolute file:// URI (Oswald 500 for labels, Newsreader for the reading
  layer; SIL OFL). The monument needs no font.
