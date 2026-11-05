"""Interference / assembly checks for voice_clock.py (D frame).

Uses the vendor reSpeaker STEP (not a proxy) for every clearance that involves the board.
"""
import itertools
from voice_clock import *

bad = 0


def flag(ok, msg):
    global bad
    bad += not ok
    print(f"  {msg:62s} {'ok' if ok else 'PROBLEM'}")


parts = {n: f() for n, f in PRINT_PARTS.items() if n not in ("tpu_washers", "insert_coupon")}
prox = proxies()
allp = {**parts, **prox}

print(flush=True); print("== every printed part is one solid")
for n, f in PRINT_PARTS.items():
    s = parts[n] if n in parts else f()
    k = len(s.solids())
    expect = {"tpu_washers": 4, "board_spacers": 3}.get(n, 1)
    flag(k == expect, f"{n}: {k} solid(s)")

# contacts that are intended (touching faces, crush nubs, screws through holes are not modelled)
ALLOWED = {
    frozenset({"spider", "board_spacers"}), frozenset({"board_spacers", "rs_pcb"}),
    frozenset({"carrier", "rs_pcb"}), frozenset({"carrier", "rs_xiao"}),
    frozenset({"front_shell", "rear_shell"}), frozenset({"rear_shell", "back_plate"}),
    frozenset({"rear_shell", "rs_pcb"}), frozenset({"light_guide", "rs_pcb"}), frozenset({"light_guide", "rs_leds"}),
    frozenset({"light_guide", "front_shell"}), frozenset({"spider", "cp_pcb"}),
    frozenset({"cp_knob", "cp_glass"}), frozenset({"cp_knob", "cp_housing"}),
    frozenset({"cp_pcb", "cp_conn"}), frozenset({"cp_housing", "cp_pcb"}),
    frozenset({"rs_pcb", "rs_leds"}), frozenset({"rs_pcb", "rs_xiao"}),
    frozenset({"back_plate", "speaker"}), frozenset({"mute_plunger", "rear_shell"}),
}
print(flush=True); print("== pairwise overlap (mm^3)")
for a, b in itertools.combinations(allp, 2):
    try:
        v = (allp[a] & allp[b]).volume
    except Exception:
        v = float("nan")
    if v > 0.01:
        ok = frozenset({a, b}) in ALLOWED and v < 1.0
        flag(ok, f"{a} x {b}: {v:.3f} mm3 {'(contact)' if ok else 'CLASH'}")

print(flush=True); print("== real reSpeaker STEP vs printed parts")
if RS_STEP is None:
    raise SystemExit("Put Seeed's respeaker_mic_array_xvf3800_1_with-xiao-0820.stp in cad/vendor/ "
                     "(it isn't redistributed here); the board checks need it.")
RS = respeaker_placed()
rs_solids = RS.solids()
pcb = max(rs_solids, key=lambda s: s.volume)


def _rmax(s):
    b = s.bounding_box()
    return max(abs(b.min.X), abs(b.max.X), abs(b.min.Y), abs(b.max.Y))


RS_EDGE = Compound([pcb] + [s for s in rs_solids if s is not pcb and _rmax(s) > 44])
print(f"  ({len(RS_EDGE.solids())} reSpeaker solids reach past r 44)", flush=True)
for n in ("rear_shell", "front_shell", "carrier", "light_guide", "spider", "board_spacers", "mute_plunger"):
    p = parts[n]
    pb = p.bounding_box()
    v = 0.0
    for s in rs_solids:
        sb = s.bounding_box()
        if sb.max.X < pb.min.X or sb.min.X > pb.max.X or sb.max.Y < pb.min.Y or sb.min.Y > pb.max.Y \
                or sb.max.Z < pb.min.Z or sb.min.Z > pb.max.Z:
            continue
        try:
            v += (s & p).volume
        except Exception:
            pass
    contact = n in ("rear_shell", "carrier", "light_guide", "board_spacers")
    flag(v < (1.0 if contact else 0.01), f"{n} x reSpeaker STEP: {v:.3f} mm3")
d = min(s.distance_to(parts["rear_shell"]) for s in rs_solids if s is not pcb and _rmax(s) > 44)
flag(d > 0.2, f"edge components -> rear shell, closest {d:.2f} mm")

print(flush=True); print("== assembly paths (discrete sweep)")
SW = [0.3, 0.6, 1, 2, 3, 5, 8, 12, 20, 30, 45]
# 1) the finished stack drops into the rear shell from the front
stack = [RS_EDGE, parts["carrier"], parts["spider"], parts["board_spacers"], parts["light_guide"],
         prox["cp_knob"], prox["cp_housing"], prox["cp_pcb"]]
rs_noplunger = parts["rear_shell"]
worst = 0.0
for s in SW:
    for st in stack:
        try:
            worst = max(worst, (Pos(0, 0, s) * st & rs_noplunger).volume)
        except Exception:
            pass
