// Bridges the toolkit to the live hand-off (supabase/migrations/20260928020000_phg_menu_design_handoff.sql,
// 20260928030000_phg_menu_design_score_gate.sql, Edge function phg-menu-design).
//
//   voice transcript ──► requestDesignPayload() ──► phg-menu-design {action:'request_design'} ──► phg_design_task_create
//   phg.menu_design_tasks row ──► taskToRequest() ──► design.mjs ──► submitPayload() ──► Coordinator calls
//                                                                    phg_design_proposal_submit(p_task_id, p_doc, …, p_layout)
// The designer never calls either write itself.

import { parseTranscript } from './parse-voice.mjs';

const nameKey = s => String(s || '').trim().toLowerCase().replace(/\s+/g, ' ');

// ---------------------------------------------------------------- voice -> task
// Body for POST phg-menu-design {action:'request_design'} (the app adds menu_project_id + sync_token).
// inputs.items[].prices MUST be plain numbers: phg_design_doc_check casts every element to numeric.
// Labels (Glass/Bottle, 4 Pack…) ride alongside in price_labels, index-matched.
export function requestDesignPayload(transcript, ctx = {}) {
  const parsed = parseTranscript(transcript);
  const items = [];
  for (const s of parsed.sections) for (const it of s.items) items.push(voiceItem(it, s.key));
  for (const it of parsed.unplaced_items) items.push(voiceItem(it, null));
  // Edits to existing items travel as name + flags (no price); the design check accepts them because the name is in
  // the draft, and no price is proposed.
  for (const e of parsed.edits || []) items.push(Object.defineProperty({ name: e.name, list: null, prices: [], flags: e.flags, edit: true }, '_heard', { value: e.heard, enumerable: false }));
  const d = parsed.design;
  const venue = { ...(ctx.venue || {}) };
  if (parsed.venue_name && !venue.name) venue.name = parsed.venue_name;
  if (parsed.venue_type && !venue.type) venue.type = parsed.venue_type;
  if (parsed.design.area && !venue.area) venue.area = parsed.design.area;
  const inputs = {
    items, lists: parsed.lists, venue,
    ...(parsed.menu_type ? { menu_type: parsed.menu_type } : {}),
    format: clean({ size: ['letter', 'legal', 'tabloid', 'half_letter', 'table_tent'].includes(d.format) ? d.format : undefined,
                    screen: ['phone', 'tablet', 'tv'].includes(d.format) ? d.format : undefined,
                    orientation: d.orientation || undefined, pages: d.pages || undefined, columns: d.columns || undefined }),
    brand: clean({ colours: d.colours.length ? d.colours.map(c => c.hex) : undefined, fonts: d.fonts.length ? d.fonts : undefined,
                   tone: d.tone.length ? d.tone : undefined }),
    constraints: clean({ hours: d.hours || undefined, no_dollar_signs: d.no_dollar_signs || undefined,
                         legal_lines: (d.legal_lines || []).length ? d.legal_lines : undefined }),
    // One pour size said for a whole list ("Drafts are poured at 16 ounces"): printed once under that heading.
    ...((parsed.pours || []).some(p => p.single) ? { pour_notes: parsed.pours.filter(p => p.single).map(p => ({ lists: p.lists, pours: p.pours, heard: p.heard, single: true })) } : {}),
  };
  return {
    request: String(transcript).trim().slice(0, 4000),
    source: 'user_prompt_flow',
    source_detail: 'harmony_voice',
    inputs,
    // not sent to the app: what the parser could not settle, for the Designer panel to show before sending
    _parser: { questions: parsed.questions, heard: items.map(i => i._heard) },
  };
}

