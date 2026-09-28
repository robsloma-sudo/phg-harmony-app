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

## Round 3 — high-altitude

Scores: Design Theory 66, 65, 65, 70, 67 (mean 66.4) · Cocktail & Beverage 67, 68, 67, 66, 64 (mean 66.4) ·
Concept & Brand 67, 67, 66, 70, 69 (mean 67.6). Lowest 64. Gate not met (all 15 below 80).
Weakest subscores: list_conventions 54, grid_space 58, format_layout 58, descriptions 59.

All 15 reviewers led with the same defect: the CANS subhead orphaned at the foot of column 1.

Changed (toolkit, applies to every menu):
- **Keep-with-next.** After fitting, any subhead whose first two items land in another column or page is promoted to
  its own section ("Beer · Cans"), which Menu Studio keeps whole, and the page is refitted from the unfitted style.
  The Menu Studio fix is filed as S15.
- **Section rhythm.** Space above a section head (item gap + section gap) is capped at 40 px (10.6 mm), in both the
  spread step and the justify step. Spare height now goes into type: the page fill is measured to the last line of
  ink (the cursor carried the trailing gaps, so a page 36 mm short read as 0.86 full), and composing runs below 0.86
  fill. High Altitude went from type x1.0 with 16–18 mm section gaps to type x1.20 with one 10.6 mm gap.
- **One accent value.** A featured name's accent must meet 4.5:1; when the look's accent was raised for contrast, the
  feature takes the raised section colour. Taproom's accent is now #8e5e18 at source (4.8:1, was #b7791f at 3.1:1).
- **Say what prints.** Multi-column files set `dots: false, priceAlign: 'inline'` (Menu Studio prints multi-column
  prices inline, S5); the look note and "why" drop "leader dots" when none print. Taproom's note no longer claims a
  condensed face.
- **Footer** never repeats the masthead: "Fort Collins, CO" under "Taproom · Fort Collins" is dropped.
- **Pour sizes.** "Drafts are poured at sixteen ounces" / "Whiskey is poured at one and a half ounces" print once under
  that heading ("16 oz pours unless noted", "1.5 oz pours"). An item's own pour from the venue's answer ("poured at ten
  ounces") prints on its line before the ABV ("Imperial stout · 10 oz pour · 10.5% ABV"). Carried through the hand-off
  payload (`inputs.pour_notes`, `items[].pour`). Never invented.
- **Names as spoken.** A number word the speaker capitalised is part of a name ("Laws Four Grain Bourbon", not
  "Laws 4 Grain"); "four pack" stays "4 Pack". Kölsch, Märzen, Gewürztraminer, Grüner Veltliner keep their diacritics.
  A leading "our" is dropped from answer descriptions.
- **Sample transcript.** High Altitude's voice note gained the venue's (simulated, labelled) answers: styles for the six
  ABV-only drafts, can format and ABV, cider and seltzer style and ABV (Stem Real Dry 6.9%), whiskey type and ABV
  (Stranahan's Original 47%, Laws Four Grain 47.5%), Athletic Run Wild as a non-alcoholic IPA, cocktail garnishes,
  draft/whiskey pours and the 10 oz imperial stout pour. No price changed. It now submits (confidence 0.76, one open
  question: legal lines); self-check 46/47 (bottom margin 34 mm, traded for the gap cap).
- Tests: 72 passed (7 new).

Filed: S15 (keep a subhead with its first items). S14 extended with the badge baseline, size and colour for round 3.

Open, carried to later rounds:
- **Tags.** HOUSE / SEASONAL / NEW still print raised, 7 pt, grey (Menu Studio `mdcDrawItem`, S14). Moving them into the
  description line is the designer-side alternative if S14 is not taken.
- **Beer order.** Reviewers want drafts light to dark by family (lagers, pale/hoppy, amber, wheat/sour, stouts) with the
  house beer first and the imperial stout closing. The designer keeps spoken order apart from the edge promotions.
- **Column balance.** Right column ends about 30 mm below the left on High Altitude; the bottom margin is 21 mm deeper
  than declared (self-check). Type growth is capped by the longest description line (no wrapping in Menu Studio, S6).
- **Concept.** Nothing says altitude (e.g. "5,003 ft" in the deck); the masthead is a generic grotesque. Needs the
  venue's words, never invented; a condensed display face is not among the 8 system fonts.
- From round 2: leaders style (Menu Studio), Speakeasy Noir cantina character, two golds on Casa Luna.
