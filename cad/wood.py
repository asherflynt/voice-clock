"""Turned-wood exterior for the Voice Clock (alternate to the knit texture), v2.

v2 (6 Nov 2026) follows /tmp/vc_design/WOOD_GRAIN_PLAN.md (research + critique):
  * Tone follows the grain, not the layers: every head holds ONE temperature for the whole print.
    No per-layer temperature drift (wood_temps.py is retired), no dithering, no surface relief.
  * Only the outer skin is wood: the unpainted volume (inner walls, bayonet lugs, collar, ribs,
    bosses) prints in plain PLA on the object's own head, so nothing load-bearing is brittle.
  * Heads (paint state = head + 1):
        T0 CORE  plain PLA (brown)       - object default, never painted
        T1 BASE  JAYO cherry, 205 C       - earlywood
        T2 HOT   JAYO cherry, 230 C       - latewood ramp (the same spool scorched darker; C1 may raise it)
        T3 DARK  JAYO walnut, 212 C       - only the cores of the strongest rings + a gum streak
  * One procedural log through the whole clock in the D frame (front-to-back axis by default, so
    the layers cut across the grain instead of along it), a ring-width table (lognormal widths,
    year-to-year correlation, an age trend, runs of narrow years), an asymmetric 3-level ring
    profile (wide soft side, sharp boundary), broad heartwood streaks, end-grain darkening.

Validate with the test coupons (README) before the full print: the HOT step and the minimum
feature sizes come from them (palette.json, MIN_AREA).

Run:  .venv/bin/python wood.py          -> out/wood/<part>.ply + <part>_paint.npy (print orientation)
      .venv/bin/python wood.py walnut   -> out/wood_walnut/ (the turned-walnut style, below)

WALNUT STYLE (7 Nov 2026, from a photo of a real turned bowl; research in /tmp/walnut_research.txt):
  * Heads: T0 PLA core, T1 JAYO oak 206 C (golden base, ~60 % of the skin), T2 JAYO cherry 205 C
    (latewood lines, one tone darker), T3 JAYO walnut 212 C (heartwood zones, one more tone down).
    No second spool: all four are on hand. Cherry-on-oak is about the photo's streak contrast (17 vs 20 L*).
  * Fine growth rings far from the pith (period 4.4 mm: the photo's ~3 mm x1.5, so every line is at
    least 2 paint samples wide), rippled strongly across the grain and gently along it. Side grain then
    shows fine streaks that fade in and out; end grain shows a rippled labyrinth (coherence ~0.5 vs the
    photo's 0.37). End grain carries more latewood (darker, as in the photo).
  * A broad heartwood field shifts the whole ladder one step (oak -> cherry, cherry -> walnut), so the
    grain stays visible over the dark zone. The log runs ACROSS the face, as a bowl turned from a
    board: side grain on the front, end grain toward the left and right.
"""
import json
import os
import sys
from math import pi
from pathlib import Path

import numpy as np
import trimesh

from voice_clock import (OUT, SPHERE_R, C_Z, UP_D, FOOT_H, BACK_Z, BACK_T, MESH_PRINT_ROT,
                         FRONT_EDGE_Z, RING_BORE_R, BP_PAWLS, BP_PAWL_SLOT, BP_PAWL_LEN,
                         front_shell, rear_shell, back_plate, export_stl)

STYLES = ("cherry", "walnut", "walnut_fs")
STYLE = next((a for a in sys.argv[1:] if a in STYLES), os.environ.get("VC_WOOD", "cherry"))
WOOD_OUT = OUT / {"cherry": "wood", "walnut": "wood_walnut", "walnut_fs": "wood_walnut_fs"}[STYLE]

# ------------------------------------------------------------------ heads
CORE, BASE, HOT, DARK = 0, 1, 2, 3
if STYLE == "walnut":                              # HOT is the middle tone (cherry) in this style
    HEAD_NAMES = {CORE: "PLA core", BASE: "oak 206 C", HOT: "cherry 205 C", DARK: "walnut 212 C"}
    PALETTE = {CORE: "#6B4A35", BASE: "#A8804F", HOT: "#8A4A32", DARK: "#3E2418"}
