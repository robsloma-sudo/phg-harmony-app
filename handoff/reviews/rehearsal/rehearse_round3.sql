-- ===== block A (run on its own; ends in RAISE EXCEPTION, so everything rolls back) =====
DO $rehearse_main$
DECLARE
  r jsonb := '{}'; a jsonb := '{}'; b jsonb := '{}'; c jsonb := '{}'; v jsonb; res jsonb;
  t0 timestamptz; t1 timestamptz; acct text := 'ACC-CO-LED-03-25486'; orig_url text;
  cur_id uuid; cur2 uuid; cur_now uuid; secs jsonb; secs2 jsonb; secs4 jsonb; secs9 jsonb; items jsonb; item_x uuid;
  rem int; calls jsonb; lease_owner uuid := gen_random_uuid(); claimed timestamptz := clock_timestamp();
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
--    replaced the venue's menu; the last page promoted won. 185 venues lost a larger pre-existing
--    menu; 7,429 menus were created today from only ~2,500 distinct item sets.
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
-- Apply with cron 7 (promotion) and 13 (extraction) PAUSED. Data repair is a separate script.
-- Apply through the runbook (apply_migration, or psql -1 -f), in order: this file, then 20260927191000. Not with
-- `supabase db push`: newer migrations (20260927200000 and later) are already applied, so db push would refuse or
-- skip these out-of-order files.

set local lock_timeout = '3s';

-- ---------- 0. save the live definitions this migration replaces (rollback: phg_rollback_function_defs_20260927) ----------
create table if not exists public.phg_backup_function_defs_20260927 (
  signature text primary key, definition text not null, acl text, saved_at timestamptz not null default now());
alter table public.phg_backup_function_defs_20260927 enable row level security;
revoke all on public.phg_backup_function_defs_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_function_defs_20260927 from service_role;
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
revoke all on function public.phg_rollback_function_defs_20260927() from public, anon, authenticated;

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

-- Drinks item count of a payload: typed drinks items plus every item in a drinks section.
create or replace function public.phg_menu_payload_bev_count(p_sections jsonb)
returns integer language sql immutable set search_path = '' as $$
  select count(*)::int
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

-- Drinks item count of a stored menu (beer / wine are item_type 'other' inside typed sections).
create or replace function public.phg_menu_bev_count(p_menu_id uuid)
returns integer language sql stable set search_path = '' as $$
  select count(*)::int
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
 for c in select m.id, coalesce(m.source_key, public.phg_menu_source_key(m.evidence_url)) as source_key, m.item_keys, m.created_at
            from public.menus m where m.account_id=p_account_id and m.is_current
           order by m.created_at desc, m.id for update loop
  c_keys := coalesce(c.item_keys, public.phg_menu_item_keys(c.id));
  c_n    := cardinality(c_keys);
  v_ov   := public.phg_menu_keys_overlap(v_keys, c_keys);
  -- items whose price the capture supplies and the current menu lacks: never a duplicate (price enrichment)
  v_adds := public.phg_menu_keys_price_adds(v_keys, c_keys);
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
   if v_itemish and c_n > 0 and not (v_n >= c_n and v_ov >= ceil(c_dup_ratio * c_n)) then
    -- an item page shares the menu's key (?item= is stripped) but is not a fuller copy of it
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
   c_bev := public.phg_menu_bev_count(c.id);
   if v_itemish and c_n > 0 then
    v_make_current := false; v_alt_of := c.id; v_reason := 'alternate_item_page';
   elsif (v_n, v_bev) > (c_n, c_bev) then
    v_supersede := v_supersede || c.id;
    v_reason := coalesce(v_reason, case when c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) then 'contained_in_larger_capture' else 'larger_beverage_capture' end);
   elsif v_n >= c_n and c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) and v_adds = 0
         and c.created_at > now() - c_damping then
    -- flip-flop damping: two pages of the same menu must not keep swapping current. The current menu came from
    -- another source less than 7 days ago and this capture is only near-identical (not larger): keep it as an alternate.
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

-- ===== block B (run on its own; ends in RAISE EXCEPTION, so everything rolls back) =====
DO $rehearse_main$
DECLARE
  r jsonb := '{}'; a jsonb := '{}'; b jsonb := '{}'; c jsonb := '{}'; v jsonb; res jsonb;
  t0 timestamptz; t1 timestamptz; acct text := 'ACC-CO-LED-03-25486'; orig_url text;
  cur_id uuid; cur2 uuid; cur_now uuid; secs jsonb; secs2 jsonb; secs4 jsonb; secs9 jsonb; items jsonb; item_x uuid;
  rem int; calls jsonb; lease_owner uuid := gen_random_uuid(); claimed timestamptz := clock_timestamp();
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
--    replaced the venue's menu; the last page promoted won. 185 venues lost a larger pre-existing
--    menu; 7,429 menus were created today from only ~2,500 distinct item sets.
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
-- Apply with cron 7 (promotion) and 13 (extraction) PAUSED. Data repair is a separate script.
-- Apply through the runbook (apply_migration, or psql -1 -f), in order: this file, then 20260927191000. Not with
-- `supabase db push`: newer migrations (20260927200000 and later) are already applied, so db push would refuse or
-- skip these out-of-order files.

set local lock_timeout = '3s';

-- ---------- 0. save the live definitions this migration replaces (rollback: phg_rollback_function_defs_20260927) ----------
create table if not exists public.phg_backup_function_defs_20260927 (
  signature text primary key, definition text not null, acl text, saved_at timestamptz not null default now());
alter table public.phg_backup_function_defs_20260927 enable row level security;
revoke all on public.phg_backup_function_defs_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_function_defs_20260927 from service_role;
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
revoke all on function public.phg_rollback_function_defs_20260927() from public, anon, authenticated;

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

-- Drinks item count of a payload: typed drinks items plus every item in a drinks section.
create or replace function public.phg_menu_payload_bev_count(p_sections jsonb)
returns integer language sql immutable set search_path = '' as $$
  select count(*)::int
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

-- Drinks item count of a stored menu (beer / wine are item_type 'other' inside typed sections).
create or replace function public.phg_menu_bev_count(p_menu_id uuid)
returns integer language sql stable set search_path = '' as $$
  select count(*)::int
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
 for c in select m.id, coalesce(m.source_key, public.phg_menu_source_key(m.evidence_url)) as source_key, m.item_keys, m.created_at
            from public.menus m where m.account_id=p_account_id and m.is_current
           order by m.created_at desc, m.id for update loop
  c_keys := coalesce(c.item_keys, public.phg_menu_item_keys(c.id));
  c_n    := cardinality(c_keys);
  v_ov   := public.phg_menu_keys_overlap(v_keys, c_keys);
  -- items whose price the capture supplies and the current menu lacks: never a duplicate (price enrichment)
  v_adds := public.phg_menu_keys_price_adds(v_keys, c_keys);
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
   if v_itemish and c_n > 0 and not (v_n >= c_n and v_ov >= ceil(c_dup_ratio * c_n)) then
    -- an item page shares the menu's key (?item= is stripped) but is not a fuller copy of it
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
   c_bev := public.phg_menu_bev_count(c.id);
   if v_itemish and c_n > 0 then
    v_make_current := false; v_alt_of := c.id; v_reason := 'alternate_item_page';
   elsif (v_n, v_bev) > (c_n, c_bev) then
    v_supersede := v_supersede || c.id;
    v_reason := coalesce(v_reason, case when c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) then 'contained_in_larger_capture' else 'larger_beverage_capture' end);
   elsif v_n >= c_n and c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) and v_adds = 0
         and c.created_at > now() - c_damping then
    -- flip-flop damping: two pages of the same menu must not keep swapping current. The current menu came from
    -- another source less than 7 days ago and this capture is only near-identical (not larger): keep it as an alternate.
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
    EXECUTE $rehearse_f2$-- PHG-026 data repair (run AFTER 20260927190000_phg_menu_dedupe_one_current.sql, with cron 7 and 13 paused).
-- Reversible: every changed value is backed up first; phg_repair_20260927_rollback() undoes it safely (below).
-- Review round 2 version (2026-09-28): spec + safety round-1 findings addressed; see handoff/reviews/PHG-026_REVIEW_LOG.md.
-- Review round 3 version (2026-09-28): lock_timeout 5s; independent damaged-venue check (phg_repair_damaged_20260927);
--   item-page / pre-incident picks recorded; rollback skip test by backup membership + full restore of the promoted
--   menus' superseded_* values; Step 3 counts in one GROUP BY; release gate + monitor scripts.
--
-- HOW TO APPLY: as ONE transaction, after 20260927190000 and through the runbook (apply_migration, which runs the file
--   in one transaction, or `psql -1 -f`). Not `supabase db push` (newer migrations are already applied). If any lock
--   is not granted within 5 s, or any postcondition fails, the whole file rolls back and nothing has changed.
--
-- Counts, defined (they measure different things):
--   1,547 venues "touched" = have a menu created since 2026-09-27 00:00Z (the incident window).
--     185 of them also had a menu from before the incident.
--     119 of those 185 had a pre-incident menu with MORE distinct items than today's current one (the damaged venues).
--   Step 2 changes the current menu of ~350 touched venues (rehearsal 2026-09-28: 348 = 300 more items, 12 same items
--   and more drinks, 36 ties where a real page replaces an item page; exact figure is written to
--   phg_repair_run_20260927 at run time). Steps 1-2 hold SHARE ROW EXCLUSIVE on menus for ~8 s (rehearsed 7.7 s). Acceptance: 0 venues end with fewer distinct items than their largest
--   pre-incident menu, 0 venues with 2 current menus, 0 touched venues left without a current menu.
--
-- Step 1  backfill menus.source_key / item_keys / item_set_hash (12,229 rows, ~8 s)
-- Step 2  one best current menu per touched venue: distinct items desc, drinks items desc, real page before item page,
--         the menu that is ALREADY current on ties, then newest. Runs under a table lock; ends with checks that raise
--         (and roll the whole step back) if any rule is broken; then the one-current-menu rule becomes a unique index.
-- Step 3  staging rows re-staged from sibling pages with an identical item set -> superseded (batched function).
-- Step 4  menu_source_candidates.item_set_hash backfill (batched function) + its index (CONCURRENTLY, runbook).
-- Note: v_public_drinks, v_public_drinks_classified, v_menu_header_catalog and v_pipeline_status do not filter
--   superseded_at, so Step 3 does not change their counts (earlier wording claimed it did). It stops duplicates from
--   being promoted and from feeding the promotion-based views.

set local lock_timeout = '5s';   -- fail fast (and roll back everything) instead of queueing behind a long lock

-- ---------- Step 1 + 2 (one transaction) ----------
lock table public.menus in share row exclusive mode;   -- no submit_menu can interleave with the plan

update public.menus m
   set source_key    = public.phg_menu_source_key(m.evidence_url),
       item_keys     = k.keys,
       item_set_hash = public.phg_menu_key_set_hash(k.keys)
  from (select id, public.phg_menu_item_keys(id) as keys from public.menus) k
 where k.id = m.id and (m.item_keys is null or m.source_key is null);

create table if not exists public.phg_backup_menus_currency_20260927 as
  select id, account_id, is_current, superseded_by, superseded_reason, superseded_at, now() as backed_up_at
  from public.menus;
alter table public.phg_backup_menus_currency_20260927 enable row level security;
revoke all on public.phg_backup_menus_currency_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_menus_currency_20260927 from service_role;
create unique index if not exists phg_backup_menus_currency_20260927_id on public.phg_backup_menus_currency_20260927 (id);

-- Independent damaged-venue list, saved BEFORE Step 2 decides anything: touched venues whose largest pre-incident menu
-- has more distinct items than the menu current right now. Step 2 must bring every one back to at least that size.
create table if not exists public.phg_repair_damaged_20260927 as
with touched as (select distinct account_id from public.menus where created_at >= '2026-09-27 00:00:00+00')
select t.account_id,
       (select max(cardinality(coalesce(o.item_keys, '{}'::text[]))) from public.menus o
         where o.account_id = t.account_id and o.created_at < '2026-09-27 00:00:00+00') as old_max_n,
       (select max(cardinality(coalesce(c.item_keys, '{}'::text[]))) from public.menus c
         where c.account_id = t.account_id and c.is_current) as cur_n_before,
       now() as saved_at
  from touched t;
