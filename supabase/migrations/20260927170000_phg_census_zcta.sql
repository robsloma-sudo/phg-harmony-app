-- PHG census by ZIP (ZCTA), ACS 5-year 2020-2024, for the Menu Library census filters (PHG-027).
-- Only Iowa had census data (place/county, from the bulk summary files). Every menu document has a
-- 5-digit ZIP, so ZIP-level (ZIP Code Tabulation Area) data covers IA, CO and NY uniformly.
-- Data is fetched from api.census.gov by the database (pg_net), parsed from the stored response.
-- Service-role only. Nothing existing is changed.

create table if not exists public.phg_census_zcta (
  zcta                      text primary key check (zcta ~ '^[0-9]{5}$'),
  acs_vintage               text not null default '2020-2024',
  total_population          integer,
  median_age                numeric(5,1),
  median_household_income   integer,
  pop_21_34_pct             numeric(5,1),
  households_over_100k_pct  numeric(5,1),
  bachelors_or_higher_pct   numeric(5,1),
  hispanic_latino_pct       numeric(5,1),
  raw                       jsonb not null default '{}'::jsonb,
  retrieved_at              timestamptz not null default now()
);
alter table public.phg_census_zcta enable row level security;
revoke all on public.phg_census_zcta from anon, authenticated;
comment on table public.phg_census_zcta is
  'ACS 2020-2024 5-year estimates by ZIP Code Tabulation Area (api.census.gov). Joined to venues by accounts.postal_code. Percentages 0-100; medians null when the Census suppresses them.';

create table if not exists public.phg_census_fetch (
  part          text primary key,
  url           text not null,
  request_id    bigint,
  requested_at  timestamptz,
  loaded_at     timestamptz,
  rows_loaded   integer,
  error         text
);
alter table public.phg_census_fetch enable row level security;
revoke all on public.phg_census_fetch from anon, authenticated;

-- Merge one fetched part (a JSON array of arrays, first row = header) into phg_census_zcta.raw.
create or replace function public.phg_census_zcta_apply(p_part text)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_req    bigint;
  v_status int;
  v_body   text;
  v_err    text;
  v_rows   integer;
begin
  select request_id into v_req from public.phg_census_fetch where part = p_part;
  if v_req is null then raise exception 'part % not requested', p_part; end if;
  select r.status_code, r.content, coalesce(r.error_msg, case when r.timed_out then 'timed out' end)
    into v_status, v_body, v_err
    from net._http_response r where r.id = v_req;
  if not found then raise exception 'response for part % not ready', p_part; end if;
  if v_status is distinct from 200 or v_body is null or left(btrim(v_body), 1) <> '[' then
    update public.phg_census_fetch
       set error = coalesce(v_err, 'http ' || coalesce(v_status::text, '?') || ': ' || left(coalesce(v_body, ''), 200))
     where part = p_part;
    return 0;
  end if;

  with arr as (select v_body::jsonb as a),
  hdr as (select array_agg(h order by i) as cols from arr, jsonb_array_elements_text(arr.a -> 0) with ordinality as t(h, i)),
  body as (
    select r.value as row_arr
      from arr, jsonb_array_elements(arr.a) with ordinality as r(value, i)
     where r.i > 1
  ),
  objs as (
    select (select jsonb_object_agg(hdr.cols[k], b.row_arr ->> (k - 1))
              from generate_subscripts(hdr.cols, 1) as k
             where hdr.cols[k] not in ('zip code tabulation area', 'NAME')) as obj,
           b.row_arr ->> (array_position(hdr.cols, 'zip code tabulation area') - 1) as zcta
      from body b, hdr
  )
  insert into public.phg_census_zcta as z (zcta, raw, retrieved_at)
  select zcta, obj, now() from objs where zcta ~ '^[0-9]{5}$'
  on conflict (zcta) do update set raw = z.raw || excluded.raw, retrieved_at = now();
  get diagnostics v_rows = row_count;

  update public.phg_census_fetch set loaded_at = now(), rows_loaded = v_rows, error = null where part = p_part;
  return v_rows;
end;
$$;
revoke all on function public.phg_census_zcta_apply(text) from public, anon, authenticated;

