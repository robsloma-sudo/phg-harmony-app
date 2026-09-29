import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{"Content-Type":"application/json"}});
function evaluate(test:any, turns:any[], state:any){
 const exp=test.expected_state||{}, reasons:string[]=[]; let pass=true;
 const goals=state?.goals||[]; const all=JSON.stringify({turns,state}).toLowerCase();
 if(exp.minimum_goals && goals.length<exp.minimum_goals){pass=false;reasons.push("not enough persistent goals");}
 if(exp.must_preserve_goal && !goals.some((g:any)=>JSON.stringify(g).toLowerCase().includes(String(exp.must_preserve_goal).toLowerCase()))){pass=false;reasons.push("required goal not preserved");}
 if(exp.must_attach_requirement && !all.includes(String(exp.must_attach_requirement).toLowerCase())){pass=false;reasons.push("requirement not preserved");}
 if(exp.must_pause_named_goal_only && !turns.some((x:any)=>x.response?.status==="goal_suspended")){pass=false;reasons.push("named goal was not suspended");}
 if(exp.must_resume_named_goal && !turns.some((x:any)=>x.response?.status==="goal_resumed")){pass=false;reasons.push("named goal was not resumed");}
 if(exp.must_clarify_if_multiple_candidates && !turns.some((x:any)=>x.response?.status==="needs_clarification")){pass=false;reasons.push("ambiguous referent was not clarified");}
 if(exp.must_branch && !all.includes("plan")){pass=false;reasons.push("no branch/plan evidence observed");}
 return {pass,reasons,goal_count:goals.length};
}
Deno.serve(async(req)=>{
 if(req.method!=="POST")return out({error:"POST required"},405);
 const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
 if(!url||!key)return out({error:"runtime config missing"},500);
 const sb=createClient(url,key,{auth:{persistSession:false}}); const body=await req.json().catch(()=>({}));
 const {data:tests,error}=await sb.rpc("phg_conversation_tests"); if(error)return out({error:error.message},500);
 const chosen=(tests||[]).filter((t:any)=>!body.test_key||t.test_key===body.test_key); const results:any[]=[];
 for(const test of chosen){
  let cid:any=null; const turnResults:any[]=[]; let err:any=null;
  for(const turn of test.turns){
   try{
    const r=await fetch(`${url}/functions/v1/phg-conversation`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({message:turn.user,conversation_id:cid,external_key:cid?null:`ct:${test.test_key}:${crypto.randomUUID()}`})});
    const d=await r.json(); cid=d.conversation_id||cid; turnResults.push({user:turn.user,http:r.status,response:d}); if(!r.ok){err=JSON.stringify(d);break;}
   }catch(e){err=String(e);break;}
  }
  let state:any=null;if(cid){const s=await sb.rpc("phg_conversation_state",{p_conversation_id:cid});state=s.data;}
  const ev=err?{pass:false,reasons:[err]}:evaluate(test,turnResults,state); const status=err?"error":ev.pass?"passed":"failed";
  await sb.rpc("phg_record_conversation_test_run",{p_test_id:test.id,p_conversation_id:cid,p_version:"0.4",p_status:status,p_turn_results:turnResults,p_evaluation:ev,p_error:err});
  results.push({test_key:test.test_key,status,evaluation:ev,conversation_id:cid});
 }
 return out({version:"0.4",total:results.length,passed:results.filter(x=>x.status==="passed").length,failed:results.filter(x=>x.status==="failed").length,errors:results.filter(x=>x.status==="error").length,results});
});