# PHG-051 review gate (market explorer v2)

Gate (Rob): nothing is published until the Spec Reviewer and the Safety Reviewer each average above 80.
"Publish" = PART C (phg_explorer_swap_next) + PART D (refresh_explorer_v2, cron 8 re-enable) of
supabase/migration_drafts/10_explorer_v2.sql. Parts A+B are already live (migration phg_explorer_v2_view_and_builder);
one-off build running as pg_cron job 25.

| Round | Spec score | Safety score | Spec average | Safety average | Changes made after the round |
|---|---|---|---|---|---|
| 1 | - | 68 | - | 68 | pending |

## Safety Reviewer - round 1 (2026-09-29, draft commit 1814d69)

**Evidence limits.** This session had no live database access: the Supabase MCP tools were not available to the
reviewer, and the proxy refused a direct REST connection (CONNECT 403). The review is based on the draft, the repo
(index.html, supabase/functions/*, migrations) and the handoff facts. Anything that needs the catalog is written below
as a pre-swap gate query. Those queries must be run, and their output recorded, before round 2.

### Scores
| Area | Score | Main evidence |
|---|---|---|
| Data preservation | 80 | No data deleted; old MVs kept as *_old. No check yet for objects bound to the old OIDs, and dropping *_old later with CASCADE would take those objects with it. |
| Correctness | 68 | mv_menu_dev_venue_profile groups by (venue, city, state_code), but its unique key is lower(venue)\|lower(city)\|state. The venue CTE has no tie-break. staging_id is unique only if every join is 1:1. getAll stops at 40,000 rows and pages without an ORDER BY. |
| Concurrency | 65 | lock_timeout 3 s applies per statement, and up to 6 renames can wait, so readers can be blocked for up to ~18 s. anon has a 3 s statement timeout (PHG-018). The refresh runs as one long transaction that includes the stats functions. |
| Performance | 55 | Nothing measured yet (v2 view time, build time, time for a CONCURRENTLY refresh). pin_row renumbers the pins on every refresh. The select=* payload grows. |
| Security | 80 | SECURITY DEFINER functions set search_path; EXECUTE revoked from anon, authenticated and service_role. The grant list is hard-coded, not copied from the old ACL. *_old stays readable by anon. Default privileges probably already expose *_next (and staging_id) to anon. |
| Reversibility | 60 | swap_back is atomic but not rehearsed. It does not pause cron 8 or restore its command. The old MVs probably have no unique index, so refresh_explorer_v2 fails on them. There is no verification query and no rollback for parts A/B. |
| **Round score** | **68** | |

### Blockers
- **B1 A refresh failure can make the explorer stale again (P0 again).** mv_menu_dev_venue_profile_next groups by
  (venue, city, state_code), but the unique index is on venue_key = lower(venue)|lower(city)|state. Two account_names
  that differ only in case in the same city (for example "Buffalo Wild Wings" and "BUFFALO WILD WINGS"), or city NULL
  vs '', give two groups with the same venue_key. The next REFRESH ... CONCURRENTLY then fails with a unique
  violation. refresh_explorer_v2 runs all six refreshes in one transaction, so all six roll back, and every later
  cron run fails the same way. Fix: build the key into the grouping:
  `SELECT min(venue) AS venue, min(city) AS city, min(state_code) AS state_code, venue_key, ... FROM mv_drink_explorer_next GROUP BY venue_key HAVING ...`
  with venue_key = (lower(venue)||'|'||lower(coalesce(city,''))||'|'||coalesce(state_code,'')). Readers already key
  on venue_key (index.html MD.byKey, phg-harmony-data), so they are not affected.
- **B2 The swap's lock budget can block readers for longer than the anon timeout.** Each ALTER ... RENAME takes
  ACCESS EXCLUSIVE and keeps it until commit. Up to six old-name renames can each wait 3 s, so the MVs renamed first
  stay blocked for all readers for up to ~18 s. Every new reader also queues behind a waiting rename. anon's 3 s
  statement timeout then gives 57014 / 504, the PHG-018 symptom. LOCK TABLE cannot lock materialized views up front.
  Fix: in both swap functions, `set lock_timeout = '300ms'` and `set statement_timeout = '3s'`. The operator retries
  up to N times on 55P03 / 57014 (nothing changes on failure). Before calling, check pg_stat_activity for readers of
  mv_% older than 1 s. Run at a quiet time.
- **B3 Objects that depend on the old MVs have not been checked.** Views, MVs (for example
  mv_venue_cocktail_similarity, v_public_drink_avg, v_venue_cocktail_profile) and BEGIN ATOMIC functions bind by OID.
  After the swap they would keep reading *_old, which is never refreshed. A later "drop by hand" with CASCADE would
  drop them. Gate query (must return only the four known old-chain MVs):
  ```sql
  select distinct c.relname as depends_on, d.classid::regclass, coalesce(v.relname, p.proname) as dependent
  from pg_depend d
  join pg_class c on c.oid = d.refobjid and c.relname in ('mv_drink_explorer','mv_dash_pins','mv_menu_dev_venue_profile',
       'mv_dash_sections','mv_dash_breakdown','mv_dash_filters') and c.relnamespace = 'public'::regnamespace
  left join pg_rewrite r on d.classid = 'pg_rewrite'::regclass and r.oid = d.objid
  left join pg_class v on v.oid = r.ev_class
  left join pg_proc p on d.classid = 'pg_proc'::regclass and p.oid = d.objid
  where d.deptype = 'n' and coalesce(v.oid, 0) <> c.oid;
  ```
  Also add this to phg_explorer_swap_next: raise if any dependent outside the six-MV chain exists.
- **B4 The rollback is incomplete and has not been rehearsed.** Write the rollback runbook in this order:
  (1) `select cron.alter_job(8, active := false)` (the old MVs probably have no unique index, so a CONCURRENTLY
  refresh fails on them; and re-enabling the old refresh_explorer brings back the ACCESS EXCLUSIVE blocking);
  (2) `select phg_explorer_swap_back()`;
  (3) `NOTIFY pgrst, 'reload schema'`;
  (4) verify with pg_class oid/relname: each live name is the pre-swap OID (record the OIDs before the swap), and
  anon can read each live name (has_table_privilege);
  (5) rollback for A/B: drop the _next MVs, phg_explorer_build_next and v_public_drink_explorer_v2.
  Rehearse swap -> checks -> swap_back in a DO block that ends with RAISE EXCEPTION. The DO block itself takes
  ACCESS EXCLUSIVE, so run it with the short lock_timeout from B2 and at a quiet time.

### Should fix
- **S1** Take corpus_counts, refresh_state_stats() and refresh_corpus_scale() out of refresh_explorer_v2. Job 5
  already runs the stats; PHG-024 shows they time out; and the extract-menus Edge functions call refresh_state_stats
  too, so they contend with it. As written, a stats timeout or deadlock rolls back minutes of MV refreshes, and the
  whole run is one snapshot that holds back xmin (accounts bloat, PHG-018). Better: a procedure with one COMMIT per
  refresh (timeouts set with set_config inside the procedure, no SET clause), called from cron as a single
  `CALL ...`. Or wrap each step in BEGIN/EXCEPTION so one failure does not undo the others.
- **S2** Venue CTE: `ORDER BY norm_site(a.website_url), a.google_review_count DESC NULLS LAST, a.account_id` needs a
  deterministic tie-break. Without one, venue name and city can flip between refreshes, and venue_key changes with
  them (Menu Studio clientKey, profile rows).
- **S3** Make staging_id unique by construction, or show which constraints guarantee it: a unique index on
  menu_item_cocktail_core(staging_menu_extract_id), one geography_demographics row per geography (a second ACS
  vintage would duplicate rows), one geographies city row per (upper(name), subdivision), and phg_census_zcta.zcta as
  PK. Otherwise use DISTINCT ON / LATERAL ... LIMIT 1 in the view.
- **S4** pin_row = row_number over the whole table renumbers every row after an insertion, so each CONCURRENTLY
  refresh rewrites most of mv_dash_pins. Use a stable key instead: pin_key = md5(row-as-text) plus dup_no = row_number()
  over (partition by pin_key). Put the unique index on (pin_key, dup_no).
- **S5** Copy the ACL from the old MV instead of a hard-coded role list (grantees of SELECT, excluding the owner):
  `for g in select distinct a.grantee::regrole::text from pg_class c, aclexplode(c.relacl) a where c.oid = ('public.'||r||'_old')::regclass and a.privilege_type = 'SELECT' and a.grantee <> c.relowner and a.grantee <> 0 loop execute format('grant select on public.%I to %s', r, g); end loop;`
  Then revoke anon and authenticated on *_old (and restore them in swap_back).
- **S6** `NOTIFY pgrst, 'reload schema'` after swap and swap_back. The comment "PostgREST resolves by name per request"
  is true for the SQL it runs, but its column cache (for staging_id / pin_row) needs a reload.
- **S7** Pre-swap gate, recorded in this log:
  - job 25 succeeded (cron.job_run_details);
  - row counts old vs _next, per state;
  - per-state _next rows for mv_drink_explorer must stay below 40,000, because index.html getAll stops at 40 pages and
    heavyLoad (select=*) would silently drop the rest;
  - venues present in the old MV and missing from _next, with the reason;
  - share of rows with income / median_age, per state (IA must not drop);
  - index parity between old and _next (pg_indexes). No old index a reader relies on may be missing.
- **S8** Index names travel with the MV, so after the swap the live MVs carry mv_de_next_* index names, and any later
  phg_explorer_build_next() fails with "relation already exists". Rename the indexes in the swap (old ones to
  *_old_*, new ones to live names), or give the builder names that cannot collide.
- **S9** index.html: CONCURRENTLY commits in the middle of a paged read, and pages have no ORDER BY, so a page read
  can skip or duplicate rows. Add `&order=staging_id` (mv_drink_explorer) and a unique order (venue_key) for
  mv_menu_dev_venue_profile. Replace select=* in heavyLoad with the columns that are actually used.
- **S10** Prevent overlap: `if not pg_try_advisory_xact_lock(hashtext('phg_explorer')) then return 'skipped: running'; end if;`
  in refresh_explorer_v2, phg_explorer_build_next and both swap functions. This covers job 25, manual runs and cron 8.

### Minor
- Default privileges probably make the _next MVs anon/authenticated-readable already (including staging_id). Check
  their relacl; revoke from anon and authenticated until the swap.
- Census now mixes city-level (IA) and ZIP/ZCTA-level (CO/NY and IA fallback) medians in the same income/age bands,
  and income and age can come from different levels for the same row. Document this in the UI and catalog; the
  ZIP != ZCTA caveat from PHG-029 applies.
- The swap functions write no log row (who, when, OIDs before/after). Add one to make rollback verification easier.
- Plan the Part D timing: measure one manual run first, as planned. If it takes more than a few minutes, run hourly
  instead of every 30 min.

### Verdict
fix_and_resubmit. Blockers B1-B4 must be fixed, and the S7 gate output recorded, before round 2.

## Round 2 submission (2026-09-29 ~16:30 UTC) - lead developer
Draft rewritten for round-1 findings (see [R2 Bn/Sn] markers in supabase/migration_drafts/10_explorer_v2.sql).
Live facts gathered with DB access (the round-1 reviewer had none):
- B1 confirmed live: round-1 build (cron job 25) failed after ~8 min exactly on the mdvp venue_key unique index
  (ilili|new york|NY). Also: job 25 put cron.unschedule in the same transaction as the build, so the failure rolled the
  unschedule back and it re-ran (3 runs); all cancelled; job 25 removed. Round 2 job 26 was unscheduled by hand after
  its first run started; it ran 15:56:00 -> 16:05:31 UTC (571 s) and SUCCEEDED.
- B3 gate (pg_depend): no dependents of the six live MVs outside the chain; no functions bound to them.
- S3: menu_item_cocktail_core.staging_menu_extract_id, city demographics per (upper(name), state) and zcta: 0 duplicates
  today; v2 view uses LATERAL ... LIMIT 1 anyway.
- S5: all six *_next ACLs are {postgres, service_role} only (not app-readable before the swap).
- Unique indexes: every *_next has one (mv_de_next_uk staging_id, mv_dash_pins_next_uk pin_key, mv_mdvp_next_key,
  sections/breakdown/filters _uk). Live mv_drink_explorer and mv_dash_pins have none (so swap_back + concurrent refresh
  would fail on the old copies - swap_back runbook must restore the OLD cron 8 command, not refresh_explorer_v2).
- Added index mv_de_next_st_sec_sid (state_code, section, staging_id) for the app's keyset paging.
- Sizes: explorer 13 MB -> 50 MB; pins 5.6 -> 8.3 MB; others < 3 MB.
- Gate counts live -> next: CO 16,920 -> 37,325 rows (773 -> 1,641 venues, income 0% -> 100%); IA 11,627 -> 15,144
  (522 -> 770, 99.6% -> 100%); NY 9,110 -> 75,549 (383 -> 3,218, 0% -> 99.1%). NY unclassified 25,176 rows avg $239.
- S7/S9 app: 18.49.45 deployed to main (Netlify ready): explicit 11 columns, keyset order=staging_id when the column
  exists (probe cached; re-checked every 10 min so the swap is picked up mid-session), fallback ordered offset paging on
  the old MV, 100-page cap with a visible warning, drink sections first and unclassified in the background, fix for a
  57014-retry duplicate-rows bug. Playwright test: 75,549 NY rows arrive exactly, both MV shapes.
- phg-harmony-data selects named columns from mv_dash_pins / mv_drink_explorer (no select=*).
Asks for round 2: review parts C (swap / swap_back with lock_timeout 300 ms, statement_timeout 3 s, ACL copy, index
renames, OID log, NOTIFY pgrst) and D (procedure with per-refresh COMMIT; not SECURITY DEFINER because it commits), the
rehearsal plan, and whether anything still blocks applying C and running the rehearsal.
