-- DRAFT — NOT APPLIED. Needs Rob's approval. Spec: handoff/HARMONY_CONVERSATION_MODEL.md §4D (4D.1-4D.4), §0, §10
-- Apply order: 02 -> 04 -> 03 -> 05 -> 06 (this file is FOURTH). 04 MUST be applied before 05: coach_actions.metric_key
--   has an FK to phg.metric_definitions (created in 04); applying 05 first fails with "relation does not exist".
--
-- What this does (plain English)
--   The profit coach's storage. It does NOT compute anything yet (detectors run later as database functions).
--   * phg.coach_detectors (admin library, shared): each check Harmony can run — area, what data it needs, the rule,
--     the dollar-impact formula, thresholds and the wording. Seeded with the starting set from §4D.2, all 'planned'.
--   * phg.coach_findings (per project): one finding per detector per period/location — problem, $ impact, confidence,
--     evidence, status new | seen | acted | dismissed | resolved. Ranked by impact x confidence.
--   * phg.coach_actions (per project): what was done about a finding — a Command Center proposal id, the outcome, and
--     the metric before/after, so Harmony learns which advice pays off.
--   * public.phg_harmony_coach_db(op, args): service_role reads + marking a finding seen/dismissed.
--
-- How it builds on management_alert_* (spec: "Builds on management_alert_* rather than duplicating it")
--   Live schema (2026-09-28): there are TWO alert-state tables with the same shape idea:
--     phg.management_alert_states (7 rows, used by phg_management_sync_alert_lifecycle, phg_management_alert_inbox,
--       phg_command_attention_queue) — the one in use;
--     phg.management_alert_state (0 rows, used by phg_management_operations_state / acknowledge_lifecycle_alert).
--   Both are keyed by (menu_project_id, location_key, lifecycle_key), NOT by account; alert keys seen today:
--   actual_cogs_missing, labor_incomplete, budget_actual:net_sales, forecast:sales.
--   So: a finding may point at the alert it came from (management_alert_state_id -> management_alert_states), and a
--   detector may declare the alert_key it consumes. Alerts stay the "something changed" signal; findings add dollars,
--   evidence, actions and learning. No alert data is copied or moved. Which of the two alert tables is canonical is an
--   open question for Rob; this draft links only to management_alert_states (the populated one).
--
-- Project guards (triggers, because the referenced tables are not keyed by account_id)
--   coach_findings: location_id -> sales_locations.account_id, menu_project_id -> menu_projects.account_id,
--     reporting_period_id -> reporting_periods.account_id, management_alert_state_id -> management_alert_states
--     .menu_project_id -> menu_projects.account_id: each must equal the finding's account_id.
--   coach_actions: finding and proposal_id (command_action_proposals -> command_sessions.menu_project_id ->
--     menu_projects.account_id) must be in the action's project.
-- finding_mark: status transitions are forward-only: new -> seen -> acted | dismissed | resolved; dismissed only from
--   new/seen/acted; only owner/admin may dismiss. Through this door a person can set seen or dismissed only.
--
-- Rollback (scripted; run as postgres in ONE transaction, AFTER rolling back 06)
--   begin;
--   set local lock_timeout = '3s';
--   create table if not exists phg._rb05_coach_findings as select * from phg.coach_findings;
--   create table if not exists phg._rb05_coach_actions  as select * from phg.coach_actions;
--   revoke all on phg._rb05_coach_findings, phg._rb05_coach_actions from public, anon, authenticated;
--   drop function if exists public.phg_harmony_coach_db(text, jsonb);
--   drop trigger if exists coach_actions_guard on phg.coach_actions; drop function if exists phg.coach_actions_guard();
--   drop trigger if exists coach_findings_guard on phg.coach_findings; drop function if exists phg.coach_findings_guard();
--   drop table if exists phg.coach_actions, phg.coach_findings, phg.coach_detectors;
--   -- verify (expect: all nulls)
--   select to_regclass('phg.coach_actions') ca, to_regclass('phg.coach_findings') cf, to_regclass('phg.coach_detectors') cd,
--          to_regprocedure('public.phg_harmony_coach_db(text,jsonb)') fn, to_regprocedure('phg.coach_actions_guard()') g1,
--          to_regprocedure('phg.coach_findings_guard()') g2;
--   commit;

