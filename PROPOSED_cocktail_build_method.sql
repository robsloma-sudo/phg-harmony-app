-- ============================================================================
-- PROPOSED MIGRATION (NOT APPLIED) — full build method on PHG cocktail cards
-- Brief: "Full build method on PHG cocktail cards" (#phg-ops 2026-10-06 14:47, Priority High)
-- Author: Backend Lead. Needs leadership sign-off before it runs.
--
-- WHAT IT DOES
--   1. phg.build_options        the option lists (style, vessel, technique, ice, strain, glass prep,
--                               service ice, garnish placement/action). Cocktail Dev owns these rows and
--                               can add/rename/retire options without another migration.
--   2. phg.recipe_builds        one row per recipe version: the build, glassware and numbered method steps.
--   3. phg.recipe_garnishes     one or more garnish rows per recipe version, in order.
--   4. recipe_versions.method_legacy   the old one-line method is COPIED here. The existing `method` column is
--                               left exactly as it is, because ~29 database functions (costing, menu engineering,
--                               training, Harmony) read it today. Nothing is extracted from the old text.
--   5. phg.phg_recipe_build_check(id)  the six blocking checks -> {complete, problems[]}.
--   6. Approval gate            a trigger refuses status -> 'approved' while the check fails ("Method incomplete").
--                               Already-approved cards are NOT changed; they show the "Method incomplete" badge
--                               until Cocktail Dev fills in their builds.
--   7. phg.phg_recipe_build_render(id) the one text block every surface prints (card, PDF, training view), in the
--                               brief's exact format, or a METHOD INCOMPLETE block with the legacy line.
--   8. API: public.phg_recipe_build_get(id) / public.phg_recipe_build_save(id, build, garnishes)
--                               signed-in only; same permission as the cocktail card (phg_cocktail_can); saving
--                               also needs owner/admin/editor on the venue's account (or platform admin).
--
-- RISK: additive. No existing column, constraint, row value or function changes. New tables have RLS on with no
--       direct grants to anon/authenticated (all access through the two RPCs).
-- KNOWN EFFECT: until Cocktail Dev fills in builds, NO card can move to 'approved'. That is the brief's intent.
-- ROLLBACK (in this order):
--   drop trigger if exists recipe_versions_build_gate on phg.recipe_versions;
--   drop function if exists phg.trg_recipe_versions_build_gate(), public.phg_recipe_build_save(uuid,jsonb,jsonb),
--     public.phg_recipe_build_get(uuid), phg.phg_recipe_build_render(uuid), phg.phg_recipe_build_check(uuid),
--     phg.trg_build_option_validate();
--   drop table if exists phg.recipe_garnishes, phg.recipe_builds, phg.build_options;
--   alter table phg.recipe_versions drop column if exists method_legacy;
-- ============================================================================
begin;

-- 1 ---------------------------------------------------------------------------
create table if not exists phg.build_options (
  field   text not null,
  value   text not null,
  label   text not null,
  sort    int  not null default 100,
  active  boolean not null default true,
  primary key (field, value)
);
comment on table phg.build_options is 'Option lists for cocktail builds. Owned by Cocktail Dev; retire with active=false rather than delete.';
insert into phg.build_options (field, value, label, sort) values
 ('style','shaken','Shaken',10),('style','stirred','Stirred',20),('style','built','Built',30),('style','thrown','Thrown',40),
 ('style','swizzled','Swizzled',50),('style','blended','Blended',60),('style','carbonated','Carbonated',70),('style','layered','Layered',80),
 ('vessel','shaker_tin','Shaker tin',10),('vessel','mixing_glass','Mixing glass',20),('vessel','serving_glass','Serving glass',30),('vessel','blender','Blender',40),
 ('technique','hard_shake','Hard shake',10),('technique','short_shake','Short shake',20),('technique','whip_shake','Whip shake',30),
 ('technique','dry_shake','Dry shake',40),('technique','reverse_dry_shake','Reverse dry shake',50),('technique','stir','Stir',60),
 ('technique','throw','Throw',70),('technique','swizzle','Swizzle',80),('technique','build_and_top','Build and top',90),
 ('mixing_ice','standard_cubes','Standard cubes',10),('mixing_ice','large_cubes','Large cubes',20),('mixing_ice','crushed','Crushed',30),
 ('mixing_ice','pebble','Pebble',40),('mixing_ice','one_small_cube','One small cube',50),('mixing_ice','none','No ice',60),
 ('strain','single','Single strain',10),('strain','double','Double strain',20),('strain','julep','Julep strain',30),('strain','none','No strain',40),
 ('glass_prep','chilled','chilled',10),('glass_prep','frozen','frozen',20),('glass_prep','rinse','rinsed',30),
 ('glass_prep','salt_rim','salt rim',40),('glass_prep','sugar_rim','sugar rim',50),('glass_prep','none','',60),
 ('service_ice','served_up','Served up',10),('service_ice','large_cube','Large cube',20),('service_ice','clear_king_cube','Clear king cube',30),
 ('service_ice','standard_cubes','Standard cubes',40),('service_ice','crushed','Crushed ice',50),('service_ice','collins_spear','Collins spear',60),
 ('service_ice','sphere','Ice sphere',70),
 ('garnish_placement','on_rim','on the rim',10),('garnish_placement','floated','floated',20),('garnish_placement','skewered','skewered',30),
 ('garnish_placement','dropped_in','dropped in',40),('garnish_placement','discarded','then discarded',50),
 ('garnish_action','express','expressed over the surface',10),('garnish_action','flame','flamed',20),('garnish_action','mist','misted',30),
 ('garnish_action','grate','grated over',40),('garnish_action','spank','spanked',50),('garnish_action','none','',60)
on conflict (field, value) do nothing;

-- 2 ---------------------------------------------------------------------------
create table if not exists phg.recipe_builds (
  recipe_version_id     uuid primary key references phg.recipe_versions(id) on delete cascade,
  style                 text,
  vessel                text,
  technique             text,
  technique_seconds_min numeric check (technique_seconds_min is null or technique_seconds_min > 0),
  technique_seconds_max numeric check (technique_seconds_max is null or technique_seconds_max >= technique_seconds_min),
  technique_until       text,      -- e.g. 'until the ice dissolves' (whip shake)
  technique_passes      int  check (technique_passes is null or technique_passes > 0),  -- throw
  mixing_ice            text,
  strain                text,
  dilution_target_pct   numeric check (dilution_target_pct is null or dilution_target_pct between 0 and 100),
  glass_type            text,
  glass_size_ml         numeric check (glass_size_ml is null or glass_size_ml > 0),
  glass_prep            text,
  glass_prep_product    text,      -- the rinse product, e.g. 'absinthe'
  service_ice           text,
  no_garnish            boolean not null default false,  -- explicit "No garnish" row
  steps                 text[] not null default '{}',     -- numbered method, one action per step, in order
  notes                 text,
  updated_at            timestamptz not null default now(),
  updated_by            uuid
);

-- 3 ---------------------------------------------------------------------------
create table if not exists phg.recipe_garnishes (
  id                uuid primary key default gen_random_uuid(),
  recipe_version_id uuid not null references phg.recipe_versions(id) on delete cascade,
  position          int  not null check (position > 0),
  item              text not null,
  prep              text,          -- e.g. '5 cm swath, pith trimmed'
  placement         text,
  action            text,
  allergen          text,          -- e.g. 'tree nuts'
  unique (recipe_version_id, position)
);

-- option values must exist (and be active) in build_options
create or replace function phg.trg_build_option_validate() returns trigger
language plpgsql set search_path = phg, pg_temp as $$
declare f text; v text; pairs text[][];
begin
  if tg_table_name = 'recipe_builds' then
    pairs := array[['style',new.style],['vessel',new.vessel],['technique',new.technique],['mixing_ice',new.mixing_ice],
                   ['strain',new.strain],['glass_prep',new.glass_prep],['service_ice',new.service_ice]];
    new.updated_at := now();
  else
    pairs := array[['garnish_placement',new.placement],['garnish_action',new.action]];
  end if;
  for i in 1 .. array_length(pairs,1) loop
    f := pairs[i][1]; v := pairs[i][2];
    if v is not null and not exists (select 1 from phg.build_options o where o.field = f and o.value = v and o.active) then
      raise exception 'unknown % "%" (see phg.build_options)', f, v using errcode = '23514';
    end if;
  end loop;
  return new;
end $$;
drop trigger if exists recipe_builds_validate on phg.recipe_builds;
create trigger recipe_builds_validate before insert or update on phg.recipe_builds
  for each row execute function phg.trg_build_option_validate();
drop trigger if exists recipe_garnishes_validate on phg.recipe_garnishes;
create trigger recipe_garnishes_validate before insert or update on phg.recipe_garnishes
  for each row execute function phg.trg_build_option_validate();

-- 4 ---------------------------------------------------------------------------
alter table phg.recipe_versions add column if not exists method_legacy text;
update phg.recipe_versions set method_legacy = method
 where method_legacy is null and coalesce(method, '') <> '';
comment on column phg.recipe_versions.method_legacy is
  'The old one-line method, kept verbatim (2026-10-06). Not parsed. The full build lives in phg.recipe_builds + phg.recipe_garnishes.';

-- RLS: no direct access; everything goes through the RPCs below
alter table phg.build_options    enable row level security;
alter table phg.recipe_builds    enable row level security;
alter table phg.recipe_garnishes enable row level security;
revoke all on phg.build_options, phg.recipe_builds, phg.recipe_garnishes from anon, authenticated;

-- 5 ---------------------------------------------------------------------------
create or replace function phg.phg_recipe_build_check(p_recipe_version_id uuid)
returns jsonb language plpgsql stable security definer set search_path = phg, public, pg_temp as $$
declare b phg.recipe_builds%rowtype; p text[] := '{}'; n_g int; card_allergens text[]; g record;
begin
  select * into b from phg.recipe_builds where recipe_version_id = p_recipe_version_id;
  if not found then
    return jsonb_build_object('complete', false, 'problems', jsonb_build_array('No build entered yet (method is one line)'));
  end if;
  if coalesce(array_length(b.steps, 1), 0) < 3 then p := p || 'Fewer than 3 method steps'::text; end if;
  if b.style is null then p := p || 'No build style'::text; end if;
  if (b.style in ('shaken','stirred') or b.technique in ('hard_shake','short_shake','dry_shake','reverse_dry_shake','stir'))
     and b.technique_seconds_min is null then
    p := p || 'Shake or stir has no time'::text;
  end if;
  if b.technique = 'whip_shake' and b.technique_seconds_min is null and coalesce(b.technique_until,'') = '' then
    p := p || 'Whip shake needs a time or an "until" cue'::text;
  end if;
  if coalesce(b.style,'') not in ('built','blended','layered') and b.strain is null then
    p := p || 'No strain (only built, blended or layered drinks may skip it)'::text;
  end if;
  if b.glass_type is null    then p := p || 'No glass'::text; end if;
  if b.glass_size_ml is null then p := p || 'No glass size'::text; end if;
  if b.service_ice is null   then p := p || 'No serving ice'::text; end if;
  select count(*) into n_g from phg.recipe_garnishes where recipe_version_id = p_recipe_version_id;
  if n_g = 0 and not b.no_garnish then p := p || 'No garnish row (add one, or mark "No garnish")'::text; end if;
  select coalesce(array_agg(lower(a->>'allergen')), '{}') into card_allergens
    from jsonb_array_elements(coalesce(phg.phg_recipe_compliance(p_recipe_version_id)->'allergens', '[]'::jsonb)) a;
  for g in select item, allergen from phg.recipe_garnishes
            where recipe_version_id = p_recipe_version_id and coalesce(allergen,'') <> '' loop
    if not lower(g.allergen) = any(card_allergens) then
      p := p || format('Garnish allergen "%s" (%s) is not in the card''s allergen list', g.allergen, g.item)::text;
    end if;
  end loop;
  return jsonb_build_object('complete', coalesce(array_length(p,1),0) = 0, 'problems', to_jsonb(p));
end $$;

-- 6 ---------------------------------------------------------------------------
create or replace function phg.trg_recipe_versions_build_gate() returns trigger
language plpgsql set search_path = phg, public, pg_temp as $$
declare c jsonb;
begin
  if new.status = 'approved' and (tg_op = 'INSERT' or old.status is distinct from 'approved') then
    c := phg.phg_recipe_build_check(new.id);
    if not (c->>'complete')::boolean then
      raise exception 'Method incomplete: %', (select string_agg(x, '; ') from jsonb_array_elements_text(c->'problems') x)
        using errcode = '23514', hint = 'Fill in the build (phg.recipe_builds + phg.recipe_garnishes) before approving.';
    end if;
  end if;
  return new;
end $$;
drop trigger if exists recipe_versions_build_gate on phg.recipe_versions;
create trigger recipe_versions_build_gate before insert or update of status on phg.recipe_versions
  for each row execute function phg.trg_recipe_versions_build_gate();

-- 7 ---------------------------------------------------------------------------
create or replace function phg.phg_recipe_build_render(p_recipe_version_id uuid)
returns text language plpgsql stable security definer set search_path = phg, public, pg_temp as $$
declare b phg.recipe_builds%rowtype; c jsonb; legacy text; lbl text; t text; build text; glass text; gars text; steps text := ''; i int;
begin
  c := phg.phg_recipe_build_check(p_recipe_version_id);
  select coalesce(method_legacy, method) into legacy from phg.recipe_versions where id = p_recipe_version_id;
  select * into b from phg.recipe_builds where recipe_version_id = p_recipe_version_id;
  if not found or not (c->>'complete')::boolean then
    return 'METHOD INCOMPLETE' || E'\n' || coalesce('Legacy method: ' || legacy, 'No method recorded') || E'\n'
        || 'Missing: ' || coalesce((select string_agg(x, '; ') from jsonb_array_elements_text(c->'problems') x), '');
  end if;
  -- BUILD line
  build := (select label from build_options where field='style' and value=b.style);
  if b.technique is not null then
    t := (select label from build_options where field='technique' and value=b.technique);
    if b.technique_seconds_min is not null then
      t := t || ' ' || trim(to_char(b.technique_seconds_min,'FM999.##'))
             || case when b.technique_seconds_max is not null and b.technique_seconds_max <> b.technique_seconds_min
                     then E'\u2013' || trim(to_char(b.technique_seconds_max,'FM999.##')) else '' end || ' s';
    elsif b.technique_passes is not null then t := t || ' ' || b.technique_passes || ' passes';
    elsif coalesce(b.technique_until,'') <> '' then t := t || ' ' || b.technique_until;
    end if;
    build := build || E' \u00b7 ' || t;
  end if;
  if b.strain is not null and b.strain <> 'none' then
    build := build || E' \u00b7 ' || (select label from build_options where field='strain' and value=b.strain);
  end if;
  -- GLASS line
  glass := b.glass_type || ' ' || trim(to_char(b.glass_size_ml,'FM9999')) || ' ml';
  lbl := (select label from build_options where field='glass_prep' and value=b.glass_prep);
  if coalesce(lbl,'') <> '' then glass := glass || ', ' || lbl || coalesce(' with ' || b.glass_prep_product, ''); end if;
  glass := glass || E' \u00b7 ' || (select label from build_options where field='service_ice' and value=b.service_ice);
  -- GARNISH line
  if b.no_garnish then gars := 'No garnish';
  else
    select string_agg(g.item || coalesce(' (' || g.prep || ')', '')
             || coalesce(', ' || nullif((select label from build_options where field='garnish_action' and value=g.action),''), '')
             || coalesce(', ' || nullif((select label from build_options where field='garnish_placement' and value=g.placement),''), ''),
           '; ' order by g.position) into gars
      from recipe_garnishes g where g.recipe_version_id = p_recipe_version_id;
  end if;
  for i in 1 .. array_length(b.steps,1) loop steps := steps || i || '. ' || b.steps[i] || E'\n'; end loop;
  return 'BUILD   ' || E'\u00b7 ' || build || E'\n'
      || 'GLASS   ' || E'\u00b7 ' || glass || E'\n'
      || 'GARNISH ' || E'\u00b7 ' || gars || E'\n\nMETHOD\n' || rtrim(steps, E'\n');
end $$;

-- 8 ---------------------------------------------------------------------------
create or replace function public.phg_recipe_build_get(p_recipe_version_id uuid)
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare uid uuid := auth.uid();
begin
  if not public.phg_cocktail_can(uid, p_recipe_version_id) then raise exception 'not permitted' using errcode = '42501'; end if;
  return jsonb_build_object(
    'build',     (select to_jsonb(b) - 'recipe_version_id' from phg.recipe_builds b where b.recipe_version_id = p_recipe_version_id),
    'garnishes', coalesce((select jsonb_agg(to_jsonb(g) - 'recipe_version_id' - 'id' order by g.position) from phg.recipe_garnishes g where g.recipe_version_id = p_recipe_version_id), '[]'::jsonb),
    'method_legacy', (select coalesce(v.method_legacy, v.method) from phg.recipe_versions v where v.id = p_recipe_version_id),
    'check',     phg.phg_recipe_build_check(p_recipe_version_id),
    'render',    phg.phg_recipe_build_render(p_recipe_version_id),
    'options',   (select jsonb_object_agg(field, opts) from (select field, jsonb_agg(jsonb_build_object('value',value,'label',label) order by sort) opts
                    from phg.build_options where active group by field) o));
end $$;

create or replace function public.phg_recipe_build_save(p_recipe_version_id uuid, p_build jsonb, p_garnishes jsonb default '[]'::jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare uid uuid := auth.uid(); may boolean; g jsonb; pos int := 0;
begin
  select phg.is_platform_admin(uid) or exists (
           select 1 from phg.recipe_versions v
             join phg.menu_items mi on mi.recipe_project_id = v.project_id
             join phg.menu_projects mp on mp.id = mi.menu_project_id
             join phg.account_memberships m on m.account_id = mp.account_id
            where v.id = p_recipe_version_id and m.user_id = uid and m.status = 'active' and m.role in ('owner','admin','editor'))
    into may;
  if not coalesce(may, false) then raise exception 'not permitted' using errcode = '42501'; end if;

  insert into phg.recipe_builds as r (recipe_version_id, style, vessel, technique, technique_seconds_min, technique_seconds_max,
     technique_until, technique_passes, mixing_ice, strain, dilution_target_pct, glass_type, glass_size_ml, glass_prep,
     glass_prep_product, service_ice, no_garnish, steps, notes, updated_by)
  values (p_recipe_version_id, p_build->>'style', p_build->>'vessel', p_build->>'technique',
     (p_build->>'technique_seconds_min')::numeric, (p_build->>'technique_seconds_max')::numeric,
     p_build->>'technique_until', (p_build->>'technique_passes')::int, p_build->>'mixing_ice', p_build->>'strain',
     (p_build->>'dilution_target_pct')::numeric, p_build->>'glass_type', (p_build->>'glass_size_ml')::numeric,
     p_build->>'glass_prep', p_build->>'glass_prep_product', p_build->>'service_ice',
     coalesce((p_build->>'no_garnish')::boolean, false),
     coalesce((select array_agg(x) from jsonb_array_elements_text(coalesce(p_build->'steps','[]'::jsonb)) x), '{}'),
     p_build->>'notes', uid)
  on conflict (recipe_version_id) do update set
     style = excluded.style, vessel = excluded.vessel, technique = excluded.technique,
     technique_seconds_min = excluded.technique_seconds_min, technique_seconds_max = excluded.technique_seconds_max,
     technique_until = excluded.technique_until, technique_passes = excluded.technique_passes,
     mixing_ice = excluded.mixing_ice, strain = excluded.strain, dilution_target_pct = excluded.dilution_target_pct,
     glass_type = excluded.glass_type, glass_size_ml = excluded.glass_size_ml, glass_prep = excluded.glass_prep,
     glass_prep_product = excluded.glass_prep_product, service_ice = excluded.service_ice,
     no_garnish = excluded.no_garnish, steps = excluded.steps, notes = excluded.notes, updated_by = excluded.updated_by;

  delete from phg.recipe_garnishes where recipe_version_id = p_recipe_version_id;
  for g in select * from jsonb_array_elements(coalesce(p_garnishes, '[]'::jsonb)) loop
    pos := pos + 1;
    insert into phg.recipe_garnishes (recipe_version_id, position, item, prep, placement, action, allergen)
    values (p_recipe_version_id, pos, g->>'item', g->>'prep', g->>'placement', g->>'action', nullif(g->>'allergen',''));
  end loop;
  return public.phg_recipe_build_get(p_recipe_version_id);
end $$;

revoke all on function public.phg_recipe_build_get(uuid), public.phg_recipe_build_save(uuid,jsonb,jsonb) from public, anon;
grant execute on function public.phg_recipe_build_get(uuid), public.phg_recipe_build_save(uuid,jsonb,jsonb) to authenticated;
revoke all on function phg.phg_recipe_build_check(uuid), phg.phg_recipe_build_render(uuid) from public, anon, authenticated;

commit;

-- VERIFY (read-only)
-- select count(*) from phg.build_options;                                              -- 55
-- select count(*) from phg.recipe_versions where method_legacy is not null;             -- 6
-- select recipe_name, phg.phg_recipe_build_check(id)->>'complete' from phg.recipe_versions;  -- all false until builds exist
-- select phg.phg_recipe_build_render(id) from phg.recipe_versions limit 1;              -- METHOD INCOMPLETE block
