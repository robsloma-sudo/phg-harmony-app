/* What Harmony may query through public.phg_harmony_query (the read-only knowledge-map gateway, migration
   20260929020000). Only tables in phg.harmony_table_access with shared_read / project_read are listed; the gateway
   rejects anything else and scopes project tables to the caller's project (RLS), so no account filter is needed. */
export const SCHEMA_DOC = `
POSTGRES, read-only. One SELECT (or WITH ... SELECT). No comments, no semicolons, no schema-qualified function calls.
Always LIMIT (max 200). Use ILIKE '%...%' for names. Round money with round(x::numeric, 2).

MARKET DATA (shared; bars and restaurants PHG tracks in Iowa IA, Colorado CO, New York NY)
public.mv_drink_explorer  -- one row per priced drink on a venue's menu (best table for drinks by venue/city/state)
  state_code, city, venue, venue_key, venue_type, address, rating, lat, lng, income, median_age, income_band, age_band,
  section (cocktails|beer|wine|liquor|non_alcoholic), menu_section (header printed on the menu),
  family (tequila|mezcal|whiskey|vodka|gin|rum|brandy|liqueur|wine|beer|non_alcoholic), subfamily, serve_format,
  item_name (as printed), item_price, drink_name (recognised cocktail identity; often empty outside Iowa), identity_class
  -> a drink is best found with (item_name ILIKE '%margarita%' OR drink_name ILIKE '%margarita%').
public.v_cocktail_items_filterable -- cocktails with their build: item_name, item_price, venue, city, venue_type,
  income_band, age_band, spec_name, build_family, base_spirits (text[]), modifiers (text[]), flavour_cues (text[])
public.mv_menu_dev_venue_profile -- one row per venue: venue, city, state_code, venue_type, cocktail_items,
  cocktail_avg_price, cocktail_median_price, beer_items, wine_items, liquor_items, na_items, income_band, age_band
public.v_public_venues -- all tracked venues: state_code, venue, city, address, venue_type, rating, reviews, website, lat, lng
public.v_menu_brand_presence -- brand_name, venues, menu_items, in_cocktails, as_pour, avg_price, first_seen, last_seen
public.menu_item_brands -- menu_item_id, brand_id, raw_brand_text, spirit_category, expression
public.menus (account_id text = public.accounts.account_id, menu_title, menu_type, is_current)
  -> public.menu_sections (menu_id, section_name, section_type) -> public.menu_items (section_id, item_name, price, raw_text)
public.accounts -- venues: account_id (text), account_name, account_types, street_address, postal_code, geography_id,
  google_rating, website_url
public.geographies -- id, geography_name, geo_type (city|county|state), subdivision_code (e.g. US-IA), population
public.phg_census_zcta -- zcta (ZIP), state, total_population, median_age, median_household_income, pop_21_34_pct,
  households_over_100k_pct, bachelors_or_higher_pct, hispanic_latino_pct

SPIRITS
public.brands -- brand_name, aliases, category (tequila), primary_nom, brand_status, official_website
public.organizations -- producers: organization_name, nom, organization_types
public.production_sites -- distilleries: site_name, registry_code (NOM), latitude, longitude
public.products -- product_name, brand_id, product_class, expression_variant, package_size_ml, abv_percent
public.cola_label_approvals -- US label approvals: ttb_id, completed_date, brand_name_raw, fanciful_name,
  class_type_desc, origin_desc
public.cocktail_reference -- classic specs: cocktail_name, base_spirit, consensus_spec, method, glassware, garnish, profile
public.spirit_lexicon -- term, family, subfamily

THE BUSINESS'S OWN DATA (project; the gateway returns only the caller's project)
phg.menu_projects (id, name, season, status, target_cogs_pct) -> phg.menu_items (menu_project_id, name, section_name,
  menu_price, menu_description, current_recipe_version_id, status)
phg.recipe_projects (id, name, status) -> phg.recipe_versions (project_id, version, recipe_name, cocktail_name, method,
  glassware, garnish, ingredients json, status) -> phg.recipe_components (recipe_version_id, ingredient_id,
  prep_recipe_id, quantity, unit, role)
phg.recipe_cost_snapshots -- menu_item_id, costed_on, recipe_cost, menu_price, theoretical_cogs_pct, contribution_margin
phg.purchase_invoices -- vendor_id, invoice_number, invoice_date, subtotal, tax, total, status, location_key
phg.purchase_costs -- ingredient_id, vendor_key, package_size, package_size_unit, cost, effective_from
phg.operating_expenses -- expense_date, vendor_id, category_id -> phg.expense_categories (name, category_group),
  description, signed_amount
phg.sales_daily -- business_date, revenue_center, gross_sales, discounts, comps, refunds, net_sales, guest_count, check_count
phg.sales_items -- business_date, item_name, category, quantity, net_sales, comps
phg.labor_shifts -- business_date, role_id, regular_hours, overtime_hours; phg.labor_pay_rates (hourly_rate)
phg.budget_plans, phg.reporting_periods (name, period_type, start_date, end_date)
phg.harmony_notes -- kind (note|task|idea|reminder), body, tags, due_at, done
`;
