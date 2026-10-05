"""
PHG glassware seed builder (proposal v1).
Published dimensions come from spec-sheet data (manufacturer/dealer listings, URLs per row).
Profiles are FITTED from family templates: one unpublished parameter per glass
(bowl depth for stemware, base thickness for tumblers) is solved so the brimful
volume of the revolved inner profile equals the published capacity.
Result: verification_status = 'spec_sheet' for dimensions; the profile shape is a model -> flagged in notes.
"""
import json, math
IN = 25.4; OZ = 29.5735
WALL = 1.6  # mm assumed wall thickness (stemware thin, tumblers heavier set per row)

def vol(profile):  # frustum sum, profile [(r,h)] ascending h, mm -> ml
    v = 0.0
    for (r1,h1),(r2,h2) in zip(profile, profile[1:]):
        v += math.pi*(h2-h1)/3*(r1*r1+r1*r2+r2*r2)
    return v/1000

def fill_curve(profile, step_ml=5):
    out=[]; total=vol(profile); target=0.0
    while target <= total+1e-9:
        lo,hi=profile[0][1],profile[-1][1]
        for _ in range(60):
            mid=(lo+hi)/2
            if vol(clip(profile,mid))<target: lo=mid
            else: hi=mid
        out.append({"ml":round(target,1),"h_mm":round(hi-profile[0][1],2)})
        target+=step_ml
    out.append({"ml":round(total,1),"h_mm":round(profile[-1][1]-profile[0][1],2)})
    return out

def clip(p,h):
    q=[p[0]]
    for (r1,h1),(r2,h2) in zip(p,p[1:]):
        if h2<=h: q.append((r2,h2))
        else:
            if h>h1: q.append((r1+(r2-r1)*(h-h1)/(h2-h1),h)); 
            break
    return q

def solve(fn, target_ml, lo, hi):
    for _ in range(80):
        mid=(lo+hi)/2
        if vol(fn(mid))<target_ml: lo=mid
        else: hi=mid
    return (lo+hi)/2

N=24
# ---- templates: each returns inner profile [(r_mm, h_mm)] with h measured from glass bottom (table)
def tumbler(g, wall):
    rb=g["bottom_d"]*IN/2-wall; rt=g["top_d"]*IN/2-wall; H=g["height"]*IN
    def f(base):  # straight taper from base to rim
        return [(0,base)]+[(rb+(rt-rb)*i/N, base+(H-base)*i/N) for i in range(N+1)]
    return f
def nick_nora(g, wall):  # rounded bell: r = Rtop * sqrt(t) near bottom, near-vertical at rim
    rt=g["top_d"]*IN/2-wall; H=g["height"]*IN
    def f(depth):
        b=H-depth
        return [(rt*math.sin(math.pi/2*(i/N))**0.9, b+depth*(1-math.cos(math.pi/2*i/N))) for i in range(N+1)] if False else \
               [(rt*math.sin(math.pi/2*(i/N))**0.55, b+depth*(i/N)) for i in range(N+1)]
    return f
def coupe(g, wall):  # shallow round bowl swelling to max diameter then turning in to the rim
    rt=g["top_d"]*IN/2-wall; rm=g["max_d"]*IN/2-wall; H=g["height"]*IN; tm=0.72
    def f(depth):
        b=H-depth; pts=[]
        for i in range(N+1):
            t=i/N
            r = rm*math.sin(math.pi/2*t/tm) if t<=tm else rm+(rt-rm)*((t-tm)/(1-tm))**1.5
            pts.append((r, b+depth*t))
        return pts
    return f

GLASSES=[
 dict(glass_key="libbey_9252_circa_nick_nora_5_5oz", name="Libbey Reserve Circa Nick & Nora 5.5 oz", family="nick_and_nora",
      manufacturer="Libbey (Reserve by Libbey)", sku="9252", cap_oz=5.5, height=6, top_d=3, max_d=3, bottom_d=2.625,
      tpl="nick_nora", wall=1.5, fit=("bowl_depth_mm",40,140),
      src="https://www.katom.com/634-9252.html", corroborated="https://www.don.com/product/1159068"),
 dict(glass_key="libbey_3055_perception_coupe_8_5oz", name="Libbey Perception Cocktail Coupe 8.5 oz", family="coupe",
      manufacturer="Libbey", sku="3055", cap_oz=8.5, height=6, top_d=3.75, max_d=4.125, bottom_d=3,
      tpl="coupe", wall=1.6, fit=("bowl_depth_mm",25,110),
      src="https://www.webstaurantstore.com/libbey-3055-perception-8-5-oz-cocktail-coupe-glass-case/5513055.html", corroborated="https://www.gofoodservice.com/p/libbey-3055"),
 dict(glass_key="libbey_918cd_heavy_base_dof_13_5oz", name="Libbey Heavy Base Double Old Fashioned 13.5 oz", family="double_rocks",
      manufacturer="Libbey", sku="918CD", cap_oz=13.5, height=4.25, top_d=3.375, max_d=3.375, bottom_d=3.125,
      tpl="tumbler", wall=2.5, fit=("base_thickness_mm",3,40),
      src="https://www.restaurantsupply.com/libbey-918cd-heavy-base-13-5-oz-double-rocks-old-fashioned-glass", corroborated="https://shop.libbey.com/products/libbey-heavy-base-double-old-fashioned-glasses-13-5-ounce-set-of-12"),
 dict(glass_key="libbey_125_heavy_base_highball_9oz", name="Libbey Heavy Base Highball 9 oz", family="highball",
      manufacturer="Libbey", sku="125", cap_oz=9, height=4.75, top_d=2.75, max_d=2.75, bottom_d=2.25,
      tpl="tumbler", wall=2.2, fit=("base_thickness_mm",3,40),
      src="https://bargreen.com/products/LIB125", corroborated="https://www.amazon.com/Libbey-Heavy-Ounce-Highball-Glass/dp/B00CHUKVYG"),
 dict(glass_key="libbey_2518_chicago_collins_10_5oz", name="Libbey Chicago Tall Hi-Ball / Collins 10.5 oz", family="collins",
      manufacturer="Libbey", sku="2518", cap_oz=10.5, height=6.625, top_d=2.375, max_d=2.375, bottom_d=2.125,
      tpl="tumbler", wall=1.8, fit=("base_thickness_mm",3,40),
      src="https://www.katom.com/634-2518.html", corroborated=None),
 dict(glass_key="libbey_1639ht_pint_mixing_16oz", name="Libbey Restaurant Basics Pint / Mixing Glass 16 oz", family="pint",
      manufacturer="Libbey", sku="1639HT", cap_oz=16, height=5.875, top_d=3.5, max_d=3.5, bottom_d=2.375,
      tpl="tumbler", wall=2.4, fit=("base_thickness_mm",3,40),
      src="https://www.webstaurantstore.com/libbey-1639ht-restaurant-basics-16-oz-mixing-glass-case/5511639HT.html", corroborated="https://eastbayrestaurantsupply.com/products/cck1639ht"),
]
PLAUSIBLE={"base_thickness_mm":(5,25),"bowl_depth_mm":(35,110)}
TPL={"tumbler":tumbler,"nick_nora":nick_nora,"coupe":coupe}

