-- PHG-026 post-release verification. Run after the migration, the repair and its runbook; run again after the first
-- cron 13 and cron 7 cycles. Every row must say pass = true.
with
multi as (select count(*) n from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x),
idx as (select count(*) n from pg_indexes where schemaname = 'public' and indexname = 'menus_one_current_per_account'),
touched as (select distinct account_id from public.menus where created_at >= '2026-09-27'),
no_current as (select count(*) n from touched t
                where not exists (select 1 from public.menus m where m.account_id = t.account_id and m.is_current)),
smaller as (
  select count(*) n from (
    select t.account_id,
           (select max(cardinality(coalesce(m.item_keys,'{}'))) from public.menus m where m.account_id = t.account_id and m.is_current) cur_n,
           (select max(cardinality(coalesce(m.item_keys,'{}'))) from public.menus m where m.account_id = t.account_id and m.created_at < '2026-09-27') old_n
    from touched t) z
  where z.old_n is not null and z.cur_n < z.old_n),
fdefs as (select count(*) n from public.phg_backup_function_defs_20260927),
step2 as (select detail from public.phg_repair_run_20260927 where step = 'step2'),
step3_left as (select count(distinct s.account_id) n from public.staging_menu_extract s
                where s.superseded_at is null and s.loaded_at >= '2026-09-27' and s.account_id is not null
                  and not exists (select 1 from public.phg_repair_step3_done d where d.account_id = s.account_id)),
step4_left as (select count(distinct c.account_id) n from public.menu_source_candidates c
                where c.item_set_hash is null and c.duplicate_of_candidate_id is null and c.account_id is not null
                  and not exists (select 1 from public.phg_repair_step4_done d where d.account_id = c.account_id)),
cand_idx as (select count(*) n from pg_indexes where indexname = 'menu_source_candidates_item_set_idx'),
-- after cron 7 resumes: menus created since release per distinct item set (expected close to 1.0; the incident was ~3.0)
since as (select min(ran_at) t from public.phg_repair_run_20260927),
per_set as (select count(*)::numeric / nullif(count(distinct (account_id, item_set_hash)), 0) r
              from public.menus, since where created_at > since.t),
promo as (select jsonb_object_agg(coalesce(promotion_status,'(queued)'), n) j
            from (select promotion_status, count(*) n from public.staging_menu_extract, since
                   where promoted_at > since.t group by 1) p)
select * from (values
  ('0 accounts with more than one current menu',            (select n from multi) = 0,        (select n from multi)::text),
  ('one-current unique index exists',                       (select n from idx) = 1,          (select n from idx)::text),
  ('0 touched venues without a current menu',               (select n from no_current) = 0,   (select n from no_current)::text),
  ('0 venues smaller than their largest pre-incident menu', (select n from smaller) = 0,      (select n from smaller)::text),
  ('4 pre-change function definitions saved',               (select n from fdefs) = 4,        (select n from fdefs)::text),
  ('step 2 ran (current_changed recorded)',                 (select detail from step2) is not null, (select detail::text from step2)),
  ('step 3 finished',                                       (select n from step3_left) = 0,   (select n from step3_left)::text),
  ('step 4 finished',                                       (select n from step4_left) = 0,   (select n from step4_left)::text),
  ('candidate item-set index exists',                       (select n from cand_idx) = 1,     (select n from cand_idx)::text),
  ('after cron 7: menus per distinct item set <= 1.2 (null until menus are created)',
                                                            coalesce((select r from per_set), 1) <= 1.2, (select r::text from per_set)),
  ('after cron 7: promotion outcomes (informational)',      true,                             (select j::text from promo))
) v(check_name, pass, value);
