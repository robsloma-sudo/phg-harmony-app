# TEST-1 explore-K1v2: HILERAS v2 (the field carries the menu)

**Thesis.** Iowa corn and Jalisco agave are both row crops. The menu is one field seen from the air, and every drink is planted in its row.

**Content.** Built on `expanded-v2/manifest.json` (sha256 prefix `fa881aa9ab7ebc11`). Every price is real and whole-dollar, so there is no TBC anywhere. There are 33 spirit pours, each with 1 oz / 1½ oz / 2 oz prices, plus 3 flights. Wine shows copa and botella prices. Every beer has a brewery line.

## What changed from K1 (panel + coordinator)
- **The field carries the menu.** One terrain function, `h = -y + W(y)·B(x,y)`, draws the hero with contourpy. The same function runs in the page script after the fonts load:
  - Each hilera's furrow is the level line of `h` through that row.
  - Each name is set where the furrow passes under it, so rows near the top step with the land and relax into straight hileras lower down.
  - Section strips (the tinted De la Casa and beer/wine strips) are bounded by level lines.
  - Text stays horizontal; only the rules and strip edges bend.
- **Serape read removed.**
  - The front divider bands are gone.
  - Agave is drawn as true plan-view rosettes: three leaf-whorl variants, each with a cast shadow.
  - Planting varies: blocks of plants with bare gaps, size drifting along the row, spacing that grows with plant size, and every other earth strip left as bare furrows.
  - About half as many plants as K1.
- **One modular grid.** Three equal columns (166.3 pt, 20 pt gutters) run through the cocktails, flights and beer/wine.
  - Zero proof uses a 4-up subdivision.
  - The spirits survey table uses 2 columns of the same measure.
  - Items that share a row share their serve-line baseline (`margin-top:auto`).
- **Hierarchy.**
  - Section heads are 20 pt, 1.67× the 12 pt names.
  - Level-2 heads are tracked caps of 3 words or fewer.
  - The wordmark is a lock-up sitting on the first furrow, which runs flat under the words and joins the land's level lines on either side.
- **Colour.**
  - Survey red `#AD1F18` is used for prices only.
  - Oak bars and the oak scale bar are oak brown `#6E4A2E`.
  - The red earth is pushed to a lower-chroma brown `#86603F`.
- **Removed:** the north arrows and the art legend. The only keys left are the proposed ring, the oak scale (moved beside the spirits head), and "beer ABV to confirm".
- **Back page:**
  - A thin planted head band.
  - The spirits survey table in 2 balanced columns (17 / 16 rows). Each row reads:
    - top line: name, NOM, oak mark on a 0–36 axis, then the 1 oz, 1½ oz and 2 oz price columns (the 1½ oz standard in bold);
    - second line: the tasting line directly under the name, then region.
  - A Flights band on the 3-column grid.
  - A full beer, cider and wine band: Draft | Cans + Cider | Wine, with copa and botella in aligned columns.
- **Rules applied:**
  - The 3-size pour grid carries the proposed ring in its header, because the size rule is `PROPOSED`.
  - Mezcal with oak "not stated" is off the axis. Ilegal Joven ("Unaged") gets the unaged dot.
  - Cognac VSOP gets its own off-scale arrow.
  - Brewery and producer proposals on approved rows carry the ring on the brewery or producer line.
  - Ingredient phrases are glued with non-breaking spaces, so lines break only at " · ".
  - The last word of each name stays attached to its price.
  - Zero-proof items show "recipe to confirm" in the ingredient slot. Spicy Pineapple Margarita also carries "recipe to confirm".
  - Unknown NOM or region is left blank.
  - Tres Generaciones is printed with no region (its NOM 1102 is shared with Hornitos, whose region is null).
  - Brewery lines are shortened for Tecate and Dos Equis, per the coordinator.
- **Phone:**
  - Its own hero, computed from the same function.
  - Beer and wine come ahead of spirits, and read column by column.
  - Spirits rows show the tasting line and region, then "NOM ####" with the oak mark on its own track.

## Gates (measured; `gates.json`)
| Gate | Result |
|---|---|
| DOM diff vs manifest (letter and phone) | **PASS**. Across 65 items, all of these match: 32 single prices, 99 pour prices, 3 bottle prices, 10 breweries, 3 producers, 3 flights (items + pour), every sensory line, ingredients, garnish, glass, NOM, region, oak class, and the placement of every ring. |
| Price within 1 em, or an aligned column with a guide | **PASS**. The maximum inline gap is 0.683 em on letter and 0.481 em on phone, all on the same line. The table pour columns and wine copa/botella have a right-edge spread of 0.00 px, with a furrow guide on each row. |
| Worst-pixel contrast ≥ 4.5 | **PASS**. Front 5.51, back 5.45, phone 5.51. |
| Legibility | **PASS**. Letter minimum is 8.5 pt; phone minimum is 12 px. |
| Text overlap (em box per line, every text element) | **PASS**. 0 overlapping pairs on the front, back and phone. |
| No taglines or banned lines | **PASS**. 0 hits. |
| Safe area (text ink) | **PASS**. Front ink margins are 36.48 left / 57.6 right / 41.5 bottom pt. Back ink margins are 36.48 left / 37.2 right / 49.4 bottom pt, with the top at 36.48 pt. |
| Bleed PDF | **PASS**. 2 pages at 666 × 846 pt (trim + 3.175 mm bleed + slug, with crop marks). The bleed band is 100% filled. |

## visual_tests.json
- **Front:** primary 22.1%, primary:secondary 54.8, accent 8.1%, 4 regions.
- **Back:** primary 3.5%, primary:secondary n/a (one region), accent 2.4%.

The field is now clearly the only gesture. The ratio overshoots the 11–17 reference band because the old divider bands, which were the secondary regions, are gone.
