-- DRAFT — NOT APPLIED. Needs Rob's approval. Spec: handoff/HARMONY_CONVERSATION_MODEL.md §4B (4B.1-4B.5), §4C, §4A.1, §4A.3, §6.1 (records only)
-- Revised 2026-09-29 (Rob: no folders): adds phg.parties, phg.invoice_coding_rules and phg.workspace_records (moved here from
-- the dropped folders draft); the folder-template setting is replaced by a default-period setting.
--
-- What this does (plain English)
--   The "setup skeleton": everything Harmony needs to know about a business, and each business's answers.
--   * phg.setting_definitions (admin-owned, shared): one row per thing to know (week start, POS, labor target ...),
--     with the question to ask, options, default, what it unlocks, when to ask, and where it can be inferred from.
--   * phg.account_settings (per project): the answer, where it came from (asked | inferred | imported | default),
--     confidence, who confirmed it and when, and the full history of previous values (kept by a trigger).
--   * phg.account_glossary (per project): the business's own words mapped to PHG things ("hall" = revenue center Hall).
--   * phg.harmony_memory (per project, optionally per person): facts, preferences and habits, soft-deletable so the
--     "What Harmony knows about you" page can correct or forget anything.
--   * phg.data_sources (per project): where each kind of data comes from (POS, payroll ...), how it arrives, and the
--     column mapping. POS sources reuse the existing phg.sales_import_mappings.
--   * phg.parties (per project): suppliers, distributors, service providers, landlords ... name, kinds, contact fields,
--     delivery days, default GL code, notes. Filled by the setup walkthrough ("Who delivers your liquor? What days?").
--     No login/password fields exist on purpose (the Parkway FH "Vendors/People/Login Info" logins are never copied).
--   * phg.invoice_coding_rules (per project): how invoice lines get a GL code — by party or party-name pattern, plus a
--     line-description pattern -> gl_code, with confidence and who confirmed it. Learned in conversation
--     ("Breakthru lines with 'tequila' go to 5100-01 Liquor, right?").
--   * phg.workspace_records (per project): free-form jsonb records for things that have no table yet ("make a supplier
--     contact card"). Kept from the old folders draft because create_record (06) needs it; everything else from that
--     draft is gone. A record type that keeps coming up should graduate to a real table.
--   * Registers these tables in the draft-01 whitelist (project_read) and re-runs phg.harmony_apply_table_access().
--   * public.phg_harmony_setup_db(op, args): service_role-only dispatcher (same shape as phg_harmony_inbox_db) for
--     reading settings/setup status/glossary/memory and for the person's own memory edits. Changing a SETTING goes
--     through the Command Center proposal flow (set_account_setting, file 06), not through this function.
--
-- Apply order: 02 -> 04 -> 03 -> 05 -> 06 (this file is FIRST). Depends on the live knowledge map
--   (20260929020000_harmony_knowledge_map.sql: harmony_table_access, harmony_apply_table_access, harmony_entities).
--
-- Name resolution order (read before approving)
--   phg.harmony_aliases (live, from 20260929013000) is read FIRST: it holds what a person actually said -> what they meant
--   (heard/kind/means/ref_id), learned from corrections. phg.account_glossary (this file) maps the business's own
--   TERMS to ENTITIES ('the hall' -> revenue_center Hall). Glossary is consulted only when no alias matches.
--
-- Live-schema facts (read-only checks 2026-09-29)
--   * phg.sales_import_mappings(id, mapping_name, source_system, version, mapping_spec jsonb, active, created_at) has NO
--     account_id: one row today ('generic_sales_csv'). This draft adds a NULLABLE account_id (null = shared template) —
--     additive, existing row untouched. Open question for Rob.
--     Reader search (pg_proc.prosrc ILIKE '%import_mapping%', all non-system schemas; plus views and FKs on the table):
--     NO live function, view or FK reads phg.sales_import_mappings today, and no code in this repo references it besides
--     this draft. ACL: postgres + service_role only. RULE: any function/edge code written later that reads this table
--     MUST filter `account_id is null or account_id = <caller's account>` BEFORE any project-owned mapping
--     (account_id set) is written; otherwise one business's POS column mapping leaks to another. Re-run the pg_proc
--     search immediately before the first project-owned mapping is inserted.
--   * Membership roles in the live check constraint are owner|admin|editor|analyst|viewer (spec §4C.2 says
--     owner/admin/manager/staff). Seeds below use the live names.
--   * No credentials are stored in any table here. data_sources.connector_ref only NAMES a secret kept elsewhere.
--     phg.data_sources is registered as 'never' in the query whitelist (connection details); read it via phg_harmony_setup_db.
--   * phg.vendors (existing, global, no account_id, 0 project scoping) stays as the costing graph's vendor key;
--     parties.vendor_id optionally points at it. gl_default_code / invoice_coding_rules.gl_code are text, not FKs, because
--     phg.gl_accounts arrives in draft 04 (validated by the command action at write time).
--   * The live 'vendor' entity already owns the alias 'vendor' (aliases {distributor,supplier}); the 'party' entity
--     below does NOT use 'vendor' as an alias. 'distributor'/'supplier' still overlap with the vendor entity's aliases:
--     harmony_aliases / a clarifying question decides between them.
--   * account_settings.user_id: NULL = business-wide answer; set = that person's own answer (per_scope 'person').
--     Readers (query gateway scope_expr, settings_get) show business-wide rows plus only the caller's own rows.
--   * harmony_memory: personal memory any active member; project-wide memory (user_id NULL) only owner/admin/editor,
--     and only with source 'conversation' or 'inferred'.
--
-- Rollback (scripted; run as postgres in ONE transaction, off-peak, AFTER rolling back 06, 05, 03 and 04 in that order)
--   begin;
--   set local lock_timeout = '3s';
--   -- 1. backups of everything a person may have entered (kept until Rob deletes them)
--   create table if not exists phg._rb02_account_settings   as select * from phg.account_settings;
--   create table if not exists phg._rb02_account_glossary   as select * from phg.account_glossary;
--   create table if not exists phg._rb02_harmony_memory     as select * from phg.harmony_memory;
--   create table if not exists phg._rb02_data_sources       as select * from phg.data_sources;
--   create table if not exists phg._rb02_parties            as select * from phg.parties;
--   create table if not exists phg._rb02_invoice_coding_rules as select * from phg.invoice_coding_rules;
--   create table if not exists phg._rb02_workspace_records  as select * from phg.workspace_records;
--   create table if not exists phg._rb02_sales_import_mappings_owned as
--     select * from phg.sales_import_mappings where account_id is not null;
--   revoke all on phg._rb02_account_settings, phg._rb02_account_glossary, phg._rb02_harmony_memory, phg._rb02_data_sources,
--     phg._rb02_parties, phg._rb02_invoice_coding_rules, phg._rb02_workspace_records, phg._rb02_sales_import_mappings_owned
--     from public, anon, authenticated;
--   -- 2. functions and triggers
--   drop function if exists public.phg_harmony_setup_db(text, jsonb);
--   drop trigger if exists account_settings_history on phg.account_settings; drop function if exists phg.account_settings_keep_history();
--   drop trigger if exists data_sources_same_account on phg.data_sources; drop function if exists phg.data_sources_same_account();
--   -- 3. whitelist rows + entities (policies go with the tables in step 4)
--   delete from phg.harmony_table_access where schema_name = 'phg' and table_pattern in
--     ('parties','invoice_coding_rules','workspace_records','account_settings','account_glossary','harmony_memory',
--      'data_sources','setting_definitions');
--   delete from phg.harmony_entities where key in ('party','record','setting');
--   -- 4. tables (children first)
--   drop table if exists phg.invoice_coding_rules, phg.parties, phg.workspace_records;
--   drop table if exists phg.data_sources, phg.harmony_memory, phg.account_glossary, phg.account_settings, phg.setting_definitions;
--   -- only if _rb02_sales_import_mappings_owned is empty, or Rob accepts those rows becoming shared templates:
--   delete from phg.sales_import_mappings where account_id is not null;   -- backed up in step 1
--   alter table phg.sales_import_mappings drop column if exists account_id;
--   -- 5. verify (expect: all nulls, 0, 0, false)
--   select to_regclass('phg.account_settings') s, to_regclass('phg.parties') p, to_regclass('phg.data_sources') d,
--          to_regprocedure('public.phg_harmony_setup_db(text,jsonb)') fn,
--          (select count(*) from phg.harmony_entities where key in ('party','record','setting')) entities,
--          (select count(*) from phg.harmony_table_access where table_pattern in ('parties','invoice_coding_rules',
--             'workspace_records','account_settings','account_glossary','harmony_memory','data_sources','setting_definitions')) access_rows,
--          exists (select 1 from information_schema.columns where table_schema = 'phg' and table_name = 'sales_import_mappings'
--                   and column_name = 'account_id') sim_account_col;
--   commit;

begin;

set local lock_timeout = '3s';   -- off-peak; on 55P03 (lock_not_available) nothing is applied, retry later

create table if not exists phg.setting_definitions (
  key            text primary key,                                   -- 'calendar.week_start'
  setting_group  text not null check (setting_group in ('Business','Locations','Calendar','Sales/POS','Labor','Purchasing',
                                                        'Accounting','Menus','Targets','Voice','People')),
  label          text not null,
  value_type     text not null check (value_type in ('choice','number','percent','money','text','list','mapping','connector','bool','time','date')),
  question       text not null,                                      -- what Harmony asks
  options        jsonb,                                              -- fixed choices, or {"from":"phg.sales_locations"} for data-driven options
  default_value  jsonb,
  default_note   text,                                               -- "Monday (asked, can change)"
  needed_by      text[] not null default '{}',                       -- metric / feature keys it unlocks
  ask_when       text not null default 'first_use' check (ask_when in ('first_use','setup_interview','never')),
  infer_from     text[] not null default '{}',                       -- "sales export dates", "Airtable Financial.Week"
  per_scope      text not null default 'account' check (per_scope in ('account','location','revenue_center','person')),
  edit_roles     text[] not null default '{owner,admin}',            -- who may change it
  sort           int not null default 100,
  active         boolean not null default true,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table if not exists phg.account_settings (
  id             uuid primary key default gen_random_uuid(),
  account_id     uuid not null references phg.accounts(id) on delete cascade,
  key            text not null references phg.setting_definitions(key) on update cascade,
  user_id        uuid,                                               -- NULL = whole business; set = this person's own answer
  scope_key      text not null default '',                           -- '' = whole business; else location / revenue center key
  value          jsonb not null,
  source         text not null check (source in ('asked','inferred','imported','default')),
  confidence     numeric check (confidence between 0 and 1),
  evidence       jsonb not null default '{}'::jsonb,                 -- what an inferred/imported value was based on
  confirmed_by   uuid,                                               -- auth user id
  confirmed_at   timestamptz,
  history        jsonb not null default '[]'::jsonb,                 -- previous {value, source, confidence, confirmed_by, confirmed_at, replaced_at}
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  unique nulls not distinct (account_id, key, scope_key, user_id)    -- PG15+; live is PG17. 06 upserts on these columns
);

create or replace function phg.account_settings_keep_history() returns trigger
language plpgsql set search_path = phg, pg_temp as $$
begin
  if (old.value, old.source, old.confidence, old.confirmed_by, old.confirmed_at)
     is distinct from (new.value, new.source, new.confidence, new.confirmed_by, new.confirmed_at) then
    new.history := old.history || jsonb_build_array(jsonb_build_object(
      'value', old.value, 'source', old.source, 'confidence', old.confidence,
      'confirmed_by', old.confirmed_by, 'confirmed_at', old.confirmed_at, 'replaced_at', now()));
    new.updated_at := now();
  end if;
  return new;
end $$;
drop trigger if exists account_settings_history on phg.account_settings;
create trigger account_settings_history before update on phg.account_settings
  for each row execute function phg.account_settings_keep_history();

create table if not exists phg.account_glossary (
  id             uuid primary key default gen_random_uuid(),
  account_id     uuid not null references phg.accounts(id) on delete cascade,
  term           text not null,                                      -- as the business says it: 'the hall'
  term_norm      text generated always as (lower(btrim(term))) stored,
  entity_type    text not null,                                      -- harmony_entities.key or workspace_entity_types.key ('revenue_center', 'ingredient' ...)
  entity_id      text,                                               -- id when it points at a row
  entity_value   jsonb,                                              -- or a value ({"revenue_center":"Hall"})
  confirmed      boolean not null default false,                     -- true only after "By 'hall' do you mean ...?" -> yes
  confirmed_by   uuid,
  confirmed_at   timestamptz,
  source         text not null default 'asked' check (source in ('asked','inferred','imported')),
  created_by     uuid,
  created_at     timestamptz not null default now(),
  deleted_at     timestamptz,
  check (entity_id is not null or entity_value is not null)
);
create unique index if not exists account_glossary_term_uq on phg.account_glossary (account_id, term_norm, entity_type) where deleted_at is null;

create table if not exists phg.harmony_memory (
  id             uuid primary key default gen_random_uuid(),
  account_id     uuid not null references phg.accounts(id) on delete cascade,
  user_id        uuid,                                               -- null = project-level memory; set = this person only
  kind           text not null check (kind in ('fact','preference','habit')),
  text           text not null check (length(text) <= 2000),
  data           jsonb not null default '{}'::jsonb,                 -- structured form, e.g. habit {"question":"labor_pct","default_rc":"Bar"}
  source         text not null default 'conversation' check (source in ('conversation','inferred','imported','admin')),
  source_ref     text,                                               -- conversation / turn id
  created_at     timestamptz not null default now(),
  confirmed_at   timestamptz,
  last_used_at   timestamptz,
  use_count      int not null default 0,
  deleted_at     timestamptz
);
create index if not exists harmony_memory_scope on phg.harmony_memory (account_id, user_id) where deleted_at is null;

-- optional, additive: lets a business own its confirmed POS mapping (null = shared template, as today)
alter table phg.sales_import_mappings add column if not exists account_id uuid references phg.accounts(id) on delete cascade;

create table if not exists phg.data_sources (
  id                        uuid primary key default gen_random_uuid(),
  account_id                uuid not null references phg.accounts(id) on delete cascade,
  location_id               uuid references phg.sales_locations(id) on delete set null,
  kind                      text not null check (kind in ('pos','payroll','accounting','scheduling','spreadsheet','airtable','other')),
  vendor                    text,                                    -- 'Toast', 'Square', 'QuickBooks Online', 'Airtable' ...
  transport                 text not null check (transport in ('connector','export','email','upload')),
  sales_import_mapping_id   uuid references phg.sales_import_mappings(id) on delete set null,  -- POS only
  mapping_spec              jsonb not null default '{}'::jsonb,      -- non-POS column/field mapping until each has its own mapper
  connector_ref             text,                                    -- NAME of a stored connection/secret; never the secret itself
  schedule                  text,                                    -- 'nightly', cron text, or null for manual
  status                    text not null default 'draft'
                            check (status in ('draft','awaiting_sample','mapping_proposed','active','paused','error','retired')),
  last_sync_at              timestamptz,
  last_error                text,
  created_by                uuid,
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now(),
  check (sales_import_mapping_id is null or kind = 'pos')
);
create index if not exists data_sources_account on phg.data_sources (account_id, kind);

-- a data source may only point at its own project's location and at a shared (NULL) or its own POS mapping
create or replace function phg.data_sources_same_account() returns trigger
language plpgsql security definer set search_path = phg, pg_temp as $$
begin
  if new.location_id is not null and not exists (
       select 1 from phg.sales_locations l where l.id = new.location_id and l.account_id = new.account_id) then
    raise exception 'location % does not belong to this project', new.location_id;
  end if;
  if new.sales_import_mapping_id is not null and not exists (
       select 1 from phg.sales_import_mappings m
        where m.id = new.sales_import_mapping_id and (m.account_id is null or m.account_id = new.account_id)) then
    raise exception 'sales import mapping % belongs to another project', new.sales_import_mapping_id;
  end if;
  return new;
end $$;
revoke all on function phg.data_sources_same_account() from public, anon, authenticated;
drop trigger if exists data_sources_same_account on phg.data_sources;
create trigger data_sources_same_account before insert or update on phg.data_sources
  for each row execute function phg.data_sources_same_account();

-- ---------------------------------------------------------------------------------------------------------------
-- Parties, invoice coding rules, free-form records
-- ---------------------------------------------------------------------------------------------------------------
create table if not exists phg.parties (
  id               uuid primary key default gen_random_uuid(),
  account_id       uuid not null references phg.accounts(id) on delete cascade,
  name             text not null check (length(btrim(name)) between 1 and 200),
  kinds            text[] not null default '{supplier}'
                   check (kinds <@ array['supplier','distributor','service_provider','landlord','utility','contractor',
                                         'marketing','entertainment','bank','payroll','insurance','government','other']::text[]
                          and cardinality(kinds) >= 1),
  legal_name       text,
  aliases          text[] not null default '{}',          -- how the business / invoices name it ('Breakthru', 'BB&G')
  contact_name     text,
  email            text,
  phone            text,
  address          jsonb,                                  -- {"street","city","state","postal_code"}
  website          text,
  account_number   text,                                   -- the business's customer number AT the party (not a secret)
  delivery_days    text[] not null default '{}'
                   check (delivery_days <@ array['mon','tue','wed','thu','fri','sat','sun']::text[]),
  order_cutoff     text,                                   -- 'Tue 2pm for Thu delivery'
  payment_terms    text,                                   -- 'net 30', 'COD'
  gl_default_code  text,                                   -- phg.gl_accounts.code (draft 04)
  vendor_id        uuid references phg.vendors(id) on delete set null,   -- link to the costing graph's vendor row
  notes            text,
  source           text not null default 'asked' check (source in ('asked','inferred','imported')),
  created_by       uuid,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  archived_at      timestamptz,
  unique (id, account_id)                                  -- target of the composite FK from invoice_coding_rules
);
create unique index if not exists parties_name_uq on phg.parties (account_id, lower(name)) where archived_at is null;
comment on table phg.parties is 'Project-scoped suppliers/distributors/service providers/landlords. Never store logins or passwords here.';

create table if not exists phg.invoice_coding_rules (
  id             uuid primary key default gen_random_uuid(),
  account_id     uuid not null references phg.accounts(id) on delete cascade,
  party_id       uuid,                                     -- same-project party: composite FK below
  party_pattern  text,                                     -- when the party is not known yet: ILIKE on the invoice vendor name
  line_pattern   text,                                     -- on purchase_invoice_lines.raw_description
  match_kind     text not null default 'ilike' check (match_kind in ('ilike','regex','exact')),
  gl_code        text not null,                            -- phg.gl_accounts.code (draft 04)
  priority       int not null default 100,                 -- lower wins when several rules match
  confidence     numeric check (confidence between 0 and 1),
  source         text not null default 'asked' check (source in ('asked','inferred','imported')),
  confirmed_by   uuid,
  confirmed_at   timestamptz,
  hit_count      int not null default 0,
  last_hit_at    timestamptz,
  active         boolean not null default true,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  foreign key (party_id, account_id) references phg.parties (id, account_id) on delete cascade,  -- MATCH SIMPLE: null party_id = no check
  check (party_id is not null or party_pattern is not null or line_pattern is not null)
);
create index if not exists invoice_coding_rules_lookup on phg.invoice_coding_rules (account_id, party_id, priority) where active;

create table if not exists phg.workspace_records (
  id            uuid primary key default gen_random_uuid(),
  account_id    uuid not null references phg.accounts(id) on delete cascade,
  record_type   text not null,                            -- 'supplier_contact', 'idea', 'event' ... free text
  title         text not null,
  fields        jsonb not null default '{}'::jsonb,
  files         jsonb not null default '[]'::jsonb,       -- [{"storage_path":..., "name":..., "mime":...}]
  created_by    uuid,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  archived_at   timestamptz
);
create index if not exists workspace_records_account on phg.workspace_records (account_id, record_type) where archived_at is null;

alter table phg.parties              enable row level security;
alter table phg.invoice_coding_rules enable row level security;
alter table phg.workspace_records    enable row level security;
revoke all on phg.parties, phg.invoice_coding_rules, phg.workspace_records from public, anon, authenticated;

alter table phg.setting_definitions enable row level security;
alter table phg.account_settings    enable row level security;
alter table phg.account_glossary    enable row level security;
alter table phg.harmony_memory      enable row level security;
alter table phg.data_sources        enable row level security;
revoke all on phg.setting_definitions, phg.account_settings, phg.account_glossary, phg.harmony_memory, phg.data_sources
  from public, anon, authenticated;

-- ---------------------------------------------------------------------------------------------------------------
-- Seed: starter skeleton (§4B.1 "examples, not final"). Rob edits these as admin; no code change needed.
-- ---------------------------------------------------------------------------------------------------------------
insert into phg.setting_definitions (key, setting_group, label, value_type, question, options, default_value, needed_by, ask_when, infer_from, per_scope, sort) values
  ('business.name','Business','Business name','text','What should I call your business?',null,null,'{}','setup_interview','{}','account',10),
  ('business.type','Business','Business type','choice','What kind of business is it: a bar, restaurant, food hall, hotel or a group?','["bar","restaurant","food_hall","hotel","group"]',null,'{coach}','setup_interview','{}','account',11),
  ('business.time_zone','Business','Time zone','text','What time zone are you in?',null,null,'{sales_by_day,labor_pct}','first_use','{"location address"}','account',12),
  ('business.currency','Business','Currency','choice','Which currency do you report in?','["USD","CAD","MXN","EUR","GBP"]','"USD"','{}','never','{"phg.accounts.currency"}','account',13),
  ('locations.list','Locations','Locations','list','What locations do you have?','{"from":"phg.sales_locations"}',null,'{sales_by_location}','setup_interview','{"POS export location column"}','account',20),
  ('locations.revenue_centers','Locations','Revenue centers','list','What revenue centers do you track, like bar, hall, patio, events or catering?',null,null,'{net_sales,labor_pct,cogs_pct_by_category}','first_use','{"POS export revenue center column","Airtable Manager"}','location',21),
  ('calendar.week_start','Calendar','Week start','choice','What day does your week start?','["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]','"monday"','{labor_pct,declining_budget_remaining,sales_by_week}','first_use','{"sales export dates","Airtable Financial.Week"}','account',30),
  ('calendar.fiscal_year_start','Calendar','Fiscal year start','date','When does your fiscal year start?',null,'"01-01"','{pl,budget_variance}','first_use','{"accounting system"}','account',31),
  ('calendar.period_type','Calendar','Reporting period type','choice','Do you report by week, by 4-4-5 periods, or by calendar month?','["weekly","4-4-5","4-5-4","5-4-4","13x4","monthly"]','"weekly"','{period_review,pl,budget_variance}','first_use','{"Airtable Financial"}','account',32),
  ('calendar.day_close_time','Calendar','Business day closes at','time','What time does your business day end, for late nights?',null,'"04:00"','{net_sales,labor_pct}','first_use','{"POS export timestamps"}','location',33),
  ('pos.vendor','Sales/POS','POS system','choice','Which POS do you use?','["toast","square","clover","lightspeed","spoton","other","spreadsheet","none"]',null,'{net_sales,comp_pct,discount_pct,void_pct,avg_check}','first_use','{}','location',40),
  ('pos.transport','Sales/POS','How sales data arrives','choice','How can you get me the sales data: a connection, a nightly export, an emailed report, or uploading a file?','["connector","export","email","upload"]',null,'{net_sales}','first_use','{}','location',41),
  ('pos.net_sales_definition','Sales/POS','Net sales definition','choice','Is your net sales before or after comps and discounts?','["gross_minus_discounts_comps","gross_minus_discounts","gross"]','"gross_minus_discounts_comps"','{net_sales,comp_pct}','first_use','{"POS export columns"}','account',42),
  ('labor.roles','Labor','Roles','list','What roles do you schedule, like bartender, server, barback, manager?','{"from":"phg.labor_roles"}',null,'{labor_pct,hourly_labor_pct,sales_per_labor_hour}','first_use','{"payroll export","Airtable Manager hours by role"}','account',50),
  ('labor.scheduling_tool','Labor','Scheduling tool','choice','What do you use for schedules?','["7shifts","homebase","hotschedules","toast","sling","spreadsheet","none","other"]',null,'{labor_pct}','setup_interview','{}','account',51),
  ('labor.payroll_tool','Labor','Payroll tool','choice','What do you use for payroll?','["paychex","adp","gusto","toast_payroll","quickbooks","other","none"]',null,'{labor_pct}','setup_interview','{}','account',52),
  ('labor.tips_in_labor','Labor','Tips in labor %','bool','Should tips count in your labor percentage?',null,'false','{labor_pct}','first_use','{}','account',53),
  ('purchasing.invoice_arrival','Purchasing','How invoices arrive','choice','How do invoices reach you: paper, email, a vendor portal, or your accounting system?','["paper","email","portal","accounting_system"]',null,'{cogs_pct_by_category,declining_budget_remaining}','setup_interview','{}','account',60),
  ('purchasing.price_source','Purchasing','Where prices live today','choice','Where do your ingredient prices live today?','["spreadsheet","airtable","accounting_system","invoices_only","nowhere"]',null,'{recipe_cost}','first_use','{}','account',61),
  ('accounting.system','Accounting','Accounting system','choice','Which accounting system do you use?','["quickbooks_online","xero","restaurant365","sage","none","other"]',null,'{pl}','setup_interview','{}','account',70),
  ('accounting.coa_template','Accounting','Chart of accounts','choice','Start from the restaurant chart of accounts, or use your own?','["restaurant_usar","own"]','"restaurant_usar"','{cogs_pct_by_category,declining_budget_remaining,budget_variance}','first_use','{"Airtable Invoices GL columns"}','account',71),
  ('targets.labor_pct','Targets','Labor % target','percent','What labor percentage are you aiming for?',null,null,'{labor_pct,coach.labor}','first_use','{"Airtable Financial labor %"}','location',80),
  ('targets.cogs_pct_by_category','Targets','COGS % targets','mapping','What cost percentage do you aim for on liquor, beer, wine and N/A?','{"keys":["liquor","beer","wine","na_bev","bar_mix","food"]}',null,'{cogs_pct_by_category,coach.cogs}','first_use','{}','account',81),
  ('targets.comp_limit_pct','Targets','Comp % limit','percent','What''s the most you want comps to be, as a percent of sales?',null,null,'{comp_pct,coach.comps}','first_use','{}','account',82),
  ('targets.prime_cost_pct','Targets','Prime cost target','percent','What prime cost percentage are you aiming for?',null,null,'{prime_cost_pct}','first_use','{}','account',83),
  ('targets.weekly_budgets','Targets','Weekly budgets by account group','mapping','What''s your weekly budget for each spending group?','{"keys_from":"phg.gl_accounts"}',null,'{declining_budget_remaining,coach.budget}','first_use','{"Airtable Financial declining budgets"}','account',84),
  ('menus.units','Menus','Recipe units','choice','Do you build drinks in ounces or milliliters?','["oz","ml"]','"oz"','{recipe_build}','first_use','{}','account',90),
  ('menus.house_pours','Menus','House pour sizes','mapping','What are your standard pours, like 1.5 ounces for a shot?',null,null,'{recipe_cost}','first_use','{"Airtable Bar Inventory pour sizes"}','account',91),
  ('menus.technique_rules','Menus','House technique rules','list','Any house rules for technique I should follow, like how long you stir?',null,null,'{recipe_build}','first_use','{}','account',92),
  ('views.default_period','Calendar','Default time window','choice','When you ask about "lately", how far back should I look?','{"from":"phg.period_presets"}','"last_week"','{saved_views}','first_use','{}','person',34),
  ('purchasing.delivery_days','Purchasing','Delivery days by supplier','mapping','Which days does each supplier deliver?','{"from":"phg.parties"}',null,'{coach.purchasing}','setup_interview','{}','account',62),
  ('people.approval_roles','People','Who can approve what','mapping','Who can approve prices, publish menus, and see labor and pay?','{"keys":["approve_prices","publish_menus","see_labor","see_pay","change_settings","connect_data"]}','{"approve_prices":["owner","admin"],"publish_menus":["owner","admin"],"see_labor":["owner","admin","analyst"],"see_pay":["owner","admin"],"change_settings":["owner","admin"],"connect_data":["owner","admin"]}','{}','setup_interview','{}','account',100),
  ('voice.detail_level','Voice','How much detail','choice','Do you want short answers, or more detail?','["short","normal","detailed"]','"short"','{}','first_use','{}','person',110),
  ('voice.number_style','Voice','Spoken numbers','choice','Should I round numbers when I say them?','["round_dollars","exact"]','"round_dollars"','{}','never','{}','person',111),
  ('voice.name','Voice','What Harmony calls you','text','What should I call you?',null,null,'{}','setup_interview','{}','person',112),
  ('voice.open_app','Voice','When to open the app','choice','Should I only open the app when you say yes?','["ask_first","never","when_useful"]','"ask_first"','{}','never','{}','person',113)
on conflict (key) do nothing;

-- ---------------------------------------------------------------------------------------------------------------
-- Knowledge map (draft 01): new entities + whitelist entries, then (re)apply grants/policies for the reader role
-- ---------------------------------------------------------------------------------------------------------------
insert into phg.harmony_entities (key, label, entity_group, aliases, main_tables, scope, name_lookup) values
  ('party','supplier','Buying and cost','{distributor,supplier,landlord,service provider}','{phg.parties}','project','{"table":"phg.parties","id":"id","name":"name","aliases":"aliases"}'),
  ('record','record','Organising','{card,entry}','{phg.workspace_records}','project','{"table":"phg.workspace_records","id":"id","name":"title"}'),
  ('setting','business setting','Organising','{setting,setup}','{phg.account_settings,phg.setting_definitions}','project','{"table":"phg.setting_definitions","id":"key","name":"label"}')
on conflict (key) do nothing;

insert into phg.harmony_table_access (schema_name, table_pattern, access, account_column, scope_kind, scope_expr, notes) values
  ('phg','setting_definitions','shared_read', null, null, null, 'admin skeleton'),
  ('phg','account_settings',   'project_read','account_id','custom','account_id = phg.harmony_scope_account() and (user_id is null or user_id = phg.harmony_scope_user())', 'person layer: business-wide + own answers only'),
  ('phg','account_glossary',   'project_read','account_id','custom','account_id = phg.harmony_scope_account() and deleted_at is null', null),
  ('phg','harmony_memory',     'project_read','account_id','custom','account_id = phg.harmony_scope_account() and deleted_at is null and (user_id is null or user_id = phg.harmony_scope_user())', 'person layer: own + project memory only'),
  ('phg','parties',            'project_read','account_id','account_id','account_id = phg.harmony_scope_account()', null),
  ('phg','invoice_coding_rules','project_read','account_id','account_id','account_id = phg.harmony_scope_account()', null),
  ('phg','workspace_records',  'project_read','account_id','custom','account_id = phg.harmony_scope_account() and archived_at is null', null)
on conflict (schema_name, table_pattern) do nothing;
-- data_sources is deliberately NOT readable through the query gateway (connection details); use phg_harmony_setup_db.
insert into phg.harmony_table_access (schema_name, table_pattern, access, notes) values
  ('phg','data_sources','never','connection details; read through phg_harmony_setup_db only')
on conflict (schema_name, table_pattern) do nothing;
select phg.harmony_apply_table_access();

-- ---------------------------------------------------------------------------------------------------------------
-- Dispatcher (service_role only). Every op checks active membership for (user, account).
-- ---------------------------------------------------------------------------------------------------------------
create or replace function public.phg_harmony_setup_db(p_op text, p_args jsonb)
returns jsonb
language plpgsql
volatile
security definer
set search_path = phg, pg_temp
as $$
declare
  v_user    uuid := nullif(p_args->>'user', '')::uuid;
  v_account uuid := nullif(p_args->>'account', '')::uuid;
  v_row     jsonb;
begin
  if v_user is null or v_account is null then raise exception 'user and account required'; end if;
  if not exists (select 1 from phg.account_memberships
                  where user_id = v_user and account_id = v_account and status = 'active') then
    raise exception 'not a member of that account';
  end if;

  if p_op = 'settings_get' then
    -- one key, or all; always says where each value came from. Business-wide rows plus ONLY this person's own rows;
    -- for the same (key, scope_key) the person's own answer wins over the business-wide one.
    return coalesce((select jsonb_agg(jsonb_build_object(
        'key', d.key, 'group', d.setting_group, 'label', d.label, 'scope_key', s.scope_key,
        'value', coalesce(s.value, d.default_value), 'source', coalesce(s.source, case when d.default_value is not null then 'default' end),
        'personal', s.user_id is not null, 'confidence', s.confidence, 'confirmed_at', s.confirmed_at) order by d.sort, s.scope_key)
      from phg.setting_definitions d
      left join lateral (
        select distinct on (s0.scope_key) s0.* from phg.account_settings s0
         where s0.key = d.key and s0.account_id = v_account and (s0.user_id is null or s0.user_id = v_user)
         order by s0.scope_key, (s0.user_id is not null) desc) s on true
      where d.active and (p_args->>'key' is null or d.key = p_args->>'key')), '[]'::jsonb);

  elsif p_op = 'setup_status' then
    -- "What's left to set up?": missing settings with what they unlock
    return coalesce((select jsonb_agg(jsonb_build_object('key', d.key, 'group', d.setting_group, 'question', d.question,
                                                          'unlocks', d.needed_by) order by d.sort)
      from phg.setting_definitions d
      where d.active and d.ask_when <> 'never' and d.per_scope <> 'person'
        and not exists (select 1 from phg.account_settings s where s.account_id = v_account and s.key = d.key and s.user_id is null)), '[]'::jsonb);

  elsif p_op = 'glossary_list' then
    return coalesce((select jsonb_agg(to_jsonb(g) - 'term_norm' order by g.term)
      from phg.account_glossary g where g.account_id = v_account and g.deleted_at is null
        and (not coalesce((p_args->>'confirmed_only')::boolean, false) or g.confirmed)), '[]'::jsonb);

  elsif p_op = 'memory_list' then
    -- project-level memory plus this person's own; never another person's
    return coalesce((select jsonb_agg(jsonb_build_object('id', m.id, 'kind', m.kind, 'text', m.text, 'personal', m.user_id is not null,
                                                          'source', m.source, 'created_at', m.created_at, 'confirmed_at', m.confirmed_at) order by m.created_at desc)
      from phg.harmony_memory m
      where m.account_id = v_account and m.deleted_at is null and (m.user_id is null or m.user_id = v_user)), '[]'::jsonb);

  elsif p_op = 'memory_add' then
    -- personal memory: any active member. Project-wide memory (seen by everyone in the project): owner/admin/editor
    -- only, and only from a conversation or an inference (never 'imported'/'admin' through this door).
    if not coalesce((p_args->>'personal')::boolean, true) then
      if not exists (select 1 from phg.account_memberships am where am.user_id = v_user and am.account_id = v_account
                        and am.status = 'active' and am.role in ('owner','admin','editor')) then
        raise exception 'only owners, admins and editors can save project-wide memory';
      end if;
      if coalesce(p_args->>'source', 'conversation') not in ('conversation','inferred') then
        raise exception 'project-wide memory source must be conversation or inferred';
      end if;
    end if;
    insert into phg.harmony_memory (account_id, user_id, kind, text, data, source, source_ref, confirmed_at)
    values (v_account,
            case when coalesce((p_args->>'personal')::boolean, true) then v_user end,
            coalesce(p_args->>'kind', 'fact'), left(p_args->>'text', 2000), coalesce(p_args->'data', '{}'::jsonb),
            coalesce(p_args->>'source', 'conversation'), p_args->>'source_ref',
            case when coalesce((p_args->>'confirmed')::boolean, false) then now() end)
    returning jsonb_build_object('id', id, 'kind', kind, 'text', text) into v_row;
    return v_row;

  elsif p_op = 'memory_forget' then
    -- soft delete; a person can forget project-level memory only as owner/admin
    update phg.harmony_memory m set deleted_at = now()
     where m.id = nullif(p_args->>'id', '')::uuid and m.account_id = v_account and m.deleted_at is null
       and (m.user_id = v_user or (m.user_id is null and exists (
             select 1 from phg.account_memberships am where am.user_id = v_user and am.account_id = v_account
                and am.status = 'active' and am.role in ('owner','admin'))));
    return jsonb_build_object('ok', found);
  end if;

  raise exception 'unknown op %', p_op;
end;
$$;
revoke all on function public.phg_harmony_setup_db(text, jsonb) from public, anon, authenticated;
grant execute on function public.phg_harmony_setup_db(text, jsonb) to service_role;

commit;
