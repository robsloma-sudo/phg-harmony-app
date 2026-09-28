# TEST-1 round 20: "Sun Behind the Page, landed in Iowa" (proposal v20)

Base: round 19. Its full panel scored combined 70.1: critic 70.9, content 77.0 (the best content mean so far) and accuracy
62.3. The best overall full panel is still round 17 at 74.1. This round applies the "Round-20 fixes" from
scores/NOTES.md and the Coordinator's round-20 brief. Built in build20/ (a copy of build19); round-19 and build19 are
untouched.

## Creative thesis

**A late gold sun sets behind a torn page, and an agave rises out of Iowa's contour-ploughed fields. The menu is one
hand-cut paper collage, in which Mexico's plant grows from Iowa's ground, while the drinks sit in calm, bilingual
editorial type.**

- **Concept words (6):** torn paper · setting sun · agave · Iowa loam · contour rows · editorial calm
- **The fusion lives in the image, not in labels.** The agave (Mexico) grows from strip-cropped contour rows and loess
  bluffs (Iowa), cut from the same paper with the same tear. Substitution test: a generic cantina gets desert and
  cactus; a generic Iowa bar gets no agave. This picture only fits a cantina in Iowa City.
- **Avoid-list:** lotería, papel picado, sombreros, cacti clip-art, skulls, serape stripes; neon or "fiesta" colour; any
  lettering in the art; trademarked worlds; fake grunge; a second grain or texture; gold anywhere but the sun; boxes;
  leaders or price ornaments; taglines or kickers; tracked caps on anything but the H3 labels and the wordmark.

**Device → thesis trace**

| Device | Traces to |
|---|---|
| Torn page edge (cream fibre rim, one down-left shadow) | torn paper; the page is laid over the scene, and the art stays in the rail |
| Gold sun disc, cropped by the torn edge, with no speckle | setting sun; the only gold on the page |
| Agave rosette (round-17 two-tone folded leaves, tips leaning toward the list) | agave; its gaze vector points at the content |
| Two torn loess bluffs (rounded crests, terracotta) | Iowa: the Loess Hills ridgeline; dusk warmth |
| Five contour strip rows (crop green and loam brown) that bow down around the agave and frame it | Iowa loam and contour ploughing; they replace the flat dark ground slab |
| One paper-fibre grain on every shape (55% in the rail, 10% on the reading paper) | hand-cut paper; one grain treatment; low contrast near text |
| Vertical CANTINA with the rail line on the same axis | editorial calm; the name stands at the seam |
| H2 rules | reading path; they mark the right edge of the reading column |
| Terracotta H3 labels (italic Spanish · roman English) | dusk warmth; one accent in the type |

Illustration grammar (one, from round 17): flat cut-paper planes, torn edges with a cream fibre rim, one light from the
top right, no outlines and no gradients inside shapes except the sky wash and the sun's soft radial light.

## Revision hypothesis and best-so-far

Hypothesis: the round-19 critic score (70.9) and accuracy score (62.3) were held down by five things:
- dotted leaders and loud prices (12.5 pt 600, heavier than the names);
- tracked-caps names;
- Spanish demoted as a lighter half of each head;
- stubs that echo the name (spirits);
- art that told only the Mexican half of the story.

The fix is inline muted prices, title-case names, equal-status bilingual heads, name-only spirits and Iowa strata under
the agave. That should lift critic criteria 1-3, 7, 15 and 16, and accuracy criteria 12 and 13, without losing round 19's
content gains (77.0).

Kept at best-so-far: the round-17/19 page zones, rail and wordmark; all 14 prices exact; every sourced fact; the missing-data table and allergen line.

## What changed from round 19 (by Coordinator item)

1. **No leaders. Prices inline, 1 em after the last word of their row**, at the name size (Fraunces 500, 11 pt, tabular)
   in muted ink #5A4B3F. Prices no longer outrank names (names are Fraunces 600, 11 pt, ink #1D1815). Measured eye travel,
   from the end of the row's text to the price, as a fraction of the column: **0.037 on every letter row and 0.047 on
   every phone row** (limit 0.40).
2. **Item names in title case**, Fraunces 600, 11 pt, no tracking. Tracked caps remain only on the H3 labels and the
   wordmark (and the vertical rail line, which is part of the wordmark lock-up).
