# Design knowledge base: gateway queries

Ready-to-run SQL for the Menu Designer and the critics to read Rob's design-theory knowledge base (schema `phg_design`,
project `lqjtwabzmgjcufftuqvu`) through the read-only gateway. For the summary, read
handoff/agents/DESIGN_KNOWLEDGE_DIGEST.md first; query here when you need a row's full detail.

## Status: the gateway cannot read phg_design yet (tested 2026-09-28)

```sql
select public.phg_designer_query($q$select count(*) from phg_design.principles$q$, 5, null);
-- ERROR: designer query failed: permission denied for schema phg_design
```

The gateway runs queries through `phg_designer.run`, which is `SECURITY DEFINER` owned by role `phg_menu_designer`.
That role has `USAGE` on `phg` but **not** on `phg_design` (`has_schema_privilege('phg_menu_designer','phg_design','USAGE')`
is false). **A grant is needed.** It has not been applied; Rob (or whoever owns the schema) must decide. The minimal
read-only grant would be:

```sql
grant usage on schema phg_design to phg_menu_designer;
grant select on all tables in schema phg_design to phg_menu_designer;
-- optional, so future tables are readable too:
alter default privileges in schema phg_design grant select on tables to phg_menu_designer;
```

Until then, the queries below only run with direct SQL access, and agents should rely on the digest.

## How to call

```sql
select public.phg_designer_query($q$ <one SELECT> $q$, 500, '<task id or null>');
```

- One statement, no trailing second statement. Always schema-qualify tables: `phg_design.<table>` (the gateway's
  search_path is `public, phg`).
- Rows come back as JSON in `rows`. Keep `p_max_rows` small for wide rows.
- Replace the values in `in (...)` or `= '...'` with what you need.

## 1. Agent guidance (all 11 rules, by priority)

```sql
select public.phg_designer_query($q$
  select guidance_key, domain, title, instruction, rationale, priority
  from phg_design.agent_guidance
  where active
  order by priority desc, guidance_key
$q$, 50, null);
```

## 2. The brief profile for this job

```sql
select public.phg_designer_query($q$
  select profile_key, name, venue_type, artifact_type, goals, required_domains,
         hard_gate_dimensions, default_tests, retrieval_terms
  from phg_design.brief_profiles
  where profile_key in ('cocktail_menu', 'mobile_menu')
$q$, 10, null);
```

## 3. The rubric

Hard gates first (these block approval outright):

```sql
select public.phg_designer_query($q$
  select dimension_key, name, domain, definition, score_anchors, failure_conditions
  from phg_design.rubric_dimensions
  where hard_gate
  order by domain, dimension_key
$q$, 50, null);
```

The menu-relevant scored dimensions:

```sql
select public.phg_designer_query($q$
  select dimension_key, name, domain, hard_gate, weight, definition, score_anchors
  from phg_design.rubric_dimensions
  where domain in ('art_direction','color','composition','craft','gestalt','grid','identity',
                   'illustration','imagery','menu_design','strategy','systems','typography',
                   'functional','environment','production','perception','visual_communication')
  order by hard_gate desc, domain, dimension_key
$q$, 100, null);
```

The whole rubric (58 rows):

```sql
select public.phg_designer_query($q$
  select dimension_key, domain, hard_gate, weight, definition, score_anchors, failure_conditions
  from phg_design.rubric_dimensions order by domain, dimension_key
$q$, 100, null);
```

## 4. Decision rules for a domain

Domains with rules: accessibility, art_direction, color, composition, critique, depth, digital_design, editorial,
evaluation, gestalt, grid, iconography, identity, illustration, imagery, information_design, mark_making, menu_design,
menu_engineering, perception, process, production, sequence, systems, typography.

```sql
select public.phg_designer_query($q$
  select rule_key, name, domain, priority, confidence, problem_pattern,
         diagnostic_signals, interventions, expected_effects, validation_tests, exceptions
  from phg_design.decision_rules
  where domain in ('menu_design', 'art_direction')
  order by priority desc, rule_key
$q$, 100, null);
```

A compact version for a quick critique (one line of text per rule):

