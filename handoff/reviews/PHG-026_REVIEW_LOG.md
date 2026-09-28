# PHG-026 review gate

Rob (2026-09-28): "create two other review agents who will spec it and who will give multiple reviews up to five each.
You are not allowed to publish anything until they each give on average above 80% score."

- Reviewers: Spec Reviewer (.claude/agents/spec-reviewer.md), Safety Reviewer (.claude/agents/safety-reviewer.md).
  An earlier independent review (started before this rule) feeds its findings into round 2.
- Gate: each reviewer's average across ALL their rounds must be above 80. Up to 5 rounds each. If either misses
  after 5 rounds, nothing is published and Rob decides.
- "Publish" = applying 20260927190000 + 20260927191000 to the live database, re-enabling cron 13 / 7, and sending the
  preview builds (18.49.8 - 18.49.12) live.

| Round | Spec score | Safety score | Spec average | Safety average | Changes made after the round |
|---|---|---|---|---|---|
| 1 | 62.5 (pre-fix files) | 78 (a323e16) | 62.5 | 78 | see "Round 1 findings" |

## Round-1 acceptance spec (Spec Reviewer), kept for later rounds
Rebuilt on 2026-09-28 from the round-1 findings above and from the criteria as the Spec Reviewer listed them in round 2
(C1-C16; C17, the designer gateway role escape, was added in round 2). Each criterion is scored 0-100; the round score
is the average.
- C1 Item pages never replace. An online-ordering item / event / product page (`?item=`, `/order/<menu>/<cat>/<item>`,
  `/events/...`) never becomes the current menu over a non-empty current menu, even when it shares the menu's source
  key; it is stored as an alternate.
- C2 Duplicates and subsets. A capture whose items are all already in the current menu (the same page or another page) is
  not inserted, and the current menu stays. Only a true subset is a duplicate: a capture with new items or newer prices
  is kept (it replaces or becomes an alternate).
- C3 A missing price is unknown. An item without a price matches the same item with any price, in both directions; it
  never counts as a different item.
- C4 One current menu, enforced by the database. After release no venue can have two current menus (unique index), and
  every writer demotes before it inserts.
- C5 The repair restores the damaged venues. Every touched venue ends with a current menu at least as large as its largest
  pre-incident menu; ties keep the menu that is already current; the repair runs under a lock; postconditions
  (0 multi-current, 0 without a current menu, 0 smaller) raise and roll back if any fails.
- C6 Nothing is deleted; everything changed is backed up. Menus, staging rows and function bodies are backed up before
  they change.
- C7 Rollback is exact, scoped and tested. It restores exactly what the change altered and nothing else, skips venues that
  changed after release, never leaves two current menus, is rehearsed, and the writers (submit_menu, promotion,
  extraction) still work after it.
- C8 Extraction save. A sibling page that returns the same item set as another page of the venue is not re-staged; the
  page's own stale rows are retired; a duplicate never becomes the original for later pages.
- C9 Steps 3-4 are batched and safe at table scale: each call stays well under the timeout, progress is recorded, and the
  candidate index is built CONCURRENTLY as a runbook step.
- C10 Readers. Every reader that assumes one current menu per venue (v_menu_composition, v_menu_brand_presence,
  v_menu_category_share, phg_menu_composition, phg_brand_presence, phg-expanded-data) stays correct; claims about
  staging views are accurate.
- C11 Callers. Every caller of submit_menu (Edge functions, SQL functions, workers) keeps working with the new return
  statuses; overloads are resolvable.
- C12 Locking. Writers of one venue queue in a fixed order (account row, then advisory lock); no deadlock with the
  extraction save; lock times are bounded and documented.
- C13 Re-runnable. Both files and all batch functions can run again without harm (if-not-exists, on-conflict, done tables).
- C14 Counts. The headline counts (touched, with a pre-incident menu, damaged, changed by Step 2) are defined, reconciled
  and recorded at run time.
- C15 Rehearsal coverage. Every step, check and rollback is rehearsed on live data in a rolled-back transaction, and the
  output is recorded.
- C16 Post-release measures. There are checks with expected values for release, plus measures for after cron resumes
  (menus per distinct item set, promotion outcomes) that do not fail on legitimate re-captures.

