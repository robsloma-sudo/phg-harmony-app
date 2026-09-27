-- PHG-026 data repair (run AFTER 20260927190000_phg_menu_dedupe_one_current.sql, with cron 7 and 13 paused).
-- Reversible: every changed value is backed up first; rollback statements are at the end.
--
-- Step 1  backfill menus.source_key / item_keys / item_set_hash (12,229 rows, ~16 s)
-- Step 2  one best current menu per venue touched since 2026-09-27 00:00Z
--         rank: distinct items desc, drinks items desc (typed items + items in drinks sections), not an
--         item/event page, newest first (fresher prices on ties). Review round 1: the old rank put drinks items
--         first and counted only cocktail/spirit items, so full beer/wine menus scored 0 and 23 venues kept a
--         smaller menu. Acceptance: every one of the 185 venues gets back a menu at least as large as its old one.
-- Step 3  staging duplicates: live staging rows re-staged from sibling pages with the identical item
--         set are marked superseded (reason duplicate_item_set_of_sibling); one page per set survives
--         (not an item page first, then the earliest). Inflated cocktail counts in staging-based views
--         drop to the real menu.
-- Step 4  menu_source_candidates.item_set_hash backfill from their live staged items, so the
--         extraction-side duplicate check also sees venues extracted before the fix.

-- ---------- Step 1 ----------
update public.menus m
   set source_key    = public.phg_menu_source_key(m.evidence_url),
       item_keys     = k.keys,
       item_set_hash = public.phg_menu_key_set_hash(k.keys)
  from (select id, public.phg_menu_item_keys(id) as keys from public.menus) k
 where k.id = m.id and (m.item_keys is null or m.source_key is null);

-- ---------- Step 2 ----------
create table if not exists public.phg_backup_menus_currency_20260927 as
  select id, account_id, is_current, superseded_by, superseded_reason, superseded_at, now() as backed_up_at
  from public.menus;
alter table public.phg_backup_menus_currency_20260927 enable row level security;
revoke all on public.phg_backup_menus_currency_20260927 from anon, authenticated;

create table if not exists public.phg_repair_plan_menus_20260927 as
with touched as (select distinct account_id from public.menus where created_at >= '2026-09-27 00:00:00+00'),
m as (
  select m.id, m.account_id, m.created_at, m.is_current as was_current,
         cardinality(coalesce(m.item_keys, '{}'::text[])) as n,
         public.phg_menu_bev_count(m.id) as bev,
         public.phg_menu_url_is_item_page(m.evidence_url) as itemish
  from public.menus m join touched using (account_id)
),
ranked as (
  select m.*, row_number() over (partition by account_id
                                 order by n desc, bev desc, itemish asc, created_at desc, id) as rk
  from m
)
select id, account_id, was_current, (rk = 1) as make_current,
       first_value(id) over (partition by account_id order by rk) as chosen_id, n, bev, itemish
from ranked;
alter table public.phg_repair_plan_menus_20260927 enable row level security;
revoke all on public.phg_repair_plan_menus_20260927 from anon, authenticated;

update public.menus m
   set is_current        = p.make_current,
       superseded_by     = case when p.make_current then null else p.chosen_id end,
       superseded_reason = case when p.make_current then null else 'repair_20260927_best_single_menu' end,
       superseded_at     = case when p.make_current then null else now() end
  from public.phg_repair_plan_menus_20260927 p
 where p.id = m.id and m.is_current is distinct from p.make_current;

-- ---------- Step 3 (batched; review round 1: one statement over ~1M staging rows timed out) ----------
-- Only venues whose staging changed since 2026-09-27; 300 venues per call; progress kept in
-- phg_repair_step3_done so the runbook loops:  select public.phg_repair_step3_batch(300);  until it returns 0.
create table if not exists public.phg_backup_staging_dupes_20260927 (
  staging_id bigint primary key, account_id text, menu_page_url text, kept_page_url text, backed_up_at timestamptz default now());
alter table public.phg_backup_staging_dupes_20260927 enable row level security;
revoke all on public.phg_backup_staging_dupes_20260927 from anon, authenticated;
create table if not exists public.phg_repair_step3_done (account_id text primary key, dup_rows int, done_at timestamptz default now());
alter table public.phg_repair_step3_done enable row level security;
revoke all on public.phg_repair_step3_done from anon, authenticated;

create or replace function public.phg_repair_step3_batch(p_accounts int default 300)
returns int language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_accts text[]; v_n int;
begin
  set local statement_timeout = '110s';
  select array_agg(account_id) into v_accts from (
    select distinct s.account_id from public.staging_menu_extract s
     where s.superseded_at is null and s.account_id is not null and s.loaded_at >= '2026-09-27'
       and not exists (select 1 from public.phg_repair_step3_done d where d.account_id = s.account_id)
     order by s.account_id limit greatest(1, p_accounts)) a;
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
  get diagnostics v_n = row_count;
  insert into public.phg_repair_step3_done (account_id, dup_rows)
  select a, (select count(*) from public.phg_backup_staging_dupes_20260927 b where b.account_id = a) from unnest(v_accts) a
  on conflict (account_id) do nothing;
  return cardinality(v_accts);
end $$;
revoke all on function public.phg_repair_step3_batch(int) from public, anon, authenticated;

-- Runbook: repeat  select public.phg_repair_step3_batch(300);  until it returns 0.

-- ---------- Step 4 ----------
-- update public.menu_source_candidates c set item_set_hash = x.set_hash
--   from (select account_id, menu_page_url, public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price) order by public.phg_menu_item_key(item_name, item_price))) set_hash
--         from public.staging_menu_extract where superseded_at is null and item_type <> 'summary' group by 1, 2) x
--  where x.account_id = c.account_id and x.menu_page_url = c.source_url and c.item_set_hash is null;

-- ---------- Rollback ----------
-- update public.menus m set is_current = b.is_current, superseded_by = b.superseded_by,
--        superseded_reason = b.superseded_reason, superseded_at = b.superseded_at
--   from public.phg_backup_menus_currency_20260927 b where b.id = m.id
--    and (m.is_current, m.superseded_by, m.superseded_reason, m.superseded_at) is distinct from (b.is_current, b.superseded_by, b.superseded_reason, b.superseded_at);
-- update public.staging_menu_extract s set superseded_at = null, superseded_reason = null
--   from public.phg_backup_staging_dupes_20260927 b where b.staging_id = s.id and s.superseded_reason = 'duplicate_item_set_of_sibling';
