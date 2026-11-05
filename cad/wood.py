"""Turned-wood exterior for the Voice Clock (alternate to the knit texture).

One procedural log runs through the whole clock in the D frame, so the grain is continuous
across the front shell, rear shell and back plate, as if the sphere was turned from a single
half-log blank (log axis across the face, pith below the clock, sapwood cap on top).

Every exterior surface (sphere, flat base, back face, face rim) gets:
  * a subtle relief: open earlywood pores sit 0.12 mm low, plus fibre streaks along the grain;
  * a 4-tool colour paint (Orca "paint_color"), one JAYO wood PLA per U1 head:
        T0 cherry  - heartwood earlywood (also the unpainted structure inside)
        T1 walnut  - heartwood latewood rings
        T2 maple   - sapwood earlywood
        T3 oak     - sapwood latewood rings ("logs" spool)

Run:  .venv/bin/python wood.py    -> out/wood/<part>.ply + <part>_paint.npy (print orientation)
"""
from math import pi
from pathlib import Path

import numpy as np
import trimesh

from voice_clock import (OUT, SPHERE_R, C_Z, UP_D, FOOT_H, FACE_Z, BACK_Z, BACK_T, MESH_PRINT_ROT,
                         front_shell, rear_shell, back_plate, export_stl)

WOOD_OUT = OUT / "wood"

# ------------------------------------------------------------------ the log
PITH = np.array([0.0, -66.0, C_Z - 8.0])          # pith line passes just below the base (half-log blank)
AXIS = np.array([1.0, 0.12, 0.38])
AXIS = AXIS / np.linalg.norm(AXIS)                # across the face, slightly skewed (more figure)
RING = 3.6                                        # mean ring spacing, mm
LATE_MIN, LATE_MAX = 0.14, 0.22                   # latewood share of a ring (0.14 * 3.6 = 0.5 mm, >= one line)
FAINT = -0.45                                     # rings whose strength is below this show no dark line
SAPWOOD = False                                   # v1 had a maple/oak sapwood cap; off = all heartwood
HEART_R = 106.0                                   # heartwood / sapwood boundary (only if SAPWOOD)
DEPTH_EARLY = 0.12                                # earlywood pore recess, mm
DEPTH_FIBRE = 0.05                                # fibre streaks, mm
STEP = 0.30                                       # surface sampling (also the paint resolution)

# tools (paint state = tool + 1)
CHERRY, WALNUT, MAPLE, OAK = 0, 1, 2, 3
DEFAULT_TOOL = CHERRY


# ------------------------------------------------------------------ noise
_rng = np.random.default_rng(11)
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
    out = 0.0
    res = np.zeros(len(p))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                h = _PERM[_PERM[_PERM[pi_[:, 0] + dx] + pi_[:, 1] + dy] + pi_[:, 2] + dz] % 12
                g = _GRAD[h]
                d = f - np.array([dx, dy, dz])
                dot = (g * d).sum(1)
                w = (u[:, 0] if dx else 1 - u[:, 0]) * (u[:, 1] if dy else 1 - u[:, 1]) * (u[:, 2] if dz else 1 - u[:, 2])
                res += w * dot
    return res * 1.4


def fbm(p, octaves=3):
    s, a, tot = 1.0, 1.0, 0.0
    for _ in range(octaves):
        tot = tot + a * perlin(p * s)
        s *= 2.03
        a *= 0.5
    return tot


def _log_frame(p):
    """Return (along-axis coordinate, distance from the pith line, across-grain vector)."""
    d = p - PITH
    along = d @ AXIS
    radial = d - np.outer(along, AXIS)
    return along, np.linalg.norm(radial, axis=1)


