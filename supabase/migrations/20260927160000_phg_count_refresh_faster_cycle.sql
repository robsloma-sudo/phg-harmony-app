-- PHG: per-venue menu counters refresh in ~1.5 h instead of ~28 h, recently changed
-- venues first, with a smaller lock footprint than before, and skipped work made visible.
--
-- Context (2026-09-27): refresh_menu_page_counts() (cron job 15, even minutes) and
-- refresh_menu_visual_counts() (cron job 18, odd minutes) were rewritten at 03:27Z to scan
-- 50 accounts per run behind a shared advisory lock. That removed the 09-26 deadlocks, but a
-- full pass over 41,886 accounts takes ~838 runs (~28 h), so per-venue counts lag.
--
-- What changes:
--  * batch 50 -> 1000 accounts. Measured on production (rolled back): page 1,259 ms,
--    visual 493 ms per 1000. Full cycle ~84 min. Cron limits for jobs 15/18 stay at 5 s.
--  * Lock footprint (review finding): the old bodies locked EVERY picked account FOR UPDATE
--    for the whole aggregate. Now the aggregate is computed first without locks, and only the
--    accounts whose counters actually differ are locked, FOR NO KEY UPDATE ... SKIP LOCKED,
--    for the final UPDATE only (milliseconds). FOR NO KEY UPDATE does not conflict with the
--    FOR KEY SHARE taken by foreign-key checks, so inserts of menus/candidates/documents/pages
--    for a venue are never blocked by a counter refresh. The UPDATE re-checks IS DISTINCT FROM.
--  * refresh_menu_visual_counts() first takes up to 300 accounts whose visual documents or
--    pages changed since its last run (oldest change first), then fills the batch from the
--    cursor sweep. A recent account that was skipped because another writer held its row pulls
--    the high-water mark back so it is retried next run; a truncated recent pass resumes from
--    the newest change it covered (minus 1 microsecond, so ties are re-read, never skipped).
--  * The shared advisory key (830927,1) is KEPT on purpose: it serialises the only two
--    accounts batch writers. Runs that find it held are counted (skipped_busy).
--  * Bookkeeping on phg_menu_refresh_cursors: runs, last_run_at, last_picked, last_changed,
--    last_locked_skipped, last_duration_ms, cycles_completed, last_cycle_completed_at,
--    skipped_busy, last_skipped_at, recent_since.
--  * Unchanged: columns maintained and their aggregate expressions, SECURITY DEFINER,
--    search_path, zero-argument signatures (cron, kick_menu_document_page_counting,
--    sync_candidate_page_counts_from_visuals and the count-menu-document-pages Edge function
--    call them with no arguments), EXECUTE grants (access tiers are being redesigned
--    separately; not changed here by instruction).

set local lock_timeout = '2s';

alter table public.phg_menu_refresh_cursors
  add column if not exists runs                    bigint      not null default 0,
  add column if not exists skipped_busy            bigint      not null default 0,
  add column if not exists last_run_at             timestamptz,
  add column if not exists last_skipped_at         timestamptz,
  add column if not exists last_picked             integer,
  add column if not exists last_changed            integer,
  add column if not exists last_locked_skipped     integer,
  add column if not exists last_duration_ms        integer,
  add column if not exists cycles_completed        bigint      not null default 0,
  add column if not exists last_cycle_completed_at timestamptz,
  add column if not exists recent_since            timestamptz;

comment on column public.phg_menu_refresh_cursors.skipped_busy is
  'Runs that found the shared accounts-writer advisory lock (830927,1) held and did nothing.';
comment on column public.phg_menu_refresh_cursors.last_locked_skipped is
  'Accounts whose counters differed but whose row was locked by another writer (retried later).';
comment on column public.phg_menu_refresh_cursors.recent_since is
  'visual_counts only: high-water mark for the recently-changed-accounts pass.';

create or replace function public.refresh_menu_page_counts()
 returns void
 language plpgsql
 security definer
 set search_path to 'public', 'pg_temp'
