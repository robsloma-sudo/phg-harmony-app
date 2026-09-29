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

  const {data:authorized,error:authErr}=await sb.rpc("phg_menu_authorize",{
    p_menu_project_id:b.menu_project_id||null,
    p_sync_token:b.sync_token||null
  });
  if(authErr)return out({error:authErr.message},500);
  if(!authorized)return out({error:"invalid_menu_token"},403);

  try{
    if(action==="list_vendors"){
      const {data,error}=await sb.rpc("phg_vendors_list",{p_query:b.query||null});
      if(error)throw error; return out({vendors:data||[]});
    }

    if(action==="upsert_vendor"){
      const {data,error}=await sb.rpc("phg_upsert_vendor",{
        p_vendor_key:b.vendor_key,
        p_name:b.name,
        p_account_ref:b.account_ref||null,
        p_metadata:b.metadata||{}
      });
      if(error)throw error; return out({vendor:data});
    }

    if(action==="ingredients_search"){
      const {data,error}=await sb.rpc("phg_ingredients_search",{
        p_query:b.query||null,
        p_limit:b.limit||50
      });
      if(error)throw error; return out({ingredients:data||[]});
    }

    if(action==="resolve_line_existing"){
      const {data,error}=await sb.rpc("phg_resolve_invoice_line_to_ingredient",{
        p_line_id:b.line_id,
        p_ingredient_id:b.ingredient_id
      });
      if(error)throw error; return out(data);
    }

    if(action==="resolve_line_new"){
      const {data,error}=await sb.rpc("phg_resolve_invoice_line_new_ingredient",{
        p_line_id:b.line_id,
        p_name:b.name,
        p_ingredient_type:b.ingredient_type||"ingredient",
        p_category:b.category||null,
        p_default_unit:b.default_unit||"oz"
      });
      if(error)throw error; return out(data);
    }

    if(action==="resolve_deposit_line"){
      const {data,error}=await sb.rpc("phg_resolve_invoice_deposit_line",{
        p_line_id:b.line_id,
        p_returnable_container_type_id:b.returnable_container_type_id
      });
      if(error)throw error; return out(data);
    }

    if(action==="catalog"){
      const {data,error}=await sb.rpc("phg_procurement_catalog",{
        p_vendor_id:b.vendor_id||null,
        p_query:b.query||null,
        p_limit:b.limit||100
      });
      if(error)throw error; return out({items:data||[]});
    }

    if(action==="upsert_catalog_item"){
      const {data,error}=await sb.rpc("phg_upsert_procurement_item",{
        p_vendor_id:b.vendor_id,
        p_vendor_sku:b.vendor_sku,
        p_display_name:b.display_name,
        p_product_family_key:b.product_family_key||null,
        p_flavor_variant:b.flavor_variant||null,
        p_product_id:b.product_id||null,
        p_brand_product_id:b.brand_product_id||null,
        p_ingredient_id:b.ingredient_id||null,
        p_purchase_unit:b.purchase_unit||"case",
        p_containers_per_purchase_unit:b.containers_per_purchase_unit??1,
        p_container_size:b.container_size??null,
        p_container_size_unit:b.container_size_unit||null,
        p_container_type:b.container_type||null,
        p_costing_priority:b.costing_priority??100,
        p_metadata:b.metadata||{}
      });
      if(error)throw error; return out({item:data});
    }

    if(action==="returnable_catalog"){
      const {data,error}=await sb.rpc("phg_returnable_container_catalog",{
        p_vendor_id:b.vendor_id||null
      });
      if(error)throw error; return out({containers:data||[]});
    }

    if(action==="upsert_returnable_container"){
      const {data,error}=await sb.rpc("phg_upsert_returnable_container_type",{
        p_vendor_id:b.vendor_id,
        p_container_key:b.container_key,
        p_name:b.name,
        p_container_type:b.container_type,
        p_nominal_size:b.nominal_size??null,
        p_nominal_size_unit:b.nominal_size_unit||null,
        p_product_family_key:b.product_family_key||null,
        p_refundable:b.refundable??true,
        p_metadata:b.metadata||{}
      });
      if(error)throw error; return out({container:data});
    }

    if(action==="create_invoice"){
      const {data,error}=await sb.rpc("phg_create_purchase_invoice",{
        p_vendor_id:b.vendor_id,
        p_location_key:b.location_key,
        p_invoice_number:b.invoice_number||null,
        p_invoice_date:b.invoice_date,
        p_due_date:b.due_date||null,
        p_currency:b.currency||"USD",
        p_subtotal:b.subtotal??null,
        p_discounts:b.discounts??0,
        p_tax:b.tax??0,
        p_fees:b.fees??0,
        p_freight:b.freight??0,
        p_deposit_charges:b.deposit_charges??0,
        p_deposit_credits:b.deposit_credits??0,
        p_total:b.total??null,
        p_content_hash:b.content_hash||null,
        p_source_ref:b.source_ref||null,
        p_raw_payload:b.raw_payload||{}
      });
      if(error)throw error; return out(data);
    }

    if(action==="add_lines"){
      const {data,error}=await sb.rpc("phg_add_purchase_invoice_lines",{
        p_invoice_id:b.invoice_id,
        p_lines:Array.isArray(b.lines)?b.lines:[],
        p_replace:!!b.replace
      });
      if(error)throw error; return out(data);
    }

    if(action==="validate_invoice"){
      const {data,error}=await sb.rpc("phg_validate_purchase_invoice",{p_invoice_id:b.invoice_id});
      if(error)throw error; return out(data);
    }

    if(action==="approve_invoice"){
      const {data,error}=await sb.rpc("phg_approve_purchase_invoice",{p_invoice_id:b.invoice_id});
      if(error)throw error; return out(data);
    }

    if(action==="invoice_detail"){
      const {data,error}=await sb.rpc("phg_purchase_invoice_detail",{p_invoice_id:b.invoice_id});
      if(error)throw error; return out(data);
    }

    if(action==="invoices"){
      const {data,error}=await sb.rpc("phg_purchase_invoices_list",{
        p_location_key:b.location_key||null,
        p_vendor_id:b.vendor_id||null,
        p_limit:b.limit||100
      });
      if(error)throw error; return out({invoices:data||[]});
    }

    if(action==="deposit_status"){
      const {data,error}=await sb.rpc("phg_returnable_deposit_status",{
        p_location_key:b.location_key||null,
        p_vendor_id:b.vendor_id||null
      });
      if(error)throw error; return out(data);
    }

    return out({error:"unknown action"},400);
  }catch(e:any){
    const msg=String(e?.message||e||"error");
    if(msg.includes("not found"))return out({error:msg},404);
    if(msg.includes("validation failed"))return out({error:msg},409);
    return out({error:msg},500);
  }
});