elif STYLE == "walnut_fs":                         # Full Spectrum: head 3 is maple (no cherry); tones are layer mixes
    HEAD_NAMES = {CORE: "PLA core", BASE: "oak 206 C", HOT: "maple 204 C", DARK: "walnut 212 C"}
    PALETTE = {CORE: "#6B4A35", BASE: "#A8804F", HOT: "#DCC497", DARK: "#3E2418"}
else:
    HEAD_NAMES = {CORE: "PLA core", BASE: "cherry 205 C", HOT: "cherry 230 C", DARK: "walnut"}
    PALETTE = {CORE: "#6B4A35", BASE: "#8A4A32", HOT: "#6E3A26", DARK: "#3E2418"}   # until C1 measures them
_pal = WOOD_OUT / "palette.json"
if _pal.exists():                                  # written from coupon C1
    PALETTE.update({int(k): v for k, v in json.loads(_pal.read_text()).items()})

# ------------------------------------------------------------------ the log
LOG = "front_back"        # "front_back" (recommended) or "across" (v1's story: axis across the face)


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def _rot(axis, deg):
    a = np.radians(deg)
    x, y, z = _unit(axis)
    c, s, C = np.cos(a), np.sin(a), 1 - np.cos(a)
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


if LOG == "front_back":   # axis along device z, yawed 15 and pitched 10; pith 74 mm below, 12 to one side
    AXIS = _rot([0, 1, 0], 15.0) @ _rot([1, 0, 0], 10.0) @ np.array([0, 0, 1.0])
    PITH = np.array([12.0, -74.0, C_Z])
else:                     # axis across the face, pith 90 mm behind and above the far side
    AXIS = _unit([1.0, 0.0, 0.0])
    PITH = np.array([0.0, 45.0, C_Z - 78.0])
E1 = _unit(np.cross(AXIS, [0, 0, 1.0]) if abs(AXIS[2]) < 0.9 else np.cross(AXIS, [1.0, 0, 0]))
E2 = np.cross(AXIS, E1)

# growth field (Liu 2016 / Larsson 2022 structure)
TAPER = 0.012             # rings widen toward the butt
ECC, ECC_ANG = 0.06, 0.7  # eccentric pith
DIST = [(1.8, 45.0, 180.0)]   # (amplitude mm, wavelength across, wavelength along); 3 more octaves
for _ in range(3):
    a, lx, la = DIST[-1]
    DIST.append((a / 2, lx / 2, la / 2))
# ring table
N_RINGS, RING_MEAN, RING_CV, RING_RHO = 60, 3.4, 0.35, 0.5
RING_TREND = (4.2, 2.8)   # pith -> bark
SEED = 11
CORE_MIN_MM = 0.9         # walnut cores at least 2 lines wide (radially; the surface cut widens them)
MIN_AREA = 1.0            # mm2: smaller paint islands merge into their surroundings (C2 tunes this)
STEP = 0.45               # paint sampling of the surface (about one line width)

# ------------------------------------------------------------------ noise
_rng = np.random.default_rng(SEED)
_PERM = np.concatenate([_rng.permutation(256)] * 2)
_GRAD = np.array([[1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0], [1, 0, 1], [-1, 0, 1], [1, 0, -1],
                  [-1, 0, -1], [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1]], float)


