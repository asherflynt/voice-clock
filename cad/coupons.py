"""Wood-tone test coupon C1 (see /tmp/vc_design/WOOD_GRAIN_PLAN.md, section 4).

Three columns, one per outer-wall flow (37 / 60 / 119 mm/s = 2.5 / 4 / 8 mm3/s at 0.42 x 0.16 mm),
each with a vertical wall and a 50 deg slope, stacked in four 8 mm temperature tiers
(205 / 220 / 235 / 245 C) printed from ONE head. A temperature tower is fine for a coupon: it only
has to show which temperature gives a usable, even step from the 205 C base tone.

  .venv/bin/python coupons.py [preset name]   -> out/wood/coupons/C1_<spool>.3mf + .gcode
Default spool: "JAYO Wood Cherry @U1". Photograph under fixed light next to a grey card.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import trimesh
from build123d import Box, Pos, Align, Polygon, Plane, extrude, export_stl

import make_3mf as M3
import wood_project as WP

OUTC = WP.WOOD_OUT / "coupons"
TIERS = [205, 220, 235, 245]
TIER_H = 8.0
FLOWS = [("c1_2p5", 37), ("c1_4", 60), ("c1_8", 119)]   # object name, outer wall mm/s


def column():
    """20 x 14 block, 32 mm tall, with a 50 deg slope on its +y face."""
    h = TIER_H * len(TIERS)
    run = h / np.tan(np.radians(50))
    prof = Plane.YZ * Polygon((0, 0), (14 + run, 0), (14, h), (0, h), align=None)
    return Pos(-10, 0, 0) * extrude(prof, amount=20)


def post(gcode, temps, tier_h, first_layer=0.2):
    """Set the head's temperature at the start of each tier (waits so each tier is at temperature)."""
    lines = open(gcode, encoding="utf-8", errors="surrogateescape").read().split("\n")
    out, tier = [], 0
    for ln in lines:
        out.append(ln)
        if ln.startswith(";Z:"):
            z = float(ln[3:])
            k = min(int((z - first_layer + 1e-6) // tier_h), len(temps) - 1)
            if k > tier:
                tier = k
                out.append(f"M109 S{temps[k]} ; C1 tier {k + 1}: {temps[k]} C")
    open(gcode, "w", encoding="utf-8", errors="surrogateescape").write("\n".join(out))


if __name__ == "__main__":
    spool = sys.argv[1] if len(sys.argv) > 1 else "JAYO Wood Cherry @U1"
    OUTC.mkdir(parents=True, exist_ok=True)
    stl = OUTC / "_column.stl"
    export_stl(column(), str(stl), tolerance=0.02, angular_tolerance=0.1)
    meshes = []
    for i, (name, speed) in enumerate(FLOWS):
        m = trimesh.load(stl)
        m.apply_translation([90 + i * 45 - m.bounds[0][0], 110 - m.bounds[0][1], -m.bounds[0][2]])
        meshes.append((name, 1, m))
        M3.SETTINGS[name] = {"outer_wall_speed": str(speed), "wall_loops": "3", "sparse_infill_density": "15%"}
    stl.unlink()
    tag = re.sub(r"[^A-Za-z0-9]+", "_", spool).strip("_")
    model = OUTC / f"C1_{tag}.3mf"
    M3.write(model, [(f"C1 tone coupon - {spool}", meshes)])
    fil = next(f for f in WP.FILAMENTS if f[0] == spool)
    pre = WP.WOOD_OUT / "presets"
    fp = pre / f"{spool}.json"
    fp.write_text(json.dumps(WP.filament_preset(*fil[:3], fil[3], 8), indent=4))   # no 2.5 cap here
    proc = pre / f"{WP.PROCESS_NAME} - resolved.json"
    mach = pre / "Snapmaker U1 (0.4 nozzle) - resolved.json"
    sliced = OUTC / "sliced"
    shutil.rmtree(sliced, ignore_errors=True)
    sliced.mkdir()
    r = WP.flatpak_cli(["--arrange", "0", "--load-settings", f"{mach};{proc}", "--load-filaments", str(fp),
                        "--slice", "0", "--outputdir", str(sliced), str(model)])
    g = sliced / "plate_1.gcode"
    assert g.exists(), f"slicing failed: {r.stderr[-1500:]}"
    post(g, TIERS, TIER_H)
    dst = OUTC / f"C1_{tag}.gcode"
    shutil.copy(g, dst)
    t = next((ln for ln in open(dst, errors="ignore") if ln.startswith("; estimated printing time")), "").strip()
    print("C1 coupon:", model, "and", dst, t)
