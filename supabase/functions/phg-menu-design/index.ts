// phg-menu-design v1 (2026-09-28, PHG-036): the app's side of the Menu Designer hand-off.
// Actions (all need a signed-in user AND the Menu Studio project token, checked with phg_menu_authorize):
//   request_design  {menu_project_id, sync_token, request, source: user_prompt_flow|admin_button, source_detail?, inputs?}
//   design_status   {menu_project_id, sync_token}                       -> tasks + proposals (no documents)
//   take_approved   {menu_project_id, sync_token, proposal_id}          -> the approved document, for the app to save
//                                                                          through phg-menu-adapter sync_menu
//   mark_applied    {menu_project_id, sync_token, proposal_id, revision} -> after that save succeeded
// Deliberately absent: submitting or approving proposals. Only the Coordinator does that (service role, SQL), so
// nothing reaches a draft without passing the automatic checks and the Coordinator's approval.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "no-store" } });
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SOURCES = ["user_prompt_flow", "admin_button"];
// Inputs the designer may use (see handoff/agents/MENU_DESIGNER_BRIEF.md section 4); anything else is dropped.
const INPUT_KEYS = ["menu_type", "lists", "items", "price_band", "demographics", "brand", "format", "constraints", "comparables", "venue"];

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "POST required" }, 405);
  const url = Deno.env.get("SUPABASE_URL"), svc = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !svc) return json({ error: "config" }, 500);
  const sb = createClient(url, svc, { auth: { persistSession: false } });

  const bearer = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "").trim();
  if (!bearer) return json({ error: "login required" }, 401);
  const { data: ud } = await sb.auth.getUser(bearer);
  if (!ud?.user) return json({ error: "invalid or expired login" }, 401);

  const b: any = await req.json().catch(() => ({}));
  const action = String(b.action || "");
  const pid = String(b.menu_project_id || "");
  const token = String(b.sync_token || "");
  if (!UUID.test(pid) || !token) return json({ error: "menu_project_id and sync_token required" }, 400);
  const { data: ok, error: ae } = await sb.rpc("phg_menu_authorize", { p_menu_project_id: pid, p_sync_token: token });
  if (ae) return json({ error: ae.message }, 500);
  if (!ok) return json({ error: "invalid_menu_token" }, 403);

  try {
    if (action === "request_design") {
      const request = String(b.request || "").trim().slice(0, 4000);
      const source = String(b.source || "");
      if (!request) return json({ error: "request required" }, 400);
      if (!SOURCES.includes(source)) return json({ error: "source must be user_prompt_flow or admin_button" }, 400);
      const raw = (b.inputs && typeof b.inputs === "object") ? b.inputs : {};
      const inputs: Record<string, unknown> = {};
      for (const k of INPUT_KEYS) if (raw[k] !== undefined) inputs[k] = raw[k];
      if (JSON.stringify(inputs).length > 200_000) return json({ error: "inputs too large" }, 413);
      const { data, error } = await sb.rpc("phg_design_task_create", {
        p_menu_project_id: pid, p_source: source, p_source_detail: String(b.source_detail || "").slice(0, 120) || null,
        p_request: request, p_inputs: inputs, p_requested_by: ud.user.id,
      });
      if (error) throw error;
      return json(data);
    }
    if (action === "design_status") {
      const { data, error } = await sb.rpc("phg_design_status", { p_menu_project_id: pid });
      if (error) throw error;
      return json({ status: "ok", ...data });
    }
    if (action === "take_approved") {
      const prop = String(b.proposal_id || "");
      if (!UUID.test(prop)) return json({ error: "proposal_id required" }, 400);
      const { data, error } = await sb.rpc("phg_design_take_approved", { p_menu_project_id: pid, p_proposal_id: prop });
      if (error) throw error;
      return json(data, data?.error ? 404 : 200);
    }
    if (action === "mark_applied") {
      const prop = String(b.proposal_id || "");
      const rev = Number(b.revision);
      if (!UUID.test(prop) || !Number.isFinite(rev)) return json({ error: "proposal_id and revision required" }, 400);
      const { data, error } = await sb.rpc("phg_design_mark_applied", { p_menu_project_id: pid, p_proposal_id: prop, p_revision: rev });
      if (error) return json({ error: error.message }, 409);
      return json(data);
    }
    return json({ error: "unknown action" }, 400);
  } catch (e: any) {
    return json({ error: String(e?.message || e) }, 500);
  }
});
