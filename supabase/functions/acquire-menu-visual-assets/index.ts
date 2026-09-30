import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import {createClient} from 'jsr:@supabase/supabase-js@2';
import {parseHTML} from 'npm:linkedom@0.18.12/worker';
import {PDFDocument} from 'npm:pdf-lib@1.17.1';
/* asset-recovery-9 (2026-09-29): same behaviour as asset-recovery-8, but candidates are processed CONCURRENTLY
   (6 at a time) and a batch may hold up to 24, so one run is no longer gated by the slowest restaurant website
   (each fetch can take up to 20 s and runs used to be strictly one after another). Claims stay atomic per row,
   the 55 s deadline and every size/redirect/safety check are unchanged. */
const BUCKET='phg-menu-assets',VERSION='asset-recovery-9',CONCURRENCY=6,MAX_BATCH=24;
const json=(b,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{'Content-Type':'application/json'}});
function equal(a,b){if(!a||!b)return false;const x=new TextEncoder().encode(a.trim()),y=new TextEncoder().encode(b.trim());if(x.length!==y.length)return false;let d=0;for(let i=0;i<x.length;i++)d|=x[i]^y[i];return d===0;}
function safe(raw,base){const u=new URL(raw,base);const h=u.hostname.toLowerCase();if(!['http:','https:'].includes(u.protocol)||u.username||u.password||!h.includes('.')||/^\d+\.\d+\.\d+\.\d+$/.test(h)||h.includes(':')||/(^|\.)(localhost|internal|local)$/.test(h))throw Error('unsafe_source_url');return u.href;}
async function checked(p){const r=await p;if(r.error)throw Error(r.error.message);return r.data;}
async function resource(raw){const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),20000);try{let target=safe(raw),r;
 for(let i=0;i<5;i++){r=await fetch(target,{redirect:'manual',signal:ctrl.signal,headers:{'User-Agent':'Mozilla/5.0 (compatible; PHGMenuAssetArchiver/2.0)','Accept':'application/pdf,image/*,text/html,*/*'}});if(r.status>=300&&r.status<400&&r.headers.get('location')){const next=safe(r.headers.get('location'),target);await r.body?.cancel();target=next;continue;}break;}
 if(!r?.ok)throw Error('source_http_'+(r?.status||0));const mime=(r.headers.get('content-type')||'').split(';')[0].toLowerCase();const limit=mime.includes('html')?4000000:25000000;
 if(Number(r.headers.get('content-length')||0)>limit){await r.body?.cancel();throw Error('large_source_requires_external_download');}
 const reader=r.body.getReader(),chunks=[];let total=0;while(true){const x=await reader.read();if(x.done)break;total+=x.value.length;if(total>limit){await reader.cancel();throw Error('large_source_requires_external_download');}chunks.push(x.value);}
 const bytes=new Uint8Array(total);let offset=0;for(const x of chunks){bytes.set(x,offset);offset+=x.length;}
 const pdf=bytes.length>5&&new TextDecoder().decode(bytes.slice(0,5))==='%PDF-';
 const image=(bytes[0]===137&&bytes[1]===80&&bytes[2]===78&&bytes[3]===71)||(bytes[0]===255&&bytes[1]===216)||(new TextDecoder().decode(bytes.slice(0,4))==='RIFF'&&new TextDecoder().decode(bytes.slice(8,12))==='WEBP');
 return {bytes,mime,url:r.url||target,kind:pdf?'pdf':image?'image':mime.includes('html')?'html':'unknown'};
 }finally{clearTimeout(timer);}}
