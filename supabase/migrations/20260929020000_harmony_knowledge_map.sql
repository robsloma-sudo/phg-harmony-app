-- APPLIED 2026-09-29 (Rob approved; safety review rounds 1-2 fixed; forward + rollback dry-run clean). Spec: handoff/HARMONY_CONVERSATION_MODEL.md §4, §4.1-4.3, §4C, §10
--
-- What this does (plain English)
--   Gives Harmony a map of PHG data and one safe door to ask it questions.
--   * phg.harmony_entities / harmony_entity_fields: the ~35 "things" Rob talks about (venue, brand, recipe ...),
--     their aliases, the tables behind them, how to look one up by name, and their useful fields in plain words.
--   * phg.harmony_paths: the join paths between things, written once and checked (verified_at) so the navigator
--     never guesses a join.
--   * phg.harmony_table_access: the whitelist. Every table is shared_read (market/knowledge data, same for all
--     projects), project_read (house data, filtered to one project) or never (secrets, sessions, keys, auth, vault,
--     staging, logs). Anything not listed is refused.
--   * public.phg_harmony_query(account, user, sql, max_rows): the read-only gateway, modelled on phg_designer_query:
--     membership check, one statement, no comments, function denylist, schema-qualified-call allowlist (pg_catalog
--     only), EXPLAIN-based table whitelist, read-only transaction, row cap, 5 MB payload cap, logged to
--     phg.harmony_query_log. NOTE: it does NOT enforce a wall-clock timeout by itself (see risk 6).
--   * role phg_harmony_reader (NOLOGIN): the only role the query runs as. SELECT on whitelisted tables only; project
--     tables get row-level-security policies that show only the current project's rows.
--
-- Live-schema facts this draft relies on (checked read-only on 2026-09-28/29)
--   * phg.account_memberships(account_id, user_id, role in owner|admin|editor|analyst|viewer, status active|invited|disabled).
--   * phg.accounts = PHG projects (1 row). public.accounts = 41,886 market VENUES. Different things, same name.
--   * Most phg operations tables are NOT scoped by account_id: they carry menu_project_id, location_key
--     (= phg.sales_locations.external_location_key, as phg_sales_summary joins it) or location_id (= phg.sales_locations.id).
--     So "account_column" alone cannot scope them; this draft stores a scope_kind + scope_expr per table.
--   * phg.recipe_projects / recipe_versions / ingredients / prep_recipes / vendors / units have NO account_id today
--     (see 04 for recipe_*). Until 04 is applied and backfilled, recipe tables are mapped via menu_items -> menu_projects.
--   * 21 SECURITY DEFINER functions in public are EXECUTE-able by PUBLIC (kick_*, refresh_*, sync_*, classify_menu_page ...).
--     Any new role inherits that. The gateway allows qualified calls only into pg_catalog, and README asks Rob to revoke PUBLIC.
--   * Pattern reused from 20260928050000/052000 (designer gateway): inner SECURITY DEFINER function OWNED BY the
--     low-privilege role, so the query cannot switch role (Postgres refuses role changes inside definer functions).
--
-- Remaining risk of SQL-level scoping (read before approving)
--   1. Scoping is enforced by RLS policies on the reader role, keyed to a per-transaction scope row
--      (phg.harmony_query_scope: backend pid + transaction id -> account). The query runs read-only, so it cannot
--      insert a scope row for another account. This is much stronger than rewriting SQL text, BUT:
--   2. Every project_read table needs a correct scope_expr. A wrong or missing expression = a leak for that table.
--      The loop below refuses to grant a project_read table that has no scope_expr, and the checklist tests each one.
--   3. Enabling RLS on existing phg tables changes behaviour for any non-owner, non-BYPASSRLS role reading them.
--      Today that is only phg_menu_designer (service_role and postgres bypass RLS). The loop adds a permissive
--      menu_designer_read policy wherever it enables RLS, so the designer keeps exactly what it has today.
--   4. SECURITY DEFINER functions run as their owner and ignore the reader's RLS. The gateway refuses every
--      schema-qualified function call except pg_catalog (allowlist) and OPERATOR(...), and runs with search_path = pg_catalog, but a PUBLIC-executable definer function is still
--      a hole if it can be reached unqualified through pg_catalog (it cannot today). Revoking PUBLIC EXECUTE on the 21
--      functions listed in README closes it properly.
--   5. EXPLAIN shows base tables after view expansion. A view is allowed only if every base table under it is
--      whitelisted (security_invoker=false views check privileges as the view owner, so the plan check is what guards them).
--   6. Timeouts: the gateway's `set local statement_timeout = '10s'` does NOT bound the query. statement_timeout is
--      armed when a top-level statement starts; changing it inside the already-running RPC call does not re-arm the
--      timer for that statement (it only affects later statements of the same transaction). The CALLER must enforce
--      the limit: (a) the edge function wraps the RPC in an AbortController / fetch timeout (~10 s), and (b) for a
--      dedicated caller role, `alter role <harmony_caller> set statement_timeout = '10s'` (recommendation only; this
--      draft deliberately does NOT alter service_role). Row-count/timing side channels: row cap, 5 MB payload cap, log.
--   7. Locks: enabling RLS / creating policies takes ACCESS EXCLUSIVE locks on ~25 phg tables. The script sets
--      lock_timeout = 3s. Run it OFF-PEAK; if it fails with SQLSTATE 55P03 (lock_not_available) nothing was applied
--      (single transaction) -> simply retry later.
--   8. Every project_read table carries TWO policies for the reader: permissive harmony_read AND restrictive
--      harmony_scope (same expression). Permissive policies are OR-ed, so any other permissive policy reaching the
--      reader (TO public or TO phg_harmony_reader) would widen access; the restrictive one is AND-ed and cannot be
--      widened. harmony_apply_table_access() also refuses (raises) if such a foreign policy exists.
--
-- Rollback (scripted; run as postgres in ONE transaction, off-peak; order matters: RLS/policies need the access table and
-- the scope functions, so they go first, then functions, then tables, then grants, then the role)
--   begin;
--   set local lock_timeout = '3s';
--   do $rb$
--   declare r record;
--   begin
--     -- 1. disable RLS only where this migration enabled it
--     if to_regclass('phg.harmony_table_access') is not null then
--       for r in select to_regclass(format('%I.%I', schema_name, table_pattern)) t from phg.harmony_table_access
--                 where rls_enabled_by_migration and not is_pattern loop
--         if r.t is not null then execute format('alter table %s disable row level security', r.t); end if;
--       end loop;
--     end if;
--     -- 2. drop our policies everywhere
--     for r in select polname, polrelid::regclass t from pg_policy
--               where polname in ('harmony_read','harmony_scope','menu_designer_read_h') loop
--       execute format('drop policy %I on %s', r.polname, r.t);
--     end loop;
--   end $rb$;
--   -- 3. functions (gateway first, then the reader-owned inner functions, then helpers)
--   drop function if exists public.phg_harmony_query(uuid, uuid, text, int);
--   drop function if exists public.phg_harmony_query_finish(bigint, int, int, text);
--   drop function if exists phg_harmony_q.run(text, int);
--   drop function if exists phg_harmony_q.plan(text);
--   drop schema if exists phg_harmony_q;
--   drop function if exists phg.harmony_apply_table_access();
--   drop function if exists phg.harmony_table_rule(text, text);
--   drop function if exists phg.harmony_scope_recipe_versions();
--   drop function if exists phg.harmony_scope_menu_items();
--   drop function if exists phg.harmony_scope_menu_projects();
--   drop function if exists phg.harmony_scope_location_ids();
--   drop function if exists phg.harmony_scope_location_keys();
--   drop function if exists phg.harmony_scope_user();
--   drop function if exists phg.harmony_scope_account();
--   -- 4. tables (children first)
--   drop table if exists phg.harmony_query_scope, phg.harmony_query_log, phg.harmony_paths, phg.harmony_entity_fields,
--     phg.harmony_entities, phg.harmony_table_access;
--   -- 5. grants and the role
--   do $rb$ begin
--     if exists (select 1 from pg_roles where rolname = 'phg_harmony_reader') then
--       revoke all on all tables in schema public, phg, phg_design, phg_flavor from phg_harmony_reader;
--       revoke usage on schema public, phg, phg_design, phg_flavor from phg_harmony_reader;
--       drop owned by phg_harmony_reader;       -- PG16+: needs postgres's membership, so it runs before any revoke of it
--       drop role phg_harmony_reader;           -- also removes the postgres membership
--     end if;
--   end $rb$;
--   -- 6. verify (expect: all nulls, 0, 0)
--   select to_regclass('phg.harmony_table_access') ta, to_regclass('phg.harmony_query_scope') qs,
--          to_regprocedure('public.phg_harmony_query(uuid,uuid,text,int)') gw, to_regnamespace('phg_harmony_q') ns,
--          (select count(*) from pg_roles where rolname = 'phg_harmony_reader') roles,
--          (select count(*) from pg_policy where polname in ('harmony_read','harmony_scope','menu_designer_read_h')) policies;
--   commit;

