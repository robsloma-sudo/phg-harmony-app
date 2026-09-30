-- PHG-036d (2): the designer gateway refuses functions with effects that outlive the query (safety review round 2, SF9):
-- advisory locks (a session lock could block cron 7 / 13), set_config (session settings), notifications, sleeps,
-- backend signalling, large objects, dblink / net / cron / vault. Read-only transaction + security-definer ownership
-- already prevent writes and role changes; this closes the remaining session side effects.
create or replace function phg_designer.run(p_sql text, p_limit int)
returns jsonb language plpgsql security definer set search_path to 'public', 'phg', 'pg_temp' as $$
declare v jsonb;
begin
  if p_sql ~* '(pg_advisory|pg_try_advisory|set_config|pg_notify|pg_sleep|pg_terminate|pg_cancel|pg_reload|pg_signal|\mlo_|dblink|\mnet\.|\mcron\.|\mvault\.|pg_read|pg_ls_|pg_stat_file|txid_|pg_logical)' then
    raise exception 'function not allowed in designer queries';
  end if;
  execute format('select coalesce(jsonb_agg(q), ''[]''::jsonb) from (select * from (%s) s limit %s) q', p_sql, p_limit) into v;
  return v;
end $$;
