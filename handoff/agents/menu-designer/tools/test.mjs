// Regression tests for the voice parser and designer invariants. Run: node test.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { parseTranscript, wordsToDigits } from './parse-voice.mjs';
import { design } from './design.mjs';

let pass = 0, fail = 0;
const t = (name, fn) => { try { fn(); pass++; } catch (e) { fail++; console.error(`✗ ${name}\n  ${e.message}`); } };
const items = r => r.sections.flatMap(s => s.items.map(i => ({ ...i, list: s.key })));
const find = (r, n) => items(r).find(i => i.name === n);

// numbers as spoken
for (const [a, b] of [['twelve fifty', '12.50'], ['fourteen', '14'], ['eleven seventy five', '11.75'], ['a hundred and twenty', '120'],
  ['nine and a half', '9.50'], ['six point two', '6.2'], ['nine oh five', '9.05'], ['twenty two', '22'], ['forty', '40']])
  t(`number: ${a}`, () => assert.equal(wordsToDigits(a), b));

const casa = parseTranscript(fs.readFileSync(new URL('../examples/casa-luna.voice.txt', import.meta.url), 'utf8'));
t('venue name', () => assert.equal(casa.venue_name, 'Casa Luna'));
t('venue type', () => assert.equal(casa.venue_type, 'latin_cantina'));
t('description split', () => { const first = parseTranscript(fs.readFileSync(new URL('../examples/casa-luna.voice.txt', import.meta.url), 'utf8').split('\n')[0]); assert.equal(find(first, 'Paloma').description, 'Tequila, grapefruit, lime and soda'); });
t('spoken cents', () => assert.deepEqual(find(casa, 'Ranch Water').prices, [{ label: '', value: 11.5 }]));
t('follow-on flag attaches to previous item', () => assert.ok(find(casa, 'House Margarita').flags.includes('house_special')));
t('no phantom item from follow-on', () => assert.ok(!items(casa).some(i => /^That/i.test(i.name))));
t('new flag', () => assert.ok(find(casa, 'Mezcal Negroni').flags.includes('new')));
t('ABV captured, not in name', () => { const i = find(casa, 'Lagunitas IPA'); assert.equal(i.abv, 6.2); assert.equal(i.prices[0].value, 8); });
t('draft sub', () => assert.equal(find(casa, 'Modelo').sub, 'Draft'));
t('cans sub mid-sentence', () => { const i = find(casa, 'Tecate'); assert.ok(i, 'Tecate missing'); assert.equal(i.sub, 'Cans'); });
t('glass/bottle prices', () => assert.deepEqual(find(casa, 'House Cabernet').prices, [{ label: 'Glass', value: 11 }, { label: 'Bottle', value: 40 }]));
t('by-the-glass context labels a single price', () => assert.deepEqual(find(casa, 'Prosecco').prices, [{ label: 'Glass', value: 10 }]));
t('tequila expression subs', () => { assert.equal(find(casa, 'Siete Leguas').sub, 'Blanco'); assert.equal(find(casa, 'Cascahuín').sub, 'Reposado'); });
t('non-alcoholic list', () => assert.equal(find(casa, 'Nojito').list, 'non_alcoholic'));
t('design: dark + gold + letter + no $', () => { const d = casa.design; assert.ok(d.tone.includes('dark')); assert.ok(d.colours.some(c => c.name === 'gold')); assert.equal(d.format, 'letter'); assert.ok(d.no_dollar_signs); });

const ha = parseTranscript(fs.readFileSync(new URL('../examples/high-altitude.voice.txt', import.meta.url), 'utf8'));
t('item names never set colours ("Double Black Diamond")', () => assert.ok(!ha.design.colours.length));
t('item names never set mood ("Nightfall Stout")', () => assert.ok(!ha.design.tone.includes('dark')));
t('capitalised "This is for"', () => assert.equal(ha.venue_name, 'High Altitude Brewing'));
t('comma before "with" keeps name short', () => { const i = find(ha, 'Switchback IPA'); assert.ok(i); assert.match(i.description, /Simcoe and Mosaic/); });
t('casual tone', () => assert.ok(ha.design.tone.includes('casual')));
t('neighbourhood stops at the sentence end', () => assert.equal(casa.design.area, 'RiNo'));
const ed = parseTranscript('Put the House Daiquiri first, it\'s our house special. Feature the Margarita.');
t('edit commands are edits, not new items', () => { assert.equal(ed.edits.length, 2); assert.equal(items(ed).length, 0); assert.ok(ed.edits[0].flags.includes('house_special')); });

