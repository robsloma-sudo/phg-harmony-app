# PHG-026 round-3 rehearsal results (2026-09-28)

Every block ran on the live database (project lqjtwabzmgjcufftuqvu) inside one `DO` block that ends in
`RAISE EXCEPTION`, so nothing was kept. Each block re-runs the setup it needs, because an MCP call times out at 60 s.
No `apply_migration`, no cron change. Generator: `gen.py`. SQL: `rehearse_round3.sql` (all blocks) and
`rehearse_round3_<A..F>.sql` (one per block, exactly as generated).

Afterwards, read-only checks confirmed that nothing exists live: phg_backup_function_defs_20260927,
phg_repair_run_20260927, phg_repair_damaged_20260927, menus_one_current_per_account, menu_source_candidates_item_set_idx
and phg_backup_design_fn_defs_20260928 are all absent. menus.item_keys does not exist. The new functions do not
exist, and the live 10-arg submit_menu is still present. There are 0 rehearsal menus, cron 7 and 13 are still paused
(`active=false`), and the candidate_extraction lease and candidate 13965 are unchanged.

## Pass / fail

| # | Part | Block | Result | Time |
|---|---|---|---|---|
| 1 | File 1 (20260927190000) applied | A-F | PASS | 67-199 ms without lock waits; 2.5-3.1 s when it waited for cron job 16 (see note 1) |
| 2 | 4 function definitions (+ ACL) saved; service_role cannot INSERT into the backup (can SELECT) | A | PASS | - |
| 3 | promote_clean_menu_batch clamps to 5 pages (`least(5,`) | A | PASS | - |
| 4 | s1 exact copy from another URL -> `duplicate_of_current`, nothing inserted | A | PASS | scenarios total 386 ms |
| 5 | s2 3 prices changed, other URL, current menu aged 30 days -> replaces (`newer_near_identical_capture`) | A | PASS | |
| 6 | s9 flip-flop: original page again, current menu minutes old -> `created_alternate` (`alternate_near_identical_recent_other_source`), current unchanged | A | PASS | |
| 7 | s9b control: the original page with one more item -> replaces (`contained_in_larger_capture`) | A | PASS | |
| 8 | s3 `?item=` page on the current URL -> `alternate_item_page` | A | PASS | |
| 9 | s4 same URL, 10 of 33 items -> `alternate_partial_recapture` | A | PASS | |
| 10 | s5 2 food items, other URL -> `alternate_smaller_other_source` | A | PASS | |
| 11 | s6 zero items -> `empty_capture_ignored` | A | PASS | |
| 12 | s7 unknown price overlaps both ways (1/1), different prices 0; price-adds 1 / reverse 0 / current has both 0 | A | PASS | |
| 13 | s8a price enrichment, same source (current item has no price, capture has it) -> `created` (`same_source_price_enrichment`), not a duplicate | A | PASS | |
| 14 | s8b price enrichment, other source, current minutes old -> `created` (`price_enrichment_other_source`); damping does not hold back a price | A | PASS | |
| 15 | 0 multi-current accounts after every scenario | A | PASS | |
| 16 | File 2 steps 1-2 (under SHARE ROW EXCLUSIVE on menus) | B-E | PASS | 8.0-11.2 s |
| 17 | Step 2 postconditions: `{current_changed 348, multi_current 0, no_current 0, smaller 0}` | B, D | PASS | |
| 18 | Damaged venues saved before Step 2: 119; after Step 2 `damaged_not_restored` 0 (in-file assert + independent recount 0) | B, D | PASS | |
| 19 | Picks recorded: `chosen_item_pages` 42 (4 of them changed to an item page); `pre_incident_replaced_newer_same_source` 22 | B | recorded | |
| 20 | Changed-by-reason: more items 300, same items + more drinks 12, real page over item page 36, exact ties 0 | B | PASS | B checks 35 ms |
| 21 | Touched 1,547; with a pre-incident menu 185; 0 without a current menu; 0 NULL item_keys | B | PASS | |
| 22 | service_role cannot INSERT into the 3 backup tables | B | PASS | |
| 23 | Extraction save (candidate 13965 `/menu` saves the same 16 priced items as sibling 515238 `/happyhour`) -> `review`, `duplicate_of` 515238, 0 rows re-staged | B | PASS | 49 ms |
| 24 | promote_clean_menu_batch(1) on the queue as it is today | B | queue empty (0 candidates), nothing to promote | 5.1 s |
| 25 | promote_clean_menu_batch(1) on a re-staged incident sibling (`thesherpagrill.com/menu?item=rehearsal-new-sibling`, 13 beverage rows) -> `duplicate_of_current` 1, created 0, current unchanged, rows marked | E | PASS | 6.6 s |
| 26 | phg_repair_step3_batch(100) | C, D | runs | 12.8 / 13.0 / 11.5 / 12.4 s per call |
| 27 | phg_repair_step4_batch(200) | D, E | runs | 11.0 / 10.9 s per call |
| 28 | Candidate item-set index (plain CREATE INDEX here; CONCURRENTLY in the runbook) | D | PASS | 2.5 s |
| 29 | Release-gate SQL (rows below) | D | 9 PASS, 2 expected FAIL (steps 3-4 only partly run) | 6.2 s |
| 30 | phg_repair_20260927_rollback() after Step 3: 348 venues rolled back, 348 demoted, 348 restored, 0 skipped, 30,126 staging rows restored; currency identical to backup (all four columns) | D | PASS | 5.9 s |
| 31 | phg_rollback_function_defs_20260927(): returns 4, index dropped, 10-arg overload back, live body restored, anon/authenticated cannot execute, service_role can | E | PASS | 16 ms |
| 32 | Then ONE submit_menu on ACC-CO-LED-03-25486 (has a current menu) with the restored live body -> `created`; 1 current menu; old one demoted | D, E | PASS | 21-23 ms |
| 33 | SF10 score-gate migration: 3 definitions saved, NULL layout rejected (coalesce), rollback returns 3, drops the 11-arg submit + score function, restores the 10-arg submit/review/status, revokes OK, service_role keeps EXECUTE | F | PASS | 84 ms |

