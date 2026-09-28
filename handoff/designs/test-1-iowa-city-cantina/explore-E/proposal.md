# Explore-E: RÓTULO (divergent concept E of 6)

**Creative thesis:** The menu is a painted shop front: every section is its own enamel sign board, and bold shaded
sign-writer lettering carries the whole design, so a guest reads it the way they'd read a street from across the road.

**Concept words:** painted · loud · vernacular · enamel · shaded · joyful
**Avoid-list:** lotería cards, papel picado, cut-paper sun, torn rail, vertical CANTINA, botanical/agave illustration,
editorial hairlines, gold leaf, AI raster art, trademarked IP, invented facts in taglines.

## Why this is the opposite of rounds 1-18
| Rounds 1-18 | Explore-E |
|---|---|
| Quiet editorial page, one menu column beside an art rail | No art rail. The page is a wall of five flat-colour sign boards |
| Illustration carries the mood (lotería, papel picado, sun, torn paper) | No illustration at all. The lettering carries the mood (shaded, outlined, stacked shadows) |
| Vertical wordmark | Horizontal shaded marquee wordmark on a red board |
| Hairline rules, price column, small serif ingredients | Price in a painted starburst (cocktails) or oval (everything else); ingredient lines in caps `+` notation |
| Muted or dark grounds | Saturated enamel: red, yellow, cobalt, green, black |

## Pipeline
- ART layer: CSS/SVG only (no Canva raster needed). Painted-wall trim (green band + cream + red pinstripe) is a `::before`
  box set 12 px (3.2 mm) past trim, so it bleeds more than 3 mm. The panels, keylines, bursts and ovals are CSS/SVG.
- TEXT layer: all HTML from `../build/draft_doc.json`. No text is baked into any image.
- Fonts: local `../build/fonts` (Fraunces 700 for sign lettering and prices; DM Sans 500/700 for items).

## Layout geometry (letter, 612 x 792 pt; CSS px x 0.75 = pt)
- Safe margin 48 px = 36 pt all sides. Measured: no text box outside the 48-768 x 48-1008 px box.
- Stack: marquee 48-186 · COCKTAILS board 196-559 (two columns, 2x2 cards) · Beer | Wine | Spirits row 569-859
  (three columns, 232 px each, 12 px gutters) · Cider strip 869-937 (slack spread by `space-between` in the final pass,
  so the numbers shift slightly; the order and grid are unchanged).
- Boards: 4 px white keyline + 3 px ink outline, 12 px radius. Sign heads are Fraunces 700 32 px, white fill, 2 px ink
  stroke, stacked 2/4/5 px ink drop shadow. Wordmark 90 px yellow, ink stroke, ink/white/ink stacked shadow.
- Items: name DM Sans 700 18 px (15.5 px in the three-column row), tracked 1-1.6 px; spec DM Sans 500 13-13.5 px
  caps; serve cue DM Sans 700 12.5 px in yellow.
- Prices: cocktails in a 62 px 14-point SVG starburst (yellow, ink stroke, 3 px ink drop shadow), Fraunces 30 px ink;
  other items in a 48 x 36 px yellow oval, Fraunces 22 px. Every price sits on its item's row and is vertically
  centred on it (flex row), so it can't read against a different item.
- Palette: red #B8102A, yellow #FFC414, cobalt #173E9A, green #0B6135, ink #1B1512, white #FFFFFF, wall #F4EAD3.
- Phone: 390 css px at 3x = 1170 wide. Single column, all boards stacked, wordmark 58 px, body 14 px.

## Contrast (worst pixel)
Method: text-free render vs. full render. The ink mask is the pixels that differ, dilated about 2 css px, and every
text-free background pixel under the mask is checked against the text colour.
Letter minimum by role: serve 6.00 (yellow on cobalt), name/spec 6.68 (white on red), price 11.32, pill/tab 18.06.
The outlined sign lettering (wordmark, board heads) is measured fill against its own ink outline: wordmark 11.32,
heads 18.06. Gate 4.5:1 passes.
Legible at 1 m: the smallest body text is 12.5 px = 9.4 pt caps (serve cue); specs are 13-13.5 px caps.

## Content and sources (14 items, verbatim names and prices)
Manhattan 15 · Margarita 15 · House Daiquiri 14 · Brown Butter Old Fashioned 16 · Czech Pilsner 7 · Dry-Hopped IPA 8 ·
Amber Lager 7 · Malbec 12 · Pinot Grigio 11 · Brut Rosé 13 · Blanco Tequila 12 · Añejo Tequila 16 · Cognac VSOP 18 · Dry Cider 8.
- Cocktail lines come from the draft components (quantity + unit + name). Garnish components move to the serve line.
  The Manhattan's aromatic bitters are hidden (meta.public_components). The Old Fashioned shows no quantities because
  its public_visibility.house_recipe is false. "Juice" is dropped from "Fresh Lime Juice", as in round 17.
- Serve lines (method · glass · ice · garnish) come from phg.recipe_versions, as cited in ../round-17/proposal.md.
- Beer, wine, spirits and cider use the full draft description text, set in caps.
- Taglines: the only one is "¡SALUD!" (generic brand voice, no item facts).
- Library references: none newly queried for this exploration. The quality bar is Rob's refs (ref-01, ref-02 opened);
  this concept deliberately departs from their editorial language.

## Restraint pass
Devices considered (12): 1 painted-wall trim · 2 marquee board · 3 shaded wordmark · 4 pill badges · 5 shaded sign
heads · 6 white sub-tabs · 7 starburst prices · 8 oval prices · 9 dashed row rules · 10 yellow serve cue · 11 footer
tagline pill · 12 dark header plate behind sign heads.
Removed (3, 25%): 11 footer pill (moved "¡SALUD!" into the marquee), 12 dark plate behind heads (fought the shadow),
and a planned hand-drawn arrow/pointing-hand ornament (decoration with no information).
Kept: each remaining device either carries hierarchy (3, 5, 6), ties prices to items (7, 8, 9), or is the thesis (1, 2).

## Revision log
- R1 hypothesis: two-by-two lower boards. Overflowed by 318 px. Fix: bursts moved to the right of the card, three-column row.
- R2: fits. Cider head was red fill (2.71 against its outline), so it became white fill with red and ink shadows.
- R3: 71 px slack spread evenly, wordmark 74 to 90 px. Best-so-far on every criterion; nothing regressed.

## Open questions
- Is "CANTINA / & COCKTAIL BAR / IOWA CITY, IOWA" still the correct venue name block? It's carried from the earlier rounds.
- Should the house-recipe quantities for the classics (Manhattan, Margarita, Daiquiri) appear on a guest menu? They
  are public per the draft visibility flags, but Rob should confirm.
