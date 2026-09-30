// promote-menus — REVISION 4.3
//
// Feeds staged menu extractions into the canonical tables through the existing
// submit-menu intake endpoint. Contains NO write logic of its own beyond its
// own two marker columns: submit_menu() already handles menu creation,
// supersession, content-hash dedupe, brand matching and cocktail inference.
// A second write path is what emptied these tables the first time.
//
// FIXED IN REV 4 (rev 3 was not deployable)
//   F   1,000-row PostgREST truncation. Exact head count first, then paged
//       reads until the loaded count matches. On mismatch: post nothing, mark
//       nothing. A short read is a hard stop, not a degraded run.
//   F1  Deterministic order. Every query orders by id.
//   F2  Marking chunked at 150 ids and the update result CHECKED. Rev 3 put up
//       to 3,388 ids in one URL, ~24,000 characters.
//   F3  Marking by the exact ids loaded for that page, never by
//       menu_page_url: 55,954 rows of excluded history sit on pages this
//       feeder claims. The ids ARE the set posted, so claim and mark describe
//       the same rows by construction rather than by two filter lists agreeing.
//   D   source_code on every payload.
//   E   A rejection sets promotion_status and leaves promoted_at null: out of
//       the claim pool, still visibly unfinished.
//
// NEW IN 4.1  ?pages= for dry runs, so the paging path can be exercised on
//             purpose. A typical batch is ~240 rows and never reaches the cap.
// NEW IN 4.2  Live runs refuse to start if the provenance source row is
//             missing. Retrofitting provenance to 78,000 promoted rows is a
//             different job from attaching it at write time.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const PAGES_PER_RUN = 25;
const OVERALL_MS = 125_000;
const PAGE_SIZE = 1000;   // PostgREST hard cap. Do not raise.
const MARK_CHUNK = 150;   // ids per update, to stay inside URL length limits.

const SOURCE_CODE = "NBCC-FIRECRAWL-MENUS";

// staging item_type -> menu_items.item_type. menu_items has no 'beer' or
// 'wine' member: those are section-level facts carried by section_type and the
// verbatim heading. Mapping to 'other' loses nothing and avoids a violation.
const ITEM_TYPE: Record<string, string> = {
  cocktail: "cocktail",
  spirit_pour: "spirit_pour",
  beer: "other",
  wine: "other",
  other: "other",
};

// Heading -> section_type. Conservative on purpose: anything not matching
// confidently stays 'unsectioned', and the printed heading is preserved
// verbatim in section_name either way, so this is reversible.
function sectionType(heading: string | null): string {
  if (!heading) return "unsectioned";
  const h = heading.toLowerCase();
  if (/cocktail|martini|margarita|signature|craft|mixed|classic/.test(h)) return "cocktails";
  if (/wine|vino|red|white|ros|sparkling|champagne|bubbl/.test(h)) return "wine";
  if (/beer|draft|draught|tap|cider|lager|ale|seltzer/.test(h)) return "beer";
  if (/tequila|mezcal|whisk|bourbon|rye|vodka|gin|rum|scotch|spirit|agave|cognac/.test(h)) return "spirits";
  if (/food|kitchen|bite|snack|small plate|shareable|entr/.test(h)) return "food";
  return "unsectioned";
}

