-- APPLIED 2026-09-29 as migration phg_dispatch_visual_sibling_fast.
-- Menu acquisition had stalled since 2026-09-27 22:08 UTC: the dispatcher's PHG-034 sibling pick ("other drinks pages
-- of venues that already have a drinks menu") took 14-16 s (nested loop over ~550k candidates) and job 16 hit its 5 s
-- statement timeout on every run (1,079 failures in 6 h). Fix: partial index phg_visual_acq_account_idx (created
-- CONCURRENTLY first) + one index lookup per venue (~0.15 s). Nothing else in the function changed.
create index if not exists phg_visual_acq_account_idx on public.menu_source_candidates (account_id, visual_asset_attempt_count, id)
  where visual_asset_status in ('not_started','retry');
-- function body: see live public.phg_dispatch_menu_recovery_work(text); the sibling pick is now:
--   SELECT y.id FROM (SELECT DISTINCT d.account_id FROM menu_visual_documents d JOIN phg_menu_doc_class k ON k.document_id=d.id
--                     WHERE k.menu_kind IN ('beverage','mixed','happy_hour') AND d.account_id IS NOT NULL) acc
--   CROSS JOIN LATERAL (SELECT c.id, c.visual_asset_attempt_count FROM menu_source_candidates c WHERE c.account_id=acc.account_id
--     AND c.visual_asset_status IN ('not_started','retry') AND c.visual_asset_attempt_count<4
--     AND (c.visual_asset_next_retry_at IS NULL OR c.visual_asset_next_retry_at<=now()) AND NOT(c.id=ANY(v_ids))
--     ORDER BY c.visual_asset_attempt_count, c.id LIMIT 1) y ORDER BY y.visual_asset_attempt_count, y.id LIMIT 4
