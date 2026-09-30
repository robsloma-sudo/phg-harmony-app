export function htmlText(html,parseHTML) {
  const {document}=parseHTML(html);
  for(const n of document.querySelectorAll('script,style,noscript,nav,header,footer,svg,form,[hidden],[aria-hidden="true"]')) n.remove();
  const root=document.querySelector('main')||document.body||document.documentElement;
  for(const n of root.querySelectorAll('h1,h2,h3,h4,h5,h6')){n.prepend('\n# ');n.append('\n');}
  for(const n of root.querySelectorAll('br'))n.replaceWith('\n');
  for(const n of root.querySelectorAll('div,p,li,section,article,tr,dl,dt,dd')){n.prepend('\n');n.append('\n');}
  for(const n of root.querySelectorAll('td,th'))n.append(' ');
  return root.textContent.split(/\r?\n/).map(s=>s.replace(/\s+/g,' ').trim()).filter(Boolean).join('\n');
}
export function itemType(section,name){
 const s=section+' '+name;
 if(/\b(cocktails?|martinis?|margaritas?|old fashioned|spritz|negroni|daiquiri|mojito|paloma|manhattan|sangria)\b/i.test(s))return 'cocktail';
 if(/\b(beers?|lager|ale|ipa|stout|porter|pilsner|cider|seltzer)\b/i.test(s))return 'beer';
 if(/\b(wines?|cabernet|merlot|pinot|chardonnay|sauvignon|riesling|ros[eé]|prosecco|champagne)\b/i.test(s))return 'wine';
 if(/\b(spirits?|whisk(?:e)?y|bourbon|rye|tequila|mezcal|vodka|gin|rum|scotch|cognac|brandy)\b/i.test(s))return 'spirit_pour';
 return 'other';
}
const category=/^(?:signature |classic |craft |house |seasonal )?(?:cocktails?|drinks?|beverages?|spirits?|wines?(?: by the glass)?|beers?(?: on tap)?|drafts?|bottles?|dinner|lunch|appetizers?|desserts?|entrees?|salads?)$/i;
export function parseMenu(text){
 const out=[];let section='',pendingTitle='',description='';
 for(const raw of text.split(/\r?\n/)){
  const cl=raw.replace(/!\[[^\]]*\]\([^)]*\)/g,' ').replace(/\[([^\]]+)\]\([^)]*\)/g,'$1').replace(/^\s*#{1,6}\s*/,'').replace(/^\s*[-*+>]\s*/,'').replace(/[*_~]/g,'').replace(/\s+/g,' ').trim();
  if(!cl||cl.length>800)continue;
  const prices=[...cl.matchAll(/\$\s*(\d{1,3}(?:\.\d{1,2})?)(?![\d,.])/g)];
  if(prices.length>1){pendingTitle='';description='';continue;}
  const standalone=cl.match(/^\$?\s*(\d{1,3}(?:\.\d{1,2})?)$/);
  let name='',price=null,notes=cl;
  if(standalone&&pendingTitle){name=pendingTitle;price=Number(standalone[1]);notes=[name,description,cl].filter(Boolean).join(' | ');}
  else if(prices.length===1){name=cl.slice(0,prices[0].index).trim();price=Number(prices[0][1]);}
  else{const tail=cl.match(/\s+(\d{1,3}(?:\.\d{1,2})?)\s*$/);if(tail&&(section||itemType('',cl)!=='other')){name=cl.slice(0,tail.index).trim();price=Number(tail[1]);}}
  if(price!==null){
   name=name.replace(/[.·•|\-–—:\s]+$/g,'').trim();
   if(name.length>=2&&name.length<=300&&price>=1&&price<=1000&&!category.test(name)&&!/^(hours?|open|close|address|phone|subtotal|total|minimum|maximum|tax|gratuity|copyright|call us|tel|save|off|discount|add |extra )\b/i.test(name)&&!/\d\s*(?:am|pm)|https?:|@|%/i.test(name)){
    out.push({section_name:section||null,item_type:itemType(section,name),item_name:name,item_price:price,spirit_brands:null,notes});pendingTitle='';description='';
   }
   if(out.length>350)throw Error('too_many_items_requires_followup');
   continue;
  }
  if(category.test(cl)){section=cl;pendingTitle='';description='';continue;}
  const letters=(cl.match(/[A-Za-z]/g)||[]).length,upp=(cl.match(/[A-Z]/g)||[]).length;
  if(/^\s*#/.test(raw)||(letters>3&&cl.length<70&&upp/letters>.8)){
   if(/menu|happy hour|by the glass|on tap/i.test(cl)){section=cl;pendingTitle='';}else{pendingTitle=cl;description='';}
  }else if(cl.length<100&&!/[,;]|\d{3}|https?:|@/.test(cl)){pendingTitle=cl;description='';}else if(pendingTitle)description=cl;
 }
 return [...new Map(out.map(x=>[(x.section_name+'|'+x.item_name+'|'+x.item_price).toLowerCase(),x])).values()];
}