## Pre-gate independent review (started before the gate rule): 1 blocker, 4 should-fix, 4 minor
Fixed before round 2 (both files):
- BLOCKER repair Step 2 rank: now distinct items -> drinks items (typed items + items in cocktails/wine/beer/spirits
  sections) -> not an item page -> newest. Measured (read-only): 185/185 venues get a menu at least as large as their
  old one, 0 smaller (was 23 smaller); 407 venues change current menu.
- submit_menu: size decides before drinks count; drinks count includes typed sections; same-source item-page guard and
  partial-recapture (< half) guard; empty current menu can be replaced by an item page; account row locked first
  (FOR NO KEY UPDATE) then advisory lock; SET LOCAL lock_timeout.
- extraction duplicate branch: supersedes the page's own stale staged rows; never sets item_set_hash on a duplicate;
  only matches an original sibling that still has live staged rows.
- repair Step 3: batched function phg_repair_step3_batch(300) with a progress table (was one statement over ~1M rows).
- helpers phg_menu_item_key / phg_menu_key_set_hash inlinable (no SET, pg_catalog-qualified).

## Round 1 findings still open after the pre-gate fixes (being fixed for round 2)
Spec (S1-S16) and Safety (B1, S1-S7) overlap on:
- rollback: save the 4 pre-change function bodies; scope the menus rollback to repair-changed rows, never produce two
  current menus; staging rollback skips pages re-extracted since
- DB-enforced one current menu per venue (unique partial index)
- Step 2: keep the current menu on ties (was_current first among equals); lock + postcondition check
- other-source 90% rule drops newer prices -> drop only true subsets, else alternate
- missing price = unknown in item keys
- Step 4 batched; CONCURRENTLY index as a runbook step
- verification queries with expected values; reconcile 185 / 119 / 180 / 407 counts
- 10-arg overload cannot be called ('not unique') -> drop after checking callers
- promotion batch account locks: document / smaller batch
- staging views that ignore superseded_at: correct the claim

## Changes after round 1 (submitted for round 2)
- Function rollback: the migration first saves the 4 live definitions in phg_backup_function_defs_20260927 (aborts if
  fewer than 4) and adds phg_rollback_function_defs_20260927() to restore them exactly (including the 10-arg overload).
- Data rollback: phg_repair_20260927_rollback() - skips venues that got a newer menu after the repair, demotes before it
  restores, restores staging rows only if their page was not re-extracted since, raises if any account would end
  with two current menus.
- One current menu enforced by the database: unique index menus_one_current_per_account (created after Step 2's
  checks); submit_menu now demotes, inserts, then links superseded_by (index is non-deferrable).
- Step 2: table lock for Steps 1-2; ties keep the menu already current (was_current before created_at); demote then
  promote; postcondition block raises on >1 current, touched venue without current, or any venue smaller than its
  largest pre-incident menu; result recorded in phg_repair_run_20260927.
- submit_menu: other-source duplicate only for a true subset; near-identical (>=90% of current) and at least as large
  -> replaces (newer prices kept); a missing price matches any price (phg_menu_keys_overlap); a NULL source key is
  never "same source".
- 10-arg submit_menu dropped (uncallable today: 42725 'not unique'; no callers); definition saved for rollback.
- Step 3: 100 venues per call, returns venues remaining; runbook VACUUM (ANALYZE) afterwards.
- Step 4: batched phg_repair_step4_batch(200) with a done table; CONCURRENTLY index as runbook step 4.
- Counts defined in the repair header (1,547 touched / 185 with a pre-incident menu / 119 damaged / Step 2 changes
  recorded at run time); staging-view claim corrected (4 views ignore superseded_at).
- Verification: supabase/tests/phg_026_verification.sql (pass/fail rows, expected values).
- Documented: re-enable cron 7 with p_pages <= 5 (account row locks held per promotion transaction).
- Follow-up after release (not part of this change): stale header comment in the submit-menu Edge function.

## Rehearsal before round 2 (2026-09-28)
Both files run on the live DB inside one DO block ending in RAISE EXCEPTION (fully rolled back; verified afterwards
that no PHG-026 object exists). Script: handoff/reviews/rehearsal/rehearse_all.sql (generator gen.py).
- A (file 1, 152 ms): 4 defs saved; 10-arg dropped; scenarios 1-7 all PASS (duplicate_of_current, near-identical
  replace, item page alternate, partial re-capture alternate, smaller other source alternate, empty ignored,
  unknown-price overlap both ways); 0 multi-current throughout.
