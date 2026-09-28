# TEST-1 explore A: "Price Is the Picture" (brutalist typographic poster)

**Creative thesis:** A Mexico City gallery-poster sheet where the numbers do the shouting: prices set as giant black grotesk numerals on a safety-orange field, every drink reduced to its honest spec on a hard Swiss grid.

**Concept words:** blunt, numeric, spec-sheet, gallery poster, orange, ruled.
**Avoid-list:** illustration of any kind, lotería, papel picado, cut-paper sun, torn rail, vertical wordmark, serif display, script, texture, gradients, generated art.

## What makes it the opposite of rounds 1-18
Rounds 1-18 were illustrated, warm and editorial (Fraunces serif, a vertical CANTINA, cut-paper and folk-art devices, the price as a quiet column). This one has **no art layer at all**: the grid and type carry everything. The wordmark is horizontal and cropped tight, the palette is three flat colours, the type is grotesk plus mono, and the price is the biggest object on the page instead of the smallest.

## Geometry (letter portrait, 816x1056 CSS px = 8.5x11 in; exported at 3.125x = 2550x3300)
- Margins: 48 px (36 pt) on all sides; text-box check reports 0 elements outside the safe zone. The orange band bleeds to the trim on left and right (it is a flat field, not art).
- Grid: 12 columns, 720 px measure, 12 px gutter. Cocktail rows are 232 | 1fr | 214 (price | spec | serve), which is deliberately off-module against the 3-column lower zone (Beer+Cider | Wine | Spirits) for tension.
- Palette: ink #0D0D0D, paper #F1EEE6, safety orange #FF5A1F. Orange is only ever a field, never text colour.
- Contrast (flat fields, so the worst pixel equals the field): ink on paper 16.76:1; ink on orange 6.23:1. Both pass 4.5:1.
- Type (system fonts only, no Google): Liberation Sans Bold (Helvetica-metric grotesk) for the wordmark (108 px, -0.065em), cocktail prices (122 px), other prices (40 px), names (19 px / 13 px tracked caps); Liberation Mono for specs (13 px), serve data and descriptions (12 px). Minimum text 10.5 px caps labels; item text is 12 px or larger, so it reads at 1 m.
- Positions: masthead y 48-150 with a 10 px rule; cocktails band y ~160-700; lower zone y ~710-983; footer rule y 987; footer text ends at y 1008.
- Price-to-item tie: each price sits in the same ruled row as its name, directly left, with a 6 px vertical bar (cocktails) or a 2 px row rule (lower zone).
- Phone (390 CSS px, 1170 px export): one column; cocktail serve data drops under the spec.

## Data used (all from build/draft_doc.json, 14 items; prices unchanged)
- Cocktail specs come from the draft `components` (quantity, unit, name). The Manhattan hides Aromatic Bitters (`meta.public_components`), and the Cocktail Cherry (role Garnish) moves into the GARNISH field.
- **The Old Fashioned prints ingredients with no quantities** because its `public_visibility.house_recipe` is false. Needs Rob's call: if the flag should allow quantities, the build prints 2 oz / ¼ oz / 2 dash automatically.
- Glass, garnish and method come from the phg.recipe_versions rows cited in ../round-17/proposal.md (f06abb74, 9fb77eaa, 7095fd3d, 14d45e57). Quantities show as ¾, ½ and ¼ for 0.75, 0.5 and 0.25.
- Daiquiri: "house demerara syrup" is the draft desc's wording for the Demerara Syrup component.
- Beer, wine, spirits and cider print the full draft desc. The section desc "Classic and house cocktails." and the subheads (Classics, House Originals, By the Glass, Sparkling, Agave, Brandy) come from the draft.
- "CANTINA / & COCKTAIL BAR / IOWA CITY, IOWA" is carried over from the round-16 title (the draft title is "Bar menu", which also prints). The subtitle "PHG Publishing Beta · Test Content" prints in the footer. The only tagline is the generic "GOOD DRINKS / GOOD COMPANY".
- Library references (inherited from round 17, not re-queried in this 12-minute pass): 572 and 7923 (Coa Cantina, Iowa City, for the local price band).

## Restraint pass
Devices: 1 horizontal cropped wordmark, 2 masthead rule, 3 orange band, 4 giant cocktail numerals, 5 vertical price bar, 6 section index numbers, 7 serve-data table, 8 heavy lower section bars, 9 row rules, 10 mono spec type, 11 footer tagline, 12 subhead labels.
Removed (25%): a second accent colour, rotated section labels, a big "$" glyph, and a half-tone numeral outline. Every one fought the numerals. Kept: everything above, because each one either carries data or ties a price to its item.

## Revision hypothesis (round 1)
Taking the art out completely and putting all the scale into the prices should score high on criterion 16 (thesis) and on legibility. The risk is hospitality warmth, so reviewers may read it as cold.

needs_input: false for this sheet. Open questions: the Old Fashioned house_recipe flag, and the venue name (see above).
