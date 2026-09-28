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
   Model: OPENAI_API_KEY + gpt-4.1 (override OPENAI_INBOX_MODEL). */

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

/* v10: CONVERSATION. The Shortcut loops (listen -> Harmony -> speak -> listen) and passes back
   the "context" string each turn, so Harmony remembers the thread without storing anything.
   Before answering an open-ended request she asks ONE narrowing question with concrete choices
   (e.g. classic vs your house Manhattan vs one from the internet vs a few variations vs build one
   together). "next" tells the Shortcut what to do: listen again, open the app (only when asked
   to see it on screen; iPhone still requires Face ID), or end. */
const CONVERSE = [
  "You are Harmony, the voice assistant of PHG (Perfect Harmony Group), a bar and restaurant operations and menu-design app. This is a hands-free voice conversation from the iPhone Action button; the phone may be locked, so everything is heard, never seen.",
  "You get the recent turns and what you last showed them (context), then their new words. Decide the next action and return JSON only.",
  "clarify: when a request is open-ended or has meaningfully different versions, ask ONE short question offering 2 to 5 concrete choices before answering. Recipes: 'Do you want the classic Manhattan, your house Manhattan, one from the internet, a few variations to pick from, or should we build one together?'. Data: ask for the missing piece. Prices, venues, bars and menus need a place: if they gave no city or state, ask which one (PHG covers Iowa, Colorado and New York, or all three). Prices also need the drink; venues may need the kind of place. Menus: which venue and city. Do NOT clarify when they already chose, answered your question in context, said 'just', 'quick' or 'the usual', or for notes.",
  "recipe: once the drink and version are known. recipe_drink = the drink exactly as they named it, keeping every modifier (a 'chocolate Manhattan' is NOT a Manhattan; 'smoked', 'spicy', 'frozen', 'mezcal' versions keep that word). recipe_source = classic | house | internet | list | create. If they already said where they want it from ('from the internet', 'my house one', 'the classic'), use that and do not ask again. Twists that are not classics (chocolate Manhattan, spicy margarita) default to internet or create, never to the classic spec of the base drink.",
  "Understand context: read the whole conversation. Short answers ('the second one', 'yeah the internet', 'Denver', 'my house') answer your last question. Never repeat a question they already answered. Sound like a sharp bartender colleague, not a form: one natural question at a time, and only when it changes the answer.",
  "data: PHG data they want answered (NOM distilleries and where they are, distilleries in a town, venues or bars in a city, a venue's real menu, drink prices and averages, top brands, spirit categories on menus, a venue's drinks profile, ZIP census demographics, label approvals, how much data PHG has); data_query = the full, specific question.",
  "note: they want something logged or remembered (task, reminder, idea, note); note_text cleaned up, kind, tags, due_iso (ISO 8601 with their offset) only if they gave a time. Never clarify notes.",
  "read_back: they want the last result read out loud instead of opened ('don't open it', 'just tell me', 'read it to me', 'what were they'); put the full read-out, from context.last.detail, in say, in natural speech.",
  "Questions PHG data can answer (where a NOM distillery is, even 'show me on a map'; venues, menus, prices, brands, demographics) are ALWAYS data first, so they hear the real answer; the app offer comes after. offer_open: only when they explicitly ask to open the app or the screen and there is nothing to look up first; you may ASK 'Want me to open it in the Harmony app?' (put that question in say). open_screen: ONLY when your previous turn asked whether to open the app AND they now clearly agree (yes, sure, do it, let's do it, approve, open it, go ahead). Otherwise never open anything. open_query = what to show if it isn't the last result.",
  "answer: general conversation or bar knowledge you can answer directly in speech (1 to 4 sentences). Never answer facts about specific distilleries, NOMs, venues, menus or prices from memory; use data.",
  "end: they're finished ('that's all', 'no thanks', 'nope', 'bye', 'stop', 'I'm good').",
  "say: what you say now for clarify, answer, read_back, note (brief confirmation), open_screen ('Opening it now.') and end (a short goodbye). Leave say empty for recipe and data; those are spoken by the next step. Warm, natural, plain text, no markdown, no filler.",
  "Never invent business figures or prices.",
].join(" ");

