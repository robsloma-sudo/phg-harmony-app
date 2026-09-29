import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

function json(data: unknown, status=200) {
  return new Response(JSON.stringify(data), { status, headers: { ...cors, "Content-Type": "application/json" } });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST required" }, 405);

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const openaiKey = Deno.env.get("OPENAI_API_KEY");
  const model = Deno.env.get("OPENAI_MODEL") || "gpt-4o-mini";
  if (!supabaseUrl || !serviceKey) return json({ error: "Supabase runtime configuration missing" }, 500);
  if (!openaiKey) return json({ error: "OPENAI_API_KEY is not configured for the orchestrator" }, 503);

  const body = await req.json().catch(() => ({}));
  const userRequest = String(body?.message || "").trim();
  if (!userRequest) return json({ error: "message is required" }, 400);

  const sb = createClient(supabaseUrl, serviceKey, { auth: { persistSession: false } });
  const { data: registry, error: registryError } = await sb.rpc("phg_orchestrator_context");
  let persistentContext:any=null;
  if(body?.conversation_id){
    const st=await sb.rpc("phg_conversation_state",{p_conversation_id:body.conversation_id});
    if(!st.error) persistentContext=st.data;
  }
  if (registryError) return json({ error: "Could not load PHG semantic registry", detail: registryError.message }, 500);

  const schema = {
    type: "object",
    additionalProperties: false,
    properties: {
      intent_summary: { type: "string" },
      needs_clarification: { type: "boolean" },
      clarification_question: { type: ["string","null"] },
      referenced_concepts: { type: "array", items: { type: "string" } },
      applicable_quality_rules: { type: "array", items: { type: "string" } },
      goals: {
        type: "array",
        items: {
          type: "object",
          additionalProperties: false,
          properties: {
            title: { type: "string" },
            goal_type: { type: "string" },
            priority: { type: "integer", minimum: 0, maximum: 100 },
            objective: { type: "object", additionalProperties: false, properties: { summary: { type: "string" } }, required: ["summary"] },
            constraints: { type: "object", additionalProperties: false, properties: { items: { type: "array", items: { type: "string" } } }, required: ["items"] },
            plans: {
              type: "array",
              items: {
                type: "object",
                additionalProperties: false,
                properties: {
                  method: { type: "object", additionalProperties: false, properties: { summary: { type: "string" } }, required: ["summary"] },
                  assumptions: { type: "array", items: { type: "string" } },
                  tasks: {
                    type: "array",
                    items: {
                      type: "object",
                      additionalProperties: false,
                      properties: {
                        task_type: { type: "string" },
                        input: { type: "object", additionalProperties: false, properties: { description: { type: "string" }, concepts: { type: "array", items: { type: "string" } }, constraints: { type: "array", items: { type: "string" } } }, required: ["description","concepts","constraints"] },
                        risk_level: { type: "string", enum: ["R0","R1","R2","R3"] },
                        confirmation_required: { type: "boolean" }
                      },
                      required: ["task_type","input","risk_level","confirmation_required"]
                    }
                  }
                },
                required: ["method","assumptions","tasks"]
              }
            }
          },
          required: ["title","goal_type","priority","objective","constraints","plans"]
        }
      }
    },
    required: ["intent_summary","needs_clarification","clarification_question","referenced_concepts","applicable_quality_rules","goals"]
  };

  const instructions = [
    "You are PHG Orchestrator v0.1. Convert a user's conversational request into traceable goals, candidate plans, and tasks.",
    "A conversation may contain multiple independent or related goals. Preserve concurrency when work can run independently.",
    "For one uncertain or important goal, multiple competing plans are allowed.",
    "Never invent missing business data. If a required entity, threshold, time range, or definition is genuinely ambiguous, set needs_clarification=true and ask one concise question.",
    "If the user uses an undefined subjective threshold such as expensive, cheap, high, low, strong, or weak and no explicit definition exists in context, require clarification rather than inventing a cutoff.",
    "If the semantic registry has no concept/source capable of answering a requested metric (for example an expense category when no expense concept exists), do not create executable retrieval tasks; set needs_clarification=true and explain the capability/data gap in the clarification question.",
    "For an unbounded request such as analyze this restaurant, clarify the analysis objective unless the conversation context clearly supplies one.",
    "If the user explicitly requests N different approaches to the same goal, create exactly one goal with at least N distinct competing plans under that goal, each with a materially different method. Do not turn approaches or methods into separate goals.",
    "Before planning retrieval, compare the requested business concept against the supplied semantic registry. If sales, labor, inventory, expenses, invoices, linen, vendor costs, or another requested domain is absent, treat it as a capability gap: needs_clarification=true, create no executable retrieval or analysis task for that missing domain, and never estimate or infer a value from unrelated concepts.",
    "Quality rules are scoped, not global. Include a quality rule only when the request, selected semantic concept, selected source, geography, time period, or planned data path can actually trigger that rule. Never attach Iowa rules to non-Iowa requests, and never attach menu-extraction rules to requests that do not use menu extraction data.",
    "Distinguish independent objectives from alternative methods. Coordinated verbs requesting distinct outputs (for example find similar programs, compare prices, and analyze demographics) are separate goals that may run concurrently. Different methods, approaches, scenarios, or models for one requested outcome are competing plans under one goal.",
    "Use persistent conversation state when supplied. Resolve phrases like that, it, those, back to, same one, or previous result only when the referent is clear from active goals/results/recent messages. Otherwise ask for clarification.",
    "R0=read/analyze, R1=temporary/draft, R2=persistent write, R3=consequential/destructive/external. R2/R3 should normally require confirmation.",
    "Use only semantic concepts present in the supplied registry. Apply relevant quality rules. A blocking quality rule must be represented in applicable_quality_rules and in task constraints rather than ignored.",
    "This version plans work; it does not claim that planned tasks have already executed.",
    "Keep task types descriptive and reusable, e.g. resolve_entity, retrieve_evidence, quality_check, analyze_evidence, reconcile_claims, generate_result."
  ].join("\n");

  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: { "Authorization": `Bearer ${openaiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      instructions,
      input: JSON.stringify({ user_request: userRequest, semantic_registry: registry, persistent_conversation_state: persistentContext, conversation_hint: body?.conversation_context || null }),
      text: { format: { type: "json_schema", name: "phg_orchestration_plan", strict: true, schema } }
    })
  });

  const raw = await response.json();
  if (!response.ok) return json({ error: "Model planning failed", detail: raw?.error?.message || raw }, 502);

  let outputText = raw.output_text;
  if (!outputText && Array.isArray(raw.output)) {
    for (const item of raw.output) {
      if (item?.type === "message" && Array.isArray(item.content)) {
        const part = item.content.find((x: any) => x?.type === "output_text");
        if (part?.text) { outputText = part.text; break; }
      }
    }
  }
  if (!outputText) return json({ error: "Planner returned no structured output" }, 502);

  let parsed;
  try { parsed = JSON.parse(outputText); } catch { return json({ error: "Planner output was not valid JSON" }, 502); }
  const reqLower=userRequest.toLowerCase();
  parsed.applicable_quality_rules=(parsed.applicable_quality_rules||[]).filter((rule:string)=>{
    if(rule.startsWith("iowa_")) return /\biowa\b/.test(reqLower);
    if(rule==="menu_collapsed_notes_v1_v5") return (parsed.referenced_concepts||[]).some((x:string)=>x==="menu_observation") || /extract(ed|ion)? menu|menu extract/i.test(userRequest);
    return true;
  });

  const { data: recorded, error: recordError } = await sb.rpc("phg_record_orchestration", {
    p_conversation_id: body?.conversation_id || null,
    p_external_key: body?.external_key || null,
    p_user_request: userRequest,
    p_parsed: parsed
  });
  if (recordError) return json({ error: "Plan created but could not be recorded", detail: recordError.message, plan: parsed }, 500);

  return json({ orchestrator_version: "0.1", model, ...recorded, plan: parsed });
});
