-- PHG-051 (2026-09-29): market explorer v2 - fresh data, live rows only, ZIP census, non-blocking refreshes.
-- ROUND 2 (after safety review round 1 = 68, handoff/reviews/PHG-051_REVIEW_LOG.md). Changes are marked [R2 Bn/Sn].
--
-- Problem: mv_drink_explorer (+ mv_dash_pins and the 4 MVs built on them) were last refreshed 2026-09-25 21:10 UTC;
-- cron 8 (refresh_explorer) is paused because its two NON-concurrent refreshes lock every reader for minutes
-- (PHG-018, iPhone-login 504s). The base view reads all 1.1 M staging rows (including 765 k superseded duplicates and
-- old prices, PHG-026) and joins income / median age only at city level (geography_demographics = Iowa only), so CO and
-- NY have 0% census coverage although phg_census_zcta covers 99.6% of their venues by postal code.
--
-- Live facts gathered for round 2 (2026-09-29 ~16:00 UTC):
--   * Round-1 build (cron job 25) failed after ~8 min exactly on review blocker B1: unique index mv_mdvp_next_key,
--     duplicate venue_key (ilili|new york|NY). A re-run started (the failed transaction had rolled back the
--     unschedule) and was cancelled (pg_cancel_backend); job 25 no longer exists; no *_next MV exists.
--   * B3 gate: pg_depend shows NO dependents of the six MVs outside the chain itself (only mv_drink_explorer ->
--     mv_dash_breakdown/filters/pins/sections/menu_dev_venue_profile) and no functions bound to them.
--   * S3: today menu_item_cocktail_core.staging_menu_extract_id, (upper(city), state) demographics and zcta are all
--     unique (0 duplicates each); v2 still enforces one row per staging row by construction (LATERAL ... LIMIT 1).
--
-- Design:
--   PART A  v_public_drink_explorer_v2: the 23 live columns in the same order + staging_id (unique by construction),
--           live staging rows only (superseded_at is null), census = city demographics, else the venue ZIP
--           (phg_census_zcta). [R2 S2] venue tie-break by account_id. [R2 S3] lateral LIMIT 1 joins.
--   PART B  phg_explorer_build_next(): builds mv_*_next copies of all six MVs with UNIQUE indexes (every future
--           refresh CONCURRENT). [R2 B1] venue profile grouped by venue_key. [R2 S4] pins keyed by md5 of the row +
--           row_number within equal rows. [R2 S5] _next MVs are not readable by anon/authenticated before the swap.
--           [R2 S10] advisory lock. Runs as a one-off pg_cron job that unschedules itself in its own transaction.
--   PART C  phg_explorer_swap_next(): [R2 B2] lock_timeout 300 ms + statement_timeout 3 s (a busy reader makes the
--           swap fail fast and change nothing; retry at a quiet time); [R2 S5] SELECT grants copied from the old ACL,
--           old copies revoked from anon/authenticated; [R2 S8] index names moved with the MVs; [R2 S6] NOTIFY pgrst;
--           [R2] OIDs logged in phg_explorer_swap_log. phg_explorer_swap_back() reverses all of it. [R2 B4] rehearsal:
--           swap -> checks -> swap_back inside a DO block that ends in RAISE EXCEPTION (nothing kept).
--   PART D  [R2 S1] procedure refresh_explorer_v2(): one COMMIT per concurrent refresh, no stats functions inside
--           (refresh_state_stats stays on job 5). Cron 8 switched only after one timed manual CALL.
--   ROLLBACK of A/B: drop the six *_next MVs, the v2 view and the two functions (nothing live depends on them).
-- Known limit to fix in the app before the swap (S7/S9): index.html getAll() stops at 40 pages x 1,000 rows per state
-- and pages without ORDER BY; the v2 explorer may exceed 40,000 rows in a state. The pre-swap gate reports per-state
-- counts; if any state is over the cap, the app change (explicit columns, order=staging_id, higher cap or aggregated
-- reads) ships first.

