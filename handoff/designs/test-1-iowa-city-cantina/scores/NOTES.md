# Scoring notes
- Rounds 2-3: original calibration (critic criteria 1-7, 10).
- From round 4 (Rob, 2026-09-28): Roger-Ebert-tough calibration + critic criterion 15 (Design concept). Scores are
  not comparable with rounds 2-3; round 4 sets the new baseline, and "must improve" applies from round 5 on.

## Round 10 (restart from round 8, option (b): equal 36 pt margins)
Combined 68.9 (critic 69.2, content 70.8, accuracy 66.6). Not an improvement over the round-8 best of 70.7.
What all three reviewer types agreed on:
- The El Cantarito face takes 64% of the cocktail card, which pushes the highest-margin items into the bottom third.
- The concept reads as coloured boxes, not a lotería tabla: no card numbers, no card proportions.
- La Botella and El Barril sit 2 pt off the 6 pt grid, and card 1's subhead space is 12.75 pt.
- There are three description voices, and the spirits have no description line.
- The Manhattan is missing "aromatic bitters", which is in the venue's own draft description.
- Brut Rosé's price has no label.
- proposal.md says Espumoso and Por copa, but the render prints Sparkling and By the Glass.
- Serve cues break across lines.
Round 11 builds from round 10 (the grid and margins are sound) with a bigger concept change: a real numbered lotería tabla.

## Round 11 (numbered lotería tabla, 2+2 grid, one description style)
Combined 71.4 (critic 75.2, content 74.7, accuracy 64.4). NEW BEST on the tough scale (the previous best was round 8 at 70.7).
Round 12 builds from round 11. Round-12 fixes:
- Remove the "glass / bottle TBC" note from the guest print.
- Fix the La Rosa verse to "ven que te quiero ahora".
- Change the DRAFT & CIDER subhead so it makes no draft claim.
- Rewrite the spirit lines so they don't repeat the name.
- Put every serve cue on its own line.
- Change "rye whiskey" to "rye".
- Change "over one large cube" to "over a large cube".
- Remove the agave blue so the palette has 4 hues.
- Put the faces on one template; the La Botella figure matches the others.
- Line up the lower cards across columns and widen the gutter to 18 pt.
- Fix the masthead overlap.
- Order: Margarita first, agave card top-right.
- Card numbers are distinct from prices.
- Use Spanish-first subheads.

## Round 12 (verse fixed, TBC removed, spirits name-only, beer/spirits cards swapped)
Combined 71.434, which ties round 11 exactly (critic 73.0, content 72.1, accuracy 69.2). Not an improvement.
- Accuracy rose from 64.4 to 69.2 because the "TBC" proof note came off the guest print.
- Content and critic fell because of the name-only spirits and 84 pt of empty space in El Barril.
Coordinator finding: build/draft_doc.json DOES have a "Draft" subhead for all three beers, a "By the Glass" subhead for Malbec and Pinot Grigio, and a "Sparkling" subhead for Brut Rosé.
- The round-11 reviewer's claim that "draft" was unsupported was wrong.
- These are sourced labels and answer part of criterion 14.
Round 13 builds from round 12:
- Restore the draft spirit lines.
- Restore the sourced Draft and By the Glass subheads, written bilingually.
- Put the agave card back at top right.
- Use one bilingual pattern.

## Round 13 (descriptions restored, sourced Draft/By the Glass subheads, split column breaks)
Combined 71.344 (critic 73.7, content 73.0, accuracy 67.3). Just under the 71.434 best (rounds 11 and 12).
Plateau: rounds 11-13 all land at 71.3-71.4.
Every accuracy and content reviewer names the same cap: criteria 8 and 12 cannot pass about 70 without venue data.
- Beer: brewery and ABV.
- Wine: region and producer.
- Spirits: brand, age and pour size.
- Brut Rosé: glass or bottle.
- Also: a Mexican lager, mezcal, agua fresca, and the venue name.
The sample draft (ddc4bb5b) has none of these, and we must not invent them.
Round 14 fixes the design-side items:
- Lock the 2x2 grid with columns that end level.
- Remove the doubled Agave/Brandy gloss.
- Old Fashioned wording.
- Spirits: a card-level "straight pours" note instead of lines that repeat the name.
- Bigger name bands.
- Phone figure-strip tabs.

