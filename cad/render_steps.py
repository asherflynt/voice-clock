"""Step-by-step assembly renders -> out/steps/step_XX.png

New parts in each step are shown in full colour, pulled back along the way they go
in, with orange arrows. Parts already assembled are faded. Screws (steel), heat-set
inserts (brass), TPU washers, foam gaskets and the USB-C breakout are modelled as
simple proxies so every fastener shows up where it goes.
"""
import numpy as np
import trimesh
from math import radians
from voice_clock import *
import render as R

OUT_STEPS = OUT / "steps"
STEEL, BRASS, ARROW, FOAM, TPU = "#aeb4bd", "#c9a646", "#ff7a1a", "#2b2b2b", "#3d6fd1"


# ------------------------------------------------------------ geometry (D frame)
def tess_all():
    parts = {n: f() for n, f in PRINT_PARTS.items() if n not in ("tpu_washers", "insert_coupon", "foot_pads")}
    prox = proxies()
    g = {}
    for n, s in {**parts, **prox}.items():
        if n in TEXTURED:
            m = trimesh.load(OUT / "asm" / f"{n}.ply", process=False)
            g[n] = (np.asarray(m.vertices), np.asarray(m.faces))
        else:
            g[n] = R.tess(s)
    g["foot_pad_front"] = R.tess(foot_pad_placed("front"))
    g["foot_pad_rear"] = R.tess(foot_pad_placed("rear"))
    g["ballast_fill"] = R.tess(ballast_pocket())
    return g


def tm(mesh):
    return np.asarray(mesh.vertices), np.asarray(mesh.faces)


def cylseg(p0, p1, r, sections=20):
    return tm(trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=sections))


def screw(xy, z_head_seat, length, d, head_d, head_h, toward=+1):
    """Screw whose head sits at z_head_seat and whose shank points toward +z (toward=+1) or -z."""
    x, y = xy
    s = toward
    shank = cylseg((x, y, z_head_seat), (x, y, z_head_seat + s * length), d / 2)
    head = cylseg((x, y, z_head_seat - s * head_h), (x, y, z_head_seat), head_d / 2)
    return [shank, head]


def ins(xy, z0, z1, od):
    return [cylseg((xy[0], xy[1], z0), (xy[0], xy[1], z1), od / 2)]


def box(c, size):
    b = trimesh.creation.box(extents=size)
    b.apply_translation(c)
    return tm(b)


def arrow(p0, p1, r=0.9):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    u = d / L
    tip = 5.0
    shaft = cylseg(p0, p1 - u * tip, r, 12)
    cone = trimesh.creation.cone(radius=r * 2.6, height=tip, sections=16)
    # cone is along +z from 0 to tip: rotate +z onto u, move base to p1 - u*tip
    T = trimesh.geometry.align_vectors([0, 0, 1], u)
    cone.apply_transform(T)
    cone.apply_translation(p1 - u * tip)
    return [shaft, tm(cone)]


def moved(meshes, dz=0.0, dy=0.0, dx=0.0):
    out = []
    for v, f in meshes:
        v = v.copy()
        v[:, 0] += dx
        v[:, 1] += dy
        v[:, 2] += dz
        out.append((v, f))
    return out


def tint(hexc, k=0.55):
    c = R.hexrgb(hexc) * (1 - k) + k
    return "#%02x%02x%02x" % tuple(int(round(x * 255)) for x in c)


# ------------------------------------------------------------ hardware positions
SHCS_M3 = dict(d=3.0, head_d=5.5, head_h=3.0)
BTN_M3 = dict(d=3.0, head_d=5.7, head_h=1.65)
SHCS_M2 = dict(d=2.0, head_d=3.8, head_h=2.0)
M3_INS_OD, M3_INS_L = 4.2, 4.0
M2_INS_OD = 3.2


def hw_cp_screws():                      # spider -> CrowPanel hub (from the board side, toward +z)
    m = []
    for xy in cp_screws():
        m += screw(xy, STANDOFF_L + 1.0, 12, **SHCS_M3)
    return m


def hw_clamp_screws():                   # carrier back -> spider insert
    m = []
    for xy in rs_holes():
        m += screw(xy, CARRIER_Z0 + CARRIER_CB, M2_CLAMP_LEN, **SHCS_M2)
    return m


SPK_FACE = BACK_Z + SPK_GASKET
EAR_TOP = SPK_FACE + SPK_EAR_FROM_FACE + SPK_EAR_T          # ear face away from the plate


