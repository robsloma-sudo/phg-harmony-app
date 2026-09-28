# K3 · MAPA DE SABOR (the flavor field)

Content: `../expanded-v1/manifest.json` (sha256 prefix `6bd0338296207153`). Build: `python3 build.py` regenerates every file here, and `gates.json` holds the measured gates.

## Thesis

*The guest's question is "what does it taste like?", so the menu is the answer drawn as a field.*

- **Concept words:** plotted, measured, comparable, exact, calm.
- **The one gesture:** a single citrus-yellow → smoke-charcoal field that bleeds off the top and right edges of the front, with 12 drinks placed on it.
- **Avoid-list:** flavor wheels, sombreros/cacti/papel picado/sugar skulls/serapes, agave or sun pictograms, taglines, boxes around sections, price ornaments, and colour in the reading layer.

## How the structure encodes the concept

**Front: the field is the menu's table of contents.**
- The x axis runs bright → rich and the y axis runs clean → smoky. Smoke rises, so smoky is up.
- The field's colour *is* the axis sum. The linear gradient runs from plot (0,0) to (10,10), so a drink's ground colour already tells you where it sits.
- Each cocktail is a paper disc at its coordinate. The disc holds its glass glyph, and an ink badge carries its number.
- The index below is set in large Inter Tight 200 numerals, the only display type besides the wordmark. The numerals key each point to the full binding stack:
  1. name + price;
  2. sensory line (serif italic);
  3. ingredients in manifest role order (serif roman);
  4. garnish · glass (grotesk, muted).
- The index runs column-major, so Clásicos fill columns 1–2 and De la Casa fill columns 3–4. There is one subhead row and no boxes.
- Zero-proof sits on the bottom margin. It is not plotted, because the manifest gives it no ingredients.

**Back: the same idea as small multiples.**
- There are 25 identical micro-cards on one grid. Each card carries exactly four data marks:
  1. class (serif italic);
  2. an oak-age bar on a shared 0–54 month track (ticks at 0/12/24/36/48);
  3. region;
  4. price (inline with the name).
- The cards are grouped Blanco / Reposado / Añejo / Mezcal / Casa. The group label column carries the class-level sensory line once, rather than 25 times (data-ink).
- **Macro reading:** a full-bleed ink band at the top draws the cards' oak scale once at poster size. Its large numerals 0 12 24 36 48 are the back's display type, with the class ranges drawn as paper bars:
  - blanco · joven: dot at 0;
  - reposado: 2–12;
  - añejo: 12–36;
  - cognac VSOP: arrow at 48+.
- Read down the page, the card bars step from dot to short bar to long bar to arrow.
- Oak ages come only from the manifest's own class-level sensory text: "Unaged", "2–12 months oak", "1–3 years oak", "4+ years oak".
- Three mezcals state no age ("Pit-roasted espadín"). They get an empty track, and the key says so rather than guessing.

**Mexico and Iowa appear as systems, not stickers.**
- The map shows the house signatures bridging the two: Milpa (roasted Iowa corn syrup) and Loess (Iowa wildflower honey on mezcal).
- The back is an agave age/region census: Los Altos, Tequila Valley, Guanajuato, Oaxaca.

**Grid and type.**
- 12 columns on letter: 52 px (0.54 in) margins and 16 px gutters. The field starts on column 5.
- On the back, spirit cards, beer and wine use the same column 4–12 subgrid. The label column (1–3) matches the front index's first column.
- Typefaces: **Inter Tight** (grotesk) for names, prices, labels and numerals; **Source Serif 4** (text serif) for sensory lines and ingredients. Both are variable and were fetched from Google Fonts into `fonts/`.
- Inks: paper `#F3F0E8` and ink `#161513`, plus two ink tints for secondary text. The only colour is the field gradient and the three ingredient-driven liquid tints, all inside the map.

## Coordinates (PHG inference, not a tasting panel)

- **Scale:** 0–10 on each axis.
- **x axis, bright → rich:** acid and length pull toward bright; sugar, aged spirit, butter, vermouth, coffee and cacao pull toward rich.
- **y axis, clean → smoky:** smoke, roast, char and lingering pungency pull toward smoky. Soda lengthening and unaged neutral spirit pull toward clean.
- **Inputs:** only the manifest's sensory line and ingredient list. Nothing is tasted.
- **Spacing:** where drinks are near-identical on paper (Paloma, Ranch Water, Margarita), they were spread by at least one disc width. Their relative order was kept. The minimum centre distance on the letter map is 43 px, and the discs are 39 px across.