const RECIPE_VOICE = [
  "You are Harmony, an expert bartender speaking hands-free; everything you say is heard, not seen.",
  "Walk them through the drink: the ingredients with exact measurements in ounces (and dashes or barspoons), then the method step by step (build, stir or shake, strain, ice), then the glass and the garnish.",
  "TECHNIQUE (PHG house standard, from the owner): stirred drinks are stirred for six to eight seconds. Never state any other stir or shake duration, dilution time or temperature unless it is in the spec you were given; for shaken drinks say 'shake hard' without a time.",
  "Say where the spec comes from in a few words (your house recipe, the classic spec, or the named source). If a spec is given, follow it exactly; fill a missing measurement only from the classic spec and say so.",
  "Plain spoken sentences, no lists, no markdown, no symbols like ½ (say 'three quarters of an ounce'). 60 to 130 words. End with the garnish; no sign-off.",
].join(" ");

const LIST_VOICE = [
  "You are Harmony, an expert bartender speaking hands-free. List four or five well-known variations of the drink (include their house version first if one is given), one short sentence each on what makes it different, then ask which one they want walked through. Plain speech, no lists or markdown, under 110 words.",
].join(" ");

const CREATE_VOICE = [
  "You are Harmony, building a new cocktail together with a bar owner, hands-free. If you don't yet know their base spirit, flavour direction and occasion, ask the single most useful question with two to four choices. Once you know enough, propose one original spec with exact measurements, method, glass and garnish in natural speech, give it a short name, then ask if they want to tweak it or log it. Under 120 words, plain speech.",
].join(" ");

const KIND_ENUM = KINDS;
const SCHEMA = {
  type: "object", additionalProperties: false,
  required: ["action", "say", "recipe_drink", "recipe_source", "data_query", "open_query", "note_text", "kind", "tags", "due_iso"],
  properties: {
    action: { type: "string", enum: ["clarify", "recipe", "data", "note", "read_back", "offer_open", "open_screen", "answer", "end"] },
    say: { type: "string" },
    recipe_drink: { type: ["string", "null"] },
    recipe_source: { type: "string", enum: ["classic", "house", "internet", "list", "create", "none"] },
    data_query: { type: ["string", "null"] },
    open_query: { type: ["string", "null"] },
    note_text: { type: "string" },
    kind: { type: "string", enum: KIND_ENUM },
    tags: { type: "array", items: { type: "string" } },
    due_iso: { type: ["string", "null"] },
  },
};

