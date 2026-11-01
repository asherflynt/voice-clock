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
    parts = {n: f() for n, f in PRINT_PARTS.items() if n not in ("tpu_washers", "insert_coupon")}
    prox = proxies()
    g = {}
    for n, s in {**parts, **prox}.items():
        if n in TEXTURED:
            m = trimesh.load(OUT / "asm" / f"{n}.ply", process=False)
            g[n] = (np.asarray(m.vertices), np.asarray(m.faces))
        else:
            g[n] = R.tess(s)
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
    for xy in CP_SCREWS:
        m += screw(xy, STANDOFF_L + 1.0, 12, **SHCS_M3)
    return m


def hw_clamp_screws():                   # carrier back -> spider insert
    m = []
    for xy in rs_holes():
        m += screw(xy, SPLIT_Z + CARRIER_CB, M2_CLAMP_LEN, **SHCS_M2)
    return m


def hw_rim_screws():
    m = []
    for a in SHELL_LUG_ANG:
        m += screw(polar(SHELL_LUG_R, a), SPLIT_Z + RIM_CB[1], 6, **SHCS_M3)
    return m


def hw_rib_screws():
    m = []
    for a in REAR_RIB_ANG:
        m += screw(polar(REAR_RIB_R, a), SPLIT_Z - 4.0, 8, **BTN_M3)
    return m


def hw_back_screws():
    m = []
    for a in BACK_LUG_ANG:
        m += screw(polar(BACK_SCREW_R, a), BACK_Z - BACK_T, 8, **BTN_M3)
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
    if "front" in which:
        for a in SHELL_LUG_ANG:
            m += ins(polar(SHELL_LUG_R, a), CARRIER_FRONT, CARRIER_FRONT + M3_INS_L, M3_INS_OD)
    if "carrier" in which:
        for a in REAR_RIB_ANG:
            m += ins(polar(REAR_RIB_R, a), SPLIT_Z, SPLIT_Z + M3_INS_L, M3_INS_OD)
    if "rear" in which:
        for a in BACK_LUG_ANG:
            m += ins(polar(BACK_SCREW_R, a), BACK_Z, BACK_Z + M3_INS_L, M3_INS_OD)
    if "spider" in which:
        for xy in rs_holes():
            m += ins(xy, STANDOFF_L, STANDOFF_L + M2_INSERT_L, M2_INS_OD)
    if "back" in which:
        bt = BACK_Z + SPK_GASKET + SPK_EAR_FROM_FACE - TPU_WASHER_T
        for sx in (-1, 1):
            m += ins((sx * SPK_EAR_PITCH / 2, SPK_CY), bt - M2_INSERT_L, bt, M2_INS_OD)
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
    z_mouth = BACK_Z - BACK_T + USB_RECESS[2]
    rec = box((0, USB_CY, z_mouth + 3.65), (8.94, 3.26, 7.3))
    pcb = box((0, USB_CY - 2.45, BACK_Z + 0.1 + 11.05), (13.05, 1.6, 22.1))
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


CP = ["cp_knob", "cp_glass", "cp_housing", "cp_pcb", "cp_conn"]
RS = ["rs_pcb", "rs_leds", "rs_xiao"]
REAR_VIEW = (150, 18, 1.0)
FRONT_VIEW = (-35, 14, 1.0)


