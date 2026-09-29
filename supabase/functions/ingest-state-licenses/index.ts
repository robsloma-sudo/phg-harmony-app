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
   v3: + CT (Socrata, no permit class published -> on_premise unknown), DC + KY/Louisville (ArcGIS), VA (xlsx);
   {probe:true} returns headers + sample rows without writing.
   v5: CT and VA adapters removed (see notes), KY NQ4/caterer and DC 'Retail -' classes fixed.
   v4: + MI (master xlsx), WA (weekly On Premise xlsx), CA (daily zipped CSV), ME (FOAA xlsx); download links are
   discovered on each state's page because the file names change.
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

function arcgis(layer: string, where: string, map: (a: any) => Row | null, source: string): Adapter {
  return {
    source,
    async pages(offset, pages) {
      const rows: Row[] = []; let done = false;
      for (let p = 0; p < pages; p++) {
        const u = `${layer}/query?where=${encodeURIComponent(where)}&outFields=*&returnGeometry=false&orderByFields=OBJECTID&resultOffset=${offset + p * PAGE}&resultRecordCount=${PAGE}&f=json`;
        const page = await getJson(u);
        if (page?.error) throw new Error(`ArcGIS ${page.error.code}: ${page.error.message}`);
        const feats = Array.isArray(page?.features) ? page.features : [];
        for (const f of feats) { const m = map(f.attributes || {}); if (m) rows.push(m); }
        if (feats.length < PAGE && !page?.exceededTransferLimit) { done = true; break; }
      }
      return { rows, done };
    },
  };
}
const epochDate = (v: unknown) => (typeof v === "number" ? new Date(v).toISOString().slice(0, 10) : isoDate(v));

