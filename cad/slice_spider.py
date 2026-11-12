"""Slice the spider alone for the U1 (after a CP_ROT_TRIM_DEG change), in PLA Matte on one head.

  .venv/bin/python voice_clock.py && .venv/bin/python slice_spider.py [head]   (default head 4)
      -> out/spider/Spider_PLA_U1.3mf (project) + Spider_PLA_U1.gcode

Plate down, 100 % infill (make_3mf.SETTINGS), no brim, engineering plate. The other heads are fillers.
"""
import json
import shutil

import make_3mf as M3
import wood_project as W

OUT = M3.OUT / "spider"
PLA_BASE = "Snapmaker PLA Matte @U1"
FILLER = "Snapmaker PETG Translucent @U1 0.4 nozzle"
PROC_BASE = "0.20mm Standard @Snapmaker U1 (0.4 nozzle)"
PROC_NAME = "0.20mm spider @Snapmaker U1 (0.4 nozzle)"
PROC = {"skirt_loops": "0", "enable_support": "0", "enable_prime_tower": "0", "brim_type": "no_brim",
        "curr_bed_type": "Engineering Plate"}


def main(slot=4):
    shutil.rmtree(OUT, ignore_errors=True)
    sliced = OUT / "sliced"
    sliced.mkdir(parents=True)
    model = OUT / "Spider_PLA_model.3mf"
    M3.write(model, [(f"Spider - PLA head {slot}", M3.place([("spider", slot, 135, 135, 0)]))])
    mach = W.resolve(W.PRINTER)
    mach["from"] = "system"
    proc = W.resolve(PROC_BASE)
    proc.update({"name": PROC_NAME, "from": "User", "inherits": PROC_BASE, "print_settings_id": PROC_NAME,
                 "compatible_printers": [W.PRINTER]})
    proc.update(PROC)
    proc.pop("setting_id", None)
    proc.pop("wipe_tower_filament", None)       # the 2.4.1 CLI segfaults on it
    files = {}
    for kind, d in (("machine", mach), ("process", proc)):
        files[kind] = sliced / f"{kind}.json"
        files[kind].write_text(json.dumps(d, indent=1))
    fil_files = []
    for i in range(1, 5):
        base = PLA_BASE if i == slot else FILLER
        f = W.resolve(base)
        name = "PLA Matte @U1" if i == slot else f"unused head {i} @U1"
        f.update({"name": name, "from": "User", "inherits": base, "filament_settings_id": [name],
                  "compatible_printers": [W.PRINTER]})
        if i == slot:
            f["eng_plate_temp"] = f["eng_plate_temp_initial_layer"] = ["60"]
        f.pop("setting_id", None)
        p = sliced / f"filament_{i}.json"
        p.write_text(json.dumps(f, indent=1))
        fil_files.append(str(p))
    common = ["--arrange", "0", "--load-settings", f"{files['machine']};{files['process']}",
              "--load-filaments", ";".join(fil_files)]
    proj = OUT / "Spider_PLA_U1.3mf"
    r = W.flatpak_cli(common + ["--export-3mf", str(proj), str(model)], timeout=900)
    print("project rc", r.returncode, proj if proj.exists() else "MISSING")
    r = W.flatpak_cli(common + ["--slice", "0", "--outputdir", str(sliced), str(model)], timeout=900)
    print("slice rc", r.returncode)
    if r.returncode:
        print(r.stderr[-3000:], r.stdout[-3000:])
    g = sliced / "plate_1.gcode"
    if g.exists():
        shutil.copy(g, OUT / "Spider_PLA_U1.gcode")
        print("gcode ->", OUT / "Spider_PLA_U1.gcode")


if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
