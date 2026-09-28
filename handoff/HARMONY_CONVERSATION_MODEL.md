# Harmony Conversation Model

Build spec for talking to all of PHG: asking about any data, building recipes and menus by voice,
organising everything in folders, and driving the app's screens hands-free.

Status: proposal for Rob, 2026-09-28. Nothing here is built yet unless it says "exists today".
Invoice photo capture is deliberately left for a later phase (Rob, 2026-09-28).

---

## 1. The idea in one paragraph

Every time Rob speaks, Harmony turns it into a **job** (find something, build something, organise
something, show something, change the screen). A job has **slots** it must fill (which drink, which
venue, which folder). Harmony fills what it can from the words, the conversation and the screen, and
asks **one short question at a time** for the rest, offering choices that really exist in the data.
To answer, it walks a **map of all PHG data** (every table described in plain words, with the paths
between them). To change anything it makes a **proposal** and saves only after a yes. To change the
screen it sends **screen commands** (zoom, focus, filter, open). If Rob talks over it, it stops
immediately, **parks** the job, listens, and later offers to pick the parked job back up.

---

## 2. What exists today (build on it, don't replace it)

| Piece | State | Use in this model |
|---|---|---|
| Capability registry `phg.capabilities` | 33 capabilities (venue search, brand presence, cocktail development, menu engineering, recipe costing, sales, labor, P&L ...) | The list of "verbs" Harmony can call for reads |
| Command Center (`phg-command-center`, `command_sessions/turns/action_proposals/workflows`) | Works. Writes are proposals with a one-time approval token; 9 write actions (create_menu_item, persist_recipe_candidate, set_purchase_cost, set_menu_price ...) | The only way Harmony writes. New write actions are added here |
| Language interpreter (`phg-language-interpreter`) | Works, gpt-4o-mini, strict JSON intent + entities, logs to `language_interpretations` | Becomes the "understanding" step; upgrade model and schema |
| Conversation state (`conversations`, `goals` (nested), `plans`, `tasks`, `conversation_referents`) | Built 2026-09-20 but **not wired to the app**; referents table empty | Becomes Harmony's memory: jobs = goals, parked jobs = suspended goals, "it/that one" = referents |
| Conversation tests (`conversation_tests`, `golden_tests`, `shadow_regression_cases`) | 4 + 32 + 10 cases | The regression suite for every dialog below |
| Recipe + costing schema (`units`, `ingredients`, `prep_recipes` (nestable), `recipe_components`, `vendors`, `procurement_catalog_items`, `purchase_costs`, `recipe_cost_snapshots`) | Tables exist, **all empty** except 13 units and 6 ingredients | The costing graph. Filled by voice building now, by invoices later |
| House menus `menu_projects` | 1 project; has a flat `season` text field | Becomes one kind of folder item |
| Read-only SQL gateway `phg_designer_query` | Works for the menu designer agent: read-only transaction, 20 s timeout, row cap, every query logged | Pattern for Harmony's deep-question tool |
| In-app voice (talk mode) | Hands-free, turn-based. Mic is **off while Harmony speaks**; interrupt only by tapping the orb | Upgrade to talk-over interruption (section 9) |
| Data canvas map (Leaflet) | Draws pins and flies to one place. No zoom/focus/filter by voice; pins not kept after drawing | Upgrade to a controllable map (section 8) |
| Action button (`phg-harmony-inbox`) | Conversation loop, recipes, 12 fixed data sources, opens app only after offer + yes | Uses the same brain once it exists |

Gap to fix first: most of the command, interpreter and conversation functions exist only on the
live server, not in git (80+ live functions vs 10 in the repo). Pull their source into the repo
before changing them.

---

## 3. The layers

```
 Voice in/out  ->  Understand  ->  Dialogue manager  ->  Tools  ->  Answer (speech + screen)
 (barge-in)        (intent,         (jobs, slots,        read: capabilities, data map navigator
                    entities,        questions, parking,  write: proposals (confirm, undo)
                    references)      memory)              screen: UI command bus
                                           |
                                    Knowledge map (all tables, plain words, paths, live values)
                                    Workspace (folders, links, views)
```

