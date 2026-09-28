// Harmony voice transcript -> structured menu request.
// Deterministic and conservative: it only records what was said. Anything it cannot place
// becomes a question, never a guess. Names are kept as spoken (title-cased for print),
// prices only when a number was attached to an item.

import { LIST_PHRASES, LIST_BY_KEY, FLAG_WORDS, MENU_TYPES, FORMAT_WORDS, TONE_WORDS,
         COLOR_WORDS, VENUE_TYPES } from './lexicon.mjs';

// ---------- number words ----------
const UNITS = { zero:0, oh:0, one:1, two:2, three:3, four:4, five:5, six:6, seven:7, eight:8, nine:9,
  ten:10, eleven:11, twelve:12, thirteen:13, fourteen:14, fifteen:15, sixteen:16, seventeen:17,
  eighteen:18, nineteen:19 };
const TENS = { twenty:20, thirty:30, forty:40, fourty:40, fifty:50, sixty:60, seventy:70, eighty:80, ninety:90 };
const NUMWORD = new RegExp('\\b(' + [...Object.keys(UNITS), ...Object.keys(TENS), 'hundred', 'a', 'and', 'half', 'quarter', 'point']
  .join('|') + ')\\b', 'i');

// Turn "twelve fifty" -> "12.50", "fourteen" -> "14", "six point two" -> "6.2",
// "a hundred and twenty" -> "120", "nine and a half" -> "9.50". Operates on a token list.
export function wordsToDigits(text) {
  const toks = text.split(/(\s+|[,.;:!?()])/);
  const out = [];
  let i = 0;
  const isNumTok = t => t && (t.toLowerCase() in UNITS || t.toLowerCase() in TENS || t.toLowerCase() === 'hundred');
  const readInt = (start) => {
    // reads up to "N hundred (and) TENS UNITS" -> {value, end}
    let j = start, val = 0, got = false, cur = 0;
    const skipWs = k => { while (k < toks.length && /^\s*$/.test(toks[k])) k++; return k; };
    j = skipWs(j);
    let w = (toks[j] || '').toLowerCase();
    if ((w === 'a' || w === 'one') && (toks[skipWs(j + 1)] || '').toLowerCase() === 'hundred') { cur = 1; got = true; j = skipWs(j + 1); w = 'hundred'; }
    let unitOnly = false;
    if (w in UNITS && w !== 'oh') { cur = UNITS[w]; got = true; unitOnly = true; j = skipWs(j + 1); w = (toks[j] || '').toLowerCase(); }
    if (w === 'hundred' && got) {
      unitOnly = false;
      val = cur * 100; cur = 0; j = skipWs(j + 1); w = (toks[j] || '').toLowerCase();
      if (w === 'and') { const k = skipWs(j + 1); const n = (toks[k] || '').toLowerCase(); if (n in UNITS || n in TENS) { j = k; w = n; } }
    }
    if (w in TENS && !unitOnly) {
      cur += TENS[w]; got = true; j = skipWs(j + 1); w = (toks[j] || '').toLowerCase();
      if (w in UNITS && UNITS[w] > 0 && UNITS[w] < 10) { cur += UNITS[w]; j = skipWs(j + 1); }
    } else if (!val && !got) return null;
    return { value: val + cur, end: j };
  };
  while (i < toks.length) {
    const t = toks[i];
    const lower = (t || '').toLowerCase();
    const aHundred = (lower === 'a') && /^hundred$/i.test(toks.slice(i + 1).find(x => !/^\s*$/.test(x)) || '');
    if (isNumTok(t) && lower !== 'oh' || aHundred) {
      const r = readInt(i);
      if (r) {
        let s = String(r.value), j = r.end;
        const peek = k => { while (k < toks.length && /^\s*$/.test(toks[k])) k++; return [k, (toks[k] || '').toLowerCase()]; };
        let [k, w] = peek(j);
        if (w === 'point') {                         // six point two
          const [k2, w2] = peek(k + 1);
          if (w2 in UNITS) { s += '.' + UNITS[w2]; j = k2 + 1; [k, w] = peek(j); }
        } else if (w === 'and') {                    // nine and a half
          const [k2, w2] = peek(k + 1); const [k3, w3] = peek(k2 + 1);
          if (w2 === 'a' && (w3 === 'half' || w3 === 'quarter')) { s = (r.value + (w3 === 'half' ? 0.5 : 0.25)).toFixed(2); j = k3 + 1; }
        } else if (r.value < 100 && (w in TENS || (w in UNITS && UNITS[w] >= 10) || w === 'oh')) {
          // "twelve fifty" / "eleven seventy five" / "nine oh five" -> cents
          const r2 = w === 'oh' ? (() => { const [k2, w2] = peek(k + 1); return w2 in UNITS ? { value: UNITS[w2], end: k2 + 1 } : null; })()
                                : readInt(k);
          if (r2 && r2.value < 100) { s = r.value + '.' + String(r2.value).padStart(2, '0'); j = r2.end; }
        }
        out.push(s);
        // keep the whitespace that followed the number
        if (j > 0 && /^\s+$/.test(toks[j - 1] || '')) out.push(' ');
        i = j;
        continue;
      }
    }
    out.push(t);
    i++;
  }
  return out.join('').replace(/\s{2,}/g, ' ');
}