## Round 14 (locked 2x2 tabla, name bands, marigold La Botella, phone chip tabs)
Combined 72.305 (critic 74.0, content 73.3, accuracy 69.7). NEW BEST (the previous best was 71.434).
Round-15 fixes that reviewers agree on:
- Use one item pitch on every card; drop the stretched 24/6 pt padding.
- Take up row-height differences in the face, the band, or real content.
- Put "Straight pours." in the band so the first subheads align.
- Price colour on La Botella: deep ochre, 4.5:1 or better.
- Card numbers no larger than the prices on the phone.
- Put the Manhattan public_components aromatic-bitters=false conflict on the needs_input list, since it is unflagged.
- Use the Margarita's "tequila blanco" word order.
- Add a "copa" price label under By the Glass.
- One description measure per card.
- Consistent SPANISH · English subheads.

## Round 15 (one item pitch, faces absorb row difference, bilingual subheads, copa labels)
Combined 72.597 (critic 72.9, content 73.5, accuracy 71.4). NEW BEST (just above 72.305).
- Accuracy rose to 71.4, its highest yet.
- Critic fell because the name bands are offset inside each row: the grid critic scored 70.6 and header criterion 2 got 58.

Round 16:
- Align the name bands in each row, with faces equal per row.
- Keep one item pitch.
- Fill the short card's foot with a card seal or cantor line, not decoration padding.
- Manhattan follows the draft (hide the aromatic bitters) pending the venue's answer.
- Subheads become AGAVE · Agave and BRANDY · Brandy.
- Band gloss "Spirits".
- Spirit and wine and beer lines built from name/draft facts: "Malbec, dry red", "Pale lager · draft".
- Cocktail leads from method rows.
- Put doc.json section order in line with print.
- Try agave top-right.

## Round 16 (shared band line, card foot, method leads, Manhattan follows the draft)
Combined 72.399 (critic 73.6, content 74.0, accuracy 69.6). Not above round 15 (72.597), so round 15 stays best.
- Aligning the bands raised the critic score.
- Accuracy fell. The "poured straight" serve on the spirits has no source (the recipe fields are null), and the name-echo tags ("Malbec · dry red") auto-fail criterion 12.
- The El Barril foot reads as filler.
- 13 of the 15 reviews were re-run after a usage-limit stop (06:00 UTC reset).
Paused after round 16: Rob has loaded the phg_design knowledge base (938 records) and new reference concepts. The loop resumes once the designer and critics have been updated from it.

## Round 17 (new editorial direction "Sun Behind the Page", updated KB-based scorecard)
Combined 74.087: critic 74.0 (average of 1-7, 10, 15, 16), content 77.8, accuracy 70.5. NEW BEST (was 72.597).
All hard gates PASS on all 15 reviews.
Consensus fixes for round 18:
- (a) Replace the Bistro-derived structure with a concept only this venue could own: agave country meets the Iowa prairie at dusk, carried through the section structure.
- (b) Remove both rail taglines ("GOOD DRINKS GOOD COMPANY" copies ref-01).
- (c) Drop the no-name-echo rule and print the draft's short phrases ("toasty amber lager", "dry sparkling cider"). Spirits get no description rather than "pour".
- (d) Restore "bright and citrus-forward" on the Margarita.
- (e) Split the header and item-name hierarchy.
- (f) Agave spirits prominent; a small set of Spanish subheads back.
- (g) Equal lower columns on one baseline grid.
- (h) Phone: never start a line with a separator, a shorter hero, and a closing art band.
- (i) Give Cider its own header again.
- (j) Machine-readable meta.missing per item.
- (k) Prices in a palette colour with stronger leaders.

## KB rebuild screening (explore G-J, 1 critic + 1 content + 1 accuracy each)
G Monument 63.5 (60.4/70.8/59.4) · H Sun & Terrace 61.1 (57.0/65.6/60.6) · I Night Field 65.4 (65.4/69.2/61.6) · J Horizon 66.3 (58.0/75.4/65.4).
All are below the round-17 best of 74.1. Price-association gate fails on G, H and I. The unanimous causes are:
1. Remote prices. My brief banned leaders, and the price track was sized to the longest name, so 10-13 of 14 rows exceed 40% eye travel.
2. Thin descriptions. My "no name echo" rule cut the draft down to one-word stubs and blank spirits. This is the same mistake as round 18.
3. Menus copy the reference panels and are not ownable. They fail the substitution test and have no Mexico x Iowa City idea.
4. Venue order. The Manhattan leads, and agave sits below wine; H dropped the Agave sub head.
5. The "Good drinks / Good people" tagline is costume.
6. Garnishes from recipe_versions are unused. "agave" is ambiguous (should be agave syrup), and demerara/demerara syrup is inconsistent.
Data drift: phg.menu_items has Junmai Ginjo (12), which is not in draft rev 3. Flagged to Rob.
