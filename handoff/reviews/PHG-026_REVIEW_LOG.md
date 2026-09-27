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
