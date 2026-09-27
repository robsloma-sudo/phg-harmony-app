-- PHG-035c: drinks categories v3, from a review of real library data (2026-09-28).
-- Found in staging_menu_extract spirit lines: food and page text mislabeled as spirits ("Reuben on Marble Rye" -> rye,
-- "Vodka Pizza Slice", "penne alla vodka", hotel check-in text); mixed headings ("Tequila & Mezcal") deciding for the
-- item (Don Julio -> mezcal); beer brands in spirit lists; frequent brands unknown (Milagro, Whistle Pig, Fireball ...).
-- Fixes: (1) phg_drink_line_is_junk guard; (2) the item's own words decide first, the heading only when the item says
-- nothing; (3) beer brands -> beer; (4) brand list grown from the most frequent unsorted names in the library.

create or replace function public.phg_drink_line_is_junk(p_line text) returns boolean
language sql immutable parallel safe set search_path to '' as $$
  select lower(coalesce(p_line,'')) ~ ('(sandwich|reuben|rachel\M|marble rye|rye bread|\mon rye\M|pizza|\mslice\M|pasta|penne|rigatoni|alla vodka|vodka sauce|'
    || 'burrito|\mbowl\M|quesadilla|quesabirria|\mtacos?\M|garlic bread|provolone|coleslaw|cheese|\mfries\M|\mwings?\M|burger|salad|'
    || 'check-?in|check-?out|policy|credit card|debit card|semester|\mclasses\M|regular price|average rating|\mreviews?\M|'
    || 'reservation|gift card|\mhours\M|parking|wi-?fi)')
$$;

create or replace function public.phg_drink_item_category(p_line text) returns text
language sql immutable parallel safe set search_path to '' as $$
  select case
    when public.phg_drink_line_is_junk(l) then null
    when l ~ '(zacapa|\mron (abuelo|barcel[oó]|zacapa|matusalem))' then 'rum'  -- "Zacapa Centenario" is rum, not the tequila brand
    when l ~ '(mezcal|mescal|del maguey|ilegal|\mvago\M|montelobos|bruxo|madre mezcal|union mezcal|400 conejos|creyente|sotol|raicilla|marca negra|cenizo|banh[eé]z|la luna mezcal|alipus|real minero|rey campero|pierde almas)' then 'mezcal'
    when l ~ '(tequila|reposado|a[nñ]ejo|\mblanco\M|\mplata\M|cristalino|casamigos|don julio|patr[oó]n|herradura|espol[oó]n|clase azul|el tesoro|fortaleza|siete leguas|cazadores|hornitos|\m1800\M|jose cuervo|cuervo|avi[oó]n|teremana|casa noble|tapat[ií]o|\mg4\M|\mocho\M|cimarron|olmeca|\mlalo\M|codigo|\m818\M|volcan|milagro|tres generaciones|corralejo|dobel|casa dragones|cabo wabo|centenario|el mayor|coraz[oó]n|don fulano|partida|jimador|casa del sol|corzo|cinco sentidos|riazul|tres agaves|lunazul|21 seeds|mijenta|suerte|arette|pueblo viejo|san matias|dos artes|cantera negra|gran coramino|komos|la gritona|\mtequilas?\M)' then 'tequila'
    when l ~ '(whisk(e)?y|bourbon|scotch|\mrye\M|single malt|macallan|glenlivet|glenfiddich|glenmorangie|glenfarclas|glendronach|glengoyne|lagavulin|laphroaig|\moban\M|balvenie|talisker|ardbeg|dalmore|dalwhinnie|bowmore|highland park|aberlour|mortlach|springbank|bruichladdich|auchentoshan|johnn(ie|y) walker|black label|chivas|dewar|monkey shoulder|buchanan|buffalo trace|maker.?s mark|woodford|knob creek|bulleit|jim beam|wild turkey|four roses|eagle rare|blanton|weller|pappy|rip van winkle|basil hayden|angel.?s envy|elijah craig|old forester|michter|high west|whistle ?pig|sazerac rye|rittenhouse|old overholt|redemption|widow jane|tin cup|breckenridge bourbon|stranahan|laws whiskey|brother.?s bond|blood oath|penelope|\m1792\M|jameson|red ?breast|green spot|yellow spot|tullamore|bushmills|\mpowers\M|knappogue|glendalough|slane|teeling|crown royal|crown apple|canadian club|black velvet|seagram.?s 7|pendleton|suntory|hibiki|yamazaki|hakushu|nikka|\mtoki\M|jack daniel|jack fire|gentleman jack|uncle nearest|evan williams|larceny|heaven hill|old grand.?dad|fireball|skrewball|screwball)' then 'whiskey'
    when l ~ '(cognac|brandy|armagnac|calvados|pisco|grappa|hennessy|r[eé]my martin|courvoisier|martell|d.?uss[eé]|\mhine\M|st.? r[eé]my|\me ?& ?j\M|\mb ?& ?b\M|korbel brandy|paul masson|christian brothers)' then 'brandy_cognac'
    when l ~ '(\mrum\M|rhum|cacha[cç]a|bacardi|captain morgan|diplom[aá]tico|zacapa|appleton|mount gay|plantation|kraken|sailor jerry|flor de ca[nñ]a|havana club|goslings|el dorado|smith (&|and) cross|brugal|malibu|myers|don q\M|clairin|admiral nelson|blue chair bay|cruzan|parrot bay|pusser|ron abuelo|santa teresa|papa.?s pilar|opthimus|bumbu|rumhaven)' then 'rum'
    when l ~ '(\mgin\M|genever|hendrick|tanqueray|bombay|beefeater|aviation|botanist|monkey 47|\mroku\M|sipsmith|plymouth|empress 1908|nolet|citadelle|gray whale|st.? george terroir|malfy|bluecoat|fords gin|brockmans|procera|uncle val|seagram.?s gin|gordon.?s|new amsterdam gin|drumshanbo|conniption|barr hill)' then 'gin'
    when l ~ '(vodka|tito.?s|grey goose|ketel one|belvedere|\mabsolut\M|stoli|smirnoff|c[iî]roc|chopin|reyka|deep eddy|new amsterdam|svedka|skyy|pinnacle|\mhaku\M|crystal head|kettle one|sobieski|luksusowa|wheatley|three olives|\m360 vodka|burnett.?s|mile high|western son|dripping springs|hangar 1|effen|platinum 7x|ketel)' then 'vodka'
    when l ~ '(amaro|amari|liqueur|cordial|schnapps|irish cream|triple sec|cr[eè]me de|aperol|campari|fernet|chartreuse|b[eé]n[eé]dictine|cointreau|grand marnier|gran marnier|kahl[uú]a|bailey.?s|rumchata|disaronno|amaretto|frangelico|j[aä]germeister|montenegro|averna|cynar|nonino|braulio|limoncello|sambuca|absinthe|st.? germain|chambord|drambuie|licor 43|midori|pimm|lillet|vermouth|sherry|\mport\M|taylor fladgate|madeira|aperitivo|digestivo|southern comfort|tuaca|goldschl[aä]ger|rumple ?minze|pama\M|hpnotiq|galliano|strega|luxardo|mr.? black|borghetti|carolans)' then 'liqueur_amaro'
    when l ~ '(sake|soju|shochu|junmai|ginjo|daiginjo|nigori|jinro|chamisul|makgeolli|dassai)' then 'sake_soju'
    when l ~ '(coors|budweiser|bud light|\mcorona\M|michelob|miller lite|miller high life|modelo|stella artois|heineken|guinness|blue moon|fat tire|\mpbr\M|pabst|yuengling|dos equis|pacifico|sam(uel)? adams|lagunitas|sierra nevada|voodoo ranger|kona|high noon|white claw|truly\M|twisted tea|angry orchard)' then case when l ~ '(high noon|white claw|truly\M|twisted tea|angry orchard)' then 'cider_seltzer' else 'beer' end
    else null end
  from (select lower(coalesce(p_line,'')) l) x
