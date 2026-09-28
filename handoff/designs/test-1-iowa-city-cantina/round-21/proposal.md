# TEST-1 round 21: "Sun Behind the Page, landed in Iowa" (proposal v21)

Built in build21/ (a copy of build20b) and written to round-21/. round-20b and build20b are untouched.

Input: the round-20b full panel (scores/NOTES.md "Round 20b full panel", scores/r20b.jsonl) scored combined 69.8: critic
68.5, content 74.6, accuracy 66.2. All 15/15 gates passed. Round 17 (74.1) is still the best full panel.

The art, the palette (apart from the price ink), the item list, the prices and the approved content are unchanged. The
ART block of build.py is byte-identical to build20b (checked with diff).

## Creative thesis

**A late gold sun sets behind a torn page, and an agave rises out of Iowa's contour-ploughed fields. The menu is one
hand-cut paper collage, in which Mexico's plant grows from Iowa's ground, while the drinks sit in calm, bilingual
editorial type with one grammar for every item.**

- **Concept words (6):** torn paper · setting sun · agave · Iowa loam · contour rows · editorial calm
- **Avoid-list:** lotería, papel picado, sombreros, cacti clip-art, skulls, serape stripes; neon or fiesta colour;
  lettering in the art; trademarked worlds; fake grunge; a second grain; gold anywhere but the sun; boxes; leaders or
  price ornaments; taglines; tracked caps anywhere but the H3 labels and the wordmark lock-up; **more than one item
  grammar**; invented sensory copy.

Illustration grammar, unchanged: flat cut-paper planes, torn edges with a cream fibre rim, one light from the top right,
and one paper-fibre grain on every shape.

## Revision hypothesis

All 15 reviewers of round 20b named two price systems:
- price after the name for cocktails and spirits;
- price after a mid-row descriptor for beer and wine, with a 136 pt spread of price edges.

Twelve also named duplicated labels; nine the Old Fashioned widow; six the long-s italic "l". Five critics flagged the
dead right third.

One item grammar on every row, clean labels and a filled two-column lower grid should lift critic criteria 1, 2, 3, 5
and 6, and content criteria 3 and 5, without costing the gains in the sourced copy.

## What changed (Coordinator items 1-8)

### 1. One item grammar on every row

