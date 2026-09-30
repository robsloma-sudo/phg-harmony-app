-- PHG-033 visual-capture gate v1, APPLIED 2026-09-27 ~21:00Z (migration phg_menu_visual_gate_v1 + batched updates).
-- Evidence (sorted documents by discovery method x URL words): drink word -> mostly drinks menus (sitemap 83%);
-- homepage/hub images -> 7 drinks of ~1,300; no menu or drink word -> 35 of ~800; bare "menu" -> mostly food.
-- Rule phg_menu_candidate_signal(method, url): drink word -> keep; homepage_image/menu_hub_image -> skip;
-- download_link/menu_hub_link -> keep; "menu" -> defer; else skip. BEFORE INSERT trigger phg_menu_candidate_gate
-- sets visual_asset_status skipped_no_menu_signal / deferred_generic_menu for new rows.
-- Backfill of waiting rows (ids 1..700000, statuses not_started/retry): 350,672 gated.
-- Queue after: not_started 169,519 + retry 370 kept; deferred_generic_menu 151,922; skipped_no_menu_signal 198,750.
-- Undo: update public.menu_source_candidates set visual_asset_status='not_started'
--         where visual_asset_status in ('skipped_no_menu_signal','deferred_generic_menu');
--       drop trigger phg_menu_candidate_gate on public.menu_source_candidates;
create or replace function public.phg_menu_candidate_signal(p_method text, p_url text)
returns text language sql immutable parallel safe set search_path = '' as $$
  select case
    when lower(coalesce(p_url,'')) ~ '(drink|cocktail|beverage|wine|beer|spirit|liquor|whisk|tequila|mezcal|sake|bar[-_]?menu|happy[-_]?hour|taps?\M|brew)' then 'keep'
    when coalesce(p_method,'') in ('homepage_image','menu_hub_image') then 'skip'
    when coalesce(p_method,'') in ('download_link','menu_hub_link') then 'keep'
    when lower(coalesce(p_url,'')) ~ 'menu' then 'defer'
    else 'skip' end
$$;
create or replace function public.phg_menu_candidate_gate_trg()
returns trigger language plpgsql set search_path = public, pg_temp as $$
declare g text;
begin
  if coalesce(new.visual_asset_status,'not_started') = 'not_started' then
    g := public.phg_menu_candidate_signal(new.discovery_method, new.source_url);
    if g = 'skip' then new.visual_asset_status := 'skipped_no_menu_signal';
    elsif g = 'defer' then new.visual_asset_status := 'deferred_generic_menu'; end if;
  end if;
  return new;
end $$;
drop trigger if exists phg_menu_candidate_gate on public.menu_source_candidates;
create trigger phg_menu_candidate_gate before insert on public.menu_source_candidates
  for each row execute function public.phg_menu_candidate_gate_trg();