const hh = parseTranscript('Happy hour menu for The Rusty Nail, Monday through Friday 4 to 6 pm. Beers: Coors Light three, PBR three. Well drinks five. House wine six a glass.');
t('happy hour type', () => assert.equal(hh.menu_type, 'Happy hour page'));
t('happy hour times kept verbatim', () => assert.match(hh.design.hours || '', /Monday through Friday 4 to 6 pm/i));

const missing = parseTranscript('For cocktails, the Paloma and the Old Fashioned fourteen.');
t('missing price asks, never invents', () => { assert.equal(find(missing, 'Paloma').prices.length, 0); assert.ok(missing.questions.some(q => /Paloma/.test(q))); });

// pour sizes
import { parsePourScheme } from './parse-voice.mjs';
t('pour scheme: spirits ladder', () => assert.deepEqual(parsePourScheme('All spirits are poured in 1 ounce, 1.50 ounce and 2.50 ounce pours.'), ['1 oz', '1.5 oz', '2.5 oz']));
t('pour scheme: draft with pitcher', () => assert.deepEqual(parsePourScheme('Draft beers come in 10 ounce, 16 ounce and pitchers.'), ['10 oz', '16 oz', 'Pitcher']));
const sb = parseTranscript(fs.readFileSync(new URL('../examples/sample-bar.voice.txt', import.meta.url), 'utf8'));
t('sample bar: 45 items, 5 house + 5 classics', () => { assert.equal(items(sb).length, 45); const c = sb.sections.find(x => x.key === 'cocktails').items; assert.equal(c.filter(i => i.sub === 'House').length, 5); assert.equal(c.filter(i => i.sub === 'Classics').length, 5); });
t('sample bar: spirit ladders by list', () => { assert.deepEqual(find(sb, "Tito's").prices.map(p => p.label), ['1 oz', '1.5 oz', '2.5 oz']); assert.deepEqual(find(sb, "Blanton's Single Barrel").prices.map(p => p.label), ['1.5 oz', '3 oz']); });
t('sample bar: draft ladder, cans single price', () => { assert.deepEqual(find(sb, 'Summit Pils').prices.map(p => p.value), [5, 7, 22]); assert.equal(find(sb, 'Coors Light').prices.length, 1); });
t('"Margarita, blanco tequila…" is an item, not a Blanco label', () => assert.equal(find(sb, 'Margarita').sub, 'Classics'));
t('ginger beer is not beer; New Zealand is not a "new" flag', () => { assert.equal(find(sb, 'Fever-Tree Ginger Beer').list, 'non_alcoholic'); assert.match(find(sb, 'Whitehaven Sauvignon Blanc').description, /New Zealand/); });
t('mocktails are their own list', () => assert.equal(find(sb, 'Garden Spritz').list, 'mocktails'));
t('pour mismatch asks', () => { const r = parseTranscript('All spirits are poured in 1 ounce, 1.50 ounce and 2.50 ounce pours. Vodka: Titos seven, ten.'); assert.ok(r.questions.some(q => /Which price goes with which pour/.test(q))); });
const sbd = design(sb, { venue: { city: 'Denver', state: 'CO' } }).options[0].menu_studio_file.doc;
t('pour labels printed once, values unchanged', () => { const sp = sbd.sections.find(x => x.name === 'Spirits'); const v = sp.subs.find(b => b.name === 'Vodka'); assert.match(sp.desc, /1 oz.*1\.5 oz.*2\.5 oz/); assert.equal(v.desc, ''); const tito = v.items.find(i => i.name === "Tito's"); assert.deepEqual(tito.prices.map(p => p.value), [7, 10, 16]); assert.deepEqual(tito.meta.price_labels, ['1 oz', '1.5 oz', '2.5 oz']); });
t('wine: glass/bottle said once for the section', () => { const w = sbd.sections.find(x => x.name === 'Wine'); assert.match(w.desc, /Glass.*Bottle/); assert.deepEqual(w.subs.map(b => b.name), ['Sparkling', 'White', 'Rosé', 'Red']); });
t('zero-proof program in one section, beside the cocktails on a two-page menu (Crafted then softs)', () => { const n = sbd.sections.filter(x => !x.designer_role).map(x => x.name); assert.ok(!n.includes('Mocktails')); assert.equal(n[n.indexOf('Cocktails') + 1], 'Zero Proof'); const z = sbd.sections.find(x => x.name === 'Zero Proof'); assert.deepEqual(z.subs.map(b => b.name), ['Crafted', 'Soft Drinks & Coffee']); assert.ok(z.subs[0].items.some(i => i.name === 'Nojito')); });
t('spirits in back-bar order, whiskey last', () => { const sp = sbd.sections.find(x => x.name === 'Spirits'); const k = sp.subs.map(b => b.name.toLowerCase()); assert.ok(k.indexOf('vodka') < k.indexOf('tequila') && k.indexOf('whiskey') === k.length - 1, k.join(',')); });
t('no HOUSE badge under a House subhead', () => { const c = sbd.sections.find(x => x.name === 'Cocktails'); const lp = c.subs.find(b => /house/i.test(b.name)).items.find(i => i.name === 'Luna Paloma'); assert.ok(!lp.badges.includes('house')); });
import { LOOKS, styleForLook, TRACKING_MAX } from '../styles/looks.mjs';
t('looks: tracking within ceilings, prices under names', () => { for (const l of LOOKS) { const s = styleForLook(l); for (const [k, m] of Object.entries(TRACKING_MAX)) assert.ok(s[k].sp <= m, `${l.k}.${k}`); assert.ok(s.price.s < s.name.s || s.price.s <= s.desc.s + 1, l.k); } });

