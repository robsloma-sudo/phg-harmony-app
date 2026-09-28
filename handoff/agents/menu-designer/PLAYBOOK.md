# PHG Menu Designer: design playbook

This is the craft the Menu Designer applies to every job. The brief (`../MENU_DESIGNER_BRIEF.md`) says what you
may and may not do. This file says how to do the design well. The toolkit (`README.md`) automates most of it; this
is what you check its output against, and what you change when it gets something wrong.

## 0. The one constraint that shapes everything

The design must be **drawable by Menu Studio as-is**. Menu Studio is a Fabric.js canvas with:

- 8 fonts by index: 0 Georgia, 1 Times, 2 Palatino, 3 Helvetica, 4 Avenir, 5 Trebuchet, 6 Century Gothic, 7 Courier;
- 8 type levels: title, subtitle, section, sub, name, brand, desc, price. Each has font `f`, size `s` (px @96 dpi),
  weight `w`, italic `i`, tracking `sp` (1/1000 em), colour `c`, case `cs` and alignment `al`;
- page settings: bg, ink, rule colour, margin (inches, all four sides), columns, gutter, item and section gaps, rules on/off,
  leader dots, price alignment, spanning heads;
- badges: `new, seasonal, house, local, gluten-free, low-ABV, zero-proof`;
- per-node overrides (`node.format[level]`), atomic sections, and "start on a new page / new column" breaks.

It has no images, ornaments, logos, boxes, web fonts or text wrapping: each description is one line. Anything beyond
this is a recommendation to the Coordinator, never part of the design. The looks in `styles/looks.mjs` are
built only from these parts, which is why the preview can promise "this is what the app will draw".

Two rules from the app code you never break:

- **`#6b4fa8` (purple) is reserved.** It marks prices seeded from library medians. Never use it anywhere.
- **Prices are a list and `[]` means "no printed price".** Never 0 and never a guess. Voice and Coordinator prices
  carry `source: 'manual'`.

## 1. Workflow per job (target: under a minute from transcript to proposal)

1. **Read the task.** Transcript or `input_payload`. Run the parser, then read `request.json` against the transcript:
   every heard item present, nothing invented, and every price attached to the right item.
2. **Pull evidence.** Get the census row for the ZIP and 3–8 comparable library menus (`references.sql` §1, §3), then
   look at their sections, depth and price spread (§4). Write one sentence per reference saying what you borrowed from it.
3. **Design.** Run `tools/run.mjs`. It picks up to 3 looks, orders the sections, promotes house and featured items,
   tunes type for the demographics, fixes contrast and fits the page.
4. **Look at every page PNG.** Check it against §8 below. If something is off, fix the cause: re-run with `--look`,
   supply columns or pages, or edit the `.menu.json` and re-render with `tools/render.mjs`.
5. **Submit.** Insert `proposal.sql`, which is your one allowed write. Missing prices, unplaced items or no venue name
   mean `needs_input` with the questions. Never hold a design back just because questions are open: send both.

## 2. Reading the room: venue type → look

| Venue | First choice | Also strong | Why |
|---|---|---|---|
| Cocktail lounge / speakeasy | Speakeasy Noir | Midnight Deco, Grand Hotel | Low light: cream on near-black with gold heads, big names. |
| Hotel bar / rooftop | Grand Hotel | Midnight Deco, Coastal | Quiet luxury: tracking caps, navy/brass, lots of air. |
| Latin cantina / mezcaleria | Cantina Sol | Speakeasy Noir (if "dark") | Warm sand and terracotta, geometric heads that carry across a loud room. |
| Brewery / taproom | Taproom | Corner Tavern | Long beer lists: bold sans, ABV on every line, dense but scannable. |
| Dive / sports / neighbourhood | Corner Tavern | Taproom | Readable standing up, from a metre away, in a hurry. |
| Wine bar / fine dining | Cellar & Vine | Grand Hotel, Studio Minimal | Serif italics for tasting notes; glass/bottle pricing sits cleanly. |
| Tiki / patio / beach | Tropic | Coastal | Colour does the talking; keep type bold so it survives sunlight. |
| Modern restaurant | Studio Minimal | Cellar & Vine, Coastal | Swiss-style: one family, weight and space instead of decoration. |

