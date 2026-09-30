# TEST-1 expanded: three high-concept directions (brief v1, 2026-09-28)

Rob: "Think outside the box … upper-echelon, high-concept design theory … expand the cocktails and descriptions … about 25 spirit pours."

## Why rounds 17–20b plateaued near 70

Every one of them was the same object: *an illustration on the left, a list on the right.* We polished its typography for four rounds. The handoff's central lesson (§0, §6.4) is that **the concept must govern the geometry and the reading path.** Art behind or beside rows is decoration.

A second point is a craft decision. Code-drawn *pictures* (suns, agaves, soil) have hit a ceiling. Code-drawn *systems* (maps, charts, diagrams, typographic structures) are where code is at full strength: vector-exact, infinitely crisp, data-true. So each direction below makes its image **a functional carrier of information** (handoff §0, 01 MISSION). The art is built from the menu's own data, not painted around it.

## Locked content

`manifest.json` in this folder (sha256 prefix is recorded in the changelog).

**Content rules:**
- 12 cocktails, 25 spirit pours, 6 beer/cider, 3 wine, 4 zero-proof.
- Every row carries a `status`. Rows marked `PROPOSED_…` or `rob_reference_image` are proposals.
- Each design must include a small, quiet key: "◦ proposed — pending approval". The mark can be a hairline ring, not a shout.
- **Never alter a name, price or ingredient.** Never add items.

**Item stack (binding):**
1. Name + price.
2. Sensory line in a different treatment.
3. Ingredients in role order.
4. Garnish · glass.

**Mini glass glyphs:** Rob asked for small drink illustrations showing the actual glass, colour, ice and garnish. Draw them only from the manifest's glass and garnish fields, as a simple coded family: rocks, highball, coupe, plus an ice cue and a garnish cue. Liquid colour comes only where the ingredients make it obvious (Campari → red, espresso → dark, jamaica → magenta); otherwise use a neutral tint.

**Formats:**
- Letter, 2 pages: a front with cocktails and zero-proof, and a back with spirits, beer, cider and wine. Render each at 2550×3300.
- Phone: 1170 wide, one scroll.
- Never lower the resolution.
- Exact HTML/SVG text. No text in any raster.

## Theory the directions must use (KB keys in brackets)

- **Creative thesis first** (`creative_thesis_required`, `concept_before_decoration`): one sentence that generates decisions.
- **Structure is the concept** (handoff §6.4): item clusters live *in* the image's geometry, and name/price/sensory/ingredients never separate.
- **Information design as aesthetic** (Tufte VDQI: data-ink, small multiples, micro/macro readings): the page reads at arm's length as one image and at reading distance as exact data.
- **Hierarchy is finite** (`hierarchy_not_everything_loud`, `contrast_is_finite_resource`, `accent_requires_scarcity`): one dominant field. Rob's preferred references (Glass Garden, Solstice) measure a primary:secondary of about 11–17 with about 12% accent *concentrated in the gesture*.
- **Style is not costume** (`style_not_costume`, `literal_motif_budget`, `abstraction_reduces_cliche`):
  - No sombreros, cacti, papel picado, sugar skulls or serapes.
  - At most one literal motif per direction.
  - Mexico and Iowa must appear as *systems* (agriculture, geology, time, measurement), not stickers.
- **Process breadth** (`process_breadth_before_refinement`): the three directions must differ in grayscale silhouette. I will check with visual_tests.py, and correlation must stay below 0.5 between directions.
- **Zero slogans or taglines.** Venue line only: "Cantina & Cocktail Bar · Iowa City, Iowa".

## Direction K1: HILERAS (the field survey)

**Thesis:** *Iowa corn and Jalisco agave are both row crops. The menu is one field seen from the air, and every drink is planted in its row.*

