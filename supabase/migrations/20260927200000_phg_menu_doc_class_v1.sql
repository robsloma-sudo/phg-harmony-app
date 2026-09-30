-- PHG-030 menu type v1 (text rules), APPLIED 2026-09-27 ~20:15Z via execute_sql.
-- Table phg_menu_doc_class: one menu_kind per document + multi-label tags, from live staged items
-- (menu_page_url = original_menu_url) and URL keywords. No text => 'unread' (unknown, never a guess).
-- Kinds: delivery | unread | happy_hour (>=60% items in happy-hour sections) | specials (>=60% in dated/day/event
-- sections) | not_menu (text but no drink or food items) | mixed (>=3 drinks and >=3 food) | beverage | food.
-- Tags: cocktails, beer, wine, spirits, sake_soju, non_alcoholic, food, happy_hour, specials, brunch, delivery.
-- Result 2026-09-27: unread 11,287; beverage 5,253; food 2,406; not_menu 1,147; mixed 471; happy_hour 303;
-- specials 187; delivery 6. Spot checks: Terrace 225 specials, Downtown Brew 675 beverage, El Centenario 629
-- beverage, UMI 16922 unread; random food sample all food.
-- The full statement is in the session transcript; next step folds it into a refresh function + browse filters.
create table if not exists public.phg_menu_doc_class (
  document_id bigint primary key, menu_kind text not null, tags text[] not null default '{}',
  bev_items int, food_items int, hh_items int, spec_items int, total_items int,
  reason text, rules_version text not null default 'v1-text', classified_at timestamptz not null default now());
alter table public.phg_menu_doc_class enable row level security;
revoke all on public.phg_menu_doc_class from anon, authenticated;
