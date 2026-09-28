# TEST-1 explore-B: "Courtyard" (Mexican modernism, after Barragán's flat-plane architecture)

**Thesis (one sentence):** The page is built like a sunlit courtyard: flat walls of rosa, marigold and cobalt enclose a pale plaster floor, and every word sits calmly in the light.

**Concept words:** plane, wall, light, stillness, geometry, colour.
**Avoid-list:** lotería, papel picado, cut-paper sun, torn or rough edges, vertical wordmark, illustration, ornament, texture, script type, cacti/agave drawings, trademarked worlds.

## Why it is the opposite of rounds 1-18
| Rounds 1-18 | explore-B |
|---|---|
| Folk-craft illustration: lotería, papel picado, cut-paper sun | No illustration at all. The art layer is 5 flat CSS planes |
| Torn rail, hand-made edges | Hard, straight architectural edges and one hard diagonal shadow |
| Vertical CANTINA wordmark on a side rail | Horizontal, widely tracked wordmark set into the rosa wall |
| Serif display plus italic taglines, busy rails | One family (DM Sans 400/500/700), 3 short generic taglines |
| Warm, textured, dense | Cool and serene: big empty wall, still water, lots of air |

## Geometry (letter, CSS px at 96/in; 816x1056 = 8.5x11 in; rendered at 3.125x = 2550x3300)
- Safe margins 48 px (36 pt) on all sides. All text sits inside x 48..768, y 48..1015.
- ART (CSS, text-free, full-bleed planes run 12 px, about 3.2 mm, past trim):
  rosa wall #C2185B x0..816, y0..270; marigold sun block #F2A93B x576..816, y0..172; one hard shadow #7E0E3E,
  polygon (576,172)(816,172)(816,270)(674,270); cobalt wall #1D3A8A x528..816, y270..960; still water #A9D0CF y960..1056
  with a 1 px cream waterline at y982; plaster floor #F5EEE2 everywhere else.
- Grid: 2 columns. Left (plaster) x48..492, 444 wide: Cocktails, Spirits. Right (cobalt) x560..768, 208 wide: Beer, Wine, Cider.
  Measured: left column y304..937, right y304..850; title y72..181; motto x600..768, y48..94; footer y1000..1015.
- Type: DM Sans (local, ../build/fonts). Wordmark 74 px/500/tracking .2em; section heads 15 px/700/.32em with a 14 px marigold
  square; subheads 11.5 px/700/.28em; item names 16 px/700/.12em caps; prices 17 px/700 tabular; descriptions 14 px (13.5 px on
  cobalt)/400, line-height 1.4. Smallest text 11.5 px = 8.6 pt (subheads, taglines, all tracked caps); items and prices are 12-12.75 pt.
- Price tie: each price sits on the name's baseline row (measured offset <= 1 px) joined by a 1 px leader rule at 35% opacity.
- Phone (390 CSS px at 3x = 1170 wide): the same planes become a walk through the courtyard, stacked: rosa (title), marigold
  (motto), plaster (cocktails, spirits), cobalt (beer, wine, cider), water (footer). 24 px side margins.

## Contrast (flat planes, no texture, so the plane is the worst pixel; WCAG ratio)
cream on rosa 5.45 · ink on marigold 8.55 · ink on plaster 14.81 · rosa-ink subheads on plaster 6.63 · cream on cobalt 9.63 ·
marigold subheads on cobalt 5.19 · navy on water 7.61. All >= 4.5. No text sits on the shadow.

## Copy and sources
- 14 items, names and prices exactly from ../build/draft_doc.json (build.py asserts 14 and reads prices from the draft).
- Cocktail sentences use only the draft components plus glass, garnish and method from phg.recipe_versions, as cited in
  ../round-17/proposal.md: Margarita rocks / lime wheel / shaken (f06abb74); Manhattan coupe / cocktail cherry / stirred
  (9fb77eaa); Old Fashioned rocks / large cube / orange peel / stirred (7095fd3d); Daiquiri coupe / lime coin / shaken (14d45e57).
- Manhattan: aromatic bitters left out (meta.public_components {"aromatic-bitters": false}).
- Quantities, units and roles set the order of the ingredients (base spirit first, then modifiers by role and quantity). Ounces are
  not printed: the Old Fashioned has public_visibility.house_recipe = false, and printing specs for three drinks but not the fourth
  would be inconsistent. If Rob wants ounces, the three open recipes can carry them.
- Beer, wine, spirits and cider print the draft desc in full.
- Taglines are generic brand voice only: "Good drinks / Good company", "Sit in the light", "Salud".

## Devices and restraint pass (1c)
Considered: 1 rosa wall · 2 marigold block · 3 hard shadow · 4 cobalt wall · 5 still water · 6 waterline · 7 marigold square
before section heads · 8 leader rules · 9 motto · 10 footer taglines · 11 section intro lines (draft section desc) ·
12 a second water pool behind the title · 13 thin frame round the page.
Removed (about 25%): 11 (repeated what the headings say), 12 (a second pool broke "one still water"), 13 (a frame is ornament;
the walls already frame). Kept items trace to the thesis: walls, shadow and water are the courtyard; squares and leaders are the
only marks and are needed for wayfinding and price tie.
Revision hypothesis (round 1 of this concept): lowering the wall from 300 to 270 px and tightening the rhythm keeps the left
column off the water (fit went from 1016 to 937 px) with no type reduction.

## Flags (needs_input stays open from round 17)
Venue name "Cantina & Cocktail Bar, Iowa City" follows round 16/17 (draft title is "Bar menu"). Wine producer, region and bottle
prices are not in the draft, so wine prints name + draft desc + one price. Brut Rosé price label is empty, so it prints unlabelled.

## References
Library menus (menu_visual_documents.id): 572, 7923, 4969, 208 (as cited in round 17). Quality bar: Rob's references
ref-02 (restrained tracked caps, price near name) and ref-05 (editorial item format).
Art: no Canva commission needed; the planes are CSS.
