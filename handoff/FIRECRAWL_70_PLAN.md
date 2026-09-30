# Firecrawl 70% plan: website discovery (cron 9) and paid blocked-menu recovery (cron 33)

Prepared 2026-09-30. Read-only investigation: SELECT queries only, no Firecrawl or other paid calls, no writes, no cron changes.
Rule under test (Rob): a paid Firecrawl job may run only when a test sample shows >= 70% success.

## 0. Bottom line

| Job | Success definition used | Current test result | Best with proposed changes, on data we already have | Can 70% be shown now? |
|---|---|---|---|---|
| A: website discovery | Accepted website is the venue's own site (precision) | **30%** (12/40 'matched' correct) | **~96%** precision (48/50 sample) | **Yes, for precision.** |
| A: website discovery | Processed accounts that end with a correct own site (yield) | ~13% (about 645 / 5,050) | **~25-29%** (about 1,250-1,450 / 5,050) | **No.** Stored candidates cap this near 29-33%. |
| B: paid blocked menus | At least 3 alcoholic drink items (name, with a price or clearly listed) pulled from the right venue's beverage or mixed page | **1/40 = 2.5%** (the 3 'extracted' rows include 2 false successes) | 1/3 to 3/3 on the 3 sample pages that pass the pre-filter | **No.** Only 3 sample pages pass, which is too few to prove anything. 36 of 39 paid scrapes were pages that should never have been bought. |

Recommendation: keep both jobs paused. Job A can be turned back on after the re-scoring in section A4, **if Rob accepts precision as the success measure** and tracks yield as a separate number. Job B needs the pre-filter in section B4, then a free probe, then a paid test of 10 pages. Run Job B only if that test gets 7 or more out of 10.

---

## Job A: website discovery (cron 9, `discover-restaurant-websites`)

### A1. How the scoring code works (`supabase/functions/discover-restaurant-websites/index.ts`)
- Query: `name + street + city + state + "official website"`, with `limit: 3` web results.
- `score = 0.60 * (name tokens found in url+title+desc) + 0.18 (city in text) + 0.08 (street number) + 0.14 (a name token is in the domain)`.
- A candidate is `matched` when `best >= 0.78` and `best - second >= 0.10`.
- BLOCKED lists only 10 domains (facebook, instagram, yelp, tripadvisor.com, google.com, mapquest, foursquare, doordash, ubereats, grubhub).

Structural flaws:
1. **A directory page scores 0.86 without matching the domain.** It gets 0.60 for the name, 0.18 for the city and 0.08 for the street number. A chamber, tourism or yellowpages listing contains all three, so it passes 0.78. The domain signal counts for only 0.14, so it cannot veto a directory page.
2. **Two results from the same domain destroy the margin.** Example: `sadiesward.com/` and `sadiesward.com/about` both score 1.00, the margin is 0, and the row goes to `review`. The same happens for Mary's, Jajaja, McManus, Bellagio, Evil Twin, Snarf's, Sweet Science and Three Pillars.
3. **Generic name and city tokens count as name evidence.** "Grinnell" in `grinnellchamber.org` and "legion" in `ialegion.org` are examples.
4. **The blocklist uses exact domains**, so it misses `tripadvisor.ie`, `waze.com`, `maps.apple.com`, `*.wheree.com` and hundreds of local directories.
5. Only 3 results are kept, and the query phrase "official website" pulls in directories.

### A2. Live status (numbers in the brief were stale)
```sql
with a as (select * from accounts where account_status='active' and 'on_premise_spirits'=any(account_types)
  and (account_id like 'ACC-IA-%' or account_id like 'ACC-CO-%' or account_id like 'ACC-NY-%'))
select website_discovery_status, count(*), count(*) filter (where website_url is not null) has_url
from a group by 1;
```
matched **2,151**, review **2,020**, no_match **879**, retry 11. That is 5,061 processed, with **3,962** eligible and not yet processed. Candidates are stored in `website_discovery_candidates`: 7,420 rows for 4,187 accounts, about 2.2 per account. `no_match` rows have no stored candidates.

