// ingest-census-acs
// Loads ACS 2020-2024 5-year estimates for a state into staging_census_acs,
// matching the shape Iowa was loaded in.
//
// WHY THE API AND NOT THE SUMMARY FILE
// Iowa was loaded from the nationwide table-based Summary File (.dat). Those
// files carry every geography in the country per table; pulling twelve of them
// to extract two states is not workable inside an Edge Function. The API
// returns the same 2020-2024 estimates filtered to one state in one request.
//
// KEY NORMALISATION - READ THIS BEFORE CHANGING ANYTHING
// The Summary File names cells B19013_E001 / B19013_M001.
// The API names the same cells B19013_001E / B19013_001M.
// Same data, different convention. Rows are normalised to the SUMMARY FILE
// convention on the way in, so Iowa's 13,512 existing rows and the new ones
// are computed by identical downstream code. Storing both conventions would
// mean every consumer has to know which state it is reading.
//
// PROBE MODE
//   ?probe=1&state=08&table=B19013
// Fetches one table for one state, returns the raw first rows and the
// normalised form, WRITES NOTHING. Run this before any load: the response
// shape is asserted here, not assumed.
//
// NO ABSENCE INFERENCE
// The API returns null for a geography where the estimate is suppressed or
// unavailable. That is recorded as null. It is not zero, and a geography
// missing from a response is not recorded at all rather than recorded empty.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const VINTAGE = "2020-2024";
const API_YEAR = "2024";
const BASE = `https://api.census.gov/data/${API_YEAR}/acs/acs5`;

// The twelve tables Iowa carries. Confirmed against
// select distinct acs_table from geography_demographics.
const TABLES = [
  "B01001", // age by sex
  "B01002", // median age
  "B03003", // hispanic or latino origin
  "B08007", // place of work
  "B08008", // workers by place of residence
  "B08604", // worker population weight
  "B11001", // household type
  "B15003", // educational attainment
  "B19001", // household income brackets
  "B19013", // median household income
  "B25010", // average household size
  "C24030", // industry by sex
];

// sumlevel -> API geography clause. Matches the sumlevels already staged:
// 040 state, 050 county, 160 place.
const LEVELS: Record<string, (fips: string) => string> = {
  "040": (f) => `for=state:${f}`,
  "050": (f) => `for=county:*&in=state:${f}`,
  "160": (f) => `for=place:*&in=state:${f}`,
};

const STATE_FIPS: Record<string, string> = { CO: "08", NY: "36", IA: "19" };

function json(b: unknown, s = 200) {
  return new Response(JSON.stringify(b), {
    status: s, headers: { "Content-Type": "application/json" },
  });
}

function eq(given: string | null, expected: string): boolean {
  if (!given || !expected) return false;
  const a = new TextEncoder().encode(given.trim());
  const b = new TextEncoder().encode(expected.trim());
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a[i] ^ b[i];
  return d === 0;
}

// B19013_001E -> B19013_E001 . Anything that does not match the API pattern is
// passed through untouched rather than guessed at.
function normaliseKey(k: string): string | null {
  const m = k.match(/^([A-Z]\d{5}[A-Z]?)_(\d{3})([EM])$/);
  return m ? `${m[1]}_${m[3]}${m[2]}` : null;
}

// The API returns [[header...],[row...],...]. Geography identifiers are the
// trailing columns and vary by level, so they are taken by name.
function toRows(raw: string[][], table: string, sumlevel: string, url: string) {
  const [header, ...body] = raw;
  const out: Record<string, unknown>[] = [];
  for (const r of body) {
    const rec: Record<string, string> = {};
    header.forEach((h, i) => (rec[h] = r[i]));

    const geoId = sumlevel === "040"
      ? `0400000US${rec.state}`
      : sumlevel === "050"
      ? `0500000US${rec.state}${rec.county}`
      : `1600000US${rec.state}${rec.place}`;

    const cells: Record<string, string | null> = {};
    for (const [k, v] of Object.entries(rec)) {
      const nk = normaliseKey(k);
      if (!nk) continue;
      // A suppressed or unavailable estimate stays null. Census uses large
      // negative sentinels for these; they are not values.
      cells[nk] = v === null || v === "" || Number(v) <= -999999999 ? null : v;
    }
    if (!Object.keys(cells).length) continue;

    out.push({
      acs_vintage: VINTAGE,
      table_id: table,
      census_geo_id: geoId,
      sumlevel,
      row_data: cells,
      source_url: url,
      retrieved_at: new Date().toISOString(),
      geography_name: rec.NAME ?? null,
    });
  }
  return out;
}

