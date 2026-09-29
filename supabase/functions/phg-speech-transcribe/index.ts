import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type, x-audio-filename, x-context, x-account",
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


/* ---------------- name repair (v4) ---------------- */
type Entry={name:string;kind:string;cat:string;k:string;sk:string};
const LEX:{entries:Entry[];grams:Map<string,number[]>;exact:Map<string,number>;at:number;loading:Promise<void>|null}={entries:[],grams:new Map(),exact:new Map(),at:0,loading:null};
const LETTER:Record<string,string>={a:"ei",b:"bi",c:"si",d:"di",e:"i",f:"ef",g:"yi",h:"eich",i:"ai",j:"yei",k:"kei",l:"el",m:"em",n:"en",o:"o",p:"pi",q:"kiu",r:"ar",s:"es",t:"ti",u:"iu",v:"bi",w:"dabeliu",x:"eks",y:"uai",z:"si"};
const STOP=new Set("a an the and or of to in on at for with from by is it its i me my we our you your he she they them this that these those what which who how when where why do does did can could would should will shall be been being am are was were have has had not no yes yeah okay ok so just please want need give show tell find get make let lets like one two three some any all more most much many menu menus drink drinks cocktail cocktails recipe price prices bar bars city about near best new old good bottle bottles shot neat rocks up".split(" "));
const norm=(s:string)=>s.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/&/g," and ").replace(/[^a-z0-9 ]+/g," ").replace(/\s+/g," ").trim();
/* a cross-language sound key: the same key for how a name is spelled in Spanish, French, Italian... and how an
   English speech engine tends to write it */
const UNITS:Record<string,number>={zero:0,one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10,eleven:11,twelve:12,thirteen:13,fourteen:14,fifteen:15,sixteen:16,seventeen:17,eighteen:18,nineteen:19};
const TENS:Record<string,number>={twenty:20,thirty:30,forty:40,fifty:50,sixty:60,seventy:70,eighty:80,ninety:90};
/* spoken numbers to digits ("forty seven" -> 47), so "Monkey forty seven" meets "Monkey 47" */
function digits(s:string){
  const w=s.split(" ");const out:string[]=[];
  for(let i=0;i<w.length;i++){
    if(TENS[w[i]]!=null){const u=UNITS[w[i+1]];if(u!=null&&u<10){out.push(String(TENS[w[i]]+u));i++;}else out.push(String(TENS[w[i]]));}
    else if(UNITS[w[i]]!=null&&w[i]!=="one")out.push(String(UNITS[w[i]]));else out.push(w[i]);
  }
  return out.join(" ");
}
function soundKey(s:string){
  /* per word first, so word endings are known ("key" sounds like "ki") */
  const w=digits(norm(s)).split(" ").map((x)=>x.replace(/ee|ea/g,"i").replace(/oo/g,"u").replace(/(ey|ie|y)$/,"i").replace(/ooh$|oh$/,"o"));
  let x=w.join("");
  x=x.replace(/cch/g,"k").replace(/sch|sh|ch/g,"X").replace(/ph/g,"f").replace(/gh/g,"g").replace(/qu/g,"k").replace(/gu(?=[ei])/g,"g")
     .replace(/eaux?|aux?/g,"o").replace(/ou/g,"u").replace(/oi/g,"ua").replace(/ai|ei|ay|ey/g,"e")
     .replace(/c(?=[eiy])/g,"s").replace(/ck|c|q/g,"k").replace(/z/g,"s").replace(/x/g,"s").replace(/v/g,"b").replace(/w/g,"u")
     .replace(/j/g,"h").replace(/h/g,"").replace(/y/g,"i").replace(/X/g,"x")
     /* vowels are the least reliable part of a foreign name heard in English: e~i, o~u */
     .replace(/e/g,"i").replace(/o/g,"u").replace(/(.)\1+/g,"$1");
  return x;
}
const skel=(k:string)=>k.replace(/x/g,"s").replace(/[aeiou]+/g,"").replace(/(.)\1+/g,"$1");
function bigrams(s:string){const m=new Map<string,number>();for(let i=0;i<s.length-1;i++){const g=s.slice(i,i+2);m.set(g,(m.get(g)||0)+1);}return m;}
function dice(a:string,b:string){if(a===b)return 1;if(a.length<2||b.length<2)return 0;const A=bigrams(a),B=bigrams(b);let n=0;A.forEach((c,g)=>{n+=Math.min(c,B.get(g)||0);});return 2*n/(a.length-1+b.length-1);}
function trigrams(s:string){const out=new Set<string>();const t="^"+s+"$";for(let i=0;i<t.length-2;i++)out.add(t.slice(i,i+3));return out;}
const LEGAL=/,?\s+(s\.?\s?a\.?(\s?p\.?\s?i\.?)?|s\.?\s?de\s+r\.?\s?l\.?|s\.?\s?c\.?|llc|inc\.?|ltd\.?|co\.?)(\s+de\s+c\.?\s?v\.?)?\.?\s*$/i;

