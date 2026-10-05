/* ==========================================================================
   PHG COCKTAIL DESIGN STUDIO — proposed tab module (v1)
   Plugs into index.html exactly like the other tabs:
     setApp('studio') -> render() -> csSideNav() + csPage() -> csMount()
   Live 3D: three.js (lazy-loaded from CDN only when this tab opens).
   Data:   phg-cocktail-studio Edge Function (Backend Lead DEV). Until it is
           deployed the tab runs on cocktail-studio-demo.json and shows a
           "demo data" banner — no silent fallback.
   Style:  vanilla ES5 strings for the shell (matches host), ES module only
           for three.js. Host helpers used if present: esc, money.
   ========================================================================== */

var CS_URL = (typeof BASE === 'string' ? BASE.replace('/rest/v1', '') : '') + '/functions/v1/phg-cocktail-studio';
var CS = {
  started: false, loading: false, demo: false, error: null,
  drinks: [], glassware: [], serveStyles: [], garnishTypes: [],
  cur: null,            // current drink payload (recipe, balance, cost, stock, visuals)
  draft: null,          // editable visuals (what the 3D shows)
  three: null,          // {THREE, renderer, scene, camera, controls, group}
  renderJob: null
};

var CS_SERVE = {  // mirrors phg.serve_styles + builder SERVE (defaults when the API is not up)
  up: {ice: {type: 'none'}, stem: true}, neat: {ice: {type: 'none'}, stem: null},
  down: {ice: {type: 'large_cube'}, stem: false}, on_large_cube: {ice: {type: 'large_cube'}, stem: false},
  on_sphere: {ice: {type: 'sphere'}, stem: false}, on_cubes: {ice: {type: 'cubes', count: 0}, stem: false},
  on_spear: {ice: {type: 'spear'}, stem: false}, on_crushed: {ice: {type: 'crushed'}, stem: false}
};
var CS_STEMMED = {coupe:1, nick_and_nora:1, martini:1, flute:1, wine:1, margarita:1, hurricane:1, snifter:1, cordial:1, goblet:1};
var CS_GARNISH = ['cherry','olive','orange_half_moon','lemon_half_moon','lime_half_moon','orange_wheel','lemon_wheel','lime_wheel',
  'lime_wedge','lemon_wedge','orange_peel','lemon_peel','lime_peel','orange_twist','lemon_twist','mint_sprig','drops'];
var CS_PLACE = ['pick','rim','dropped','float','drape','inside_wall','surface'];
var CS_DROPS = ['angostura','peychauds','orange_bitters','olive_oil','chili_oil','sesame_oil','citrus_oil'];

