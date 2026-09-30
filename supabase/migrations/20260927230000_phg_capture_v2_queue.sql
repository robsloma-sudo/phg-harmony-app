-- PHG-034 capture v2: a separate queue lane for the new HTML capture worker (GitHub Actions, OIDC-authenticated
-- Edge function menu-capture-v2-api). Pages moved into the lane get render_strategy 'html_capture_v2', which the
-- old Railway worker never claims (its query only takes firecrawl_screenshot_after_download_check /
-- railway_external_html_screenshot). Every moved page is backed up first; v2 images go to a NEW storage path
-- (page-NNN.v2.jpg) so the old image stays in the bucket. Rollback: select public.phg_capture_v2_rollback(ids).

create table if not exists public.phg_capture_v2_backup (
  page_id bigint primary key,
  document_id bigint,
  old_render_strategy text, old_render_status text, old_capture_method text,
  old_page_image_bucket text, old_page_image_path text, old_width int, old_height int,
  reason text, queued_at timestamptz default now()
);
alter table public.phg_capture_v2_backup enable row level security;
revoke all on public.phg_capture_v2_backup from anon, authenticated;

create or replace function public.phg_capture_v2_queue(p_page_ids bigint[], p_reason text default 'manual')
returns int language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare n int;
begin
  insert into public.phg_capture_v2_backup (page_id, document_id, old_render_strategy, old_render_status, old_capture_method,
         old_page_image_bucket, old_page_image_path, old_width, old_height, reason)
  select p.id, p.menu_visual_document_id, p.render_strategy, p.render_status, p.capture_method,
         p.page_image_bucket, p.page_image_path, p.width, p.height, p_reason
  from public.menu_visual_pages p
  join public.menu_visual_documents d on d.id = p.menu_visual_document_id
  where p.id = any (p_page_ids) and d.asset_kind = 'html' and p.render_status <> 'processing'
  on conflict (page_id) do nothing;
  -- the page keeps serving its old image (render_status stays 'ready') until v2 replaces it
  update public.menu_visual_pages p
     set render_strategy = 'html_capture_v2', render_next_retry_at = null, render_attempt_count = 0,
         render_last_error = 'capture_v2_queued|' || p_reason, updated_at = now()
   where p.id = any (p_page_ids) and exists (select 1 from public.phg_capture_v2_backup b where b.page_id = p.id)
     and p.render_status <> 'processing';
  get diagnostics n = row_count;
  return n;
end $$;

create or replace function public.phg_capture_v2_rollback(p_page_ids bigint[] default null)
returns int language plpgsql security definer set search_path to 'public', 'pg_temp' as $$
declare n int;
begin
  update public.menu_visual_pages p
     set render_strategy = b.old_render_strategy, render_status = b.old_render_status, capture_method = b.old_capture_method,
         page_image_bucket = b.old_page_image_bucket, page_image_path = b.old_page_image_path,
         width = b.old_width, height = b.old_height, render_last_error = null, updated_at = now()
    from public.phg_capture_v2_backup b
   where b.page_id = p.id and (p_page_ids is null or p.id = any (p_page_ids));
  get diagnostics n = row_count;
  return n;
end $$;

revoke all on function public.phg_capture_v2_queue(bigint[], text) from public, anon, authenticated;
revoke all on function public.phg_capture_v2_rollback(bigint[]) from public, anon, authenticated;