async function loadLexicon(db:any){
  const rows=async(table:string,cols:string,total:number,filter?:(q:any)=>any)=>{
    const col=cols.split(",")[0];
    const out:any[]=[];const n=Math.ceil(total/1000);
    for(let i=0;i<n;i+=8){
      const batch=await Promise.all(Array.from({length:Math.min(8,n-i)},(_,j)=>{let q=db.from(table).select(cols).order(col).range((i+j)*1000,(i+j)*1000+999);if(filter)q=filter(q);return q;}));
      let got=0;for(const r of batch){(r.data||[]).forEach((x:any)=>{if(x[col])out.push(x);});got+=(r.data||[]).length;}
      if(got<Math.min(8,n-i)*1000)break;
    }
    return out;
  };
  const pages=async(table:string,col:string,total:number,filter?:(q:any)=>any)=>(await rows(table,col,total,filter)).map((x:any)=>String(x[col]));
  /* v5: + every brand name in US label approvals (view v_harmony_brand_names, service_role only). Pages are ordered
     so paging is stable. */
  const [brands,menuBrands,cocktails,terms,orgs,venues,labelBrands]=await Promise.all([
    pages("brands","brand_name",3000),
    pages("menu_item_brands","raw_brand_text",60000,(q:any)=>q.not("raw_brand_text","is",null)),
    pages("cocktail_reference","cocktail_name",1000),
    pages("spirit_lexicon","term",1000),
    pages("organizations","organization_name",2000,(q:any)=>q.not("nom","is",null)),
    pages("mv_dash_pins","venue",40000),
    rows("v_harmony_brand_names","name,category",20000),
  ]);
  const entries:Entry[]=[];const seen=new Set<string>();
  const add=(name:string,kind:string,cat="")=>{name=name.replace(LEGAL,"").replace(/\s+/g," ").trim();const nn=norm(name);if(nn.length<3||seen.has(kind+"|"+nn)||/^\d+$/.test(nn))return;seen.add(kind+"|"+nn);const k=soundKey(name);if(k.length<3)return;entries.push({name:/^[A-Z0-9 .,'&-]+$/.test(name)&&name.length>4?name.toLowerCase().replace(/(^|[\s'-])([a-z])/g,(_a,p,c)=>p+c.toUpperCase()):name,kind,cat,k,sk:skel(k)});};
  cocktails.forEach((x)=>add(x,"cocktail"));brands.forEach((x)=>add(x,"brand","tequila"));
  const mc=new Map<string,number>();menuBrands.forEach((x)=>{const n=norm(x);mc.set(n,(mc.get(n)||0)+1);});
  const firstSpelling=new Map<string,string>();menuBrands.forEach((x)=>{const n=norm(x);if(!firstSpelling.has(n))firstSpelling.set(n,x);});
  mc.forEach((c,n)=>{if(c>=2)add(firstSpelling.get(n)||n,"brand");});
  labelBrands.forEach((x:any)=>add(String(x.name),"brand",String(x.category||"")));
  orgs.forEach((x)=>add(x,"producer","tequila"));terms.forEach((x)=>add(x,"term"));venues.forEach((x)=>add(x,"venue"));
  const grams=new Map<string,number[]>(),exact=new Map<string,number>();
  entries.forEach((e,i)=>{exact.set(norm(e.name),i);trigrams(e.k).forEach((g)=>{let a=grams.get(g);if(!a){a=[];grams.set(g,a);}a.push(i);});});
  LEX.entries=entries;LEX.grams=grams;LEX.exact=exact;LEX.at=Date.now();
  console.log(JSON.stringify({lexicon:entries.length,brands:brands.length,menu_brands:menuBrands.length,label_brands:labelBrands.length,venues:venues.length}));
}
function lexiconReady(db:any,waitMs:number){
  if(LEX.entries.length&&Date.now()-LEX.at<6*3600e3)return Promise.resolve(true);
  if(!LEX.loading){LEX.loading=loadLexicon(db).catch((e)=>console.log(JSON.stringify({lexicon_error:String(e)}))).finally(()=>{LEX.loading=null;});
    try{(globalThis as any).EdgeRuntime?.waitUntil?.(LEX.loading);}catch{/* ignore */}}
  return Promise.race([LEX.loading.then(()=>LEX.entries.length>0),new Promise<boolean>((r)=>setTimeout(()=>r(LEX.entries.length>0),waitMs))]);
}

