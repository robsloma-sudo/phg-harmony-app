# PHG Flavor Intelligence: Lead Developer Response

Responds to: brief PHG-FLAVOR-DEV-2026-09-28.01, stored as `phg_flavor.research_documents`, document_key
`flavor-lead-developer-brief-2026-09-28`, revision 1 (53,540 chars, created 2026-09-28 06:50:10Z).
Author: PHG lead backend developer (Claude session), 2026-09-28.
Method: live database, SELECT only (execute_sql, list_migrations, list_edge_functions). I made no DDL, DML, cron,
grant, Edge Function or deployment changes, and I printed no secrets. I treated the brief as a set of claims to
check.

Section numbering: the brief puts its implemented-state claims in section 3, grants and security in section 9, and
the "Required developer response" in section 15. There is no section 16. This document answers the section-15
items in the order the lead requested.

**Status in one line.** The flavor engine is **not populated, not connected and not complete.** It is a private
catalog of 36 source records, with zero extracted findings, zero assertions and zero production-eligible evidence.
Nothing reads it from the app.

---

## 1. Confirmed live state

Baseline read at 2026-09-28 ~07:00Z against project `lqjtwabzmgjcufftuqvu`.

### 1.1 Claimed vs actual

| # | Claim (brief section) | Claimed | Actual (live) | Result |
|---|---|---|---|---|
| 1 | Migration applied (s3) | `20260928063244 phg_flavor_research_catalog_and_coverage_foundation` | Present in `supabase_migrations.schema_migrations`; 1 statement, 20,415 chars | Match |
| 2 | phg_flavor base tables (s3) | 15 | 15, all RLS enabled, 0 policies, FORCE RLS off | Match |
| 3 | phg_flavor views (s3) | 4, security_invoker | `latest_rights`, `unit_coverage`, `source_coverage`, `production_eligible_evidence`, all `security_invoker=true` | Match |
| 4 | research_documents | 5 archives + a rev-2 pointer | 6 rows (4 keys at rev 1, plus `flavor-foundation-current-handoff` at revs 1 and 2, plus this brief) | Match |
| 5 | source_catalog | 35 researched + 1 candidate (FooDB) | 36 (19 book, 4 research_paper, 3 research_database, 3 reference_database, 2 commercial_resource, 2 educational_resource, 1 ontology, 1 sensory_reference, 1 discovery_candidate) | Match |
| 6 | source_versions | 36 placeholders, not acquired | 36: 35 `metadata_only`, 1 `blocked` (CAND-001 FooDB) | Match (adds the access split) |
| 7 | rights_assessments | 36: 34 pending_review, 2 restricted; all flags false | 34 `pending_review`, 2 `restricted` (SRC-020 FlavorDB2, SRC-022 RecipeDB); 0 rows with any capability flag true | Match |
| 8 | work_items | 151 = 144 source + 7 GLOBAL | 151 = 144 (36 each of access / rights / manifest / extraction-audit) + 7 GLOBAL | Match |
| 9 | work states | 41 queued, 109 blocked, 1 done | 41 queued (36 rights + 5 GLOBAL), 109 blocked (108 source + GLOBAL/production-integration), 1 done (GLOBAL/full-coverage-policy). 144 rows `blocks_completion=true`; all GLOBAL rows false | Match |
| 10 | source_coverage | 36 rows, all `content_not_acquired`, percent NULL | 36 `content_not_acquired`, `audited_unit_percent` NULL on all 36 | Match |
| 11 | Empty tables | 0 source_units, unit_reviews, ingestion_runs, subjects, extraction_items, source_lineage, pairing_assertions, pairing_members, pairing_evidence | All 0 | Match |
| 12 | production_eligible_evidence | 0 | 0 | Match |
| 13 | change_log | not counted in brief | 6 events (schema-v1, catalog-import-v1, validation-v1, originals-preserved-v1, current-handoff-saved-v1, brief-saved-v1) | New detail |
| 14 | public.sources | 118 -> 154 | 154; the 36 flavor rows all have `under_review / manual / ad_hoc / unchecked / supporting / tier 5` and empty `allowed_hosts`. Tier-5 total is 39 (3 pre-existing non-flavor rows) | Match |
| 15 | public.cocktail_reference | 150 | 150 | Match |
| 16 | public.cocktail_specs | 449 | 449 | Match |
| 17 | public.cocktail_spec_components | 468 | 468 | Match |
| 18 | public.cocktail_spec_sources | 449 | 449 | Match |
| 19 | phg.ingredients | 6, all generated_draft | 6, all `generated_draft`, all `metadata.created_by = phg_recipe_generator_v2`, all created at 2026-09-20 13:51:04Z | Match |
| 20 | phg.recipe_versions | 6 | 6 (4 approved, 1 candidate, 1 superseded; one has `ingredients = []`) | Match |
| 21 | phg.recipe_components / prep_recipes | 0 / 0 | 0 / 0 (also prep_components 0, prep_recipe_versions 0, ingredient_products 0) | Match |
| 22 | Maple Syrup vs Pure Maple Syrup | Both exist; an ambiguity, not a merge | `maple_syrup` (6df22ecb...) and `pure_maple_syrup` (bd550a93...), both `syrup`, `oz`, generated_draft. **No row anywhere references either one**: 0 in recipe_components, prep_components, inventory, purchasing and costing FKs, and 0 recipe_versions whose JSON mentions "maple". | Match, plus a new finding: both rows are orphans |
| 23 | recipe_versions.ingredients JSON is the real ingredient data | stated | Confirmed. Also, JSON names do **not** join to `phg.ingredients` names ("Rye Whiskey" vs "Rye whiskey"; "Aromatic Bitters" vs "Angostura Bitters"; "Tequila Blanco", "Fresh Lime Juice" and others have no ingredient row) | New finding |
| 24 | Schema grants (s9) | PUBLIC/anon/authenticated have no USAGE | `phg_flavor` ACL = `{postgres=UC, service_role=U}` | Match |
| 25 | Table grants (s9) | service_role read/write, no DELETE/TRUNCATE; 5 append-only tables | `arw` on 10 tables; `ar` (append-only) on research_documents, change_log, rights_assessments, unit_reviews, source_lineage; views `r`; no `d`/`D` anywhere | Match |
| 26 | Append-only enforcement | "append-only under those grants" | Grants only. The schema has **no triggers and no functions**, so the owner (`postgres`) can still UPDATE/DELETE, and `work_items.updated_at` is never maintained automatically | New detail (feeds H3/H10) |
| 27 | Designer gateway isolation | not stated | `phg_designer.run` is owned by `phg_menu_designer` (not superuser, no BYPASSRLS, no USAGE on phg_flavor). The designer SQL gateway **cannot** read phg_flavor. `menu_designer_query_log`: 147 rows, 0 mention phg_flavor | New finding (positive) |
| 28 | Generic crawler exposure (s7) | "do not enable generic crawlers" | `public.check_scrape_target` refuses any source whose `source_status <> 'active'`, and all 36 are `under_review` with empty `allowed_hosts`. `scrape-source` cannot target them today | New finding (positive) |
| 29 | 19 rollback-only checks (s12) | passed | Cannot be verified: no persisted test file or result row exists (change_log has a `validation-v1` event only) | Unverifiable; recreate (Phase A) |
| 30 | Registry semantic checksum (s14) | 625ace3b... | Not recomputed in this pass | Not verified |
| 31 | Historical main commit (s2) | `ee278f2`, tree = index.html + netlify.toml | `origin/main` is still `ee278f2`, and its tree is still only `index.html` + `netlify.toml` | Match |

