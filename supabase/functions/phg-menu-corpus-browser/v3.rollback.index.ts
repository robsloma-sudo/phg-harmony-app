// phg-menu-corpus-browser v3
// Authenticated corpus/gallery drill-down for the Live Menu Corpus cards.
//
// Changes from v2:
//  - Queries go through service-role-only SQL functions (phg_corpus_browse_documents /
//    phg_corpus_browse_candidates / phg_corpus_filter_values) so venue (state, city,
//    venue_type), cocktail-name, ingredient-text and preparation-class filters run in
//    the database, paginated, with no large result sets sent to the browser.
//  - Page images are returned as short-lived SIGNED URLs (private bucket phg-menu-assets)
//    for every ready page regardless of capture method. v2 returned raw storage paths and
//    the frontend fell back to menu-render-chat-preview, which only serves 6 page ids.
//  - `filters` vocabularies are derived from real data (v2 advertised values that do not
//    occur, so most selects returned 0 rows).
//  - action: "list" (default) | "document" (all pages of one document, signed) | "filters".
//  - Legacy v2 body keys (kind, limit, offset, asset_kind, menu_scope, status, q) still work.
//
// Data rule (Rob): missing menu text is UNKNOWN, never proof an ingredient is absent.
// Every row carries text_coverage so the UI can say "no stored text" instead of "no match".

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const SIGN_TTL = 900; // seconds
const DEFAULT_BUCKET = "phg-menu-assets";
const PREP_TYPES = ["syrup","infusion","cordial","shrub","puree","bitters","citrus","garnish","foam","tincture","saline","tea","coffee"];
const COVERAGE_NOTE = "Cocktail, ingredient and preparation filters match stored menu text linked to each document. A document without stored text (text_coverage=false) cannot match; that is unknown coverage, not evidence the ingredient is absent.";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "no-store" },
  });

const str = (v: unknown, max = 200) => String(v ?? "").trim().slice(0, max);

type Page = {
  id: number; page_number: number; render_status: string; capture_method: string | null;
  width: number | null; height: number | null; bucket: string | null; path: string | null;
  signed_url?: string | null;
};

// Sign a batch of (bucket,path) pairs; one storage call per bucket. Failures leave
// signed_url null (never fail the whole listing because one object is missing).
async function signPages(sb: any, pages: Page[]): Promise<Map<string, string>> {
  const byBucket = new Map<string, string[]>();
  for (const p of pages) {
    if (!p.path || p.render_status !== "ready") continue;
    const b = p.bucket || DEFAULT_BUCKET;
    const list = byBucket.get(b) || [];
    if (!list.includes(p.path)) list.push(p.path);
    byBucket.set(b, list);
  }
  const out = new Map<string, string>();
  for (const [bucket, paths] of byBucket) {
    for (let i = 0; i < paths.length; i += 100) {
      const chunk = paths.slice(i, i + 100);
      const { data, error } = await sb.storage.from(bucket).createSignedUrls(chunk, SIGN_TTL);
      if (error || !data) continue;
      for (const r of data) if (r?.signedUrl && r?.path) out.set(bucket + "|" + r.path, r.signedUrl);
    }
  }
  return out;
}

