"""Blender (Cycles) renderer for scene.json.

flatpak run org.blender.Blender -b -P blender/render_scene.py -- [--only id,id] [--samples N] [--res W]
Writes blender/renders/<id>.png (transparent film + shadow catcher) and <id>.json
(pixel positions of callout anchors and arrows).
"""
import json
import sys
from math import radians, sin, cos, tan, atan, sqrt
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
opt = {argv[i].lstrip("-"): argv[i + 1] for i in range(0, len(argv) - 1, 2)}
ONLY = set(opt["only"].split(",")) if "only" in opt else None
SAMPLES = int(opt.get("samples", 160))
RES_X = int(opt.get("res", 1800))
RES_Y = int(RES_X * 0.75)
PROJECT_ONLY = opt.get("project", "0") == "1"   # rebuild scenes and re-project anchors without rendering

S = json.loads((HERE / "scene.json").read_text())
F = S["frame"]
MM = 0.001


# ------------------------------------------------------------------ frames
def d_to_blender():
    """D frame (mm) -> Blender world (m, Z up). D->world: tilt about X, table at y=0;
    world (x, y up, z toward viewer) -> Blender (x, -z, y)."""
    t = radians(-F["tilt"])
    tilt = Matrix.Rotation(t, 4, "X")
    lift = Matrix.Translation((0, -F["foot_h"], 0))
    w2b = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    return Matrix.Scale(MM, 4) @ w2b @ lift @ tilt


M_D = d_to_blender()


def to_b(p):
    return M_D @ Vector(p)


# ------------------------------------------------------------------ scene setup
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 10
    sc.cycles.transparent_max_bounces = 10
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = RES_X, RES_Y
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.threads_mode = "AUTO"
    # studio world: soft vertical gradient, gives metals something to reflect
    w = bpy.data.worlds.new("studio")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.10, 0.095, 0.09, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.95, 0.93, 0.90, 1)
    map_ = nt.nodes.new("ShaderNodeMapRange")
    map_.inputs["From Min"].default_value = -1
    map_.inputs["From Max"].default_value = 1
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(tc.outputs["Normal"] if False else tc.outputs["Generated"], sep.inputs[0])
    # 'Generated' on the world = view direction; Z component -> up/down
    nt.links.new(sep.outputs["Z"], map_.inputs["Value"])
    nt.links.new(map_.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.35
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return sc


def hexlin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1,)


def principled(name, base, rough, metal=0.0, **kw):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = base
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k, v in kw.items():
        b.inputs[k].default_value = v
    return m, nt, b