```sql
select public.phg_designer_query($q$
  select rule_key, domain, priority, problem_pattern,
         (select string_agg(i->>'action', '; ') from jsonb_array_elements(interventions) i) as interventions,
         (select string_agg(t->>'test', '; ') from jsonb_array_elements(validation_tests) t) as tests
  from phg_design.decision_rules
  where domain = 'composition'
  order by priority desc
$q$, 50, null);
```

Find the rule for a symptom (full-text match on the problem and its signals):

```sql
select public.phg_designer_query($q$
  select rule_key, domain, problem_pattern
  from phg_design.decision_rules
  where problem_pattern ilike '%price%' or diagnostic_signals::text ilike '%price%'
  order by priority desc
$q$, 20, null);
```

## 5. Principles

By domain, highest confidence first:

```sql
select public.phg_designer_query($q$
  select principle_key, name, domain, definition, mechanism, desired_effects,
         failure_modes, exceptions, evidence_class, confidence
  from phg_design.principles
  where domain in ('menu_design', 'typography')
  order by domain, confidence desc
$q$, 100, null);
```

One principle with its sources:

```sql
select public.phg_designer_query($q$
  select p.principle_key, p.definition, p.mechanism, p.conditions, p.failure_modes, p.exceptions,
         p.evidence_class, p.confidence,
         (select jsonb_agg(jsonb_build_object('source', s.title, 'creator', s.creator,
                                              'year', s.publication_year, 'support', ps.support_type, 'note', ps.note))
          from phg_design.principle_sources ps join phg_design.sources s on s.id = ps.source_id
          where ps.principle_id = p.id) as sources
  from phg_design.principles p
  where p.principle_key = 'menu_sweet_spot_skepticism'
$q$, 5, null);
```

## 6. Validation tests

For a domain, or the defaults of a brief profile:

```sql
select public.phg_designer_query($q$
  select test_key, name, domain, test_type, procedure, measures, pass_logic, limitations
  from phg_design.validation_tests
  where test_key in ('thumbnail_test','blur_squint_test','grayscale_test','logo_off_test',
                     'price_pair_scan','actual_size_test','item_block_proximity_test',
                     'device_subtraction_test','salience_budget_test')
  order by domain, test_key
$q$, 50, null);
```

## 7. Case studies (lessons from earlier cantina and Casa Luna rounds)

```sql
select public.phg_designer_query($q$
  select case_key, title, venue_type, round_no, outcome, brief, global_analysis, critique, lessons
  from phg_design.case_studies
  order by case_key
$q$, 20, null);
```

## 8. Vocabulary: concepts and measurable variables

```sql
select public.phg_designer_query($q$
  select concept_key, name, domain, definition, measurable, unit_or_scale
  from phg_design.concepts where domain = 'menu_design' order by concept_key
$q$, 100, null);
```

```sql
select public.phg_designer_query($q$
  select variable_key, name, domain, data_type, unit, scale_min, scale_max, description, perceptual_role
  from phg_design.variables where domain in ('menu_design','art_direction','color') order by domain, variable_key
$q$, 100, null);
```

## 9. Critic pack (one call: gates, guidance and the menu rules)

```sql
select public.phg_designer_query($q$
  select 'guidance' as kind, guidance_key as key, instruction as text, priority::int as priority
    from phg_design.agent_guidance where active
  union all
  select 'hard_gate', dimension_key, definition || ' | fails if: ' || coalesce(failure_conditions::text, ''), 100
    from phg_design.rubric_dimensions where hard_gate
  union all
  select 'rule', rule_key, problem_pattern, priority::int
    from phg_design.decision_rules where domain in ('menu_design','art_direction','composition','typography','color')
  order by kind, priority desc, key
$q$, 200, null);
```

## Knowledge base contents (2026-09-28)

sources 37, concepts 316, principles 187, variables 192, decision_rules 69, rule_principles 0, rubric_dimensions 58
(11 hard gates, all weight 1), validation_tests 60, agent_guidance 11, brief_profiles 2, case_studies 7,
principle_sources 49, relationship_types 10, ingestion_runs 0. Empty: palettes, typography_profiles,
composition_profiles, critiques, revision_decisions, visual_objects, visual_relationships. The view
`phg_design.v_knowledge_counts` returns the current counts.
