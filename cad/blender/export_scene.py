"""Export every part / fastener mesh (D frame, mm) + scene.json describing each render.

Run from cad/:  .venv/bin/python blender/export_scene.py
Then:           flatpak run org.blender.Blender -b -P blender/render_scene.py
Then:           .venv/bin/python blender/callouts.py ../docs/assembly/img
"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from voice_clock import *          # noqa: E402,F401
import render_steps as RS          # noqa: E402
import render as R                 # noqa: E402

HERE = Path(__file__).resolve().parent
MESH = HERE / "meshes"

# ------------------------------------------------------------------ materials
# every mesh gets one material key; render_scene.py defines what each key looks like
MAT = {
    "front_shell": "pla", "rear_shell": "pla", "back_plate": "pla", "mute_plunger": "pla",
    "carrier": "pla", "spider": "pla",
    "ring_base": "petg_natural", "ring_shell": "petg_natural",
    "cp_knob": "alu_dark", "cp_glass": "display", "cp_pcb": "pcb_green", "cp_conn": "nylon_white",
    "rs_pcb": "pcb_black", "rs_leds": "led", "rs_xiao": "pcb_blue",
    "speaker": "plastic_black",
    "foot_pad_front": "tpu", "foot_pad_rear": "tpu", "ballast_fill": "steel_shot",
}
LABEL = {
    "front_shell": "Front shell", "rear_shell": "Rear shell", "back_plate": "Back plate",
    "mute_plunger": "Mute button", "carrier": "Carrier", "spider": "Spider bracket",
    "ring_base": "Ring base (PETG)", "ring_shell": "Ring shell (PETG)",
    "cp_knob": "CrowPanel 2.1\" display", "rs_pcb": "reSpeaker XVF3800", "speaker": "Speaker 4428 3 W",
    "foot_pad_front": "TPU grip pad (small)", "foot_pad_rear": "TPU grip pad (large)",
    "ballast_fill": "Ballast: steel shot in slow epoxy",
}


def write(name, v, f):
    MESH.mkdir(parents=True, exist_ok=True)
    m = trimesh.Trimesh(np.asarray(v, float), np.asarray(f, int), process=False)
    m.export(MESH / f"{name}.ply")
    return name


def merged(meshes):
    vs, fs, off = [], [], 0
    for v, f in meshes:
        vs.append(v)
        fs.append(np.asarray(f) + off)
        off += len(v)
    return np.vstack(vs), np.vstack(fs)


def centroid(name):
    m = trimesh.load(MESH / f"{name}.ply", process=False)
    return m.bounds.mean(0)


def foil_meshes():
    """Aluminium foil tape: round the ring base's outer face, and inside the ring shell's sleeve."""
    z1, z2, z3, z4 = RING_IW_Z
    R0, R1, R2, T, zt = RING_IW_R0, RING_IW_R1, RING_IW_R2, RING_IW_T, RING_TOP_Z
    prof = [(R0 + T, 1.0), (R0 + T, z1), (R1 + T, z2), (R1 + T, z3), (R2 + T, z4), (R2 + T, zt - 2.0)]
    base = revolve_rz([(r + 0.02, z) for r, z in prof] + [(r + 0.14, z) for r, z in reversed(prof)])
    zs = zt - RING_CAP_T - 4.0
    shell = revolve_rz([(RING_SLV_RI - 0.14, 0.0), (RING_SLV_RI - 0.02, 0.0), (RING_SLV_RI - 0.02, zs),
                        (RING_SLV_RI - 0.14, zs)])
    return R.tess(base), R.tess(shell)


def usb_screws():
    """2 x M2 x 10 from the board's back (rim side) through it into the pads' inserts."""
    _, y_back = usb_pcb_y()
    z = BACK_Z + USB_HOLE_Z
    m = []
    for sx in (-1, 1):
        x = sx * USB_HOLE_PITCH / 2
        m.append(RS.cylseg((x, y_back, z), (x, y_back + 10.0, z), 1.0))
        m.append(RS.cylseg((x, y_back - 2.0, z), (x, y_back, z), 1.9))
    return m


def arc(r, z, a0, a1, n=24):
    """3D polyline (D frame) round the Z axis from angle a0 to a1 (deg, CCW seen from the front)."""
    return [[*polar(r, a0 + (a1 - a0) * k / n), z] for k in range(n + 1)]


def main():
    print("tessellating parts ...", flush=True)
    g = RS.tess_all()
    for n, (v, f) in g.items():
        write(n, v, f)
    fb, fs = foil_meshes()

    # fastener / small-part groups (each one mesh + material + label)
    hw = {
        "ins_spider":  (RS.hw_inserts("spider"),  "brass",   "3x M2 insert"),
        "ins_back":    (RS.hw_inserts("back"),    "brass",   "4x M2 insert (2 speaker, 2 USB-C pads)"),
        "scr_cp":      (RS.hw_cp_screws(),        "steel_black", "3x M3x12 SHCS"),
        "scr_clamp":   (RS.hw_clamp_screws(),     "steel_black", "3x M2x20 SHCS"),
        "scr_spk":     (RS.hw_spk_screws(),       "steel_black", "2x M2x10 SHCS (speaker)"),
        "scr_usb":     (usb_screws(),             "steel_black", "2x M2x10 SHCS (USB-C)"),
        "tpu_wash":    (RS.hw_spk_washers(),      "tpu",     "4x TPU washer"),
        "foam_mic":    (RS.hw_mic_foam(),         "foam",    "4x foam mic gasket"),
        "foam_spk":    (RS.hw_spk_foam(),         "foam",    "Foam ring"),
        "usb":         (RS.hw_usb(),              "pcb_blue", "USB-C breakout (5.1k)"),
        "foil_base":   ([fb],                     "alu",     "Foil tape (outside)"),
        "foil_shell":  ([fs],                     "alu",     "Foil tape (inside)"),
    }
    for k, (meshes, mat, lab) in hw.items():
        v, f = merged(meshes)
        write(k, v, f)
        MAT[k] = mat
        LABEL[k] = lab

    CP = ["cp_knob", "cp_glass", "cp_pcb", "cp_conn"]
    RSB = ["rs_pcb", "rs_leds", "rs_xiao"]
    head = CP + ["spider", "scr_cp", "ins_spider"]
    core = head + ["ring_base", "foil_base"] + RSB + ["carrier", "scr_clamp"]
    stack = core + ["ring_shell", "foil_shell"]
    shell_r = ["rear_shell", "mute_plunger", "ballast_fill", "foot_pad_rear"]
    shell_f = ["front_shell", "foot_pad_front", "foam_mic"]
    plate = ["back_plate", "ins_back", "usb", "scr_usb", "speaker", "foam_spk", "tpu_wash", "scr_spk"]
    rh = rs_holes()
    out = [-UP_D.X, -UP_D.Y, -UP_D.Z]        # straight out of the flat base (the pads go on there)

    def items(base, new=(), **mv):
        """base: names at their final place. new: (name, dz) or (name, dict(off=[x,y,z], rz=deg))."""
        res = [{"mesh": n, "dz": 0.0, "new": False} for n in base]
        for n, m in new:
            it = {"mesh": n, "new": True}
            if isinstance(m, dict):
                off = list(m.get("off", (0, 0, 0)))
                it.update(dz=float(off[2]), off=[float(c) for c in off], rz=float(m.get("rz", 0.0)))
            else:
                it.update(dz=float(m))
            res.append(it)
        return res

    REAR, FRONT = (150, 18), (-35, 14)
    up = 62                                   # stack / front shell lifted along D +z
    lift = 9
    assembled = stack + shell_r + shell_f + plate
    entry_f = dict(off=(0, 0, up), rz=TW_ANGLE)          # front shell: on at +10 deg, turned clockwise (front view)
    bdz = -40
    entry_b = dict(off=(0, 0, bdz), rz=-BP_TWIST)        # back plate: in 32 deg back, turned clockwise (back view)
    steps = [
        dict(id="hero_front", title="Voice Clock", view=(-32, 12), items=items(assembled),
             callouts=[], ground=True),
        dict(id="hero_back", title="Back", view=(148, 14), items=items(assembled),
             callouts=["back_plate", "usb", "mute_plunger", "rear_shell"], ground=True),
        # 1. inserts
        dict(id="step_01", title="Heat-set inserts: spider (3)", view=REAR, items=items(
            [], [("spider", 0), ("ins_spider", -lift)]),
             callouts=["spider", "ins_spider"]),
        dict(id="step_01b", title="Heat-set inserts: back plate (2 + 2)", view=(-25, 38), items=items(
            [], [("back_plate", 0), ("ins_back", dict(off=(0, 0, 0)))]),
             callouts=["back_plate", "ins_back"],
             arrows=[[(sx * SPK_EAR_PITCH / 2, SPK_CY, RS.EAR_TOP + 16), (sx * SPK_EAR_PITCH / 2, SPK_CY, RS.EAR_TOP + 2)]
                     for sx in (-1, 1)] +
                    [[(sx * USB_HOLE_PITCH / 2, usb_pcb_y()[0] + USB_WALL_T + 14, BACK_Z + USB_HOLE_Z),
                      (sx * USB_HOLE_PITCH / 2, usb_pcb_y()[0] + USB_WALL_T + 1, BACK_Z + USB_HOLE_Z)] for sx in (-1, 1)]),
        # 3. spider
        dict(id="step_02", title="Spider bracket onto the CrowPanel", view=REAR, items=items(
            CP, [("spider", -22), ("ins_spider", -22), ("scr_cp", -40)]),
             callouts=["cp_knob", "spider", "ins_spider", "scr_cp"],
             arrows=[[(0, 0, -44), (0, 0, -26)]]),
        # 4. ring base (foil outside) from behind
        dict(id="step_03", title="Ring base, foil tape round the outside", view=(135, 20), items=items(
            head, [("ring_base", -48), ("foil_base", -48)]),
             callouts=["ring_base", "foil_base", "spider", "cp_knob"],
             arrows=[[(*polar(46, 300), -86), (*polar(46, 300), -56)]]),
        # 5. reSpeaker, then carrier + clamp screws
        dict(id="step_04", title="reSpeaker onto the ring base", view=(118, 24), items=items(
            head + ["ring_base", "foil_base"], [(n, -36) for n in RSB]),
             callouts=["rs_pcb", "ring_base", "spider"],
             arrows=[[(x, y, -50), (x, y, -38)] for x, y in rh]),
        dict(id="step_05", title="Carrier and clamp screws", view=REAR, items=items(
            head + ["ring_base", "foil_base"] + RSB, [("carrier", -26), ("scr_clamp", -48)]),
             callouts=["carrier", "scr_clamp", "rs_pcb"],
             arrows=[[(x, y, -56), (x, y, -38)] for x, y in rh]),
        # 6. ring shell from the front
        dict(id="step_06", title="Ring shell on over the knob (foil inside)", view=(-64, 22), items=items(
            core, [("ring_shell", 34), ("foil_shell", 34)]),
             callouts=["ring_shell", "foil_shell", "ring_base"],
             arrows=[[(*polar(47, 230), 92), (*polar(47, 230), 72)]]),
        # 7. ballast + grip pads
        dict(id="step_07", title="Ballast in the pocket, grip pads on the base", view=(-50, 22), items=items(
            ["rear_shell"],
            [("ballast_fill", 34), ("foot_pad_rear", dict(off=[12 * c for c in out]))]),
             callouts=["ballast_fill", "foot_pad_rear", "rear_shell"],
             arrows=[[(*polar(46, 205), 74), (*polar(46, 205), 44)],
                     [[FOOT_C.X + 34 * out[0], FOOT_C.Y + 34 * out[1], FOOT_C.Z + 34 * out[2]],
                      [FOOT_C.X + 17 * out[0], FOOT_C.Y + 17 * out[1], FOOT_C.Z + 17 * out[2]]]]),
        # 8. mute button, then the stack into the rear shell
        dict(id="step_08", title="Mute button, then the stack into the rear shell", view=(-72, 20),
             items=items(shell_r, [(n, up) for n in stack]),
             callouts=["rear_shell", "mute_plunger", "carrier", "rs_pcb"],
             arrows=[[(0, -30, up + 45), (0, -30, up + 20)], [(0, 74, PLG_Z), (0, 63, PLG_Z)]]),
        # 9. front shell: on 10 deg anticlockwise, then clockwise to the click
        dict(id="step_09", title="Front shell: drop on, turn clockwise to click", view=(-62, 16), items=items(
            shell_r + stack, [(n, entry_f) for n in shell_f]),
             callouts=["front_shell", "rear_shell", "foam_mic"],
             arrows=[[(*polar(70, 200), up + 30), (*polar(70, 200), up + 8)]],
             arcs=[arc(66, up + 14, 125, 75)]),
        # 10. USB-C and speaker (either order; the USB-C screws go in from the rim)
        # the plate lies loose on the bench: shown turned 180 deg so the rim-side screw heads face the camera
        dict(id="step_10", title="USB-C breakout: screws in from the rim", view=(-25, 38), items=items(
            [], [("back_plate", dict(rz=180)), ("ins_back", dict(rz=180)), ("usb", dict(rz=180)),
                 ("scr_usb", dict(off=(0, 16, 0), rz=180))]),
             callouts=["back_plate", "usb", "scr_usb"],
             arrows=[[(sx * (USB_HOLE_PITCH / 2 + 3.5), -(usb_pcb_y()[1] - 22), BACK_Z + USB_HOLE_Z),
                      (sx * (USB_HOLE_PITCH / 2 + 3.5), -(usb_pcb_y()[1] - 6), BACK_Z + USB_HOLE_Z)] for sx in (-1, 1)]),
        dict(id="step_10b", title="Speaker on the back plate", view=(-62, 18), items=items(
            ["back_plate", "ins_back", "usb", "scr_usb"],
            [("speaker", 28), ("foam_spk", 14), ("tpu_wash", 28), ("scr_spk", 48)]),
             callouts=["speaker", "foam_spk", "tpu_wash", "scr_spk"],
             arrows=[[(sx * SPK_EAR_PITCH / 2, SPK_CY, RS.EAR_TOP + 62), (sx * SPK_EAR_PITCH / 2, SPK_CY, RS.EAR_TOP + 44)]
                     for sx in (-1, 1)]),
        # 11. back plate: in at 5 o'clock (seen from the back), clockwise to 6 o'clock
        dict(id="step_11", title="Back plate: push in, turn clockwise to click", view=REAR, items=items(
            stack + shell_r + shell_f, [(n, entry_b) for n in plate]),
             callouts=["back_plate", "usb", "rear_shell"],
             arrows=[[(*polar(48, 20), BACK_Z + bdz - 26), (*polar(48, 20), BACK_Z + bdz - 4)]],
             arcs=[arc(46, BACK_Z + bdz - 4, 215, 262)]),
    ]
    for s in steps:
        s.setdefault("arrows", [])
        s.setdefault("arcs", [])
        s.setdefault("ground", False)
        s["anchors"] = {}
    scene = dict(materials=MAT, labels=LABEL, steps=steps,
                 frame=dict(tilt=TILT, foot_h=FOOT_H, display_r=33.0, display_z=12.5 + CP_Z0))
    (HERE / "scene.json").write_text(json.dumps(scene, indent=1))
    print("wrote", HERE / "scene.json", len(steps), "scenes,", len(list(MESH.glob("*.ply"))), "meshes")


if __name__ == "__main__":
    main()
