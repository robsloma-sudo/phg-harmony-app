import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
const cors={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type"};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});
Deno.serve(async(req)=>{
 if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
 if(req.method!=="POST")return out({error:"POST required"},405);
 const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
 if(!url||!key)return out({error:"runtime config missing"},500);
 const b=await req.json().catch(()=>({})); const msg=String(b.message||"").trim(); if(!msg)return out({error:"message required"},400);
 const sb=createClient(url,key,{auth:{persistSession:false}});
 let conversationId=b.conversation_id||null;
 let state:any=null;
 if(conversationId){const s=await sb.rpc("phg_conversation_state",{p_conversation_id:conversationId});state=s.data;}
 const lower=msg.toLowerCase();
 const active=(state?.goals||[]).filter((g:any)=>g.status==="active"||g.status==="suspended");
 const named=(needle:string)=>active.find((g:any)=>String(g.title).toLowerCase().includes(needle));
 if(conversationId && /pause.*demographic/.test(lower)){const g=named("demograph");if(g){await sb.rpc("phg_update_goal_state",{p_goal_id:g.id,p_status:"suspended",p_constraints:null});await sb.rpc("phg_record_message",{p_conversation_id:conversationId,p_role:"user",p_content:msg,p_metadata:{action:"pause_goal",goal_id:g.id}});return out({conversation_id:conversationId,status:"goal_suspended",goal_id:g.id,message:`Paused ${g.title}.`});}}
 if(conversationId && /resume.*demographic/.test(lower)){const g=named("demograph");if(g){await sb.rpc("phg_update_goal_state",{p_goal_id:g.id,p_status:"active",p_constraints:null});await sb.rpc("phg_record_message",{p_conversation_id:conversationId,p_role:"user",p_content:msg,p_metadata:{action:"resume_goal",goal_id:g.id}});return out({conversation_id:conversationId,status:"goal_resumed",goal_id:g.id,message:`Resumed ${g.title}.`});}}
 if(conversationId && /(go back|back to).*(winter|menu)/.test(lower)){const g=active.find((x:any)=>/winter|menu/i.test(x.title));if(g){await sb.rpc("phg_update_goal_state",{p_goal_id:g.id,p_status:"active",p_constraints:null});await sb.rpc("phg_record_message",{p_conversation_id:conversationId,p_role:"user",p_content:msg,p_metadata:{action:"resume_goal",goal_id:g.id}});return out({conversation_id:conversationId,status:"goal_resumed",goal_id:g.id,message:`Back to ${g.title}.`});}}
 const r=await fetch(`${url}/functions/v1/phg-execute-readonly`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({message:msg,conversation_id:conversationId,external_key:b.external_key||null,conversation_context:state})});
 const data=await r.json(); return out(data,r.status);
});