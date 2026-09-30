# PHG Design Intelligence — Audited Status + Controlled Benchmark Plan

Version 2026-09-28.3 (adds script-03 results) · for Rob Sloma · responds to handoff 2026-09-28.1 (FIRST DELIVERABLE)
Project: lqjtwabzmgjcufftuqvu (older robsloma@gmail.com's Project). Schema `phg_design`.
**No writes, grants, migrations, paid renders or deploys were made for this audit.** Every figure below came from read-only `SELECT`s / read-only function calls run today by this agent. The handoff's D-01 note ("fresh count blocked") is now resolved: the query ran under this session's authorised connector; no security gate was bypassed.

Evidence classes used: **[DB]** = queried today · **[FILE]** = repo file hash/listing today · **[PREF]** = Rob's stated preference · **[INF]** = PHG inference, unverified.

---

## 1. Audited status

### 1.1 Knowledge-base counts [DB] — historical checkpoint CONFIRMED

| table | rows | note |
|---|---|---|
| sources | 37 | list reconciled in §1.4 |
| concepts | 316 | |
| principles | 187 | only **43** have ≥1 source link (23%) |
| variables | 192 | |
| decision_rules | 69 | `rule_principles` = **0** → no rule is linked to a principle |
| rubric_dimensions | 58 | 11 `hard_gate = true` |
| validation_tests | 60 | table has procedure/measures/pass_logic columns only — **no results table exists**; these are definitions, never executions |
| principle_sources | 49 | cover 43 principles from 22 of 37 sources; 15 sources support nothing |
| case_studies | 7 | **all 7 `artifact_ref` = NULL** (D-14 confirmed) |
| agent_guidance | 11 | none mentions ingredient ordering |
| brief_profiles | 2 | `cocktail_menu`, `mobile_menu` |
| relationship_types | 10 | |
| palettes, typography_profiles, composition_profiles, critiques, revision_decisions, visual_objects, visual_relationships, ingestion_runs | **0** | empty scaffolding |

The "938 structured records" total is arithmetic over eight tables, not 938 findings. The 612 / 184,320+ / 68% infographic figures have no DB basis. **Retired.**

### 1.2 Gateways and access [DB]

| function | exists | security | execute granted to | behaviour checked |
|---|---|---|---|---|
| `public.phg_design_knowledge(domain, query, limit)` | yes | DEFINER, owner postgres, `search_path=phg_design,pg_temp` | authenticated, service_role | returns rows. Match is lexical ILIKE, not semantic |
| `public.phg_design_packet(profile_key, query, limit)` | **yes** (D-15 → exists) | DEFINER, same search_path | authenticated, service_role | returns `{profile, rubric, principles, decision_rules, benchmark_cases, validation_tests, required_preflight}`. **Defect:** an unknown profile key (`no_such_profile`) still returns a full packet with no error, so a typo silently yields generic guidance |
| `public.phg_designer_query(sql, max_rows, task_id)` | yes | INVOKER, `search_path=public,phg,pg_temp` | postgres, service_role | the designer's path. It **cannot see `phg_design`** |

- **RLS is OFF on all 21 `phg_design` tables.** Schema USAGE is held only by postgres / supabase_admin / read_only / etl. anon and authenticated have none, so the tables are not API-reachable directly. Exposure is via the two DEFINER gateways, which any *authenticated* user can call. The knowledge is non-tenant data, so this is low risk. It is still not "hardened" (D-05 stays open, downgraded to P1).
- **Integration (D-02):** no code in this repo calls `phg_design_packet` or `phg_design_knowledge`; the only textual hit is the flavor handoff doc. `phg_design_task_create/proposal_submit/review` exist but take no packet input. **The production designer does not retrieve design knowledge today.** In TEST-1 the KB reached designers only because I pasted doctrine into their prompts (DESIGN_THEORY_BRIEF.md). That is a manual bridge, not an integration.

### 1.3 Ingredient display order (D-04) [DB]

- `phg.recipe_components` has 0 rows. Ingredients live in `phg.recipe_versions.ingredients` (jsonb: name, quantity, unit, kind, role).
- The 18 stored ingredient rows carry free-text roles: Base spirit 4, Citrus 3, Bitters 2, Liqueur 2, Sweetener 2, Fortified wine 1, House prep 1, "House prep / base spirit" 1, "House prep / sweetener" 1, Garnish 1.
- **Rob's order (base → modifier → sweetener → citrus → bitters → soda → other; garnish/ice separate) is NOT persisted anywhere**: no rank column, no mapping table, no guidance row, no principle.
- Roles are usable but inconsistent: compound "House prep / x" values, and Garnish sits inside `ingredients` even though `recipe_versions.garnish` exists.
- **Proposed** (not applied; needs your approval): a `phg.ingredient_display_roles(role_key, rank)` lookup, a normalised `display_role` per ingredient element, and a render-side sort. Mixing order is untouched.

### 1.4 Source register reconciliation [DB vs handoff]

All 37 DB titles were read today. They are 14 books, 8 web resources/archives (AIGA, Fonts In Use, Letterform Archive, Google Fonts Knowledge, HIG, Material, MIT 6.831 page, Design Teaching Resource), 1 journal (Design Issues) and 14 menu/consumer-research papers.

- "Interaction of Color" appears twice, as print and as Complete Digital Edition. That is two editions, not a duplicate error, but they should be aliased (D-10).
- The 50-entry and 20-entry lists were **not** in the uploads (files 02, 04, 05 and 09, plus visual_examples/ and media/, are missing). Line-by-line reconciliation is blocked until they arrive.
- **Provisional reconciliation from the lists in 00 §3.2** (file 02 has not arrived, so this is by title only):
  - **In both the lists and the DB (≈20):**
    - MIT Art of Color, Media and Methods, Digital Typography
    - New Basics, Primer of Visual Literacy, Graphic Design Manual, Interaction of Color (×2 editions)
    - Thinking with Type, Elements of Typographic Style, Grid Systems, Ruder (*Typography: A Manual of Design* = *Typographie*), Designing Programmes, Vignelli Canon, Tufte VDQI
    - Google Fonts Knowledge, Letterform Archive, Fonts In Use, AIGA Design Archives, Design Issues
    - HIG, Material; W3C WAI ≈ "Designing for Web Accessibility" (to verify)
  - **On the lists, not in the DB (≈30):**
    - courses and centres: Yale S131, CalArts, BCcampus, RIT Vignelli Center, Cooper Union Lubalin
    - books: Arnheim, Tschichold, Rand, Munari, Hara, Armstrong, Wheeler, Pater, Meggs, Berger, Lupton *Design Is Storytelling*, Tufte *Envisioning Information*, Munzner
    - web sources: Butterick, Letterform Toolkit, Emigre, PGDA, Cooper Hewitt Bauhaus, Eye, Design Observer, readings.design
    - journals: Visible Language, Dialectic
    - applied systems: IBM Carbon, Atomic Design
    - other professional-list entries: Brand New, BP&O, Eye on Design, Communication Arts, D&AD, TDC, Typographica, Dieline, It's Nice That, Creative Review
  - **In the DB, not on the lists:**
    - *Introduction to Graphic Design*, *Visual Communication Fundamentals*, Design Teaching Resource, *Digital Color Composition*, MIT 6.831 activity page
    - the **9 menu-research citations**, which matches the handoff's "nine"
- `ingestion_runs = 0` means no source has a logged read or extract. Reading completeness is "unknown", not "partial" (D-07).

### 1.4b Results of handoff script 03 (groups 1–9, run read-only 2026-09-28T14:26Z as `postgres` via the Supabase connector)

- **G1** — every object exists: `v_knowledge_counts`, `brief_profiles`, `phg_design_knowledge`, `phg_design_packet`.
- **G3** — the view returns 37 / 316 / 192 / 187 / 7 / 69 / 49 / 60 / 58, with `structured_knowledge_records` = 938. This matches the checkpoint exactly.
- **G4** — all 37 sources have `access_status = 'reference'`. Not one is marked acquired, read or blocked, so reading state is not recorded at all (D-07). Every source has a creator filled in; accuracy is unchecked (D-09).
- **G5** — **all 69 decision rules have no principle link.** 144 of 187 principles have no source link.
  - Principles *claiming* empirical or standard evidence but with no source: perceptual_research 7/13, academic_research 3/10, production_standard 3/3, technical_standard 1/3, human_factors 2/2, color_science 2/2.
  - These 18 rows are the highest-priority provenance repair: each needs a citation or reclassification to `phg_synthesis`.
- **G6** — `ingestion_runs` = 0. Cases 7/7 have `artifact_ref` NULL. visual_objects, visual_relationships, palettes, typography_profiles, composition_profiles, critiques and revision_decisions all have 0 rows.
- **G7** — ingredient-order rule: **no match** in agent_guidance (the only hit is `hard_gates`) and none in decision_rules. The 6 matching rules (fix_remote_prices, responsive_menu_recompose, audience_specific_menu, numeric_column_figures, menu_item_block_spacing, expressive_type_boundary) cover price and description layout, not ingredient role order. **D-04 confirmed: not persisted.**
- **G8** — 0 RLS policies and 0 forced-RLS tables. Table grants go to `postgres` only. Gateways: DEFINER, owner postgres, pinned `search_path`, EXECUTE to authenticated + service_role.
- **G9** — `evidence_class` has **33 distinct uncontrolled values** across 187 principles (e.g. professional_education 24, phg_synthesis 21, design_theory 16, typographic_practice 16). This needs a controlled vocabulary (D-11).
  - No duplicate concept names by normalised string. Overlaps are semantic, not lexical (D-10).
  - Flagged variables include `value_difference` vs `luminance_contrast_ratio`, `chroma_difference` vs `image_mean_saturation`, `cielab_delta_e` (formula unspecified), `center_gravity_x/y` vs `visual_mass_x/y`, `corner_distance`, and `reading_order_confidence`. Each needs a unit, estimator and coordinate frame before any value is reported (D-12).
- **G10–G11** — the gateways were called with test queries and returned data (§1.2). A full packet dump was not saved.
- **G12** (full export) — **not run.** The export would pass several hundred KB through the connector. I'll run it into a dated repo snapshot if you want a portable checkpoint. It is read-only either way.

### 1.5 TEST-1 (Iowa City cantina) design loop [FILE + scores/NOTES.md]

| artifact | letter preview sha256 (first 12) | full panel (critic / content / accuracy / combined) |
|---|---|---|
| round-17 (best checkpoint) | 4c13a4f8b996 | 74.0 / 77.8 / 70.5 / **74.1** |
| round-19 (KB content wins) | 98c4e83423f4 | 70.9 / 77.0 / 62.3 / 70.1 |
| explore-I5 | — | 71.2 / 74.0 / 65.1 / 70.1 |
| round-20 | building | — |

- No design has cleared 80 on all three reviewer types.
- Accuracy is capped by missing service data (beer style/ABV/brewery, wine grape/region, spirit brand/pour), not by layout.
- Measured reviewer noise is ±5 for a single reviewer; 3-reviewer screens overstated by about 4.
- These are LLM-panel scores: useful for regression, **not** independent validation.

### 1.6 The Last Round [FILE 08]

The transcription only. The two source rasters are not in the uploads, so I cannot hash or re-inspect them (D-19 stands).

---

## 2. Corrections, separated

### 2A. Factual / content corrections (no design change; need Rob or beverage-owner sign-off)

**The Last Round (from 08, "as displayed"):**

1. "a touch of magic" is listed as an ingredient in The Fellowship. It is not an ingredient; remove it or name the real one.
2. "Second Chance" is used twice: a $12 cocktail and a $6 NA drink. One name → two products; rename one.
3. "zero-proof spritz" is a category, not ingredients. Its components are unknown.
4. Vague components: "citrus" (Sorcerer's Apprentice, Safe Passage), "spice" (Chosen One), "herbs" (Ring Bearer). Specify each or mark it unknown.
5. Activated charcoal (The Dark Lord) has a known absorption interaction with medications, and some jurisdictions restrict it in food service. Needs an owner decision.
6. Ingredient order does not follow Rob's rule. For example, Fellowship should read gin → elderflower → honey → lemon; Sorcerer's should read rum → blue curaçao → coconut/pineapple … citrus. Reorder only after the roles are confirmed.
7. Descriptions are thematic taglines ("Destiny tastes familiar."), not sensory. The item stack needs a 3–5-word sensory line per drink, sourced from the recipe.
8. Beer and wine carry invented names only: no brewery, style/ABV, producer, region or pour. Do not infer them (per 08 cautions).
9. Scope conflict: an earlier plan had 20 tequilas / 12 beers / 8 wines; the current version has 10/6/5/6 (D-20). Rob decides.
10. Third-party IP names (Fellowship, Ring Bearer, Mithril, Rivendell, Gondor, Isengard, Mirkwood, Shire, Volturi, Breaking Dawn, Jumanji, Dark Lord/Chosen One adjacent) are **not cleared** (D-18). This is a rights decision, not a design one.

**TEST-1 cantina:**

- beer/wine/spirit service facts
- Brut Rosé glass vs bottle
- Brown Butter OF dairy allergen
- venue name "Cantina" (no Mexican items in the draft)
- Manhattan bitters display (needs_input 11)
- Junmai Ginjo retired (confirmed; omission is correct)

### 2B. Visual redesign (no content change)

- Concept-governed composition: the reading path is part of the art, per the handoff's quest-landscape and leaf ideas. It must not be a themed background behind rows.
- Two layers: generated or drawn art underneath, exact editable HTML text on top. No menu text is ever rasterised by an image model.
- Small drink glyphs must show the real glass, colour, ice and garnish from `recipe_versions`, not generic icons.
- Item stack: name + price, then the sensory line in a contrasting face, then ingredients in role order.
- Accent ≤6% of area. At least one structural quiet field. Legibility gate at actual size, with phone labels ≥ 12 px.
- Craft ceiling: code-drawn art has read as sunburst, confetti and gravel. Raster art needs the Canva download hosts allowed in the environment's network policy (still blocked), or supplied assets.

---

## 3. Rob's aesthetic preference — recorded as preference [PREF]

- Rob prefers the developed fantasy/expressive Last Round designs over the originals.
- For TEST-1 he rejected the r17/r18/A–F set as "atrocious" and asked for radical structural variation.
- He favours concept-driven geometry, a single gesture, restrained ink, and descriptions + ingredients present.

This is **one stakeholder's judgement**. It governs what we build for Rob, but it is **not** evidence that the designs perform better for guests. No blind, calibrated or audience test has been run (D-26). The benchmark below keeps his vote in a separate field and never pools it with panel scores.

---

## 4. ONE controlled benchmark

**Question:** Does design knowledge retrieved from `phg_design` (via `phg_design_packet`) produce better menus than the same designer without it, holding content, format and art tooling fixed?

**Brief:** TEST-1 Iowa City cantina, the 14 approved items. I chose it because its content is fixed in the DB (`phg.menu_items` status approved; Junmai Ginjo retired). **Correction (2026-09-28): every item carries `metadata.beta_seed/sample_content = true`. It is seeded sample content, not a real venue's menu.** That is fine for a controlled benchmark, where the only requirement is content locked across arms, but results say nothing about a live menu. The Last Round content is still unapproved (§2A), so it would confound content errors with design quality. The Last Round becomes benchmark #2 once §2A is signed off.

**Locked inputs:**
- content manifest JSON (names, prices, descriptions, ingredients in role order), sha256 recorded before any generation
- formats: letter 2550×3300 and phone 1170 wide
- same fonts licence pool
- code/CSS art only in all arms: no paid renders and no Canva, so art craft is held constant

**Arms:**

| arm | designer input |
|---|---|
| A — baseline | brief + manifest only |
| B — KB-assisted | brief + manifest + `phg_design_packet('cocktail_menu', …)` output, logged verbatim with the packet hash |
| C — reference | round-17 as-is (current best checkpoint, hash 4c13a4f8b996…) |
| D — reference | Rob-preferred direction. Proposed: **Solstice** structure (comparison-artifacts/ref-solstice.png), rebuilt on the locked manifest with exact HTML text. Pending Rob's confirmation |

- Arms A and B each produce 3 structurally different proposals (silhouette corr < 0.8 via `visual_tests.py`).
- The best of each is picked by a deterministic gate pass only, not taste.

**Hard gates, run deterministically before any judging.** A failure disqualifies the proposal.
1. Text diff: rendered DOM text equals the manifest (every item, price and ingredient; no additions).
2. Price pairing: each price sits within 1 em of its name on the same baseline group.
3. Contrast: measured text/background pairs meet WCAG 2.2 1.4.3; non-text 1.4.11 where the art carries meaning.
4. Actual-size legibility: letter ≥ 8.5 pt body; phone ≥ 12 px.
5. Ingredient order matches role ranks.

**Judging:**
- Blind pairwise: B vs A, B vs C, A vs C, and D vs the winner.
- Files are renamed to random IDs and the left/right order is swapped for half the judges.
- 10 fresh LLM judges per pair who have never seen TEST-1 history, split 5 design-critic / 5 content lens.
- Each judge picks a winner + one observed-evidence reason. No 0–100 scores, which avoids the ±5 noise.
- Optional human arm: 5–10 people choose "which menu would you order from faster/happier", with time-to-find a named drink and price.

**Pre-registered decision rule:**
- **B beats A** if B wins ≥ 7/10 blind judgements *and* passes all gates.
- 6/10 is a tie, meaning the KB adds nothing measurable at this N.
- Anything else means the KB is not helping and the retrieval or packet needs work before more ingestion.

**Logged outputs** go to `handoff/design-intelligence/benchmark-1/`:
- the manifest hash, packet hash and every PNG hash
- judge prompts and raw JSON
- gate results
- a separate `rob_preference.json`, kept out of the win count

**Cost:** about 6 designer runs + about 40 judge runs, all within the existing agent budget. No paid media, no DB writes. Recording to `phg_design.critiques` or `case_studies` would be a write and waits for your approval.

**Needs from Rob before the run:**
1. OK to run it. It has zero production impact.
2. Confirm Arm D = Solstice structure (see comparison-artifacts/COMPARISON_AUDIT.md), or name another.
3. Whether to include the human arm.

---

## 5. Remaining open items (from handoff 07, re-statused)

| id | status |
|---|---|
| D-01 | closed. Audit ran read-only. |
| D-02 | confirmed gap. No generation path calls the KB. |
| D-04 | confirmed gap. Order not persisted; migration proposal pending approval. |
| D-05 | P1. RLS off, no API schema exposure, DEFINER gateways open to any authenticated user. |
| D-06 | 144 of 187 principles unsourced. |
| D-13 | no results table exists. |
| D-14 | 7/7 cases without artifact. |
| D-15 | exists and works. New defect: unknown profile does not error. |
| D-03, D-07 to D-12, D-16 to D-26 | open as filed. |

**Missing from the handoff upload:** 02 source register, 04 count checkpoint, 05 proposed contract, 09 media manifest, visual_examples/ (17 images), media/ (MP4/M4A/report). Please re-attach them if you want the 50/20 source reconciliation and the image-level Last Round comparison.
