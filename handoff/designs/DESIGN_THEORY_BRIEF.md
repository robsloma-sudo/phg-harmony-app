# What good design means for PHG menus (from phg_design + Rob's references)

Written 2026-09-28 after Rob's reaction to explore A-F: "atrocious... not using the abstract design knowledge."
Sources: `phg_design.principles` (full definitions, mechanisms and failure modes), `decision_rules`, `validation_tests`,
`case_studies`, and `references/rob-2026-09-28/`. Every designer and critic reads this before working.

## 1. The theory in one paragraph
A menu is one governing idea (`creative_thesis_required`, `concept_before_decoration`) expressed through **one** dominant
gesture, with everything else made quiet so that gesture can win (`focal_dominance_relative`, `hierarchy_not_everything_loud`,
`contrast_is_finite_resource`). The reading layer — names, descriptions, prices — is conventional, calm and tightly grouped
(`expressive_type_boundary`, `menu_item_is_unit`, `price_association`). Categories are separated by space and a small
typographic head, not by boxes (`menu_sections_need_transition`, `enclosure_strong_grouping`). The identity comes from
transforming, not illustrating, the subject (`abstraction_reduces_cliche`, `literal_motif_budget`,
`style_not_costume`), and every device must earn its place or be removed (`restraint_devices`, `fix_overdecorated`,
`ablation_reveals_value`). Breadth means different *structures*, not different costumes (`process_breadth_before_refinement`:
failure mode "dozens of thumbnails are cosmetic variants"; `systematic_options`, `system_option_matrix`).

## 2. What Rob's references actually do (the house grammar)
All ten panels of ref-02 and most of ref-03 share one grammar; only the art gesture changes:
1. **One art gesture**, cropped by the page edge: painterly agave leaves, a flat sun disc plus stair, a gold line
   agave, a brush-stroke vertical wordmark, a floral rail. Never several.
2. **Wordmark is the only large type.** One display word, widely tracked or monumental, plus a tiny tracked sub-line.
3. **Reading layer is small and plain.** Item names in sentence/title case in a text serif or clean sans; an optional
   one-line ingredient description smaller and lighter; price a short hop to the right in the same size. No leaders,
   no starbursts, no boxes, no tables.
4. **Section heads are small tracked caps in the single accent colour** — the only place the accent appears besides the art.
5. **Two short columns** (short measure keeps prices near names without leaders — `fix_remote_prices`).
6. **Two or three inks.** Ground + ink + one accent. Measured accent area in the refs: 0.4-6% of the page (except
   where the art itself is the colour field).
7. **Quiet space is structural**: it frames the list and lets the art breathe (`whitespace_relational`), and a small
   tagline stack ("GOOD DRINKS / GOOD PEOPLE") sits in a quiet corner as a signature, not a banner.

## 3. Why our rounds 17-18 and explorations A-F failed (measured + observed)
| Failure | Where | KB key violated |
|---|---|---|
| Every section boxed / carded with equal weight | E, D (8 enclosures + tables), B, r17 | `menu_sections_need_transition` ("fragmented card wall"), `hierarchy_not_everything_loud` |
| Prices louder than names (starbursts, badges, big numerals) | E, A | `expressive_type_boundary`, `price_prominence_contextual` |
| Accent colour everywhere: measured accent area 48% (A), 47% (B), 60% (E) vs refs ≤6% | A, B, E | `accent_requires_scarcity`, `contrast_is_finite_resource` |
| No single focal gesture — D's squint test has no dominant region (0.06% primary) | D, C | `focal_dominance_relative`, `thumbnail_test` |
| Style costume: borrowing rótulo, riso, brutalist, field-guide *surfaces* | E, C, A, D | `style_not_costume`, `semantics_before_form` |
| Literal motifs (agave, sun, moon, glasses) drawn as stamps | E, F, r18 | `literal_motif_budget`, `motif_system_not_stamp` |
| Long passages in tracked caps | E, A, D | `case_has_cost` |
| Hand-drawn SVG art below the craft bar of the refs | F, r18, D | `craft_quality`, `illustration_family_grammar` |
| Descriptions echo names ("Blanco tequila pour.") | all | `description_supports_choice` |
| Critics rewarded boldness/elements; nobody subtracted | process | `cantina_round3_cards`, `fix_overdecorated` |

## 4. The corrected process (every direction, every round)
1. **Thesis first** (in proposal.md before any code): one sentence, 4-7 concept words, an avoid-list, and the one gesture.
2. **Device budget**: 1 art gesture · 1 display word · 1 accent colour · 0 section boxes · 0 price ornaments ·
   tracked caps only on labels ≤ 3 words. Anything beyond the budget needs a written reason.
3. **Reading layer fixed**: names sentence/title case ≥ 11 pt print; descriptions ingredient-first, lighter, one line;
   prices same size as names, right of the name within a short column, tabular figures.
4. **Build, then run** `python3 handoff/designs/tools/visual_tests.py preview-letter.png` and look at the render at
   thumbnail size. Targets: accent area ≤ 8% (unless the art is the colour field), one clearly dominant region.
5. **Subtraction pass**: remove 25% of devices; keep only what the render proves it needs (`fix_overdecorated`).
6. **Compare to the best checkpoint and revert** anything that got worse (`iterate_with_reversion`).
7. Art: no raster until `media.canva.com` is allowed. Use gestures that code can execute at reference craft —
   monumental type, flat geometric abstraction, a single disciplined line drawing with one stroke weight — never
   multi-object hand-drawn scenes.
