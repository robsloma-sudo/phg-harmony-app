-- PHG corpus browser v2 (PHG-027, 2026-09-27): multi-select filters, census (ZIP-level ACS) bands,
-- sort options and page sizes up to 100 for the iPhone-compact Menu Library.
-- Backward compatible: every filter key still accepts a single string (live 18.49.4 / 18.49.5 bodies),
-- and now also accepts a JSON array of strings (any-of). Service-role only, as before.
--
-- New keys (documents; candidates accept the same filters except sort):
--   state, city, venue_type, asset_kind, menu_scope, status, prep_type : string | string[]
--   income | age | young | affluent | edu | hisp : string[] of census band keys (see phg_census_band_catalog)
--   sort : recent (default) | name | city | income_desc | income_asc | age_asc | age_desc |
--          young_desc | affluent_desc | edu_desc | hisp_desc
--   limit 1..100 (was 60)
-- Census values come from phg_census_zcta joined on the venue ZIP (accounts.postal_code). A venue
-- whose ZIP has no census row, or whose value the Census suppresses, is band 'na' ("No census data").

create or replace function public.phg_jsonb_text_list(p jsonb, k text)
returns text[]
language sql immutable parallel safe
set search_path = ''
as $$
  select case jsonb_typeof(p -> k)
    when 'array' then (
      select nullif(array(
        select distinct btrim(x)
          from jsonb_array_elements_text(p -> k) with ordinality as t(x, i)
         where btrim(x) <> '' and i <= 200), '{}'::text[]))
    when 'string' then case when btrim(p ->> k) <> '' then array[btrim(p ->> k)] end
    else null
  end;
$$;

-- No SET clause on purpose: a SET prevents the planner from inlining this pure CASE expression,
-- and the filter-values query evaluates it ~105k times (5.5 s -> 11 s in the dry run when not inlined).
-- It references no tables or user-defined operators, so search_path cannot change its meaning.
create or replace function public.phg_census_band(p_metric text, v numeric)
returns text
language sql immutable parallel safe
as $$
  select case
    when v is null then 'na'
    when p_metric = 'income' then case when v < 50000 then 'lt50' when v < 75000 then '50_75'
                                       when v < 100000 then '75_100' when v < 150000 then '100_150' else '150p' end
    when p_metric = 'age'    then case when v < 30 then 'lt30' when v < 35 then '30_35'
                                       when v < 40 then '35_40' when v < 45 then '40_45' else '45p' end
    when p_metric = 'young'  then case when v < 15 then 'lt15' when v < 20 then '15_20'
                                       when v < 30 then '20_30' else '30p' end
    when p_metric in ('affluent', 'edu')
                             then case when v < 25 then 'lt25' when v < 40 then '25_40'
                                       when v < 60 then '40_60' else '60p' end
    when p_metric = 'hisp'   then case when v < 10 then 'lt10' when v < 25 then '10_25'
                                       when v < 50 then '25_50' else '50p' end
  end;
$$;

create or replace function public.phg_census_band_catalog()
returns jsonb
language sql immutable parallel safe
set search_path = ''
as $$
  select jsonb_build_object(
    'income', jsonb_build_object('label', 'Income', 'long', 'Median household income', 'bands', jsonb_build_array(
        jsonb_build_object('v','lt50','label','Under $50k'), jsonb_build_object('v','50_75','label','$50–75k'),
        jsonb_build_object('v','75_100','label','$75–100k'), jsonb_build_object('v','100_150','label','$100–150k'),
        jsonb_build_object('v','150p','label','$150k+'), jsonb_build_object('v','na','label','No census data'))),
    'age', jsonb_build_object('label', 'Age', 'long', 'Median age', 'bands', jsonb_build_array(
        jsonb_build_object('v','lt30','label','Under 30'), jsonb_build_object('v','30_35','label','30–35'),
        jsonb_build_object('v','35_40','label','35–40'), jsonb_build_object('v','40_45','label','40–45'),
        jsonb_build_object('v','45p','label','45+'), jsonb_build_object('v','na','label','No census data'))),
    'young', jsonb_build_object('label', '21–34', 'long', 'Share of people aged 21–34', 'bands', jsonb_build_array(
        jsonb_build_object('v','lt15','label','Under 15%'), jsonb_build_object('v','15_20','label','15–20%'),
        jsonb_build_object('v','20_30','label','20–30%'), jsonb_build_object('v','30p','label','30%+'),
        jsonb_build_object('v','na','label','No census data'))),
    'affluent', jsonb_build_object('label', '$100k+', 'long', 'Share of households earning $100k+', 'bands', jsonb_build_array(
        jsonb_build_object('v','lt25','label','Under 25%'), jsonb_build_object('v','25_40','label','25–40%'),
        jsonb_build_object('v','40_60','label','40–60%'), jsonb_build_object('v','60p','label','60%+'),
        jsonb_build_object('v','na','label','No census data'))),
    'edu', jsonb_build_object('label', 'Degree', 'long', 'Adults 25+ with a bachelor''s degree or higher', 'bands', jsonb_build_array(
        jsonb_build_object('v','lt25','label','Under 25%'), jsonb_build_object('v','25_40','label','25–40%'),
        jsonb_build_object('v','40_60','label','40–60%'), jsonb_build_object('v','60p','label','60%+'),
        jsonb_build_object('v','na','label','No census data'))),
    'hisp', jsonb_build_object('label', 'Hispanic', 'long', 'Hispanic or Latino share of population', 'bands', jsonb_build_array(
        jsonb_build_object('v','lt10','label','Under 10%'), jsonb_build_object('v','10_25','label','10–25%'),
        jsonb_build_object('v','25_50','label','25–50%'), jsonb_build_object('v','50p','label','50%+'),
        jsonb_build_object('v','na','label','No census data')))
  );