async function llm(oa: string, model: string, instructions: string, input: string, opts: Record<string, unknown> = {}) {
  const r = await fetch("https://api.openai.com/v1/responses", {
    method: "POST", headers: { Authorization: `Bearer ${oa}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, instructions, input, max_output_tokens: 600, ...opts }),
  });
  const j = await r.json().catch(() => ({}));
  let t = typeof j.output_text === "string" ? j.output_text : "";
  if (!t && Array.isArray(j.output)) for (const o of j.output) for (const c of (o?.content || [])) if (c?.type === "output_text") t += c.text || "";
  return { ok: r.ok, text: t.trim(), error: j?.error?.message };
}

/* a compact spoken-friendly summary of a data view, kept in context for "read it to me" */
function viewDetail(v: any): string {
  if (!v) return "";
  const out: string[] = [];
  if (v.title) out.push(v.title);
  (v.tiles || []).forEach((t: any) => out.push(`${t.label}: ${t.value}`));
  const bars = v.bars?.bars || v.bars || v.side?.bars || [];
  if (Array.isArray(bars)) bars.slice(0, 10).forEach((b: any) => out.push(`${b.label}: ${b.value}${b.sub ? " (" + b.sub + ")" : ""}`));
  (v.slices || []).slice(0, 8).forEach((b: any) => out.push(`${b.label}: ${b.value}`));
  if (v.card) { (v.card.rows || []).forEach((r: any) => out.push(`${r[0]}: ${r[1]}`)); if (v.card.chips?.length) out.push("Brands: " + v.card.chips.slice(0, 15).join(", ")); }
  (v.rows || []).forEach((r: any) => Array.isArray(r) && out.push(`${r[0]}: ${r[1]}`));
  if (v.spec) out.push("Spec: " + v.spec);
  (v.table?.rows || []).slice(0, 8).forEach((r: any) => out.push(r.join(" · ")));
  (v.pins || []).slice(0, 8).forEach((p: any) => out.push(`${p.label}${p.sub ? " — " + p.sub : ""}`));
  return out.join("\n").slice(0, 1800);
}

async function readBody(req: Request): Promise<Record<string, any>> {
  const ct = (req.headers.get("content-type") || "").toLowerCase();
  let raw = "";
  try {
    if (ct.includes("multipart/form-data")) {
      const fd = await req.formData(); const o: Record<string, any> = {};
      fd.forEach((v, k) => { o[k] = typeof v === "string" ? v : ""; });
      return lower(o);
    }
    raw = await req.text();
  } catch { return {}; }
  const t = raw.trim();
  if (!t) return {};
  if (t.startsWith("{")) { try { const j = JSON.parse(t); if (j && typeof j === "object") return lower(j); } catch { /* fall through */ } }
  if (ct.includes("application/x-www-form-urlencoded") || (/^[\w-]+=/.test(t) && !/\s/.test(t.split("&")[0].split("=")[0]))) {
    const o: Record<string, any> = {}; new URLSearchParams(t).forEach((v, k) => { o[k] = v; }); return lower(o);
  }
  return { text: t }; // plain text body: the whole thing is what they said
}
function lower(o: Record<string, any>) {
  const out: Record<string, any> = {};
  for (const [k, v] of Object.entries(o)) out[String(k).trim().toLowerCase()] = v;
  return out;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ ok: false, speak: "Send a POST request.", error: "POST required" }, 405);

  const url = Deno.env.get("SUPABASE_URL");
  const anon = Deno.env.get("SUPABASE_ANON_KEY");
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const oa = Deno.env.get("OPENAI_API_KEY");
  const model = Deno.env.get("OPENAI_INBOX_MODEL") || "gpt-4.1"; // v12: stronger model; the mini model lost context
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

  /* v5: Shortcuts can send the Request Body as JSON, Form (urlencoded or multipart) or plain
     text, and people name the field "text", "Text", etc. Read all of them, case-insensitively. */
  const b: Record<string, any> = await readBody(req);
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

  // ---- inbox: one turn of the conversation (the Shortcut loops; the app calls it once)
  if (action !== "inbox") return json({ ok: false, error: "unknown action" }, 400);
  /* v6: take the words from whatever field the Shortcut used */
  const RESERVED = new Set(["key", "action", "tz", "account_id", "kind", "tags", "due_iso", "limit", "open_only", "id", "done", "name", "context"]);
  const others = Object.entries(b).filter(([k]) => !RESERVED.has(k));
  const pick = () => {
    for (const k of ["text", "input", "query", "prompt", "message", "dictated text", "dictated_text", "words", "q"]) {
      if (typeof b[k] === "string" && b[k].trim()) return b[k];
    }
    const filled = others.filter(([, v]) => typeof v === "string" && v.trim()).sort((x, y) => String(y[1]).length - String(x[1]).length);
    if (filled.length) return String(filled[0][1]);
    const named = others.map(([k]) => k).filter((k) => /\s/.test(k)).sort((x, y) => y.length - x.length);
    return named[0] || "";
  };
  const text = String(pick()).trim().slice(0, 2000);
  let ctx: any = { turns: [], last: null };
  try { const c = typeof b.context === "string" ? JSON.parse(b.context) : b.context; if (c && typeof c === "object") ctx = { turns: Array.isArray(c.turns) ? c.turns.slice(-6) : [], last: c.last || null, offered: !!c.offered }; } catch { /* fresh conversation */ }
  console.log(JSON.stringify({ inbox: via, fields: Object.keys(b).filter((k) => k !== "key"), text_len: text.length, turns: ctx.turns.length }));
  const home = `${appUrl}/?harmony=1`;
  const withQ = (q: string) => `${appUrl}/?harmony=1&q=${encodeURIComponent(q)}`;
  /* v12: "url" is filled ONLY when Harmony is actually opening the app (next = "open"), so an
     older Shortcut that opens any non-empty url never opens on its own. The link is kept in
     app_url for display. Opening happens only after Harmony asked "Want me to open it in the
     Harmony app?" (offered = true in context) and they said yes. */
  const reply = (speak: string, next: "listen" | "open" | "end", extra: Record<string, unknown> = {}, last: any = ctx.last, offered = false) => {
    const turns = [...ctx.turns, { u: text.slice(0, 300), h: speak.slice(0, 400) }].slice(-6);
    const link = String(extra.url || last?.url || home);
    return json({ ok: true, speak, next, ...extra, url: next === "open" ? link : "", app_url: link, context: JSON.stringify({ turns, last, offered }) });
  };
  if (!text) {
    return reply(ctx.turns.length ? "I didn't catch that. Say it again, or say that's all." : "I'm listening. Ask me anything, or tell me what to log.", "listen");
  }
  if (!oa) {
    const n = await saveNote(text, "note", [], null).catch(() => null);
    return reply(n ? "Logged." : "I couldn't save that.", "end");
  }
  const tz = String(b.tz || "America/Chicago");
  const recent = await listNotes(10, false);
  const plannerInput = [
    `Current time: ${new Date().toISOString()} (user's time zone ${tz}).`,
    recent.length ? "Their recent notes: " + recent.map((n: any) => `[${n.kind}${n.done ? ", done" : ""}] ${n.body}`).join(" | ") : "",
    ctx.turns.length ? "Conversation so far:\n" + ctx.turns.map((t: any) => `User: ${t.u}\nHarmony: ${t.h}`).join("\n") : "This is the start of the conversation.",
    ctx.last ? `Last result (context.last): ${ctx.last.title || ""}\n${ctx.last.detail || ""}` : "",
    ctx.offered ? "Your previous turn asked whether to open the Harmony app." : "You have NOT offered to open the app in your previous turn, so open_screen is not allowed now.",
    "They now said: " + text,
  ].filter(Boolean).join("\n\n");
  const plan = await llm(oa, model, CONVERSE, plannerInput, { max_output_tokens: 500, text: { format: { type: "json_schema", name: "harmony_turn", strict: true, schema: SCHEMA } } });
  let out: any = null;
  try { out = JSON.parse(plan.text); } catch { out = null; }
  if (!out) {
    const n = await saveNote(text, "note", [], null).catch(() => null);
    return reply(n ? "I couldn't think that through just now, so I logged it as a note." : "Something went wrong. Try again.", "end", { error: plan.error });
  }
  const say = String(out.say || "").trim();

  if (out.action === "end") return reply(say || "Okay. Talk soon.", "end");
  if (out.action === "clarify" || out.action === "answer" || out.action === "read_back") return reply(say || "Say that again?", "listen");
  if (out.action === "offer_open" || (out.action === "open_screen" && !ctx.offered)) {
    const last = out.open_query ? { ...(ctx.last || {}), url: withQ(String(out.open_query)) } : ctx.last;
    return reply(say && /open/i.test(say) ? say : "Want me to open it in the Harmony app?", "listen", {}, last, true);
  }
  if (out.action === "open_screen") {
    /* v15: open exactly what was offered; open_query only when nothing was */
    const target = ctx.last?.url || (out.open_query ? withQ(String(out.open_query)) : home);
    return reply(say || "Opening it now.", "open", { url: target });
  }
  if (out.action === "note") {
    try { await saveNote(out.note_text || text, out.kind, out.tags, out.due_iso); }
    catch (e) { return reply("I couldn't save that note.", "listen", { error: String(e) }); }
    return reply((say || "Got it, logged.") + " Anything else?", "listen");
  }
  if (out.action === "data") {
    const q = String(out.data_query || text).trim();
    try {
      const dr = await fetch(`${url}/functions/v1/phg-harmony-data`, {
        method: "POST", headers: { "Content-Type": "application/json", apikey: anon, "x-phg-internal": service },
        body: JSON.stringify({ prompt: q }),
      });
      const dj = await dr.json().catch(() => ({}));
      if (dr.ok && dj.source === "menu_lookup") {
        return reply("That menu is a document, so it needs the screen. Want me to open it in the Harmony app?", "listen", {}, { title: q, detail: "", url: withQ(q) }, true);
      }
      if (dr.ok && dj.speak && dj.source !== "none") {
        const last = { title: dj.view?.title || q, detail: viewDetail(dj.view), url: withQ(q) };
        /* v14: visual results (map, chart) are spoken first, then the app is offered; a yes opens it */
        const visual = /^(map|bars|donut|dashboard)$/.test(String(dj.view?.type || ""));
        const more = visual ? " Want me to open it in the Harmony app?" : dj.view && dj.view.type !== "empty" ? " Want me to read you the details?" : " Anything else?";
        return reply(String(dj.speak) + more, "listen", {}, last, visual);
      }
    } catch (e) { console.log(JSON.stringify({ data_error: String(e) })); }
    return reply("I couldn't find that in PHG's data. Try asking it another way.", "listen");
  }
  if (out.action === "recipe") {
    const drink = String(out.recipe_drink || "").replace(/[%_,()]/g, " ").trim();
    const src = out.recipe_source;
    let house: any[] = [];
    if (accountId && (src === "house" || src === "list")) {
      /* v13: "my house Manhattan" -> look up "Manhattan"; fall back to each longer word */
      const hq = drink.replace(/\b(my|our|the|a|house|in-house|signature|version|recipe|spec)\b/gi, " ").replace(/\s+/g, " ").trim();
      const tries = [hq, ...hq.split(" ").filter((w) => w.length >= 4).sort((x, y) => y.length - x.length)];
      for (const q of tries) {
        if (!q) continue;
        try { house = (await dbx("house_recipes", { user: userId, account: accountId, q })) || []; } catch { house = []; }
        if (house.length) break;
      }
    }
    let ref: any = null;
    if (drink && src !== "internet") {
      const { data } = await admin.from("cocktail_reference").select("cocktail_name,base_spirit,consensus_spec,method,glassware,garnish,profile").ilike("cocktail_name", drink).limit(1);
      ref = data?.[0] || null;
    }
    const cardUrl = withQ(`How do you make a ${drink}?`);
    let speakText = "";
    if (src === "house") {
      if (!house.length) return reply(`I don't see a ${drink || "drink like that"} on your house menu yet. Want the classic spec instead, or one from the internet?`, "listen");
      const h = house[0];
      speakText = (await llm(oa, model, RECIPE_VOICE, `They asked for their HOUSE recipe. Drink: ${h.name}. House recipe (use exactly): ${JSON.stringify({ ingredients: h.ingredients, method: h.method, glassware: h.glassware, garnish: h.garnish, menu_price: h.menu_price, description: h.menu_description })}`)).text;
    } else if (src === "internet") {
      const w = await llm(oa, Deno.env.get("OPENAI_WEB_MODEL") || "gpt-4.1", RECIPE_VOICE + " Search the web for a well-regarded recipe for EXACTLY the drink asked for (keep every modifier, e.g. a chocolate Manhattan uses chocolate bitters or crème de cacao, not a plain Manhattan) from a reputable cocktail source (for example Difford's Guide, PUNCH, Liquor.com, Imbibe), follow its measurements, and name the source.", `Find and speak a recipe for: ${drink}. What they said: ${text}`, { tools: [{ type: "web_search_preview" }] });
      speakText = w.text || (await llm(oa, model, RECIPE_VOICE, `Drink: ${drink}. The web search failed; use the classic spec and say it's the classic.` + (ref ? ` PHG reference: ${JSON.stringify(ref)}` : ""))).text;
    } else if (src === "list") {
      speakText = (await llm(oa, model, LIST_VOICE, `Drink: ${drink}.` + (house.length ? ` Their house version: ${JSON.stringify(house[0])}` : " They have no house version.") + (ref ? ` Classic reference: ${JSON.stringify(ref)}` : ""))).text;
      return reply(speakText || `I couldn't list ${drink} variations just now.`, "listen", {}, { title: `${drink} variations`, detail: speakText, url: cardUrl });
    } else if (src === "create") {
      const convo = ctx.turns.map((t: any) => `User: ${t.u}\nHarmony: ${t.h}`).join("\n");
      speakText = (await llm(oa, model, CREATE_VOICE, `Conversation so far:\n${convo}\nThey now said: ${text}\nStarting point: ${drink || "(not set)"}`)).text;
      return reply(speakText || "Tell me the base spirit you want to build around.", "listen", {}, { title: `New ${drink || "cocktail"}`, detail: speakText, url: home });
    } else {
      speakText = (await llm(oa, model, RECIPE_VOICE, `Drink: ${ref?.cocktail_name || drink}. What they said: ${text}. ` + (ref ? `PHG classic reference spec: ${JSON.stringify(ref)}` : "No PHG reference; use the widely accepted classic spec for exactly this drink."))).text;
    }
    const last = { title: `${drink} recipe`, detail: speakText, url: cardUrl };
    return reply((speakText || `I couldn't pull that recipe just now.`) + " Want another version, or anything else?", "listen", {}, last);
  }
  return reply(say || "Say that again?", "listen");
});
