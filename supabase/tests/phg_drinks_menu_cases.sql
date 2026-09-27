-- PHG-035 filter R&D: what the classifier must decide for each kind of page. Run after any rule change:
--   select * from phg_drinks_menu_cases_run();   -- every row must say pass = true
-- Cases mirror what Rob has flagged (2026-09-27): full drinks menus, tabbed lists, unpriced lists, generic
-- "Spirits" lists sorted by brand, and pages that are NOT drinks menus (food, homepage, bot check, delivery,
-- happy-hour page, specials page, cocktail photo gallery).
create table if not exists public.phg_drinks_menu_cases (
  name text primary key,
  page_text text not null,
  expect_kind text not null,          -- beverage | mixed | food | happy_hour | specials | little_text | unread
  expect_lists text[] not null default '{}',   -- lists that must be found (others may also appear)
  forbid_lists text[] not null default '{}',   -- lists that must NOT be found
  note text
);
alter table public.phg_drinks_menu_cases enable row level security;
revoke all on public.phg_drinks_menu_cases from anon, authenticated;

create or replace function public.phg_drinks_menu_kind(f jsonb, p_url text default '') returns text
language sql immutable parallel safe set search_path to '' as $$
  -- same decision as phg_menu_doc_classify path (1)
  select case
    when p_url ~ '(doordash|ubereats|grubhub|postmates|seamless|slicelife|chownow|menufy)' then 'delivery'
    when t = 0 then 'unread'
    when hh >= 0.6*t or (p_url ~ 'happy[-_ ]?hour' and hh > 0) then 'happy_hour'
    when sp >= 0.6*t then 'specials'
    when t < 5 then 'little_text'
    when b + na >= 3 and fd >= 3 and fd > (b + na) / 3 then 'mixed'
    when b + na > 0 and b + na >= fd then 'beverage'
    when fd > 0 then 'food'
    else 'unread' end
  from (select (f->>'items')::int t, (f->>'drinks')::int b, (f->>'na')::int na, (f->>'food')::int fd,
               (f->>'hh')::int hh, (f->>'spec')::int sp) x
$$;

create or replace function public.phg_drinks_menu_cases_run()
returns table (name text, pass boolean, got_kind text, expect_kind text, got_lists jsonb, missing text[], forbidden_found text[])
language sql stable set search_path to 'public', 'pg_temp' as $$
  with r as (select c.*, public.phg_menu_text_profile(c.page_text) f from public.phg_drinks_menu_cases c)
  select r.name,
         public.phg_drinks_menu_kind(r.f) = r.expect_kind
           and not exists (select 1 from unnest(r.expect_lists) e where not (r.f->'lists') ? e)
           and not exists (select 1 from unnest(r.forbid_lists) e where (r.f->'lists') ? e),
         public.phg_drinks_menu_kind(r.f), r.expect_kind, r.f->'lists',
         array(select e from unnest(r.expect_lists) e where not (r.f->'lists') ? e),
         array(select e from unnest(r.forbid_lists) e where (r.f->'lists') ? e)
  from r order by 2, 1
$$;

insert into public.phg_drinks_menu_cases (name, page_text, expect_kind, expect_lists, forbid_lists, note) values
('watershed_tabs', E'OUR DRINKS\nBEER\nWINE\nCOCKTAILS\nSPIRITS\nDRAFT & CANS\nTradewinds House Boat\n$9.31\nFive Borroughs Summer Ale\n$9.31\nMiller High Life\n$7.24\nRED\nEast End Estate\n$15.52\nCoast & Barrell\n$18.63\nWHITE\nNorth Fork Selection\n$14.49\nWATERSHED CLASSICS\nSunset Breeze\n$16.00\nBarrel Aged Old Fashion\n$17.00\nLittle Kisses\n$19.00\nAFTER DINNER FAVORITES\nThe Balvenie\n$18.00\nOban\n$18.00\nMacallan\n$20.00',
  'beverage', '{beer,wine,cocktails,whiskey}', '{food}', 'tabbed menu, every tab captured'),
('mymoon_unpriced', E'Bar Menu\nRosé\n2023 STOLPMAN LOVE YOU BUNCHES\ngrenache, syrah\nWhite\n2022 KURTATSCH\npinot grigio, alto adige\nEL NEPTUNE\nalbarino\nCervezas Draught\nKCBC VENOMOUS VILLAINS\nbrooklyn, west coast ipa\nSIXPOINTS SUMMER SESH\nbrooklyn lager\nSignature Cocktails\nSTRAWBERRY MYMOON\nvodka, strawberry cordial\nPENDENNIS CLUB\ngin, apricot liqueur\nLAVENDER SOUR\ngin, lavender syrup',
  'beverage', '{wine,beer,cocktails}', '{vodka,gin,liqueur_amaro}', 'no prices; ingredients inside cocktails are not spirit lists'),