$$;

-- Raise if any requested band is not in the catalog for that metric.
create or replace function public.phg_census_check_bands(p_metric text, p_bands text[])
returns void
language plpgsql immutable
set search_path = ''
as $$
declare v_ok text[];
begin
  if p_bands is null then return; end if;
  select array_agg(b ->> 'v') into v_ok
    from jsonb_array_elements(public.phg_census_band_catalog() -> p_metric -> 'bands') b;
  if v_ok is null or not (p_bands <@ v_ok) then
    raise exception 'invalid census band for %', p_metric;
  end if;
end;
$$;

create or replace function public.phg_corpus_browse_documents(p jsonb)
returns jsonb
language plpgsql stable security definer
set search_path = public, pg_temp
as $$
declare
  v_kind       text := coalesce(nullif(btrim(p->>'kind'),''), 'rendered');
  v_limit      int  := least(100, greatest(1, coalesce((p->>'limit')::int, 24)));
  v_offset     int  := least(1000000, greatest(0, coalesce((p->>'offset')::int, 0)));
  v_q          text := nullif(btrim(p->>'q'), '');
  v_states     text[] := (select array_agg(upper(x)) from unnest(public.phg_jsonb_text_list(p, 'state')) x);
  v_cities     text[] := (select array_agg(upper(x)) from unnest(public.phg_jsonb_text_list(p, 'city')) x);
  v_vtypes     text[] := (select array_agg(lower(x)) from unnest(public.phg_jsonb_text_list(p, 'venue_type')) x);
  v_assets     text[] := public.phg_jsonb_text_list(p, 'asset_kind');
  v_scopes     text[] := public.phg_jsonb_text_list(p, 'menu_scope');
  v_statuses   text[] := public.phg_jsonb_text_list(p, 'status');
  v_cocktail   text := nullif(btrim(p->>'cocktail'), '');
  v_ingredient text := nullif(btrim(p->>'ingredient'), '');
  v_preps      text[] := (select array_agg(lower(x)) from unnest(public.phg_jsonb_text_list(p, 'prep_type')) x);
  v_income     text[] := public.phg_jsonb_text_list(p, 'income');
  v_age        text[] := public.phg_jsonb_text_list(p, 'age');
  v_young      text[] := public.phg_jsonb_text_list(p, 'young');
  v_affluent   text[] := public.phg_jsonb_text_list(p, 'affluent');
  v_edu        text[] := public.phg_jsonb_text_list(p, 'edu');
  v_hisp       text[] := public.phg_jsonb_text_list(p, 'hisp');
  v_sort       text := lower(coalesce(nullif(btrim(p->>'sort'),''), 'recent'));
  v_patterns   text[];
  v_text_filter boolean;
  v_count      bigint;
  v_rows       jsonb;
