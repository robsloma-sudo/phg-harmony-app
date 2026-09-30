# Airtable "Parkway FH" -> PHG Supabase: sync plan

Status: **plan only. Nothing has been written to Supabase or Airtable.** Prepared 2026-09-29 (read-only).
Source: Airtable base `appYRF92Tt7lXkB0V` ("Parkway FH"). Target: Supabase project `lqjtwabzmgjcufftuqvu`, schema `phg`.

Where the files are (scratchpad, outside the git repo):
`/tmp/claude-0/-home-user-phg-harmony-app/c0df8ae8-562c-5574-b6e9-9bdd13434505/scratchpad/airtable/`

- `<table_slug>.json`: the raw Airtable pull, restricted to the fields listed below. Fields are keyed by name, and select values are flattened.
- `_schema_field_types.json`: field name -> Airtable type, with the credential and contact fields removed.
- `gen_sql.py`: builds every `load_*.sql` from the JSON files. To re-sync, pull again and re-run it. `ACCOUNT_KEY` and `LOCATION_KEY` are set at the top of the script.
- `load_00 ... load_23 *.sql`: the load itself. It has not been run against Supabase. Section 7 describes how I checked it.
- `_load_stats.json`: row counts and the review list the generator produced.

---

## 1. Record counts and what loads

| Airtable table | Records | Target(s) | Rows produced | Runnable |
|---|---|---|---|---|
| Bar Inventory/Pricing | 316 | `ingredients`; `procurement_catalog_items`; `purchase_costs`; `inventory_count_sessions` + `inventory_counts` | 315 ingredients, 293 catalog items, 315 costs, 1 session + 547 counts | now (ingredients: better after 04, see D4) |
| Bar Recipes | 213 (28 cocktails, 159 linked lines, 26 unlinked lines) | `recipe_projects` / `recipe_versions` / `recipe_components` | 28 / 28 / 125 | now; Harmony can only see them after 04 plus `load_23` |
| Invoices | 469 | `purchase_invoices` + `purchase_invoice_lines` (GL 5xxx); `operating_expenses` (GL 6xxx) | 233 headers (2 void duplicates), 280 lines; 261 expense rows; 7 skipped | now |
| Manager (daily log) | 173 | `sales_imports` (1) + `sales_daily` | 342 rows (171 Bar + 171 Food Hall Stalls) | now |
| Financial (weekly) | 23 | `reporting_periods` (entered values go in metadata) | 22 (1 blank row skipped) | now |
| Vendors/People/Login Info | 168 | `vendors` (now); `parties` (draft 02); `invoice_coding_rules` (02 + 04) | 106 vendors; 131 parties; 19 rules | vendors now; the rest after 02 |
| Employees | 21 | `labor_roles` (job titles only) | 8 roles | now |
| Invoices GL columns | 57 currency columns | `gl_accounts` (account-level, `source='imported'`) | 41 extra codes (the 14 template codes are seeded by 04) | after 04 |
| Menus | 67 (1 blank) | none | not loaded | see section 5 |
| Events/Marketing | 114 | none | not loaded | see section 5 |

## 2. What is in Supabase today (read-only inspection)

- `phg.accounts`: 1 row, `phg_ops_test` "PHG Ops Test" (America/Denver). `phg.sales_locations`: 1 row, `phg_ops_test_location`.
- These tables are empty: `vendors`, `procurement_catalog_items`, `purchase_costs`, `purchase_invoices`, `purchase_invoice_lines`, `operating_expenses`, `labor_roles`, `reporting_periods`, `inventory_counts`, `inventory_count_sessions`.
- These tables already have rows:
  - `ingredients`: 6 generated drafts, such as `rye_whiskey`. There are no `pfh_` keys, so nothing collides.
  - `recipe_projects` / `recipe_versions`: 5 / 6 beta seeds.
  - `sales_daily`: 1 test row.
  - `budget_plans`: 1 row.
  - `expense_categories`: 19 generic categories.
  - `units`: 13 rows, including `oz` (fluid), `lb`, `each` and `dash`. There is no mass-ounce unit.
