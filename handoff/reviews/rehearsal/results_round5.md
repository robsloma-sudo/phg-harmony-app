# PHG-026 round-5 rehearsal results (2026-09-28)

Every block ran on the live database (project lqjtwabzmgjcufftuqvu, as `postgres`) inside one `DO` block that ends in
`RAISE EXCEPTION`, so nothing was kept. Each MCP call stayed under 60 s (`statement_timeout` 58 s inside the block).
No `apply_migration`, no cron change. Generator: `gen.py` (round 5). SQL: `rehearse_round5.sql` (all blocks) and
`rehearse_round5_<A..G>.sql` (one per block). Blocks were sent with full-line comments removed and indentation collapsed
(payload size), statements unchanged. Every block now ends with `REHEARSAL SUMMARY {passes, ms, key values} FULL {...}`
so the result survives the MCP output truncation.

## Read-only check afterwards (all as before round 5)
- cron 7 `active=false`, 13 `active=false`, 16 `active=true`.
- None of these exist: phg_backup_function_defs_20260927, phg_repair_run_20260927, phg_repair_damaged_20260927,
  phg_repair_plan_menus_20260927, phg_backup_staging_dupes_20260927, phg_backup_menus_currency_20260927,
  phg_repair_step3_done, phg_repair_step4_done, menus_one_current_per_account, menus_item_set_idx,
  menu_source_candidates_item_set_idx, phg_backup_design_fn_defs_20260928.
- 0 new columns on menus / menu_source_candidates / staging_menu_extract; 0 new columns on phg.menu_design_proposals.
- None of the new functions exist (phg_menu_bev_count, phg_menu_payload_bev_count, phg_repair_*, rollbacks,
  phg_design_proposal_score, ...). The 10-arg submit_menu is still present.
- md5 of the live definitions of submit_menu (both), promote_clean_menu_batch, phg_save_menu_candidate_extraction,
  phg_design_proposal_submit / review / status and phg_designer_query: `e02e48ec...` before and after (identical);
  phg_designer.run `251b22ba...` before and after (identical).
- 0 rehearsal menus, 0 rehearsal staging rows, 0 rehearsal design tasks; candidate 13965 still `legacy_empty`.

## Pass / fail

