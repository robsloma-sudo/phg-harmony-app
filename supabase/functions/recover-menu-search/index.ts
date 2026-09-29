
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const SEARCH="https://api.firecrawl.dev/v2/search";
const BATCH=25;
const CONCURRENCY=10;

const HOSTED=[
  "toasttab.com","toast.site","menufy.com","clover.com","square.site",
  "chownow.com","spoton.com","order.spoton.com"
];

function json(b:unknown,s=200){return new Response(JSON.stringify(b),{status:s,headers:{"Content-Type":"application/json"}})}
function eq(g:string|null,e:string){if(!g||!e)return false;const a=new TextEncoder().encode(g.trim()),b=new TextEncoder().encode(e.trim());if(a.length!==b.length)return false;let d=0;for(let i=0;i<a.length;i++)d|=a[i]^b[i];return d===0}
function host(u:string){try{return new URL(u).hostname.replace(/^www\./,"").toLowerCase()}catch{return""}}
function sameSite(a:string,b:string){const x=host(a),y=host(b);return !!x&&!!y&&(x===y||x.endsWith("."+y)||y.endsWith("."+x))}
function isHosted(u:string){const h=host(u);return HOSTED.some(d=>h===d||h.endsWith("."+d))}
function clean(s:string){return s.toLowerCase().replace(/[^a-z0-9 ]+/g," ").replace(/\s+/g," ").trim()}
function tokens(name:string){return clean(name).split(" ").filter(t=>t.length>=3&&!["the","and","bar","grill","restaurant","cafe","hotel","llc","inc","company"].includes(t))}
function identityScore(name:string,title:string,desc:string,url:string){
  const ts=tokens(name), hay=clean(title+" "+desc+" "+url);
  if(!ts.length)return 0;
  return ts.filter(t=>hay.includes(t)).length/ts.length;
}
function scoreUrl(u:string){
  const l=u.toLowerCase();let s=0;
  ["drink","cocktail","bar-menu","barmenu","beverage","wine","beer","spirits","happy-hour"].forEach((x,i)=>{if(l.includes(x))s+=100-i});
  if(l.includes("menu"))s+=40;
  if(l.includes(".pdf"))s+=25;
  return s;
}
function linksFromHtml(html:string,base:string){
  const out=new Set<string>(),re=/href\s*=\s*["']([^"'#]+)["']/gi;let m:RegExpExecArray|null;
  while((m=re.exec(html))!==null){try{const u=new URL(m[1],base);if(u.protocol==="http:"||u.protocol==="https:")out.add(u.href)}catch{}if(out.size>=250)break}
  return [...out];
}
async function freeMenuTarget(site:string){
  try{
    const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),7000);
    const r=await fetch(site,{redirect:"follow",signal:ctrl.signal,headers:{"User-Agent":"Mozilla/5.0 (compatible; PHGMenuIndexer/1.0)","Accept":"text/html,application/xhtml+xml"}});
    clearTimeout(timer);
    if(!r.ok||!(r.headers.get("content-type")||"").toLowerCase().includes("html"))return null;
    const html=(await r.text()).slice(0,1500000);
    return linksFromHtml(html,r.url||site).filter(u=>sameSite(u,site))
      .map(u=>({u,s:scoreUrl(u)})).filter(x=>x.s>0).sort((a,b)=>b.s-a.s)[0]?.u??null;
  }catch{return null}
}
function parseCity(notes:string|null){const m=(notes??"").match(/City:\s*([^.]+)/i);return m?.[1]?.trim()??""}
function stateOf(id:string){if(id.startsWith("ACC-IA-"))return"Iowa";if(id.startsWith("ACC-CO-"))return"Colorado";if(id.startsWith("ACC-NY-"))return"New York";return""}