-- ============================== PART A ==============================
create or replace view public.v_public_drink_explorer_v2 as
 WITH venue AS (
         SELECT DISTINCT ON ((norm_site(a.website_url))) norm_site(a.website_url) AS site_key,
            account_state(a.account_id) AS state_code,
            a.account_name,
            upper(TRIM(BOTH FROM "substring"(a.notes, 'City: ([^.]+)'::text))) AS city_up,
            initcap(lower(TRIM(BOTH FROM "substring"(a.notes, 'City: ([^.]+)'::text)))) AS city,
            COALESCE(a.google_types[1], a.format_code) AS venue_type,
            a.google_rating,
            a.latitude,
            a.longitude,
            a.street_address,
            left(a.postal_code, 5) AS zip5
           FROM accounts a
          WHERE a.website_url IS NOT NULL AND account_state(a.account_id) IS NOT NULL
          ORDER BY (norm_site(a.website_url)), a.google_review_count DESC NULLS LAST, a.account_id
        ), items AS (
         SELECT DISTINCT ON ((norm_site(s.site_url)), (lower(s.item_name)), s.item_price) s.id AS staging_id,
            s.item_type,
            s.item_name,
            s.item_price,
            s.notes,
            norm_site(s.site_url) AS site_key
           FROM staging_menu_extract s
          WHERE s.item_name <> ''::text AND s.item_type <> 'summary'::text AND s.superseded_at IS NULL
          ORDER BY (norm_site(s.site_url)), (lower(s.item_name)), s.item_price, s.id
        ), base AS (
         SELECT i.*, v.state_code, v.account_name, v.city, v.venue_type AS v_type, v.google_rating, v.latitude, v.longitude,
                v.street_address,
                COALESCE(dm.income, z.median_household_income) AS income,
                COALESCE(dm.median_age, z.median_age) AS median_age
           FROM items i
             JOIN venue v ON v.site_key = i.site_key
             LEFT JOIN LATERAL (SELECT d.median_household_income AS income, d.median_age
                                  FROM geographies g JOIN geography_demographics d ON d.geography_id = g.id
                                 WHERE g.geo_type = 'city'::text AND upper(g.geography_name) = v.city_up AND g.subdivision_code = v.state_code
                                 ORDER BY g.id LIMIT 1) dm ON true
             LEFT JOIN LATERAL (SELECT zc.median_household_income, zc.median_age FROM phg_census_zcta zc
                                 WHERE zc.zcta = v.zip5 LIMIT 1) z ON true
        )
 SELECT b.state_code,
    b.item_type AS reported_type,
    COALESCE(c.family, 'unclassified'::text) AS family,
    c.subfamily,
    serve_format(b.item_name, split_part(COALESCE(b.notes, ''::text), '|'::text, 1)) AS serve_format,
    NULLIF(TRIM(BOTH FROM split_part(COALESCE(b.notes, ''::text), '|'::text, 1)), ''::text) AS menu_section,
    b.item_name,
    b.item_price,
    sp.display_name AS drink_name,
    core.identity_class,
    b.account_name AS venue,
    b.city,
    b.street_address AS address,
    COALESCE(b.v_type, 'unclassified'::text) AS venue_type,
    b.google_rating AS rating,
    b.latitude AS lat,
    b.longitude AS lng,
    b.income,
    b.median_age,
        CASE
            WHEN b.income IS NULL THEN 'unknown'::text
            WHEN b.income < 50000 THEN 'under $50k'::text
            WHEN b.income < 65000 THEN '$50k-$65k'::text
            WHEN b.income < 80000 THEN '$65k-$80k'::text
            WHEN b.income < 100000 THEN '$80k-$100k'::text
            ELSE '$100k+'::text
        END AS income_band,
        CASE
            WHEN b.median_age IS NULL THEN 'unknown'::text
            WHEN b.median_age < 25::numeric THEN '21-25'::text
            WHEN b.median_age < 30::numeric THEN '25-30'::text
            WHEN b.median_age < 35::numeric THEN '30-35'::text
            WHEN b.median_age < 40::numeric THEN '35-40'::text
            WHEN b.median_age < 45::numeric THEN '40-45'::text
            WHEN b.median_age < 50::numeric THEN '45-50'::text
            WHEN b.median_age < 55::numeric THEN '50-55'::text
            WHEN b.median_age < 60::numeric THEN '55-60'::text
            ELSE '60+'::text
        END AS age_band,
        CASE
            WHEN b.item_type = 'cocktail'::text THEN 'cocktails'::text
            WHEN c.family = 'beer'::text THEN 'beer'::text
            WHEN c.family = 'wine'::text THEN 'wine'::text
            WHEN c.family = 'non_alcoholic'::text THEN 'non_alcoholic'::text
            WHEN c.family = ANY (ARRAY['whiskey'::text, 'gin'::text, 'vodka'::text, 'rum'::text, 'tequila'::text, 'mezcal'::text, 'brandy'::text, 'agave_other'::text, 'liqueur'::text, 'sake'::text]) THEN 'liquor'::text
            ELSE 'unclassified'::text
        END AS section,
    b.staging_id
   FROM base b
     LEFT JOIN LATERAL classify_item(b.item_name) c(family, subfamily, matched_term) ON true
     LEFT JOIN LATERAL (SELECT k.identity_class, k.spec_id FROM menu_item_cocktail_core k
                         WHERE k.staging_menu_extract_id = b.staging_id ORDER BY k.spec_id NULLS LAST LIMIT 1) core ON true
     LEFT JOIN cocktail_specs sp ON sp.id = core.spec_id;
