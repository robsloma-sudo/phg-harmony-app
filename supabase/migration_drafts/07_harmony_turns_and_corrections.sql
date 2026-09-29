-- Harmony learns from corrections. Approved by Rob 2026-09-29 ("yes to the two database changes").
-- Spec: handoff/HARMONY_CONVERSATION_MODEL.md §5 (jobs, question rules), §4C (project and person layers).
--
-- What this does (plain English)
--   * phg.harmony_turns: every conversation turn Harmony handles (what was said, what Harmony understood, what it
--     did, on which surface). Project- and person-scoped. No audio, no secrets; text is capped.
--   * phg.harmony_corrections: whenever someone says "no / that's wrong / I meant ...", the wrong turn, what was
--     wrong (the item, version, place, source, intent ...) and what was right.
--   * phg.harmony_aliases: the immediate fix - per project, a heard term mapped to what it really means
--     ("easton co" -> venue "East & Co"; "a lot of manhattans" -> the Manhattan variations list). Harmony reads these
--     before matching, so the same mistake is not repeated.
--   * Access only through public.phg_harmony_inbox_db (service_role only), extended with ops turn_log,
--     correction_add, aliases_list, alias_upsert, turns_recent. Every existing op is unchanged.
--
-- Rollback
--   -- re-run supabase/migrations/20260928234500_harmony_inbox_house_recipes.sql (restores the previous dispatcher)
--   -- drop table if exists phg.harmony_aliases, phg.harmony_corrections, phg.harmony_turns;

begin;

create table if not exists phg.harmony_turns (
  id           bigint generated always as identity primary key,
  account_id   uuid references phg.accounts(id) on delete cascade,
  user_id      uuid not null,
  surface      text not null default 'app' check (surface in ('app','shortcut','other')),
  user_text    text not null,
  action       text,                                   -- clarify | recipe | data | note | read_back | answer | end ...
  understood   jsonb not null default '{}'::jsonb,     -- planner output (slots), no secrets
  reply_text   text,
  is_correction boolean not null default false,        -- the user was correcting the previous turn
  created_at   timestamptz not null default now()
);
create index if not exists harmony_turns_acct_at on phg.harmony_turns (account_id, created_at desc);
create index if not exists harmony_turns_user_at on phg.harmony_turns (user_id, created_at desc);

create table if not exists phg.harmony_corrections (
  id            bigint generated always as identity primary key,
  account_id    uuid references phg.accounts(id) on delete cascade,
  user_id       uuid not null,
  wrong_turn_id bigint references phg.harmony_turns(id) on delete set null,
  fix_turn_id   bigint references phg.harmony_turns(id) on delete set null,
  heard         text,                                  -- what Harmony got wrong ("Easton Co", "Black Manhattan")
  wrong_part    text check (wrong_part in ('item','version','place','source','intent','amount','time','other')),
  meant         text,                                  -- what was right ("East & Co", "the Manhattan variations")
  resolved      boolean not null default false,        -- Harmony then got it right
  reviewed      boolean not null default false,        -- seen in the nightly review
  created_at    timestamptz not null default now()
);
create index if not exists harmony_corrections_acct_at on phg.harmony_corrections (account_id, created_at desc);

