# Design knowledge digest (phg_design)

The operating manual for the Menu Designer and the critics. It summarises Rob's design-theory knowledge base in Supabase
(project `lqjtwabzmgjcufftuqvu`, schema `phg_design`), read in full on 2026-09-28. Keys in `backticks` are database keys
(`principle_key`, `rule_key`, `dimension_key`, `test_key`, `guidance_key`), so you can pull the full row. See
handoff/agents/DESIGN_KB_QUERIES.md for ready-to-run SQL. **Note: the designer gateway cannot read `phg_design` yet (a
grant is needed; see that file).** Until then, this digest is your copy of the knowledge base.

What was read:

| Table | Rows | Notes |
|---|---|---|
| agent_guidance | 11 | all read, section A |
| brief_profiles | 2 | all read, section B |
| case_studies | 7 | all read, section B; `scores` is `{}` and `creative_thesis`/`artifact_ref` are null in every row |
| rubric_dimensions | 58 | all read, section C; every weight is 1; 11 are hard gates |
| decision_rules | 69 | all read, section D |
| rule_principles | 0 | empty, so rules are not yet linked to principles |
| validation_tests | 60 | all read, section F |
| principles | 187 | all read, section E (menu-relevant subset listed) |
| concepts | 316 | vocabulary across 28 domains (typography 58, composition 37, production 23, ...); 303 marked measurable |
| variables | 192 | measurable variables with units and scales (composition 28, typography 26, geometry 12, ...) |
| sources | 37 | books (Albers, Bringhurst, Lupton, Müller-Brockmann, Ruder, Hofmann, Gerstner, Vignelli, Tufte, Dondis), MIT/Yale/AIGA courses, W3C/Apple/Material, 9 menu studies (e.g. Yang et al. 2023 meta-analysis, Reynolds 2012 scanpaths) |
| principle_sources | 49 | links 22 sources to principles |
| relationship_types | 10 | aligned_with, balances, dominates, groups_with, points_toward, frames, contrasts_with, repeats, interrupts, anchors |
| ingestion_runs | 0 | empty |
| palettes, typography_profiles, composition_profiles, critiques, revision_decisions, visual_objects, visual_relationships | 0 each | confirmed empty |

