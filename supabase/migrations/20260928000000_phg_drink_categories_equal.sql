-- Also applied in place the same day: phg_menu_text_profile sorts each item under a generic spirits heading (or no
-- heading) with phg_drink_item_category; unpriced lines count only when a page lists 8+; classifier staging path counts
-- every drinks category (patched in place). Reclassified 22,666 documents. Test suite: supabase/tests/phg_drinks_menu_cases.sql.
-- PHG-035b: every drinks category is its own equal list (Rob, 2026-09-27: "Every spirit needs to be treated equally.
-- Every single category treated equally."). No catch-all "other spirits" when the type can be told.
-- Categories: cocktails, beer, cider_seltzer, wine, vodka, gin, rum, tequila, mezcal, whiskey, brandy_cognac,
--   liqueur_amaro, sake_soju, non_alcoholic  (+ food, happy_hour, specials for the page kind).
--   'spirits' remains only for spirit lines whose type the text does not state.
-- phg_drink_item_category(line): category of ONE item line from its words and common brand names.
-- phg_menu_section_list(heading): category a list heading starts (generic "Spirits / Liquor / After dinner" = 'spirits',
--   whose items are then sorted one by one with phg_drink_item_category).

create or replace function public.phg_drink_item_category(p_line text) returns text
language sql immutable parallel safe set search_path to '' as $$
  select case
    when l ~ '(mezcal|mescal|del maguey|ilegal|\mvago\M|montelobos|bruxo|madre mezcal|union mezcal|400 conejos|creyente|sotol|raicilla)' then 'mezcal'
    when l ~ '(tequila|reposado|a[nñ]ejo|\mblanco\M|cristalino|casamigos|don julio|patr[oó]n|herradura|espol[oó]n|clase azul|el tesoro|fortaleza|siete leguas|cazadores|hornitos|\m1800\M|jose cuervo|cuervo|avi[oó]n|teremana|casa noble|tapat[ií]o|\mg4\M|\mocho\M|cimarron|olmeca|\mlalo\M|codigo 1530|\m818\M|volcan)' then 'tequila'
    when l ~ '(whisk(e)?y|bourbon|scotch|\mrye\M|single malt|macallan|glenlivet|glenfiddich|glenmorangie|lagavulin|laphroaig|\moban\M|balvenie|talisker|ardbeg|dalmore|johnnie walker|chivas|dewar|monkey shoulder|buffalo trace|maker.?s mark|woodford|knob creek|bulleit|jim beam|wild turkey|four roses|eagle rare|blanton|weller|pappy|basil hayden|angel.?s envy|elijah craig|old forester|michter|high west|whistlepig|sazerac rye|rittenhouse|jameson|redbreast|tullamore|bushmills|\mpowers\M|crown royal|suntory|hibiki|yamazaki|hakushu|nikka|\mtoki\M|jack daniel|gentleman jack|uncle nearest|evan williams|larceny|heaven hill|old grand.?dad)' then 'whiskey'
    when l ~ '(cognac|brandy|armagnac|calvados|pisco|grappa|hennessy|r[eé]my martin|courvoisier|martell|d.?uss[eé]|\mhine\M|st.? r[eé]my|e&j\M)' then 'brandy_cognac'
    when l ~ '(\mrum\M|rhum|cacha[cç]a|bacardi|captain morgan|diplom[aá]tico|zacapa|appleton|mount gay|plantation|kraken|sailor jerry|flor de ca[nñ]a|havana club|goslings|el dorado|smith (&|and) cross|brugal|malibu|myers|don q\M|clairin)' then 'rum'
    when l ~ '(\mgin\M|genever|hendrick|tanqueray|bombay|beefeater|aviation|the botanist|monkey 47|\mroku\M|sipsmith|plymouth|empress 1908|nolet|citadelle|gray whale|st.? george terroir|malfy|bluecoat|fords gin|brockmans)' then 'gin'
    when l ~ '(vodka|tito.?s|grey goose|ketel one|belvedere|\mabsolut\M|stoli|smirnoff|cîroc|ciroc|chopin|reyka|deep eddy|new amsterdam|svedka|skyy|pinnacle|\mhaku\M|crystal head|kettle one|sobieski|luksusowa|wheatley)' then 'vodka'
    when l ~ '(amaro|amari|liqueur|cordial|aperol|campari|fernet|chartreuse|b[eé]n[eé]dictine|cointreau|grand marnier|kahl[uú]a|baileys|disaronno|amaretto|frangelico|jägermeister|jagermeister|montenegro|averna|cynar|nonino|limoncello|sambuca|absinthe|st.? germain|chambord|drambuie|licor 43|midori|pimm|lillet|vermouth|sherry|\mport\M|madeira|aperitivo|digestivo)' then 'liqueur_amaro'
    when l ~ '(sake|soju|shochu|junmai|ginjo|daiginjo|nigori|jinro|chamisul|makgeolli)' then 'sake_soju'
    else null end
  from (select lower(coalesce(p_line,'')) l) x
$$;

create or replace function public.phg_menu_section_list(p_heading text) returns text
language sql immutable parallel safe set search_path to '' as $$
  select case
    when h ~ '(happy\s*hour|\mhh\M)' then 'happy_hour'
    when h ~ '(special|monday|tuesday|wednesday|thursday|friday|saturday|sunday|event|trivia|live music|brunch)' and h !~ '(cocktail|wine|beer)' then 'specials'
    when h ~ '(mocktail|zero[- ]?proof|spirit[- ]?free|non[- ]?alc|alcohol[- ]?free|\mn/?a\M|soft drinks|refreshing|coffee|\mtea\M|juices?|sodas?|lemonades?)' then 'non_alcoholic'
    when h ~ '(cocktail|signature|classics?\M|martinis?\M|margaritas?\M|spritz|\mmules?\M|sangria|frozen|house drinks|libations|mixed drinks|tiki|highball|negroni|old fashioned|punch)' then 'cocktails'
    when h ~ '(ciders?|seltzers?|hard tea|hard lemonade|kombucha)' then 'cider_seltzer'
    when h ~ '(\mbeers?\M|draft|draught|on tap|\mtaps?\M|cans|bottles? (&|and) cans|\mipa\M|lagers?|stouts?|\males?\M|brews?|cervezas?)' then 'beer'
    when h ~ '(\mwines?\M|\mreds?\M|\mwhites?\M|ros[eé]|sparkling|bubbles|champagne|prosecco|by the glass|by the bottle|vino|orange wine|dessert wine)' then 'wine'
    when public.phg_drink_item_category(h) is not null then public.phg_drink_item_category(h)
    when h ~ '(spirits|liquors?|after dinner|pours|shots?|\mneat\M|top shelf|\mwell\M|\mcall\M|premium|back bar|bottle service|digestif|aperitif)' then 'spirits'
    when h ~ '(appetizer|starter|small plates|shareables|entr[eé]e|\mmains?\M|burgers?|sandwich|salads?|soups?|pizza|pasta|desserts?|\msides?\M|tacos|breakfast|lunch|dinner|kids|raw bar|sushi|rolls|bowls|platters|wings|flatbread|seafood|steaks?)' then 'food'
    else null end
  from (select lower(coalesce(p_heading,'')) h) x
$$;
