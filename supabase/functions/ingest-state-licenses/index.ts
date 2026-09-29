import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

/* INGEST STATE LICENSES (PHG-050, 2026-09-29) - free public liquor-license lists for the 47-state rollout.
   POST {state:"TX", offset?:0, pages?:8}  header x-ingest-token (public.internal_secrets 'ingest_token', same as the
   other pipeline functions). Each call loads up to `pages` pages (1,000 rows each) from the state's open-data source,
   classifies on-premise licence types, upserts into phg_license.licenses via public.phg_license_upsert, logs the run
   in phg_license.ingest_runs, and returns {next_offset|null}. Re-call with next_offset until it is null.
   Sources (all free, no key; see data/expansion/states_*.jsonl):
     TX  data.texas.gov Socrata kguh-7q9z (TABC licences; MB/BG/BE/N* are on-premise)
     MO  data.mo.gov Socrata yyhn-562y (primary_type 'Retail by Drink' = on-premise; out-of-state holders skipped)
     OR  data.oregon.gov Socrata srxe-qkm2 (only license_expired = 'No'; 'ON-PREMISES' types)
     IL  ilcc.illinois.gov daily CSV export (retail_type ON-PREMISES / COMBINATION = on-premise)
   Never calls a paid service. */

const PAGE = 1000;
type Row = Record<string, unknown>;

function json(b: unknown, s = 200) { return new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json" } }); }
function eq(a: string | null, b: string) {
  if (!a || !b) return false;
  const x = new TextEncoder().encode(a.trim()), y = new TextEncoder().encode(b.trim());
  if (x.length !== y.length) return false;
  let d = 0; for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i];
  return d === 0;
}
const t = (v: unknown) => { const s = String(v ?? "").replace(/\s+/g, " ").trim(); return s || null; };
const zip5 = (v: unknown) => { const m = String(v ?? "").match(/(\d{5})\d{0,4}\s*$/); return m ? m[1] : null; };
const isoDate = (v: unknown) => {
  const s = String(v ?? "").trim(); if (!s) return null;
  let m = s.match(/^(\d{4})-(\d{2})-(\d{2})/); if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/); if (m) return `${m[3]}-${m[1].padStart(2, "0")}-${m[2].padStart(2, "0")}`;
  return null;
};

async function getJson(url: string, ms = 25000) {
  const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetch(url, { signal: ctl.signal, headers: { "Accept": "application/json", "User-Agent": "PHG-license-ingest/1.0" } });
    if (!r.ok) throw new Error(`HTTP ${r.status} from ${new URL(url).host}`);
    return await r.json();
  } finally { clearTimeout(tm); }
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

const TX_ON = new Set(["MB", "BG", "BE", "N", "NB", "NE"]);
const TX_OFF = new Set(["BQ", "P", "Q", "BF"]);

type Adapter = { source: string; pages: (offset: number, pages: number) => Promise<{ rows: Row[]; done: boolean }> };

function socrata(host: string, id: string, where: string, map: (r: any) => Row | null, source: string): Adapter {
  return {
    source,
    async pages(offset, pages) {
      const rows: Row[] = []; let done = false;
      for (let p = 0; p < pages; p++) {
        const u = `https://${host}/resource/${id}.json?$limit=${PAGE}&$offset=${offset + p * PAGE}&$order=:id${where ? "&$where=" + encodeURIComponent(where) : ""}`;
        const page = await getJson(u);
        if (!Array.isArray(page)) throw new Error("unexpected response");
        for (const r of page) { const m = map(r); if (m) rows.push(m); }
        if (page.length < PAGE) { done = true; break; }
      }
      return { rows, done };
    },
  };
}