- **No account column** on `vendors`, `ingredients`, `procurement_catalog_items`, `purchase_invoices`, `purchase_costs` or `operating_expenses`. These tables are scoped by `location_key`, and `ingredients` and `vendors` are global.
  - Harmony's knowledge map shows `purchase_costs`, `purchase_invoices`, `operating_expenses` and `inventory_counts` only when `location_key` belongs to the project's `sales_locations`. That is why every row gets `location_key = 'parkway_fh'`.
- Constraints the load has to meet:
  - `purchase_invoices` has a unique `(vendor_id, invoice_number)` where status is not void. Duplicates are handled as described in section 6.
  - `operating_expenses` has a unique `(location_key, source_system, source_ref)`. The load uses this as its upsert key.
  - `operating_expenses` sign check: an expense must be > 0 and a credit < 0.
  - `sales_daily` needs an `import_id`, and has a unique `(import_id, business_date, revenue_center)`.
  - `procurement_catalog_items` needs `vendor_id` and `vendor_sku`, and has a unique `(vendor_id, vendor_sku)`.
  - `recipe_components` needs quantity > 0 and a unit that is in `phg.units`.
  - `budget_plans.menu_project_id` is NOT NULL.
  - `inventory_count_sessions.id` has no default.
- **Drafts not applied:**
  - Draft 02 (`phg.parties`, `phg.invoice_coding_rules`): confirmed absent.
  - Draft 04 (`phg.gl_accounts`, `metric_definitions`, and `account_id` on `ingredients` / `recipe_projects` / `recipe_versions` / `prep_recipes`): confirmed absent.

## 3. Field-by-field mapping

Common to every table:
- **Idempotency.** Each row's `id` is `md5('pfh:<kind>:<airtable record id>[:<qualifier>]')::uuid`, and every insert is `on conflict ... do update`. Re-running a file after a new pull updates the same rows.
- **Where the Airtable id is stored.** It goes in `metadata`, `brief`, `rationale` or `source_payload` as `airtable_record_id`, and in `source_ref` where the table has that column.
- **Tagging.** Every row is tagged with `source='airtable'` and `source_base='appYRF92Tt7lXkB0V'`.

### 3.1 Bar Inventory/Pricing -> ingredients / catalog / costs / counts

| Airtable field | Target | Rule |
|---|---|---|
| Item | `ingredients.name` (trimmed); `ingredient_key = 'pfh_' + slug(name)` | The untrimmed original goes to `aliases`. 15 names have stray whitespace. |
| Type, Sub-Type | `ingredient_type`, `category` | Whiskey, gin, agave etc. become `spirit`. Liqueur/Amaro becomes `liqueur`, Bitters `bitter`, Bottle Batch `batch`, Fortified Wine/Vermouth `fortified_wine`, and the wine subtypes `wine`. Draft and Beer become `beer`, Cider `cider`, Non-Alcoholic `na_beverage`, Grocery `grocery`. |
| Volume (oz) | `purchase_costs.package_size` and `procurement_catalog_items.container_size` (unit `oz`) | Draft = `keg`: 1984 oz is a 1/2 bbl, 661 oz a 1/6 bbl. Grocery items with lb or # in the name are mass: size = oz / 16, unit `lb`. Grocery rows with volume = 1 are count items, so size is NULL and unit is `each`. |
| Bottle/Unit Cost | `purchase_costs.cost`, per one container | `package_quantity = 1`. `package_unit` is one of bottle, can_or_bottle, keg or each. |
| Case Size | `procurement_catalog_items.containers_per_purchase_unit` | `purchase_unit` is `case` when the case size is > 1, `keg` for draft, and `each` otherwise. |
| Distributor (link) | `procurement_catalog_items.vendor_id`, one row per distributor; `purchase_costs.vendor_key` (first distributor) | `vendor_sku = 'AT-<record id>'` because Airtable has no SKU. |
| Main Bar, Liquor Room, Keg Cooler, Main Bar - Cloud | `inventory_counts.quantity`, one row per non-empty area, `unit='each'` (containers) | All counts go in one session, 'Airtable snapshot', dated at the latest Last Modified (2025-07-30), `status='draft'`. |
| Par, Location, Current Inventory, the nine "Sale Price" fields | `ingredients.metadata` | Kept as reference. See section 5 for why sale prices are not loaded to menus. |
| Last Modified Date & Time | `purchase_costs.effective_from` (date) | A later sync with a changed cost inserts a new cost row, and the previous row's `effective_to` is closed. |

