-- STATUS: NOT APPLIED (2026-09-27 ~22:05Z). Applying the library-wide rollout + cron was stopped by the session safety
-- check; waiting for Rob's explicit go-ahead.
-- PHG-034 rollout: apply capture v2 to the whole library, not just Rob's examples.
--  * phg_capture_v2_topup(target): keeps ~target pages waiting in the v2 lane, in priority order:
--      1 first-screen-only railway screenshots (height = 1000)   2 drinks documents / drink-word links
--      3 every other ready HTML screenshot (railway or firecrawl)
--  * pages whose v2 attempt hits a CAPTCHA / bot wall and whose OLD image is one screen tall are the bot page
--    itself: their document is classed not_menu + tag bot_check (rules_version 'bot_check_v1'), so the gallery
--    stops showing them. Undo: delete from phg_menu_doc_class where rules_version='bot_check_v1'
--    (the classifier cron re-adds its own class).
--  * cron phg-capture-v2-topup every 5 minutes.
create or replace function public.phg_capture_v2_topup(p_target int default 400)
returns jsonb language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare v_wait int; v_ids bigint[]; v_q int := 0; v_bot int := 0;
begin
  if not pg_try_advisory_xact_lock(830927, 34) then return jsonb_build_object('status','busy'); end if;

  -- bot-check documents (see header)
  insert into public.phg_menu_doc_class (document_id, menu_kind, tags, reason, rules_version)
  select distinct p.menu_visual_document_id, 'not_menu', array['bot_check'], 'capture v2 hit a CAPTCHA/bot wall; old capture one screen tall', 'bot_check_v1'
  from public.menu_visual_pages p join public.phg_capture_v2_backup b on b.page_id = p.id
  where p.render_strategy = 'html_capture_v2' and p.render_last_error like '%bot_check_blocked%'
    and coalesce(b.old_height, 0) <= 1100 and coalesce(p.capture_method, '') <> 'html_capture_v2'
  on conflict (document_id) do update set menu_kind = 'not_menu', tags = array['bot_check'], reason = excluded.reason,
     rules_version = 'bot_check_v1'
   where public.phg_menu_doc_class.rules_version is distinct from 'bot_check_v1';
  get diagnostics v_bot = row_count;
  -- a later v2 attempt got through: it is a real page after all, let the text classifier decide again
  delete from public.phg_menu_doc_class k where k.rules_version = 'bot_check_v1'
     and exists (select 1 from public.menu_visual_pages p where p.menu_visual_document_id = k.document_id
                 and p.capture_method = 'html_capture_v2');

  select count(*) into v_wait from public.menu_visual_pages
   where render_strategy = 'html_capture_v2' and coalesce(capture_method, '') <> 'html_capture_v2'
     and (render_next_retry_at is null or render_next_retry_at < '2099-01-01');
  if v_wait < p_target / 2 then
    select coalesce(array_agg(id), '{}') into v_ids from (
      select p.id
      from public.menu_visual_pages p
      join public.menu_visual_documents d on d.id = p.menu_visual_document_id and d.asset_kind = 'html'
      left join public.menu_source_candidates c on c.id = d.menu_source_candidate_id
      left join public.phg_menu_doc_class k on k.document_id = d.id
      where p.render_status = 'ready' and p.capture_method in ('railway_playwright_screenshot', 'firecrawl_full_page_screenshot')
        and p.render_strategy is distinct from 'html_capture_v2'
        and not exists (select 1 from public.phg_capture_v2_backup b where b.page_id = p.id)
      order by (p.capture_method = 'railway_playwright_screenshot' and p.height = 1000) desc,
               (k.menu_kind in ('beverage','mixed','happy_hour')
                or public.phg_menu_candidate_rule(c.discovery_method, c.source_url) in ('keep_word','keep_method')) desc,
               p.id
      limit p_target - v_wait) x;
    if cardinality(v_ids) > 0 then v_q := public.phg_capture_v2_queue(v_ids, 'rollout'); end if;
  end if;
  return jsonb_build_object('status','ok','waiting',v_wait,'queued',v_q,'bot_check_docs',v_bot);
end $$;
revoke all on function public.phg_capture_v2_topup(int) from public, anon, authenticated;

select cron.schedule('phg-capture-v2-topup', '*/5 * * * *', $$SET statement_timeout='20s'; SELECT public.phg_capture_v2_topup(400);$$);