def wood(p):
    """Wood field at D-frame points p (N, 3).
    Returns dict: tool (int), relief (mm, >= 0, inward), phase, heart (bool)."""
    p = np.asarray(p, float)
    along, r = _log_frame(p)
    # stretch the noise along the grain: long gentle waves along the axis, tighter across it
    q = np.stack([along * 0.012, r * 0.035, (p @ np.cross(AXIS, [0, 0, 1.0])) * 0.03], 1)
    r_eff = r + 2.6 * fbm(q, 3) + 0.45 * perlin(np.stack([along * 0.05, r * 0.4, p[:, 2] * 0.2], 1) + 7.3)
    # uneven ring widths (wet and dry years)
    phase = r_eff / RING + 1.1 * perlin(np.stack([r_eff / 38.0, np.full(len(p), 0.5), np.full(len(p), 2.5)], 1))
    frac = phase - np.floor(phase)
    # each year is different: ring strength sets how thick its dark latewood line is, and the
    # faintest years show no dark line at all (only the pore texture), like real cherry
    year = np.floor(phase)
    strength = perlin(np.stack([year * 0.61 + 0.3, along * 0.004, np.full(len(p), 5.3)], 1))
    late_share = LATE_MIN + (LATE_MAX - LATE_MIN) * np.clip((strength - FAINT) / (0.6 - FAINT), 0, 1)
    late = (frac > 1.0 - late_share) & (strength > FAINT)
    heart = (r_eff < HEART_R + 4.0 * perlin(np.stack([along * 0.02, p[:, 2] * 0.02, np.full(len(p), 4.2)], 1))) \
        if SAPWOOD else np.ones(len(p), bool)
    tool = np.where(heart, np.where(late, WALNUT, CHERRY), np.where(late, OAK, MAPLE))
    # relief: earlywood pores recessed (smooth ramp into the latewood), fibre streaks along the grain
    early_w = np.where(late, 0.0, np.clip((1.0 - late_share - frac) / 0.05, 0, 1))
    fibre = np.abs(perlin(np.stack([along * 0.10, r * 2.2, p[:, 2] * 2.2 + p[:, 0] * 0.3], 1) + 3.1))
    relief = DEPTH_EARLY * early_w * (0.65 + 0.35 * np.clip(perlin(p * 0.9 + 1.7) + 0.5, 0, 1)) \
        + DEPTH_FIBRE * np.clip(fibre * 1.6, 0, 1)
    return dict(tool=tool, relief=relief, phase=phase, heart=heart, late=late)


# ------------------------------------------------------------------ cutters (closed meshes)
def _grid_surface(u_rng, v_rng, step):
    us = np.arange(u_rng[0], u_rng[1] + 1e-9, step)
    vs = np.arange(v_rng[0], v_rng[1] + 1e-9, step)
    U, V = np.meshgrid(us, vs, indexing="ij")
    nu, nv = U.shape
    idx = np.arange(nu * nv).reshape(nu, nv)
    a, b, c, d = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
    faces = np.vstack([np.stack([a, b, c], 1), np.stack([a, c, d], 1)])
    return U.ravel(), V.ravel(), faces, (nu, nv)


def _slab_cutter(origin, n, e1, e2, half, step, thick=200.0):
    """Closed slab whose top face is the displaced plane: keeps {x : (x-origin).n >= -0.02-relief}
    ... built as the region *behind* (+n side) of a displaced grid, thickness `thick`."""
    U, V, F, (nu, nv) = _grid_surface((-half, half), (-half, half), step)
    base = origin + np.outer(U, e1) + np.outer(V, e2)
    rel = wood(base)["relief"]
    top = base + np.outer(0.02 + rel, n)           # displaced inward (+n is into the part)
    # bottom (far) face: coarse copy pushed far along +n; build as a box with the grid as one face
    far = top + n * thick
    nvtx = len(top)
    verts = np.vstack([top, far])
    faces = [F[:, ::-1], F + nvtx]                  # grid faces outward (-n), far faces outward (+n)
    # side walls along the four grid borders
    idx = np.arange(nu * nv).reshape(nu, nv)
    borders = [idx[:, 0], idx[-1, :], idx[::-1, -1], idx[0, ::-1]]
    for bd in borders:
        a, b = bd[:-1], bd[1:]
        faces.append(np.stack([a, b, b + nvtx], 1))
        faces.append(np.stack([a, b + nvtx, a + nvtx], 1))
    m = trimesh.Trimesh(verts, np.vstack(faces), process=True)
    m.fix_normals()
    assert m.is_watertight and m.volume > 0
    return m