delete from public.phg_repair_damaged_20260927 where old_max_n is null or old_max_n <= coalesce(cur_n_before, 0);
alter table public.phg_repair_damaged_20260927 enable row level security;
revoke all on public.phg_repair_damaged_20260927 from anon, authenticated;

create table if not exists public.phg_repair_run_20260927 (
  step text primary key, ran_at timestamptz not null default now(), detail jsonb);
alter table public.phg_repair_run_20260927 enable row level security;
revoke all on public.phg_repair_run_20260927 from anon, authenticated;

create table if not exists public.phg_repair_plan_menus_20260927 as
with touched as (select distinct account_id from public.menus where created_at >= '2026-09-27 00:00:00+00'),
m as (
  select m.id, m.account_id, m.created_at, m.is_current as was_current, m.source_key,
         cardinality(coalesce(m.item_keys, '{}'::text[])) as n,
         public.phg_menu_bev_count(m.id) as bev,
         public.phg_menu_url_is_item_page(m.evidence_url) as itemish
  from public.menus m join touched using (account_id)
),
ranked as (
  select m.*, row_number() over (partition by account_id
                                 order by n desc, bev desc, itemish asc, was_current desc, created_at desc, id) as rk
  from m
)
select id, account_id, was_current, (rk = 1) as make_current,
       first_value(id) over (partition by account_id order by rk) as chosen_id, n, bev, itemish, created_at, source_key
from ranked;
alter table public.phg_repair_plan_menus_20260927 enable row level security;
revoke all on public.phg_repair_plan_menus_20260927 from anon, authenticated;

-- demote first, then promote: the one-current rule must hold row by row
update public.menus m
   set is_current = false, superseded_by = p.chosen_id,
       superseded_reason = 'repair_20260927_best_single_menu', superseded_at = now()
  from public.phg_repair_plan_menus_20260927 p
 where p.id = m.id and m.is_current and not p.make_current;
update public.menus m
   set is_current = true, superseded_by = null, superseded_reason = null, superseded_at = null
  from public.phg_repair_plan_menus_20260927 p
 where p.id = m.id and not m.is_current and p.make_current;

do $$
declare v_multi int; v_none int; v_smaller int; v_changed int; v_dmg int; v_dmg_bad int; v_itempg int; v_itempg_chg int;
        v_old_over_new int;
begin
  select count(*) into v_multi from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x;
  select count(*) into v_none from (select distinct account_id from public.phg_repair_plan_menus_20260927) t
   where not exists (select 1 from public.menus m where m.account_id = t.account_id and m.is_current);
  select count(*) into v_smaller from (
    select p.account_id, max(p.n) filter (where p.make_current) chosen_n,
           max(cardinality(coalesce(m.item_keys, '{}'))) filter (where m.created_at < '2026-09-27') old_n
      from public.phg_repair_plan_menus_20260927 p join public.menus m on m.id = p.id group by 1) z
   where z.old_n is not null and z.chosen_n < z.old_n;
  select count(*) into v_changed from public.phg_repair_plan_menus_20260927 where make_current and not was_current;
  -- independent check against the list saved before the plan: every damaged venue's CURRENT menu is at least as large
  select count(*), count(*) filter (where coalesce(c.n, 0) < d.old_max_n) into v_dmg, v_dmg_bad
    from public.phg_repair_damaged_20260927 d
    left join lateral (select max(cardinality(coalesce(m.item_keys, '{}'::text[]))) n from public.menus m
                        where m.account_id = d.account_id and m.is_current) c on true;
  -- reported picks: item pages chosen as current, and pre-incident menus that replaced a newer capture of the same page
  select count(*), count(*) filter (where not was_current) into v_itempg, v_itempg_chg
    from public.phg_repair_plan_menus_20260927 where make_current and itemish;
  select count(*) into v_old_over_new from public.phg_repair_plan_menus_20260927 ch
   where ch.make_current and not ch.was_current and ch.created_at < '2026-09-27 00:00:00+00'
     and exists (select 1 from public.phg_repair_plan_menus_20260927 o
                  where o.account_id = ch.account_id and o.was_current and o.created_at > ch.created_at
                    and o.source_key is not null and o.source_key = ch.source_key);
  if v_multi > 0 or v_none > 0 or v_smaller > 0 or v_dmg_bad > 0 then
    raise exception 'repair step 2 postcondition failed: % accounts with >1 current, % without current, % smaller than before, % of % damaged venues not restored',
      v_multi, v_none, v_smaller, v_dmg_bad, v_dmg;
  end if;
  insert into public.phg_repair_run_20260927 (step, detail)
  values ('step2', jsonb_build_object('current_changed', v_changed, 'multi_current', v_multi, 'no_current', v_none, 'smaller', v_smaller,
          'damaged_venues', v_dmg, 'damaged_not_restored', v_dmg_bad,
          'chosen_item_pages', v_itempg, 'chosen_item_pages_changed', v_itempg_chg,
          'pre_incident_replaced_newer_same_source', v_old_over_new))
  on conflict (step) do nothing;
end $$;

-- the rule is now enforced by the database (submit_menu demotes before it inserts)
create unique index if not exists menus_one_current_per_account on public.menus (account_id) where is_current;

-- ---------- Step 3 (batched) ----------
create table if not exists public.phg_backup_staging_dupes_20260927 (
  staging_id bigint primary key, account_id text, menu_page_url text, kept_page_url text, backed_up_at timestamptz default now());
alter table public.phg_backup_staging_dupes_20260927 enable row level security;
revoke all on public.phg_backup_staging_dupes_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_staging_dupes_20260927 from service_role;
create index if not exists phg_backup_staging_dupes_20260927_acct on public.phg_backup_staging_dupes_20260927 (account_id);
create table if not exists public.phg_repair_step3_done (account_id text primary key, dup_rows int, done_at timestamptz default now());
alter table public.phg_repair_step3_done enable row level security;
revoke all on public.phg_repair_step3_done from anon, authenticated;

-- returns the number of venues still to do (0 = finished); ~100 venues per call keeps each call well under 60 s
create or replace function public.phg_repair_step3_batch(p_accounts int default 100)
returns int language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_accts text[];
begin
  select array_agg(account_id) into v_accts from (
    select distinct s.account_id from public.staging_menu_extract s
     where s.superseded_at is null and s.account_id is not null and s.loaded_at >= '2026-09-27'
       and not exists (select 1 from public.phg_repair_step3_done d where d.account_id = s.account_id)
     order by s.account_id limit greatest(1, least(p_accounts, 300))) a;
  if v_accts is null then return 0; end if;
  with pages as (
    select account_id, menu_page_url, min(id) as first_id,
           public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price)
                                                  order by public.phg_menu_item_key(item_name, item_price))) as set_hash
    from public.staging_menu_extract
    where superseded_at is null and account_id = any (v_accts) and item_type <> 'summary'
    group by account_id, menu_page_url),
  ranked as (
    select p.*, row_number() over w as rk, first_value(menu_page_url) over w as kept_url
    from pages p
    window w as (partition by account_id, set_hash order by public.phg_menu_url_is_item_page(menu_page_url) asc, first_id))
  insert into public.phg_backup_staging_dupes_20260927 (staging_id, account_id, menu_page_url, kept_page_url)
  select s.id, s.account_id, s.menu_page_url, r.kept_url
  from ranked r
  join public.staging_menu_extract s on s.account_id = r.account_id and s.menu_page_url = r.menu_page_url and s.superseded_at is null
  where r.rk > 1
  on conflict (staging_id) do nothing;
  update public.staging_menu_extract s set superseded_at = now(), superseded_reason = 'duplicate_item_set_of_sibling'
    from public.phg_backup_staging_dupes_20260927 b
   where b.staging_id = s.id and b.account_id = any (v_accts) and s.superseded_at is null;
  insert into public.phg_repair_step3_done (account_id, dup_rows)
  select a.a, coalesce(c.n, 0) from unnest(v_accts) a(a)
    left join (select b.account_id, count(*)::int n from public.phg_backup_staging_dupes_20260927 b
                where b.account_id = any (v_accts) group by 1) c on c.account_id = a.a
  on conflict (account_id) do nothing;
  return (select count(distinct s.account_id) from public.staging_menu_extract s
           where s.superseded_at is null and s.loaded_at >= '2026-09-27' and s.account_id is not null
             and not exists (select 1 from public.phg_repair_step3_done d where d.account_id = s.account_id));
end $$;
revoke all on function public.phg_repair_step3_batch(int) from public, anon, authenticated;

-- ---------- Step 4 (batched) ----------
create table if not exists public.phg_repair_step4_done (account_id text primary key, done_at timestamptz default now());
alter table public.phg_repair_step4_done enable row level security;
revoke all on public.phg_repair_step4_done from anon, authenticated;

create or replace function public.phg_repair_step4_batch(p_accounts int default 200)
returns int language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_accts text[];
begin
  select array_agg(account_id) into v_accts from (
    select distinct c.account_id from public.menu_source_candidates c
     where c.item_set_hash is null and c.duplicate_of_candidate_id is null and c.account_id is not null
       and not exists (select 1 from public.phg_repair_step4_done d where d.account_id = c.account_id)
     order by c.account_id limit greatest(1, least(p_accounts, 500))) a;
  if v_accts is null then return 0; end if;
  update public.menu_source_candidates c set item_set_hash = x.set_hash
    from (select account_id, menu_page_url,
                 public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price)
                                                        order by public.phg_menu_item_key(item_name, item_price))) set_hash
            from public.staging_menu_extract
           where superseded_at is null and item_type <> 'summary' and account_id = any (v_accts)
           group by 1, 2) x
   where x.account_id = c.account_id and x.menu_page_url = c.source_url
     and c.item_set_hash is null and c.duplicate_of_candidate_id is null;
  insert into public.phg_repair_step4_done (account_id) select unnest(v_accts) on conflict do nothing;
  return (select count(distinct c.account_id) from public.menu_source_candidates c
           where c.item_set_hash is null and c.duplicate_of_candidate_id is null and c.account_id is not null
             and not exists (select 1 from public.phg_repair_step4_done d where d.account_id = c.account_id));
end $$;
revoke all on function public.phg_repair_step4_batch(int) from public, anon, authenticated;

