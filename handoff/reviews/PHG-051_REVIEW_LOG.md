# PHG-051 review gate (market explorer v2)

Gate (Rob): nothing is published until the Spec Reviewer and the Safety Reviewer each average above 80.
"Publish" = PART C (phg_explorer_swap_next) + PART D (refresh_explorer_v2, cron 8 re-enable) of
supabase/migration_drafts/10_explorer_v2.sql. Parts A+B are already live (migration phg_explorer_v2_view_and_builder);
one-off build running as pg_cron job 25.

| Round | Spec score | Safety score | Spec average | Safety average | Changes made after the round |
|---|---|---|---|---|---|
| 1 | - | 68 | - | 68 | draft rewritten, live gate facts gathered (round 2 submission) |
| 2 | - | 75 | - | 75 | round 3: reviewer helpers, lock_timeout only, session lock in refresh, pg_proc check, classify_item LIMIT 1; applied live, rehearsal OK |
| 3 | - | 83 | - | 83 | pending (swap approved; cron 8 re-enable gated on S-R3-1..S-R3-4 and the timed run) |

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

## Safety Reviewer - round 2 (2026-09-29, draft commit 2d53250, app 18.49.45)

**Evidence.** Still no live DB access for the reviewer; the live facts are the lead's (round 2 submission above).
New in this round: Part C and the procedure pattern were executed on a throwaway local PostgreSQL 16.13 cluster
(mock six-MV chain with Supabase-style roles anon / authenticated / service_role and default grants). Live is PG 17.6;
nothing tested here differs between 16 and 17. Results quoted below are from those runs.

### Round-1 findings: status
| Item | Status | Evidence |
|---|---|---|
| B1 venue_key duplicates | fixed | mdvp grouped by venue_key; job 26 build SUCCEEDED with mv_mdvp_next_key unique (571 s). |
| B2 swap lock budget | partly | lock_timeout 300 ms works (local: swap against a reader holding AccessShare failed in 311 ms, nothing renamed). `SET statement_timeout = '3s'` on the function does nothing (local: a function with SET statement_timeout 1s ran pg_sleep(2) to completion). Only live-MV renames can wait (index renames take ShareUpdateExclusive, which readers do not conflict with), so the worst reader stall is about 6 x 300 ms. |
| B3 dependents | fixed | Live pg_depend gate clean. The in-function check covers views/MVs only (pg_rewrite), not BEGIN ATOMIC functions (see S-R2-4). |
| B4 rollback + rehearsal | partly | Runbook and swap_back written, but both swap functions fail on every run (R2-B1), so the rehearsal has not been run. cron 8's current command has not been recorded. |
| S1 stats out, per-refresh COMMIT | fixed, with caveats | See S-R2-2 and S-R2-3 (timeouts, advisory lock across COMMITs). |
| S2 venue tie-break | fixed | `ORDER BY norm_site, google_review_count DESC NULLS LAST, account_id`. |
| S3 staging_id unique | fixed | LATERAL ... LIMIT 1, 0 duplicates live, unique index built. One open point: classify_item (S-R2-7). |
| S4 stable pin key | fixed | md5(row) plus row_number within identical rows. |
| S5 ACL copy | partly | Copies grantees of every privilege (not only SELECT), skips PUBLIC (grantee 0), and quotes `regrole::text` a second time with %I. Old live relacl has not been recorded. |
| S6 NOTIFY pgrst | fixed | Transactional: sent on commit, dropped when the rehearsal rolls back. It is fine inside a SECURITY DEFINER function. |
| S7 pre-swap gate | partly | Counts, per-state rows, income share and job success are recorded. Still missing: index parity old vs new, venues in the old MV missing from _next (with the reason), old relacl, old index names. |
| S8 index names | not fixed (design right, code broken) | See R2-B1. With the fix, no name collides across build -> swap -> drop _old -> build -> swap -> swap_back (tested locally for two full cycles). |
| S9 app ordering / columns | fixed | Keyset `order=staging_id.asc&staging_id=gt.<last>` backed by (state_code, section, staging_id). Old-MV fallback is ordered Range paging. There is a visible 100-page cap, and partial pages are flagged. |
| S10 overlap | fixed (swap / build); partly (refresh) | See S-R2-3. |

