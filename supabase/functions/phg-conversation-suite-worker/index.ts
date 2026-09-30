import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{"Content-Type":"application/json"}});
Deno.serve(async(req)=>{if(req.method!=="POST")return out({error:"POST required"},405);
const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");if(!url||!key)return out({error:"config"},500);
const sb=createClient(url,key,{auth:{persistSession:false}}),b=await req.json().catch(()=>({})),id=b.run_id;
const {data:run}=await sb.rpc("phg_get_conversation_suite_run",{p_run_id:id});if(!run)return out({error:"not found"},404);
const {data:tests}=await sb.rpc("phg_conversation_tests");const test=(tests||[])[run.next_offset];if(!test){await sb.rpc("phg_update_conversation_suite_run",{p_run_id:id,p_status:"completed",p_processed:run.processed,p_passed:run.passed,p_failed:run.failed,p_errors:run.errors,p_next_offset:run.next_offset,p_last_error:null});return out({status:"completed"});}
const r=await fetch(`${url}/functions/v1/phg-conversation-tests`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({test_key:test.test_key})});const d=await r.json().catch(()=>({}));
const ok=r.ok&&d.errors===0, pass=ok&&d.passed===1;const processed=run.processed+1,passed=run.passed+(pass?1:0),failed=run.failed+(ok&&!pass?1:0),errors=run.errors+(ok?0:1),next=run.next_offset+1,done=next>=(tests||[]).length;
await sb.rpc("phg_update_conversation_suite_run",{p_run_id:id,p_status:done?"completed":"running",p_processed:processed,p_passed:passed,p_failed:failed,p_errors:errors,p_next_offset:next,p_last_error:ok?null:JSON.stringify(d)});
if(!done)EdgeRuntime.waitUntil(fetch(`${url}/functions/v1/phg-conversation-suite-worker`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({run_id:id})}).catch(()=>{}));
return out({run_id:id,status:done?"completed":"running",processed,total:run.total,passed,failed,errors});});