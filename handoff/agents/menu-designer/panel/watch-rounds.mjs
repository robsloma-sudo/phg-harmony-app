// Watches a running menu-review-panel workflow and reports every completed round.
//   node watch-rounds.mjs <workflow transcript dir>
// For each round it saves the exact render the 15 reviewers scored to out/panel/rounds/rNN-<menu>/ (page PNGs, phone,
// scores.json) and prints ONE line: ROUND n · menu · PASS|FAIL · per-reviewer scores · files.
// Snapshot rule: a menu's render only changes when a round's "improve" step re-renders, so the renders captured right
// after round N's improve result are exactly what round N+1 reviews. Round 1 was snapshotted before the watcher started.
// State in out/panel/rounds/watch-state.json keeps re-arms from repeating lines or re-snapshotting.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(here, '../out/panel');
const ROUNDS = path.join(OUT, 'rounds');
const PENDING = path.join(ROUNDS, 'pending');
const STATE = path.join(ROUNDS, 'watch-state.json');
const MENUS = ['sample-bar', 'casa-luna', 'high-altitude'];
const journal = path.join(process.argv[2], 'journal.jsonl');
const NAMES = { design_theory: 'Design Theory', beverage: 'Cocktail & Beverage', concept_brand: 'Concept & Brand' };

fs.mkdirSync(PENDING, { recursive: true });
const state = fs.existsSync(STATE) ? JSON.parse(fs.readFileSync(STATE, 'utf8')) : { emitted: [], improved: [] };
const save = () => fs.writeFileSync(STATE, JSON.stringify(state, null, 2));
const pad = n => String(n).padStart(2, '0');

function copyRender(menu, dest) {
  const src = path.join(OUT, menu, 'current', 'option-A');
  fs.mkdirSync(dest, { recursive: true });
  for (const f of fs.readdirSync(src)) if (/^page-\d+\.png$|^phone\.png$/.test(f)) fs.copyFileSync(path.join(src, f), path.join(dest, f));
}

function tick() {
  if (!fs.existsSync(journal)) return;
  const lines = fs.readFileSync(journal, 'utf8').split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  const label = {}; const results = {};
  for (const l of lines) {
    if (l.type === 'started' && l.agentId) label[l.agentId] = l.label;
    if (l.type === 'result' && l.agentId) results[l.agentId] = l.result;
  }
  const rounds = {};
  for (const [id, lab] of Object.entries(label)) {
    let m = /^r(\d+) (\S+) · (\w+) (\d)$/.exec(lab || '');
    if (m) { const r = +m[1]; rounds[r] = rounds[r] || { menu: m[2], reviews: [], improveStarted: false, improve: undefined }; if (id in results) rounds[r].reviews.push({ reviewer: m[3], n: +m[4], ...(results[id] || { score: null }) }); continue; }
    m = /^r(\d+) improve \((\S+)\)$/.exec(lab || '');
    if (m) { const r = +m[1]; rounds[r] = rounds[r] || { menu: m[2], reviews: [] }; rounds[r].improveStarted = true; if (id in results) rounds[r].improve = results[id]; }
  }
  const maxRound = Math.max(0, ...Object.keys(rounds).map(Number));
  for (const r of Object.keys(rounds).map(Number).sort((a, b) => a - b)) {
    const R = rounds[r];
    // a round's reviews are complete when all 15 answered, or when its improve step / the next round has started
    const done = R.reviews.length >= 15 || R.improveStarted || r < maxRound;
    if (done && !state.emitted.includes(r)) {
      const dir = path.join(ROUNDS, `r${pad(r)}-${R.menu}`);
      if (!fs.existsSync(path.join(dir, 'page-1.png'))) {
        const pend = path.join(PENDING, R.menu);
        if (fs.existsSync(path.join(pend, 'page-1.png'))) { fs.mkdirSync(dir, { recursive: true }); for (const f of fs.readdirSync(pend)) fs.copyFileSync(path.join(pend, f), path.join(dir, f)); }
        else copyRender(R.menu, dir);             // no improve has run since the first render: current is what was reviewed
      }
      const by = {};
      for (const v of R.reviews) if (typeof v.score === 'number') (by[v.reviewer] = by[v.reviewer] || []).push(Math.round(v.score));
      const all = Object.values(by).flat();
      const pass = all.length === 15 && Math.min(...all) >= 80;
      const parts = Object.keys(NAMES).map(k => { const s = by[k] || []; const mean = s.length ? (s.reduce((a, b) => a + b, 0) / s.length).toFixed(1) : '—'; return `${NAMES[k]} ${mean} (${s.join(', ')})`; });
      const subs = {};
      for (const v of R.reviews) for (const [k, x] of Object.entries(v.subscores || {})) if (typeof x === 'number') (subs[k] = subs[k] || []).push(x);
      const weakest = Object.entries(subs).map(([k, v]) => [k, Math.round(v.reduce((a, b) => a + b, 0) / v.length)]).sort((a, b) => a[1] - b[1]).slice(0, 4).map(([k, v]) => `${k} ${v}`).join(', ');
      fs.writeFileSync(path.join(dir, 'scores.json'), JSON.stringify({ round: r, menu: R.menu, pass, by, lowest: all.length ? Math.min(...all) : null, weakest, reviews: R.reviews }, null, 2));
      const files = fs.readdirSync(dir).filter(f => /^page-\d+\.png$/.test(f)).map(f => path.join(dir, f)).join(',');
      console.log(`ROUND ${r} · ${R.menu} · ${pass ? 'PASS' : 'FAIL'} · ${parts.join(' · ')} · lowest ${all.length ? Math.min(...all) : '—'} · weakest: ${weakest} · files: ${files}`);
      state.emitted.push(r); save();
    }
    if (R.improve !== undefined && !state.improved.includes(r)) {
      // improve finished (re-render + commit done): these renders are what the next round reviews
      for (const m of MENUS) { fs.rmSync(path.join(PENDING, m), { recursive: true, force: true }); copyRender(m, path.join(PENDING, m)); }
      const ch = (R.improve && R.improve.changes) || [];
      console.log(`IMPROVED after round ${r} · ${ch.length} change(s): ${ch.slice(0, 4).join(' | ').slice(0, 600)} · tests: ${(R.improve && R.improve.tests) || '?'}`);
      state.improved.push(r); save();
    }
  }
}

setInterval(() => { try { tick(); } catch (e) { console.log(`WATCHER ERROR ${e.message}`); } }, 2000);
try { tick(); } catch (e) { console.log(`WATCHER ERROR ${e.message}`); }