-- ---------- Rollback (rehearsed in a rolled-back transaction, see handoff/reviews/rehearsal/results_round3.md) ----------
-- Undoes only what this repair changed, and never leaves two current menus:
--  * a venue that has ANY menu not in the currency backup (i.e. it received a menu after the repair) is skipped;
--  * otherwise: menus the repair made current are demoted first and get back their backed-up superseded_by /
--    superseded_reason / superseded_at; then menus the repair demoted are restored exactly from the backup;
--  * staging rows the repair superseded come back only if their page has not been re-extracted since.
-- Function definitions: run this first, then select public.phg_rollback_function_defs_20260927();
create or replace function public.phg_repair_20260927_rollback()
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_run timestamptz; v_skip int; v_dem int; v_res int; v_stg int; v_multi int; v_rb int;
begin
  select ran_at into v_run from public.phg_repair_run_20260927 where step = 'step2';
  if v_run is null then raise exception 'step 2 never ran'; end if;
  set local lock_timeout = '5s';
  lock table public.menus in share row exclusive mode;
  drop table if exists pg_temp.rb_accts;
  create temp table rb_accts on commit drop as
    select distinct p.account_id from public.phg_repair_plan_menus_20260927 p
     where p.make_current <> p.was_current
       and not exists (select 1 from public.menus m
                        where m.account_id = p.account_id
                          and not exists (select 1 from public.phg_backup_menus_currency_20260927 b where b.id = m.id));
  select count(*) into v_rb from rb_accts;
  select count(distinct account_id) - v_rb into v_skip
    from public.phg_repair_plan_menus_20260927 where make_current <> was_current;
  -- 1. demote what the repair promoted, restoring the row's own backed-up supersession
  update public.menus m set is_current = b.is_current, superseded_by = b.superseded_by,
         superseded_reason = b.superseded_reason, superseded_at = b.superseded_at
    from public.phg_backup_menus_currency_20260927 b, public.phg_repair_plan_menus_20260927 p
   where b.id = m.id and p.id = m.id and p.make_current and not p.was_current and m.is_current
     and p.account_id in (select account_id from rb_accts);
  get diagnostics v_dem = row_count;
  -- 2. restore what the repair demoted
  update public.menus m set is_current = b.is_current, superseded_by = b.superseded_by,
         superseded_reason = b.superseded_reason, superseded_at = b.superseded_at
    from public.phg_backup_menus_currency_20260927 b, public.phg_repair_plan_menus_20260927 p
   where b.id = m.id and p.id = m.id and p.was_current and not p.make_current
     and m.superseded_reason = 'repair_20260927_best_single_menu'
     and p.account_id in (select account_id from rb_accts);
  get diagnostics v_res = row_count;
  update public.staging_menu_extract s set superseded_at = null, superseded_reason = null
    from public.phg_backup_staging_dupes_20260927 b
   where b.staging_id = s.id and s.superseded_reason = 'duplicate_item_set_of_sibling'
     and not exists (select 1 from public.staging_menu_extract n
                      where n.account_id = s.account_id and n.menu_page_url = s.menu_page_url
                        and n.superseded_at is null and n.loaded_at > b.backed_up_at);
  get diagnostics v_stg = row_count;
  select count(*) into v_multi from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x;
  if v_multi > 0 then raise exception 'rollback would leave % accounts with 2 current menus', v_multi; end if;
  return jsonb_build_object('venues_rolled_back', v_rb, 'venues_skipped_newer_menu', v_skip,
                            'menus_demoted', v_dem, 'menus_restored', v_res, 'staging_rows_restored', v_stg);
end $$;
revoke all on function public.phg_repair_20260927_rollback() from public, anon, authenticated;

-- ---------- Runbook ----------
-- 0. Pause cron 7 and 13 (already paused). Apply 20260927190000 then this file, each as ONE transaction, through
--    apply_migration (or psql -1 -f), in that order. Not `supabase db push`.
-- 1. loop:  select public.phg_repair_step3_batch(100);   until it returns 0   (see results_round3.md for timings)
-- 2. vacuum (analyze) public.staging_menu_extract;
-- 3. loop:  select public.phg_repair_step4_batch(200);   until it returns 0
-- 4. create index concurrently if not exists menu_source_candidates_item_set_idx
--      on public.menu_source_candidates (account_id, item_set_hash) where item_set_hash is not null;
-- 5. run supabase/tests/phg_026_release_gate.sql; every row must say pass = true before cron 13, then 7, are
--    re-enabled (cron 7 calls phg_promote_menu_batch_safe(10); promote_clean_menu_batch now caps it at 5 pages).
-- 6. after the first cron 13 / 7 cycles and daily for a week: supabase/tests/phg_026_monitor.sql.
-- Rollback: select public.phg_repair_20260927_rollback(); then, if the functions must go back too,
--   select public.phg_rollback_function_defs_20260927();   (drops the one-current index, restores the 4 bodies)
$rehearse_f2$;
  EXCEPTION WHEN others THEN 
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
    RAISE EXCEPTION 'REHEARSAL %', r || jsonb_build_object('stage','file2','sqlstate',e_state,'error',e_msg,'detail',e_det,'context',right(e_ctx, 600),'ms',round(extract(epoch from clock_timestamp()-t0)*1000));
  END;
  r := r || jsonb_build_object('file2_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  t0 := clock_timestamp();
  BEGIN
    b := b || jsonb_build_object(
      'repair_run', (select jsonb_object_agg(step, detail) from public.phg_repair_run_20260927),
      'unique_index_exists', to_regclass('public.menus_one_current_per_account') is not null,
      'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x),
      'touched_venues', (select count(distinct account_id) from public.phg_repair_plan_menus_20260927),
      'damaged_saved', (select count(*) from public.phg_repair_damaged_20260927),
      'damaged_not_restored_recount', (select count(*) from public.phg_repair_damaged_20260927 d
          where coalesce((select max(cardinality(coalesce(m.item_keys,'{}'))) from public.menus m where m.account_id=d.account_id and m.is_current),0) < d.old_max_n),
      'touched_with_pre_incident_menu', (select count(distinct p.account_id) from public.phg_repair_plan_menus_20260927 p where p.created_at < '2026-09-27 00:00:00+00'),
      'touched_without_current', (select count(*) from (select distinct account_id from public.phg_repair_plan_menus_20260927) t where not exists (select 1 from public.menus m where m.account_id=t.account_id and m.is_current)),
      'backfill_null_item_keys', (select count(*) from public.menus where item_keys is null),
      'changed_by_reason', (select jsonb_object_agg(k, cnt) from (select k, count(*) cnt from (
          select distinct on (ch.account_id) ch.account_id,
                 case when o.id is null then 'no_prior_current' when ch.n>o.n then 'more_items' when ch.n=o.n and ch.bev>o.bev then 'same_n_more_bev'
                      when ch.n=o.n and ch.bev=o.bev and ch.itemish<o.itemish then 'same_n_bev_real_page' when (ch.n,ch.bev,ch.itemish)=(o.n,o.bev,o.itemish) then 'exact_tie' else 'other' end k
            from public.phg_repair_plan_menus_20260927 ch
            left join public.phg_repair_plan_menus_20260927 o on o.account_id=ch.account_id and o.was_current and o.id<>ch.id
           where ch.make_current and not ch.was_current order by ch.account_id, o.n desc nulls last) z group by k) y),
      'backup_privs_service_role_insert', jsonb_build_object(
          'function_defs', has_table_privilege('service_role','public.phg_backup_function_defs_20260927','INSERT'),
          'menus_currency', has_table_privilege('service_role','public.phg_backup_menus_currency_20260927','INSERT'),
          'staging_dupes', has_table_privilege('service_role','public.phg_backup_staging_dupes_20260927','INSERT')),
      'plan_rows', (select count(*) from public.phg_repair_plan_menus_20260927));
    b := b || jsonb_build_object('pass',
          (b->>'unique_index_exists')::boolean and (b->>'multi_current_global')::int = 0 and (b->>'touched_without_current')::int = 0
      and (b->>'damaged_not_restored_recount')::int = 0 and (b->'repair_run'->'step2'->>'damaged_not_restored')::int = 0
      and (b->>'damaged_saved')::int > 0 and (b->>'backfill_null_item_keys')::int = 0);
  EXCEPTION WHEN others THEN 
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      b := b || jsonb_build_object('ERROR_B', jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx), 'pass', false));
  END;
  r := r || jsonb_build_object('B', b, 'B_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  t0 := clock_timestamp();
  BEGIN
    -- sibling page 515238 (/happyhour) keeps its staged set; Step 4's formula gives it item_set_hash
    update public.menu_source_candidates mc set item_set_hash = x.h
      from (select public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price)
                                                          order by public.phg_menu_item_key(item_name, item_price))) h
              from public.staging_menu_extract s join public.menu_source_candidates sc on sc.id = 515238
             where s.account_id = sc.account_id and s.menu_page_url = sc.source_url and s.superseded_at is null and s.item_type <> 'summary') x
     where mc.id = 515238;
    -- the worker re-extracts candidate 13965 (/menu) and gets the same priced items (the incident pattern)
    select jsonb_agg(jsonb_build_object('item_name', s.item_name, 'item_price', s.item_price, 'item_type', s.item_type,
                                        'section_name', s.section_name, 'spirit_brands', s.spirit_brands) order by s.id)
      into items from public.staging_menu_extract s join public.menu_source_candidates sc on sc.id = 515238
     where s.account_id = sc.account_id and s.menu_page_url = sc.source_url and s.superseded_at is null and s.item_type <> 'summary';
    update public.phg_menu_worker_leases set owner = lease_owner, lease_until = now() + interval '10 minutes' where lane = 'candidate_extraction';
    update public.menu_source_candidates set status = 'processing', last_attempt_at = claimed where id = 13965;
    t1 := clock_timestamp();
    res := public.phg_save_menu_candidate_extraction(13965, claimed, lease_owner, items, 'rehearsal source text', 'rehearsal', 'html');
    c := jsonb_build_object('result', res, 'call_ms', round(extract(epoch from clock_timestamp()-t1)*1000), 'items_sent', jsonb_array_length(items),
      'candidate_after', (select jsonb_build_object('status', status, 'duplicate_of', duplicate_of_candidate_id, 'item_set_hash', item_set_hash) from public.menu_source_candidates where id = 13965),
      'new_staged_rows_for_candidate_page', (select count(*) from public.staging_menu_extract s join public.menu_source_candidates mc on mc.id = 13965
                                              where s.account_id = mc.account_id and s.menu_page_url = mc.source_url and s.superseded_at is null and s.loaded_at >= now()));
    c := c || jsonb_build_object('pass', res->>'status' = 'review' and (res->>'duplicate_of')::bigint = 515238
                                        and (c->>'new_staged_rows_for_candidate_page')::int = 0
                                        and (c->'candidate_after'->>'duplicate_of')::bigint = 515238);
    RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback extraction';
  EXCEPTION
    WHEN sqlstate 'P0099' THEN NULL;
    WHEN others THEN 
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      c := c || jsonb_build_object('ERROR', jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx), 'pass', false));
  END;
  r := r || jsonb_build_object('extraction_sibling_duplicate', c); c := '{}';
  RAISE EXCEPTION 'REHEARSAL %', r;
END
$rehearse_main$;

-- ===== block C (run on its own; ends in RAISE EXCEPTION, so everything rolls back) =====
DO $rehearse_main$
DECLARE
  r jsonb := '{}'; a jsonb := '{}'; b jsonb := '{}'; c jsonb := '{}'; v jsonb; res jsonb;
  t0 timestamptz; t1 timestamptz; acct text := 'ACC-CO-LED-03-25486'; orig_url text;
  cur_id uuid; cur2 uuid; cur_now uuid; secs jsonb; secs2 jsonb; secs4 jsonb; secs9 jsonb; items jsonb; item_x uuid;
  rem int; calls jsonb; lease_owner uuid := gen_random_uuid(); claimed timestamptz := clock_timestamp();
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
--    replaced the venue's menu; the last page promoted won. 185 venues lost a larger pre-existing
--    menu; 7,429 menus were created today from only ~2,500 distinct item sets.
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
-- Apply with cron 7 (promotion) and 13 (extraction) PAUSED. Data repair is a separate script.
-- Apply through the runbook (apply_migration, or psql -1 -f), in order: this file, then 20260927191000. Not with
-- `supabase db push`: newer migrations (20260927200000 and later) are already applied, so db push would refuse or
-- skip these out-of-order files.

set local lock_timeout = '3s';

-- ---------- 0. save the live definitions this migration replaces (rollback: phg_rollback_function_defs_20260927) ----------
create table if not exists public.phg_backup_function_defs_20260927 (
  signature text primary key, definition text not null, acl text, saved_at timestamptz not null default now());
alter table public.phg_backup_function_defs_20260927 enable row level security;
revoke all on public.phg_backup_function_defs_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_function_defs_20260927 from service_role;
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
revoke all on function public.phg_rollback_function_defs_20260927() from public, anon, authenticated;

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

-- Drinks item count of a payload: typed drinks items plus every item in a drinks section.
create or replace function public.phg_menu_payload_bev_count(p_sections jsonb)
returns integer language sql immutable set search_path = '' as $$
  select count(*)::int
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

