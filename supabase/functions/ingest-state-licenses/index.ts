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
   v7: streaming xlsx reader (sheet1 + sharedStrings via fflate), CSV preamble lines skipped (CA banner).
   v6: memory-safe readers (streamed zip/CSV window; xlsx dense + sheetRows), ZIP+4 with a dash.
   v5: CT and VA adapters removed (see notes), KY NQ4/caterer and DC 'Retail -' classes fixed.
   v4: + MI (master xlsx), WA (weekly On Premise xlsx), CA (daily zipped CSV), ME (FOAA xlsx); download links are
   discovered on each state's page because the file names change.
   v11: + CT (DCP permits, LBD excluded), RI (DOH ArcGIS), ID (ISP CSV), NE, GA, NJ (xlsx; GA/NJ need a browser UA), OK
   (ABLE HTML-table lists). v10: MI Number/Group/combined address. v9: CO. v8: CA key file-no + type, more date formats.
   v12: rules enforced in the DB (active on-premise only); NJ inactivity -> inactive; NE class codes; GA ID/name; CT prefixes.
   Never calls a paid service. */

const PAGE = 1000;
/* GA/NJ serve their public files only to browser user agents (no challenge, no login) */
const BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36 PHG-license-ingest";
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
/* last 5-digit ZIP in the text: "97203-3731", "601882117", "OR 97203" -> 5 digits (v6: dash ZIP+4 accepted) */
const zip5 = (v: unknown) => { const all = [...String(v ?? "").matchAll(/(?:^|\D)(\d{5})(?:-?\d{4})?(?=\D|$)/g)]; return all.length ? all[all.length - 1][1] : null; };
const isoDate = (v: unknown) => {
  const s = String(v ?? "").trim(); if (!s) return null;
  let m = s.match(/^(\d{4})-(\d{2})-(\d{2})/); if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/); if (m) return `${m[3]}-${m[1].padStart(2, "0")}-${m[2].padStart(2, "0")}`;
  m = s.match(/^(\d{4})(\d{2})(\d{2})$/); if (m && +m[2] >= 1 && +m[2] <= 12) return `${m[1]}-${m[2]}-${m[3]}`;
  m = s.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);
  if (m) { const mo = "JANFEBMARAPRMAYJUNJULAUGSEPOCTNOVDEC".indexOf(m[2].toUpperCase()) / 3 + 1; if (mo >= 1) return `${m[3]}-${String(mo).padStart(2, "0")}-${m[1].padStart(2, "0")}`; }
  if (/^\d{5}(\.\d+)?$/.test(s) && +s > 20000 && +s < 80000) return new Date(Math.round((+s - 25569) * 86400000)).toISOString().slice(0, 10); // Excel serial
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
async function discover(page: string, re: RegExp, ua = "PHG-license-ingest/1.0"): Promise<string> {
  const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), 30000);
  try {
    const r = await fetch(page, { signal: ctl.signal, headers: { "User-Agent": ua } });
    if (!r.ok) throw new Error(`HTTP ${r.status} from ${new URL(page).host}`);
    const html = await r.text();
    const links = [...html.matchAll(/href="([^"]+)"/gi)].map((m) => m[1].replace(/&amp;/g, "&")).filter((h) => re.test(decodeURIComponent(h)));
    if (!links.length) throw new Error(`no download link matching ${re} on ${page}`);
    return new URL(links[links.length - 1], page).href;
  } finally { clearTimeout(tm); }
}
/* v6: memory-safe readers (the edge runtime has ~250 MB). Returns the header and only the rows in [from, from+count);
   done = the file has no rows after the window. Zipped CSV is streamed and parsing stops after the window. */
