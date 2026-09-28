# PHG-026 round 5: live definitions for the reviewers (read-only, 2026-09-28)

Captured with `pg_get_functiondef` / `pg_get_viewdef` on the live database (project lqjtwabzmgjcufftuqvu, as postgres)
before and during round 5. Nothing here was changed; the designer gateway (C17) is untouched. ACLs are `proacl` / `relacl`.

## C17: designer gateway

### phg_designer.run(text, integer)  (ACL `{phg_menu_designer=X/phg_menu_designer,postgres=X/phg_menu_designer}`; owner phg_menu_designer)
```sql
CREATE OR REPLACE FUNCTION phg_designer.run(p_sql text, p_limit integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'phg', 'pg_temp'
AS $function$
declare v jsonb;
begin
  if p_sql ~* '(pg_advisory|pg_try_advisory|set_config|pg_notify|pg_sleep|pg_terminate|pg_cancel|pg_reload|pg_signal|\mlo_|dblink|\mnet\.|\mcron\.|\mvault\.|pg_read|pg_ls_|pg_stat_file|txid_|pg_logical|_to_xml|to_xmlschema|ts_stat|ts_rewrite|\mxmltable|\mu&|\muescape)' then
    raise exception 'function not allowed in designer queries';
  end if;
  execute format('select coalesce(jsonb_agg(q), ''[]''::jsonb) from (select * from (%s) s limit %s) q', p_sql, p_limit) into v;
  return v;
end $function$
```

### public.phg_designer_query(text, integer, uuid)  (ACL `{postgres=X/postgres,service_role=X/postgres}`; SECURITY INVOKER)
```sql
CREATE OR REPLACE FUNCTION public.phg_designer_query(p_sql text, p_max_rows integer DEFAULT 500, p_task_id uuid DEFAULT NULL::uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO 'public', 'phg', 'pg_temp'
AS $function$
declare v_rows jsonb; v_t0 timestamptz := clock_timestamp(); v_log bigint;
begin
  if p_sql is null or btrim(p_sql) = '' then raise exception 'sql required'; end if;
  if p_sql ~ ';\s*\S' then raise exception 'one statement only'; end if;
  insert into phg.menu_designer_query_log (task_id, sql) values (p_task_id, left(p_sql, 20000)) returning id into v_log;
  -- note: read-only and the 20 s timeout stay on for the rest of the caller's transaction (call it on its own)
  set local statement_timeout = '20s';
  set local transaction_read_only = on;
  begin
    v_rows := phg_designer.run(regexp_replace(p_sql, ';\s*$', ''), least(greatest(coalesce(p_max_rows, 500), 1), 5000));
  exception when others then
    perform pg_advisory_unlock_all();
    raise exception 'designer query failed: %', sqlerrm;
  end;
  perform pg_advisory_unlock_all();
  return jsonb_build_object('rows', v_rows, 'row_count', jsonb_array_length(v_rows), 'log_id', v_log,
                            'ms', (extract(epoch from clock_timestamp() - v_t0) * 1000)::int);
end $function$
```

## C10: readers that assume one current menu per venue

### public.v_menu_composition  (ACL: postgres, anon, authenticated, service_role all `arwdDxtm`; phg_menu_designer `r`)
```sql
 SELECT m.account_id, a.account_name, m.menu_id, m.menu_format, m.extraction_confidence,
    (m.captured_at)::date AS captured_on,
    count(DISTINCT s.id) FILTER (WHERE (s.section_type = 'cocktails'::text)) AS cocktail_sections,
    count(DISTINCT i.id) FILTER (WHERE (s.section_type = 'cocktails'::text)) AS cocktail_items,
    count(DISTINCT i.id) FILTER (WHERE (s.section_type = 'spirits'::text)) AS spirit_pours,
    count(DISTINCT i.id) AS total_items,
    count(DISTINCT i.id) FILTER (WHERE (b.spirit_category = 'tequila'::text)) AS tequila_items,
    count(DISTINCT i.id) FILTER (WHERE ((b.spirit_category = 'tequila'::text) AND b.brand_named)) AS tequila_branded,
    count(DISTINCT i.id) FILTER (WHERE ((b.spirit_category = 'tequila'::text) AND (NOT b.brand_named))) AS tequila_unnamed,
    count(DISTINCT b.brand_id) FILTER (WHERE (b.spirit_category = 'tequila'::text)) AS distinct_tequila_brands,
    round(avg(i.price) FILTER (WHERE (b.spirit_category = 'tequila'::text)), 2) AS avg_tequila_price,
    round(avg(i.price), 2) AS avg_item_price,
    round(((100.0 * (count(DISTINCT i.id) FILTER (WHERE (b.spirit_category = 'tequila'::text)))::numeric) / (NULLIF(count(DISTINCT i.id) FILTER (WHERE (s.section_type = ANY (ARRAY['cocktails'::text, 'spirits'::text]))), 0))::numeric), 1) AS tequila_share_pct
   FROM ((((menus m
     JOIN accounts a ON ((a.account_id = m.account_id)))
     LEFT JOIN menu_sections s ON ((s.menu_id = m.id)))
     LEFT JOIN menu_items i ON ((i.section_id = s.id)))
     LEFT JOIN menu_item_brands b ON ((b.menu_item_id = i.id)))
  WHERE m.is_current
  GROUP BY m.account_id, a.account_name, m.menu_id, m.menu_format, m.extraction_confidence, m.captured_at;
```
One row per current menu. With the unique index `menus_one_current_per_account` this is one row per venue.

