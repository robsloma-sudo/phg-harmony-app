import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
const cors={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type"};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});
function words(s:string){return s.toLowerCase().replace(/[^a-z0-9 ]/g," ").split(/\s+/).filter(x=>x.length>2)}
function searchHint(msg:string){const stop=new Set(["what","were","this","that","with","from","last","year","month","show","compare","analyze","cocktail","price","prices","average","median","venue","restaurant","market","income","household","many","does","have"]);return words(msg).filter(x=>!stop.has(x)).slice(0,4).join(" ")}
Deno.serve(async(req)=>{
 if(req.method==="OPTIONS") return new Response("ok",{headers:cors});
 if(req.method!=="POST") return out({error:"POST required"},405);
 const url=Deno.env.get("SUPABASE_URL"), key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
 if(!url||!key) return out({error:"runtime config missing"},500);
 const b=await req.json().catch(()=>({})); const message=String(b.message||"").trim();
 if(!message) return out({error:"message required"},400);
 const sb=createClient(url,key,{auth:{persistSession:false}});
 if(b?.use_capability_router!==false){
   const cr=await fetch(`${url}/functions/v1/phg-capability-router`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({message,conversation_context:b.conversation_context||null})});
   const cd=await cr.json().catch(()=>({}));
   if(cr.ok && cd?.status==="executed" && Array.isArray(cd.results) && cd.results.some((x:any)=>x.status==="succeeded")){
     const ar=await fetch(`${url}/functions/v1/phg-reconcile-answer`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({message,conversation_id:b.conversation_id||null,capability_execution:cd})});
     const ad=await ar.json().catch(()=>({}));
     if(ar.ok) return out(ad);
     return out({status:"capabilities_executed",capability_execution:cd,reconciliation_error:ad});
   }
   if(cr.ok && cd?.status==="needs_clarification") return out(cd);
 }
 const planResp=await fetch(`${url}/functions/v1/phg-orchestrator`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${key}`,"apikey":key},body:JSON.stringify({message,conversation_id:b.conversation_id||null,external_key:b.external_key||null,conversation_context:b.conversation_context||null})});
 const planned=await planResp.json(); if(!planResp.ok) return out({stage:"planning",...planned},502);
 const plan=planned.plan;
 if(plan.needs_clarification) return out({status:"needs_clarification",conversation_id:planned.conversation_id,question:plan.clarification_question,plan});
 const concepts=new Set(plan.referenced_concepts||[]);
 const quality=plan.applicable_quality_rules||[];
 if(quality.includes("iowa_historical_truncation") && /2020|2021|2022|2023|2024|year.over.year|yoy/i.test(message))
   return out({status:"blocked",conversation_id:planned.conversation_id,reason:"Known incomplete Iowa historical slices are not fit for ordinary full-year comparison.",quality_rules:quality,plan});
 const hint=searchHint(message)||null; const evidence:any={}; let retrieved=0;
 if(concepts.has("venue_menu_profile")||concepts.has("menu_price")){
   const {data,error}=await sb.rpc("phg_read_venue_profiles",{p_search:hint,p_limit:20}); if(error)return out({stage:"retrieve",error:error.message},500); evidence.venue_profiles=data; retrieved+=(data||[]).length;
 }
 if(concepts.has("market_demographics")){
   const {data,error}=await sb.rpc("phg_read_market_demographics",{p_search:hint,p_limit:20}); if(error)return out({stage:"retrieve",error:error.message},500); evidence.demographics=data; retrieved+=(data||[]).length;
 }
 if(retrieved===0) return out({status:"insufficient_data",conversation_id:planned.conversation_id,message:"PHG does not yet have an approved read-only execution path for the requested data.",plan});
 let answer:any=null; let claim=""; let value:any=null;
 const vp=evidence.venue_profiles||[], dm=evidence.demographics||[];
 if(vp.length===1 && /average cocktail price/i.test(message)){value={amount:vp[0].cocktail_avg_price,currency:"USD"};claim=`Average cocktail price for ${vp[0].venue} is ${vp[0].cocktail_avg_price} USD.`;answer=claim;}
 else if(vp.length===1 && /(how many|count).*(cocktail)/i.test(message)){value={count:vp[0].cocktail_items};claim=`${vp[0].venue} has ${vp[0].cocktail_items} cocktail items in the current derived venue profile.`;answer=claim;}
 else if(dm.length===1 && /median.*household.*income|household.*income/i.test(message)){value={amount:dm[0].median_household_income,currency:"USD",acs_vintage:dm[0].acs_vintage};claim=`Median household income for ${dm[0].geography_name} is ${dm[0].median_household_income} USD (ACS ${dm[0].acs_vintage}).`;answer=claim;}
 if(!answer) return out({status:"evidence_retrieved",conversation_id:planned.conversation_id,plan,execution:{retrieved_records:retrieved,quality_rules:quality,evidence}});
 const firstGoal=planned.goals?.[0]?.goal_id;
 let firstTask:any=null;
 if(firstGoal){ const {data:t}=await sb.rpc("phg_first_task_for_goal",{p_goal_id:firstGoal});firstTask=t||null;}
 let trace:any=null;
 if(firstGoal&&firstTask){const {data}=await sb.rpc("phg_record_execution_result",{p_goal_id:firstGoal,p_task_id:firstTask,p_evidence:evidence,p_claim_statement:claim,p_claim_value:value,p_result_content:{answer},p_verification:{passed:true,method:"deterministic",retrieved_records:retrieved}});trace=data;}
 return out({status:"verified_result",conversation_id:planned.conversation_id,answer,value,quality_rules:quality,trace,plan});
});