"""Interference / assembly checks for voice_clock.py v2 (D frame).

Uses the vendor reSpeaker STEP (not a proxy) for every clearance that involves the board, and steps
both twist locks through their whole travel.
"""
import itertools
from math import degrees, radians, atan2, hypot, asin
from voice_clock import *

bad = 0


def flag(ok, msg):
    global bad
    bad += not ok
    print(f"  {msg:70s} {'ok' if ok else 'PROBLEM'}", flush=True)


def vol(a, b):
    try:
        r = a & b
        return 0.0 if r is None else r.volume
    except Exception:
        return float("nan")


parts = {n: f() for n, f in PRINT_PARTS.items() if n not in ("tpu_washers", "foot_pads")}
prox = proxies()
allp = {**parts, **prox}

print(flush=True); print("== every printed part is one solid")
for n, f in PRINT_PARTS.items():
    s = parts[n] if n in parts else f()
    k = len(s.solids())
    expect = {"tpu_washers": 4, "foot_pads": 2}.get(n, 1)
    flag(k == expect, f"{n}: {k} solid(s)")

# contacts that are intended (touching faces, crush ribs, screws through holes are not modelled)
ALLOWED = {
    frozenset({"spider", "ring_base"}), frozenset({"ring_base", "rs_pcb"}), frozenset({"ring_shell", "rs_pcb"}),
    frozenset({"ring_base", "ring_shell"}),
    frozenset({"carrier", "rs_pcb"}), frozenset({"carrier", "rs_xiao"}),
    frozenset({"front_shell", "rear_shell"}), frozenset({"rear_shell", "back_plate"}),
    frozenset({"rear_shell", "rs_pcb"}), frozenset({"spider", "cp_pcb"}),
    frozenset({"cp_knob", "cp_glass"}), frozenset({"cp_pcb", "cp_conn"}),
    frozenset({"rs_pcb", "rs_leds"}), frozenset({"rs_pcb", "rs_xiao"}),
    frozenset({"back_plate", "speaker"}), frozenset({"mute_plunger", "rear_shell"}),
}
print(flush=True); print("== pairwise overlap, locked (mm^3)")
for a, b in itertools.combinations(allp, 2):
    v = vol(allp[a], allp[b])
    if v > 0.01:
        ok = frozenset({a, b}) in ALLOWED and v < 1.5
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


def step_overlap(p):
    pb = p.bounding_box()
    v = 0.0
    for s in rs_solids:
        sb = s.bounding_box()
        if sb.max.X < pb.min.X or sb.min.X > pb.max.X or sb.max.Y < pb.min.Y or sb.min.Y > pb.max.Y \
                or sb.max.Z < pb.min.Z or sb.min.Z > pb.max.Z:
            continue
        v += vol(s, p)
    return v


RS_EDGE = Compound([pcb] + [s for s in rs_solids if s is not pcb and _rmax(s) > 44])
RS_FRONT = Compound([s for s in rs_solids if s is not pcb and s.bounding_box().min.Z > -0.05])
print(f"  ({len(RS_EDGE.solids())} reSpeaker solids reach past r 44)", flush=True)
for n in ("rear_shell", "front_shell", "carrier", "ring_base", "ring_shell", "spider", "mute_plunger"):
    v = step_overlap(parts[n])
    contact = n in ("rear_shell", "carrier", "ring_base", "ring_shell")
    flag(v < (1.5 if contact else 0.01), f"{n} x reSpeaker STEP: {v:.3f} mm3")
for n in ("ring_base", "ring_shell"):
    d = min(s.distance_to(parts[n]) for s in RS_FRONT.solids())
    flag(d > 0.05, f"{n} -> LEDs and LED capacitors: closest {d:.2f} mm")
d = min(s.distance_to(parts["rear_shell"]) for s in rs_solids if s is not pcb and _rmax(s) > 44)
flag(d > 0.2, f"edge components -> rear shell, closest {d:.2f} mm")

SW = [0.3, 0.6, 1, 2, 3, 5, 8, 12, 20, 30, 45]
print(flush=True); print("== the stack drops into the rear shell from the front")
stack = [RS_EDGE, parts["carrier"], parts["spider"], parts["ring_base"], parts["ring_shell"],
         prox["cp_knob"], prox["cp_pcb"]]
worst = 0.0
rear_plg = parts["rear_shell"] + parts["mute_plunger"]       # the plunger is clicked in first
for s in SW + [9, 10, 11, 15]:
    for st in stack:
        worst = max(worst, vol(Pos(0, 0, s) * st, rear_plg))
