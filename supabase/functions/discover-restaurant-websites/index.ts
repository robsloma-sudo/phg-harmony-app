
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const SEARCH = "https://api.firecrawl.dev/v2/search";
const BATCH = 100;
const CONCURRENCY = 20;
const MAX_RESULTS = 3;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function eq(g: string | null, e: string): boolean {
  if (!g || !e) return false;
  const a = new TextEncoder().encode(g.trim()), b = new TextEncoder().encode(e.trim());
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a[i] ^ b[i];
  return d === 0;
}

const BLOCKED = [
  "facebook.com","instagram.com","yelp.com","tripadvisor.com","google.com",
  "mapquest.com","foursquare.com","doordash.com","ubereats.com","grubhub.com"
];

function clean(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9 ]+/g," ").replace(/\s+/g," ").trim();
}

function significantTokens(name: string) {
  return clean(name).split(" ").filter(t => t.length >= 3 && !["the","and","bar","grill","restaurant","cafe","hotel","llc","inc"].includes(t));
}

function domainOf(u: string) {
  try { return new URL(u).hostname.replace(/^www\./,"").toLowerCase(); } catch { return ""; }
}

function scoreCandidate(name: string, city: string, address: string, url: string, title: string, desc: string) {
  const domain = domainOf(url);
  if (!domain) return 0;
  if (BLOCKED.some(d => domain === d || domain.endsWith("." + d))) return 0;

  const hay = clean([url,title,desc].filter(Boolean).join(" "));
  const tokens = significantTokens(name);
  const hits = tokens.filter(t => hay.includes(t)).length;
  const nameRatio = tokens.length ? hits / tokens.length : 0;
  let score = 0.60 * nameRatio;

  const cityClean = clean(city);
  if (cityClean && hay.includes(cityClean)) score += 0.18;

  const streetNum = (address.match(/\b\d{1,6}\b/) || [])[0];
  if (streetNum && hay.includes(streetNum)) score += 0.08;

  const dclean = clean(domain.replace(/\.[a-z]{2,}$/,"").replace(/[.-]/g," "));
  if (tokens.some(t => dclean.includes(t))) score += 0.14;

  return Math.min(1, score);
}

function parseCity(notes: string | null) {
  const m = (notes ?? "").match(/City:\s*([^.]+)/i);
  return m?.[1]?.trim() ?? "";
}

