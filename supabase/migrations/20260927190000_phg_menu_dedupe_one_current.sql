-- PHG-026 (2026-09-27): stop order-item duplicate menus from replacing venues' real menus.
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
--   same source (canonical URL)      -> re-capture replaces, unless identical or a strict subset
--   other source, >=90% contained    -> duplicate, nothing inserted
--   zero-item capture beside a menu  -> ignored
--   item/event/product page          -> never replaces a non-empty current menu (stored as alternate), even
--                                       when it shares the menu's source key (?item= is stripped from the key)
--   same source, less than half the items -> partial re-capture, stored as alternate
--   other source, more distinct items (then more drinks items) -> replaces; otherwise stored as alternate
-- "Drinks items" = cocktail / spirit_pour items plus every item in a cocktails / wine / beer / spirits section
-- (beer and wine are stored as item_type 'other' inside typed sections).
-- Alternates are real rows with is_current=false and superseded_reason, so nothing is lost.
-- Menus are never deleted. submit_menu locks the account row first (the same lock the extraction save takes),
-- then an advisory lock, so both writers of one account queue behind each other.
--
-- Review round 1 fixes (2026-09-28): drinks count includes typed sections; size decides before drinks count;
-- item-page and partial-recapture guards on the same-source branch; empty current menus can be replaced;
-- extraction duplicate branch supersedes the candidate's own stale rows and never matches an empty duplicate;
-- helpers inlinable (no SET) so the repair can run at table scale.
--
-- Apply with cron 7 (promotion) and 13 (extraction) PAUSED. Data repair is a separate script.

set local lock_timeout = '3s';

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

create or replace function public.phg_menu_key_set_hash(p_keys text[])
returns text language sql immutable parallel safe as $$
  select pg_catalog.md5(pg_catalog.array_to_string(coalesce(p_keys, '{}'::text[]), '~'))
$$;

revoke all on function public.phg_menu_source_key(text), public.phg_menu_url_is_item_page(text),
  public.phg_menu_item_key(text, numeric), public.phg_menu_payload_item_keys(jsonb),
  public.phg_menu_payload_bev_count(jsonb), public.phg_menu_extract_item_keys(jsonb),
  public.phg_menu_item_keys(uuid), public.phg_menu_bev_count(uuid), public.phg_menu_key_set_hash(text[])
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
 c record; c_keys text[]; c_n int; c_bev int; v_ov int;
 v_make_current boolean := true; v_alt_of uuid; v_reason text; v_supersede uuid[] := '{}';
 c_dup_ratio constant numeric := 0.9;
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
 for c in select m.id, coalesce(m.source_key, public.phg_menu_source_key(m.evidence_url)) as source_key, m.item_keys
            from public.menus m where m.account_id=p_account_id and m.is_current
           order by m.created_at desc, m.id for update loop
  c_keys := coalesce(c.item_keys, public.phg_menu_item_keys(c.id));
  c_n    := cardinality(c_keys);
  v_ov   := cardinality(array(select unnest(v_keys) intersect select unnest(c_keys)));
  if c.source_key is not distinct from v_source_key then
   -- Same source: identical or strict-subset re-capture keeps the current menu.
   if v_n > 0 and v_ov = v_n and c_n >= v_n then
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
    v_supersede := v_supersede || c.id; v_reason := coalesce(v_reason, 'same_source_recapture');
   end if;
  else
   -- Other source: (near-)contained in an equal-or-larger current menu is a duplicate.
   if v_n > 0 and c_n >= v_n and v_ov >= ceil(c_dup_ratio * v_n) then
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
 insert into public.menus(menu_id,account_id,source_id,evidence_url,menu_title,menu_format,extraction_confidence,extraction_notes,published_date,content_hash,is_current,superseded_by,superseded_reason,superseded_at,raw_content,raw_content_type,raw_content_chars,platform,source_file_url,needs_vision_pass,item_count,source_key,item_keys,item_set_hash)
 values(v_menu_code,p_account_id,v_source_id,p_evidence_url,p_menu_title,p_menu_format,p_extraction_confidence,p_extraction_notes,p_published_date,p_content_hash,v_make_current,
        case when v_make_current then null else v_alt_of end, case when v_make_current then null else v_reason end, case when v_make_current then null else now() end,
        p_raw_content,p_raw_content_type,length(p_raw_content),p_platform,p_source_file_url,p_needs_vision_pass,v_expected_items,v_source_key,v_keys,v_set_hash) returning id into v_menu_id;

 if cardinality(v_supersede) > 0 then
  update public.menus
     set is_current=false, superseded_by=v_menu_id, superseded_at=now(), superseded_reason=v_reason
   where id = any(v_supersede) and is_current;
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

-- The 10-arg overload was a second, divergent write path (account-wide supersession, no cocktail
-- inference). Keep the signature for any old caller but route it through the 15-arg logic.
create or replace function public.submit_menu(p_account_id text, p_source_code text, p_evidence_url text, p_menu_title text, p_menu_format text, p_extraction_confidence text, p_extraction_notes text, p_published_date date, p_content_hash text, p_sections jsonb)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
begin
  return public.submit_menu(p_account_id, p_source_code, p_evidence_url, p_menu_title, p_menu_format,
                            p_extraction_confidence, p_extraction_notes, p_published_date, p_content_hash,
                            p_sections, null::text, null::text, null::text, null::text, false);
end $function$;

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
 p_pages:=least(20,greatest(1,coalesce(p_pages,1)));
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
revoke all on function public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb) from public, anon, authenticated;
revoke all on function public.promote_clean_menu_batch(integer) from public, anon, authenticated;
revoke all on function public.phg_save_menu_candidate_extraction(bigint,timestamp with time zone,uuid,jsonb,text,text,text) from public, anon, authenticated;
