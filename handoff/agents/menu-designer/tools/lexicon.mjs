// Shared vocabulary for the PHG Menu Designer: drinks lists, spoken cues, style words.
// Every drinks list is a first-class citizen; order here is only the default section order.

export const LISTS = [
  { key: 'cocktails',      label: 'Cocktails',            kind: 'bev',  words: ['cocktails', 'cocktail', 'signature drinks', 'signatures', 'house drinks', 'mixed drinks', 'well drinks', 'wells', 'classics', 'martinis', 'margaritas', 'spritzes', 'shots'] },
  { key: 'beer',           label: 'Beer',                 kind: 'bev',  words: ['beers', 'beer', 'on draft', 'draft', 'draught', 'on tap', 'taps', 'cans', 'bottles and cans', 'bottled beer', 'lagers', 'ales', 'ipas'] },
  { key: 'cider_seltzer',  label: 'Cider & Seltzer',      kind: 'bev',  words: ['cider and seltzer', 'ciders', 'cider', 'seltzers', 'seltzer', 'hard seltzer'] },
  { key: 'wine_sparkling', label: 'Sparkling',            kind: 'bev',  words: ['sparkling wine', 'sparkling', 'bubbles', 'champagne', 'prosecco', 'cava'] },
  { key: 'wine_white',     label: 'White Wine',           kind: 'bev',  words: ['white wines', 'white wine', 'whites'] },
  { key: 'wine_rose',      label: 'Rosé',                 kind: 'bev',  words: ['rose wine', 'rosé wine', 'rosés', 'roses', 'rosé', 'rose'] },
  { key: 'wine_red',       label: 'Red Wine',             kind: 'bev',  words: ['red wines', 'red wine', 'reds'] },
  { key: 'wine',           label: 'Wine',                 kind: 'bev',  words: ['wines by the glass', 'wine by the glass', 'wine list', 'wines', 'wine'] },
  { key: 'vodka',          label: 'Vodka',                kind: 'bev',  words: ['vodkas', 'vodka'] },
  { key: 'gin',            label: 'Gin',                  kind: 'bev',  words: ['gins', 'gin'] },
  { key: 'rum',            label: 'Rum',                  kind: 'bev',  words: ['rums', 'rum', 'rhum'] },
  { key: 'tequila',        label: 'Tequila',              kind: 'bev',  words: ['tequilas', 'tequila', 'agave'] },
  { key: 'mezcal',         label: 'Mezcal',               kind: 'bev',  words: ['mezcals', 'mezcal', 'mescal'] },
  { key: 'whiskey',        label: 'Whiskey',              kind: 'bev',  words: ['whiskeys', 'whiskies', 'whiskey', 'whisky', 'bourbons', 'bourbon', 'ryes', 'scotch', 'scotches', 'japanese whisky', 'brown spirits'] },
  { key: 'brandy_cognac',  label: 'Brandy & Cognac',      kind: 'bev',  words: ['brandy and cognac', 'cognacs', 'cognac', 'brandies', 'brandy', 'armagnac', 'calvados'] },
  { key: 'liqueurs_amari', label: 'Liqueurs & Amari',     kind: 'bev',  words: ['liqueurs and amari', 'amari', 'amaro', 'liqueurs', 'liqueur', 'digestifs', 'cordials', 'aperitifs'] },
  { key: 'sake_soju',      label: 'Sake & Soju',          kind: 'bev',  words: ['sake and soju', 'sakes', 'sake', 'soju', 'shochu'] },
  { key: 'non_alcoholic',  label: 'Zero Proof',           kind: 'bev',  words: ['non alcoholic', 'non-alcoholic', 'na drinks', 'n/a', 'zero proof', 'zero-proof', 'spirit free', 'spirit-free', 'mocktails', 'mocktail', 'soft drinks', 'sodas', 'coffee and tea', 'coffee', 'tea'] },
  { key: 'food_small',     label: 'Small Plates',         kind: 'food', words: ['small plates', 'snacks', 'bar snacks', 'starters', 'appetizers', 'apps', 'shareables', 'to share', 'bites', 'tapas'] },
  { key: 'food_mains',     label: 'Mains',                kind: 'food', words: ['mains', 'entrees', 'entrées', 'large plates', 'plates', 'burgers', 'sandwiches', 'tacos', 'pizzas', 'pizza'] },
  { key: 'food_sides',     label: 'Sides',                kind: 'food', words: ['sides', 'side dishes'] },
  { key: 'food_dessert',   label: 'Dessert',              kind: 'food', words: ['desserts', 'dessert', 'sweets'] },
];

export const LIST_BY_KEY = Object.fromEntries(LISTS.map(l => [l.key, l]));

// Longest phrase first so "red wine" beats "wine" and "on draft" beats "draft".
export const LIST_PHRASES = LISTS.flatMap(l => l.words.map(w => ({ w, key: l.key })))
  .sort((a, b) => b.w.length - a.w.length);

