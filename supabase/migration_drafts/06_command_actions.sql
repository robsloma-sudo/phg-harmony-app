-- DRAFT — NOT APPLIED. Needs Rob's approval. Spec: handoff/HARMONY_CONVERSATION_MODEL.md §7.3, §7.2, §4B.2-4B.3, §10
-- Revised 2026-09-29 (Rob: no folders): the folder actions (create_folder, rename_folder, move_link, link_to_folder, unlink)
-- are replaced by save_filter, save_view, update_view, delete_view. Nothing is "filed" any more; built things live in their
-- normal tables and people find them with saved views/filters (draft 03).
--
-- What this does (plain English)
--   Adds new Command Center write actions. Writes still happen ONLY after a proposal is approved with its one-time token
--   (existing flow: phg_command_propose_action -> phg_command_execute_approved_action).
--
--   Approach: the live public.phg_command_execute_approved_action is ~10 KB and handles 9 existing actions plus workflow
--   step bookkeeping. Rewriting it is risky, so this draft:
--     (a) adds a SEPARATE internal dispatcher, phg.harmony_execute_command_action(...), holding all new actions; and
--     (b) replaces phg_command_execute_approved_action with the LIVE definition copied verbatim (pg_get_functiondef,
--         2026-09-28) plus ONE new `elsif` branch that forwards the new keys to the dispatcher. Nothing else changes:
--         authorization (phg_menu_authorize), proposal lookup/locking, token check, the 9 existing branches, the
--         'executed' update and the workflow-step bookkeeping are byte-for-byte the live code.
--   BEFORE APPLYING: re-run pg_get_functiondef on the live function and diff it against section 3 below. If the live
--   function changed since 2026-09-28, re-copy it and re-insert the single marked branch.
--   Checked: section 3 with the marked branch removed (and the final ';' dropped) is byte-identical to the live definition:
--   md5 bc1b0d154a7a756c4ad1dfd0f3966648, 10,083 bytes =
--   select md5(pg_get_functiondef('public.phg_command_execute_approved_action(uuid,text,uuid,text)'::regprocedure));
--
-- Added action keys
--   From §7.3 (minus folders):  create_record, create_ingredient, create_prep_recipe, create_recipe_version,
--                               update_recipe_draft, attach_recipe_to_menu_item, set_account_setting
--   Views/filters (Rob 09-29):  save_filter, save_view, update_view, delete_view
--   BEYOND THE BRIEF (remove if unwanted): save_party, save_invoice_coding_rule — without them nothing can write the new
--                               phg.parties / phg.invoice_coding_rules tables that the setup walkthrough is meant to fill.
-- Also added
--   * phg.harmony_command_actions: registry of the new keys with risk class and whether a spoken "yes" is enough (§10).
--   * phg.harmony_session_user(): finds the approving person (user + role) from the sync token when it is a user session
--     token. Menu-studio editor tokens carry no user: those callers may build recipes/ingredients/records but NOT change
--     settings, views, filters or parties (needs_user).
--   * helpers: phg.harmony_create_ingredient, phg.harmony_new_ingredients, phg.harmony_check_ingredient,
--     phg.harmony_recipe_visible, phg.harmony_recipe_version_visible.
-- Existing action keys and behaviour unchanged: set_menu_price, set_financial_rule, set_purchase_cost, save_reporting_period,
--   set_menu_item_recipe, persist_recipe_candidate, create_menu_item, persist_training_package, approve_training_package.
--
-- Depends on: 02 (setting_definitions, account_settings, parties, invoice_coding_rules, workspace_records),
--   03 (saved_filters, saved_views, period_presets), 04 (account_id on recipe_projects, recipe_versions, ingredients,
--   prep_recipes; gl_accounts for code validation).
--
-- Payloads (proposal.payload; proposal.target_id used where noted)
--   create_record              {record_type, title, fields?, files?}
--   create_ingredient          {name, ingredient_type?, category?, default_unit?, aliases?, abv?, density_g_per_ml?, force_new?}
--   create_prep_recipe         {name, prep_type?, description?, batch_yield, batch_yield_unit, method?, new_ingredients?,
--                               components:[{ingredient_id|ingredient_ref|nested_prep_recipe_id, quantity, unit, yield_pct?, role?, notes?}]}
--   create_recipe_version      {recipe_project_id? | project_name?, cocktail_name?, recipe_name?, concept?, build_family?, method?,
--                               glassware?, garnish?, targets?, status (draft|candidate)?, new_ingredients?,
--                               components:[{ingredient_id|ingredient_ref|prep_recipe_id, quantity, unit, role?, optional?, notes?}]}
--   update_recipe_draft        target_id|recipe_version_id, {fields:{method, glassware, garnish, ...}, components?, new_ingredients?}
--   attach_recipe_to_menu_item {menu_item_id (or target_id), recipe_version_id}
--   set_account_setting        {key, value, scope_key?, source?, confidence?, evidence?}   (role must be in edit_roles)
--   save_filter                {filter_id? (replace own/shared), name, entity, conditions:[{field, op, value}], shared?, source?}
--   save_view                  {name, entity? | metric_keys?, filter_ids?, extra_conditions?, period_preset_key?, group_by?,
--                               columns?, sort?, display?, pinned?, shared?, source?}
--   update_view                target_id|view_id, any save_view field except shared (changing who sees it = save a new view)
--   delete_view                target_id|view_id  (archive: sets archived_at; undo = update_view {restore:true})
--   save_party                 {party_id?, name, kinds?, aliases?, contact_name?, email?, phone?, address?, website?,
--                               account_number?, delivery_days?, order_cutoff?, payment_terms?, gl_default_code?, notes?}
--   save_invoice_coding_rule   {rule_id?, party_id? | party_pattern?, line_pattern?, match_kind?, gl_code, priority?, confidence?}
--   new_ingredients            [{ref:'n1', name, ...create_ingredient fields}] — created in the same approval (§7.2 step 7)
--   Shared filters/views (shared = true) need role owner|admin|editor; personal ones any active member.
--
-- Rollback
--   -- 1. restore the live phg_command_execute_approved_action: re-run section 3 WITHOUT the marked HARMONY branch
--   --    (or the definition saved from pg_get_functiondef before applying)
--   -- 2. drop function if exists phg.harmony_execute_command_action(uuid, text, uuid, text, text, jsonb);
--   -- 3. drop function if exists phg.harmony_session_user(uuid, text); drop function if exists phg.harmony_create_ingredient(uuid, uuid, jsonb);
--   --    drop function if exists phg.harmony_new_ingredients(uuid, uuid, jsonb); drop function if exists phg.harmony_check_ingredient(uuid, uuid);
--   --    drop function if exists phg.harmony_recipe_visible(uuid, uuid); drop function if exists phg.harmony_recipe_version_visible(uuid, uuid);
--   -- 4. drop table if exists phg.harmony_command_actions;

