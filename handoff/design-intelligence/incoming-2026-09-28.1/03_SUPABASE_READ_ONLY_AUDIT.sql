-- PHG DESIGN KNOWLEDGE: READ-ONLY AUDIT AND RETRIEVAL
-- Target project: lqjtwabzmgjcufftuqvu
-- Prepared 2026-09-28. This file has not been run during handoff.
-- Use an authorized server-side/database connector. Respect security gates.
-- Run each numbered group separately and inspect results before continuing.
-- No DDL, data mutation, privilege changes, server filesystem reads, or OS commands.

-- 1. Identity/context and existence. Connection authorization is external to this SQL.
SELECT now() AS audited_at, current_database(), current_user;
SELECT to_regclass('phg_design.v_knowledge_counts') AS count_view,
       to_regclass('phg_design.sources') AS sources,
       to_regclass('phg_design.brief_profiles') AS optional_brief_profiles,
       to_regprocedure('public.phg_design_knowledge(text,text,integer)') AS knowledge_function,
       to_regprocedure('public.phg_design_packet(text,text,integer)') AS optional_packet_function;

-- 2. Authoritative relation and column inventory.
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema='phg_design'
ORDER BY table_name;
SELECT table_name,column_name,data_type,udt_name,is_nullable,column_default
FROM information_schema.columns
WHERE table_schema='phg_design'
ORDER BY table_name,ordinal_position;

-- 3. Count view: run only if confirmed in group 1.
SELECT * FROM phg_design.v_knowledge_counts;
SELECT pg_get_viewdef('phg_design.v_knowledge_counts'::regclass,true) AS counting_definition;

-- 4. Fresh source inventory. Review actual access status; do not infer reading from presence.
SELECT source_key,title,creator,source_type,evidence_class,authority_tier,
       url,publication_year,access_status,notes,created_at,updated_at
FROM phg_design.sources ORDER BY source_key;

-- 5. Real provenance coverage and orphan records.
SELECT count(*) AS total_principles,
       count(*) FILTER (WHERE EXISTS (
           SELECT 1 FROM phg_design.principle_sources ps WHERE ps.principle_id=p.id
       )) AS principles_with_any_source_link,
       count(*) FILTER (WHERE NOT EXISTS (
           SELECT 1 FROM phg_design.principle_sources ps WHERE ps.principle_id=p.id
       )) AS principles_without_source_link
FROM phg_design.principles p;
SELECT p.principle_key,p.name,p.domain,p.evidence_class,p.confidence
FROM phg_design.principles p
WHERE NOT EXISTS (SELECT 1 FROM phg_design.principle_sources ps WHERE ps.principle_id=p.id)
ORDER BY p.domain,p.principle_key;
SELECT p.principle_key,s.source_key,s.title,s.url,ps.support_type,ps.note
FROM phg_design.principle_sources ps
JOIN phg_design.principles p ON p.id=ps.principle_id
JOIN phg_design.sources s ON s.id=ps.source_id
ORDER BY p.principle_key,s.source_key;
SELECT r.rule_key,r.name FROM phg_design.decision_rules r
WHERE NOT EXISTS (SELECT 1 FROM phg_design.rule_principles rp WHERE rp.rule_id=r.id)
ORDER BY r.rule_key;

-- 6. Ingestion activity and cases. These are not proof that upstream documents were read.
SELECT * FROM phg_design.ingestion_runs ORDER BY started_at DESC;
SELECT case_key,title,case_type,venue_type,artifact_ref,round_no,iteration_no,outcome,
       global_analysis,critique,lessons
FROM phg_design.case_studies ORDER BY created_at,case_key;
SELECT 'visual_objects' AS relation,count(*) AS records FROM phg_design.visual_objects
UNION ALL SELECT 'visual_relationships',count(*) FROM phg_design.visual_relationships
UNION ALL SELECT 'palettes',count(*) FROM phg_design.palettes
UNION ALL SELECT 'typography_profiles',count(*) FROM phg_design.typography_profiles
UNION ALL SELECT 'composition_profiles',count(*) FROM phg_design.composition_profiles
UNION ALL SELECT 'critiques',count(*) FROM phg_design.critiques
UNION ALL SELECT 'revision_decisions',count(*) FROM phg_design.revision_decisions
UNION ALL SELECT 'agent_guidance',count(*) FROM phg_design.agent_guidance
UNION ALL SELECT 'relationship_types',count(*) FROM phg_design.relationship_types;

-- 7. Find protected ingredient-order/content rules; inspect the actual text.
SELECT guidance_key,title,instruction FROM phg_design.agent_guidance
WHERE concat_ws(' ',guidance_key,title,instruction) ILIKE ANY
      (ARRAY['%ingredient%','%display order%','%sweetener%','%base spirit%','%description%','%price%']);
SELECT rule_key,name,problem_pattern,interventions FROM phg_design.decision_rules
WHERE concat_ws(' ',rule_key,name,problem_pattern,interventions::text) ILIKE ANY
      (ARRAY['%ingredient%','%sweetener%','%base spirit%','%description%','%price%']);