flag(worst < 0.01, f"stack into rear shell (mute plunger already fitted): max overlap {worst:.3f}")

# ---------------------------------------------------------------- front <-> rear bayonet
print(flush=True); print("== front <-> rear twist lock")
band = zslab(-8, 10)
fs_band = parts["front_shell"] & band
rs_band = parts["rear_shell"] & band
fs = parts["front_shell"]
stack_fs = [parts["ring_shell"], prox["cp_knob"], RS_EDGE]
# 1) axial approach at the entry angle (front turned TW_ANGLE CCW = unlocked)
entry = Rot(0, 0, TW_ANGLE)
worst = 0.0
for s in SW:
    worst = max(worst, vol(Pos(0, 0, s) * (entry * fs_band), rs_band))
    for st in stack_fs:
        worst = max(worst, vol(Pos(0, 0, s) * (entry * fs), st))
flag(worst < 0.01, f"front shell on at the entry angle (+{TW_ANGLE:.0f} deg): max overlap {worst:.3f}")
# 2) the twist, seated: front from +TW_ANGLE back to 0 (clockwise seen from the front). The detent
#    fingers flex radially by design, so they are masked here and checked on their own below.
fmask = None
for a in TW_FINGERS:
    k0, k1 = finger_span(a, dict(TW_LUGS)[a])
    m = sector([(FING_BUMP_R - 0.3, SPLIT_Z - 1), (BLK_RI + FING_T + 0.01, SPLIT_Z - 1),
                (BLK_RI + FING_T + 0.01, BLK_TOP + 0.5), (FING_BUMP_R - 0.3, BLK_TOP + 0.5)], k0 - 0.3, k1 + 0.3)
    fmask = m if fmask is None else fmask + m
fs_rigid = fs_band - fmask
rigid_vol, finger_vol, worst_stack = 0.0, 0.0, 0.0
for phi in (TW_ANGLE, 9, 8, 7, 6, 5, 4, 3, 2, 1.5, 1, 0.5, 0.25, 0):
    t = Rot(0, 0, phi)
    rigid_vol = max(rigid_vol, vol(t * fs_rigid, rs_band))
    finger_vol = max(finger_vol, vol(t * (fs_band & fmask), rs_band))
    for st in stack_fs:
        worst_stack = max(worst_stack, vol(t * fs, st))
n_lugs = len(TW_LUGS)
flag(rigid_vol < 0.01, f"twist sweep vs rear shell (rigid parts): max overlap {rigid_vol:.3f} mm3")
defl = COL_RO - FING_BUMP_R
Lf = FING_LEN
f_strain = 1.5 * FING_T * defl / Lf ** 2
print(f"  detent fingers: {len(TW_FINGERS)} x {Lf:.1f} mm long, {FING_T:.1f} thick, ride the collar {defl:.2f} mm deflected "
      f"(strain {f_strain * 100:.2f} %), click into V-grooves at lock; bump overlap while riding {finger_vol:.2f} mm3")
flag(f_strain < 0.012 and 0 < finger_vol, "detent fingers flex within the strain limit and do engage the collar")
flag(worst_stack < 0.01, f"twist sweep vs light ring, knob and board: max overlap {worst_stack:.3f}")
v_lock = vol(fs_band, rs_band)
flag(v_lock < 0.05, f"locked: front x rear overlap {v_lock:.3f} mm3 (bumps sit in their dimples)")
v_over = vol(Rot(0, 0, -0.6) * fs_band, rs_band)
flag(v_over > 0.05, f"stop posts block over-travel (-0.6 deg overlap {v_over:.2f} mm3)")
flat = COL_RO + LUG_FLAT - BLK_RI
print(f"  lug engagement: flat bearing {flat:.2f} mm radial on {n_lugs} lugs, axial clearance {LUG_Z0 - BLK_TOP:.2f} mm")
flag(flat >= 0.45, "flat bearing (no 45 deg cam face in the load path) >= 0.45 mm")
arc = sum(radians(block_span(sp)) * (BLK_RI + COL_RO + LUG_FLAT) / 2 for _, sp in TW_LUGS)
print(f"  bearing area {arc * flat:.0f} mm2; lug root shear area {sum(radians(sp) * COL_RO * (COL_TOP - LUG_Z0) for _, sp in TW_LUGS):.0f} mm2")
gaps = sorted(a for a, _ in TW_LUGS)
gmax = max((gaps[(i + 1) % len(gaps)] - gaps[i]) % 360 for i in range(len(gaps)))
flag(gmax <= 95, f"largest angle between lugs {gmax:.0f} deg")