set local lock_timeout = '3s';   -- off-peak; on 55P03 nothing is applied, retry later

-- ---------------------------------------------------------------------------------------------------------------
-- 1. Knowledge map tables (shared layer, admin-owned; no account_id because they describe the schema, not a business)
-- ---------------------------------------------------------------------------------------------------------------

create table if not exists phg.harmony_entities (
  key            text primary key,                        -- 'venue', 'house_recipe', 'brand' ...
  label          text not null,                           -- plain name Harmony says
  entity_group   text not null,                           -- Market | Place | Spirits | House work | Buying and cost | Operations | Knowledge | Organising
  aliases        text[] not null default '{}',            -- words Rob uses ('bar', 'restaurant', 'spot')
  description    text,
  main_tables    text[] not null default '{}',            -- schema-qualified, e.g. {'public.accounts'}
  scope          text not null check (scope in ('shared','project')),
  name_lookup    jsonb not null default '{}'::jsonb,      -- {"table":"public.accounts","id":"id","name":"account_name","aliases":null,"narrow_by":["city","state","type"],"match":"ilike|trigram|exact"}
  display        jsonb not null default '{}'::jsonb,      -- how to name one in speech: {"template":"{account_name} in {city}"}
  active         boolean not null default true,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table if not exists phg.harmony_entity_fields (
  id             uuid primary key default gen_random_uuid(),
  entity_key     text not null references phg.harmony_entities(key) on delete cascade,
  field_key      text not null,                           -- 'price', 'city'
  label          text not null,                           -- 'menu price'
  aliases        text[] not null default '{}',
  source         text not null,                           -- 'public.menu_items.price' or an expression over main_tables
  data_type      text not null default 'text',            -- text | number | money | percent | date | bool | geo
  unit           text,
  sample_values  jsonb,                                   -- a few live values refreshed by a job (never secrets)
  sensitive      boolean not null default false,          -- true = never spoken/returned (pay rates, personal data)
  filterable     boolean not null default true,           -- may be used in saved filters (draft 03)
  is_date_axis   boolean not null default false,          -- the date column time presets apply to (one per entity)
  unique (entity_key, field_key)
);

create table if not exists phg.harmony_paths (
  id             uuid primary key default gen_random_uuid(),
  path_key       text not null unique,                    -- 'venue_to_current_menu_items'
  from_entity    text not null references phg.harmony_entities(key),
  to_entity      text not null references phg.harmony_entities(key),
  description    text not null,
  join_spec      jsonb not null,                          -- ordered steps: [{"from":"public.accounts.account_id","to":"public.menus.account_id","filter":"menus.is_current"}]
  sample_sql     text,                                    -- a runnable example used by the path test
  verified_at    timestamptz,                             -- set only after the path test passes against the live schema
  verified_note  text,
  active         boolean not null default true,
  created_at     timestamptz not null default now()
);

create table if not exists phg.harmony_table_access (
  id                        uuid primary key default gen_random_uuid(),
  schema_name               text not null,
  table_pattern             text not null,                -- exact name, or a LIKE pattern when is_pattern (only for 'never')
  is_pattern                boolean not null default false,
  access                    text not null check (access in ('shared_read','project_read','never')),
  account_column            text,                         -- set when the table has its own account_id-style column
  scope_kind                text check (scope_kind in ('account_id','menu_project','location_id','location_key','custom')),
  scope_expr                text,                         -- RLS USING expression for the reader role (admin-authored)
  denied_columns            text[] not null default '{}', -- column-level grant excludes these (e.g. editor_token_hash)
  required_roles            text[] not null default '{}', -- membership roles allowed (empty = any active member)
  rls_enabled_by_migration  boolean not null default false,
  notes                     text,
  unique (schema_name, table_pattern),
  check (access <> 'project_read' or scope_expr is not null),
  check (not is_pattern or access = 'never')
);

create table if not exists phg.harmony_query_log (
  id            bigserial primary key,
  at            timestamptz not null default now(),
  account_id    uuid references phg.accounts(id) on delete set null,
  user_id       uuid,
  sql           text not null,
  tables        text[],
  rejected      text,                                     -- reason when refused before running
  row_count     int,
  ms            int,
  error         text
);
create index if not exists harmony_query_log_account_at on phg.harmony_query_log (account_id, at desc);

-- per-transaction scope: written by the gateway BEFORE the transaction turns read-only, read by RLS policies
create table if not exists phg.harmony_query_scope (
  backend_pid   int not null,
  xact_id       xid8 not null,
  account_id    uuid not null references phg.accounts(id) on delete cascade,
  user_id       uuid not null,
  created_at    timestamptz not null default now(),
  primary key (backend_pid, xact_id)
);

alter table phg.harmony_entities       enable row level security;
alter table phg.harmony_entity_fields  enable row level security;
alter table phg.harmony_paths          enable row level security;
alter table phg.harmony_table_access   enable row level security;
alter table phg.harmony_query_log      enable row level security;
alter table phg.harmony_query_scope    enable row level security;
revoke all on phg.harmony_entities, phg.harmony_entity_fields, phg.harmony_paths, phg.harmony_table_access,
              phg.harmony_query_log, phg.harmony_query_scope from public, anon, authenticated;
grant select on phg.harmony_entities, phg.harmony_entity_fields, phg.harmony_paths to service_role;

-- ---------------------------------------------------------------------------------------------------------------
-- 2. Seed: the 'never' list (spec §4.3) and the obvious extras found in the live schema
-- ---------------------------------------------------------------------------------------------------------------
insert into phg.harmony_table_access (schema_name, table_pattern, is_pattern, access, notes) values
  ('public', 'internal_secrets',            false, 'never', 'secrets'),
  ('phg',    'user_sessions',               false, 'never', 'session token hashes'),
  ('phg',    'harmony_device_keys',         false, 'never', 'Action button key hashes'),
  ('phg',    'account_memberships',         false, 'never', 'membership is checked by the gateway, not queried'),
  ('phg',    'command_action_proposals',    false, 'never', 'holds approval token hashes'),
  ('phg',    'harmony_query_scope',         false, 'never', 'gateway internals'),
  ('phg',    'language_interpretations',    false, 'never', 'raw utterance log'),
  ('phg',    'interpretation_shadow_runs',  false, 'never', 'raw utterance log'),
  ('phg',    'harmony_turns',               false, 'never', 'raw conversation turns (live since 2026-09-29)'),
  ('phg',    'harmony_corrections',         false, 'never', 'user corrections log (live since 2026-09-29)'),
  ('phg',    'harmony_aliases',             false, 'never', 'alias learning store (live since 2026-09-29)'),
  ('auth',   '%',                           true,  'never', 'Supabase auth'),
  ('vault',  '%',                           true,  'never', 'Supabase vault'),
  ('storage','%',                           true,  'never', 'storage internals'),
  ('cron',   '%',                           true,  'never', 'pg_cron'),
  ('net',    '%',                           true,  'never', 'pg_net'),
  ('realtime','%',                          true,  'never', 'realtime'),
  ('supabase_migrations','%',               true,  'never', 'migration history'),
  ('phg_internal','%',                      true,  'never', 'internal schema'),
  ('phg_designer','%',                      true,  'never', 'designer gateway internals'),
  ('pg_catalog','%',                        true,  'never', 'catalogs (also unlisted)'),
  ('information_schema','%',                true,  'never', 'catalogs (also unlisted)'),
  ('public', 'staging\_%',                  true,  'never', 'raw staging tables'),
  ('phg',    'staging\_%',                  true,  'never', 'raw staging tables'),
  ('public', '%\_log',                      true,  'never', 'logs'),
  ('phg',    '%\_log',                      true,  'never', 'logs (menu_designer_query_log, harmony_query_log ...)'),
  ('phg_flavor','%\_log',                   true,  'never', 'logs (change_log)'),
  ('public', '%\_audit%',                   true,  'never', 'audit tables'),
  ('phg',    '%\_audit%',                   true,  'never', 'audit tables (cola_pull_audit)'),
  ('public', '%backup%',                    true,  'never', 'backups (phg_capture_v2_backup)')
on conflict (schema_name, table_pattern) do nothing;

-- shared_read: market, place, spirits and knowledge data (same for every project, read-only)
insert into phg.harmony_table_access (schema_name, table_pattern, access, notes)
select 'public', t, 'shared_read', 'market/knowledge (§4C.1 shared layer)' from unnest(array[
  'accounts','menus','menu_sections','menu_items','menu_item_brands','menu_item_tags','menu_item_cocktail_core',
  'menu_headers','menu_header_tags','cocktail_reference','cocktail_specs','cocktail_spec_components','cocktail_spec_terms',
  'cocktail_tag_dimensions','cocktail_tag_terms','cocktail_tag_values','brands','brand_lines','brand_products',
  'brand_category_links','brand_producer_links','products','product_category_links','organizations','production_sites',
  'cola_label_approvals','beverage_categories','legal_designations','designation_category_links','geographies',
  'city_county_map','phg_census_zcta','geography_demographics','venue_concepts','spirit_lexicon',
  'v_public_venues','v_public_drinks','v_menu_brand_presence','v_brand_geography_presence','v_cocktail_items_filterable',
  'mv_drink_explorer','mv_menu_dev_venue_profile'
]) t
on conflict (schema_name, table_pattern) do nothing;

insert into phg.harmony_table_access (schema_name, table_pattern, access, notes)
select s, t, 'shared_read', 'knowledge / admin skeleton' from (values
  ('phg','capabilities'),('phg','units'),('phg','expense_categories'),('phg','harmony_entities'),('phg','harmony_entity_fields'),
  ('phg','harmony_paths'),('phg_design','principles'),('phg_design','concepts'),('phg_design','decision_rules'),
  ('phg_flavor','pairing_assertions'),('phg_flavor','pairing_members'),('phg_flavor','subjects')
) v(s, t)
on conflict (schema_name, table_pattern) do nothing;

-- project_read: house data. scope_expr is evaluated as the reader role; helper functions are defined below.
insert into phg.harmony_table_access (schema_name, table_pattern, access, account_column, scope_kind, scope_expr, denied_columns, required_roles, notes) values
  ('phg','accounts',             'project_read', 'id',         'custom',       'id = phg.harmony_scope_account()', '{metadata}', '{}', 'the project row itself; metadata excluded (holds auth_bootstrap / allow_first_owner_claim)'),
  ('phg','menu_projects',        'project_read', 'account_id', 'account_id',   'account_id = phg.harmony_scope_account()', '{editor_token_hash}', '{}', 'house menus'),
  ('phg','menu_items',           'project_read', null,         'menu_project', 'menu_project_id in (select phg.harmony_scope_menu_projects())', '{}', '{}', 'house menu items'),
  ('phg','recipe_projects',      'project_read', null,         'custom',       'id in (select mi.recipe_project_id from phg.harmony_scope_menu_items() mi)', '{}', '{}', 'TEMPORARY scope via menu_items until 04 backfills account_id; unlinked recipes are invisible'),
  ('phg','recipe_versions',      'project_read', null,         'custom',       'project_id in (select mi.recipe_project_id from phg.harmony_scope_menu_items() mi)', '{}', '{}', 'TEMPORARY, see recipe_projects'),
  ('phg','recipe_components',    'project_read', null,         'custom',       'recipe_version_id in (select v.id from phg.harmony_scope_recipe_versions() v)', '{}', '{}', 'via recipe_versions'),
  ('phg','recipe_cost_snapshots','project_read', null,         'custom',       'menu_item_id in (select mi.id from phg.harmony_scope_menu_items() mi)', '{}', '{}', 'via menu_items'),
  ('phg','menu_item_prices',     'project_read', null,         'location_id',  'location_id in (select phg.harmony_scope_location_ids())', '{}', '{}', 'NOTE: rows with null location_id are hidden'),
  ('phg','budget_plans',         'project_read', 'account_id', 'account_id',   'account_id = phg.harmony_scope_account()', '{}', '{}', null),
  ('phg','reporting_periods',    'project_read', 'account_id', 'account_id',   'account_id = phg.harmony_scope_account()', '{}', '{}', null),
  ('phg','financial_rules',      'project_read', 'account_id', 'account_id',   'account_id = phg.harmony_scope_account()', '{}', '{}', null),
  ('phg','sales_locations',      'project_read', 'account_id', 'account_id',   'account_id = phg.harmony_scope_account()', '{}', '{}', null),
  ('phg','sales_daily',          'project_read', null,         'location_id',  'location_id in (select phg.harmony_scope_location_ids())', '{}', '{}', 'POS daily'),
  ('phg','sales_items',          'project_read', null,         'location_id',  'location_id in (select phg.harmony_scope_location_ids())', '{}', '{}', 'POS item mix'),
  ('phg','sales_imports',        'project_read', null,         'location_id',  'location_id in (select phg.harmony_scope_location_ids())', '{}', '{}', null),
  ('phg','operating_expenses',   'project_read', null,         'location_key', 'location_key in (select phg.harmony_scope_location_keys())', '{}', '{owner,admin,analyst}', 'expenses'),
  ('phg','purchase_invoices',    'project_read', null,         'location_key', 'location_key in (select phg.harmony_scope_location_keys())', '{}', '{}', null),
  ('phg','purchase_costs',       'project_read', null,         'location_key', 'location_key in (select phg.harmony_scope_location_keys())', '{}', '{}', 'NOTE: rows with null location_key are hidden'),
  ('phg','labor_shifts',         'project_read', null,         'location_key', 'location_key in (select phg.harmony_scope_location_keys())', '{}', '{owner,admin,analyst}', 'labor (pay-adjacent)'),
  ('phg','labor_pay_rates',      'project_read', null,         'location_key', 'location_key in (select phg.harmony_scope_location_keys())', '{}', '{owner,admin}', 'pay: owner/admin only'),
  ('phg','inventory_counts',     'project_read', null,         'location_key', 'location_key in (select phg.harmony_scope_location_keys())', '{}', '{}', null),
  ('phg','pl_snapshots',         'project_read', null,         'menu_project', 'menu_project_id in (select phg.harmony_scope_menu_projects())', '{}', '{owner,admin,analyst}', null),
  ('phg','management_alert_states','project_read', null,       'menu_project', 'menu_project_id in (select phg.harmony_scope_menu_projects())', '{}', '{}', null),
  ('phg','menu_engineering_snapshots','project_read', null,    'menu_project', 'menu_project_id in (select phg.harmony_scope_menu_projects())', '{}', '{}', null),
  ('phg','harmony_notes',        'project_read', 'account_id', 'custom',       'account_id = phg.harmony_scope_account() and user_id = phg.harmony_scope_user()', '{}', '{}', 'person layer: only the asker''s notes')
on conflict (schema_name, table_pattern) do nothing;
-- NOT seeded (open question for Rob): phg.ingredients, phg.prep_recipes, phg.vendors, phg.procurement_catalog_items,
-- phg.labor_employees. They have no account column at all today, so they cannot be project_read without 04's columns.

-- ---------------------------------------------------------------------------------------------------------------
-- 3. Seed: entities (§4.1) — main tables verified to exist on 2026-09-28
-- ---------------------------------------------------------------------------------------------------------------
insert into phg.harmony_entities (key, label, entity_group, aliases, main_tables, scope, name_lookup) values
  ('venue','venue','Market','{bar,restaurant,spot,place}','{public.accounts}','shared','{"table":"public.accounts","id":"id","name":"account_name","narrow_by":["city","state","account_types"]}'),
  ('library_menu','menu','Market','{menu}','{public.menus}','shared','{"table":"public.menus","id":"id","name":"menu_title","default_filter":"is_current"}'),
  ('menu_section','menu section','Market','{section}','{public.menu_sections}','shared','{"table":"public.menu_sections","id":"id","name":"section_name"}'),
  ('library_menu_item','menu item','Market','{drink,item,dish}','{public.menu_items}','shared','{"table":"public.menu_items","id":"id","name":"item_name"}'),
  ('cocktail','cocktail','Market','{drink,classic}','{public.cocktail_specs,public.cocktail_reference,public.menu_item_cocktail_core}','shared','{"table":"public.cocktail_reference","id":"id","name":"cocktail_name","aliases":"aliases"}'),
  ('state','state','Place','{}','{public.geographies}','shared','{"table":"public.geographies","id":"id","name":"geography_name","where":"geo_type = ''state''"}'),
  ('city','city','Place','{town}','{public.geographies,public.city_county_map}','shared','{"table":"public.geographies","id":"id","name":"geography_name","where":"geo_type = ''city''"}'),
  ('zip','ZIP code','Place','{zip,zcta,postcode}','{public.phg_census_zcta}','shared','{"table":"public.phg_census_zcta","id":"zcta","name":"zcta","match":"exact"}'),
  ('brand','brand','Spirits','{label,marca}','{public.brands}','shared','{"table":"public.brands","id":"id","name":"brand_name","aliases":"aliases"}'),
  ('product','product','Spirits','{expression,bottle,sku}','{public.products}','shared','{"table":"public.products","id":"id","name":"product_name"}'),
  ('producer','producer','Spirits','{distillery company,organization}','{public.organizations}','shared','{"table":"public.organizations","id":"id","name":"organization_name"}'),
  ('distillery','distillery','Spirits','{NOM,production site,plant}','{public.production_sites}','shared','{"table":"public.production_sites","id":"id","name":"site_name","code":"registry_code"}'),
  ('cola','label approval','Spirits','{COLA,TTB label}','{public.cola_label_approvals}','shared','{"table":"public.cola_label_approvals","id":"ttb_id","name":"fanciful_name"}'),
  ('category','category','Spirits','{type,spirit category}','{public.beverage_categories}','shared','{}'),
  ('designation','designation','Spirits','{DO,appellation}','{public.legal_designations}','shared','{}'),
  ('house_menu','house menu','House work','{our menu,my menu}','{phg.menu_projects}','project','{"table":"phg.menu_projects","id":"id","name":"name"}'),
  ('house_menu_item','house menu item','House work','{our drink,menu item}','{phg.menu_items}','project','{"table":"phg.menu_items","id":"id","name":"name"}'),
  ('recipe','recipe','House work','{spec,house recipe,build}','{phg.recipe_projects,phg.recipe_versions}','project','{"table":"phg.recipe_projects","id":"id","name":"name"}'),
  ('recipe_version','recipe version','House work','{version}','{phg.recipe_versions}','project','{"table":"phg.recipe_versions","id":"id","name":"coalesce(recipe_name,cocktail_name)"}'),
  ('prep_recipe','prep recipe','House work','{syrup,brine,batch,cordial,infusion,shrub}','{phg.prep_recipes,phg.prep_recipe_versions,phg.prep_components}','project','{"table":"phg.prep_recipes","id":"id","name":"name"}'),
  ('ingredient','ingredient','House work','{}','{phg.ingredients}','project','{"table":"phg.ingredients","id":"id","name":"name","aliases":"aliases"}'),
  ('unit','unit','House work','{measure}','{phg.units}','shared','{"table":"phg.units","id":"code","name":"label","aliases":"aliases"}'),
  ('vendor','vendor','Buying and cost','{distributor,supplier}','{phg.vendors}','project','{"table":"phg.vendors","id":"id","name":"name"}'),
  ('catalog_item','catalog item','Buying and cost','{vendor item}','{phg.procurement_catalog_items}','project','{}'),
  ('purchase_cost','purchase cost','Buying and cost','{price paid,cost}','{phg.purchase_costs}','project','{}'),
  ('invoice','invoice','Buying and cost','{bill}','{phg.purchase_invoices,phg.purchase_invoice_lines}','project','{}'),
  ('recipe_cost','recipe cost','Buying and cost','{pour cost,COGS}','{phg.recipe_cost_snapshots}','project','{}'),
  ('sales','sales','Operations','{POS,revenue}','{phg.sales_daily,phg.sales_items}','project','{}'),
  ('labor','labor','Operations','{payroll,hours,shifts}','{phg.labor_shifts,phg.labor_employees,phg.labor_roles}','project','{}'),
  ('expense','expense','Operations','{spend,cost}','{phg.operating_expenses}','project','{}'),
  ('budget','budget','Operations','{declining budget}','{phg.budget_plans}','project','{}'),
  ('pl','P&L','Operations','{profit and loss,income statement}','{phg.pl_snapshots}','project','{}'),
  ('training_package','training package','Knowledge','{training}','{phg.training_packages}','project','{}'),
  ('note','note','Organising','{idea,reminder,task}','{phg.harmony_notes}','project','{}')
on conflict (key) do nothing;

-- paths (§4.2). verified_at stays NULL until the path test runs; the first two joins were checked column-by-column.
insert into phg.harmony_paths (path_key, from_entity, to_entity, description, join_spec, verified_note) values
  ('venue_current_menu_items','venue','library_menu_item','venue -> current menus -> sections -> items',
   '[{"from":"public.accounts.account_id","to":"public.menus.account_id","filter":"public.menus.is_current"},
     {"from":"public.menus.id","to":"public.menu_sections.menu_id"},
     {"from":"public.menu_sections.id","to":"public.menu_items.section_id"}]',
   'columns exist; accounts.account_id and menus.account_id are both text'),
  ('venue_city','venue','city','venue -> geography (city)',
   '[{"from":"public.accounts.geography_id","to":"public.geographies.id"}]', 'columns exist; geo_type level not yet confirmed'),
  ('menu_item_brand','library_menu_item','brand','menu item -> menu_item_brands -> brand',
   '[{"from":"public.menu_items.id","to":"public.menu_item_brands.menu_item_id"},{"from":"public.menu_item_brands.brand_id","to":"public.brands.id"}]', null),
  ('brand_distillery','brand','distillery','brand.primary_nom -> production_sites.registry_code',
   '[{"from":"public.brands.primary_nom","to":"public.production_sites.registry_code"}]', 'UNVERIFIED: registry_code format vs primary_nom'),
  ('brand_cola','brand','cola','brand -> label approvals',
   '[{"from":"public.brands.id","to":"public.cola_label_approvals.brand_id"}]', null),
  ('menu_item_cocktail','library_menu_item','cocktail','menu item -> cocktail identity',
   '[{"note":"menu_item_cocktail_core is keyed by staging_menu_extract_id, not menu_items.id; path must be confirmed"}]', 'UNVERIFIED'),
  ('house_item_recipe_cost','house_menu_item','recipe_cost','house menu item -> current recipe version -> components -> ingredient/prep -> catalog item -> latest purchase cost',
   '[{"from":"phg.menu_items.current_recipe_version_id","to":"phg.recipe_versions.id"},
     {"from":"phg.recipe_versions.id","to":"phg.recipe_components.recipe_version_id"},
     {"from":"phg.recipe_components.ingredient_id","to":"phg.procurement_catalog_items.ingredient_id"},
     {"from":"phg.procurement_catalog_items.id","to":"phg.purchase_costs.procurement_item_id","pick":"latest effective_from"}]',
   'prefer public.phg_recipe_cost(recipe_version_id, date) for the number itself')