function stateOf(id: string) {
  if (id.startsWith("ACC-IA-")) return "Iowa";
  if (id.startsWith("ACC-CO-")) return "Colorado";
  if (id.startsWith("ACC-NY-")) return "New York";
  return "";
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({error:"method_not_allowed"},405);

  const url = Deno.env.get("SUPABASE_URL")!;
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const key = Deno.env.get("FIRECRAWL_API_KEY");
  const sb = createClient(url, service, {auth:{persistSession:false}});

  const { data: tok } = await sb.from("internal_secrets").select("value").eq("key","ingest_token").single();
  if (!eq(req.headers.get("x-ingest-token"), tok?.value ?? "")) return json({error:"unauthorized"},401);
  if (!key) return json({error:"firecrawl_key_not_configured"},500);

  const { data: rows, error } = await sb.from("accounts")
    .select("account_id,account_name,street_address,postal_code,notes,website_discovery_status")
    .eq("account_status","active")
    .contains("account_types",["on_premise_spirits"])
    .or("website_url.is.null,menu_status.eq.social_hold")
    .or("website_discovery_status.is.null,website_discovery_status.eq.retry")
    .limit(BATCH);

  if (error) return json({error:"query_failed",detail:error.message},500);
  if (!rows?.length) return json({status:"complete"});

  let found=0, review=0, noMatch=0, providerBlocked=0;

  let cursor = 0;
  async function worker() {
    while (true) {
      const i = cursor++;
      if (i >= rows.length) return;
      const a:any = rows[i];
    const claim = await sb.from("accounts")
      .update({website_discovery_status:"processing"})
      .eq("account_id",a.account_id)
      .or("website_discovery_status.is.null,website_discovery_status.eq.retry")
      .select("account_id").maybeSingle();
    if (!claim.data?.account_id) return;

    const city = parseCity(a.notes);
    const state = stateOf(a.account_id);
    const q = [a.account_name,a.street_address,city,state,"official website"].filter(Boolean).join(" ");

    try {
      const rr = await fetch(SEARCH,{
        method:"POST",
        headers:{"Content-Type":"application/json",Authorization:`Bearer ${key.trim()}`},
        body:JSON.stringify({query:q,limit:MAX_RESULTS,sources:["web"]})
      });

      if (rr.status===402 || rr.status===429) {
        providerBlocked++;
        await sb.from("accounts").update({
          website_discovery_status:"retry",
          website_discovery_attempted_at:new Date().toISOString()
        }).eq("account_id",a.account_id);
        return;
      }

      if (!rr.ok) {
        await sb.from("accounts").update({
          website_discovery_status:"retry",
          website_discovery_attempted_at:new Date().toISOString()
        }).eq("account_id",a.account_id);
        return;
      }

      const sj = await rr.json().catch(()=>null);
      let items:any[] = [];
      if (Array.isArray(sj?.data?.web)) items = sj.data.web;
      else if (Array.isArray(sj?.web)) items = sj.web;
      else if (Array.isArray(sj?.data)) items = sj.data;

      const scored = items
        .map((x:any) => ({
          url:String(x?.url ?? ""),
          title:String(x?.title ?? ""),
          description:String(x?.description ?? x?.snippet ?? ""),
          score:scoreCandidate(a.account_name,city,a.street_address ?? "",String(x?.url ?? ""),String(x?.title ?? ""),String(x?.description ?? x?.snippet ?? ""))
        }))
        .filter((x:any)=>x.url && x.score>0)
        .sort((x:any,y:any)=>y.score-x.score);

      if (scored.length) {
        await sb.from("website_discovery_candidates").insert(scored.map((x:any,i:number)=>({
          account_id:a.account_id,
          search_query:q,
          candidate_url:x.url,
          candidate_title:x.title,
          candidate_description:x.description,
          score:x.score,
          selected:false
        })));
      }

      const best = scored[0];
      const second = scored[1];
      const margin = best && second ? best.score-second.score : best ? best.score : 0;

      if (best && best.score>=0.78 && margin>=0.10) {
        await sb.from("accounts").update({
          website_url:best.url,
          website_discovery_status:"matched",
          website_discovery_attempted_at:new Date().toISOString(),
          website_discovery_score:best.score,
          website_discovery_source:"firecrawl_search"
        }).eq("account_id",a.account_id);

        await sb.from("website_discovery_candidates").update({selected:true})
          .eq("account_id",a.account_id).eq("candidate_url",best.url);
        found++;
      } else if (best) {
        await sb.from("accounts").update({
          website_discovery_status:"review",
          website_discovery_attempted_at:new Date().toISOString(),
          website_discovery_score:best.score,
          website_discovery_source:"firecrawl_search"
        }).eq("account_id",a.account_id);
        review++;
      } else {
        await sb.from("accounts").update({
          website_discovery_status:"no_match",
          website_discovery_attempted_at:new Date().toISOString(),
          website_discovery_source:"firecrawl_search"
        }).eq("account_id",a.account_id);
        noMatch++;
      }
    } catch {
      await sb.from("accounts").update({
        website_discovery_status:"retry",
        website_discovery_attempted_at:new Date().toISOString()
      }).eq("account_id",a.account_id);
    }
    }
  }

  await Promise.all(Array.from({length:CONCURRENCY},()=>worker()));

  await sb.from("menu_api_usage_ledger").insert({
    pipeline:"website_discovery",
    endpoint:"search",
    request_count:rows.length,
    estimated_credits:rows.length*2,
    successful_outputs:found
  });

  return json({processed:rows.length,found,review,no_match:noMatch,provider_blocked:providerBlocked});
});
