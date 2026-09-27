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
