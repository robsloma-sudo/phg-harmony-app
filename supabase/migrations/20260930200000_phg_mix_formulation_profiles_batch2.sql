-- PHG formulation profiles, batch 2 (2026-09-30). Same rules as batch 1 (source + basis + confidence + verification;
-- unknown stays NULL; "resolve" in notes = mapped_needs_composition).
-- Source notes: Alko (Finland) blocks AI agents in robots.txt (anthropic-ai, ClaudeBot) -> not used, not even via search
-- snippets. Systembolaget blocks automated access -> not used. Fever-Tree nutrition sits behind an age gate -> not used.
-- Most liqueur/vermouth sugar is therefore still unpublished-to-us; those profiles carry official ABV and stay "resolve".

insert into phg_mix.sources (key, title, kind, source_kind, tier, publisher, year, url, access, focus) values
 ('src_luxardo_official', 'Luxardo Maraschino Originale - technical sheet', 'brand', 'brand', 1, 'Girolamo Luxardo S.p.A.', 2019,
  'https://www.luxardo.it/wp-content/uploads/2019/06/Scheda-Maraschino.pdf', 'open', '{ABV,liqueur}'),
 ('src_kahlua_official', 'Kahlúa Original - product page and Pernod Ricard e-label L00032', 'brand', 'brand', 1, 'Pernod Ricard', 2026,
  'https://www.kahlua.com/en-us/products/original-coffee-liqueur/', 'open', '{ABV,liqueur}')
on conflict (key) do nothing;

insert into phg_mix.ingredient_profiles
 (key, name, ingredient_class, brand, generic_name, basis, density_g_ml, abv_pct, brix_deg, brix_min, brix_max, brix_type,
  sugar_g_100ml, sugar_g_100g, ta_g_100ml, ta_min_g_100ml, ta_max_g_100ml, sugar_profile, acid_profile, variability,
  measurement_basis, confidence, verification, notes) values
 ('ip_agave_syrup_undiluted', 'Agave Syrup / Nectar - Undiluted (USDA)', 'sweetener', null, 'agave syrup', 'literature_range',
  1.40, 0, null, null, null, 'not_applicable', 95.2, 68.0, null, null, null,
  '{"total_g_100g":68.0,"fructose_g_100g":55.6,"glucose_g_100g":12.4,"sucrose_g_100g":0,"water_g_100g":22.9,"source":"USDA FDC 170277"}', '{}',
  '{"density_note":"USDA portions conflict: 1 tsp = 6.9 g (1.40 g/mL, used) vs 1/4 cup = 55 g (0.93 g/mL, rejected: below water)"}',
  'USDA FDC 170277 Sweetener, syrup, agave: 68.0 g sugars/100 g (fructose-dominant). Density 1.40 g/mL from the 1 tsp portion; sugar 95.2 g/100 mL derived.',
  'medium', 'official', 'Fructose-dominant: sweetness per gram differs from sucrose (see fc_sugar_identity_matters). Titratable acidity not published.'),
 ('ip_agave_syrup_dilution_unspecified', 'Agave Syrup - Dilution Unspecified', 'sweetener', null, 'agave syrup', 'generic',
  null, 0, null, null, null, 'not_applicable', null, null, null, null, null,
  '{"resolution_required":"undiluted nectar or cut with water (1:1, 2:1)?"}', '{}', '{}',
  'Generic recipe term.', 'low', 'derived',
  'Resolve whether "agave syrup" means undiluted nectar or a house dilution before calculating sugar.'),
 ('ip_luxardo_maraschino', 'Luxardo Maraschino Originale', 'liqueur', 'Luxardo', 'maraschino liqueur', 'specific_product',
  null, 32, null, null, null, 'not_applicable', null, null, null, null, null,
  '{"sweetened_with":"simple syrup of water and sugar (producer)"}', '{}', '{}',
  'ABV 32% per producer technical sheet; sugar content not stated there.', 'high', 'official',
  'Resolve sugar: the producer sheet does not state it.'),
 ('ip_maraschino_liqueur_unspecified', 'Maraschino Liqueur - Product Unspecified', 'liqueur', null, 'maraschino liqueur', 'generic',
  null, null, null, null, null, 'not_applicable', null, null, null, null, null, '{}', '{}', '{}',
  'Generic category only.', 'low', 'derived', 'Resolve the product (sugar and ABV vary by brand).'),
 ('ip_kahlua_original', 'Kahlúa Original Coffee Liqueur (US)', 'liqueur', 'Kahlúa', 'coffee liqueur', 'specific_product',
  null, 20, null, null, null, 'not_applicable', null, null, null, null, null, '{}', '{}', '{"note":"ABV differs by market"}',
  'ABV 20% per US product page and Pernod Ricard e-label L00032.', 'high', 'official',
  'Resolve sugar: nutrition is on the e-label but was not machine-readable.'),
 ('ip_coffee_liqueur_unspecified', 'Coffee Liqueur - Product Unspecified', 'liqueur', null, 'coffee liqueur', 'generic',
  null, null, null, null, null, 'not_applicable', null, null, null, null, null, '{}', '{}', '{}',
  'Generic category only.', 'low', 'derived', 'Resolve the product (sugar and ABV vary widely: sweet vs dry cold-brew styles).'),
 ('ip_sweet_vermouth_unspecified', 'Sweet (Rosso) Vermouth - Product Unspecified', 'other', null, 'sweet vermouth', 'generic',
  null, null, null, null, null, 'not_applicable', null, null, null, null, null, '{}', '{"note":"wine-based: carries wine acidity"}', '{}',
  'Generic category only (aromatised wine).', 'low', 'derived', 'Resolve the product: sugar, acidity and ABV vary by brand.'),
 ('ip_dry_vermouth_unspecified', 'Dry Vermouth - Product Unspecified', 'other', null, 'dry vermouth', 'generic',
  null, null, null, null, null, 'not_applicable', null, null, null, null, null, '{}', '{"note":"wine-based: carries wine acidity"}', '{}',
  'Generic category only (aromatised wine).', 'low', 'derived', 'Resolve the product: sugar, acidity and ABV vary by brand.')
