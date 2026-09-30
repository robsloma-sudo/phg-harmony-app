# TEST-1 round 17: "Sun Behind the Page", Cantina & Cocktail Bar, Iowa City (proposal v17)

## Creative thesis

**A late gold sun sets behind a torn page, and an agave rises toward the list. The menu reads as one hand-cut paper
collage, warm and unhurried, where the art stays in the rail and the drinks sit in calm editorial type.**

- **Concept words (6):** torn paper · setting sun · agave · dusk warmth · editorial calm · hand-cut
- **Avoid-list:** lotería cards and papel picado (retired after round 16); sombreros, cacti clip-art, skulls, piñatas, serape
  stripes; neon or "fiesta" colour; any lettering inside the art; trademarked worlds; fake distressed grunge; gold anywhere
  but the sun; boxed modules; a second illustration style; taglines that state item facts.

**Device → thesis trace**

| Device | Traces to |
|---|---|
| Torn page edge (cream fibre rim + one down-left shadow) | torn paper, hand-cut; the page is laid over the scene so the art stays in the rail |
| Gold-leaf sun disc, cropped by the torn edge | setting sun; gold accent (the only gold on the page) |
| Agave rosette, two-tone "folded" leaves, tips leaning toward the list | agave; gaze vector toward the content (crop_with_intent) |
| Two torn hill bands and the deep ground band | dusk warmth; the ground also backs the lower tagline |
| Paper-fibre grain (feTurbulence), 55 % in the rail, 10 % on the menu paper | hand-cut paper; lower texture contrast near text |
| Vertical CANTINA wordmark + vertical "& COCKTAIL BAR · IOWA CITY, IOWA" | editorial calm; the name stands at the seam where the sun sets |
| Side-rail taglines GOOD DRINKS / GOOD COMPANY and PULL UP / A CHAIR / STAY / A WHILE | unhurried, generic brand voice (no item facts) |
| Section rule + italic tagline (raise a glass / one more round / for the table / ¡salud!) | editorial calm; generic voice |
| Terracotta tracked-caps subheads | dusk warmth (hill colour carried into the type) |
| Dotted leaders | functional: item-to-price association |

One illustration grammar: flat cut-paper planes, torn or displaced edges, one light direction (top right, shadows down and
to the left), no outlines, no gradients inside shapes except the sky wash and the sun's leaf light. One image treatment:
warm, low-saturation earth palette, the same fibre grain everywhere, edges always torn and never cleanly vector-cut.

## Restraint pass (scorecard 1c)

