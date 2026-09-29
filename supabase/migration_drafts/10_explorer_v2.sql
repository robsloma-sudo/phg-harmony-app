-- PHG-051 (2026-09-29): market explorer v2 - fresh data, live rows only, ZIP census, non-blocking refreshes.
--
-- Problem: mv_drink_explorer (+ mv_dash_pins and the 4 MVs built on them) were last refreshed 2026-09-25 21:10 UTC;
-- cron 8 (refresh_explorer) is paused because its two NON-concurrent refreshes lock every reader for minutes
-- (PHG-018, iPhone-login 504s). The base view reads all 1.1 M staging rows (including 765 k superseded duplicates and
-- old prices, PHG-026) and joins income / median age only at city level (geography_demographics = Iowa only), so CO and
-- NY have 0% census coverage although phg_census_zcta covers 99.6% of their venues by postal code.
--
-- Design (additive until PART C):
--   PART A  v_public_drink_explorer_v2: same 23 columns in the same order + staging_id (unique per row), live staging
--           rows only (superseded_at is null), census = city demographics, else the venue's ZIP (phg_census_zcta).
--   PART B  phg_explorer_build_next(): builds mv_*_next copies of all six MVs from v2, with UNIQUE indexes so every
--           future refresh can be CONCURRENT (readers never blocked). Readers keep using the old MVs meanwhile.
--           Runs as a one-off pg_cron job (it takes minutes; no client timeout).
--   PART C  phg_explorer_swap_next(): one short transaction (lock_timeout 3 s): old -> *_old, *_next -> live names,
--           grants copied. Rollback: phg_explorer_swap_back() renames them back (the *_old MVs are kept until dropped
--           by hand after verification).
--   PART D  refresh_explorer_v2(): concurrent refreshes; replaces cron 8's command (re-enabled only after C + checks).
-- mv_dash_pins has exact duplicate rows (v_public_venues duplicates), so its _next adds a row number column at the END
-- (pin_row) to make it unique; existing readers select named columns, so an extra trailing column is harmless.

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
          ORDER BY (norm_site(a.website_url)), a.google_review_count DESC NULLS LAST
        ), demo AS (
         SELECT upper(g.geography_name) AS city_up,
            g.subdivision_code AS st,
            d.median_household_income AS income,
            d.median_age
           FROM geographies g
             JOIN geography_demographics d ON d.geography_id = g.id
          WHERE g.geo_type = 'city'::text
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
             LEFT JOIN demo dm ON dm.city_up = v.city_up AND dm.st = v.state_code
             LEFT JOIN phg_census_zcta z ON z.zcta = v.zip5
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
     LEFT JOIN menu_item_cocktail_core core ON core.staging_menu_extract_id = b.staging_id
     LEFT JOIN cocktail_specs sp ON sp.id = core.spec_id;
revoke all on public.v_public_drink_explorer_v2 from anon, authenticated;
grant select on public.v_public_drink_explorer_v2 to service_role;

-- ============================== PART B ==============================
create or replace function public.phg_explorer_build_next() returns text
language plpgsql security definer set search_path = public, pg_temp as $$
declare t0 timestamptz := clock_timestamp();
begin
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

  create materialized view public.mv_dash_pins_next as
   SELECT v.state_code, v.venue, v.city, v.venue_type, v.rating, v.reviews, v.website, v.lat, v.lng, v.menu_attempted,
    (((lower(v.venue) || '|'::text) || lower(COALESCE(v.city, ''::text))) || '|'::text) || COALESCE(v.state_code, ''::text) AS venue_key,
    COALESCE(d.items, 0::bigint) AS drink_items,
    row_number() over (order by v.state_code, v.venue, v.city, v.lat, v.lng, v.website) AS pin_row
   FROM public.v_public_venues v
     LEFT JOIN ( SELECT venue_key, count(*) AS items FROM public.mv_drink_explorer_next GROUP BY venue_key) d
       ON d.venue_key = ((((lower(v.venue) || '|'::text) || lower(COALESCE(v.city, ''::text))) || '|'::text) || COALESCE(v.state_code, ''::text))
  WHERE v.lat IS NOT NULL;
  create unique index mv_dash_pins_next_uk on public.mv_dash_pins_next (pin_row);
  create index mv_dash_pins_next_state on public.mv_dash_pins_next (state_code);
  create index mv_dash_pins_next_items on public.mv_dash_pins_next (drink_items desc);

  create materialized view public.mv_menu_dev_venue_profile_next as
   SELECT venue, city, state_code,
    (((lower(venue) || '|'::text) || lower(COALESCE(city, ''::text))) || '|'::text) || COALESCE(state_code, ''::text) AS venue_key,
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
  GROUP BY venue, city, state_code
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

  return 'built in ' || round(extract(epoch from clock_timestamp() - t0)) || ' s: explorer ' ||
    (select count(*) from public.mv_drink_explorer_next) || ' rows, pins ' || (select count(*) from public.mv_dash_pins_next) ||
    ', venue profiles ' || (select count(*) from public.mv_menu_dev_venue_profile_next);
end $$;
revoke all on function public.phg_explorer_build_next() from public, anon, authenticated, service_role;

-- ============================== PART C (only after the _next checks pass; review first) ==============================
-- create or replace function public.phg_explorer_swap_next() ... renames in one transaction, lock_timeout 3s, copies
-- grants (select to anon, authenticated, service_role; + phg_menu_designer, phg_harmony_reader on mv_drink_explorer and
-- mv_menu_dev_venue_profile); swap_back reverses it. Written after the build is measured.
-- ============================== PART D ==============================
-- refresh_explorer_v2(): refresh materialized view CONCURRENTLY for all six; cron 8 command switched to it.
