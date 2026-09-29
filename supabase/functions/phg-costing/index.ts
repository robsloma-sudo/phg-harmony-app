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
  const action=String(b.action||"");
  const today=new Date().toISOString().slice(0,10);
  try{
    if(action==="overview"){
      const {data,error}=await sb.rpc("phg_menu_cost_overview",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_on:b.on_date||today
      });
      if(error) throw error;
      return out(data);
    }

    if(action==="set_cost"){
      const {data,error}=await sb.rpc("phg_set_menu_ingredient_cost",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_ingredient_id:b.ingredient_id,
        p_cost:b.cost,
        p_package_quantity:b.package_quantity??1,
        p_package_size:b.package_size,
        p_package_size_unit:b.package_size_unit,
        p_vendor_key:b.vendor_key||null,
        p_effective_from:b.effective_from||today,
        p_source_ref:b.source_ref||null
      });
      if(error) throw error;
      return out({status:"cost_saved",cost:data});
    }

    if(action==="set_target"){
      const {data,error}=await sb.rpc("phg_set_menu_target_cogs",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_target_cogs_pct:b.target_cogs_pct??null
      });
      if(error) throw error;
      return out(data);
    }

    if(action==="snapshot"){
      const {data,error}=await sb.rpc("phg_snapshot_menu_item_cost",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_menu_item_id:b.menu_item_id,
        p_on:b.on_date||null
      });
      if(error) throw error;
      return out(data);
    }

    if(action==="map_sales_item"){
      const {data,error}=await sb.rpc("phg_map_sales_item_to_menu",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_location_key:b.location_key,
        p_menu_item_id:b.menu_item_id,
        p_sales_item_key:b.sales_item_key||null,
        p_sales_item_name:b.sales_item_name||null,
        p_effective_from:b.effective_from||null
      });
      if(error) throw error;
      return out(data);
    }

    if(action==="sales_theoretical_cogs"){
      const {data,error}=await sb.rpc("phg_sales_theoretical_cogs",{
        p_location_key:b.location_key,
        p_start:b.start_date,
        p_end:b.end_date,
        p_revenue_center:b.revenue_center||null
      });
      if(error) throw error;
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