**Summary of differences.** Every numeric claim matches. The real differences are these:
- (a) Section numbering: s3/s15, not s4/s16.
- (b) The two maple rows are unreferenced orphans, and recipe JSON names do not resolve to `phg.ingredients`.
- (c) Append-only is enforced by ACL only; there are no triggers.
- (d) The 19 validation checks are not persisted anywhere.
- (e) Positive isolation facts the brief did not record: the designer gateway is walled off from phg_flavor, and the scrape guard excludes the flavor sources.

### 1.2 Authoritative backend repository and branch

| Location | Migrations | Edge Function dirs | Flavor files |
|---|---|---|---|
| `origin/main` (`ee278f2`) | 0 | 0 | 0 (index.html + netlify.toml only) |
| `origin/claude/phg-gallery-html-render-j246dy` (this branch, `ca54fab`) | 22 | 6 (`menu-capture-v2-api`, `menu-render-chat-preview`, `menu-render-worker-api`, `phg-expanded-data`, `phg-menu-corpus-browser`, `phg-menu-design`) | 0 |
| `origin/claude/menu-design-voice-inputs-pdsr9j` | 19 | 5 | 0 |
| other branches (`capture-v2-debug`, `fix/mobile-navigation-20260927`, `phg/ux-performance-cleanup-20260926`) | 0 | 0 | 0 |
| **Live** `schema_migrations` | **408** (2026-09-02 -> 2026-09-28) | **83 deployed functions** | migration 20260928063244 + seed DML |

Findings:
1. **No repository holds the complete backend.** The live history is authoritative for 386 of 408 migrations. Only
   this working branch holds any migration source, and only for the window from 2026-09-27 15:00Z onward.
2. **Migration 20260928063244 is not in any repo branch.** Its SQL survives only in
   `supabase_migrations.schema_migrations.statements`. The 36 catalog registrations, 151 work items, 6 research
   documents and 6 change_log events were loaded as separate DML and exist in **no** file (brief H10, confirmed).
3. The repo window does not reconcile with live. Of the 22 repo files, 15 match live migration names. The versions
   differ throughout, because repo files use authoring timestamps and live uses apply timestamps (for example repo
   `20260928050000_phg_designer_gateway_definer` = live `20260928001438`).
   - **7 exist only in the repo**, as pending or renamed work: `phg_menu_dedupe_one_current`,
     `phg_menu_repair_20260927` (PHG-026, not applied), `phg_menu_doc_class_v1` (~ live `phg_menu_doc_classify_fn`),
     `phg_capture_rule_review`, `phg_capture_dedupe_sibling_priority`, `phg_capture_v2_rollout`,
     `phg_menu_design_score_gate`.
   - **11 exist only live**: `phg_census_zcta_censusreporter`, `phg_menu_doc_classify_fn`, `phg_drinks_menu_cases`
     (the repo has it as a test), `phg_menu_designer_role_membership`, `phg_menu_designer_read_policies`, the five
     `phg_design_*` migrations, and `phg_flavor_research_catalog_and_coverage_foundation`.