### public.v_menu_brand_presence  (same ACL as above)
```sql
 SELECT br.brand_name,
    count(DISTINCT m.account_id) AS venues,
    count(DISTINCT i.id) AS menu_items,
    count(DISTINCT i.id) FILTER (WHERE (s.section_type = 'cocktails'::text)) AS in_cocktails,
    count(DISTINCT i.id) FILTER (WHERE (s.section_type = 'spirits'::text)) AS as_pour,
    round(avg(i.price), 2) AS avg_price,
    (min(m.captured_at))::date AS first_seen,
    (max(m.captured_at))::date AS last_seen
   FROM ((((menu_item_brands b
     JOIN brands br ON ((br.id = b.brand_id)))
     JOIN menu_items i ON ((i.id = b.menu_item_id)))
     JOIN menu_sections s ON ((s.id = i.section_id)))
     JOIN menus m ON ((m.id = s.menu_id)))
  WHERE (m.is_current AND (b.brand_id IS NOT NULL))
  GROUP BY br.brand_name;
```
`venues` is distinct; `menu_items` / `in_cocktails` / `as_pour` count item rows of current menus, so they were inflated
while venues had several current menus (the incident) and are exact again with one current menu per venue.

### public.v_menu_category_share  (same ACL as above)
```sql
 SELECT b.spirit_category,
    count(DISTINCT i.id) AS items,
    count(DISTINCT m.account_id) AS venues,
    count(DISTINCT b.brand_id) AS distinct_brands,
    count(*) FILTER (WHERE (NOT b.brand_named)) AS unnamed_references,
    round(avg(i.price), 2) AS avg_price
   FROM (((menu_item_brands b
     JOIN menu_items i ON ((i.id = b.menu_item_id)))
     JOIN menu_sections s ON ((s.id = i.section_id)))
     JOIN menus m ON ((m.id = s.menu_id)))
  WHERE m.is_current
  GROUP BY b.spirit_category;
```

### public.phg_menu_composition(text, integer)  (ACL `{postgres=X/postgres,service_role=X/postgres}`)
```sql
CREATE OR REPLACE FUNCTION public.phg_menu_composition(p_query text, p_limit integer DEFAULT 20)
 RETURNS jsonb
 LANGUAGE sql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
select coalesce(jsonb_agg(to_jsonb(x)),'[]'::jsonb) from (
 select account_id,account_name,menu_id,menu_format,extraction_confidence,captured_on,cocktail_sections,cocktail_items,spirit_pours,total_items,tequila_items,tequila_branded,tequila_unnamed,distinct_tequila_brands,avg_tequila_price,avg_item_price,tequila_share_pct
 from public.v_menu_composition where p_query is null or account_name ilike '%'||p_query||'%' order by captured_on desc nulls last limit greatest(1,least(coalesce(p_limit,20),50))
)x $function$
```

### public.phg_brand_presence(text, integer)  (ACL `{postgres=X/postgres,service_role=X/postgres}`)
```sql
CREATE OR REPLACE FUNCTION public.phg_brand_presence(p_brand text, p_limit integer DEFAULT 20)
 RETURNS jsonb
 LANGUAGE sql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
select jsonb_build_object(
 'menu',coalesce((select jsonb_agg(to_jsonb(m)) from (select brand_name,venues,menu_items,in_cocktails,as_pour,avg_price,first_seen,last_seen from public.v_menu_brand_presence where brand_name ilike '%'||p_brand||'%' order by venues desc limit greatest(1,least(coalesce(p_limit,20),50)))m),'[]'::jsonb),
 'geography',coalesce((select jsonb_agg(to_jsonb(g)) from (select brand_name,geography_name,geo_type,subdivision_code,first_seen,last_seen,confirmed_availability_events,distinct_accounts from public.v_brand_geography_presence where brand_name ilike '%'||p_brand||'%' order by confirmed_availability_events desc limit greatest(1,least(coalesce(p_limit,20),50)))g),'[]'::jsonb)
) $function$
```

### Edge function phg-expanded-data (v4, verify_jwt true): the menu-reading part
The function reads secrets only through `Deno.env.get(...)`; no key is in the source. The only part that reads menus
(action `restaurant_menu_map`):
```ts
const {data:md,error:menuErr}=await sb.from("menus")
  .select("id,menu_id,account_id,evidence_url,menu_title,menu_format,extraction_confidence,captured_at,published_date,is_current,item_count,source_file_url,needs_vision_pass")
  .in("account_id",accountIds).order("captured_at",{ascending:false});
...
const menuByAccount=new Map();
for(const m of menus){if(!menuByAccount.has(m.account_id))menuByAccount.set(m.account_id,m);}
```
**Finding (C10, round 5):** this picks each venue's NEWEST menu by `captured_at`, not its current one. It selects
`is_current` but does not filter or order by it. Before PHG-026 the newest menu was always current (every submit
superseded everything), so it matched. After PHG-026, an alternate (`created_alternate`: item page, partial re-capture,
damped near-identical, smaller other source) is newer than the current menu and would be shown instead of it. The fix
is one line in the Edge function (`.order("is_current",{ascending:false}).order("captured_at",{ascending:false})`, or
`.eq("is_current",true)`). It is NOT deployed in this change (Edge deploys are outside the PHG-026 files); it is on the
post-release list in file 2's runbook (step 7) and should be done before or with cron 7 re-enable.

Observation (pre-existing, outside PHG-026): the three views grant `arwdDxtm` to anon and authenticated. They are
aggregate (GROUP BY) views, so they are not updatable and only the SELECT part has any effect.
