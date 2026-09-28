// PHG Menu Designer: design request -> Menu Studio file(s) (.menu.json, schema_version 2) + reasoning.
// Input is either an agent_tasks.input_payload (brief section 4) or the output of parse-voice.mjs.
// Output documents use only Menu Studio's own model, so the Coordinator can apply them unchanged.

import { LIST_BY_KEY } from './lexicon.mjs';
import { buildDocFromBase, itemsOf, listForName, contentGaps, gapFlag } from './draft.mjs';
import { applyStandards } from './standards.mjs';
import { layout, priceText, MDC_SIZES, MDC_DPI } from './layout.mjs';
import { LOOKS, LOOK_BY_KEY, styleForLook, fontIndexFor, MDC_FONTS } from '../styles/looks.mjs';

export const MDC_FILE_APP = 'nbcc-menu-designer';
export const MDC_FILE_VERSION = 2;
const BADGE_FOR_FLAG = { house_special: 'house', new: 'new', seasonal: 'seasonal' };   // MDC_BADGES subset
// Print legibility floor (px @96 dpi; pt = px x 0.75): names/prices 10.5 pt, descriptions 8.25 pt, labels 6.75 pt.
// Butterick: body 10–12 pt in print, never below 8 pt; Sensory Trust clear print prefers 12 pt+ (knowledge/01 [16], 02).
const FLOOR = { name: 14, desc: 11, price: 14, section: 13, sub: 9 };

// ---------------------------------------------------------------- request normalisation
// Accepts brief-style payloads ({venue, menu_type, lists, items, brand, format, constraints, demographics})
// or parse-voice output ({sections, design, venue_name, ...}). Returns one shape.
export function normalizeRequest(input = {}) {
  if (input.sections && input.design) return fromVoice(input);
  if ('base_doc' in input && Array.isArray(input.items)) return { questions: [], voice: null, ...input };   // handoff.taskToRequest
  const p = input.input_payload || input;
  const items = (p.items || []).map(it => ({
    name: it.name, description: it.description || it.desc || null, list: normList(it.list),
    sub: it.sub || it.serve_format || null, abv: it.abv ?? null, brand: it.brand || '',
    prices: Array.isArray(it.prices) ? it.prices.map(x => ({ label: x.label || '', value: Number(x.value) }))
      : (it.price !== undefined && it.price !== null && it.price !== '') ? [{ label: '', value: Number(it.price) }] : [],
    flags: Array.isArray(it.flags) ? it.flags : Object.keys(it.flags || {}).filter(k => it.flags[k]),
  }));
  const fmt = p.format || {};
  return {
    request: p.request || '', source: p.source || 'user_prompt_flow',
    venue: p.venue || {}, menu_type: p.menu_type || null,
    lists: (p.lists || []).map(normList), items,
    price_band: p.price_band || null, demographics: p.demographics || null,
    brand: p.brand || {}, constraints: p.constraints || {}, comparables: p.comparables || [],
    format: { size: fmt.size || fmt.print || null, orientation: fmt.orientation || null, medium: fmt.medium || (fmt.screen ? 'screen' : 'print'),
              screen: fmt.screen || null, pages: fmt.pages || null, columns: fmt.columns || null },
    voice: null, questions: [],
  };
}

function normList(l) {
  if (!l) return null;
  const k = String(l).toLowerCase().replace(/[^a-z]+/g, '_').replace(/^_|_$/g, '');
  const alias = { wine_red: 'wine_red', red: 'wine_red', red_wine: 'wine_red', white: 'wine_white', white_wine: 'wine_white',
    rose: 'wine_rose', ros: 'wine_rose', ros_wine: 'wine_rose', sparkling: 'wine_sparkling', cider: 'cider_seltzer',
    seltzer: 'cider_seltzer', cider_seltzer: 'cider_seltzer', brandy: 'brandy_cognac', cognac: 'brandy_cognac',
    liqueurs: 'liqueurs_amari', amari: 'liqueurs_amari', liqueur_amaro: 'liqueurs_amari', liqueurs_amaro: 'liqueurs_amari', sake: 'sake_soju', soju: 'sake_soju', na: 'non_alcoholic',
    non_alcoholic: 'non_alcoholic', zero_proof: 'non_alcoholic', mocktails: 'non_alcoholic', whisky: 'whiskey' };
  return alias[k] || k;
}

function fromVoice(v) {
  const items = [];
  for (const s of v.sections) for (const it of s.items) items.push({ ...it, list: s.key, brand: '' });
  for (const it of v.unplaced_items || []) items.push({ ...it, list: null, brand: '' });
  const d = v.design;
  const size = d.format && ['letter', 'legal', 'tabloid', 'half_letter', 'table_tent'].includes(d.format) ? d.format : null;
  return {
    request: v.transcript, source: 'user_prompt_flow:voice',
    venue: { name: v.venue_name || null, type: v.venue_type || null },
    menu_type: v.menu_type, lists: v.lists, items, price_band: null, demographics: null,
    brand: { colours: d.colours.map(c => c.hex), fonts: d.fonts, tone: d.tone },
    constraints: {}, comparables: [],
    format: { size, orientation: d.orientation, medium: ['phone', 'tablet', 'tv'].includes(d.format) ? 'screen' : 'print',
              screen: ['phone', 'tablet', 'tv'].includes(d.format) ? d.format : null, pages: d.pages, columns: d.columns },
    voice: { tone: d.tone, notes: d.notes, hours: d.hours || null }, questions: [...v.questions],
  };
}