/* v6: CONTEXT. Words around a heard phrase say what it is: "a bottle of ___", "___ reposado", "___ 12 year",
   "tequila", "scotch", "gin"... A phrase in a brand slot or next to a spirit word is matched more readily, and brands
   of that spirit are preferred. The conversation so far counts as weaker context. */
const CAT_CUES:[RegExp,string][]=[
  [/^(mezcal|mezcales|mescal|espadin|tobala|ensamble|pechuga|ancestral|tepextate|arroqueno)$/,"mezcal"],
  [/^(tequila|tequilas|blanco|plata|reposado|reposados|anejo|anejos|cristalino|highland|lowland|nom)$/,"tequila"],
  [/^(whiskey|whiskeys|whisky|whiskies|bourbon|bourbons|rye|scotch|malt|islay|speyside|highlands|cask|year|years|yr)$/,"whiskey"],
  [/^(vodka|vodkas)$/,"vodka"],[/^(gin|gins|genever|london)$/,"gin"],
  [/^(rum|rums|rhum|agricole|cachaca)$/,"rum"],
  [/^(brandy|cognac|armagnac|vsop|xo|pisco|grappa|calvados)$/,"brandy"],
  [/^(liqueur|liqueurs|amaro|amari|aperitivo|aperitif|vermouth|bitter|bitters|digestivo|fernet|cordial)$/,"liqueur"],
];
const SLOT=new Set("of pour pours bottle bottles case cases shot shots order carry stock price cost brand brands sell using with add try need want some the our their".split(" "));
function catOf(words:string[]){for(const w of words){const n=norm(w);for(const [re,c] of CAT_CUES)if(re.test(n))return c;}return "";}
let CTX_HINT="";

