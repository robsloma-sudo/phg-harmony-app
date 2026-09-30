import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
const cors={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type"};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});
function check(plan:any, exp:any){
 const reasons:string[]=[]; let pass=true;
 const goals=Array.isArray(plan?.goals)?plan.goals:[];
 if(exp.outcome==="insufficient_data" && !plan?.needs_clarification && goals.some((g:any)=>g.goal_type!=="unknown")) { pass=false; reasons.push("missing-data request was planned as executable without clarification"); }
 if(exp.outcome==="block_ordinary_yoy" && !(plan?.applicable_quality_rules||[]).includes(exp.quality_rule)){pass=false;reasons.push("required blocking quality rule missing");}
 if(exp.outcome==="create_multiple_goals" && goals.length<2){pass=false;reasons.push("multiple goals were not created");}
 if(exp.outcome==="create_competing_plans" && Math.max(0,...goals.map((g:any)=>Array.isArray(g.plans)?g.plans.length:0))<(exp.minimum_plans||2)){pass=false;reasons.push("not enough competing plans");}
 if(exp.outcome==="clarify_or_apply_explicit_preexisting_threshold" && !plan?.needs_clarification){pass=false;reasons.push("undefined threshold was not clarified");}
 if(exp.outcome==="resolve_restaurant_and_clarify_analysis_goal" && !plan?.needs_clarification){pass=false;reasons.push("unbounded analysis was not clarified");}
 if(exp.must_not_estimate===true){
   const text=JSON.stringify(plan).toLowerCase();
   if(text.includes("estimate") && !text.includes("must_not_estimate")) { pass=false; reasons.push("plan appears to estimate unavailable data"); }
 }
 return {pass,reasons,goal_count:goals.length,quality_rules:plan?.applicable_quality_rules||[],needs_clarification:!!plan?.needs_clarification};
}
Deno.serve(async(req)=>{
 if(req.method==="OPTIONS") return new Response("ok",{headers:cors});
 if(req.method!=="POST") return out({error:"POST required"},405);
 const url=Deno.env.get("SUPABASE_URL"), key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
 if(!url||!key) return out({error:"runtime config missing"},500);
 const sb=createClient(url,key,{auth:{persistSession:false}});
 const {data:tests,error}=await sb.rpc("phg_golden_tests"); if(error) return out({error:error.message},500);
 const input=await req.json().catch(()=>({}));
 const selected=input?.test_keys as string[]|undefined;
 const batchSize=Math.max(1,Math.min(Number(input?.batch_size||6),8));
 const offset=Math.max(0,Number(input?.offset||0));
 const all=(tests||[]).filter((t:any)=>!selected||selected.includes(t.test_key));
 const list=all.slice(offset,offset+batchSize);
 const results:any[]=[];
 for(const t of list){
   try{
     const r=await fetch(`${url}/functions/v1/phg-orchestrator`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({message:t.user_request,external_key:`golden:${t.test_key}:${Date.now()}`})});
     const body=await r.json();
     if(!r.ok){
       const ev={pass:false,reasons:[`orchestrator HTTP ${r.status}`],detail:body};
       await sb.rpc("phg_record_test_run",{p_test_id:t.id,p_orchestrator_version:"0.1",p_status:"error",p_response:body,p_evaluation:ev,p_error:JSON.stringify(body)});
       results.push({test_key:t.test_key,status:"error",evaluation:ev}); continue;
     }
     const ev=check(body.plan,t.expected_behavior);
     await sb.rpc("phg_record_test_run",{p_test_id:t.id,p_orchestrator_version:"0.1",p_status:ev.pass?"passed":"failed",p_response:body,p_evaluation:ev,p_error:null});
     results.push({test_key:t.test_key,status:ev.pass?"passed":"failed",evaluation:ev});
   }catch(e){
     const msg=String(e); await sb.rpc("phg_record_test_run",{p_test_id:t.id,p_orchestrator_version:"0.1",p_status:"error",p_response:null,p_evaluation:{pass:false,reasons:[msg]},p_error:msg});
     results.push({test_key:t.test_key,status:"error",error:msg});
   }
 }
 const passed=results.filter(x=>x.status==="passed").length;
 return out({orchestrator_version:"0.1",batch_total:results.length,suite_total:all.length,offset,next_offset:offset+results.length<all.length?offset+results.length:null,passed,failed:results.filter(x=>x.status==="failed").length,errors:results.filter(x=>x.status==="error").length,results});
});