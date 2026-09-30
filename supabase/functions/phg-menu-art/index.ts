import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

/* PHG MENU ART — the painted layer of a Harmony menu design.

   Returns one image with NO text in it. Every name, price and ingredient is
   typeset by the app on top of this image, so the model can never misspell
   or invent menu content. Uses the same OPENAI_API_KEY secret as
   phg-speech-generate / phg-speech-transcribe. One image per call; the app
   only calls this when the user asks Harmony to paint. */

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (x: unknown, s = 200) =>
  new Response(JSON.stringify(x), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

const NO_TEXT =
  " Absolutely no text, letters, numbers, words, signage, labels, menus, logos or typography anywhere in the image.";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST required" }, 405);

  const url = Deno.env.get("SUPABASE_URL");
  const anon = Deno.env.get("SUPABASE_ANON_KEY");
  const oa = Deno.env.get("OPENAI_API_KEY");
  const model = Deno.env.get("OPENAI_IMAGE_MODEL") || "gpt-image-1";
  if (!url || !anon || !oa) return json({ error: "runtime configuration missing" }, 500);

  const auth = req.headers.get("Authorization") || "";
  if (!auth.toLowerCase().startsWith("bearer ")) return json({ error: "login required" }, 401);
  const sb = createClient(url, anon, { auth: { persistSession: false }, global: { headers: { Authorization: auth } } });
  const { data: ud, error: ue } = await sb.auth.getUser(auth.slice(7).trim());
  if (ue || !ud?.user) return json({ error: "invalid or expired login" }, 401);

  const b = await req.json().catch(() => ({}));
  let prompt = String(b.prompt || "").trim();
  if (!prompt) return json({ error: "prompt required" }, 400);
  if (prompt.length > 1800) prompt = prompt.slice(0, 1800);
  const size = ["1024x1536", "1536x1024", "1024x1024"].includes(String(b.size)) ? String(b.size) : "1024x1536";
  const quality = ["low", "medium", "high"].includes(String(b.quality)) ? String(b.quality) : "medium";

  /* Reference photos (up to 4 data: URLs from the app) go to the edits
     endpoint as image inputs; without them this is a plain generation. */
  const refs: string[] = Array.isArray(b.refs) ? b.refs.filter((x: unknown) => typeof x === "string" && /^data:image\/(jpeg|png|webp);base64,/.test(x as string)).slice(0, 4) : [];
  let rr: Response;
  if (refs.length) {
    const form = new FormData();
    form.append("model", model);
    form.append("prompt", prompt + " Use the attached reference photos for subject, palette, materials and mood; do not copy any text, labels or logos from them." + NO_TEXT);
    form.append("size", size);
    form.append("quality", quality);
    form.append("n", "1");
    form.append("output_format", "jpeg");
    form.append("output_compression", "88");
    refs.forEach((d, i) => {
      const m = d.match(/^data:(image\/[a-z]+);base64,(.*)$/)!;
      const bin = Uint8Array.from(atob(m[2]), (c) => c.charCodeAt(0));
      if (bin.byteLength <= 8 * 1024 * 1024) form.append("image[]", new Blob([bin], { type: m[1] }), `ref${i}.${m[1].split("/")[1]}`);
    });
    rr = await fetch("https://api.openai.com/v1/images/edits", { method: "POST", headers: { Authorization: `Bearer ${oa}` }, body: form });
  } else {
    rr = await fetch("https://api.openai.com/v1/images/generations", {
      method: "POST",
      headers: { Authorization: `Bearer ${oa}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model, prompt: prompt + NO_TEXT, size, quality, n: 1, output_format: "jpeg", output_compression: 88 }),
    });
  }
  const raw = await rr.json().catch(() => ({}));
  if (!rr.ok) return json({ error: "image generation failed", detail: raw?.error?.message || raw }, 502);
  const b64 = raw?.data?.[0]?.b64_json;
  if (!b64) return json({ error: "no image returned" }, 502);
  return json({ status: "ok", model, size, quality, refs: refs.length, image: "data:image/jpeg;base64," + b64 });
});