# ---------------------------------------------------------------- back plate bayonet
print(flush=True); print("== back plate twist lock")
bp = parts["back_plate"]
spk = prox["speaker"]
rear = parts["rear_shell"]
rb_band = rear & zslab(BACK_Z - 3, BACK_Z + 16)
tmask = None
for t in BP_PAWLS:
    m = sector([(BP_PAWL_SLOT[0] - 0.1, BACK_Z - 3), (BP_TOOTH_RO + 0.5, BACK_Z - 3),
                (BP_TOOTH_RO + 0.5, BACK_Z + BP_LIP_T + 1), (BP_PAWL_SLOT[0] - 0.1, BACK_Z + BP_LIP_T + 1)],
               t - 1.2, t + BP_PAWL_LEN + 1)
    tmask = m if tmask is None else tmask + m
bp_rigid = bp - tmask
# the pawls flex inward: model each bent (rotated about its root) so the tooth apex just clears the lip
from math import cos as _c, sin as _s
bp_bent = bp_rigid
for t in BP_PAWLS:
    region = sector([(BP_PAWL_SLOT[0] + 0.01, BACK_Z - 3), (BP_PAWL_SLOT[1] - 0.01, BACK_Z - 3),
                     (BP_PAWL_SLOT[1] - 0.01, BACK_Z + BP_LIP_T + 1), (BP_PAWL_SLOT[0] + 0.01, BACK_Z + BP_LIP_T + 1)],
                    t - 2.3, t + BP_PAWL_LEN - 0.2) + \
             sector([(BP_PAWL_R[1] - 0.2, BACK_Z - 1.3), (BP_TOOTH_RO + 0.3, BACK_Z - 1.3),
                     (BP_TOOTH_RO + 0.3, BACK_Z + BP_LIP_T), (BP_PAWL_R[1] - 0.2, BACK_Z + BP_LIP_T)], t - 2.3, t + 3.5)
    pawl = bp & region
    root_a = t + BP_PAWL_LEN
    rx, ry = polar((BP_PAWL_R[0] + BP_PAWL_R[1]) / 2, root_a)
    need = BP_TOOTH_RO - (BP_LIP_RI - 0.1)
    best = None
    for sgn in (1, -1):
        for k in range(1, 121):
            ang = sgn * k * 0.1
            bent = Pos(rx, ry, 0) * (Rot(0, 0, ang) * (Pos(-rx, -ry, 0) * pawl))
            tip = bent & sector([(BP_LIP_RI - 0.1, BACK_Z - 3), (BP_TOOTH_RO + 1, BACK_Z - 3),
                                 (BP_TOOTH_RO + 1, BACK_Z + 3), (BP_LIP_RI - 0.1, BACK_Z + 3)], t - 3, t + 5)
            if tip is None or tip.volume < 1e-4:
                best = (ang, bent)
                break
        if best:
            break
    assert best, "pawl cannot bend clear of the lip"
    wall = bp - region
    # a real cantilever doesn't move at its root; the rigid-rotation model does, so skip the last 2 deg
    rootzone = sector([(BP_PAWL_SLOT[0] - 1, BACK_Z - 4), (BP_TOOTH_RO + 1, BACK_Z - 4),
                       (BP_TOOTH_RO + 1, BACK_Z + 4), (BP_PAWL_SLOT[0] - 1, BACK_Z + 4)], t + BP_PAWL_LEN - 2.0, t + BP_PAWL_LEN + 1)
    hit = vol(best[1] - rootzone, wall)
    flag(hit < 0.01, f"pawl at {t:.0f} deg bent {abs(best[0]):.2f} deg (tooth {need:.2f} mm in) clears its slot wall ({hit:.3f} mm3)")
    bp_bent = bp_bent + best[1]
usb_y_top, usb_y_back = usb_pcb_y()
tips = None
for sx in (-1, 1):                                 # M2 x 10 from the board's back (rim side) toward the speaker
    hx = sx * USB_HOLE_PITCH / 2
    scr = Pos(hx, usb_y_back, BACK_Z + USB_HOLE_Z) * Rot(-90, 0, 0) * Cylinder(1.0, USB_SCREW_L,
                                                                               align=(Align.CENTER, Align.CENTER, Align.MIN))
    scr = scr + Pos(hx, usb_y_back - 2.0, BACK_Z + USB_HOLE_Z) * Rot(-90, 0, 0) * Cylinder(1.9, 2.0,
                                                                                       align=(Align.CENTER, Align.CENTER, Align.MIN))
    tips = scr if tips is None else tips + scr
