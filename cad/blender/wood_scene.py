"""Add the turned-wood variant to blender/scene.json (run after export_scene.py and ../wood.py).

Each wood shell is split into its four paint regions (exactly what the slicer will assign to
each toolhead) and rendered with the matching wood PLA material.

  .venv/bin/python blender/wood_scene.py
  flatpak run --filesystem=home org.blender.Blender -b -P "$PWD/blender/render_scene.py" -- \
      --only hero_wood_front,hero_wood_back,hero_wood_top,hero_wood_parts
  .venv/bin/python blender/wood_scene.py walnut   # the walnut style (after wood.py walnut): hero_walnut_*
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from voice_clock import OUT, BACK_Z, SPLIT_Z  # noqa: E402

MESH = HERE / "meshes"
STYLE = next((a for a in ("walnut_fs", "walnut") if a in sys.argv[1:]), "cherry")
SRC = OUT / {"cherry": "wood", "walnut": "wood_walnut", "walnut_fs": "wood_walnut_fs"}[STYLE]
EXTRA = {}
if STYLE == "walnut_fs":       # paint states: 2 oak, 4 walnut, 5.. mixed rows; tones rendered as their optical mix
    sys.path.insert(0, str(HERE.parent))
    from wood import FS_TONES

    def _lin(h):
        c = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255
        return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

    def _hex(l):
        c = np.where(l <= 0.0031308, 12.92 * l, 1.055 * np.maximum(l, 1e-9) ** (1 / 2.4) - 0.055)
        return "#%02X%02X%02X" % tuple(int(round(x * 255)) for x in np.clip(c, 0, 1))
    RENDER = {"1": "#5A3B2A", "2": "#8E6B47", "3": "#C6AA80", "4": "#36221A"}   # render colours of the 4 heads
    TONES = {1: "pla_core", 3: "wood_maple"}
    for st, pat, _ in FS_TONES:
        key = f"fs_{pat}"
        EXTRA[key] = _hex(np.mean([_lin(RENDER[c]) for c in pat], 0))
        TONES[st] = key
    PFX, SID, TITLE = "wf", "hero_walnut_fs", "Turned walnut, Full Spectrum"
elif STYLE == "walnut":
    TONES = {1: "pla_core", 2: "wood_oak", 3: "wood_cherry", 4: "wood_walnut"}   # core, oak, cherry, walnut
    PFX, SID, TITLE = "wn", "hero_walnut", "Turned walnut"
else:
    TONES = {1: "pla_core", 2: "wood_cherry", 3: "wood_cherry_hot", 4: "wood_walnut"}   # v2 heads (paint state = head + 1)
    PFX, SID, TITLE = "wd", "hero_wood", "Turned wood"


def main():
    S = json.loads((HERE / "scene.json").read_text())
    shells = []
    for part in ("front_shell", "rear_shell", "back_plate"):
        m = trimesh.load(SRC / f"{part}_D.ply", process=False)
        paint = np.load(SRC / f"{part}_paint.npy")
        paint = np.where(paint == 0, 1, paint)                  # unpainted = object default (plain-PLA core)
        for state, mat in TONES.items():
            sel = paint == state
            if not sel.any():
                continue
            sub = trimesh.Trimesh(m.vertices, m.faces[sel], process=False)
            sub.remove_unreferenced_vertices()
            name = f"{PFX}_{part}_{mat}"
            sub.export(MESH / f"{name}.ply")
            S["materials"][name] = mat
            shells.append((part, name))
    plg = f"{PFX}_plunger"
    shutil.copy(MESH / "mute_plunger.ply", MESH / f"{plg}.ply")
    S["materials"][plg] = "wood_walnut"
    S["labels"][plg] = "Mute button (walnut)"

    CP = ["cp_knob", "cp_glass", "cp_pcb", "cp_conn"]
    core = CP + ["spider", "ring_base", "ring_shell", "rs_pcb", "rs_leds", "rs_xiao", "carrier", "foot_pad_front",
                 "foot_pad_rear", "ballast_fill"]
    whole = [n for _, n in shells] + [plg]

    def items(names, dz=None):
        dz = dz or {}
        return [{"mesh": n, "dz": float(dz.get(n, 0.0)), "new": True} for n in names]

    front = [n for p, n in shells if p == "front_shell"]
    back = [n for p, n in shells if p == "back_plate"]
    wood = [
        dict(id=f"{SID}_front", title=TITLE, view=(-32, 12), items=items(core + whole + ["usb"]),
             callouts=[], ground=True),
        dict(id=f"{SID}_back", title=f"{TITLE}, back", view=(148, 14), items=items(core + whole + ["usb"]),
             callouts=[], ground=True),
        dict(id=f"{SID}_top", title=f"{TITLE}, from above", view=(-60, 48), items=items(core + whole + ["usb"]),
             callouts=[], ground=True),
        dict(id=f"{SID}_parts", title=f"{TITLE}, shells apart", view=(-70, 18),
             items=items(core + whole + ["usb"], {**{n: 55 for n in front}, **{n: -45 for n in back}, "usb": -45}),
             callouts=[], ground=False),
    ]
    for s in wood:
        s.update(arrows=[], anchors={})
    S.setdefault("wood_tones", {}).update(EXTRA)
    mine = {f"{SID}_{v}" for v in ("front", "back", "top", "parts")}     # exact ids: hero_walnut_ is a prefix of hero_walnut_fs_
    S["steps"] = [s for s in S["steps"] if s["id"] not in mine] + wood
    (HERE / "scene.json").write_text(json.dumps(S, indent=1))
    print("wood scenes:", [s["id"] for s in wood], "meshes:", len(shells) + 1)


if __name__ == "__main__":
    main()
