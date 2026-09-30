import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const FIRECRAWL_URL = "https://api.firecrawl.dev/v2/scrape";
const DEFAULT_MAX_CHARS = 100_000;
const HARD_MAX_CHARS = 400_000;
const TIMEOUT_MS = 90_000;

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// Both sides are trimmed. HTTP trims header values in transit but an
// environment variable keeps whatever was pasted into the dashboard, so a
// stray newline or trailing space would otherwise cause a permanent,
// silent 401 that looks identical to a wrong secret.
function secretMatches(given: string | null, expected: string): boolean {
  if (!given) return false;
  const a = new TextEncoder().encode(given.trim());
  const b = new TextEncoder().encode(expected.trim());
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405);

  const agentSecret = Deno.env.get("AGENT_SECRET");
  if (!agentSecret) return json({ error: "unauthorized" }, 401);
  if (!secretMatches(req.headers.get("x-agent-secret"), agentSecret)) {
    return json({ error: "unauthorized" }, 401);
  }

  const firecrawlKey = Deno.env.get("FIRECRAWL_API_KEY");
  if (!firecrawlKey) {
    return json({ error: "scraper_not_configured", retryable: false }, 500);
  }

  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { return json({ error: "invalid_json" }, 400); }

  const sourceId = body.source_id;
  const url = body.url;
  const onlyMainContent = body.only_main_content !== false;
  const maxChars = Math.min(Number(body.max_chars) || DEFAULT_MAX_CHARS, HARD_MAX_CHARS);

  if (typeof sourceId !== "string" || !sourceId) return json({ error: "source_id is required" }, 400);
  if (typeof url !== "string" || !url) return json({ error: "url is required" }, 400);

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { auth: { persistSession: false } },
  );

  const { data: check, error: checkError } = await supabase.rpc("check_scrape_target", {
    p_source_id: sourceId, p_url: url,
  });
  if (checkError) return json({ error: "guard_check_failed", detail: checkError.message }, 500);
  if (!check?.allowed) {
    console.warn("scrape refused", JSON.stringify({ sourceId, url, check }));
    return json({ error: "target_not_approved", detail: check }, 403);
  }

  const started = Date.now();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let fc: Response;
  try {
    fc = await fetch(FIRECRAWL_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${firecrawlKey.trim()}` },
      body: JSON.stringify({ url, formats: ["markdown"], onlyMainContent }),
      signal: controller.signal,
    });
  } catch (e) {
    clearTimeout(timer);
    const aborted = (e as Error).name === "AbortError";
    return json({ error: aborted ? "scrape_timeout" : "scrape_request_failed", detail: String(e), retryable: true }, 504);
  }
  clearTimeout(timer);

  if (!fc.ok) {
    const text = await fc.text().catch(() => "");
    const retryable = fc.status === 429 || fc.status >= 500;
    return json({ error: "scraper_error", status: fc.status, detail: text.slice(0, 500), retryable }, 502);
  }

  const payload = await fc.json().catch(() => null);
  const markdown: string = payload?.data?.markdown ?? "";
  const meta = payload?.data?.metadata ?? {};

  if (!markdown) {
    return json({ error: "empty_content", source_code: check.source_code, retryable: true }, 502);
  }

  await supabase.rpc("mark_source_checked", { p_source_id: sourceId });
  const truncated = markdown.length > maxChars;

  return json({
    source_id: sourceId,
    source_code: check.source_code,
    authority_tier: check.authority_tier,
    evidence_class: check.evidence_class,
    evidence_url: meta?.sourceURL ?? url,
    fetched_at: new Date().toISOString(),
    http_status: meta?.statusCode ?? null,
    page_title: meta?.title ?? null,
    content_chars: markdown.length,
    truncated,
    duration_ms: Date.now() - started,
    markdown: truncated ? markdown.slice(0, maxChars) : markdown,
  }, 200);
});
