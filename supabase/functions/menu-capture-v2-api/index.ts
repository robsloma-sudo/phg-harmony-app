// menu-capture-v2-api (2026-09-27, PHG-034): queue API for the HTML capture v2 worker (workers/html-capture).
// Separate from menu-render-worker-api so the live Railway workers are untouched.
//
// Auth: a GitHub Actions OIDC token in header x-gh-oidc (no shared secret). Accepted only when it is signed by
// GitHub, audience "phg-menu-capture-v2", repository_id 1384918236 (robsloma-sudo/phg-harmony-app) and the job runs
// the workflow .github/workflows/html-capture-v2.yml of that repository. Deployed with verify_jwt=false because the
// token is GitHub's, not Supabase's; this function does the verification itself.
//
// Lane: pages with render_strategy 'html_capture_v2' (queued by phg_capture_v2_queue, backed up first). A queued page
// keeps serving its old image until v2 replaces it. v2 images go to page-NNN.v2.jpg (old image stays in the bucket).
// Lease: render_next_retry_at (10 min) + render_last_error 'capture_v2_claim|..'. Three failures -> gave up, old kept.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
import { createRemoteJWKSet, jwtVerify } from "jsr:@panva/jose@6";

const BUCKET = "phg-menu-assets";
const LANE = "html_capture_v2";
const METHOD = "html_capture_v2";
const LEASE_MS = 10 * 60_000;
const MAX_BYTES = 40_000_000;
const MAX_FAILS = 3;
const REPO_ID = "1384918236";
const WORKFLOW = "robsloma-sudo/phg-harmony-app/.github/workflows/html-capture-v2.yml@";
const JWKS = createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));

const json = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json" } });

async function githubWorker(req: Request): Promise<string | null> {
  const tok = req.headers.get("x-gh-oidc") || "";
  if (!tok) return null;
  try {
    const { payload } = await jwtVerify(tok, JWKS, {
      issuer: "https://token.actions.githubusercontent.com", audience: "phg-menu-capture-v2", algorithms: ["RS256"],
    });
    if (String(payload.repository_id) !== REPO_ID) return null;
    if (!String(payload.job_workflow_ref || "").startsWith(WORKFLOW)) return null;
    return ("gh-" + String(payload.run_id || "?") + "-" + String(payload.run_attempt || "1")).slice(0, 64);
  } catch (_e) {
    return null;
  }
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405);
  const me = await githubWorker(req);
  if (!me) return json({ error: "unauthorized" }, 401);
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const u = new URL(req.url);
  const action = u.searchParams.get("action") || "claim_html";

  if (action === "claim_html") {
    const now = new Date().toISOString();
    const { data: pages, error } = await sb.from("menu_visual_pages")
      .select("id,menu_visual_document_id,page_number,updated_at,render_attempt_count")
      .eq("render_strategy", LANE).or("capture_method.is.null,capture_method.neq." + METHOD)
      .or("render_next_retry_at.is.null,render_next_retry_at.lte." + now)
      .order("render_attempt_count", { ascending: true }).order("id", { ascending: true }).limit(10);
    if (error) return json({ error: "queue_query_failed", detail: error.message }, 500);
    if (!pages?.length) return json({ status: "empty" });
    for (const p of pages as any[]) {
      const at = new Date().toISOString();
      const { data: got } = await sb.from("menu_visual_pages").update({
        render_next_retry_at: new Date(Date.now() + LEASE_MS).toISOString(),
        render_last_error: "capture_v2_claim|by=" + me + "|at=" + at, updated_at: at,
      }).eq("id", p.id).eq("updated_at", p.updated_at).select("id").maybeSingle();
      if (!got?.id) continue;
      const { data: doc } = await sb.from("menu_visual_documents").select("id,original_menu_url").eq("id", p.menu_visual_document_id).maybeSingle();
      if (!doc?.original_menu_url) continue;
      return json({ status: "job", page_id: p.id, document_id: doc.id, page_number: p.page_number,
        source_url: doc.original_menu_url, target_width: 1400, jpeg_quality: 85 });
    }
    return json({ status: "contended" });
  }

  if (action === "complete_html") {
    const pageId = Number(u.searchParams.get("page_id"));
    const width = Math.round(Number(u.searchParams.get("width"))), height = Math.round(Number(u.searchParams.get("height")));
    const { data: page } = await sb.from("menu_visual_pages").select("id,menu_visual_document_id,page_number,render_strategy")
      .eq("id", pageId).maybeSingle();
    if (!page?.id || page.render_strategy !== LANE) return json({ error: "page_not_in_v2_lane" }, 404);
    const declared = Number(req.headers.get("content-length") || "0");
    if (declared > MAX_BYTES) return json({ error: "image_too_large" }, 413);
    const bytes = new Uint8Array(await req.arrayBuffer());
    if (bytes.length < 3 || bytes[0] !== 0xff || bytes[1] !== 0xd8 || bytes.length > MAX_BYTES) return json({ error: "bad_jpeg" }, 400);
    const path = "document/" + page.menu_visual_document_id + "/page-" + String(page.page_number).padStart(3, "0") + ".v2.jpg";
    const up = await sb.storage.from(BUCKET).upload(path, bytes, { contentType: "image/jpeg", upsert: true });
    if (up.error) return json({ error: "upload_failed", detail: up.error.message }, 500);
    const t = new Date().toISOString();
    const { error } = await sb.from("menu_visual_pages").update({
      page_image_bucket: BUCKET, page_image_path: path, render_status: "ready", capture_method: METHOD,
      width: Number.isFinite(width) ? width : null, height: Number.isFinite(height) ? height : null,
      render_next_retry_at: null, render_error: null, render_last_error: "capture_v2_done|by=" + me + "|at=" + t, updated_at: t,
    }).eq("id", pageId);
    if (error) return json({ error: "page_update_failed", detail: error.message }, 500);
    await sb.from("menu_visual_documents").update({ page_render_status: "ready", page_rendered_at: t, updated_at: t })
      .eq("id", page.menu_visual_document_id);
    return json({ status: "ready", page_id: pageId, bytes: bytes.length, path });
  }

  if (action === "fail_html") {
    let body: any = {};
    try { body = await req.json(); } catch { /* empty */ }
    const pageId = Number(body.page_id);
    const { data: page } = await sb.from("menu_visual_pages").select("id,render_attempt_count,render_strategy").eq("id", pageId).maybeSingle();
    if (!page?.id || page.render_strategy !== LANE) return json({ error: "page_not_in_v2_lane" }, 404);
    const n = Number(page.render_attempt_count || 0) + 1;
    const gaveUp = n >= MAX_FAILS;
    await sb.from("menu_visual_pages").update({
      render_attempt_count: n,
      render_next_retry_at: gaveUp ? "2100-01-01T00:00:00Z" : new Date(Date.now() + 30 * 60_000).toISOString(),
      render_last_error: (gaveUp ? "capture_v2_gave_up|" : "capture_v2_fail|") + "n=" + n + "|" + String(body.error || "").slice(0, 400),
      updated_at: new Date().toISOString(),
    }).eq("id", pageId);
    return json({ status: gaveUp ? "gave_up" : "retry", page_id: pageId, attempts: n });
  }

  return json({ error: "unknown_action" }, 400);
});