// ---------------------------------------------------------------- look selection
export function rankLooks(req) {
  const venue = normVenue(req.venue.type);
  const tone = new Set([...(req.brand.tone || []), ...((req.voice && req.voice.tone) || [])].map(String));
  const demo = req.demographics || {};
  const lists = new Set(req.items.map(i => i.list));
  return LOOKS.map(l => {
    let score = 0; const why = [];
    if (venue && l.fits.venue.includes(venue)) { score += 5; why.push(`suits a ${venue.replace(/_/g, ' ')}`); }
    for (const t of tone) if (l.fits.tone.includes(t)) { score += 4; why.push(`matches "${t}" direction`); }
    if (tone.has('dark') && ['noir', 'deco'].includes(l.k)) score += 3;
    if (tone.has('light') && ['noir', 'deco', 'slate'].includes(l.k)) score -= 6;
    if (tone.has('dark') && !['noir', 'deco'].includes(l.k)) score -= 2;
    const inc = demo.median_household_income, aff = demo.households_over_100k_pct, young = demo.pop_21_34_pct;
    if ((inc >= 110000 || aff >= 45) && ['grand', 'cellar', 'noir', 'deco', 'minimal'].includes(l.k)) { score += 2; why.push('affluent trade area favours restraint and whitespace'); }
    if (inc && inc < 55000 && ['tavern', 'taproom', 'cantina'].includes(l.k)) { score += 2; why.push('value-led trade area favours direct, scannable layout'); }
    if (young >= 30 && ['tropic', 'cantina', 'taproom', 'minimal'].includes(l.k)) { score += 1; why.push('young (21–34) share supports a bolder look'); }
    if (demo.hispanic_latino_pct >= 40 && l.k === 'cantina' && (lists.has('tequila') || lists.has('mezcal') || venue === 'latin_cantina')) score += 2;
    if ((lists.has('beer') && req.items.filter(i => i.list === 'beer').length >= 10) && ['taproom', 'tavern'].includes(l.k)) { score += 2; why.push('long beer list reads best with leader dots'); }
    const wineN = req.items.filter(i => /^wine/.test(i.list || '')).length;
    if (wineN >= 8 && l.k === 'cellar') { score += 3; why.push('wine-forward program'); }
    return { look: l, score, why };
  }).sort((a, b) => b.score - a.score);
}

function normVenue(t) {
  if (!t) return null;
  const s = String(t).toLowerCase();
  const map = [[/cocktail|lounge|speakeasy/, 'cocktail_lounge'], [/dive|pub|neighbo/, 'dive_bar'], [/brew|tap ?room|beer/, 'brewery'],
    [/wine/, 'wine_bar'], [/fine|steak|tasting/, 'fine_dining'], [/cantina|mexican|taquer|mezcal|latin/, 'latin_cantina'],
    [/hotel|rooftop/, 'hotel_bar'], [/sport/, 'sports_bar'], [/night|club/, 'nightclub'], [/tiki/, 'tiki'],
    [/restaurant|bistro|cafe|diner|gastro|bar_?and_?grill|meal/, 'restaurant'], [/^bar$/, 'dive_bar']];
  for (const [re, k] of map) if (re.test(s)) return k;
  return null;
}

// ---------------------------------------------------------------- section order
// Section order. Scorecard §1 criterion 5 example: cocktails → beer → wine → spirits → non-alcoholic. Non-alcoholic sits
// last with equal type treatment (both reviewers, round 1, marked it down when it sat between alcoholic lists).
const SPIRITS_ORDER = ['tequila', 'mezcal', 'whiskey', 'gin', 'vodka', 'rum', 'brandy_cognac', 'liqueurs_amari', 'sake_soju'];
const WINES = ['wine_sparkling', 'wine_white', 'wine_rose', 'wine_red', 'wine'];
const ORDER = {
  default:       ['cocktails', 'beer', 'cider_seltzer', ...WINES, ...SPIRITS_ORDER, 'non_alcoholic'],
  brewery:       ['beer', 'cider_seltzer', 'cocktails', ...WINES, ...SPIRITS_ORDER, 'non_alcoholic'],
  dive_bar:      ['beer', 'cocktails', 'cider_seltzer', 'whiskey', 'tequila', 'vodka', 'gin', 'rum', 'mezcal', ...WINES, 'brandy_cognac', 'liqueurs_amari', 'sake_soju', 'non_alcoholic'],
  wine_bar:      [...WINES, 'cocktails', 'beer', 'cider_seltzer', 'brandy_cognac', 'liqueurs_amari', 'whiskey', 'gin', 'vodka', 'rum', 'tequila', 'mezcal', 'sake_soju', 'non_alcoholic'],
  latin_cantina: ['cocktails', 'tequila', 'mezcal', 'beer', 'cider_seltzer', ...WINES, 'whiskey', 'rum', 'gin', 'vodka', 'brandy_cognac', 'liqueurs_amari', 'sake_soju', 'non_alcoholic'],
};
ORDER.sports_bar = ORDER.dive_bar; ORDER.fine_dining = ORDER.wine_bar;
const FOOD = ['food_small', 'food_mains', 'food_sides', 'food_dessert'];
const WINE_SUB = { wine_sparkling: 'Sparkling', wine_white: 'White', wine_rose: 'Rosé', wine_red: 'Red' };

let seq = 0;
const id = p => `${p}_d${++seq}`;

