-- ============================================================================
-- PROPOSED MIGRATION (NOT APPLIED) — ABV on menus + one source for the build
-- Brief: "ABV engine is live" (#phg-ops 2026-10-06 15:14), build items 1, 3, 5. Needs leadership sign-off.
-- Depends on: PROPOSED_cocktail_build_method.sql (phg.recipe_builds) — run that first.
--
-- 1. public.phg_menu_abv(menu_project_id)  the app's only door to ABV. Signed-in users have no USAGE on schema
--    phg, so Menu Studio cannot read phg.v_menu_item_abv directly. Same membership rule as menus: platform admin,
--    or an active member of the menu project's account. Returns ONE row per menu item with `menu_label` ONLY when
--    abv_status is menu_ready / menu_ready_measured; otherwise label is null and blockers / estimate reasons are
--    returned so the app can show why ("Never print an estimate on a menu").
-- 2. public.phg_recipe_abv(recipe_version_id)  same data for one recipe (Cocktail view / cocktail-studio balance
--    block), behind phg_cocktail_can.
-- 3. ONE SOURCE FOR THE BUILD. phg.recipe_builds (the card) now feeds the ABV engine: saving a build writes
--    recipe_versions.serve_method and serve_params.{vessel_key, ice_type_key, agitation_s} from it (and the measured
--    dilution field stays on recipe_versions). The ABV recompute trigger on recipe_versions then fires on its own.
--    Mapping: style shaken→shaken, stirred→stirred, built→built (built_long when service ice is a Collins spear or
--    standard cubes in a highball), blended→blended; vessel shaker_tin→tin_on_tin, mixing_glass→mixing_glass,
--    serving_glass→rocks_glass/highball_glass by glass, blender→blender_jar; mixing ice standard_cubes→kold_draft_1_25in,
--    large_cubes→large_cube_2in, crushed/pebble→crushed_pebble; agitation = mid-point of the technique seconds.
--    Keys the engine already holds in serve_params (environment_key, ambient_c, ice_mass_g, ...) are kept.
-- 4. Build item 5: a statement-level trigger recomputes ABV after edits to preps, prep components, ingredient ABV and
--    the five parameter tables (it calls phg.recompute_all_recipe_abv() once per statement).
--
-- RISK: additive. Two read functions, one sync trigger on phg.recipe_builds, six recompute triggers.
-- ROLLBACK:
--   drop function if exists public.phg_menu_abv(uuid), public.phg_recipe_abv(uuid);
--   drop trigger if exists recipe_builds_sync_abv on phg.recipe_builds; drop function if exists phg.trg_recipe_builds_sync_abv();
--   drop trigger if exists abv_recompute_stmt on phg.prep_components, phg.prep_recipe_versions, phg.ingredients,
--     phg.ice_types, phg.bar_vessels, phg.serve_method_profiles, phg.bar_environment, phg.measure_volume_standards;
--   drop function if exists phg.trg_abv_recompute_all();
-- ============================================================================
begin;

-- 1 ---------------------------------------------------------------------------
create or replace function public.phg_menu_abv(p_menu_project_id uuid)
returns table(menu_item_id uuid, name text, abv_status text, menu_label text, abv_pct numeric, abv_low_pct numeric,
              abv_high_pct numeric, standard_drinks_us numeric, method text, dilution_basis text,
              blockers text[], estimate_reasons text[], computed_at timestamptz)
language plpgsql stable security definer set search_path = '' as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'login required' using errcode = '42501'; end if;
  if not (phg.is_platform_admin(uid) or exists (
            select 1 from phg.menu_projects mp
              join phg.account_memberships m on m.account_id = mp.account_id
             where mp.id = p_menu_project_id and m.user_id = uid and m.status = 'active')) then
    raise exception 'not permitted' using errcode = '42501';
  end if;
  return query
    select v.menu_item_id, v.name, v.abv_status,
           case when v.abv_status in ('menu_ready','menu_ready_measured') then v.menu_label end,
           v.abv_pct, v.abv_low_pct, v.abv_high_pct, v.standard_drinks_us, v.method, v.dilution_basis,
           v.blockers, v.estimate_reasons, v.computed_at
      from phg.v_menu_item_abv v
     where v.menu_project_id = p_menu_project_id;
end $$;

-- 2 ---------------------------------------------------------------------------
create or replace function public.phg_recipe_abv(p_recipe_version_id uuid)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare uid uuid := auth.uid(); a record;
begin
  if not public.phg_cocktail_can(uid, p_recipe_version_id) then raise exception 'not permitted' using errcode = '42501'; end if;
  select * into a from phg.recipe_abv where recipe_version_id = p_recipe_version_id;
  if not found then return jsonb_build_object('abv_status', 'not_computed'); end if;
  return jsonb_build_object(
    'abv_status', a.status,
    'menu_label', case when a.status in ('menu_ready','menu_ready_measured') then a.menu_label end,
    'abv_pct', a.abv_pct, 'abv_low_pct', a.abv_low_pct, 'abv_high_pct', a.abv_high_pct,
    'dilution_pct', a.dilution_pct, 'final_temp_c', a.final_temp_c, 'standard_drinks_us', a.standard_drinks_us,
    'method', a.method, 'dilution_basis', a.dilution_basis,
    'blockers', to_jsonb(a.blockers), 'estimate_reasons', to_jsonb(a.estimate_reasons), 'computed_at', a.computed_at);
end $$;

revoke all on function public.phg_menu_abv(uuid), public.phg_recipe_abv(uuid) from public, anon;
grant execute on function public.phg_menu_abv(uuid), public.phg_recipe_abv(uuid) to authenticated;

-- 3 ---------------------------------------------------------------------------
create or replace function phg.trg_recipe_builds_sync_abv() returns trigger
language plpgsql security definer set search_path = phg, public, pg_temp as $$
declare m text; ves text; ice text; secs numeric; sp jsonb;
begin
  m := case new.style
         when 'shaken' then 'shaken' when 'stirred' then 'stirred' when 'blended' then 'blended'
         when 'built' then case when new.service_ice in ('collins_spear') or lower(coalesce(new.glass_type,'')) ~ '(highball|collins)'
                                then 'built_long' else 'built' end
         when 'carbonated' then 'built_long'
         else null end;                                   -- thrown / swizzled / layered: engine default stays
  ves := case new.vessel
           when 'shaker_tin' then 'tin_on_tin' when 'mixing_glass' then 'mixing_glass' when 'blender' then 'blender_jar'
           when 'serving_glass' then case when lower(coalesce(new.glass_type,'')) ~ '(highball|collins)' then 'highball_glass' else 'rocks_glass' end
         end;
  ice := case new.mixing_ice
           when 'standard_cubes' then 'kold_draft_1_25in' when 'large_cubes' then 'large_cube_2in'
           when 'crushed' then 'crushed_pebble' when 'pebble' then 'crushed_pebble' when 'one_small_cube' then 'cube_1in'
         end;
  secs := case when new.technique_seconds_min is not null
               then round((new.technique_seconds_min + coalesce(new.technique_seconds_max, new.technique_seconds_min)) / 2, 1) end;
  select coalesce(serve_params, '{}'::jsonb) into sp from phg.recipe_versions where id = new.recipe_version_id;
  sp := sp - 'vessel_key' - 'ice_type_key' - 'agitation_s'
           || jsonb_strip_nulls(jsonb_build_object('vessel_key', ves, 'ice_type_key', ice, 'agitation_s', secs,
                                                   'from_build', true));
  if new.mixing_ice = 'none' then sp := sp - 'ice_type_key'; end if;
  update phg.recipe_versions
     set serve_method = coalesce(m, serve_method), serve_params = sp
   where id = new.recipe_version_id
     and (serve_method is distinct from coalesce(m, serve_method) or serve_params is distinct from sp);
  return new;
end $$;
drop trigger if exists recipe_builds_sync_abv on phg.recipe_builds;
create trigger recipe_builds_sync_abv after insert or update on phg.recipe_builds
  for each row execute function phg.trg_recipe_builds_sync_abv();

-- 4 ---------------------------------------------------------------------------
create or replace function phg.trg_abv_recompute_all() returns trigger
language plpgsql security definer set search_path = phg, public, pg_temp as $$
begin
  perform phg.recompute_all_recipe_abv();
  return null;
end $$;
do $$
declare t text;
begin
  foreach t in array array['prep_components','prep_recipe_versions','ice_types','bar_vessels','serve_method_profiles',
                           'bar_environment','measure_volume_standards'] loop
    if to_regclass('phg.'||t) is not null then
      execute format('drop trigger if exists abv_recompute_stmt on phg.%I', t);
      execute format('create trigger abv_recompute_stmt after insert or update or delete on phg.%I
                      for each statement execute function phg.trg_abv_recompute_all()', t);
    end if;
  end loop;
  -- ingredients: only when an ABV or density actually changes (the catalogue is edited often)
  execute 'drop trigger if exists abv_recompute_stmt on phg.ingredients';
  execute 'create trigger abv_recompute_stmt after update of alcohol_abv_pct, density_g_per_ml on phg.ingredients
           for each statement execute function phg.trg_abv_recompute_all()';
end $$;

commit;

-- VERIFY
-- select * from public.phg_menu_abv('<menu project id>');      -- as a signed-in member; menu_label null until menu-ready
-- select public.phg_recipe_abv('<recipe version id>');
-- after saving a build: select serve_method, serve_params from phg.recipe_versions where id = '<id>';