4. Edge Functions: 83 are deployed and 6 have source in the repo. `phg-cocktail-develop`,
   `phg-menu-item-generate-v2`, `phg-harmony-reason`, `phg-language-interpreter`, `phg-command-center` and the others
   have no source in git.

**Decision.** The **authoritative source of truth today is the live project's migration history.** The
**designated backend repo** is `robsloma-sudo/phg-harmony-app`, branch `claude/phg-gallery-html-render-j246dy`.
It is the only branch with a `supabase/` tree, and it should be promoted to a dedicated backend branch (or `main`)
once Rob approves; see PHG-FLV-001. All flavor work will be committed there as
`supabase/migrations/20260928063244_phg_flavor_research_catalog_and_coverage_foundation.sql`. That file will be
**exported byte-for-byte from `schema_migrations.statements`, and never re-run**. Seed data will go in a separate
file, `supabase/seed/phg_flavor/*.sql`, as idempotent `INSERT ... ON CONFLICT DO NOTHING`.

---

## 2. What can be reused

| Existing object | Live facts | Reuse for flavor |
|---|---|---|
| `public.sources` | 154 rows; 46 FKs point to it (including `phg_flavor.source_catalog` and `source_lineage`); consumers `check_scrape_target`, `submit_observations`, `submit_menu`, `submit_licences`, `phg_trace_observations`, `phg_pl_source_activity`; views `v_category_support`, `v_unreviewed_observations`, `v_category_attribute_profile_effective` | Keep it as the single source identity (already done). The flavor side extends it through `source_catalog`, `source_versions` and `rights_assessments`. |
| `public.check_scrape_target` | SECURITY DEFINER guard; refuses non-`active` sources | Reuse as the first gate in the H1 capture adapter, and add a flavor rights check behind it. Do **not** flip flavor sources to `active` to make a crawler work. |
| `public.beverage_categories` (730), `brands` (2,374), `brand_products` (6), `spirit_lexicon` (217), `menu_item_brands` (51,659) | Beverage taxonomy and brand resolution | Beverage and beverage_style subjects should reference `beverage_categories.id` (typed column, H6). Use `spirit_lexicon` as an alias source for spirit subjects. Use `menu_item_brands` as `recipe_or_menu_cooccurrence` evidence **only** after a rights and method decision (it is PHG-derived menu data, not a flavor source). |
| `public.cocktail_reference` (150), `cocktail_specs` (449), `cocktail_spec_components` (468), `cocktail_spec_sources` (449) | Canonical cocktail specs with source links | Recipe and style subjects for drinks. Spec components give co-occurrence structure. Each spec is already attributed through `cocktail_spec_sources` to `public.sources`, which fits the provenance model. |
| `phg.ingredients` (6), `recipe_versions` (6), `recipe_components` (0), `prep_recipes` (0), `recipe_projects` (5), `recipe_evaluations` (0) | Working recipe backbone; JSON is the real data | `subjects.ingredient_id` and `recipe_version_id` already FK here. `recipe_evaluations` is the natural home for tasting outcomes (with `evidence jsonb`). It should be extended, not duplicated. |
| `phg.menu_items` (15), `phg.menu_design_tasks`, `phg.menu_design_proposals` (0) | Menu Studio draft/approve flow: `phg_design_task_create`, `phg_design_proposal_submit`, `phg_design_proposal_review`, `phg_design_take_approved`, `phg_design_mark_applied` | Reuse the proposal/approve/apply-with-revision lifecycle as the model for flavor-driven recipe proposals, including the idempotent apply with `applied_revision`. |
| `phg.claims` / `phg.evidence` / `phg.claim_evidence` (0 / 0 / 0), `phg.goals` (352), `phg.capabilities` (33), `phg.capability_executions` | Orchestrator answer lineage | Register a `flavor_evidence` capability in `phg.capabilities`, next to `source_provenance` and `cocktail_development`, so Harmony routes through the existing capability router (`phg-capability-router`). When a flavor answer is part of a goal-bound conversation, record it in `phg.evidence` with `source_kind='phg_flavor'` and `source_ref` = the assertion or evidence UUID. |
| `phg_design` schema (37 sources, 316 concepts, 187 principles, 69 rules; `v_knowledge_counts`) | A separate design-theory knowledge base with its own `sources` and `ingestion_runs` | Pattern reuse only: its bounded gateway functions `public.phg_design_knowledge(p_domain,p_query,p_limit)` and `public.phg_design_packet(p_profile_key,p_query,p_limit)`. These are SECURITY DEFINER with pinned `search_path` and EXECUTE for authenticated and service_role. **This is the model for the flavor retrieval gateway.** |
| Designer gateway `public.phg_designer_query(p_sql,p_max_rows,p_task_id)` -> `phg_designer.run` | Arbitrary read-only SQL, logged to `phg.menu_designer_query_log`, 20 s timeout, denylist, advisory unlock; `run` owned by the non-privileged role `phg_menu_designer` | Reuse the **logging, timeout, read-only transaction and dedicated low-privilege owner role**. Do **not** reuse the arbitrary-SQL surface: the brief (s9) and PHG-036d/e show that a denylist is bypassable. |
| Edge Functions `phg-cocktail-develop`, `phg-menu-item-generate-v2`, `phg-harmony-reason`, `phg-language-interpreter`, `phg-command-center`, `phg-capability-router` | Harmony and menu-development runtime (source not in git) | The flavor gateway is called server-side from these functions using the service key. No new user-facing assistant is added. |
| Frontend `index.html` (2.16 MB) | Calls 29 `functions/v1/*` endpoints, including `MDC_MENU_GEN_URL` (phg-menu-item-generate-v2), `MDC_DESIGN_URL` (phg-menu-design), `MDC_COMMAND_URL` (phg-command-center) and `MDC_LANGUAGE_URL` (phg-language-interpreter). No `.rpc(` or `.schema(` calls; no flavor or pairing calls | The integration point is the existing Menu Development card (`why_it_works` block) and Harmony command flow. No new navigation. |

