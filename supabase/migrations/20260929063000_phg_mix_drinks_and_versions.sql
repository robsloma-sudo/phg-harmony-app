-- APPLIED 2026-09-29 as migration phg_mix_drinks_and_versions (Rob: catalog many recipes per cocktail -
-- classic, traditional, house, happy hour, Cadillac ...). Backfill of the 93 existing recipes was run separately
-- (79 drinks, 26 riffs linked to a parent, one reference spec per drink).
set local lock_timeout = '3s';
create table phg_mix.drinks (
  key text primary key, name text not null, aka text[] not null default '{}', family text,
  parent_key text references phg_mix.drinks(key) on delete set null, description text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now());
create index drinks_parent on phg_mix.drinks (parent_key);
create index drinks_name on phg_mix.drinks (lower(name));
alter table phg_mix.recipes
  add column drink_key text references phg_mix.drinks(key) on delete set null,
  add column version_type text check (version_type in ('original','classic','modern_standard','traditional','regional','house',
      'happy_hour','premium','frozen','flavored','spicy','skinny','batch','zero_proof','bartender_signature','brand','style',
      'spirit_swap','other')),
  add column version_label text,
  add column serve text check (serve in ('up','rocks','frozen','neat','highball','collins','hot','punch','other')),
  add column price_tier text check (price_tier in ('well','call','premium','top_shelf')),
  add column is_reference boolean not null default false;
create index recipes_drink on phg_mix.recipes (drink_key, version_type);
create unique index recipes_one_reference on phg_mix.recipes (drink_key) where is_reference;
revoke all on phg_mix.drinks from public, anon, authenticated;
grant select, insert, update, delete on phg_mix.drinks to service_role;
grant select on phg_mix.drinks to phg_harmony_reader;
alter table phg_mix.drinks enable row level security;
create policy harmony_read on phg_mix.drinks for select to phg_harmony_reader using (true);
insert into phg.harmony_table_access (schema_name, table_pattern, access, notes)
values ('phg_mix','drinks','shared_read','drink identities; recipes.drink_key groups every version of a drink')
on conflict (schema_name, table_pattern) do nothing;