def perlin(p):
    """Vectorised 3D gradient noise, roughly -1..1. p: (N, 3)."""
    p = np.asarray(p, float)
    pi_ = np.floor(p).astype(np.int64)
    f = p - pi_
    pi_ &= 255
    u = f * f * f * (f * (f * 6 - 15) + 10)
    res = np.zeros(len(p))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                h = _PERM[_PERM[_PERM[pi_[:, 0] + dx] + pi_[:, 1] + dy] + pi_[:, 2] + dz] % 12
                d = f - np.array([dx, dy, dz])
                w = (u[:, 0] if dx else 1 - u[:, 0]) * (u[:, 1] if dy else 1 - u[:, 1]) * (u[:, 2] if dz else 1 - u[:, 2])
                res += w * (_GRAD[h] * d).sum(1)
    return res * 1.4


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ring_table():
    """Ring outer radii and per-ring strength / latewood share / dark-core share."""
    rng = np.random.default_rng(SEED + 7)
    sigma = np.sqrt(np.log(1 + RING_CV ** 2))
    z = np.zeros(N_RINGS)
    for k in range(N_RINGS):                       # AR(1): neighbouring years are alike
        z[k] = RING_RHO * (z[k - 1] if k else 0.0) + np.sqrt(1 - RING_RHO ** 2) * rng.standard_normal()
    w = np.exp(np.log(RING_MEAN) - sigma ** 2 / 2 + sigma * z)
    w *= np.linspace(*RING_TREND, N_RINGS) / RING_MEAN
    for start in rng.choice(np.arange(8, N_RINGS - 6), 2, replace=False):     # two runs of lean years
        w[start:start + rng.integers(3, 6)] *= 0.5
    edges = np.concatenate([[0.0], np.cumsum(w)])
    s = np.clip(0.3 + 0.7 * rng.random(N_RINGS) ** 0.8, 0.3, 1.0)
    lw = 0.10 + 0.20 * s + 0.02 * rng.standard_normal(N_RINGS)
    u = rng.random(N_RINGS)
    lw = np.where(u < 0.08, 0.0, np.where(u < 0.28, lw * 0.5, lw))         # no latewood / weak rings
    lw = np.clip(lw, 0, 0.32)
    strong = (s >= np.quantile(s, 0.87)) & (u >= 0.28) & (lw * w >= 1.3)
    core = np.where(strong, np.minimum(np.maximum(0.3 * lw, CORE_MIN_MM / w), 0.8 * lw), 0.0)
    return edges, w, lw, core


EDGES, WIDTHS, LW, CORE_SHARE = ring_table()


def log_coords(p):
    d = p - PITH
    along = d @ AXIS
    x1, x2 = d @ E1, d @ E2
    r = np.hypot(x1, x2)
    th = np.arctan2(x2, x1)
    r = r * (1 + ECC * np.cos(th - ECC_ANG)) - TAPER * along
    for k, (amp, lx, la) in enumerate(DIST):
        r = r + amp * perlin(np.stack([along / la, x1 / lx, x2 / lx], 1) + 3.7 * k + 0.31)
    return along, r, th, x1, x2


# ------------------------------------------------------------------ walnut style
WN_AXIS = _rot([1, 0, 0], 8.0) @ _rot([0, 1, 0], 12.0) @ np.array([1.0, 0.0, 0.0])   # across the face
WN_PITH = np.array([0.0, 0.0, C_Z]) + 170.0 * _unit([0.0, 60.0, 70.0])              # far: rings nearly parallel
WN = dict(PERIOD=4.4, PERIOD_CV=0.18,
          RIP=[(3.2, 8.5, 140.0), (1.7, 4.2, 60.0), (0.7, 2.1, 26.0)],   # ripple: amplitude, across, along (mm)
          LW=0.32, LW_END=0.16,                     # latewood share; extra on end grain
          FADE_A=9.0, FADE_C=4.0, FADE_W=0.35,      # side-grain streaks fade in and out along the grain
          BRK=3.4, BRK_W=0.30,                      # end-grain ripples break into short worms
          MIN_LINE=0.9,                             # mm: latewood lines are at least 2 paint samples wide or absent
          CA=95.0, CC=40.0, T_PATCH=0.38, T_PATCH2=0.62, PATCH_GRAIN=0.45)   # heartwood: lines darken, then base
# 3-tone style shares on a test sphere: about oak 64 %, cherry 23 %, walnut 13 %
_wn_e1 = _unit(np.cross(WN_AXIS, [0, 0, 1.0]))
_wn_e2 = np.cross(WN_AXIS, _wn_e1)


