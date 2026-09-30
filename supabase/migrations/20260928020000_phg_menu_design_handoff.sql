-- PHG-036: Menu Designer hand-off plumbing (Coordinator <-> Designer <-> Menu Studio).
-- Flow: the app (user prompt flow or an admin button on the Menu Studio page) asks for a design -> a TASK with the
-- draft's current document and inputs -> the Designer submits a PROPOSAL (a full Menu Studio document) -> automatic
-- checks (shape; no invented items; no changed or invented prices) -> the Coordinator approves or rejects -> only an
-- APPROVED proposal is released to the app, which applies it through its own save path (phg_menu_sync with the
-- project token + revision check) and reports the revision. The Designer never writes to a draft; app users can
-- neither submit nor approve proposals.
-- Separate tables on purpose: public.agent_tasks / agent_proposals belong to the brand/product intelligence system
-- (strict task types and target tables).

create table if not exists phg.menu_design_tasks (
  id              uuid primary key default gen_random_uuid(),
  menu_project_id uuid not null references phg.menu_projects(id) on delete cascade,
  source          text not null check (source in ('user_prompt_flow','admin_button','coordinator')),
  source_detail   text,                 -- e.g. the admin button name: add_section, bulk_price, colours, new_page ...
  request         text not null check (length(request) between 1 and 4000),
  inputs          jsonb not null default '{}'::jsonb,   -- menu_type, lists, items, price_band, demographics, brand, format, constraints, comparables
  base_revision   bigint,
  base_doc        jsonb,                -- the draft document when the task was created (reference for the checks)
  status          text not null default 'queued'
                  check (status in ('queued','in_progress','proposed','approved','applied','rejected','needs_input','cancelled')),
  requested_by    uuid,
  dedupe_key      text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists menu_design_tasks_project_idx on phg.menu_design_tasks (menu_project_id, created_at desc);
create index if not exists menu_design_tasks_queue_idx on phg.menu_design_tasks (status, created_at) where status in ('queued','in_progress');
create unique index if not exists menu_design_tasks_dedupe_idx on phg.menu_design_tasks (dedupe_key) where dedupe_key is not null;

create table if not exists phg.menu_design_proposals (
  id               uuid primary key default gen_random_uuid(),
  task_id          uuid not null references phg.menu_design_tasks(id) on delete cascade,
  version          int not null,
  doc              jsonb not null,      -- full Menu Studio document {title, sections:[{name, items:[...], subs:[...]}], ...}
  options          jsonb,               -- up to 3 alternative documents
  changes          jsonb,               -- plain list of what changed vs the previous version
  previews         jsonb,               -- storage paths of full-resolution previews
  reasoning        text,
  evidence_document_ids bigint[],       -- library menus used as references (menu_visual_documents.id)
  confidence       numeric check (confidence is null or confidence between 0 and 1),
  risk_flags       text[] not null default '{}',
  check_result     jsonb,               -- phg_design_doc_check output
  status           text not null default 'submitted'
                   check (status in ('submitted','auto_rejected','approved','rejected','applied','superseded','needs_input')),
  review_note      text,
  reviewed_at      timestamptz,
  applied_at       timestamptz,
  applied_revision bigint,
  created_at       timestamptz not null default now(),
  unique (task_id, version)
);
create index if not exists menu_design_proposals_task_idx on phg.menu_design_proposals (task_id, version desc);

alter table phg.menu_design_tasks enable row level security;
alter table phg.menu_design_proposals enable row level security;
revoke all on phg.menu_design_tasks, phg.menu_design_proposals from anon, authenticated;

-- Every item of a Menu Studio document (sections[].items and sections[].subs[].items) as (name_key, name, prices[]).
create or replace function public.phg_design_doc_items(p_doc jsonb)
returns table (name_key text, name text, prices numeric[])
language sql immutable set search_path to '' as $$
  with it as (
    select i from jsonb_array_elements(coalesce(p_doc->'sections','[]'::jsonb)) s,
                  jsonb_array_elements(coalesce(s->'items','[]'::jsonb)) i
    union all
    select i from jsonb_array_elements(coalesce(p_doc->'sections','[]'::jsonb)) s,
                  jsonb_array_elements(coalesce(s->'subs','[]'::jsonb)) sb,
                  jsonb_array_elements(coalesce(sb->'items','[]'::jsonb)) i)
  select regexp_replace(lower(btrim(coalesce(i->>'name',''))), '\s+', ' ', 'g'), i->>'name',
         array(select (p->>'value')::numeric from jsonb_array_elements(coalesce(i->'prices','[]'::jsonb)) p
               where (p->>'value') ~ '^\s*\d+(\.\d+)?\s*$')
  from it
$$;

-- Automatic checks on a proposed document against what the task was given.
create or replace function public.phg_design_doc_check(p_doc jsonb, p_base_doc jsonb, p_inputs jsonb)
returns jsonb language plpgsql stable set search_path to 'public', 'pg_temp' as $$
declare v_problems text[] := '{}'; v_known jsonb := '{}'; r record; v_n int := 0; v_sections int;
begin
  if p_doc is null or jsonb_typeof(p_doc) <> 'object' or jsonb_typeof(p_doc->'sections') <> 'array' then
    return jsonb_build_object('ok', false, 'problems', array['doc.sections must be an array']);
  end if;
  v_sections := jsonb_array_length(p_doc->'sections');
  if v_sections = 0 then v_problems := v_problems || 'no sections'; end if;
  if v_sections > 60 then v_problems := v_problems || 'more than 60 sections'; end if;
  if exists (select 1 from jsonb_array_elements(p_doc->'sections') s where coalesce(btrim(s->>'name'),'') = '') then
    v_problems := v_problems || 'a section has no name'; end if;

  -- known items: the draft at task time + items passed in the task inputs {items:[{name, price|prices}]}
  for r in select * from public.phg_design_doc_items(p_base_doc) loop
    v_known := jsonb_set(v_known, array[r.name_key], coalesce(v_known->r.name_key, '[]'::jsonb) || to_jsonb(r.prices));
  end loop;
  for r in select regexp_replace(lower(btrim(coalesce(x->>'name', x->>'item_name', ''))), '\s+', ' ', 'g') k,
                  coalesce(case when jsonb_typeof(x->'prices') = 'array' then x->'prices' end,
                           case when (x->>'price') ~ '^\s*\d+(\.\d+)?\s*$' then jsonb_build_array((x->>'price')::numeric) end,
                           '[]'::jsonb) p
             from jsonb_array_elements(coalesce(p_inputs->'items','[]'::jsonb)) x loop
    continue when r.k = '';
    v_known := jsonb_set(v_known, array[r.k], coalesce(v_known->r.k, '[]'::jsonb) || r.p);
  end loop;

  for r in select * from public.phg_design_doc_items(p_doc) loop
    v_n := v_n + 1;
    if r.name_key = '' then v_problems := v_problems || 'an item has no name'; continue; end if;
    if not v_known ? r.name_key then
      v_problems := v_problems || ('item not in the draft or the inputs (invented?): ' || r.name);
    elsif cardinality(r.prices) > 0 and exists (
          select 1 from unnest(r.prices) pv
          where not exists (select 1 from jsonb_array_elements_text(v_known->r.name_key) kv where kv::numeric = pv)) then
      v_problems := v_problems || ('price not in the draft or the inputs: ' || r.name);
    end if;
  end loop;
  if v_n > 600 then v_problems := v_problems || 'more than 600 items'; end if;
  return jsonb_build_object('ok', cardinality(v_problems) = 0, 'problems', to_jsonb(v_problems[1:50]),
                            'items', v_n, 'sections', v_sections);
end $$;

-- App -> task. The caller (Edge function phg-menu-design) has already authorized the project.
create or replace function public.phg_design_task_create(p_menu_project_id uuid, p_source text, p_source_detail text,
  p_request text, p_inputs jsonb, p_requested_by uuid default null)
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_p phg.menu_projects%rowtype; v_id uuid; v_key text;
begin
  select * into v_p from phg.menu_projects where id = p_menu_project_id;
  if not found then raise exception 'menu project not found'; end if;
  v_key := p_menu_project_id::text || '|' || md5(coalesce(p_source,'') || coalesce(p_source_detail,'') || coalesce(p_request,'')
           || coalesce(p_inputs::text,'')) || '|' || to_char(date_trunc('minute', now()), 'YYYYMMDDHH24MI');
  select id into v_id from phg.menu_design_tasks where dedupe_key = v_key;
  if v_id is not null then return jsonb_build_object('status','duplicate','task_id',v_id); end if;
  insert into phg.menu_design_tasks (menu_project_id, source, source_detail, request, inputs, base_revision, base_doc, requested_by, dedupe_key)
  values (p_menu_project_id, p_source, left(p_source_detail, 120), left(p_request, 4000), coalesce(p_inputs, '{}'::jsonb),
          v_p.backend_revision, coalesce(v_p.editor_state->'doc', '{}'::jsonb), p_requested_by, v_key)
  returning id into v_id;
  return jsonb_build_object('status','queued','task_id',v_id,'base_revision',v_p.backend_revision);
end $$;

-- Designer -> proposal (called by the Coordinator on the Designer's behalf; never by app users).
create or replace function public.phg_design_proposal_submit(p_task_id uuid, p_doc jsonb, p_options jsonb default null,
  p_changes jsonb default null, p_previews jsonb default null, p_reasoning text default null,
  p_evidence_document_ids bigint[] default null, p_confidence numeric default null, p_risk_flags text[] default '{}',
  p_needs_input boolean default false)
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_t phg.menu_design_tasks%rowtype; v_chk jsonb; v_ver int; v_id uuid; v_status text;
begin
  select * into v_t from phg.menu_design_tasks where id = p_task_id for update;
  if not found then raise exception 'design task not found'; end if;
  if v_t.status in ('applied','cancelled') then raise exception 'task is %', v_t.status; end if;
  v_chk := case when p_needs_input then jsonb_build_object('ok', true, 'problems', '[]'::jsonb, 'needs_input', true)
                else public.phg_design_doc_check(p_doc, v_t.base_doc, v_t.inputs) end;
  v_status := case when p_needs_input then 'needs_input' when (v_chk->>'ok')::boolean then 'submitted' else 'auto_rejected' end;
  select coalesce(max(version), 0) + 1 into v_ver from phg.menu_design_proposals where task_id = p_task_id;
  update phg.menu_design_proposals set status = 'superseded' where task_id = p_task_id and status in ('submitted','needs_input');
  insert into phg.menu_design_proposals (task_id, version, doc, options, changes, previews, reasoning, evidence_document_ids,
    confidence, risk_flags, check_result, status)
  values (p_task_id, v_ver, coalesce(p_doc, '{}'::jsonb), p_options, p_changes, p_previews, p_reasoning, p_evidence_document_ids,
    p_confidence, coalesce(p_risk_flags, '{}'), v_chk, v_status)
  returning id into v_id;
  update phg.menu_design_tasks set status = case v_status when 'needs_input' then 'needs_input' when 'submitted' then 'proposed' else 'in_progress' end,
    updated_at = now() where id = p_task_id;
  return jsonb_build_object('status', v_status, 'proposal_id', v_id, 'version', v_ver, 'check', v_chk);
end $$;

-- Coordinator review. Approval re-runs the checks; a failing proposal cannot be approved.
create or replace function public.phg_design_proposal_review(p_proposal_id uuid, p_approve boolean, p_note text default null)
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_pr phg.menu_design_proposals%rowtype; v_t phg.menu_design_tasks%rowtype; v_chk jsonb;
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
  end if;
  update phg.menu_design_proposals set status = case when p_approve then 'approved' else 'rejected' end,
    reviewed_at = now(), review_note = p_note where id = v_pr.id;
  update phg.menu_design_tasks set status = case when p_approve then 'approved' else 'in_progress' end, updated_at = now()
   where id = v_t.id;
  return jsonb_build_object('status', case when p_approve then 'approved' else 'rejected' end, 'proposal_id', v_pr.id);
end $$;

-- App: tasks and proposals of a project (documents only for approved / applied proposals).
create or replace function public.phg_design_status(p_menu_project_id uuid)
returns jsonb language sql stable security definer set search_path to 'public', 'pg_temp' as $$
  select jsonb_build_object('tasks', coalesce(jsonb_agg(jsonb_build_object(
    'task_id', t.id, 'status', t.status, 'source', t.source, 'source_detail', t.source_detail, 'request', t.request,
    'created_at', t.created_at,
    'proposals', (select coalesce(jsonb_agg(jsonb_build_object('proposal_id', p.id, 'version', p.version, 'status', p.status,
                    'reasoning', p.reasoning, 'risk_flags', p.risk_flags, 'problems', p.check_result->'problems',
                    'changes', p.changes, 'previews', p.previews, 'created_at', p.created_at) order by p.version desc), '[]'::jsonb)
                  from phg.menu_design_proposals p where p.task_id = t.id)) order by t.created_at desc), '[]'::jsonb))
  from (select * from phg.menu_design_tasks where menu_project_id = p_menu_project_id order by created_at desc limit 30) t
$$;

create or replace function public.phg_design_take_approved(p_menu_project_id uuid, p_proposal_id uuid)
returns jsonb language sql stable security definer set search_path to 'public', 'pg_temp' as $$
  select coalesce((select jsonb_build_object('proposal_id', p.id, 'task_id', t.id, 'version', p.version, 'doc', p.doc,
            'base_revision', t.base_revision, 'current_revision', mp.backend_revision)
     from phg.menu_design_proposals p join phg.menu_design_tasks t on t.id = p.task_id
     join phg.menu_projects mp on mp.id = t.menu_project_id
    where p.id = p_proposal_id and t.menu_project_id = p_menu_project_id and p.status = 'approved'),
    jsonb_build_object('error','no approved proposal with that id for this project'))
$$;

-- App: the approved document was saved through phg_menu_sync; record the revision it produced.
create or replace function public.phg_design_mark_applied(p_menu_project_id uuid, p_proposal_id uuid, p_revision bigint)
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_pr phg.menu_design_proposals%rowtype; v_rev bigint;
begin
  select p.* into v_pr from phg.menu_design_proposals p join phg.menu_design_tasks t on t.id = p.task_id
   where p.id = p_proposal_id and t.menu_project_id = p_menu_project_id for update of p;
  if not found then raise exception 'proposal not found for this project'; end if;
  if v_pr.status <> 'approved' then raise exception 'proposal is %', v_pr.status; end if;
  select backend_revision into v_rev from phg.menu_projects where id = p_menu_project_id;
  if p_revision is null or v_rev is null or p_revision > v_rev then raise exception 'revision % not saved yet', p_revision; end if;
  update phg.menu_design_proposals set status = 'applied', applied_at = now(), applied_revision = p_revision where id = v_pr.id;
  update phg.menu_design_tasks set status = 'applied', updated_at = now() where id = v_pr.task_id;
  return jsonb_build_object('status','applied','proposal_id',v_pr.id,'revision',p_revision);
end $$;

revoke all on function public.phg_design_doc_items(jsonb), public.phg_design_doc_check(jsonb,jsonb,jsonb),
  public.phg_design_task_create(uuid,text,text,text,jsonb,uuid),
  public.phg_design_proposal_submit(uuid,jsonb,jsonb,jsonb,jsonb,text,bigint[],numeric,text[],boolean),
  public.phg_design_proposal_review(uuid,boolean,text), public.phg_design_status(uuid),
  public.phg_design_take_approved(uuid,uuid), public.phg_design_mark_applied(uuid,uuid,bigint)
  from public, anon, authenticated;

-- Applied in place after this file: phg_design_mark_applied also refuses a revision that is not newer than the task's
-- base_revision (the app must actually have saved the approved document). Rehearsal (rolled back) on the one live
-- project: invented item + changed price auto-rejected; clean proposal approved, released, applied; duplicate request
-- within the minute collapsed; unsaved / old revisions refused.
