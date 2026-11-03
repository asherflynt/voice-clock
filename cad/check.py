"""Interference / assembly checks for voice_clock.py (D frame)."""
import itertools
from voice_clock import *

parts = {n: f() for n, f in PRINT_PARTS.items() if n not in ("tpu_washers", "insert_coupon")}
prox = proxies()
allp = {**parts, **prox}

# contacts that are intended (touching faces, screws through holes are not modelled)
ALLOWED = {
    frozenset({"spider", "board_spacers"}), frozenset({"board_spacers", "rs_pcb"}),
    frozenset({"carrier", "rs_pcb"}), frozenset({"carrier", "rs_xiao"}), frozenset({"carrier", "front_shell"}),
    frozenset({"carrier", "rear_shell"}), frozenset({"front_shell", "rear_shell"}),
    frozenset({"rear_shell", "back_plate"}), frozenset({"light_guide", "rs_pcb"}),
    frozenset({"light_guide", "front_shell"}), frozenset({"spider", "cp_pcb"}),
    frozenset({"cp_knob", "cp_glass"}), frozenset({"cp_knob", "cp_housing"}),
    frozenset({"cp_pcb", "cp_conn"}), frozenset({"cp_housing", "cp_pcb"}),
    frozenset({"rs_pcb", "rs_leds"}), frozenset({"rs_pcb", "rs_xiao"}),
    frozenset({"back_plate", "speaker"}), frozenset({"mute_plunger", "front_shell"}),
}
bad = 0
print("== pairwise overlap (mm^3)")
for a, b in itertools.combinations(allp, 2):
    try:
        v = (allp[a] & allp[b]).volume
    except Exception as e:
        v = float("nan")
    if v > 0.01:
        tag = "ok (contact)" if frozenset({a, b}) in ALLOWED and v < 1.0 else "CLASH"
        if tag == "CLASH":
            bad += 1
        print(f"  {a:14s} x {b:14s} {v:9.3f}  {tag}")

