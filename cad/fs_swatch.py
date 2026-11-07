"""Full Spectrum tone swatch for the walnut_fs style: a 72 x 3 x 4 mm plate whose front face shows the 8 tones
as 9 mm stripes (darkest left), sliced with the same presets and mixed rows as the clock.

  .venv/bin/python fs_swatch.py walnut_fs          # 0.08 mm layers
  .venv/bin/python fs_swatch.py walnut_fs fine     # 0.04 mm layers
-> out/wood_walnut_fs/coupons/FS_swatch_<layer>.3mf and .gcode

Print it before the clock: it shows each mixed tone's real colour and whether the layer height prints
cleanly in wood PLA. Stripe order (left to right) is wood.FS_TONES.
"""
import json
import shutil
import sys

import numpy as np
import trimesh

if "walnut_fs" not in sys.argv:
    sys.argv.append("walnut_fs")
import wood_project as P                     # presets, CLI wrapper, FILAMENTS (style walnut_fs)
from wood import FS_TONES, WOOD_OUT

W_, T_, H_ = 72.0, 3.0, 4.0          # 4 mm tall: enough to judge the blend; every layer costs 3 tool changes


def swatch_mesh():
    m = trimesh.creation.box(extents=(W_, T_, H_))
    m.apply_translation((0, 0, H_ / 2))
    for _ in range(7):
        m = m.subdivide()
    m.merge_vertices()
    c, n = m.triangles_center, m.face_normals
    paint = np.zeros(len(m.faces), np.int8)
    front = n[:, 1] < -0.9
    k = np.clip(((c[:, 0] + W_ / 2) // (W_ / len(FS_TONES))).astype(int), 0, len(FS_TONES) - 1)
    states = np.array([t[0] for t in FS_TONES])
    paint[front] = states[k[front]]
    return m, paint


if __name__ == "__main__":
    out = WOOD_OUT / "coupons"
    out.mkdir(parents=True, exist_ok=True)
    pre = out / "presets"
    pre.mkdir(exist_ok=True)
    fil = []
    for name, col, temp, base, maxvol in P.FILAMENTS:
        fp = pre / f"{name}.json"
        fp.write_text(json.dumps(P.filament_preset(name, col, temp, base, maxvol), indent=4))
        fil.append(fp)
    proc = pre / f"{P.PROCESS_NAME} - resolved.json"
    proc.write_text(json.dumps(P.process_preset_full(), indent=4))
    mach = pre / "Snapmaker U1 (0.4 nozzle) - resolved.json"
    mach.write_text(json.dumps(P.machine_preset(), indent=4))
    m, paint = swatch_mesh()
    m.apply_translation((135, 135, 0))
    tag = f"FS_swatch_{P.FS_LAYER.replace('.', '')}"
    model = out / f"{tag}.3mf"
    P.M3.write(model, [(f"Full Spectrum walnut tones {P.FS_LAYER} mm", [("fs_swatch", 1, m)])], paints={"fs_swatch": paint})
    sl = out / "sliced"
    shutil.rmtree(sl, ignore_errors=True)
    sl.mkdir()
    common = ["--arrange", "0", "--load-settings", f"{mach};{proc}", "--load-filaments", ";".join(str(f) for f in fil)]
    r = P.flatpak_cli(common + ["--slice", "0", "--outputdir", str(sl), str(model)])
    print("slice rc", r.returncode, (sl / "result.json").read_text()[:200] if (sl / "result.json").exists() else r.stderr[-800:])
    g = sl / "plate_1.gcode"
    shutil.copy(g, out / f"{tag}.gcode")
    txt = g.read_text(errors="ignore")
    for key in ("estimated printing time (normal mode)", "total filament change", "total layer number", "total filament used [g]"):
        line = next((l for l in txt.splitlines() if key in l), "")
        print(line.strip())