Deno.serve(async (req: Request) => {
  const secret = Deno.env.get("AGENT_SECRET") ?? "";
  if (!eq(req.headers.get("x-agent-secret"), secret)) {
    return json({ error: "unauthorized" }, 401);
  }

  const p = new URL(req.url).searchParams;
  const probe = p.get("probe") === "1";
  const stateArg = (p.get("state") ?? "").toUpperCase();
  const fips = STATE_FIPS[stateArg] ?? (/^\d{2}$/.test(stateArg) ? stateArg : null);
  if (!fips) {
    return json({ error: "state_required", detail: "pass state=CO or state=NY" }, 400);
  }

  const key = Deno.env.get("CENSUS_API_KEY"); // optional under 500 calls/day
  const suffix = key ? `&key=${key}` : "";

  const fetchOne = async (table: string, sumlevel: string) => {
    const url = `${BASE}?get=NAME,group(${table})&${LEVELS[sumlevel](fips)}${suffix}`;
    const r = await fetch(url);
    if (!r.ok) {
      return { url, error: `http ${r.status}`, body: (await r.text()).slice(0, 300) };
    }
    const raw = await r.json().catch(() => null);
    if (!Array.isArray(raw) || !Array.isArray(raw[0])) {
      return { url, error: "unexpected_shape" };
    }
    return { url, raw: raw as string[][] };
  };

  // PROBE: assert the shape, write nothing.
  if (probe) {
    const table = p.get("table") ?? "B19013";
    const sumlevel = p.get("sumlevel") ?? "160";
    const got = await fetchOne(table, sumlevel);
    if ("error" in got) return json({ probe: true, table, sumlevel, ...got }, 502);
    const rows = toRows(got.raw, table, sumlevel, got.url);
    return json({
      probe: true, wrote_nothing: true,
      table, sumlevel, state: stateArg,
      url: got.url,
      header: got.raw[0],
      raw_sample: got.raw.slice(1, 3),
      normalised_sample: rows.slice(0, 2),
      geographies_returned: rows.length,
      note: "Compare normalised keys against an existing Iowa row before loading.",
    });
  }

  // LOAD
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { auth: { persistSession: false } },
  );

  const only = p.get("table");
  const tables = only ? [only] : TABLES;
  const sumlevels = (p.get("sumlevels") ?? "160,050,040").split(",");
  const report: Record<string, unknown>[] = [];
  let staged = 0;

  for (const table of tables) {
    for (const sumlevel of sumlevels) {
      const got = await fetchOne(table, sumlevel);
      if ("error" in got) {
        report.push({ table, sumlevel, status: got.error, detail: (got as any).body });
        continue;
      }
      const rows = toRows(got.raw, table, sumlevel, got.url)
        .map(({ geography_name: _drop, ...r }) => r);
      if (!rows.length) {
        report.push({ table, sumlevel, status: "no_rows" });
        continue;
      }
      for (let i = 0; i < rows.length; i += 500) {
        const { error } = await supabase.from("staging_census_acs").insert(rows.slice(i, i + 500));
        if (error) {
          report.push({ table, sumlevel, status: "insert_failed", detail: error.message });
          break;
        }
        staged += Math.min(500, rows.length - i);
      }
      report.push({ table, sumlevel, status: "staged", rows: rows.length });
    }
  }

  return json({ state: stateArg, fips, vintage: VINTAGE, staged, report });
});
