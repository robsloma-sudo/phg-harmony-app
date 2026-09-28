# PHG DESIGN INTELLIGENCE — MASTER ROLE AND PROJECT HANDOFF

**Version:** 2026-09-28.1  
**Prepared for:** Robert “Rob” Sloma and the receiving graphic-design/development agent  
**Project:** Perfect Harmony Group (PHG)  
**Scope:** research, design theory, visual art direction, menu design, critique, Supabase knowledge architecture, generative artwork, promotional video, narration, and delivery  
**Authority:** this document transfers the work and operating method, not model weights or a claim of universal mastery.

## 0. Read this before doing anything

Rob wants you to assume the design-research and creative-director role, not simply summarize this document. He values the visual results developed in this conversation more highly than his other agents’ menus and wants that capability made portable. Preserve the ambition and the specific visual lessons, while independently checking the database, sources, files, and production claims.

**The central creative lesson is: make the concept govern the composition, not merely decorate a generic menu.** A garden should influence how sections branch and grow; a fantasy quest should influence the reading path and the location of drinks in the landscape. But names, prices, ingredients, and useful descriptions must remain complete and readable.

### Evidence and status notice

A fresh read-only Supabase count query was attempted while preparing this handoff. The tool blocked the call because it could not determine the request’s safety status. No data was returned and no database change was made. Consequently, the database figures below are the **last successful checkpoint returned in this conversation**, not a new live audit. Use the supplied read-only audit script through an authorized connection before relying on them operationally.

The original 50-entry research file was reopened in full for this handoff. It explicitly distinguishes cataloging and selected public reading from completing books or courses. The final menu images, narrated MP4, silent MP4, audio files, and media verification report were also inspected or checked locally. Selected public sources were rechecked for the evidence appendix; these checks do not constitute wholesale course or book ingestion.

Do not repeat previous claims of **612 resources, 184,320+ extracted data points, or 68% overall completion**. Those appeared in generated infographics without a supporting inventory and are not valid project metrics. Likewise, “hundreds of principles” does not establish that hundreds of studies were read, and a `validation_tests` row does not mean a test was implemented or run.

## 1. Mission and role boundaries

Build an evidence-aware design practice that can research, reason visually, originate compelling directions, execute, compare alternatives, preserve content, and hand off implementable artifacts. PHG remains a beverage-focused analytics and consulting platform; do not recast the whole company as a fantasy tavern, hospitality operator, or cocktail-inspiration site.

The receiving role combines:

- **Research librarian and evidence editor:** discover authoritative resources, record access and rights, inspect actual content, and preserve claim-level provenance.
- **Visual analyst:** describe geometry, color relationships, typography, imagery, hierarchy, density, depth, material, and object-to-object relationships.
- **Creative director:** turn a brief into a generative idea, choose meaningful influences, create structurally different directions, and direct abstraction and imagery.
- **Menu designer:** protect item names, descriptions, prices, categories, service facts, reading order, and ingredient-display conventions.
- **Design critic and experiment designer:** separate observable defects from taste; formulate revision hypotheses; compare against the best prior version; retain or revert deliberately.
- **Knowledge architect:** extend the existing PHG design schema, not a disconnected replacement; expose useful retrieval packets to the established agent.
- **Production and media coordinator:** create final-size deliverables, stage cinematic shots, manage sound and narration, verify exports, and distinguish plans from finished files.

These are transferable responsibilities and methods. This package is not an export of private reasoning, a fine-tuned model, or a guarantee that another agent will immediately reproduce the same quality. The receiving agent must use the references and critique loop in actual visual work.

## 2. Rob’s binding preferences and working style

### 2.1 Creative direction

Rob repeatedly pushed beyond polite, generic, well-aligned menus. He asked for beautiful, abstract, emotionally strong, highly imaginative design, sometimes with lush or extreme density. He wants broad creative range, not one signature palette reused everywhere.

“More abstract” in this project usually means **more integrated and spatially transformed**: items positioned along branches, ruins, portals, paths, rivers, or other structures; glass illustrations acting as objects in the world; and category structure expressed by the artwork. It does not mean making the content illegible or throwing text randomly across an image.

He requested dramatically different options: cosmic, garden, classroom, back alley, punk/rock, sunset indie, romantic glasshouse, haunted jungle, heavy metal, and epic fantasy. A variant is not meaningfully different merely because its background changes from cream to navy.

The hidden-garden and horror directions were specific briefs, not a permanent house style. Never carry “The Bistro,” “Cantina,” or an earlier visual identity into an explicitly new concept unless requested. This happened once and Rob corrected it.

### 2.2 Content and presentation

Preserve descriptions and prices. Generated artwork repeatedly omitted or altered them; that is a defect, not creative freedom.

The required item stack is:

**Cocktail name + price**  
*Short sensory description in a visibly different type treatment*  
Ingredients

The description belongs **between the name and the ingredients**, not beneath the ingredients. Rob’s dictated request mentioned “up to five-letter description sentences”; the workable interpretation used here is a short phrase of roughly three to five **words**, not a five-character limit. Treat that as an interpretation, not an exact re-quotation.

The phrase should communicate flavor, aroma, mouthfeel, or experience. “Bright citrus, soft herbal finish” is more decision-useful than a purely atmospheric label such as “mystical and dangerous.” Do not assert tasting results that have not been tasted; label draft sensory descriptions accordingly.

Rob asked for small illustrated drink “emojis” beside every item so guests can anticipate the glass, color, ice, and garnish. These should be purposeful mini-illustrations, not arbitrary symbols. An attractive fantasy vessel is not proof that the actual service vessel exists.

He requested removal of these filler lines: “Beauty lives here too”; “Sip at your own risk”; “Plants, People, Pours, Possibility/Possibilities”; and “Adventure tastes better together.” Do not reintroduce them. He selected the principal line **EVERY ROUND TAKES YOU FURTHER IN.** Later generated images drifted into additional unapproved slogans; preserve the selected line and avoid filler creep.

