DO $rehearse_main$
DECLARE
  r jsonb := '{}'; a jsonb := '{}'; b jsonb := '{}'; c jsonb := '{}'; v jsonb; res jsonb;
  t0 timestamptz; t1 timestamptz; acct text := 'ACC-CO-LED-03-25486'; orig_url text;
  cur_id uuid; cur2 uuid; cur_now uuid; secs jsonb; secs2 jsonb; secs4 jsonb; secs9 jsonb; items jsonb; item_x uuid;
  rem int; calls jsonb; lease_owner uuid := gen_random_uuid(); claimed timestamptz := clock_timestamp();
  secs10 jsonb; gres jsonb := '{}'; skip_acct text; multi_acct text; stg_acct text; stg_url text; snap jsonb; snap2 jsonb;
  n1 int; n2 int; tid uuid; pid uuid; dlayout jsonb; ddoc jsonb; secs11 jsonb; w jsonb; mon_sql text;
  e_state text; e_msg text; e_ctx text; e_det text;
BEGIN
  set local statement_timeout = '58s';
  t0 := clock_timestamp();
  BEGIN
    EXECUTE $rehearse_f1$-- PHG-026 (2026-09-27): stop order-item duplicate menus from replacing venues' real menus.
--
-- Root cause (read-only investigation wf_50c3da17-0c7):
--  * promote_clean_menu_batch hashes account|page URL|sections, so the same full menu scraped from
--    dozens of online-ordering item pages (?item=..., /order/<menu>/<cat>/<item>) never matched the
--    submit_menu duplicate check, and
--  * submit_menu superseded EVERY current menu of the account unconditionally, so each item page
--    replaced the venue's menu; the last page promoted won. 119 damaged venues out of 185 with a
--    pre-incident menu (their current menu became smaller than their largest pre-incident one); 7,429 menus were created today from only ~2,500 distinct item sets.
--  * Upstream, phg_save_menu_candidate_extraction re-stages the full item list for every sibling
--    page (85% of today's staging rows are copies).
--
-- Design choice (differs from the investigation's multi-current proposal on purpose): every reader
-- (v_menu_composition, v_menu_brand_presence, v_menu_category_share, phg_menu_composition,
-- phg_brand_presence, phg-expanded-data) assumes ONE current menu per venue. This keeps that
-- invariant and decides which capture should be current:
--   same source (canonical URL)      -> re-capture replaces, unless identical or a strict subset (no URL = never same)
--   other source, a true subset       -> duplicate, nothing inserted (a missing price matches any price: unknown)
--   other source, near-identical (>=90% of the current items) and at least as large -> replaces (newer prices kept),
--                                     except when the current menu is under 7 days old (flip-flop damping -> alternate)
--   a capture that supplies a price the current menu lacks for the same item is never a duplicate / subset
--   zero-item capture beside a menu  -> ignored
--   item/event/product page          -> never replaces a non-empty current menu (stored as alternate), even
--                                       when it shares the menu's source key (?item= is stripped from the key)
--   same source, less than half the items -> partial re-capture, stored as alternate
--   other source, more distinct items (then more drinks items) -> replaces; otherwise stored as alternate
-- "Drinks items" = cocktail / spirit_pour items plus every item in a cocktails / wine / beer / spirits section
-- (beer and wine are stored as item_type 'other' inside typed sections).
-- Alternates are real rows with is_current=false and superseded_reason, so nothing is lost.
-- One current menu per venue is enforced by the unique index menus_one_current_per_account (created by the repair after
-- it has made the data consistent); submit_menu demotes before it inserts.
-- Menus are never deleted. submit_menu locks the account row first (the same lock the extraction save takes),
-- then an advisory lock, so both writers of one account queue behind each other.
--
-- Review round 1 fixes (2026-09-28): drinks count includes typed sections; size decides before drinks count;
-- item-page and partial-recapture guards on the same-source branch; empty current menus can be replaced;
-- extraction duplicate branch supersedes the candidate's own stale rows and never matches an empty duplicate;
-- helpers inlinable (no SET) so the repair can run at table scale.
--
-- Review round 3 fixes (2026-09-28): function rollback drops the one-current index first (the restored live bodies
-- insert before they demote) and re-applies the revokes; the definition backup is read-only for service_role too;
-- a capture that ADDS a price the current menu lacks is never a duplicate (price enrichment); near-identical
-- captures from another source do not replace a current menu created in the last 7 days (flip-flop damping);
-- promote_clean_menu_batch takes at most 5 pages per call.
--
-- Review round 4 fixes (2026-09-28): the definition backup is SELECT-only for service_role (revoke all, grant select);
-- an item page from the SAME source replaces a real-page current menu only when it is strictly larger by
-- (distinct items, drinks items) - the same order the repair's Step 2 uses - so a same-size item page never takes the
-- real page's place (it is kept as an alternate). An item page still replaces a current menu that is itself an item
-- page when it is at least as large (unchanged in round 4; changed in round 5, below).
--
-- Review round 5 fixes (2026-09-28):
--  * Over a current menu that is itself an item page, every comparison uses (distinct items, drinks items), Step 2's
--    order: a real page from another source replaces it when at least as large by (items, drinks)
--    ('real_page_over_item_page'), and the 7-day damping never holds a real page behind an item-page current menu.
--  * An item page replaces an item-page current menu of the same source only when strictly larger by (items, drinks),
--    unless it is the very same URL (a re-capture of that page), where at least as large is enough (safety SF-D).
--  * "Drinks items" counts DISTINCT drinks item keys (name|price), in submit_menu and in the repair's Step 2 ranking
--    alike (both use phg_menu_payload_bev_count / phg_menu_bev_count), so a repeated line cannot tip a tie (M1).
--  * submit_menu has lock_timeout 5s as a function-level setting (SET LOCAL scoped to the call; reset on return):
--    a writer waiting on the account row or menus longer than 5 s fails with 55P03 and changes nothing.
--  * phg_rollback_function_defs_20260927 is not executable by service_role (runbook runs as postgres).
--
-- Apply with cron 7 (promotion) and 13 (extraction) PAUSED. Data repair is a separate script.
-- Apply through the runbook (apply_migration, or psql -1 -f), in order: this file, then 20260927191000. Not with
-- `supabase db push`: newer migrations (20260927200000 and later) are already applied, so db push would refuse or
-- skip these out-of-order files.

set local lock_timeout = '3s';

-- ---------- 0. save the live definitions this migration replaces (rollback: phg_rollback_function_defs_20260927) ----------
create table if not exists public.phg_backup_function_defs_20260927 (
  signature text primary key, definition text not null, acl text, saved_at timestamptz not null default now());
alter table public.phg_backup_function_defs_20260927 enable row level security;
revoke all on public.phg_backup_function_defs_20260927 from anon, authenticated, service_role;
grant select on public.phg_backup_function_defs_20260927 to service_role;
insert into public.phg_backup_function_defs_20260927 (signature, definition, acl)
select p.oid::regprocedure::text, pg_get_functiondef(p.oid), p.proacl::text
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('submit_menu','promote_clean_menu_batch','phg_save_menu_candidate_extraction')
on conflict (signature) do nothing;
do $$ begin
  if (select count(*) from public.phg_backup_function_defs_20260927) < 4 then
    raise exception 'expected 4 saved function definitions before replacing them';
  end if;
end $$;
-- Restores all four exactly as they were (including the 10-arg submit_menu this migration drops).
-- The restored live submit_menu bodies INSERT the new current menu before they demote the old one, so the
-- one-current-menu unique index (created by the repair) must go first, or every restored call would fail.
-- Re-applies the revokes on each restored signature (a re-created function gets the schema's default grants) and the
-- service_role grant each one had (saved in acl; live 2026-09-28: postgres + service_role only on all four).
-- The data repair has its own rollback (phg_repair_20260927_rollback); run it BEFORE this one if both are needed.
create or replace function public.phg_rollback_function_defs_20260927()
returns int language plpgsql set search_path to 'public', 'pg_temp' as $$
declare r record; n int := 0;
begin
  drop index if exists public.menus_one_current_per_account;
  for r in select signature, definition, acl from public.phg_backup_function_defs_20260927 order by signature loop
    execute r.definition;
    execute format('revoke all on function %s from public, anon, authenticated', r.signature::regprocedure);
    if r.acl like '%service_role=X%' then
      execute format('grant execute on function %s to service_role', r.signature::regprocedure);
    end if;
    n := n + 1;
  end loop;
  return n;
end $$;
revoke all on function public.phg_rollback_function_defs_20260927() from public, anon, authenticated, service_role;

-- ---------- A. schema additions (nullable, no defaults: metadata-only, no table rewrite) ----------
alter table public.menus
  add column if not exists source_key        text,
  add column if not exists item_keys         text[],
  add column if not exists item_set_hash     text,
  add column if not exists superseded_reason text,
  add column if not exists superseded_at     timestamptz;
alter table public.staging_menu_extract
  add column if not exists promoted_menu_id  uuid,
  add column if not exists superseded_reason text;
alter table public.menu_source_candidates
  add column if not exists item_set_hash             text,
  add column if not exists duplicate_of_candidate_id bigint;

create index if not exists menus_item_set_idx on public.menus (account_id, item_set_hash);
-- menu_source_candidates (account_id, item_set_hash) index is built CONCURRENTLY separately.

-- ---------- B. helpers ----------
-- Canonical identity of an evidence URL: host without www/port, path without trailing slash,
-- '&amp;' decoded, fragment and tracking/item-selector params dropped, remaining params sorted.
create or replace function public.phg_menu_source_key(p_url text)
returns text language plpgsql immutable parallel safe set search_path = '' as $$
declare u text; h text; p text; q text; kept text[];
begin
  if p_url is null or btrim(p_url) = '' then return null; end if;
  u := regexp_replace(replace(btrim(p_url), '&amp;', '&'), '#.*$', '');
  h := lower(substring(u from '^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]+)'));
  if h is null then return lower(u); end if;
  h := regexp_replace(regexp_replace(h, '^www\.', ''), ':(80|443)$', '');
  p := coalesce(substring(u from '^[A-Za-z][A-Za-z0-9+.-]*://[^/?#]+(/[^?#]*)'), '');
  p := regexp_replace(p, '/+$', '');
  q := substring(u from '\?(.*)$');
  if q is not null then
    select array_agg(kv order by kv) into kept
      from unnest(string_to_array(q, '&')) as kv
     where kv <> ''
       and lower(split_part(kv, '=', 1)) not in
           ('item','matchitemname','utm_source','utm_medium','utm_campaign','utm_term',
            'utm_content','fbclid','gclid','msclkid','ref','source');
  end if;
  return h || p || case when kept is null then '' else '?' || array_to_string(kept, '&') end;
end $$;

-- Online-ordering item/detail, event and product pages.
create or replace function public.phg_menu_url_is_item_page(p_url text)
returns boolean language sql immutable parallel safe set search_path = '' as $$
  select coalesce(p_url, '') ~* '([?&](amp;)?(item|matchitemname)=|/order/[^/?#]+/[^/?#]+/[^/?#]+|/(events?|event-details|calendar|products?|producto)/[^/?#]+)'
$$;

-- One comparable key per item: normalized name + normalized price.
create or replace function public.phg_menu_item_key(p_name text, p_price numeric)
returns text language sql immutable parallel safe as $$
  select nullif(pg_catalog.regexp_replace(pg_catalog.lower(pg_catalog.btrim(coalesce(p_name, ''))), '\s+', ' ', 'g'), '')
         || '|' || coalesce(pg_catalog.trim_scale(p_price)::text, '')
$$;

-- Keys of a submit_menu payload (same '(unnamed)' fallback submit_menu stores).
create or replace function public.phg_menu_payload_item_keys(p_sections jsonb)
returns text[] language sql immutable set search_path = '' as $$
  select coalesce(array_agg(distinct k order by k), '{}'::text[])
  from (
    select public.phg_menu_item_key(coalesce(nullif(it->>'item_name', ''), '(unnamed)'),
                                    nullif(it->>'price', '')::numeric) as k
    from jsonb_array_elements(coalesce(p_sections, '[]'::jsonb)) as s,
         jsonb_array_elements(coalesce(s->'items', '[]'::jsonb)) as it
  ) x where k is not null
$$;

-- Drinks item count of a payload: DISTINCT keys (name|price, same '(unnamed)' fallback as the item keys) of typed
-- drinks items plus every item in a drinks section. Same definition as phg_menu_bev_count (stored menus).
create or replace function public.phg_menu_payload_bev_count(p_sections jsonb)
returns integer language sql immutable set search_path = '' as $$
  select count(distinct public.phg_menu_item_key(coalesce(nullif(it->>'item_name', ''), '(unnamed)'),
                                                 nullif(it->>'price', '')::numeric))::int
  from jsonb_array_elements(coalesce(p_sections, '[]'::jsonb)) as s,
       jsonb_array_elements(coalesce(s->'items', '[]'::jsonb)) as it
  where coalesce(it->>'item_type', '') in ('cocktail', 'spirit_pour', 'beer', 'wine')
     or coalesce(s->>'section_type', '') in ('cocktails', 'wine', 'beer', 'spirits')
$$;

-- Keys of an extraction payload (phg_save_menu_candidate_extraction items: item_name, item_price).
create or replace function public.phg_menu_extract_item_keys(p_items jsonb)
returns text[] language sql immutable set search_path = '' as $$
  select coalesce(array_agg(distinct k order by k), '{}'::text[])
  from (select public.phg_menu_item_key(x->>'item_name', nullif(x->>'item_price', '')::numeric) as k
        from jsonb_array_elements(coalesce(p_items, '[]'::jsonb)) x) y
  where k is not null
$$;

-- Keys of a stored menu.
create or replace function public.phg_menu_item_keys(p_menu_id uuid)
returns text[] language sql stable set search_path = '' as $$
  select coalesce(array_agg(distinct k order by k), '{}'::text[])
  from (
    select public.phg_menu_item_key(i.item_name, i.price) as k
    from public.menu_sections s join public.menu_items i on i.section_id = s.id
    where s.menu_id = p_menu_id
  ) x where k is not null
$$;

-- Drinks item count of a stored menu: DISTINCT drinks item keys (beer / wine are item_type 'other' inside typed
-- sections). Used by submit_menu and by the repair's Step 2 ranking, so both count the same way.
create or replace function public.phg_menu_bev_count(p_menu_id uuid)
returns integer language sql stable set search_path = '' as $$
  select count(distinct public.phg_menu_item_key(i.item_name, i.price))::int
  from public.menu_sections s join public.menu_items i on i.section_id = s.id
  where s.menu_id = p_menu_id
    and (i.item_type in ('cocktail', 'spirit_pour', 'beer', 'wine') or s.section_type in ('cocktails', 'wine', 'beer', 'spirits'))
$$;

-- Items of a that also appear in b. Same name and same price, or the same name where either side has no price
-- (a missing price is unknown, not a different item).
create or replace function public.phg_menu_keys_overlap(a text[], b text[])
returns integer language sql immutable parallel safe as $$
  select count(*)::int from (select distinct x from pg_catalog.unnest(coalesce(a, '{}'::text[])) x) ax
  where exists (select 1 from pg_catalog.unnest(coalesce(b, '{}'::text[])) y
                where y = ax.x
                   or (pg_catalog.split_part(y, '|', 1) = pg_catalog.split_part(ax.x, '|', 1)
                       and (pg_catalog.split_part(y, '|', 2) = '' or pg_catalog.split_part(ax.x, '|', 2) = '')))
$$;

-- Capture items that ADD a price the other menu lacks: a has 'name|price', b has 'name|' (no price) and not
-- 'name|price'. Such a capture enriches the menu and is never a duplicate or a subset of it.
create or replace function public.phg_menu_keys_price_adds(a text[], b text[])
returns integer language sql immutable parallel safe as $$
  select count(*)::int from (select distinct x from pg_catalog.unnest(coalesce(a, '{}'::text[])) x) ax
  where pg_catalog.split_part(ax.x, '|', 2) <> ''
    and exists (select 1 from pg_catalog.unnest(coalesce(b, '{}'::text[])) y where y = pg_catalog.split_part(ax.x, '|', 1) || '|')
    and not exists (select 1 from pg_catalog.unnest(coalesce(b, '{}'::text[])) y where y = ax.x)
$$;

create or replace function public.phg_menu_key_set_hash(p_keys text[])
returns text language sql immutable parallel safe as $$
  select pg_catalog.md5(pg_catalog.array_to_string(coalesce(p_keys, '{}'::text[]), '~'))
$$;

revoke all on function public.phg_menu_source_key(text), public.phg_menu_url_is_item_page(text),
  public.phg_menu_item_key(text, numeric), public.phg_menu_payload_item_keys(jsonb),
  public.phg_menu_payload_bev_count(jsonb), public.phg_menu_extract_item_keys(jsonb),
  public.phg_menu_item_keys(uuid), public.phg_menu_bev_count(uuid), public.phg_menu_key_set_hash(text[]),
  public.phg_menu_keys_overlap(text[], text[]), public.phg_menu_keys_price_adds(text[], text[])
  from public, anon, authenticated;

-- ---------- C. submit_menu (15-arg): the single chokepoint for every writer ----------
create or replace function public.submit_menu(p_account_id text, p_source_code text, p_evidence_url text, p_menu_title text, p_menu_format text, p_extraction_confidence text, p_extraction_notes text, p_published_date date, p_content_hash text, p_sections jsonb, p_raw_content text default null::text, p_raw_content_type text default null::text, p_platform text default null::text, p_source_file_url text default null::text, p_needs_vision_pass boolean default false)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
 set lock_timeout to '5s'
as $function$
declare v_menu_id uuid;v_menu_code text;v_source_id uuid;v_section jsonb;v_item jsonb;v_brand jsonb;v_section_id uuid;v_item_id uuid;v_brand_id uuid;v_items int:=0;v_brands int:=0;v_inferred int:=0;v_expected_items int:=0;v_existing uuid;v_cat text;v_has_brands boolean;
 v_source_key text; v_keys text[]; v_n int; v_bev int; v_set_hash text; v_itemish boolean;
 c record; c_keys text[]; c_n int; c_bev int; v_ov int; v_adds int;
 v_make_current boolean := true; v_alt_of uuid; v_reason text; v_supersede uuid[] := '{}';
 c_dup_ratio constant numeric := 0.9;
 c_damping constant interval := interval '7 days';
begin
 -- Lock the account row first: the extraction save locks the same row, so the two writers queue instead of
 -- deadlocking; the advisory lock then serializes promotion with the submit-menu Edge function.
 -- lock_timeout 5s (function-level SET above): a wait longer than that raises 55P03 and the call changes nothing.
 perform 1 from public.accounts where account_id=p_account_id for no key update;
 if not found then raise exception 'unknown account_id %',p_account_id;end if;
 perform pg_advisory_xact_lock(hashtextextended('phg_submit_menu:'||p_account_id, 0));
 select id into v_source_id from public.sources where source_code=p_source_code;
 if p_content_hash is not null then
  select id into v_existing from public.menus where account_id=p_account_id and content_hash=p_content_hash limit 1;
  if v_existing is not null then return jsonb_build_object('status','duplicate','menu_id',v_existing,'message','identical capture already recorded; nothing inserted');end if;
 end if;
 select coalesce(sum(jsonb_array_length(coalesce(section->'items','[]'::jsonb))),0)::int into v_expected_items from jsonb_array_elements(coalesce(p_sections,'[]'::jsonb)) section;
 if p_menu_format in ('pdf','image') and v_expected_items=0 then raise exception 'PDF/image capture requires positive item evidence; keep zero-item sources in review';end if;

 v_source_key := public.phg_menu_source_key(p_evidence_url);
 v_keys       := public.phg_menu_payload_item_keys(p_sections);
 v_n          := cardinality(v_keys);
 v_bev        := public.phg_menu_payload_bev_count(p_sections);
 v_set_hash   := public.phg_menu_key_set_hash(v_keys);
 v_itemish    := public.phg_menu_url_is_item_page(p_evidence_url);

 -- Decide against the current menu(s) before writing anything.
 for c in select m.id, coalesce(m.source_key, public.phg_menu_source_key(m.evidence_url)) as source_key, m.item_keys, m.created_at,
                  m.evidence_url, public.phg_menu_url_is_item_page(m.evidence_url) as itemish
            from public.menus m where m.account_id=p_account_id and m.is_current
           order by m.created_at desc, m.id for update loop
  c_keys := coalesce(c.item_keys, public.phg_menu_item_keys(c.id));
  c_n    := cardinality(c_keys);
  v_ov   := public.phg_menu_keys_overlap(v_keys, c_keys);
  -- items whose price the capture supplies and the current menu lacks: never a duplicate (price enrichment)
  v_adds := public.phg_menu_keys_price_adds(v_keys, c_keys);
  c_bev  := public.phg_menu_bev_count(c.id);
  -- a capture without a URL is never "the same page" as another capture without one
  if c.source_key is not null and c.source_key = v_source_key then
   -- Same source: identical or strict-subset re-capture keeps the current menu (unless it adds prices).
   if v_n > 0 and v_ov = v_n and c_n >= v_n and v_adds = 0 then
    return jsonb_build_object('status', case when c_n > v_n then 'subset_of_current' else 'duplicate_of_current' end,
      'menu_id',c.id,'items',v_n,'current_items',c_n,
      'message','same source returned the same items or a subset of the current menu; current menu kept');
   end if;
   if v_n = 0 and c_n > 0 then
    return jsonb_build_object('status','empty_capture_ignored','menu_id',c.id,'items',0,'message','zero-item re-capture ignored; current menu kept');
   end if;
   if v_itemish and c_n > 0 and not (v_ov >= ceil(c_dup_ratio * c_n)
                                     and ((v_n, v_bev) > (c_n, c_bev)
                                          or (c.itemish and p_evidence_url = c.evidence_url and (v_n, v_bev) >= (c_n, c_bev)))) then
    -- an item page shares the menu's key (?item= is stripped) but is not a fuller copy of it. It must be strictly
    -- larger by (items, then drinks items: Step 2's order), over a real page (C1, round 4) and over another item page
    -- alike (SF-D, round 5), so sibling item pages of one menu never swap places. The one exemption: the SAME item page
    -- URL re-captured, over itself, replaces when at least as large (its own newer prices).
    v_make_current := false; v_alt_of := c.id; v_reason := 'alternate_item_page';
   elsif c_n > 0 and v_n < ceil(0.5 * c_n) then
    -- a partial parse of the same page must not replace the full menu
    v_make_current := false; v_alt_of := c.id; v_reason := 'alternate_partial_recapture';
   else
    v_supersede := v_supersede || c.id;
    v_reason := coalesce(v_reason, case when v_adds > 0 and v_ov = v_n then 'same_source_price_enrichment' else 'same_source_recapture' end);
   end if;
  else
   -- Other source: only a TRUE subset of an equal-or-larger current menu is a duplicate (a 90% match may carry
   -- newer prices, and those must not be thrown away); a capture that adds a missing price is not a subset.
   if v_n > 0 and c_n >= v_n and v_ov = v_n and v_adds = 0 then
    return jsonb_build_object('status','duplicate_of_current','menu_id',c.id,'items',v_n,'overlap',v_ov,'current_items',c_n,
      'message','item set already present in the current menu of this account; nothing inserted');
   end if;
   if v_n = 0 then
    return jsonb_build_object('status','empty_capture_ignored','menu_id',c.id,'items',0,'message','zero-item capture not promoted beside an existing current menu');
   end if;
   if v_itemish and c_n > 0 then
    v_make_current := false; v_alt_of := c.id; v_reason := 'alternate_item_page';
   elsif (v_n, v_bev) > (c_n, c_bev) then
    v_supersede := v_supersede || c.id;
    v_reason := coalesce(v_reason, case when c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) then 'contained_in_larger_capture' else 'larger_beverage_capture' end);
   elsif c.itemish and (v_n, v_bev) >= (c_n, c_bev) then
    -- (round 5, C1) the current menu is an item page and this capture is a REAL page (v_itemish is false here) at least
    -- as large by (items, drinks items): Step 2's order puts the real page first on ties
    v_supersede := v_supersede || c.id;
    v_reason := coalesce(v_reason, 'real_page_over_item_page');
   elsif v_n >= c_n and c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) and v_adds = 0
         and c.created_at > now() - c_damping and not (c.itemish and not v_itemish) then
    -- flip-flop damping: two pages of the same menu must not keep swapping current. The current menu came from
    -- another source less than 7 days ago and this capture is only near-identical (not larger): keep it as an alternate.
    -- Never applied to a real page behind an item-page current menu (round 5, C1): that page should become current.
    v_make_current := false; v_alt_of := c.id; v_reason := 'alternate_near_identical_recent_other_source';
   elsif v_n >= c_n and c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) then
    -- same menu, same size, from another page, with some new prices (or prices the current menu lacked):
    -- the newer capture becomes current
    v_supersede := v_supersede || c.id;
    v_reason := coalesce(v_reason, case when v_adds > 0 then 'price_enrichment_other_source' else 'newer_near_identical_capture' end);
   else
    v_make_current := false; v_alt_of := c.id; v_reason := 'alternate_smaller_other_source';
   end if;
  end if;
 end loop;

 if not v_make_current then
  v_supersede := '{}';
  -- The same item set already stored (e.g. an earlier alternate): nothing new to keep.
  select id into v_existing from public.menus where account_id=p_account_id and item_set_hash=v_set_hash limit 1;
  if v_existing is not null then
   return jsonb_build_object('status','duplicate_item_set','menu_id',v_existing,'items',v_n,'message','same item set already stored for this account; nothing inserted');
  end if;
 end if;

 v_menu_code:='MENU-'||left(md5(p_account_id||coalesce(p_content_hash,'')||clock_timestamp()::text),20);
 -- demote first: the one-current-menu unique index is checked row by row
 if v_make_current and cardinality(v_supersede) > 0 then
  update public.menus set is_current=false, superseded_at=now(), superseded_reason=v_reason
   where id = any(v_supersede) and is_current;
 end if;
 insert into public.menus(menu_id,account_id,source_id,evidence_url,menu_title,menu_format,extraction_confidence,extraction_notes,published_date,content_hash,is_current,superseded_by,superseded_reason,superseded_at,raw_content,raw_content_type,raw_content_chars,platform,source_file_url,needs_vision_pass,item_count,source_key,item_keys,item_set_hash)
 values(v_menu_code,p_account_id,v_source_id,p_evidence_url,p_menu_title,p_menu_format,p_extraction_confidence,p_extraction_notes,p_published_date,p_content_hash,v_make_current,
        case when v_make_current then null else v_alt_of end, case when v_make_current then null else v_reason end, case when v_make_current then null else now() end,
        p_raw_content,p_raw_content_type,length(p_raw_content),p_platform,p_source_file_url,p_needs_vision_pass,v_expected_items,v_source_key,v_keys,v_set_hash) returning id into v_menu_id;

 if v_make_current and cardinality(v_supersede) > 0 then
  update public.menus set superseded_by=v_menu_id where id = any(v_supersede);
 end if;

 for v_section in select * from jsonb_array_elements(coalesce(p_sections,'[]'::jsonb)) loop
  insert into public.menu_sections(menu_id,section_name,section_type,section_position) values(v_menu_id,nullif(v_section->>'section_name',''),coalesce(nullif(v_section->>'section_type',''),'unsectioned'),(v_section->>'section_position')::int) returning id into v_section_id;
  for v_item in select * from jsonb_array_elements(coalesce(v_section->'items','[]'::jsonb)) loop
   insert into public.menu_items(section_id,item_name,raw_text,item_position,item_type,price,price_text,currency) values(v_section_id,coalesce(nullif(v_item->>'item_name',''),'(unnamed)'),nullif(v_item->>'raw_text',''),(v_item->>'item_position')::int,coalesce(nullif(v_item->>'item_type',''),'unknown'),(nullif(v_item->>'price',''))::numeric,nullif(v_item->>'price_text',''),coalesce(nullif(v_item->>'currency',''),'USD')) returning id into v_item_id;
   v_items:=v_items+1;
   v_has_brands:=jsonb_array_length(coalesce(v_item->'brands','[]'::jsonb))>0;
   for v_brand in select * from jsonb_array_elements(coalesce(v_item->'brands','[]'::jsonb)) loop
    v_brand_id:=null;
    if nullif(v_brand->>'raw_brand_text','') is not null then select b.id into v_brand_id from public.brands b where lower(b.brand_name)=lower(trim(v_brand->>'raw_brand_text')) and b.merged_into_brand_id is null limit 1;end if;
    insert into public.menu_item_brands(menu_item_id,brand_id,raw_brand_text,spirit_category,expression,brand_named,match_confidence) values(v_item_id,v_brand_id,nullif(v_brand->>'raw_brand_text',''),coalesce(nullif(v_brand->>'spirit_category',''),'unknown'),nullif(v_brand->>'expression',''),coalesce((v_brand->>'brand_named')::boolean,nullif(v_brand->>'raw_brand_text','') is not null),(nullif(v_brand->>'match_confidence',''))::numeric);
    v_brands:=v_brands+1;
   end loop;
   if not v_has_brands then
    select cr.base_spirit_norm into v_cat from public.cocktail_reference cr where lower(cr.cocktail_name)=lower(trim(coalesce(v_item->>'item_name',''))) or lower(trim(coalesce(v_item->>'item_name','')))=any(select lower(a) from unnest(cr.aliases) a) limit 1;
    if v_cat is not null then insert into public.menu_item_brands(menu_item_id,brand_id,raw_brand_text,spirit_category,brand_named,match_confidence) values(v_item_id,null,null,v_cat,false,0.700);v_brands:=v_brands+1;v_inferred:=v_inferred+1;end if;
   end if;
  end loop;
 end loop;
 if v_items<>v_expected_items then raise exception 'menu item count mismatch';end if;
 update public.menus set item_count=v_items where id=v_menu_id;
 return jsonb_build_object('status',case when v_make_current then 'created' else 'created_alternate' end,
   'menu_id',v_menu_id,'menu_code',v_menu_code,'sections',jsonb_array_length(coalesce(p_sections,'[]'::jsonb)),'items',v_items,
   'brand_references',v_brands,'inferred_from_cocktail_reference',v_inferred,'is_current',v_make_current,
   'superseded',to_jsonb(v_supersede),'reason',v_reason,'source_key',v_source_key);
end $function$;

-- The 10-arg overload cannot be called at all today (any 10-argument call is ambiguous with the 15-arg version and
-- fails with 42725 'is not unique'), no function or Edge function calls it, and the submit-menu Edge function passes
-- p_needs_vision_pass, so it already uses the 15-arg version. Drop it; its definition is saved for rollback.
drop function if exists public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb);

