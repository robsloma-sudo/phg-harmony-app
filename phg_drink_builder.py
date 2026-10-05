"""
PHG Drink Builder (Blender, headless)
=====================================
Builds a photoreal cocktail from a PHG drink spec JSON: glass (from phg.glassware profile),
liquid at the correct fill height (ml -> height via the glass fill curve, ice displacement included),
ice, and a composable garnish stack. Renders PNG (Cycles) and exports GLB for the web viewer.

Run:  blender -b -P phg_drink_builder.py -- spec.json out_dir
  or  python3 phg_drink_builder.py spec.json out_dir      (with the `bpy` pip wheel)

Garnish grammar (list, order matters on a pick: first item goes on first):
  {"type": "cherry"|"orange_half_moon"|"lemon_half_moon"|"lime_half_moon"|"orange_wheel"|"lemon_wheel"|
           "lime_wheel"|"lime_wedge"|"lemon_wedge"|"orange_peel"|"lemon_peel"|"lime_peel"|"mint_sprig"|"olive",
   "count": 1..n,
   "placement": "pick" | "rim" | "dropped" | "float" | "drape" | "inside_wall"}
Examples: 1 cherry dropped; 2 cherries on a pick; orange half moon + cherry on a pick ("flag");
          2 orange half moons on the rim + lime peel drape; lime wedge on the rim.
Units: spec in mm / ml, Blender scene in metres.
"""
import bpy, bmesh, json, math, os, sys, random
from mathutils import Vector, Matrix

MM = 0.001
Z_TOP = [0.0]; R_TOP = [0.0]; ICE_TOP = [None]   # top of drink (foam top if any), set by build_liquid
BEND_SIGN = 1
SEG = 128
random.seed(7)

# ----------------------------------------------------------------- helpers
def hex_rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

def srgb_to_lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

def interp_fill(fill_curve, ml):
    if ml <= 0: return 0.0
    for a, b in zip(fill_curve, fill_curve[1:]):
        if a["ml"] <= ml <= b["ml"]:
            t = 0 if b["ml"] == a["ml"] else (ml - a["ml"]) / (b["ml"] - a["ml"])
            return a["h_mm"] + t * (b["h_mm"] - a["h_mm"])
    return fill_curve[-1]["h_mm"]

def r_at(profile, h):
    """inner radius (mm) at height h (mm above bowl bottom)."""
    for a, b in zip(profile, profile[1:]):
        if a["h_mm"] <= h <= b["h_mm"]:
            t = 0 if b["h_mm"] == a["h_mm"] else (h - a["h_mm"]) / (b["h_mm"] - a["h_mm"])
            return a["r_mm"] + t * (b["r_mm"] - a["r_mm"])
    return profile[-1]["r_mm"]