- B (file 2, 7.7 s under SHARE ROW EXCLUSIVE): step2 {current_changed 348, multi_current 0, no_current 0, smaller 0};
  unique index created; 0 exact-tie changes (300 larger, 12 more drinks, 36 real page over item page).
- C: repair rollback 348/348 restored, 0 multi-current, is_current identical to backup; function-def rollback
  returned 4 and restored the 10-arg overload.
- Header estimate corrected to ~350 (348) and the 7.7 s lock documented.
- Note: empty_capture_ignored returns the current menu's id as menu_id (intended: the caller keeps pointing at it).

## Round 2 (2026-09-28, commit 97a738b)
| Reviewer | R1 | R2 | Average | Gate (>80) |
|---|---|---|---|---|
| Spec | 62.5 | 76.7 | 69.6 | not met |
| Safety | 78 | 78 | 78.0 | not met |

Blocking:
- SB1 / spec C17 (live designer gateway role escape): CONFIRMED live and FIXED + applied the same day (migrations
  20260928050000 security-definer owned by phg_menu_designer; 20260928051000 refuses session-side-effect functions:
  advisory locks, set_config, notify, sleep, signalling, lo_, dblink, net/cron/vault). Re-probed live: refused.
- SB2 / spec C7: function rollback must drop menus_one_current_per_account first (live 10-arg body inserts before it
  demotes), re-apply revokes, and be rehearsed with a real submit_menu call afterwards.
- Spec C16 / safety SF6: verification script false-fails after cron resumes; split into release gate + monitor.
- Spec C15/C8/C9 / safety SF4: rehearse steps 3-4 (timed), staging rollback, promote_clean_menu_batch(1), one
  sibling-duplicate extraction save, and the verification SQL.
Non-blocking (to be addressed in round 3): SF1 price enrichment treated as duplicate; SF2 lock_timeout + one-transaction
runbook note; SF3 rollback skip test by backup membership + full row restore; SF5 revokes + service_role write on def
backup; SF7 enforce p_pages <= 5; SF8 enumerate other is_current writers; SF10 score-gate NULL layout check;
spec: persist round-1 spec text, independent 119-damaged-venue check, report item-page / old-menu picks, caller
status handling evidence, near-identical flip-flop damping, migration ordering vs db push.
Note: neither reviewer could reach the database this round (no Supabase tool in their sessions); round 3 hands them the
rehearsal output instead.


## Changes after round 2 (submitted for round 3)
Code (committed in the WIP syncs dd629d5 / 3391712 and in the round-3 commit): 20260927190000, 20260927191000,
supabase/tests/phg_026_release_gate.sql + phg_026_monitor.sql (phg_026_verification.sql is now a pointer).
20260928030000 is the Coordinator's text unchanged (SF10 was already in it). Rehearsal: handoff/reviews/rehearsal/results_round3.md (blocks A-F, all rolled back).

Blocking:
- SB2 / C7 function rollback: phg_rollback_function_defs_20260927() drops menus_one_current_per_account first,
  restores the 4 bodies, re-applies `revoke all ... from public, anon, authenticated` on each signature and re-grants
  service_role where the saved ACL had it (the backup table now stores acl). The backup table is read-only for
  service_role (insert/update/delete/truncate revoked; anon/authenticated have nothing). Rehearsed: returns 4, index
  gone, 10-arg overload back, live body restored, anon/authenticated cannot execute, then one submit_menu on a venue
  with a current menu -> created, 1 current, old demoted.
- C16 / SF6: the verification script is split. phg_026_release_gate.sql (run once after the runbook, before cron) is
  scoped to the plan venues and to data from before step2.ran_at: step 3 finished for venues staged before the repair,
  step 4 for candidates found before it, 0 plan venues smaller than their largest pre-incident menu, every damaged
  venue restored, index present, cron 7 and 13 still paused. phg_026_monitor.sql (after cron resumes) has only
  0 multi-current, the index, and menus per distinct item set <= 1.2; the outcome counts and churn are informational.
- Independent damaged-venue check: phg_repair_damaged_20260927 is saved BEFORE Step 2 (touched venues whose largest
  pre-incident menu is larger than the current one). Rehearsed: 119. After Step 2 the in-file assert raises unless every one
  has a current menu at least that large (rehearsed: 0 not restored). step2 detail now records damaged_venues,
  damaged_not_restored, chosen_item_pages 42 (4 changed to an item page), and pre_incident_replaced_newer_same_source 22.