// designer invariants
const res = design(casa, { venue: { city: 'Denver', state: 'CO' } });
const docItems = o => o.menu_studio_file.doc.sections.flatMap(s => [...s.items, ...s.subs.flatMap(x => x.items)]);
t('every heard item is on the menu, once', () => { for (const o of res.options) assert.equal(docItems(o).length, items(casa).length); });
t('prices unchanged and manual-sourced', () => { for (const o of res.options) for (const it of docItems(o)) for (const p of it.prices) { assert.equal(p.source, 'manual'); } });
t('never uses reserved purple', () => { for (const o of res.options) assert.ok(!JSON.stringify(o.menu_studio_file.style).includes('#6b4fa8')); });
t('Menu Studio file header', () => { const f = res.options[0].menu_studio_file; assert.equal(f.app, 'nbcc-menu-designer'); assert.equal(f.schema_version, 2); assert.ok(f.size && f.style && f.doc.sections.length); });
t('font indices valid', () => { for (const o of res.options) for (const [k, v] of Object.entries(o.menu_studio_file.style)) if (k !== 'page') assert.ok(v.f >= 0 && v.f <= 7); });
t('fits one page', () => { for (const o of res.options) assert.equal(o.fit.pages, 1); });
t('footer pinned inside the margins', () => { for (const o of res.options) { const f = o.menu_studio_file.doc.sections.find(x => x.designer_role === 'footer'); if (f) { assert.ok(f.pos.x > 0.03 && f.pos.y > 0.8 && f.pos.y < 0.97, JSON.stringify(f.pos)); } } });
t('non-alcoholic is the last list', () => { for (const o of res.options) { const n = o.menu_studio_file.doc.sections.filter(x => !x.designer_role).map(x => x.name); assert.match(n[n.length - 1], /Zero Proof|Non-Alcoholic/); } });
t('small fresh menus are flat (equal space above every header)', () => { for (const o of res.options) assert.ok(o.menu_studio_file.doc.sections.every(x => !(x.subs || []).length)); });
t('folded serve formats become facts on the line', () => { const d = res.options[0].menu_studio_file.doc; const all = d.sections.flatMap(x => x.items); assert.equal(all.find(i => i.name === 'Tecate').desc, 'Can · Mexican lager · 4.5% ABV'); assert.equal(all.find(i => i.name === 'Siete Leguas').desc, 'Blanco · Los Altos, Jalisco · 40% ABV'); assert.match(all.find(i => i.name === 'Lagunitas IPA').desc, /^Draft · West Coast IPA, Petaluma, California · 16 oz pour · 6.2% ABV$/); });
t('missing prices -> needs input flag', () => assert.ok(design(missing).risk_flags.includes('missing_prices')));