as $function$
declare
  c_batch   constant int := 1000;
  v_started timestamptz := clock_timestamp();
  v_after   text;
  v_last    text;
  v_picked  int;
  v_rows    jsonb;
  v_diff    int;
  v_changed int;
begin
  insert into public.phg_menu_refresh_cursors(name) values ('page_counts') on conflict (name) do nothing;
  if not pg_try_advisory_xact_lock(830927, 1) then
    update public.phg_menu_refresh_cursors
       set skipped_busy = skipped_busy + 1, last_skipped_at = now()
     where name in (select name from public.phg_menu_refresh_cursors
                     where name = 'page_counts' for update skip locked);
    return;
  end if;
  select coalesce(last_account_id, '') into v_after
    from public.phg_menu_refresh_cursors where name = 'page_counts';

  -- 1. aggregate without taking any row locks; keep only accounts whose counters differ
  with picked as materialized (
         select account_id from public.accounts
          where account_id > v_after order by account_id limit c_batch),
       agg as materialized (
         select x.account_id,
                count(c.id) filter (where c.menu_scope in ('beverage','beverage_candidate','mixed'))::int bf,
                count(c.id) filter (where c.menu_scope in ('food','food_candidate','mixed'))::int ff,
                count(c.id) filter (where c.menu_scope = 'mixed')::int mf,
                coalesce(sum(c.page_count) filter (where c.menu_scope in ('beverage','beverage_candidate','mixed')),0)::int bp,
                coalesce(sum(c.page_count) filter (where c.menu_scope in ('food','food_candidate','mixed')),0)::int fp,
                coalesce(sum(c.page_count),0)::int tp,
                coalesce(sum(c.page_count) filter (where c.menu_scope = 'unknown'),0)::int up,
                count(c.id) filter (where not c.page_count_exact)::int pf
           from picked x left join public.menu_source_candidates c on c.account_id = x.account_id
          group by x.account_id)
  select (select max(account_id) from picked), (select count(*) from picked),
         coalesce(jsonb_agg(to_jsonb(g)) filter (where g.account_id is not null), '[]'::jsonb)
    into v_last, v_picked, v_rows
    from agg g join public.accounts a using (account_id)
   where (a.beverage_menu_file_count, a.food_menu_file_count, a.mixed_menu_file_count,
          a.beverage_menu_page_count, a.food_menu_page_count, a.menu_page_count_total,
          a.menu_page_count_unclassified, a.menu_page_count_pending_files)
         is distinct from (g.bf, g.ff, g.mf, g.bp, g.fp, g.tp, g.up, g.pf);
  -- (an ungrouped aggregate always returns one row, so v_last/v_picked are set even when
  --  no account differs)
  v_diff := jsonb_array_length(v_rows);

  -- 2. lock only the differing rows, briefly, without blocking foreign-key checks
  with src as (
         select * from jsonb_to_recordset(v_rows)
           as x(account_id text, bf int, ff int, mf int, bp int, fp int, tp int, up int, pf int)),
       writable as materialized (
         select a.account_id from public.accounts a join src using (account_id)
          order by a.account_id for no key update of a skip locked),
       updated as (
         update public.accounts a
            set beverage_menu_file_count = g.bf, food_menu_file_count = g.ff, mixed_menu_file_count = g.mf,
                beverage_menu_page_count = g.bp, food_menu_page_count = g.fp, menu_page_count_total = g.tp,
                menu_page_count_unclassified = g.up, menu_page_count_pending_files = g.pf,
                menu_page_counts_refreshed_at = now()
           from src g join writable w using (account_id)
          where a.account_id = g.account_id
            and (a.beverage_menu_file_count, a.food_menu_file_count, a.mixed_menu_file_count,
                 a.beverage_menu_page_count, a.food_menu_page_count, a.menu_page_count_total,
                 a.menu_page_count_unclassified, a.menu_page_count_pending_files)
                is distinct from (g.bf, g.ff, g.mf, g.bp, g.fp, g.tp, g.up, g.pf)
         returning a.account_id)
  select count(*) into v_changed from updated;

  update public.phg_menu_refresh_cursors
     set last_account_id = case when coalesce(v_picked, 0) < c_batch then '' else v_last end,
         cycles_completed = cycles_completed + case when coalesce(v_picked, 0) < c_batch then 1 else 0 end,
         last_cycle_completed_at = case when coalesce(v_picked, 0) < c_batch then now() else last_cycle_completed_at end,
         runs = runs + 1, last_run_at = now(), last_picked = coalesce(v_picked, 0),
         last_changed = v_changed, last_locked_skipped = greatest(v_diff - v_changed, 0),
         last_duration_ms = (extract(epoch from clock_timestamp() - v_started) * 1000)::int,
         updated_at = now()
   where name = 'page_counts';
