import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});

Deno.serve(async req=>{
  if(req.method==="OPTIONS") return new Response("ok",{headers:cors});
  if(req.method!=="POST") return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!url||!key)return out({error:"runtime configuration missing"},500);
  const sb=createClient(url,key,{auth:{persistSession:false}});
  const b=await req.json().catch(()=>({}));

  const {data:authorized,error:authErr}=await sb.rpc("phg_menu_authorize",{
    p_menu_project_id:b.menu_project_id||null,
    p_sync_token:b.sync_token||null
  });
  if(authErr)return out({error:authErr.message},500);
  if(!authorized)return out({error:"invalid_menu_token"},403);

  try{
    const action=String(b.action||"");

    if(action==="locations"){
      const {data,error}=await sb.rpc("phg_inventory_locations",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="sessions"){
      const {data,error}=await sb.rpc("phg_inventory_sessions",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:b.location_key||null
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="reconcile"){
      const {data,error}=await sb.rpc("phg_cogs_reconcile",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,
        p_beginning_session_id:b.beginning_session_id,
        p_ending_session_id:b.ending_session_id,
        p_revenue_center:b.revenue_center||null,
        p_save:!!b.save
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="history"){
      const {data,error}=await sb.rpc("phg_cogs_reconciliation_history",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:b.location_key||null,
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