1. **Voice in/out**: listens, speaks, stops the moment Rob talks (section 9).
2. **Understand**: turns words into `{intent, entities, slot values, references}`. "That one",
   "zoom in there", "save it" are resolved against memory and what is on screen.
3. **Dialogue manager**: owns the job stack; decides answer vs ask vs propose vs do; writes memory.
4. **Tools**: reads (registered capabilities first, the data-map navigator for anything else),
   writes (proposals only), screen commands.
5. **Knowledge map**: the description of all data (section 4).
6. **Workspace**: folders and what is linked into them (section 6).

---

## 4. The knowledge map (so Harmony can reach anything)

About 300 tables across `public`, `phg`, `phg_design`, `phg_flavor`. Harmony should not think in
tables. It thinks in about 35 **things** Rob talks about. Each thing has: plain name and aliases,
the tables behind it, how to find one by name, its useful fields in plain words, and links to other
things.

### 4.1 Things (entities)

| Group | Things (what Rob says) | Main tables today |
|---|---|---|
| Market | venue / bar / restaurant, menu, menu section, menu item, cocktail (identity), price | `accounts` (41,886), `menus` (12,229), `menu_sections`, `menu_items` (211,174), `menu_item_cocktail_core`, `cocktail_specs` |
| Place | state, city, county, ZIP, demographics | `geographies`, `city_county_map`, `phg_census_zcta`, `geography_demographics` |
| Spirits | brand, product / expression, producer, distillery / NOM, label approval (COLA), category, designation (e.g. Tequila DO) | `brands` (2,374), `products`, `organizations`, `production_sites` (201), `cola_label_approvals` (50,336), `beverage_categories`, `legal_designations` |
| House work | house menu, house menu item, recipe, recipe version, prep recipe (syrups, brines, batches), ingredient, unit, recipe book | `phg.menu_projects`, `phg.menu_items`, `phg.recipe_projects`, `phg.recipe_versions`, `phg.prep_recipes`, `phg.recipe_components`, `phg.ingredients`, `phg.units` |
| Buying and cost | vendor / distributor, catalog item (what the vendor sells), purchase cost, invoice, recipe cost, COGS | `phg.vendors`, `phg.procurement_catalog_items`, `phg.purchase_costs`, `phg.purchase_invoices`, `phg.recipe_cost_snapshots` |
| Operations | sales, POS item, labor, shift, expense, inventory count, budget, P&L | `phg.sales_*`, `phg.labor_*`, `phg.operating_expenses`, `phg.inventory_*`, `phg.budget_*`, `phg.pl_snapshots` |
| Knowledge | classic spec, cocktail tag, flavor pairing, design principle, training package | `cocktail_reference`, `cocktail_tag_*`, `phg_flavor.*`, `phg_design.*`, `phg.training_packages` |
| Organising | folder, note, task, idea, reminder | new `phg.workspace_*` (section 6), `phg.harmony_notes` |

### 4.2 Paths between things

The map stores the join paths once, so Harmony never guesses them. Examples:

- **Margaritas at a venue**: state -> city -> venue (`accounts`) -> current menu (`menus.is_current`)
  -> sections -> items -> cocktail identity = Margarita (resolver), plus the name text as fallback.
- **Brand at a distillery**: NOM -> production site -> organization -> brands (`primary_nom`,
  producer) -> products -> label approvals.
- **Who pours a brand in a city**: brand -> `menu_item_brands` -> menu items -> menus -> venues -> city.
- **Recipe cost**: menu item -> current recipe version -> components -> ingredient or nested prep
  -> catalog item -> latest purchase cost -> unit conversion -> cost; missing links become
  "cost pending".

Each path is checked against the live schema when it is written into the map, then covered by a test.

### 4.3 How Harmony answers a deep question (the navigator)

For anything the 33 capabilities don't cover, Harmony runs a short research loop (up to about 8 steps):

1. **Find the things**: search the map for the words ("margaritas" = cocktail, "Tacos Tequila" = venue?).
2. **Pin them down**: look up real matches. 0 matches: say so and suggest the closest. 1: use it.
   2 to 5: ask, naming them ("I see Tacos Tequila in Des Moines and in Ankeny. Which one?").
   Many: ask for the narrowing slot (city, state, type).