### 2.3 Ingredient order

Normalize the intended display order as:

1. Base spirit(s).
2. Supporting liqueurs and alcoholic modifiers, including amaro/vermouth where they serve that role.
3. Sweetener(s).
4. Citrus/acid component(s).
5. Bitters.
6. Soda/carbonated lengthener(s).
7. Other support ingredients, with garnish and ice described separately where appropriate.

This is the best interpretation of the dictated instruction “base spirit … supporting Lacore … [sweet] … citrus … bitters … soda and other support ingredients.” Use ingredient **function within the recipe**, not a universal dictionary label, to sort. A fruit preparation may be a sweetener in one drink and a supporting juice in another. Mixed modifiers need an explicit role. Do not infer proportions or alter the mixing method from display order.

Implement it in structured data with fields such as `display_role`, `display_rank`, and a stable tie-breaker. Preserve the actual recipe, amounts, and preparation order. The visible history does **not** establish that this exact instruction was persisted in Supabase; make checking and saving it through the approved workflow a first acceptance test.

### 2.4 Delivery and coordination

Rob primarily works on iPhone and wants minimal sign-ins, copying, downloads, and manual editing. Check available tools and account authorization before promising a render. Never make him reconnect a working service merely because a tool-discovery approach failed.

Keep a Change Log and Open Issues Log. Preserve stable IDs, current source/build context, and existing approvals. Do not mutate application infrastructure, deploy, publish, expose storage, or spend generation credits merely because a broad creative brief exists. Report the specific successful write/task/output.

Do not promise continued invisible work after a response. Scheduled research or a full-time worker requires an actual scheduler/worker, authorization, and an observable queue.

## 3. Research library and actual learning status

### 3.1 What was assembled

The initial educational library contains **50 entries** with access routes and qualifications. The subsequent professional list contains **20 entries**, seven of which directly repeat an original resource. The handoff register therefore preserves all 70 list entries with duplicate links; 63 remain after only those explicit overlaps are collapsed. That is a catalog accounting choice, not 63 fully read works or 63 Supabase source rows.

The database’s last recorded source count is **37**. It includes selected theory references, institutional pages, additional education resources, and nine menu-research citations. The 50/20 reading lists and the 37 database source records are not the same inventory. Reconciling them is outstanding work.

The original research document’s access distinctions are important: a publisher page is not a full book; an archival syllabus is not a complete class; an archive portal is not every artifact in the collection. Several later batches were manually authored ontology/rule seeds, often drawing on broad design knowledge or our synthesis. Do not label them verbatim source extraction.

### 3.2 The complete foundational library, grouped

**University/institutional entry points:** MIT Art of Color; MIT Media and Methods: Seeing and Expression; MIT Digital Typography; Yale Art S131; CalArts graphic-design courses; BCcampus Graphic Design and Print Production Fundamentals; RIT Vignelli Center; Cooper Union Herb Lubalin Study Center.

**Foundations, perception, color:** Lupton and Phillips, *Graphic Design: The New Basics*; Dondis, *A Primer of Visual Literacy*; Hofmann, *Graphic Design Manual*; Arnheim, *Art and Visual Perception*; Albers, *Interaction of Color*.

**Typography and grids:** Lupton, *Thinking with Type*; Bringhurst, *The Elements of Typographic Style*; Ruder, *Typographie*; Müller-Brockmann, *Grid Systems in Graphic Design*; Tschichold, *The New Typography*.

**Systems, identity, history, and meaning:** Gerstner, *Designing Programmes*; Vignelli, *The Vignelli Canon*; Rand, *Thoughts on Design*; Munari, *Design as Art*; Hara, *Designing Design*; Armstrong, *Graphic Design Theory*; Wheeler and Meyerson, *Designing Brand Identity*; Pater, *The Politics of Design*; Meggs and Purvis, *Meggs’ History of Graphic Design*; Berger, *Ways of Seeing*; Lupton, *Design Is Storytelling*.

**Information design:** Tufte, *The Visual Display of Quantitative Information* and *Envisioning Information*; Munzner, *Visualization Analysis and Design* with its UBC companion material.

**Online education and criticism:** Google Fonts Knowledge; Butterick’s Practical Typography; Letterform Archive Online Archive; Letterform Type History Toolkit; Fonts In Use; Emigre Essays and Interviews; People’s Graphic Design Archive; Cooper Hewitt Bauhaus Typography at 100; Eye; Design Observer.

**Journals:** Design Issues; Visible Language; Dialectic.

**Applied systems:** W3C WAI; Apple Human Interface Guidelines; Material Design; IBM Carbon; Brad Frost’s Atomic Design.

The 20 professional references are AIGA Design Archives, Letterform Archive, Fonts In Use, Brand New, BP&O, Eye, Design Observer, AIGA Eye on Design, Communication Arts, D&AD, Type Directors Club, Typographica, Google Fonts Knowledge, Thinking with Type’s companion, The Dieline, It’s Nice That, Creative Review, People’s Graphic Design Archive, readings.design, and Design Issues. URLs, overlap mappings, historical access notes, and the nine menu citations are in `02_SOURCE_REGISTER.json` and the original reference file.

### 3.3 How to study and record a source

Use a finite, versioned inventory. For a course: enumerate the syllabus, readings, exercises, lecture pages, downloadable documents, and visual examples within the chosen scope. For a book: record the exact edition and a lawful chapter/page inventory. For a continually growing archive: define a collection/query and capture date; “all of the internet” is not a useful completion denominator.

Then acquire accessible material; inspect text and actual page/artifact images; extract separate ideas; attach exact locators; record uncertainty and contrary evidence; translate relevant ideas into conditional decisions; test them on original work; and review the resulting notes. A denied, paid, missing, or unread unit stays on the coverage ledger rather than disappearing.

The proposed completion states are `discovered`, `cataloged`, `metadata_reviewed`, `content_acquired`, `text_reviewed`, `visuals_reviewed`, `claims_extracted`, `reviewed`, `blocked`, and `complete_for_defined_scope`. These states are an extension plan, not a claim that all are implemented in the current tables.