def _walnut_fields(p, n=None, P=WN):
    """Shared geometry of the walnut styles: ring phase f, latewood share lw (0 = no line), end-grain
    weight, fade, heartwood field C, log coordinates."""
    p = np.asarray(p, float)
    d = p - WN_PITH
    a, x1, x2 = d @ WN_AXIS, d @ _wn_e1, d @ _wn_e2
    rr = np.hypot(x1, x2)
    for k, (amp, lc, la) in enumerate(P["RIP"]):
        rr = rr + amp * perlin(np.stack([a / la, x1 / lc, x2 / lc], 1) + 7.1 * k)
    ph = rr / P["PERIOD"] + P["PERIOD_CV"] * 2.0 * perlin(np.stack([rr / 40.0, a / 400.0, a * 0 + 0.37], 1) + 3.3)
    f = ph - np.floor(ph)
    end = smoothstep(0.5, 0.95, np.abs(np.asarray(n) @ WN_AXIS)) if n is not None else 0 * a
    fade = perlin(np.stack([a / P["FADE_A"], x1 / P["FADE_C"], x2 / P["FADE_C"]], 1) + 11.0)
    brk = perlin(np.stack([x1, x2, a], 1) / P["BRK"] + 17.0)
    lw = P["LW"] + P["LW_END"] * end + P["FADE_W"] * 0.5 * fade * (1 - 0.5 * end) + P["BRK_W"] * end * brk
    lw = np.where(lw * P["PERIOD"] < P["MIN_LINE"], 0.0, np.clip(lw, 0, 0.7))
    C = 0.75 * perlin(np.stack([a / P["CA"], x1 / P["CC"], x2 / P["CC"]], 1) + 21.0) + \
        0.25 * perlin(np.stack([a / (P["CA"] / 2.5), x1 / (P["CC"] / 2.5), x2 / (P["CC"] / 2.5)], 1) + 33.0)
    return dict(f=f, lw=lw, end=end, fade=fade, C=C, a=a, x1=x1, x2=x2, ph=ph)


# Full Spectrum walnut (7 Nov 2026): 8 tones, each a physical head or an exact per-layer head sequence
# (Snapmaker Orca 2.4.1 'mixed_filament_definitions' pattern rows; digits = heads 1 core, 2 oak, 3 maple,
# 4 walnut). Cycles are at most 3 layers: 0.24 mm at 0.08 mm layers. L* by
# linear-light averaging of the preset colours (to be measured on the swatch).
FS_TONES = [  # (paint state, layer sequence, L*)
    (4, "4", 17.2), (5, "41", 27.6), (6, "442", 37.3), (7, "42", 43.3),
    (8, "422", 48.3), (2, "2", 56.4), (9, "223", 65.9), (10, "23", 69.9)]
FS_ROWS = ["41", "442", "42", "422", "223", "23"]      # mixed filament ids 5..10, in this order
FS_BED = (4, 1, 2)                                     # on bed faces only physical heads (no Z mix in one layer)
FS = dict(BASE_L=60.0, BASE_VAR=4.0, EARLY_L=5.0, EARLY_F=0.22, LINE_D=17.0, END_D=6.0,
          H0=-0.05, H1=0.55, HEART_D=36.0, DITHER=2.6)
# tone percentiles on a test sphere, L* p10/25/50/75/90: 17/37/48/56/66 (photo 18/35/51/59/65)


def walnut_fs_lightness(p, n=None, P=WN, F=FS):
    """Target L* per point: golden earlywood (lighter at the ring start), latewood lines whose depth fades
    along the grain, darker end grain, soft heartwood zones, a little dither against contouring."""
    w = _walnut_fields(p, n, P)
    a, x1, x2 = w["a"], w["x1"], w["x2"]
    L = F["BASE_L"] + F["BASE_VAR"] * perlin(np.stack([a / 60.0, x1 / 22.0, x2 / 22.0], 1) + 41.0)
    L = L - F["END_D"] * w["end"]
    line = w["f"] > 1 - w["lw"]
    early = (w["f"] < F["EARLY_F"]) & (w["lw"] > 0)
    depth = np.clip(0.62 + 0.45 * w["fade"], 0.35, 1.0)
    L = L - F["LINE_D"] * depth * line + F["EARLY_L"] * early
    H = smoothstep(F["H0"], F["H1"], w["C"] + 0.12 * (line - 0.5))
    L = L - F["HEART_D"] * H
    q = np.asarray(p, float)
    L = L + F["DITHER"] * perlin(q / 1.3 + 57.0)
    return L, w


