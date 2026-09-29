# State expansion research brief (for research agents)

PHG covers Iowa, Colorado and New York. Rob wants the other 47 states (+ DC). For each state, find how PHG can get
the list of bars and restaurants that serve alcohol (on-premise liquor licences), because that list seeds everything
else (Google Places enrichment -> website -> menu discovery -> menus). Reference: CO used the state's Socrata open-data
licence register (data.colorado.gov ier5-5ms2, includes lat/long); NY used data.ny.gov 9s3h-dpkz (active licences,
geocoded); Iowa is a control state and we used Iowa Data Hub liquor sales + licensee data.

For EACH state write one JSON object (one per line) to the file named in your task:
{"state":"TX","name":"Texas",
 "regime":"license|control|hybrid",            // control = state runs wholesale/retail of spirits
 "agency":"Texas Alcoholic Beverage Commission (TABC)","agency_url":"...",
 "licence_data":{"available":"open_data|bulk_download|search_only|request_or_foia|paid|none|unknown",
   "portal":"Socrata|ArcGIS|CKAN|agency site|other","dataset_url":"...","dataset_id":"...",
   "format":"api_json|csv|xlsx|pdf|html_search","geocoded":true|false|null,"update_frequency":"daily|weekly|monthly|unknown",
   "on_premise_codes":"how to tell bars/restaurants apart (licence types/classes), if shown","row_estimate":null,
   "cost":"free|fee (amount)|unknown","terms_notes":"any use restrictions"},
 "local_control":"if licences are issued by counties/cities instead of the state, say so and name the level",
 "alternatives":["other lists if the state has no usable one: county/city open data, health inspection data, sales tax permits, FOIA"],
 "automation":"full|partial|manual",           // full = scheduled API/download; partial = periodic manual export; manual = request/FOIA/scrape needed
 "manual_steps":["exactly what a person must do, if anything (e.g. 'submit public records request to X at URL', 'download xlsx monthly')"],
 "notes":"gotchas (dry counties, private clubs, tribal land, etc.)",
 "sources":[{"url":"...","title":"..."}],"confidence":"high|medium|low"}

Rules: use ONLY WebSearch (WebFetch is blocked; never use any Firecrawl tool). Cap ~45 searches for your states.
Prefer the state's own open-data portal (data.<state>.gov, Socrata, ArcGIS Hub) and the licensing agency's site.
Never guess a dataset URL or id: if you did not see it in a result, set it null and say so. Validate each line as JSON.
Write only your file. Return a short report: which states are fully automatable, which need manual steps, gaps.
