"""PHG-026 rehearsal generator (round 4; round-3 blocks kept and extended).

Builds rolled-back DO blocks that run the real migration files against the live database and end in
RAISE EXCEPTION, so nothing is kept. Each block re-runs the setup it needs (the MCP call times out at 60 s).

  python3 gen.py            -> rehearse_round4.sql (all blocks, in order) + rehearse_round4_<X>.sql (one per block)

Round-2 output (rehearse_all.sql) and round-3 output (rehearse_round3*.sql) are kept for reference.
Round 4 adds: A s10/s10b (same-source item page vs real page, C1), B backup privileges + lock_timeout + monitor,
F approve path (layout re-check, accuracy_reviewer), G rollback skip path (newer menu, multi-current backup, re-extracted page).
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
M = ROOT / 'supabase' / 'migrations'
T = ROOT / 'supabase' / 'tests'
f1 = (M / '20260927190000_phg_menu_dedupe_one_current.sql').read_text()
f2 = (M / '20260927191000_phg_menu_repair_20260927.sql').read_text()
gate = (T / 'phg_026_release_gate.sql').read_text().rstrip().rstrip(';')
mon = (T / 'phg_026_monitor.sql').read_text().rstrip().rstrip(';')
f3 = (M / '20260928030000_phg_menu_design_score_gate.sql').read_text()   # SF10 (not applied live)
for tag in ('$rehearse_f1$', '$rehearse_f2$', '$rehearse_f3$', '$rehearse_main$', '$rehearse_gate$', '$rehearse_mon$'):
    for src in (f1, f2, f3, gate, mon):
        assert tag not in src

MULTI = "(select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x)"
MS = "round(extract(epoch from clock_timestamp()-t0)*1000)"
ACCT = 'ACC-CO-LED-03-25486'          # 33-item current menu, no other menus
SIB_ACCT = 'ACC-CO-LED-03-08090'      # sibling page 515238 (/happyhour, 16 staged items), candidate 13965 (/menu)
SIB_ID, CAND_ID = 515238, 13965
PROMO_ACCT = 'ACC-CO-LED-03-06531'   # The Sherpa Grill: 13-item incident item pages
PROMO_URL = 'https://thesherpagrill.com/menu?item=aloo-gobi-NKZx'
PROMO_NEW_URL = 'https://thesherpagrill.com/menu?item=rehearsal-new-sibling'


def err(stage, into='r'):
    return f"""
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
    RAISE EXCEPTION 'REHEARSAL %', {into} || jsonb_build_object('stage','{stage}','sqlstate',e_state,'error',e_msg,'detail',e_det,'context',right(e_ctx, 600),'ms',{MS});"""


def soft_err(key, into):
    return f"""
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      {into} := {into} || jsonb_build_object('{key}', jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx), 'pass', false));"""


def run_file(label, tag, text):
    return f"""
  t0 := clock_timestamp();
  BEGIN
    EXECUTE {tag}{text}{tag};
  EXCEPTION WHEN others THEN {err(label)}
  END;
  r := r || jsonb_build_object('{label}_ms', {MS});"""


def call(url, seed, sections, acct='acct'):
    return (f"res := public.submit_menu({acct},'NBCC-FIRECRAWL-MENUS',{url},null,'html','unknown','rehearsal',null,"
            f"md5('{seed}'||clock_timestamp()::text),{sections},null,null,null,null,false);")


def sqlq(t):
    return "'" + t.replace("'", "''") + "'"


def after(label, expect):
    """record the result of the last submit_menu call plus a pass flag (expect is a boolean SQL expression)."""
    return f"""
    select id into cur_now from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('{label}', res || jsonb_build_object(
       'current_after', cur_now, 'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', {MULTI}, 'expect', {sqlq(expect)}, 'pass', coalesce(({expect}), false)));"""


J3 = '\'[{"section_name":"Order","section_type":"unsectioned","section_position":1,"items":[{"item_name":"Rehearsal Item A","item_type":"other","price":9},{"item_name":"Rehearsal Item B","item_type":"other","price":10}]}]\'::jsonb'
J5 = '\'[{"section_name":"Food","section_type":"unsectioned","section_position":1,"items":[{"item_name":"Rehearsal Fries","item_type":"other","price":7},{"item_name":"Rehearsal Burger","item_type":"other","price":15}]}]\'::jsonb'

DECL = f"""DO $rehearse_main$
DECLARE
  r jsonb := '{{}}'; a jsonb := '{{}}'; b jsonb := '{{}}'; c jsonb := '{{}}'; v jsonb; res jsonb;
  t0 timestamptz; t1 timestamptz; acct text := '{ACCT}'; orig_url text;
  cur_id uuid; cur2 uuid; cur_now uuid; secs jsonb; secs2 jsonb; secs4 jsonb; secs9 jsonb; items jsonb; item_x uuid;
  rem int; calls jsonb; lease_owner uuid := gen_random_uuid(); claimed timestamptz := clock_timestamp();
  secs10 jsonb; g jsonb := '{{}}'; skip_acct text; multi_acct text; stg_acct text; stg_url text; snap jsonb; snap2 jsonb;
  n1 int; n2 int; tid uuid; pid uuid; dlayout jsonb; ddoc jsonb;
  e_state text; e_msg text; e_ctx text; e_det text;
BEGIN
  set local statement_timeout = '58s';"""

END = """
  RAISE EXCEPTION 'REHEARSAL %', r;
