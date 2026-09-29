# Product knowledge data contract (PHG-046)

Rob 2026-09-29: click a distillery or brand on the map and get all the product knowledge: the Blancos, Reposados,
Añejos, Extra Añejos, how they are made, origin and history. This contract is what research agents write and what
the loader reads. Files: `data/product_knowledge/<batch>.jsonl`, one JSON object per line.

## Rules
- **Facts, not prose.** Short facts in your own words. Never copy sentences from brand sites or articles.
- **Every fact has a source** (`sources: [{url, title, kind, tier}]`). No source, no fact. Unknown = null.
- **Never guess numbers** (proof, aging months, price). Take them only from what a source actually shows.
- `verification`: `page` (read on the page), `excerpt` (from search-result excerpts only), `unverified`.
- Source tiers: 1 = official regulator/registry (CRT, TTB COLA, NOM register); 2 = the brand or producer itself;
  3 = established trade/reference (Tequila Matchmaker, Difford's, PUNCH, Imbibe, Wine Enthusiast, Distiller);
  4 = named expert reviewers / creators; 5 = retailers, marketing copy, forums.
- "Additive-free" only when a named program says so (e.g. Tequila Matchmaker's Additive-Free Alliance / confirmed
  list), with that source; otherwise null.

## Record types

### brand
```json
{"type":"brand","key":"brand_fortaleza","name":"Fortaleza","aka":["Los Abuelos"],"category":"tequila",
 "nom":"1493","producer":"Destilería La Fortaleza","owner":"Sauza family (Guillermo Erickson Sauza)",
 "region":"Tequila valley (lowlands), Jalisco","founded_year":2005,
 "history":["family descends from Don Cenobio Sauza","sold as Los Abuelos in Mexico"],
 "sources":[{"url":"...","title":"...","kind":"brand_site","tier":2}],"verification":"excerpt"}
```

### expression (one bottling)
```json
{"type":"expression","key":"exp_fortaleza_blanco","brand_key":"brand_fortaleza","name":"Fortaleza Blanco",
 "style":"blanco","abv":40.0,"aging_months_min":null,"aging_months_max":null,"barrels":null,
 "agave":"Blue Weber, estate-grown","agave_region":"lowlands","cooking":"stone/brick oven (horno)",
 "milling":"tahona","fermentation":"wooden vats, open-air, natural yeast","distillation":"double, copper pot",
 "water":null,"additive_free":null,"tasting":["cooked agave","citrus","olive brine","black pepper"],
 "price_usd_750":null,"awards":[],
 "sources":[...],"verification":"excerpt"}
```
`style` one of: blanco, joven, reposado, anejo, extra_anejo, cristalino, other. For mezcal add `agave_species`,
`maestro`, `village`, `cooking` (earthen pit), `category` (mezcal, mezcal artesanal, ancestral).

## Report
Counts per type, sources by tier, and what could not be found.
