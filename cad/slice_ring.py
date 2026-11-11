"""Slice the light ring for the U1: natural/translucent PETG on head 1 (T0), white PETG on head 2 (T1).

  .venv/bin/python make_3mf.py && .venv/bin/python slice_ring.py
      -> out/light_ring/LightRing_PETG_U1.3mf (project) + LightRing_PETG_U1.gcode
         + LightRingShell_PETG_U1.* (the outer ring_shell only, for a reprint)

ring_shell is one object from two bodies: natural PETG for the cap and the band above the sphere,
white PETG for the rest of the sleeve. ring_base is all white. No brim (it can't be peeled off the
thin walls). Both heads use the Snapmaker PETG Translucent profile (250 C; engineering plate at 70 C);
only the colour differs.
"""
import json
import shutil

import make_3mf as M3
import wood_project as W

OUT = M3.OUT / "light_ring"
FIL_BASE = "Snapmaker PETG Translucent @U1 0.4 nozzle"
PROC_BASE = "0.20mm Standard @Snapmaker U1 (0.4 nozzle)"
PROC_NAME = "0.20mm Light ring PETG @Snapmaker U1 (0.4 nozzle)"
FILS = [("PETG natural @U1", "#E8F2F6"), ("PETG white @U1", "#FFFFFF")]
ITEMS = [("ring_shell_2c", 2, 75, 135, 0), ("ring_base", 2, 190, 135, 0)]
SHELL_ONLY = [("ring_shell_2c", 2, 135, 135, 0)]     # reprint just the outer piece (the part that changes most)

PROC = {
    "wall_loops": "3",
    "brim_type": "no_brim",
    "skirt_loops": "0",
    "enable_support": "0",
    "curr_bed_type": "Engineering Plate",    # 70 C (the default Cool Plate runs PETG on a 0 C bed). On a
                                             # textured PEI plate use 80 C: the cap face comes out matte
    "enable_prime_tower": "1",
}


def main(items=ITEMS, stem="LightRing", title="Light ring - PETG natural T1 + white T2"):
    sliced = OUT / f"sliced_{stem}"
    shutil.rmtree(sliced, ignore_errors=True)
    sliced.mkdir(parents=True)
    model = OUT / f"{stem}_PETG_model.3mf"
    M3.write(model, [(title, M3.place(items))])

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
    for name, col in FILS:
        f = W.resolve(FIL_BASE)
        f.update({"name": name, "from": "User", "inherits": FIL_BASE, "filament_settings_id": [name],
                  "filament_colour": [col], "default_filament_colour": [col], "compatible_printers": [W.PRINTER]})
        for k in ("eng_plate_temp", "eng_plate_temp_initial_layer"):
            f[k] = ["70"]
        f.pop("setting_id", None)
        p = OUT / f"{name}.json"
        p.write_text(json.dumps(f, indent=1))
        fil_files.append(str(p))

    common = ["--arrange", "0", "--load-settings", f"{files['machine']};{files['process']}",
              "--load-filaments", ";".join(fil_files)]
    proj = OUT / f"{stem}_PETG_U1.3mf"
    r = W.flatpak_cli(common + ["--export-3mf", str(proj), str(model)], timeout=900)
    print("project rc", r.returncode, proj if proj.exists() else "MISSING")
    r = W.flatpak_cli(common + ["--slice", "0", "--outputdir", str(sliced), str(model)], timeout=900)
    res = (sliced / "result.json").read_text() if (sliced / "result.json").exists() else ""
    print("slice rc", r.returncode, res[:800])
    if r.returncode:
        print(r.stderr[-3000:], r.stdout[-3000:])
    g = sliced / "plate_1.gcode"
    if g.exists():
        shutil.copy(g, OUT / f"{stem}_PETG_U1.gcode")
        print("gcode ->", OUT / f"{stem}_PETG_U1.gcode")


if __name__ == "__main__":
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    main()
    main(SHELL_ONLY, "LightRingShell", "Light ring outer shell only - PETG natural T1 + white T2")