const ADAPTERS: Record<string, Adapter> = {
  TX: socrata("data.texas.gov", "kguh-7q9z", "", (r) => {
    const type = t(r.aimslicensetype);
    return {
      state: "TX", license_no: t(String(r.aimslicenseid ?? "").replace(/\.0$/, "")), license_type: type,
      on_premise: type ? (TX_ON.has(type) ? true : TX_OFF.has(type) ? false : null) : null, status: "active",
      business_name: t(r.aimstradename), owner_name: t(r.aimsownername), address: t(r.locationaddress), city: t(r.city),
      zip: zip5(r.zip), county: t(r.txcounty), raw: r,
    };
  }, "tx_tabc_socrata"),
  MO: socrata("data.mo.gov", "yyhn-562y", "state = 'Missouri'", (r) => {
    const type = t(r.primary_type);
    return {
      state: "MO", license_no: t(r.primary_license), license_type: type, on_premise: type ? /by (the )?drink/i.test(type) : null,
      status: "active", business_name: t(r.dbaname) || t(r.licensee), owner_name: t(r.licensee),
      address: t([r.street_number, r.street].filter(Boolean).join(" ")), city: t(r.city), zip: zip5(r.zipcode),
      county: t(String(r.county ?? "").replace(/^\d+\s*-\s*/, "")), raw: r,
    };
  }, "mo_ata_socrata"),
  OR: socrata("data.oregon.gov", "srxe-qkm2", "license_expired = 'No'", (r) => {
    const type = t(r.license_type);
    const addr = String(r.physical_address ?? "");
    return {
      state: "OR", license_no: t(r.license_number), license_type: type,
      on_premise: type ? (/\bON-PREMISES\b/i.test(type) && !/\bOFF-PREMISES\b/i.test(type)) : null, status: "active",
      business_name: t(r.trade_name) || t(r.licensee_name), owner_name: t(r.licensee_name),
      address: t(addr.replace(/\s+[A-Z .'-]+\s+OR\s+\d{5}(-\d{4})?\s*$/i, "")), city: t(r.city), zip: zip5(addr.replace(/-\d{4}\s*$/, "")),
      county: t(r.county), issued_on: isoDate(r.effective_date), expires_on: isoDate(r.license_expires), raw: r,
    };
  }, "or_olcc_socrata"),
  IL: {
    source: "il_ilcc_csv",
    async pages(offset, pages) {
      const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), 60000);
      let text = "";
      try {
        const r = await fetch("https://ilcc.illinois.gov/content/dam/soi/en/web/ilcc/datasources/ilcc-licenses-daily-export.csv", { signal: ctl.signal, headers: { "User-Agent": "PHG-license-ingest/1.0" } });
        if (!r.ok) throw new Error(`HTTP ${r.status} from ilcc.illinois.gov`);
        text = await r.text();
      } finally { clearTimeout(tm); }
      const all = parseCsv(text); const head = (all.shift() || []).map((h) => h.trim().toLowerCase());
      const ix = (k: string) => head.indexOf(k);
      const slice = all.slice(offset, offset + pages * PAGE);
      const rows = slice.filter((c) => c.length >= head.length - 1).map((c) => {
        const g = (k: string) => (ix(k) >= 0 ? c[ix(k)] : "");
        const retail = t(g("retail_type")) || "";
        const addr = String(g("dba_address"));
        return {
          state: "IL", license_no: t(g("license_number")), license_type: t([g("license_class"), g("business_type")].filter(Boolean).join(" · ")),
          /* COMBINATION = on- and off-premise sales: a bar/restaurant with carry-out counts, a store with a tasting bar does not */
          on_premise: retail ? (/^ON-PREMISES/i.test(retail) ? true : /COMBINATION/i.test(retail) ? !/store|station|supermarket|grocery|pharmacy|liquor|package|drug|gas|convenience/i.test(String(g("business_type"))) : false) : null,
          status: "active", business_name: t(g("acct_name")), owner_name: t(g("cust_name")),
          address: t(addr.split(/\s{2,}/)[0]), city: t(g("acct_city")), zip: zip5(addr.replace(/[^0-9]+$/, "")),
          county: t(g("county")), issued_on: isoDate(g("current_effective_date")), expires_on: isoDate(g("current_expiration_date")),
          raw: Object.fromEntries(head.map((h, i) => [h, c[i]])),
        } as Row;
      });
      return { rows, done: offset + pages * PAGE >= all.length };
    },
  },
};

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "POST required" }, 405);
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const { data: tok } = await sb.from("internal_secrets").select("value").eq("key", "ingest_token").single();
  if (!eq(req.headers.get("x-ingest-token"), tok?.value ?? "")) return json({ error: "unauthorized" }, 401);

  const b = await req.json().catch(() => ({}));
  if (b.warm) return json({ ok: true, warm: true, states: Object.keys(ADAPTERS) });
  const state = String(b.state || "").toUpperCase();
  const ad = ADAPTERS[state];
  if (!ad) return json({ error: "unsupported state", supported: Object.keys(ADAPTERS) }, 400);
  const offset = Math.max(0, Math.floor(Number(b.offset) || 0));
  const pages = Math.min(20, Math.max(1, Math.floor(Number(b.pages) || 8)));

  const { data: run } = await sb.rpc("phg_license_run", { p_action: "start", p_state: state, p_source: ad.source, p_cursor: String(offset) });
  try {
    const { rows, done } = await ad.pages(offset, pages);
    const good: Row[] = rows.filter((r) => r.license_no).map((r) => ({ ...r, source: ad.source }));
    let upserted = 0;
    for (let i = 0; i < good.length; i += 1000) {
      const { data: n, error } = await sb.rpc("phg_license_upsert", { p_rows: good.slice(i, i + 1000) });
      if (error) throw error;
      upserted += Number(n || 0);
    }
    const onp = good.filter((r) => r.on_premise === true).length;
    const next = done ? null : offset + pages * PAGE;
    await sb.rpc("phg_license_run", { p_action: "progress", p_state: state, p_source: ad.source, p_run: run, p_cursor: String(next ?? "end"), p_seen: rows.length, p_upserted: upserted, p_onprem: onp });
    await sb.rpc("phg_license_run", { p_action: "done", p_state: state, p_source: ad.source, p_run: run });
    return json({ ok: true, state, source: ad.source, offset, rows: rows.length, upserted, on_premise: onp, next_offset: next });
  } catch (e) {
    const msg = String((e as Error)?.message || e).slice(0, 500);
    await sb.rpc("phg_license_run", { p_action: "error", p_state: state, p_source: ad.source, p_run: run, p_error: msg });
    return json({ ok: false, state, offset, error: msg }, 500);
  }
});