### A3. Sample judgement (I judged each row from domain, title and city)
Sampling SQL (the review sample uses seed `s2` and a limit of 60):
```sql
with a as (select account_id, account_name, substring(notes from 'City:\s*([^.]+)') city, website_url, website_discovery_score sc
  from accounts where account_status='active' and 'on_premise_spirits'=any(account_types)
  and website_discovery_status='matched' order by md5(account_id||'s1') limit 40)
select a.account_name, a.city, a.sc, a.website_url,
 (select string_agg(round(w.score,2)||' '||left(w.candidate_url,70)||' | '||left(w.candidate_title,50),' || ' order by w.score desc)
  from website_discovery_candidates w where w.account_id=a.account_id) c from a;
```

**'matched' sample (n=40): 12 correct = 30% precision.**
- Correct: manhattanvalleyny.com, caribeschenectady.com, murphsirondequoitpub.com, cromptonalehouse.com, socialcapitolevents.com, winneshiekcountyfair.org, pubmulligans.com, bistro93akronny.wixsite.com, brooklynoperahouse.com (right domain but the /donate page), destinationgrille.com, primepubgroup.com/somers, highsidebrewing.com/colorado-bbq (CO BBQ).
- Wrong (28): members.okobojichamber.com, mindtrip.ai, colorado.com, yellowpages.com (x2), howard-county.com (and this listing is for a *different* bar), westcottsyr.com, tourchautauqua.com, us.trip.com, traveliowa.com (x3), enchantedmountains.com, livemillscounty.com, bellevueia.gov chamber list, tripadvisor.ie, sla.ny.gov PDF agenda, opentable.com, onhavanastreet.com, mississippivalleypublishing.com news, q-billiards.wheree.com, waze.com, commercial.century21.com, maps.apple.com, cityofdelta.net PDF notice, visitbuffalo.com, enprimeurclub.com, news10.com. In the news10.com case the correct pdtcatering.com was the #2 candidate.

**'review' sample (n=60): 23 (38%) have the correct own site among the stored candidates.** Of those 23:
- 9 lost only because of the duplicate-domain margin bug: Sadie's Ward, Mary's, Jajaja, McManus, Bellagio Cafe, Three Pillars, Evil Twin, Snarf's, Sweet Science.
- 9 are single own-domain hits below 0.78: lazyboysaloonwp.com, goodroombk.com, vibranyc.com, laguardiaairport.com, restaurants.applebees.com/…/rensselaer, williamsville.canterburywoods.org, greencastletavern.ueniweb.com, yummychinesegreeley.kwickmenu.com, hyatt.com (lost only to booking.com).
- 5 are hard: bottegany.com vs bottegaveneta.com; rookies… vs sevens… (both belong to the account); mdrnyc.com (no name token in the domain); commonchordqc.org (renamed org); ihg.com (brand domain).
- The other 37 have only directories, maps, real-estate, government, TikTok or Reddit results, or nothing relevant.

**Failure patterns, by frequency in the 100 sampled rows:** local tourism, chamber or county directories (about 25); national aggregators such as yellowpages, tripadvisor.*, trip.com, opentable, resy, theinfatuation, wheree and mindtrip (about 15); maps (waze, apple) (4); .gov pages, PDFs and agendas (5); real estate (zillow, realtor, century21) (4); news (3); social and UGC (tiktok, reddit, cash.app) (3); OTA and hotel booking (booking, expedia) (2). Chains and multi-location brands (Applebee's, LongHorn, Hyatt, Snarf's, Olive Garden) are usually right at the domain level, and the location page is the best URL.

**Side effect that needs cleanup:** menu discovery has already crawled from the wrong 'matched' URLs. Matched accounts now have 29,121 menu candidates, and 4,157 of them are on directory or aggregator hosts:
```sql
select count(distinct a.account_id), count(*),
 count(*) filter (where c.source_url ~ '(chamber|traveliowa|visit|tourism|yellowpages|tripadvisor|wheree|mindtrip|waze|apple\.com|opentable|restaurants-info|\.gov)')
from accounts a join menu_source_candidates c using(account_id)
where a.website_discovery_status='matched' and a.website_discovery_source='firecrawl_search';
```
This also explains the blocked-menu pool in Job B: taphunter.com for TEXTILE TAPHAUS, amctheatres.com popcorn-pass pages, and so on.

