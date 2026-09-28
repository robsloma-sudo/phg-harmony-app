-- PHG Menu Designer: read-only library and census queries (Supabase project lqjtwabzmgjcufftuqvu).
-- Run through the Supabase connector (execute_sql) or the Coordinator. SELECT / STABLE functions only.
-- Save results as JSON and pass them to tools/run.mjs with --demographics / --comparables.

-- 1. Census for the venue ZIP  ->  --demographics census.json
--    Coverage today: CO, IA, NY (phg_census_zcta). No row = say so in the proposal, don't guess.
select zcta, state, median_age, median_household_income, pop_21_34_pct,
       households_over_100k_pct, bachelors_or_higher_pct, hispanic_latino_pct
from public.phg_census_zcta where zcta = left(:'zip', 5);

-- 2. Band names the corpus filters accept (income lt50|50_75|75_100|100_150|150p, age lt30|30_35|35_40|40_45|45p,
--    young lt15|15_20|20_30|30p, affluent/edu lt25|25_40|40_60|60p, hisp lt10|10_25|25_50|50p).
select public.phg_census_band_catalog();

-- 3. Comparable menus  ->  pick 3+ and write --comparables refs.json  [{document_id, venue, city, note}]
--    Widen in this order until you have 3–8 good ones: same city + kind + list  ->  same state  ->  same census bands anywhere.
select (r->>'id')::bigint document_id, r->'accounts'->>'account_name' venue, r->>'city' city, r->>'state' st,
       r->>'venue_type' venue_type, r->'lists' lists, r->'census'->>'median_household_income' income,
       r->>'ready_page_count' pages
from jsonb_array_elements((public.phg_corpus_browse_documents(jsonb_build_object(
       'menu_kind', jsonb_build_array('beverage','mixed'),   -- or happy_hour / specials / food
       'has',       jsonb_build_array('cocktails'),          -- lists that must be present
       'state',     jsonb_build_array('CO'),
       'young',     jsonb_build_array('30p'),                -- census bands, optional
       'limit', 12, 'sort', 'recent')))->'rows') r;

-- 4. What a comparable actually prints: sections, counts and price spread per section.
select d.id document_id, coalesce(s.section_name,'-') section, s.item_type, count(*) n,
       min(s.item_price) lo, percentile_cont(0.5) within group (order by s.item_price) median, max(s.item_price) hi,
       left(string_agg(distinct s.item_name, ' | '), 200) sample_items
from public.menu_visual_documents d
join public.staging_menu_extract s on s.menu_page_url = d.original_menu_url and s.superseded_at is null
where d.id = any (:'ids'::bigint[])
group by 1,2,3 order by 1, n desc;

-- 5. Page images to look at (full resolution; sign via storage for viewing, never downscale).
select p.menu_visual_document_id document_id, p.page_number, p.width, p.height, p.page_image_bucket, p.page_image_path
from public.menu_visual_pages p
where p.menu_visual_document_id = any (:'ids'::bigint[]) and p.render_status = 'ready'
order by 1, 2;

-- 6. List make-up across the library for a menu kind (how deep each list usually runs).
select key as list, count(*) menus, round(avg(value::int),1) avg_items, percentile_cont(0.5) within group (order by value::int) median_items
from public.phg_menu_doc_class, jsonb_each_text(lists)
where menu_kind = 'beverage'
group by 1 order by menus desc;

-- 8. Classic specs for items with no description  ->  --standards specs.json  (labelled "standard"; venue recipe wins)
select public.phg_designer_query($q$
  select cocktail_name, consensus_spec, garnish, glassware from public.cocktail_reference
  where lower(cocktail_name) = any (array['ranch water','paloma'])      -- the draft/voice item names, lower-cased
$q$, 200, '<task id>');

-- NOTE: every query goes through public.phg_designer_query(...) (handoff/agents/MENU_DATA_ACCESS.md). The plain SELECTs
-- above show the SQL to wrap; the designer role cannot run SQL outside the gateway.

-- 7. The designer's hand-off: tools/run.mjs writes submit.json / submit.sql (phg_design_proposal_submit arguments,
--    including p_layout). The Coordinator runs it; the designer writes nothing.
