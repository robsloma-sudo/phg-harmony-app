// submit-menu
// Intake for a single extracted venue menu: sections, items, brand references.
//
// MENUS ARE NEVER DELETED OR OVERWRITTEN. A new capture demotes the previous
// one to is_current = false and records what replaced it.
//
// ABSENCE-INFERENCE GUARD: an empty sections array is a positive claim that
// the menu was read and contained no drinks. That claim can only be made
// about a menu actually opened. PDF and image menus are recorded but not
// extracted, so posting one with no items is refused - otherwise the database
// would record "this venue serves no cocktails" when nobody looked.
//
// 2026-09-13 ITEM A: 'unknown' added to CONFIDENCE. The menus table CHECK was
// widened to permit it on 12 Sep and this validator was not updated, so every
// promotion call would have been refused here. unknown means NOT MEASURED. It
// does not mean low.
//
// 2026-09-13 ITEM B: p_needs_vision_pass added to the rpc call. Two submit_menu
// overloads exist; without this parameter PostgREST resolves to the 10-argument
// one, which has NO cocktail inference - every unbranded cocktail lands
// uncategorised. Passing this single argument selects the 15-argument overload.
// The other four extras are deliberately NOT passed: they carry NULL defaults,
// and an explicit null on p_needs_vision_pass would override its FALSE default
// and create a third state nothing downstream handles.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const FORMATS = new Set(["html", "pdf", "image", "other"]);
const CONFIDENCE = new Set(["high", "medium", "low", "unknown"]);
const SECTION_TYPES = new Set([
  "cocktails", "spirits", "wine", "beer", "food", "other", "unsectioned",
]);
const SPIRIT_CATEGORIES = new Set([
  "tequila", "mezcal", "agave_other", "vodka", "gin", "rum", "whiskey",
  "brandy", "liqueur", "wine", "beer", "non_alcoholic", "other", "unknown",
]);

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status, headers: { "Content-Type": "application/json" },
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

async function sha256Hex(s: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0")).join("");
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

  const accountId = body.account_id;
  const evidenceUrl = body.evidence_url;
  const format = String(body.menu_format ?? "").toLowerCase();
  const confidence = String(body.extraction_confidence ?? "").toLowerCase();
  const sections = body.sections;

  const errors: string[] = [];

  if (typeof accountId !== "string" || !accountId) errors.push("account_id is required");

  if (typeof evidenceUrl !== "string" || !/^https?:\/\//i.test(evidenceUrl)) {
    errors.push("evidence_url must be the venue's own URL");
  } else if (/firecrawl|webcache|googleusercontent|r\.jina\.ai|proxy/i.test(evidenceUrl)) {
    errors.push("evidence_url must be the publisher's URL, not a scraper or cache");
  }
  if (!FORMATS.has(format)) {
    errors.push(`menu_format must be one of: ${[...FORMATS].join(", ")}`);
  }
  if (!CONFIDENCE.has(confidence)) {
    errors.push(`extraction_confidence must be one of: ${[...CONFIDENCE].join(", ")}`);
  }
  if (!Array.isArray(sections)) {
    errors.push("sections must be an array");
  }

  if (errors.length) return json({ error: "validation_failed", errors }, 400);

  let itemCount = 0;
  for (const [si, s] of (sections as Record<string, unknown>[]).entries()) {
    const st = String(s?.section_type ?? "unsectioned");
    if (!SECTION_TYPES.has(st)) errors.push(`section[${si}].section_type invalid: ${st}`);
    const items = s?.items;
    if (items !== undefined && !Array.isArray(items)) {
      errors.push(`section[${si}].items must be an array`);
      continue;
    }
    for (const [ii, it] of ((items ?? []) as Record<string, unknown>[]).entries()) {
      itemCount++;
      const brands = it?.brands;
      if (brands !== undefined && !Array.isArray(brands)) {
        errors.push(`section[${si}].items[${ii}].brands must be an array`);
        continue;
      }
      for (const [bi, b] of ((brands ?? []) as Record<string, unknown>[]).entries()) {
        const cat = String(b?.spirit_category ?? "unknown");
        if (!SPIRIT_CATEGORIES.has(cat)) {
          errors.push(`section[${si}].items[${ii}].brands[${bi}].spirit_category invalid: ${cat}`);
        }
      }
    }
  }

  // THE ABSENCE GUARD. A PDF or image menu was recorded, not read. It cannot
  // support the claim "this menu contains no drinks".
  if (itemCount === 0 && (format === "pdf" || format === "image")) {
    return json({
      error: "absence_inference_refused",
      detail:
        `A ${format} menu with no items would record that this venue serves no drinks, ` +
        `but a ${format} menu is not opened in this pilot. Report the URL in your summary ` +
        `instead of posting it. Only post menus whose text you actually read.`,
    }, 400);
  }

  if (errors.length) {
    return json({ error: "validation_failed", errors: errors.slice(0, 50) }, 400);
  }

  const contentHash = typeof body.content_hash === "string" && body.content_hash
    ? body.content_hash
    : await sha256Hex(JSON.stringify({ accountId, evidenceUrl, sections }));

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { auth: { persistSession: false } },
  );

  const { data, error } = await supabase.rpc("submit_menu", {
    p_account_id: accountId,
    p_source_code: body.source_code ?? null,
    p_evidence_url: evidenceUrl,
    p_menu_title: body.menu_title ?? null,
    p_menu_format: format,
    p_extraction_confidence: confidence,
    p_extraction_notes: body.extraction_notes ?? null,
    p_published_date: body.published_date ?? null,
    p_content_hash: contentHash,
    p_sections: sections,
    // ITEM B: this one argument selects the 15-arg overload, which carries the
    // cocktail inference. Do not add the other four - their NULL defaults are
    // correct and an explicit null here would override the FALSE default.
    p_needs_vision_pass: false,
  });

  if (error) {
    console.error("submit_menu failed", error.message);
    return json({ error: "insert_failed", detail: error.message }, 500);
  }

  return json({ ...data, submitted_items: itemCount, content_hash: contentHash }, 200);
});
