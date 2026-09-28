DO $rehearse_main$
DECLARE
  r jsonb := '{}'; a jsonb := '{}'; b jsonb := '{}'; c jsonb := '{}'; v jsonb; res jsonb;
  t0 timestamptz; t1 timestamptz; acct text := 'ACC-CO-LED-03-25486'; orig_url text;
  cur_id uuid; cur2 uuid; cur_now uuid; secs jsonb; secs2 jsonb; secs4 jsonb; secs9 jsonb; items jsonb; item_x uuid;
  rem int; calls jsonb; lease_owner uuid := gen_random_uuid(); claimed timestamptz := clock_timestamp();
  e_state text; e_msg text; e_ctx text; e_det text;
BEGIN
  set local statement_timeout = '58s';
  t0 := clock_timestamp();
  BEGIN
    EXECUTE $rehearse_f3$-- PHG-036b: Rob's design scorecard as a hard gate (handoff/agents/MENU_DESIGN_SCORECARD.md).
-- A proposal carries its layout geometry; two design reviewers (design_critic, content_reviewer) score it per
-- criterion; phg_design_proposal_review refuses to approve unless EACH reviewer's average is above 80.

-- Review (PHG-026 round 3, SF10): the layout check treats a missing key as missing (coalesce), and the three
-- functions this file replaces are saved first; phg_rollback_design_score_gate_20260928() puts them back.

-- ---------- 0. save the definitions this migration replaces ----------
create table if not exists public.phg_backup_design_fn_defs_20260928 (
  signature text primary key, definition text not null, acl text, saved_at timestamptz not null default now());
alter table public.phg_backup_design_fn_defs_20260928 enable row level security;
revoke all on public.phg_backup_design_fn_defs_20260928 from anon, authenticated;
revoke insert, update, delete, truncate on public.phg_backup_design_fn_defs_20260928 from service_role;
insert into public.phg_backup_design_fn_defs_20260928 (signature, definition, acl)
select p.oid::regprocedure::text, pg_get_functiondef(p.oid), p.proacl::text
  from pg_proc p
 where p.oid in (to_regprocedure('public.phg_design_proposal_submit(uuid,jsonb,jsonb,jsonb,jsonb,text,bigint[],numeric,text[],boolean)'),
                 to_regprocedure('public.phg_design_proposal_review(uuid,boolean,text)'),
                 to_regprocedure('public.phg_design_status(uuid)'))
on conflict (signature) do nothing;
do $$ begin
  if (select count(*) from public.phg_backup_design_fn_defs_20260928) < 3 then
    raise exception 'expected 3 saved function definitions before replacing them';
  end if;
end $$;
-- Rollback: drops the new submit (11 args) and the score function, restores the three saved bodies, re-applies revokes
-- and the service_role grant each had (live 2026-09-28: postgres + service_role only).
-- The added columns (layout, review_scores) stay: nullable / defaulted, unused by the restored functions.
create or replace function public.phg_rollback_design_score_gate_20260928()
returns int language plpgsql set search_path to 'public', 'pg_temp' as $$
declare r record; n int := 0;
begin
  drop function if exists public.phg_design_proposal_submit(uuid,jsonb,jsonb,jsonb,jsonb,text,bigint[],numeric,text[],boolean,jsonb);
  drop function if exists public.phg_design_proposal_score(uuid,text,jsonb,jsonb,jsonb);
  for r in select signature, definition, acl from public.phg_backup_design_fn_defs_20260928 order by signature loop
    execute r.definition;
    execute format('revoke all on function %s from public, anon, authenticated', r.signature::regprocedure);
    if r.acl like '%service_role=X%' then
      execute format('grant execute on function %s to service_role', r.signature::regprocedure);
    end if;
    n := n + 1;
  end loop;
  return n;
end $$;
revoke all on function public.phg_rollback_design_score_gate_20260928() from public, anon, authenticated;

alter table phg.menu_design_proposals
  add column if not exists layout jsonb,
  add column if not exists review_scores jsonb not null default '{}'::jsonb;

