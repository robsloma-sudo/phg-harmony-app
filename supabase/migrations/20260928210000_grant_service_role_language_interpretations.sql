-- Harmony history: phg-language-interpreter (service_role) must insert one row per
-- interpretation and read them back for Recent work / Brief. Without these grants
-- every insert failed silently (0 rows ever) and action:'history' returned 500.
-- Least privilege: no UPDATE/DELETE. Reverse with:
--   revoke select, insert on phg.language_interpretations from service_role;
-- Applied to lqjtwabzmgjcufftuqvu 2026-09-28 at Rob's request ("fix the history").
grant select, insert on phg.language_interpretations to service_role;