/* generic spreadsheet adapter: finds columns by header words (licence no., name, address, city, zip, type) */
/* find the current download link on a state's page (file names carry dates) */
async function discover(page: string, re: RegExp): Promise<string> {
  const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), 30000);
  try {
    const r = await fetch(page, { signal: ctl.signal, headers: { "User-Agent": "PHG-license-ingest/1.0" } });
    if (!r.ok) throw new Error(`HTTP ${r.status} from ${new URL(page).host}`);
    const html = await r.text();
    const links = [...html.matchAll(/href="([^"]+)"/gi)].map((m) => m[1].replace(/&amp;/g, "&")).filter((h) => re.test(decodeURIComponent(h)));
    if (!links.length) throw new Error(`no download link matching ${re} on ${page}`);
    return new URL(links[links.length - 1], page).href;
  } finally { clearTimeout(tm); }
}
async function sheetRows(url: string): Promise<{ head: string[]; rows: string[][] }> {
  const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), 90000);
  let buf: ArrayBuffer;
  try {
    const r = await fetch(url, { signal: ctl.signal, headers: { "User-Agent": "PHG-license-ingest/1.0" } });
    if (!r.ok) throw new Error(`HTTP ${r.status} from ${new URL(url).host}`);
    buf = await r.arrayBuffer();
  } finally { clearTimeout(tm); }
  if (/\.zip(\?|$)/i.test(url)) {
    const { unzipSync, strFromU8 } = await import("npm:fflate@0.8.2");
    const files = unzipSync(new Uint8Array(buf));
    const name = Object.keys(files).find((k) => /\.(csv|txt)$/i.test(k));
    if (!name) throw new Error("zip has no csv");
    const text = strFromU8(files[name]);
    const tab = text.split("\n", 2)[0].includes("\t");
    const all = tab ? text.split(/\r?\n/).map((l) => l.split("\t")) : parseCsv(text);
    return { head: (all.shift() || []).map((h) => h.trim()), rows: all.filter((r) => r.length > 1) };
  }
  const XLSX = await import("npm:xlsx@0.18.5");
  const wb = XLSX.read(new Uint8Array(buf), { type: "array", cellDates: true });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const all: any[][] = XLSX.utils.sheet_to_json(ws, { header: 1, raw: false, defval: "" });
  // header = first row with at least 3 non-empty cells that mentions licen/permit
  let h = all.findIndex((r) => r.filter((c: any) => String(c).trim()).length >= 3 && r.some((c: any) => /licen|permit/i.test(String(c))));
  if (h < 0) h = 0;
  return { head: all[h].map((c: any) => String(c).trim()), rows: all.slice(h + 1).map((r) => r.map((c: any) => String(c ?? ""))) };
}
function col(head: string[], ...res: RegExp[]) { for (const re of res) { const i = head.findIndex((h) => re.test(h)); if (i >= 0) return i; } return -1; }
function sheetAdapter(state: string, url: string | (() => Promise<string>), source: string, onPremise: (type: string) => boolean | null): Adapter {
  return {
    source,
    async pages(offset, pages) {
      const { head, rows: all } = await sheetRows(typeof url === "string" ? url : await url());
      const iNo = col(head, /licen[cs]e\s*(no|num|#|id)/i, /permit\s*(no|num|#)/i, /^licen[cs]e$/i);
      const iType = col(head, /licen[cs]e\s*(type|class|desc|privilege)/i, /privilege/i, /^type$/i, /class/i);
      const iName = col(head, /trade|dba|doing business/i, /business\s*name/i, /establishment/i, /^name$/i);
      const iOwner = col(head, /licensee|owner|entity|applicant/i);
      const iAddr = col(head, /(premise|physical|location|street)?\s*address(\s*1|\s*line\s*1)?$/i, /street/i);
      const iCity = col(head, /city/i, /locality|town/i);
      const iZip = col(head, /zip|postal/i);
      const iCounty = col(head, /county/i);
      const iStatus = col(head, /status/i);
      const iExp = col(head, /expir/i);
      const g = (r: string[], i: number) => (i >= 0 ? r[i] : "");
      const slice = all.slice(offset, offset + pages * PAGE).filter((r) => g(r, iNo).trim());
      const rows = slice.map((r) => {
        const type = t(g(r, iType)) || "";
        return {
          state, license_no: t(g(r, iNo)), license_type: type || null, on_premise: type ? onPremise(type) : null,
          status: t(g(r, iStatus)) || "active", business_name: t(g(r, iName)) || t(g(r, iOwner)), owner_name: t(g(r, iOwner)),
          address: t(g(r, iAddr)), city: t(g(r, iCity)), zip: zip5(g(r, iZip)), county: t(g(r, iCounty)), expires_on: isoDate(g(r, iExp)),
          raw: Object.fromEntries(head.map((h, i) => [h || `col${i}`, r[i]])),
        } as Row;
      });
      return { rows, done: offset + pages * PAGE >= all.length, head } as any;
    },
  };
}

const KY_ON = /retail drink|retail malt beverage drink|supplemental bar|hotel in-room|entertainment destination|golf course|authorized public consumption|qualified historic|microbrewery|caterer/i;
const KY_SUPPLEMENTAL = /special sunday|extended hours/i;

const ADAPTERS: Record<string, Adapter> = {
  /* CT: data.ct.gov gwv2-eswx is mostly brand registrations (LBD.*), not premises -> removed 2026-09-29; manual source needed. */
  DC: arcgis("https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Business_Licensing_and_Grants_WebMercator/FeatureServer/5", "1=1", (a) => {
    const type = t([a.TYPE, a.CLASS].filter(Boolean).join(" · "));
    const on = type ? (/wholesal|manufactur|retail\s*-|internet|third-party delivery|25 percent|off.?premise/i.test(type) ? false
      : /restaurant|tavern|night\s*club|hotel|club|multipurpose|caterer|arena|stadium|marine vessel|railroad|bed and breakfast/i.test(type) ? true : null) : null;
    return {
      state: "DC", license_no: t(a.LICENSE), license_type: type, on_premise: on, status: t(a.STATUS),
      business_name: t(a.TRADE_NAME) || t(a.APPLICANT), owner_name: t(a.APPLICANT), address: t(a.ADDRESS), city: "Washington",
      zip: zip5(a.ZIPCODE), lat: a.LATITUDE ?? null, lng: a.LONGITUDE ?? null, expires_on: epochDate(a.EXPIRATION_DATE), raw: a,
    };
  }, "dc_abca_arcgis"),
  KY: arcgis("https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/ABC_State_ActiveLicenses/FeatureServer/0", "Status='Active'", (a) => {
    const type = t(a.LicenseType) || "";
    const cityState = String(a.PremisesCityState ?? "");
    return {
      state: "KY", license_no: t(a.LicenseNumber), license_type: type || null,
      on_premise: !type ? null : KY_SUPPLEMENTAL.test(type) ? null : KY_ON.test(type),
      status: t(a.Status), business_name: t(a.DBA) || t(a.Licensee), owner_name: t(a.Licensee), address: t(a.PremisesStreet),
      city: t(a.City) || t(cityState.split(",")[0]), zip: zip5(cityState), county: t(a.County),
      lat: a.Latitude ?? null, lng: a.Longitude ?? null, issued_on: epochDate(a.IssueDate), expires_on: epochDate(a.ExpiryDate), raw: a,
    };
  }, "ky_abc_louisville_arcgis"),
  /* Michigan LCC master list (all licence types; SDM/SDD are package/off-premise) */
  MI: sheetAdapter("MI", () => discover("https://www.michigan.gov/lara/bureau-list/lcc/licensing-list", /Master-License-List\.xlsx/i), "mi_lcc_xlsx",
    (type) => /\bSD[MD]\b|off[- ]premise|specially designated/i.test(type) && !/class c|tavern|hotel|club|on[- ]premise/i.test(type) ? false
      : /class c|tavern|hotel|club|brewpub|micro ?brew|resort|on[- ]premise|winery|distill|small distiller/i.test(type) ? true : null),
  /* Washington LCB weekly "On Premise" list: every row is an on-premise licensee */
  WA: sheetAdapter("WA", () => discover("https://lcb.wa.gov/records/frequently-requested-lists", /On ?Premise ?\d+\.xlsx/i), "wa_lcb_onpremise_xlsx", () => true),
  /* California ABC daily export (zipped CSV); on-sale types 40-42, 47-49, 51-52, 57, 59-61, 67-68, 70, 75 */
  CA: sheetAdapter("CA", () => discover("https://www.abc.ca.gov/licensing/licensing-reports/", /DailyExport-CSV\.zip/i), "ca_abc_daily_csv",
    (type) => { const m = type.match(/\b(\d{2})\b/); if (!m) return null; const c = +m[1];
      return [40, 41, 42, 47, 48, 49, 51, 52, 57, 59, 60, 61, 67, 68, 70, 75].includes(c) ? true : [20, 21, 17, 9, 1, 2, 3, 4, 13, 14, 22, 23, 12].includes(c) ? false : null; }),
  /* Maine BABLO licence report */
  ME: sheetAdapter("ME", () => discover("https://www.maine.gov/dafs/bablo/liquor-licensing/license-data", /FOAA_Report\.xlsx/i), "me_bablo_xlsx",
    (type) => /off[- ]premise|agency store|retail store|wholesal|manufactur/i.test(type) && !/on[- ]premise/i.test(type) ? false
      : /restaurant|lounge|tavern|hotel|club|bar|brew ?pub|on[- ]premise|class [a-i]\b|caterer|golf|bowling|vessel/i.test(type) ? true : null),
  /* VA: abc.virginia.gov serves a certificate chain Deno/curl do not trust (UnknownIssuer) -> needs another free route. */

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

  if (b.probe) {
    const res: any = await ad.pages(offset, 1);
    return json({ ok: true, probe: true, state, source: ad.source, head: res.head || null, rows: res.rows.length, sample: res.rows.slice(0, 3).map((r: Row) => ({ ...r, raw: undefined })), types: [...new Set(res.rows.map((r: Row) => `${r.license_type} => ${r.on_premise}`))].slice(0, 40) });
  }
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
