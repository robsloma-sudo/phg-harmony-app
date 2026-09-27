-- PHG-036c: the Menu Designer reads everything menu-related, and can change nothing (Rob, 2026-09-28: "I want them
-- to have access to real ingredients in Supabase ... full access to anything menu related").
-- * role phg_menu_designer (NOLOGIN): SELECT on an explicit allowlist of menu, ingredient, recipe, cocktail, brand /
--   product, library, census and venue tables and views. No INSERT / UPDATE / DELETE anywhere; no secrets, no auth or
--   user tables; the Menu Studio project token hash is not readable.
-- * phg_designer_query(sql, max_rows): runs ONE query as that role inside a read-only transaction, statement timeout
--   20 s, returns jsonb rows, and logs every call (phg.menu_designer_query_log). The query is wrapped as a subquery,
--   so it can only be a single SELECT / WITH ... SELECT.

do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'phg_menu_designer') then
    create role phg_menu_designer nologin;
  end if;
end $$;
grant usage on schema public, phg to phg_menu_designer;

do $$
declare t text;
begin
  foreach t in array array[
    -- the app's menus, recipes, ingredients, costs, sales mapping
    'phg.menu_items','phg.menu_item_prices','phg.menu_item_evaluations','phg.menu_engineering_snapshots',
    'phg.menu_design_tasks','phg.menu_design_proposals','phg.menu_publication_versions','phg.public_menu_experiences',
    'phg.ingredients','phg.ingredient_products','phg.prep_recipes','phg.prep_recipe_versions','phg.prep_components',
    'phg.recipe_projects','phg.recipe_versions','phg.recipe_components','phg.recipe_cost_snapshots','phg.recipe_evaluations',
    'phg.purchase_costs','phg.procurement_catalog_items','phg.sales_items','phg.sales_item_menu_map',
    -- captured menus (library) and their text, images, classification
    'public.menus','public.menu_sections','public.menu_items','public.menu_item_brands','public.menu_item_tags',
    'public.menu_item_cocktail_core','public.menu_headers','public.menu_header_tags','public.staging_menu_extract',
    'public.menu_visual_documents','public.menu_visual_pages','public.phg_page_text','public.phg_menu_doc_class',
    'public.menu_source_candidates','public.menu_extraction_sources','public.classified_item_cache',
    -- cocktails, spirits, brands, products
    'public.cocktail_reference','public.cocktail_specs','public.cocktail_spec_components','public.cocktail_spec_sources',
    'public.cocktail_spec_terms','public.cocktail_tag_dimensions','public.cocktail_tag_terms','public.cocktail_tag_values',
    'public.spirit_lexicon','public.brands','public.brand_lines','public.brand_products','public.brand_category_links',
    'public.brand_producer_links','public.products','public.product_category_links','public.product_attribute_links',
    'public.product_measure_values','public.product_packages','public.product_releases','public.production_methods',
    'public.production_sites','public.beverage_categories','public.beverage_attribute_dimensions',
    'public.beverage_attribute_values','public.beverage_measures','public.legal_designations','public.venue_concepts',
    -- venues and demographics
    'public.accounts','public.phg_census_zcta',
    -- ready-made views
    'public.v_menu_composition','public.v_menu_category_share','public.v_menu_brand_presence','public.v_menu_header_catalog',
    'public.v_cocktail_items_filterable','public.v_cocktail_build_combinations','public.v_cocktail_site_context',
    'public.v_venue_cocktail_profile','public.v_public_drinks','public.v_public_drinks_classified','public.v_public_venues',
    'public.v_public_drink_explorer','public.v_public_drink_avg','public.mv_drink_explorer','public.mv_menu_dev_venue_profile',
    'public.mv_venue_cocktail_similarity']
  loop
    if to_regclass(t) is not null then execute format('grant select on %s to phg_menu_designer', t); end if;
  end loop;
end $$;

-- Menu Studio drafts: every column except the project token hash.
grant select (id, conversation_id, name, season, launch_date, status, brief, constraints, created_at, updated_at,
              editor_state, backend_revision, editor_source, target_cogs_pct, account_id)
  on phg.menu_projects to phg_menu_designer;

create table if not exists phg.menu_designer_query_log (
  id bigserial primary key, at timestamptz not null default now(), task_id uuid, sql text not null,
  rows int, ms int, error text);
alter table phg.menu_designer_query_log enable row level security;
revoke all on phg.menu_designer_query_log from anon, authenticated, phg_menu_designer;

-- Not SECURITY DEFINER on purpose: it is called by the Coordinator's database connection and switches DOWN to
-- phg_menu_designer for the query itself (SET ROLE is not allowed inside SECURITY DEFINER functions).
create or replace function public.phg_designer_query(p_sql text, p_max_rows int default 500, p_task_id uuid default null)
returns jsonb language plpgsql set search_path to 'public', 'phg', 'pg_temp' as $$
declare v_rows jsonb; v_n int; v_t0 timestamptz := clock_timestamp(); v_log bigint;
begin
  if p_sql is null or btrim(p_sql) = '' then raise exception 'sql required'; end if;
  if p_sql ~ ';\s*\S' then raise exception 'one statement only'; end if;
  insert into phg.menu_designer_query_log (task_id, sql) values (p_task_id, left(p_sql, 20000)) returning id into v_log;
  set local statement_timeout = '20s';
  set local transaction_read_only = on;
  set local role phg_menu_designer;
  begin
    execute format('select coalesce(jsonb_agg(q), ''[]''::jsonb) from (select * from (%s) s limit %s) q',
                   regexp_replace(p_sql, ';\s*$', ''), least(greatest(coalesce(p_max_rows, 500), 1), 5000))
      into v_rows;
  exception when others then
    reset role;
    raise exception 'designer query failed: %', sqlerrm;
  end;
  reset role;
  v_n := jsonb_array_length(v_rows);
  -- the transaction is read-only now; the row count is recorded by the caller's next log write (see note)
  return jsonb_build_object('rows', v_rows, 'row_count', v_n, 'log_id', v_log,
                            'ms', (extract(epoch from clock_timestamp() - v_t0) * 1000)::int);
end $$;
revoke all on function public.phg_designer_query(text, int, uuid) from public, anon, authenticated;
