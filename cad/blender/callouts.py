"""Composite Blender renders onto a studio backdrop and draw arrows + numbered callouts.

.venv/bin/python blender/callouts.py [out_dir]
Reads blender/renders/<id>.png/.json + blender/scene.json; writes <out_dir>/<id>.jpg and
<out_dir>/callouts.json ({id: [{n, key, label}, ...]}) for the guide page.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "final"
def _font(*names):
    for n in names:
        try:
            ImageFont.truetype(n, 10)
            return n
        except OSError:
            continue
    raise SystemExit("no TrueType font found; install Noto Sans or DejaVu Sans")


FONT_B = _font("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", "NotoSans-Bold.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf")
FONT_R = _font("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "NotoSans-Regular.ttf", "DejaVuSans.ttf", "Arial.ttf", "arial.ttf")
ORANGE = (255, 106, 19, 255)
INK = (40, 36, 33, 255)
SS = 2                                            # supersample for clean lines
# render id -> step number in the assembly guide (guide step 2 is wiring, no render)
GUIDE_STEP = {"step_01": 1, "step_01b": 1, "step_02": 3, "step_03": 4, "step_04": 5, "step_05": 5,
              "step_06": 6, "step_07": 7, "step_08": 8, "step_09": 9, "step_10": 10, "step_10b": 10, "step_11": 11}


def backdrop(w, h):
    top, bot = (246, 243, 238), (226, 219, 209)
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = (y / (h - 1)) ** 1.4
        g.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    bg = g.resize((w, h)).convert("RGBA")
    # soft vignette
    v = Image.new("L", (w, h), 0)
    ImageDraw.Draw(v).ellipse([-w * 0.25, -h * 0.35, w * 1.25, h * 1.35], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(w * 0.08))
    dark = Image.new("RGBA", (w, h), (200, 192, 182, 255))
    return Image.composite(bg, dark, v)


def arrow(d, p0, p1, width):
    import math
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 4:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    head = min(width * 4.2, L * 0.6)
    bx, by = x1 - ux * head, y1 - uy * head
    d.line([(x0, y0), (bx, by)], fill=ORANGE, width=int(width))
    px, py = -uy * head * 0.55, ux * head * 0.55
    d.polygon([(x1, y1), (bx + px, by + py), (bx - px, by - py)], fill=ORANGE)


def layout(points, H, top, bottom, gap):
    """Spread label y positions (sorted by anchor y) so they are >= gap apart, within [top, bottom]."""
    order = sorted(range(len(points)), key=lambda i: points[i][1])
    ys = [min(max(points[i][1], top), bottom) for i in order]
    for k in range(1, len(ys)):
        ys[k] = max(ys[k], ys[k - 1] + gap)
    over = ys[-1] - bottom if ys else 0
    if over > 0:
        ys = [y - over for y in ys]
        for k in range(len(ys) - 2, -1, -1):
            ys[k] = min(ys[k], ys[k + 1] - gap)
    return {order[k]: ys[k] for k in range(len(order))}


def compose(step, labels, title, number_from=1):
    sid = step["id"]
    rgba = Image.open(HERE / "renders" / f"{sid}.png").convert("RGBA")
    proj = json.loads((HERE / "renders" / f"{sid}.json").read_text())
    W, H = rgba.size
    img = backdrop(W, H)
    img.alpha_composite(rgba)
    big = img.resize((W * SS, H * SS), Image.LANCZOS)
    d = ImageDraw.Draw(big)
    for (a, b) in proj["arrows"]:
        if a[2] > 0 and b[2] > 0:
            arrow(d, (a[0] * SS, a[1] * SS), (b[0] * SS, b[1] * SS), 7 * SS)
    for pts in proj.get("arcs", []):                     # curved "turn" arrows: polyline, head on the last chord
        if len(pts) < 4 or min(p[2] for p in pts) <= 0:
            continue
        q = [(p[0] * SS, p[1] * SS) for p in pts]
        d.line(q[:-3], fill=ORANGE, width=7 * SS, joint="curve")
        arrow(d, q[-4], q[-1], 7 * SS)

    keys = [k for k in step["callouts"] if proj["anchors"].get(k, [0, 0, -1])[2] > 0]
    legend = []
    if keys:
        fb = ImageFont.truetype(FONT_B, 30 * SS)
        fr = ImageFont.truetype(FONT_R, 30 * SS)
        pts = {k: (proj["anchors"][k][0] * SS, proj["anchors"][k][1] * SS) for k in keys}
        left = [k for k in keys if pts[k][0] < W * SS * 0.5]
        right = [k for k in keys if k not in left]
        margin = 40 * SS
        badge_r = 22 * SS
        gap = 74 * SS
        n = number_from
        num = {}
        for k in keys:                                   # number in reading order: top to bottom, left first
            pass
        for side, ks in (("L", left), ("R", right)):
            ys = layout([pts[k] for k in ks], H * SS, 120 * SS, (H - 60) * SS, gap)
            for i, k in enumerate(ks):
                num[k] = (side, ys[i])
        ordered = sorted(keys, key=lambda k: (num[k][0] == "R", num[k][1]))
        for k in ordered:
            side, ly = num[k]
            ax, ay = pts[k]
            text = labels.get(k, k)
            tw = d.textlength(text, font=fr)
            if side == "L":
                bx = margin + badge_r
                tx = bx + badge_r + 14 * SS
                elbow = tx + tw + 26 * SS
            else:
                bx = W * SS - margin - badge_r
                tx = bx - badge_r - 14 * SS - tw
                elbow = tx - 26 * SS
            # leader: anchor -> elbow (horizontal at label height) -> label
            d.line([(ax, ay), (elbow, ly)], fill=(40, 36, 33, 230), width=3 * SS)
            d.line([(elbow, ly), (tx + (tw + 8 * SS if side == "L" else -8 * SS), ly)], fill=(40, 36, 33, 230), width=3 * SS)
            d.ellipse([ax - 9 * SS, ay - 9 * SS, ax + 9 * SS, ay + 9 * SS], fill=(255, 255, 255, 255), outline=INK, width=3 * SS)
            d.ellipse([ax - 4 * SS, ay - 4 * SS, ax + 4 * SS, ay + 4 * SS], fill=ORANGE)
            pad = 10 * SS
            d.rounded_rectangle([tx - pad, ly - 24 * SS, tx + tw + pad, ly + 24 * SS], radius=10 * SS,
                                fill=(255, 255, 255, 236), outline=(210, 202, 192, 255), width=2 * SS)
            d.text((tx, ly), text, fill=INK, font=fr, anchor="lm")
            d.ellipse([bx - badge_r, ly - badge_r, bx + badge_r, ly + badge_r], fill=INK)
            d.text((bx, ly + 1 * SS), str(n), fill=(255, 255, 255, 255), font=fb, anchor="mm")
            legend.append({"n": n, "key": k, "label": text})
            n += 1
    if title:
        ft = ImageFont.truetype(FONT_B, 40 * SS)
        d.text((margin if keys else 40 * SS, 34 * SS), title, fill=INK, font=ft, anchor="lt")
    out = big.resize((W, H), Image.LANCZOS).convert("RGB")
    OUT.mkdir(parents=True, exist_ok=True)
    out.save(OUT / f"{sid}.jpg", quality=90, optimize=True, progressive=True)
    return legend


def main():
    scene = json.loads((HERE / "scene.json").read_text())
    labels = scene["labels"]
    allleg = {}
    for st in scene["steps"]:
        if not (HERE / "renders" / f"{st['id']}.png").exists():
            print("skip (not rendered)", st["id"])
            continue
        title = "" if st["id"].startswith("hero") else st["title"]
        if st["id"] in GUIDE_STEP:
            title = f"Step {GUIDE_STEP[st['id']]} — {st['title']}"
        allleg[st["id"]] = compose(st, labels, title)
        print("composed", st["id"], len(allleg[st["id"]]), "callouts")
    (OUT / "callouts.json").write_text(json.dumps(allleg, indent=1))


if __name__ == "__main__":
    main()