What the user says beats the venue type: "dark and moody" means a dark page even at a cantina, and a named colour
becomes the accent. Always offer at least one alternative from the other side of light/dark.

## 3. Demographics → decisions (census for the venue's ZIP)

- **Median age 45+**: body type up one step (the designer does this automatically), more contrast, and fewer small caps
  for descriptions.
- **Income $110k+ or 45%+ of households at $100k+**: restraint. More whitespace, fewer items per column, no leader
  dots, descriptions carry the story, and no price column: prices sit after the name.
- **Income under $55k**: directness. Leader dots, prices easy to find, specials and value called out with badges.
- **21–34 share 30%+**: a bolder look is welcome (Tropic, Cantina Sol, Taproom, Minimal). Zero-proof gets real billing.
- **Hispanic/Latino 40%+ with agave lists**: the agave program leads. Bilingual headings are something to *ask* about;
  never translate on your own.
- **No census row** (today only CO, IA and NY are covered): say so in the reasoning and design from venue type and voice alone.

## 4. Menu engineering (placement and pricing presentation)

- **Section order is the venue's story.** Lounge and cantina: cocktails first, agave next at a cantina. Brewery: beer first.
  Wine bar: sparkling → white → rosé → red first. Non-alcoholic sits directly after cocktails, never last in small type.
- **Prime slots**: the first item of the first section, and the top of each column. House specials and featured items go
  first in their section, get a badge, and their name takes the accent colour (via a per-node override). Promote at most
  one or two per section, because emphasis only works if it's rare.
- **Don't sort by price** and don't leave a descending or ascending price run: it teaches guests to shop the cheapest.
  Keep the order the venue gave, except for promotions.
- **No dollar signs.** Menu Studio prints bare numbers ("14", "11.50"). Whole-dollar prices print without ".00".
- **Anchors and decoys** are the venue's pricing decisions. You may *suggest* ("a 22 reserve margarita at the top would
  make the 14 house marg the obvious choice") in the reasoning, but you never add an item.
- **Sensible depth** (library medians / 80th percentile per menu): cocktails 10 / 18, beer 8 / 20, wine 8 / 18,
  non-alcoholic 4 / 16, whiskey 4 / 15, tequila 5 / 13, other spirits 2 / 5. Well past the 80th percentile, flag
  `long_list` and suggest a separate page for that list rather than shrinking the type.

## 5. How each list is laid out

- **Cocktails**: name, then ingredients as the description, lower-case after the first word, commas, no full stop.
  Subsections (Classics, House, Seasonal, Frozen, Spritzes, Martinis, Margaritas) only when there are 3+ in each.
- **Beer**: subsections by serve (Draft, Cans, Bottles, Local). ABV on every beer ("6.2% ABV · style or note").
  Pack prices keep their pack in the name as spoken ("4 Pack").
- **Cider & seltzer**: its own section, even with one item. It is a list the venue asked for.
- **Wine**: one Wine section with style subsections in the order Sparkling, White, Rosé, Red; or a "By the glass" /
  "By the bottle" split when that's how it was given. Two prices print as "Glass 11 / Bottle 40". A single wine price
  with no label is a question ("glass or bottle?") unless the speaker was in a by-the-glass list.
- **Spirits** (vodka, gin, rum, tequila, mezcal, whiskey, brandy & cognac, liqueurs & amari, sake & soju): every list gets its own
  section with equal type treatment. Split by expression when given: Blanco / Reposado / Añejo; Bourbon / Rye /
  Scotch / Japanese. Pour size is a price label ("2 oz 14"), never assumed.