The source ledger must track both extraction and review. Do not backfill a historical “read date” for material whose reading was never logged.

### 3.4 Evidence classes and attribution

Separate empirical perception research, technical standards, historical claims, academic instruction, practitioner philosophy, professional conventions, case observations, user preferences, and PHG synthesis. The existing schema has an `evidence_class`, but its values were not normalized into one controlled vocabulary. Several entries marked “research” or “standard” require reclassification.

A high authority tier is a selection aid, not a guarantee that every sentence from that source is correct. The seeded decimal confidence values were not statistically calibrated. Treat them as author-entered editorial confidence until reviewed, not probabilities of correctness or measured effect sizes.

Every useful claim needs a claim-level citation. Linking a general MIT homepage to a detailed perception mechanism, or a book title to an unseen chapter, is not sufficient evidence. Store exact page/section/figure or timestamp and what the passage actually supports. Store disagreement rather than forcing all schools of design into one theory.

### 3.5 Rights and access

Public access does not equal unrestricted commercial ingestion. MIT OCW’s current terms specify CC BY-NC-SA conditions and explicit restrictions for AI training. Keep its material’s permission record separate from public-domain and commercially licensed sources; obtain review before using raw course content in a commercial training/redistribution pipeline [R8]. This does not mean foundational ideas cannot be discussed; it means the source material and intended use need proper handling.

For books and archives, retain bibliographic records, lawful excerpts, original analysis, and permitted reference imagery. Do not upload unauthorized full books or imply that museum images and font files are automatically reusable. Do not redistribute font binaries. Film-inspired concept images and a generated clip do not come with a documented rights clearance in this project.

## 4. What is in Supabase

### 4.1 Identity and latest recorded checkpoint

- Project display name previously confirmed: **robsloma@gmail.com’s Project** — the older project.
- Project reference: **`lqjtwabzmgjcufftuqvu`**.
- Knowledge namespace: **`phg_design`**.
- Existing operational menu namespace: **`phg`**, with public access functions already present before this work.
- Do not use GlowScape/Glowscape for this knowledge base.

Last successful `phg_design.v_knowledge_counts` response in the conversation:

| Record type | Count |
|---|---:|
| Cataloged database sources | 37 |
| Concepts | 316 |
| Principles | 187 |
| Variables | 192 |
| Decision rules | 69 |
| Rubric dimensions | 58 |
| Validation-test definitions | 60 |
| Principle-to-source links | 49 |
| Cases | 7 |
| Reported structured record total | 938 |

**938 = 316 + 187 + 192 + 69 + 58 + 60 + 49 + 7.** It includes relationship rows and case rows, excludes the 37 source rows, and is not a count of independent facts learned from online sources. It also excludes some other tables, including agent guidance and relationship types. Earlier inserts recorded 11 guidance directives and 10 relationship types, but those require a current recount too.

There are far fewer provenance links than principles. Even if every link pointed to a different principle, only 49 of 187 principles would have a link. The source-link deficit must be investigated; more glossary rows alone will not fix it.

### 4.2 Recorded table responsibilities

**Knowledge definitions**

`phg_design.sources`: stable source key, title, creator, type, authority tier, evidence class, URL, year, access status, notes, timestamps.

`phg_design.concepts`: stable key, domain, parent link, definition, measurable flag, unit/scale, flexible attributes.

`phg_design.principles`: definition, proposed mechanism, desired effects, conditions, failure modes, exceptions, evidence class, confidence, timestamps.

`phg_design.principle_sources`: many-to-many link from principle to source with support type and note.

`phg_design.variables`: variable key, domain, type, bounds, units, description, perceptual role.

`phg_design.relationship_types`: vocabulary such as aligned_with, balances, dominates, groups_with, points_toward, frames, contrasts_with, repeats, interrupts, and anchors, with directionality and proposed measurements.

`phg_design.decision_rules`: problem pattern, diagnostic signals, interventions, expected effects, validation tests, exceptions, priority, confidence.

`phg_design.rule_principles`: links between rules and principles. The visible seeds do not establish how many of these links are populated.

**Visual corpus and reusable profiles**

`case_studies`, `visual_objects`, `visual_relationships`, `palettes`, `typography_profiles`, and `composition_profiles` provide slots for examples, objects, geometry, style, relationships, color roles, type hierarchy, and composition logic.

Seven case records are evidenced by the last checkpoint. The record definitions permit an `artifact_ref`, but the displayed case seed SQL did not attach stable image references. The history does not establish a populated object-by-object visual analysis, measured palette corpus, or profile library. Do not infer that those tables are full merely because they exist.

**Critique, process, and ingestion**

`critiques`: role/rubric version, hard gates, dimension scores, observations, recommended actions, optional existing task/proposal IDs.

`revision_decisions`: prior/next iteration, problem, hypothesis, intervention, expected/actual effect, and keep/revert/mixed/pending disposition.

`agent_guidance`: prioritized instructions and rationale.

`rubric_dimensions`: definitions, hard-gate flags, weights, anchors, failure conditions.

`validation_tests`: procedures, proposed measures, pass logic, limitations. These are definitions, not an executable test suite.

`ingestion_runs`: source scope, start/end, extraction status, reviewed-unit count and counts added by record type. The visible history shows creation, not a fully backfilled source-by-source ingestion log.

`v_knowledge_counts`: count view used for the checkpoint above.

`brief_profiles` and `public.phg_design_packet(...)` were drafted/submitted in an earlier step, but the retained conversation does not show a successful completion response or a test result for that packet migration. Verify existence and behavior before using them.

### 4.3 Retrieval functions and their limits

A successful historical migration and test are recorded for:

`public.phg_design_knowledge(p_domain text default null, p_query text default null, p_limit integer default 100)`