Totals by extrapolation (Step 3 and Step 4 are too long for a 60 s call, so they were timed per call and not run to the end):
- Step 3: 1,899 venues -> 19 calls x ~12.5 s = **~4 min**. The duplicate rows superseded were 30,126 for the first
  100 venues and 60,157 for the first 300.
- Step 4: 19,244 venues -> ~97 calls x ~11 s = **~18 min**. The per-call time is mostly the fixed "venues remaining"
  count. `phg_repair_step4_batch(500)` (the cap) should cut this to about 40 calls. That was not rehearsed.
- Release gate, repair rollback and function rollback each take seconds.

## Release gate rows (block D, after one Step 3 call and one Step 4 call)

| check | pass | value |
|---|---|---|
| 0 accounts with more than one current menu | true | 0 |
| one-current unique index exists | true | 1 |
| 0 plan venues without a current menu | true | 0 |
| 0 plan venues smaller than their largest pre-incident menu | true | 0 |
| every damaged venue (saved before Step 2) restored | true | 0 of 119 not restored |
| 4 pre-change function definitions saved | true | 4 |
| step 2 recorded (current_changed, damaged, picks) | true | {current_changed 348, damaged_venues 119, damaged_not_restored 0, chosen_item_pages 42, chosen_item_pages_changed 4, pre_incident_replaced_newer_same_source 22, smaller 0, no_current 0, multi_current 0} |
| step 3 finished for venues staged before the repair | false (expected: 1 of 19 calls run) | 1799 |
| step 4 finished for candidates found before the repair | false (expected: 1 of ~97 calls run) | 19044 |
| candidate item-set index exists | true | 1 |
| cron 7 and 13 still paused (re-enable only after this gate) | true | 7:false,13:false |

## Notes

1. **Lock wait on file 1 (runbook item).** The first attempt of block A failed with `55P03 canceling statement due to
   lock timeout` (file 1's own `lock_timeout = '3s'`) and rolled back cleanly. Active cron job 16
   (gtt-acquire-menu-visual-assets, every 20 s, up to 5 s per run) touches menu_source_candidates, and
   `ALTER TABLE ... ADD COLUMN` needs a brief exclusive lock. A retry succeeded, and later runs waited 2.5-3.1 s. The
   runbook: if file 1 or file 2 stops with 55P03, re-run it. Nothing was applied. Job 16 does not have to be paused.
2. **Block D's function-rollback row**: the rollback itself worked (the response of the following submit_menu has the live
   body's shape, without `reason` or `is_current`). One check read pg_proc in the same statement as the rollback call, so it
   saw the old snapshot. The check now runs in its own statement, and block E re-ran it: PASS.
3. **promote test**: the promotion queue (`v_menu_staging_promotion_candidates`) is empty today, and the 6,760
   `promotion_ready` rows are food pages the view excludes. Block E therefore re-staged one incident item page's rows
   under a new sibling `?item=` URL (a new content hash, the same items). The update also touched that page's 88
   non-beverage rows, which the view does not select (they stayed NULL). All of it was rolled back.
4. **Scenario 2 aging**: every live menu is under 7 days old (created 2026-09-25..27), so the rehearsal set the test
   venue's current menu back 30 days before s2. That exercises the near-identical replacement rather than the damping.
   Scenario 9 then exercises the damping.
5. The generated files for blocks B and D are the final versions. Block B's first run also included an earlier
   promote step (row 24). That step now lives in block E (row 25).
