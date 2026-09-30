-- PHG formulation step 3: recipe balance calculator (2026-09-30, Rob approved).
-- Part A: data needed by the calculator (densities from USDA household measures, TA=0 for pure sucrose/water,
--         physical_state so solids measured by spoon are never counted as liquid volume).
-- Part B: phg_mix.calc_recipe_balance(recipe_key, dilution_pct) - read-only, SECURITY INVOKER, returns every line's
--         contribution, totals, labelled ranges and exactly what is unresolved. Never guesses a missing value.
-- Part C: phg_mix.persist_recipe_balance(recipe_key) - writes recipe_balance_analysis ONLY when every liquid line is
--         resolved for sugar AND titratable acidity (guardrail 10). ABV is stored only if complete. Values are
--         pre-dilution unless a dilution is recorded for the recipe.

-- ================================================================ Part A
alter table phg_mix.ingredient_profiles add column if not exists physical_state text not null default 'liquid';
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'ingredient_profiles_physical_state_chk') then
    alter table phg_mix.ingredient_profiles add constraint ingredient_profiles_physical_state_chk check (physical_state in ('liquid','solid'));
  end if; end $$;
update phg_mix.ingredient_profiles set physical_state = 'solid' where key in ('ip_granulated_sucrose','ip_sucrose_reference');

-- Densities: USDA FDC household measures (1 US cup = 236.588 mL, 1 fl oz = 29.574 mL); sugar/100 mL = sugar/100 g x density.
update phg_mix.ingredient_profiles p set density_g_ml = v.d, sugar_g_100ml = round(p.sugar_g_100g * v.d, 2), updated_at = now(),
  measurement_basis = coalesce(p.measurement_basis,'') || ' Density ' || v.d || ' g/mL from USDA FDC ' || v.fdc || ' portion weights (' || v.portion || '); sugar per 100 mL derived.'
from (values
  ('ip_lemon_juice_working', 1.031, '167747', '1 cup = 244 g; 1 fl oz = 30.5 g'),
  ('ip_lime_juice_working', 1.023, '168156', '1 cup = 242 g (1 fl oz = 30.8 g gives 1.041; cup used)'),
  ('ip_pineapple_juice_unsweetened', 1.057, '169947', '1 cup = 250 g; 1 fl oz = 31.3 g'),
  ('ip_tomato_juice_canned', 1.027, '170458', '1 cup = 243 g; 6 fl oz = 182 g'),
  ('ip_egg_white_raw', 1.027, '172183', '1 cup = 243 g; 1 large = 33 g'),
  ('ip_cola_generic', 1.040, '174852', '16 fl oz = 492 g; 1 fl oz = 30.7 g'),
  ('ip_cranberry_juice_cocktail', 1.069, '171903', '1 cup = 253 g; 1 fl oz = 31.6 g')
) v(key, d, fdc, portion)
where p.key = v.key and p.density_g_ml is null and p.sugar_g_100g is not null;

update phg_mix.ingredient_profiles set sugar_g_100g = 8.4, density_g_ml = 1.048, sugar_g_100ml = 8.80, updated_at = now(),
  sugar_profile = sugar_profile || '{"total_g_100g":8.4,"source":"USDA FDC 169098 Orange juice, raw"}'::jsonb,
  measurement_basis = measurement_basis || ' Sugar 8.4 g/100 g (USDA FDC 169098 Orange juice, raw); density 1.048 g/mL from 1 cup = 248 g; 8.80 g/100 mL derived.'
 where key = 'ip_orange_juice_working' and sugar_g_100g is null;

-- Pure sucrose-water and water carry no titratable acid; unsweetened soda counted as 0 (TA convention degasses CO2).
update phg_mix.ingredient_profiles set ta_g_100ml = 0, updated_at = now()
 where key in ('ip_simple_1_1_weight','ip_simple_1_1_volume','ip_rich_2_1_weight','ip_rich_2_1_volume',
               'ip_simple_1_1_basis_unspecified','ip_rich_2_1_basis_unspecified','ip_water') and ta_g_100ml is null;
update phg_mix.ingredient_profiles set density_g_ml = 0.9982, sugar_g_100ml = 0, updated_at = now() where key = 'ip_water' and density_g_ml is null;
update phg_mix.ingredient_profiles set sugar_g_100ml = 0, ta_g_100ml = 0, updated_at = now(),
  notes = coalesce(notes,'') || ' TA counted as 0: titratable-acidity methods degas samples, so dissolved CO2 (carbonic acid) is excluded; carbonation is a separate sensory modifier.'
 where key = 'ip_club_soda' and ta_g_100ml is null;

