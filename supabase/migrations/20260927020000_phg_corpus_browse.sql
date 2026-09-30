-- PHG corpus browser: server-side document/candidate browsing with venue, text and
-- preparation filters. Additive only. Called exclusively by the service-role Edge
-- Function phg-menu-corpus-browser (v3+); EXECUTE is revoked from anon/authenticated
-- because the functions are SECURITY DEFINER over RLS-protected tables.
--
-- Filters honoured (all optional, jsonb keys):
--   kind            rendered | remaining | archived   (documents)
--   limit (1..60) offset (>=0)
--   q               venue name ILIKE
--   state           IA | CO | NY   (account_id prefix, 100% coverage)
--   city            exact, case-insensitive, from accounts.notes 'City: X.' (same rule as v_public_venues)
--   venue_type      matches accounts.google_types (any element) or format_code, case-insensitive
--   asset_kind      html | pdf | image           menu_scope   beverage | beverage_candidate
--   status          documents.page_render_status (ready | pending); candidates.status
--   source_format   candidates only (html | pdf | image | social | none)
--   cocktail        cocktail name ILIKE on staging_menu_extract.item_name (live rows, item_type='cocktail')
--   ingredient      text ILIKE on staging_menu_extract.notes (same rows)
--   prep_type       syrup|infusion|cordial|shrub|puree|bitters|citrus|garnish|foam|tincture|saline|tea|coffee
--
-- Text filters join documents/candidates to staging_menu_extract by menu_page_url =
-- original_menu_url / source_url (94.5% of documents have such rows). A document with
-- NO stored text can never match a text filter; the row field text_coverage tells the
-- UI whether text exists at all, so "no match" is never presented as "ingredient absent".

