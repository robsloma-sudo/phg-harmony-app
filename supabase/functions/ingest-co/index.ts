// ingest-co
//
// Colorado LED licence register (data.colorado.gov, ier5-5ms2) ->
// staging_co_venues, normalised and tiered.
//
//   ?probe=1      column names + sample. No write.
//   ?types=1      licence-type vocabulary with tier assignment. No write.
//   ?dry=1        full run, reports tier counts, writes NOTHING.
//   ?truncate=1   replace staging (the normal reload path).
//   ?tier=        on_premise (default) | spirits_on_premise | beer_wine | all
//   ?include_expired=1
//
// PAGING: $order=:id on every paged query. Socrata gives no stable order
// otherwise, and unordered paging duplicates AND skips simultaneously - an
// unordered NY load returned 30,000 rows holding 23,621 distinct licences.
// The duplicates were visible in a count check; the skips were not.
//
// SOURCE: ier5-5ms2 is the same register as the SBG All-State Excel (both
// 20,539 rows) and additionally carries location.latitude/longitude, so
// Colorado needs no Census geocoding. `zip` arrives float-formatted
// ("80026.0") and `state` is not always CO - out-of-state Master File rows
// exist and are classified as exclude.
//
// VENUE KEY: Colorado suffixes stacked permits onto a base licence number
// (01-45972-0000 / -0001). Rows are collapsed to one per base licence,
// keeping the strongest licence class; stacked permits land in
// attached_permits.
//
// TIERS: both on-premise tiers load by default. Do NOT filter to spirits
// only - that is what silently dropped 2,118 beer/wine venues before.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "@supabase/supabase-js";

const DATASET = "ier5-5ms2";
const BASE = `https://data.colorado.gov/resource/${DATASET}.json`;
const PAGE = 5000;
const SOURCE_CODE = "US-CO-LED";
const ORDER = ":id";

// Order matters: first match wins. Exclusions before everything, so a permit
// stacked on a venue never out-ranks the venue's own class.
const RULES: [string, string[]][] = [
  ["exclude", [
    "takeout", "delivery permit", "sidewalk service", "warehouse storage",
    "master file", "manager permit", "festival permit", "noncontiguous",
    "alternating proprietor", "related facility", "retail establishment permit",
    "art gallery permit", "tastings permit",
  ]],
  ["off_premise_or_trade", [
    "retail liquor store", "liquor licensed drug store", "liquor-licensed drugstore",
    "wholesale", "importer", "manufacturer", "limited winery", "winery",
    "brewery", "distillery license", "direct shipper", "public transportation",
    "salesroom", "nonresident", "fermented malt beverage off", "liquor store",
  ]],
  ["beer_wine", [
    "beer & wine", "beer and wine", "fermented malt beverage", "bed & breakfast",
  ]],
  ["spirits_on_premise", [
    "hotel & restaurant", "hotel and restaurant", "tavern", "club license",
    "arts license", "brew pub", "distillery pub", "racetrack",
    "entertainment facility", "entertainment district", "lodging facility",
    "resort complex", "campus liquor complex", "optional premises",
    "vintner's restaurant", "vintners restaurant",
  ]],
];

const RANK: Record<string, number> = {
  spirits_on_premise: 0, beer_wine: 1, off_premise_or_trade: 2,
  unknown: 3, exclude: 4,
};

