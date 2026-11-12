"""Slice the TPU plate for the U1: grip pads + speaker washers on head 4 (T3), 0.4 nozzle.

  .venv/bin/python voice_clock.py && .venv/bin/python slice_tpu.py
      -> out/tpu/TPU_U1.3mf (project) + TPU_U1.gcode

Heads 1-3 are listed only so the TPU lands on head 4 (the slot the other U1 files use for TPU);
nothing prints from them. Object settings from make_3mf.SETTINGS: 100 % infill, 2 walls, a 3 mm
brim on the small washers only. Engineering plate.
"""
import json
import shutil

import make_3mf as M3
import wood_project as W

OUT = M3.OUT / "tpu"
TPU_BASE = "Snapmaker TPU 95A HF @U1 0.4 nozzle"
FILLER = "Snapmaker PETG Translucent @U1 0.4 nozzle"        # heads 1-3: unused on this plate
PROC_BASE = "0.20mm Standard @Snapmaker U1 (0.4 nozzle)"
PROC_NAME = "0.20mm TPU parts @Snapmaker U1 (0.4 nozzle)"
ITEMS = [("foot_pads", 4, 110, 135, 0), ("tpu_washers", 4, 175, 135, 0)]
PROC = {
    "skirt_loops": "0",
    "enable_support": "0",
    "enable_prime_tower": "0",
    "curr_bed_type": "Engineering Plate",
}


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    sliced = OUT / "sliced"
    sliced.mkdir(parents=True)
    model = OUT / "TPU_model.3mf"
    M3.write(model, [("TPU - grip pads + speaker washers - head 4", M3.place(ITEMS))])

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
        files[kind] = OUT / f"{kind}.json"
        files[kind].write_text(json.dumps(d, indent=1))
    fil_files = []
    for i, base in enumerate([FILLER, FILLER, FILLER, TPU_BASE], 1):
        f = W.resolve(base)
        name = f"TPU 95A HF @U1" if base == TPU_BASE else f"unused head {i} @U1"
        f.update({"name": name, "from": "User", "inherits": base, "filament_settings_id": [name],
                  "compatible_printers": [W.PRINTER]})
        f.pop("setting_id", None)
        p = OUT / f"filament_{i}.json"
        p.write_text(json.dumps(f, indent=1))
        fil_files.append(str(p))

    common = ["--arrange", "0", "--load-settings", f"{files['machine']};{files['process']}",
              "--load-filaments", ";".join(fil_files)]
    proj = OUT / "TPU_U1.3mf"
    r = W.flatpak_cli(common + ["--export-3mf", str(proj), str(model)], timeout=900)
    print("project rc", r.returncode, proj if proj.exists() else "MISSING")
    r = W.flatpak_cli(common + ["--slice", "0", "--outputdir", str(sliced), str(model)], timeout=900)
    res = (sliced / "result.json").read_text() if (sliced / "result.json").exists() else ""
    print("slice rc", r.returncode, res[:600])
    if r.returncode:
        print(r.stderr[-3000:], r.stdout[-3000:])
    g = sliced / "plate_1.gcode"
    if g.exists():
        shutil.copy(g, OUT / "TPU_U1.gcode")
        print("gcode ->", OUT / "TPU_U1.gcode")


if __name__ == "__main__":
    main()