3. **Bilingual heads at equal status.** Spanish italic and English roman, same ink, same weight, joined by " · ".
   - H2: Fraunces 600, 17 pt (1.55x the name), 21 pt line.
   - H3: DM Sans 700, 9 pt (12 px), tracked .16em, terracotta.
   - "*Destilados de agave* · Agave" and "*Brandy* · Brandy" now follow the same pattern.
   - Phone: H2s stack Spanish over English, with no "·".
4. **Descriptions.**
   - **Spirits** print name and price only.
   - **Manhattan:** "rye whiskey" (draft component 'Rye Whiskey', role Base spirit); aromatic bitters stay hidden
     (public_components).
   - **"house demerara syrup" on both the Daiquiri and the Old Fashioned.** Old Fashioned: draft component
     'Demerara Syrup', kind `prep`, role **"House prep / sweetener"**. Daiquiri: kind `prep`, role "House prep", notes
     "House 1:1 demerara syrup by weight." (build/draft_doc.json, items beta_old_fashioned and beta_daiquiri).
   - **IPA:** "hop-forward IPA".
   - **Margarita:** "bright, citrus-forward" in the lower-case voice, before the glass.
   - **Beer, cider and wine** descriptors sit on **one tab stop** (x = 382 pt letter, 144 px phone), in Fraunces 400
     at 10.5 pt, #40352D, lighter than the names.
5. **Glass in its own quiet slot.** A thin space plus .25 em, then DM Sans 600 caps at 9 pt (12 px) in the ingredient
   colour, with no "·". The .25 em is added to the thin space because a bare thin space made "citrus-forward ROCKS" read
   as one phrase.

   Ingredient breaks are set by hand. On letter, line 1 is always the longer line, and no line starts or ends with a
   separator (each break replaces its "·"):

   | Item | Letter lines |
   |---|---|
   | Margarita | "tequila blanco · fresh lime · orange liqueur · agave syrup" / "lime wheel · bright, citrus-forward ROCKS" |
   | Manhattan | one line |
   | Old Fashioned | "brown butter-washed bourbon · house demerara syrup" / "aromatic bitters · orange peel ROCKS" |
   | Daiquiri | "white rum · fresh lime · house demerara syrup" / "lime coin COUPE" |

   The phone measure (342 px at 15 px) needs its own breaks: Margarita on 3 lines, Manhattan 2, Old Fashioned 3,
   Daiquiri 2. Line 1 is the longest on all of them except the Old Fashioned, where "brown butter-washed bourbon" cannot
   carry more at 15 px. Still, no phone line starts or ends with a separator.
6. **One 7 pt baseline unit (letter).**
   - Every line box is 14 pt (names, ingredient lines, H3, allergen) or 21 pt (H2).
   - The H2 block is 28 pt including the rule, plus 7 pt below. Item gap 7 pt, sub gap 7 pt, section gap 21 pt.
   - The menu top is 31.88 pt, so the **first H2 cap line is at 36.0 pt, level with the CANTINA ink top (36.0 pt)**.
   - **CANTINA and the vertical rail line share one axis**: ink centres at 223.8 and 224.0 pt.
   - The one exception: the allergen line sits on the last grid line, lifted 1.7 pt so its italic descenders stay inside
     the 36 pt safe inset.
7. **Art: Iowa strata in round 17's torn-paper method.**
   - Two rounded loess bluffs behind the agave.
   - Five contour strip rows in front: crop green alternating with desaturated Iowa loam. They bow down around the agave
     and rise toward both edges, so the field frames the plant. This tears back the flat dark slab.
   - The sun's coarse gold speckle is removed. A soft radial gold is left under the same fine paper-fibre grain that
     covers every shape.
8. **Phone.**
   - Its own 390x416 hero: the full sun disc, loess bluffs, the rosette rising out of the contour rows, and a torn cream
     seam into the text.
   - One-row items stay on one line with the inline price.
   - Stacked bilingual H2s. A 96 px torn-edge footer where the page tears open onto the contour rows.
   - **All 49 measured row tops are on the 8 px grid** (page 2184 px = 273 x 8). Labels are at least 12 px.

## Restraint pass (scorecard 1c), with before and after numbers