function json(b: unknown, s = 200) {
  return new Response(JSON.stringify(b), {
    status: s, headers: { "Content-Type": "application/json" },
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

type Row = {
  id: number;
  menu_page_url: string;
  menu_format: string;
  account_id: string;
  item_type: string;
  item_name: string;
  item_price: number | null;
  section_name: string | null;
  spirit_brands: string | null;
};

Deno.serve(async (req: Request) => {
  const secret = Deno.env.get("AGENT_SECRET") ?? "";
  if (!eq(req.headers.get("x-agent-secret"), secret)) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = Deno.env.get("SUPABASE_URL")!;
  const supabase = createClient(url, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
    auth: { persistSession: false },
  });

  const params = new URL(req.url).searchParams;
  const dryRun = params.get("dry_run") === "1";
  const started = Date.now();

  // DRY RUN ONLY: target specific pages, to exercise the pager deliberately.
  // Refused outside dry run - hand-picking pages is a diagnostic, not a mode of
  // operation, and it would let a caller bypass the claim order.
  const forcedPages = (params.get("pages") ?? "")
    .split(",").map((s) => s.trim()).filter(Boolean);
  if (forcedPages.length && !dryRun) {
    return json({ error: "pages_requires_dry_run" }, 400);
  }

  // 4.2 GUARD. Provenance must exist BEFORE anything is written. Attaching a
  // source at write time is cheap; retrofitting it to 78,000 promoted rows is
  // not. Dry runs are exempt - they write nothing and are how you check the
  // payloads before the row exists.
  if (!dryRun) {
    const { data: src, error: srcErr } = await supabase
      .from("sources").select("source_code").eq("source_code", SOURCE_CODE).maybeSingle();
    if (srcErr) return json({ error: "source_check_failed", detail: srcErr.message }, 500);
    if (!src) {
      return json({
        error: "provenance_source_missing",
        detail: `No row in sources for ${SOURCE_CODE}. Register it before the first live run - ` +
                `everything promoted would otherwise land with source_id null. Dry runs still work.`,
      }, 412);
    }
  }

  // Refresh the staging quality filter before claiming anything. Legacy/pre-v8 rows,
  // recovery rows, zero-item summaries and manual-review rows are preserved but excluded.
  const { error: qualityErr } = await supabase.rpc("refresh_menu_staging_quality");
  if (qualityErr) return json({ error: "quality_refresh_failed", detail: qualityErr.message }, 500);

  // Unclaimed = never promoted AND never rejected AND explicitly promotion-ready.
  // promotion_status carries rejection; quality_status is the data-quality gate.
  const unclaimed = (q: any) => q
    .is("superseded_at", null)
    .is("promoted_at", null)
    .is("promotion_status", null)
    .eq("quality_status", "promotion_ready")
    .not("account_id", "is", null);

  // Claim whole pages. This read is itself subject to the 1,000-row cap, which
  // is fine - we only need 25 distinct pages - but it must be ORDERED so the
  // same run twice sees the same pages (F1).
  let pageUrls: string[];
  if (forcedPages.length) {
    pageUrls = forcedPages.slice(0, PAGES_PER_RUN);
  } else {
    const { data: pageRows, error: pageErr } = await unclaimed(
      supabase.from("staging_menu_extract").select("menu_page_url"),
    ).order("id", { ascending: true }).limit(PAGE_SIZE);

    if (pageErr) return json({ error: "page_query_failed", detail: pageErr.message }, 500);

    pageUrls = [...new Set((pageRows ?? []).map((p: any) => p.menu_page_url))]
      .slice(0, PAGES_PER_RUN);
  }
  if (!pageUrls.length) return json({ status: "complete", message: "nothing left to promote" });

  // F: how many rows SHOULD we get? Ask before reading, so truncation is
  // detectable rather than invisible.
  const { count: expected, error: countErr } = await unclaimed(
    supabase.from("staging_menu_extract").select("id", { count: "exact", head: true }),
  ).in("menu_page_url", pageUrls);

  if (countErr) return json({ error: "count_query_failed", detail: countErr.message }, 500);

  // F + F1: page through in id order until we have them all.
  const rows: Row[] = [];
  for (let from = 0; from < (expected ?? 0); from += PAGE_SIZE) {
    const { data, error } = await unclaimed(
      supabase.from("staging_menu_extract").select(
        "id, menu_page_url, menu_format, account_id, item_type, item_name, item_price, section_name, spirit_brands",
      ),
    ).in("menu_page_url", pageUrls)
      .order("id", { ascending: true })
      .range(from, from + PAGE_SIZE - 1);

    if (error) return json({ error: "row_query_failed", detail: error.message }, 500);
    if (!data?.length) break;
    rows.push(...(data as Row[]));
  }

  // F: hard stop. A short read means some page would be posted incomplete, and
  // there is no way to tell which. Post nothing; mark nothing.
  if (rows.length !== (expected ?? 0)) {
    return json({
      error: "incomplete_read",
      detail: "row count does not match the pre-read count; nothing was posted",
      expected, received: rows.length,
    }, 500);
  }

  const byPage = new Map<string, Row[]>();
  for (const r of rows) {
    if (!byPage.has(r.menu_page_url)) byPage.set(r.menu_page_url, []);
    byPage.get(r.menu_page_url)!.push(r);
  }

  // F2: chunked, and the result is checked. Silent marking failures are how a
  // queue stops advancing while every run reports success.
  const mark = async (ids: number[], status: string, promoted: boolean) => {
    if (dryRun) return true;
    const patch = promoted
      ? { promoted_at: new Date().toISOString(), promotion_status: status }
      : { promotion_status: status };
    for (let i = 0; i < ids.length; i += MARK_CHUNK) {
      const { error } = await supabase.from("staging_menu_extract")
        .update(patch).in("id", ids.slice(i, i + MARK_CHUNK));
      if (error) return false;
    }
    return true;
  };

  const results: Record<string, unknown>[] = [];
  let created = 0, duplicate = 0, skipped = 0, failed = 0, markFailures = 0;

  for (const [pageUrl, pageRowsForPage] of byPage) {
    if (Date.now() - started > OVERALL_MS) break;

    const accountId = pageRowsForPage[0].account_id;
    const format = ["html", "pdf", "image"].includes(pageRowsForPage[0].menu_format)
      ? pageRowsForPage[0].menu_format : "other";

    const real = pageRowsForPage.filter((r) => r.item_type !== "summary");
    const ids = pageRowsForPage.map((r) => r.id); // F3: this page's rows only

    // A PDF or image we never opened cannot support "no drinks here".
    if (real.length === 0 && (format === "pdf" || format === "image")) {
      skipped++;
      results.push({ page: pageUrl, status: "skipped_unopened_menu", format, rows: ids.length });
      if (!await mark(ids, "skipped_unopened_menu", true)) markFailures++;
      continue;
    }

    // Null heading is its own bucket: the extractor returned no section, which
    // is not the same as the menu having none.
    const sections = new Map<string, Row[]>();
    for (const r of real) {
      const key = r.section_name ?? "\u0000none";
      if (!sections.has(key)) sections.set(key, []);
      sections.get(key)!.push(r);
    }

    const payload = {
      account_id: accountId,
      source_code: SOURCE_CODE,
      evidence_url: pageUrl,
      menu_format: format,
      extraction_confidence: "unknown", // never measured; not the same as low
      extraction_notes: "promoted from staging_menu_extract by promote-menus rev4",
      sections: [...sections.entries()].map(([heading, items], si) => ({
        section_name: heading === "\u0000none" ? null : heading,
        section_type: sectionType(heading === "\u0000none" ? null : heading),
        section_position: si + 1,
        items: items.map((it, ii) => ({
          item_name: it.item_name,
          item_position: ii + 1,
          item_type: ITEM_TYPE[it.item_type] ?? "unknown",
          price: it.item_price,
          brands: it.spirit_brands
            ? [{ raw_brand_text: it.spirit_brands, brand_named: true }]
            : [],
        })),
      })),
    };

    if (dryRun) {
      results.push({
        page: pageUrl, status: "dry_run", format,
        rows: ids.length, sections: payload.sections.length, items: real.length,
      });
      continue;
    }

    try {
      const r = await fetch(`${url}/functions/v1/submit-menu`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-agent-secret": secret },
        body: JSON.stringify(payload),
      });
      const out = await r.json().catch(() => null);

      if (!r.ok) {
        failed++;
        results.push({ page: pageUrl, status: "rejected", http: r.status, detail: out });
        if (!await mark(ids, `rejected_${r.status}`, false)) markFailures++;
        continue;
      }

      if (out?.status === "duplicate") duplicate++; else created++;
      results.push({
        page: pageUrl, status: out?.status, items: out?.items,
        menu_code: out?.menu_code,
        inferred: out?.inferred_from_cocktail_reference,
      });
      if (!await mark(ids, out?.status === "duplicate" ? "duplicate" : "promoted", true)) markFailures++;
    } catch (e) {
      failed++;
      results.push({ page: pageUrl, status: "error", detail: String(e).slice(0, 160) });
      if (!await mark(ids, "error", false)) markFailures++;
    }
  }

  const { count: remaining } = await unclaimed(
    supabase.from("staging_menu_extract").select("id", { count: "exact", head: true }),
  );

  return json({
    revision: "4.3",
    dry_run: dryRun,
    pages_attempted: byPage.size,
    rows_read: rows.length,
    created, duplicate, skipped, failed,
    mark_failures: markFailures,
    staging_rows_remaining: remaining,
    duration_ms: Date.now() - started,
    results,
  });
});