-- Recompute the metric columns from raw. Census sentinels (negative values) mean suppressed -> null.
create or replace function public.phg_census_zcta_compute()
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare v_rows integer;
begin
  with v as (
    select z.zcta,
      nullif(greatest((z.raw ->> 'B01001_001E')::numeric, -1), -1) as pop,
      (z.raw ->> 'B01002_001E')::numeric as med_age,
      (z.raw ->> 'B19013_001E')::numeric as med_inc,
      ( coalesce((z.raw->>'B01001_009E')::numeric,0) + coalesce((z.raw->>'B01001_010E')::numeric,0)
      + coalesce((z.raw->>'B01001_011E')::numeric,0) + coalesce((z.raw->>'B01001_012E')::numeric,0)
      + coalesce((z.raw->>'B01001_033E')::numeric,0) + coalesce((z.raw->>'B01001_034E')::numeric,0)
      + coalesce((z.raw->>'B01001_035E')::numeric,0) + coalesce((z.raw->>'B01001_036E')::numeric,0)) as a21_34,
      nullif((z.raw ->> 'B19001_001E')::numeric, 0) as hh,
      ( coalesce((z.raw->>'B19001_014E')::numeric,0) + coalesce((z.raw->>'B19001_015E')::numeric,0)
      + coalesce((z.raw->>'B19001_016E')::numeric,0) + coalesce((z.raw->>'B19001_017E')::numeric,0)) as hh100,
      nullif((z.raw ->> 'B15003_001E')::numeric, 0) as ed_base,
      ( coalesce((z.raw->>'B15003_022E')::numeric,0) + coalesce((z.raw->>'B15003_023E')::numeric,0)
      + coalesce((z.raw->>'B15003_024E')::numeric,0) + coalesce((z.raw->>'B15003_025E')::numeric,0)) as ba,
      nullif((z.raw ->> 'B03003_001E')::numeric, 0) as hisp_base,
      (z.raw ->> 'B03003_003E')::numeric as hisp
    from public.phg_census_zcta z
  )
  update public.phg_census_zcta t set
    total_population         = v.pop::int,
    median_age               = case when v.med_age >= 0 then round(v.med_age, 1) end,
    median_household_income  = case when v.med_inc >= 0 then v.med_inc::int end,
    pop_21_34_pct            = case when v.pop > 0 and (t.raw ? 'B01001_009E') then round(100 * v.a21_34 / v.pop, 1) end,
    households_over_100k_pct = case when v.hh > 0 and (t.raw ? 'B19001_014E') then round(100 * v.hh100 / v.hh, 1) end,
    bachelors_or_higher_pct  = case when v.ed_base > 0 and (t.raw ? 'B15003_022E') then round(100 * v.ba / v.ed_base, 1) end,
    hispanic_latino_pct      = case when v.hisp_base > 0 and v.hisp >= 0 then round(100 * v.hisp / v.hisp_base, 1) end
  from v where v.zcta = t.zcta;
  get diagnostics v_rows = row_count;
  return v_rows;
end;
$$;
revoke all on function public.phg_census_zcta_compute() from public, anon, authenticated;

-- ---------------------------------------------------------------------------------------------
-- Applied as migration phg_census_zcta_censusreporter (2026-09-27 ~17:10Z).
-- api.census.gov now answers "Missing Key" for these queries and no Census key is stored, so the
-- same ACS 2024 5-year tables are read from Census Reporter (api.censusreporter.org), which
-- republishes the Census Bureau's ACS tables without a key. Release is checked (acs2024_5yr).
-- Load (9 pg_net requests, one per state x table group):
--   table groups: B01001,B01002 | B19013,B19001 | B15003,B03003
--   geo_ids=860|04000US19 (IA), 860|04000US08 (CO), 860|04000US36 (NY)
--   then: select public.phg_census_zcta_apply_cr(part, <state>) per part; select public.phg_census_zcta_compute();
-- Result 2026-09-27: 3,326 ZCTAs (IA 972, CO 530, NY 1,824); menu documents matched by ZIP:
--   CO 8,530/8,561, IA 3,507/3,509, NY 5,259/5,288.
alter table public.phg_census_zcta add column if not exists source text not null default 'api.censusreporter.org acs2024_5yr';
alter table public.phg_census_zcta add column if not exists state text;

create or replace function public.phg_census_zcta_apply_cr(p_part text, p_state text)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_req    bigint;
  v_status int;
  v_body   text;
  v_err    text;
  v_rel    text;
  v_rows   integer;
begin
  if p_state !~ '^[A-Z]{2}$' then raise exception 'invalid state'; end if;
  select request_id into v_req from public.phg_census_fetch where part = p_part;
  if v_req is null then raise exception 'part % not requested', p_part; end if;
  select r.status_code, r.content, coalesce(r.error_msg, case when r.timed_out then 'timed out' end)
    into v_status, v_body, v_err
    from net._http_response r where r.id = v_req;
  if not found then raise exception 'response for part % not ready', p_part; end if;
  if v_status is distinct from 200 or v_body is null or left(btrim(v_body), 1) <> '{' or (v_body::jsonb -> 'data') is null then
    update public.phg_census_fetch
       set error = coalesce(v_err, 'http ' || coalesce(v_status::text, '?') || ': ' || left(coalesce(v_body, ''), 300))
     where part = p_part;
    return 0;
  end if;
  v_rel := v_body::jsonb -> 'release' ->> 'id';
  if v_rel is distinct from 'acs2024_5yr' then
    update public.phg_census_fetch set error = 'unexpected release ' || coalesce(v_rel, 'null') where part = p_part;
    return 0;
  end if;

  with d as (select v_body::jsonb -> 'data' as data),
  kv as (
    select substring(g.geo from '^86000US([0-9]{5})$') as zcta,
           t.tbl || '_' || right(e.col, 3) || 'E' as k,
           e.val as v
      from d, jsonb_each(d.data) as g(geo, tables),
           jsonb_each(g.tables) as t(tbl, obj),
           jsonb_each(t.obj -> 'estimate') as e(col, val)
     where g.geo ~ '^86000US[0-9]{5}$' and length(e.col) = 9
  ),
  objs as (select zcta, jsonb_object_agg(k, v) as obj from kv group by zcta)
  insert into public.phg_census_zcta as z (zcta, state, raw, retrieved_at, source)
  select zcta, p_state, obj, now(), 'api.censusreporter.org acs2024_5yr' from objs
  on conflict (zcta) do update set raw = z.raw || excluded.raw, state = coalesce(z.state, excluded.state), retrieved_at = now();
  get diagnostics v_rows = row_count;

  update public.phg_census_fetch set loaded_at = now(), rows_loaded = v_rows, error = null where part = p_part;
  return v_rows;
end;
$$;
revoke all on function public.phg_census_zcta_apply_cr(text, text) from public, anon, authenticated;
