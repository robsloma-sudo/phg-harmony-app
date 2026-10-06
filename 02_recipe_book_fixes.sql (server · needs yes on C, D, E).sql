-- PHG 2026-10-06 · RECIPE BOOK DESIGNER open issues #7, #8, #10 (all guarded, all idempotent, one transaction)
-- Needs Rob's yes (items C, D, E in the Backend Lead summary). #9 (gate blocks publishing) is a workflow change in the
-- Recipe Book Designer's recipe-book-qa-publish skill, not SQL; it is NOT in this file.
begin;

-- #7 · shaken dilution constant 0.0203 -> 0.203. Guard: only if the stored text is exactly what was read on 2026-10-06.
update phg_mix.techniques
   set params = jsonb_set(params, '{shaken_formula}', to_jsonb('-1.567*abv^2 + 1.742*abv + 0.203'::text))
 where key = 'tq_dilution_targets'
   and params->>'shaken_formula' = '-1.567*abv^2 + 1.742*abv + 0.0203';
-- undo: same update with the two strings swapped.

-- #8 · maple_syrup / pure_maple_syrup. Checked 2026-10-06: 0 references in all 16 tables that point at phg.ingredients.
-- Keep maple_syrup; record pure_maple_syrup as its alias; retire (not delete) the duplicate.
update phg.ingredients
   set aliases = (select array(select distinct x from unnest(coalesce(aliases,'{}') || array['pure_maple_syrup','Pure Maple Syrup']) x)),
       metadata = metadata - 'note' || jsonb_build_object('merged_from','pure_maple_syrup','merged_at',now(),'merged_by','backend_lead (Rob approved)')
 where ingredient_key = 'maple_syrup';
-- (verification_status allows only verified/user_confirmed/generated_draft/imported_unverified, so retirement is
--  recorded in metadata.retired = true; costing and pickers should skip rows with metadata->>'retired' = 'true')
update phg.ingredients
   set metadata = metadata - 'note' || jsonb_build_object('retired',true,'retired_reason','duplicate of maple_syrup','merged_into','maple_syrup','retired_at',now())
 where ingredient_key = 'pure_maple_syrup' and coalesce(metadata->>'retired','') <> 'true';
-- undo: restore both metadata notes, drop the retired keys on pure_maple_syrup, remove the 2 aliases from maple_syrup.

-- #10 · compliance gate false PASS: STABLE -> VOLATILE (re-reads inside the caller's transaction).
alter function phg.phg_recipe_compliance volatile;
-- undo: alter function phg.phg_recipe_compliance stable;

-- close the three issues with the evidence (raised by the designer, closed by the Backend Lead)
update phg.open_issues set status='resolved', resolved_at=now(), resolution=r.txt
  from (values
   ('dilution_constant_conflict','shaken_formula constant set to 0.203 (guarded update), Rob approved 2026-10-06'),
   ('duplicate_maple_rows','pure_maple_syrup retired into maple_syrup as alias; 0 references existed; Rob approved 2026-10-06'),
   ('compliance_gate_snapshot_trap','phg_recipe_compliance is now VOLATILE; Rob approved 2026-10-06')) r(k,txt)
 where issue_key = r.k and status = 'open';

commit;

-- verify:
-- select params->>'shaken_formula' from phg_mix.techniques where key='tq_dilution_targets';           -- ... + 0.203
-- select ingredient_key, metadata->>'retired', aliases from phg.ingredients where ingredient_key like '%maple_syrup';
-- select provolatile from pg_proc where proname='phg_recipe_compliance';                               -- v
-- select issue_key, status from phg.open_issues order by status;                                       -- 3 resolved, 9 open
