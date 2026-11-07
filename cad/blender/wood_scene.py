"""Add the turned-wood variant to blender/scene.json (run after export_scene.py and ../wood.py).

Each wood shell is split into its four paint regions (exactly what the slicer will assign to
each toolhead) and rendered with the matching wood PLA material.

  .venv/bin/python blender/wood_scene.py
  flatpak run --filesystem=home org.blender.Blender -b -P "$PWD/blender/render_scene.py" -- \
      --only hero_wood_front,hero_wood_back,hero_wood_top,hero_wood_parts
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
TONES = {1: "pla_core", 2: "wood_cherry", 3: "wood_cherry_hot", 4: "wood_walnut"}   # v2 heads (paint state = head + 1)


def main():
    S = json.loads((HERE / "scene.json").read_text())
    shells = []
    for part in ("front_shell", "rear_shell", "back_plate"):
        m = trimesh.load(OUT / "wood" / f"{part}_D.ply", process=False)
        paint = np.load(OUT / "wood" / f"{part}_paint.npy")
        paint = np.where(paint == 0, 1, paint)                  # unpainted = object default (plain-PLA core)
        for state, mat in TONES.items():
            sel = paint == state
            if not sel.any():
                continue
            sub = trimesh.Trimesh(m.vertices, m.faces[sel], process=False)
            sub.remove_unreferenced_vertices()
            name = f"wd_{part}_{mat}"
            sub.export(MESH / f"{name}.ply")
            S["materials"][name] = mat
            shells.append((part, name))
    shutil.copy(MESH / "mute_plunger.ply", MESH / "wd_plunger.ply")
    S["materials"]["wd_plunger"] = "wood_walnut"
    S["labels"]["wd_plunger"] = "Mute button (walnut)"

    CP = ["cp_knob", "cp_glass", "cp_pcb", "cp_conn"]
    core = CP + ["spider", "ring_base", "ring_shell", "rs_pcb", "rs_leds", "rs_xiao", "carrier", "foot_pad_front",
                 "foot_pad_rear", "ballast_fill"]
    whole = [n for _, n in shells] + ["wd_plunger"]

    def items(names, dz=None):
        dz = dz or {}
        return [{"mesh": n, "dz": float(dz.get(n, 0.0)), "new": True} for n in names]

    front = [n for p, n in shells if p == "front_shell"]
    back = [n for p, n in shells if p == "back_plate"]
    wood = [
        dict(id="hero_wood_front", title="Turned wood", view=(-32, 12), items=items(core + whole + ["usb"]),
             callouts=[], ground=True),
        dict(id="hero_wood_back", title="Turned wood, back", view=(148, 14), items=items(core + whole + ["usb"]),
             callouts=[], ground=True),
        dict(id="hero_wood_top", title="Turned wood, from above", view=(-60, 48), items=items(core + whole + ["usb"]),
             callouts=[], ground=True),
        dict(id="hero_wood_parts", title="Turned wood, shells apart", view=(-70, 18),
             items=items(core + whole + ["usb"], {**{n: 55 for n in front}, **{n: -45 for n in back}, "usb": -45}),
             callouts=[], ground=False),
    ]
    for s in wood:
        s.update(arrows=[], anchors={})
    S["steps"] = [s for s in S["steps"] if not s["id"].startswith("hero_wood")] + wood
    (HERE / "scene.json").write_text(json.dumps(S, indent=1))
    print("wood scenes:", [s["id"] for s in wood], "meshes:", len(shells) + 1)


if __name__ == "__main__":
    main()
