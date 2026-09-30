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

## Round 2 of the KB rebuilds (G2-J2, 3-reviewer screening)
| Direction | critic | content | accuracy | combined | change |
|---|---|---|---|---|---|
| I2 Night Field | 73.1 | 75.6 | 67.6 | 72.1 | +6.7 |
| G2 Monument | 71.2 | 72.0 | 68.2 | 70.5 | +7.0 |
| H2 Sun & Furrow | 66.5 | 69.0 | 67.8 | 67.8 | +6.7 |
| J2 Horizon | 62.9 | 75.0 | 60.4 | 66.1 | -0.2 |

- Every gate passes on all four. The price-association failures from round 1 are fixed by inline prices.
- The round-17 best is still 74.1. I2 is closest at 72.1.
- Garnishes are verified against phg.recipe_versions (f06abb74 lime wheel, 9fb77eaa cocktail cherry, 14d45e57 lime coin, 7095fd3d orange peel).
- Remaining ceiling: the description criteria (8 and 12) sit at 40-61 everywhere.
  - The draft only has name-like text for 10 of the 14 non-cocktail descriptions: beer ABV, wine region and spirit brand/age are all missing.
  - This is a data gap, so we need Rob's venue facts. Design work can't fix it.
- Reviewer contradiction to note: round 1 penalised stubs ("Toasty"), and round 2 penalises the full draft text as a name echo.

## Round 3 of the KB rebuilds (G3-J3, 3-reviewer screening)
| Direction | critic | content | accuracy | combined | vs round 2 |
|---|---|---|---|---|---|
| J3 Horizon | 68.9 | 73.4 | 67.0 | 69.8 | +3.7 |
| I3 Night Field | 63.8 | 74.6 | 67.4 | 68.6 | -3.5 (regressed, revert to I2) |
| H3 Sun & Furrow | 68.2 | 73.2 | 63.6 | 68.3 | +0.5 |
| G3 Monument | 70.3 | 76.6 | 64.4 | 70.4 | -0.1 (flat, keep G2) |

Best checkpoint across the KB rebuilds is still I2 at 72.1. The round-17 legacy best is 74.1.

Plateau diagnosis:
1. The description criteria are stuck at 40-62, because 10 of the 14 source descriptions are name-echo sample text. The data comes from Rob.
2. Critics repeat the same point: the Mexico × Iowa fusion is "written in proposal.md, not visible". Programmatic vector art is hitting its craft ceiling next to Rob's raster references (craft_quality).
3. Column balancing by padding keeps creating dead islands.

## Round 4 (I4, J4)
| Direction | critic | content | accuracy | combined | vs prior |
|---|---|---|---|---|---|
| I4 Night Field | 71.2 | 76.8 | 66.0 | 71.3 | vs I2 72.1: -0.8 |
| J4 Horizon | 69.4 | 79.8 | 64.6 | 71.3 | vs J3 69.8: +1.5 |

All gates pass. The best checkpoint is still I2 at 72.1.

For four rounds the KB-rebuild directions have sat in a 68-72 band, so they have plateaued. The caps are the same every round:
1. Criterion 12 (description quality) auto-caps at 40-55. The spirit, beer and wine lines are name-echo sample text, and we need Rob's venue data to replace them.
2. Criteria 15 and 16 (concept and art direction) sit at 56-64. Critics say the art is "a competent copy of the ref panel", that it has flat vector with no materiality, and that the fusion is not visible. Reaching the reference craft needs raster art, and media.canva.com is blocked.
3. The remaining fixable issues are small: rag and orphans, margins, and column balance.

Recommendation: do not spend more rounds until Rob supplies the data or the art access. Another round of this kind is expected to gain about 1 point.

## Round 5 (I5, J5)
| Direction | critic | content | accuracy | combined | vs prior |
|---|---|---|---|---|---|
| I5 Night Field (loam + agave palette, soil line) | 80.4 | 76.2 | 64.8 | 73.8 | NEW BEST of rebuilds (I2 72.1) |
| J5 Horizon (true elevator, papel picado band, riso raster) | 71.4 | 75.4 | 64.4 | 70.4 | vs J4 71.3: -0.9 |

