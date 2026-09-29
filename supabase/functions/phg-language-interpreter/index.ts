import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
import { dispatchShadow } from "./shadow_seam.ts";

const INTERPRETER_VERSION = "8+m2-shadow-seam";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});

function localDate(timeZone?:string|null){
  try{
    const p=new Intl.DateTimeFormat("en-CA",{timeZone:timeZone||"UTC",year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date());
    const m:any={};for(const x of p)m[x.type]=x.value;
    return `${m.year}-${m.month}-${m.day}`;
  }catch{return new Date().toISOString().slice(0,10);}
}
function cleanText(x:any){return String(x||"").trim();}
function fallbackInterpret(text:string,catalog:any,active:any){
  const q=text.trim(),l=q.toLowerCase();
  let intent="command_center",exec="read_only",tool="general",route="general";
  let displayMode="standard",displayContext:any={};
  const restaurantMap=/\b(show|map|find|where|locations?)\b[\s\S]{0,90}\b(restaurants?|restaurant menus?|menus?)\b/i.test(q)&&/\b(in|around|near)\b/i.test(q);
  const cityState=q.match(/\b(?:in|around|near)\s+([A-Za-z .'-]+?)(?:,\s*([A-Z]{2}|[A-Za-z ]+))?(?:\?|$)/i);
  if(restaurantMap){
    intent="market_venue_research";tool="venue_research";route="market";displayMode="map";
    const cuisine=(q.match(/\b(mexican|italian|japanese|chinese|indian|thai|korean|french|spanish|mediterranean)\b/i)||[])[1]||"";
    displayContext={map_kind:"restaurant_menu",city:cityState?cleanText(cityState[1]):null,state_code:cityState&&cityState[2]?cleanText(cityState[2]).toUpperCase():null,query:cuisine||"restaurant"};
  }else if(/\b(build|make|create|design|develop|start)\b[\s\S]{0,60}\b(menu|beverage program|drink list|cocktail list)\b|\b(menu|beverage menu)\b[\s\S]{0,50}\b(build|design|create)\b/i.test(q)){
    intent="menu_workflow";exec="proposal_required";tool="menu";route="menu";
  }else if(/\b(build|make|develop|create)\b[\s\S]{0,35}\b(cocktail|drink)\b/i.test(q)){
    intent="cocktail_development";exec="proposal_required";tool="cocktail";route="cocktail";
  }else if(/\b(training|train staff|training package)\b/i.test(q)){
    intent="training_generation";exec="proposal_required";tool="menu";route="training";
  }else if(/\b(cogs|costing|recipe cost|food cost|beverage cost)\b/i.test(q)){
    intent="cogs_analysis";tool="cogs";route="cogs";
  }else if(/\b(labor|wages|hours|payroll)\b/i.test(q)){
    intent="labor_analysis";tool="labor";route="labor";
  }else if(/\b(inventory|count|depletion|variance)\b/i.test(q)){
    intent="inventory_analysis";tool="inventory";route="inventory";
  }else if(/\b(p&l|profit|loss|budget|financial)\b/i.test(q)){
    intent=/\bbudget\b/i.test(q)?"budget_forecast":"pl_analysis";tool="financial";route="financial";
  }else if(/\b(sales|revenue|checks|guests|mix)\b/i.test(q)){
    intent="sales_analysis";tool="sales";route="sales";
  }
  const pts=[q.length>120?q.slice(0,117)+"…":q];
  const entities:any[]=[];
  const cocktails=Array.isArray(catalog?.cocktails)?catalog.cocktails:[];
  const ql=q.toLowerCase();
  for(const c of cocktails){
    const n=cleanText(c?.name);if(n&&ql.includes(n.toLowerCase()))entities.push(n);
    if(entities.length>=6)break;
  }
  return {
    normalized_text:q,intent_hint:intent,execution_class_hint:exec,confidence:0.68,
    needs_clarification:false,clarification_question:null,context_patch:{
      location_key:active?.location_key||null,start_date:null,end_date:null,report_date:null,
      revenue_center:null,budget_plan_id:null,cocktail_name:entities[0]||null,cocktail_names:entities,
      ingredient_name:null,menu_item_id:null,menu_project_id:active?.menu_project_id||null,
      navigation_target:null,retail_state:null,retail_city:null,retail_radius_miles:null,
      retail_year_start:null,retail_year_end:null,retail_category:null,retail_store_query:null,
      retail_store_no:null,retail_vendor:null,retail_item_query:null
    },
    corrections:[],entity_matches:[],
    brief_bullet:intent==="menu_workflow"?"Build and refine a beverage menu":(pts[0]||"Harmony request"),
    recent_points:pts,tool_context:tool,tool_entities:entities,display_mode:displayMode,display_context:displayContext,notes:["deterministic fallback"],degraded:true
  };
}
function trimCatalog(x:any){
  const c=x||{};
  return {
    account:c.account||null,
    locations:(c.locations||[]).slice(0,50),
    menu_projects:(c.menu_projects||[]).slice(0,50),
    menu_items:(c.menu_items||[]).slice(0,200),
    ingredients:(c.ingredients||[]).slice(0,400),
    vendors:(c.vendors||[]).slice(0,150),
    labor_roles:(c.labor_roles||[]).slice(0,150),
    expense_categories:(c.expense_categories||[]).slice(0,150),
    cocktails:(c.cocktails||[]).slice(0,350)
  };
}

Deno.serve(async req=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL"),service=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"),oa=Deno.env.get("OPENAI_API_KEY");
  if(!url||!service)return out({error:"runtime configuration missing"},500);
  const auth=req.headers.get("Authorization")||"";
  if(!auth.toLowerCase().startsWith("bearer "))return out({error:"login required"},401);
  const jwt=auth.slice(7).trim();
  const sb=createClient(url,service,{auth:{persistSession:false}});
  const {data:ud,error:ue}=await sb.auth.getUser(jwt);
  if(ue||!ud?.user)return out({error:"invalid or expired login"},401);
  const user=ud.user;
  const b=await req.json().catch(()=>({}));
  const action=String(b.action||"interpret");

  const {data:catalog,error:ctxErr}=await sb.rpc("phg_language_context",{
    p_user_id:user.id,p_account_id:b.account_id||null,p_menu_project_id:b.menu_project_id||null
  });
  if(ctxErr)return out({error:ctxErr.message},403);
  const cat=trimCatalog(catalog);
  const accountId=cat.account?.id;

  if(action==="history"){
    if(!accountId)return out({status:"ok",items:[]});
    const limit=Math.max(1,Math.min(100,Number(b.limit||40)));
    const {data,error}=await sb.schema("phg").from("language_interpretations")
      .select("id,brief_bullet,recent_points,tool_context,tool_entities,display_mode,display_context,intent_hint,normalized_text,created_at")
      .eq("account_id",accountId).eq("user_id",user.id).order("created_at",{ascending:false}).limit(limit);
    if(error)return out({error:error.message},500);
    return out({status:"ok",items:data||[]});
  }

  const rawText=cleanText(b.user_text);
  if(!rawText)return out({error:"user_text required"},400);
  const t0=Date.now();
  const active=b.active_context||{};
  const recent=Array.isArray(b.recent_conversation)?b.recent_conversation.slice(-10):[];
  const base=fallbackInterpret(rawText,cat,active);
  if(!oa){
    try{if(accountId)await sb.schema("phg").from("language_interpretations").insert({
      account_id:accountId,user_id:user.id,command_session_id:b.command_session_id||null,raw_text:rawText,
      normalized_text:base.normalized_text,intent_hint:base.intent_hint,execution_class_hint:base.execution_class_hint,
      confidence:base.confidence,needs_clarification:false,context_patch:base.context_patch,active_context:active,
      brief_bullet:base.brief_bullet,recent_points:base.recent_points,tool_context:base.tool_context,tool_entities:base.tool_entities,display_mode:base.display_mode,display_context:base.display_context,model:"fallback"
    });}catch{}
    return out(base);
  }

  const intents=["navigation","cocktail_menu_training_workflow","menu_training_workflow","price_change_workflow","period_review",
    "management_operations","variance_explanation","pl_analysis","budget_forecast","labor_analysis","expense_analysis",
    "inventory_analysis","purchasing","cogs_analysis","training_generation","cocktail_development","menu_workflow",
    "sales_analysis","market_venue_research","retail_sales_analysis","command_center"];

  const schema:any={type:"object",additionalProperties:false,properties:{
    normalized_text:{type:"string"},intent_hint:{type:"string",enum:intents},
    execution_class_hint:{type:"string",enum:["read_only","proposal_required","approval_required"]},
    confidence:{type:"number"},needs_clarification:{type:"boolean"},clarification_question:{type:["string","null"]},
    context_patch:{type:"object",additionalProperties:true},
    corrections:{type:"array",items:{type:"object",additionalProperties:true}},
    entity_matches:{type:"array",items:{type:"object",additionalProperties:true}},
    brief_bullet:{type:"string"},recent_points:{type:"array",items:{type:"string"}},
    tool_context:{type:"string",enum:["cocktail","brand_history","sales","retail_sales","local_retail","venue_research","labor","cogs","inventory","purchasing","financial","menu","general"]},
    tool_entities:{type:"array",items:{type:"string"}},
    display_mode:{type:"string",enum:["standard","map","timeline","chart","comparison","recipe","network","evidence","builder"]},
    display_context:{type:"object",additionalProperties:true},
    notes:{type:"array",items:{type:"string"}}
  },required:["normalized_text","intent_hint","execution_class_hint","confidence","needs_clarification","clarification_question",
    "context_patch","corrections","entity_matches","brief_bullet","recent_points","tool_context","tool_entities","display_mode","display_context","notes"]};

  const instructions=`You are Harmony's semantic interpreter for Perfect Harmony Group. Convert typed or dictated language into a canonical PHG request; do not answer or execute.

Critical routing:
- A request to build/create/design/develop a WHOLE beverage menu, cocktail menu, drink list, or venue menu is menu_workflow. Do NOT downgrade it to command_center or management_dashboard.
- A request to build one cocktail is cocktail_development.
- "Make me a margarita menu" means menu_workflow, not one Margarita cocktail.
- Follow-up questions such as "what's the progress" or "anything building yet" should preserve the active workflow from context; if a menu workflow is active, keep menu_workflow.
- Venue type, cuisine, concept, demographics, price point, geography, trends, brand guidelines, visual style, fonts, page size, orientation, export formats, website/interactive menu and item/category preferences are all menu_workflow context, not separate hard-coded menu types.
- Correct likely speech-to-text substitutions only when the PHG catalog or surrounding context strongly grounds the intended word. Never invent an entity.
- normalized_text must preserve explicit ingredients, brands, sizes, prices, formats, design choices and requested outputs.
- For a menu build, brief_bullet should describe the menu-build task and recent_points should capture the active menu decisions/questions.
- tool_context should be menu for whole-menu work.
- Venue/restaurant geography research such as "show me Mexican restaurant menus in Iowa City, Iowa" is market_venue_research, read_only, tool_context venue_research, display_mode map. Put map_kind="restaurant_menu", grounded city/state, and cuisine/query terms in display_context. Never guess missing geography.
- Use proposal_required for creating/editing menu content or design state.
- If a user requests a new menu without enough detail, do not block immediately on every missing field. Route menu_workflow and let the interactive menu-building workflow ask progressive questions.
- If one consequential target is genuinely ambiguous, set needs_clarification and ask ONE concise question.
- Relative dates use account-local date ${localDate(cat.account?.timezone)}.

Return only the JSON schema.`;

  let interpreted:any=null,model="gpt-4o-mini",detail:any=null;
  try{
    const rr=await fetch("https://api.openai.com/v1/responses",{
      method:"POST",headers:{Authorization:`Bearer ${oa}`,"Content-Type":"application/json"},
      body:JSON.stringify({model,instructions,input:JSON.stringify({raw_transcript:rawText,active_context:active,recent_conversation:recent,catalog:cat}),
        text:{format:{type:"json_schema",name:"phg_language_interpretation",strict:true,schema}}})
    });
    const raw=await rr.json().catch(()=>({}));
    if(rr.ok){
      let txt=raw.output_text;
      if(!txt&&Array.isArray(raw.output))for(const item of raw.output||[])for(const p of item?.content||[])if(p?.type==="output_text"&&p?.text){txt=p.text;break;}
      if(txt)interpreted=JSON.parse(txt);
    }else detail=raw?.error?.message||raw;
  }catch(e:any){detail=String(e?.message||e);}

  if(!interpreted){interpreted={...base,notes:[...(base.notes||[]),"model interpreter unavailable"],degraded:true};}
  interpreted.context_patch={...base.context_patch,...(interpreted.context_patch||{})};
  interpreted.recent_points=Array.isArray(interpreted.recent_points)&&interpreted.recent_points.length?interpreted.recent_points.slice(0,4):base.recent_points;
  interpreted.tool_entities=Array.isArray(interpreted.tool_entities)?interpreted.tool_entities.slice(0,8):[];
  interpreted.display_mode=interpreted.display_mode||base.display_mode||"standard";
  interpreted.display_context={...(base.display_context||{}),...(interpreted.display_context||{})};
  if(detail)interpreted.notes=[...(interpreted.notes||[]),"model fallback used"];

  try{if(accountId)await sb.schema("phg").from("language_interpretations").insert({
    account_id:accountId,user_id:user.id,command_session_id:b.command_session_id||null,raw_text:rawText,
    normalized_text:interpreted.normalized_text||rawText,intent_hint:interpreted.intent_hint||base.intent_hint,
    execution_class_hint:interpreted.execution_class_hint||base.execution_class_hint,confidence:interpreted.confidence??base.confidence,
    needs_clarification:!!interpreted.needs_clarification,clarification_question:interpreted.clarification_question||null,
    corrections:interpreted.corrections||[],entity_matches:interpreted.entity_matches||[],context_patch:interpreted.context_patch||{},
    active_context:active,brief_bullet:interpreted.brief_bullet||base.brief_bullet,recent_points:interpreted.recent_points||base.recent_points,
    tool_context:interpreted.tool_context||base.tool_context,tool_entities:interpreted.tool_entities||[],display_mode:interpreted.display_mode||base.display_mode,display_context:interpreted.display_context||base.display_context,model:interpreted.degraded?"fallback":model
  });}catch{}

  // PHG Milestone 2 shadow seam. Non-blocking, failure-swallowing, advisory only.
  // The authoritative result below is already fixed and is NOT affected by this call.
  dispatchShadow(req,b,{interpreted,rawText,active,recent,accountId,model:interpreted.degraded?"fallback":model,interpreterVersion:INTERPRETER_VERSION,latencyMs:Date.now()-t0,userId:user.id});

  return out({...interpreted,raw_text:rawText,model:interpreted.degraded?"fallback":model,interpreted_at:new Date().toISOString()});
});
