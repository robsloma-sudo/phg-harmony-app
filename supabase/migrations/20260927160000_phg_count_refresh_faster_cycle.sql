-- PHG: per-venue menu counters refresh in ~1.5 h instead of ~28 h, recently changed
-- venues first, and skipped runs become visible.
--
-- Context (2026-09-27): refresh_menu_page_counts() (cron job 15, even minutes) and
-- refresh_menu_visual_counts() (cron job 18, odd minutes) were rewritten at 03:27Z to scan
-- 50 accounts per run behind a shared advisory lock, which removed the 09-26 deadlocks but
-- means a full pass over 41,886 accounts takes ~838 runs (~28 h), so per-venue counts lag.
--
-- What changes:
--  * batch 50 -> 1000 accounts (measured: 1.77 s for the page-count aggregate over 1000
--    accounts on 2026-09-27 15:35Z; visual counts are cheaper). Full cycle ~84 min.
--  * refresh_menu_visual_counts() first takes up to 300 accounts whose visual documents or
--    pages changed since its last run (menu_visual_documents/pages are ~16k/~20k rows, so
--    the scan is cheap), then fills the rest of the batch from the cursor sweep. Gallery
--    progress per venue is therefore current within minutes.
--  * The shared advisory key (830927,1) is KEPT on purpose: it serialises the only two
--    accounts-table batch writers, which is what keeps the deadlocks gone. The jobs run on
--    alternate minutes and finish in ~1-2 s, so they do not normally collide; when one is
--    skipped it is now counted in phg_menu_refresh_cursors.skipped_busy / last_skipped_at.
--  * Run bookkeeping: runs, last_run_at, last_picked, last_changed, last_duration_ms,
--    cycles_completed, last_cycle_completed_at, recent_since.
--  * The cursor wraps as soon as a short batch reaches the end (no empty run per cycle).
--  * Unchanged: FOR UPDATE SKIP LOCKED on accounts (never waits on another writer), the
--    IS DISTINCT FROM change filter (untouched rows are not rewritten), SECURITY DEFINER,
--    search_path, zero-argument signatures (cron, kick_menu_document_page_counting and
--    the count-menu-document-pages Edge function call them with no arguments), grants.

alter table public.phg_menu_refresh_cursors
  add column if not exists runs                    bigint      not null default 0,
  add column if not exists skipped_busy            bigint      not null default 0,
  add column if not exists last_run_at             timestamptz,
  add column if not exists last_skipped_at         timestamptz,
  add column if not exists last_picked             integer,
  add column if not exists last_changed            integer,
  add column if not exists last_duration_ms        integer,
  add column if not exists cycles_completed        bigint      not null default 0,
  add column if not exists last_cycle_completed_at timestamptz,
  add column if not exists recent_since            timestamptz;