scr_all = tips
L_, H_, T_ = USB_PCB                               # the board itself (PCB + socket) turns with the plate too
tips = tips + Pos(0, usb_y_back + T_ / 2, BACK_Z + H_ / 2) * Box(L_, T_, H_) \
            + Pos(0, USB_CY, BACK_Z - 1.48 + 7.3 / 2) * Box(8.94, USB_SOCKET_H, 7.3)
moving = [bp_bent, spk, tips]
worst = 0.0
entry = Rot(0, 0, -BP_TWIST)
for s in SW:
    for m in moving:
        worst = max(worst, vol(Pos(0, 0, -s) * (entry * m), rb_band))
flag(worst < 0.01, f"back plate in at the entry angle (-{BP_TWIST:.0f} deg): max overlap {worst:.3f}")
worst = 0.0
for phi in (-BP_TWIST, -24, -16, -8, -4, -1, 0):
    t = Rot(0, 0, phi)
    for m in moving:
        worst = max(worst, vol(t * m, rear))
    worst = max(worst, vol(t * spk, parts["carrier"]))
flag(worst < 0.01, f"twist sweep (plate, speaker, USB-C board + screws) vs rear shell + carrier: max overlap {worst:.3f}")
v_lock = vol(bp, rear)
flag(v_lock < 0.05, f"locked: back plate x rear shell {v_lock:.3f} mm3 (teeth sit in their notches)")
flag(vol(Rot(0, 0, 0.6) * bp_rigid, rear) > 0.05, "hard stop blocks over-travel")
flat_bp = (BP_LIP_RI + 0.5) - BP_LIP_RI
print(f"  lugs: flat bearing {flat_bp:.2f} mm on the lip (then 45 deg out to r {BP_LUG_RO}), axial clearance {BP_LUG_Z0 - BACK_Z - BP_LIP_T:.2f} mm")
flag(flat_bp >= 0.5, "back-plate lugs bear flat on the lip >= 0.5 mm")
defl = BP_TOOTH_RO - BP_LIP_RI
L = radians(BP_PAWL_LEN) * (BP_PAWL_R[0] + BP_PAWL_R[1]) / 2
tk = BP_PAWL_R[1] - BP_PAWL_R[0]
strain = 1.5 * tk * defl / L ** 2
flag(strain < 0.012, f"pawl arm {L:.1f} mm x {tk:.1f} mm flexes {defl:.2f} mm in-plane -> strain {strain * 100:.2f} %")

# ---------------------------------------------------------------- stack keying
print(flush=True); print("== stack keying (rotation)")
key_r = (CRADLE_PAD_R + CARRIER_R) / 2
play = degrees(CARRIER_KEY_CLR / key_r)
flag(play < 0.25, f"carrier notches on the {len(CRADLE_ANG)} key ribs: +-{CARRIER_KEY_CLR:.2f} mm -> +-{play:.2f} deg")
flag(KEY_Z0 < CARRIER_Z0 - 0.5, f"key ribs reach below the carrier (z {KEY_Z0} vs {CARRIER_Z0})")
v = vol(parts["carrier"], rear)
flag(v < 0.01, f"carrier x key ribs: {v:.3f} mm3")
m2 = (CARRIER_M2_CLR - 1.886) / 2
print(f"  carrier M2 holes d{CARRIER_M2_CLR}: hole tolerance alone allows +-{degrees(m2 / 33):.2f} deg between board and carrier")
m3 = (M3_CLR - 2.874) / 2
print(f"  spider M3 holes d{M3_CLR}: hole tolerance alone allows +-{degrees(m3 / 5.95):.2f} deg for the CrowPanel (6g screw, worst case; it sets once, it does not wobble)")
print(f"  CrowPanel trim CP_ROT_TRIM_DEG = {CP_ROT_TRIM_DEG:+.1f} deg: cancels the fixed ~5 deg dial offset measured on v1 (one photo, +-2); the firmware has no trim")

# ---------------------------------------------------------------- base and floor
print(flush=True); print("== base and floor (heights along world up, from the table)")


def lowest(shape):
    return min(Vector(v).dot(UP_D) for v in shape.vertices())