Element inventory for the round-20 draft (first render, before subtraction): 19 elements.
1. torn page edge
2. gold sun disc
3. sun speckle grain
4. agave rosette
5. back loess bluff
6. front loess bluff
7-13. seven contour strips (four crop, three terracotta soil)
14. paper-fibre grain (rail and reading paper)
15. sky wash
16. vertical wordmark
17. vertical rail line
18. H2 rules
19. dotted leaders (inherited from round 19)

Also counted: the terracotta H3 colour (type accent, not counted as an element).

**Tested: 5 of 19 (26%). Removed for good: 4 (21%).**
- Dotted leaders (19). The inline price at 1 em makes them unnecessary; eye travel went from up to 0.68 to 0.037.
- Sun speckle (3). It was a second grain treatment.
- Two of the seven contour strips (12, 13). The three saturated terracotta soil strips became two desaturated loam strips
  (#5E4636, #4A372B), so the terracotta now belongs to the bluffs alone and the field reads as Iowa soil, not as stripes.
- Tested and returned: the reading-side paper grain (part of 14). Rendered without it, the reading paper turned flat
  digital cream, and the torn edge no longer read as two sheets of the same stock. That loses the one-grain materiality,
  so it came back.

Measured with `handoff/designs/tools/visual_tests.py` on the letter render:

| Metric | Round 19 | Round 20 before subtraction (7 strips) | **Round 20 final** |
|---|---|---|---|
| accent area % (target ≤ 8) | 6.49 | 10.26 | **7.56** |
| squint salient regions | 9 | 8 | **8** |
| primary area % | 13.58 | 16.79 | **16.21** |
| primary : secondary | 56.7 | 68.5 | **66.1** |
| ground luminance | 0.853 | 0.861 | **0.861** |
| value range p5-p95 | 0.258-0.909 | 0.275-0.908 | **0.273-0.908** |
| visual centroid | (0.273, 0.635) | (0.265, 0.618) | **(0.266, 0.622)** |

Reading: the rail is more clearly the one dominant region (66x the next region, against 57x in round 19), and there is one
fewer competing region. The accent area is back under 8% after the subtraction; the bluffs were also lowered 15%.

## Layout geometry (full element list with x/y/w/h in pt and mm: layout.json)

- **Page:** US letter, 612 x 792 pt, margins 36 pt (12.7 mm), art bleed 9 pt (3.175 mm) on all sides.
- **Zones:**
  - art rail x -9 to about 158 pt (the torn edge wanders 150-166);
  - wordmark ink 188.7-258.8 pt (axis 224);
  - reading column 282-576 pt (294 pt), single column;
  - one-row tab stop at 382 pt.
- **Vertical positions:**

  | Element | y (pt, line box) |
  |---|---|
  | H2 Cócteles | 31.88 (cap line 36.0) |
  | H3 Clásicos | 67.6 |
  | H3 De la Casa | 165.6 |
  | H2 Cerveza y Sidra | 290.9 |
  | H3 De Barril | 326.6 |
  | H3 Sidra | 403.6 |
  | H2 Vino | 451.8 |
  | H3 Por Copa | 487.6 |
  | H3 Espumosos | 543.5 |
  | H2 Destilados | 591.8 |
  | H3 Destilados de agave | 627.5 |
  | H3 Brandy | 683.5 |
  | allergen line | 744.9 |

  The vertical rail line starts at 503.7 and ends 36 pt from the bottom.
- **Type:**

  | Role | Setting |
  |---|---|
  | CANTINA | Fraunces 96 pt vertical (opsz 144, weight 380, .075em) |
  | H2 | Fraunces 600, 17/21 pt, italic Spanish · roman English |
  | H3 | DM Sans 700, 9/14 pt, .16em caps, italic Spanish · roman English, #9A3B22 |
  | Names | Fraunces 600, 11/14 pt, title case |
  | Ingredient and descriptor lines | Fraunces 400, 10.5/14 pt, #40352D |
  | Glass | DM Sans 600, 9 pt caps, #40352D |
  | Prices | Fraunces 500, 11 pt, tabular, #5A4B3F, no currency sign |
  | Allergen line | Fraunces italic 9.5 pt, #4F4238 |

- **Palette:**
  - paper #F2E9D6, ink #1D1815;
  - terracotta #9A3B22 (H3), muted #5A4B3F and #40352D;
  - sky #F1DEC2 → #CF7F55, gold (sun only) #C38F34-#E2BC62;
  - bluffs #B5532F and #7C3322;
  - agave #244A3E-#56866F;
  - contour strips #27463A, #5E4636, #1D382E, #4A372B, #132720.
- **Phone:**
  - 390 CSS px at 3x = 1170 px; 24 px margins;
  - lines 24 px (H2 32 px); gaps 16, 24 and 40 px;
  - hero 416 px, footer 96 px, tab stop 144 px.

## Hard gates (measured; layout.json → measured_checks)

| Gate | Result | Evidence |
|---|---|---|
| accessibility (4.5:1 at the worst pixel) | **pass** | Letter minimum by role: subheader 5.19, price 6.26, legal 7.26, rail line 7.59, description 8.83, glass 9.00, header 13.15, name 13.15, title 13.06. Phone minimum 5.76. Method: a text-free render at 300 dpi; each line's ink box plus 2 px; every background pixel checked. |
| menu_item_association | **pass** | Every price is on its name row, 1 em after the last word; maximum eye travel 0.037 (letter) and 0.047 (phone); there are no leaders. Name left edges spread 0 pt. |
| legibility / environmental_legibility | **pass** | At 1 m: names and prices 9.1′ cap height, ingredient lines 6.37′ x-height, H3 and glass 7.28′, H2 14.6′. No reversed small text. No metallic ink on text. Phone minimum 12 px. |
| content_integrity | **pass (open questions below)** | Prices match 14/14 in the doc and in print, and names are unchanged. No taglines. Every printed word traces to the draft, recipe_versions (log_id 248) or the Coordinator's label strings. Spirits print no description on purpose (`every_item_has_description` is false for those three only). **Junmai Ginjo is omitted because phg.menu_items has it as status='retired'** (item 57617f46-50f6-48f3-943e-a3a49a47ee4b, menu_price 12, project ddc4bb5b; verified through the read-only gateway, **log_id 258**). It is also absent from draft rev 3, so the omission is correct and is not a dropped item. |
| margins and bleed | **pass** | Text ink: top 12.70 mm, bottom 12.62 mm. The right edge of the reading column is set by the H2 rules at 576 pt (36 pt); text lines end short of it because prices are inline. Left: the full-bleed art rail. All text sits inside the 36 pt safe inset. The art box runs 3.175 mm past trim; menu-print-bleed.pdf has the bleed and crop marks. |

## Copy table (every printed word and its source)

| Section / sub | Item | Price | Printed | Source |
|---|---|---|---|---|
| Cócteles / Clásicos | Margarita | 15 | tequila blanco · fresh lime · orange liqueur · agave syrup / lime wheel · bright, citrus-forward ROCKS | draft desc 'Tequila blanco, lime, orange liqueur, agave. Bright and citrus-forward.'; components 'Fresh Lime Juice', 'Agave Syrup'; rv f06abb74 garnish 'Lime wheel', glassware 'Rocks' |
| Cócteles / Clásicos | Manhattan | 15 | rye whiskey · sweet vermouth · cocktail cherry COUPE | components 'Rye Whiskey', 'Sweet Vermouth', 'Cocktail Cherry'; bitters hidden (public_components); rv 9fb77eaa 'Coupe' |
| Cócteles / De la Casa | Brown Butter Old Fashioned | 16 | brown butter-washed bourbon · house demerara syrup / aromatic bitters · orange peel ROCKS | components 'Brown Butter-Washed Bourbon', 'Demerara Syrup' (prep, role 'House prep / sweetener'), 'Aromatic Bitters'; rv 7095fd3d garnish 'Orange peel', 'Rocks' |
| Cócteles / De la Casa | House Daiquiri | 14 | white rum · fresh lime · house demerara syrup / lime coin COUPE | draft desc 'White rum, lime, and house demerara syrup.'; 'Demerara Syrup' (prep, 'House prep'); rv 14d45e57 'Lime coin', 'Coupe' |
| Cerveza y Sidra / De Barril | Czech Pilsner | 7 | crisp pale lager | draft desc 'Crisp pale lager.' |
| Cerveza y Sidra / De Barril | Dry-Hopped IPA | 8 | hop-forward IPA | draft desc 'Hop-forward draft IPA.' ('draft' is carried by the De Barril · Draft label) |
| Cerveza y Sidra / De Barril | Amber Lager | 7 | toasty amber lager | draft desc 'Toasty amber lager.' |
| Cerveza y Sidra / Sidra | Dry Cider | 8 | dry sparkling cider | draft desc 'Dry sparkling cider.' |
| Vino / Por Copa | Malbec | 12 | dry red wine | draft desc 'Dry red wine.' |
| Vino / Por Copa | Pinot Grigio | 11 | dry white wine | draft desc 'Dry white wine.' |
| Vino / Espumosos | Brut Rosé | 13 | dry sparkling rosé | draft desc 'Dry sparkling rosé.' |
| Destilados / Destilados de agave | Blanco Tequila | 12 | (name and price only) | draft desc 'Blanco tequila pour.' only repeats the name |
| Destilados / Destilados de agave | Añejo Tequila | 16 | (name and price only) | same |
| Destilados / Brandy | Cognac VSOP | 18 | (name and price only) | same |
| (foot) | — | — | Please tell your server about any allergies. | generic guest line; no item claim |

Notes:
- **Cider sits under Beer.** `sec_cider` stays its own section in doc.json (renamed "Sidra · Cider",
  `meta.printed_under = "sec_beer"`), so ids and links survive.
- **Order** is the standard Cocktails → Beer & Cider → Wine → Spirits.

## missing_ingredients, item by item (also in doc.json → item.meta.missing)

| Item | Missing (never invented) | needs_input |
|---|---|---|
| Czech Pilsner, Dry-Hopped IPA, Amber Lager | brewery · ABV · pour size | 2 |
| Dry Cider | producer · ABV · format (draft / can / bottle) | 3 |
| Malbec, Pinot Grigio | producer · region · vintage · pour size | 4 |
| Brut Rosé | producer · region · vintage · **glass or bottle?** (the price prints unlabelled) | 4, 5 |
| Blanco Tequila, Añejo Tequila | brand · age statement · pour size (the line stays name-only until supplied) | 6 |
| Cognac VSOP | brand · pour size | 6 |
| Manhattan | display of aromatic bitters (hidden per public_components; the venue's own description lists them) | **11** |
| Brown Butter Old Fashioned | **dairy allergen confirmation**; only the generic allergen line prints until then | 1 |
| Margarita, House Daiquiri | none | — |

## Flags and needs_input (via the Coordinator)

needs_input = true. risk_flags: missing_ingredients, allergen_unconfirmed, price_label_unknown.
1. Old Fashioned dairy allergen: confirm, and give the wording.
2. Beer: brewery, ABV and pour size.
3. Cider: producer, ABV and format.
4. Wine: producer, region, vintage and pour.
5. Brut Rosé: glass or bottle?
6. Spirits: brand, age and pour.
7. Cantina gaps (asked, not added): Mexican lager, mezcal, agua fresca?
8. Venue name (the draft title is "Bar menu").
9. **Junmai Ginjo: status='retired' in phg.menu_items (log_id 258), so it is omitted. No action is needed unless the
   venue reactivates it.**
10. *(retired)*
11. Manhattan aromatic bitters: show them or keep them hidden?
12. *(retired)*

## References

- **Library (`menu_visual_documents.id`):**
  - 572 (Coa Cantina, Iowa City: local price band, agave emphasis);
  - 7923 (Coa Cantina, Des Moines: compact cocktail-led list);
  - 4969 (Blue Agave, Iowa: Classic / House tiers);
  - 208 (Alta Calidad: pour size in the header once supplied);
  - 2585 (La Buena Vida: plain Spanish/English headers).
- **Quality bar:**
  - ref-01 (Bistro): vertical wordmark, art rail, one-row beer lines, inline short-measure prices.
  - ref-04 (Solstice): sun disc, cut-paper collage, "name / ingredient · ingredient".

  Structure and type roles are borrowed from these; their art and lettering are not.
- **Gateway calls:** log_id 248 (recipe_versions glassware and garnish), log_id 258 (Junmai Ginjo status).

## Files

round-20/:
- menu.html
- menu.pdf (trim)
- menu-print-bleed.pdf (3.175 mm bleed and crop marks)
- preview-letter.png (2550 x 3300, 300 dpi, not downscaled)
- preview-phone.png (1170 x 6552)
- doc.json
- layout.json
- proposal.md

Build: build20/build.py → render.py → finalize.py.
