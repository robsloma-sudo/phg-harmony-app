-- DRAFT — NOT APPLIED. Needs Rob's approval. Spec: handoff/HARMONY_CONVERSATION_MODEL.md §4A.2, §4B.1, §4C.2 (PHG-FLV-006 gap)
-- Apply order: 02 -> 04 -> 03 -> 05 -> 06 (this file is SECOND: 05 needs metric_definitions, 06 needs account_id columns
--   and gl_accounts). Depends on the live knowledge map (harmony_table_access / harmony_apply_table_access).
--
-- What this does (plain English)
--   * phg.gl_accounts: chart of accounts. Rows with account_id NULL are the shared "restaurant_usar" TEMPLATE (from the
--     codes the spec names for Parkway FH); each business gets its own copy/renames later by talking (account_id set).
--   * phg.metric_definitions: every number Harmony says is a named metric, defined once (formula, source tables, unit,
--     period rules, which settings it needs). function_name is the PLANNED database function; status says whether it
--     exists yet. Existing functions that already compute parts are listed in existing_sources.
--   * Adds account_id (NULLABLE) to phg.recipe_projects and phg.recipe_versions (the §4C.2 gap), plus a trigger so new
--     versions inherit their project's account. Also adds nullable account_id to phg.ingredients and phg.prep_recipes
--     (NULL = shared PHG library) because create_ingredient / create_prep_recipe (file 06) must keep new rows in the project.
--     NOTHING is backfilled here — see "Backfill needed" below.
--
-- Live-schema facts (checked 2026-09-28)
--   * phg.recipe_projects: 5 rows, no account_id, conversation_id is NULL on all 5.
--     phg.recipe_versions: 6 rows, project_id NOT NULL -> recipe_projects.
--   * 4 of 5 projects are reachable through phg.menu_items.recipe_project_id -> phg.menu_projects.account_id; all resolve to
--     the only account, 37c239a7-9c79-478b-b224-c6c17dd92d98 ("PHG Ops Test", key phg_ops_test).
--   * 1 project (eb72e58e-806d-4d1e-be0b-8e02927a17b8, "Manhattan", its one version status 'candidate') is on no menu item.
--     It was created by an executed persist_recipe_candidate proposal whose command_session.menu_project_id is
--     ddc4bb5b-70e6-4581-8aae-1b4042cd75ef ("Bar menu"), which is also account 37c239a7...; the link is only in
--     command_action_proposals.result (JSON), not in a column.
--   * public.phg_persist_recipe_candidate(p_payload) inserts recipe_projects WITHOUT an account: after this migration new
--     projects from that path will have account_id NULL until that function is patched (follow-up, not in this draft,
--     because the brief keeps existing actions unchanged). The version trigger below cannot fill it (project has none).
--   * phg.ingredients: 6 rows, ingredient_key globally UNIQUE; phg.prep_recipes: 0 rows, prep_key globally UNIQUE
--     (replaced below by per-project uniqueness, see "UNIQUE keys").
--   * phg.expense_categories (19 rows, keys like rent_occupancy, marketing) is a different, older category list with no
--     GL codes; gl_accounts.expense_category_key lets the two be mapped later (left NULL in the seed).
--   * phg.sales_daily has gross_sales, discounts, comps, refunds, net_sales, guest_count, check_count — but NO voids column.
--     void_pct is seeded as status 'blocked_no_data'.
--
-- Backfill needed (describe only; run as a separate, approved step after checking the counts again)
--   1. recipe_projects via menu items (covers 4 of 5 today):
--        update phg.recipe_projects rp set account_id = x.account_id
--          from (select mi.recipe_project_id, min(mp.account_id::text)::uuid account_id, count(distinct mp.account_id) n
--                  from phg.menu_items mi join phg.menu_projects mp on mp.id = mi.menu_project_id
--                 where mi.recipe_project_id is not null group by 1) x
--         where rp.id = x.recipe_project_id and x.n = 1 and rp.account_id is null;
--      (a project used by menus in two accounts must NOT be auto-assigned: report it instead; none exist today)
--   2. recipe_projects created by Command Center proposals (covers eb72e58e...):
--        update phg.recipe_projects rp set account_id = mp.account_id
--          from phg.command_action_proposals p join phg.command_sessions s on s.id = p.session_id
--          join phg.menu_projects mp on mp.id = s.menu_project_id
--         where p.action_key = 'persist_recipe_candidate' and p.status = 'executed'
--           and (p.result->>'project_id')::uuid = rp.id and rp.account_id is null;
--      VERIFY first that result->>'project_id' is the key used (phg_persist_recipe_candidate returns 'project_id';
--      phg_command_persist_recipe_candidate returns that object merged with component_count/cost).
--   3. recipe_versions: update phg.recipe_versions v set account_id = rp.account_id from phg.recipe_projects rp
--        where rp.id = v.project_id and v.account_id is null;
--   4. Anything still NULL: list it for Rob; do not guess. Only when zero rows remain NULL, a later migration sets
--      NOT NULL and adds RLS policies by account.
--   5. ingredients / prep_recipes: leave NULL (= shared library) unless Rob decides the 6 existing ingredients are
--      PHG Ops Test's own.
--
--   * UNIQUE keys (read-only check 2026-09-29): ingredients_ingredient_key_key UNIQUE (ingredient_key) and
--     prep_recipes_prep_key_key UNIQUE (prep_key). No FK, dependency or ON CONFLICT clause uses either constraint.
--     This draft REPLACES them with per-project uniqueness on (coalesce(account_id, zero-uuid), key): the shared library
--     (NULL) keeps unique keys and each business gets its own key space.
--     Live functions that look a key up WITHOUT an account (they always insert account_id NULL rows):
--     phg_upsert_draft_ingredient, phg_resolve_invoice_line_new_ingredient (`where ingredient_key = ...`),
--     phg_command_recipe_candidate_prepare (lower(ingredient_key) = ...), phg_persist_generated_menu_candidates (inserts
--     prep_recipes). Once a business owns a key that also exists shared, `where ingredient_key = k` can match two rows.
--     Follow-up (not in this draft): add `and account_id is null` (or the caller's account) to those lookups.
--     06 builds project keys with an 'a<account8>_' prefix, so they do not collide with shared keys today.
--   * ON DELETE for the new account_id columns is CASCADE (documented choice): deleting a phg.accounts row deletes that
--     project's own recipe_projects / recipe_versions / ingredients / prep_recipes (shared NULL rows are never touched).
--     Every inbound FK to those four tables is RESTRICT/NO ACTION (menu_items, recipe_components, purchase_invoice_lines,
--     training_packages, inventory_counts ...), so an account delete FAILS while any of its recipes/ingredients are still
--     referenced: nothing is silently orphaned. gl_accounts.account_id is also CASCADE.
--   * Whitelist: gl_accounts = project_read (template rows + the project's own), metric_definitions = shared_read.
--
-- Rollback (scripted; run as postgres in ONE transaction, off-peak, AFTER rolling back 06, 05 and 03)
--   begin;
--   set local lock_timeout = '3s';
--   -- 1. backups
--   create table if not exists phg._rb04_gl_accounts as select * from phg.gl_accounts;
--   create table if not exists phg._rb04_metric_definitions as select * from phg.metric_definitions;
--   create table if not exists phg._rb04_owned_rows as
--     select 'recipe_projects' t, id, account_id, null::text k from phg.recipe_projects where account_id is not null
--     union all select 'recipe_versions', id, account_id, null from phg.recipe_versions where account_id is not null
--     union all select 'ingredients', id, account_id, ingredient_key from phg.ingredients where account_id is not null
--     union all select 'prep_recipes', id, account_id, prep_key from phg.prep_recipes where account_id is not null;
--   revoke all on phg._rb04_gl_accounts, phg._rb04_metric_definitions, phg._rb04_owned_rows from public, anon, authenticated;
--   -- 2. policies. Drop the reader policies on the two new tables explicitly (so step 5 can verify), then their
--   --    whitelist rows. If a LATER migration switched recipe_projects / recipe_versions scope_expr to account_id, drop
--   --    BOTH harmony_read and harmony_scope on those tables, put the menu_items-based scope_expr back in
--   --    harmony_table_access and re-run select phg.harmony_apply_table_access() BEFORE step 4 (drop column fails while a
--   --    policy references the column).
--   drop policy if exists harmony_read on phg.gl_accounts; drop policy if exists harmony_scope on phg.gl_accounts;
--   drop policy if exists harmony_read on phg.metric_definitions;
--   delete from phg.harmony_table_access where schema_name = 'phg' and table_pattern in ('gl_accounts','metric_definitions');
--   -- 3. trigger
--   drop trigger if exists recipe_versions_inherit_account on phg.recipe_versions; drop function if exists phg.recipe_versions_inherit_account();
--   -- 4. keys + columns. Restoring the global UNIQUE fails if two projects now share a key: check first with
--   --    select ingredient_key, count(*) from phg.ingredients group by 1 having count(*) > 1 (same for prep_key); rename first.
--   drop index if exists phg.ingredients_key_per_account_uq; drop index if exists phg.prep_recipes_key_per_account_uq;
--   alter table phg.ingredients  add constraint ingredients_ingredient_key_key unique (ingredient_key);
--   alter table phg.prep_recipes add constraint prep_recipes_prep_key_key unique (prep_key);
--   alter table phg.recipe_versions drop column if exists account_id;
--   alter table phg.recipe_projects drop column if exists account_id;
--   alter table phg.ingredients drop column if exists account_id;
--   alter table phg.prep_recipes drop column if exists account_id;
--   drop table if exists phg.metric_definitions, phg.gl_accounts;
--   -- 5. verify (expect: null, null, null, 0, 0, 2, 0)
--   select to_regclass('phg.gl_accounts') gl, to_regclass('phg.metric_definitions') md,
--          to_regprocedure('phg.recipe_versions_inherit_account()') trg_fn,
--          (select count(*) from information_schema.columns where table_schema = 'phg' and column_name = 'account_id'
--             and table_name in ('recipe_projects','recipe_versions','ingredients','prep_recipes')) acct_cols,
--          (select count(*) from phg.harmony_table_access where table_pattern in ('gl_accounts','metric_definitions')) access_rows,
--          (select count(*) from pg_constraint where conname in ('ingredients_ingredient_key_key','prep_recipes_prep_key_key')) global_uniques,
--          (select count(*) from pg_class where relname in ('ingredients_key_per_account_uq','prep_recipes_key_per_account_uq')) per_acct_idx;
--   commit;

begin;

set local lock_timeout = '3s';   -- ALTER TABLE on recipe_*/ingredients/prep_recipes: off-peak; on 55P03 nothing applied, retry

-- ---------------------------------------------------------------------------------------------------------------
-- Chart of accounts
-- ---------------------------------------------------------------------------------------------------------------
create table if not exists phg.gl_accounts (
  id                    uuid primary key default gen_random_uuid(),
  account_id            uuid references phg.accounts(id) on delete cascade,     -- NULL = template row
  template_key          text not null default 'restaurant_usar',
  code                  text not null,
  name                  text not null,
  parent_code           text,
  type                  text not null check (type in ('revenue','cogs','labor','operating_expense','other_income','other_expense',
                                                      'asset','liability','equity')),
  cogs_category         text check (cogs_category in ('liquor','beer','wine','na_bev','bar_mix','food','other')),
  labor_class           text check (labor_class in ('management','hourly','taxes_benefits')),
  expense_category_key  text,                                                   -- optional map to phg.expense_categories.category_key
  budget_group          text,                                                   -- declining budget group, e.g. 'bar_cost'
  sort                  int not null default 0,
  active                boolean not null default true,
  source                text not null default 'template' check (source in ('template','asked','imported')),
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);
create unique index if not exists gl_accounts_code_uq
  on phg.gl_accounts (coalesce(account_id, '00000000-0000-0000-0000-000000000000'::uuid), template_key, code);
alter table phg.gl_accounts enable row level security;
revoke all on phg.gl_accounts from public, anon, authenticated;

-- Seed: ONLY the codes the spec names (§4A.1 Invoices row, §4A.2, and the brief). Revenue (4xxx) accounts are not named in
-- the spec and are not seeded. 5420 has no named parent (5400 is not in the spec), so parent_code is NULL.
insert into phg.gl_accounts (account_id, template_key, code, name, parent_code, type, cogs_category, labor_class, budget_group, sort) values
  (null,'restaurant_usar','5100',   'Bar cost',         null,   'cogs',             null,      null,        'bar_cost',   5100),
  (null,'restaurant_usar','5100-01','Liquor',           '5100', 'cogs',             'liquor',  null,        'bar_cost',   5101),
  (null,'restaurant_usar','5100-02','Beer',             '5100', 'cogs',             'beer',    null,        'bar_cost',   5102),
  (null,'restaurant_usar','5100-03','Wine',             '5100', 'cogs',             'wine',    null,        'bar_cost',   5103),
  (null,'restaurant_usar','5200',   'Bar mix',          null,   'cogs',             'bar_mix', null,        'bar_cost',   5200),
  (null,'restaurant_usar','5420',   'N/A beverage',     null,   'cogs',             'na_bev',  null,        'bar_cost',   5420),
  (null,'restaurant_usar','6100',   'Labor',            null,   'labor',            null,      null,        'labor',      6100),
  (null,'restaurant_usar','6110',   'Management labor', '6100', 'labor',            null,      'management','labor',      6110),
  (null,'restaurant_usar','6120',   'Hourly labor',     '6100', 'labor',            null,      'hourly',    'labor',      6120),
  (null,'restaurant_usar','6200',   'Food hall',        null,   'operating_expense',null,      null,        'food_hall',  6200),
  (null,'restaurant_usar','6300',   'Facility',         null,   'operating_expense',null,      null,        'facility',   6300),
  (null,'restaurant_usar','6400',   'General and administrative', null, 'operating_expense', null, null,    'g_and_a',    6400),
  (null,'restaurant_usar','6500',   'Marketing',        null,   'operating_expense',null,      null,        'marketing',  6500),
  (null,'restaurant_usar','6540',   'Rewards',          '6500', 'operating_expense',null,      null,        'marketing',  6540)
on conflict do nothing;
-- The Airtable "Invoices" table splits amounts by more GL codes between 5100-01 and 6540; import them from Parkway FH
-- as account-level rows (source = 'imported') rather than guessing names here.

-- ---------------------------------------------------------------------------------------------------------------
-- Metric definitions
-- ---------------------------------------------------------------------------------------------------------------
create table if not exists phg.metric_definitions (
  key                text primary key,
  label              text not null,
  description        text not null,
  formula            text not null,                     -- plain words + symbols; the function is the truth
  function_name      text,                              -- planned/actual DB function computing it
  status             text not null default 'planned' check (status in ('planned','live','blocked_no_data')),
  existing_sources   text[] not null default '{}',      -- functions that already compute pieces today
  source_tables      text[] not null default '{}',
  unit               text not null check (unit in ('usd','pct','usd_per_hour','usd_per_check','count')),
  good_direction     text check (good_direction in ('up','down','target')),
  period_rules       jsonb not null default '{}'::jsonb, -- {"calendar_setting":"calendar.week_start","close_setting":"calendar.day_close_time","grains":["day","week","period","month"]}
  required_settings  text[] not null default '{}',
  target_setting     text,                              -- setting_definitions.key holding the business's target
  dimensions         text[] not null default '{}',      -- location, revenue_center, category, role, gl_group
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);
alter table phg.metric_definitions enable row level security;
revoke all on phg.metric_definitions from public, anon, authenticated;

insert into phg.metric_definitions (key, label, description, formula, function_name, status, existing_sources, source_tables, unit, good_direction, period_rules, required_settings, target_setting, dimensions) values
  ('net_sales','Net sales','Sales after discounts and comps (per the business''s definition)',
   'sum(net_sales) per the pos.net_sales_definition setting','phg.metric_net_sales','planned','{public.phg_sales_summary}',
   '{phg.sales_daily,phg.sales_locations}','usd','up','{"calendar_setting":"calendar.week_start","close_setting":"calendar.day_close_time"}',
   '{calendar.week_start,pos.net_sales_definition}',null,'{location,revenue_center}'),
  ('comp_pct','Comp %','Comps as a share of sales','sum(comps) / sum(gross_sales) * 100 (denominator follows pos.net_sales_definition)',
   'phg.metric_comp_pct','planned','{public.phg_sales_summary}','{phg.sales_daily}','pct','down','{"calendar_setting":"calendar.week_start"}',
   '{calendar.week_start,pos.net_sales_definition}','targets.comp_limit_pct','{location,revenue_center}'),
  ('discount_pct','Discount %','Discounts as a share of sales','sum(discounts) / sum(gross_sales) * 100',
   'phg.metric_discount_pct','planned','{public.phg_sales_summary}','{phg.sales_daily}','pct','down','{"calendar_setting":"calendar.week_start"}',
   '{calendar.week_start}',null,'{location,revenue_center}'),
  ('void_pct','Void %','Voids as a share of sales','sum(voids) / sum(gross_sales) * 100',
   'phg.metric_void_pct','blocked_no_data','{}','{phg.sales_daily}','pct','down','{}',
   '{calendar.week_start}',null,'{location,revenue_center}'),
  ('labor_pct','Labor %','Labor cost as a share of net sales','labor_cost / net_sales * 100 (tips included only if labor.tips_in_labor)',
   'phg.metric_labor_pct','planned','{public.phg_labor_report,public.phg_labor_shift_cost_rows,public.phg_labor_salary_accrual,public.phg_budget_labor_status}',
   '{phg.labor_shifts,phg.labor_pay_rates,phg.labor_salary_allocations,phg.sales_daily}','pct','down','{"calendar_setting":"calendar.week_start"}',
   '{calendar.week_start,labor.tips_in_labor}','targets.labor_pct','{location,revenue_center,role}'),
  ('hourly_labor_pct','Hourly labor %','Hourly (not management) labor as a share of net sales','hourly_labor_cost / net_sales * 100',
   'phg.metric_hourly_labor_pct','planned','{public.phg_labor_report}','{phg.labor_shifts,phg.labor_pay_rates,phg.sales_daily}','pct','down',
   '{"calendar_setting":"calendar.week_start"}','{calendar.week_start,labor.roles}',null,'{location,revenue_center,role}'),
  ('cogs_pct_by_category','COGS % by category','Cost of goods as a share of category sales (liquor, beer, wine, N/A ...)',
   '(beginning inventory + purchases - ending inventory) / category sales * 100, per gl_accounts.cogs_category',
   'phg.metric_cogs_pct_by_category','planned','{public.phg_cogs_category_breakdown,public.phg_sales_theoretical_cogs,public.phg_cogs_reconcile}',
   '{phg.purchase_invoices,phg.purchase_invoice_lines,phg.inventory_counts,phg.sales_items,phg.gl_accounts}','pct','down',
   '{"calendar_setting":"calendar.period_type"}','{calendar.period_type,accounting.coa_template}','targets.cogs_pct_by_category','{location,category}'),
  ('prime_cost_pct','Prime cost %','COGS plus labor as a share of net sales','(total_cogs + labor_cost) / net_sales * 100',
   'phg.metric_prime_cost_pct','planned','{public.phg_pl_statement}','{phg.sales_daily,phg.labor_shifts,phg.purchase_invoices}','pct','down',
   '{"calendar_setting":"calendar.period_type"}','{calendar.period_type}','targets.prime_cost_pct','{location}'),
  ('declining_budget_remaining','Declining budget left','Budget left to spend this week for a GL group','budget(gl_group, week) - spent_to_date(gl_group, week)',
   'phg.metric_declining_budget_remaining','planned','{public.phg_budget_status,public.phg_budget_expense_status,public.phg_budget_purchase_activity}',
   '{phg.budget_plans,phg.operating_expenses,phg.purchase_invoices,phg.gl_accounts}','usd','target','{"calendar_setting":"calendar.week_start","grains":["week"]}',
   '{calendar.week_start,targets.weekly_budgets}','targets.weekly_budgets','{location,gl_group}'),
  ('budget_variance','Budget vs actual','Actual minus budget for a period','actual - budget (and % of budget)',
   'phg.metric_budget_variance','planned','{public.phg_management_budget_variance,public.phg_pl_budget_compare}','{phg.budget_plans,phg.pl_snapshots}','usd','target',
   '{"calendar_setting":"calendar.period_type"}','{calendar.period_type}',null,'{location,gl_group}'),
  ('sales_per_labor_hour','Sales per labor hour','Net sales divided by labor hours worked','net_sales / sum(regular + overtime + doubletime hours)',
   'phg.metric_sales_per_labor_hour','planned','{public.phg_labor_report,public.phg_sales_summary}','{phg.sales_daily,phg.labor_shifts}','usd_per_hour','up',
   '{"calendar_setting":"calendar.week_start","grains":["day","daypart","week"]}','{calendar.week_start}',null,'{location,revenue_center,role}'),
  ('avg_check','Average check','Net sales per check','net_sales / check_count',
   'phg.metric_avg_check','planned','{public.phg_sales_summary}','{phg.sales_daily}','usd_per_check','up','{"calendar_setting":"calendar.week_start"}',
   '{calendar.week_start}',null,'{location,revenue_center}')
on conflict (key) do nothing;

-- ---------------------------------------------------------------------------------------------------------------
-- account_id on recipe / ingredient / prep tables (nullable; no backfill here)
-- ---------------------------------------------------------------------------------------------------------------
alter table phg.recipe_projects add column if not exists account_id uuid references phg.accounts(id) on delete cascade;
alter table phg.recipe_versions add column if not exists account_id uuid references phg.accounts(id) on delete cascade;
alter table phg.ingredients     add column if not exists account_id uuid references phg.accounts(id) on delete cascade;  -- NULL = shared library
alter table phg.prep_recipes    add column if not exists account_id uuid references phg.accounts(id) on delete cascade;  -- NULL = shared library
create index if not exists recipe_projects_account on phg.recipe_projects (account_id);
create index if not exists recipe_versions_account on phg.recipe_versions (account_id);
create index if not exists ingredients_account     on phg.ingredients (account_id);
create index if not exists prep_recipes_account    on phg.prep_recipes (account_id);
-- same name twice in one project is allowed today; the create_ingredient action checks for a close match first.

-- keys unique per project (shared library = the zero uuid), replacing the global UNIQUE constraints (names checked live)
create unique index if not exists ingredients_key_per_account_uq
  on phg.ingredients (coalesce(account_id, '00000000-0000-0000-0000-000000000000'::uuid), ingredient_key);
create unique index if not exists prep_recipes_key_per_account_uq
  on phg.prep_recipes (coalesce(account_id, '00000000-0000-0000-0000-000000000000'::uuid), prep_key);
alter table phg.ingredients  drop constraint if exists ingredients_ingredient_key_key;
alter table phg.prep_recipes drop constraint if exists prep_recipes_prep_key_key;

-- runs as its owner so the project lookup does not depend on the writer's privileges/RLS
create or replace function phg.recipe_versions_inherit_account() returns trigger
language plpgsql security definer set search_path = phg, pg_temp as $$
declare v_acct uuid;
begin
  select account_id into v_acct from phg.recipe_projects where id = new.project_id;
  if new.account_id is null then
    new.account_id := v_acct;
  elsif v_acct is not null and new.account_id <> v_acct then
    raise exception 'recipe version account differs from its project';
  end if;
  return new;
end $$;
revoke execute on function phg.recipe_versions_inherit_account() from public, anon, authenticated;
drop trigger if exists recipe_versions_inherit_account on phg.recipe_versions;
create trigger recipe_versions_inherit_account before insert or update of project_id, account_id on phg.recipe_versions
  for each row execute function phg.recipe_versions_inherit_account();

-- ---------------------------------------------------------------------------------------------------------------
-- Knowledge-map whitelist: register the two new tables, then (re)apply grants/policies for the reader role.
-- Both tables are new and revoked from public/anon/authenticated above, so no pre-RLS check is needed here.
-- ---------------------------------------------------------------------------------------------------------------
insert into phg.harmony_table_access (schema_name, table_pattern, access, account_column, scope_kind, scope_expr, notes) values
  ('phg','gl_accounts',       'project_read','account_id','custom','account_id is null or account_id = phg.harmony_scope_account()',
   'template rows (NULL) + the project''s own chart'),
  ('phg','metric_definitions','shared_read', null, null, null, 'admin-owned metric catalogue')
on conflict (schema_name, table_pattern) do nothing;
select phg.harmony_apply_table_access();

commit;
