import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});
async function sha256Hex(value:string){
  const bytes=new TextEncoder().encode(value);
  const digest=await crypto.subtle.digest("SHA-256",bytes);
  return Array.from(new Uint8Array(digest)).map(x=>x.toString(16).padStart(2,"0")).join("");
}

Deno.serve(async req=>{
  if(req.method==="OPTIONS") return new Response("ok",{headers:cors});
  if(req.method!=="POST") return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL");
  const key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!url||!key) return out({error:"runtime configuration missing"},500);
  const sb=createClient(url,key,{auth:{persistSession:false}});
  const b=await req.json().catch(()=>({}));
  const action=String(b.action||"");
  const authHeader=req.headers.get("Authorization")||"";
  const bearer=authHeader.replace(/^Bearer\s+/i,"").trim();

  try{
    if(action==="verify_project"){
      const pid=String(b.menu_project_id||"");
      const token=String(b.sync_token||"");
      if(!pid||!token) return out({error:"project ID and access token required"},400);

      const {data:ok,error:ae}=await sb.rpc("phg_menu_authorize",{
        p_menu_project_id:pid,
        p_sync_token:token
      });
      if(ae) throw ae;
      if(!ok) return out({error:"invalid_menu_token"},403);

      const {data:p,error:pe}=await sb.schema("phg").from("menu_projects")
        .select("id,name,status,backend_revision,editor_state,account_id,updated_at")
        .eq("id",pid).maybeSingle();
      if(pe) throw pe;
      if(!p) return out({error:"menu project not found"},404);

      let account:any=null;
      if(p.account_id){
        const {data:a,error:ace}=await sb.schema("phg").from("accounts")
          .select("id,account_key,name").eq("id",p.account_id).maybeSingle();
        if(ace) throw ace;
        account=a||null;
      }

      const {count:itemCount,error:ice}=await sb.schema("phg").from("menu_items")
        .select("id",{count:"exact",head:true}).eq("menu_project_id",pid).neq("status","retired");
      if(ice) throw ice;
      const {count:candidateCount,error:cce}=await sb.schema("phg").from("menu_items")
        .select("id",{count:"exact",head:true}).eq("menu_project_id",pid)
        .is("editor_item_id",null).neq("status","retired");
      if(cce) throw cce;

      const st=(p.editor_state&&typeof p.editor_state==="object")?p.editor_state:{};
      const doc=(st as any).doc||null;
      return out({
        status:"verified",
        project:{
          id:p.id,
          name:p.name,
          status:p.status,
          backend_revision:p.backend_revision,
          account_id:p.account_id,
          has_editor_snapshot:!!doc,
          snapshot_title:doc?.title||null,
          last_synced_at:(st as any).synced_at||doc?.phg?.last_synced_at||null,
          menu_item_count:itemCount||0,
          unlinked_candidate_count:candidateCount||0,
          updated_at:p.updated_at
        },
        account
      });
    }

    if(action==="create_project"){
      if(!bearer) return out({error:"login required"},401);
      const {data:ud,error:ue}=await sb.auth.getUser(bearer);
      if(ue||!ud?.user) return out({error:"invalid or expired login"},401);

      const accountId=String(b.account_id||"");
      if(!accountId) return out({error:"account_id required"},400);
      const {data:mem,error:me}=await sb.schema("phg").from("account_memberships")
        .select("id,role,status").eq("account_id",accountId).eq("user_id",ud.user.id)
        .eq("status","active").limit(1).maybeSingle();
      if(me) throw me;
      if(!mem) return out({error:"account access denied"},403);

      const name=String(b.name||"Menu").trim().slice(0,160)||"Menu";
      const rawToken=crypto.randomUUID()+"-"+crypto.randomUUID();
      const tokenHash=await sha256Hex(rawToken);

      const {data:p,error:pe}=await sb.schema("phg").from("menu_projects").insert({
        name,
        status:"development",
        editor_source:"mdc-index",
        editor_token_hash:tokenHash,
        brief:{source:"menu_studio_create",created_by_user:ud.user.id},
        constraints:{},
        account_id:accountId
      }).select("id,name,status,backend_revision,account_id,updated_at").single();
      if(pe) throw pe;

      const {data:a,error:ae}=await sb.schema("phg").from("accounts")
        .select("id,account_key,name").eq("id",accountId).maybeSingle();
      if(ae) throw ae;

      return out({
        status:"created",
        project:{
          id:p.id,name:p.name,status:p.status,backend_revision:p.backend_revision,
          account_id:p.account_id,has_editor_snapshot:false,last_synced_at:null,
          menu_item_count:0,unlinked_candidate_count:0,updated_at:p.updated_at
        },
        account:a||null,
        sync_token:rawToken
      });
    }

    if(action==="sync_menu"){
      const {data,error}=await sb.rpc("phg_menu_sync",{
        p_menu_project_id:b.menu_project_id||null,
        p_sync_token:b.sync_token||null,
        p_expected_revision:b.expected_revision??null,
        p_doc:b.doc||null,
        p_style:b.style||null,
        p_size:b.size||null,
        p_preset:b.preset||null
      });
      if(error) throw error;
      if(data?.error==="revision_conflict") return out(data,409);
      return out(data||{error:"empty sync result"},data?200:500);
    }

    if(action==="pull_menu"){
      const {data,error}=await sb.rpc("phg_menu_pull",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null
      });
      if(error) throw error;
      return out(data);
    }

    if(action==="list_candidates"){
      const {data,error}=await sb.rpc("phg_menu_list_candidates",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null
      });
      if(error) throw error;
      return out(data);
    }

    if(action==="training_overview"){
      const {data,error}=await sb.rpc("phg_menu_training_overview",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null
      });
      if(error) throw error;
      return out(data);
    }

    if(action==="training_latest"){
      const {data,error}=await sb.rpc("phg_training_latest",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null,
        p_menu_item_id:b.menu_item_id
      });
      if(error) throw error;
      return out(data);
    }

    if(action==="list_preps"){
      const {data,error}=await sb.rpc("phg_menu_list_preps",{
        p_menu_project_id:b.menu_project_id,
        p_sync_token:b.sync_token||null
      });
      if(error) throw error;
      return out(data);
    }

    return out({error:"unknown action"},400);
  }catch(e:any){
    const msg=String(e?.message||e||"error");
    if(msg.includes("invalid_menu_token")) return out({error:"invalid_menu_token"},403);
    if(msg.includes("menu project not found")) return out({error:"menu project not found"},404);
    return out({error:msg},500);
  }
});