def hw_spk_screws():
    m = []
    for sx in (-1, 1):
        m += screw((sx * SPK_EAR_PITCH / 2, SPK_CY), EAR_TOP + TPU_WASHER_T, 10, toward=-1, **SHCS_M2)
    return m


def hw_spk_washers():
    m = []
    for sx in (-1, 1):
        x = sx * SPK_EAR_PITCH / 2
        ring = trimesh.creation.annulus(r_min=1.25, r_max=3.0, height=TPU_WASHER_T)
        for zc in (EAR_TOP + TPU_WASHER_T / 2, EAR_TOP - SPK_EAR_T - TPU_WASHER_T / 2):
            r = ring.copy()
            r.apply_translation((x, SPK_CY, zc))
            m.append(tm(r))
    return m


def hw_inserts(which):
    m = []
    if "spider" in which:
        for xy in rs_holes():
            m += ins(xy, STANDOFF_L, STANDOFF_L + M2_INSERT_L, M2_INS_OD)
    if "back" in which:
        bt = BACK_Z + SPK_GASKET + SPK_EAR_FROM_FACE - TPU_WASHER_T
        for sx in (-1, 1):
            m += ins((sx * SPK_EAR_PITCH / 2, SPK_CY), bt - M2_INSERT_L, bt, M2_INS_OD)
        y_top, _ = usb_pcb_y()                         # USB-C pads: pressed in from their speaker-side face
        y1 = y_top + USB_WALL_T
        for sx in (-1, 1):
            x = sx * USB_HOLE_PITCH / 2
            m.append(cylseg((x, y1 - M2_INSERT_L, BACK_Z + USB_HOLE_Z), (x, y1, BACK_Z + USB_HOLE_Z), M2_INS_OD / 2))
    return m


def hw_mic_foam():
    m = []
    for a in (45, 135, 225, 315):
        ring = trimesh.creation.annulus(r_min=1.0, r_max=2.5, height=MIC_LUG_Z0)
        ring.apply_translation((*polar(RS_MIC_R, a), MIC_LUG_Z0 / 2))
        m.append(tm(ring))
    return m


def hw_spk_foam():
    ring = trimesh.creation.annulus(r_min=SPK_CONE_R, r_max=14.0, height=SPK_GASKET)
    ring.apply_translation((0, SPK_CY, BACK_Z + SPK_GASKET / 2))
    return [tm(ring)]


def hw_usb():
    """Measured 6-pin breakout: standing on its USB edge, socket through the slot."""
    L, Hb, T = USB_PCB
    y_top = USB_CY - USB_SOCKET_H / 2
    rec = box((0, USB_CY, BACK_Z - 1.48 + 7.3 / 2), (8.94, USB_SOCKET_H, 7.3))
    pcb = box((0, y_top - T / 2, BACK_Z + Hb / 2), (L, T, Hb))
    return [rec, pcb]


# ------------------------------------------------------------ step scenes
def scene(g, base, new, views, title, fname, arrows=(), hw_base=(), hw_new=()):
    """base/new: list of (part name, dz). hw_*: list of (meshes, colour, dz)."""
    items = []
    for n, dz in base:
        v, f = g[n]
        items.append((v + [0, 0, dz], f, tint(R.COL[n])))
    for meshes, col, dz in hw_base:
        for v, f in moved(meshes, dz):
            items.append((v, f, tint(col, 0.35)))
    for n, dz in new:
        v, f = g[n]
        items.append((v + [0, 0, dz], f, R.COL[n]))
    for meshes, col, dz in hw_new:
        for v, f in moved(meshes, dz):
            items.append((v, f, col))
    for p0, p1 in arrows:
        for v, f in arrow(p0, p1):
            items.append((v, f, ARROW))
    out = []
    for k, (yaw, pitch, zoom) in enumerate(views):
        fn = OUT_STEPS / (fname if len(views) == 1 else fname.replace(".png", f"_{'ab'[k]}.png"))
        R.render(items, yaw=yaw, pitch=pitch, zoom=zoom, fname=fn, title=title)
        out.append(fn)
    return out


CP = ["cp_knob", "cp_glass", "cp_pcb", "cp_conn"]
RS = ["rs_pcb", "rs_leds", "rs_xiao"]
REAR_VIEW = (150, 18, 1.0)
FRONT_VIEW = (-35, 14, 1.0)


def main():
    raise SystemExit("The assembly images come from the Blender pipeline now: see blender/export_scene.py")


if __name__ == "__main__":
    main()
