-- PHG v12.4 · BETA ACCESS: Harmony + Atlas  ->  Harmony + Atlas + Menu (library + studio) + Financials + Cocktail 3D
-- Rob, 2026-10-06: "for the beta users add in the menu function the cocktail 3-D rendering function, the financial function".
-- Changes: the 'beta' surfaces line; 'cocktail' is also named for user + developer (they already see the Cocktail view;
-- naming it lets "view as beta" keep it). view_mode logic, memberships, invites: unchanged.
-- Pair: phg-access v11 (same list in MODE_SURFACES.beta, so "view as beta" matches). App: index.html v12.4.
-- Rollback: re-run the 2026-10-04 definition (beta = 'harmony','atlas'; no 'cocktail' anywhere).
CREATE OR REPLACE FUNCTION public.phg_auth_context(p_user_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'phg', 'pg_temp'
AS $function$
declare
  v_email text; v_confirmed boolean; v_admin boolean; v_beta boolean := false;
  v_memberships jsonb; v_invites jsonb; v_reason text; v_mode text;
begin
  select u.email, (u.email_confirmed_at is not null) into v_email, v_confirmed
    from auth.users u where u.id = p_user_id;
  if v_email is null then return jsonb_build_object('ok', false, 'reason', 'unknown_user'); end if;

  v_admin := phg.is_platform_admin(p_user_id);

  select coalesce(jsonb_agg(jsonb_build_object(
           'account_id', a.id, 'account_key', a.account_key, 'name', a.name,
           'role', m.role, 'status', m.status, 'tier', m.package_tier,
           'is_beta', m.is_beta, 'data_retention', m.data_retention,
           'timezone', a.default_timezone, 'currency', a.currency,
           'last_used_at', m.last_used_at) order by m.last_used_at desc nulls last), '[]'::jsonb),
         bool_or(m.is_beta)
    into v_memberships, v_beta
    from phg.account_memberships m
    join phg.accounts a on a.id = m.account_id
   where m.user_id = p_user_id and m.status = 'active';

  select coalesce(jsonb_agg(jsonb_build_object(
           'invite_id', i.id, 'account_id', i.account_id, 'account_name', a.name,
           'role', i.role, 'tier', i.package_tier, 'is_beta', i.is_beta,
           'expires_at', i.expires_at)), '[]'::jsonb)
    into v_invites
    from phg.account_invites i
    join phg.accounts a on a.id = i.account_id
   where lower(i.email) = lower(v_email) and i.status = 'pending' and i.expires_at > now();

  if jsonb_array_length(v_memberships) > 0 then v_reason := null;
  elsif jsonb_array_length(v_invites) > 0 and not v_confirmed then v_reason := 'email_not_confirmed';
  elsif jsonb_array_length(v_invites) > 0 then v_reason := 'invite_pending_claim';
  elsif v_admin then v_reason := 'platform_admin_no_tenant';
  else v_reason := 'no_membership_no_invite';
  end if;

  -- Platform admin wins: Rob keeps the developer view even if also flagged beta somewhere.
  v_mode := case when v_admin then 'developer'
                 when coalesce(v_beta,false) then 'beta'
                 when jsonb_array_length(v_memberships) > 0 then 'user'
                 else 'none' end;

  -- DEV-0025 (2026-10-04): beta = Harmony + Atlas only; everyone else also gets 'atlas'.
  -- v12.4 (2026-10-06, Rob): beta also gets Menu (library + studio), Financials and the Cocktail 3D view.
  return jsonb_build_object(
    'ok', true, 'user_id', p_user_id, 'email_confirmed', v_confirmed,
    'is_platform_admin', v_admin, 'is_beta', coalesce(v_beta,false),
    'view_mode', v_mode,
    'surfaces', case v_mode
        when 'developer' then jsonb_build_array('harmony','market','menu_library','menu_studio','financial','settings','dev','atlas','cocktail')
        when 'beta'      then jsonb_build_array('harmony','atlas','menu_library','menu_studio','financial','cocktail')
        when 'user'      then jsonb_build_array('harmony','market','menu_library','menu_studio','financial','settings','atlas','cocktail')
        else jsonb_build_array() end,
    'memberships', v_memberships, 'pending_invites', v_invites, 'access_reason', v_reason);
end
$function$;

-- verify:  select public.phg_auth_context('<a beta user id>')->'surfaces';
--   -> ["harmony","atlas","menu_library","menu_studio","financial","cocktail"]
