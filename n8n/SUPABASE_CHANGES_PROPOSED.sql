-- =====================================================================================
-- n8n control plane - Supabase changes PROPOSED
--
--   STATUS: NOT APPLIED. PROPOSAL ONLY. NEEDS ROB'S APPROVAL BEFORE ANY OF THIS RUNS.
--
-- Project: lqjtwabzmgjcufftuqvu. Written 2026-09-30 by the lead developer (Claude) for PHG-008.
-- Read n8n/README.md first. Apply as ONE migration (e.g. supabase/migrations/<ts>_phg_control_n8n.sql)
-- only after Rob says yes, then run the POST-APPLY CHECKS at the bottom.
--
-- Design in one paragraph:
--   n8n logs into Postgres as a dedicated LOGIN role `n8n_control`. That role owns nothing and has
--   no table privileges. It can USE schema phg_control and EXECUTE a short, named list of
--   SECURITY DEFINER functions in it. Every consequential action is a row in
--   phg_control.action_requests whose action_key must be in phg_control.action_catalog, and it can
--   only be executed after a recorded human decision, by the same n8n execution that claimed it.
--   Every workflow run is logged in phg_control.workflow_runs. The service_role key is never given
--   to n8n. phg_control is NOT added to the PostgREST exposed schemas, so none of this is
--   reachable over the REST API with the anon/publishable key.
--
-- Why not public.agent_runs for run logging: agent_runs.task_id is NOT NULL with an FK to
--   public.agent_tasks, and agent_tasks requires a GTT target (source/brand/product/account/
--   geography) and a GTT task_type. n8n control runs have none of those. Option B (commented at
--   the end) mirrors workflow_runs into agent_runs if Rob prefers one log; it needs a schema change
--   to an existing table, so it is not the default.
-- =====================================================================================

begin;

-- -------------------------------------------------------------------------------------
-- 0. Role. Password is NOT in this file. Rob sets it once in the SQL editor from a password
--    manager value:  alter role n8n_control password '<generated 40+ chars>';
--    and pastes the same value into the n8n credential "PHG Supabase (n8n_control)".
-- -------------------------------------------------------------------------------------
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'n8n_control') then
    create role n8n_control login noinherit nocreatedb nocreaterole noreplication nobypassrls
      connection limit 5;
  end if;
end $$;
alter role n8n_control set statement_timeout = '20s';
alter role n8n_control set idle_in_transaction_session_timeout = '30s';
alter role n8n_control set search_path = phg_control;

create schema if not exists phg_control;
revoke all on schema phg_control from public;
grant usage on schema phg_control to n8n_control;

-- -------------------------------------------------------------------------------------
-- 1. Tables (n8n_control gets NO privileges on any of them; functions only)
-- -------------------------------------------------------------------------------------
create table if not exists phg_control.settings (
  key        text primary key,
  value      jsonb not null,
  note       text,
  updated_at timestamptz not null default now()
);
insert into phg_control.settings (key, value, note) values
  ('spend_daily_credit_limit',  '1500',  'Firecrawl estimated credits per UTC day, all pipelines. ROB TO SET. 2026-09-30 so far: ~5,239.'),
  ('spend_min_success_rate',    '0.70',  'PHG-059: paid scrapes only where a sample shows >= 70% success.'),
  ('spend_min_sample',          '20',    'Requests needed in the window before a success rate is judged.'),
  ('spend_auto_pause_hours',    '24',    'How long an automatic protective pause lasts (max 72).'),
  ('health_cron_fail_pct',      '10',    'Nightly health: flag an active cron job failing more than this % in 24 h.'),
  ('health_stale_lease_minutes','10',    'Lease expired this long ago without finished_at = worker died.'),
  ('approval_ttl_hours',        '72',    'Pending requests older than this expire.')
on conflict (key) do nothing;

create table if not exists phg_control.action_catalog (
  action_key        text primary key,
  description       text not null,
  risk              text not null check (risk in ('protective','low','consequential')),
  requires_approval boolean not null default true,
  enabled           boolean not null default true
);
insert into phg_control.action_catalog (action_key, description, risk, requires_approval) values
  ('pause_menu_lane',        'Set paused_until on public.phg_menu_worker_leases for one allow-listed lane.', 'protective', true),
  ('resume_menu_lane',       'Clear paused_until on one allow-listed lane.',                                  'consequential', true),
  ('pause_cron_job',         'cron.alter_job(active := false) for one job in spend_kill_switches.',          'protective', true),
  ('resume_cron_job',        'cron.alter_job(active := true) for one job in spend_kill_switches.',           'consequential', true),
  ('close_harmony_feedback', 'Set status reviewed/wontfix/duplicate + fix_notes on phg.harmony_feedback ids.','low', true)
