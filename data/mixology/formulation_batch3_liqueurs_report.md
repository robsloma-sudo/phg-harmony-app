# Formulation batch 3: liqueurs, aperitifs, vermouths - research report (2026-09-30)

## Outcome
**0 verified records written.** `data/mixology/formulation_batch3_liqueurs.jsonl` is empty on purpose.

Why: this session's network egress policy blocked every page fetch. No producer page, e-label, tech sheet or
regulation text could be opened, so no value was seen on a primary page. The hard rule says search
summaries are not evidence, so nothing was recorded. robots.txt could not be read either, because those
requests were blocked too.

## Fetch tally
| channel | attempts | usable | result |
|---|---|---|---|
| curl (robots.txt checks) | 24 hosts | 0 | proxy `CONNECT 403` (organization egress policy) on every host: e-label.pernod-ricard.com, campari.com, campariusa.com, aperol.com, cointreau.com, grandmarnier.com, chartreuse.fr, benedictinedom.com, eur-lex.europa.eu, stgermain.fr, chambord.com, disaronno.com, licor43.com, giffard.com, fernetbranca.com, dolin.fr, noillyprat.com, lillet.com, cocchi.it, martini.com, cinzano.com, u-label.com |
| WebFetch | 9 | 0 | `EGRESS_BLOCKED`: e-label.pernod-ricard.com, eur-lex.europa.eu, cointreau.com, giffard.com, lillet.com, en.wikipedia.org (control test), bacardilimited.com, legislation.gov.uk, alpenz.com |
| WebSearch | 16 | 0 values (leads only) | works, but its summaries are not admissible as evidence |
| Firecrawl | 0 | - | Firecrawl tools were not available in this session. **Credits used: 0 / 80** |

Per the proxy README, policy denials were not retried or routed around.
Not used at all: alko.fi, systembolaget.se, OpenFoodFacts and calorie sites.

## Primary-source leads for a re-run with egress to these hosts
The "search snippet claimed" column is **unverified**, recorded only so the re-run knows what to check. Do not load any of it.

| item | primary lead URL | search snippet claimed (UNVERIFIED) | note |
|---|---|---|---|
| EU Reg. 251/2014 (vermouth definition, sweetness terms) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A02014R0251-20211207 ; mirror https://legislation.gov.uk/eur/2014/251/article/6?view=plain | Art. 6: extra-dry <30 g/L, dry <50, semi-dry 50-<90, semi-sweet 90-<130, sweet >=130 g/L, as invert sugar | Quote Art. 6 and Annex II (vermouth definition, 14.5-22% ABV) from the consolidated text |
| Martini Rosso / Extra Dry | https://www.bacardilimited.com/nutrition/martini/ | Rosso 6.7 g sugars per 1.5 oz; Extra Dry 0.9 g per 1.5 oz | Producer page (US serving basis: 1.5 oz = 44.36 mL). Record the market, and derive per 100 mL only as a labelled derivation |
| St-Germain | https://www.bacardilimited.com/nutrition/st-germain/ | 15.2 g sugars per 1.5 oz | same |
| Bénédictine D.O.M. | https://www.bacardilimited.com/nutrition/benedictine/ | 14.6 g sugars per 1.5 oz | same |
| Green Chartreuse (and VEP) | https://www.chartreuse.fr/qr/verte-011-fr/ ; https://www.chartreuse.fr/qr/vep_verte-001-fr/ | 24 g/100 mL (Verte 55%); 23 g/100 mL (VEP 54%) | Official QR e-label pages. Yellow is probably at a parallel /qr/jaune-... URL |
| Lillet Blanc | https://e-label.pernod-ricard.com/L00952 ; https://www.lillet.com/en/nutrition-calories/ | 8.8 g/100 mL at 17% | e-label plus brand nutrition page |
| Kahlúa | https://e-label.pernod-ricard.com/L00032 | one snippet: 39.3 g/100 mL at **16%** (EU); US product is 20% | Market mismatch: the EU 16% and US 20% products are different formulations. Don't cross-apply them |
| Cointreau | https://www.cointreau.com/int/en/faq | "6.6 g sugars/100 mL" | **Conflicts** with PHG's loaded official 22.5 g/100 mL. Probably a garbled snippet, but re-check the FAQ and confirm the source of ip_cointreau_unique. No TA found |
| Dolin Dry / Blanc / Rouge | https://alpenz.com/producer-dolin.html (US importer) ; dolin.fr | Dry 30 g/L; Blanc and Rouge 130 g/L | Importer page = producer-adjacent; prefer dolin.fr tech sheets. TA not found |
| Noilly Prat Original Dry | noillyprat.com ; https://e-label.pernod-ricard.com (Noilly is not Pernod: it's Bacardi, so check bacardilimited.com/nutrition/) | 21 g/L, 18% | Source of the snippet unclear. Needs producer confirmation |
| Cocchi Americano | https://www.cocchi.it/en/wines/americano/ | 16.5% only; no sugar or TA found | Check the product sheet PDF on cocchi.it |
| Mr Black | https://www.mrblack.co/en/products/coffee-liqueur | conflicting 18% sugar vs 34 g/100 mL | Brand FAQ; resolve on the page |
| Giffard (all) | giffard.com product sheets | no sugar for Mûre; 380 g/L claimed for Pêche (off-scope) | Giffard usually publishes sugar g/L on its pro sheets. Check each |
| Campari / Aperol | campari.com, aperol.com, Campari Group e-label (EU) | Campari US 24% / EU 25% (retailer-sourced only); sugar only from OpenFoodFacts (not admissible) | Need the Campari Group EU e-label URL (usually on the bottle QR) |
| Disaronno | disaronno.com | only an aggregator figure (not admissible) | - |
| Carpano Antica / Punt e Mes | Fratelli Branca / carpano.com | none | Branca e-labels are likely via the bottle QR |

Not searched this session (budget kept small given no fetch path): Grand Marnier, Pierre Ferrand Dry Curaçao,
DeKuyper, Yellow Chartreuse (see the Chartreuse QR lead), Cherry Heering, Chambord, Luxardo Maraschino sugar,
Tia Maria, Galliano Espresso, Licor 43, Midori, Passoã, Chinola, Fernet-Branca, Nonino, Averna, Cynar, Braulio,
Amer Picon, peach schnapps, falernum, Toschi Nocello, Martini Riserva Ambrato, Cinzano, Strucchi, and wine TA for all vermouths.

## Recommendation
Re-run this batch in a session whose egress allowlist includes at least: eur-lex.europa.eu (or legislation.gov.uk),
www.bacardilimited.com, www.chartreuse.fr, e-label.pernod-ricard.com, www.lillet.com, www.cointreau.com, www.cocchi.it,
www.giffard.com, www.dolin.fr, www.mrblack.co, and campari.com/aperol.com. Bacardi's nutrition pages plus the Chartreuse
and Pernod e-labels alone would cover about 8 profiles with official data.