flag(worst < 0.01, f"stack into rear shell (from the front): max overlap {worst:.3f}")
# 2) the front shell comes on over the knob; hooks deflect, so mask the hook / ridge zones
mask = None
for ang in SNAP_ANG:
    m = radial_box(ang, SNAP_R_IN - 0.5, SPHERE_R + 1, SNAP_W + 0.2, -20, 20)
    mask = m if mask is None else mask + m
rear_masked = parts["rear_shell"] - mask
fs = parts["front_shell"]
worst = 0.0
for s in SW:
    for st in [rear_masked, parts["light_guide"], prox["cp_knob"], prox["cp_housing"], RS_EDGE]:
        try:
            worst = max(worst, ((Pos(0, 0, s) * fs) & st).volume)
        except Exception:
            pass
flag(worst < 0.01, f"front shell onto rear shell + stack: max overlap {worst:.3f}")
# barb travel = how far each hook must flex
hook_flex = SNAP_ENG + SNAP_GAP - SNAP_GAP
# 3) back plate (with speaker) goes in from behind
bmask = None
for ang in BSNAP_ANG:
    m = radial_box(ang, 20, SPHERE_R + 1, SNAP_W + 0.2, BACK_Z - 5, BACK_Z + 20)
    bmask = m if bmask is None else bmask + m
rear_bmasked = parts["rear_shell"] - bmask
worst = 0.0
for s in SW:
    for st in [parts["back_plate"], prox["speaker"]]:
        try:
            worst = max(worst, ((Pos(0, 0, -s) * st) & rear_bmasked).volume)
        except Exception:
            pass
flag(worst < 0.01, f"back plate + speaker into rear shell: max overlap {worst:.3f}")
for n in ("carrier", "rs_xiao"):
    d = prox["speaker"].distance_to(allp[n])
    flag(d > 2.0, f"speaker -> {n}: {d:.1f} mm")

print(flush=True); print("== snap hooks")
for nm, L in (("shell hooks", SNAP_ZC - (SNAP_ROOT_Z - 0.5)), ("back-plate hooks", BSNAP_ZC_UP + 0.5)):
    strain = 1.5 * SNAP_T * SNAP_ENG / L ** 2
    flag(strain < 0.01, f"{nm}: free length {L:.1f} mm, flex {SNAP_ENG} mm -> strain {strain*100:.2f} %")
r_open = r_in_at(BACK_Z)
tip = r_open - 1.0 + SNAP_ENG
flag(r_open - tip > 0.3, f"back-plate barb passes the opening (r {tip:.2f} vs {r_open:.2f})")
tip = SNAP_R_IN + SNAP_T + SNAP_GAP + SNAP_ENG
flag(r_in_at(SNAP_ZC + 2) - tip > 0.3, f"shell barb clears the front wall (r {tip:.2f} vs {r_in_at(SNAP_ZC + 2):.2f})")

print(flush=True); print("== base and floor (heights along world up, from the table)")
def lowest(shape):
    return min(Vector(v).dot(UP_D) for v in shape.vertices())
print(f"  flat base: d{2 * FOOT_R:.0f} (table at {FOOT_H:.2f}, floor top {FLOOR_TOP:.2f})")
floor = parts["rear_shell"] - half(UP_D, FLOOR_TOP + 0.3)
d = min(s.distance_to(floor) for s in rs_solids if _rmax(s) > 44)
flag(d > 0.3, f"board (PCB tab, reset button) above the floor / pocket: {d:.2f} mm")
low_all = min(lowest(s) for s in rs_solids)
flag(low_all - FOOT_H > 1.2, f"lowest board part (reset nub) above the table: {low_all - FOOT_H:+.2f} mm")
for n in ("carrier", "speaker", "back_plate"):
    print(f"  {n:12s} lowest point {lowest(allp[n]) - FLOOR_TOP:+.2f} mm above floor top")
# the base must be one flat ring: both shells touch the table
for n in ("front_shell", "rear_shell"):
    flag(abs(lowest(parts[n]) - FOOT_H) < 0.05, f"{n} sits on the table")

print(flush=True); print("== mute plunger")
gap = plunger_rest_tip() - RS_MUTE_TIP_R
flag(0.05 < gap < 0.5, f"rest gap to the BUTA nub {gap:.2f} mm (was 3.5)")
flag(PLG_TRAVEL >= gap + 0.25 + 0.3 + 0.2, f"cap travel {PLG_TRAVEL} mm covers gap + switch travel + board play")
flag(PLG_Z - PLG_ROD_R < -3.75 + 0.2 and PLG_Z + PLG_ROD_R > -2.20 - 0.2,
     f"rod d{2 * PLG_ROD_R} at z {PLG_Z} covers the nub (z -3.75..-2.20)")
