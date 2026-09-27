
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const ALLOWED = new Set([778,783,784,786,793,797]);

Deno.serve(async (req: Request) => {
  if (req.method !== "GET") return new Response("method_not_allowed",{status:405});
  const u=new URL(req.url);
  const pageId=Number(u.searchParams.get("page_id"));
  if(!ALLOWED.has(pageId)) return new Response("not_found",{status:404});

  const sb=createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    {auth:{persistSession:false}}
  );

  const {data:p}=await sb.from("menu_visual_pages")
    .select("page_image_bucket,page_image_path,render_status,capture_method")
    .eq("id",pageId).maybeSingle();

  if(!p || p.render_status!=="ready" || p.capture_method!=="railway_pymupdf_jpeg" || !p.page_image_bucket || !p.page_image_path){
    return new Response("not_found",{status:404});
  }

  const {data:file,error}=await sb.storage.from(p.page_image_bucket).download(p.page_image_path);
  if(error || !file) return new Response("not_found",{status:404});
  return new Response(file.stream(),{
    headers:{
      "Content-Type":"image/jpeg",
      "Cache-Control":"public, max-age=300",
      "Access-Control-Allow-Origin":"*"
    }
  });
});
