// phg-harmony-shadow-capture v0.1 -- PHG Milestone 2 SHADOW MODE
// Harmony is the single user-facing identity; Claude is the reasoning provider.
//
// INVARIANTS (structural, not merely intended):
//  - This function is invoked AFTER the authoritative interpreter has already responded.
//  - Its return value is discarded by the caller. It cannot alter any user-facing response,
//    routing, capability execution, approval behaviour, task/menu/financial/publication state
//    or taxonomy.
//  - It writes to exactly ONE table: phg.interpretation_shadow_runs.
//  - It never stores JWTs, API keys, authorization headers or hidden chain-of-thought.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const SHADOW_FUNCTION_VERSION = "0.1";
const PROMPT_VERSION = "m2-shadow-2026-09-24";
const MODEL = "claude-sonnet-4-5-20250929";
const PROVIDER_TIMEOUT_MS = 20000;

const ONLY_TABLE = "interpretation_shadow_runs";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS"
};
const out = (x: any, s = 200) =>
  new Response(JSON.stringify(x), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

const INTENTS = ["navigation","cocktail_menu_training_workflow","menu_training_workflow","price_change_workflow","period_review","management_operations","variance_explanation","pl_analysis","budget_forecast","labor_analysis","expense_analysis","inventory_analysis","purchasing","cogs_analysis","training_generation","cocktail_development","menu_workflow","sales_analysis","market_venue_research","retail_sales_analysis","command_center"];
const EXEC = ["read_only","proposal_required","approval_required"];
const TOOLS = ["cocktail","brand_history","sales","retail_sales","local_retail","venue_research","labor","cogs","inventory","purchasing","financial","menu","general"];
const DISPLAY = ["standard","map","timeline","chart","comparison","recipe","network","evidence","builder"];

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
  if (!TOOLS.includes(o.tool_context)) e.push("bad:tool_context");
  if (!DISPLAY.includes(o.display_mode)) e.push("bad:display_mode");
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

// Context summary only -- never the full catalog, never credentials.
function contextSummary(active: any) {
  const a = active || {};
  return {
    has_menu_project: !!a.menu_project_id,
    menu_project_id: a.menu_project_id || null,
    location_key: a.location_key || null,
    workflow_intent: a.workflow_intent || null,
    keys: Object.keys(a).slice(0, 40)
  };
}

// The active workflow a follow-up should preserve ("what's the progress?").
function activeWorkflow(active: any): string | null {
  const a = active || {};
  if (a.workflow_intent && INTENTS.includes(a.workflow_intent)) return a.workflow_intent;
  if (a.menu_project_id) return "menu_workflow";
  return null;
}

const riskRank = (x: string | null) => {
  const i = EXEC.indexOf(String(x || ""));
  return i < 0 ? null : i;
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return out({ status: "error", code: "method_not_allowed" }, 405);

  const url = Deno.env.get("SUPABASE_URL");
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!url || !service) return out({ status: "error", code: "runtime_configuration_missing" }, 500);

  // AUTH: reuse the existing PHG model. The forwarded user JWT is the only identity source.
  const auth = req.headers.get("Authorization") || "";
  if (!auth.toLowerCase().startsWith("bearer ")) return out({ status: "error", code: "login_required" }, 401);
  const jwt = auth.slice(7).trim();
  const sb = createClient(url, service, { auth: { persistSession: false } });
  const { data: ud, error: ue } = await sb.auth.getUser(jwt);
  if (ue || !ud?.user) return out({ status: "error", code: "invalid_or_expired_login" }, 401);
  const user = ud.user;

  const b = await req.json().catch(() => ({} as any));
  const rawText = String(b?.raw_text || "").trim();
  const correlationId = String(b?.correlation_id || "").trim();
  if (!rawText || !correlationId) return out({ status: "error", code: "correlation_id_and_raw_text_required" }, 400);

  // AUTHORIZATION: membership is enforced server-side by phg_language_context.
  // A client-supplied account_id is a proposal only; the RPC validates it.
  const { data: catalog, error: ctxErr } = await sb.rpc("phg_language_context", {
    p_user_id: user.id,
    p_account_id: b?.account_id || null,
    p_menu_project_id: b?.menu_project_id || null
  });
  if (ctxErr) return out({ status: "error", code: "account_authorization_failed" }, 403);
  const cat = trimCatalog(catalog);
  const accountId = cat.account?.id;
  if (!accountId) return out({ status: "error", code: "no_active_account_membership" }, 403);

  // ELIGIBILITY: default OFF. A missing settings row means disabled.
  const { data: cfg } = await sb.schema("phg").from("shadow_mode_settings")
    .select("shadow_enabled,sample_rate").eq("account_id", accountId).maybeSingle();
  const enabled = !!cfg?.shadow_enabled;
  const sampleRate = typeof cfg?.sample_rate === "number" ? cfg.sample_rate : 1;
  if (!enabled) return out({ status: "skipped", reason: "shadow_disabled_for_account", wrote_shadow_row: false });
  if (Math.random() > sampleRate) return out({ status: "skipped", reason: "not_sampled", wrote_shadow_row: false });

  const prod = b?.production || {};
  const active = b?.active_context || {};
  const recent = Array.isArray(b?.recent_conversation) ? b.recent_conversation.slice(-10) : [];

  const system = [
    "You are the reasoning provider behind Harmony, Perfect Harmony Group's operating intelligence.",
    "Harmony is the only user-facing identity. Never refer to yourself as a separate assistant and never name your provider.",
    "",
    "You are running in SHADOW MODE. Your output is recorded for comparison ONLY.",
    "PHG's existing interpreter is authoritative. Nothing you return reaches the user, changes routing,",
    "executes a capability, creates a proposal, or grants an approval.",
    "You are not the database, the authorization system, the financial engine, the taxonomy owner, or a SQL agent.",
    "",
    "Interpret the request into a canonical PHG request. Routing rules:",
    "- Building/creating/designing a WHOLE beverage menu, cocktail menu or drink list is menu_workflow. Never downgrade it to command_center.",
    "- Building ONE cocktail is cocktail_development.",
    "- 'Make me a margarita menu' is menu_workflow, not a single Margarita.",
    "- Follow-ups such as \"what's the progress\" preserve the active workflow from context.",
    "- Venue/restaurant geography research is market_venue_research, read_only, tool_context venue_research, display_mode map, with grounded city/state in display_context. Never guess missing geography.",
    "- Creating or editing menu content or design state is proposal_required.",
    "- Anything consequential (writes, closes, approvals, publication, price changes) is proposal_required or approval_required. NEVER read_only.",
    "",
    "Integrity rules:",
    "- Never invent business data, costs, sales, thresholds or entities.",
    "- normalized_text must preserve explicit ingredients, brands, sizes, prices, formats and requested outputs.",
    "- If a subjective threshold is used with no definition in context, set needs_clarification rather than inventing a cutoff.",
    "- If one consequential target is genuinely ambiguous, set needs_clarification and ask exactly ONE concise question.",
    `- Relative dates resolve against account-local date ${localDate(cat.account?.timezone)}.`,
    "",
    "Return your answer ONLY by calling the emit_interpretation tool. Do not write prose."
  ].join("\n");

  let parsed: any = null;
  let shadowStatus = "ok";
  let errorCode: string | null = null;
  const started = Date.now();

  if (!anthropicKey) {
    shadowStatus = "provider_error";
    errorCode = "reasoning_provider_not_configured";
  } else {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), PROVIDER_TIMEOUT_MS);
    try {
      const rr = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        signal: ac.signal,
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
        // Status class only. Upstream body is never surfaced or logged.
        shadowStatus = "provider_error";
        errorCode = `provider_http_${rr.status}`;
      } else {
        const raw = await rr.json();
        const block = Array.isArray(raw?.content)
          ? raw.content.find((c: any) => c?.type === "tool_use" && c?.name === "emit_interpretation")
          : null;
        if (block?.input) parsed = block.input;
        else { shadowStatus = "provider_error"; errorCode = "provider_returned_no_structured_output"; }
      }
    } catch (e: any) {
      const aborted = e?.name === "AbortError";
      shadowStatus = aborted ? "provider_timeout" : "provider_error";
      errorCode = aborted ? "provider_timeout" : "provider_unreachable";
    } finally {
      clearTimeout(timer);
    }
  }

  const claudeLatency = Date.now() - started;
  const errors = parsed ? validate(parsed) : [];
  if (parsed && errors.length) shadowStatus = "schema_invalid";

  // ---- Disagreement analysis (structural, not prose comparison) ----
  const pIntent = prod.intent_hint ?? null;
  const cIntent = parsed?.intent_hint ?? null;
  const pExec = prod.execution_class_hint ?? null;
  const cExec = parsed?.execution_class_hint ?? null;

  let intentD = null, continuityD = null, capabilityD = null, riskD = null,
      approvalD = null, clarificationD = null, presentationD = null,
      riskDir: string | null = null, severity: string | null = null;

  if (parsed) {
    intentD = pIntent !== null && cIntent !== null ? pIntent !== cIntent : null;
    capabilityD = (prod.tool_context ?? null) !== null ? prod.tool_context !== parsed.tool_context : null;
    riskD = pExec !== null && cExec !== null ? pExec !== cExec : null;

    const pApproval = pExec === null ? null : pExec !== "read_only";
    const cApproval = cExec === null ? null : cExec !== "read_only";
    approvalD = pApproval !== null && cApproval !== null ? pApproval !== cApproval : null;

    clarificationD = typeof prod.needs_clarification === "boolean"
      ? prod.needs_clarification !== parsed.needs_clarification : null;
    presentationD = (prod.display_mode ?? null) !== null
      ? prod.display_mode !== parsed.display_mode : null;

    // Task continuity: with an active workflow, did each side preserve it?
    const aw = activeWorkflow(active);
    if (aw && pIntent !== null && cIntent !== null) {
      continuityD = (pIntent === aw) !== (cIntent === aw);
    }

    const pr = riskRank(pExec), cr = riskRank(cExec);
    if (pr !== null && cr !== null) {
      riskDir = cr === pr ? "same" : (cr > pr ? "claude_stricter" : "claude_looser");
    }

    const anyD = [intentD, continuityD, capabilityD, riskD, approvalD, clarificationD, presentationD].some(x => x === true);
    // Risk and approval divergence is always high severity.
    severity = (riskD === true || approvalD === true) ? "high" : (anyD ? "low" : "none");
  }

  const row: any = {
    correlation_id: correlationId,
    shadow_function_version: SHADOW_FUNCTION_VERSION,
    account_id: accountId,
    user_id: user.id,
    command_session_id: b?.command_session_id || null,
    conversation_id: b?.conversation_id || null,
    production_interpretation_id: b?.production_interpretation_id || null,
    raw_text: rawText,
    active_context_summary: contextSummary(active),
    recent_conversation_len: recent.length,

    prod_interpreter_version: prod.interpreter_version || null,
    prod_model: prod.model || null,
    prod_normalized_text: prod.normalized_text || null,
    prod_intent_hint: pIntent,
    prod_execution_class_hint: pExec,
    prod_confidence: typeof prod.confidence === "number" ? prod.confidence : null,
    prod_needs_clarification: typeof prod.needs_clarification === "boolean" ? prod.needs_clarification : null,
    prod_clarification_question: prod.clarification_question || null,
    prod_tool_context: prod.tool_context || null,
    prod_tool_entities: prod.tool_entities || [],
    prod_display_mode: prod.display_mode || null,
    prod_display_context: prod.display_context || {},
    prod_context_patch: prod.context_patch || {},
    prod_degraded: typeof prod.degraded === "boolean" ? prod.degraded : null,
    prod_latency_ms: typeof prod.latency_ms === "number" ? prod.latency_ms : null,

    claude_model: MODEL,
    claude_prompt_version: PROMPT_VERSION,
    claude_normalized_text: parsed?.normalized_text ?? null,
    claude_intent_hint: cIntent,
    claude_execution_class_hint: cExec,
    claude_confidence: typeof parsed?.confidence === "number" ? parsed.confidence : null,
    claude_needs_clarification: typeof parsed?.needs_clarification === "boolean" ? parsed.needs_clarification : null,
    claude_clarification_question: parsed?.clarification_question ?? null,
    claude_tool_context: parsed?.tool_context ?? null,
    claude_tool_entities: parsed?.tool_entities ?? [],
    claude_display_mode: parsed?.display_mode ?? null,
    claude_display_context: parsed?.display_context ?? {},
    claude_context_patch: parsed?.context_patch ?? {},
    claude_interpretation: parsed ?? null,
    claude_latency_ms: claudeLatency,

    schema_valid: parsed ? errors.length === 0 : null,
    schema_errors: errors,
    shadow_status: shadowStatus,
    error_code: errorCode,

    intent_disagreement: intentD,
    task_continuity_disagreement: continuityD,
    capability_disagreement: capabilityD,
    risk_disagreement: riskD,
    approval_disagreement: approvalD,
    clarification_disagreement: clarificationD,
    presentation_disagreement: presentationD,
    risk_divergence_direction: riskDir,
    disagreement_severity: severity
  };

  // Idempotent: a retry of the same production request cannot create a duplicate.
  const { error: insErr } = await sb.schema("phg").from(ONLY_TABLE)
    .upsert(row, { onConflict: "correlation_id,shadow_function_version", ignoreDuplicates: true });

  if (insErr) {
    console.error(JSON.stringify({ evt: "shadow_write_failed", version: SHADOW_FUNCTION_VERSION, code: "insert_failed" }));
    return out({ status: "error", code: "shadow_write_failed", wrote_shadow_row: false }, 500);
  }

  console.log(JSON.stringify({
    evt: "shadow_run", version: SHADOW_FUNCTION_VERSION, model: MODEL,
    account_id: accountId, correlation_id: correlationId,
    shadow_status: shadowStatus, schema_valid: parsed ? errors.length === 0 : null,
    severity, risk_divergence: riskDir, claude_latency_ms: claudeLatency,
    authoritative: "phg-language-interpreter"
  }));

  return out({
    status: "recorded",
    shadow_status: shadowStatus,
    wrote_shadow_row: true,
    wrote_production_data: false,
    authoritative_interpreter: "phg-language-interpreter",
    claude_is_primary: false,
    correlation_id: correlationId,
    schema_valid: parsed ? errors.length === 0 : null,
    disagreement_severity: severity,
    risk_divergence_direction: riskDir,
    claude_latency_ms: claudeLatency
  });
});