### A4. Proposed scoring change and re-scoring of existing candidates (no new paid calls)
New acceptance rule, applied at the **domain** level:
1. **Hard block** by host pattern: directories, aggregators, maps, OTAs, real estate, news, .gov/.us, social and UGC, ordering platforms. Also block a page whose title contains 404, "page not found", "for sale" or "MLS#". The full regex is in the SQL below. Also block path patterns `/listing/`, `/directory/`, `/business/`, `/places/` and the hosts `restaurants-info` and `vacation*`. These last two cover the only 2 false positives found in the check sample.
2. **Identity test:** the host (minus www and TLD, with dots and dashes removed) must contain at least one *distinctive* name token of 4 or more characters. Tokens that match the city, the state, generic venue words (bar, grill, pub, tavern, club, lounge, restaurant, inn, bistro, kitchen, house, brewing, pizza, bbq, …) or org words (legion, post, vfw, eagles, aerie, elks, lodge, council, community, center, catering, …) do not count. Website-builder subdomains such as `*.wixsite.com`, `*.ueniweb.com` and `*.kwickmenu.com` pass because the host includes the venue label.
3. **Group candidates by registrable domain** (last two labels). Accept when exactly **one** registrable domain passes both 1 and 2. Several results from the same site no longer compete with each other. If two or more distinct domains pass, send the row to `review` (for example Bottega vs Bottega Veneta).
4. Pick the URL: prefer the site root, and otherwise the highest-scoring page on that domain. For chains, keep the location page when the city is in its URL.
5. The old numeric score becomes a tie-breaker only.

Re-scoring SQL (read-only preview; it runs on the stored candidates):
```sql
with acc as (select account_id, account_name, website_discovery_status st, website_url,
   lower(coalesce(substring(notes from 'City:\s*([^.]+)'),'')) city
  from accounts where account_status='active' and 'on_premise_spirits'=any(account_types)
   and website_discovery_status in ('matched','review')),
tok as (select a.account_id, array_agg(distinct t) toks
  from acc a, regexp_split_to_table(regexp_replace(regexp_replace(lower(a.account_name),'[^a-z0-9 ]+',' ','g'),'\s+',' ','g'),' ') t
  where length(t)>=3 and t not in ('the','and','bar','grill','grille','restaurant','rest','cafe','hotel','llc','inc','corp','company','dba',
   'club','lounge','tavern','pub','post','american','legion','vfw','foreign','wars','veterans','fraternal','order','eagles','aerie','elks',
   'lodge','moose','loyal','council','community','center','centre','association','assn','country','golf','new','york','iowa','colorado',
   'city','county','north','south','east','west','street','main','food','foods','kitchen','house','bistro','eatery','sports','catering',
   'caterers','events','inn','brewing','brewery','neighborhood','mexican','italian','chinese','pizza','bbq','steakhouse','restaurants',
   'cantina','saloon','wine','spirits','liquor','liquors','store','market','shop','amp')
   and position(t in a.city)=0 group by 1),
c as (select w.account_id, w.candidate_url, w.candidate_title, w.score,
   lower(regexp_replace(w.candidate_url,'^https?://(www\.)?([^/:?#]+).*$','\2')) host
  from website_discovery_candidates w join acc using(account_id)),
f as (select c.*, regexp_replace(host,'^(?:.*\.)?([^.]+\.[^.]+)$','\1') reg,
   regexp_replace(regexp_replace(host,'\.[a-z]{2,}$',''),'[.-]','','g') hlabel,
   (host ~ '(yelp|tripadvisor|facebook|instagram|google\.|mapquest|foursquare|doordash|ubereats|grubhub|yellowpages|wheree|mindtrip|waze\.com|apple\.com|opentable|resy\.com|zillow|realtor|homes\.com|causeiq|tiktok|reddit|wikipedia|cash\.app|theinfatuation|booking\.com|expedia|trip\.com|travelweekly|travel|colorado\.com|chamber|visit|tourism|tour|discover|explore|enchantedmountains|livemillscounty|howard-county|westcottsyr|onhavanastreet|century21|news|journal|publishing|gazette|times|tribune|register|\.gov$|\.us$|yahoo|chalkysticks|usnews|partyslate|rentalz|cgmimm|sideways|nooklyn|lulac|legion|crew\.fun|menupix|allmenus|restaurantji|sirved|toasttab|toast\.app|order\.online|beermenus|untappd|linkedin|twitter|x\.com|youtube|nextdoor|bbb\.org|manta|chownow|slicelife|seamless|postmates|roadtrippers|wanderlog|restaurantguru|zomato|groupon|eventbrite|allevents|patch\.com|theknot|weddingwire|indeed|glassdoor|loopnet|crexi|bizbuysell|enprimeurclub|dnb\.com|bizapedia|opencorporates|mapcarta|cylex|hotfrog|superpages|citysearch|menupages|kayak|hotels\.com|agoda|priceline|orbitz|uber\.com|lyft)'
    or candidate_title ~* '(page not found|\m404\M|for sale|mls#|homedetails)') blocked
  from c),
g as (select f.*, exists(select 1 from unnest(t.toks) x where length(x)>=4 and position(x in f.hlabel)>0) ident
  from f join tok t using(account_id)),
best as (select account_id, count(distinct reg) filter (where ident and not blocked) ident_domains,
   (array_agg(candidate_url order by (candidate_url ~ '^https?://[^/]+/?$') desc, score desc) filter (where ident and not blocked))[1] pick
  from g group by 1)
select a.st, count(*) n, count(*) filter (where b.ident_domains=1) accept_new,
 count(*) filter (where b.ident_domains>1) ambiguous, count(*) filter (where coalesce(b.ident_domains,0)=0) reject_new
from acc a left join best b using(account_id) group by 1;
```
Result:

| current status | n | accept (new) | ambiguous -> review | reject -> no_site_found |
|---|---|---|---|---|
| matched | 2,151 | 797 (65 of them move to a different, correct URL, e.g. PDT Catering) | 22 | 1,332 (mostly directory URLs; `website_url` should be cleared) |
| review | 2,020 | 717 | 53 | 1,250 |
| **total** | 4,171 | **1,514** | 75 | 2,582 |

**Precision check** on a fresh random sample of 50 accepted rows (seed `s3`): **48/50 correct (96%)**. Correct examples: toroloconyc.com, toniswinebar.com, restaurants.applebees.com/…/brooklyn, texasdebrazil.com, hyatt.com/park-hyatt/…, locations.tacobell.com/ny/brooklyn, m.longhornsteakhouse.com/…/camillus, felicerestaurants.com/felice-15-gold-street, golfhollowbrook.com, and others. The 2 wrong ones were `oldtrailinn.restaurants-info.com` and `vacationokoboji.com/listing/murphys`; the path and host blocks added in rule 1 fix both.

**Recall** of correct sites that exist in the stored candidates: 12/13 in the matched sample and 18/23 in the review sample, about 83% overall. Of the 5 missed, 2 are ambiguous (sent to review) and 3 are brand or renamed domains with no name token.

**Estimated result:** about 1,250-1,450 processed accounts end with a correct own site. That is **25-29% of the 5,050 processed**, up from about 13% today, at about 95% precision. The ceiling from stored candidates is about (0.33 x 2,151 + 0.38 x 2,020) / 5,050, which is roughly **29-33%**, because 62-67% of sampled accounts have no correct candidate stored at all. No `no_match` row has any stored candidate.