const keyOf = (p: Page) => (p.bucket || DEFAULT_BUCKET) + "|" + p.path;

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "POST required" }, 405);

  const url = Deno.env.get("SUPABASE_URL"), anon = Deno.env.get("SUPABASE_ANON_KEY"), svc = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !anon || !svc) return json({ error: "config" }, 500);

  // Authentication: a real Supabase Auth user. (Account-level authorization is tracked as
  // an open issue; v2 had the same boundary.)
  const auth = req.headers.get("Authorization") || "";
  if (!auth.toLowerCase().startsWith("bearer ")) return json({ error: "login required" }, 401);
  const uc = createClient(url, anon, { auth: { persistSession: false }, global: { headers: { Authorization: auth } } });
  const { data: ud } = await uc.auth.getUser(auth.slice(7));
  if (!ud?.user) return json({ error: "invalid login" }, 401);

  const sb = createClient(url, svc, { auth: { persistSession: false } });
  const b: any = await req.json().catch(() => ({}));
  const action = str(b.action || "list", 20).toLowerCase();

  if (action === "filters") {
    const { data, error } = await sb.rpc("phg_corpus_filter_values");
    if (error) return json({ error: error.message }, 500);
    return json({ status: "ok", action, values: data, coverage_note: COVERAGE_NOTE });
  }

  if (action === "document") {
    const id = Number(b.document_id);
    if (!Number.isFinite(id) || id <= 0) return json({ error: "document_id required" }, 400);
    const { data: doc, error: de } = await sb.from("menu_visual_documents")
      .select("id,account_id,original_menu_url,discovered_asset_url,asset_kind,acquisition_method,acquisition_status,page_count,menu_scope,page_render_status,page_rendered_at,updated_at,accounts!inner(account_name,street_address,postal_code,google_types,website_url)")
      .eq("id", id).maybeSingle();
    if (de) return json({ error: de.message }, 500);
    if (!doc) return json({ error: "not found" }, 404);
    const { data: pg, error: pe } = await sb.from("menu_visual_pages")
      .select("id,page_number,render_status,capture_method,width,height,page_image_bucket,page_image_path")
      .eq("menu_visual_document_id", id).order("page_number").limit(200);
    if (pe) return json({ error: pe.message }, 500);
    const pages: Page[] = (pg || []).map((x: any) => ({
      id: x.id, page_number: x.page_number, render_status: x.render_status, capture_method: x.capture_method,
      width: x.width, height: x.height, bucket: x.page_image_bucket, path: x.page_image_path,
    }));
    const signed = await signPages(sb, pages);
    for (const p of pages) p.signed_url = p.render_status === "ready" && p.path ? (signed.get(keyOf(p)) || null) : null;
    return json({ status: "ok", action, document: doc, pages, signed_expires_in: SIGN_TTL });
  }

  // ---- action: list ----
  const kind = str(b.kind || "rendered", 20).toLowerCase();
  const prep = str(b.prep_type, 20).toLowerCase();
  if (prep && !PREP_TYPES.includes(prep)) return json({ error: "unknown prep_type", prep_types: PREP_TYPES }, 400);
  const state = str(b.state, 2).toUpperCase();
  if (state && !/^[A-Z]{2}$/.test(state)) return json({ error: "invalid state" }, 400);

  const params = {
    kind,
    limit: Math.min(60, Math.max(1, Number(b.limit) || 24)),
    offset: Math.max(0, Number(b.offset) || 0),
    q: str(b.q, 120),
    state,
    city: str(b.city, 80),
    venue_type: str(b.venue_type, 60),
    asset_kind: str(b.asset_kind, 20),
    source_format: str(b.source_format, 20),
    menu_scope: str(b.menu_scope, 30),
    status: str(b.status, 30),
    cocktail: str(b.cocktail, 80),
    ingredient: str(b.ingredient, 80),
    prep_type: prep,
  };
  const sign = str(b.sign || "first", 10).toLowerCase(); // first | none

  const fn = kind === "candidates" ? "phg_corpus_browse_candidates" : "phg_corpus_browse_documents";
  const { data, error } = await sb.rpc(fn, { p: params });
  if (error) {
    const msg = String(error.message || "");
    const bad = /invalid state|unknown prep_type|invalid input/i.test(msg);
    return json({ error: msg }, bad ? 400 : 500);
  }
  const rows: any[] = Array.isArray(data?.rows) ? data.rows : [];
  const count = Number(data?.count || 0);
  const countCapped = !!data?.count_capped;

  if (kind !== "candidates") {
    const firstReady: Page[] = [];
    for (const r of rows) {
      const pages: Page[] = Array.isArray(r.pages) ? r.pages : [];
      const p = pages.find((x) => x.render_status === "ready" && x.path) || null;
      r.thumb = p ? { page_id: p.id, page_number: p.page_number, width: p.width, height: p.height, capture_method: p.capture_method, signed_url: null } : null;
      if (p && sign !== "none") firstReady.push(p);
    }
    if (firstReady.length) {
      const signed = await signPages(sb, firstReady);
      for (const r of rows) {
        if (!r.thumb) continue;
        const p = (r.pages as Page[]).find((x) => x.id === r.thumb.page_id)!;
        r.thumb.signed_url = signed.get(keyOf(p)) || null;
        p.signed_url = r.thumb.signed_url;
      }
    }
  }

  const gallery = kind !== "candidates";
  const next_offset = rows.length === params.limit && (countCapped || params.offset + params.limit < count)
    ? params.offset + params.limit : null;

  return json({
    status: "ok",
    kind,
    count,
    count_capped: countCapped,
    rows,
    next_offset,
    gallery,
    signed_expires_in: gallery ? SIGN_TTL : null,
    filters: {
      // vocabularies with counts come from action:"filters"; these are the accepted keys
      keys: ["q","state","city","venue_type","asset_kind","source_format","menu_scope","status","cocktail","ingredient","prep_type"],
      prep_types: PREP_TYPES,
      states: ["NY","CO","IA"],
      asset_kind: ["html","pdf","image"],
      menu_scope: gallery ? ["beverage","beverage_candidate"] : ["beverage_candidate","unknown","food_candidate","mixed","beverage","food"],
      status: gallery ? ["ready","pending"] : ["queued","scope_check","legacy_empty","retry","extracted","no_items","review","processing"],
      source_format: ["html","pdf","image","social","none"],
      search: "venue name",
    },
    coverage_note: COVERAGE_NOTE,
  });
});
