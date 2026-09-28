-- PHG-026 monitor. Run after cron 13 / 7 resume (after their first cycles, then daily for a week).
-- Only invariants that stay true whatever venues legitimately re-capture: one current menu per venue, no return of the
-- incident's duplicate-menu rate, no plan venue shrinking below its largest pre-incident menu except through a
-- re-capture of its own page, and no venue flip-flopping. Everything else is informational (pass is always true).
-- Round 5 (safety SF-C): the smaller-than-pre-incident row and the churn row are pass/fail.
-- Pre-publish (safety m4, spec minor): the flip-flop row counts only current-menu changes between DIFFERENT sources (the
-- replaced menu's source key differs from its replacement's; a venue re-capturing its own page is not a flip-flop), and
-- the changes since release are shown split by kind (growth / non-growing same source / non-growing other source).
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
                                          'same_source_price_enrichment','larger_beverage_capture','contained_in_larger_capture',
                                          'real_page_over_item_page')
                                   group by 1 having count(*) > 2) x),
-- every current-menu change since release: the replaced menu, its replacement, growth or not, same source or not
changes as (select o.account_id,
                   o.superseded_reason in ('larger_beverage_capture','contained_in_larger_capture') as growth,
                   coalesce(o.source_key, public.phg_menu_source_key(o.evidence_url))
                     is not distinct from coalesce(r.source_key, public.phg_menu_source_key(r.evidence_url)) as same_source
              from public.menus o join public.menus r on r.id = o.superseded_by, since
             where o.superseded_at > since.t and o.superseded_reason in
                   ('newer_near_identical_capture','price_enrichment_other_source','same_source_recapture',
                    'same_source_price_enrichment','larger_beverage_capture','contained_in_larger_capture',
                    'real_page_over_item_page')),
-- pass/fail churn: current-menu changes that did NOT grow the menu (a larger capture is progress, not a flip-flop) and
-- went from one source to ANOTHER (m4). More than 2 such changes in one venue since release is the flip-flop pattern
-- the damping is meant to stop.
flip as (select count(*) n, coalesce(string_agg(account_id, ',' order by account_id) filter (where rn <= 20), '') ids
           from (select account_id, row_number() over (order by account_id) rn from changes
                  where not growth and not same_source
                  group by 1 having count(*) > 2) x),
by_kind as (select count(*) filter (where growth) g, count(distinct account_id) filter (where growth) gv,
                   count(*) filter (where not growth and same_source) s, count(distinct account_id) filter (where not growth and same_source) sv,
                   count(*) filter (where not growth and not same_source) o, count(distinct account_id) filter (where not growth and not same_source) ov
              from changes),
-- plan venues whose current menu has fewer distinct items than their largest pre-incident menu. Allowed only when the
-- current menu is a re-capture of the previous current menu's own page (the venue shortened that page).
shrunk as (
  select count(*) n,
         count(*) filter (where same_page) allowed,
         coalesce(array_to_string((array_agg(account_id order by account_id) filter (where not same_page))[1:20], ','), '') ids
    from (select t.account_id, coalesce(c.same_page, false) same_page
            from (select distinct account_id from public.phg_repair_plan_menus_20260927) t
            cross join lateral (select max(cardinality(coalesce(m.item_keys, '{}'::text[]))) old_n from public.menus m
                                 where m.account_id = t.account_id and m.created_at < '2026-09-27 00:00:00+00') o
            left join lateral (select cardinality(coalesce(m.item_keys, '{}'::text[])) cur_n,
                                      exists (select 1 from public.menus d where d.superseded_by = m.id
                                                 and d.superseded_reason in ('same_source_recapture','same_source_price_enrichment')) same_page
                                 from public.menus m where m.account_id = t.account_id and m.is_current) c on true
           where o.old_n is not null and coalesce(c.cur_n, 0) < o.old_n) z)
select * from (values
  ('0 accounts with more than one current menu',            (select n from multi) = 0,   (select n from multi)::text),
  ('one-current unique index exists',                       (select n from idx) = 1,     (select n from idx)::text),
  ('menus per distinct item set since release <= 1.2 (null until menus are created)',
                                                            coalesce((select r from per_set), 1) <= 1.2,
                                                            (select round(r, 3)::text || ' (' || n || ' menus / ' || sets || ' sets)' from per_set)),
  ('submit_menu outcomes since release (informational)',    true, (select j::text from created)),
  ('promotion outcomes since release (informational)',      true, (select j::text from promo)),
  ('0 plan venues smaller than their largest pre-incident menu (except a re-capture of their own page)',
                                                            (select n - allowed from shrunk) = 0,
                                                            (select n || ' smaller, ' || allowed || ' allowed (same-page re-capture)'
                                                                    || case when ids <> '' then '; review (first 20): ' || ids else '' end from shrunk)),
  ('0 venues with > 2 non-growing current-menu changes between different sources since release (flip-flop)',
                                                            (select n from flip) = 0,
                                                            (select n || case when ids <> '' then ' (first 20: ' || ids || ')' else '' end from flip)),
  ('venues with > 2 current-menu changes of any kind since release (informational)', true, (select n::text from churn)),
  ('current-menu changes since release by kind (informational): changes / venues',
                                                            true,
                                                            (select 'growth ' || g || ' / ' || gv || '; non-growing same source ' || s || ' / ' || sv
                                                                    || '; non-growing other source ' || o || ' / ' || ov from by_kind))
) v(check_name, pass, value)
