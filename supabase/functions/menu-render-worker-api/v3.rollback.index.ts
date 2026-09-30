
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const BUCKET="phg-menu-assets";

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


  if(action==="claim_html"){
    const now=new Date().toISOString();
    await sb.from("menu_visual_pages").update({
      render_status:"retry",render_next_retry_at:null,
      render_error:"stale external html claim reset",updated_at:now
    }).eq("render_status","processing")
      .in("render_strategy",["firecrawl_screenshot_after_download_check","railway_external_html_screenshot"])
      .lt("updated_at",new Date(Date.now()-20*60_000).toISOString());

    const {data:pages,error}=await sb.from("menu_visual_pages")
      .select("id,menu_visual_document_id,page_number,render_status,render_attempt_count")
      .in("render_strategy",["firecrawl_screenshot_after_download_check","railway_external_html_screenshot"])
      .in("render_status",["pending","retry"])
      .or("render_next_retry_at.is.null,render_next_retry_at.lte."+now)
      .order("render_attempt_count",{ascending:true}).order("id",{ascending:true}).limit(12);
    if(error)return json({error:"html_queue_query_failed",detail:error.message},500);
    if(!pages?.length)return json({status:"empty"});

    for(const p of pages as any[]){
      const attempt=Number(p.render_attempt_count??0)+1;
      const {data:claim}=await sb.from("menu_visual_pages").update({
        render_status:"processing",render_strategy:"railway_external_html_screenshot",
        render_attempt_count:attempt,render_error:null,updated_at:new Date().toISOString()
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
      .select("id,menu_visual_document_id,page_number").eq("id",pageId).maybeSingle();
    if(!page?.id)return json({error:"page_not_found"},404);
    const bytes=new Uint8Array(await req.arrayBuffer());
    if(!bytes.length)return json({error:"empty_image"},400);
    if(bytes.length>12_000_000)return json({error:"image_too_large"},413);
    const path="document/"+page.menu_visual_document_id+"/page-"+String(page.page_number).padStart(3,"0")+".jpg";
    const up=await sb.storage.from(BUCKET).upload(path,bytes,{contentType:"image/jpeg",upsert:true});
    if(up.error)return json({error:"upload_failed",detail:up.error.message},500);
    await sb.from("menu_visual_pages").update({
      page_image_bucket:BUCKET,page_image_path:path,render_status:"ready",
      capture_method:"railway_playwright_screenshot",render_strategy:"railway_external_html_screenshot",
      width:Number.isFinite(width)?Math.round(width):null,height:Number.isFinite(height)?Math.round(height):null,
      render_next_retry_at:null,render_error:null,updated_at:new Date().toISOString()
    }).eq("id",pageId);
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
    const attempt=Number(page.render_attempt_count??1),minutes=attempt>=6?120:attempt>=3?30:10;
    await sb.from("menu_visual_pages").update({
      render_status:"retry",render_error:String(body.error||"external html render failed").slice(0,500),
      render_next_retry_at:new Date(Date.now()+minutes*60_000).toISOString(),updated_at:new Date().toISOString()
    }).eq("id",pageId);
    return json({status:"retry",page_id:pageId,retry_minutes:minutes});
  }

  return json({error:"unknown_action"},400);
});