print(f"  flat base: d{2 * FOOT_R:.0f} (table at {FOOT_H:.2f}, floor top {FLOOR_TOP:.2f})")
floor = rear - half(UP_D, FLOOR_TOP + 0.3)
d = min(s.distance_to(floor) for s in rs_solids if _rmax(s) > 44)
flag(d > 0.3, f"board (PCB tab, reset button) above the floor / pocket: {d:.2f} mm")
low_all = min(lowest(s) for s in rs_solids)
flag(low_all - FOOT_H > 1.2, f"lowest board part (reset nub) above the table: {low_all - FOOT_H:+.2f} mm")
for n in ("carrier", "speaker", "back_plate"):
    print(f"  {n:12s} lowest point {lowest(allp[n]) - FLOOR_TOP:+.2f} mm above floor top")
for n in ("front_shell", "rear_shell"):
    flag(abs(lowest(parts[n]) - FOOT_H) < 0.05, f"{n} sits on the table")

print(flush=True); print("== ballast and grip pads")
bal = ballast_pocket().volume / 1000
print(f"  ballast pocket {bal:.1f} cm3 (rear shell, {BAL_ARC[0]:.0f}-{BAL_ARC[1]:.0f} deg, below z {BAL_TOP}): steel shot in epoxy "
      f"about {bal * 5.3:.0f} g, tungsten putty about {bal * 10:.0f} g")
flag(bal > 20, "ballast pocket holds more than 20 cm3")
flag(CARRIER_Z0 - BAL_TOP >= 1.5, f"pocket rim {CARRIER_Z0 - BAL_TOP:.1f} mm below the carrier")
for side in ("front", "rear"):
    pad = foot_pad_placed(side)
    o = vol(pad, parts[side + "_shell"])
    br = vol(pad_recess(side), cavity())
    flag(o < 0.01 and br < 0.01, f"{side} grip pad: sits in its recess ({o:.3f} mm3), stands {PAD_T - PAD_RECESS:.1f} mm proud, floor intact ({br:.3f})")

# weight, stability and knob-turn resistance (electronics masses are estimates)
items = [(parts[n].volume / 1000 * d * f, parts[n].center()) for n, d, f in
         (("front_shell", 1.24, .9), ("rear_shell", 1.24, .9), ("back_plate", 1.24, .85), ("ring_base", 1.27, 1.0),
          ("ring_shell", 1.27, 1.0), ("carrier", 1.27, .6), ("spider", 1.27, 1.0))]
items += [(95.0, Vector(0, 0, (CP_PCB_REAR_Z + CP_KNOB_Z[1]) / 2)), (25.0, Vector(0, 0, -1.5)),
          (30.0, prox["speaker"].center()), (20.0, Vector(0, -10, -25))]
bcen = ballast_pocket().center()
for label, extra, mu in (("no ballast, bare base", 0.0, 0.3), ("steel shot ballast + TPU pads", bal * 5.3, 0.8),
                         ("tungsten putty + TPU pads", bal * 10.0, 0.8)):
    its = items + ([(extra, bcen)] if extra else [])
    M = sum(m for m, _ in its)
    cg = Vector(sum(m * c.X for m, c in its) / M, sum(m * c.Y for m, c in its) / M, sum(m * c.Z for m, c in its) / M)
    d = cg - FOOT_C
    h = d.dot(UP_D)
    off = (d - UP_D * h).length
    tip = degrees(atan2(FOOT_R - off, h))
    print(f"  {label:30s} about {M:4.0f} g, centre of mass {h:4.1f} mm up, {off:3.1f} mm off the base centre, tips at {tip:4.1f} deg, "
          f"turning resistance about {M * 9.81 * mu * 0.016:3.0f} mN*m")
    if extra:
        flag(off < FOOT_R - 15 and tip > 25, f"  ballasted clock is stable ({label})")

print(flush=True); print("== mute plunger")
gap = plunger_rest_tip() - RS_MUTE_TIP_R
flag(0.05 < gap < 0.5, f"rest gap to the BUTA nub {gap:.2f} mm")
flag(PLG_TRAVEL >= gap + 0.25 + 0.3 + 0.2, f"cap travel {PLG_TRAVEL} mm covers gap + switch travel + board play")
flag(PLG_Z - PLG_ROD_R < -3.75 + 0.2 and PLG_Z + PLG_ROD_R > -2.20 - 0.2,
     f"rod d{2 * PLG_ROD_R} at z {PLG_Z} covers the nub (z -3.75..-2.20)")
