# TEST-1 explore-D: "Field Guide to the Bar" (botanical plate / apothecary)

**Thesis (one sentence):** The menu is a naturalist's field guide: each cocktail is an engraved specimen plate that dissects the drink into its measured parts, and every other pour is catalogued in a numbered register.

- **Concept words (6):** specimen plate · line engraving · measured · catalogued · aged ivory · sepia ink
- **Avoid-list:** everything from rounds 1-18 (lotería, papel picado, cut-paper sun, torn rail, vertical CANTINA, agave rosette art, gold); fiesta colour; any lettering inside the art; invented Latin (lime, orange and vermouth carry none because the species or source is not certain); invented ABV, region, brand or pour; trademarked worlds.

## Why this is the opposite of rounds 1-18
| Rounds 1-18 | explore-D |
|---|---|
| Warm dusk palette, gold sun, painterly or cut-paper raster art | Three inks only: ivory #F4EDDC, sepia #3A2716 / #5E4630, one botanical green #34502F. No gradient art and no raster. |
| Art sits in a rail, text sits in a column | The art is the content: each glass diagram carries the ingredients through callout leaders |
| Vertical wordmark, torn edge, cultural motifs | A horizontal tracked title, a double-rule plate frame, specimen numbers, and data tables |
| Ingredients shown as one `a · b · c` line | Every component with its quantity, unit and role, plus a graduated ½ oz scale drawn to proportion |

## Device → thesis trace (restraint pass, scorecard 1c)
Before the pass (12 devices): 1 double-rule page frame · 2 tracked title · 3 key box · 4 plate frames (double) · 5 engraved glass per plate · 6 graduated oz scale · 7 callout leaders (green for garnish) · 8 Latin names · 9 Glass/Garnish/Ice/Method table · 10 serve line (draft serve_format) · 11 specimen numbers 01-14 · 12 register with ruled missing-fact fields.
Removed (3, 25%): a foxing/stain overlay (it lowered contrast near text), a corner-tick ornament on each plate (it repeated device 4), and a bottom "botanical sprig" illustration (a second illustration grammar that carried no data). Everything that is kept carries data or navigation.
Revision hypothesis (r1 to r3): the first render let fonts fall back, overflowed the proof register past the footer, and pushed the Old Fashioned price outside its plate. Loading the fonts from file, using equal minmax grid columns, wrapping long names and a 146 px diagram body fixed all three without losing any component.

## Layout geometry (letter 8.5x11 in, 816x1056 CSS px, rendered at 3.125x = 2550x3300)
- Frame: double rule inset 40 px. Content padding 48/54 px, all text ≥ 48 px (36 pt) from trim. Footer text sits at y 990-1006.
- Header y 48-136: kicker DM Sans 700 10 px tracked .32em green; title "BAR MENU" (draft title) Fraunces 700 36 px tracked .34em; the key sits at right, DM Sans 9.5 px.
- Cocktails: a 2x2 grid of equal columns (341 px each, gap 14 px), plates at y 161-433 and 441-705. Plate = header (plate no. / sub), name row (Fraunces 700 15 px caps .1em, dotted leader, price Fraunces 700 19 px), diagram body 146 px (glass at x 4-94 scaled .82, oz scale at x 108, labels from x 150; labels Fraunces 12.5 px, role DM Sans 9.5 px), data table DM Sans 8/11 px, serve line Fraunces italic 11 px.
- Register y 730-977 (proof) / 925 (guest): 3 equal columns Beer+Cider | Wine | Spirits; name Fraunces 700 13.5 px caps .12em, price 15 px with a dotted leader, desc italic 11.5 px, proof fields DM Sans 8.5 px.
- Phone: 390 CSS px x3 = 1170 px wide, single column, the same components.

## Accuracy (all 14 draft items, prices exact)
Manhattan 15, Margarita 15, House Daiquiri 14, Brown Butter Old Fashioned 16, Czech Pilsner 7, Dry-Hopped IPA 8, Amber Lager 7, Malbec 12, Pinot Grigio 11, Brut Rosé 13, Blanco Tequila 12, Añejo Tequila 16, Cognac VSOP 18, Dry Cider 8.
- Components (name, quantity, unit, role, prep note) come from draft `components`. Manhattan aromatic bitters are hidden (meta.public_components). The Old Fashioned has `public_visibility.house_recipe = false`, so its **quantities are withheld** and no scale is drawn; the ingredients and roles still show. **Please confirm this reading with Rob.**
- Glass, garnish, ice and method come from phg.recipe_versions (9fb77eaa, f06abb74, 14d45e57, 7095fd3d; cited in ../round-17/proposal.md). The "Serve:" lines are the draft meta.serve_format verbatim. The Margarita field note is from its draft desc.
- The Latin names are used only where the product's botanical source is certain: Agave tequilana (tequila), Agave (agave syrup, genus), Secale cereale (rye), Zea mays (bourbon), Saccharum (rum, genus), Vitis vinifera (Malbec, Pinot Grigio, Cognac), Humulus lupulus (dry-hopped IPA), Malus (cider). There is none on lime, orange, vermouth, the lagers or the rosé.
- Beer, wine, spirits and cider print their draft desc in full. Missing facts (brewer, producer, region, brand, ABV, pour) are ruled "—" fields in the **proof only** (menu.html / preview-letter.png / preview-phone.png). The guest version (menu-guest.html / preview-letter-guest.png) omits them.
- Venue line "Cantina & Cocktail Bar · Iowa City" is carried over from round 17. The footer shows the draft subtitle.

## Hard gates
- Contrast (worst pixel, text-free render, each text box checked): letter proof min 6.57, guest min 6.57, phone min 6.55 (contrast.json).
- Every price sits on its item's name row with a dotted leader. The smallest price is 15 px (11 pt), and item names are 13.5-15 px.
- The 36 pt safe margin holds, and nothing overflows (geometry in contrast.json).

## Open questions (needs_input)
1. Does house_recipe=false on the Old Fashioned mean its quantities stay hidden? (It is assumed hidden here.)
2. Brewer, producer, region, brand, ABV and pour size for items 05-14.
3. Is the Brut Rosé price for a glass or a bottle?

## References
Rob's quality bar is handoff/designs/references/rob-2026-09-28/ (ref-01 for the tracked caps with ingredient line and one price column; ref-05 for the parchment cards and specimen/prop voice). The PHG library was not queried in this 12-minute exploration, so there are no library document IDs. The Coordinator should treat that as a gap.