begin;

-- ---------------------------------------------------------------------------------------------------------------
-- 1. Registry of the new actions (for the app/brain: which need the on-screen Approve button)
-- ---------------------------------------------------------------------------------------------------------------
create table if not exists phg.harmony_command_actions (
  action_key         text primary key,
  label              text not null,
  risk_class         text not null default 'write' check (risk_class in ('write','close','approve','publish')),
  voice_approval_ok  boolean not null default true,      -- §10: spoken yes enough for low-risk writes
  needs_user         boolean not null default false,     -- true = editor tokens (no person) cannot run it
  description        text
);
alter table phg.harmony_command_actions enable row level security;
revoke all on phg.harmony_command_actions from public, anon, authenticated;
grant select on phg.harmony_command_actions to service_role;

insert into phg.harmony_command_actions (action_key, label, voice_approval_ok, needs_user, description) values
  ('create_record','Create record',true,false,'Free-form record (supplier card ...)'),
  ('create_ingredient','Create ingredient',true,false,null),
  ('create_prep_recipe','Create prep recipe',true,false,'Prep + new ingredients in one approval'),
  ('create_recipe_version','Create recipe version',true,false,'Recipe (or new version) + components + new ingredients'),
  ('update_recipe_draft','Update recipe draft',true,false,'Only draft/candidate versions'),
  ('attach_recipe_to_menu_item','Attach recipe to menu item',false,false,'Changes what a live menu item is costed/trained on: on-screen approve'),
  ('set_account_setting','Change a business setting',true,true,'Role must be in setting_definitions.edit_roles. Targets: Rob to decide on-screen vs voice'),
  ('save_filter','Save filter',true,true,'Personal, or shared in the project (owner/admin/editor)'),
  ('save_view','Save view',true,true,'Personal, or shared in the project (owner/admin/editor)'),
  ('update_view','Update view',true,true,null),
  ('delete_view','Remove view',true,true,'Archive-first; can be restored'),
  ('save_party','Save supplier / party',true,true,'Setup walkthrough; never stores logins'),
  ('save_invoice_coding_rule','Save invoice coding rule',false,true,'Decides which GL account spend lands in: on-screen approve')
on conflict (action_key) do nothing;

-- ---------------------------------------------------------------------------------------------------------------
-- 2. Helpers and the dispatcher (internal: callable only from phg_command_execute_approved_action, both owned by postgres)
-- ---------------------------------------------------------------------------------------------------------------
create or replace function phg.harmony_session_user(p_menu_project_id uuid, p_sync_token text)
returns table (user_id uuid, role text)
language sql stable security definer set search_path = '' as $$
  select s.user_id, m.role
    from phg.menu_projects p
    join phg.user_sessions s on s.account_id = p.account_id
    join phg.account_memberships m on m.id = s.membership_id and m.account_id = s.account_id and m.user_id = s.user_id
   where p.id = p_menu_project_id and p_sync_token is not null
     and encode(extensions.digest(p_sync_token, 'sha256'), 'hex') = s.token_hash
     and s.revoked_at is null and s.expires_at > now() and m.status = 'active'
   limit 1
$$;

-- recipe ownership: the project's own (04 account_id) or, until 04 is backfilled, reachable from this account's menus
create or replace function phg.harmony_recipe_visible(p_account uuid, p_project uuid)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from phg.recipe_projects r where r.id = p_project and (r.account_id = p_account
           or (r.account_id is null and exists (select 1 from phg.menu_items mi join phg.menu_projects mp on mp.id = mi.menu_project_id
                                                 where mi.recipe_project_id = r.id and mp.account_id = p_account))))
$$;
create or replace function phg.harmony_recipe_version_visible(p_account uuid, p_version uuid)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from phg.recipe_versions v where v.id = p_version
                    and (v.account_id = p_account or phg.harmony_recipe_visible(p_account, v.project_id)))
$$;