on conflict (key) do nothing;

insert into phg_mix.formulation_evidence (record_type, record_key, source_key, url, locator, evidence_role, note) values
 ('ingredient_profile','ip_agave_syrup_undiluted','src_usda_fdc_sr_legacy','https://fdc.nal.usda.gov/food-details/170277/nutrients','FDC 170277','primary','68.0 g sugars/100 g; 1 tsp = 6.9 g'),
 ('ingredient_profile','ip_luxardo_maraschino','src_luxardo_official',null,'technical sheet: Alcohol strength','primary','32% ABV'),
 ('ingredient_profile','ip_kahlua_original','src_kahlua_official','https://e-label.pernod-ricard.com/L00032','product page + e-label header','primary','20% ABV')
on conflict do nothing;

insert into phg_mix.ingredient_profile_aliases (alias, profile_key, alias_type) values
 ('agave nectar','ip_agave_syrup_undiluted','normalized_term'),
 ('light agave nectar','ip_agave_syrup_undiluted','recipe_term'),
 ('agave syrup','ip_agave_syrup_dilution_unspecified','normalized_term'),
 ('light agave syrup','ip_agave_syrup_dilution_unspecified','recipe_term'),
 ('luxardo maraschino','ip_luxardo_maraschino','brand'),
 ('luxardo maraschino liqueur','ip_luxardo_maraschino','brand'),
 ('maraschino liqueur','ip_maraschino_liqueur_unspecified','normalized_term'),
 ('maraschino','ip_maraschino_liqueur_unspecified','recipe_term'),
 ('kahlúa','ip_kahlua_original','brand'),
 ('kahlua','ip_kahlua_original','brand'),
 ('coffee liqueur','ip_coffee_liqueur_unspecified','normalized_term'),
 ('coffee liqueur (sweet style)','ip_coffee_liqueur_unspecified','recipe_term'),
 ('sweet vermouth','ip_sweet_vermouth_unspecified','normalized_term'),
 ('sweet vermouth (blend)','ip_sweet_vermouth_unspecified','recipe_term'),
 ('dry vermouth','ip_dry_vermouth_unspecified','normalized_term'),
 ('french (dry) vermouth','ip_dry_vermouth_unspecified','recipe_term')
on conflict do nothing;
