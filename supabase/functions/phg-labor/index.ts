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
  if(req.method==="OPTIONS") return new Response("ok",{headers:cors});
  if(req.method!=="POST") return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!url||!key)return out({error:"runtime configuration missing"},500);
  const sb=createClient(url,key,{auth:{persistSession:false}});
  const b=await req.json().catch(()=>({}));
  const action=String(b.action||"");

  try{
    if(action==="locations"){
      const {data,error}=await sb.rpc("phg_labor_locations",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="people"){
      const {data,error}=await sb.rpc("phg_labor_people_overview",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,
        p_on:b.on_date||today()
      });
      if(error)throw error; return out(data);
    }

    if(action==="upsert_employee"){
      const {data,error}=await sb.rpc("phg_labor_upsert_employee",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_employee_key:b.employee_key,p_display_name:b.display_name,
        p_employment_type:b.employment_type||"hourly",p_status:b.status||"active",
        p_hire_date:b.hire_date||null,p_termination_date:b.termination_date||null,
        p_metadata:b.metadata||{}
      });
      if(error)throw error; return out(data);
    }

    if(action==="upsert_role"){
      const {data,error}=await sb.rpc("phg_labor_upsert_role",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_role_key:b.role_key,p_name:b.name,p_role_group:b.role_group||null,p_metadata:b.metadata||{}
      });
      if(error)throw error; return out(data);
    }

    if(action==="assign_role"){
      const {data,error}=await sb.rpc("phg_labor_assign_role",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_employee_id:b.employee_id,p_role_id:b.role_id,p_location_key:b.location_key,
        p_effective_from:b.effective_from||today(),p_effective_to:b.effective_to||null,
        p_is_primary:!!b.is_primary
      });
      if(error)throw error; return out(data);
    }

    if(action==="set_pay_rate"){
      const {data,error}=await sb.rpc("phg_labor_set_pay_rate",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_employee_id:b.employee_id,p_role_id:b.role_id||null,p_location_key:b.location_key,
        p_pay_type:b.pay_type,p_hourly_rate:b.hourly_rate??null,p_annual_salary:b.annual_salary??null,
        p_overtime_multiplier:b.overtime_multiplier??1.5,p_doubletime_multiplier:b.doubletime_multiplier??2,
        p_employer_burden_pct:b.employer_burden_pct??0,p_effective_from:b.effective_from||today(),
        p_source_ref:b.source_ref||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="set_salary_allocations"){
      const {data,error}=await sb.rpc("phg_labor_set_salary_allocations",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_employee_id:b.employee_id,p_location_key:b.location_key,
        p_effective_from:b.effective_from||today(),
        p_allocations:Array.isArray(b.allocations)?b.allocations:[],
        p_source_ref:b.source_ref||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="save_shift"){
      const {data,error}=await sb.rpc("phg_labor_save_shift",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_employee_id:b.employee_id,p_role_id:b.role_id||null,p_location_key:b.location_key,
        p_revenue_center:b.revenue_center||null,p_business_date:b.business_date||today(),
        p_scheduled_start:b.scheduled_start||null,p_scheduled_end:b.scheduled_end||null,
        p_actual_start:b.actual_start||null,p_actual_end:b.actual_end||null,
        p_scheduled_break_minutes:b.scheduled_break_minutes??0,p_actual_break_minutes:b.actual_break_minutes??0,
        p_scheduled_regular_hours:b.scheduled_regular_hours??null,
        p_scheduled_overtime_hours:b.scheduled_overtime_hours??null,
        p_scheduled_doubletime_hours:b.scheduled_doubletime_hours??null,
        p_regular_hours:b.regular_hours??null,p_overtime_hours:b.overtime_hours??null,
        p_doubletime_hours:b.doubletime_hours??null,
        p_assume_actual_all_regular:!!b.assume_actual_all_regular,
        p_assume_scheduled_all_regular:!!b.assume_scheduled_all_regular,
        p_shift_status:b.shift_status||"completed",p_source_system:b.source_system||null,
        p_source_ref:b.source_ref||null,p_metadata:b.metadata||{}
      });
      if(error)throw error; return out(data);
    }

    if(action==="add_supplemental"){
      const {data,error}=await sb.rpc("phg_labor_add_supplemental",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_employee_id:b.employee_id||null,p_location_key:b.location_key,
        p_revenue_center:b.revenue_center||null,p_business_date:b.business_date||today(),
        p_entry_type:b.entry_type,p_amount:b.amount,
        p_included_in_labor_cost:b.included_in_labor_cost!==false,
        p_source_ref:b.source_ref||null,p_metadata:b.metadata||{}
      });
      if(error)throw error; return out(data);
    }

    if(action==="report"){
      const {data,error}=await sb.rpc("phg_labor_report_safe",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_start:b.start_date,p_end:b.end_date,
        p_revenue_center:b.revenue_center||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="import_canonical"){
      const {data,error}=await sb.rpc("phg_labor_import_canonical",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_source_system:b.source_system||"canonical_csv",
        p_source_file_name:b.source_file_name||null,p_content_hash:b.content_hash||null,
        p_rows:Array.isArray(b.rows)?b.rows:[]
      });
      if(error)throw error; return out(data);
    }

    if(action==="budget_set_target"){
      const {data,error}=await sb.rpc("phg_budget_set_labor_target",{
        p_budget_plan_id:b.budget_plan_id,p_sync_token:b.sync_token||null,
        p_labor_budget:b.labor_budget
      });
      if(error)throw error; return out(data);
    }

    if(action==="budget_seed_history"){
      const {data,error}=await sb.rpc("phg_budget_seed_labor_from_history",{
        p_budget_plan_id:b.budget_plan_id,p_sync_token:b.sync_token||null,
        p_labor_change_pct:b.labor_change_pct??0
      });
      if(error)throw error; return out(data);
    }

    if(action==="budget_status"){
      const {data,error}=await sb.rpc("phg_budget_labor_status",{
        p_budget_plan_id:b.budget_plan_id,p_sync_token:b.sync_token||null,
        p_as_of:b.as_of||today()
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