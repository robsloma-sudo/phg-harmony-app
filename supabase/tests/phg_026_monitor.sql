-- PHG-026 monitor. Run after cron 13 / 7 resume (after their first cycles, then daily for a week).
-- Only invariants that stay true whatever venues legitimately re-capture: one current menu per venue, and no return
-- of the incident's duplicate-menu rate. Everything else is informational (pass is always true).
with
since as (select ran_at t from public.phg_repair_run_20260927 where step = 'step2'),
multi as (select count(*) n from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x),
idx as (select count(*) n from pg_indexes where schemaname = 'public' and indexname = 'menus_one_current_per_account'),
-- menus created since release per distinct (venue, item set): the incident was ~3.0; expected close to 1.0
per_set as (select count(*) n, count(distinct (account_id, item_set_hash)) sets,
                   count(*)::numeric / nullif(count(distinct (account_id, item_set_hash)), 0) r
              from public.menus, since where created_at > since.t),
-- submit_menu outcomes since release, as stored: current / alternate reason
created as (select jsonb_object_agg(k, n) j from (
              select case when is_current then 'current' else coalesce(superseded_reason, 'superseded') end k, count(*) n
                from public.menus, since where created_at > since.t group by 1) x),
-- promotion outcomes since release (staging rows by promotion_status)
promo as (select jsonb_object_agg(coalesce(promotion_status, '(none)'), n) j
            from (select promotion_status, count(*) n from public.staging_menu_extract, since
                   where promoted_at > since.t group by 1) p),
-- venues whose current menu changed more than twice since release (flip-flop watch)
churn as (select count(*) n from (select account_id from public.menus, since
                                   where superseded_at > since.t and superseded_reason in
                                         ('newer_near_identical_capture','price_enrichment_other_source','same_source_recapture',
                                          'same_source_price_enrichment','larger_beverage_capture','contained_in_larger_capture')
                                   group by 1 having count(*) > 2) x)
select * from (values
  ('0 accounts with more than one current menu',            (select n from multi) = 0,   (select n from multi)::text),
  ('one-current unique index exists',                       (select n from idx) = 1,     (select n from idx)::text),
  ('menus per distinct item set since release <= 1.2 (null until menus are created)',
                                                            coalesce((select r from per_set), 1) <= 1.2,
                                                            (select round(r, 3)::text || ' (' || n || ' menus / ' || sets || ' sets)' from per_set)),
  ('submit_menu outcomes since release (informational)',    true, (select j::text from created)),
  ('promotion outcomes since release (informational)',      true, (select j::text from promo)),
  ('venues with > 2 current-menu changes since release (informational)', true, (select n::text from churn))
) v(check_name, pass, value)