- First critic score over 80 (I5). All gates pass.
- The spirits wording from public.beverage_categories ("Blanco-class agave spirit · pour") was a mistake and gets reverted:
  - It reads as taxonomy language.
  - Those nodes have proposal_status=proposed.
  - In US label terms, "agave spirit" is the TTB class for spirits that are not tequila.
- Next moves:
  - I6: turn the loam into a real soil band with strata or furrows in place of the root fan; tighten the wordmark lock-up; ease the leaves off column 2; add plate texture.
  - J6: cut the papel picado into the elevator itself.

## Round 6 (I6, J6)
| Direction | critic | content | accuracy | combined | vs prior |
|---|---|---|---|---|---|
| I6 Night Field (loam band, plate tone) | 71.8 | 77.0 | 64.0 | 70.9 | vs I5 73.8: -2.9 |
| J6 Horizon (cut-paper elevator, wordmark on beam) | 74.2 | 75.4 | 62.8 | 70.8 | vs J5 70.4: +0.4 |

- Noise: I5 and I6 differ only in the soil band, yet the critic score moved from 80.4 to 71.8. A single-critic screen is noisy by about ±5 (critic_consensus_not_truth).
- Next: run the full 15-reviewer panel on I5, the best checkpoint, to get a reliable score before more design rounds.

## Full 15-reviewer panel on I5
- Critic: 73.2 (grid), 66.7 (type), 71.1 (palette), 74.5 (concept), 70.5 (phone). Mean 71.2.
- Content: 77.6 (prices), 74.6 (descriptions), 74.4 (flow), 73.4 (voice), 69.8 (missing data). Mean 74.0.
- Accuracy: 68.8 (trace), 67.6 (voice), 66.2 (venue fit), 61.2 (print), 61.8 (phone). Mean 65.1.
- Combined 70.1. The 3-reviewer screen said 73.8, so the screen overstated it by 3.7. All gates pass.
- Round 17 legacy was 74.1 (critic 74.0, content 77.8, accuracy 70.5). The KB rebuilds have not beaten it on the full panel yet.

Consolidated fixes for I7 (asked for by several reviewers):
- Design:
  - Remove the marginal leaf teeth (4/5 critics).
  - Make the Iowa soil a real engraved loam/furrow band holding about 1/3 of the art, drawn in the leaf grammar, not confetti.
  - Modulate the hatch.
  - Wordmark: either tie it to the soil line or change the face.
  - Separate the sub-line from the H3.
  - Resolve the axis: header over the text block, or narrow col 2.
  - Put every line on the 8 px baseline.
  - Balance the column ends.
  - Add one warm accent on the H2s.
  - Phone: the art should rise beside Wine, without the 93 px gap.
- Content:
  - Standard order: Cocktails > Beer & Cider > Wine > Spirits.
  - Restore the bilingual subheads from rounds 11–17 (Clásicos, De la Casa, De Barril, Sidra, Por Copa, Espumoso).
  - Spirits text: draft wording ("Blanco tequila pour" etc.), or the category names only.
  - Use the sourced serve facts: coupe for the Manhattan and Daiquiri, "over a large cube" for the Old Fashioned (recipe_versions), and "house demerara syrup".
  - Make the tasting-note rule consistent.
  - Fix the stale page title.
  - Put an item-by-item missing_ingredients table in proposal.md, including the Old Fashioned dairy allergen.

## Full 15-reviewer panel on I8
Critic 72.0/67.1/67.4/68.6/65.4 → 68.1 (phone critic FAILED environmental_legibility: 10 px reversed serve labels).
Content 73.6/74.0/73.6/75.2/73.2 → 73.9. Accuracy 64.4/60.2/61.2/63.2/62.0 → 62.2. Combined 68.1 (I5 panel 70.1; round-17 74.1).