revoke all on public.v_public_drink_explorer_v2 from public, anon, authenticated;
grant select on public.v_public_drink_explorer_v2 to service_role;

-- ============================== PART B ==============================
create or replace function public.phg_explorer_build_next() returns text
language plpgsql security definer set search_path = public, pg_temp as $$
declare t0 timestamptz := clock_timestamp(); r text;
begin
  if not pg_try_advisory_xact_lock(hashtext('phg_explorer')) then raise exception 'explorer build/swap/refresh already running'; end if;
  drop materialized view if exists public.mv_dash_filters_next, public.mv_dash_breakdown_next, public.mv_dash_sections_next,
    public.mv_menu_dev_venue_profile_next, public.mv_dash_pins_next, public.mv_drink_explorer_next;

  create materialized view public.mv_drink_explorer_next as
   SELECT state_code, reported_type, family, subfamily, serve_format, menu_section, item_name, item_price, drink_name,
    identity_class, venue, city, address, venue_type, rating, lat, lng, income, median_age, income_band, age_band, section,
    (((lower(venue) || '|'::text) || lower(COALESCE(city, ''::text))) || '|'::text) || COALESCE(state_code, ''::text) AS venue_key,
    staging_id
   FROM public.v_public_drink_explorer_v2;
  create unique index mv_de_next_uk on public.mv_drink_explorer_next (staging_id);
  create index mv_de_next_state on public.mv_drink_explorer_next (state_code);
  create index mv_de_next_section on public.mv_drink_explorer_next (section);
  create index mv_de_next_city on public.mv_drink_explorer_next (city);
  create index mv_de_next_name on public.mv_drink_explorer_next (item_name);
  create index mv_de_next_vkey on public.mv_drink_explorer_next (venue_key);
  create index mv_de_next_drink on public.mv_drink_explorer_next (drink_name);
  -- app 18.49.45 pages each state/section by staging_id (keyset): one index serves every page
  create index mv_de_next_st_sec_sid on public.mv_drink_explorer_next (state_code, section, staging_id);

  -- [R2 S4] a stable key: md5 of the whole row, numbered only within identical rows (v_public_venues has exact duplicates)
  create materialized view public.mv_dash_pins_next as
   WITH p AS (
    SELECT v.state_code, v.venue, v.city, v.venue_type, v.rating, v.reviews, v.website, v.lat, v.lng, v.menu_attempted,
     (((lower(v.venue) || '|'::text) || lower(COALESCE(v.city, ''::text))) || '|'::text) || COALESCE(v.state_code, ''::text) AS venue_key,
     COALESCE(d.items, 0::bigint) AS drink_items
    FROM public.v_public_venues v
      LEFT JOIN ( SELECT venue_key, count(*) AS items FROM public.mv_drink_explorer_next GROUP BY venue_key) d
        ON d.venue_key = ((((lower(v.venue) || '|'::text) || lower(COALESCE(v.city, ''::text))) || '|'::text) || COALESCE(v.state_code, ''::text))
    WHERE v.lat IS NOT NULL)
   SELECT p.*, md5(row(p.state_code, p.venue, p.city, p.venue_type, p.rating, p.reviews, p.website, p.lat, p.lng, p.menu_attempted)::text)
            || ':' || row_number() over (partition by md5(row(p.state_code, p.venue, p.city, p.venue_type, p.rating, p.reviews, p.website, p.lat, p.lng, p.menu_attempted)::text) order by p.drink_items) AS pin_key
   FROM p;
  create unique index mv_dash_pins_next_uk on public.mv_dash_pins_next (pin_key);
  create index mv_dash_pins_next_state on public.mv_dash_pins_next (state_code);
  create index mv_dash_pins_next_items on public.mv_dash_pins_next (drink_items desc);

  -- [R2 B1] grouped by venue_key (the unique key), so name/city case or NULL-vs-'' differences cannot duplicate it
  create materialized view public.mv_menu_dev_venue_profile_next as
   SELECT min(venue) AS venue, min(city) AS city, min(state_code) AS state_code, venue_key,
    min(venue_type) AS venue_type, min(income) AS income, min(median_age) AS median_age, min(income_band) AS income_band,
    min(age_band) AS age_band, max(rating) AS rating,
    count(*) FILTER (WHERE section = 'cocktails'::text) AS cocktail_items,
    count(*) FILTER (WHERE section = 'cocktails'::text AND item_price >= 4::numeric AND item_price <= 30::numeric) AS cocktail_priced,
    round(avg(item_price) FILTER (WHERE section = 'cocktails'::text AND item_price >= 4::numeric AND item_price <= 30::numeric), 2) AS cocktail_avg_price,
    percentile_cont(0.5::double precision) WITHIN GROUP (ORDER BY (item_price::double precision)) FILTER (WHERE section = 'cocktails'::text AND item_price >= 4::numeric AND item_price <= 30::numeric) AS cocktail_median_price,
    count(*) FILTER (WHERE section = 'beer'::text) AS beer_items,
    count(*) FILTER (WHERE section = 'wine'::text) AS wine_items,
    count(*) FILTER (WHERE section = 'liquor'::text) AS liquor_items,
    count(*) FILTER (WHERE section = 'non_alcoholic'::text) AS na_items,
    count(*) FILTER (WHERE section = 'unclassified'::text) AS unclassified_items
   FROM public.mv_drink_explorer_next
  GROUP BY venue_key
 HAVING count(*) FILTER (WHERE section = 'cocktails'::text AND item_price >= 4::numeric AND item_price <= 30::numeric) >= 1;
  create unique index mv_mdvp_next_key on public.mv_menu_dev_venue_profile_next (venue_key);
  create index mv_mdvp_next_type on public.mv_menu_dev_venue_profile_next (venue_type);
  create index mv_mdvp_next_state on public.mv_menu_dev_venue_profile_next (state_code);

  create materialized view public.mv_dash_sections_next as
   SELECT state_code, section, count(*) AS items, count(item_price) AS priced, round(avg(item_price), 2) AS avg_price,
    percentile_cont(0.5::double precision) WITHIN GROUP (ORDER BY (item_price::double precision)) AS median_price,
    min(item_price) AS lo, max(item_price) AS hi, count(DISTINCT venue) AS venues, count(DISTINCT city) AS cities
   FROM public.mv_drink_explorer_next GROUP BY state_code, section;
  create unique index mv_dash_sections_next_uk on public.mv_dash_sections_next (state_code, section);

  create materialized view public.mv_dash_breakdown_next as
   SELECT state_code, section, 'city'::text AS dimension, city AS label, count(*) AS items, count(item_price) AS priced,
    round(avg(item_price), 2) AS avg_price, count(DISTINCT venue) AS venues
   FROM public.mv_drink_explorer_next WHERE city IS NOT NULL GROUP BY state_code, section, city
  UNION ALL
   SELECT state_code, section, 'venue_type'::text, venue_type, count(*), count(item_price), round(avg(item_price), 2), count(DISTINCT venue)
   FROM public.mv_drink_explorer_next WHERE venue_type IS NOT NULL GROUP BY state_code, section, venue_type
  UNION ALL
   SELECT state_code, section, 'subfamily'::text, subfamily, count(*), count(item_price), round(avg(item_price), 2), count(DISTINCT venue)
   FROM public.mv_drink_explorer_next WHERE subfamily IS NOT NULL GROUP BY state_code, section, subfamily
  UNION ALL
   SELECT state_code, section, 'serve_format'::text, serve_format, count(*), count(item_price), round(avg(item_price), 2), count(DISTINCT venue)
   FROM public.mv_drink_explorer_next WHERE serve_format IS NOT NULL GROUP BY state_code, section, serve_format
  UNION ALL
   SELECT state_code, section, 'item'::text, item_name, count(*), count(item_price), round(avg(item_price), 2), count(DISTINCT venue)
   FROM public.mv_drink_explorer_next WHERE item_name <> ''::text GROUP BY state_code, section, item_name HAVING count(*) >= 2;
  create unique index mv_dash_breakdown_next_uk on public.mv_dash_breakdown_next (state_code, section, dimension, label);
  create index mv_dash_breakdown_next_idx on public.mv_dash_breakdown_next (state_code, section, dimension);

  create materialized view public.mv_dash_filters_next as
   SELECT state_code, 'city'::text AS dimension, city AS value, count(*) AS items FROM public.mv_drink_explorer_next WHERE city IS NOT NULL GROUP BY state_code, city
  UNION ALL SELECT state_code, 'venue_type'::text, venue_type, count(*) FROM public.mv_drink_explorer_next WHERE venue_type IS NOT NULL GROUP BY state_code, venue_type
  UNION ALL SELECT state_code, 'income_band'::text, income_band, count(*) FROM public.mv_drink_explorer_next WHERE income_band IS NOT NULL GROUP BY state_code, income_band
  UNION ALL SELECT state_code, 'age_band'::text, age_band, count(*) FROM public.mv_drink_explorer_next WHERE age_band IS NOT NULL GROUP BY state_code, age_band
  UNION ALL SELECT state_code, 'drink_name'::text, drink_name, count(*) FROM public.mv_drink_explorer_next WHERE drink_name IS NOT NULL GROUP BY state_code, drink_name;
  create unique index mv_dash_filters_next_uk on public.mv_dash_filters_next (state_code, dimension, value);
  create index mv_dash_filters_next_idx on public.mv_dash_filters_next (state_code, dimension);

  -- [R2 S5] not readable by the app until the swap (default privileges would otherwise expose them)
  foreach r in array array['mv_drink_explorer_next','mv_dash_pins_next','mv_menu_dev_venue_profile_next','mv_dash_sections_next','mv_dash_breakdown_next','mv_dash_filters_next'] loop
    execute format('revoke all on public.%I from public, anon, authenticated', r);
    execute format('grant select on public.%I to service_role', r);
  end loop;

  return 'built in ' || round(extract(epoch from clock_timestamp() - t0)) || ' s: explorer ' ||
    (select count(*) from public.mv_drink_explorer_next) || ' rows, pins ' || (select count(*) from public.mv_dash_pins_next) ||
    ', venue profiles ' || (select count(*) from public.mv_menu_dev_venue_profile_next);
