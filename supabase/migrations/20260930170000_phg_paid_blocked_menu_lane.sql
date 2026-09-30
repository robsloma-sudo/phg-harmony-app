-- 2026-09-30 Rob: "I loaded a lot of Firecrawl credits, so let's start enabling Firecrawl for whatever we needed."
-- Paid Firecrawl lane for menu pages that refused our fetcher (source_http_401/403/429; 4,869 on 2026-09-30).
-- Works with extract-menu-candidates v5 (allow_paid:true -> lease lane 'candidate_extraction_paid').

-- 1) the paid lane is a valid worker lane
do $$ begin
  execute replace(pg_get_functiondef('public.phg_try_menu_worker_lease'::regproc),
    $q$('candidate_extraction','visual_acquisition','website_menu_discovery')$q$,
    $q$('candidate_extraction','candidate_extraction_paid','visual_acquisition','website_menu_discovery')$q$);
end $$;

-- 2) results saved by the paid lane are accepted (same stale-run guard, either lane)
do $$ declare d text := pg_get_functiondef('public.phg_save_menu_candidate_extraction'::regproc); begin
  if position($q$lane='candidate_extraction' and owner=p_run_owner$q$ in d) = 0 then raise exception 'save rpc changed; review by hand'; end if;
  execute replace(d, $q$lane='candidate_extraction' and owner=p_run_owner$q$,
                     $q$lane in ('candidate_extraction','candidate_extraction_paid') and owner=p_run_owner$q$);
end $$;

-- 3) dispatcher: 20 blocked HTML candidates per call, oldest first; beverage/mixed/unknown scope only
create or replace function public.phg_dispatch_paid_blocked_menus(p_batch int default 20)
returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare v_ids bigint[]; v_req bigint;
begin
  if exists (select 1 from public.phg_menu_worker_leases where lane = 'candidate_extraction_paid'
              and (lease_until > now() or paused_until > now())) then
    return jsonb_build_object('status', 'worker_busy_or_paused');
  end if;
  select coalesce(array_agg(id), '{}') into v_ids from (
    select id from public.menu_source_candidates
     where source_format = 'html' and is_food_only = false
       and menu_scope in ('beverage','beverage_candidate','mixed','unknown','food_candidate')
       and last_error ~ 'source_http_(401|403|429)' and extraction_attempt_count < 6
       and (status = 'review' or (status = 'retry' and (extraction_next_retry_at is null or extraction_next_retry_at <= now())))
     order by id limit least(20, greatest(1, p_batch))) x;
  if cardinality(v_ids) = 0 then return jsonb_build_object('status', 'nothing_blocked'); end if;
  select net.http_post(url := 'https://lqjtwabzmgjcufftuqvu.supabase.co/functions/v1/extract-menu-candidates',
    headers := jsonb_build_object('Content-Type','application/json','x-ingest-token',(select value from public.internal_secrets where key='ingest_token')),
    body := jsonb_build_object('batch', 20, 'concurrency', 3, 'allow_paid', true, 'candidate_ids', to_jsonb(v_ids)),
    timeout_milliseconds := 90000) into v_req;
  return jsonb_build_object('status', 'dispatched', 'request_id', v_req, 'count', cardinality(v_ids));
end $$;
revoke all on function public.phg_dispatch_paid_blocked_menus(int) from public, anon, authenticated;

-- 4) cron: every minute (the lane lease keeps calls from overlapping)
select cron.schedule('gtt-extract-paid-blocked', '* * * * *',
  $$SET statement_timeout='10s'; SET lock_timeout='500ms'; SELECT public.phg_dispatch_paid_blocked_menus(20);$$);
