import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json","Cache-Control":"no-store"}});
const slug=(x:any)=>String(x||"menu").toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"").slice(0,72)||"menu";
const clone=(x:any)=>JSON.parse(JSON.stringify(x==null?null:x));

function countItems(doc:any){
  let n=0;
  for(const sec of (doc?.sections||[])){
    n+=(sec?.items||[]).length;
    for(const sub of (sec?.subs||[]))n+=(sub?.items||[]).length;
  }
  return n;
}
function countSections(doc:any){
  let n=0;
  for(const sec of (doc?.sections||[])){
    n+=1+(sec?.subs||[]).length;
  }
  return n;
}
function targetObject(rows:any[]){
  return Object.fromEntries((rows||[]).map((t:any)=>[
    t.target_key,{enabled:!!t.enabled,settings:t.settings||{}}
  ]));
}
function itemKey(it:any,sec:any,sub:any){
  return String(it?.id||it?.phg?.menu_item_id||
    [sec?.name||"",sub?.name||"",it?.name||""].join("|").toLowerCase());
}
function flattenDoc(doc:any){
  const items=new Map<string,any>(),sections:string[]=[];
  for(const sec of (doc?.sections||[])){
    sections.push(String(sec?.name||"Section"));
    for(const it of (sec?.items||[])){
      items.set(itemKey(it,sec,null),{
        name:it?.name||"",brand:it?.brand||"",desc:it?.desc||"",
        prices:it?.prices||[],section:sec?.name||"",subsection:null,
        recipe_version_id:it?.phg?.recipe_version_id||null
      });
    }
    for(const sub of (sec?.subs||[])){
      sections.push(String(sec?.name||"Section")+" / "+String(sub?.name||"Subsection"));
      for(const it of (sub?.items||[])){
        items.set(itemKey(it,sec,sub),{
          name:it?.name||"",brand:it?.brand||"",desc:it?.desc||"",
          prices:it?.prices||[],section:sec?.name||"",subsection:sub?.name||"",
          recipe_version_id:it?.phg?.recipe_version_id||null
        });
      }
    }
  }
  return {items,sections};
}
function compareDocs(a:any,b:any){
  const A=flattenDoc(a),B=flattenDoc(b),added:any[]=[],removed:any[]=[],changed:any[]=[];
  for(const [k,v] of B.items){
    if(!A.items.has(k))added.push(v);
    else{
      const av=A.items.get(k);
      if(JSON.stringify(av)!==JSON.stringify(v))changed.push({before:av,after:v});
    }
  }
  for(const [k,v] of A.items)if(!B.items.has(k))removed.push(v);
  const aset=new Set(A.sections),bset=new Set(B.sections);
  return {
    added,removed,changed,
    section_added:B.sections.filter((x:string)=>!aset.has(x)),
    section_removed:A.sections.filter((x:string)=>!bset.has(x)),
    summary:{
      items_before:A.items.size,items_after:B.items.size,
      added:added.length,removed:removed.length,changed:changed.length,
      sections_before:A.sections.length,sections_after:B.sections.length
    }
  };
}
function firstPrice(it:any){
  const ps=Array.isArray(it?.prices)?it.prices:[];
  for(const p of ps){const v=Number(p?.value);if(Number.isFinite(v)&&v>=0)return v;}
  return null;
}
function priceOptions(it:any){
  const ps=Array.isArray(it?.prices)?it.prices:[];
  return ps.map((p:any)=>({label:p?.label||null,value:Number(p?.value)})).filter((p:any)=>Number.isFinite(p.value)&&p.value>=0);
}
function publicRules(it:any){
  const v=it?.meta?.public_visibility||{};
  const on=(k:string)=>v[k]===undefined?true:!!v[k];
  return {
    item:on("item"),
    description:on("description"),
    price:on("price"),
    brand:on("brand"),
    ingredients:on("ingredients"),
    house_recipe:on("house_recipe")
  };
}
function publicComponentKey(x:any){
  return String(x?.name||x?.ingredient_name||x?.value||x?.k||"ingredient")
    .toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"");
}
function publicComponentAllowed(it:any,x:any){
  const map=it?.meta?.public_components||{};
  const k=publicComponentKey(x);
  return map[k]===undefined?true:!!map[k];
}
function itemIngredients(it:any,rv:any){
  if(Array.isArray(rv?.ingredients)&&rv.ingredients.length)return rv.ingredients;
  if(Array.isArray(it?.components)&&it.components.length)return it.components;
  if(Array.isArray(it?.ing)&&it.ing.length){
    return it.ing.filter((x:any)=>x?.value).map((x:any)=>({
      name:x.value,quantity:null,unit:null,role:x.k||null,kind:"ingredient",notes:null
    }));
  }
  return [];
}
function ingredientNode(x:any,i:number,parent:string,showAmount=true){
  const prep=!!(x?.prep_recipe_id||x?.kind==="prep"||x?.type==="prep");
  const q=showAmount&&x?.quantity!=null?String(x.quantity):null;
  const u=showAmount&&x?.unit?String(x.unit):"";
  const node:any={
    id:`${parent}-ing-${i}`,
    type:prep?"prep":"ingredient",
    label:String(x?.name||x?.ingredient_name||x?.value||"Ingredient"),
    amount:q?(q+(u?" "+u:"")):null,
    subtitle:x?.role?String(x.role):null,
    body:x?.notes?String(x.notes):null,
    children:[]
  };
  if(Array.isArray(x?.components)){
    node.children=x.components
      .filter((c:any)=>c&&(c.name||c.ingredient_name||c.value))
      .map((c:any,j:number)=>ingredientNode(c,j,node.id,showAmount));
  }
  return node;
}
function itemNode(it:any,sec:any,sub:any,recipes:Map<string,any>){
  const rules=publicRules(it);
  if(!rules.item)return null;

  const rvId=it?.phg?.recipe_version_id||null;
  const rv=rvId?recipes.get(String(rvId)):null;
  const isCocktail=!!(rv?.cocktail_name||rv?.build_family||it?.meta?.canonical||
    String(it?.meta?.identity_class||"").toLowerCase()==="cocktail");
  const id=String(it?.id||it?.phg?.menu_item_id||crypto.randomUUID());
  const ingredients=itemIngredients(it,rv).filter((x:any)=>publicComponentAllowed(it,x));
  const desc=rules.description?String(it?.desc||"").trim():"";
  const brand=rules.brand?String(it?.brand||"").trim():"";

  const node:any={
    id,
    type:isCocktail?"cocktail":"menu_item",
    label:String(it?.name||"Menu item"),
    subtitle:desc||brand||null,
    body:desc||null,
    price:rules.price?firstPrice(it):null,
    price_options:rules.price?priceOptions(it):[],
    detail:{
      brand:brand||null,
      build_family:rv?.build_family||it?.meta?.family||null,
      method:rules.house_recipe?(rv?.method||null):null,
      glassware:rules.house_recipe?(rv?.glassware||null):null,
      garnish:rules.house_recipe?(rv?.garnish||null):null,
      section:sec?.name||null,
      subsection:sub?.name||null,
      house_recipe_public:rules.house_recipe
    },
    source:{
      menu_item_id:it?.phg?.menu_item_id||null,
      recipe_version_id:rvId,
      editor_item_id:it?.id||null
    },
    children:[]
  };

  if(brand){
    node.children.push({
      id:id+"-brand",type:"brand",label:brand,subtitle:"Featured product",children:[]
    });
  }

  if(rules.house_recipe&&(rv||ingredients.length)){
    const recipe:any={
      id:id+"-house-recipe",
      type:"recipe",
      label:"House Recipe",
      subtitle:rv?.method?String(rv.method):"House build",
      body:null,
      detail:{
        method:rv?.method||null,
        glassware:rv?.glassware||null,
        garnish:rv?.garnish||null,
        build_family:rv?.build_family||it?.meta?.family||null
      },
      children:[]
    };
    if(rules.ingredients){
      recipe.children=ingredients.map((x:any,i:number)=>ingredientNode(x,i,recipe.id,true));
    }
    node.children.push(recipe);
  }else if(rules.ingredients){
    node.children.push(...ingredients.map((x:any,i:number)=>ingredientNode(x,i,id,false)));
  }

  return node;
}
function buildTree(doc:any,project:any,version:number,recipes:Map<string,any>){
  const root:any={
    id:"menu-"+String(project.id),
    type:"section",
    label:String(doc?.title||project?.name||"Menu"),
    eyebrow:"PUBLISHED MENU",
    subtitle:String(doc?.subtitle||"").trim()||null,
    description:"Explore the menu by section, item, ingredient and product.",
    publication_version:version,
    children:[]
  };
  for(const sec of (doc?.sections||[])){
    const sn:any={
      id:String(sec?.id||crypto.randomUUID()),
      type:"category",
      label:String(sec?.name||"Section"),
      subtitle:String(sec?.desc||"").trim()||null,
      children:[]
    };
    for(const it of (sec?.items||[])){
      const n=itemNode(it,sec,null,recipes);
      if(n)sn.children.push(n);
    }
    for(const sub of (sec?.subs||[])){
      const subn:any={
        id:String(sub?.id||crypto.randomUUID()),
        type:"category",
        label:String(sub?.name||"Subsection"),
        subtitle:String(sub?.desc||"").trim()||null,
        children:[]
      };
      for(const it of (sub?.items||[])){
        const n=itemNode(it,sec,sub,recipes);
        if(n)subn.children.push(n);
      }
      if(subn.children.length)sn.children.push(subn);
    }
    if(sn.children.length)root.children.push(sn);
  }
  return root;
}
function defaultTargets(sizeKey:string|null,presetKey:string|null){
  return {
    interactive:{enabled:true,settings:{layout:"node_rails",motion:"gentle",depth:"progressive",show_product_education:true,node_shape:"oval",density:"airy"}},
    digital:{enabled:true,settings:{layout:"single_column",show_descriptions:true,show_prices:true,pdf_download:true,page_size:"letter"}},
    print:{enabled:true,settings:{size:sizeKey||"letter_p",preset:presetKey||"house",columns:1,bleed:false,crop_marks:false}},
    display:{enabled:false,settings:{aspect_ratio:"16:9",rotation_seconds:12,transition:"fade"}},
    embed:{enabled:true,settings:{mode:"responsive",header:true,theme:"dark"}}
  };
}