Full-panel standings: round 17 74.1 > I5 70.1 > I8 68.1.
Findings:
- The KB rebuild family improved the reading layer: bilingual subheads, sourced serve facts and inline prices all got good content scores.
- Its code-drawn art has not beaten the round-17 base. Four soil attempts in a row read as sunburst, confetti, sea and gravel/water (craft ceiling without raster art).
- Accuracy is held at about 62 by name-echo descriptions (Rob's data gap), plus reviewers asking for Mexican items (mezcal, Mexican lager) that the draft does not have.
- Recommendation: stop the I-line art iterations.
  - Next: port the proven KB content wins onto the round-17 base (bilingual H2+H3, serve facts as one glass rule, one inline price rhythm, the missing-data table, a generic allergen line, 12 px+ labels).
  - Then run a full panel.
  - Raster art only after the Canva hosts are allowed.

## Full 15-reviewer panel on round 19 (r17 base + KB content wins)
- Critic: 67.7 grid / 70.3 type / 71.2 palette / 73.1 concept / 72.4 phone. Mean 70.9.
- Content: 78.8 prices / 80.2 descriptions / 76.0 flow / 77.8 voice / 72.4 missing data. Mean 77.0, the best content mean so far.
- Accuracy: 62.0 trace / 62.8 voice / 67.8 venue / 60.0 print / 58.8 phone. Mean 62.3.
- Combined 70.1.
- Three accuracy reviewers failed content_integrity over Junmai Ginjo. phg.menu_items has status='retired' for it (verified by query), so omitting it is correct. The failures are false positives. The next proposal must cite the retired status.

Round-20 fixes, requested by several reviewers:
- Prices inline, about 1 em after the text, same size as names or muted, no leaders.
- Item names in title case, not tracked caps.
- Bilingual heads at equal status: Spanish in italic, English in roman, same ink and weight.
- Agave and Brandy follow the pattern.
- Spirits: name + price only (no echo lines).
- "rye whiskey".
- "house demerara syrup" on both cocktails (the OF component role is House prep).
- Drop "draft" from the IPA line.
- Glass labels get their own quiet slot, not joined by "·".
- Margarita tasting note in the same voice.
- Balanced ingredient breaks.
- Art: torn-paper Iowa strata (loess bluffs or corn rows) under the agave.
- One grain treatment on all shapes (no speckle sun).
- Phone hero: its own crop with the torn edge and a footer.

## Round 20b full panel (2026-09-28)
critic 68.5 · content 74.6 · accuracy 66.2 · combined 69.8. 15/15 gates pass. r17 (74.1) remains best.
Consensus across reviewers (number of reviewers raising each):
- two price grammars (price after the name in cocktails and spirits, after the descriptor in beer and wine;
  price right-edge spread 136 pt): 15/15
- Fraunces italic 'l' reads as a long-s ('Cócteſes', 'Destiſados'); verified at full resolution: 6
- 'BRANDY · BRANDY' / 'DESTILADOS DE AGAVE' under 'Destilados' / 'SIDRA' under 'Cerveza y Sidra' redundancies: 12
- Old Fashioned 'aromatic bitters' widow with the separator lost at the break: 9
- beer and wine descriptors echo the name ('hop-forward IPA', 'dry red wine'): 10. They are the DB menu_description.
- lone italic sensory line (Margarita only) looks accidental: 6
- dead right third / H2 rules longer than the text: 5 (all critics)
- serve line (DM Sans tracked caps) is the same treatment as the H3s: 1
- prices in the same muted ink as descriptions: 2
- art reads as generic Southwest, and Iowa is not structural: 3 critics
- paperwork: proposal needs_input 13 and 21 pt notes are stale: 2
Round-21 plan:
- one item grammar everywhere: name + price / italic sensory line (beer and wine descriptors move there, sourced
  menu_description) / ingredients / garnish·glass
- WONK off; dedupe the H3s
- rebreak the Old Fashioned keeping the separator
- rules to the content measure
- serve line in Fraunces small caps
- prices a weight step up in agave green
- fix the paperwork
