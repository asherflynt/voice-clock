"""Snapmaker Orca project for the turned-wood Voice Clock (4 x JAYO wood PLA on the U1).

  .venv/bin/python wood.py            # painted, textured meshes -> out/wood/
  .venv/bin/python wood_project.py    # presets + project 3MF + sliced G-code
  .venv/bin/python wood.py walnut && .venv/bin/python wood_project.py walnut   # 3-tone walnut (superseded) -> out/wood_walnut/
  .venv/bin/python wood.py walnut_fs && .venv/bin/python wood_project.py walnut_fs
      # Full Spectrum walnut, 8 tones -> out/wood_walnut_fs/VoiceClock_walnut_fs_008_U1.3mf/.gcode/_model.3mf

Outputs (out/wood/):
  VoiceClock_wood_model.3mf    painted model only (your own presets stay selected)
  VoiceClock_wood_U1.3mf       full project: printer, process, 4 filaments, post-processing
  VoiceClock_wood_U1.gcode     sliced (each head at one fixed temperature; no post-processing)
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
import sys
from wood import STYLE, WOOD_OUT, HEAD_NAMES, FS_ROWS

FS_LAYER = "0.08"   # walnut_fs only: the U1 0.4 nozzle minimum; thin layers hide the Z mixes
TAG = {"cherry": "wood", "walnut": "walnut",
       "walnut_fs": f"walnut_fs_{FS_LAYER.replace('.', '')}"}[STYLE]   # VoiceClock_<TAG>_U1.3mf etc.
APP = "io.github.Snapmaker.Snapmaker_Orca"
REAL_HOME = Path(os.environ.get("VOICE_CLOCK_HOME", str(Path.home())))   # your login home
POST = REAL_HOME / ".local/share/voice-clock/wood_temps.py"
USER_PRESETS = REAL_HOME / ".var/app" / APP / "config/Snapmaker_Orca/user/default"

PRINTER = "Snapmaker U1 (0.4 nozzle)"
PROCESS_BASE = "0.20mm Standard @Snapmaker U1 (0.4 nozzle)"
FILAMENT_BASE = "Snapmaker PLA Wood @U1 0.4 nozzle"

# head -> spool, fixed temperature for the whole print (paint state = head + 1). v2: the unpainted
# core is plain PLA (strong); only the outer skin is wood. No per-layer temperature post-processing.
FILAMENT_BASE_PLAIN = "Snapmaker PLA Basic @U1"
FILAMENTS = [  # (preset name, colour, nozzle C, base preset, max volumetric mm3/s)
    ("PLA core (brown) @U1", "#6B4A35", 215, FILAMENT_BASE_PLAIN, 15),   # T0 structure under the skin
    ("JAYO Wood Cherry @U1", "#8A4A32", 205, FILAMENT_BASE, 8),         # T1 earlywood (cool)
    ("JAYO Wood Cherry HOT @U1", "#6E3A26", 230, FILAMENT_BASE, 2.5),   # T2 latewood: same spool, hotter.
    # 230 C, not the plan's 235-240: untested above JAYO's range, so the first full print stays safe from
    # clogs. Coupon C1 says whether 235-240 is worth it.
    ("JAYO Wood Walnut @U1", "#3E2418", 212, FILAMENT_BASE, 8),         # T3 ring cores, gum streak, mute button
]
if STYLE == "walnut_fs":  # Full Spectrum: maple replaces cherry on head 3; tones are per-layer head sequences
    FILAMENTS = [
        ("PLA core (brown) @U1", "#6B4A35", 215, FILAMENT_BASE_PLAIN, 15),   # T0 structure; one dark mix (41)
        ("JAYO Wood Oak @U1", "#A8804F", 206, FILAMENT_BASE, 8),            # T1
        ("JAYO Wood Maple @U1", "#DCC497", 204, FILAMENT_BASE, 8),          # T2 (only in the lightest mixes)
        ("JAYO Wood Walnut @U1", "#3E2418", 212, FILAMENT_BASE, 8),         # T3, also the mute button
    ]
elif STYLE == "walnut":   # all four spools are on hand; no hot head, so no second spool of anything
    FILAMENTS = [
        ("PLA core (brown) @U1", "#6B4A35", 215, FILAMENT_BASE_PLAIN, 15),   # T0 structure (a darker brown is better)
        ("JAYO Wood Oak @U1", "#A8804F", 206, FILAMENT_BASE, 8),            # T1 golden base
        ("JAYO Wood Cherry @U1", "#8A4A32", 205, FILAMENT_BASE, 8),         # T2 latewood lines
        ("JAYO Wood Walnut @U1", "#3E2418", 212, FILAMENT_BASE, 8),         # T3 heartwood zones, mute button
    ]
PROCESS_NAME = "0.16mm Turned Wood v2 @Snapmaker U1 (0.4 nozzle)"
PROCESS_OVERRIDES = {
    "layer_height": "0.16",
    "initial_layer_print_height": "0.2",
    "wall_loops": "4",
    "sparse_infill_density": "20%",
    "sparse_infill_pattern": "gyroid",
    "enable_support": "0",
    "mmu_segmented_region_max_width": "0.5",       # wood skin = the outer wall only; inner walls are core PLA
    "mmu_segmented_region_interlocking_depth": "0",
    "outer_wall_speed": "40",                      # about 2.7 mm3/s at 0.42 x 0.16: cool and hot heads match
    "inner_wall_speed": "100",
    "gap_infill_speed": "40",
    "seam_position": "back",
    "wipe_tower_x": ["150"],
    "wipe_tower_y": ["158"],
}
if STYLE == "walnut_fs":
    PROCESS_NAME = f"{FS_LAYER}mm Walnut Full Spectrum @Snapmaker U1 (0.4 nozzle)"
    PROCESS_OVERRIDES.update({
        "layer_height": FS_LAYER,
        "initial_layer_print_height": "0.2",       # adhesion; the bed face uses physical heads only
        # one row per mixed tone: a=1,b=2 so pattern digits are head numbers (1 core, 2 oak, 3 maple, 4 walnut);
        # ids 5.. follow the rows in order (Snapmaker Orca 2.4.1 MixedFilament.cpp, tested headless)
        "mixed_filament_definitions": ";".join(f"1,2,1,1,50,0,g,w,m2,z0,xa0,xb0,d0,o0,u{i},{pat}"
                                               for i, pat in enumerate(FS_ROWS, 1)),
        "dithering_local_z_mode": "0",             # Subdivide Mix Layer ignores pattern rows: plain thin layers
    })
# plate layout (bed 270 x 270): shells side by side, back plate + walnut mute button below
LAYOUT = [("front_shell", 1, 67, 69), ("rear_shell", 1, 201, 69), ("back_plate", 1, 67, 205),
          ("mute_plunger", 4, 240, 245)]


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


def filament_preset(name, colour, temp, base=None, maxvol=8):
    base = base or FILAMENT_BASE
    try:
        f = resolve(base)
    except KeyError:
        base = FILAMENT_BASE
        f = resolve(base)
    f.update({"name": name, "from": "User", "inherits": base, "filament_vendor": ["JAYO" if "JAYO" in name else "Generic"],
              "filament_settings_id": [name], "filament_colour": [colour], "default_filament_colour": [colour],
              "nozzle_temperature": [str(temp)], "nozzle_temperature_initial_layer": [str(min(temp + 5, 245))],
              "nozzle_temperature_range_low": ["190"], "nozzle_temperature_range_high": ["245"],
              "filament_max_volumetric_speed": [str(maxvol)],
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


def filament_user_preset(name, colour, temp, base=None, maxvol=8):
    """Same filament as filament_preset(), stored the way the GUI saves user presets."""
    full = filament_preset(name, colour, temp, base, maxvol)
    b = resolve(full["inherits"])
    d = {k: v for k, v in full.items() if b.get(k) != v}
    d.update({"type": "filament", "name": name, "from": "User", "inherits": full["inherits"], "version": "2.4.1.0"})
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
    for name, col, temp, base, maxvol in FILAMENTS:
        fp = pre / f"{name}.json"
        fp.write_text(json.dumps(filament_preset(name, col, temp, base, maxvol), indent=4))
        fil_files.append(fp)
    proc = pre / f"{PROCESS_NAME} - resolved.json"
    proc.write_text(json.dumps(process_preset_full(), indent=4))
    mach = pre / "Snapmaker U1 (0.4 nozzle) - resolved.json"
    mach.write_text(json.dumps(machine_preset(), indent=4))
    print("presets written", flush=True)

    # model-only 3MF with paint
    M3.SETTINGS["mute_plunger"] = {"sparse_infill_density": "100%"}
    meshes, paints = placed_meshes()
    model = WOOD_OUT / f"VoiceClock_{TAG}_model.3mf"
    plate = {"cherry": "Turned wood v2 - PLA core + cherry cool/hot + walnut",
             "walnut": "Turned walnut - PLA core + oak + cherry + walnut",
             "walnut_fs": f"Turned walnut Full Spectrum {FS_LAYER} mm - core + oak + maple + walnut, 8 tones"}[STYLE]
    M3.write(model, [(plate, meshes)], paints=paints)
    print("model 3MF:", model, round(model.stat().st_size / 1e6, 1), "MB", flush=True)

    # v2: no post-processing (each head holds one temperature; wood_temps.py is retired)

    # install the presets for the GUI (Snapmaker Orca -> user presets)
    for sub in ("filament", "process"):
        (USER_PRESETS / sub).mkdir(parents=True, exist_ok=True)
    for name, col, temp, base, maxvol in FILAMENTS:
        (USER_PRESETS / "filament" / f"{name}.json").write_text(json.dumps(filament_user_preset(name, col, temp, base, maxvol), indent=4))
    (USER_PRESETS / "process" / f"{PROCESS_NAME}.json").write_text(json.dumps(process_preset(), indent=4))
    print("installed user presets in", USER_PRESETS, flush=True)

    # full project + slice with Snapmaker Orca's own CLI
    proj = WOOD_OUT / f"VoiceClock_{TAG}_U1.3mf"
    sliced_dir = WOOD_OUT / "sliced"
    shutil.rmtree(sliced_dir, ignore_errors=True)
    sliced_dir.mkdir()
    common = ["--arrange", "0", "--load-settings", f"{mach};{proc}", "--load-filaments", ";".join(str(f) for f in fil_files)]
    r = flatpak_cli(common + ["--export-3mf", str(proj), str(model)])
    print("export project rc", r.returncode, "->", proj if proj.exists() else "MISSING", flush=True)
    r = flatpak_cli(common + ["--slice", "0", "--outputdir", str(sliced_dir), str(model)])
    if r.returncode != 0:
        print("slicer stderr:", r.stderr[-3000:], "\nstdout:", r.stdout[-3000:], flush=True)
    res = (sliced_dir / "result.json").read_text() if (sliced_dir / "result.json").exists() else ""
    print("slice rc", r.returncode, res[:400], flush=True)
    g = sliced_dir / "plate_1.gcode"
    assert g.exists(), "slicing failed"
    shutil.copy(g, WOOD_OUT / f"VoiceClock_{TAG}_U1.gcode")
    print("gcode:", WOOD_OUT / f"VoiceClock_{TAG}_U1.gcode", flush=True)
