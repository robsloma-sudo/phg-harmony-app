// Builds the agent_proposals row (brief §5) from a design result. The designer's ONLY write is inserting this row.

import path from 'node:path';

// Blocking = the designer cannot finish without an answer, so the proposal goes back as needs_input.
const BLOCKING = ['missing_prices', 'unplaced_items', 'no_items', 'missing_venue_name', 'empty_list'];

export function buildProposal(result, { refs = [], taskId = null, targetRecordId = null, outDir = '.', parsed = null } = {}) {
  const req = result.request;
  const blocking = result.risk_flags.filter(f => BLOCKING.includes(f));
  const status = blocking.length ? 'needs_input' : 'submitted';
  const refIds = refs.map(r => r.document_id ?? r.id).filter(v => v !== undefined && v !== null);
  let confidence = 0.92 - 0.12 * blocking.length - 0.04 * (result.risk_flags.length - blocking.length) - (refIds.length >= 3 ? 0 : 0.08);
  confidence = Math.round(Math.max(0.2, Math.min(0.97, confidence)) * 100) / 100;
  const risk = [...result.risk_flags];
  if (refIds.length < 3) risk.push('fewer_than_3_library_references');

  const primary = result.options[0];
  const rel = p => path.relative(outDir, p) || '.';
  const options = result.options.map(o => ({
    option: o.option, look: o.look, look_label: o.look_label, look_note: o.look_note,
    menu_studio_file: o.menu_studio_file,
    preview: o.render ? {
      dpi: o.render.dpi, pixel_size: o.render.pixel_size, pages: o.render.files.filter(f => /^page-\d+\.png$/.test(f)).map(f => `option-${o.option}/${f}`),
      pdf: `option-${o.option}/menu.pdf`, print_pdf: `option-${o.option}/menu-print.pdf`, phone: `option-${o.option}/phone.png`,
      location: 'designer_output_dir', note: 'Full resolution, never downscaled. The Coordinator uploads these to storage; the designer does not write storage.',
    } : null,
    fit: { pages: o.fit.pages, columns: o.fit.cols, fill_of_last_page: o.fit.fill, adjustments: o.fit_log },
    risk_flags: o.risk_flags,
  }));

  const demo = req.demographics;
  const demoLine = demo ? `ZIP ${demo.zcta || req.venue.zip || '?'}: median income $${fmt(demo.median_household_income)}, median age ${demo.median_age}, ` +
    `21–34 share ${demo.pop_21_34_pct}%, $100k+ households ${demo.households_over_100k_pct}%, degree ${demo.bachelors_or_higher_pct}%, Hispanic/Latino ${demo.hispanic_latino_pct}%.` : 'No census row supplied for the venue ZIP.';
  const refLine = refIds.length
    ? `References studied (library document IDs): ${refIds.join(', ')}.` + (refs.some(r => r.note) ? ' ' + refs.filter(r => r.note).map(r => `#${r.document_id ?? r.id}: ${r.note}`).join(' ') : '')
    : 'No library references were supplied for this run.';

  const reasoning = [
    status === 'needs_input' ? `NEEDS INPUT. ${result.questions.join(' ')}` : null,
    `Recommended: Option ${primary.option}, ${primary.look_label}. ${primary.look_note}`,
    primary.why.length ? `Why: ${[...new Set(primary.why)].join('; ')}.` : null,
    demoLine,
    req.price_band ? `Price band given: ${JSON.stringify(req.price_band)}. Prices are shown exactly as supplied, with no dollar signs (Menu Studio prints bare numbers).` : 'Prices are shown exactly as supplied, with no dollar signs (Menu Studio prints bare numbers).',
    primary.changes.length ? `Layout decisions: ${primary.changes.join(' ')}` : null,
    primary.tuning.length ? `Adjustments: ${primary.tuning.join(' ')}` : null,
    primary.fit_log.length ? `Fit: ${primary.fit_log.join(', ')}.` : null,
    `Fits on ${primary.fit.pages} page(s), ${primary.fit.cols} column(s), ${result.size}.`,
    result.options.length > 1 ? `Alternatives: ${result.options.slice(1).map(o => `${o.option} ${o.look_label}`).join('; ')}.` : null,
    refLine,
    status !== 'needs_input' && result.questions.length ? `Open questions (non-blocking): ${result.questions.join(' ')}` : null,
  ].filter(Boolean).join('\n');

  return {
    proposal_id: `menu_design_${(taskId || 'adhoc').toString().slice(0, 8)}_${Date.now().toString(36)}`,
    task_id: taskId,
    proposal_type: 'menu_design',
    target_table: 'phg.menu_projects',
    target_record_id: targetRecordId,
    proposal_status: status,
    confidence,
    risk_flags: [...new Set(risk)],
    evidence_summary: refIds.length ? `Library documents studied: ${refIds.join(', ')}` : 'No library documents cited',
    reasoning_summary: reasoning,
    dedupe_key: `menu_design:${taskId || req.venue.name || 'adhoc'}:${hash(JSON.stringify(req.items))}`,
    proposed_data: {
      design_spec: primary.menu_studio_file,
      design_spec_format: 'Menu Studio file (app nbcc-menu-designer, schema_version 2). Load with Menu Studio > Open file, or apply doc/style/size to the draft.',
      preview: options[0].preview,
      options,
      changes: [...new Set(result.options.flatMap(o => o.changes))],
      questions: result.questions,
      source: { kind: parsed ? 'harmony_voice' : req.source, transcript: parsed ? parsed.transcript : null,
                heard_items: parsed ? parsed.sections.flatMap(s => s.items.map(i => ({ list: s.key, heard: i.heard }))) : null },
    },
  };
}