insert into phg_mix.formulation_evidence (record_type, record_key, source_key, url, locator, evidence_role, note) values
 ('ingredient_profile','ip_orange_juice_working','src_usda_fdc_sr_legacy','https://fdc.nal.usda.gov/food-details/169098/nutrients','FDC 169098','supporting','sugars 8.4 g/100 g; 1 cup = 248 g'),
 ('ingredient_profile','ip_lemon_juice_working','src_usda_fdc_sr_legacy','https://fdc.nal.usda.gov/food-details/167747/portions','FDC 167747 portions','calculation_basis','density'),
 ('ingredient_profile','ip_lime_juice_working','src_usda_fdc_sr_legacy','https://fdc.nal.usda.gov/food-details/168156/portions','FDC 168156 portions','calculation_basis','density')
on conflict do nothing;

-- ================================================================ Part B: calculator
create or replace function phg_mix.calc_recipe_balance(p_recipe_key text, p_dilution_pct numeric default null)
returns jsonb
language plpgsql stable security invoker
set search_path = phg_mix, pg_temp
as $$
declare
  r record; lines jsonb := '[]'; warn text[] := '{}';
  v_vol numeric := 0; v_vol_parts boolean := false; v_has_ml boolean := false;
  s numeric := 0; s_lo numeric := 0; s_hi numeric := 0; t numeric := 0; t_lo numeric := 0; t_hi numeric := 0; e numeric := 0;
  sugar_ok boolean := true; ta_ok boolean := true; abv_ok boolean := true; vol_ok boolean := true;
  n_liquid int := 0; n_resolved int := 0; carb boolean := false;
  blockers text[] := '{}'; unresolved_sugar text[] := '{}'; unresolved_ta text[] := '{}'; unresolved_abv text[] := '{}';
  v_status text; v_ml numeric; v_s100 numeric; v_s100_lo numeric; v_s100_hi numeric; v_t100 numeric; v_t_lo numeric; v_t_hi numeric;
  rec_name text; fin numeric; res jsonb;
