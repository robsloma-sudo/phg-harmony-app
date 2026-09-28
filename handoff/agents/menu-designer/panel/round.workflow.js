export const meta = {
  name: 'menu-review-panel',
  description: 'Menu review panel: 15 reviews per round (3 reviewers x 5 lenses), gate 80 on every review; designer improves the toolkit between rounds',
  phases: [{ title: 'Review', detail: '15 parallel reviews of the current menu' }, { title: 'Improve', detail: 'designer turns fixes into toolkit improvements and re-renders' }],
}

const ROOT = '/home/user/phg-harmony-app/handoff/agents/menu-designer'
const MAX_ROUNDS = (args && args.maxRounds) || 25
const START = (args && args.startRound) || 1
const MENUS = (args && args.menus) || ['sample-bar', 'casa-luna', 'high-altitude']
const TRANSCRIPT = { 'sample-bar': 'sample-bar.voice.txt', 'casa-luna': 'casa-luna.voice.txt', 'high-altitude': 'high-altitude.voice.txt' }

const REVIEWERS = [
  { key: 'design_theory', title: 'Reviewer 1 — Design Theory', lenses: [
    'Swiss grid and typographic purist (Muller-Brockmann)', 'Colour theorist (Albers; contrast and harmony)',
    'Editorial art director (magazine hierarchy)', 'Legibility and accessibility specialist (WCAG, low light, older readers)',
    'Butterick / Bringhurst typographer'] },
  { key: 'beverage', title: 'Reviewer 2 — Cocktail & Beverage', lenses: [
    'Head bartender of a top craft cocktail bar', 'Beverage director (whole program)', 'Sommelier (wine list)',
    'Cicerone (beer list)', 'Zero-proof / NA program specialist'] },
  { key: 'concept_brand', title: 'Reviewer 3 — Concept & Brand', lenses: [
    'Hospitality brand strategist', 'Restaurant menu engineer (pricing and placement)', 'Print production manager',
    'Guest in the room (low light, first visit)', 'Agency creative director'] },
]

const REVIEW_SCHEMA = { type: 'object', properties: {
  score: { type: 'number' }, subscores: { type: 'object' },
  strengths: { type: 'array', items: { type: 'string' } }, fixes: { type: 'array', items: { type: 'string' } } },
  required: ['score', 'subscores', 'fixes'] }
const IMPROVE_SCHEMA = { type: 'object', properties: {
  changes: { type: 'array', items: { type: 'string' } }, tests: { type: 'string' }, committed: { type: 'boolean' },
  filed_for_lead_dev: { type: 'array', items: { type: 'string' } } }, required: ['changes', 'tests', 'committed'] }

function reviewPrompt(menu, rv, lens, round) {
  const dir = `${ROOT}/out/panel/${menu}/current`
  return `You are one of 15 independent reviewers on the PHG menu review panel, round ${round}.
Role: ${rv.title}. Your lens: ${lens}. Read ${ROOT}/REVIEW_PANEL.md (your reviewer's subscores and the scoring bands) and score only against it. Be demanding and specific; you are read-only (do not modify any file).
Menu under review: "${menu}" (a fictional sample venue made from a voice note; option A is the recommended design).
Files (read what your role needs; keep it quick — this round has a 5-minute budget):
- Page images at 300 dpi: ${dir}/option-A/page-1.png (and page-2.png if present); phone view: ${dir}/option-A/phone.png
- The menu document, reasoning, questions and risk flags: ${dir}/submit.json (p_doc, p_reasoning, p_changes.questions, p_changes.menu_studio.style, p_risk_flags)
- Measured geometry and self-check: ${dir}/option-A/layout.json, ${dir}/option-A/selfcheck.json
- What the venue said: ${ROOT}/examples/${TRANSCRIPT[menu]} and ${dir}/request_design.json
Menu Studio limits (judge what is on the page, but name the limit in your fix if it costs points): 8 system fonts, no ornaments/images, one-line descriptions, prices inline beside names above one column, non-integer prices print with two decimals.
Return JSON: score (0-100, the mean of your subscores), subscores (your reviewer's subscore keys, each 0-100), strengths (max 3), fixes (3-8 specific, actionable changes, most important first).`
}