def main():
    OUT_STEPS.mkdir(exist_ok=True)
    g = tess_all()
    z = lambda names, dz=0.0: [(n, dz) for n in names]
    rh = rs_holes()

    # 1 - heat-set inserts (exploded parts, inserts hovering over their holes)
    E = 40
    offs = {"front_shell": 2.0 * E, "spider": 0.5 * E, "carrier": -0.6 * E, "rear_shell": -1.3 * E, "back_plate": -2.2 * E}
    lift = 9
    scene(g, [], [(n, d) for n, d in offs.items()], [REAR_VIEW, (-30, 20, 1.0)],
          "Step 1 - heat-set inserts: 3x M3 front-shell lugs, 3x M3 carrier, 3x M3 rear shell, 3x M2 spider underside, 2x M2 speaker bosses",
          "step_01_inserts.png",
          hw_new=[(hw_inserts("front"), BRASS, offs["front_shell"] - lift),
                  (hw_inserts("spider"), BRASS, offs["spider"] - lift),
                  (hw_inserts("carrier"), BRASS, offs["carrier"] - lift),
                  (hw_inserts("rear"), BRASS, offs["rear_shell"] - lift),
                  (hw_inserts("back"), BRASS, offs["back_plate"] + lift)])

    # 2 - spider onto the CrowPanel hub (3x M3 x 12 from the board side)
    d_sp, d_sc = -22, -40
    scene(g, z(CP), [("spider", d_sp)], [REAR_VIEW],
          "Step 2 - spider bracket onto the CrowPanel hub: remove the 3 stock rear screws, refit with 3x M3x12 through the spider",
          "step_02_spider.png",
          hw_base=[], hw_new=[(hw_inserts("spider"), BRASS, d_sp), (hw_cp_screws(), STEEL, d_sc)],
          arrows=[((0, 0, d_sc - 2), (0, 0, d_sc + 14))])

    # 3 - spacers + reSpeaker
    d_spc, d_rs = -16, -42
    scene(g, z(CP) + [("spider", 0)], [("board_spacers", d_spc)] + z(RS, d_rs), [(118, 24, 1.0)],
          "Step 3 - 3 printed spacers on the reSpeaker's front mounting holes, then the reSpeaker (LEDs facing the display)",
          "step_03_respeaker.png",
          hw_base=[(hw_cp_screws(), STEEL, 0), (hw_inserts("spider"), BRASS, 0)],
          arrows=[((x, y, d_rs - 14), (x, y, d_rs - 2)) for x, y in rh] +
                 [((x, y, d_spc - 8), (x, y, d_spc - 1)) for x, y in rh])

    # 4 - carrier + clamp screws
    d_c, d_s = -26, -48
    scene(g, z(CP) + [("spider", 0), ("board_spacers", 0)] + z(RS), [("carrier", d_c)], [REAR_VIEW],
          "Step 4 - carrier behind the reSpeaker (plug the speaker lead in first), 3x M2x20 from the back into the spider inserts",
          "step_04_carrier.png",
          hw_base=[(hw_cp_screws(), STEEL, 0)],
          hw_new=[(hw_inserts("carrier"), BRASS, d_c), (hw_clamp_screws(), STEEL, d_s)],
          arrows=[((x, y, d_s - 8), (x, y, d_s + 10)) for x, y in rh])

    # 5 - light guide + mic foam (from the front)
    d_lg, d_f = 46, 14
    core = z(CP) + [("spider", 0), ("board_spacers", 0), ("carrier", 0)] + z(RS)
    scene(g, core, [("light_guide", d_lg)], [FRONT_VIEW],
          "Step 5 - light guide over the display ring (notch at the CrowPanel cable), 4 foam mic gaskets on the diagonals",
          "step_05_lightguide.png",
          hw_base=[(hw_clamp_screws(), STEEL, 0)],
          hw_new=[(hw_mic_foam(), FOAM, d_f)],
          arrows=[((0, 46, d_lg + 30), (0, 46, d_lg + 8))])

    # 6 - stack into the front shell, plunger, rim screws
    core6 = core + [("light_guide", 0)]
    d_fs = 70
    scene(g, core6, [("front_shell", d_fs), ("mute_plunger", d_fs)], [(115, 16, 1.0), FRONT_VIEW],
          "Step 6 - mute plunger into the top hole, slide the stack into the front shell (knob through the face), 3x M3x6 through the carrier rim",
          "step_06_frontshell.png",
          hw_base=[(hw_clamp_screws(), STEEL, 0)],
          hw_new=[(hw_inserts("front"), BRASS, d_fs), (hw_rim_screws(), STEEL, -22)],
          arrows=[((0, 0, d_fs + 70), (0, 0, d_fs + 50))] +
                 [((*polar(SHELL_LUG_R, a), -45), (*polar(SHELL_LUG_R, a), -26)) for a in SHELL_LUG_ANG])

    # 7 - rear shell + rib screws
    core7 = core6 + [("front_shell", 0), ("mute_plunger", 0)]
    d_r, d_rs7 = -36, -70
    scene(g, core7, [("rear_shell", d_r)], [REAR_VIEW],
          "Step 7 - rear shell onto the front shell, 3x M3x8 button head straight in through the open back into the carrier",
          "step_07_rearshell.png",
          hw_base=[(hw_rim_screws(), STEEL, 0)],
          hw_new=[(hw_inserts("rear"), BRASS, d_r), (hw_rib_screws(), STEEL, d_rs7)],
          arrows=[((*polar(REAR_RIB_R, a), d_rs7 - 30), (*polar(REAR_RIB_R, a), d_rs7 - 12)) for a in REAR_RIB_ANG])

    # 8 - speaker + USB-C onto the back plate (back plate on its own, inside up)
    d_sp8, d_w = 28, 48
    scene(g, [("back_plate", 0)], [("speaker", d_sp8)], [(-62, 18, 1.0)],
          "Step 8 - back plate: foam ring on the speaker face, speaker on its bosses with a TPU washer each side of each ear, 2x M2x10; epoxy the USB-C breakout into its cage",
          "step_08_speaker.png",
          hw_base=[(hw_inserts("back"), BRASS, 0)],
          hw_new=[(hw_spk_foam(), FOAM, d_sp8 / 2), (hw_spk_washers(), TPU, d_sp8), (hw_spk_screws(), STEEL, d_w),
                  (hw_usb(), "#2f7d4f", 5)],
          arrows=[((sx * SPK_EAR_PITCH / 2, SPK_CY, EAR_TOP + d_w + 8), (sx * SPK_EAR_PITCH / 2, SPK_CY, EAR_TOP + d_w - 6))
                  for sx in (-1, 1)])

    # 9 - close up
    core9 = core7 + [("rear_shell", 0)]
    d_b, d_bs = -40, -70
    scene(g, core9, [("back_plate", d_b), ("speaker", d_b)], [REAR_VIEW],
          "Step 9 - plug the inlet into the harness, then the back plate onto the rear shell with 3x M3x8 button head",
          "step_09_backplate.png",
          hw_base=[(hw_rib_screws(), STEEL, 0)],
          hw_new=[(hw_spk_washers(), TPU, d_b), (hw_spk_screws(), STEEL, d_b), (hw_usb(), "#2f7d4f", d_b),
                  (hw_back_screws(), STEEL, d_bs)],
          arrows=[((*polar(BACK_SCREW_R, a), d_bs - 30), (*polar(BACK_SCREW_R, a), d_bs - 12)) for a in BACK_LUG_ANG])

    # 10 - done
    scene(g, [], core9 + [("back_plate", 0), ("speaker", 0)], [(-32, 12, 1.0), REAR_VIEW],
          "Step 10 - assembled", "step_10_done.png")


if __name__ == "__main__":
    main()
