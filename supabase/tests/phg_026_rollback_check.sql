-- PHG-026 rollback check (safety SF-E / M2, round 5). Run right after `select public.phg_repair_20260927_rollback();`
-- (as postgres, cron 7 and 13 still paused). Three queries:
--   1. checks: every row must say pass = true;
--   2. review candidates: the venues, pages and candidates the rollback did NOT put back, to look at by hand;
--   3. ONLY before a roll-forward (file 2 header, RF1): saves query 2's list and the run rows into
--      public.phg_repair_rollback_saved_20260927, because the roll-forward DROPs the tables query 2 reads (m3).
-- The rollback records its result (counts + skipped_accounts) in phg_repair_run_20260927 as step 'rollback'.
-- Scope: plan venues whose current menu Step 2 changed, plus Step-3 staging venues, minus skipped_accounts.

-- ===== 1. checks =====
with
rb as (select ran_at t, detail from public.phg_repair_run_20260927 where step = 'rollback'),
skipped as (select x->>'account_id' account_id, x->>'reason' reason, x->>'scope' scope
              from rb, jsonb_array_elements(coalesce(rb.detail->'skipped_accounts', '[]'::jsonb)) x),
cur_scope as (select distinct p.account_id from public.phg_repair_plan_menus_20260927 p
               where p.make_current <> p.was_current
                 and not exists (select 1 from skipped s where s.account_id = p.account_id)),
multi as (select count(*) n from (select account_id from public.menus where is_current group by 1 having count(*) > 1) x),
-- every menu of a rolled-back venue has exactly its backed-up currency again
currency_diff as (select count(*) n from public.menus m
                    join public.phg_backup_menus_currency_20260927 b on b.id = m.id
                    join cur_scope c on c.account_id = m.account_id
                   where (m.is_current, m.superseded_by, m.superseded_reason, m.superseded_at)
                         is distinct from (b.is_current, b.superseded_by, b.superseded_reason, b.superseded_at)),
cur_none as (select count(*) n from cur_scope c
              where not exists (select 1 from public.menus m where m.account_id = c.account_id and m.is_current)
                and exists (select 1 from public.phg_backup_menus_currency_20260927 b where b.account_id = c.account_id and b.is_current)),
-- staging rows of rolled-back venues still superseded by the repair, other than pages re-extracted since the backup
stg_left as (select count(*) n from public.staging_menu_extract s
               join public.phg_backup_staging_dupes_20260927 b on b.staging_id = s.id
              where s.superseded_reason = 'duplicate_item_set_of_sibling'
                and not exists (select 1 from skipped k where k.account_id = b.account_id)
                and not exists (select 1 from public.staging_menu_extract n
                                 where n.account_id = s.account_id and n.menu_page_url = s.menu_page_url
                                   and n.superseded_at is null and n.loaded_at > b.backed_up_at)),
skip_bad as (select count(*) n from skipped k
              where (select count(*) from public.menus m where m.account_id = k.account_id and m.is_current) <> 1),
cron_paused as (select count(*) = 2 and coalesce(bool_and(not active), false) ok,
                       count(*) || ' jobs; ' || coalesce(string_agg(jobid || ':' || active, ',' order by jobid), '') v
                  from cron.job where jobid in (7, 13))
select * from (values
  ('rollback recorded in phg_repair_run_20260927',                  (select count(*) from rb) = 1,
                                                                    (select t::text || ' ' || (detail - 'skipped_accounts')::text from rb)),
  ('0 accounts with more than one current menu',                    (select n from multi) = 0,          (select n from multi)::text),
  ('rolled-back venues: every menu has its backed-up currency again', (select n from currency_diff) = 0, (select n from currency_diff)::text),
  ('rolled-back venues: none without a current menu (that had one)', (select n from cur_none) = 0,      (select n from cur_none)::text),
  ('rolled-back venues: repair-superseded staging rows restored (except pages re-extracted since)',
                                                                    (select n from stg_left) = 0,       (select n from stg_left)::text),
  ('every skipped venue has exactly one current menu',              (select n from skip_bad) = 0,       (select n from skip_bad)::text),
  ('skipped venues (informational; listed by query 2)',              true,
       (select count(*) || ' (' || count(*) filter (where reason = 'newer_menu') || ' newer menu, '
               || count(*) filter (where reason = 'multi_current_backup') || ' multi-current backup)' from skipped)),
  ('one-current unique index (informational: gone after the function rollback)', true,
       (select count(*)::text from pg_indexes where schemaname = 'public' and indexname = 'menus_one_current_per_account')),
  ('cron 7 and 13 exist and are still paused',                      (select ok from cron_paused),       (select v from cron_paused))
) v(check_name, pass, value);

-- ===== 2. review candidates =====
-- Skipped venues (the rollback left them exactly as they were), backed-up staging pages still superseded by the
-- repair (skipped venue, or page re-extracted since), and what the NEW extraction save did after release, which no
-- rollback undoes (spec should-fix 2): staging rows it superseded as copies of a sibling page (not in the Step-3
-- backup) and candidates it marked as duplicates (status 'review', duplicate_of_candidate_id set; the roll-forward
-- puts them back to 'retry', RF2). For venues: what is current now and the largest pre-incident menu.
with
rb as (select detail from public.phg_repair_run_20260927 where step = 'rollback'),
s2 as (select ran_at t from public.phg_repair_run_20260927 where step = 'step2'),
skipped as (select x->>'account_id' account_id, x->>'reason' reason, x->>'scope' scope
              from rb, jsonb_array_elements(coalesce(rb.detail->'skipped_accounts', '[]'::jsonb)) x)
