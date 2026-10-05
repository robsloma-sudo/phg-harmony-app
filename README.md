# PHG Cocktail Design: Blender drink builder (v1)

`phg_drink_builder.py` turns a PHG drink spec into a photoreal render (PNG) and a web model (GLB) without anyone opening Blender. It runs headless, either as `blender -b -P phg_drink_builder.py -- spec.json out/` or with the `bpy` pip wheel, which is how these test renders were made (Blender 5.0, Cycles).

## What it builds
| Layer | How |
|---|---|
| Glass | Revolves the `phg.glassware.inner_profile` (+ wall thickness) into the glass shape. Stemware gets a stem and foot; tumblers get a solid base. |
| Liquid | Fill height comes from `fill_curve`, adding the ice displacement first. A meniscus is modelled. Colour comes from physically scaled volume absorption, set so the spec colour appears at a 40 mm path. Cloudy drinks (clarity < 0.9) use subsurface scattering. Foam cap is optional. |
| Ice | `none`, `large_cube`, `sphere`, `spear`, `cubes` (count), `crushed`. Bevelled edges and a faint internal cloud so the ice reads. |
| Garnish | Composable grammar (below). Every garnish is a procedural model, so there are no asset licences to manage. |
| Studio | Dark sweep backdrop, key light, back strip (makes the liquid glow), twin rim lights, 85 mm camera with depth of field, AgX colour. Refractive caustics are on so garnish inside the drink is lit correctly. |

## Service style (`serve`)
| serve | Ice (default) | Glass check | Meaning |
|---|---|---|---|
| `up` | none | warns if not stemware | shaken or stirred, strained, no ice |
| `neat` | none | any | straight pour, room temperature, no ice, no dilution |
| `down` | large cube | warns if stemware | over ice in a rocks glass |
| `on_large_cube` / `on_sphere` / `on_spear` | as named | warns if stemware | |
| `on_cubes` | cubes, count calculated to fill the glass (stops at the rim) | warns if stemware | |
| `on_crushed` | crushed / pebble, domed above the rim | warns if stemware | floating garnish crowns the dome |

An explicit `ice` field in the spec overrides the default. Contradictions (e.g. `up` with ice, or `up` in a rocks glass) come back in `warnings`, so the app can flag them.

## Drops (bitters or oil on the surface)
```json
{"type":"drops","liquid":"angostura","count":3,"pattern":"line"}
```
- **Liquids:** `angostura`, `peychauds`, `orange_bitters`, `olive_oil`, `chili_oil`, `sesame_oil`, `citrus_oil` (expressed-peel mist)
- **Patterns:** `line` (default for bitters), `ring`, `triangle` (only with 3 drops), `random` (default for oils, drops never touch). `"drag": true` streaks the dots, like a pick pulled through them.
- **Placement:** drops sit on top of the foam if there is any, otherwise on the liquid. Bitters are opaque dots; oils are clear lenses (IOR 1.47).
- **Size:** `size_mm` overrides the typical spread size. The defaults are visual estimates, not measured; bench check them.
- **Camera:** rises to 32° automatically when a drink has drops or floating garnish, so the surface is visible. Override with `camera_elevation_deg`.

## Garnish grammar (stored in `phg.drink_visuals.garnish`)
```json
[{"type":"orange_half_moon","count":1,"placement":"pick"},
 {"type":"cherry","count":1,"placement":"pick"}]
```
- **Types:** cherry, olive, orange/lemon/lime half moon, wheel, peel (expressed swath), twist (spiral), lime/lemon wedge, mint sprig
- **Placements:** `pick` (every pick item goes on one pick, in list order), `rim` (slit onto the rim), `dropped`, `float`, `drape` (over the rim), `inside_wall` (bent to the curve of the glass)

Examples:

| Garnish | Grammar |
|---|---|
| 1 cherry | `cherry ×1 dropped` |
| 2 cherries | `cherry ×2 pick` |
| Orange half moon & cherry "flag" | `orange_half_moon pick` + `cherry pick` |
| 2 orange half moons & lime peel | `orange_half_moon ×2 inside_wall` + `lime_peel drape` |
| Lime wedge | `lime_wedge rim` |

## Test renders (`renders/`)
| File | Drink | Glass | Ice | Garnish |
|---|---|---|---|---|
| 01 | Manhattan | Nick & Nora | none | 1 cherry, dropped |
| 02 | Daiquiri | Coupe | none | lime wheel on the rim |
| 03 | Old Fashioned | Double rocks | large cube | orange half moon + cherry flag |
| 04 | Tom Collins | Collins | spear | 2 orange half moons inside the wall + lime peel |
| 05 | Highball | Highball | cubes | lime wedge on the rim |
| 06 | Red cocktail | Pint | cubes | 2 cherries on a pick |
| 07 | Pisco Sour | Coupe | up | 3 Angostura drops in a line on the foam |
| 08 | Martini | Nick & Nora | up | 5 olive-oil drops + olive, dropped |
| 09 | Whiskey | Double rocks | neat | none |
| 10 | Negroni | Double rocks | down (large cube) | orange peel, draped |
| 11 | Julep-style | Double rocks | on crushed | mint sprig crown |
| 12 | Highball | Highball | on cubes (auto count 12) | lime wheel inside the wall |

Each test render has a matching `.glb` file. The colours and fill volumes in these specs are placeholders, not PHG recipes.

## Known gaps (v1)
- Glass shapes are fitted from published dimensions plus a family template, not traced from real glasses. The Collins (2518) and pint (1639HT) fits came out implausible (implied base > 25 mm), so they stay `unverified` until they are measured in house.
- Peel: rounded swath with a C-curl, an oil-gland bump texture and low waxy specular. Twists are spirals. Studio exposure is −0.7 EV so saturated garnish keeps its colour under AgX.
- Condensation: water beads on the outside of iced drinks, below the fill line only (`condensation`: auto / true / false, plus `condensation_density`). Frost on chilled 'up' glasses isn't built yet.
- The dropped cherry in the Manhattan is correctly hidden by the dark liquid. A guest would see it under bar lighting, so a "showcase" light option is planned.
- Crushed ice is built from 9 mm pebbles. Finer snow-cone ice would need a particle system.
- Mint: `count` above 1 on `float` fans the sprigs into a julep bouquet.
- Render time on CPU: about 100 s per image at 720×960 / 64 samples. A GPU worker brings this to a few seconds.