on conflict (path_key) do nothing;

-- ---------------------------------------------------------------------------------------------------------------
-- 4. Scope helpers (read by RLS policies). SECURITY DEFINER so the reader needs no grant on the tables they read.
--    PARALLEL RESTRICTED: pg_backend_pid() must be evaluated in the leader, never a parallel worker.
-- ---------------------------------------------------------------------------------------------------------------
create or replace function phg.harmony_scope_account() returns uuid
language sql stable security definer parallel restricted set search_path = phg, pg_temp as $$
  select account_id from phg.harmony_query_scope
   where backend_pid = pg_backend_pid() and xact_id = pg_current_xact_id_if_assigned()
$$;
create or replace function phg.harmony_scope_user() returns uuid
language sql stable security definer parallel restricted set search_path = phg, pg_temp as $$
  select user_id from phg.harmony_query_scope
   where backend_pid = pg_backend_pid() and xact_id = pg_current_xact_id_if_assigned()
$$;
create or replace function phg.harmony_scope_menu_projects() returns setof uuid
language sql stable security definer parallel restricted set search_path = phg, pg_temp as $$
  select id from phg.menu_projects where account_id = phg.harmony_scope_account()
$$;
create or replace function phg.harmony_scope_menu_items() returns table (id uuid, recipe_project_id uuid)
language sql stable security definer parallel restricted set search_path = phg, pg_temp as $$
  select mi.id, mi.recipe_project_id from phg.menu_items mi
   where mi.menu_project_id in (select id from phg.menu_projects where account_id = phg.harmony_scope_account())