### Scores
| Area | Score | Main evidence |
|---|---|---|
| Data preservation | 85 | Nothing is deleted. Old MVs are kept as *_old, and the swap is one transaction. Still no written drop-of-_old statement (it must not use CASCADE), and the old relacl is not logged. |
| Correctness | 70 | Part B is correct and built. Part C cannot succeed as written (R2-B1). The ACL copy drops PUBLIC and over-grants. |
| Concurrency | 80 | lock_timeout is effective, the refresh is CONCURRENT, and there are advisory locks. But statement_timeout is illusory in both the functions and the procedure, and the xact advisory lock is released at every COMMIT. |
| Performance | 70 | Build time, sizes and the keyset index are measured. No timing yet for a CONCURRENTLY refresh of the v2 chain. Each hourly run holds a snapshot of about 8-10 min (xmin horizon; accounts churn). |
| Security | 82 | DEFINER functions set search_path; EXECUTE is revoked from anon, authenticated and service_role; the _next MVs are closed until the swap. ACL-copy flaws are listed in S-R2-1. Nobody has checked who can EXECUTE the old refresh_explorer(). |
| Reversibility | 62 | swap_back exists, but it is broken by R2-B1 and has not been rehearsed. The per-state cron 8 plan is not written down, and the current cron 8 command has not been saved. |
| **Round score** | **75** | |

### Blockers
- **R2-B1 Both swap functions always fail: the index names come from `regclass::text`, which is unqualified.**
  The functions run with `search_path = public, pg_temp`, so `indexrelid::regclass::text` prints `mv_de_next_uk`
  without the schema, and `split_part(name, '.', 2)` returns ''. Local run of the draft:
  `ERROR: zero-length delimited identifier ... alter index mv_dash_filters_next_uk rename to ""`. An old MV with two
  or more indexes would also collide on the name `_old`. The failure is atomic, so no data is at risk, but Part C, the
  rehearsal and the rollback cannot work. Fix (tested locally: rehearsal, swap, drop _old, rebuild, second swap,
  swap_back, PUBLIC and a quoted role name). Add two helpers and use them in both swap functions:
  ```sql
  create or replace function public.phg_explorer_rename_indexes(rel text, pat text, rep text) returns void
  language plpgsql security definer set search_path = public, pg_temp as $$
  declare ix record; newname text;
  begin
    for ix in select ic.relname from pg_index i join pg_class ic on ic.oid = i.indexrelid
               where i.indrelid = format('public.%I', rel)::regclass order by ic.relname loop
      newname := regexp_replace(ix.relname, pat, rep);
      if newname <> ix.relname then
        if length(newname) > 63 then raise exception 'index name too long: %', newname; end if;
        execute format('alter index public.%I rename to %I', ix.relname, newname);
      end if;
    end loop;
  end $$;
  create or replace function public.phg_explorer_copy_select(src text, dst text) returns void
  language plpgsql security definer set search_path = public, pg_temp as $$
  declare g record;
  begin
    for g in select distinct a.grantee from pg_class c, aclexplode(c.relacl) a
              where c.oid = format('public.%I', src)::regclass and a.privilege_type = 'SELECT' and a.grantee <> c.relowner loop
      if g.grantee = 0 then execute format('grant select on public.%I to public', dst);
      else execute format('grant select on public.%I to %I', dst, (select rolname from pg_roles where oid = g.grantee)); end if;
    end loop;
  end $$;
  revoke all on function public.phg_explorer_rename_indexes(text,text,text), public.phg_explorer_copy_select(text,text)
    from public, anon, authenticated, service_role;
  ```
  swap_next loop body:
  ```sql
  perform public.phg_explorer_rename_indexes(r, '$', '_old');
  execute format('alter materialized view public.%I rename to %I', r, r || '_old');
  execute format('alter materialized view public.%I rename to %I', r || '_next', r);
  perform public.phg_explorer_rename_indexes(r, '_next', '_v2');
  perform public.phg_explorer_copy_select(r || '_old', r);
  execute format('revoke all on public.%I from public, anon, authenticated', r || '_old');
  ```
  swap_back loop body: use `('_v2','_next')` before the renames, `('_old$','')` after them, and
  `copy_select(r || '_next', r)`. In the precheck, also fail if any `r || '_next'` exists, i.e. a rebuild ran after the
  swap (otherwise the rename collides with a less clear error).
  Traced names: live v1 `X` -> `X_old`; v2 `mv_de_next_uk` -> `mv_de_v2_uk`; the next build makes `mv_de_next_uk`
  again (free); the second swap makes `mv_de_v2_uk` -> `mv_de_v2_uk_old` and `mv_de_next_uk` -> `mv_de_v2_uk`;
  swap_back reverses each step. Gate: every live old index name is 59 characters or less (the helper raises
  otherwise).