-- is this ingredient usable in this project? (shared library or the project's own)
create or replace function phg.harmony_check_ingredient(p_account uuid, p_ingredient uuid)
returns void language plpgsql stable security definer set search_path = '' as $$
begin
  if not exists (select 1 from phg.ingredients i where i.id = p_ingredient and (i.account_id is null or i.account_id = p_account)) then
    raise exception 'ingredient % not found in this project', p_ingredient;
  end if;
end $$;

create or replace function phg.harmony_create_ingredient(p_account uuid, p_user uuid, p jsonb)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare v_name text := btrim(coalesce(p->>'name', '')); v_id uuid; v_key text; v_slug text;
begin
  if v_name = '' then raise exception 'ingredient name required'; end if;
  -- reuse an existing match (name or alias) unless the proposal explicitly said it is a new, different ingredient
  if not coalesce((p->>'force_new')::boolean, false) then
    select i.id into v_id from phg.ingredients i
     where (i.account_id is null or i.account_id = p_account)
       and (lower(i.name) = lower(v_name) or exists (select 1 from unnest(i.aliases) a where lower(a) = lower(v_name)))
     order by (i.account_id = p_account) desc nulls last limit 1;
    if v_id is not null then return jsonb_build_object('ingredient_id', v_id, 'created', false, 'name', v_name); end if;
  end if;
  v_slug := trim(both '_' from regexp_replace(lower(v_name), '[^a-z0-9]+', '_', 'g'));
  v_key := 'a' || left(replace(p_account::text, '-', ''), 8) || '_' || left(v_slug, 60);
  if exists (select 1 from phg.ingredients where ingredient_key = v_key) then
    v_key := v_key || '_' || left(replace(gen_random_uuid()::text, '-', ''), 6);
  end if;
  insert into phg.ingredients (ingredient_key, name, ingredient_type, category, default_unit, density_g_per_ml, alcohol_abv_pct,
                               aliases, verification_status, account_id, metadata)
  values (v_key, v_name, coalesce(nullif(p->>'ingredient_type', ''), 'other'), nullif(p->>'category', ''), nullif(p->>'default_unit', ''),
          nullif(p->>'density_g_per_ml', '')::numeric, nullif(p->>'abv', '')::numeric,
          coalesce(array(select jsonb_array_elements_text(coalesce(p->'aliases', '[]'::jsonb))), '{}'),
          'user_confirmed', p_account,
          jsonb_build_object('created_by', 'harmony_command_center', 'user_id', p_user))
  returning id into v_id;
  return jsonb_build_object('ingredient_id', v_id, 'created', true, 'name', v_name, 'ingredient_key', v_key);
end $$;

-- create the proposal's new_ingredients; returns {"refs":{"n1":"<uuid>"}, "created":[...]}
create or replace function phg.harmony_new_ingredients(p_account uuid, p_user uuid, p_list jsonb)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare c jsonb; r jsonb; v_refs jsonb := '{}'::jsonb; v_out jsonb := '[]'::jsonb;
begin
  for c in select value from jsonb_array_elements(coalesce(p_list, '[]'::jsonb)) loop
    r := phg.harmony_create_ingredient(p_account, p_user, c);
    if nullif(c->>'ref', '') is not null then v_refs := v_refs || jsonb_build_object(c->>'ref', r->>'ingredient_id'); end if;
    v_out := v_out || r;
  end loop;
  return jsonb_build_object('refs', v_refs, 'created', v_out);
end $$;

create or replace function phg.harmony_execute_command_action(p_menu_project_id uuid, p_sync_token text, p_proposal_id uuid,
                                                              p_action_key text, p_target_id text, p jsonb)
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
  v_account uuid; v_user uuid; v_role text; v_owner uuid;
  v_id uuid; v_id2 uuid; v_row jsonb; v_prev jsonb; v_new jsonb; v_refs jsonb := '{}'::jsonb;
  v_ver int; v_parent uuid; v_def phg.setting_definitions; c jsonb; v_ing uuid; v_ord int := 0; v_cost jsonb;
  v_shared boolean;
begin
  select account_id into v_account from phg.menu_projects where id = p_menu_project_id;
  if v_account is null then raise exception 'menu project has no account; cannot run Harmony actions'; end if;
  select su.user_id, su.role into v_user, v_role from phg.harmony_session_user(p_menu_project_id, p_sync_token) su;

  if exists (select 1 from phg.harmony_command_actions where action_key = p_action_key and needs_user) and v_user is null then
    raise exception '% needs a signed-in person, not a menu editor token', p_action_key;
  end if;

  -- ---------------------------------------------------------------- free-form records
  if p_action_key = 'create_record' then
    insert into phg.workspace_records (account_id, record_type, title, fields, files, created_by)
    values (v_account, coalesce(nullif(p->>'record_type', ''), 'note'), coalesce(nullif(p->>'title', ''), 'Untitled'),
            coalesce(p->'fields', '{}'::jsonb), coalesce(p->'files', '[]'::jsonb), v_user)
    returning id into v_id;
    return jsonb_build_object('record_id', v_id);

  -- ---------------------------------------------------------------- ingredients, preps, recipes
  elsif p_action_key = 'create_ingredient' then
    return phg.harmony_create_ingredient(v_account, v_user, p);

  elsif p_action_key = 'create_prep_recipe' then
    if nullif(p->>'batch_yield', '') is null or nullif(p->>'batch_yield_unit', '') is null then
      raise exception 'batch yield and unit required ("What does the batch make, roughly?")';
    end if;
    v_new := phg.harmony_new_ingredients(v_account, v_user, p->'new_ingredients');
    v_refs := v_new->'refs';
    insert into phg.prep_recipes (prep_key, name, description, prep_type, account_id)
    values ('a' || left(replace(v_account::text, '-', ''), 8) || '_' || left(replace(gen_random_uuid()::text, '-', ''), 12),
            coalesce(nullif(btrim(p->>'name'), ''), 'Untitled prep'), nullif(p->>'description', ''),
            coalesce(nullif(p->>'prep_type', ''), 'other'), v_account)
    returning id into v_id;
    insert into phg.prep_recipe_versions (prep_recipe_id, version, batch_yield, batch_yield_unit, method, status)
    values (v_id, 1, (p->>'batch_yield')::numeric, p->>'batch_yield_unit', nullif(p->>'method', ''), 'draft')
    returning id into v_id2;
    for c in select value from jsonb_array_elements(coalesce(p->'components', '[]'::jsonb)) loop
      v_ord := v_ord + 1;
      v_ing := coalesce(nullif(c->>'ingredient_id', '')::uuid, nullif(v_refs->>(c->>'ingredient_ref'), '')::uuid);
      if v_ing is not null then
        perform phg.harmony_check_ingredient(v_account, v_ing);
      elsif nullif(c->>'nested_prep_recipe_id', '') is not null then
        if not exists (select 1 from phg.prep_recipes x where x.id = (c->>'nested_prep_recipe_id')::uuid and (x.account_id is null or x.account_id = v_account)) then
          raise exception 'nested prep not found in this project';
        end if;
      else
        raise exception 'component % has no ingredient or nested prep', v_ord;
      end if;
      insert into phg.prep_components (prep_version_id, ingredient_id, nested_prep_recipe_id, quantity, unit, yield_pct, role, notes, sort_order)
      values (v_id2, v_ing, case when v_ing is null then (c->>'nested_prep_recipe_id')::uuid end, (c->>'quantity')::numeric, c->>'unit',
              coalesce(nullif(c->>'yield_pct', '')::numeric, 100), nullif(c->>'role', ''), nullif(c->>'notes', ''), v_ord);
    end loop;
    return jsonb_build_object('prep_recipe_id', v_id, 'prep_version_id', v_id2, 'component_count', v_ord,
                              'new_ingredients', v_new->'created', 'cost', 'pending');

  elsif p_action_key = 'create_recipe_version' then
    v_new := phg.harmony_new_ingredients(v_account, v_user, p->'new_ingredients');
    v_refs := v_new->'refs';
    v_id := nullif(p->>'recipe_project_id', '')::uuid;
    if v_id is null then
      insert into phg.recipe_projects (name, brief, account_id)
      values (coalesce(nullif(p->>'project_name', ''), nullif(p->>'cocktail_name', ''), nullif(p->>'recipe_name', ''), 'Untitled recipe'),
              jsonb_build_object('source', 'harmony_voice_build', 'proposal_id', p_proposal_id), v_account)
      returning id into v_id;
    elsif not phg.harmony_recipe_visible(v_account, v_id) then
      raise exception 'recipe not found in this project';
    end if;
    select id, version into v_parent, v_ver from phg.recipe_versions where project_id = v_id order by version desc limit 1;
    -- resolve components first so the jsonb snapshot and the rows agree
    v_row := '[]'::jsonb;
    for c in select value from jsonb_array_elements(coalesce(p->'components', '[]'::jsonb)) loop
      v_ing := coalesce(nullif(c->>'ingredient_id', '')::uuid, nullif(v_refs->>(c->>'ingredient_ref'), '')::uuid);
      if v_ing is not null then perform phg.harmony_check_ingredient(v_account, v_ing);
      elsif nullif(c->>'prep_recipe_id', '') is null then raise exception 'each component needs an ingredient or a prep';
      elsif not exists (select 1 from phg.prep_recipes x where x.id = (c->>'prep_recipe_id')::uuid and (x.account_id is null or x.account_id = v_account)) then
        raise exception 'prep not found in this project';
      end if;
      v_row := v_row || jsonb_build_array((c - 'ingredient_ref') || jsonb_strip_nulls(jsonb_build_object('ingredient_id', v_ing)));
    end loop;
    insert into phg.recipe_versions (project_id, version, cocktail_name, recipe_name, concept, build_family, method, glassware, garnish,
                                     ingredients, targets, rationale, status, parent_version_id, account_id)
    values (v_id, coalesce(v_ver, 0) + 1, nullif(p->>'cocktail_name', ''), nullif(p->>'recipe_name', ''), nullif(p->>'concept', ''),
            nullif(p->>'build_family', ''), nullif(p->>'method', ''), nullif(p->>'glassware', ''), nullif(p->>'garnish', ''),
            v_row, coalesce(p->'targets', '{}'::jsonb), jsonb_build_object('source', 'harmony_voice_build', 'proposal_id', p_proposal_id),
            case when p->>'status' = 'candidate' then 'candidate' else 'draft' end, v_parent,
            (select account_id from phg.recipe_projects where id = v_id))
    returning id into v_id2;
    for c in select value from jsonb_array_elements(v_row) loop
      v_ord := v_ord + 1;
      insert into phg.recipe_components (recipe_version_id, ingredient_id, prep_recipe_id, quantity, unit, role, optional, notes, sort_order)
      values (v_id2, nullif(c->>'ingredient_id', '')::uuid,
              case when nullif(c->>'ingredient_id', '') is null then (c->>'prep_recipe_id')::uuid end,
              (c->>'quantity')::numeric, c->>'unit', nullif(c->>'role', ''), coalesce((c->>'optional')::boolean, false), nullif(c->>'notes', ''), v_ord);
    end loop;
    begin
      v_cost := to_jsonb(public.phg_recipe_cost(v_id2, current_date));
    exception when others then
      v_cost := jsonb_build_object('status', 'pending', 'reason', sqlerrm);
    end;
    return jsonb_build_object('recipe_project_id', v_id, 'recipe_version_id', v_id2, 'version', coalesce(v_ver, 0) + 1,
                              'component_count', v_ord, 'new_ingredients', v_new->'created', 'cost', v_cost);

  elsif p_action_key = 'update_recipe_draft' then
    v_id := coalesce(nullif(p_target_id, '')::uuid, nullif(p->>'recipe_version_id', '')::uuid);
    if not phg.harmony_recipe_version_visible(v_account, v_id) then raise exception 'recipe version not found in this project'; end if;
    select to_jsonb(v) || jsonb_build_object('components', (select coalesce(jsonb_agg(to_jsonb(rc) order by rc.sort_order), '[]'::jsonb)
                                                           from phg.recipe_components rc where rc.recipe_version_id = v.id))
      into v_prev from phg.recipe_versions v where v.id = v_id and v.status in ('draft','candidate') for update;
    if v_prev is null then raise exception 'only draft or candidate versions can be edited; make a new version instead'; end if;
    update phg.recipe_versions set
      cocktail_name = coalesce(p#>>'{fields,cocktail_name}', cocktail_name),
      recipe_name   = coalesce(p#>>'{fields,recipe_name}', recipe_name),
      concept       = coalesce(p#>>'{fields,concept}', concept),
      build_family  = coalesce(p#>>'{fields,build_family}', build_family),
      method        = coalesce(p#>>'{fields,method}', method),
      glassware     = coalesce(p#>>'{fields,glassware}', glassware),
      garnish       = coalesce(p#>>'{fields,garnish}', garnish),
      targets       = coalesce(p#>'{fields,targets}', targets)
    where id = v_id;
    if p ? 'components' then
      v_new := phg.harmony_new_ingredients(v_account, v_user, p->'new_ingredients');
      v_refs := v_new->'refs';
      delete from phg.recipe_components where recipe_version_id = v_id;   -- draft only; previous rows are returned in 'undo'
      v_row := '[]'::jsonb;
      for c in select value from jsonb_array_elements(p->'components') loop
        v_ord := v_ord + 1;
        v_ing := coalesce(nullif(c->>'ingredient_id', '')::uuid, nullif(v_refs->>(c->>'ingredient_ref'), '')::uuid);
        if v_ing is not null then perform phg.harmony_check_ingredient(v_account, v_ing);
        elsif not exists (select 1 from phg.prep_recipes x where x.id = nullif(c->>'prep_recipe_id', '')::uuid and (x.account_id is null or x.account_id = v_account)) then
          raise exception 'component % has no ingredient or prep in this project', v_ord;
        end if;
        insert into phg.recipe_components (recipe_version_id, ingredient_id, prep_recipe_id, quantity, unit, role, optional, notes, sort_order)
        values (v_id, v_ing, case when v_ing is null then (c->>'prep_recipe_id')::uuid end, (c->>'quantity')::numeric, c->>'unit',
                nullif(c->>'role', ''), coalesce((c->>'optional')::boolean, false), nullif(c->>'notes', ''), v_ord);
        v_row := v_row || jsonb_build_array((c - 'ingredient_ref') || jsonb_strip_nulls(jsonb_build_object('ingredient_id', v_ing)));
      end loop;
      update phg.recipe_versions set ingredients = v_row where id = v_id;
    end if;
    return jsonb_build_object('recipe_version_id', v_id, 'updated', true, 'undo', jsonb_build_object('previous', v_prev));

  elsif p_action_key = 'attach_recipe_to_menu_item' then
    v_id := coalesce(nullif(p->>'menu_item_id', '')::uuid, nullif(p_target_id, '')::uuid);
    v_id2 := nullif(p->>'recipe_version_id', '')::uuid;
    if v_id is null or v_id2 is null then raise exception 'menu item and recipe version required'; end if;
    if not exists (select 1 from phg.menu_items where id = v_id and menu_project_id = p_menu_project_id) then raise exception 'menu item not found'; end if;
    if not phg.harmony_recipe_version_visible(v_account, v_id2) then raise exception 'recipe version not found in this project'; end if;
    if exists (select 1 from phg.recipe_versions where id = v_id2 and status = 'rejected') then raise exception 'recipe version was rejected'; end if;
    select to_jsonb(current_recipe_version_id) into v_prev from phg.menu_items where id = v_id;
    perform public.phg_set_menu_item_recipe(v_id, v_id2);     -- same effect as set_menu_item_recipe (training marked stale)
    return jsonb_build_object('menu_item_id', v_id, 'recipe_version_id', v_id2,
                              'undo', jsonb_build_object('action', 'attach_recipe_to_menu_item', 'menu_item_id', v_id, 'recipe_version_id', v_prev));

  -- ---------------------------------------------------------------- settings
  elsif p_action_key = 'set_account_setting' then
    select * into v_def from phg.setting_definitions where key = p->>'key' and active;
    if not found then raise exception 'unknown setting %', p->>'key'; end if;
    if v_def.per_scope = 'person' then raise exception 'personal settings are stored as preferences (harmony_memory), not account settings'; end if;
    if v_role is null or v_role <> all (v_def.edit_roles) then raise exception 'your role cannot change %', v_def.label; end if;
    if not (p ? 'value') then raise exception 'value required'; end if;
    select to_jsonb(s) - 'history' into v_prev from phg.account_settings s
     where s.account_id = v_account and s.key = v_def.key and s.scope_key = coalesce(p->>'scope_key', '');
    insert into phg.account_settings (account_id, key, scope_key, value, source, confidence, evidence, confirmed_by, confirmed_at)
    values (v_account, v_def.key, coalesce(p->>'scope_key', ''), p->'value', coalesce(nullif(p->>'source', ''), 'asked'),
            nullif(p->>'confidence', '')::numeric, coalesce(p->'evidence', '{}'::jsonb) || jsonb_build_object('proposal_id', p_proposal_id),
            v_user, now())
    on conflict (account_id, key, scope_key) do update set
      value = excluded.value, source = excluded.source, confidence = excluded.confidence, evidence = excluded.evidence,
      confirmed_by = excluded.confirmed_by, confirmed_at = excluded.confirmed_at;
    return jsonb_build_object('key', v_def.key, 'scope_key', coalesce(p->>'scope_key', ''), 'value', p->'value',
                              'undo', jsonb_build_object('previous', v_prev));

  -- ---------------------------------------------------------------- saved filters and views (draft 03)
  elsif p_action_key = 'save_filter' then
    v_shared := coalesce((p->>'shared')::boolean, false);
    if v_shared and v_role not in ('owner','admin','editor') then raise exception 'only owners, admins and editors can share filters'; end if;
    v_owner := case when v_shared then null else v_user end;
    v_id := nullif(p->>'filter_id', '')::uuid;
    if v_id is null then
      insert into phg.saved_filters (account_id, user_id, name, entity_key, conditions, created_by, source)
      values (v_account, v_owner, btrim(p->>'name'), p->>'entity', coalesce(p->'conditions', '[]'::jsonb), v_user,
              coalesce(nullif(p->>'source', ''), 'spoken'))
      returning id into v_id;
      return jsonb_build_object('filter_id', v_id, 'created', true);
    end if;
    select to_jsonb(f) into v_prev from phg.saved_filters f
     where f.id = v_id and f.account_id = v_account and f.archived_at is null
       and (f.user_id = v_user or (f.user_id is null and v_role in ('owner','admin','editor')));
    if v_prev is null then raise exception 'filter not found, or not yours to change'; end if;
    update phg.saved_filters set name = coalesce(nullif(btrim(p->>'name'), ''), name),
                                 conditions = coalesce(p->'conditions', conditions)
     where id = v_id;   -- entity and sharing are fixed once saved
    return jsonb_build_object('filter_id', v_id, 'created', false, 'undo', jsonb_build_object('previous', v_prev));

  elsif p_action_key = 'save_view' then
    v_shared := coalesce((p->>'shared')::boolean, false);
    if v_shared and v_role not in ('owner','admin','editor') then raise exception 'only owners, admins and editors can share views'; end if;
    insert into phg.saved_views (account_id, user_id, name, entity_key, metric_keys, filter_ids, extra_conditions, period_preset_key,
                                 group_by, columns, sort, display, pinned, created_by, source)
    values (v_account, case when v_shared then null else v_user end, btrim(p->>'name'), nullif(p->>'entity', ''),
            coalesce(array(select jsonb_array_elements_text(p->'metric_keys')), '{}'),
            coalesce(array(select (jsonb_array_elements_text(p->'filter_ids'))::uuid), '{}'),
            coalesce(p->'extra_conditions', '[]'::jsonb), nullif(p->>'period_preset_key', ''),
            coalesce(array(select jsonb_array_elements_text(p->'group_by')), '{}'),
            coalesce(array(select jsonb_array_elements_text(p->'columns')), '{}'),
            coalesce(p->'sort', '[]'::jsonb), coalesce(nullif(p->>'display', ''), 'table'),
            coalesce((p->>'pinned')::boolean, false), v_user, coalesce(nullif(p->>'source', ''), 'spoken'))
    returning id into v_id;
    return jsonb_build_object('view_id', v_id, 'undo', jsonb_build_object('action', 'delete_view', 'view_id', v_id));

  elsif p_action_key in ('update_view','delete_view') then
    v_id := coalesce(nullif(p_target_id, '')::uuid, nullif(p->>'view_id', '')::uuid);
    select to_jsonb(v) into v_prev from phg.saved_views v
     where v.id = v_id and v.account_id = v_account
       and (v.user_id = v_user or (v.user_id is null and v_role in ('owner','admin','editor')));
    if v_prev is null then raise exception 'view not found, or not yours to change'; end if;
    if p_action_key = 'delete_view' then
      update phg.saved_views set archived_at = now() where id = v_id and archived_at is null;
      return jsonb_build_object('view_id', v_id, 'archived', true,
                                'undo', jsonb_build_object('action', 'update_view', 'view_id', v_id, 'restore', true));
    end if;
    update phg.saved_views set
      archived_at       = case when coalesce((p->>'restore')::boolean, false) then null else archived_at end,
      name              = coalesce(nullif(btrim(p->>'name'), ''), name),
      entity_key        = case when p ? 'entity' then nullif(p->>'entity', '') else entity_key end,
      metric_keys       = case when p ? 'metric_keys' then coalesce(array(select jsonb_array_elements_text(p->'metric_keys')), '{}') else metric_keys end,
      filter_ids        = case when p ? 'filter_ids' then coalesce(array(select (jsonb_array_elements_text(p->'filter_ids'))::uuid), '{}') else filter_ids end,
      extra_conditions  = coalesce(p->'extra_conditions', extra_conditions),
      period_preset_key = case when p ? 'period_preset_key' then nullif(p->>'period_preset_key', '') else period_preset_key end,
      group_by          = case when p ? 'group_by' then coalesce(array(select jsonb_array_elements_text(p->'group_by')), '{}') else group_by end,
      columns           = case when p ? 'columns' then coalesce(array(select jsonb_array_elements_text(p->'columns')), '{}') else columns end,
      sort              = coalesce(p->'sort', sort),
      display           = coalesce(nullif(p->>'display', ''), display),
      pinned            = coalesce((p->>'pinned')::boolean, pinned)
    where id = v_id;
    return jsonb_build_object('view_id', v_id, 'updated', true, 'undo', jsonb_build_object('previous', v_prev));

  -- ---------------------------------------------------------------- setup walkthrough (beyond the brief; see header)
  elsif p_action_key = 'save_party' then
    if nullif(p->>'gl_default_code', '') is not null and to_regclass('phg.gl_accounts') is not null
       and not exists (select 1 from phg.gl_accounts g where g.code = p->>'gl_default_code' and (g.account_id = v_account or g.account_id is null)) then
      raise exception 'unknown GL account %', p->>'gl_default_code';
    end if;
    v_id := nullif(p->>'party_id', '')::uuid;
    if v_id is null then
      insert into phg.parties (account_id, name, kinds, aliases, contact_name, email, phone, address, website, account_number,
                               delivery_days, order_cutoff, payment_terms, gl_default_code, notes, source, created_by)
      values (v_account, btrim(p->>'name'),
              coalesce(array(select jsonb_array_elements_text(p->'kinds')), '{supplier}'),
              coalesce(array(select jsonb_array_elements_text(p->'aliases')), '{}'),
              nullif(p->>'contact_name', ''), nullif(p->>'email', ''), nullif(p->>'phone', ''), p->'address', nullif(p->>'website', ''),
              nullif(p->>'account_number', ''), coalesce(array(select jsonb_array_elements_text(p->'delivery_days')), '{}'),
              nullif(p->>'order_cutoff', ''), nullif(p->>'payment_terms', ''), nullif(p->>'gl_default_code', ''), nullif(p->>'notes', ''),
              coalesce(nullif(p->>'source', ''), 'asked'), v_user)
      returning id into v_id;
      return jsonb_build_object('party_id', v_id, 'created', true);
    end if;
    select to_jsonb(x) into v_prev from phg.parties x where x.id = v_id and x.account_id = v_account and x.archived_at is null;
    if v_prev is null then raise exception 'supplier not found'; end if;
    update phg.parties set
      name = coalesce(nullif(btrim(p->>'name'), ''), name),
      kinds = case when p ? 'kinds' then coalesce(array(select jsonb_array_elements_text(p->'kinds')), kinds) else kinds end,
      aliases = case when p ? 'aliases' then coalesce(array(select jsonb_array_elements_text(p->'aliases')), '{}') else aliases end,
      contact_name = coalesce(p->>'contact_name', contact_name), email = coalesce(p->>'email', email), phone = coalesce(p->>'phone', phone),
      address = coalesce(p->'address', address), website = coalesce(p->>'website', website),
      account_number = coalesce(p->>'account_number', account_number),
      delivery_days = case when p ? 'delivery_days' then coalesce(array(select jsonb_array_elements_text(p->'delivery_days')), '{}') else delivery_days end,
      order_cutoff = coalesce(p->>'order_cutoff', order_cutoff), payment_terms = coalesce(p->>'payment_terms', payment_terms),
      gl_default_code = coalesce(p->>'gl_default_code', gl_default_code), notes = coalesce(p->>'notes', notes), updated_at = now()
    where id = v_id;
    return jsonb_build_object('party_id', v_id, 'created', false, 'undo', jsonb_build_object('previous', v_prev));

  elsif p_action_key = 'save_invoice_coding_rule' then
    if to_regclass('phg.gl_accounts') is not null
       and not exists (select 1 from phg.gl_accounts g where g.code = p->>'gl_code' and (g.account_id = v_account or g.account_id is null)) then
      raise exception 'unknown GL account %', p->>'gl_code';
    end if;
    if nullif(p->>'party_id', '') is not null
       and not exists (select 1 from phg.parties x where x.id = (p->>'party_id')::uuid and x.account_id = v_account) then
      raise exception 'supplier not found';
    end if;
    v_id := nullif(p->>'rule_id', '')::uuid;
    if v_id is not null then
      select to_jsonb(r) into v_prev from phg.invoice_coding_rules r where r.id = v_id and r.account_id = v_account;
      if v_prev is null then raise exception 'rule not found'; end if;
      update phg.invoice_coding_rules set active = false, updated_at = now() where id = v_id;   -- replace = retire + insert
    end if;
    insert into phg.invoice_coding_rules (account_id, party_id, party_pattern, line_pattern, match_kind, gl_code, priority, confidence,
                                          source, confirmed_by, confirmed_at)
    values (v_account, nullif(p->>'party_id', '')::uuid, nullif(p->>'party_pattern', ''), nullif(p->>'line_pattern', ''),
            coalesce(nullif(p->>'match_kind', ''), 'ilike'), p->>'gl_code', coalesce(nullif(p->>'priority', '')::int, 100),
            nullif(p->>'confidence', '')::numeric, coalesce(nullif(p->>'source', ''), 'asked'), v_user, now())
    returning id into v_id2;
    return jsonb_build_object('rule_id', v_id2, 'replaced', v_id, 'undo', jsonb_build_object('previous', v_prev));
  end if;

  raise exception 'harmony action % not handled', p_action_key;
end $$;

revoke all on function phg.harmony_session_user(uuid, text), phg.harmony_check_ingredient(uuid, uuid),
                       phg.harmony_create_ingredient(uuid, uuid, jsonb), phg.harmony_new_ingredients(uuid, uuid, jsonb),
                       phg.harmony_recipe_visible(uuid, uuid), phg.harmony_recipe_version_visible(uuid, uuid),
                       phg.harmony_execute_command_action(uuid, text, uuid, text, text, jsonb)
  from public, anon, authenticated, service_role;

-- ---------------------------------------------------------------------------------------------------------------
-- 3. REPLACEMENT of public.phg_command_execute_approved_action
--    = live definition (pg_get_functiondef, 2026-09-28) + ONE branch marked "HARMONY DRAFT 06". Diff before applying.
-- ---------------------------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.phg_command_execute_approved_action(p_menu_project_id uuid, p_sync_token text, p_proposal_id uuid, p_approval_token text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
 a phg.command_action_proposals%rowtype; p jsonb; v_result jsonb;
 menu_item_id uuid; recipe_version_id uuid; training_package_id uuid; new_price numeric;
begin
 if not public.phg_menu_authorize(p_menu_project_id,p_sync_token) then raise exception 'invalid_menu_token'; end if;
 select a0.* into a from phg.command_action_proposals a0
 join phg.command_sessions s0 on s0.id=a0.session_id
 where a0.id=p_proposal_id and s0.menu_project_id=p_menu_project_id for update of a0;
 if not found then raise exception 'action proposal not found'; end if;
 if a.status<>'proposed' then raise exception 'action proposal is no longer pending'; end if;
 if p_approval_token is null or encode(extensions.digest(p_approval_token,'sha256'),'hex')<>a.approval_token_hash then raise exception 'invalid approval token'; end if;
 p:=a.payload;

 if a.action_key='set_menu_price' then
  menu_item_id:=coalesce(nullif(a.target_id,'')::uuid,nullif(p->>'menu_item_id','')::uuid); new_price:=nullif(p->>'menu_price','')::numeric;
  if menu_item_id is null or new_price is null or new_price<0 then raise exception 'menu item and valid menu price required'; end if;
  v_result:=public.phg_menu_item_price_set(
    p_menu_project_id,p_sync_token,menu_item_id,
    nullif(p->>'location_key',''),nullif(p->>'revenue_center',''),new_price,
    coalesce(nullif(p->>'effective_from','')::date,current_date),
    nullif(p->>'effective_to','')::date,
    coalesce(nullif(p->>'source_ref',''),'harmony_command_center'),
    coalesce(p->'metadata','{}'::jsonb)||jsonb_build_object('proposal_id',a.id)
  );
 elsif a.action_key='set_financial_rule' then
  v_result:=public.phg_financial_rule_set(
    p_menu_project_id,p_sync_token,
    nullif(p->>'location_key',''),nullif(p->>'revenue_center',''),
    p->>'rule_key',p->>'rule_group',coalesce(nullif(p->>'calculation_type',''),'rate'),
    nullif(p->>'rate_fraction','')::numeric,nullif(p->>'fixed_amount','')::numeric,
    coalesce(nullif(p->>'currency',''),'USD'),nullif(p->>'base_metric',''),
    coalesce(nullif(p->>'effective_from','')::date,current_date),
    nullif(p->>'effective_to','')::date,
    coalesce(nullif(p->>'source_ref',''),'harmony_command_center'),
    coalesce(p->'metadata','{}'::jsonb)||jsonb_build_object('proposal_id',a.id)
  );
 elsif a.action_key='set_purchase_cost' then
  v_result:=public.phg_purchase_cost_set(
    p_menu_project_id,p_sync_token,
    nullif(p->>'location_key',''),
    nullif(p->>'ingredient_id','')::uuid,
    nullif(p->>'product_id','')::uuid,
    nullif(p->>'procurement_item_id','')::uuid,
    nullif(p->>'vendor_key',''),
    coalesce(nullif(p->>'package_quantity','')::numeric,1),
    p->>'package_unit',
    nullif(p->>'package_size','')::numeric,
    nullif(p->>'package_size_unit',''),
    nullif(p->>'cost','')::numeric,
    coalesce(nullif(p->>'currency',''),'USD'),
    coalesce(nullif(p->>'effective_from','')::date,current_date),
    nullif(p->>'effective_to','')::date,
    coalesce(nullif(p->>'source_ref',''),'harmony_command_center')
  );
 elsif a.action_key='save_reporting_period' then
  v_result:=public.phg_reporting_period_save(
    p_menu_project_id,p_sync_token,
    coalesce(nullif(a.target_id,'')::uuid,nullif(p->>'period_id','')::uuid),
    nullif(p->>'location_key',''),nullif(p->>'period_key',''),p->>'name',
    coalesce(nullif(p->>'period_type',''),'custom'),
    nullif(p->>'start_date','')::date,nullif(p->>'end_date','')::date,
    nullif(p->>'revenue_center',''),nullif(p->>'default_basis',''),
    coalesce(p->'metadata','{}'::jsonb)||jsonb_build_object('proposal_id',a.id)
  );
 elsif a.action_key='set_menu_item_recipe' then
  menu_item_id:=coalesce(nullif(a.target_id,'')::uuid,nullif(p->>'menu_item_id','')::uuid); recipe_version_id:=nullif(p->>'recipe_version_id','')::uuid;
  if menu_item_id is null or recipe_version_id is null then raise exception 'menu item and recipe version required'; end if;
  if not exists(select 1 from phg.menu_items where id=menu_item_id and menu_project_id=p_menu_project_id) then raise exception 'menu item not found'; end if;
  if not exists(select 1 from phg.recipe_versions where id=recipe_version_id) then raise exception 'recipe version not found'; end if;
  perform public.phg_set_menu_item_recipe(menu_item_id,recipe_version_id);
  v_result:=jsonb_build_object('menu_item_id',menu_item_id,'recipe_version_id',recipe_version_id,'training_status','prior approved training marked stale when recipe changed');
 elsif a.action_key='persist_recipe_candidate' then
  v_result:=public.phg_command_persist_recipe_candidate(p_menu_project_id,p_sync_token,p);
 elsif a.action_key='create_menu_item' then
  recipe_version_id:=nullif(p->>'recipe_version_id','')::uuid;
  insert into phg.menu_items(menu_project_id,item_key,name,item_type,status,recipe_project_id,current_recipe_version_id,menu_description,menu_price,training_required,metadata,section_name,subsection_name)
  values(p_menu_project_id,coalesce(nullif(p->>'item_key',''),'cmd_'||substr(replace(gen_random_uuid()::text,'-',''),1,16)),coalesce(nullif(p->>'name',''),'Untitled menu item'),coalesce(nullif(p->>'item_type',''),'cocktail'),coalesce(nullif(p->>'status',''),'concept'),
   case when recipe_version_id is null then null else (select project_id from phg.recipe_versions where id=recipe_version_id) end,recipe_version_id,nullif(p->>'menu_description',''),nullif(p->>'menu_price','')::numeric,coalesce((p->>'training_required')::boolean,false),
   coalesce(p->'metadata','{}'::jsonb)||jsonb_build_object('created_by','harmony_command_center','proposal_id',a.id),nullif(p->>'section_name',''),nullif(p->>'subsection_name',''))
  returning id into menu_item_id;
  if nullif(p->>'menu_price','') is not null then
    perform public.phg_menu_item_price_set(
      p_menu_project_id,p_sync_token,menu_item_id,
      nullif(p->>'location_key',''),nullif(p->>'revenue_center',''),
      (p->>'menu_price')::numeric,
      coalesce(nullif(p->>'effective_from','')::date,current_date),
      nullif(p->>'effective_to','')::date,
      'harmony_command_center',
      jsonb_build_object('proposal_id',a.id,'created_with_menu_item',true)
    );
  end if;
  v_result:=public.phg_menu_item_full_context(menu_item_id);
 elsif a.action_key='persist_training_package' then
  menu_item_id:=coalesce(nullif(a.target_id,'')::uuid,nullif(p->>'menu_item_id','')::uuid); recipe_version_id:=nullif(p->>'recipe_version_id','')::uuid;
  if menu_item_id is null or recipe_version_id is null then raise exception 'menu item and recipe version required'; end if;
  if not exists(select 1 from phg.menu_items where id=menu_item_id and menu_project_id=p_menu_project_id) then raise exception 'menu item not found'; end if;
  v_result:=public.phg_training_persist(menu_item_id,recipe_version_id,coalesce(p->'content','{}'::jsonb),coalesce(p->'claims','[]'::jsonb),coalesce(p->'assessments','[]'::jsonb),coalesce(p->'research','{}'::jsonb));
 elsif a.action_key='approve_training_package' then
  training_package_id:=coalesce(nullif(a.target_id,'')::uuid,nullif(p->>'training_package_id','')::uuid);
  if training_package_id is null then raise exception 'training package required'; end if;
  update phg.training_packages tp set status='approved',updated_at=now() from phg.menu_items mi
  where tp.id=training_package_id and mi.id=tp.menu_item_id and mi.menu_project_id=p_menu_project_id
  returning jsonb_build_object('training_package_id',tp.id,'status',tp.status,'version',tp.version) into v_result;
  if v_result is null then raise exception 'training package not found'; end if;
 -- >>> HARMONY DRAFT 06: new recipe-building / settings / views / setup actions (the only change to this function) >>>
 elsif a.action_key in ('create_record','create_ingredient','create_prep_recipe','create_recipe_version','update_recipe_draft',
                        'attach_recipe_to_menu_item','set_account_setting','save_filter','save_view','update_view','delete_view',
                        'save_party','save_invoice_coding_rule') then
  v_result:=phg.harmony_execute_command_action(p_menu_project_id,p_sync_token,a.id,a.action_key,a.target_id,p);
 -- <<< HARMONY DRAFT 06 <<<
 else raise exception 'approved action is not executable by command center';
 end if;

 update phg.command_action_proposals set status='executed',decided_at=coalesce(decided_at,now()),executed_at=now(),result=v_result where id=a.id;

 if a.action_key in ('persist_recipe_candidate','create_menu_item','persist_training_package','approve_training_package','set_menu_price','set_menu_item_recipe','set_financial_rule','set_purchase_cost','save_reporting_period')
    and exists(select 1 from phg.command_workflow_steps where proposal_id=a.id) then
  update phg.command_workflow_steps set status='complete',result=v_result,updated_at=now() where proposal_id=a.id;
  update phg.command_workflows w set
   context=w.context||
    case
     when a.action_key='persist_recipe_candidate' then jsonb_build_object('recipe_project_id',v_result->>'recipe_project_id','recipe_version_id',v_result->>'recipe_version_id')
     when a.action_key='create_menu_item' then jsonb_build_object('menu_item_id',v_result#>>'{menu_item,id}','recipe_version_id',coalesce(v_result#>>'{menu_item,current_recipe_version_id}',w.context->>'recipe_version_id'))
     when a.action_key='persist_training_package' then jsonb_build_object('training_package_id',coalesce(v_result->>'training_package_id',v_result->>'id'))
     else '{}'::jsonb end,
   current_step=(select coalesce(min(s.step_no),w.current_step) from phg.command_workflow_steps s where s.workflow_id=w.id and s.status='pending'),
   status='running',updated_at=now()
  where w.id=(select workflow_id from phg.command_workflow_steps where proposal_id=a.id limit 1);
  update phg.command_workflow_steps set status=case
      when execution_class in ('proposal_required','approval_required') then 'waiting_approval'
      when execution_class='external_research' then 'waiting_input'
      else 'ready' end,updated_at=now()
  where workflow_id=(select workflow_id from phg.command_workflow_steps where proposal_id=a.id limit 1)
    and step_no=(select min(s2.step_no) from phg.command_workflow_steps s2 where s2.workflow_id=(select workflow_id from phg.command_workflow_steps where proposal_id=a.id limit 1) and s2.status='pending');
 end if;

 return jsonb_build_object('status','executed','action_key',a.action_key,'result',v_result);
end $function$;

-- grants unchanged from live: {postgres=X, service_role=X}; CREATE OR REPLACE keeps them, re-stated for clarity
revoke all on function public.phg_command_execute_approved_action(uuid, text, uuid, text) from public, anon, authenticated;
grant execute on function public.phg_command_execute_approved_action(uuid, text, uuid, text) to service_role;

commit;