-- Drinks item count of a stored menu (beer / wine are item_type 'other' inside typed sections).
create or replace function public.phg_menu_bev_count(p_menu_id uuid)
returns integer language sql stable set search_path = '' as $$
  select count(*)::int
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
 for c in select m.id, coalesce(m.source_key, public.phg_menu_source_key(m.evidence_url)) as source_key, m.item_keys, m.created_at
            from public.menus m where m.account_id=p_account_id and m.is_current
           order by m.created_at desc, m.id for update loop
  c_keys := coalesce(c.item_keys, public.phg_menu_item_keys(c.id));
  c_n    := cardinality(c_keys);
  v_ov   := public.phg_menu_keys_overlap(v_keys, c_keys);
  -- items whose price the capture supplies and the current menu lacks: never a duplicate (price enrichment)
  v_adds := public.phg_menu_keys_price_adds(v_keys, c_keys);
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
   if v_itemish and c_n > 0 and not (v_n >= c_n and v_ov >= ceil(c_dup_ratio * c_n)) then
    -- an item page shares the menu's key (?item= is stripped) but is not a fuller copy of it
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
   c_bev := public.phg_menu_bev_count(c.id);
   if v_itemish and c_n > 0 then
    v_make_current := false; v_alt_of := c.id; v_reason := 'alternate_item_page';
   elsif (v_n, v_bev) > (c_n, c_bev) then
    v_supersede := v_supersede || c.id;
    v_reason := coalesce(v_reason, case when c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) then 'contained_in_larger_capture' else 'larger_beverage_capture' end);
   elsif v_n >= c_n and c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) and v_adds = 0
         and c.created_at > now() - c_damping then
    -- flip-flop damping: two pages of the same menu must not keep swapping current. The current menu came from
    -- another source less than 7 days ago and this capture is only near-identical (not larger): keep it as an alternate.
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
    EXECUTE $rehearse_f2$-- PHG-026 data repair (run AFTER 20260927190000_phg_menu_dedupe_one_current.sql, with cron 7 and 13 paused).
-- Reversible: every changed value is backed up first; phg_repair_20260927_rollback() undoes it safely (below).
-- Review round 2 version (2026-09-28): spec + safety round-1 findings addressed; see handoff/reviews/PHG-026_REVIEW_LOG.md.
-- Review round 3 version (2026-09-28): lock_timeout 5s; independent damaged-venue check (phg_repair_damaged_20260927);
--   item-page / pre-incident picks recorded; rollback skip test by backup membership + full restore of the promoted
--   menus' superseded_* values; Step 3 counts in one GROUP BY; release gate + monitor scripts.
--
-- HOW TO APPLY: as ONE transaction, after 20260927190000 and through the runbook (apply_migration, which runs the file
--   in one transaction, or `psql -1 -f`). Not `supabase db push` (newer migrations are already applied). If any lock
--   is not granted within 5 s, or any postcondition fails, the whole file rolls back and nothing has changed.
--
-- Counts, defined (they measure different things):
--   1,547 venues "touched" = have a menu created since 2026-09-27 00:00Z (the incident window).
--     185 of them also had a menu from before the incident.
--     119 of those 185 had a pre-incident menu with MORE distinct items than today's current one (the damaged venues).
--   Step 2 changes the current menu of ~350 touched venues (rehearsal 2026-09-28: 348 = 300 more items, 12 same items
--   and more drinks, 36 ties where a real page replaces an item page; exact figure is written to
--   phg_repair_run_20260927 at run time). Steps 1-2 hold SHARE ROW EXCLUSIVE on menus for ~8 s (rehearsed 7.7 s). Acceptance: 0 venues end with fewer distinct items than their largest
--   pre-incident menu, 0 venues with 2 current menus, 0 touched venues left without a current menu.
--
-- Step 1  backfill menus.source_key / item_keys / item_set_hash (12,229 rows, ~8 s)
-- Step 2  one best current menu per touched venue: distinct items desc, drinks items desc, real page before item page,
--         the menu that is ALREADY current on ties, then newest. Runs under a table lock; ends with checks that raise
--         (and roll the whole step back) if any rule is broken; then the one-current-menu rule becomes a unique index.
-- Step 3  staging rows re-staged from sibling pages with an identical item set -> superseded (batched function).
-- Step 4  menu_source_candidates.item_set_hash backfill (batched function) + its index (CONCURRENTLY, runbook).
-- Note: v_public_drinks, v_public_drinks_classified, v_menu_header_catalog and v_pipeline_status do not filter
--   superseded_at, so Step 3 does not change their counts (earlier wording claimed it did). It stops duplicates from
--   being promoted and from feeding the promotion-based views.

set local lock_timeout = '5s';   -- fail fast (and roll back everything) instead of queueing behind a long lock

-- ---------- Step 1 + 2 (one transaction) ----------
lock table public.menus in share row exclusive mode;   -- no submit_menu can interleave with the plan

update public.menus m
   set source_key    = public.phg_menu_source_key(m.evidence_url),
       item_keys     = k.keys,
       item_set_hash = public.phg_menu_key_set_hash(k.keys)
  from (select id, public.phg_menu_item_keys(id) as keys from public.menus) k
 where k.id = m.id and (m.item_keys is null or m.source_key is null);

create table if not exists public.phg_backup_menus_currency_20260927 as
  select id, account_id, is_current, superseded_by, superseded_reason, superseded_at, now() as backed_up_at
  from public.menus;
alter table public.phg_backup_menus_currency_20260927 enable row level security;
revoke all on public.phg_backup_menus_currency_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_menus_currency_20260927 from service_role;
create unique index if not exists phg_backup_menus_currency_20260927_id on public.phg_backup_menus_currency_20260927 (id);

-- Independent damaged-venue list, saved BEFORE Step 2 decides anything: touched venues whose largest pre-incident menu
-- has more distinct items than the menu current right now. Step 2 must bring every one back to at least that size.
create table if not exists public.phg_repair_damaged_20260927 as
with touched as (select distinct account_id from public.menus where created_at >= '2026-09-27 00:00:00+00')
select t.account_id,
       (select max(cardinality(coalesce(o.item_keys, '{}'::text[]))) from public.menus o
         where o.account_id = t.account_id and o.created_at < '2026-09-27 00:00:00+00') as old_max_n,
       (select max(cardinality(coalesce(c.item_keys, '{}'::text[]))) from public.menus c
         where c.account_id = t.account_id and c.is_current) as cur_n_before,
       now() as saved_at
  from touched t;
delete from public.phg_repair_damaged_20260927 where old_max_n is null or old_max_n <= coalesce(cur_n_before, 0);
alter table public.phg_repair_damaged_20260927 enable row level security;
revoke all on public.phg_repair_damaged_20260927 from anon, authenticated;

create table if not exists public.phg_repair_run_20260927 (
  step text primary key, ran_at timestamptz not null default now(), detail jsonb);
alter table public.phg_repair_run_20260927 enable row level security;
revoke all on public.phg_repair_run_20260927 from anon, authenticated;

create table if not exists public.phg_repair_plan_menus_20260927 as
with touched as (select distinct account_id from public.menus where created_at >= '2026-09-27 00:00:00+00'),
m as (
  select m.id, m.account_id, m.created_at, m.is_current as was_current, m.source_key,
         cardinality(coalesce(m.item_keys, '{}'::text[])) as n,
         public.phg_menu_bev_count(m.id) as bev,
         public.phg_menu_url_is_item_page(m.evidence_url) as itemish
  from public.menus m join touched using (account_id)
),
ranked as (
  select m.*, row_number() over (partition by account_id
                                 order by n desc, bev desc, itemish asc, was_current desc, created_at desc, id) as rk
  from m
)
select id, account_id, was_current, (rk = 1) as make_current,
       first_value(id) over (partition by account_id order by rk) as chosen_id, n, bev, itemish, created_at, source_key
from ranked;
alter table public.phg_repair_plan_menus_20260927 enable row level security;
revoke all on public.phg_repair_plan_menus_20260927 from anon, authenticated;

-- demote first, then promote: the one-current rule must hold row by row
update public.menus m
   set is_current = false, superseded_by = p.chosen_id,
       superseded_reason = 'repair_20260927_best_single_menu', superseded_at = now()
  from public.phg_repair_plan_menus_20260927 p
 where p.id = m.id and m.is_current and not p.make_current;
update public.menus m
   set is_current = true, superseded_by = null, superseded_reason = null, superseded_at = null
  from public.phg_repair_plan_menus_20260927 p
 where p.id = m.id and not m.is_current and p.make_current;

do $$
declare v_multi int; v_none int; v_smaller int; v_changed int; v_dmg int; v_dmg_bad int; v_itempg int; v_itempg_chg int;
        v_old_over_new int;
begin
  select count(*) into v_multi from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x;
  select count(*) into v_none from (select distinct account_id from public.phg_repair_plan_menus_20260927) t
   where not exists (select 1 from public.menus m where m.account_id = t.account_id and m.is_current);
  select count(*) into v_smaller from (
    select p.account_id, max(p.n) filter (where p.make_current) chosen_n,
           max(cardinality(coalesce(m.item_keys, '{}'))) filter (where m.created_at < '2026-09-27') old_n
      from public.phg_repair_plan_menus_20260927 p join public.menus m on m.id = p.id group by 1) z
   where z.old_n is not null and z.chosen_n < z.old_n;
  select count(*) into v_changed from public.phg_repair_plan_menus_20260927 where make_current and not was_current;
  -- independent check against the list saved before the plan: every damaged venue's CURRENT menu is at least as large
  select count(*), count(*) filter (where coalesce(c.n, 0) < d.old_max_n) into v_dmg, v_dmg_bad
    from public.phg_repair_damaged_20260927 d
    left join lateral (select max(cardinality(coalesce(m.item_keys, '{}'::text[]))) n from public.menus m
                        where m.account_id = d.account_id and m.is_current) c on true;
  -- reported picks: item pages chosen as current, and pre-incident menus that replaced a newer capture of the same page
  select count(*), count(*) filter (where not was_current) into v_itempg, v_itempg_chg
    from public.phg_repair_plan_menus_20260927 where make_current and itemish;
  select count(*) into v_old_over_new from public.phg_repair_plan_menus_20260927 ch
   where ch.make_current and not ch.was_current and ch.created_at < '2026-09-27 00:00:00+00'
     and exists (select 1 from public.phg_repair_plan_menus_20260927 o
                  where o.account_id = ch.account_id and o.was_current and o.created_at > ch.created_at
                    and o.source_key is not null and o.source_key = ch.source_key);
  if v_multi > 0 or v_none > 0 or v_smaller > 0 or v_dmg_bad > 0 then
    raise exception 'repair step 2 postcondition failed: % accounts with >1 current, % without current, % smaller than before, % of % damaged venues not restored',
      v_multi, v_none, v_smaller, v_dmg_bad, v_dmg;
  end if;
  insert into public.phg_repair_run_20260927 (step, detail)
  values ('step2', jsonb_build_object('current_changed', v_changed, 'multi_current', v_multi, 'no_current', v_none, 'smaller', v_smaller,
          'damaged_venues', v_dmg, 'damaged_not_restored', v_dmg_bad,
          'chosen_item_pages', v_itempg, 'chosen_item_pages_changed', v_itempg_chg,
          'pre_incident_replaced_newer_same_source', v_old_over_new))
  on conflict (step) do nothing;
end $$;

-- the rule is now enforced by the database (submit_menu demotes before it inserts)
create unique index if not exists menus_one_current_per_account on public.menus (account_id) where is_current;

-- ---------- Step 3 (batched) ----------
create table if not exists public.phg_backup_staging_dupes_20260927 (
  staging_id bigint primary key, account_id text, menu_page_url text, kept_page_url text, backed_up_at timestamptz default now());
alter table public.phg_backup_staging_dupes_20260927 enable row level security;
revoke all on public.phg_backup_staging_dupes_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_staging_dupes_20260927 from service_role;
create index if not exists phg_backup_staging_dupes_20260927_acct on public.phg_backup_staging_dupes_20260927 (account_id);
create table if not exists public.phg_repair_step3_done (account_id text primary key, dup_rows int, done_at timestamptz default now());
alter table public.phg_repair_step3_done enable row level security;
revoke all on public.phg_repair_step3_done from anon, authenticated;

