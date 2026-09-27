-- PHG cron changes applied 2026-09-27 (~15:40Z) by the backend agent, with Rob's approval
-- ("fix all of these, except five"). pg_cron job definitions are not in migrations, so
-- they are recorded here. Each block lists the previous value for rollback.

-- Covering index so refresh_state_stats (job 5) and refresh_public_batches_cache (job 23)
-- read ~8 MB of index instead of the ~184 MB bloated accounts heap.
-- Measured: job-5 account_map scan 778 ms -> 110 ms; job-23 aggregate 2,050 ms -> 94 ms.
-- Built CONCURRENTLY (no reader/writer blocking). Rollback:
--   DROP INDEX CONCURRENTLY IF EXISTS public.phg_accounts_state_stats_cover_idx;
CREATE INDEX CONCURRENTLY IF NOT EXISTS phg_accounts_state_stats_cover_idx
  ON public.accounts USING btree (account_id)
  INCLUDE (account_status, account_types, places_looked_up_at, website_url, menu_status);

-- Job 5 gtt-refresh-state-stats: 5 s limit -> 20 s headroom (runs were 1-4 s against 5 s).
-- Previous: command SET statement_timeout='5s'; SET lock_timeout='500ms'; SELECT public.refresh_state_stats_live();
SELECT cron.alter_job(job_id := 5, schedule := '2-57/5 * * * *',
  command := $cmd$SET statement_timeout='20s'; SET lock_timeout='500ms'; SELECT public.refresh_state_stats_live();$cmd$);

-- Job 23 gtt-refresh-public-batches-cache: re-enabled (was inactive since the Sep-26 pause;
-- v_public_batches was serving 00:20Z data). Every 10 min, offset from other jobs.
-- Previous: schedule '*/10 * * * *', command 'select phg_internal.refresh_public_batches_cache()', active false.
SELECT cron.alter_job(job_id := 23, schedule := '4-54/10 * * * *',
  command := $cmd$SET statement_timeout='15s'; SET lock_timeout='500ms'; SELECT phg_internal.refresh_public_batches_cache();$cmd$,
  active := true);

-- Job 13 gtt-extract-menu-candidates: 5 s -> 10 s (2 timeouts in the read-only priority SELECT).
-- Previous: SET statement_timeout='5s'; SET lock_timeout='500ms'; SELECT public.phg_dispatch_menu_recovery_work('candidate_extraction');
SELECT cron.alter_job(job_id := 13,
  command := $cmd$SET statement_timeout='10s'; SET lock_timeout='500ms'; SELECT public.phg_dispatch_menu_recovery_work('candidate_extraction');$cmd$);

-- ~15:44Z, with migration phg_count_refresh_faster_cycle (aggregate without row locks; only
-- differing rows locked FOR NO KEY UPDATE for the final UPDATE), longer limits no longer
-- lengthen row-lock holds. Previous for both: statement_timeout '5s'.
SELECT cron.alter_job(job_id := 15,
  command := $cmd$SET statement_timeout='20s'; SET lock_timeout='500ms'; SELECT public.refresh_menu_page_counts();$cmd$);
SELECT cron.alter_job(job_id := 18,
  command := $cmd$SET statement_timeout='15s'; SET lock_timeout='500ms'; SELECT public.refresh_menu_visual_counts(); SELECT public.phg_reconcile_completed_image_documents(100);$cmd$);

-- ~15:57Z: pause promotion (7) and extraction (13) while the duplicate order-item menu fix
-- (PHG-026) is built. Resume 13 first, then 7, after the fix is applied and verified.
-- Previous: both active=true, schedule '20 seconds'.
SELECT cron.alter_job(job_id := 7,  active := false);
SELECT cron.alter_job(job_id := 13, active := false);

-- ~16:06Z: job 22 (full reconciliation of phg_menu_pipeline_live_stats_cache; delta triggers keep
-- it current between runs) was hitting its 5 s limit (2 of 6 runs failed) as candidates grow.
-- Previous: schedule '*/5 * * * *', statement_timeout '5s'.
SELECT cron.alter_job(job_id := 22, schedule := '9,39 * * * *',
  command := $cmd$SET statement_timeout='30s'; SET lock_timeout='500ms'; SELECT public.refresh_phg_menu_pipeline_live_stats_cache();$cmd$);