select k.account_id, 'skipped_' || k.reason as review_reason, k.scope as detail,
       (select m.id::text || ' (' || cardinality(coalesce(m.item_keys, '{}'::text[])) || ' items, ' || m.evidence_url || ')'
          from public.menus m where m.account_id = k.account_id and m.is_current limit 1) as current_menu,
       (select max(cardinality(coalesce(m.item_keys, '{}'::text[]))) from public.menus m
         where m.account_id = k.account_id and m.created_at < '2026-09-27 00:00:00+00') as largest_pre_incident_items,
       (select count(*) from public.menus m where m.account_id = k.account_id
           and not exists (select 1 from public.phg_backup_menus_currency_20260927 b where b.id = m.id)) as menus_after_repair
  from skipped k
union all
select b.account_id, 'staging_page_not_restored',
       b.menu_page_url || ' (' || count(*) || ' rows; kept page ' || min(b.kept_page_url) || ')',
       null, null, null
  from public.phg_backup_staging_dupes_20260927 b
  join public.staging_menu_extract s on s.id = b.staging_id and s.superseded_reason = 'duplicate_item_set_of_sibling'
 group by b.account_id, b.menu_page_url
union all
select s.account_id, 'staging_superseded_after_release',
       s.menu_page_url || ' (' || count(*) || ' rows, superseded ' || min(s.superseded_at)::text || ')',
       null, null, null
  from public.staging_menu_extract s, s2
 where s.superseded_reason = 'duplicate_item_set_of_sibling' and s.superseded_at >= s2.t
   and not exists (select 1 from public.phg_backup_staging_dupes_20260927 b where b.staging_id = s.id)
 group by s.account_id, s.menu_page_url
union all
select c.account_id, 'candidate_marked_duplicate',
       'candidate ' || c.id || ' (' || c.status || ', duplicate of ' || c.duplicate_of_candidate_id
         || ', attempts ' || coalesce(c.extraction_attempt_count, 0) || '): ' || c.source_url,
       null, null, null
  from public.menu_source_candidates c
 where c.duplicate_of_candidate_id is not null
 order by 1, 2, 3;

-- ===== 3. save before a roll-forward DROP (RF1 in file 2's header; not part of the plain rollback check) =====
-- Keeps the run rows (step2, rollback) and the query-2 list after the roll-forward drops the repair tables. Re-running
-- it adds another snapshot row. SELECT-only for service_role, like every table the repair creates.
create table if not exists public.phg_repair_rollback_saved_20260927 (
  saved_at timestamptz not null default now(), run_rows jsonb not null, review_candidates jsonb not null);
alter table public.phg_repair_rollback_saved_20260927 enable row level security;
revoke all on public.phg_repair_rollback_saved_20260927 from anon, authenticated, service_role;
grant select on public.phg_repair_rollback_saved_20260927 to service_role;
insert into public.phg_repair_rollback_saved_20260927 (run_rows, review_candidates)
select (select coalesce(jsonb_agg(to_jsonb(r) order by r.step), '[]'::jsonb) from public.phg_repair_run_20260927 r),
       coalesce((select jsonb_agg(to_jsonb(q)) from (
         with
         rb as (select detail from public.phg_repair_run_20260927 where step = 'rollback'),
         s2 as (select ran_at t from public.phg_repair_run_20260927 where step = 'step2'),
         skipped as (select x->>'account_id' account_id, x->>'reason' reason, x->>'scope' scope
                       from rb, jsonb_array_elements(coalesce(rb.detail->'skipped_accounts', '[]'::jsonb)) x)
         select k.account_id, 'skipped_' || k.reason as review_reason, k.scope as detail,
                (select m.id::text || ' (' || cardinality(coalesce(m.item_keys, '{}'::text[])) || ' items, ' || m.evidence_url || ')'
                   from public.menus m where m.account_id = k.account_id and m.is_current limit 1) as current_menu,
                (select max(cardinality(coalesce(m.item_keys, '{}'::text[]))) from public.menus m
                  where m.account_id = k.account_id and m.created_at < '2026-09-27 00:00:00+00') as largest_pre_incident_items,
                (select count(*) from public.menus m where m.account_id = k.account_id
                    and not exists (select 1 from public.phg_backup_menus_currency_20260927 b where b.id = m.id)) as menus_after_repair
           from skipped k
         union all
         select b.account_id, 'staging_page_not_restored',
                b.menu_page_url || ' (' || count(*) || ' rows; kept page ' || min(b.kept_page_url) || ')', null, null, null
           from public.phg_backup_staging_dupes_20260927 b
           join public.staging_menu_extract s on s.id = b.staging_id and s.superseded_reason = 'duplicate_item_set_of_sibling'
          group by b.account_id, b.menu_page_url
         union all
         select s.account_id, 'staging_superseded_after_release',
                s.menu_page_url || ' (' || count(*) || ' rows, superseded ' || min(s.superseded_at)::text || ')', null, null, null
           from public.staging_menu_extract s, s2
          where s.superseded_reason = 'duplicate_item_set_of_sibling' and s.superseded_at >= s2.t
            and not exists (select 1 from public.phg_backup_staging_dupes_20260927 b where b.staging_id = s.id)
          group by s.account_id, s.menu_page_url
         union all
         select c.account_id, 'candidate_marked_duplicate',
                'candidate ' || c.id || ' (' || c.status || ', duplicate of ' || c.duplicate_of_candidate_id
                  || ', attempts ' || coalesce(c.extraction_attempt_count, 0) || '): ' || c.source_url, null, null, null
           from public.menu_source_candidates c
          where c.duplicate_of_candidate_id is not null) q), '[]'::jsonb)
returning saved_at, jsonb_array_length(run_rows) as run_rows, jsonb_array_length(review_candidates) as review_candidates;
