-- PHG-026 release gate. Run ONCE, right after the runbook (both migrations, steps 1-4, the CONCURRENTLY index) and
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
-- both jobs must exist (count = 2) and both be inactive: a missing job is a failure, not a pass
cron_paused as (select count(*) = 2 and coalesce(bool_and(not active), false) ok,
                       count(*) || ' jobs; ' || coalesce(string_agg(jobid || ':' || active, ',' order by jobid), '') v
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
  ('cron 7 and 13 exist and are still paused (re-enable only after this gate)', (select ok from cron_paused),     (select v from cron_paused))
) v(check_name, pass, value)
