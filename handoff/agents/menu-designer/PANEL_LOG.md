# Review panel log

One entry per round (appended by the designer after each round). Gate: all 15 reviews ≥ 80.

## Round 1 — sample-bar

Scores: Design Theory 71, 70, 71, 72, 72 (mean 71.3) · Cocktail & Beverage 77, 76, 74, 75, 71 (mean 74.6) ·
Concept & Brand 75, 73, 72, 69, 71 (mean 71.9). Gate not met (all 15 below 80).

Changed (toolkit, applies to every menu):
- One zero-proof program: when a venue has both mocktails and soft drinks they become one Zero Proof section with
  Crafted and Soft Drinks & Coffee subsections, placed last (all orders). Mocktails no longer hold the front-right slot.
- Spirits in conventional back-bar order: vodka, gin, rum, tequila, mezcal, whiskey (default and brewery orders).
- HOUSE badge dropped on items that sit under a House/Signature subhead (it repeated the subhead).
- Looks: letterspacing ceilings (title 150, subtitle 180, section 120, subhead 110 per 1000 em) applied in
  `styleForLook`; prices set one step under the name size in normal weight (`quietPrices`).
- Speakeasy Noir: second accent changed from copper #c7876a to warm neutral #a39a88 (one accent only); descriptions and
  prices brightened to #c4baa4 for low light.
- Tests: 4 new (zero-proof merge, spirits order, HOUSE badge, tracking/price ceilings); 60 passed.

Filed: S14 (subhead/legend spacing, price separator, badge size, section order within the page plan).
Still open: page balance on sample-bar (page 1 lower third and page 2 lower-left remain empty); garnishes and spirit
descriptors not yet in the sample transcript.

## Round 2 — casa-luna

Scores: Design Theory 75, 81, 78, 80, 81 (mean 79.0) · Cocktail & Beverage 68, 69, 69, 67, 68 (mean 68.2) ·
Concept & Brand 76, 78, 78, 77, 73 (mean 76.4). Lowest 67. Gate not met (10 of 15 below 80).
Weakest subscores: descriptions 59, list_conventions 63.

The panel's improve step hit the account's usage limit partway through ("session limit, resets 1am UTC"), and so did
every agent in rounds 3–25 of that run: **those rounds never ran**. The designer finished round 2's improvements by
hand the next morning.

Changed (toolkit, applies to every menu):
- **Follow-up answers.** The parser takes the venue's answers to the designer's questions ("The Paloma is blanco
  tequila, grapefruit, lime and soda, garnished with a grapefruit wedge", "Modelo is Modelo Especial, Mexican lager,
  4.4 percent") and fills the known item's description, ABV and garnish. It never takes a price or adds an item.
  "Answers to the designer's questions" is a header, not an item.
- **Garnish** prints after a middle dot at the end of the line ("… agave · salt rim"), in the speaker's casing
  (Tajín), unless the whole phrase is already there. It is carried through the hand-off payload and recorded as a
  garnish component, which answers the garnish question.
- **Question bug.** `\b%\b` never matched a printed ABV, so every spirit with an ABV was still asked for "age or
  proof". A subsection name (Blanco, Reposado) now counts as the expression.
- **Flavour-choice sodas** ("mandarin, tamarind, lime or grapefruit") are not asked for a garnish.
- **Wine key.** Items that carry part of the ladder (a glass-only Prosecco beside a glass/bottle Cabernet) still take
  one "Glass · Bottle" key under the heading. The redundant colour tag ("Red" before a Cabernet) is dropped.
- **HOUSE badge** dropped beside a name that already starts with "House".
- **Subtitle** is text-size caps: tracking capped at 120/1000 em, and a floor of 8.25 pt.
- **Footer** centred under a centred masthead (one axis); flush left when it carries legal copy.
- **Measure.** A wide single column first tries wider side margins (to about 5.5 in) before leader dots. On Casa Luna
  the page is full, so the leaders stay.
- **Sample transcript.** Casa Luna's voice note gained the venue's (simulated, labelled) answers: builds, garnishes,
  spirit origins and ABV, beer styles, wine grapes and regions. No price changed.
- Tests: 65 passed (5 new).

Result: Casa Luna now submits (confidence 0.88), with one open question (legal lines).

Open, carried to later rounds:
- **Leaders.** They run about 150 mm on a full single column. Menu Studio draws them as dashes in the price colour
  at 60% opacity; a quieter leader style would be a Menu Studio change.
- **Concept.** "Speakeasy Noir" reads as a generic lounge, not a RiNo cantina. The venue asked for "dark and moody with
  gold": it needs a dark look with cantina character (a warmer marigold gold, a punchier display face).
- **Two golds.** #c9a45c and #b8903a are near-duplicates. Merge them, or give each a distinct role.
- **Beer.** Draft and Can print as description facts. Subheads would carry the pour size, once the venue gives it.