### A5. Honest answer on reaching 70% yield
It **cannot** be reached from the stored candidates. Options, cheapest first:
1. **Choose what "70% success" means.** The job's sample-able output is "the URL we accept is right". That is about 30% today and about 96% with A4. I recommend gating on precision of at least 90%, which A4 already meets, and reporting yield (correct sites / processed) as a separate KPI.
2. **Free directory hop, with no Firecrawl.** 1,161 accounts have a directory or aggregator candidate, and 667 of those are local chamber or tourism pages. Local listings such as traveliowa, chamber members pages and visitX usually carry the venue's "Website" link. Fetch each listing with the normal free fetcher, pull the outbound link, and run it through the A4 identity rule. If half of the local listings have a site link, yield rises by about 5-7 points.
3. **Handle social-only venues.** Many small Iowa and upstate NY bars have only a Facebook page, and BLOCKED throws those away before they are stored. Store the Facebook or Instagram URL in a separate `social_url` or `menu_status='social_hold'` field instead of discarding it. Counting "own site or official social page" would raise yield a lot. I cannot measure how much, because those results were never stored.
4. **Remove non-venue licensees from the denominator** or tag them: county fairs, airports, golf and country clubs, VFW, Legion, Eagles and other clubs, caterers, and entities like "OSSINING N Y". In the review sample these are about 15-20% of rows, and they rarely have a findable own site.
5. **A better paid search, only after a 50-account paid test** (about 100 credits):
   - Query `"<name>" <city> <state>` without "official website", `limit: 10`.
   - Add `-site:` exclusions for the top 10 directory hosts (yellowpages, tripadvisor, traveliowa, chamber sites, waze, apple maps, mindtrip, wheree, opentable, zillow).
   - Apply the A4 rule.
   - Proceed only if at least 70% of accepted results are correct **and** the yield on those 50 is measurably higher than 29%.

Even with 2-5, I expect yield to land around **45-60%**, not 70%, because a large share of rural licensees have no website at all. If Rob wants 70% as a *yield* target, the denominator has to exclude non-venues and social-only venues.

Implementation notes (not done here, no edits made):
- Port rules 1-3 into `scoreCandidate` and the selection logic of `index.ts`.
- Raise `MAX_RESULTS` to 5-10.
- Store every result, including blocked ones, with a `blocked_reason` so the rules can be re-scored later.
- Apply the re-score with a reviewed migration that does three things:
  - sets `website_url` / `website_discovery_status='matched'` for the 1,514 accepted rows;
  - demotes the 1,332 rejected 'matched' rows to `review` and clears their directory `website_url`;
  - marks the menu candidates spawned from directory hosts (4,157) as out of scope.

---

## Job B: paid blocked-menu recovery (cron 33, `extract-menu-candidates` with allow_paid)

### B1. How the pipeline decides the outcome
- The worker calls Firecrawl `/v2/scrape` (`formats:['markdown'], onlyMainContent:true`) for rows whose `last_error` matches `source_http_(401|403|429)`. It then runs `parseMenu()` and saves through `phg_save_menu_candidate_extraction`.
- The RPC sets `review` when 0 items are parsed. When items are parsed, it sets `extracted` only if `classify_menu_page()` returns `beverage` or `mixed`.
- The dispatcher `phg_dispatch_paid_blocked_menus` selects `order by id` over **all** scopes, including `food_candidate` and `unknown`. It has no per-account cap and no URL filter. That is how 14 Olive Garden pages (13 of them locations in MI/PA/VA/FL/SK/IL/CA/AZ/SC for an **Iowa** account) went into one 40-page batch. Their `menu_type='spirits'/'cocktail'` came from place slugs such as "aiken-whiskey-rd", "bourbonnais" and "near-margaritaville-resort".

### B2. What the 40 paid pages were
```sql
select c.id, a.account_name, c.source_url, c.menu_type, c.menu_scope, c.discovery_method, c.status, c.item_count,
       s.extraction_method, length(s.source_text) len
from menu_source_candidates c left join accounts a using(account_id)
left join lateral (select * from menu_extraction_sources s where s.candidate_id=c.id order by created_at desc limit 1) s on true
where c.id in (select candidate_id from menu_extraction_sources where extraction_method='firecrawl_markdown_v5')
   or c.id in (291,1177,1533,2760,4950,4565,2829,6052,5744,6945,8113,5176,8371,8502,10149,10667,10838,7430,10849,9081)
order by c.last_attempt_at;
-- join is menu_extraction_sources.candidate_id = menu_source_candidates.id
```
Per-page content counts (dollar prices, bare trailing numbers, drink and food keywords) came from the regexp_matches query in section B6. I then read the full text of every page under 2.8k characters and the relevant lines of the larger ones.

