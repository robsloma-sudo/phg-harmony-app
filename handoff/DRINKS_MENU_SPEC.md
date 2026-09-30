# What makes a drinks menu: PHG filter spec (v3, 2026-09-28)

For Rob to review. This is exactly what the classifier looks for. Test suite: `supabase/tests/phg_drinks_menu_cases.sql`
(`select * from phg_drinks_menu_cases_run();`, which currently passes 17 of 17; v3 rules, 2026-09-28).

## 1. Menu types (one per page)

| Type | Rule |
|---|---|
| Drinks menu | Drink items (all drinks categories + non-alcoholic) at least equal to food items |
| Drinks + food | 3+ drink items and 3+ food items, and food is more than a third of the drinks |
| Food menu | Food items outnumber drinks |
| Happy hour page | 60%+ of items are under a happy-hour heading (or a happy-hour link with happy-hour items) |
| Specials / events page | 60%+ of items are under specials / weekday / event headings |
| Little menu text | Fewer than 5 items; usually a page that links to the menu |
| Not read yet | No readable items (image-only menus, homepages, photo galleries, bot checks). This means unknown, never "not a drinks menu". |
| Delivery app listing | DoorDash, Uber Eats, Grubhub, Postmates, Seamless, Slice, ChowNow, Menufy |

A drinks menu with a happy-hour or specials section stays a drinks menu and is tagged with that section.

## 2. Drinks categories (all equal; each is its own filter)

Beer · Brandy & cognac · Cider & seltzer · Cocktails · Gin · Liqueurs & amari · Mezcal · Non-alcoholic · Rum ·
Sake & soju · Tequila · Vodka · Whiskey · Wine. There's also "Spirits (type not stated)" for spirit lines the menu
doesn't name, such as "House pour".

A category is found in two ways:
1. **Its heading:** "DRAFT & CANS", "Cervezas", "Reds", "Bubbles", "Mocktails", "After dinner", "AGAVE", and so on.
2. **The item itself, under a generic "Spirits / Liquor / After dinner" heading:** by name or brand. For example,
   Tito's → vodka, Hendrick's → gin, Diplomático → rum, Casamigos → tequila, Del Maguey → mezcal,
   Macallan / Buffalo Trace → whiskey, Hennessy → cognac, Aperol / Fernet → liqueurs & amari.

A spirit named inside a cocktail's ingredients ("vodka, strawberry cordial") is **not** a spirits list.

The drink's own name decides before the heading does: Don Julio under "Tequila & Mezcal" is tequila, Malibu under "Rum &
Cognac" is rum, Coors Light under "Liquor & Beer" is beer, and "Gin & Tonic" or "Vodka Mule" inside a spirits list is a
cocktail. Food and page text mislabeled as drinks ("Reuben on Marble Rye", "Penne alla Vodka", "cognac sauce w/ shrimp",
hotel check-in text) are ignored.

## 3. How a page is read

- A **heading** is a short line (up to 40 characters, 5 words), capitalised, with no comma or number.
- An **item** is a line with a price ($12, 12.00, 9/36), or on unpriced menus a listed line under a heading (a name
  line plus a description line counts as one item). Unpriced lines only count when the page lists 8 or more.
- A page's text includes every tab (Beer / Wine / Cocktails / Spirits) and embedded lists (Untappd beer menus).

## 4. What is never a drinks menu

Food menus · homepages and navigation · cookie / CAPTCHA / "checking your connection" screens · photo galleries of
drinks · delivery-app listings · pages that only link to a menu.

## 5. Known gaps (R&D, no scraping or spending)

- **12,477 documents have no text yet** (mostly images and PDFs). They stay "Not read yet" until read, which means
  either re-capture with text (HTML pages) or reading the image (vision; costs money, needs your approval).
- Brand lists cover the most common brands, grown from the library's most frequent unsorted names (8.7% of spirit
  lines are still "type not stated"); unknown brands under a generic "Spirits" heading fall into
  "Spirits (type not stated)". The list grows as we find misses.
- Wine is one category. Say if you want Red / White / Rosé / Sparkling as separate equal filters.
- Cocktails are one category. Say if you want them split by base spirit (tequila cocktails, gin cocktails ...).

## 6. How to review

Open the Menu Library preview, pick one category in **Has** (for example Mezcal), and send me the card numbers that are wrong.
Each miss becomes a new test case before any rule changes.