function voiceItem(it, list) {
  const out = { name: it.name, list, prices: it.prices.map(p => p.value) };
  if (it.prices.some(p => p.label)) out.price_labels = it.prices.map(p => p.label || '');
  if (it.prices.length === 1) out.price = it.prices[0].value;
  if (it.description) out.description = it.description;
  if (it.sub) out.sub = it.sub;
  if (it.abv !== null && it.abv !== undefined) out.abv = it.abv;
  if (it.garnish) out.garnish = it.garnish;
  if (it.pour) out.pour = it.pour;
  if (it.flags && it.flags.length) out.flags = it.flags;
  Object.defineProperty(out, '_heard', { value: it.heard, enumerable: false });
  return out;
}
const clean = o => Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined));

// ---------------------------------------------------------------- task -> designer request
// Accepts a phg.menu_design_tasks row ({id, request, source, source_detail, inputs, base_doc, base_revision}).
export function taskToRequest(task) {
  const inp = task.inputs || {};
  const items = (inp.items || []).map(x => {
    const vals = Array.isArray(x.prices) ? x.prices.map(p => (p && typeof p === 'object') ? Number(p.value) : Number(p))
      : (x.price !== undefined && x.price !== null && x.price !== '') ? [Number(x.price)] : [];
    const labels = Array.isArray(x.price_labels) ? x.price_labels
      : Array.isArray(x.prices) ? x.prices.map(p => (p && typeof p === 'object') ? (p.label || '') : '') : [];
    return { edit: !!x.edit, name: x.name || x.item_name, description: x.description || x.desc || null, list: x.list || null, sub: x.sub || null,
             abv: x.abv ?? null, garnish: x.garnish || null, pour: x.pour || null, brand: x.brand || '', flags: x.flags || [],
             prices: vals.filter(v => isFinite(v)).map((v, i) => ({ label: labels[i] || '', value: v })) };
  });
  return {
    task_id: task.id || task.task_id || null,
    request: task.request || '', source: task.source || 'user_prompt_flow', source_detail: task.source_detail || null,
    venue: inp.venue || {}, menu_type: inp.menu_type || null, lists: inp.lists || [], items,
    price_band: inp.price_band || null, demographics: inp.demographics || null, brand: inp.brand || {},
    constraints: inp.constraints || {}, comparables: inp.comparables || [],
    format: { size: inp.format?.size || null, orientation: inp.format?.orientation || null, medium: inp.format?.screen ? 'screen' : 'print',
              screen: inp.format?.screen || null, pages: inp.format?.pages || null, columns: inp.format?.columns || null },
    base_doc: stripSecrets(task.base_doc || null), base_revision: task.base_revision ?? null,
    voice: inp.constraints?.hours ? { hours: inp.constraints.hours } : null, questions: [],
    pour_notes: Array.isArray(inp.pour_notes) ? inp.pour_notes : [],
  };
}

// The draft document carries doc.phg.sync_token (the Menu Studio project credential). It never leaves the designer:
// not in proposals, previews, logs or commits. The app restores doc.phg itself when it applies a design.
export function stripSecrets(doc) {
  if (!doc || typeof doc !== 'object') return doc;
  const d = JSON.parse(JSON.stringify(doc));
  delete d.phg;
  return d;
}

// ---------------------------------------------------------------- designer -> proposal (arguments for the Coordinator)
export function submitPayload(taskId, result, proposal, { layout, previews }) {
  const primary = result.options[0];
  return {
    p_task_id: taskId,
    p_doc: stripSecrets(primary.menu_studio_file.doc),
    p_options: result.options.slice(1).map(o => ({ option: o.option, look: o.look_label, doc: stripSecrets(o.menu_studio_file.doc),
      menu_studio: { size: o.menu_studio_file.size, style: o.menu_studio_file.style, preset: o.menu_studio_file.preset } })),
    // Menu Studio does not store a layout spec with the draft yet, so the look travels in `changes` (brief §5).
    p_changes: {
      summary: proposal.proposed_data.changes,
      menu_studio: { size: primary.menu_studio_file.size, style: primary.menu_studio_file.style, preset: primary.menu_studio_file.preset,
                     note: 'Apply size and style with the document; the doc alone keeps the draft\'s current look.' },
      questions: result.questions,
    },
    p_previews: previews,
    p_reasoning: proposal.reasoning_summary,
    p_evidence_document_ids: (proposal.evidence_ids || []).map(Number).filter(Number.isFinite),
    p_confidence: proposal.confidence,
    p_risk_flags: proposal.risk_flags,
    p_needs_input: proposal.proposal_status === 'needs_input',
    p_layout: layout,
  };
}