async function sheetRows(url: string, from: number, count: number, ua = "PHG-license-ingest/1.0"): Promise<{ head: string[]; rows: string[][]; done: boolean; pre?: string[][] }> {
  const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), 140000);
  try {
    const r = await fetch(url, { signal: ctl.signal, headers: { "User-Agent": ua } });
    if (!r.ok || !r.body) throw new Error(`HTTP ${r.status} from ${new URL(url).host}`);
    if (/\.zip(\?|$)/i.test(url)) return await zipCsvWindow(r.body, from, count, ctl);
    if (/\/csv(\?|$)|\.csv(\?|$)/i.test(url) || /text\/csv/i.test(r.headers.get("content-type") || "")) {
      // v11: plain CSV (ID); small files, parsed whole; header = first row naming a licence/permit
      const all = parseCsv(await r.text());
      const hi = Math.max(0, all.findIndex((row) => row.filter((x) => x.trim()).length >= 3 && row.some((x) => /licen|permit/i.test(x))));
      const body = all.slice(hi + 1).filter((row) => row.length > 1);
      return { head: (all[hi] || []).map((x) => x.trim()), rows: body.slice(from, from + count), done: from + count >= body.length };
    }
    return await xlsxWindow(r.body, from, count);
  } finally { clearTimeout(tm); }
}

/* v7: streaming .xlsx reader (SheetJS keeps the whole workbook in memory; state lists are too big for the edge
   runtime). An .xlsx is a zip of XML: the first worksheet is streamed row by row and only the header candidates and
   the requested window are kept (as raw cell values); shared strings are resolved at the end. */