| # | Drink | x (bright→rich) | y (clean→smoky) | Reasoning from the manifest text |
|---|---|---|---|---|
| 01 | Margarita | 2.6 | 1.4 | "Bright and citrus-forward". Lime-led, but orange liqueur + agave syrup round it more than the long highballs do. Shaken blanco shows more cooked-agave pepper than a soda-lengthened drink, so it sits a little above the floor. |
| 02 | Paloma | 1.6 | 0.5 | "Tart grapefruit, salted edge". Very bright. Grapefruit soda adds a little sweetness over Ranch Water, so it sits a touch right. Salt is not smoke, so it stays near the floor. |
| 03 | Ranch Water | 0.4 | 0.8 | "Dry, bracing, lime-bright". No sweetener at all and mineral water, so it is the brightest point. Blanco pepper keeps it just off the floor. |
| 04 | Manhattan | 8.2 | 3.3 | "Deep, spiced, silky". Rye + sweet vermouth is rich. Barrel spice and char give some toast but no smoke. |
| 05 | Batanga | 4.7 | 2.0 | "Cola-dark, salty, sharp lime". Cola's caramel pulls it to the centre, and sharp lime holds it left of the stirred drinks. Caramel colour/roast lifts it slightly. |
| 06 | Carajillo | 8.6 | 5.9 | "Espresso, vanilla, bittersweet". Licor 43 vanilla sweetness makes it rich. Espresso roast is the nearest thing to smoke outside the mezcal drinks. |
| 07 | Brown Butter Old Fashioned | 9.5 | 4.3 | "Nutty, round, warm". Butter-washed bourbon + demerara make it the richest drink. Charred new oak and browned butter add toast. |
| 08 | House Daiquiri | 3.9 | 0.3 | "Crisp, clean, lightly rich". Its own words put it at the clean floor. Demerara ("lightly rich") moves it right of the tequila highballs. |
| 09 | Mezcal Negroni | 6.7 | 8.7 | "Smoke, bitter orange, velvet". Smoke is named first and mezcal is the base, so it is the smokiest point. Campari + vermouth are rich and bittersweet, but less sweet than the dessert drinks. |
| 10 | Spicy Pineapple Margarita | 3.1 | 2.9 | "Green heat, ripe pineapple". Ripe pineapple is rounder than lime. Jalapeño heat lingers (pungency) but is not smoke, so it sits in the lower third. |
| 11 | Milpa Old Fashioned | 7.1 | 5.3 | "Toasted corn, cacao, oak". Reposado + roasted-corn syrup + mole bitters give toast and roast. Lighter-bodied than the bourbon drinks, so left of 07. |
| 12 | Loess | 4.6 | 7.1 | "Soft smoke, honey, ginger snap". Espadín mezcal gives smoke ("soft", so below 09). Honey is rich, and lemon + ginger pull it back to the centre. |

Two findings for Rob, as observation rather than a recommendation:
- The top-left quadrant (bright *and* smoky) is empty.
- The richest drinks are all stirred or short.

A citrus-forward mezcal serve would fill the gap, but that is a menu decision, not a design one.

## Glass glyphs

- The glyphs form one coded family drawn only from the manifest's `glass` and `garnish` fields: rocks, highball and coupe.
  - **Ice cue:** a cube for rocks and highball. The coupe is served up.
  - **Garnish cues:** lime wheel (spoked disc), lime wedge, lime coin, salt rim (dotted rim), orange peel (twist), cocktail cherry, candied ginger (cube on a pick). No garnish means no cue.
- **Liquid colour** appears only where an ingredient makes it obvious: Campari → red (09), espresso → dark (06), Mexican cola → dark (05, whose own sensory line says "Cola-dark"). Every other drink gets one neutral tint.
- A key on the front explains all of this.

## KB principle keys used

- `creative_thesis_required`, `concept_before_decoration`: the field is the information.
- `focal_dominance_relative`, `hierarchy_not_everything_loud`, `contrast_is_finite_resource`: one field on the front and one ink band on the back; everything else is quiet.
- `accent_requires_scarcity`: all colour is inside the map.
- `menu_item_is_unit`, `price_association`: prices inline, ≤ 0.42 em from the name.
- `expressive_type_boundary`: display numerals are index keys and scale values, never prices.
- `menu_sections_need_transition`, `enclosure_strong_grouping`: rules and space, no boxes.
- `abstraction_reduces_cliche`, `literal_motif_budget`, `style_not_costume`: the only literal motif is the glass family, which the brief requested.
- `case_has_cost`: tracked caps only on short subheads.
- `description_supports_choice`: the sensory line is on every drink.
- Tufte micro/macro, small multiples and data-ink: the class sensory is printed once per group.

