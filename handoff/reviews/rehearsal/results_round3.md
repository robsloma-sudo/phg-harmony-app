# PHG-026 round-3 rehearsal results (2026-09-28)

Every block ran on the live database (project lqjtwabzmgjcufftuqvu) inside one `DO` block that ends in
`RAISE EXCEPTION`, so nothing was kept. Each block re-runs the setup it needs, because an MCP call times out at 60 s.
No `apply_migration` was used and no cron job was changed. Generator: `gen.py`. SQL: `rehearse_round3.sql` (all blocks) and
`rehearse_round3_<A..F>.sql` (one per block, exactly as generated from the current migration files).

**Final run (this file's numbers):** the round-3 engineer session re-ran every block against the committed files.
- Block A ran exactly as generated.
- Blocks B and D ran with the same statements with the SQL comments removed, to keep the payload small. No statement
  was changed.
- The C variant, the E promote step, and F: see the notes.
An earlier session ran the same blocks. Its figures agree and are kept in the notes where they add something.

Afterwards, read-only checks confirmed that nothing exists live:
- These objects are absent: phg_backup_function_defs_20260927, phg_repair_run_20260927, phg_repair_damaged_20260927,
  phg_repair_plan_menus_20260927, phg_backup_staging_dupes_20260927, phg_backup_menus_currency_20260927,
  menus_one_current_per_account, menu_source_candidates_item_set_idx and phg_backup_design_fn_defs_20260928.
- menus.item_keys does not exist. phg_rollback_function_defs_20260927, phg_menu_keys_price_adds and
  phg_design_proposal_score do not exist.
- The live 10-arg submit_menu is still present.
- There are 0 rehearsal menus and 0 rehearsal staging rows.
- Cron 7 and 13 are still paused (`active=false`); cron 16 is active as before.
- Candidate 13965 is unchanged (`legacy_empty`).

## Pass / fail

| # | Part | Block | Result | Time |
|---|---|---|---|---|
| 1 | File 1 (20260927190000) applied | A, B, D, C', E' | PASS | 115-211 ms; 2.6 s when it waited for cron job 16 (note 1) |
| 2 | 4 function definitions (+ ACL) saved; service_role cannot INSERT into the backup (can SELECT); 10-arg overload dropped | A | PASS | - |
| 3 | promote_clean_menu_batch clamps to 5 pages (`least(5,`) | A | PASS | - |
| 4 | s1 exact copy from another URL -> `duplicate_of_current`, nothing inserted | A | PASS | scenarios total 570 ms |
| 5 | s2 3 prices changed, other URL, current menu aged 30 days -> `created` (`newer_near_identical_capture`) | A | PASS | |
| 6 | s9 flip-flop: original page again, current menu minutes old -> `created_alternate` (`alternate_near_identical_recent_other_source`), current unchanged | A | PASS | |
| 7 | s9b control: the original page with one more item -> `created` (`contained_in_larger_capture`) | A | PASS | |
| 8 | s3 `?item=` page on the current URL -> `alternate_item_page` | A | PASS | |
| 9 | s4 same URL, 10 of 33 items -> `alternate_partial_recapture` | A | PASS | |
| 10 | s5 2 food items, other URL -> `alternate_smaller_other_source` | A | PASS | |
| 11 | s6 zero items -> `empty_capture_ignored` | A | PASS | |
| 12 | s7 unknown price overlaps both ways (1/1), different prices 0; price-adds 1 / reverse 0 / current has both 0 | A | PASS | |
| 13 | s8a price enrichment, same source (current item lost its price, capture has it; price_adds 1) -> `created` (`same_source_price_enrichment`), not a duplicate | A | PASS | |
| 14 | s8b price enrichment, other source, current minutes old -> `created` (`price_enrichment_other_source`); damping does not hold back a price | A | PASS | |
| 15 | 0 multi-current accounts before, after every scenario, and at the end | A | PASS | |
| 16 | File 2 steps 1-2 (under SHARE ROW EXCLUSIVE on menus) | B, D, C', E' | PASS | 8.2 / 8.3 / 8.9 / 11.5 s |
| 17 | Step 2 postconditions: `{current_changed 348, multi_current 0, no_current 0, smaller 0}` | B, D | PASS | |
| 18 | Damaged venues saved before Step 2: 119; after Step 2 `damaged_not_restored` 0 (in-file assert + independent recount 0) | B, D | PASS | |
| 19 | Picks recorded: `chosen_item_pages` 42 (4 of them changed to an item page); `pre_incident_replaced_newer_same_source` 22 | B | recorded | |
| 20 | Changed-by-reason: more items 300, same items + more drinks 12, real page over item page 36, exact ties 0 | B | PASS | B checks 53 ms |
| 21 | Touched 1,547 (7,614 plan rows); with a pre-incident menu 185; 0 without a current menu; 0 NULL item_keys | B | PASS | |
| 22 | service_role cannot INSERT into the 3 backup tables | B | PASS | |
| 23 | Extraction save: candidate 13965 `/menu` saves the same 16 priced items as sibling 515238 `/happyhour` -> `review`, `duplicate_of` 515238, 0 rows re-staged | B | PASS | 64 ms |
| 24 | promote_clean_menu_batch(1) on a re-staged incident sibling (`thesherpagrill.com/menu?item=rehearsal-new-sibling`, 13 beverage rows) -> `duplicate_of_current` 1, created 0, failed 0, current unchanged, rows marked | E' | PASS | 2.6 s (queue before: 0) |
| 25 | phg_repair_step3_batch(100), one call | D, C' | runs (1,799 venues left) | 14.5 / 13.2 s |
| 26 | phg_repair_step4_batch(200), one call | D | runs (19,045 left) | 11.0 s |
| 27 | phg_repair_step4_batch(500), one call (the cap; new this run) | C' | runs (18,745 left) | 17.2 s |
| 28 | Candidate item-set index (plain CREATE INDEX here; CONCURRENTLY in the runbook) | D | PASS | 2.2 s |
| 29 | Release-gate SQL (rows below) | D | 9 PASS, 2 expected FAIL (steps 3-4 only partly run) | 6.2 s |
| 30 | phg_repair_20260927_rollback() after Step 3: 348 venues rolled back, 348 demoted, 348 restored, 0 skipped, 30,126 staging rows restored (= backup rows); 0 still superseded; currency identical to backup (all four columns); 0 multi-current | D | PASS | 10.6 s |
| 31 | phg_rollback_function_defs_20260927(): returns 4, index dropped, 10-arg overload back, live body restored, anon/authenticated cannot execute any of the 4, service_role can | D | PASS | 38 ms |
| 32 | Then ONE submit_menu on ACC-CO-LED-03-25486 (has a current menu) with the restored live body -> `created`; 1 current menu; old one demoted | D | PASS | 50 ms |
| 33 | SF10 score-gate migration (Coordinator's version, unmodified): 3 definitions saved, NULL layout rejected (coalesce), rollback returns 3, drops the 11-arg submit + score function, restores the 10-arg submit/review/status, anon/authenticated cannot execute, service_role can (default privileges) | F | PASS | 32 ms |

Block D ran file 1, file 2, one Step 3 call, one Step 4 call, the index, the gate, the repair rollback and the
function rollback plus submit in one call: about 53 s in total.

**Totals by extrapolation.** Step 3 and Step 4 are too long for one 60 s call, so they were timed per call and not run
to the end:
- **Step 3:** 1,899 venues. 19 calls x ~13-14.5 s = **~4.5 min**. The first 100 venues supersede 30,126 duplicate rows.
  An earlier run superseded 60,157 for the first 300.
- **Step 4 at 500 (runbook, changed from 200):** 19,245 venues. ~39 calls x ~17 s = **~11 min**.
- **Step 4 at 200:** ~97 calls x ~11 s = ~18 min. Most of each call's time is the fixed "venues remaining" count, so
  the larger batch is cheaper overall.
- The release gate, the repair rollback and the function rollback each take seconds.

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
| step 4 finished for candidates found before the repair | false (expected: 1 of ~39 calls run) | 19045 |
| candidate item-set index exists | true | 1 |
| cron 7 and 13 still paused (re-enable only after this gate) | true | 7:false,13:false |

## Notes

1. **Lock wait on file 1 (runbook item).** Active cron job 16 (gtt-acquire-menu-visual-assets) runs every 20 s, for up
   to 5 s, on menu_source_candidates. `ALTER TABLE ... ADD COLUMN` needs a brief exclusive lock.
   - In this run, block B waited 2.6 s for it, inside file 1's 3 s `lock_timeout`.
   - An earlier session hit the limit once: `55P03 canceling statement due to lock timeout`, followed by a full,
     clean rollback.
   - Runbook: if file 1 or file 2 stops with 55P03, re-run it. Job 16 does not have to be paused.
2. **C' and E' are reduced blocks built from the same statements.**
   - C' is file 1 up to the helpers, then file 2 steps 1-2, the index, and the Step 3 / Step 4 functions. It then
     runs one `step3_batch(100)` and one `step4_batch(500)`. It exists to time the Step 4 cap, which had not been
     rehearsed.
   - E' is file 1's helpers plus submit_menu and promote_clean_menu_batch, then file 2 steps 1-2 and the index. It
     then runs the promote test from block E.
   - The generated `rehearse_round3_C.sql` / `_E.sql` are the full blocks the earlier session ran. Its figures were
     Step 3 12.8 / 13.0 / 11.5 / 12.4 s per call and the promote test 6.6 s.
3. **Why the promote test uses a re-staged page.** The promotion queue (`v_menu_staging_promotion_candidates`) is
   empty today. The 6,760 `promotion_ready` rows are food pages the view excludes. So E' re-staged one incident item
   page's rows under a new sibling `?item=` URL, which gives a new content hash with the same items.
   - The update also touched that page's 88 non-beverage rows, which the view does not select. They stayed NULL.
   - All of it was rolled back.
4. **Scenario 2 aging.** Every live menu is under 7 days old (created 2026-09-25..27). So the rehearsal set the test
   venue's current menu back 30 days before s2. That exercises the near-identical replacement rather than the damping.
   Scenario 9 then exercises the damping.
5. **Catalog reads after the function rollback** run in a separate statement from the rollback call. A read in the
   same statement would see the old snapshot; an earlier run showed this.
6. **Score-gate file (20260928030000).** An earlier session had added an `acl` column and a service_role re-grant to
   this file's backup/rollback. That went beyond the SF10 fix allowed there, so the file was reverted to the
   Coordinator's version (9e41e78). The revert landed on the branch in commit abc0066.
   - The SF10 coalesce fix was already in the Coordinator's version.
   - Block F shows service_role still has EXECUTE after the score-gate rollback, through the schema's default
     privileges, so the extra grant was not needed.