Inventory, 22 devices considered (baseline round 16 plus this round's plan):
1 torn page edge · 2 gold-leaf sun · 3 agave rosette · 4 torn hills · 5 ground band · 6 paper grain · 7 sky wash ·
8 vertical wordmark · 9 vertical venue/location line · 10 top rail tagline · 11 bottom rail tagline · 12 section rules
with italic taglines · 13 terracotta subheads · 14 dotted leaders · 15 Bistro-style gold vertical hairlines · 16 gold
ticks above section heads · 17 boxed footer card · 18 serve-cue line under each cocktail (method / glass) · 19 bilingual
SPANISH · English subheads · 20 menu-column intro block (COCKTAILS · BEER · WINE · SPIRITS + rule) · 21 second, distant
agave silhouette on the hill · 22 "¡Salud!" footer sign-off.

**Removed (8 of 22 = 36 %):** 15, 16 (a second gold would break "gold only on the sun"), 17 (enclosure for a generic
line), 18 (the cue line added a third line to each cocktail and repeated method/glass facts; garnish moved into the
ingredient line instead), 19 (the doubled labels cluttered the editorial column; the draft's own English names print),
20 (it repeats the section heads), 21 (a second literal agave weakens the one anchor, per literal_motif_ablation), 22 (a
sign-off in a corner competes with the bottom tagline; "¡salud!" survives as the Spirits rule tagline).
Honesty note: 15, 16, 17, 20 and 21 were cut at the plan and first-render stage; 18 and 19 are cut from the round-16
baseline. Nothing came back: removing any of the 14 that remain either loses the concept (1-9), the reading path (12-13),
price association (14) or the rail's balance (10-11).

## Revision hypothesis and best-so-far

Hypothesis: the lotería tabla (rounds 13-16) plateaued on criteria 5, 6 and 15 because four equal cards gave four equal
focal points and forced card feet or dead space (El Barril 84 pt). One editorial column beside one art rail should give a
single entry point (wordmark, then Cocktails), fill the page with no empty card, and pass criterion 16 with a written thesis.
Criteria where round 16 is best-so-far and must not regress: 9 (prices, kept exact), 11 (sourced copy, kept; three
corrections applied), 1 and 3 (one left edge and one price edge per column, both 0.0 pt spread here), and 6 (36 pt margins,
now measured on ink at 12.62-12.78 mm).

## Layout geometry (summary; full element list in layout.json)

- Page: US letter 612 x 792 pt (215.9 x 279.4 mm), margins 36 pt (12.7 mm) on all sides, art bleed 9 pt (3.175 mm).
- Zones: art rail x -9..~158 pt (torn edge wanders 150-166); wordmark lane 166-262 pt; menu column 282-576 pt (294 pt, 103.7 mm).
  Lower pair: Wine 282-420, Spirits 438-576 (18 pt gutter).
- Type: CANTINA Fraunces 96 pt vertical (opsz 144, weight 380); heads Fraunces 600 15 pt, tracked .2em; rule taglines Fraunces italic
  9.5 pt; subheads DM Sans 700 7.5 pt tracked .26em in #9A3B22; names Fraunces 600 11 pt caps tracked .11em; ingredient lines
  Fraunces 400 10.5 pt, 14 pt leading, #40352D; prices Fraunces 600 12.5 pt tabular, no currency sign.
- Palette: paper #F2E9D6, ink #1D1815, terracotta #9A3B22, agave greens #244A3E-#56866F, hills #B5532F/#7C3322, ground
  #162C25, gold (sun only) #C99532-#E4BF66.
- Rhythm: 10 pt between items, 30 pt across a subhead, 31.64 pt between sections (about 3x the item gap).

## Hard gates (measured from the render; all in layout.json → measured_checks)

| Gate | Result | Evidence |
|---|---|---|
| accessibility (4.5:1 at the worst pixel) | **pass** | Letter minimum by role: title 13.06, tagline 6.31, header 13.15, subheader 5.21, item_name 13.18, price 13.31, description 8.91. Phone minimum 5.76. Method: text-free 300 dpi render, each line's ink box +2 px, every background pixel checked. |
| menu_item_association | **pass** | Prices sit on the name row; every row has a dotted leader (eye travel up to 72% of the column, all led). Price right edges spread 0.0 pt per column; name left edges 0.0 pt. Phone: prices on the name row, leaders kept. |
| legibility, 1 m (letter) | **pass** | Threshold 5 arcmin at 1 m (Snellen 20/20 detail). Names: cap height 2.65 mm = 9.1'. Prices: 10.91'. Ingredient lines: x-height 1.85 mm = 6.37'. Heads 12.73'. Subheads 6.37'. The rail taglines are decorative, all caps at 6.37'. |
| equal 36 pt margins | **pass** | Text ink to trim: left 12.78 mm, top 12.7, right 12.62, bottom 12.62 (spread 0.17 mm). |
| bleed and safe area | **pass** | Art layer box x -9, y -9, 630 x 810 pt, so 3.175 mm past trim on all four sides. All text sits inside the 36 pt inset. Print file menu-print-bleed.pdf has the bleed and crop marks; menu.pdf is trim size. |
| content_integrity | **pass (with open questions)** | Prices match the draft 14/14; names unchanged; every item has an ingredient-style line; no tagline states an item fact. |
| environmental_legibility | **pass** | Dark ink on warm paper for all essential text; no metallic ink on text (the gold is art only); no reversed small type in the menu column. The only reversed text is the 7.5 pt bottom rail tagline (decorative, 7.6:1). |

Other measured checks: one header size (15 pt) and one subhead size (7.5 pt); the Wine and Spirits columns both end at
757.43 pt; the menu column ends on the bottom margin (no dead field). Phone: 1170 px wide, no horizontal
scroll, minimum type 11 css px (subheads) and 15 px for names and lines. Letter PNG 2550 x 3300 px, not downscaled.

## Copy (sourced wording from round 16, recast as "word · word"; corrections applied)

Corrections: "poured straight" removed; no name-echo tags (a line never repeats a word from its item name); Manhattan without
bitters (draft meta.public_components {"aromatic-bitters": false}). Method and glass cues ("Stirred:", "In a coupe") are dropped
(restraint, item 18); garnishes from the recipe versions stay as the last ingredient. "Draft" and "By the Glass" print only
as subheads, as in the draft.

| Section / sub | Item | Price | Printed line | Source |
|---|---|---|---|---|
| Cocktails / Classics | Margarita | 15 | tequila blanco · fresh lime · orange liqueur · agave syrup · lime wheel | draft desc 'Tequila blanco, lime, orange liqueur, agave'; draft components 'Fresh Lime Juice', 'Agave Syrup'; garnish 'Lime wheel' from phg.recipe_versions f06abb74 |
| Cocktails / Classics | Manhattan | 15 | rye · sweet vermouth · cocktail cherry | draft desc 'Rye, sweet vermouth, aromatic bitters.' with bitters hidden (meta.public_components {'aromatic-bitters': false}); draft component 'Cocktail Cherry' (role Garnish); recipe_versions 9fb77eaa garnish 'Cocktail cherry' |
| Cocktails / House Originals | Brown Butter Old Fashioned | 16 | brown butter-washed bourbon · demerara syrup · aromatic bitters · orange peel | draft components 'Brown Butter-Washed Bourbon', 'Demerara Syrup', 'Aromatic Bitters' (not hidden); garnish 'Orange peel' from phg.recipe_versions 7095fd3d |
| Cocktails / House Originals | House Daiquiri | 14 | white rum · fresh lime · house demerara syrup · lime coin | draft desc 'White rum, lime, and house demerara syrup.'; component 'Fresh Lime Juice'; garnish 'Lime coin' from phg.recipe_versions 14d45e57 |
| Beer / Draft | Czech Pilsner | 7 | crisp · pale lager | draft desc 'Crisp pale lager.' |
| Beer / Draft | Dry-Hopped IPA | 8 | hop-forward | draft desc 'Hop-forward draft IPA.' ('draft' lives in the Draft subhead; 'IPA' would echo the name) |
| Beer / Draft | Amber Lager | 7 | toasty | draft desc 'Toasty amber lager.' ('amber lager' would echo the name) |
| Cider / Cider | Dry Cider | 8 | sparkling | draft desc 'Dry sparkling cider.' ('dry', 'cider' would echo the name) |
| Wine / By the Glass | Malbec | 12 | dry · red | draft desc 'Dry red wine.' |
| Wine / By the Glass | Pinot Grigio | 11 | dry · white | draft desc 'Dry white wine.' |
| Wine / Sparkling | Brut Rosé | 13 | dry · sparkling | draft desc 'Dry sparkling rosé.' ('rosé' would echo the name) |
| Spirits / Agave | Blanco Tequila | 12 | pour | draft desc 'Blanco tequila pour.' (every other word echoes the name) |
| Spirits / Agave | Añejo Tequila | 16 | pour | draft desc 'Añejo tequila pour.' (every other word echoes the name) |
| Spirits / Brandy | Cognac VSOP | 18 | pour | draft desc 'VSOP Cognac pour.' (every other word echoes the name) |

Taglines (all generic brand voice, none states an item fact): rail GOOD DRINKS / GOOD COMPANY; PULL UP / A CHAIR / STAY /
A WHILE; section rules "raise a glass", "one more round", "for the table", "¡salud!".
No gateway calls this round; the facts come from round 16's logged rows (log_id 167-171) and draft_doc.json.

## Flags and needs_input (for the venue, via the Coordinator)

needs_input = true. risk_flags: missing_ingredients (spirits, beer, wine detail), allergen_unconfirmed, price_label_unknown.
1. **Spirits lines read only "pour".** Every other word in the draft descriptions echoes the item name. Please send brand, age
   statement and pour size for Blanco Tequila, Añejo Tequila and Cognac VSOP so the line can say something useful.
2. **Beer and cider:** brewery or producer and ABV (Czech Pilsner, Dry-Hopped IPA, Amber Lager, Dry Cider). The IPA, Amber and
   Cider lines are one word ("hop-forward", "toasty", "sparkling") because the other words echo the names.
3. **Wine:** producer and region, so wine can print as producer · region (Rob's format); the pour size by the glass.
4. **Brut Rosé: glass or bottle?** The price label is empty in the draft, so the price prints unlabelled.
5. **Brown Butter Old Fashioned:** confirm the dairy allergen note.
6. **Manhattan bitters:** the draft hides them; confirm that is intended.
7. **Venue name:** the design uses "Cantina" / "& Cocktail Bar" from the round-16 title (the draft title is "Bar menu").
8. **Cantina gaps** (asked, not added): a Mexican lager, mezcal, a non-alcoholic agua fresca?
9. **Art pipeline:** this art is SVG because generated raster art cannot be downloaded here yet. A Canva generate-image prompt for a
   future raster ART layer: "Text-free vertical collage, 1:4.5, hand-torn warm paper: pale apricot sky, large gold-leaf sun
   disc half hidden behind a torn cream paper edge on the right, one blue-green agave rosette of folded paper leaves leaning
   up and right, two torn terracotta hills, deep green ground at the bottom, soft paper fibre, one light from top right, no
   lettering, no people, no logos."

## References

Library (`menu_visual_documents.id`): 572 (Coa Cantina, Iowa City: agave first, the local price band); 7923 (Coa Cantina,
Des Moines: compact cocktail-led list); 4969 (Blue Agave, Iowa: Classic / House tiers); 208 (Alta Calidad: pour size in the
header once supplied); 2585 (La Buena Vida: Spanish used sparingly for tone).
Quality bar: handoff/designs/references/rob-2026-09-28/ ref-01 (the Bistro: vertical wordmark, art rail, tracked caps with a
serif ingredient line, rule taglines, side-rail taglines); ref-04 (Solstice: large sun disc, cut-paper collage, name /
ingredient · ingredient); ref-05 (Greenhouse: text on stable backing fields). Transferred: structure and type roles.
Not copied: their art, their gold-leaf ink wash, their lettering.

## Files

round-17/: menu.html, menu.pdf (trim), menu-print-bleed.pdf (3.175 mm bleed + crop marks), preview-letter.png
(2550x3300), preview-phone.png (1170x5436), doc.json, layout.json, proposal.md.
Build: build17/build.py → render.py → finalize.py (build/ untouched as the round-16 baseline).
