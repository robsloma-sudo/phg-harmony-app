import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
const cors={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type"};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});
Deno.serve(async(req)=>{
 if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
 if(req.method!=="POST")return out({error:"POST required"},405);
 const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
 if(!url||!key)return out({error:"runtime config missing"},500);
 const sb=createClient(url,key,{auth:{persistSession:false}});
 const {data,error}=await sb.rpc("phg_create_composition_suite_run");
 if(error)return out({error:error.message},500);
 EdgeRuntime.waitUntil(fetch(`${url}/functions/v1/phg-composition-suite-worker`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({run_id:data.run_id})}).catch(()=>{}));
 return out({ok:true,run_id:data.run_id,total:data.total,message:`PHG composition suite started: ${data.total} tests. You can use your phone normally.`});
});