rows=[]
for g in GLASSES:
    cap=g["cap_oz"]*OZ
    f=TPL[g["tpl"]](g,g["wall"])
    pname,lo,hi=g["fit"]
    p=solve(f,cap,lo,hi) if g["tpl"]!="tumbler" else None
    if g["tpl"]=="tumbler":
        # more base -> less volume: invert search
        a,b=lo,hi
        for _ in range(80):
            m=(a+b)/2
            if vol(f(m))>cap: a=m
            else: b=m
        p=(a+b)/2
    prof=f(p); base_h=prof[0][1]
    inner=[{"r_mm":round(r,2),"h_mm":round(h-base_h,2)} for r,h in prof]
    v=vol(prof); pl=PLAUSIBLE[pname]; ok=pl[0]<=p<=pl[1]
    stem = None if g["tpl"]=="tumbler" else round(g["height"]*IN-p,1)
    rows.append(dict(
        glass_key=g["glass_key"], name=g["name"], family=g["family"], manufacturer=g["manufacturer"], manufacturer_sku=g["sku"],
        capacity_ml=round(cap,1), height_mm=round(g["height"]*IN,1), rim_diameter_mm=round(g["top_d"]*IN,1),
        max_diameter_mm=round(g["max_d"]*IN,1), foot_diameter_mm=round(g["bottom_d"]*IN,1),
        wall_thickness_mm=g["wall"], base_thickness_mm=round(p,1) if g["tpl"]=="tumbler" else round(stem,1),
        inner_profile=inner, fill_curve=fill_curve(prof),
        source_url=g["src"], verification_status="spec_sheet" if ok else "unverified",
        fit={"param":pname,"value_mm":round(p,1),"plausible_range_mm":pl,"plausible":ok,"model_volume_ml":round(v,1),"template":g["tpl"]},
        notes=(f"Dimensions from spec sheet ({g['src']}"+(f"; corroborated {g['corroborated']}" if g['corroborated'] else "")+"). "
               f"Capacity is brimful; Libbey states individual pieces may vary up to 5%. "
               f"Inner profile is a '{g['tpl']}' template fitted by solving {pname}={p:.1f} mm to match capacity; wall thickness {g['wall']} mm assumed. "
               f"{'Stem+foot height implied ' + str(stem) + ' mm. ' if stem else ''}Shape is a model, not a trace - upgrade to measured when the glass is in house.")
    ))
json.dump(rows,open("glassware_seed_v1.json","w"),indent=1)

def q(s): return "null" if s is None else "'"+str(s).replace("'","''")+"'"
sql=["-- PROPOSAL ONLY. Not applied. Review, then run as migration 'glassware_seed_v1'.","begin;"]
for r in rows:
    sql.append(f"""insert into phg.glassware (glass_key,name,family,manufacturer,manufacturer_sku,capacity_ml,height_mm,rim_diameter_mm,max_diameter_mm,foot_diameter_mm,wall_thickness_mm,base_thickness_mm,inner_profile,fill_curve,source_url,verification_status,notes)
values ({q(r['glass_key'])},{q(r['name'])},{q(r['family'])},{q(r['manufacturer'])},{q(r['manufacturer_sku'])},{r['capacity_ml']},{r['height_mm']},{r['rim_diameter_mm']},{r['max_diameter_mm']},{r['foot_diameter_mm']},{r['wall_thickness_mm']},{r['base_thickness_mm']},{q(json.dumps(r['inner_profile']))}::jsonb,{q(json.dumps(r['fill_curve']))}::jsonb,{q(r['source_url'])},{q(r['verification_status'])},{q(r['notes'])})
on conflict do nothing;""")
sql.append("commit;")
open("glassware_seed_v1.sql","w").write("\n".join(sql))
for r in rows: print(r["glass_key"], r["capacity_ml"], r["fit"])
