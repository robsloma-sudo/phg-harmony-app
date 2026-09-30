# TEST-1 round 19: "Sun Behind the Page", reading layer rebuilt (proposal v19)

Base: round 17, the best full-panel score (74.1: critic 74.0, content 77.8, accuracy 70.5). The art layer, the vertical
CANTINA wordmark, the "& COCKTAIL BAR · IOWA CITY, IOWA" rail line and the page zones are kept unchanged. The build19 ART
block is byte-identical to build17 (checked with diff). This round ports the content and typography wins that the
KB-rebuild panels (I5, I8) proved, and removes round 17's invented copy.

## Creative thesis (unchanged from round 17)

**A late gold sun sets behind a torn page, and an agave rises toward the list. The menu reads as one hand-cut paper
collage, warm and unhurried, where the art stays in the rail and the drinks sit in calm editorial type.**

- **Concept words (6):** torn paper · setting sun · agave · dusk warmth · editorial calm · hand-cut
- **Avoid-list:** lotería cards and papel picado; sombreros, cacti clip-art, skulls, piñatas, serape stripes; neon or
  "fiesta" colour; any lettering inside the art; trademarked worlds; fake distressed grunge; gold anywhere but the sun;
  boxed modules; a second illustration style; **any tagline or kicker (round 19: brand-voice lines with no source are costume)**.
- **Round-19 addition to the thesis:** the page speaks both languages plainly. Spanish and English share every label,
  set in the same type, so the bilingual voice lives in the structure and is not decoration.

## Revision hypothesis (round 19) and best-so-far

Hypothesis: round 17's visual score was capped by its reading layer, not its art. Accuracy (70.5) and content (77.8) lost
points to five things:
- invented taglines and kickers;
- one-word stub descriptions ("toasty", "pour");
- missing serve facts;
- English-only heads;
- 10 px labels.

The I5/I8 panels scored well on the fixes for these (bilingual H2+H3, sourced glass, full draft wording), but their
code-drawn art did not beat round 17's. Porting the fixes onto the round-17 page should lift criteria 8, 11-14 and 13
(venue fit) without regressing criteria 7, 15 and 16.

Held at best-so-far (round 17) treatment:
- art, wordmark and palette (criteria 4, 7, 15 and 16);
- dotted leaders (3, 14);
- one left edge and one price edge (1);
- 36 pt margins (6);
- exact prices (9).

Deliberate change with a regression risk: round 17's Wine | Spirits pair is now a single column. The bilingual labels do
not fit a 138 pt half column at the 12 px minimum. Measured in the real fonts:

| Label | Width | Half column |
|---|---|---|
| "POR COPA · BY THE GLASS" (9 pt, .14em) | 147 pt | 138 pt |
| "ESPUMOSOS · SPARKLING" | 142 pt | 138 pt |
| "DESTILADOS · SPIRITS" (13 pt caps, .12em) | 176 pt | 138 pt |

To fit the page, the beer, cider, wine and spirits rows use ref-01's one-row format (NAME, draft words, leader, price).
Watch criteria 1, 5 and 6 in review. If they regress, the fallback is to keep the single column and restore the two-line
rows by moving the allergen line into the rail.

## What changed from round 17

