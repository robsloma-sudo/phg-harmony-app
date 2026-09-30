-- Applied live 2026-09-30.
-- 1) Geocode cron: every 5 min, one geocode-licenses call per state that still has pending rows (1,000 rows each,
--    PostgREST row cap). kick_geocode is a no-op when nothing is pending, so the job stays on for new licences.
select cron.schedule('phg-license-geocode', '*/5 * * * *', $$SET statement_timeout='60s'; SELECT phg_license.kick_geocode(1000);$$);

-- 2) OR address repair. The loader's "strip city + OR + zip" regex was greedy ([A-Z .'-]+) and ate the street name,
--    leaving only the house number ("1525" for "1525 GEARY ST SE ALBANY OR 97322"). Rebuilt from raw.physical_address
--    (drop "OR zip", then the known city) and re-queued for geocoding. Loader fixed in ingest-state-licenses.
with x as (select license_no, city, address old,
  btrim(regexp_replace(raw->>'physical_address', '\s+OR\s+\d{5}(-\d{0,4})?\s*$', '', 'i'), ' ,') a1
  from phg_license.licenses where state='OR' and coalesce(raw->>'physical_address','')<>''),
y as (select license_no, old, case when upper(a1) like '% '||upper(city) and length(a1)>length(city)+3
            then btrim(left(a1, length(a1)-length(city)), ' ,') else a1 end fixed from x)
update phg_license.licenses l set address=y.fixed, lat=null, lng=null, geocoded_at=null, geocode_match=null
  from y where l.state='OR' and l.license_no=y.license_no and y.fixed is distinct from y.old and y.fixed<>'';

-- 3) Source-probe helper for the temporary probe-licence-sources function (allowlisted state agency hosts only).
create or replace function phg_license._probe(p jsonb) returns bigint language sql security definer set search_path=public as $$
 select net.http_post(url:='https://lqjtwabzmgjcufftuqvu.supabase.co/functions/v1/probe-licence-sources',
 headers:=jsonb_build_object('Content-Type','application/json','x-ingest-token',(select value from public.internal_secrets where key='ingest_token')),
 body:=p, timeout_milliseconds:=70000) $$;
revoke all on function phg_license._probe(jsonb) from public, anon, authenticated;
