// phg-menu-corpus-browser v6 (2026-09-27, PHG-033): + rule (keep_word|keep_method|defer|skip, capture-gate review) and sort "shuffle" with seed. v5 = v5.rollback.index.ts
// phg-menu-corpus-browser v5 (2026-09-27, PHG-030): + menu_kind / has / hide (phg_menu_doc_class). v4 = v4.rollback.index.ts
// phg-menu-corpus-browser v4 (2026-09-27, PHG-027)
// Authenticated corpus/gallery drill-down for the Menu Library.
//
// Changes from v3 (rollback source: v3.rollback.index.ts):
//  - Every venue/format/scope/status/prep filter accepts a string OR an array of strings (any-of),
//    for the multi-select dropdowns. Single strings still work (live 18.49.4 / 18.49.5 bodies).
//  - Census filters by the venue's ZIP (ACS 2020-2024 5-year, phg_census_zcta): income, age, young
//    (share 21-34), affluent (share of households $100k+), edu (bachelor's+), hisp - each an array of
//    band keys from action "filters" (values.census). Band 'na' = no census data for that ZIP.
//  - sort: recent | name | city | income_desc | income_asc | age_asc | age_desc | young_desc |
//    affluent_desc | edu_desc | hisp_desc (documents only).
//  - limit 1..100 (was 60) for the 20 / 50 / 100 per-page picker.
//  - action "filters" reads the cached vocabularies (phg_corpus_filter_values_cached, 15 min).
//  - action "document" also returns the venue's census row.
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

// A filter value may be one string or an array of strings. Returns undefined when empty.
const list = (v: unknown, maxItems = 60, maxLen = 80): string[] | undefined => {
  const raw = Array.isArray(v) ? v : (v === undefined || v === null ? [] : [v]);
  const out: string[] = [];
  for (const x of raw) {
    if (typeof x !== "string" && typeof x !== "number") continue;
    const t = String(x).trim().slice(0, maxLen);
    if (t && !out.includes(t)) out.push(t);
    if (out.length >= maxItems) break;
  }
  return out.length ? out : undefined;
};
const CENSUS_KEYS = ["income", "age", "young", "affluent", "edu", "hisp"];
const SORTS = ["recent","name","city","income_desc","income_asc","age_asc","age_desc","young_desc","affluent_desc","edu_desc","hisp_desc","shuffle"];

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
    const { data, error } = await sb.rpc("phg_corpus_filter_values_cached", { p_max_age: 900 });
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
    let census: unknown = null;
    const zip = String((doc as any)?.accounts?.postal_code || "").slice(0, 5);
    if (/^[0-9]{5}$/.test(zip)) {
      const { data: cz } = await sb.from("phg_census_zcta")
        .select("zcta,total_population,median_age,median_household_income,pop_21_34_pct,households_over_100k_pct,bachelors_or_higher_pct,hispanic_latino_pct")
        .eq("zcta", zip).maybeSingle();
      census = cz || null;
    }
    return json({ status: "ok", action, document: doc, pages, census, signed_expires_in: SIGN_TTL });
  }

  // ---- action: list ----
  const kind = str(b.kind || "rendered", 20).toLowerCase();
  const preps = list(b.prep_type, 13, 20)?.map((x) => x.toLowerCase());
  if (preps && preps.some((x) => !PREP_TYPES.includes(x))) return json({ error: "unknown prep_type", prep_types: PREP_TYPES }, 400);
  const states = list(b.state, 60, 12)?.map((x) => x.toUpperCase());
  if (states && states.some((x) => !/^[A-Z]{2}$/.test(x))) return json({ error: "invalid state" }, 400);
  const sortIn = str(b.sort || "recent", 20).toLowerCase();
  const limitIn = Math.floor(Number(b.limit) || 24);

  const params: Record<string, unknown> = {
    kind,
    limit: Math.min(100, Math.max(1, limitIn)),
    offset: Math.min(1000000, Math.max(0, Math.floor(Number(b.offset) || 0))),
    q: str(b.q, 120),
    state: states,
    city: list(b.city, 200, 80),
    venue_type: list(b.venue_type, 60, 60),
    asset_kind: list(b.asset_kind, 20, 20),
    source_format: list(b.source_format, 20, 20),
    menu_scope: list(b.menu_scope, 20, 30),
    status: list(b.status, 20, 30),
    cocktail: str(b.cocktail, 80),
    ingredient: str(b.ingredient, 80),
    prep_type: preps,
    sort: SORTS.includes(sortIn) ? sortIn : "recent",
  };
  for (const k of CENSUS_KEYS) params[k] = list(b[k], 10, 10);
  const KINDS = ["beverage","mixed","food","happy_hour","specials","delivery","not_menu","little_text","unread"];
  const TAGS = ["cocktails","beer","wine","spirits","sake_soju","non_alcoholic","food","happy_hour","specials","brunch","events","delivery"];
  params.menu_kind = list(b.menu_kind, 10, 20)?.filter((x) => KINDS.includes(x));
  params.has = list(b.has, 12, 20)?.filter((x) => TAGS.includes(x));
  params.hide = list(b.hide, 12, 20)?.filter((x) => TAGS.includes(x));
  const RULES = ["keep_word","keep_method","defer","skip"];
  params.rule = list(b.rule, 4, 20)?.filter((x) => RULES.includes(x));
  params.seed = str(b.seed, 40);
  for (const k of ["menu_kind", "has", "hide", "rule"]) if (!(params[k] as string[] | undefined)?.length) delete params[k];
  for (const k of Object.keys(params)) if (params[k] === undefined || params[k] === "") delete params[k];
  const sign = str(b.sign || "first", 10).toLowerCase(); // first | none

  const fn = kind === "candidates" ? "phg_corpus_browse_candidates" : "phg_corpus_browse_documents";
  const { data, error } = await sb.rpc(fn, { p: params });
  if (error) {
    const msg = String(error.message || "");
    const bad = /invalid state|unknown prep_type|invalid census band|invalid input/i.test(msg);
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
  const lim = params.limit as number, off = params.offset as number;
  const next_offset = rows.length === lim && (countCapped || off + lim < count) ? off + lim : null;

  return json({
    status: "ok",
    kind,
    count,
    count_capped: countCapped,
    rows,
    next_offset,
    offset: off,
    limit: lim,
    sort: kind === "candidates" ? "recent" : params.sort,
    gallery,
    signed_expires_in: gallery ? SIGN_TTL : null,
    filters: {
      // vocabularies with counts come from action:"filters"; these are the accepted keys
      keys: ["q","state","city","venue_type","asset_kind","source_format","menu_scope","status","cocktail","ingredient","prep_type","sort", ...CENSUS_KEYS],
      multi: ["state","city","venue_type","asset_kind","source_format","menu_scope","status","prep_type", ...CENSUS_KEYS],
      sorts: SORTS,
      page_sizes: [20, 50, 100],
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
