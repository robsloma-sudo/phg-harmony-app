// One command from a Harmony voice note or a phg.menu_design_tasks row to a finished, self-checked proposal.
//
//   Voice (user side, Harmony viewport menu builder):
//     node run.mjs --transcript-file note.txt [--base-doc draft.json] --venue-type latin_cantina --city Denver --state CO \
//                  --demographics census.json --comparables refs.json --out ../out/casa-luna
//     -> request_design.json : the body the app sends to phg-menu-design {action:'request_design'} (creates the task
//                              with phg_design_task_create, source 'user_prompt_flow', source_detail 'harmony_voice')
//     -> the design the Designer would propose for that task (below)
//
//   Task (designer side):
//     node run.mjs --task-row task.json --demographics census.json --comparables refs.json --out ../out/<task>
//     task.json is a phg.menu_design_tasks row read through phg_designer_query ({id, request, source, inputs, base_doc, ...}).
//
// Output: SUMMARY.md, request.json, submit.json (phg_design_proposal_submit arguments incl. p_layout), submit.sql
//         (for the Coordinator), and option-X/: menu.menu.json, page-N.png (300 dpi), menu.pdf, menu-print.pdf,
//         phone.png, layout.json (scorecard geometry), selfcheck.json, render.json.
// Options: --look <key>  --options 1-3  --legal "line | line"  --standards specs.json  --no-render  --task-id <uuid>

import fs from 'node:fs';
import path from 'node:path';
import { design } from './design.mjs';
import { render } from './render.mjs';
import { buildProposal, summaryMarkdown } from './proposal.mjs';
import { requestDesignPayload, taskToRequest, submitPayload, submitSQL, docCheck, stripSecrets } from './handoff.mjs';
import { selfcheck } from './selfcheck.mjs';

const args = process.argv.slice(2);
const opt = (k, d = null) => { const i = args.indexOf('--' + k); return i >= 0 ? (args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true) : d; };
const readJSON = p => p ? JSON.parse(fs.readFileSync(p, 'utf8')) : null;
const t0 = Date.now();

const venueFacts = { name: opt('venue'), type: opt('venue-type'), city: opt('city'), state: opt('state'), zip: opt('zip'), website: opt('website') };
const legal = opt('legal') ? String(opt('legal')).split('|').map(s => s.trim()).filter(Boolean) : null;
const out = path.resolve(opt('out', '../out/' + new Date().toISOString().replace(/[:.]/g, '-')));
fs.mkdirSync(out, { recursive: true });

// ---- 1. the task (real row, or the one the app would create from this voice note)
let task, requestBody = null, parsedFor = null;
const transcript = opt('transcript') || (opt('transcript-file') ? fs.readFileSync(opt('transcript-file'), 'utf8') : null);
if (transcript) {
  requestBody = requestDesignPayload(transcript, { venue: Object.fromEntries(Object.entries(venueFacts).filter(([, v]) => v)) });
  const { _parser, ...body } = requestBody;
  fs.writeFileSync(path.join(out, 'request_design.json'), JSON.stringify({ action: 'request_design', ...body }, null, 2));
  parsedFor = _parser;
  const base = readJSON(opt('base-doc'));
  task = { id: opt('task-id'), request: body.request, source: body.source, source_detail: body.source_detail, inputs: body.inputs,
           base_doc: base ? (base.editor_state?.doc || base.doc || base) : null, base_revision: null };
} else if (opt('task-row') || opt('task')) {
  const t = readJSON(opt('task-row') || opt('task'));
  task = t.input_payload ? { id: t.id, request: t.input_payload.request || '', source: 'coordinator', inputs: t.input_payload, base_doc: null } : t;
} else { console.error('Give --transcript, --transcript-file or --task-row'); process.exit(2); }

// ---- 2. design
const req = taskToRequest(task);
if (parsedFor) req.questions = parsedFor.questions.filter(q => !(task.base_doc && /No menu items were heard/.test(q)));
const dem = readJSON(opt('demographics'));
const refs = readJSON(opt('comparables')) || [];
const standards = readJSON(opt('standards'));          // classic specs (references.sql §8), used only where no description exists
const result = design(req, { look: opt('look'), options: Number(opt('options', 0)) || undefined,
  venue: venueFacts, demographics: dem ? (Array.isArray(dem) ? dem[0] : dem) : null, constraints: legal ? { legal_lines: legal } : null, standards });