Skipped:
- The formulas Case Price, Oz Price, Total Volume, Total Inv. Cost, all "COG's" fields, Item TOTAL, Low Inventory and Total Inventory.
- The order-quantity fields.
- The E-mail lookup.

**Oz Price is not trusted.** The per-oz cost is recomputed as `cost / package_size`. As a check, the formula matched `cost / volume` on all 314 rows where it had a value. The other 2 rows show "Infinity" because their volume is blank.

### 3.2 Bar Recipes -> recipe_projects / recipe_versions / recipe_components

The table mixes two kinds of row:
- **Cocktails** (28 rows): these have `Ingredients` links.
- **Recipe lines** (185 rows): for example ".25oz Amaro Nonino". Of these, 159 link to an inventory item through `Item Lookup` and 26 do not.

| Airtable | Target | Rule |
|---|---|---|
| Cocktail row, `Item` | `recipe_projects.name`, `recipe_versions.recipe_name` / `cocktail_name` (version 1) | |
| Cocktail Status | project `status` and version `status` | Current becomes active / approved. Retired becomes completed / superseded. Blank (10 rows) becomes active / draft. |
| Cocktail Type, Sale Price | `recipe_projects.brief`; `recipe_versions.targets.sale_price` | |
| Ingredients (links to lines) | `recipe_versions.ingredients` (jsonb list, every line) | |
| Linked line: Volume(oz) + Item Lookup | `recipe_components` (ingredient_id, quantity, unit `oz`) | 125 components. If Volume(oz) is blank, the quantity is parsed from the line name (".75oz ..."). Dashes are already given in oz (0.0625). |
| Unlinked line | kept only in `recipe_versions.ingredients` with `kind: 'unlinked'` | 20 references. These are house syrups, purees, water, soda and 2 spirits with no inventory row. |

Skipped:
- The formulas Ingredient Cost, COG's and the float COG's.
- The Oz Price lookup.
- Cocktail Cost (rollup). It is kept in `rationale` only as a reference, because cost is recomputed from `purchase_costs`.

### 3.3 Invoices -> purchase_invoices / purchase_invoice_lines / operating_expenses

Airtable has no item lines. Each invoice record carries one amount per GL-code column: 57 currency columns such as `5100-01 Liquor` and `6315-Music & Entertainment`.

| Airtable | Target | Rule |
|---|---|---|
| GL columns 5xxx (5100-01/02/03, 5200, 5420-xx) | 1 `purchase_invoices` header per invoice + 1 `purchase_invoice_lines` row per code | `raw_description` is the GL code and name, `resolution_status='unresolved'`, and `metadata.gl_code` is set. The header `total` is the 5xxx portion only. |
| GL columns 6xxx | 1 `operating_expenses` row per invoice per code | `source_ref = '<record id>:<code>'`. `category_id` comes from a GL -> `expense_categories` mapping, which is approximate (list in `gen_sql.py`, `OPEX_CAT`). The exact code is kept in `metadata.gl_code`. |
| Total Amount | the sign of all amounts | A negative total is a credit, but Airtable stores the GL amounts as positive. Credit lines are therefore signed negative (`line_type='credit'`, `entry_type='credit'`). 4 invoices are credits. |
| Distributor/Vendor | `vendor_id` via `vendors.vendor_key` | |
| Invoice Number | `invoice_number` | Duplicate handling is described in section 6. |
| Delivery Date, else Date Submitted | `invoice_date` / `expense_date` | |
| Due Date, Payment Type, Type, Financial (week link) | `raw_payload` / `metadata` | Payment Type is reduced to `ap`, `card` or `payout`. Card digits and the cardholder's name are dropped. |
| GL columns but no amounts (22 invoices) | | If there is exactly one `Type`, the whole total is coded to it. Otherwise the invoice goes to review. |

