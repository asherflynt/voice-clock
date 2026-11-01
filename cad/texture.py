"""Surface texture for the sphere shells (mesh level).

A closed "textured sphere" is built whose radius dips inward by up to DEPTH
following a pattern, then intersected with each shell mesh. Only the outer
DEPTH mm of the shells is touched, so all internal features stay as checked.

The pattern is mapped in a lat/long frame whose pole is the face axis (D +Z),
so the textured band (THETA0..THETA1) avoids both poles: the face opening and
the back plate.
"""
import numpy as np
import trimesh
from math import pi

from voice_clock import SPHERE_R, C_Z

TEXTURE = "knit"          # "knit" | "hex" | "none"
DEPTH = 0.6               # mm carved into the 2.5 mm wall
THETA0, THETA1 = np.radians(40.0), np.radians(137.0)   # textured band (polar angle from +Z)
STEP = 0.28               # mm surface sampling in the band

# smooth "hem" bands: texture fades in/out over HEM_FADE next to the face rim and
# the back-plate seam (cleaner edges, full first-layer contact on the face rim)
HEM_FACE = np.radians(42.8 + 0.6)      # face rim is at 42.8 deg
HEM_BACK = np.radians(131.7 - 0.8)     # rear-shell / back-plate seam at 131.7 deg
HEM_FADE = np.radians(2.4)


def amplitude(theta):
    def ss(x):
        x = np.clip(x, 0, 1)
        return x * x * (3 - 2 * x)
    return ss((theta - HEM_FACE) / HEM_FADE) * ss((HEM_BACK - theta) / HEM_FADE)


# knit: stitch columns around, stitch height along the meridian
KNIT_COLS = 96            # -> 3.9 mm stitch width at the equator
KNIT_H = 3.4              # mm stitch height


def _knit(u, v):
    """u: across stitch (0..1 per column), v: down stitch (0..1 per row) -> height 0..1."""
    fu = u - np.floor(u)
    fv = v - np.floor(v)
    h = np.zeros_like(fu)
    # jersey stitch: two yarn legs forming a V that meet at the bottom centre
    # each leg is a sheared ellipse that stays inside its row (rounded ends, no clipping)
    for cx, tilt in ((0.29, 0.40), (0.71, -0.40)):
        x = (fu - cx) * 2.0              # leg half-width units (cell width -> 2)
        y = (fv - 0.5)
        xr = x - tilt * y * 2.0          # shear into a slanted leg
        d2 = (xr / 0.42) ** 2 + (y / 0.49) ** 2
        # rounded yarn with a finite edge slope (no vertical wall -> no stair-stepping)
        h = np.maximum(h, np.clip(1 - d2, 0, 1) ** 0.85)
    return h


def _hex(u, v):
    """Hex dimple field (alternative geometric look)."""
    x = u * 1.0
    y = v * 0.866
    # nearest hex centre
    r = np.floor(y / 0.866 + 0.5)
    xs = x - 0.5 * (r % 2)
    c = np.floor(xs + 0.5)
    dx = xs - c
    dy = (y - r * 0.866)
    d = np.sqrt(dx * dx + dy * dy)
    return np.clip((d - 0.30) / 0.12, 0, 1)   # 1 = ridge, 0 = dimple floor


def height(theta, phi):
    """0..1, 1 = untouched outer surface."""
    if TEXTURE == "none":
        return np.ones_like(theta)
    arc_v = theta * SPHERE_R                       # mm along meridian
    if TEXTURE == "knit":
        u = phi / (2 * pi) * KNIT_COLS
        v = arc_v / KNIT_H
        return _knit(u, v)
    if TEXTURE == "hex":
        cols = 84
        u = phi / (2 * pi) * cols
        v = arc_v / (2 * pi * SPHERE_R / cols)
        return _hex(u, v)
    raise ValueError(TEXTURE)


def texture_solid():
    """Closed, single-valued radial mesh (D frame)."""
    n_phi = int(round(2 * pi * SPHERE_R / STEP / 12)) * 12
    if TEXTURE == "knit":
        n_phi = KNIT_COLS * max(1, round(n_phi / KNIT_COLS))
    band = np.arange(THETA0, THETA1 + 1e-9, STEP / SPHERE_R)
    thetas = np.concatenate([np.linspace(0, THETA0, 12, endpoint=False)[1:],
                             [THETA0 - 1e-4], band, [THETA1 + 1e-4],
                             np.linspace(THETA1, pi, 12)[1:-1]])
    phis = np.arange(n_phi) * 2 * pi / n_phi
    T, P = np.meshgrid(thetas, phis, indexing="ij")
    inband = (T >= THETA0) & (T <= THETA1)
    R = np.full(T.shape, SPHERE_R + 1.0)                 # outside band: no cut
    R[inband] = SPHERE_R - DEPTH * amplitude(T[inband]) * (1.0 - height(T[inband], P[inband]))
    xyz = np.stack([R * np.sin(T) * np.cos(P), R * np.sin(T) * np.sin(P), R * np.cos(T) + C_Z], -1)
    nt, npf = T.shape
    verts = np.vstack([[0, 0, SPHERE_R + 1 + C_Z], xyz.reshape(-1, 3), [0, 0, -(SPHERE_R + 1) + C_Z]])
    idx = lambda i, j: 1 + i * npf + (j % npf)
    faces = []
    j = np.arange(npf)
    faces.append(np.stack([np.zeros(npf, int), idx(0, j), idx(0, j + 1)], 1))
    rad = np.concatenate([[0], R.reshape(-1), [0]])
    for i in range(nt - 1):
        a, b, c, d = idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)
        # split each quad along the diagonal with the smaller height change so
        # slanted features don't stair-step against a fixed diagonal
        ac = np.abs(rad[a] - rad[c]) <= np.abs(rad[b] - rad[d])
        faces.append(np.where(ac[:, None], np.stack([a, b, c], 1), np.stack([a, b, d], 1)))
        faces.append(np.where(ac[:, None], np.stack([a, c, d], 1), np.stack([b, c, d], 1)))
    last = len(verts) - 1
    faces.append(np.stack([np.full(npf, last), idx(nt - 1, j + 1), idx(nt - 1, j)], 1))
    m = trimesh.Trimesh(verts, np.vstack(faces), process=False)
    if m.volume < 0:
        m.invert()
    return m


_SOLID = None


def apply(mesh_D):
    """Intersect a D-frame shell mesh with the textured sphere."""
    global _SOLID
    if TEXTURE == "none":
        return mesh_D
    if _SOLID is None:
        _SOLID = texture_solid()
    out = trimesh.boolean.intersection([mesh_D, _SOLID], engine="manifold")
    return out


def clean(mesh, tol=0.01):
    """Manifold simplify: collapses sub-tol edges where safe (keeps it a valid manifold)."""
    import manifold3d as m3
    M = m3.Manifold(m3.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                            tri_verts=np.asarray(mesh.faces, np.uint32)))
    o = M.set_tolerance(tol).simplify(tol).to_mesh()
    return trimesh.Trimesh(np.asarray(o.vert_properties[:, :3], float), np.asarray(o.tri_verts), process=False)


if __name__ == "__main__":
    s = texture_solid()
    print("texture solid:", len(s.vertices), "verts", len(s.faces), "faces, watertight", s.is_watertight,
          "volume", round(s.volume / 1000, 1), "cm3")
