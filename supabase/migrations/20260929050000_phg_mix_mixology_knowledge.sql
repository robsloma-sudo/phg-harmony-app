-- DRAFT 08 v2: PHG mixology knowledge base (shared library) with credibility and quality scoring.
-- Rob 2026-09-29: catalog every recipe, syrup/infusion, advanced and molecular technique and flavor pairing in
-- Supabase, and grade them by the quality of who stands behind them (credentials, known or not, influencer vs
-- legitimate writer). Scoring rules: handoff/agents/MIXOLOGY_CREDIBILITY_SCORING.md. Data format:
-- handoff/agents/MIXOLOGY_DATA_CONTRACT.md. Loaded from data/mixology/*.jsonl by the lead developer only.
--
-- v2 = safety review round 1 (score 76) fixes:
--   B1 no call to the global phg.harmony_apply_table_access() (it re-grants and adds policies on OTHER tables that
--      this rollback cannot undo); phg_mix access is granted explicitly here
--   B2 preps.storage -> storage_note (the gateway's word filter blocks "storage")
--   B3 create schema (not "if not exists") + refuse to run if phg_mix access rows or mix_* entities already exist
--   B4 complete, transactional rollback (below)
--   attributions: on delete restrict, unique nulls not distinct; recipe_variants unique; creator_key soft link;
--   category checks; FK / reverse-lookup indexes; grant hygiene; narrower entity aliases (no collision with the
--   house recipe/prep entities).
--
-- Scores (computed by the loader from the scoring rules, never typed in by hand):
--   sources / creators: cred_score 0-100, cred_grade A-E, cred_parts {credentials, standing, recognition, rigor,
--     independence, track_record}, cred_evidence [{part, points, url, note}], reach (followers etc., never scored),
--     source_kind / creator_kind (canon_author, pro_bartender, bar, publication, reference_site, technical_creator,
--     lifestyle_influencer, brand, academic, historian)
--   recipes / preps / techniques / pairings: quality_score 0-100, quality_grade A-E, quality_parts {best_backer,
--     agreement, completeness, verification}, verification (page_verified | excerpt | unverified)
--
-- Rollback (tested with the forward script inside begin ... rollback before applying):
--   begin;
--   set local lock_timeout = '3s';
--   -- library data is rebuilt from data/mixology/*.jsonl; if anything was hand-edited, pg_dump -n phg_mix first
--   delete from phg.harmony_paths where from_entity like 'mix\_%' or to_entity like 'mix\_%';
--   delete from phg.harmony_table_access where schema_name = 'phg_mix';
--   delete from phg.harmony_entities where key in ('mix_recipe','mix_prep','mix_technique','mix_source','mix_creator','mix_pairing');
--   drop schema phg_mix cascade;
--   select (select count(*) from pg_namespace where nspname = 'phg_mix') = 0 as schema_gone,
--          (select count(*) from phg.harmony_table_access where schema_name = 'phg_mix') = 0 as access_gone,
--          (select count(*) from phg.harmony_entities where key like 'mix\_%') = 0 as entities_gone;
--   commit;

set local lock_timeout = '3s';

do $$ begin
  if exists (select 1 from phg.harmony_table_access where schema_name = 'phg_mix')
     or exists (select 1 from phg.harmony_entities where key like 'mix\_%') then
    raise exception '08: phg_mix access rows or mix_* entities already exist';
  end if;
end $$;

create schema phg_mix;
revoke all on schema phg_mix from public, anon, authenticated;
grant usage on schema phg_mix to service_role;

create table phg_mix.sources (
  key            text primary key check (key ~ '^src_[a-z0-9_]+$'),
  title          text not null,
  kind           text not null check (kind in ('book','site','publication','bartender','creator','brand','academic','database')),
  source_kind    text check (source_kind in ('canon_author','pro_bartender','bar','publication','reference_site','technical_creator','lifestyle_influencer','brand','academic','historian')),
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
  reach          jsonb not null default '{}',
  cred_score     smallint check (cred_score between 0 and 100),
  cred_grade     text check (cred_grade in ('A','B','C','D','E')),
  cred_parts     jsonb not null default '{}',
  cred_evidence  jsonb not null default '[]',
  public_source_id uuid references public.sources(id) on delete set null,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table phg_mix.creators (
  key            text primary key check (key ~ '^cr_[a-z0-9_]+$'),
  name           text not null,
  role           text check (role in ('bartender','author','creator','scientist','chef','historian','owner')),
  creator_kind   text check (creator_kind in ('canon_author','pro_bartender','bar','publication','reference_site','technical_creator','lifestyle_influencer','brand','academic','historian')),
  tier           smallint check (tier between 1 and 5),
  affiliations   text[] not null default '{}',
  home_url       text,
  platforms      jsonb not null default '[]',
  known_for      text[] not null default '{}',
  signature_drinks text[] not null default '{}',
  techniques     text[] not null default '{}',
  awards         jsonb not null default '[]',
  reach          jsonb not null default '{}',
  cred_score     smallint check (cred_score between 0 and 100),
  cred_grade     text check (cred_grade in ('A','B','C','D','E')),
  cred_parts     jsonb not null default '{}',
  cred_evidence  jsonb not null default '[]',
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
  creator_key    text,                      -- soft link (like prep_key): the creator may arrive in a later batch
  origin_bar     text,
  origin_city    text,
  method         text check (method in ('shake','stir','build','throw','swizzle','blend','dry_shake','whip','clarified','carbonated','layer','other')),
  steps          text[] not null default '{}',
  dilution_target_pct numeric,
  glass          text,
  ice            text,
  garnish        text,
  abv_est        numeric,
  notes          text,
  confidence     text not null check (confidence in ('high','medium','low')),
  verification   text not null default 'unverified' check (verification in ('page_verified','excerpt','unverified')),
  quality_score  smallint check (quality_score between 0 and 100),
  quality_grade  text check (quality_grade in ('A','B','C','D','E')),
  quality_parts  jsonb not null default '{}',
  cocktail_spec_id uuid references public.cocktail_specs(id) on delete set null,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index recipes_family on phg_mix.recipes (family);
create index recipes_name_lower on phg_mix.recipes (lower(name));
create index recipes_grade on phg_mix.recipes (quality_grade);
create index recipes_cocktail_spec_id on phg_mix.recipes (cocktail_spec_id) where cocktail_spec_id is not null;

create table phg_mix.preps (
  key            text primary key check (key ~ '^pr_[a-z0-9_]+$'),
  name           text not null,
  category       text not null check (category in ('syrup','rich_syrup','flavored_syrup','cordial','infusion','shrub','oleo','tincture','bitters','fat_wash','milk_punch','clarified_juice','acid_blend','super_juice','foam','gel','air','caviar','brine','salt_solution','other')),
  yield          jsonb,
  ratio_note     text,
  process        text[] not null default '{}',
  params         jsonb not null default '{}',
  equipment      text[] not null default '{}',
  shelf_life_days numeric,
  storage_note   text,
  confidence     text not null check (confidence in ('high','medium','low')),
  verification   text not null default 'unverified' check (verification in ('page_verified','excerpt','unverified')),
  quality_score  smallint check (quality_score between 0 and 100),
  quality_grade  text check (quality_grade in ('A','B','C','D','E')),
  quality_parts  jsonb not null default '{}',
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
  source_key     text references phg_mix.sources(key) on delete restrict,
  tier           smallint check (tier between 1 and 5),
  url            text,
  unique nulls not distinct (recipe_key, name, source_key)
);
create index recipe_variants_recipe_key on phg_mix.recipe_variants (recipe_key);

create table phg_mix.techniques (
  key            text primary key check (key ~ '^tq_[a-z0-9_]+$'),
  name           text not null,
  category       text not null check (category in ('classic','dilution','clarification','infusion','carbonation','temperature','texture','spherification','fermentation','acid_adjustment','distillation','aroma','ice','balance')),
  what_it_does   text,
  when_to_use    text,
  steps          text[] not null default '{}',
  params         jsonb not null default '{}',
  equipment      text[] not null default '{}',
  safety         text[] not null default '{}',
  pitfalls       text[] not null default '{}',
  confidence     text not null check (confidence in ('high','medium','low')),
  verification   text not null default 'unverified' check (verification in ('page_verified','excerpt','unverified')),
  quality_score  smallint check (quality_score between 0 and 100),
  quality_grade  text check (quality_grade in ('A','B','C','D','E')),
  quality_parts  jsonb not null default '{}',
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create table phg_mix.pairings (
  key            text primary key check (key ~ '^pa_[a-z0-9_]+$'),
  relationship   text not null check (relationship in ('classic_pairing','complementary','contrasting','bridge','shared_compounds','regional_tradition')),
  context        jsonb not null default '{}',
  rationale      text,
  confidence     text not null check (confidence in ('high','medium','low')),
  verification   text not null default 'unverified' check (verification in ('page_verified','excerpt','unverified')),
  quality_score  smallint check (quality_score between 0 and 100),
  quality_grade  text check (quality_grade in ('A','B','C','D','E')),
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
  source_key     text not null references phg_mix.sources(key) on delete restrict,
  url            text,
  locator        text,
  tier           smallint check (tier between 1 and 5),
  unique nulls not distinct (record_type, record_key, source_key, url)
);
create index attributions_record on phg_mix.attributions (record_type, record_key);
create index attributions_source_key on phg_mix.attributions (source_key);

create table phg_mix.uses (
  from_type      text not null check (from_type in ('recipe','technique','prep')),
  from_key       text not null,
  to_type        text not null check (to_type in ('prep','technique','recipe')),
  to_key         text not null,
  primary key (from_type, from_key, to_type, to_key)
);
create index uses_to on phg_mix.uses (to_type, to_key);

-- rights: service_role reads and writes; nobody else
revoke all on all tables in schema phg_mix from public, anon, authenticated;
revoke all on all sequences in schema phg_mix from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema phg_mix to service_role;
revoke truncate, references, trigger on all tables in schema phg_mix from service_role;
grant usage, select on all sequences in schema phg_mix to service_role;

-- Harmony's read-only gateway may read the library: explicit grants and a reader-only policy on phg_mix tables
-- (deliberately NOT phg.harmony_apply_table_access(), which touches other tables)
grant usage on schema phg_mix to phg_harmony_reader;
grant select on all tables in schema phg_mix to phg_harmony_reader;
do $$ declare t text; begin
  for t in select tablename from pg_tables where schemaname = 'phg_mix' loop
    execute format('alter table phg_mix.%I enable row level security', t);
    execute format('create policy harmony_read on phg_mix.%I for select to phg_harmony_reader using (true)', t);
  end loop;
end $$;

insert into phg.harmony_table_access (schema_name, table_pattern, access, notes)
select 'phg_mix', t, 'shared_read', 'mixology library (shared knowledge, draft 08)' from unnest(array[
  'sources','creators','recipes','recipe_lines','recipe_variants','preps','prep_lines','techniques','pairings',
  'pairing_members','attributions','uses']) t
on conflict (schema_name, table_pattern) do nothing;

insert into phg.harmony_entities (key, label, entity_group, aliases, main_tables, scope, name_lookup) values
  ('mix_recipe','library cocktail recipe','Mixology','{library recipe,mixology recipe,classic spec,cocktail library}','{phg_mix.recipes,phg_mix.recipe_lines}','shared','{"table":"phg_mix.recipes","id":"key","name":"name","aliases":"aka"}'),
  ('mix_prep','library prep','Mixology','{library prep,mixology prep,library syrup}','{phg_mix.preps,phg_mix.prep_lines}','shared','{"table":"phg_mix.preps","id":"key","name":"name"}'),
  ('mix_technique','mixology technique','Mixology','{technique,molecular,clarification,spherification,foam,carbonation}','{phg_mix.techniques}','shared','{"table":"phg_mix.techniques","id":"key","name":"name"}'),
  ('mix_source','cocktail source','Mixology','{cocktail book,cocktail reference,recipe source}','{phg_mix.sources}','shared','{"table":"phg_mix.sources","id":"key","name":"title"}'),
  ('mix_creator','bartender','Mixology','{bartender,cocktail creator,influencer,cocktail author}','{phg_mix.creators}','shared','{"table":"phg_mix.creators","id":"key","name":"name"}'),
  ('mix_pairing','flavor pairing','Mixology','{pairing,goes with,flavor match}','{phg_mix.pairings,phg_mix.pairing_members}','shared','{}');
