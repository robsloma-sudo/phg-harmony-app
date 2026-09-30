import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{"Content-Type":"application/json"}});
Deno.serve(async req=>{
 if(req.method!=="POST")return out({error:"POST required"},405);
 const callerAuth=req.headers.get("Authorization")||"";
 const callerApiKey=req.headers.get("apikey")||Deno.env.get("SUPABASE_ANON_KEY")||"";
 const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"),oa=Deno.env.get("OPENAI_API_KEY"),model=Deno.env.get("OPENAI_MODEL")||"gpt-4o-mini";
 if(!url||!key||!oa)return out({error:"runtime configuration missing"},500);
 const b=await req.json().catch(()=>({}));
 const brief=String(b.brief||"").trim();
 const count=Math.max(1,Math.min(Number(b.candidate_count||3),5));
 if(!brief)return out({error:"brief required"},400);
 const sb=createClient(url,key,{auth:{persistSession:false}});
 if(b.menu_project_id){
   const {data:ok,error:ae}=await sb.rpc("phg_menu_authorize",{p_menu_project_id:b.menu_project_id,p_sync_token:b.sync_token||null});
   if(ae)return out({error:ae.message},500);
   if(!ok)return out({error:"invalid_menu_token"},403);
 }
 const reference=String(b.reference_cocktail||brief);
 const {data:ctx,error:ctxErr}=await sb.rpc("phg_recipe_context",{p_query:reference,p_spirit:b.base_spirit||null});
 if(ctxErr)return out({error:"Could not load recipe context",detail:ctxErr.message},500);

 const simplePrepComponent={
   type:"object",additionalProperties:false,
   properties:{
     name:{type:"string"},
     quantity:{type:"number",exclusiveMinimum:0},
     unit:{type:"string",enum:["oz","ml","tsp","tbsp","g","kg","lb","each","dash","drop"]},
     role:{type:"string"},
     ingredient_type:{type:"string"},
     category:{type:["string","null"]},
     yield_pct:{type:"number",exclusiveMinimum:0,maximum:100},
     notes:{type:["string","null"]},
     sort_order:{type:"integer"}
   },
   required:["name","quantity","unit","role","ingredient_type","category","yield_pct","notes","sort_order"]
 };
 const component={
   type:"object",additionalProperties:false,
   properties:{
     kind:{type:"string",enum:["ingredient","prep"]},
     name:{type:"string"},
     quantity:{type:"number",exclusiveMinimum:0},
     unit:{type:"string",enum:["oz","ml","tsp","tbsp","g","kg","lb","each","dash","drop"]},
     role:{type:"string"},
     ingredient_type:{type:"string"},
     category:{type:["string","null"]},
     optional:{type:"boolean"},
     notes:{type:["string","null"]},
     sort_order:{type:"integer"},
     prep:{
       anyOf:[
         {type:"null"},
         {type:"object",additionalProperties:false,
          properties:{
            description:{type:["string","null"]},
            prep_type:{type:"string",enum:["fatwash","acid","batch","syrup","shrub","infusion","cordial","other"]},
            batch_yield:{type:"number",exclusiveMinimum:0},
            batch_yield_unit:{type:"string",enum:["oz","ml","l","g","kg","each"]},
            method:{type:"string"},
            components:{type:"array",items:simplePrepComponent}
          },
          required:["description","prep_type","batch_yield","batch_yield_unit","method","components"]
         }
       ]
     }
   },
   required:["kind","name","quantity","unit","role","ingredient_type","category","optional","notes","sort_order","prep"]
 };
 const candidate={
   type:"object",additionalProperties:false,
   properties:{
     name:{type:"string"},
     concept:{type:"string"},
     build_family:{type:["string","null"]},
     method:{type:"string"},
     glassware:{type:"string"},
     garnish:{type:"string"},
     menu_description:{type:"string"},
     proposed_price:{type:["number","null"]},
     price_basis:{type:["string","null"]},
     training_required:{type:"boolean"},
     targets:{
       type:"object",additionalProperties:false,
       properties:{style:{type:"string"},balance:{type:"string"},service:{type:"string"}},
       required:["style","balance","service"]
     },
     rationale:{type:"array",items:{type:"string"}},
     components:{type:"array",minItems:2,items:component}
   },
   required:["name","concept","build_family","method","glassware","garnish","menu_description","proposed_price","price_basis","training_required","targets","rationale","components"]
 };
 const schema={
   type:"object",additionalProperties:false,
   properties:{
     candidates:{type:"array",minItems:count,maxItems:count,items:candidate},
     menu_level_notes:{type:"array",items:{type:"string"}},
     missing_data:{type:"array",items:{type:"string"}}
   },
   required:["candidates","menu_level_notes","missing_data"]
 };
 const instructions=[
   "You are PHG Recipe Generator v2.",
   `Generate exactly ${count} materially distinct cocktail menu-item candidates from the user's brief.`,
   "Use supplied canonical cocktail/spec/build evidence when relevant, but do not copy it blindly.",
   "Each candidate must be a structured executable recipe, not prose only.",
   "Use nested prep objects for house-made syrups, infusions, fat-washed spirits, cordials, batches, or other preparations; do not hide prep work inside notes.",
   "Keep candidates meaningfully different in flavor/structure, not cosmetic renames.",
   "Do not invent purchase costs, COGS, sales performance, inventory performance, or vendor data.",
   "A proposed menu price is allowed only when supported by user constraints or observational market price context; otherwise use null. Explain the basis in price_basis.",
   "Generated ingredient identities will be stored as draft/unverified until confirmed.",
   "For a prep used in a cocktail, the component quantity is the amount of finished prep used in ONE drink. The prep object's batch_yield is the batch output. Never use the whole batch yield as the cocktail component quantity.",
   "Do not include both a raw ingredient and a prepared version of that same ingredient for the same functional role unless the drink truly uses both.",
   "Use unit dash for bitters specified in dashes and drop for drops. Do not convert dashes into teaspoons.",
   "If a house-made preparation is used, represent it as a prep recipe with its own source ingredients, yield, method, and prep_type. Use fatwash, acid, batch, syrup, shrub, infusion, cordial, or other.",
   "Training_required should be true when the item has enough technique, product knowledge, prep, or storytelling value that rollout training would materially help."
 ].join("\n");

 const rr=await fetch("https://api.openai.com/v1/responses",{
   method:"POST",
   headers:{"Authorization":`Bearer ${oa}`,"Content-Type":"application/json"},
   body:JSON.stringify({
     model,
     instructions,
     input:JSON.stringify({
       brief,
       candidate_count:count,
       reference_cocktail:b.reference_cocktail||null,
       base_spirit:b.base_spirit||null,
       constraints:b.constraints||{},
       existing_menu_context:b.existing_menu_context||null,
       evidence:ctx
     }),
     text:{format:{type:"json_schema",name:"phg_menu_item_candidates_v2",strict:true,schema}}
   })
 });
 const raw=await rr.json();
 if(!rr.ok)return out({error:"generation failed",detail:raw?.error?.message||raw},502);
 let txt=raw.output_text;
 if(!txt&&Array.isArray(raw.output))for(const i of raw.output){const p=i?.content?.find((x:any)=>x?.type==="output_text");if(p?.text){txt=p.text;break;}}
 if(!txt)return out({error:"generator returned no output"},502);
 const generated=JSON.parse(txt);

 const {data:persisted,error:pErr}=await sb.rpc("phg_persist_generated_menu_candidates_v2",{
   p_menu_project_id:b.menu_project_id||null,
   p_sync_token:b.sync_token||null,
   p_conversation_id:b.conversation_id||null,
   p_project_name:b.project_name||"Generated Menu Project",
   p_season:b.season||null,
   p_launch_date:b.launch_date||null,
   p_brief:{text:brief,reference_cocktail:b.reference_cocktail||null,base_spirit:b.base_spirit||null},
   p_constraints:b.constraints||{},
   p_candidates:generated.candidates
 });
 if(pErr)return out({error:"candidates generated but persistence failed",detail:pErr.message,candidates:generated},500);

 for(const item of persisted?.candidates||[]){
   EdgeRuntime.waitUntil(fetch(`${url}/functions/v1/phg-menu-item-evaluate`,{
     method:"POST",
     headers:{"Content-Type":"application/json","Authorization":callerAuth,"apikey":callerApiKey},
     body:JSON.stringify({menu_item_id:item.menu_item_id})
   }).catch(()=>{}));
 }

 return out({
   status:"candidates_created",
   menu_project_id:persisted.menu_project_id,
   persisted_candidates:persisted.candidates,
   generated,
   evaluation_started:true
 });
});