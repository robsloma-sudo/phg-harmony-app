# Harmony data catalog (build 18.49.28)

Harmony can put any of these on screen in the Harmony view. Ask in your own words; the examples are starting points.
Server: `supabase/functions/phg-harmony-data` (fixed catalog of read-only queries, the model only picks one + parameters; no model-written SQL).
App: `<script id="phgDataCanvasV1">` in index.html (containers) and the Harmony view router.

## Containers

| Container | What it is for | Try saying |
|---|---|---|
| Map | Pins on a live dark map. One place: opens on the country, then flies in and pulses the pin; a profile card rides along. | "Where is NOM 1610?", "Map every tequila distillery in Arandas", "Show cocktail bars in Denver on a map" |
| Menu viewer | A venue's real captured menu, full screen, pinch zoom. | "Show me Eatery A's menu in Des Moines" |
| Stat cards | Headline numbers. | "Census for ZIP 50309", "How much data do we have?" |
| Ranking bars | Ranked list with detail under each bar. | "Top brands on menus", "Top cocktails in Iowa" |
| Share donut | Parts of a whole plus a detail table. | "Which spirit categories are on the most menus?" |
| Price dashboard | Average / median / range tiles, bars by city or venue type, real examples. | "Average margarita price in Denver", "Espresso martini prices by venue type" |
| Profile card | Everything we know about one venue or producer. | "Drinks profile for Clyde Common", "Where is Casamigos made?" |
| Recipe card | Classic spec, glass, garnish, and what it sells for on menus. | "How do you make a Paloma?" |
| Table | Scrollable records. | "Label approvals for Casamigos" |

## Data sources (server catalog)

| Source | Data | Container |
|---|---|---|
| distillery | organizations (NOM register) + brands.primary_nom | map + profile card |
| distilleries | all NOM producers, filter by town/state | map + by-town bars |
| venues | mv_dash_pins (IA, CO, NY) | map |
| drink_prices | mv_drink_explorer | dashboard |
| category_share | v_menu_category_share (unknown/unclassified excluded) | donut + table |
| top_brands | v_menu_brand_presence | bars |
| cocktail_recipe | cocktail_reference + mv_drink_explorer prices | recipe card |
| zip_demographics | phg_census_zcta (ACS) | tiles |
| coverage | v_public_stats | dashboard |
| venue_profile | mv_menu_dev_venue_profile + v_venue_cocktail_profile | profile + donut |
| label_approvals | cola_label_approvals (TTB COLA) | table |
| menu_breakdown | mv_dash_breakdown | bars |
| menu_lookup | handed back to the app's menu library lookup | menu viewer |

## Notes and limits
- Distillery pins are the **municipality centre of the CRT registered address**, which may be an office rather than the distillery; the card says so. 200 of 201 addresses place (one has no parsable town). Exact plant coordinates would need a data load into production_sites.latitude/longitude.
- Venue data covers Iowa, Colorado and New York.
- Business finance questions (sales, labor, P&L, budgets...) still go to the existing report router, not this catalog.
- Adding a source = one entry in SOURCES (about + run) in the function; the planner picks it up automatically.