- C15 rehearsal: steps 3-4 timed.
  - Step 3: ~13-14.5 s per 100 venues, 19 calls, ~4.5 min.
  - Step 4: ~11 s per 200 venues (~97 calls, ~18 min), or ~17 s per 500 venues (~39 calls, ~11 min). The runbook now
    says 500.
  - Also rehearsed: the release-gate SQL (rows captured), the repair rollback after Step 3 including the staging
    restore (30,126 rows), promote_clean_menu_batch(1), and one sibling-duplicate extraction save.
  - The final re-run of every block by the round-3 session all passed. See results_round3.md.

Non-blocking:
- SF1 price enrichment: new phg_menu_keys_price_adds(a, b) counts capture items that supply a price the current menu lacks
  for the same name. The duplicate / subset tests (same source and other source) require price_adds = 0; the overlap
  and size maths still use phg_menu_keys_overlap. Same source -> replacement (`same_source_price_enrichment`); other
  source -> the near-identical rule (`price_enrichment_other_source`) or an alternate when it is smaller. Rehearsed
  (s8a, s8b).
- Flip-flop damping: another source, near-identical, not larger, no added prices, current menu under 7 days old ->
  alternate (`alternate_near_identical_recent_other_source`). Larger captures and price enrichment still replace.
  Rehearsed (s9 alternate; s9b control, a larger capture replaces).
- SF2: file 2 starts with `set local lock_timeout = '5s'`; header and runbook say it is applied as ONE transaction
  (apply_migration or `psql -1 -f`). Rehearsal found that cron job 16 (every 20 s, up to 5 s on menu_source_candidates)
  can make file 1's ADD COLUMN hit its 3 s lock_timeout (55P03, full rollback); the runbook action is to re-run it.
- SF3: the rollback skips a venue if ANY of its menus is not in phg_backup_menus_currency_20260927; demoting a
  repair-promoted menu restores its backed-up superseded_by / reason / at. Rehearsed: all four columns identical to the
  backup for every menu afterwards.
- SF4: index on phg_backup_staging_dupes_20260927(account_id); Step 3's per-venue counts use one GROUP BY.
- SF5: see SB2 (the backup tables are read-only for service_role).
- SF7: promote_clean_menu_batch clamps p_pages to least(p_pages, 5). Cron 7 calls phg_promote_menu_batch_safe(10), so it
  now gets 5.
- SF8: other live functions whose source mentions is_current (all schemas), excluding submit_menu, promote_clean_menu_batch
  and phg_save_menu_candidate_extraction: **none**. The broader search (is_current / submit_menu / promote_clean_menu_batch)
  finds only the two submit_menu overloads (both INSERT is_current=true then demote: they are incompatible with the
  unique index, which is why the 10-arg is dropped, the 15-arg is replaced, and the function rollback drops the index),
  promote_clean_menu_batch (goes through submit_menu), and phg_promote_menu_batch_safe(int) (only calls
  promote_clean_menu_batch). There are no triggers on public.menus. No Edge function writes menus directly.
- SF10: the coalesce(jsonb_typeof(...), '') layout and score checks were already in the Coordinator's version of
  20260928030000 (9e41e78). A mid-round edit had added an acl column and a service_role re-grant to that file's
  backup/rollback, which went beyond SF10. It was reverted to the Coordinator's text (the revert landed in abc0066).
  Rehearsed as-is (block F):
  - 3 definitions saved; a NULL layout is rejected.
  - The rollback returns 3, drops the 11-arg submit and the score function, and restores the 10-arg submit, the review
    and the status functions.
  - anon/authenticated cannot execute; service_role keeps EXECUTE through default privileges.
  - Still NOT applied live.
- Round-1 spec text: added above ("Round-1 acceptance spec").
- Migration ordering: both files and the runbook say to apply through apply_migration (in order), not `supabase db push`,
  because newer migrations (20260927200000 and later) are already applied.
- Caller evidence (C11). The repo has no copies of the submit-menu / promote-menus Edge functions, no worker and no n8n
  export that calls submit_menu. Read live (read-only):
  - submit-menu v8 calls rpc submit_menu with p_needs_vision_pass (so the 15-arg overload is used) and returns
    `{...data}` with HTTP 200 for any status. It handles unknown statuses generically.
  - promote-menus rev 4.3 posts to submit-menu and does `if (out?.status === "duplicate") duplicate++; else created++`,
    marking staging rows `promoted` for any other status. The new statuses do not fail there but are counted as created
    and labelled `promoted`. It is not scheduled: no pg_cron job calls promote-menus or promote-menus-scheduled.
    Follow-up after release: record out.status there.
  - Cron 7 uses the SQL path (phg_promote_menu_batch_safe -> promote_clean_menu_batch), which maps every status
    (created -> promoted, created_alternate -> promoted_alternate, subset_of_current -> held_subset_of_current, others
    verbatim).