export const FLAG_WORDS = {
  house_special: ['house special', 'house favorite', 'house favourite', 'our signature', 'signature', 'our specialty', 'specialty of the house', 'house'],
  featured:      ['featured', 'feature it', 'feature this', 'highlight', 'highlight it', 'push this', 'best seller', 'bestseller', 'most popular', 'popular'],
  new:           ['new this', "it's new", 'new item', 'brand new', 'just added', 'new'],
  seasonal:      ['seasonal', 'for the season', 'this season', 'limited time', 'limited', 'fall only', 'summer only', 'winter only', 'spring only'],
};

export const MENU_TYPES = [
  { key: 'Happy hour page',       words: ['happy hour', 'hh menu', 'happy-hour'] },
  { key: 'Specials / events page', words: ['specials page', 'special event', 'event menu', 'tonight only', 'specials board', 'brunch special', 'holiday menu', 'new years', 'valentine'] },
  { key: 'Drinks + food',         words: ['drinks and food', 'food and drinks', 'food and drink', 'drinks plus food'] },
  { key: 'Food menu',             words: ['food menu', 'dinner menu', 'lunch menu', 'brunch menu'] },
  { key: 'Drinks menu',           words: ['drinks menu', 'drink menu', 'cocktail menu', 'bar menu', 'beverage menu', 'wine list', 'beer list'] },
];

export const FORMAT_WORDS = {
  letter: ['letter size', 'letter', '8.5 by 11', 'eight and a half by eleven', 'standard page'],
  legal: ['legal size', 'legal'],
  tabloid: ['tabloid', '11 by 17', 'eleven by seventeen'],
  half_letter: ['half page', 'half sheet', 'half letter', '5.5 by 8.5'],
  table_tent: ['table tent', 'tent card'],
  phone: ['phone', 'mobile', 'qr', 'qr code', 'online menu'],
  tablet: ['tablet', 'ipad'],
  tv: ['tv', 'television', 'screen board', 'menu board', 'digital board'],
};

// Words people actually say about a look, mapped onto style axes the designer uses.
export const TONE_WORDS = {
  dark: ['dark', 'moody', 'black background', 'all black', 'speakeasy', 'low light', 'sexy', 'sultry'],
  light: ['light', 'bright', 'airy', 'white background', 'clean white', 'sunny'],
  elegant: ['elegant', 'classy', 'upscale', 'fancy', 'refined', 'luxury', 'luxurious', 'high end', 'high-end', 'sophisticated', 'fine dining'],
  rustic: ['rustic', 'farmhouse', 'wood', 'woody', 'country', 'barn', 'craft'],
  playful: ['playful', 'fun', 'colorful', 'colourful', 'loud', 'tropical', 'tiki', 'bold', 'party', 'vibrant'],
  minimal: ['minimal', 'minimalist', 'simple', 'clean', 'modern', 'scandinavian', 'sleek'],
  vintage: ['vintage', 'retro', 'old school', 'old-school', 'classic', 'art deco', 'deco', 'prohibition', '1920s', 'twenties'],
  latin: ['cantina', 'mexican', 'latin', 'latino', 'mezcaleria', 'taqueria', 'agave bar'],
  coastal: ['coastal', 'beach', 'nautical', 'ocean', 'surf', 'seaside'],
  industrial: ['industrial', 'brewery', 'taproom', 'warehouse', 'concrete'],
  casual: ['casual', 'laid back', 'laid-back', 'chill', 'relaxed', 'easygoing', 'friendly', 'neighborhood'],
};

export const COLOR_WORDS = {
  black: '#111111', white: '#ffffff', cream: '#f4ecd8', ivory: '#f8f3e6', gold: '#b8903a', brass: '#a8873f',
  navy: '#1b2a41', blue: '#2458a6', teal: '#1f6f6b', green: '#2f5d3a', emerald: '#1d6b4f', olive: '#6b6b2f',
  burgundy: '#6d1f2c', wine: '#6d1f2c', red: '#b3261e', coral: '#e2674f', orange: '#d9772b', terracotta: '#b75a3c',
  pink: '#d77a8f', blush: '#e8c3c3', purple: '#5b3a78', lavender: '#b7a6d6', yellow: '#e2b93b', mustard: '#c99a2e',
  brown: '#5a3e2b', tan: '#c8a97e', grey: '#6b6b6b', gray: '#6b6b6b', charcoal: '#2b2b2b', silver: '#a7a9ac', copper: '#b8733f',
};

export const VENUE_TYPES = {
  cocktail_lounge: ['cocktail bar', 'cocktail lounge', 'lounge', 'speakeasy'],
  dive_bar: ['dive bar', 'dive', 'neighborhood bar', 'neighbourhood bar', 'pub'],
  brewery: ['brewery', 'taproom', 'brewpub', 'beer hall', 'beer garden'],
  wine_bar: ['wine bar', 'enoteca', 'wine shop'],
  fine_dining: ['fine dining', 'tasting menu', 'steakhouse'],
  latin_cantina: ['cantina', 'taqueria', 'mexican restaurant', 'mezcaleria', 'agave bar'],
  hotel_bar: ['hotel bar', 'hotel lobby', 'rooftop', 'rooftop bar'],
  sports_bar: ['sports bar', 'sports pub'],
  restaurant: ['restaurant', 'bistro', 'brasserie', 'gastropub', 'cafe', 'café', 'diner'],
  nightclub: ['nightclub', 'club', 'bottle service'],
  tiki: ['tiki bar', 'tiki'],
};