END
$rehearse_main$;
"""

# ---------------------------------------------------------------- block A: file 1 + scenarios 1-9
A = DECL + run_file('file1', '$rehearse_f1$', f1) + f"""
  t0 := clock_timestamp();
  BEGIN
    a := a || jsonb_build_object('backup_rows', (select count(*) from public.phg_backup_function_defs_20260927),
       'backup_sigs', (select jsonb_agg(signature order by signature) from public.phg_backup_function_defs_20260927),
       'backup_service_role_can_insert', has_table_privilege('service_role','public.phg_backup_function_defs_20260927','INSERT'),
       'backup_service_role_can_select', has_table_privilege('service_role','public.phg_backup_function_defs_20260927','SELECT'),
       'submit_menu_10arg_exists', to_regprocedure('public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb)') is not null,
       'promote_clamp_5', (select prosrc ~ 'least\\(5,' from pg_proc where oid='public.promote_clean_menu_batch(integer)'::regprocedure),
       'multi_current_global_before', {MULTI});
    select id, evidence_url into cur_id, orig_url from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('account', acct, 'orig_current', cur_id,
       'orig_distinct_keys', cardinality(public.phg_menu_item_keys(cur_id)), 'orig_bev', public.phg_menu_bev_count(cur_id));
    with it as (select s.id sid, i.*, row_number() over (order by s.section_position, s.id, i.item_position, i.id) rn
                  from public.menu_sections s join public.menu_items i on i.section_id=s.id where s.menu_id=cur_id)
    select jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',it.price,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)) order by s.section_position, s.id),
           jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',case when it.rn<=3 then coalesce(it.price,0)+1 else it.price end,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)) order by s.section_position, s.id),
           jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',it.price,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)
                     || case when s.section_position = (select min(section_position) from public.menu_sections where menu_id=cur_id)
                             then '[{{"item_name":"Rehearsal Extra Pour","item_type":"spirit_pour","price":14}}]'::jsonb else '[]'::jsonb end) order by s.section_position, s.id)
      into secs, secs2, secs9 from public.menu_sections s where s.menu_id=cur_id;
    with it as (select s.id sid, i.*, row_number() over (order by s.section_position, s.id, i.item_position, i.id) rn
                  from public.menu_sections s join public.menu_items i on i.section_id=s.id where s.menu_id=cur_id)
    select jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',case when it.rn<=3 then coalesce(it.price,0)+1 when it.rn=5 then coalesce(it.price,0)+2 else it.price end,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)) order by s.section_position, s.id)
      into secs10 from public.menu_sections s where s.menu_id=cur_id;

    -- 1 exact copy of the current menu from another URL -> duplicate, nothing inserted
    {call("'https://rehearsal.example.com/copy1'", 'reh1', 'secs')}{after('s1_exact_copy_other_url', "res->>'status'='duplicate_of_current' and cur_now=cur_id")}
    -- all live menus are < 7 days old (created 2026-09-25..27); age this one so the near-identical rule (not damping) applies
    update public.menus set created_at = created_at - interval '30 days' where id = cur_id;
    -- 2 same items, 3 prices changed, another URL, current menu 30 days old -> replaces
    {call("'https://rehearsal.example.com/copy2'", 'reh2', 'secs2')}{after('s2_three_prices_changed_other_url', "res->>'status'='created' and res->>'reason' in ('newer_near_identical_capture','price_enrichment_other_source') and cur_now<>cur_id")}
    select id into cur2 from public.menus where account_id=acct and is_current;
    -- 9 flip-flop damping: the original page again (original prices). Current (copy2) is minutes old and from another
    --   source; the capture is only near-identical -> alternate, current stays copy2
    {call('orig_url', 'reh9', 'secs')}{after('s9_flipflop_original_page_again', "res->>'status' in ('created_alternate','duplicate_item_set') and coalesce(res->>'reason','alternate_near_identical_recent_other_source')='alternate_near_identical_recent_other_source' and cur_now=cur2")}
    -- 9b control: the original page with ONE MORE item (larger) still replaces a recent current menu
    BEGIN
      {call('orig_url', 'reh9b', 'secs9')}{after('s9b_flipflop_control_larger_replaces', "res->>'status'='created' and cur_now<>cur2")}
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 9b';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- 3 ?item= page on the current URL with 2 new items -> alternate
    {call("'https://rehearsal.example.com/copy2?item=abc'", 'reh3', J3)}{after('s3_item_page_same_url', "res->>'status'='created_alternate' and res->>'reason'='alternate_item_page' and cur_now=cur2")}
    -- 4 same URL as current, 10 items (5 current + 5 new) < half of 33 -> alternate
    select jsonb_build_array(jsonb_build_object('section_name','Partial','section_type','unsectioned','section_position',1,'items',
             (select jsonb_agg(x) from (
                (select jsonb_build_object('item_name',i.item_name,'item_type','other','price',i.price) x
                   from public.menu_sections s join public.menu_items i on i.section_id=s.id where s.menu_id=cur2 order by i.id limit 5)
                union all
                select jsonb_build_object('item_name','Rehearsal Partial '||g,'item_type','other','price',5+g) from generate_series(1,5) g) q)))
      into secs4;
    {call("'https://rehearsal.example.com/copy2'", 'reh4', 'secs4')}{after('s4_partial_same_url', "res->>'status'='created_alternate' and res->>'reason'='alternate_partial_recapture' and cur_now=cur2")}
    -- 5 another URL, 2 food items -> alternate
    {call("'https://rehearsal.example.com/food'", 'reh5', J5)}{after('s5_small_food_other_url', "res->>'status'='created_alternate' and res->>'reason'='alternate_smaller_other_source' and cur_now=cur2")}
    -- 6 zero items -> ignored
    {call("'https://rehearsal.example.com/empty'", 'reh6', "'[]'::jsonb")}{after('s6_zero_items', "res->>'status'='empty_capture_ignored' and cur_now=cur2")}
    -- 10 (C1, round 4) SAME source item page (copy2?item=full, key = copy2), same size as the real-page current menu,
    --    one price changed: before round 4 it replaced the real page; now it is an alternate and the real page stays
    BEGIN
      {call("'https://rehearsal.example.com/copy2?item=full'", 'reh10', 'secs10')}{after('s10_same_source_item_page_same_size', "res->>'status'='created_alternate' and res->>'reason'='alternate_item_page' and cur_now=cur2")}
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 10';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- 10b control: the same item page with ONE MORE item (strictly larger) replaces
    BEGIN
      {call("'https://rehearsal.example.com/copy2?item=full'", 'reh10b', 'secs9')}{after('s10b_same_source_item_page_larger_replaces', "res->>'status'='created' and cur_now<>cur2")}
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 10b';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- 7 a missing price overlaps a priced item (both ways); price-adds helper
    a := a || jsonb_build_object('s7_overlap',
       jsonb_build_object('capture_noprice_vs_current_priced', public.phg_menu_keys_overlap(array[public.phg_menu_item_key('Rehearsal Negroni', null)], array[public.phg_menu_item_key('Rehearsal Negroni', 12)]),
                          'reverse', public.phg_menu_keys_overlap(array[public.phg_menu_item_key('Rehearsal Negroni', 12)], array[public.phg_menu_item_key('Rehearsal Negroni', null)]),
                          'different_prices', public.phg_menu_keys_overlap(array['rehearsal negroni|12'], array['rehearsal negroni|13']),
                          'price_adds_capture_priced_vs_current_unpriced', public.phg_menu_keys_price_adds(array['rehearsal negroni|12'], array['rehearsal negroni|']),
                          'price_adds_reverse', public.phg_menu_keys_price_adds(array['rehearsal negroni|'], array['rehearsal negroni|12']),
                          'price_adds_when_current_has_both', public.phg_menu_keys_price_adds(array['rehearsal negroni|12'], array['rehearsal negroni|','rehearsal negroni|12'])));
    a := jsonb_set(a, '{{s7_overlap,pass}}', to_jsonb(
          (a->'s7_overlap'->>'capture_noprice_vs_current_priced')::int = 1 and (a->'s7_overlap'->>'reverse')::int = 1
      and (a->'s7_overlap'->>'different_prices')::int = 0 and (a->'s7_overlap'->>'price_adds_capture_priced_vs_current_unpriced')::int = 1
      and (a->'s7_overlap'->>'price_adds_reverse')::int = 0 and (a->'s7_overlap'->>'price_adds_when_current_has_both')::int = 0));
    -- 8 price enrichment: the current menu (copy2) lost one price (stored NULL, item_keys refreshed); the capture has it
    select i.id into item_x from public.menu_sections s join public.menu_items i on i.section_id=s.id
     where s.menu_id=cur2 and i.price is not null order by s.section_position, s.id, i.item_position, i.id offset 5 limit 1;
    update public.menu_items set price = null where id = item_x;
    update public.menus set item_keys = public.phg_menu_item_keys(cur2), item_set_hash = public.phg_menu_key_set_hash(public.phg_menu_item_keys(cur2)) where id = cur2;
    a := a || jsonb_build_object('s8_setup', jsonb_build_object('item_without_price', item_x,
       'overlap_capture_vs_current', public.phg_menu_keys_overlap(public.phg_menu_payload_item_keys(secs2), public.phg_menu_item_keys(cur2)),
       'capture_keys', cardinality(public.phg_menu_payload_item_keys(secs2)),
       'price_adds', public.phg_menu_keys_price_adds(public.phg_menu_payload_item_keys(secs2), public.phg_menu_item_keys(cur2))));
    -- 8a same source (copy2): before round 3 this was 'duplicate_of_current'; now a same-source replacement
    BEGIN
      {call("'https://rehearsal.example.com/copy2'", 'reh8a', 'secs2')}{after('s8a_price_enrichment_same_source', "res->>'status'='created' and res->>'reason'='same_source_price_enrichment' and cur_now<>cur2")}
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 8a';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    -- 8b another source, same size, current menu minutes old: not a duplicate, and damping does not hold back a price
    BEGIN
      {call("'https://rehearsal.example.com/copy8'", 'reh8b', 'secs2')}{after('s8b_price_enrichment_other_source', "res->>'status'='created' and res->>'reason'='price_enrichment_other_source' and cur_now<>cur2")}
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback 8b';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    a := a || jsonb_build_object('final_acct_menus', (select jsonb_agg(jsonb_build_object('url',evidence_url,'is_current',is_current,'reason',superseded_reason,'n',cardinality(item_keys)) order by created_at, id) from public.menus where account_id=acct),
       'multi_current_global_end', {MULTI});
    RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback scenarios';
  EXCEPTION
    WHEN sqlstate 'P0099' THEN NULL;
    WHEN others THEN {soft_err('ERROR_A', 'a')}
  END;
  r := r || jsonb_build_object('A', a, 'A_ms', {MS});""" + END

# ---------------------------------------------------------------- block B: files 1-2, B checks, promote, extraction save
B_CHECKS = f"""
  t0 := clock_timestamp();
  BEGIN
    b := b || jsonb_build_object(
      'repair_run', (select jsonb_object_agg(step, detail) from public.phg_repair_run_20260927),
      'unique_index_exists', to_regclass('public.menus_one_current_per_account') is not null,
      'multi_current_global', {MULTI},
      'touched_venues', (select count(distinct account_id) from public.phg_repair_plan_menus_20260927),
      'damaged_saved', (select count(*) from public.phg_repair_damaged_20260927),
      'damaged_not_restored_recount', (select count(*) from public.phg_repair_damaged_20260927 d
          where coalesce((select max(cardinality(coalesce(m.item_keys,'{{}}'))) from public.menus m where m.account_id=d.account_id and m.is_current),0) < d.old_max_n),
      'touched_with_pre_incident_menu', (select count(distinct p.account_id) from public.phg_repair_plan_menus_20260927 p where p.created_at < '2026-09-27 00:00:00+00'),
      'touched_without_current', (select count(*) from (select distinct account_id from public.phg_repair_plan_menus_20260927) t where not exists (select 1 from public.menus m where m.account_id=t.account_id and m.is_current)),
      'backfill_null_item_keys', (select count(*) from public.menus where item_keys is null),
      'changed_by_reason', (select jsonb_object_agg(k, cnt) from (select k, count(*) cnt from (
          select distinct on (ch.account_id) ch.account_id,
                 case when o.id is null then 'no_prior_current' when ch.n>o.n then 'more_items' when ch.n=o.n and ch.bev>o.bev then 'same_n_more_bev'
                      when ch.n=o.n and ch.bev=o.bev and ch.itemish<o.itemish then 'same_n_bev_real_page' when (ch.n,ch.bev,ch.itemish)=(o.n,o.bev,o.itemish) then 'exact_tie' else 'other' end k
            from public.phg_repair_plan_menus_20260927 ch
            left join public.phg_repair_plan_menus_20260927 o on o.account_id=ch.account_id and o.was_current and o.id<>ch.id
           where ch.make_current and not ch.was_current order by ch.account_id, o.n desc nulls last) z group by k) y),
      'backup_privs_service_role_insert', jsonb_build_object(
          'function_defs', has_table_privilege('service_role','public.phg_backup_function_defs_20260927','INSERT'),
          'menus_currency', has_table_privilege('service_role','public.phg_backup_menus_currency_20260927','INSERT'),
          'staging_dupes', has_table_privilege('service_role','public.phg_backup_staging_dupes_20260927','INSERT')),
      'plan_rows', (select count(*) from public.phg_repair_plan_menus_20260927),
      'backup_privs_service_role', (select jsonb_object_agg(t, jsonb_build_object(
            'select', has_table_privilege('service_role', t, 'SELECT'), 'insert', has_table_privilege('service_role', t, 'INSERT'),
            'update', has_table_privilege('service_role', t, 'UPDATE'), 'delete', has_table_privilege('service_role', t, 'DELETE'),
            'truncate', has_table_privilege('service_role', t, 'TRUNCATE'), 'trigger', has_table_privilege('service_role', t, 'TRIGGER'),
            'references', has_table_privilege('service_role', t, 'REFERENCES')))
          from unnest(array['public.phg_backup_function_defs_20260927','public.phg_backup_menus_currency_20260927','public.phg_backup_staging_dupes_20260927']) t),
      'batch_proconfig', (select jsonb_object_agg(proname, proconfig) from pg_proc where proname in ('phg_repair_step3_batch','phg_repair_step4_batch')),
      'real_multi_current_backup_venues', (select count(*) from (select account_id from public.phg_backup_menus_currency_20260927 where is_current group by 1 having count(*) > 1) x));
    b := b || jsonb_build_object('pass',
          (b->>'unique_index_exists')::boolean and (b->>'multi_current_global')::int = 0 and (b->>'touched_without_current')::int = 0
      and (b->>'damaged_not_restored_recount')::int = 0 and (b->'repair_run'->'step2'->>'damaged_not_restored')::int = 0
      and (b->>'damaged_saved')::int > 0 and (b->>'backfill_null_item_keys')::int = 0
      and not exists (select 1 from jsonb_each(b->'backup_privs_service_role') t, jsonb_each_text(t.value) pr
                       where (pr.key = 'select') <> pr.value::boolean)
      and (select bool_and(x.value::text ~ 'lock_timeout=5s') from jsonb_each(b->'batch_proconfig') x));
  EXCEPTION WHEN others THEN {soft_err('ERROR_B', 'b')}
  END;
  r := r || jsonb_build_object('B', b, 'B_ms', {MS});"""

PROMOTE = f"""
  t0 := clock_timestamp();
  BEGIN
    -- The promotion queue is empty today (v_menu_staging_promotion_candidates = 0 rows). Re-stage one incident item
    -- page's 13 beverage rows under a NEW sibling ?item= URL: same items, new content hash (the incident pattern).
    update public.staging_menu_extract
       set menu_page_url = '{PROMO_NEW_URL}', promoted_at = null, promotion_status = null, quality_status = 'promotion_ready'
     where account_id = '{PROMO_ACCT}' and menu_page_url = '{PROMO_URL}' and superseded_at is null;
    get diagnostics rem = row_count;
    select id into cur_id from public.menus where account_id = '{PROMO_ACCT}' and is_current;
    t1 := clock_timestamp();
    res := public.promote_clean_menu_batch(1);
    c := jsonb_build_object('rows_requeued', rem, 'result', res, 'ms', round(extract(epoch from clock_timestamp()-t1)*1000),
      'current_unchanged', (select id from public.menus where account_id = '{PROMO_ACCT}' and is_current) = cur_id,
      'acct_menus_created', (select count(*) from public.menus where account_id = '{PROMO_ACCT}' and created_at >= now()),
      'staging_outcome', (select jsonb_object_agg(coalesce(promotion_status,'(null)'), n) from (select promotion_status, count(*) n from public.staging_menu_extract
                            where account_id = '{PROMO_ACCT}' and menu_page_url = '{PROMO_NEW_URL}' group by 1) x),
      'multi_current_global', {MULTI});
    c := c || jsonb_build_object('pass', coalesce((res->>'failed')::int, 1) = 0 and (res->>'created')::int = 0
              and (coalesce((res->>'alternate')::int,0)+coalesce((res->>'duplicate')::int,0)+coalesce((res->>'held_subset')::int,0)) = 1
              and (c->>'current_unchanged')::boolean and (c->>'multi_current_global')::int = 0 and (c->>'acct_menus_created')::int = 0);
    RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback promote';
  EXCEPTION
    WHEN sqlstate 'P0099' THEN NULL;
    WHEN others THEN {soft_err('ERROR', 'c')}
  END;
  r := r || jsonb_build_object('promote_clean_menu_batch_1', c); c := '{{}}';"""

EXTRACT = f"""
  t0 := clock_timestamp();
  BEGIN
    -- sibling page {SIB_ID} (/happyhour) keeps its staged set; Step 4's formula gives it item_set_hash
    update public.menu_source_candidates mc set item_set_hash = x.h
      from (select public.phg_menu_key_set_hash(array_agg(distinct public.phg_menu_item_key(item_name, item_price)
                                                          order by public.phg_menu_item_key(item_name, item_price))) h
              from public.staging_menu_extract s join public.menu_source_candidates sc on sc.id = {SIB_ID}
             where s.account_id = sc.account_id and s.menu_page_url = sc.source_url and s.superseded_at is null and s.item_type <> 'summary') x
     where mc.id = {SIB_ID};
    -- the worker re-extracts candidate {CAND_ID} (/menu) and gets the same priced items (the incident pattern)
    select jsonb_agg(jsonb_build_object('item_name', s.item_name, 'item_price', s.item_price, 'item_type', s.item_type,
                                        'section_name', s.section_name, 'spirit_brands', s.spirit_brands) order by s.id)
      into items from public.staging_menu_extract s join public.menu_source_candidates sc on sc.id = {SIB_ID}
     where s.account_id = sc.account_id and s.menu_page_url = sc.source_url and s.superseded_at is null and s.item_type <> 'summary';
    update public.phg_menu_worker_leases set owner = lease_owner, lease_until = now() + interval '10 minutes' where lane = 'candidate_extraction';
    update public.menu_source_candidates set status = 'processing', last_attempt_at = claimed where id = {CAND_ID};
    t1 := clock_timestamp();
    res := public.phg_save_menu_candidate_extraction({CAND_ID}, claimed, lease_owner, items, 'rehearsal source text', 'rehearsal', 'html');
    c := jsonb_build_object('result', res, 'call_ms', round(extract(epoch from clock_timestamp()-t1)*1000), 'items_sent', jsonb_array_length(items),
      'candidate_after', (select jsonb_build_object('status', status, 'duplicate_of', duplicate_of_candidate_id, 'item_set_hash', item_set_hash) from public.menu_source_candidates where id = {CAND_ID}),
      'new_staged_rows_for_candidate_page', (select count(*) from public.staging_menu_extract s join public.menu_source_candidates mc on mc.id = {CAND_ID}
                                              where s.account_id = mc.account_id and s.menu_page_url = mc.source_url and s.superseded_at is null and s.loaded_at >= now()));
    c := c || jsonb_build_object('pass', res->>'status' = 'review' and (res->>'duplicate_of')::bigint = {SIB_ID}
                                        and (c->>'new_staged_rows_for_candidate_page')::int = 0
                                        and (c->'candidate_after'->>'duplicate_of')::bigint = {SIB_ID});
    RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback extraction';
  EXCEPTION
    WHEN sqlstate 'P0099' THEN NULL;
    WHEN others THEN {soft_err('ERROR', 'c')}
  END;
  r := r || jsonb_build_object('extraction_sibling_duplicate', c); c := '{{}}';"""

MONITOR = f"""
  -- phg_026_monitor.sql in the rehearsed post-repair state, the baseline for its 1.2 threshold, and a replay over the
  -- incident window (step2.ran_at moved back to 2026-09-27 00:00Z) to show the check fails on incident data
  t0 := clock_timestamp();
  BEGIN
    EXECUTE 'select jsonb_agg(to_jsonb(g)) from (' || $rehearse_mon${mon}