export function proposalSQL(p) {
  const j = v => v === null || v === undefined ? 'null' : `$mdz$${JSON.stringify(v)}$mdz$::jsonb`;
  const t = v => v === null || v === undefined ? 'null' : `$mdz$${v}$mdz$`;
  return `-- The PHG Menu Designer's only write: one proposal row. The Coordinator reviews and applies it.
insert into public.agent_proposals
  (proposal_id, task_id, proposal_type, target_table, target_record_id, proposed_data, evidence_summary,
   confidence, reasoning_summary, dedupe_key, risk_flags, proposal_status)
values
  (${t(p.proposal_id)}, ${p.task_id ? `${t(p.task_id)}::uuid` : 'null'}, 'menu_design', ${t(p.target_table)},
   ${p.target_record_id ? `${t(p.target_record_id)}::uuid` : 'null'}, ${j(p.proposed_data)}, ${t(p.evidence_summary)},
   ${p.confidence}, ${t(p.reasoning_summary)}, ${t(p.dedupe_key)},
   array[${p.risk_flags.map(f => `'${f.replace(/'/g, "''")}'`).join(', ')}]::text[], '${p.proposal_status}')
returning id, proposal_id, proposal_status;
`;
}

export function summaryMarkdown(result, p, { ms } = {}) {
  const req = result.request;
  const lines = [];
  lines.push(`# ${req.venue.name || 'Untitled venue'}: menu design proposal`);
  lines.push(`Status **${p.proposal_status}** · confidence ${p.confidence} · ${result.options.length} option(s) · ${req.items.length} items in ${new Set(req.items.map(i => i.list)).size} lists · ${result.size}${ms ? ` · built in ${(ms / 1000).toFixed(1)}s` : ''}`);
  if (result.questions.length) { lines.push('\n## Questions for the Coordinator'); for (const q of result.questions) lines.push(`- ${q}`); }
  lines.push('\n## Options');
  for (const o of result.options) {
    lines.push(`- **${o.option}: ${o.look_label}**: ${o.look_note} ${o.fit.pages} page(s), ${o.fit.cols} col.` +
      (o.render ? ` Preview ${o.render.pixel_size.join('×')} px @ ${o.render.dpi} dpi.` : '') + (o.risk_flags.length ? ` Flags: ${o.risk_flags.join(', ')}.` : ''));
    if (o.render && o.render.wide_lines.length) lines.push(`  - Lines wider than the column: ${o.render.wide_lines.map(w => `${w.item} (${w.kind}, +${w.over_px}px)`).join('; ')}`);
  }
  lines.push('\n## What was heard / supplied');
  const byList = {};
  for (const it of req.items) (byList[it.list || 'unplaced'] = byList[it.list || 'unplaced'] || []).push(it);
  for (const [l, arr] of Object.entries(byList)) {
    lines.push(`- **${l}**: ` + arr.map(i => `${i.name}${i.prices.length ? ' ' + i.prices.map(x => (x.label ? x.label + ' ' : '') + x.value).join('/') : ' (no price)'}${i.flags?.length ? ' [' + i.flags.join(', ') + ']' : ''}`).join(' · '));
  }
  lines.push('\n## Reasoning');
  lines.push(p.reasoning_summary);
  lines.push(`\nRisk flags: ${p.risk_flags.join(', ') || 'none'}`);
  return lines.join('\n') + '\n';
}

const fmt = n => (n === null || n === undefined) ? '?' : Number(n).toLocaleString('en-US');
function hash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36); }
