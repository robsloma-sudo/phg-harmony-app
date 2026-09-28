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