-- returns the number of venues still to do (0 = finished); ~100 venues per call keeps each call well under 60 s
create or replace function public.phg_repair_step3_batch(p_accounts int default 100)
returns int language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_accts text[];
begin
  select array_agg(account_id) into v_accts from (
    select distinct s.account_id from public.staging_menu_extract s
     where s.superseded_at is null and s.account_id is not null and s.loaded_at >= '2026-09-27'
       and not exists (select 1 from public.phg_repair_step3_done d where d.account_id = s.account_id)
     order by s.account_id limit greatest(1, least(p_accounts, 300))) a;
  if v_accts is null then return 0; end if;
  with pages as (
    select account_id, menu_page_url, min(id) as first_id,
           public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price)
                                                  order by public.phg_menu_item_key(item_name, item_price))) as set_hash
    from public.staging_menu_extract
    where superseded_at is null and account_id = any (v_accts) and item_type <> 'summary'
    group by account_id, menu_page_url),
  ranked as (
    select p.*, row_number() over w as rk, first_value(menu_page_url) over w as kept_url
    from pages p
    window w as (partition by account_id, set_hash order by public.phg_menu_url_is_item_page(menu_page_url) asc, first_id))
  insert into public.phg_backup_staging_dupes_20260927 (staging_id, account_id, menu_page_url, kept_page_url)
  select s.id, s.account_id, s.menu_page_url, r.kept_url
  from ranked r
  join public.staging_menu_extract s on s.account_id = r.account_id and s.menu_page_url = r.menu_page_url and s.superseded_at is null
  where r.rk > 1
  on conflict (staging_id) do nothing;
  update public.staging_menu_extract s set superseded_at = now(), superseded_reason = 'duplicate_item_set_of_sibling'
    from public.phg_backup_staging_dupes_20260927 b
   where b.staging_id = s.id and b.account_id = any (v_accts) and s.superseded_at is null;
  insert into public.phg_repair_step3_done (account_id, dup_rows)
  select a.a, coalesce(c.n, 0) from unnest(v_accts) a(a)
    left join (select b.account_id, count(*)::int n from public.phg_backup_staging_dupes_20260927 b
                where b.account_id = any (v_accts) group by 1) c on c.account_id = a.a
  on conflict (account_id) do nothing;
  return (select count(distinct s.account_id) from public.staging_menu_extract s
           where s.superseded_at is null and s.loaded_at >= '2026-09-27' and s.account_id is not null
             and not exists (select 1 from public.phg_repair_step3_done d where d.account_id = s.account_id));
end $$;
revoke all on function public.phg_repair_step3_batch(int) from public, anon, authenticated;

-- ---------- Step 4 (batched) ----------
create table if not exists public.phg_repair_step4_done (account_id text primary key, done_at timestamptz default now());
alter table public.phg_repair_step4_done enable row level security;
revoke all on public.phg_repair_step4_done from anon, authenticated;

create or replace function public.phg_repair_step4_batch(p_accounts int default 200)
returns int language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_accts text[];
begin
  select array_agg(account_id) into v_accts from (
    select distinct c.account_id from public.menu_source_candidates c
     where c.item_set_hash is null and c.duplicate_of_candidate_id is null and c.account_id is not null
       and not exists (select 1 from public.phg_repair_step4_done d where d.account_id = c.account_id)
     order by c.account_id limit greatest(1, least(p_accounts, 500))) a;
  if v_accts is null then return 0; end if;
  update public.menu_source_candidates c set item_set_hash = x.set_hash
    from (select account_id, menu_page_url,
                 public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price)
                                                        order by public.phg_menu_item_key(item_name, item_price))) set_hash
            from public.staging_menu_extract
           where superseded_at is null and item_type <> 'summary' and account_id = any (v_accts)
           group by 1, 2) x
   where x.account_id = c.account_id and x.menu_page_url = c.source_url
     and c.item_set_hash is null and c.duplicate_of_candidate_id is null;
  insert into public.phg_repair_step4_done (account_id) select unnest(v_accts) on conflict do nothing;
  return (select count(distinct c.account_id) from public.menu_source_candidates c
           where c.item_set_hash is null and c.duplicate_of_candidate_id is null and c.account_id is not null
             and not exists (select 1 from public.phg_repair_step4_done d where d.account_id = c.account_id));
end $$;
revoke all on function public.phg_repair_step4_batch(int) from public, anon, authenticated;

-- ---------- Rollback (rehearsed in a rolled-back transaction, see handoff/reviews/rehearsal/results_round3.md) ----------
-- Undoes only what this repair changed, and never leaves two current menus:
--  * a venue that has ANY menu not in the currency backup (i.e. it received a menu after the repair) is skipped;
--  * otherwise: menus the repair made current are demoted first and get back their backed-up superseded_by /
--    superseded_reason / superseded_at; then menus the repair demoted are restored exactly from the backup;
--  * staging rows the repair superseded come back only if their page has not been re-extracted since.
-- Function definitions: run this first, then select public.phg_rollback_function_defs_20260927();
create or replace function public.phg_repair_20260927_rollback()
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_run timestamptz; v_skip int; v_dem int; v_res int; v_stg int; v_multi int; v_rb int;
begin
  select ran_at into v_run from public.phg_repair_run_20260927 where step = 'step2';
  if v_run is null then raise exception 'step 2 never ran'; end if;
  set local lock_timeout = '5s';
  lock table public.menus in share row exclusive mode;
  drop table if exists pg_temp.rb_accts;
  create temp table rb_accts on commit drop as
    select distinct p.account_id from public.phg_repair_plan_menus_20260927 p
     where p.make_current <> p.was_current
       and not exists (select 1 from public.menus m
                        where m.account_id = p.account_id
                          and not exists (select 1 from public.phg_backup_menus_currency_20260927 b where b.id = m.id));
  select count(*) into v_rb from rb_accts;
  select count(distinct account_id) - v_rb into v_skip
    from public.phg_repair_plan_menus_20260927 where make_current <> was_current;
  -- 1. demote what the repair promoted, restoring the row's own backed-up supersession
  update public.menus m set is_current = b.is_current, superseded_by = b.superseded_by,
         superseded_reason = b.superseded_reason, superseded_at = b.superseded_at
    from public.phg_backup_menus_currency_20260927 b, public.phg_repair_plan_menus_20260927 p
   where b.id = m.id and p.id = m.id and p.make_current and not p.was_current and m.is_current
     and p.account_id in (select account_id from rb_accts);
  get diagnostics v_dem = row_count;
  -- 2. restore what the repair demoted
  update public.menus m set is_current = b.is_current, superseded_by = b.superseded_by,
         superseded_reason = b.superseded_reason, superseded_at = b.superseded_at
    from public.phg_backup_menus_currency_20260927 b, public.phg_repair_plan_menus_20260927 p
   where b.id = m.id and p.id = m.id and p.was_current and not p.make_current
     and m.superseded_reason = 'repair_20260927_best_single_menu'
     and p.account_id in (select account_id from rb_accts);
  get diagnostics v_res = row_count;
  update public.staging_menu_extract s set superseded_at = null, superseded_reason = null
    from public.phg_backup_staging_dupes_20260927 b
   where b.staging_id = s.id and s.superseded_reason = 'duplicate_item_set_of_sibling'
     and not exists (select 1 from public.staging_menu_extract n
                      where n.account_id = s.account_id and n.menu_page_url = s.menu_page_url
                        and n.superseded_at is null and n.loaded_at > b.backed_up_at);
  get diagnostics v_stg = row_count;
  select count(*) into v_multi from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x;
  if v_multi > 0 then raise exception 'rollback would leave % accounts with 2 current menus', v_multi; end if;
  return jsonb_build_object('venues_rolled_back', v_rb, 'venues_skipped_newer_menu', v_skip,
                            'menus_demoted', v_dem, 'menus_restored', v_res, 'staging_rows_restored', v_stg);
end $$;
revoke all on function public.phg_repair_20260927_rollback() from public, anon, authenticated;

-- ---------- Runbook ----------
-- 0. Pause cron 7 and 13 (already paused). Apply 20260927190000 then this file, each as ONE transaction, through
--    apply_migration (or psql -1 -f), in that order. Not `supabase db push`.
-- 1. loop:  select public.phg_repair_step3_batch(100);   until it returns 0   (see results_round3.md for timings)
-- 2. vacuum (analyze) public.staging_menu_extract;
-- 3. loop:  select public.phg_repair_step4_batch(200);   until it returns 0
-- 4. create index concurrently if not exists menu_source_candidates_item_set_idx
--      on public.menu_source_candidates (account_id, item_set_hash) where item_set_hash is not null;
-- 5. run supabase/tests/phg_026_release_gate.sql; every row must say pass = true before cron 13, then 7, are
--    re-enabled (cron 7 calls phg_promote_menu_batch_safe(10); promote_clean_menu_batch now caps it at 5 pages).
-- 6. after the first cron 13 / 7 cycles and daily for a week: supabase/tests/phg_026_monitor.sql.
-- Rollback: select public.phg_repair_20260927_rollback(); then, if the functions must go back too,
--   select public.phg_rollback_function_defs_20260927();   (drops the one-current index, restores the 4 bodies)
$rehearse_f2$;
  EXCEPTION WHEN others THEN 
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
    RAISE EXCEPTION 'REHEARSAL %', r || jsonb_build_object('stage','file2','sqlstate',e_state,'error',e_msg,'detail',e_det,'context',right(e_ctx, 600),'ms',round(extract(epoch from clock_timestamp()-t0)*1000));
  END;
  r := r || jsonb_build_object('file2_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  -- Step 3: phg_repair_step3_batch(100) until done, the time budget, or the call cap
  calls := '[]'; rem := -1;
  WHILE rem <> 0 and jsonb_array_length(calls) < 100
        and coalesce((select sum((x->>'ms')::numeric) from jsonb_array_elements(calls) x), 0) < 30000 LOOP
    t0 := clock_timestamp();
    rem := public.phg_repair_step3_batch(100);
    calls := calls || jsonb_build_object('ms', round(extract(epoch from clock_timestamp()-t0)*1000), 'remaining_venues', rem);
  END LOOP;
  r := r || jsonb_build_object('step3', jsonb_build_object('calls', calls,
     'backup_rows', (select count(*) from public.phg_backup_staging_dupes_20260927),
     'venues_done', (select count(*) from public.phg_repair_step3_done)));
  -- Step 4: phg_repair_step4_batch(200)
  calls := '[]'; rem := -1;
  WHILE rem <> 0 and coalesce((select sum((x->>'ms')::numeric) from jsonb_array_elements(calls) x), 0) < 0 LOOP
    t0 := clock_timestamp();
    rem := public.phg_repair_step4_batch(200);
    calls := calls || jsonb_build_object('ms', round(extract(epoch from clock_timestamp()-t0)*1000), 'remaining_venues', rem);
  END LOOP;
  r := r || jsonb_build_object('step4', jsonb_build_object('calls', calls,
     'hashed', (select count(*) from public.menu_source_candidates where item_set_hash is not null)));
  RAISE EXCEPTION 'REHEARSAL %', r;
END
$rehearse_main$;

-- ===== block D (run on its own; ends in RAISE EXCEPTION, so everything rolls back) =====
DO $rehearse_main$
DECLARE
  r jsonb := '{}'; a jsonb := '{}'; b jsonb := '{}'; c jsonb := '{}'; v jsonb; res jsonb;
  t0 timestamptz; t1 timestamptz; acct text := 'ACC-CO-LED-03-25486'; orig_url text;
  cur_id uuid; cur2 uuid; cur_now uuid; secs jsonb; secs2 jsonb; secs4 jsonb; secs9 jsonb; items jsonb; item_x uuid;
  rem int; calls jsonb; lease_owner uuid := gen_random_uuid(); claimed timestamptz := clock_timestamp();
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
--    replaced the venue's menu; the last page promoted won. 185 venues lost a larger pre-existing
--    menu; 7,429 menus were created today from only ~2,500 distinct item sets.
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
-- Apply with cron 7 (promotion) and 13 (extraction) PAUSED. Data repair is a separate script.
-- Apply through the runbook (apply_migration, or psql -1 -f), in order: this file, then 20260927191000. Not with
-- `supabase db push`: newer migrations (20260927200000 and later) are already applied, so db push would refuse or
-- skip these out-of-order files.

set local lock_timeout = '3s';

-- ---------- 0. save the live definitions this migration replaces (rollback: phg_rollback_function_defs_20260927) ----------
create table if not exists public.phg_backup_function_defs_20260927 (
  signature text primary key, definition text not null, acl text, saved_at timestamptz not null default now());
alter table public.phg_backup_function_defs_20260927 enable row level security;
revoke all on public.phg_backup_function_defs_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_function_defs_20260927 from service_role;
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
revoke all on function public.phg_rollback_function_defs_20260927() from public, anon, authenticated;

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

-- Drinks item count of a payload: typed drinks items plus every item in a drinks section.
create or replace function public.phg_menu_payload_bev_count(p_sections jsonb)
returns integer language sql immutable set search_path = '' as $$
  select count(*)::int
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

-- Drinks item count of a stored menu (beer / wine are item_type 'other' inside typed sections).
create or replace function public.phg_menu_bev_count(p_menu_id uuid)
returns integer language sql stable set search_path = '' as $$
  select count(*)::int
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
 for c in select m.id, coalesce(m.source_key, public.phg_menu_source_key(m.evidence_url)) as source_key, m.item_keys, m.created_at
            from public.menus m where m.account_id=p_account_id and m.is_current
           order by m.created_at desc, m.id for update loop
  c_keys := coalesce(c.item_keys, public.phg_menu_item_keys(c.id));
  c_n    := cardinality(c_keys);
  v_ov   := public.phg_menu_keys_overlap(v_keys, c_keys);
  -- items whose price the capture supplies and the current menu lacks: never a duplicate (price enrichment)
  v_adds := public.phg_menu_keys_price_adds(v_keys, c_keys);
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
   if v_itemish and c_n > 0 and not (v_n >= c_n and v_ov >= ceil(c_dup_ratio * c_n)) then
    -- an item page shares the menu's key (?item= is stripped) but is not a fuller copy of it
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
   c_bev := public.phg_menu_bev_count(c.id);
   if v_itemish and c_n > 0 then
    v_make_current := false; v_alt_of := c.id; v_reason := 'alternate_item_page';
   elsif (v_n, v_bev) > (c_n, c_bev) then
    v_supersede := v_supersede || c.id;
    v_reason := coalesce(v_reason, case when c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) then 'contained_in_larger_capture' else 'larger_beverage_capture' end);
   elsif v_n >= c_n and c_n > 0 and v_ov >= ceil(c_dup_ratio * c_n) and v_adds = 0
         and c.created_at > now() - c_damping then
    -- flip-flop damping: two pages of the same menu must not keep swapping current. The current menu came from
    -- another source less than 7 days ago and this capture is only near-identical (not larger): keep it as an alternate.
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
    EXECUTE $rehearse_f2$-- PHG-026 data repair (run AFTER 20260927190000_phg_menu_dedupe_one_current.sql, with cron 7 and 13 paused).
