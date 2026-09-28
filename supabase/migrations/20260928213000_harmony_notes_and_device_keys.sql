-- Harmony notes log + personal device keys for the iPhone Action-button Shortcut.
-- Requested by Rob 2026-09-28 ("Now let's build the action shortcut button").
--
-- Access model: both tables are reached ONLY through the phg-harmony-inbox edge
-- function (service_role). RLS is enabled with no policies, so anon/authenticated
-- clients cannot read or write them directly. Device keys are stored as SHA-256
-- hashes; the plaintext key is shown to the user once and never stored.

create table if not exists phg.harmony_notes (
  id          uuid primary key default gen_random_uuid(),
  account_id  uuid references phg.accounts(id) on delete cascade,
  user_id     uuid not null,
  kind        text not null default 'note' check (kind in ('note','task','idea','reminder')),
  body        text not null check (length(body) between 1 and 4000),
  tags        text[] not null default '{}',
  due_at      timestamptz,
  done        boolean not null default false,
  source      text not null default 'app' check (source in ('app','shortcut')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists harmony_notes_user_created_idx on phg.harmony_notes (user_id, created_at desc);
create index if not exists harmony_notes_account_created_idx on phg.harmony_notes (account_id, created_at desc);

create table if not exists phg.harmony_device_keys (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null,
  account_id   uuid references phg.accounts(id) on delete cascade,
  name         text not null default 'iPhone Shortcut' check (length(name) <= 80),
  key_hash     text not null unique check (key_hash ~ '^[0-9a-f]{64}$'),
  key_hint     text not null,          -- last 4 characters, to recognise a key in the list
  created_at   timestamptz not null default now(),
  last_used_at timestamptz,
  revoked_at   timestamptz
);
create index if not exists harmony_device_keys_user_idx on phg.harmony_device_keys (user_id);

alter table phg.harmony_notes enable row level security;
alter table phg.harmony_device_keys enable row level security;

revoke all on phg.harmony_notes from anon, authenticated;
revoke all on phg.harmony_device_keys from anon, authenticated;
grant select, insert, update, delete on phg.harmony_notes to service_role;
grant select, insert, update on phg.harmony_device_keys to service_role;
