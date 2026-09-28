# PHG-026 pre-publish rehearsal results (after round 5, 2026-09-28)

Every block ran on the live database (project lqjtwabzmgjcufftuqvu, as `postgres`). Each block ran inside one `DO`
block that ends in `RAISE EXCEPTION 'REHEARSAL SUMMARY % FULL %'`, so nothing was kept. Each MCP call stayed under
60 s (`statement_timeout` 58 s inside the block).

The rules held throughout: no `apply_migration`, no Edge function deploy, no cron change, and the designer gateway
and design files were not touched.

- Generator: `gen.py` (pre-publish version).
- SQL: `rehearse_prepublish.sql` (all blocks) and `rehearse_prepublish_<A..G>.sql` (one per block).
- Blocks were sent with full-line comments removed and indentation collapsed; the statements were unchanged.
- The migration files are embedded verbatim through `EXECUTE $tag$ ... $tag$`. Blocks were syntax-checked first on a
  local Postgres 16.

## Read-only check (the same query before the first block and after the last)

| Item | Before | After |
|---|---|---|
| cron 7 / 13 / 16 active | false / false / true | false / false / true |
| PHG-026 tables and indexes (13 names, incl. the new phg_repair_rollback_saved_20260927) | none | none |
| New columns on menus / menu_source_candidates / staging_menu_extract | 0 | 0 |
| New functions (phg_menu_exact_url, phg_menu_bev_count, phg_repair_*, rollbacks, phg_design_proposal_score, ...) | none | none |
| submit_menu overloads | 2 | 2 |
| md5 of the live definitions (submit_menu x2, promote_clean_menu_batch, phg_save_menu_candidate_extraction, phg_design_proposal_submit / review / status, phg_designer_query) | 6b6ab2c8... | 6b6ab2c8... |
| md5 of phg_designer.run | 251b22ba... | 251b22ba... |
| menus total / current | 12,229 / 6,162 | 12,229 / 6,162 |
| staging rows superseded | 39,918 | 39,918 |
| candidate 13965 | legacy_empty | legacy_empty |
| menus with "rehearsal" in the URL / staging items named "Rehearsal%" (pre-existing, broad match) | 3 / 3 | 3 / 3 |
| Edge functions | phg-expanded-data v4; all versions as listed | unchanged (phg-expanded-data v4) |

## Pass / fail