function mdcItem(it, accent, emphasise) {
  const badges = [...new Set((it.flags || []).map(f => BADGE_FOR_FLAG[f]).filter(Boolean))];
  let desc = it.description || '';
  // Beer convention: style/description first, then ABV ("Oatmeal stout with coffee · 6.2% ABV").
  if (it.abv !== null && it.abv !== undefined && it.abv !== '') desc = (desc ? `${desc} · ` : '') + `${it.abv}% ABV`;
  const node = {
    id: id('itm'), source: 'manual', origin: { venue_key: null, item_name: it.name },
    name: it.name, brand: it.brand || '', desc,
    prices: (it.prices || []).filter(p => isFinite(p.value)).map(p => ({ id: id('prc'), label: p.label || '', value: p.value, source: 'manual' })),
    badges,
    meta: { canonical: null, identity_class: null, section: it.list, family: null, subfamily: null, serve_format: it.sub || null,
            venue_heading: null, abv: it.abv ?? null, designer_flags: it.flags || [],
            public_visibility: { item: true, description: true, price: true, brand: true, ingredients: true, house_recipe: true },
            public_components: {} },
    evidence: null,
  };
  // Featured / house items: accent the name. Menu Studio honours node.format[level] overrides (menuNodeStyleOverride).
  if (emphasise && (it.flags || []).some(f => f === 'featured' || f === 'house_special')) node.format = { name: { c: accent, w: 'bold' } };
  return node;
}

export function buildDoc(req, look, opts = {}) {
  seq = 0;
  const venue = normVenue(req.venue.type);
  const order = [...(ORDER[venue] || ORDER.default), ...FOOD];
  const present = [...new Set(req.items.map(i => i.list).filter(Boolean))];
  for (const l of req.lists || []) if (l && !present.includes(l)) present.push(l);        // requested but empty: keep, flag
  const lists = present.sort((a, b) => (order.indexOf(a) + 1 || 99) - (order.indexOf(b) + 1 || 99));

  const sections = []; const changes = [];
  const wineKeys = lists.filter(l => /^wine/.test(l));
  const accent = opts.accent || look.accent;
  const promote = arr => {
    // Menu engineering: house specials and featured items take the first slot(s) of their section,
    // where the eye lands first. Everything else keeps the order it was given in.
    const hot = arr.filter(i => (i.flags || []).some(f => f === 'house_special' || f === 'featured'));
    if (!hot.length || hot.length === arr.length) return arr;
    // Edges sell: items first or last in a category are chosen ~20% more than mid-list (Dayan & Bar-Hillel 2011,
    // knowledge/01 [6]). The first promoted item leads the list, a second one closes it, any others follow the first.
    const rest = arr.filter(i => !hot.includes(i));
    const out = hot.length >= 2 && rest.length >= 2 ? [hot[0], ...hot.slice(2), ...rest, hot[1]] : [...hot, ...rest];
    if (out.some((x, i) => x !== arr[i])) changes.push(`Placed ${hot.map(h => `"${h.name}"`).join(', ')} at the edges of their list (first${hot.length >= 2 && rest.length >= 2 ? ' and last' : ''}), where items sell best.`);
    return out;
  };
  const buildSection = (name, items, subsFrom) => {
    const sec = { id: id('sec'), name, items: [], subs: [] };
    const bySub = new Map();
    for (const it of items) {
      const sub = subsFrom(it);
      if (!sub) { sec.items.push(it); continue; }
      if (!bySub.has(sub)) bySub.set(sub, []);
      bySub.get(sub).push(it);
    }
    sec.items = promote(sec.items).map(i => mdcItem(i, accent, true));
    for (const [sub, arr] of bySub) sec.subs.push({ id: id('sub'), name: sub, items: promote(arr).map(i => mdcItem(i, accent, true)) });
    return sec;
  };

  let wineDone = false;
  for (const l of lists) {
    if (/^wine/.test(l)) {
      if (wineDone) continue; wineDone = true;
      const items = req.items.filter(i => /^wine/.test(i.list || ''));
      // One Wine section; styles become subsections in the classic order (sparkling → white → rosé → red).
      const subOrder = ['Sparkling', 'White', 'Rosé', 'Red'];
      const sec = buildSection('Wine', items, i => WINE_SUB[i.list] || i.sub || null);
      sec.subs.sort((a, b) => (subOrder.indexOf(a.name) + 1 || 50) - (subOrder.indexOf(b.name) + 1 || 50));
      if (sec.subs.some(x => subOrder.includes(x.name))) changes.push('Grouped wine styles into one Wine section with Sparkling / White / Rosé / Red subsections.');
      sections.push(sec);
      continue;
    }
    const label = sectionLabel(l, look);
    sections.push(buildSection(label, req.items.filter(i => i.list === l), i => i.sub || null));
  }
  // A one- or two-item agave list does not earn its own header (round-1 review): tequila and mezcal share one section,
  // each keeping its own subsection so both lists stay visibly equal.
  const tq = sections.find(x => x.name === 'Tequila'), mz = sections.find(x => x.name === 'Mezcal');
  if (tq && mz && (countItems(tq) <= 2 || countItems(mz) <= 2)) {
    const subs = tq.subs.length ? tq.subs : [{ id: id('sub'), name: 'Tequila', items: tq.items }];
    if (tq.subs.length && tq.items.length) subs.unshift({ id: id('sub'), name: 'Tequila', items: tq.items });
    subs.push(...(mz.subs.length ? mz.subs.map(b => ({ ...b, name: `Mezcal · ${b.name}` })) : [{ id: id('sub'), name: 'Mezcal', items: mz.items }]));
    tq.name = 'Tequila & Mezcal'; tq.items = []; tq.subs = subs;
    sections.splice(sections.indexOf(mz), 1);
    changes.push('Tequila and Mezcal share one section with their own subsections (a one-item list does not earn a full header).');
  }
  // A "By the glass" subsection that also carries bottle prices is renamed so the heading tells the truth.
  for (const sec of sections) for (const b of sec.subs || []) {
    if (/^by the glass$/i.test(b.name) && b.items.some(i => (i.prices || []).some(p => /bottle/i.test(p.label || '')))) {
      b.name = 'By the glass & bottle'; changes.push('Renamed "By the glass" to "By the glass & bottle": some wines carry a bottle price.');
    }
  }
  const unplaced = req.items.filter(i => !i.list);
  if (unplaced.length) sections.push(buildSection('Unplaced', unplaced, () => null));

  const title = req.venue.name || (req.menu_type === 'Happy hour page' ? 'Happy Hour' : null);
  let subtitle = '';
  if (req.menu_type === 'Happy hour page' && req.venue.name) subtitle = 'Happy Hour' + (req.voice?.hours ? ` · ${req.voice.hours}` : '');
  else if (req.voice?.hours) subtitle = req.voice.hours;
  else {
    const offer = sections.map(x => x.name).join('  ·  ');
    if (sections.length >= 2 && offer.length <= 64) subtitle = offer;       // the city goes in the footer, never twice
  }
  return { doc: { id: 'doc_designer', title: title || 'Menu', subtitle, sections }, changes, title_missing: !title };
}

