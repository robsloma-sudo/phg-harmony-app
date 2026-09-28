-- PHG-026 data repair (run AFTER 20260927190000_phg_menu_dedupe_one_current.sql, with cron 7 and 13 paused).
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