begin
  if v_kind not in ('rendered','remaining','archived') then v_kind := 'archived'; end if;
  if v_kind = 'rendered' then v_statuses := array['ready']; end if;
  if v_states is not null and exists (select 1 from unnest(v_states) s where s !~ '^[A-Z]{2}$') then
    raise exception 'invalid state';
  end if;
  if v_preps is not null then
    if exists (select 1 from unnest(v_preps) x where public.phg_prep_patterns(x) is null) then
      raise exception 'unknown prep_type %', array_to_string(v_preps, ',');
    end if;
    select array_agg(distinct pat) into v_patterns
      from unnest(v_preps) x, unnest(public.phg_prep_patterns(x)) pat;
  end if;
  perform public.phg_census_check_bands('income', v_income);
  perform public.phg_census_check_bands('age', v_age);
  perform public.phg_census_check_bands('young', v_young);
  perform public.phg_census_check_bands('affluent', v_affluent);
  perform public.phg_census_check_bands('edu', v_edu);
  perform public.phg_census_check_bands('hisp', v_hisp);
  if v_sort not in ('recent','name','city','income_desc','income_asc','age_asc','age_desc',
                    'young_desc','affluent_desc','edu_desc','hisp_desc') then
    v_sort := 'recent';
  end if;
  v_text_filter := (v_cocktail is not null or v_ingredient is not null or v_patterns is not null);

  with base as (
    select d.id, d.account_id, d.menu_source_candidate_id, d.original_menu_url, d.discovered_asset_url,
           d.asset_kind, d.acquisition_method, d.acquisition_status, d.page_count, d.menu_scope,
           d.page_render_status, d.page_rendered_at, d.discovered_at, d.acquired_at, d.updated_at,
           a.account_name, a.street_address, a.postal_code, a.google_types, a.website_url,
           public.account_state(a.account_id)                 as state,
           substring(a.notes from 'City: ([^.]+)')            as city,
           coalesce(a.google_types[1], a.format_code)         as venue_type,
           z.zcta, z.total_population, z.median_age, z.median_household_income, z.pop_21_34_pct,
           z.households_over_100k_pct, z.bachelors_or_higher_pct, z.hispanic_latino_pct
    from public.menu_visual_documents d
    join public.accounts a on a.account_id = d.account_id
    left join public.phg_census_zcta z on z.zcta = left(a.postal_code, 5)
    where (v_kind <> 'rendered'  or d.page_render_status = 'ready')
      and (v_kind <> 'remaining' or d.page_render_status is distinct from 'ready')
      and (v_statuses is null or d.page_render_status = any (v_statuses))
      and (v_assets   is null or d.asset_kind = any (v_assets))
      and (v_scopes   is null or d.menu_scope = any (v_scopes))
      and (v_q        is null or a.account_name ilike '%' || public.phg_like_escape(v_q) || '%')
      and (v_states   is null or public.account_state(a.account_id) = any (v_states))
      and (v_cities   is null or upper(btrim(substring(a.notes from 'City: ([^.]+)'))) = any (v_cities))
      and (v_vtypes   is null
           or lower(coalesce(a.google_types[1], a.format_code)) = any (v_vtypes)
           or exists (select 1 from unnest(coalesce(a.google_types, '{}'::text[])) t where lower(t) = any (v_vtypes)))
      and (v_income   is null or public.phg_census_band('income',   z.median_household_income)  = any (v_income))
      and (v_age      is null or public.phg_census_band('age',      z.median_age)               = any (v_age))
      and (v_young    is null or public.phg_census_band('young',    z.pop_21_34_pct)            = any (v_young))
      and (v_affluent is null or public.phg_census_band('affluent', z.households_over_100k_pct) = any (v_affluent))
      and (v_edu      is null or public.phg_census_band('edu',      z.bachelors_or_higher_pct)  = any (v_edu))
      and (v_hisp     is null or public.phg_census_band('hisp',     z.hispanic_latino_pct)      = any (v_hisp))
      and (not v_text_filter
           or exists (select 1 from public.staging_menu_extract s
                      where s.superseded_at is null
                        and s.menu_page_url = d.original_menu_url
                        and s.item_type = 'cocktail'
                        and (v_cocktail   is null or s.item_name ilike '%' || public.phg_like_escape(v_cocktail) || '%')
                        and (v_ingredient is null or s.notes     ilike '%' || public.phg_like_escape(v_ingredient) || '%')
                        and (v_patterns   is null or s.notes     ilike any (v_patterns))))
  ),
  keyed as (
    select b.*,
      case v_sort
        when 'income_desc'   then -b.median_household_income
        when 'income_asc'    then  b.median_household_income
        when 'age_asc'       then  b.median_age
        when 'age_desc'      then -b.median_age
        when 'young_desc'    then -b.pop_21_34_pct
        when 'affluent_desc' then -b.households_over_100k_pct
        when 'edu_desc'      then -b.bachelors_or_higher_pct
        when 'hisp_desc'     then -b.hispanic_latino_pct
      end::numeric as k1,
      case v_sort
        when 'name' then lower(b.account_name)
        when 'city' then upper(btrim(coalesce(b.city, ''))) || ' ' || lower(coalesce(b.account_name, ''))
      end as k2
    from base b
  ),
  counted as (select count(*) as c from base),
  pg as (
    select k.*, row_number() over (order by k.k1 asc nulls last, k.k2 asc nulls last,
                                            k.updated_at desc nulls last, k.id desc) as rn
    from keyed k
    order by k.k1 asc nulls last, k.k2 asc nulls last, k.updated_at desc nulls last, k.id desc
    limit v_limit offset v_offset
  )
  select (select c from counted),
         coalesce(jsonb_agg(jsonb_build_object(
           'id', pg.id, 'account_id', pg.account_id, 'menu_source_candidate_id', pg.menu_source_candidate_id,
           'original_menu_url', pg.original_menu_url, 'discovered_asset_url', pg.discovered_asset_url,
           'asset_kind', pg.asset_kind, 'acquisition_method', pg.acquisition_method,
           'acquisition_status', pg.acquisition_status, 'page_count', pg.page_count,
           'menu_scope', pg.menu_scope, 'page_render_status', pg.page_render_status,
           'page_rendered_at', pg.page_rendered_at, 'discovered_at', pg.discovered_at,
           'acquired_at', pg.acquired_at, 'updated_at', pg.updated_at,
           'state', pg.state, 'city', pg.city, 'venue_type', pg.venue_type,
           'accounts', jsonb_build_object('account_name', pg.account_name, 'street_address', pg.street_address,
                                          'postal_code', pg.postal_code, 'google_types', pg.google_types,
                                          'website_url', pg.website_url),
           'census', case when pg.zcta is null then null else jsonb_build_object(
                        'zcta', pg.zcta, 'total_population', pg.total_population, 'median_age', pg.median_age,
                        'median_household_income', pg.median_household_income, 'pop_21_34_pct', pg.pop_21_34_pct,
                        'households_over_100k_pct', pg.households_over_100k_pct,
                        'bachelors_or_higher_pct', pg.bachelors_or_higher_pct,
                        'hispanic_latino_pct', pg.hispanic_latino_pct) end,
           'pages', coalesce((select jsonb_agg(jsonb_build_object(
                        'id', x.id, 'page_number', x.page_number, 'render_status', x.render_status,
                        'capture_method', x.capture_method, 'width', x.width, 'height', x.height,
                        'bucket', x.page_image_bucket, 'path', x.page_image_path) order by x.page_number)
                      from public.menu_visual_pages x where x.menu_visual_document_id = pg.id), '[]'::jsonb),
           'ready_page_count', (select count(*) from public.menu_visual_pages x
                                where x.menu_visual_document_id = pg.id and x.render_status = 'ready'),
           'text_coverage', exists (select 1 from public.staging_menu_extract s
                                    where s.superseded_at is null and s.menu_page_url = pg.original_menu_url
                                      and s.item_type = 'cocktail'),
           'matched_items', case when v_text_filter then
                (select coalesce(jsonb_agg(m.item_name), '[]'::jsonb) from (
                   select distinct s.item_name
                   from public.staging_menu_extract s
                   where s.superseded_at is null and s.menu_page_url = pg.original_menu_url and s.item_type = 'cocktail'
                     and (v_cocktail   is null or s.item_name ilike '%' || public.phg_like_escape(v_cocktail) || '%')
                     and (v_ingredient is null or s.notes     ilike '%' || public.phg_like_escape(v_ingredient) || '%')
                     and (v_patterns   is null or s.notes     ilike any (v_patterns))
                   order by s.item_name limit 6) m)
              else '[]'::jsonb end
         ) order by pg.rn), '[]'::jsonb)
    into v_count, v_rows
  from pg;

  return jsonb_build_object('count', coalesce(v_count, 0), 'count_capped', false, 'rows', v_rows,
                            'limit', v_limit, 'offset', v_offset, 'sort', v_sort);
