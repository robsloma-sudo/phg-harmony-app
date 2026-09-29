-- APPLIED 2026-09-29 as migration phg_know_lookup_fn. Read-only lookup of phg_know for the place cards and Harmony.
create or replace function public.phg_know_lookup(p_nom text default null, p_names text[] default null)
returns jsonb language sql stable security definer set search_path = phg_know, pg_temp as $$
  with b as (
    select * from phg_know.brand_profiles bp
    where (p_nom is not null and bp.nom = regexp_replace(p_nom, '\D', '', 'g'))
       or (p_names is not null and (lower(bp.name) = any (select lower(x) from unnest(p_names) x)
           or exists (select 1 from unnest(bp.aka) a where lower(a) = any (select lower(x) from unnest(p_names) x))))
    limit 60
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'key', b.key, 'name', b.name, 'category', b.category, 'nom', b.nom, 'producer', b.producer, 'owner', b.owner,
    'region', b.region, 'founded_year', b.founded_year, 'history', b.history, 'verification', b.verification,
    'sources', (select coalesce(jsonb_agg(jsonb_build_object('title', s.title, 'url', s.url, 'tier', s.tier)), '[]') from phg_know.sources s where s.key = any (b.source_keys)),
    'expressions', (select coalesce(jsonb_agg(to_jsonb(e) - 'source_keys' - 'updated_at' - 'brand_key'
                     order by array_position(array['blanco','joven','reposado','anejo','extra_anejo','cristalino','other'], e.style), e.name), '[]')
                    from phg_know.expressions e where e.brand_key = b.key)
  ) order by b.name), '[]'::jsonb) from b;
$$;
revoke all on function public.phg_know_lookup(text, text[]) from public, anon, authenticated;
grant execute on function public.phg_know_lookup(text, text[]) to service_role;