-- submit gains p_layout (geometry: page, margins, grid, palette, type, elements)
drop function if exists public.phg_design_proposal_submit(uuid,jsonb,jsonb,jsonb,jsonb,text,bigint[],numeric,text[],boolean);
create or replace function public.phg_design_proposal_submit(p_task_id uuid, p_doc jsonb, p_options jsonb default null,
  p_changes jsonb default null, p_previews jsonb default null, p_reasoning text default null,
  p_evidence_document_ids bigint[] default null, p_confidence numeric default null, p_risk_flags text[] default '{}',
  p_needs_input boolean default false, p_layout jsonb default null)
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_t phg.menu_design_tasks%rowtype; v_chk jsonb; v_ver int; v_id uuid; v_status text;
begin
  select * into v_t from phg.menu_design_tasks where id = p_task_id for update;
  if not found then raise exception 'design task not found'; end if;
  if v_t.status in ('applied','cancelled') then raise exception 'task is %', v_t.status; end if;
  v_chk := case when p_needs_input then jsonb_build_object('ok', true, 'problems', '[]'::jsonb, 'needs_input', true)
                else public.phg_design_doc_check(p_doc, v_t.base_doc, v_t.inputs) end;
  if not p_needs_input and (p_layout is null or coalesce(jsonb_typeof(p_layout->'elements'), '') <> 'array'
                            or coalesce(jsonb_typeof(p_layout->'page'), '') <> 'object') then
    v_chk := jsonb_set(v_chk, '{ok}', 'false'::jsonb);
    v_chk := jsonb_set(v_chk, '{problems}', coalesce(v_chk->'problems','[]'::jsonb) || '["layout geometry missing (page + elements required by the scorecard)"]'::jsonb);
  end if;
  v_status := case when p_needs_input then 'needs_input' when (v_chk->>'ok')::boolean then 'submitted' else 'auto_rejected' end;
  select coalesce(max(version), 0) + 1 into v_ver from phg.menu_design_proposals where task_id = p_task_id;
  update phg.menu_design_proposals set status = 'superseded' where task_id = p_task_id and status in ('submitted','needs_input');
  insert into phg.menu_design_proposals (task_id, version, doc, options, changes, previews, reasoning, evidence_document_ids,
    confidence, risk_flags, check_result, status, layout)
  values (p_task_id, v_ver, coalesce(p_doc, '{}'::jsonb), p_options, p_changes, p_previews, p_reasoning, p_evidence_document_ids,
    p_confidence, coalesce(p_risk_flags, '{}'), v_chk, v_status, p_layout)
  returning id into v_id;
  update phg.menu_design_tasks set status = case v_status when 'needs_input' then 'needs_input' when 'submitted' then 'proposed' else 'in_progress' end,
    updated_at = now() where id = p_task_id;
  return jsonb_build_object('status', v_status, 'proposal_id', v_id, 'version', v_ver, 'check', v_chk);
end $$;

-- A reviewer records its scores. Keys per reviewer follow the scorecard; each 0-100.
create or replace function public.phg_design_proposal_score(p_proposal_id uuid, p_reviewer text, p_scores jsonb,
  p_fixes jsonb default null, p_notes jsonb default null)
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_keys text[]; v_avg numeric; v_pr phg.menu_design_proposals%rowtype; k text;
begin
  v_keys := case p_reviewer when 'design_critic' then array['1','2','3','4','5','6','7','10']
                            when 'content_reviewer' then array['3','5','8','9','10']
                            when 'accuracy_reviewer' then array['10','11','12','13','14'] end;
  if v_keys is null then raise exception 'reviewer must be design_critic, content_reviewer or accuracy_reviewer'; end if;
  foreach k in array v_keys loop
    if not coalesce(p_scores ? k, false) or coalesce(jsonb_typeof(p_scores->k), '') <> 'number' or (p_scores->>k)::numeric not between 0 and 100 then
      raise exception 'score % missing or not 0-100', k; end if;
  end loop;
  select * into v_pr from phg.menu_design_proposals where id = p_proposal_id for update;
  if not found then raise exception 'proposal not found'; end if;
  if v_pr.status <> 'submitted' then raise exception 'proposal is %', v_pr.status; end if;
  select round(avg((p_scores->>x)::numeric), 1) into v_avg from unnest(v_keys) x;
  update phg.menu_design_proposals
     set review_scores = review_scores || jsonb_build_object(p_reviewer, jsonb_build_object(
           'scores', (select jsonb_object_agg(x, p_scores->x) from unnest(v_keys) x), 'average', v_avg,
           'fixes', coalesce(p_fixes, '[]'::jsonb), 'notes', p_notes, 'at', now()))
   where id = p_proposal_id;
  return jsonb_build_object('reviewer', p_reviewer, 'average', v_avg, 'passes', v_avg > 80);
end $$;

-- Review: approval now also needs both reviewers' averages above 80.
create or replace function public.phg_design_proposal_review(p_proposal_id uuid, p_approve boolean, p_note text default null)
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_pr phg.menu_design_proposals%rowtype; v_t phg.menu_design_tasks%rowtype; v_chk jsonb; v_c numeric; v_m numeric; v_a numeric;
begin
  select * into v_pr from phg.menu_design_proposals where id = p_proposal_id for update;
  if not found then raise exception 'proposal not found'; end if;
  if v_pr.status <> 'submitted' then raise exception 'proposal is %', v_pr.status; end if;
  select * into v_t from phg.menu_design_tasks where id = v_pr.task_id for update;
  if p_approve then
    v_chk := public.phg_design_doc_check(v_pr.doc, v_t.base_doc, v_t.inputs);
    if not (v_chk->>'ok')::boolean then
      update phg.menu_design_proposals set status = 'auto_rejected', check_result = v_chk, reviewed_at = now(), review_note = p_note where id = v_pr.id;
      return jsonb_build_object('status','auto_rejected','check',v_chk);
    end if;
    v_c := (v_pr.review_scores->'design_critic'->>'average')::numeric;
    v_m := (v_pr.review_scores->'content_reviewer'->>'average')::numeric;
    v_a := (v_pr.review_scores->'accuracy_reviewer'->>'average')::numeric;
    if v_c is null or v_m is null or v_a is null or v_c <= 80 or v_m <= 80 or v_a <= 80 then
      return jsonb_build_object('status','blocked_by_score_gate','design_critic',v_c,'content_reviewer',v_m,'accuracy_reviewer',v_a,
        'rule','each reviewer average must be above 80 (MENU_DESIGN_SCORECARD.md)');
    end if;
  end if;
  update phg.menu_design_proposals set status = case when p_approve then 'approved' else 'rejected' end,
    reviewed_at = now(), review_note = p_note where id = v_pr.id;
  update phg.menu_design_tasks set status = case when p_approve then 'approved' else 'in_progress' end, updated_at = now()
   where id = v_t.id;
  return jsonb_build_object('status', case when p_approve then 'approved' else 'rejected' end, 'proposal_id', v_pr.id,
                            'design_critic', v_c, 'content_reviewer', v_m);
