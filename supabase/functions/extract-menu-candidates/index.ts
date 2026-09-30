import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import {createClient} from 'jsr:@supabase/supabase-js@2';
import {parseHTML} from 'npm:linkedom@0.18.12/worker';
import {htmlText,parseMenu} from './parser.mjs';
/* v5 (2026-09-30, Rob: Firecrawl credits loaded - enable what was held back):
   - allow_paid:true runs in its own lease lane (candidate_extraction_paid) so it never competes with the free cron 13.
   - In paid mode Firecrawl is also used for pages that refused our fetcher (source_http_401/403/429); unsafe URLs never.
   - In paid mode, rows parked in 'review' only because of 401/403/429 can be claimed (dispatcher:
     phg_dispatch_paid_blocked_menus, cron job 'gtt-extract-paid-blocked'); known-blocked rows skip the direct fetch.
   - Firecrawl 4xx answers are final ('review'), so a page is paid for at most once per 4xx.
   v4 source is kept by Supabase (version 4); only the lines above changed. */
const VERSION='candidate-recovery-5';
const BLOCKED=/source_http_(401|403|429)/;
const json=(b,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{'Content-Type':'application/json'}});
function equal(a,b){if(!a||!b)return false;const x=new TextEncoder().encode(a.trim()),y=new TextEncoder().encode(b.trim());if(x.length!==y.length)return false;let d=0;for(let i=0;i<x.length;i++)d|=x[i]^y[i];return d===0;}
function safeURL(raw){const u=new URL(raw);const h=u.hostname.toLowerCase();if(!['https:','http:'].includes(u.protocol)||u.username||u.password||!h.includes('.')||/^\d+\.\d+\.\d+\.\d+$/.test(h)||h.includes(':')||/(^|\.)(localhost|internal|local)$/.test(h))throw Error('unsafe_source_url');return u.href;}
async function directText(raw){
 const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),18000);
 try{let target=safeURL(raw),r;
  for(let i=0;i<5;i++){r=await fetch(target,{redirect:'manual',signal:ctrl.signal,headers:{'User-Agent':'Mozilla/5.0 (compatible; PHGMenuIndexer/2.0)','Accept':'text/html,application/xhtml+xml,text/plain'}});if(r.status>=300&&r.status<400&&r.headers.get('location')){const next=safeURL(new URL(r.headers.get('location'),target).href);await r.body?.cancel();target=next;continue;}break;}
  if(!r?.ok)throw Error('source_http_'+(r?.status||0));
  const mime=(r.headers.get('content-type')||'').toLowerCase();if(!mime.includes('html')&&!mime.startsWith('text/plain')){await r.body?.cancel();throw Error('needs_document_text_or_vision');}
  const reader=r.body.getReader(),chunks=[];let total=0;
  while(true){const x=await reader.read();if(x.done)break;total+=x.value.length;if(total>4000000){await reader.cancel();throw Error('source_too_large_for_edge');}chunks.push(x.value);}
  const bytes=new Uint8Array(total);let off=0;for(const x of chunks){bytes.set(x,off);off+=x.length;}
  const rawText=new TextDecoder().decode(bytes);const text=mime.includes('html')?htmlText(rawText,parseHTML):rawText;
  if(text.length>2000000)throw Error('source_text_too_large');return text;
 }finally{clearTimeout(timer);}
}
Deno.serve(async req=>{
 if(req.method!=='POST')return json({error:'method_not_allowed'},405);
 const sb=createClient(Deno.env.get('SUPABASE_URL'),Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'),{auth:{persistSession:false}});
 const {data:secret,error:authError}=await sb.from('internal_secrets').select('value').eq('key','ingest_token').single();
 if(authError||!equal(req.headers.get('x-ingest-token'),secret?.value))return json({error:'unauthorized'},401);
 const opts=await req.json().catch(()=>({}));const batch=Math.max(1,Math.min(20,Math.floor(Number(opts.batch)||10))),concurrency=Math.max(1,Math.min(3,Math.floor(Number(opts.concurrency)||2)));
 const dry=opts.dry_run===true,allowPaid=opts.allow_paid===true,probe=opts.probe_provider===true;
 const lane=allowPaid?'candidate_extraction_paid':'candidate_extraction';
 const ids=Array.isArray(opts.candidate_ids)?opts.candidate_ids.filter(Number.isSafeInteger).slice(0,batch):[];
 if(probe&&(!dry||ids.length!==1))return json({error:'provider_probe_requires_one_id_and_dry_run'},400);
 const owner=crypto.randomUUID();const {data:lease,error:leaseError}=await sb.rpc('phg_try_menu_worker_lease',{p_lane:lane,p_owner:owner,p_seconds:180});
 if(leaseError)return json({error:'lease_failed',detail:leaseError.message},500);if(!lease)return json({status:'already_running_or_paused',version:VERSION,lane});
 const result={version:VERSION,lane,dry_run:dry,selected:0,claimed:0,extracted:0,items:0,review:0,failed:0,paid_calls:0,provider_blocked:0,samples:[]};let cursor=0,providerBlocked=false;
 const deadline=Date.now()+55000;
 const claimable=c=>['queued','retry','legacy_empty','scope_check'].includes(c.status)||(allowPaid&&c.status==='review'&&BLOCKED.test(c.last_error||''));
 try{
  const fields='id,account_id,source_url,source_format,menu_scope,status,extraction_attempt_count,last_attempt_at,last_error';
  let q=sb.from('menu_source_candidates').select(fields);
  if(ids.length)q=q.in('id',ids);else q=q.eq('is_food_only',false).eq('source_format','html').in('menu_scope',['beverage','beverage_candidate','mixed','unknown','food_candidate']).in('status',['queued','retry','legacy_empty','scope_check']).lt('extraction_attempt_count',4).or('extraction_next_retry_at.is.null,extraction_next_retry_at.lte.'+new Date().toISOString()).order('extraction_attempt_count',{ascending:true}).order('id',{ascending:true});
  const {data:rows,error}=await q.limit(batch);if(error)throw Error('candidate_query: '+error.message);result.selected=rows.length;
  async function worker(){while(Date.now()<deadline){const ix=cursor++;if(ix>=rows.length)return;const c=rows[ix];let claimedAt=null;
   const knownBlocked=allowPaid&&BLOCKED.test(c.last_error||'');
   if(!dry){if(!claimable(c))continue;
    const {data:claim,error}=await sb.from('menu_source_candidates').update({status:'processing',last_attempt_at:new Date().toISOString(),extraction_attempt_count:Number(c.extraction_attempt_count||0)+1}).eq('id',c.id).eq('status',c.status).select('id,last_attempt_at').maybeSingle();if(error)throw Error('claim: '+error.message);if(!claim)continue;claimedAt=claim.last_attempt_at;result.claimed++;
   }
   try{
    let text='',items=[],method='direct_html_text_v4',directError='';
    if(!probe&&!knownBlocked){try{text=await directText(c.source_url);items=parseMenu(text);}catch(e){directError=String(e.message||e);}}
    const blockedSource=allowPaid?/unsafe_source_url/.test(directError):/source_http_(401|403|429)|unsafe_source_url/.test(directError);
    if((!items.length||probe)&&allowPaid&&!providerBlocked&&!blockedSource){
     const fc=Deno.env.get('FIRECRAWL_API_KEY');if(!fc)throw Error('firecrawl_key_not_configured');
     const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),20000);let response;
     try{result.paid_calls++;response=await fetch('https://api.firecrawl.dev/v2/scrape',{method:'POST',signal:ctrl.signal,headers:{'Content-Type':'application/json',Authorization:'Bearer '+fc.trim()},body:JSON.stringify({url:safeURL(c.source_url),formats:['markdown'],onlyMainContent:true})});
      await sb.from('menu_api_usage_ledger').insert({pipeline:'candidate_recovery',endpoint:'scrape_markdown',request_count:1,estimated_credits:response.ok?1:0,successful_outputs:0});
      if([402,429].includes(response.status)){providerBlocked=true;result.provider_blocked++;throw Error('provider_'+response.status);}
      if(!response.ok)throw Error('provider_http_'+response.status);
      const j=await response.json();text=String(j?.data?.markdown??j?.markdown??'');if(text.length>2000000)throw Error('source_text_too_large');items=parseMenu(text);method='firecrawl_markdown_v5';
     }finally{clearTimeout(timer);}
    }
    if(!text&&directError)throw Error(directError);if(!text)throw Error('empty_source_requires_followup');
    if(dry){result.items+=items.length;result.samples.push({candidate_id:c.id,method,items:items.length,source_characters:text.length,preview:items.slice(0,6)});continue;}
    const {data:saved,error}=await sb.rpc('phg_save_menu_candidate_extraction',{p_candidate_id:c.id,p_claimed_at:claimedAt,p_run_owner:owner,p_items:items,p_source_text:text,p_method:method,p_source_format:c.source_format==='pdf'?'pdf':c.source_format==='image'?'image':'html'});
    if(error)throw Error('save: '+error.message);if(saved?.status==='extracted')result.extracted++;else if(saved?.status==='review')result.review++;else throw Error(saved?.status||'save_unknown_result');result.items+=Number(saved.items||0);
    result.samples.push({candidate_id:c.id,method,...saved});
   }catch(e){result.failed++;const note=String(e.message||e).slice(0,350);result.samples.push({candidate_id:c.id,error:note});
    if(!dry&&claimedAt){const permanent=/source_http_(400|401|403|404|410)|provider_http_4\d\d|unsafe_source_url|source_too_large|needs_document_text_or_vision|too_many_items/.test(note);
     const {error}=await sb.from('menu_source_candidates').update({status:permanent?'review':'retry',last_error:note,extraction_next_retry_at:permanent?null:new Date(Date.now()+3600000).toISOString()}).eq('id',c.id).eq('status','processing').eq('last_attempt_at',claimedAt);if(error)result.samples.push({candidate_id:c.id,state_update_error:error.message});
    }
   }
  }}
  const settled=await Promise.allSettled(Array.from({length:concurrency},()=>worker()));
  const rejected=settled.filter(x=>x.status==='rejected');if(rejected.length)throw Error(rejected.map(x=>String(x.reason)).join('; '));
 }catch(e){result.error=String(e.message||e).slice(0,350);}
 finally{const {error}=await sb.rpc('phg_finish_menu_worker_lease',{p_lane:lane,p_owner:owner,p_result:result,p_pause_seconds:providerBlocked?900:0});if(error)result.lease_release_error=error.message;}
 return json(result,result.error?500:200);
});