end $$;
revoke all on function public.phg_explorer_build_next() from public, anon, authenticated, service_role;
-- Run (one-off): select cron.schedule('phg-explorer-build-next', '* * * * *', $c$SET statement_timeout='30min'; SELECT public.phg_explorer_build_next();$c$);
-- then, as soon as cron.job_run_details shows the first run started, select cron.unschedule('phg-explorer-build-next');
-- (unscheduling does not stop the running build; it only prevents a second run - the round-1 mistake was putting the
-- unschedule inside the same failing transaction.)

-- ============================== PART C ==============================
create table if not exists public.phg_explorer_swap_log (
  id bigserial primary key, action text not null, at timestamptz not null default now(), detail jsonb);
alter table public.phg_explorer_swap_log enable row level security;
revoke all on public.phg_explorer_swap_log from public, anon, authenticated;
grant select on public.phg_explorer_swap_log to service_role;

-- moves one MV name set: live -> *_old (and its indexes), *_next -> live (and its indexes), grants copied / revoked
create or replace function public.phg_explorer_swap_next() returns text
language plpgsql security definer set search_path = public, pg_temp set lock_timeout = '300ms' set statement_timeout = '3s' as $$
declare r text; ix record; g record; before jsonb; after jsonb;
  names text[] := array['mv_dash_filters','mv_dash_breakdown','mv_dash_sections','mv_menu_dev_venue_profile','mv_dash_pins','mv_drink_explorer'];
