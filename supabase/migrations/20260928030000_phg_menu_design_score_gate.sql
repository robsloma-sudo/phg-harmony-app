-- PHG-036b: Rob's design scorecard as a hard gate (handoff/agents/MENU_DESIGN_SCORECARD.md).
-- A proposal carries its layout geometry; three reviewers (design_critic, content_reviewer, accuracy_reviewer) score it
-- per criterion; phg_design_proposal_review refuses to approve unless EACH reviewer's average is above 80 and the
-- stored layout still has its page and elements.

-- Review (PHG-026 round 3, SF10): the layout check treats a missing key as missing (coalesce), and the three
-- functions this file replaces are saved first; phg_rollback_design_score_gate_20260928() puts them back.
-- Review (PHG-026 round 4, C18): header names the three reviewers; approve re-checks the layout (page + elements) and
-- returns accuracy_reviewer too; the definition backup is SELECT-only for service_role (revoke all, grant select).
-- Review (PHG-026 round 5, C18 / M4 / M5): lock_timeout 5s before the first lock (the ALTER below); an EMPTY elements
-- array is rejected on submit and blocked on approve; every score is appended to review_score_history (a re-score is
-- kept, not overwritten; the gate reads the latest per reviewer); the rollback re-grants EXECUTE to service_role
-- where the saved ACL had it, and is itself not executable by service_role.
--
-- NOT PART OF THE PHG-026 PUBLISH. This file is reviewed under PHG-026 (criterion C18) only because it was written in
-- the same window. Publishing PHG-026 (20260927190000 + 20260927191000, cron 13 / 7, builds 18.49.8-18.49.12) does
-- NOT apply it; it is applied separately, as one transaction, when Rob approves the design score gate.

set local lock_timeout = '5s';   -- fail fast (and roll back everything) instead of queueing behind phg.menu_design_proposals users

-- ---------- 0. save the definitions this migration replaces ----------
create table if not exists public.phg_backup_design_fn_defs_20260928 (
  signature text primary key, definition text not null, acl text, saved_at timestamptz not null default now());
alter table public.phg_backup_design_fn_defs_20260928 enable row level security;
revoke all on public.phg_backup_design_fn_defs_20260928 from anon, authenticated, service_role;
grant select on public.phg_backup_design_fn_defs_20260928 to service_role;
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
-- Rollback: drops the new submit (11 args) and the score function, restores the three saved bodies, re-applies the
-- revokes and re-grants EXECUTE to service_role on each signature whose saved ACL had it.
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
revoke all on function public.phg_rollback_design_score_gate_20260928() from public, anon, authenticated, service_role;

alter table phg.menu_design_proposals
  add column if not exists layout jsonb,
  add column if not exists review_scores jsonb not null default '{}'::jsonb,
  add column if not exists review_score_history jsonb not null default '[]'::jsonb;

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
  -- an elements array must exist AND be non-empty (case: jsonb_array_length only runs on an array)
  if not p_needs_input and (p_layout is null
                            or not (case when jsonb_typeof(p_layout->'elements') = 'array'
                                         then jsonb_array_length(p_layout->'elements') > 0 else false end)
                            or coalesce(jsonb_typeof(p_layout->'page'), '') <> 'object') then
    v_chk := jsonb_set(v_chk, '{ok}', 'false'::jsonb);
    v_chk := jsonb_set(v_chk, '{problems}', coalesce(v_chk->'problems','[]'::jsonb) || '["layout geometry missing (page + a non-empty elements array required by the scorecard)"]'::jsonb);
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

-- A reviewer records its scores. Keys per reviewer follow the scorecard; each 0-100. review_scores keeps the latest
-- entry per reviewer (what the gate reads); every call is also appended to review_score_history, so a re-score on the
-- same version is visible and nothing is overwritten silently. The result says how many earlier scores this reviewer
-- gave the same version (rescore_of_same_version).
create or replace function public.phg_design_proposal_score(p_proposal_id uuid, p_reviewer text, p_scores jsonb,
  p_fixes jsonb default null, p_notes jsonb default null)
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_keys text[]; v_avg numeric; v_pr phg.menu_design_proposals%rowtype; k text; v_entry jsonb; v_prior int;
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
  v_entry := jsonb_build_object('scores', (select jsonb_object_agg(x, p_scores->x) from unnest(v_keys) x), 'average', v_avg,
                                'fixes', coalesce(p_fixes, '[]'::jsonb), 'notes', p_notes, 'at', now());
  select count(*) into v_prior from jsonb_array_elements(v_pr.review_score_history) h where h->>'reviewer' = p_reviewer;
  update phg.menu_design_proposals
     set review_scores = review_scores || jsonb_build_object(p_reviewer, v_entry),
         review_score_history = review_score_history || jsonb_build_array(v_entry || jsonb_build_object('reviewer', p_reviewer))
   where id = p_proposal_id;
  return jsonb_build_object('reviewer', p_reviewer, 'average', v_avg, 'passes', v_avg > 80, 'rescore_of_same_version', v_prior);
end $$;

-- Review: approval now also needs all three reviewers' averages above 80, and the stored layout must still have a page
-- object and a non-empty elements array (a proposal stored before this migration has layout NULL: it is blocked, not
-- approved).
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
    if v_pr.layout is null
       or not (case when jsonb_typeof(v_pr.layout->'elements') = 'array' then jsonb_array_length(v_pr.layout->'elements') > 0 else false end)
       or coalesce(jsonb_typeof(v_pr.layout->'page'), '') <> 'object' then
      return jsonb_build_object('status','blocked_by_layout_gate','proposal_id',v_pr.id,
        'rule','layout geometry missing (page + a non-empty elements array required by the scorecard); re-submit with p_layout');
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
                            'design_critic', v_c, 'content_reviewer', v_m, 'accuracy_reviewer', v_a);
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