export function submitSQL(p) {
  const j = v => v === null || v === undefined ? 'null' : `$mdz$${JSON.stringify(v)}$mdz$::jsonb`;
  const t = v => v === null || v === undefined ? 'null' : `$mdz$${v}$mdz$`;
  return `-- For the Coordinator (service role). The designer does not run this.
select public.phg_design_proposal_submit(
  p_task_id => ${p.p_task_id ? `${t(p.p_task_id)}::uuid` : 'null /* task id */'},
  p_doc => ${j(p.p_doc)},
  p_options => ${j(p.p_options)},
  p_changes => ${j(p.p_changes)},
  p_previews => ${j(p.p_previews)},
  p_reasoning => ${t(p.p_reasoning)},
  p_evidence_document_ids => array[${p.p_evidence_document_ids.join(',')}]::bigint[],
  p_confidence => ${p.p_confidence},
  p_risk_flags => array[${p.p_risk_flags.map(f => `'${f.replace(/'/g, "''")}'`).join(', ')}]::text[],
  p_needs_input => ${p.p_needs_input},
  p_layout => ${j(p.p_layout)});
`;
}

// ---------------------------------------------------------------- local copy of phg_design_doc_check (pre-flight)
// Same rules as the database: every item must be in the draft or the inputs (by lower-cased, space-collapsed name),
// and every price value must be one the draft or the inputs gave for that name.
export function docCheck(doc, baseDoc, inputs) {
  const problems = [];
  if (!doc || !Array.isArray(doc.sections)) return { ok: false, problems: ['doc.sections must be an array'] };
  if (!doc.sections.length) problems.push('no sections');
  if (doc.sections.length > 60) problems.push('more than 60 sections');
  if (doc.sections.some(s => !String(s.name || '').trim())) problems.push('a section has no name');
  const docItems = d => (d?.sections || []).flatMap(s => [...(s.items || []), ...(s.subs || []).flatMap(b => b.items || [])]);
  const known = new Map();
  const add = (k, vals) => { if (!known.has(k)) known.set(k, []); known.get(k).push(...vals); };
  for (const i of docItems(baseDoc)) add(nameKey(i.name), (i.prices || []).map(p => Number(p.value)).filter(Number.isFinite));
  for (const x of inputs?.items || []) {
    const k = nameKey(x.name || x.item_name); if (!k) continue;
    if (Array.isArray(x.prices)) {
      for (const p of x.prices) if (typeof p === 'object') problems.push(`inputs price for "${x.name}" is an object; the database check needs plain numbers`);
      add(k, x.prices.map(Number));
    } else add(k, /^\s*\d+(\.\d+)?\s*$/.test(String(x.price ?? '')) ? [Number(x.price)] : []);
  }
  let n = 0;
  for (const i of docItems(doc)) {
    n++;
    const k = nameKey(i.name);
    if (!k) { problems.push('an item has no name'); continue; }
    if (!known.has(k)) { problems.push(`item not in the draft or the inputs (invented?): ${i.name}`); continue; }
    for (const p of i.prices || []) if (!known.get(k).includes(Number(p.value))) { problems.push(`price not in the draft or the inputs: ${i.name}`); break; }
  }
  if (n > 600) problems.push('more than 600 items');
  return { ok: problems.length === 0, problems: problems.slice(0, 50), items: n, sections: doc.sections.length };
}
