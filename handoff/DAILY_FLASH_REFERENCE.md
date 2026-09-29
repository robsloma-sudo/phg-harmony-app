# Daily flash: what the Parkway Airtable teaches (reference model, not a data source)

Rob 2026-09-29: "The Parkway Airtable data is just an example of how expenses are calculated every day against sales
and labor and everything else and broken down. We will create our own system."

So the Airtable base is **not loaded** into PHG (the load files stay in the scratchpad, unused). It is kept only as a
worked example of the daily and weekly money picture a bar runs on. PHG builds its own version (spec
HARMONY_CONVERSATION_MODEL.md §4A finance, §4B setup skeleton, §4D profit coach; drafts 02-05).

## What the example tracks, and how PHG will do it

| The example (Airtable) | What it measures | PHG's own system |
|---|---|---|
| **Manager daily log**: net sales all day and 11-3 pm, per revenue center (Bar, Food Hall); fountain drinks; order total; weather; shift rating; hours by role (bartender, barback, bar lead, porter, closing keyholder, training); an hourly-labor-$ formula | Daily sales vs labor | `phg.sales_daily` / `sales_items` from the POS connector (Toast etc.) or a daily voice/manual entry; labor from `labor_shifts` x `labor_pay_rates` (real rates, not a hidden formula); weather/shift notes as structured fields |
| **Invoices** coded to GL numbers (5100-6540: liquor, beer, wine, N/A, food, supplies, repairs, marketing...) with a split per GL line | What was bought, into which bucket | `purchase_invoices` + lines with GL codes via `invoice_coding_rules` (draft 02) and the GL template (draft 04); invoice photos later (PHG-039) |
| **Weekly financial**: beginning and ending inventory $ by category, purchases by category, net sales by category, discounts, forecast, variance, budgeted sales for each weekday | COGS % by category = (begin inv + purchases - end inv) / sales; declining budget; net income | `reporting_periods` (draft 03 period presets), inventory counts, and a computed weekly flash: COGS % per category, labor %, prime cost, declining budget remaining, variance to forecast |
| **Bar inventory / pricing**: bottle cost, size, oz price, par | Pour cost per drink | `ingredients` + `purchase_costs` -> recipe cost -> menu item COGS % (costing already in PHG) |
| **Bar recipes** | Specs used for costing | House recipes (`phg.recipe_*`, per project) linked to the shared mixology library |
| **Vendors** | Who supplies what, delivery days | `parties` (draft 02) |

## The daily/weekly numbers PHG must produce (from the example)

- Net sales by revenue center and category; discounts and comps; comp %.
- Labor $ and labor % (hours x rate by role; overtime), by day and week.
- COGS $ and % by category (liquor, beer, wine, N/A, food) on the inventory method, weekly.
- Prime cost (COGS + labor) and prime cost %.
- Declining budget: weekly purchase budget per category = budgeted sales x target COGS %, minus purchases so far.
- Variance: actual vs forecast sales; actual vs budget spend.
- Net income for the week after operating expenses.

Harmony answers all of these by voice ("what's my labor % yesterday", "how much liquor budget is left this week")
once the drafts 02-05 tables exist and a business connects its POS or enters its day.

## Rules carried over

- Never store logins or passwords from a business's old tools (the example had them; PHG-042).
- Staff names, phones and emails are not needed for the numbers; roles and hours are.