The recorded implementation returns JSON arrays of principles, decision rules, and active guidance. It uses exact domain filtering and substring `ILIKE` matching. It clamps limits and sorts by editorial priority/confidence. It is **not semantic search**, not a vector database, and not an automatic visual reasoning engine. The first gateway does not return the full source citations, objects, palettes, case studies, tests, or rubric dimensions.

The proposed packet function includes principles with source metadata, decision rules, rubric dimensions, test definitions, benchmark cases, and a required preflight. Its draft has gaps: top-N selection can crowd out entire domains; rubric dimensions are globally returned rather than scoped; hard-gate lists in profiles may lag new dimensions; case retrieval by venue type can exclude useful mobile examples; and the query does not filter every section consistently. Treat these as review issues, not fixed behavior.

Existing public functions previously observed include `phg_designer_query`, `phg_design_status`, and `phg_design_doc_items`. Existing `phg` objects include menu design tasks, proposals, visual documents/pages, and a designer query log. Their exact live definitions and authorization model must be inspected before integrating. No new parallel menu database is needed.

### 4.4 Security

The recorded gateway is `SECURITY DEFINER`. Its execute privilege was explicitly revoked from PUBLIC/anon, then granted to authenticated and service_role. That blocks anonymous calls but does **not** by itself restrict access to a particular tenant, project, or designer. Do not call this fully hardened without verifying the owner, search path, role checks, data exposure, grants, and tests with actual agent credentials. Supabase’s official function guidance makes both definer behavior and execute privileges explicit [R7].

The displayed table migrations do not demonstrate per-table RLS policies. Schema placement alone is not a proof of security. Do not turn on/off security indiscriminately in shared production; coordinate a migration, least-privilege design, and non-owner tests with the backend owner.

Raw service keys, sync tokens, signed asset URLs, cookies, and credentials must not be copied into handoffs or browser code. This package deliberately excludes them.

## 5. Formal design knowledge developed

The following is a **competency map**, not a claim that every listed item has a reviewed primary source or implemented detector. The database contains representative seeds across these areas; the receiving agent must audit coverage and deduplicate synonymous rows.

### 5.1 Perception and Gestalt

Figure/ground, proximity, similarity, continuity, closure, symmetry, common region/enclosure, connectedness, common fate, salience, pre-attentive distinctions, visual crowding, eccentricity, depth cues, and grouping conflicts.

Useful question: does visual grouping agree with semantic grouping? On a menu, a description or price must associate with its own item more strongly than with an adjacent item. Do not assume distance alone explains every table; clear alignment and row structure can override raw proximity.

MIT’s reviewed exercise explicitly uses squint testing, visual variables, contrast, and alignment as instructional tasks [R1]. That supports a diagnostic practice; it does not establish a universal saliency algorithm or a measured revenue effect.

### 5.2 Form, geometry, and composition

Point, line, plane, shape, contour, silhouette, scale, proportion, rotation, skew, curvature, compactness, aspect ratio, layering, transparency, overlap, occlusion, frame relationships, and positive/negative forms.

Composition extends to visual axes, edge and corner distances, diagonals, centroids, optical centers, asymmetrical balance, visual counterweight, tension, tangency, density gradients, focal dominance, quiet zones, rhythm, cadence, syncopation, visual echoes, and reading paths.

Always name the coordinate system. Bounding boxes may use normalized canvas coordinates; distances should specify whether normalized by width, height, or diagonal. A corner-to-center distance can exceed 1 if both coordinates use a unit square and the distance is not diagonal-normalized. Some seeded numeric bounds need correction.

Visual mass multiplied by spatial distance is a useful design analogy, not a physical law of perceived beauty. Likewise, a low-density region may be purposeful suspense rather than wasted space. Interpret measurements against the brief.

### 5.3 Grids, hierarchy, and sequence

Manuscript, column, modular, hierarchical, compound, nested, baseline, and fluid grids; margins, gutters, fields, modules, spans, offsets, and responsive recomposition.

Use the grid to organize relationships, not to force every category into an equal-height card. Break it deliberately when the break communicates something. Assess hierarchy across scale, weight, luminance, hue, position, spacing, enclosure, image detail, and semantic importance; conflicts are not automatically wrong, but accidental contradictions need repair.

Sequence includes section transitions, pacing, navigation cues, folios, running heads, captions, cross-references, and contact-sheet evaluation. The reading path can be expressive without being unknowable.

### 5.4 Typography: macro and micro

Macro: voice, family/category selection, semantic roles, pairing, role contrast, page color, hierarchy, columns, text-image balance, scripts, localization, and display-versus-body behavior.

Micro: kerning, tracking, leading, measure, x-height, cap height, ascenders/descenders, apertures/counters, terminals/serifs, stroke stress/contrast, ligatures, optical size, optical margin alignment, overshoot, punctuation, baseline shift, numerical styles, decimal alignment, rag, hyphenation, justification, whitespace rivers, and stranded lines.

Do not confuse font weight with thick/thin stroke contrast. Do not assume all scripts share Latin baselines, punctuation, casing, or line-breaking rules. “Widow” and “orphan” labels vary in usage; record the concrete failure as a short terminal line or stranded first/last paragraph line rather than relying on a vague label.

Butterick’s line-length and spacing recommendations are practical starting ranges for many prose contexts, not mandatory recipes for every menu label, display headline, script, or device [R2, R3]. Test the actual face, size, text, and viewing context.

### 5.5 Color and material perception

Palette roles, dominant/support/accent/neutral color, hue relationships, value contrast, chroma, simultaneous/successive effects, adaptation, temperature, area ratio, adjacency, semantic color roles, image color treatment, gamut, output spaces, spot/process color, overprint, knockout, metamerism, and lighting.

The recorded seeds sometimes merge **value with luminance** and **chroma with saturation**. Normalize them before measurement. Every color difference needs a defined color space and formula; “Delta E” alone is incomplete. A palette-area share derived from pixels differs from perceived dominance and from the area of semantic objects.

