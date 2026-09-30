import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});

function safeLike(v:any){
  return String(v||"").trim().replace(/[,*()]/g," ").replace(/\s+/g," ").slice(0,120);
}
function wanted(src:any,key:string){return !src||src[key]!==false;}

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
  const {data:ud,error:ue}=await userClient.auth.getUser(jwt);
  if(ue||!ud?.user)return out({error:"invalid or expired login"},401);

  const sb=createClient(url,service,{auth:{persistSession:false}});
  const b=await req.json().catch(()=>({}));
  const q=safeLike(b.market_query);
  const sources=b.sources||null;
  const result:any={status:"ok",market_query:q,sources:{},summary:[]};

  async function capture(key:string,p:Promise<any>){
    try{
      const x=await p;
      if(x?.error)throw x.error;
      result.sources[key]=x?.data||[];
      return result.sources[key];
    }catch(e:any){
      result.sources[key]=[];
      result.summary.push({source:key,status:"unavailable",note:String(e?.message||e)});
      return [];
    }
  }

  let demographics:any[]=[];
  if(wanted(sources,"demographics")){
    let x=sb.from("v_geography_demographics")
      .select("geography_name,geo_type,state,acs_vintage,total_population,median_household_income,median_age,pop_21_34_pct,pop_35_54_pct,pop_55_plus_pct,households_over_100k_pct,households_under_35k_pct,bachelors_or_higher_pct,accommodation_foodservice_pct,daytime_population_ratio,avg_household_size,family_households_pct,living_alone_pct")
      .limit(12);
    if(q)x=x.ilike("geography_name",`%${q}%`);
    demographics=await capture("demographics",x);
    result.summary.push({source:"demographics",status:"ok",records:demographics.length});
  }

  let venues:any[]=[];
  if(wanted(sources,"venues")||wanted(sources,"websites")||wanted(sources,"cocktail_profiles")){
    let x=sb.from("v_public_venues")
      .select("state_code,venue,city,address,venue_type,rating,reviews,website,lat,lng,match_status,menu_attempted")
      .limit(80);
    if(q){
      const words=q.split(/[,|]/).map((z:string)=>z.trim()).filter(Boolean);
      const term=words[0]||q;
      x=x.or(`city.ilike.%${term}%,venue.ilike.%${term}%`);
    }
    venues=await capture("venues",x);
    result.summary.push({source:"venues",status:"ok",records:venues.length,websites:venues.filter(v=>v.website).length,menu_attempted:venues.filter(v=>v.menu_attempted).length});
  }

  if(wanted(sources,"concepts")){
    const concepts=await capture("concepts",
      sb.from("venue_concepts").select("code,label,axis,family,naics_code,naics_label,description,beverage_notes,sort_order").order("sort_order").limit(250)
    );
    result.summary.push({source:"concepts",status:"ok",records:concepts.length});
  }

  if(wanted(sources,"menu_composition")||wanted(sources,"websites")){
    let x=sb.from("v_menu_composition")
      .select("account_id,account_name,menu_id,menu_format,extraction_confidence,captured_on,cocktail_sections,cocktail_items,spirit_pours,total_items,avg_item_price,tequila_items,tequila_branded,distinct_tequila_brands,tequila_share_pct")
      .order("captured_on",{ascending:false}).limit(120);
    const names=venues.map(v=>v.venue).filter(Boolean).slice(0,40);
    if(names.length)x=x.in("account_name",names);
    const menus=await capture("menu_composition",x);
    result.summary.push({source:"menu_composition",status:"ok",records:menus.length});
  }

  if(wanted(sources,"brands")){
    const brands=await capture("brands",
      sb.from("v_menu_brand_presence")
        .select("brand_name,venues,menu_items,in_cocktails,as_pour,avg_price,first_seen,last_seen")
        .order("venues",{ascending:false}).limit(60)
    );
    result.summary.push({source:"brands",status:"ok",records:brands.length});
  }

  if(wanted(sources,"cocktail_profiles")){
    let x=sb.from("v_venue_cocktail_profile")
      .select("site_key,venue,city,venue_type,income_band,age_band,is_chain_url,drinks,originals,named_drinks,median_price,share_originals,family_mix,spirit_mix")
      .limit(80);
    if(q){
      const term=(q.split(",")[0]||q).trim();
      x=x.or(`city.ilike.%${term}%,venue.ilike.%${term}%`);
    }
    const profiles=await capture("cocktail_profiles",x);
    result.summary.push({source:"cocktail_profiles",status:"ok",records:profiles.length});
  }

  result.generated_at=new Date().toISOString();
  return out(result);
});