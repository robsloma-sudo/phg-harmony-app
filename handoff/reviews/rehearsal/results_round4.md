# PHG-026 round-4 rehearsal results (2026-09-28)

Every block ran on the live database (project lqjtwabzmgjcufftuqvu) inside one `DO` block that ends in
`RAISE EXCEPTION`, so nothing was kept. Each block re-runs the setup it needs (an MCP call times out at 60 s).
No `apply_migration` was used and no cron job was changed. Generator: `gen.py` (round 4). SQL: `rehearse_round4.sql`
(all blocks) and `rehearse_round4_<A..G>.sql` (one per block, exactly as generated from the current files).

**How the blocks were sent.** Every block was generated from the committed files and sent with full-line SQL
comments removed and leading whitespace collapsed (payload size); no statement was changed. Unlike round 3 there are
no reduced variants: C, E and F ran as generated.
- Two harness fixes were needed along the way and are in `gen.py`: a PL/pgSQL variable `g` clashed with the alias in
  scenario 4's `generate_series(1,5) g` (renamed `gres`), and a `r` column alias clashed with the block's `r`
  variable in the monitor baseline (renamed `ratio`). Block F first read the proposal status in the same statement as
  the review call and saw the statement snapshot (the same effect as round-3 note 5); the read is now a separate
  statement. None of these touched a migration file.

Afterwards, read-only checks confirmed that nothing exists live:
- Absent: phg_backup_function_defs_20260927, phg_repair_run_20260927, phg_repair_damaged_20260927,
  phg_repair_plan_menus_20260927, phg_backup_staging_dupes_20260927, phg_backup_menus_currency_20260927,
  phg_repair_step3_done, phg_repair_step4_done, menus_one_current_per_account, menus_item_set_idx,
  menu_source_candidates_item_set_idx, phg_backup_design_fn_defs_20260928.
- No new columns on menus / menu_source_candidates; phg.menu_design_proposals has no layout / review_scores.
- None of these functions exist: phg_rollback_function_defs_20260927, phg_menu_keys_price_adds, phg_menu_source_key,
  phg_repair_20260927_rollback, phg_repair_step3_batch, phg_repair_step4_batch, phg_design_proposal_score,
  phg_rollback_design_score_gate_20260928.
- The live 10-arg submit_menu is still present. 0 rehearsal menus, 0 rehearsal staging rows (the 73 staging rows that
  contain "rehearsal" are real venue items such as "Rehearsal Dinner", loaded from 2026-09-27 05:17Z), 0 design tasks.
- Cron 7 and 13 still paused (`active=false`), cron 16 active as before. Candidate 13965 unchanged (`legacy_empty`).

## Pass / fail