on conflict (action_key) do nothing;
-- Only these five exist. Adding an action = a reviewed migration that adds a catalog row AND a
-- branch in phg_control._dispatch() AND a branch in phg_control.verify_request().

-- Which switch stops which paid pipeline. confirmed = false rows are alert-only: the spend guard
-- files an approval request instead of pausing. ROB MUST CONFIRM THIS MAPPING (open question).
create table if not exists phg_control.spend_kill_switches (
  pipeline     text primary key,          -- public.menu_api_usage_ledger.pipeline
  lane         text,                      -- public.phg_menu_worker_leases.lane, or null
  cron_jobname text,                      -- cron.job.jobname, or null
  confirmed    boolean not null default false,
  note         text
);
insert into phg_control.spend_kill_switches (pipeline, lane, cron_jobname, confirmed, note) values
  ('candidate_recovery',      'candidate_extraction_paid', 'gtt-extract-paid-blocked',        false, 'extract-menu-candidates allow_paid:true (migration 20260930170000)'),
  ('website_discovery',       null,                        'gtt-discover-restaurant-websites', false, 'discover-restaurant-websites; 2 credits/request; no lease'),
  ('menu_visual_capture',     null,                        null,                               false, 'screenshot provider; source function not in repo - Rob to name the switch'),
  ('economy_extract',         null,                        'gtt-extract-menus',                false, 'extract-menus-economy (guess)'),
  ('menu_target_recovery',    null,                        'gtt-menu-search-recovery',         false, 'recover-menu-search (guess)'),
  ('multi_menu_discovery',    null,                        'gtt-discover-beverage-menus',      false, 'discover-beverage-menus is live-only (guess)'),
  ('multi_menu_discovery_v2', null,                        'gtt-discover-beverage-menus',      false, 'guess'),
  ('multi_menu_extract',      null,                        null,                               false, 'unknown')
on conflict (pipeline) do nothing;

create table if not exists phg_control.action_requests (
  id                   uuid primary key default gen_random_uuid(),
  action_key           text not null references phg_control.action_catalog(action_key),
  params               jsonb not null default '{}'::jsonb,
  reason               text not null,
  evidence             jsonb not null default '{}'::jsonb,
  requested_by         text not null,          -- 'claude:lead-dev', 'harmony', 'n8n:spend-guard', ...
  dedupe_key           text not null unique,   -- idempotency: same key = same request
  status               text not null default 'pending' check (status in
                         ('pending','awaiting_approval','approved','rejected','expired',
                          'executed','verified','failed','verification_failed')),
  claim_token_hash     text,                   -- sha256 of the token handed to ONE n8n execution
  claimed_at           timestamptz,
  claimed_by_execution text,
  decided_at           timestamptz,
  decided_by           text,
  decision_note        text,
  executed_at          timestamptz,
  result               jsonb,
  verified_at          timestamptz,
  verification         jsonb,
  attempts             int not null default 0,
  expires_at           timestamptz not null default now() + interval '72 hours',
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);
create index if not exists action_requests_status_idx on phg_control.action_requests (status, created_at);

create table if not exists phg_control.workflow_runs (
  id               bigint generated always as identity primary key,
  run_key          text not null unique,        -- '<workflow>:<n8n execution id>' - idempotent
  workflow         text not null,
  n8n_execution_id text,
  request_id       uuid references phg_control.action_requests(id),
  status           text not null default 'running' check (status in ('running','succeeded','failed','cancelled')),
  summary          jsonb not null default '{}'::jsonb,
  error            text,
  started_at       timestamptz not null default now(),
  finished_at      timestamptz
);
create index if not exists workflow_runs_started_idx on phg_control.workflow_runs (started_at desc);

create table if not exists phg_control.watermarks (
  key        text primary key,
  value      jsonb not null,
  updated_at timestamptz not null default now()
);

-- RLS on, no policies: nothing but the definer functions (and postgres) can touch these.
alter table phg_control.settings            enable row level security;
alter table phg_control.action_catalog      enable row level security;
alter table phg_control.spend_kill_switches enable row level security;
alter table phg_control.action_requests     enable row level security;
alter table phg_control.workflow_runs       enable row level security;
alter table phg_control.watermarks          enable row level security;
revoke all on all tables in schema phg_control from public, anon, authenticated;

-- -------------------------------------------------------------------------------------
-- 2. Helpers (NOT granted to n8n_control)
-- -------------------------------------------------------------------------------------
create or replace function phg_control._setting(p_key text) returns jsonb
language sql stable security definer set search_path = '' as $$
  select value from phg_control.settings where key = p_key
$$;

create or replace function phg_control._allowed_lane(p_lane text) returns boolean
language sql immutable as $$
  select p_lane in ('candidate_extraction','candidate_extraction_paid','visual_acquisition','website_menu_discovery')
