
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const MAP = "https://api.firecrawl.dev/v2/map";
const SCRAPE = "https://api.firecrawl.dev/v2/scrape";
const BATCH = 100;
const CONCURRENCY = 25;
const FETCH_CANDIDATES = 260;
const CALL_MS = 45000;

const ELIGIBLE = ["queued","retry","pdf_queue","image_queue","no_items_review","attempted"];
const DRINK_HINTS = [
  "cocktail","cocktails","martini","margarita","beer","wine","spirits",
  "whiskey","whisky","bourbon","rye","tequila","mezcal","vodka","gin","rum",
  "brandy","cognac","aperitif","digestif","happy hour","beverage","drinks"
];

function json(body: unknown, status=200) {
  return new Response(JSON.stringify(body), {status, headers:{"Content-Type":"application/json"}});
}

function eq(g:string|null,e:string) {
  if(!g||!e) return false;
  const a=new TextEncoder().encode(g.trim()), b=new TextEncoder().encode(e.trim());
  if(a.length!==b.length) return false;
  let d=0; for(let i=0;i<a.length;i++) d|=a[i]^b[i];
  return d===0;
}

function stateOf(id:string) {
  if(id.startsWith("ACC-IA-")) return "IA";
  if(id.startsWith("ACC-CO-")) return "CO";
  if(id.startsWith("ACC-NY-")) return "NY";
  return null;
}

async function withTimeout(p:Promise<Response>,ms:number):Promise<Response|null> {
  const t=new Promise<null>(res=>setTimeout(()=>res(null),ms));
  return await Promise.race([p.catch(()=>null),t]);
}

function cleanLine(s:string) {
  return s
    .replace(/!\[[^\]]*\]\([^)]*\)/g," ")
    .replace(/\[([^\]]+)\]\([^)]*\)/g,"$1")
    .replace(/^\s{0,3}#{1,6}\s*/,"")
    .replace(/^\s*[-*+>]\s*/,"")
    .replace(/[*_~]/g,"")
    .replace(/\s+/g," ")
    .trim();
}

