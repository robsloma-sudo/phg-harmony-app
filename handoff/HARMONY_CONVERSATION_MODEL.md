# Harmony Conversation Model

Build spec for talking to all of PHG: asking about any data, building recipes and menus by voice,
organising it with views and filters, and driving the app's screens hands-free.

Status: proposal for Rob, 2026-09-28. Nothing here is built yet unless it says "exists today".
Invoice photo capture is deliberately left for a later phase (Rob, 2026-09-28).

---

## 0. Why this exists

The end goal (Rob, 2026-09-28): as each business builds out its model, Harmony finds and improves its
**profitability**. "Your costs are too high on that. Your labor is too high this week. These should be your
reporting periods. You're losing this much in food waste. Charge this much more on these items. Cut back on dairy
costs." Everything else in this spec (the knowledge map, setup walkthrough, views and filters, voice building, finance data)
exists so Harmony has complete, trustworthy data about a business to coach it from. Section 4D describes the coach.

---

## 1. The idea in one paragraph

Every time Rob speaks, Harmony turns it into a **job** (find something, build something, organise
something, show something, change the screen). A job has **slots** it must fill (which drink, which
venue, which menu). Harmony fills what it can from the words, the conversation and the screen, and
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
| House menus `menu_projects` | 1 project; has a flat `season` text field | A house menu is a normal row; views group its items |
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
                                    Views and filters (saved, per project and person)
