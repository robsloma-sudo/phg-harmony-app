-- DRAFT — NOT APPLIED. Needs Rob's approval. Spec: handoff/HARMONY_CONVERSATION_MODEL.md §4A.2 (time words), §4.1-4.3, §6.3-6.4 (as revised)
-- Replaces the dropped 03_workspace_folders.sql. Rob, 2026-09-29: "NO folders. Everything built by talking to Harmony lives
-- in normal tables; people organise it with saved VIEWS and FILTERS instead."
-- Apply order: 02 -> 04 -> 03 -> 05 -> 06 (this file is THIRD: needs 02's settings/parties; reads 04's metric_definitions).
--
-- What this does (plain English)
--   * phg.period_presets: the time windows a business talks in — this week, last week, last 2 / 4 weeks, month, quarter,
--     year to date, same week last year, rolling 7 / 28 days, this/last reporting period, custom. PHG ships defaults
--     (account_id NULL); a business can add its own or override one by key. Calendar windows are anchored on the
--     business's settings from draft 02: calendar.week_start and calendar.fiscal_year_start; "period" presets use the
--     business's own phg.reporting_periods rows (which already exist and handle 4-4-5 etc.).
--   * phg.resolve_period(account, preset_key, as_of): turns a preset + date into start/end dates. The only place date
--     arithmetic for "last week" happens (spec §4D.3: numbers come from database functions).
--   * phg.saved_filters: named, reusable conditions on one kind of thing (entity from draft 01), e.g.
--     "Dairy" = ingredient.category = dairy; "Main distributors" = party.name in (...). Personal (user_id set) or shared
--     in the project (user_id NULL). Conditions are data (field/op/value), never SQL.
--   * phg.saved_views: a named way to look at something — an entity OR a set of metrics, filters, a time preset,
--     group-by, columns, sort and a display (table | bars | tiles | map | dashboard), pinnable.
--   * phg.harmony_view_spec(account, user, view_id, as_of): resolves a view into a read-only QUERY SPEC (jsonb) for the
--     draft-01 gateway. It does not build or run SQL. Unknown fields are reported in spec.errors, never guessed.
--   * public.phg_harmony_views_db(op, args): service_role reads (presets, period_resolve, filters, views, view_spec).
--     Creating/changing filters and views goes through Command Center proposals (draft 06: save_filter, save_view,
--     update_view, delete_view).
--   * Seeds harmony_entity_fields for the entities people filter most (ingredient, party, expense, invoice, invoice line,
--     sales day, house menu item, recipe) with the date axis each time preset applies to.
--
-- Query spec format (version 1) — what harmony_view_spec returns and what a spec compiler must accept
--   {
--     "spec_version": 1,
--     "view": {"id","name","display","pinned"},
--     "source": {"kind":"entity", "entity":"expense", "table":"phg.operating_expenses"}
--             | {"kind":"metrics", "metrics":[{"key","function_name","status","unit"}]},
--     "period": {"preset":"last_4_weeks","start":"2026-08-31","end":"2026-09-27","label":"Last 4 weeks",
--                "date_field":"expense_date","date_source":"expense_date"} | null,
--     "conditions": [{"field":"category","op":"eq","value":"dairy","source":"category","data_type":"text"}],
--                   (rebuilt key by key: ONLY field/op/value/source/data_type; any other key stored in a condition is dropped)
--     "group_by": [{"field","source"}], "columns": [{"field","source","label"}], "sort": [{"field","source","dir":"asc|desc"}],
--     "limit": 500,
--     "scope": {"account_id":"...","user_id":"..."},        -- the gateway re-checks membership and applies RLS anyway
--     "errors": ["unknown field 'gl_account' on expense"]   -- non-empty = do not run; ask the user or fix the view
--   }
--   Ops: eq, neq, in, not_in, gt, gte, lt, lte, between (value [a,b]), prefix (value text, e.g. '5100' for "5100%"),
--        contains (case-insensitive substring), is_null, not_null.
--   A compiler (next step, not drafted) turns this into SQL using ONLY: the table from harmony_entities.main_tables[1],
--   sources that are plain column names on that table (validated against pg_attribute), format('%I') for identifiers and
--   format('%L') for values, then sends it through public.phg_harmony_query (same whitelist, RLS, row cap, log).
--   Sources that are not plain columns (joins through harmony_paths) are marked "path:<path_key>.<column>" and the v1
--   compiler must refuse them with a clear error until paths are verified.
--
-- Time basis
--   * "today" / as_of defaults to the date in the business's time zone (setting business.time_zone, validated against
--     pg_timezone_names; UTC when unset or invalid), via phg.harmony_business_today(account).
--   * calendar.fiscal_year_start accepts 'MM-DD' or 'YYYY-MM-DD' (year ignored); the day is clamped to the month's length
--     in the year being resolved (02-29 -> 02-28 in non-leap years). Anything else returns
--     {"error": ..., "missing_setting": "calendar.fiscal_year_start"} instead of guessing.
--   * reporting-period presets filter phg.reporting_periods.period_type by the preset's period_type_filter, else by the
--     business's EXPLICITLY SET calendar.period_type (the skeleton default is not used, because saved periods carry
--     whatever type they were saved with, e.g. 'custom').
--   * One date axis per entity is now enforced: unique index harmony_entity_fields_one_date_axis (live check 2026-09-29:
--     no entity has two today).
--
-- purchase_invoice_lines (whitelisted here as project_read; RLS is OFF on it today, ACL postgres + service_role only)
--   A pre-RLS check (copied from the knowledge map, narrowed to this one table) raises a NOTICE listing any non-owner,
--   non-BYPASSRLS role that can SELECT it; any name other than '(none)' must be reviewed before approving.
--   required_roles is copied from the live purchase_invoices row (today '{}' = any active member).
--
-- Rollback (scripted; run as postgres in ONE transaction, off-peak, AFTER rolling back 06 and 05)
--   begin;
--   set local lock_timeout = '3s';
--   -- 1. backups of what people saved
--   create table if not exists phg._rb03_saved_views   as select * from phg.saved_views;
--   create table if not exists phg._rb03_saved_filters as select * from phg.saved_filters;
--   create table if not exists phg._rb03_period_presets as select * from phg.period_presets where account_id is not null;
--   revoke all on phg._rb03_saved_views, phg._rb03_saved_filters, phg._rb03_period_presets from public, anon, authenticated;
--   -- 2. functions
--   drop function if exists public.phg_harmony_views_db(text, jsonb);
--   drop function if exists phg.harmony_view_spec(uuid, uuid, uuid, date);
--   drop function if exists phg.resolve_period(uuid, text, date);
--   drop function if exists phg.harmony_business_today(uuid);
--   drop trigger if exists saved_views_validate on phg.saved_views; drop function if exists phg.saved_views_validate();
--   drop trigger if exists saved_filters_validate on phg.saved_filters; drop function if exists phg.saved_filters_validate();
--   -- 3. purchase_invoice_lines: policies, grant, whitelist row, RLS (only if THIS migration enabled it)
--   do $rb$
--   declare v_rls boolean;
--   begin
--     select rls_enabled_by_migration into v_rls from phg.harmony_table_access
--      where schema_name = 'phg' and table_pattern = 'purchase_invoice_lines';
--     drop policy if exists harmony_read on phg.purchase_invoice_lines;
--     drop policy if exists harmony_scope on phg.purchase_invoice_lines;
--     drop policy if exists menu_designer_read_h on phg.purchase_invoice_lines;
--     revoke all on phg.purchase_invoice_lines from phg_harmony_reader;
--     delete from phg.harmony_table_access where schema_name = 'phg' and table_pattern = 'purchase_invoice_lines';
--     if coalesce(v_rls, false) then alter table phg.purchase_invoice_lines disable row level security; end if;
--   end $rb$;
--   -- 4. seeded knowledge-map rows: ONLY the (entity_key, field_key) pairs this file inserted
--   delete from phg.harmony_entity_fields f using (values
--     ('ingredient','name'),('ingredient','category'),('ingredient','ingredient_type'),
--     ('party','name'),('party','kinds'),('party','delivery_days'),('party','gl_default_code'),
--     ('expense','expense_date'),('expense','description'),('expense','amount'),('expense','revenue_center'),
--     ('expense','location_key'),('expense','category'),
--     ('invoice','invoice_date'),('invoice','invoice_number'),('invoice','total'),('invoice','status'),('invoice','vendor'),
--     ('invoice_line','description'),('invoice_line','product_family'),('invoice_line','amount'),('invoice_line','invoice_date'),
--     ('sales','business_date'),('sales','revenue_center'),('sales','net_sales'),('sales','comps'),('sales','discounts'),
--     ('house_menu_item','name'),('house_menu_item','section'),('house_menu_item','status'),('house_menu_item','price'),
--     ('recipe','name'),('recipe','status'),('recipe','created_at')) x(e, k)
--    where f.entity_key = x.e and f.field_key = x.k;
--   --    (a pair that existed BEFORE this migration was skipped by ON CONFLICT DO NOTHING; check the pre-apply snapshot
--   --     select entity_key, field_key from phg.harmony_entity_fields and exclude those pairs from this list)
--   delete from phg.harmony_entities where key = 'invoice_line';
--   drop index if exists phg.harmony_entity_fields_one_date_axis;
--   -- 5. tables
--   drop table if exists phg.saved_views, phg.saved_filters, phg.period_presets;
--   drop function if exists phg.harmony_conditions_valid(jsonb);
--   -- 6. verify (expect: nulls, 0, 0, false, 0)
--   select to_regclass('phg.saved_views') sv, to_regclass('phg.saved_filters') sf, to_regclass('phg.period_presets') pp,
--          to_regprocedure('public.phg_harmony_views_db(text,jsonb)') fn, to_regclass('phg.harmony_entity_fields_one_date_axis') ix,
--          (select count(*) from pg_policy where polrelid = 'phg.purchase_invoice_lines'::regclass) pil_policies,
--          (select count(*) from phg.harmony_table_access where table_pattern = 'purchase_invoice_lines') pil_access,
--          (select relrowsecurity from pg_class where oid = 'phg.purchase_invoice_lines'::regclass) pil_rls,
--          (select count(*) from phg.harmony_entities where key = 'invoice_line') entity;
--   commit;

