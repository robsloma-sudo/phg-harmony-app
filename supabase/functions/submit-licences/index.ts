// submit-licences
// Intake for alcohol licence register rows scraped from a state portal.
//
// Same contract shape as submit-observation: shared-secret header, batches of
// 500, duplicates reported rather than treated as failures. External tools
// never touch tables directly - everything passes through here so it can be
// validated first.
//
// licence_status is stored VERBATIM. "Expired" and "cancelled" mean different
// things - a late renewal is not a closed bar - and normalising them here
// would bury a guess inside the evidence.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const MAX_BATCH = 500;

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function secretMatches(given: string | null, expected: string): boolean {
  if (!given) return false;
  const a = new TextEncoder().encode(given.trim());
  const b = new TextEncoder().encode(expected.trim());
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a[i] ^ b[i];
  return d === 0;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405);

  const agentSecret = Deno.env.get("AGENT_SECRET");
  if (!agentSecret) return json({ error: "unauthorized" }, 401);
  if (!secretMatches(req.headers.get("x-agent-secret"), agentSecret)) {
    return json({ error: "unauthorized" }, 401);
  }

  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { return json({ error: "invalid_json" }, 400); }

  const sourceCode = body.source_code;
  const rows = body.rows;
  const evidenceUrl = body.evidence_url;

  if (typeof sourceCode !== "string" || !sourceCode) {
    return json({ error: "source_code is required" }, 400);
  }
  if (!Array.isArray(rows)) {
    return json({ error: "rows must be an array" }, 400);
  }
  if (rows.length > MAX_BATCH) {
    return json({ error: "batch_too_large", max: MAX_BATCH, received: rows.length }, 413);
  }

  // Provenance must point at the publisher. A scraper URL, cache or proxy in
  // evidence_url breaks the evidence chain, so it is rejected outright.
  if (typeof evidenceUrl !== "string" || !/^https:\/\/[^/]*iowa\.gov(\/|$)/i.test(evidenceUrl)) {
    return json({
      error: "invalid_evidence_url",
      detail: "evidence_url must be the official iowa.gov page, not an intermediary",
    }, 400);
  }

  const errors: Array<{ index: number; reason: string }> = [];
  rows.forEach((r: Record<string, unknown>, i: number) => {
    if (r === null || typeof r !== "object") {
      errors.push({ index: i, reason: "not_an_object" });
      return;
    }
    if (!r.licence_number && !r.business_name) {
      errors.push({ index: i, reason: "needs licence_number or business_name" });
    }
    if (!r.licence_status) {
      errors.push({ index: i, reason: "licence_status is required and must be verbatim" });
    }
  });

  if (errors.length) {
    return json({
      error: "validation_failed",
      submitted: rows.length, created: 0, duplicates: 0,
      failed: errors.length, errors: errors.slice(0, 50),
    }, 400);
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { auth: { persistSession: false } },
  );

  const { data, error } = await supabase.rpc("submit_licences", {
    p_source_code: sourceCode,
    p_permit_type_run: body.permit_type_run ?? null,
    p_evidence_url: evidenceUrl,
    p_retrieved_at: body.retrieved_at ?? null,
    p_rows: rows,
  });

  if (error) {
    console.error("submit_licences failed", error.message);
    return json({ error: "insert_failed", detail: error.message }, 500);
  }

  // A duplicate means this exact licence state was already recorded. Expected
  // on every refresh, and on any retry of an interrupted run.
  return json({
    submitted: data.submitted,
    created: data.created,
    duplicates: data.duplicates,
    failed: 0,
    errors: [],
  }, 200);
});
