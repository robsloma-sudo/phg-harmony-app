-- PHG-036d (3): close the dynamic-SQL bypass of the designer denylist (PHG-026 spec review round 3, C17):
-- query_to_xml('select pg_'||'advisory_lock(1)') or ts_stat / ts_rewrite / *_to_xml run query text built at run
-- time, and U&"..." identifiers can spell a blocked name. Refuse those functions and U& quoting, and after every call
-- release any session advisory locks the call might have taken (pg_advisory_unlock_all), on success and on error.
create or replace function phg_designer.run(p_sql text, p_limit int)
returns jsonb language plpgsql security definer set search_path to 'public', 'phg', 'pg_temp' as $$
declare v jsonb;
begin
  if p_sql ~* '(pg_advisory|pg_try_advisory|set_config|pg_notify|pg_sleep|pg_terminate|pg_cancel|pg_reload|pg_signal|\mlo_|dblink|\mnet\.|\mcron\.|\mvault\.|pg_read|pg_ls_|pg_stat_file|txid_|pg_logical|_to_xml|to_xmlschema|ts_stat|ts_rewrite|\mxmltable|\mu&|\muescape)' then
    raise exception 'function not allowed in designer queries';
  end if;
  execute format('select coalesce(jsonb_agg(q), ''[]''::jsonb) from (select * from (%s) s limit %s) q', p_sql, p_limit) into v;
  return v;
end $$;

create or replace function public.phg_designer_query(p_sql text, p_max_rows int default 500, p_task_id uuid default null)
returns jsonb language plpgsql set search_path to 'public', 'phg', 'pg_temp' as $$
declare v_rows jsonb; v_t0 timestamptz := clock_timestamp(); v_log bigint;
begin
  if p_sql is null or btrim(p_sql) = '' then raise exception 'sql required'; end if;
  if p_sql ~ ';\s*\S' then raise exception 'one statement only'; end if;
  insert into phg.menu_designer_query_log (task_id, sql) values (p_task_id, left(p_sql, 20000)) returning id into v_log;
  -- note: read-only and the 20 s timeout stay on for the rest of the caller's transaction (call it on its own)
  set local statement_timeout = '20s';
  set local transaction_read_only = on;
  begin
    v_rows := phg_designer.run(regexp_replace(p_sql, ';\s*$', ''), least(greatest(coalesce(p_max_rows, 500), 1), 5000));
  exception when others then
    perform pg_advisory_unlock_all();
    raise exception 'designer query failed: %', sqlerrm;
  end;
  perform pg_advisory_unlock_all();
  return jsonb_build_object('rows', v_rows, 'row_count', jsonb_array_length(v_rows), 'log_id', v_log,
                            'ms', (extract(epoch from clock_timestamp() - v_t0) * 1000)::int);
end $$;
revoke all on function public.phg_designer_query(text, int, uuid) from public, anon, authenticated;