begin
  select name into rec_name from phg_mix.recipes where key = p_recipe_key;
  if rec_name is null then return jsonb_build_object('error','recipe not found','recipe_key',p_recipe_key); end if;
  -- parts-only recipes: concentrations are scale-free, so parts act as relative volumes
  select bool_or(ml is not null), bool_and(ml is not null or unit <> 'part') and bool_or(unit = 'part')
    into v_has_ml, v_vol_parts from phg_mix.recipe_lines where recipe_key = p_recipe_key;
  v_vol_parts := coalesce(v_vol_parts,false) and not coalesce(v_has_ml,false);

  for r in
    select i.position, i.ingredient_raw, i.amount, i.unit, i.ml, i.profile_key, i.resolution_state,
           p.ingredient_class, p.physical_state, p.abv_pct, p.sugar_g_100ml, p.sugar_g_100g, p.density_g_ml,
           p.ta_g_100ml, p.ta_min_g_100ml, p.ta_max_g_100ml, p.sugar_profile, p.basis, p.confidence, p.verification
      from phg_mix.v_recipe_balance_inputs i
      left join phg_mix.ingredient_profiles p on p.key = i.profile_key
     where i.recipe_key = p_recipe_key order by i.position
  loop
    v_ml := case when r.ml is not null then r.ml when v_vol_parts and r.unit = 'part' then r.amount end;
    v_s100 := null; v_t100 := null; v_s100_lo := null; v_s100_hi := null; v_t_lo := null; v_t_hi := null;
    if r.resolution_state = 'unmapped' then
      if v_ml is null and lower(coalesce(r.unit,'')) in ('leaf','leaves','sprig','sprigs','wedge','slice','twist','peel','piece','pinch','grind','rim') then
        v_status := 'excluded_garnish';
        warn := warn || format('"%s" (%s %s) left out as garnish/seasoning', r.ingredient_raw, coalesce(r.amount::text,''), coalesce(r.unit,''));
      else v_status := 'unresolved_unmapped'; vol_ok := false;
        blockers := blockers || (r.ingredient_raw || case when v_ml is null then ' (no profile, amount ' || coalesce(r.unit,'?') || ')' else '' end); end if;
    elsif r.physical_state = 'solid' then
      v_status := 'unresolved_solid_needs_mass'; sugar_ok := false; blockers := blockers || (r.ingredient_raw || ' (solid: needs grams)');
      unresolved_sugar := unresolved_sugar || r.ingredient_raw;
    elsif v_ml is null then
      if r.unit in ('dash','dashes','drop','drops') then
        v_status := 'trace_excluded';
        warn := warn || format('"%s" %s %s treated as trace (dash/drop volume not standardized)', r.ingredient_raw, coalesce(r.amount::text,''), r.unit);
      else v_status := 'unresolved_volume'; vol_ok := false; blockers := blockers || (r.ingredient_raw || ' (volume unknown: ' || coalesce(r.unit,'?') || ')'); end if;
    else
      n_liquid := n_liquid + 1;
      v_vol := v_vol + v_ml;
      if r.ingredient_class = 'carbonated_mixer' then carb := true; end if;
      v_s100 := coalesce(r.sugar_g_100ml, case when r.density_g_ml is not null then r.sugar_g_100g * r.density_g_ml end);
      v_s100_lo := coalesce((r.sugar_profile->>'sugar_g_100ml_min')::numeric, v_s100);
      v_s100_hi := coalesce((r.sugar_profile->>'sugar_g_100ml_max')::numeric, v_s100);
      v_t100 := r.ta_g_100ml; v_t_lo := coalesce(r.ta_min_g_100ml, v_t100); v_t_hi := coalesce(r.ta_max_g_100ml, v_t100);
      v_status := case when r.resolution_state = 'mapped_needs_composition' then 'unresolved_composition' else 'resolved' end;
      if v_s100 is null or v_status <> 'resolved' then sugar_ok := false; unresolved_sugar := unresolved_sugar || r.ingredient_raw;
      else s := s + v_ml*v_s100/100; s_lo := s_lo + v_ml*v_s100_lo/100; s_hi := s_hi + v_ml*v_s100_hi/100; end if;
      if v_t100 is null or v_status <> 'resolved' then ta_ok := false; unresolved_ta := unresolved_ta || r.ingredient_raw;
      else t := t + v_ml*v_t100/100; t_lo := t_lo + v_ml*v_t_lo/100; t_hi := t_hi + v_ml*v_t_hi/100; end if;
      if r.abv_pct is null then abv_ok := false; unresolved_abv := unresolved_abv || r.ingredient_raw; else e := e + v_ml*r.abv_pct/100; end if;
      if v_status = 'resolved' and v_s100 is not null and v_t100 is not null and r.abv_pct is not null then n_resolved := n_resolved + 1; end if;
    end if;
    lines := lines || jsonb_strip_nulls(jsonb_build_object(
      'position', r.position, 'ingredient', r.ingredient_raw, 'amount', r.amount, 'unit', r.unit, 'ml', v_ml,
      'profile_key', r.profile_key, 'status', v_status, 'basis', r.basis, 'confidence', r.confidence, 'verification', r.verification,
      'sugar_g', round(v_ml*v_s100/100, 2), 'ta_g', round(v_ml*v_t100/100, 3), 'ethanol_ml', round(v_ml*r.abv_pct/100, 2)));
  end loop;

  if not vol_ok then sugar_ok := false; ta_ok := false; abv_ok := false; end if;
  if v_vol_parts then warn := warn || 'Recipe is in parts: volumes are relative (concentrations valid, absolute grams are per "part" as mL).'::text; end if;
  warn := warn || 'Values are pre-dilution unless a dilution scenario is given; dilution is recipe- and technique-specific.'::text;
  fin := case when p_dilution_pct is not null and v_vol > 0 then v_vol * (1 + p_dilution_pct/100) end;

  res := jsonb_build_object(
    'recipe_key', p_recipe_key, 'recipe_name', rec_name, 'calculator', 'phg-balance-v1',
    'complete', jsonb_build_object('volume', vol_ok, 'sugar', sugar_ok, 'ta', ta_ok, 'abv', abv_ok),
    'blockers', to_jsonb(blockers),
    'unresolved', jsonb_build_object('sugar', to_jsonb(unresolved_sugar), 'ta', to_jsonb(unresolved_ta), 'abv', to_jsonb(unresolved_abv)),
    'input_coverage_pct', case when n_liquid > 0 then round(100.0*n_resolved/n_liquid, 1) end,
    'carbonated', carb,
    'pre_dilution', jsonb_strip_nulls(jsonb_build_object(
      'volume_ml', round(v_vol,1),
      'sugar_g', case when sugar_ok then round(s,2) end,
      'sugar_g_range', case when sugar_ok and s_hi > s_lo then jsonb_build_array(round(s_lo,2), round(s_hi,2)) end,
      'sugar_g_100ml', case when sugar_ok and v_vol > 0 then round(s/v_vol*100,2) end,
      'ta_g', case when ta_ok then round(t,3) end,
      'ta_g_range', case when ta_ok and t_hi > t_lo then jsonb_build_array(round(t_lo,3), round(t_hi,3)) end,
      'ta_g_100ml', case when ta_ok and v_vol > 0 then round(t/v_vol*100,3) end,
      'sugar_acid_ratio', case when sugar_ok and ta_ok and t > 0 then round(s/t,2) end,
      'abv_pct', case when abv_ok and v_vol > 0 then round(e/v_vol*100,1) end,
      'partial_sugar_g_known_lines', case when not sugar_ok then round(s,2) end,
      'partial_ta_g_known_lines', case when not ta_ok then round(t,3) end)),
    'dilution_scenario', case when fin is not null then jsonb_strip_nulls(jsonb_build_object(
      'dilution_pct', p_dilution_pct, 'finished_volume_ml', round(fin,1),
      'sugar_g_100ml', case when sugar_ok then round(s/fin*100,2) end,
      'ta_g_100ml', case when ta_ok then round(t/fin*100,3) end,
      'abv_pct', case when abv_ok then round(e/fin*100,1) end)) end,
    'lines', lines,
    'warnings', to_jsonb(warn),
    'rules', 'Brix is not sweetness; ratio never without absolutes; generic terms never borrow a brand''s numbers; taste at service temperature.');
  return res;
