import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
import { DESIGN_KNOWLEDGE } from "./design_knowledge.ts";

/* PHG HARMONY ATTACH — Harmony's conversation brain in the Harmony view.
   v6: menus and looks are designed from PHG's design knowledge base (design_knowledge.ts) and carry a creative thesis.
   v5: every drafted menu carries its own design (palette, fonts, layout, art style); mode "design" invents a
       new look for the current menu.
   v3: mode "menu" drafts/revises a whole menu as strict JSON (see MENU_INSTRUCTIONS).
   v2: also answers plain conversation with no attachments (mode "chat"), so
   everyday questions no longer fall through to the finance command router
   (which answered everything with "Management dashboard completed").

   With attachments it answers a prompt about attached photos, video, PDFs or
   text files.

   The app prepares everything in the browser: photos are downscaled JPEGs,
   a video arrives as a handful of still frames, PDFs as base64, and text,
   CSV or JSON files as plain text. This function only sends them to the
   model with Harmony's voice rules and returns one short reply that the app
   types on screen and speaks aloud. It reads and writes no PHG data.
   Uses the existing OPENAI_API_KEY secret (same key as the voice functions). */

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (x: unknown, s = 200) =>
  new Response(JSON.stringify(x), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

const INSTRUCTIONS = [
  "You are Harmony, the assistant inside PHG, a hospitality operations and menu-design app for bars and restaurants.",
  "The user has attached one or more files (photos, video frames, a PDF or a text file) and asked a question about them.",
  "Answer in plain spoken sentences: no markdown, no bullet symbols, no headings. Your reply is typed on screen and read aloud.",
  "Keep it under 120 words unless the user asks for detail. Lead with the direct answer.",
  "Describe only what is actually visible or written in the attachments. Never invent prices, quantities, names or numbers; if something cannot be read, say so.",
  "Video arrives as still frames sampled in order; treat them as a sequence, and say you are looking at frames rather than full video when it matters.",
  "When useful for a bar or restaurant (menus, drinks, plating, invoices, inventory, spaces), add one practical observation or next step.",
].join(" ");

const CHAT_INSTRUCTIONS = [
  "You are Harmony, the voice assistant inside PHG (Perfect Harmony Group), a hospitality operations and menu-design app for bars and restaurants.",
  "Speak naturally and warmly, like a sharp bar-industry colleague. Plain spoken sentences only: no markdown, no lists, no headings. Your reply is typed on screen and read aloud, so keep it to one to four sentences unless asked for more.",
  "What the app can do from this screen, so you can guide the user: say 'make a menu' (or tap + then Start a menu) to open Menu Studio, where they can say next, back, darker, use gold, title something, change the splash page, paint it, or add reference photos;",
  "tap + then 'Photo, video or file' to show you a photo, a short video, a PDF or a spreadsheet export and ask about it; ask about sales, labor, costs, expenses, P&L, budgets or forecasts to run the business reports; the gear menu has Brief, Recent work, Tools, Chat history and Voice settings.",
  "You cannot see the user's live business numbers in this conversation; if they ask for figures, tell them to ask for the specific report (for example 'show me last week's sales') and it will run.",
  "Never invent prices, figures, names or facts about their business. Bar and restaurant expertise (cocktails, spirits, menu design, pricing strategy, service, operations) is welcome.",
  "When they are describing a menu concept (venue, style, spirits, number of drinks, price point), help shape it with them, then offer: say 'build it' or 'make the menu' and you will draft it on screen from this conversation.",
].join(" ");

/* v3: MENU mode - Harmony drafts or revises a whole drinks menu from the
   conversation, so the Menu Studio shows what was discussed instead of a
   built-in sample. Output is strict JSON the app renders as live text. */
/* v5: every menu gets its OWN look (was: one of five fixed designs, so every menu looked the same).
   The app renders it on one of five page layouts, with the palette, fonts and art style invented here. */
const DISPLAY_FONTS = ["DM Serif Display", "Playfair Display", "Cormorant Garamond", "Bebas Neue", "Space Grotesk", "Abril Fatface", "Fraunces", "Syne", "Unbounded", "Marcellus", "Rozha One", "Yeseva One", "Righteous", "Monoton", "Big Shoulders Display", "Italiana", "Limelight", "Chivo", "Archivo Black", "Libre Caslon Display"];
const BODY_FONTS = ["Inter", "EB Garamond", "Work Sans", "DM Sans", "Lora", "IBM Plex Sans", "Source Serif 4", "Karla", "Manrope", "Crimson Pro"];
const DESIGN_RULES = "design = a visual identity made for THIS concept, different from any look listed as already used: thesis (one sentence: the intended identity and guest experience, from which every choice follows), name (one or two evocative words, not a generic label), layout (solstice = painted field above, reading field below, a sun or focal disc; garden = airy panes and arches; noche = dark cinematic field; swiss = geometric grid with bold shapes; letterpress = classic engraved frame), palette (bg, paper, ink, muted, accent, art1, art2, art3 as #rrggbb; ink must read clearly on paper and bg, contrast at least 7:1; dark palettes are fine), display_font and body_font from the lists, art_style = one sentence describing the painted artwork style (medium, texture, light, mood; no text in the art).";
const DESIGN_PROPS = {
  type: "object", additionalProperties: false,
  required: ["thesis", "name", "layout", "palette", "display_font", "body_font", "art_style"],
  properties: {
    thesis: { type: "string" },
    name: { type: "string" },
    layout: { type: "string", enum: ["solstice", "garden", "noche", "swiss", "letterpress"] },
    palette: { type: "object", additionalProperties: false, required: ["bg", "paper", "ink", "muted", "accent", "art1", "art2", "art3"],
      properties: { bg: { type: "string" }, paper: { type: "string" }, ink: { type: "string" }, muted: { type: "string" }, accent: { type: "string" }, art1: { type: "string" }, art2: { type: "string" }, art3: { type: "string" } } },
    display_font: { type: "string", enum: DISPLAY_FONTS },
    body_font: { type: "string", enum: BODY_FONTS },
    art_style: { type: "string" },
  },
};
const DESIGN_INSTRUCTIONS = [
  "You are Harmony, the menu designer inside PHG. Invent ONE new visual design for the drinks menu described.",
  "It must be clearly different from every look listed as already used (different palette family, layout or type pairing), unless they asked to tweak the current one.",
  "Follow any direction they gave (e.g. more modern, darker, beachy, luxurious, 70s).",
  DESIGN_RULES,
  "reply = one short spoken sentence naming the new look and what makes it different.",
  DESIGN_KNOWLEDGE,
].join(" ");
const DESIGN_SCHEMA = { type: "object", additionalProperties: false, required: ["reply", "design"], properties: { reply: { type: "string" }, design: DESIGN_PROPS } };

const MENU_INSTRUCTIONS = [
  "You are Harmony, the menu designer inside PHG, working with a bar or restaurant owner.",
  "Write or revise a complete drinks menu as JSON for the concept in the conversation. If a current menu is given and the request is an edit (add, remove, rename, reprice, more of, fewer, swap), change only what was asked and keep everything else exactly; set changed=true. If they ask for a brand new or different menu, write a new one; changed=true. If they only asked a question or gave feedback that needs no change, answer in reply, set changed=false and return the current menu unchanged (or an empty menu if none).",
  "Menu shape: a short venue-style title (the venue name if they gave one, otherwise a fitting name), a subtitle like 'Cocktail Bar · Des Moines, Iowa' when a place is known, 3 to 5 sections, 14 to 28 items in total. Section kinds: cocktails, zero (non-alcoholic), beer, wine, spirits, food, other.",
  "Each item: name; price as a plain number string (wine may be 'glass / bottle' like '12 / 44'); sensory = a short evocative tasting line of 3 to 7 words; ingredients = ingredients in role order (base spirit, modifiers, sweetener, acid, lengthener, bitters) joined with ' · ' (for beer: brewery · city; for wine: producer · region; for spirits: region or style); serve = garnish · glass for cocktails, otherwise empty.",
  "Price realistically for the concept and city (US bar pricing). Use real, widely available brands only when the user asked for them or they are generic category names; otherwise use generic names (e.g. 'reposado tequila', 'house amaro').",
  "No slogans, no taglines, no filler lines anywhere. style_hint picks the visual direction that suits the concept: solstice (sunny, Mexican, coastal, citrus), garden (brunch, botanical, wine, daytime), noche (night, cocktail lounge, speakeasy, tiki, neon), swiss (modern, brewery, minimal), letterpress (classic, supper club, steakhouse, whiskey). concept = a short visual subject for painted art (no text).",
  "reply = one or two warm spoken sentences saying what you made or changed. Plain text.",
  DESIGN_RULES,
  DESIGN_KNOWLEDGE,
].join(" ");
const menuSchema = (withDesign: boolean) => ({
  type: "object", additionalProperties: false, required: ["reply", "changed", "menu"],
  properties: {
    reply: { type: "string" },
    changed: { type: "boolean" },
    menu: {
      type: "object", additionalProperties: false,
      required: withDesign ? ["title", "subtitle", "concept", "style_hint", "design", "sections"] : ["title", "subtitle", "concept", "style_hint", "sections"],
      properties: {
        title: { type: "string" }, subtitle: { type: "string" }, concept: { type: "string" },
        style_hint: { type: "string", enum: ["solstice", "garden", "noche", "swiss", "letterpress"] },
        ...(withDesign ? { design: DESIGN_PROPS } : {}),
        sections: { type: "array", items: {
          type: "object", additionalProperties: false, required: ["name", "kind", "items"],
          properties: {
            name: { type: "string" },
            kind: { type: "string", enum: ["cocktails", "zero", "beer", "wine", "spirits", "food", "other"] },
            items: { type: "array", items: {
              type: "object", additionalProperties: false, required: ["name", "price", "sensory", "ingredients", "serve"],
              properties: { name: { type: "string" }, price: { type: "string" }, sensory: { type: "string" }, ingredients: { type: "string" }, serve: { type: "string" } },
            } },
          },
        } },
      },
    },
  },
});
const MENU_SCHEMA = menuSchema(true), MENU_SCHEMA_LEGACY = menuSchema(false);

const isImg = (x: unknown) => typeof x === "string" && /^data:image\/(jpeg|png|webp);base64,/.test(x);

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST required" }, 405);

  const url = Deno.env.get("SUPABASE_URL");
  const anon = Deno.env.get("SUPABASE_ANON_KEY");
  const oa = Deno.env.get("OPENAI_API_KEY");
  const model = Deno.env.get("OPENAI_VISION_MODEL") || "gpt-4o-mini";
  if (!url || !anon || !oa) return json({ error: "runtime configuration missing" }, 500);

  const auth = req.headers.get("Authorization") || "";
  if (!auth.toLowerCase().startsWith("bearer ")) return json({ error: "login required" }, 401);
  const sb = createClient(url, anon, { auth: { persistSession: false }, global: { headers: { Authorization: auth } } });
  const { data: ud, error: ue } = await sb.auth.getUser(auth.slice(7).trim());
  if (ue || !ud?.user) return json({ error: "invalid or expired login" }, 401);

  const b = await req.json().catch(() => ({}));

  const used = (Array.isArray(b.used_looks) ? b.used_looks : []).slice(-12).map((x: any) => String(x).slice(0, 160));
  if (b.mode === "design") {
    const recentD = Array.isArray(b.recent) ? b.recent.slice(-8) : [];
    const cur = b.current && typeof b.current === "object" ? JSON.stringify(b.current).slice(0, 6000) : "";
    const rd = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: { Authorization: `Bearer ${oa}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: Deno.env.get("OPENAI_MENU_MODEL") || model, instructions: DESIGN_INSTRUCTIONS, max_output_tokens: 900,
        input: [{ role: "user", content: [
          { type: "input_text", text: "Menu: " + (cur || "(none)") },
          { type: "input_text", text: "Looks already used: " + (used.join(" | ") || "(none)") },
          { type: "input_text", text: "Conversation: " + (recentD.map((m: any) => `${m.role === "user" ? "Owner" : "Harmony"}: ${String(m.text || "").slice(0, 300)}`).join("\n") || "(none)") },
          { type: "input_text", text: "Request: " + (String(b.prompt || "").trim().slice(0, 600) || "A new look.") },
        ] }],
        text: { format: { type: "json_schema", name: "harmony_design", strict: true, schema: DESIGN_SCHEMA } },
      }),
    });
    const rawD = await rd.json().catch(() => ({}));
    if (!rd.ok) return json({ error: "design failed", detail: rawD?.error?.message || rawD }, 502);
    let td = typeof rawD.output_text === "string" ? rawD.output_text : "";
    if (!td && Array.isArray(rawD.output)) for (const o of rawD.output) for (const c of (o?.content || [])) if (c?.type === "output_text") td += c.text || "";
    try { return json({ status: "ok", mode: "design", model, ...JSON.parse(td) }); }
    catch { return json({ error: "design returned nothing" }, 502); }
  }

  if (b.mode === "menu") {
    const recentM = Array.isArray(b.recent) ? b.recent.slice(-12) : [];
    const cur = b.current && typeof b.current === "object" ? JSON.stringify(b.current).slice(0, 20000) : "";
    const ask = String(b.prompt || "").trim().slice(0, 2000) || "Draft the menu we discussed.";
    const callMenu = (schema: unknown) => fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: { Authorization: `Bearer ${oa}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: Deno.env.get("OPENAI_MENU_MODEL") || model, instructions: MENU_INSTRUCTIONS, max_output_tokens: 6000,
        input: [{ role: "user", content: [
          { type: "input_text", text: "Conversation so far:\n" + (recentM.map((m: any) => `${m.role === "user" ? "Owner" : "Harmony"}: ${String(m.text || "").slice(0, 600)}`).join("\n") || "(none)") },
          { type: "input_text", text: cur ? "Current menu JSON:\n" + cur : "There is no current menu yet." },
          { type: "input_text", text: "Looks already used: " + (used.join(" | ") || "(none)") },
          { type: "input_text", text: "Request: " + ask },
        ] }],
        text: { format: { type: "json_schema", name: "harmony_menu", strict: true, schema } },
      }),
    });
    /* v5 safety net: if the design-bearing schema is refused, draft with the v3 schema (no design) */
    let rm = await callMenu(MENU_SCHEMA);
    if (rm.status === 400) { console.log(JSON.stringify({ menu_schema_fallback: true })); rm = await callMenu(MENU_SCHEMA_LEGACY); }
    const rawM = await rm.json().catch(() => ({}));
    if (!rm.ok) return json({ error: "menu drafting failed", detail: rawM?.error?.message || rawM }, 502);
    let t = typeof rawM.output_text === "string" ? rawM.output_text : "";
    if (!t && Array.isArray(rawM.output)) for (const o of rawM.output) for (const c of (o?.content || [])) if (c?.type === "output_text") t += c.text || "";
    try { const out = JSON.parse(t); return json({ status: "ok", mode: "menu", model, ...out }); }
    catch { return json({ error: "menu drafting returned no menu" }, 502); }
  }

  const prompt = String(b.prompt || "").trim().slice(0, 4000) || "What is this? Tell me what matters about it.";
  const images: string[] = (Array.isArray(b.images) ? b.images : []).filter(isImg).slice(0, 6);
  const video = b.video && Array.isArray(b.video.frames)
    ? { name: String(b.video.name || "video").slice(0, 120), duration: Number(b.video.duration) || null, frames: b.video.frames.filter(isImg).slice(0, 8) }
    : null;
  const pdf = b.pdf && typeof b.pdf.data === "string" && /^data:application\/pdf;base64,/.test(b.pdf.data) && b.pdf.data.length < 12_000_000
    ? { name: String(b.pdf.name || "file.pdf").slice(0, 120), data: b.pdf.data }
    : null;
  const texts: { name: string; content: string }[] = (Array.isArray(b.texts) ? b.texts : [])
    .filter((t: any) => t && typeof t.content === "string")
    .slice(0, 3)
    .map((t: any) => ({ name: String(t.name || "file.txt").slice(0, 120), content: t.content.slice(0, 60_000) }));
  const chat = !images.length && !video?.frames.length && !pdf && !texts.length;
  if (chat && !String(b.prompt || "").trim()) return json({ error: "prompt required" }, 400);

  const content: any[] = [];
  const recent = Array.isArray(b.recent) ? b.recent.slice(-6) : [];
  if (recent.length) {
    content.push({ type: "input_text", text: "Recent conversation for context:\n" + recent.map((m: any) => `${m.role === "user" ? "User" : "Harmony"}: ${String(m.text || "").slice(0, 400)}`).join("\n") });
  }
  for (const t of texts) content.push({ type: "input_text", text: `Attached file "${t.name}":\n${t.content}` });
  if (pdf) content.push({ type: "input_file", filename: pdf.name, file_data: pdf.data });
  for (const im of images) content.push({ type: "input_image", image_url: im, detail: "auto" });
  if (video?.frames.length) {
    content.push({ type: "input_text", text: `Video "${video.name}"${video.duration ? ` (${Math.round(video.duration)} s)` : ""}: ${video.frames.length} frames sampled evenly, in order:` });
    for (const f of video.frames) content.push({ type: "input_image", image_url: f, detail: "low" });
  }
  content.push({ type: "input_text", text: (chat ? "User: " : "User's question: ") + prompt });

  const rr = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: { Authorization: `Bearer ${oa}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, instructions: chat ? CHAT_INSTRUCTIONS : INSTRUCTIONS, input: [{ role: "user", content }], max_output_tokens: chat ? 300 : 500 }),
  });
  const raw = await rr.json().catch(() => ({}));
  if (!rr.ok) return json({ error: "attachment reading failed", detail: raw?.error?.message || raw }, 502);

  let reply = typeof raw.output_text === "string" ? raw.output_text : "";
  if (!reply && Array.isArray(raw.output)) {
    for (const o of raw.output) for (const c of (o?.content || [])) if (c?.type === "output_text" && c.text) reply += c.text;
  }
  reply = reply.trim();
  if (!reply) return json({ error: "no reply returned" }, 502);
  return json({
    status: "ok", mode: chat ? "chat" : "attachments", model, reply,
    counts: { images: images.length, video_frames: video?.frames.length || 0, pdf: pdf ? 1 : 0, texts: texts.length },
  });
});