There is no sourced universal rule in this project that “premium” requires a 5–15% gold accent, a particular black, or a particular emotional adjective. Treat such numbers as a test proposal only. Judge palettes inside the intended composition and output conditions.

### 5.6 Mark-making, imagery, and art direction

Brush/stroke width, pressure proxy, taper, curvature, opacity, direction, direction variance, edge softness, roughness, frequency, texture density, detail scale, gesture, and mark repetition.

Do not infer literal brush pressure or tool identity with certainty from a flattened raster. Label “handmade-looking” or “pressure-like variation” as observation; record the physical process only when known.

Imagery includes focal point, crop pressure, headroom, look room, gaze/motion vectors, leading lines, tonal range, grain, saturation, duotone/monotone treatment, edge integration, image/type semantics, collage unification, illustration-family rules, perspective, and light/shadow consistency.

High abstraction can come from cropping, scale transformations, changing materials, metaphor, double reading, shape substitution, interrupted continuity, or integrating content into environmental geometry. Merely using an arch, a sun, and botanical stock imagery repeatedly is not strong conceptual variation.

### 5.7 Identity, history, meaning, and flexible systems

Creative thesis, rhetorical purpose, audience, semantic specificity, culturally contextual signs, motifs, motif grammar, controlled variation, invariants, exceptions, logo lockups, clear space, minimum size, responsive identity, distinctive assets, and cross-media continuity.

Study conflicting approaches rather than crowning one universal doctrine. Modernist discipline, expressive grid-breaking, vernacular typography, Japanese visual thinking, cultural critique, and information clarity can all contribute in context. Letterform’s themed curriculum explicitly offers non-linear, global, material, modular, and grid-breaking entry points [R4].

### 5.8 Digital and production systems

Primitive and semantic tokens, aliasing, component anatomy, role consistency, responsive layout, reflow, state feedback, focus, selected/error/disabled/loading/empty states, progressive disclosure, and user-controlled playback.

Print concerns include bleed, safe area, trim, binding gutter, folds, creep, imposition, paper reflectance/opacity, show-through, dot gain, trapping, reversed text, halftone detail, effective raster resolution, and proofing under intended light and distance.

Do not apply print-only hard gates to digital-only work or call a flattened decorative poster accessible merely because its text can be zoomed. WCAG specifies distinct criteria with distinct scopes; preserve those boundaries and evaluate text over its actual background, not just isolated palette swatches [R5, R6].

### 5.9 Menu design and commercial reasoning

Item-block structure, name/price association, section architecture, description measure, density, choice sets, dietary/allergen communication, pour sizes, serving units, mobile adaptation, price prominence, actual viewing conditions, and atmosphere versus task clarity.

Menu engineering introduces contribution margin, popularity, choice substitution, and measured business outcomes. A visually attention-grabbing item is not automatically a profitable intervention. The checked menu meta-analysis distinguishes physiological measures from attitudes, intentions, and purchases; the eye-tracking study challenges traditional anecdotal scanpath assumptions rather than establishing that placement never matters [R9, R10].

## 6. The design method that should transfer

### 6.1 Start with a communication thesis

Resolve what the guest should understand, feel, and do; what makes this venue specific; what content is immutable; and which medium and context matter. Then write one sentence that can generate decisions.

For the eventual fantasy direction: **a menu is a living game board, and each drink is a place, encounter, artifact, or consequence along the quest.** That is stronger than “make a Lord of the Rings/Jumanji-looking menu.”

A thesis is a proposal until accepted. A named establishment, palette, menu contents, and price list remain separate from its stylistic treatment.

### 6.2 Retrieve precedents for a reason

Select a manageable group of relevant examples spanning different problems: hierarchy, type behavior, spatial integration, palette, material, and category presentation. For each, record why it was retrieved, the transferable principle, and what must not be copied. Do not describe generated study images as award-winning professional precedent.

Do not retrieve twenty near-identical reference images. Include at least one deliberate counterexample or opposing approach to break habitual solutions. A garden brief can learn from scientific plates, a climbing structure, editorial typography, and fluid geometry without borrowing a whole composition.

### 6.3 Make different structures before polishing

Create alternative compositions that remain different in grayscale silhouettes. Change reading path, hierarchy, focal location, figure/ground logic, image/type relationship, space distribution, and typography behavior—not only the hue and font.

Useful separation axes: dense versus sparse, organic versus geometric, symmetrical versus off-axis, representational versus nonrepresentational, pictorial versus typographic, monumental versus intimate, archival versus contemporary, material versus luminous, quiet versus confrontational. Choose a few; randomizing every variable produces incoherence.

### 6.4 Integrate the world and the content

For expressive menus, create quiet reading pockets inside the artwork: stone faces, smooth mist, open water, broad leaves, glass panels, negative shapes, or light pools. The background determines where those pockets belong, while content length determines their minimum usable size.

Anchor name, sensory line, ingredient line, price, and glass illustration as one item cluster. Let the cluster move along the composition; do not scatter its components independently. Use a subtle repeated grammar so guests understand how to read even when the surface layout appears freeform.

Then connect clusters through branches, paths, rays, rivers, line direction, or repeated colors. Reading need not be a strict top-to-bottom spreadsheet, but a guest must still find the category, identify a drink, see its price, and understand its ingredients.

### 6.5 Use abstraction with content locks

Interpret Rob’s “75% more abstract” as a strong directional request, not an auditable 75% metric. Define observable changes instead: remove visible card borders; replace uniform rows with staggered terrain-anchored clusters; let illustrated glass/forms cross environmental layers; increase the amount of scene that is not concealed by panels; preserve exact copy in vector or HTML text.

A maximalist scene can be successful. Avoid an automatic “remove all ornament” critic. Ask what each device does for identity, navigation, meaning, or emotional effect. The best subtraction is one that increases the clarity of the intended idea without erasing character.

### 6.6 Separate generated artwork from production text

The strongest workflow for accurate menus is a structured content layer plus an art layer. Generate concept art and visual elements, then set exact approved text and prices deterministically. Prefer editable SVG, HTML/CSS, or a real design document for production typography; the existing images are flattened raster concepts.

