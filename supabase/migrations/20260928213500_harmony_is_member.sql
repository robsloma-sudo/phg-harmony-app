-- Narrow membership check for phg-harmony-inbox: answers only yes/no for one
-- (user, account) pair, so service_role needs no SELECT on account_memberships.
create or replace function phg.harmony_is_member(p_user uuid, p_account uuid)
returns boolean
language sql
stable
security definer
set search_path = phg, pg_temp
as $$
  select exists (
    select 1 from phg.account_memberships
    where user_id = p_user and account_id = p_account and status = 'active'
  );
$$;
revoke all on function phg.harmony_is_member(uuid, uuid) from public, anon, authenticated;
grant execute on function phg.harmony_is_member(uuid, uuid) to service_role;