comment on column public.phg_menu_refresh_cursors.skipped_busy is
  'Runs that found the shared accounts-writer advisory lock (830927,1) held and did nothing.';
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
  select last_account_id into v_after from public.phg_menu_refresh_cursors where name = 'page_counts';
  v_after := coalesce(v_after, '');

  with picked as materialized (
         select account_id from public.accounts
          where account_id > v_after order by account_id limit c_batch),
       agg as materialized (
         select x.account_id,
                count(c.id) filter (where c.menu_scope in ('beverage','beverage_candidate','mixed'))::int beverage_files,
                count(c.id) filter (where c.menu_scope in ('food','food_candidate','mixed'))::int food_files,
                count(c.id) filter (where c.menu_scope = 'mixed')::int mixed_files,
                coalesce(sum(c.page_count) filter (where c.menu_scope in ('beverage','beverage_candidate','mixed')),0)::int beverage_pages,
                coalesce(sum(c.page_count) filter (where c.menu_scope in ('food','food_candidate','mixed')),0)::int food_pages,
                coalesce(sum(c.page_count),0)::int total_pages,
                coalesce(sum(c.page_count) filter (where c.menu_scope = 'unknown'),0)::int unclassified_pages,
                count(c.id) filter (where not c.page_count_exact)::int pending_files
           from picked x left join public.menu_source_candidates c on c.account_id = x.account_id
          group by x.account_id),
       writable as materialized (
         select a.account_id from public.accounts a join picked x using (account_id)
          order by a.account_id for update of a skip locked),
       updated as (
         update public.accounts a
            set beverage_menu_file_count = g.beverage_files, food_menu_file_count = g.food_files,
                mixed_menu_file_count = g.mixed_files, beverage_menu_page_count = g.beverage_pages,
                food_menu_page_count = g.food_pages, menu_page_count_total = g.total_pages,
                menu_page_count_unclassified = g.unclassified_pages,
                menu_page_count_pending_files = g.pending_files,
                menu_page_counts_refreshed_at = now()
           from agg g join writable w using (account_id)
          where a.account_id = g.account_id
            and (a.beverage_menu_file_count, a.food_menu_file_count, a.mixed_menu_file_count,
                 a.beverage_menu_page_count, a.food_menu_page_count, a.menu_page_count_total,
                 a.menu_page_count_unclassified, a.menu_page_count_pending_files)
                is distinct from
                (g.beverage_files, g.food_files, g.mixed_files, g.beverage_pages, g.food_pages,
                 g.total_pages, g.unclassified_pages, g.pending_files)
         returning a.account_id)
  select (select max(account_id) from picked), (select count(*) from picked), (select count(*) from updated)
    into v_last, v_picked, v_changed;

  update public.phg_menu_refresh_cursors
     set last_account_id = case when v_picked < c_batch then '' else v_last end,
         cycles_completed = cycles_completed + case when v_picked < c_batch then 1 else 0 end,
         last_cycle_completed_at = case when v_picked < c_batch then now() else last_cycle_completed_at end,
         runs = runs + 1, last_run_at = now(), last_picked = v_picked, last_changed = v_changed,
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
  c_batch    constant int := 1000;
  c_recent   constant int := 300;
  v_started  timestamptz := clock_timestamp();
  v_after    text;
  v_since    timestamptz;
  v_new_since timestamptz;
  v_last     text;
  v_recent   int;
  v_recent_max timestamptz;
  v_recent_ids text[];
  v_sweep_ids text[];
  v_swept    int;
  v_picked   int;
  v_changed  int;
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
  select coalesce(array_agg(account_id order by mx), '{}'::text[]), count(*), max(mx)
    into v_recent_ids, v_recent, v_recent_max
    from (select account_id, max(mx) mx from (
              select account_id, max(updated_at) mx from public.menu_visual_documents
               where updated_at > v_since and account_id is not null group by account_id
              union all
              select account_id, max(updated_at) mx from public.menu_visual_pages
               where updated_at > v_since and account_id is not null group by account_id) s
           group by account_id order by max(mx) limit c_recent) r;
  -- if the recent pass was truncated, resume from the newest change it covered; otherwise
  -- advance to this run's start with a 2-minute overlap for transactions still in flight
  v_new_since := case when v_recent >= c_recent then v_recent_max else v_started - interval '2 minutes' end;

  -- 2. fill the rest of the batch from the cursor sweep (backstop for everything else)
  select coalesce(array_agg(account_id order by account_id), '{}'::text[]), count(*), max(account_id)
    into v_sweep_ids, v_swept, v_last
    from (select account_id from public.accounts
           where account_id > v_after and account_id <> all (v_recent_ids)
           order by account_id limit (c_batch - v_recent)) s;

  with picked as materialized (select distinct unnest(v_recent_ids || v_sweep_ids) as account_id),
       d as materialized (
         select d.account_id, count(*)::int document_count, coalesce(sum(d.page_count),0)::int pages_required,
                count(*) filter (where d.acquisition_status = 'downloaded')::int downloaded_documents,
                count(*) filter (where d.acquisition_status = 'ready' and d.acquisition_method = 'firecrawl_screenshot_fallback')::int screenshot_documents
           from public.menu_visual_documents d join picked x using (account_id) group by d.account_id),
       p as materialized (
         select p.account_id, count(*) filter (where p.render_status = 'ready')::int pages_ready,
                count(*) filter (where p.render_status <> 'ready')::int pages_pending
           from public.menu_visual_pages p join picked x using (account_id) group by p.account_id),
       agg as materialized (
         select x.account_id, coalesce(d.document_count,0) document_count, coalesce(d.pages_required,0) pages_required,
                coalesce(p.pages_ready,0) pages_ready, coalesce(p.pages_pending,0) pages_pending,
                coalesce(d.downloaded_documents,0) downloaded_documents, coalesce(d.screenshot_documents,0) screenshot_documents
           from picked x left join d using (account_id) left join p using (account_id)),
       writable as materialized (
         select a.account_id from public.accounts a join picked x using (account_id)
          order by a.account_id for update of a skip locked),
       updated as (
         update public.accounts a
            set menu_visual_document_count = g.document_count, menu_visual_pages_required = g.pages_required,
                menu_visual_pages_ready = g.pages_ready, menu_visual_pages_pending = g.pages_pending,
                menu_visual_downloaded_document_count = g.downloaded_documents,
                menu_visual_screenshot_document_count = g.screenshot_documents,
                menu_visual_counts_refreshed_at = now()
           from agg g join writable w using (account_id)
          where a.account_id = g.account_id
            and (a.menu_visual_document_count, a.menu_visual_pages_required, a.menu_visual_pages_ready,
                 a.menu_visual_pages_pending, a.menu_visual_downloaded_document_count,
                 a.menu_visual_screenshot_document_count)
                is distinct from
                (g.document_count, g.pages_required, g.pages_ready, g.pages_pending,
                 g.downloaded_documents, g.screenshot_documents)
         returning a.account_id)
  select (select count(*) from picked), (select count(*) from updated) into v_picked, v_changed;

  update public.phg_menu_refresh_cursors
     set last_account_id = case when v_swept < (c_batch - v_recent) then '' else coalesce(v_last, v_after) end,
         cycles_completed = cycles_completed + case when v_swept < (c_batch - v_recent) then 1 else 0 end,
         last_cycle_completed_at = case when v_swept < (c_batch - v_recent) then now() else last_cycle_completed_at end,
         recent_since = v_new_since,
         runs = runs + 1, last_run_at = now(), last_picked = v_picked, last_changed = v_changed,
         last_duration_ms = (extract(epoch from clock_timestamp() - v_started) * 1000)::int,
         updated_at = now()
   where name = 'visual_counts';
end
$function$;
