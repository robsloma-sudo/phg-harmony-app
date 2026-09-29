import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});

function hex(bytes:Uint8Array){return Array.from(bytes).map(b=>b.toString(16).padStart(2,"0")).join("");}
async function sha256(s:string){
  const b=new TextEncoder().encode(s);
  return hex(new Uint8Array(await crypto.subtle.digest("SHA-256",b)));
}
function randomToken(){
  const b=new Uint8Array(32);crypto.getRandomValues(b);return hex(b);
}

Deno.serve(async(req)=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL");
  const anon=Deno.env.get("SUPABASE_ANON_KEY");
  const service=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!url||!anon||!service)return out({error:"runtime configuration missing"},500);

  const auth=req.headers.get("Authorization")||"";
  if(!auth.toLowerCase().startsWith("bearer "))return out({error:"login required"},401);
  const jwt=auth.slice(7).trim();
  if(!jwt)return out({error:"login required"},401);

  const userClient=createClient(url,anon,{auth:{persistSession:false},global:{headers:{Authorization:auth}}});
  const {data:userData,error:userErr}=await userClient.auth.getUser(jwt);
  const user=userData?.user;
  if(userErr||!user)return out({error:"invalid or expired login"},401);

  const sb=createClient(url,service,{auth:{persistSession:false}});
  const body=await req.json().catch(()=>({}));
  const action=String(body.action||"bootstrap");

  try{
    if(action==="bootstrap"||action==="switch_account"){
      const token=randomToken();
      const tokenHash=await sha256(token);
      const expiresAt=new Date(Date.now()+7*24*60*60*1000).toISOString();
      const {data,error}=await sb.rpc("phg_auth_bootstrap",{
        p_user_id:user.id,
        p_account_id:body.account_id||null,
        p_device_key:body.device_key||null,
        p_token_hash:tokenHash,
        p_expires_at:expiresAt
      });
      if(error)throw error;
      if(!data||data.status!=="ok")return out(data||{status:"no_account"},200);
      return out({...data,phg_session_token:token,phg_session_expires_at:expiresAt,user:{id:user.id,email:user.email||null}});
    }
    if(action==="logout"){
      const phgToken=String(body.phg_session_token||"");
      if(phgToken){
        const tokenHash=await sha256(phgToken);
        const {error}=await sb.rpc("phg_auth_logout",{p_user_id:user.id,p_token_hash:tokenHash});
        if(error)throw error;
      }
      return out({status:"ok"});
    }
    return out({error:"unknown action"},400);
  }catch(e:any){
    return out({error:String(e?.message||e||"error")},500);
  }
});