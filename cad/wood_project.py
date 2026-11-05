"""Snapmaker Orca project for the turned-wood Voice Clock (4 x JAYO wood PLA on the U1).

  .venv/bin/python wood.py            # painted, textured meshes -> out/wood/
  .venv/bin/python wood_project.py    # presets + project 3MF + sliced, post-processed G-code

Outputs (out/wood/):
  VoiceClock_wood_model.3mf    painted model only (your own presets stay selected)
  VoiceClock_wood_U1.3mf       full project: printer, process, 4 filaments, post-processing
  VoiceClock_wood_U1.gcode     sliced + wood_temps.py applied, ready to send to the U1
  presets/*.json               the 4 JAYO filament presets + process preset (also installed
                               into Snapmaker Orca's user preset folder)
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import trimesh

import make_3mf as M3
from voice_clock import OUT

WOOD_OUT = OUT / "wood"
APP = "io.github.Snapmaker.Snapmaker_Orca"
REAL_HOME = Path(os.environ.get("VOICE_CLOCK_HOME", str(Path.home())))   # your login home
POST = REAL_HOME / ".local/share/voice-clock/wood_temps.py"
USER_PRESETS = REAL_HOME / ".var/app" / APP / "config/Snapmaker_Orca/user/default"

PRINTER = "Snapmaker U1 (0.4 nozzle)"
PROCESS_BASE = "0.20mm Standard @Snapmaker U1 (0.4 nozzle)"
FILAMENT_BASE = "Snapmaker PLA Wood @U1 0.4 nozzle"

# head -> JAYO spool. Paint state = head + 1. Cherry is also the unpainted structure inside.
FILAMENTS = [
    ("JAYO Wood Cherry @U1", "#8A4A32", 210),   # T0 heartwood earlywood
    ("JAYO Wood Walnut @U1", "#4A2A1C", 212),   # T1 heartwood latewood rings
    ("JAYO Wood Maple @U1", "#DCC497", 204),    # T2 sapwood earlywood
    ("JAYO Wood Oak @U1", "#A8804F", 206),      # T3 sapwood latewood ("logs" spool)
]
PROCESS_NAME = "0.20mm Turned Wood @Snapmaker U1 (0.4 nozzle)"
PROCESS_OVERRIDES = {
    "wall_loops": "4",
    "sparse_infill_density": "20%",
    "sparse_infill_pattern": "gyroid",
    "enable_support": "0",
    "mmu_segmented_region_max_width": "1.2",       # the wood colours go 1.2 mm deep, the core is cherry
    "mmu_segmented_region_interlocking_depth": "0",
    "post_process": [str(POST)],
    "outer_wall_speed": "80",                      # wood fibre likes a gentler outer wall
    "inner_wall_speed": "150",
    "seam_position": "back",
    "wipe_tower_x": ["150"],                       # prime tower in the free corner of the plate
    "wipe_tower_y": ["158"],
}
# plate layout (bed 270 x 270): shells side by side, back plate + walnut mute button below
LAYOUT = [("front_shell", 1, 67, 69), ("rear_shell", 1, 201, 69), ("back_plate", 1, 67, 205),
          ("mute_plunger", 2, 240, 245)]


# ------------------------------------------------------------------ system profiles
def profile_root():
    loc = subprocess.run(["flatpak", "info", "--show-location", APP], capture_output=True, text=True,
                         check=True).stdout.strip()
    return Path(loc) / "files/share/Snapmaker_Orca/profiles"


_INDEX = None


def find(name):
    global _INDEX
    if _INDEX is None:
        _INDEX = {}
        for p in profile_root().rglob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if isinstance(d, dict) and "name" in d:
                _INDEX.setdefault(d["name"], d)
    return _INDEX[name]


def resolve(name):
    """Flatten an inheritance chain into one full config dict."""
    d = find(name)
    base = resolve(d["inherits"]) if d.get("inherits") else {}
    out = dict(base)
    out.update({k: v for k, v in d.items() if k not in ("inherits", "instantiation")})
    return out


def filament_preset(name, colour, temp):
    f = resolve(FILAMENT_BASE)
    f.update({"name": name, "from": "User", "inherits": FILAMENT_BASE, "filament_vendor": ["JAYO"],
              "filament_settings_id": [name], "filament_colour": [colour], "default_filament_colour": [colour],
              "nozzle_temperature": [str(temp)], "nozzle_temperature_initial_layer": [str(temp + 5)],
              "nozzle_temperature_range_low": ["190"], "nozzle_temperature_range_high": ["230"],
              "filament_max_volumetric_speed": ["12"],     # 15 % wood fibre through a 0.4 nozzle
              "hot_plate_temp": ["60"], "hot_plate_temp_initial_layer": ["60"],
              "textured_plate_temp": ["60"], "textured_plate_temp_initial_layer": ["60"],
              "compatible_printers": [PRINTER]})
    f.pop("setting_id", None)
    return f


def process_preset():
    """User preset in Orca's own format: inherits + overrides (a fully flattened copy crashes the CLI)."""
    p = {"type": "process", "name": PROCESS_NAME, "from": "User", "inherits": PROCESS_BASE,
         "print_settings_id": PROCESS_NAME, "compatible_printers": [PRINTER], "version": "2.4.1.0"}
    p.update(PROCESS_OVERRIDES)
    return p