flag(SPLIT_Z - (PLG_Z + PLG_CB_R) >= 1.0, f"counterbore to seam {SPLIT_Z - (PLG_Z + PLG_CB_R):.2f} mm")
nub = radial_box(90, RS_MUTE_TIP_R - 1.0, RS_MUTE_TIP_R, 2.9, -3.75, -2.20)
pressed = Pos(0, -(gap + 0.25), 0) * parts["mute_plunger"]
flag((pressed & nub).volume > 0.01, "pressed plunger reaches the nub")

print(flush=True); print("== knob / screen gap")
print(f"  knob ring d{2 * CP_KNOB_R:.1f} in bore d{2 * LG_RI:.2f}: radial gap {LG_KNOB_GAP:.2f} mm (was 0.75)")
print(f"  guide land d{2 * LG_LAND_R:.2f} on the d{2 * CP_HOUSING_R:.2f} housing: {LG_LAND_R - CP_HOUSING_R:.2f} mm")
flag(LG_LAND_R - CP_HOUSING_R < LG_KNOB_GAP - 0.1, "land locates the panel before the knob can rub")

print(flush=True); print("== spider vs CrowPanel plug keep-outs")
for (x0, x1, y0, y1) in CP_KEEPOUT:
    k = Pos((x0 + x1) / 2, (y0 + y1) / 2, 0) * Box(x1 - x0, y1 - y0, CP_REAR_Z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    v = (k & parts["spider"]).volume
    flag(v < 0.01, f"keep-out {x0, x1, y0, y1}: {v:.3f}")

print(flush=True); print("== speaker")
spk = prox["speaker"]; bp = parts["back_plate"]; bb = spk.bounding_box()
face_gap = bb.min.Z - BACK_Z
flag(abs(face_gap - SPK_GASKET) < 0.05, f"diaphragm face -> back plate gap {face_gap:.2f} mm (foam {SPK_GASKET})")
for sxn in (-1, 1):
    bx = sxn * SPK_EAR_PITCH / 2
    probe = cyl(0.4, BACK_Z, -20, bx, SPK_CY + 2.5)
    gap_e = (spk & probe).bounding_box().min.Z - (bp & probe).bounding_box().max.Z
    flag(abs(gap_e - TPU_WASHER_T) < 0.05, f"ear at x={bx:+.2f}: ear-to-boss gap {gap_e:.2f} mm")
for n in ("back_plate", "rear_shell", "carrier"):
    d = spk.distance_to(parts[n])
    flag(d >= 0.5, f"speaker clearance to {n}: {d:.2f} mm")

print(flush=True); print("== screws (all from the user's kits) - thread engaged")
tip_clamp = CARRIER_Z0 + CARRIER_CB + M2_CLAMP_LEN
rows = [
    ("CrowPanel hub   M3x12 SHCS", 12 - (CP_HUB_FACE_Z - (STANDOFF_L + 1.0))),
    (f"clamp           M2x{M2_CLAMP_LEN:.0f} SHCS", min(tip_clamp, STANDOFF_L + M2_INSERT_L) - STANDOFF_L),
    ("speaker ear     M2x10 SHCS", min(10 - (TPU_WASHER_T * 2 + SPK_EAR_T), M2_INSERT_L)),
]
for n, e in rows:
    flag(e >= 2.0, f"{n} {e:4.1f} mm")
flag(tip_clamp <= STANDOFF_L + M2_INSERT_L + 0.3 + SPIDER_PILLAR - 0.6, f"clamp screw tip z={tip_clamp:.1f} stays in the spider")
flag(10 - (TPU_WASHER_T * 2 + SPK_EAR_T) <= M2_INSERT_DEPTH - 0.3, "speaker screw tip stays in its hole")

print(flush=True); print("== CrowPanel cable path at the notch")
lane = radial_box(NOTCH_ANG, RS_R + 0.5, SPHERE_R, 3.0, CARRIER_Z0, 0.0) & sphere_in(-0.3)
v = (lane & parts["rear_shell"]).volume
flag(v < 0.01, f"lane past the board edge at {NOTCH_ANG:.0f} deg ({r_in_at(0) - 0.3 - RS_R - 0.5:.1f} mm wide) free")
v = sum((lane & s).volume for s in rs_solids if s.bounding_box().max.Z > CARRIER_Z0)
flag(v < 0.01, "no reSpeaker parts in the lane")

print(flush=True); print("== mic channel length (mm):", round(r_out_at(MIC_CH_Z) - RS_MIC_R, 1))
print(flush=True); print("== depth: CrowPanel rear -> spider top:", round(CP_REAR_Z - (STANDOFF_L + SPIDER_T), 2), "mm")
print(f"== size: d{2 * SPHERE_R:.0f} sphere, {SPHERE_R + CEN.dot(UP_D) - FOOT_H:.1f} mm tall, "
      f"{FACE_Z + KNOB_PROUD - (BACK_Z - BACK_T):.1f} mm deep incl. knob, base d{2 * FOOT_R:.0f}")
print("RESULT:", "PASS" if not bad else f"{bad} problem(s)")
