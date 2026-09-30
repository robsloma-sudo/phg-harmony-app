-- APPLIED 2026-09-29 as migration phg_mix_drink_styles (Rob: a style like Cadillac can itself have 150+ recipes).
-- drink (Margarita) -> style (Cadillac) -> any number of recipes. Backfill: one style per (drink, version label),
-- recipes linked, style reference = the drink's reference spec; then Difford's 10:3:2 was moved under Classic Daiquiri.
set local lock_timeout = '3s';
create table phg_mix.drink_styles (
  key text primary key, drink_key text not null references phg_mix.drinks(key) on delete cascade, name text not null,
  aka text[] not null default '{}',
  version_type text check (version_type in ('original','classic','modern_standard','traditional','regional','house',
      'happy_hour','premium','frozen','flavored','spicy','skinny','batch','zero_proof','bartender_signature','brand','style',
      'spirit_swap','other')),
  description text, reference_recipe_key text, sort int not null default 100,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), unique (drink_key, name));
create index drink_styles_drink on phg_mix.drink_styles (drink_key, sort);
alter table phg_mix.recipes add column style_key text references phg_mix.drink_styles(key) on delete set null;
create index recipes_style_rank on phg_mix.recipes (style_key, quality_score desc nulls last);
revoke all on phg_mix.drink_styles from public, anon, authenticated;
grant select, insert, update, delete on phg_mix.drink_styles to service_role;
grant select on phg_mix.drink_styles to phg_harmony_reader;
alter table phg_mix.drink_styles enable row level security;
create policy harmony_read on phg_mix.drink_styles for select to phg_harmony_reader using (true);
insert into phg.harmony_table_access (schema_name, table_pattern, access, notes)
values ('phg_mix','drink_styles','shared_read','styles of a drink (Classic, Tommy''s, Cadillac, Frozen...); recipes.style_key')
on conflict (schema_name, table_pattern) do nothing;