**Structure:** horizontal bands. The page is an aerial survey plate:
- Contour-ploughed strips (Iowa) curve and lock into straight agave hileras (Jalisco).
- Each strip *is* a section band. Items sit *on* the furrow lines as the baseline; the ruling of the field is the typographic grid.
- The back page is the **spirits survey table**: a Tufte-style data table of the 25 pours. Columns are class, NOM, region and a tiny inline "age bar" (0 → 36 months of oak; blanco is a dot, reposado a short bar, añejo a long bar) plus the price.
- A legend, scale bar and north arrow sit in the margin.

**Palette:**
- Aerial earth: loam, agave blue-green, corn-stubble straw.
- One accent: survey-red for prices and the scale bar.

**Precedents** (for the transferable principle only; copy nothing):
- USGS/USDA aerial survey plates.
- Swiss topographic maps (Imhof relief shading).
- Tufte's small multiples.

## Direction K2: EL RELOJ (the sun clock)

**Thesis:** *A cantina runs on the sun. The menu is one evening, from first light at 5 pm to last call, and every drink sits at its hour.*

**Structure:** a great arc or dial.
- The front is a sundial or ecliptic. A single huge arc sweeps the page, with hour ticks (5 pm … 2 am).
- Cocktails cluster at the hour they belong to: aperitivo (Ranch Water, Paloma), dinner (Margaritas, Negroni), after dinner (Carajillo, Old Fashioneds).
- Text stays horizontal. The clusters step down along the arc, so the reading path *is* the evening.
- The back is the night: the 25 pours as a star chart or ladder ordered by time in oak, with blanco at dusk and añejo at midnight. The age in months is the vertical position.

**Palette:** dusk gradient from warm paper to ink-indigo, and one gold for the sun/hour marks and prices.

**Precedents:**
- Astronomical instruments and volvelles.
- Herbert Bayer's diagrams.
- The Aztec sun stone is **not** to be copied or quoted. It is used only for the principle of a calendar as structure.

## Direction K3: MAPA DE SABOR (the flavor field)

**Thesis:** *The guest's question is "what does it taste like?", so the menu is the answer drawn as a field.*

**Structure:** a two-axis map as the hero.
- The front is a large plotted field with the axes **bright ↔ rich** and **clean ↔ smoky**. Each cocktail is a numbered point with its glass glyph, positioned from the manifest's sensory and ingredient data. Record the coordinates and the reasoning in the proposal; this is a PHG-inferred placement, labelled as such.
- An index column keys the numbers to the full item stack (name + price / sensory / ingredients / garnish · glass).
- The back is small multiples: 25 pours as a grid of identical micro-cards, each with the same four data marks (class, oak age bar, region, price), grouped blanco / reposado / añejo / mezcal / house.

**Typography-led:**
- A strict Swiss grid.
- One grotesk plus one text serif.
- Large numerals as the only display type besides the wordmark.

**Palette:** paper plus ink plus one field colour gradient (bright citrus-yellow to smoke-charcoal) used only inside the map.

**Precedents:**
- Swiss International Style (Müller-Brockmann grids).
- Isotype (Neurath/Arntz).
- The flavor-wheel tradition, with the principle of plotting taste; do not copy any wheel.

## Hard gates (all directions)

- Every name, price and ingredient matches manifest.json exactly (DOM text diff).
- Each price sits within 1 em of its name on the same line, *or* in a true aligned column with a guide.
- WCAG contrast of at least 4.5 for body text over its actual background, measured at the worst pixel.
- Legibility at actual size: letter ≥ 8.5 pt body; phone ≥ 12 px.
- Ingredients follow role order; garnish is separate.
- No taglines, and none of the banned filler lines.
- Text inside a 0.5 in safe area; bleed PDF with 3.175 mm bleed.

## Deliverables per direction

The folder is `explore-K1` / `explore-K2` / `explore-K3`, containing:
- `build.py`
- `menu.html`
- `preview-front.png` and `preview-back.png` (2550×3300)
- `preview-phone.png` (1170 wide)
- `menu-print-bleed.pdf`
- `proposal.md`: the thesis, how the structure encodes the concept, the KB principle keys used, precedents and what is *not* copied, and the gate results
- `visual_tests.json`: from `handoff/designs/tools/visual_tests.py` on the front and back