// Panel round 2
import { answerFor } from './parse-voice.mjs';
import { contentGaps } from './draft.mjs';
t('answers fill description, garnish and ABV of a known item, never a price', () => {
  const secs = [{ key: 'cocktails', items: [{ name: 'Paloma', description: 'Tequila, grapefruit', prices: [{ value: 12 }], heard: '' }, { name: 'Modelo', description: null, prices: [{ value: 7 }], heard: '' }] }];
  assert.ok(answerFor('The Paloma is blanco tequila, grapefruit, lime and soda, garnished with a grapefruit wedge', secs));
  assert.equal(secs[0].items[0].description, 'Blanco tequila, grapefruit, lime and soda'); assert.equal(secs[0].items[0].garnish, 'grapefruit wedge');
  assert.ok(answerFor('Modelo is Modelo Especial, Mexican lager, 4.4 percent', secs)); assert.equal(secs[0].items[1].abv, 4.4);
  assert.equal(answerFor('Paloma, twelve', secs), false); assert.equal(answerFor('Paloma 12 dollars', secs), false);
});
t('garnish prints after a middle dot and counts as answered; HOUSE badge dropped beside "House …"', () => {
  const all = res.options[0].menu_studio_file.doc.sections.flatMap(x => [...x.items, ...(x.subs || []).flatMap(b => b.items)]);
  const hm = all.find(i => i.name === 'House Margarita');
  assert.match(hm.desc, /agave · salt rim$/); assert.ok(!hm.badges.includes('house'));
  assert.ok(!res.questions.some(q => /^Garnish:/.test(q)));
});
t('wine: a partial glass/bottle ladder is named on each line (no floating key), sparkling first, bare prices, no redundant colour tag', () => {
  const wine = res.options[0].menu_studio_file.doc.sections.find(x => /wine/i.test(x.name));
  const items = [...wine.items, ...(wine.subs || []).flatMap(b => b.items)];
  assert.ok(![wine.desc, ...(wine.subs || []).map(b => b.desc)].join(' ').trim(), 'no key line');
  assert.deepEqual(items.map(i => i.name), ['Prosecco', 'House Cabernet']);
  assert.match(items[0].desc, /^Glass · Glera/); assert.match(items[1].desc, /^Glass \/ bottle · /);
  assert.deepEqual(items[1].meta.price_labels, ['Glass', 'Bottle']); assert.deepEqual(items[1].prices.map(p => p.value), [11, 40]);
  assert.ok(items.every(i => i.prices.every(p => !p.label)));
  assert.ok(!/^Red\b/.test(items.find(i => i.name === 'House Cabernet').desc));
});
t('subtitle floor and tracking; centred footer under a centred masthead', () => {
  const o = res.options[0]; const st = o.menu_studio_file.style || o.menu_studio_file.doc.style;
  if (st) { assert.ok(st.subtitle.s >= 11); assert.ok(st.subtitle.sp <= 120); }
  const f = o.menu_studio_file.doc.sections.find(x => x.designer_role === 'footer');
  if (f && st && st.title.al === 'center' && !f.desc) assert.ok(f.pos.x > st.page.margin * 96 / (8.5 * 96) + 0.05);
});
t('printed ABV and a Blanco subsection answer the spirit questions ("\\b%\\b" never matched)', () => {
  assert.deepEqual(contentGaps({ name: 'Siete Leguas', desc: 'Los Altos, Jalisco · 40% ABV' }, 'tequila', 'Blanco'), []);
  assert.equal(contentGaps({ name: 'Siete Leguas', desc: '' }, 'tequila', 'Blanco').length, 1);
  assert.ok(!res.questions.some(q => /which expression/.test(q)));
  assert.ok(!items(casa).some(i => /^Answers/i.test(i.name)));
});

