"""Bambu Lab project 3MFs (for MakerWorld / Bambu Studio): X1 Carbon, P1S, A1 and A1 mini.

  .venv/bin/python voice_clock.py && .venv/bin/python make_bambu.py
      -> out/bambu/VoiceClock_<printer>.3mf (Bambu Studio project: printer, process, filaments, plates)
         + VoiceClock_<printer>_sliced.3mf (the same, with every plate sliced: print times for MakerWorld)

Uses the Bambu Studio flatpak's CLI (flatpak install --user flathub com.bambulab.BambuStudio) and
its own system presets, so the files open in Bambu Studio with stock profiles selected.

Filament slots (AMS): 1 = PLA (shells, back plate, internals), 2 = translucent PETG (the light ring's
glowing band and cap), 3 = white PETG (rest of the light ring, mute button), 4 = TPU (grip pads,
speaker washers; TPU doesn't feed through the AMS: use the external spool for that plate).
Object settings (brims on the shells only, wall counts, 100 % infill on small parts) come from
make_3mf.SETTINGS. Every plate is also sliced here to check it.
"""
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import make_3mf as M3

APP = "com.bambulab.BambuStudio"
OUT = M3.OUT / "bambu"
HOME = Path.home()

PRINTERS = {   # file tag: (machine preset, bed size)
    "X1C": ("Bambu Lab X1 Carbon 0.4 nozzle", 256),
    "P1S": ("Bambu Lab P1S 0.4 nozzle", 256),
    "A1": ("Bambu Lab A1 0.4 nozzle", 256),
    "A1mini": ("Bambu Lab A1 mini 0.4 nozzle", 180),
}
# slot: (preferred system filament presets, colour)
FILAMENTS = [
    (["Bambu PLA Basic", "Generic PLA"], "#E9E6DF"),
    (["Bambu PETG Translucent", "Generic PETG"], "#E8F2F6"),
    (["Bambu PETG HF", "Bambu PETG Basic", "Generic PETG"], "#FFFFFF"),
    (["Bambu TPU 95A HF", "Generic TPU"], "#3A3A3A"),
]
PLA, PETG_CLEAR, PETG_WHITE, TPU = 1, 2, 3, 4
MULTI = {"ring_shell_2c": [("ring_shell_natural", PETG_CLEAR), ("ring_shell_white", PETG_WHITE)]}

# (plate name, [(part, slot, x, y, rot)]) laid out per bed size
PLATES_256 = [
    ("Shells - PLA", [("front_shell", PLA, 68, 68, 0), ("rear_shell", PLA, 188, 188, 0),
                      ("back_plate", PLA, 196, 60, 0)]),
    ("Internals - PLA", [("carrier", PLA, 70, 128, 0), ("spider", PLA, 192, 128, 0)]),
    ("Light ring - translucent + white PETG", [("ring_shell_2c", PETG_CLEAR, 66, 128, 0),
                                               ("ring_base", PETG_WHITE, 180, 128, 0),
                                               ("mute_plunger", PETG_WHITE, 180, 210, 0)]),
    ("Grip pads + speaker washers - TPU (external spool)", [("foot_pads", TPU, 100, 128, 0),
                                                            ("tpu_washers", TPU, 180, 128, 0)]),
]
PLATES_180 = [
    ("Front shell - PLA", [("front_shell", PLA, 90, 90, 0)]),
    ("Rear shell - PLA", [("rear_shell", PLA, 90, 90, 0)]),
    ("Back plate - PLA", [("back_plate", PLA, 90, 90, 0)]),
    ("Internals - PLA", [("carrier", PLA, 62, 90, 0), ("spider", PLA, 147, 90, 90)]),
    ("Light ring - translucent + white PETG", [("ring_shell_2c", PETG_CLEAR, 52, 52, 0),
                                               ("ring_base", PETG_WHITE, 130, 130, 0),
                                               ("mute_plunger", PETG_WHITE, 150, 30, 0)]),
    ("Grip pads + speaker washers - TPU (external spool)", [("foot_pads", TPU, 60, 90, 0),
                                                            ("tpu_washers", TPU, 135, 90, 0)]),
]
PROC = {
    "curr_bed_type": "Textured PEI Plate",
    "enable_prime_tower": "1",
    "brim_type": "no_brim",              # per-object brims (the shells) come from make_3mf.SETTINGS
    "enable_support": "0",
}


def profiles_dir():
    loc = subprocess.run(["flatpak", "info", "--user", "--show-location", APP], capture_output=True, text=True).stdout.strip()
    return Path(loc) / "files/share/BambuStudio/profiles/BBL"


