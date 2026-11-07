"""Render the assembled clock: exterior, back, cutaway, exploded and texture close-up.

Vectorised numpy z-buffer (handles the ~1M-triangle textured shells). Textured
parts are read from out/asm/<name>.stl (D frame, written by voice_clock.py).
"""
import numpy as np
import trimesh
from math import radians, cos, sin
from voice_clock import *

COL = {
    "front_shell": "#d8a29c", "rear_shell": "#d8a29c", "back_plate": "#c99590",
    "ring_base": "#c9ccd2", "ring_shell": "#f2f0ea", "spider": "#5a6270", "carrier": "#5a6270",
    "mute_plunger": "#c98f89", "cp_knob": "#3b3d42", "cp_glass": "#f7e9e8",
    "cp_housing": "#8e9196", "cp_pcb": "#2f7d4f", "cp_conn": "#e8e2d0",
    "rs_pcb": "#1d1f24", "rs_leds": "#ffffff", "rs_xiao": "#3466a8",
    "speaker": "#202020",
}
BG = "#f4f1ec"


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255


def tess(shape, tol=0.05):
    v, f = shape.tessellate(tol, 0.1)
    return np.array([[p.X, p.Y, p.Z] for p in v]), np.array(f, int)


def world(v):
    """D frame -> world: tilt about X, table at y=0."""
    a = radians(-TILT)
    R = np.array([[1, 0, 0], [0, cos(a), -sin(a)], [0, sin(a), cos(a)]])
    w = v @ R.T
    w[:, 1] -= FOOT_H
    return w


def _raster_small(zb, img, sx, sy, sz, tri, shade, col, k):
    """Vectorised fill for triangles whose bbox fits in k x k pixels."""
    H2, W2 = zb.shape
    for c0 in range(0, len(tri), 60000):
        t = tri[c0:c0 + 60000]
        xs, ys, zs = sx[t], sy[t], sz[t]
        x0 = np.floor(xs.min(1)).astype(int)
        y0 = np.floor(ys.min(1)).astype(int)
        ox, oy = np.meshgrid(np.arange(k), np.arange(k))
        px = x0[:, None] + ox.ravel()[None]          # (n, k*k)
        py = y0[:, None] + oy.ravel()[None]
        gx, gy = px + 0.5, py + 0.5
        X0, X1, X2 = xs[:, 0:1], xs[:, 1:2], xs[:, 2:3]
        Y0, Y1, Y2 = ys[:, 0:1], ys[:, 1:2], ys[:, 2:3]
        d = (Y1 - Y2) * (X0 - X2) + (X2 - X1) * (Y0 - Y2)
        d = np.where(np.abs(d) < 1e-12, np.nan, d)
        w0 = ((Y1 - Y2) * (gx - X2) + (X2 - X1) * (gy - Y2)) / d
        w1 = ((Y2 - Y0) * (gx - X2) + (X0 - X2) * (gy - Y2)) / d
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6) & (px >= 0) & (py >= 0) & (px < W2) & (py < H2)
        z = w0 * zs[:, 0:1] + w1 * zs[:, 1:2] + w2 * zs[:, 2:3]
        sh = np.broadcast_to(shade[c0:c0 + 60000, None], m.shape)
        idx = (py * W2 + px)[m]
        z, sh = z[m], sh[m]
        flat = zb.reshape(-1)
        keep = z > flat[idx]
        idx, z, sh = idx[keep], z[keep], sh[keep]
        o = np.argsort(z)                             # ascending: last write = nearest
        flat[idx[o]] = z[o]
        img.reshape(-1, 3)[idx[o]] = col[None] * sh[o, None]


def _raster_big(zb, img, sx, sy, sz, tri, shade, col):
    H2, W2 = zb.shape
    for ti, (i0, i1, i2) in enumerate(tri):
        xs = np.array([sx[i0], sx[i1], sx[i2]]); ys = np.array([sy[i0], sy[i1], sy[i2]])
        x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, W2))
        y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, H2))
        if x0 >= x1 or y0 >= y1:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-9:
            continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any():
            continue
        z = w0 * sz[i0] + w1 * sz[i1] + w2 * sz[i2]
        sub = zb[y0:y1, x0:x1]
        upd = m & (z > sub)
        sub[upd] = z[upd]
        img[y0:y1, x0:x1][upd] = col * shade[ti]


