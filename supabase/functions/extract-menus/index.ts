
// extract-menus v9 — continuous menu pipeline with recovery lanes
// 2026-09-25
// - explicit queue/status model instead of "attempted = finished"
// - retries transient failures with backoff
// - reprocesses PDF/image/zero-item results
// - attempts public Facebook/Instagram pages, then sends failures to manual review
// - Firecrawl PDF parser uses auto/OCR fallback
// - every transition is recorded in menu_pipeline_events
// - bounded claiming prevents overlapping cron invocations from double-processing

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const MAP = "https://api.firecrawl.dev/v2/map";
const SCRAPE = "https://api.firecrawl.dev/v2/scrape";

const BATCH = 100;
const FETCH_CANDIDATES = 260;
const PER_CALL_MS = 50_000;
const OVERALL_MS = 125_000;
const MAX_ATTEMPTS = 3;

const ELIGIBLE = [
  "queued",
  "retry",
  "pdf_queue",
  "image_queue",
  "no_items_review",
  "attempted",
];

const DRINK = [
  "drink","drinks","cocktail","cocktails","bar-menu","barmenu",
  "beverage","beverages","wine","beer","spirits","happy-hour","taproom"
];
const MENU = ["menu","menus","dine","food"];

const PROMPT =
  "Extract every DRINK visible in this source - cocktails, spirits by the pour, beer and wine. " +
  "Capture the full drinks programme, not one category. For each item return the section heading " +
  "as printed, item name, numeric price when present, and any spirit brands named. " +
  "PDFs, scanned PDFs, image menus and image-heavy pages are valid menu sources: extract them when " +
  "the source exposes readable content. Never invent an item, price or brand. If no drink items can " +
  "actually be read, return an empty items array and report the source format accurately.";

const SCHEMA = {
  type: "object",
  properties: {
    menu_format: { type: "string", enum: ["html","pdf","image","social","none"] },
    items: {
      type: "array",
      items: {
        type: "object",
        properties: {
          section_name: { type: "string" },
          item_type: { type: "string", enum: ["cocktail","spirit_pour","beer","wine","other"] },
          item_name: { type: "string" },
          item_price: { type: ["number","null"] },
          spirit_brands: { type: "string" },
        },
        required: ["item_type","item_name"],
      },
    },
  },
  required: ["menu_format","items"],
};

function json(b: unknown, s = 200) {
  return new Response(JSON.stringify(b), {
    status: s,
    headers: { "Content-Type": "application/json" },
  });
}

function eq(g: string | null, e: string): boolean {
  if (!g || !e) return false;
  const a = new TextEncoder().encode(g.trim());
  const b = new TextEncoder().encode(e.trim());
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a[i] ^ b[i];
  return d === 0;
}

function verbatim(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const t = v.trim();
  return t.length ? t.slice(0, 300) : null;
}

function sourceKind(url: string): "facebook" | "instagram" | "website" {
  const l = url.toLowerCase();
  if (l.includes("facebook.com")) return "facebook";
  if (l.includes("instagram.com")) return "instagram";
  return "website";
}

function stateOf(id: string): string | null {
  if (id.startsWith("ACC-IA-")) return "IA";
  if (id.startsWith("ACC-CO-")) return "CO";
  if (id.startsWith("ACC-NY-")) return "NY";
  return null;
}

function pickMenu(links: string[]): string | null {
  const score = (u: string) => {
    const l = u.toLowerCase();
    let s = 0;
    DRINK.forEach((h, i) => { if (l.includes(h)) s += 120 - i; });
    MENU.forEach((h) => { if (l.includes(h)) s += 25; });
    if (l.includes(".pdf")) s += 30;
    if (l.split("/").length > 8) s -= 10;
    return s;
  };
  const r = links
    .filter((u) => typeof u === "string" && u.startsWith("http"))
    .map((u) => ({ u, s: score(u) }))
    .filter((x) => x.s > 0)
    .sort((a, b) => b.s - a.s);
  return r.length ? r[0].u : null;
}