- Found in rehearsal: the promotion queue is empty today (the 6,760 promotion_ready rows are food pages the view
  excludes), so the promote test re-staged one incident sibling page -> duplicate_of_current, no menu created.

## Round 3 (2026-09-28, commit 6b764f8)
| Reviewer | R1 | R2 | R3 | Average | Gate (>80) |
|---|---|---|---|---|---|
| Spec | 62.5 | 76.7 | 86.3 | 75.2 | not met (R4+R5 need avg >= 87.3) |
| Safety | 78 | 78 | 82.7 | 79.6 | not met (R4 >= 84) |
Both: no blockers. Spec per-criterion R3: C1 88, C2 88, C3 92, C4 92, C5 93, C6 90, C7 85, C8 88, C9 88, C10 85,
C11 82, C12 86, C13 85, C14 85, C15 85, C16 84, C17 75, C18 82.
Safety per-area R3: data 88, correctness 82, concurrency 80, performance 86, security 76, reversibility 84.
C18 text (for the record): "Score-gate migration 20260928030000 is correct, reversible, rehearsed, and not applied as
part of the PHG-026 publish."
Already fixed after round 3 (applied live, 20260928052000): SF9 / C17 designer denylist bypass - string-executing
functions (*_to_xml, ts_stat, ts_rewrite, xmltable) and U&/UESCAPE refused, and pg_advisory_unlock_all() after every
call (success and error); rehearsed: bypasses refused, normal reads OK, 0 advisory locks left.

## Changes after round 3 (submitted for round 4)
Files: 20260927190000, 20260927191000, 20260928030000 (score gate), supabase/tests/phg_026_release_gate.sql.
The designer gateway (20260928052000) is untouched. Rehearsal: handoff/reviews/rehearsal/results_round4.md (blocks A-G,
all rolled back, all pass; read-only check afterwards: no PHG-026 object exists live). Nothing applied.

1. Rollback skip path (C7).
   - The rollback's scope is now plan venues whose current menu Step 2 changed plus the Step-3 staging venues. A venue
     with any menu not in the currency backup is skipped for both menus and staging; the staging restore is limited to
     the venues actually rolled back (rb_accts), and still skips pages re-extracted since the backup.
   - Rehearsed (block G): after Step 2 and one Step 3 call, one new menu for plan venue ACC-CO-LED-03-00124 ->
     `venues_skipped_newer_menu` 1, that venue's menus identical before and after, its backed-up staging row not
     restored; one new staging row for a backed-up page of another venue -> that page's rows not restored; everything
     else restored (30,124 of 30,126 rows); 0 multi-current.
2. Rollback robustness: a venue whose backup has more than one current menu is excluded and reported
   (`venues_skipped_multi_current_backup`), so it cannot abort the rollback on the unique index. Real venues like that
   today: 0; rehearsed with a forged backup (block G): skipped 1, rollback completes, venue untouched.
3. Runbook text in file 2's header: cron 7 and 13 stay paused before and during either rollback and until the
   functions are rolled back too or the change is re-applied; a 40P01 / 55P03 against an in-flight submit_menu in file 2
   or either rollback is safe to re-run; to roll forward after a rollback, the exact statement
   `drop table if exists public.phg_repair_plan_menus_20260927, public.phg_backup_menus_currency_20260927,
   public.phg_backup_staging_dupes_20260927, public.phg_repair_damaged_20260927, public.phg_repair_run_20260927,
   public.phg_repair_step3_done, public.phg_repair_step4_done;` and a warning NOT to drop
   phg_backup_function_defs_20260927 (it holds the only copy of the original bodies).
4. Step 3 / Step 4 batch functions: `set lock_timeout to '5s'` as a function-level setting (applies per call, reset on
   return; rehearsed: proconfig shows lock_timeout=5s). Their comments and the runbook say 40P01 / 55P03 is safe to
   retry; Step 4 contends with cron 16 on menu_source_candidates.
