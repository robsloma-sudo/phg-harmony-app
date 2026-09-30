-- 2026-09-29 Harmony: all brand names for hearing (Rob: "deploy all brand names").
-- Read-only view of the distinct brand names in US TTB label approvals (~14,200), so phg-speech-transcribe can load
-- them in ~15 pages instead of paging all 50k approval rows. No data is written or changed.
-- Access: service_role only (the view is not exposed to anon/authenticated); security_invoker keeps the base
-- table's RLS for any other caller.
-- Rollback: drop view if exists public.v_harmony_brand_names;
set local lock_timeout = '3s';

create or replace view public.v_harmony_brand_names
with (security_invoker = true) as
select min(btrim(brand_name_raw)) as name, count(*)::int as labels
from public.cola_label_approvals
where brand_name_raw is not null and length(btrim(brand_name_raw)) >= 3
group by lower(btrim(brand_name_raw));

revoke all on public.v_harmony_brand_names from public, anon, authenticated;
grant select on public.v_harmony_brand_names to service_role;

comment on view public.v_harmony_brand_names is
  'Distinct TTB COLA brand names for Harmony name repair (phg-speech-transcribe). service_role only.';