end;
$$;

create or replace function public.phg_corpus_browse_candidates(p jsonb)
returns jsonb
language plpgsql stable security definer
set search_path = public, pg_temp
as $$
declare
  v_limit      int  := least(100, greatest(1, coalesce((p->>'limit')::int, 24)));
  v_offset     int  := least(1000000, greatest(0, coalesce((p->>'offset')::int, 0)));
  v_q          text := nullif(btrim(p->>'q'), '');
  v_states     text[] := (select array_agg(upper(x)) from unnest(public.phg_jsonb_text_list(p, 'state')) x);
  v_cities     text[] := (select array_agg(upper(x)) from unnest(public.phg_jsonb_text_list(p, 'city')) x);
  v_vtypes     text[] := (select array_agg(lower(x)) from unnest(public.phg_jsonb_text_list(p, 'venue_type')) x);
  v_formats    text[] := coalesce(public.phg_jsonb_text_list(p, 'source_format'), public.phg_jsonb_text_list(p, 'asset_kind'));
  v_scopes     text[] := public.phg_jsonb_text_list(p, 'menu_scope');
  v_statuses   text[] := public.phg_jsonb_text_list(p, 'status');
  v_cocktail   text := nullif(btrim(p->>'cocktail'), '');
  v_ingredient text := nullif(btrim(p->>'ingredient'), '');
  v_preps      text[] := (select array_agg(lower(x)) from unnest(public.phg_jsonb_text_list(p, 'prep_type')) x);
  v_income     text[] := public.phg_jsonb_text_list(p, 'income');
  v_age        text[] := public.phg_jsonb_text_list(p, 'age');
  v_young      text[] := public.phg_jsonb_text_list(p, 'young');
  v_affluent   text[] := public.phg_jsonb_text_list(p, 'affluent');
  v_edu        text[] := public.phg_jsonb_text_list(p, 'edu');
  v_hisp       text[] := public.phg_jsonb_text_list(p, 'hisp');
  v_census     boolean;
  v_patterns   text[];
  v_text_filter boolean;
  v_cap        int := 5001;   -- counting 470k+ candidates exactly is the known latency hotspot
  v_count      bigint;
  v_rows       jsonb;
