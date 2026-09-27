// menu-render-chat-preview v2 (2026-09-27). Approved by Rob as a stopgap for the live 18.49.4 gallery.
// Serves one finished menu page image by page id, without sign-in (verify_jwt=false, as in v1).
// v1 served only six hard-coded page ids with capture_method railway_pymupdf_jpeg, so almost every
// live gallery card showed a broken image. v2 serves any ready page stored in the phg-menu-assets
// bucket. When the requested page is not ready it falls back to the first ready page of the same
// document. Content-Type follows the stored file (jpg, png, webp).
// Rollback: deploy v1.rollback.index.ts from this folder. Retire once the signed-URL gallery is live.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const BUCKET = "phg-menu-assets";
const EXT_TYPES: Record<string, string> = { jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png", webp: "image/webp", gif: "image/gif" };

type PageRow = {
  id: number;
  menu_visual_document_id: number | null;
  page_image_bucket: string | null;
  page_image_path: string | null;
  render_status: string | null;
};

function notFound(): Response {
  return new Response("not_found", { status: 404, headers: { "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store" } });
}
function usable(p: PageRow | null | undefined): p is PageRow {
  return !!p && p.render_status === "ready" && p.page_image_bucket === BUCKET && !!p.page_image_path;
}
function contentType(path: string, blobType: string): string {
  if (/^image\/(jpeg|png|webp|gif)$/i.test(blobType)) return blobType.toLowerCase();
  const m = /\.([a-z0-9]+)$/i.exec(path);
  return (m && EXT_TYPES[m[1].toLowerCase()]) || "image/jpeg";
}

Deno.serve(async (req: Request) => {
  if (req.method !== "GET" && req.method !== "HEAD") return new Response("method_not_allowed", { status: 405 });
  const raw = new URL(req.url).searchParams.get("page_id") || "";
  if (!/^[1-9][0-9]{0,11}$/.test(raw)) return notFound();
  const pageId = Number(raw);

  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const cols = "id,menu_visual_document_id,page_image_bucket,page_image_path,render_status";

  const { data: asked } = await sb.from("menu_visual_pages").select(cols).eq("id", pageId).maybeSingle();
  if (!asked) return notFound();
  let page: PageRow | null = usable(asked as PageRow) ? (asked as PageRow) : null;

  const docId = (asked as PageRow).menu_visual_document_id;
  if (!page && docId) {
    const { data: alt } = await sb.from("menu_visual_pages").select(cols)
      .eq("menu_visual_document_id", docId)
      .eq("render_status", "ready")
      .eq("page_image_bucket", BUCKET)
      .not("page_image_path", "is", null)
      .order("page_number", { ascending: true })
      .limit(1)
      .maybeSingle();
    if (usable(alt as PageRow)) page = alt as PageRow;
  }
  if (!page) return notFound();

  const { data: file, error } = await sb.storage.from(BUCKET).download(page.page_image_path!);
  if (error || !file) return notFound();
  return new Response(req.method === "HEAD" ? null : file.stream(), {
    headers: {
      "Content-Type": contentType(page.page_image_path!, file.type || ""),
      "Content-Length": String(file.size),
      "Cache-Control": "public, max-age=300",
      "Access-Control-Allow-Origin": "*",
      "X-Content-Type-Options": "nosniff",
    },
  });
});
