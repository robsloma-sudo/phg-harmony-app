// enrich-places
// Google Places lookup: name + address in, website / phone / rating / venue
// type / coordinates out. A lookup, not a generation.
//
// TWO THINGS WERE WASTING THE RUN:
//
//   1. The batch was split evenly across three states, but Iowa and Colorado
//      are finished. Two thirds of every pass fetched nothing. Slack now goes
//      to whichever states actually have work.
//
//   2. Calls ran one after another - 20 venues in 8 seconds inside a 150
//      second window, most of it spent waiting on Google rather than working.
//      They now run in parallel with a bounded pool.
//
// Net effect: roughly 20 venues per pass to roughly 150.
//
// A venue with no match is RECORDED as no_match, never guessed at.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const PLACES_URL = "https://places.googleapis.com/v1/places:searchText";
const FIELDS = [
  "places.id", "places.displayName", "places.formattedAddress",
  "places.websiteUri", "places.nationalPhoneNumber", "places.rating",
  "places.userRatingCount", "places.types", "places.businessStatus",
  "places.location",
].join(",");

const BATCH = 180;            // fetched per pass
const CONCURRENCY = 12;       // simultaneous Google calls
const TIME_BUDGET_MS = 115_000;
const STATE_NAME: Record<string, string> = { IA: "Iowa", CO: "Colorado", NY: "New York" };

function json(b: unknown, s = 200) {
  return new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json" } });
}

function eq(g: string | null, e: string): boolean {
  if (!g || !e) return false;
  const a = new TextEncoder().encode(g.trim()), b = new TextEncoder().encode(e.trim());
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a[i] ^ b[i];
  return d === 0;
}

// A wrong venue is far worse than a missing one: nothing downstream reveals
// the error. Street number is the strongest single confirmation available.
function addressAgrees(asked: string, got: string): boolean {
  const num = (s: string) => (s.match(/\b(\d{1,6})\b/) || [])[1];
  const a = num(asked), g = num(got);
  if (a && g) return a === g;
  return true;
}

function stateOf(id: string): string | null {
  if (id.startsWith("ACC-IA-")) return "IA";
  if (id.startsWith("ACC-CO-")) return "CO";
  if (id.startsWith("ACC-NY-")) return "NY";
  return null;
}

Deno.serve(async (req: Request) => {
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { auth: { persistSession: false } },
  );

  const { data: tok } = await supabase
    .from("internal_secrets").select("value").eq("key", "ingest_token").single();
  const ok = eq(req.headers.get("x-agent-secret"), Deno.env.get("AGENT_SECRET") ?? "") ||
             eq(req.headers.get("x-ingest-token"), tok?.value ?? "");
  if (!ok) return json({ error: "unauthorized" }, 401);

  const placesKey = Deno.env.get("GOOGLE_PLACES_API_KEY");
  if (!placesKey) return json({ error: "places_key_not_configured" }, 500);

  // Lowest phase with work left.
  const { data: phaseRow } = await supabase
    .from("accounts").select("enrich_phase")
    .is("places_looked_up_at", null)
    .eq("account_status", "active")
    .contains("account_types", ["on_premise_spirits"])
    .not("enrich_phase", "is", null).gt("enrich_phase", 0)
    .order("enrich_phase", { ascending: true }).limit(1);

  if (!phaseRow?.length) return json({ status: "complete" });
  const phase = phaseRow[0].enrich_phase as number;

  // One query, no per-state split. A finished state simply contributes no
  // rows instead of reserving a share it cannot use.
  const { data: accounts, error } = await supabase
    .from("accounts")
    .select("account_id, account_name, street_address, notes")
    .is("places_looked_up_at", null)
    .eq("account_status", "active")
    .eq("enrich_phase", phase)
    .contains("account_types", ["on_premise_spirits"])
    .limit(BATCH);

  if (error) return json({ error: "query_failed", detail: error.message }, 500);
  if (!accounts?.length) return json({ status: "phase_empty", phase });

  const started = Date.now();
  const res = { matched: 0, no_match: 0, ambiguous: 0, error: 0 };
  const byState: Record<string, number> = {};
  let cursor = 0;

  async function one(a: Record<string, unknown>) {
    const id = a.account_id as string;
    const st = stateOf(id);
    if (!st) return;
    byState[st] = (byState[st] ?? 0) + 1;

    const city = ((a.notes as string)?.match(/City: ([^.]+)/) || [])[1] ?? "";
    const textQuery = [a.account_name, a.street_address, city, STATE_NAME[st]]
      .filter(Boolean).join(", ");

    try {
      const r = await fetch(PLACES_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Goog-Api-Key": placesKey!.trim(),
          "X-Goog-FieldMask": FIELDS,
        },
        body: JSON.stringify({ textQuery, maxResultCount: 3, regionCode: "US" }),
      });

      if (!r.ok) {
        res.error++;
        await supabase.rpc("apply_places_result", { p_account_id: id, p_status: "error" });
        return;
      }

      const places = (await r.json())?.places ?? [];
      if (!places.length) {
        res.no_match++;
        await supabase.rpc("apply_places_result", { p_account_id: id, p_status: "no_match" });
        return;
      }

      const top = places[0];
      if (!addressAgrees((a.street_address as string) ?? "", top.formattedAddress ?? "")) {
        res.ambiguous++;
        await supabase.rpc("apply_places_result", { p_account_id: id, p_status: "ambiguous" });
        return;
      }

      await supabase.rpc("apply_places_result", {
        p_account_id: id, p_status: "matched",
        p_website: top.websiteUri ?? null,
        p_phone: top.nationalPhoneNumber ?? null,
        p_place_id: top.id ?? null,
        p_rating: top.rating ?? null,
        p_reviews: top.userRatingCount ?? null,
        p_types: top.types ?? null,
        p_business_status: top.businessStatus ?? null,
        p_lat: top.location?.latitude ?? null,
        p_lng: top.location?.longitude ?? null,
      });
      res.matched++;
    } catch (_e) {
      res.error++;
    }
  }

  // Bounded pool: CONCURRENCY workers pulling from a shared cursor. Stops
  // cleanly on the time budget rather than being killed mid-write.
  async function worker() {
    while (true) {
      if (Date.now() - started > TIME_BUDGET_MS) return;
      const i = cursor++;
      if (i >= accounts.length) return;
      await one(accounts[i] as Record<string, unknown>);
    }
  }
  await Promise.all(Array.from({ length: CONCURRENCY }, worker));

  const { count: phaseLeft } = await supabase.from("accounts")
    .select("account_id", { count: "exact", head: true })
    .is("places_looked_up_at", null)
    .eq("account_status", "active")
    .eq("enrich_phase", phase)
    .contains("account_types", ["on_premise_spirits"]);

  return json({
    phase, fetched: accounts.length, processed: cursor, by_state: byState, ...res,
    phase_remaining: phaseLeft, duration_ms: Date.now() - started,
  });
});