## Precedents: what transfers and what is not copied

- **Müller-Brockmann / Swiss International Style:** the modular column grid, asymmetric placement, and flush-left ragged-right grotesk. No poster layout is copied.
- **Neurath / Arntz Isotype:** one consistent pictogram family whose variables (glass, ice, garnish, tint) encode data. No Isotype figures are copied.
- **Flavor-wheel tradition:** only the principle that taste can be plotted. There is no wheel, no radial segments, and no borrowed descriptor vocabulary. The axes are a Cartesian plane built from this menu's own words.

## Hard gates (measured, `gates.json`)

| Gate | Result |
|---|---|
| Names, prices, sensory, ingredients (in order), garnish, glass, spirit class vs manifest.json | **Pass**: DOM diff over 50/50 items (12 cocktails, 25 spirits, 6 beer/cider, 3 wine, 4 zero-proof), 0 differences, 0 extra items. Every spirit sensory string is present in page text. 11.5 prints as "11.50". |
| Proposed key | **Pass**: a hairline ring after the price on every `PROPOSED_needs_rob_approval` / `rob_reference_image` row (the DOM check confirms ring ⇔ status). Key "◦ proposed — pending approval" on both pages and the phone. |
| Price within 1 em of name on the same line | **Pass**: max gap 0.42 em on letter and phone. The last name word and price are bound with a no-break space, so a price never wraps alone. |
| WCAG ≥ 4.5 at the worst pixel | **Pass**: minimum 6.72 (muted grotesk on paper) on the front, back and phone. Badges on the field ≥ 16.0; ink-band text ≥ 10.4. Method: text-free re-render at 300 dpi, each line box narrowed to its ink box, every background pixel tested. |
| Legibility | **Pass**: letter minimum 9.0 pt (≥ 8.5); phone minimum 12 css px. |
| Ingredients in role order; garnish separate | **Pass**: printed order equals the manifest order (already base → modifier → sweetener → citrus → bitters → lengthener). The garnish is only in the garnish · glass line. |
| No taglines or banned filler | **Pass**: 0 hits against the banned list (Rob's four removed lines, "Good drinks / Good people", the selected tagline, and the Glass Garden/Solstice slogans). The only venue line is "Cantina & Cocktail Bar · Iowa City, Iowa". |
| Safe area 0.5 in | **Pass**: the closest text line box to the trim is 0.50 in (top and bottom), 0.51 in left, 0.59 in right. |
| Bleed PDF 3.175 mm | **Pass**: `menu-print-bleed.pdf`, 2 pages at 9.25 × 11.75 in, trim at 0.375 in with crop marks. The front field bleeds 9 px (3.175 mm) top and right; the back band bleeds top, left and right; the paper ground carries a 9 pt bleed. |
| Formats | **Pass**: front and back are 2550 × 3300; phone is 1170 × 18831 (one scroll, no horizontal scroll). All text is live HTML; no raster text. |
| No block overlap | Back groups → beer 10 px, band → groups 12 px, front index → zero-proof rule 36 px. |

## visual_tests.py

| | salient regions | primary area % | primary : secondary | accent % |
|---|---|---|---|---|
| front | 4 | 20.9 | **21.5** | **14.7** (all inside the field) |
| back | 10 | 15.1 | 200 (the ink band; nothing competes) | 0 |

- Front/back silhouette correlation: 0.49.
- The front's primary region is the smoky/rich half of the field. The yellow half sits within 0.18 luminance of the paper, so the squint tool does not count it. By eye, the whole field reads as one plate.
- The front accent of about 15% sits in the gesture, the same pattern as Glass Garden and Solstice (about 12%).

## Open items

- **Placeholder data:**
  - Mezcal prices are manifest placeholders.
  - Regions shown as "—" are null in the manifest ("verify before print").
  - Oak ages are class-level (NOM-006 classes), not per expression.
- **Coordinates** are PHG's reading of draft sensory lines that are marked `draft_not_tasted`. They should be re-plotted after a tasting.
- **Zero-proof** is not plotted, because the manifest has no ingredients for it.