end
$function$;

create or replace function public.refresh_menu_visual_counts()
 returns void
 language plpgsql
 security definer
 set search_path to 'public', 'pg_temp'
as $function$
declare
  c_batch      constant int := 1000;
  c_recent     constant int := 300;
  v_started    timestamptz := clock_timestamp();
  v_after      text;
  v_since      timestamptz;
  v_new_since  timestamptz;
  v_last       text;
  v_recent_ids text[];
  v_recent_mx  timestamptz[];
  v_recent     int;
  v_truncated  boolean;
  v_sweep_ids  text[];
  v_swept      int;
  v_picked     int;
  v_rows       jsonb;
  v_diff       int;
  v_done       text[];
  v_changed    int;
  v_skip_mx    timestamptz;
begin
  insert into public.phg_menu_refresh_cursors(name) values ('visual_counts') on conflict (name) do nothing;
  if not pg_try_advisory_xact_lock(830927, 1) then
    update public.phg_menu_refresh_cursors
       set skipped_busy = skipped_busy + 1, last_skipped_at = now()
     where name in (select name from public.phg_menu_refresh_cursors
                     where name = 'visual_counts' for update skip locked);
    return;
  end if;
  select coalesce(last_account_id, ''), coalesce(recent_since, now() - interval '1 hour')
    into v_after, v_since
    from public.phg_menu_refresh_cursors where name = 'visual_counts';

  -- 1. accounts whose visual documents/pages changed since the last run, oldest change first
  --    (one extra row fetched to tell "exactly 300" from "more than 300")
  select coalesce(array_agg(account_id order by mx, account_id), '{}'::text[]),
         coalesce(array_agg(mx order by mx, account_id), '{}'::timestamptz[])
    into v_recent_ids, v_recent_mx
    from (select account_id, max(mx) mx from (
              select account_id, max(updated_at) mx from public.menu_visual_documents
               where updated_at > v_since group by account_id
              union all
              select account_id, max(updated_at) mx from public.menu_visual_pages
               where updated_at > v_since group by account_id) s
           group by account_id order by max(mx), account_id limit c_recent + 1) r;
  v_truncated := cardinality(v_recent_ids) > c_recent;
  if v_truncated then
    v_recent_ids := v_recent_ids[1:c_recent];
    v_recent_mx  := v_recent_mx[1:c_recent];
  end if;
  v_recent := cardinality(v_recent_ids);
  -- truncated: resume at the newest change covered, minus 1 us so equal timestamps are re-read;
  -- otherwise: this run's start with a 2-minute overlap for transactions still in flight
  v_new_since := case when v_truncated then v_recent_mx[v_recent] - interval '1 microsecond'
                      else v_started - interval '2 minutes' end;

  -- 2. fill the rest of the batch from the cursor sweep (backstop for everything else)
  select coalesce(array_agg(account_id order by account_id), '{}'::text[]), count(*), max(account_id)
    into v_sweep_ids, v_swept, v_last
    from (select account_id from public.accounts
           where account_id > v_after and account_id <> all (v_recent_ids)
           order by account_id limit (c_batch - v_recent)) s;
  v_picked := v_recent + v_swept;

  -- 3. aggregate without row locks; keep only accounts whose counters differ
  with picked as materialized (select unnest(v_recent_ids || v_sweep_ids) as account_id),
       d as materialized (
         select d.account_id, count(*)::int dc, coalesce(sum(d.page_count),0)::int pr,
                count(*) filter (where d.acquisition_status = 'downloaded')::int dd,
                count(*) filter (where d.acquisition_status = 'ready' and d.acquisition_method = 'firecrawl_screenshot_fallback')::int sd
           from public.menu_visual_documents d join picked x using (account_id) group by d.account_id),
       p as materialized (
         select p.account_id, count(*) filter (where p.render_status = 'ready')::int rd,
                count(*) filter (where p.render_status <> 'ready')::int pd
           from public.menu_visual_pages p join picked x using (account_id) group by p.account_id),
       agg as materialized (
         select x.account_id, coalesce(d.dc,0) dc, coalesce(d.pr,0) pr, coalesce(p.rd,0) rd,
                coalesce(p.pd,0) pd, coalesce(d.dd,0) dd, coalesce(d.sd,0) sd
           from picked x left join d using (account_id) left join p using (account_id))
  select coalesce(jsonb_agg(to_jsonb(g)), '[]'::jsonb) into v_rows
    from agg g join public.accounts a using (account_id)
   where (a.menu_visual_document_count, a.menu_visual_pages_required, a.menu_visual_pages_ready,
          a.menu_visual_pages_pending, a.menu_visual_downloaded_document_count,
          a.menu_visual_screenshot_document_count)
         is distinct from (g.dc, g.pr, g.rd, g.pd, g.dd, g.sd);
  v_diff := jsonb_array_length(v_rows);

  -- 4. lock only the differing rows, briefly, without blocking foreign-key checks
  with src as (
         select * from jsonb_to_recordset(v_rows)
           as x(account_id text, dc int, pr int, rd int, pd int, dd int, sd int)),
       writable as materialized (
         select a.account_id from public.accounts a join src using (account_id)
          order by a.account_id for no key update of a skip locked),
       updated as (
         update public.accounts a
            set menu_visual_document_count = g.dc, menu_visual_pages_required = g.pr,
                menu_visual_pages_ready = g.rd, menu_visual_pages_pending = g.pd,
                menu_visual_downloaded_document_count = g.dd,
                menu_visual_screenshot_document_count = g.sd,
                menu_visual_counts_refreshed_at = now()
           from src g join writable w using (account_id)
          where a.account_id = g.account_id
            and (a.menu_visual_document_count, a.menu_visual_pages_required, a.menu_visual_pages_ready,
                 a.menu_visual_pages_pending, a.menu_visual_downloaded_document_count,
                 a.menu_visual_screenshot_document_count)
                is distinct from (g.dc, g.pr, g.rd, g.pd, g.dd, g.sd)
         returning a.account_id)
  select coalesce(array_agg(account_id), '{}'::text[]) into v_done from updated;
  v_changed := cardinality(v_done);

  -- 5. a recent account skipped because its row was locked must be seen again next run
  select min(r.mx) into v_skip_mx
    from unnest(v_recent_ids, v_recent_mx) as r(account_id, mx)
    join jsonb_to_recordset(v_rows) as s(account_id text) using (account_id)
   where r.account_id <> all (v_done);
  if v_skip_mx is not null then
    v_new_since := least(v_new_since, v_skip_mx - interval '1 microsecond');
  end if;

  update public.phg_menu_refresh_cursors
     set last_account_id = case when v_swept < (c_batch - v_recent) then '' else coalesce(v_last, v_after) end,
         cycles_completed = cycles_completed + case when v_swept < (c_batch - v_recent) then 1 else 0 end,
         last_cycle_completed_at = case when v_swept < (c_batch - v_recent) then now() else last_cycle_completed_at end,
         recent_since = v_new_since,
         runs = runs + 1, last_run_at = now(), last_picked = v_picked, last_changed = v_changed,
         last_locked_skipped = greatest(v_diff - v_changed, 0),
         last_duration_ms = (extract(epoch from clock_timestamp() - v_started) * 1000)::int,
         updated_at = now()
   where name = 'visual_counts';
end
$function$;