- **R2-B2 (gate, not code) The rehearsal and the cron 8 baseline must be on record before the real swap.** After
  R2-B1, applying Part C creates only the log table and functions, so it is safe to apply for the rehearsal. The
  real swap stays blocked until:
  (a) `select jobid, schedule, command, active from cron.job where jobid = 8` is pasted here verbatim;
  (b) the rehearsal below has been run live, with its output here;
  (c) `select relname, relacl, relowner::regrole from pg_class where relname in (<6 live names>)` plus old index
      names/definitions (pg_indexes) are pasted here.

### Rehearsal (run as ONE statement, at a quiet time; catalog-only checks keep the ACCESS EXCLUSIVE hold under ~100 ms)
```sql
set statement_timeout = '5s';  -- same string as the DO: a SET before a DO/SELECT in one query string is honoured
do $r$ declare o jsonb; n text; begin
  select jsonb_object_agg(relname, oid) into o from pg_class where relnamespace='public'::regnamespace and relkind='m'
     and relname ~ '^mv_(drink_explorer|dash_pins|menu_dev_venue_profile|dash_sections|dash_breakdown|dash_filters)(_next)?$';
  perform public.phg_explorer_swap_next();
  foreach n in array array['mv_drink_explorer','mv_dash_pins','mv_menu_dev_venue_profile','mv_dash_sections','mv_dash_breakdown','mv_dash_filters'] loop
    if not has_table_privilege('anon', 'public.'||n, 'select') or not has_table_privilege('authenticated', 'public.'||n, 'select')
      then raise exception 'FAIL app cannot read %', n; end if;
    if has_table_privilege('anon', 'public.'||n||'_old', 'select') then raise exception 'FAIL %_old still open', n; end if;
    if to_regclass('public.'||n)::oid <> (o->>(n||'_next'))::oid then raise exception 'FAIL % is not the v2 build', n; end if;
    if not exists (select 1 from pg_index where indrelid = ('public.'||n)::regclass and indisunique) then raise exception 'FAIL % has no unique index', n; end if;
  end loop;
  perform public.phg_explorer_swap_back();
  if (select jsonb_object_agg(relname, oid) from pg_class where relnamespace='public'::regnamespace and relkind='m'
        and relname ~ '^mv_(drink_explorer|dash_pins|menu_dev_venue_profile|dash_sections|dash_breakdown|dash_filters)(_next)?$') <> o
    then raise exception 'FAIL OIDs not restored'; end if;
  raise exception 'REHEARSAL OK';
end $r$;
```
The swap functions' try-lock is re-entrant inside one session, so swap_back inside the same DO works. The NOTIFY and the
log rows roll back with the DO. A result of 55P03 (lock timeout) means a busy reader. Nothing changes in that case;
retry.

