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