$rehearse_mon$ || ') g' INTO v;
    c := jsonb_build_object('monitor_post_repair', v, 'monitor_ms', {MS});
    c := c || jsonb_build_object('menus_per_item_set_by_day', (select jsonb_object_agg(d, jsonb_build_object('menus', n, 'sets', sets, 'ratio', r)) from (
            select created_at::date::text d, count(*) n, count(distinct (account_id, item_set_hash)) sets,
                   round(count(*)::numeric / nullif(count(distinct (account_id, item_set_hash)), 0), 3) r
              from public.menus group by 1) x),
       'menus_per_item_set_windows', (select jsonb_object_agg(w, jsonb_build_object('menus', n, 'sets', sets, 'ratio', r)) from (
            select case when created_at < '2026-09-27 00:00:00+00' then 'pre_incident' else 'incident_window' end w, count(*) n,
                   count(distinct (account_id, item_set_hash)) sets,
                   round(count(*)::numeric / nullif(count(distinct (account_id, item_set_hash)), 0), 3) r
              from public.menus group by 1) x));
    update public.phg_repair_run_20260927 set ran_at = '2026-09-27 00:00:00+00' where step = 'step2';
    EXECUTE 'select jsonb_agg(to_jsonb(g)) from (' || $rehearse_mon${mon}
