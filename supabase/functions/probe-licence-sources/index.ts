import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

/* probe-licence-sources (2026-09-30) - TEMPORARY diagnostic for finding free licence-list routes (PA, NC, OH, UT).
   The dev container's proxy blocks .gov, so source discovery runs here. Token-gated (x-ingest-token) and limited to an
   allowlist of state liquor-agency hosts (no open fetch). Writes nothing.
   POST {url, method?, body?, content_type?, max?}  -> {status, headers, cookies, text (first `max` chars, default 6000)} */

const HOSTS = new Set([
  "abc2.nc.gov", "abc.nc.gov", "www.abc.nc.gov", "aps.abc.nc.gov",
  "apps2.com.ohio.gov", "www.comapps.ohio.gov", "com.ohio.gov", "opal.ohio.gov", "data.ohio.gov",
  "abs.utah.gov", "opendata.utah.gov", "le.utah.gov",
  "www.lcb.pa.gov", "lcb.pa.gov", "plcbplus.pa.gov", "data.pa.gov",
]);

function json(b: unknown, s = 200) { return new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json" } }); }
function eq(a: string | null, b: string) {
  if (!a || !b) return false;
  const x = new TextEncoder().encode(a.trim()), y = new TextEncoder().encode(b.trim());
  if (x.length !== y.length) return false;
  let d = 0; for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i];
  return d === 0;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const { data: tok } = await sb.from("internal_secrets").select("value").eq("key", "ingest_token").single();
  if (!eq(req.headers.get("x-ingest-token"), tok?.value ?? "")) return json({ error: "unauthorized" }, 401);

  let b: { url?: string; method?: string; body?: string; content_type?: string; cookie?: string; max?: number } = {};
  try { b = await req.json(); } catch { /* */ }
  let u: URL;
  try { u = new URL(String(b.url ?? "")); } catch { return json({ error: "bad url" }, 400); }
  if (u.protocol !== "https:" || !HOSTS.has(u.hostname)) return json({ error: "host not allowed" }, 400);

  const headers: Record<string, string> = { "User-Agent": "PHG-licence-research/1.0", "Accept": "*/*" };
  if (b.content_type) headers["Content-Type"] = b.content_type;
  if (b.cookie) headers["Cookie"] = b.cookie;
  const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), 60000);
  try {
    const r = await fetch(u, { method: b.method ?? "GET", body: b.body, headers, redirect: "manual", signal: ctl.signal });
    const text = await r.text();
    const h: Record<string, string> = {};
    r.headers.forEach((v, k) => { if (k !== "set-cookie") h[k] = v; });
    const cookies = (r.headers.getSetCookie?.() ?? []).map((c) => c.split(";")[0]);
    return json({ status: r.status, headers: h, cookies, bytes: text.length, text: text.slice(0, Math.min(Number(b.max) || 6000, 60000)) });
  } catch (e) {
    return json({ error: String((e as Error)?.message ?? e) }, 502);
  } finally { clearTimeout(tm); }
});
