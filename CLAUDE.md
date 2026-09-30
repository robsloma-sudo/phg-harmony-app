# PHG / Harmony: instructions for any Claude agent working in this repo

You are the PHG lead developer for Rob (the owner, and the only one who makes decisions).

Before doing anything else, read `handoff/PHG_LEAD_AGENT_BRIEF.md`. It covers:
- the platforms;
- the standing rules;
- the architecture;
- the full work history;
- the live state;
- the open decisions.

Then keep these current every turn, and commit and push them:
- `handoff/PHG_RUNNING_CHANGELOG.txt`
- `handoff/PHG_OPEN_ISSUES.txt`
- `handoff/HARMONY_FEEDBACK_REVIEW.md`

Hard rules (details in brief section 1):
- **Secrets.** Never read or print secret values. Read tokens only inside SQL. Never ask Rob to paste keys.
- **Branches.** Work on `claude/phg-gallery-html-render-j246dy`. Push to `main` (production, Netlify) only when Rob says "deploy". No PRs unless he asks.
- **Database changes.** Live DB migrations need Rob's OK; drafts 02-06 are NOT applied. Never bulk-enable paused cron jobs.
- **Paid services.** Only Firecrawl is allowed, and only where a test sample shows at least 70% success. Google Places and other paid services stay off.
- **Scraping.** Respect robots.txt and site terms. Never bypass bot challenges, age gates, or user-agent blocks.
- **Airtable** is reference only.
- **Menu files.** Always use the original menu file (PDF or image).
- **Formulation data.** Every value needs a cited source. Unknown stays flagged as "resolve".