Evidence classes matter (`evidence_weighting`): `technical_standard`, `perceptual_research`, `academic_research` and
`meta_analysis` outrank `practitioner_philosophy`, `design_theory` and `phg_synthesis` (Rob's own synthesis). Quote the
class when you cite a principle.

---

## A. Agent guidance (all 11, ordered by priority)

| Pri | Key | Domain | Instruction (verbatim) | Why |
|---|---|---|---|---|
| 100 | `atomize_sources` | research | When ingesting a source, create separate records for distinct concepts, mechanisms, failure modes, exceptions, tests and applications rather than one summary record. | Fine-grained retrieval produces more precise design reasoning. |
| 100 | `creative_thesis_required` | art_direction | Before producing a visual direction, write a one-sentence creative thesis describing the intended identity and experience. Derive concept vocabulary and an explicit avoid-list from it. | Prevents category-template design and decorative drift. |
| 100 | `evidence_weighting` | reasoning | Do not treat perceptual research, technical standards, historical facts, practitioner philosophies, professional conventions and PHG synthesis as equivalent. Preserve evidence class and confidence in recommendations. | Prevents influential opinion from masquerading as universal law. |
| 100 | `hard_gates` | critique | Treat content integrity, legibility, accessibility, and item-price association as hard gates. Do not allow high scores elsewhere to compensate for failure. | Averages can hide fatal usability defects. |
| 100 | `no_single_average` | critique | Track hierarchy, composition, typography, color, specificity, concept, craft, originality, restraint, emotional fit, legibility and integrity independently. | Prevents metric gaming. |
| 100 | `revert_allowed` | process | Maintain the best-known checkpoint. A revision that weakens the design should be reverted rather than retained because it is newer. | Iteration should learn, not accumulate. |
| 95 | `global_script_check` | typography | Before applying typography guidance, identify the writing system and avoid assuming Latin classifications, proportions or conventions apply unchanged. | Typography is culturally and structurally script-dependent. |
| 95 | `measure_then_interpret` | visual_analysis | Where a visual property is measurable, record normalized geometry, contrast, spacing, density, palette area and related values before adding qualitative interpretation. | Separates observation from judgment. |
| 95 | `precedent_analysis` | research | Retrieve multiple relevant precedents and record why each is relevant, transferable principles, and elements that must not be copied. | Builds visual literacy while avoiding imitation. |
| 90 | `visual_tests` | critique | Run thumbnail, blur or squint, grayscale, density, negative-space, alignment, proximity and visual-mass checks where applicable before subjective critique. | Adds observable evidence to critique. |
| 85 | `style_not_costume` | art_direction | When drawing from a historical style or movement, identify its underlying organization, technology and communication logic before borrowing surface motifs. | Reduces superficial pastiche. |

---

## B. Brief profiles and case studies

### Brief profiles (2)

| Key | Venue / artifact | Goals | Required domains | Hard-gate dimensions | Default tests | Retrieval terms |
|---|---|---|---|---|---|---|
| `cocktail_menu` | cocktail_bar / menu | brand_specificity, scanability, item_price_association, atmosphere, craft | menu_design, typography, composition, color, art_direction, identity, accessibility | content_integrity, legibility, accessibility | thumbnail_test, blur_squint_test, grayscale_test, logo_off_test, price_pair_scan, actual_size_test | menu, price, hierarchy, typography, palette, identity, whitespace, ornament |
| `mobile_menu` | restaurant / mobile_menu | legibility, responsive_recomposition, item_price_association, brand_continuity | menu_design, digital_design, typography, composition, accessibility | content_integrity, legibility, accessibility | thumbnail_test, grayscale_test, price_pair_scan, actual_size_test | responsive, mobile, price, reflow, typography, hierarchy |

Use `cocktail_menu` for every bar / cantina beverage menu and `mobile_menu` for the phone rendering. Note the profiles list
three hard gates, but `agent_guidance.hard_gates` and the rubric also make **item-price association**
(`menu_item_association`) a gate; treat it as one.

### Case studies (7): which venue they concern

All seven are `case_type = agent_training`, `venue_type = cocktail_bar`. **Four concern the cantina** (the Iowa City
"Cantina & Cocktail Bar" test menu); **three concern Casa Luna** (a cocktail bar). **None concern a bistro.** In every row
`scores` is empty (`{}`) and `creative_thesis` and `artifact_ref` are null, so there are no numeric scores to report; the
lessons are in `global_analysis`, `critique` and `lessons`.

| Case | Round | Outcome | Brief | Analysis (from `global_analysis`) | Critique | Lessons |
|---|---|---|---|---|---|---|
| `casa_luna_round1_black` (Casa Luna, black/gold two-column) | 1 | passed_current_80_threshold | Create a Casa Luna beverage menu under the current multi-agent critique process. | two_column; black/bone/gold; minimal ornament; low visual energy; large lower field; mixed inline prices; identity **low** | Clean and readable, but generic and under-art-directed. Large lower area behaves more like content underflow than active whitespace. | Palette variation is not concept development. Technical cleanliness can pass while identity remains weak. |
| `casa_luna_round1_cream` (cream/gold/teal single column) | 1 | passed_current_80_threshold | same | single column, remote prices far right; very high negative space; identity **low** | Remote-right prices create excessive eye travel and weaken item-price association. Composition is highly underfilled. | Alignment alone does not guarantee association. Empty canvas should not be scored as successful whitespace. |
| `casa_luna_round1_navy` (navy/gold editorial) | 1 | passed_current_80_threshold | same | single column, remote prices; navy/bone/gold; serif plus spaced caps; low energy; identity **low to medium** | More atmospheric than the cream version but still relies on palette and type treatment rather than a distinctive visual concept. | Mood is not the same as brand specificity. |
| `cantina_round2_two_column` (cantina, two-column banners) | 2 | passed_current_80_threshold | Second-round design after critique-driven iteration. | two_column; papel-picado-like banners, agave, diamonds; cream/rust/mustard/green; moderate ornament; identity **medium** | Stronger identity and hierarchy, but category-coded ornament risks substituting decoration for a more specific creative thesis. | Identity devices improve memorability but require conceptual justification. Category cues can become cliché. |
| `cantina_round2_mobile` (cantina, mobile single column) | 2 | passed_current_80_threshold | Responsive/mobile variant of round two. | single_column_mobile; same palette; moderate ornament; clear hierarchy | Usable responsive adaptation with clearer item-price proximity, but inherits the desktop system's art-direction limits. | Responsive success does not repair a weak creative thesis. |
| `cantina_round3_cards` (cantina, numbered card system) | 3 | current | Later iteration using stronger modular ornament. | six_card_grid; numbers, banners, icons, double borders, translations; ornament **high**; device density **high** | Moved from generic restraint to over-decoration. Nearly every module gets several equal-strength devices, flattening hierarchy and suggesting the critics reward visible additions. | More designed elements do not necessarily make better design. Critic optimization can cause device accumulation. Retain and compare prior best checkpoints. |
| `cantina_phg_development_v1` (cantina, PHG tile/agave system) | 4 | study_not_final | Build on the round 2/3 cantina direction using the expanded knowledge base. | asymmetric two-column modular; agave, tile geometry, arched sun/moon, botanical watermarks; cream/deep green/rust/ochre; ornament high but systematized; hierarchy stronger; identity **high**; price association strong; section enclosure high; cultural reference density high | Major improvement in identity, item-price association, hierarchy and motif coherence. Still needs ablation: section enclosure is heavy, the top ornamental field may compete with content, and Mexican-coded motifs must be checked for specificity and context rather than category shorthand. | Ornament improves when motifs follow a shared grammar. High identity can coexist with functional item blocks. A stronger concept does not remove the need for subtraction. Cultural reference needs provenance and context. Next iteration should test fewer borders and more abstract motif behaviour. |

The pattern across all seven: **our 80-threshold passed designs the knowledge base rates as generic** (Casa Luna ×3,
cantina round 2), and our critics then pushed the cantina into over-decoration (round 3). The KB's fix is thesis first,
motif grammar, then subtraction.

---

## C. The rubric (58 dimensions)

All 58 dimensions have **weight 1** and anchors on a **0 / 0.5 / 1** scale (0 = failure, 0.5 = competent, 1 =
exceptional); `content_integrity` has only 0 and 1. **11 are hard gates** (marked **G**): a gate failure blocks approval
regardless of every other score. Only gates have `failure_conditions`.

### Hard gates (11)

| Key | Domain | Anchors 0 / 0.5 / 1 | Failure conditions |
|---|---|---|---|
| `content_integrity` | functional | materially wrong or missing / — / fully correct | wrong price; missing item; misassociated content |
| `legibility` | functional | unusable / effortful / clear | essential text unreadable |
| `accessibility` | functional | major barrier / partial compliance / robust | required contrast fails; meaning only by color |
| `menu_item_association` | menu_design | ambiguous / usable / immediate | price or description materially associates with wrong item |
| `environmental_legibility` | environment | fails real use / usable with effort / robust | essential menu content unreadable in intended environment |
| `information_integrity` | information_design | misleading / mostly accurate / rigorous | material graphical distortion |
| `production_fitness` | production | fails output / workable / well engineered | critical content lost in output |
| `color_reproduction` | production | uncontrolled failure / acceptable / well proofed | critical brand/content color materially fails output |
| `raster_fitness` | production | visible failure / acceptable / well optimized | critical image detail materially degrades |
| `binding_fitness` | production | assembly failure / acceptable / well engineered | critical content lost or sequence broken |
| `state_feedback` | digital_design | ambiguous / usable / robust | critical focus, error, or selection state unavailable |

### Scored dimensions (47), by domain

| Domain | Key: definition (anchors 0 / 0.5 / 1) |
|---|---|
| art_direction | `concept_strength`: a clear governing idea meaningfully connects major decisions (none / partial / strong and generative). `emotional_fit`: experience supports intended tone for audience (mismatch / plausible / strong fit). `image_type_integration`: conceptual and spatial integration of imagery and type (disconnected / coexistent / mutually reinforcing). `originality`: synthesizes influences into a fresh solution (derivative / competent synthesis / distinctive). `restraint_quality`: devices used because they serve concept, hierarchy, identity or function (cluttered/arbitrary / controlled / precise) |
| color | `color_quality`: colour supports hierarchy, identity, perception, accessibility (harmful / functional / exceptional). `palette_system`: functional roles, area ratios, controlled exceptions (arbitrary / usable / highly coherent) |
| composition | `boundary_craft`: edge distances, tangencies, cropping, frames (accidental / controlled / exceptionally resolved). `composition_quality`: balance, tension, rhythm, negative space form a whole (unresolved / competent / exceptional). `focal_dominance`: stability of primary focal priority (no priority / readable / precisely controlled). `hierarchy_consistency`: scale, weight, colour, position, spacing, enclosure agree (contradictory / mostly aligned / nuanced and coherent). `hierarchy_quality`: priority and reading order evident (flat/confused / usable / clear and nuanced). `salience_control`: high-contrast attention allocated per hierarchy (scattered / mostly controlled / precisely allocated). `visual_balance`: equilibrium or intentional imbalance (accidentally lopsided / stable / purposeful and nuanced) |
| craft | `craft_quality`: microrelationships, optical corrections, reproduction details resolved (rough / professional / highly refined) |
| depth | `shadow_depth_coherence`: depth cues, light direction, shadows (conflicting / coherent / purposeful) |
| digital_design | `loading_continuity` (disruptive / acceptable / seamless) |
| editorial | `editorial_navigation`: folios, running heads, section cues (disorienting / usable / effortless) |
| evaluation | `critic_independence` (same blind spot / some diversity / strong independent coverage). `critique_quality` (taste assertion / actionable / observable, sourced and testable) |
| gestalt | `grouping_clarity`: grouping cues match semantic structure (conflicting / mostly clear / immediate and precise) |
| grid | `grid_logic` (arbitrary / functional / coherent and flexible) |
| identity | `brand_specificity`: specific to this identity, not a category template (generic / some specificity / distinctive and coherent). `identity_responsiveness`: marks survive size and media (fails constrained use / usable variants / robust system) |
| illustration | `illustration_coherence`: one grammar of line, shape, perspective, detail, texture, colour (fragmented / mostly consistent / strong family) |
| imagery | `image_direction`: gaze, motion, leading lines vs crop and type (leaks attention / neutral / strongly integrated). `image_treatment_coherence`: tone, colour, grain, crop (fragmented / mostly coherent / strongly art-directed) |
| information_design | `navigation_quality` (disorienting / usable / effortless) |
| menu_design | `menu_section_navigation`: identifying and moving among categories (merged/confusing / usable / effortless) |
| menu_engineering | `commercial_evidence`: evidence linking design to sales (assumed / observational / well controlled) |
| perception | `crowding_control` (interfering / usable / effortless). `depth_coherence` (conflicting / coherent / purposeful) |
| process | `option_diversity`: directions differ structurally (cosmetic variants / some structural difference / genuinely distinct). `revision_learning`: iterations test hypotheses and keep strengths (random accumulation / partially tracked / causal and cumulative) |
| research | `evidence_quality` (unsupported / mixed / strong provenance) |
| sequence | `pacing_quality` (monotonous/confusing / functional / intentional and engaging) |
| strategy | `audience_fit` (mismatched / plausible / well evidenced). `cultural_context`: use of cultural references, symbols, scripts, historical styles (misleading/extractive / basic context / well researched and appropriate) |
| systems | `adaptability` (breaks easily / limited flexibility / robust). `spacing_consistency` (arbitrary / mostly systematic / systematic with contextual judgment). `system_coherence` (fragmented / mostly coherent / strong system). `token_system_quality` (arbitrary values / partial system / coherent semantic system) |
| typography | `localization_robustness` (source-language only / limited / robust). `numeric_scanability`: associating and comparing prices (confusing / usable / effortless). `typographic_texture`: evenness of spacing across words, lines, paragraphs (distracting / competent / highly refined). `typography_quality`: selection, spacing, hierarchy, measure, optical craft (poor / competent / exceptional) |
| visual_communication | `semantic_clarity` (misleading / understandable / precise and rich) |

### Notes for critics

- **Which dimensions apply to a printed/HTML bar menu.** Score these: the 7 menu-relevant gates (`content_integrity`,
  `legibility`, `accessibility`, `menu_item_association`, `environmental_legibility`, `production_fitness`,
  `color_reproduction`, plus `raster_fitness` when there is illustration or photography) and the scored dimensions in
  art_direction, color, composition, craft, gestalt, grid, identity, illustration/imagery (when present), menu_design,
  strategy, systems (`spacing_consistency`, `system_coherence`) and typography. Mark `state_feedback`,
  `loading_continuity`, `information_integrity`, `binding_fitness` (unless folded/bound), `editorial_navigation`,
  `pacing_quality` (single page) and `localization_robustness` as n/a where they do not apply. `commercial_evidence`,
  `critic_independence`, `critique_quality`, `evidence_quality`, `option_diversity` and `revision_learning` score the
  process, not the artifact.
- **Do not average** (`no_single_average`, `regressions_block_pass`): report each dimension, and compare each revision to
  the best checkpoint dimension by dimension (`rubric_delta_matrix`).
- To map to our 0-100 scale: 0 ≈ 0-40, 0.5 ≈ 60-74, 1 ≈ 90+. "Competent" (0.5) matches our 60-74 "clean but safe" band.

---

## D. Decision rules (69), by domain

Format: **problem** → interventions → expected effect → validation. Priority / confidence in brackets.

### Menu design
- `menu_item_block_spacing` [100/0.99]: descriptions or prices look attached to neighbouring items (signal: item-block gap ≤ internal name-description gap; price nearer another item) → reduce internal distances, increase inter-item gap, repeated alignment anchors, measure nearest competing association → strong item grouping → item-block proximity map, price pair scan.
- `real_world_menu_legibility` [100/0.99]: approved from a digital proof only (small description type, dark venue, glossy stock, low-contrast palette) → print/render at actual size, view at expected distance, test low light and glare, increase angular size or contrast → real-world readability → environmental legibility test, glare-angle test, actual-size proof.
- `reject_sweet_spot_claim` [100/0.98]: layout justified by a universal gaze hot spot (golden triangle, top-right, first/last) → replace folklore with hierarchy, grouping and task reasoning; test real scanpaths when it matters → more defensible layout → find empirical evidence for the placement claim.
- `separate_attention_sales` [100/0.99]: a critic rewards an element for attracting attention and assumes more sales → label the outcome "attention only"; purchase claims need POS or a controlled test; consider substitution → honest optimization target → state the measured outcome (gaze, attitude, intention, purchase, revenue).
- `fix_remote_prices` [95/0.96]: prices on a remote edge lose connection to names (large eye travel, dense list, no leader) → move prices nearer, stable tabular grid, subtle leaders only if appropriate, reduce column span → faster lookup, fewer association errors → scan five random item-price pairs; proximity map.
- `menu_section_transition_pass` [95/0.98]: categories merge, or every category is boxed with equal weight → spacing and type before enclosure; boxes only for conceptually justified groups; vary transition strength by hierarchy → clear navigation, less noise → section-boundary recognition; device subtraction.
- `responsive_menu_recompose` [95/0.97]: hierarchy or price relationships degrade on mobile → one primary reading column, keep item-price proximity, re-evaluate heading scale and spacing, move secondary info after primary → mobile readability → narrow viewport, large-text reflow, item-price scan.
- `audience_specific_menu` [85/0.92]: design assumes every guest scans and compares alike → define audience and context, their decision priorities; adapt price prominence, descriptions, density → context fit → persona walkthrough.

### Menu engineering
- `menu_commercial_validation` [100/0.99]: sales/profit claim without behavioural evidence → define outcome, capture contribution margin and baseline popularity, controlled test, inspect substitution → evidence-based claims → pre/post or A/B; category share and margin analysis.

### Art direction
- `global_reference_context` [100/0.97]: cultural or script references borrowed for exotic look (no documented origin; sacred/specific form used decoratively) → identify source culture and function, research context, separate structural learning from motif extraction, avoid restricted or misleading use → broader vocabulary, more responsibility → document provenance and intended transfer; verify script-specific typography.
- `controlled_maximalism_pass` [95/0.98]: high density feels noisy (uniform ornament, many equal focal points, no quiet zones) → map density field, create quiet counterzones, concentrate ornament near anchors, reduce secondary contrast → rich but hierarchical → density map, salience budget, device subtraction.
- `literal_motif_ablation` [95/0.98]: identity built from many direct category symbols, motif count rising each round → rank motifs by specificity, ablate weakest literal ones, abstract the strongest into geometry/pattern/crop, keep one or two literal anchors → more proprietary identity → single-feature ablation, logo-off, category-cliché comparison.
- `rhetorical_preflight` [95/0.96]: coherent style but no stated purpose/audience/response → state purpose, audience, intended viewer response; map each major visual choice to one of them → purposeful decisions → explain what each major element contributes.
- `fix_generic_menu` [90/0.95]: clean and legible but could belong to any venue (palette swap is the main variation; generic header + list) → one-sentence creative thesis, 4-7 concept vocabulary terms, explicit avoid-list, identity-relevant precedents, **one proprietary graphic behaviour derived from the concept** → stronger identity → remove venue name and ask whether the concept is still identifiable; compare with unrelated category templates.
- `word_image_integration_pass` [90/0.96]: text and image coexist without interacting (image swappable; headline just labels it) → decide whether the image reinforces, complicates, contrasts or extends the text; adjust crop, scale, position or wording → integration → state the relation in one sentence; image substitution test.
- `fix_overdecorated` [85/0.93]: borders, banners, icons, labels, translations, rules and ornaments compete in each module → rank devices by function, remove lowest-value ones, reserve strongest motif for primary hierarchy, allow quiet regions → clearer hierarchy, sophistication → **remove 25% of decorative devices and compare**; grayscale; thumbnail. Exception: intentional maximalism, if hierarchy survives density.
- `motif_systemize` [85/0.94]: motif repeated identically or arbitrarily → define invariant, allowed scale range, crop and rotation rules; tie density to hierarchy level; reserve exceptional treatment for focal moments → coherent but not mechanical → remove logo and check the motif system is still recognisable; list every variation and verify it follows a rule.
- `historical_style_context` [75/0.91]: historical surface features without their logic → identify the movement's principles, separate structure from motif, adapt only what fits the brief → less pastiche → explain each borrowed feature without naming the style; remove motifs and see if structural influence remains.

### Composition
- `hierarchy_conflict_audit` [100/0.99]: variables disagree about priority (small low-priority content has the strongest accent; framing elevates tertiary modules) → rank semantic priorities, score scale/weight/value/colour/position/spacing/enclosure per element, align strongest cues with top priorities → predictable reading order → hierarchy cue matrix, blur/squint, three-second recall.
- `salience_budget_pass` [100/0.98]: too many regions demand primary attention → rank focal priorities, reserve strongest contrast for top levels, remove devices from secondary regions, retest → clearer focal hierarchy → blur test, salience map, high-salience region count.
- `focal_dominance_audit` [95/0.98]: primary content exists but does not dominate → measure primary:secondary salience ratio, **reduce competitors before enlarging the primary**, concentrate contrast → clearer focal order → salience budget, focal dominance ratio.
- `hierarchy_quiet_pass` [95/0.98]: too many sections use equally strong devices → rank content, reduce contrast on secondary/tertiary, remove framing from low-priority modules, concentrate the strongest accent → restraint → blur test shows no more than the intended focal regions; count high-salience devices per level.
- `tangency_cleanup` [85/0.97]: edges almost touch → separate decisively or overlap decisively; check at actual size → cleaner craft → tangency scan; actual-size proof.
- `edge_tension_audit` [80/0.93]: objects near edges/corners without reason → measure edge and corner distances; more breathing room or decisive boundary interaction; rebalance mass → edge-distance map, visual-mass centroid.
- `fix_dead_space` [80/0.92]: large empty regions with no function (content ends far above the bottom; columns end at different heights) → re-evaluate format, redistribute modules, increase meaningful scale, counterweight only if the concept supports it → intentional negative space → thumbnail balance, blur, visual-mass map.

### Critique and evaluation
- `squint_before_detail` [100/0.97]: critique fixes micro-details before macro hierarchy → blur/squint, identify top three masses, compare observed vs intended order, fix scale/value/spacing first → thumbnail, blur, three-second reading order.
- `critic_independence_check` [100/0.99]: many critics agree but share model/rubric/prompt → record critic model and rubric, add a structurally different perspective, separate perceptual, functional, art-direction and commercial critics → critic diversity audit; agreement by dimension.
- `single_variable_ablation` [90/0.98]: critics disagree whether a device helps → make a variant removing only that feature, run the same tests, keep it only if its contribution is measurable or conceptually necessary → feature ablation delta.

### Process
- `diverge_before_polish` [100/0.98]: early options polished but alike (same grid, same hierarchy, different palettes) → orthogonal, diagonal and freeform structures; vary information architecture and image-type relationship; delay polish → variant silhouette test.
- `iterate_with_reversion` [100/0.98]: accumulated changes cause drift (score rises while coherence falls) → keep the best checkpoint, state a hypothesis before each revision, measure, revert failed interventions → blind A/B against the best prior iteration; dimension delta.
- `revision_regression_gate` [100/0.99]: new revision scores higher overall while important qualities fall → compare to checkpoint by dimension, revert or isolate the harmful change, never average away hard regressions → rubric delta matrix.

### Systems
- `system_option_matrix` [100/0.98]: concepts differ only by palette or font → define independent variables (composition, hierarchy, type behaviour, image strategy, motif logic), combine within constraints, select on brief criteria → grayscale silhouettes stay distinguishable; describe each option without naming colour or font.
- `rule_break_budget` [90/0.97]: exceptions everywhere → state the baseline rule, limit exceptions to focal/semantic conditions, make the important exception decisive, remove weak ones → rule-break frequency.
- `token_system_audit` [85/0.97]: near-duplicate colours, spaces, type values → cluster, define primitives, map semantic roles → token reuse rate.

### Typography
- `expressive_type_boundary` [95/0.98]: expressive manipulation spreads into content that must be read fast (prices/descriptions distorted, cropped body, tracking/rotation impairs scanning) → **reserve strongest manipulation for display roles**, keep body and price conventional, connect layers through shared type details → three-second recognition, actual-size reading, role-by-role type audit.
- `localization_stress_test` [95/0.99]: layout works only for source-language length (tight labels, all-caps English hierarchy) → test expansion strings, alternate scripts, flexible containers → localization expansion test.
- `macro_micro_type_pass` [95/0.98]: typography judged as one quality → score macro and micro separately; fix macro first unless readability is broken → thumbnail macro test, actual-size micro test.
- `justify_text_audit` [90/0.98]: rivers in justified text → adjust measure, hyphenation, justification, line breaks → river overlay, word-space variance.
- `numeric_column_figures` [90/0.98]: ragged price columns → tabular figures, consistent decimal alignment, currency subordinate → price-column silhouette. Exception: inline prices may not need tabular figures.
- `reverse_type_preflight` [90/0.98]: thin/small light text on dark (hairlines, small counters, uncoated stock) → increase size or weight, open tracking, proof on actual process → counter-closure inspection.
- `type_texture_audit` [90/0.96]: uneven or amateur texture → kerning pairs, tracking by hierarchy level, leading tuned to measure → paragraph texture comparison.
- `optical_alignment_pass` [85/0.96]: mathematically aligned but looks uneven (round glyphs, punctuation) → optical offsets; compare without guides → hide guides; mirror to expose bias.

### Colour and accessibility
- `accessibility_contrast_gate` [100/0.99]: text or graphics below contrast (including over images or gradients) → change value, add a stable backing field behind text, never rely on hue alone → WCAG contrast, grayscale, bright-light simulation. Exception: logos and incidental text.
- `color_legibility_gate` [100/0.97]: hue without value contrast → adjust value first, add non-colour cue, rebalance accent area, test colour-vision deficiencies → grayscale, contrast, CVD simulation, squint.
- `color_output_preflight` [95/0.99]: palette approved in one colour environment → identify target space/process, soft and physical proof, measure critical colours, gamut and total ink → gamut check, proof under intended lighting, DeltaE.
- `palette_in_context` [95/0.97]: attractive swatches behave badly together (accent overwhelms content) → test at intended area ratios and on actual backgrounds, inspect grayscale value structure → Albers-style ground swap, accent-area measurement.
- `palette_role_audit` [95/0.98]: hierarchy unstable across the artifact (accent covers large area; one colour means different things) → label each role, measure area shares, document exceptions → palette-role map, accent-area ratio.

### Gestalt and grid
- `grouping_conflict_audit` [100/0.99] and `gestalt_grouping_audit` [90/0.96]: proximity, similarity, alignment, enclosure or connectedness imply the wrong groups → map intended groups, score each cue, remove or weaken the contradictory cue, increase within-group proximity and between-group separation, remove accidental alignment → grouping-cue matrix; blur grouping test; hide text and inspect clusters.
- `grid_variation_control` [85/0.94]: mechanically uniform or inconsistently misaligned → define base grid, name the hierarchy level allowed to break it, limit and repeat the deviation logic → overlay grid and label every intentional break.

### Identity
- `identity_without_logo_test` [90/0.96]: design relies on the name while the rest is generic → hide logo and venue name, evaluate remaining cues, strengthen concept-derived type, composition, imagery or motif behaviour → logo-off recognition test.
- `brand_cross_media_test` [90/0.97]: identity works in one hero layout only → name 3-5 invariants and the medium-specific variables; test print, narrow screen, wide screen → cross-media contact sheet.
- `responsive_logo_test` [90/0.97]: mark loses recognition when reduced → simplified variant; adjust the lockup rather than only scaling → minimum-size test.
- `audience_signifier_test` [80/0.94]: meaning assumed from designer intent → unprompted interpretation study.

### Imagery, illustration, mark-making, depth
- `crop_with_intent` [90/0.95]: image fitted to a box without regard to focal point, gaze, edge tension → identify focal point, map gaze vector, test tight and loose crops, align crop energy with adjacent type → compare three crops at thumbnail size.
- `image_treatment_normalize` [90/0.97]: images differ in contrast, saturation, grain without reason → define tonal range, saturation mapping, grain behaviour; allow documented focal exceptions → contact sheet, histogram comparison.
- `image_direction_space` [85/0.94]: subject's gaze or motion sends attention out of frame → re-crop for look room, place text/focal object on the gaze vector → gaze-vector overlay.
- `illustration_style_audit` [90/0.98]: illustrations look sourced from different systems → define line-quality profile, perspective system, detail-density range, fill/texture/colour behaviour → asset contact sheet.
- `icon_family_audit` [90/0.98]: icons do not look like one system → construction grid, optical size, stroke and corner logic → silhouette and stroke overlay.
- `texture_reproduction_test` [85/0.95]: texture fails at physical size or competes with small text → preview at 100% output size, print proof, **reduce texture contrast near text**, adjust mark scale → actual-size proof, low-resolution preview, grayscale print.
- `shadow_coherence_audit` [80/0.96]: inconsistent shadows → one light direction; remove shadows if depth is not needed → shadow-vector overlay.

### Other domains
- `production_preflight` [95/0.98]: approved before checking output (spot colours, fine strokes, overprint, trim/binding) → identify process early, proof colour and registration, check trim, bleed, fold, substrate, inspect at actual size.
- `editorial_navigation_pass` [85/0.96], `pacing_sequence_audit` [85/0.95]: multi-page menus need stable section cues and deliberate quiet intervals rather than uniform intensity.
- `crowding_audit` [90/0.97]: dense clusters are hard to identify → increase spacing, fewer simultaneous labels.
- `state_distinction_audit` [100/0.99], `chart_type_task_match` [100/0.99], `data_integrity_gate` [100/0.99], `information_graphic_restraint` [90/0.92]: digital states and charts; apply only if the menu has interactive states or data graphics.

---

## E. Principles that matter most for menus

Key, evidence class, confidence. Full definitions, mechanisms, conditions and exceptions are in `phg_design.principles`.

### Menu layout and item blocks
| Key | Principle | Class | Conf |
|---|---|---|---|
| `menu_item_is_unit` | Each item block (name, description, price) must be internally tighter than its link to neighbours. | phg_synthesis | 0.98 |
| `price_association` | Prices stay visually tied to their item unless a strong grid makes the mapping unambiguous. | phg_synthesis | 0.90 |
| `proximity_grouping` | Proximity is a strong grouping cue; remote prices weaken association. | perceptual_research | 0.95 |
| `price_prominence_contextual` | Prices must be legible and associated but need not dominate unless price comparison is the main task. | phg_synthesis | 0.93 |
| `numeric_alignment_task` / `tabular_figures_for_columns` | Choose decimal/tabular alignment only when guests compare vertically; use tabular figures in price columns. | typographic_practice | 0.98 |
| `menu_sections_need_transition` | Enough separation to signal a new category without boxing every section. | phg_synthesis | 0.97 |
| `enclosure_strong_grouping` / `rules_have_hierarchy` | Boxing every section creates clutter; rules should vary by structural role. | perceptual_research / editorial_practice | 0.98 / 0.96 |
| `menu_type_size_context` / `legibility_environmental` | Test type at holding distance and venue lighting, not point-size rules or a bright monitor. | phg_synthesis / human_factors | 0.99 |
| `glare_reduces_effective_contrast` / `menu_surface_context` | Gloss, stock opacity and show-through change real contrast. | human_factors / production_practice | 0.98 / 0.97 |
| `description_supports_choice` / `menu_description_uncertainty` | Descriptions should give ingredients, preparation, flavour and differentiators in the brand voice, not flourish only. | academic_research | 0.94 / 0.90 |
| `menu_sweet_spot_skepticism` | Eye-tracking does not support universal menu "sweet spots". | academic_research (Reynolds 2012) | 0.96 |
| `attention_not_purchase` / `menu_sales_attention_distinct` | Attention to an item is not proof of more purchases or revenue. | meta_analysis (Yang 2023) | 0.98 / 0.99 |
| `menu_audience_scanpaths` | Price-conscious guests scan menus differently. | academic_research (Ngan 2022) | 0.93 |
| `menu_substitution_matters` / `menu_item_interdependence` / `menu_engineering_needs_margin_popularity` | Emphasis redistributes demand among substitutes; judge with margin and popularity together. | academic_research / practice | 0.94-0.97 |
| `price_format_context` | Removing the $ sign etc. is not a guaranteed revenue tactic. | academic_research (Yang 2009) | 0.95 |
| `authenticity_cues_contextual` | Handwritten type can signal authenticity in some ethnic-dining contexts, moderated by audience; not universal. | academic_research | 0.87 |
| `menu_material_signals` | Typeface, substrate colour and physical weight can shift perceived scale/service; not a universal luxury formula. | academic_research (Magnini & Kim 2016) | 0.88 |

### Typography
| Key | Principle | Class | Conf |
|---|---|---|---|
| `type_roles_semantic` | Display, heading, body, label, caption treatments must map consistently to meaning. | typographic_practice | 0.98 |
| `expressive_type_readability_tradeoff` / `type_word_symbol_form` | Distortion, cropping, unusual spacing build identity, but essential text must stay recognisable. | typographic_practice / academic_instruction | 0.96 / 0.94 |
| `case_has_cost` | All-caps gives shape and emphasis but loses word shapes and needs added tracking; avoid long passages in tight caps. | typographic_practice | 0.96 |
| `macro_micro_typography` | Page hierarchy and glyph-level spacing must both work. | professional_education | 0.97 |
| `type_contrast_dimensions` / `hierarchy_by_difference` | Contrast via case, weight, width, size, spacing; adjacent levels need perceptible, not tiny, differences. | professional_education / design_theory | 0.97 / 0.90 |
| `type_pairing_shared_difference` | Pairs share structure yet differ enough to set roles. | typographic_practice | 0.94 |
| `type_spacing_texture` / `type_color_balance` | Kerning, tracking, word space and leading together set text colour and mass. | typographic_practice | 0.96 / 0.95 |
| `optical_size_context` | Display cuts used tiny become fragile; text cuts used huge look coarse. | typographic_practice | 0.96 |
| `optical_not_geometric` | Mathematically aligned shapes can look misaligned; compensate optically. | typographic_practice | 0.96 |
| `reverse_type_needs_care` | Light-on-dark small type loses hairlines and fills counters. | production_practice | 0.97 |
| `rag_shape_matters` / `line_measure_context` | Control rag; judge measure with size, leading, language and context. | typographic_practice | 0.96 / 0.93 |
| `vertical_rhythm_supports_page` | Baseline intervals align modules, but a strict baseline grid must not damage local spacing. | typographic_practice | 0.94 |
| `global_scripts_context` / `scripts_not_font_swap` / `localization_needs_elasticity` | Spanish and other languages need room; do not impose Latin/English assumptions. | design_education / i18n practice | 0.95-0.99 |

### Colour
| Key | Principle | Class | Conf |
|---|---|---|---|
| `accent_requires_scarcity` | An accent loses focal power when spread widely. | perceptual_design | 0.97 |
| `palette_roles_stable` | A palette is a system when colours have stable roles and controlled exceptions. | systems_design | 0.97 |
| `color_contextual` / `simultaneous_contrast_context` / `same_color_different_appearance` | Colours are judged in context, never as isolated swatches. | practitioner/perceptual research (Albers) | 0.95-0.99 |
| `color_value_balance` | Judge colour by value and distribution, not hue alone. | academic_instruction | 0.94 |
| `limited_palette_depth` | Few inks can give rich systems through value, overprint, transparency, texture. | professional_education | 0.92 |
| `color_emotion_not_fixed` / `warm_cool_relation` | Mood words do not map to one palette. | professional_education / design_theory | 0.88 / 0.85 |
| `gamut_output_dependency` / `metamerism_proof_lighting` | Screen colours may not print; matches can fail under venue light. | color_science | 0.99 / 0.96 |
| `contrast_accessibility` / `not_color_alone` / `accessibility_multiple_cues` | Sufficient luminance contrast; never colour-only meaning. | technical_standard | 0.99 |

### Composition and grid
| Key | Principle | Class | Conf |
|---|---|---|---|
| `hierarchy_variables_should_agree` | Scale, weight, colour, position, spacing, enclosure must not assign conflicting ranks. | phg_synthesis | 0.98 |
| `hierarchy_not_everything_loud` / `contrast_is_finite_resource` | If everything is boxed and accented, hierarchy collapses. | design_theory / phg_synthesis | 0.97 / 0.96 |
| `focal_dominance_relative` | The primary wins by being more salient than competitors, not by absolute size. | perceptual_synthesis | 0.97 |
| `whitespace_relational` | Empty space must group, separate, frame, emphasise or pace; unused canvas is not a virtue. | phg_synthesis | 0.90 |
| `tangencies_need_intent` / `collision_needs_clear_intent` | Separate clearly or overlap clearly; near-touches look accidental. | design_practice | 0.96 / 0.95 |
| `asymmetry_requires_counterweight` / `visual_moment_balance` | Asymmetry needs counterweight; small high-contrast far from centre balances large low-contrast. | design_theory | 0.93 / 0.91 |
| `grid_as_system_not_cage` / `grid_breaking_intent` / `exception_gains_from_rule` | Break the grid deliberately where the baseline system stays perceptible. | practitioner/historical | 0.88-0.98 |
| `grid_matches_content` / `gutter_separates_columns` | Choose grid type by content; gutters must stop columns merging. | design_theory / typographic_practice | 0.96 / 0.97 |
| `rhythm_variation_balance` / `rhythm_needs_cadence` / `density_guides_flow` | Repetition with controlled variation, pauses and syncopation. | design_theory | 0.90-0.94 |
| `diagonal_composition` / `freeform_composition` / `layers_organize_complexity` | Diagonals and freeform need reading-path control; layered compositions need legible separation. | professional_education / design_theory | 0.91-0.93 |
| `edge_proximity_creates_tension` / `visual_echo_unifies` / `counterpoint_preserves_difference` | Edge placement creates tension; echoed angles/proportions unify; orchestrate distinct voices. | practice/theory | 0.89-0.92 |
| `grouping_cues_should_agree` / `spacing_groups_content` | Grouping cues must agree with content structure. | perceptual_synthesis / technical_guidance | 0.97 |

### Concept and art direction
| Key | Principle | Class | Conf |
|---|---|---|---|
| `concept_before_decoration` | Devices emerge from the concept, not accumulate to look designed. | phg_synthesis | 0.90 |
| `literal_motif_budget` | Many direct category symbols at once (their example: agave + cactus + sun + moon + tiles + Spanish labels all equally prominent) make identity generic. | phg_synthesis | 0.97 |
| `abstraction_reduces_cliche` | Transform category symbols through geometry, crop, scale, material or pattern. | phg_synthesis | 0.94 |
| `motif_system_not_stamp` | Motifs repeat by rules of scale, crop, orientation, density, not identical stamps. | phg_synthesis | 0.91 |
| `restraint_devices` | Every border, icon, banner, translation, rule or ornament must serve hierarchy, identity, navigation or concept. | phg_synthesis | 0.88 |
| `maximalism_requires_hierarchy` / `maximalism_needs_quiet` | Dense work needs salience, grouping and quiet zones. | phg_synthesis / design_theory | 0.97 / 0.94 |
| `surprise_should_not_break_task` | Surprise in composition, type or imagery, never at the cost of navigation or reading. | phg_synthesis | 0.96 |
| `image_type_semantic_relation` / `word_image_synthesis` | Type and image interact conceptually, not just by adjacency. | design_theory / professional_education | 0.92 / 0.95 |
| `materiality_supports_voice` | Paper, grain, ink, emboss and edge carry character when consistent with concept and production; fake generic texture fails. | design_practice | 0.89 |
| `appropriateness_context` / `semantics_before_form` / `form_content_context` | A formally excellent device is wrong if it conflicts with audience, content, medium or culture. | practitioner_philosophy | 0.91-0.97 |
| `signal_noise_task_relative` | Ornament is not automatically noise; it can carry identity and context. | phg_synthesis | 0.95 |
| `identity_multiple_cues` | Identity should live in type, palette, composition, imagery, motifs, materiality and language, not just the logo. | design_practice | 0.92 |
| `global_reference_expands_design` / `historical_comparison_form` / `type_technology_context` | Learn from other cultures and periods structurally; avoid pastiche and extraction. | professional_education / historical_fact | 0.95-0.96 |
| `audience_rhetorical_design` | Choose arrangement and imagery for what guests should understand, feel or do. | academic_instruction | 0.94 |

### Imagery, illustration, texture, production (for illustrated / collage menus)
| Key | Principle | Class | Conf |
|---|---|---|---|
| `collage_unify_theme` | Collage must unify sources through concept, composition, colour, scale, edge treatment; otherwise it reads as scrapbook. | professional_education | 0.94 |
| `crop_changes_meaning` / `look_room_direction` / `gaze_directs_attention` / `leading_lines_guide` | A crop is an editorial decision; gaze and leading lines should point to content. | visual_practice | 0.90-0.94 |
| `image_treatment_system` | One set of rules for contrast, saturation, crop, grain, colour mapping, edges. | art_direction_practice | 0.97 |
| `illustration_family_grammar` / `detail_density_hierarchy` | One line/perspective/texture/detail grammar; vary detail to direct attention. | design_practice / visual_practice | 0.97 / 0.91 |
| `texture_needs_scale_fit` | Texture that works at one size can vanish, alias or overpower at another. | production_practice | 0.94 |
| `figure_ground_clarity` / `depth_cues_consistent` / `shadows_need_consistent_light` | Type over imagery needs clear figure-ground; depth cues and shadows must agree. | perceptual_research / visual_practice | 0.95 |
| `bleed_prevents_edge_slivers` / `safe_trim_content` | Full-bleed art extends past trim; critical content stays inside the safe area. | production_standard | 0.99 |
| `resolution_output_size` / `halftone_process_affects_detail` / `overprint_creates_new_color` | Judge raster by placed size; fine texture may plug in print; overprints make new colours. | production_standard / practice | 0.90-0.99 |
| `production_process_shapes_form` | The output process should shape design decisions. | professional_education | 0.95 |

### Evaluation and process
`critique_requires_observable` (0.99: say what is seen, why it matters, which principle, which variable to change; "make it pop" and "feels premium" are not critique), `critic_consensus_not_truth` (0.99), `ablation_reveals_value` (0.98), `regressions_block_pass` (0.99), `revision_hypothesis_test` (0.99), `process_breadth_before_refinement` (0.96), `squint_test_hierarchy` (0.94). All phg_synthesis except the last two.

---

## F. Validation tests you can measure automatically in a Playwright / HTML render

60 tests exist; about half need people, physical proofs or print. These can be computed from the rendered page
(`page.evaluate` over DOM boxes and computed styles, plus a screenshot processed with sharp/canvas). Tag each element with
a role (`data-role="item-name|description|price|section-head|ornament|image|display"` and `data-item="<id>"`).

| Test key | How to measure in the render | Pass |
|---|---|---|
| `item_block_proximity_test` (+ rule `menu_item_block_spacing`) | For each item, `getBoundingClientRect()` of name, description, price. Compute name→price and description→price distances vs the distance from the price to the nearest element of any **other** item; compute internal gap vs inter-item gap. | every component nearer its own item; `item_block_gap` > max internal gap (aim ≥ 1.5×) |
| `price_pair_scan` (geometric proxy; `fix_remote_prices`) | Horizontal eye travel = price.left − name.right, as a fraction of column width; flag rows with no leader/row rule where travel > ~40% of column. | no remote prices without a strong row grid |
| `numeral_alignment_test` (`numeric_column_figures`) | For column prices: right edges within ±0.5 px; `font-variant-numeric` includes `tabular-nums`; decimal positions equal. | no jitter (inline prices exempt) |
| `grayscale_test` / `color_only_removal_test` | Screenshot, convert to luminance; re-run contrast and salience checks; verify every colour-coded distinction also has a text/shape cue. | hierarchy and meaning survive |
| WCAG contrast (`accessibility_contrast_gate`) | For each text node, computed colour vs the sampled background pixels beneath its box (median and 5th-percentile luminance when over images or texture). | ≥ 4.5:1 body/price, ≥ 3:1 large display; worst-case sample, not the average |
| `blur_squint_test` / `thumbnail_test` / `salience_budget_test` / `focal_dominance_test` | Screenshot, Gaussian blur (σ ≈ 1% of page width) and downscale to ~200 px wide; threshold local contrast into regions; count high-salience regions; compute primary:secondary ratio; compare order to the intended list in `proposal.md`. | region count ≤ intended focal count; primary ratio clearly > 1 (e.g. ≥ 1.3); order matches |
| `hierarchy_cue_matrix` | From computed styles per role: font-size, weight, colour luminance contrast, y-position, margin, enclosure (border/background); rank each cue; compare with the semantic rank. | no lower role outranks a higher one on the strongest cues |
| `grouping_cue_matrix` / `section_boundary_test` (geometric) | Cluster element boxes by vertical gaps; compare clusters to sections; check section gap > item gap; count bordered sections. | clusters = sections; boxes not on every section |
| `edge_corner_test` / `tangency_scan` | Pairwise nearest edge distances between boxes (text, ornaments, image masks); flag 0 < d < ~1.5 mm at print size; edge distances vs declared margins. | no near-tangencies; margins equal |
| `grid_overlay_audit` | Compare element left/right edges to declared column lines; classify aligned / spanning / offset. | every deviation is listed as intentional in `layout` |
| `palette_role_map` | Quantize screenshot to palette colours; area share per role; accent share. | roles stable; accent area small (roughly ≤ 10-15%; the KB gives no number) |
| `device_subtraction_test` / `feature_ablation_test` | Render variants with `data-role="ornament"` groups hidden (25% at a time or one feature at a time); re-run salience, grayscale and logo-off checks; critic compares. | a device stays only if removing it hurts hierarchy, identity or navigation |
| `logo_off_test` (`identity_without_logo_test`) | Render with the wordmark and venue name hidden (`visibility:hidden`); give that image to a critic. | still identifiable as this venue |
| `actual_size_test` / `macro_micro_type_test` | Screenshot at device-pixel ratio for 1:1 print size (e.g. 300 dpi) and at phone viewport; check minimum rendered x-height in mm/px for descriptions and prices. | descriptions and prices readable at holding distance (agree a floor, e.g. x-height ≥ 1.4 mm print) |
| `reflow_400_test` / `text_spacing_override_test` / `responsive_menu_recompose` | Set viewport 320 px and `zoom`/font-size 200-400%; inject WCAG text-spacing CSS; detect overflow (`scrollWidth > clientWidth`) and overlapping boxes; re-run proximity. | no clipping or overlap; prices stay with items |
| `rag_profile_test` / `river_overlay_test` | Use `Range.getClientRects()` per description line: line-end x variance, single-word last lines (widows/orphans). | no one-word last lines; controlled rag |
| `token_consistency_test` | Collect distinct computed font sizes, colours, margins; count near-duplicates (e.g. within 1 px or ΔE < 2). | few one-off values |
| `effective_resolution_test` / `trim_bleed_test` | Image natural size vs placed size at print dpi; full-bleed art extends ≥ 3 mm beyond trim; text inside safe inset. | ≥ 300 effective ppi for print; bleed present |
| `localization_expansion_test` | Replace strings with +30% length pseudo-text; detect overflow. | no overflow |
| `visual_moment_test` | Luminance-weighted centroid of the blurred screenshot vs page centre. | offset is intentional (asymmetric designs declare it) |
| `variant_silhouette_test` | Blur/threshold each proposed direction to grayscale blocks; compare structural similarity (e.g. SSIM). | directions differ structurally |

Not automatable (need people or physical proof): `environmental_legibility_test`, `glare_angle_test`,
`lighting_color_test`, `gamut_proof_test`, `production_proof_test`, `reverse_type_proof`, `binding_spread_proof`,
`peripheral_recognition_test`, `unprompted_interpretation_test`, `audience_task_walkthrough`, `menu_commercial_ab_test`,
`image_substitution_test` (critic judgment), `critic_diversity_audit` and `rubric_delta_matrix` (process). Approximate the
dim-venue case by rendering with reduced brightness (`filter: brightness(0.5)`) and re-checking contrast; note it is a proxy.

---

## G. What changes for us

Compared with handoff/agents/MENU_DESIGN_SCORECARD.md and handoff/designs/REVIEW_PROTOCOL.md:

1. **Hard gates replace averaging.** Our rule is "each reviewer's average above 80". The KB says content integrity,
   legibility, accessibility and item-price association are gates that no other score can offset (`hard_gates`,
   `regressions_block_pass`). Our criteria 9 (prices match), 11 (ingredient accuracy) and the price-association part of 3
   and 14 must become pass/fail gates, as must text contrast and `environmental_legibility`.
2. **Do not optimize one number.** `no_single_average` asks for independent tracking of about 12 qualities. Our three
   averages are single aggregates; keep them for the database gate, but critics must also report per-dimension scores and
   a delta against the best checkpoint.
3. **Keep the best checkpoint and allow reversion.** Our loop always moves to the newest version. The KB
   (`revert_allowed`, `iterate_with_reversion`, `revision_hypothesis_test`) requires: state a hypothesis before each
   revision, compare to the best prior round dimension by dimension, and revert failed changes. The cantina round 3 case
   is exactly the drift it warns about.
4. **Critics must penalise accumulation, not only reward boldness.** Our criterion 7 rewards "design elements that
   elevate it" and criterion 15 rewards a "bold" idea, and the protocol tells critics to name "the single boldest idea
   missing". The KB found this pushed the cantina into device accumulation (`cantina_round3_cards`). Add
   `restraint_quality`, `salience_control` and a device-subtraction check: each critique should also name one device to
   remove.
5. **Creative thesis is mandatory.** Before rendering, the designer writes a one-sentence creative thesis, 4-7 concept
   words and an avoid-list (`creative_thesis_required`, `fix_generic_menu`). Our scorecard has no such step.
6. **Sweet-spot placement is rejected.** Our criterion 5 says "best sellers and high-margin items in the prime spots".
   The KB (`reject_sweet_spot_claim`, `menu_sweet_spot_skepticism`, `attention_not_purchase`, `separate_attention_sales`)
   says there is no universal prime spot and attention is not sales. Reword: emphasise items by hierarchy and grouping,
   and never score a placement as a revenue gain without POS evidence; consider substitution.
7. **Empty space is not automatically good.** Casa Luna passed our 80 bar with large unused lower fields. The KB
   (`whitespace_relational`, `fix_dead_space`) scores content underflow as a failure.
8. **Far-right price columns are not automatically good.** Our criterion 3 rewards "prices in one right-aligned column".
   The KB (`fix_remote_prices`, `price_association`) says a remote right edge weakens association unless the row grid is
   strong (leaders, rules, short measure). Measure eye travel, not only alignment.
9. **"Measured correctly" is necessary, not sufficient** (already in our protocol) and the KB agrees (`casa_luna_*`
   lessons). But the KB also wants the measurement done first (`measure_then_interpret`, `visual_tests`), while our fast
   protocol forbids re-rendering and Playwright. Move the automatic tests in section F into the render script so
   `layout.json` carries them, and the 90-second critics read the results.
10. **Cultural references need provenance.** Criterion 13 checks Spanish use; the KB goes further (`global_reference_context`,
    `literal_motif_budget`, `cultural_context`): document each Mexican-coded motif's source and function, cap literal
    category symbols (keep one or two), and abstract the rest.
11. **Critic independence.** All our critics are the same model with similar prompts. The KB (`critic_independence_check`,
    `critic_consensus_not_truth`) asks us to record critic model and rubric and to separate perceptual, functional,
    art-direction and commercial lenses. Our three lenses partly do this; agreement alone should not raise confidence.
12. **New checks we do not have:** logo-off test, grayscale test, blur/thumbnail salience, device subtraction, image
    substitution, environmental legibility (dim light, glare), reverse-type and texture-at-size checks, bleed and
    effective resolution for full-bleed art, and colour output (gamut, metallic/foil) proofing.
13. **Where our scorecard goes beyond the KB:** ingredient sourcing and description accuracy (criteria 8, 11, 12), venue
    type and demographics (13), exact price matching (9) and the layout geometry contract (section 3) are PHG-specific and
    stay. The KB has no numeric margin/contrast thresholds of its own; keep our 4.5:1 and ±mm tolerances.

### Top instructions for editorial, art-directed menus
(full-bleed illustration, collage, tracked caps, vertical wordmarks, textured stock, gold-leaf accents)

1. Write the creative thesis, concept vocabulary and avoid-list first; every device must trace to it (`creative_thesis_required`, `concept_before_decoration`).
2. One illustration or collage grammar: line, perspective, detail range, grain, crop and colour mapping (`illustration_family_grammar`, `image_treatment_system`, `collage_unify_theme`).
3. Type and image must interact (reinforce, contrast, extend); pass the image-substitution test (`word_image_synthesis`, `word_image_integration_pass`).
4. Crop full-bleed art on purpose: look room, gaze toward the menu content, bleed past trim, text in the safe area (`crop_with_intent`, `bleed_prevents_edge_slivers`, `safe_trim_content`).
5. Keep expressive type (vertical wordmark, heavy tracking, rotation, cropping) in display roles; item names, descriptions and prices stay conventional (`expressive_type_boundary`).
6. Tracked caps only for short labels, with tracking opened for caps; never long passages (`case_has_cost`, `type_texture_audit`).
7. Type over illustration or texture needs a stable backing field and must pass contrast at its worst pixel; reduce texture contrast near text (`accessibility_contrast_gate`, `texture_reproduction_test`, `figure_ground_clarity`).
8. Textured stock and grain must be tuned to actual size and be conceptually justified, not generic fake texture (`materiality_supports_voice`, `texture_needs_scale_fit`).
9. Gold/metallic accents: scarce accent role only; they cannot be reproduced in RGB, so specify foil/spot and proof under venue light; keep them off small or reversed text (`accent_requires_scarcity`, `gamut_output_dependency`, `metamerism_proof_lighting`, `reverse_type_needs_care`). The KB does not mention gold leaf by name; this applies its colour and production principles.
10. Maximalism needs quiet zones and one clear focal order; then subtract 25% of devices and keep only what earns its place (`maximalism_needs_quiet`, `controlled_maximalism_pass`, `fix_overdecorated`).