$rehearse_mon$ || ') g' INTO v;
    c := c || jsonb_build_object('monitor_replay_incident_window', v);
    RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback monitor replay';
  EXCEPTION
    WHEN sqlstate 'P0099' THEN NULL;
    WHEN others THEN {soft_err('ERROR', 'c')}
  END;
  r := r || jsonb_build_object('monitor', c); c := '{{}}';"""

B = DECL + run_file('file1', '$rehearse_f1$', f1) + run_file('file2', '$rehearse_f2$', f2) + B_CHECKS + EXTRACT + MONITOR + END


# ---------------------------------------------------------------- blocks C/D: steps 3-4, gate, rollbacks, submit after
def steps(step3_budget_ms, step4_budget_ms, step3_max_calls):
    return f"""
  -- Step 3: phg_repair_step3_batch(100) until done, the time budget, or the call cap
  calls := '[]'; rem := -1;
  WHILE rem <> 0 and jsonb_array_length(calls) < {step3_max_calls}
        and coalesce((select sum((x->>'ms')::numeric) from jsonb_array_elements(calls) x), 0) < {step3_budget_ms} LOOP
    t0 := clock_timestamp();
    rem := public.phg_repair_step3_batch(100);
    calls := calls || jsonb_build_object('ms', {MS}, 'remaining_venues', rem);
  END LOOP;
  r := r || jsonb_build_object('step3', jsonb_build_object('calls', calls,
     'backup_rows', (select count(*) from public.phg_backup_staging_dupes_20260927),
     'venues_done', (select count(*) from public.phg_repair_step3_done)));
  -- Step 4: phg_repair_step4_batch(200)
  calls := '[]'; rem := -1;
  WHILE rem <> 0 and coalesce((select sum((x->>'ms')::numeric) from jsonb_array_elements(calls) x), 0) < {step4_budget_ms} LOOP
    t0 := clock_timestamp();
    rem := public.phg_repair_step4_batch(200);
    calls := calls || jsonb_build_object('ms', {MS}, 'remaining_venues', rem);
  END LOOP;
  r := r || jsonb_build_object('step4', jsonb_build_object('calls', calls,
     'hashed', (select count(*) from public.menu_source_candidates where item_set_hash is not null)));"""


GATE = f"""
  -- runbook step 4 index (CONCURRENTLY in the runbook; plain here because CONCURRENTLY cannot run in a transaction)
  t0 := clock_timestamp();
  create index if not exists menu_source_candidates_item_set_idx on public.menu_source_candidates (account_id, item_set_hash) where item_set_hash is not null;
  r := r || jsonb_build_object('cand_index_ms', {MS});
  t0 := clock_timestamp();
  BEGIN
    EXECUTE 'select jsonb_agg(to_jsonb(g)) from (' || $rehearse_gate${gate}
