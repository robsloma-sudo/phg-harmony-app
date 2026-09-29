// ingest-iowa
// Streams an Iowa Data Hub year file, keeps only tequila rows, writes them to
// staging. Driven by pg_cron; nothing is uploaded by hand.
//
// DESIGN NOTE - why there is no byte-offset resume any more.
//
// The first version resumed mid-file using an offset. Iowa's server does NOT
// honour HTTP Range (confirmed: supports_range = false), so every resumed run
// re-streamed from byte zero and discarded what it had already processed.
// Each attempt therefore spent most of its budget re-downloading, and made
// less progress than the one before. Twenty attempts produced 20,010 distinct
// rows and 315,000 duplicates - a quadratic dead end.
//
// The fix is to stop resuming and instead give one run enough time to finish a
// whole year. Supabase allows up to 400s wall clock; the budget below is set
// under that with margin. A year is streamed once, filtered on the fly, and
// only matching rows are ever held in memory.
//
// If a run still cannot finish a year, the honest outcome is a failure that
// says so - not silent partial progress that looks like success.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const TEQUILA_CODES = new Set(["1022100", "1022200"]);
const TIME_BUDGET_MS = 340_000;   // under Supabase's 400s ceiling
const FLUSH_ROWS = 500;

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status, headers: { "Content-Type": "application/json" },
  });
}

function eq(a: string, b: string): boolean {
  const x = new TextEncoder().encode(a.trim());
  const y = new TextEncoder().encode(b.trim());
  if (x.length !== y.length) return false;
  let d = 0;
  for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i];
  return d === 0;
}

async function sha256Hex(s: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function splitCsv(line: string): string[] {
  const out: string[] = [];
  let cur = "", q = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (q) {
      if (c === '"') { if (line[i + 1] === '"') { cur += '"'; i++; } else q = false; }
      else cur += c;
    } else if (c === '"') q = true;
    else if (c === ",") { out.push(cur); cur = ""; }
    else cur += c;
  }
  out.push(cur);
  return out;
}

Deno.serve(async (req: Request) => {
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { auth: { persistSession: false } },
  );

  const { data: secretRow } = await supabase
    .from("internal_secrets").select("value").eq("key", "ingest_token").single();
  const expected = secretRow?.value ?? "";
  if (!expected || !eq(req.headers.get("x-ingest-token") ?? "", expected)) {
    return json({ error: "unauthorized" }, 401);
  }

  // Claim a job atomically so overlapping cron ticks cannot both take the
  // same year. Only 'pending' is claimable; 'running' is left alone.
  const { data: claimed } = await supabase.rpc("claim_ingest_job");
  const job = claimed?.[0] ?? claimed;
  if (!job || !job.id) return json({ status: "idle", message: "no claimable job" });

  const started = Date.now();
  const url = `https://idh-be.iowa.gov/api/v1/datasets/${job.dataset_id}/rows.csv`;

  let res: Response;
  try {
    res = await fetch(url);
  } catch (e) {
    await supabase.from("ingest_jobs").update({
      status: "pending", last_error: `fetch failed: ${String(e).slice(0, 300)}`,
    }).eq("id", job.id);
    return json({ status: "retry", year: job.data_year, error: String(e) });
  }

  if (!res.ok) {
    await supabase.from("ingest_jobs").update({
      status: "pending", last_error: `http ${res.status}`,
    }).eq("id", job.id);
    return json({ status: "retry", year: job.data_year, http: res.status });
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let carry = "", header: string[] | null = null;
  const idx: Record<string, number> = {};
  let seen = 0, matched = 0, inserted = 0, timedOut = false;
  let batch: Record<string, string>[] = [];

  async function flush() {
    if (!batch.length) return;
    const { data, error } = await supabase.rpc("ingest_iowa_rows", {
      p_year: job.data_year, p_rows: batch,
    });
    if (error) throw new Error(`insert failed: ${error.message}`);
    inserted += Number(data ?? 0);
    batch = [];
  }

  try {
    while (true) {
      if (Date.now() - started > TIME_BUDGET_MS) { timedOut = true; break; }
      const { done, value } = await reader.read();
      if (done) break;

      carry += decoder.decode(value!, { stream: true });
      const lines = carry.split("\n");
      carry = lines.pop() ?? "";

      for (const raw of lines) {
        const line = raw.replace(/\r$/, "");
        if (!line) continue;
        if (!header) {
          header = splitCsv(line).map((h) => h.trim().replace(/^"|"$/g, ""));
          header.forEach((h, i) => { idx[h] = i; });
          continue;
        }
        seen++;
        const f = splitCsv(line);
        const code = (f[idx["category_code"]] ?? "").trim();
        if (!TEQUILA_CODES.has(code)) continue;

        matched++;
        const g = (k: string) => (f[idx[k]] ?? "").trim();
        batch.push({
          row_sha256: await sha256Hex(line),
          invoice_id: g("invoice_id"), ordered_on: g("ordered_on"),
          store_no: g("store_no"), store_name: g("store_name"),
          store_address: g("store_address"), store_city: g("store_city"),
          store_zip_code: g("store_zip_code"), county_fips_code: g("county_fips_code"),
          county_name: g("county_name"), category_code: code,
          category_name: g("category_name"), vendor_number: g("vendor_number"),
          vendor_name: g("vendor_name"), item_no: g("item_no"),
          im_desc: g("im_desc"), pack: g("pack"),
          bottle_volume_ml: g("bottle_volume_ml"),
          state_bottle_cost: g("state_bottle_cost"),
          state_bottle_retail: g("state_bottle_retail"),
        });
        if (batch.length >= FLUSH_ROWS) await flush();
      }
    }
    await flush();
    await reader.cancel();
  } catch (e) {
    await supabase.from("ingest_jobs").update({
      status: "pending", last_error: String(e).slice(0, 500),
      rows_seen: seen, rows_matched: matched,
      rows_inserted: job.rows_inserted + inserted,
    }).eq("id", job.id);
    return json({ status: "error", year: job.data_year, error: String(e), inserted });
  }

  // A run either finishes the year or it does not. There is no partial
  // success here, because a partial pass cannot be resumed on this server.
  await supabase.from("ingest_jobs").update({
    status: timedOut ? "failed" : "complete",
    rows_seen: seen,
    rows_matched: matched,
    rows_inserted: job.rows_inserted + inserted,
    resume_offset: 0,
    completed_at: timedOut ? null : new Date().toISOString(),
    last_error: timedOut
      ? `ran out of time after ${Math.round((Date.now() - started) / 1000)}s having scanned ${seen} rows; server does not support HTTP Range so this year cannot be resumed and needs a different approach`
      : null,
  }).eq("id", job.id);

  return json({
    status: timedOut ? "timed_out" : "complete",
    year: job.data_year,
    rows_seen: seen,
    tequila_matched: matched,
    inserted_this_run: inserted,
    duration_ms: Date.now() - started,
  });
});