### cron 8 in each state (write this into the runbook)
| State | cron 8 |
|---|---|
| Before the swap | paused, command = the old one (recorded per R2-B2a). Never re-enable it: it does non-concurrent refreshes (PHG-018). |
| Swapped, not yet timed | still paused. Time one run as a one-off pg_cron job whose command is exactly `CALL public.refresh_explorer_v2()`. This proves the COMMIT path under pg_cron libpq mode (cron.use_background_workers=off). |
| Swapped, timed | `select cron.alter_job(8, schedule := '<from timing>', command := 'CALL public.refresh_explorer_v2()', active := true)`. The command must be that single statement. Local test: `set statement_timeout='10min'; call p();` in one string gives `ERROR: invalid transaction termination` (an implicit transaction block). |
| Rollback | 1) `cron.alter_job(8, active := false)`. 2) Wait until no `CALL public.refresh_explorer_v2` is running (swap_back's try-lock fails fast while it runs). 3) `set statement_timeout='3s'; select public.phg_explorer_swap_back();` 4) Set command := <recorded old command>, active := false. 5) Verify that the swap_log 'after' OIDs equal the first 'swap' row's 'before' OIDs, and that anon has SELECT on all six. Do not leave refresh_explorer_v2 active on the old MVs: mv_drink_explorer and mv_dash_pins have no unique index, so every run would fail at the first MV. |
| Drop _old (later) | `drop materialized view public.mv_dash_filters_old, public.mv_dash_breakdown_old, public.mv_dash_sections_old, public.mv_menu_dev_venue_profile_old, public.mv_dash_pins_old, public.mv_drink_explorer_old;` Never use CASCADE. This drops only rollback capability. |

### Should fix
- **S-R2-1 ACL copy.** Use `phg_explorer_copy_select` above. It copies SELECT only, maps PUBLIC to `to public`, and
  quotes rolname once. Store `relacl::text` for each name in the swap_log `before` / `after` JSON as well as the OIDs,
  so a rollback can be compared exactly. swap_back grants SELECT only. If the old ACL was `anon=arwdDxtm`, the result
  is not byte-identical, but it is equivalent for an MV.
- **S-R2-2 statement_timeout does not bound a running call.** This project already knows it (changelog: "SET LOCAL
  statement_timeout does not bound the running call"). Local tests confirm it for a function SET clause, for
  `set_config(...,true)` in a procedure, and for set_config after a COMMIT inside a procedure. lock_timeout does work
  via set_config (a local test failed in 201 ms).
  Fix: drop `set statement_timeout = '3s'` from both swap functions (keep lock_timeout) and run them as
  `set statement_timeout = '3s'; select public.phg_explorer_swap_next();` (one string is fine for a function). In the
  procedure, delete the `statement_timeout` set_config line; it gives a false sense of a bound. Record the real bound
  with `select rolname, rolconfig from pg_roles where rolname = 'postgres'` and
  `select * from pg_db_role_setting`. If none applies, add a watchdog to an existing cron job:
  `select pg_cancel_backend(pid) from pg_stat_activity where query ilike 'CALL public.refresh_explorer_v2%' and now() - query_start > interval '30 min';`
- **S-R2-3 The advisory xact lock is released at every COMMIT** (a local test showed the lock was no longer held after
  the COMMIT). A build or swap can slip in between two refreshes. Use a session lock for the whole CALL:
  `if not pg_try_advisory_lock(hashtext('phg_explorer')) then raise notice 'explorer busy; skipped'; return; end if;`
  before the loop and `perform pg_advisory_unlock(hashtext('phg_explorer'));` after it. Session locks conflict with
  the xact try-locks on the same key held by other sessions. An error before the unlock leaks the lock only until the
  cron connection closes, and pg_cron libpq mode opens a new connection each run. Do not use an EXCEPTION block around
  the COMMITs, because COMMIT is not allowed inside one.
- **S-R2-4** The B3 check in swap_next should also refuse pg_proc dependents: add
  `or exists (select 1 from pg_depend d join pg_class src on src.oid = d.refobjid where d.classid = 'pg_proc'::regclass and src.relnamespace = 'public'::regnamespace and src.relname = any (names))`.
- **S-R2-5 Old refresh_explorer().** Before the swap, check
  `select has_function_privilege('anon','public.refresh_explorer()','execute'), has_function_privilege('authenticated','public.refresh_explorer()','execute')`.
  After the swap the function refreshes the v2 MVs non-concurrently by name, so any caller locks readers again. Revoke
  EXECUTE from public, anon and authenticated (no repo caller other than cron 8 was found).
- **S-R2-6 Performance.** Record the timed CALL with the time per MV (add `raise notice '% % s', r, ...` per step), and
  EXPLAIN (ANALYZE, BUFFERS) of `select count(*) from v_public_drink_explorer_v2`. Choose the cadence from that: hourly
  only if a run takes 3 min or less, otherwise every 3 h or off-peak. While a run is going, watch
  `n_dead_tup` on accounts and staging_menu_extract, because each run holds one snapshot for the length of the
  mv_drink_explorer refresh.
- **S-R2-7** Confirm `select proretset, prorows from pg_proc where proname = 'classify_item'`. If it returns a set, a
  second match for one name duplicates staging_id, and every later CONCURRENTLY refresh fails. In that case wrap it as
  `left join lateral (select * from classify_item(b.item_name) limit 1) c on true`.
- **S-R2-8 Finish S7:** index parity (every old live index column set has an equivalent on _next), and old venues
  missing from _next with the reason (a count by reason is enough).

### Minor
- swap_back revokes only public, anon and authenticated from the demoted v2 copy. Any other grantee copied at the
  swap keeps SELECT on *_next.
- The app's old-MV fallback order `venue_key,item_name,item_price` is not unique (the old MV has duplicate rows), so a
  Range page can still repeat or skip tied rows. The old MV is frozen, so the plan is stable in practice. This goes
  away after the swap.
- The comment in Part B still says the build job "unschedules itself in its own transaction". The actual method is a
  manual unschedule. Fix the comment.
- The procedure returns after a failed refresh without refreshing the dependents. That is intended, but the header
  comment ("a failure in one leaves the others fresh") overstates it: only the earlier ones are fresh.

### Verdict
**fix_and_resubmit** (75; the gate needs more than 80). What remains is small and specific. Apply the R2-B1 code
(tested), S-R2-1, S-R2-2 and S-R2-3 in the draft. Record the R2-B2 baseline. Then applying the corrected Part C and
running the rehearsal is safe (it creates only a table and functions; the DO block keeps nothing). Resubmit with the
rehearsal output. If that is green and the S-R2 items are done, the expected scores are about Correctness 85,
Reversibility 85 and Concurrency 85, for a round score in the mid-80s.

## Round 3 submission (2026-09-29, lead developer)

Applied live as migration `phg_explorer_v2_round3_swap_refresh` (file supabase/migrations/20260929170000_...):
Part A (view; classify_item via LATERAL (...) LIMIT 1), Part C (swap log table, reviewer's rename/ACL helpers verbatim,
phg_explorer_state, swap_next/swap_back with lock_timeout 300 ms only and the pg_proc dependents check), Part D
(refresh_explorer_v2 with a session advisory lock, lock_timeout 5 s per refresh, no statement_timeout). Part B unchanged.

| Round-2 item | Status |
|---|---|
| R2-B1 swap always failed (unqualified regclass::text) | fixed: helpers read pg_class.relname; rehearsal passes live |
| R2-B2 gate facts | (a)(b)(c) below |
| S-R2-1 SELECT-only ACL copy | reviewer's copy_select verbatim (anon/authenticated get SELECT only after swap, down from arwdDxtm) |
| S-R2-2 statement_timeout illusory | removed from both functions and the procedure; operator runs `set statement_timeout='3s'; select ...` |
| S-R2-3 xact lock released at COMMIT | refresh uses pg_try_advisory_lock / pg_advisory_unlock (session). A failed run leaves the lock until its backend exits; pg_cron uses one backend per run, so it clears when the run ends |
| S-R2-4 functions depending on live MVs | pg_depend classid = pg_proc check added |
| classify_item is SETOF (1000 rows est.) | LATERAL LIMIT 1; today's MVs have 0 duplicate staging_ids, so the _next builds are unaffected |

(a) cron 8, verbatim: `{"jobid":8,"schedule":"*/10 * * * *","command":"select public.refresh_explorer()","active":false}`

(b) Rehearsal, run live 2026-09-29 as one statement with `set statement_timeout = '5s'`:
```
ERROR:  P0001: REHEARSAL OK
CONTEXT:  PL/pgSQL function inline_code_block line 16 at RAISE
```
After it: phg_explorer_swap_log rows = 0; side MVs = the six *_next only (no *_old); live OIDs unchanged.

(c) Live ACL / owner (all owner postgres):
- mv_dash_breakdown, mv_dash_filters, mv_dash_pins, mv_dash_sections:
  `{postgres=arwdDxtm/postgres,anon=arwdDxtm/postgres,authenticated=arwdDxtm/postgres,service_role=arwdDxtm/postgres}`
- mv_drink_explorer, mv_menu_dev_venue_profile: the same plus `phg_menu_designer=r/postgres,phg_harmony_reader=r/postgres`

Live indexes (old names, all <= 21 chars, so "_old" suffix fits):
mv_dash_breakdown_idx (state_code, section, dimension); mv_dash_breakdown_uk UNIQUE (state_code, section, dimension, label);
mv_dash_filters_idx (state_code, dimension); mv_dash_filters_uk UNIQUE (state_code, dimension, value);
mv_dash_pins_items (drink_items DESC); mv_dash_pins_state (state_code);
mv_dash_sections_idx (state_code, section); mv_dash_sections_uk UNIQUE (state_code, section);
mv_de_city_idx, mv_de_drink_idx, mv_de_name_idx, mv_de_section_idx, mv_de_state_idx, mv_de_vkey_idx (single columns city,
drink_name, item_name, section, state_code, venue_key); mv_mdvp_key UNIQUE (venue_key); mv_mdvp_state; mv_mdvp_type.

Asks for round 3: approve the real swap (`set statement_timeout='3s'; select public.phg_explorer_swap_next();`), then one
timed `CALL public.refresh_explorer_v2()` as a one-off cron job, then cron 8 switched per the table above, with the watchdog.

## Safety Reviewer - round 3 (2026-09-29, commits 420a909 + 24765c9, migration 20260929170000 applied live)

**Evidence.** Still no live DB access for the reviewer: no Supabase tools in this session, and the local throwaway
cluster could not be started this round. So the live facts are the lead's (round 3 submission above). This round
checked the applied migration file against the draft (git diff 2d53250..420a909), the repo callers (index.html,
supabase/functions/*, the earlier grant migrations) and documented PostgreSQL 17 semantics. Nothing was changed
live.

### Round-2 findings: status
| Item | Status | Evidence |
|---|---|---|
| R2-B1 unqualified index names | fixed | The helpers are verbatim from the round-2 test. The live rehearsal returned `REHEARSAL OK`. It checked the OIDs, anon/authenticated SELECT, `_old` closed, the unique index, and the OIDs restored after swap_back. |
| R2-B2 gate facts | fixed | (a) The cron 8 baseline is recorded verbatim. (b) The rehearsal output and the post-state are recorded (0 log rows, only `*_next`, live OIDs unchanged). (c) The live relacl, owner and index names are recorded. The longest old index name is 21 characters. |
| S-R2-1 SELECT-only ACL copy | fixed | copy_select is verbatim. It also carries `phg_menu_designer=r` and `phg_harmony_reader=r` on mv_drink_explorer and mv_menu_dev_venue_profile. Both were table-level grants (the harmony `denied_columns` path is not used for these two), so relacl covers them. |
| S-R2-2 statement_timeout | fixed in code; the record is still missing | The SET clauses are gone. `pg_roles.rolconfig` for postgres and `pg_db_role_setting` are still not recorded (S-R3-3). |
| S-R2-3 session lock | fixed for cron; new edge cases | See S-R3-1 and S-R3-2. |
| S-R2-4 pg_proc dependents | fixed | The `classid = 'pg_proc'` branch has been added. |
| S-R2-5 old refresh_explorer() EXECUTE | **not done** | The submission does not mention it. Carried over as S-R3-4. |
| S-R2-6 timing / EXPLAIN | open (planned) | The plan is to time a one-off `CALL` before cron 8 is changed. That is the right gate. No numbers yet. |
| S-R2-7 classify_item SETOF | fixed | `LATERAL (... LIMIT 1)`. See "View change and the _next builds" below. |
| S-R2-8 parity / missing venues | half done | Index parity is confirmed from (c) against Part B: every old column set has an equivalent `_next` index (mv_dash_sections_idx (state_code, section) is covered by `_next_uk` on the same columns). Still missing: the count of old venues that are absent from `_next`, by reason. This is not safety-relevant, because every state grows. |

### Specific questions from the lead
**1. Session advisory lock when a refresh fails partway.**
- Under pg_cron, the lock is safe. In libpq mode, each run opens its own connection and closes it when the command
  ends, whether it succeeded or failed. So a failed or cancelled (watchdog) `CALL` releases the lock when the run
  ends. The MVs committed before the failure stay fresh, and the next run starts again from mv_drink_explorer.
- In any other session, the lock can leak. PostgreSQL documents that a session-level advisory lock taken inside a
  transaction that is later rolled back is still held after the rollback. It stays until an explicit unlock or until
  the backend exits. That happens if someone runs the `CALL` from the SQL editor, the MCP `execute_sql`, or through
  the pooler (Supavisor transaction mode reuses server connections). Any wrapping transaction makes the first COMMIT
  fail with `invalid transaction termination`, and the lock survives on that connection.
- The consequences of a leak:
  (a) Every later cron run hits `raise notice 'explorer busy; skipped'; return;` and pg_cron records it as
  **succeeded**. The explorer goes stale silently, which is the original PHG-051 P0 again, with no failed runs to
  show it.
  (b) `phg_explorer_swap_back()` and `phg_explorer_build_next()` fail on their try-lock, which blocks the rollback
  path until the holder is found. That is S-R3-1 and S-R3-2.

**2. ACL narrowing (anon and authenticated go from arwdDxtm to SELECT only). This is safe, and it is an improvement.**
- a/w/d/D (INSERT/UPDATE/DELETE/TRUNCATE): PostgreSQL rejects these on a materialized view whatever the privileges
  ("cannot change materialized view").
- x (REFERENCES): a foreign key cannot reference an MV.
- t (TRIGGER): an MV cannot have triggers.
- m (PG17 MAINTAIN): this is the only real loss. It covers REFRESH, VACUUM, ANALYZE, LOCK TABLE, CLUSTER and
  REINDEX. anon and authenticated can only use it through a SECURITY INVOKER function exposed over /rpc.
- The repo has no such caller:
  - index.html only does GETs on mv_drink_explorer and mv_menu_dev_venue_profile.
  - phg-harmony-data and phg-speech-transcribe only do `.select()` on mv_*. They use the service_role client.
    service_role keeps its default full grant on the `_next` copies (round-2 fact: `{postgres, service_role}`), so
    nothing changes for it.
  - The only rpc refreshes in edge functions are refresh_state_stats, refresh_menu_staging_quality and
    refresh_visual_page_placeholders. None of them is an explorer MV refresh (job 5 and the stats functions were
    kept out of refresh_explorer_v2 in round 2).
  - phg_designer_query and phg_harmony_q run as phg_menu_designer and phg_harmony_reader. Those roles are SELECT-only
    and are carried over.
- One unchecked exception: if the old `refresh_explorer()` is SECURITY INVOKER and executable by anon, today anon
  can trigger a non-concurrent refresh through MAINTAIN. After the swap that call fails, which is better. If it is
  SECURITY DEFINER, anon can still call it after the swap, and it takes an ACCESS EXCLUSIVE lock on the v2 MVs.
  Either way, S-R3-4 closes it.

**3. Does the view change (classify_item LIMIT 1) invalidate the existing _next builds? No.**
- mv_drink_explorer_next selects from v_public_drink_explorer_v2 by OID. `create or replace view` keeps the OID and
  had to keep the same output columns, or the applied migration would have failed. The stored rows are not touched.
- The builds already hold the result that LIMIT 1 would give. mv_de_next_uk (UNIQUE staging_id) was built
  successfully. So at build time no item matched more than one classify_item row: an item matching n > 1 rows would
  have produced n rows with the same staging_id. With at most one row per item, LIMIT 1 changes nothing.
- The first CONCURRENTLY refresh uses the new definition, so from then on a fan-out cannot break the unique index.
- One residual point: a LIMIT 1 with no ORDER BY picks whichever row the function returns first. If classify_item
  ever returns two rows, family and section could flip between refreshes (row churn only, no failure). This is a
  minor item.

### Scores
| Area | Score | Main evidence |
|---|---|---|
| Data preservation | 88 | Nothing is dropped. `*_old` is kept, the swap is one transaction, and the log stores the OID and ACL of every live, `_old` and `_next` name. The drop-`_old` statement is written without CASCADE. The old relacl is on record. |
| Correctness | 85 | The swap and swap_back are proven live by the rehearsal. The ACL copy is correct, including the two app roles. LIMIT 1 removes the staging_id fan-out, and the builds are unaffected. Minus: a busy skip returns success, and LIMIT 1 has no ORDER BY. |
| Concurrency | 84 | lock_timeout 300 ms held in the live rehearsal. The session lock spans the whole CALL under cron and conflicts with the build and swap xact try-locks. The refresh takes ExclusiveLock only, so readers are not blocked. Minus: a lock leak in non-cron sessions, plus the silent skip (S-R3-1). |
| Performance | 72 | Index parity is confirmed. No CONCURRENTLY timing and no EXPLAIN yet. The snapshot and xmin hold per run are unknown. This is correctly gated by the timed one-off run before cron 8 changes. |
| Security | 86 | The DEFINER helpers set search_path, and EXECUTE is revoked from anon, authenticated and service_role. swap_log has RLS and service_role SELECT only. The ACL narrowing removes MAINTAIN from anon and authenticated, and no caller needs it. Open: S-R3-4 (refresh_explorer EXECUTE). |
| Reversibility | 84 | swap and swap_back are rehearsed live with OID restoration. The cron 8 baseline and the per-state runbook are written. swap_back refuses to run after a rebuild. Minus: a leaked session lock blocks swap_back, and the runbook has no step to find and clear it (S-R3-2). |
| **Round score** | **83** | |

### Blockers
None for the swap itself, or for the one-off timed CALL.

### Should fix (S-R3-1 to S-R3-4 gate re-enabling cron 8; S-R3-4 should be done before the swap)
- **S-R3-1 Make a busy skip visible.** In refresh_explorer_v2, replace
  `raise notice 'explorer busy; skipped'; return;` with
  `raise exception 'explorer busy (phg_explorer lock held); skipped';`.
  A true overlap then appears as a failed cron run, which is harmless because nothing has changed yet, and a leaked
  lock shows up at once instead of silently stopping every refresh. Only ever run the CALL as a one-off pg_cron job,
  never from the SQL editor, the MCP or the pooler.
- **S-R3-2 Add a runbook step to find the lock holder.** Add it before the swap_back step, and to "explorer busy"
  triage (untested here, so check it on a read-only connection first):
  ```sql
  select l.pid, a.usename, a.application_name, a.backend_start, a.state, left(a.query, 80)
    from pg_locks l join pg_stat_activity a using (pid)
   where l.locktype = 'advisory' and l.objsubid = 1
     and l.objid::text::bigint   = (hashtext('phg_explorer')::bigint & 4294967295)
     and l.classid::text::bigint = ((hashtext('phg_explorer')::bigint >> 32) & 4294967295);
  ```
  Then run `select pg_terminate_backend(<pid>)` for the idle holder only.
- **S-R3-3 Record the real bound on the CALL.** Record `select rolname, rolconfig from pg_roles where rolname = 'postgres'`
  and `select * from pg_db_role_setting`. A pg_cron command cannot `SET statement_timeout` in front of the CALL (an
  implicit transaction block breaks the COMMIT), so the role or database setting is the only statement bound. The
  watchdog is the other bound. If postgres has a short role timeout, the timed run fails at mv_drink_explorer.
- **S-R3-4 (carried from S-R2-5) Close the old refresh_explorer() to the app roles.** Before the swap, run
  `select has_function_privilege('anon','public.refresh_explorer()','execute'), has_function_privilege('authenticated','public.refresh_explorer()','execute'), prosecdef from pg_proc where proname='refresh_explorer'`.
  If either is true, run `revoke execute on function public.refresh_explorer() from public, anon, authenticated;`.
  After the swap, this function refreshes the v2 MVs non-concurrently by name.
- **Before the timed run (cheap):** confirm that `pg_class.relowner` is postgres for all six `*_next`. The cron job
  runs as postgres, and REFRESH needs the owner or MAINTAIN. The rehearsal did not check the owner.

### Minor
- Add a deterministic order to the classify_item pick, either an ORDER BY inside classify_item or
  `ORDER BY ci.family, ci.subfamily` in the lateral, so a future multi-match cannot flip family or section between
  refreshes.
- S-R2-8 remainder: record the count of old venues missing from `_next`, by reason.
- Carried over: swap_back leaves SELECT for phg_menu_designer and phg_harmony_reader on the demoted `*_next`. This is
  harmless because the data is the same kind.
- Record the timed CALL's per-MV notices and `n_dead_tup` on accounts and staging_menu_extract before and after
  (S-R2-6), and pick the cadence from those numbers.

### Verdict
**pass (83).** Approve the real swap:
`set statement_timeout='3s'; select public.phg_explorer_swap_next();`
Run it at a quiet time, and retry on 55P03 or 57014. Do S-R3-4 first. After the swap, run
`NOTIFY`-dependent checks: anon has SELECT on all six live names, `*_old` is closed, and the swap_log row is
present.
Then run one timed `CALL public.refresh_explorer_v2()` as a one-off pg_cron job, unscheduled by hand once it has
started.
Re-enable cron 8 (`command := 'CALL public.refresh_explorer_v2()'`, with the watchdog) only after S-R3-1, S-R3-2 and
S-R3-3 are done and the timing is recorded here.