begin
  if v_states is not null and exists (select 1 from unnest(v_states) s where s !~ '^[A-Z]{2}$') then
    raise exception 'invalid state';
  end if;
  if v_preps is not null then
    if exists (select 1 from unnest(v_preps) x where public.phg_prep_patterns(x) is null) then
      raise exception 'unknown prep_type %', array_to_string(v_preps, ',');
    end if;
    select array_agg(distinct pat) into v_patterns
      from unnest(v_preps) x, unnest(public.phg_prep_patterns(x)) pat;
  end if;
  perform public.phg_census_check_bands('income', v_income);
  perform public.phg_census_check_bands('age', v_age);
  perform public.phg_census_check_bands('young', v_young);
  perform public.phg_census_check_bands('affluent', v_affluent);
  perform public.phg_census_check_bands('edu', v_edu);
  perform public.phg_census_check_bands('hisp', v_hisp);
  v_census := (v_income is not null or v_age is not null or v_young is not null
               or v_affluent is not null or v_edu is not null or v_hisp is not null);
  v_text_filter := (v_cocktail is not null or v_ingredient is not null or v_patterns is not null);

  -- NOT MATERIALIZED: base is referenced twice (capped count + page). Materialized, it built all
  -- ~545k joined rows before counting (6.2 s in v3, 15 s with the census join); inlined, the count
  -- stops at 5,001 rows and the page walks the primary key backwards.
  with base as not materialized (
    select c.id, c.account_id, c.source_url, c.menu_type, c.source_format, c.discovery_method,
           c.discovery_confidence, c.status, c.is_food_only, c.first_discovered_at, c.last_seen_at,
           c.item_count, c.menu_scope, c.page_count, c.visual_asset_status, c.visual_asset_method,
           c.visual_asset_url, c.visual_document_id, c.screenshot_pages_ready,
           a.account_name, a.street_address, a.postal_code, a.google_types, a.website_url,
           public.account_state(a.account_id)           as state,
           substring(a.notes from 'City: ([^.]+)')      as city,
           coalesce(a.google_types[1], a.format_code)   as venue_type,
           z.zcta, z.total_population, z.median_age, z.median_household_income, z.pop_21_34_pct,
           z.households_over_100k_pct, z.bachelors_or_higher_pct, z.hispanic_latino_pct
    from public.menu_source_candidates c
    join public.accounts a on a.account_id = c.account_id
    left join public.phg_census_zcta z on z.zcta = left(a.postal_code, 5)
    where (v_formats  is null or c.source_format = any (v_formats))
      and (v_scopes   is null or c.menu_scope = any (v_scopes))
      and (v_statuses is null or c.status = any (v_statuses))
      and (v_q        is null or a.account_name ilike '%' || public.phg_like_escape(v_q) || '%')
      and (v_states   is null or public.account_state(a.account_id) = any (v_states))
      and (v_cities   is null or upper(btrim(substring(a.notes from 'City: ([^.]+)'))) = any (v_cities))
      and (v_vtypes   is null
           or lower(coalesce(a.google_types[1], a.format_code)) = any (v_vtypes)
           or exists (select 1 from unnest(coalesce(a.google_types, '{}'::text[])) t where lower(t) = any (v_vtypes)))
      and (not v_census or (
               (v_income   is null or public.phg_census_band('income',   z.median_household_income)  = any (v_income))
           and (v_age      is null or public.phg_census_band('age',      z.median_age)               = any (v_age))
           and (v_young    is null or public.phg_census_band('young',    z.pop_21_34_pct)            = any (v_young))
           and (v_affluent is null or public.phg_census_band('affluent', z.households_over_100k_pct) = any (v_affluent))
           and (v_edu      is null or public.phg_census_band('edu',      z.bachelors_or_higher_pct)  = any (v_edu))
           and (v_hisp     is null or public.phg_census_band('hisp',     z.hispanic_latino_pct)      = any (v_hisp))))
      and (not v_text_filter
           or exists (select 1 from public.staging_menu_extract s
                      where s.superseded_at is null
                        and s.menu_page_url = c.source_url
                        and s.item_type = 'cocktail'
                        and (v_cocktail   is null or s.item_name ilike '%' || public.phg_like_escape(v_cocktail) || '%')
                        and (v_ingredient is null or s.notes     ilike '%' || public.phg_like_escape(v_ingredient) || '%')
                        and (v_patterns   is null or s.notes     ilike any (v_patterns))))
  ),
  counted as (select count(*) as c from (select 1 from base limit v_cap) z),
  pg as (
    select b.* from base b
    order by b.id desc            -- newest discovered first; pkey-ordered so no 470k-row sort per request
    limit v_limit offset v_offset
  )
  select (select c from counted),
         coalesce(jsonb_agg(jsonb_build_object(
           'id', pg.id, 'account_id', pg.account_id, 'source_url', pg.source_url, 'menu_type', pg.menu_type,
           'source_format', pg.source_format, 'discovery_method', pg.discovery_method,
           'discovery_confidence', pg.discovery_confidence, 'status', pg.status, 'is_food_only', pg.is_food_only,
           'first_discovered_at', pg.first_discovered_at, 'last_seen_at', pg.last_seen_at,
           'item_count', pg.item_count, 'menu_scope', pg.menu_scope, 'page_count', pg.page_count,
           'visual_asset_status', pg.visual_asset_status, 'visual_asset_method', pg.visual_asset_method,
           'visual_asset_url', pg.visual_asset_url, 'visual_document_id', pg.visual_document_id,
           'screenshot_pages_ready', pg.screenshot_pages_ready,
           'state', pg.state, 'city', pg.city, 'venue_type', pg.venue_type,
           'accounts', jsonb_build_object('account_name', pg.account_name, 'street_address', pg.street_address,
                                          'postal_code', pg.postal_code, 'google_types', pg.google_types,
                                          'website_url', pg.website_url),
           'census', case when pg.zcta is null then null else jsonb_build_object(
                        'zcta', pg.zcta, 'total_population', pg.total_population, 'median_age', pg.median_age,
                        'median_household_income', pg.median_household_income, 'pop_21_34_pct', pg.pop_21_34_pct,
                        'households_over_100k_pct', pg.households_over_100k_pct,
                        'bachelors_or_higher_pct', pg.bachelors_or_higher_pct,
                        'hispanic_latino_pct', pg.hispanic_latino_pct) end,
           'text_coverage', exists (select 1 from public.staging_menu_extract s
                                    where s.superseded_at is null and s.menu_page_url = pg.source_url
                                      and s.item_type = 'cocktail')
         ) order by pg.id desc), '[]'::jsonb)
    into v_count, v_rows
  from pg;

  return jsonb_build_object('count', coalesce(v_count, 0), 'count_capped', coalesce(v_count, 0) >= v_cap,
                            'rows', v_rows, 'limit', v_limit, 'offset', v_offset, 'sort', 'recent');