function candidates(text:string){
  const words=text.split(/\s+/).filter(Boolean);
  const spans:{from:number;to:number;heard:string;k:string;sk:string;cat:string;slot:boolean}[]=[];
  /* names already heard right are protected, longest first ("East and Co", "Black Manhattan") */
  const safe=new Array(words.length).fill(false);
  for(let n=6;n>=1;n--)for(let i=0;i+n<=words.length;i++){
    if(safe.slice(i,i+n).some(Boolean))continue;
    const nn=norm(words.slice(i,i+n).join(" "));
    if(!(nn.length>=4&&LEX.exact.has(nn)&&!(n===1&&STOP.has(nn))))continue;
    /* a single short word, or a brand of another spirit than the one being talked about, may still be part of a
       longer misheard name ("Nick a 12 year" is Nikka, not the vodka Nick) */
    if(n===1){const e=LEX.entries[LEX.exact.get(nn)!];const c=catOf([...words.slice(Math.max(0,i-3),i),...words.slice(i+1,i+4)]);
      if(nn.length<6||(c&&e.cat&&e.cat!==c))continue;}
    for(let j=i;j<i+n;j++)safe[j]=true;
  }
  for(let i=0;i<words.length;i++)for(let n=1;n<=5&&i+n<=words.length;n++){
    if(safe.slice(i,i+n).some(Boolean))continue;
    const ws=words.slice(i,i+n);const plain=ws.map((w)=>norm(w)).filter(Boolean);
    /* at least one real word; small words at the edges are allowed ("a rhett" = Arette, "CT leg was") */
    if(!plain.some((w)=>w.length>=3&&!STOP.has(w)&&!SLOT.has(w)))continue;
    const heard=ws.join(" ").replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu,"");
    const variants=[heard];
    /* spelled-out letters: "CT" is how "Siete" can come back */
    if(ws.some((w)=>/^[A-Z]{2,3}$/.test(w.replace(/[^A-Za-z]/g,""))))variants.push(ws.map((w)=>{const l=w.replace(/[^A-Za-z]/g,"");return /^[A-Z]{2,3}$/.test(l)?l.toLowerCase().split("").map((c)=>LETTER[c]||c).join(""):w;}).join(" "));
    const around=[...words.slice(Math.max(0,i-3),i),...words.slice(i+n,i+n+3)];
    const cat=catOf(around)||catOf(CTX_HINT.split(/\s+/).slice(-40));
    const slot=SLOT.has(norm(words[i-1]||""))||!!catOf(words.slice(i+n,i+n+2));
    for(const v of variants){const k=soundKey(v);if(k.length>=4)spans.push({from:i,to:i+n,heard,k,sk:skel(k),cat,slot});}
  }
  const found:{from:number;to:number;heard:string;score:number;cat:string;slot:boolean;options:{name:string;kind:string;cat:string;score:number}[]}[]=[];
  for(const sp of spans){
    if(LEX.exact.has(norm(sp.heard)))continue;
    const cnt=new Map<number,number>();const tg=trigrams(sp.k);
    tg.forEach((g)=>{const a=LEX.grams.get(g);if(a&&a.length<6000)a.forEach((i)=>cnt.set(i,(cnt.get(i)||0)+1));});
    const need=Math.max(2,Math.floor(tg.size*0.3));
    const opts:{name:string;kind:string;cat:string;score:number}[]=[];
    const min=sp.slot||sp.cat?0.64:0.72;
    cnt.forEach((c,i)=>{if(c<need)return;const e=LEX.entries[i];if(Math.abs(e.k.length-sp.k.length)>Math.max(3,sp.k.length*0.45))return;
      const w=e.sk.length>=4?0.45:e.sk.length===3||(e.sk.length===2&&e.k.length>=4)?0.3:0;let sc=(1-w)*dice(sp.k,e.k)+w*dice(sp.sk,e.sk);
      if(sp.cat&&e.cat){sc+=e.cat===sp.cat?0.08:(sp.cat+e.cat).match(/^(tequilamezcal|mezcaltequila)$/)?0.03:-0.05;}
      sc=Math.min(1,sc);if(sc>=min)opts.push({name:e.name,kind:e.kind,cat:e.cat,score:Math.round(sc*100)/100});});
    if(!opts.length)continue;
    opts.sort((a,b)=>b.score-a.score);
    const uniq:typeof opts=[];opts.forEach((o)=>{if(!uniq.some((u)=>norm(u.name)===norm(o.name)))uniq.push(o);});
    const hn=norm(sp.heard),on=norm(uniq[0].name);
    if(on===hn||on+"s"===hn||on+"es"===hn)continue; /* already right, or just the plural */
    const prev=found.find((f)=>f.from===sp.from&&f.to===sp.to);
    if(prev){if(uniq[0].score>prev.score){prev.score=uniq[0].score;prev.options=uniq.slice(0,4);}continue;}
    found.push({from:sp.from,to:sp.to,heard:sp.heard,score:uniq[0].score,cat:sp.cat,slot:sp.slot,options:uniq.slice(0,4)});
  }
  /* keep the strongest non-overlapping spans, longer spans win ties */
  found.sort((a,b)=>b.score-a.score||(b.to-b.from)-(a.to-a.from));
  const keep:typeof found=[];
  for(const f of found){if(keep.some((k)=>f.from<k.to&&k.from<f.to))continue;keep.push(f);if(keep.length>=6)break;}
  return {words,spans:keep};
}