begin
  if not pg_try_advisory_xact_lock(hashtext('phg_explorer')) then raise exception 'explorer build/swap/refresh already running'; end if;
  if (select count(*) from pg_matviews where schemaname = 'public' and matviewname = any (select n || '_next' from unnest(names) n)) <> 6
  then raise exception 'swap: the six _next MVs are not all present'; end if;
  if exists (select 1 from pg_matviews where schemaname = 'public' and matviewname = any (select n || '_old' from unnest(names) n))
  then raise exception 'swap: *_old MVs still exist (drop or swap back first)'; end if;
  -- [R2 B3] nothing outside the six-MV chain may depend on the live MVs (it would keep reading the old copies)
  if exists (select 1 from pg_depend d join pg_rewrite rw on rw.oid = d.objid join pg_class dep on dep.oid = rw.ev_class
              join pg_class src on src.oid = d.refobjid
             where src.relnamespace = 'public'::regnamespace and src.relname = any (names) and dep.oid <> src.oid
               and not (dep.relname = any (names)))
  then raise exception 'swap: an object outside the explorer chain depends on the live MVs'; end if;
  select jsonb_object_agg(n, to_regclass('public.' || n)::oid) into before from unnest(names) n;
  foreach r in array names loop
    for ix in select indexrelid::regclass::text as name from pg_index where indrelid = ('public.' || r)::regclass loop
      execute format('alter index %s rename to %I', ix.name, split_part(ix.name, '.', 2) || '_old');
    end loop;
    execute format('alter materialized view public.%I rename to %I', r, r || '_old');
    execute format('alter materialized view public.%I rename to %I', r || '_next', r);
    for ix in select indexrelid::regclass::text as name from pg_index where indrelid = ('public.' || r)::regclass loop
      execute format('alter index %s rename to %I', ix.name, replace(split_part(ix.name, '.', 2), '_next', '_v2'));
    end loop;
    -- [R2 S5] copy SELECT grantees from the old ACL, then close the old copy to the app
    for g in select distinct (aclexplode(c.relacl)).grantee as grantee from pg_class c where c.oid = ('public.' || r || '_old')::regclass loop
      if g.grantee <> 0 then execute format('grant select on public.%I to %I', r, g.grantee::regrole::text); end if;
    end loop;
    execute format('revoke all on public.%I from public, anon, authenticated', r || '_old');
  end loop;
  select jsonb_object_agg(n, to_regclass('public.' || n)::oid) into after from unnest(names) n;
  insert into public.phg_explorer_swap_log (action, detail) values ('swap', jsonb_build_object('before', before, 'after', after));
  notify pgrst, 'reload schema';
  return 'swapped: live MVs are the v2 builds; previous ones kept as *_old';