Deno.serve(async(req)=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL");
  const anon=Deno.env.get("SUPABASE_ANON_KEY");
  const service=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!url||!anon||!service)return out({error:"runtime configuration missing"},500);

  const auth=req.headers.get("Authorization")||"";
  if(!auth.toLowerCase().startsWith("bearer "))return out({error:"login required"},401);
  const jwt=auth.slice(7).trim();
  const userClient=createClient(url,anon,{auth:{persistSession:false},global:{headers:{Authorization:auth}}});
  const {data:userData}=await userClient.auth.getUser(jwt);
  const user=userData?.user;
  if(!user)return out({error:"invalid or expired login"},401);

  const b=await req.json().catch(()=>({}));
  const action=String(b.action||"status");
  const pid=String(b.menu_project_id||"");
  const token=String(b.sync_token||"");
  if(!pid||!token)return out({error:"menu_project_id and session token required"},400);

  const sb=createClient(url,service,{auth:{persistSession:false}});
  const {data:ok,error:authErr}=await sb.rpc("phg_menu_authorize",{p_menu_project_id:pid,p_sync_token:token});
  if(authErr||!ok)return out({error:"menu authorization failed"},403);

  const {data:project,error:projectErr}=await sb.schema("phg").from("menu_projects")
    .select("id,name,status,backend_revision,account_id").eq("id",pid).maybeSingle();
  if(projectErr||!project)return out({error:projectErr?.message||"menu project not found"},404);
  const {data:account}=await sb.schema("phg").from("accounts")
    .select("account_key,name").eq("id",project.account_id).maybeSingle();

  async function versionTargets(versionId:string|null){
    if(!versionId)return [];
    const {data:t,error:te}=await sb.schema("phg").from("menu_publication_targets")
      .select("*").eq("publication_version_id",versionId).order("target_key");
    if(te)throw te;
    return t||[];
  }
  async function latest(){
    const {data:v,error:e}=await sb.schema("phg").from("menu_publication_versions")
      .select("*").eq("menu_project_id",pid).order("version",{ascending:false}).limit(1);
    if(e)throw e;
    const row=v?.[0]||null;
    return {version:row,targets:await versionTargets(row?.id||null)};
  }
  async function state(){
    const newest=await latest();
    const {data:pub,error:pe}=await sb.schema("phg").from("public_menu_experiences")
      .select("publication_version_id,menu_key,published")
      .eq("source_menu_project_id",pid).limit(1);
    if(pe)throw pe;
    const liveId=pub?.[0]?.publication_version_id||null;
    let live:any=null;
    if(liveId){
      const {data:l,error:le}=await sb.schema("phg").from("menu_publication_versions")
        .select("*").eq("id",liveId).maybeSingle();
      if(le)throw le; live=l||null;
    }
    const active=live||newest.version;
    const targets=await versionTargets(active?.id||null);
    return {latest:newest.version,live,active,targets,public_menu:pub?.[0]||null};
  }
  async function getVersion(id:string){
    const {data:v,error:e}=await sb.schema("phg").from("menu_publication_versions")
      .select("*").eq("id",id).eq("menu_project_id",pid).maybeSingle();
    if(e)throw e;
    if(!v)throw new Error("publication version not found");
    return v;
  }

  if(action==="status"){
    try{
      const st=await state();
      return out({status:"ok",project,account,latest:st.latest,live:st.live,targets:st.targets});
    }catch(e:any){return out({error:e.message||String(e)},500);}
  }

  if(action==="history"){
    try{
      const st=await state();
      const {data:rows,error:e}=await sb.schema("phg").from("menu_publication_versions")
        .select("id,version,source_revision,source_title,status,published_at,activated_at,item_count,section_count")
        .eq("menu_project_id",pid).order("version",{ascending:false}).limit(60);
      if(e)throw e;
      const ids=(rows||[]).map((x:any)=>x.id);
      let targetRows:any[]=[];
      if(ids.length){
        const {data:t,error:te}=await sb.schema("phg").from("menu_publication_targets")
          .select("publication_version_id,target_key,enabled,settings,public_key").in("publication_version_id",ids);
        if(te)throw te; targetRows=t||[];
      }
      const by=new Map<string,any[]>();
      for(const t of targetRows){
        const k=String(t.publication_version_id);
        if(!by.has(k))by.set(k,[]);
        by.get(k)!.push(t);
      }
      const items=(rows||[]).map((v:any)=>({
        ...v,
        live:!!st.live&&String(st.live.id)===String(v.id),
        targets:by.get(String(v.id))||[]
      }));
      return out({status:"ok",project,account,live_id:st.live?.id||null,items});
    }catch(e:any){return out({error:e.message||String(e)},500);}
  }

  if(action==="version"){
    try{
      const v=await getVersion(String(b.version_id||""));
      const targets=await versionTargets(v.id);
      const snap=v.snapshot||{};
      const tree=v.published_tree||buildTree(snap.doc||{},project,v.version,new Map());
      return out({
        status:"ok",project,account,publication:v,targets,tree,
        menu:{name:v.source_title||project.name,version:v.version},
        metadata:{targets:targetObject(targets),publication_version:v.version}
      });
    }catch(e:any){return out({error:e.message||String(e)},404);}
  }

  if(action==="compare"){
    try{
      const a=await getVersion(String(b.version_a||""));
      const bver=await getVersion(String(b.version_b||""));
      const diff=compareDocs(a.snapshot?.doc||{},bver.snapshot?.doc||{});
      const ta=await versionTargets(a.id),tb=await versionTargets(bver.id);
      const amap=targetObject(ta),bmap=targetObject(tb),target_changes:any[]=[];
      for(const k of ["interactive","digital","print","display","embed"]){
        if(JSON.stringify(amap[k]||null)!==JSON.stringify(bmap[k]||null)){
          target_changes.push({target_key:k,before:amap[k]||null,after:bmap[k]||null});
        }
      }
      return out({
        status:"ok",
        version_a:{id:a.id,version:a.version,published_at:a.published_at},
        version_b:{id:bver.id,version:bver.version,published_at:bver.published_at},
        diff:{...diff,target_changes}
      });
    }catch(e:any){return out({error:e.message||String(e)},400);}
  }

  if(action==="activate"){
    try{
      const selected=await getVersion(String(b.version_id||""));
      const before=await state();
      if(before.live&&String(before.live.id)===String(selected.id)){
        return out({status:"ok",already_live:true,live:selected,targets:before.targets});
      }
      const targets=await versionTargets(selected.id);
      const snap=selected.snapshot||{};
      const tree=selected.published_tree||buildTree(snap.doc||{},project,selected.version,new Map());
      const menuKey=slug(project.name)+"-"+String(project.id).slice(0,8);
      const publicEnabled=targets.some((t:any)=>t.enabled&&["interactive","digital","display","embed"].includes(t.target_key));

      await sb.schema("phg").from("menu_publication_versions")
        .update({status:"superseded"}).eq("menu_project_id",pid).eq("status","published");
      await sb.schema("phg").from("menu_publication_versions")
        .update({status:"published",activated_at:new Date().toISOString()}).eq("id",selected.id);

      const {error:pubErr}=await sb.schema("phg").from("public_menu_experiences").upsert({
        account_key:account?.account_key||String(project.account_id),
        account_name:account?.name||"PHG account",
        menu_key:menuKey,
        menu_name:selected.source_title||project.name,
        source_menu_project_id:pid,
        publication_version_id:selected.id,
        status:"beta",
        published:publicEnabled,
        preview_badge:"Published menu · v"+selected.version,
        theme:{accent:"#7ef9ff",accent_secondary:"#ff4fbd",background:"#05070d",node_shape:"oval"},
        published_tree:tree,
        metadata:{
          consumer_mode:"interactive_nodes",
          publication_version:selected.version,
          source_revision:selected.source_revision,
          item_count:selected.item_count,
          targets:targetObject(targets)
        },
        updated_at:new Date().toISOString()
      },{onConflict:"account_key,menu_key"});
      if(pubErr)throw pubErr;

      await sb.schema("phg").from("menu_publication_targets")
        .update({public_key:menuKey}).eq("publication_version_id",selected.id)
        .in("target_key",["interactive","digital","display","embed"]);

      await sb.schema("phg").from("menu_publication_activations").insert({
        menu_project_id:pid,
        publication_version_id:selected.id,
        previous_publication_version_id:before.live?.id||null,
        activated_by:user.id,
        reason:String(b.reason||"restore")
      });

      const after=await state();
      return out({status:"ok",restored:true,latest:after.latest,live:after.live,targets:after.targets});
    }catch(e:any){return out({error:e.message||String(e)},500);}
  }

  const doc=clone(b.doc||{});
  if(doc?.phg&&typeof doc.phg==="object"){
    delete doc.phg.sync_token;
    delete doc.phg.session_token;
    delete doc.phg.approval_token;
  }
  const style=clone(b.style||{});
  const sizeKey=b.size||null,presetKey=b.preset||null;
  const itemCount=countItems(doc);
  const rvIds:string[]=[];
  for(const sec of (doc?.sections||[])){
    for(const it of (sec?.items||[]))if(it?.phg?.recipe_version_id)rvIds.push(String(it.phg.recipe_version_id));
    for(const sub of (sec?.subs||[]))for(const it of (sub?.items||[]))if(it?.phg?.recipe_version_id)rvIds.push(String(it.phg.recipe_version_id));
  }
  const recipes=new Map<string,any>();
  if(rvIds.length){
    const {data:rvs}=await sb.schema("phg").from("recipe_versions")
      .select("id,recipe_name,cocktail_name,build_family,method,glassware,garnish,ingredients,status")
      .in("id",Array.from(new Set(rvIds)));
    for(const rv of (rvs||[]))recipes.set(String(rv.id),rv);
  }

  if(action==="preview"){
    const last=await latest().catch(()=>({version:null,targets:[]}));
    const next=(last.version?.version||0)+1;
    const tree=buildTree(doc,project,next,recipes);
    return out({
      status:"ok",preview:true,item_count:itemCount,next_version:next,tree,
      targets:defaultTargets(sizeKey,presetKey),
      source_revision:b.source_revision??project.backend_revision??null
    });
  }

  if(action==="publish"){
    if(itemCount<1 && !b.allow_empty)return out({error:"This menu has no items. Add menu content before publishing a guest version.",code:"EMPTY_MENU"},409);
    try{
      const prev=await latest();
      const ver=(prev.version?.version||0)+1;
      if(prev.version){
        await sb.schema("phg").from("menu_publication_versions")
          .update({status:"superseded"}).eq("id",prev.version.id).eq("status","published");
      }
      const snapshot={doc,style,size:sizeKey,preset:presetKey};
      const tree=buildTree(doc,project,ver,recipes);
      const {data:pub,error:pe}=await sb.schema("phg").from("menu_publication_versions").insert({
        menu_project_id:pid,
        account_id:project.account_id,
        version:ver,
        source_revision:b.source_revision??project.backend_revision??null,
        source_title:doc?.title||project.name,
        snapshot,
        style,
        size_key:sizeKey,
        preset_key:presetKey,
        status:"published",
        published_by:user.id,
        published_tree:tree,
        item_count:itemCount,
        section_count:countSections(doc),
        activated_at:new Date().toISOString()
      }).select("*").single();
      if(pe)throw pe;

      const incoming=b.targets&&typeof b.targets==="object"?b.targets:defaultTargets(sizeKey,presetKey);
      const defs=defaultTargets(sizeKey,presetKey);
      const keys=["interactive","digital","print","display","embed"];
      const targetRows=keys.map(k=>{
        const x=incoming[k]||defs[k];
        return {
          publication_version_id:pub.id,
          target_key:k,
          enabled:x.enabled!==undefined?!!x.enabled:!!defs[k].enabled,
          settings:{...defs[k].settings,...(x.settings||{})},
          public_key:null
        };
      });
      const {error:te}=await sb.schema("phg").from("menu_publication_targets").insert(targetRows);
      if(te)throw te;

      const acct=account;
      const menuKey=slug(project.name)+"-"+String(project.id).slice(0,8);
      const publicEnabled=targetRows.some((t:any)=>t.enabled&&["interactive","digital","display","embed"].includes(t.target_key));
      const {error:pubErr}=await sb.schema("phg").from("public_menu_experiences").upsert({
        account_key:acct?.account_key||String(project.account_id),
        account_name:acct?.name||"PHG account",
        menu_key:menuKey,
        menu_name:doc?.title||project.name,
        source_menu_project_id:pid,
        publication_version_id:pub.id,
        status:"beta",
        published:publicEnabled,
        preview_badge:"Published menu · v"+ver,
        theme:{accent:"#7ef9ff",accent_secondary:"#ff4fbd",background:"#05070d",node_shape:"oval"},
        published_tree:tree,
        metadata:{
          consumer_mode:"interactive_nodes",
          publication_version:ver,
          source_revision:b.source_revision??project.backend_revision??null,
          item_count:itemCount,
          targets:Object.fromEntries(targetRows.map((t:any)=>[t.target_key,{enabled:t.enabled,settings:t.settings}]))
        },
        updated_at:new Date().toISOString()
      },{onConflict:"account_key,menu_key"});
      if(pubErr)throw pubErr;

      await sb.schema("phg").from("menu_publication_targets")
        .update({public_key:menuKey}).eq("publication_version_id",pub.id).in("target_key",["interactive","digital","display","embed"]);

      await sb.schema("phg").from("menu_publication_activations").insert({
        menu_project_id:pid,
        publication_version_id:pub.id,
        previous_publication_version_id:prev.version?.id||null,
        activated_by:user.id,
        reason:"publish"
      });

      const st=await state();
      return out({
        status:"ok",published:true,item_count:itemCount,publication:st.live||st.latest,targets:st.targets,
        public_menu:{account_key:acct?.account_key||String(project.account_id),menu_key:menuKey}
      });
    }catch(e:any){return out({error:e.message||String(e)},500);}
  }

  if(action==="set_target"){
    const target=String(b.target_key||"");
    if(!["interactive","digital","print","display","embed"].includes(target))return out({error:"invalid target"},400);
    try{
      const st=await state();
      const active=st.live||st.latest;
      if(!active)return out({error:"Publish a menu version before changing live targets."},409);
      const existing=st.targets.find((x:any)=>x.target_key===target);
      const settings={...(existing?.settings||{}),...(b.settings||{})};
      const {error:e}=await sb.schema("phg").from("menu_publication_targets").upsert({
        publication_version_id:active.id,target_key:target,
        enabled:b.enabled===undefined?!!existing?.enabled:!!b.enabled,
        settings,public_key:existing?.public_key||null,updated_at:new Date().toISOString()
      },{onConflict:"publication_version_id,target_key"});
      if(e)throw e;
      const after=await state();
      const webEnabled=after.targets.some((t:any)=>t.enabled&&["interactive","digital","display","embed"].includes(t.target_key));
      await sb.schema("phg").from("public_menu_experiences")
        .update({
          published:webEnabled,
          metadata:{
            consumer_mode:"interactive_nodes",
            publication_version:active.version,
            source_revision:active.source_revision,
            item_count:active.item_count,
            targets:targetObject(after.targets)
          },
          updated_at:new Date().toISOString()
        })
        .eq("publication_version_id",active.id);
      return out({status:"ok",latest:after.latest,live:after.live,targets:after.targets});
    }catch(e:any){return out({error:e.message||String(e)},500);}
  }

  return out({error:"unknown action"},400);
});