// ---------- helpers ----------
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const hasPhrase = (text, w) => new RegExp('(^|[^a-z])' + esc(w) + '($|[^a-z])', 'i').test(text);
const SMALL = new Set(['a', 'an', 'and', 'the', 'of', 'on', 'in', 'with', 'de', 'del', 'la', 'le', 'y', 'or', 'to', 'at', 'for']);
export const titleCase = s => s.trim().split(/\s+/).map((w, i) => {
  if (/[A-Z]/.test(w.slice(1)) || /^[A-Z0-9&]+$/.test(w)) return w;          // keep IPA, McXxx, 1792
  if (i > 0 && SMALL.has(w.toLowerCase())) return w.toLowerCase();
  return w.charAt(0).toUpperCase() + w.slice(1);
}).join(' ');

const FILLER = /\b(um+|uh+|like|you know|okay so|ok so|so yeah|alright|all right|basically|let'?s see|and then|then we have|then we've got|next up|next)\b/gi;
const PRICE_NUM = '\\$?\\s?(\\d{1,4}(?:\\.\\d{1,2})?)';

// Section intro patterns: "for cocktails we have", "on the beer list", "wines by the glass:", "our reds are"
function findHeading(seg) {
  const s = seg.toLowerCase().trim();
  for (const { w, key } of LIST_PHRASES) {
    const W = esc(w) + '(?:\\s+(?:on tap|on draft|on draught|by the glass|by the bottle|in cans|in bottles))?';
    const intro = new RegExp(
      `^(?:(?:and\\s+)?(?:for|under|on|in)\\s+(?:the\\s+|our\\s+)?${W}(?:\\s+(?:list|section|menu|side))?` +
      `|(?:the\\s+|our\\s+)?${W}(?:\\s+(?:list|section|menu))?\\s*(?::|-|we(?:'ve| have)? got|we have|we're doing|we are doing|are|is|include|includes|will be|would be)` +
      `|(?:add|start|make|do|let'?s do|put)\\s+(?:a\\s+|an\\s+|the\\s+)?${W}(?:\\s+(?:list|section|page))?)` +
      `(?:\\s*(?:we(?:'ve| have)? got|we have|we're doing|we are doing|there'?s|there is|there are|include|:|-|,))?\\s*`, 'i');
    const m = s.match(intro) || s.match(new RegExp(`^(?:the\\s+|our\\s+)?${W}\\s*,\\s*`, 'i'));
    if (m) {
      const r = withSub(key, seg.trim().slice(m[0].length));
      const q = m[0].toLowerCase();
      if (!r.sub && /by the glass/.test(q)) r.sub = 'By the glass';
      if (!r.sub && /by the bottle/.test(q)) r.sub = 'By the bottle';
      if (!r.sub && /on (tap|draft|draught)/.test(q)) r.sub = 'Draft';
      if (!r.sub && /in cans/.test(q)) r.sub = 'Cans';
      if (!r.sub && /in bottles/.test(q)) r.sub = 'Bottles';
      if (!r.sub && /^(on draft|draft|draught|on tap|taps)$/.test(w)) r.sub = 'Draft';
      if (!r.sub && /^cans$/.test(w)) r.sub = 'Cans';
      return r;
    }
    if (new RegExp(`^${W}\\s*$`, 'i').test(s)) return { key, rest: '', sub: null };
  }
  return null;
}