begin;

set local lock_timeout = '3s';   -- enables RLS on phg.purchase_invoice_lines: off-peak; on 55P03 nothing applied, retry

-- ---------------------------------------------------------------------------------------------------------------
-- 1. Period presets
-- ---------------------------------------------------------------------------------------------------------------
create table if not exists phg.period_presets (
  id                   uuid primary key default gen_random_uuid(),
  account_id           uuid references phg.accounts(id) on delete cascade,      -- NULL = PHG default for every business
  key                  text not null,                                           -- 'last_week'
  label                text not null,
  aliases              text[] not null default '{}',                            -- 'last week', 'previous week'
  kind                 text not null check (kind in ('calendar','rolling','reporting_period','custom')),
  unit                 text check (unit in ('day','week','month','quarter','year')),
  length               int not null default 1 check (length between 1 and 520),
  "offset"             int not null default 0 check ("offset" between -520 and 0),   -- in units; 0 = current, -1 = previous
  to_date              boolean not null default false,                          -- cut the window at the as-of date
  anchor               text not null default 'calendar' check (anchor in ('calendar','week_start','fiscal_year')),
  period_type_filter   text,                                                    -- kind='reporting_period': phg.reporting_periods.period_type
  custom_start         date,
  custom_end           date,
  sort                 int not null default 100,
  active               boolean not null default true,
  created_by           uuid,
  created_at           timestamptz not null default now(),
  check (kind <> 'custom' or (custom_start is not null and custom_end is not null and custom_start <= custom_end)),
  check (kind not in ('calendar','rolling') or unit is not null),
  check (kind <> 'custom' or account_id is not null)
);
create unique index if not exists period_presets_key_uq
  on phg.period_presets (coalesce(account_id, '00000000-0000-0000-0000-000000000000'::uuid), key);