flag(SPLIT_Z - (PLG_Z + PLG_CB_R) >= 1.0, f"counterbore to seam {SPLIT_Z - (PLG_Z + PLG_CB_R):.2f} mm")
nub = radial_box(90, RS_MUTE_TIP_R - 1.0, RS_MUTE_TIP_R, 2.9, -3.75, -2.20)
pressed = Pos(0, -(gap + 0.25), 0) * parts["mute_plunger"]
flag(vol(pressed, nub) > 0.01, "pressed plunger reaches the nub")
flag(vol(parts["mute_plunger"], rear) < 0.01, "plunger slides free in its bore")

# ---------------------------------------------------------------- light ring
print(flush=True); print("== light ring")
z1, z2, z3, z4 = RING_IW_Z
print(f"  knob ring d{2 * CP_KNOB_R:.1f} in the ring bore d{2 * RING_IW_R2:.2f}: radial gap {LG_KNOB_GAP:.2f} mm")
flag(RING_IW_R0 + RING_IW_T < 39.01 - 0.4, f"inner wall foot (r {RING_IW_R0 + RING_IW_T:.2f}) inside the LEDs (r 39.01) by >= 0.4")
flag(RING_SLV_RI > 41.04 + 0.6, f"sleeve (r {RING_SLV_RI:.2f}) outside the LEDs (r 41.04) by >= 0.6")
w_lo = RING_SLV_RI - (RING_IW_R1 + RING_IW_T)
w_hi = RING_SLV_RI - (RING_IW_R2 + RING_IW_T)
print(f"  channel width {w_lo:.2f} mm (z {z2}..{z3}), {w_hi:.2f} mm at the knob (z {z4}..)")
flag(w_hi >= 1.5, "channel at least 1.5 mm wide everywhere")
d = parts["ring_base"].distance_to(parts["spider"]) if vol(parts["ring_base"], parts["spider"]) < 0.01 else 0
v = vol(parts["ring_base"] - zslab(-1, STANDOFF_L + 0.01), parts["spider"])
flag(v < 0.01, f"inner wall clears the spider pads: {v:.3f} mm3")
flag(vol(parts["ring_base"], prox["cp_knob"]) < 0.01 and vol(parts["ring_shell"], prox["cp_knob"]) < 0.01, "ring clears the knob")
flag(RING_BORE_R - RING_SLV_RO >= 0.25, f"front-shell bore -> ring_shell: {RING_BORE_R - RING_SLV_RO:.2f} mm (the front shell turns round it)")
# retention: lifted by more than the collar gap + 0.2, the ring_shell's collar hits the front shell
lift = RING_COLLAR_GAP + 0.2
v = vol(Pos(0, 0, lift) * parts["ring_shell"], parts["front_shell"])
flag(v > 1.0, f"front shell captures the ring_shell (lifted {lift:.1f} mm the collar bites {v:.1f} mm3)")
print(f"  ring stands {RING_PROUD:.1f} mm proud of the sphere (top z {RING_TOP_Z:.2f}); knob exposed "
      f"{CP_KNOB_Z[1] - RING_TOP_Z:.1f} mm (v1: {KNOB_PROUD:.1f})")
flag(CP_KNOB_Z[1] - RING_TOP_Z >= 4.5, "knob stays grippable (>= 4.5 mm exposed)")
flag(vol(parts["ring_shell"], parts["front_shell"]) < 0.01, "ring_shell clears the front shell (mic boots, bore)")
# the shell slides on over the knob from the front once the stack is screwed together
worst = 0.0
for s in SW:
    for st in (prox["cp_knob"], parts["ring_base"] - zslab(RING_TOP_Z - 3, RING_TOP_Z + 1)):
        worst = max(worst, vol(Pos(0, 0, s) * parts["ring_shell"], st))
flag(worst < 0.01, f"ring_shell slides on from the front: max overlap {worst:.3f}")
v = vol(parts["ring_base"], parts["ring_shell"])
flag(0.01 < v < 1.5, f"crush ribs bite the cap's skirt: {v:.2f} mm3")
# the face: the cap overlaps the inner wall's top, so no straight line from the face reaches the channel
flag(RING_CAP_RI <= RING_IW_R2 + 1e-6, f"cap covers the inner wall's top (cap from r {RING_CAP_RI:.2f}, wall from r {RING_IW_R2:.2f})")
flag(RING_IW_R0 + RING_IW_T <= 37.83 - 0.2, f"inner wall foot (r {RING_IW_R0 + RING_IW_T:.2f}) inside the LED capacitors (r 37.83) by >= 0.2: no notches")

