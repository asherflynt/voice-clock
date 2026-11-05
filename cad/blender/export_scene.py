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

HERE = Path(__file__).resolve().parent
MESH = HERE / "meshes"

# ------------------------------------------------------------------ materials
# every mesh gets one material key; render_scene.py defines what each key looks like
MAT = {
    "front_shell": "pla", "rear_shell": "pla", "back_plate": "pla", "mute_plunger": "pla",
    "carrier": "pla", "spider": "pla", "board_spacers": "pla",
    "light_guide": "petg_natural",
    "cp_knob": "alu_dark", "cp_glass": "display", "cp_housing": "alu", "cp_pcb": "pcb_green",
    "cp_conn": "nylon_white",
    "rs_pcb": "pcb_black", "rs_leds": "led", "rs_xiao": "pcb_blue",
    "speaker": "plastic_black",
}
LABEL = {
    "front_shell": "Front shell", "rear_shell": "Rear shell", "back_plate": "Back plate",
    "mute_plunger": "Mute button", "carrier": "Carrier", "spider": "Spider bracket",
    "board_spacers": "3x printed spacer", "light_guide": "Light guide (PETG)",
    "cp_knob": "CrowPanel 2.1\" display", "rs_pcb": "reSpeaker XVF3800", "speaker": "Speaker 4428 3 W",
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


def main():
    print("tessellating parts ...", flush=True)
    g = RS.tess_all()
    for n, (v, f) in g.items():
        write(n, v, f)

    # fastener / small-part groups (each one mesh + material + label)
    hw = {
        "ins_spider":  (RS.hw_inserts("spider"),  "brass",   "3x M2 insert"),
        "ins_back":    (RS.hw_inserts("back"),    "brass",   "2x M2 insert"),
        "scr_cp":      (RS.hw_cp_screws(),        "steel_black", "3x M3x12 SHCS"),
        "scr_clamp":   (RS.hw_clamp_screws(),     "steel_black", "3x M2x20 SHCS"),
        "scr_spk":     (RS.hw_spk_screws(),       "steel_black", "2x M2x10 SHCS"),
        "tpu_wash":    (RS.hw_spk_washers(),      "tpu",     "4x TPU washer"),
        "foam_mic":    (RS.hw_mic_foam(),         "foam",    "4x foam mic gasket"),
        "foam_spk":    (RS.hw_spk_foam(),         "foam",    "Foam ring"),
        "usb":         (RS.hw_usb(),              "pcb_blue", "USB-C breakout (5.1k)"),
    }
    for k, (meshes, mat, lab) in hw.items():
        v, f = merged(meshes)
        write(k, v, f)
        MAT[k] = mat
        LABEL[k] = lab

    # board-side callout anchors that read better than a bbox centre
    anchor = {n: centroid(n).tolist() for n in list(g) + list(hw)}
    anchor["cp_knob"] = [0, CP_KNOB_R * 0.72, 12.4 + CP_Z0]
    anchor["light_guide"] = [0, -(LG_RO + 0.5), 18.0]
    anchor["front_shell"] = [-40.0, 30.0, 8.0]
    anchor["rear_shell"] = [44.0, -10.0, -28.0]
    anchor["back_plate"] = [0.0, 32.0, BACK_Z - BACK_T]
    anchor["carrier"] = [-44.0, -20.0, CARRIER_Z0]
    anchor["rs_pcb"] = [36.0, -30.0, -RS_T]
    anchor["spider"] = [*polar(22.0, 200), STANDOFF_L + SPIDER_T]
    anchor["speaker"] = [8.0, -12.0, BACK_Z + 12.0]
    anchor["usb"] = [0.0, USB_CY - 2.0, BACK_Z + 16.0]
    for k, (x, y) in {"scr_clamp": rs_holes()[0], "ins_spider": rs_holes()[1]}.items():
        pass

    CP = ["cp_knob", "cp_glass", "cp_housing", "cp_pcb", "cp_conn"]
    RSB = ["rs_pcb", "rs_leds", "rs_xiao"]
    core = CP + ["spider", "scr_cp", "ins_spider", "board_spacers"] + RSB + ["carrier", "scr_clamp"]
    rh = rs_holes()

    def items(base, new):
        """base: names; new: list of (name, dz) moved along D z."""
        out = [{"mesh": n, "dz": 0.0, "new": False} for n in base]
        out += [{"mesh": n, "dz": float(dz), "new": True} for n, dz in new]
        return out

    REAR, FRONT = (150, 18), (-35, 14)
    lift = 9
    stack = core + ["light_guide", "foam_mic"]
    up = 62                                   # stack / front shell lifted along D +z
    steps = [
        dict(id="hero_front", title="Voice Clock", view=(-32, 12), items=items(
            core + ["light_guide", "front_shell", "mute_plunger", "rear_shell", "back_plate", "ins_back",
                    "speaker", "tpu_wash", "scr_spk", "usb"], []),
             callouts=[], ground=True),
        dict(id="hero_back", title="Back", view=(148, 14), items=items(
            core + ["light_guide", "front_shell", "mute_plunger", "rear_shell", "back_plate", "usb"], []),
             callouts=["back_plate", "usb", "mute_plunger", "rear_shell"], ground=True),
        dict(id="step_01", title="Heat-set inserts: spider (3)", view=REAR, items=items(
            [], [("spider", 0), ("ins_spider", -lift)]),
             callouts=["spider", "ins_spider"]),
        # the back plate's speaker bosses face into the clock: look at its inside face
        dict(id="step_01b", title="Heat-set inserts: back plate (2)", view=(-25, 38), items=items(
            [], [("back_plate", 0), ("ins_back", 12)]),
             callouts=["back_plate", "ins_back"],
             arrows=[[(x, 0, -26.8), (x, 0, -34.6)] for x in (-18.35, 18.35)]),
        dict(id="step_02", title="Spider bracket onto the CrowPanel", view=REAR, items=items(
            CP, [("spider", -22), ("ins_spider", -22), ("scr_cp", -40)]),
             callouts=["cp_knob", "spider", "ins_spider", "scr_cp"],
             arrows=[[(0, 0, -44), (0, 0, -26)]]),
        dict(id="step_03", title="Light guide from behind", view=(135, 20), items=items(
            CP + ["spider", "scr_cp", "ins_spider"], [("light_guide", -48)]),
             callouts=["light_guide", "spider", "cp_knob"],
             arrows=[[(0, -47, -95), (0, -47, -62)]]),
        dict(id="step_04", title="Spacers and reSpeaker", view=(118, 24), items=items(
            CP + ["spider", "scr_cp", "ins_spider", "light_guide"],
            [("board_spacers", -16), ("foam_mic", -42)] + [(n, -42) for n in RSB]),
             callouts=["board_spacers", "rs_pcb", "foam_mic", "light_guide"],
             arrows=[[(x, y, -56), (x, y, -44)] for x, y in rh] + [[(x, y, -24), (x, y, -17)] for x, y in rh]),
        dict(id="step_05", title="Carrier and clamp screws", view=REAR, items=items(
            CP + ["spider", "scr_cp", "ins_spider", "board_spacers", "light_guide"] + RSB,
            [("carrier", -26), ("scr_clamp", -48)]),
             callouts=["carrier", "scr_clamp", "rs_pcb"],
             arrows=[[(x, y, -56), (x, y, -38)] for x, y in rh]),
        dict(id="step_06", title="Mute button, then the stack into the rear shell", view=(-72, 20),
             items=[{"mesh": n, "dz": float(up), "new": False} for n in stack] +
                   [{"mesh": "rear_shell", "dz": 0.0, "new": True}, {"mesh": "mute_plunger", "dz": 0.0, "new": True}],
             callouts=["rear_shell", "mute_plunger", "carrier", "rs_pcb"],
             arrows=[[(0, -30, up + 45), (0, -30, up + 20)], [(0, 74, PLG_Z), (0, 63, PLG_Z)]]),
        dict(id="step_07", title="Snap on the front shell", view=(-58, 16), items=items(
            ["rear_shell", "mute_plunger"] + stack, [("front_shell", up)]),
             callouts=["front_shell", "rear_shell", "cp_knob", "mute_plunger"],
             arrows=[[(*polar(r_in_at(0) + 6, a), up + 20), (*polar(r_in_at(0) + 6, a), up - 5)] for a in SNAP_ANG[:2]]),
        dict(id="step_08", title="Speaker and USB-C on the back plate", view=(-62, 18), items=items(
            ["back_plate", "ins_back"], [("speaker", 28), ("foam_spk", 14), ("tpu_wash", 28), ("scr_spk", 48), ("usb", 5)]),
             callouts=["back_plate", "speaker", "foam_spk", "tpu_wash", "scr_spk", "usb"],
             arrows=[[(sx * SPK_EAR_PITCH / 2, SPK_CY, RS.EAR_TOP + 62), (sx * SPK_EAR_PITCH / 2, SPK_CY, RS.EAR_TOP + 44)]
                     for sx in (-1, 1)]),
        dict(id="step_09", title="Snap in the back plate", view=REAR, items=items(
            core + ["light_guide", "front_shell", "mute_plunger", "rear_shell"],
            [("back_plate", -40), ("ins_back", -40), ("speaker", -40), ("tpu_wash", -40), ("scr_spk", -40),
             ("usb", -40)]),
             callouts=["back_plate", "rear_shell", "usb", "speaker"],
             arrows=[[(*polar(30, a), BACK_Z - 75), (*polar(30, a), BACK_Z - 50)] for a in BSNAP_ANG]),
    ]
    for s in steps:
        s.setdefault("arrows", [])
        s.setdefault("ground", False)
        s["anchors"] = {}
        for c in s["callouts"]:
            dz = next((it["dz"] for it in s["items"] if it["mesh"] == c), 0.0)
            a = list(anchor[c])
            a[2] += dz
            s["anchors"][c] = a
    scene = dict(materials=MAT, labels=LABEL, steps=steps,
                 frame=dict(tilt=TILT, foot_h=FOOT_H, display_r=33.0, display_z=12.5 + CP_Z0))
    (HERE / "scene.json").write_text(json.dumps(scene, indent=1))
    print("wrote", HERE / "scene.json", len(steps), "scenes,", len(list(MESH.glob("*.ply"))), "meshes")


if __name__ == "__main__":
    main()
