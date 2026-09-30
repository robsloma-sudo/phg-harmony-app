import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"content-type, apikey, authorization, x-client-info",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json","Cache-Control":"no-store"}});

Deno.serve(async(req)=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return out({error:"POST required"},405);
  const url=Deno.env.get("SUPABASE_URL");
  const service=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!url||!service)return out({error:"runtime configuration missing"},500);
  const sb=createClient(url,service,{auth:{persistSession:false}});
  const b=await req.json().catch(()=>({}));
  const action=String(b.action||"catalog");

  if(action==="catalog"){
    const {data,error}=await sb.schema("phg").from("public_menu_experiences")
      .select("account_key,account_name,menu_key,menu_name,status,preview_badge,theme,metadata,updated_at")
      .eq("published",true).neq("status","archived")
      .order("account_name",{ascending:true}).order("menu_name",{ascending:true});
    if(error)return out({error:error.message},500);
    const rows=(data||[]).map((x:any)=>({
      account_key:x.account_key,
      account_name:x.account_name,
      menu_key:x.menu_key,
      menu_name:x.menu_name,
      status:x.status,
      preview_badge:x.preview_badge||null,
      theme:x.theme||{},
      beta:x.status==="beta",
      updated_at:x.updated_at
    }));
    return out({status:"ok",items:rows});
  }

  if(action==="menu"){
    const accountKey=String(b.account_key||"").trim();
    const menuKey=String(b.menu_key||"").trim();
    if(!accountKey||!menuKey)return out({error:"account_key and menu_key required"},400);
    const {data,error}=await sb.schema("phg").from("public_menu_experiences")
      .select("account_key,account_name,menu_key,menu_name,status,preview_badge,theme,published_tree,metadata,updated_at")
      .eq("published",true).eq("account_key",accountKey).eq("menu_key",menuKey).neq("status","archived")
      .maybeSingle();
    if(error)return out({error:error.message},500);
    if(!data)return out({error:"menu not found"},404);
    return out({
      status:"ok",
      account:{key:data.account_key,name:data.account_name},
      menu:{key:data.menu_key,name:data.menu_name,status:data.status,preview_badge:data.preview_badge||null,updated_at:data.updated_at},
      theme:data.theme||{},
      tree:data.published_tree||{},
      metadata:{
        consumer_mode:data.metadata?.consumer_mode||"interactive_nodes",
        content_basis:data.metadata?.content_basis||null,
        publication_version:data.metadata?.publication_version||null,
        source_revision:data.metadata?.source_revision||null,
        item_count:data.metadata?.item_count||null,
        targets:data.metadata?.targets||{},
        sample_content_only:!!data.metadata?.sample_content_only,
        test_state:data.metadata?.test_state||null
      }
    });
  }

  return out({error:"unknown action"},400);
});