// Panel round 3 (high-altitude)
import { parseSinglePour } from './parse-voice.mjs';
import { orphanSubs, contrast, SEC_SPACE_MAX } from './design.mjs';
import { requestDesignPayload, taskToRequest } from './handoff.mjs';
const haText = fs.readFileSync(new URL('../examples/high-altitude.voice.txt', import.meta.url), 'utf8');
const haBody = requestDesignPayload(haText, { venue: { city: 'Fort Collins', state: 'CO', type: 'brewery' } });
const haRes = design(taskToRequest({ request: haBody.request, inputs: haBody.inputs }), { venue: { city: 'Fort Collins', state: 'CO' } });
const haAll = o => o.menu_studio_file.doc.sections.flatMap(x => [...x.items, ...(x.subs || []).flatMap(b => b.items)]);
t('names as spoken: capitalised number words stay words, "four pack" stays 4 Pack, Kölsch spelled', () => {
  assert.ok(find(ha, 'Laws Four Grain Bourbon')); assert.ok(find(ha, 'Summit Pils 4 Pack')); assert.ok(find(ha, 'Kölsch'));
});
t('one pour for a list: "Drafts are poured at 16 ounces" prints once under Draft; an item\'s own pour on its line', () => {
  assert.deepEqual(parseSinglePour('Drafts are poured at 16 ounces'), { subject: 'Drafts', pour: '16 oz' });
  assert.equal(parseSinglePour('Summit Pils 7'), null); assert.equal(parseSinglePour('Drafts are great'), null);
  const secs = haRes.options[0].menu_studio_file.doc.sections, beer = secs.find(x => x.name === 'Beer');
  // Draft is its own "On Draft" section when Cans had to leave the column (round 6), else Beer's Draft subsection.
  const draftDesc = beer ? beer.subs.find(b => b.name === 'Draft').desc : secs.find(x => x.name === 'On Draft').desc;
  assert.equal(draftDesc, '16 oz pours unless noted');
  assert.match(haAll(haRes.options[0]).find(i => i.name === 'Double Black Diamond').desc, /10 oz pour · 10\.5% ABV$/);
  assert.equal(haAll(haRes.options[0]).find(i => i.name === 'Double Black Diamond').prices[0].value, 9);
});
t('no subhead is left at a column foot without its first two items', () => {
  for (const o of haRes.options) assert.deepEqual(orphanSubs(o.menu_studio_file.doc, o.menu_studio_file.style, o.menu_studio_file.size), []);
  // Round 6: Draft and Cans are peer sections, never "Beer" beside "Beer · Cans".
  const names = haRes.options[0].menu_studio_file.doc.sections.map(x => x.name);
  assert.ok(!names.includes('Beer · Cans'), names.join(', '));
  assert.ok(names.includes('Beer') || (names.includes('On Draft') && names.includes('Cans to Go')), names.join(', '));
  assert.equal(haAll(haRes.options[0]).length, items(ha).length);
});
t('featured-name accent meets 4.5:1 (one accent value)', () => {
  for (const o of [...haRes.options, ...res.options]) for (const it of haAll(o)) if (it.format?.name?.c) assert.ok(contrast(it.format.name.c, o.menu_studio_file.style.page.bg) >= 4.5, `${o.look} ${it.name}`);
});
t('multi-column says what prints: no leader dots claimed, prices inline', () => {
  for (const o of haRes.options) { const P = o.menu_studio_file.style.page; if (P.cols > 1) { assert.equal(P.dots, false); assert.equal(P.priceAlign, 'inline'); assert.ok(!/leader dots/i.test(o.look_note + o.why.join(' ')), o.look); } }
});
t('space above a section head is capped (item gap + section gap)', () => {
  for (const o of haRes.options) { const P = o.menu_studio_file.style.page; assert.ok(P.itemGap + P.secGap <= SEC_SPACE_MAX + 0.5, `${o.look}: ${P.itemGap}+${P.secGap}`); }
});
t('footer never repeats the masthead ("Fort Collins, CO" under "Taproom · Fort Collins")', () => {
  for (const o of haRes.options) { const d = o.menu_studio_file.doc; const f = d.sections.find(x => x.designer_role === 'footer'); assert.ok(!f || !/fort collins/i.test(f.name), o.look); }
});
// panel round 4 (sample-bar)
import { placeCommas, styleDesc } from './parse-voice.mjs';
t('wine region takes a comma before its country or state; words unchanged', () => {
  assert.equal(placeCommas('Marlborough New Zealand'), 'Marlborough, New Zealand');
  assert.equal(placeCommas('Russian River Valley California'), 'Russian River Valley, California');
  assert.equal(placeCommas('California coast'), 'California coast');
  assert.equal(placeCommas('Glera, Prosecco DOC, Veneto, Italy'), 'Glera, Prosecco DOC, Veneto, Italy');
  assert.equal(styleDesc('Non alcoholic IPA'), 'Non-alcoholic IPA'); assert.equal(styleDesc('West coast IPA'), 'West Coast IPA');
  assert.equal(find(sb, 'Catena Malbec').description, 'Mendoza, Argentina');
});
t('a key shared by most subsections prints once under the section; the exception keeps its own', () => {
  const sp = sbd.sections.find(x => x.name === 'Spirits');
  assert.equal(sp.desc, '1 oz  ·  1.5 oz  ·  2.5 oz');
  const w = sp.subs.find(b => b.name === 'Whiskey'); assert.ok(w, 'Whiskey back under Spirits'); assert.equal(w.desc, '1.5 oz  ·  3 oz');
  assert.equal(sp.subs.filter(b => b.desc).length, 1);
});
t('two-page plan: zero proof moves up only when it fills the pages more evenly; no promoted sub left beside its parent', () => {
  const o = design(sb, { venue: { city: 'Denver', state: 'CO' } }).options[0];
  const d = o.menu_studio_file.doc, secs = d.sections.filter(x => !x.designer_role);
  assert.ok(secs.find(x => x.name === 'Zero Proof').breakCol, 'Zero Proof opens column 2 of page 1');
  assert.ok(!secs.some((x, i) => x.designer_promoted_from && secs[i - 1]?.id === x.designer_promoted_from && !x.breakCol && !x.breakBefore));
  assert.ok(/type and spacing x1\.(1|2|3)\d? to fill the planned pages \(descriptions held/.test(JSON.stringify(o)), 'type grew past the longest description');
  assert.deepEqual(orphanSubs(d, o.menu_studio_file.style, o.menu_studio_file.size), []);
  assert.equal(haAll(o).length, items(sb).length);
});
t('garnish question covers crafted zero-proof, never a bottled or brewed soft drink', () => {
  const q = design(sb, { venue: { city: 'Denver', state: 'CO' } }).questions.join(' ');
  for (const n of ['Mexican Coca-Cola', 'Topo Chico', 'Fever-Tree Ginger Beer', 'Cold Brew Coffee']) assert.ok(!q.includes(`"${n}"`), n);
  const bare = parseTranscript('Mocktails: Nojito, mint, lime, soda, seven.');
  assert.match(design(bare, {}).questions.join(' '), /Garnish: .*"Nojito"/);
});
// Panel round 5: tags lead the description line; the reasoning says only what was built; no forced leaders.
t('tags lead the description line (New · / Signature ·), no raised badge', () => {
  const all = res.options[0].menu_studio_file.doc.sections.flatMap(x => [...x.items, ...(x.subs || []).flatMap(b => b.items)]);
  const mn = all.find(i => i.name === 'Mezcal Negroni'), hm = all.find(i => i.name === 'House Margarita');
  assert.match(mn.desc, /^NEW · /); assert.deepEqual(mn.badges, []); assert.ok(mn.meta.designer_flags.includes('new'));
  assert.match(hm.desc, /^SIGNATURE · /); assert.deepEqual(hm.badges, []);
});
t('a tag that would push its line past the column stays a Menu Studio badge', () => {
  const o = design(sb, { venue: { city: 'Denver', state: 'CO' } }).options[0];
  const all = o.menu_studio_file.doc.sections.flatMap(x => [...x.items, ...(x.subs || []).flatMap(b => b.items)]);
  const gg = all.find(i => i.name === 'Garden Gimlet');
  assert.ok(!/^Seasonal · /i.test(gg.desc) && gg.badges.includes('seasonal'));
});
t('reasoning names only the wine subsections built; a wide single column gets no forced leaders', () => {
  const txt = JSON.stringify(res);
  assert.ok(!/White \/ Rosé|Sparkling \/ White/.test(txt));
  const P = res.options[0].menu_studio_file.style?.page || res.options[0].menu_studio_file.doc.style?.page;
  if (P && P.cols === 1) assert.equal(P.dots, false);
});
// Panel round 6: beer light to dark by style; peer format sections; caps tags with ink names; "Czech-style".
import { beerRank, peerName } from './design.mjs';
t('beer ranks light to dark by style (name first, imperial from the description)', () => {
  const r = (name, description = '') => beerRank({ name, description });
  assert.ok(r('Mexican Lager') < r('Juniper Pale Ale') && r('Juniper Pale Ale') < r('Switchback IPA') && r('Switchback IPA') < r('Hazy Peak'));
  assert.ok(r('Hazy Peak') < r('Raspberry Wheat') && r('Raspberry Wheat') < r('Mountain Saison') && r('Mountain Saison') < r('Sour Cherry Gose'));
  assert.ok(r('Sour Cherry Gose') < r('Alpenglow Amber') && r('Alpenglow Amber') < r('Nightfall Stout') && r('Nightfall Stout') < r('Double Black Diamond', 'Imperial stout'));
  assert.equal(r('Mystery Tap'), null);
});
t('High Altitude draft list runs light to dark; the house special keeps its slot, its tag in caps, its name in ink', () => {
  const o = haRes.options[0], secs = o.menu_studio_file.doc.sections;
  const draft = (secs.find(x => x.name === 'On Draft') || secs.find(x => x.name === 'Beer').subs.find(b => b.name === 'Draft')).items.map(i => i.name);
  assert.deepEqual([draft[0], draft.at(-2), draft.at(-1)], ['Mexican Lager', 'Nightfall Stout', 'Double Black Diamond']);
  const ns = haAll(o).find(i => i.name === 'Nightfall Stout');
  assert.match(ns.desc, /^HOUSE SPECIAL · /); assert.equal(ns.format?.name?.c, undefined);
  assert.match(haAll(o).find(i => i.name === 'Summit Pils').desc, /Czech-style pilsner/);
});
t('serve-format subsections name peer sections', () => {
  assert.equal(peerName('Draft'), 'On Draft'); assert.equal(peerName('Cans', [{ desc: 'Pils in pint cans to go' }]), 'Cans to Go');
  assert.equal(peerName('Cans', [{ desc: 'Mexican lager' }]), 'Cans'); assert.equal(peerName('Whiskey'), null);
});
import { parseLegalLine } from './parse-voice.mjs';
t('the venue\'s legal line is heard, printed as the pinned footer line; "less than 0.5 percent" keeps its bound', () => {
  assert.equal(parseLegalLine('Legal line: must be 21 to drink, please drink responsibly'), 'Must be 21 to drink, please drink responsibly');
  assert.equal(parseLegalLine('Summit Pils is a Czech-style pilsner'), null);
  assert.deepEqual(ha.design.legal_lines, ['Must be 21 to drink, please drink responsibly']);
  assert.equal(ha.design.format, 'letter');
  assert.equal(find(ha, 'Athletic Run Wild IPA').abv, '<0.5');
  const foot = haRes.options[0].menu_studio_file.doc.sections.find(x => x.designer_role === 'footer');
  assert.equal(foot.name, 'Must be 21 to drink, please drink responsibly'); assert.equal(foot.desc, '');
  assert.match(haAll(haRes.options[0]).find(i => i.name === 'Athletic Run Wild IPA').desc, /<0\.5% ABV$/);
});
console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