end $$;

-- ================================================================ Part C: persistence (guarded)
create or replace function phg_mix.persist_recipe_balance(p_recipe_key text, p_version text default 'phg-balance-v1')
returns jsonb
language plpgsql security definer
set search_path = phg_mix, pg_temp
as $$
declare c jsonb; pd jsonb;
begin
  c := phg_mix.calc_recipe_balance(p_recipe_key);
  if c ? 'error' then return c; end if;
  if not ((c->'complete'->>'volume')::boolean and (c->'complete'->>'sugar')::boolean and (c->'complete'->>'ta')::boolean)
     or coalesce((c->'pre_dilution'->>'volume_ml')::numeric, 0) <= 0 then
    return jsonb_build_object('recipe_key', p_recipe_key, 'persisted', false, 'reason', 'coverage incomplete',
                              'blockers', c->'blockers', 'unresolved', c->'unresolved');
  end if;
  pd := c->'pre_dilution';
  insert into phg_mix.recipe_balance_analysis (recipe_key, analysis_version, pre_dilution_volume_ml, finished_volume_ml,
      sugar_g, sugar_g_100ml, ta_g, ta_g_100ml, sugar_acid_ratio, abv_pre_dilution, abv_finished, brix_estimated,
      service_temp_c, carbonated, input_coverage_pct, assumptions, warnings)
  values (p_recipe_key, p_version, (pd->>'volume_ml')::numeric, null,
      (pd->>'sugar_g')::numeric, (pd->>'sugar_g_100ml')::numeric, (pd->>'ta_g')::numeric, (pd->>'ta_g_100ml')::numeric,
      (pd->>'sugar_acid_ratio')::numeric, (pd->>'abv_pct')::numeric, null, null, null, (c->>'carbonated')::boolean,
      (c->>'input_coverage_pct')::numeric,
      jsonb_build_object('basis','pre_dilution','calculator',c->>'calculator','complete',c->'complete','unresolved',c->'unresolved',
                         'sugar_g_range',pd->'sugar_g_range','ta_g_range',pd->'ta_g_range','lines',c->'lines'),
      array(select jsonb_array_elements_text(c->'warnings')))
  on conflict (recipe_key, analysis_version) do update set
      pre_dilution_volume_ml = excluded.pre_dilution_volume_ml, sugar_g = excluded.sugar_g, sugar_g_100ml = excluded.sugar_g_100ml,
      ta_g = excluded.ta_g, ta_g_100ml = excluded.ta_g_100ml, sugar_acid_ratio = excluded.sugar_acid_ratio,
      abv_pre_dilution = excluded.abv_pre_dilution, carbonated = excluded.carbonated, input_coverage_pct = excluded.input_coverage_pct,
      assumptions = excluded.assumptions, warnings = excluded.warnings, calculated_at = now();
  return jsonb_build_object('recipe_key', p_recipe_key, 'persisted', true, 'abv_complete', c->'complete'->'abv');
end $$;

create or replace function phg_mix.persist_all_recipe_balances(p_version text default 'phg-balance-v1')
returns jsonb language plpgsql security definer set search_path = phg_mix, pg_temp as $$
declare k text; r jsonb; n_ok int := 0; n_skip int := 0;
begin
  for k in select key from phg_mix.recipes order by key loop
    r := phg_mix.persist_recipe_balance(k, p_version);
    if (r->>'persisted')::boolean then n_ok := n_ok + 1; else n_skip := n_skip + 1; end if;
  end loop;
  return jsonb_build_object('persisted', n_ok, 'skipped_incomplete', n_skip);
end $$;

revoke all on function phg_mix.calc_recipe_balance(text, numeric) from public;
grant execute on function phg_mix.calc_recipe_balance(text, numeric) to phg_harmony_reader, service_role;
revoke all on function phg_mix.persist_recipe_balance(text, text) from public, anon, authenticated;
revoke all on function phg_mix.persist_all_recipe_balances(text) from public, anon, authenticated;
grant execute on function phg_mix.persist_recipe_balance(text, text) to service_role;
grant execute on function phg_mix.persist_all_recipe_balances(text) to service_role;