end $$;

-- The app sees the scores and fixes (not the raw geometry).
create or replace function public.phg_design_status(p_menu_project_id uuid)
returns jsonb language sql stable security definer set search_path to 'public', 'pg_temp' as $$
  select jsonb_build_object('tasks', coalesce(jsonb_agg(jsonb_build_object(
    'task_id', t.id, 'status', t.status, 'source', t.source, 'source_detail', t.source_detail, 'request', t.request,
    'created_at', t.created_at,
    'proposals', (select coalesce(jsonb_agg(jsonb_build_object('proposal_id', p.id, 'version', p.version, 'status', p.status,
                    'reasoning', p.reasoning, 'risk_flags', p.risk_flags, 'problems', p.check_result->'problems',
                    'scores', jsonb_build_object('design_critic', p.review_scores->'design_critic'->'average',
                                                 'content_reviewer', p.review_scores->'content_reviewer'->'average',
                                                 'accuracy_reviewer', p.review_scores->'accuracy_reviewer'->'average'),
                    'changes', p.changes, 'previews', p.previews, 'created_at', p.created_at) order by p.version desc), '[]'::jsonb)
                  from phg.menu_design_proposals p where p.task_id = t.id)) order by t.created_at desc), '[]'::jsonb))
  from (select * from phg.menu_design_tasks where menu_project_id = p_menu_project_id order by created_at desc limit 30) t
$$;

revoke all on function public.phg_design_proposal_submit(uuid,jsonb,jsonb,jsonb,jsonb,text,bigint[],numeric,text[],boolean,jsonb),
  public.phg_design_proposal_score(uuid,text,jsonb,jsonb,jsonb), public.phg_design_proposal_review(uuid,boolean,text),
  public.phg_design_status(uuid) from public, anon, authenticated;
$rehearse_f3$;
  EXCEPTION WHEN others THEN 
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
    RAISE EXCEPTION 'REHEARSAL %', r || jsonb_build_object('stage','file3','sqlstate',e_state,'error',e_msg,'detail',e_det,'context',right(e_ctx, 600),'ms',round(extract(epoch from clock_timestamp()-t0)*1000));
  END;
  r := r || jsonb_build_object('file3_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  BEGIN
    r := r || jsonb_build_object('after_migration', jsonb_build_object('fns', (select jsonb_agg(p.oid::regprocedure::text order by 1) from pg_proc p where p.proname in ('phg_design_proposal_submit','phg_design_proposal_score','phg_design_proposal_review','phg_design_status')),
      'backup_rows', (select count(*) from public.phg_backup_design_fn_defs_20260928),
      'null_layout_is_rejected', (select prosrc ~ 'coalesce\(jsonb_typeof\(p_layout' from pg_proc where proname = 'phg_design_proposal_submit')));
    r := r || jsonb_build_object('rollback_returns', public.phg_rollback_design_score_gate_20260928());
    r := r || jsonb_build_object('after_rollback', jsonb_build_object('fns', (select jsonb_agg(p.oid::regprocedure::text order by 1) from pg_proc p where p.proname in ('phg_design_proposal_submit','phg_design_proposal_score','phg_design_proposal_review','phg_design_status')),
      'anon_or_auth_exec', (select bool_or(has_function_privilege('anon', p.oid, 'EXECUTE') or has_function_privilege('authenticated', p.oid, 'EXECUTE'))
                              from pg_proc p where p.proname like 'phg_design_proposal%' or p.proname = 'phg_design_status'),
      'service_role_exec', (select bool_and(has_function_privilege('service_role', p.oid, 'EXECUTE'))
                              from pg_proc p where p.proname like 'phg_design_proposal%' or p.proname = 'phg_design_status'),
      'review_body_restored', (select prosrc !~ 'accuracy_reviewer' from pg_proc where proname = 'phg_design_proposal_review')));
  EXCEPTION WHEN others THEN 
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      r := r || jsonb_build_object('ERROR', jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx), 'pass', false));
  END;
  RAISE EXCEPTION 'REHEARSAL %', r;
END
$rehearse_main$;
