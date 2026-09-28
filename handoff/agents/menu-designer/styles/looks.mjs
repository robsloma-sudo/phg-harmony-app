// House looks for the PHG Menu Designer.
// Every look is expressed ONLY in Menu Studio's own style model (index.html: MDC_FONTS, mdcStyleDefault,
// MDC_PRESETS), so whatever the designer previews is exactly what Menu Studio draws after the Coordinator
// applies it. `base` names the MDC preset the look starts from; `d` is merged over it level by level.
//
// MDC_FONTS index: 0 Georgia · 1 Times · 2 Palatino · 3 Helvetica · 4 Avenir · 5 Trebuchet · 6 Century Gothic · 7 Courier
// Sizes are Menu Studio canvas px at 96 dpi (13 px = 9.75 pt in print).
// Never use #6b4fa8 (purple): Menu Studio reserves it for prices seeded from observed medians.

export const MDC_FONTS = [
  { label: 'Georgia',        f: 'Georgia, serif' },
  { label: 'Times',          f: '"Times New Roman", Times, serif' },
  { label: 'Palatino',       f: 'Palatino, "Palatino Linotype", Georgia, serif' },
  { label: 'Helvetica',      f: 'Helvetica, Arial, sans-serif' },
  { label: 'Avenir',         f: '"Avenir Next", Avenir, "Segoe UI", sans-serif' },
  { label: 'Trebuchet',      f: '"Trebuchet MS", Tahoma, sans-serif' },
  { label: 'Century Gothic', f: '"Century Gothic", Futura, sans-serif' },
  { label: 'Courier',        f: '"Courier New", Courier, monospace' },
];

export function mdcStyleDefault() {
  return {
    page: { cols: 1, gutter: 18, bg: '#ffffff', ink: '#111111', rule: '#111111', margin: 0.6,
            itemGap: 5, secGap: 14, rules: true, dots: false, priceAlign: 'right' },
    title:    { f: 0, s: 26, w: 'normal', i: false, sp: 0,   c: '#111111', cs: 'none',  al: 'center' },
    subtitle: { f: 0, s: 11, w: 'normal', i: false, sp: 220, c: '#666666', cs: 'upper', al: 'center' },
    section:  { f: 0, s: 15, w: 'bold',   i: false, sp: 140, c: '#111111', cs: 'upper', al: 'left' },
    sub:      { f: 0, s: 11, w: 'normal', i: false, sp: 120, c: '#777777', cs: 'upper', al: 'left' },
    name:     { f: 3, s: 13, w: 'normal', i: false, sp: 0,   c: '#111111', cs: 'none',  al: 'left' },
    brand:    { f: 3, s: 13, w: 'normal', i: true,  sp: 0,   c: '#333333', cs: 'none',  al: 'left' },
    desc:     { f: 3, s: 11, w: 'normal', i: false, sp: 0,   c: '#555555', cs: 'none',  al: 'left' },
    price:    { f: 3, s: 13, w: 'normal', i: false, sp: 0,   c: '#111111', cs: 'none',  al: 'right' },
  };
}

