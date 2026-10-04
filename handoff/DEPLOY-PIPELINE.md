PHG Harmony app — how production deploys (verified 2026-10-04)
A commit to `main` in this repository goes live on prismatic-rugelach-777e48.netlify.app.
Evidence: Netlify deploy `6ac28f30bdf145000863da95` (current production at the time of writing)
has `branch: main`, `commit_ref: b351ee86f154a7b3de1d6c61754a5267120b1fb7`, `context: production`,
`manual_deploy: false`. The live `index.html` md5 `92d742574c35df94ae85dda5693526f4` equals
`main:index.html`. Rob confirmed on 2026-10-04: "uploading to GitHub does update directly to Netlify".
What this changes
`main` is now the source of production. Anything merged or uploaded to `main` ships.
The older rule "Netlify is the source of truth, GitHub does nothing" is out of date.
The drag-and-drop of the whole deploy folder is no longer the normal path.
It still works as an emergency path, but the next push to `main` will overwrite it.
If anyone deploys by hand, commit the same files to `main` straight away.
Rules that still apply (phg-deploy-verification skill)
Read `CHANGELOG.txt` from the newest post in Slack #phg-ops first. Check the `Follows:` chain.
Announce "Deploying new update" with the proposed entry in #phg-admin and #phg-ops.
Hash live, `main:index.html` and the newest #phg-ops `index.html`. Understand any difference.
Build on the live file. The diff must show only your change.
Protected code counts must not drop: `phgAccessContext`, `phgInvOpen`, `PHGAUTH.noAccess`,
`phgNoAccessHTML`, `phgUpdOpen`, `phgUpdBtnHTML`, `PHG_ADMIN_URL`, plus style/script tag counts.
Pre-deploy checks (node --check, tag counts, no duplicate definitions, secret scan).
Commit to `main`. One commit per deploy, message names the change and the DEV ref.
Post-deploy: Netlify deploy for that commit is `ready` and published; live md5 equals the
committed file; protected counts unchanged; assets return 200.
Append the entry to `CHANGELOG.txt` and upload it (and `index.html`) to #phg-ops.
Rollback: Netlify > prismatic-rugelach > Deploys > previous deploy > Publish,
then revert the commit on `main` so the next push does not re-ship the bad version.
This repository is public
Never commit keys, tokens or passwords. Keys needed by the page are injected at build time
from Netlify environment variables, never written into the HTML.
Internal notes live under `/handoff/`, which `netlify.toml` blocks from being served (404).
