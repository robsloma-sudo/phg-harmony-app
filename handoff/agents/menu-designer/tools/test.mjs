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

const hh = parseTranscript('Happy hour menu for The Rusty Nail, Monday through Friday 4 to 6 pm. Beers: Coors Light three, PBR three. Well drinks five. House wine six a glass.');
t('happy hour type', () => assert.equal(hh.menu_type, 'Happy hour page'));
t('happy hour times kept verbatim', () => assert.match(hh.design.hours || '', /Monday through Friday 4 to 6 pm/i));

const missing = parseTranscript('For cocktails, the Paloma and the Old Fashioned fourteen.');
t('missing price asks, never invents', () => { assert.equal(find(missing, 'Paloma').prices.length, 0); assert.ok(missing.questions.some(q => /Paloma/.test(q))); });

// designer invariants
const res = design(casa, { venue: { city: 'Denver', state: 'CO' } });
const docItems = o => o.menu_studio_file.doc.sections.flatMap(s => [...s.items, ...s.subs.flatMap(x => x.items)]);
t('every heard item is on the menu, once', () => { for (const o of res.options) assert.equal(docItems(o).length, items(casa).length); });
t('prices unchanged and manual-sourced', () => { for (const o of res.options) for (const it of docItems(o)) for (const p of it.prices) { assert.equal(p.source, 'manual'); } });
t('never uses reserved purple', () => { for (const o of res.options) assert.ok(!JSON.stringify(o.menu_studio_file.style).includes('#6b4fa8')); });
t('Menu Studio file header', () => { const f = res.options[0].menu_studio_file; assert.equal(f.app, 'nbcc-menu-designer'); assert.equal(f.schema_version, 2); assert.ok(f.size && f.style && f.doc.sections.length); });
t('font indices valid', () => { for (const o of res.options) for (const [k, v] of Object.entries(o.menu_studio_file.style)) if (k !== 'page') assert.ok(v.f >= 0 && v.f <= 7); });
t('fits one page', () => { for (const o of res.options) assert.equal(o.fit.pages, 1); });
t('missing prices -> needs input flag', () => assert.ok(design(missing).risk_flags.includes('missing_prices')));

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