def walnut_fs(p, n=None):
    L, w = walnut_fs_lightness(p, n)
    Ls = np.array([t[2] for t in FS_TONES])
    st = np.array([t[0] for t in FS_TONES])
    k = np.abs(L[:, None] - Ls[None, :]).argmin(1)
    return dict(state=st[k], L=L, ring=np.floor(w["ph"]).astype(int))


def walnut(p, n=None, P=WN):
    """Walnut-style head per point: BASE (oak), HOT (cherry, latewood) or DARK (walnut, heartwood)."""
    p = np.asarray(p, float)
    d = p - WN_PITH
    a, x1, x2 = d @ WN_AXIS, d @ _wn_e1, d @ _wn_e2
    rr = np.hypot(x1, x2)
    for k, (amp, lc, la) in enumerate(P["RIP"]):    # smooth 3D coordinates only (no angle: no seam)
        rr = rr + amp * perlin(np.stack([a / la, x1 / lc, x2 / lc], 1) + 7.1 * k)
    ph = rr / P["PERIOD"] + P["PERIOD_CV"] * 2.0 * perlin(np.stack([rr / 40.0, a / 400.0, a * 0 + 0.37], 1) + 3.3)
    f = ph - np.floor(ph)
    end = smoothstep(0.5, 0.95, np.abs(np.asarray(n) @ WN_AXIS)) if n is not None else 0 * a
    fade = perlin(np.stack([a / P["FADE_A"], x1 / P["FADE_C"], x2 / P["FADE_C"]], 1) + 11.0)
    brk = perlin(np.stack([x1, x2, a], 1) / P["BRK"] + 17.0)
    lw = P["LW"] + P["LW_END"] * end + P["FADE_W"] * 0.5 * fade * (1 - 0.5 * end) + P["BRK_W"] * end * brk
    lw = np.where(lw * P["PERIOD"] < P["MIN_LINE"], 0.0, lw)   # a fading line stops; it never thins to a wisp
    late = f > 1 - np.clip(lw, 0, 0.7)
    C = 0.75 * perlin(np.stack([a / P["CA"], x1 / P["CC"], x2 / P["CC"]], 1) + 21.0) + \
        0.25 * perlin(np.stack([a / (P["CA"] / 2.5), x1 / (P["CC"] / 2.5), x2 / (P["CC"] / 2.5)], 1) + 33.0)
    zone = C + P["PATCH_GRAIN"] * (late - 0.5)
    outer = zone > P["T_PATCH"]                     # heartwood, step 1: the latewood lines go one tone darker
    inner = zone > P["T_PATCH2"]                    # step 2 (deeper in): the earlywood darkens too
    tool = np.clip(BASE + late.astype(int) + (outer & late).astype(int) + inner.astype(int), BASE, DARK)
    return dict(tool=tool, ring=np.floor(ph).astype(int), frac=f)


