import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors={
  "Access-Control-Allow-Origin":"*",
  "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods":"POST, OPTIONS"
};
const out=(x:any,s=200)=>new Response(JSON.stringify(x),{status:s,headers:{...cors,"Content-Type":"application/json"}});
const BUCKET="phg-invoices";

function b64ToBytes(s:string){
  const clean=s.includes(",")?s.slice(s.indexOf(",")+1):s;
  const bin=atob(clean),a=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i);
  return a;
}
async function sha256Hex(bytes:Uint8Array){
  const d=await crypto.subtle.digest("SHA-256",bytes);
  return Array.from(new Uint8Array(d)).map(x=>x.toString(16).padStart(2,"0")).join("");
}
function safeName(s:string){
  return s.replace(/[^a-zA-Z0-9._-]+/g,"_").slice(-140)||"invoice";
}
function outputText(raw:any){
  if(typeof raw?.output_text==="string"&&raw.output_text)return raw.output_text;
  for(const item of raw?.output||[])for(const p of item?.content||[])
    if(p?.type==="output_text"&&typeof p.text==="string")return p.text;
  return "";
}

Deno.serve(async req=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(req.method!=="POST")return out({error:"POST required"},405);

  const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const oa=Deno.env.get("OPENAI_API_KEY"),model=Deno.env.get("OPENAI_INVOICE_MODEL")||Deno.env.get("OPENAI_MODEL")||"gpt-4o-mini";
  if(!url||!key||!oa)return out({error:"runtime configuration missing"},500);
  const sb=createClient(url,key,{auth:{persistSession:false}});
  const b=await req.json().catch(()=>({}));
  const action=String(b.action||"");

  const {data:authorized,error:authErr}=await sb.rpc("phg_menu_authorize",{
    p_menu_project_id:b.menu_project_id||null,
    p_sync_token:b.sync_token||null
  });
  if(authErr)return out({error:authErr.message},500);
  if(!authorized)return out({error:"invalid_menu_token"},403);

  try{
    if(action==="parse_file"){
      const filename=safeName(String(b.filename||"invoice"));
      const mime=String(b.mime_type||"application/octet-stream");
      const fileData=String(b.file_data||"");
      if(!fileData)return out({error:"file_data required"},400);
      const bytes=b64ToBytes(fileData);
      if(bytes.byteLength>12*1024*1024)return out({error:"invoice file exceeds 12 MB intake limit"},413);
      const hash=await sha256Hex(bytes);

      const {data:existing}=await sb.rpc("phg_invoice_document_detail",{p_document_id:null});
      // exact duplicate check by content hash lives in record RPC; storage path is deterministic.
      const day=new Date().toISOString().slice(0,10).replace(/-/g,"/");
      const path=`${day}/${hash.slice(0,16)}/${filename}`;

      const buckets=await sb.storage.listBuckets();
      if(!buckets.data?.some((x:any)=>x.name===BUCKET)){
        const cr=await sb.storage.createBucket(BUCKET,{public:false,fileSizeLimit:12582912});
        if(cr.error && !String(cr.error.message).toLowerCase().includes("already"))throw cr.error;
      }
      const up=await sb.storage.from(BUCKET).upload(path,bytes,{contentType:mime,upsert:false});
      if(up.error && !String(up.error.message).toLowerCase().includes("already"))throw up.error;

      const nullableNumber={type:["number","null"]};
      const nullableString={type:["string","null"]};
      const lineSchema={
        type:"object",additionalProperties:false,
        properties:{
          line_number:{type:["integer","null"]},
          line_type:{type:"string",enum:["merchandise","deposit_charge","deposit_return","fee","tax","discount","credit","freight","other"]},
          vendor_sku:nullableString,
          raw_description:{type:"string"},
          product_family_key:nullableString,
          flavor_variant:nullableString,
          purchase_quantity:nullableNumber,
          purchase_unit:{type:["string","null"],enum:["each","case","keg","bag","box","tray","pallet","other",null]},
          containers_per_purchase_unit:nullableNumber,
          container_size:nullableNumber,
          container_size_unit:{type:["string","null"],enum:["ml","l","oz","gal","bbl","g","kg","lb","each","dash","drop",null]},
          container_type:nullableString,
          unit_price:nullableNumber,
          extended_amount:nullableNumber,
          discount_amount:nullableNumber,
          net_merchandise_amount:nullableNumber,
          deposit_quantity:nullableNumber,
          deposit_amount_per_unit:nullableNumber,
          deposit_amount:nullableNumber,
          container_key:nullableString,
          notes:nullableString,
          confidence:{type:"number",minimum:0,maximum:1}
        },
        required:[
          "line_number","line_type","vendor_sku","raw_description","product_family_key","flavor_variant",
          "purchase_quantity","purchase_unit","containers_per_purchase_unit","container_size","container_size_unit",
          "container_type","unit_price","extended_amount","discount_amount","net_merchandise_amount",
          "deposit_quantity","deposit_amount_per_unit","deposit_amount","container_key","notes","confidence"
        ]
      };
      const schema={
        type:"object",additionalProperties:false,
        properties:{
          vendor_name:{type:"string"},
          vendor_account_ref:nullableString,
          invoice_number:nullableString,
          invoice_date:{type:"string"},
          due_date:nullableString,
          currency:{type:"string"},
          location_hint:nullableString,
          subtotal:nullableNumber,
          discounts:nullableNumber,
          tax:nullableNumber,
          fees:nullableNumber,
          freight:nullableNumber,
          deposit_charges:nullableNumber,
          deposit_credits:nullableNumber,
          total:nullableNumber,
          lines:{type:"array",items:lineSchema},
          warnings:{type:"array",items:{type:"string"}}
        },
        required:[
          "vendor_name","vendor_account_ref","invoice_number","invoice_date","due_date","currency","location_hint",
          "subtotal","discounts","tax","fees","freight","deposit_charges","deposit_credits","total","lines","warnings"
        ]
      };

      const content:any[]=[
        {type:"input_text",text:[
          "Extract this supplier invoice exactly enough for beverage purchasing review.",
          "Preserve each invoice line separately. Do not merge variants.",
          "Recognize pack and size notation such as 24 x 12 oz, 12 x 19.2 oz, 6 x 750 mL, 1 L, 1/6 bbl, 1/4 bbl, 1/2 bbl, 50 L.",
          "Treat different flavors as separate variants even when the parent product is the same.",
          "Do not treat package-size words such as half barrel, quarter barrel, sixth barrel, 1/2 bbl, 1/4 bbl, 1/6 bbl, 50 L, 750 mL, or 1 L as flavors.",
          "Treat different case packs or container sizes as distinct purchasing variants.",
          "Classify refundable keg/shell/container charges as deposit_charge and credits/returns as deposit_return, never merchandise.",
          "Taxes, freight, service fees, discounts and credits are not merchandise.",
          "raw_description must preserve the invoice wording. If a field is uncertain, use null and add a warning instead of guessing.",
          "For merchandise, purchase_quantity is the number of purchase units ordered; containers_per_purchase_unit is the pack count; container_size is one container's size.",
          "For a keg sold as one keg, purchase_quantity=1, purchase_unit=keg, containers_per_purchase_unit=1, and container_size is its beer volume.",
          "Amounts should retain the invoice's sign/meaning, but deposit_return should have a positive deposit_amount representing the credit magnitude.",
          "Use ISO date YYYY-MM-DD for invoice_date. If unreadable, use an empty string and add a warning."
        ].join("\n")}
      ];
      let openaiFileId:string|null=null;
      if(mime.startsWith("image/")){
        content.push({type:"input_image",image_url:`data:${mime};base64,${fileData.includes(",")?fileData.slice(fileData.indexOf(",")+1):fileData}`,detail:"high"});
      }else{
        const form=new FormData();
        form.append("purpose","user_data");
        form.append("expires_after[anchor]","created_at");
        form.append("expires_after[seconds]","3600");
        form.append("file",new Blob([bytes],{type:mime}),filename);
        const fu=await fetch("https://api.openai.com/v1/files",{
          method:"POST",headers:{"Authorization":`Bearer ${oa}`},body:form
        });
        const fj=await fu.json();
        if(!fu.ok||!fj?.id)return out({error:"invoice file upload for extraction failed",detail:fj?.error?.message||fj},502);
        openaiFileId=fj.id;
        content.push({type:"input_file",file_id:openaiFileId});
      }

      const rr=await fetch("https://api.openai.com/v1/responses",{
        method:"POST",
        headers:{"Authorization":`Bearer ${oa}`,"Content-Type":"application/json"},
        body:JSON.stringify({
          model,
          instructions:"You extract beverage supplier invoices into structured accounting data. Accuracy and uncertainty disclosure are more important than filling every field.",
          input:[{role:"user",content}],
          text:{format:{type:"json_schema",name:"phg_invoice_extract_v1",strict:true,schema}}
        })
      });
      const raw=await rr.json();
      if(openaiFileId){
        fetch("https://api.openai.com/v1/files/"+openaiFileId,{method:"DELETE",headers:{"Authorization":`Bearer ${oa}`}}).catch(()=>{});
      }
      if(!rr.ok){
        await sb.rpc("phg_invoice_document_record",{
          p_storage_bucket:BUCKET,p_storage_path:path,p_original_filename:filename,p_mime_type:mime,
          p_size_bytes:bytes.byteLength,p_content_hash:hash,p_parser_model:model,p_extracted:{},
          p_parse_warnings:["Parser failed: "+String(raw?.error?.message||"unknown error")],
          p_source_metadata:{parse_error:raw?.error||raw}
        });
        return out({error:"invoice extraction failed",detail:raw?.error?.message||raw},502);
      }
      const txt=outputText(raw);
      if(!txt)return out({error:"invoice extraction returned no output"},502);
      const extracted=JSON.parse(txt);

      // Deterministic cleanup: deposits are not merchandise, and package-size words are not flavors.
      if(Array.isArray(extracted.lines)){
        for(const line of extracted.lines){
          if(line.line_type==="deposit_charge"||line.line_type==="deposit_return"){
            if(line.deposit_quantity==null && line.purchase_quantity!=null) line.deposit_quantity=line.purchase_quantity;
            if(line.deposit_amount_per_unit==null && line.unit_price!=null) line.deposit_amount_per_unit=Math.abs(Number(line.unit_price));
            if(line.deposit_amount==null && line.extended_amount!=null) line.deposit_amount=Math.abs(Number(line.extended_amount));
            line.net_merchandise_amount=null;
          }
          if(line.container_type==="keg" && typeof line.flavor_variant==="string" &&
             /^(half[ -]?barrel|quarter[ -]?barrel|sixth[ -]?barrel|1\/2 ?bbl|1\/4 ?bbl|1\/6 ?bbl|50 ?l)$/i.test(line.flavor_variant.trim())){
            line.flavor_variant=null;
          }
        }
      }

      // Normalize obvious empty invoice date to null-compatible override later.
      const warnings=Array.isArray(extracted.warnings)?extracted.warnings:[];
      if(!/^\d{4}-\d{2}-\d{2}$/.test(String(extracted.invoice_date||""))){
        warnings.push("Invoice date needs review.");
        extracted.invoice_date=null;
      }

      const {data:rec,error:recErr}=await sb.rpc("phg_invoice_document_record",{
        p_storage_bucket:BUCKET,p_storage_path:path,p_original_filename:filename,p_mime_type:mime,
        p_size_bytes:bytes.byteLength,p_content_hash:hash,p_parser_model:model,
        p_extracted:extracted,p_parse_warnings:warnings,
        p_source_metadata:{input_type:mime.startsWith("image/")?"image":"file"}
      });
      if(recErr)throw recErr;

      const {data:vendorMatch}=await sb.rpc("phg_vendor_match_exact",{p_name:extracted.vendor_name||""});

      return out({
        status:"parsed",
        document:rec?.document||null,
        extracted,
        vendor_match:vendorMatch||null,
        storage:{bucket:BUCKET,path,content_hash:hash}
      });
    }

    if(action==="discard_document"){
      const {data,error}=await sb.rpc("phg_invoice_document_discard",{p_document_id:b.document_id});
      if(error)throw error;
      const rm=await sb.storage.from(data.storage_bucket||BUCKET).remove([data.storage_path]);
      if(rm.error)return out({error:"document metadata removed but storage deletion failed",detail:rm.error.message,document_id:b.document_id},500);
      return out({status:"discarded",document_id:b.document_id});
    }

    if(action==="document_detail"){
      const {data,error}=await sb.rpc("phg_invoice_document_detail",{p_document_id:b.document_id});
      if(error)throw error; return out(data);
    }

    if(action==="commit_document"){
      const {data,error}=await sb.rpc("phg_invoice_document_commit",{
        p_document_id:b.document_id,
        p_vendor_id:b.vendor_id,
        p_location_key:b.location_key,
        p_override:b.override||{}
      });
      if(error)throw error; return out(data);
    }

    return out({error:"unknown action"},400);
  }catch(e:any){
    const msg=String(e?.message||e||"error");
    if(msg.includes("not found"))return out({error:msg},404);
    return out({error:msg},500);
  }
});