end $$;
revoke all on function public.phg_explorer_swap_next() from public, anon, authenticated, service_role;

create or replace function public.phg_explorer_swap_back() returns text
language plpgsql security definer set search_path = public, pg_temp set lock_timeout = '300ms' set statement_timeout = '3s' as $$
declare r text; ix record; g record; before jsonb; after jsonb;
  names text[] := array['mv_dash_filters','mv_dash_breakdown','mv_dash_sections','mv_menu_dev_venue_profile','mv_dash_pins','mv_drink_explorer'];
begin
  if not pg_try_advisory_xact_lock(hashtext('phg_explorer')) then raise exception 'explorer build/swap/refresh already running'; end if;
  foreach r in array names loop
    if to_regclass('public.' || r || '_old') is null then raise exception 'swap back: public.%_old is missing', r; end if;
  end loop;
  select jsonb_object_agg(n, to_regclass('public.' || n)::oid) into before from unnest(names) n;
  foreach r in array names loop
    for ix in select indexrelid::regclass::text as name from pg_index where indrelid = ('public.' || r)::regclass loop
      execute format('alter index %s rename to %I', ix.name, replace(split_part(ix.name, '.', 2), '_v2', '_next'));
    end loop;
    execute format('alter materialized view public.%I rename to %I', r, r || '_next');
    execute format('alter materialized view public.%I rename to %I', r || '_old', r);
    for ix in select indexrelid::regclass::text as name from pg_index where indrelid = ('public.' || r)::regclass loop
      execute format('alter index %s rename to %I', ix.name, regexp_replace(split_part(ix.name, '.', 2), '_old$', ''));
    end loop;
    for g in select distinct (aclexplode(c.relacl)).grantee as grantee from pg_class c where c.oid = ('public.' || r || '_next')::regclass loop
      if g.grantee <> 0 then execute format('grant select on public.%I to %I', r, g.grantee::regrole::text); end if;
    end loop;
    execute format('revoke all on public.%I from public, anon, authenticated', r || '_next');
  end loop;
  select jsonb_object_agg(n, to_regclass('public.' || n)::oid) into after from unnest(names) n;
  insert into public.phg_explorer_swap_log (action, detail) values ('swap_back', jsonb_build_object('before', before, 'after', after));
  notify pgrst, 'reload schema';
  return 'swapped back: live MVs are the previous builds; v2 builds are *_next again';