print("== insertion sweeps into front shell (from behind)")
fs = parts["front_shell"]
board_sweep = cyl(RS_R, -40, 0) + (prox["rs_pcb"] & zslab(-RS_T, 0))
for ang in (90, 270):  # edge buttons
    board_sweep = board_sweep + Rot(0, 0, ang) * Pos(RS_R + 1.8, 0, -40) * Box(3.6, 6, 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
v = (board_sweep & fs).volume
print(f"  reSpeaker path vs front shell: {v:.3f}", "CLASH" if v > 0.01 else "ok")
bad += v > 0.01
lg_sweep = cyl(LG_RO, -40, LG_STEP_Z - 1.5)
v = (lg_sweep & fs).volume
print(f"  light-guide path vs front shell: {v:.3f}", "CLASH" if v > 0.01 else "ok")
bad += v > 0.01

print("== floor / foot")
for n in ("rs_pcb", "carrier", "speaker", "back_plate"):
    bb_min = min(Vector(v).dot(UP_D) for v in allp[n].vertices())
    print(f"  {n:12s} lowest point {bb_min - FLOOR_TOP:+.2f} mm above floor top")

print("== spider vs CrowPanel plug keep-outs")
n_sp = len(parts["spider"].solids())
print(f"  spider is {n_sp} solid(s)", "ok" if n_sp == 1 else "ARM DETACHED")
bad += n_sp != 1
for (x0, x1, y0, y1) in CP_KEEPOUT:
    k = Pos((x0 + x1) / 2, (y0 + y1) / 2, 0) * Box(x1 - x0, y1 - y0, CP_REAR_Z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    v = (k & parts["spider"]).volume
    print(f"  keep-out {x0,x1,y0,y1}: {v:.3f}", "CLASH" if v > 0.01 else "ok")
    bad += v > 0.01

print("== speaker")
spk = prox["speaker"]; bp = parts["back_plate"]; bb = spk.bounding_box()
face_gap = bb.min.Z - BACK_Z
print(f"  diaphragm face -> back plate gap {face_gap:.2f} mm (foam {SPK_GASKET} compressed)")
bad += abs(face_gap - SPK_GASKET) > 0.05
for sxn in (-1, 1):
    bx = sxn * SPK_EAR_PITCH / 2
    probe = cyl(0.4, BACK_Z, -20, bx, SPK_CY + 2.5)
    ear = spk & probe
    boss = bp & probe
    gap = ear.bounding_box().min.Z - boss.bounding_box().max.Z
    print(f"  ear at x={bx:+.2f}: ear-to-boss gap {gap:.2f} mm (TPU washer {TPU_WASHER_T})")
    bad += abs(gap - TPU_WASHER_T) > 0.05
for n in ("back_plate", "rear_shell", "carrier"):
    d = spk.distance_to(parts[n])
    print(f"  speaker clearance to {n}: {d:.2f} mm")
    bad += d < 0.5
print("== heat-set insert holes fully enclosed (>= 0.8 mm wall, entry face open)")
def insert_ok(part, x, y, z_entry, depth, d, direction=+1, name=""):
    wall = 0.8
    z0, z1 = (z_entry + 0.05, z_entry + depth + wall) if direction > 0 else (z_entry - depth - wall, z_entry - 0.05)
    shell = cyl(d / 2 + wall, z0, z1, x, y) - cyl(d / 2, z0 - 1, z_entry + depth * direction, x, y) if direction > 0 else None
    missing = (shell - part).volume
    print(f"  {name:28s} missing wall {missing:6.2f} mm3", "ok" if missing < 0.5 else "BREAKS OUT")
    return missing < 0.5
for ang in SHELL_LUG_ANG:
    bad += not insert_ok(parts["front_shell"], *polar(SHELL_LUG_R, ang), CARRIER_FRONT, M3_INSERT_DEPTH, M3_INSERT_D, name=f"front lug {ang:.0f} (M3)")
for ang in REAR_RIB_ANG:
    bad += not insert_ok(parts["carrier"], *polar(REAR_RIB_R, ang), SPLIT_Z, CARRIER_INSERT_DEPTH, M3_INSERT_D, name=f"carrier boss {ang:.0f} (M3)")
for ang in BACK_LUG_ANG:
    bad += not insert_ok(parts["rear_shell"], *polar(BACK_SCREW_R, ang), BACK_Z, M3_INSERT_DEPTH, M3_INSERT_D, name=f"back lug {ang:.0f} (M3)")

print("== screws (all from the user's kits) - thread engaged in the insert")
tip_clamp = SPLIT_Z + CARRIER_CB + M2_CLAMP_LEN
rows = [
    ("CrowPanel hub   M3x12 SHCS", 12 - (CP_HUB_FACE_Z - (STANDOFF_L + 1.0)), "stock screw: 3.5"),
    (f"clamp           M2x{M2_CLAMP_LEN:.0f} SHCS", min(tip_clamp, STANDOFF_L + M2_INSERT_L) - STANDOFF_L,
     f"tip at z={tip_clamp:.1f}, insert {STANDOFF_L:.0f}..{STANDOFF_L + M2_INSERT_L:.0f}, hole to {STANDOFF_L + M2_INSERT_L + 0.3 + SPIDER_PILLAR:.1f}"),
    ("carrier rim     M3x6 SHCS", min(6 - (CARRIER_T - RIM_CB[1]), 4.0), "insert 4 long"),
    ("rear rib        M3x8 button", min(8 - 4.0, 4.0), ""),
    ("back plate      M3x8 button", min(8 - BACK_T, 4.0), f"{8 - BACK_T - 4.0:.1f} mm past insert, hole {M3_INSERT_DEPTH}"),
    ("speaker ear     M2x10 SHCS", min(10 - (TPU_WASHER_T * 2 + SPK_EAR_T), M2_INSERT_L),
     f"{10 - (TPU_WASHER_T * 2 + SPK_EAR_T) - M2_INSERT_L:.1f} mm past insert, hole {M2_INSERT_DEPTH}"),
]
for n, e, note in rows:
    print(f"  {n:28s} {e:4.1f}  {note}")
    bad += e < 2.0
bad += tip_clamp > STANDOFF_L + M2_INSERT_L + 0.3 + SPIDER_PILLAR - 0.6
bad += 10 - (TPU_WASHER_T * 2 + SPK_EAR_T) > M2_INSERT_DEPTH - 0.3
bad += 8 - BACK_T > M3_INSERT_DEPTH - 0.3
print("== screw heads clear the rear shell")
for ang in SHELL_LUG_ANG:
    x, y = polar(SHELL_LUG_R, ang)
    head = cyl(2.75, SPLIT_Z - (3.0 - RIM_CB[1]), SPLIT_Z, x, y)
    v = (head & parts["rear_shell"]).volume
    d = head.distance_to(parts["rear_shell"])
    print(f"  rim M3 head at {ang:.0f}: overlap {v:.3f} mm3, gap {d:.2f} mm", "ok" if v < 0.01 else "CLASH")
    bad += v > 0.01
print(f"== USB-C: plate left at the recess {BACK_T - USB_RECESS[2]:.1f} mm (receptacle lip ~1 mm reaches the outer face)")

print("== mic channel length (mm):", round(sqrt(SPHERE_R**2 - (MIC_CH_Z - C_Z)**2) - RS_MIC_R, 1))
print("== depth: CrowPanel rear -> spider top:", round(CP_REAR_Z - (STANDOFF_L + SPIDER_T), 2), "mm")
print("RESULT:", "PASS" if not bad else f"{bad} problem(s)")