```

1. **Voice in/out**: listens, speaks, stops the moment Rob talks (section 9).
2. **Understand**: turns words into `{intent, entities, slot values, references}`. "That one",
   "zoom in there", "save it" are resolved against memory and what is on screen.
3. **Dialogue manager**: owns the job stack; decides answer vs ask vs propose vs do; writes memory.
4. **Tools**: reads (registered capabilities first, the data-map navigator for anything else),
   writes (proposals only), screen commands.
5. **Knowledge map**: the description of all data (section 4).
6. **Views and filters**: saved ways of looking at any data (section 6).

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
| Organising | view, filter, note, task, idea, reminder | new `phg.saved_views` / `phg.saved_filters` (section 6), `phg.harmony_notes` |

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

## 4A. Operations and finance: one open database Harmony can ask

Goal (Rob, 2026-09-28): "show me comp percent on the POS report for last week", "labor percentage for last
month", "my current week's declining budget on food expenses". Everything lands in Supabase, and Harmony asks it.

### 4A.1 What exists

- **PHG tables already built, nearly empty**: `phg.sales_imports / sales_daily / sales_items` (POS), `labor_*`
  (employees, roles, pay rates, shifts), `operating_expenses`, `expense_categories` (19), `budget_plans`
  (declining budget), `reporting_periods`, `pl_snapshots`, `inventory_*`, `purchase_invoices`. Capabilities
  `sales_analysis`, `labor_analysis`, `budget_forecasting`, `expense_analysis`, `pl_intelligence`,
  `management_dashboard`, `management_variance`, `period_review` are registered. Today: 1 sales import,
  1 budget plan, no labor or expenses.
- **First test business: Rob's Airtable base "Parkway FH"** (one data-source adapter among many; other businesses may use spreadsheets, other POS systems or nothing yet):

| Airtable table | What's in it | Goes to (Supabase) |
|---|---|---|
| Bar Inventory/Pricing | item, bottle/unit cost, case size and price, oz price, type, distributor, par, counts by location, sale prices and COGS by pour size | `ingredients`, `procurement_catalog_items`, `purchase_costs`, `vendors`, `inventory_counts` |
| Bar Recipes | cocktail, ingredients (linked), volumes, cost, sale price, COGS, status | `recipe_projects`, `recipe_versions`, `recipe_components` |
| Invoices | date, vendor, invoice number, photo, amounts split by GL account (5100-01 Liquor ... 6540 Rewards), due/delivery dates | `purchase_invoices`, `operating_expenses` by GL account |
| Manager (daily log) | bar and hall net sales, hours by role, hourly labor $ and %, weather, shift notes, repairs | `sales_daily`, labor hours by role, `harmony_notes`-style shift notes |
| Financial (weekly) | revenue, purchases by category, beginning/ending inventory, COGS by category, budgets and **declining budgets** by GL group, budgeted daily sales, labor %, CC fees, net ordinary income, variance | `budget_plans`, `reporting_periods`, `pl_snapshots` |
| Events/Marketing, Catering/TripleSeat | events, band cost, event sales, catering subtotals, taxes | later: events tables |
| Employees | staff, job title, onboarding checklist (Toast, 7shifts, Paychex, TIPS expiry) | `labor_employees` (no personal contact data unless Rob asks) |
| Vendors/People/Login Info | vendor contacts, delivery days ... and **usernames and passwords** | vendors only; **login fields are never copied** |

The Airtable data gives real ingredient prices now, so recipe costing can start before invoice photos.

### 4A.2 Chart of accounts and metric definitions

- The first test business (Parkway FH) already uses a restaurant chart of accounts (5100 bar cost, 5200 bar mix, 5420 N/A bev, 6100 labor,
  6200 food hall, 6300 facility, 6400 G&A, 6500 marketing), in the style of the Uniform System of Accounts for
  Restaurants. Ship it as the default template in `phg.gl_accounts` (code, name, parent, type, per account); each business renames or adds accounts by talking.
- Every number Harmony says is a **named metric** defined once as a database function, never model arithmetic:
  net sales, comp %, discount %, void %, labor $ and %, hourly vs management labor, COGS $ and % by category
  (liquor, beer, wine, N/A), prime cost, declining budget remaining (budget - spent to date, by GL group, by week),
  budget vs actual variance, sales per labor hour, average check. Each metric has: definition, formula, source
  tables, period rules (from the business's calendar settings, 4B), and a target/range the business sets.
- Harmony's time words map to reporting periods: "last week", "this week", "last month", "period to date", "same
  week last year".

### 4A.3 Getting data in (connectors)

| Source | Holds | How | Priority |
|---|---|---|---|
| Airtable (connected) | inventory, pricing, recipes, invoices, daily log, weekly financials | Scheduled sync into Supabase (one-way, Airtable stays the entry tool for now) | First |
| Toast POS | sales, comps, voids, discounts, item mix, tips, clock-ins | No Claude connector exists. Options: Toast's nightly data export (SFTP) or scheduled emailed reports read through the connected Gmail, or Toast API partner access | Second |
| QuickBooks Online (Intuit connector exists) | books of record: P&L, bills, vendors, bank, cash flow; has industry benchmarking | Read-only connect, sync P&L and bills monthly | If Rob uses QuickBooks |
| 7shifts / Paychex | schedules, labor cost, payroll | No connectors; CSV exports or API later | Later |
| Invoice photos | line-item prices | Vision model (PHG-039) | Later |

### 4A.4 How Harmony learns finance and how to present it

- A **finance knowledge set** (like `phg_design` for menu design): metric definitions, healthy ranges for a bar and
  food hall, what to look at when a number moves (labor % up: sales down or hours up? which role?), and the order
  to explain a variance. Sources: USAR, each business's own targets (4B), and its history once synced.
- **Presentation rules**: headline number first with the period and the target ("Labor was 24.1% last week,
  target 22"), then the one driver that explains most of the gap, then offer the detail (by day, by role).
  Declining budget always as "left to spend this week" plus a pace bar. Money rounded to dollars in speech,
  exact on screen.
- Questions follow the same rules as section 5: "which location?" only if more than one; "gross or net?" only if
  the metric needs it.

## 4B. The setup skeleton: every business sets itself up by talking to Harmony

PHG is a product for many businesses. Rob is the administrator, not the only customer. Nothing specific to one
business (its POS, week start, chart of accounts, targets, revenue centers, words it uses) is built into code.
Instead there is a **skeleton**: a list of everything Harmony needs to know about a business, each item with the
question to ask. Harmony fills it by talking, when it's first needed, and keeps learning. Over time Harmony
"becomes" that business: it knows its places, words, numbers and habits.

### 4B.1 Setting definitions (the skeleton, owned by the admin)

`phg.setting_definitions`, edited by Rob as admin, no code change to add one:

| Field | Example |
|---|---|
| key | `calendar.week_start` |
| group | Calendar, Locations, Sales/POS, Labor, Purchasing, Accounting, Menus, Targets, Voice, People |
| type | choice / number / percent / text / list / mapping / connector |
| question | "What day does your week start?" |
| options | Monday ... Sunday (or pulled from data) |
| default + source | Monday (asked, can change) |
| needed by | `labor_pct`, `declining_budget`, `sales_by_week` |
| ask when | first use / setup interview / never (infer only) |
| can infer from | "sales export dates", "Airtable Financial.Week" |

Starter skeleton (examples, not final):

- **Business**: name, type (bar, restaurant, food hall, hotel, group), locations, time zone, currency.
- **Locations**: each location's name, address, revenue centers (bar, hall, patio, events, catering), outlets/stalls.
- **Calendar**: week start, fiscal year start, period type (weekly, 4-4-5, monthly), day close time.
- **Sales / POS**: which POS (Toast, Square, Clover, Lightspeed, SpotOn, other, spreadsheet), how data arrives
  (connector, nightly export, emailed report, CSV upload), what counts as net sales, how comps/voids/discounts appear.
- **Labor**: roles, hourly vs salaried, scheduling tool, payroll tool, whether tips are in labor %.
- **Purchasing**: vendors/distributors, delivery days, how invoices arrive, where prices live today (spreadsheet,
  Airtable, accounting system).
- **Accounting**: chart of accounts (start from a restaurant template, rename/add by talking), accounting system.
- **Targets**: labor %, COGS % per category, comp % limit, prime cost, weekly budgets by account group.
- **Menus and recipes**: menu types, seasons, default views, units (oz vs ml), house pour sizes,
  house technique rules (e.g. stir 6 to 8 seconds).
- **People and permissions**: who can approve prices, publish menus, see labor and pay.
- **Voice and style**: how much detail, spoken number style, name Harmony uses for them, when to open the app.

### 4B.2 Account settings (the answers, per business)

`phg.account_settings`: `account_id, key, value, source (asked | inferred | imported | default), confidence,
confirmed_by, confirmed_at, history`. Harmony can always say where a value came from and change it on request
("actually our week starts Tuesday").

### 4B.3 How setup happens in conversation

1. **Just in time** (default): when a question needs a missing setting, Harmony asks it once, then answers.
   "Labor % needs your week. Does your week start Monday?" -> "Tuesday" -> saved -> answer.
2. **Guided setup** (optional): "Harmony, let's set up my business" runs the skeleton group by group, skipping
   anything it can infer, and can stop and resume any time ("let's finish setup").
3. **Infer, then confirm**: from an uploaded POS export, Airtable base or spreadsheet, Harmony proposes values
   ("Your exports show weeks starting Monday and two revenue centers, Bar and Hall. Right?").
4. **Connect a data source by talking**: "Which POS do you use?" -> picks the adapter for that POS (or "other") ->
   "How can you get me the data: a connection, a nightly export, an emailed report, or uploading a file?" ->
   Rob/owner provides a sample -> Harmony proposes the column mapping (uses the existing
   `phg.sales_import_mappings`) -> owner confirms -> saved and reused for every future import.
5. **Setup status**: "What's left to set up?" lists missing settings by what they unlock ("Add your labor
   targets to get labor alerts").

### 4B.3a The setup walkthrough (visual, then automatic)

Setting up a business is a guided, on-screen walkthrough that Harmony talks through, step by step:

1. **The business and its places**: name, type, locations, revenue centers, calendar (week start, periods).
2. **Who you buy from and pay**: suppliers, distributors, service providers (linen, pest control, music, repairs,
   POS, utilities), landlords. Harmony asks, fills in what it can from uploaded invoices, email or spreadsheets,
   and shows each one as a card to confirm (name, kind, contact, delivery days, default account).
3. **How you code invoices**: the chart of accounts (start from the restaurant template, rename or add accounts)
   and the coding rules, shown on real example invoices: "Breakthru lines for liquor go to 5100-01; their bar mix
   lines to 5200. Right?" Each confirmed answer becomes a rule.
4. **Sales and labor sources**: which POS and scheduling or payroll tools, and how data will arrive.
5. **Targets and budgets**: labor %, COGS % by category, comp limit, weekly budgets by account group.
6. **Review**: a summary screen of the financial model, with anything still missing and what it unlocks.

After setup, the model runs itself: new invoices are coded by the confirmed rules (asking only when unsure),
new parties are proposed when they first appear, metrics and views update as data arrives, and every later
conversation adds to or corrects the model. Stored in `phg.parties` and `phg.invoice_coding_rules` plus the
setting tables (drafts 02 and 04).

### 4B.4 Harmony learns the business (memory)

- **Glossary**: the business's own words mapped to PHG things ("hall" = revenue center Hall; "the stalls" =
  outlets; "well vodka" = house pour item). Learned when Harmony asks "By 'hall' do you mean the Hall revenue
  center?" and gets a yes.
- **Facts and preferences**: "prices are always rounded to the dollar", "Fridays have live music", "don't read
  me decimals". Stored with source and date; shown in a "What Harmony knows about you" page where anything can
  be corrected or deleted.
- **Habits**: frequent questions become one-tap shortcuts and faster defaults (always Bar revenue center,
  always last week).
- Memory is per business and per person; never shared across accounts.

### 4B.5 Admin layer (Rob)

Rob manages the skeleton itself: setting definitions, question wording, starter views, chart-of-accounts
templates, metric definitions, POS adapters, and the question bank. Each business only answers; the admin
decides what can be asked. Changes apply to every business without code.

## 4C. Projects and users: one Harmony per project, tuned per person

Each login opens a **project** (a business, group or venue). Harmony's whole model belongs to that project; switch
projects and Harmony is a different assistant with different data, settings, words and memory. On top of that,
each person gets their own layer inside the project.

### 4C.1 Layers

| Layer | Belongs to | Holds | Shared with |
|---|---|---|---|
| **PHG shared knowledge** | Everyone | Market data (41k venues, 12k menus, brands, NOMs, labels, census), classic specs, finance and design knowledge, the admin skeleton and templates | All projects, read-only |
| **Project** | One business (`phg.accounts`) | Settings (4B), glossary, saved views and filters, recipes, menus, ingredients, vendors, costs, sales, labor, budgets, data-source mappings, project memory, Harmony device keys | Only members of that project |
| **Person in project** | One user in one project (`phg.account_memberships`) | Role and permissions, voice and detail preferences, personal notes and reminders, habits, parked jobs, conversation history | Only that person (admins can see the setup, not the private notes) |

### 4C.2 Rules

- A user can belong to several projects (e.g. Rob as admin, a consultant, a group owner). Harmony always knows the
  current project, says it when it matters, and switches only when asked ("switch to Parkway").
- Every project table carries `account_id`, protected by row-level security and the existing membership check
  (`phg_harmony_inbox_db is_member` pattern). Gap to fix: `phg.recipe_projects` / `recipe_versions` and some
  flavor tables have no `account_id` yet (PHG-FLV-006).
- Harmony's memory, glossary and learned facts are stored with `account_id` (and `user_id` for the person layer)
  and are never used in another project. Learning from one business never leaks into another's answers.
- Roles per project: owner, admin, manager, staff (names editable in the skeleton). Roles decide who can approve
  prices, publish menus, see labor/pay, change settings, connect data sources.
- Action button keys are already tied to one project (`harmony_device_keys.account_id`); a person with several
  projects makes one key per project or says "switch to ..." at the start.
- The PHG admin (Rob) manages the shared layer and the skeleton, and can enter a project only as a member of it.
- **What carries over vs what doesn't** (Rob, 2026-09-28): functions, capabilities, templates, the skeleton and
  shared knowledge work the same in every project and for every user. Anything **created** in a project (views,
  files, records, recipes, preps, menus, ingredients, costs, notes) stays in that project and is never carried
  into another.
- **Cross-project export (tabled, PHG-043)**: a deliberate, user-started link or export that copies chosen items
  (e.g. a recipe, a menu or a view) from one project to another the user belongs to, with provenance kept. Not built now.

## 4D. The profit coach

### 4D.1 What already exists

Registered capabilities `management_dashboard`, `management_operations` (alert lifecycle, management inbox, report
snapshots), `management_variance` (arithmetic bridge of period changes: volume, mix, price, discounts, comps),
`menu_engineering` (item mix, contribution), `recipe_costing`, `inventory_analysis` (theoretical vs actual use),
`budget_forecasting`, `period_review`, and tables `management_alert_*`, `management_variance_snapshots`,
`menu_engineering_snapshots`. PHG also has something no single restaurant has: **market prices and menus for
41,886 venues**, so it can compare a business's prices with the real market around it.

### 4D.2 How it works

1. **Signals**: every metric (4A.2) per period, per location and revenue center, compared with the business's
   target, its own history (last week, same week last year, trend) and the market (PHG menu prices nearby, and
   anonymised peer benchmarks once enough businesses opt in).
   (The example findings below use made-up numbers to show the format.)
2. **Detectors**: an admin-editable library of checks, each with a data requirement, a rule and a dollar-impact
   formula. Starting set:

| Area | Detector | Example finding |
|---|---|---|
| Labor | labor % over target; hours by role vs sales per hour; scheduled vs actual; overtime | "Labor was 27% this week vs 22 target: Tuesday and Wednesday nights had 2 bartenders at under $300 sales/hour. About $610 over." |
| COGS | category COGS % drift; theoretical vs actual (waste, overpour, theft, missing invoices) | "Liquor COGS 24% vs 19% theoretical: about $1,150 unaccounted this period." |
| Waste | inventory variance by item; prep yield vs recipe | "You're losing about $180 a week on citrus: usage is 30% over what sales explain." |
| Pricing | item margin vs target; price vs nearby market for the same drink; price not updated after cost rises | "Your Margarita is $9; 38 bars within 5 miles charge a median $12. At your volume, +$2 is about $420 a month." |
| Menu mix | menu engineering quadrants (stars, plowhorses, puzzles, dogs); items to reprice, reposition or cut | "Espresso Martini sells well but earns $3.10; raise $1 or swap the vodka." |
| Purchasing | vendor price increases; category spend trend (e.g. dairy); cheaper equivalent products; order vs par | "Dairy spend is up 22% in 6 weeks, mostly heavy cream from one vendor." |
| Comps and discounts | comp % over limit; by staff, by day | "Comps were 4.8% last week vs a 2% limit, 70% on Friday." |
| Budget | declining budget pace; forecast to overspend | "At this pace you'll overspend bar supplies by $240 this week." |
| Calendar and setup | reporting periods that don't match the business rhythm; missing data that blocks answers | "Your week starts Monday but your busiest block is Thu to Sun; a Thursday week start would make weekly labor comparisons cleaner." |

3. **Findings**: each has the problem, the dollar impact (per week, month or year), the evidence (numbers and
   source records, tappable), confidence, and 1 to 3 actions. Ranked by dollar impact times confidence, so the
   biggest real money comes first.
4. **Delivery**: a weekly brief (spoken or on screen), live alerts for big items, and answers when asked ("where
   am I losing money?", "what should I raise prices on?"). Harmony uses the same voice rules: headline and dollars
   first, one driver, offer the detail.
5. **Action**: Harmony can carry out the fix as a proposal: reprice items, change a par level, adjust a schedule
   template, switch a recipe ingredient, set a new reporting calendar. Same approval rules as section 10.
6. **Follow-up and learning**: each finding records whether it was acted on and what the metric did afterwards.
   Harmony learns which advice pays off for this business (and, anonymised and opt-in, across businesses) and
   stops repeating advice that is ignored or wrong. Dismissed findings stay dismissed unless the numbers get worse.

### 4D.3 Guardrails

- Numbers come from database functions only; the model explains, it never calculates money.
- No finding without enough data; otherwise Harmony says what data is missing and how to add it (ties to 4B setup).
- Every recommendation shows its evidence and assumptions; market comparisons name the sample (how many venues,
  where, how recent).
- Peer benchmarks use anonymised aggregates only, from businesses that opt in; one business's data is never shown
  to another.

### 4D.4 Tables (new, with the finance phase)

`phg.coach_detectors` (admin library: key, area, requirement, rule, impact formula, thresholds, wording),
`phg.coach_findings` (account, detector, period, impact $, confidence, evidence, status: new / seen / acted /
dismissed / resolved), `phg.coach_actions` (finding, proposal id, outcome, metric before/after). Builds on
`management_alert_*` rather than duplicating it.

---

## 5. How Harmony talks: jobs, slots and questions

### 5.1 Jobs

Every request becomes a job: `{kind, slots, status, source turn, result, parked_at}`. Kinds:

| Kind | Examples |
|---|---|
| **find** | "all the margaritas at X in Denver", "where is NOM 1610", "average price of a Paloma in Iowa" |
| **explain** | "why is our COGS up", "what makes this brand different" |
| **build** | new cocktail, new prep recipe, new dish (later), new menu, new menu item |
| **organise** | save a view or filter, rename, "show me everything for Spring 2028", "by week" |
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
| new cocktail | name (or "untitled"), destination (a menu, or later) | family, base spirit, season, target price, glass, garnish | draft status |
| new prep recipe | name, ingredients + amounts, method | yield, shelf life, storage, menu | saved as a draft prep if no menu given |
| save | what (defaults to the current job's result) | which menu, tags | saved as a normal record |
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
| Destination | "Add it to the Spring 2028 menu, or keep it as a draft for later?" |
| Menu missing | "There's no Seasonal 2026 menu yet. Start one?" |
| New ingredient | "I don't have 'Tajin salt' yet. Add it as a new ingredient?" |
| Ambiguous ingredient | "Salt: kosher, sea salt or table salt?" |
| Unit | "Is that grams or ounces?" |
| Yield | "What does the batch make, roughly?" |
| Template now or later | "Set up the menu template first, or just the recipe for now?" |
| Confirm write | "Save 'Citrus Brine' as a prep recipe for the Spring 2028 menu? Say yes to save." |
| Interrupted | "Sorry, go ahead." then later "Want me to finish the Manhattan, or save it for later?" |
| Too broad | "That's 4,000 venues. Narrow it by city, type, or cocktails only?" |
| No data | "I don't have [X] for [place]. Closest I have is [Y]. Want that?" |

---

## 6. Views and filters (no folders)

Decision (Rob, 2026-09-29): **no folders.** Everything anyone builds by talking to Harmony is stored as ordinary
rows in the database (recipes, preps, ingredients, menu items, parties, invoices, costs, notes, settings). People
find and organise it with **saved views and filters** over those tables, the same way for every kind of data.

### 6.1 Filters

- **Time filters**, defined per business from its calendar settings (4B): 1 week at a time, 2 weeks at a time,
  4 weeks, a month, a quarter, period to date, same period last year, or any custom window ("Thursday to Sunday").
  Each is a named preset that resolves to start and end dates from any as-of date, so "last two weeks" and "the
  two weeks before that" always mean the same thing.
- **Field filters**: any column the knowledge map (section 4) knows, e.g. category = dairy, vendor = Breakthru,
  GL account starts with 5100, cocktails with tequila, menu items over $14, recipes missing a cost.
- Filters are **said or tapped** ("just dairy", "only Breakthru invoices", "by week"), saved with a name when the
  person wants to reuse them ("save that as Dairy spend"), and belong to the project, or only to that person.

### 6.2 Views

A view = what (one kind of thing, or a set of metrics) + filters + time preset + grouping + columns + sort +
display (table, bars, tiles, map, dashboard). Examples:

| View | What it shows |
|---|---|
| Dairy costs, week by week | purchase lines where category = dairy, grouped by week, last 12 weeks, bars |
| Spring 2028 menu | menu items where menu = Spring 2028, with recipe cost, price, COGS %, missing costs |
| Labor by role, two weeks at a time | labor hours and $ by role, grouped by 2-week period, vs target |
| Prep book | prep recipes, grouped by type (syrups, brines, batches), with batch cost |
| Declining budget, this week | budget remaining by GL group for the current week, pace bar |

"Show me dairy costs one week at a time" becomes a view on the fly; "save it" keeps it; "open Dairy costs" brings
it back; "now by month" changes only the time grouping. Harmony can pin views for the weekly brief.

### 6.3 Storage

`phg.time_presets` (per business), `phg.saved_filters`, `phg.saved_views`, all project-scoped with an optional
owner. Views resolve to a read-only query through the knowledge-map gateway (4.3); they never store copies of
data. Drafted in `supabase/migration_drafts/03_saved_views_and_filters.sql`.

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
         already there. Costs are pending until we have prices. Save it as a prep recipe for the Spring 2028 menu?
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
7. **Save**: one proposal: create the prep/recipe + new ingredients (+ link to a menu if asked). One yes.
8. **Drinks** use the same loop with bar units, a method (stir 6 to 8 seconds, shake hard), glass,
   garnish, and optional link to a house menu item and a price.

### 7.3 New write actions needed in the Command Center

`save_filter`, `save_view`, `update_view`, `archive_view`, `create_party`, `create_coding_rule`,
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
| Views | `open(view)`, `group(week / 2 weeks / month)`, `filter(field, value)`, `save` | "open Dairy costs", "now by month", "just Breakthru", "save that" |
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
  (create a draft, save a view, note, new ingredient). Prices, publishing, deleting and
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
| 4 | **Views and filters** (time presets, saved filters, saved views, spoken and tapped) | Migration: view tables + new write actions |
| 5 | **Voice building** of recipes and preps (capture loop, ingredient matching, nested preps, save to a menu, cost pending) | New Command Center actions |
| 6 | **Talk-over** in the app (option 1, then maybe realtime) | Frontend + tuning on Rob's phone |
| 2A | **Projects, setup skeleton + finance data**: project/person layers and RLS audit (add account_id where missing), setting definitions, account settings, glossary/memory, guided setup, data-source adapters and mappings, chart-of-accounts template, metric functions | Migration; Rob as admin writes the first skeleton with Harmony |
| 7 | **Costing live** in Finance views as prices arrive | Airtable prices first, invoices later |
| 8 | **Profit coach**: detectors, findings with $ impact, weekly brief, actions as proposals, outcome learning; market price comparison first (data already here) | Finance data from 2A; migration |
| Later | Invoice photos -> vision model -> prices; food side; native iPhone app | Separate decisions |

Each phase ships with conversation tests (existing `conversation_tests` table) covering the dialogs
above, run before every deploy.

---

## 12. Decisions for Rob (as admin)

1. Start order: recommend Phase 1 (map control, no migration), Phase 2 (knowledge map) and Phase 2A (setup
   skeleton) together, since every later feature reads settings.
2. Approve the migrations as each phase starts.
3. Voice approval: is a spoken "yes" enough for drafts, views, ingredients and settings? (Recommended yes;
   prices, publishing and deletes stay on-screen.)
4. Model cost: stronger model for the dialogue manager and navigator (recommended).
5. Business-specific details (POS, week start, targets, accounting system) are **not decided here**: each business
   answers them through Harmony. Rob's Parkway FH Airtable is the first test business.