def sphere_cutter(theta0=np.radians(36.0), theta1=np.radians(146.0)):
    """Radial mesh: r(theta, phi) = R - 0.02 - relief inside the band, R + 1 outside."""
    n_phi = int(round(2 * pi * SPHERE_R / STEP / 8)) * 8
    band = np.arange(theta0, theta1 + 1e-9, STEP / SPHERE_R)
    thetas = np.concatenate([np.linspace(0, theta0, 12, endpoint=False)[1:], [theta0 - 1e-4], band,
                             [theta1 + 1e-4], np.linspace(theta1, pi, 12)[1:-1]])
    phis = np.arange(n_phi) * 2 * pi / n_phi
    T, P = np.meshgrid(thetas, phis, indexing="ij")
    inband = (T >= theta0) & (T <= theta1)
    dirs = np.stack([np.sin(T) * np.cos(P), np.sin(T) * np.sin(P), np.cos(T)], -1)
    R = np.full(T.shape, SPHERE_R + 1.0)
    pts = dirs[inband] * SPHERE_R + [0, 0, C_Z]
    R[inband] = SPHERE_R - 0.02 - wood(pts)["relief"]
    xyz = dirs * R[..., None] + [0, 0, C_Z]
    nt, npf = T.shape
    verts = np.vstack([[0, 0, SPHERE_R + 1 + C_Z], xyz.reshape(-1, 3), [0, 0, -(SPHERE_R + 1) + C_Z]])
    idx = lambda i, j: 1 + i * npf + (j % npf)
    j = np.arange(npf)
    faces = [np.stack([np.zeros(npf, int), idx(0, j), idx(0, j + 1)], 1)]
    for i in range(nt - 1):
        a, b, c, d = idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)
        faces += [np.stack([a, b, c], 1), np.stack([a, c, d], 1)]
    last = len(verts) - 1
    faces.append(np.stack([np.full(npf, last), idx(nt - 1, j + 1), idx(nt - 1, j)], 1))
    m = trimesh.Trimesh(verts, np.vstack(faces), process=False)
    if m.volume < 0:
        m.invert()
    return m


def cutters():
    up = np.array([UP_D.X, UP_D.Y, UP_D.Z])
    e1 = np.array([1.0, 0, 0])
    e2 = np.cross(up, e1)
    base_o = up * FOOT_H                          # plane p.up = FOOT_H
    cs = {"sphere": sphere_cutter(),
          "base": _slab_cutter(base_o, up, e1, e2, 70.0, STEP),
          "back": _slab_cutter(np.array([0, 0, BACK_Z - BACK_T]), np.array([0, 0, 1.0]),
                               np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), 70.0, STEP),
          "face": _slab_cutter(np.array([0, 0, FACE_Z]), np.array([0, 0, -1.0]),
                               np.array([1.0, 0, 0]), np.array([0, -1.0, 0]), 70.0, STEP)}
    return cs


# ------------------------------------------------------------------ parts
def exterior_mask(m):
    """Triangles on the outside of the clock (sphere, base, back face, face rim)."""
    c = m.triangles_center
    n = m.face_normals
    up = np.array([UP_D.X, UP_D.Y, UP_D.Z])
    rc = c - [0, 0, C_Z]
    rr = np.linalg.norm(rc, axis=1)
    sph = (rr > SPHERE_R - 0.5) & ((n * rc).sum(1) / np.maximum(rr, 1e-9) > 0.3)
    base = (c @ up < FOOT_H + 0.5) & (n @ up < -0.7)
    back = (c[:, 2] < BACK_Z - BACK_T + 0.5) & (n[:, 2] < -0.7)
    face = (c[:, 2] > FACE_Z - 0.5) & (n[:, 2] > 0.7)
    return sph | base | back | face


def woodify(name, shape, cs):
    raw = WOOD_OUT / f"_{name}_raw.stl"
    export_stl(shape, str(raw), tolerance=0.02, angular_tolerance=0.1)
    m = trimesh.load(raw)
    raw.unlink()
    for c in cs.values():
        m = trimesh.boolean.intersection([m, c], engine="manifold")
    bodies = [b for b in m.split(only_watertight=False) if b.is_watertight and b.volume > 1.0]
    assert len(bodies) == 1, (name, len(bodies))
    import texture
    m = texture.clean(bodies[0])
    assert m.is_watertight, name
    ext = exterior_mask(m)
    tools = wood(m.triangles_center)["tool"]
    paint = np.where(ext, tools + 1, 0).astype(np.int8)    # state = extruder number, 0 = object default
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
    t = time.time()
    cs = cutters()
    print("cutters:", {k: len(v.faces) for k, v in cs.items()}, f"{time.time() - t:.0f}s", flush=True)
    for name, fn in PARTS.items():
        t = time.time()
        m, paint = woodify(name, fn(), cs)
        m.export(WOOD_OUT / f"{name}_D.ply")
        np.save(WOOD_OUT / f"{name}_paint.npy", paint)
        p = to_print(name, m)
        p.export(WOOD_OUT / f"{name}.ply")
        share = np.bincount(paint, minlength=5) / len(paint)
        print(f"{name}: {len(m.faces)} faces, watertight {m.is_watertight}, vol {m.volume / 1000:.1f} cm3, "
              f"painted {np.mean(paint > 0) * 100:.0f}% (cherry/walnut/maple/oak "
              f"{'/'.join(f'{s * 100:.0f}' for s in share[1:])} %), {time.time() - t:.0f}s", flush=True)