async function repairNames(heard:string,hint:string,oa:string,user:string,account:string|null){
  const url=Deno.env.get("SUPABASE_URL")!,svc=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!svc)return {text:heard,fixes:[],unsure:[]};
  const db=createClient(url,svc,{auth:{persistSession:false}});
  let text=heard;const fixes:any[]=[];
  /* 1. what this user already taught Harmony ("no, I said ...") */
  try{
    const {data}=await db.rpc("phg_harmony_inbox_db",{p_op:"aliases_list",p_args:{user,account}});
    for(const a of (Array.isArray(data)?data:[])){
      const h=String(a.heard||"").trim();if(h.length<2||!a.means)continue;
      const re=new RegExp("(^|[^\\p{L}\\p{N}])("+h.replace(/[.*+?^${}()|[\]\\]/g,"\\$&").replace(/\s+/g,"\\s+")+")(?=$|[^\\p{L}\\p{N}])","giu");
      if(re.test(text)){text=text.replace(re,(_m,p)=>p+a.means);fixes.push({heard:h,meant:a.means,kind:a.kind,why:"learned"});}
    }
  }catch{/* aliases are optional */}
  /* 2. sound-alike names, read in context */
  if(!(await lexiconReady(db,1500)))return {text,fixes,unsure:[]};
  CTX_HINT=hint.slice(-400);
  const {words,spans}=candidates(text);
  if(!spans.length)return {text,fixes,unsure:[]};
  let decisions:any[]|null=null;
  try{
    const ctl=new AbortController();const tm=setTimeout(()=>ctl.abort(),2500);
    const r=await fetch("https://api.openai.com/v1/responses",{method:"POST",signal:ctl.signal,headers:{Authorization:`Bearer ${oa}`,"Content-Type":"application/json"},body:JSON.stringify({
      model:Deno.env.get("OPENAI_REPAIR_MODEL")||"gpt-4.1-mini",max_output_tokens:300,
      instructions:"A speech engine transcribed a bar owner. Brand, producer, cocktail and venue names in Spanish, French, Italian, Japanese and other languages often come out as English sound-alikes. For each heard phrase you get PHG's closest real names (with their spirit category) and the context: the spirit being talked about and whether the phrase sits where a brand name goes ('a bottle of ___', '___ reposado'). If the heard words are not letter for letter a real name, pick the name whose SOUND matches and that fits the context (a phrase next to 'reposado' is a tequila brand, next to '12 year' or 'scotch' a whisky). Pick keep when the heard words are ordinary words that make sense as said, or you can't tell. sure=false when two options are about equally likely or the fit is weak.",
      input:JSON.stringify({transcript:text,conversation:hint.slice(-500),heard:spans.map((s,i)=>({i,heard:s.heard,context_spirit:s.cat||null,brand_slot:s.slot,options:s.options.map((o)=>o.name+" ("+o.kind+(o.cat?", "+o.cat:"")+")")}))}),
      text:{format:{type:"json_schema",name:"name_repair",strict:true,schema:{type:"object",additionalProperties:false,required:["picks"],properties:{picks:{type:"array",items:{type:"object",additionalProperties:false,required:["i","pick","sure"],properties:{i:{type:"integer"},pick:{type:"string",description:"one option's name exactly, or keep"},sure:{type:"boolean"}}}}}}}},
    })});
    clearTimeout(tm);
    const j=await r.json().catch(()=>({}));
    let t=typeof j.output_text==="string"?j.output_text:"";
    if(!t&&Array.isArray(j.output))for(const o of j.output)for(const c of (o?.content||[]))if(c?.type==="output_text")t+=c.text||"";
    decisions=JSON.parse(t).picks;
  }catch{decisions=null;}
  const unsure:any[]=[];const repl=new Map<number,{to:number;name:string}>();
  spans.forEach((s,i)=>{
    const d=decisions?decisions.find((x:any)=>x.i===i):null;
    const pk=d?String(d.pick||"").replace(/\s*\([^)]*\)\s*$/,"").trim().toLowerCase():"";
    /* without the model's check, only swap clear multi-word sound-alikes (never a single ordinary word) */
    const clear=s.options.length===1||s.options[0].score-s.options[1].score>=0.08;
    /* a single word is swapped without the model only when the context backs it: a brand slot and the same spirit */
    const ctxOk=(s.to-s.from>=2)||((s.slot||!!s.cat)&&!!s.cat&&s.options[0].cat===s.cat);
    const opt=d?s.options.find((o)=>o.name.toLowerCase()===pk):(ctxOk&&s.score>=0.9&&clear?s.options[0]:null);
    if(opt&&(!d||d.sure)){repl.set(s.from,{to:s.to,name:opt.name});fixes.push({heard:s.heard,meant:opt.name,kind:opt.kind,why:"sounds like"});}
    else if(opt||((s.to-s.from>=2||s.slot||!!s.cat)&&s.score>=0.85))unsure.push({heard:s.heard,options:s.options.map((o)=>o.name)});
  });
  if(repl.size){
    const outw:string[]=[];
    for(let i=0;i<words.length;){const r=repl.get(i);if(r){const tail=(words[r.to-1].match(/[^\p{L}\p{N}]+$/u)||[""])[0];outw.push(r.name+tail);i=r.to;}else{outw.push(words[i]);i++;}}
    text=outw.join(" ");
  }
  return {text,fixes,unsure};
}

