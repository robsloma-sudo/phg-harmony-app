
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const BUCKET="phg-menu-assets";

// ---------------------------------------------------------------------------
// HTML screenshot worker settings (v4). PDF actions below are unchanged from v3.
// ---------------------------------------------------------------------------
const HTML_STRATEGIES=["firecrawl_screenshot_after_download_check","railway_external_html_screenshot"];
// Global safety net: any html claim still 'processing' after this long is reset.
// Observed renders take 3-6 s; worker Playwright timeouts are 30 s per step.
const HTML_STALE_MS=10*60_000;
// A worker polls claim_html only after finishing its previous job (strictly
// sequential in the logs). A claim of its own that is older than this when it
// polls again was abandoned (no complete_html / fail_html ever arrived).
const HTML_ABANDON_MS=180_000;
// Circuit breaker: a claimer that has abandoned this many claims inside the
// window (or holds this many open claims) receives {status:"empty"} instead of
// a job, so a worker with a dead browser stops burning the queue.
const HTML_BREAKER_THRESHOLD=3;
const HTML_BREAKER_WINDOW_MS=30*60_000;
// Size cap: bucket file_size_limit is 52,428,800 bytes; keep headroom for the
// 256 MB Edge Function memory limit (body + upload copy). Resolution is never
// reduced; observed max JPEG is 6.6 MB.
const HTML_MAX_BYTES=40_000_000;
// Pages whose render crashed Chromium ("Target crashed" while loading or
// screenshotting that page) are held back so they cannot kill the next replica.
const HTML_CRASH_QUARANTINE_MIN=24*60;
const CRASH_RE=/Target crashed/i;
// A worker whose browser is already dead fails EVERY page it takes with errors
// like "Browser.new_page: Target page, context or browser has been closed". Those
// pages are innocent: they get the normal short backoff, and the failure counts
// against the worker (circuit breaker below), not against the page.
const DEAD_BROWSER_RE=/new_page|new_context|browser has been closed|Browser closed|browser has disconnected|context or browser has been closed/i;
const DEAD_BROWSER_PREFIX="worker_browser_dead";
const STALE_PREFIX="stale external html claim reset";
const ABANDON_PREFIX="abandoned external html claim reset";

function json(b:unknown,s=200){
  return new Response(JSON.stringify(b),{status:s,headers:{"Content-Type":"application/json"}});
}
function eq(g:string|null,e:string){
  if(!g||!e)return false;
  const a=new TextEncoder().encode(g.trim()),b=new TextEncoder().encode(e.trim());
  if(a.length!==b.length)return false;
  let d=0;for(let i=0;i<a.length;i++)d|=a[i]^b[i];
  return d===0;
}
function backoffMinutes(attempt:number){
  return attempt>=6?120:attempt>=3?30:10;
}
function workerIdentity(req:Request){
  const raw=req.headers.get("x-worker-id")||req.headers.get("x-real-ip")||
    req.headers.get("cf-connecting-ip")||"unknown";
  return raw.trim().replace(/[^A-Za-z0-9.:-]/g,"-").slice(0,64)||"unknown";
}
// Claim ledger kept in the previously unused column render_last_error while a
// page is processing:  html_claim|by=<identity>|at=<iso>|attempt=<n>
function claimNote(by:string,at:string,attempt:number){
  return "html_claim|by="+by+"|at="+at+"|attempt="+attempt;
}
function parseClaimNote(s:string|null|undefined){
  if(!s||!s.startsWith("html_claim|"))return null;
  const out:Record<string,string>={};
  for(const part of s.split("|").slice(1)){
    const i=part.indexOf("=");if(i>0)out[part.slice(0,i)]=part.slice(i+1);
  }
  return {by:out.by??"unknown",at:out.at??"",attempt:Number(out.attempt??"0")};
}

