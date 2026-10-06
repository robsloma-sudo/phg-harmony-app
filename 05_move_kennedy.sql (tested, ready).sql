-- PHG 2026-10-06 · Move Kennedy into her own private workspace (Rob: "Yes").
-- She keeps beta access (Harmony, Atlas, Menu, Financials, Cocktail) but in her own, empty workspace on the
-- Call package; she stops seeing PHG Ops Test. Her PHG Ops Test membership is DISABLED, not deleted.
-- Her own data is per-login (4 chat turns, 2 sessions) and is not touched.
-- Undo: update phg.account_memberships set status='active' where user_id=<kennedy> and account_id=<PHG Ops Test>;
--       update phg.account_memberships set status='disabled' where user_id=<kennedy> and account_id=<her workspace>;
do $$
declare
  v_user uuid; v_ops uuid; v_ws uuid; v_started timestamptz; v_rob uuid;
begin
  select id into v_user from auth.users where lower(email) = 'kennedymarieburke@gmail.com';
  select id into v_ops  from phg.accounts where account_key = 'phg_ops_test';
  select user_id into v_rob from phg.platform_admins order by user_id limit 1;
  if v_user is null or v_ops is null then raise exception 'kennedy or PHG Ops Test not found'; end if;

  v_ws := phg.beta_workspace_for(v_rob, 'kennedymarieburke@gmail.com', 'Kennedy');

  select beta_started_at into v_started from phg.account_memberships where user_id = v_user and account_id = v_ops;

  insert into phg.account_memberships (account_id, user_id, role, status, display_name, package_tier, is_beta, beta_started_at)
  values (v_ws, v_user, 'editor', 'active', 'Kennedy', 'call', true, coalesce(v_started, now()))
  on conflict (account_id, user_id) do update set status = 'active', role = 'editor', package_tier = 'call', is_beta = true;

  update phg.account_memberships
     set status = 'disabled',
         metadata = metadata || jsonb_build_object('disabled_reason', 'moved to own beta workspace', 'moved_to', v_ws, 'moved_at', now()),
         updated_at = now()
   where user_id = v_user and account_id = v_ops and status = 'active';

  perform phg.log_auth(v_rob, v_ws, 'beta_member_moved', jsonb_build_object('user', v_user, 'from', v_ops, 'to', v_ws));
end $$;