function assetLinks(html,base){const {document}=parseHTML(html);const links=new Map();for(const n of document.querySelectorAll('a[href],iframe[src],embed[src],object[data],img[src]')){const raw=n.getAttribute('href')||n.getAttribute('src')||n.getAttribute('data');if(!raw)continue;let u;try{u=safe(raw,base);}catch{continue;}const path=new URL(u).pathname;const file=/\.(pdf|png|jpe?g|webp)$/i.test(path);const hint=u+' '+(n.textContent||'')+' '+(n.getAttribute('alt')||'')+' '+(n.getAttribute('title')||'');if(file&&(/menu|drink|cocktail|wine|beer|beverage|spirits?|happy.?hour/i.test(hint)||n.hasAttribute('download')||['IFRAME','EMBED','OBJECT'].includes(n.tagName)))links.set(u,/\.pdf$/i.test(path)?'pdf':'image');}if(links.size>100)throw Error('too_many_assets_requires_followup');return [...links].map(([url,kind])=>({url,kind}));}
Deno.serve(async req=>{
 if(req.method!=='POST')return json({error:'method_not_allowed'},405);
 const sb=createClient(Deno.env.get('SUPABASE_URL'),Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'),{auth:{persistSession:false}});
 const secret=await checked(sb.from('internal_secrets').select('value').eq('key','ingest_token').single());if(!equal(req.headers.get('x-ingest-token'),secret?.value))return json({error:'unauthorized'},401);
 const opts=await req.json().catch(()=>({})),batch=Math.max(1,Math.min(MAX_BATCH,Math.floor(Number(opts.batch)||6))),dry=opts.dry_run===true;
 const ids=Array.isArray(opts.candidate_ids)?opts.candidate_ids.filter(Number.isSafeInteger).slice(0,batch):[];
 const owner=crypto.randomUUID(),lease=await checked(sb.rpc('phg_try_menu_worker_lease',{p_lane:'visual_acquisition',p_owner:owner,p_seconds:180}));if(!lease)return json({status:'already_running_or_paused'});
 const result={version:VERSION,dry_run:dry,processed:0,stored:0,pdf_pages:0,html_queued:0,discovered_assets:0,already_saved:0,failed:0,samples:[]};const deadline=Date.now()+55000;
 const sample=(x)=>{if(result.samples.length<40)result.samples.push(x);};
 async function candidateFor(parent,url,kind){if(url===parent.source_url)return parent;const existing=await checked(sb.from('menu_source_candidates').select('id,account_id,source_url,source_format,menu_scope,menu_type').eq('account_id',parent.account_id).eq('source_url',url).maybeSingle());if(existing)return existing;
  const r=await sb.from('menu_source_candidates').insert({account_id:parent.account_id,source_url:url,menu_type:parent.menu_type||'mixed_or_unknown',menu_scope:parent.menu_scope||'unknown',source_format:kind,discovery_method:'download_link',discovery_confidence:.98,status:parent.menu_scope==='food_candidate'?'scope_check':'queued',is_food_only:false,scope_reason:'Downloadable asset linked by source menu page',page_count:1,page_count_exact:kind==='image',page_count_basis:kind==='image'?'single_image_exact':'archived_pdf_pending_exact_count',visual_asset_status:'not_started'}).select('id,account_id,source_url,source_format,menu_scope,menu_type').single();
  if(r.error){const raced=await checked(sb.from('menu_source_candidates').select('id,account_id,source_url,source_format,menu_scope,menu_type').eq('account_id',parent.account_id).eq('source_url',url).single());return raced;}result.discovered_assets++;return r.data;}
 async function saveFile(c,assetUrl,r,method){
  const existing=await checked(sb.from('menu_visual_documents').select('id,storage_path,acquisition_status,page_count,page_count_exact').eq('menu_source_candidate_id',c.id).eq('discovered_asset_url',assetUrl).maybeSingle());
  if(existing?.storage_path&&['downloaded','ready'].includes(existing.acquisition_status)){result.already_saved++;await checked(sb.from('menu_source_candidates').update({visual_asset_status:'downloaded',visual_document_id:existing.id,visual_asset_started_at:null,visual_asset_last_error:null,visual_asset_next_retry_at:null}).eq('id',c.id));return;}
  let pages=1,exact=r.kind==='image',countError=null;
  if(r.kind==='pdf'){try{const pdf=await PDFDocument.load(r.bytes,{ignoreEncryption:false,updateMetadata:false});pages=pdf.getPageCount();if(pages<1)throw Error('empty_pdf');exact=true;}catch(e){countError=String(e.message||e).slice(0,300);}}
  const ext=r.kind==='pdf'?'pdf':r.bytes[0]===137?'png':r.bytes[0]===255?'jpg':'webp';const mime=r.kind==='pdf'?'application/pdf':ext==='jpg'?'image/jpeg':'image/'+ext;
  const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',r.bytes));const hash=Array.from(digest,x=>x.toString(16).padStart(2,'0')).join('');
  const path='candidate/'+c.id+'/source-'+hash+'.'+ext;
  const upload=await sb.storage.from(BUCKET).upload(path,r.bytes,{contentType:mime,upsert:false});if(upload.error&&!/already exists|duplicate/i.test(upload.error.message))throw Error(upload.error.message);
  const data={menu_source_candidate_id:c.id,account_id:c.account_id,original_menu_url:c.source_url,discovered_asset_url:assetUrl,menu_scope:c.menu_scope,asset_kind:r.kind,acquisition_method:method,storage_bucket:BUCKET,storage_path:path,mime_type:mime,byte_size:r.bytes.length,page_count:pages,page_count_exact:exact,acquisition_status:'downloaded',screenshot_fallback_required:false,acquired_at:new Date().toISOString(),last_error:countError};
  const doc=existing?await checked(sb.from('menu_visual_documents').update(data).eq('id',existing.id).select('id').single()):await checked(sb.from('menu_visual_documents').insert(data).select('id').single());
  if(pages<=1000)await checked(sb.rpc('refresh_visual_page_placeholders',{p_document_id:doc.id}));
  if(r.kind==='image')await checked(sb.from('menu_visual_pages').update({page_image_bucket:BUCKET,page_image_path:path,render_status:'ready',capture_method:method,updated_at:new Date().toISOString()}).eq('menu_visual_document_id',doc.id).eq('page_number',1));
  await checked(sb.from('menu_source_candidates').update({visual_asset_status:'downloaded',visual_asset_method:method,visual_asset_url:assetUrl,visual_document_id:doc.id,page_count:pages,page_count_exact:exact,page_count_basis:exact?(r.kind==='pdf'?'archived_pdf_exact':'single_image_exact'):'archived_pdf_pending_exact_count',page_count_checked_at:exact?new Date().toISOString():null,visual_asset_started_at:null,visual_asset_next_retry_at:null,visual_asset_last_error:pages>1000?'large_page_count_requires_external_render':countError}).eq('id',c.id));
  result.stored++;if(r.kind==='pdf')result.pdf_pages+=exact?pages:0;sample({candidate_id:c.id,document_id:doc.id,kind:r.kind,bytes:r.bytes.length,pages,page_count_exact:exact});
 }
 async function queueHTML(c){
  const existing=await checked(sb.from('menu_visual_documents').select('id,acquisition_status').eq('menu_source_candidate_id',c.id).eq('asset_kind','html').eq('original_menu_url',c.source_url).maybeSingle());
  let doc=existing;if(!doc)doc=await checked(sb.from('menu_visual_documents').insert({menu_source_candidate_id:c.id,account_id:c.account_id,original_menu_url:c.source_url,menu_scope:c.menu_scope,asset_kind:'html',acquisition_method:'download_first_no_asset_found',page_count:1,page_count_exact:true,acquisition_status:'fallback_required',screenshot_fallback_required:true}).select('id').single());
  if(!existing)await checked(sb.rpc('refresh_visual_page_placeholders',{p_document_id:doc.id}));
  await checked(sb.from('menu_source_candidates').update({visual_asset_status:existing?.acquisition_status==='ready'?'downloaded':'screenshot_fallback',visual_asset_method:'download_first_no_asset_found',visual_document_id:doc.id,visual_asset_started_at:null,visual_asset_next_retry_at:null,visual_asset_last_error:null}).eq('id',c.id));result.html_queued++;sample({candidate_id:c.id,document_id:doc.id,kind:'html',status:'queued_for_existing_renderer'});
 }
 async function handle(c){
  if(!dry){if(!['not_started','retry'].includes(c.visual_asset_status))return;const claim=await checked(sb.from('menu_source_candidates').update({visual_asset_status:'processing',visual_asset_started_at:new Date().toISOString(),visual_asset_attempt_count:Number(c.visual_asset_attempt_count||0)+1}).eq('id',c.id).eq('visual_asset_status',c.visual_asset_status).select('id').maybeSingle());if(!claim)return;}
  result.processed++;
  try{
   const existing=await checked(sb.from('menu_visual_documents').select('id,storage_path,acquisition_status').eq('menu_source_candidate_id',c.id).eq('discovered_asset_url',c.source_url).maybeSingle());
   if(existing?.storage_path&&['downloaded','ready'].includes(existing.acquisition_status)){result.already_saved++;if(!dry)await checked(sb.from('menu_source_candidates').update({visual_asset_status:'downloaded',visual_document_id:existing.id,visual_asset_started_at:null,visual_asset_last_error:null}).eq('id',c.id));return;}
   const r=await resource(c.source_url);
   if(dry){let n=null;if(r.kind==='pdf'){try{n=(await PDFDocument.load(r.bytes,{ignoreEncryption:false,updateMetadata:false})).getPageCount();}catch{}}sample({candidate_id:c.id,kind:r.kind,bytes:r.bytes.length,pages:n,links:r.kind==='html'?assetLinks(new TextDecoder().decode(r.bytes),r.url):[]});return;}
   if(['pdf','image'].includes(r.kind)){await saveFile(c,c.source_url,r,'direct_file_download');return;}
   if(r.kind!=='html')throw Error('unsupported_source_requires_review');
   const links=assetLinks(new TextDecoder().decode(r.bytes),r.url);if(!links.length){await queueHTML(c);return;}
   const children=[];for(const link of links)children.push(await candidateFor(c,link.url,link.kind));
   await checked(sb.from('menu_source_candidates').update({visual_asset_status:'download_links_queued',visual_asset_method:'html_download_link',visual_asset_started_at:null,visual_asset_next_retry_at:null,visual_asset_last_error:null}).eq('id',c.id));sample({candidate_id:c.id,download_assets_queued:children.length});
  }catch(e){result.failed++;const note=String(e.message||e).slice(0,350);sample({candidate_id:c.id,error:note});if(!dry)await checked(sb.from('menu_source_candidates').update({visual_asset_status:'retry',visual_asset_started_at:null,visual_asset_last_error:note,visual_asset_next_retry_at:new Date(Date.now()+3600000).toISOString()}).eq('id',c.id));}
 }
 try{
  const fields='id,account_id,source_url,source_format,menu_scope,menu_type,visual_asset_status,visual_asset_attempt_count';let rows=[];
  const base=()=>sb.from('menu_source_candidates').select(fields).in('visual_asset_status',['not_started','retry']).lt('visual_asset_attempt_count',4).or('visual_asset_next_retry_at.is.null,visual_asset_next_retry_at.lte.'+new Date().toISOString()).order('visual_asset_attempt_count',{ascending:true}).order('id',{ascending:true});
  if(ids.length)rows=await checked(sb.from('menu_source_candidates').select(fields).in('id',ids));else{
   const files=await checked(base().in('source_format',['pdf','image']).limit(Math.ceil(batch/2)));const html=await checked(base().eq('source_format','html').limit(batch-files.length));rows=[...files,...html];
  }
  /* a small pool: CONCURRENCY workers take the next candidate until the list or the deadline runs out */
  let next=0;
  const worker=async()=>{while(next<rows.length&&Date.now()<deadline){const c=rows[next++];await handle(c);}};
  await Promise.all(Array.from({length:Math.min(CONCURRENCY,rows.length)},worker));
 }catch(e){result.error=String(e.message||e).slice(0,350);}
 finally{try{await checked(sb.rpc('phg_finish_menu_worker_lease',{p_lane:'visual_acquisition',p_owner:owner,p_result:result,p_pause_seconds:0}));}catch(e){result.lease_release_error=String(e.message||e);}}
 return json(result,result.error?500:200);
});