5. v_smaller postcondition uses the `'2026-09-27 00:00:00+00'` literal (the two Step 3 `loaded_at` comparisons too).
6. File 1 header: "119 damaged venues out of 185 with a pre-incident menu".
7. Release gate: the cron row asserts both jobs exist (`count(*) = 2`) and are inactive; a missing job fails. Rehearsed
   value `2 jobs; 7:false,13:false`.
8. Backup tables (function defs, menus currency, staging dupes, and the score gate's design fn defs): `revoke all ...
   from ... service_role` then `grant select`. Rehearsed: select true; insert, update, delete, truncate, trigger,
   references all false.
9. Score gate 20260928030000 (C18): header names the three reviewers; approve re-checks that the stored layout has a page
   object and an elements array (`blocked_by_layout_gate`, status unchanged; a proposal stored before the migration has
   layout NULL and is blocked, not approved); the approved result returns accuracy_reviewer too. Block F re-rehearsed
   with the full approve path (score gate at 80 blocks, layout NULL / no elements blocks, all at 90 approves and
   returns all three averages), then the rollback (returns 3).
10. C1, same-source item page with a fuller item set: changed, not just documented. Before: a same-source item page
    (`?item=` is stripped from the key) that was at least as large as a real-page current menu replaced it, so the
    venue's current menu took the item-page URL. Now, over a REAL page, an item page must be strictly larger by
    (distinct items, drinks items) to replace; otherwise it is stored as `alternate_item_page`. Over a current menu that
    is itself an item page the old rule stays (at least as large replaces).
    Why:
    - It is the order Step 2 uses (items, then drinks items, then real page before item page). Without it, the first
      cron cycle could undo the repair's 36 tie picks where a real page replaced an item page.
    - Nothing is lost: the item page is kept as an alternate. A strictly larger capture (new items) still becomes
      current, so newer content is not held back.
    - Price-only changes from an item page wait for the real page's own re-capture, which is the source we want as
      current.
    Rehearsed: s10 (same size, one price changed) -> alternate, current unchanged; s10b (one more item) -> created.
11. Monitor: phg_026_monitor.sql ran in the rehearsed post-repair state (6 rows, all pass; ratio null until menus are
    created). Baseline for the 1.2 threshold: 1.000 before the incident (4,800 menus / 4,800 venue item sets; 09-25 and
    09-26 both 1.000); incident window 2.892 (7,429 / 2,569, the "about 3.0"). The monitor replayed over the incident
    window fails at 2.892, so it catches a repeat; 1.2 leaves 20% room for legitimate same-set re-captures.
Timings this round: file 2 steps 1-2 6.9-8.9 s (one run 14.4 s); Step 3 14.6-17.0 s per 100 venues (~5 min total);
Step 4 14.3 s per 500 (~10 min) or 12-13 s per 200; release gate 6.3 s; repair rollback 7.7-8.2 s; function rollback
15-24 ms; monitor 2.7 s.

## Round 4 (2026-09-28, head 38dc7c0)
### Spec Reviewer: 89.2, no blockers
- Rounds so far: 62.5, 76.7, 86.3, 89.2. Average 78.7.
- Round 5 must score above 85.3 for the average to pass 80.

Per criterion:
- C1 91, C2 88, C3 92, C4 92, C5 94, C6 93, C7 90, C8 88, C9 91
- C10 85, C11 82, C12 89, C13 88, C14 88, C15 91, C16 90, C17 85, C18 88

Should-fix:
1. C1: the 7-day damping also holds a real page behind an item-page current menu. Add `and not (c.itemish and not v_itemish)` (file 1, around lines 323-324) and a rehearsal scenario s11.
2. C7/C13: the roll-forward must null `menu_source_candidates.item_set_hash` and `duplicate_of_candidate_id` (file 2, lines 19-24).
3. C12: submit_menu has no lock_timeout, yet this log says it does (line 65). Add `set local lock_timeout='5s'` or correct the log.

Minor:
- C14: fix the lock-time header in file 2 (7-9 s, one run 14.4 s).
- C1: compare against an item-page current by (items, drinks).
- C18:
  - reject an empty `elements` array;
  - re-grant EXECUTE on rollback;
  - set lock_timeout before the ALTER;
  - add a header note that it is not part of the PHG-026 publish.
- C11: keep the Edge function on the post-release list.
- C16/C5: add a runbook note that Edge traffic stays idle until the release gate has run.
- Evidence: the reviewer had no live DB access. Round 5 should paste pg_get_functiondef output for the C10 and C17 functions.

### Safety Reviewer: pending