def add_bump(nt, b, kind, strength, scale, axis_z=True):
    """Layer lines (kind='layers', 0.2 mm bands along object Z) or grain noise."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    if kind == "layers":
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.bands_direction = "Z"
        wave.inputs["Scale"].default_value = scale
        wave.inputs["Distortion"].default_value = 0.4
        wave.inputs["Detail"].default_value = 1.0
        nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
        nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    else:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = scale
        noise.inputs["Detail"].default_value = 6
        nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])


def materials(hero):
    M = {}
    m, nt, b = principled("pla", hexlin("#d39b95"), 0.62, **{"Specular IOR Level": 0.35})
    add_bump(nt, b, "layers", 0.06, 0.314 / 0.2)        # wave scale: 1 band per 0.2 mm (object units = mm)
    M["pla"] = m
    m, nt, b = principled("petg_natural", (0.93, 0.93, 0.91, 1), 0.38,
                          **{"Transmission Weight": 0.85, "IOR": 1.57, "Subsurface Weight": 0.15})
    add_bump(nt, b, "layers", 0.04, 0.314 / 0.2)
    M["petg_natural"] = m
    M["alu_dark"] = principled("alu_dark", (0.045, 0.045, 0.05, 1), 0.32, 1.0)[0]
    M["alu"] = principled("alu", (0.62, 0.62, 0.64, 1), 0.38, 1.0)[0]
    M["pcb_green"] = principled("pcb_green", hexlin("#1d5a37"), 0.32, **{"Coat Weight": 0.4})[0]
    M["pcb_black"] = principled("pcb_black", (0.012, 0.012, 0.014, 1), 0.3, **{"Coat Weight": 0.5})[0]
    M["pcb_blue"] = principled("pcb_blue", hexlin("#1b2f6b"), 0.3, **{"Coat Weight": 0.5})[0]
    M["nylon_white"] = principled("nylon_white", (0.82, 0.80, 0.74, 1), 0.5)[0]
    M["plastic_black"] = principled("plastic_black", (0.018, 0.018, 0.02, 1), 0.48)[0]
    M["brass"] = principled("brass", (0.86, 0.64, 0.27, 1), 0.24, 1.0)[0]
    M["steel_black"] = principled("steel_black", (0.035, 0.035, 0.04, 1), 0.33, 0.9)[0]
    m, nt, b = principled("tpu", (0.03, 0.03, 0.035, 1), 0.75)
    M["tpu"] = m
    m, nt, b = principled("foam", (0.012, 0.012, 0.012, 1), 0.95)
    add_bump(nt, b, "noise", 0.5, 2.0)
    M["foam"] = m
    m, nt, b = principled("led", (0.95, 0.95, 0.95, 1), 0.3,
                          **{"Emission Color": (1.0, 0.82, 0.62, 1), "Emission Strength": 40.0 if hero else 0.0})
    M["led"] = m
    # display: clock face as emission under a glossy coat, mapped from object XY (mm)
    m, nt, b = principled("display", (0.0, 0.0, 0.0, 1), 0.08, **{"Coat Weight": 1.0, "Coat Roughness": 0.02,
                                                                  "Emission Strength": 0.9})
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    r = F["display_r"]
    mp.inputs["Scale"].default_value = (1 / (2 * r), 1 / (2 * r), 1)
    mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(str(HERE / "clockface.png"))
    img.extension = "CLIP"
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], img.inputs["Vector"])
    nt.links.new(img.outputs["Color"], b.inputs["Emission Color"])
    nt.links.new(img.outputs["Color"], b.inputs["Base Color"])
    M["display"] = m
    # wood PLA (turned-wood variant): matte, 0.2 mm layer lines, fine fibre speckle + tone drift
    M["steel_shot"] = principled("steel_shot", (0.10, 0.10, 0.11, 1), 0.48, 0.85)[0]
    woods = [("wood_cherry", "#6A3527"), ("wood_walnut", "#36221A"), ("wood_cherry_hot", "#552A1E"),
             ("pla_core", "#5A3B2A"), ("wood_maple", "#C6AA80"), ("wood_oak", "#8E6B47")]
    woods += list(S.get("wood_tones", {}).items())      # Full Spectrum layer mixes (wood_scene.py walnut_fs)
    for key, hexc in woods:
        m, nt, b = principled(key, hexlin(hexc), 0.74, **{"Specular IOR Level": 0.3})
        tc = nt.nodes.new("ShaderNodeTexCoord")
        speck = nt.nodes.new("ShaderNodeTexNoise")
        speck.inputs["Scale"].default_value = 3.5          # object units are mm -> ~0.3 mm fibres
        speck.inputs["Detail"].default_value = 8
        drift = nt.nodes.new("ShaderNodeTexNoise")
        drift.inputs["Scale"].default_value = 0.04          # slow tone drift (the temperature script)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs[6].default_value = hexlin(hexc)        # colour A
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[0].color = (0.50, 0.48, 0.47, 1)
        ramp.color_ramp.elements[1].position = 0.68
        ramp.color_ramp.elements[1].color = (0.70, 0.69, 0.68, 1)
        add = nt.nodes.new("ShaderNodeMath")
        add.operation = "MULTIPLY_ADD"
        add.inputs[1].default_value = 0.5
        nt.links.new(tc.outputs["Object"], speck.inputs["Vector"])
        nt.links.new(tc.outputs["Object"], drift.inputs["Vector"])
        nt.links.new(speck.outputs["Fac"], add.inputs[0])
        nt.links.new(drift.outputs["Fac"], add.inputs[2])
        nt.links.new(add.outputs["Value"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], mix.inputs[7])     # colour B
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(mix.outputs[2], b.inputs["Base Color"])  # colour result
        add_bump(nt, b, "layers", 0.05, 0.314 / 0.2)
        M[key] = m
    return M


def load_meshes(names, mats, matkey):
    objs = {}
    for n in names:
        bpy.ops.wm.ply_import(filepath=str(HERE / "meshes" / f"{n}.ply"))
        o = bpy.context.selected_objects[0]
        o.name = n
        o.data.materials.clear()
        o.data.materials.append(mats[matkey[n]])
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_smooth_by_angle(angle=radians(32))
        objs[n] = o
    return objs


def place(o, it):
    """Item offset (D frame, mm) and turn about the D z axis (deg, CCW seen from the front)."""
    off = it.get("off", (0.0, 0.0, it.get("dz", 0.0)))
    o.matrix_world = M_D @ Matrix.Translation(off) @ Matrix.Rotation(radians(it.get("rz", 0.0)), 4, "Z")


def lights_and_camera(sc, center, radius, view, ground_z):
    yaw, pitch = radians(view[0]), radians(view[1])
    # camera direction in the old renderer's "world" (x, y up, z toward viewer)
    Ry = Matrix(((cos(yaw), 0, sin(yaw)), (0, 1, 0), (-sin(yaw), 0, cos(yaw))))
    Rx = Matrix(((1, 0, 0), (0, cos(pitch), -sin(pitch)), (0, sin(pitch), cos(pitch))))
    vw = (Rx @ Ry).transposed() @ Vector((0, 0, 1))
    vb = Vector((vw.x, -vw.z, vw.y)).normalized()          # to Blender axes
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 85
    cam_data.sensor_width = 36
    fov = 2 * atan(18 / 85) * min(1.0, RES_Y / RES_X)
    dist = radius / sin(fov / 2) * 1.04
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = center + vb * dist
    cam.rotation_euler = (-vb).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    cam_data.clip_start, cam_data.clip_end = 0.01, 50
    # three-point softbox rig relative to the camera
    right = (-vb).cross(Vector((0, 0, 1))).normalized()
    up = right.cross(-vb).normalized()

    def area(name, pos, size, energy, color=(1, 1, 1), shadows=True):
        L = bpy.data.lights.new(name, "AREA")
        L.use_shadow = shadows
        L.shape = "RECTANGLE"
        L.size, L.size_y = size, size * 0.7
        L.energy = energy
        L.color = color
        o = bpy.data.objects.new(name, L)
        sc.collection.objects.link(o)
        o.location = pos
        o.rotation_euler = (center - pos).to_track_quat("-Z", "Y").to_euler()

    R = dist
    area("key", center + (vb * 0.6 - right * 0.7 + up * 1.6).normalized() * R * 1.1, R * 0.9, 42 * R * R, (1.0, 0.97, 0.93))
    area("fill", center + (vb * 0.9 + right * 1.0 + up * 0.2).normalized() * R * 1.2, R * 1.2, 16 * R * R, (0.93, 0.96, 1.0), shadows=False)
    area("rim", center + (-vb * 0.9 + up * 1.0 + right * 0.3).normalized() * R * 1.1, R * 0.6, 40 * R * R, shadows=False)
    # shadow catcher floor
    bpy.ops.mesh.primitive_plane_add(size=6, location=(center.x, center.y, ground_z))
    floor = bpy.context.object
    floor.is_shadow_catcher = True
    return cam


def project(sc, cam, p):
    v = world_to_camera_view(sc, cam, p)
    return [round(v.x * RES_X, 1), round((1 - v.y) * RES_Y, 1), round(v.z, 4)]


def smart_anchor(sc, cam, obj, n_samples=600):
    """Visible surface point of obj nearest its projected centre (ray-cast from the camera)."""
    import random
    dg = bpy.context.evaluated_depsgraph_get()
    mw = obj.matrix_world
    verts = obj.data.vertices
    if not len(verts):
        return None
    rnd = random.Random(7)
    idx = [rnd.randrange(len(verts)) for _ in range(min(n_samples, len(verts)))]
    cen = sum((mw @ Vector(c) for c in obj.bound_box), Vector()) / 8
    c2 = world_to_camera_view(sc, cam, cen)
    best, bestd = None, 1e9
    origin = cam.matrix_world.translation
    for i in idx:
        p = mw @ verts[i].co
        v = p - origin
        dist = v.length
        hit, loc, nrm, fi, hobj, _ = sc.ray_cast(dg, origin, v.normalized(), distance=dist + 1e-4)
        if not hit or hobj is None or hobj.name != obj.name or (loc - p).length > 0.0006:
            continue
        q = world_to_camera_view(sc, cam, p)
        if not (0.02 < q.x < 0.98 and 0.02 < q.y < 0.95):
            continue
        dd = (q.x - c2.x) ** 2 + (q.y - c2.y) ** 2
        if dd < bestd:
            best, bestd = p, dd
    return best


def render_step(step):
    sc = reset()
    hero = step["id"].startswith("hero")
    mats = materials(hero)
    names = [it["mesh"] for it in step["items"]]
    objs = load_meshes(names, mats, S["materials"])
    for it in step["items"]:
        place(objs[it["mesh"]], it)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs.values() for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2
    radius = (hi - lo).length / 2
    ground = 0.0 if step.get("ground") else lo.z - 0.002
    cam = lights_and_camera(sc, center, radius * 0.86, step["view"], ground)
    OUT.mkdir(exist_ok=True)
    sc.render.filepath = str(OUT / f"{step['id']}.png")
    if not PROJECT_ONLY:
        bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.update()
    anchors = {}
    for k in step["callouts"]:
        p = smart_anchor(sc, cam, objs[k]) if k in objs else None
        if p is not None:
            anchors[k] = project(sc, cam, p)
    proj = {
        "size": [RES_X, RES_Y],
        "anchors": anchors,
        "arrows": [[project(sc, cam, to_b(a)), project(sc, cam, to_b(b))] for a, b in step["arrows"]],
        "arcs": [[project(sc, cam, to_b(p)) for p in a] for a in step.get("arcs", [])],
    }
    (OUT / f"{step['id']}.json").write_text(json.dumps(proj))
    print("RENDERED", step["id"], flush=True)


for st in S["steps"]:
    if ONLY and st["id"] not in ONLY:
        continue
    render_step(st)
