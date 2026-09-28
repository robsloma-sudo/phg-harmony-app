-- Harmony inbox data access for the phg-harmony-inbox edge function.
-- Approved by Rob 2026-09-28 (Action button setup: "Could not create a key: not a member of that account").
--
-- Why: the phg schema is not exposed through the REST API, so the function's
-- supabase-js calls to phg.harmony_device_keys / phg.harmony_notes / the
-- phg.harmony_is_member RPC were refused with HTTP 406. Every other PHG function
-- reaches phg through SECURITY DEFINER functions in public (e.g. phg_auth_bootstrap);
-- this follows the same pattern. One dispatcher, callable by service_role only.
-- Every operation is scoped to the p_args.user the function authenticated.

create or replace function public.phg_harmony_inbox_db(p_op text, p_args jsonb)
returns jsonb
language plpgsql
volatile
security definer
set search_path = phg, pg_temp
as $$
declare
  v_user uuid := nullif(p_args->>'user', '')::uuid;
  v_row jsonb;
  v_n int;
begin
  if p_op = 'key_lookup' then
    select jsonb_build_object('id', k.id, 'user_id', k.user_id, 'account_id', k.account_id, 'revoked_at', k.revoked_at)
      into v_row from phg.harmony_device_keys k where k.key_hash = p_args->>'hash';
    if v_row is not null and v_row->>'revoked_at' is null then
      update phg.harmony_device_keys set last_used_at = now() where id = (v_row->>'id')::uuid;
    end if;
    return v_row;
  end if;

  if v_user is null then
    raise exception 'user required';
  end if;

  if p_op = 'is_member' then
    return to_jsonb(exists (
      select 1 from phg.account_memberships
      where user_id = v_user and account_id = nullif(p_args->>'account', '')::uuid and status = 'active'));

  elsif p_op = 'key_issue' then
    select count(*) into v_n from phg.harmony_device_keys where user_id = v_user and revoked_at is null;
    if v_n >= 5 then
      return jsonb_build_object('error', 'limit');
    end if;
    insert into phg.harmony_device_keys (user_id, account_id, name, key_hash, key_hint)
    values (v_user, nullif(p_args->>'account', '')::uuid, left(coalesce(p_args->>'name', 'iPhone Shortcut'), 80),
            p_args->>'hash', p_args->>'hint')
    returning jsonb_build_object('id', id, 'name', name, 'key_hint', key_hint, 'created_at', created_at) into v_row;
    return v_row;

  elsif p_op = 'key_list' then
    return coalesce((select jsonb_agg(jsonb_build_object('id', id, 'name', name, 'key_hint', key_hint, 'created_at', created_at,
                                                          'last_used_at', last_used_at, 'revoked_at', revoked_at) order by created_at desc)
                     from phg.harmony_device_keys where user_id = v_user), '[]'::jsonb);

  elsif p_op = 'key_revoke' then
    update phg.harmony_device_keys set revoked_at = now()
      where id = nullif(p_args->>'id', '')::uuid and user_id = v_user and revoked_at is null;
    return jsonb_build_object('ok', true);

  elsif p_op = 'notes_list' then
    return coalesce((select jsonb_agg(to_jsonb(x) order by x.created_at desc) from (
        select id, kind, body, tags, due_at, done, source, created_at
        from phg.harmony_notes
        where user_id = v_user and (not coalesce((p_args->>'open_only')::boolean, false) or done = false)
        order by created_at desc
        limit least(200, greatest(1, coalesce((p_args->>'limit')::int, 50)))) x), '[]'::jsonb);

  elsif p_op = 'note_add' then
    insert into phg.harmony_notes (user_id, account_id, kind, body, tags, due_at, source)
    values (v_user, nullif(p_args->>'account', '')::uuid, coalesce(p_args->>'kind', 'note'), left(p_args->>'body', 4000),
            coalesce(array(select jsonb_array_elements_text(coalesce(p_args->'tags', '[]'::jsonb))), '{}'),
            nullif(p_args->>'due', '')::timestamptz, coalesce(p_args->>'source', 'app'))
    returning jsonb_build_object('id', id, 'kind', kind, 'body', body, 'due_at', due_at, 'created_at', created_at) into v_row;
    return v_row;

  elsif p_op = 'note_done' then
    update phg.harmony_notes set done = coalesce((p_args->>'done')::boolean, true), updated_at = now()
      where id = nullif(p_args->>'id', '')::uuid and user_id = v_user;
    return jsonb_build_object('ok', true);

  elsif p_op = 'note_delete' then
    delete from phg.harmony_notes where id = nullif(p_args->>'id', '')::uuid and user_id = v_user;
    return jsonb_build_object('ok', true);
  end if;

  raise exception 'unknown op %', p_op;
end;
$$;

revoke all on function public.phg_harmony_inbox_db(text, jsonb) from public, anon, authenticated;
grant execute on function public.phg_harmony_inbox_db(text, jsonb) to service_role;