insert into phg.period_presets (account_id, key, label, aliases, kind, unit, length, "offset", to_date, anchor, sort) values
  (null,'today',              'Today',               '{today}',                                  'rolling', 'day',   1,   0, false,'calendar',   10),
  (null,'yesterday',          'Yesterday',           '{yesterday,last night}',                   'rolling', 'day',   1,  -1, false,'calendar',   11),
  (null,'this_week',          'This week',           '{this week,week to date}',                 'calendar','week',  1,   0, true, 'week_start', 20),
  (null,'last_week',          'Last week',           '{last week,previous week}',                'calendar','week',  1,  -1, false,'week_start', 21),
  (null,'last_2_weeks',       'Last 2 weeks',        '{last two weeks,past two weeks}',          'calendar','week',  2,  -2, false,'week_start', 22),
  (null,'last_4_weeks',       'Last 4 weeks',        '{last four weeks,past four weeks}',        'calendar','week',  4,  -4, false,'week_start', 23),
  (null,'same_week_last_year','Same week last year', '{same week last year}',                    'calendar','week',  1, -52, false,'week_start', 24),
  (null,'rolling_7_days',     'Last 7 days',         '{last 7 days,past week}',                  'rolling', 'day',   7,   0, false,'calendar',   25),
  (null,'rolling_28_days',    'Last 28 days',        '{last 28 days}',                           'rolling', 'day',  28,   0, false,'calendar',   26),
  (null,'this_month',         'This month',          '{this month,month to date,MTD}',           'calendar','month', 1,   0, true, 'calendar',   30),
  (null,'last_month',         'Last month',          '{last month,previous month}',              'calendar','month', 1,  -1, false,'calendar',   31),
  (null,'this_quarter',       'This quarter',        '{this quarter,quarter to date,QTD}',       'calendar','quarter',1,  0, true, 'calendar',   40),
  (null,'last_quarter',       'Last quarter',        '{last quarter}',                           'calendar','quarter',1, -1, false,'calendar',   41),
  (null,'year_to_date',       'Year to date',        '{year to date,YTD,this year}',             'calendar','year',  1,   0, true, 'fiscal_year',50),
  (null,'last_year',          'Last year',           '{last year}',                              'calendar','year',  1,  -1, false,'fiscal_year',51)
on conflict do nothing;
insert into phg.period_presets (account_id, key, label, aliases, kind, "offset", to_date, sort) values
  (null,'period_to_date','Period to date','{period to date,PTD,this period}','reporting_period', 0, true, 60),
  (null,'last_period',   'Last period',   '{last period,previous period}',   'reporting_period',-1, false,61)
on conflict do nothing;

-- "today" for a business: the date in its time zone (business.time_zone, business-wide row); UTC if unset/invalid
create or replace function phg.harmony_business_today(p_account uuid)
returns date language plpgsql stable security definer set search_path = phg, pg_temp as $$
declare v_tz text;
begin
  select s.value #>> '{}' into v_tz from phg.account_settings s
   where s.account_id = p_account and s.key = 'business.time_zone' and s.scope_key = '' and s.user_id is null;
  if v_tz is null or not exists (select 1 from pg_catalog.pg_timezone_names where name = v_tz) then v_tz := 'UTC'; end if;
  return (now() at time zone v_tz)::date;
end $$;

-- start/end for a preset. Reads calendar.week_start ('monday'..'sunday'), calendar.fiscal_year_start ('MM-DD' or
-- 'YYYY-MM-DD') and calendar.period_type from phg.account_settings (draft 02, business-wide rows only); week start and
-- fiscal year fall back to the setting's default, then Monday / 01-01. p_as_of NULL = today in the business's time zone.
create or replace function phg.resolve_period(p_account uuid, p_preset_key text, p_as_of date default null)
returns jsonb language plpgsql stable security definer set search_path = phg, pg_temp as $$
declare
  v_p     phg.period_presets;
  v_as_of date := coalesce(p_as_of, phg.harmony_business_today(p_account));
  v_ws    int;           -- ISO day of week the business's week starts on (1 = Monday)
  v_fy    text;          -- raw setting
  v_fy_m  int; v_fy_d int;
  v_fy_y  int;
  v_ptype text;
  v_unit  interval;
  v_start date; v_end date; v_base date;
  v_rp    record;
