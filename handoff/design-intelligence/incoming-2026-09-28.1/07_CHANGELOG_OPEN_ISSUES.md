# CHANGE LOG AND OPEN ISSUES

Version 2026-09-28.1

## This handoff pass

- Reopened the original 50-entry research file in full.
- Attempted a fresh read-only Supabase count query; it was blocked. No database data or permissions changed.
- Rechecked selected primary guidance and publisher/repository abstracts; recorded scope limits.
- Inspected final menu artwork and checked the existing media streams/durations.
- Read the existing audio-mix verification report from the delivered archive.
- Reconstructed reference mapping from the conversation, including all original/professional entries and historical 37 source keys.
- Created the master role brief, startup prompt, read-only audit/export queries, proposed agent contract, evidence samples and visual/media manifest.
- Packaged existing visual references and completed media without generating new paid media.

## Open issues

### D-01 | P0 | Current database audit unavailable

**Status:** Open. **Owner:** Authorized backend agent.

**Evidence:** Fresh read-only count query was blocked; latest counts come from prior successful tool output.

**Acceptance:** Run authorized read-only inventory; preserve existing data; do not bypass security gates.

### D-02 | P0 | Receiving-agent integration unverified

**Status:** Open. **Owner:** Backend + agent owner.

**Evidence:** Function existence is not proof that generation actually retrieves knowledge.

**Acceptance:** Trace a real brief through retrieval, generation, evidence IDs and logged output.

### D-03 | P0 | Content preservation failures

**Status:** Open. **Owner:** Menu content owner + designer.

**Evidence:** Generated iterations changed recipes, removed items, dropped prices and introduced filler.

**Acceptance:** Canonical content manifest and deterministic text comparison before release.

### D-04 | P0 | Ingredient sorting persistence unknown

**Status:** Open. **Owner:** Backend + menu agent.

**Evidence:** Exact user display ordering was requested but no confirmed dedicated database save appears.

**Acceptance:** Persist role-aware display sorting through approved workflow; test all new items.

### D-05 | P0 | Authorization model incomplete

**Status:** Open. **Owner:** Backend security owner.

**Evidence:** Definer gateway grants authenticated execute; visible table DDL does not show RLS policies.

**Acceptance:** Inspect owners, search paths, grants, tenant scope and real agent credentials; propose controlled migration.

### D-06 | P1 | Provenance gap

**Status:** Open. **Owner:** Research editor.

**Evidence:** 49 principle-source links versus 187 principles in historical checkpoint.

**Acceptance:** Find unlinked claims and exact locators; distinguish synthesis from study findings.

### D-07 | P1 | Reading completeness unknown

**Status:** Open. **Owner:** Research editor.

**Evidence:** 50+20 references were cataloged, not all fully read or acquired.

**Acceptance:** Scope unit inventories; log acquired/read/unread/blocked states and permissions.

### D-08 | P1 | Misleading infographic totals

**Status:** Open. **Owner:** Reporting owner.

**Evidence:** 612 sources, 184,320+ points and 68% completion have no evidence.

**Acceptance:** Retire screenshots as status evidence; use reproducible counts and scoped coverage.

### D-09 | P1 | Source metadata needs correction

**Status:** Open. **Owner:** Research editor.

**Evidence:** Some author fields are placeholders or suspect; generic MIT root used for detailed principles.

**Acceptance:** Resolve bibliographic metadata and replace vague locators without inventing support.

### D-10 | P1 | Terminology and duplicate rows

**Status:** Open. **Owner:** Ontology owner.

**Evidence:** Luminance/value, chroma/saturation, repeated spacing and visual-mass concepts overlap.

**Acceptance:** Alias rather than blindly delete stable IDs; define units and semantics.

### D-11 | P1 | Uncalibrated confidence

**Status:** Open. **Owner:** Research + evaluation.

**Evidence:** High decimal confidence values are author-entered and not statistical.

**Acceptance:** Store confidence_type and review status; avoid ranking solely by these values.

### D-12 | P1 | Measurement implementation missing

**Status:** Open. **Owner:** Vision/measurement engineer.