$$;
create or replace function phg.harmony_scope_recipe_versions() returns table (id uuid)
language sql stable security definer parallel restricted set search_path = phg, pg_temp as $$
  select v.id from phg.recipe_versions v
   where v.project_id in (select mi.recipe_project_id from phg.harmony_scope_menu_items() mi)
$$;
create or replace function phg.harmony_scope_location_ids() returns setof uuid
language sql stable security definer parallel restricted set search_path = phg, pg_temp as $$
  select id from phg.sales_locations where account_id = phg.harmony_scope_account()
$$;
create or replace function phg.harmony_scope_location_keys() returns setof text
language sql stable security definer parallel restricted set search_path = phg, pg_temp as $$
  select external_location_key from phg.sales_locations
   where account_id = phg.harmony_scope_account() and external_location_key is not null
$$;

-- whitelist lookup: 'never' (exact or pattern) wins; otherwise the exact row; otherwise null (= refused)
create or replace function phg.harmony_table_rule(p_schema text, p_table text)
returns phg.harmony_table_access
language sql stable security definer set search_path = phg, pg_temp as $$
  select a.* from phg.harmony_table_access a
   where a.schema_name = p_schema
     and ((not a.is_pattern and a.table_pattern = p_table) or (a.is_pattern and p_table like a.table_pattern))
   order by (a.access = 'never') desc, a.is_pattern asc
   limit 1
