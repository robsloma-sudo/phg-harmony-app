// ingest-ny
//
// NY State Liquor Authority active-licence list (data.ny.gov, 9s3h-dpkz)
// -> staging_ny_licences, verbatim.
//
//   ?probe=1      column names + sample. No write.
//   ?classes=1    server-side group-by on type/class/description. No write.
//   ?verify=1     compare Socrata's own row count to what is staged. No write.
//   ?limit= ?offset= ?max= ?truncate=1
//
// PAGING: every paged query carries $order=:id. Socrata does NOT guarantee a
// stable row order otherwise, and unordered paging silently BOTH duplicates
// and skips rows - an earlier run produced 30,000 rows containing only 23,621
// distinct licences. The duplicates were visible; the skipped rows were not.
// Do not remove the $order.
//
// NY specifics:
//   - `class` is a 4-digit code; `description` is NOT unique to a class
//     ("Restaurant" is both 0340 and 0240), so tiering must key on `class`.
//   - `georeference` is a GeoJSON Point - NY arrives pre-geocoded.
//   - `premisescounty` is populated; no ZIP-to-county crosswalk needed.
//   - ACTIVE-ONLY snapshot: lapsed licences disappear rather than showing as
//     expired, so losses come from differencing snapshots. retrieved_at is
//     stamped per row and nothing is overwritten.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "@supabase/supabase-js";

const DATASET = "9s3h-dpkz";
const BASE = `https://data.ny.gov/resource/${DATASET}.json`;
const PAGE = 5000;
const SOURCE_CODE = "US-NY-SLA";
const ORDER = ":id"; // stable paging key. See PAGING note above.

async function sha256(s: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function soda(params: string) {
  const res = await fetch(`${BASE}?${params}`, {
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Socrata ${res.status} ${res.statusText} for ${params}`);
  }
  return await res.json() as Record<string, unknown>[];
}

Deno.serve(async (req: Request) => {
  const started = Date.now();
  const q = new URL(req.url).searchParams;

  try {
    if (q.get("probe")) {
      const rows = await soda(`$limit=5&$order=${ORDER}`);
      const keys = new Set<string>();
      for (const r of rows) for (const k of Object.keys(r)) keys.add(k);
      return Response.json({
        mode: "probe", dataset: DATASET,
        columns: [...keys].sort(), sample: rows.slice(0, 2),
        note: "Nothing written.",
      });
    }

    if (q.get("classes")) {
      const rows = await soda(
        "$select=type,class,description,count(1) as n" +
        "&$group=type,class,description&$order=count(1) desc&$limit=2000",
      );
      return Response.json({
        mode: "classes", dataset: DATASET,
        distinct_classes: rows.length,
        total_rows: rows.reduce((a, r) => a + Number(r.n ?? 0), 0),
        classes: rows, note: "Nothing written.",
      });
    }

    if (q.get("verify")) {
      const [{ n }] = await soda("$select=count(1) as n") as { n: string }[];
      return Response.json({
        mode: "verify", dataset: DATASET, socrata_row_count: Number(n),
        note: "Compare against count(*) in staging_ny_licences.",
      });
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    );

    if (q.get("truncate")) {
      const { error } = await supabase
        .from("staging_ny_licences").delete().neq("id", -1);
      if (error) throw new Error(`truncate failed: ${error.message}`);
    }

    const pageSize = Math.min(Number(q.get("limit") ?? PAGE), PAGE);
    const max = q.get("max") ? Number(q.get("max")) : Infinity;
    let offset = Number(q.get("offset") ?? 0);

    const retrievedAt = new Date().toISOString();
    let inserted = 0, pages = 0;

    while (inserted < max) {
      const want = Math.min(pageSize, max - inserted);
      const rows = await soda(`$limit=${want}&$offset=${offset}&$order=${ORDER}`);
      if (!rows.length) break;

      const payload = await Promise.all(rows.map(async (r) => ({
        source_code: SOURCE_CODE,
        dataset_id: DATASET,
        row_data: r,
        row_sha256: await sha256(JSON.stringify(r, Object.keys(r).sort())),
        retrieved_at: retrievedAt,
      })));

      const { error } = await supabase
        .from("staging_ny_licences").insert(payload);
      if (error) throw new Error(`insert failed at offset ${offset}: ${error.message}`);

      inserted += rows.length;
      offset += rows.length;
      pages += 1;

      if (rows.length < want) break;

      if (Date.now() - started > 110_000) {
        return Response.json({
          mode: "partial", inserted, pages, resume_offset: offset,
          retrieved_at: retrievedAt,
          note: `Time budget reached. Re-run with ?offset=${offset} to continue.`,
        });
      }
    }

    return Response.json({
      mode: "complete", inserted, pages, next_offset: offset,
      retrieved_at: retrievedAt, elapsed_ms: Date.now() - started,
    });
  } catch (err) {
    return Response.json(
      { mode: "error", error: String(err instanceof Error ? err.message : err) },
      { status: 500 },
    );
  }
});