$$;

-- Applied in place after this file (same day, from a second pass over real data):
--  * phg_drink_line_is_junk also rejects sauce / shrimp / garlic / mozzarella / basil / chicken / steak / salmon /
--    jumbo / entree / appetizer / tuition ("Creamy cognac sauce w/ jumbo shrimp").
--  * phg_drink_item_category first recognises classic cocktails named inside spirits lists (Gin & Tonic, Vodka Mule,
--    Brandy Alexander, Martini, Margarita, Sour, Spritz, Collins, Old Fashioned, Manhattan, Negroni, Mojito, Daiquiri,
--    Bloody Mary, Paloma, Mimosa, Irish Coffee, Long Island ... not "Margaritaville" tequila) -> 'cocktails';
--    tequila + 'tequilia' (misspelled headings), 'margaritaville'; whiskey + 'cask', prichard, greenspot, dunville,
--    singleton, baby jane.
--  * phg_menu_text_profile: under any spirits-type, beer or cider heading (or none) the item's own words decide;
--    junk lines under those headings are skipped.
--  * phg_menu_doc_classify staging path: category = item name first, then section name, then 'spirits'; junk
--    spirit lines excluded.
-- Result on the library's 18,000 spirit lines: whiskey 6,310 · tequila 3,511 · vodka 1,349 · liqueurs 860 · gin 764 ·
-- rum 761 · mezcal 650 · brandy/cognac 457 · sake/soju 414 · cocktails 145 · beer 114 · seltzer 38 ·
-- type not stated 1,577 (8.7%) · food/page text excluded 1,045. Test suite 17/17.