create table if not exists phg.harmony_aliases (
  id          bigint generated always as identity primary key,
  account_id  uuid references phg.accounts(id) on delete cascade,   -- null = shared across projects (admin only)
  heard       text not null,                                        -- normalised lower-case phrase
  kind        text not null default 'term' check (kind in ('venue','cocktail','brand','ingredient','place','term','intent')),
  means       text not null,                                        -- canonical value / name
  ref_id      text,                                                 -- optional id of the thing
  uses        int not null default 1,
  source      text not null default 'correction' check (source in ('correction','confirmed','admin')),
  created_by  uuid,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create unique index if not exists harmony_aliases_uniq on phg.harmony_aliases (coalesce(account_id,'00000000-0000-0000-0000-000000000000'::uuid), heard, kind);

alter table phg.harmony_turns       enable row level security;
alter table phg.harmony_corrections enable row level security;
alter table phg.harmony_aliases     enable row level security;
revoke all on phg.harmony_turns, phg.harmony_corrections, phg.harmony_aliases from public, anon, authenticated;

create or replace function public.phg_harmony_inbox_db(p_op text, p_args jsonb)
returns jsonb
language plpgsql
volatile
security definer
set search_path = phg, pg_temp
as $$
declare
  v_user uuid := nullif(p_args->>'user', '')::uuid;
  v_acct uuid := nullif(p_args->>'account', '')::uuid;
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

  elsif p_op = 'house_recipes' then
    -- read-only: house menu items + current recipe for one account the user belongs to;
    -- q filters by item/recipe name (empty = all cocktails on the house menu)
    if not exists (select 1 from phg.account_memberships
                   where user_id = v_user and account_id = nullif(p_args->>'account', '')::uuid and status = 'active') then
      return '[]'::jsonb;
    end if;
    return coalesce((select jsonb_agg(to_jsonb(x) order by x.name) from (
        select mi.name, mi.item_type, mi.menu_price, mi.menu_description, mi.section_name,
               rv.recipe_name, rv.method, rv.glassware, rv.garnish, rv.ingredients, rv.build_family
        from phg.menu_items mi
        join phg.menu_projects mp on mp.id = mi.menu_project_id
        left join phg.recipe_versions rv on rv.id = mi.current_recipe_version_id
        where mp.account_id = nullif(p_args->>'account', '')::uuid
          and (coalesce(p_args->>'q', '') = ''
               or mi.name ilike '%' || (p_args->>'q') || '%'
               or rv.recipe_name ilike '%' || (p_args->>'q') || '%')
        order by mi.name
        limit 25) x), '[]'::jsonb);

  /* ---- 2026-09-29: turns, corrections, aliases. Account-scoped rows require active membership;
          account null = the user's own rows with no project. ---- */
  elsif p_op in ('turn_log', 'correction_add', 'aliases_list', 'alias_upsert', 'turns_recent') then
    if v_acct is not null and not exists (select 1 from phg.account_memberships
                   where user_id = v_user and account_id = v_acct and status = 'active') then
      return jsonb_build_object('error', 'not a member');
    end if;

    if p_op = 'turn_log' then
      insert into phg.harmony_turns (account_id, user_id, surface, user_text, action, understood, reply_text, is_correction)
      values (v_acct, v_user,
              case when p_args->>'surface' in ('app','shortcut') then p_args->>'surface' else 'other' end,
              left(coalesce(p_args->>'text', ''), 1000), left(p_args->>'action', 40),
              coalesce(p_args->'understood', '{}'::jsonb), left(p_args->>'reply', 1500),
              coalesce((p_args->>'is_correction')::boolean, false))
      returning jsonb_build_object('id', id) into v_row;
      return v_row;

    elsif p_op = 'correction_add' then
      insert into phg.harmony_corrections (account_id, user_id, wrong_turn_id, fix_turn_id, heard, wrong_part, meant)
      values (v_acct, v_user,
              (select id from phg.harmony_turns where id = nullif(p_args->>'wrong_turn', '')::bigint and user_id = v_user),
              (select id from phg.harmony_turns where id = nullif(p_args->>'fix_turn', '')::bigint and user_id = v_user),
              left(p_args->>'heard', 300),
              case when p_args->>'wrong_part' in ('item','version','place','source','intent','amount','time') then p_args->>'wrong_part' else 'other' end,
              left(p_args->>'meant', 300))
      returning jsonb_build_object('id', id) into v_row;
      return v_row;

    elsif p_op = 'aliases_list' then
      return coalesce((select jsonb_agg(jsonb_build_object('heard', heard, 'kind', kind, 'means', means, 'ref_id', ref_id) order by uses desc)
        from (select * from phg.harmony_aliases
              where (account_id = v_acct or account_id is null)
              order by uses desc limit 200) a), '[]'::jsonb);

    elsif p_op = 'alias_upsert' then
      if v_acct is null then return jsonb_build_object('error', 'project required'); end if;
      insert into phg.harmony_aliases (account_id, heard, kind, means, ref_id, source, created_by)
      values (v_acct, lower(left(trim(p_args->>'heard'), 120)),
              case when p_args->>'kind' in ('venue','cocktail','brand','ingredient','place','term','intent') then p_args->>'kind' else 'term' end,
              left(trim(p_args->>'means'), 200), left(p_args->>'ref_id', 100),
              case when p_args->>'source' in ('correction','confirmed') then p_args->>'source' else 'correction' end, v_user)
      on conflict (coalesce(account_id,'00000000-0000-0000-0000-000000000000'::uuid), heard, kind)
      do update set means = excluded.means, ref_id = excluded.ref_id, uses = phg.harmony_aliases.uses + 1, updated_at = now()
      returning jsonb_build_object('id', id, 'uses', uses) into v_row;
      return v_row;

    elsif p_op = 'turns_recent' then
      return coalesce((select jsonb_agg(to_jsonb(t) order by t.created_at desc) from (
          select id, surface, user_text, action, reply_text, is_correction, created_at
          from phg.harmony_turns
          where user_id = v_user and (account_id is not distinct from v_acct)
          order by created_at desc limit least(50, greatest(1, coalesce((p_args->>'limit')::int, 10)))) t), '[]'::jsonb);
    end if;
  end if;

  raise exception 'unknown op %', p_op;
end;
$$;

revoke all on function public.phg_harmony_inbox_db(text, jsonb) from public, anon, authenticated;
grant execute on function public.phg_harmony_inbox_db(text, jsonb) to service_role;

commit;