| Class | n | Candidate ids |
|---|---|---|
| **Real drinks menu, items in the markdown** | **1** | 5176 Beachcomber beer-and-wine-list: 34 items, success |
| Real drinks menu, but items not rendered (Popmenu lazy "Load More Content", QR link) | 3 | 5744 American Whiskey /menus/drinks (only a "Happy Hour" header); 291 Westbound & Down (anchors "## Drink Menu" with nothing under them); 6945 58 Main /menus/beer-menu (QR code linking to beermenus.com) |
| Olive Garden out-of-state location stubs (about 100 characters, JS shell) | 12 | 15326, 15334, 15343, 15349, 15356, 15365, 15373, 15378, 15382, 15391, 15403, 15417 |
| Olive Garden catering marketing pages | 2 | 15292, 15305 |
| Hotel overview pages (marriott.com) | 2 | 2760, 11262 |
| Homepages and location landing pages | 7 | 1533 LongHorn, 2829 Cenizas (Toast food menu), 4950, 10667 iPIE, 10838 DC's (food menu), 12530, 15061 |
| Online ordering (closed, pickup, food only) | 3 | 4565 toast.app, 8371 toast.site, 8502 order.online (food plus soft drinks) |
| Food-only menus | 3 | 8113 sushi catering, 10887 Fireside (food), 14886 lunch specials |
| Single-item or package pages | 3 | 1177 "Barq's Root Beer" item, 10149 "Beer & Wine $25.00 p/p" package (**counted extracted, but it is a false success**), 10849 empty "Option 1" |
| Catering marketplace | 1 | 15287 ezcater (**counted extracted with 2 items; the only beverage is a $4 soft drink**) |
| Events page | 1 | 6052 |
| Aggregator (photo menu) | 1 | 7430 wheree |
| Aborted, not archived | 1 | 9081 wanderboat.ai |

Summary: of 39 archived pages, **1** contained drink items in text and **3** more were real drinks pages whose items were not rendered. **35** were homepages, locations, hotels, ordering, catering, food-only or JS shells. Under the definition above, the sample success rate is **1/40 (2.5%)**, not 3/40.

### B3. Parser behaviour (ported and run locally)
I copied `parser.mjs` to the scratchpad and ran it on text patterns taken from the archive. `parser_v6.mjs` in the same folder is a prototype of the fixes.

| Pattern (from the archive) | v5 items | v6 prototype |
|---|---|---|
| Popmenu doubled price `Paloma` / `Tequila…$12.00$12.00Tequila…` (seen in 10887, 8113, 6052) | 0. `prices.length>1` drops the line | 3 (Paloma 12, Old Fashioned 13, Mule 11.5) |
| Toast multi-line link `[House Margarita\\ … $9.00\\ …](…)` (seen in 2829) | 0 | 2 |
| Bold-only heading `**BOTTLES AND CANS**` followed by `Labatt Blue & Light 5` | 0. The section is not set, so bare numbers are rejected | 3 |
| Unpriced draft list (`Big Ditch Hayburner IPA`, `Rohrbach Scotch Ale`) | 0 | 2 with `allowUnpriced` (needs an RPC change, since price must now be 1-1000) |
| Catering package `Beer & Wine $25.00 p/p` | 1 (false item) | 0 (`p/p`, `per person`, `serves N` rejected) |

v6 changes:
1. Collapse `$X$X` into `$X`.
2. Join `\\`-continued markdown link lines before splitting.
3. Treat `**bold**`, `#` and ALL-CAPS lines that contain drink or food words as sections.
4. In Popmenu layouts, a `###` heading followed by a priced description line becomes the item name.
5. Reject per-person and package prices.
6. Optionally keep unpriced items under drink sections, with `item_price null` and a separate `unpriced` flag. This needs `phg_save_menu_candidate_extraction` to accept null price for beverage rows.

**Effect on the sample: none.** None of the 35 bad pages has drink items to extract. v6 would only add the unpriced drafts to 5176, which was already a success. The parser is not the bottleneck; page selection is. A broader check of 400 free-fetched pages in `review` with beverage-looking paths agrees. 361 had fewer than 5 drink words (not a drinks page, or a shell), and 127 were under 1,500 characters. Of the 39 that did contain drink text, 25 were **unpriced** and 7 had `$` prices in other layouts. So allowing unpriced drinks is the single most useful parser change, but it matters for about 6% of pages, not 70%. The doubled-price bug occurs only in Firecrawl markdown: 5 archived texts in total, all from paid scrapes.

