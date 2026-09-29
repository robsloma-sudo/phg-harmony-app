import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});

Deno.serve(async(req)=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL");
  const anon=Deno.env.get("SUPABASE_ANON_KEY");
  const service=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!url||!anon||!service)return out({error:"runtime configuration missing"},500);

  const auth=req.headers.get("Authorization")||"";
  if(!auth.toLowerCase().startsWith("bearer "))return out({error:"login required"},401);

  const userClient=createClient(url,anon,{auth:{persistSession:false},global:{headers:{Authorization:auth}}});
  const {data:userData,error:userErr}=await userClient.auth.getUser(auth.slice(7).trim());
  const user=userData?.user;
  if(userErr||!user)return out({error:"invalid or expired login"},401);

  const body=await req.json().catch(()=>({}));
  const sb=createClient(url,service,{auth:{persistSession:false}});

  const accountId=body.account_id||null;
  const {data:membership,error:memErr}=await sb.schema("phg").from("account_memberships")
    .select("account_id,role,status").eq("user_id",user.id).eq("status","active");
  if(memErr)return out({error:memErr.message},500);
  if(accountId && !(membership||[]).some((m:any)=>m.account_id===accountId))return out({error:"account access denied"},403);
  if(!(membership||[]).length)return out({error:"active PHG account membership required"},403);

  const action=String(body.action||"coverage");
  const filters=body.filters&&typeof body.filters==="object"?body.filters:{};
  const limit=Math.max(1,Math.min(200,Number(body.limit||50)));

  const {data,error}=await sb.rpc("phg_retail_explorer",{
    p_action:action,
    p_filters:filters,
    p_limit:limit
  });
  if(error)return out({error:error.message},500);
  return out(data||{status:"ok"});
});