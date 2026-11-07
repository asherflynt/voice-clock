"""Draft fit-test print set for v2: short bands of the shells at every interface, plus the small
real parts, untextured, with light draft settings (2 walls, 10 % infill, layer height left at your
preset so the fits stay representative).

  .venv/bin/python fit_tests.py     -> out/fit_tests/VoiceClock_v2_fit_tests.3mf (+ per-plate files)

What each band tests:
  fit_front_band  seam rim, the 7 bayonet blocks with the 4 detent fingers, mic-boot bottoms (gaskets)
  fit_rear_band   collar + lugs + stop posts (twist lock with fit_front_band), cradle pads and the 4 key
                  ribs (drop your real reSpeaker + carrier in), mute plunger bore, floor pocket
  fit_back_ring   rear shell's back opening: lip, entry notches, pawl notches, hard stop (with back_plate)
  fit_front_top   the light-ring bore and the sphere edge round it (with ring_shell on the stack)
"""
import json
import os
import shutil

import numpy as np
import trimesh
from build123d import export_stl, Pos

import voice_clock as V
import make_3mf as M3

OUTF = V.OUT / "fit_tests"
BANDS = {
    "fit_front_band": (V.front_shell, V.SPLIT_Z, 9.5),
    "fit_rear_band": (V.rear_shell, -15.5, V.COL_TOP + 0.5),
    "fit_back_ring": (V.rear_shell, V.BACK_Z, V.BACK_Z + 7.0),
    "fit_front_top": (V.front_shell, 27.0, 40.0),
}
REAL = ["back_plate", "mute_plunger", "ring_base", "ring_shell", "carrier", "spider"]
DRAFT = {"wall_loops": "2", "sparse_infill_density": "10%", "enable_support": "0", "brim_type": "no_brim"}
RING_BRIM = {**DRAFT, "brim_type": "outer_only", "brim_width": "3"}

PLATES = [
    ("Draft 1 - shell bands (PLA)", [("fit_front_band", 2, 67, 69, 0), ("fit_rear_band", 2, 201, 69, 0)]),
    ("Draft 2 - back plate, back opening, ring bore, plunger (PLA)",
     [("back_plate", 2, 52, 52, 0), ("fit_back_ring", 2, 52, 150, 0), ("fit_front_top", 2, 175, 80, 0),
      ("mute_plunger", 2, 175, 200, 0)]),
    ("Draft 3 - light ring, carrier, spider (any PLA is fine for a fit check)",
     [("carrier", 1, 62, 62, 0), ("ring_shell", 1, 62, 205, 0), ("ring_base", 1, 200, 205, 0),
      ("spider", 1, 200, 45, 0)]),
]


def export_print(name, shape, rot):
    p = rot * shape
    bb = p.bounding_box()
    p = Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * p
    f = OUTF / f"{name}.stl"
    export_stl(p, str(f), tolerance=0.02, angular_tolerance=0.15)
    return f


if __name__ == "__main__":
    OUTF.mkdir(parents=True, exist_ok=True)
    built = {}
    for name, (fn, z0, z1) in BANDS.items():
        key = fn.__name__
        if key not in built:
            built[key] = fn()
        band = built[key] & V.zslab(z0, z1)
        assert band is not None and len(band.solids()) >= 1, name
        export_print(name, band, V.Rot(0, 0, 0))
        print(f"  {name}: z {z0:.1f}..{z1:.1f}, {len(band.solids())} solid(s), vol {band.volume / 1000:.1f} cm3", flush=True)
    for name in REAL:
        export_print(name, V.PRINT_PARTS[name](), V.PRINT_ROT[name])
    # make_3mf loads out/<name>.ply first (textured shells); point it at the draft folder instead
    M3.OUT = OUTF
    for name in list(BANDS) + REAL:
        M3.SETTINGS[name] = RING_BRIM if name.startswith("fit_") or name in ("ring_base", "ring_shell") else DRAFT
    placed = []
    for i, (pname, items) in enumerate(PLATES):
        ox, oy = M3.plate_origin(i, len(PLATES))
        placed.append((pname, M3.place(items, ox, oy)))
    M3.write(OUTF / "VoiceClock_v2_fit_tests.3mf", placed)
    for i, (pname, items) in enumerate(PLATES, 1):
        M3.write(OUTF / f"VoiceClock_v2_fit_plate{i}.3mf", [(pname, M3.place(items))])
    print("fit-test 3MFs:", sorted(p.name for p in OUTF.glob("*.3mf")))
