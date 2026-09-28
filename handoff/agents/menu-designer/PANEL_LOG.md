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

## Round 4 — sample-bar

Scores: Design Theory 69, 69, 75, 71, 70 (mean 70.9) · Cocktail & Beverage 74, 76, 75, 75, 74 (mean 75.0) ·
Concept & Brand 69, 72, 65, 72, 71 (mean 69.8). Lowest 65. Gate not met (all 15 below 80).
Weakest subscores: grid_space 55, format_layout 57, overall_design 64, descriptions 68.

All 15 reviewers led with page balance: page 1 ended 121 mm above its margin while Zero Proof closed a crammed page 2
and the Wine column stopped at 44%. Next most common: the spirit pour key printed five times, keys touching their
items, no garnishes or spirit type/proof, wine regions without commas.

Changed (toolkit, applies to every menu):
- **Page plan may move Zero Proof up.** The planner tries the zero-proof section directly after the cocktails (their
  peer, on the same page) and keeps it when the columns fill clearly more evenly (mean/max column fill +0.05). A stale
  break flag no longer skews the page count, and a plan that orphans a subhead is a last resort. Sample Bar: Cocktails
  | Zero Proof on page 1, Beer + Wine | Spirits on page 2.
- **Growth past the longest description.** Type used to stop at x1.03 because descriptions do not wrap (S6). Once a
  line would run wide, the description size holds at the last size that fit while names, prices, heads and spacing
  keep growing (x1.24 on Sample Bar; page 2 now fills to the footer). `scaleStyle` also keeps item gap + section gap
  within the 40 px rhythm cap.
- **One key per section.** When most subsections share a pour key and the rest carry their own, the shared key prints
  once under the section heading and only the exception keeps its own ("1 oz · 1.5 oz · 2.5 oz" under SPIRITS,
  "1.5 oz · 3 oz" under WHISKEY). Frees four lines.
- **Undo a promotion the plan no longer needs.** A keep-with-next subsection ("Spirits · Whiskey") goes back under its
  parent when the final plan keeps it in the same column, with no orphan and no page added.