$$;

-- ---------------------------------------------------------------------------------------------------------------
-- 5. The low-privilege role (VERIFY: postgres may create roles on this project — it did for phg_menu_designer)
-- ---------------------------------------------------------------------------------------------------------------
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'phg_harmony_reader') then
    create role phg_harmony_reader nologin noinherit nobypassrls;
  end if;
end $$;
grant phg_harmony_reader to postgres;          -- lets postgres assign function ownership below (same as designer)
grant usage on schema public, phg to phg_harmony_reader;
grant usage on schema phg_design, phg_flavor to phg_harmony_reader;
grant execute on function phg.harmony_scope_account(), phg.harmony_scope_user(), phg.harmony_scope_menu_projects(),
  phg.harmony_scope_menu_items(), phg.harmony_scope_recipe_versions(), phg.harmony_scope_location_ids(),
  phg.harmony_scope_location_keys() to phg_harmony_reader;
revoke all on function phg.harmony_scope_account(), phg.harmony_scope_user(), phg.harmony_scope_menu_projects(),
  phg.harmony_scope_menu_items(), phg.harmony_scope_recipe_versions(), phg.harmony_scope_location_ids(),
  phg.harmony_scope_location_keys(), phg.harmony_table_rule(text, text) from public, anon, authenticated;