$$;

create or replace function phg_control._allowed_cron(p_jobname text) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from phg_control.spend_kill_switches where cron_jobname = p_jobname)
$$;

-- The only place an action touches production state.
create or replace function phg_control._dispatch(p_action_key text, p_params jsonb) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_lane text := p_params->>'lane';
  v_job  text := p_params->>'cron_jobname';
  v_hours numeric;
  v_ids bigint[];
  v_status text;
  v_n int;
  v_jobid bigint;
begin
  if p_action_key = 'pause_menu_lane' then
    if not phg_control._allowed_lane(v_lane) then raise exception 'lane not allow-listed: %', v_lane; end if;
    v_hours := least(72, greatest(1, coalesce((p_params->>'hours')::numeric, 24)));
    update public.phg_menu_worker_leases
       set paused_until = greatest(coalesce(paused_until, now()), now() + make_interval(secs => (v_hours * 3600)::int))
     where lane = v_lane;
    get diagnostics v_n = row_count;
    if v_n <> 1 then raise exception 'lane row missing: %', v_lane; end if;
    return jsonb_build_object('lane', v_lane, 'paused_hours', v_hours);

  elsif p_action_key = 'resume_menu_lane' then
    if not phg_control._allowed_lane(v_lane) then raise exception 'lane not allow-listed: %', v_lane; end if;
    update public.phg_menu_worker_leases set paused_until = null where lane = v_lane;
    return jsonb_build_object('lane', v_lane, 'resumed', true);

  elsif p_action_key in ('pause_cron_job','resume_cron_job') then
    if not phg_control._allowed_cron(v_job) then raise exception 'cron job not allow-listed: %', v_job; end if;
    select jobid into v_jobid from cron.job where jobname = v_job;
    if v_jobid is null then raise exception 'cron job not found: %', v_job; end if;
    perform cron.alter_job(job_id := v_jobid, active := (p_action_key = 'resume_cron_job'));
    return jsonb_build_object('cron_jobname', v_job, 'active', p_action_key = 'resume_cron_job');

  elsif p_action_key = 'close_harmony_feedback' then
    v_status := p_params->>'status';
    if v_status not in ('reviewed','wontfix','duplicate') then raise exception 'status must be reviewed/wontfix/duplicate'; end if;
    select array_agg(x::bigint) into v_ids from jsonb_array_elements_text(p_params->'ids') x;
    if v_ids is null or cardinality(v_ids) > 50 then raise exception '1..50 feedback ids required'; end if;
    update phg.harmony_feedback
       set status = v_status, fix_notes = left(coalesce(p_params->>'notes',''), 1000), reviewed_at = now()
     where id = any(v_ids) and status = 'new';
    get diagnostics v_n = row_count;
    return jsonb_build_object('closed', v_n, 'ids', to_jsonb(v_ids), 'status', v_status);
  end if;
  raise exception 'unsupported action_key: %', p_action_key;
end $$;

-- -------------------------------------------------------------------------------------
-- 3. Approval flow API (granted to n8n_control)
-- -------------------------------------------------------------------------------------

-- Intake. Idempotent on dedupe_key: a repeat returns the existing row, never a second request.
create or replace function phg_control.submit_request(
  p_action_key text, p_params jsonb, p_reason text, p_requested_by text,
  p_dedupe_key text, p_evidence jsonb default '{}'::jsonb) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare r phg_control.action_requests%rowtype; v_created boolean := false;
begin
  if not exists (select 1 from phg_control.action_catalog where action_key = p_action_key and enabled) then
    raise exception 'action_key not allowed: %', p_action_key;
  end if;
  if coalesce(length(p_reason),0) < 10 then raise exception 'reason required (>= 10 chars)'; end if;
  if coalesce(length(p_dedupe_key),0) < 8 then raise exception 'dedupe_key required (>= 8 chars)'; end if;
  if pg_column_size(coalesce(p_params,'{}'::jsonb)) > 8000 then raise exception 'params too large'; end if;
  insert into phg_control.action_requests (action_key, params, reason, evidence, requested_by, dedupe_key, expires_at)
  values (p_action_key, coalesce(p_params,'{}'::jsonb), left(p_reason, 2000), coalesce(p_evidence,'{}'::jsonb),
          left(coalesce(p_requested_by,'unknown'), 100), p_dedupe_key,
          now() + make_interval(hours => coalesce((phg_control._setting('approval_ttl_hours'))::int, 72)))
  on conflict (dedupe_key) do nothing
  returning * into r;
  if found then v_created := true;
  else select * into r from phg_control.action_requests where dedupe_key = p_dedupe_key; end if;
  return jsonb_build_object('id', r.id, 'status', r.status, 'created', v_created, 'action_key', r.action_key);
end $$;