function looksHeading(raw:string, clean:string) {
  if(/^\s{0,3}#{1,6}\s+/.test(raw)) return true;
  if(clean.length<4 || clean.length>60) return false;
  if(/[.$]\s*\d/.test(clean)) return false;
  const letters=(clean.match(/[A-Za-z]/g)||[]).length;
  if(letters<3) return false;
  const upp=(clean.match(/[A-Z]/g)||[]).length;
  return upp/letters>0.75;
}

function classify(section:string,item:string) {
  const s=(section+" "+item).toLowerCase();
  if(/cocktail|martini|margarita|old fashioned|spritz|negroni|daiquiri|mojito/.test(s)) return "cocktail";
  if(/beer|lager|ale|ipa|stout|porter|pilsner|cider|seltzer/.test(s)) return "beer";
  if(/wine|cabernet|merlot|pinot|chardonnay|sauvignon|riesling|ros[eé]|prosecco|champagne/.test(s)) return "wine";
  if(/spirit|whisk|bourbon|rye|tequila|mezcal|vodka|gin|rum|scotch|cognac|brandy/.test(s)) return "spirit_pour";
  return "other";
}

function parseMarkdown(md:string) {
  const lines=md.split(/\r?\n/).slice(0,12000);
  const out:any[]=[];
  let section="";
  const money=/\$\s*(\d{1,3}(?:\.\d{1,2})?)/g;
  const tail=/(?:^|\s)(\d{1,3}(?:\.\d{1,2})?)\s*$/;
  for(const raw0 of lines) {
    const raw=raw0.slice(0,500);
    const cl=cleanLine(raw);
    if(!cl) continue;
    if(looksHeading(raw,cl)) { section=cl.slice(0,120); continue; }
    if(cl.length<3 || cl.length>320) continue;

    let price:number|null=null, idx=-1;
    money.lastIndex=0;
    let m:RegExpExecArray|null, last:RegExpExecArray|null=null;
    while((m=money.exec(cl))!==null) last=m;
    if(last) {
      price=Number(last[1]); idx=last.index;
    } else {
      const tm=cl.match(tail);
      if(tm && !/%\s*$/.test(cl)) {
        const v=Number(tm[1]);
        if(v>=2 && v<=300) { price=v; idx=cl.lastIndexOf(tm[1]); }
      }
    }
    if(price===null || !Number.isFinite(price) || price<1 || price>500) continue;

    const name=cl.slice(0,idx).replace(/[.·•|\-–—:\s]+$/g,"").trim();
    if(name.length<2) continue;
    if(/^(hours?|open|close|address|phone|subtotal|total|minimum|maximum|tax|gratuity)/i.test(name)) continue;

    out.push({
      section_name:section||null,
      item_type:classify(section,name),
      item_name:name.slice(0,300),
      item_price:price,
      spirit_brands:null,
      notes:cl.slice(0,300)
    });
    if(out.length>=250) break;
  }

  const dedup=new Map<string,any>();
  for(const x of out) {
    const k=((x.section_name||"")+"|"+x.item_name+"|"+x.item_price).toLowerCase();
    if(!dedup.has(k)) dedup.set(k,x);
  }
  return [...dedup.values()];
}

function scoreMenuUrl(u:string) {
  const l=u.toLowerCase(); let s=0;
  ["drink","cocktail","bar-menu","barmenu","beverage","wine","beer","spirits","happy-hour"].forEach((h,i)=>{if(l.includes(h))s+=120-i});
  if(l.includes("menu")) s+=35;
  if(l.includes(".pdf")) s+=25;
  if(l.split("/").length>9) s-=10;
  return s;
}

function pickMenu(links:string[]) {
  return links.filter(u=>typeof u==="string"&&u.startsWith("http"))
    .map(u=>({u,s:scoreMenuUrl(u)}))
    .filter(x=>x.s>0).sort((a,b)=>b.s-a.s)[0]?.u ?? null;
}

function linksFromHtml(html:string,base:string) {
  const out=new Set<string>(), re=/href\s*=\s*["']([^"'#]+)["']/gi;
  let m:RegExpExecArray|null;
  while((m=re.exec(html))!==null) {
    try {
      const u=new URL(m[1],base);
      if(u.protocol==="http:"||u.protocol==="https:") out.add(u.href);
    } catch {}
    if(out.size>=300) break;
  }
  return [...out];
}

async function freeMenuLink(site:string) {
  try {
    const ctrl=new AbortController();
    const timer=setTimeout(()=>ctrl.abort(),7000);
    const r=await fetch(site,{
      redirect:"follow",signal:ctrl.signal,
      headers:{"User-Agent":"Mozilla/5.0 (compatible; PHGMenuIndexer/1.0)","Accept":"text/html,application/xhtml+xml"}
    });
    clearTimeout(timer);
    if(!r.ok) return null;
    if(!(r.headers.get("content-type")||"").toLowerCase().includes("html")) return null;
    const html=(await r.text()).slice(0,1600000);
    return pickMenu(linksFromHtml(html,r.url||site));
  } catch { return null; }
}

Deno.serve(async(req:Request)=>{
  if(req.method!=="POST") return json({error:"method_not_allowed"},405);

  const url=Deno.env.get("SUPABASE_URL")!;
  const service=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const fc=Deno.env.get("FIRECRAWL_API_KEY");
  const sb=createClient(url,service,{auth:{persistSession:false}});

  const {data:tok}=await sb.from("internal_secrets").select("value").eq("key","ingest_token").single();
  const authorized=eq(req.headers.get("x-ingest-token"),tok?.value??"") ||
                   eq(req.headers.get("x-agent-secret"),Deno.env.get("AGENT_SECRET")??"");
  if(!authorized) return json({error:"unauthorized"},401);
  if(!fc) return json({error:"firecrawl_key_not_configured"},500);

  const now=new Date().toISOString();
  const fields="account_id,account_name,website_url,menu_status,menu_attempt_count,menu_next_retry_at,menu_attempt_note,menu_priority,menu_search_recovery_url";

  // Freshly discovered websites are the highest-yield population, so they get
  // first claim. Recovery work fills the remainder of each batch.
  const {data:fresh,error:freshError}=await sb.from("accounts")
    .select(fields)
    .not("website_url","is",null)
    .eq("menu_source_kind","website")
    .eq("menu_status","queued")
    .or("menu_next_retry_at.is.null,menu_next_retry_at.lte."+now)
    .order("menu_priority",{ascending:true,nullsFirst:false})
    .limit(FETCH_CANDIDATES);

  if(freshError) return json({error:"fresh_query_failed",detail:freshError.message},500);

  const need=Math.max(0,FETCH_CANDIDATES-(fresh?.length??0));
  let recovery:any[]=[];
  if(need>0){
    const {data:rec,error:recError}=await sb.from("accounts")
      .select(fields)
      .not("website_url","is",null)
      .eq("menu_source_kind","website")
      .in("menu_status",["retry","pdf_queue","image_queue","no_items_review","attempted"])
      .or("menu_next_retry_at.is.null,menu_next_retry_at.lte."+now)
      .order("menu_priority",{ascending:true,nullsFirst:false})
      .order("menu_next_retry_at",{ascending:true,nullsFirst:true})
      .limit(need);
    if(recError) return json({error:"recovery_query_failed",detail:recError.message},500);
    recovery=rec??[];
  }

  const candidates=[...(fresh??[]),...recovery];
  if(!candidates.length) return json({status:"complete"});

  const claimed:any[]=[];
  for(const a of candidates) {
    if(claimed.length>=BATCH) break;
    const prev=a.menu_status;
    const {data:lock}=await sb.from("accounts").update({menu_status:"processing"})
      .eq("account_id",a.account_id).eq("menu_status",prev)
      .select("account_id").maybeSingle();
    if(lock?.account_id) claimed.push({...a,previous_status:prev});
  }

  let cursor=0;
  const totals:any={processed:0,extracted:0,retry:0,review:0,free_link:0,map_calls:0,markdown_calls:0,rate_limited:0,provider_blocked:0};
  const fcHeaders={"Content-Type":"application/json",Authorization:"Bearer "+fc.trim()};

  async function record(endpoint:string,credits:number,success=0) {
    await sb.from("menu_api_usage_ledger").insert({
      pipeline:"economy_extract",endpoint,request_count:1,estimated_credits:credits,successful_outputs:success
    });
  }

  async function transition(a:any,status:string,note:string,next:string|null,itemCount:number|null,target:string,http:number|null=null) {
    const attempt=Number(a.menu_attempt_count??0)+1;
    await sb.from("accounts").update({
      menu_status:status,
      menu_attempt_count:attempt,
      menu_last_attempt_at:new Date().toISOString(),
      menu_attempted_at:new Date().toISOString(),
      menu_attempt_note:note.slice(0,200),
      menu_next_retry_at:next,
      menu_finalized_at:status==="extracted"?new Date().toISOString():null
    }).eq("account_id",a.account_id);
    await sb.from("menu_pipeline_events").insert({
      account_id:a.account_id,state_code:stateOf(a.account_id),
      event_type:"economy_menu_extract",from_status:a.previous_status,to_status:status,
      attempt_no:attempt,menu_url:target,http_status:http,item_count:itemCount,detail:note.slice(0,500)
    });
  }

  async function worker() {
    while(true) {
      const i=cursor++; if(i>=claimed.length) return;
      const a=claimed[i]; totals.processed++;
      let target=(a.menu_search_recovery_url || a.website_url) as string;

      try {
        const {data:prior}=await sb.from("staging_menu_extract")
          .select("menu_page_url")
          .eq("account_id",a.account_id)
          .not("menu_page_url","is",null)
          .is("superseded_at",null)
          .order("loaded_at",{ascending:false})
          .limit(8);
        const priorTarget=(prior??[]).map((x:any)=>String(x.menu_page_url??""))
          .filter((u:string)=>u&&u!==a.website_url)
          .map((u:string)=>({u,s:scoreMenuUrl(u)})).sort((x:any,y:any)=>y.s-x.s)
          .find((x:any)=>x.s>0)?.u;
        if(a.menu_search_recovery_url) target=a.menu_search_recovery_url;
        else if(priorTarget) target=priorTarget;
        else {
          const free=await freeMenuLink(a.website_url);
          if(free) { target=free; totals.free_link++; }
          else {
            totals.map_calls++;
            const mr=await withTimeout(fetch(MAP,{
              method:"POST",headers:fcHeaders,
              body:JSON.stringify({url:a.website_url,search:"drinks cocktails beverage wine beer spirits menu pdf",limit:50})
            }),CALL_MS);
            await record("map",1,0);
            if(!mr) {
              const next=new Date(Date.now()+30*60_000).toISOString();
              await transition(a,"retry","map timeout",next,null,target);
              totals.retry++; continue;
            }
            if(mr.status===402) {
              const next=new Date(Date.now()+60*60_000).toISOString();
              await transition(a,"retry","Firecrawl credit block (402)",next,null,target,402);
              totals.provider_blocked++; continue;
            }
            if(mr.status===429) {
              const next=new Date(Date.now()+15*60_000).toISOString();
              await transition(a,"retry","Firecrawl rate limit (429)",next,null,target,429);
              totals.rate_limited++; continue;
            }
            if(mr.ok) {
              const mj=await mr.json().catch(()=>null);
              const links:string[]=(mj?.links??mj?.data?.links??[])
                .map((x:any)=>typeof x==="string"?x:x?.url).filter(Boolean);
              target=pickMenu(links)??target;
            }
          }
        }

        totals.markdown_calls++;
        const body:any={url:target,formats:["markdown"],onlyMainContent:true};
        if(/\.pdf($|\?)/i.test(target)) { body.parsePDF="auto"; body.maxPages=20; }

        const sr=await withTimeout(fetch(SCRAPE,{method:"POST",headers:fcHeaders,body:JSON.stringify(body)}),CALL_MS);
        await record("scrape_markdown",1,0);

        if(!sr) {
          const next=new Date(Date.now()+30*60_000).toISOString();
          await transition(a,"retry","markdown scrape timeout",next,null,target);
          totals.retry++; continue;
        }
        if(sr.status===402) {
          const next=new Date(Date.now()+60*60_000).toISOString();
          await transition(a,"retry","Firecrawl credit block (402)",next,null,target,402);
          totals.provider_blocked++; continue;
        }
        if(sr.status===429) {
          const next=new Date(Date.now()+15*60_000).toISOString();
          await transition(a,"retry","Firecrawl rate limit (429)",next,null,target,429);
          totals.rate_limited++; continue;
        }
        if(!sr.ok) {
          if(sr.status>=500) {
            const next=new Date(Date.now()+30*60_000).toISOString();
            await transition(a,"retry","markdown scrape http "+sr.status,next,null,target,sr.status);
            totals.retry++;
          } else {
            await transition(a,"manual_review","markdown scrape http "+sr.status,null,null,target,sr.status);
            totals.review++;
          }
          continue;
        }

        const sj=await sr.json().catch(()=>null);
        const md=String(sj?.data?.markdown??sj?.markdown??"");
        const items=parseMarkdown(md);
        const lower=md.toLowerCase();
        const hintCount=DRINK_HINTS.filter(h=>lower.includes(h)).length;

        if(items.length>=2 || (items.length===1 && hintCount>=2)) {
          await sb.from("staging_menu_extract").update({superseded_at:new Date().toISOString()})
            .eq("account_id",a.account_id).eq("menu_page_url",target).is("superseded_at",null);

          const rows=items.map((it:any)=>({
            site_url:a.website_url,menu_page_url:target,
            menu_format:/\.pdf($|\?)/i.test(target)?"pdf":"html",
            account_id:a.account_id,item_type:it.item_type,item_name:it.item_name,
            item_price:it.item_price,section_name:it.section_name,spirit_brands:null,notes:it.notes
          }));
          await sb.from("staging_menu_extract").insert(rows);
          await transition(a,"extracted","economy markdown: "+items.length+" items",null,items.length,target);
          totals.extracted++;
          await record("economy_success",0,1);
        } else {
          await sb.from("accounts").update({
            menu_status:"manual_review",
            menu_attempt_note:"economy markdown: no confident drink items",
            menu_last_attempt_at:new Date().toISOString(),
            menu_search_recovery_status:null,
            menu_search_recovery_at:null
          }).eq("account_id",a.account_id);
          await sb.from("menu_pipeline_events").insert({
            account_id:a.account_id,state_code:stateOf(a.account_id),
            event_type:"economy_menu_extract",from_status:a.previous_status,to_status:"manual_review",
            menu_url:target,item_count:items.length,detail:"economy markdown: no confident drink items"
          });
          totals.review++;
        }
      } catch(e) {
        const next=new Date(Date.now()+30*60_000).toISOString();
        await transition(a,"retry","economy pipeline error",next,null,target);
        totals.retry++;
      }
    }
  }

  await Promise.all(Array.from({length:CONCURRENCY},()=>worker()));
  await sb.rpc("refresh_state_stats");
  return json({batch:BATCH,claimed:claimed.length,totals});
});
