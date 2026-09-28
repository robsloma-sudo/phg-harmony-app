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
// Round 2: the subtitle deck has a floor too (11 px = 8.25 pt; 6.75 pt tracked caps vanished in bar light).
const FLOOR = { name: 14, desc: 11, price: 14, section: 13, sub: 11, subtitle: 11 };

// ---------------------------------------------------------------- request normalisation
// Accepts brief-style payloads ({venue, menu_type, lists, items, brand, format, constraints, demographics})
// or parse-voice output ({sections, design, venue_name, ...}). Returns one shape.
export function normalizeRequest(input = {}) {
  if (input.sections && input.design) return fromVoice(input);
  if ('base_doc' in input && Array.isArray(input.items)) return { questions: [], voice: null, ...input };   // handoff.taskToRequest
  const p = input.input_payload || input;
  const items = (p.items || []).map(it => ({
    name: it.name, description: it.description || it.desc || null, list: normList(it.list),
    sub: it.sub || it.serve_format || null, abv: it.abv ?? null, garnish: it.garnish || null, pour: it.pour || null, brand: it.brand || '',
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
    voice: null, questions: [], pour_notes: Array.isArray(p.pour_notes) ? p.pour_notes : [],
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
    pour_notes: (v.pours || []).filter(p => p.single),
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
// Section order. Scorecard §1 criterion 5 example: cocktails → beer → wine → spirits → non-alcoholic. Mocktails sit
// right after the cocktails, styled like them (zero-proof as a peer: Dandelyan, NoMad; knowledge/03 [4][10]); soft drinks
// (non-alcoholic) sit last with equal type treatment (both reviewers, round 1, marked it down when it sat between alcoholic lists).
// Conventional back-bar order, light to dark (panel round 1: vodka, gin, rum, tequila, mezcal, whiskey).
const SPIRITS_ORDER = ['vodka', 'gin', 'rum', 'tequila', 'mezcal', 'whiskey', 'brandy_cognac', 'liqueurs_amari', 'sake_soju'];
const WINES = ['wine_sparkling', 'wine_white', 'wine_rose', 'wine_red', 'wine'];
const ORDER = {
  default:       ['cocktails', 'beer', 'cider_seltzer', ...WINES, 'spirits', ...SPIRITS_ORDER, 'mocktails', 'non_alcoholic'],
  brewery:       ['beer', 'cider_seltzer', 'cocktails', ...WINES, 'spirits', ...SPIRITS_ORDER, 'mocktails', 'non_alcoholic'],
  dive_bar:      ['beer', 'cocktails', 'cider_seltzer', 'whiskey', 'tequila', 'vodka', 'gin', 'rum', 'mezcal', ...WINES, 'brandy_cognac', 'liqueurs_amari', 'sake_soju', 'mocktails', 'non_alcoholic'],
  wine_bar:      [...WINES, 'cocktails', 'beer', 'cider_seltzer', 'brandy_cognac', 'liqueurs_amari', 'whiskey', 'gin', 'vodka', 'rum', 'tequila', 'mezcal', 'sake_soju', 'mocktails', 'non_alcoholic'],
  latin_cantina: ['cocktails', 'tequila', 'mezcal', 'beer', 'cider_seltzer', ...WINES, 'whiskey', 'rum', 'gin', 'vodka', 'brandy_cognac', 'liqueurs_amari', 'sake_soju', 'mocktails', 'non_alcoholic'],
};
ORDER.sports_bar = ORDER.dive_bar; ORDER.fine_dining = ORDER.wine_bar;
const FOOD = ['food_small', 'food_mains', 'food_sides', 'food_dessert'];
const WINE_SUB = { wine_sparkling: 'Sparkling', wine_white: 'White', wine_rose: 'Rosé', wine_red: 'Red' };

let seq = 0;
const id = p => `${p}_d${++seq}`;

function mdcItem(it, accent, emphasise) {
  // A HOUSE badge beside a name that already says "House" repeats itself (panel round 2); the accent carries it.
  const badges = [...new Set((it.flags || []).map(f => BADGE_FOR_FLAG[f]).filter(Boolean))].filter(b => !(b === 'house' && /^house\b/i.test(it.name || '')));
  let desc = it.description || '';
  // Garnish from the venue's answer closes the line after a middle dot ("… agave · salt rim"), one line kept.
  const garnish = String(it.garnish || '').trim();
  // Printed unless the whole phrase is already in the line ("lime wedge" still prints after "fresh lime"); the speaker's
  // casing is kept so proper nouns survive (Tajín rim).
  if (garnish && !desc.toLowerCase().includes(garnish.toLowerCase())) desc = (desc ? `${desc} · ` : '') + garnish;
  // Tags lead the description line instead of Menu Studio's raised 7 pt grey badge (panel round 5, 9 of 15 reviewers:
  // "NEW disappears in bar light"; "the signature is marked by gold alone", WCAG 1.4.1). The word prints at description
  // size as the line's first token ("New · Mezcal, Campari, …"); flags stay in meta.designer_flags. "House special" beside
  // a name that already says "House" reads "Signature" (the speaker's "house special", without the repeat).
  const tagWords = badges.map(b => b === 'house' ? 'House special' : b === 'new' ? 'New' : b === 'seasonal' ? 'Seasonal' : null).filter(Boolean);
  if ((it.flags || []).includes('house_special') && /^house\b/i.test(it.name || '')) tagWords.unshift('Signature');
  const lead = tagWords.filter(w => !new RegExp('^' + w, 'i').test(desc));
  if (lead.length) desc = [...lead, desc].filter(Boolean).join(' · ');
  // A pour that differs from the list's (panel round 3: a 10 oz imperial stout under "16 oz pours unless noted").
  if (it.pour && !/\b\d+(?:\.\d+)?\s*oz\b/i.test(desc)) desc = (desc ? `${desc} · ` : '') + `${it.pour} pour`;
  // Beer convention: style/description first, then ABV ("Oatmeal stout with coffee · 6.2% ABV").
  if (it.abv !== null && it.abv !== undefined && it.abv !== '') desc = (desc ? `${desc} · ` : '') + `${it.abv}% ABV`;
  const node = {
    id: id('itm'), source: 'manual', origin: { venue_key: null, item_name: it.name },
    name: it.name, brand: it.brand || '', desc,
    prices: (it.prices || []).filter(p => isFinite(p.value)).map(p => ({ id: id('prc'), label: p.label || '', value: p.value, source: 'manual' })),
    badges: [],
    meta: { canonical: null, identity_class: null, section: it.list, family: null, subfamily: null, serve_format: it.sub || null,
            venue_heading: null, abv: it.abv ?? null, designer_flags: it.flags || [],
            public_visibility: { item: true, description: true, price: true, brand: true, ingredients: true, house_recipe: true },
            public_components: {} },
    evidence: null,
    ...(garnish ? { components: [{ role: 'garnish', name: garnish }] } : {}),
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
    // A new item takes the closing edge when a house/featured item already holds the first (both edges sell).
    const fresh = arr.filter(i => !hot.includes(i) && (i.flags || []).includes('new'));
    if (hot.length === 1 && fresh.length) hot.push(fresh[0]);
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
    // A HOUSE badge under a House/Signature subhead repeats the subhead (panel round 1): drop the badge there.
    const dropHouse = (sub, node) => { if (/house|signature/i.test(sub)) node.desc = String(node.desc || '').replace(/^(?:House special|Signature)(?: · |$)/, ''); return node; };
    for (const [sub, arr] of bySub) sec.subs.push({ id: id('sub'), name: sub, items: promote(arr).map(i => dropHouse(sub, mdcItem(i, accent, true))) });
    return sec;
  };

  let wineDone = false;
  for (const l of lists) {
    if (/^wine/.test(l)) {
      if (wineDone) continue; wineDone = true;
      const WHITE = /sauvignon blanc|chardonnay|pinot gri[gs]io?|riesling|chenin|albari[nñ]o|gr[uü]ner|viognier|verdejo|vermentino|moscato|white/i;
      const RED = /pinot noir|malbec|cabernet|merlot|syrah|shiraz|zinfandel|tempranillo|sangiovese|nebbiolo|grenache|garnacha|rioja|chianti|red/i;
      const items = req.items.filter(i => /^wine/.test(i.list || '')).map(i => {
        if (i.list !== 'wine') return i;
        const t = `${i.name} ${i.description || ''}`;
        // Sparkling and rosé first (panel round 5: "Prosecco sat under Red / By the glass, after the Cabernet").
        const SPARK = /prosecco|cava|champagne|cr[eé]mant|sparkling|brut|lambrusco|franciacorta|\bsekt\b|p[eé]t[- ]?nat/i;
        const ROSE = /\bros[eé]\b|rosado|rosato/i;
        const style = SPARK.test(i.name) ? 'wine_sparkling' : ROSE.test(i.name) ? 'wine_rose' : WHITE.test(i.name) ? 'wine_white' : RED.test(i.name) ? 'wine_red'
          : SPARK.test(t) ? 'wine_sparkling' : ROSE.test(t) ? 'wine_rose' : WHITE.test(t) ? 'wine_white' : RED.test(t) ? 'wine_red' : null;
        // "By the glass" says nothing once every price is labelled glass / bottle; the style is the better heading.
        return style ? { ...i, list: style, sub: (i.prices || []).every(p => p.label) ? null : i.sub } : i;
      });
      // One Wine section; styles become subsections in the classic order (sparkling → white → rosé → red).
      const subOrder = ['Sparkling', 'White', 'Rosé', 'Red'];
      const sec = buildSection('Wine', items, i => WINE_SUB[i.list] || i.sub || null);
      sec.subs.sort((a, b) => (subOrder.indexOf(a.name) + 1 || 50) - (subOrder.indexOf(b.name) + 1 || 50));
      // Say only what was built (panel round 5: the reasoning claimed White and Rosé subsections the page did not have).
      const styled = sec.subs.filter(x => subOrder.includes(x.name)).map(x => x.name);
      if (styled.length >= 2) changes.push(`Wine ordered light to full: ${styled.join(', ')}.`);
      sections.push(sec);
      continue;
    }
    // One zero-proof program (panel round 1: all 15 reviewers marked down mocktails and soft drinks split across pages):
    // crafted drinks and softs share one section, as two subsections.
    if (l === 'mocktails' && lists.includes('non_alcoholic')) continue;
    if (l === 'non_alcoholic' && lists.includes('mocktails')) {
      const zp = req.items.filter(i => i.list === 'mocktails' || i.list === 'non_alcoholic');
      const zs = buildSection(sectionLabel(l, look), zp, i => i.list === 'mocktails' ? 'Crafted' : 'Soft Drinks & Coffee');
      zs.subs.sort((a, b) => (a.name === 'Crafted' ? 0 : 1) - (b.name === 'Crafted' ? 0 : 1));
      sections.push(zs);
      changes.push('Mocktails and soft drinks set together in one zero-proof section (Crafted / Soft Drinks & Coffee).');
      continue;
    }
    const label = sectionLabel(l, look);
    sections.push(buildSection(label, req.items.filter(i => i.list === l), i => i.sub || null));
  }
  // A one- or two-item agave list does not earn its own header (round-1 review): tequila and mezcal share one section,
  // each keeping its own subsection so both lists stay visibly equal.
  const tq = sections.find(x => x.name === 'Tequila'), mz = sections.find(x => x.name === 'Mezcal');
  if (tq && mz && (countItems(tq) <= 2 || countItems(mz) <= 2)) {
    const subs = tq.subs.length ? tq.subs.map(b => ({ ...b, name: /^tequila/i.test(b.name) ? b.name : `Tequila ${b.name}` })) : [{ id: id('sub'), name: 'Tequila', items: tq.items }];
    if (tq.subs.length && tq.items.length) subs.unshift({ id: id('sub'), name: 'Tequila', items: tq.items });
    subs.push(...(mz.subs.length ? mz.subs.map(b => ({ ...b, name: `Mezcal ${b.name}` })) : [{ id: id('sub'), name: 'Mezcal', items: mz.items }]));
    tq.name = 'Tequila & Mezcal'; tq.items = []; tq.subs = subs;
    sections.splice(sections.indexOf(mz), 1);
    changes.push('Tequila and Mezcal share one section with their own subsections (a one-item list does not earn a full header).');
  }
  // Several small spirit lists read better as one Spirits section with a subsection per list (same level for all,
  // so every list is treated equally) than as a row of one- and two-item headers.
  const SPIRIT_NAMES = ['Vodka', 'Gin', 'Rum', 'Tequila', 'Mezcal', 'Tequila & Mezcal', 'Whiskey', 'Brandy & Cognac', 'Liqueurs & Amari', 'Sake & Soju'];
  const sp = sections.filter(x => SPIRIT_NAMES.includes(x.name));
  if (sp.length >= 3 && sp.reduce((a, x) => a + countItems(x), 0) <= 24) {
    const merged = { id: id('sec'), name: 'Spirits', items: [], subs: [] };
    for (const x of sp) {
      if (x.subs.length) for (const b of x.subs) merged.subs.push({ ...b, name: /tequila|mezcal/i.test(b.name) || x.name === b.name ? b.name : `${x.name} · ${b.name}` });
      if (x.items.length) merged.subs.push({ id: id('sub'), name: x.name, items: x.items });
    }
    sections.splice(sections.indexOf(sp[0]), 0, merged);
    for (const x of sp) sections.splice(sections.indexOf(x), 1);
    changes.push(`Spirits: ${sp.map(x => x.name).join(', ')} set as subsections of one Spirits section (each list at the same level).`);
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
  else if (req.venue.area && venueWord(req.venue.type)) subtitle = `${venueWord(req.venue.type)}  ·  ${req.venue.area}`;
  else {
    const offer = sections.map(x => x.name).join('  ·  ');
    if (sections.length >= 2 && offer.length <= 64) subtitle = offer;       // the city goes in the footer, never twice
  }
  return { doc: { id: 'doc_designer', title: title || 'Menu', subtitle, sections }, changes, title_missing: !title };
}

// The venue's own kind, as a plain word for the masthead ("Cantina · RiNo"); only for recognised venue types.
function venueWord(t) {
  return { latin_cantina: 'Cantina', cocktail_lounge: 'Cocktail bar', brewery: 'Taproom', wine_bar: 'Wine bar', hotel_bar: 'Hotel bar',
           dive_bar: 'Bar', sports_bar: 'Sports bar', tiki: 'Tiki bar', fine_dining: 'Restaurant', restaurant: 'Restaurant' }[normVenue(t)] || null;
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
    // One gold (panel round 5): the brand line in the look's own accent sat beside heads in the requested colour.
    if (style.brand && look.accent && String(style.brand.c).toLowerCase() === look.accent.toLowerCase()) style.brand.c = accent;
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
  if (style.subtitle.cs === 'upper' && style.subtitle.sp > 120) style.subtitle.sp = 120;
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
  // Fill is measured to the last line of ink, not the cursor (which carries the trailing item and section gaps, ~6%
  // of a page: round 3's taproom page read 0.86 full with 36 mm of bare paper under it).
  let pages = L.pages, fill = Math.round(((L.pages - 1) + Math.max(0, Math.min(1, (L.contentBottom - L.M) / (L.H - 2 * L.M)))) * 100) / 100;
  if (foot && L.pages === 1) {
    const usable = L.H - 2 * L.M;
    const reserve = (foot.desc ? S.section.s + 11 + S.desc.s * 1.16 : Math.max(8, S.sub.s) * 1.16) + Math.max(S.page.secGap, S.name.s * 1.3);
    if (L.contentBottom + reserve > L.H - L.M) pages = 2;
    fill = Math.round(((L.contentBottom - L.M) / (usable - reserve)) * 100) / 100;
  }
  return { pages, cols: L.n, colW: Math.round(L.colW), overflowing: L.overflow.map(o => o.name), wide, imbalance: L.imbalance, fill };
}

// Most space above a section head, item gap + section gap (px at 96 dpi; 40 px = 10.6 mm). Panel round 3: 16–18 mm
// gaps read as "scattered islands"; every lens asked for one fixed gap near 10 mm and spare height spent on type.
export const SEC_SPACE_MAX = 40;
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
    let did = null;
    for (const f of steps) { did = f(); if (did) break; }        // one remedy at a time, in order (v1 ran them all)
    if (!did) break;
    log.push(did); m = measure(doc, S, sizeKey);
  }
  // Compose: when everything fits with room to spare, search columns x scale for the layout that fills the page
  // best (target ~88% of the last page) while keeping every line inside its column. A half-empty page reads unfinished;
  // bigger type is also the single best legibility gain in bar lighting.
  // Round 3: section gaps are capped at 10 mm, so spare height must go into type, not gaps: compose below 0.86 fill.
  if (m.pages <= budget && m.fill - (m.pages - 1) < 0.86) {
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
        const measurePenalty = Math.max(0, r.colW - 528) / 300 + (cols === 1 && r.colW > 640 ? 0.35 : 0);
        // Unbalanced columns (one ends far above the other) read as a mistake; single-column pages have none.
        // Menu Studio prints prices inline beside the name when there is more than one column (mdcDrawItem), so only a
        // single column gives the scorecard's one right-aligned price column. Multi-column must earn its place.
        // A line wider than its column runs into the next one in Menu Studio (no wrapping): heavy cost per line.
        const score = -Math.abs(0.88 - last) * 3 - measurePenalty - (r.imbalance || 0) * 4 - (cols > 1 ? 0.1 : 0) - r.wide.length * 0.3 - r.wide.reduce((a, x) => a + Math.max(0, x.over), 0) / 150 + (cols === 1 ? 0.08 : 0) + Math.min(T.name.s, 20) / 100;
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
      if (S.page.secGap < Math.min(SEC_SPACE_MAX - S.page.itemGap, Math.round(S.name.s * 1.6))) S.page.secGap += 2;
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
  // - (round 1 gave a single column wider than ~5.5 in leader dots; round 5 retired that, see below).
  S.section.s = Math.max(S.section.s, Math.round(S.name.s * 1.3));
  // Round 2: every lens objected to 150 mm leaders across a full-width column. First narrow the measure toward ~5.5 in
  // with wider side margins (Menu Studio's margin is one value, so top and bottom grow too) while it still fits;
  // a column that stays wide keeps its right-aligned price column without leaders (round 5).
  if (S.page.cols === 1 && measure(doc, S, sizeKey).colW > 528) {
    const w = MDC_SIZES[sizeKey][0], m0 = S.page.margin;
    for (const mg of [1.5, 1.4, 1.3, 1.25, 1.15, 1.0]) {
      if (mg <= m0 || mg * 2 >= w - 3) continue;
      S.page.margin = mg;
      const r = measure(doc, S, sizeKey);
      if (r.pages <= budget && !r.wide.length && r.fill - (r.pages - 1) <= 0.97) { log.push(`narrowed the measure: ${mg}" side margins (column ${(r.colW / 96).toFixed(2)} in)`); break; }
      S.page.margin = m0;
    }
  }
  // Round 5 (11 of 15 reviewers): leaders forced onto a column that could not be narrowed ran ~6 in per row, became the
  // heaviest texture on the page and ended at different x before 11.50 / 11 / 40 / 7. Menu Studio has one margin value
  // (S17), so when the measure stays wide the right-aligned price column stands alone and leaders are no longer forced
  // on; a look that asks for leaders (taproom, dive) keeps them.
  if (S.page.cols === 1 && !S.page.dots && measure(doc, S, sizeKey).colW > 528) log.push('no leader dots: the wide single column keeps a clean right-aligned price column');
  m = measure(doc, S, sizeKey);
  if (m.pages > budget) { S.section.s = Math.max(S.name.s + 2, S.section.s - 3); m = measure(doc, S, sizeKey); }
  if (m.pages === 1) {
    const footTop = placeFooter(doc, S, sizeKey);
    const H = MDC_SIZES[sizeKey][1] * MDC_DPI, M = S.page.margin * MDC_DPI;
    const s0 = S.page.secGap, i0 = S.page.itemGap;
    // f(g) = how far the flow's last line is from where it should end (0 = on target). With a footer the flow stops
    // a clear break above it (twice the section gap, at least two lines); without one, on the bottom margin as far as
    // Menu Studio's page count (which includes trailing gaps) allows.
    // Section gap capped at 10 mm (panel round 3: 16–18 mm gaps read as scattered islands; "one fixed gap, let the
    // spare height pool at the bottom"). Item gaps may still open a little.
    const apply = g => {
      S.page.itemGap = Math.max(2, Math.min(Math.max(i0, Math.round(S.name.s * 0.75)), i0 + g * 0.3));
      S.page.secGap = Math.min(Math.max(4, SEC_SPACE_MAX - S.page.itemGap), Math.max(4, s0 + g));
    };
    const f = g => {
      apply(g);
      const L = layout({ doc, style: S, size: sizeKey });
      if (L.pages > 1) return Infinity;
      return footTop !== null ? L.contentBottom + Math.max(S.page.secGap, S.name.s * 1.3) - footTop : L.contentBottom - (H - M);
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

// Descriptions from facts already in the inputs, and one house style for description copy (Content Reviewer round 2):
// - an item heard under an expression subsection gets that expression + spirit ("Blanco tequila");
// - a beer whose name carries its style prints the style before the ABV ("IPA · 6.2% ABV");
// - ingredient lists are serial lists without a closing "and" ("Mint, lime, soda"); "X infused" -> "X-infused".
const BEER_STYLES = ['double ipa', 'hazy ipa', 'ipa', 'pale ale', 'pilsner', 'pils', 'lager', 'stout', 'porter', 'amber', 'wheat', 'hefeweizen', 'gose', 'saison', 'kolsch', 'kölsch', 'sour', 'red ale', 'brown ale', 'blonde'];
function knownFacts(doc) {
  const changes = [];
  for (const { it, s, sub } of itemsOf(doc)) {
    const list = it.meta?.section || listForName(sub?.name || s.name);
    const d0 = String(it.desc || '');
    if (!d0.trim() && sub && ['tequila', 'mezcal'].includes(list)) {
      const expr = sub.name.replace(/^(tequila|mezcal)\s*/i, '').trim();
      if (expr && /blanco|reposado|a[nñ]ejo|joven|extra/i.test(expr)) { it.desc = `${expr.charAt(0).toUpperCase() + expr.slice(1).toLowerCase()} ${list}`; it.meta = { ...(it.meta || {}), description_source: 'inputs' }; changes.push(`"${it.name}" description "${it.desc}" from how it was listed.`); }
    }
    if (false && list === 'beer') {                       // round 3: the name already carries the style; don't repeat it
      const st = BEER_STYLES.find(x => new RegExp(`\\b${x}\\b`, 'i').test(it.name));
      if (st && /^\s*\d+(\.\d+)?%\s*ABV\s*$/i.test(d0)) { it.desc = `${st.toUpperCase() === 'IPA' || /ipa/.test(st) ? st.replace(/ipa/i, 'IPA').replace(/^./, c => c.toUpperCase()) : st.charAt(0).toUpperCase() + st.slice(1)} · ${d0.trim()}`; it.meta = { ...(it.meta || {}), style_from_name: true }; changes.push(`"${it.name}" shows its style from its name: ${it.desc}.`); }
    }
    let d = String(it.desc || '');
    const styled = d.replace(/,\s+([^,]+?)\s+and\s+([^,]+)$/i, ', $1, $2').replace(/\b(\w+) infused\b/gi, '$1-infused');
    if (styled !== d && it.meta?.description_source !== 'recipe_components') { it.desc = styled; changes.push(`"${it.name}" description set in house style (serial list, hyphenation); words unchanged.`); }
  }
  return changes;
}

// Flat sections for small fresh menus (critic round 2): Menu Studio adds 6 px after every subsection only, so a menu
// mixing sections with and without subsections can never have equal space above its headers (scorecard ±0.5 mm).
// When every subsection is short, the subsection name moves into each item's line as a fact ("Draft · …",
// "Blanco tequila") and the page gets one clean level of headers. Suggestion S7 would make this unnecessary.
const OBVIOUS_WINE = { red: /cabernet|merlot|pinot noir|malbec|syrah|shiraz|zinfandel|tempranillo|sangiovese|grenache/i,
  white: /chardonnay|sauvignon blanc|pinot gri|riesling|albari|verdejo|gr[uü]ner/i, sparkling: /prosecco|champagne|cava|cr[eé]mant|\bbrut\b/i };
function flattenSubs(doc) {
  const secs = doc.sections.filter(x => !x.designer_role);
  const total = secs.reduce((a, x) => a + countItems(x), 0);
  if (total > 24 || !secs.some(x => (x.subs || []).length) || secs.some(x => (x.subs || []).some(b => b.items.length > 4))) return [];
  const changes = [];
  for (const sec of secs) {
    if (!(sec.subs || []).length) continue;
    const moved = [];
    for (const b of sec.subs) for (const it of b.items) {
      const tag = b.name.replace(/^(tequila|mezcal)\s+(?=\S)/i, '').trim().replace(/^cans$/i, 'Can').replace(/^bottles$/i, 'Bottle');
      const d = String(it.desc || '');
      const agave = /^(tequila|mezcal)/i.test(b.name) || /tequila|mezcal/i.test(sec.name);
      if (agave && /^(blanco|reposado|a[nñ]ejo|joven|extra a[nñ]ejo)$/i.test(tag)) {
        if (!new RegExp(tag, 'i').test(d)) it.desc = d ? `${tag} · ${d}` : `${tag} ${/mezcal/i.test(b.name) ? 'mezcal' : 'tequila'}`;
      } else if (agave && /^(tequila|mezcal)$/i.test(b.name)) {
        if (!d) it.desc = b.name.charAt(0).toUpperCase() + b.name.slice(1).toLowerCase();
      } else if (OBVIOUS_WINE[tag.toLowerCase()]?.test(`${it.name} ${d}`)) {
        // "House Cabernet / Red" says nothing new (panel round 2): the grape already names the colour.
      } else if (!/^by the glass/i.test(b.name) || !(it.prices || []).some(p => p.label)) {
        if (!new RegExp('^' + tag, 'i').test(d)) it.desc = d ? `${tag} · ${d}` : tag;
      }
      it.meta = { ...(it.meta || {}), serve_format: it.meta?.serve_format || b.name };
      moved.push(it);
    }
    sec.items = [...(sec.items || []), ...moved];
    changes.push(`${sec.name}: subsections (${sec.subs.map(b => b.name).join(', ')}) folded into each item's line, so every header has the same space above it.`);
    sec.subs = [];
  }
  return changes;
}

// A tag word that pushes its description past the column (descriptions do not wrap in Menu Studio, S6) goes back to
// Menu Studio's badge beside the name, so the line stays inside its column (panel round 5).
const TAG_LEAD = /^(House special|Signature|New|Seasonal) · /;
const BADGE_FOR_WORD = { 'House special': 'house', Signature: null, New: 'new', Seasonal: 'seasonal' };
export function tagsThatFit(doc, S, sizeKey) {
  const wide = new Set(measure(doc, S, sizeKey).wide.map(w => w.item));
  const changes = [];
  for (const sec of doc.sections) for (const it of [...(sec.items || []), ...(sec.subs || []).flatMap(b => b.items)]) {
    const mm = String(it.desc || '').match(TAG_LEAD);
    if (!mm || !wide.has(it.name)) continue;
    it.desc = it.desc.slice(mm[0].length);
    if (BADGE_FOR_WORD[mm[1]]) it.badges = [...new Set([...(it.badges || []), BADGE_FOR_WORD[mm[1]]])];
    changes.push(`"${it.name}": "${mm[1]}" kept as Menu Studio's badge; in the description line it would run past the column.`);
  }
  return changes;
}

// Pour sizes and glass/bottle labels printed once (Design Critic round 3; professional drinks lists head their price
// columns instead of repeating "1 oz / 1.5 oz / 2.5 oz" on every line). When every item in a list shares the same
// labels, the labels become that list's description line ("1 oz  ·  1.5 oz  ·  2.5 oz") and the rows print bare
// values ("9 / 13 / 20"). Values never change; the labels stay on each item in meta.price_labels.
function pourHeaders(doc) {
  const changes = [];
  for (const sec of doc.sections) for (const holder of [sec, ...(sec.subs || [])]) {
    const items = holder.items || [];
    if (!items.length || holder.designer_role) continue;
    // Items may carry a prefix of the longest ladder (wine: "Glass 11 / Bottle 40" beside "Glass 10", panel round 2):
    // the key reads "Glass · Bottle" and a single value sits under the first label.
    const labs = it => (it.prices || []).map(p => p.label || '');
    const widest = items.reduce((a, it) => labs(it).length > labs(a).length ? it : a, items[0]);
    const labels = labs(widest);
    if (labels.length < 2 || labels.some(l => !l) || !items.every(it => labs(it).length && labs(it).every((l, i) => l === labels[i]))) continue;
    if (String(holder.desc || '').trim()) continue;
    // Some items carry only part of the ladder (Prosecco "Glass 10" beside "Glass 11 / Bottle 40"): a key line that
    // Menu Studio can only set flush left, 6 in from the prices, leaves the lone price ambiguous (panel round 5, 14 of 15
    // reviewers). Each line then leads with its own units instead ("Glass / bottle · Cabernet Sauvignon, …",
    // "Glass · Glera, …"), and no key line prints. Values never change; labels stay in meta.price_labels.
    if (items.some(it => labs(it).length < labels.length)) {
      for (const it of items) {
        const lead = labs(it).map((l, i) => i ? l.toLowerCase() : l.charAt(0).toUpperCase() + l.slice(1).toLowerCase()).join(' / ');
        const d = String(it.desc || '');
        if (!new RegExp('^' + lead.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&'), 'i').test(d)) it.desc = d ? `${lead} · ${d}` : lead;
        it.meta = { ...(it.meta || {}), price_labels: labs(it) }; it.prices = it.prices.map(p => ({ ...p, label: '' }));
      }
      changes.push(`${holder.name}: ${labels.join(' / ')} named at the start of each line (${items.map(it => `${it.name}: ${labs(it).join(' / ')}`).join('; ')}), so a single price is never read as the wrong unit.`);
      continue;
    }
    holder.desc = labels.join('  ·  ');
    for (const it of items) { it.meta = { ...(it.meta || {}), price_labels: labs(it) }; it.prices = it.prices.map(p => ({ ...p, label: '' })); }
    changes.push(`${holder.name}: ${labels.join(' / ')} printed once under the heading; each line shows the prices in that order (labels kept in meta.price_labels).`);
  }
  // Every subsection of a section carries the same labels (wine: Glass · Bottle): say it once, under the section heading.
  for (const sec of doc.sections) {
    const subs = (sec.subs || []).filter(b => b.items.length);
    if (subs.length < 2 || sec.items.length || String(sec.desc || '').trim()) continue;
    const d = subs[0].desc;
    if (d && subs.every(b => b.desc === d) && subs.every(b => b.items.every(i => i.meta?.price_labels))) {
      sec.desc = d; for (const b of subs) b.desc = '';
      changes.push(`${sec.name}: "${d}" printed once for the whole section.`);
      continue;
    }
    // Most subsections share one key and the rest carry their own (panel round 4, 11 of 15 reviewers: "1 oz · 1.5 oz ·
    // 2.5 oz" printed five times under Vodka, Gin, Rum, Tequila, Mezcal): the shared key prints once under the section
    // heading and only the exceptions keep theirs ("1.5 oz · 3 oz" under Whiskey), so every price still has a key.
    const keyed = subs.filter(b => b.desc && b.items.every(i => i.meta?.price_labels));
    if (keyed.length !== subs.length) continue;
    const count = {}; for (const b of keyed) count[b.desc] = (count[b.desc] || 0) + 1;
    const [top, n] = Object.entries(count).sort((a, b) => b[1] - a[1])[0] || [];
    if (!top || n < 2 || n * 2 <= subs.length) continue;
    sec.desc = top; for (const b of subs) if (b.desc === top) b.desc = '';
    changes.push(`${sec.name}: "${top}" printed once under the heading; ${subs.filter(b => b.desc).map(b => `${b.name} keeps its own "${b.desc}"`).join(', ')}.`);
  }
  return changes;
}

// One pour size for a whole list (panel round 3, every beverage reviewer: "a beer list with no pour sizes"). The venue's
// "Drafts are poured at 16 ounces" prints once under the Draft subhead (or the list heading) as "16 oz pours", with
// "unless noted" when an item on that list states its own pour. Never invented: only what the venue said.
export function applyPourNotes(doc, notes) {
  const changes = [];
  for (const n of notes || []) for (const key of n.lists || []) {
    const [list, subName] = key.split(':');
    for (const sec of doc.sections) {
      if (sec.designer_role) continue;
      const all = [...sec.items, ...(sec.subs || []).flatMap(b => b.items)];
      if (!all.some(i => i.meta?.section === list)) continue;
      const sub = subName ? (sec.subs || []).find(b => b.name.toLowerCase() === subName.toLowerCase()) : null;
      // A folded "Draft" (flat section, "Draft · …" on each line) takes the note on the section when every item is draft.
      const holder = sub || (!subName || all.every(i => /^draft\b/i.test(i.desc || '') || (i.meta?.serve_format || '').toLowerCase() === subName.toLowerCase()) ? sec : null);
      if (!holder || String(holder.desc || '').trim()) continue;
      const items = holder === sec ? all : holder.items;
      const own = items.some(i => /\b\d+(?:\.\d+)?\s*oz pour\b/.test(i.desc || ''));
      holder.desc = `${n.pours[0]} pours${own ? ' unless noted' : ''}`;
      changes.push(`${holder.name}: "${holder.desc}" printed under the heading, as the venue said ("${n.heard}").`);
    }
  }
  return changes;
}

// A subhead left at the foot of a column or page while its first item starts the next one (panel round 3, all 15
// reviewers: "the orphaned CANS subhead"). Menu Studio keeps a section together but checks a subhead only for its own
// height, so the designer promotes that subsection to its own section ("Beer · Cans"), which moves as one block.
export function orphanSubs(doc, S, sizeKey) {
  const L = layout({ doc, style: S, size: sizeKey });
  const slot = op => `${Math.floor(op.y / L.H)}|${Math.max(0, Math.round((op.x - L.M) / (L.colW + L.gutter)))}`;
  const out = [];
  for (const op of L.ops) {
    if (op.t !== 'head' || op.lvl !== 'sub' || !op.node?.items?.length) continue;
    // Keep-with-next: the subhead stays with at least its first two items (a two-item "Cans" split 1 + 1 still reads
    // as a stray line at the top of the next column).
    const lead = op.node.items.slice(0, 2).map(it => L.ops.find(o => o.t === 'item' && o.item === it)).filter(Boolean);
    if (lead.some(o => slot(o) !== slot(op))) out.push(op.node);
  }
  return out;
}
function promoteSubs(doc, subs) {
  const changes = [];
  for (const sub of subs) {
    const i = doc.sections.findIndex(x => (x.subs || []).includes(sub));
    if (i < 0) continue;
    const sec = doc.sections[i];
    sec.subs = sec.subs.filter(b => b !== sub);
    const name = new RegExp(`\\b${sec.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i').test(sub.name) ? sub.name : `${sec.name} · ${sub.name}`;
    doc.sections.splice(i + 1, 0, { id: `${sub.id}_sec`, name, desc: sub.desc || '', items: sub.items, subs: [], designer_promoted_from: sec.id, designer_sub: { ...sub, items: undefined } });
    changes.push(`"${sub.name}" would have been left at the foot of a column without its items, so it became its own section "${name}" (Menu Studio keeps sections whole).`);
  }
  return changes;
}

// Undo a keep-with-next promotion the final plan no longer needs (panel round 4: "SPIRITS · WHISKEY" printed as a
// section head directly under Spirits in the same column once the page plan had moved the break elsewhere). The
// subsection goes back under its parent when it still sits right after it, in the same column, with no subhead
// orphaned and no page added.
export function demoteSubs(doc, S, sizeKey) {
  const changes = [];
  for (let i = doc.sections.length - 1; i > 0; i--) {
    const x = doc.sections[i], parent = doc.sections[i - 1];
    if (!x.designer_promoted_from || parent.id !== x.designer_promoted_from || x.breakBefore || x.breakCol || !x.designer_sub) continue;
    const before = layout({ doc, style: S, size: sizeKey });
    const snapshot = [...doc.sections], subs0 = [...(parent.subs || [])];
    const sub = { ...x.designer_sub, items: x.items, desc: x.desc || '' };
    parent.subs = [...subs0, sub];
    doc.sections = doc.sections.filter(y => y !== x);
    const after = layout({ doc, style: S, size: sizeKey });
    if (after.pages > before.pages || orphanSubs(doc, S, sizeKey).length) { doc.sections = snapshot; parent.subs = subs0; continue; }
    changes.push(`"${sub.name}" back under ${parent.name} as a subsection (the final page plan keeps it with its items).`);
  }
  return changes;
}

// Multi-page menus: Menu Studio moves whole sections between columns and pages, which can strand a half-empty page.
// Choose, in order, which section starts each column and page (Menu Studio's own "Start on a new column/page" flags)
// so the slots fill evenly. Order is kept, with one exception below.
function planCuts(doc, S, sizeKey) {
  const secs = doc.sections.filter(x => !x.designer_role);
  if (secs.length < 3 || secs.length > 14) return null;
  const n = Math.max(1, S.page.cols || 1);
  const clear = () => { for (const x of secs) { delete x.breakBefore; delete x.breakCol; } };
  clear();
  const L0 = layout({ doc, style: S, size: sizeKey });
  const pages = L0.pages;
  const slots = pages * n;
  if (slots < 2 || slots > 8) return null;
  let best = null;
  // enumerate order-preserving splits of secs into `slots` consecutive groups (small n: brute force)
  const rec = (start, k, cuts) => {
    if (k === slots - 1) { tryCuts([...cuts]); return; }
    for (let i = start + 1; i <= secs.length - (slots - 1 - k); i++) { cuts.push(i); rec(i, k + 1, cuts); cuts.pop(); }
  };
  const tryCuts = cuts => {
    clear();
    cuts.forEach((c, i) => { const slot = i + 1; if (slot % n === 0) secs[c].breakBefore = true; else secs[c].breakCol = true; });
    const L = layout({ doc, style: S, size: sizeKey });
    if (L.pages > pages || L.overflow.length) return;
    // fill of each column slot
    const bottoms = Array(slots).fill(0);
    for (const op of L.ops) { if (op.node?.pos) continue; const pg = Math.floor(op.y / L.H); const col = Math.max(0, Math.round((op.x - L.M) / (L.colW + L.gutter))); const k = pg * n + Math.min(col, n - 1); if (k < slots) bottoms[k] = Math.max(bottoms[k], op.y - pg * L.H); }
    if (bottoms.some(b => b === 0)) return;
    const mean = bottoms.reduce((a, b) => a + b, 0) / slots;
    // A plan that leaves a subhead at a column foot without its items is a last resort (keep-with-next, round 3).
    const score = bottoms.reduce((a, b) => a + (b - mean) ** 2, 0) + (orphanSubs(doc, S, sizeKey).length ? 1e9 : 0);
    if (!best || score < best.score) best = { score, cuts: [...cuts], fill: mean / Math.max(...bottoms) };
  };
  rec(0, 0, []);
  clear();
  if (!best) return null;
  best.cuts.forEach((c, i) => { const slot = i + 1; if (slot % n === 0) secs[c].breakBefore = true; else secs[c].breakCol = true; });
  return { fill: best.fill, cuts: best.cuts, msg: `planned ${pages} pages × ${n} columns: ${best.cuts.map(c => secs[c].name).join(', ')} start new ${n > 1 ? 'columns/pages' : 'pages'}` };
}
// The one move the plan may make (panel round 4, all 15 reviewers: page 1 ended 121 mm short while Zero Proof closed a
// crammed page 2): the zero-proof section may sit directly after the cocktails, as their peer on the same page
// (knowledge/03: Dandelyan, NoMad), when that fills the pages clearly more evenly (mean/max column fill +0.05).
export const ZP_MOVE_GAIN = 0.05;
const secItems = x => [...(x.items || []), ...(x.subs || []).flatMap(b => b.items || [])];
function planPages(doc, S, sizeKey) {
  const base = planCuts(doc, S, sizeKey);
  if (!base) return null;
  const secs = doc.sections.filter(x => !x.designer_role);
  const zi = secs.findIndex(x => secItems(x).length && secItems(x).every(i => ['non_alcoholic', 'mocktails'].includes(i.meta?.section)));
  const ci = secs.findIndex(x => secItems(x).length && secItems(x).every(i => i.meta?.section === 'cocktails'));
  if (zi < 0 || ci < 0 || zi <= ci + 1) return base.msg;
  const orig = [...doc.sections];
  const flags = new Map(secs.map(x => [x, [x.breakBefore, x.breakCol]]));
  const zp = secs[zi];
  const moved = doc.sections.filter(x => x !== zp);
  moved.splice(moved.indexOf(secs[ci]) + 1, 0, zp);
  doc.sections = moved;
  const alt = planCuts(doc, S, sizeKey);
  if (alt && alt.fill >= base.fill + ZP_MOVE_GAIN) {
    return `${zp.name} moved up beside ${secs[ci].name} (a peer of the cocktails; column fill ${Math.round(base.fill * 100)}% -> ${Math.round(alt.fill * 100)}% of the fullest); ${alt.msg}`;
  }
  doc.sections = orig;
  for (const [x, [bb, bc]] of flags) { delete x.breakBefore; delete x.breakCol; if (bb) x.breakBefore = bb; if (bc) x.breakCol = bc; }
  return base.msg;
}

// Colophon footer: a pinned, item-less section on the bottom margin. Only known facts: city/state and website from
// the venue record, and legal lines exactly as supplied. It gives the page a finished foot and lets the layout meet
// the scorecard's equal-margin rule inside Menu Studio (which counts trailing gaps toward the page height).
function addFooter(doc, req) {
  // Nothing the masthead already says (panel round 3: "Fort Collins, CO" under "Taproom · Fort Collins" repeats it).
  const said = `${doc.title || ''} ${doc.subtitle || ''}`.toLowerCase();
  const city = req.venue.city && said.includes(String(req.venue.city).toLowerCase()) ? '' : [req.venue.city, req.venue.state].filter(Boolean).join(', ');
  const place = [req.venue.area && said.includes(String(req.venue.area).toLowerCase()) ? null : req.venue.area, city].filter(Boolean).join('  ·  ');
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
  f.format = { section: { f: S.sub.f, s: Math.max(11, S.sub.s), w: S.sub.w, i: false, sp: 20, c: S.sub.c, cs: 'none' } };   // keeps "RiNo" as spelled; lowercase takes no tracking
  // One axis (panel round 2): a centred masthead gets a centred sign-off. Pinned headings draw left-aligned at pos.x, so
  // the x is solved from the measured line width. A footer with legal copy stays flush left (long lines read better).
  const centred = S.title.al === 'center' && !f.desc;
  const vis = f.desc ? S.section.s + 11 + S.desc.s * 1.16 : f.format.section.s * 1.16;
  const top = H - M - vis;
  const pages = layout({ doc, style: S, size: sizeKey }).pages;
  const x = centred ? Math.max(M, (W - textW(f.name, f.format.section)) / 2) : M;
  f.pos = { page: Math.max(0, pages - 1), x: +(x / W).toFixed(5), y: +(top / H).toFixed(5) };
  return top;
}

function scaleStyle(base, k) {
  const T = JSON.parse(JSON.stringify(base));
  for (const l of ['title', 'subtitle', 'section', 'sub', 'name', 'brand', 'desc', 'price']) T[l].s = Math.round(base[l].s * (l === 'title' ? Math.min(k, 1.35) : k));
  T.page.itemGap = Math.round(base.page.itemGap * k); T.page.secGap = Math.round(base.page.secGap * k);
  // Round 3 rhythm: space above a section head (item gap + section gap) stays within SEC_SPACE_MAX.
  if (T.page.itemGap + T.page.secGap > SEC_SPACE_MAX) T.page.secGap = Math.max(base.page.secGap, SEC_SPACE_MAX - T.page.itemGap);
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
    // The accent on a featured name must meet 4.5:1 like every other text colour (panel round 3: the house beer printed
    // in the look's lighter #b7791f, 3.2:1, beside section heads already raised to #8e5e18). One accent, one value.
    const accent0 = (req.brand.colours && req.brand.colours[0]) || r.look.accent;
    const accent = contrast(accent0, style.page.bg) >= 4.5 ? accent0
      : (r.look.roles.includes('section') && contrast(style.section.c, style.page.bg) >= 4.5 ? style.section.c : pushContrast(accent0, style.page.bg, 4.5));
    const venueKey = normVenue(req.venue.type);
    const built = fromDraft
      ? buildDocFromBase(req, r.look, { accent, order: [...(ORDER[venueKey] || ORDER.default), ...FOOD] })
      : buildDoc(req, r.look, { accent });
    const { doc, changes, title_missing } = built;
    if (options.standards) for (const c of applyStandards(doc, options.standards)) changes.push(c);
    if (built.questions) for (const q of built.questions) questions.push(q);
    if (built.flags) for (const f of built.flags) risk.add(f);
    for (const c of knownFacts(doc)) changes.push(c);
    // Mixed drinks take a garnish question (cocktails and crafted zero-proof); a bottled, canned or brewed soft drink
    // ("Made with cane sugar, in a glass bottle") does not (panel round 4: the four sodas were asked, the mocktails not).
    const PACKAGED = /\b(bottle|bottled|can|canned|mineral water|steeped|brewed|cola|soda water|ginger beer|tonic water|coffee)\b/i;
    const noGarnish = itemsOf(doc).filter(({ it, s }) => ['cocktails', 'mocktails', 'non_alcoholic'].includes(it.meta?.section || '') && it.desc && (['cocktails', 'mocktails'].includes(it.meta?.section) || (/,/.test(it.desc) && !/\bor\b/.test(it.desc) && !PACKAGED.test(it.desc) && !PACKAGED.test(it.name || ''))) && !(it.components || []).some(c => /garnish/i.test(c.role || '')));
    if (noGarnish.length) questions.push(`Garnish: which garnish goes on ${noGarnish.map(x => `"${x.it.name}"`).join(', ')}? (Printed garnishes are a scorecard requirement for cocktails.)`);
    if (!fromDraft) for (const { it, s, sub } of itemsOf(doc)) {
      if (s.designer_role) continue;
      for (const q of contentGaps(it, it.meta?.section || listForName(sub?.name || s.name), sub?.name || '')) { questions.push(q); risk.add(gapFlag(q)); }
    }
    if (!fromDraft && options.flatten !== false) {
      const fl = flattenSubs(doc);
      if (fl.length) {
        // The notes must describe what is printed (Content Reviewer round 3): drop the subsection-era notes.
        for (let i = changes.length - 1; i >= 0; i--) if (/own subsections|Renamed "By the glass"/.test(changes[i])) changes.splice(i, 1);
        changes.push(...fl);
      }
    }
    for (const c of pourHeaders(doc)) changes.push(c);
    for (const c of applyPourNotes(doc, req.pour_notes)) changes.push(c);
    addFooter(doc, req);
    const style0 = JSON.parse(JSON.stringify(style));
    let { m: m0, log } = fit(doc, style, sizeKey, req.format);
    for (let pass = 0; pass < 3; pass++) {
      const orphans = orphanSubs(doc, style, sizeKey);
      if (!orphans.length) break;
      for (const c of promoteSubs(doc, orphans)) changes.push(c);
      for (const key of Object.keys(style0)) style[key] = JSON.parse(JSON.stringify(style0[key]));
      ({ m: m0, log } = fit(doc, style, sizeKey, req.format));
    }
    const tagFix = tagsThatFit(doc, style, sizeKey);
    if (tagFix.length) {
      for (const c of tagFix) changes.push(c);
      for (const key of Object.keys(style0)) style[key] = JSON.parse(JSON.stringify(style0[key]));
      ({ m: m0, log } = fit(doc, style, sizeKey, req.format));
    }
    // Say what prints (panel round 3): Menu Studio sets prices inline beside the name in any multi-column layout
    // (S5), so the file must not claim leader dots or a right-aligned price column it cannot draw.
    if (style.page.cols > 1 && (style.page.dots || style.page.priceAlign !== 'inline')) {
      style.page.dots = false; style.page.priceAlign = 'inline';
      log.push('prices inline beside each name (Menu Studio sets multi-column prices inline), leader dots off');
    }
    let m = m0;
    if (m.pages > 1) {
      const pl = planPages(doc, style, sizeKey);
      if (pl) {
        log.push(pl);
        // With the page plan fixed, grow type and spacing while every section still lands in its planned slot.
        const base = JSON.parse(JSON.stringify(style)), pages = measure(doc, style, sizeKey).pages;
        const starts = () => layout({ doc, style, size: sizeKey }).ops.filter(o => o.t === 'head' && o.lvl === 'section' && !o.node?.pos).map(o => `${Math.floor(o.y / 1e9)}|${o.node?.id}`);
        // Descriptions do not wrap in Menu Studio (S6), so the longest one used to stop all growth at x1.03 and leave
        // page 1 a third empty (panel round 4). Once a line would run wide, the description size holds at the last size
        // that fit and names, prices, heads and spacing keep growing.
        let bestK = 1, descK = null;
        const grown = k => { const T = scaleStyle(base, k); if (descK !== null) T.desc.s = Math.round(base.desc.s * descK); return T; };
        for (let k = 1.03; k <= 1.45; k += 0.03) {
          let T = grown(k); for (const key of Object.keys(T)) style[key] = T[key];
          let r = measure(doc, style, sizeKey);
          if (r.wide.length && descK === null && r.pages === pages && !r.overflowing.length) {
            descK = bestK; T = grown(k); for (const key of Object.keys(T)) style[key] = T[key];
            r = measure(doc, style, sizeKey);
          }
          if (r.pages !== pages || r.wide.length || r.overflowing.length || orphanSubs(doc, style, sizeKey).length) break;
          bestK = k;
        }
        const T = grown(bestK); for (const key of Object.keys(T)) style[key] = T[key];
        if (bestK > 1) log.push(`type and spacing x${bestK.toFixed(2)} to fill the planned pages${descK !== null && descK < bestK ? ` (descriptions held at x${descK.toFixed(2)} so the longest line stays in its column)` : ''}`);
        for (const c of demoteSubs(doc, style, sizeKey)) changes.push(c);
        m = measure(doc, style, sizeKey); placeFooter(doc, style, sizeKey);
      }
    }
    const optRisk = [];
    if (req.format.pages && m.pages > req.format.pages) optRisk.push('too_many_items_for_format');
    if (m.overflowing.length) optRisk.push('section_taller_than_page');
    if (m.wide.length) optRisk.push('lines_may_exceed_column');
    // Page breaks for multi-page menus: start each overflow page at a whole section (Menu Studio "Start on a new page").
    return {
      option: String.fromCharCode(65 + idx), look: r.look.k, look_label: r.look.label, look_note: lookNote(r.look.note, style),
      why: r.why.map(w => style.page.dots ? w : w.replace(/reads best with leader dots/, 'needs a dense, scannable list')), score: r.score,
      menu_studio_file: { app: MDC_FILE_APP, schema_version: MDC_FILE_VERSION, saved_at: new Date().toISOString(),
                          preset: r.look.base, size: sizeKey, style, doc },
      fit: m, fit_log: log, tuning, changes, risk_flags: optRisk, title_missing,
    };
  });
  for (const o of out) for (const f of o.risk_flags) risk.add(f);
  return { request: req, size: sizeKey, options: out, questions: [...new Set(questions)], risk_flags: [...risk] };
}

// The look's one-line note describes what prints: no leader dots unless the page draws them.
export function lookNote(note, style) {
  if (style.page.dots) return note;
  return String(note).replace(/,\s*leader dots(?: to prices)?(?=[.,])/i, ', prices beside each name');
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