-- Claim ONE pending request for one n8n execution. Returns the claim token in plaintext once.
-- Expires old pending/awaiting rows first. SKIP LOCKED makes concurrent pollers safe.
create or replace function phg_control.claim_next_request(p_execution_id text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare r phg_control.action_requests%rowtype; v_token text := encode(extensions.gen_random_bytes(24), 'hex');
begin
  update phg_control.action_requests set status = 'expired', updated_at = now()
   where status in ('pending','awaiting_approval') and expires_at < now();
  -- a claim whose n8n execution died (no decision in 26 h) goes back to pending
  update phg_control.action_requests set status = 'pending', claim_token_hash = null, claimed_at = null,
         claimed_by_execution = null, updated_at = now()
   where status = 'awaiting_approval' and claimed_at < now() - interval '26 hours';
  select * into r from phg_control.action_requests
   where status = 'pending' order by created_at limit 1 for update skip locked;
  if not found then return null; end if;
  update phg_control.action_requests
     set status = 'awaiting_approval', claim_token_hash = encode(extensions.digest(v_token,'sha256'),'hex'),
         claimed_at = now(), claimed_by_execution = left(p_execution_id, 100), updated_at = now()
   where id = r.id;
  return jsonb_build_object('id', r.id, 'claim_token', v_token, 'action_key', r.action_key,
    'description', (select description from phg_control.action_catalog where action_key = r.action_key),
    'params', r.params, 'reason', r.reason, 'evidence', r.evidence, 'requested_by', r.requested_by,
    'created_at', r.created_at, 'expires_at', r.expires_at);
end $$;

create or replace function phg_control._check_claim(p_id uuid, p_claim_token text, p_status text)
returns phg_control.action_requests
language plpgsql security definer set search_path = '' as $$
declare r phg_control.action_requests%rowtype;
begin
  select * into r from phg_control.action_requests where id = p_id for update;
  if not found then raise exception 'request not found'; end if;
  if r.claim_token_hash is null or p_claim_token is null
     or encode(extensions.digest(p_claim_token,'sha256'),'hex') <> r.claim_token_hash then
    raise exception 'invalid claim token';
  end if;
  if p_status is not null and r.status <> p_status then raise exception 'request is %, expected %', r.status, p_status; end if;
  return r;
end $$;

-- Record the human decision. Only the execution holding the claim token can do it.
create or replace function phg_control.decide_request(
  p_id uuid, p_claim_token text, p_approved boolean, p_decided_by text, p_note text default null) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare r phg_control.action_requests%rowtype;
begin
  r := phg_control._check_claim(p_id, p_claim_token, 'awaiting_approval');
  if r.expires_at < now() then
    update phg_control.action_requests set status = 'expired', updated_at = now() where id = p_id;
    return jsonb_build_object('id', p_id, 'status', 'expired');
  end if;
  update phg_control.action_requests
     set status = case when p_approved then 'approved' else 'rejected' end,
         decided_at = now(), decided_by = left(coalesce(p_decided_by,'unknown'),100),
         decision_note = left(p_note, 1000), updated_at = now()
   where id = p_id;
  return jsonb_build_object('id', p_id, 'status', case when p_approved then 'approved' else 'rejected' end);
end $$;

-- Execute an approved request. Idempotent: a second call after success returns already_executed.
create or replace function phg_control.execute_request(p_id uuid, p_claim_token text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare r phg_control.action_requests%rowtype; v_result jsonb;
begin
  r := phg_control._check_claim(p_id, p_claim_token, null);
  if r.status in ('executed','verified') then
    return jsonb_build_object('id', p_id, 'status', r.status, 'already_executed', true, 'result', r.result);
  end if;
  if r.status <> 'approved' then raise exception 'request is %, not approved', r.status; end if;
  if not exists (select 1 from phg_control.action_catalog where action_key = r.action_key and enabled) then
    raise exception 'action disabled: %', r.action_key;
  end if;
  begin
    v_result := phg_control._dispatch(r.action_key, r.params);
    update phg_control.action_requests set status = 'executed', executed_at = now(), result = v_result,
           attempts = attempts + 1, updated_at = now() where id = p_id;
    return jsonb_build_object('id', p_id, 'status', 'executed', 'result', v_result);
  exception when others then
    update phg_control.action_requests set status = 'failed', attempts = attempts + 1,
           result = jsonb_build_object('error', left(sqlerrm, 500)), updated_at = now() where id = p_id;
    return jsonb_build_object('id', p_id, 'status', 'failed', 'error', left(sqlerrm, 500));
  end;
end $$;

-- Verification: re-read the real state the action was meant to change. Never trusts the executor.
create or replace function phg_control.verify_request(p_id uuid) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare r phg_control.action_requests%rowtype; v_ok boolean; v_obs jsonb;
begin
  select * into r from phg_control.action_requests where id = p_id for update;
  if not found then raise exception 'request not found'; end if;
  if r.status not in ('executed','verified','verification_failed') then
    return jsonb_build_object('id', p_id, 'ok', false, 'reason', 'status is ' || r.status);
  end if;
  if r.action_key = 'pause_menu_lane' then
    select coalesce(paused_until > now() + interval '30 minutes', false), to_jsonb(l) - 'owner' - 'last_result'
      into v_ok, v_obs from public.phg_menu_worker_leases l where lane = r.params->>'lane';
  elsif r.action_key = 'resume_menu_lane' then
    select coalesce(paused_until is null or paused_until <= now(), false), to_jsonb(l) - 'owner' - 'last_result'
      into v_ok, v_obs from public.phg_menu_worker_leases l where lane = r.params->>'lane';
  elsif r.action_key in ('pause_cron_job','resume_cron_job') then
    select active = (r.action_key = 'resume_cron_job'), jsonb_build_object('jobname', jobname, 'active', active)
      into v_ok, v_obs from cron.job where jobname = r.params->>'cron_jobname';
  elsif r.action_key = 'close_harmony_feedback' then
    select count(*) filter (where status = 'new') = 0,
           jsonb_build_object('rows', count(*), 'still_new', count(*) filter (where status = 'new'))
      into v_ok, v_obs from phg.harmony_feedback
     where id in (select x::bigint from jsonb_array_elements_text(r.params->'ids') x);
  end if;
  v_ok := coalesce(v_ok, false);
  update phg_control.action_requests
     set status = case when v_ok then 'verified' else 'verification_failed' end,
         verified_at = now(), verification = jsonb_build_object('ok', v_ok, 'observed', v_obs, 'at', now()),
         updated_at = now()
   where id = p_id;
  return jsonb_build_object('id', p_id, 'ok', v_ok, 'observed', v_obs);
end $$;

-- -------------------------------------------------------------------------------------
-- 4. Run log + watermarks (granted to n8n_control)
-- -------------------------------------------------------------------------------------
create or replace function phg_control.run_start(p_workflow text, p_execution_id text, p_summary jsonb default '{}'::jsonb)
returns bigint language plpgsql security definer set search_path = '' as $$
declare v_id bigint;
begin
  insert into phg_control.workflow_runs (run_key, workflow, n8n_execution_id, summary)
  values (left(p_workflow,80) || ':' || coalesce(p_execution_id,'manual-' || gen_random_uuid()), left(p_workflow,80),
          left(p_execution_id,100), coalesce(p_summary,'{}'::jsonb))
  on conflict (run_key) do update set summary = phg_control.workflow_runs.summary   -- no-op, returns id
  returning id into v_id;
  return v_id;
end $$;

create or replace function phg_control.run_finish(p_run_id bigint, p_status text, p_summary jsonb default '{}'::jsonb,
                                                  p_error text default null, p_request_id uuid default null)
returns void language plpgsql security definer set search_path = '' as $$
begin
  if p_status not in ('succeeded','failed','cancelled') then raise exception 'bad status'; end if;
  update phg_control.workflow_runs
     set status = p_status, finished_at = now(), summary = summary || coalesce(p_summary,'{}'::jsonb),
         error = left(p_error, 2000), request_id = coalesce(p_request_id, request_id)
   where id = p_run_id;
end $$;

-- Used by the error workflow, which only knows the execution id.
create or replace function phg_control.run_fail_by_execution(p_workflow text, p_execution_id text, p_error text)
returns void language plpgsql security definer set search_path = '' as $$
begin
  insert into phg_control.workflow_runs (run_key, workflow, n8n_execution_id, status, error, finished_at)
  values (left(p_workflow,80) || ':' || p_execution_id, left(p_workflow,80), left(p_execution_id,100), 'failed', left(p_error,2000), now())
  on conflict (run_key) do update set status = 'failed', error = excluded.error, finished_at = now();
end $$;

create or replace function phg_control.get_watermark(p_key text) returns jsonb
language sql stable security definer set search_path = '' as $$
  select value from phg_control.watermarks where key = p_key
$$;

create or replace function phg_control.set_watermark(p_key text, p_value jsonb) returns void
language sql security definer set search_path = '' as $$
  insert into phg_control.watermarks (key, value) values (left(p_key,200), p_value)
  on conflict (key) do update set value = excluded.value, updated_at = now()
$$;

-- -------------------------------------------------------------------------------------
-- 5. Read models (granted to n8n_control). No secrets, no cron commands, no response bodies.
-- -------------------------------------------------------------------------------------

-- Harmony failure-log review: new open items since a watermark id + grouped counts.
create or replace function phg_control.harmony_feedback_digest(p_after_id bigint default 0, p_limit int default 40)
returns jsonb language sql stable security definer set search_path = '' as $$
  select jsonb_build_object(
    'open_total', (select count(*) from phg.harmony_feedback where status = 'new'),
    'new_since',  (select count(*) from phg.harmony_feedback where status = 'new' and id > coalesce(p_after_id,0)),
    'max_id',     (select coalesce(max(id), coalesce(p_after_id,0)) from phg.harmony_feedback),
    'by_kind_source', coalesce((select jsonb_agg(g order by g.n desc) from (
        select kind, coalesce(source,'-') as source, count(*) as n from phg.harmony_feedback where status = 'new' group by 1,2) g), '[]'::jsonb),
    'items', coalesce((select jsonb_agg(i order by i.id) from (
        select id, created_at, kind, surface, source, left(user_text,300) as user_text, left(reply_text,300) as reply_text,
               left(followup_text,300) as followup_text, view_title, left(error,300) as error, left(sql,300) as sql
          from phg.v_harmony_feedback_open where id > coalesce(p_after_id,0)
         order by id limit least(greatest(coalesce(p_limit,40),1),100)) i), '[]'::jsonb)
  )
$$;

-- Nightly health: cron failures, stale/paused leases, pg_net (cron -> edge function) failures,
-- stuck approval requests, failed n8n runs. Excludes cron.job.command (may embed tokens).
create or replace function phg_control.health_snapshot(p_hours int default 24) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare
  v_since timestamptz := now() - make_interval(hours => least(greatest(coalesce(p_hours,24),1),168));
  v_fail_pct numeric := coalesce((phg_control._setting('health_cron_fail_pct'))::numeric, 10);
  v_stale int := coalesce((phg_control._setting('health_stale_lease_minutes'))::int, 10);
begin
  return jsonb_build_object(
    'window_hours', p_hours, 'at', now(),
    'cron', coalesce((select jsonb_agg(c order by c.fail_pct desc nulls last, c.jobname) from (
        select j.jobid, j.jobname, j.schedule, j.active,
               count(d.runid) as runs,
               count(d.runid) filter (where d.status = 'failed') as failed,
               round(100.0 * count(d.runid) filter (where d.status = 'failed') / nullif(count(d.runid),0), 1) as fail_pct,
               max(d.start_time) filter (where d.status = 'failed') as last_failed_at,
               (select left(d2.return_message, 160) from cron.job_run_details d2
                 where d2.jobid = j.jobid and d2.status = 'failed' and d2.start_time > v_since
                 order by d2.start_time desc limit 1) as last_error,
               (j.active and count(d.runid) = 0) as silent
          from cron.job j left join cron.job_run_details d on d.jobid = j.jobid and d.start_time > v_since
         group by j.jobid, j.jobname, j.schedule, j.active) c), '[]'::jsonb),
    'cron_flagged', coalesce((select jsonb_agg(jobname) from (
        select j.jobname from cron.job j left join cron.job_run_details d on d.jobid = j.jobid and d.start_time > v_since
         where j.active group by j.jobname
        having count(d.runid) = 0
            or 100.0 * count(d.runid) filter (where d.status = 'failed') / nullif(count(d.runid),0) > v_fail_pct) f), '[]'::jsonb),
    'leases', coalesce((select jsonb_agg(jsonb_build_object(
        'lane', lane, 'lease_until', lease_until, 'paused_until', paused_until, 'started_at', started_at,
        'finished_at', finished_at,
        'stale', finished_at is null and lease_until < now() - make_interval(mins => v_stale),
        'paused', paused_until > now())) from public.phg_menu_worker_leases), '[]'::jsonb),
    'pg_net', (select jsonb_build_object(
        'responses', count(*),
        'failed', count(*) filter (where status_code >= 400 or timed_out or error_msg is not null),
        'timed_out', count(*) filter (where timed_out),
        'by_status', (select coalesce(jsonb_object_agg(sc, n), '{}'::jsonb) from (
            select coalesce(status_code::text, 'none') as sc, count(*) as n
              from net._http_response where created > v_since group by 1) s))
        from net._http_response where created > v_since),
    'requests', (select jsonb_build_object(
        'awaiting_approval', count(*) filter (where status = 'awaiting_approval'),
        'pending', count(*) filter (where status = 'pending'),
        'failed_24h', count(*) filter (where status in ('failed','verification_failed') and updated_at > v_since))
        from phg_control.action_requests),
    'n8n_runs', (select jsonb_build_object(
        'runs', count(*), 'failed', count(*) filter (where status = 'failed'),
        'stuck_running', count(*) filter (where status = 'running' and started_at < now() - interval '2 hours'))
        from phg_control.workflow_runs where started_at > v_since),
    'harmony_feedback_open', (select count(*) from phg.harmony_feedback where status = 'new')
  );
end $$;

-- Spend guard read model: per pipeline, today (UTC) and last 24 h, with breaches computed here so
-- the rule lives in one reviewed place. success_rate = least(1, successful_outputs / request_count)
-- because some endpoints count several outputs per request (see README open question).
create or replace function phg_control.spend_snapshot() returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare
  v_limit numeric := coalesce((phg_control._setting('spend_daily_credit_limit'))::numeric, 1500);
  v_min_rate numeric := coalesce((phg_control._setting('spend_min_success_rate'))::numeric, 0.70);
  v_min_n int := coalesce((phg_control._setting('spend_min_sample'))::int, 20);
  v_today numeric; v_rows jsonb; v_breaches jsonb := '[]'::jsonb;
begin
  select coalesce(sum(estimated_credits),0) into v_today from public.menu_api_usage_ledger where created_at >= date_trunc('day', now());
  select coalesce(jsonb_agg(p order by p.credits_24h desc), '[]'::jsonb) into v_rows from (
    select l.pipeline,
           sum(l.estimated_credits) filter (where l.created_at >= date_trunc('day', now())) as credits_today,
           sum(l.estimated_credits) as credits_24h,
           sum(l.request_count) as requests_24h,
           sum(l.successful_outputs) as outputs_24h,
           round(least(1, sum(l.successful_outputs)::numeric / nullif(sum(l.request_count),0)), 3) as success_rate_24h,
           k.lane, k.cron_jobname, coalesce(k.confirmed,false) as switch_confirmed,
           (select active from cron.job where jobname = k.cron_jobname) as cron_active,
           (select paused_until > now() from public.phg_menu_worker_leases where lane = k.lane) as lane_paused
      from public.menu_api_usage_ledger l
      left join phg_control.spend_kill_switches k on k.pipeline = l.pipeline
     where l.created_at > now() - interval '24 hours' and l.estimated_credits > 0
     group by l.pipeline, k.lane, k.cron_jobname, k.confirmed) p;

  select coalesce(jsonb_agg(b), '[]'::jsonb) into v_breaches from (
    select 'low_success_rate' as kind, r->>'pipeline' as pipeline,
           (r->>'success_rate_24h')::numeric as value, v_min_rate as threshold,
           r->>'lane' as lane, r->>'cron_jobname' as cron_jobname, (r->>'switch_confirmed')::boolean as switch_confirmed,
           coalesce((r->>'cron_active')::boolean, false) or coalesce(not (r->>'lane_paused')::boolean, false) as still_running
      from jsonb_array_elements(v_rows) r
     where (r->>'requests_24h')::int >= v_min_n and (r->>'success_rate_24h')::numeric < v_min_rate
    union all
    select 'daily_credit_limit', '*', v_today, v_limit, null, null, false, true where v_today > v_limit
  ) b;

  return jsonb_build_object('at', now(), 'day_utc', current_date, 'credits_today', v_today,
    'daily_limit', v_limit, 'min_success_rate', v_min_rate, 'min_sample', v_min_n,
    'pipelines', v_rows, 'breaches', v_breaches);
end $$;

-- Protective auto-pause (PHG-059). Only for kill switches Rob has CONFIRMED; otherwise it files an
-- approval request instead. Recorded as an action_request with decided_by = 'policy:PHG-059' so the
-- audit trail is identical to a human-approved action. Idempotent per pipeline per UTC day.
create or replace function phg_control.guard_pause(p_pipeline text, p_reason text, p_evidence jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  k phg_control.spend_kill_switches%rowtype;
  v_hours numeric := least(72, coalesce((phg_control._setting('spend_auto_pause_hours'))::numeric, 24));
  v_out jsonb := '[]'::jsonb; v_req jsonb; v_key text; v_action text; v_params jsonb;
begin
  select * into k from phg_control.spend_kill_switches where pipeline = p_pipeline;
  if not found or (k.lane is null and k.cron_jobname is null) then
    return jsonb_build_object('pipeline', p_pipeline, 'paused', false, 'reason', 'no kill switch mapped - alert only');
  end if;
  foreach v_action in array array['pause_cron_job','pause_menu_lane'] loop
    v_params := case v_action when 'pause_cron_job' then jsonb_build_object('cron_jobname', k.cron_jobname)
                               else jsonb_build_object('lane', k.lane, 'hours', v_hours) end;
    continue when (v_action = 'pause_cron_job' and k.cron_jobname is null) or (v_action = 'pause_menu_lane' and k.lane is null);
    v_key := 'spend-guard:' || v_action || ':' || p_pipeline || ':' || current_date;
    v_req := phg_control.submit_request(v_action, v_params, p_reason, 'n8n:spend-guard', v_key, p_evidence);
    if k.confirmed then
      update phg_control.action_requests
         set status = 'approved', decided_at = now(), decided_by = 'policy:PHG-059',
             claim_token_hash = encode(extensions.digest(v_key,'sha256'),'hex'), claimed_at = now(), updated_at = now()
       where id = (v_req->>'id')::uuid and status = 'pending';
      v_out := v_out || jsonb_build_array(phg_control.execute_request((v_req->>'id')::uuid, v_key) || jsonb_build_object('auto', true));
    else
      v_out := v_out || jsonb_build_array(v_req || jsonb_build_object('auto', false, 'note', 'kill switch unconfirmed - needs approval'));
    end if;
  end loop;
  return jsonb_build_object('pipeline', p_pipeline, 'requests', v_out);
end $$;

-- -------------------------------------------------------------------------------------
-- 6. Grants: exactly these, nothing else.
-- -------------------------------------------------------------------------------------
revoke all on all functions in schema phg_control from public, anon, authenticated;
grant execute on function
  phg_control.submit_request(text, jsonb, text, text, text, jsonb),
  phg_control.claim_next_request(text),
  phg_control.decide_request(uuid, text, boolean, text, text),
  phg_control.execute_request(uuid, text),
  phg_control.verify_request(uuid),
  phg_control.run_start(text, text, jsonb),
  phg_control.run_finish(bigint, text, jsonb, text, uuid),
  phg_control.run_fail_by_execution(text, text, text),
  phg_control.get_watermark(text),
  phg_control.set_watermark(text, jsonb),
  phg_control.harmony_feedback_digest(bigint, int),
  phg_control.health_snapshot(int),
  phg_control.spend_snapshot(),
  phg_control.guard_pause(text, text, jsonb)
to n8n_control;
-- Harmony / Claude (server side) may FILE requests but never decide or execute them:
grant usage on schema phg_control to service_role;
grant execute on function phg_control.submit_request(text, jsonb, text, text, text, jsonb) to service_role;

-- -------------------------------------------------------------------------------------
-- 7. Fix so a lane pause sticks (FOUND 2026-09-30): public.phg_finish_menu_worker_lease sets
--    paused_until := NULL when a worker finishes with p_pause_seconds = 0, which silently clears
--    any pause set while that worker was running. Keep the later of the two instead.
-- -------------------------------------------------------------------------------------
create or replace function public.phg_finish_menu_worker_lease(p_lane text, p_owner uuid, p_result jsonb, p_pause_seconds integer default 0)
returns boolean language plpgsql security definer set search_path = 'public', 'pg_temp' as $function$
declare n integer;
begin
  update public.phg_menu_worker_leases
     set lease_until = now(), finished_at = now(), last_result = p_result,
         paused_until = greatest(   -- greatest() ignores nulls; null only when neither applies
            case when paused_until > now() then paused_until end,
            case when p_pause_seconds > 0 then now() + make_interval(secs => least(86400, p_pause_seconds)) end
         )
   where lane = p_lane and owner = p_owner;
  get diagnostics n = row_count; return n = 1;
end $function$;

commit;

-- =====================================================================================
-- POST-APPLY CHECKS (read-only; run as postgres after applying)
-- =====================================================================================
-- 1) n8n_control can execute ONLY the 14 phg_control functions plus whatever PUBLIC already has.
--    Anything listed here outside phg_control is a PUBLIC-executable SECURITY DEFINER function
--    that must be reviewed (revoke from public) before n8n_control gets its password.
-- select n.nspname, p.proname, p.prosecdef
--   from pg_proc p join pg_namespace n on n.oid = p.pronamespace
--  where has_function_privilege('n8n_control', p.oid, 'execute') and p.prosecdef
--    and n.nspname not in ('pg_catalog','information_schema') order by 1,2;
-- 2) n8n_control can read no tables:
-- select table_schema, table_name from information_schema.tables
--  where has_table_privilege('n8n_control', quote_ident(table_schema)||'.'||quote_ident(table_name), 'select')
--    and table_schema not in ('pg_catalog','information_schema');
-- 3) Smoke: set role n8n_control; select phg_control.health_snapshot(); select phg_control.spend_snapshot(); reset role;

-- =====================================================================================
-- OPTION B (NOT PROPOSED BY DEFAULT): also mirror runs into public.agent_runs.
-- Requires: alter table public.agent_runs alter column task_id drop not null;
-- then an AFTER UPDATE trigger on phg_control.workflow_runs inserting
-- (run_id = run_key, agent_name = 'n8n:' || workflow, run_status, started_at, finished_at,
--  decision_trace = summary, error_message = error). Changes an existing table - Rob to decide.
-- =====================================================================================

-- ROLLBACK (if needed):
-- drop schema phg_control cascade; drop role n8n_control;
-- and restore phg_finish_menu_worker_lease from the definition captured before applying.
