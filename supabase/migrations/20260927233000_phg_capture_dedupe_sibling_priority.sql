-- PHG-034 (applied 2026-09-27 ~22:00Z via execute_sql):
-- 1. phg_url_key(url): lower-case, no scheme/www, no #fragment, no utm_/fbclid/gclid/mc_ tags, no trailing / ? &.
--    Query strings are kept (?page_id=765 is a different WordPress page).
-- 2. 1,769 queued candidates (not_started/retry) that repeat an earlier candidate of the same venue with the same key
--    -> visual_asset_status 'skipped_duplicate_url'. Undo: update ... set visual_asset_status='not_started'
--    where visual_asset_status='skipped_duplicate_url'.
-- 3. index menu_source_candidates_url_key_idx (account_id, phg_url_key(source_url)); gate trigger
--    phg_menu_candidate_gate_trg also marks new duplicates 'skipped_duplicate_url'.
-- 4. phg_dispatch_menu_recovery_work('visual_acquisition') patched in place: up to 4 queued links per dispatch
--    from venues that already have a drinks/mixed/happy-hour document go first (their other drinks pages,
--    e.g. Adrift cocktail / spirits / happy-hour pages).
create or replace function public.phg_url_key(p_url text) returns text language sql immutable parallel safe set search_path to '' as $$
  select regexp_replace(regexp_replace(regexp_replace(regexp_replace(
           lower(coalesce(p_url,'')), '^https?://(www\.)?', ''), '#.*$', ''),
           '[?&](utm_[a-z]+|fbclid|gclid|mc_[a-z]+)=[^&]*', '', 'g'), '[/?&]+$', '')
$$;
create index if not exists menu_source_candidates_url_key_idx on public.menu_source_candidates (account_id, public.phg_url_key(source_url));