function countItems(sec) { return (sec.items || []).length + (sec.subs || []).reduce((a, b) => a + (b.items || []).length, 0); }

function sectionLabel(key, look) {
  if (key === 'non_alcoholic') return ['noir', 'deco', 'grand', 'minimal', 'cellar'].includes(look.k) ? 'Zero Proof' : 'Non-Alcoholic';
  return (LIST_BY_KEY[key] && LIST_BY_KEY[key].label) || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ---------------------------------------------------------------- style tuning
export function tuneStyle(req, look, style) {
  const notes = [];
  const demo = req.demographics || {};
  const accent = (req.brand.colours && req.brand.colours[0]) || null;
  if (accent) {
    for (const lvl of look.roles) style[lvl].c = accent;
    notes.push(`Applied the requested colour ${accent} to ${look.roles.join(', ')}.`);
  }
  if (look.accent2 && !(req.brand.colours && req.brand.colours[1])) style.sub.c = look.accent2;   // second accent: subheads + badges
  if (req.brand.colours && req.brand.colours[1]) { style.page.bg = req.brand.colours[1]; notes.push(`Page background set to brand colour ${req.brand.colours[1]}.`); }
  for (const f of req.brand.fonts || []) {
    const i = fontIndexFor(f);
    if (i === null) continue;
    if (/serif|georgia|times|palatino|classic|elegant/.test(f) && !/sans/.test(f)) { style.title.f = style.section.f = style.name.f = i; }
    else if (/sans|helvetica|avenir|trebuchet|gothic|futura|modern|bold/.test(f)) { style.title.f = style.section.f = i; style.name.f = style.desc.f = style.price.f = i; }
    else style.title.f = i;
    notes.push(`Font request "${f}" mapped to Menu Studio font ${MDC_FONTS[i].label}.`);
  }
  // Typography rules from the research (knowledge/02): caps tracking 50–120/1000 em is the text norm; headers may go a
  // little wider as display labels, but not the 300–480 of fashion mastheads (title only). Trebuchet is on Butterick's
  // avoid list; Georgia's oldstyle figures make price columns uneven.
  for (const lvl of ['section', 'sub', 'subtitle']) if (style[lvl].cs === 'upper' && style[lvl].sp > 180) style[lvl].sp = 180;
  if (style.title.cs === 'upper' && style.title.sp > 300) style.title.sp = 300;
  for (const lvl of Object.keys(style)) if (lvl !== 'page' && style[lvl].f === 5) style[lvl].f = 3;
  if (style.price.f === 0) style.price.f = style.name.f === 0 ? 2 : style.name.f;
  for (const [lvl, min] of Object.entries(FLOOR)) if (style[lvl].s < min) style[lvl].s = min;
  if ((demo.median_household_income >= 110000 || demo.households_over_100k_pct >= 45) && style.page.dots) {
    style.page.dots = false; notes.push('Affluent trade area: leader dots off, so prices sit quietly after the name.');
  }
  if (demo.median_age >= 45) {
    for (const l of ['name', 'desc', 'price']) style[l].s += 1;
    notes.push(`Median age ${demo.median_age}: body type up one step for bar-light legibility.`);
  }
  // Contrast guard (WCAG AA 4.5:1 for body text) — fix silently, report it.
  for (const lvl of ['title', 'subtitle', 'section', 'sub', 'name', 'brand', 'desc', 'price']) {
    const r = contrast(style[lvl].c, style.page.bg);
    const need = 4.5;                                    // scorecard §4: every text colour ≥ 4.5:1
    if (r < need) {
      const fixed = pushContrast(style[lvl].c, style.page.bg, need);
      notes.push(`Raised ${lvl} colour ${style[lvl].c} → ${fixed} (contrast ${r.toFixed(1)}:1 was below ${need}:1).`);
      style[lvl].c = fixed;
    }
  }
  return notes;
}

// ---------------------------------------------------------------- fit (mirrors Menu Studio's page arithmetic)
// Average advance per character (em) measured in Chromium with the preview fonts: [regular, bold, all-caps].
// Re-measure with styles/calibrate.mjs if fonts change. 3% safety margin added in textW.
const CHAR_W = [[0.455, 0.528, 0.58], [0.417, 0.445, 0.563], [0.458, 0.473, 0.585], [0.457, 0.486, 0.578],
                [0.461, 0.479, 0.566], [0.46, 0.463, 0.51], [0.496, 0.496, 0.552], [0.6, 0.6, 0.6]];
export function textW(t, st) {
  const up = st.cs === 'upper', bold = st.w === 'bold';
  const [r, b, u] = CHAR_W[st.f];
  const per = up ? u * (bold ? b / r : 1) : (bold ? b : r);
  const n = String(t).length;
  return (n * st.s * per + n * st.s * (st.sp || 0) / 1000) * 1.03;
}
export function measure(doc, S, sizeKey) {
  const L = layout({ doc, style: S, size: sizeKey });
  const wide = [];
  for (const op of L.ops) {
    if (op.t !== 'item') continue;
    const it = op.item;
    const line = textW(it.name, S.name) + (it.brand ? textW(' ' + it.brand, S.brand) : 0) + it.badges.reduce((a, b) => a + 6 + b.length * Math.max(7, Math.round(S.desc.s * 0.7)) * 0.72, 0) + textW(priceText(it), S.price) + 16;
    const d = it.desc ? textW(it.desc, S.desc) : 0;
    if (line > L.colW || d > L.colW) wide.push({ item: it.name, over: Math.round(Math.max(line, d) - L.colW) });
  }
  // A pinned footer takes no flow height in Menu Studio, but the flow must stop a clear break above it.
  const foot = doc.sections.find(x => x.designer_role === 'footer');
  let pages = L.pages, fill = Math.round(((L.pages - 1) + L.lastPageUsed) * 100) / 100;
  if (foot && L.pages === 1) {
    const usable = L.H - 2 * L.M;
    const reserve = (foot.desc ? S.section.s + 11 + S.desc.s * 1.16 : Math.max(8, S.sub.s) * 1.16) + Math.max(S.page.secGap * 1.25, S.name.s * 1.6);
    if (L.contentBottom + reserve > L.H - L.M) pages = 2;
    fill = Math.round(((L.contentBottom - L.M) / (usable - reserve)) * 100) / 100;
  }
  return { pages, cols: L.n, colW: Math.round(L.colW), overflowing: L.overflow.map(o => o.name), wide, imbalance: L.imbalance, fill };
}

// Try to make the menu fit its page budget without dropping anything: gaps → columns → type steps → pages.
export function fit(doc, S, sizeKey, want) {
  const log = [];
  const budget = want.pages || 1;
  let m = measure(doc, S, sizeKey);
  const steps = [
    () => { if (S.page.itemGap > 4 || S.page.secGap > 12) { S.page.itemGap = Math.max(4, S.page.itemGap - 2); S.page.secGap = Math.max(12, S.page.secGap - 4); return 'tightened spacing'; } },
    () => { const [w] = MDC_SIZES[sizeKey]; const max = w >= 10 ? 3 : w >= 7 ? 2 : 1; if (!want.columns && S.page.cols < max) { S.page.cols++; return `went to ${S.page.cols} columns`; } },
    () => { if (S.page.margin > 0.5) { S.page.margin = Math.max(0.5, +(S.page.margin - 0.15).toFixed(2)); return 'narrowed margins'; } },
    () => { let ch = false; for (const l of ['name', 'price', 'desc', 'section', 'sub']) if (S[l].s - 1 >= FLOOR[l]) { S[l].s -= 1; ch = true; } return ch ? 'stepped type down one size' : null; },
  ];
  for (let i = 0; m.pages > budget && i < 12; i++) {
    const did = steps.map(f => f()).find(Boolean);
    if (!did) break;
    log.push(did); m = measure(doc, S, sizeKey);
  }
  // Compose: when everything fits with room to spare, search columns x scale for the layout that fills the page
  // best (target ~88% of the last page) while keeping every line inside its column. A half-empty page reads unfinished;
  // bigger type is also the single best legibility gain in bar lighting.
  if (m.pages <= budget && m.fill - (m.pages - 1) < 0.8) {
    const base = JSON.parse(JSON.stringify(S));
    const [w] = MDC_SIZES[sizeKey];
    const colOpts = want.columns ? [want.columns] : [1, 2, 3].filter(c => c <= (w >= 10 ? 3 : w >= 7 ? 2 : 1));
    let best = null;
    const W = w * MDC_DPI;
    for (const cols of colOpts) {
      // A single column on a wide page gets wider margins so name and price stay within one eye-span.
      const margins = cols === 1 ? [base.page.margin, 1.0, 1.25, 1.5].filter(x => x >= base.page.margin && x * 2 < w - 3) : [base.page.margin];
      for (const mg of margins) for (let k = 1; k <= 1.8001; k += 0.05) {
        const T = scaleStyle(base, k); T.page.cols = cols; T.page.margin = mg;
        const r = measure(doc, T, sizeKey);
        if (r.pages > budget) break;
        const last = r.fill - (r.pages - 1);
        // Prefer fill near 0.88, a measure no wider than ~5.5 in (528 px), and larger body type.
        const measurePenalty = Math.max(0, r.colW - 528) / 300;
        // Unbalanced columns (one ends far above the other) read as a mistake; single-column pages have none.
        // Menu Studio prints prices inline beside the name when there is more than one column (mdcDrawItem), so only a
        // single column gives the scorecard's one right-aligned price column. Multi-column must earn its place.
        // A line wider than its column runs into the next one in Menu Studio (no wrapping): heavy cost per line.
        const score = -Math.abs(0.88 - last) * 3 - measurePenalty - (r.imbalance || 0) * 4 - (cols > 1 ? 0.45 : 0) - r.wide.length * 0.3 - r.wide.reduce((a, x) => a + Math.max(0, x.over), 0) / 150 + (cols === 1 ? 0.08 : 0) + Math.min(T.name.s, 20) / 100;
        if (process.env.MDZ_DEBUG) console.error(cols, mg, k.toFixed(2), r.pages, (r.fill).toFixed(2), r.colW, (r.imbalance||0).toFixed(2), r.wide.length, score.toFixed(3));
        if (!best || score > best.score) best = { score, T, r, k, cols, mg };
      }
    }
    if (best && (best.k > 1.001 || best.cols !== S.page.cols || best.mg !== S.page.margin)) {
      for (const key of Object.keys(best.T)) S[key] = best.T[key];
      m = best.r; log.push(`composed to fill the page: ${best.cols} column(s), ${best.mg}" margins, type x${best.k.toFixed(2)}`);
    }
  }
  // Vertical rhythm: whatever height is still spare goes into section and item spacing (width-neutral), so the
  // page ends near its foot instead of stopping two-thirds down.
  if (m.pages <= budget) {
    for (let i = 0; i < 60; i++) {
      const last = m.fill - (m.pages - 1);
      if (last >= 0.9) break;
      const prev = [S.page.secGap, S.page.itemGap];
      if (S.page.secGap < Math.round(S.name.s * 1.6)) S.page.secGap += 2;
      if (i % 2 === 1 && S.page.itemGap < Math.round(S.name.s * 0.6)) S.page.itemGap += 1;
      if (prev[0] === S.page.secGap && prev[1] === S.page.itemGap) break;
      const n = measure(doc, S, sizeKey);
      if (n.pages > m.pages) { [S.page.secGap, S.page.itemGap] = prev; break; }
      m = n;
      if (i === 0) log.push('spread spare height into section and item spacing');
    }
  }
  // Justify: the scorecard measures margins from the outermost elements, so the last line must sit on the bottom
  // margin (±1 mm = ±3.8 px). Solve for the gap scale that lands it there; gaps may be fractional in Menu Studio.
  // Finishing rules from review round 1:
  // - hierarchy: section headers at least 1.3 x item names (critic: "hierarchy relies on colour alone");
  // - a single column wider than ~5.5 in gets leader dots so the eye can travel from name to price.
  S.section.s = Math.max(S.section.s, Math.round(S.name.s * 1.3));
  if (S.page.cols === 1 && measure(doc, S, sizeKey).colW > 528 && !S.page.dots) { S.page.dots = true; log.push('leader dots on: a wide single column needs a path from name to price'); }
  m = measure(doc, S, sizeKey);
  if (m.pages > budget) { S.section.s = Math.max(S.name.s + 2, S.section.s - 3); m = measure(doc, S, sizeKey); }
  if (m.pages === 1) {
    const footTop = placeFooter(doc, S, sizeKey);
    const H = MDC_SIZES[sizeKey][1] * MDC_DPI, M = S.page.margin * MDC_DPI;
    const s0 = S.page.secGap, i0 = S.page.itemGap;
    // f(g) = how far the flow's last line is from where it should end (0 = on target). With a footer the flow stops
    // a clear break above it (twice the section gap, at least two lines); without one, on the bottom margin as far as
    // Menu Studio's page count (which includes trailing gaps) allows.
    const apply = g => { S.page.secGap = Math.max(4, s0 + g); S.page.itemGap = Math.max(2, i0 + g * 0.3); };
    const f = g => {
      apply(g);
      const L = layout({ doc, style: S, size: sizeKey });
      if (L.pages > 1) return Infinity;
      return footTop !== null ? L.contentBottom + Math.max(S.page.secGap * 1.25, S.name.s * 1.6) - footTop : L.contentBottom - (H - M);
    };
    const f0 = f(0);
    if (isFinite(f0) && Math.abs(f0) > 2) {
      let lo = f0 < 0 ? 0 : -(s0 - 4), hi = f0 < 0 ? Math.max(4, S.name.s * 3 - s0) : 0;
      for (let i = 0; i < 50; i++) { const mid = (lo + hi) / 2; if (f(mid) > 0) hi = mid; else lo = mid; }
      lo -= 0.5;                                   // half a pixel inside the boundary, then round down
      const fl = f(lo); apply(lo);
      S.page.secGap = Math.floor(S.page.secGap * 100) / 100; S.page.itemGap = Math.floor(S.page.itemGap * 100) / 100;
      const off = isFinite(fl) ? -fl : Infinity;
      if (off <= 3.8) log.push(footTop !== null ? 'justified above the footer; footer on the bottom margin' : 'justified: last line sits on the bottom margin');
      else log.push(`flow ends ${(off * 25.4 / 96).toFixed(1)} mm short of its target (spacing capped)`);
      m = measure(doc, S, sizeKey);
      m.bottom_short_mm = footTop !== null ? 0 : +(Math.max(0, off) * 25.4 / 96).toFixed(1);
    } else { apply(0); m = measure(doc, S, sizeKey); m.bottom_short_mm = footTop !== null ? 0 : +(Math.max(0, -f0) * 25.4 / 96).toFixed(1); }
  }
  placeFooter(doc, S, sizeKey);                        // always pinned to the final style, whichever path ran above
  // Break long descriptions' risk: prefer fewer columns if lines would run out of their column.
  if (m.wide.length && S.page.cols > 1 && !want.columns) {
    S.page.cols--; const n = measure(doc, S, sizeKey);
    if (n.pages <= budget && n.wide.length < m.wide.length) { m = n; log.push(`back to ${S.page.cols} column(s) so long lines fit`); } else S.page.cols++;
  }
  return { m, log };
}

// Colophon footer: a pinned, item-less section on the bottom margin. Only known facts: city/state and website from
// the venue record, and legal lines exactly as supplied. It gives the page a finished foot and lets the layout meet
// the scorecard's equal-margin rule inside Menu Studio (which counts trailing gaps toward the page height).
function addFooter(doc, req) {
  const place = [req.venue.area, [req.venue.city, req.venue.state].filter(Boolean).join(', ')].filter(Boolean).join('  ·  ');
  const line = [place, req.venue.website].filter(Boolean).join('  ·  ');
  const legal = [].concat(req.constraints.legal_lines || req.constraints.legal || []).filter(Boolean);
  if (!line && !legal.length) return;
  if (doc.sections.some(x => x.designer_role === 'footer')) return;
  doc.sections.push({ id: 'sec_designer_footer', name: line || 'Please note', desc: legal.join('  ·  '), items: [], subs: [],
                      designer_role: 'footer', pos: { page: 0, x: 0, y: 0.9 } });
}

// Style and pin the footer for the current style: small tracked caps (the subsection voice), left edge on the margin,
// last line exactly on the bottom margin. Returns the y (px) the flow must end above, or null when there is no footer.
function placeFooter(doc, S, sizeKey) {
  const f = doc.sections.find(x => x.designer_role === 'footer');
  if (!f) return null;
  const [wIn, hIn] = MDC_SIZES[sizeKey]; const W = wIn * MDC_DPI, H = hIn * MDC_DPI, M = S.page.margin * MDC_DPI;
  f.format = { section: { f: S.sub.f, s: Math.max(8, S.sub.s), w: S.sub.w, i: false, sp: Math.max(200, S.sub.sp || 0), c: S.sub.c, cs: 'upper' } };
  const vis = f.desc ? S.section.s + 11 + S.desc.s * 1.16 : f.format.section.s * 1.16;
  const top = H - M - vis;
  f.pos = { page: 0, x: +(M / W).toFixed(5), y: +(top / H).toFixed(5) };
  return top;
}

function scaleStyle(base, k) {
  const T = JSON.parse(JSON.stringify(base));
  for (const l of ['title', 'subtitle', 'section', 'sub', 'name', 'brand', 'desc', 'price']) T[l].s = Math.round(base[l].s * (l === 'title' ? Math.min(k, 1.35) : k));
  T.page.itemGap = Math.round(base.page.itemGap * k); T.page.secGap = Math.round(base.page.secGap * k);
  return T;
}

// ---------------------------------------------------------------- main
export function design(input, options = {}) {
  const req = normalizeRequest(input);
  // Facts supplied beside a voice note (venue record, census row) only fill gaps; they never override what was said.
  for (const [k, v] of Object.entries(options.venue || {})) if (v && !req.venue[k]) req.venue[k] = v;
  if (options.demographics && !req.demographics) req.demographics = options.demographics;
  if (options.constraints) req.constraints = { ...options.constraints, ...req.constraints };
  const risk = new Set(); const questions = [...(req.questions || [])];
  const priced = req.items.filter(i => i.prices.length || i.edit);
  if (!req.items.length && !(req.base_doc && req.base_doc.sections && req.base_doc.sections.length)) { questions.push('No items were supplied.'); risk.add('no_items'); }
  if (priced.length < req.items.length) risk.add('missing_prices');
  const fromDraft = !!(req.base_doc && Array.isArray(req.base_doc.sections) && req.base_doc.sections.length);
  if (!req.venue.name && !(fromDraft && req.base_doc.title)) { questions.push('What name should head the menu?'); risk.add('missing_venue_name'); }
  if (!(req.constraints.legal_lines || req.constraints.legal)) { risk.add('legal_lines_not_supplied'); questions.push('Should the menu carry any legal lines (ABV note, allergen statement, consumer advisory, gratuity policy)? Please give the exact wording.'); }
  if (req.menu_type === 'Happy hour page' && !(req.voice && req.voice.hours) && !req.constraints.hours) questions.push('What are the happy hour days and times?');
  if (req.items.some(i => !i.list && !i.edit)) risk.add('unplaced_items');
  for (const l of req.lists || []) if (l && !req.items.some(i => i.list === l)) { risk.add('empty_list'); questions.push(`The ${LIST_BY_KEY[l]?.label || l} list was requested but has no items.`); }
  if (req.brand.logo) risk.add('logo_not_supported_in_menu_studio');
  // Library 80th percentile of items per list (phg_menu_doc_class, beverage/mixed/happy hour menus).
  const P80 = { cocktails: 18, beer: 20, wine: 18, non_alcoholic: 16, whiskey: 15, tequila: 13, cider_seltzer: 4 };
  const counts = {};
  for (const i of req.items) { const k = /^wine/.test(i.list || '') ? 'wine' : i.list; counts[k] = (counts[k] || 0) + 1; }
  for (const [k, n] of Object.entries(counts)) if (k && n > (P80[k] || (/^food/.test(k) ? 40 : 6)) * 1.25) {
    risk.add('long_list'); questions.push(`The ${LIST_BY_KEY[k]?.label || k} list has ${n} items, well above what comparable menus run. Would a separate page for it suit the venue?`);
  }

  const sizeKey = (!req.format.size && !req.format.screen && req.base_doc?.size) ? req.base_doc.size : pickSize(req.format);
  const ranked = rankLooks(req);
  const n = Math.max(1, Math.min(3, options.options || (options.look ? 1 : 3)));
  const chosen = options.look ? [ranked.find(r => r.look.k === options.look) || { look: LOOK_BY_KEY[options.look], why: [] }] : diverse(ranked, n);

  const out = chosen.map((r, idx) => {
    const style = styleForLook(r.look);
    if (req.format.columns) style.page.cols = req.format.columns;
    const tuning = tuneStyle(req, r.look, style);
    const accent = (req.brand.colours && req.brand.colours[0]) || r.look.accent;
    const venueKey = normVenue(req.venue.type);
    const built = fromDraft
      ? buildDocFromBase(req, r.look, { accent, order: [...(ORDER[venueKey] || ORDER.default), ...FOOD] })
      : buildDoc(req, r.look, { accent });
    const { doc, changes, title_missing } = built;
    if (options.standards) for (const c of applyStandards(doc, options.standards)) changes.push(c);
    if (built.questions) for (const q of built.questions) questions.push(q);
    if (built.flags) for (const f of built.flags) risk.add(f);
    const noGarnish = itemsOf(doc).filter(({ it, s }) => (it.meta?.section === 'cocktails' || /cocktail/i.test(s.name)) && it.desc && !(it.components || []).some(c => /garnish/i.test(c.role || '')));
    if (noGarnish.length) questions.push(`Garnish: which garnish goes on ${noGarnish.map(x => `"${x.it.name}"`).join(', ')}? (Printed garnishes are a scorecard requirement for cocktails.)`);
    if (!fromDraft) for (const { it, s, sub } of itemsOf(doc)) {
      if (s.designer_role) continue;
      for (const q of contentGaps(it, it.meta?.section || listForName(sub?.name || s.name))) { questions.push(q); risk.add(gapFlag(q)); }
    }
    addFooter(doc, req);
    const { m, log } = fit(doc, style, sizeKey, req.format);
    const optRisk = [];
    if (req.format.pages && m.pages > req.format.pages) optRisk.push('too_many_items_for_format');
    if (m.overflowing.length) optRisk.push('section_taller_than_page');
    if (m.wide.length) optRisk.push('lines_may_exceed_column');
    // Page breaks for multi-page menus: start each overflow page at a whole section (Menu Studio "Start on a new page").
    return {
      option: String.fromCharCode(65 + idx), look: r.look.k, look_label: r.look.label, look_note: r.look.note,
      why: r.why, score: r.score,
      menu_studio_file: { app: MDC_FILE_APP, schema_version: MDC_FILE_VERSION, saved_at: new Date().toISOString(),
                          preset: r.look.base, size: sizeKey, style, doc },
      fit: m, fit_log: log, tuning, changes, risk_flags: optRisk, title_missing,
    };
  });
  for (const o of out) for (const f of o.risk_flags) risk.add(f);
  return { request: req, size: sizeKey, options: out, questions: [...new Set(questions)], risk_flags: [...risk] };
}

function diverse(ranked, n) {
  // Top pick, then the best-scoring looks that differ in darkness so options are real alternatives.
  const dark = k => ['noir', 'deco'].includes(k);
  const picks = [ranked[0]];
  for (const r of ranked.slice(1)) {
    if (picks.length >= n) break;
    if (picks.length === 1 && dark(r.look.k) === dark(picks[0].look.k) && ranked.some(x => dark(x.look.k) !== dark(picks[0].look.k) && x.score >= ranked[0].score - 4) && r.score < ranked[0].score) continue;
    picks.push(r);
  }
  return picks;
}

function pickSize(f) {
  const o = f.orientation === 'landscape' ? 'l' : 'p';
  const s = String(f.size || '').toLowerCase();
  if (f.medium === 'screen') return f.screen === 'tv' ? 'letter_l' : 'half';
  if (/tabloid|11 ?x ?17/.test(s)) return o === 'l' ? 'tabloid_l' : 'tabloid';
  if (/legal/.test(s)) return 'legal_' + o;
  if (/half|5\.5/.test(s)) return o === 'l' ? 'half_l' : 'half';
  if (/tent|4 ?x ?6/.test(s)) return o === 'l' ? 'tent_l' : 'tent';
  if (/a4/.test(s)) return 'a4_' + o;
  if (/a5/.test(s)) return 'a5_' + o;
  if (/rack/.test(s)) return 'rack_' + o;
  if (/square/.test(s)) return 'square8';
  if (MDC_SIZES[s]) return s;
  return 'letter_' + o;
}

// ---------------------------------------------------------------- colour maths
function hex2rgb(h) { const x = h.replace('#', ''); const n = parseInt(x.length === 3 ? x.split('').map(c => c + c).join('') : x, 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function lum(h) { return hex2rgb(h).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }).reduce((a, v, i) => a + v * [0.2126, 0.7152, 0.0722][i], 0); }
export function contrast(a, b) { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); }
function pushContrast(fg, bg, need) {
  const toward = lum(bg) > 0.4 ? 0 : 255; let [r, g, b] = hex2rgb(fg);
  for (let i = 0; i < 40 && contrast(rgb2hex(r, g, b), bg) < need; i++) { r += (toward - r) * 0.12; g += (toward - g) * 0.12; b += (toward - b) * 0.12; }
  return rgb2hex(r, g, b);
}
function rgb2hex(r, g, b) { return '#' + [r, g, b].map(v => Math.round(v).toString(16).padStart(2, '0')).join(''); }