Deno.serve(async(req:Request)=>{
  if(req.method!=="POST")return json({error:"method_not_allowed"},405);
  const url=Deno.env.get("SUPABASE_URL")!,service=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,key=Deno.env.get("FIRECRAWL_API_KEY");
  const sb=createClient(url,service,{auth:{persistSession:false}});
  const {data:tok}=await sb.from("internal_secrets").select("value").eq("key","ingest_token").single();
  if(!eq(req.headers.get("x-ingest-token"),tok?.value??""))return json({error:"unauthorized"},401);
  if(!key)return json({error:"firecrawl_key_not_configured"},500);

  const {data:rows,error}=await sb.from("accounts")
    .select("account_id,account_name,website_url,notes,menu_search_recovery_status")
    .eq("menu_status","manual_review")
    .eq("menu_source_kind","website")
    .not("website_url","is",null)
    .or("menu_search_recovery_status.is.null,menu_search_recovery_status.eq.retry")
    .limit(BATCH);
  if(error)return json({error:"query_failed",detail:error.message},500);
  if(!rows?.length)return json({status:"complete"});

  let cursor=0,targetFound=0,noMatch=0,providerBlocked=0,failed=0,searchCalls=0,freeFound=0;

  async function worker(){
    while(true){
      const i=cursor++;if(i>=rows.length)return;
      const a:any=rows[i];
      const {data:claim}=await sb.from("accounts").update({menu_search_recovery_status:"processing"})
        .eq("account_id",a.account_id)
        .or("menu_search_recovery_status.is.null,menu_search_recovery_status.eq.retry")
        .select("account_id").maybeSingle();
      if(!claim?.account_id)continue;

      try{
        let target:string|null=null;

        const {data:prior}=await sb.from("staging_menu_extract").select("menu_page_url")
          .eq("account_id",a.account_id).not("menu_page_url","is",null)
          .order("loaded_at",{ascending:false}).limit(8);
        target=(prior??[]).map((x:any)=>String(x.menu_page_url??""))
          .filter((u:string)=>u&&u!==a.website_url&&sameSite(u,a.website_url))
          .map((u:string)=>({u,s:scoreUrl(u)})).filter((x:any)=>x.s>0)
          .sort((x:any,y:any)=>y.s-x.s)[0]?.u??null;

        if(!target){
          target=await freeMenuTarget(a.website_url);
          if(target)freeFound++;
        }

        if(!target){
          searchCalls++;
          const city=parseCity(a.notes),state=stateOf(a.account_id);
          const q=[a.account_name,city,state,"drinks menu cocktails wine beer spirits"].filter(Boolean).join(" ");
          const sr=await fetch(SEARCH,{
            method:"POST",
            headers:{"Content-Type":"application/json",Authorization:"Bearer "+key.trim()},
            body:JSON.stringify({query:q,limit:3,sources:["web"]})
          });

          if(sr.status===402||sr.status===429){
            providerBlocked++;
            await sb.from("accounts").update({menu_search_recovery_status:"retry",menu_search_recovery_at:new Date().toISOString()}).eq("account_id",a.account_id);
            continue;
          }
          if(!sr.ok){
            failed++;
            await sb.from("accounts").update({menu_search_recovery_status:"retry",menu_search_recovery_at:new Date().toISOString()}).eq("account_id",a.account_id);
            continue;
          }

          const sj=await sr.json().catch(()=>null);
          let items:any[]=[];
          if(Array.isArray(sj?.data?.web))items=sj.data.web;
          else if(Array.isArray(sj?.web))items=sj.web;
          else if(Array.isArray(sj?.data))items=sj.data;

          const candidates=items.map((x:any)=>{
            const u=String(x?.url??""),title=String(x?.title??""),desc=String(x?.description??x?.snippet??"");
            const ident=identityScore(a.account_name,title,desc,u);
            const same=sameSite(u,a.website_url);
            const hosted=isHosted(u);
            const menuScore=scoreUrl(u);
            const score=(same?1:0)+(hosted&&ident>=0.6?0.8:0)+(menuScore>0?0.5:0)+ident;
            return {u,score};
          }).filter((x:any)=>x.u&&x.score>=1.2).sort((x:any,y:any)=>y.score-x.score);
          target=candidates[0]?.u??null;
        }

        if(!target){
          noMatch++;
          await sb.from("accounts").update({
            menu_search_recovery_status:"no_match",
            menu_search_recovery_at:new Date().toISOString()
          }).eq("account_id",a.account_id);
          continue;
        }

        await sb.from("accounts").update({
          menu_status:"queued",
          menu_next_retry_at:new Date().toISOString(),
          menu_search_recovery_status:"target_found",
          menu_search_recovery_at:new Date().toISOString(),
          menu_search_recovery_url:target,
          menu_finalized_at:null
        }).eq("account_id",a.account_id);

        await sb.from("menu_pipeline_events").insert({
          account_id:a.account_id,
          event_type:"menu_target_recovery",
          from_status:"manual_review",
          to_status:"queued",
          menu_url:target,
          detail:"alternate menu target found; queued for economy extraction"
        });
        targetFound++;
      }catch{
        failed++;
        await sb.from("accounts").update({menu_search_recovery_status:"retry",menu_search_recovery_at:new Date().toISOString()}).eq("account_id",a.account_id);
      }
    }
  }

  await Promise.all(Array.from({length:CONCURRENCY},()=>worker()));

  if(searchCalls>0){
    await sb.from("menu_api_usage_ledger").insert({
      pipeline:"menu_target_recovery",
      endpoint:"search",
      request_count:searchCalls,
      estimated_credits:searchCalls*2,
      successful_outputs:targetFound
    });
  }

  return json({processed:rows.length,target_found:targetFound,free_found:freeFound,search_calls:searchCalls,no_match:noMatch,failed,provider_blocked:providerBlocked});
});