-- Reversible: every changed value is backed up first; phg_repair_20260927_rollback() undoes it safely (below).
-- Review round 2 version (2026-09-28): spec + safety round-1 findings addressed; see handoff/reviews/PHG-026_REVIEW_LOG.md.
-- Review round 3 version (2026-09-28): lock_timeout 5s; independent damaged-venue check (phg_repair_damaged_20260927);
--   item-page / pre-incident picks recorded; rollback skip test by backup membership + full restore of the promoted
--   menus' superseded_* values; Step 3 counts in one GROUP BY; release gate + monitor scripts.
--
-- HOW TO APPLY: as ONE transaction, after 20260927190000 and through the runbook (apply_migration, which runs the file
--   in one transaction, or `psql -1 -f`). Not `supabase db push` (newer migrations are already applied). If any lock
--   is not granted within 5 s, or any postcondition fails, the whole file rolls back and nothing has changed.
--
-- Counts, defined (they measure different things):
--   1,547 venues "touched" = have a menu created since 2026-09-27 00:00Z (the incident window).
--     185 of them also had a menu from before the incident.
--     119 of those 185 had a pre-incident menu with MORE distinct items than today's current one (the damaged venues).
--   Step 2 changes the current menu of ~350 touched venues (rehearsal 2026-09-28: 348 = 300 more items, 12 same items
--   and more drinks, 36 ties where a real page replaces an item page; exact figure is written to
--   phg_repair_run_20260927 at run time). Steps 1-2 hold SHARE ROW EXCLUSIVE on menus for ~8 s (rehearsed 7.7 s). Acceptance: 0 venues end with fewer distinct items than their largest
--   pre-incident menu, 0 venues with 2 current menus, 0 touched venues left without a current menu.
--
-- Step 1  backfill menus.source_key / item_keys / item_set_hash (12,229 rows, ~8 s)
-- Step 2  one best current menu per touched venue: distinct items desc, drinks items desc, real page before item page,
--         the menu that is ALREADY current on ties, then newest. Runs under a table lock; ends with checks that raise
--         (and roll the whole step back) if any rule is broken; then the one-current-menu rule becomes a unique index.
-- Step 3  staging rows re-staged from sibling pages with an identical item set -> superseded (batched function).
-- Step 4  menu_source_candidates.item_set_hash backfill (batched function) + its index (CONCURRENTLY, runbook).
-- Note: v_public_drinks, v_public_drinks_classified, v_menu_header_catalog and v_pipeline_status do not filter
--   superseded_at, so Step 3 does not change their counts (earlier wording claimed it did). It stops duplicates from
--   being promoted and from feeding the promotion-based views.

set local lock_timeout = '5s';   -- fail fast (and roll back everything) instead of queueing behind a long lock

-- ---------- Step 1 + 2 (one transaction) ----------
lock table public.menus in share row exclusive mode;   -- no submit_menu can interleave with the plan

update public.menus m
   set source_key    = public.phg_menu_source_key(m.evidence_url),
       item_keys     = k.keys,
       item_set_hash = public.phg_menu_key_set_hash(k.keys)
  from (select id, public.phg_menu_item_keys(id) as keys from public.menus) k
 where k.id = m.id and (m.item_keys is null or m.source_key is null);

create table if not exists public.phg_backup_menus_currency_20260927 as
  select id, account_id, is_current, superseded_by, superseded_reason, superseded_at, now() as backed_up_at
  from public.menus;
alter table public.phg_backup_menus_currency_20260927 enable row level security;
revoke all on public.phg_backup_menus_currency_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_menus_currency_20260927 from service_role;
create unique index if not exists phg_backup_menus_currency_20260927_id on public.phg_backup_menus_currency_20260927 (id);

-- Independent damaged-venue list, saved BEFORE Step 2 decides anything: touched venues whose largest pre-incident menu
-- has more distinct items than the menu current right now. Step 2 must bring every one back to at least that size.
create table if not exists public.phg_repair_damaged_20260927 as
with touched as (select distinct account_id from public.menus where created_at >= '2026-09-27 00:00:00+00')
select t.account_id,
       (select max(cardinality(coalesce(o.item_keys, '{}'::text[]))) from public.menus o
         where o.account_id = t.account_id and o.created_at < '2026-09-27 00:00:00+00') as old_max_n,
       (select max(cardinality(coalesce(c.item_keys, '{}'::text[]))) from public.menus c
         where c.account_id = t.account_id and c.is_current) as cur_n_before,
       now() as saved_at
  from touched t;
delete from public.phg_repair_damaged_20260927 where old_max_n is null or old_max_n <= coalesce(cur_n_before, 0);
alter table public.phg_repair_damaged_20260927 enable row level security;
revoke all on public.phg_repair_damaged_20260927 from anon, authenticated;

create table if not exists public.phg_repair_run_20260927 (
  step text primary key, ran_at timestamptz not null default now(), detail jsonb);
alter table public.phg_repair_run_20260927 enable row level security;
revoke all on public.phg_repair_run_20260927 from anon, authenticated;

create table if not exists public.phg_repair_plan_menus_20260927 as
with touched as (select distinct account_id from public.menus where created_at >= '2026-09-27 00:00:00+00'),
m as (
  select m.id, m.account_id, m.created_at, m.is_current as was_current, m.source_key,
         cardinality(coalesce(m.item_keys, '{}'::text[])) as n,
         public.phg_menu_bev_count(m.id) as bev,
         public.phg_menu_url_is_item_page(m.evidence_url) as itemish
  from public.menus m join touched using (account_id)
),
ranked as (
  select m.*, row_number() over (partition by account_id
                                 order by n desc, bev desc, itemish asc, was_current desc, created_at desc, id) as rk
  from m
)
select id, account_id, was_current, (rk = 1) as make_current,
       first_value(id) over (partition by account_id order by rk) as chosen_id, n, bev, itemish, created_at, source_key
from ranked;
alter table public.phg_repair_plan_menus_20260927 enable row level security;
revoke all on public.phg_repair_plan_menus_20260927 from anon, authenticated;

-- demote first, then promote: the one-current rule must hold row by row
update public.menus m
   set is_current = false, superseded_by = p.chosen_id,
       superseded_reason = 'repair_20260927_best_single_menu', superseded_at = now()
  from public.phg_repair_plan_menus_20260927 p
 where p.id = m.id and m.is_current and not p.make_current;
update public.menus m
   set is_current = true, superseded_by = null, superseded_reason = null, superseded_at = null
  from public.phg_repair_plan_menus_20260927 p
 where p.id = m.id and not m.is_current and p.make_current;

do $$
declare v_multi int; v_none int; v_smaller int; v_changed int; v_dmg int; v_dmg_bad int; v_itempg int; v_itempg_chg int;
        v_old_over_new int;
begin
  select count(*) into v_multi from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x;
  select count(*) into v_none from (select distinct account_id from public.phg_repair_plan_menus_20260927) t
   where not exists (select 1 from public.menus m where m.account_id = t.account_id and m.is_current);
  select count(*) into v_smaller from (
    select p.account_id, max(p.n) filter (where p.make_current) chosen_n,
           max(cardinality(coalesce(m.item_keys, '{}'))) filter (where m.created_at < '2026-09-27') old_n
      from public.phg_repair_plan_menus_20260927 p join public.menus m on m.id = p.id group by 1) z
   where z.old_n is not null and z.chosen_n < z.old_n;
  select count(*) into v_changed from public.phg_repair_plan_menus_20260927 where make_current and not was_current;
  -- independent check against the list saved before the plan: every damaged venue's CURRENT menu is at least as large
  select count(*), count(*) filter (where coalesce(c.n, 0) < d.old_max_n) into v_dmg, v_dmg_bad
    from public.phg_repair_damaged_20260927 d
    left join lateral (select max(cardinality(coalesce(m.item_keys, '{}'::text[]))) n from public.menus m
                        where m.account_id = d.account_id and m.is_current) c on true;
  -- reported picks: item pages chosen as current, and pre-incident menus that replaced a newer capture of the same page
  select count(*), count(*) filter (where not was_current) into v_itempg, v_itempg_chg
    from public.phg_repair_plan_menus_20260927 where make_current and itemish;
  select count(*) into v_old_over_new from public.phg_repair_plan_menus_20260927 ch
   where ch.make_current and not ch.was_current and ch.created_at < '2026-09-27 00:00:00+00'
     and exists (select 1 from public.phg_repair_plan_menus_20260927 o
                  where o.account_id = ch.account_id and o.was_current and o.created_at > ch.created_at
                    and o.source_key is not null and o.source_key = ch.source_key);
  if v_multi > 0 or v_none > 0 or v_smaller > 0 or v_dmg_bad > 0 then
    raise exception 'repair step 2 postcondition failed: % accounts with >1 current, % without current, % smaller than before, % of % damaged venues not restored',
      v_multi, v_none, v_smaller, v_dmg_bad, v_dmg;
  end if;
  insert into public.phg_repair_run_20260927 (step, detail)
  values ('step2', jsonb_build_object('current_changed', v_changed, 'multi_current', v_multi, 'no_current', v_none, 'smaller', v_smaller,
          'damaged_venues', v_dmg, 'damaged_not_restored', v_dmg_bad,
          'chosen_item_pages', v_itempg, 'chosen_item_pages_changed', v_itempg_chg,
          'pre_incident_replaced_newer_same_source', v_old_over_new))
  on conflict (step) do nothing;
