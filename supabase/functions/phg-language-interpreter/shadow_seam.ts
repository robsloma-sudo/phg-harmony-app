// PHG Milestone 2 -- shadow dispatch seam.
//
// This module is the ONLY addition to the authoritative interpreter's file set.
// It is deliberately incapable of affecting production behaviour:
//
//  1. It is called AFTER the authoritative interpretation is complete.
//  2. Its return value is ignored and it is never awaited on the response path.
//  3. Every failure mode is swallowed -- provider errors, timeouts, rate limits,
//     malformed output and shadow-write failures can never surface to the user,
//     never block the request, and never alter routing (in particular they can
//     never cause a fallback to an incorrect Administrative route).
//  4. It reads no production state and writes no production data itself.
//
// It never logs or forwards anything beyond the already-authenticated request's
// own Authorization header, which is passed straight through and never stored.

const SHADOW_SLUG = "phg-harmony-shadow-capture";

// Stable correlation id so a retry of the SAME production request cannot create
// uncontrolled duplicate shadow evaluations. Caller-supplied request_id wins.
async function correlationId(parts: {
  requestId?: string | null;
  accountId: string;
  userId: string;
  sessionId?: string | null;
  rawText: string;
}): Promise<string> {
  if (parts.requestId) return String(parts.requestId).slice(0, 200);
  const basis = [parts.accountId, parts.userId, parts.sessionId || "", parts.rawText].join("\u0000");
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(basis));
  return Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, "0")).join("");
}

export function dispatchShadow(req: Request, body: any, ctx: {
  interpreted: any;
  rawText: string;
  active: any;
  recent: any[];
  accountId: string | null | undefined;
  model: string;
  interpreterVersion: string;
  latencyMs: number;
  userId: string;
}): void {
  try {
    const url = Deno.env.get("SUPABASE_URL");
    const auth = req.headers.get("Authorization") || "";
    if (!url || !ctx.accountId || !auth) return;

    const task = (async () => {
      try {
        const correlation_id = await correlationId({
          requestId: body?.request_id || null,
          accountId: ctx.accountId as string,
          userId: ctx.userId,
          sessionId: body?.command_session_id || null,
          rawText: ctx.rawText
        });

        const i = ctx.interpreted || {};
        await fetch(`${url}/functions/v1/${SHADOW_SLUG}`, {
          method: "POST",
          headers: { Authorization: auth, "Content-Type": "application/json" },
          body: JSON.stringify({
            correlation_id,
            account_id: body?.account_id || null,
            menu_project_id: body?.menu_project_id || null,
            command_session_id: body?.command_session_id || null,
            conversation_id: body?.conversation_id || null,
            raw_text: ctx.rawText,
            active_context: ctx.active,
            recent_conversation: ctx.recent,
            production: {
              interpreter_version: ctx.interpreterVersion,
              model: ctx.model,
              normalized_text: i.normalized_text ?? null,
              intent_hint: i.intent_hint ?? null,
              execution_class_hint: i.execution_class_hint ?? null,
              confidence: typeof i.confidence === "number" ? i.confidence : null,
              needs_clarification: !!i.needs_clarification,
              clarification_question: i.clarification_question ?? null,
              tool_context: i.tool_context ?? null,
              tool_entities: i.tool_entities ?? [],
              display_mode: i.display_mode ?? null,
              display_context: i.display_context ?? {},
              context_patch: i.context_patch ?? {},
              degraded: !!i.degraded,
              latency_ms: ctx.latencyMs
            }
          })
        });
      } catch {
        // Shadow mode is best-effort by design. Never propagate.
      }
    })();

    // Complete the background task without holding the production response.
    const rt = (globalThis as any).EdgeRuntime;
    if (rt?.waitUntil) rt.waitUntil(task); else task.catch(() => {});
  } catch {
    // Never propagate.
  }
}
