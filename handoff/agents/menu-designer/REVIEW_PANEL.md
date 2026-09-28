# Menu review panel (Rob, 2026-09-28)

Every menu the designer makes is reviewed by **three reviewers, five independent reviews each: 15 reviews per round**.
The gate: **every one of the 15 reviews must score 80 or more.** Rounds repeat (up to 100) until the menu passes. After
every failed round the designer improves, preferring general improvements to the toolkit, so every later menu is
better too. Each round must finish within five minutes.

The panel sits alongside the backend's two-reviewer gate (`../MENU_DESIGN_SCORECARD.md`: Design Critic and Menu
Content Reviewer, each averaging above 80). The database gate knows only those two reviewer keys. Extending it to this
panel is suggestion S14 in `SUGGESTIONS_FOR_LEAD_DEV.md`.

Each review returns JSON: `{"reviewer", "lens", "score": 0-100, "subscores": {...}, "strengths": [...], "fixes": [...]}`.
`score` is the mean of the subscores, rounded. Fixes are specific and actionable ("section headers 1.3× item size",
not "improve hierarchy"). Reviewers are read-only.

**Scoring bands:**

| Score | Meaning |
|---|---|
| 95+ | Portfolio grade |
| 85–94 | Strong professional work |
| 80–84 | Publishable |
| 60–79 | Visibly amateur somewhere |
| Below 60 | Not a professional menu |

**Every reviewer judges what is on the page.** Menu Studio's limits are noted but not excused:
- no ornaments or images;
- one-line descriptions;
- prices inline above one column;
- non-integer prices printed with two decimals.

When a limit costs points, the fix says so, and the designer files it for the lead developer.

## Reviewer 1: Design Theory (`panel-design-theory`)

Upper-level design theory and graphic design: headers, hierarchy, colour, palette.

**Subscores:**

| Subscore | What it covers |
|---|---|
| `hierarchy` | Title → section → subsection → item → description → price, each clearly distinct in size, weight, case or tracking; never colour alone |
| `headers` | Consistent style per level, alignment, and space above and below |
| `typography` | Faces and pairing, sizes, tracking (caps 50–120/1000 em in text), line length, legibility at bar light |
| `palette` | 2–4 deliberate colours plus neutrals; contrast of 4.5:1 or more; accent used sparingly and with meaning |
| `grid_space` | Margins, gutters, rhythm, balance, whitespace, alignment |
| `graphic_craft` | Overall visual quality and elements that elevate the menu |

**The five lenses:**
1. Swiss grid and typographic purist (Müller-Brockmann)
2. Colour theorist (Albers; contrast and harmony)
3. Editorial art director (magazine hierarchy)
4. Legibility and accessibility specialist (WCAG, low light, older readers)
5. Butterick / Bringhurst typographer

## Reviewer 2: Cocktail & Beverage (`panel-beverage`)

Cocktail theory, relevance, descriptions and ingredients.

**Subscores:**

| Subscore | What it covers |
|---|---|
| `cocktail_theory` | Builds make sense (balance, families: sours, spirit-forward, highballs); classics named and specced correctly |
| `relevance` | The program fits the venue type, the neighbourhood and the price level; the lists are complete and balanced |
| `descriptions` | Every item described; cocktails name spirit, modifiers and garnish; beer shows style and ABV; wine shows grape/producer and region; spirits show type, age or proof |
| `ingredients` | Real, specific, correctly spelled ingredients; nothing invented; unknowns flagged and asked |
| `list_conventions` | Pour sizes, glass/bottle, draft/can, and zero-proof treated as peers, laid out as professionals do |

**The five lenses:**
1. Head bartender of a top craft cocktail bar
2. Beverage director (whole program)
3. Sommelier (wine list)
4. Cicerone (beer list)
5. Zero-proof / NA program specialist

## Reviewer 3: Concept & Brand (`panel-concept-brand`)

Overall concept and scheme, brand guidelines, colour choice, pricing, format, layout and design.

**Subscores:**

| Subscore | What it covers |
|---|---|
| `concept` | The menu has a clear idea that fits the venue (tone, neighbourhood, audience) |
| `brand` | The masthead, voice, colour and type read as one brand; consistent with any brand input |
| `colour_choice` | The colour choice suits this concept and room |
| `pricing` | Consistent price format; ladders (pours, glass/bottle) clear; price architecture sensible; no "$"; nothing looks like an error |
| `format_layout` | Page size, pages, columns, section order and flow, balance across pages, print and phone |
| `overall_design` | Would a top agency sign it? |

**The five lenses:**
1. Hospitality brand strategist
2. Restaurant menu engineer (pricing and placement)
3. Print production manager
4. Guest in the room (low light, first visit)
5. Agency creative director

## Loop

Driven by the Workflow in `panel/round.workflow.js`, with its log in `PANEL_LOG.md`:
1. Render the menu.
2. Run 15 reviews in parallel.
3. Aggregate. It passes if every review is 80 or more.
4. If not, the designer turns the most common and most costly fixes into toolkit improvements (tests must stay
   green), then the next round starts.

The menus in rotation are the fictional examples (PHG Sample Bar, Casa Luna, High Altitude Brewing). For those, the
designer may add *simulated venue answers* to its own questions, labelled as sample. It never does this for a real
venue.
