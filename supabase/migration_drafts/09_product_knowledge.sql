-- APPLIED 2026-09-29 as migration phg_know_product_knowledge (Rob: "Do whatever you need to"). Was DRAFT 09: PHG product knowledge (PHG-046). Shared, sourced facts about spirit brands and each bottling
-- (expression): how it is made, aging, proof, tasting notes, history. Rob 2026-09-29: tap a distillery or brand on
-- the map and get "all the product knowledge on the Blancos, the Repos, the Añejos, extra Añejos ... the origin, the
-- history". Data format: handoff/agents/PRODUCT_KNOWLEDGE_CONTRACT.md. Loaded from data/product_knowledge/*.jsonl by
-- scripts/product_knowledge_load.py (lead developer only). Same safety pattern as draft 08 (phg_mix):
--   * new schema, created fresh (fails if it exists); nothing else in the database is changed
--   * service_role reads/writes; Harmony's read-only gateway role may read (explicit grants + reader-only policy);
--     no call to the global phg.harmony_apply_table_access(); anon/authenticated get nothing
--   * links to public.brands / organizations / products are soft text keys (no FKs into live tables)
--
-- Rollback (one transaction):
--   begin;
--   set local lock_timeout = '3s';
--   delete from phg.harmony_table_access where schema_name = 'phg_know';
--   delete from phg.harmony_entities where key in ('know_brand','know_expression');
--   drop schema phg_know cascade;
--   commit;

set local lock_timeout = '3s';

do $$ begin
  if exists (select 1 from phg.harmony_table_access where schema_name = 'phg_know')
     or exists (select 1 from phg.harmony_entities where key in ('know_brand','know_expression')) then
    raise exception '09: phg_know access rows or know_* entities already exist';
  end if;
end $$;

create schema phg_know;
revoke all on schema phg_know from public, anon, authenticated;
grant usage on schema phg_know to service_role;

create table phg_know.sources (
  key         text primary key,                       -- src_<short>
  url         text,
  title       text,
  kind        text,                                   -- regulator, brand_site, reference, reviewer, retailer, article
  tier        smallint check (tier between 1 and 5),
  created_at  timestamptz not null default now()
);

create table phg_know.brand_profiles (
  key            text primary key,                    -- brand_<slug>
  name           text not null,
  aka            text[] not null default '{}',
  category       text not null check (category in ('tequila','mezcal','raicilla','sotol','bacanora','whiskey','rum',
                                                   'gin','vodka','brandy','liqueur','other')),
  nom            text,
  producer       text,
  owner          text,
  region         text,
  founded_year   int check (founded_year between 1500 and 2100),
  history        text[] not null default '{}',        -- short facts, own words
  brand_id       text,                                -- soft link: public.brands.brand_id
  organization_id text,                               -- soft link: public.organizations.organization_id (by NOM)
  verification   text not null default 'unverified' check (verification in ('page','excerpt','unverified')),
  source_keys    text[] not null default '{}',
  updated_at     timestamptz not null default now()
);
create index brand_profiles_nom on phg_know.brand_profiles (nom);
create index brand_profiles_name on phg_know.brand_profiles (lower(name));

create table phg_know.expressions (
  key              text primary key,                  -- exp_<brand>_<style>
  brand_key        text not null references phg_know.brand_profiles(key) on delete cascade,
  name             text not null,
  style            text not null check (style in ('blanco','joven','reposado','anejo','extra_anejo','cristalino','other')),
  abv              numeric(4,1) check (abv between 0 and 100),
  aging_months_min numeric(5,1),
  aging_months_max numeric(5,1),
  barrels          text,
  agave            text,
  agave_species    text,
  agave_region     text,
  cooking          text,
  milling          text,
  fermentation     text,
  distillation     text,
  water_source     text,
  additive_free    boolean,                           -- only when a named confirmation program says so
  tasting          text[] not null default '{}',
  price_usd_750    numeric(8,2),
  awards           text[] not null default '{}',
  mezcal_category  text,
  maestro          text,
  village          text,
  product_id       text,                              -- soft link: public.products.product_id
  verification     text not null default 'unverified' check (verification in ('page','excerpt','unverified')),
  source_keys      text[] not null default '{}',
  updated_at       timestamptz not null default now()
);
create index expressions_brand on phg_know.expressions (brand_key);

-- rights: service_role reads and writes; nobody else
revoke all on all tables in schema phg_know from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema phg_know to service_role;
revoke truncate, references, trigger on all tables in schema phg_know from service_role;

-- Harmony's read-only gateway may read it (explicit, like phg_mix)
grant usage on schema phg_know to phg_harmony_reader;
grant select on all tables in schema phg_know to phg_harmony_reader;
do $$ declare t text; begin
  for t in select tablename from pg_tables where schemaname = 'phg_know' loop
    execute format('alter table phg_know.%I enable row level security', t);
    execute format('create policy harmony_read on phg_know.%I for select to phg_harmony_reader using (true)', t);
  end loop;
end $$;

insert into phg.harmony_table_access (schema_name, table_pattern, access, notes)
select 'phg_know', t, 'shared_read', 'product knowledge (shared, sourced; draft 09)' from unnest(array['sources','brand_profiles','expressions']) t
on conflict (schema_name, table_pattern) do nothing;

insert into phg.harmony_entities (key, label, entity_group, aliases, main_tables, scope, name_lookup) values
  ('know_brand','brand profile','Spirits','{brand story,brand history,how it is made,production details}','{phg_know.brand_profiles}','shared','{"table":"phg_know.brand_profiles","id":"key","name":"name","aliases":"aka"}'),
  ('know_expression','bottling details','Spirits','{tasting notes,aging,how long is it aged,additive free,barrels,proof}','{phg_know.expressions}','shared','{"table":"phg_know.expressions","id":"key","name":"name"}');