-- grants + RLS for every whitelisted table. project_read tables get RLS (if off) and a scoped policy;
-- where RLS is newly enabled and phg_menu_designer can read the table, it gets a permissive policy so nothing changes for it.
-- A function (not a DO block) so later drafts (02, 03, 05) can register their own tables and call it again. Idempotent.
-- NOTE: existing harmony_read / harmony_scope policies are NOT replaced when scope_expr changes; drop BOTH policies
-- first (dropping only one leaves the old expression in force: permissive OR-ed, restrictive AND-ed), e.g. after 04's
-- backfill, when recipe_projects moves to 'account_id = phg.harmony_scope_account()'.
create or replace function phg.harmony_apply_table_access()
returns int language plpgsql volatile security definer set search_path = phg, pg_temp as $$
declare r record; v_oid oid; v_cols text; v_n int := 0;
begin
  for r in select * from phg.harmony_table_access where access in ('shared_read','project_read') and not is_pattern loop
    v_oid := to_regclass(format('%I.%I', r.schema_name, r.table_pattern));
    continue when v_oid is null;
    v_n := v_n + 1;
    if cardinality(r.denied_columns) > 0 then
      select string_agg(quote_ident(attname), ', ' order by attnum) into v_cols from pg_attribute
       where attrelid = v_oid and attnum > 0 and not attisdropped and attname <> all (r.denied_columns);
      execute format('grant select (%s) on %s to phg_harmony_reader', v_cols, v_oid::regclass);
    else
      execute format('grant select on %s to phg_harmony_reader', v_oid::regclass);
    end if;

    if r.access = 'project_read' then
      -- permissive policies are OR-ed: refuse if any foreign policy could reach the reader (TO public or TO reader)
      if exists (select 1 from pg_policy p
                  where p.polrelid = v_oid and p.polname not in ('harmony_read','harmony_scope')
                    and (0::oid = any (p.polroles)
                         or (select oid from pg_roles where rolname = 'phg_harmony_reader') = any (p.polroles))) then
        raise exception 'harmony: %.% has a pre-existing policy for PUBLIC or phg_harmony_reader; resolve before granting',
          r.schema_name, r.table_pattern;
      end if;
      if not (select relrowsecurity from pg_class where oid = v_oid) then
        execute format('alter table %s enable row level security', v_oid::regclass);
        update phg.harmony_table_access set rls_enabled_by_migration = true where id = r.id;
        -- has_any_column_privilege: phg_menu_designer holds a COLUMN-level grant on menu_projects (has_table_privilege = false)
        if has_any_column_privilege('phg_menu_designer', v_oid, 'select')
           and not exists (select 1 from pg_policy where polrelid = v_oid and polname in ('menu_designer_read','menu_designer_read_h')) then
          execute format('create policy menu_designer_read_h on %s for select to phg_menu_designer using (true)', v_oid::regclass);
        end if;
      end if;
      if not exists (select 1 from pg_policy where polrelid = v_oid and polname = 'harmony_read') then
        execute format('create policy harmony_read on %s for select to phg_harmony_reader using (%s)', v_oid::regclass, r.scope_expr);
      end if;
      if not exists (select 1 from pg_policy where polrelid = v_oid and polname = 'harmony_scope') then
        execute format('create policy harmony_scope on %s as restrictive for select to phg_harmony_reader using (%s)',
                       v_oid::regclass, r.scope_expr);
      end if;
    elsif (select relrowsecurity from pg_class where oid = v_oid)
          and not exists (select 1 from pg_policy where polrelid = v_oid and polname = 'harmony_read') then
      execute format('create policy harmony_read on %s for select to phg_harmony_reader using (true)', v_oid::regclass);
    end if;
  end loop;
  return v_n;