function norm(s: unknown): string {
  return String(s ?? "").toLowerCase().replace(/[^a-z0-9&' ]+/g, " ").trim();
}

function classify(licenceType: unknown): string {
  const v = norm(licenceType);
  for (const [tier, pats] of RULES) {
    if (pats.some((p) => v.includes(norm(p)))) return tier;
  }
  return "unknown";
}

function baseLicence(n: unknown): string {
  return String(n ?? "").split("-").slice(0, 2).join("-");
}

function zip5(z: unknown): string | null {
  const d = String(z ?? "").replace(/\D/g, "");
  return d ? d.slice(0, 5) : null;
}

async function soda(params: string) {
  const res = await fetch(`${BASE}?${params}`, {
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) throw new Error(`Socrata ${res.status} ${res.statusText}`);
  return await res.json() as Record<string, any>[];
}

async function fetchAll(started: number) {
  const out: Record<string, any>[] = [];
  let offset = 0;
  for (;;) {
    const rows = await soda(`$limit=${PAGE}&$offset=${offset}&$order=${ORDER}`);
    if (!rows.length) break;
    out.push(...rows);
    offset += rows.length;
    if (rows.length < PAGE) break;
    if (Date.now() - started > 100000) {
      throw new Error(`time budget hit at offset ${offset} (${out.length} rows)`);
    }
  }
  return out;
}

function collapse(rows: Record<string, any>[]) {
  const byBase = new Map<string, Record<string, any>>();
  const permits = new Map<string, Set<string>>();

  for (const r of rows) {
    const key = baseLicence(r.license_number);
    if (!key) continue;
    const tier = classify(r.license_type);

    if (tier === "exclude") {
      if (!permits.has(key)) permits.set(key, new Set());
      permits.get(key)!.add(String(r.license_type ?? ""));
    }

    const prev = byBase.get(key);
    if (!prev || RANK[tier] < RANK[classify(prev.license_type)]) {
      byBase.set(key, r);
    }
  }

  return [...byBase.entries()].map(([key, r]) => {
    const loc = r.location ?? {};
    return {
      source_account_id: key,
      license_number_full: String(r.license_number ?? ""),
      account_name: r.doing_business_as ?? r.licensee_name ?? null,
      legal_name: r.licensee_name ?? null,
      license_type: r.license_type ?? null,
      tier: classify(r.license_type),
      attached_permits: [...(permits.get(key) ?? [])].sort().join("; "),
      street: r.street_address ?? null,
      city: r.city ?? null,
      state: r.state ?? null,
      postal_code: zip5(r.zip),
      latitude: loc.latitude ? Number(loc.latitude) : null,
      longitude: loc.longitude ? Number(loc.longitude) : null,
      country_code: "US",
      admin_area: "US-CO",
      account_type: "venue",
      source_code: SOURCE_CODE,
      expiry_date: r.expiration ?? null,
      observed_date: new Date().toISOString().slice(0, 10),
    };
  });
}

Deno.serve(async (req: Request) => {
  const started = Date.now();
  const q = new URL(req.url).searchParams;

  try {
    if (q.get("probe")) {
      const rows = await soda(`$limit=50&$offset=5000&$order=${ORDER}`);
      const keys = new Set<string>();
      for (const r of rows) for (const k of Object.keys(r)) keys.add(k);
      return Response.json({
        mode: "probe", dataset: DATASET,
        columns: [...keys].sort(), sample: rows.slice(0, 2), note: "Nothing written.",
      });
    }

    if (q.get("types")) {
      const rows = await soda(
        "$select=license_type,count(1) as n&$group=license_type&$order=count(1) desc&$limit=500",
      );
      return Response.json({
        mode: "types", dataset: DATASET,
        types: rows.map((r) => ({
          license_type: r.license_type, n: Number(r.n), tier: classify(r.license_type),
        })),
        unknown: rows.filter((r) => classify(r.license_type) === "unknown")
          .map((r) => ({ license_type: r.license_type, n: Number(r.n) })),
        note: "Nothing written. `unknown` must be empty before loading.",
      });
    }

    const tierWanted = q.get("tier") ?? "on_premise";
    const includeExpired = !!q.get("include_expired");

    const raw = await fetchAll(started);
    let venues = collapse(raw);
    const beforeFilter = venues.length;

    const tierCounts: Record<string, number> = {};
    for (const v of venues) tierCounts[v.tier] = (tierCounts[v.tier] ?? 0) + 1;

    if (tierWanted === "on_premise") {
      venues = venues.filter((v) =>
        v.tier === "spirits_on_premise" || v.tier === "beer_wine"
      );
    } else if (tierWanted !== "all") {
      venues = venues.filter((v) => v.tier === tierWanted);
    }

    let expiredDropped = 0;
    if (!includeExpired) {
      const today = new Date().toISOString().slice(0, 10);
      const before = venues.length;
      venues = venues.filter((v) =>
        !v.expiry_date || String(v.expiry_date).slice(0, 10) >= today
      );
      expiredDropped = before - venues.length;
    }

    const summary = {
      raw_rows: raw.length,
      venues_after_collapse: beforeFilter,
      tier_counts: tierCounts,
      tier_loaded: tierWanted,
      expired_dropped: expiredDropped,
      to_load: venues.length,
      elapsed_ms: Date.now() - started,
    };

    if (q.get("dry")) {
      return Response.json({ mode: "dry_run", ...summary, note: "Nothing written." });
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    );

    if (q.get("truncate")) {
      const { error } = await supabase
        .from("staging_co_venues").delete().neq("id", -1);
      if (error) throw new Error(`truncate failed: ${error.message}`);
    }

    for (let i = 0; i < venues.length; i += 1000) {
      const { error } = await supabase
        .from("staging_co_venues").insert(venues.slice(i, i + 1000));
      if (error) throw new Error(`insert failed at ${i}: ${error.message}`);
    }

    return Response.json({ mode: "complete", ...summary });
  } catch (err) {
    return Response.json(
      { mode: "error", error: String(err instanceof Error ? err.message : err) },
      { status: 500 },
    );
  }
});
