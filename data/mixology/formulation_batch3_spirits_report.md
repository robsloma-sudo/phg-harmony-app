# Formulation batch 3: base spirits. Run report (2026-09-30)

## Outcome: BLOCKED, 0 records written

`data/mixology/formulation_batch3_spirits.jsonl` was **not created**. I did not open a single primary page in this
session, so no value (ABV, sugar, bound, TA, density) meets the rule "never record a value you did not see on the
page itself". An empty or placeholder file would look like finished work, so there isn't one.

## Why

- All outbound fetches from this session are denied by the organization's network egress policy
  (`EGRESS_BLOCKED` from WebFetch; `CONNECT tunnel failed, response 403` from curl). Per the proxy README,
  a policy denial is reported, not retried or routed around.
- Firecrawl tools are not exposed in this session (ToolSearch returned no firecrawl_* tools). **Firecrawl credits
  used: 0.**
- WebSearch works, but it only returns result titles and URLs plus a model summary. Search summaries are not
  evidence under the task rules, so nothing was taken from them. For example, a search returned the rum
  "20 g/L as invert sugar" limit. I did **not** record it because I couldn't open the page.
- I did not use web.archive.org or other mirrors to reach blocked hosts. That would be routing around the policy.
- robots.txt checks were not possible for the same reason, because the robots.txt fetch itself was blocked.

## Fetch tally

| # | host | purpose | result |
|---|---|---|---|
| 1-8 | eur-lex.europa.eu, legislation.gov.uk, ecfr.gov, planalto.gov.br, dof.gob.mx, legifrance.gouv.fr, irishstatutebook.ie, bcn.cl | robots.txt (curl) | 403 proxy CONNECT denied |
| 9-11 | eur-lex.europa.eu, legislation.gov.uk, ecfr.gov | robots.txt (WebFetch) | EGRESS_BLOCKED |
| 12 | planalto.gov.br | robots.txt | EGRESS_BLOCKED |
| 13-16 | bacardi.com, govinfo.gov, law.cornell.edu, delmaguey.com | robots.txt | EGRESS_BLOCKED |
| 17-20 | wipo.int, rumwonk.com, oldstcroix.com, en.wikipedia.org | robots.txt | EGRESS_BLOCKED |
| 21 | raw.githubusercontent.com | reachability probe | reachable (404), not a source |
| 22-25 | ttb.gov, crt.org.mx, scotch-whisky.org.uk, buffalotracedistillery.com | robots.txt | EGRESS_BLOCKED |
| - | WebSearch x1 | discovery | results returned, none usable as evidence |

Fetch attempts: 25 (8 curl, 17 WebFetch). Usable primary results: 0. Firecrawl credits: 0/60.

## What already exists (not duplicated here)

`supabase/migrations/20260930180000_phg_mix_formulation_profiles_batch1.sql` already has sourced generic profiles for:
bourbon (27 CFR 5.143), straight rye, rye (working model), London gin (EU 2019/787 Annex I(22)), gin (working model),
and tequila regulation via NOM-006 (`src_nom_006_tequila`). A re-run should not repeat those.
`data/product_knowledge/tequila_batch1.jsonl` and `agave_batch2.jsonl` may already hold tequila brand ABVs from an
earlier agent. They are worth checking before re-fetching. I did not copy values from them because I did not see
those pages myself.

## Recipe wording that the batch should cover (from data/mixology/*.jsonl, for aliases)

- Rum: white rum; light white rum; light gold rum (1-3 year molasses column); rum; light/gold/aged Puerto Rican rum;
  dark Jamaican rum; gold or dark Jamaican rum; aged Jamaican rum (orig. 17-year J. Wray & Nephew); overproof rum
  (e.g. Wray & Nephew or Lemon Hart 151); 151-proof Demerara rum (Hamilton or Lemon Hart); Demerara rum;
  aged Guyanese rum (El Dorado 8); aged rum (Santa Teresa 1796); aged white rum (Denizen Aged White);
  white rum (Bacardí Superior); Bacardi Superior white rum; white Cuban-style rum; navy rum (Pusser's);
  dark rum (Gosling's Black Seal...); Captain Morgan Original Spiced Rum; unaged rum (Copalli);
  Caribbean blended rum aged 3-5 / 6-10 years; full-bodied rum; unaged or lightly aged rum.
- Mezcal: mezcal; mezcal (Del Maguey Vida Clásico); Del Maguey Chichicapa; Del Maguey San Luis del Rio or Chichicapa.
- Brandy: brandy; cognac; Cognac (Hennessy VS); cognac (H by Hine); cognac (brandy); pisco.
- Whisk(e)y: blended Scotch; Scotch whisky; Irish whiskey; Jameson Irish Whiskey; Jameson Black Barrel;
  bourbon (Buffalo Trace / Elijah Craig / Colonel E.H. Taylor Small Batch / Jim Beam Black / Four Roses);
  Maker's Mark bourbon; Jefferson's Reserve bourbon; cask-strength bourbon (Booker's); bourbon (45% abv);
  straight rye whiskey (50% abv).
- Other: cachaça; oude genever; genever (Bols); Old Tom gin; absinthe; vodka; vodka (Ketel One / Belvedere /
  Suntory Haku / Wodka); vanilla vodka; citrus vodka (Absolut Citron / Ketel One Citroen); apricot-infused vodka.
- Tequila: Patrón Silver, Patrón Reposado, El Tesoro Blanco/Reposado, Espolón Reposado, Cascahuín Blanco,
  Tapatío Blanco, Milagro, Ocho Plata.

Note: Four Roses, Ketel One, Ketel One Citroen, Absolut Citron, Copalli and Wodka appear in recipes but were not
in the task's scope list. Add them to the re-run.

## Leads for a re-run (UNVERIFIED: URLs from search results only, not opened)

- EU 2019/787 Annex I: https://www.legislation.gov.uk/eur/2019/787/annex/I/adopted and
  https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32019R0787 (cat. 1 rum, 4 wine spirit, 5 brandy,
  15 vodka, 22-23 gin, 31 flavoured vodka; definitions of sweetening and caramel in Annex I intro).
- Scotch Whisky Regulations 2009: legislation.gov.uk/uksi/2009/2890 (reg. 3).
- US: eCFR 27 CFR 5.143 (whisky), 5.145 (brandy), 5.146 (rum), 5.23 (2.5% harmless coloring/flavoring/blending
  materials), 5.88 (bottled in bond).
- Mezcal: NOM-070-SCFI-2016 on dof.gob.mx. Cachaça: Decreto 6.871/2009 (planalto.gov.br).
  Cognac: cahier des charges AOC Cognac (legifrance / INAO). Irish whiskey: Irish Whiskey Act 1980 and the
  EU technical file. Pisco: Chile Decreto 521 (bcn.cl). Peru NTP 211.001 is not openly published.

## Needed to complete

Either an egress allowlist for the regulatory hosts above plus producer domains, or a session with Firecrawl
exposed (budget unchanged at 60 credits). Many producer sites have age gates. The re-run should record ABV only
where the page serves it without interacting with the gate, and otherwise use state liquor-control listings as
'secondary', ABV only.