-- ---------- D. promote_clean_menu_batch: one group per (page, account); mark exactly the rows used ----------
create or replace function public.promote_clean_menu_batch(p_pages integer default 10)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public', 'extensions', 'pg_temp'
as $function$
declare v_page text;v_account text;v_format text;v_sections jsonb;v_hash text;v_result jsonb;v_status text;v_ids bigint[];
 v_created integer:=0;v_alternate integer:=0;v_duplicate integer:=0;v_held integer:=0;v_skipped integer:=0;v_failed integer:=0;v_errors jsonb:='[]'::jsonb;
begin
 if not pg_try_advisory_xact_lock(830927,2) then return jsonb_build_object('status','already_running'); end if;
 -- at most 5 pages per call: each promotion holds its venues' account row locks until the transaction ends
 p_pages:=least(5,greatest(1,coalesce(p_pages,1)));
 for v_page, v_account in
   select menu_page_url, account_id from public.v_menu_staging_promotion_candidates
   group by menu_page_url, account_id order by min(id) limit p_pages
 loop
  begin
   select array_agg(id order by id), coalesce(max(menu_format) filter (where menu_format in ('html','pdf','image')),'other')
     into v_ids, v_format
     from public.v_menu_staging_promotion_candidates where menu_page_url=v_page and account_id=v_account;
   with rows as (select * from public.staging_menu_extract where id = any(v_ids) and item_type<>'summary'),
   section_keys as (select section_name,min(id) as first_id from rows group by section_name),
   section_payloads as (select sk.first_id,jsonb_build_object('section_name',sk.section_name,'section_type',public.menu_section_type_for_promotion(sk.section_name),'section_position',row_number() over(order by sk.first_id),'items',(select coalesce(jsonb_agg(jsonb_build_object('item_name',r.item_name,'item_position',r.item_pos,'item_type',case when r.item_type='cocktail' then 'cocktail' when r.item_type='spirit_pour' then 'spirit_pour' else 'other' end,'price',r.item_price,'brands',case when nullif(btrim(r.spirit_brands),'') is not null then jsonb_build_array(jsonb_build_object('raw_brand_text',r.spirit_brands,'brand_named',true)) else '[]'::jsonb end) order by r.id),'[]'::jsonb) from(select rr.*,row_number() over(order by rr.id) as item_pos from rows rr where rr.section_name is not distinct from sk.section_name) r)) as payload from section_keys sk)
   select coalesce(jsonb_agg(payload order by first_id),'[]'::jsonb) into v_sections from section_payloads;
   if jsonb_array_length(v_sections)=0 then
    update public.staging_menu_extract set promoted_at=now(), promotion_status='skipped_empty' where id = any(v_ids);
    v_skipped:=v_skipped+1; continue;
   end if;
   v_hash:=encode(extensions.digest(convert_to(v_account||'|'||v_page||'|'||v_sections::text,'UTF8'),'sha256'),'hex');
   v_result:=public.submit_menu(v_account,'NBCC-FIRECRAWL-MENUS',v_page,null,v_format,'unknown','promotion from quality-filtered staging',null,v_hash,v_sections,null,null,null,null,false);
   v_status:=coalesce(v_result->>'status','created');
   update public.staging_menu_extract
      set promoted_at = now(),
          promotion_status = case v_status when 'created' then 'promoted'
                                           when 'created_alternate' then 'promoted_alternate'
                                           when 'subset_of_current' then 'held_subset_of_current'
                                           else v_status end,
          promoted_menu_id = nullif(v_result->>'menu_id','')::uuid
    where id = any(v_ids);
   if v_status='created' then v_created:=v_created+1;
   elsif v_status='created_alternate' then v_alternate:=v_alternate+1;
   elsif v_status='subset_of_current' then v_held:=v_held+1;
   else v_duplicate:=v_duplicate+1; end if;
  exception when others then v_failed:=v_failed+1;v_errors:=v_errors||jsonb_build_array(jsonb_build_object('page',v_page,'account',v_account,'sqlstate',SQLSTATE,'error',SQLERRM));
  end;
 end loop;
 return jsonb_build_object('created',v_created,'alternate',v_alternate,'duplicate',v_duplicate,'held_subset',v_held,'skipped',v_skipped,'failed',v_failed,'errors',v_errors,'remaining',(select count(*) from public.v_menu_staging_promotion_candidates));