// Serve formats inside a list become Menu Studio subsections: Beer > Draft, Wine > By the glass.
const SUBS = [
  [/^(?:on draft|on draught|on tap|draft|draught)\b/i, 'Draft'],
  [/^(?:in (?:the )?cans|cans|canned)\b/i, 'Cans'],
  [/^(?:in (?:the )?bottles|bottles|bottled)\b/i, 'Bottles'],
  [/^(?:by the glass)\b/i, 'By the glass'],
  [/^(?:by the bottle)\b/i, 'By the bottle'],
  [/^(?:classics?)\b/i, 'Classics'],
  [/^(?:frozen)\b/i, 'Frozen'],
  [/^(?:local)\b/i, 'Local'],
  [/^(?:blancos?|silver|plata)\b/i, 'Blanco'], [/^(?:reposados?)\b/i, 'Reposado'], [/^(?:extra a(?:ñ|n)ejos?)\b/i, 'Extra Añejo'],
  [/^(?:a(?:ñ|n)ejos?)\b/i, 'Añejo'], [/^(?:bourbons?)\b/i, 'Bourbon'], [/^(?:ryes?)\b/i, 'Rye'], [/^(?:scotch(?:es)?)\b/i, 'Scotch'],
  [/^(?:japanese)\b/i, 'Japanese'], [/^(?:spritz(?:es)?)\b/i, 'Spritzes'], [/^(?:martinis?)\b/i, 'Martinis'], [/^(?:margaritas?)\b/i, 'Margaritas'],
];
function withSub(key, rest) {
  let sub = null;
  for (const [re, name] of SUBS) {
    const m = rest.match(new RegExp(re.source + '\\s*(?:,|:|-)?\\s*(?:we(?:\'ve| have)? got|we have|there\'?s|there are|is|are)?\\s*', 'i'));
    if (m && m.index === 0) { sub = name; rest = rest.slice(m[0].length); break; }
  }
  return { key, rest, sub };
}
// Sub-only intros inside an open list: "and on draft we have ...", "by the bottle, ..."
function findSub(seg) {
  const r = withSub(null, seg.trim().replace(/^(?:and\s+)?(?:then\s+)?/i, ''));
  return r.sub ? r : null;
}

// "that's our house special", "it's new", "which is seasonal": a follow-on about the previous item.
const FOLLOW_ON = /^(?:and\s+)?(?:that'?s|that is|it'?s|it is|this is|which is|this one'?s|this one is|mark (?:it|that|this)|make (?:it|that|this)|put a|add a)\b/i;

// "this is for Casa Luna", "menu for Casa Luna", "the bar is called Casa Luna"
function findVenueName(text) {
  const m = text.match(/\b(?:(?:[Tt]his|[Ii]t)\s+is\s+for|(?:[Tt]his\s+)?[Mm]enu\s+for|(?:bar|restaurant|place|venue|spot)\s+(?:is\s+)?called|[Ww]e(?:'re| are)\s+called|[Vv]enue\s+(?:name\s+)?is)\s+((?:(?:[A-Z0-9][\w'&.-]*|of|the|and|de|la|&)\s?){1,6})/);
  return m ? m[1].trim().replace(/[,.]$/, '') : null;
}

