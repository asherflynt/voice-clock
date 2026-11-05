#!/usr/bin/env python3
"""Wood PLA tone drift for the Snapmaker U1 (Orca post-processing script).

Wood-filled PLA prints darker when it is hotter. This script lets each toolhead's nozzle
temperature wander slowly and smoothly with print height, inside safe limits, so each wood
tone shades gently lighter and darker the way a real board does. It does not make stripes:
the change is at most RATE degC per layer over a 14-30 mm wavelength.

What it does to the G-code (Orca passes the file path as the first argument):
  * from layer 2 on, every M104/M109 that sets a tool to its *printing* temperature (the
    slicer's preheat before a tool change, and the tool change itself) is rewritten to that
    tool's drifted target for the current layer;
  * standby / cool-down commands are left exactly as the slicer wrote them. With the U1's
    ooze prevention, idle heads drop to about 60 C, so wood never sits hot and chars;
  * at every layer change it nudges the active tool to the new target (no waiting);
  * the first layer is left alone (adhesion), and the file is only processed once.

Base temperatures come from the slicer's nozzle_temperature for each filament.
Tunables (environment variables or the defaults below): WOOD_AMP, WOOD_RATE, WOOD_MIN, WOOD_MAX.
"""
import math
import os
import re
import sys

AMP = float(os.environ.get("WOOD_AMP", 9))        # +- degC around each filament's base
RATE = float(os.environ.get("WOOD_RATE", 1.0))    # max degC change per layer
TMIN = float(os.environ.get("WOOD_MIN", 190))     # JAYO wood PLA window
TMAX = float(os.environ.get("WOOD_MAX", 228))
WAVE = (17.0, 23.0, 29.0, 14.0)                   # mm, per tool (different so tones don't move together)
MARK = "; WOOD_TEMPS applied"

TEMP_RE = re.compile(r"^(M10[49])\b(.*)$")
S_RE = re.compile(r"\bS(-?\d+(?:\.\d+)?)")
T_RE = re.compile(r"\bT(\d+)")
TOOL_RE = re.compile(r"^T(\d+)\s*(;.*)?$")


def smooth_noise(x, seed):
    """1D value noise, cosine-interpolated, two octaves, about -1..1."""
    def v(i):
        n = (i * 374761393 + seed * 668265263) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 32767.5 - 1.0

    def octave(x):
        i = math.floor(x)
        f = x - i
        w = (1 - math.cos(f * math.pi)) / 2
        return v(i) * (1 - w) + v(i + 1) * w
    return (octave(x) + 0.45 * octave(x * 2.3 + 11.7)) / 1.45


def read_config(lines):
    cfg = {}
    for ln in lines[-4000:]:
        if ln.startswith("; ") and " = " in ln:
            k, _, val = ln[2:].partition(" = ")
            cfg[k.strip()] = val.strip()
    return cfg


def main(path):
    with open(path, encoding="utf-8", errors="surrogateescape") as f:
        lines = f.read().split("\n")
    if any(ln.startswith(MARK) for ln in lines[:400]):
        print("wood_temps: already applied, skipping")
        return
    # pass 1: layer heights, tools used, and each tool's printing temperature. The base
    # temperature is read from the commands themselves (the most common S above 150 C after
    # the first layer): Orca's config footer lists only one value for some per-filament keys.
    layer_z, used = [], set()
    z_pending, tool, layer = False, None, -1
    counts = {}
    for ln in lines:
        if ln.startswith(";LAYER_CHANGE"):
            z_pending = True
        elif z_pending and ln.startswith(";Z:"):
            layer_z.append(float(ln[3:]))
            z_pending = False
            layer += 1
        m = TOOL_RE.match(ln)
        if m:
            tool = int(m.group(1))
            used.add(tool)
        mt = TEMP_RE.match(ln)
        if mt and layer >= 1:
            body = ln.split(";", 1)[0]
            ms, mtool = S_RE.search(body), T_RE.search(body)
            t = int(mtool.group(1)) if mtool else tool
            if ms and t is not None and float(ms.group(1)) > 150:
                c = counts.setdefault(t, {})
                c[float(ms.group(1))] = c.get(float(ms.group(1)), 0) + 1
    if not layer_z:
        print("wood_temps: no ;LAYER_CHANGE markers found, nothing to do")
        return
    cfg = read_config(lines)
    fallback = float(cfg.get("nozzle_temperature", "210").split(",")[0])
    n_tools = max(used | set(counts) | {0}) + 1
    base = [max(counts[t], key=counts[t].get) if t in counts else fallback for t in range(n_tools)]
    first = base

    # schedule: target[t][layer], rate limited, layer 0 = first-layer temperature
    target = []
    for t in range(n_tools):
        seq, prev = [], None
        for li, z in enumerate(layer_z):
            if li == 0:
                val = first[t]
            else:
                want = base[t] + AMP * smooth_noise(z / WAVE[t % len(WAVE)], 17 + 31 * t)
                want = min(max(want, TMIN), TMAX)
                val = want if prev is None else max(prev - RATE, min(prev + RATE, want))
            seq.append(val)
            prev = val
        target.append([int(round(v)) for v in seq])

    # pass 2: rewrite
    out = [MARK + f" (amp +-{AMP:g} C, <= {RATE:g} C/layer, window {TMIN:g}-{TMAX:g} C)"]
    layer, tool, z_pending, rewritten, inserted = -1, None, False, 0, 0
    for ln in lines:
        m = TOOL_RE.match(ln)
        if m:
            tool = int(m.group(1))
        if ln.startswith(";LAYER_CHANGE"):
            z_pending = True
            out.append(ln)
            continue
        if z_pending and ln.startswith(";Z:"):
            z_pending = False
            layer += 1
            out.append(ln)
            if layer >= 1 and tool is not None and tool < n_tools:
                out.append(f"M104 S{target[tool][layer]} T{tool} ; wood tone")
                inserted += 1
            continue
        mt = TEMP_RE.match(ln)
        if mt and layer >= 1:
            body = ln.split(";", 1)[0]
            ms = S_RE.search(body)
            mtool = T_RE.search(body)
            t = int(mtool.group(1)) if mtool else tool
            if ms and t is not None and t < n_tools:
                s_old = float(ms.group(1))
                offset = s_old - base[t]
                if s_old > 0 and abs(offset) <= 12:    # a printing temperature (not standby/off)
                    s_new = int(round(target[t][min(layer, len(layer_z) - 1)] + offset))
                    body = body[:ms.start()] + f"S{s_new}" + body[ms.end():]
                    ln = body.rstrip() + " ; wood tone (was S" + ms.group(1) + ")"
                    rewritten += 1
        out.append(ln)

    # summary graph
    out.append("; WOOD_TEMPS per-layer targets (every 10th layer): z, " + ", ".join(f"T{t}" for t in sorted(used)))
    for li in range(0, len(layer_z), 10):
        out.append(f";   {layer_z[li]:6.2f}  " + "  ".join(f"{target[t][li]:3d}" for t in sorted(used) if t < n_tools))
    tmp = path + ".woodtmp"
    with open(tmp, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write("\n".join(out))
    os.replace(tmp, path)
    rng = {t: (min(target[t][1:] or [0]), max(target[t][1:] or [0])) for t in sorted(used) if t < n_tools}
    print(f"wood_temps: {len(layer_z)} layers, tools {sorted(used)}, {rewritten} temps rewritten, "
          f"{inserted} inserted, ranges {rng}")


if __name__ == "__main__":
    main(sys.argv[1])
