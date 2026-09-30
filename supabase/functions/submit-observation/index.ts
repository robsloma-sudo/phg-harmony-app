// submit-observation
// Batched, idempotent observation intake for Global Tequila Trends.
//
// Auth: shared secret in the x-agent-secret header. verify_jwt is OFF because
// the caller is n8n, which has no user identity. The secret check below IS the
// authentication - if it is removed, this endpoint is open to the internet.
//
// The insert itself lives in public.submit_observations(), a security definer
// Postgres function, so the whole batch is one atomic statement and duplicates
// are handled by the table's own unique constraints rather than by app logic.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const MAX_BATCH = 500;

const SIGNAL_TYPES = new Set([
  "label_approval", "brand_launch", "product_launch", "product_listing",
  "provincial_listing", "state_listing", "retail_listing", "menu_pour",
  "menu_cocktail", "back_bar_presence", "in_stock", "out_of_stock",
  "price_observed", "importer_appointment", "distributor_appointment",
  "new_market_entry", "airport_duty_free_listing", "hotel_program", "award",
  "press_mention", "event_activation", "social_mention", "account_opening",
  "account_closing",
]);

const EVIDENCE_CLASSES = new Set(["primary", "supporting", "early_signal"]);

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// Constant-time comparison. A naive === leaks length and prefix information
// through timing, which is a real if unglamorous way to guess a secret.
function secretMatches(given: string | null, expected: string): boolean {
  if (!given) return false;
  const a = new TextEncoder().encode(given);
  const b = new TextEncoder().encode(expected);
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return json({ error: "method_not_allowed" }, 405);
  }

  const agentSecret = Deno.env.get("AGENT_SECRET");
  if (!agentSecret) {
    console.error("AGENT_SECRET is not configured");
    return json({ error: "server_misconfigured" }, 500);
  }

  if (!secretMatches(req.headers.get("x-agent-secret"), agentSecret)) {
    return json({ error: "unauthorized" }, 401);
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: "invalid_json" }, 400);
  }

  const sourceId = body.source_id;
  const observations = body.observations;

  if (typeof sourceId !== "string" || !sourceId) {
    return json({ error: "source_id is required" }, 400);
  }
  if (!Array.isArray(observations)) {
    return json({ error: "observations must be an array" }, 400);
  }
  if (observations.length > MAX_BATCH) {
    // Reject loudly rather than truncating. Silent truncation would drop
    // evidence and report success.
    return json(
      { error: "batch_too_large", max: MAX_BATCH, received: observations.length },
      413,
    );
  }

  // Shape validation before touching the database, so a single bad row does
  // not roll back an otherwise valid batch of 500.
  const errors: Array<{ index: number; reason: string }> = [];
  observations.forEach((o: Record<string, unknown>, i: number) => {
    if (o === null || typeof o !== "object") {
      errors.push({ index: i, reason: "not_an_object" });
      return;
    }
    if (typeof o.signal_type !== "string" || !SIGNAL_TYPES.has(o.signal_type)) {
      errors.push({ index: i, reason: `invalid_signal_type: ${o.signal_type}` });
    }
    if (
      o.evidence_class !== undefined && o.evidence_class !== null &&
      !EVIDENCE_CLASSES.has(String(o.evidence_class))
    ) {
      errors.push({ index: i, reason: `invalid_evidence_class: ${o.evidence_class}` });
    }
    if (o.confidence !== undefined && o.confidence !== null) {
      const c = Number(o.confidence);
      if (!Number.isFinite(c) || c < 0 || c > 1) {
        errors.push({ index: i, reason: `confidence_out_of_range: ${o.confidence}` });
      }
    }
  });

  if (errors.length > 0) {
    return json({
      error: "validation_failed",
      submitted: observations.length,
      created: 0,
      duplicates: 0,
      failed: errors.length,
      errors,
    }, 400);
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { auth: { persistSession: false } },
  );

  const { data, error } = await supabase.rpc("submit_observations", {
    p_source_id: sourceId,
    p_observations: observations,
  });

  if (error) {
    console.error("submit_observations failed", error.message);
    return json({ error: "insert_failed", detail: error.message }, 500);
  }

  // A duplicate is not an error. Re-running a window must be free, because a
  // large backfill will be interrupted at some point and restarted.
  return json({
    submitted: data.submitted,
    created: data.created,
    duplicates: data.duplicates,
    failed: 0,
    observation_ids: data.observation_ids,
    errors: [],
  }, 200);
});