$rehearse_gate$ || ') g' INTO v;
    r := r || jsonb_build_object('release_gate', v, 'release_gate_ms', {MS});
  EXCEPTION WHEN others THEN {soft_err('release_gate', 'r')}
  END;"""

REPAIR_RB = f"""
  -- repair rollback (after step 3, including the staging restore)
  t0 := clock_timestamp();
  BEGIN
    res := public.phg_repair_20260927_rollback();
    c := jsonb_build_object('result', res, 'ms', {MS}, 'multi_current_global', {MULTI},
      'currency_mismatch_vs_backup', (select count(*) from public.menus m join public.phg_backup_menus_currency_20260927 bk on bk.id=m.id
                                       where (m.is_current, m.superseded_by, m.superseded_reason, m.superseded_at)
                                             is distinct from (bk.is_current, bk.superseded_by, bk.superseded_reason, bk.superseded_at)),
      'staging_backup_rows', (select count(*) from public.phg_backup_staging_dupes_20260927),
      'staging_still_superseded_by_repair', (select count(*) from public.staging_menu_extract s join public.phg_backup_staging_dupes_20260927 bk on bk.staging_id=s.id
                                              where s.superseded_reason = 'duplicate_item_set_of_sibling'));
    c := c || jsonb_build_object('pass', (c->>'multi_current_global')::int = 0 and (c->>'currency_mismatch_vs_backup')::int = 0
                                        and (c->>'staging_still_superseded_by_repair')::int = 0
                                        and (res->>'staging_rows_restored')::int = (c->>'staging_backup_rows')::int);
  EXCEPTION WHEN others THEN {soft_err('ERROR', 'c')}
  END;
  r := r || jsonb_build_object('repair_rollback', c); c := '{{}}';
