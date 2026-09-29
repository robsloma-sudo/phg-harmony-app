
// Scheduled bridge for canonical menu promotion.
// Authenticates scheduled calls with the existing ingest token, then forwards
// to promote-menus using the project-wide AGENT_SECRET without exposing it.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function eq(given: string | null, expected: string): boolean {
  if (!given || !expected) return false;
  const a = new TextEncoder().encode(given.trim());
  const b = new TextEncoder().encode(expected.trim());
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a[i] ^ b[i];
  return d === 0;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405);

  const url = Deno.env.get("SUPABASE_URL")!;
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const agentSecret = Deno.env.get("AGENT_SECRET") ?? "";
  if (!url || !service || !agentSecret) {
    return json({ error: "runtime_configuration_missing" }, 500);
  }

  const sb = createClient(url, service, { auth: { persistSession: false } });
  const { data: tok } = await sb
    .from("internal_secrets").select("value").eq("key", "ingest_token").single();

  if (!eq(req.headers.get("x-ingest-token"), tok?.value ?? "")) {
    return json({ error: "unauthorized" }, 401);
  }

  const r = await fetch(url + "/functions/v1/promote-menus", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-agent-secret": agentSecret,
    },
    body: "{}",
  });

  const body = await r.text();
  return new Response(body, {
    status: r.status,
    headers: { "Content-Type": r.headers.get("Content-Type") ?? "application/json" },
  });
});
