# GL template: bar & restaurant standard (how invoices get categorized)

Rob 2026-09-29: "the invoices and the GLs you see in the Airtable file ... are just an example of what one business
might use to categorize invoices. Use that as an example to build a template off of."

So the example business's codes are **not** loaded as anyone's chart. They were used to design a generic template
that any bar or restaurant starts from and then makes its own by talking to Harmony.

## Files (source of truth, edit these)

| file | what |
|---|---|
| `data/finance/gl_template_bar_restaurant.csv` | the chart: 135 accounts with code, name, parent, type, COGS category, labor class, expense category (`phg.expense_categories` key), budget group, notes |
| `data/finance/invoice_coding_template.json` | how invoices get coded: 10 general rules, 22 line patterns, 36 vendor profiles |
| `scripts/gl_template_sql.py` | generates the SQL draft below from the two files |
| `scripts/gl_template_backtest.py` | checks the profiles against an example coded-invoice export |
| `supabase/migration_drafts/04a_gl_template_bar_restaurant.sql` | **DRAFT, not applied.** Seeds the template; apply right after draft 04 |

## The chart (numbering follows the example, so that style maps 1:1)

| range | section | budget group |
|---|---|---|
| 1200, 1500, 1510 | deposits, equipment, leasehold improvements (so invoices for these never land in expenses) | none |
| 4000-4600 | sales: food, liquor, beer, wine, N/A, merchandise, events, cover, service charges retained | none |
| 4900 | discounts, comps, rewards redeemed (contra revenue) | none |
| 5100 / -01 -02 -03 | bar cost: liquor, beer, wine | bar_cost |
| 5200 / -10 -20 -30 | bar mix: mixers and syrups, bar produce and garnish, ice | bar_cost |
| 5300 / -10..-50 | food cost: meat and seafood, produce, dairy, dry goods, bakery | food_cost |
| 5420 / -10 -20 -30 | N/A: canned and bottled, fountain, coffee and tea | bar_cost |
| 5500 | merchandise cost | other_cogs |
| 6100-6170 | labor: management, hourly (FOH, BOH, bar), overtime, contract, payroll taxes, benefits, workers comp | labor |
| 6200-6270 | operating supplies: paper, linen and uniform, bar supplies, glassware, chemicals, smallwares, catering, menus, decor, freight | operating_supplies |
| 6300-6360 | facility: phone, music and entertainment, TV and internet, hood and grease, pest, CO2, equipment lease, utilities, R&M, security, cleaning | facility |
| 6400-6465 | G&A: office, subscriptions and POS, professional fees, bank and card fees, payroll service, insurance, licenses, travel, training, delivery platform fees, cash over/short | g_and_a |
| 6500-6540 | marketing: advertising, promotions, social and digital, events, signage, donations, loyalty program | marketing |
| 7000-7040 | occupancy: rent, CAM, property tax, percentage rent | occupancy |
| 8000-8120 | below the line: depreciation, amortization, interest, management fees, income tax, other income | none |

What changed from the example: its business-specific group ("food hall") became **operating_supplies**; food COGS,
revenue, labor detail, occupancy, insurance, professional fees and below-the-line accounts were added (the example
had none of them on invoices); code 6200 is now the supplies parent.

## How an invoice gets coded (the vendor profiles)

The example showed the real pattern: **the vendor type predicts the codes, the line decides between them.**
Beverage distributors carry liquor, wine, beer and mixers on one invoice; the broadline food distributor carried
fountain syrup, bar mix and paper goods in about equal counts; one online marketplace was coded to 9 different
accounts; about 1 invoice in 9 was split across two or more codes.

Each of the 36 profiles has a default code (or none), when to ask (`no_match`, `per_line`, `once`, `mixed_receipt`),
and ordered line rules (pattern -> code). Examples:

| profile | default | line rules (first match wins) |
|---|---|---|
| Wine & spirits distributor | none, code every line | deposit -> 1200, wine -> 5100-03, liquor -> 5100-01, beer -> 5100-02, mixers -> 5200-10, N/A -> 5420-10 ... |
| Beer distributor | 5100-02 | deposit, N/A, mixers, liquor, wine, fuel surcharge |
| Broadline foodservice | 5300 (bar-only: bar mix) | fountain -> 5420-20, N/A, coffee, paper -> 6210, chemicals -> 6240-17 ... |
| Marketplace / big box | none, ask per line | bar tools, glassware, chemicals, smallwares, paper, office, decor, promo items, speakers -> 6315, grounds ... |
| Linen service | 6230-05 | uniforms -> 6230-10 |
| CO2 supplier | 6335-15 | deposit, tank lease -> 6335-10, propane -> 6345-15, bag-in-box -> 5420-20 |
| POS & software | 6415-10 | processing -> 6430, hardware -> 6350-05, marketing -> 6520, music -> 6315 |

General rules (in `phg.gl_templates.general_rules`): code by line, not by invoice; credits go to the item's code as
negatives; deposits to 1200; freight and fuel to 6270 unless the business folds them into cost; tax follows its
lines; items above the capitalization threshold to 1500; in a bar with no kitchen, produce and grocery default to
bar mix; payment method never decides the code; check the brand lexicon before asking (bottle size alone never
decides liquor vs wine); when unsure, ask and save the answer as a rule.

Backtest on the example's 469 invoices (vendors mapped to profiles by hand): the profile can produce the coded
account for **98% of coded lines and 99% of dollars** (coding to a parent such as 6500 counts). That measures
coverage, not accuracy of the pick: the example has no line descriptions.

Pattern syntax: case-insensitive, JavaScript regex (the edge functions apply them). If a rule is ever applied in SQL,
`\b` must become `\y` (PostgreSQL word boundary); tested locally.

## Setup walkthrough (what Harmony does with it)

1. "Do you have a chart of accounts from your bookkeeper?" If yes, import it (source `imported`) and map each code to
   the nearest template account (by name and number) so the metrics still know what is liquor, labor, etc.
   If no, copy the template into the business's own rows (source `template`).
2. Trim by talking: "Do you split beer and wine?" "Is there a kitchen?" (drops 5300 or keeps it), "Do you pay rent or
   own?" Renames are kept ("we call it Bar Consumables").
3. Vendors as they appear: "Who's Eagle Rock? A wine and spirits distributor?" This sets `parties.coding_profile`
   and `gl_default_code`, and copies the profile's line rules into `phg.invoice_coding_rules` for that vendor
   (source `inferred`), confirmed the first time each one fires.
4. Every answer becomes a rule ("Amazon speakers go to music and entertainment"), so the questions stop.

## Status

- Draft 04a is written and tested locally (PG16): applied twice (idempotent), rollback clean, anon cannot read,
  the reader can, 135 accounts with no orphan parents, 36 profiles / 115 rules all pointing at real codes.
- Not applied: it needs draft 04 (and 02 for the parties column), which need Rob's explicit approval.