| # | Part | Block | Result | Time |
|---|---|---|---|---|
| 1 | File 1 applied | A-E, G | PASS | 64-292 ms (C's first try: 55P03 at 3.1 s, see below) |
| 2 | **s13 (SF-1)**: the current menu is item page `copy2?item=a` with 33 items. The same URL is re-captured with 4 of 33 prices changed (overlap 29, under the round-5 threshold of 30). Result: `created`, `same_source_recapture` (round 5 froze it). | A | PASS | scenarios 1,352 ms |
| 3 | **s13b**: the same URL with 12 of 33 items. The partial-recapture guard holds: `created_alternate`, `alternate_partial_recapture`. | A | PASS | |
| 4 | **s13c (normalised exact URL)**: `HTTP://WWW.Rehearsal.Example.com:443/copy2/?item=a#reviews` counts as the same URL: `created`. | A | PASS | |
| 5 | **s13d control**: `copy2?item=a&size=large` is a different exact URL: `alternate_item_page`. | A | PASS | |
| 6 | `phg_menu_exact_url` variants: `&amp;` decoded; `''` -> null; anon has no EXECUTE. | A | PASS | |
| 7 | **m6 / spec minor**: proconfig of `submit_menu` and of `phg_save_menu_candidate_extraction` is `[search_path=public, pg_temp, lock_timeout=5s]`. | A | PASS | |
| 8 | s1-s12c as in round 5 (s11/s11b/s11c, s12/s12b/s12c, M1 ...). | A | PASS (all 25 checks) | |
| 9 | File 2 steps 1-2. | B-E, G | PASS | B 8.4 / C 8.4 / D 7.2 / E 9.0 / G 8.3 s |
| 10 | Step 2 matches round 5 exactly. Totals: `{current_changed 348, damaged 119, not_restored 0, chosen_item_pages 42 (4 changed), pre_incident_replaced_newer_same_source 22, smaller 0, no_current 0, multi 0}`. By reason: 300 / 12 / 36. | B | PASS | |
| 11 | Extraction save: candidate 13965 -> `review`, duplicate_of 515238, 0 rows re-staged. | B, E | PASS | 42 / 40 ms |
| 12 | Monitor after the repair: 9 rows, all pass. That includes the new informational row "current-menu changes since release by kind". | B | PASS | 2.8 s |
| 13 | **m4 flip-flop**: 3 forged non-growing changes at ACC-CO-LED-03-06531 whose replaced menus share the current menu's source -> row PASSES (0). By kind: "non-growing same source 4 / 2". The same 3 with distinct sources -> row FAILS "1 (first 20: ACC-CO-LED-03-06531)". By kind: "same source 1 / 1; other source 3 / 1". | B | PASS | |
| 14 | The forged "smaller" row fails (ACC-CO-LED-01-55836). The same shrink marked as a same-page re-capture is allowed. | B | PASS | |
| 15 | Monitor replay over the incident window: row 1.2 FAILS at 2.892 (7,429 / 2,569). | B | as expected | |
| 16 | Step 3 (100 venues), one call: 1,799 left, 30,126 rows backed up. | C, D, G | as round 5 | 15.5 / 16.9 / 11.9 s |
| 17 | Step 4 (500), one call: 18,745 left. | C | as round 5 | 12.8 s |
| 18 | Step 4 (200), one call: 19,044 left. | E | as round 5 | 11.7 s |
| 19 | Candidate index (plain here; CONCURRENTLY in the runbook). | D | PASS | 2.5 s |
| 20 | **Release gate, new row (B1)**: "restaurant_menu_map (v5 read: current menus only) returns the Step-2 menu for 3 changed venues" -> `3 of 3 ok`. The v4 read would differ at all three: ACC-CO-LED-01-55836, ACC-CO-LED-01-64433, ACC-CO-LED-02-41796. | D | PASS | gate 6.4 s |
| 21 | **Release gate, new informational row**: venues whose newest menu is not current = 407 after Step 2 (190 live today, before the repair). | D | shown | |
| 22 | Release gate, other rows: 11 pass. The step 3 / step 4 rows fail as expected after one call each (1,799 / 19,245 left). | D | as expected | |
| 23 | Data rollback: `{rolled back 348, demoted 348, restored 348, staging 30,126 rows / 371 venues, skipped []}`, which equals the run row. | D | PASS | 5.3 s |
| 24 | rollback_check query 1: 9 / 9 true. | D, G | PASS | 143 / 170 ms |
| 25 | rollback_check query 2 (review list) without post-release activity: 0 rows. | D | PASS | 4.9 s (was ~0.1 s; two new scans) |
| 26 | **rollback_check query 2 with post-release activity (should-fix 2)**. A real extraction save after release: candidate 13965 of ACC-CO-LED-03-08090 -> `review`, duplicate_of 515238, 3 staging rows superseded (duplicate_item_set_of_sibling). After the rollback, query 2 lists 6 rows: 2 skipped venues (ACC-CO-LED-03-00124 newer_menu, ACC-CO-LED-01-55836 multi_current_backup), 2 staging_page_not_restored, **candidate_marked_duplicate** "candidate 13965 (review, duplicate of 515238, attempts 0): http://9thdoorcapitolhill.com/menu", and **staging_superseded_after_release** "http://9thdoorcapitolhill.com/menu (3 rows ...)". | G | PASS | 4.6 s |
| 27 | G rollback with skips: 346 rolled back; 30,124 staging rows restored; the re-extracted page of ACC-CO-LED-01-65702 stayed superseded. | G | PASS | 6.7 s |
| 28 | **rollback_check query 3 (m3, save before DROP)**: creates phg_repair_rollback_saved_20260927 and returns 1 row. Run steps [rollback, step2]; review list = the query-2 rows (0 in D; 6 candidates / reasons matching in G); service_role SELECT only (insert / trigger false). | D, G | PASS | 6.1 / 7.5 s |
| 29 | **Roll-forward RF2 (should-fix 2 + m2)**, after a real promote, an extraction save and one step-4 call: `lock_timeout` in effect is 5s. Reset to retry: 1 row (candidate 13965: review -> retry, next retry due now, last_error "PHG-026 roll-forward: was Same priced items as candidate 515238 ..."). Then the hash reset: 301 rows, 0 left. | E | PASS | 5.0 s (reset 30 ms, hashes 2.0 s) |
| 30 | promote_clean_menu_batch(1) against a re-queued item-page sibling: duplicate 1, current menu unchanged, 0 venues with two current menus. | E | PASS | 4.3 s |
| 31 | Function rollback returns 4. The index is gone, the 10-arg submit_menu is back and the live body is restored. anon / authenticated have no EXECUTE; service_role has EXECUTE. submit_menu afterwards -> created. | D, E | PASS | 25 / 19 ms; submit 24 / 29 ms |
| 32 | Score gate (file 3, unchanged): approve path, layout gates, blocked at 80, approved at 90, rollback returns 3. | F | PASS | 90 ms |

**Lock timeout on block C's first try.** File 1 stopped at 3,075 ms with `55P03 canceling statement due to lock
timeout`, because another session held a lock on one of the tables for more than 3 s. The whole block rolled back.
pg_stat_activity was empty a moment later, and the unchanged block then passed. This is the "55P03: nothing changed,
re-run" path in the file 2 header, seen on live traffic.

## Per-block wall time (all under the 58 s budget)

| Block | Contents | Approx. total |
|---|---|---|
| A | file 1 + scenarios s1-s13d + config checks | ~1.7 s |
| B | files 1-2 + checks + monitor (real and forged) + replay | ~15 s |
| C | files 1-2 + one step-3 call + one step-4(500) call | ~37 s |
| D | files 1-2 + step 3 + index + gate + rollback + rollback_check q1-q3 + function rollback | ~50 s |
| E | files 1-2 + promote + extraction + step 4(200) + RF2 + function rollback | ~31 s |
| F | file 3 + approve path + rollback | ~0.1 s |
| G | files 1-2 + step 3 + post-release extraction + rollback with skips + rollback_check q1-q3 | ~50 s |