**Evidence:** Many numeric-looking variables are qualitative proxies with no estimator.

**Acceptance:** Specify method/version/uncertainty; use not_measured until implementation and validation.

### D-13 | P1 | Test definitions not executions

**Status:** Open. **Owner:** QA owner.

**Evidence:** 60 procedures exist in table form; execution and results not established.

**Acceptance:** Implement a small real suite; log image hash, parameters, applicability and outcomes.

### D-14 | P1 | Case images and object annotations unverified

**Status:** Open. **Owner:** Visual corpus owner.

**Evidence:** Seven case seeds did not visibly populate artifact_ref or detailed object graphs.

**Acceptance:** Attach durable permitted images and annotate actual objects, relationships and observations.

### D-15 | P1 | Packet/profile migration uncertain

**Status:** Open. **Owner:** Backend owner.

**Evidence:** Draft phg_design_packet/brief_profiles had no retained success/test response.

**Acceptance:** Check existence; review domain balance, scoping, tests, source output and missing-profile behavior.

### D-16 | P1 | Historic test lineage inferred

**Status:** Open. **Owner:** Experiment owner.

**Evidence:** Sixth reference was labeled round three without explicit user mapping.

**Acceptance:** Import actual run/round/critic logs and correct lineage.

### D-17 | P1 | Source rights review outstanding

**Status:** Open. **Owner:** Rights/research owner.

**Evidence:** Publicly visible educational and archive material may restrict commercial reuse/training.

**Acceptance:** Store per-source license and permitted uses; review commercial ingest before raw copying.

### D-18 | P1 | Fantasy IP usage not cleared

**Status:** Open. **Owner:** Brand/rights owner.

**Evidence:** Concepts use famous worlds, names, symbols and character-inspired imagery.

**Acceptance:** Determine intended use and obtain relevant review; no clearance is claimed.

### D-19 | P1 | Final menu not production-ready

**Status:** Open. **Owner:** Beverage owner + designer.

**Evidence:** Flat 766x1024 side images, questionable placeholder ingredients, limited price/quantity verification.

**Acceptance:** Validate recipes/service facts; rebuild production text; proof actual format and environment.

### D-20 | P1 | Expanded inventory not reconciled

**Status:** Open. **Owner:** Rob + menu owner.

**Evidence:** Prior 20 tequilas, 12 beers and 8 wines do not match current 10/6/5/6 category counts.

**Acceptance:** Confirm current scope; restore or explicitly approve reductions.

### D-21 | P2 | Cultural claims and source diversity shallow

**Status:** Open. **Owner:** Research + design.

**Evidence:** List includes global resources; deep systematic artifact review not established.

**Acceptance:** Study bounded diverse specimens with contextual notes rather than motif extraction.

### D-22 | P2 | Video is not editable 3D

**Status:** Open. **Owner:** Video owner.

**Evidence:** Delivered MP4 has no rigs, scene graph or reeditable camera.

**Acceptance:** Preserve exact requested output type; create a true 3D pipeline only for a new authorized scope.

### D-23 | P2 | Video was text-prompt based

**Status:** Open. **Owner:** Video owner.

**Evidence:** Generation task had no reference images, so exact menu fidelity was not locked.

**Acceptance:** For future renders, anchor verified assets and separate readable labels in post.

### D-24 | P2 | No isolated voice-only export in editor bundle

**Status:** Open. **Owner:** Audio owner.

**Evidence:** M4A/WAV contains narration plus original soundtrack.

**Acceptance:** Label accurately; retrieve original TTS segments only when a voice-only stem is required.

### D-25 | P2 | Frame-precise duration

**Status:** Open. **Owner:** Media QA.

**Evidence:** Narrated and silent MP4 containers probe at 30.041667 seconds.

**Acceptance:** Only trim if a strict 30.000 delivery spec requires it; preserve master otherwise.

### D-26 | P2 | Unknown full-suite quality comparison

**Status:** Open. **Owner:** Evaluation owner.

**Evidence:** Rob prefers the designs, but no independent calibrated benchmark was run.

**Acceptance:** Same content, blind pairwise choices, logged scores, task tests and resource budget.

