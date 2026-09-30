// probe-iowa  --  TEMPORARY diagnostic. Resolves DQI-0002. Delete after use.
//
// Question: does the Iowa Data Hub endpoint support server-side filtering,
// paging, or HTTP range requests? If yes, ingestion is a series of small
// targeted pulls. If no, every refresh means streaming the whole ~600MB
// year file and filtering client-side - a different pipeline shape.
//
// Reads response headers and the first few KB only. Never downloads the file.
// Touches no secrets and writes nothing.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const BASE = "https://idh-be.iowa.gov/api/v1/datasets/1262";
const TOKEN = "<REDACTED:hardcoded access token>";

async function probe(label: string, url: string, headers: Record<string, string> = {}) {
  const out: Record<string, unknown> = { label, url };
  try {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), 15_000);
    const r = await fetch(url, { headers, signal: ctl.signal });
    clearTimeout(t);
    out.status = r.status;
    out.content_type = r.headers.get("content-type");
    out.content_length = r.headers.get("content-length");
    out.accept_ranges = r.headers.get("accept-ranges");
    out.content_range = r.headers.get("content-range");
    out.content_encoding = r.headers.get("content-encoding");

    if (r.body) {
      const reader = r.body.getReader();
      const { value } = await reader.read();
      await reader.cancel();
      const text = new TextDecoder().decode(value ?? new Uint8Array());
      out.first_chunk_bytes = value?.length ?? 0;
      out.first_300 = text.slice(0, 300);
      out.newlines_in_chunk = (text.match(/\n/g) || []).length;
    }
  } catch (e) {
    out.error = String(e);
  }
  return out;
}

Deno.serve(async (req: Request) => {
  const u = new URL(req.url);
  if (u.searchParams.get("t") !== TOKEN) {
    return new Response(JSON.stringify({ error: "unauthorized" }), {
      status: 401, headers: { "Content-Type": "application/json" },
    });
  }

  const results = [];
  results.push(await probe("1 plain csv", `${BASE}/rows.csv`));
  results.push(await probe("2 range first 2KB", `${BASE}/rows.csv`, { Range: "bytes=0-2047" }));
  results.push(await probe("3 limit param", `${BASE}/rows.csv?limit=5`));
  results.push(await probe("4 page+pageSize", `${BASE}/rows.csv?page=1&pageSize=5`));
  results.push(await probe("5 offset+limit", `${BASE}/rows.csv?offset=0&limit=5`));
  results.push(await probe("6 filter category_code", `${BASE}/rows.csv?category_code=1022200&limit=5`));
  results.push(await probe("7 json limit", `${BASE}/rows.json?limit=5`));
  results.push(await probe("8 columns.json", `${BASE}/columns.json`));

  return new Response(JSON.stringify(results, null, 2), {
    status: 200, headers: { "Content-Type": "application/json" },
  });
});
