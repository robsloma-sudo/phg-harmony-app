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
      const {data,error}=await sb.rpc("phg_menu_engineering_locations",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="list"){
      const {data,error}=await sb.rpc("phg_budget_list",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:b.location_key||null,
        p_limit:b.limit||100
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="create_from_history"){
      const {data,error}=await sb.rpc("phg_budget_create_from_history",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,
        p_name:b.name||null,
        p_period_start:b.period_start,
        p_period_end:b.period_end,
        p_baseline_start:b.baseline_start,
        p_baseline_end:b.baseline_end,
        p_revenue_center:b.revenue_center||null,
        p_volume_change_pct:b.volume_change_pct??0,
        p_price_change_pct:b.price_change_pct??0,
        p_recipe_cost_change_pct:b.recipe_cost_change_pct??0,
        p_purchase_budget:b.purchase_budget??null
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="detail"){
      const {data,error}=await sb.rpc("phg_budget_plan_detail",{
        p_budget_plan_id:b.budget_plan_id,
        p_sync_token:b.sync_token||null
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="update_targets"){
      const {data,error}=await sb.rpc("phg_budget_update_targets",{
        p_budget_plan_id:b.budget_plan_id,
        p_sync_token:b.sync_token||null,
        p_sales_budget:b.sales_budget??null,
        p_units_budget:b.units_budget??null,
        p_cogs_budget:b.cogs_budget??null,
        p_purchase_budget:b.purchase_budget??null,
        p_status:b.status||null,
        p_notes:b.notes||null
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="status"){
      const {data,error}=await sb.rpc("phg_budget_status",{
        p_budget_plan_id:b.budget_plan_id,
        p_sync_token:b.sync_token||null,
        p_as_of:b.as_of||today(),
        p_save:!!b.save
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="scenario"){
      const {data,error}=await sb.rpc("phg_budget_run_scenario",{
        p_budget_plan_id:b.budget_plan_id,
        p_sync_token:b.sync_token||null,
        p_name:b.name||"Scenario",
        p_assumptions:b.assumptions||{},
        p_save:!!b.save
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="history"){
      const {data,error}=await sb.rpc("phg_budget_history",{
        p_budget_plan_id:b.budget_plan_id,
        p_sync_token:b.sync_token||null,
        p_limit:b.limit||50
      });
      if(error)throw error;
      return out(data);
    }

    return out({error:"unknown action"},400);
  }catch(e:any){
    const msg=String(e?.message||e||"error");
    if(msg.includes("invalid_menu_token"))return out({error:"invalid_menu_token"},403);
    if(msg.includes("not found"))return out({error:msg},404);
    return out({error:msg},500);
  }
});