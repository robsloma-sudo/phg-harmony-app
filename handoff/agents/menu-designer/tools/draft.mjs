// Designing FROM the venue's Menu Studio draft (task.base_doc) instead of from scratch.
// - Every draft item keeps its object: id, phg links (menu_item_id, recipe ids), meta, components, origin, source.
//   The app's links to recipes and costing survive because nothing is rebuilt.
// - Items from the task inputs (e.g. a Harmony voice note) update a draft item with the same name, or are added to
//   the section that holds their list.
// - Descriptions are written only from known facts: the draft item's own recipe components, respecting
//   meta.public_visibility and meta.public_components. Anything missing is flagged, never invented.

import { LIST_PHRASES, LIST_BY_KEY } from './lexicon.mjs';

const nameKey = s => String(s || '').trim().toLowerCase().replace(/\s+/g, ' ');
const BADGE_FOR_FLAG = { house_special: 'house', new: 'new', seasonal: 'seasonal' };
let seq = 0;
const nid = p => `${p}_mdz${Date.now().toString(36)}${++seq}`;

// Which drinks list a section or subsection name stands for ("Draft" -> beer, "Agave" -> tequila…).
const EXTRA = { spirits: 'spirits', agave: 'tequila', 'by the glass': 'wine', 'house originals': 'cocktails', classics: 'cocktails',
                draft: 'beer', cans: 'beer', bottles: 'beer', cider: 'cider_seltzer', brandy: 'brandy_cognac', 'non-alcoholic': 'non_alcoholic' };
export function listForName(name) {
  const n = nameKey(name);
  if (EXTRA[n]) return EXTRA[n];
  const hit = LIST_PHRASES.find(p => n === p.w || n.startsWith(p.w + ' ') || n.endsWith(' ' + p.w));
  return hit ? hit.key : null;
}
const sameFamily = (a, b) => a === b || (/^wine/.test(a || '') && /^wine/.test(b || ''));

export function itemsOf(doc) {
  const out = [];
  (doc.sections || []).forEach((s, si) => {
    (s.items || []).forEach(it => out.push({ it, s, sub: null, si }));
    (s.subs || []).forEach(b => (b.items || []).forEach(it => out.push({ it, s, sub: b, si })));
  });
  return out;
}

// Description from the venue's recipe components: spirit first, then modifiers, then garnish.
// Honours public_visibility.ingredients / house_recipe and public_components[slug] === false.
export function describeFromComponents(it) {
  const vis = it.meta?.public_visibility || {};
  if (vis.ingredients === false || vis.description === false) return null;
  if (vis.house_recipe === false) return null;           // the venue keeps this recipe private: keep its own words
  const hidden = it.meta?.public_components || {};
  const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const comps = (it.components || []).filter(c => c && c.name && hidden[slug(c.name)] !== false);
  if (comps.length < 2) return null;
  const rank = c => /base|spirit/i.test(c.role || '') ? 0 : /garnish/i.test(c.role || '') ? 2 : 1;
  const names = comps.slice().sort((a, b) => rank(a) - rank(b)).map((c, i) => {
    let n = String(c.name).replace(/^fresh\s+/i, '').replace(/\s+juice$/i, '');
    return i === 0 ? n.charAt(0).toUpperCase() + n.slice(1).toLowerCase() : n.toLowerCase();
  });
  return names.join(', ');
}

