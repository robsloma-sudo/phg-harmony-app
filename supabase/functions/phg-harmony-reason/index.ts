// phg-harmony-reason v0.1 — DRY RUN ONLY
// Harmony is the single user-facing identity; Claude is the reasoning provider.
// Invariants: no DB writes, no capability execution, no proposals, no approvals,
// no routing changes. The production phg-language-interpreter remains authoritative.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const VERSION = "0.1";
const MODEL = "claude-sonnet-4-5-20250929";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS"
};
const out = (x: any, s = 200) =>
  new Response(JSON.stringify(x), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

// Sanitized failure: never echo upstream payloads, prompts, tokens or secrets.
function fail(code: string, status: number, hint?: string) {
  console.error(JSON.stringify({ evt: "harmony_reason_error", version: VERSION, code }));
  return out({ status: "error", mode: "dry_run", version: VERSION, code, hint: hint ?? null }, status);
}

const INTENTS = ["navigation","cocktail_menu_training_workflow","menu_training_workflow","price_change_workflow","period_review","management_operations","variance_explanation","pl_analysis","budget_forecast","labor_analysis","expense_analysis","inventory_analysis","purchasing","cogs_analysis","training_generation","cocktail_development","menu_workflow","sales_analysis","market_venue_research","retail_sales_analysis","command_center"];
const EXEC = ["read_only","proposal_required","approval_required"];
const TOOLS = ["cocktail","brand_history","sales","retail_sales","local_retail","venue_research","labor","cogs","inventory","purchasing","financial","menu","general"];
const DISPLAY = ["standard","map","timeline","chart","comparison","recipe","network","evidence","builder"];

// Mirrors the production interpreter contract so shadow output is directly comparable.
const SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    normalized_text: { type: "string" },
    intent_hint: { type: "string", enum: INTENTS },
    execution_class_hint: { type: "string", enum: EXEC },
    confidence: { type: "number" },
    needs_clarification: { type: "boolean" },
    clarification_question: { type: ["string", "null"] },
    context_patch: { type: "object" },
    brief_bullet: { type: "string" },
    recent_points: { type: "array", items: { type: "string" } },
    tool_context: { type: "string", enum: TOOLS },
    tool_entities: { type: "array", items: { type: "string" } },
    display_mode: { type: "string", enum: DISPLAY },
    display_context: { type: "object" },
    notes: { type: "array", items: { type: "string" } }
  },
  required: ["normalized_text","intent_hint","execution_class_hint","confidence","needs_clarification","clarification_question","context_patch","brief_bullet","recent_points","tool_context","tool_entities","display_mode","display_context","notes"]
};

// Server-side validation. The model is never trusted to have honoured the schema.
function validate(o: any): string[] {
  const e: string[] = [];
  if (!o || typeof o !== "object") return ["not_an_object"];
  for (const k of SCHEMA.required) if (!(k in o)) e.push(`missing:${k}`);
  if (typeof o.normalized_text !== "string" || !o.normalized_text.trim()) e.push("bad:normalized_text");
  if (!INTENTS.includes(o.intent_hint)) e.push("bad:intent_hint");
  if (!EXEC.includes(o.execution_class_hint)) e.push("bad:execution_class_hint");
  if (typeof o.confidence !== "number" || o.confidence < 0 || o.confidence > 1) e.push("bad:confidence");
  if (typeof o.needs_clarification !== "boolean") e.push("bad:needs_clarification");
  if (o.clarification_question !== null && typeof o.clarification_question !== "string") e.push("bad:clarification_question");
  if (typeof o.context_patch !== "object" || o.context_patch === null || Array.isArray(o.context_patch)) e.push("bad:context_patch");
  if (typeof o.display_context !== "object" || o.display_context === null || Array.isArray(o.display_context)) e.push("bad:display_context");
  if (typeof o.brief_bullet !== "string") e.push("bad:brief_bullet");
  if (!TOOLS.includes(o.tool_context)) e.push("bad:tool_context");
  if (!DISPLAY.includes(o.display_mode)) e.push("bad:display_mode");
  for (const k of ["recent_points","tool_entities","notes"]) {
    if (!Array.isArray(o[k]) || o[k].some((x: any) => typeof x !== "string")) e.push(`bad:${k}`);
  }
  return e;
}

function trimCatalog(c: any) {
  c = c || {};
  return {
    account: c.account || null,
    locations: (c.locations || []).slice(0, 50),
    menu_projects: (c.menu_projects || []).slice(0, 50),
    menu_items: (c.menu_items || []).slice(0, 200),
    ingredients: (c.ingredients || []).slice(0, 400),
    vendors: (c.vendors || []).slice(0, 150),
    labor_roles: (c.labor_roles || []).slice(0, 150),
    expense_categories: (c.expense_categories || []).slice(0, 150),
    cocktails: (c.cocktails || []).slice(0, 350)
  };
}