end;
$$;

-- Vocabularies for the gallery's dropdowns, derived from real data (not literals), now with every
-- city (with its state), census bands with document counts, sort options and page sizes.
create or replace function public.phg_corpus_filter_values()
returns jsonb
language sql stable security definer
set search_path = public, pg_temp
as $$
  with docs as (
    select d.id, d.asset_kind, d.menu_scope, d.page_render_status,
           public.account_state(a.account_id) as state,
           upper(btrim(substring(a.notes from 'City: ([^.]+)'))) as city,
           lower(coalesce(a.google_types[1], a.format_code)) as venue_type,
           z.zcta, z.median_household_income, z.median_age, z.pop_21_34_pct,
           z.households_over_100k_pct, z.bachelors_or_higher_pct, z.hispanic_latino_pct
    from public.menu_visual_documents d
    join public.accounts a on a.account_id = d.account_id
    left join public.phg_census_zcta z on z.zcta = left(a.postal_code, 5)
  ),
  cat as (select public.phg_census_band_catalog() as c),
  metric_bands as (
    select m.metric, public.phg_census_band(m.metric,
             case m.metric when 'income'   then d.median_household_income
                           when 'age'      then d.median_age
                           when 'young'    then d.pop_21_34_pct
                           when 'affluent' then d.households_over_100k_pct
                           when 'edu'      then d.bachelors_or_higher_pct
                           when 'hisp'     then d.hispanic_latino_pct end) as band
    from docs d cross join (values ('income'),('age'),('young'),('affluent'),('edu'),('hisp')) as m(metric)
  ),
  band_counts as (select metric, band, count(*) as n from metric_bands group by 1, 2)
  select jsonb_build_object(
    'states',      (select coalesce(jsonb_agg(jsonb_build_object('v', state, 'n', n) order by n desc), '[]'::jsonb)
                    from (select state, count(*) n from docs where state is not null group by 1) s),
    'cities',      (select coalesce(jsonb_agg(jsonb_build_object('v', city, 'st', state, 'n', n) order by n desc, city), '[]'::jsonb)
                    from (select city, state, count(*) n from docs where city is not null and city <> ''
                          group by 1, 2 order by 3 desc, 1 limit 2500) s),
    'venue_types', (select coalesce(jsonb_agg(jsonb_build_object('v', venue_type, 'n', n) order by n desc), '[]'::jsonb)
                    from (select venue_type, count(*) n from docs where venue_type is not null group by 1 order by 2 desc limit 80) s),
    'asset_kinds', (select coalesce(jsonb_agg(jsonb_build_object('v', asset_kind, 'n', n) order by n desc), '[]'::jsonb)
                    from (select asset_kind, count(*) n from docs where asset_kind is not null group by 1) s),
    'menu_scopes', (select coalesce(jsonb_agg(jsonb_build_object('v', menu_scope, 'n', n) order by n desc), '[]'::jsonb)
                    from (select menu_scope, count(*) n from docs where menu_scope is not null group by 1) s),
    'render_statuses', (select coalesce(jsonb_agg(jsonb_build_object('v', page_render_status, 'n', n) order by n desc), '[]'::jsonb)
                    from (select page_render_status, count(*) n from docs where page_render_status is not null group by 1) s),
    'candidate_statuses', (select coalesce(jsonb_agg(jsonb_build_object('v', status, 'n', n) order by n desc), '[]'::jsonb)
                    from (select status, count(*) n from public.menu_source_candidates group by 1) s),
    'candidate_formats', (select coalesce(jsonb_agg(jsonb_build_object('v', source_format, 'n', n) order by n desc), '[]'::jsonb)
                    from (select source_format, count(*) n from public.menu_source_candidates group by 1) s),
    'candidate_scopes', (select coalesce(jsonb_agg(jsonb_build_object('v', menu_scope, 'n', n) order by n desc), '[]'::jsonb)
                    from (select menu_scope, count(*) n from public.menu_source_candidates group by 1) s),
    'prep_types', to_jsonb(array['syrup','infusion','cordial','shrub','puree','bitters','citrus','garnish','foam','tincture','saline','tea','coffee']),
    'census', (select jsonb_object_agg(m.metric, jsonb_build_object(
                  'label', cat.c -> m.metric ->> 'label',
                  'long',  cat.c -> m.metric ->> 'long',
                  'bands', (select jsonb_agg((e.b) || jsonb_build_object('n', coalesce(bc.n, 0)) order by e.ord)
                              from jsonb_array_elements(cat.c -> m.metric -> 'bands') with ordinality as e(b, ord)
                              left join band_counts bc on bc.metric = m.metric and bc.band = e.b ->> 'v')))
               from cat, (values ('income'),('age'),('young'),('affluent'),('edu'),('hisp')) as m(metric)),
    'census_coverage', jsonb_build_object(
        'documents_with_census', (select count(*) from docs where zcta is not null),
        'documents_total', (select count(*) from docs),
        'source', 'US Census ACS 2020–2024 5-year estimates by ZIP Code Tabulation Area (via Census Reporter)'),
    'sorts', jsonb_build_array(
        jsonb_build_object('v','recent','label','Newest'), jsonb_build_object('v','name','label','Venue A–Z'),
        jsonb_build_object('v','city','label','City A–Z'), jsonb_build_object('v','income_desc','label','Income high–low'),
        jsonb_build_object('v','income_asc','label','Income low–high'), jsonb_build_object('v','age_asc','label','Youngest area'),
        jsonb_build_object('v','age_desc','label','Oldest area'), jsonb_build_object('v','young_desc','label','Most 21–34'),
        jsonb_build_object('v','affluent_desc','label','Most $100k+ homes'), jsonb_build_object('v','edu_desc','label','Most degrees'),
        jsonb_build_object('v','hisp_desc','label','Most Hispanic')),
    'page_sizes', jsonb_build_array(20, 50, 100),
    'text_coverage', jsonb_build_object(
        'documents_with_cocktail_text', (select count(distinct d.id) from public.menu_visual_documents d
                                         where exists (select 1 from public.staging_menu_extract s
                                                       where s.superseded_at is null and s.menu_page_url = d.original_menu_url
                                                         and s.item_type = 'cocktail')),
        'documents_total', (select count(*) from public.menu_visual_documents)),
    'generated_at', now()
  );