def wood(p, n=None):
    """Head per point (N, 3) in the D frame; n = surface normals (for end-grain darkening)."""
    if STYLE == "walnut":
        return walnut(p, n)
    p = np.asarray(p, float)
    along, r, th, x1, x2 = log_coords(p)
    k = np.clip(np.searchsorted(EDGES, r) - 1, 0, N_RINGS - 1)
    f = np.clip((r - EDGES[k]) / WIDTHS[k], 0, 1)
    lw = LW[k].copy()
    if n is not None:                              # end grain reads darker (about 3 L*)
        lw = lw + 0.05 * smoothstep(0.6, 0.95, np.abs(np.asarray(n) @ AXIS)) * (lw > 0)
    tool = np.where(f < 1 - lw, BASE, np.where(f < 1 - CORE_SHARE[k], HOT, DARK))
    # 2-3 broad heartwood streaks (20-40 mm), drawn in the hot tone over earlywood
    streak = perlin(np.stack([along / 90.0, x1 / 28.0, x2 / 28.0], 1) + 5.1)
    tool = np.where((tool == BASE) & (streak > 0.62), HOT, tool)
    # one gum streak along the fibre, kept 15 mm away from the light ring
    gum = (np.abs(r - 58.0) < 0.6 + 0.35 * perlin(np.stack([along / 6.0, th * 9, x1 * 0], 1))) & \
          (np.abs(along - 8.0) < 9.0 + 3.0 * perlin(np.stack([th * 4, r * 0.2, x2 * 0], 1))) & \
          (np.abs(((th - 2.2) + pi) % (2 * pi) - pi) < 0.05)
    ring_dist = np.hypot(np.hypot(p[:, 0], p[:, 1]) - RING_BORE_R, p[:, 2] - FRONT_EDGE_Z)
    tool = np.where(gum & (ring_dist > 15.0), DARK, tool)
    return dict(tool=tool, ring=k, frac=f)


# ------------------------------------------------------------------ surfaces
def exterior_mask(m):
    """Triangles on the outside of the clock (sphere, base flat, back face)."""
    c = m.triangles_center
    n = m.face_normals
    up = np.array([UP_D.X, UP_D.Y, UP_D.Z])
    rc = c - [0, 0, C_Z]
    rr = np.linalg.norm(rc, axis=1)
    sph = (rr > SPHERE_R - 0.5) & ((n * rc).sum(1) / np.maximum(rr, 1e-9) > 0.3)
    base = (c @ up < FOOT_H + 0.5) & (n @ up < -0.7)
    back = (c[:, 2] < BACK_Z - BACK_T + 0.5) & (n[:, 2] < -0.7)
    rxy = np.hypot(c[:, 0], c[:, 1])
    ang = np.degrees(np.arctan2(c[:, 1], c[:, 0])) % 360
    pawl = np.zeros(len(c), bool)
    for t in BP_PAWLS:                                  # the flexing pawl arms stay plain PLA
        pawl |= (rxy > BP_PAWL_SLOT[0] - 0.4) & (rxy < BP_PAWL_SLOT[1] + 1.2) & \
                (((ang - t) % 360 < BP_PAWL_LEN + 0.6) | ((t - ang) % 360 < 2.6))
    back &= ~pawl
    return sph | base | back, back


def refine(m, step=STEP):
    """Subdivide so the paint has ~STEP resolution on the exterior."""
    while True:
        e = m.edges_unique_length
        if e.max() <= step * 1.6:
            return m
        v, f = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=step * 1.5, max_iter=12)
        return trimesh.Trimesh(v, f, process=True)


