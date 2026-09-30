import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS",
  "Access-Control-Expose-Headers":"Content-Type, X-PHG-Voice, X-PHG-Model"
};
const json=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});

const VOICES=new Set(["alloy","ash","ballad","coral","echo","fable","onyx","nova","sage","shimmer","verse","marin","cedar"]);

Deno.serve(async(req)=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return json({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL");
  const anon=Deno.env.get("SUPABASE_ANON_KEY");
  const oa=Deno.env.get("OPENAI_API_KEY");
  const model=Deno.env.get("OPENAI_TTS_MODEL")||"gpt-4o-mini-tts";
  if(!url||!anon||!oa)return json({error:"runtime configuration missing"},500);

  const auth=req.headers.get("Authorization")||"";
  if(!auth.toLowerCase().startsWith("bearer "))return json({error:"login required"},401);
  const b=await req.json().catch(()=>({}));
  /* v3 SPEED: the app wakes this function when the mic opens, so the first reply does not pay the start-up time */
  if(b.warm)return json({ok:true,warm:true});
  /* v3 SPEED: the login is checked while the voice is being generated (the gateway already verified the JWT's
     signature, verify_jwt=true); no audio is returned unless the check passes. */
  const jwt=auth.slice(7).trim();
  const sb=createClient(url,anon,{auth:{persistSession:false},global:{headers:{Authorization:auth}}});
  const authP=sb.auth.getUser(jwt).then(({data,error})=>!error&&!!data?.user).catch(()=>false);

  const input=String(b.text||b.input||"").trim();
  if(!input)return json({error:"text required"},400);
  if(input.length>4096)return json({error:"text too long","max_chars":4096},400);

  const voice=String(b.voice||"marin").toLowerCase();
  if(!VOICES.has(voice))return json({error:"unsupported voice"},400);

  let speed=Number(b.speed==null?1:b.speed);
  if(!Number.isFinite(speed))speed=1;
  speed=Math.max(.25,Math.min(4,speed));

  let instructions=String(b.instructions||"").trim();
  if(instructions.length>3500)instructions=instructions.slice(0,3500);

  const rrP=fetch("https://api.openai.com/v1/audio/speech",{
    method:"POST",
    headers:{
      Authorization:`Bearer ${oa}`,
      "Content-Type":"application/json"
    },
    body:JSON.stringify({
      model,
      voice,
      input,
      instructions:instructions||undefined,
      speed,
      response_format:"mp3",
      stream_format:"audio"
    })
  });
  const [authed,rr]=await Promise.all([authP,rrP]);
  if(!authed){try{await rr.body?.cancel();}catch{}return json({error:"invalid or expired login"},401);}

  if(!rr.ok){
    const raw=await rr.json().catch(async()=>({message:await rr.text().catch(()=>(""))}));
    return json({error:"speech generation failed",detail:raw?.error?.message||raw?.message||raw},502);
  }

  /* v3 SPEED: stream the audio through instead of holding it until the last byte */
  return new Response(rr.body,{
    status:200,
    headers:{
      ...cors,
      "Content-Type":"audio/mpeg",
      "Cache-Control":"no-store",
      "X-PHG-Voice":voice,
      "X-PHG-Model":model
    }
  });
});