Deno.serve(async(req)=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL");
  const anon=Deno.env.get("SUPABASE_ANON_KEY");
  const oa=Deno.env.get("OPENAI_API_KEY");
  const model=Deno.env.get("OPENAI_TRANSCRIBE_MODEL")||"gpt-transcribe";
  if(!url||!anon||!oa)return out({error:"runtime configuration missing"},500);

  /* v4: text-only name repair for other PHG functions (the iPhone Shortcut's dictated text goes through
     phg-harmony-inbox, not through this transcriber). Server-to-server only: proven with the service-role key. */
  const svcKey=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")||"";
  if(svcKey&&(req.headers.get("x-phg-internal")||"")===svcKey){
    const b=await req.json().catch(()=>({}));
    const t=String(b.text||"").trim().slice(0,2000);
    if(!t||!b.user)return out({error:"text and user required"},400);
    try{const r=await repairNames(t,String(b.hint||""),oa,String(b.user),b.account?String(b.account):null);return out({status:"ok",text:r.text,heard:t,fixes:r.fixes,unsure:r.unsure});}
    catch(e){return out({status:"ok",text:t,heard:t,fixes:[],unsure:[],error:String(e)});}
  }

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
  /* names in other languages keep their own spelling */
  const LANG="Bar and restaurant talk in American English that often includes spirit brands, producers, cocktails and places in Spanish, French, Italian, Japanese, Portuguese, German or Gaelic; write those names in their original spelling with accents (Siete Leguas, Fortaleza, Cointreau, Amaro Nonino, Nikka, Laphroaig). ";
  hint=(LANG+hint).slice(0,1000);
  form.append("prompt",hint);

  let rr=await fetch("https://api.openai.com/v1/audio/transcriptions",{
    method:"POST",
    headers:{Authorization:`Bearer ${oa}`},
    body:form
  });
  /* safety net: if the hint is ever refused, transcribe without it */
  if(!rr.ok){form.delete("prompt");rr=await fetch("https://api.openai.com/v1/audio/transcriptions",{method:"POST",headers:{Authorization:`Bearer ${oa}`},body:form});}
  const raw=await rr.json().catch(()=>({}));
  if(!rr.ok)return out({error:"transcription failed",detail:raw?.error?.message||raw},502);

  const heardRaw=String(raw?.text||"").trim();
  if(!heardRaw)return out({error:"no speech detected"},422);
  /* v4 (2026-09-29): NAME REPAIR. Brand, producer, cocktail and venue names from many languages
     (Spanish, French, Italian, Japanese, Portuguese...) are often written as English sound-alikes
     ("CT leg was" for Siete Leguas, "quantro" for Cointreau). The words heard are checked against
     PHG's own names with a cross-language sound key; a small model confirms each swap in context.
     Learned aliases (things the user corrected before) win first. Never blocks: on any failure the
     transcript is returned as heard. */
  let text=heardRaw,fixes:any[]=[],unsure:any[]=[];
  try{
    const acct=(req.headers.get("x-account")||"").trim();
    const r=await repairNames(heardRaw,hint,oa,userData.user.id,/^[0-9a-f-]{36}$/i.test(acct)?acct:null);
    text=r.text;fixes=r.fixes;unsure=r.unsure;
  }catch(e){console.log(JSON.stringify({repair_error:String(e)}));}
  return out({status:"ok",text,heard:heardRaw,fixes,unsure,model,bytes:bytes.byteLength,transcribed_at:new Date().toISOString()});
});