end $function$;

-- ---------- E. extraction save: do not re-stage an item set a sibling page of the venue already staged ----------
create or replace function public.phg_save_menu_candidate_extraction(p_candidate_id bigint, p_claimed_at timestamp with time zone, p_run_owner uuid, p_items jsonb, p_source_text text, p_method text, p_source_format text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public', 'pg_temp'
as $function$
declare c public.menu_source_candidates%rowtype; v_hash text; v_scope text; n integer; v_set text; v_dup bigint;
begin
 if not exists(select 1 from public.phg_menu_worker_leases where lane='candidate_extraction' and owner=p_run_owner and lease_until>now()) then return jsonb_build_object('status','stale_run'); end if;
 if jsonb_typeof(p_items)<>'array' or jsonb_array_length(p_items)>350 or p_source_text is null or length(p_source_text)>2000000 or p_source_format not in ('html','pdf','image') then raise exception 'invalid extraction payload'; end if;
 select * into c from public.menu_source_candidates where id=p_candidate_id for update;
 if not found or c.status<>'processing' or c.last_attempt_at is distinct from p_claimed_at then return jsonb_build_object('status','stale_claim'); end if;
 v_hash:=encode(sha256(convert_to(p_source_text,'UTF8')),'hex');
 insert into public.menu_extraction_sources(candidate_id,content_hash,source_url,source_format,extraction_method,source_text) values(c.id,v_hash,c.source_url,p_source_format,p_method,p_source_text) on conflict(candidate_id,content_hash) do nothing;
 n:=jsonb_array_length(p_items);
 if n=0 then
   update public.menu_source_candidates set status='review',last_error='No confident priced items parsed; source text archived for follow-up',extraction_next_retry_at=null where id=c.id;
   return jsonb_build_object('status','review','items',0,'source_archived',true);
 end if;
 if exists(select 1 from jsonb_array_elements(p_items) x where nullif(btrim(x->>'item_name'),'') is null or length(x->>'item_name')>300 or jsonb_typeof(x->'item_price')<>'number' or (x->>'item_price')::numeric<1 or (x->>'item_price')::numeric>1000 or coalesce(x->>'item_type','') not in ('cocktail','beer','wine','spirit_pour','other')) then raise exception 'invalid menu item'; end if;
 -- Account lock first, so two workers saving sibling pages of one venue cannot both miss each other.
 perform 1 from public.accounts where account_id=c.account_id for update;
 v_set := public.phg_menu_key_set_hash(public.phg_menu_extract_item_keys(p_items));
 -- the sibling must be an original (not itself a duplicate) whose items are still staged
 select s.id into v_dup from public.menu_source_candidates s
  where s.account_id=c.account_id and s.id<>c.id and s.item_set_hash=v_set and s.source_url is distinct from c.source_url
    and s.duplicate_of_candidate_id is null
    and exists (select 1 from public.staging_menu_extract x where x.account_id=s.account_id and x.menu_page_url=s.source_url and x.superseded_at is null)
  order by s.id limit 1;
 if v_dup is not null then
   -- this page's own earlier staged set is stale now; retire it so it is not promoted
   update public.staging_menu_extract set superseded_at=now(), superseded_reason='duplicate_item_set_of_sibling'
    where account_id=c.account_id and menu_page_url=c.source_url and superseded_at is null;
   -- no item_set_hash on a duplicate, so later pages never match an empty duplicate
   update public.menu_source_candidates
      set status='review', content_hash=v_hash, item_set_hash=null, duplicate_of_candidate_id=v_dup,
          last_error='Same priced items as candidate '||v_dup||' of this venue; not re-staged (source text archived)',
          extraction_next_retry_at=null
    where id=c.id;
   return jsonb_build_object('status','review','items',0,'duplicate_of',v_dup,'source_archived',true);
 end if;
 update public.staging_menu_extract set superseded_at=now(), superseded_reason='same_page_recapture' where account_id=c.account_id and menu_page_url=c.source_url and superseded_at is null;
 insert into public.staging_menu_extract(menu_page_url,menu_format,account_id,item_type,item_name,item_price,section_name,spirit_brands,notes)
 select c.source_url,p_source_format,c.account_id,x->>'item_type',x->>'item_name',(x->>'item_price')::numeric,nullif(x->>'section_name',''),nullif(x->>'spirit_brands',''),x->>'notes' from jsonb_array_elements(p_items) x;
 v_scope:=public.classify_menu_page(c.account_id,c.source_url);
 if v_scope in ('beverage','mixed') then
   update public.accounts set menu_status='extracted',menu_attempt_note='verified source extraction; '||n||' priced items',menu_last_attempt_at=now(),menu_finalized_at=now() where account_id=c.account_id;
   update public.staging_menu_extract set quality_status=case when item_scope='beverage' and item_type<>'summary' then 'promotion_ready' else 'hold_review' end,quality_reason='Page-scoped source extraction; beverage evidence required for promotion',quality_checked_at=now() where account_id=c.account_id and menu_page_url=c.source_url and superseded_at is null and promoted_at is null;
 end if;
 update public.menu_source_candidates set content_hash=v_hash,item_set_hash=v_set,last_error=null,extraction_next_retry_at=case when v_scope='food_candidate' then now()+interval '7 days' else null end where id=c.id;
 return jsonb_build_object('status',case when v_scope in ('beverage','mixed') then 'extracted' else 'review' end,'scope',v_scope,'items',n,'source_archived',true);
end $function$;

revoke all on function public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb,text,text,text,text,boolean) from public, anon, authenticated;
revoke all on function public.promote_clean_menu_batch(integer) from public, anon, authenticated;
revoke all on function public.phg_save_menu_candidate_extraction(bigint,timestamp with time zone,uuid,jsonb,text,text,text) from public, anon, authenticated;
$rehearse_f1$;
  EXCEPTION WHEN others THEN 
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
    RAISE EXCEPTION 'REHEARSAL %', r || jsonb_build_object('stage','file1','sqlstate',e_state,'error',e_msg,'detail',e_det,'context',right(e_ctx, 600),'ms',round(extract(epoch from clock_timestamp()-t0)*1000));
  END;
  r := r || jsonb_build_object('file1_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  t0 := clock_timestamp();
  BEGIN
    a := a || jsonb_build_object('backup_rows', (select count(*) from public.phg_backup_function_defs_20260927),
       'backup_sigs', (select jsonb_agg(signature order by signature) from public.phg_backup_function_defs_20260927),
       'backup_service_role_can_insert', has_table_privilege('service_role','public.phg_backup_function_defs_20260927','INSERT'),
       'backup_service_role_can_select', has_table_privilege('service_role','public.phg_backup_function_defs_20260927','SELECT'),
       'submit_menu_10arg_exists', to_regprocedure('public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb)') is not null,
       'promote_clamp_5', (select prosrc ~ 'least\(5,' from pg_proc where oid='public.promote_clean_menu_batch(integer)'::regprocedure),
       'multi_current_global_before', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x));
    select id, evidence_url into cur_id, orig_url from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('account', acct, 'orig_current', cur_id,
       'orig_distinct_keys', cardinality(public.phg_menu_item_keys(cur_id)), 'orig_bev', public.phg_menu_bev_count(cur_id));
    with it as (select s.id sid, i.*, row_number() over (order by s.section_position, s.id, i.item_position, i.id) rn
                  from public.menu_sections s join public.menu_items i on i.section_id=s.id where s.menu_id=cur_id)
    select jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',it.price,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)) order by s.section_position, s.id),
           jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',case when it.rn<=3 then coalesce(it.price,0)+1 else it.price end,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)) order by s.section_position, s.id),
           jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',it.price,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)
                     || case when s.section_position = (select min(section_position) from public.menu_sections where menu_id=cur_id)
                             then '[{"item_name":"Rehearsal Extra Pour","item_type":"spirit_pour","price":14}]'::jsonb else '[]'::jsonb end) order by s.section_position, s.id)
      into secs, secs2, secs9 from public.menu_sections s where s.menu_id=cur_id;
    with it as (select s.id sid, i.*, row_number() over (order by s.section_position, s.id, i.item_position, i.id) rn
                  from public.menu_sections s join public.menu_items i on i.section_id=s.id where s.menu_id=cur_id)
    select jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',case when it.rn<=3 then coalesce(it.price,0)+1 when it.rn=5 then coalesce(it.price,0)+2 else it.price end,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)) order by s.section_position, s.id)
      into secs10 from public.menu_sections s where s.menu_id=cur_id;

    -- 1 exact copy of the current menu from another URL -> duplicate, nothing inserted
    res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy1',null,'html','unknown','rehearsal',null,md5('reh1'||clock_timestamp()::text),secs,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s1_exact_copy_other_url', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''duplicate_of_current'' and cur_now=cur_id', 'pass', coalesce((res->>'status'='duplicate_of_current' and cur_now=cur_id), false)));
    -- all live menus are < 7 days old (created 2026-09-25..27); age this one so the near-identical rule (not damping) applies
    update public.menus set created_at = created_at - interval '30 days' where id = cur_id;
    -- 2 same items, 3 prices changed, another URL, current menu 30 days old -> replaces
    res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy2',null,'html','unknown','rehearsal',null,md5('reh2'||clock_timestamp()::text),secs2,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s2_three_prices_changed_other_url', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created'' and res->>''reason'' in (''newer_near_identical_capture'',''price_enrichment_other_source'') and cur_now<>cur_id', 'pass', coalesce((res->>'status'='created' and res->>'reason' in ('newer_near_identical_capture','price_enrichment_other_source') and cur_now<>cur_id), false)));
    select id into cur2 from public.menus where account_id=acct and is_current;
    -- 9 flip-flop damping: the original page again (original prices). Current (copy2) is minutes old and from another
    --   source; the capture is only near-identical -> alternate, current stays copy2
    res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS',orig_url,null,'html','unknown','rehearsal',null,md5('reh9'||clock_timestamp()::text),secs,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s9_flipflop_original_page_again', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status'' in (''created_alternate'',''duplicate_item_set'') and coalesce(res->>''reason'',''alternate_near_identical_recent_other_source'')=''alternate_near_identical_recent_other_source'' and cur_now=cur2', 'pass', coalesce((res->>'status' in ('created_alternate','duplicate_item_set') and coalesce(res->>'reason','alternate_near_identical_recent_other_source')='alternate_near_identical_recent_other_source' and cur_now=cur2), false)));
    -- 9b control: the original page with ONE MORE item (larger) still replaces a recent current menu
    BEGIN
      res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS',orig_url,null,'html','unknown','rehearsal',null,md5('reh9b'||clock_timestamp()::text),secs9,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s9b_flipflop_control_larger_replaces', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created'' and cur_now<>cur2', 'pass', coalesce((res->>'status'='created' and cur_now<>cur2), false)));
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 9b';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- 3 ?item= page on the current URL with 2 new items -> alternate
    res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy2?item=abc',null,'html','unknown','rehearsal',null,md5('reh3'||clock_timestamp()::text),'[{"section_name":"Order","section_type":"unsectioned","section_position":1,"items":[{"item_name":"Rehearsal Item A","item_type":"other","price":9},{"item_name":"Rehearsal Item B","item_type":"other","price":10}]}]'::jsonb,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s3_item_page_same_url', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created_alternate'' and res->>''reason''=''alternate_item_page'' and cur_now=cur2', 'pass', coalesce((res->>'status'='created_alternate' and res->>'reason'='alternate_item_page' and cur_now=cur2), false)));
    -- 4 same URL as current, 10 items (5 current + 5 new) < half of 33 -> alternate
    select jsonb_build_array(jsonb_build_object('section_name','Partial','section_type','unsectioned','section_position',1,'items',
             (select jsonb_agg(x) from (
                (select jsonb_build_object('item_name',i.item_name,'item_type','other','price',i.price) x
                   from public.menu_sections s join public.menu_items i on i.section_id=s.id where s.menu_id=cur2 order by i.id limit 5)
                union all
                select jsonb_build_object('item_name','Rehearsal Partial '||g,'item_type','other','price',5+g) from generate_series(1,5) g) q)))
      into secs4;
    res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy2',null,'html','unknown','rehearsal',null,md5('reh4'||clock_timestamp()::text),secs4,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s4_partial_same_url', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created_alternate'' and res->>''reason''=''alternate_partial_recapture'' and cur_now=cur2', 'pass', coalesce((res->>'status'='created_alternate' and res->>'reason'='alternate_partial_recapture' and cur_now=cur2), false)));
    -- 5 another URL, 2 food items -> alternate
    res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/food',null,'html','unknown','rehearsal',null,md5('reh5'||clock_timestamp()::text),'[{"section_name":"Food","section_type":"unsectioned","section_position":1,"items":[{"item_name":"Rehearsal Fries","item_type":"other","price":7},{"item_name":"Rehearsal Burger","item_type":"other","price":15}]}]'::jsonb,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s5_small_food_other_url', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created_alternate'' and res->>''reason''=''alternate_smaller_other_source'' and cur_now=cur2', 'pass', coalesce((res->>'status'='created_alternate' and res->>'reason'='alternate_smaller_other_source' and cur_now=cur2), false)));
    -- 6 zero items -> ignored
    res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/empty',null,'html','unknown','rehearsal',null,md5('reh6'||clock_timestamp()::text),'[]'::jsonb,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s6_zero_items', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''empty_capture_ignored'' and cur_now=cur2', 'pass', coalesce((res->>'status'='empty_capture_ignored' and cur_now=cur2), false)));
    -- 10 (C1, round 4) SAME source item page (copy2?item=full, key = copy2), same size as the real-page current menu,
    --    one price changed: before round 4 it replaced the real page; now it is an alternate and the real page stays
    BEGIN
      res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy2?item=full',null,'html','unknown','rehearsal',null,md5('reh10'||clock_timestamp()::text),secs10,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s10_same_source_item_page_same_size', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created_alternate'' and res->>''reason''=''alternate_item_page'' and cur_now=cur2', 'pass', coalesce((res->>'status'='created_alternate' and res->>'reason'='alternate_item_page' and cur_now=cur2), false)));
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 10';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- 10b control: the same item page with ONE MORE item (strictly larger) replaces
    BEGIN
      res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy2?item=full',null,'html','unknown','rehearsal',null,md5('reh10b'||clock_timestamp()::text),secs9,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s10b_same_source_item_page_larger_replaces', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created'' and cur_now<>cur2', 'pass', coalesce((res->>'status'='created' and cur_now<>cur2), false)));
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 10b';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- 11 (round 5, C1) a REAL page from another source behind an ITEM-PAGE current menu that is minutes old: not damped.
    --    The current menu (copy2) is turned into an item page of another source (/order/<menu>/<cat>/<item>).
    BEGIN
      update public.menus set evidence_url = 'https://rehearsal.example.com/order/main/wine/item-1',
             source_key = public.phg_menu_source_key('https://rehearsal.example.com/order/main/wine/item-1') where id = cur2;
      a := a || jsonb_build_object('s11_setup', jsonb_build_object('current_is_item_page', (select public.phg_menu_url_is_item_page(evidence_url) from public.menus where id = cur2),
             'current_age_minutes', (select round(extract(epoch from now() - created_at) / 60) from public.menus where id = cur2)));
      -- 11: the same items (original prices, 30 of 33 keys shared), same (items, drinks): Step 2's tie rule -> replaces
      BEGIN
        res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/drinks',null,'html','unknown','rehearsal',null,md5('reh11'||clock_timestamp()::text),secs,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s11_real_page_over_item_page_tie', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created'' and res->>''reason''=''real_page_over_item_page'' and cur_now<>cur2', 'pass', coalesce((res->>'status'='created' and res->>'reason'='real_page_over_item_page' and cur_now<>cur2), false)));
        RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 11';
      EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
      END;
      -- 11b: the damping condition itself: same items but one wine section re-typed 'unsectioned' (28 drinks < 33), so
      --     only the near-identical rule applies. Round 4 damped it (alternate_near_identical_recent_other_source).
      secs11 := jsonb_set(secs, '{1,section_type}', '"unsectioned"');
      BEGIN
        res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/drinks',null,'html','unknown','rehearsal',null,md5('reh11b'||clock_timestamp()::text),secs11,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s11b_real_page_not_damped_behind_item_page', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created'' and res->>''reason''=''newer_near_identical_capture'' and cur_now<>cur2', 'pass', coalesce((res->>'status'='created' and res->>'reason'='newer_near_identical_capture' and cur_now<>cur2), false)));
        a := jsonb_set(a, '{s11b_real_page_not_damped_behind_item_page,capture_bev}', to_jsonb(public.phg_menu_payload_bev_count(secs11)));
        RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 11b';
      EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
      END;
      -- 11c control: the same capture behind a REAL-page current menu of another source (copy2 URL restored) is damped
      update public.menus set evidence_url = 'https://rehearsal.example.com/copy2', source_key = 'rehearsal.example.com/copy2' where id = cur2;
      BEGIN
        res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/drinks',null,'html','unknown','rehearsal',null,md5('reh11c'||clock_timestamp()::text),secs11,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s11c_control_real_page_current_still_damped', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created_alternate'' and res->>''reason''=''alternate_near_identical_recent_other_source'' and cur_now=cur2', 'pass', coalesce((res->>'status'='created_alternate' and res->>'reason'='alternate_near_identical_recent_other_source' and cur_now=cur2), false)));
        RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 11c';
      EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
      END;
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 11 setup';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- 12 (round 5, SF-D) item page over an ITEM-PAGE current menu of the same source (key copy2): the current menu becomes
    --    copy2?item=a. A sibling item page copy2?item=b, same size, one price changed -> alternate (round 4: replaced).
    BEGIN
      update public.menus set evidence_url = 'https://rehearsal.example.com/copy2?item=a' where id = cur2;
      a := a || jsonb_build_object('s12_setup', jsonb_build_object('current_is_item_page', (select public.phg_menu_url_is_item_page(evidence_url) from public.menus where id = cur2),
             'current_key', (select coalesce(source_key, public.phg_menu_source_key(evidence_url)) from public.menus where id = cur2),
             'capture_key', public.phg_menu_source_key('https://rehearsal.example.com/copy2?item=b')));
      BEGIN
        res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy2?item=b',null,'html','unknown','rehearsal',null,md5('reh12'||clock_timestamp()::text),secs10,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s12_sibling_item_page_same_size', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created_alternate'' and res->>''reason''=''alternate_item_page'' and cur_now=cur2', 'pass', coalesce((res->>'status'='created_alternate' and res->>'reason'='alternate_item_page' and cur_now=cur2), false)));
        RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 12';
      EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
      END;
      -- 12b exact-URL exemption: the SAME item page (copy2?item=a) re-captured with the changed price -> replaces
      BEGIN
        res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy2?item=a',null,'html','unknown','rehearsal',null,md5('reh12b'||clock_timestamp()::text),secs10,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s12b_same_item_page_url_recapture_replaces', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created'' and res->>''reason''=''same_source_recapture'' and cur_now<>cur2', 'pass', coalesce((res->>'status'='created' and res->>'reason'='same_source_recapture' and cur_now<>cur2), false)));
        RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 12b';
      EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
      END;
      -- 12c control: the sibling item page with one more item (strictly larger) -> replaces
      BEGIN
        res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy2?item=b',null,'html','unknown','rehearsal',null,md5('reh12c'||clock_timestamp()::text),secs9,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s12c_sibling_item_page_larger_replaces', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created'' and cur_now<>cur2', 'pass', coalesce((res->>'status'='created' and cur_now<>cur2), false)));
        RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 12c';
      EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
      END;
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 12 setup';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- M1 (round 5): drinks items are DISTINCT keys, in the payload count and the stored count alike; submit_menu lock_timeout
    a := a || jsonb_build_object('m1_distinct_drinks', jsonb_build_object(
       'payload_same_line_twice', public.phg_menu_payload_bev_count('[{"section_type":"cocktails","items":[{"item_name":"Rehearsal Mule","price":9},{"item_name":"Rehearsal Mule","price":9},{"item_name":"Rehearsal Sour","price":9}]}]'::jsonb),
       'stored_current', public.phg_menu_bev_count(cur2),
       'stored_rows_in_drinks_sections', (select count(*) from public.menu_sections s join public.menu_items i on i.section_id = s.id where s.menu_id = cur2 and s.section_type in ('cocktails','wine','beer','spirits')),
       'payload_of_current', public.phg_menu_payload_bev_count(secs2)),
       'submit_menu_proconfig', (select proconfig from pg_proc where oid = 'public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb,text,text,text,text,boolean)'::regprocedure));
    a := jsonb_set(a, '{m1_distinct_drinks,pass}', to_jsonb((a->'m1_distinct_drinks'->>'payload_same_line_twice')::int = 2
       and (a->'m1_distinct_drinks'->>'stored_current')::int = (a->'m1_distinct_drinks'->>'payload_of_current')::int
       and (a->>'submit_menu_proconfig') ~ 'lock_timeout=5s'));
    -- 7 a missing price overlaps a priced item (both ways); price-adds helper
    a := a || jsonb_build_object('s7_overlap',
       jsonb_build_object('capture_noprice_vs_current_priced', public.phg_menu_keys_overlap(array[public.phg_menu_item_key('Rehearsal Negroni', null)], array[public.phg_menu_item_key('Rehearsal Negroni', 12)]),
                          'reverse', public.phg_menu_keys_overlap(array[public.phg_menu_item_key('Rehearsal Negroni', 12)], array[public.phg_menu_item_key('Rehearsal Negroni', null)]),
                          'different_prices', public.phg_menu_keys_overlap(array['rehearsal negroni|12'], array['rehearsal negroni|13']),
                          'price_adds_capture_priced_vs_current_unpriced', public.phg_menu_keys_price_adds(array['rehearsal negroni|12'], array['rehearsal negroni|']),
                          'price_adds_reverse', public.phg_menu_keys_price_adds(array['rehearsal negroni|'], array['rehearsal negroni|12']),
                          'price_adds_when_current_has_both', public.phg_menu_keys_price_adds(array['rehearsal negroni|12'], array['rehearsal negroni|','rehearsal negroni|12'])));
    a := jsonb_set(a, '{s7_overlap,pass}', to_jsonb(
          (a->'s7_overlap'->>'capture_noprice_vs_current_priced')::int = 1 and (a->'s7_overlap'->>'reverse')::int = 1
      and (a->'s7_overlap'->>'different_prices')::int = 0 and (a->'s7_overlap'->>'price_adds_capture_priced_vs_current_unpriced')::int = 1
      and (a->'s7_overlap'->>'price_adds_reverse')::int = 0 and (a->'s7_overlap'->>'price_adds_when_current_has_both')::int = 0));
    -- 8 price enrichment: the current menu (copy2) lost one price (stored NULL, item_keys refreshed); the capture has it
    select i.id into item_x from public.menu_sections s join public.menu_items i on i.section_id=s.id
     where s.menu_id=cur2 and i.price is not null order by s.section_position, s.id, i.item_position, i.id offset 5 limit 1;
    update public.menu_items set price = null where id = item_x;
    update public.menus set item_keys = public.phg_menu_item_keys(cur2), item_set_hash = public.phg_menu_key_set_hash(public.phg_menu_item_keys(cur2)) where id = cur2;
    a := a || jsonb_build_object('s8_setup', jsonb_build_object('item_without_price', item_x,
       'overlap_capture_vs_current', public.phg_menu_keys_overlap(public.phg_menu_payload_item_keys(secs2), public.phg_menu_item_keys(cur2)),
       'capture_keys', cardinality(public.phg_menu_payload_item_keys(secs2)),
       'price_adds', public.phg_menu_keys_price_adds(public.phg_menu_payload_item_keys(secs2), public.phg_menu_item_keys(cur2))));
    -- 8a same source (copy2): before round 3 this was 'duplicate_of_current'; now a same-source replacement
    BEGIN
      res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy2',null,'html','unknown','rehearsal',null,md5('reh8a'||clock_timestamp()::text),secs2,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s8a_price_enrichment_same_source', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created'' and res->>''reason''=''same_source_price_enrichment'' and cur_now<>cur2', 'pass', coalesce((res->>'status'='created' and res->>'reason'='same_source_price_enrichment' and cur_now<>cur2), false)));
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 8a';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- 8b another source, same size, current menu minutes old: not a duplicate, and damping does not hold back a price
    BEGIN
      res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/copy8',null,'html','unknown','rehearsal',null,md5('reh8b'||clock_timestamp()::text),secs2,null,null,null,null,false);
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('s8b_price_enrichment_other_source', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x), 'expect', 'res->>''status''=''created'' and res->>''reason''=''price_enrichment_other_source'' and cur_now<>cur2', 'pass', coalesce((res->>'status'='created' and res->>'reason'='price_enrichment_other_source' and cur_now<>cur2), false)));
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 8b';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    a := a || jsonb_build_object('final_acct_menus', (select jsonb_agg(jsonb_build_object('url',evidence_url,'is_current',is_current,'reason',superseded_reason,'n',cardinality(item_keys)) order by created_at, id) from public.menus where account_id=acct),
       'multi_current_global_end', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x));
    RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback scenarios';
  EXCEPTION
    WHEN sqlstate 'P0099' THEN NULL;
    WHEN others THEN 
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      a := a || jsonb_build_object('ERROR_A', jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx), 'pass', false));
  END;
  r := r || jsonb_build_object('A', a, 'A_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  RAISE EXCEPTION 'REHEARSAL %', r;
END
$rehearse_main$;