// Content gaps the Menu Content Reviewer scores (criterion 8). Returns human questions; never fills the gap.
export function contentGaps(it, list, holder = '') {
  // Category-specific questions (Content Reviewer, round 1): ask for what that list prints, never "ingredients, style, origin".
  // `holder` is the subsection the item sits under ("Blanco"): it already states the expression.
  const d = String(it.desc || ''), n = `"${it.name}"`, known = `${d} ${holder || ''}`;
  const q = [];
  const spirit = ['tequila', 'mezcal', 'whiskey', 'rum', 'gin', 'vodka', 'brandy_cognac', 'liqueurs_amari', 'sake_soju', 'spirits'].includes(list);
  if (list === 'beer') {
    if (!d.trim()) q.push(`${n}: what style is it, and what is its ABV?`);
    else if (!/\d(\.\d)?\s*%/.test(d)) q.push(`${n}: what is its ABV?`);
    else if (d.replace(/\d+(\.\d+)?\s*%\s*ABV/i, '').replace(/[·\s]/g, '') === '' && !/\b(ipa|lager|pils|stout|porter|ale|wheat|gose|saison|sour|amber)\b/i.test(it.name)) q.push(`${n}: what style should print next to the ABV (for example lager, IPA, stout)?`);
  } else if (list === 'cider_seltzer') {
    if (!d.trim()) q.push(`${n}: what style or flavour is it, and its ABV?`);
  } else if (/^wine/.test(list || '')) {
    if (!d.trim() || !/[A-Z][a-z]+,?\s+(?:[A-Z][a-z]+|\d{4})|valley|coast|france|italy|spain|california|oregon|washington|argentina|chile|australia|new zealand|germany|portugal|mendoza|napa|sonoma|doc|docg|aoc/i.test(d))
      q.push(`${n}: which producer and region should print${/cabernet|merlot|pinot|malbec|syrah|shiraz|zinfandel|chardonnay|sauvignon|riesling|grigio|tempranillo|sangiovese|nebbiolo|grenache|garnacha/i.test(it.name) ? '' : ' (and the grape)'}${/prosecco|champagne|cava|sparkling|brut/i.test(it.name + d) ? ' (for sparkling: producer and DOC/region)' : ''}?`);
  } else if (spirit) {
    // "%" sits outside the \b groups: there is no word boundary after it, so "\b%\b" never matched a printed ABV.
    const strength = /\b(proof|abv|year|aged)\b|\d\s*%/i.test(d);
    if (/\b(blanco|reposado|a[nñ]ejo|joven|extra)\b/i.test(known) && !strength) q.push(`${n}: ${(d.trim() || holder)} is printed; any proof, ABV or age to add?`);
    else if (!strength && !/\b(year|yr|aged|blanco|reposado|a[nñ]ejo|joven|espad[ií]n|tobal[aá]|vsop|xo|vs|proof|single|small batch|bottled|cask|barrel)\b/i.test(known + ' ' + it.name))
      q.push(list === 'mezcal' ? `${n}: which agave and style (joven, reposado…), and its ABV?`
           : list === 'tequila' ? `${n}: which expression (blanco, reposado, añejo) and any age or proof to print?`
           : `${n}: what type, age or proof should print?`);
  } else if (list === 'non_alcoholic') {
    if (!d.trim()) q.push(`${n}: what is in it (or which flavours are offered)?`);
  } else if (list === 'cocktails' || !list) {
    if (!d.trim()) q.push(`${n}: what is the build (spirit, modifiers, sweetener, citrus) and garnish?`);
    else if (d.split(/[,·]|\band\b/).filter(x => x.trim()).length < 3) q.push(`${n}: the description names ${d.split(/[,·]|\band\b/).filter(x => x.trim()).length} ingredients; what else goes in it, and the garnish?`);
  }
  if (it.meta?.description_source === 'standard_spec') q.push(`${n}: the description uses the classic spec (standard). Please confirm or give your build.`);
  return q;
}