fs.writeFileSync(path.join(out, 'request.json'), JSON.stringify({ task: { ...task, base_doc: task.base_doc ? '(draft document, secrets stripped: base_doc.json)' : null }, request: { ...result.request, base_doc: undefined } }, null, 2));
if (task.base_doc) fs.writeFileSync(path.join(out, 'base_doc.json'), JSON.stringify(stripSecrets(task.base_doc), null, 2));

// ---- 3. render, measure, self-check every option
for (const o of result.options) {
  const dir = path.join(out, `option-${o.option}`);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'menu.menu.json'), JSON.stringify({ ...o.menu_studio_file, doc: stripSecrets(o.menu_studio_file.doc) }, null, 2));
  if (args.includes('--no-render')) continue;
  o.render = await render(o.menu_studio_file, dir);
  o.layout = o.render.layout;
  o.selfcheck = selfcheck(o.layout, o.menu_studio_file, { base_doc: task.base_doc, inputs: task.inputs });
  fs.writeFileSync(path.join(dir, 'selfcheck.json'), JSON.stringify(o.selfcheck, null, 2));
  if (o.render.wide_lines.length) o.risk_flags.push('lines_exceed_column');
  else o.risk_flags = o.risk_flags.filter(f => f !== 'lines_may_exceed_column');
  if (!o.selfcheck.ok) o.risk_flags.push('selfcheck_failures');
}
if (!args.includes('--no-render')) result.risk_flags = result.risk_flags.filter(f => f !== 'lines_may_exceed_column');
result.risk_flags = [...new Set([...result.risk_flags, ...result.options.flatMap(o => o.risk_flags)])];

// ---- 4. proposal -> submit arguments for the Coordinator
const proposal = buildProposal(result, { refs, taskId: task.id, outDir: out, parsed: null });
const primary = result.options[0];
const previews = primary.render ? { dir: path.relative(process.cwd(), out), pages: primary.render.files.filter(f => /^page-\d+\.png$/.test(f)).map(f => `option-${primary.option}/${f}`),
  pdf: `option-${primary.option}/menu.pdf`, print_pdf: `option-${primary.option}/menu-print.pdf`, phone: `option-${primary.option}/phone.png`,
  dpi: primary.render.dpi, pixel_size: primary.render.pixel_size, note: 'Local paths in the designer output; the Coordinator uploads them to storage.' } : null;
const submit = submitPayload(task.id || null, result, proposal, { layout: primary.layout || null, previews });
submit.p_changes.selfcheck = primary.selfcheck ? { ok: primary.selfcheck.ok, failed: primary.selfcheck.failed, fixes: primary.selfcheck.fixes } : null;
fs.writeFileSync(path.join(out, 'submit.json'), JSON.stringify(submit, null, 2));
fs.writeFileSync(path.join(out, 'submit.sql'), submitSQL(submit));
const pre = docCheck(submit.p_doc, task.base_doc, task.inputs);

let md = summaryMarkdown(result, proposal, { ms: Date.now() - t0 });
md += `\n## Hand-off\n- Database automatic check (local copy): ${pre.ok ? 'passes' : 'FAILS: ' + pre.problems.join('; ')}\n`;
for (const o of result.options) if (o.selfcheck) md += `- Option ${o.option} scorecard self-check: ${o.selfcheck.checks - o.selfcheck.failed}/${o.selfcheck.checks} measured checks pass${o.selfcheck.fixes.length ? '. Fix: ' + o.selfcheck.fixes.slice(0, 4).join(' | ') : ''}\n`;
if (requestBody) md += `- request_design.json: the body the app sends to create this task (source user_prompt_flow / harmony_voice).\n`;
md += `- submit.json / submit.sql: phg_design_proposal_submit arguments for the Coordinator (p_layout included).\n`;
fs.writeFileSync(path.join(out, 'SUMMARY.md'), md);
console.log(md);
console.log(`Output: ${out}`);