PROFILES = profiles_dir()
BY_NAME = {}
for kind in ("machine", "process", "filament"):
    for p in (PROFILES / kind).glob("*.json"):
        try:
            d = json.loads(p.read_text())
        except ValueError:
            continue
        BY_NAME[(kind, d.get("name", p.stem))] = d


def resolve(kind, name):
    d = BY_NAME[(kind, name)]
    base = resolve(kind, d["inherits"]) if d.get("inherits") else {}
    out = {**base, **d}
    out.pop("inherits", None)
    return out


def pick(kind, prefixes, machine):
    for pre in prefixes:
        for (k, n), d in sorted(BY_NAME.items()):
            if k == kind and n.startswith(pre + " @") and "nozzle" not in n.split("@")[1].replace("0.4 nozzle", "") \
                    and machine in (d.get("compatible_printers") or []) and d.get("instantiation", "true") == "true":
                return n
    raise SystemExit(f"no {kind} preset for {machine} from {prefixes}")


def cli(args, timeout=1800):
    return subprocess.run(["flatpak", "run", APP] + args, capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, "HOME": str(HOME)})


def build(tag):
    machine, bed = PRINTERS[tag]
    plates = PLATES_256 if bed == 256 else PLATES_180
    M3.BED, M3.STRIDE = float(bed), bed * 1.2
    M3.MULTI.update(MULTI)
    work = OUT / f"_{tag}"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    placed = []
    for i, (pname, items) in enumerate(plates):
        ox, oy = M3.plate_origin(i, len(plates))
        placed.append((pname, M3.place(items, ox, oy)))
    model = work / f"VoiceClock_{tag}_model.3mf"
    M3.write(model, placed)

    mach = resolve("machine", machine)
    proc_name = pick("process", ["0.20mm Standard"], machine)
    proc = resolve("process", proc_name)
    proc.update(PROC)
    # prime tower (light ring plate only) in a free corner: the stock spot (15, 220) is off the A1 mini's bed
    wx, wy = ("15", "205") if bed == 256 else ("8", "112")
    proc["wipe_tower_x"], proc["wipe_tower_y"] = [wx] * len(plates), [wy] * len(plates)   # one value per plate
    fil_names = [pick("filament", prefs, machine) for prefs, _ in FILAMENTS]
    files = []
    for kind, d in (("machine", mach), ("process", proc)):
        p = work / f"{kind}.json"
        p.write_text(json.dumps(d, indent=1))
        files.append(str(p))
    fils = []
    for (prefs, col), name in zip(FILAMENTS, fil_names):
        d = resolve("filament", name)
        d["filament_colour"] = [col]
        p = work / f"filament_{len(fils) + 1}.json"
        p.write_text(json.dumps(d, indent=1))
        fils.append(str(p))
    common = ["--load-settings", ";".join(files), "--load-filaments", ";".join(fils), "--arrange", "0", "--orient", "0"]
    proj = OUT / f"VoiceClock_{tag}.3mf"
    r = cli(common + ["--export-3mf", str(proj), str(model)])
    ok = proj.exists()
    print(f"{tag}: {machine} | {proc_name} | {', '.join(fil_names)}")
    print(f"  project rc {r.returncode} {'ok' if ok else 'MISSING'}")
    if not ok:
        print(r.stdout[-2000:], r.stderr[-2000:])
        return
    sl = work / "sliced"
    sl.mkdir()
    sliced_proj = OUT / f"VoiceClock_{tag}_sliced.3mf"     # what Bambu Studio saves after "Slice all"
    r = cli(common + ["--slice", "0", "--export-3mf", sliced_proj.name, "--outputdir", str(sl), str(model)])
    if (sl / sliced_proj.name).exists():                    # the CLI writes it inside --outputdir
        shutil.move(sl / sliced_proj.name, sliced_proj)
    res = json.loads((sl / "result.json").read_text()) if (sl / "result.json").exists() else {}
    print(f"  slice rc {r.returncode} {res.get('error_string', '')}")
    for p in res.get("sliced_plates", []):
        if p.get("warning_message"):
            print(f"  plate {p['id']} warning: {p['warning_message']}")
    for g in sorted(sl.glob("plate_*.gcode")):
        t = next((l.split("total estimated time:")[1].strip() for l in g.open() if "total estimated time:" in l), "?")
        print(f"  {g.stem}: {t}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    import sys
    for tag in (sys.argv[1:] or PRINTERS):
        build(tag)