// Verbatim copy of MDC_PRESETS deltas (index.html ~10003).
export const MDC_PRESETS = {
  house: {},
  corner: { page: { dots: true, itemGap: 3, secGap: 10, margin: 0.45 }, title: { f: 5, s: 22, w: 'bold', sp: 60 },
    section: { f: 5, s: 13, w: 'bold', sp: 80 }, sub: { f: 5, s: 10 }, name: { f: 5, s: 12 }, brand: { f: 5, s: 12 },
    desc: { f: 5, s: 10 }, price: { f: 5, s: 12 } },
  coastal: { page: { rules: false, itemGap: 10, secGap: 22, margin: 0.8, ink: '#2b3a42' }, title: { f: 6, s: 24, sp: 180, c: '#2b3a42' },
    subtitle: { f: 6, s: 10, sp: 300, c: '#7d8f99' }, section: { f: 6, s: 12, w: 'normal', sp: 260, c: '#2b3a42' },
    sub: { f: 6, s: 9, sp: 200, c: '#7d8f99' }, name: { f: 6, s: 12, c: '#2b3a42' }, brand: { f: 6, s: 12, c: '#4a5d68' },
    desc: { f: 6, s: 10, c: '#7d8f99' }, price: { f: 6, s: 12, c: '#2b3a42' } },
  slate: { page: { bg: '#1c1c1a', ink: '#f0e6d2', rule: '#6b6355' }, title: { s: 25, c: '#f0e6d2' }, subtitle: { c: '#9c9384' },
    section: { c: '#d8c9a3' }, sub: { c: '#9c9384' }, name: { c: '#f0e6d2' }, brand: { c: '#d8c9a3' }, desc: { c: '#9c9384' },
    price: { c: '#f0e6d2' } },
  press: { page: { itemGap: 7, secGap: 18 }, title: { f: 1, s: 30, sp: 0 }, subtitle: { f: 4, s: 10, sp: 240 },
    section: { f: 1, s: 16, w: 'normal', sp: 0, cs: 'none' }, sub: { f: 4, s: 9, sp: 180 }, name: { f: 4, s: 12, w: 'bold' },
    brand: { f: 4, s: 12, i: true }, desc: { f: 4, s: 10 }, price: { f: 4, s: 12 } },
};

