import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});

function outputText(raw:any){
  if(typeof raw?.output_text==="string" && raw.output_text) return raw.output_text;
  if(Array.isArray(raw?.output)){
    for(const item of raw.output){
      if(Array.isArray(item?.content)){
        for(const part of item.content){
          if(part?.type==="output_text" && typeof part.text==="string") return part.text;
        }
      }
    }
  }
  return "";
}

function collectSources(raw:any){
  const out:any[]=[];
  const seen=new Set<string>();
  const walk=(v:any)=>{
    if(!v || typeof v!=="object") return;
    if(typeof v.url==="string" && /^https?:\/\//i.test(v.url)){
      const url=v.url;
      if(!seen.has(url)){
        seen.add(url);
        out.push({url,title:typeof v.title==="string"?v.title:null});
      }
    }
    if(Array.isArray(v)) for(const x of v) walk(x);
    else for(const k of Object.keys(v)) walk(v[k]);
  };
  walk(raw?.output||raw);
  return out.slice(0,80);
}
function normalizeUrl(u:any){
  return String(u||"").trim().replace(/\/$/,"");
}

Deno.serve(async req=>{
  if(req.method==="OPTIONS") return new Response("ok",{headers:cors});
  if(req.method!=="POST") return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL");
  const key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const oa=Deno.env.get("OPENAI_API_KEY");
  const model=Deno.env.get("OPENAI_MODEL")||"gpt-4o-mini";
  const searchModel=Deno.env.get("OPENAI_SEARCH_MODEL")||model;
  if(!url||!key||!oa) return out({error:"runtime configuration missing"},500);

  const b=await req.json().catch(()=>({}));
  const menuProjectId=b.menu_project_id;
  const menuItemId=b.menu_item_id;
  const syncToken=b.sync_token;
  if(!menuProjectId||!menuItemId||!syncToken) return out({error:"menu_project_id, menu_item_id and sync_token required"},400);

  const sb=createClient(url,key,{auth:{persistSession:false}});
  const {data:ctx,error:ctxErr}=await sb.rpc("phg_training_context",{
    p_menu_project_id:menuProjectId,
    p_sync_token:syncToken,
    p_menu_item_id:menuItemId
  });
  if(ctxErr){
    const msg=String(ctxErr.message||ctxErr);
    return out({error:msg},msg.includes("invalid_menu_token")?403:500);
  }

  const mi=ctx?.menu_item||{};
  if(!mi.current_recipe_version_id){
    return out({error:"This menu item has no linked recipe version yet. Generate or link a structured recipe before training."},409);
  }

  const compNames=(ctx?.components||[]).map((x:any)=>x?.name).filter(Boolean);
  const metadata=ctx?.editor_metadata||{};
  const researchQuery=[
    mi.name,
    ctx?.recipe?.recipe_name,
    metadata?.brand,
    compNames.join(", "),
    "cocktail history spirit category producer brand production method staff training"
  ].filter(Boolean).join(" | ");

  let researchNotes="";
  let sources:any[]=[];
  let researchStatus="completed";
  let researchError:string|null=null;

  try{
    const rr=await fetch("https://api.openai.com/v1/responses",{
      method:"POST",
      headers:{"Authorization":`Bearer ${oa}`,"Content-Type":"application/json"},
      body:JSON.stringify({
        model:searchModel,
        tools:[{type:"web_search"}],
        include:["web_search_call.action.sources"],
        instructions:[
          "Research background for a professional beverage staff training packet.",
          "Use web search. Prefer primary producer/brand sites, official category/regulatory sources, creator interviews, and respected beverage publications.",
          "Research only facts relevant to the exact menu item and its ingredients/products: cocktail lineage/history, spirit/category production, brand or producer story, ingredient origin/context, and memorable but accurate service talking points.",
          "Do not invent facts. Distinguish a producer's own claim from independently reported information.",
          "Avoid long quotations. Return concise research notes with citations."
        ].join("\n"),
        input:JSON.stringify({
          menu_item:mi,
          recipe:ctx?.recipe||null,
          components:ctx?.components||[],
          preps:ctx?.preps||[],
          editor_metadata:metadata
        })
      })
    });
    const raw=await rr.json();
    if(!rr.ok) throw new Error(raw?.error?.message||"web research failed");
    researchNotes=outputText(raw);
    sources=collectSources(raw);
    if(!researchNotes) researchStatus="partial";
  }catch(e:any){
    researchStatus="partial";
    researchError=String(e?.message||e);
  }

  const sourceList=sources.map((s:any)=>({url:s.url,title:s.title}));
  const schema={
    type:"object",additionalProperties:false,
    properties:{
      content:{
        type:"object",additionalProperties:false,
        properties:{
          title:{type:"string"},
          recipe_training:{
            type:"object",additionalProperties:false,
            properties:{
              spec_lines:{type:"array",items:{type:"string"}},
              method:{type:"string"},
              glassware:{type:"string"},
              garnish:{type:"string"},
              prep_dependencies:{type:"array",items:{type:"string"}},
              qc_checks:{type:"array",items:{type:"string"}},
              common_mistakes:{type:"array",items:{type:"string"}}
            },
            required:["spec_lines","method","glassware","garnish","prep_dependencies","qc_checks","common_mistakes"]
          },
          why_it_works:{
            type:"object",additionalProperties:false,
            properties:{
              classic_lineage:{type:"string"},
              structure:{type:"string"},
              flavor_progression:{type:"string"}
            },
            required:["classic_lineage","structure","flavor_progression"]
          },
          category_education:{type:"array",items:{type:"string"}},
          brand_product_background:{type:"array",items:{type:"string"}},
          fun_background:{type:"array",items:{type:"string"}},
          guest_language:{
            type:"object",additionalProperties:false,
            properties:{
              ten_second:{type:"string"},
              thirty_second:{type:"string"},
              tasting_notes:{type:"array",items:{type:"string"}},
              common_questions:{
                type:"array",
                items:{
                  type:"object",additionalProperties:false,
                  properties:{question:{type:"string"},answer:{type:"string"}},
                  required:["question","answer"]
                }
              }
            },
            required:["ten_second","thirty_second","tasting_notes","common_questions"]
          },
          rollout_notes:{type:"array",items:{type:"string"}},
          limitations:{type:"array",items:{type:"string"}}
        },
        required:["title","recipe_training","why_it_works","category_education","brand_product_background","fun_background","guest_language","rollout_notes","limitations"]
      },
      claims:{
        type:"array",
        items:{
          type:"object",additionalProperties:false,
          properties:{
            claim_type:{type:"string"},
            statement:{type:"string"},
            source_url:{type:["string","null"]},
            source_label:{type:["string","null"]},
            source_kind:{type:"string",enum:["internal","producer","official","secondary","unverified"]},
            verification_status:{type:"string",enum:["verified","producer_claim","secondary","unverified"]}
          },
          required:["claim_type","statement","source_url","source_label","source_kind","verification_status"]
        }
      },
      assessments:{
        type:"array",
        items:{
          type:"object",additionalProperties:false,
          properties:{
            assessment_type:{type:"string"},
            prompt:{type:"string"},
            answer:{type:"object",additionalProperties:true},
            sort_order:{type:"integer"}
          },
          required:["assessment_type","prompt","answer","sort_order"]
        }
      }
    },
    required:["content","claims","assessments"]
  };

  const sr=await fetch("https://api.openai.com/v1/responses",{
    method:"POST",
    headers:{"Authorization":`Bearer ${oa}`,"Content-Type":"application/json"},
    body:JSON.stringify({
      model,
      instructions:[
        "You are PHG Training Package Generator v1.",
        "Build a concise professional staff training package for the exact recipe version supplied.",
        "Recipe/spec/service facts from PHG internal context may be treated as verified internal facts.",
        "For external history, category, producer, brand, ingredient, or cultural facts, use only the supplied research notes and supplied source URLs.",
        "Every external factual claim must appear in claims with a source_url copied exactly from the supplied source list. If no adequate source exists, label it unverified and do not present it confidently in the training prose.",
        "First-party producer or brand statements must use verification_status producer_claim, not verified.",
        "Independent publication claims use secondary unless they are merely quoting a producer, in which case use producer_claim.",
        "Do not invent COGS, purchase cost, inventory, sales performance, provenance, ABV, or production details that are absent.",
        "Generate practical guest language, QC points, common mistakes, and a short quiz."
      ].join("\n"),
      input:JSON.stringify({
        internal_context:ctx,
        research_notes:researchNotes,
        research_sources:sourceList,
        research_error:researchError
      }),
      text:{format:{type:"json_schema",name:"phg_training_package_v1",strict:true,schema}}
    })
  });
  const synthRaw=await sr.json();
  if(!sr.ok) return out({error:"training synthesis failed",detail:synthRaw?.error?.message||synthRaw},502);
  const txt=outputText(synthRaw);
  if(!txt) return out({error:"training synthesis returned no output"},502);
  const generated=JSON.parse(txt);

  const allowed=new Set(sourceList.map((s:any)=>normalizeUrl(s.url)));
  const claims=(generated.claims||[]).map((c:any)=>{
    const kind=String(c.source_kind||"unverified");
    let status=String(c.verification_status||"unverified");
    let sourceUrl=c.source_url||null;
    if(kind==="internal"){
      status="verified"; sourceUrl=null;
    }else{
      const ok=sourceUrl && allowed.has(normalizeUrl(sourceUrl));
      if(!ok){ status="unverified"; }
      else if(kind==="producer"){ status="producer_claim"; }
      else if(status==="verified"){ status="secondary"; }
    }
    return {...c,source_url:sourceUrl,verification_status:status,metadata:{research_status:researchStatus}};
  });

  const {data:persisted,error:pErr}=await sb.rpc("phg_training_persist",{
    p_menu_item_id:menuItemId,
    p_recipe_version_id:mi.current_recipe_version_id,
    p_content:generated.content,
    p_claims:claims,
    p_assessments:generated.assessments||[],
    p_research:{
      query_text:researchQuery,
      model:searchModel,
      status:researchStatus,
      source_count:sourceList.length,
      sources:sourceList,
      research_notes:researchNotes
    }
  });
  if(pErr) return out({error:pErr.message},500);

  return out({
    status:"training_created",
    menu_item_id:menuItemId,
    recipe_version_id:mi.current_recipe_version_id,
    training:persisted,
    content:generated.content,
    claims,
    assessments:generated.assessments||[],
    research:{status:researchStatus,source_count:sourceList.length,sources:sourceList,error:researchError}
  });
});