def process_preset_full():
    """Flattened copy for the CLI (it doesn't resolve "inherits" for loaded files).
    wipe_tower_filament is dropped: the 2.4.1 CLI segfaults on it."""
    p = resolve(PROCESS_BASE)
    p.update(process_preset())
    p.pop("setting_id", None)
    p.pop("wipe_tower_filament", None)
    return p


def filament_user_preset(name, colour, temp):
    """Same filament as filament_preset(), stored the way the GUI saves user presets."""
    full = filament_preset(name, colour, temp)
    base = resolve(FILAMENT_BASE)
    d = {k: v for k, v in full.items() if base.get(k) != v}
    d.update({"type": "filament", "name": name, "from": "User", "inherits": FILAMENT_BASE, "version": "2.4.1.0"})
    return d


def machine_preset():
    m = resolve(PRINTER)
    m["from"] = "system"
    return m


# ------------------------------------------------------------------ model 3MF
def placed_meshes():
    meshes, paints = [], {}
    for name, ext, x, y in LAYOUT:
        if name == "mute_plunger":
            m = trimesh.load(OUT / "mute_plunger.stl")
            m.merge_vertices()
            paint = None
        else:
            m = trimesh.load(WOOD_OUT / f"{name}.ply", process=False)
            paint = np.load(WOOD_OUT / f"{name}_paint.npy")
            assert len(paint) == len(m.faces), name
        b = m.bounds
        m.apply_translation([x - (b[0][0] + b[1][0]) / 2, y - (b[0][1] + b[1][1]) / 2, -b[0][2]])
        b = m.bounds
        assert b[0][0] >= 2 and b[0][1] >= 2 and b[1][0] <= 268 and b[1][1] <= 268, (name, b)
        assert m.is_watertight, name
        meshes.append((name, ext, m))
        if paint is not None:
            paints[name] = paint
    return meshes, paints


def flatpak_cli(args, timeout=3600):
    cmd = ["flatpak", "run", APP] + args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env={**os.environ, "HOME": str(REAL_HOME)})
    return r


if __name__ == "__main__":
    pre = WOOD_OUT / "presets"
    pre.mkdir(parents=True, exist_ok=True)
    fil_files = []
    for name, col, temp in FILAMENTS:
        fp = pre / f"{name}.json"
        fp.write_text(json.dumps(filament_preset(name, col, temp), indent=4))
        fil_files.append(fp)
    proc = pre / f"{PROCESS_NAME} - resolved.json"
    proc.write_text(json.dumps(process_preset_full(), indent=4))
    mach = pre / "Snapmaker U1 (0.4 nozzle) - resolved.json"
    mach.write_text(json.dumps(machine_preset(), indent=4))
    print("presets written", flush=True)

    # model-only 3MF with paint
    M3.SETTINGS["mute_plunger"] = {"sparse_infill_density": "100%"}
    meshes, paints = placed_meshes()
    model = WOOD_OUT / "VoiceClock_wood_model.3mf"
    M3.write(model, [("Turned wood - 4x JAYO wood PLA", meshes)], paints=paints)
    print("model 3MF:", model, round(model.stat().st_size / 1e6, 1), "MB", flush=True)

    # install the post-processing script where Orca (in its flatpak sandbox) can run it
    POST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).parent / "wood_temps.py", POST)
    POST.chmod(0o755)

    # install the presets for the GUI (Snapmaker Orca -> user presets)
    for sub in ("filament", "process"):
        (USER_PRESETS / sub).mkdir(parents=True, exist_ok=True)
    for name, col, temp in FILAMENTS:
        (USER_PRESETS / "filament" / f"{name}.json").write_text(json.dumps(filament_user_preset(name, col, temp), indent=4))
    (USER_PRESETS / "process" / f"{PROCESS_NAME}.json").write_text(json.dumps(process_preset(), indent=4))
    print("installed user presets in", USER_PRESETS, flush=True)

    # full project + slice with Snapmaker Orca's own CLI
    proj = WOOD_OUT / "VoiceClock_wood_U1.3mf"
    sliced_dir = WOOD_OUT / "sliced"
    shutil.rmtree(sliced_dir, ignore_errors=True)
    sliced_dir.mkdir()
    common = ["--arrange", "0", "--load-settings", f"{mach};{proc}", "--load-filaments", ";".join(str(f) for f in fil_files)]
    r = flatpak_cli(common + ["--export-3mf", str(proj), str(model)])
    print("export project rc", r.returncode, "->", proj if proj.exists() else "MISSING", flush=True)
    r = flatpak_cli(common + ["--slice", "0", "--outputdir", str(sliced_dir), str(model)])
    res = (sliced_dir / "result.json").read_text() if (sliced_dir / "result.json").exists() else ""
    print("slice rc", r.returncode, res[:400], flush=True)
    g = sliced_dir / "plate_1.gcode"
    assert g.exists(), "slicing failed"
    # the CLI doesn't run post-processing (the GUI does on export/send): run it in the same sandbox
    r = subprocess.run(["flatpak", "run", "--command=python3", APP, str(POST), str(g)], capture_output=True, text=True,
                       env={**os.environ, "HOME": str(REAL_HOME)})
    print("post-process:", r.stdout.strip(), r.stderr.strip()[-500:], flush=True)
    shutil.copy(g, WOOD_OUT / "VoiceClock_wood_U1.gcode")
    print("gcode:", WOOD_OUT / "VoiceClock_wood_U1.gcode", flush=True)
