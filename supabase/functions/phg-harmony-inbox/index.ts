import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

/* PHG HARMONY INBOX — the iPhone Action-button Shortcut's door into Harmony,
   and the notes log for the app.

   AUTH (deployed with verify_jwt=false; this function authenticates itself):
     - the app:      Authorization: Bearer <user JWT>   (validated with auth.getUser)
     - the Shortcut: x-api-key (or x-harmony-key, or body "key"): <personal key>  (SHA-256 looked up in
                     phg.harmony_device_keys; never stored in plaintext)
   Key management (issue/list/revoke) requires the app login, never a key.

   ACTIONS (JSON body "action", default "inbox"):
     inbox        {text}             -> route to note | answer | open; returns {speak, url}
     add_note     {text, kind?}      -> save a note
     list_notes   {limit?, open_only?}
     update_note  {id, done}         (app only)
     issue_key    {account_id?, name?} (app only) -> {key} shown once
     list_keys / revoke_key {id}     (app only)

   Tables: phg.harmony_notes, phg.harmony_device_keys (RLS on, service_role only).
   Model: OPENAI_API_KEY + gpt-4o-mini (override OPENAI_INBOX_MODEL). */

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-harmony-key, x-api-key",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (x: unknown, s = 200) =>
  new Response(JSON.stringify(x), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

const KINDS = ["note", "task", "idea", "reminder"];

async function sha256hex(s: string) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
function newKey() {
  const b = crypto.getRandomValues(new Uint8Array(32));
  return "hk_" + btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

const ROUTER = [
  "You are Harmony, the voice assistant of PHG (Perfect Harmony Group), a hospitality operations and menu-design app for bars and restaurants.",
  "The user pressed a button on their iPhone and spoke one sentence. Decide what they want and return JSON only.",
  "route = 'note' when they are telling you something to remember or log: notes, tasks, to-dos, ideas, reminders, observations (e.g. 'log that the Tito's delivery was two cases short', 'remind me to call the Sysco rep Friday', 'idea: a smoked pineapple margarita').",
  "route = 'answer' for questions or conversation you can answer in speech, including questions about their saved notes (their recent notes are provided).",
  "route = 'open' when they want to see or do something on screen in the app: design or show a menu, show photos, open the dashboard, show reports, maps. open_query is the request to run in the app.",
  "For notes: kind is task (something to do), reminder (time-bound), idea, or note; note_text is their content cleaned up (no 'log that'/'remind me to' prefix, keep names and numbers exactly); due_iso only if they gave a time, in ISO 8601 with offset for their time zone; tags are 0-3 short lowercase words.",
  "reply is what you say out loud: one or two short, warm, natural sentences. For a note, confirm briefly (e.g. 'Got it, I logged that the Tito's delivery was two cases short.'). For open, say what you're opening. Plain text, no markdown.",
  "Never invent business figures. If they ask for live numbers, route to open with their request so the app runs the report.",
].join(" ");

const SCHEMA = {
  type: "object", additionalProperties: false,
  required: ["route", "kind", "note_text", "tags", "due_iso", "reply", "open_query"],
  properties: {
    route: { type: "string", enum: ["note", "answer", "open"] },
    kind: { type: "string", enum: KINDS },
    note_text: { type: "string" },
    tags: { type: "array", items: { type: "string" } },
    due_iso: { type: ["string", "null"] },
    reply: { type: "string" },
    open_query: { type: ["string", "null"] },
  },
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ ok: false, speak: "Send a POST request.", error: "POST required" }, 405);

  const url = Deno.env.get("SUPABASE_URL");
  const anon = Deno.env.get("SUPABASE_ANON_KEY");
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const oa = Deno.env.get("OPENAI_API_KEY");
  const model = Deno.env.get("OPENAI_INBOX_MODEL") || "gpt-4o-mini";
  const appUrl = (Deno.env.get("PHG_APP_URL") || "https://prismatic-rugelach-777e48.netlify.app").replace(/\/+$/, "");
  if (!url || !anon || !service) return json({ ok: false, speak: "Harmony's inbox is not configured.", error: "runtime configuration missing" }, 500);
  /* v3: phg is not exposed through the REST API (direct table calls got HTTP 406), so every
     read/write goes through public.phg_harmony_inbox_db, a service_role-only SECURITY DEFINER
     dispatcher (migration 20260928230000), the same pattern as phg_auth_bootstrap. */
  const admin = createClient(url, service, { auth: { persistSession: false } });
  const dbx = async (op: string, args: Record<string, unknown>) => {
    const { data, error } = await admin.rpc("phg_harmony_inbox_db", { p_op: op, p_args: args });
    if (error) throw new Error(error.message);
    return data as any;
  };

  const b = await req.json().catch(() => ({}));
  const action = String(b.action || "inbox");

  // ---- who is calling
  let userId: string | null = null, accountId: string | null = null, via: "app" | "shortcut" = "app";
  const bearer = (req.headers.get("Authorization") || "").replace(/^bearer\s+/i, "").trim();
  const hkey = (req.headers.get("x-harmony-key") || req.headers.get("x-api-key") || String(b.key || "")).trim();
  if (hkey) {
    if (!/^hk_[A-Za-z0-9_-]{30,}$/.test(hkey)) return json({ ok: false, speak: "That Harmony key doesn't look right.", error: "bad key" }, 401);
    let k: any = null;
    try { k = await dbx("key_lookup", { hash: await sha256hex(hkey) }); }
    catch (e) { return json({ ok: false, speak: "Harmony couldn't check your key just now. Try again in a moment.", error: String(e) }, 500); }
    if (!k || k.revoked_at) return json({ ok: false, speak: "That Harmony key isn't valid anymore. Make a new one in the app.", error: "invalid key" }, 401);
    userId = k.user_id; accountId = k.account_id; via = "shortcut";
  } else if (bearer && bearer.split(".").length === 3) {
    const sb = createClient(url, anon, { auth: { persistSession: false } });
    const { data: ud, error: ue } = await sb.auth.getUser(bearer);
    if (ue || !ud?.user) return json({ ok: false, error: "invalid or expired login" }, 401);
    userId = ud.user.id;
    accountId = b.account_id ? String(b.account_id) : null;
  } else {
    return json({ ok: false, speak: "Harmony needs your key to hear you.", error: "login or x-harmony-key required" }, 401);
  }
  if (accountId && via === "app") {
    let member = false;
    try { member = (await dbx("is_member", { user: userId, account: accountId })) === true; }
    catch (e) { return json({ ok: false, error: "membership check failed: " + String((e as Error)?.message || e) }, 500); }
    if (!member) return json({ ok: false, error: "not a member of that account" }, 403);
  }
  const appOnly = () => json({ ok: false, error: "sign in to the app for this" }, 403);

  // ---- key management (app login only)
  if (action === "issue_key") {
    if (via !== "app") return appOnly();
    const key = newKey();
    let data: any;
    try { data = await dbx("key_issue", { user: userId, account: accountId, name: String(b.name || "iPhone Shortcut").slice(0, 80), hash: await sha256hex(key), hint: key.slice(-4) }); }
    catch (e) { return json({ ok: false, error: String((e as Error)?.message || e) }, 500); }
    if (data?.error === "limit") return json({ ok: false, error: "5 active keys max; revoke one first" }, 409);
    return json({ ok: true, key, ...data, endpoint: `${url}/functions/v1/phg-harmony-inbox` });
  }
  if (action === "list_keys") {
    if (via !== "app") return appOnly();
    try { return json({ ok: true, items: (await dbx("key_list", { user: userId })) || [] }); }
    catch (e) { return json({ ok: false, error: String((e as Error)?.message || e) }, 500); }
  }
  if (action === "revoke_key") {
    if (via !== "app") return appOnly();
    try { await dbx("key_revoke", { user: userId, id: String(b.id || "") }); return json({ ok: true }); }
    catch (e) { return json({ ok: false, error: String((e as Error)?.message || e) }, 500); }
  }

  // ---- notes
  const listNotes = async (limit: number, openOnly: boolean) => {
    try { return ((await dbx("notes_list", { user: userId, limit, open_only: openOnly })) || []) as any[]; }
    catch { return [] as any[]; }
  };
  const saveNote = async (text: string, kind: string, tags: string[], due: string | null) => {
    return await dbx("note_add", {
      user: userId, account: accountId, kind: KINDS.includes(kind) ? kind : "note",
      body: text.slice(0, 4000), tags: (tags || []).map((t) => String(t).toLowerCase().slice(0, 30)).slice(0, 5),
      due: due && !isNaN(Date.parse(due)) ? new Date(due).toISOString() : "", source: via,
    });
  };
  if (action === "list_notes") {
    return json({ ok: true, items: await listNotes(Math.min(200, Math.max(1, Number(b.limit) || 50)), !!b.open_only) });
  }
  if (action === "update_note") {
    if (via !== "app") return appOnly();
    try { await dbx("note_done", { user: userId, id: String(b.id || ""), done: !!b.done }); return json({ ok: true }); }
    catch (e) { return json({ ok: false, error: String((e as Error)?.message || e) }, 500); }
  }
  if (action === "delete_note") {
    if (via !== "app") return appOnly();
    try { await dbx("note_delete", { user: userId, id: String(b.id || "") }); return json({ ok: true }); }
    catch (e) { return json({ ok: false, error: String((e as Error)?.message || e) }, 500); }
  }
  if (action === "add_note") {
    const text = String(b.text || "").trim();
    if (!text) return json({ ok: false, speak: "I didn't catch anything to log.", error: "text required" }, 400);
    try {
      const n = await saveNote(text, String(b.kind || "note"), Array.isArray(b.tags) ? b.tags : [], b.due_iso || null);
      return json({ ok: true, route: "note", note: n, speak: "Logged." });
    } catch (e) { return json({ ok: false, speak: "I couldn't save that note.", error: String(e) }, 500); }
  }

  // ---- inbox: one spoken sentence from the Shortcut (or the app)
  if (action !== "inbox") return json({ ok: false, error: "unknown action" }, 400);
  const text = String(b.text || b.input || "").trim().slice(0, 2000);
  if (!text) return json({ ok: true, route: "answer", speak: "I'm here. Press and hold, then tell me what to log or ask me anything.", url: "" });
  if (!oa) {
    const n = await saveNote(text, "note", [], null).catch(() => null);
    return json({ ok: !!n, route: "note", speak: n ? "Logged." : "I couldn't save that.", url: "" });
  }
  const tz = String(b.tz || "America/Chicago");
  const recent = await listNotes(15, false);
  const ctx = recent.length
    ? "Their recent notes (newest first):\n" + recent.map((n: any) => `- [${n.kind}${n.done ? ", done" : ""}] ${n.body}${n.due_at ? ` (due ${n.due_at})` : ""} — saved ${n.created_at}`).join("\n")
    : "They have no saved notes yet.";

  const rr = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: { Authorization: `Bearer ${oa}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model, instructions: ROUTER, max_output_tokens: 400,
      input: [{ role: "user", content: [
        { type: "input_text", text: `Current time: ${new Date().toISOString()} (user's time zone ${tz}).\n${ctx}` },
        { type: "input_text", text: "They said: " + text },
      ] }],
      text: { format: { type: "json_schema", name: "harmony_route", strict: true, schema: SCHEMA } },
    }),
  });
  const raw = await rr.json().catch(() => ({}));
  let out: any = null;
  try {
    let t = typeof raw.output_text === "string" ? raw.output_text : "";
    if (!t && Array.isArray(raw.output)) for (const o of raw.output) for (const c of (o?.content || [])) if (c?.type === "output_text") t += c.text || "";
    out = JSON.parse(t);
  } catch { out = null; }
  if (!rr.ok || !out) {
    // never lose what they said: fall back to logging it
    const n = await saveNote(text, "note", [], null).catch(() => null);
    return json({ ok: !!n, route: "note", speak: n ? "I couldn't think it through just now, so I logged it as a note." : "Something went wrong. Try again.", url: "", error: raw?.error?.message });
  }

  let note = null, link = "";
  if (out.route === "note") {
    try { note = await saveNote(out.note_text || text, out.kind, out.tags, out.due_iso); }
    catch (e) { return json({ ok: false, route: "note", speak: "I couldn't save that note.", url: "", error: String(e) }, 500); }
  } else if (out.route === "open") {
    link = `${appUrl}/?harmony=1&q=${encodeURIComponent(out.open_query || text)}`;
  }
  return json({ ok: true, route: out.route, speak: String(out.reply || "Done.").trim(), url: link, note });
});
