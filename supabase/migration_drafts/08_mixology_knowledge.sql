-- DRAFT 08 (not applied): PHG mixology knowledge base.
-- Rob 2026-09-29: "make an agent who becomes the best at cocktail recipes and its syrups and infusions and advanced
-- mixology and molecular gastronomy ... catalog them at Supabase ... catalog the best resources versus social media
-- resources and influencers ... categorize all of them separately ... flavor pairings".
--
-- What this adds (new schema phg_mix, shared knowledge: the same for every project, per the isolation rule the
-- LIBRARY is shared and each project's own recipes stay in phg.recipe_*):
--   sources      every resource, tiered 1-5 (1 canon book, 2 pro site/publication, 3 named bartender/bar,
--                4 social creator, 5 brand) with an access and rights note
--   creators     people (bartenders, authors, creators, scientists)
--   recipes      drinks: family (Cocktail Codex roots), era, origin, method, glass, garnish, confidence
--   recipe_lines ingredients with amount/unit/ml and an optional prep
--   recipe_variants  named variations and whose they are
--   preps        syrups, cordials, infusions, shrubs, fat washes, clarifications, foams, gels, spheres...
--   prep_lines
--   techniques   classic to molecular, with params, equipment, safety, pitfalls
--   pairings + pairing_members   flavor pairings with relationship type (staging; promoted into phg_flavor later)
--   attributions every record's sources (record_type, record_key, source_key, url, locator, tier)
--   uses         links: recipe -> prep, recipe -> technique, technique -> example recipe
-- Loaded from data/mixology/*.jsonl (format: handoff/agents/MIXOLOGY_DATA_CONTRACT.md) by the lead developer,
-- idempotently (insert ... on conflict (key) do update), never by the research agents.
--
-- Access: schema usage and table rights for service_role only (no anon/authenticated). Every table is registered in
-- phg.harmony_table_access as shared_read, so Harmony's read-only gateway (phg_harmony_query) can answer from it; RLS
-- is enabled with a read policy for phg_harmony_reader only.
--
-- Rollback:
--   delete from phg.harmony_table_access where schema_name = 'phg_mix';
--   delete from phg.harmony_entities where key in ('mix_recipe','mix_prep','mix_technique','mix_source','mix_creator','mix_pairing');
--   drop schema phg_mix cascade;
--   verify: select count(*) = 0 from pg_namespace where nspname = 'phg_mix';

set local lock_timeout = '3s';

create schema if not exists phg_mix;
revoke all on schema phg_mix from public, anon, authenticated;
grant usage on schema phg_mix to service_role;

create table phg_mix.sources (
  key            text primary key check (key ~ '^src_[a-z0-9_]+$'),
  title          text not null,
  kind           text not null check (kind in ('book','site','publication','bartender','creator','brand','academic','database')),
  tier           smallint not null check (tier between 1 and 5),
  authors        text[] not null default '{}',
  publisher      text,
  year           int,
  url            text,
  platforms      jsonb not null default '[]',
  focus          text[] not null default '{}',
  notable_for    text,
  access         text check (access in ('open','paywalled','print_only','login')),
  rights_note    text,
  recipe_count_estimate int,
  public_source_id uuid references public.sources(id) on delete set null,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table phg_mix.creators (
  key            text primary key check (key ~ '^cr_[a-z0-9_]+$'),
  name           text not null,
  role           text check (role in ('bartender','author','creator','scientist','chef','historian','owner')),
  tier           smallint check (tier between 1 and 5),
  affiliations   text[] not null default '{}',
  home_url       text,
  platforms      jsonb not null default '[]',
  known_for      text[] not null default '{}',
  signature_drinks text[] not null default '{}',
  techniques     text[] not null default '{}',
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table phg_mix.recipes (
  key            text primary key check (key ~ '^rx_[a-z0-9_]+$'),
  name           text not null,
  aka            text[] not null default '{}',
  family         text not null check (family in ('old_fashioned','martini','daiquiri','sidecar','highball','flip','other')),
  subfamily      text,
  style_tags     text[] not null default '{}',
  base_spirits   text[] not null default '{}',
  era            text check (era in ('pre-prohibition','prohibition','tiki','post-war','disco','modern_classic','contemporary')),
  year_created   int,
  creator_key    text references phg_mix.creators(key) on delete set null,
  origin_bar     text,
  origin_city    text,
  method         text check (method in ('shake','stir','build','throw','swizzle','blend','dry_shake','whip','clarified','carbonated','layer','other')),
  steps          text[] not null default '{}',
  dilution_target_pct numeric,
  glass          text,
  ice            text,
  garnish        text,
  abv_est        numeric,
  confidence     text not null check (confidence in ('high','medium','low')),
  cocktail_spec_id uuid references public.cocktail_specs(id) on delete set null,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index recipes_family on phg_mix.recipes (family);
create index recipes_name_lower on phg_mix.recipes (lower(name));

create table phg_mix.preps (
  key            text primary key check (key ~ '^pr_[a-z0-9_]+$'),
  name           text not null,
  category       text not null,
  yield          jsonb,
  ratio_note     text,
  process        text[] not null default '{}',
  params         jsonb not null default '{}',
  equipment      text[] not null default '{}',
  shelf_life_days numeric,
  storage        text,
  confidence     text not null check (confidence in ('high','medium','low')),
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table phg_mix.recipe_lines (
  id             bigint generated always as identity primary key,
  recipe_key     text not null references phg_mix.recipes(key) on delete cascade,
  position       smallint not null,
  ingredient     text not null,
  amount         numeric,
  unit           text,
  ml             numeric,
  prep_key       text,                      -- soft link: the prep may arrive in a later batch
  note           text,
  unique (recipe_key, position)
);
create index recipe_lines_ingredient on phg_mix.recipe_lines (lower(ingredient));

create table phg_mix.prep_lines (
  id             bigint generated always as identity primary key,
  prep_key       text not null references phg_mix.preps(key) on delete cascade,
  position       smallint not null,
  ingredient     text not null,
  amount         numeric,
  unit           text,
  note           text,
  unique (prep_key, position)
);

create table phg_mix.recipe_variants (
  id             bigint generated always as identity primary key,
  recipe_key     text not null references phg_mix.recipes(key) on delete cascade,
  name           text not null,
  change         text,
  source_key     text references phg_mix.sources(key) on delete set null
);

create table phg_mix.techniques (
  key            text primary key check (key ~ '^tq_[a-z0-9_]+$'),
  name           text not null,
  category       text not null,
  what_it_does   text,
  when_to_use    text,
  steps          text[] not null default '{}',
  params         jsonb not null default '{}',
  equipment      text[] not null default '{}',
  safety         text[] not null default '{}',
  pitfalls       text[] not null default '{}',
  confidence     text not null check (confidence in ('high','medium','low')),
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table phg_mix.pairings (
  key            text primary key check (key ~ '^pa_[a-z0-9_]+$'),
  relationship   text not null check (relationship in ('classic_pairing','complementary','contrasting','bridge','shared_compounds','regional_tradition')),
  context        jsonb not null default '{}',
  rationale      text,
  confidence     text not null check (confidence in ('high','medium','low')),
  created_at     timestamptz not null default now()
);
create table phg_mix.pairing_members (
  pairing_key    text not null references phg_mix.pairings(key) on delete cascade,
  subject        text not null,
  kind           text not null default 'ingredient',
  primary key (pairing_key, subject)
);
create index pairing_members_subject on phg_mix.pairing_members (lower(subject));

create table phg_mix.attributions (
  id             bigint generated always as identity primary key,
  record_type    text not null check (record_type in ('recipe','prep','technique','pairing','creator')),
  record_key     text not null,
  source_key     text not null references phg_mix.sources(key) on delete cascade,
  url            text,
  locator        text,
  tier           smallint check (tier between 1 and 5),
  unique (record_type, record_key, source_key, url)
);
create index attributions_record on phg_mix.attributions (record_type, record_key);

create table phg_mix.uses (
  from_type      text not null check (from_type in ('recipe','technique','prep')),
  from_key       text not null,
  to_type        text not null check (to_type in ('prep','technique','recipe')),
  to_key         text not null,
  primary key (from_type, from_key, to_type, to_key)
);

-- rights: service_role reads and writes; nobody else
revoke all on all tables in schema phg_mix from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema phg_mix to service_role;
grant usage, select on all sequences in schema phg_mix to service_role;
do $$ declare t text; begin
  for t in select tablename from pg_tables where schemaname = 'phg_mix' loop
    execute format('alter table phg_mix.%I enable row level security', t);
  end loop;
end $$;

-- Harmony's read-only gateway may read the library (shared_read; the apply function grants SELECT and adds the
-- reader-only policy)
grant usage on schema phg_mix to phg_harmony_reader;
insert into phg.harmony_table_access (schema_name, table_pattern, access, notes)
select 'phg_mix', t, 'shared_read', 'mixology library (shared knowledge)' from unnest(array[
  'sources','creators','recipes','recipe_lines','recipe_variants','preps','prep_lines','techniques','pairings',
  'pairing_members','attributions','uses']) t
on conflict do nothing;
select phg.harmony_apply_table_access();

insert into phg.harmony_entities (key, label, entity_group, aliases, main_tables, scope, name_lookup) values
  ('mix_recipe','cocktail recipe','Mixology','{recipe,spec,drink,cocktail,classic}','{phg_mix.recipes,phg_mix.recipe_lines}','shared','{"table":"phg_mix.recipes","id":"key","name":"name","aliases":"aka"}'),
  ('mix_prep','prep','Mixology','{syrup,cordial,infusion,shrub,oleo,tincture,fat wash,clarified}','{phg_mix.preps,phg_mix.prep_lines}','shared','{"table":"phg_mix.preps","id":"key","name":"name"}'),
  ('mix_technique','technique','Mixology','{method,molecular,clarification,spherification,foam,carbonation}','{phg_mix.techniques}','shared','{"table":"phg_mix.techniques","id":"key","name":"name"}'),
  ('mix_source','cocktail source','Mixology','{book,resource,reference,site}','{phg_mix.sources}','shared','{"table":"phg_mix.sources","id":"key","name":"title"}'),
  ('mix_creator','bartender','Mixology','{creator,influencer,bartender,author}','{phg_mix.creators}','shared','{"table":"phg_mix.creators","id":"key","name":"name"}'),
  ('mix_pairing','flavor pairing','Mixology','{pairing,goes with,flavor match}','{phg_mix.pairings,phg_mix.pairing_members}','shared','{}')
on conflict (key) do nothing;