For a moodboard, small type is acceptable as a concept indication. For an actual guest-facing menu, it is not. Never validate ingredient spelling or prices from a tiny contact sheet. Inspect each full-size output and compare against a canonical content manifest.

### 6.7 Critique, revise, and preserve the best result

Every revision should declare:

`observed problem → affected goal/principle → proposed intervention → expected result → actual comparison → keep/revert/mixed`

Keep a best-known checkpoint. Later is not automatically better. Test a single disputed change when possible; acknowledge interactions when several features cannot sensibly be separated. Store not only a score but the observation and reason.

The winning output remains a user choice within hard content and usability constraints. Rob’s stated preference is direct feedback, not proof of population-wide design superiority.

## 7. Repairing the 100-round / three-critic training experiment

Rob described 100 rounds, three agents, five critiques per agent per menu, and an 80% pass threshold. The early examples were clean but generic; later ones gained identity yet accumulated repeated boxes, banners, icons, numbers, and labels.

**Our diagnosis is a hypothesis:** correlated critics or weak criteria may have rewarded conventional polish and visible decoration while overlooking brand specificity, structural variation, or content loss. We did not obtain the complete prompts, critic logs, seeds, scores, and revision histories, so we cannot establish which criticism caused each change.

Obtain those artifacts before modifying the experiment. Record model/provider/version, critic role, prompt version, source packet, image hash, and whether a critic saw other critics’ feedback. Fifteen repeated judgments from one underlying perspective are not fifteen independent expert observations.

### 7.1 Suggested critic roles

**Content and usability critic:** exact strings, item counts, prices, units, associations, accessibility applicability, output conditions, and production facts.

**Art-direction critic:** identity, thesis, concept specificity, originality, atmosphere, metaphor, coherent influences, and structural rather than cosmetic differences.

**Visual-craft critic:** macro hierarchy, typography, palette behavior, spacing, imagery, contours, edges, density, contrast, and reproduction.

Use a fourth specialist only when the brief genuinely needs one—for example cultural/script review, statistical business evaluation, or physical printing. Role labels alone do not establish independence; the evidence and process must differ.

### 7.2 Select relevant rubric dimensions

The database has 58 dimension definitions at the last checkpoint, not a requirement to score all 58 on every menu. Some overlap and need deduplication. Establish a stable small core plus task-specific dimensions. Mark irrelevant and untested criteria `not_applicable` or `not_tested`, not zero or passed.

Hard failures include missing/wrong essential content, ambiguous item-price mapping, unreadable text at intended use, and confirmed applicable production/accessibility failures. Aesthetic dimensions stay separate: concept, identity, composition, typography, color, imagery, restraint or controlled density, craft, and emotional fit. No weighted average should hide a material content defect.

Do not let a rule database become a house-style police force. High density, asymmetry, unusual type, and ambiguity can be correct in an appropriate brief. Require a demonstrated purpose and preserved functional reading.

### 7.3 Definitions versus executed tests

The 60 database tests include thumbnail, blur/squint, grayscale, logo-off identity, subtraction, actual size, price pairing, grid overlay, grouping/hierarchy matrices, edge/tangency, typographic texture/rag/rivers, localization, responsive reflow, text-spacing overrides, color-only removal, illustration and image contact sheets, gaze direction, numeric alignment, substrate/glare/light, trim/bleed/binding, raster resolution, token/state checks, critic diversity, regression comparison, and controlled ablation.

A definition becomes a real test only when it has an implementation or documented human procedure, input asset/version, applicable scope, parameters, result, limitations, reviewer, and timestamp. Automated saliency, perceived warmth, “premium,” balance, and originality must not be reported as objective measurements without a specified and validated method.

## 8. Visual evolution and what to preserve

### 8.1 Original Casa Luna / Cantina baselines

Six images were supplied even when the user referred conversationally to five. The first three Casa Luna studies used black/gold, cream/gold/teal, and navy/gold treatments. The fourth and fifth showed a Cantina & Cocktail Bar direction in wide and mobile forms. The sixth used numbered framed modules.

The first group’s weaknesses were my visual judgment: generic identity, weak use of the available format, and in some layouts long item-to-price travel. The Cantina direction had more personality and clearer grouping, but repeated enclosure and surface devices risked overwhelming hierarchy. These are hypotheses for comparison, not universal anti-grid or anti-ornament rules.

The user only explicitly described rounds one and two and an ongoing round three. A historical seed assigned a round-three label to the sixth card design. Verify that mapping rather than treating it as documented experiment lineage.

### 8.2 Cantina and Bistro

Cantina evolved through warm cream, rust, ochre, green, decorative tile/agave systems, then sunset/indie, cosmic, neon, collage, geometric, and abstract explorations. The strongest reusable lesson is to turn cultural/category cues into a coherent visual behavior, not endlessly add sun/moon/cactus/tile icons.

Bistro explored leafy editorial, dark botanical, metallic, textured, and abstract systems. Rob specifically wanted categories growing from leaves. That becomes a semantic branching structure: the leaf is not merely ornament; it becomes the category’s spatial carrier.

Some exploration boards contained ten or twenty small concepts in one raster. Treat them as directional thumbnails. They do not contain twenty production-ready menus with guaranteed legible or accurate ingredients.

### 8.3 New citrus/garden concept

The brief shifted to citrus-forward drinks, unusual fruits, novel spritzes, amari, natural wines, international spirits, locally grown herbs/garden ingredients, and crushed ice. The assistant first reused The Bistro, which was incorrect. A later independent concept became Solstice.

The lesson: when Rob asks for an entirely new concept, reset the identity deliberately while preserving only explicitly carried content requirements. Do not let convenient previous naming and palette silently control the next brief.

### 8.4 Glass garden to haunted greenhouse

A romantic hidden garden introduced glasshouses, moss, blush, sage, spring dew, wrought iron, and roses. The Glass Garden then shifted into a playful jungle-adventure Greenhouse with nostalgic flavors and themed names.

