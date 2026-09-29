import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});
const today=()=>new Date().toISOString().slice(0,10);

Deno.serve(async req=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!url||!key)return out({error:"runtime configuration missing"},500);
  const sb=createClient(url,key,{auth:{persistSession:false}});
  const b=await req.json().catch(()=>({}));
  const action=String(b.action||"");

  try{
    if(action==="locations"){
      const {data,error}=await sb.rpc("phg_expense_locations",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="catalog"){
      const {data,error}=await sb.rpc("phg_expense_catalog",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="upsert_category"){
      const {data,error}=await sb.rpc("phg_expense_upsert_category",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_category_key:b.category_key,p_name:b.name,p_category_group:b.category_group,
        p_behavior:b.behavior||"variable",p_financial_treatment:b.financial_treatment||"operating_expense",
        p_description:b.description||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="save_expense"){
      const {data,error}=await sb.rpc("phg_expense_save",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_expense_date:b.expense_date||today(),
        p_category_id:b.category_id,p_description:b.description,p_signed_amount:b.signed_amount,
        p_entry_type:b.entry_type||"expense",p_vendor_id:b.vendor_id||null,
        p_revenue_center:b.revenue_center||null,p_service_period_start:b.service_period_start||null,
        p_service_period_end:b.service_period_end||null,p_recurring_rule_id:b.recurring_rule_id||null,
        p_recurring_occurrence_date:b.recurring_occurrence_date||null,
        p_source_system:b.source_system||null,p_source_ref:b.source_ref||null,
        p_allocations:Array.isArray(b.allocations)?b.allocations:[],p_metadata:b.metadata||{}
      });
      if(error)throw error; return out(data);
    }

    if(action==="save_recurring"){
      const {data,error}=await sb.rpc("phg_recurring_expense_save",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_rule_id:b.rule_id||null,p_location_key:b.location_key,p_category_id:b.category_id,
        p_name:b.name,p_signed_amount:b.signed_amount,p_cadence:b.cadence,
        p_interval_count:b.interval_count||1,p_anchor_date:b.anchor_date||today(),
        p_end_date:b.end_date||null,p_vendor_id:b.vendor_id||null,
        p_revenue_center:b.revenue_center||null,p_active:b.active!==false,
        p_source_ref:b.source_ref||null,p_allocations:Array.isArray(b.allocations)?b.allocations:[],
        p_metadata:b.metadata||{}
      });
      if(error)throw error; return out(data);
    }

    if(action==="mark_period"){
      const {data,error}=await sb.rpc("phg_expense_mark_period",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_period_start:b.start_date,p_period_end:b.end_date,
        p_revenue_center:b.revenue_center||null,p_status:b.status||"open",
        p_note:b.note||null,p_source_ref:b.source_ref||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="report"){
      const {data,error}=await sb.rpc("phg_expense_report",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_start:b.start_date,p_end:b.end_date,
        p_revenue_center:b.revenue_center||null,p_basis:b.basis||"accrual"
      });
      if(error)throw error; return out(data);
    }

    if(action==="list"){
      const {data,error}=await sb.rpc("phg_expense_list",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_start:b.start_date,p_end:b.end_date,
        p_limit:b.limit||250
      });
      if(error)throw error; return out(data);
    }

    if(action==="recurring_list"){
      const {data,error}=await sb.rpc("phg_recurring_expense_list",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key
      });
      if(error)throw error; return out(data);
    }

    if(action==="import_canonical"){
      const {data,error}=await sb.rpc("phg_expense_import_canonical",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_source_system:b.source_system||"canonical_csv",
        p_source_file_name:b.source_file_name||null,p_content_hash:b.content_hash||null,
        p_rows:Array.isArray(b.rows)?b.rows:[]
      });
      if(error)throw error; return out(data);
    }

    if(action==="budget_set_target"){
      const {data,error}=await sb.rpc("phg_budget_set_expense_target",{
        p_budget_plan_id:b.budget_plan_id,p_sync_token:b.sync_token||null,
        p_operating_expense_budget:b.operating_expense_budget
      });
      if(error)throw error; return out(data);
    }

    if(action==="budget_seed_history"){
      const {data,error}=await sb.rpc("phg_budget_seed_expense_from_history",{
        p_budget_plan_id:b.budget_plan_id,p_sync_token:b.sync_token||null,
        p_expense_change_pct:b.expense_change_pct??0,p_basis:b.basis||"accrual"
      });
      if(error)throw error; return out(data);
    }

    if(action==="budget_status"){
      const {data,error}=await sb.rpc("phg_budget_expense_status",{
        p_budget_plan_id:b.budget_plan_id,p_sync_token:b.sync_token||null,
        p_as_of:b.as_of||today(),p_basis:b.basis||"accrual"
      });
      if(error)throw error; return out(data);
    }

    return out({error:"unknown action"},400);
  }catch(e:any){
    const msg=String(e?.message||e||"error");
    if(msg.includes("invalid_menu_token"))return out({error:"invalid_menu_token"},403);
    if(msg.includes("not found"))return out({error:msg},404);
    return out({error:msg},500);
  }
});