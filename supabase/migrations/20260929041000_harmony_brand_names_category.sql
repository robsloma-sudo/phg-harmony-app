-- 2026-09-29 Harmony: brand names with their spirit category, so a name heard next to "tequila", "reposado",
-- "scotch", "gin"... is matched against brands of that spirit first (Rob: match sound to the brand name when it is
-- in the right context). Read-only view, adds one column at the end; access unchanged (service_role only).
-- Rollback: re-run 20260929040000_harmony_brand_names_view.sql after
--   drop view if exists public.v_harmony_brand_names;
set local lock_timeout = '3s';

create or replace view public.v_harmony_brand_names
with (security_invoker = true) as
with c as (
  select btrim(brand_name_raw) as name,
         case
           when class_type_desc ~* 'mezcal|agave' then 'mezcal'
           when class_type_desc ~* 'tequila' then 'tequila'
           when class_type_desc ~* 'whisk|bourbon|scotch|rye' then 'whiskey'
           when class_type_desc ~* 'vodka' then 'vodka'
           when class_type_desc ~* 'gin' then 'gin'
           when class_type_desc ~* 'rum' then 'rum'
           when class_type_desc ~* 'brandy|cognac|armagnac|pisco|grappa|calvados' then 'brandy'
           when class_type_desc ~* 'liqueur|cordial|bitters|herb|anis|amaro|vermouth|creme|cream' then 'liqueur'
           when class_type_desc ~* 'cocktail|margarita' then 'cocktail'
           else ''
         end as category
  from public.cola_label_approvals
  where brand_name_raw is not null and length(btrim(brand_name_raw)) >= 3
)
select min(name) as name, count(*)::int as labels, mode() within group (order by category) as category
from c
group by lower(name);

revoke all on public.v_harmony_brand_names from public, anon, authenticated;
grant select on public.v_harmony_brand_names to service_role;
