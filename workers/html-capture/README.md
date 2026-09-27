# HTML capture worker v2 (PHG-034)

Replaces the screenshot logic of the Railway HTML worker (whose source, WORKER_CODE_B64, is not in this repo - PHG-007).
Same queue and API (`menu-render-worker-api` claim_html / complete_html / fail_html), so no server change is needed and
both workers can run side by side while v2 is checked.

What it fixes (Rob's examples, 2026-09-27):

| Problem | Example | Fix |
|---|---|---|
| Screenshot stops after the first screen (4,137 of 14,008 are exactly 1000 px) | Mymoon bar menu | dismiss cookie/age pop-ups, unlock scrolling, expand inner scroll containers |
| Photos / drinks that load on scroll come out blank | 317 Main Street, Bonao | scroll the whole page until its height is stable, force lazy images, wait for images |
| Tabbed menus keep only the first tab | Watershed: Beer / Wine / Cocktails / Spirits | click each drinks tab and stitch every state under the first |
| Sticky "Order online" bars over the menu | Bonao | hide small fixed/sticky overlays |

Separate pages (Adrift: Cocktails, Spirits, Happy Hour) are not a worker job: discovery already found them and they
are queued as their own documents.

Resolution is unchanged (1400 px wide, JPEG 85); tall pages are shot in 8,000 px slices and stitched (max 60,000 px).

## Deploy on Railway

1. New service from this repo, root directory `workers/html-capture` (Dockerfile build).
2. Variables: `PHG_WORKER_API_URL` = `https://lqjtwabzmgjcufftuqvu.supabase.co/functions/v1/menu-render-worker-api`,
   `PHG_WORKER_TOKEN` = the existing HTML worker token (same value the current worker uses), `PHG_WORKER_ID` = `html-v2-1`.
3. Start 1 replica, check its log lines (`{"page_id":..,"status":"ready","h":..,"notes":[..]}`), then scale up and stop the old worker.

## Test locally

    pip install -r requirements.txt
    python test/run_fixtures.py      # old vs new on 5 fixtures reproducing the examples; writes test/out/*.jpg
    python test/mock_api_test.py     # full claim -> capture -> complete loop against a mock API
