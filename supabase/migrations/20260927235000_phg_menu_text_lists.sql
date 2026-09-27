-- PHG-035: what makes a drinks menu a drinks menu, from the page's own text.
-- phg_page_text: full visible text saved by capture v2 (main page + embedded frames + every clicked tab).
-- phg_menu_section_list(heading): which list a heading starts (beer / wine / tequila_mezcal / whiskey / spirits /
--   cocktails / non_alcoholic / sake_soju / food / happy_hour / specials), null if not a list heading.
-- phg_menu_text_profile(text): walks the lines, tracks the current list, counts priced (or listed) items per list.

create table if not exists public.phg_page_text (
  page_id bigint primary key,
  document_id bigint not null,
  text text not null,
  chars int generated always as (length(text)) stored,
  source text not null default 'capture_v2',
  captured_at timestamptz not null default now()
);
create index if not exists phg_page_text_doc_idx on public.phg_page_text (document_id);
alter table public.phg_page_text enable row level security;
revoke all on public.phg_page_text from anon, authenticated;

create or replace function public.phg_menu_section_list(p_heading text) returns text
language sql immutable parallel safe set search_path to '' as $$
  select case
    when h ~ '(happy\s*hour|\mhh\M)' then 'happy_hour'
    when h ~ '(special|monday|tuesday|wednesday|thursday|friday|saturday|sunday|event|trivia|live music|brunch)' and h !~ '(cocktail|wine|beer)' then 'specials'
    when h ~ '(mocktail|zero[- ]?proof|spirit[- ]?free|non[- ]?alc|alcohol[- ]?free|\mn/?a\M|soft drinks|refreshing|coffee|\mtea\M|juices?|sodas?)' then 'non_alcoholic'
    when h ~ '(tequila|mezcal|agave|reposado|a[nñ]ejo|blanco|raicilla|sotol)' then 'tequila_mezcal'
    when h ~ '(whisk(e)?y|bourbon|scotch|\mrye\M|single malt|japanese whisky|irish)' then 'whiskey'
    when h ~ '(cocktail|signature|classics?\M|martini|margarita|spritz|\mmules?\M|sangria|frozen|house drinks|libations|mixed drinks|tiki|highball|negroni|old fashioned)' then 'cocktails'
    when h ~ '(\mbeers?\M|draft|draught|on tap|\mtaps?\M|cans|bottles? (&|and) cans|ciders?|seltzers?|\mipa\M|lager|stout|brews?)' then 'beer'
    when h ~ '(\mwines?\M|\mreds?\M|\mwhites?\M|ros[eé]|sparkling|bubbles|champagne|prosecco|by the glass|by the bottle|vino|orange wine|dessert wine|port\M)' then 'wine'
    when h ~ '(sake|soju|shochu|junmai)' then 'sake_soju'
    when h ~ '(vodka|\mgin\M|\mrum\M|cognac|brandy|armagnac|amaro|amari|liqueurs?|cordials?|spirits|after dinner|digestif|aperitif|pours|shots?)' then 'spirits'
    when h ~ '(appetizer|starter|small plates|shareables|entr[eé]e|\mmains?\M|burgers?|sandwich|salads?|soups?|pizza|pasta|desserts?|\msides?\M|tacos|breakfast|lunch|dinner|kids|raw bar|sushi|rolls|bowls|platters|wings|flatbread|seafood|steaks?)' then 'food'
    else null end
  from (select lower(coalesce(p_heading,'')) h) x
$$;

create or replace function public.phg_menu_text_profile(p_text text) returns jsonb
language plpgsql immutable parallel safe set search_path to 'public', 'pg_temp' as $$
-- per list: p = priced lines, l = other short lines (item names / descriptions on menus without prices).
-- items per list = greatest(p, l / 2)  (a name line + a description line per item on unpriced menus)
declare
  ln text; cur text := null; lst text; p jsonb := '{}'; l jsonb := '{}'; out jsonb := '{}'; priced bool; k text; v int;
  drinks int := 0; total int := 0;
begin
  for ln in select btrim(x) from regexp_split_to_table(coalesce(p_text,''), E'\n') x loop
    continue when ln = '' or length(ln) > 220;
    priced := ln ~ '(\$\s?\d{1,3}([.,]\d{2})?|\m\d{1,3}[.,]\d{2}\M|^\d{1,3}(\s*/\s*\d{1,3})?$)';
    if not priced and length(ln) <= 45 then
      lst := public.phg_menu_section_list(ln);
      if lst is not null then cur := lst; continue; end if;
    end if;
    k := coalesce(cur, case when priced then coalesce(nullif(public.phg_menu_section_list(ln), ''), 'unsorted') end);
    continue when k is null;
    if priced then p := jsonb_set(p, array[k], to_jsonb(coalesce((p->>k)::int, 0) + 1));
    elsif length(ln) <= 120 and cur is not null then l := jsonb_set(l, array[k], to_jsonb(coalesce((l->>k)::int, 0) + 1));
    end if;
  end loop;
  for k in select jsonb_object_keys(p || l) loop
    v := greatest(coalesce((p->>k)::int, 0), coalesce((l->>k)::int, 0) / 2);
    continue when v = 0;
    out := out || jsonb_build_object(k, v);
    total := total + v;
    if k in ('beer','wine','tequila_mezcal','whiskey','spirits','cocktails','sake_soju') then drinks := drinks + v; end if;
  end loop;
  return jsonb_build_object('lists', out, 'items', total, 'drinks', drinks,
    'na', coalesce((out->>'non_alcoholic')::int,0), 'food', coalesce((out->>'food')::int,0),
    'hh', coalesce((out->>'happy_hour')::int,0), 'spec', coalesce((out->>'specials')::int,0));
end $$;