def render(items, yaw, pitch, fname, W=1400, H=1100, ss=2, zoom=1.0, focus=None, title=None):
    W2, H2 = W * ss, H * ss
    zb = np.full((H2, W2), -1e9)
    img = np.ones((H2, W2, 3)) * hexrgb(BG)
    y, p = radians(yaw), radians(pitch)
    Ry = np.array([[cos(y), 0, sin(y)], [0, 1, 0], [-sin(y), 0, cos(y)]])
    Rx = np.array([[1, 0, 0], [0, cos(p), -sin(p)], [0, sin(p), cos(p)]])
    R = Rx @ Ry
    allv = np.vstack([world(v) for v, f, c in items])
    cen = (allv.max(0) + allv.min(0)) / 2 if focus is None else np.asarray(focus, float)
    ext = np.abs((allv - (allv.max(0) + allv.min(0)) / 2) @ R.T)[:, :2].max(0)
    scale = min(W2 / (2.3 * ext[0]), H2 / (2.3 * ext[1])) * zoom
    light = np.array([-0.45, 0.65, 0.62]); light /= np.linalg.norm(light)
    for v, f, c in items:
        q = (world(v) - cen) @ R.T
        sx = q[:, 0] * scale + W2 / 2
        sy = -q[:, 1] * scale + H2 / 2
        sz = q[:, 2]
        p0, p1, p2 = q[f[:, 0]], q[f[:, 1]], q[f[:, 2]]
        n = np.cross(p1 - p0, p2 - p0)
        n = n / (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
        shade = 0.30 + 0.70 * np.clip(np.abs(n @ light), 0, 1)
        col = hexrgb(c)
        bw = np.ptp(sx[f], 1); bh = np.ptp(sy[f], 1)
        small = (bw < 7) & (bh < 7)
        if small.any():
            _raster_small(zb, img, sx, sy, sz, f[small], shade[small], col, 8)
        if (~small).any():
            _raster_big(zb, img, sx, sy, sz, f[~small], shade[~small], col)
    img = img.reshape(H, ss, W, ss, 3).mean((1, 3))
    from PIL import Image, ImageDraw
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    if title:
        ImageDraw.Draw(im).text((24, 20), title, fill=(60, 60, 60))
    im.save(fname)
    print("wrote", fname, flush=True)


OFFS = {"front_shell": 2.6, "ring_shell": 2.0, "ring_base": 0.3, "cp_knob": 1.1, "cp_glass": 1.1,
        "cp_pcb": 1.1, "cp_conn": 1.1, "spider": 0.5, "rs_pcb": 0, "rs_leds": 0,
        "rs_xiao": 0, "carrier": -0.5, "rear_shell": -1.1, "speaker": -1.6, "back_plate": -1.8,
        "mute_plunger": 2.6}


def build(cut=False, explode=0.0):
    parts = {n: f() for n, f in PRINT_PARTS.items() if n not in ("tpu_washers", "insert_coupon", "foot_pads")}
    prox = proxies()
    items = []
    for n, s in {**parts, **prox}.items():
        if n in TEXTURED:
            m = trimesh.load(OUT / "asm" / f"{n}.ply", process=False)
            if cut:
                m = m.slice_plane([0, 0, 0], [-1, 0, 0], cap=True)
            v, f = np.asarray(m.vertices), np.asarray(m.faces)
        else:
            if cut:
                s = s & half((-1, 0, 0), 0)
                if s.volume < 1e-6:
                    continue
            v, f = tess(s)
        if not len(f):
            continue
        v = v.copy()
        if explode:
            v[:, 2] += OFFS[n] * explode
            if n == "mute_plunger":
                v[:, 1] += 12
        items.append((v, f, COL[n]))
    return items


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    full = build()
    render(full, yaw=-32, pitch=12, fname=OUT / "render_exterior.png",
           title="Voice Clock - exterior, knit texture 0.6 mm")
    render(full, yaw=148, pitch=12, fname=OUT / "render_back.png",
           title="Back: speaker grille, USB-C inlet, twist-lock back plate")
    # close-up of the texture on the upper left shoulder
    # point on the sphere facing the camera, upper-right of the body
    yc, pc = radians(-32), radians(12)
    Ry = np.array([[cos(yc), 0, sin(yc)], [0, 1, 0], [-sin(yc), 0, cos(yc)]])
    Rx = np.array([[1, 0, 0], [0, cos(pc), -sin(pc)], [0, sin(pc), cos(pc)]])
    view = (Rx @ Ry).T @ np.array([0.55, 0.25, 0.80])
    focus = world(np.array([[0, 0, C_Z]]))[0] + SPHERE_R * view / np.linalg.norm(view)
    render(full, yaw=-32, pitch=12, zoom=4.0, focus=focus,
           fname=OUT / "render_texture_closeup.png", title="Knit texture close-up (about 30 mm across)")
    render(build(cut=True), yaw=-90 + 1e-3, pitch=0, fname=OUT / "render_cutaway.png",
           title="Side section through the centre (right half removed)")
    render(build(explode=40), yaw=-58, pitch=14, fname=OUT / "render_exploded.png",
           title="Exploded view")