begin
  select * into v_p from phg.period_presets
   where key = p_preset_key and active and (account_id = p_account or account_id is null)
   order by account_id nulls last limit 1;
  if not found then return jsonb_build_object('error', format('unknown time window %s', p_preset_key)); end if;

  select array_position(array['monday','tuesday','wednesday','thursday','friday','saturday','sunday'],
                        lower(coalesce(s.value, d.default_value) #>> '{}'))
    into v_ws
    from phg.setting_definitions d
    left join phg.account_settings s on s.key = d.key and s.account_id = p_account and s.scope_key = '' and s.user_id is null
   where d.key = 'calendar.week_start';
  v_ws := coalesce(v_ws, 1);
  select coalesce(s.value, d.default_value) #>> '{}' into v_fy
    from phg.setting_definitions d
    left join phg.account_settings s on s.key = d.key and s.account_id = p_account and s.scope_key = '' and s.user_id is null
   where d.key = 'calendar.fiscal_year_start';
  v_fy := btrim(coalesce(nullif(v_fy, ''), '01-01'));
  -- 'MM-DD' or 'YYYY-MM-DD' (year ignored); month 1-12, day 1-31, clamped to the month's length below
  if v_fy ~ '^(\d{4}-)?\d{2}-\d{2}$' then
    v_fy_m := split_part(right(v_fy, 5), '-', 1)::int;
    v_fy_d := split_part(right(v_fy, 5), '-', 2)::int;
  end if;
  if v_fy_m is null or v_fy_m not between 1 and 12 or v_fy_d not between 1 and 31 then
    return jsonb_build_object('error', format('fiscal year start %L is not a month and day (MM-DD)', v_fy),
                              'missing_setting', 'calendar.fiscal_year_start');
  end if;

  if v_p.kind = 'custom' then
    v_start := v_p.custom_start; v_end := v_p.custom_end;

  elsif v_p.kind = 'reporting_period' then
    -- preset's own filter, else the business's EXPLICITLY SET calendar.period_type (not the skeleton default)
    v_ptype := v_p.period_type_filter;
    if v_ptype is null then
      select s.value #>> '{}' into v_ptype from phg.account_settings s
       where s.account_id = p_account and s.key = 'calendar.period_type' and s.scope_key = '' and s.user_id is null;
    end if;
    select rp.start_date, rp.end_date, rp.name into v_rp from phg.reporting_periods rp
     where rp.account_id = p_account and rp.active and rp.start_date <= v_as_of
       and (v_ptype is null or rp.period_type = v_ptype)
     order by rp.start_date desc offset (-v_p."offset") limit 1;
    if not found then
      return jsonb_build_object('error', 'no reporting periods set up for this business', 'missing_setting', 'calendar.period_type');
    end if;
    v_start := v_rp.start_date; v_end := v_rp.end_date;

  else
    v_unit := case v_p.unit when 'day' then interval '1 day' when 'week' then interval '7 days'
                            when 'month' then interval '1 month' when 'quarter' then interval '3 months' else interval '1 year' end;
    if v_p.kind = 'rolling' then
      v_end := (v_as_of + v_p."offset" * v_unit)::date;
      v_start := (v_end - v_p.length * v_unit)::date + 1;
    else  -- calendar
      if v_p.unit = 'year' and v_p.anchor = 'fiscal_year' then
        -- fiscal year start in the as-of year (day clamped), else the year before
        v_fy_y := extract(year from v_as_of)::int;
        v_base := make_date(v_fy_y, v_fy_m, 1)
                  + (least(v_fy_d, extract(day from make_date(v_fy_y, v_fy_m, 1) + interval '1 month - 1 day')::int) - 1);
        if v_base > v_as_of then
          v_fy_y := v_fy_y - 1;
          v_base := make_date(v_fy_y, v_fy_m, 1)
                    + (least(v_fy_d, extract(day from make_date(v_fy_y, v_fy_m, 1) + interval '1 month - 1 day')::int) - 1);
        end if;
      else
        v_base := case
          when v_p.unit = 'day'     then v_as_of
          when v_p.unit = 'week'    then v_as_of - ((extract(isodow from v_as_of)::int - v_ws + 7) % 7)
          when v_p.unit = 'month'   then date_trunc('month', v_as_of)::date
          when v_p.unit = 'quarter' then date_trunc('quarter', v_as_of)::date
          else date_trunc('year', v_as_of)::date end;
      end if;
      v_start := (v_base + v_p."offset" * v_unit)::date;
      v_end := (v_start + v_p.length * v_unit)::date - 1;
    end if;
  end if;

  if v_p.to_date and v_end > v_as_of then v_end := v_as_of; end if;
  return jsonb_build_object('preset', v_p.key, 'label', v_p.label, 'start', v_start, 'end', v_end, 'as_of', v_as_of,
                            'basis', jsonb_build_object('kind', v_p.kind, 'week_start_isodow', v_ws,
                                                        'fiscal_year_start', lpad(v_fy_m::text, 2, '0') || '-' || lpad(v_fy_d::text, 2, '0'),
                                                        'period_type', v_ptype, 'custom_preset', v_p.account_id is not null));
end $$;

-- ---------------------------------------------------------------------------------------------------------------
-- 2. Saved filters and views
-- ---------------------------------------------------------------------------------------------------------------
-- shape check for conditions: [{field, op, value}] — data only, never SQL
create or replace function phg.harmony_conditions_valid(p jsonb) returns boolean
language sql immutable set search_path = pg_catalog, pg_temp as $$
  select jsonb_typeof(p) = 'array' and not exists (
    select 1 from jsonb_array_elements(p) c
     where jsonb_typeof(c) <> 'object'
        or coalesce(c->>'field', '') !~ '^[a-z][a-z0-9_]{0,62}$'
        or coalesce(c->>'op', '') not in ('eq','neq','in','not_in','gt','gte','lt','lte','between','prefix','contains','is_null','not_null')
        or (c->>'op' in ('in','not_in') and jsonb_typeof(c->'value') <> 'array')
        or (c->>'op' = 'between' and (jsonb_typeof(c->'value') <> 'array' or jsonb_array_length(c->'value') <> 2))
        or (c->>'op' not in ('is_null','not_null') and not (c ? 'value')))
$$;

create table if not exists phg.saved_filters (
  id           uuid primary key default gen_random_uuid(),
  account_id   uuid not null references phg.accounts(id) on delete cascade,
  user_id      uuid,                                                  -- NULL = shared in the project
  name         text not null check (length(btrim(name)) between 1 and 120),
  entity_key   text not null references phg.harmony_entities(key),
  conditions   jsonb not null default '[]'::jsonb check (phg.harmony_conditions_valid(conditions)),
  created_by   uuid,
  source       text not null default 'spoken' check (source in ('spoken','ui')),
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  archived_at  timestamptz
);
create unique index if not exists saved_filters_name_uq
  on phg.saved_filters (account_id, coalesce(user_id, '00000000-0000-0000-0000-000000000000'::uuid), lower(name)) where archived_at is null;

create table if not exists phg.saved_views (
  id                  uuid primary key default gen_random_uuid(),
  account_id          uuid not null references phg.accounts(id) on delete cascade,
  user_id             uuid,                                           -- NULL = shared in the project
  name                text not null check (length(btrim(name)) between 1 and 120),
  entity_key          text references phg.harmony_entities(key),     -- a view of things ...
  metric_keys         text[] not null default '{}',                   -- ... or of metrics (phg.metric_definitions, draft 04)
  filter_ids          uuid[] not null default '{}',                   -- saved_filters, ANDed
  extra_conditions    jsonb not null default '[]'::jsonb check (phg.harmony_conditions_valid(extra_conditions)),
  period_preset_key   text,                                           -- phg.period_presets.key
  group_by            text[] not null default '{}',
  columns             text[] not null default '{}',
  sort                jsonb not null default '[]'::jsonb,             -- [{"field":"amount","dir":"desc"}]
  display             text not null default 'table' check (display in ('table','bars','tiles','map','dashboard')),
  pinned              boolean not null default false,
  sort_order          int not null default 0,
  created_by          uuid,
  source              text not null default 'spoken' check (source in ('spoken','ui')),
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now(),
  archived_at         timestamptz,                                    -- delete_view = archive
  check (entity_key is not null or cardinality(metric_keys) > 0)
);
create unique index if not exists saved_views_name_uq
  on phg.saved_views (account_id, coalesce(user_id, '00000000-0000-0000-0000-000000000000'::uuid), lower(name)) where archived_at is null;
create index if not exists saved_views_pinned on phg.saved_views (account_id, user_id) where pinned and archived_at is null;

create or replace function phg.saved_filters_validate() returns trigger
language plpgsql set search_path = phg, pg_temp as $$
begin
  new.updated_at := now();
  -- a shared filter used by a shared view cannot become personal
  if tg_op = 'UPDATE' and old.user_id is null and new.user_id is not null
     and exists (select 1 from phg.saved_views v where new.id = any (v.filter_ids) and v.user_id is null and v.archived_at is null) then
    raise exception 'filter is used by a shared view';
  end if;
  return new;
end $$;
drop trigger if exists saved_filters_validate on phg.saved_filters;
create trigger saved_filters_validate before update on phg.saved_filters for each row execute function phg.saved_filters_validate();

create or replace function phg.saved_views_validate() returns trigger
language plpgsql set search_path = phg, pg_temp as $$
declare v_bad int;
begin
  new.updated_at := now();
  -- every filter: same project, same entity, not archived, and visible to everyone who can see the view
  select count(*) into v_bad from unnest(new.filter_ids) fid
   where not exists (select 1 from phg.saved_filters f
                      where f.id = fid and f.account_id = new.account_id and f.archived_at is null
                        and (new.entity_key is null or f.entity_key = new.entity_key)
                        and (f.user_id is null or f.user_id = new.user_id));
  if v_bad > 0 then raise exception 'view uses % filter(s) that are missing, archived, for another kind of thing, or private', v_bad; end if;
  if new.period_preset_key is not null and not exists (
       select 1 from phg.period_presets p where p.key = new.period_preset_key and p.active
          and (p.account_id is null or p.account_id = new.account_id)) then
    raise exception 'unknown time window %', new.period_preset_key;
  end if;
  return new;
end $$;
drop trigger if exists saved_views_validate on phg.saved_views;
create trigger saved_views_validate before insert or update on phg.saved_views for each row execute function phg.saved_views_validate();

alter table phg.period_presets enable row level security;
alter table phg.saved_filters  enable row level security;
alter table phg.saved_views    enable row level security;
revoke all on phg.period_presets, phg.saved_filters, phg.saved_views from public, anon, authenticated;

-- ---------------------------------------------------------------------------------------------------------------
-- 3. Entity fields people filter by (sources are plain columns on the entity's first main table unless 'path:...')
--    All columns below were checked on the live schema 2026-09-28/29.
-- ---------------------------------------------------------------------------------------------------------------
insert into phg.harmony_entities (key, label, entity_group, aliases, main_tables, scope, name_lookup) values
  ('invoice_line','invoice line','Buying and cost','{line item}','{phg.purchase_invoice_lines,phg.purchase_invoices}','project','{}')
on conflict (key) do nothing;
-- required_roles copied from the live purchase_invoices row (today '{}' = any active member) so lines never show wider
insert into phg.harmony_table_access (schema_name, table_pattern, access, scope_kind, scope_expr, required_roles, notes)
select 'phg','purchase_invoice_lines','project_read','custom',
       'invoice_id in (select i.id from phg.purchase_invoices i where i.location_key in (select phg.harmony_scope_location_keys()))',
       coalesce((select a.required_roles from phg.harmony_table_access a
                  where a.schema_name = 'phg' and a.table_pattern = 'purchase_invoices'), '{}'),
       'via purchase_invoices'
on conflict (schema_name, table_pattern) do nothing;

-- Pre-RLS check (knowledge-map block, narrowed to purchase_invoice_lines): list every non-owner, non-BYPASSRLS role that
-- can SELECT it today (table relacl + column attacl, PUBLIC included, plus pg_read_all_data members). Those roles see ZERO
-- rows once RLS is on unless a policy covers them. Read-only check 2026-09-29: RLS off; ACL postgres + service_role only
-- (both owner/BYPASSRLS) -> expected '(none)'. Any other name must be reviewed before approving.
do $$
declare v text; v_oid oid := to_regclass('phg.purchase_invoice_lines');
begin
  with g as (
    select a.grantee, c.oid::regclass::text t from pg_class c, aclexplode(c.relacl) a
     where c.oid = v_oid and a.privilege_type = 'SELECT' and a.grantee <> c.relowner
    union
    select a.grantee, c.oid::regclass::text || ' (columns)' from pg_attribute at join pg_class c on c.oid = at.attrelid,
           aclexplode(at.attacl) a
     where at.attrelid = v_oid and a.privilege_type = 'SELECT' and a.grantee <> c.relowner
  )
  select string_agg(x, ', ') into v from (
    select distinct case when g.grantee = 0 then 'PUBLIC' else g.grantee::regrole::text end || ' -> ' || g.t x
      from g left join pg_roles r on r.oid = g.grantee
     where g.grantee = 0 or (not r.rolbypassrls and r.rolname <> 'phg_harmony_reader')
    union
    select rolname || ' -> ALL (pg_read_all_data)' from pg_roles
     where pg_has_role(oid, 'pg_read_all_data', 'member') and not rolbypassrls and rolname <> 'pg_read_all_data'
  ) s;
  raise notice 'harmony pre-RLS check (purchase_invoice_lines): non-owner, non-BYPASSRLS roles with SELECT: %', coalesce(v, '(none)');
end $$;

select phg.harmony_apply_table_access();

-- one date axis per entity (time presets need exactly one); live check 2026-09-29: no duplicates today
create unique index if not exists harmony_entity_fields_one_date_axis on phg.harmony_entity_fields (entity_key) where is_date_axis;

insert into phg.harmony_entity_fields (entity_key, field_key, label, aliases, source, data_type, is_date_axis, filterable) values
  ('ingredient','name','name','{}','name','text',false,true),
  ('ingredient','category','category','{type of ingredient}','category','text',false,true),
  ('ingredient','ingredient_type','ingredient type','{}','ingredient_type','text',false,true),
  ('party','name','name','{supplier,vendor}','name','text',false,true),
  ('party','kinds','kind','{type}','kinds','list',false,true),
  ('party','delivery_days','delivery days','{}','delivery_days','list',false,true),
  ('party','gl_default_code','default GL account','{gl account}','gl_default_code','text',false,true),
  ('expense','expense_date','date','{}','expense_date','date',true,true),
  ('expense','description','description','{}','description','text',false,true),
  ('expense','amount','amount','{spend}','signed_amount','money',false,true),
  ('expense','revenue_center','revenue center','{}','revenue_center','text',false,true),
  ('expense','location_key','location','{}','location_key','text',false,true),
  ('expense','category','expense category','{}','path:expense_category.category_key','text',false,true),
  ('invoice','invoice_date','invoice date','{date}','invoice_date','date',true,true),
  ('invoice','invoice_number','invoice number','{}','invoice_number','text',false,true),
  ('invoice','total','total','{amount}','total','money',false,true),
  ('invoice','status','status','{}','status','text',false,true),
  ('invoice','vendor','vendor','{supplier}','path:invoice_vendor.name','text',false,true),
  ('invoice_line','description','description','{item}','raw_description','text',false,true),
  ('invoice_line','product_family','product family','{category}','product_family_key','text',false,true),
  ('invoice_line','amount','amount','{}','extended_amount','money',false,true),
  ('invoice_line','invoice_date','invoice date','{date}','path:invoice_line_invoice.invoice_date','date',true,true),
  ('sales','business_date','date','{day}','business_date','date',true,true),
  ('sales','revenue_center','revenue center','{}','revenue_center','text',false,true),
  ('sales','net_sales','net sales','{}','net_sales','money',false,true),
  ('sales','comps','comps','{}','comps','money',false,true),
  ('sales','discounts','discounts','{}','discounts','money',false,true),
  ('house_menu_item','name','name','{drink}','name','text',false,true),
  ('house_menu_item','section','section','{}','section_name','text',false,true),
  ('house_menu_item','status','status','{}','status','text',false,true),
  ('house_menu_item','price','price','{}','menu_price','money',false,true),
  ('recipe','name','name','{}','name','text',false,true),
  ('recipe','status','status','{}','status','text',false,true),
  ('recipe','created_at','created','{}','created_at','date',true,true)
on conflict (entity_key, field_key) do nothing;
-- 'gl_account' is NOT a field anywhere yet: no expense or invoice-line column holds a GL code today. Where the result of
-- phg.invoice_coding_rules is stored (a new gl_code column vs. metadata) is an open question for Rob.

-- ---------------------------------------------------------------------------------------------------------------
-- 4. View -> query spec resolver (no SQL built, nothing executed against business data)
-- ---------------------------------------------------------------------------------------------------------------
create or replace function phg.harmony_view_spec(p_account uuid, p_user uuid, p_view_id uuid, p_as_of date default null)
returns jsonb language plpgsql stable security definer set search_path = phg, pg_temp as $$
declare
  v        phg.saved_views;
  e        phg.harmony_entities;
  v_conds  jsonb := '[]'::jsonb;
  v_errors text[] := '{}';
  v_period jsonb;
  v_date   phg.harmony_entity_fields;
  f        phg.harmony_entity_fields;
  c        jsonb;
  r        record;
  v_gb     jsonb := '[]'::jsonb; v_cols jsonb := '[]'::jsonb; v_sort jsonb := '[]'::jsonb;
  v_source jsonb;
  v_metrics jsonb;
begin
  select * into v from phg.saved_views
   where id = p_view_id and account_id = p_account and archived_at is null and (user_id is null or user_id = p_user);
  if not found then return jsonb_build_object('errors', jsonb_build_array('view not found')); end if;

  if v.entity_key is not null then
    select * into e from phg.harmony_entities where key = v.entity_key;
    v_source := jsonb_build_object('kind', 'entity', 'entity', e.key, 'table', e.main_tables[1]);
    select * into v_date from phg.harmony_entity_fields where entity_key = e.key and is_date_axis limit 1;
  else
    -- metric views: metric_definitions arrives in draft 04; read it dynamically so this draft does not depend on 04
    if to_regclass('phg.metric_definitions') is null then
      v_errors := v_errors || 'metric definitions not installed (draft 04)'::text;
    else
      execute 'select coalesce(jsonb_agg(jsonb_build_object(''key'', key, ''function_name'', function_name, ''status'', status, ''unit'', unit)), ''[]''::jsonb)
                 from phg.metric_definitions where key = any ($1)' into v_metrics using v.metric_keys;
      if jsonb_array_length(v_metrics) < cardinality(v.metric_keys) then v_errors := v_errors || 'unknown metric in view'::text; end if;
    end if;
    v_source := jsonb_build_object('kind', 'metrics', 'metrics', coalesce(v_metrics, '[]'::jsonb));
  end if;

  -- a filter that is gone, private to someone else, or for another kind of thing is an error, never silently skipped
  if cardinality(v.filter_ids) > 0 and (select count(distinct x) from unnest(v.filter_ids) x) <> (
       select count(*) from phg.saved_filters sf
        where sf.id = any (v.filter_ids) and sf.account_id = p_account and sf.archived_at is null
          and (sf.user_id is null or sf.user_id = p_user) and sf.entity_key = v.entity_key) then
    v_errors := v_errors || 'view uses a filter that is missing, private or for another kind of thing'::text;
  end if;

  -- conditions: every filter (in order) then the view's own
  for r in
    select sf.id fid, x.c from unnest(v.filter_ids) with ordinality u(fid_u, n)
      join phg.saved_filters sf on sf.id = u.fid_u and sf.account_id = p_account and sf.archived_at is null
                               and (sf.user_id is null or sf.user_id = p_user) and sf.entity_key = v.entity_key
      cross join lateral jsonb_array_elements(sf.conditions) x(c)
    union all
    select null, x.c from jsonb_array_elements(v.extra_conditions) x(c)
  loop
    if v.entity_key is null then v_errors := v_errors || 'filters need a view of things, not metrics'::text; exit; end if;
    select * into f from phg.harmony_entity_fields where entity_key = v.entity_key and field_key = r.c->>'field' and filterable and not sensitive;
    if f.id is null then
      v_errors := v_errors || format('unknown field %L on %s', r.c->>'field', v.entity_key);
    else
      -- rebuilt key by key: nothing else stored in a condition reaches the compiler
      v_conds := v_conds || jsonb_build_array(jsonb_build_object('field', f.field_key, 'op', r.c->'op', 'value', r.c->'value',
                                                                 'source', f.source, 'data_type', f.data_type));
    end if;
  end loop;

  if v.period_preset_key is not null then
    v_period := phg.resolve_period(p_account, v.period_preset_key, p_as_of);
    if v_period ? 'error' then v_errors := v_errors || (v_period->>'error');
    elsif v.entity_key is not null and v_date.id is null then v_errors := v_errors || format('%s has no date to apply a time window to', v.entity_key);
    elsif v.entity_key is not null then v_period := v_period || jsonb_build_object('date_field', v_date.field_key, 'date_source', v_date.source);
    end if;
  end if;

  if v.entity_key is not null then
    for r in select unnest(v.group_by) k loop
      select * into f from phg.harmony_entity_fields where entity_key = v.entity_key and field_key = r.k and not sensitive;
      if f.id is null then v_errors := v_errors || format('unknown group-by %L', r.k);
      else v_gb := v_gb || jsonb_build_array(jsonb_build_object('field', f.field_key, 'source', f.source)); end if;
    end loop;
    for r in select unnest(v.columns) k loop
      select * into f from phg.harmony_entity_fields where entity_key = v.entity_key and field_key = r.k and not sensitive;
      if f.id is null then v_errors := v_errors || format('unknown column %L', r.k);
      else v_cols := v_cols || jsonb_build_array(jsonb_build_object('field', f.field_key, 'source', f.source, 'label', f.label)); end if;
    end loop;
    for c in select value from jsonb_array_elements(v.sort) loop
      select * into f from phg.harmony_entity_fields where entity_key = v.entity_key and field_key = c->>'field' and not sensitive;
      if f.id is null then v_errors := v_errors || format('unknown sort field %L', c->>'field');
      else v_sort := v_sort || jsonb_build_array(jsonb_build_object('field', f.field_key, 'source', f.source,
                                                                     'dir', case when c->>'dir' = 'desc' then 'desc' else 'asc' end)); end if;
    end loop;
  end if;

  return jsonb_build_object(
    'spec_version', 1,
    'view', jsonb_build_object('id', v.id, 'name', v.name, 'display', v.display, 'pinned', v.pinned),
    'source', v_source, 'period', v_period, 'conditions', v_conds,
    'group_by', v_gb, 'columns', v_cols, 'sort', v_sort, 'limit', 500,
    'scope', jsonb_build_object('account_id', p_account, 'user_id', p_user),
    'errors', to_jsonb(v_errors));
end $$;

revoke all on function phg.resolve_period(uuid, text, date), phg.harmony_view_spec(uuid, uuid, uuid, date),
                       phg.harmony_business_today(uuid)
  from public, anon, authenticated, service_role;

-- ---------------------------------------------------------------------------------------------------------------
-- 5. Reads for Harmony (service_role only)
-- ---------------------------------------------------------------------------------------------------------------
create or replace function public.phg_harmony_views_db(p_op text, p_args jsonb)
returns jsonb language plpgsql stable security definer set search_path = phg, pg_temp as $$
declare
  v_user    uuid := nullif(p_args->>'user', '')::uuid;
  v_account uuid := nullif(p_args->>'account', '')::uuid;
  v_as_of   date := nullif(p_args->>'as_of', '')::date;     -- NULL = today in the business's time zone (resolve_period)
begin
  if v_user is null or v_account is null then raise exception 'user and account required'; end if;
  if not exists (select 1 from phg.account_memberships where user_id = v_user and account_id = v_account and status = 'active') then
    raise exception 'not a member of that account';
  end if;

  if p_op = 'presets_list' then
    return coalesce((select jsonb_agg(jsonb_build_object('key', p.key, 'label', p.label, 'aliases', p.aliases, 'custom', p.account_id is not null) order by p.sort)
      from (select distinct on (key) * from phg.period_presets
             where active and (account_id is null or account_id = v_account) order by key, account_id nulls last) p), '[]'::jsonb);
  elsif p_op = 'period_resolve' then
    return phg.resolve_period(v_account, p_args->>'preset', v_as_of);
  elsif p_op = 'filters_list' then
    return coalesce((select jsonb_agg(jsonb_build_object('id', id, 'name', name, 'entity', entity_key, 'conditions', conditions,
                                                          'shared', user_id is null) order by name)
      from phg.saved_filters where account_id = v_account and archived_at is null and (user_id is null or user_id = v_user)
        and (p_args->>'entity' is null or entity_key = p_args->>'entity')), '[]'::jsonb);
  elsif p_op = 'views_list' then
    return coalesce((select jsonb_agg(jsonb_build_object('id', id, 'name', name, 'entity', entity_key, 'metrics', metric_keys,
                                                          'display', display, 'pinned', pinned, 'shared', user_id is null)
                                      order by pinned desc, sort_order, name)
      from phg.saved_views where account_id = v_account and archived_at is null and (user_id is null or user_id = v_user)), '[]'::jsonb);
  elsif p_op = 'view_spec' then
    return phg.harmony_view_spec(v_account, v_user, nullif(p_args->>'view_id', '')::uuid, v_as_of);
  end if;
  raise exception 'unknown op %', p_op;
end $$;
revoke all on function public.phg_harmony_views_db(text, jsonb) from public, anon, authenticated;
grant execute on function public.phg_harmony_views_db(text, jsonb) to service_role;

commit;