---

## 3. Conflicts with the current architecture

1. **The source of truth is split (the most serious conflict).** Live has 408 migrations and 83 functions; git
   has 22 migrations (7 not applied) and 6 functions. `main` has no backend at all. Any flavor migration written
   now would land in a repo that cannot rebuild the database it targets. Brief H10 plus
   GLOBAL/backend-source-control.
2. **Two knowledge-base source registries.** `phg_design.sources` (37 rows, its own `authority_tier`,
   `evidence_class` and `access_status`) is independent of `public.sources`, and `phg_design.ingestion_runs` is
   separate from `phg_flavor.ingestion_runs`. Flavor correctly uses `public.sources`; design does not. Fixing
   design is out of scope for this workstream. But the two ingestion-run tables and two rights vocabularies must
   not be merged by accident, and a shared rights model is a later decision.
3. **The existing generator emits unsourced flavor rationale.** `phg-menu-item-generate-v2` returns
   `why_it_works.flavor_progression`, and the frontend renders it with `esc(c.why_it_works.flavor_progression)`.
   That is LLM text presented without evidence status. Under the brief's evidence policy it is
   `generated_hypothesis` and must be labelled so. It must never be written into `pairing_evidence` as anything
   else, and never cited as a source.
4. **Ingredient identity is not normalized.** `phg.ingredients` has 6 generated drafts, including 2 orphan maple
   rows. Recipe JSON names do not join to ingredient names. `recipe_components` is empty. `subjects.ingredient_id`
   FKs into this table with `UNIQUE(ingredient_id, form_key)`, which allows unlimited NULL-form duplicates. Loading
   subjects now would bind flavor evidence to unstable identities. GLOBAL/ingredient-normalization blocks subject
   loading.
5. **No account model on flavor, and a thin one elsewhere.** `phg.accounts` has 1 row and
   `phg.account_memberships` has about 1. `phg.recipe_projects` and `phg.recipe_versions` have no `account_id`.
   Flavor tables have no `account_id` or visibility. In-house tastings (`attributable_inhouse_tasting`) and venue
   recipes cannot be scoped. Brief H7; also blocks release criterion E.
6. **Typed links vs existing columns.** `phg.menu_design_proposals.evidence_document_ids` is `bigint[]` for menu
   documents, and `phg.claims.goal_id` is NOT NULL. Neither can carry flavor evidence without fabrication. Flavor
   links need new typed link tables (see H7 and Phase E), not reuse of those columns.
7. **Arbitrary-SQL gateway pattern.** `phg_designer_query` accepts free SQL. A flavor equivalent would expose the
   research corpus and rights-restricted content. The flavor gateway must be parameterized functions only.
8. **Append-only by ACL only.** There are no triggers in phg_flavor. Owner and migration paths can rewrite
   "append-only" tables, and checksum fields are not verified (H3/H10).
9. **Advisor backlog (GLOBAL/security-review-existing).** The brief records 24 security-definer views, 19
   mutable-search-path functions and anon-callable SECURITY DEFINER functions. A new flavor gateway must not add to
   that count: it needs a pinned `search_path`, explicit REVOKE from PUBLIC/anon, and its own role.

---

## 4. Hardening plan H1-H10

All objects are additive, in new migrations under `supabase/migrations/`, and first rehearsed in a
`BEGIN ... ROLLBACK` block against live (the PHG-026 rehearsal pattern) or a Supabase branch. Tests live in
`supabase/tests/phg_flavor_*.sql`, and every test is a rollback-only script that raises on failure.