export function buildDocFromBase(req, look, opts = {}) {
  const doc = JSON.parse(JSON.stringify(req.base_doc));
  delete doc.phg;                                          // project credential: never carried in a proposal
  doc.sections = doc.sections || [];
  const changes = [], questions = [], flags = new Set();
  const accent = opts.accent || look.accent;
  const byName = new Map(itemsOf(doc).map(x => [nameKey(x.it.name), x]));

  // 1. Merge the task's items into the draft.
  for (const inp of req.items) {
    const k = nameKey(inp.name);
    const hit = byName.get(k);
    if (hit) {
      const it = hit.it;
      if (inp.prices.length) {
        const before = JSON.stringify((it.prices || []).map(p => p.value));
        it.prices = inp.prices.map((p, i) => ({ id: it.prices?.[i]?.id || nid('prc'), label: p.label || '', value: p.value, source: 'manual' }));
        if (before !== JSON.stringify(it.prices.map(p => p.value))) changes.push(`"${it.name}" price set to ${it.prices.map(p => (p.label ? p.label + ' ' : '') + p.value).join(' / ')} as given in the request.`);
      }
      if (inp.description && !String(it.desc || '').trim()) { it.desc = inp.description; changes.push(`"${it.name}" description added from the request.`); }
      if (inp.abv !== null && inp.abv !== undefined && !/\d\s*%/.test(it.desc || '')) { it.desc = (it.desc ? `${String(it.desc).replace(/\.$/, '')} · ` : '') + `${inp.abv}% ABV`; it.meta = { ...(it.meta || {}), abv: inp.abv }; }
      for (const f of inp.flags || []) if (BADGE_FOR_FLAG[f] && !(it.badges || []).includes(BADGE_FOR_FLAG[f])) (it.badges = it.badges || []).push(BADGE_FOR_FLAG[f]);
      if ((inp.flags || []).some(f => f === 'featured' || f === 'house_special')) it.format = { ...(it.format || {}), name: { c: accent, w: 'bold' } };
      continue;
    }
    if (inp.edit) { questions.push(`"${inp.name}" was asked for but is not on the draft. Which item did you mean?`); flags.add('edit_target_not_found'); continue; }
    // New item: into the section (and subsection) for its list; create them if the draft has none.
    const node = newItem(inp, accent);
    let sec = doc.sections.find(s => sameFamily(listForName(s.name), inp.list));
    if (!sec) {
      sec = { id: nid('sec'), name: (LIST_BY_KEY[inp.list]?.label) || 'New items', desc: '', items: [], subs: [] };
      doc.sections.push(sec);
      changes.push(`Added a ${sec.name} section for items in the request.`);
    }
    let sub = inp.sub ? (sec.subs || []).find(b => nameKey(b.name) === nameKey(inp.sub)) : null;
    if (inp.sub && !sub && (sec.subs || []).length) { sub = { id: nid('sub'), name: inp.sub, desc: '', items: [] }; sec.subs.push(sub); }
    if (!sub && !(sec.items || []).length && (sec.subs || []).length) {
      // the section is organised in subsections only: keep that, put the item in the matching or last subsection
      sub = sec.subs.find(b => sameFamily(listForName(b.name), inp.list)) || sec.subs[sec.subs.length - 1];
    }
    (sub ? sub.items : (sec.items = sec.items || [])).push(node);
    byName.set(k, { it: node, s: sec, sub });
    changes.push(`Added "${node.name}" to ${sec.name}${sub ? ' › ' + sub.name : ''}.`);
  }

  // 2. Descriptions from the venue's own recipe components (known facts only).
  for (const { it } of itemsOf(doc)) {
    const comp = describeFromComponents(it);
    if (!comp) continue;
    const have = String(it.desc || '');
    const missing = (it.components || []).filter(c => !new RegExp(String(c.name).replace(/^fresh\s+/i, '').split(/\s+/)[0], 'i').test(have));
    if (have && !missing.length) continue;
    // Keep the venue's own tasting note (a sentence that is not an ingredient list), drop the old ingredient list.
    const note = have.split(/(?<=\.)\s+/).slice(1).join(' ').trim();
    it.desc = comp + (note ? `. ${note.replace(/\.$/, '')}` : '');
    it.meta = { ...(it.meta || {}), description_source: 'recipe_components' };
    changes.push(`"${it.name}" description written from its recipe (${comp}).`);
  }

  // 3. Content gaps -> questions (criterion 8), never guesses.
  for (const { it, s, sub } of itemsOf(doc)) {
    const list = it.meta?.section ? normMeta(it.meta.section, sub?.name || s.name) : listForName(sub?.name || s.name);
    for (const q of contentGaps(it, list, sub?.name || '')) { questions.push(q); flags.add(gapFlag(q)); }
  }

  // 4. Menu engineering inside each list: house/featured first.
  for (const s of doc.sections) {
    for (const holder of [s, ...(s.subs || [])]) {
      const arr = holder.items || [];
      const hot = arr.filter(i => (i.badges || []).includes('house') || i.format?.name);
      if (hot.length && hot.length < arr.length) {
        const rest = arr.filter(i => !hot.includes(i));
        const out = hot.length >= 2 && rest.length >= 2 ? [hot[0], ...hot.slice(2), ...rest, hot[1]] : [...hot, ...rest];
        if (out.some((x, i) => x !== arr[i])) { holder.items = out; changes.push(`Placed ${hot.map(h => `"${h.name}"`).join(', ')} at the edges of ${holder.name}.`); }
      }
    }
  }

  // 5. Section order for the venue (only reorders; never renames or merges the venue's sections).
  const order = opts.order || [];
  if (order.length) {
    const before = doc.sections.map(s => s.name).join(' › ');
    const pos = s => { const l = listForName(s.name) || s.subs?.map(b => listForName(b.name)).find(Boolean); const i = order.indexOf(l === 'spirits' ? 'tequila' : l); return i < 0 ? 90 : i; };
    doc.sections = doc.sections.map((s, i) => ({ s, i })).sort((a, b) => pos(a.s) - pos(b.s) || a.i - b.i).map(x => x.s);
    const after = doc.sections.map(s => s.name).join(' › ');
    if (before !== after) changes.push(`Section order: ${after} (was ${before}).`);
  }
  return { doc, changes, questions, flags: [...flags], title_missing: !doc.title };
}

function normMeta(section, name) {
  if (section === 'spirits') return listForName(name) || 'spirits';
  if (section === 'cider') return 'cider_seltzer';
  return section;
}

function newItem(inp, accent) {
  const badges = [...new Set((inp.flags || []).map(f => BADGE_FOR_FLAG[f]).filter(Boolean))];
  let desc = inp.description || '';
  if (inp.abv !== null && inp.abv !== undefined) desc = (desc ? `${desc} · ` : '') + `${inp.abv}% ABV`;
  const node = {
    id: nid('itm'), source: 'manual', origin: { venue_key: null, item_name: inp.name }, name: inp.name, brand: inp.brand || '', desc,
    prices: inp.prices.map(p => ({ id: nid('prc'), label: p.label || '', value: p.value, source: 'manual' })), badges,
    meta: { canonical: null, identity_class: null, section: inp.list, family: null, subfamily: null, serve_format: inp.sub || null,
            venue_heading: null, abv: inp.abv ?? null,
            public_visibility: { item: true, description: true, price: true, brand: true, ingredients: true, house_recipe: true }, public_components: {} },
    evidence: null,
  };
  if ((inp.flags || []).some(f => f === 'featured' || f === 'house_special')) node.format = { name: { c: accent, w: 'bold' } };
  return node;
}

export function gapFlag(q) {
  return /standard\)/.test(q) ? 'standard_spec_to_confirm' : /ABV|style/.test(q) ? 'missing_beer_detail' : /producer|region/.test(q) ? 'missing_wine_origin'
       : /agave|expression|type, age/.test(q) ? 'missing_spirit_detail' : 'missing_ingredients';
}