Skipped:
- Photo of Invoice (attachment).
- Processed (always blank).
- All rollup formulas.
- Name (from Distributor) lookup.

Header status is `validated` (decision D2).

### 3.4 Manager (daily log) -> sales_daily

A single `sales_imports` row is created with `source_system='airtable'` and `content_hash='appYRF92Tt7lXkB0V/tbl0YAlLLsoF8r1s0'`. Two revenue centers are loaded per date:
- `Bar`: `net_sales` = Bar Net All Day.
- `Food Hall Stalls`: `net_sales` = Hall Net All Day. Decision D5: these are the stalls' sales, not PHG revenue.

`source_payload` holds:
- Bar Net 11-3pm, Ftn Drink Sales, Bar EOW Sales, Bar Order Total, Weather and Shift Rating.
- Hours by role (Bartender, Barback, Bar Lead, Porter, Closing Keyholder, Training).
- The Airtable "Total Hourly Labor $". It is a formula with hidden rates and is labeled "not trusted".

Skipped:
- Closing Manager (a person's name).
- The free-text notes: shift, live music, repairs, notes for opening manager, financial and staffing notes. These may name staff or guests.
- All formulas and rollups.

Hours are not loaded to `labor_shifts`, which requires an `employee_id` per shift.

### 3.5 Financial (weekly) -> reporting_periods

- `period_key = 'airtable:<record id>'` and `period_type='week'`.
- Start and end dates are parsed from the label, for example "Week 2 - 3.24.25 - 3.30.25 (Inventory)".
- Entered values go into `metadata.entered_values`:
  - beginning and ending inventory in dollars by category (liquor, beer, wine, N/A);
  - net sales by category, discounts, purchases by category;
  - forecast, variance, and the seven "Budgeted <day> Sales" fields.
- Rollups (Total Bar Sales, Total Hall Sales) are kept as reference only. All formula fields (COG's, budgets, percentages, net income) are skipped. They can be recomputed from `sales_daily`, `purchase_invoices` and `operating_expenses`.
- The category dollar totals do not fit `inventory_counts`, which is per item.

### 3.6 Vendors/People/Login Info -> vendors / parties

Only these fields were requested from Airtable: Name, Contacts, Type, Delivery Days, Website, Location, Category, Service/Product, Price/Rate, Rating, Notes/Details. **Username and Password were never requested.** Phone Number, E-mail, Graphics and Social Media were not requested either.

**`vendors` (now), 106 rows:**
- `vendor_key = 'pfh_' + slug(name)` and `name`. `metadata` holds the Airtable record ids and types. Nothing else is stored.
- A row is included if it is typed Distributor, Supplier or Service Provider, or if an invoice or inventory item references it.
- These rows are excluded:
  - 29 rows typed only "Login Credentials" that nothing references (wifi, lockboxes, app logins).
  - 5 junk rows ("j", "black", "taylor", a blank row, and one employee name).
  - Musicians, entertainers and popup vendors that are never invoiced. These go to parties only.
- Merged duplicates:
  - Staples, Indeed, Instagram, MailChimp, Longmont Chamber of Commerce and ResQ Coffee each appear twice.
  - Fed Ex and FedEx are one vendor.
  - Linxspire and Linxspire LLC are one vendor.
  - CSA and Crooked Stave Artisans are one vendor.
- Three login-typed rows are loaded as plain vendor names only, because invoices reference them: Amazon, Moxie/USFoods and Canva.
- A vendor row named after an employee is referenced by 1 invoice. That invoice is mapped to a neutral `pfh_staff_reimbursement` vendor.

**`parties` (after draft 02), 131 rows:**
- Columns: `kinds` (from Type), `contact_name` (Contacts), `website`, `delivery_days` (mon..sun), `vendor_id`, and `notes`.
- `notes` holds Category, Service/Product, Price/Rate, Rating and Notes/Details, plus the Airtable ids. "On-Demand" delivery becomes a note.
- `email` and `phone` stay NULL. A Location value on a login row is dropped, because it is access information.
- Notes that mention an employee's first name are dropped (1 row).

**`invoice_coding_rules` (after 02 + 04), 19 rows:**
- A rule is created for each vendor with at least 2 invoices coded to a single GL code, where one code covers at least 80% of them.
- `source='imported'`, `confidence` = that share, and `confirmed_by` is NULL.

### 3.7 Employees -> labor_roles

Only Employee and Job Title were requested. **No names are loaded anywhere.** `labor_roles` gets 8 roles:
- The 5 Job Title values: Bartender, Barback, Porter/Busser, Manager, Line Cook/Cashier.
- 3 roles that appear only as hour columns in the Manager log: Bar Lead, Closing Keyholder, Training.

Each role's headcount is kept in metadata.

### 3.8 GL chart (after draft 04)

`load_22` inserts the 41 GL codes that the Invoices table uses and that are not among the 04 template codes, as account-level `gl_accounts` rows with `source='imported'`. For each code it sets:
- the parent code (6230-05 -> 6230 -> 6200, and so on);
- the type (cogs, labor or operating_expense);
- the COGS category (liquor, beer, wine, bar_mix, na_bev);
- the budget group (bar_cost, food_hall, facility, g_and_a, marketing);
- the matching expense-category key.

## 4. What depends on the unapplied drafts

| Needs | Files | Why |
|---|---|---|
| Draft 02 | `load_20_parties.sql`, `load_21_invoice_coding_rules.sql` | `phg.parties` and `phg.invoice_coding_rules` do not exist yet. |
| Draft 04 | `load_21` (GL codes it refers to), `load_22_gl_accounts.sql`, `load_23_account_backfill.sql` | `phg.gl_accounts` does not exist, and `account_id` is not yet on ingredients or recipes. |
| Draft 04 (visibility only) | `load_02`, `load_05` | They can run now. Until 04 plus `load_23` run, Parkway ingredients look like "shared library" rows, and the recipes are invisible to Harmony, which scopes recipes through `menu_items` for now. |

## 5. Skipped on purpose, and why

- **Credentials.** Username, Password, and every row typed only "Login Credentials". These were never requested, stored or printed.
- **Personal data.**
  - Employee phone, email, emergency contacts, TIPS certification files, and the onboarding and offboarding checkboxes.
  - Employee names.
  - Vendor phone and email.
  - Manager "Closing Manager" and the free-text notes.
  - The cardholder names and card digits in Payment Type.
- **Formulas, rollups and lookups.** All of them. They are recomputed in Supabase from the loaded base values: Oz Price, COG's, Case Price, labor $, and the budget and percent fields.
- **Attachments.** Invoice photos, graphics, TIPS certificates.
- **Menus (67).** These are catering menus owned by the food stalls (Hesher BBQ, HipPops, Hatchet, Chile Con Quesadilla, Spice Fusion), not PHG's bar menu. There is no fitting target table. They could go to `workspace_records` once draft 02 is applied.
- **Events/Marketing (114).** No target table exists. Booking Price (9 events) is already represented by the 6315 Music & Entertainment invoices. Candidate target: `workspace_records` after draft 02.
- **Catering/TripleSeat and Cleaver/Shawarma.** Not in scope.
- **Keg Shell Deposit.** This is an inventory row but a returnable container, not an ingredient.
- **Budgeted day sales.** They stay in `reporting_periods.metadata`, because `budget_plans` requires a Parkway `menu_project_id` (D3).

## 6. Data-quality issues found

**Inventory**
- 2 items have no Volume: Pickles and one Pinot Grigio. Their Airtable Oz Price shows "Infinity", and `package_size` is NULL.
- 1 can row has a volume of 112 oz for a 12 oz can. It is loaded as is, with `review_flags: suspicious_can_volume`.
- Grocery "oz" values are sometimes weight, not volume: 25 lb Sugar = 400, Strawberries 30# = 480, Coffee 5lb = 80. 4 items are converted to lb and flagged. `phg.units` has only fluid `oz`.
- 3 grocery items are counts with volume = 1 (limes, lemons, oranges, grapefruit). Their size is unknown.
- 26 items have no distributor, so they get no catalog row. 4 items have 2 distributors.
- 59 have no Case Size.
- 20 "Bottle Batch" items are house batches. They should become `prep_recipes` later.
- 15 names have leading or trailing spaces.
- No blank costs. All 316 rows have a Bottle/Unit Cost; the cheapest is $0.98.

**Recipes**
- 26 recipe lines have no inventory link, and 20 of them are used in cocktails. Their costs are unknown.
- 1 linked line (".75oz Grenadine") has no volume, so its quantity is parsed from the name.
- 47 lines are orphans that no cocktail uses.
- 10 cocktails have no Sale Price and no status. Some are placeholders, such as "Tiki Cocktail TBD".
- A misspelled line, "buffralo trace", is unlinked.

**Invoices**
- 5 records are blank or $0 with no vendor, and are skipped.
- 72 have no invoice number and 3 have no date.
- 10 invoices repeat the 6410-05 Office Supplies amount in 6410-10 Postage. This looks like a duplicated field. When Type lists only 6410-05, the copy is dropped.
- The GL split does not match the total on 26 invoices.
  - 5 US Foods invoices leave $100-$230 unallocated: tax or other lines.
  - Some opex invoices are $10 off either way.
  - All differences are recorded in `validation.unallocated_amount` / `metadata.notes`. $207.77 is unallocated on the 5xxx headers alone.
- 4 credits are stored with a negative total but positive GL amounts.
- 7 vendor + invoice-number pairs repeat:
  - 4 are true double entries (same vendor, number, total and delivery date). The later copy is loaded as `void` for COGS, or skipped for opex (2 opex records).
  - 3 are different invoices that reuse a number. These are suffixed `-<rec>`.
- Processed is blank on all 469 records.
- Loaded total is 5xxx $69,162.80 plus 6xxx $56,344.42 = $125,507.22, against $126,721.19 in Airtable's Total Amount. The gap comes from the unallocated remainders, the voided and skipped duplicates, and the dropped 6410-10 copies.

**Manager**
- 2 days have no net sales and 1 day has a $0 bar.
- Labor $ is a formula with hidden rates.

**Financial**
- 1 blank week.
- One record covers 2 weeks ("Week 4 2.03.25-2.16.25") and overlaps "Week 4 - 2.10.25-2.16.25".
- The week labels are inconsistent.
- The last two weeks are empty ($0).

**Vendors**
- 6 names are duplicated, plus 3 spelling or abbreviation pairs.
- 1 row's Contacts field holds a URL. The load skips it.
- 8 rows have no Type.
- 2 rows are named after employees.
- 1 note mentions a staff member.

**Events**
- 6 events end before they start.
- Several recurring events share one name across dates.

## 7. Load order

The files were checked against a **local** throwaway Postgres 16 with mock copies of the target tables, built from the constraints read off Supabase and from the draft 02 / 04 DDL. All files ran cleanly, and a second full run produced identical counts. Nothing was run against Supabase.

**Decisions for Rob first**
- **D1: which project account.** The only account is `phg_ops_test` "PHG Ops Test". The files load into that account under a new location `parkway_fh` ("Parkway Food Hall"). For a real Parkway account, create it, set `ACCOUNT_KEY` in `gen_sql.py` and regenerate.
- **D2: invoice header status.** Currently `validated`. The alternatives are `approved` or `draft`.
- **D3: budgets.** Create a Parkway `menu_projects` row so `budget_plans` can hold the Financial budgets? Or keep them in `reporting_periods.metadata`?
- **D4: timing of the ingredients load.** Load ingredients now (global `pfh_` keys, backfilled by 23), or wait for draft 04.
- **D5: Food Hall Stalls sales.** Load them as a revenue center (current plan), or keep them only as the license-fee base in metadata.

**Order** (each file is one transaction; run as the migration owner or service role):
1. `load_00_location_and_import.sql`: Parkway location and the sales import row.
2. `load_01_vendors.sql`
3. `load_02_ingredients.sql`: see D4.
4. `load_03_catalog_and_costs.sql`
5. `load_04_inventory_snapshot.sql`
6. `load_05_recipes.sql`
7. `load_06_labor_roles.sql`
8. `load_07_sales_daily.sql`
9. `load_08_reporting_periods.sql`
10. `load_09_purchase_invoices.sql`
11. `load_10_operating_expenses.sql`
12. *Apply draft 02*, then `load_20_parties.sql`.
13. *Apply draft 04*, then `load_22_gl_accounts.sql`, `load_21_invoice_coding_rules.sql` and `load_23_account_backfill.sql`.

**Checks after loading:**
- Row counts should match section 1.
- `sum(purchase_invoices.total where status <> 'void') = 69,162.80` and `sum(operating_expenses.signed_amount) = 56,344.42`.
- Spot-check per-oz costs against Airtable Oz Price for about 10 items.
- Confirm Harmony sees the Parkway rows (location scope).

## 8. Anonymised example rows

Inventory item -> ingredient + cost + catalog item. Record `rec04o5F...`, "Apple Cider Vinegar" (Consumable/Grocery, US Foods), 128 oz, $10.73, case of 6, par 2, 4 in the Liquor Room:
```
ingredients:   key pfh_apple_cider_vinegar, type grocery, category Grocery, default_unit oz
purchase_costs: package_unit bottle, package_size 128 oz, cost 10.73 -> 0.0838 $/oz (Airtable Oz Price 0.083828 matches)
catalog:        vendor pfh_us_foods, vendor_sku AT-rec04o5F..., purchase_unit case, containers_per_purchase_unit 6
inventory_counts: liquor_room 4 each
```
Cocktail "Port in the Storm" (Current, Craft, $12). It becomes 1 `recipe_project` (active) and 1 `recipe_version` (approved, `targets.sale_price` 12) with these components:
- 1.75 oz rye
- 0.25 oz Solerno
- 0.25 oz ruby port
- 0.0625 oz orange bitters (2 dashes)
- 0.25 oz spiced pear

Invoice (a US Foods record): total $873.59, split 5420-20 $505.36 / 5200 $196.92 / 6210 $172.31. It produces:
- `purchase_invoices`: total 702.28, with 2 lines, 5200 and 5420-20.
- `operating_expenses`: 172.31 under `smallwares_supplies`, `gl_code 6210`.
- A note: "GL split differs from total by -1.0".

Manager day (2025-03-15, anonymised): 2 `sales_daily` rows.
- `Bar`: net = Bar Net All Day. The payload holds weather, rating, and hours by role (Bartender, Porter and so on).
- `Food Hall Stalls`: net = Hall Net All Day.