print(flush=True); print("== spider vs CrowPanel plug keep-outs")
for (x0, x1, y0, y1) in CP_KEEPOUT_NOM:
    k = Rot(0, 0, CP_ROT_TRIM_DEG) * (Pos((x0 + x1) / 2, (y0 + y1) / 2, 0) *
                                      Box(x1 - x0, y1 - y0, CP_REAR_Z, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    flag(vol(k, parts["spider"]) < 0.01, f"keep-out {x0, x1, y0, y1}")

print(flush=True); print("== speaker")
bb = spk.bounding_box()
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

print(flush=True); print("== screws and inserts (kit: M2 SHCS 10/12/16/20, M3 SHCS 6/8/12/16/20)")
head_z = STANDOFF_L + 1.0
m3_tip = head_z + 12
flag(m3_tip <= CP_STOCK_TIP_Z + 0.1, f"CrowPanel M3x12 tip z {m3_tip:.1f} no deeper than Elecrow's screws ({CP_STOCK_TIP_Z})")
print(f"  CrowPanel M3x12 thread engaged {m3_tip - CP_HUB_THREAD_Z:.1f} mm (Elecrow's own screws: "
      f"{CP_STOCK_TIP_Z - CP_HUB_THREAD_Z:.1f} mm; the hub face is at z {CP_HUB_THREAD_Z}, behind 2 pin tips at z {CP_HUB_FACE_Z})")
tip_clamp = CARRIER_Z0 + CARRIER_CB + M2_CLAMP_LEN
flag(min(tip_clamp, STANDOFF_L + M2_INSERT_L) - STANDOFF_L >= 2.0, f"clamp M2x{M2_CLAMP_LEN:.0f} engaged {min(tip_clamp, STANDOFF_L + M2_INSERT_L) - STANDOFF_L:.1f} mm")
flag(tip_clamp <= STANDOFF_L + SPIDER_T + SPIDER_PILLAR - 0.5, f"clamp screw tip z={tip_clamp:.1f} stays inside the spider pillar")
probe = parts["spider"] & cyl(0.5, STANDOFF_L + 0.5, STANDOFF_L + SPIDER_T + SPIDER_PILLAR + 0.5, *rot2(rs_holes()[0], 0))
flag(probe is None or probe.volume < 1e-4, "spider insert holes are through holes (melt and screw-tip room, >= 2.5 mm rule)")
stack_spk = TPU_WASHER_T * 2 + SPK_EAR_T
boss_top = speaker_boss_top()
hole_bottom = BACK_Z - BACK_T + SPK_HOLE_SKIN
spk_tip = boss_top + stack_spk - SPK_SCREW_L
flag(spk_tip - hole_bottom >= SCREW_MARGIN, f"speaker M2x{SPK_SCREW_L:.0f}: {spk_tip - hole_bottom:.1f} mm of hole below the tip "
     f"(was 0.9), engaged {min(SPK_SCREW_L - stack_spk, M2_INSERT_L):.1f} mm")
flag(SPK_HOLE_SKIN >= 1.0, f"speaker insert hole leaves {SPK_HOLE_SKIN:.1f} mm on the outer face")
hxp = USB_HOLE_PITCH / 2
wall_wd = min(hxp - M2_INSERT_D / 2 - USB_PAD_X[0], USB_PAD_X[1] - hxp - M2_INSERT_D / 2)
flag(wall_wd >= 1.3, f"USB-C insert: pad wall beside the insert {wall_wd:.2f} mm, below it {USB_HOLE_Z - M2_INSERT_D / 2 + BACK_T:.1f} mm")
flag(hxp - USB_BOSS_D / 2 - 0.5 > 8.94 / 2, f"USB-C pads clear the socket body (boss edge |x| {hxp - USB_BOSS_D / 2:.2f} vs 4.47)")
usb_in = USB_SCREW_L - USB_PCB[2]
flag(usb_in - (USB_WALL_T - M2_INSERT_L) >= M2_INSERT_L and usb_in > USB_WALL_T, f"USB-C M2x{USB_SCREW_L:.0f}: {usb_in:.1f} mm through the pad, "
     f"full {M2_INSERT_L:.0f} mm insert engaged, tip {usb_in - USB_WALL_T:.1f} mm past it")
d_spk = scr_all.distance_to(spk)
flag(d_spk >= 1.0, f"USB-C screw tips -> speaker: {d_spk:.2f} mm")
plug_room = spk.bounding_box().min.Y - usb_y_top
flag(plug_room >= 14.0, f"USB-C board face -> speaker {plug_room:.1f} mm (JST plug on the board + its lead bend need ~14)")
bp_only = parts["back_plate"]
key = None
for sx in (-1, 1):                                 # bench: plate on its own, hex key and screw come in from the rim
    hx = sx * hxp
    k = Pos(hx, usb_y_back - 2.0, BACK_Z + USB_HOLE_Z) * Rot(90, 0, 0) * Cylinder(1.1, 60.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    feed = Pos(hx, usb_y_back - 0.01, BACK_Z + USB_HOLE_Z) * Rot(90, 0, 0) * Cylinder(2.1, USB_SCREW_L + 6.0,
                                                                                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    key = (k + feed) if key is None else key + k + feed
v_key = vol(key, bp_only)
flag(v_key < 0.01, f"hex key and screw reach both USB-C screws straight in from the plate's rim ({v_key:.3f} mm3)")
print(f"  inserts: M2 (hole d{M2_INSERT_D}, {INSERT_CHAMFER} mm lead-in): spider 3 (through), speaker bosses 2, "
      f"USB-C pads 2 (pressed in from the pads' speaker-side face)")

print(flush=True); print("== mic channels (port -> outside, all 4 diagonals)")
fs = parts["front_shell"]
others = [p for n, p in parts.items() if n != "front_shell"] + [prox["cp_knob"], prox["cp_pcb"]]
rs_front = [s for s in rs_solids if s is not pcb and s.bounding_box().max.Z > 0.0]
open_ok, wall_ok, voids = True, True, []
for ang in (45, 135, 225, 315):
    core = mic_channel(ang, -0.15) - zslab(-5, 0.02)            # air path from the PCB face outward
    blocked = vol(core, fs) + sum(vol(core, p) for p in others) + sum(vol(core, q) for q in rs_front)
    ring = (mic_channel(ang, 0.8) - mic_channel(ang)) & sector(
        [(RS_MIC_R + 1.5, SPLIT_Z + 0.01), (R_IN - 0.5, SPLIT_Z + 0.01), (R_IN - 0.5, 20), (RS_MIC_R + 1.5, 20)],
        ang - 12, ang + 12)                                     # inside the boot (below z SPLIT_Z is the gasket gap)
    frac = vol(ring, fs) / ring.volume                          # boot material round the bore (no break-through)
    voids.append(vol(mic_channel(ang, 0.5), fs))
    print(f"  {ang:3d} deg: blocked {blocked:.3f} mm3, boot wall >= 0.8 mm over {frac * 100:.1f} % of the bore")
    open_ok &= blocked < 0.01
    wall_ok &= frac > 0.98
flag(open_ok, "mic channels open from the port to the outside (front shell cut, no part or board component in the way)")
flag(wall_ok, "boot wall at least 0.8 mm round each bore (no break-through into the cavity)")
flag(max(voids) - min(voids) < 0.05, f"the 4 channels are identical (shell material round them: spread {max(voids) - min(voids):.3f} mm3)")
L = MIC_CH_Z + r_out_at(MIC_CH_Z) - RS_MIC_R
print(f"  centreline {L:.1f} mm (quarter-wave about {343e3 / (4 * (L + 0.85 * MIC_BORE / 2)) / 1000:.1f} kHz); "
      f"pointed roofs (cone + {degrees(atan2(MIC_ROOF_TAN, 1)):.0f} deg ridge), ceiling >= 45 deg everywhere in the face-up print")
print(flush=True); print("== mic channel length (mm):", round(r_out_at(MIC_CH_Z) - RS_MIC_R, 1))
print("== depth: CrowPanel rear -> spider top:", round(CP_REAR_Z - (STANDOFF_L + SPIDER_T), 2), "mm")
print(f"== size: d{2 * SPHERE_R:.0f} sphere, {SPHERE_R + CEN.dot(UP_D) - FOOT_H:.1f} mm tall, "
      f"{CP_KNOB_Z[1] - (BACK_Z - BACK_T):.1f} mm deep incl. knob, base d{2 * FOOT_R:.0f}")
print("RESULT:", "PASS" if not bad else f"{bad} problem(s)")
