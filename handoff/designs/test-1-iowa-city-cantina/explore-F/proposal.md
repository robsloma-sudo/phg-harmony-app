# TEST-1 explore-F: "Under the Same Moon" (immersive night scene), Cantina & Cocktail Bar, Iowa City

needs_input = true (same open questions as round 17: spirits brand/age/pour, beer/cider producer + ABV, wine producer/region,
Brut Rosé glass or bottle label, Old Fashioned dairy note). Proposal only; create-only; not committed.

## Creative thesis
**Late at night the agave field is quiet under a full moon, lanterns glow on the adobe wall, and the menu hangs in the scene like
lamp-lit parchment you walk up to.**

- Concept words (6): moonlight · agave field · lantern glow · fireflies · parchment in the dark · cinematic
- Avoid-list: lotería, papel picado, cut-paper sun, torn rail, vertical CANTINA (all of rounds 1-18); sombreros, skulls, cacti clip-art;
  lettering inside the art; trademarked worlds; neon; taglines that state item facts.

## Why this is the opposite of rounds 1-18
| Rounds 1-18 | Explore-F |
|---|---|
| Light cream editorial page, art confined to a rail | Dark full-bleed illustrated world; the page *is* the scene |
| Warm daytime/dusk sun, gold disc | Cold indigo night, full moon, warm light only from lanterns |
| Flat cut-paper / folk-card grammar | Layered atmospheric depth (sky, mesas, haze, wall, 3 agave rows, fireflies) |
| Vertical CANTINA wordmark in a rail | Horizontal CANTINA on a hanging wooden sign (a prop) |
| Taglines on section rules / rail | Taglines painted on props: lantern tag + field board |
| Calm, airy | Moody, dramatic, glowing cards |

## Layout geometry (letter 8.5x11 in; CSS px = 1/96 in; render 3.125x = 2550x3300)
- Page 816x1056; safe margin 48 px (36 pt) all sides; art bleeds 12 px (3.2 mm) past trim (sky + ground SVGs at -12 px).
- Grid: 720 px live width; cocktails card full width x48 y170 w720 h322 (2 columns, 30 px gutter); row of three cards y512, w230,
  x = 48 / 293 / 538 (15 px gutters): Beer+Cider h354, Wine h275, Spirits h312. Lowest card edge 866 < 1008.
- Props: wordmark sign centered, top 40, rotated -1.2 deg, hung on two ropes; lantern post x292 bottom 30; tag x362 bottom 52 (-5 deg);
  board right 70 bottom 62 (+2 deg) on a post. Moon cx676 cy118 r50 with halo.
- Palette: sky #070a22 -> #141a4a -> #262a62; adobe #4a3547/#2a1f33; agave #243a5a / #1d3550 / #0e1b2c, moon rim #b4c6f0;
  lantern #ffc56b/#ff9a3d; parchment #f1e6ca -> #e8d9b4; ink #2a1c12 / #4a3522; serve line #6a4020; wood #4b2e1c/#3a2214; cream #f6e9c9.
- Type: Fraunces 700 (wordmark 52 px tracked .34em, card heads 25 px .2em), DM Sans 700 names 15 px tracked .12em caps, Fraunces 600
  ingredients 14 px, Fraunces 600 italic serve/description 13.5-14 px, Fraunces 700 prices 17 px, DM Sans 500 sub-heads 12 px.
- Phone (390 CSS, 3x = 1170 wide): sign, cards stacked 18 px side margins, cocktails single column, ground scene + props at foot.

## Item format and sources (all from ../build/draft_doc.json; 14 items, prices exact; build.py asserts parity)
- Cocktails: NAME ····· price, then `qty unit ingredient · ...` from draft components (quantity/unit), then italic serve line
  `method · glass · garnish` from phg.recipe_versions as cited in ../round-17/proposal.md. Manhattan omits aromatic bitters
  (meta.public_components {"aromatic-bitters": false}); its cocktail cherry (component role Garnish) moves to the serve line.
  Daiquiri prints "house demerara syrup" (draft desc wording; component role House prep).
- Beer, cider, wine, spirits: the draft description in full (e.g. "Hop-forward draft IPA.", "VSOP Cognac pour.").
- Taglines (props only, generic): "GOOD DRINKS / GOOD COMPANY" (lantern tag), "UNDER THE SAME MOON" (board). Sub-line on the sign
  "Cocktail Bar · Iowa City" is the venue descriptor used since round 1.

## Gates
- Contrast: every text sits on an opaque parchment card or wood prop. Worst sampled text-box background in the render: 5.94:1
  (12 px sub-heads #6a4a2a on parchment); body ink #2a1c12 on #e8d9b4 about 13:1; cream on wood about 10:1.
- Prices: each on the name row, joined by a dotted leader. Legibility at 1 m: names 11.25 pt caps, prices 12.75 pt, ingredients 10.5 pt.
- 36 pt margins: asserted in build.py for all cards; props inside the live area.

## Restraint pass (devices listed, ~25% removed)
Kept: 1 moon + halo, 2 star field, 3 adobe wall with 3 lanterns, 4 three-row agave field, 5 fireflies, 6 parchment cards with lantern glow,
7 hanging wordmark sign, 8 lantern tag tagline, 9 field board tagline, 10 dotted price leaders, 11 sub-head rules.
Removed: section-rule taglines (props carry voice), front-layer agave overlapping cards (would crowd text), a second hanging sign,
decorative corner ornaments on cards. Revision hypothesis this round: moving the lantern out of the Beer card's path and lifting the
near agave row (it read as black lines) increases scene depth without touching text.

## References
Rob 2026-09-28 ref-05..09 (Greenhouse series: immersive world, cards on the illustration, props carry taglines), ref-06 opened.
Library document IDs: none queried this round (time box); facts come from draft_doc.json and round-17's logged recipe citations.
Art layer is SVG (text-free); if a raster is wanted, Canva prompt: "Moonlit blue agave field at night, low adobe wall with three warm
hanging lanterns, fireflies, deep indigo sky, full moon upper right, painterly cinematic, no text, no letters, no signage, calm open
space in the upper-middle two thirds."
