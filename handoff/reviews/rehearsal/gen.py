import pathlib
M='/home/user/phg-harmony-app/supabase/migrations/'
f1=pathlib.Path(M+'20260927190000_phg_menu_dedupe_one_current.sql').read_text()
f2=pathlib.Path(M+'20260927191000_phg_menu_repair_20260927.sql').read_text()
for tag in ('$rehearse_f1$','$rehearse_f2$','$rehearse_main$'):
    assert tag not in f1 and tag not in f2
MULTI="(select count(*) from (select account_id from public.menus where is_current group by 1 having count(*)>1) x)"
def after(label):
    return f"""
    a := a || jsonb_build_object('{label}', res || jsonb_build_object(
       'current_after', (select id from public.menus where account_id=acct and is_current limit 1),
       'acct_current_count', (select count(*) from public.menus where account_id=acct and is_current),
       'multi_current_global', {MULTI}));"""
def call(url, hashseed, sections):
    return f"res := public.submit_menu(acct,'NBCC-FIRECRAWL-MENUS',{url},null,'html','unknown','test',null,md5('{hashseed}'||clock_timestamp()::text),{sections},null,null,null,null,false);"
J3='\'[{"section_name":"Order","section_type":"unsectioned","section_position":1,"items":[{"item_name":"Rehearsal Item A","item_type":"other","price":9},{"item_name":"Rehearsal Item B","item_type":"other","price":10}]}]\'::jsonb'
J5='\'[{"section_name":"Food","section_type":"unsectioned","section_position":1,"items":[{"item_name":"Rehearsal Fries","item_type":"other","price":7},{"item_name":"Rehearsal Burger","item_type":"other","price":15}]}]\'::jsonb'
sql=f"""DO $rehearse_main$
DECLARE
  r jsonb := '{{}}'; a jsonb := '{{}}'; b jsonb := '{{}}'; c jsonb := '{{}}';
  t0 timestamptz; acct text := 'ACC-CO-LED-03-25486';
  cur_id uuid; cur2 uuid; secs jsonb; secs2 jsonb; secs4 jsonb; res jsonb;
  e_state text; e_msg text; e_ctx text; e_det text;
BEGIN
  -- ================= file 1 =================
  t0 := clock_timestamp();
  BEGIN
    EXECUTE $rehearse_f1${f1}$rehearse_f1$;
  EXCEPTION WHEN others THEN
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
    RAISE EXCEPTION 'REHEARSAL %', jsonb_build_object('stage','file1','sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx,'ms',round(extract(epoch from clock_timestamp()-t0)*1000));
  END;
  r := r || jsonb_build_object('file1_ms', round(extract(epoch from clock_timestamp()-t0)*1000));

  -- ================= checks A (rolled back to a savepoint afterwards) =================
  t0 := clock_timestamp();
  BEGIN
    a := a || jsonb_build_object('backup_rows', (select count(*) from public.phg_backup_function_defs_20260927),
       'backup_sigs', (select jsonb_agg(signature order by signature) from public.phg_backup_function_defs_20260927),
       'submit_menu_10arg_exists', to_regprocedure('public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb)') is not null,
       'submit_menu_15arg_exists', to_regprocedure('public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb,text,text,text,text,boolean)') is not null,
       'multi_current_global_before', {MULTI});
    select id into cur_id from public.menus where account_id=acct and is_current;
    a := a || jsonb_build_object('account', acct, 'orig_current', cur_id,
       'orig_distinct_keys', cardinality(public.phg_menu_item_keys(cur_id)), 'orig_bev', public.phg_menu_bev_count(cur_id));
    with it as (select s.id sid, i.*, row_number() over (order by s.section_position, s.id, i.item_position, i.id) rn
                  from public.menu_sections s join public.menu_items i on i.section_id=s.id where s.menu_id=cur_id)
    select jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',it.price,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)) order by s.section_position, s.id),
           jsonb_agg(jsonb_build_object('section_name',s.section_name,'section_type',s.section_type,'section_position',s.section_position,
             'items',coalesce((select jsonb_agg(jsonb_build_object('item_name',it.item_name,'item_type',it.item_type,'price',case when it.rn<=3 then coalesce(it.price,0)+1 else it.price end,'item_position',it.item_position) order by it.rn) from it where it.sid=s.id),'[]'::jsonb)) order by s.section_position, s.id)
      into secs, secs2 from public.menu_sections s where s.menu_id=cur_id;

    -- 1 exact copy from another URL
    {call("'https://rehearsal.example.com/copy1'", 'reh1', 'secs')}{after('s1_exact_copy_other_url')}
    -- 2 same items, 3 prices changed, another URL
    {call("'https://rehearsal.example.com/copy2'", 'reh2', 'secs2')}{after('s2_three_prices_changed_other_url')}
    select id into cur2 from public.menus where account_id=acct and is_current;
    -- 3 ?item= page on current URL with 2 new items
    {call("'https://rehearsal.example.com/copy2?item=abc'", 'reh3', J3)}{after('s3_item_page_same_url')}
    -- 4 same URL as current, 10 items (5 current + 5 new) < half of 33
    select jsonb_build_array(jsonb_build_object('section_name','Partial','section_type','unsectioned','section_position',1,'items',
             (select jsonb_agg(x) from (
                (select jsonb_build_object('item_name',i.item_name,'item_type','other','price',i.price) x
                   from public.menu_sections s join public.menu_items i on i.section_id=s.id where s.menu_id=cur2 order by i.id limit 5)
                union all
                select jsonb_build_object('item_name','Rehearsal Partial '||g,'item_type','other','price',5+g) from generate_series(1,5) g) q)))
      into secs4;
    {call("'https://rehearsal.example.com/copy2'", 'reh4', 'secs4')}{after('s4_partial_same_url')}
    -- 5 another URL, 2 food items
    {call("'https://rehearsal.example.com/food'", 'reh5', J5)}{after('s5_small_food_other_url')}
    -- 6 zero items
    {call("'https://rehearsal.example.com/empty'", 'reh6', "'[]'::jsonb")}{after('s6_zero_items')}
    -- 7 missing price overlaps priced item
    a := a || jsonb_build_object('s7_overlap',
       jsonb_build_object('capture_noprice_vs_current_priced', public.phg_menu_keys_overlap(array[public.phg_menu_item_key('Rehearsal Negroni', null)], array[public.phg_menu_item_key('Rehearsal Negroni', 12)]),
                          'reverse', public.phg_menu_keys_overlap(array[public.phg_menu_item_key('Rehearsal Negroni', 12)], array[public.phg_menu_item_key('Rehearsal Negroni', null)]),
                          'different_prices', public.phg_menu_keys_overlap(array['rehearsal negroni|12'], array['rehearsal negroni|13']),
                          'key_noprice', public.phg_menu_item_key('Rehearsal Negroni', null)));
    a := a || jsonb_build_object('final_acct_menus', (select jsonb_agg(jsonb_build_object('id',id,'url',evidence_url,'is_current',is_current,'reason',superseded_reason,'n',cardinality(item_keys)) order by created_at, id) from public.menus where account_id=acct));
    RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'rollback scenarios';
  EXCEPTION
    WHEN sqlstate 'P0099' THEN NULL;
    WHEN others THEN
      GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
      a := a || jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx));
  END;
  r := r || jsonb_build_object('A', a, 'A_ms', round(extract(epoch from clock_timestamp()-t0)*1000),
     'acct_menus_after_A_rollback', (select count(*) from public.menus where account_id=acct));

  -- ================= file 2 =================
  t0 := clock_timestamp();
  BEGIN
    EXECUTE $rehearse_f2${f2}$rehearse_f2$;
  EXCEPTION WHEN others THEN
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT, e_det = PG_EXCEPTION_DETAIL;
    RAISE EXCEPTION 'REHEARSAL %', r || jsonb_build_object('stage','file2','sqlstate',e_state,'error',e_msg,'detail',e_det,'context',e_ctx,'ms',round(extract(epoch from clock_timestamp()-t0)*1000));
  END;
  r := r || jsonb_build_object('file2_ms', round(extract(epoch from clock_timestamp()-t0)*1000));

  -- ================= checks B =================
  t0 := clock_timestamp();
  BEGIN
    b := b || jsonb_build_object(
      'repair_run', (select jsonb_object_agg(step, detail) from public.phg_repair_run_20260927),
      'unique_index_exists', to_regclass('public.menus_one_current_per_account') is not null,
      'multi_current_global', {MULTI},
      'touched_venues', (select count(distinct account_id) from public.phg_repair_plan_menus_20260927),
      'touched_without_current', (select count(*) from (select distinct account_id from public.phg_repair_plan_menus_20260927) t where not exists (select 1 from public.menus m where m.account_id=t.account_id and m.is_current)),
      'touched_current_smaller_than_largest_pre', (select count(*) from (select distinct account_id from public.phg_repair_plan_menus_20260927) t
          join public.menus cm on cm.account_id=t.account_id and cm.is_current
         where cardinality(coalesce(cm.item_keys,'{{}}')) < (select max(cardinality(coalesce(o.item_keys,'{{}}'))) from public.menus o where o.account_id=t.account_id and o.created_at < '2026-09-27 00:00:00+00')),
      'backfill_null_item_keys', (select count(*) from public.menus where item_keys is null),
      'venues_current_changed', (select count(distinct account_id) from public.phg_repair_plan_menus_20260927 where make_current and not was_current),
      'changed_without_prior_current', (select count(distinct ch.account_id) from public.phg_repair_plan_menus_20260927 ch where ch.make_current and not ch.was_current
          and not exists (select 1 from public.phg_repair_plan_menus_20260927 o where o.account_id=ch.account_id and o.was_current)),
      'changed_exact_ties', (select count(distinct ch.account_id) from public.phg_repair_plan_menus_20260927 ch
          join public.phg_repair_plan_menus_20260927 o on o.account_id=ch.account_id and o.was_current and o.id<>ch.id
         where ch.make_current and not ch.was_current and (ch.n,ch.bev,ch.itemish)=(o.n,o.bev,o.itemish)),
      'changed_by_reason', (select jsonb_object_agg(k, cnt) from (select k, count(*) cnt from (
          select distinct on (ch.account_id) ch.account_id,
                 case when o.id is null then 'no_prior_current' when ch.n>o.n then 'more_items' when ch.n=o.n and ch.bev>o.bev then 'same_n_more_bev'
                      when ch.n=o.n and ch.bev=o.bev and ch.itemish<o.itemish then 'same_n_bev_real_page' when (ch.n,ch.bev,ch.itemish)=(o.n,o.bev,o.itemish) then 'exact_tie' else 'other' end k
            from public.phg_repair_plan_menus_20260927 ch
            left join public.phg_repair_plan_menus_20260927 o on o.account_id=ch.account_id and o.was_current and o.id<>ch.id
           where ch.make_current and not ch.was_current order by ch.account_id, o.n desc nulls last) z group by k) y),
      'plan_rows', (select count(*) from public.phg_repair_plan_menus_20260927));
  EXCEPTION WHEN others THEN
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT;
    b := b || jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'context',e_ctx));
  END;
  r := r || jsonb_build_object('B', b, 'B_ms', round(extract(epoch from clock_timestamp()-t0)*1000));

  -- ================= C: rollback rehearsal =================
  t0 := clock_timestamp();
  BEGIN
    c := c || jsonb_build_object('repair_rollback_result', public.phg_repair_20260927_rollback());
    c := c || jsonb_build_object('repair_rollback_ms', round(extract(epoch from clock_timestamp()-t0)*1000),
      'multi_current_global_after_rollback', {MULTI},
      'is_current_mismatch_vs_backup', (select count(*) from public.menus m join public.phg_backup_menus_currency_20260927 bk on bk.id=m.id where m.is_current is distinct from bk.is_current));
    c := c || jsonb_build_object('fn_rollback_returns', public.phg_rollback_function_defs_20260927());
    c := c || jsonb_build_object('submit_menu_10arg_exists_after', to_regprocedure('public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb)') is not null,
      'submit_menu_15arg_exists_after', to_regprocedure('public.submit_menu(text,text,text,text,text,text,text,date,text,jsonb,text,text,text,text,boolean)') is not null);
  EXCEPTION WHEN others THEN
    GET STACKED DIAGNOSTICS e_state = RETURNED_SQLSTATE, e_msg = MESSAGE_TEXT, e_ctx = PG_EXCEPTION_CONTEXT;
    c := c || jsonb_build_object('ERROR', jsonb_build_object('sqlstate',e_state,'error',e_msg,'context',e_ctx));
  END;
  r := r || jsonb_build_object('C', c, 'C_ms', round(extract(epoch from clock_timestamp()-t0)*1000));
  RAISE EXCEPTION 'REHEARSAL %', r;
END
$rehearse_main$;
"""
pathlib.Path('rehearse_all.sql').write_text(sql)
print(len(sql))