end $$;
revoke all on function phg.harmony_apply_table_access() from public, anon, authenticated, service_role;

-- Pre-RLS check: list every non-owner, non-BYPASSRLS role that can SELECT a project_read table today, read straight
-- from the ACLs (table relacl + column attacl, PUBLIC included) plus members of pg_read_all_data. Those roles see ZERO
-- rows once RLS is on unless a policy covers them. phg_menu_designer is covered by menu_designer_read_h; any other
-- name in this NOTICE must be reviewed before approving.
-- Read-only run on 2026-09-29: only phg_menu_designer (table ACL on 9 tables + column ACL on menu_projects); the other
-- grantees (service_role) and pg_read_all_data members (postgres, supabase_admin, supabase_read_only_user,
-- supabase_etl_admin) are all BYPASSRLS.
do $$
declare v text; v_oids oid[];
begin
  select array_agg(to_regclass(format('%I.%I', schema_name, table_pattern))) into v_oids
    from phg.harmony_table_access where access = 'project_read' and not is_pattern
     and to_regclass(format('%I.%I', schema_name, table_pattern)) is not null;
  with g as (
    select a.grantee, c.oid::regclass::text t from pg_class c, aclexplode(c.relacl) a
     where c.oid = any (v_oids) and a.privilege_type = 'SELECT' and a.grantee <> c.relowner
    union
    select a.grantee, c.oid::regclass::text || ' (columns)' from pg_attribute at join pg_class c on c.oid = at.attrelid,
           aclexplode(at.attacl) a
     where at.attrelid = any (v_oids) and a.privilege_type = 'SELECT' and a.grantee <> c.relowner
  )
  select string_agg(x, ', ') into v from (
    select distinct case when g.grantee = 0 then 'PUBLIC' else g.grantee::regrole::text end || ' -> ' || g.t x
      from g left join pg_roles r on r.oid = g.grantee
     where g.grantee = 0 or (not r.rolbypassrls and r.rolname <> 'phg_harmony_reader')
    union
    select rolname || ' -> ALL (pg_read_all_data)' from pg_roles
     where pg_has_role(oid, 'pg_read_all_data', 'member') and not rolbypassrls and rolname <> 'pg_read_all_data'
  ) s;
  raise notice 'harmony pre-RLS check: non-owner, non-BYPASSRLS roles with SELECT on project_read tables: %', coalesce(v, '(none)');
end $$;

select phg.harmony_apply_table_access();

-- ---------------------------------------------------------------------------------------------------------------
-- 6. Inner runner + planner, OWNED BY the reader role (cannot switch role inside SECURITY DEFINER)
-- ---------------------------------------------------------------------------------------------------------------
create schema if not exists phg_harmony_q;
revoke all on schema phg_harmony_q from public;
grant usage on schema phg_harmony_q to phg_harmony_reader, postgres;

create or replace function phg_harmony_q.plan(p_sql text)
returns json language plpgsql security definer set search_path = pg_catalog, pg_temp as $$
declare v json;
begin
  execute 'explain (verbose, format json) ' || p_sql into v;
  return v;
end $$;

create or replace function phg_harmony_q.run(p_sql text, p_limit int)
returns jsonb language plpgsql security definer set search_path = pg_catalog, pg_temp as $$
declare v jsonb;
begin
  execute format('select coalesce(jsonb_agg(q), ''[]''::jsonb) from (select * from (%s) s limit %s) q', p_sql, p_limit) into v;
  return v;
end $$;

grant create on schema phg_harmony_q to phg_harmony_reader;
alter function phg_harmony_q.plan(text) owner to phg_harmony_reader;
alter function phg_harmony_q.run(text, int) owner to phg_harmony_reader;
revoke create on schema phg_harmony_q from phg_harmony_reader;
revoke all on function phg_harmony_q.plan(text), phg_harmony_q.run(text, int) from public, anon, authenticated;
grant execute on function phg_harmony_q.plan(text), phg_harmony_q.run(text, int) to postgres;

-- ---------------------------------------------------------------------------------------------------------------
-- 7. The gateway
-- ---------------------------------------------------------------------------------------------------------------
create or replace function public.phg_harmony_query(p_account uuid, p_user uuid, p_sql text, p_max_rows int default 200)
returns jsonb
language plpgsql
volatile
security definer
set search_path = phg, pg_temp
as $$
declare
  v_role   text;
  v_sql    text;
  v_plan   json;
  v_rel    record;
  v_rule   phg.harmony_table_access;
  v_tables text[] := '{}';
  v_log    bigint;
  v_rows   jsonb;
  v_t0     timestamptz := clock_timestamp();
  v_reject text;