end $$;

-- the rule is now enforced by the database (submit_menu demotes before it inserts)
create unique index if not exists menus_one_current_per_account on public.menus (account_id) where is_current;

-- ---------- Step 3 (batched) ----------
create table if not exists public.phg_backup_staging_dupes_20260927 (
  staging_id bigint primary key, account_id text, menu_page_url text, kept_page_url text, backed_up_at timestamptz default now());
alter table public.phg_backup_staging_dupes_20260927 enable row level security;
revoke all on public.phg_backup_staging_dupes_20260927 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_staging_dupes_20260927 from service_role;
create index if not exists phg_backup_staging_dupes_20260927_acct on public.phg_backup_staging_dupes_20260927 (account_id);
create table if not exists public.phg_repair_step3_done (account_id text primary key, dup_rows int, done_at timestamptz default now());
alter table public.phg_repair_step3_done enable row level security;
revoke all on public.phg_repair_step3_done from anon, authenticated;

-- returns the number of venues still to do (0 = finished); ~100 venues per call keeps each call well under 60 s
create or replace function public.phg_repair_step3_batch(p_accounts int default 100)
returns int language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_accts text[];
begin
  select array_agg(account_id) into v_accts from (
    select distinct s.account_id from public.staging_menu_extract s
     where s.superseded_at is null and s.account_id is not null and s.loaded_at >= '2026-09-27'
       and not exists (select 1 from public.phg_repair_step3_done d where d.account_id = s.account_id)
     order by s.account_id limit greatest(1, least(p_accounts, 300))) a;
  if v_accts is null then return 0; end if;
  with pages as (
    select account_id, menu_page_url, min(id) as first_id,
           public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price)
                                                  order by public.phg_menu_item_key(item_name, item_price))) as set_hash
    from public.staging_menu_extract
    where superseded_at is null and account_id = any (v_accts) and item_type <> 'summary'
    group by account_id, menu_page_url),
  ranked as (
    select p.*, row_number() over w as rk, first_value(menu_page_url) over w as kept_url
    from pages p
    window w as (partition by account_id, set_hash order by public.phg_menu_url_is_item_page(menu_page_url) asc, first_id))
  insert into public.phg_backup_staging_dupes_20260927 (staging_id, account_id, menu_page_url, kept_page_url)
  select s.id, s.account_id, s.menu_page_url, r.kept_url
  from ranked r
  join public.staging_menu_extract s on s.account_id = r.account_id and s.menu_page_url = r.menu_page_url and s.superseded_at is null
  where r.rk > 1
  on conflict (staging_id) do nothing;
  update public.staging_menu_extract s set superseded_at = now(), superseded_reason = 'duplicate_item_set_of_sibling'
    from public.phg_backup_staging_dupes_20260927 b
   where b.staging_id = s.id and b.account_id = any (v_accts) and s.superseded_at is null;
  insert into public.phg_repair_step3_done (account_id, dup_rows)
  select a.a, coalesce(c.n, 0) from unnest(v_accts) a(a)
    left join (select b.account_id, count(*)::int n from public.phg_backup_staging_dupes_20260927 b
                where b.account_id = any (v_accts) group by 1) c on c.account_id = a.a
  on conflict (account_id) do nothing;
  return (select count(distinct s.account_id) from public.staging_menu_extract s
           where s.superseded_at is null and s.loaded_at >= '2026-09-27' and s.account_id is not null
             and not exists (select 1 from public.phg_repair_step3_done d where d.account_id = s.account_id));
end $$;
revoke all on function public.phg_repair_step3_batch(int) from public, anon, authenticated;

-- ---------- Step 4 (batched) ----------
create table if not exists public.phg_repair_step4_done (account_id text primary key, done_at timestamptz default now());
alter table public.phg_repair_step4_done enable row level security;
revoke all on public.phg_repair_step4_done from anon, authenticated;

create or replace function public.phg_repair_step4_batch(p_accounts int default 200)
returns int language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_accts text[];
begin
  select array_agg(account_id) into v_accts from (
    select distinct c.account_id from public.menu_source_candidates c
     where c.item_set_hash is null and c.duplicate_of_candidate_id is null and c.account_id is not null
       and not exists (select 1 from public.phg_repair_step4_done d where d.account_id = c.account_id)
     order by c.account_id limit greatest(1, least(p_accounts, 500))) a;
  if v_accts is null then return 0; end if;
  update public.menu_source_candidates c set item_set_hash = x.set_hash
    from (select account_id, menu_page_url,
                 public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price)
                                                        order by public.phg_menu_item_key(item_name, item_price))) set_hash
            from public.staging_menu_extract
           where superseded_at is null and item_type <> 'summary' and account_id = any (v_accts)
           group by 1, 2) x
   where x.account_id = c.account_id and x.menu_page_url = c.source_url
     and c.item_set_hash is null and c.duplicate_of_candidate_id is null;
  insert into public.phg_repair_step4_done (account_id) select unnest(v_accts) on conflict do nothing;
  return (select count(distinct c.account_id) from public.menu_source_candidates c
           where c.item_set_hash is null and c.duplicate_of_candidate_id is null and c.account_id is not null
             and not exists (select 1 from public.phg_repair_step4_done d where d.account_id = c.account_id));
end $$;
revoke all on function public.phg_repair_step4_batch(int) from public, anon, authenticated;

-- ---------- Rollback (rehearsed in a rolled-back transaction, see handoff/reviews/rehearsal/results_round3.md) ----------
-- Undoes only what this repair changed, and never leaves two current menus:
--  * a venue that has ANY menu not in the currency backup (i.e. it received a menu after the repair) is skipped;
--  * otherwise: menus the repair made current are demoted first and get back their backed-up superseded_by /
--    superseded_reason / superseded_at; then menus the repair demoted are restored exactly from the backup;
--  * staging rows the repair superseded come back only if their page has not been re-extracted since.
-- Function definitions: run this first, then select public.phg_rollback_function_defs_20260927();
create or replace function public.phg_repair_20260927_rollback()
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_run timestamptz; v_skip int; v_dem int; v_res int; v_stg int; v_multi int; v_rb int;
begin
  select ran_at into v_run from public.phg_repair_run_20260927 where step = 'step2';
  if v_run is null then raise exception 'step 2 never ran'; end if;
  set local lock_timeout = '5s';
  lock table public.menus in share row exclusive mode;
  drop table if exists pg_temp.rb_accts;
  create temp table rb_accts on commit drop as
    select distinct p.account_id from public.phg_repair_plan_menus_20260927 p
     where p.make_current <> p.was_current
       and not exists (select 1 from public.menus m
                        where m.account_id = p.account_id
                          and not exists (select 1 from public.phg_backup_menus_currency_20260927 b where b.id = m.id));
  select count(*) into v_rb from rb_accts;
  select count(distinct account_id) - v_rb into v_skip
    from public.phg_repair_plan_menus_20260927 where make_current <> was_current;
  -- 1. demote what the repair promoted, restoring the row's own backed-up supersession
  update public.menus m set is_current = b.is_current, superseded_by = b.superseded_by,
         superseded_reason = b.superseded_reason, superseded_at = b.superseded_at
    from public.phg_backup_menus_currency_20260927 b, public.phg_repair_plan_menus_20260927 p
   where b.id = m.id and p.id = m.id and p.make_current and not p.was_current and m.is_current
     and p.account_id in (select account_id from rb_accts);
  get diagnostics v_dem = row_count;
  -- 2. restore what the repair demoted
  update public.menus m set is_current = b.is_current, superseded_by = b.superseded_by,
         superseded_reason = b.superseded_reason, superseded_at = b.superseded_at
    from public.phg_backup_menus_currency_20260927 b, public.phg_repair_plan_menus_20260927 p
   where b.id = m.id and p.id = m.id and p.was_current and not p.make_current
     and m.superseded_reason = 'repair_20260927_best_single_menu'
     and p.account_id in (select account_id from rb_accts);
  get diagnostics v_res = row_count;
  update public.staging_menu_extract s set superseded_at = null, superseded_reason = null
    from public.phg_backup_staging_dupes_20260927 b
   where b.staging_id = s.id and s.superseded_reason = 'duplicate_item_set_of_sibling'
     and not exists (select 1 from public.staging_menu_extract n
                      where n.account_id = s.account_id and n.menu_page_url = s.menu_page_url
                        and n.superseded_at is null and n.loaded_at > b.backed_up_at);
  get diagnostics v_stg = row_count;
  select count(*) into v_multi from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x;
  if v_multi > 0 then raise exception 'rollback would leave % accounts with 2 current menus', v_multi; end if;
  return jsonb_build_object('venues_rolled_back', v_rb, 'venues_skipped_newer_menu', v_skip,
                            'menus_demoted', v_dem, 'menus_restored', v_res, 'staging_rows_restored', v_stg);
end $$;
revoke all on function public.phg_repair_20260927_rollback() from public, anon, authenticated;

