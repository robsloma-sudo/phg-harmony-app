-- PHG-033 capture-gate review (applied 2026-09-27 ~21:30Z). Lets Rob see numbered, shuffled samples of the
-- documents each capture rule keeps, so he can reject the ones that are not drinks menus.
-- phg_menu_candidate_rule mirrors phg_menu_candidate_signal (20260927210000) but splits 'keep' by reason.

create or replace function public.phg_menu_candidate_word(p_url text) returns text
language sql immutable parallel safe set search_path to '' as $$
  select substring(lower(coalesce(p_url,'')) from '(drink|cocktail|beverage|wine|beer|spirit|liquor|whisk|tequila|mezcal|sake|bar[-_]?menu|happy[-_]?hour|taps?\M|brew)')
$$;

create or replace function public.phg_menu_candidate_rule(p_method text, p_url text) returns text
language sql immutable parallel safe set search_path to '' as $$
  select case
    when public.phg_menu_candidate_word(p_url) is not null then 'keep_word'
    when coalesce(p_method,'') in ('homepage_image','menu_hub_image') then 'skip'
    when coalesce(p_method,'') in ('download_link','menu_hub_link') then 'keep_method'
    when lower(coalesce(p_url,'')) ~ 'menu' then 'defer'
    else 'skip' end
$$;

-- phg_corpus_browse_documents was patched IN PLACE (pg_get_functiondef + replace + EXECUTE):
--   + p->'rule'  (array of keep_word|keep_method|defer|skip), joined via menu_source_candidates sc
--   + sort 'shuffle' ordered by md5(p->>'seed' || id) - stable across pages for one seed
--   + rows carry cand_method, cand_rule, cand_word, cand_url
-- Rollback: re-run the function body from 20260927180000 plus the 18.49.8 menu_kind/has/hide patch
-- (or replace() the added lines back out).