begin
  if p_account is null or p_user is null then raise exception 'account and user required'; end if;
  -- stale scope rows (crashed/aborted callers); must run while the transaction is still read-write
  delete from phg.harmony_query_scope where ctid in (select ctid from phg.harmony_query_scope
                                                     where created_at < now() - interval '10 minutes' for update skip locked);
  select role into v_role from phg.account_memberships
   where account_id = p_account and user_id = p_user and status = 'active';
  if v_role is null then raise exception 'not a member of that account'; end if;

  v_sql := regexp_replace(coalesce(p_sql, ''), ';\s*$', '');
  if btrim(v_sql) = '' then v_reject := 'sql required';
  elsif v_sql ~ ';' then v_reject := 'one statement only';
  elsif v_sql ~ '(--|/\*)' then v_reject := 'comments not allowed';
  elsif v_sql !~* '^\s*(select|with)\M' then v_reject := 'select only';
  -- same denylist as the designer gateway, plus catalog-introspection and definer-reaching patterns
  elsif v_sql ~* '(pg_advisory|pg_try_advisory|set_config|current_setting|pg_notify|pg_sleep|pg_terminate|pg_cancel|pg_reload|pg_signal|\mlo_|dblink|pg_read|pg_read_file|pg_ls_|pg_ls_dir|pg_stat_file|pg_stat_get|pg_show_all_settings|pg_get_viewdef|obj_description|txid_|pg_current_xact|pg_backend_pid|pg_logical|_to_xml|to_xmlschema|ts_stat|ts_rewrite|\mxmltable|\mu&|\muescape|pg_get_functiondef|\mharmony_scope)' then
    v_reject := 'function not allowed';
  -- ALLOWLIST: the only schema a qualified function call may name is pg_catalog; OPERATOR(...) syntax is refused.
  -- (schema-qualified TABLES such as public.accounts are fine: they are not followed by "(")
  elsif regexp_replace(v_sql, '(\mpg_catalog|"pg_catalog")\s*\.', '', 'gi') ~* '(\w+|"[^"]+")\s*\.\s*(\w+|"[^"]+")\s*\(|\moperator\s*\(' then
    v_reject := 'schema-qualified function calls (other than pg_catalog) and OPERATOR() are not allowed; use a capability';
  elsif v_sql ~* '\m(auth|vault|storage|cron|net|internal_secrets|user_sessions|harmony_device_keys)\M' then
    v_reject := 'table not allowed';
  end if;

  insert into phg.harmony_query_log (account_id, user_id, sql, rejected)
  values (p_account, p_user, left(coalesce(p_sql, ''), 20000), v_reject)
  returning id into v_log;
  if v_reject is not null then
    return jsonb_build_object('error', v_reject, 'log_id', v_log);
  end if;

  -- scope row for RLS; must be written before the transaction turns read-only
  insert into phg.harmony_query_scope (backend_pid, xact_id, account_id, user_id)
  values (pg_backend_pid(), pg_current_xact_id(), p_account, p_user)
  on conflict (backend_pid, xact_id) do update
    set account_id = excluded.account_id, user_id = excluded.user_id, created_at = now();

  -- harmless but NOT a bound on this call (see header risk 6): the caller must enforce the timeout
  set local statement_timeout = '10s';
  set local max_parallel_workers_per_gather = 0;
  set local transaction_read_only = on;

  -- plan as the reader role and check every relation the plan touches
  begin
    v_plan := phg_harmony_q.plan(v_sql);
  exception when others then
    perform pg_advisory_unlock_all();
    return jsonb_build_object('error', 'query failed to plan: ' || sqlerrm, 'log_id', v_log);
  end;

  for v_rel in
    with recursive n(node) as (
      select (v_plan::jsonb -> 0 -> 'Plan')
      union all
      select c from n, jsonb_array_elements(coalesce(n.node -> 'Plans', '[]'::jsonb)) c
    )
    select distinct node ->> 'Schema' s, node ->> 'Relation Name' t from n where node ? 'Relation Name'
  loop
    v_rule := phg.harmony_table_rule(v_rel.s, v_rel.t);
    v_tables := v_tables || (v_rel.s || '.' || v_rel.t);
    if v_rule.id is null then
      return jsonb_build_object('error', format('table %s.%s is not in the Harmony map', v_rel.s, v_rel.t), 'log_id', v_log, 'tables', v_tables);
    elsif v_rule.access = 'never' then
      return jsonb_build_object('error', format('table %s.%s is never readable', v_rel.s, v_rel.t), 'log_id', v_log, 'tables', v_tables);
    elsif cardinality(v_rule.required_roles) > 0 and v_role <> all (v_rule.required_roles) then
      return jsonb_build_object('error', format('your role (%s) cannot read %s.%s', v_role, v_rel.s, v_rel.t), 'log_id', v_log, 'tables', v_tables);
    end if;
  end loop;

  -- function scans (FROM f(...)) must be harmless set-returning built-ins; this also stops catalog views that are
  -- pure function scans (pg_settings -> pg_show_all_settings) from slipping past the relation check
  for v_rel in
    with recursive n(node) as (
      select (v_plan::jsonb -> 0 -> 'Plan')
      union all
      select c from n, jsonb_array_elements(coalesce(n.node -> 'Plans', '[]'::jsonb)) c
    )
    select distinct node ->> 'Schema' s, node ->> 'Function Name' t from n where node ? 'Function Name'
  loop
    if not (coalesce(v_rel.s, 'pg_catalog') = 'pg_catalog'
            and v_rel.t in ('generate_series','unnest','jsonb_array_elements','jsonb_array_elements_text','jsonb_each',
                            'jsonb_each_text','json_array_elements','regexp_matches','regexp_split_to_table','string_to_table',
                            'jsonb_to_recordset','jsonb_populate_recordset')) then
      return jsonb_build_object('error', format('function %s is not allowed in FROM', v_rel.t), 'log_id', v_log, 'tables', v_tables);
    end if;
  end loop;

  begin
    v_rows := phg_harmony_q.run(v_sql, least(greatest(coalesce(p_max_rows, 200), 1), 2000));
  exception when others then
    perform pg_advisory_unlock_all();
    return jsonb_build_object('error', 'query failed: ' || sqlerrm, 'log_id', v_log, 'tables', v_tables);
  end;
  perform pg_advisory_unlock_all();

  if pg_column_size(v_rows) > 5000000 then
    return jsonb_build_object('error', 'result too large (over 5 MB); narrow the query or aggregate', 'log_id', v_log,
                              'tables', v_tables);
  end if;

  -- the transaction is read-only now: the caller records row_count/ms via phg_harmony_query_finish in a new call
  return jsonb_build_object('rows', v_rows, 'row_count', jsonb_array_length(v_rows), 'log_id', v_log, 'tables', v_tables,
                            'ms', (extract(epoch from clock_timestamp() - v_t0) * 1000)::int);
end;
$$;
revoke all on function public.phg_harmony_query(uuid, uuid, text, int) from public, anon, authenticated;
grant execute on function public.phg_harmony_query(uuid, uuid, text, int) to service_role;

create or replace function public.phg_harmony_query_finish(p_log_id bigint, p_row_count int, p_ms int, p_error text default null)
returns void language sql volatile security definer set search_path = phg, pg_temp as $$
  update phg.harmony_query_log set row_count = p_row_count, ms = p_ms, error = left(p_error, 2000)
   where id = p_log_id and row_count is null and ms is null;
  delete from phg.harmony_query_scope where ctid in (select ctid from phg.harmony_query_scope
                                                     where created_at < now() - interval '10 minutes' for update skip locked);
$$;
revoke all on function public.phg_harmony_query_finish(bigint, int, int, text) from public, anon, authenticated;
grant execute on function public.phg_harmony_query_finish(bigint, int, int, text) to service_role;