def lathe(name, pts, closed_top=False, closed_bottom=False, seg=SEG):
    """pts: [(r_m, z_m)] polyline revolved about Z. Returns object (smooth shaded)."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = []
    for r, z in pts:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring.append(bm.verts.new((max(r, 0) * math.cos(a), max(r, 0) * math.sin(a), z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            try: bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
            except ValueError: pass
    if closed_bottom: bm.faces.new(list(reversed(rings[0])))
    if closed_top: bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    return ob

def add_mod_bevel(ob, w, seg=3):
    m = ob.modifiers.new("bevel", 'BEVEL'); m.width = w; m.segments = seg; m.limit_method = 'ANGLE'

def subsurf(ob, lvl=2):
    m = ob.modifiers.new("sub", 'SUBSURF'); m.levels = lvl; m.render_levels = lvl

def place(ob, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob.location = loc; ob.rotation_euler = rot

# ----------------------------------------------------------------- materials
def mat_principled(name, base=(1, 1, 1), rough=0.3, metal=0.0, trans=0.0, ior=1.45, sss=0.0, sss_col=None,
                   coat=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = trans
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = sss_col or (1, 0.4, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.004
    if coat: b.inputs["Coat Weight"].default_value = coat
    b.inputs["Alpha"].default_value = alpha
    return m

def mat_glass():
    return mat_principled("PHG_Glass", base=(1, 1, 1), rough=0.0, trans=1.0, ior=1.52)

def mat_liquid(color_hex, clarity):
    """clarity 1 = crystal clear (stirred / clarified), 0 = opaque (cream, egg white, shaken citrus).
    Colour comes from volume absorption so depth reads correctly (thin rim edge lighter, centre darker)."""
    c = srgb_to_lin(hex_rgb(color_hex))
    m = mat_principled("PHG_Liquid", base=(1, 1, 1) if clarity >= 0.9 else c,
                       rough=0.0 if clarity >= 0.9 else 0.12 * (1 - clarity), trans=clarity, ior=1.36,
                       sss=0.0 if clarity >= 0.9 else (1 - clarity) * 0.9, sss_col=c)
    nt = m.node_tree; out = nt.nodes["Material Output"]
    vol = nt.nodes.new("ShaderNodeVolumeAbsorption")
    d_ref = 0.04
    sigma = [-math.log(max(x, 1e-3)) / d_ref for x in c]          # per-channel coefficient, 1/m
    D = max(max(sigma), 1e-3)
    vol.inputs["Color"].default_value = (*[1 - s_ / D for s_ in sigma], 1)
    vol.inputs["Density"].default_value = D * (0.6 + 0.4 * clarity)
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    return m

def mat_ice():
    m = mat_principled("PHG_Ice", base=(0.97, 0.99, 1.0), rough=0.12, trans=1.0, ior=1.31)
    nt = m.node_tree; sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Density"].default_value = 6.0
    nt.links.new(sc.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    return m

MAT = {}
def M(key):
    if key in MAT: return MAT[key]
    lib = {
        "cherry":      dict(base=srgb_to_lin((0.23, 0.01, 0.03)), rough=0.12, coat=1.0, sss=0.3, sss_col=(0.8, 0.05, 0.05)),
        "cherry_stem": dict(base=srgb_to_lin((0.25, 0.16, 0.07)), rough=0.6),
        "orange_flesh":dict(base=srgb_to_lin((0.98, 0.55, 0.08)), rough=0.35, sss=0.6, sss_col=(1, 0.5, 0.1)),
        "orange_peel": dict(base=srgb_to_lin((0.90, 0.40, 0.0)), rough=0.35),
        "lemon_flesh": dict(base=srgb_to_lin((0.98, 0.88, 0.35)), rough=0.35, sss=0.6, sss_col=(1, 0.9, 0.3)),
        "lemon_peel":  dict(base=srgb_to_lin((0.90, 0.72, 0.02)), rough=0.5),
        "lime_flesh":  dict(base=srgb_to_lin((0.62, 0.80, 0.25)), rough=0.35, sss=0.6, sss_col=(0.6, 0.9, 0.3)),
        "lime_peel":   dict(base=srgb_to_lin((0.18, 0.45, 0.08)), rough=0.45),
        "pith":        dict(base=srgb_to_lin((0.97, 0.94, 0.85)), rough=0.6, sss=0.3, sss_col=(1, 1, 0.9)),
        "olive":       dict(base=srgb_to_lin((0.35, 0.42, 0.12)), rough=0.25, coat=0.6),
        "mint":        dict(base=srgb_to_lin((0.12, 0.42, 0.10)), rough=0.5, sss=0.4, sss_col=(0.3, 0.8, 0.2)),
        "pick_wood":   dict(base=srgb_to_lin((0.78, 0.62, 0.40)), rough=0.7),
        "pick_metal":  dict(base=(0.9, 0.9, 0.9), rough=0.15, metal=1.0),
        "foam":        dict(base=srgb_to_lin((0.95, 0.92, 0.84)), rough=0.8, sss=0.8, sss_col=(1, 0.95, 0.85)),
    }[key]
    MAT[key] = mat_principled("PHG_" + key, **lib)
    if key.endswith("_peel"):
        add_zest_bump(MAT[key])
        # waxy zest: low, tight specular so the big softboxes don't wash the colour to pastel
        MAT[key].node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.12
    return MAT[key]

def add_zest_bump(m, scale=900.0, strength=0.35):
    """Oil-gland dimples on citrus skin (cherries get a fainter version)."""
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = scale
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.0004
    nt.links.new(vor.outputs["Distance"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])

def assign(ob, mat):
    ob.data.materials.clear(); ob.data.materials.append(mat)

# ----------------------------------------------------------------- glass
def build_glass(g):
    """Returns (glass_obj, z_bowl_bottom_m, inner_profile). Outer = inner offset by wall thickness;
    stemware gets a stem + foot below the bowl, tumblers a solid base."""
    prof = g["inner_profile"]; wall = g.get("wall_thickness_mm", 2.0)
    H = g["height_mm"]; foot_r = g["foot_diameter_mm"] / 2
    stem = g["family"] in ("coupe", "nick_and_nora", "martini", "flute", "wine")
    bowl_depth = prof[-1]["h_mm"]
    z0 = H - bowl_depth                                     # bowl bottom height above table (mm)
    inner = [(p["r_mm"], z0 + p["h_mm"]) for p in prof]
    outer = [(p["r_mm"] + wall, z0 + p["h_mm"]) for p in prof]
    pts = []
    if stem:
        foot_t = 3.0; stem_r = 3.8
        pts += [(0, 0), (foot_r, 0), (foot_r, 1.2), (foot_r - 2, foot_t), (stem_r * 2.2, foot_t + 3),
                (stem_r, foot_t + 10), (stem_r, z0 - 8), (stem_r * 1.8, z0 - 2)]
        pts += [(max(r, wall * 1.5), z) for r, z in outer]
    else:
        pts += [(0, 0), (foot_r - 1.5, 0), (foot_r, 1.5)]
        pts += outer[1:] if outer[0][0] < foot_r * 0.5 else outer
        pts[3:3] = []
    rim_out = pts[-1]; rim_in = inner[-1]
    pts += [((rim_out[0] + rim_in[0]) / 2, H + wall * 0.35)]      # rolled rim lip
    pts += list(reversed(inner))
    pts = [(r * MM, z * MM) for r, z in pts]
    ob = lathe("Glass", pts)
    assign(ob, mat_glass())
    return ob, z0, prof

# ----------------------------------------------------------------- service style
# serve: how the drink is presented. Sets default ice + validates glass choice. Explicit "ice" in the spec wins.
SERVE = {
    "up":            dict(ice={"type": "none"}, stemmed=True,  chilled=True,  desc="Shaken/stirred, strained, no ice, stemmed glass"),
    "neat":          dict(ice={"type": "none"}, stemmed=None,  chilled=False, desc="Straight from the bottle, room temperature, no ice, no dilution"),
    "down":          dict(ice={"type": "large_cube"}, stemmed=False, chilled=True, desc="Over ice in a rocks glass (default large cube)"),
    "on_large_cube": dict(ice={"type": "large_cube"}, stemmed=False, chilled=True, desc="Over one large clear cube"),
    "on_sphere":     dict(ice={"type": "sphere"}, stemmed=False, chilled=True, desc="Over an ice sphere"),
    "on_cubes":      dict(ice={"type": "cubes", "count": 0}, stemmed=False, chilled=True, desc="Over cubed ice, filled to the top"),
    "on_spear":      dict(ice={"type": "spear"}, stemmed=False, chilled=True, desc="Collins spear"),
    "on_crushed":    dict(ice={"type": "crushed"}, stemmed=False, chilled=True, desc="Over crushed / pebble ice, domed above the rim"),
}
STEMMED = ("coupe", "nick_and_nora", "martini", "flute", "wine")

def resolve_serve(spec):
    warn = []; serve = spec.get("serve")
    g = spec["glass"]; stem = g["family"] in STEMMED
    if serve:
        rule = SERVE[serve]
        if "ice" not in spec: spec["ice"] = dict(rule["ice"])
        if rule["stemmed"] is True and not stem: warn.append(f"'{serve}' is normally served in stemware, not a {g['family']}")
        if rule["stemmed"] is False and stem: warn.append(f"'{serve}' needs a tumbler - ice in a {g['family']} is unusual")
        if serve in ("up", "neat") and spec["ice"].get("type") not in (None, "none"): warn.append(f"'{serve}' means no ice, but ice is set")
    if spec.get("ice", {}).get("type") == "cubes" and not spec["ice"].get("count"):
        # fill the glass with cubes (bar standard): estimate count from capacity
        spec["ice"]["count"] = max(3, int(g["capacity_ml"] * 0.6 / 15.6 / 0.85))
    return warn

# ----------------------------------------------------------------- liquid + ice
ICE = {  # submerged-volume approximations for displacement, and builders
    "none": 0, "large_cube": 50 ** 3, "sphere": 4 / 3 * math.pi * 27.5 ** 3, "cubes": 25 ** 3,
    "spear": None, "crushed": None,
}

def ice_volume_ml(ice, g):
    t = ice.get("type", "none"); n = ice.get("count", 1)
    if t == "spear":
        return 22 * 22 * g["inner_profile"][-1]["h_mm"] * 0.8 / 1000 * 0.9
    if t == "crushed":
        return g["capacity_ml"] * 0.45
    return ICE[t] * n / 1000 * 0.9 if ICE[t] else 0  # ~90% submerged (ice floats)

def build_liquid(g, z0, fill_ml, ice, liquid):
    prof = g["inner_profile"]
    disp = ice_volume_ml(ice, g)
    h = interp_fill(g["fill_curve"], min(fill_ml + disp, g["capacity_ml"] * 0.97))
    pts = []
    for p in prof:
        if p["h_mm"] < h: pts.append((max(p["r_mm"] - 0.15, 0), z0 + p["h_mm"]))
    rt = r_at(prof, h) - 0.15
    pts.append((rt, z0 + h))
    # meniscus: liquid climbs the glass ~1.5 mm at the wall
    pts.append((rt - 1.2, z0 + h - 0.6)); pts.append((0, z0 + h - 0.8))
    pts = [(r * MM, z * MM) for r, z in pts]
    ob = lathe("Liquid", pts, closed_bottom=False)
    assign(ob, mat_liquid(liquid.get("color_hex", "#c9802b"), liquid.get("clarity", 0.9)))
    foam = liquid.get("foam_mm", 0)
    Z_TOP[0] = (z0 + h + (foam * 1.05 if foam else -0.8)) * MM; R_TOP[0] = rt - (3 if foam else 1.5)
    if foam:
        fp = [(0, z0 + h - 0.8), (rt - 0.3, z0 + h), (rt - 0.3, z0 + h + foam * 0.8), (rt - 3, z0 + h + foam),
              (0, z0 + h + foam * 1.05)]
        fo = lathe("Foam", [(r * MM, z * MM) for r, z in fp]); assign(fo, M("foam"))
    return (z0 + h) * MM, rt

def cube(name, sx, sy, sz, bevel):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object; ob.name = name
    ob.scale = (sx * MM, sy * MM, sz * MM); bpy.ops.object.transform_apply(scale=True)
    add_mod_bevel(ob, bevel * MM, 4)
    for p in ob.data.polygons: p.use_smooth = True
    return ob

def build_ice(ice, g, z0, z_surface, r_surface):
    t = ice.get("type", "none"); n = ice.get("count", 1); obs = []
    floor = z0 + 1.0
    if t == "large_cube":
        s = min(50, r_surface * 1.35)
        ob = cube("Ice", s, s, s, 3); place(ob, (0, 0, (floor + s / 2 + max(0, (z_surface / MM - floor - s * 0.92))) * MM),
                                            (0, 0, math.radians(17))); obs.append(ob)
    elif t == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=27.5 * MM, segments=64, ring_count=32)
        ob = bpy.context.active_object; ob.name = "Ice"
        place(ob, (0, 0, z_surface - 27.5 * MM * 0.8)); obs.append(ob)
        for p in ob.data.polygons: p.use_smooth = True
    elif t == "spear":
        L = g["inner_profile"][-1]["h_mm"] * 0.85
        ob = cube("Ice", 22, 22, L, 2.5); place(ob, (0, 0, (z0 / MM + 1 + L / 2) * MM), (0, 0, math.radians(8)))
        obs.append(ob)
    elif t in ("cubes", "crushed"):
        s = 25 if t == "cubes" else 9
        count = n if t == "cubes" else 900
        top = (g["height_mm"] + 10) if t == "crushed" else z_surface / MM + 4
        layer_h = s * 0.9; z = z0 + s / 2 + 1; k = 0
        rim_cap = g["height_mm"] - s * 0.45 if t == "cubes" else 1e9
        while k < count and z < top + s and z < rim_cap:
            r_here = r_at(g["inner_profile"], max(0, z - z0)) - s * 0.62
            per = max(1, int((2 * math.pi * max(r_here, 1)) / (s * 1.15))) if r_here > s * 0.4 else 1
            for i in range(per):
                if k >= count: break
                a = 2 * math.pi * i / per + random.uniform(-0.2, 0.2) + z * 0.13
                rr = r_here if per > 1 else 0
                sz = s * random.uniform(0.85, 1.1)
                ob = cube("Ice", sz, sz * random.uniform(0.9, 1.1), sz * random.uniform(0.9, 1.05), sz * 0.12)
                place(ob, (rr * math.cos(a) * MM, rr * math.sin(a) * MM, z * MM),
                      tuple(random.uniform(-0.5, 0.5) for _ in range(3)))
                obs.append(ob); k += 1
            z += layer_h
    for ob in obs: assign(ob, mat_ice())
    ICE_TOP[0] = (g["height_mm"] + 8) * MM if t == "crushed" else None
    return obs

# ----------------------------------------------------------------- condensation
def build_condensation(g, z0, z_surface, density=1.0):
    """Beads of water on the outside of the glass, only where the cold liquid/ice is (below the fill line)."""
    prof = g["inner_profile"]; wall = g.get("wall_thickness_mm", 2.0)
    zs = z_surface / MM; n = int(260 * density * (zs - z0) / 60)
    mat = mat_principled("PHG_Condensation", base=(1, 1, 1), rough=0.0, trans=1.0, ior=1.333)
    me = bpy.data.meshes.new("condensation"); bm = bmesh.new()
    proto = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
    proto_verts = [v.co.copy() for v in bm.verts]; proto_faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.clear()
    for _ in range(n):
        h = random.uniform(max(z0 + 2, z0), zs - 1.5) - z0
        r = r_at(prof, h) + wall + 0.05; a = random.uniform(0, 2 * math.pi)
        size = random.choice([0.35, 0.5, 0.6, 0.8, 1.0, 1.3, 1.7]) * random.uniform(0.8, 1.2)
        nrm = Vector((math.cos(a), math.sin(a), 0))
        rot = nrm.to_track_quat('Z', 'Y').to_matrix()
        c = Vector((r * math.cos(a), r * math.sin(a), z0 + h))
        vs = [bm.verts.new(c + rot @ Vector((p.x * size, p.y * size * 1.15, p.z * size * 0.45))) for p in proto_verts]
        for f in proto_faces:
            try: bm.faces.new([vs[i] for i in f])
            except ValueError: pass
    for v in bm.verts: v.co *= MM
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new("Condensation", me); bpy.context.collection.objects.link(ob); assign(ob, mat)
    return ob

# ----------------------------------------------------------------- garnish primitives (all built at origin, +X = outward)
def g_cherry(stem=True):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=11 * MM, segments=48, ring_count=24)
    ob = bpy.context.active_object; ob.name = "Cherry"; ob.scale = (1, 1, 0.92)
    for p in ob.data.polygons: p.use_smooth = True
    assign(ob, M("cherry")); parts = [ob]
    if stem:
        cu = bpy.data.curves.new("stem", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.9 * MM
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
        sp.bezier_points[0].co = (0, 0, 9 * MM); sp.bezier_points[1].co = (8 * MM, 2 * MM, 38 * MM)
        for bp in sp.bezier_points: bp.handle_left_type = bp.handle_right_type = 'AUTO'
        st = bpy.data.objects.new("CherryStem", cu); bpy.context.collection.objects.link(st)
        st.data.materials.append(M("cherry_stem")); parts.append(st)
    return join(parts, "Cherry")

def g_olive():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=9, segments=40, ring_count=20)
    ob = bpy.context.active_object; ob.scale = (1, 1, 1.3); ob.name = "Olive"
    for p in ob.data.polygons: p.use_smooth = True
    assign(ob, M("olive")); return ob

def citrus_disc(fruit, radius, thick, arc=math.pi, name="Citrus"):
    """Half moon (arc=pi) or wheel (arc=2pi): flesh with segment lines, pith ring, peel ring.
    Built in XZ plane (standing up), thickness along Y, flat edge at z=0."""
    parts = []
    def ring(r0, r1, mat, y_off=0.0, t=thick):
        me = bpy.data.meshes.new("ring"); bm = bmesh.new(); n = 48
        segs = n if arc < 6.3 else n
        for side in (-t / 2, t / 2):
            pass
        verts_f, verts_b = [], []
        for i in range(n + 1):
            a = arc * i / n
            for rr, lst in ((r0, verts_f), (r1, verts_f)):
                pass
        # explicit quad strip build
        F = []; B = []
        for i in range(n + 1):
            a = arc * i / n; c, s = math.cos(a), math.sin(a)
            F.append((bm.verts.new((r0 * c, -t / 2, r0 * s)), bm.verts.new((r1 * c, -t / 2, r1 * s))))
            B.append((bm.verts.new((r0 * c, t / 2, r0 * s)), bm.verts.new((r1 * c, t / 2, r1 * s))))
        for i in range(n):
            bm.faces.new((F[i][0], F[i][1], F[i + 1][1], F[i + 1][0]))        # front
            bm.faces.new((B[i][0], B[i + 1][0], B[i + 1][1], B[i][1]))        # back
            bm.faces.new((F[i][1], B[i][1], B[i + 1][1], F[i + 1][1]))        # outer
            if r0 > 0: bm.faces.new((F[i][0], F[i + 1][0], B[i + 1][0], B[i][0]))
        if arc < 6.28:  # flat cut faces
            for e in (0, n):
                try: bm.faces.new((F[e][0], B[e][0], B[e][1], F[e][1]))
                except ValueError: pass
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-8)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("ring", me); bpy.context.collection.objects.link(ob)
        ob.data.materials.append(mat); add_mod_bevel(ob, 0.4 * MM, 2); return ob
    peel_t = 2.2; pith_t = 2.5
    parts.append(ring(2.5, radius - peel_t - pith_t, M(fruit + "_flesh"), t=thick * 0.96))
    parts.append(ring(0.01, 2.5, M("pith"), t=thick * 0.98))
    parts.append(ring(radius - peel_t - pith_t, radius - peel_t, M("pith")))
    parts.append(ring(radius - peel_t, radius, M(fruit + "_peel"), t=thick * 1.02))
    # segment membranes (radial pith lines) so it reads as citrus, not a disc
    nseg = 10
    for i in range(int(nseg * arc / (2 * math.pi)) + 1):
        a = arc * i / (nseg * arc / (2 * math.pi)) if arc < 6.3 else 2 * math.pi * i / nseg
        bpy.ops.mesh.primitive_cube_add(size=1)
        m = bpy.context.active_object
        L = radius - peel_t - pith_t
        m.scale = (L * MM, thick * 1.0 * MM, 0.7 * MM)
        m.location = (L / 2 * math.cos(a) * MM, 0, L / 2 * math.sin(a) * MM)
        m.rotation_euler = (0, -a, 0); assign(m, M("pith")); parts.append(m)
    ob = join(parts, name)
    for o in [ob]:
        o.scale = (MM / MM, 1, 1)
    # convert mm geometry built in metres? rings were built in mm units -> scale to metres
    return ob

def scale_mm(ob):
    ob.scale = (MM, MM, MM); bpy.context.view_layer.objects.active = ob
    ob.select_set(True); bpy.ops.object.transform_apply(scale=True); ob.select_set(False); return ob

def g_half_moon(fruit):
    r = {"orange": 34, "lemon": 28, "lime": 24}[fruit]
    ob = citrus_disc(fruit, r, 6, math.pi, fruit.title() + "HalfMoon"); return ob

def g_wheel(fruit):
    r = {"orange": 34, "lemon": 28, "lime": 24}[fruit]
    return citrus_disc(fruit, r, 5, 2 * math.pi - 1e-4, fruit.title() + "Wheel")

def g_wedge(fruit):
    """1/8 wedge of an ellipsoid fruit: peel outside, flesh on the two cut faces."""
    R = {"lime": 26, "lemon": 30}[fruit]; Lz = R * 1.25
    me = bpy.data.meshes.new("wedge"); bm = bmesh.new()
    nu, nv = 10, 24; a0, a1 = -math.pi / 8, math.pi / 8
    grid = []
    for j in range(nv + 1):
        v = math.pi * j / nv; row = []
        for i in range(nu + 1):
            u = a0 + (a1 - a0) * i / nu
            row.append(bm.verts.new((R * math.sin(v) * math.cos(u), R * math.sin(v) * math.sin(u), Lz * math.cos(v))))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    axis = [bm.verts.new((0, 0, Lz * math.cos(math.pi * j / nv))) for j in range(nv + 1)]
    flesh_faces = []
    for j in range(nv):
        for col in (0, nu):
            f = bm.faces.new((axis[j], grid[j][col], grid[j + 1][col], axis[j + 1]) if col == 0 else
                             (axis[j], axis[j + 1], grid[j + 1][col], grid[j][col]))
            flesh_faces.append(f)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces: f.material_index = 0
    for f in flesh_faces:
        if f.is_valid: f.material_index = 1
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(fruit.title() + "Wedge", me); bpy.context.collection.objects.link(ob)
    me.materials.append(M(fruit + "_peel")); me.materials.append(M(fruit + "_flesh"))
    return ob

def g_peel(fruit, length=62, width=22, twist=0.0, curl=1.0):
    """Expressed peel / twist: a curled strip with pith underside."""
    me = bpy.data.meshes.new("peel"); bm = bmesh.new(); n = 40; t = 1.6
    top, bot = [], []
    for i in range(n + 1):
        s = i / n; ang = twist * math.pi * s
        x = length * (s - 0.5); cy = math.cos(ang); cz = math.sin(ang)
        w = width * (1 - abs(2 * s - 1) ** 3.5) ** 0.3 if twist == 0 else width * (0.6 + 0.4 * math.sin(math.pi * s))
        bend = 7 * math.sin(math.pi * s) + curl * 2.5 * math.sin(2 * math.pi * s)
        top.append((bm.verts.new((x, -w / 2 * cy, -w / 2 * cz + bend)), bm.verts.new((x, w / 2 * cy, w / 2 * cz + bend))))
        bot.append((bm.verts.new((x, -w / 2 * cy - t * cz * 0, -w / 2 * cz + bend - t)),
                    bm.verts.new((x, w / 2 * cy, w / 2 * cz + bend - t))))
    for i in range(n):
        f = bm.faces.new((top[i][0], top[i + 1][0], top[i + 1][1], top[i][1])); f.material_index = 0
        f = bm.faces.new((bot[i][0], bot[i][1], bot[i + 1][1], bot[i + 1][0])); f.material_index = 1
        bm.faces.new((top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0])).material_index = 0
        bm.faces.new((top[i][1], top[i + 1][1], bot[i + 1][1], bot[i][1])).material_index = 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(fruit.title() + "Peel", me); bpy.context.collection.objects.link(ob)
    me.materials.append(M(fruit + "_peel")); me.materials.append(M("pith"))
    subsurf(ob, 1); return ob

def mint_leaf(L, W):
    """Ovate, serrated, slightly cupped leaf with a midrib crease. Built along +X from the petiole, mm units."""
    me = bpy.data.meshes.new("leaf"); bm = bmesh.new(); nx, ny = 28, 8; grid = []
    for i in range(nx + 1):
        x = L * i / nx; t = i / nx
        w = W * (math.sin(math.pi * t) ** 0.75) * (1 - 0.35 * t) * (1 + 0.06 * math.sin(t * 2 * math.pi * 9))
        row = []
        for j in range(ny + 1):
            v = -1 + 2 * j / ny; y = v * w / 2
            z = 0.9 * (abs(v) ** 2) * (w / W) * 2.2 - 0.4 * abs(v) ** 0.5 + 1.5 * t * t   # cup + midrib + tip lift
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("Leaf", me); bpy.context.collection.objects.link(ob)
    sol = ob.modifiers.new("t", 'SOLIDIFY'); sol.thickness = 0.35
    for p in me.polygons: p.use_smooth = True
    return ob

def g_mint():
    """Mint crown: stem with paired leaves, opposite and rotating 90 deg per node (as mint grows)."""
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=34, vertices=10)
    st = bpy.context.active_object; st.location = (0, 0, 10); assign(st, M("mint")); parts.append(st)
    nodes = [(26, 16, 10, 0.9), (18, 24, 14, 0.7), (9, 30, 17, 0.5), (0, 34, 18, 0.35)]   # z, length, width, upward tilt
    for k, (z, L, W, up) in enumerate(nodes):
        for side in (0, math.pi):
            lf = mint_leaf(L, W); a = side + k * math.pi / 2
            lf.rotation_euler = (0, -up, a); lf.location = (0, 0, z)
            bpy.ops.object.select_all(action='DESELECT'); lf.select_set(True); bpy.context.view_layer.objects.active = lf
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            assign(lf, M("mint")); parts.append(lf)
    for o in parts:
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return join(parts, "Mint")

def g_pick(length, metal=False):
    bpy.ops.mesh.primitive_cylinder_add(radius=1.4, depth=length, vertices=16)
    ob = bpy.context.active_object; ob.name = "Pick"
    assign(ob, M("pick_metal" if metal else "pick_wood")); return ob

def join(objs, name):
    objs = [o for o in objs if o]
    for o in objs:
        if o.type == 'CURVE':
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
            bpy.context.view_layer.objects.active = o; bpy.ops.object.convert(target='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    ob = bpy.context.active_object; ob.name = name; ob.select_set(False); return ob

# garnish factory. Builders that work in mm are flagged so they get scaled to metres.
def make(item_type):
    t = item_type
    if t == "cherry": return g_cherry(), False
    if t == "olive":  return g_olive(), True
    if t.endswith("_half_moon"): return g_half_moon(t.split("_")[0]), True
    if t.endswith("_wheel"):     return g_wheel(t.split("_")[0]), True
    if t.endswith("_wedge"):     return g_wedge(t.split("_")[0]), True
    if t.endswith("_peel"):      return g_peel(t.split("_")[0]), True
    if t.endswith("_twist"):     return g_peel(t.split("_")[0], length=95, width=8, twist=3.0, curl=0), True
    if t == "mint_sprig":        return g_mint(), True
    raise ValueError("unknown garnish " + t)

def to_m(ob, in_mm):
    if in_mm: scale_mm(ob)
    return ob

# ----------------------------------------------------------------- drops (bitters / oils on the surface)
DROP_LIQ = {   # look, plus typical spread diameter on the surface (mm)
    "angostura":   dict(base=(0.16, 0.02, 0.01), trans=0.0, rough=0.15, ior=1.38, d=7.5, flat=0.18),
    "peychauds":   dict(base=(0.55, 0.02, 0.03), trans=0.0, rough=0.15, ior=1.38, d=6.0, flat=0.18),
    "orange_bitters": dict(base=(0.55, 0.22, 0.03), trans=0.0, rough=0.2, ior=1.38, d=5.5, flat=0.18),
    "olive_oil":   dict(base=(0.85, 0.75, 0.25), trans=0.85, rough=0.0, ior=1.47, d=5.0, flat=0.35),
    "chili_oil":   dict(base=(0.85, 0.22, 0.04), trans=0.6, rough=0.0, ior=1.47, d=4.5, flat=0.35),
    "sesame_oil":  dict(base=(0.75, 0.45, 0.12), trans=0.8, rough=0.0, ior=1.47, d=4.5, flat=0.35),
    "citrus_oil":  dict(base=(0.95, 0.85, 0.40), trans=0.95, rough=0.0, ior=1.47, d=1.6, flat=0.4),   # expressed peel mist
}

def drop_positions(n, pattern, R, d):
    if n <= 0: return []
    if pattern == "dot" or n == 1: return [(0.0, 0.0)][:n] if n == 1 else [(0.0, 0.0)] * 0
    if pattern == "line":
        step = min(d * 1.8, (R * 1.4) / max(n - 1, 1)); x0 = -step * (n - 1) / 2
        return [(x0 + i * step, 0.0) for i in range(n)]
    if pattern == "ring":
        rr = min(R * 0.55, max(d * 1.4, n * d * 0.35))
        return [(rr * math.cos(2 * math.pi * i / n), rr * math.sin(2 * math.pi * i / n)) for i in range(n)]
    if pattern == "triangle" and n == 3:
        rr = d * 1.3; return [(rr * math.cos(a), rr * math.sin(a)) for a in (math.pi / 2, math.pi * 7 / 6, math.pi * 11 / 6)]
    pts = []; tries = 0
    while len(pts) < n and tries < 5000:          # random, non-touching, inside the surface
        tries += 1; r = R * 0.8 * math.sqrt(random.random()); a = random.uniform(0, 2 * math.pi)
        p = (r * math.cos(a), r * math.sin(a))
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > (d * 1.2) ** 2 for q in pts): pts.append(p)
    return pts

def build_drops(item, z_top, r_top):
    liq = item.get("liquid", "angostura"); L = DROP_LIQ[liq]
    n = int(item.get("count", 1)); d = float(item.get("size_mm", L["d"]))
    pattern = item.get("pattern", "line" if liq in ("angostura", "peychauds", "orange_bitters") else "random")
    m = mat_principled("PHG_drop_" + liq, base=srgb_to_lin(L["base"]), rough=L["rough"], trans=L["trans"], ior=L["ior"])
    obs = []
    for (x, y) in drop_positions(n, pattern, r_top, d):
        k = random.uniform(0.85, 1.15)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=d / 2 * k * MM, segments=24, ring_count=12)
        ob = bpy.context.active_object; ob.name = "Drop_" + liq
        ob.scale = (1, random.uniform(0.85, 1.0), L["flat"])        # lens / bead sitting on the surface
        ob.location = (x * MM, y * MM, z_top + d / 2 * k * L["flat"] * MM * 0.35)
        for p in ob.data.polygons: p.use_smooth = True
        assign(ob, m); obs.append(ob)
    if item.get("drag") and pattern == "line" and len(obs) > 1:      # pick dragged through bitters dots -> hearts/streak
        for ob in obs: ob.scale = (1.6, 0.6, ob.scale[2])
    return obs

# ----------------------------------------------------------------- garnish composer
def compose_garnish(items, g, z_rim, r_rim, z_surface, r_surface, z0):
    """Turns the garnish list into placed objects. Rules (bar-standard):
       pick   -> everything flagged 'pick' skewered on ONE pick in list order, pick rests across the rim at ~35deg
       rim    -> cut wheels/half moons/wedges slit onto the rim, spread round the back of the glass
       dropped-> sinks to the bottom (cherries) / rests on ice
       float  -> lies flat on the surface
       drape  -> peel hung over the rim, half inside half outside
       inside_wall -> wheel/half moon pressed against the inside wall (highballs, Collins)"""
    out = []
    expanded = []
    for it in [i for i in items if i.get("type") == "drops"]:
        out += build_drops(it, Z_TOP[0], R_TOP[0])
    items = [i for i in items if i.get("type") != "drops"]
    for it in items:
        for _ in range(int(it.get("count", 1))): expanded.append(dict(it))

    on_pick = [e for e in expanded if e.get("placement") == "pick"]
    if on_pick:
        L = max(90.0, r_rim * 2 * 1.35)
        pick = g_pick(L, metal=any(e.get("pick") == "metal" for e in on_pick)); scale_mm(pick)
        tilt = math.radians(68)
        # pick lies in XZ plane resting on the rim at the back (-X), tip down into the glass
        pivot = Vector((-r_rim * MM, 0, z_rim + 1.5 * MM))
        d = Vector((math.sin(tilt), 0, -math.cos(tilt)))       # pointing into the glass
        pick.location = pivot + d * (L * 0.5 - 30) * MM
        pick.rotation_euler = (0, math.pi - tilt, 0)   # cylinder +Z mapped onto d
        out.append(pick)
        pos = 14.0  # mm from rim pivot along the pick
        for e in on_pick:
            ob, mm = make(e["type"]); to_m(ob, mm)
            size = 22 if e["type"] in ("cherry", "olive") else 30
            pos += size * 0.55
            p = pivot + d * pos * MM
            ob.location = p
            if e["type"] in ("cherry", "olive"):
                ob.rotation_euler = (0, tilt - math.pi / 2, 0)
            else:  # citrus flag: half moon folded over the pick, flat face across it
                phi = math.pi / 2 - tilt
                ob.rotation_euler = (0, phi, 0)
                ob.location = p - Vector((math.sin(phi), 0, math.cos(phi))) * 9 * MM
            pos += size * 0.55
            out.append(ob)

    rim_items = [e for e in expanded if e.get("placement") == "rim"]
    for k, e in enumerate(rim_items):
        ob, mm = make(e["type"]); to_m(ob, mm)
        ang = math.radians(318 - k * 34)                     # spread round the back-left of the glass
        cx, cy = r_rim * math.cos(ang) * MM, r_rim * math.sin(ang) * MM
        if "wedge" in e["type"]:
            ob.rotation_euler = (0, math.radians(100), ang)
            ob.location = (cx * 1.05, cy * 1.05, z_rim + 4 * MM)
        else:  # half moon / wheel slit onto the rim, stands vertical, tangent-normal to the rim
            ob.rotation_euler = (0, 0, ang)
            ob.location = (cx, cy, z_rim - 12 * MM)
        out.append(ob)

    for e in [e for e in expanded if e.get("placement") == "dropped"]:
        ob, mm = make(e["type"]); to_m(ob, mm)
        n = len([o for o in out if o.name.startswith("Cherry")])
        ob.location = (random.uniform(-6, 6) * MM + n * 9 * MM, random.uniform(-5, 5) * MM, z0 * MM + 11 * MM)
        out.append(ob)

    floats = [e for e in expanded if e.get("placement") == "float"]
    n_mint = sum(1 for e in floats if e["type"] == "mint_sprig"); i_mint = 0
    for e in floats:
        ob, mm = make(e["type"]); to_m(ob, mm)
        if e["type"] == "mint_sprig" and n_mint > 1:      # julep bouquet: sprigs fanned round a tight centre
            a = 2 * math.pi * i_mint / n_mint + 0.4; rr = 9 * MM
            ob.rotation_euler = (math.radians(18) * math.cos(a + math.pi / 2), math.radians(18) * math.sin(a + math.pi / 2) * -1, a)
            ob.location = (rr * math.cos(a), rr * math.sin(a), (ICE_TOP[0] or z_surface) - 4 * MM); i_mint += 1
            out.append(ob); continue
        ob.rotation_euler = (math.pi / 2, 0, random.uniform(0, 6.28)) if ("wheel" in e["type"] or "half_moon" in e["type"]) else (0, 0, 0.4)
        ob.location = (0, 0, (ICE_TOP[0] or z_surface) + 1 * MM); out.append(ob)   # crowns crushed ice

    for k, e in enumerate([e for e in expanded if e.get("placement") == "drape"]):
        ob, mm = make(e["type"]); to_m(ob, mm)
        ang = math.radians(35 - k * 50)
        ob.rotation_euler = (math.radians(10), math.radians(-48), ang)
        ob.location = (r_rim * math.cos(ang) * MM * 0.95, r_rim * math.sin(ang) * MM * 0.95, z_rim - 4 * MM)
        out.append(ob)

    for k, e in enumerate([e for e in expanded if e.get("placement") == "inside_wall"]):
        ob, mm = make(e["type"]); to_m(ob, mm)
        ang = math.radians(240 + k * 62)
        h = (z_surface / MM - z0) * 0.55 + z0
        rr = r_at(g["inner_profile"], h - z0) - 4
        disc_r = {"orange": 34, "lemon": 28, "lime": 24}.get(e["type"].split("_")[0], 30)
        k_fit = min(1.0, rr * 0.8 / disc_r); ob.scale = (k_fit, k_fit, k_fit)
        ob.rotation_euler = (0, 0, ang + math.pi / 2)
        # bend the slice to follow the glass wall (it is pressed against the inside of the glass)
        k_fit = min(1.0, rr * 0.95 / disc_r); ob.scale = (k_fit, k_fit, k_fit)
        bend = ob.modifiers.new("wall_bend", 'SIMPLE_DEFORM'); bend.deform_method = 'BEND'; bend.deform_axis = 'Z'
        bend.angle = BEND_SIGN * (2 * disc_r * k_fit) / rr
        rpos = rr + 3.0
        ob.location = (rpos * math.cos(ang) * MM, rpos * math.sin(ang) * MM, h * MM - 12 * MM)
        out.append(ob)
    return out

# ----------------------------------------------------------------- studio
def studio(glass_h_m, glass_r_m, res=(900, 1200), samples=96, elev_deg=9):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 24; sc.cycles.transmission_bounces = 24; sc.cycles.transparent_max_bounces = 24
    sc.cycles.caustics_refractive = True; sc.cycles.caustics_reflective = False; sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.film_transparent = False
    try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError: pass
    sc.view_settings.exposure = -0.7   # keeps saturated garnish (orange zest, cherries) from washing to pastel
    # seamless sweep backdrop
    pts = [(-0.6, 0.0), (0.25, 0.0), (0.33, 0.02), (0.38, 0.08), (0.40, 0.6)]
    me = bpy.data.meshes.new("sweep"); bm = bmesh.new(); W = 1.2; rows = []
    for x, z in pts:
        rows.append((bm.verts.new((-W / 2, x, z)), bm.verts.new((W / 2, x, z))))
    for a, b in zip(rows, rows[1:]): bm.faces.new((a[0], a[1], b[1], b[0]))
    bm.to_mesh(me); bm.free(); sw = bpy.data.objects.new("Sweep", me); bpy.context.collection.objects.link(sw)
    subsurf(sw, 3); for_p = [setattr(p, "use_smooth", True) for p in me.polygons]
    sw.data.materials.append(mat_principled("PHG_Sweep", base=(0.025, 0.023, 0.021), rough=0.45))
    def area(name, loc, rot, size, energy, col=(1, 1, 1), shape='RECTANGLE', sy=None):
        l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = col; l.shape = shape
        if sy: l.size_y = sy
        o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    h = glass_h_m
    area("Key", (-0.35, -0.30, h * 2.2), (math.radians(55), 0, math.radians(-50)), 0.35, 9)
    area("BackStrip", (0.0, 0.30, h * 0.75), (math.radians(-90), 0, 0), 0.05, 9, sy=0.35)   # backlight: liquid glows
    area("RimL", (-0.28, 0.12, h * 1.0), (math.radians(90), 0, math.radians(-110)), 0.04, 10, sy=0.5)
    area("RimR", (0.28, 0.12, h * 1.0), (math.radians(90), 0, math.radians(110)), 0.04, 10, sy=0.5)
    area("Top", (0, 0, h * 3.5), (0, 0, 0), 0.3, 4, col=(1, 0.97, 0.92))
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.03
    cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 85
    cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
    fit = max(h * 1.35, glass_r_m * 3.2)
    dist = fit / (2 * math.tan(cam_d.angle_y / 2)) * 1.05
    tgt = Vector((0, 0, h * (0.55 + 0.25 * min(elev_deg, 45) / 45))); el = math.radians(elev_deg)
    cam.location = tgt + Vector((0, -math.cos(el) * dist, math.sin(el) * dist))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_d.dof.use_dof = True; cam_d.dof.focus_distance = (tgt - cam.location).length; cam_d.dof.aperture_fstop = 8

# ----------------------------------------------------------------- main
def build(spec, out_dir, render=True, samples=96, res=(900, 1200)):
    bpy.ops.wm.read_factory_settings(use_empty=True); MAT.clear(); ICE_TOP[0] = None
    g = spec["glass"]; warnings = resolve_serve(spec)
    glass, z0, prof = build_glass(g)
    z_surface, r_surface = build_liquid(g, z0, spec["fill_ml"], spec.get("ice", {}), spec.get("liquid", {}))
    build_ice(spec.get("ice", {"type": "none"}), g, z0, z_surface, r_surface)
    iced = spec.get("ice", {}).get("type", "none") != "none"
    cond = spec.get("condensation", "auto")
    if cond is True or (cond == "auto" and iced and spec.get("serve") != "neat"):
        build_condensation(g, z0, z_surface, density=float(spec.get("condensation_density", 1.0)))
    z_rim = g["height_mm"] * MM; r_rim = prof[-1]["r_mm"] + g.get("wall_thickness_mm", 2) / 2
    compose_garnish(spec.get("garnish", []), g, z_rim, r_rim, z_surface, r_surface, z0)
    top_detail = any(i.get("type") == "drops" or i.get("placement") == "float" for i in spec.get("garnish", []))
    elev = spec.get("camera_elevation_deg", 32 if top_detail else 9)   # show drops / floats on the surface
    studio(z_rim, (g["max_diameter_mm"] / 2) * MM, res=res, samples=samples, elev_deg=elev)
    os.makedirs(out_dir, exist_ok=True); key = spec.get("key", "drink")
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, key + ".glb"), export_format='GLB',
                              use_selection=False, export_cameras=False, export_lights=False)
    if render:
        bpy.context.scene.render.filepath = os.path.join(out_dir, key + ".png")
        bpy.ops.render.render(write_still=True)
    return dict(key=key, serve=spec.get("serve"), ice=spec.get("ice"), fill_height_mm=round(z_surface / MM - z0, 1), warnings=warnings)

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    spec = json.load(open(argv[0])); print(build(spec, argv[1]))