function detectFlags(text) {
  const flags = new Set();
  for (const [flag, words] of Object.entries(FLAG_WORDS)) {
    for (const w of words) {
      // "house" alone only counts in "our house X"/"house special", not "house cabernet" (that's a name)
      if (w === 'house') continue;
      if (w === 'new' && !/\b(it'?s|this is|that'?s|is|mark(?:ed)?|brand)\s+new\b|\bnew\s*(this|item|one|addition)\b|\bnew\s*[,.]?\s*$/i.test(text)) continue;
      if (w === 'signature' && /^signature\b/i.test(text.trim())) continue;   // part of a name
      if (hasPhrase(text, w)) flags.add(flag);
    }
  }
  return [...flags];
}

const FLAG_STRIP = new RegExp('(?:,?\\s*(?:and\\s+)?(?:it\'?s|that\'?s|this is|mark(?:ed)?\\s+(?:it|this)(?:\\s+as)?|make\\s+(?:it|this))?\\s*(?:a|an|our|the)?\\s*(?:' +
  Object.values(FLAG_WORDS).flat().filter(w => w !== 'house' && w !== 'new').map(esc).join('|') +
  '|brand new|new)\\b[^,.;]*)', 'gi');

// Parse one item phrase. Returns null if it doesn't look like an item.
export function parseItem(raw, listKey) {
  let seg = raw.trim().replace(/^(?:and|also|plus|then|the next one is|next is|we(?:'ve| have)? got|we have|there'?s)\s+/i, '').trim();
  if (!seg) return null;
  const item = { name: null, description: null, prices: [], abv: null, flags: detectFlags(seg), heard: raw.trim(), list: listKey || null };

  // ABV: "6.2 percent", "6.2% abv", "abv 6.2"
  const abv = seg.match(/(\d{1,2}(?:\.\d)?)\s*(?:%|percent|per cent)(?:\s*(?:abv|alcohol))?|\babv\s*(?:of\s*)?(\d{1,2}(?:\.\d)?)/i);
  if (abv) { item.abv = Number(abv[1] || abv[2]); seg = seg.replace(abv[0], ' ').trim(); }

  // Multi-price: "11 glass 40 bottle", "11 a glass and 40 for the bottle", "glass 11 bottle 40", "5 oz 9, 8 oz 14", "pint 7 pitcher 22"
  const LBL = '(glass|bottle|btl|carafe|half bottle|pint|pitcher|can|draft|pour|shot|neat|rocks|double|single|flight|taster|5 ?oz|6 ?oz|8 ?oz|9 ?oz|1 ?oz|2 ?oz|1\\.5 ?oz|16 ?oz|12 ?oz|20 ?oz|small|large|half|full|well|call|premium)';
  const labelled = [];
  const reAfter = new RegExp(PRICE_NUM + '\\s*(?:dollars|bucks)?\\s*(?:a|an|per|for (?:the|a)|by the)?\\s*' + LBL + '\\b', 'gi');
  const reBefore = new RegExp('\\b' + LBL + '\\s*(?:is|at|for|,)?\\s*' + PRICE_NUM + '(?:\\s*(?:dollars|bucks))?', 'gi');
  let m;
  const taken = [];
  while ((m = reAfter.exec(seg))) { labelled.push({ label: m[2], value: Number(m[1]), at: m.index }); taken.push([m.index, m.index + m[0].length]); }
  if (labelled.length < 2) {
    // "glass 11 bottle 40" style; keep whichever reading found more labelled prices.
    const lb = [], tb = [];
    while ((m = reBefore.exec(seg))) { lb.push({ label: m[1], value: Number(m[2]), at: m.index }); tb.push([m.index, m.index + m[0].length]); }
    if (lb.length > labelled.length) { labelled.splice(0, labelled.length, ...lb); taken.splice(0, taken.length, ...tb); }
  }
  // A single "11 a glass" is still a labelled price; a lone "pint" with no number is ignored.
  if (labelled.length) {
    labelled.sort((a, b) => a.at - b.at);
    item.prices = labelled.map(p => ({ label: p.label.replace(/\s+/g, ' ').replace(/^(\d(?:\.\d)?) ?oz$/i, '$1 oz').replace(/^btl$/i, 'bottle')
      .replace(/^./, c => c.toUpperCase()), value: p.value }));
    for (const [a, b] of taken.sort((x, y) => y[0] - x[0])) seg = (seg.slice(0, a) + ' ' + seg.slice(b)).trim();
  } else {
    // Unlabelled price. Prefer explicit money: "$12", "12 dollars", "12 bucks", "for 12", "at 12", "is 12", trailing number.
    const money = seg.match(new RegExp('(?:\\$\\s?(\\d{1,4}(?:\\.\\d{1,2})?)|(\\d{1,4}(?:\\.\\d{1,2})?)\\s*(?:dollars|bucks)|(?:for|at|costs?|priced at|price is|it\'?s|goes for|sells for|runs)\\s+\\$?(\\d{1,4}(?:\\.\\d{1,2})?)(?!\\s*(?:oz|ounce|year|yr|%|percent))|,?\\s(\\d{1,3}(?:\\.\\d{1,2})?)\\s*[.,;]?\\s*$)', 'i'));
    if (money) {
      item.prices = [{ label: '', value: Number(money[1] || money[2] || money[3] || money[4]) }];
      seg = (seg.slice(0, money.index) + ' ' + seg.slice(money.index + money[0].length)).trim();
    }
  }

  // Strip flag phrases from the text now that they're recorded.
  seg = seg.replace(FLAG_STRIP, ' ').replace(/\s{2,}/g, ' ').trim();

  // Name vs description: "<name>, it's / made with / with / that's / which is <desc>"
  const split = seg.match(/^(.*?)(?:\s*[,-]\s*|\s+)(?:it'?s|it is|that'?s|that is|which is|made with|made from|with|has|comes with|featuring|served with|:)\s+(.+)$/i);
  let name = seg, desc = null;
  const comma = seg.indexOf(',');
  const commaFirst = comma > 0 && (!split || comma < split[1].length) && seg.slice(0, comma).trim().split(/\s+/).length <= 6;
  if (split && !commaFirst && split[1].trim().split(/\s+/).length <= 7 && split[1].trim().length > 1) { name = split[1]; desc = split[2]; }
  else if (seg.includes(',')) {
    const [a, ...b] = seg.split(',');
    if (a.trim().split(/\s+/).length <= 6 && b.join(',').trim()) { name = a; desc = b.join(',').trim(); }
  }
  name = name.replace(/^(?:a|an|the|our)\s+/i, '').replace(/[\s,;:.-]+$/g, '').replace(/^[\s,;:.-]+/, '').trim();
  if (desc) desc = desc.replace(/[\s,;:-]+$/g, '').replace(/^(?:a|an)\s+/i, '').trim();
  if (!name || name.split(/\s+/).length > 9 || !/[a-z]/i.test(name)) return null;
  item.name = titleCase(name);
  item.description = desc ? desc.charAt(0).toUpperCase() + desc.slice(1) : null;
  return item;
}

// Design-direction sentences are about the page, not items.
const DIRECTIVE = /\b(make it|make the menu|i want (it|the menu)|we want|use (our|the)|colou?rs?|fonts?|typeface|letter size|legal size|tabloid|half (page|sheet)|landscape|portrait|columns?|pages?|print|phone|mobile|qr|tv|screen|logo|look(s)?|feel|vibe|style|dollar signs?|background|design|layout|format|font|size)\b/i;

export function parseTranscript(transcript, ctx = {}) {
  const heard = String(transcript || '');
  const text = wordsToDigits(heard.replace(/[“”]/g, '"').replace(/[‘’]/g, "'")).replace(FILLER, ' ').replace(/\s{2,}/g, ' ');

  const design = { tone: [], colours: [], fonts: [], format: null, orientation: null, columns: null, pages: null,
                   no_dollar_signs: false, venue_type: null, menu_type: null, notes: [], hours: null };
  // ---- items ----
  // Split into clauses: sentences, semicolons, and commas that are followed by a new name-ish start after a price.
  const sentences = text.split(/(?<=[.!?;])\s+|\n+/).map(s => s.trim()).filter(Boolean);
  const sections = [];            // [{key, items: []}]
  const orphans = [];             // item phrases with no list
  const directives = [];
  let current = ctx.default_list || null, currentSub = null, lastItem = null;
  const sectionFor = key => { let s = sections.find(x => x.key === key); if (!s) { s = { key, label: LIST_BY_KEY[key]?.label || key, items: [] }; sections.push(s); } return s; };
  const venueName = findVenueName(text);

  // Edit commands about items already on the menu: "put the House Daiquiri first", "feature the Paloma",
  // "highlight the Old Fashioned", "mark the Gose as new". They change flags on an existing item, never add one.
  const edits = [];
  const EDIT = /^(?:please\s+)?(?:put|move|place|feature|highlight|push|mark|make|flag|star)\s+(?:the\s+|our\s+)?(.+?)(?:\s+(?:first|at the top|on top|up front|to the top|as (?:a |the |our )?(?:feature|featured|house special|special|new|seasonal)|new|seasonal))?(?:\s*,?\s*(?:it'?s|it is|that'?s|as)\s+(?:a |an |our |the )?(house special|special|signature|featured|new|seasonal))?$/i;
  for (let sent of sentences) {
    sent = sent.replace(/[.!?;]+$/, '').trim();
    if (!sent) continue;
    const em = sent.match(EDIT);
    if (em && !/\d/.test(sent) && em[1].split(/\s+/).length <= 6 && !DIRECTIVE.test(em[1])) {
      const fl = new Set(detectFlags(sent));
      if (/\b(first|top|up front|feature|highlight|push|star)\b/i.test(sent)) fl.add('featured');
      edits.push({ name: titleCase(em[1].replace(/\s+(first|at the top|on top|up front)$/i, '')), flags: [...fl], heard: sent });
      continue;
    }
    if (venueName && sent.includes(venueName) && !/\d/.test(sent)) { directives.push(sent); continue; }
    // Headings can appear mid-sentence: "... and on the beer side, Modelo 7" -> split on heading phrases after a comma.
    const parts = sent.split(/,\s*(?=(?:and\s+)?(?:for|on|under|by the)\s+(?:the\s+|our\s+)?[a-z])/i);
    for (let part of parts) {
      const h = findHeading(part);
      if (h) { current = h.key; currentSub = h.sub; lastItem = null; sectionFor(current); part = h.rest; if (!part) continue; }
      else if (current) { const sb = findSub(part); if (sb) { currentSub = sb.sub; part = sb.rest; if (!part) continue; } }
      if (DIRECTIVE.test(part) && !/\d/.test(part.replace(/\b\d\s*col(?:umn)?s?\b|\b\d\s*pages?\b/gi, ''))) { directives.push(part); continue; }
      // Items within a clause: split after each price.
      const chunksHere = splitItems(part);
      for (let chunkIdx = 0; chunkIdx < chunksHere.length; chunkIdx++) {
        const ch = chunksHere[chunkIdx];
        if (lastItem && FOLLOW_ON.test(ch.trim()) && !/\d/.test(ch)) {
          // Belongs to the previous item: flags, or a description if it has none.
          const f = detectFlags(ch);
          if (f.length) lastItem.flags = [...new Set([...lastItem.flags, ...f])];
          else if (!lastItem.description) lastItem.description = ch.replace(FOLLOW_ON, '').trim().replace(/^./, c => c.toUpperCase());
          lastItem.heard += ' | ' + ch.trim();
          continue;
        }
        let chunk = ch;
        if (current) { const sb = findSub(chunk.replace(/^(?:and|also|plus)\s+/i, '')); if (sb) { currentSub = sb.sub; chunk = sb.rest; if (!chunk) continue; } }
        const it = parseItem(chunk, current);
        if (!it) continue;
        if (!it.prices.length && !it.description && !current && !it.flags.length) { directives.push(ch); continue; }
        let itemList = current;
        if (!h && chunkIdx === 0) {
          const hit = LIST_PHRASES.find(p => p.key !== current && new RegExp(`(^|\\s)${esc(p.w)}$`, 'i').test(it.name));
          if (hit) { itemList = hit.key; it.list = hit.key; }
        }
        if (currentSub && itemList === current) it.sub = currentSub;
        // "Wines by the glass: prosecco ten" -> the speaker already said it's a glass price.
        if (it.prices.length === 1 && !it.prices[0].label && /^By the (glass|bottle)$/.test(currentSub || '')) it.prices[0].label = currentSub.slice(7).replace(/^./, c => c.toUpperCase());
        if (itemList) sectionFor(itemList).items.push(it); else orphans.push(it);
        lastItem = it;
      }
    }
  }
  design.notes = directives;
  design.venue_name = venueName;
  // Neighbourhood as spoken: "a cantina in RiNo" -> area "RiNo" (a fact for the footer, never invented).
  const area = text.match(/\b(?:bar|cantina|taproom|brewery|lounge|restaurant|pub|spot|place)\s+in\s+([A-Z][\w'-]*(?:\s+[A-Z][\w'-]*){0,2})/);
  design.area = area ? area[1].trim().replace(/[,.]$/, '') : null;
  // ---- page-level directives: read only from sentences that are about the page, never from item names ----
  // ("Double Black Diamond" is a beer, not a colour request; "Nightfall" is not a mood.)
  const lower = directives.join(' . ').toLowerCase();
  const whole = text.toLowerCase();
  for (const [tone, words] of Object.entries(TONE_WORDS)) if (words.some(w => hasPhrase(lower, w))) design.tone.push(tone);
  for (const [c, hex] of Object.entries(COLOR_WORDS)) if (hasPhrase(lower, c) && !new RegExp(`\\b${c}\\s+(wine|wines|label|ale|lager|ipa|sangria|stag|horse|hat)\\b`, 'i').test(lower)
      && !(c === 'white' && /\bwhite\s+(wine|claw|russian|negroni|lady)/i.test(lower)) && !(c === 'red' && /\bred\s+(wine|bull|stripe|eye|snapper)/i.test(lower))
      && !(c === 'rose' || c === 'wine')) design.colours.push({ name: c, hex });
  for (const [fmt, words] of Object.entries(FORMAT_WORDS)) if (words.some(w => hasPhrase(lower, w) && (fmt !== 'letter' || /\bletter\b/.test(lower)))) { design.format = design.format || fmt; }
  if (/\blandscape|horizontal|sideways\b/.test(lower)) design.orientation = 'landscape';
  if (/\bportrait|vertical\b/.test(lower)) design.orientation = 'portrait';
  const cols = lower.match(/\b(\d)\s*(?:-\s*)?col(?:umn)?s?\b|\b(single|one|two|three)\s*col(?:umn)?s?\b/);
  if (cols) design.columns = Number(cols[1]) || { single: 1, one: 1, two: 2, three: 3 }[cols[2]];
  const pages = lower.match(/\b(\d)\s*(?:-\s*)?pages?\b|\b(one|single|two|double)[\s-]?(?:page|sided)\b|\bfront and back\b/);
  if (pages) design.pages = Number(pages[1]) || ({ one: 1, single: 1, two: 2, double: 2 }[pages[2]] || 2);
  if (/\bno (dollar signs?|\$)|without (the )?dollar signs?|drop the dollar/.test(lower)) design.no_dollar_signs = true;
  for (const [vt, words] of Object.entries(VENUE_TYPES)) if (words.some(w => hasPhrase(whole, w))) { design.venue_type = vt; break; }
  for (const mt of MENU_TYPES) if (mt.words.some(w => hasPhrase(whole, w))) { design.menu_type = mt.key; break; }
  const fontAsk = lower.match(/\b(serif|sans[- ]serif|script|handwritten|typewriter|bold|condensed|georgia|times|palatino|helvetica|avenir|trebuchet|century gothic|futura|courier)\b(?:\s+fonts?)?/g);
  if (fontAsk) design.fonts = [...new Set(fontAsk.map(f => f.replace(/\s+fonts?$/, '')))];

  // Happy hour / service times, kept verbatim: "4 to 6", "from 4 to 7 pm", "Monday through Friday 3-6".
  const hrs = text.match(/\b((?:(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\s*(?:-|to|through|thru)\s*(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*,?\s*)?(?:from\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:-|to|till|until)\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?)(?!\s*(?:dollars|bucks|percent|%))/i);
  if (hrs && /happy hour|hours|from|until|till|pm|am|daily|monday|friday/i.test(text)) design.hours = hrs[1].replace(/^from\s+/i, '').trim();


  // ---- questions: never invent, ask ----
  const questions = [];
  for (const s of sections) {
    if (!s.items.length) questions.push(`You mentioned ${s.label} but no items were heard for it. What goes in that list?`);
    for (const it of s.items) {
      if (!it.prices.length) questions.push(`What is the price for "${it.name}" (${s.label})?`);
      if (/^wine/.test(s.key) && it.prices.length === 1 && !it.prices[0].label) questions.push(`Is ${it.prices[0].value} for "${it.name}" the glass or the bottle price?`);
    }
  }
  if (orphans.length) questions.push(`Which list do these belong to: ${orphans.map(o => `"${o.name}"`).join(', ')}?`);
  if (!sections.length && !orphans.length) questions.push('No menu items were heard. What should be on the menu (item, price, and which list)?');

  return {
    transcript: heard,
    normalized: text,
    menu_type: design.menu_type,
    venue_type: design.venue_type,
    venue_name: design.venue_name,
    lists: sections.map(s => s.key),
    sections: sections.map(s => ({ key: s.key, label: s.label, items: s.items })),
    unplaced_items: orphans,
    edits,
    design,
    questions,
  };
}

// Split "Paloma 12, House Margarita 14 it's our house special, Ranch Water 11" into item chunks.
function splitItems(part) {
  const chunks = [];
  // Split after a price token when followed by a comma/"and" and a new capital-ish word.
  const re = new RegExp('(' + PRICE_NUM + '(?:\\s*(?:dollars|bucks))?(?:\\s*(?:a|an|per|for the|by the)?\\s*(?:glass|bottle|pint|pitcher|can|pour|shot|oz))?' +
    '(?:[^,]*?(?:house special|featured|seasonal|signature|new|best seller|limited time)[^,]*?)?)\\s*(?:,|\\band\\b|\\bthen\\b)\\s+', 'gi');
  let last = 0, m;
  while ((m = re.exec(part))) {
    const end = m.index + m[1].length;
    const rest = part.slice(m.index + m[0].length);
    // Don't split a labelled price pair: "11 glass, 40 bottle"
    if (/^\$?\d/.test(rest) || /^(?:glass|bottle|pint|pitcher|can|pour|shot|\d+\s?oz)\b/i.test(rest)) continue;
    chunks.push(part.slice(last, end));
    last = m.index + m[0].length;
  }
  chunks.push(part.slice(last));
  // "the Paloma and the Old Fashioned 14": two items, the price belongs to the last one only.
  return chunks.flatMap(c => c.split(/\s*(?:,\s*and|,|\band)\s+(?=the\s+[A-Z])/)).map(c => c.trim()).filter(Boolean);
}

// CLI: node parse-voice.mjs "transcript..."   or   echo "..." | node parse-voice.mjs
if (import.meta.url === `file://${process.argv[1]}`) {
  const arg = process.argv.slice(2).join(' ');
  const run = t => console.log(JSON.stringify(parseTranscript(t), null, 2));
  if (arg) run(arg); else { let b = ''; process.stdin.on('data', d => b += d).on('end', () => run(b)); }
}
