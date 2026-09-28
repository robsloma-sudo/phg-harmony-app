# TEST-1 round 20b — full 15-reviewer panel (2026-09-28)

| # | type | lens | per-criterion scores | avg | gates |
|---|---|---|---|---|---|
| 1 | critic | grid, alignment, margins and spacing, measured from layout.json | c1=72 c2=68 c3=64 c4=74 c5=70 c6=61 c7=70 c10=74 c15=67 c16=70 | **69.0** | all pass |
| 2 | critic | typography and hierarchy, including the display wordmark and the bilin | c1=74 c2=64 c3=64 c4=79 c5=73 c6=58 c7=72 c10=75 c15=73 c16=75 | **70.7** | all pass |
| 3 | critic | palette, contrast over the art, price and number styling | c1=74 c2=69 c3=55 c4=66 c5=72 c6=63 c7=71 c10=71 c15=63 c16=67 | **67.1** | all pass |
| 4 | critic | design concept and art direction (15, 16) against ref-02, ref-solstice | c1=72 c2=64 c3=63 c4=74 c5=72 c6=60 c7=69 c10=71 c15=66 c16=68 | **67.9** | all pass |
| 5 | critic | phone version (preview-phone.png) and print-phone coherence | c1=72 c2=68 c3=55 c4=73 c5=70 c6=62 c7=71 c10=71 c15=67 c16=69 | **67.8** | all pass |
| 6 | content | every item and price vs build/draft_doc.json (rev 3) | c3=68 c5=74 c8=66 c9=97 c10=76 | **76.2** | all pass |
| 7 | content | ingredient names and description completeness | c3=66 c5=72 c8=62 c9=100 c10=70 | **74.0** | all pass |
| 8 | content | flow and reading path for a Mexican restaurant and cocktail bar in Iow | c3=64 c5=70 c8=66 c9=100 c10=70 | **74.0** | all pass |
| 9 | content | voice and consistency of descriptions, bilingual headings, venue copy, | c3=68 c5=72 c8=64 c9=100 c10=71 | **75.0** | all pass |
| 10 | content | missing data: how the known gaps are flagged, and whether anything was | c3=66 c5=72 c8=63 c9=100 c10=69 | **74.0** | all pass |
| 11 | accuracy | Ingredient, garnish, glassware and heading traceability (build/draft_d | c10=72 c11=80 c12=58 c13=70 c14=64 | **68.8** | all pass |
| 12 | accuracy | description quality and one guest-facing voice (TEST-1 round 20b, Mexi | c10=68 c11=78 c12=40 c13=62 c14=66 | **62.8** | all pass |
| 13 | accuracy | Venue fit for a Mexican restaurant and cocktail bar in Iowa City, IA:  | c10=72 c11=78 c12=55 c13=62 c14=68 | **67.0** | all pass |
| 14 | accuracy | How descriptions and prices sit together in preview-letter.png (price- | c10=66 c11=76 c12=56 c13=62 c14=63 | **64.6** | all pass |
| 15 | accuracy | How descriptions and prices sit together on the phone preview (preview | c10=72 c11=80 c12=58 c13=58 c14=70 | **67.6** | all pass |

| type | mean | vs R19 | vs r17 (best) |
|---|---|---|---|
| critic | 68.5 | 70.9 | 74.0 |
| content | 74.6 | 77.0 | 77.8 |
| accuracy | 66.2 | 62.3 | 70.5 |
| **combined** | **69.8** | 70.1 | **74.1** |

Hard gates: 15/15 pass. R19 had 3 content_integrity fails, all false positives over Junmai Ginjo.
Decision: r17 stays the best checkpoint. 20b does not replace it. Keep 20b's content fixes (item stack, role order, garnish·glass line).
