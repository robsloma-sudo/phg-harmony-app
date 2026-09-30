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
    if(action==="bind_location"){
      const {data,error}=await sb.rpc("phg_inventory_bind_location",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:String(b.location_key||"").trim()
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="locations"){
      const {data,error}=await sb.rpc("phg_inventory_locations",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="ingredients"){
      const {data,error}=await sb.rpc("phg_inventory_menu_ingredients",{
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

    if(action==="create_session"){
      const businessDate=b.business_date||today();
      let countedAt=b.counted_at||null;
      if(!countedAt){
        countedAt=businessDate+(b.position==="opening"?"T00:00:00":"T23:59:59");
      }
      const {data,error}=await sb.rpc("phg_inventory_create_session",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,
        p_business_date:businessDate,
        p_position:b.position||"closing",
        p_counted_at:countedAt,
        p_label:b.label||null,
        p_source_ref:b.source_ref||null,
        p_counts:Array.isArray(b.counts)?b.counts:[]
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="add_movements"){
      const {data,error}=await sb.rpc("phg_inventory_add_movements",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,
        p_movements:Array.isArray(b.movements)?b.movements:[]
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="reconcile"){
      const {data,error}=await sb.rpc("phg_inventory_reconcile",{
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

    if(action==="recipe_theoretical"){
      const {data,error}=await sb.rpc("phg_recipe_theoretical_usage",{
        p_recipe_version_id:b.recipe_version_id,
        p_servings:b.servings??1,
        p_on:b.on_date||today()
      });
      if(error)throw error;
      return out(data);
    }

    if(action==="sales_theoretical"){
      const {data,error}=await sb.rpc("phg_sales_theoretical_usage",{
        p_location_key:b.location_key,
        p_start:b.start_date,
        p_end:b.end_date,
        p_revenue_center:b.revenue_center||null
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