function localDate(tz?: string | null) {
  try {
    const p = new Intl.DateTimeFormat("en-CA", { timeZone: tz || "UTC", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
    const m: any = {}; for (const x of p) m[x.type] = x.value;
    return `${m.year}-${m.month}-${m.day}`;
  } catch { return new Date().toISOString().slice(0, 10); }
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return fail("method_not_allowed", 405);

  const url = Deno.env.get("SUPABASE_URL");
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!url || !service) return fail("runtime_configuration_missing", 500);
  if (!anthropicKey) return fail("reasoning_provider_not_configured", 503);

  // --- AUTH: identical pattern to the production interpreter. JWT is the only identity source.
  const auth = req.headers.get("Authorization") || "";
  if (!auth.toLowerCase().startsWith("bearer ")) return fail("login_required", 401);
  const jwt = auth.slice(7).trim();
  const sb = createClient(url, service, { auth: { persistSession: false } });
  const { data: ud, error: ue } = await sb.auth.getUser(jwt);
  if (ue || !ud?.user) return fail("invalid_or_expired_login", 401);
  const user = ud.user;

  const b = await req.json().catch(() => ({} as any));
  const rawText = String(b?.user_text || "").trim();
  if (!rawText) return fail("user_text_required", 400);
  if (rawText.length > 8000) return fail("user_text_too_long", 413);

  // --- AUTHORIZATION: membership enforced server-side by phg_language_context.
  // account_id/menu_project_id from the client are proposals only; the RPC validates membership.
  const { data: catalog, error: ctxErr } = await sb.rpc("phg_language_context", {
    p_user_id: user.id,
    p_account_id: b?.account_id || null,
    p_menu_project_id: b?.menu_project_id || null
  });
  if (ctxErr) return fail("account_authorization_failed", 403);
  const cat = trimCatalog(catalog);
  if (!cat.account?.id) return fail("no_active_account_membership", 403);

  const active = b?.active_context || {};
  const recent = Array.isArray(b?.recent_conversation) ? b.recent_conversation.slice(-10) : [];

  const system = [
    "You are the reasoning provider behind Harmony, Perfect Harmony Group's operating intelligence.",
    "Harmony is the only user-facing identity. Never refer to yourself as a separate assistant, never name your provider, and never speak in the first person as a distinct AI.",
    "",
    "Your ONLY job in this call is to interpret language into a canonical PHG request. You are running in DRY RUN mode.",
    "You do not execute anything. You do not read business data. You do not write. You do not approve.",
    "You are not the database, the authorization system, the financial engine, the taxonomy owner, or a SQL agent.",
    "Supabase and PHG's deterministic engines are authoritative for every number and every fact.",
    "",
    "Routing rules:",
    "- Building/creating/designing a WHOLE beverage menu, cocktail menu or drink list is menu_workflow. Never downgrade it to command_center.",
    "- Building ONE cocktail is cocktail_development.",
    "- 'Make me a margarita menu' is menu_workflow, not a single Margarita.",
    "- Follow-ups such as 'what's the progress' preserve the active workflow from context.",
    "- Venue/restaurant geography research is market_venue_research, read_only, tool_context venue_research, display_mode map, with grounded city/state in display_context. Never guess missing geography.",
    "- Creating or editing menu content or design state is proposal_required.",
    "- Anything consequential (writes, closes, approvals, publication, price changes) is proposal_required or approval_required. NEVER read_only.",
    "",
    "Integrity rules:",
    "- Never invent business data, costs, sales, thresholds or entities.",
    "- Correct likely speech-to-text errors ONLY when the supplied PHG catalog strongly grounds the intended word.",
    "- normalized_text must preserve explicit ingredients, brands, sizes, prices, formats and requested outputs.",
    "- If a subjective threshold (expensive, high, low, premium) is used with no definition in context, set needs_clarification=true rather than inventing a cutoff.",
    "- If one consequential target is genuinely ambiguous, set needs_clarification and ask exactly ONE concise question.",
    `- Relative dates resolve against account-local date ${localDate(cat.account?.timezone)}.`,
    "",
    "Return your answer ONLY by calling the emit_interpretation tool. Do not write prose."
  ].join("\n");

  let parsed: any = null;
  let providerError: string | null = null;
  const started = Date.now();

  try {
    const rr = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": anthropicKey,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 2000,
        system,
        tools: [{ name: "emit_interpretation", description: "Emit the canonical PHG interpretation.", input_schema: SCHEMA }],
        tool_choice: { type: "tool", name: "emit_interpretation" },
        messages: [{
          role: "user",
          content: JSON.stringify({
            raw_transcript: rawText,
            active_context: active,
            recent_conversation: recent,
            catalog: cat
          })
        }]
      })
    });

    if (!rr.ok) {
      // Capture status class only. Upstream body is never surfaced or logged.
      providerError = `provider_http_${rr.status}`;
    } else {
      const raw = await rr.json();
      const block = Array.isArray(raw?.content)
        ? raw.content.find((c: any) => c?.type === "tool_use" && c?.name === "emit_interpretation")
        : null;
      if (block?.input) parsed = block.input;
      else providerError = "provider_returned_no_structured_output";
    }
  } catch {
    providerError = "provider_unreachable";
  }

  const latency_ms = Date.now() - started;

  if (!parsed) {
    return out({
      status: "dry_run_failed", mode: "dry_run", version: VERSION, model: MODEL,
      code: providerError, schema_valid: false, production_impact: "none",
      latency_ms
    }, 502);
  }

  const errors = validate(parsed);

  // Dry-run safety net: this function can never imply a consequential action is safe to auto-run.
  const consequential = parsed.execution_class_hint !== "read_only";

  console.log(JSON.stringify({
    evt: "harmony_reason_dry_run", version: VERSION, model: MODEL,
    account_id: cat.account.id, user_id: user.id,
    intent: parsed.intent_hint, execution_class: parsed.execution_class_hint,
    schema_valid: errors.length === 0, error_count: errors.length,
    latency_ms, wrote_to_database: false
  }));

  return out({
    status: errors.length === 0 ? "dry_run_ok" : "dry_run_schema_invalid",
    mode: "dry_run",
    version: VERSION,
    model: MODEL,
    schema_valid: errors.length === 0,
    schema_errors: errors,
    interpretation: parsed,
    authoritative: false,
    production_interpreter_authoritative: true,
    wrote_to_database: false,
    executed_capabilities: false,
    created_proposals: false,
    requires_proposal_and_explicit_approval: consequential,
    account_id: cat.account.id,
    latency_ms,
    interpreted_at: new Date().toISOString()
  });
});