| # | Part | Block | Result | Time |
|---|---|---|---|---|
| 1 | File 1 applied | A-E, G | PASS | 78-171 ms |
| 2 | 4 definitions saved; backup SELECT-only; 10-arg dropped; promote clamp 5; `submit_menu` proconfig `[search_path=public, lock_timeout=5s]` | A | PASS | |
| 3 | s1-s10b as in round 4 (duplicate, near-identical, damping s9 / s9b, item page, partial, smaller, empty, unknown price, price enrichment x2, same-source item page s10 / s10b) | A | PASS (all) | scenarios 814 ms |
| 4 | **s11 (new, C1)**: current menu is an ITEM page of another source, 0 minutes old; a REAL page with the same items / same (items, drinks) -> `created`, `real_page_over_item_page` | A | PASS | |
| 5 | **s11b (new, C1 damping)**: same, but the real page has 28 drinks items vs 33 (near-identical, not larger) -> `created`, `newer_near_identical_capture` (round 4 damped it to `alternate_near_identical_recent_other_source`) | A | PASS | |
| 6 | **s11c control**: the same capture behind a REAL-page current menu of another source -> still damped (`alternate_near_identical_recent_other_source`) | A | PASS | |
| 7 | **s12 (new, SF-D)**: current menu is item page `copy2?item=a`; sibling item page `copy2?item=b` (same key), same size, one price changed -> `created_alternate`, `alternate_item_page` (round 4 replaced it) | A | PASS | |
| 8 | **s12b (new, exact-URL exemption)**: the SAME URL `copy2?item=a` with the changed price -> `created`, `same_source_recapture` | A | PASS | |
| 9 | **s12c control**: sibling item page with one more item (strictly larger) -> `created` | A | PASS | |
| 10 | **M1**: payload with the same drinks line twice + one other -> 2; stored count of the current menu 33 = payload count 33 | A | PASS | |
| 11 | File 2 steps 1-2 | B-E, G | PASS | 6.8 / 7.7 / 7.9 / 8.2 / 8.7 s (one B run 14.2 s) |
| 12 | Step 2 with DISTINCT drinks keys: `{current_changed 348, damaged 119, not_restored 0, chosen_item_pages 42 (4 changed), pre_incident_replaced_newer_same_source 22, smaller 0, no_current 0, multi 0}`; by reason 300 more items / 12 same items more drinks / 36 real page over item page / 0 exact ties (identical to round 4); touched 1,547, with pre-incident menu 185, plan rows 7,614 | B | PASS | |
| 13 | **SF-A**: all 8 tables created by the two files are SELECT-only for service_role (insert/update/delete/truncate/trigger/references false): function_defs, menus_currency, staging_dupes, plan_menus, run, damaged, step3_done, step4_done | B | PASS | |
| 14 | **SF-B**: step3_batch, step4_batch, phg_repair_20260927_rollback, phg_rollback_function_defs_20260927: EXECUTE false for service_role, anon, authenticated; true for postgres. `current_user` = postgres (the runbook role) | B | PASS | |
| 15 | **M6**: rollback proconfig `[search_path=public, pg_temp, lock_timeout=5s]`; batch functions the same | B | PASS | |
| 16 | Extraction save: candidate 13965 -> `review`, `duplicate_of` 515238, 0 rows re-staged | B | PASS | 41 ms |
| 17 | **Monitor (SF-C), post-repair**: 8 rows, all pass (new: `0 smaller, 0 allowed`; flip-flop `0`) | B | PASS | 2.9 s |
| 18 | **Monitor new rows on forged data**: damaged venue ACC-CO-LED-01-55836 made smaller -> smaller row FAILS (`1 smaller, 0 allowed; review: ACC-CO-LED-01-55836`); the same shrink marked as a re-capture of its own page -> PASSES (`1 smaller, 1 allowed`); 3 non-growing changes at ACC-CO-LED-03-06531 -> flip-flop row FAILS (`1 (first 20: ACC-CO-LED-03-06531)`) | B | PASS | |
| 19 | Monitor replay over the incident window: 1.2 row FAILS at 2.892 (7,429 / 2,569); new rows pass | B | as expected | |
| 20 | Step 3 (100 venues), one call | C, D, G | 1,799 left, 30,126 rows backed up | 15.6 / 13.5 / 16.7 s |
| 21 | Step 4 (500), one call | C | 18,745 left | 16.1 s |
| 22 | Step 4 (200), one call | E | 19,045 left | 11.8 s |
| 23 | Candidate index (plain here, CONCURRENTLY in runbook) | D | PASS | 2.5 s |
| 24 | Release gate: 9 pass, step 3 / step 4 rows fail as expected (one call each), cron `2 jobs; 7:false,13:false` | D | PASS | 6.4 s |
| 25 | Repair rollback: `{348 rolled back / demoted / restored, staging 30,126 rows / 371 venues, skipped 0, skipped_accounts []}`; the same object stored in `phg_repair_run_20260927` step `rollback` | D | PASS | 6.5 s |
| 26 | **SF-E: phg_026_rollback_check.sql after the rollback**: 9 rows all pass; review candidates 0 | D | PASS | 196 + 103 ms |
| 27 | Function rollback returns 4, index gone, 10-arg back, live body, anon/auth no, service_role yes; then submit_menu -> `created`, 1 current, old demoted | D, E | PASS | 20 / 25 ms; submit 26 / 51 ms |
| 28 | promote_clean_menu_batch(1) on a re-staged incident sibling page -> `duplicate` 1, created 0, failed 0, current unchanged | E | PASS | 4.3 s |
| 29 | **Roll-forward candidate-hash reset** (header statement): 299 rows updated, 0 left | E | PASS | 5.8 s (a scan of all 550,045 candidates; in production it touches every hashed candidate) |
| 30 | **Rollback skip paths + skipped_accounts (G)**: new menu at ACC-CO-LED-03-00124 -> `newer_menu`; forged 2-current backup at ACC-CO-LED-01-55836 -> `multi_current_backup`; both in `skipped_accounts` with scope `menus_and_staging`; both venues untouched, 1 current each; re-extracted page of ACC-CO-LED-01-65702 stays superseded; 346 rolled back, 30,124 staging rows restored, 0 other rows left, 0 currency mismatches, 0 multi-current | G | PASS | rollback 7.1 s |
| 31 | **Rollback check after the skip-path rollback (G)**: 9 rows all pass (`2 (1 newer menu, 1 multi-current backup)`); review list (M2) has 4 rows: both skipped venues (with current menu, largest pre-incident size, menus after the repair) and 2 staging pages not restored (the re-extracted page and the skipped venue's page) | G | PASS | 208 + 171 ms |
| 32 | Score gate file: 3 definitions saved with ACL; backup SELECT-only; NULL layout and EMPTY elements -> `auto_rejected`; with layout -> `submitted` | F | PASS | file 16 ms |
| 33 | **Score gate approve path**: accuracy 80 -> `blocked_by_score_gate`; **re-score appended** (`rescore_of_same_version` 1, history 4 entries dc 90 / cr 90 / ar 80 / ar 90, latest average 90); EMPTY elements -> `blocked_by_layout_gate`; NULL / no elements -> blocked; status stays `submitted`; all 90 -> `approved` with three averages | F | PASS | |
| 34 | **Score gate rollback**: returns 3; restored bodies; **service_role EXECUTE re-granted from the saved ACL** (`{postgres=X/postgres,service_role=X/postgres}` x3); anon/auth none; rollback function not executable by service_role; `set local lock_timeout` precedes the ALTER | F | PASS | |

## Problems found by the rehearsal and fixed
1. Score gate: `if ... or not case when ... then ... end` is a PL/pgSQL syntax error (the IF scanner stops at the
   CASE's THEN). The CASE is now in parentheses (both places). Found with a local Postgres 16 parse, then live.
2. Score gate rollback: the loop did not select the new `acl` column (42703). Fixed; re-grant rehearsed (row 34).
3. Harness only (no migration change): a variable `w` clashed with a `w` column alias in the monitor baseline (42702,
   renamed `wres`); an operator-precedence slip in D's summary line (`->` vs `-`); s11c first used an item set already
   stored by s9 (would return `duplicate_item_set`), so s11b/s11c use the s10 prices.

## Timings summary
- File 2 steps 1-2 hold SHARE ROW EXCLUSIVE on menus 6.8-8.7 s (one run 14.2 s), same as round 4 (DISTINCT drinks
  count adds no measurable time).
- Step 3: 13.5-16.7 s per 100 venues, 19 calls, ~4.5-5.3 min. Step 4 at 500: 16.1 s, ~39 calls, ~10.5 min.
- Rollback 6.5-7.1 s; rollback check 0.3-0.4 s; release gate 6.4 s; monitor 2.9 s; function rollback 20-25 ms.