def despeckle(m, paint, ext, min_area=MIN_AREA, bed=None):
    """Merge painted islands smaller than min_area into the head that surrounds them. On bed faces
    the threshold is 3x and walnut is not used (the first layers can't hold fine detail)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    paint = paint.copy()
    if bed is not None and STYLE == "walnut_fs":       # one layer can't show a Z mix: nearest physical head
        Lst = {t[0]: t[2] for t in FS_TONES}
        Lst.update({1: 34.6, 2: 56.4, 3: 80.1, 4: 17.2})
        phys = np.array(FS_BED)
        for s_ in np.unique(paint[bed]):
            if s_ > 0 and s_ not in FS_BED:
                paint[bed & (paint == s_)] = phys[np.abs(np.array([Lst[q] for q in phys]) - Lst[s_]).argmin()]
    elif bed is not None:
        paint[bed & (paint == DARK + 1)] = HOT + 1
    adj = m.face_adjacency
    area = m.area_faces
    for _ in range(3):
        same = paint[adj[:, 0]] == paint[adj[:, 1]]
        a = adj[same]
        g = coo_matrix((np.ones(len(a)), (a[:, 0], a[:, 1])), shape=(len(paint), len(paint)))
        ncomp, lab = connected_components(g, directed=False)
        comp_area = np.bincount(lab, weights=area, minlength=ncomp)
        thr = np.where(bed if bed is not None else False, min_area * 3, min_area)
        small = ext & (comp_area[lab] < thr) & (paint > 0)
        if not small.any():
            break
        # neighbour vote: the most common other head across each small island's border
        diff = adj[~same]
        for i, j in ((diff[:, 0], diff[:, 1]), (diff[:, 1], diff[:, 0])):
            sel = small[i] & (paint[j] > 0)
            paint[i[sel]] = paint[j[sel]]
    return paint


def woodify(name, shape):
    raw = WOOD_OUT / f"_{name}_raw.stl"
    export_stl(shape, str(raw), tolerance=0.02, angular_tolerance=0.1)
    m = trimesh.load(raw)
    raw.unlink()
    import texture
    if name == "back_plate" and STYLE == "walnut_fs":   # walnut only: one-layer knit patch in the bed face
        m = texture.bed_texture(m)
    m = texture.clean(m)                           # before refining: clean() collapses flat sub-0.01 mm detail
    m = refine(m)
    assert m.is_watertight, name
    ext, bed = exterior_mask(m)
    if STYLE == "walnut_fs":                       # paint state = head (1-4) or mixed filament id (5..)
        paint = np.where(ext, walnut_fs(m.triangles_center, m.face_normals)["state"], 0).astype(np.int8)
    else:
        tools = wood(m.triangles_center, m.face_normals)["tool"]
        paint = np.where(ext, tools + 1, 0).astype(np.int8)    # state = head + 1, 0 = object default (core)
    paint = despeckle(m, paint, ext, bed=bed)
    return m, paint


def to_print(name, m):
    m = m.copy()
    m.apply_transform(MESH_PRINT_ROT.get(name, np.eye(4)))
    b = m.bounds
    m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
    return m


PARTS = {"front_shell": front_shell, "rear_shell": rear_shell, "back_plate": back_plate}

if __name__ == "__main__":
    import time
    WOOD_OUT.mkdir(parents=True, exist_ok=True)
    if STYLE.startswith("walnut"):
        print(f"style {STYLE}: axis {np.round(WN_AXIS, 3)}, pith {np.round(WN_PITH, 1)}, ring period {WN['PERIOD']} mm", flush=True)
    else:
        print(f"log: {LOG}, axis {np.round(AXIS, 3)}, pith {np.round(PITH, 1)}; rings mean {WIDTHS.mean():.2f} mm, "
              f"{(LW == 0).mean() * 100:.0f} % without latewood, {(CORE_SHARE > 0).mean() * 100:.0f} % with a walnut core", flush=True)
    for name, fn in PARTS.items():
        t = time.time()
        m, paint = woodify(name, fn())
        m.export(WOOD_OUT / f"{name}_D.ply")
        np.save(WOOD_OUT / f"{name}_paint.npy", paint)
        p = to_print(name, m)
        p.export(WOOD_OUT / f"{name}.ply")
        share = np.bincount(paint, weights=m.area_faces, minlength=18) / m.area_faces[paint > 0].sum()
        if STYLE == "walnut_fs":
            tones = " ".join(f"L{L:.0f}:{share[s_] * 100:.0f}" for s_, _, L in FS_TONES)
            print(f"{name}: {len(m.faces)} faces, watertight {m.is_watertight}, skin by tone (L* : %) {tones}, "
                  f"{time.time() - t:.0f}s", flush=True)
        else:
            print(f"{name}: {len(m.faces)} faces, watertight {m.is_watertight}, vol {m.volume / 1000:.1f} cm3, "
                  f"skin area by head ({'/'.join(HEAD_NAMES[k] for k in (BASE, HOT, DARK))}) "
                  f"{'/'.join(f'{s * 100:.0f}' for s in share[2:5])} %, {time.time() - t:.0f}s", flush=True)