$$;

-- Cached vocabularies: computing them scans all candidates and the text links (~5 s). The Edge
-- function reads this; a stale cache (older than p_max_age seconds) is recomputed by one caller
-- while concurrent callers get the previous payload instead of piling up.
create table if not exists public.phg_corpus_filter_cache (
  id            int primary key default 1 check (id = 1),
  payload       jsonb not null,
  generated_at  timestamptz not null default now(),
  duration_ms   integer
);
alter table public.phg_corpus_filter_cache enable row level security;
revoke all on public.phg_corpus_filter_cache from anon, authenticated;

create or replace function public.phg_corpus_filter_values_cached(p_max_age integer default 900)
returns jsonb
language plpgsql volatile security definer
set search_path = public, pg_temp
as $$
declare
  v_row  public.phg_corpus_filter_cache;
  v_t0   timestamptz;
  v_new  jsonb;
begin
  select * into v_row from public.phg_corpus_filter_cache where id = 1;
  if found and v_row.generated_at > now() - make_interval(secs => greatest(30, least(86400, coalesce(p_max_age, 900)))) then
    return v_row.payload || jsonb_build_object('cached', true, 'cache_age_s', round(extract(epoch from now() - v_row.generated_at)));
  end if;
  if found and not pg_try_advisory_xact_lock(830927, 6) then
    return v_row.payload || jsonb_build_object('cached', true, 'stale', true);
  end if;
  v_t0 := clock_timestamp();
  v_new := public.phg_corpus_filter_values();
  insert into public.phg_corpus_filter_cache as c (id, payload, generated_at, duration_ms)
  values (1, v_new, now(), round(extract(epoch from clock_timestamp() - v_t0) * 1000))
  on conflict (id) do update set payload = excluded.payload, generated_at = excluded.generated_at, duration_ms = excluded.duration_ms;
  return v_new || jsonb_build_object('cached', false);