async function xlsxWindow(stream: ReadableStream<Uint8Array>, from: number, count: number) {
  const { Unzip, UnzipInflate } = await import("npm:fflate@0.8.2");
  const dec = new TextDecoder();
  const unesc = (x: string) => x.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&#(\d+);/g, (_, d) => String.fromCharCode(+d)).replace(/&amp;/g, "&");
  const colIdx = (ref: string) => { const m = ref.match(/^([A-Z]+)/); let n = 0; if (m) for (const ch of m[1]) n = n * 26 + ch.charCodeAt(0) - 64; return n - 1; };
  type Cell = { t: string; v: string };
  const pre: Cell[][] = []; let nRows = 0; let headAt = -1;
  let sst: string[] = []; let sstText = ""; let sheetBuf = "";
  const isHead = (cells: Cell[], strs: (c: Cell) => string) => {
    const vals = cells.map((c) => strs(c).trim()).filter(Boolean);
    return (vals.length >= 3 && vals.some((v) => /licen|permit|\blic\b/i.test(v)))
      || (vals.length >= 5 && vals.every((v) => v.length <= 40 && /[A-Za-z]/.test(v) && !/^\d[\d\s\/.-]*$/.test(v)) && vals.some((v) => /name|address|city|type|number|no\.?$/i.test(v)));
  };
  const takeRow = (xml: string) => {
    const cells: Cell[] = [];
    for (const m of xml.matchAll(/<c\b([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g)) {
      const attrs = m[1] || ""; const inner = m[2] || "";
      const ref = (attrs.match(/\br="([A-Z]+\d+)"/) || [])[1] || ""; const t = (attrs.match(/\bt="(\w+)"/) || [])[1] || "n";
      const v = t === "inlineStr" ? [...inner.matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map((x) => x[1]).join("") : ((inner.match(/<v>([\s\S]*?)<\/v>/) || [])[1] || "");
      cells[ref ? colIdx(ref) : cells.length] = { t, v: unesc(v) };
    }
    for (let i = 0; i < cells.length; i++) if (!cells[i]) cells[i] = { t: "n", v: "" };
    if (nRows < 40) pre.push(cells);
    nRows++;
    return cells;
  };
  // the header row is found at the end (shared strings may arrive after the sheet), so keep every row whose sheet
  // index could fall in the window for any header position in the first 40 rows
  const keep: { si: number; cells: Cell[] }[] = [];
  const feedSheet = (text: string, final: boolean) => {
    sheetBuf += text;
    let end: number;
    while ((end = sheetBuf.indexOf("</row>")) >= 0) {
      const start = sheetBuf.lastIndexOf("<row", end);
      const si = nRows;
      const cells = takeRow(sheetBuf.slice(start, end));
      sheetBuf = sheetBuf.slice(end + 6);
      if (si >= from && si < from + count + 41) keep.push({ si, cells });
    }
    if (final) sheetBuf = "";
  };
  await new Promise<void>((resolve, reject) => {
    let open = 0; let ended = false;
    const maybeDone = () => { if (ended && open === 0) resolve(); };
    const uz = new Unzip((file: any) => {
      const isSheet = /^xl\/worksheets\/sheet1\.xml$/i.test(file.name), isSst = /^xl\/sharedStrings\.xml$/i.test(file.name);
      if (!isSheet && !isSst) return;
      open++;
      file.ondata = (err: any, chunk: Uint8Array, final: boolean) => {
        if (err) return reject(err);
        const text = dec.decode(chunk, { stream: !final });
        if (isSst) sstText += text; else feedSheet(text, final);
        if (final) { open--; maybeDone(); }
      };
      file.start();
    });
    uz.register(UnzipInflate);
    (async () => {
      const rd = stream.getReader();
      try { for (;;) { const { value, done } = await rd.read(); if (done) { uz.push(new Uint8Array(0), true); break; } uz.push(value); } ended = true; maybeDone(); }
      catch (e) { reject(e); }
    })();
  });
  sst = [...sstText.matchAll(/<si>([\s\S]*?)<\/si>/g)].map((m) => unesc([...m[1].matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map((x) => x[1]).join("")));
  sstText = "";
  const str = (c: Cell) => (c.t === "s" ? (sst[+c.v] ?? "") : c.v);
  // header: first of the first 40 rows that looks like one; body index = sheet index - headAt - 1
  headAt = pre.findIndex((r) => isHead(r, str));
  if (headAt < 0) headAt = 0;
  const rows = keep.filter((k) => k.si - headAt - 1 >= from && k.si - headAt - 1 < from + count).map((k) => k.cells.map(str));
  return { head: (pre[headAt] || []).map(str).map((x) => x.trim()), rows, done: nRows - headAt - 1 <= from + count,
    pre: pre.slice(0, 12).map((r) => r.slice(0, 10).map(str).map((x) => x.slice(0, 40))) };
}

async function zipCsvWindow(stream: ReadableStream<Uint8Array>, from: number, count: number, ctl: AbortController) {
  const { Unzip, UnzipInflate } = await import("npm:fflate@0.8.2");
  const dec = new TextDecoder();
  let head: string[] | null = null; const rows: string[][] = []; let idx = 0; let stop = false; let finished = false;
  let row: string[] = []; let f = ""; let q = false; let sep: string | null = null; let prev = "";
  const emit = () => {
    row.push(f); f = "";
    if (!head) { if (row.filter((x) => x.trim()).length >= 3 && row.some((x) => /licen|permit/i.test(x))) head = row.map((x) => x.trim()); }
    else if (row.length > 1) { if (idx >= from && idx < from + count) rows.push(row); idx++; if (idx >= from + count) stop = true; }
    row = [];
  };
  const feed = (text: string) => {
    if (sep === null) { const nl = (prev + text).indexOf("\n"); if (nl < 0) { prev += text; return; } const first = (prev + text).slice(0, nl); sep = first.includes("\t") && !first.includes(",") ? "\t" : ","; text = prev + text; prev = ""; }
    for (let i = 0; i < text.length && !stop; i++) {
      const c = text[i];
      if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
      else if (c === '"' && sep === ",") q = true;
      else if (c === sep) { row.push(f); f = ""; }
      else if (c === "\n") emit();
      else if (c !== "\r") f += c;
    }
  };
  await new Promise<void>((resolve, reject) => {
    let picked = false;
    const uz = new Unzip((file: any) => {
      if (picked || !/\.(csv|txt)$/i.test(file.name)) return;
      picked = true;
      file.ondata = (err: any, chunk: Uint8Array, final: boolean) => {
        if (err) return reject(err);
        if (!stop) feed(dec.decode(chunk, { stream: !final }));
        if (final) { if (!stop && (f || row.length)) emit(); finished = !stop; resolve(); }
        else if (stop) resolve();
      };
      file.start();
    });
    uz.register(UnzipInflate);
    (async () => {
      const rd = stream.getReader();
      try {
        for (;;) {
          if (stop) { try { ctl.abort(); } catch { /* done */ } break; }
          const { value, done } = await rd.read();
          if (done) { uz.push(new Uint8Array(0), true); break; }
          uz.push(value);
        }
        if (!picked) reject(new Error("zip has no csv"));
      } catch (e) { if (!stop) reject(e); }
    })();
  });
  return { head: head || [], rows, done: finished };
}
function col(head: string[], ...res: RegExp[]) { for (const re of res) { const i = head.findIndex((h) => re.test(h)); if (i >= 0) return i; } return -1; }
function sheetAdapter(state: string, url: string | (() => Promise<string>), source: string, onPremise: (type: string, row: string) => boolean | null, keyByType = false, o: { ua?: string; type?: RegExp[] } = {}): Adapter {
  return {
    source,
    async pages(offset, pages) {
      const { head, rows: win, done, pre } = await sheetRows(typeof url === "string" ? url : await url(), offset, pages * PAGE, o.ua);
      const iNo = col(head, /licen[cs]e\s*(no|num|#|id)/i, /permit\s*(no|num|#)/i, /^licen[cs]e$/i, /file\s*(no|num)/i, /lic(ense)?\s*#/i, /^(licen[cs]e\s*)?number$/i, /^id$/i);
      const iType = col(head, ...(o.type || []), /licen[cs]e\s*(type|class|desc|privilege)/i, /privilege/i, /^type$/i, /class/i);
      const iType2 = col(head, /secondary\s*licen[cs]e\s*type/i); // NE: "Catering (Secondary License)"
      const iInact = col(head, /inactiv/i); // NJ: pocket licences carry an "Inactivity Start Date"
      const iName = col(head, /trade|dba|doing business/i, /business\s*name/i, /premises?\s*name/i, /establishment/i, /primary\s*name/i, /^name$/i, /format\s*name/i, /name$/i);
      const iOwner = col(head, /licensee|^owner|owner\s*name|entity|applicant/i, /primary\s*name/i, /account\s*name/i); // not MI "Statute: Ownership Transferable\"
      const iGroup = col(head, /^group$/i); // MI: Retail - On Premises / Retail - Off Premises
      const iAddr = col(head, /(premise|physical|location|street)?\s*address(\s*1|\s*line\s*1)?$/i, /prem\w*\s*addr\w*\s*1?$/i, /street/i, /addr/i);
      const iCity = col(head, /city/i, /locality|town/i);
      const iZip = col(head, /zip|postal/i);
      const iCounty = col(head, /county/i);
      const iStatus = col(head, /status/i, /^licen[cs]e\s*state$/i);
      const iExp = col(head, /expir/i);
      const g = (r: string[], i: number) => (i >= 0 ? r[i] : "");
      const slice = win.filter((r) => g(r, iNo).trim());
      const rows = slice.map((r) => {
        const type = t([g(r, iGroup), g(r, iType), g(r, iType2)].filter((x) => String(x ?? "").trim()).join(" · ")) || "";
        const addr = String(g(r, iAddr) ?? "").replace(/_x000D_/g, " ").replace(/\s+/g, " ").trim();
        const cityCol = t(g(r, iCity));
        // "1620 Dodge St Ste 2200 Omaha, NE 68102" / "560 NEW JERSEY AVENUE ABSECON, NJ 08201 USA" -> street only
        const street = cityCol ? addr.replace(new RegExp(`\\s*,?\\s*${cityCol.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*,\\s*${state}\\b[\\s\\d-]*(USA|United States)?\\s*$`, "i"), "") : addr; // MI: "5160 N Hubbard Lake Rd, Spruce, MI 48762" (no city/zip columns)
        const addrCity = iCity < 0 ? (addr.match(/,\s*([^,]+),\s*[A-Z]{2}\s*\d{5}/) || [])[1] : undefined;
        return {
          state, license_no: keyByType && type ? `${t(g(r, iNo))}-${type}` : t(g(r, iNo)), license_type: type || null, on_premise: type ? onPremise(type, r.join(" | ")) : null,
          status: String(g(r, iInact) ?? "").trim() ? "inactive" : t(g(r, iStatus)) || "active", business_name: t(g(r, iName)) || t(g(r, iOwner)), owner_name: t(g(r, iOwner)),
          address: iCity < 0 ? t(addr.replace(/,\s*[^,]+,\s*[A-Z]{2}\s*[\d-]*\s*(United States)?\s*$/i, "")) : t(street), city: cityCol || t(addrCity),
          zip: zip5(iZip >= 0 ? g(r, iZip) : addr), county: t(g(r, iCounty)), expires_on: isoDate(g(r, iExp)),
          raw: Object.fromEntries(head.map((h, i) => [h || `col${i}`, r[i]])),
        } as Row;
      });
      return { rows, done, head, pre } as any;
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
    (type) => /on[- ]premises?/i.test(type) ? true : /off[- ]premises?|wholesal|manufactur|supplier|vendor/i.test(type) ? false
      : /class c|tavern|b-hotel|a-hotel|club|brewpub|micro ?brew|resort/i.test(type) ? true : /\bSD[MD]\b|specially designated/i.test(type) ? false : null),
  /* Washington LCB weekly "On Premise" list: every row is an on-premise licensee */
  WA: sheetAdapter("WA", () => discover("https://lcb.wa.gov/records/frequently-requested-lists", /On ?Premise ?\d+\.xlsx/i), "wa_lcb_onpremise_xlsx", () => true),
  /* California ABC daily export (zipped CSV); on-sale types 40-42, 47-49, 51-52, 57, 59-61, 67-68, 70, 75 */
  CA: sheetAdapter("CA", () => discover("https://www.abc.ca.gov/licensing/licensing-reports/", /DailyExport-CSV\.zip/i), "ca_abc_daily_csv",
    (type) => { const m = type.match(/\b(\d{2})\b/); if (!m) return null; const c = +m[1];
      return [40, 41, 42, 47, 48, 49, 51, 52, 57, 59, 60, 61, 67, 68, 70, 75].includes(c) ? true : [20, 21, 17, 9, 1, 2, 3, 4, 13, 14, 22, 23, 12].includes(c) ? false : null; }, true),
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
  /* Colorado LED "Liquor Licenses in Colorado" (data.colorado.gov ier5-5ms2, ~20k rows). FMB-and-Wine = grocery/off-premise;
     Takeout & Delivery permits ride on an on-premise licence (same venue) -> null so venues are not double counted. */
  CO: socrata("data.colorado.gov", "ier5-5ms2", "state = 'CO'", (r) => {
    const type = t(r.license_type) || "";
    const on = !type ? null
      : /retail liquor store|drug store|malt beverage and wine|wholesal|importer|manufacturer|direct shipper|^delivery permit|warehouse|master file|manager permit|limited winery/i.test(type) ? false
      : /hotel & restaurant|tavern|beer & wine|brew ?pub|club license|entertainment facility|lodging facility|arts license|malt beverage on|vintner|distillery pub|resort complex|campus liquor|racetrack|gaming tavern|public transportation|bed & breakfast|optional premises/i.test(type) ? true
      : null;
    return {
      state: "CO", license_no: t(r.license_number), license_type: type || null, on_premise: on, status: "active",
      business_name: t(r.doing_business_as) || t(r.licensee_name), owner_name: t(r.licensee_name),
      address: t(r.street_address), city: t(r.city), zip: zip5(r.zip), expires_on: isoDate(r.expiration), raw: r,
    };
  }, "co_led_socrata"),
  /* v11 (2026-09-29) sources found by the free-source sweep (Socrata/ArcGIS catalogues + state pages) */
  /* CT DCP liquor permits: credential prefix = permit class; LBD.* = brand registrations (excluded) */
  CT: socrata("data.ct.gov", "gwv2-eswx", "status = 'ACTIVE' AND NOT starts_with(credential, 'LBD') AND permit_state = 'CT'", (r) => {
    const cred = t(r.credential) || ""; const pfx = cred.split(".")[0].toUpperCase();
    const on = /^(LIR|LRW|LRB|LIC|LIT|LIH|LSC|LBP|LCT|LCE|LIU|LIN|LIB|LIA|LBW|LRE|LHW|LIV|LIS|LCA|LPC|LRC|LTH|LCM|LCS|LPA|LCW|LSE|LCN|LRS|LMI)$/.test(pfx) ? true
      : /^(LIP|LIG|LIW|LIM|LIO|LIF|LOS|LSH|LBR|LWS|LDS|LMF|LCL|LGB|LMB|LCR|LFW|LMW|LMS|LWG|LFM|LWB|LTR|LID|LAU|LWH|LFO|LTN|LFP)$/.test(pfx) ? false : null;
    return {
      state: "CT", license_no: cred || null, license_type: pfx || null, on_premise: on, status: t(r.status),
      business_name: t(r.dba) || t(r.backer), owner_name: t(r.backer) || t(r.permittee_name), address: t(r.permit_address),
      city: t(r.permit_city), zip: zip5(r.permit_zip), issued_on: isoDate(r.effective_date), expires_on: isoDate(r.expire_date), raw: r,
    };
  }, "ct_dcp_socrata"),
  /* RI Health Dept verified alcohol outlets (geocoded, Mar 2025; no licence number -> ObjectID key) */
  RI: arcgis("https://services1.arcgis.com/dkWT1XL4nglP5MLP/arcgis/rest/services/Verified_Alcohol_Outlets_in_Rhode_Island/FeatureServer/0", "1=1", (a) => {
    const oo = String(a.USER_On_Off_premesis ?? "");
    return {
      state: "RI", license_no: a.ObjectID != null ? `RI-${a.ObjectID}` : null, license_type: t([a.USER_License_Class, a.USER_Location_Type].filter(Boolean).join(" · ")),
      on_premise: /^\s*on/i.test(oo) ? true : /^\s*off/i.test(oo) ? false : null, status: "active",
      business_name: t(a.USER_Name), address: t(a.USER_Address), city: t(a.USER_City) || t(a.City), zip: zip5(a.USER_Zip_Code || a.ZIP || a.Match_addr), county: t(a.County),
      raw: a,
    };
  }, "ri_doh_arcgis"),
  /* Idaho State Police ABC: issued licences CSV (slow endpoint) */
  ID: sheetAdapter("ID", "https://apps.isp.idaho.gov/AbcReporting/license/search/csv?status=ISSUED", "id_isp_abc_csv",
    (_type, row) => /on[- ]premises?\s*consumption|by the drink/i.test(row) ? true : false),
  /* Nebraska LCC active licence roster (date-stamped xlsx) */
  NE: sheetAdapter("NE", () => discover("https://lcc.nebraska.gov/licensing-sdl/active-license-roster", /Active.*Roster.*\.xlsx/i), "ne_lcc_xlsx",
    (type) => { const code = (type.match(/^\s*([A-Z]{1,3})\b/) || [])[1] || "";
      return /shipper|wholesal/i.test(type) ? false : /[ACI]/.test(code) ? true : code ? false : null; }, false, { type: [/^class$/i] }),
  /* Georgia DOR active alcohol accounts (xlsx; browser UA) */
  GA: sheetAdapter("GA", () => discover("https://dor.georgia.gov/active-alcohol-licenses", /alcohol-accounts-active[^"]*xlsx/i, BROWSER_UA), "ga_dor_xlsx",
    (type) => /consumption|on[- ]?premise|pouring|by the drink/i.test(type) ? true
      : /package|wholesal|manufactur|distribut|broker|shipper|importer|retail|brewery|winery|distill/i.test(type) ? false : null, false, { ua: BROWSER_UA }),
  /* New Jersey ABC retail licence report (xlsx; browser UA): 31 club, 32 seasonal, 33 plenary consumption, 36 hotel */
  NJ: sheetAdapter("NJ", () => discover("https://www.njoag.gov/about/divisions-and-offices/division-of-alcoholic-beverage-control-home/licensing-bureau-applications-and-information/licensing-reports/", /RETAIL-LICENSE-REPORT[^"]*\.xlsx/i, BROWSER_UA), "nj_abc_xlsx",
    (type) => /consumption|club|hotel|motel|seasonal|theat|stadium|\b3[1236]\b/i.test(type) ? true : /distribution|limited retail|\b44\b|\b34\b/i.test(type) ? false : null, false, { ua: BROWSER_UA }),
  /* Oklahoma ABLE licensee lists by type (HTML tables served as .xls); every listed type is on-premise */
  OK: {
    source: "ok_able_xls",
    async pages(_offset, _pages) {
      const idx = "https://oklahoma.gov/able-commission/brand-registration/brand-registration-reports/listing-of-licensees-by-license-type.html";
      const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), 120000);
      const rows: Row[] = []; let okHead: string[] = [];
      try {
        const html = await (await fetch(idx, { signal: ctl.signal, headers: { "User-Agent": BROWSER_UA } })).text();
        const want = /(Mixed_Beverage_Licensee|Mixed_Beverage_Fraternal|Beer_and_Wine|Hotel_Beverage|Brew_Pub)[^"\/]*\.xls/i;
        const links = [...new Set([...html.matchAll(/href="([^"]+\.xls)"/gi)].map((m) => new URL(m[1], idx).href).filter((h) => want.test(h)))];
        if (!links.length) throw new Error("no OK licensee lists on the index page");
        for (const link of links) {
          let text = await (await fetch(link, { signal: ctl.signal, headers: { "User-Agent": BROWSER_UA } })).text();
          if (/quoted-printable/i.test(text)) text = text.replace(/=\r?\n/g, "").replace(/=([0-9A-F]{2})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
          const cellText = (x: string) => t(x.replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&#39;/g, "'")) || "";
          const trs = [...text.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/gi)].map((m) => [...m[1].matchAll(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi)].map((c) => cellText(c[1])));
          const hi = trs.findIndex((r) => r.some((c) => /licen[cs]e\s*(#|no|num)/i.test(c)));
          if (hi < 0) continue;
          const head = trs[hi]; if (!okHead.length) okHead = head; const ix = (re: RegExp) => head.findIndex((h) => re.test(h));
          const iNo = ix(/licen[cs]e\s*(#|no|num)/i), iDba = ix(/dba|trade|business/i), iAddr = ix(/addr|street|location/i), iCity = ix(/city/i), iZip = ix(/zip/i), iCounty = ix(/county/i), iExp = ix(/expir/i), iName = ix(/licensee|owner|name/i);
          const kind = (link.match(want) || [])[1]?.replace(/_/g, " ") || "licensee";
          for (const r of trs.slice(hi + 1)) {
            const g = (i: number) => (i >= 0 ? r[i] : "");
            if (!g(iNo)) continue;
            rows.push({ state: "OK", license_no: t(g(iNo)), license_type: kind, on_premise: true, status: "active",
              business_name: t(g(iDba)) || t(g(iName)), owner_name: iName !== iDba ? t(g(iName)) : null, address: t(g(iAddr)), city: t(g(iCity)),
              zip: zip5(g(iZip)), county: t(g(iCounty)), expires_on: isoDate(g(iExp)), raw: Object.fromEntries(head.map((h, i) => [h || `col${i}`, r[i]])) });
          }
        }
      } finally { clearTimeout(tm); }
      return { rows, done: true, head: okHead } as any;
    },
  },
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
    return json({ ok: true, probe: true, state, source: ad.source, head: res.head || null, pre: res.pre || null, rows: res.rows.length, sample: res.rows.slice(0, 3).map((r: Row) => ({ ...r, raw: undefined })), types: [...new Set(res.rows.map((r: Row) => `${r.license_type} => ${r.on_premise}`))].slice(0, 40) });
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