Every row reads:
1. Name + price, the price 1 em after the name.
2. Italic sensory line (Newsreader italic, 11 pt, muted #5A4B3F).
3. Cocktails only: ingredients by recipe role.
4. Cocktails only: garnish · glass line.

Spirits print name + price only. The 382 pt tab stop is gone.

**Sensory lines.** These are phg.menu_items.menu_description, verbatim (gateway **log_id 266**), minus the trailing
period, and minus a trailing class noun only where it repeats the name:

| Item | menu_description | Printed | Trim |
|---|---|---|---|
| Margarita | "Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward." | Bright and citrus-forward | second sentence verbatim; period dropped (the first sentence is the ingredient list, printed below by role) |
| Czech Pilsner | "Crisp pale lager." | Crisp pale lager | period only ("lager" is not in the name) |
| Dry-Hopped IPA | "Hop-forward draft IPA." | Hop-forward, draft | trailing "IPA" repeats the name; comma joins the rest (Coordinator example) |
| Amber Lager | "Toasty amber lager." | Toasty | trailing "amber lager" repeats the name (Coordinator example) |
| Dry Cider | "Dry sparkling cider." | Dry, sparkling | trailing "cider" repeats the name; comma joins the rest (same pattern as the rosé example) |
| Malbec | "Dry red wine." | Dry red wine | period only ("wine" is not in the name) |
| Pinot Grigio | "Dry white wine." | Dry white wine | period only |
| Brut Rosé | "Dry sparkling rosé." | Dry, sparkling | trailing "rosé" repeats the name (Coordinator example) |
| Blanco Tequila, Añejo Tequila, Cognac VSOP | "… pour." | (none) | name + price only; the description only repeats the name |

No sensory copy was invented. The Manhattan, Old Fashioned and Daiquiri have no sensory sentence in their
menu_description, so they print none.

### 2. The italic "l"

Fraunces italic draws its "l" with a mid-height flag, which reads as a long s ("Cócteſes"). I tested 'WONK' 0 and 1,
opsz 9/36/72/144, SOFT 100, ss01-ss03 and salt; **the flag is in every setting** (the WONK axis does not affect "l").

Every italic role now uses **Newsreader italic** (OFL, the Google Fonts latin subset, bundled as
build21/fonts/Newsreader-italic-latin.woff2). It has a plain "l". At weight 600 its contrast and x-height sit well beside
Fraunces 600 roman, so the H2 halves keep the same weight. Verified in a full-resolution crop of "Cócteles",
"Cerveza y sidra" and "Destilados".

### 3. H3 labels deduplicated, Spanish in sentence case

| Level | Labels |
|---|---|
| H2 | "*Cócteles* · Cocktails", "*Cerveza y sidra* · Beer & Cider", "*Vino* · Wine", "*Destilados* · Spirits" |
| H3 | "*Clásicos* · Classics", "*De la casa* · House", "*De barril* · Draft", "*Sidra* · Cider", "*Por copa* · By the Glass", "*Espumosos* · Sparkling", "*De agave* · Agave", "Brandy" (printed once) |

The H2 Spanish also moves to sentence case ("Cerveza y sidra"), so both levels follow one rule.

**Why "Sidra · Cider" stays.** It is kept as one quiet label. Without it, Dry Cider would sit under "De barril · Draft"
and read as a draft pour, but its format is unknown (needs_input 3). The label also sits in its own column, beside the
draft beers, so it adds no height.

### 4. Old Fashioned break

The line breaks after "bourbon" and keeps its separator:

    brown butter-washed bourbon ·
    house demerara syrup · aromatic bitters

This is the same on phone. Rule everywhere: a break keeps its "·" at the end of the line, and no line is a single
ingredient left on its own. On phone the Margarita breaks after "orange liqueur ·".

### 5. The garnish · glass line

It no longer uses the H3 treatment. It is set in **Fraunces 500 capitals at 9 pt** (12 px), tracked .06em, in the
ingredient colour #40352D: for example "LIME WHEEL · ROCKS".

This Fraunces build has no small-caps (`smcp`) feature: with `font-synthesis: none`, small-caps text renders as plain
lowercase, and Chrome's synthetic small caps are thin. So 9 pt capitals, which sit at small-cap proportion next to the
10.5 pt ingredients, stand in for true small caps. DM Sans tracked caps now belong to the H3 labels alone.

### 6. Prices

Fraunces 600 (one step up), in agave green **#27463A**, tabular figures, 11 pt (the name size). Worst-pixel contrast is
**7.78:1**, at least the 7:1 asked for.

### 7. The dead right third

- Cocktails run full width.
- Beer & Cider (De barril | Sidra) and Wine | Spirits sit on **one two-column grid**: 282-420 and 438-576 pt, with an
  18 pt gutter. The H2 rules end at each column's own measure.
- **Right ink margin: 13.63 mm**, against top 12.70, bottom 12.87 and a declared 12.7 mm (within 1 mm).
- Cocktail blocks are separated by **14 pt**, against 7 pt between single rows. I used 14 rather than 10.5 so the gap
  stays on the 7 pt unit.
- Sections are separated by 35 pt, plus the 28 pt H2 block, plus 7 pt.
- H2 is 16.5 pt, exactly 1.5x the name size. At 17 pt, "Destilados · Spirits" was 140 pt wide and pushed its 138 pt
  column 2 pt off the grid.

### 8. Paperwork

- proposal.md and layout.json describe round 21 only (layout.json contains no "round 20" text and no tab stop).
- needs_input 13 is rewritten.
- The Daiquiri is added to missing_ingredients and to doc.json `meta.missing`.

## Ingredient display order (presentation only)

Source: phg.recipe_versions.ingredients (gateway **log_id 259**; versions f06abb74, 9fb77eaa, 14d45e57, 7095fd3d).

**Role → rank.** A role string is split on "/" and takes its best-ranked part. Ties keep recipe order. Hidden components
are dropped first.

| Rank | Roles |
|---|---|
| 1 | base spirit |
| 2 | liqueur, fortified wine, vermouth, modifier |
| 3 | sweetener, syrup |
| 4 | citrus, acid |
| 5 | bitters |
| 6 | soda, topper |
| 7 | anything else |
| (not ranked) | garnish: leaves the list and prints on the garnish · glass line |

| Cocktail | Printed ingredients | Garnish · glass |
|---|---|---|
| Margarita | tequila blanco · orange liqueur · agave syrup · fresh lime | LIME WHEEL · ROCKS |
| Manhattan | rye whiskey · sweet vermouth (aromatic bitters hidden per public_components) | COCKTAIL CHERRY · COUPE |
| Brown Butter Old Fashioned | brown butter-washed bourbon · house demerara syrup · aromatic bitters | ORANGE PEEL · ROCKS |
| House Daiquiri | white rum · **house demerara syrup · fresh lime** | LIME COIN · COUPE |

**Daiquiri: Coordinator override.** The DB role of the Daiquiri's "Demerara Syrup" is "House prep", with no sweetener
part. On the DB role alone it would rank 7 and print after the lime. **By Coordinator override it is ranked as a
sweetener and prints before the lime** (build.py `ROLE_OVERRIDE`). This is needs_input 13.

## Restraint pass (scorecard 1c), with before and after numbers

Inventory: 18 devices in the round-20b page.
- Art (1-12): torn page edge · sun · agave · 2 bluffs · 5 contour strips · paper grain · sky wash.
- Type devices (13-18): vertical wordmark · rail line · H2 rules · the 382 pt tab stop · a second tracked-caps style
  (DM Sans serve line) · duplicated H3 halves (BRANDY · BRANDY; "Destilados de agave" under "Destilados").

**Tested: 5 of 18 (28%). Removed: 3 (17%).**
- Removed: the tab stop (the second price system); the DM Sans tracked serve style (now Fraunces 9 pt caps, so tracked
  caps belong to the H3s alone); the duplicated label halves.
- Tested and kept: the "Sidra · Cider" label. Reasoned, not rendered without: dropping it would imply a draft format
  that is not sourced.
- Tested and kept: the H2 rules. They are the only marks of each column's measure on the new two-column grid.
- None of the art devices was touched (they are locked).

`handoff/designs/tools/visual_tests.py`, letter:

| Metric | Round 20b | Round 21 |
|---|---|---|
| accent area % (target ≤ 8) | 7.56 | **7.57** |
| squint salient regions | 8 | **8** |
| primary area % | 16.21 | **16.41** |
| primary : secondary | 65.6 | **65.4** |
| ground luminance | 0.861 | **0.865** |
| value range p5-p95 | 0.272-0.908 | **0.273-0.908** |
| visual centroid | (0.266, 0.620) | **(0.264, 0.620)** |

The art rail is still the one dominant region. The green prices do not raise the accent share: #27463A has 0.44
saturation, under the tool's 0.45 accent threshold.

## Layout geometry (full list with x/y/w/h in pt and mm: layout.json)

- **Page:** US letter, 612 x 792 pt, margins 36 pt (12.7 mm), art bleed 9 pt (3.175 mm) on all sides.
- **Zones:**
  - art rail -9 to about 158 pt;
  - wordmark ink 188.7-258.8 pt, on axis 224 pt shared with the vertical rail line;
  - reading area 282-576 pt;
  - two-column grid 282-420 | 438-576 pt for Beer & Cider and for Wine | Spirits.
- **Baseline:** 7 pt unit.
  - Line boxes are 14 pt (names, italic lines, ingredients, garnish · glass, H3, allergen), 21 pt (H2) and 28 pt (H2 +
    rule).
  - The italic and garnish · glass lines keep their 14 pt boxes. Padding (1.5 / 0.75 pt) moves their baselines so every
    baseline sits in the same place in its box.
  - The first H2 cap line sits at 36.0 pt, level with the CANTINA ink top (36.0 pt).
- **Positions (y, pt):**

  | Element | Column | y (pt) |
  |---|---|---|
  | H2 Cócteles | full | 31.88 |
  | H3 Clásicos | full | 67.6 |
  | H3 De la casa | full | 200.6 |
  | H2 Cerveza y sidra | full | 360.9 |
  | H3 De barril | left | 396.6 |
  | H3 Sidra | right | 396.6 |
  | H2 Vino | left | 542.8 |
  | H2 Destilados | right | 542.8 |
  | H3 Por copa | left | 578.6 |
  | H3 De agave | right | 578.6 |
  | H3 Brandy | right | 634.6 |
  | H3 Espumosos | left | 662.6 |
  | allergen line | full | 745.7 |

  Item-name left edges: 0 pt spread in every column. H2 x: 282 / 282 / 438.
- **Type:**

  | Role | Setting |
  |---|---|
  | CANTINA | Fraunces 96 pt vertical |
  | H2 | 16.5/21 pt, Newsreader italic 600 · Fraunces roman 600 |
  | H3 | DM Sans 700, 9/14 pt, .08em caps (Spanish italic · English roman), #9A3B22 |
  | Names | Fraunces 600, 11 pt |
  | Prices | Fraunces 600, 11 pt, #27463A, tabular |
  | Sensory lines | Newsreader italic 400, 11 pt, #5A4B3F |
  | Ingredients | Fraunces 400, 10.5 pt, #40352D |
  | Garnish · glass | Fraunces 500, 9 pt caps, #40352D |
  | Allergen line | Newsreader italic, 10 pt, #4F4238 |

- **Palette:** as round 20, except prices are #27463A.
  - paper #F2E9D6, ink #1D1815, terracotta #9A3B22;
  - sky #F1DEC2 → #CF7F55, gold (sun only) #C38F34-#E2BC62;
  - bluffs #B5532F and #7C3322, agave #244A3E-#56866F;
  - contour strips #27463A, #5E4636, #1D382E, #4A372B, #132720.
- **Phone:**
  - 390 CSS px at 3x = 1170 x 7176 px; 24 px side margins;
  - own hero (416 px) and torn footer (96 px);
  - H2 stacks Spanish over English with no "·"; the two-column grids stack;
  - **all 61 measured row tops on the 8 px grid** (page 2392 px = 299 x 8); minimum type 12 px.

## Hard gates (measured; layout.json → measured_checks)

| Gate | Result | Evidence |
|---|---|---|
| accessibility (4.5:1 at the worst pixel) | **pass** | Letter minimum by role: H3 5.19, sensory/ingredient lines 6.26, legal 7.26, rail line 7.59, **price 7.78**, garnish · glass 8.92, H2 13.15, name 13.19, title 13.06. Phone minimum 5.76. Method: a text-free render at 300 dpi, every background pixel in each line's ink box (+2 px). |
| menu_item_association | **pass** | One grammar: the price is always 1 em after the name. Maximum eye travel 0.080 (letter; the half-width columns make the fraction larger) and 0.047 (phone). Every row is within 40%. There are no leaders. |
| legibility / environmental_legibility | **pass** | At 1 m: names and prices 9.1′ cap height; ingredient lines 6.37′ x-height; H3 7.28′; garnish · glass 8.19′ cap height; H2 14.6′. No reversed small text. No metallic ink on text. Phone minimum 12 px. |
| content_integrity | **pass (open questions below)** | Prices match 14/14 in the doc and in print; names are unchanged. Sensory lines are verbatim menu_description with the trims listed above. Ingredients and garnish · glass come from recipe_versions. The Daiquiri order is a Coordinator override, flagged as needs_input 13. **Junmai Ginjo is omitted because phg.menu_items has it as status='retired'** (log_id 258, re-read at log_id 266); it is not a dropped item. |
| margins and bleed | **pass** | Text ink: top 12.70 mm, right 13.63 mm, bottom 12.87 mm. The left is the full-bleed art rail. All text sits inside the safe inset. The bleed is 3.175 mm; menu-print-bleed.pdf has the crop marks. |

## missing_ingredients, item by item (also in doc.json → item.meta.missing)

| Item | Missing (never invented) | needs_input |
|---|---|---|
| Czech Pilsner, Dry-Hopped IPA, Amber Lager | brewery · ABV · pour size | 2 |
| Dry Cider | producer · ABV · format (draft / can / bottle) | 3 |
| Malbec, Pinot Grigio | producer · region · vintage · pour size | 4 |
| Brut Rosé | producer · region · vintage · **glass or bottle?** | 4, 5 |
| Blanco Tequila, Añejo Tequila | brand · age statement · pour size | 6 |
| Cognac VSOP | brand · pour size | 6 |
| Manhattan | aromatic bitters display (hidden per public_components) | 11 |
| Brown Butter Old Fashioned | dairy allergen confirmation; only the generic allergen line prints | 1 |
| **House Daiquiri** | **demerara syrup role: confirm "House prep / sweetener"** | **13** |
| Margarita | none | — |

## Flags and needs_input (via the Coordinator)

needs_input = true. risk_flags: missing_ingredients, allergen_unconfirmed, price_label_unknown, role_override.
1. Old Fashioned dairy allergen: confirm, and give the wording.
2. Beer: brewery, ABV and pour size.
3. Cider: producer, ABV and format.
4. Wine: producer, region, vintage and pour.
5. Brut Rosé: glass or bottle?
6. Spirits: brand, age and pour.
7. Cantina gaps (asked, not added): Mexican lager, mezcal, agua fresca?
8. Venue name (the draft title is "Bar menu").
9. Junmai Ginjo is status='retired' in phg.menu_items (log_id 258 / 266), so it is omitted. No action is needed unless
   the venue reactivates it.
10. *(retired)*
11. Manhattan aromatic bitters: show them or keep them hidden?
12. *(retired)*
13. **House Daiquiri: the house demerara syrup prints BEFORE the fresh lime, by Coordinator override.** recipe_versions
    14d45e57 lists its role as "House prep". **Rob, please confirm the role should read "House prep / sweetener"** (as on
    the Old Fashioned, 7095fd3d). Once the role is updated, the override can be removed with no change to the print.

## References

- **Library (`menu_visual_documents.id`):**
  - 572 (Coa Cantina, Iowa City: local price band, agave emphasis);
  - 7923 (Coa Cantina, Des Moines: compact cocktail-led list);
  - 4969 (Blue Agave, Iowa: Classic / House tiers);
  - 208 (Alta Calidad: pour size in the header once supplied);
  - 2585 (La Buena Vida: plain Spanish/English headers).
- **Quality bar:**
  - ref-01 (Bistro): vertical wordmark and art rail, a short-measure price beside the name, a quiet italic descriptor.
  - ref-04 (Solstice): sun disc, cut-paper collage.

  Structure and type roles are borrowed from these; their art and lettering are not.
- **Gateway calls:** log_id 248 (glassware and garnish), 258 (Junmai Ginjo status), 259 (ingredient roles), 266
  (menu_description and status for all 15 menu_items).
- **Font:** Newsreader italic (Production Type, SIL Open Font License), fetched from fonts.gstatic.com (latin subset).

## Files

round-21/:
- menu.html
- menu.pdf (trim)
- menu-print-bleed.pdf (3.175 mm bleed and crop marks)
- preview-letter.png (2550 x 3300, 300 dpi, not downscaled)
- preview-phone.png (1170 x 7176)
- doc.json
- layout.json
- proposal.md

Build: build21/build.py → render.py → finalize.py; font in build21/fonts/.