end;
$$;

revoke execute on function public.phg_jsonb_text_list(jsonb, text)        from public, anon, authenticated;
revoke execute on function public.phg_census_band(text, numeric)          from public, anon, authenticated;
revoke execute on function public.phg_census_band_catalog()               from public, anon, authenticated;
revoke execute on function public.phg_census_check_bands(text, text[])    from public, anon, authenticated;
revoke execute on function public.phg_corpus_browse_documents(jsonb)      from public, anon, authenticated;
revoke execute on function public.phg_corpus_browse_candidates(jsonb)     from public, anon, authenticated;
revoke execute on function public.phg_corpus_filter_values()              from public, anon, authenticated;
revoke execute on function public.phg_corpus_filter_values_cached(integer) from public, anon, authenticated;
grant  execute on function public.phg_jsonb_text_list(jsonb, text)        to service_role;
grant  execute on function public.phg_census_band(text, numeric)          to service_role;
grant  execute on function public.phg_census_band_catalog()               to service_role;
grant  execute on function public.phg_census_check_bands(text, text[])    to service_role;
grant  execute on function public.phg_corpus_browse_documents(jsonb)      to service_role;
grant  execute on function public.phg_corpus_browse_candidates(jsonb)     to service_role;
grant  execute on function public.phg_corpus_filter_values()              to service_role;
grant  execute on function public.phg_corpus_filter_values_cached(integer) to service_role;

comment on function public.phg_corpus_browse_documents(jsonb)  is 'PHG gallery v2: paginated visual documents; multi-select venue/format/scope/status, census (ZIP ACS) bands, text/prep filters, sort; limit 1..100. Service-role only.';
comment on function public.phg_corpus_browse_candidates(jsonb) is 'PHG gallery v2: paginated discovery candidates; same filters as documents (no sort); count capped at 5001. Service-role only.';
comment on function public.phg_corpus_filter_values()          is 'PHG gallery v2: real filter vocabularies with counts, all cities with state, census bands with counts, sorts, page sizes. Service-role only.';