### B4. Pre-filter proposal: decide before paying
Pay for a blocked page only when **all** of these hold, using data we already have:
1. **Path intent.** The last path segment contains `drink|beer|wine|cocktail|bar-menu|beverage|spirits|tap-list|on-tap|happy-hour|margarita|sake|libation`. Matching the last segment avoids hits on place slugs like `aiken-whiskey-rd`, and on domain names like indulge**wine**bar.com.
2. **Path exclusions:** `/items?/`, `/locations?/`, `/order`, `catering`, `package`, `event`, `/posts?/`, `/blog`, `terms`, `popcorn`, `p-p`, `gift`, `careers`, `jobs`, `-ordering`.
3. **Same host as the account website**, and that website passes the Job A A4 rule (not a directory, a maps site, or a hotel-brand overview).
4. **Host not an aggregator or platform:** toast*, order.online, ezcater, wheree, wanderboat, marriott, hilton, hyatt, ihg, amctheatres, taphunter, chambers, visitX, yellowpages, tripadvisor, .gov.
5. The account does not already have `menu_status='extracted'`.
6. **At most 2 pages per account per run**, ranked drinks/cocktails > beer/wine > happy hour. This stops floods like Olive Garden, AMC and 110 Grill.
7. For Popmenu pages (`/menus/<slug>`), send render options: `waitFor` about 3000 ms, `onlyMainContent:false`, or a scroll action. The archive shows Popmenu pages can come back with a "Load More Content" placeholder instead of items (5744, 291).

Pre-filter SQL on the current blocked pool:
```sql
with p as (select c.id, c.account_id, a.menu_status,
   lower(regexp_replace(c.source_url,'^https?://[^/]+','')) path,
   lower(regexp_replace(c.source_url,'^https?://(www\.)?([^/]+).*$','\2')) host,
   lower(regexp_replace(coalesce(a.website_url,''),'^https?://(www\.)?([^/]+).*$','\2')) whost
 from menu_source_candidates c join accounts a using(account_id)
 where c.source_format='html' and c.is_food_only=false
   and c.menu_scope in ('beverage','beverage_candidate','mixed','unknown','food_candidate')
   and c.last_error ~ 'source_http_(401|403|429)' and c.extraction_attempt_count<6 and c.status in ('review','retry')),
f as (select *, row_number() over (partition by account_id order by (path ~ '(drink|cocktail|bar-menu|beverage)') desc, length(path)) rk
 from p
 where regexp_replace(path,'[?#].*$','') ~ '/[^/]*(drink|beer|wine|cocktail|bar-menu|barmenu|beverage|spirits|tap-list|taplist|on-tap|happy-hour|happyhour|margarita|sake|libation)[^/]*/?$'
   and path !~ '(/items?/|/locations?/|/order|catering|package|event|/posts?/|/blog|terms|popcorn|/p-p|gift|careers|jobs)'
   and host=whost
   and host !~ '(toast|order\.online|ezcater|wheree|wanderboat|marriott|hilton|hyatt|ihg|amctheatres|taphunter|chamber|visit|travel|yellowpages|tripadvisor|\.gov)'
   and coalesce(menu_status,'')<>'extracted')
select count(*), count(*) filter (where rk<=2), count(distinct account_id), count(*) filter (where rk<=2 and path ~ '^/menus/') from f;
```
- **Blocked pool now:** 4,848 candidates across 285 accounts. 1,456 are `/items/` pages, 563 are on a different host from the account website, and 129 are aggregators.
- **After the pre-filter:** 218 pages across 53 accounts, or **86 pages with the 2-per-account cap**. 67 of the 86 are Popmenu-style `/menus/…`. Examples: miguelsmex.com/menus/beer, bellaciaobuffalo.com/menus/drinks, alidadebrewing.com/menus/cocktails, darkhorsetavern.net/menus/high-horse-classic-cocktails, verdeeatdrink.com/menus/bar-menu. One slip-through, weence.com/faqs/…-drinks-between-meals, shows the list still needs a `faq` exclusion.

