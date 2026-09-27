-- PHG-026 data repair (run AFTER 20260927190000_phg_menu_dedupe_one_current.sql, with cron 7 and 13 paused).
-- Reversible: every changed value is backed up first; rollback statements are at the end.
--
-- Step 1  backfill menus.source_key / item_keys / item_set_hash (12,229 rows, ~16 s)
-- Step 2  one best current menu per venue touched since 2026-09-27 00:00Z
--         rank: beverage items desc, distinct items desc, not an item/event page, oldest first
--         (restores the 185 venues whose larger older menu was replaced by an item-page copy)
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
                                 order by bev desc, n desc, itemish asc, created_at asc, id) as rk
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

-- ---------- Step 3 ----------
create table if not exists public.phg_backup_staging_dupes_20260927 (
  staging_id bigint primary key, account_id text, menu_page_url text, kept_page_url text, backed_up_at timestamptz default now());
alter table public.phg_backup_staging_dupes_20260927 enable row level security;
revoke all on public.phg_backup_staging_dupes_20260927 from anon, authenticated;

with pages as (
  select account_id, menu_page_url, min(id) as first_id,
         public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price) order by public.phg_menu_item_key(item_name, item_price))) as set_hash
  from public.staging_menu_extract
  where superseded_at is null and account_id is not null and item_type <> 'summary'
  group by account_id, menu_page_url
),
ranked as (
  select p.*, row_number() over (partition by account_id, set_hash
                                 order by public.phg_menu_url_is_item_page(menu_page_url) asc, first_id) as rk,
         first_value(menu_page_url) over (partition by account_id, set_hash
                                 order by public.phg_menu_url_is_item_page(menu_page_url) asc, first_id) as kept_url
  from pages p
)
insert into public.phg_backup_staging_dupes_20260927 (staging_id, account_id, menu_page_url, kept_page_url)
select s.id, s.account_id, s.menu_page_url, r.kept_url
from ranked r
join public.staging_menu_extract s on s.account_id = r.account_id and s.menu_page_url = r.menu_page_url and s.superseded_at is null
where r.rk > 1
on conflict (staging_id) do nothing;
-- Applied in batches (see runbook):
-- update public.staging_menu_extract s set superseded_at = now(), superseded_reason = 'duplicate_item_set_of_sibling'
--   from public.phg_backup_staging_dupes_20260927 b where b.staging_id = s.id and s.superseded_at is null and s.id between X and Y;

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
