-- PHG-026: this script was split in review round 3 (it false-failed once cron resumed).
--   supabase/tests/phg_026_release_gate.sql  - run once right after the runbook, before cron 13 / 7 are re-enabled.
--   supabase/tests/phg_026_monitor.sql       - run after cron resumes (first cycles, then daily for a week).
select 'see supabase/tests/phg_026_release_gate.sql and supabase/tests/phg_026_monitor.sql' as moved;