3. **Plan the path** from the map.
4. **Run a read-only query** through a gateway like `phg_designer_query` (read-only transaction,
   time limit, row cap, logged), limited to the tables the map allows.
5. **Check the result**: empty or odd results trigger one retry with a looser path, then an honest "no data".
6. **Answer**: short spoken summary + a screen view (table, map, bars) + offer the next step.

Allowed data is a whitelist in the map. Never readable: `internal_secrets`, sessions, device keys,
auth, raw staging tables, logs, other accounts' house data. House data (recipes, costs, sales,
labor) is always filtered to Rob's account.

---

## 5. How Harmony talks: jobs, slots and questions

### 5.1 Jobs

Every request becomes a job: `{kind, slots, status, source turn, result, parked_at}`. Kinds:

| Kind | Examples |
|---|---|
| **find** | "all the margaritas at X in Denver", "where is NOM 1610", "average price of a Paloma in Iowa" |
| **explain** | "why is our COGS up", "what makes this brand different" |
| **build** | new cocktail, new prep recipe, new dish (later), new menu, new menu item |
| **organise** | make a folder, save to folder, move, rename, "what's in Spring 2028" |
| **show** | open map, zoom, focus, filter, open a menu, go to a screen |
| **change** | set a price, swap an ingredient, change a quantity |
| **note** | remind me, log this idea |

Jobs live in a stack. A new job on top of an unfinished one **parks** the old one (status
suspended). Finished jobs stay in memory for "go back to", "that one" and "the second one".
This uses the existing `goals` (nested, with suspended/superseded states) and `conversation_referents`.

### 5.2 Slots per job kind