// Returns a claimed row to the retry queue with the same backoff schedule as
// fail_html. Never touches a row that is already 'ready'.
async function recordHtmlFailure(sb:any,pageId:number,attemptHint:number|null,err:string,extraMinutes?:number){
  const {data:row}=await sb.from("menu_visual_pages")
    .select("id,render_attempt_count,render_status").eq("id",pageId).maybeSingle();
  if(!row?.id||row.render_status==="ready")return null;
  const attempt=Number(row.render_attempt_count??attemptHint??1);
  const minutes=extraMinutes??backoffMinutes(attempt);
  const {error}=await sb.from("menu_visual_pages").update({
    render_status:"retry",
    render_error:err.slice(0,500),
    render_next_retry_at:new Date(Date.now()+minutes*60_000).toISOString(),
    updated_at:new Date().toISOString()
  }).eq("id",pageId).neq("render_status","ready");
  if(error)console.error("html_failure_record_failed",pageId,error.message);
  return minutes;
}

// Resets html claims that are stale (any claimer, older than HTML_STALE_MS) or
// abandoned (claimed by `me`, older than HTML_ABANDON_MS). Each row gets its own
// error text with the original claim time, claimer and attempt, plus backoff.
// Returns the number of open claims `me` still holds after the sweep.
async function sweepHtmlClaims(sb:any,me:string){
  const nowMs=Date.now();
  const {data:open,error}=await sb.from("menu_visual_pages")
    .select("id,render_attempt_count,render_last_error,updated_at")
    .eq("render_status","processing")
    .in("render_strategy",HTML_STRATEGIES)
    .order("updated_at",{ascending:true})
    .limit(500);
  if(error){console.error("html_sweep_query_failed",error.message);return 0;}
  let mineOpen=0,resets=0;
  for(const r of (open??[]) as any[]){
    const note=parseClaimNote(r.render_last_error);
    const claimedAt=note?.at||r.updated_at;
    const claimedMs=Date.parse(claimedAt);
    const ageMs=Number.isFinite(claimedMs)?nowMs-claimedMs:Number.POSITIVE_INFINITY;
    const updMs=Date.parse(r.updated_at);
    const rowAgeMs=Number.isFinite(updMs)?nowMs-updMs:Number.POSITIVE_INFINITY;
    const by=note?.by??"unknown";
    const attempt=Number(r.render_attempt_count??note?.attempt??1);
    let prefix:string|null=null;
    if(rowAgeMs>HTML_STALE_MS)prefix=STALE_PREFIX;
    else if(by===me&&ageMs>HTML_ABANDON_MS)prefix=ABANDON_PREFIX;
    if(!prefix){if(by===me)mineOpen++;continue;}
    if(resets>=50)continue; // bound per-request work; the next poll continues
    resets++;
    const minutes=backoffMinutes(attempt);
    const err=prefix+"|by="+by+"|claimed_at="+claimedAt+"|attempt="+attempt+
      "|age_s="+Math.round(ageMs/1000)+"|detected_by="+me;
    // Conditional on still being the same stale claim: a late complete_html
    // (status ready) or a fresh re-claim (newer updated_at) wins.
    const {error:uErr}=await sb.from("menu_visual_pages").update({
      render_status:"retry",
      render_error:err.slice(0,500),
      render_next_retry_at:new Date(nowMs+minutes*60_000).toISOString(),
      updated_at:new Date().toISOString()
    }).eq("id",r.id).eq("render_status","processing").lte("updated_at",r.updated_at);
    if(uErr)console.error("html_sweep_update_failed",r.id,uErr.message);
    else console.warn(prefix,JSON.stringify({page_id:r.id,by,claimed_at:claimedAt,attempt,age_s:Math.round(ageMs/1000),detected_by:me}));
  }
  return mineOpen;
}

async function recentAbandonsBy(sb:any,me:string){
  const since=new Date(Date.now()-HTML_BREAKER_WINDOW_MS).toISOString();
  const {data,error}=await sb.from("menu_visual_pages")
    .select("id,render_error")
    .eq("render_status","retry")
    .in("render_strategy",HTML_STRATEGIES)
    .gte("updated_at",since)
    .or('render_error.like."'+ABANDON_PREFIX+'*",render_error.like."'+DEAD_BROWSER_PREFIX+'*"')
    .limit(200);
  if(error){console.error("html_breaker_query_failed",error.message);return 0;}
  const tag="|by="+me+"|";
  return (data??[]).filter((r:any)=>String(r.render_error??"").includes(tag)).length;
}

