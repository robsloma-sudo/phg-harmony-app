-- PHG-036d: close the role escape in phg_designer_query (found by the PHG-026 round-2 spec review, confirmed live
-- 2026-09-28: a query could call set_config('role','postgres',true) and read as postgres via query_to_xml).
-- Fix: the designer's SQL now executes inside a SECURITY DEFINER function OWNED BY phg_menu_designer. Postgres refuses
-- any change of "role" inside a security-definer function (also through set_config / nested query_to_xml), so the
-- query can only ever run with the designer role's privileges. The outer gateway keeps the checks, the read-only
-- transaction, the timeout and the log.
-- Also brings the live grants into the file (membership for the caller; per-table read policies are created by the
-- loop below for every allowlisted table that has row level security).

grant phg_menu_designer to postgres;   -- lets postgres assign ownership below (already live)

create schema if not exists phg_designer;
revoke all on schema phg_designer from public;
grant usage on schema phg_designer to phg_menu_designer, postgres;

create or replace function phg_designer.run(p_sql text, p_limit int)
returns jsonb language plpgsql security definer set search_path to 'public', 'phg', 'pg_temp' as $$
declare v jsonb;
begin
  execute format('select coalesce(jsonb_agg(q), ''[]''::jsonb) from (select * from (%s) s limit %s) q', p_sql, p_limit) into v;
  return v;
end $$;

-- ownership needs CREATE on the schema for the new owner; grant it only for the ALTER, then take it back
grant create on schema phg_designer to phg_menu_designer;
alter function phg_designer.run(text, int) owner to phg_menu_designer;
revoke create on schema phg_designer from phg_menu_designer;
revoke all on function phg_designer.run(text, int) from public, anon, authenticated;
grant execute on function phg_designer.run(text, int) to postgres;

-- read policies for RLS tables on the allowlist (idempotent; mirrors what was applied live)
do $$
declare r record;
begin
  for r in
    select n.nspname s, c.relname t from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where c.relkind in ('r','p') and c.relrowsecurity and n.nspname in ('public','phg')
       and has_table_privilege('phg_menu_designer', c.oid, 'select')
       and not exists (select 1 from pg_policy p where p.polrelid = c.oid and p.polname = 'menu_designer_read')
  loop
    execute format('create policy menu_designer_read on %I.%I for select to phg_menu_designer using (true)', r.s, r.t);
  end loop;
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
    raise exception 'designer query failed: %', sqlerrm;
  end;
  return jsonb_build_object('rows', v_rows, 'row_count', jsonb_array_length(v_rows), 'log_id', v_log,
                            'ms', (extract(epoch from clock_timestamp() - v_t0) * 1000)::int);
end $$;
revoke all on function public.phg_designer_query(text, int, uuid) from public, anon, authenticated;