function absoluteLinksFromHtml(html: string, base: string): string[] {
  const out = new Set<string>();
  const re = /href\s*=\s*["']([^"'#]+)["']/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(html)) !== null) {
    try {
      const u = new URL(m[1], base);
      if (u.protocol === "http:" || u.protocol === "https:") out.add(u.href);
    } catch {}
    if (out.size >= 300) break;
  }
  return [...out];
}

async function freeHomepageMenuLink(site: string): Promise<string | null> {
  try {
    const r = await withTimeout(fetch(site, {
      redirect: "follow",
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; PHGMenuIndexer/1.0)",
        "Accept": "text/html,application/xhtml+xml"
      }
    }), 8000);
    if (!r?.ok) return null;
    const ct = (r.headers.get("content-type") || "").toLowerCase();
    if (!ct.includes("html")) return null;
    const html = (await r.text()).slice(0, 2_000_000);
    return pickMenu(absoluteLinksFromHtml(html, r.url || site));
  } catch {
    return null;
  }
}

async function withTimeout(p: Promise<Response>, ms: number): Promise<Response | null> {
  const t = new Promise<null>((res) => setTimeout(() => res(null), ms));
  return await Promise.race([p.catch(() => null), t]);
}

function backoffMinutes(attemptNo: number) {
  return Math.min(240, 15 * Math.pow(2, Math.max(0, attemptNo - 1)));
}

