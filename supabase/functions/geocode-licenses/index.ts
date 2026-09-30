import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

/* GEOCODE LICENSES (2026-09-29) - free US Census batch geocoder for phg_license.licenses (no key, no paid service).
   POST {state:"RI", limit?:2500, probe?:false}  header x-ingest-token (public.internal_secrets 'ingest_token', same as
   ingest-state-licenses). Fetches rows that still need geocoding via public.phg_license_geocode_batch, posts them to
   https://geocoding.geo.census.gov/geocoder/locations/addressbatch (benchmark Public_AR_Current, <= 2,500 rows per
   request), parses the CSV reply and writes it back via public.phg_license_geocode_apply (lat/lng, match, geocoded_at;
   empty zip/city filled from the matched address; No_Match/Tie rows marked so they are not retried).
   Returns {state, sent, matched, no_match, tie, zip_filled, city_filled, ms}. {probe:true} returns parsed rows, no write.
   Census is called from here because the dev container's proxy blocks census.gov; this is triggered from SQL (pg_net,
   and the pg_cron job phg-license-geocode). */

const CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch";
const MAX_ROWS = 2500;       // rows per Census request (speed); Census allows 10,000
const CENSUS_MS = 120000;    // stay under the edge wall-clock limit
const APPLY_CHUNK = 1000;    // rows per apply RPC (PostgREST 8 s statement timeout)

function json(b: unknown, s = 200) { return new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json" } }); }
function eq(a: string | null, b: string) {
  if (!a || !b) return false;
  const x = new TextEncoder().encode(a.trim()), y = new TextEncoder().encode(b.trim());
  if (x.length !== y.length) return false;
  let d = 0; for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i];
  return d === 0;
}

/* minimal RFC-4180 CSV parser (quoted fields, doubled quotes, CRLF) */
function parseCsv(text: string): string[][] {
  const out: string[][] = []; let row: string[] = []; let f = ""; let q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(f); f = ""; }
    else if (c === "\n") { row.push(f); out.push(row); row = []; f = ""; }
    else if (c !== "\r") f += c;
  }
  if (f !== "" || row.length) { row.push(f); out.push(row); }
  return out;
}
/* CSV field for the upload: commas/quotes/newlines stripped (Census splits on commas) */
const cf = (v: unknown) => String(v ?? "").replace(/[",\r\n]+/g, " ").replace(/\s+/g, " ").trim();

type In = { state: string; license_no: string; street: string; city: string | null; st: string; zip: string | null };
type Out = { state: string; license_no: string; match: string; lat: number | null; lng: number | null; city: string | null; zip: string | null };

async function census(rows: In[]): Promise<Map<string, string[]>> {
  const csv = rows.map((r, i) => [i, cf(r.street), cf(r.city), cf(r.st), cf(r.zip)].join(",")).join("\n") + "\n";
  const fd = new FormData();
  fd.append("addressFile", new Blob([csv], { type: "text/csv" }), "addresses.csv");
  fd.append("benchmark", "Public_AR_Current");
  const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), CENSUS_MS);
  try {
    const r = await fetch(CENSUS, { method: "POST", body: fd, signal: ctl.signal, headers: { "User-Agent": "PHG-license-geocode/1.0" } });
    const text = await r.text();
    if (!r.ok) throw new Error(`Census HTTP ${r.status}: ${text.slice(0, 200)}`);
    const m = new Map<string, string[]>();
    for (const f of parseCsv(text)) if (f.length >= 3 && /^\d+$/.test(f[0].trim())) m.set(f[0].trim(), f);
    return m;
  } finally { clearTimeout(tm); }
}

function toOut(r: In, f: string[] | undefined): Out {
  const base = { state: r.state, license_no: r.license_no, lat: null, lng: null, city: null, zip: null };
  const status = (f?.[2] ?? "").trim();
  if (status !== "Match") return { ...base, match: status || "No_Response" };
  const [lon, lat] = (f?.[5] ?? "").split(",").map((x) => Number(x.trim()));
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return { ...base, match: "No_Match" };
  /* matched address "STREET, CITY, ST, ZIP" - read from the end (street may hold commas) */
  const p = (f?.[4] ?? "").split(",").map((x) => x.trim());
  const zip = p.length >= 4 && /^\d{5}$/.test(p[p.length - 1]) ? p[p.length - 1] : null;
  const city = p.length >= 4 ? p[p.length - 3] || null : null;
  return { ...base, match: `Match:${(f?.[3] ?? "").trim() || "?"}`, lat, lng: lon, city, zip };
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const { data: tok } = await sb.from("internal_secrets").select("value").eq("key", "ingest_token").single();
  if (!eq(req.headers.get("x-ingest-token"), tok?.value ?? "")) return json({ error: "unauthorized" }, 401);

  const t0 = Date.now();
  let body: { state?: string; limit?: number; probe?: boolean } = {};
  try { body = await req.json(); } catch { /* empty body */ }
  const state = String(body.state ?? "").toUpperCase().trim();
  if (!/^[A-Z]{2}$/.test(state)) return json({ error: "state required" }, 400);
  const limit = Math.max(1, Math.min(MAX_ROWS, Math.floor(Number(body.limit) || MAX_ROWS)));

  try {
    const { data, error } = await sb.rpc("phg_license_geocode_batch", { p_state: state, p_limit: limit });
    if (error) throw new Error(`batch: ${error.message}`);
    const rows = (data ?? []) as In[];
    if (!rows.length) return json({ state, sent: 0, matched: 0, no_match: 0, tie: 0, done: true, ms: Date.now() - t0 });

    const res = await census(rows);
    const out = rows.map((r, i) => toOut(r, res.get(String(i))));
    const matched = out.filter((o) => o.match.startsWith("Match")).length;
    const tie = out.filter((o) => o.match === "Tie").length;
    const no_resp = out.filter((o) => o.match === "No_Response").length;
    const counts = { state, sent: rows.length, matched, no_match: rows.length - matched - tie - no_resp, tie, no_response: no_resp, census_ms: Date.now() - t0 };
    if (body.probe) return json({ ...counts, probe: rows.slice(0, 20).map((r, i) => ({ in: r, raw: res.get(String(i)), out: out[i] })) });

    /* rows Census did not answer for are not written, so they are retried on the next call */
    const done = out.filter((o) => o.match !== "No_Response");
    let zip_filled = 0, city_filled = 0;
    for (let i = 0; i < done.length; i += APPLY_CHUNK) {
      const { data: a, error: e } = await sb.rpc("phg_license_geocode_apply", { p: done.slice(i, i + APPLY_CHUNK) });
      if (e) throw new Error(`apply: ${e.message}`);
      zip_filled += Number(a?.zip_filled ?? 0); city_filled += Number(a?.city_filled ?? 0);
    }
    return json({ ...counts, zip_filled, city_filled, ms: Date.now() - t0 });
  } catch (e) {
    return json({ state, error: String((e as Error)?.message ?? e), ms: Date.now() - t0 }, 500);
  }
});
