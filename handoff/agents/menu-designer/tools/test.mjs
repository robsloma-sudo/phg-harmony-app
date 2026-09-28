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
t('description split', () => assert.equal(find(casa, 'Paloma').description, 'Tequila, grapefruit, lime and soda'));
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
t('pour labels printed once, values unchanged', () => { const sp = sbd.sections.find(x => x.name === 'Spirits'); const v = sp.subs.find(b => b.name === 'Vodka'); assert.match(v.desc, /1 oz.*1\.5 oz.*2\.5 oz/); const tito = v.items.find(i => i.name === "Tito's"); assert.deepEqual(tito.prices.map(p => p.value), [7, 10, 16]); assert.deepEqual(tito.meta.price_labels, ['1 oz', '1.5 oz', '2.5 oz']); });
t('wine: glass/bottle said once for the section', () => { const w = sbd.sections.find(x => x.name === 'Wine'); assert.match(w.desc, /Glass.*Bottle/); assert.deepEqual(w.subs.map(b => b.name), ['Sparkling', 'White', 'Rosé', 'Red']); });
t('mocktails follow cocktails; soft drinks last', () => { const n = sbd.sections.filter(x => !x.designer_role).map(x => x.name); assert.equal(n[1], 'Mocktails'); assert.equal(n[n.length - 1], 'Zero Proof'); });

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
t('folded serve formats become facts on the line', () => { const d = res.options[0].menu_studio_file.doc; const all = d.sections.flatMap(x => x.items); assert.equal(all.find(i => i.name === 'Tecate').desc, 'Can'); assert.equal(all.find(i => i.name === 'Siete Leguas').desc, 'Blanco tequila'); assert.match(all.find(i => i.name === 'Lagunitas IPA').desc, /^Draft · 6.2% ABV$/); });
t('missing prices -> needs input flag', () => assert.ok(design(missing).risk_flags.includes('missing_prices')));

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