| # | Part | Block | Result | Time |
|---|---|---|---|---|
| 1 | File 1 (20260927190000) applied | A-E, G | PASS | 54-202 ms (no lock wait this round) |
| 2 | 4 definitions saved; the definition backup is SELECT-only for service_role (insert/update/delete/truncate/trigger/references all false); 10-arg dropped; promote clamp 5 | A, B | PASS | - |
| 3 | Scenarios s1-s9b, s3-s8b as in round 3 (duplicate, near-identical, damping, item page, partial, smaller, empty, unknown price, price enrichment x2) | A | PASS (all 14) | scenarios total 483 ms |
| 4 | **s10 (C1, new)** same-source item page `copy2?item=full`, same size (33) as the real-page current menu, one price changed -> `created_alternate` / `alternate_item_page`, current unchanged (round 3 would have replaced it) | A | PASS | |
| 5 | **s10b (new)** the same item page with one more item (34) -> `created` / `same_source_recapture` | A | PASS | |
| 6 | 0 multi-current accounts before, after every scenario, and at the end | A | PASS | |
| 7 | File 2 steps 1-2 under SHARE ROW EXCLUSIVE | B-E, G | PASS | 6.9 / 8.3 / 8.4 / 8.4 / 8.9 s (one earlier B run 14.4 s) |
| 8 | Step 2 `{current_changed 348, multi_current 0, no_current 0, smaller 0, damaged_venues 119, damaged_not_restored 0, chosen_item_pages 42 (4 changed), pre_incident_replaced_newer_same_source 22}`; recount 0; touched 1,547; with a pre-incident menu 185; plan rows 7,614; 0 NULL item_keys | B | PASS | B checks 44 ms |
| 9 | Changed-by-reason: more items 300, same items + more drinks 12, real page over item page 36, exact ties 0 | B | PASS | |
| 10 | **Backup tables SELECT-only for service_role** (function_defs, menus_currency, staging_dupes): select true; insert/update/delete/truncate/**trigger/references** false | B | PASS | |
| 11 | **Step 3 / Step 4 functions carry `lock_timeout=5s`** in proconfig (function-level SET, reset when the call returns) | B | PASS | |
| 12 | Real venues whose currency backup has more than one current menu | B | 0 (recorded) | |
| 13 | Extraction save: candidate 13965 -> `review`, `duplicate_of` 515238, 0 rows re-staged | B | PASS | 14 ms |
| 14 | **phg_026_monitor.sql in the post-repair state** (rows below) | B | 6 rows, all pass | 2.7 s |
| 15 | **Monitor replay over the incident window** (step2.ran_at moved to 2026-09-27 00:00Z): the 1.2 check FAILS at 2.892 | B | as expected | |
| 16 | phg_repair_step3_batch(100), one call | C, D, G | runs (1,799 left, 30,126 rows backed up) | 14.6 / 17.0 / 15.2 s |
| 17 | phg_repair_step4_batch(500), one call (runbook size) | C | runs (18,745 left) | 14.3 s |
| 18 | phg_repair_step4_batch(200), one call | D, E | runs (19,045 left) | 12.2 / 13.2 s |
| 19 | Candidate item-set index (plain here; CONCURRENTLY in the runbook) | D | PASS | 2.5 s |
| 20 | Release gate (rows below): 9 PASS, 2 expected FAIL (Step 3 / Step 4 only partly run). **Cron row now asserts both jobs exist**: value `2 jobs; 7:false,13:false` | D | PASS | 6.3 s |
| 21 | Repair rollback after Step 3: `{venues_rolled_back 348, menus_demoted 348, menus_restored 348, staging_venues_rolled_back 371, staging_rows_restored 30,126 (= backup), venues_skipped_newer_menu 0, venues_skipped_multi_current_backup 0, staging_venues_skipped 0}`; currency identical to backup; 0 still superseded; 0 multi-current | D | PASS | 7.7 s |
| 22 | Function rollback: returns 4, index dropped, 10-arg back, live body restored, anon/authenticated cannot execute, service_role can; then one submit_menu -> `created`, 1 current, old demoted | D, E | PASS | 24 / 15 ms; submit 31 / 20 ms |
| 23 | promote_clean_menu_batch(1) on a re-staged incident sibling page -> `duplicate` 1, created 0, failed 0, current unchanged, 13 rows `duplicate_of_current` | E | PASS | 4.3 s |
| 24 | **Rollback skip path (new, block G)**: after Step 2 and one Step 3 call, one new menu submitted for plan venue ACC-CO-LED-03-00124 (`created`, `contained_in_larger_capture`); rollback -> `venues_skipped_newer_menu` 1; that venue's menus identical before/after (current = the new menu); its 1 backed-up staging row stays superseded | G | PASS | rollback 8.2 s |
| 25 | **Multi-current backup (new, block G)**: backup of plan venue ACC-CO-LED-01-55836 forged to 2 current menus -> rollback does not abort, `venues_skipped_multi_current_backup` 1, venue untouched, 1 current | G | PASS | |
| 26 | **Re-extracted page (new, block G)**: one new staging row loaded for a backed-up page of ACC-CO-LED-01-65702 -> that page's backed-up row stays superseded (1 of 1) | G | PASS | |
| 27 | Block G totals: `venues_rolled_back 346` (348 - 2 skipped), `staging_venues_rolled_back 369`, `staging_rows_restored 30,124` (= 30,126 - 1 skipped venue - 1 re-extracted page); every other backed-up row restored (0 left); currency of every other venue identical to backup; 0 multi-current | G | PASS | |
| 28 | Score gate 20260928030000: 3 definitions saved; backup SELECT-only for service_role (insert/trigger/references false); NULL layout on submit -> `auto_rejected`; with layout -> `submitted` | F | PASS | file 36 ms |
| 29 | **Approve path (new)**: accuracy_reviewer at 80 -> `blocked_by_score_gate` (returns accuracy_reviewer 80); layout NULL -> `blocked_by_layout_gate`; layout without elements -> `blocked_by_layout_gate`; status stays `submitted`; all three at 90 -> `approved`, result carries design_critic, content_reviewer **and accuracy_reviewer** (90 each), status `approved` | F | PASS | |
| 30 | Score-gate rollback returns 3, drops the 11-arg submit and the score function, restores the 10-arg submit / review / status; anon/authenticated cannot execute; service_role can | F | PASS | |

Block D (file 1, file 2, one Step 3 call, one Step 4 call, the index, the gate, the repair rollback, the function
rollback and a submit) took about 54 s in one call.

**Totals by extrapolation** (Step 3 and Step 4 are too long for one call):
- Step 3: 1,899 venues, 19 calls x 14.6-17.0 s = **~4.6-5.4 min**.
- Step 4 at 500 (runbook): 19,245 venues, ~39 calls x ~14-17 s = **~9-11 min**. At 200: ~97 calls x ~12-13 s = ~20 min.
- With the 5 s lock_timeout per call, a call that meets cron 16 (Step 4) or an in-flight submit_menu / extraction
  save (Step 3) can stop with 55P03 or 40P01; it rolls back completely and the runbook says to call again.

## Release gate rows (block D)

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
| cron 7 and 13 exist and are still paused (re-enable only after this gate) | true | 2 jobs; 7:false,13:false |

## Monitor rows (block B, rehearsed post-repair state, before any cron cycle)

| check | pass | value |
|---|---|---|
| 0 accounts with more than one current menu | true | 0 |
| one-current unique index exists | true | 1 |
| menus per distinct item set since release <= 1.2 (null until menus are created) | true | null (no menus created since step 2) |
| submit_menu outcomes since release (informational) | true | null |
| promotion outcomes since release (informational) | true | null |
| venues with > 2 current-menu changes since release (informational) | true | 0 |

**Baseline for the 1.2 threshold** (menus per distinct (venue, item set), computed in block B after the Step 1
backfill):

| window | menus | distinct (venue, item set) | ratio |
|---|---|---|---|
| 2026-09-25 | 4,775 | 4,775 | 1.000 |
| 2026-09-26 | 25 | 25 | 1.000 |
| pre-incident (before 2026-09-27 00:00Z) | 4,800 | 4,800 | **1.000** |
| incident window (2026-09-27) | 7,429 | 2,569 | **2.892** |

- The normal rate is 1.000: before the incident no venue stored the same item set twice. The incident rate was 2.892
  (the ~3.0 in the header).
- 1.2 therefore allows 20% legitimate same-set re-captures (for example a menu captured again after it had been
  replaced) and still sits far below the incident rate. Replaying the monitor over the incident window returns
  `pass = false` at 2.892, so the check catches a repeat.
- Replay informational rows: outcomes `{current 1438, superseded 5643, repair_20260927_best_single_menu 348}`,
  promotions `{promoted 94030}`, churn 0.

## Notes

1. **Why G forges a multi-current backup.** No real venue has more than one current menu in the backup today (row 12),
   so the exclusion could not be shown on real data. G sets `is_current = true` on a second backed-up menu of one
   plan venue, inside the rolled-back transaction.
2. **Why the new staging row sets loaded_at explicitly.** In one transaction `now()` equals the backup's
   `backed_up_at`, so a default `loaded_at` would not be "later". In production the repair and a re-extraction are
   separate transactions.
3. **staging_venues_rolled_back** counts every venue whose staging rows the rollback may restore (plan venues with a
   changed current menu plus Step-3 venues), after the skips; `staging_venues_skipped` counts Step-3-only venues that
   were skipped (plan venues that are skipped are already in the two `venues_skipped_*` counts).
4. **Lock waits.** No block waited for cron job 16 this round (file 1 took at most 202 ms).