('spirits_by_brand', E'SPIRITS\nTito''s $10\nGrey Goose $12\nHendrick''s $12\nTanqueray $10\nBacardi $9\nDiplomatico Reserva $11\nCasamigos Blanco $14\nDon Julio 1942 $28\nDel Maguey Vida $13\nMacallan 12 $18\nBuffalo Trace $11\nHennessy VS $14\nAperol $9\nFernet Branca $9',
  'beverage', '{vodka,gin,rum,tequila,mezcal,whiskey,brandy_cognac,liqueur_amaro}', '{}', 'generic spirits list sorted by brand, every spirit equal'),
('every_list_heading', E'VODKA\nHouse $9\nGIN\nHouse $9\nRUM\nHouse $9\nTEQUILA\nHouse $10\nMEZCAL\nHouse $12\nWHISKEY\nHouse $11\nCOGNAC\nHouse $14\nAMARO\nHouse $10\nSAKE\nHouse $10\nCIDERS\nHouse $7\nMOCKTAILS\nHouse $8',
  'beverage', '{vodka,gin,rum,tequila,mezcal,whiskey,brandy_cognac,liqueur_amaro,sake_soju,cider_seltzer,non_alcoholic}', '{}', 'each category heading maps to its own list'),
('bar_with_food', E'COCKTAILS\nMargarita $14\nPaloma $14\nMojito $13\nDRAFT BEER\nIPA $8\nLager $7\nAPPETIZERS\nWings $14\nNachos $12\nENTREES\nBurger $18\nSalmon $26\nSteak Frites $32',
  'mixed', '{cocktails,beer,food}', '{}', 'drinks and food on one page'),
('food_menu', E'APPETIZERS\nWings $14\nNachos $12\nCalamari $15\nENTREES\nBurger $18\nSalmon $26\nSteak Frites $32\nChicken Parm $24\nDESSERTS\nCheesecake $9\nBEVERAGES\nSoda $3',
  'food', '{food}', '{cocktails,beer,wine}', 'Rob: food menus are not drinks menus'),
('homepage_nav', E'HOME\nABOUT\nMENU\nRESERVATIONS\nGIFT CARDS\nCONTACT\nWelcome to our restaurant. Join us for dinner tonight.\nFollow us on Instagram',
  'unread', '{}', '{}', 'a homepage links to a menu but is not one'),
('bot_check', E'adriftbar.com\nChecking the site connection security\nThis page requires cookies to be enabled',
  'unread', '{}', '{}', 'bot-check screens are never menus (capture refuses them too)'),
('happy_hour_page', E'HAPPY HOUR\nMon-Fri 3-6pm\nWell Drinks $6\nHouse Wine $7\nDraft Beer $5\nMargarita $8\nSliders $9',
  'happy_hour', '{}', '{}', 'Rob: happy-hour pages are their own type'),
('drinks_with_hh_section', E'COCKTAILS\nMargarita $14\nPaloma $14\nOld Fashioned $15\nNegroni $15\nWINE\nPinot Noir $13\nChardonnay $12\nSauvignon Blanc $12\nBEER\nIPA $8\nLager $7\nHAPPY HOUR\nWell Drinks $6',
  'beverage', '{cocktails,wine,beer,happy_hour}', '{}', 'Rob: a drinks menu with a happy-hour section stays a drinks menu, tagged happy hour'),
('specials_page', E'WEEKLY SPECIALS\nTaco Tuesday $3 tacos\nWing Wednesday $0.75 wings\nTrivia Thursday\nFriday Fish Fry $16',
  'specials', '{}', '{}', 'Rob: specials pages are their own type'),
('cocktail_photo_gallery', E'Our cocktails\nPhoto\nPhoto\nPhoto\nFollow us @ourbar',
  'unread', '{}', '{}', 'Rob: photos of a cocktail are not a menu')
on conflict (name) do update set page_text = excluded.page_text, expect_kind = excluded.expect_kind,
  expect_lists = excluded.expect_lists, forbid_lists = excluded.forbid_lists, note = excluded.note;
