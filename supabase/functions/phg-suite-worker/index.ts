import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{"Content-Type":"application/json"}});
Deno.serve(async(req)=>{
 if(req.method!=="POST")return out({error:"POST required"},405);
 const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
 if(!url||!key)return out({error:"runtime config missing"},500);
 const sb=createClient(url,key,{auth:{persistSession:false}}); const b=await req.json().catch(()=>({})); const runId=b.run_id;
 if(!runId)return out({error:"run_id required"},400);
 const {data:run,error}=await sb.rpc("phg_get_suite_run",{p_run_id:runId}); if(error||!run)return out({error:"run not found"},404);
 if(run.status==="completed"||run.status==="failed")return out(run);
 const offset=Number(run.next_offset||0);
 const r=await fetch(`${url}/functions/v1/phg-golden-tests`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({offset,batch_size:4})});
 const d=await r.json().catch(()=>({}));
 if(!r.ok){await sb.rpc("phg_update_suite_run",{p_run_id:runId,p_status:"failed",p_processed:run.processed,p_passed:run.passed,p_failed:run.failed,p_errors:run.errors+1,p_next_offset:offset,p_last_error:JSON.stringify(d)});return out({status:"failed",detail:d},502);}
 const processed=Number(run.processed)+Number(d.batch_total||0), passed=Number(run.passed)+Number(d.passed||0), failed=Number(run.failed)+Number(d.failed||0), errors=Number(run.errors)+Number(d.errors||0);
 const done=d.next_offset==null; const next=done?processed:Number(d.next_offset);
 await sb.rpc("phg_update_suite_run",{p_run_id:runId,p_status:done?"completed":"running",p_processed:processed,p_passed:passed,p_failed:failed,p_errors:errors,p_next_offset:next,p_last_error:null});
 if(!done){
   EdgeRuntime.waitUntil(fetch(`${url}/functions/v1/phg-suite-worker`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({run_id:runId})}).catch(()=>{}));
 }
 return out({run_id:runId,status:done?"completed":"running",processed,total:run.total,passed,failed,errors});
});