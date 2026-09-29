import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type, x-audio-filename, x-context",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});

function extFor(mime:string){
  mime=String(mime||"").toLowerCase();
  if(mime.includes("mp4")||mime.includes("m4a"))return "m4a";
  if(mime.includes("mpeg")||mime.includes("mp3"))return "mp3";
  if(mime.includes("wav"))return "wav";
  if(mime.includes("ogg"))return "ogg";
  if(mime.includes("webm"))return "webm";
  return "audio";
}

Deno.serve(async(req)=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL");
  const anon=Deno.env.get("SUPABASE_ANON_KEY");
  const oa=Deno.env.get("OPENAI_API_KEY");
  const model=Deno.env.get("OPENAI_TRANSCRIBE_MODEL")||"gpt-transcribe";
  if(!url||!anon||!oa)return out({error:"runtime configuration missing"},500);

  const auth=req.headers.get("Authorization")||"";
  if(!auth.toLowerCase().startsWith("bearer "))return out({error:"login required"},401);
  const jwt=auth.slice(7).trim();
  const sb=createClient(url,anon,{auth:{persistSession:false},global:{headers:{Authorization:auth}}});
  const {data:userData,error:userErr}=await sb.auth.getUser(jwt);
  if(userErr||!userData?.user)return out({error:"invalid or expired login"},401);

  const mime=(req.headers.get("Content-Type")||"application/octet-stream").split(";")[0].trim();
  if(!/^(audio|video)\//i.test(mime))return out({error:"audio content required"},415);
  const bytes=await req.arrayBuffer();
  if(!bytes.byteLength)return out({error:"empty audio"},400);
  if(bytes.byteLength>20*1024*1024)return out({error:"audio too large"},413);

  const filename=(req.headers.get("x-audio-filename")||("harmony."+extFor(mime))).replace(/[^a-zA-Z0-9._-]/g,"_");
  const form=new FormData();
  form.append("model",model);
  form.append("file",new Blob([bytes],{type:mime}),filename);
  form.append("response_format","json");
  /* 2026-09-29: hearing in context. The app sends what is being talked about (last lines of the conversation,
     names on screen, the business's own words) as a hint, so names and bar terms are heard right
     ("East & Co", not "Easton Co"). URL-encoded header, capped. */
  let hint="";
  try{hint=decodeURIComponent(req.headers.get("x-context")||"").replace(/\s+/g," ").trim().slice(0,900);}catch{hint="";}
  if(hint)form.append("prompt",hint);

  let rr=await fetch("https://api.openai.com/v1/audio/transcriptions",{
    method:"POST",
    headers:{Authorization:`Bearer ${oa}`},
    body:form
  });
  /* safety net: if the hint is ever refused, transcribe without it */
  if(!rr.ok&&hint){form.delete("prompt");rr=await fetch("https://api.openai.com/v1/audio/transcriptions",{method:"POST",headers:{Authorization:`Bearer ${oa}`},body:form});}
  const raw=await rr.json().catch(()=>({}));
  if(!rr.ok)return out({error:"transcription failed",detail:raw?.error?.message||raw},502);

  const text=String(raw?.text||"").trim();
  if(!text)return out({error:"no speech detected"},422);
  return out({status:"ok",text,model,bytes:bytes.byteLength,transcribed_at:new Date().toISOString()});
});