It subsequently became a dark parallel universe, horror/metal jungle, and then a unified haunted-jungle world. User-selected typography and imagery included ruins, portals, vines, creatures, warm torchlight, dark foliage, and expressive titles. There were many increasingly scenic derivatives; all should be seen as concept iterations, not a production database of approved recipes.

### 8.5 The Last Round

The accepted later identity is **THE LAST ROUND**, with **EVERY ROUND TAKES YOU FURTHER IN.** The story combines fellowship fantasy, wizard-school magic, animated magical worlds, sword-and-sorcery, gothic supernatural romance, and a cursed living board game. Heroes face increasingly dangerous encounters and villain influences.

Rob explicitly wanted these references integrated into one world, not a collage of unrelated screenshots. In a commercial next step, distinguish desired influence, licensed assets, and unresolved rights. No legal clearance was established in this work.

The front is cocktails; the back is beer, wine, and non-alcoholic drinks. Names, prices, sensory lines, ingredients, and glass cues should be embedded in the artwork with a usable invisible structure. The final raster still retains some relatively conventional back-side grouping; this is a visible limitation, not an endpoint to defend.

### 8.6 Content drift that must be corrected before service

The currently packaged front contains ten displayed cocktail entries. The back contains six beer entries, five wine entries, and six non-alcoholic entries. Earlier the user requested 20 tequila pours, 12 beers, three reds, three whites, one sparkling, one rosé, and additional options. Those quantities are not fulfilled by the packaged final raster. Confirm the intended current content scope; do not silently call the omissions approved.

Some earlier named drinks disappeared between iterations. Some recipes changed when only names or styles were requested. Some sensory lines are atmospheric rather than useful. The final displayed Dark Lord ingredients include “charcoal”; other drafts contain placeholders such as “a touch of magic.” These are not validated service specifications. A beverage specialist must reconcile edible ingredients, preparation, claims, allergen information, actual brands/availability, serving sizes, cost, and prices before use.

The image-generation pipeline also changed the approved tagline and reintroduced filler in some versions. Build a string-level audit and an explicit forbidden-copy list. Never let generated pixels become the source of truth for operations.

## 9. Video and audio: completed work, not another production promise

### 9.1 Requested creative film

A read-only cinematic promo of approximately 30 seconds: 25 seconds of the cocktail-side journey, then five seconds for the reverse menu and brand close. Dynamic camera angles, game-board opening, multi-character combat, spells, creatures, escalating environments, cocktail landmarks, and a boss climax. Narration: an older, seasoned English/British male storyteller, restrained rather than shouted. Full audio: score, environment, combat, magic, creatures, dice, glass, ice, and pours.

The user dropped the Google/Gemini branch. Do not restart it. Do not require a desktop-centric Weave/Figma setup just to continue the already generated media.

### 9.2 What actually rendered

Runway task **`4aee086f-1ec7-4203-a80c-b27093143c79`** succeeded. Its recorded settings were 30 seconds, 16:9, 1080p, native audio. It was generated with `seedance-2.5` according to the task record. Importantly, that task’s `referenceImages` array was empty: the menu was described in the prompt, not supplied as a locked pixel/reference input. Thus this is a conceptual movie interpretation, not an exact animated version of each menu detail.

The visible credit balance changed from 3,625 to 1,585 when the successful job was accepted: a 2,040-credit historical debit. This is a record of that run, not a current quote. No additional paid visual generation is indicated for the final narration mix.

The output is a rendered video, not an editable 3D scene, multi-angle interactive viewer, or exported character rig library. No 3D project files or camera-reeditable scene were delivered.

### 9.3 Narration and final mix

Four completed narration recordings were generated. Their task IDs are retained in the media manifest, not expiring signed download URLs. Final mixing was completed through an isolated GitHub Actions branch after earlier file-transfer and hosting attempts failed.

Repository: `robsloma-sudo/phg-harmony-app`  
Branch: `media/last-round-narration-mix-20260928`  
Workflow path: `.github/workflows/last-round-audio-mix.yml`  
Recorded run: `36426399337`  
Recorded artifact: `10970694602`  
Artifact expiration in the earlier response: 2026-09-29; rely on the packaged media, not indefinite Actions retention.

The mix report records original video picture preserved without re-encoding, original soundtrack retained and ducked under speech, stereo AAC output, integrated loudness approximately **−16.15 LUFS**, and true peak approximately **−1.52 dBTP**. These loudness figures come from the included verification report, not a new listening review during this handoff.

Narration placement in that report:

| Segment | Start | End |
|---|---:|---:|
| Invitation | 0.45 s | 7.48 s |
| Choice | 7.75 s | 16.594 s |
| Warning | 17.05 s | 21.053 s |
| Brand/tagline | 24.10 s | 29.787 s |

Current local metadata confirms 1920×1080 H.264 video, AAC stereo at 48 kHz, and an MP4 container duration of **30.041667 seconds**. The small frame-duration difference matters only for strict technical delivery; it is not a newly extended film.

The silent editor MP4 contains only the video stream. The M4A and WAV editor exports contain the **complete mixed audio: narration, music, and effects**, not an isolated voice-only stem. Align one of those audio files and the silent picture at time zero. Do not stack both mixed audio formats or lay them over the already narrated movie.

### 9.4 Delivery lessons

Several earlier messages said the film was imminent while no render was running, or provided separate tracks when a finished mix was requested. Do not repeat that pattern. Verify a task ID, finished status, local file existence, media streams, output duration, and successful decoding before saying “finished.”

A storyboard is not a movie. A sound-design plan is not a mixed track. A database test row is not a test run. A signed URL is not a permanent library copy. Check the actual available tool rather than asking Rob to operate a complex desktop workflow on his phone.

## 10. Receiving-agent integration contract

Use existing PHG identifiers and approval workflow. Retrieve current content, brand constraints, and source-linked principles before generation. A useful packet contains:

- Immutable content snapshot: menu/project/revision IDs, items, prices, quantities, roles, metadata, locale, and source hash.
- Creative thesis, audience, medium, intent, selected references, and forbidden carryovers.
- Domain-balanced theory and conditional rules, each with evidence status, exceptions, and exact citations where available.
- A few actual visual references and measured/observed annotations, not just prose descriptions.
- Applicable rubric dimensions and diagnostic procedures, with implementation status.
- Prior best artifact and explicit revision hypothesis.

The output should contain artifact files, a visual specification, the content manifest, applied principle/rule/source IDs, real test results, failures/unknowns, critique, keep/revert decision, and change log. Stable design IDs and values should be preserved across renderer handoff. Any missing mapping must be reported rather than replaced silently.

Suggested future object model: canvas → regions → item clusters → text/image/shape objects, plus relationships. Each measurement stores value, units, coordinate frame, method, software/model version, asset hash, confidence type, and uncertainty. Keep observed geometry separate from inferred meaning and from recommended changes.

Embeddings can improve retrieval later; they do not replace the relational knowledge model, rights records, structured content, or evidence review. The present gateway is lexical. Design an expansion against actual query tasks, not as a duplicate “AI brain” schema.

## 11. Required next work in priority order

**First: establish the truth.** Read-only reconnect and schema/count audit; reconcile the source list against the 37 recorded database source keys; inspect function definitions and privileges; check case-image references, ingestion runs, rule links, and exact ingredient-order persistence. Produce a dated checkpoint.

**Second: repair evidence quality.** Identify duplicate concepts and variables, normalize evidence classes and units, flag uncalibrated confidence, verify nine menu research citations, replace vague source links with exact locators, and keep blocked/unread resources visible. Do not delete existing IDs without an alias/migration plan.

**Third: protect menu content.** Create a canonical content manifest for the selected brief and a deterministic text renderer. Reconcile quantities, names, prices, serving sizes, recipes, and descriptions. Fix the current image’s content drift separately from its visual art direction.

**Fourth: make visual study real.** Attach durable permitted images to cases; annotate objects and relationships; store exact artifact hashes; review diverse professional precedents. Generated examples may teach process, but must not be circularly rated as proof of their own excellence.

**Fifth: instrument the receiving agent.** Make it actually call retrieval and record returned source/rule IDs, render parameters, and tests. Keep mandatory content rules even when a search query returns few creative principles. Scope dimensions to the medium.

**Sixth: run a controlled benchmark.** Same approved brief and content; baseline versus knowledge-assisted directions; same output conditions and budget; blind pairwise review; content/hard-gate audit; Rob’s preference recorded separately. Do not conclude success from an uncalibrated self-score passing 80%.

**Then: expand coverage deliberately.** Study bounded source units with a queue, versioned evidence, permission checks, and a defined denominator. Add new topics because they fill a documented gap or improve a design decision—not to hit an arbitrary row target.

## 12. Acceptance criteria for the handoff

The new agent can name the right Supabase project and preserve it; explain the distinction between reference, claim, rule, measurement, test definition, and executed result; retrieve and cite relevant evidence; follow the protected menu text/price/description contract; create at least three structurally different directions; achieve meaningful artwork integration without losing usable reading; compare revisions against the best prior checkpoint; and deliver actual inspectable files.

It must not claim all sources have been fully read, all 60 tests run, all 316 concepts unique, all 192 variables objectively measurable, every generated ingredient validated, the scene editable in 3D, the artwork print-ready, rights cleared, the receiving agent integrated, or progress “68%” without corresponding evidence.

## 13. What success should look like

The output should not merely obey more rules than the old agent. It should make more interesting, more specific, better-resolved choices—and explain those choices with appropriate evidence and an honest understanding of what remains subjective.

**Preserve the imaginative strength of the menus, add disciplined content and production control, and make every new lesson traceable enough that another agent can use it.**

## Evidence routes rechecked for this handoff

These are specific checks, not claims of complete source ingestion. Full historical URLs are in the source register.

[R1] MIT OCW, Graphic Design in-class activity: https://ocw.mit.edu/courses/6-831-user-interface-design-and-implementation-spring-2011/pages/in-class-activities/graphic-design/

[R2] Matthew Butterick, Line length: https://practicaltypography.com/line-length.html

[R3] Matthew Butterick, Line spacing: https://practicaltypography.com/line-spacing.html

[R4] Letterform Archive, Type History Toolkit Part 3: https://letterformarchive.org/news/toolkit-for-learning-type-history-non-linear-lenses/

[R5] W3C, WCAG 2.2 Quick Reference: https://www.w3.org/WAI/WCAG22/quickref/

[R6] W3C, Understanding Contrast (Minimum): https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum

[R7] Supabase, Database Functions: https://supabase.com/docs/guides/database/functions

[R8] MIT OCW, Privacy and Terms of Use: https://ocw.mit.edu/pages/privacy-and-terms-of-use/

[R9] Publisher-indexed abstract, The effect of menu design on consumer behavior: A meta-analysis, DOI 10.1016/j.ijhm.2022.103353: https://www.sciencedirect.com/science/article/pii/S0278431922002195

[R10] Publisher-indexed abstract, Eye movements on restaurant menus: A revisitation on gaze motion and consumer scanpaths, DOI 10.1016/j.ijhm.2011.12.008: https://www.sciencedirect.com/science/article/pii/S0278431911002015

[R11] Cornell repository abstract and metadata, Menu Price Presentation Influences on Consumer Purchase Behavior in Restaurants: https://ecommons.cornell.edu/entities/publication/87c48754-8c82-49c1-911c-f74da225c6e5

**Prepared in this handoff:** reference register, read-only audit queries, receiving-agent instructions, proposed data contract, evidence sample, issue/change logs, verified media manifest, and curated visual examples. **Not performed:** new Supabase writes, new video generation, production deployment, rights clearance, exhaustive source reading, or unobserved agent execution.
