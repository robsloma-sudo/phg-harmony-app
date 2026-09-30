-- PHG licence geocoding with the free US Census batch geocoder (no key, no paid service).
--   phg_license.licenses + geocoded_at timestamptz, geocode_match text ('Match' / 'No_Match' / 'Tie' / 'Match:Exact' ...)
--   public.phg_license_geocode_batch(p_state, p_limit)  -> rows with an address that still need geocoding
--                                                          (lat is null and geocoded_at is null); street is cleaned of a
--                                                          trailing "ST 12345[-6789]" and of the known city.
--   public.phg_license_geocode_apply(p jsonb)            -> sets lat/lng/geocode_match/geocoded_at; fills zip and city from
--                                                          the matched address ONLY when they are empty. No_Match/Tie rows
--                                                          get geocoded_at = now() so they are not retried forever.
--   phg_license.kick_geocode(p_limit)                     -> pg_cron helper: one small edge-function call per state with
--                                                          pending rows (geocode-licenses, x-ingest-token auth).
-- apply also calls phg_license.refresh_state_stats(state) for the states it changed.
-- Both RPCs are service_role only (called by supabase/functions/geocode-licenses).

alter table phg_license.licenses add column if not exists geocoded_at timestamptz;
alter table phg_license.licenses add column if not exists geocode_match text;

create index if not exists licenses_geocode_pending on phg_license.licenses (state, license_no)
  where lat is null and geocoded_at is null;

drop function if exists public.phg_license_geocode_batch(text, int);
create or replace function public.phg_license_geocode_batch(p_state text, p_limit int default 2500)
returns table (state text, license_no text, street text, city text, st text, zip text)
language sql stable security definer
set search_path = phg_license, public, pg_temp
as $$
  with b as (
    select l.state, l.license_no, l.city, l.zip,
           regexp_replace(btrim(l.address), '\s+', ' ', 'g') a0
      from phg_license.licenses l
     where l.state = upper(p_state) and l.lat is null and l.geocoded_at is null
       and coalesce(btrim(l.address), '') <> ''
     order by l.license_no
     limit greatest(1, least(coalesce(p_limit, 2500), 10000))
  ), c as (
    -- a trailing "ST 12345[-6789]" is dropped from the street; its state code is used (ME lists out-of-state holders)
    select b.*, x.st2,
           case when x.st2 is not null then btrim(regexp_replace(b.a0, '[\s,]+[A-Za-z]{2}[\s,]+\d{5}(-?\d{4})?$', ''), ' ,') else b.a0 end a
      from b
      cross join lateral (select nullif(upper(substring(b.a0 from '[\s,]([A-Za-z]{2})[\s,]+\d{5}(?:-?\d{4})?$')), '') s0) y
      cross join lateral (select case when y.s0 = any('{AL,AK,AZ,AR,CA,CO,CT,DE,DC,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY,PR}'::text[]) then y.s0 end st2) x)
  select c.state, c.license_no,
         case when coalesce(c.city, '') <> '' and upper(c.a) like '% ' || upper(c.city)
                   and length(c.a) > length(c.city) + 3
              then btrim(left(c.a, length(c.a) - length(c.city)), ' ,')
              else c.a end,
         c.city, coalesce(c.st2, c.state), c.zip
    from c;
$$;

create or replace function public.phg_license_geocode_apply(p jsonb)
returns jsonb
language plpgsql security definer
set search_path = phg_license, public, pg_temp
as $$
declare res jsonb; n int;
begin
  create temp table if not exists _geo_in (state text, license_no text, match text, lat double precision, lng double precision, city text, zip text) on commit drop;
  truncate _geo_in;
  insert into _geo_in
  select x.state, x.license_no, x.match, x.lat, x.lng, nullif(btrim(x.city), ''), nullif(btrim(x.zip), '')
    from jsonb_to_recordset(p) as x(state text, license_no text, match text, lat double precision, lng double precision, city text, zip text);

  select jsonb_build_object(
           'zip_filled',  count(*) filter (where coalesce(btrim(l.zip), '') = ''  and r.match like 'Match%' and r.zip ~ '^\d{5}$'),
           'city_filled', count(*) filter (where coalesce(btrim(l.city), '') = '' and r.match like 'Match%' and r.city is not null))
    into res
    from _geo_in r join phg_license.licenses l on l.state = r.state and l.license_no = r.license_no;

  update phg_license.licenses l
     set lat = case when r.match like 'Match%' then r.lat else l.lat end,
         lng = case when r.match like 'Match%' then r.lng else l.lng end,
         geocode_match = r.match,
         geocoded_at = now(),
         zip  = case when coalesce(btrim(l.zip), '') = ''  and r.match like 'Match%' and r.zip ~ '^\d{5}$' then r.zip else l.zip end,
         city = case when coalesce(btrim(l.city), '') = '' and r.match like 'Match%' and r.city is not null then r.city else l.city end
    from _geo_in r
   where l.state = r.state and l.license_no = r.license_no;
  get diagnostics n = row_count;
  if n > 0 then
    perform phg_license.refresh_state_stats(s) from (select distinct state s from _geo_in) d;
  end if;
  return res || jsonb_build_object('updated', n);
end $$;

create or replace function phg_license.kick_geocode(p_limit int default 200)
returns int
language plpgsql security definer
set search_path = phg_license, public, pg_temp
as $$
declare s text; n int := 0;
begin
  for s in select distinct l.state from phg_license.licenses l
            where l.lat is null and l.geocoded_at is null and coalesce(btrim(l.address), '') <> '' loop
    perform net.http_post(
      url := 'https://lqjtwabzmgjcufftuqvu.supabase.co/functions/v1/geocode-licenses',
      headers := jsonb_build_object('Content-Type', 'application/json',
                   'x-ingest-token', (select value from public.internal_secrets where key = 'ingest_token')),
      body := jsonb_build_object('state', s, 'limit', p_limit),
      timeout_milliseconds := 150000);
    n := n + 1;
  end loop;
  return n;
end $$;

revoke all on function public.phg_license_geocode_batch(text, int) from public, anon, authenticated;
revoke all on function public.phg_license_geocode_apply(jsonb) from public, anon, authenticated;
revoke all on function phg_license.kick_geocode(int) from public, anon, authenticated;
grant execute on function public.phg_license_geocode_batch(text, int) to service_role;
grant execute on function public.phg_license_geocode_apply(jsonb) to service_role;