| Job | Required slots | Optional slots | Defaults |
|---|---|---|---|
| find items on menus | item or cocktail; place (state, city or venue) | venue type, price range, current vs all menus | current menus only |
| find venue | name or kind; place | type, has cocktails | Rob's states (IA, CO, NY) |
| brand info | brand | aspect (distillery, products, labels, where poured, price) | overview first |
| new cocktail | name (or "untitled"), destination (folder, menu or later) | family, base spirit, season, target price, glass, garnish | draft status |
| new prep recipe | name, ingredients + amounts, method | yield, shelf life, storage, destination | destination "Unfiled" if skipped |
| save | what (defaults to the current job's result), where | new folder? | ask "where?" |
| map control | action (zoom, focus, filter, select) | target | current map |

### 5.3 Question rules (how to not sound robotic)

1. Answer when possible. Ask only when the answer really depends on the missing piece.
2. One question per turn. Offer 2 to 5 real options **taken from the data**, never invented.
3. Never ask what has already been said in this conversation, or what the screen already shows.
4. Use defaults and say them ("From current menus. Say 'all menus' for older ones.").
5. After two questions in a row, make a best guess, answer it, and say how to change it.
6. Keep every word Rob uses: a chocolate Manhattan is not a Manhattan; "house" means Rob's recipes.
7. Short answers ("the second one", "Denver", "yeah") answer the last question asked.
8. Writes: say exactly what will be saved and where, then wait for yes (section 10).
9. Read back numbers Rob dictates ("800 grams of salt, got it") so mistakes are caught early.
10. Always end with a useful next step, not filler ("Want the prices too?").

### 5.4 The question bank (patterns Harmony reuses)

| Missing piece | Question pattern |
|---|---|
| Place | "Which city? I have [Denver, Boulder, Fort Collins] in Colorado." |
| Same name, several matches | "I see [A in Des Moines] and [A in Ankeny]. Which one?" |
| Scope | "Just current menus, or older ones too?" |
| Version | "Classic, your house one, from the internet, a few variations, or build one together?" |
| Destination | "Where should it go: [Spring 2028 > Cocktails], a new folder, or leave it unfiled?" |
| Folder missing | "There's no Seasonal 2026 folder yet. Create it under Menus?" |
| New ingredient | "I don't have 'Tajin salt' yet. Add it as a new ingredient?" |
| Ambiguous ingredient | "Salt: kosher, sea salt or table salt?" |
| Unit | "Is that grams or ounces?" |
| Yield | "What does the batch make, roughly?" |
| Template now or later | "Set up the menu template first, or just the recipe for now?" |
| Confirm write | "Save 'Citrus Brine' to Spring 2028 > Prep book? Say yes to save." |
| Interrupted | "Sorry, go ahead." then later "Want me to finish the Manhattan, or save it for later?" |
| Too broad | "That's 4,000 venues. Narrow it by city, type, or cocktails only?" |
| No data | "I don't have [X] for [place]. Closest I have is [Y]. Want that?" |

---

## 6. Folders: an open workspace

Rob wants folders for menus, recipe books, ingredients and seasons, nested as deep as needed, that
can hold anything, with views like Finance and Training inside a menu folder, and that grow as he
talks. Design:

### 6.1 Data model (new tables, need migration approval)

- `phg.workspace_folders`: `id, account_id, parent_id (nesting), name, kind, template_key, icon,
  sort, metadata, created_by, created_at, archived_at`.
  Kinds: `folder` (plain), `project` (e.g. a seasonal menu), `book` (recipe book, prep book),
  `view` (a computed page such as Finance), `smart` (a saved search).
- `phg.workspace_links`: `folder_id, entity_type, entity_id, label, role, sort, added_by, added_at`.
  A link, not a copy: the same recipe can sit in "Spring 2028 > Cocktails" and "Recipe book > Stirred".
- `phg.workspace_entity_types`: the open-ended registry of what can be linked (recipe, prep recipe,
  menu item, house menu, ingredient, vendor, venue, brand, NOM, menu from the library, note, file,
  training package, **record**). New types can be added without a new table.
- `phg.workspace_records`: free-form records (`type, title, fields jsonb, files`) for anything that
  doesn't have its own table yet. This is the "build it as we talk" part: "make a supplier contact
  card for Breakthru" becomes a record until it deserves a real table.
- `phg.workspace_templates`: saved folder structures.

### 6.2 Templates

"Seasonal menu" template (example: Spring 2028):

```
Spring 2028                       (project; linked house menu project)
  Menu design                     (the menu layout, versions, proofs)
  Cocktails                       (recipe links, in menu order)
  Prep book                       (syrups, brines, batches, nested preps)
  Food                            (later)
  Finance                         (view: computed)
  Training                        (training packages per item)
  Sourcing                        (vendors, catalog items used)
  Notes and ideas
```

Other templates: Recipe book, Ingredient library (by category), Venue research, Brand research.
Rob can say "make a new seasonal menu for Fall 2028" and get the whole structure.

### 6.3 Views (computed, never typed in)

- **Finance**: for everything linked in the parent folder: each ingredient's cost per unit, each prep's
  batch cost and cost per unit, each recipe's cost, sale price, COGS %, margin, target COGS %, and a
  list of **missing costs** ("cost pending: 6 ingredients"). Uses `recipe_cost_snapshots` and the
  costing path in 4.2. Works now with pending costs; fills in when prices arrive.
- **Training**: training packages for linked menu items (existing capability).
- **Recipe book**: printable specs of linked recipes.
- **Shopping / par list** (later): quantities from recipes x expected sales.

### 6.4 Talking to folders

| Rob says | Harmony does |
|---|---|
| "Add a new house cocktail to my seasonal 2026 folder" | Finds the folder (or asks, or offers to create it), starts a build job with destination set |
| "Make a folder called Agave for Spring 2028" | Proposes the new folder under Spring 2028, creates it on yes |
| "What's in Spring 2028?" | Speaks a summary, offers to open it |
| "Move the brine to the prep book" | Moves the link, says where it went, can undo |
| "Show me the finance for Spring 2028" | Opens the Finance view; speaks the headline (cost, COGS %, pending costs) |
| "Save it for later" | Saves to "Unfiled" (the inbox folder), says so |

---

## 7. Building by voice (drinks now, food later)

### 7.1 Example: a prep recipe

```
Rob:     Harmony, let's build a new dish for this menu.
Harmony: Want to set up the menu template first, or go straight to the recipe?
Rob:     We can do that later.
Harmony: Okay. What's it called, or should I call it untitled for now?
Rob:     Call it citrus brine. I start with 800 grams of salt and add that to one liter of water.
Harmony: Got it: 800 grams salt, 1 liter water. Which salt, kosher or sea salt?
Rob:     Kosher.
Harmony: Kosher salt, 800 grams. What next?
Rob:     Zest of six lemons, bring it to a simmer, cool it overnight.
Harmony: Added the zest of 6 lemons. Steps so far: dissolve the salt in the water, add the zest,
         bring to a simmer, cool overnight. How much does the batch make?
Rob:     About a liter.
Harmony: Citrus brine, makes about 1 liter. Kosher salt is new to your ingredients, lemons are
         already there. Costs are pending until we have prices. Save it to Spring 2028 > Prep book?
Rob:     Yes.
Harmony: Saved. Want to use it in a recipe now?
```

### 7.2 What happens underneath

1. **Capture loop**: each utterance is parsed into ingredient lines `{amount, unit, ingredient words,
   prep note}` and steps. The draft is kept in the job (and shown on screen if the app is open).
2. **Units**: normalised through `phg.units` (g, kg, ml, l, oz, dash, barspoon, each ...). Spoken
   numbers are read back.
3. **Corrections**: "no, 750", "take out the zest", "swap lemons for limes", "undo" edit the draft.
4. **Ingredient matching**: every ingredient is matched against `phg.ingredients` (name + aliases).
   Found: link it. Close match: ask ("kosher or sea salt?"). Not found: propose a new ingredient.
5. **Nesting**: a prep can be an ingredient of a recipe ("add 2 dashes of citrus brine").
6. **Cost**: each matched ingredient follows catalog item -> vendor -> latest purchase cost. With no
   prices yet, the recipe is saved with "cost pending" per ingredient. When costs arrive later
   (invoice photos, a later phase), every recipe and the Finance views update on their own.
7. **Save**: one proposal: create the prep/recipe + new ingredients + link into the folder. One yes.
8. **Drinks** use the same loop with bar units, a method (stir 6 to 8 seconds, shake hard), glass,
   garnish, and optional link to a house menu item and a price.

### 7.3 New write actions needed in the Command Center

`create_folder`, `rename_folder`, `move_link`, `link_to_folder`, `unlink`, `create_record`,
`create_ingredient`, `create_prep_recipe` (with components), `create_recipe_version` (with components),
`update_recipe_draft`, `attach_recipe_to_menu_item`. Existing actions stay (`create_menu_item`,
`persist_recipe_candidate`, `set_purchase_cost`, `set_menu_price` ...).

---

## 8. Driving the app by voice (screen commands)

The server answer carries a list of **screen commands** besides the words. The app has one command
bus (`window.harmonyUI.run(cmd)`) that each screen registers with.

| Screen | Commands | Example words |
|---|---|---|
| Map | `zoom(in / out / level)`, `focus(entity)`, `select(pin)`, `filter(layer, on/off, criteria)`, `layers(list)`, `reset` | "zoom in", "zoom in on Don Julio", "only distilleries", "hide the venues", "show Jalisco" |
| Brand / venue card | `open(entity)`, `tab(products / labels / where poured / prices)` | "pull up everything on Casamigos", "where is it poured in Denver" |
| Menu library | `filter(state, city, type, cocktail, ingredient)`, `open(menu)`, `next page` | "show me menus in Des Moines with a Paloma" |
| Folders | `open(folder)`, `show view(Finance)`, `back` | "open Spring 2028", "show the finance" |
| Menu studio | existing design commands (paint, next design, darker, page 2, undo ...) | unchanged |
| Anywhere | `go(screen)`, `close`, `scroll`, `read this` | "go to the dashboard", "close the map" |

Map changes needed (today pins are drawn and forgotten): keep all pins with their type (venue,
distillery), brand list and ids; name search over pins; layers per type; programmatic zoom/pan;
selected pin state that Harmony can refer to ("that one"). A conversation about a brand then flows:
"show tequila distilleries" -> map with 201 NOM pins -> "zoom in on Jalisco" -> "which ones make
Don Julio" -> pin focused + brand card -> "what's their best seller on menus in Denver" -> answer +
table -> "go back to the map".

---

## 9. Talking over Harmony (barge-in)

Today in the app: turn-based. The mic is off while Harmony speaks; interrupting needs a tap.

Target behaviour: Rob starts talking while Harmony speaks -> Harmony stops within about a quarter of a
second, parks what it was doing (the job, what it had said, what was left), listens, answers the
new thing, then offers: "Want me to finish the Manhattan spec, or save it for later?" "Later" keeps it
in the parked list ("what were we doing before?" brings it back).

Two ways to build it in the app:

1. **Keep today's pipeline, add a listener during speech**: mic stays open with echo cancellation
   while audio plays; a voice detector with a raised threshold (so Harmony's own voice from the
   speaker doesn't trigger it) stops playback on real speech and starts recording. Cheapest; works
   best with headphones or AirPods, needs tuning on the phone speaker.
2. **Switch talk mode to a realtime voice model** (speech-to-speech over WebRTC with server-side
   turn detection and built-in interruption). Most natural, fastest replies, higher running cost,
   bigger change.

Recommendation: do 1 first (days), test on Rob's phone, move to 2 if it isn't natural enough.

Action button: iOS Shortcuts cannot listen while speaking, so talk-over is **not possible** there.
It stays turn-based (say "stop" at the next listen). Full talk-over from the lock screen needs a
native iPhone app later.

---

## 10. Safety

- Reads: free, account-scoped, whitelist only, logged.
- Writes: always a proposal first (existing token flow). Spoken yes is enough for low-risk writes
  (create a draft, new folder, link, note, new ingredient). Prices, publishing, deleting and
  anything financial need the on-screen Approve button.
- Every write is undoable ("undo that") for at least the session; deletes are archive-first.
- Numbers (money, COGS) always come from database functions, never from the model's arithmetic
  (existing Command Center rule).
- Never opens the app from the Action button unless offered and accepted (live since v12).

---

## 11. Build plan

| Phase | What | Needs |
|---|---|---|
| 0 | Pull live-only function sources (command center, interpreter, conversation, orchestrator) into git | Nothing |
| 1 | **Screen command bus + controllable map** (zoom, focus by name, filter layers, brand card) | Frontend only |
| 2 | **Knowledge map + navigator** (entity catalog, paths, value samples, read-only gateway for Harmony) so "all margaritas at venue X in city Y" and deep questions work | Migration: map tables + read-only role/function |
| 3 | **Dialogue manager** (jobs, slots, question rules, parking, memory via goals/referents), shared by app and Action button | Wiring existing tables; small migration |
| 4 | **Folders workspace** (folders, links, records, templates, Finance/Training views) | Migration: workspace tables + new write actions |
| 5 | **Voice building** of recipes and preps (capture loop, ingredient matching, nested preps, save to folder, cost pending) | New Command Center actions |
| 6 | **Talk-over** in the app (option 1, then maybe realtime) | Frontend + tuning on Rob's phone |
| 7 | **Costing live** in Finance views as prices arrive | Price source |
| Later | Invoice photos -> vision model -> prices; food side; native iPhone app | Separate decisions |

Each phase ships with conversation tests (existing `conversation_tests` table) covering the dialogs
above, run before every deploy.

---

## 12. Decisions for Rob

1. Start order: recommend Phase 1 (map control, no migration) and Phase 2 (knowledge map) in parallel.
2. Approve the migrations as each phase starts (read-only gateway; workspace tables; new write actions).
3. Voice approval: is a spoken "yes" enough for creating drafts, folders and ingredients? (Recommended yes;
   prices, publishing and deletes stay on-screen.)
4. Model cost: stronger model for the dialogue manager and navigator (recommended), and later the
   realtime voice option.
5. Off-limits data beyond the default list (staff, sales, labor details?).
6. Folder templates: confirm the Seasonal menu layout in 6.2 or change it.