begin;

set local lock_timeout = '3s';   -- new tables only, but FKs lock referenced tables briefly; on 55P03 retry

create table if not exists phg.coach_detectors (
  key             text primary key,
  area            text not null check (area in ('labor','cogs','waste','pricing','menu_mix','purchasing','comps','budget','calendar_setup')),
  label           text not null,
  description     text,
  requirement     jsonb not null default '{}'::jsonb,   -- {"metrics":["labor_pct"],"settings":["targets.labor_pct"],"min_days":7,"tables":[...]}
  rule            jsonb not null default '{}'::jsonb,   -- {"compare":"labor_pct","against":"target","op":">","by_pct_points":1}
  impact_formula  text,                                 -- plain words; the function is the truth
  impact_function text,                                 -- planned DB function returning impact_usd + evidence
  thresholds      jsonb not null default '{}'::jsonb,   -- {"min_impact_usd_week":50,"min_confidence":0.6}
  wording         jsonb not null default '{}'::jsonb,   -- {"headline":"Labor was {value}% this week vs {target} target ...","actions":[...]}
  alert_key       text,                                 -- management_alert_states.alert_key this detector consumes/raises, if any
  uses_market     boolean not null default false,       -- compares with PHG market data (must name the sample)
  status          text not null default 'planned' check (status in ('planned','live','retired')),
  version         int not null default 1,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create table if not exists phg.coach_findings (
  id                         uuid primary key default gen_random_uuid(),
  account_id                 uuid not null references phg.accounts(id) on delete cascade,
  detector_key               text not null references phg.coach_detectors(key),
  detector_version           int not null default 1,
  location_id                uuid references phg.sales_locations(id) on delete set null,
  revenue_center             text,
  menu_project_id            uuid references phg.menu_projects(id) on delete set null,
  period_start               date,
  period_end                 date,
  reporting_period_id        uuid references phg.reporting_periods(id) on delete set null,
  fingerprint                text not null,             -- detector + subject + period; a re-run updates instead of duplicating
  headline                   text not null,
  impact_usd                 numeric,                   -- from impact_function, never model arithmetic
  impact_basis               text check (impact_basis in ('week','month','year','period')),
  confidence                 numeric check (confidence between 0 and 1),
  rank_score                 numeric generated always as (coalesce(impact_usd, 0) * coalesce(confidence, 0)) stored,
  evidence                   jsonb not null default '[]'::jsonb,   -- numbers + source record refs (tappable)
  assumptions                jsonb not null default '[]'::jsonb,
  market_sample              jsonb,                     -- {"venues":38,"radius_mi":5,"as_of":"..."} when uses_market
  suggested_actions          jsonb not null default '[]'::jsonb,   -- 1-3 actions, each can become a proposal
  status                     text not null default 'new' check (status in ('new','seen','acted','dismissed','resolved')),
  seen_at                    timestamptz,
  dismissed_at               timestamptz,
  dismissed_by               uuid,
  dismiss_reason             text,
  reopen_if_worse_than       numeric,                   -- dismissed stays dismissed unless impact exceeds this
  resolved_at                timestamptz,
  management_alert_state_id  uuid references phg.management_alert_states(id) on delete set null,
  created_at                 timestamptz not null default now(),
  updated_at                 timestamptz not null default now(),
  unique (account_id, detector_key, fingerprint)
);
create index if not exists coach_findings_rank on phg.coach_findings (account_id, status, rank_score desc);
-- FK columns (on delete set null on the parent must not scan the whole table)
create index if not exists coach_findings_alert_state on phg.coach_findings (management_alert_state_id) where management_alert_state_id is not null;
create index if not exists coach_findings_location    on phg.coach_findings (location_id) where location_id is not null;
create index if not exists coach_findings_menu_project on phg.coach_findings (menu_project_id) where menu_project_id is not null;
create index if not exists coach_findings_rperiod     on phg.coach_findings (reporting_period_id) where reporting_period_id is not null;

create table if not exists phg.coach_actions (
  id             uuid primary key default gen_random_uuid(),
  account_id     uuid not null references phg.accounts(id) on delete cascade,
  finding_id     uuid not null references phg.coach_findings(id) on delete cascade,
  action_kind    text not null,                          -- 'reprice_item','change_par','adjust_schedule','swap_ingredient','set_calendar' ...
  description    text not null,
  proposal_id    uuid references phg.command_action_proposals(id) on delete set null,
  status         text not null default 'suggested' check (status in ('suggested','proposed','executed','rejected','abandoned')),
  metric_key     text references phg.metric_definitions(key),   -- from file 04
  metric_before  numeric,
  metric_after   numeric,
  measured_at    timestamptz,
  outcome        text check (outcome in ('improved','no_change','worse','unknown')),
  outcome_note   text,
  created_by     uuid,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index if not exists coach_actions_finding on phg.coach_actions (finding_id);
create index if not exists coach_actions_proposal on phg.coach_actions (proposal_id) where proposal_id is not null;

-- guards: a finding / action and everything it points at must stay in its project
create or replace function phg.coach_findings_guard() returns trigger
language plpgsql security definer set search_path = phg, pg_temp as $$
begin
  if new.location_id is not null and not exists (
       select 1 from phg.sales_locations l where l.id = new.location_id and l.account_id = new.account_id) then
    raise exception 'location belongs to another project';
  end if;
  if new.menu_project_id is not null and not exists (
       select 1 from phg.menu_projects mp where mp.id = new.menu_project_id and mp.account_id = new.account_id) then
    raise exception 'menu project belongs to another project';
  end if;
  if new.reporting_period_id is not null and not exists (
       select 1 from phg.reporting_periods rp where rp.id = new.reporting_period_id and rp.account_id = new.account_id) then
    raise exception 'reporting period belongs to another project';
  end if;
  if new.management_alert_state_id is not null and not exists (
       select 1 from phg.management_alert_states a join phg.menu_projects mp on mp.id = a.menu_project_id
        where a.id = new.management_alert_state_id and mp.account_id = new.account_id) then
    raise exception 'alert belongs to another project';
  end if;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists coach_findings_guard on phg.coach_findings;
create trigger coach_findings_guard before insert or update on phg.coach_findings
  for each row execute function phg.coach_findings_guard();

create or replace function phg.coach_actions_guard() returns trigger
language plpgsql security definer set search_path = phg, pg_temp as $$
begin
  if not exists (select 1 from phg.coach_findings f where f.id = new.finding_id and f.account_id = new.account_id) then
    raise exception 'finding belongs to another project';
  end if;
  if new.proposal_id is not null and not exists (
       select 1 from phg.command_action_proposals p
         join phg.command_sessions s on s.id = p.session_id
         join phg.menu_projects mp on mp.id = s.menu_project_id
        where p.id = new.proposal_id and mp.account_id = new.account_id) then
    raise exception 'proposal belongs to another project';
  end if;
  new.updated_at := now();
  return new;
end $$;
revoke all on function phg.coach_findings_guard(), phg.coach_actions_guard() from public, anon, authenticated;
drop trigger if exists coach_actions_guard on phg.coach_actions;
create trigger coach_actions_guard before insert or update on phg.coach_actions
  for each row execute function phg.coach_actions_guard();

alter table phg.coach_detectors enable row level security;
alter table phg.coach_findings  enable row level security;
alter table phg.coach_actions   enable row level security;
revoke all on phg.coach_detectors, phg.coach_findings, phg.coach_actions from public, anon, authenticated;

-- ---------------------------------------------------------------------------------------------------------------
-- Seed: starting detectors (§4D.2). All 'planned'; wording uses placeholders, never numbers.
-- ---------------------------------------------------------------------------------------------------------------
insert into phg.coach_detectors (key, area, label, requirement, impact_formula, alert_key, uses_market, wording) values
  ('labor_over_target','labor','Labor % over target',
     '{"metrics":["labor_pct","sales_per_labor_hour"],"settings":["targets.labor_pct","calendar.week_start"]}',
     '(labor_pct - target) / 100 * net_sales for the period', 'labor_incomplete', false,
     '{"headline":"Labor was {value}% {period} vs {target} target: {driver}. About {impact} over."}'),
  ('labor_low_sales_per_hour','labor','Hours vs sales by role and daypart',
     '{"metrics":["sales_per_labor_hour"],"settings":["labor.roles"]}', 'hours above the business''s sales-per-hour floor x hourly rate', null, false, '{}'),
  ('labor_scheduled_vs_actual','labor','Scheduled vs actual hours','{"tables":["phg.labor_shifts"]}', '(actual - scheduled hours) x rate', null, false, '{}'),
  ('labor_overtime','labor','Overtime','{"tables":["phg.labor_shifts"]}', 'overtime hours x (overtime rate - regular rate)', null, false, '{}'),
  ('cogs_category_drift','cogs','Category COGS % drift','{"metrics":["cogs_pct_by_category"],"settings":["targets.cogs_pct_by_category"]}',
     '(actual % - target %) / 100 x category sales', 'actual_cogs_missing', false, '{}'),
  ('cogs_theoretical_vs_actual','cogs','Theoretical vs actual COGS (waste, overpour, theft, missing invoices)',
     '{"functions":["public.phg_sales_theoretical_cogs","public.phg_cogs_reconcile"]}', 'actual COGS $ - theoretical COGS $', 'actual_cogs_missing', false, '{}'),
  ('waste_inventory_variance','waste','Inventory variance by item','{"tables":["phg.inventory_counts","phg.sales_items"]}',
     '(actual usage - usage explained by sales) x unit cost, per week', null, false, '{}'),
  ('waste_prep_yield','waste','Prep yield vs recipe','{"tables":["phg.prep_recipe_versions","phg.inventory_counts"]}', 'yield shortfall x batch cost', null, false, '{}'),
  ('pricing_margin_below_target','pricing','Item margin vs target','{"functions":["public.phg_recipe_cost"],"settings":["targets.cogs_pct_by_category"]}',
     '(price needed for target COGS - current price) x units sold', null, false, '{}'),
  ('pricing_vs_market','pricing','Price vs nearby market for the same drink','{"tables":["public.menu_items","public.menu_item_cocktail_core","public.accounts"]}',
     '(market median - price) x units sold, capped by elasticity assumption', null, true,
     '{"headline":"Your {item} is {price}; {n} bars within {radius} miles charge a median {median}. At your volume, +{delta} is about {impact} a month."}'),
  ('pricing_stale_after_cost_rise','pricing','Price not updated after a cost rise','{"tables":["phg.purchase_costs","phg.menu_item_prices"]}',
     'cost increase x units sold since the rise', null, false, '{}'),
  ('menu_mix_quadrants','menu_mix','Menu engineering quadrants','{"functions":["public.phg_menu_engineering_analysis"]}',
     'contribution gain from repricing/repositioning plowhorses and puzzles', null, false, '{}'),
  ('purchasing_vendor_price_increase','purchasing','Vendor price increases','{"functions":["public.phg_purchase_price_variance"]}',
     'price change x quantity bought', null, false, '{}'),
  ('purchasing_category_spend_trend','purchasing','Category spend trend (e.g. dairy)','{"tables":["phg.purchase_invoice_lines"]}',
     'spend above trailing baseline', null, false, '{}'),
  ('comps_over_limit','comps','Comp % over limit','{"metrics":["comp_pct"],"settings":["targets.comp_limit_pct"]}',
     '(comp % - limit) / 100 x gross sales', null, false,
     '{"headline":"Comps were {value}% {period} vs a {target}% limit, {share} on {day}."}'),
  ('budget_declining_pace','budget','Declining budget pace','{"metrics":["declining_budget_remaining"],"settings":["targets.weekly_budgets"]}',
     'projected spend at current pace - budget', 'budget_actual:net_sales', false, '{}'),
  ('calendar_rhythm_mismatch','calendar_setup','Reporting periods vs business rhythm','{"settings":["calendar.week_start"],"tables":["phg.sales_daily"]}',
     'none (clarity finding, impact 0)', null, false, '{}'),
  ('setup_missing_data','calendar_setup','Missing data that blocks answers','{"tables":["phg.setting_definitions","phg.account_settings","phg.data_sources"]}',
     'none (lists what to add and what it unlocks)', 'labor_incomplete', false, '{}')
on conflict (key) do nothing;

-- ---------------------------------------------------------------------------------------------------------------
-- Dispatcher (service_role only)
-- ---------------------------------------------------------------------------------------------------------------
create or replace function public.phg_harmony_coach_db(p_op text, p_args jsonb)
returns jsonb language plpgsql volatile security definer set search_path = phg, pg_temp as $$
declare
  v_user    uuid := nullif(p_args->>'user', '')::uuid;
  v_account uuid := nullif(p_args->>'account', '')::uuid;
  v_limit   int := 10;
  v_new     text;
  v_cur     text;
begin
  if v_user is null or v_account is null then raise exception 'user and account required'; end if;
  if not exists (select 1 from phg.account_memberships where user_id = v_user and account_id = v_account and status = 'active') then
    raise exception 'not a member of that account';
  end if;

  if p_op = 'findings_list' then
    if nullif(p_args->>'limit', '') is not null then
      if p_args->>'limit' !~ '^\d{1,4}$' then raise exception 'limit must be a whole number'; end if;
      v_limit := (p_args->>'limit')::int;
    end if;
    return coalesce((select jsonb_agg(jsonb_build_object('id', f.id, 'detector', f.detector_key, 'area', d.area, 'headline', f.headline,
                       'impact_usd', f.impact_usd, 'impact_basis', f.impact_basis, 'confidence', f.confidence, 'status', f.status,
                       'period_start', f.period_start, 'period_end', f.period_end, 'evidence', f.evidence,
                       'suggested_actions', f.suggested_actions) order by f.rank_score desc)
      from (select * from phg.coach_findings
             where account_id = v_account
               and status = any (coalesce((select array_agg(value) from jsonb_array_elements_text(p_args->'status')), array['new','seen']))
             order by rank_score desc
             limit least(50, greatest(1, v_limit))) f
      join phg.coach_detectors d on d.key = f.detector_key), '[]'::jsonb);

  elsif p_op = 'finding_mark' then
    -- a person sets seen or dismissed only; 'acted' and 'resolved' are set by the action and detector runs.
    -- forward-only: new -> seen -> acted | dismissed | resolved; dismissed only from new/seen/acted; dismiss = owner/admin
    v_new := coalesce(p_args->>'status', '');
    if v_new not in ('seen','dismissed') then raise exception 'status must be seen or dismissed'; end if;
    if v_new = 'dismissed' and not exists (
         select 1 from phg.account_memberships am where am.user_id = v_user and am.account_id = v_account
            and am.status = 'active' and am.role in ('owner','admin')) then
      raise exception 'only owners and admins can dismiss a finding';
    end if;
    select coalesce(f.status, 'new') into v_cur from phg.coach_findings f
     where f.id = nullif(p_args->>'id', '')::uuid and f.account_id = v_account for update;
    if not found then return jsonb_build_object('ok', false, 'reason', 'not found'); end if;
    if v_new = 'seen' and v_cur <> 'new' then
      -- already seen or further along: keep the status, only stamp seen_at
      update phg.coach_findings set seen_at = coalesce(seen_at, now()), updated_at = now()
       where id = nullif(p_args->>'id', '')::uuid and account_id = v_account;
      return jsonb_build_object('ok', true, 'status', v_cur, 'changed', false);
    end if;
    if v_new = 'dismissed' and v_cur not in ('new','seen','acted') then
      raise exception 'a % finding cannot be dismissed', v_cur;
    end if;
    update phg.coach_findings set
      status = v_new,
      seen_at = coalesce(seen_at, now()),
      dismissed_at = case when v_new = 'dismissed' then now() else dismissed_at end,
      dismissed_by = case when v_new = 'dismissed' then v_user else dismissed_by end,
      dismiss_reason = case when v_new = 'dismissed' then left(p_args->>'reason', 500) else dismiss_reason end,
      reopen_if_worse_than = case when v_new = 'dismissed' then coalesce(impact_usd, 0) else reopen_if_worse_than end,
      updated_at = now()
    where id = nullif(p_args->>'id', '')::uuid and account_id = v_account;
    return jsonb_build_object('ok', true, 'status', v_new, 'changed', true);
  end if;

  raise exception 'unknown op %', p_op;
end $$;
revoke all on function public.phg_harmony_coach_db(text, jsonb) from public, anon, authenticated;
grant execute on function public.phg_harmony_coach_db(text, jsonb) to service_role;

commit;