create or replace function public.phg_like_escape(p text)
returns text language sql immutable strict parallel safe as $$
  select replace(replace(replace(p, '\', '\\'), '%', '\%'), '_', '\_');
$$;

create or replace function public.phg_prep_patterns(p_prep text)
returns text[] language sql immutable strict parallel safe as $$
  select case lower(btrim(p_prep))
    when 'syrup'    then array['%syrup%','%orgeat%','%grenadine%','%agave nectar%','%honey syrup%']
    when 'infusion' then array['%infus%','%fat-wash%','%fat wash%','%washed %']
    when 'cordial'  then array['%cordial%']
    when 'shrub'    then array['%shrub%']
    when 'puree'    then array['%puree%','%purée%']
    when 'bitters'  then array['%bitters%']
    when 'citrus'   then array['%lemon%','%lime%','%grapefruit%','%orange%','%yuzu%','%citrus%']
    when 'garnish'  then array['%garnish%']
    when 'foam'     then array['%foam%','%aquafaba%','%egg white%']
    when 'tincture' then array['%tincture%']
    when 'saline'   then array['%saline%','%salt solution%']
    when 'tea'      then array['% tea%','%tea-%','%tea infused%','%tea-infused%']
    when 'coffee'   then array['%coffee%','%espresso%','%cold brew%']
    else null end;
$$;

create or replace function public.phg_corpus_browse_documents(p jsonb)
returns jsonb
language plpgsql stable security definer
set search_path = public, pg_temp
as $$
declare
  v_kind       text := coalesce(nullif(btrim(p->>'kind'),''), 'rendered');
  v_limit      int  := least(60, greatest(1, coalesce((p->>'limit')::int, 24)));
  v_offset     int  := greatest(0, coalesce((p->>'offset')::int, 0));
  v_q          text := nullif(btrim(p->>'q'), '');
  v_state      text := nullif(upper(btrim(p->>'state')), '');
  v_city       text := nullif(btrim(p->>'city'), '');
  v_vtype      text := nullif(lower(btrim(p->>'venue_type')), '');
  v_asset      text := nullif(btrim(p->>'asset_kind'), '');
  v_scope      text := nullif(btrim(p->>'menu_scope'), '');
  v_status     text := nullif(btrim(p->>'status'), '');
  v_cocktail   text := nullif(btrim(p->>'cocktail'), '');
  v_ingredient text := nullif(btrim(p->>'ingredient'), '');
  v_prep       text := nullif(lower(btrim(p->>'prep_type')), '');
  v_patterns   text[];
  v_text_filter boolean;
  v_count      bigint;
  v_rows       jsonb;
begin
  if v_kind not in ('rendered','remaining','archived') then v_kind := 'archived'; end if;
  if v_kind = 'rendered' then v_status := 'ready'; end if;
  if v_state is not null and v_state !~ '^[A-Z]{2}$' then raise exception 'invalid state'; end if;
  if v_prep is not null then
    v_patterns := public.phg_prep_patterns(v_prep);
    if v_patterns is null then raise exception 'unknown prep_type %', v_prep; end if;
  end if;
  v_text_filter := (v_cocktail is not null or v_ingredient is not null or v_prep is not null);

  with base as (
    select d.id, d.account_id, d.menu_source_candidate_id, d.original_menu_url, d.discovered_asset_url,
           d.asset_kind, d.acquisition_method, d.acquisition_status, d.page_count, d.menu_scope,
           d.page_render_status, d.page_rendered_at, d.discovered_at, d.acquired_at, d.updated_at,
           a.account_name, a.street_address, a.postal_code, a.google_types, a.website_url,
           public.account_state(a.account_id)                 as state,
           substring(a.notes from 'City: ([^.]+)')            as city,
           coalesce(a.google_types[1], a.format_code)         as venue_type
    from public.menu_visual_documents d
    join public.accounts a on a.account_id = d.account_id
    where (v_kind <> 'rendered'  or d.page_render_status = 'ready')
      and (v_kind <> 'remaining' or d.page_render_status is distinct from 'ready')
      and (v_status is null or d.page_render_status = v_status)
      and (v_asset  is null or d.asset_kind = v_asset)
      and (v_scope  is null or d.menu_scope = v_scope)
      and (v_q      is null or a.account_name ilike '%' || public.phg_like_escape(v_q) || '%')
      and (v_state  is null or a.account_id like 'ACC-' || v_state || '-%')
      and (v_city   is null or upper(substring(a.notes from 'City: ([^.]+)')) = upper(v_city))
      and (v_vtype  is null
           or lower(coalesce(a.google_types[1], a.format_code)) = v_vtype
           or v_vtype = any (select lower(t) from unnest(coalesce(a.google_types, '{}'::text[])) t))
      and (not v_text_filter
           or exists (select 1 from public.staging_menu_extract s
                      where s.superseded_at is null
                        and s.menu_page_url = d.original_menu_url
                        and s.item_type = 'cocktail'
                        and (v_cocktail   is null or s.item_name ilike '%' || public.phg_like_escape(v_cocktail) || '%')
                        and (v_ingredient is null or s.notes     ilike '%' || public.phg_like_escape(v_ingredient) || '%')
                        and (v_prep       is null or s.notes     ilike any (v_patterns))))
  ),
  counted as (select count(*) as c from base),
  pg as (
    select b.*
    from base b
    order by b.updated_at desc nulls last, b.id desc
    limit v_limit offset v_offset
  )
  select (select c from counted),
         coalesce(jsonb_agg(jsonb_build_object(
           'id', pg.id, 'account_id', pg.account_id, 'menu_source_candidate_id', pg.menu_source_candidate_id,
           'original_menu_url', pg.original_menu_url, 'discovered_asset_url', pg.discovered_asset_url,
           'asset_kind', pg.asset_kind, 'acquisition_method', pg.acquisition_method,
           'acquisition_status', pg.acquisition_status, 'page_count', pg.page_count,
           'menu_scope', pg.menu_scope, 'page_render_status', pg.page_render_status,
           'page_rendered_at', pg.page_rendered_at, 'discovered_at', pg.discovered_at,
           'acquired_at', pg.acquired_at, 'updated_at', pg.updated_at,
           'state', pg.state, 'city', pg.city, 'venue_type', pg.venue_type,
           'accounts', jsonb_build_object('account_name', pg.account_name, 'street_address', pg.street_address,
                                          'postal_code', pg.postal_code, 'google_types', pg.google_types,
                                          'website_url', pg.website_url),
           'pages', coalesce((select jsonb_agg(jsonb_build_object(
                        'id', x.id, 'page_number', x.page_number, 'render_status', x.render_status,
                        'capture_method', x.capture_method, 'width', x.width, 'height', x.height,
                        'bucket', x.page_image_bucket, 'path', x.page_image_path) order by x.page_number)
                      from public.menu_visual_pages x where x.menu_visual_document_id = pg.id), '[]'::jsonb),
           'ready_page_count', (select count(*) from public.menu_visual_pages x
                                where x.menu_visual_document_id = pg.id and x.render_status = 'ready'),
           'text_coverage', exists (select 1 from public.staging_menu_extract s
                                    where s.superseded_at is null and s.menu_page_url = pg.original_menu_url
                                      and s.item_type = 'cocktail'),
           'matched_items', case when v_text_filter then
                (select coalesce(jsonb_agg(m.item_name), '[]'::jsonb) from (
                   select distinct s.item_name
                   from public.staging_menu_extract s
                   where s.superseded_at is null and s.menu_page_url = pg.original_menu_url and s.item_type = 'cocktail'
                     and (v_cocktail   is null or s.item_name ilike '%' || public.phg_like_escape(v_cocktail) || '%')
                     and (v_ingredient is null or s.notes     ilike '%' || public.phg_like_escape(v_ingredient) || '%')
                     and (v_prep       is null or s.notes     ilike any (v_patterns))
                   order by s.item_name limit 6) m)
              else '[]'::jsonb end
         ) order by pg.updated_at desc nulls last, pg.id desc), '[]'::jsonb)
    into v_count, v_rows
  from pg;

  return jsonb_build_object('count', coalesce(v_count, 0), 'count_capped', false, 'rows', v_rows,
                            'limit', v_limit, 'offset', v_offset);
end;
$$;

create or replace function public.phg_corpus_browse_candidates(p jsonb)
returns jsonb
language plpgsql stable security definer
set search_path = public, pg_temp
as $$
declare
  v_limit      int  := least(60, greatest(1, coalesce((p->>'limit')::int, 24)));
  v_offset     int  := greatest(0, coalesce((p->>'offset')::int, 0));
  v_q          text := nullif(btrim(p->>'q'), '');
  v_state      text := nullif(upper(btrim(p->>'state')), '');
  v_city       text := nullif(btrim(p->>'city'), '');
  v_vtype      text := nullif(lower(btrim(p->>'venue_type')), '');
  v_format     text := coalesce(nullif(btrim(p->>'source_format'), ''), nullif(btrim(p->>'asset_kind'), ''));
  v_scope      text := nullif(btrim(p->>'menu_scope'), '');
  v_status     text := nullif(btrim(p->>'status'), '');
  v_cocktail   text := nullif(btrim(p->>'cocktail'), '');
  v_ingredient text := nullif(btrim(p->>'ingredient'), '');
  v_prep       text := nullif(lower(btrim(p->>'prep_type')), '');
  v_patterns   text[];
  v_text_filter boolean;
  v_cap        int := 5001;   -- counting 470k+ candidates exactly is the known latency hotspot
  v_count      bigint;
  v_rows       jsonb;
begin
  if v_state is not null and v_state !~ '^[A-Z]{2}$' then raise exception 'invalid state'; end if;
  if v_prep is not null then
    v_patterns := public.phg_prep_patterns(v_prep);
    if v_patterns is null then raise exception 'unknown prep_type %', v_prep; end if;
  end if;
  v_text_filter := (v_cocktail is not null or v_ingredient is not null or v_prep is not null);

  with base as (
    select c.id, c.account_id, c.source_url, c.menu_type, c.source_format, c.discovery_method,
           c.discovery_confidence, c.status, c.is_food_only, c.first_discovered_at, c.last_seen_at,
           c.item_count, c.menu_scope, c.page_count, c.visual_asset_status, c.visual_asset_method,
           c.visual_asset_url, c.visual_document_id, c.screenshot_pages_ready,
           a.account_name, a.street_address, a.postal_code, a.google_types, a.website_url,
           public.account_state(a.account_id)           as state,
           substring(a.notes from 'City: ([^.]+)')      as city,
           coalesce(a.google_types[1], a.format_code)   as venue_type
    from public.menu_source_candidates c
    join public.accounts a on a.account_id = c.account_id
    where (v_format is null or c.source_format = v_format)
      and (v_scope  is null or c.menu_scope = v_scope)
      and (v_status is null or c.status = v_status)
      and (v_q      is null or a.account_name ilike '%' || public.phg_like_escape(v_q) || '%')
      and (v_state  is null or a.account_id like 'ACC-' || v_state || '-%')
      and (v_city   is null or upper(substring(a.notes from 'City: ([^.]+)')) = upper(v_city))
      and (v_vtype  is null
           or lower(coalesce(a.google_types[1], a.format_code)) = v_vtype
           or v_vtype = any (select lower(t) from unnest(coalesce(a.google_types, '{}'::text[])) t))
      and (not v_text_filter
           or exists (select 1 from public.staging_menu_extract s
                      where s.superseded_at is null
                        and s.menu_page_url = c.source_url
                        and s.item_type = 'cocktail'
                        and (v_cocktail   is null or s.item_name ilike '%' || public.phg_like_escape(v_cocktail) || '%')
                        and (v_ingredient is null or s.notes     ilike '%' || public.phg_like_escape(v_ingredient) || '%')
                        and (v_prep       is null or s.notes     ilike any (v_patterns))))
  ),
  counted as (select count(*) as c from (select 1 from base limit v_cap) z),
  pg as (
    select b.* from base b
    order by b.id desc            -- newest discovered first; pkey-ordered so no 470k-row sort per request
    limit v_limit offset v_offset
  )
  select (select c from counted),
         coalesce(jsonb_agg(jsonb_build_object(
           'id', pg.id, 'account_id', pg.account_id, 'source_url', pg.source_url, 'menu_type', pg.menu_type,
           'source_format', pg.source_format, 'discovery_method', pg.discovery_method,
           'discovery_confidence', pg.discovery_confidence, 'status', pg.status, 'is_food_only', pg.is_food_only,
           'first_discovered_at', pg.first_discovered_at, 'last_seen_at', pg.last_seen_at,
           'item_count', pg.item_count, 'menu_scope', pg.menu_scope, 'page_count', pg.page_count,
           'visual_asset_status', pg.visual_asset_status, 'visual_asset_method', pg.visual_asset_method,
           'visual_asset_url', pg.visual_asset_url, 'visual_document_id', pg.visual_document_id,
           'screenshot_pages_ready', pg.screenshot_pages_ready,
           'state', pg.state, 'city', pg.city, 'venue_type', pg.venue_type,
           'accounts', jsonb_build_object('account_name', pg.account_name, 'street_address', pg.street_address,
                                          'postal_code', pg.postal_code, 'google_types', pg.google_types,
                                          'website_url', pg.website_url),
           'text_coverage', exists (select 1 from public.staging_menu_extract s
                                    where s.superseded_at is null and s.menu_page_url = pg.source_url
                                      and s.item_type = 'cocktail')
         ) order by pg.id desc), '[]'::jsonb)
    into v_count, v_rows
  from pg;

  return jsonb_build_object('count', coalesce(v_count, 0), 'count_capped', coalesce(v_count, 0) >= v_cap,
                            'rows', v_rows, 'limit', v_limit, 'offset', v_offset);
end;
$$;

-- Vocabularies for the gallery's selects, derived from real data (not literals).
create or replace function public.phg_corpus_filter_values()
returns jsonb
language sql stable security definer
set search_path = public, pg_temp
as $$
  with docs as (
    select d.id, d.asset_kind, d.menu_scope, d.page_render_status,
           public.account_state(a.account_id) as state,
           upper(substring(a.notes from 'City: ([^.]+)')) as city,
           lower(coalesce(a.google_types[1], a.format_code)) as venue_type
    from public.menu_visual_documents d join public.accounts a on a.account_id = d.account_id
  )
  select jsonb_build_object(
    'states',      (select coalesce(jsonb_agg(jsonb_build_object('v', state, 'n', n) order by n desc), '[]'::jsonb)
                    from (select state, count(*) n from docs where state is not null group by 1) s),
    'cities',      (select coalesce(jsonb_agg(jsonb_build_object('v', city, 'n', n) order by n desc), '[]'::jsonb)
                    from (select city, count(*) n from docs where city is not null group by 1 order by 2 desc limit 80) s),
    'venue_types', (select coalesce(jsonb_agg(jsonb_build_object('v', venue_type, 'n', n) order by n desc), '[]'::jsonb)
                    from (select venue_type, count(*) n from docs where venue_type is not null group by 1 order by 2 desc limit 60) s),
    'asset_kinds', (select coalesce(jsonb_agg(jsonb_build_object('v', asset_kind, 'n', n) order by n desc), '[]'::jsonb)
                    from (select asset_kind, count(*) n from docs where asset_kind is not null group by 1) s),
    'menu_scopes', (select coalesce(jsonb_agg(jsonb_build_object('v', menu_scope, 'n', n) order by n desc), '[]'::jsonb)
                    from (select menu_scope, count(*) n from docs where menu_scope is not null group by 1) s),
    'render_statuses', (select coalesce(jsonb_agg(jsonb_build_object('v', page_render_status, 'n', n) order by n desc), '[]'::jsonb)
                    from (select page_render_status, count(*) n from docs where page_render_status is not null group by 1) s),
    'candidate_statuses', (select coalesce(jsonb_agg(jsonb_build_object('v', status, 'n', n) order by n desc), '[]'::jsonb)
                    from (select status, count(*) n from public.menu_source_candidates group by 1) s),
    'candidate_formats', (select coalesce(jsonb_agg(jsonb_build_object('v', source_format, 'n', n) order by n desc), '[]'::jsonb)
                    from (select source_format, count(*) n from public.menu_source_candidates group by 1) s),
    'candidate_scopes', (select coalesce(jsonb_agg(jsonb_build_object('v', menu_scope, 'n', n) order by n desc), '[]'::jsonb)
                    from (select menu_scope, count(*) n from public.menu_source_candidates group by 1) s),
    'prep_types', to_jsonb(array['syrup','infusion','cordial','shrub','puree','bitters','citrus','garnish','foam','tincture','saline','tea','coffee']),
    'text_coverage', jsonb_build_object(
        'documents_with_cocktail_text', (select count(distinct d.id) from public.menu_visual_documents d
                                         where exists (select 1 from public.staging_menu_extract s
                                                       where s.superseded_at is null and s.menu_page_url = d.original_menu_url
                                                         and s.item_type = 'cocktail')),
        'documents_total', (select count(*) from public.menu_visual_documents)),
    'generated_at', now()
  );
$$;

revoke execute on function public.phg_corpus_browse_documents(jsonb)  from public, anon, authenticated;
revoke execute on function public.phg_corpus_browse_candidates(jsonb) from public, anon, authenticated;
revoke execute on function public.phg_corpus_filter_values()          from public, anon, authenticated;
grant  execute on function public.phg_corpus_browse_documents(jsonb)  to service_role;
grant  execute on function public.phg_corpus_browse_candidates(jsonb) to service_role;
grant  execute on function public.phg_corpus_filter_values()          to service_role;
grant  execute on function public.phg_like_escape(text)               to service_role;
grant  execute on function public.phg_prep_patterns(text)             to service_role;

comment on function public.phg_corpus_browse_documents(jsonb)  is 'PHG gallery: paginated visual documents with venue/text/prep filters. Service-role only (Edge phg-menu-corpus-browser).';
comment on function public.phg_corpus_browse_candidates(jsonb) is 'PHG gallery: paginated discovery candidates with venue/text/prep filters; count capped at 5001. Service-role only.';
comment on function public.phg_corpus_filter_values()          is 'PHG gallery: real filter vocabularies with counts. Service-role only.';
