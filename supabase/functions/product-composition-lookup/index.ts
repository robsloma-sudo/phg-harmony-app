import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

/* UNUSED - Alko answers 403 and its robots.txt disallows AI agents (anthropic-ai, ClaudeBot); do not call.
   product-composition-lookup (2026-09-30) - free, official product composition for the phg_mix formulation work.
   Source: Alko (Finnish state alcohol retailer) public price list, published daily as an .xlsx
   ("Alkon hinnasto tekstitiedostona"): every product with Alkoholi-% (ABV), Hapot g/l (acids), Sokeri g/l (sugar),
   Energia kcal/100 ml. The dev container cannot reach alko.fi, so the download runs here. Read-only, writes nothing.
   POST {q:["campari","luxardo maraschino"], limit?:100}  header x-ingest-token  ->  {head, rows:[{...}], total_rows}
   A row matches when its name (Nimi) contains every word of any one query term (case-insensitive). */

const ALKO = "https://www.alko.fi/INTERSHOP/static/WFS/Alko-OnlineShop-Site/-/Alko-OnlineShop/fi_FI/Alkon%20Hinnasto%20Tekstitiedostona/alkon-hinnasto-tekstitiedostona.xlsx";
const WANT = ["Numero", "Nimi", "Valmistaja", "Pullokoko", "Tyyppi", "Alatyyppi", "Valmistusmaa", "Alkoholi-%", "Hapot g/l", "Sokeri g/l", "Energia kcal/100 ml", "Pakkaustyyppi"];

function json(b: unknown, s = 200) { return new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json" } }); }
function eq(a: string | null, b: string) {
  if (!a || !b) return false;
  const x = new TextEncoder().encode(a.trim()), y = new TextEncoder().encode(b.trim());
  if (x.length !== y.length) return false;
  let d = 0; for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i];
  return d === 0;
}

/* whole-sheet reader (price list is ~12k rows; fits in memory as raw cells), sheet1 + sharedStrings via fflate */
async function readSheet(stream: ReadableStream<Uint8Array>) {
  const { Unzip, UnzipInflate } = await import("npm:fflate@0.8.2");
  const dec = new TextDecoder();
  const unesc = (x: string) => x.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&#(\d+);/g, (_, d) => String.fromCharCode(+d)).replace(/&amp;/g, "&");
  const colIdx = (ref: string) => { const m = ref.match(/^([A-Z]+)/); let n = 0; if (m) for (const ch of m[1]) n = n * 26 + ch.charCodeAt(0) - 64; return n - 1; };
  type Cell = { t: string; v: string };
  const rows: Cell[][] = []; let sstText = ""; let buf = "";
  const feed = (text: string) => {
    buf += text; let end: number;
    while ((end = buf.indexOf("</row>")) >= 0) {
      const xml = buf.slice(buf.lastIndexOf("<row", end), end); buf = buf.slice(end + 6);
      const cells: Cell[] = [];
      for (const m of xml.matchAll(/<c\b([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g)) {
        const a = m[1] || "", inner = m[2] || "";
        const ref = (a.match(/\br="([A-Z]+\d+)"/) || [])[1] || ""; const t = (a.match(/\bt="(\w+)"/) || [])[1] || "n";
        const v = t === "inlineStr" ? [...inner.matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map((x) => x[1]).join("") : ((inner.match(/<v>([\s\S]*?)<\/v>/) || [])[1] || "");
        cells[ref ? colIdx(ref) : cells.length] = { t, v: unesc(v) };
      }
      rows.push(cells);
    }
  };
  await new Promise<void>((resolve, reject) => {
    let open = 0, ended = false; const done = () => { if (ended && open === 0) resolve(); };
    const uz = new Unzip((file: any) => {
      const isSheet = /^xl\/worksheets\/sheet1\.xml$/i.test(file.name), isSst = /^xl\/sharedStrings\.xml$/i.test(file.name);
      if (!isSheet && !isSst) return;
      open++;
      file.ondata = (err: any, chunk: Uint8Array, final: boolean) => {
        if (err) return reject(err);
        const text = dec.decode(chunk, { stream: !final });
        if (isSst) sstText += text; else feed(text);
        if (final) { open--; done(); }
      };
      file.start();
    });
    uz.register(UnzipInflate);
    (async () => {
      const rd = stream.getReader();
      try { for (;;) { const { value, done: d } = await rd.read(); if (d) { uz.push(new Uint8Array(0), true); break; } uz.push(value); } ended = true; done(); }
      catch (e) { reject(e); }
    })();
  });
  const sst = [...sstText.matchAll(/<si>([\s\S]*?)<\/si>/g)].map((m) => unesc([...m[1].matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map((x) => x[1]).join("")));
  return rows.map((r) => Array.from(r, (c) => (c ? (c.t === "s" ? (sst[+c.v] ?? "") : c.v) : "")));
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const { data: tok } = await sb.from("internal_secrets").select("value").eq("key", "ingest_token").single();
  if (!eq(req.headers.get("x-ingest-token"), tok?.value ?? "")) return json({ error: "unauthorized" }, 401);
  let b: { q?: string[]; limit?: number } = {};
  try { b = await req.json(); } catch { /* */ }
  const terms = (b.q ?? []).map((t) => String(t).toLowerCase().split(/\s+/).filter(Boolean)).filter((t) => t.length);
  if (!terms.length) return json({ error: "q required" }, 400);
  const limit = Math.max(1, Math.min(500, Number(b.limit) || 100));
  const t0 = Date.now();
  const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), 90000);
  try {
    const r = await fetch(ALKO, { signal: ctl.signal, headers: { "User-Agent": "PHG-formulation-research/1.0" } });
    if (!r.ok || !r.body) return json({ error: `alko HTTP ${r.status}` }, 502);
    const all = await readSheet(r.body);
    const hi = all.findIndex((row) => row.includes("Numero") && row.includes("Nimi"));
    if (hi < 0) return json({ error: "header not found", preview: all.slice(0, 5) }, 502);
    const head = all[hi].map((h) => h.trim());
    const ix = Object.fromEntries(WANT.map((w) => [w, head.indexOf(w)]));
    const nameI = ix["Nimi"];
    const out = [];
    for (const row of all.slice(hi + 1)) {
      const name = (row[nameI] ?? "").toLowerCase();
      if (!terms.some((t) => t.every((w) => name.includes(w)))) continue;
      out.push(Object.fromEntries(WANT.filter((w) => ix[w] >= 0).map((w) => [w, row[ix[w]] ?? ""])));
      if (out.length >= limit) break;
    }
    return json({ source: ALKO, list_date: all.slice(0, hi).map((r) => r.filter(Boolean).join(" ")).join(" | ").slice(0, 200), head: WANT.filter((w) => ix[w] >= 0), total_rows: all.length - hi - 1, rows: out, ms: Date.now() - t0 });
  } catch (e) {
    return json({ error: String((e as Error)?.message ?? e) }, 500);
  } finally { clearTimeout(tm); }
});