- **Non-alcoholic**: equal standing. Same type sizes, placed next to cocktails. "Zero Proof" for lounges and upscale looks,
  "Non-Alcoholic" elsewhere.
- **Food** (Drinks + food): food sections after drinks at a bar and before drinks at a restaurant; small plates → mains →
  sides → dessert.
- **Happy hour page**: the days and times are the subtitle, exactly as said. No times means a question. Fewer items,
  bigger type.

## 6. Typography

- A clear scale: title ≈ 2.2–2.8 × name, section ≈ 1.1 × name in tracked caps or 1.2 × name in upper/lower case,
  description ≈ 0.8 × name, price = name size.
- **Print floor** (px @96 dpi): name 12, price 12, description 10, section 12, sub 8. The fitter never goes below these.
  If a menu still won't fit, it gets another page or a question, never smaller type.
- **Tracking**: wide (250–480) only for caps. Upper/lower case gets 0.
- **Measure**: keep a name and its price within about 5.5 in (528 px). In one column on a wide page, use wider margins; otherwise use two columns.
- **Contrast**: 4.5:1 minimum for names, descriptions and prices; 3:1 for headings. The designer raises any colour
  that fails and says so.
- **Meaning is never colour-only.** A house special is accented *and* badged.

## 7. Fitting and composition

The fitter mirrors Menu Studio's own flow (`tools/layout.mjs`: atomic sections, column-target balancing, page foot at
H − M), so a pass here is a pass in the app.

1. Too long: tighten gaps, then add a column, then narrow the margins, then step type down to the floor, then add a page.
2. Too short: search columns × margins × type scale for about 88% fill with balanced columns, then spread any spare
   height into section and item gaps (capped so gaps still look deliberate).
3. Lines wider than their column (Menu Studio doesn't wrap): measured for real in the browser (`render.json`
   `wide_lines`). Fix by using fewer columns, shortening nothing (text is the venue's), or flagging
   `lines_exceed_column` so the Coordinator can ask for a shorter description.

## 8. Final visual check (look at the full-resolution PNG, every page)

- [ ] Title is the venue's name exactly as given, and the subtitle is a fact (city, hours), not a slogan you wrote.
- [ ] Every heard or supplied item appears once, in its list, with its exact price(s).
- [ ] Prime slots hold the house or featured items, badges are correct, and nothing is badged that wasn't said.
- [ ] Columns end near each other and the page is not two-thirds empty; no orphaned heading at a column foot.
- [ ] No line runs into the next column (`render.json` → `wide_lines` is empty, or it's flagged).
- [ ] Legal lines are present only if they were supplied, word for word, in the closing "Please note" section.
- [ ] The phone preview reads at arm's length: names 16 px or more, prices aligned.
- [ ] The reasoning cites 3+ library document IDs, each with what was borrowed.

## 9. Voice input: what Harmony sends and how to read it

Harmony transcribes with `phg-speech-transcribe` and normalises with `phg-language-interpreter`. That text is what
you get. Spoken menus are loose, and the parser (`tools/parse-voice.mjs`) handles the usual patterns:

- numbers in words: "twelve fifty" → 12.50, "nine and a half" → 9.50, "six point two percent" → 6.2% ABV;
- list intros: "for cocktails we have…", "beers on tap…", "wines by the glass:", "in cans…", "blanco…";
- item forms: "the Paloma, it's tequila, grapefruit…, twelve" · "Modelo seven" · "house cab eleven a glass forty a bottle";
- follow-ons: "…fourteen, that's our house special" attaches to the previous item;
- page directions only from sentences about the page: "make it dark and moody with gold, letter size, two columns".
  Item names never set colours or mood ("Double Black Diamond" is a beer).

When the parser is unsure, it asks rather than guessing: a missing price, a list that can't be placed, or a wine price
with no glass/bottle label. Read `heard` beside each item in `request.json`. If the parser split or merged items
wrongly, correct `request.json` by hand from the transcript (not from memory) and re-run with `--task`.
