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

  const {data:authorized,error:authErr}=await sb.rpc("phg_menu_authorize",{
    p_menu_project_id:b.menu_project_id||null,
    p_sync_token:b.sync_token||null
  });
  if(authErr)return out({error:authErr.message},500);
  if(!authorized)return out({error:"invalid_menu_token"},403);

  try{
    if(action==="locations"){
      const {data,error}=await sb.rpc("phg_pl_locations",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="budgets"){
      const {data,error}=await sb.rpc("phg_budget_list",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key||null,p_limit:b.limit||100
      });
      if(error)throw error; return out(data);
    }

    if(action==="dashboard"){
      const {data,error}=await sb.rpc("phg_management_dashboard",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_budget_plan_id:b.budget_plan_id||null,
        p_as_of:b.as_of||today(),p_basis:b.basis||"accrual",p_save:!!b.save
      });
      if(error)throw error; return out(data);
    }

    if(action==="settings"){
      const {data,error}=await sb.rpc("phg_management_settings",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key
      });
      if(error)throw error; return out(data);
    }

    if(action==="update_settings"){
      const {data,error}=await sb.rpc("phg_management_update_settings",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,
        p_min_variance_dollars:b.min_variance_dollars??50,
        p_min_variance_pct:b.min_variance_pct??2,
        p_show_acknowledged:!!b.show_acknowledged,
        p_lookback_days:b.lookback_days??30
      });
      if(error)throw error; return out(data);
    }

    if(action==="acknowledge"){
      const {data,error}=await sb.rpc("phg_management_acknowledge_alert",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_fingerprint:b.fingerprint,
        p_alert_key:b.alert_key,p_note:b.note||null
      });
      if(error)throw error; return out(data);
    }

    if(action==="unacknowledge"){
      const {data,error}=await sb.rpc("phg_management_unacknowledge_alert",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,p_fingerprint:b.fingerprint
      });
      if(error)throw error; return out(data);
    }

    if(action==="history"){
      const {data,error}=await sb.rpc("phg_management_dashboard_history",{
        p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null,
        p_location_key:b.location_key||null,p_limit:b.limit||50
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