Deno.serve(async (req: Request) => {
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { auth: { persistSession: false } },
  );

  const { data: tok } = await supabase
    .from("internal_secrets")
    .select("value")
    .eq("key", "ingest_token")
    .single();

  const ok =
    eq(req.headers.get("x-agent-secret"), Deno.env.get("AGENT_SECRET") ?? "") ||
    eq(req.headers.get("x-ingest-token"), tok?.value ?? "");
  if (!ok) return json({ error: "unauthorized" }, 401);

  const key = Deno.env.get("FIRECRAWL_API_KEY");
  if (!key) return json({ error: "firecrawl_key_not_configured" }, 500);
  const auth = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${key.trim()}`,
  };

  const nowIso = new Date().toISOString();

  const { data: candidates, error } = await supabase
    .from("accounts")
    .select("account_id, account_name, website_url, menu_status, menu_attempt_count, menu_priority, menu_next_retry_at, menu_attempt_note")
    .not("website_url", "is", null)
    .in("menu_status", ELIGIBLE)
    .or(`menu_next_retry_at.is.null,menu_next_retry_at.lte.${nowIso}`)
    .order("menu_next_retry_at", { ascending: true, nullsFirst: true })
    .order("menu_priority", { ascending: true, nullsFirst: false })
    .order("account_name", { ascending: true })
    .limit(FETCH_CANDIDATES);

  if (error) return json({ error: "query_failed", detail: error.message }, 500);
  if (!candidates?.length) return json({ status: "complete", message: "eligible queue empty" });

  const claimed: any[] = [];

  for (const a of candidates) {
    if (claimed.length >= BATCH) break;
    const previous = a.menu_status as string;

    const { data: lock } = await supabase
      .from("accounts")
      .update({ menu_status: "processing" })
      .eq("account_id", a.account_id)
      .eq("menu_status", previous)
      .select("account_id")
      .maybeSingle();

    if (lock?.account_id) claimed.push({ ...a, previous_status: previous });
  }

  if (!claimed.length) return json({ status: "busy", message: "candidates already claimed" });

  const started = Date.now();
  const totals: Record<string, number> = {
    extracted: 0,
    retry: 0,
    manual_review: 0,
    pdf_queue: 0,
    image_queue: 0,
    no_items_review: 0,
    rate_limited: 0,
    error: 0,
    direct_link_discovery: 0,
    map_fallback: 0,
  };

  async function event(a: any, toStatus: string, detail: string, extras: Record<string, unknown> = {}) {
    await supabase.from("menu_pipeline_events").insert({
      account_id: a.account_id,
      state_code: stateOf(a.account_id),
      event_type: "menu_pipeline_transition",
      from_status: a.previous_status,
      to_status: toStatus,
      attempt_no: extras.attempt_no ?? a.menu_attempt_count ?? 0,
      menu_url: extras.menu_url ?? a.website_url,
      http_status: extras.http_status ?? null,
      item_count: extras.item_count ?? null,
      detail: detail.slice(0, 500),
    });
  }

  async function setStatus(
    a: any,
    toStatus: string,
    note: string,
    attemptNo: number,
    nextRetry: string | null,
    finalized = false,
    extras: Record<string, unknown> = {},
  ) {
    await supabase.from("accounts").update({
      menu_status: toStatus,
      menu_attempt_count: attemptNo,
      menu_last_attempt_at: new Date().toISOString(),
      menu_attempted_at: new Date().toISOString(),
      menu_attempt_note: note.slice(0, 200),
      menu_next_retry_at: nextRetry,
      menu_source_kind: sourceKind(a.website_url),
      menu_finalized_at: finalized ? new Date().toISOString() : null,
    }).eq("account_id", a.account_id);

    await event(a, toStatus, note, { ...extras, attempt_no: attemptNo });
    totals[toStatus] = (totals[toStatus] ?? 0) + 1;
  }

  async function releaseRateLimit(a: any, detail: string, menuUrl?: string) {
    const next = new Date(Date.now() + 15 * 60_000).toISOString();
    await supabase.from("accounts").update({
      menu_status: "retry",
      menu_next_retry_at: next,
      menu_source_kind: sourceKind(a.website_url),
    }).eq("account_id", a.account_id);
    await event(a, "retry", detail, { menu_url: menuUrl ?? a.website_url, attempt_no: a.menu_attempt_count ?? 0, http_status: 429 });
    totals.rate_limited++;
  }

  async function work(a: any) {
    const attemptNo = Number(a.menu_attempt_count ?? 0) + 1;
    const kind = sourceKind(a.website_url);
    let target = a.website_url as string;

    try {
      // Reuse a previously discovered menu URL whenever we already had one.
      // This is especially important for HTTP 402 retries: the provider failed
      // after discovery, so remapping the homepage would waste time and credits.
      if (a.previous_status === "pdf_queue" || a.previous_status === "image_queue") {
        const { data: prior } = await supabase
          .from("staging_menu_extract")
          .select("menu_page_url, menu_format")
          .eq("account_id", a.account_id)
          .is("superseded_at", null)
          .order("loaded_at", { ascending: false })
          .limit(1)
          .maybeSingle();
        if (prior?.menu_page_url) target = prior.menu_page_url;
      } else if (a.previous_status === "retry" && String(a.menu_attempt_note ?? "").includes("402")) {
        const { data: prior402 } = await supabase
          .from("menu_pipeline_events")
          .select("menu_url")
          .eq("account_id", a.account_id)
          .eq("http_status", 402)
          .order("created_at", { ascending: false })
          .limit(1)
          .maybeSingle();
        if (prior402?.menu_url) target = prior402.menu_url;
      } else if (kind === "website") {
        // Cheapest path first: fetch the public homepage directly and inspect
        // its links locally. Firecrawl Map is only used when that produces no
        // plausible menu/drinks URL.
        const freeTarget = await freeHomepageMenuLink(a.website_url);
        if (freeTarget) {
          target = freeTarget;
          totals.direct_link_discovery++;
        } else {
          totals.map_fallback++;
          const m = await withTimeout(fetch(MAP, {
            method: "POST",
            headers: auth,
            body: JSON.stringify({
              url: a.website_url,
              search: "drinks beverages cocktails bar wine beer spirits menu pdf",
              limit: 60,
            }),
          }), PER_CALL_MS);

          if (m?.status === 429) {
            await releaseRateLimit(a, "Firecrawl map rate limited");
            return;
          }

          if (m?.status === 402) {
            const next = new Date(Date.now() + 60 * 60_000).toISOString();
            await setStatus(a, "retry", "Firecrawl provider payment/credit block (HTTP 402)", Math.max(Number(a.menu_attempt_count ?? 0), attemptNo - 1), next, false, { menu_url: a.website_url, http_status: 402 });
            return;
          }

          if (m?.ok) {
            const mj = await m.json().catch(() => null);
            const links: string[] = (mj?.links ?? mj?.data?.links ?? [])
              .map((x: unknown) => typeof x === "string" ? x : (x as { url?: string })?.url)
              .filter(Boolean);
            target = pickMenu(links) ?? target;
          }
        }
      }

      const body: Record<string, unknown> = {
        url: target,
        formats: [{ type: "json", prompt: PROMPT, schema: SCHEMA }],
        onlyMainContent: kind === "website",
      };

      if (/\.pdf($|\?)/i.test(target) || a.previous_status === "pdf_queue") {
        body.parsePDF = "auto";
        body.maxPages = 20;
      }

      const r = await withTimeout(fetch(SCRAPE, {
        method: "POST",
        headers: auth,
        body: JSON.stringify(body),
      }), PER_CALL_MS);

      if (!r) {
        if (attemptNo >= MAX_ATTEMPTS) {
          await setStatus(a, "manual_review", "scrape timed out after retry limit", attemptNo, null, true, { menu_url: target });
        } else {
          const next = new Date(Date.now() + backoffMinutes(attemptNo) * 60_000).toISOString();
          await setStatus(a, "retry", "scrape timed out", attemptNo, next, false, { menu_url: target });
        }
        return;
      }

      if (r.status === 402) {
        const next = new Date(Date.now() + 60 * 60_000).toISOString();
        await setStatus(
          a,
          "retry",
          "Firecrawl provider payment/credit block (HTTP 402)",
          Math.max(Number(a.menu_attempt_count ?? 0), attemptNo - 1),
          next,
          false,
          { menu_url: target, http_status: 402 }
        );
        return;
      }

      if (r.status === 429) {
        await releaseRateLimit(a, "Firecrawl scrape rate limited", target);
        return;
      }

      if (!r.ok) {
        const retryable = r.status >= 500;
        if (retryable && attemptNo < MAX_ATTEMPTS) {
          const next = new Date(Date.now() + backoffMinutes(attemptNo) * 60_000).toISOString();
          await setStatus(a, "retry", `scrape http ${r.status}`, attemptNo, next, false, { menu_url: target, http_status: r.status });
        } else {
          await setStatus(a, "manual_review", `scrape http ${r.status}`, attemptNo, null, true, { menu_url: target, http_status: r.status });
        }
        return;
      }

      const pj = await r.json().catch(() => null);
      const j = pj?.data?.json ?? pj?.json ?? null;
      const items = Array.isArray(j?.items) ? j.items : [];
      let fmt = j?.menu_format ?? (/\.pdf($|\?)/i.test(target) ? "pdf" : "html");
      if (kind !== "website" && fmt === "none") fmt = "social";

      const rows = items.length
        ? items.map((it: Record<string, unknown>) => {
            const section = verbatim(it.section_name);
            const brands = verbatim(it.spirit_brands);
            return {
              site_url: a.website_url,
              menu_page_url: target,
              menu_format: fmt,
              account_id: a.account_id,
              item_type: String(it.item_type ?? "other").toLowerCase(),
              item_name: String(it.item_name ?? "").slice(0, 300),
              item_price: typeof it.item_price === "number" ? it.item_price : null,
              section_name: section,
              spirit_brands: brands,
              notes: [section, brands].filter(Boolean).join(" | ").slice(0, 300),
            };
          })
        : [{
            site_url: a.website_url,
            menu_page_url: target,
            menu_format: fmt,
            account_id: a.account_id,
            item_type: "summary",
            item_name: "",
            item_price: null,
            section_name: null,
            spirit_brands: null,
            notes: "menu reached, no drink items found",
          }];

      await supabase.from("staging_menu_extract")
        .update({ superseded_at: new Date().toISOString() })
        .eq("menu_page_url", target)
        .is("superseded_at", null);

      await supabase.from("staging_menu_extract").insert(rows);

      if (items.length > 0) {
        await setStatus(a, "extracted", `${fmt}: ${items.length} items`, attemptNo, null, true, {
          menu_url: target,
          item_count: items.length,
        });
        return;
      }

      // Recovery lanes: one deliberate recovery attempt, then manual review.
      if (kind !== "website") {
        await setStatus(a, "manual_review", `${fmt}: 0 items from social source`, attemptNo, null, true, { menu_url: target, item_count: 0 });
        return;
      }

      if (fmt === "pdf") {
        if (a.previous_status === "pdf_queue" || attemptNo >= 2) {
          await setStatus(a, "manual_review", "pdf: 0 items after recovery", attemptNo, null, true, { menu_url: target, item_count: 0 });
        } else {
          const next = new Date(Date.now() + 30 * 60_000).toISOString();
          await setStatus(a, "pdf_queue", "pdf: 0 items; queued for parser recovery", attemptNo, next, false, { menu_url: target, item_count: 0 });
        }
        return;
      }

      if (fmt === "image") {
        if (a.previous_status === "image_queue" || attemptNo >= 2) {
          await setStatus(a, "manual_review", "image: 0 items after recovery", attemptNo, null, true, { menu_url: target, item_count: 0 });
        } else {
          const next = new Date(Date.now() + 60 * 60_000).toISOString();
          await setStatus(a, "image_queue", "image: 0 items; queued for recovery", attemptNo, next, false, { menu_url: target, item_count: 0 });
        }
        return;
      }

      if (a.previous_status === "no_items_review" || a.previous_status === "attempted" || attemptNo >= 2) {
        await setStatus(a, "manual_review", `${fmt}: 0 items after deeper retry`, attemptNo, null, true, { menu_url: target, item_count: 0 });
      } else {
        const next = new Date(Date.now() + 2 * 60 * 60_000).toISOString();
        await setStatus(a, "no_items_review", `${fmt}: 0 items; queued for deeper retry`, attemptNo, next, false, { menu_url: target, item_count: 0 });
      }
    } catch (e) {
      totals.error++;
      if (attemptNo >= MAX_ATTEMPTS) {
        await setStatus(a, "manual_review", "pipeline error after retry limit: " + String(e).slice(0, 120), attemptNo, null, true);
      } else {
        const next = new Date(Date.now() + backoffMinutes(attemptNo) * 60_000).toISOString();
        await setStatus(a, "retry", "pipeline error: " + String(e).slice(0, 120), attemptNo, next);
      }
    }
  }

  const guard = new Promise<null>((res) => setTimeout(() => res(null), OVERALL_MS));
  const detail = await Promise.race([Promise.all(claimed.map(work)), guard]);

  // Any rows still stuck in processing because the overall guard fired are
  // released back to retry without incrementing their attempt counter.
  if (detail === null) {
    for (const a of claimed) {
      const { data: cur } = await supabase.from("accounts")
        .select("menu_status")
        .eq("account_id", a.account_id)
        .maybeSingle();
      if (cur?.menu_status === "processing") {
        await supabase.from("accounts").update({
          menu_status: "retry",
          menu_next_retry_at: new Date(Date.now() + 15 * 60_000).toISOString(),
        }).eq("account_id", a.account_id);
      }
    }
  }

  await supabase.rpc("refresh_state_stats");

  const { count: remaining } = await supabase
    .from("accounts")
    .select("account_id", { count: "exact", head: true })
    .not("website_url", "is", null)
    .in("menu_status", ELIGIBLE);

  return json({
    batch: BATCH,
    claimed: claimed.length,
    remaining,
    duration_ms: Date.now() - started,
    totals,
    detail: detail ?? "overall budget reached; unfinished claims released to retry",
  });
});