"""

FN_RB = f"""
  -- function rollback, then ONE submit_menu call (the restored live 15-arg body) on a venue with a current menu
  t0 := clock_timestamp();
  BEGIN
    c := jsonb_build_object('fn_rollback_returns', public.phg_rollback_function_defs_20260927(), 'ms', {MS});
    -- a separate statement: catalog reads in the same statement as the rollback call would see the old snapshot
    c := c || jsonb_build_object(
      'unique_index_after', to_regclass('public.menus_one_current_per_account') is not null,
      'submit_menu_10arg_exists_after', to_regprocedure('public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb)') is not null,
      'restored_body_is_live', (select prosrc !~ 'phg_menu_source_key' from pg_proc where oid = 'public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb,text,text,text,text,boolean)'::regprocedure),
      'anon_or_authenticated_can_execute', (select jsonb_object_agg(b.signature, has_function_privilege('anon', b.signature::regprocedure, 'EXECUTE')
                                                                        or has_function_privilege('authenticated', b.signature::regprocedure, 'EXECUTE'))
                                              from public.phg_backup_function_defs_20260927 b),
      'service_role_can_execute', (select bool_and(has_function_privilege('service_role', b.signature::regprocedure, 'EXECUTE')) from public.phg_backup_function_defs_20260927 b));
    select id into cur_id from public.menus where account_id = acct and is_current;
    t1 := clock_timestamp();
    {call("'https://rehearsal.example.com/after-rollback'", 'rehrb', J5)}
    c := c || jsonb_build_object('submit_after_rollback', res, 'submit_ms', round(extract(epoch from clock_timestamp()-t1)*1000),
      'acct_current_count', (select count(*) from public.menus where account_id = acct and is_current),
      'old_current_demoted', (select not is_current from public.menus where id = cur_id));
    c := c || jsonb_build_object('pass', (c->>'fn_rollback_returns')::int = 4 and not (c->>'unique_index_after')::boolean
                                        and (c->>'submit_menu_10arg_exists_after')::boolean and (c->>'restored_body_is_live')::boolean
                                        and not exists (select 1 from jsonb_each_text(c->'anon_or_authenticated_can_execute') e where e.value::boolean)
                                        and (c->>'service_role_can_execute')::boolean
                                        and res ? 'menu_id' and (c->>'acct_current_count')::int = 1 and (c->>'old_current_demoted')::boolean);
  EXCEPTION WHEN others THEN {soft_err('ERROR', 'c')}
  END;
  r := r || jsonb_build_object('function_rollback_and_submit', c); c := '{{}}';"""


# C: timing - as much of Step 3 as fits in ~40 s
C = DECL + run_file('file1', '$rehearse_f1$', f1) + run_file('file2', '$rehearse_f2$', f2) + steps(30000, 0, 100) + END
# D: a few batches of each step, then the gate, the repair rollback (with staging restore), function rollback + submit
# D: one Step 3 call and one Step 4 call, then the gate, the repair rollback (with staging restore), function rollback + submit
D = DECL + run_file('file1', '$rehearse_f1$', f1) + run_file('file2', '$rehearse_f2$', f2) + steps(1, 1, 1) + GATE + REPAIR_RB + FN_RB + END
# E: promote_clean_menu_batch(1) on a re-staged incident sibling page, one more Step 4 call, then the function
#    rollback + submit_menu again (its catalog check fixed to run in a separate statement)
E = DECL + run_file('file1', '$rehearse_f1$', f1) + run_file('file2', '$rehearse_f2$', f2) + PROMOTE + steps(0, 1, 0) + FN_RB + END

# F: SF10 - the design score-gate migration and its new rollback function (the migration is not applied live)
SIGS = "(select jsonb_agg(p.oid::regprocedure::text order by 1) from pg_proc p where p.proname in ('phg_design_proposal_submit','phg_design_proposal_score','phg_design_proposal_review','phg_design_status'))"
F = DECL + run_file('file3', '$rehearse_f3$', f3) + f"""
  BEGIN
    r := r || jsonb_build_object('after_migration', jsonb_build_object('fns', {SIGS},
      'backup_rows', (select count(*) from public.phg_backup_design_fn_defs_20260928),
      'null_layout_is_rejected', (select prosrc ~ 'coalesce\\(jsonb_typeof\\(p_layout' from pg_proc where proname = 'phg_design_proposal_submit')));
    r := r || jsonb_build_object('backup_privs_service_role', jsonb_build_object(
       'select', has_table_privilege('service_role','public.phg_backup_design_fn_defs_20260928','SELECT'),
       'insert', has_table_privilege('service_role','public.phg_backup_design_fn_defs_20260928','INSERT'),
       'trigger', has_table_privilege('service_role','public.phg_backup_design_fn_defs_20260928','TRIGGER'),
       'references', has_table_privilege('service_role','public.phg_backup_design_fn_defs_20260928','REFERENCES')));
    -- approve path (round 4): a throwaway task; everything in this sub-block is rolled back
    BEGIN
      ddoc := '{{"sections":[{{"name":"Rehearsal Cocktails","items":[]}}]}}';
      dlayout := '{{"page":{{"w":612,"h":792}},"elements":[]}}';
      insert into phg.menu_design_tasks (menu_project_id, source, request, base_doc)
      values ((select id from phg.menu_projects order by id limit 1), 'coordinator', 'PHG-026 round 4 rehearsal', ddoc) returning id into tid;
      v := jsonb_build_object('submit_null_layout', public.phg_design_proposal_submit(tid, ddoc)->>'status');
      res := public.phg_design_proposal_submit(tid, ddoc, p_layout => dlayout);
      pid := (res->>'proposal_id')::uuid;
      v := v || jsonb_build_object('submit_with_layout', res->>'status');
      secs := (select jsonb_object_agg(k::text, 90) from generate_series(1, 14) k);
      perform public.phg_design_proposal_score(pid, 'design_critic', secs);
      perform public.phg_design_proposal_score(pid, 'content_reviewer', secs);
      perform public.phg_design_proposal_score(pid, 'accuracy_reviewer', secs || '{{"10":80,"11":80,"12":80,"13":80,"14":80}}');
      v := v || jsonb_build_object('approve_accuracy_at_80', public.phg_design_proposal_review(pid, true));
      perform public.phg_design_proposal_score(pid, 'accuracy_reviewer', secs);
      update phg.menu_design_proposals set layout = null where id = pid;
      v := v || jsonb_build_object('approve_layout_null', public.phg_design_proposal_review(pid, true));
      update phg.menu_design_proposals set layout = '{{"page":{{"w":612}}}}' where id = pid;
      v := v || jsonb_build_object('approve_layout_no_elements', public.phg_design_proposal_review(pid, true),
                                   'status_after_blocked', (select status from phg.menu_design_proposals where id = pid));
      update phg.menu_design_proposals set layout = dlayout where id = pid;
      v := v || jsonb_build_object('approve_ok', public.phg_design_proposal_review(pid, true),
                                   'status_after_approve', (select status from phg.menu_design_proposals where id = pid));
      v := v || jsonb_build_object('pass', v->>'submit_null_layout' = 'auto_rejected' and v->>'submit_with_layout' = 'submitted'
        and v->'approve_accuracy_at_80'->>'status' = 'blocked_by_score_gate' and (v->'approve_accuracy_at_80'->>'accuracy_reviewer')::numeric = 80
        and v->'approve_layout_null'->>'status' = 'blocked_by_layout_gate' and v->'approve_layout_no_elements'->>'status' = 'blocked_by_layout_gate'
        and v->>'status_after_blocked' = 'submitted' and v->'approve_ok'->>'status' = 'approved'
        and (v->'approve_ok'->>'accuracy_reviewer')::numeric = 90 and (v->'approve_ok'->>'design_critic')::numeric = 90
        and (v->'approve_ok'->>'content_reviewer')::numeric = 90 and v->>'status_after_approve' = 'approved');
      r := r || jsonb_build_object('approve_path', v);
      RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback approve path';
    EXCEPTION WHEN sqlstate 'P0099' THEN NULL;
    END;
    r := r || jsonb_build_object('rollback_returns', public.phg_rollback_design_score_gate_20260928());
    r := r || jsonb_build_object('after_rollback', jsonb_build_object('fns', {SIGS},
      'anon_or_auth_exec', (select bool_or(has_function_privilege('anon', p.oid, 'EXECUTE') or has_function_privilege('authenticated', p.oid, 'EXECUTE'))
                              from pg_proc p where p.proname like 'phg_design_proposal%' or p.proname = 'phg_design_status'),
      'service_role_exec', (select bool_and(has_function_privilege('service_role', p.oid, 'EXECUTE'))
                              from pg_proc p where p.proname like 'phg_design_proposal%' or p.proname = 'phg_design_status'),
      'review_body_restored', (select prosrc !~ 'accuracy_reviewer' from pg_proc where proname = 'phg_design_proposal_review')));
  EXCEPTION WHEN others THEN {soft_err('ERROR', 'r')}
  END;""" + END

# G (round 4): the rollback skip paths. After Step 2 and one Step 3 call:
#  - one NEW menu is submitted for a plan venue whose current menu Step 2 changed (skip_acct) -> skipped, untouched;
#  - the currency backup of another changed plan venue (multi_acct) is forged to show 2 current menus -> skipped and
#    reported, the rollback does not abort;
#  - one new staging row is loaded for a backed-up page of a third venue (stg_acct) -> that page's rows stay superseded.
MENU_SNAP = ("(select jsonb_agg(jsonb_build_object('id',m.id,'c',m.is_current,'by',m.superseded_by,'r',m.superseded_reason,"
             "'at',m.superseded_at) order by m.id) from public.menus m where m.account_id={a})")
MSNAP_SKIP = MENU_SNAP.format(a='skip_acct')
MSNAP_MULTI = MENU_SNAP.format(a='multi_acct')
G = DECL + run_file('file1', '$rehearse_f1$', f1) + run_file('file2', '$rehearse_f2$', f2) + steps(1, 0, 1) + f"""
  t0 := clock_timestamp();
  BEGIN
    select p.account_id into skip_acct from public.phg_repair_plan_menus_20260927 p
     where p.make_current and not p.was_current
     order by exists (select 1 from public.phg_backup_staging_dupes_20260927 b where b.account_id = p.account_id) desc, p.account_id limit 1;
    select id into cur_id from public.menus where account_id = skip_acct and is_current;
    select jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',i.item_name,'item_type',i.item_type,'price',i.price) order by i.item_position, i.id)
                                 from public.menu_items i where i.section_id=s.id),'[]'::jsonb)
                     || case when s.section_position = (select min(section_position) from public.menu_sections where menu_id=cur_id)
                             then '[{{"item_name":"Rehearsal Skip-Path Pour","item_type":"spirit_pour","price":13}}]'::jsonb else '[]'::jsonb end) order by s.section_position, s.id)
      into secs from public.menu_sections s where s.menu_id = cur_id;
    {call("'https://rehearsal.example.com/skip-path'", 'rehG', 'secs', acct='skip_acct')}
    g := jsonb_build_object('skip_acct', skip_acct, 'submit', res - 'brand_references' - 'inferred_from_cocktail_reference',
       'skip_acct_staging_backup_rows', (select count(*) from public.phg_backup_staging_dupes_20260927 where account_id = skip_acct));
    snap := {MSNAP_SKIP};
    n1 := (select count(*) from public.staging_menu_extract s join public.phg_backup_staging_dupes_20260927 b on b.staging_id = s.id
            where b.account_id = skip_acct and s.superseded_reason = 'duplicate_item_set_of_sibling');
    -- forge a 2-current backup for another changed plan venue
    select p.account_id into multi_acct from public.phg_repair_plan_menus_20260927 p
     where p.make_current and not p.was_current and p.account_id <> skip_acct order by p.account_id limit 1;
    update public.phg_backup_menus_currency_20260927 b set is_current = true
      from public.phg_repair_plan_menus_20260927 p where p.id = b.id and p.account_id = multi_acct and p.make_current and not p.was_current;
    snap2 := {MSNAP_MULTI};
    -- a new staging row for a backed-up page of a venue that will be rolled back (loaded_at explicit: in one
    -- transaction now() equals backed_up_at; in production they are separate transactions)
    select b.account_id, b.menu_page_url into stg_acct, stg_url from public.phg_backup_staging_dupes_20260927 b
     where b.account_id not in (skip_acct, multi_acct) order by b.account_id, b.menu_page_url limit 1;
    insert into public.staging_menu_extract (menu_page_url, menu_format, account_id, item_type, item_name, item_price, loaded_at)
    values (stg_url, 'html', stg_acct, 'other', 'Rehearsal Re-extracted Item', 9, clock_timestamp());
    n2 := (select count(*) from public.phg_backup_staging_dupes_20260927 b where b.account_id = stg_acct and b.menu_page_url = stg_url);
    g := g || jsonb_build_object('multi_acct', multi_acct, 'stg_acct', stg_acct, 'stg_page_backup_rows', n2);
    t1 := clock_timestamp();
    res := public.phg_repair_20260927_rollback();
    g := g || jsonb_build_object('rollback', res, 'rollback_ms', round(extract(epoch from clock_timestamp()-t1)*1000),
      'skip_acct_menus_untouched', {MSNAP_SKIP} = snap,
      'skip_acct_current_is_new_menu', (select id from public.menus where account_id = skip_acct and is_current) = (res->>'menu_id')::uuid,
      'skip_acct_staging_still_superseded', (select count(*) from public.staging_menu_extract s join public.phg_backup_staging_dupes_20260927 b on b.staging_id = s.id
            where b.account_id = skip_acct and s.superseded_reason = 'duplicate_item_set_of_sibling') = n1,
      'multi_acct_menus_untouched', {MSNAP_MULTI} = snap2,
      'multi_acct_current_count', (select count(*) from public.menus where account_id = multi_acct and is_current),
      'stg_page_rows_still_superseded', (select count(*) from public.staging_menu_extract s join public.phg_backup_staging_dupes_20260927 b on b.staging_id = s.id
            where b.account_id = stg_acct and b.menu_page_url = stg_url and s.superseded_reason = 'duplicate_item_set_of_sibling'),
      'other_backup_rows_not_restored', (select count(*) from public.staging_menu_extract s join public.phg_backup_staging_dupes_20260927 b on b.staging_id = s.id
            where b.account_id not in (skip_acct, multi_acct) and not (b.account_id = stg_acct and b.menu_page_url = stg_url)
              and s.superseded_reason = 'duplicate_item_set_of_sibling'),
      'currency_mismatch_vs_backup_rolled_back_venues', (select count(*) from public.menus m join public.phg_backup_menus_currency_20260927 bk on bk.id = m.id
            where m.account_id not in (skip_acct, multi_acct)
              and (m.is_current, m.superseded_by, m.superseded_reason, m.superseded_at)
                  is distinct from (bk.is_current, bk.superseded_by, bk.superseded_reason, bk.superseded_at)),
      'multi_current_global', {MULTI});
    g := g || jsonb_build_object('pass', (res->>'venues_skipped_newer_menu')::int >= 1 and (res->>'venues_skipped_multi_current_backup')::int >= 1
      and (g->>'skip_acct_menus_untouched')::boolean and (g->>'skip_acct_staging_still_superseded')::boolean
      and (g->>'multi_acct_menus_untouched')::boolean and (g->>'multi_acct_current_count')::int = 1
      and (g->>'stg_page_rows_still_superseded')::int = n2 and n2 > 0
      and (g->>'other_backup_rows_not_restored')::int = 0 and (g->>'currency_mismatch_vs_backup_rolled_back_venues')::int = 0
      and (g->>'multi_current_global')::int = 0);
  EXCEPTION WHEN others THEN {soft_err('ERROR', 'g')}
  END;
  r := r || jsonb_build_object('G', g, 'G_ms', {MS});""" + END

blocks = {'A': A, 'B': B, 'C': C, 'D': D, 'E': E, 'F': F, 'G': G}
allsql = []
for k, sql in blocks.items():
    (HERE / f'rehearse_round4_{k}.sql').write_text(sql)
    allsql.append(f'-- ===== block {k} (run on its own; ends in RAISE EXCEPTION, so everything rolls back) =====\n' + sql)
(HERE / 'rehearse_round4.sql').write_text('\n'.join(allsql))
print({k: len(v) for k, v in blocks.items()})
