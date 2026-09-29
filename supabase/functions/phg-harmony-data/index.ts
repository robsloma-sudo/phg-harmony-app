import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
import { SCHEMA_DOC } from "./schema_doc.ts";

/* PHG HARMONY DATA — lets Harmony show any PHG data in the Harmony view.

   The model never writes SQL. It only picks one entry from SOURCES (a fixed
   catalog of read-only, parameterised queries) plus parameters and a display
   container; this function runs that query with the service role and returns
   a "view" the app renders (map, bars, donut, table, tiles, profile card,
   recipe card) together with one spoken sentence built from the real numbers.
   Obvious requests (a NOM number, a ZIP code) skip the model entirely.

   Distillery coordinates: production_sites has no coordinates yet, so each
   NOM is placed at the centre of the municipality in its CRT registered
   address and flagged approx=true ("registered address, may be an office"). */

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (x: unknown, s = 200) =>
  new Response(JSON.stringify(x), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

/* v15 (Rob 2026-09-29): every failure is logged to phg.harmony_feedback (reviewed with the lead developer; fixes become
   phg.harmony_lessons, which the planner and the SQL writer read on every request - learning without a redeploy). */
function background(p: Promise<unknown>) {
  try { const er = (globalThis as any).EdgeRuntime; if (er?.waitUntil) { er.waitUntil(p); return; } } catch { /* fall through */ }
  p.catch(() => null);
}
function logFeedback(db: any, entry: Record<string, unknown>) {
  background(Promise.resolve(db.rpc("harmony_log_feedback", { p: { surface: "harmony-data", ...entry } })).catch(() => null));
}
const LESSONS: Record<string, { at: number; text: string }> = {};
async function lessons(db: any, scope: string): Promise<string> {
  const c = LESSONS[scope];
  if (c && Date.now() - c.at < 120000) return c.text;
  try { const { data } = await db.rpc("harmony_lessons_for", { p_scope: scope }); LESSONS[scope] = { at: Date.now(), text: String(data || "") }; }
  catch { LESSONS[scope] = { at: Date.now(), text: c?.text || "" }; }
  return LESSONS[scope].text;
}

/* municipality seat coordinates (lat, lng) for every town in the CRT addresses */
const MUNI: Record<string, [number, number]> = {
  "GUADALAJARA": [20.6767, -103.3475], "TEQUILA": [20.882, -103.8363], "AMATITAN": [20.834, -103.724],
  "ZAPOPAN": [20.7236, -103.3848], "ARANDAS": [20.7048, -102.3458], "EL ARENAL": [20.776, -103.692],
  "TEPATITLAN DE MORELOS": [20.817, -102.763], "ATOTONILCO EL ALTO": [20.551, -102.51],
  "SAN JUANITO DE ESCOBEDO": [20.8, -104.0], "JESUS MARIA": [20.609, -102.223],
  "TLAJOMULCO DE ZUÑIGA": [20.474, -103.443], "TLAJOMULCO DE ZUNIGA": [20.474, -103.443], "TEPIC": [21.5042, -104.8946],
  "SAN IGNACIO CERRO GORDO": [20.74, -102.51], "VILLA CORONA": [20.399, -103.689],
  "CUAUHTEMOC": [19.433, -99.147], "DEGOLLADO": [20.467, -102.154], "ALVARO OBREGON": [19.359, -99.204],
  "ZAPOTLAN DEL REY": [20.466, -102.926], "TLAQUEPAQUE": [20.641, -103.293], "MIGUEL HIDALGO": [19.432, -99.2],
  "IXTLAN DEL RIO": [21.035, -104.367], "TALA": [20.653, -103.701], "TOTOTLAN": [20.54, -102.79],
  "SAHUAYO": [20.058, -102.724], "UNION DE TULA": [19.957, -104.267], "AGUASCALIENTES": [21.881, -102.291],
  "VILLA HIDALGO": [21.676, -102.588], "HUANIMARO": [20.367, -101.499], "AMACUECA": [19.999, -103.6],
  "EL SALTO": [20.519, -103.181], "JUANACATLAN": [20.509, -103.169], "PURISIMA DEL RINCON": [21.035, -101.878],
  "AYOTLAN": [20.53, -102.336], "EL GRULLO": [19.806, -104.216], "JAMAY": [20.294, -102.709],
  "AUTLAN DE NAVARRO": [19.771, -104.365], "QUERETARO": [20.5888, -100.3899], "PENJAMO": [20.431, -101.722],
  "GONZALEZ": [22.828, -98.429], "BENITO JUAREZ": [19.372, -99.157], "MARCOS CASTELLANOS": [19.966, -103.017],
  "MARAVATIO": [19.894, -100.443], "ZAPOTLAN EL GRANDE": [19.704, -103.461], "TULTITLAN": [19.645, -99.169],
  "SAN MARTIN HIDALGO": [20.435, -103.928], "SAN JULIAN": [21.01, -102.172], "TIZAPAN EL ALTO": [20.16, -103.05],
  "CUAJIMALPA DE MORELOS": [19.357, -99.299], "ROMITA": [20.871, -101.516], "MAGDALENA": [20.911, -103.98],
  "TONAYA": [19.786, -103.972], "VALLE DE JUAREZ": [19.93, -102.943],
};
const STATE_CENTRE: Record<string, [number, number]> = {
  "JALISCO": [20.66, -103.35], "NAYARIT": [21.75, -104.85], "GUANAJUATO": [21.02, -101.26],
  "MICHOACAN DE OCAMPO": [19.57, -101.71], "TAMAULIPAS": [24.27, -98.84], "CIUDAD DE MÉXICO": [19.43, -99.13],
  "AGUASCALIENTES": [21.88, -102.29], "QUERETARO DE ARTEAGA": [20.59, -100.39], "MEXICO": [19.35, -99.63],
};
const STATE_NAMES: Record<string, string> = {
  AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California", CO: "Colorado", CT: "Connecticut", DE: "Delaware",
  DC: "Washington DC", FL: "Florida", GA: "Georgia", HI: "Hawaii", ID: "Idaho", IL: "Illinois", IN: "Indiana", IA: "Iowa", KS: "Kansas",
  KY: "Kentucky", LA: "Louisiana", ME: "Maine", MD: "Maryland", MA: "Massachusetts", MI: "Michigan", MN: "Minnesota", MS: "Mississippi",
  MO: "Missouri", MT: "Montana", NE: "Nebraska", NV: "Nevada", NH: "New Hampshire", NJ: "New Jersey", NM: "New Mexico", NY: "New York",
  NC: "North Carolina", ND: "North Dakota", OH: "Ohio", OK: "Oklahoma", OR: "Oregon", PA: "Pennsylvania", RI: "Rhode Island",
  SC: "South Carolina", SD: "South Dakota", TN: "Tennessee", TX: "Texas", UT: "Utah", VT: "Vermont", VA: "Virginia", WA: "Washington",
  WV: "West Virginia", WI: "Wisconsin", WY: "Wyoming",
};
/* "California" / "new jersey" / "NJ" -> "NJ" */
function stateCode(x: unknown): string {
  const v = String(x || "").trim(); if (!v) return "";
  if (/^[A-Za-z]{2}$/.test(v)) return v.toUpperCase();
  const hit = Object.entries(STATE_NAMES).find(([, n]) => n.toLowerCase() === v.toLowerCase());
  return hit ? hit[0] : v.slice(0, 2).toUpperCase();
}

function addressOf(notes: string | null) {
  const n = String(notes || "");
  const m = n.match(/Registered address[^:]*:\s*(.*?)\.\s*May be/i);
  const addr = m ? m[1].replace(/\s+/g, " ").trim() : "";
  const t = n.match(/C\.P\.\s*\d{5}\.?\s*\.?\s*([^,.]+),\s*([^.]+?)\.\s*May be/i);
  const muni = t ? t[1].trim().toUpperCase() : "";
  const state = t ? t[2].trim().toUpperCase() : "";
  const c = MUNI[muni] || STATE_CENTRE[state] || null;
  return { addr, muni, state, coord: c, approx: MUNI[muni] ? "municipality" : c ? "state" : null };
}
/* v8: product knowledge helpers (phg_know rows from public.phg_know_lookup) */
const STYLE_LABEL: Record<string, string> = { blanco: "Blanco", joven: "Joven", reposado: "Reposado", anejo: "Añejo", extra_anejo: "Extra Añejo", cristalino: "Cristalino", other: "Other" };
function knowLine(e: any): string {
  const aged = e.aging_months_min != null ? `aged ${e.aging_months_min}${e.aging_months_max != null && e.aging_months_max !== e.aging_months_min ? "–" + e.aging_months_max : ""} months${e.barrels ? " in " + e.barrels : ""}` : e.barrels ? `rested in ${e.barrels}` : "";
  return [e.agave_species || e.agave, e.cooking, e.milling, e.fermentation, e.distillation, aged, e.abv != null ? `${e.abv}% ABV` : "", e.additive_free === true ? "confirmed additive-free" : ""].filter(Boolean).join(", ");
}
function knowRows(b: any): string[][] {
  return [["Producer", b.producer], ["Owner", b.owner], ["Region", b.region], ["Founded", b.founded_year ? String(b.founded_year) : ""], ["History", (b.history || []).slice(0, 3).join(" · ")]].filter((r) => r[1]) as string[][];
}
function knowSections(list: any[]): any[] {
  return list.map((b: any) => ({
    title: `${b.name} · how it's made`,
    count: (b.expressions || []).length,
    items: [
      ...((b.history || []).length ? [{ name: "Story", sub: (b.history || []).slice(0, 4).join(" · "), value: b.founded_year ? String(b.founded_year) : "" }] : []),
      ...(b.expressions || []).map((e: any) => ({ name: e.name, value: e.price_usd_750 != null ? "$" + Number(e.price_usd_750).toFixed(0) : (STYLE_LABEL[e.style] || ""), sub: [knowLine(e), (e.tasting || []).length ? "Tastes of " + e.tasting.slice(0, 5).join(", ") : "", ...(e.notes || []).slice(0, 2)].filter(Boolean).join(" — ") })),
    ],
    empty: "No bottlings researched yet",
  }));
}
function knowNote(list: any[]): string {
  const src = new Map<string, any>(); list.forEach((b: any) => (b.sources || []).forEach((x: any) => { if (x?.title) src.set(x.title, x); }));
  const v = list.some((b: any) => b.verification === "page") ? "checked on the source pages" : "from source excerpts, not yet checked page by page";
  return `Production and tasting facts ${v}. Sources: ${[...src.keys()].slice(0, 5).join(", ") || "PHG research"}.`;
}
const title = (s: string) => s.toLowerCase().replace(/(^|[\s(\-/])([a-zà-ÿ])/g, (_a, p, ch) => p + ch.toUpperCase());
const money = (n: unknown) => (n == null || !isFinite(Number(n)) ? null : Math.round(Number(n) * 100) / 100);
/* legal-form suffix only: ", S.A. DE C.V.", "SAPI DE CV", "S. DE R.L. DE C.V." - never "CASA" or "SAN" */
const LEGAL = /,?\s+(S\.?\s?A\.?(\s?P\.?\s?I\.?)?|S\.?\s?DE\s+R\.?\s?L\.?|S\.?\s?C\.?)(\s+DE\s+C\.?\s?V\.?)?\.?\s*$/i;
const esc = (s: string) => s.replace(/[%_,()]/g, " ").trim();
/* v13: refinable views. Numeric filters arrive as strings from the planner ("" = unused). */
const num = (v: unknown): number | null => { const t = String(v ?? "").trim().toLowerCase().replace(/[$,\s]/g, ""); const m = t.match(/^(-?\d+(?:\.\d+)?)(k)?$/); if (!m) return null; const n = parseFloat(m[1]) * (m[2] ? 1000 : 1); return isFinite(n) ? n : null; };
const truthy = (v: unknown) => /^(1|true|yes|y|on)$/i.test(String(v ?? "").trim());
/* shared price / census filters for mv_drink_explorer queries */
function drinkFilters(q: any, p: P) {
  const lo = num(p.price_min), hi = num(p.price_max), inc = num(p.income_min), incHi = num(p.income_max), ageLo = num(p.age_min), ageHi = num(p.age_max);
  if (lo != null) q = q.gte("item_price", lo);
  if (hi != null) q = q.lte("item_price", hi);
  if (inc != null) q = q.gte("income", inc);
  if (incHi != null) q = q.lte("income", incHi);
  if (ageLo != null) q = q.gte("median_age", ageLo);
  if (ageHi != null) q = q.lte("median_age", ageHi);
  if (p.venue_type) q = q.ilike("venue_type", `%${esc(p.venue_type)}%`);
  return q;
}
function filterWords(p: P) {
  const w: string[] = [];
  const lo = num(p.price_min), hi = num(p.price_max), inc = num(p.income_min), incHi = num(p.income_max), ageHi = num(p.age_max), ageLo = num(p.age_min);
  if (lo != null && hi != null) w.push(`$${lo}–$${hi}`); else if (hi != null) w.push(`under $${hi}`); else if (lo != null) w.push(`over $${lo}`);
  if (inc != null) w.push(`income over $${Math.round(inc / 1000)}k`);
  if (incHi != null) w.push(`income under $${Math.round(incHi / 1000)}k`);
  if (ageHi != null) w.push(`median age under ${ageHi}`);
  if (ageLo != null) w.push(`median age over ${ageLo}`);
  if (p.venue_type) w.push(String(p.venue_type));
  return w.join(", ");
}
function sortRows(rows: any[], sort: string) {
  const by: Record<string, (a: any, b: any) => number> = {
    price_asc: (a, b) => a.item_price - b.item_price, price_desc: (a, b) => b.item_price - a.item_price,
    income_desc: (a, b) => (b.income || 0) - (a.income || 0), income_asc: (a, b) => (a.income || 9e9) - (b.income || 9e9),
    rating_desc: (a, b) => (b.rating || 0) - (a.rating || 0), name: (a, b) => String(a.venue).localeCompare(String(b.venue)),
    city: (a, b) => String(a.city).localeCompare(String(b.city)),
  };
  return by[sort] ? [...rows].sort(by[sort]) : rows;
}

/* ---------------- the catalog ---------------- */
type P = Record<string, any>;
type View = Record<string, any>;
type Result = { speak: string; view: View };

const SOURCES: Record<string, { about: string; run: (db: any, p: P) => Promise<Result> }> = {
  distillery: {
    about: "One tequila/mezcal distillery by NOM number or producer name: map pin in Mexico + profile card with its brands.",
    async run(db, p) {
      let q = db.from("organizations").select("id,organization_name,nom,notes,organization_types,verified_at").not("nom", "is", null).limit(8);
      const nom = String(p.nom || "").replace(/\D/g, "");
      if (nom) q = q.eq("nom", nom);
      else if (p.q) q = q.ilike("organization_name", `%${esc(p.q)}%`);
      else throw new Error("say a NOM number or a producer name");
      const { data: orgs, error } = await q;
      if (error) throw error;
      if (!orgs?.length) {
        // brand name -> its NOM
        if (p.q) {
          const { data: br } = await db.from("brands").select("brand_name,primary_nom").ilike("brand_name", `%${esc(p.q)}%`).not("primary_nom", "is", null).limit(1);
          if (br?.length) return SOURCES.distillery.run(db, { nom: br[0].primary_nom });
        }
        return { speak: `I could not find ${nom ? "NOM " + nom : p.q} in the tequila distillery register.`, view: { type: "empty", title: "Not found" } };
      }
      const o = orgs[0], a = addressOf(o.notes);
      const { data: brands } = await db.from("brands").select("brand_name,category,brand_status").eq("primary_nom", o.nom).order("brand_name").limit(40);
      const names = (brands || []).map((b: any) => b.brand_name);
      const name = title(String(o.organization_name).replace(LEGAL, ""));
      const pins = a.coord ? [{ lat: a.coord[0], lng: a.coord[1], label: `NOM ${o.nom} · ${name}`, sub: a.muni ? title(a.muni) + ", " + title(a.state) : "", approx: a.approx }] : [];
      return {
        speak: `NOM ${o.nom} is ${name}${a.muni ? `, registered in ${title(a.muni)}, ${title(a.state)}` : ""}.` +
          (names.length ? ` It makes ${names.length} brand${names.length > 1 ? "s" : ""} we track, including ${names.slice(0, 3).join(", ")}.` : "") +
          (a.approx ? " The pin is the town centre of its registered address, which may be an office." : ""),
        view: {
          type: "map", title: `NOM ${o.nom} · ${name}`, pins, focus: a.coord ? { lat: a.coord[0], lng: a.coord[1], zoom: a.approx === "state" ? 7 : 11 } : null, region: "MX",
          card: { kind: "profile", title: name, badge: `NOM ${o.nom}`, rows: [["Legal name", o.organization_name], ["Registered address", a.addr || "—"], ["Town", a.muni ? title(a.muni) + ", " + title(a.state) : "—"], ["Register", "CRT, verified " + (o.verified_at || "")]], chips: names, note: "Location is the municipality centre of the registered address (may be an office, not the distillery)." },
        },
      };
    },
  },
  distilleries: {
    about: "All NOM distilleries, optionally in one Mexican town or state (e.g. Arandas, Tequila, Jalisco): map of pins + counts by town.",
    async run(db, p) {
      const { data, error } = await db.from("organizations").select("organization_name,nom,notes").not("nom", "is", null).limit(1000);
      if (error) throw error;
      const want = String(p.town || p.state || p.q || "").toUpperCase().trim();
      const rows = (data || []).map((o: any) => ({ o, a: addressOf(o.notes) })).filter((r: any) => r.a.coord && (!want || r.a.muni.includes(want) || r.a.state.includes(want)));
      const jitter = (i: number) => ((i * 7919) % 100) / 100 - 0.5;
      const pins = rows.map((r: any, i: number) => ({ lat: r.a.coord[0] + jitter(i) * 0.03, lng: r.a.coord[1] + jitter(i + 13) * 0.03, label: `NOM ${r.o.nom} · ${title(String(r.o.organization_name).replace(LEGAL, ""))}`, sub: title(r.a.muni), nom: r.o.nom }));
      const by: Record<string, number> = {};
      rows.forEach((r: any) => { const k = title(r.a.muni); by[k] = (by[k] || 0) + 1; });
      const bars = Object.entries(by).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([label, value]) => ({ label, value }));
      return {
        speak: `${rows.length} registered distilleries${want ? " in " + title(want) : ""}${bars.length > 1 ? `. The most are in ${bars[0].label} with ${bars[0].value}` : ""}.`,
        view: { type: "map", title: `Tequila distilleries${want ? " · " + title(want) : ""}`, pins, region: "MX", side: { type: "bars", title: "By town", bars } },
      };
    },
  },
  venues: {
    about: "Bars/restaurants we track in IA, CO, NY, filtered by city, state, venue type or name: map of pins.",
    async run(db, p) {
      let q = db.from("mv_dash_pins").select("venue,city,state_code,venue_type,rating,lat,lng,drink_items").not("lat", "is", null).limit(800);
      if (p.state) q = q.eq("state_code", String(p.state).toUpperCase().slice(0, 2));
      if (p.city) q = q.ilike("city", esc(p.city));
      if (p.venue_type) q = q.ilike("venue_type", `%${esc(p.venue_type)}%`);
      if (p.q) q = q.ilike("venue", `%${esc(p.q)}%`);
      if (truthy(p.with_menus)) q = q.gt("drink_items", 0);
      const { data, error } = await q.order("drink_items", { ascending: false });
      if (error) throw error;
      const pins = (data || []).map((v: any) => ({ lat: +v.lat, lng: +v.lng, label: v.venue, sub: `${v.city}, ${v.state_code}${v.venue_type ? " · " + v.venue_type : ""}${v.drink_items ? " · " + v.drink_items + " drinks" : ""}`, weight: v.drink_items || 0,
        city: v.city, state: v.state_code, venue_type: v.venue_type, rating: v.rating == null ? null : +v.rating, drinks: v.drink_items || 0 }));
      const where = [p.q, p.venue_type, p.city, p.state && (STATE_NAMES[String(p.state).toUpperCase()] || p.state)].filter(Boolean).join(", ");
      return { speak: pins.length ? `${pins.length}${pins.length >= 800 ? "+" : ""} venues${where ? " for " + where : ""} on the map.` : `No venues found${where ? " for " + where : ""}.`, view: { type: "map", title: `Venues${where ? " · " + where : ""}`, pins, region: "US" } };
    },
  },
  drink_prices: {
    about: "Prices of a drink or drink family (e.g. margarita, espresso martini, IPA, tequila) across menus, optionally in a city/state; group_by city, venue_type or venue: stat tiles + bars + sample table.",
    async run(db, p) {
      let q = db.from("mv_drink_explorer").select("item_name,item_price,venue,city,state_code,venue_type,family,drink_name,income,median_age,rating").not("item_price", "is", null).gt("item_price", 0).limit(4000);
      q = drinkFilters(q, p);
      if (p.q) q = q.or(`item_name.ilike."%${esc(p.q)}%",drink_name.ilike."%${esc(p.q)}%"`);
      if (p.family) q = q.eq("family", String(p.family).toLowerCase());
      if (p.state) q = q.eq("state_code", String(p.state).toUpperCase().slice(0, 2));
      if (p.city) q = q.ilike("city", esc(p.city));
      const { data, error } = await q;
      if (error) throw error;
      const rows = (data || []).filter((r: any) => r.item_price < 500);
      if (!rows.length) return { speak: `I found no priced ${p.q || p.family || "drinks"} on the menus we have${p.city ? " in " + p.city : ""}.`, view: { type: "empty", title: "No prices" } };
      const prices = rows.map((r: any) => +r.item_price).sort((a: number, b: number) => a - b);
      const avg = prices.reduce((a: number, b: number) => a + b, 0) / prices.length, med = prices[Math.floor(prices.length / 2)];
      /* typical range (10th-90th percentile) so a single odd listing doesn't set the range; the
         query is capped at the REST row limit, so say "over" when it hits it */
      const p10 = prices[Math.floor(prices.length * 0.1)], p90 = prices[Math.min(prices.length - 1, Math.floor(prices.length * 0.9))];
      const countSay = (data || []).length >= 1000 ? `over ${prices.length.toLocaleString("en-US")}` : prices.length.toLocaleString("en-US");
      const g = ["city", "venue_type", "venue", "state_code"].includes(p.group_by) ? p.group_by : "city";
      const agg: Record<string, number[]> = {};
      rows.forEach((r: any) => { const k = r[g] || "—"; (agg[k] = agg[k] || []).push(+r.item_price); });
      const bars = Object.entries(agg).filter(([, v]) => v.length >= (g === "venue" ? 1 : 3)).map(([label, v]) => ({ label, value: money(v.reduce((a, b) => a + b, 0) / v.length), n: v.length })).sort((a: any, b: any) => b.n - a.n).slice(0, 12).sort((a: any, b: any) => b.value - a.value);
      const what = p.q || p.family || "drinks";
      const fw = filterWords(p);
      const sorted = sortRows(rows, String(p.sort || ""));
      const off = Math.max(0, Math.floor(num(p.offset) || 0));
      return {
        speak: `Across ${countSay} ${what} listings with prices on our menus${p.city ? " in " + p.city : p.state ? " in " + (STATE_NAMES[String(p.state).toUpperCase()] || p.state) : ""}${fw ? " (" + fw + ")" : ""}, the average is $${avg.toFixed(2)} and the median $${med.toFixed(2)}; most are between $${p10} and $${p90}.`,
        view: {
          type: "dashboard", title: `${title(String(what))} prices${p.city ? " · " + p.city : p.state ? " · " + p.state : ""}${fw ? " · " + fw : ""}`,
          tiles: [{ label: "Average", value: "$" + avg.toFixed(2) }, { label: "Median", value: "$" + med.toFixed(2) }, { label: "Typical range", value: `$${p10}–$${p90}` }, { label: "Menu items", value: String(rows.length) }],
          bars: { title: `Average by ${g.replace("_code", "").replace("_", " ")}`, unit: "$", bars },
          table: { cols: ["Drink", "Price", "Venue", "City"], total: sorted.length, offset: off, rows: sorted.slice(off, off + 40).map((r: any) => [r.item_name, "$" + r.item_price, r.venue, r.city]) },
        },
      };
    },
  },
  drink_map: {
    about: "Map of the venues that serve a drink or drink family (e.g. margaritas, espresso martini, tequila), each pin with that venue's average price; accepts city/state/venue type and price / income / age filters.",
    async run(db, p) {
      let q = db.from("mv_drink_explorer").select("item_name,item_price,venue,venue_key,city,state_code,venue_type,lat,lng,income,median_age,rating,drink_name").not("lat", "is", null).not("item_price", "is", null).gt("item_price", 0).limit(5000);
      q = drinkFilters(q, p);
      if (p.q) q = q.or(`item_name.ilike."%${esc(p.q)}%",drink_name.ilike."%${esc(p.q)}%"`);
      if (p.family) q = q.eq("family", String(p.family).toLowerCase());
      if (p.state) q = q.eq("state_code", String(p.state).toUpperCase().slice(0, 2));
      if (p.city) q = q.ilike("city", esc(p.city));
      const { data, error } = await q;
      if (error) throw error;
      const byV: Record<string, any> = {};
      for (const r of (data || []) as any[]) {
        if (!(r.item_price < 500)) continue;
        const k = r.venue_key || r.venue;
        const v = byV[k] || (byV[k] = { lat: +r.lat, lng: +r.lng, label: r.venue, city: r.city, state: r.state_code, venue_type: r.venue_type, income: r.income == null ? null : +r.income, median_age: r.median_age == null ? null : +r.median_age, rating: r.rating == null ? null : +r.rating, prices: [] as number[], items: [] as string[] });
        v.prices.push(+r.item_price); if (v.items.length < 4) v.items.push(`${r.item_name} $${r.item_price}`);
      }
      let pins: any[] = Object.values(byV).map((v: any) => {
        const avg = money(v.prices.reduce((a: number, b: number) => a + b, 0) / v.prices.length)!;
        return { lat: v.lat, lng: v.lng, label: v.label, sub: `${v.city}, ${v.state} · avg $${avg.toFixed(2)} · ${v.items.join("; ")}`, weight: v.prices.length,
          city: v.city, state: v.state, venue_type: v.venue_type, price: avg, min_price: Math.min(...v.prices), items: v.prices.length, income: v.income, median_age: v.median_age, rating: v.rating };
      });
      const sort = String(p.sort || "");
      if (sort === "price_asc") pins.sort((a, b) => a.price - b.price); else if (sort === "price_desc") pins.sort((a, b) => b.price - a.price);
      else if (sort === "income_desc") pins.sort((a, b) => (b.income || 0) - (a.income || 0)); else pins.sort((a, b) => b.weight - a.weight);
      pins = pins.slice(0, 800);
      const what = p.q || p.family || "drinks", fw = filterWords(p);
      const where = p.city || (p.state && (STATE_NAMES[String(p.state).toUpperCase()] || p.state)) || "";
      if (!pins.length) return { speak: `No venues with ${what}${where ? " in " + where : ""}${fw ? " (" + fw + ")" : ""} on the menus we have.`, view: { type: "empty", title: "No venues" } };
      const prices = pins.map((x) => x.price).sort((a: number, b: number) => a - b);
      const avg = prices.reduce((a: number, b: number) => a + b, 0) / prices.length;
      return {
        speak: `${pins.length} venues serve ${what}${where ? " in " + where : ""}${fw ? " (" + fw + ")" : ""}; their average is $${avg.toFixed(2)}, from $${prices[0].toFixed(2)} to $${prices[prices.length - 1].toFixed(2)}.`,
        view: { type: "map", title: `${title(String(what))}${where ? " · " + where : ""}${fw ? " · " + fw : ""}`, pins, region: "US" },
      };
    },
  },
  category_share: {
    about: "Which spirit categories appear most on menus (tequila, whiskey, vodka...): donut + table with venues, brands and average price.",
    async run(db) {
      const { data, error } = await db.from("v_menu_category_share").select("*").not("spirit_category", "in", "(unknown,unclassified)").order("items", { ascending: false }).limit(20);
      if (error) throw error;
      const rows = data || [];
      return {
        speak: rows.length ? `${title(rows[0].spirit_category)} leads with ${rows[0].items} menu items across ${rows[0].venues} venues, then ${rows.slice(1, 3).map((r: any) => title(r.spirit_category)).join(" and ")}.` : "No category data yet.",
        view: { type: "donut", title: "Spirit categories on menus", slices: rows.slice(0, 9).map((r: any) => ({ label: title(r.spirit_category), value: +r.items })), table: { cols: ["Category", "Items", "Venues", "Brands", "Avg $"], rows: rows.map((r: any) => [title(r.spirit_category), r.items, r.venues, r.distinct_brands, r.avg_price ? "$" + (+r.avg_price).toFixed(2) : "—"]) } },
      };
    },
  },
  top_brands: {
    about: "Most-listed spirit brands on menus (optionally one brand's presence): ranked bars by venues, with menu items and average price.",
    async run(db, p) {
      let q = db.from("v_menu_brand_presence").select("*").order("venues", { ascending: false }).limit(p.q ? 10 : 20);
      if (p.q) q = q.ilike("brand_name", `%${esc(p.q)}%`);
      const { data, error } = await q;
      if (error) throw error;
      const rows = data || [];
      if (!rows.length) return { speak: `${p.q || "That brand"} does not show up on the menus we have read yet.`, view: { type: "empty", title: "No brand matches" } };
      return {
        speak: p.q ? `${rows[0].brand_name} is on ${rows[0].venues} venue menus in ${rows[0].menu_items} items${rows[0].avg_price ? `, averaging $${(+rows[0].avg_price).toFixed(2)}` : ""}.` : `${rows[0].brand_name} is the most-listed brand, on ${rows[0].venues} venue menus, followed by ${rows.slice(1, 3).map((r: any) => r.brand_name).join(" and ")}.`,
        view: { type: "bars", title: p.q ? `Brand presence · ${p.q}` : "Top brands on menus", bars: rows.map((r: any) => ({ label: r.brand_name, value: +r.venues, sub: `${r.menu_items} items${r.avg_price ? " · $" + (+r.avg_price).toFixed(2) : ""}` })), unit: " venues" },
      };
    },
  },
  cocktail_recipe: {
    about: "A classic cocktail's reference spec (build, glass, garnish, method) plus how often and at what price it appears on menus: recipe card.",
    async run(db, p) {
      const name = esc(String(p.q || ""));
      if (!name) throw new Error("which cocktail?");
      /* v5: pick the right spec. "manhattan" used to return whichever row came first ("Black Manhattan").
         Exact name wins, then names starting with it, then the shortest name containing it. */
      const { data } = await db.from("cocktail_reference").select("cocktail_name,base_spirit,profile,consensus_spec,method,glassware,garnish,harmony_build_family").ilike("cocktail_name", `%${name}%`).limit(25);
      const low = name.toLowerCase().trim();
      const rank = (n: string) => { const x = n.toLowerCase(); return x === low ? 0 : x.startsWith(low + " ") || x.startsWith(low) ? 1 : 2; };
      const cands = (data || []).slice().sort((a: any, b: any) => rank(a.cocktail_name) - rank(b.cocktail_name) || a.cocktail_name.length - b.cocktail_name.length);
      const r = cands[0];
      const variants = cands.slice(1).map((x: any) => x.cocktail_name);
      const { data: seen } = await db.from("mv_drink_explorer").select("drink_name,item_price").ilike("drink_name", `%${name}%`).not("item_price", "is", null).limit(3000);
      /* keep other named variants (e.g. Black Manhattan) out of this drink's price stats */
      const other = variants.map((v: string) => v.toLowerCase()).filter((v: string) => v !== low);
      const pr = (seen || []).filter((x: any) => !other.some((v: string) => String(x.drink_name || "").toLowerCase().includes(v)))
        .map((x: any) => +x.item_price).filter((x: number) => x > 0 && x < 200);
      const avg = pr.length ? pr.reduce((a: number, b: number) => a + b, 0) / pr.length : null;
      if (!r && !pr.length) return { speak: `I do not have a reference spec for ${p.q}.`, view: { type: "empty", title: "No spec" } };
      return {
        speak: (r ? `${r.cocktail_name}: ${r.consensus_spec || r.profile || ""}`.trim() : title(name)) + (pr.length ? ` It is on ${pr.length} menu listings we have read, averaging $${avg!.toFixed(2)}.` : "") + (variants.length ? ` I also have ${variants.slice(0, 4).join(", ")}.` : ""),
        view: { type: "recipe", title: r?.cocktail_name || title(name), spec: r?.consensus_spec || "", rows: r ? [["Base", r.base_spirit], ["Family", r.harmony_build_family], ["Method", r.method], ["Glass", r.glassware], ["Garnish", r.garnish], ["Profile", r.profile], ["Also", variants.slice(0, 6).join(", ")]].filter((x) => x[1]) : [], tiles: pr.length ? [{ label: "On menus", value: String(pr.length) }, { label: "Average", value: "$" + avg!.toFixed(2) }] : [] },
      };
    },
  },
  zip_demographics: {
    about: "Census (ACS) demographics for a US ZIP code: population, median age, income, share 21-34, households over $100k, degrees: stat tiles.",
    async run(db, p) {
      const z = String(p.zip || "").replace(/\D/g, "").slice(0, 5);
      if (z.length !== 5) throw new Error("say a five-digit ZIP code");
      const { data } = await db.from("phg_census_zcta").select("*").eq("zcta", z).limit(1);
      const c = data?.[0];
      if (!c) return { speak: `I do not have census data for ZIP ${z}. We loaded Iowa, Colorado and New York.`, view: { type: "empty", title: "No census data" } };
      const pct = (x: any) => (x == null ? "—" : (+x).toFixed(1) + "%");
      return {
        speak: `ZIP ${z} has about ${(+c.total_population).toLocaleString("en-US")} people, median age ${c.median_age}, and median household income $${(+c.median_household_income).toLocaleString("en-US")}.`,
        view: { type: "tiles", title: `ZIP ${z}${c.state ? " · " + c.state : ""} · ACS ${c.acs_vintage || ""}`, tiles: [{ label: "Population", value: (+c.total_population).toLocaleString("en-US") }, { label: "Median age", value: String(c.median_age) }, { label: "Median income", value: "$" + (+c.median_household_income).toLocaleString("en-US") }, { label: "Age 21–34", value: pct(c.pop_21_34_pct) }, { label: "Households $100k+", value: pct(c.households_over_100k_pct) }, { label: "Bachelor's+", value: pct(c.bachelors_or_higher_pct) }, { label: "Hispanic/Latino", value: pct(c.hispanic_latino_pct) }] },
      };
    },
  },
  /* v10: the menu pipeline, live (public.phg_pipeline_status): is it moving, how fast, what's waiting, any job failing */
  pipeline: {
    about: "The menu pipeline right now: are menus uploading, how many menus and venues came in the last hour, pages rendered, links and pages waiting, whether any pipeline job is failing, and per-state progress (venues, websites, menus read, still queued).",
    async run(db) {
      const { data, error } = await db.rpc("phg_pipeline_status");
      if (error) throw error;
      const p: any = data || {};
      const n = (x: any) => Number(x || 0).toLocaleString("en-US");
      const lh = p.last_hour || {}, q = p.queue || {}, t = p.totals || {};
      const mins = p.last_document_at ? Math.round((Date.now() - Date.parse(p.last_document_at)) / 60000) : null;
      const failing = (p.jobs || []).filter((j: any) => j.active && j.failed > 0 && j.failed >= j.ok);
      const moving = mins != null && mins <= 15;
      const states = (p.states || []) as any[];
      const speak = (moving ? `Menus are coming in. In the last hour ${n(lh.documents)} menu documents arrived for ${n(lh.venues_with_new_menu)} venues, and ${n(lh.pages_rendered)} pages were rendered.`
          : `The pipeline looks stalled: the last menu arrived ${mins == null ? "a long time" : mins + " minutes"} ago.`)
        + ` ${n(q.links_waiting)} links are waiting to be downloaded and ${n(q.pages_waiting)} pages are waiting to render.`
        + (failing.length ? ` Heads up: ${failing.map((j: any) => j.job.replace(/^gtt-|^phg-/, "").replace(/-/g, " ")).join(" and ")} ${failing.length === 1 ? "is" : "are"} failing.` : " All pipeline jobs are healthy.")
        + (states.length ? " " + states.map((r: any) => `${STATE_NAMES[r.state] || r.state}: ${n(r.menus_read)} menus read of ${n(r.websites)} venues with websites`).join("; ") + "." : "");
      return {
        speak,
        view: {
          type: "dashboard", title: "Menu pipeline · live",
          tiles: [
            { label: "Menus last hour", value: n(lh.documents) }, { label: "New venues last hour", value: n(lh.venues_with_new_menu) },
            { label: "Pages rendered last hour", value: n(lh.pages_rendered) }, { label: "Links waiting", value: n(q.links_waiting) },
            { label: "Pages waiting", value: n(q.pages_waiting) }, { label: "Menu documents", value: n(t.visual_documents) },
          ],
          bars: { title: "Menus read by state", bars: states.map((r: any) => ({ label: STATE_NAMES[r.state] || r.state, value: +r.menus_read, sub: `${n(r.websites)} with websites · ${n(r.menus_queue)} queued` })) },
          rows: (p.jobs || []).map((j: any) => [j.job, `${j.active ? "on" : "paused"} · ${j.ok} ok / ${j.failed} failed (15 min)`]),
        },
      };
    },
  },
  coverage: {
    about: "How much data PHG has: venues, websites, menus read, drink items, brands per state (IA, CO, NY): tiles + bars.",
    async run(db) {
      const { data, error } = await db.from("v_public_stats").select("*");
      if (error) throw error;
      const rows = data || [];
      const sum = (k: string) => rows.reduce((a: number, r: any) => a + (+r[k] || 0), 0);
      return {
        speak: `We track ${sum("venues").toLocaleString("en-US")} venues, have read ${sum("menus_read").toLocaleString("en-US")} menus and ${sum("drink_items").toLocaleString("en-US")} drink items across ${rows.length} states.`,
        view: { type: "dashboard", title: "PHG data coverage", tiles: [{ label: "Venues", value: sum("venues").toLocaleString("en-US") }, { label: "Websites", value: sum("websites").toLocaleString("en-US") }, { label: "Menus read", value: sum("menus_read").toLocaleString("en-US") }, { label: "Drink items", value: sum("drink_items").toLocaleString("en-US") }], bars: { title: "Drink items by state", bars: rows.map((r: any) => ({ label: STATE_NAMES[r.state_code] || r.state_code, value: +r.drink_items, sub: `${(+r.venues).toLocaleString("en-US")} venues` })) } },
      };
    },
  },
  licenses: {
    about: "Liquor licences (active, on-premise, not expired, one per venue) from state licence lists: coverage per state (states, licences, venues, live loading), one state's breakdown by city / licence type / county, or a list + map of licensed venues filtered by state, city, licence type or name.",
    async run(db, p) {
      const st = stateCode(p.state);
      if (st && (p.city || p.q || p.venue_type)) {
        const { data, error } = await db.rpc("phg_license_venues", { p_state: st, p_city: p.city || null, p_q: p.q || null, p_type: p.venue_type || null, p_limit: 800 });
        if (error) throw error;
        const rows = (data || []) as any[];
        const where = [p.city, STATE_NAMES[st] || st].filter(Boolean).join(", ");
        if (!rows.length) return { speak: `No active on-premise licences match${p.q ? " " + p.q : ""}${p.venue_type ? " (" + p.venue_type + ")" : ""} in ${where}.`, view: { type: "empty", title: "No licences" } };
        const pins = rows.filter((r) => r.lat != null && r.lng != null).map((r) => ({ lat: +r.lat, lng: +r.lng, label: r.business_name, sub: `${r.license_type || ""} · ${r.address || ""}, ${r.city || ""}` }));
        const table = { cols: ["Venue", "Licence type", "Address", "City", "ZIP", "Expires"], rows: rows.map((r) => [r.business_name, r.license_type, r.address, r.city, r.zip, r.expires_on || "—"]) };
        return {
          speak: `${rows.length}${rows.length >= 800 ? "+" : ""} active on-premise licensed venues${p.q ? " matching " + p.q : ""}${p.venue_type ? " with " + p.venue_type + " licences" : ""} in ${where}.`,
          view: pins.length > 20 ? { type: "map", title: `Licensed venues · ${where}`, pins, region: "US", table } : { type: "table", title: `Licensed venues · ${where}`, table },
        };
      }
      if (st) {
        const by = /type|class|kind/i.test(String(p.group_by || "")) ? "type" : /county/i.test(String(p.group_by || "")) ? "county" : "city";
        const [{ data: cov }, { data: br, error }] = await Promise.all([db.rpc("phg_license_coverage"), db.rpc("phg_license_breakdown", { p_state: st, p_by: by })]);
        if (error) throw error;
        const one = ((cov?.per_state || []) as any[]).find((r) => r.state === st);
        if (!one) return { speak: `We have no licence list for ${STATE_NAMES[st] || st} yet.`, view: { type: "empty", title: "Not loaded" } };
        const rows = (br || []) as any[];
        return {
          speak: `${STATE_NAMES[st] || st}: ${(+one.venues).toLocaleString("en-US")} active on-premise licensed venues${one.cities ? " in " + one.cities + " cities" : ""}${rows[0] ? "; the most are in " + rows[0].label + " (" + rows[0].venues + ")" : ""}.`,
          view: { type: "bars", title: `${STATE_NAMES[st] || st} · licensed venues by ${by}`, bars: rows.slice(0, 25).map((r) => ({ label: r.label, value: +r.venues })) },
        };
      }
      const { data: cov, error } = await db.rpc("phg_license_coverage");
      if (error) throw error;
      const per = (cov?.per_state || []) as any[];
      const loading = per.filter((r) => r.loading).map((r) => STATE_NAMES[r.state] || r.state);
      return {
        speak: `We have active on-premise liquor licences for ${cov.states} states: ${(+cov.venues).toLocaleString("en-US")} venues${loading.length ? "; loading now: " + loading.join(", ") : ""}. The most are in ${per.slice(0, 3).map((r) => STATE_NAMES[r.state] || r.state).join(", ")}.`,
        view: { type: "dashboard", title: "Liquor licence coverage (active, on-premise)",
          tiles: [{ label: "States", value: String(cov.states) }, { label: "Venues", value: (+cov.venues).toLocaleString("en-US") }, { label: "Licences", value: (+cov.licences).toLocaleString("en-US") }, { label: "Loading now", value: loading.length ? loading.join(", ") : "none" }],
          bars: { title: "Venues by state", bars: per.map((r) => ({ label: STATE_NAMES[r.state] || r.state, value: +r.venues, sub: r.kind === "accounts" ? "accounts" : `${r.cities || 0} cities` })) } },
      };
    },
  },
  venue_profile: {
    about: "One venue's drinks profile: counts of cocktails/beer/wine/spirits, cocktail median price, neighbourhood income and age band, spirit mix: profile card + donut.",
    async run(db, p) {
      if (!p.q) throw new Error("which venue?");
      let q = db.from("mv_menu_dev_venue_profile").select("*").ilike("venue", `%${esc(p.q)}%`).limit(1);
      if (p.city) q = q.ilike("city", esc(p.city));
      const { data } = await q;
      const v = data?.[0];
      if (!v) return { speak: `I have no drinks profile for ${p.q}${p.city ? " in " + p.city : ""} yet.`, view: { type: "empty", title: "No profile" } };
      const { data: cp } = await db.from("v_venue_cocktail_profile").select("spirit_mix,originals,share_originals").ilike("venue", v.venue).limit(1);
      const mix = cp?.[0]?.spirit_mix && typeof cp[0].spirit_mix === "object" ? Object.entries(cp[0].spirit_mix).map(([k, n]) => ({ label: title(k), value: +(n as number) })).filter((s) => s.value > 0) : [];
      return {
        speak: `${v.venue} in ${v.city} lists ${v.cocktail_items} cocktails${v.cocktail_median_price ? ` at a median of $${(+v.cocktail_median_price).toFixed(2)}` : ""}, ${v.beer_items} beers, ${v.wine_items} wines and ${v.liquor_items} spirits.`,
        view: { type: "profile", title: v.venue, badge: `${v.city}, ${v.state_code}`, rows: [["Type", v.venue_type], ["Rating", v.rating], ["Area income", v.income ? "$" + (+v.income).toLocaleString("en-US") + " · " + v.income_band : v.income_band], ["Area age", v.median_age ? v.median_age + " · " + v.age_band : v.age_band]].filter((r) => r[1]), tiles: [{ label: "Cocktails", value: String(v.cocktail_items) }, { label: "Median cocktail", value: v.cocktail_median_price ? "$" + (+v.cocktail_median_price).toFixed(2) : "—" }, { label: "Beer", value: String(v.beer_items) }, { label: "Wine", value: String(v.wine_items) }, { label: "Spirits", value: String(v.liquor_items) }, { label: "Zero proof", value: String(v.na_items) }], donut: mix.length ? { title: "Cocktail spirit mix", slices: mix } : null },
      };
    },
  },
  label_approvals: {
    about: "US TTB COLA label approvals for a brand or product name (recent first): table.",
    async run(db, p) {
      if (!p.q) throw new Error("which brand?");
      const { data, error } = await db.from("cola_label_approvals").select("ttb_id,completed_date,brand_name_raw,fanciful_name,class_type_desc,origin_desc").or(`brand_name_raw.ilike."%${esc(p.q)}%",fanciful_name.ilike."%${esc(p.q)}%"`).order("completed_date", { ascending: false }).limit(60);
      if (error) throw error;
      const rows = data || [];
      return {
        speak: rows.length ? `${rows.length}${rows.length >= 60 ? "+" : ""} label approvals for ${p.q}, the latest on ${rows[0].completed_date}.` : `No COLA label approvals found for ${p.q}.`,
        view: { type: "table", title: `Label approvals · ${p.q}`, table: { cols: ["Approved", "Brand", "Product", "Class", "Origin"], rows: rows.map((r: any) => [r.completed_date, r.brand_name_raw, r.fanciful_name || "", r.class_type_desc || "", r.origin_desc || ""]) } },
      };
    },
  },
  /* v8: PRODUCT KNOWLEDGE (phg_know, draft 09): how each brand and bottling is made, aging, proof, tasting notes and
     history, each fact from a named source. Used by the place card and by brand_knowledge below. */
  brand_knowledge: {
    about: "How a tequila or mezcal brand and its bottlings are made and taste: production (agave, cooking, milling, fermentation, stills), aging and barrels, proof, additive-free status, tasting notes, history, for a brand name or NOM (e.g. 'how is Fortaleza reposado made', 'is Siete Leguas additive free', 'tell me about G4').",
    async run(db, p) {
      if (!p.q && !p.nom) throw new Error("which brand?");
      const names = p.q ? [String(p.q).replace(/\b(tequila|mezcal|blanco|plata|reposado|a[nñ]ejo|extra|cristalino|the)\b/gi, " ").replace(/\s+/g, " ").trim(), String(p.q).trim()].filter(Boolean) : null;
      const { data } = await db.rpc("phg_know_lookup", { p_nom: p.nom ? String(p.nom) : null, p_names: names });
      const list: any[] = Array.isArray(data) ? data : [];
      if (!list.length) return { speak: `I don't have production or tasting notes for ${p.q || "NOM " + p.nom} yet.`, view: { type: "empty", title: "Not in PHG yet" } };
      const b = list[0];
      const want = String(p.q || "").toLowerCase();
      const st = /extra\s*a[nñ]ejo/.test(want) ? "extra_anejo" : /a[nñ]ejo/.test(want) ? "anejo" : /reposado/.test(want) ? "reposado" : /blanco|plata|silver/.test(want) ? "blanco" : /cristalino/.test(want) ? "cristalino" : "";
      const exps = (b.expressions || []) as any[];
      const focus = st ? exps.filter((e) => e.style === st) : exps;
      const one = focus[0];
      const speak = one ? `${one.name}: ${knowLine(one)}.` + (one.tasting?.length ? ` Tasting notes: ${one.tasting.slice(0, 4).join(", ")}.` : "") + (/additive/i.test(want) ? ((one.notes || []).find((n: string) => /additive/i.test(n)) ? " On additives: " + (one.notes || []).find((n: string) => /additive/i.test(n)) : one.additive_free == null ? " I have no current additive-free confirmation for it." : "") : "") + (b.sources?.length ? ` Source: ${b.sources[0].title || "PHG research"}.` : "")
        : `${b.name}${b.nom ? ", NOM " + b.nom : ""}${b.region ? ", " + b.region : ""}.` + (b.history?.length ? " " + b.history.slice(0, 2).join(". ") + "." : "");
      return { speak, view: { type: "place", kind: "brand", title: b.name, badge: b.nom ? `NOM ${b.nom}` : b.category, rows: knowRows(b), sections: knowSections(list), note: knowNote(list) } };
    },
  },
  /* v7: PLACE CARDS. Tapping a pin on the map (or "tell me about ...", "pull up ...") opens everything PHG holds on
     that place, in expandable sections. The same data is spoken as a short summary for the locked-phone Shortcut. */
  place_distillery: {
    about: "Everything on one tequila distillery (NOM number, producer or one of its brands): where it is, every brand it makes and each brand's lineup (Blanco, Reposado, Anejo, Extra Anejo, Cristalino...) from US label approvals: expandable place card.",
    async run(db, p) {
      let nom = String(p.nom || "").replace(/\D/g, "");
      if (!nom && p.q) {
        const { data: o } = await db.from("organizations").select("nom").not("nom", "is", null).ilike("organization_name", `%${esc(p.q)}%`).limit(1);
        nom = o?.[0]?.nom || "";
        if (!nom) { const { data: br } = await db.from("brands").select("primary_nom").ilike("brand_name", `%${esc(p.q)}%`).not("primary_nom", "is", null).limit(1); nom = br?.[0]?.primary_nom || ""; }
      }
      if (!nom) return { speak: `I couldn't find that distillery. Try its NOM number or one of its brands.`, view: { type: "empty", title: "Not found" } };
      const { data: orgs } = await db.from("organizations").select("organization_name,nom,notes,verified_at").eq("nom", nom).limit(1);
      const o = orgs?.[0];
      if (!o) return { speak: `I don't have NOM ${nom} in the register.`, view: { type: "empty", title: "Not found" } };
      const a = addressOf(o.notes), name = title(String(o.organization_name).replace(LEGAL, ""));
      const { data: brands } = await db.from("brands").select("id,brand_name,brand_status").eq("primary_nom", nom).order("brand_name").limit(80);
      const ids = (brands || []).map((b: any) => b.id);
      const labels: any[] = [];
      for (let i = 0; i < ids.length; i += 40) {
        const { data } = await db.from("cola_label_approvals").select("brand_id,fanciful_name,class_type_desc,completed_date").in("brand_id", ids.slice(i, i + 40)).order("completed_date", { ascending: false }).limit(2000);
        labels.push(...(data || []));
      }
      const style = (t: string) => { const x = t.toLowerCase(); return /extra\s*a[nñ]ejo/.test(x) ? "Extra Añejo" : /cristalino/.test(x) ? "Cristalino" : /a[nñ]ejo/.test(x) ? "Añejo" : /reposado/.test(x) ? "Reposado" : /blanco|plata|silver|platinum|white/.test(x) ? "Blanco" : /joven|gold|oro/.test(x) ? "Joven" : "Other"; };
      const ORDER = ["Blanco", "Joven", "Reposado", "Añejo", "Extra Añejo", "Cristalino", "Other"];
      const byBrand: Record<string, any[]> = {}; const styleCount: Record<string, number> = {};
      labels.forEach((l) => { (byBrand[l.brand_id] = byBrand[l.brand_id] || []).push(l); });
      const sections = (brands || []).map((b: any) => {
        const seen = new Set<string>(); const items: any[] = [];
        (byBrand[b.id] || []).forEach((l) => {
          const fn = String(l.fanciful_name || "").trim() || b.brand_name; const k = fn.toLowerCase(); if (seen.has(k)) return; seen.add(k);
          const st = style(fn + " " + (l.class_type_desc || "")); styleCount[st] = (styleCount[st] || 0) + 1;
          items.push({ name: fn, sub: st, value: l.completed_date ? String(l.completed_date).slice(0, 4) : "" });
        });
        items.sort((x, y) => ORDER.indexOf(x.sub) - ORDER.indexOf(y.sub) || x.name.localeCompare(y.name));
        return { title: b.brand_name, count: items.length, items: items.slice(0, 40), empty: items.length ? "" : "No US label approvals on file" };
      }).sort((x: any, y: any) => y.count - x.count);
      const lineup = ORDER.filter((k) => styleCount[k]).map((k) => `${k} ${styleCount[k]}`).join(" · ");
      let know: any[] = [];
      try { const { data: kd } = await db.rpc("phg_know_lookup", { p_nom: nom, p_names: (brands || []).map((b: any) => b.brand_name) }); know = Array.isArray(kd) ? kd : []; } catch { know = []; }
      const top = sections.filter((x: any) => x.count).slice(0, 3).map((x: any) => x.title);
      return {
        speak: `NOM ${nom} is ${name}${a.muni ? `, in ${title(a.muni)}, ${title(a.state)}` : ""}. It makes ${sections.length} brand${sections.length === 1 ? "" : "s"}` + (top.length ? `, including ${top.join(", ")}` : "") + "." + (lineup ? ` Their US-approved lineup covers ${ORDER.filter((k) => styleCount[k] && k !== "Other").join(", ")}.` : "") +
          (know.length ? ` I also have how ${know.slice(0, 3).map((k: any) => k.name).join(", ")} ${know.length === 1 ? "is" : "are"} made and tasting notes; ask about any bottle.` : ""),
        view: {
          type: "place", kind: "distillery", title: name, badge: `NOM ${nom}`,
          pin: a.coord ? { lat: a.coord[0], lng: a.coord[1] } : null,
          rows: [["Producer", o.organization_name], ["Town", a.muni ? title(a.muni) + ", " + title(a.state) : "—"], ["Registered address", a.addr || "—"], ["Brands", String(sections.length)], ["Lineup", lineup || "—"]],
          sections: [...knowSections(know), ...sections],
          note: know.length ? knowNote(know) + " Lineups come from US label approvals (TTB COLA) and the CRT register." : "Lineups come from US label approvals (TTB COLA) and the CRT register. Tasting notes, production process (cooking, milling, stills, barrels) and history are not in PHG for these brands yet.",
        },
      };
    },
  },
  place_venue: {
    about: "Everything on one bar or restaurant (by name, optionally city/state): address, type, rating, neighbourhood, and its drinks menu by section with prices: expandable place card. Use this to show or read out a venue's menu.",
    async run(db, p) {
      if (!p.q) throw new Error("which venue?");
      let q = db.from("mv_drink_explorer").select("venue,venue_key,city,state_code,address,venue_type,rating,lat,lng,income,median_age,income_band,age_band,section,menu_section,item_name,item_price,family").ilike("venue", `%${esc(p.q)}%`).limit(600);
      if (p.city) q = q.ilike("city", esc(p.city));
      if (p.state) q = q.eq("state_code", String(p.state).toUpperCase().slice(0, 2));
      const { data } = await q;
      let rows = data || [];
      if (rows.length) {
        /* several venues can match: keep the best (exact name first, then the one with the most drinks) */
        const low = String(p.q).toLowerCase(); const count: Record<string, number> = {};
        rows.forEach((r: any) => { count[r.venue_key] = (count[r.venue_key] || 0) + 1; });
        const keys = Object.keys(count).sort((x, y) => {
          const ex = (k: string) => rows.find((r: any) => r.venue_key === k)?.venue.toLowerCase() === low ? 0 : 1;
          return ex(x) - ex(y) || count[y] - count[x];
        });
        rows = rows.filter((r: any) => r.venue_key === keys[0]);
      }
      if (!rows.length) {
        let vq = db.from("v_public_venues").select("venue,city,state_code,address,venue_type,rating,reviews,website,lat,lng").ilike("venue", `%${esc(p.q)}%`).limit(1);
        if (p.city) vq = vq.ilike("city", esc(p.city));
        const { data: vv } = await vq; const v = vv?.[0];
        if (!v) return { speak: `I couldn't find ${p.q}${p.city ? " in " + p.city : ""}.`, view: { type: "empty", title: "Not found" } };
        return { speak: `${v.venue} is a ${v.venue_type || "venue"} in ${v.city}. I haven't read its drinks menu yet.`, view: { type: "place", kind: "venue", title: v.venue, badge: `${v.city}, ${v.state_code}`, pin: v.lat ? { lat: +v.lat, lng: +v.lng } : null, rows: [["Address", v.address], ["Type", v.venue_type], ["Rating", v.rating ? `${v.rating} (${v.reviews || 0} reviews)` : ""], ["Website", v.website]].filter((r) => r[1]), sections: [], note: "No drinks menu read for this venue yet." } };
      }
      const f = rows[0];
      const SEC: Record<string, string> = { cocktails: "Cocktails", beer: "Beer", wine: "Wine", liquor: "Spirits", non_alcoholic: "Zero proof" };
      const bySec: Record<string, any[]> = {};
      rows.forEach((r: any) => { const k = SEC[r.section] || "Other"; (bySec[k] = bySec[k] || []).push(r); });
      const sections = ["Cocktails", "Spirits", "Beer", "Wine", "Zero proof", "Other"].filter((k) => bySec[k]).map((k) => {
        const seen = new Set<string>();
        const items = bySec[k].filter((r) => { const n = String(r.item_name || "").toLowerCase(); if (seen.has(n)) return false; seen.add(n); return true; })
          .sort((x, y) => String(x.menu_section || "").localeCompare(String(y.menu_section || "")) || String(x.item_name).localeCompare(String(y.item_name)))
          .map((r) => ({ name: r.item_name, sub: r.menu_section || r.family || "", value: r.item_price != null ? "$" + (+r.item_price).toFixed(2) : "" }));
        return { title: k, count: items.length, items: items.slice(0, 80) };
      });
      const ck = (bySec["Cocktails"] || []).filter((r) => r.item_price != null).map((r) => +r.item_price).sort((a, b) => a - b);
      const med = ck.length ? ck[Math.floor(ck.length / 2)] : null;
      const say = (bySec["Cocktails"] || []).slice(0, 4).map((r) => `${r.item_name}${r.item_price != null ? " at $" + (+r.item_price).toFixed(0) : ""}`);
      return {
        speak: `${f.venue} in ${f.city} lists ${rows.length} drinks: ` + sections.map((x) => `${x.count} ${x.title.toLowerCase()}`).join(", ") + "." + (say.length ? ` Cocktails include ${say.join(", ")}.` : "") + (med ? ` The typical cocktail is $${med.toFixed(0)}.` : ""),
        view: {
          type: "place", kind: "venue", title: f.venue, badge: `${f.city}, ${f.state_code}`,
          pin: f.lat ? { lat: +f.lat, lng: +f.lng } : null,
          rows: [["Address", f.address], ["Type", f.venue_type], ["Rating", f.rating], ["Typical cocktail", med ? "$" + med.toFixed(2) : ""], ["Neighbourhood income", f.income ? "$" + (+f.income).toLocaleString("en-US") + (f.income_band ? " · " + f.income_band : "") : f.income_band], ["Neighbourhood age", f.median_age ? f.median_age + (f.age_band ? " · " + f.age_band : "") : f.age_band]].filter((r) => r[1] != null && r[1] !== ""),
          sections,
          actions: [{ label: "Open the menu document", say: `show me the menu for ${f.venue} in ${f.city}` }],
          note: "Drinks and prices as read from the venue's current menu.",
        },
      };
    },
  },
  menu_breakdown: {
    about: "Breakdown of one menu section (cocktails, beer, wine, liquor, non_alcoholic) by dimension (item, subfamily, city, venue_type, serve_format) in a state: bars with average prices.",
    async run(db, p) {
      const section = ["cocktails", "beer", "wine", "liquor", "non_alcoholic"].includes(p.section) ? p.section : "cocktails";
      const dim = ["item", "subfamily", "city", "venue_type", "serve_format"].includes(p.group_by) ? p.group_by : "item";
      let q = db.from("mv_dash_breakdown").select("label,items,avg_price,venues,state_code").eq("section", section).eq("dimension", dim).order("items", { ascending: false }).limit(15);
      if (p.state) q = q.eq("state_code", String(p.state).toUpperCase().slice(0, 2));
      const { data, error } = await q;
      if (error) throw error;
      const rows = data || [];
      return {
        speak: rows.length ? `Top ${section.replace("_", " ")} by ${dim.replace("_", " ")}${p.state ? " in " + (STATE_NAMES[String(p.state).toUpperCase()] || p.state) : ""}: ${rows.slice(0, 3).map((r: any) => `${r.label} (${r.items})`).join(", ")}.` : "No breakdown data.",
        view: { type: "bars", title: `${title(section.replace("_", " "))} by ${dim.replace("_", " ")}${p.state ? " · " + String(p.state).toUpperCase() : ""}`, bars: rows.map((r: any) => ({ label: r.label, value: +r.items, sub: `${r.venues} venues${r.avg_price ? " · $" + (+r.avg_price).toFixed(2) : ""}` })), unit: " items" },
      };
    },
  },
};

const PLAN_SCHEMA = {
  type: "object", additionalProperties: false, required: ["source", "params"],
  properties: {
    source: { type: "string", enum: [...Object.keys(SOURCES), "ask", "menu_lookup", "none"] },
    params: {
      type: "object", additionalProperties: false,
      required: ["q", "nom", "city", "state", "town", "zip", "family", "venue_type", "section", "group_by", "price_min", "price_max", "income_min", "income_max", "age_min", "age_max", "sort", "with_menus"],
      properties: {
        q: { type: "string" }, nom: { type: "string" }, city: { type: "string" }, state: { type: "string" }, town: { type: "string" },
        zip: { type: "string" }, family: { type: "string" }, venue_type: { type: "string" }, section: { type: "string" }, group_by: { type: "string" },
        price_min: { type: "string" }, price_max: { type: "string" }, income_min: { type: "string" }, income_max: { type: "string" },
        age_min: { type: "string" }, age_max: { type: "string" }, sort: { type: "string" }, with_menus: { type: "string" },
      },
    },
  },
};

function fastPlan(t: string): { source: string; params: P } | null {
  const s = t.toLowerCase();
  const nom = s.match(/\bnom\s*#?\s*-?\s*(\d{3,4})\b/);
  if (nom) return { source: "distillery", params: { nom: nom[1] } };
  const zip = s.match(/\b(\d{5})\b/);
  if (zip && /\b(zip|census|demograph|income|population|age)\b/.test(s)) return { source: "zip_demographics", params: { zip: zip[1] } };
  if (/\b(all|every|map)\b.*\bdistilleries\b|\bdistilleries\b.*\b(map|in)\b/.test(s)) {
    const m = s.match(/\bin ([a-zà-ÿ ]+?)(?:\?|$|,)/);
    return { source: "distilleries", params: { town: m ? m[1].replace(/\b(mexico|jalisco state)\b/, "").trim() : "" } };
  }
  if (/\b(pipeline|menus? (uploading|coming in|being (rendered|downloaded|scraped))|render(ing)? (queue|backlog)|(upload|download|render|scrap)(ing)? (rate|speed|status)|is (it|the scraper|the pipeline) (running|stuck|working))\b/.test(s)) return { source: "pipeline", params: {} };
  if (/\b(liquor|alcohol|on[- ]premise)?\s*licen[cs]es?\b/.test(s) && /\b(how many|coverage|total|states?|count|loaded|loading)\b/.test(s) && !/\b(in|for) [a-z]/.test(s)) return { source: "licenses", params: {} };
  if (/\b(how much data|coverage|how many (venues|menus)|data do we have)\b/.test(s)) return { source: "coverage", params: {} };
  return null;
}

/* v6: ASK. Anything the fixed catalog can't answer is written as one read-only SELECT and run through
   public.phg_harmony_query (the knowledge-map gateway: select only, table allowlist, project-scoped RLS, logged).
   One repair round on a planner error. The gateway does not bound its own runtime, so the caller does (12 s). */
/* v15 (2026-09-29): failures logged to phg.harmony_feedback; lessons (phg.harmony_lessons) read by planner + SQL writer.
   v14 (2026-09-29): licenses source (active on-premise licence coverage, state breakdowns, licensed-venue lists/maps).
   v13 (2026-09-29): refinable views - price / income / age / sort params, drink_map source, view.query.
   v12 (Rob 2026-09-29: no extra payment): priority processing OFF by default (OPENAI_SERVICE_TIER=priority to re-enable).
   v11 SPEED: OpenAI priority processing, like the inbox (OPENAI_SERVICE_TIER; "default" turns it off). If the account
   refuses it, it is switched off for this instance and the request is sent again without it. */
let TIER: string | null = (Deno.env.get("OPENAI_SERVICE_TIER") || "default").trim();
if (TIER === "default" || TIER === "auto" || !TIER) TIER = null;
async function oaCall(oa: string, body: Record<string, unknown>): Promise<Response> {
  const send = () => fetch("https://api.openai.com/v1/responses", {
    method: "POST", headers: { Authorization: `Bearer ${oa}`, "Content-Type": "application/json" },
    body: JSON.stringify(TIER ? { ...body, service_tier: TIER } : body),
  });
  let r = await send();
  if (TIER && r.status === 400) {
    const t = await r.clone().text().catch(() => "");
    if (/service_tier|priority/i.test(t)) { console.log(JSON.stringify({ tier_off: t.slice(0, 200) })); TIER = null; r = await send(); }
  }
  return r;
}

async function askData(db: any, oa: string, question: string, user: string, account: string): Promise<Result> {
  const sqlModel = Deno.env.get("OPENAI_SQL_MODEL") || "gpt-4.1";
  const sqlLessons = await lessons(db, "sql");
  const gen = async (extra: string) => {
    const r = await oaCall(oa, ({
        model: sqlModel, max_output_tokens: 700,
        instructions: "Write ONE read-only PostgreSQL SELECT that answers the question from these tables only. Return JSON. title: a short screen title. display: table, bars (label + one number per row) or map (rows have lat and lng). label_col / value_col name the columns for bars. Prefer readable column aliases (venue, city, drink, price). Never select raw ids unless asked.\n" + SCHEMA_DOC + (sqlLessons ? "\nLessons from past mistakes (follow them):\n" + sqlLessons : ""),
        input: question + extra,
        text: { format: { type: "json_schema", name: "phg_sql", strict: true, schema: {
          type: "object", additionalProperties: false, required: ["sql", "title", "display", "label_col", "value_col"],
          properties: { sql: { type: "string" }, title: { type: "string" }, display: { type: "string", enum: ["table", "bars", "map"] }, label_col: { type: "string" }, value_col: { type: "string" } } } } },
      }),
    );
    const j = await r.json().catch(() => ({}));
    let t = typeof j.output_text === "string" ? j.output_text : "";
    if (!t && Array.isArray(j.output)) for (const o of j.output) for (const c of (o?.content || [])) if (c?.type === "output_text") t += c.text || "";
    return JSON.parse(t);
  };
  const run = async (sql: string) => {
    const t0 = Date.now();
    const call = db.rpc("phg_harmony_query", { p_account: account, p_user: user, p_sql: sql, p_max_rows: 200 });
    const res: any = await Promise.race([call, new Promise((r) => setTimeout(() => r({ data: { error: "timed out after 12 s" } }), 12000))]);
    const d = res?.data || {}; const err = res?.error?.message || d.error || null;
    if (d.log_id) { try { await db.rpc("phg_harmony_query_finish", { p_log_id: d.log_id, p_row_count: (d.rows || []).length, p_ms: Date.now() - t0, p_error: err }); } catch { /* log only */ } }
    return { rows: (d.rows || []) as any[], err };
  };
  let plan = await gen("");
  let out = await run(String(plan.sql || ""));
  if (out.err) { plan = await gen(`\n\nYour previous SQL failed.\nSQL: ${plan.sql}\nError: ${out.err}\nFix it.`); out = await run(String(plan.sql || "")); }
  if (out.err) {
    logFeedback(db, { kind: "no_answer", source: "ask", user_text: question, reply_text: "Could not answer", view_title: "Could not answer", sql: String(plan.sql || ""), error: String(out.err), user_id: user, account_id: account });
    return { speak: "I couldn't work that one out from the data. Try asking it another way.", view: { type: "empty", title: "Could not answer", note: String(out.err).slice(0, 200) } };
  }
  const rows = out.rows;
  if (!rows.length) {
    logFeedback(db, { kind: "empty_result", source: "ask", user_text: question, view_title: plan.title || "No results", sql: String(plan.sql || ""), user_id: user, account_id: account });
    return { speak: `I didn't find anything for that in PHG's data.`, view: { type: "empty", title: plan.title || "No results" } };
  }
  const cols = Object.keys(rows[0]);
  const cell = (v: any) => v == null ? "" : typeof v === "number" ? (Number.isInteger(v) ? v : Math.round(v * 100) / 100) : typeof v === "object" ? JSON.stringify(v).slice(0, 80) : String(v).slice(0, 120);
  const view: View = { type: "table", title: plan.title || "Results", table: { cols, rows: rows.slice(0, 60).map((r) => cols.map((c) => cell(r[c]))) } };
  if (plan.display === "bars" && cols.includes(plan.value_col) && rows.every((r) => r[plan.value_col] == null || isFinite(Number(r[plan.value_col])))) {
    const lc = cols.includes(plan.label_col) ? plan.label_col : cols.find((c) => c !== plan.value_col)!;
    view.type = "dashboard"; view.bars = { title: plan.title, bars: rows.slice(0, 15).map((r) => ({ label: String(r[lc] ?? ""), value: Number(r[plan.value_col] || 0) })) };
  }
  const la = cols.find((c) => /^(lat|latitude)$/i.test(c)), ln = cols.find((c) => /^(lng|lon|longitude)$/i.test(c));
  if (la && ln) {
    const lab = cols.find((c) => /venue|name/i.test(c)) || cols[0];
    const pins = rows.filter((r) => r[la] != null && r[ln] != null).map((r) => ({ lat: +r[la], lng: +r[ln], label: String(r[lab] ?? ""), sub: cols.filter((c) => c !== la && c !== ln && c !== lab).slice(0, 3).map((c) => cell(r[c])).join(" · ") }));
    if (pins.length) { view.type = "map"; view.pins = pins; view.region = "US"; }
  }
  /* one or two spoken sentences from the real rows */
  let speak = "";
  try {
    const r = await oaCall(oa, ({ model: Deno.env.get("OPENAI_DATA_MODEL") || "gpt-4o-mini", max_output_tokens: 160,
        instructions: "Answer the question out loud in one or two short sentences using ONLY these rows (they are on screen too). Say how many there are and the most useful numbers (prices with dollars). No lists, no markdown, never invent anything.",
        input: JSON.stringify({ question, total_rows: rows.length, rows: rows.slice(0, 25) }) }),
    );
    const j = await r.json().catch(() => ({}));
    let t = typeof j.output_text === "string" ? j.output_text : "";
    if (!t && Array.isArray(j.output)) for (const o of j.output) for (const c of (o?.content || [])) if (c?.type === "output_text") t += c.text || "";
    speak = t.trim();
  } catch { /* fall back below */ }
  return { speak: speak || `I found ${rows.length}${rows.length >= 200 ? "+" : ""} results. They're on screen.`, view };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST required" }, 405);
  const url = Deno.env.get("SUPABASE_URL"), anon = Deno.env.get("SUPABASE_ANON_KEY"), svc = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"), oa = Deno.env.get("OPENAI_API_KEY");
  if (!url || !anon || !svc) return json({ error: "runtime configuration missing" }, 500);
  /* v2: server-to-server calls from phg-harmony-inbox (the Action button, which has no app login)
     prove themselves with the service-role key in x-phg-internal; it never leaves Supabase. */
  const internal = (req.headers.get("x-phg-internal") || "") === svc;
  let callerUser = "";
  if (!internal) {
    const auth = req.headers.get("Authorization") || "";
    if (!auth.toLowerCase().startsWith("bearer ")) return json({ error: "login required" }, 401);
    const sbu = createClient(url, anon, { auth: { persistSession: false }, global: { headers: { Authorization: auth } } });
    const { data: ud, error: ue } = await sbu.auth.getUser(auth.slice(7).trim());
    if (ue || !ud?.user) return json({ error: "invalid or expired login" }, 401);
    callerUser = ud.user.id;
  }
  const db = createClient(url, svc, { auth: { persistSession: false } });

  const b = await req.json().catch(() => ({}));
  if (b.action === "catalog") return json({ status: "ok", sources: Object.fromEntries(Object.entries(SOURCES).map(([k, v]) => [k, v.about])) });
  const ask = String(b.prompt || "").trim().slice(0, 600);
  if (!ask && !b.source) return json({ error: "prompt required" }, 400);

  let plan: { source: string; params: P } | null = b.source && SOURCES[b.source] ? { source: b.source, params: b.params || {} } : fastPlan(ask);
  if (!plan) {
    if (!oa) return json({ error: "planner unavailable" }, 500);
    const plannerLessons = await lessons(db, "planner");
    const r = await oaCall(oa, ({
        model: Deno.env.get("OPENAI_DATA_MODEL") || "gpt-4o-mini", max_output_tokens: 300,
        instructions: "Pick the one PHG data source that answers the request and fill its parameters (empty string when unused). state is a US two-letter code (menus: IA, CO, NY; liquor licences: see the licenses source). group_by is one of city, venue_type, venue, state_code, item, subfamily, serve_format. section is one of cocktails, beer, wine, liquor, non_alcoholic. family is one of tequila, mezcal, whiskey, vodka, gin, rum, brandy, liqueur, wine, beer, non_alcoholic. price_min / price_max are dollars ('under $14' -> price_max 14). income_min / income_max are the median household income of the venue ZIP in dollars ('income over 100k' -> income_min 100000; 'affluent' -> 100000). age_min / age_max are the ZIP median age ('younger areas' -> age_max 35). sort is one of price_asc, price_desc, income_desc, income_asc, rating_desc, name, city. with_menus is 'true' to keep only venues with menu data. Use licenses for anything about liquor licences or licensed venues (group_by city/type/county for one state; venue_type = licence type text). Use drink_map when they want to SEE where a drink is served (a map), drink_prices for prices and averages. Use menu_lookup when they want to SEE a specific venue's menu document. Use ask for any other question about PHG's data that the sources above cannot answer as asked (a list with several filters such as all the margaritas at one venue in one city, a specific venue's drinks, comparisons, counts, rankings, or the business's own recipes, invoices, costs, sales, labor, budgets and notes). Use none only when it is not about data.\nSources:\n" + Object.entries(SOURCES).map(([k, v]) => `${k}: ${v.about}`).join("\n") + "\nmenu_lookup: open a specific venue's menu document (q=venue, city, state)." + (plannerLessons ? "\nLessons from past mistakes (follow them):\n" + plannerLessons : ""),
        input: ask,
        text: { format: { type: "json_schema", name: "phg_data_plan", strict: true, schema: PLAN_SCHEMA } },
      }),
    );
    const raw = await r.json().catch(() => ({}));
    let t = typeof raw.output_text === "string" ? raw.output_text : "";
    if (!t && Array.isArray(raw.output)) for (const o of raw.output) for (const c of (o?.content || [])) if (c?.type === "output_text") t += c.text || "";
    try { plan = JSON.parse(t); } catch {
      logFeedback(db, { kind: "error", source: "planner", user_text: ask, error: "could not plan: " + String(raw?.error?.message || t || "empty").slice(0, 500) });
      return json({ error: "could not plan that request", detail: raw?.error?.message }, 502);
    }
  }
  /* who is asking (for the gateway: it checks the membership itself) */
  const askUser = internal ? String(b.user || "") : callerUser;
  const askAccount = String(b.account || b.account_id || "");
  const canAsk = !!oa && /^[0-9a-f-]{36}$/i.test(askUser) && /^[0-9a-f-]{36}$/i.test(askAccount);
  if (plan!.source === "ask" || (plan!.source === "none" && b.ask_fallback)) {
    if (!canAsk) return json({ status: "ok", source: "none", params: {} });
    try { return json({ status: "ok", source: "ask", params: {}, ...(await askData(db, oa!, ask, askUser, askAccount)) }); }
    catch (e) {
      logFeedback(db, { kind: "error", source: "ask", user_text: ask, view_title: "Could not answer", error: String((e as Error)?.message || e), user_id: askUser, account_id: askAccount });
      return json({ status: "ok", source: "ask", params: {}, speak: "I couldn't work that one out just now.", view: { type: "empty", title: "Could not answer" }, error: String((e as Error)?.message || e) });
    }
  }
  const params: P = {};
  for (const [k, v] of Object.entries(plan!.params || {})) if (v != null && String(v).trim() !== "") params[k] = String(v).trim().slice(0, 80);
  if (plan!.source === "menu_lookup" || plan!.source === "none") return json({ status: "ok", source: plan!.source, params });
  const src = SOURCES[plan!.source];
  if (!src) return json({ status: "ok", source: "none", params });
  try {
    const out = await src.run(db, params);
    /* v13: every view carries the query that made it, so the app can refine it ("only under $14", "sort by price") */
    if (out.view && typeof out.view === "object") (out.view as any).query = { source: plan!.source, params };
    if ((out.view as any)?.type === "empty") logFeedback(db, { kind: "empty_result", source: plan!.source, params, user_text: ask, reply_text: out.speak, view_title: (out.view as any)?.title });
    return json({ status: "ok", source: plan!.source, params, ...out });
  } catch (e) {
    logFeedback(db, { kind: "error", source: plan!.source, params, user_text: ask, view_title: "Could not load", error: String((e as Error)?.message || e) });
    return json({ status: "ok", source: plan!.source, params, speak: "I could not pull that: " + String((e as Error)?.message || e), view: { type: "empty", title: "Could not load" } });
  }
});
