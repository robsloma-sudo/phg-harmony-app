-- PHG-035 classifier v2 ('v2-lists'): which lists a menu has (beer / wine / tequila & mezcal / whiskey / other
-- spirits / cocktails / sake & soju / non-alcoholic / food / happy hour / specials) and what kind of menu it is.
--  * documents with page text from capture v2 (phg_page_text) use phg_menu_text_profile over all their pages' text;
--  * documents without it keep the item-based rules (staging_menu_extract) and gain list tags from section names
--    and item names (tequila_mezcal, whiskey), so the old corpus gets the new tags too;
--  * a document is re-read when its page text is newer than its class.
-- Missing text stays 'unread' (unknown, never "not a drinks menu").
alter table public.phg_menu_doc_class add column if not exists lists jsonb;

create or replace function public.phg_menu_doc_classify(p_limit integer default 500, p_reclassify boolean default false)
returns integer language plpgsql security definer set search_path to 'public', 'pg_temp' as $function$
declare v_n integer; v_m integer;
begin
  set local statement_timeout = '50s';
  -- (1) documents with captured page text
  with docs as (
    select d.id, lower(coalesce(d.original_menu_url,'')||' '||coalesce(d.discovered_asset_url,'')) u,
           (select string_agg(t.text, E'\n' order by t.page_id) from public.phg_page_text t where t.document_id = d.id) txt
    from public.menu_visual_documents d
    where exists (select 1 from public.phg_page_text t where t.document_id = d.id
                  and (p_reclassify or not exists (select 1 from public.phg_menu_doc_class k where k.document_id = d.id
                                                   and (k.classified_at >= t.captured_at or k.rules_version = 'bot_check_v1'))))
    order by d.id desc limit greatest(1, least(p_limit, 5000))),
  pr as (select id, u, public.phg_menu_text_profile(txt) f from docs),
  c as (
    select id, f, (f->>'items')::int total, (f->>'drinks')::int bev, (f->>'food')::int food, (f->>'hh')::int hh,
           (f->>'spec')::int spec, (f->>'na')::int na,
           u ~ '(doordash|ubereats|grubhub|postmates|seamless|cdn4dd|slicelife|chownow|menufy)' deliv,
           u ~ '(happy[-_ ]?hour)' url_hh
    from pr)
  insert into public.phg_menu_doc_class (document_id, menu_kind, tags, bev_items, food_items, hh_items, spec_items, total_items, lists, reason, rules_version, classified_at)
  select id,
    case when deliv then 'delivery'
         when total = 0 then 'unread'
         when hh >= 0.6*total or (url_hh and hh > 0) then 'happy_hour'
         when spec >= 0.6*total then 'specials'
         when total < 5 then 'little_text'
         when bev + na >= 3 and food >= 3 and food > (bev + na) / 3 then 'mixed'
         when bev + na > 0 and bev + na >= food then 'beverage'
         when food > 0 then 'food'
         else 'unread' end,
    array(select case k when 'unsorted' then null else k end from jsonb_object_keys(f->'lists') k where k <> 'unsorted'
          union select 'happy_hour' where url_hh union select 'delivery' where deliv),
    bev + na, food, hh, spec, total, f->'lists',
    format('page text: %s items (drinks %s, non-alcoholic %s, food %s, happy hour %s, specials %s)', total, bev, na, food, hh, spec),
    'v2-lists', now()
  from c
  on conflict (document_id) do update set menu_kind=excluded.menu_kind, tags=excluded.tags, bev_items=excluded.bev_items,
    food_items=excluded.food_items, hh_items=excluded.hh_items, spec_items=excluded.spec_items, total_items=excluded.total_items,
    lists=excluded.lists, reason=excluded.reason, rules_version=excluded.rules_version, classified_at=now()
  where public.phg_menu_doc_class.rules_version is distinct from 'bot_check_v1';
  get diagnostics v_m = row_count;

  -- (2) documents without page text: item-based rules (v1.1) + list tags from section / item names
  with docs as (
    select d.id, d.original_menu_url, lower(coalesce(d.original_menu_url,'')||' '||coalesce(d.discovered_asset_url,'')) u
    from public.menu_visual_documents d
    where not exists (select 1 from public.phg_page_text t where t.document_id = d.id)
      and (p_reclassify or not exists (select 1 from public.phg_menu_doc_class k where k.document_id = d.id)
       or exists (select 1 from public.phg_menu_doc_class k where k.document_id = d.id and k.menu_kind in ('unread','little_text') and k.classified_at < now() - interval '6 hours' and k.rules_version <> 'bot_check_v1'))
    order by d.id desc limit greatest(1, least(p_limit, 25000))),
  agg as (
    select s.menu_page_url, count(*) a_total,
      count(*) filter (where s.item_type in ('cocktail','beer','wine','spirit_pour')) a_bev,
      count(*) filter (where s.item_type='cocktail') ck, count(*) filter (where s.item_type='beer') br,
      count(*) filter (where s.item_type='wine') wn, count(*) filter (where s.item_type='spirit_pour') sp,
      count(*) filter (where s.item_type='spirit_pour' and (public.phg_menu_section_list(s.section_name) = 'tequila_mezcal' or s.item_name ~* '(tequila|mezcal|reposado|a[nñ]ejo|blanco)')) teq,
      count(*) filter (where s.item_type='spirit_pour' and (public.phg_menu_section_list(s.section_name) = 'whiskey' or s.item_name ~* '(whisk(e)?y|bourbon|scotch|\mrye\M)')) whi,
      count(*) filter (where s.item_type='other' and (s.item_name||' '||coalesce(s.section_name,'')) ~* '(burger|taco|salad|pizza|wings?|fries|sandwich|chicken|steak|entree|appetizer|app[s ]|dessert|soup|pasta|burrito|nachos|quesadilla|shrimp|salmon|fish|pork|beef|rice|noodle|sushi|roll|breakfast|lunch|dinner|kids|side|bread|cake|cheese|egg)') a_food,
      count(*) filter (where coalesce(s.section_name,'') ~* 'happy\s*hour' or coalesce(s.notes,'') ~* 'happy\s*hour') a_hh,
      count(*) filter (where coalesce(s.section_name,'') ~* '(special|monday|tuesday|wednesday|thursday|friday|saturday|sunday|event|trivia|live music)') a_spec,
      count(*) filter (where coalesce(s.section_name,'') ~* 'brunch' or s.item_name ~* '(mimosa|bottomless)') brunch,
      count(*) filter (where s.item_name ~* '(sake|soju|junmai|ginjo|nigori)') sake,
      count(*) filter (where s.item_type='other' and s.item_name ~* '(soda|juice|coffee|latte|espresso|tea\M|lemonade|mocktail|water|smoothie)') na
    from public.staging_menu_extract s
    where s.superseded_at is null and s.item_type <> 'summary' and s.menu_page_url in (select original_menu_url from docs)
    group by s.menu_page_url),
  c as (
    select d.id, coalesce(a.a_total,0) total, coalesce(a.a_bev,0) bev, coalesce(a.a_food,0) food, coalesce(a.a_hh,0) hh, coalesce(a.a_spec,0) spec,
      coalesce(a.ck,0) ck, coalesce(a.br,0) br, coalesce(a.wn,0) wn, coalesce(a.sp,0) sp, coalesce(a.teq,0) teq, coalesce(a.whi,0) whi,
      coalesce(a.sake,0) sake, coalesce(a.na,0) na, coalesce(a.brunch,0) brunch,
      d.u ~ '(doordash|ubereats|grubhub|postmates|seamless|cdn4dd|slicelife|chownow|menufy)' deliv,
      d.u ~ '(happy[-_ ]?hour)' url_hh, d.u ~ '(special|event|calendar)' url_spec
    from docs d left join agg a on a.menu_page_url = d.original_menu_url)
  insert into public.phg_menu_doc_class (document_id, menu_kind, tags, bev_items, food_items, hh_items, spec_items, total_items, lists, reason, rules_version, classified_at)
  select id,
    case when deliv then 'delivery'
         when total = 0 then 'unread'
         when hh >= 0.6*total or (url_hh and hh > 0) then 'happy_hour'
         when spec >= 0.6*total then 'specials'
         when bev = 0 and food = 0 then 'not_menu'
         when total < 8 then 'little_text'
         when bev >= 3 and food >= 3 then 'mixed'
         when bev > 0 and bev >= food then 'beverage'
         when food > 0 and bev < 3 then 'food'
         else 'mixed' end,
    array_remove(array[
      case when ck>0 then 'cocktails' end, case when br>0 then 'beer' end, case when wn>0 then 'wine' end,
      case when sp>teq+whi then 'spirits' end, case when teq>0 then 'tequila_mezcal' end, case when whi>0 then 'whiskey' end,
      case when sake>0 then 'sake_soju' end, case when na>0 then 'non_alcoholic' end, case when food>0 then 'food' end,
      case when hh>0 or url_hh then 'happy_hour' end, case when spec>0 or url_spec then 'specials' end,
      case when brunch>0 then 'brunch' end, case when deliv then 'delivery' end], null),
    bev, food, hh, spec, total,
    jsonb_strip_nulls(jsonb_build_object('cocktails', nullif(ck,0), 'beer', nullif(br,0), 'wine', nullif(wn,0),
      'spirits', nullif(sp-teq-whi,0), 'tequila_mezcal', nullif(teq,0), 'whiskey', nullif(whi,0), 'food', nullif(food,0))),
    format('items %s: drinks %s, food %s, happy hour %s, specials %s', total, bev, food, hh, spec), 'v2-items', now()
  from c
  on conflict (document_id) do update set menu_kind=excluded.menu_kind, tags=excluded.tags, bev_items=excluded.bev_items, food_items=excluded.food_items,
    hh_items=excluded.hh_items, spec_items=excluded.spec_items, total_items=excluded.total_items, lists=excluded.lists, reason=excluded.reason,
    rules_version=excluded.rules_version, classified_at=now()
  where public.phg_menu_doc_class.rules_version is distinct from 'bot_check_v1';
  get diagnostics v_n = row_count;
  return v_n + v_m;
end $function$;