| Gap | Design | Schema objects (proposed names) | Tests | Recovery |
|---|---|---|---|---|
| **H1** Trusted ingestion and access | All writes go through SECURITY DEFINER functions owned by a new NOLOGIN role `phg_flavor_writer`. service_role loses direct INSERT/UPDATE on content tables and keeps EXECUTE on the functions only. Every write function calls `phg_flavor.require_capability(source_version_id, capability)`, which reads `latest_rights` and checks decision, `valid_until`, the flag and upstream `source_lineage` restrictions. Reads recheck at serve time. | role `phg_flavor_writer`; `phg_flavor.require_capability()`; `phg_flavor.register_unit()`, `record_extraction_item()`, `record_review()`, `link_evidence()`; REVOKE INSERT/UPDATE on content tables from service_role | Insert into a `restricted` or `pending_review` version -> refused. Expired `valid_until` -> refused. Direct INSERT as service_role -> permission denied. Upstream restricted via lineage -> refused. | Grant changes are reversed by a paired down-migration (restore the prior `arw` grants). Functions are dropped with `DROP FUNCTION`. No data is touched. |
| **H2** Publication semantics | Three separate concepts. **Source completion** (the existing `source_coverage`). **Evidence quality** (per-item and per-unit review outcome). **Product release** (a new `publication_decisions` record). A finding can ship from an incomplete source only if its unit is `fully_audited` and a publication decision exists; the source label never changes. Retirement/revocation is append-only. Contradicts/conditional stances are returned separately, never summed as votes. | `phg_flavor.publication_decisions` (append-only), `phg_flavor.evidence_retirements`; new view `servable_evidence` (security_invoker), stricter than `production_eligible_evidence` (adds unit fully_audited, not retired, redistribution flag for any external display) | A missing page keeps the source short of `audited_complete_for_version` (criterion B). Contradicting evidence appears in `servable_evidence` with its stance. A retired row disappears from serve but stays in history. | The view can be dropped or recreated freely. The decision tables are append-only; revocation is a new row. |
| **H3** Version and snapshot integrity | Snapshots and manifests become immutable revisions. `source_versions` content fields are frozen by a BEFORE UPDATE trigger once `manifest_state='verified'`; a change needs a new version row. A verification worker recomputes SHA-256 from Storage bytes and writes `integrity_checks`. A hash change marks dependent `unit_reviews` stale via a new append-only `review_invalidations`. | `phg_flavor.manifest_revisions`, `integrity_checks`, `review_invalidations`; triggers `trg_source_versions_freeze`, `trg_source_units_freeze`; append-only guard trigger `phg_flavor.forbid_update_delete()` on the five append-only tables (closes the ACL-only gap) | UPDATE of a verified snapshot hash -> error. Hash mismatch -> integrity_check `failed` and the unit leaves `fully_audited` (criterion C). UPDATE/DELETE of research_documents as the owner -> error. | Triggers can be dropped by a down-migration. Snapshot bytes are covered by the H10 backup. |
| **H4** Review correction lifecycle | Keep `unit_reviews` as the append-only first two passes. Add `unit_review_rounds` (round number, any count), `review_adjudications` (disagreement, resolution, adjudicator), and a `reviewers` registry keyed to `auth.users` or an external verified identity, with an `independence_basis`. `unit_coverage` v2 uses the latest non-invalidated round and requires distinct verified reviewers plus the adjudication of any item-set difference. | `phg_flavor.reviewers`, `unit_review_rounds`, `review_item_observations` (per-item, so "same count, different findings" is detectable), `review_adjudications`; view `unit_coverage_v2` (the old view is kept) | Two reviewers with the same person behind different keys -> refused. Same count with different item sets -> adjudication required (criterion C). A correction adds a round and never updates. | Additive. `unit_coverage` v1 stays unchanged until v2 is accepted. |
| **H5** Per-finding provenance | Add a typed `finding_locator` (page, span offsets, table/row/cell, figure, timecode), `extractor_run` (model, prompt hash, pipeline version), a `source_strength_map` (the source's own label -> normalized strength, per source version), and a JSON-schema check per `relationship_type`. The assertion stores `evaluated_context` frozen at review. | columns on `extraction_items` (`locator jsonb NOT NULL` after backfill, `extractor_run_id`); `phg_flavor.extractor_runs`, `source_strength_maps`; CHECK functions `phg_flavor.valid_payload(kind, jsonb)` | A missing locator -> refused. Unknown strength label -> refused. Payload with the wrong shape for its type -> refused. | Columns are nullable first, and NOT NULL is set only after an empty-table check (the table is empty today). |
| **H6** Identity and graph integrity | Canonical key = `sha256(relationship_type, directionality, context_key, sorted or ordered member (subject_id, role))`. Symmetric sorts members; directed keeps order; A+B+C groups stay one assertion. Subjects get a `subject_aliases` table and a `canonical_subject_id`. A partial unique index handles NULL form: `UNIQUE (ingredient_id) WHERE form_key IS NULL`. A cycle check on `parent_subject_id` and `supersedes_id` uses a recursive-CTE trigger. Typed FKs go to `public.beverage_categories` and `public.cocktail_specs`. | `phg_flavor.subject_aliases`; columns `subjects.beverage_category_id`, `subjects.cocktail_spec_id`, `pairing_assertions.canonical_key` (unique); index `subjects_one_null_form_uq`; triggers `trg_subjects_no_cycle`, `trg_assertions_no_cycle` | Duplicate NULL-form subject -> refused. A->B symmetric equals B->A; directed does not. A 3-member group survives (criterion D). A parent cycle -> refused. | Additive constraints on empty tables. No production rows are affected. |
| **H7** Private data and domain modules | Add `account_id uuid NULL REFERENCES phg.accounts` and `visibility ('global','account')` to subjects, assertions, extraction_items and the new tasting tables; NULL means global and licensed. Serve functions filter by the caller's `phg.account_memberships`. New modules: `sensory_observations` (single subject, calibrated panel), `compound_measurements` (subject x compound, method, unit), `tasting_sessions` / `tasting_results` (linked to `phg.recipe_versions` and to `phg.recipe_evaluations` where that fits), `recommendation_runs` (inputs, rule/model version, returned IDs), and typed links `recipe_proposal_evidence (recipe_version_id, assertion_id, evidence_id)` and `menu_design_proposal_flavor_links (proposal_id uuid, assertion_id)`. | as named, all in `phg_flavor` | Account A's tasting is invisible to account B (criterion E). A global assertion cannot cite account-private evidence. An empty result returns explicit `unknown` (criterion H). | New tables only. `phg.*` tables are untouched apart from FKs from the flavor side. |
| **H8** Executing pipeline | Lease-based queue: `ingestion_tasks` (state, `lease_owner`, `lease_expires_at`, `attempt`, `max_attempts`, `next_run_at`, `budget_units`), claimed with `FOR UPDATE SKIP LOCKED`. A dead-letter state, progress counters and a watchdog cron that reclaims expired leases (the same pattern as the menu pipeline's `pipeline_processing_watchdogs`). Private Storage bucket `phg-flavor-snapshots` (no public access). The worker is an Edge Function `phg-flavor-ingest` with source in git and `verify_jwt=true`. It is built but **not scheduled** until Phase D approval. | `phg_flavor.ingestion_tasks`, `phg_flavor.claim_task()`, `complete_task()`, `fail_task()`; bucket; Edge Function; cron job (created disabled) | Kill the worker mid-task -> the lease expires, the task is reclaimed, and no duplicate `extraction_items` appear (`UNIQUE(source_unit_id,item_key)` plus the idempotency key) (criterion F). Retries stop at the limit and the task goes to dead-letter. | Stop by disabling the cron job. The queue is additive. Bucket objects are versioned by sha256 path. |
| **H9** Release gates and metrics | A `release_checklist` view combining GLOBAL blockers, advisor-clean status for flavor objects, and criteria A-I test results recorded in `test_runs`. A `metrics` view with four distinct counts: encountered occurrences, accepted occurrences, unique canonical assertions, servable evidence. Coverage over 100% or a negative count produces an `inconsistent_manifest` flag, not a clamp. | `phg_flavor.test_runs` (append-only), views `release_checklist`, `coverage_metrics` | Duplicate occurrences raise encountered but not unique. A forged manifest (units > expected) flags inconsistent. The checklist stays red while any GLOBAL blocker is open. | Views only. `test_runs` is append-only. |
| **H10** Reproducibility and recovery | (1) Export migration 20260928063244 from `schema_migrations.statements` into the repo verbatim. (2) Export all current catalog, work, document and change_log rows as idempotent seed SQL with a row-count and sha256 manifest. (3) A restore test on a Supabase branch or local stack: apply the migration plus seed, then compare counts and checksums against live. (4) Storage objects get an independent copy (a second bucket or external object store) plus a manifest, because DB backups exclude Storage bytes. (5) PITR/backup status is confirmed with Rob. | repo files `supabase/migrations/20260928063244_...sql`, `supabase/seed/phg_flavor/001_catalog.sql` ... `005_change_log.sql`, `supabase/tests/phg_flavor_restore_check.sql` | The restore check reproduces 36/36/36/151/6/6 and the registry checksum `625ace3b...` (criterion I). | This H10 work is the recovery provision. |

---

## 5. Source-access and rights decisions that need Rob

Nothing below will be acted on without an explicit written decision recorded in `rights_assessments`, with evidence.
Purchasing, access or discovery alone never turns on embeddings, training or redistribution.

1. **Acquisition order.** Proposed first wave, where rights are most tractable and value for a beverage product is
   highest. (a) **Open and identity foundations**: SRC-023 FoodOn (ontology; open licence reported, verify the release),
   SRC-024 USDA FoodData Central (US-government open data, verify) and SRC-025 PubChem (contributor-level terms). (b) **One small complete source for Phase D
   validation**: SRC-030 "Flavor network and the principles of food pairing" or SRC-032, depending on the article
   and supplement licence. (c) **Your own tastings** (`attributable_inhouse_tasting`), which need no third-party
   rights. Approve or reorder.
2. **Buying books.** 19 books (SRC-001 to SRC-019) are metadata-only. Should PHG buy physical or e-book copies for
   **internal reference and manual fact extraction**? Buying grants reading, not bulk copying. Decide the budget,
   the format, and whether manual extraction of facts (not text) is acceptable under your legal advice.
3. **Publisher licences for books.** For bulk or structured ingestion of The Flavor Bible, The Vegetarian Flavor
   Bible (Hachette), The Flavour Thesaurus and More Flavours (Bloomsbury), The Art & Science of Foodpairing (Hachette UK), Cocktail Codex,
   Liquid Intelligence and the others: should PHG request permissions or licences? Who signs, and what is the
   budget ceiling?
4. **FlavorDB2 and RecipeDB (SRC-020, SRC-022) are noncommercial and now `restricted`.** Options: (a) keep them out
   entirely; (b) use them for internal research only, never served in the product (still needs confirmation that
   PHG's internal use counts as noncommercial); (c) ask IIIT-Delhi / CoSyLab for a commercial licence. Recommended:
   (c), with (a) until it is granted.
5. **Foodpairing professional platform (SRC-028) and VCF Online (SRC-027) are paid.** Decide whether to take a
   vendor call and quote, and whether any contract must explicitly allow storage, derived assertions and in-product
   display. No subscription will be bought without your sign-off.
6. **FooDB (CAND-001, access `blocked`).** Approve an investigation of its current terms, or keep it blocked.
7. **FlavorGraph (SRC-021).** The code licence and the data licence differ, and it depends on FlavorDB/Recipe1M.
   Treat it as restricted by lineage until upstream rights clear?
8. **Embeddings and model training.** Confirm the default policy is **no embeddings and no training** on any
   third-party source until a per-source approval exists. Embeddings on PHG's own tasting data can be decided
   separately.
9. **Legal reviewer.** Name who assesses rights (the `assessed_by` field): you, counsel, or a delegate. An approved
   decision requires an evidence URL or locator.
10. **Customer data scope.** May venue recipes and tasting feedback from customer accounts ever contribute to a
    global graph (anonymized or aggregated), or are they account-private only? The default is private only.
11. **Menu co-occurrence from PHG's own corpus** (`menu_item_brands`, captured menus). This is scraped public
    menus. Decide whether it may become `recipe_or_menu_cooccurrence` evidence, and at what aggregation level.
12. **Backup spend.** Confirm the PITR/backup tier, and approve a second Storage location for snapshots (H10).
    No paid option is enabled today.
13. **Repository promotion.** Approve making this branch's `supabase/` tree the backend source (or a new
    `backend` branch), and approve exporting all 408 live migrations and the 83 function sources into it
    (PHG-FLV-001).
14. **Owners.** Name owners for source licensing, ingredient normalization, extraction review (two independent
    human reviewers are needed per unit), platform security and UI integration (brief Phase A).

---

## 6. Phased implementation plan (additive)

Rules for every phase:
- No production DDL or DML without Rob's written "apply" for that specific migration.
- Every migration is rehearsed first inside `BEGIN; ... ROLLBACK;` and on a branch or local stack, and has a
  written down-migration or disable path.
- `CREATE SCHEMA phg_flavor` is never re-run, and applied migration history is never rewritten.
- **Full-source coverage rule.** No batch size, top-N or pilot figure is ever a stopping point. Every source stays
  in the catalog, with its blockers, until it is audited complete for a named version. Blocked or unavailable
  sources are never dropped.
- **Do-not-collapse rule.** cataloged / acquired / extracted / reviewed / commercially usable / source-complete are
  reported as separate fields and are never merged into one "done" or percentage.
- Status language: nothing is described as populated, trained, connected or complete until a recorded test shows it.

### Phase A: Source of truth and baseline (repo only; no production change)

- Export `20260928063244` verbatim from `schema_migrations.statements` into
  `supabase/migrations/20260928063244_phg_flavor_research_catalog_and_coverage_foundation.sql`, with a header that
  says "already applied; do not re-run".
- Export the 5 `phg_design_*` migrations and the other 9 live-only migrations the same way.
- Export seed DML as idempotent files with a count and checksum manifest.
- Recreate the brief's 19 rollback-only checks as `supabase/tests/phg_flavor_foundation.sql`, covering incomplete
  manifests, rights constraint, distinct reviewer labels, completion blockers, draft and hypothesis exclusion,
  three-member preservation, rights withdrawal, ACLs, RLS, invoker views and archival grants.
- Add `supabase/tests/phg_flavor_baseline.sql`, which asserts section 1.1 counts and ACLs.
- Restore test on a Supabase branch (needs Rob's approval for branch cost) or a local `supabase start`.
- **Tests:** the baseline asserts pass against live read-only; the restore reproduces the counts and checksum.
- **Recovery:** none needed (files only).
- **Approval boundary:** Rob approves the repo promotion (decision 13) and the branch/restore environment.

### Phase B: Hardening before any content (H1-H7, H9 views; DDL on empty tables)

- Migrations B1 to B7 map one-to-one onto H1-H7.
- Order: H3 append-only triggers, then H1 role/functions/grant revocation, then H6 identity constraints, then H5
  provenance columns, then H4 review rounds, then H7 account/visibility and domain tables, then H2 publication and
  `servable_evidence`, then H9 checklist and metrics.
- Each migration lands separately: rehearsed, reviewed, applied only with approval.
- **Tests:** adversarial suites `phg_flavor_h1_rights.sql` ... `phg_flavor_h9_metrics.sql` covering stale hashes,
  rejected findings, fake reviewers, restricted and expired rights, identity ambiguity, cross-account reads and
  contradictory evidence (criteria A-E, H).
- **Recovery:** each migration ships with a down-script. Tables are empty, so rollback loses no data. Grant
  revocation (H1) is reversed by re-granting the recorded ACL.
- **Approval boundary:** Rob approves each B-migration apply. The GLOBAL/security-review-existing advisor check
  must show zero new findings for phg_flavor objects.

### Phase C: Acquire and inventory (all 36 intake records; data, not engine)

- Work through every `PHG-FLAVOR-*/rights` and `/access` item in the order Rob chose in section 5.
- For each source: record the exact edition, append a `rights_assessments` row with evidence, capture an authorized
  snapshot into the private bucket, build the manifest, and verify it (H3).
- Unavailable sources stay `blocked` with the reason in `resolution_note`, and are never deleted or cancelled.
- H8 queue and bucket objects are created (cron disabled).
- H10 Storage copy is enabled before the first snapshot byte is stored.
- **Tests:** integrity recompute equals the stored sha256; `source_coverage` moves only from `content_not_acquired`
  to `rights_not_cleared` or `manifest_not_verified` as the facts justify; the catalog count stays 36+ (criterion A).
- **Recovery:** snapshots are content-addressed with a second copy; rights rows are append-only.
- **Approval boundary:** a per-source written rights decision from Rob or the named assessor; any purchase or vendor
  contract is signed by Rob.

### Phase D: Extract and reconcile (workers; one small complete source first)

- Enable `phg-flavor-ingest` for **one** fully licensed, small source, run end to end, with two independent
  reviewers and adjudication.
- Measure recall against a hand-built answer key for that source.
- Only then enable further sources, with **exhaustive resumable traversal**. Per-request batch sizes are an
  implementation detail, and each run continues until the manifest is fully traversed.
- **Tests:** crash/retry (criterion F); same-count-different-findings adjudication (C); duplicate provenance kept
  and negative evidence visible (D); `source_coverage` reaches `audited_complete_for_version` only for that named
  version (B).
- **Recovery:** disable the cron job; leases expire; the idempotency key prevents duplicates. A bad extractor run
  can be retired via `extractor_run_id`, never by deleting findings.
- **Approval boundary:** Rob approves scheduling the worker, the per-run budget cap, and each new source added to
  extraction.

### Phase E: Connect draft workflows (Harmony and Menu Development; no UI rebuild)

- Add the bounded gateway: `public.phg_flavor_candidates(p_account_id uuid, p_subject_refs jsonb,
  p_context jsonb, p_limit int)`, `public.phg_flavor_explain(p_assertion_id uuid, p_account_id uuid)` and
  `public.phg_flavor_resolve(p_terms text[])`.
  - SECURITY DEFINER, owned by NOLOGIN `phg_flavor_reader`, `search_path` pinned, EXECUTE for service_role only.
  - They are called from `phg-cocktail-develop`, `phg-menu-item-generate-v2` and `phg-capability-router` via a new
    `flavor_evidence` capability.
  - They are logged like `menu_designer_query_log`.
  - They return the contract in brief section 10 (subject and form IDs, roles, assertion and evidence IDs, locators,
    stance, restrictions, separate confidence and novelty, rule version, draft status).
  - Empty results return `evidence_status: 'none_found'`.
- The generator's `why_it_works.flavor_progression` is labelled `generated_hypothesis` in the payload and in the
  existing card.
- Recipe proposals use the typed link tables (H7) and the existing proposal, approve and apply-with-revision flow.
- **Tests:** criteria E, G and H; iPhone, iPad and desktop regression of the Menu Development card and Harmony
  (PHG-003 device acceptance); no change to Presence/voice.
- **Recovery:** the capability is disabled by a row flag in `phg.capabilities`; functions are dropped; frontend
  changes ship behind the existing release process with a revert commit ready.
- **Approval boundary:** Rob approves the gateway apply, the Edge Function deploys and the `index.html` release
  separately.

### Phase F: Expand and evaluate

- Add regional first-person cuisine sources, plus deeper wine, beer, spirits and zero-proof sources, as new catalog
  rows (the 36 are a starting corpus).
- Run tasting-feedback loops through `tasting_sessions`.
- Release changes are tracked via `publication_decisions`, never by overwriting evidence.
- **Tests:** full A-I suite on every release, and the H10 restore drill quarterly.
- **Recovery:** as in Phases C and D.
- **Approval boundary:** Rob approves each new source's rights and each product release.

---

## 7. Queries used (reproducible, read-only)

Counts: `select count(*)` on each table in section 1.1.
ACLs: `pg_class.relacl`, `pg_namespace.nspacl`, `reloptions`, `pg_policies`.
Constraints: `pg_constraint` where `connamespace='phg_flavor'::regnamespace`.
Migrations: `list_migrations` and `supabase_migrations.schema_migrations` (408 rows).
Repo: `git ls-tree` on every `origin/*` branch.
Frontend: `grep functions/v1/` in `index.html` (29 endpoints).
