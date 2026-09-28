# K1v2 HILERAS: 15-reviewer panel (2026-09-28)

Averages: design critic **62.3**, content **77.9**, accuracy **68.9**, overall 69.7. Gate fails: 2. Round 17's 74.1 is still the best result, and no reviewer type reached the 80 target.

| # | type | lens | avg | criterion scores | gates |
|---|---|---|---|---|---|
| 1 | critic | grid, alignment, margins and spacing (measured from _measure.json fron | 61.8 | 1:40 2:40 3:74 4:72 5:70 6:40 7:68 10:70 15:76 16:68 | pass |
| 2 | design_critic | typography and hierarchy: wordmark, section heads, item stack, numeral | 56.5 | 1:40 2:40 3:66 4:64 5:65 6:40 7:60 10:64 15:68 16:58 | pass |
| 3 | design_critic | palette, contrast over the art, price and number styling | 63.5 | 1:40 2:72 3:70 4:66 5:70 6:55 7:64 10:68 15:70 16:60 | pass |
| 4 | design_critic | design concept and art direction (15, 16), full critic set scored | 63.3 | 1:40 2:74 3:76 4:72 5:70 6:40 7:64 10:70 15:67 16:60 | pass |
| 5 | critic | Phone version (preview-phone-1..5) and print/phone coherence; front/ba | 66.5 | 1:72 2:66 3:68 4:72 5:63 6:62 7:67 10:66 15:68 16:61 | pass |
| 6 | content_reviewer | every item and price against expanded-v2/manifest.json: single prices, | 76.8 | 3:76 5:72 8:70 9:88 10:78 | pass |
| 7 | content_reviewer | ingredient names, tasting lines, brewery/producer lines, description c | 76.8 | 3:78 5:72 8:64 9:94 10:76 | pass |
| 8 | content_reviewer | flow and reading path, front and back, Mexican restaurant and cocktail | 79.8 | 3:80 5:72 8:74 9:95 10:78 | pass |
| 9 | content_reviewer | voice and consistency of descriptions; bilingual headings and venue co | 77.6 | 3:80 5:72 8:68 9:92 10:76 | pass |
| 10 | content_reviewer | missing data: how proposed rows, brewery/producer proposals, the pour- | 78.4 | 3:80 5:72 8:71 9:93 10:76 | pass |
| 11 | accuracy | Traced every printed fact (ingredients, garnish, glass, NOM, region, b | 67.4 | 10:70 11:66 12:60 13:72 14:69 | FAIL content_integrity |
| 12 | accuracy | description quality and one guest-facing voice (K1v2 HILERAS, /home/us | 67.2 | 10:70 11:70 12:48 13:76 14:72 | FAIL menu_item_association |
| 13 | accuracy | Venue fit for a Mexican restaurant and cocktail bar in Iowa City, IA ( | 70.8 | 10:72 11:74 12:62 13:74 14:72 | pass |
| 14 | accuracy | How descriptions and prices sit together on the print PNGs: inline pri | 69.8 | 10:72 11:74 12:57 13:76 14:70 | pass |
| 15 | accuracy | How descriptions and prices sit together on the phone previews (previe | 69.2 | 10:74 11:70 12:57 13:78 14:67 | pass |

## Top problems (agreed by several reviewers)
1. **Content integrity fail:** the approved Manhattan is missing aromatic bitters (rv 9fb77eaa and menu_description both list them).
2. **Association fail:** the Vuelo Reserva line 'Highland oak, lowland agave' is reversed against its pours (Fortaleza is lowland, El Tesoro is highland).
3. **Repeated class lines:** the 33 spirit pours carry 4 class-level tasting lines stamped on every row. Wine and beer lines are taxonomy ('Dry red wine').
4. **Grid breaks** (the design critics cap criteria 1 and 6 at 40):
   - Cocktail names drift up to 4.9 mm off their column edges.
   - Level-1 heads use two sizes across the pages.
   - Item names come in four sizes, and flights are set smaller than beer.
   - The front left and right margins differ by 7.4 mm.
5. **Back-office wording printed for guests:** 'recipe to confirm', 'beer ABV to confirm', and the pour header ring.
6. **Maestro Dobel Diamante** is a cristalino but is shown on the añejo oak bar. Cognac VSOP sits under 'Casa'. Print and phone use different section orders.
7. **The concept reads as a stripe or header**, not as a governing structure (critics score criteria 15 and 16 at 58–68). The art medium is the ceiling; see the status note to Rob.
