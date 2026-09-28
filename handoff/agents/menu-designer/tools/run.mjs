// One command from Harmony voice (or an agent_tasks payload) to a finished proposal.
//
//   node run.mjs --transcript "For cocktails we have the Paloma twelve…" --out ../out/casa-luna
//   node run.mjs --task task.json --demographics census.json --comparables refs.json --out ../out/job-123
//
// Options:
//   --transcript <text> | --transcript-file <path>   Harmony speech-to-text (phg-speech-transcribe / interpreter text)
//   --task <path>            agent_tasks row or its input_payload (brief §4)
//   --venue "<name>" --venue-type <type> --city <c> --state <st> --zip <zip>   fill venue facts the voice didn't carry
//   --legal "line one | line two"   exact legal lines supplied by the venue (never written by the designer)
//   --demographics <path>    phg_census_zcta row for the venue ZIP (see references.sql)
//   --comparables <path>     library rows used as references (see references.sql) — cited in the proposal
//   --look <key>             force one look (noir, cantina, taproom, cellar, grand, coastal, tavern, tropic, minimal, deco)
//   --options <1-3>          number of alternatives (default 3; 1 when --look is given)
//   --no-render              design only (fast), skip PNG/PDF
//   --task-id <uuid> --target-record-id <uuid>   carried into the proposal row
//
// Output (in --out): option-A/…: menu.menu.json, page-N.png, menu.pdf, menu-print.pdf, phone.png, render.json
//                    request.json, proposal.json (agent_proposals row), proposal.sql (the one INSERT allowed), SUMMARY.md

import fs from 'node:fs';
import path from 'node:path';
import { parseTranscript } from './parse-voice.mjs';
import { design } from './design.mjs';
import { render } from './render.mjs';
import { buildProposal, proposalSQL, summaryMarkdown } from './proposal.mjs';

const args = process.argv.slice(2);
const opt = (k, d = null) => { const i = args.indexOf('--' + k); return i >= 0 ? (args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true) : d; };
const readJSON = p => p ? JSON.parse(fs.readFileSync(p, 'utf8')) : null;

const t0 = Date.now();
let input, parsed = null;
const transcript = opt('transcript') || (opt('transcript-file') ? fs.readFileSync(opt('transcript-file'), 'utf8') : null);
if (transcript) { parsed = parseTranscript(transcript); input = parsed; }
else if (opt('task')) { const t = readJSON(opt('task')); input = t.input_payload || t.request || t; }   // agent_tasks row, payload, or an edited request.json
else { console.error('Give --transcript, --transcript-file or --task'); process.exit(2); }

const out = path.resolve(opt('out', '../out/' + new Date().toISOString().replace(/[:.]/g, '-')));
fs.mkdirSync(out, { recursive: true });

const dem = readJSON(opt('demographics'));
const refs = readJSON(opt('comparables')) || [];
const venue = { name: opt('venue'), type: opt('venue-type'), city: opt('city'), state: opt('state'), zip: opt('zip') };
const legal = opt('legal') ? { legal_lines: String(opt('legal')).split('|').map(s => s.trim()).filter(Boolean) } : null;
const final = design(input, { look: opt('look'), options: Number(opt('options', 0)) || undefined, venue,
                              demographics: dem ? (Array.isArray(dem) ? dem[0] : dem) : null, constraints: legal });

fs.writeFileSync(path.join(out, 'request.json'), JSON.stringify({ parsed, request: final.request }, null, 2));
for (const o of final.options) {
  const dir = path.join(out, `option-${o.option}`);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'menu.menu.json'), JSON.stringify(o.menu_studio_file, null, 2));
  if (!args.includes('--no-render')) {
    o.render = await render(o.menu_studio_file, dir);
    if (o.render.wide_lines.length) { o.risk_flags.push('lines_exceed_column'); if (!final.risk_flags.includes('lines_exceed_column')) final.risk_flags.push('lines_exceed_column'); }
    else o.risk_flags = o.risk_flags.filter(f => f !== 'lines_may_exceed_column');
  }
}
if (!args.includes('--no-render') && final.options.every(o => !o.risk_flags.includes('lines_may_exceed_column'))) final.risk_flags = final.risk_flags.filter(f => f !== 'lines_may_exceed_column');

const proposal = buildProposal(final, { refs, taskId: opt('task-id'), targetRecordId: opt('target-record-id'), outDir: out, parsed });
fs.writeFileSync(path.join(out, 'proposal.json'), JSON.stringify(proposal, null, 2));
fs.writeFileSync(path.join(out, 'proposal.sql'), proposalSQL(proposal));
fs.writeFileSync(path.join(out, 'SUMMARY.md'), summaryMarkdown(final, proposal, { ms: Date.now() - t0 }));
console.log(fs.readFileSync(path.join(out, 'SUMMARY.md'), 'utf8'));
console.log(`\nOutput: ${out}`);