function improvePrompt(menu, round, digest) {
  return `You are the PHG Menu Designer improving after review round ${round} of the menu review panel (${ROOT}/REVIEW_PANEL.md). Menu reviewed: "${menu}". Gate: every one of 15 reviews must be >= 80.
Round digest (per-reviewer scores, lowest subscores, and fixes grouped by frequency):
${digest}

Your job this round (keep it to about 3 minutes of work — the whole round has a 5-minute budget):
0. Read the last two entries of ${ROOT}/PANEL_LOG.md: their "Open, carried" items are yours too when they raise the lowest scores.
1. Pick the 3-5 changes that will raise the lowest scores the most across ALL menus. Prefer general improvements to the toolkit in ${ROOT}/tools and ${ROOT}/styles (design rules, looks, parser, layout decisions) over one-off tweaks, so every future menu improves.
2. Content gaps on these fictional sample venues (missing descriptions, ABV, garnish, producer/region, spirit type/age) may be closed by appending realistic, factually correct sentences to the sample transcript in ${ROOT}/examples/ (e.g. real ABV/style of real products; plausible house-cocktail garnishes), as if the sample venue answered the designer's questions. Never do this for a real venue, never change a price, never touch ${ROOT}/examples/live-draft-*.
3. Hard rules: do NOT modify /home/user/phg-harmony-app/index.html, supabase/, netlify.toml, workers/ or .github/; never write to Supabase. Menu Studio limits you cannot fix in the toolkit go into ${ROOT}/SUGGESTIONS_FOR_LEAD_DEV.md (append or extend an S-item) and into filed_for_lead_dev.
4. Run: cd ${ROOT}/tools && node test.mjs — all tests must pass (add a test for any new behaviour). Then re-render every panel menu: bash ${ROOT}/panel/render-all.sh.
5. Append a round entry to ${ROOT}/PANEL_LOG.md: round ${round}, menu, per-reviewer scores (from the digest), what you changed, what you filed, and an "Open, carried to later rounds" list.
6. Commit (do not push): cd /home/user/phg-harmony-app && git add handoff/agents/menu-designer && git commit -m "Menu Designer panel round ${round}: <summary>" with the lines "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" and "Claude-Session: https://claude.ai/code/session_01XZinUdHQBvE68eHnB6xr16".
Return JSON: changes, tests (the test summary line), committed, filed_for_lead_dev.`
}

function digestOf(reviews) {
  const lines = []
  for (const rv of REVIEWERS) {
    const rs = reviews.filter(r => r && r.reviewer === rv.key)
    if (!rs.length) continue
    const mean = Math.round(rs.reduce((a, r) => a + r.score, 0) / rs.length * 10) / 10
    lines.push(`${rv.title}: scores ${rs.map(r => Math.round(r.score)).join(', ')} (mean ${mean})`)
    const subs = {}
    for (const r of rs) for (const [k, v] of Object.entries(r.subscores || {})) { if (typeof v === 'number') (subs[k] = subs[k] || []).push(v) }
    lines.push('  lowest subscores: ' + Object.entries(subs).map(([k, v]) => [k, Math.round(v.reduce((a, b) => a + b, 0) / v.length)]).sort((a, b) => a[1] - b[1]).slice(0, 4).map(([k, v]) => `${k} ${v}`).join(', '))
    for (const r of rs) lines.push(`  [${r.lens}] ${Math.round(r.score)}: ${(r.fixes || []).slice(0, 5).join(' | ')}`)
  }
  return lines.join('\n')
}

const status = Object.fromEntries(MENUS.map(m => [m, { passed: false, rounds: [] }]))
const history = []
let turn = (args && args.turnOffset != null) ? args.turnOffset : START - 1   // keeps the menu rotation across relaunches
for (let round = START; round < START + MAX_ROUNDS; round++) {
  const open = MENUS.filter(m => !status[m].passed)
  if (!open.length) { log('Every menu passed the panel.'); break }
  const menu = open[turn % open.length]; turn++

  const reviews = await parallel(REVIEWERS.flatMap(rv => rv.lenses.map((lens, i) => () =>
    agent(reviewPrompt(menu, rv, lens, round), { phase: 'Review', label: `r${round} ${menu} · ${rv.key} ${i + 1}`, schema: REVIEW_SCHEMA, effort: 'medium' })
      .then(r => r ? { ...r, reviewer: rv.key, lens } : null))))
  const got = reviews.filter(Boolean)
  // A round where most reviewers errored (usage limit, API failure) judged nothing: stop instead of burning rounds.
  if (got.length < 10) { log(`Round ${round} · ${menu}: only ${got.length}/15 reviews returned; stopping the loop (agent errors).`); history.push({ round, menu, aborted: true, returned: got.length }); break }
  const min = got.length ? Math.min(...got.map(r => r.score)) : 0
  const means = Object.fromEntries(REVIEWERS.map(rv => { const rs = got.filter(r => r.reviewer === rv.key); return [rv.key, rs.length ? Math.round(rs.reduce((a, r) => a + r.score, 0) / rs.length * 10) / 10 : null] }))
  const pass = got.length === 15 && min >= 80
  log(`Round ${round} · ${menu}: ${got.length}/15 reviews · means ${JSON.stringify(means)} · lowest ${Math.round(min)} · ${pass ? 'PASS' : 'fail'}`)
  const entry = { round, menu, means, min: Math.round(min), pass, scores: got.map(r => ({ reviewer: r.reviewer, lens: r.lens, score: Math.round(r.score) })) }
  status[menu].rounds.push(entry)
  if (pass) { status[menu].passed = true; history.push(entry); continue }

  const imp = await agent(improvePrompt(menu, round, digestOf(got)), { phase: 'Improve', label: `r${round} improve (${menu})`, schema: IMPROVE_SCHEMA })
  entry.improve = imp
  history.push(entry)
  if (!imp) { log(`Round ${round} improve step returned nothing; stopping so a half-applied change is not reviewed.`); break }
  if (imp) log(`Round ${round} improvements: ${(imp.changes || []).slice(0, 5).join('; ')} · tests: ${imp.tests}`)
}
return { history, status: Object.fromEntries(Object.entries(status).map(([k, v]) => [k, { passed: v.passed, last: v.rounds[v.rounds.length - 1] || null }])) }