-- 8. Definitions and grants. Definer functions need review, not automatic modification.
SELECT n.nspname AS schema_name,p.proname,pg_get_function_identity_arguments(p.oid) AS arguments,
       p.prosecdef AS security_definer,p.proconfig,p.proacl,
       pg_get_functiondef(p.oid) AS function_definition
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public' AND p.proname IN
('phg_design_knowledge','phg_design_packet','phg_designer_query','phg_design_status','phg_design_doc_items')
ORDER BY p.proname;
SELECT n.nspname,c.relname,c.relkind,c.relrowsecurity,c.relforcerowsecurity,c.relacl
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='phg_design' AND c.relkind IN ('r','p','v','m') ORDER BY c.relname;
SELECT schemaname,tablename,policyname,roles,cmd,qual,with_check
FROM pg_policies WHERE schemaname='phg_design' ORDER BY tablename,policyname;
SELECT grantee,table_name,privilege_type FROM information_schema.role_table_grants
WHERE table_schema='phg_design' ORDER BY grantee,table_name,privilege_type;

-- 9. Evidence classes, bounds, and candidate aliases. These do not auto-deduplicate.
SELECT evidence_class,count(*) FROM phg_design.principles GROUP BY evidence_class ORDER BY 2 DESC;
SELECT variable_key,name,domain,data_type,scale_min,scale_max,unit,description
FROM phg_design.variables
WHERE variable_key ILIKE ANY(ARRAY['%luminance%','%value%','%chroma%','%saturation%','%corner%','%line%length%','%mass%','%gravity%','%confidence%','%delta%'])
ORDER BY domain,variable_key;
SELECT lower(regexp_replace(name,'[^a-zA-Z0-9]+','','g')) AS normalized_name,
       count(*),array_agg(concept_key ORDER BY concept_key) AS keys
FROM phg_design.concepts GROUP BY 1 HAVING count(*)>1 ORDER BY 2 DESC;

-- 10. Direct, citation-bearing retrieval; adjust domains to the actual brief.
SELECT p.principle_key,p.name,p.domain,p.definition,p.mechanism,p.conditions,
       p.desired_effects,p.failure_modes,p.exceptions,p.evidence_class,p.confidence,
       COALESCE(jsonb_agg(jsonb_build_object('source_key',s.source_key,'title',s.title,
           'url',s.url,'access_status',s.access_status,'support_type',ps.support_type,'note',ps.note))
           FILTER (WHERE s.id IS NOT NULL),'[]'::jsonb) AS citations
FROM phg_design.principles p
LEFT JOIN phg_design.principle_sources ps ON ps.principle_id=p.id
LEFT JOIN phg_design.sources s ON s.id=ps.source_id
WHERE p.domain IN ('composition','typography','menu_design','color','art_direction','identity','accessibility')
GROUP BY p.id ORDER BY p.domain,p.principle_key;
SELECT * FROM phg_design.decision_rules
WHERE domain IN ('menu_design','art_direction','composition','process','evaluation')
ORDER BY priority DESC,rule_key;
SELECT * FROM phg_design.validation_tests ORDER BY domain,test_key;
SELECT * FROM phg_design.rubric_dimensions ORDER BY domain,dimension_key;

-- 11. OPTIONAL historical gateway: run only after reviewing definition and auth.
-- SELECT public.phg_design_knowledge('art_direction',NULL,100);
-- SELECT public.phg_design_packet('cocktail_menu',NULL,100);
-- Do not claim a missing packet function works. Do not send a service key to a browser.

-- 12. Portable export examples. Save result through client tools, never server filesystem SQL.
-- These are full records and may require pagination under connector response limits.
SELECT jsonb_build_object('exported_at',now(),'schema','phg_design',
 'sources',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.source_key),'[]') FROM phg_design.sources t),
 'concepts',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.concept_key),'[]') FROM phg_design.concepts t),
 'principles',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.principle_key),'[]') FROM phg_design.principles t),
 'principle_sources',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.principle_sources t),
 'variables',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.variable_key),'[]') FROM phg_design.variables t),
 'relationship_types',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.relationship_key),'[]') FROM phg_design.relationship_types t),
 'decision_rules',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.rule_key),'[]') FROM phg_design.decision_rules t),
 'rule_principles',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.rule_principles t),
 'agent_guidance',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.guidance_key),'[]') FROM phg_design.agent_guidance t)
) AS knowledge_core_export;

SELECT jsonb_build_object('exported_at',now(),'schema','phg_design',
 'case_studies',(SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.case_key),'[]') FROM phg_design.case_studies t),
 'visual_objects',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.visual_objects t),
 'visual_relationships',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.visual_relationships t),
 'palettes',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.palettes t),
 'typography_profiles',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.typography_profiles t),
 'composition_profiles',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.composition_profiles t),
 'critiques',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.critiques t),
 'revision_decisions',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.revision_decisions t),
 'rubric_dimensions',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.rubric_dimensions t),
 'validation_tests',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.validation_tests t),
 'ingestion_runs',(SELECT COALESCE(jsonb_agg(to_jsonb(t)),'[]') FROM phg_design.ingestion_runs t)
) AS visual_process_export;
-- Export brief_profiles separately only if inventory confirms it.