1. **Bilingual labels, exact accents, on both levels (Coordinator's strings).** Every label prints as Spanish · English
   in one line. English is set heavier (H2 English 650 in ink, Spanish 420 in #4F4238; H3 English DM Sans 700, Spanish 500),
   so the English half is read first.
   - H2: "Cócteles · Cocktails", "Cerveza y Sidra · Beer & Cider", "Vino · Wine", "Destilados · Spirits".
   - H3: "Clásicos · Classics", "De la Casa · House" (replaces "House Originals"), "De Barril · Draft", "Sidra · Cider",
     "Por Copa · By the Glass", "Espumosos · Sparkling", "Agave", "Brandy".
   - Sizes: H3 9 pt = 12 px CSS on letter, tracked .16em, and 12 px on phone. H2 13 pt caps, tracked .12em (was 15 pt/.2em,
     which cannot hold "CERVEZA Y SIDRA · BEER & CIDER": 347 pt against a 294 pt column).
   - doc.json section and sub `name`s carry the same strings.
2. **Invented copy removed.**
   - Rail taglines "GOOD DRINKS / GOOD COMPANY" and "PULL UP / A CHAIR / STAY / A WHILE" are gone.
   - Section kickers "raise a glass", "one more round", "for the table" and "¡salud!" are gone.
   - Their slots are left empty; the bilingual H2s carry the section heads.
   - The vertical "& COCKTAIL BAR · IOWA CITY, IOWA" rail line is kept.
3. **Glassware in every cocktail line, one rule.** The glass is the last element of the ingredient line, in small caps
   (DM Sans 700, 9 pt = 12 px CSS, tracked .12em), after a "·", with no full stop:
   - Margarita ROCKS;
   - Manhattan COUPE;
   - House Daiquiri COUPE;
   - Brown Butter Old Fashioned ROCKS.

   Verified through the read-only gateway, `phg.recipe_versions.glassware`, **log_id 248** (rows f06abb74 Rocks,
   9fb77eaa Coupe, 14d45e57 Coupe, 7095fd3d Rocks). The same call returned the garnishes already printed (lime wheel,
   cocktail cherry, lime coin, orange peel).
4. **Descriptions.**
   - Cocktails keep round 17's ingredient lists, including "house demerara syrup" on the Daiquiri. The Old Fashioned keeps
     "demerara syrup": its component is 'Demerara Syrup', and "house" is sourced only for the Daiquiri.
   - The Manhattan's aromatic bitters stay hidden (public_components).
   - The Margarita adds the draft's second sentence, "Bright and citrus-forward.", as its own line in the same roman.
   - Beer, cider and wine print the full draft text: "crisp pale lager", "hop-forward draft IPA", "toasty amber lager",
     "dry sparkling cider", "dry red wine", "dry white wine", "dry sparkling rosé".
   - Spirits print "blanco tequila", "añejo tequila" and "VSOP Cognac", with no "pour".
   - Voice: lower case, no full stops, like the cocktail lines (proper nouns keep their capitals). The Margarita's tasting
     note stays a sentence because it is a separate line.
   - No line starts with a separator: each "·" is bound to the word before it with a no-break space.
5. **Prices.** Round 17's dotted leaders are kept on every row, with one tabular price column (right-edge spread 0.0 pt).
   - Eye travel (price left edge minus the row's text end, divided by the column width) is 0.18-0.68.
   - Every row over 40% has a leader (Margarita 0.68 / 187 pt leader, Manhattan 0.66, Daiquiri 0.56, Malbec 0.53).
   - Spirits follow the same rule as every other row.
6. **Allergens.** One generic guest line sits at the foot of the reading area: "Please tell your server about any allergies."
   (Fraunces italic 9.5 pt). "Contains dairy" is not printed because it is unconfirmed (needs_input 1).
7. **Structure.** Order is Cocktails → Beer & Cider → Wine → Spirits (see the notes below). Four equal 18.2 pt section gaps
   are about 3.5x the 5 pt row gap. The sub gap is 9 pt, so the section break now clearly outranks the sub break.

### Notes the Coordinator asked for

- **Cider sits under Beer.** The draft has Cider as its own section (`sec_cider`). The print sets it as the sub
  "Sidra · Cider" under "Cerveza y Sidra · Beer & Cider", and doc.json keeps `sec_cider` as its own section (renamed
  "Sidra · Cider", `meta.printed_under = "sec_beer"`), so item ids and links survive.
- **Section order is the standard Cocktails → Beer & Cider → Wine → Spirits** (scorecard criterion 5). Note that this
  departs from DESIGN_THEORY_BRIEF §5 ("place Spirits/Agave before Wine"). The I5 panel's content reviewers asked for the
  standard order, and this round follows the Coordinator's instruction. Margarita still leads Clásicos and the menu.

## Restraint pass (scorecard 1c), with before and after numbers

Inventory: 15 decorative devices in round 17.
1. torn page edge
2. gold-leaf sun
3. agave rosette
4. torn hills
5. ground band
6. paper-fibre grain
7. sky wash
8. vertical wordmark
9. vertical venue line
10. top rail tagline
11. bottom rail tagline
12. H2 section rules
13. italic section-rule kickers
14. terracotta tracked subheads
15. dotted leaders

**Removed: 4 of 15 (27%).**
- 10, 11 and 13: invented brand-voice copy with no source; the KB counts it as costume.
- 12, the H2 rules, removed as an ablation test. Rendered without rules, the four sections ran together, the H2/H3
  difference rested on size alone, and the price column lost the only full-width line that marks its right edge.
  **Removal visibly hurt, so the rules came back.**

**Result: 15 → 12 devices (3 removed for good, 20%; 4 tested, 27%).**

Text strings removed from the page: 12 (4 + 4 rail lines and 4 kickers).

Functional elements added (not decorative, listed for honesty):
- 4 glass labels;
- 1 tasting-note line;
- 1 allergen line;
- the Spanish half of each label.

None of 1-9 was cut: the Coordinator locked the art and wordmark, and in round 17 each of them traced to the thesis.

Measured before (round 17) and after (round 19), from `handoff/designs/tools/visual_tests.py`:

| Metric | Round 17 | Round 19 |
|---|---|---|
| squint salient regions | 8 | 9 |
| primary area % | 15.31 | 13.58 |
| primary : secondary | 59.64 | 56.73 |
| accent area % (target ≤ 8) | 6.41 | 6.49 |
| ground luminance | 0.869 | 0.853 |
| value range p5-p95 | 0.264-0.908 | 0.258-0.909 |
| visual centroid | (0.252, 0.630) | (0.273, 0.635) |

Reading: one clearly dominant region is kept (the sun and agave rail, 57x the next region). The accent area is unchanged
within 0.1 pt. The extra salient region is the denser single reading column.

## Layout geometry (full element list with x/y/w/h in pt and mm: layout.json)

- **Page:** US letter, 612 x 792 pt (215.9 x 279.4 mm). Margins 36 pt (12.7 mm) on the reading area. Art bleed 9 pt
  (3.175 mm) on all four sides.
- **Zones:**
  - art rail x -9 to about 158 pt (the torn edge wanders between 150 and 166);
  - wordmark lane 166-262 pt;
  - reading column 282-576 pt (294 pt = 103.7 mm), single column;
  - 20 pt from the wordmark lane to the reading column.
- **Vertical positions (pt):**

  | Element | y (pt) |
  |---|---|
  | H2 Cócteles | 34.7 |
  | H3 Clásicos | 63.4 |
  | H3 De la Casa | 182.0 |
  | H2 Cerveza y Sidra | 309.7 |
  | H3 De Barril | 338.4 |
  | H3 Sidra | 419.6 |
  | H2 Vino | 468.6 |
  | H3 Por Copa | 497.3 |
  | H3 Espumosos | 557.8 |
  | H2 Destilados | 606.8 |
  | H3 Agave | 635.5 |
  | H3 Brandy | 696.0 |
  | allergen line | 745.0 (ends 756.2) |

  The wordmark runs from 33.1 to 471.9 and the rail line from 507 to 759.3.
- **Type:**

  | Role | Setting |
  |---|---|
  | CANTINA | Fraunces 96 pt (opsz 144, weight 380), vertical |
  | H2 | Fraunces 13 pt caps, tracked .12em |
  | H3 | DM Sans 9 pt caps, tracked .16em, #9A3B22 |
  | Names | Fraunces 600 11 pt caps, tracked .11em |
  | Ingredient and draft lines | Fraunces 400 10.5 pt, 14 pt leading, #40352D |
  | Glass labels | DM Sans 700 9 pt caps, tracked .12em |
  | Prices | Fraunces 600 12.5 pt, tabular, no currency sign |
  | Allergen line | Fraunces italic 9.5 pt |

- **Palette:**
  - paper #F2E9D6, ink #1D1815;
  - terracotta #9A3B22 (H3 only), secondary ink #4F4238 and #40352D;
  - agave greens #244A3E-#56866F, hills #B5532F/#7C3322, ground #162C25;
  - gold #C99532-#E4BF66 on the sun only.
- **Rhythm:**
  - cocktail gap 7 pt, one-row gap 5 pt;
  - 24 pt across a subhead;
  - H2 block: 16 pt line, 4 pt, a 0.75 pt rule, then 8 pt;
  - four section gaps of 18.2 pt each.
- **Phone:**
  - 390 CSS px wide at 3x, so 1170 px;
  - 24 px side margins; 24 px text lines; 16, 24 and 40 px gaps;
  - **all 47 measured row tops (wordmark, H2 rows, H3s, item rows, ingredient lines, notes, allergen line) sit on the 8 px grid**;
  - page height 2208 px (276 x 8);
  - one-row items stack their draft words under the name (CSS grid);
  - H2 halves never break inside a language ("CERVEZA Y SIDRA ·" / "BEER & CIDER").

## Hard gates (measured from the render; layout.json → measured_checks)

| Gate | Result | Evidence |
|---|---|---|
| accessibility (4.5:1 at the worst pixel) | **pass** | Letter minimum by role: subheader 5.19, header 13.15, item name 13.06, price 13.19, description 8.91, glass label 9.00, allergen line 7.26, rail line 7.59, title 13.06. Phone minimum 5.76. Method: a text-free render at 300 dpi (every `.tx` and its children transparent); each line's ink box plus 2 px; every background pixel checked. |
| menu_item_association | **pass** | Prices sit on the name row, and every row has a dotted leader. The maximum eye travel is 0.68, and every row over 0.40 has a leader. Name left-edge spread 0 pt, price right-edge spread 0.0 pt. Phone: prices sit in the name row box (shared baseline), and every row keeps its leader. |
| legibility / environmental_legibility | **pass** | At 1 m: names 9.1′ cap height, prices 10.9′, ingredient lines 6.37′ x-height, H3 and glass labels 7.28′ cap height (12 px CSS), header 11.8′. No reversed small text in the reading area, and no metallic ink on text. Phone: minimum type 12 px, glass labels and H3 12 px. |
| content_integrity | **pass (with open questions)** | Prices match the draft 14/14 (doc and print). Names are unchanged. No taglines. Every printed word traces to the draft, recipe_versions (log_id 248) or the Coordinator's label strings. |
| margins and bleed | **pass** | Text-ink margins: top 12.53 mm, right 12.70, bottom 12.62 (spread 0.17 mm). The left of the page is the full-bleed art rail. With the rail taglines removed, the leftmost text is the wordmark lane (60.7 mm); this is the round-17 composition, and the art is exempt. Art box -9, -9, 630 x 810 pt, so 3.175 mm past trim. menu-print-bleed.pdf has the bleed and crop marks. |

## Copy table (every printed word and its source)

| Section / sub | Item | Price | Printed line | Source |
|---|---|---|---|---|
| Cócteles / Clásicos | Margarita | 15 | tequila blanco · fresh lime · orange liqueur · agave syrup · lime wheel · ROCKS / Bright and citrus-forward. | draft desc 'Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward.'; components 'Fresh Lime Juice', 'Agave Syrup'; rv f06abb74 garnish 'Lime wheel', glassware 'Rocks' |
| Cócteles / Clásicos | Manhattan | 15 | rye · sweet vermouth · cocktail cherry · COUPE | draft desc with bitters hidden (public_components {'aromatic-bitters': false}); rv 9fb77eaa garnish 'Cocktail cherry', glassware 'Coupe' |
| Cócteles / De la Casa | Brown Butter Old Fashioned | 16 | brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel · ROCKS | components 'Brown Butter-Washed Bourbon', 'Demerara Syrup', 'Aromatic Bitters'; rv 7095fd3d garnish 'Orange peel', glassware 'Rocks' |
| Cócteles / De la Casa | House Daiquiri | 14 | white rum · fresh lime · house demerara syrup · lime coin · COUPE | draft desc 'White rum, lime, and house demerara syrup.'; component 'Fresh Lime Juice'; rv 14d45e57 garnish 'Lime coin', glassware 'Coupe' |
| Cerveza y Sidra / De Barril | Czech Pilsner | 7 | crisp pale lager | draft desc 'Crisp pale lager.' |
| Cerveza y Sidra / De Barril | Dry-Hopped IPA | 8 | hop-forward draft IPA | draft desc 'Hop-forward draft IPA.' |
| Cerveza y Sidra / De Barril | Amber Lager | 7 | toasty amber lager | draft desc 'Toasty amber lager.' |
| Cerveza y Sidra / Sidra | Dry Cider | 8 | dry sparkling cider | draft desc 'Dry sparkling cider.' |
| Vino / Por Copa | Malbec | 12 | dry red wine | draft desc 'Dry red wine.' |
| Vino / Por Copa | Pinot Grigio | 11 | dry white wine | draft desc 'Dry white wine.' |
| Vino / Espumosos | Brut Rosé | 13 | dry sparkling rosé | draft desc 'Dry sparkling rosé.' |
| Destilados / Agave | Blanco Tequila | 12 | blanco tequila | draft desc 'Blanco tequila pour.' ("pour" dropped per Coordinator) |
| Destilados / Agave | Añejo Tequila | 16 | añejo tequila | draft desc 'Añejo tequila pour.' ("pour" dropped) |
| Destilados / Brandy | Cognac VSOP | 18 | VSOP Cognac | draft desc 'VSOP Cognac pour.' ("pour" dropped) |
| (foot) | — | — | Please tell your server about any allergies. | generic guest line (Coordinator instruction); no item claim |

## missing_ingredients, item by item (also machine-readable in doc.json → item.meta.missing)

| Item | Missing (never invented) | needs_input |
|---|---|---|
| Czech Pilsner | brewery · ABV · pour size | 2 |
| Dry-Hopped IPA | brewery · ABV · pour size | 2 |
| Amber Lager | brewery · ABV · pour size | 2 |
| Dry Cider | producer · ABV · format (draft / can / bottle) | 3 |
| Malbec | producer · region · vintage · pour size | 4 |
| Pinot Grigio | producer · region · vintage · pour size | 4 |
| Brut Rosé | producer · region · vintage · **price label: glass or bottle?** (the draft label is empty, so it prints unlabelled) | 4, 5 |
| Blanco Tequila | brand · age statement · pour size | 6 |
| Añejo Tequila | brand · age statement · pour size | 6 |
| Cognac VSOP | brand (house) · pour size (VSOP is the age grade) | 6 |
| Manhattan | display of aromatic bitters: the draft hides them (public_components), the venue's menu_description lists them | **11** |
| Brown Butter Old Fashioned | **dairy allergen confirmation** (brown butter-washed bourbon); only the generic allergen line prints until then | 1 |
| Margarita, House Daiquiri | none: ingredients, garnish and glass are all sourced | — |

Wine in Rob's `producer · region` and `glass | bottle` format prints only once needs_input 4 and 5 are answered.

## Flags and needs_input (for the venue, via the Coordinator)

needs_input = true. risk_flags: missing_ingredients, allergen_unconfirmed, price_label_unknown.

The numbering is kept from rounds 15-16.
1. **Brown Butter Old Fashioned: dairy allergen.** Please confirm it, and the wording.
2. **Beer:** brewery, ABV and pour size for the three draft beers.
3. **Cider:** producer, ABV and format.
4. **Wine:** producer, region and vintage for all three wines, and the pour size by the glass.
5. **Brut Rosé: glass or bottle?**
6. **Spirits:** brand, age statement and pour size.
7. **Cantina gaps** (asked, not added): a Mexican lager, a mezcal, a non-alcoholic agua fresca?
8. **Venue name:** the page prints "Cantina / & Cocktail Bar" (the draft title is "Bar menu").
9. **Junmai Ginjo:** it is in phg.menu_items but not in the draft, so it is left off.
10. *(retired: the lotería verses are no longer in the design)*
11. **Manhattan: aromatic bitters.** Show them or keep them hidden? This design follows the draft and hides them.
12. *(retired: El Barril foot, no longer in the design)*

**Art pipeline:** the SVG art is unchanged. The Canva generate-image prompt for a future raster ART layer is the same as
round 17's (text-free torn-paper collage, gold-leaf sun, agave rosette, no lettering).

## References

- **Library (`menu_visual_documents.id`):**
  - 572 (Coa Cantina, Iowa City: local price band, agave emphasis);
  - 7923 (Coa Cantina, Des Moines: compact cocktail-led list);
  - 4969 (Blue Agave, Iowa: Classic / House tiers);
  - 208 (Alta Calidad: pour size in the header once supplied);
  - 2585 (La Buena Vida: Spanish/English headers used plainly).
- **Quality bar** (handoff/designs/references/rob-2026-09-28/):
  - ref-01 (the Bistro): vertical wordmark and art rail; NAME in tracked caps with a serif ingredient line; one-row beer
    lines with a short descriptor; one price column.
  - ref-04 (Solstice): sun disc, cut-paper collage, "name / ingredient · ingredient".

  Structure and type roles are borrowed from these; their art, taglines and lettering are not.

## Files

round-19/:
- menu.html
- menu.pdf (trim)
- menu-print-bleed.pdf (3.175 mm bleed and crop marks)
- preview-letter.png (2550 x 3300, 300 dpi, not downscaled)
- preview-phone.png (1170 x 6624)
- doc.json
- layout.json
- proposal.md

Build: build19/build.py → render.py → finalize.py. build17 and round-17 are untouched.