- **House style in descriptions.** A wine region takes its comma ("Marlborough, New Zealand", "Paso Robles,
  California"); "non alcoholic" is hyphenated; West Coast and New England are capitalised. No words added or dropped.
- **Garnish question scope.** Crafted zero-proof drinks are now asked for a garnish (they were skipped); bottled,
  canned or brewed soft drinks never are.
- **Sample transcript.** Sample Bar's voice note gained the venue's (simulated, labelled) answers: garnishes for all 10
  cocktails and 4 crafted zero-proof drinks (Cointreau named in the Margarita, simple syrup in the Garden Gimlet),
  type and ABV for all 12 spirits (Tito's 40%, Tanqueray 47.3%, Rittenhouse bottled-in-bond 50%, Blanton's 46.5%,
  Lagavulin Islay single malt 43%…), La Marca and Whispering Angel grapes and appellations, Athletic Run Wild's
  brewery, soft-drink descriptors. No price changed. It now submits (confidence 0.72, one open question: legal lines).
  Self-check 94/97 (A).
- Tests: 76 passed (4 new, 2 updated).

Filed: S16 (fill both pages of a two-page menu: column justification or a section continuing at a subsection
boundary). S14 extended for round 4 (key-line spacing, tabular figures for tiered prices).

Open, carried to later rounds:
- **Page 1 still ends about 40% short** on Sample Bar (bottom margin 107 mm). Sections are whole and Menu Studio has
  one type scale, so page-level balance needs S16. Moving Beer to page 1 balances pages but leaves page 2's Wine
  column half empty; not taken.
- **Key lines.** "Glass · Bottle" still sits right on SPARKLING and each key touches its first item (S14 spacing).
- **Content not yet answered:** pitcher volume and can sizes, wine glass pour, breweries for the five drafts (fictional
  beers: ask, never invent), Hazy Peak's 8.50 (confirm or round, a venue call), Athletic Run Wild also listed under Zero
  Proof, vintages / NV.
- **Brand.** Masthead and footer are generic ("Denver, CO"); no running head on page 2; Luna Paloma's "house special"
  shows only as a gold name. Needs the venue's words (hours, tagline).
- **Tags and colour.** SEASONAL / NEW still 7 pt grey (S14); subheads dimmer than descriptions; prices share the
  description colour.
- **Grand Hotel (option B)** runs to 3 pages on Sample Bar (too_many_items_for_format), unchanged this round.
- From round 3: beer order light to dark, column balance on High Altitude, altitude concept. From round 2: leaders
  style, Speakeasy Noir cantina character, two golds on Casa Luna.

## Round 5 — casa-luna

Scores: Design Theory 79, 79, 77, 81, 81 (mean 79.4) · Cocktail & Beverage 83, 85, 80, 81, 84 (mean 82.4) ·
Concept & Brand 80, 78, 79, 75, 79 (mean 78.2). Lowest 75. Gate not met (9 of 15 below 80).
Weakest subscores: list_conventions 73, graphic_craft 75, overall_design 75, grid_space 76, concept 76, brand 76.

Most common points: the Wine "Glass · Bottle" key sat flush left, far from "11 / 40", and Prosecco's lone 10 was
ambiguous (14 of 15); 6 in dashed leaders on a 7.1 in measure (11); NEW invisible at 7 pt grey (9); the signature
marked by gold alone (4); no pour sizes (5 beverage reviewers); Prosecco after the Cabernet; the reasoning claimed
White / Rosé subsections that were never built.

Changed (toolkit, applies to every menu):
- **Tags lead the description line.** New / Seasonal / House special print as the first word of the description
  ("New · Del Maguey Vida mezcal, Campari, …"), at description size, instead of Menu Studio's raised 7 pt grey badge.
  A house special whose name already says "House" reads "Signature · …", so the gold name has a reason a guest can
  read (not colour alone). Flags stay in `meta.designer_flags`. If the word would push the line past its column
  (descriptions do not wrap, S6) it goes back to the badge (Sample Bar's Garden Gimlet).
- **Partial price ladders named on each line.** When some items carry only part of the ladder (Prosecco glass only
  beside Cabernet glass / bottle), no floating key prints; each line leads with its units ("Glass · Glera, …",
  "Glass / bottle · Justin Cabernet Sauvignon, …"). Full ladders keep the one key under the heading.
- **Sparkling and rosé recognised.** Prosecco, Cava, Champagne, Crémant, brut, Lambrusco, pét-nat go to Sparkling and
  rosé/rosado to Rosé, so wine runs light to full (Prosecco before the Cabernet).
- **Reasoning says what was built.** "Wine ordered light to full: Sparkling, Red" instead of the boilerplate that
  named four subsections.
- **No forced leaders.** A wide single column no longer switches leader dots on; the right-aligned price column stands
  alone (looks that ask for leaders keep them). The measure could not be narrowed: one margin value (S17).
- **One gold.** The brand level follows the requested colour when it carried the look's own accent.
- **Sample transcript.** Casa Luna's voice note gained the venue's (simulated, labelled) answers: 1.5 oz tequila and
  mezcal pours, 16 oz drafts, 6 oz Cabernet and 5 oz Prosecco pours, Cointreau in the House Margarita, fresh
  grapefruit juice and soda water in the Paloma, Del Maguey Vida named in the Mezcal Negroni and as a joven mezcal,
  and Justin as the Cabernet's producer. No price changed. Still one page, 42/42 self-check, confidence 0.88.
- Tests: 79 passed (3 new, 2 updated).

Filed: S17 (a single-column measure or separate side margins; a key aligned over the price column; finer leaders
ending at a fixed price slot).

Open, carried to later rounds:
- **Measure.** Casa Luna's column is still 7.1 in (one margin value, S17). Two columns would put prices inline and
  push several description lines past 3.4 in (S6).
- **Masthead and footer axis.** Centred masthead and footer over a flush-left body (Swiss reviewer); "Denver, CO"
  footer adds nothing; no cantina voice line (needs the venue's words, never invented).
- **Key lines touch their first item** ("1.5 oz pours" on Siete Leguas; S14 spacing).
- **Content not yet answered:** Tecate can size, Ranch Water 11.50 (confirm or round, a venue call), NA beer and
  zero-proof versions of the signatures, a white or rosé, a Colorado tap. Ask, never invent.
- **Colour.** Prices share the description grey (#c4baa4); several near greys (subheads, footer); descriptions 8.25 pt
  on a dark ground (print manager asks for 9 pt).
- **Section weight.** Section heads 1.3x names; reviewers ask for more space above heads than below.
- High Altitude self-check bottom margin now 45–48 mm (was 34 mm); from rounds 2–4: beer order light to dark, column
  balance, altitude concept, Sample Bar page 1 short (S16).