function csE(s){ return (typeof esc === 'function') ? esc(s) : String(s == null ? '' : s).replace(/[&<>"]/g, function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
function csMoney(x){ return x == null ? '—' : (typeof money === 'function' ? money(x) : '$' + Number(x).toFixed(2)); }
function csPct(x){ return x == null ? '—' : Number(x).toFixed(1) + '%'; }

/* ---------------------------------------------------------------- data */
function csCall(action, body, cb){
  var x = new XMLHttpRequest(); x.open('POST', CS_URL);
  x.setRequestHeader('Content-Type', 'application/json');
  if (typeof H === 'object') for (var k in H) x.setRequestHeader(k, H[k]);
  x.onload = function(){ var j = null; try { j = JSON.parse(x.responseText); } catch(e){}
    if (x.status >= 200 && x.status < 300 && j) cb(null, j); else cb((j && j.error) || ('HTTP ' + x.status), j, x.status); };
  x.onerror = function(){ cb('network error', null, 0); };
  x.send(JSON.stringify(Object.assign({action: action}, body || {})));
}

function csLoad(){
  if (CS.loading) return; CS.loading = true; CS.error = null;
  csCall('list_drinks', {}, function(err, j, status){
    if (!err){
      CS.demo = false; CS.drinks = j.drinks || []; CS.glassware = j.glassware || [];
      CS.serveStyles = j.serve_styles || []; CS.garnishTypes = j.garnish_types || [];
      CS.loading = false; CS.started = true;
      if (CS.drinks.length) csOpen(CS.drinks[0].recipe_version_id); else render();
      return;
    }
    // function not deployed yet (404) -> demo data, clearly flagged
    var d = new XMLHttpRequest(); d.open('GET', 'cocktail-studio/cocktail-studio-demo.json');
    d.onload = function(){
      CS.loading = false; CS.started = true;
      try { var demo = JSON.parse(d.responseText); CS.demo = true; CS.drinks = demo.drinks; CS.glassware = demo.glassware;
            CS.error = 'phg-cocktail-studio not available (' + err + '). Showing demo data.'; csOpenDemo(0); }
      catch(e){ CS.error = 'Could not load studio data: ' + err; render(); }
    };
    d.onerror = function(){ CS.loading = false; CS.error = 'Could not load studio data: ' + err; render(); };
    d.send();
  });
}

function csOpen(rvId){
  CS.loading = true; render();
  csCall('get_drink', {recipe_version_id: rvId}, function(err, j){
    CS.loading = false;
    if (err){ CS.error = 'Could not open drink: ' + err; render(); return; }
    CS.cur = j; CS.draft = JSON.parse(JSON.stringify(j.visuals || csDefaultVisuals(j))); render();
  });
}
function csOpenDemo(i){ CS.cur = CS.drinks[i]; CS.draft = JSON.parse(JSON.stringify(CS.cur.visuals)); render(); }
function csDefaultVisuals(j){
  var g = CS.glassware[0] || {};
  return {glassware_id: g.id, serve: 'up', ice: {type: 'none'}, liquid: {color_hex: '#c9802b', clarity: 0.9, foam_mm: 0},
          garnish: [], finished_volume_ml: (j.balance && j.balance.finished_volume_ml) || 120};
}
function csGlass(){ var id = CS.draft && CS.draft.glassware_id;
  for (var i = 0; i < CS.glassware.length; i++) if (CS.glassware[i].id === id || CS.glassware[i].glass_key === id) return CS.glassware[i];
  return CS.glassware[0]; }

/* ---------------------------------------------------------------- validation (same rules as the Blender builder) */
function csWarnings(){
  var w = [], v = CS.draft, g = csGlass(); if (!v || !g) return w;
  var rule = CS_SERVE[v.serve], stem = !!CS_STEMMED[g.family];
  if (rule){
    if (rule.stem === true && !stem) w.push("'" + v.serve + "' is normally served in stemware, not a " + g.family);
    if (rule.stem === false && stem) w.push("'" + v.serve + "' needs a tumbler — ice in a " + g.family + ' is unusual');
    if ((v.serve === 'up' || v.serve === 'neat') && v.ice && v.ice.type !== 'none') w.push("'" + v.serve + "' means no ice, but ice is set");
  }
  if (g.verification_status === 'unverified') w.push('Glass dimensions are approximate (unverified profile)');
  var cap = Number(g.capacity_ml || 0); if (cap && Number(v.finished_volume_ml) > cap * 0.95) w.push('Drink volume is at or over the glass brim (' + cap + ' ml)');
  (v.garnish || []).forEach(function(x){ if (x.type === 'drops' && x.liquid === 'sesame_oil') w.push('Sesame oil drops: declare SESAME allergen'); });
  return w;
}

/* ---------------------------------------------------------------- shell (HTML strings, like the other tabs) */
function csSideNav(){
  if (!CS.started){ setTimeout(csLoad, 0); }
  var h = '<div class="navlbl">Cocktail Design</div>';
  CS.drinks.forEach(function(d, i){
    var on = CS.cur && (CS.cur.recipe_version_id === d.recipe_version_id);
    h += '<button class="nav' + (on ? ' on' : '') + '" onclick="' + (CS.demo ? 'csOpenDemo(' + i + ')' : "csOpen('" + csE(d.recipe_version_id) + "')") + '">' +
         csE(d.name) + '<span class="cnt" style="opacity:.5">' + csE(d.status || '') + '</span></button>';
  });
  if (!CS.drinks.length && !CS.loading) h += '<div class="navlbl" style="text-transform:none;letter-spacing:0">No drinks yet. Ask Harmony to design one.</div>';
  return h;
}

function csPage(){
  var h = '<div class="cs">';
  if (CS.error) h += '<div class="cs-banner' + (CS.demo ? ' demo' : '') + '">' + csE(CS.error) + '</div>';
  if (CS.loading && !CS.cur) return h + '<div class="cs-empty">Loading studio…</div></div>';
  if (!CS.cur) return h + '<div class="cs-empty">Pick a drink on the left.</div></div>';
  var d = CS.cur, v = CS.draft, g = csGlass() || {}, b = d.balance || {}, c = d.cost || {};
  h += '<div class="cs-head"><div><div class="cs-kick">' + csE(d.status || 'draft') + (CS.demo ? ' · demo' : '') + '</div><h2>' + csE(d.name) + '</h2>' +
       '<div class="cs-sub">' + csE(g.name || '') + ' · ' + csE(v.serve || '') + '</div></div>' +
       '<div class="cs-actions"><button class="btn" onclick="csRequestRender()">Photoreal render</button>' +
       '<button class="btn" onclick="csSaveVisuals()"' + (CS.demo ? ' disabled title="Demo data"' : '') + '>Save visuals</button>' +
       '<button class="btn" onclick="csToMenuStudio()"' + (CS.demo ? ' disabled' : '') + '>Send to Menu Studio</button></div></div>';

  h += '<div class="cs-grid"><div class="cs-stage"><div id="csCanvas"></div>' +
       '<div class="cs-stage-note">' + (g.verification_status === 'unverified' ? '<span class="cs-badge warn">approximate dimensions</span>' : '<span class="cs-badge">' + csE(g.verification_status || '') + '</span>') +
       (CS.renderJob ? ' <span class="cs-badge">render: ' + csE(CS.renderJob.status) + '</span>' : '') + '</div>' +
       (CS.renderJob && CS.renderJob.png_url ? '<img class="cs-render" src="' + csE(CS.renderJob.png_url) + '">' : '') + '</div>';

  // controls
  h += '<div class="cs-panel"><h3>Build</h3>' + csControls() ;
  var w = csWarnings(); if (w.length) h += '<div class="cs-warn">' + w.map(csE).join('<br>') + '</div>';
  h += '</div></div>';

  // recipe / balance / cost / stock
  h += '<div class="cs-cards">';
  h += '<div class="cs-card"><h3>Recipe</h3><table class="cs-t"><tr><th>Ingredient</th><th>Qty</th><th>On hand</th></tr>' +
       (d.components || []).map(function(x){ return '<tr><td>' + csE(x.name) + '</td><td>' + csE(x.quantity + ' ' + x.unit) + '</td><td>' +
         (x.on_hand == null ? '<span class="cs-mute">—</span>' : csE(x.on_hand + ' ' + (x.on_hand_unit || ''))) + '</td></tr>'; }).join('') +
       '</table><div class="cs-method">' + csE(d.method || '') + '</div></div>';
  h += '<div class="cs-card"><h3>Balance</h3><div class="cs-kv">' +
       csKV('Final ABV', b.abv_finished == null ? '—' : Number(b.abv_finished).toFixed(1) + '%') +
       csKV('Sugar', b.sugar_g_100ml == null ? '—' : Number(b.sugar_g_100ml).toFixed(1) + ' g/100 ml') +
       csKV('Acid', b.ta_g_100ml == null ? '—' : Number(b.ta_g_100ml).toFixed(2) + ' g/100 ml') +
       csKV('Dilution', csPct(b.dilution_pct)) + csKV('Volume', (b.finished_volume_ml || v.finished_volume_ml || '—') + ' ml') + '</div>' +
       (b.input_coverage_pct != null && b.input_coverage_pct < 100 ? '<div class="cs-mute">Inputs ' + csPct(b.input_coverage_pct) + ' covered — numbers partial</div>' : '') + '</div>';
  var pc = c.pour_cost_pct, pcCls = pc == null ? '' : (pc > 22 ? ' bad' : pc < 18 ? ' low' : ' ok');
  h += '<div class="cs-card"><h3>Cost</h3><div class="cs-kv">' + csKV('Recipe cost', csMoney(c.recipe_cost)) + csKV('Menu price', csMoney(c.menu_price)) +
       '<div class="cs-kvr"><span>Pour cost</span><b class="cs-pc' + pcCls + '">' + csPct(pc) + '</b></div>' +
       csKV('Target', '18–22%') + '</div>' + ((c.missing || []).length ? '<div class="cs-mute">Missing cost: ' + csE(c.missing.join(', ')) + '</div>' : '') +
       '<button class="btn sm" disabled title="Needs purchase_orders tables (Backend Lead DEV)">Draft order for low stock</button></div>';
  h += '<div class="cs-card"><h3>Allergens</h3>' + ((d.allergens || []).length ? csE(d.allergens.join(', ')) : '<span class="cs-mute">None declared</span>') + '</div>';
  h += '</div></div>';
  setTimeout(csMount, 0);
  return h;
}
function csKV(k, v){ return '<div class="cs-kvr"><span>' + csE(k) + '</span><b>' + csE(v) + '</b></div>'; }

function csControls(){
  var v = CS.draft, h = '';
  h += csRow('Glass', '<select onchange="csSet(\'glassware_id\',this.value)">' + CS.glassware.map(function(g){
    return '<option value="' + csE(g.id || g.glass_key) + '"' + ((g.id || g.glass_key) === v.glassware_id ? ' selected' : '') + '>' + csE(g.name) + '</option>'; }).join('') + '</select>');
  h += csRow('Serve', '<select onchange="csSetServe(this.value)">' + Object.keys(CS_SERVE).map(function(k){
    return '<option' + (k === v.serve ? ' selected' : '') + '>' + k + '</option>'; }).join('') + '</select>');
  h += csRow('Ice', '<select onchange="csSetIce(this.value)">' + ['none','large_cube','sphere','cubes','spear','crushed'].map(function(k){
    return '<option' + (v.ice && k === v.ice.type ? ' selected' : '') + '>' + k + '</option>'; }).join('') + '</select>');
  h += csRow('Volume ml', '<input type="number" min="10" max="700" value="' + csE(v.finished_volume_ml) + '" oninput="csSet(\'finished_volume_ml\',+this.value,1)">');
  h += csRow('Colour', '<input type="color" value="' + csE(v.liquid.color_hex) + '" oninput="csSetLiquid(\'color_hex\',this.value)">');
  h += csRow('Clarity', '<input type="range" min="0" max="1" step="0.05" value="' + csE(v.liquid.clarity) + '" oninput="csSetLiquid(\'clarity\',+this.value)">');
  h += csRow('Foam mm', '<input type="number" min="0" max="25" value="' + csE(v.liquid.foam_mm || 0) + '" oninput="csSetLiquid(\'foam_mm\',+this.value)">');
  h += '<h4>Garnish</h4>';
  (v.garnish || []).forEach(function(x, i){
    h += '<div class="cs-gar"><select onchange="csGar(' + i + ',\'type\',this.value)">' + CS_GARNISH.map(function(t){ return '<option' + (t === x.type ? ' selected' : '') + '>' + t + '</option>'; }).join('') + '</select>' +
         '<input type="number" min="1" max="12" value="' + (x.count || 1) + '" oninput="csGar(' + i + ',\'count\',+this.value)">' +
         (x.type === 'drops'
           ? '<select onchange="csGar(' + i + ',\'liquid\',this.value)">' + CS_DROPS.map(function(t){ return '<option' + (t === x.liquid ? ' selected' : '') + '>' + t + '</option>'; }).join('') + '</select>'
           : '<select onchange="csGar(' + i + ',\'placement\',this.value)">' + CS_PLACE.map(function(t){ return '<option' + (t === x.placement ? ' selected' : '') + '>' + t + '</option>'; }).join('') + '</select>') +
         '<button class="btn sm" onclick="csGarDel(' + i + ')">×</button></div>';
  });
  h += '<button class="btn sm" onclick="csGarAdd()">+ garnish</button>';
  return h;
}
function csRow(k, ctl){ return '<label class="cs-row"><span>' + k + '</span>' + ctl + '</label>'; }

/* ---------------------------------------------------------------- edits: update draft, rebuild 3D only (no full re-render while typing) */
function csSet(k, val, live){ CS.draft[k] = val; if (live) csBuild(); else render(); }
function csSetLiquid(k, val){ CS.draft.liquid[k] = val; csBuild(); }
function csSetServe(s){ CS.draft.serve = s; CS.draft.ice = JSON.parse(JSON.stringify(CS_SERVE[s].ice)); render(); }
function csSetIce(t){ CS.draft.ice = {type: t, count: t === 'cubes' ? 0 : 1}; render(); }
function csGar(i, k, val){ CS.draft.garnish[i][k] = val; if (k === 'type' && val === 'drops'){ CS.draft.garnish[i].liquid = 'angostura'; CS.draft.garnish[i].placement = 'surface'; } render(); }
function csGarAdd(){ CS.draft.garnish.push({type: 'cherry', count: 1, placement: 'dropped'}); render(); }
function csGarDel(i){ CS.draft.garnish.splice(i, 1); render(); }

function csSaveVisuals(){
  csCall('save_visuals', {recipe_version_id: CS.cur.recipe_version_id, visuals: CS.draft}, function(err){
    CS.error = err ? 'Save failed: ' + err : null; if (!err) CS.cur.visuals = JSON.parse(JSON.stringify(CS.draft)); render(); });
}
function csRequestRender(){
  if (CS.demo){ CS.error = 'Demo data: photoreal renders need phg-cocktail-studio + the Hetzner worker.'; render(); return; }
  csCall('request_render', {recipe_version_id: CS.cur.recipe_version_id, visuals: CS.draft, kind: 'hero'}, function(err, j){
    if (err){ CS.error = 'Render request failed: ' + err; render(); return; }
    CS.renderJob = j; render(); csPollRender();
  });
}
function csPollRender(){  // Realtime broadcast is the plan (brief 4c); polling is the fallback
  if (!CS.renderJob || CS.renderJob.status === 'done' || CS.renderJob.status === 'failed') return;
  setTimeout(function(){ csCall('get_render', {job_id: CS.renderJob.id}, function(err, j){ if (!err){ CS.renderJob = j; if (APP === 'studio') render(); } csPollRender(); }); }, 4000);
}
function csToMenuStudio(){
  csCall('send_to_menu_studio', {recipe_version_id: CS.cur.recipe_version_id}, function(err, j){
    CS.error = err ? 'Could not send: ' + err : 'Sent to Menu Studio as draft (needs approval).'; render(); });
}

/* ---------------------------------------------------------------- three.js live viewer */
function csMount(){
  var el = document.getElementById('csCanvas'); if (!el) return;
  if (CS.three && CS.three.el === el){ csBuild(); return; }
  import('https://esm.sh/three@0.169.0').then(function(THREE){
    return import('https://esm.sh/three@0.169.0/examples/jsm/controls/OrbitControls.js').then(function(oc){
      return import('https://esm.sh/three@0.169.0/examples/jsm/environments/RoomEnvironment.js').then(function(re){ return [THREE, oc, re]; }); });
  }).then(function(m){
    var THREE = m[0], el2 = document.getElementById('csCanvas'); if (!el2) return;
    var w = el2.clientWidth || 520, h = el2.clientHeight || 600;
    var renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); renderer.setSize(w, h);
    renderer.toneMapping = THREE.AgXToneMapping; renderer.toneMappingExposure = 0.9;
    el2.innerHTML = ''; el2.appendChild(renderer.domElement);
    var scene = new THREE.Scene();
    var pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new m[2].RoomEnvironment(), 0.04).texture;
    var camera = new THREE.PerspectiveCamera(30, w / h, 0.005, 5);
    var controls = new m[1].OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
    var key = new THREE.DirectionalLight(0xffffff, 0.8); key.position.set(-0.4, 0.6, 0.5); scene.add(key);
    var back = new THREE.DirectionalLight(0xffe8cc, 1.5); back.position.set(0, 0.3, -0.6); scene.add(back);
    var floor = new THREE.Mesh(new THREE.CircleGeometry(0.4, 64), new THREE.MeshStandardMaterial({color: 0x050404, roughness: 1, envMapIntensity: 0.05}));
    floor.rotation.x = -Math.PI / 2; scene.add(floor);
    CS.three = {THREE: THREE, renderer: renderer, scene: scene, camera: camera, controls: controls, group: null, el: el2};
    window.addEventListener('resize', function(){ var e = document.getElementById('csCanvas'); if (!e || !CS.three) return;
      CS.three.renderer.setSize(e.clientWidth, e.clientHeight); CS.three.camera.aspect = e.clientWidth / e.clientHeight; CS.three.camera.updateProjectionMatrix(); });
    (function loop(){ if (!CS.three || !document.getElementById('csCanvas')){ if (CS.three){ CS.three.renderer.dispose(); CS.three = null; } return; }
      requestAnimationFrame(loop); CS.three.controls.update(); CS.three.renderer.render(CS.three.scene, CS.three.camera); })();
    csBuild();
  }).catch(function(e){ var el3 = document.getElementById('csCanvas'); if (el3) el3.innerHTML = '<div class="cs-empty">3D viewer failed to load: ' + csE(e.message) + '</div>'; });
}

function csFillHeight(g, ml){  // fill_curve from the DB trigger: [{ml,h_mm}]
  var fc = g.fill_curve || []; if (!fc.length) return 0;
  for (var i = 1; i < fc.length; i++) if (fc[i].ml >= ml){ var a = fc[i - 1], b = fc[i]; return a.h_mm + (b.h_mm - a.h_mm) * (ml - a.ml) / Math.max(b.ml - a.ml, 1e-6); }
  return fc[fc.length - 1].h_mm;
}
function csIceMl(ice, g){
  var t = ice && ice.type; if (!t || t === 'none') return 0;
  if (t === 'large_cube') return 112; if (t === 'sphere') return 78; if (t === 'spear') return 22 * 22 * g.inner_profile[g.inner_profile.length - 1].h_mm * 0.72 / 1000;
  if (t === 'crushed') return g.capacity_ml * 0.45; return (ice.count || Math.max(3, Math.floor(g.capacity_ml * 0.6 / 15.6 / 0.85))) * 14;
}

function csBuild(){
  var T = CS.three; if (!T || !CS.draft) return; var THREE = T.THREE, g = csGlass(); if (!g || !g.inner_profile) return;
  if (T.group){ T.scene.remove(T.group); T.group.traverse(function(o){ if (o.geometry) o.geometry.dispose(); }); }
  var grp = new THREE.Group(), MM = 0.001, v = CS.draft, prof = g.inner_profile, wall = g.wall_thickness_mm || 2;
  var depth = prof[prof.length - 1].h_mm, z0 = g.height_mm - depth, stem = !!CS_STEMMED[g.family], foot = (g.foot_diameter_mm || g.max_diameter_mm * 0.8) / 2;
  // glass: outer up, lip, inner down (same construction as the Blender builder)
  var pts = [];
  if (stem){ pts.push([0, 0], [foot, 0], [foot, 1.2], [foot - 2, 3], [8, 6], [3.8, 13], [3.8, z0 - 8], [6.8, z0 - 2]); }
  else { pts.push([0, 0], [foot - 1.5, 0], [foot, 1.5]); }
  prof.forEach(function(p, i){ if (!stem && i === 0 && p.r_mm < foot * 0.5) return; pts.push([Math.max(p.r_mm + wall, stem ? wall * 1.5 : 0), z0 + p.h_mm]); });
  var rimIn = prof[prof.length - 1].r_mm; pts.push([rimIn + wall / 2, g.height_mm + wall * 0.35]);
  for (var i = prof.length - 1; i >= 0; i--) pts.push([prof[i].r_mm, z0 + prof[i].h_mm]);
  // three.js cannot show a transmissive object through another transmissive one, so the glass is a clear-coated
  // transparent shell and the LIQUID carries the transmission/absorption (the part that must look right).
  var glassMat = new THREE.MeshPhysicalMaterial({color: 0xffffff, metalness: 0, roughness: 0.03, transmission: 0, transparent: true, opacity: 0.16,
    clearcoat: 1, clearcoatRoughness: 0.02, envMapIntensity: 1.6, ior: 1.52, side: THREE.DoubleSide, depthWrite: false});
  grp.add(new THREE.Mesh(new THREE.LatheGeometry(pts.map(function(p){ return new THREE.Vector2(p[0] * MM, p[1] * MM); }), 96), glassMat));
  // liquid
  var fillH = csFillHeight(g, Math.min(Number(v.finished_volume_ml) + csIceMl(v.ice, g), g.capacity_ml * 0.97));
  var lp = [], rAt = function(h){ for (var k = 1; k < prof.length; k++) if (prof[k].h_mm >= h){ var a = prof[k - 1], b = prof[k]; return a.r_mm + (b.r_mm - a.r_mm) * (h - a.h_mm) / Math.max(b.h_mm - a.h_mm, 1e-6); } return rimIn; };
  prof.forEach(function(p){ if (p.h_mm < fillH) lp.push(new THREE.Vector2(Math.max(p.r_mm - 0.2, 0) * MM, (z0 + p.h_mm) * MM)); });
  var rTop = rAt(fillH) - 0.2; lp.push(new THREE.Vector2(rTop * MM, (z0 + fillH) * MM), new THREE.Vector2(0, (z0 + fillH - 0.8) * MM));
  var col = new THREE.Color(v.liquid.color_hex), clar = Number(v.liquid.clarity);
  var liqMat = new THREE.MeshPhysicalMaterial({color: clar > 0.5 ? col.clone().lerp(new THREE.Color(0xffffff), 0.25) : col, roughness: clar > 0.8 ? 0.02 : 0.3,
    transmission: clar, thickness: 0.06, attenuationColor: col, attenuationDistance: 0.015 + clar * 0.035, ior: 1.36, envMapIntensity: 0.8});
  grp.add(new THREE.Mesh(new THREE.LatheGeometry(lp, 96), liqMat));
  var surf = (z0 + fillH) * MM;
  if (v.liquid.foam_mm){ var fm = new THREE.Mesh(new THREE.CylinderGeometry((rTop - 2) * MM, (rTop - 0.4) * MM, v.liquid.foam_mm * MM, 64), new THREE.MeshStandardMaterial({color: 0xf3ecdc, roughness: 0.9}));
    fm.position.y = surf + v.liquid.foam_mm * MM / 2; grp.add(fm); surf += v.liquid.foam_mm * MM; }
  // ice
  var iceMat = new THREE.MeshPhysicalMaterial({color: 0xf4fbff, roughness: 0.12, transparent: true, opacity: 0.38, clearcoat: 1, envMapIntensity: 1.4, depthWrite: false});
  var it = v.ice && v.ice.type;
  if (it === 'large_cube'){ var s = Math.min(50, rTop * 1.35); var c = new THREE.Mesh(new THREE.BoxGeometry(s * MM, s * MM, s * MM), iceMat); c.position.y = (z0 + 1 + s / 2) * MM; c.rotation.y = 0.3; grp.add(c); }
  else if (it === 'sphere'){ var sp = new THREE.Mesh(new THREE.SphereGeometry(27.5 * MM, 48, 24), iceMat); sp.position.y = surf - 22 * MM; grp.add(sp); }
  else if (it === 'spear'){ var L = depth * 0.85; var spr = new THREE.Mesh(new THREE.BoxGeometry(22 * MM, L * MM, 22 * MM), iceMat); spr.position.y = (z0 + 1 + L / 2) * MM; grp.add(spr); }
  else if (it === 'cubes' || it === 'crushed'){
    var sz = it === 'cubes' ? 25 : 9, n = it === 'cubes' ? (v.ice.count || 99) : 220, top = it === 'crushed' ? g.height_mm + 8 : Math.min(z0 + fillH + 4, g.height_mm - sz * 0.45), z = z0 + sz / 2 + 1, made = 0, seed = 7;
    var rnd = function(){ seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
    while (made < n && z < top){ var rh = rAt(z - z0) - sz * 0.62, per = rh > sz * 0.4 ? Math.max(1, Math.floor(2 * Math.PI * rh / (sz * 1.15))) : 1;
      for (var q = 0; q < per && made < n; q++){ var a = 2 * Math.PI * q / per + z * 0.13, rr = per > 1 ? rh : 0;
        var cube = new THREE.Mesh(new THREE.BoxGeometry(sz * MM, sz * MM, sz * MM), iceMat); cube.position.set(rr * Math.cos(a) * MM, z * MM, rr * Math.sin(a) * MM);
        cube.rotation.set(rnd() - 0.5, rnd() - 0.5, rnd() - 0.5); grp.add(cube); made++; }
      z += sz * 0.9; }
  }
  csGarnish(THREE, grp, v.garnish || [], {MM: MM, rimR: rimIn + wall / 2, rimZ: g.height_mm * MM, surf: surf, rTop: rTop, z0: z0, rAt: rAt});
  T.scene.add(grp); T.group = grp;
  var hgt = g.height_mm * MM, top = (v.garnish || []).some(function(x){ return x.type === 'drops' || x.placement === 'float'; });
  T.camera.position.set(0, hgt * (top ? 1.9 : 0.75), hgt * (top ? 2.5 : 3.2)); T.controls.target.set(0, hgt * (top ? 0.75 : 0.55), 0); T.controls.update();
}

function csGarnish(THREE, grp, items, k){
  var MM = k.MM, M = function(hex, r, extra){ return new THREE.MeshPhysicalMaterial(Object.assign({color: hex, roughness: r}, extra || {})); };
  var mats = {cherry: M(0x4a0408, 0.12, {clearcoat: 1}), orange: M(0xe8730a, 0.5), lemon: M(0xe8c418, 0.5), lime: M(0x3f7d1a, 0.5),
              flesh_orange: M(0xf59a2a, 0.35), flesh_lemon: M(0xf6e27a, 0.35), flesh_lime: M(0xa8cf4a, 0.35), olive: M(0x5a6b1e, 0.25, {clearcoat: 0.6}),
              mint: M(0x2c7a24, 0.5), pick: M(0xc9a066, 0.7)};
  var flat = []; items.forEach(function(x){ for (var i = 0; i < (x.count || 1); i++) flat.push(x); });
  var fruit = function(t){ return t.split('_')[0]; };
  function citrus(t, half){ var f = fruit(t), r = {orange: 34, lemon: 28, lime: 24}[f] || 30;
    var geo = new THREE.CylinderGeometry(r * MM, r * MM, 6 * MM, 48, 1, false, 0, half ? Math.PI : Math.PI * 2);
    var m = new THREE.Mesh(geo, [mats[f], mats['flesh_' + f], mats['flesh_' + f]]); m.rotation.x = Math.PI / 2; var o = new THREE.Group(); o.add(m); return o; }
  function make(x){ var t = x.type, o;
    if (t === 'cherry'){ o = new THREE.Mesh(new THREE.SphereGeometry(11 * MM, 32, 16), mats.cherry); }
    else if (t === 'olive'){ o = new THREE.Mesh(new THREE.SphereGeometry(9 * MM, 24, 12), mats.olive); o.scale.y = 1.3; }
    else if (/half_moon$/.test(t)) o = citrus(t, true);
    else if (/wheel$/.test(t)) o = citrus(t, false);
    else if (/wedge$/.test(t)){ var f = fruit(t); o = new THREE.Mesh(new THREE.SphereGeometry(26 * MM, 16, 16, 0, Math.PI / 4), [mats[f]]); o.scale.y = 1.25; }
    else if (/(peel|twist)$/.test(t)){ var f2 = fruit(t); o = new THREE.Mesh(/twist$/.test(t) ? new THREE.TorusKnotGeometry(6 * MM, 1.5 * MM, 64, 6, 1, 6) : new THREE.BoxGeometry(62 * MM, 1.6 * MM, 22 * MM), mats[f2]); }
    else if (t === 'mint_sprig'){ o = new THREE.Group(); for (var i = 0; i < 8; i++){ var lf = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), mats.mint); lf.scale.set(15 * MM, 1.2 * MM, 7 * MM);
        lf.position.set(Math.cos(i * 2.4) * 9 * MM, (i * 4) * MM, Math.sin(i * 2.4) * 9 * MM); lf.rotation.set(0.5, i * 2.4, 0.3); o.add(lf); } }
    return o; }
  // pick: all pick items on one pick, in list order
  var onPick = flat.filter(function(x){ return x.placement === 'pick'; });
  if (onPick.length){ var tilt = 68 * Math.PI / 180, L = Math.max(90, k.rimR * 2.7);
    var pick = new THREE.Mesh(new THREE.CylinderGeometry(1.4 * MM, 1.4 * MM, L * MM, 8), mats.pick);
    var piv = new THREE.Vector3(-k.rimR * MM, k.rimZ + 1.5 * MM, 0), d = new THREE.Vector3(Math.sin(tilt), -Math.cos(tilt), 0);
    pick.position.copy(piv.clone().add(d.clone().multiplyScalar((L / 2 - 30) * MM))); pick.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d); grp.add(pick);
    var pos = 14; onPick.forEach(function(x){ var o = make(x); if (!o) return; var s = (x.type === 'cherry' || x.type === 'olive') ? 22 : 30; pos += s * 0.55;
      o.position.copy(piv.clone().add(d.clone().multiplyScalar(pos * MM))); if (s === 30) o.rotation.z = Math.PI / 2 - tilt; pos += s * 0.55; grp.add(o); }); }
  var nRim = 0, nWall = 0, nDrape = 0, nDrop = 0, nMint = 0;
  flat.forEach(function(x){ var o, a;
    if (x.placement === 'pick' || x.type === 'drops') return;
    o = make(x); if (!o) return;
    if (x.placement === 'rim'){ a = (318 - 34 * nRim++) * Math.PI / 180; o.position.set(k.rimR * Math.cos(a) * MM, k.rimZ - 12 * MM, -k.rimR * Math.sin(a) * MM); o.rotation.y = a; }
    else if (x.placement === 'inside_wall'){ a = (240 + 62 * nWall++) * Math.PI / 180; var rr = k.rAt(((k.surf / MM) - k.z0) * 0.55) - 4; o.scale.setScalar(Math.min(1, rr * 0.95 / 34));
      o.position.set(rr * Math.cos(a) * MM, ((k.surf / MM - k.z0) * 0.55 + k.z0 - 12) * MM, -rr * Math.sin(a) * MM); o.rotation.y = a + Math.PI / 2; }
    else if (x.placement === 'drape'){ a = (35 - 50 * nDrape++) * Math.PI / 180; o.position.set(k.rimR * 0.95 * Math.cos(a) * MM, k.rimZ - 4 * MM, -k.rimR * 0.95 * Math.sin(a) * MM); o.rotation.set(0.17, a, -0.84); }
    else if (x.placement === 'dropped'){ o.position.set((nDrop++ * 9) * MM, (k.z0 + 11) * MM, 0); }
    else { if (x.type === 'mint_sprig'){ a = nMint++ * 1.6; o.position.set(Math.cos(a) * 9 * MM, k.surf - 4 * MM, Math.sin(a) * 9 * MM); } else { o.position.y = k.surf + MM; o.rotation.x = Math.PI / 2; } }
    grp.add(o); });
  // drops: bitters dots / oil lenses on the surface (foam top if present)
  flat.filter(function(x){ return x.type === 'drops'; }).forEach(function(x){
    var oil = /oil/.test(x.liquid || ''), dmm = oil ? 5 : 7.5, n = x.count || 1;
    var mat = oil ? M(0xd9c060, 0, {transmission: 0.85, ior: 1.47, transparent: true}) : M(x.liquid === 'peychauds' ? 0x8c0508 : 0x2a0503, 0.15);
    for (var i = 0; i < n; i++){ var px = oil ? (Math.cos(i * 2.39996) * Math.sqrt(i / n) * k.rTop * 0.7) : (-dmm * 1.8 * (n - 1) / 2 + i * dmm * 1.8);
      var pz = oil ? (Math.sin(i * 2.39996) * Math.sqrt(i / n) * k.rTop * 0.7) : 0;
      var dr = new THREE.Mesh(new THREE.SphereGeometry(dmm / 2 * MM, 16, 8), mat); dr.scale.y = oil ? 0.35 : 0.18; dr.position.set(px * MM, k.surf + 0.3 * MM, pz * MM); grp.add(dr); } });
}