// `accent` = the colour the designer uses for featured-item emphasis and that brand/voice colours replace.
// `roles` says which levels carry the accent so a brand colour lands in the right places.
export const LOOKS = [
  {
    k: 'noir', label: 'Speakeasy Noir', base: 'slate', accent: '#c9a45c', accent2: '#c7876a', roles: ['section', 'price', 'subtitle'],
    note: 'Near-black page, cream ink, antique-gold heads. Low-light legible: generous size, no hairline type.',
    fits: { venue: ['cocktail_lounge', 'nightclub', 'hotel_bar'], tone: ['dark', 'elegant', 'vintage'] },
    d: { page: { bg: '#151412', ink: '#efe6d4', rule: '#3d372e', margin: 0.7, itemGap: 8, secGap: 20, rules: true },
      title: { f: 2, s: 34, w: 'normal', sp: 320, c: '#efe6d4', cs: 'upper' },
      subtitle: { f: 4, s: 9, sp: 420, c: '#c9a45c', cs: 'upper' },
      section: { f: 2, s: 15, w: 'normal', sp: 320, c: '#c9a45c', cs: 'upper' },
      sub: { f: 4, s: 9, w: 'normal', sp: 300, c: '#9a907f', cs: 'upper' },
      name: { f: 2, s: 14, w: 'bold', c: '#efe6d4' }, brand: { f: 2, s: 14, i: true, c: '#c9a45c' },
      desc: { f: 4, s: 11, c: '#b3a994' }, price: { f: 4, s: 13, c: '#c9a45c' } },
  },
  {
    k: 'cantina', label: 'Cantina Sol', base: 'house', accent: '#b5532f', roles: ['title', 'section'],
    note: 'Warm sand page, terracotta heads, agave-teal prices. Bold geometric heads read across a loud room.',
    fits: { venue: ['latin_cantina'], tone: ['latin', 'playful', 'rustic', 'casual'] },
    d: { page: { bg: '#f6eddd', ink: '#2b1a12', rule: '#d8c3a2', margin: 0.6, itemGap: 7, secGap: 18 },
      title: { f: 6, s: 38, w: 'bold', sp: 220, c: '#b5532f', cs: 'upper' },
      subtitle: { f: 4, s: 10, sp: 380, c: '#6d4c3d', cs: 'upper' },
      section: { f: 6, s: 15, w: 'bold', sp: 260, c: '#b5532f', cs: 'upper' },
      sub: { f: 6, s: 9, w: 'bold', sp: 240, c: '#1f6f6b', cs: 'upper' },
      name: { f: 4, s: 13, w: 'bold', c: '#2b1a12' }, brand: { f: 4, s: 13, i: true, c: '#6d4c3d' },
      desc: { f: 4, s: 11, c: '#6d4c3d' }, price: { f: 4, s: 13, w: 'bold', c: '#1f6f6b' } },
  },
  {
    k: 'taproom', label: 'Taproom', base: 'corner', accent: '#b7791f', roles: ['section', 'sub'],
    note: 'Chalk-paper page, condensed-feeling bold sans, leader dots to prices. Dense and scannable for long beer lists.',
    fits: { venue: ['brewery', 'sports_bar', 'dive_bar'], tone: ['industrial', 'rustic', 'casual'] },
    d: { page: { bg: '#f1eee6', ink: '#1d1d1b', rule: '#1d1d1b', dots: true, margin: 0.5, itemGap: 5, secGap: 14 },
      title: { f: 3, s: 36, w: 'bold', sp: 80, c: '#1d1d1b', cs: 'upper' },
      subtitle: { f: 3, s: 10, sp: 300, c: '#5b5a55', cs: 'upper' },
      section: { f: 3, s: 15, w: 'bold', sp: 160, c: '#b7791f', cs: 'upper' },
      sub: { f: 3, s: 10, w: 'bold', sp: 200, c: '#5b5a55', cs: 'upper' },
      name: { f: 3, s: 13, w: 'bold', c: '#1d1d1b' }, brand: { f: 3, s: 13, i: true, c: '#5b5a55' },
      desc: { f: 5, s: 10, c: '#5b5a55' }, price: { f: 3, s: 13, w: 'bold', c: '#1d1d1b' } },
  },
  {
    k: 'cellar', label: 'Cellar & Vine', base: 'press', accent: '#6a1f2b', accent2: '#5b6b3a', roles: ['title', 'section'],
    note: 'Ivory page, bordeaux serif heads, italic tasting notes, lots of air. Glass / bottle pricing sits cleanly.',
    fits: { venue: ['wine_bar', 'fine_dining', 'restaurant'], tone: ['elegant', 'rustic'] },
    d: { page: { bg: '#fbf8f2', ink: '#2a1a1c', rule: '#d6c7b8', rules: false, margin: 0.85, itemGap: 9, secGap: 24 },
      title: { f: 2, s: 34, w: 'normal', sp: 120, c: '#6a1f2b', cs: 'none' },
      subtitle: { f: 2, s: 11, i: true, sp: 60, c: '#7d6b60', cs: 'none' },
      section: { f: 2, s: 16, w: 'normal', sp: 260, c: '#6a1f2b', cs: 'upper' },
      sub: { f: 2, s: 12, i: true, sp: 0, c: '#7d6b60', cs: 'none' },
      name: { f: 2, s: 14, w: 'normal', c: '#2a1a1c' }, brand: { f: 2, s: 14, i: true, c: '#5b4b44' },
      desc: { f: 2, s: 11, i: true, c: '#6e6259' }, price: { f: 2, s: 14, c: '#2a1a1c' } },
  },
  {
    k: 'grand', label: 'Grand Hotel', base: 'house', accent: '#a8873f', accent2: '#7a4a3a', roles: ['subtitle', 'section'],
    note: 'Warm white, navy ink, brass tracking caps. Quiet luxury for hotel bars and upscale rooms.',
    fits: { venue: ['hotel_bar', 'fine_dining', 'cocktail_lounge'], tone: ['elegant', 'light', 'vintage'] },
    d: { page: { bg: '#fffdf8', ink: '#1b2a41', rule: '#cbb88c', margin: 0.85, itemGap: 8, secGap: 22 },
      title: { f: 0, s: 30, w: 'normal', sp: 380, c: '#1b2a41', cs: 'upper' },
      subtitle: { f: 4, s: 9, sp: 460, c: '#a8873f', cs: 'upper' },
      section: { f: 0, s: 14, w: 'normal', sp: 340, c: '#a8873f', cs: 'upper' },
      sub: { f: 4, s: 9, sp: 300, c: '#5d6b7d', cs: 'upper' },
      name: { f: 0, s: 14, w: 'normal', c: '#1b2a41' }, brand: { f: 0, s: 14, i: true, c: '#5d6b7d' },
      desc: { f: 4, s: 11, c: '#5d6b7d' }, price: { f: 4, s: 13, c: '#1b2a41' } },
  },
  {
    k: 'coastal', label: 'Coastal', base: 'coastal', accent: '#1f6f6b', roles: ['section', 'price'],
    note: 'Menu Studio Coastal, warmed: sea-glass teal on sand, airy spacing, no rules.',
    fits: { venue: ['restaurant', 'hotel_bar'], tone: ['coastal', 'light', 'minimal'] },
    d: { page: { bg: '#f7f4ec', ink: '#23343b' }, title: { s: 30, c: '#23343b' }, section: { s: 13, c: '#1f6f6b', w: 'bold' },
      name: { s: 13, c: '#23343b' }, desc: { s: 11, c: '#667a82' }, price: { s: 13, c: '#1f6f6b' } },
  },
  {
    k: 'tavern', label: 'Corner Tavern', base: 'corner', accent: '#b3261e', roles: ['title', 'section'],
    note: 'Pure white, big red masthead, black bold sans, leader dots. Fast to read standing at a busy bar.',
    fits: { venue: ['dive_bar', 'sports_bar'], tone: ['playful', 'casual'] },
    d: { page: { bg: '#ffffff', ink: '#111111', rule: '#111111', dots: true, margin: 0.5, itemGap: 5, secGap: 14 },
      title: { f: 3, s: 40, w: 'bold', sp: 0, c: '#b3261e', cs: 'upper' },
      subtitle: { f: 3, s: 10, w: 'bold', sp: 260, c: '#111111', cs: 'upper' },
      section: { f: 3, s: 16, w: 'bold', sp: 80, c: '#b3261e', cs: 'upper' },
      sub: { f: 3, s: 10, w: 'bold', sp: 160, c: '#444444', cs: 'upper' },
      name: { f: 3, s: 13, w: 'bold', c: '#111111' }, brand: { f: 3, s: 13, i: true, c: '#444444' },
      desc: { f: 3, s: 10, c: '#555555' }, price: { f: 3, s: 13, w: 'bold', c: '#111111' } },
  },
  {
    k: 'tropic', label: 'Tropic', base: 'house', accent: '#e0603f', roles: ['title', 'price'],
    note: 'Cream page, coral masthead and prices, jungle-green heads. For tiki, rooftop and patio programs.',
    fits: { venue: ['tiki'], tone: ['playful', 'coastal'] },
    d: { page: { bg: '#fff7ea', ink: '#1e2a24', rule: '#1f5b44', margin: 0.6, itemGap: 7, secGap: 18 },
      title: { f: 6, s: 40, w: 'bold', sp: 160, c: '#e0603f', cs: 'upper' },
      subtitle: { f: 4, s: 10, sp: 360, c: '#1f5b44', cs: 'upper' },
      section: { f: 6, s: 15, w: 'bold', sp: 220, c: '#1f5b44', cs: 'upper' },
      sub: { f: 4, s: 9, sp: 260, c: '#5f6f66', cs: 'upper' },
      name: { f: 4, s: 13, w: 'bold', c: '#1e2a24' }, brand: { f: 4, s: 13, i: true, c: '#5f6f66' },
      desc: { f: 4, s: 11, c: '#5f6f66' }, price: { f: 4, s: 13, w: 'bold', c: '#c24d2f' } },
  },
  {
    k: 'minimal', label: 'Studio Minimal', base: 'house', accent: '#111111', roles: ['section'],
    note: 'Swiss-style: one sans family, left-aligned masthead, no rules, weight and space do the work.',
    fits: { venue: ['restaurant', 'cocktail_lounge'], tone: ['minimal', 'light'] },
    d: { page: { bg: '#ffffff', ink: '#111111', rules: false, margin: 0.75, itemGap: 9, secGap: 22 },
      title: { f: 3, s: 30, w: 'bold', sp: 0, c: '#111111', cs: 'none', al: 'left' },
      subtitle: { f: 3, s: 10, sp: 200, c: '#6b6b6b', cs: 'upper', al: 'left' },
      section: { f: 3, s: 11, w: 'bold', sp: 260, c: '#111111', cs: 'upper' },
      sub: { f: 3, s: 9, w: 'normal', sp: 220, c: '#6b6b6b', cs: 'upper' },
      name: { f: 3, s: 13, w: 'bold', c: '#111111' }, brand: { f: 3, s: 13, c: '#6b6b6b' },
      desc: { f: 3, s: 11, c: '#6b6b6b' }, price: { f: 3, s: 13, c: '#111111' } },
  },
  {
    k: 'deco', label: 'Midnight Deco', base: 'slate', accent: '#d4af61', accent2: '#9fb8cf', roles: ['title', 'section', 'price'],
    note: 'Midnight navy, champagne-gold geometric caps, Palatino body. Jazz-age glamour without ornament.',
    fits: { venue: ['cocktail_lounge', 'hotel_bar', 'nightclub'], tone: ['vintage', 'dark', 'elegant'] },
    d: { page: { bg: '#101c2b', ink: '#f1e7cf', rule: '#3b4a5e', margin: 0.7, itemGap: 8, secGap: 20 },
      title: { f: 6, s: 34, w: 'normal', sp: 480, c: '#d4af61', cs: 'upper' },
      subtitle: { f: 6, s: 9, sp: 480, c: '#9aa6b5', cs: 'upper' },
      section: { f: 6, s: 14, w: 'normal', sp: 420, c: '#d4af61', cs: 'upper' },
      sub: { f: 6, s: 9, sp: 320, c: '#9aa6b5', cs: 'upper' },
      name: { f: 2, s: 14, w: 'bold', c: '#f1e7cf' }, brand: { f: 2, s: 14, i: true, c: '#d4af61' },
      desc: { f: 2, s: 11, i: true, c: '#b9b2a0' }, price: { f: 6, s: 13, c: '#d4af61' } },
  },
];

export const LOOK_BY_KEY = Object.fromEntries(LOOKS.map(l => [l.k, l]));

export function styleForLook(look) {
  const s = mdcStyleDefault();
  merge(s, MDC_PRESETS[look.base] || {});
  merge(s, look.d);
  return s;
}

export function merge(base, d) {
  for (const k of Object.keys(d || {})) {
    base[k] = base[k] || {};
    for (const p of Object.keys(d[k])) base[k][p] = d[k][p];
  }
  return base;
}

// Map a spoken or brand font request onto the nearest MDC font index.
export function fontIndexFor(name) {
  const n = String(name || '').toLowerCase();
  const table = [
    [/georgia|serif(?!.*sans)|classic|garamond|caslon|baskerville|bodoni|didot/, 0], [/times/, 1],
    [/palatino|book|elegant|pagella/, 2], [/helvetica|arial|sans|swiss|grotesk|inter|roboto/, 3],
    [/avenir|futura pt|gotham|proxima|montserrat|lato|nunito/, 4], [/trebuchet|humanist|friendly/, 5],
    [/century gothic|futura|geometric|deco|bold/, 6], [/courier|typewriter|mono/, 7],
  ];
  for (const [re, i] of table) if (re.test(n)) return i;
  return null;
}
