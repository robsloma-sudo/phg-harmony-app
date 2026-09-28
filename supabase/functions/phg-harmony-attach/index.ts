import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

/* PHG HARMONY ATTACH — answer a prompt about attached photos, video, PDFs or
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
  if (!images.length && !video?.frames.length && !pdf && !texts.length) return json({ error: "no readable attachment" }, 400);

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
  content.push({ type: "input_text", text: "User's question: " + prompt });

  const rr = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: { Authorization: `Bearer ${oa}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, instructions: INSTRUCTIONS, input: [{ role: "user", content }], max_output_tokens: 500 }),
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
    status: "ok", model, reply,
    counts: { images: images.length, video_frames: video?.frames.length || 0, pdf: pdf ? 1 : 0, texts: texts.length },
  });
});