-- ---------- Runbook ----------
-- 0. Pause cron 7 and 13 (already paused). Apply 20260927190000 then this file, each as ONE transaction, through
--    apply_migration (or psql -1 -f), in that order. Not `supabase db push`.
-- 1. loop:  select public.phg_repair_step3_batch(100);   until it returns 0   (see results_round3.md for timings)
-- 2. vacuum (analyze) public.staging_menu_extract;
-- 3. loop:  select public.phg_repair_step4_batch(200);   until it returns 0
-- 4. create index concurrently if not exists menu_source_candidates_item_set_idx
--      on public.menu_source_candidates (account_id, item_set_hash) where item_set_hash is not null;
-- 5. run supabase/tests/phg_026_release_gate.sql; every row must say pass = true before cron 13, then 7, are
--    re-enabled (cron 7 calls phg_promote_menu_batch_safe(10); promote_clean_menu_batch now caps it at 5 pages).
-- 6. after the first cron 13 / 7 cycles and daily for a week: supabase/tests/phg_026_monitor.sql.
-- Rollback: select public.phg_repair_20260927_rollback(); then, if the functions must go back too,
--   select public.phg_rollback_function_defs_20260927();   (drops the one-current index, restores the 4 bodies)
$rehearse_f2$;
  EXCEPTION WHEN others THEN 
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
    RAISE EXCEPTION 'REHEARSAL %', r || jsonb_build_object('stage','file2','sqlstate',e_state,'error',e_msg,'detail',e_det,'context',right(e_ctx, 600),'ms',round(extract(epoch from clock_timestamp()-t0)*1000));
  END;
  r := r || jsonb_build_object('file2_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  t0 := clock_timestamp();
  BEGIN
    -- The promotion queue is empty today (v_menu_staging_promotion_candidates = 0 rows). Re-stage one incident item
    -- page's 13 beverage rows under a NEW sibling ?item= URL: same items, new content hash (the incident pattern).
    update public.staging_menu_extract
       set menu_page_url = 'https://thesherpagrill.com/menu?item=rehearsal-new-sibling', promoted_at = null, promotion_status = null, quality_status = 'promotion_ready'
     where account_id = 'ACC-CO-LED-03-06531' and menu_page_url = 'https://thesherpagrill.com/menu?item=aloo-gobi-NKZx' and superseded_at is null;
    get diagnostics rem = row_count;
    select id into cur_id from public.menus where account_id = 'ACC-CO-LED-03-06531' and is_current;
    t1 := clock_timestamp();
    res := public.promote_clean_menu_batch(1);
    c := jsonb_build_object('rows_requeued', rem, 'result', res, 'ms', round(extract(epoch from clock_timestamp()-t1)*1000),
      'current_unchanged', (select id from public.menus where account_id = 'ACC-CO-LED-03-06531' and is_current) = cur_id,
      'acct_menus_created', (select count(*) from public.menus where account_id = 'ACC-CO-LED-03-06531' and created_at >= now()),
      'staging_outcome', (select jsonb_object_agg(coalesce(promotion_status,'(null)'), n) from (select promotion_status, count(*) n from public.staging_menu_extract
                            where account_id = 'ACC-CO-LED-03-06531' and menu_page_url = 'https://thesherpagrill.com/menu?item=rehearsal-new-sibling' group by 1) x),
      'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x));
    c := c || jsonb_build_object('pass', coalesce((res->>'failed')::int, 1) = 0 and (res->>'created')::int = 0
              and (coalesce((res->>'alternate')::int,0)+coalesce((res->>'duplicate')::int,0)+coalesce((res->>'held_subset')::int,0)) = 1
              and (c->>'current_unchanged')::boolean and (c->>'multi_current_global')::int = 0 and (c->>'acct_menus_created')::int = 0);
    RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback promote';
  EXCEPTION
    WHEN sqlstate 'P0099' THEN NULL;
    WHEN others THEN 
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      c := c || jsonb_build_object('ERROR', jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx), 'pass', false));
  END;
  r := r || jsonb_build_object('promote_clean_menu_batch_1', c); c := '{}';
  -- Step 3: phg_repair_step3_batch(100) until done, the time budget, or the call cap
  calls := '[]'; rem := -1;
  WHILE rem <> 0 and jsonb_array_length(calls) < 3
        and coalesce((select sum((x->>'ms')::numeric) from jsonb_array_elements(calls) x), 0) < 8000 LOOP
    t0 := clock_timestamp();
    rem := public.phg_repair_step3_batch(100);
    calls := calls || jsonb_build_object('ms', round(extract(epoch from clock_timestamp()-t0)*1000), 'remaining_venues', rem);
  END LOOP;
  r := r || jsonb_build_object('step3', jsonb_build_object('calls', calls,
     'backup_rows', (select count(*) from public.phg_backup_staging_dupes_20260927),
     'venues_done', (select count(*) from public.phg_repair_step3_done)));
  -- Step 4: phg_repair_step4_batch(200)
  calls := '[]'; rem := -1;
  WHILE rem <> 0 and coalesce((select sum((x->>'ms')::numeric) from jsonb_array_elements(calls) x), 0) < 4000 LOOP
    t0 := clock_timestamp();
    rem := public.phg_repair_step4_batch(200);
    calls := calls || jsonb_build_object('ms', round(extract(epoch from clock_timestamp()-t0)*1000), 'remaining_venues', rem);
  END LOOP;
  r := r || jsonb_build_object('step4', jsonb_build_object('calls', calls,
     'hashed', (select count(*) from public.menu_source_candidates where item_set_hash is not null)));
  -- runbook step 4 index (CONCURRENTLY in the runbook; plain here because CONCURRENTLY cannot run in a transaction)
  t0 := clock_timestamp();
  create index if not exists menu_source_candidates_item_set_idx on public.menu_source_candidates (account_id, item_set_hash) where item_set_hash is not null;
  r := r || jsonb_build_object('cand_index_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  t0 := clock_timestamp();
  BEGIN
    EXECUTE 'select jsonb_agg(to_jsonb(g)) from (' || $rehearse_gate$-- PHG-026 release gate. Run ONCE, right after the runbook (both migrations, steps 1-4, the CONCURRENTLY index) and
-- BEFORE cron 13 / 7 are re-enabled. Every row must say pass = true.
-- Scope: the venues in the repair plan (phg_repair_plan_menus_20260927) and data that existed before Step 2 ran
-- (phg_repair_run_20260927.step2.ran_at). Nothing here depends on captures made after release; those are watched by
-- supabase/tests/phg_026_monitor.sql instead.
with
run as (select ran_at t, detail from public.phg_repair_run_20260927 where step = 'step2'),
plan_accts as (select distinct account_id from public.phg_repair_plan_menus_20260927),
multi as (select count(*) n from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x),
idx as (select count(*) n from pg_indexes where schemaname = 'public' and indexname = 'menus_one_current_per_account'),
no_current as (select count(*) n from plan_accts t
                where not exists (select 1 from public.menus m where m.account_id = t.account_id and m.is_current)),
smaller as (
  select count(*) n from plan_accts t
  cross join lateral (select max(cardinality(coalesce(m.item_keys, '{}'::text[]))) cur_n from public.menus m
                       where m.account_id = t.account_id and m.is_current) c
  cross join lateral (select max(cardinality(coalesce(m.item_keys, '{}'::text[]))) old_n from public.menus m
                       where m.account_id = t.account_id and m.created_at < '2026-09-27 00:00:00+00') o
  where o.old_n is not null and coalesce(c.cur_n, 0) < o.old_n),
damaged as (
  select count(*) total, count(*) filter (where coalesce(c.n, 0) < d.old_max_n) not_restored
    from public.phg_repair_damaged_20260927 d
    left join lateral (select max(cardinality(coalesce(m.item_keys, '{}'::text[]))) n from public.menus m
                        where m.account_id = d.account_id and m.is_current) c on true),
fdefs as (select count(*) n from public.phg_backup_function_defs_20260927),
-- Step 3: every venue with live staging rows loaded in the incident window and before Step 2 ran is done
step3_left as (select count(*) n from (
                 select distinct s.account_id from public.staging_menu_extract s, run
                  where s.superseded_at is null and s.account_id is not null
                    and s.loaded_at >= '2026-09-27 00:00:00+00' and s.loaded_at < run.t) a
                where not exists (select 1 from public.phg_repair_step3_done d where d.account_id = a.account_id)),
-- Step 4: every venue with a candidate discovered before Step 2 ran and still without item_set_hash is done
step4_left as (select count(*) n from (
                 select distinct c.account_id from public.menu_source_candidates c, run
                  where c.item_set_hash is null and c.duplicate_of_candidate_id is null and c.account_id is not null
                    and c.first_discovered_at < run.t) a
                where not exists (select 1 from public.phg_repair_step4_done d where d.account_id = a.account_id)),
cand_idx as (select count(*) n from pg_indexes where schemaname = 'public' and indexname = 'menu_source_candidates_item_set_idx'),
cron_paused as (select coalesce(bool_and(not active), true) ok, string_agg(jobid || ':' || active, ',' order by jobid) v
                  from cron.job where jobid in (7, 13))
select * from (values
  ('0 accounts with more than one current menu',                   (select n from multi) = 0,        (select n from multi)::text),
  ('one-current unique index exists',                              (select n from idx) = 1,          (select n from idx)::text),
  ('0 plan venues without a current menu',                         (select n from no_current) = 0,   (select n from no_current)::text),
  ('0 plan venues smaller than their largest pre-incident menu',   (select n from smaller) = 0,      (select n from smaller)::text),
  ('every damaged venue (saved before Step 2) restored',           (select not_restored from damaged) = 0 and (select total from damaged) > 0,
                                                                   (select not_restored || ' of ' || total || ' not restored' from damaged)),
  ('4 pre-change function definitions saved',                      (select n from fdefs) = 4,        (select n from fdefs)::text),
  ('step 2 recorded (current_changed, damaged, picks)',            (select detail from run) is not null, (select detail::text from run)),
  ('step 3 finished for venues staged before the repair',          (select n from step3_left) = 0,   (select n from step3_left)::text),
  ('step 4 finished for candidates found before the repair',       (select n from step4_left) = 0,   (select n from step4_left)::text),
  ('candidate item-set index exists',                              (select n from cand_idx) = 1,     (select n from cand_idx)::text),
  ('cron 7 and 13 still paused (re-enable only after this gate)',  (select ok from cron_paused),     (select v from cron_paused))
) v(check_name, pass, value)
$rehearse_gate$ || ') g' INTO v;
    r := r || jsonb_build_object('release_gate', v, 'release_gate_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  EXCEPTION WHEN others THEN 
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      r := r || jsonb_build_object('release_gate', jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx), 'pass', false));
  END;
  -- repair rollback (after step 3, including the staging restore)
  t0 := clock_timestamp();
  BEGIN
    res := public.phg_repair_20260927_rollback();
    c := jsonb_build_object('result', res, 'ms', round(extract(epoch from clock_timestamp()-t0)*1000), 'multi_current_global', (select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x),
      'currency_mismatch_vs_backup', (select count(*) from public.menus m join public.phg_backup_menus_currency_20260927 bk on bk.id=m.id
                                       where (m.is_current, m.superseded_by, m.superseded_reason, m.superseded_at)
                                             is distinct from (bk.is_current, bk.superseded_by, bk.superseded_reason, bk.superseded_at)),
      'staging_backup_rows', (select count(*) from public.phg_backup_staging_dupes_20260927),
      'staging_still_superseded_by_repair', (select count(*) from public.staging_menu_extract s join public.phg_backup_staging_dupes_20260927 bk on bk.staging_id=s.id
                                              where s.superseded_reason = 'duplicate_item_set_of_sibling'));
    c := c || jsonb_build_object('pass', (c->>'multi_current_global')::int = 0 and (c->>'currency_mismatch_vs_backup')::int = 0
                                        and (c->>'staging_still_superseded_by_repair')::int = 0
                                        and (res->>'staging_rows_restored')::int = (c->>'staging_backup_rows')::int);
  EXCEPTION WHEN others THEN 
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      c := c || jsonb_build_object('ERROR', jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx), 'pass', false));
  END;
  r := r || jsonb_build_object('repair_rollback', c); c := '{}';
  -- function rollback, then ONE submit_menu call (the restored live 15-arg body) on a venue with a current menu
  t0 := clock_timestamp();
  BEGIN
    c := jsonb_build_object('fn_rollback_returns', public.phg_rollback_function_defs_20260927(), 'ms', round(extract(epoch from clock_timestamp()-t0)*1000),
      'unique_index_after', to_regclass('public.menus_one_current_per_account') is not null,
      'submit_menu_10arg_exists_after', to_regprocedure('public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb)') is not null,
      'restored_body_is_live', (select prosrc !~ 'phg_menu_source_key' from pg_proc where oid = 'public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb,text,text,text,text,boolean)'::regprocedure),
      'anon_or_authenticated_can_execute', (select jsonb_object_agg(b.signature, has_function_privilege('anon', b.signature::regprocedure, 'EXECUTE')
                                                                        or has_function_privilege('authenticated', b.signature::regprocedure, 'EXECUTE'))
                                              from public.phg_backup_function_defs_20260927 b),
      'service_role_can_execute', (select bool_and(has_function_privilege('service_role', b.signature::regprocedure, 'EXECUTE')) from public.phg_backup_function_defs_20260927 b));
    select id into cur_id from public.menus where account_id = acct and is_current;
    t1 := clock_timestamp();
    res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS','https://rehearsal.example.com/after-rollback',null,'html','unknown','rehearsal',null,md5('rehrb'||clock_timestamp()::text),'[{"section_name":"Food","section_type":"unsectioned","section_position":1,"items":[{"item_name":"Rehearsal Fries","item_type":"other","price":7},{"item_name":"Rehearsal Burger","item_type":"other","price":15}]}]'::jsonb,null,null,null,null,false);
    c := c || jsonb_build_object('submit_after_rollback', res, 'submit_ms', round(extract(epoch from clock_timestamp()-t1)*1000),
      'acct_current_count', (select count(*) from public.menus where account_id = acct and is_current),
      'old_current_demoted', (select not is_current from public.menus where id = cur_id));
    c := c || jsonb_build_object('pass', (c->>'fn_rollback_returns')::int = 4 and not (c->>'unique_index_after')::boolean
                                        and (c->>'submit_menu_10arg_exists_after')::boolean and (c->>'restored_body_is_live')::boolean
                                        and not exists (select 1 from jsonb_each_text(c->'anon_or_authenticated_can_execute') e where e.value::boolean)
                                        and (c->>'service_role_can_execute')::boolean
                                        and res ? 'menu_id' and (c->>'acct_current_count')::int = 1 and (c->>'old_current_demoted')::boolean);
  EXCEPTION WHEN others THEN 
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      c := c || jsonb_build_object('ERROR', jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx), 'pass', false));
  END;
  r := r || jsonb_build_object('function_rollback_and_submit', c); c := '{}';
  RAISE EXCEPTION 'REHEARSAL %', r;
END
$rehearse_main$;
