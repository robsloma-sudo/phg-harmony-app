import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});

function miles(a:number,b:number,c:number,d:number){
  const R=3959,toRad=(x:number)=>x*Math.PI/180;
  const dlat=toRad(c-a),dlon=toRad(d-b);
  const q=Math.sin(dlat/2)**2+Math.cos(toRad(a))*Math.cos(toRad(c))*Math.sin(dlon/2)**2;
  return R*2*Math.asin(Math.min(1,Math.sqrt(q)));
}
function cleanCity(x:any){return String(x||"").trim().replace(/\s+/g," ");}
async function geocodeOne(store:any,city:string,state:string,center:any){
  const full=[store.street_address,city,state,store.postal_code].filter(Boolean).join(", ");
  const u=new URL("https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates");
  u.searchParams.set("f","json");
  u.searchParams.set("SingleLine",full);
  u.searchParams.set("maxLocations","1");
  u.searchParams.set("outFields","Match_addr,Addr_type");
  try{
    const r=await fetch(u.toString(),{headers:{"User-Agent":"PHG/1.0"}});
    if(!r.ok)return null;
    const j=await r.json();
    const c=Array.isArray(j?.candidates)?j.candidates[0]:null;
    if(!c?.location)return null;
    const lat=Number(c.location.y),lng=Number(c.location.x),score=Number(c.score||0);
    if(!Number.isFinite(lat)||!Number.isFinite(lng)||score<75)return null;
    const dist=miles(Number(center.latitude),Number(center.longitude),lat,lng);
    if(dist>35)return null;
    return {
      source_account_id:store.id,
      account_external_id:store.account_id||null,
      account_name:store.account_name||null,
      street_address:store.street_address||null,
      city,state_code:state||null,postal_code:store.postal_code||null,
      latitude:lat,longitude:lng,geocode_source:"arcgis_world_geocoder",
      geocode_score:score,match_address:c.address||null,geocoded_at:new Date().toISOString(),
      metadata:{distance_from_city_center_miles:dist}
    };
  }catch{return null;}
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
  const userClient=createClient(url,anon,{auth:{persistSession:false},global:{headers:{Authorization:auth}}});
  const {data:userData,error:userErr}=await userClient.auth.getUser(jwt);
  const user=userData?.user;
  if(userErr||!user)return out({error:"invalid or expired login"},401);

  const b=await req.json().catch(()=>({}));
  const action=String(b.action||"local_retail_map");
  if(!["local_retail_map","restaurant_menu_map"].includes(action))return out({error:"unknown action"},400);

  const sb=createClient(url,service,{auth:{persistSession:false}});
  const {data:ctx,error:ctxErr}=await sb.rpc("phg_language_context",{
    p_user_id:user.id,p_account_id:b.account_id||null,p_menu_project_id:b.menu_project_id||null
  });
  if(ctxErr)return out({error:ctxErr.message},403);

  const city=cleanCity(b.city);
  const state=String(b.state_code||"").trim().toUpperCase();
  const category=String(b.category||"liquor_store");
  if(!city)return out({status:"needs_city",needs_city:true,category});

  let cq=sb.from("geographies").select("geography_name,subdivision_code,latitude,longitude,geo_type")
    .ilike("geography_name",city).eq("geo_type","city").limit(10);
  if(state)cq=cq.eq("subdivision_code",state);
  const {data:cities,error:cityErr}=await cq;
  if(cityErr)return out({error:cityErr.message},500);
  const viable=(cities||[]).filter((x:any)=>x.latitude!=null&&x.longitude!=null);
  if(!state&&viable.length>1){
    return out({
      status:"needs_state",needs_state:true,city,category,
      state_candidates:Array.from(new Set(viable.map((x:any)=>x.subdivision_code).filter(Boolean)))
    });
  }
  const center=viable[0];
  if(!center){
    return out({status:"city_not_found",city,state_code:state||null,category,points:[],stores:[]});
  }
  const resolvedState=String(center.subdivision_code||state||"").toUpperCase();

  if(action==="restaurant_menu_map"){
    const query=String(b.query||b.category||"").trim().toLowerCase();
    const limit=Math.max(1,Math.min(60,Number(b.limit||30)));
    let rq=sb.from("accounts").select("id,account_id,account_name,street_address,postal_code,latitude,longitude,website_url,menu_catalogue_url,concept_code,concept_evidence,google_rating,google_review_count,menu_attempted_at,menu_attempt_note,account_status,notes")
      .eq("account_status","active")
      .ilike("notes",`%City: ${city.toUpperCase()}.%`)
      .order("account_name",{ascending:true})
      .limit(120);
    const {data:allAccounts,error:accountsErr}=await rq;
    if(accountsErr)return out({error:accountsErr.message},500);
    const tokens=query.split(/\s+/).filter((x:string)=>x.length>2&&![ "restaurant","restaurants","menu","menus","food","show","different" ].includes(x));
    const cuisineTerms:any={
      mexican:["mexican","mex","taco","taquer","cactus","agave","cantina","acapulco","el paso","la regia","hacienda","fiesta"],
      italian:["italian","pizza","trattoria","osteria"],
      japanese:["japanese","sushi","ramen","izakaya"],
      chinese:["chinese","szechuan","sichuan","dim sum"],
      indian:["indian","curry","tandoor","masala"],
      thai:["thai"]
    };
    const expanded:string[]=[];
    for(const t of tokens){expanded.push(t);if(cuisineTerms[t])expanded.push(...cuisineTerms[t]);}
    const terms=Array.from(new Set(expanded));
    let accounts=(allAccounts||[]).filter((a:any)=>{
      if(!terms.length)return true;
      const hay=[a.account_name,a.concept_code,a.concept_evidence,a.website_url].filter(Boolean).join(" ").toLowerCase();
      return terms.some((t:string)=>hay.includes(t));
    }).slice(0,limit);

    const accountIds=accounts.map((a:any)=>a.account_id).filter(Boolean);
    let menus:any[]=[];
    if(accountIds.length){
      const {data:md,error:menuErr}=await sb.from("menus")
        .select("id,menu_id,account_id,evidence_url,menu_title,menu_format,extraction_confidence,captured_at,published_date,is_current,item_count,source_file_url,needs_vision_pass")
        .in("account_id",accountIds).order("captured_at",{ascending:false});
      if(!menuErr&&md)menus=md;
    }
    const menuByAccount=new Map();
    for(const m of menus){if(!menuByAccount.has(m.account_id))menuByAccount.set(m.account_id,m);}
    const points=accounts.map((a:any)=>{
      if(a.latitude==null||a.longitude==null)return null;
      const menu=menuByAccount.get(a.account_id)||null;
      return {
        id:a.id,account_id:a.account_id,entity_type:"restaurant",name:a.account_name,address:a.street_address,
        postal_code:a.postal_code,latitude:Number(a.latitude),longitude:Number(a.longitude),
        website_url:a.website_url||null,menu_catalogue_url:a.menu_catalogue_url||null,
        concept_code:a.concept_code||null,google_rating:a.google_rating==null?null:Number(a.google_rating),
        google_review_count:a.google_review_count==null?null:Number(a.google_review_count),
        menu_attempted_at:a.menu_attempted_at||null,menu_attempt_note:a.menu_attempt_note||null,
        menu:menu?{id:menu.id,title:menu.menu_title,format:menu.menu_format,captured_at:menu.captured_at,
          published_date:menu.published_date,item_count:menu.item_count,evidence_url:menu.evidence_url,
          source_file_url:menu.source_file_url,extraction_confidence:menu.extraction_confidence,
          needs_vision_pass:menu.needs_vision_pass}:null,
        distance_miles:miles(Number(center.latitude),Number(center.longitude),Number(a.latitude),Number(a.longitude))
      };
    }).filter(Boolean).sort((a:any,b:any)=>a.distance_miles-b.distance_miles);
    const unmapped=accounts.filter((a:any)=>a.latitude==null||a.longitude==null).map((a:any)=>({
      id:a.id,account_id:a.account_id,name:a.account_name,address:a.street_address,postal_code:a.postal_code,
      website_url:a.website_url||null,menu_attempted_at:a.menu_attempted_at||null,menu_attempt_note:a.menu_attempt_note||null
    }));
    return out({
      status:"ok",category:"restaurant",query:query||null,city:center.geography_name||city,state_code:resolvedState||null,
      center:{latitude:Number(center.latitude),longitude:Number(center.longitude)},
      points,unmapped,restaurant_count:accounts.length,mapped_count:points.length,
      menu_capture_count:points.filter((p:any)=>!!p.menu).length,
      coverage_note:`${points.length} of ${accounts.length} matching PHG restaurant records are mapped. ${points.filter((p:any)=>!!p.menu).length} currently have a structured captured menu record; missing menu evidence is reported as missing rather than fabricated.`,
      source_note:"Restaurant locations and menu evidence come from PHG account/menu data. Only stored coordinates and stored menu evidence are returned."
    });
  }

  let storesQ=sb.from("accounts")
    .select("id,account_id,account_name,street_address,postal_code,notes,account_types")
    .contains("account_types",[category])
    .ilike("notes",`%City: ${city.toUpperCase()}.%`)
    .order("account_name",{ascending:true})
    .limit(Math.max(1,Math.min(40,Number(b.limit||24))));
  const {data:stores,error:storesErr}=await storesQ;
  if(storesErr)return out({error:storesErr.message},500);

  const ids=(stores||[]).map((x:any)=>x.id);
  let cache:any[]=[];
  if(ids.length){
    const {data:c,error:cacheErr}=await sb.schema("phg").from("retail_geocodes")
      .select("*").in("source_account_id",ids);
    if(!cacheErr&&c)cache=c;
  }
  const byId=new Map(cache.map((x:any)=>[String(x.source_account_id),x]));
  const missing=(stores||[]).filter((x:any)=>!byId.has(String(x.id))).slice(0,12);

  for(let i=0;i<missing.length;i+=4){
    const group=missing.slice(i,i+4);
    const results=await Promise.all(group.map((st:any)=>geocodeOne(st,city,state,center)));
    const good=results.filter(Boolean);
    if(good.length){
      await sb.schema("phg").from("retail_geocodes").upsert(good,{onConflict:"source_account_id"});
      for(const g of good as any[])byId.set(String(g.source_account_id),g);
    }
  }

  const points=(stores||[]).map((st:any)=>{
    const g:any=byId.get(String(st.id));
    if(!g||g.latitude==null||g.longitude==null)return null;
    return {
      id:st.id,account_id:st.account_id,name:st.account_name,address:st.street_address,
      postal_code:st.postal_code,latitude:Number(g.latitude),longitude:Number(g.longitude),
      geocode_score:g.geocode_score==null?null:Number(g.geocode_score),
      geocode_source:g.geocode_source||null,match_address:g.match_address||null,
      distance_miles:miles(Number(center.latitude),Number(center.longitude),Number(g.latitude),Number(g.longitude))
    };
  }).filter(Boolean).sort((a:any,b:any)=>a.distance_miles-b.distance_miles);

  const unmapped=(stores||[]).filter((st:any)=>!byId.has(String(st.id))).map((st:any)=>({
    id:st.id,account_id:st.account_id,name:st.account_name,address:st.street_address,postal_code:st.postal_code
  }));

  return out({
    status:"ok",
    category,
    city:center.geography_name||city,
    state_code:resolvedState||null,
    center:{latitude:Number(center.latitude),longitude:Number(center.longitude)},
    points,
    unmapped,
    store_count:(stores||[]).length,
    mapped_count:points.length,
    coverage_note:unmapped.length
      ? `${points.length} of ${(stores||[]).length} store addresses are currently mapped; unmapped addresses remain listed rather than being placed approximately.`
      : `All ${points.length} returned store addresses are mapped.`,
    source_note:"Retail locations come from PHG account/license data. Map coordinates are cached from address geocoding and are not fabricated when unresolved."
  });
});