Deno.serve(async(req:Request)=>{
  if(req.method!=="POST")return json({error:"method_not_allowed"},405);

  const sb=createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    {auth:{persistSession:false}}
  );

  const {data:secrets}=await sb.from("internal_secrets")
    .select("key,value").in("key",["menu_render_worker_token","menu_html_worker_token"]);
  const supplied=req.headers.get("x-worker-token");
  const authorized=(secrets??[]).some((x:any)=>eq(supplied,x.value??""));
  if(!authorized)return json({error:"unauthorized"},401);

  const u=new URL(req.url);
  const action=u.searchParams.get("action")||"claim";

  // ===================== PDF actions: unchanged from v3 =====================
  if(action==="claim"){
    const now=new Date().toISOString();

    await sb.from("menu_visual_pages").update({
      render_status:"retry",
      render_next_retry_at:null,
      render_error:"stale external render claim reset",
      updated_at:now
    }).eq("render_status","processing")
      .in("render_strategy",["render_downloaded_pdf_page_locally","railway_external_pdf_render"])
      .lt("updated_at",new Date(Date.now()-20*60_000).toISOString());

    // Eligible retries are serviced before fresh pages so older/problematic
    // documents cannot starve behind a continuously growing discovery queue.
    let pages:any[]=[];
    const retryQ=await sb.from("menu_visual_pages")
      .select("id,menu_visual_document_id,page_number,render_status,render_attempt_count")
      .in("render_strategy",["render_downloaded_pdf_page_locally","railway_external_pdf_render"])
      .eq("render_status","retry")
      .or("render_next_retry_at.is.null,render_next_retry_at.lte."+now)
      .order("render_attempt_count",{ascending:true})
      .order("updated_at",{ascending:true})
      .order("id",{ascending:true})
      .limit(12);

    if(retryQ.error)return json({error:"retry_queue_query_failed",detail:retryQ.error.message},500);
    pages=retryQ.data??[];

    if(!pages.length){
      const freshQ=await sb.from("menu_visual_pages")
        .select("id,menu_visual_document_id,page_number,render_status,render_attempt_count")
        .in("render_strategy",["render_downloaded_pdf_page_locally","railway_external_pdf_render"])
        .eq("render_status","pending")
        .order("id",{ascending:true})
        .limit(12);
      if(freshQ.error)return json({error:"fresh_queue_query_failed",detail:freshQ.error.message},500);
      pages=freshQ.data??[];
    }

    if(!pages.length)return json({status:"empty"});

    for(const p of pages as any[]){
      const attempt=Number(p.render_attempt_count??0)+1;
      const {data:claim}=await sb.from("menu_visual_pages").update({
        render_status:"processing",
        render_strategy:"railway_external_pdf_render",
        render_attempt_count:attempt,
        render_error:null,
        updated_at:new Date().toISOString()
      }).eq("id",p.id).eq("render_status",p.render_status).select("id").maybeSingle();
      if(!claim?.id)continue;

      const {data:doc,error:docErr}=await sb.from("menu_visual_documents")
        .select("id,storage_bucket,storage_path,page_count,page_count_exact")
        .eq("id",p.menu_visual_document_id).maybeSingle();

      if(docErr||!doc?.storage_bucket||!doc?.storage_path){
        await sb.from("menu_visual_pages").update({
          render_status:"retry",
          render_error:"visual document missing storage source",
          render_next_retry_at:new Date(Date.now()+30*60_000).toISOString(),
          updated_at:new Date().toISOString()
        }).eq("id",p.id);
        continue;
      }

      const {data:signed,error:signErr}=await sb.storage.from(doc.storage_bucket)
        .createSignedUrl(doc.storage_path,900);
      if(signErr||!signed?.signedUrl){
        await sb.from("menu_visual_pages").update({
          render_status:"retry",
          render_error:"signed source URL failed: "+(signErr?.message||"unknown"),
          render_next_retry_at:new Date(Date.now()+30*60_000).toISOString(),
          updated_at:new Date().toISOString()
        }).eq("id",p.id);
        continue;
      }

      return json({
        status:"job",
        page_id:p.id,
        document_id:doc.id,
        page_number:p.page_number,
        page_count:doc.page_count,
        pdf_url:signed.signedUrl,
        target_width:1400,
        jpeg_quality:88,
        attempt
      });
    }

    return json({status:"contended"});
  }

  if(action==="complete"){
    const pageId=Number(u.searchParams.get("page_id"));
    const width=Number(u.searchParams.get("width"));
    const height=Number(u.searchParams.get("height"));
    if(!Number.isFinite(pageId)||pageId<=0)return json({error:"invalid_page_id"},400);

    const len=Number(req.headers.get("content-length")||"0");
    if(len>12_000_000)return json({error:"image_too_large"},413);

    const {data:page,error:pageErr}=await sb.from("menu_visual_pages")
      .select("id,menu_visual_document_id,page_number,render_attempt_count")
      .eq("id",pageId).maybeSingle();
    if(pageErr||!page?.id)return json({error:"page_not_found"},404);

    const bytes=new Uint8Array(await req.arrayBuffer());
    if(!bytes.length)return json({error:"empty_image"},400);

    const path="document/"+page.menu_visual_document_id+"/page-"+String(page.page_number).padStart(3,"0")+".jpg";
    const up=await sb.storage.from(BUCKET).upload(path,bytes,{
      contentType:"image/jpeg",
      upsert:true
    });
    if(up.error)return json({error:"upload_failed",detail:up.error.message},500);

    await sb.from("menu_visual_pages").update({
      page_image_bucket:BUCKET,
      page_image_path:path,
      render_status:"ready",
      capture_method:"railway_pymupdf_jpeg",
      render_strategy:"railway_external_pdf_render",
      width:Number.isFinite(width)?Math.round(width):null,
      height:Number.isFinite(height)?Math.round(height):null,
      render_next_retry_at:null,
      render_error:null,
      updated_at:new Date().toISOString()
    }).eq("id",pageId);

    await sb.from("menu_visual_documents").update({
      page_render_status:"pending",
      page_render_error:null,
      updated_at:new Date().toISOString()
    }).eq("id",page.menu_visual_document_id);

    const {count:remaining}=await sb.from("menu_visual_pages")
      .select("id",{count:"exact",head:true})
      .eq("menu_visual_document_id",page.menu_visual_document_id)
      .neq("render_status","ready");

    if((remaining??0)===0){
      await sb.from("menu_visual_documents").update({
        page_render_status:"ready",
        page_rendered_at:new Date().toISOString(),
        page_render_next_retry_at:null,
        page_render_error:null,
        updated_at:new Date().toISOString()
      }).eq("id",page.menu_visual_document_id);
    }

    return json({
      status:"ready",
      page_id:pageId,
      document_id:page.menu_visual_document_id,
      remaining:remaining??0,
      bytes:bytes.length
    });
  }

  if(action==="fail"){
    let body:any={};
    try{body=await req.json();}catch{}
    const pageId=Number(body.page_id);
    if(!Number.isFinite(pageId)||pageId<=0)return json({error:"invalid_page_id"},400);

    const {data:page}=await sb.from("menu_visual_pages")
      .select("id,menu_visual_document_id,render_attempt_count")
      .eq("id",pageId).maybeSingle();
    if(!page?.id)return json({error:"page_not_found"},404);

    const attempt=Number(page.render_attempt_count??1);
    const minutes=attempt>=6?120:attempt>=3?30:10;
    const err=String(body.error||"external render failed").slice(0,500);

    await sb.from("menu_visual_pages").update({
      render_status:"retry",
      render_error:err,
      render_next_retry_at:new Date(Date.now()+minutes*60_000).toISOString(),
      updated_at:new Date().toISOString()
    }).eq("id",pageId);

    await sb.from("menu_visual_documents").update({
      page_render_status:"pending",
      page_render_error:err,
      updated_at:new Date().toISOString()
    }).eq("id",page.menu_visual_document_id);

    return json({status:"retry",page_id:pageId,retry_minutes:minutes});
  }
  // =================== end of PDF actions (unchanged) =======================


  if(action==="claim_html"){
    const me=workerIdentity(req);
    const mineOpen=await sweepHtmlClaims(sb,me);

    // Circuit breaker: a claimer that keeps claiming without ever completing or
    // failing (dead browser) gets no more jobs until its abandons age out.
    const abandons=await recentAbandonsBy(sb,me);
    if(mineOpen>=HTML_BREAKER_THRESHOLD||abandons>=HTML_BREAKER_THRESHOLD){
      console.error("html_worker_breaker_open",JSON.stringify({worker:me,open_claims:mineOpen,abandons_30m:abandons}));
      return json({status:"empty",reason:"worker_breaker_open",open_claims:mineOpen,abandoned_recently:abandons});
    }

    const now=new Date().toISOString();
    const {data:pages,error}=await sb.from("menu_visual_pages")
      .select("id,menu_visual_document_id,page_number,render_status,render_attempt_count")
      .in("render_strategy",HTML_STRATEGIES)
      .in("render_status",["pending","retry"])
      .or("render_next_retry_at.is.null,render_next_retry_at.lte."+now)
      .order("render_attempt_count",{ascending:true}).order("id",{ascending:true}).limit(12);
    if(error)return json({error:"html_queue_query_failed",detail:error.message},500);
    if(!pages?.length)return json({status:"empty"});

    for(const p of pages as any[]){
      const attempt=Number(p.render_attempt_count??0)+1;
      const claimedAt=new Date().toISOString();
      const {data:claim}=await sb.from("menu_visual_pages").update({
        render_status:"processing",render_strategy:"railway_external_html_screenshot",
        render_attempt_count:attempt,render_error:null,
        render_last_error:claimNote(me,claimedAt,attempt),
        updated_at:claimedAt
      }).eq("id",p.id).eq("render_status",p.render_status).select("id").maybeSingle();
      if(!claim?.id)continue;
      const {data:doc}=await sb.from("menu_visual_documents")
        .select("id,original_menu_url").eq("id",p.menu_visual_document_id).maybeSingle();
      if(!doc?.original_menu_url){
        await sb.from("menu_visual_pages").update({
          render_status:"retry",render_error:"html source URL missing",
          render_next_retry_at:new Date(Date.now()+30*60_000).toISOString(),updated_at:new Date().toISOString()
        }).eq("id",p.id); continue;
      }
      return json({status:"job",page_id:p.id,document_id:doc.id,page_number:p.page_number,
        source_url:doc.original_menu_url,target_width:1400,jpeg_quality:85,attempt});
    }
    return json({status:"contended"});
  }

  if(action==="complete_html"){
    const pageId=Number(u.searchParams.get("page_id"));
    const width=Number(u.searchParams.get("width")),height=Number(u.searchParams.get("height"));
    if(!Number.isFinite(pageId)||pageId<=0)return json({error:"invalid_page_id"},400);
    const {data:page}=await sb.from("menu_visual_pages")
      .select("id,menu_visual_document_id,page_number,render_attempt_count").eq("id",pageId).maybeSingle();
    if(!page?.id)return json({error:"page_not_found"},404);
    const attemptHint=Number(page.render_attempt_count??1);

    // Reject oversized bodies before buffering them (declared length).
    const declared=Number(req.headers.get("content-length")||"0");
    if(Number.isFinite(declared)&&declared>HTML_MAX_BYTES){
      await recordHtmlFailure(sb,pageId,attemptHint,"complete_html: image_too_large "+declared+" bytes");
      return json({error:"image_too_large"},413);
    }

    let bytes:Uint8Array;
    try{
      bytes=new Uint8Array(await req.arrayBuffer());
    }catch(e){
      await recordHtmlFailure(sb,pageId,attemptHint,"complete_html: body_read_failed "+String((e as any)?.message??e));
      return json({error:"body_read_failed"},400);
    }
    if(!bytes.length){
      await recordHtmlFailure(sb,pageId,attemptHint,"complete_html: empty_image");
      return json({error:"empty_image"},400);
    }
    if(bytes.length>HTML_MAX_BYTES){
      await recordHtmlFailure(sb,pageId,attemptHint,"complete_html: image_too_large "+bytes.length+" bytes");
      return json({error:"image_too_large"},413);
    }

    const path="document/"+page.menu_visual_document_id+"/page-"+String(page.page_number).padStart(3,"0")+".jpg";
    let up:any;
    try{
      up=await sb.storage.from(BUCKET).upload(path,bytes,{contentType:"image/jpeg",upsert:true});
    }catch(e){
      up={error:{message:String((e as any)?.message??e)}};
    }
    if(up.error){
      await recordHtmlFailure(sb,pageId,attemptHint,"complete_html: upload_failed "+String(up.error.message??"unknown"));
      return json({error:"upload_failed",detail:up.error.message},500);
    }

    // A late complete for a row the sweep already reset is still accepted: the
    // image is valid and uploaded, so the row becomes ready.
    const readyPatch={
      page_image_bucket:BUCKET,page_image_path:path,render_status:"ready",
      capture_method:"railway_playwright_screenshot",render_strategy:"railway_external_html_screenshot",
      width:Number.isFinite(width)?Math.round(width):null,height:Number.isFinite(height)?Math.round(height):null,
      render_next_retry_at:null,render_error:null,updated_at:new Date().toISOString()
    };
    let upd=await sb.from("menu_visual_pages").update(readyPatch).eq("id",pageId);
    if(upd.error){
      upd=await sb.from("menu_visual_pages").update({...readyPatch,updated_at:new Date().toISOString()}).eq("id",pageId);
    }
    if(upd.error){
      // Image is in storage but the row could not be marked ready; leave it for
      // the sweep and tell the worker (same shape as other 500s).
      console.error("complete_html_page_update_failed",pageId,upd.error.message);
      return json({error:"page_update_failed",detail:upd.error.message},500);
    }
    await sb.from("menu_visual_documents").update({
      acquisition_status:"ready",screenshot_fallback_required:false,page_render_status:"ready",
      page_rendered_at:new Date().toISOString(),page_render_error:null,updated_at:new Date().toISOString()
    }).eq("id",page.menu_visual_document_id);
    return json({status:"ready",page_id:pageId,document_id:page.menu_visual_document_id,bytes:bytes.length});
  }

  if(action==="fail_html"){
    let body:any={}; try{body=await req.json();}catch{}
    const pageId=Number(body.page_id);
    const {data:page}=await sb.from("menu_visual_pages").select("id,render_attempt_count").eq("id",pageId).maybeSingle();
    if(!page?.id)return json({error:"page_not_found"},404);
    const attempt=Number(page.render_attempt_count??1);
    let minutes=backoffMinutes(attempt);
    let err=String(body.error||"external html render failed");
    if(!CRASH_RE.test(err)&&DEAD_BROWSER_RE.test(err)){
      // the worker's browser is gone; not this page's fault
      const who=workerIdentity(req);
      err=DEAD_BROWSER_PREFIX+"|by="+who+"|: "+err;
      console.error("html_worker_browser_dead",JSON.stringify({page_id:pageId,worker:who,attempt}));
    }else if(CRASH_RE.test(err)){
      // This page crashed the browser; hold it back so it cannot immediately
      // kill another replica. The original error text is kept after the prefix.
      minutes=Math.max(minutes,HTML_CRASH_QUARANTINE_MIN);
      err="browser_crash_quarantine: "+err;
      console.error("html_browser_crash",JSON.stringify({page_id:pageId,worker:workerIdentity(req),attempt}));
    }
    await sb.from("menu_visual_pages").update({
      render_status:"retry",render_error:err.slice(0,500),
      render_next_retry_at:new Date(Date.now()+minutes*60_000).toISOString(),updated_at:new Date().toISOString()
    }).eq("id",pageId);
    return json({status:"retry",page_id:pageId,retry_minutes:minutes});
  }

  return json({error:"unknown_action"},400);
});