end $$;
revoke all on function public.phg_explorer_swap_back() from public, anon, authenticated, service_role;
-- Rollback order (runbook): pause cron 8 (restore its old command if it was changed) -> select phg_explorer_swap_back()
-- -> check phg_explorer_swap_log 'after' OIDs equal the first 'swap' row's 'before' OIDs -> anon can select the live names.
-- [R2 B4] Rehearsal before the real swap (nothing is kept):
--   do $r$ begin perform public.phg_explorer_swap_next(); <checks: counts, grants, OIDs>;
--               perform public.phg_explorer_swap_back(); <checks: OIDs back to before>; raise exception 'rehearsal ok'; end $r$;

-- ============================== PART D (after the swap) ==============================
-- [R2 S1] one COMMIT per refresh (a failure in one leaves the others fresh), CONCURRENT so readers are never blocked,
-- advisory lock so it never overlaps a build or swap, no stats functions (job 5 does those).
-- (A procedure that COMMITs cannot be SECURITY DEFINER or carry SET clauses; it runs as its caller - cron runs as postgres -
--  with fully qualified names, and the timeouts are set per transaction with set_config.)
create or replace procedure public.refresh_explorer_v2()
language plpgsql as $$
declare r text;
begin
  foreach r in array array['mv_drink_explorer','mv_dash_pins','mv_menu_dev_venue_profile','mv_dash_sections','mv_dash_breakdown','mv_dash_filters'] loop
    if not pg_try_advisory_xact_lock(hashtext('phg_explorer')) then raise notice 'explorer busy; skipped %', r; return; end if;
    perform set_config('statement_timeout', '15min', true);
    perform set_config('lock_timeout', '5s', true);
    execute format('refresh materialized view concurrently public.%I', r);
    commit;
  end loop;
end $$;
revoke all on procedure public.refresh_explorer_v2() from public, anon, authenticated, service_role;
-- cron 8 (after one timed manual CALL; cadence hourly unless the run is short):
--   select cron.alter_job(8, schedule := '17 * * * *', command := $c$CALL public.refresh_explorer_v2();$c$, active := true);