**On the 40-page sample, the pre-filter passes 3 pages:** 5176, 5744 and 6945. It would have saved 36 of 39 paid scrapes (92%).
- With the current Firecrawl settings and either parser: **1/3 (33%)**.
- With Popmenu render options and a free follow of the beermenus.com QR link for 6945: **up to 3/3**. That is unverified; it needs a paid test.

Three pages cannot demonstrate 70%, so **the rule is not met yet**. A gate that can be proven:
1. **Free probe, $0.** Re-fetch the 86 pre-filtered URLs directly with a standard browser User-Agent. Many 403s are bot rules against the `PHGMenuIndexer` UA, and anything that loads this way needs no Firecrawl at all. I did not run this, per the no-external-calls brief.
2. **Paid test, 10 pages.** Take 10 pages from the 86 that still fail and scrape them with the Popmenu render options and parser v6. Count success as defined above.
3. Run cron 33 only if 7 or more of 10 succeed. It should dispatch **only** from the pre-filter view, with the per-account cap and `pause` on the first provider 402/429 (already implemented).

Estimated outcome of that test, based on the population data: Popmenu-style beverage pages parse successfully 37% of the time when the free fetcher gets the HTML (25/67, from the query in B6). Other beverage-path pages succeed about 10% of the time. **Realistic expectation: 35-55% success, not 70%**, unless the render settings reliably expand Popmenu menus. If the 10-page test falls short, the right move is to keep Job B off and use the free UA probe plus a Popmenu-specific extractor. Popmenu pages embed the full menu in their page data, so a free fetch plus a JSON parser would avoid paying per page. That would need to be verified on one page first.

### B5. Changes to the parser and the save step (not applied)
- `parser.mjs`: v6 items 1-5 (doubled price, multi-line links, bold and caps sections, Popmenu heading items, reject per-person prices).
- `phg_save_menu_candidate_extraction`: accept `item_price null` for beverage items with an `unpriced` quality flag, and do not count unpriced items toward `extracted` unless there are 3 or more.
- Success accounting: count `extracted` only when at least 3 items have `item_type in (cocktail, beer, wine, spirit_pour)`. Today 10149 (1 package) and 15287 (1 soft drink) count as successes.
- `phg_dispatch_paid_blocked_menus`: replace `order by id` over all scopes with the B4 view and the per-account cap. Drop `food_candidate` and `unknown` scope unless the path shows drink intent.

### B6. Other SQL used
```sql
-- per-page content signals for the paid sample
with s as (select distinct on (candidate_id) candidate_id, source_text t from menu_extraction_sources
           where extraction_method='firecrawl_markdown_v5' order by candidate_id, created_at desc)
select candidate_id, length(t),
 (select count(*) from regexp_matches(t,'\$\s*\d{1,3}(\.\d{1,2})?','g')) dollar,
 (select count(*) from regexp_matches(t,'(^|\n)[^\n$]{3,80}\s\d{1,2}(\.\d{2})?\s*(\n|$)','g')) tailnum,
 (select count(*) from regexp_matches(lower(t),'\m(cocktails?|margaritas?|martinis?|beers?|ipa|lager|ale|stout|wines?|cabernet|pinot|chardonnay|bourbon|whiske?y|tequila|vodka|gin|rum|draft|draught|on tap|sangria|mojito|seltzer)\M','g')) drinkkw
from s;

-- historical success by URL bucket (free-fetched pages with archived text)
with p as (select c.*, lower(regexp_replace(c.source_url,'^https?://[^/]+','')) path from menu_source_candidates c
           where c.source_format='html' and exists(select 1 from menu_extraction_sources s where s.candidate_id=c.id))
select path ~ '^/menus/' popmenu,
 (path ~ '(drink|beer|wine|cocktail|bar-menu|barmenu|beverage|spirits|tap-list|taplist|happy-hour|happyhour|libation|margarita)'
  and path !~ '/locations?/|/items?/|catering|package|event|ordering') bevpath,
 count(*), count(*) filter (where status='extracted' and item_count>=3)
from p group by 1,2;
-- popmenu+bevpath 25/67 (37%), popmenu other 184/669 (28%), other bevpath 907/9153 (10%), other 6659/44021 (15%)
```
The 400-page review sample of beverage paths (unpriced vs priced drink text) used the same regexp_matches approach, with `order by md5(id::text) limit 400`.
