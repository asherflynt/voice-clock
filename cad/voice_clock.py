"""Voice Clock enclosure - parametric build123d model.

Frame "D" (device frame), used for everything below:
  origin = centre of the reSpeaker PCB *front* face (LED / mic-port side)
  +Z     = toward the viewer (out of the display)
  +Y     = display "up" (before the 15 deg tilt)
  +X     = right, as seen from the front
The whole device is tilted face-up by TILT about X; world "up" in D is UP_D.

Run:  .venv/bin/python voice_clock.py          -> out/ (STL, STEP, checks)
Every dimension marked VERIFY is from vendor CAD/drawings, not calipers yet.
"""
from math import cos, sin, radians, sqrt, atan2, degrees
from pathlib import Path
from build123d import (Sphere, Cylinder, Cone, Box, Pos, Rot, Plane, Polygon,
                       Location, Vector, Align, extrude, export_stl, export_step,
                       Compound, Part)

OUT = Path(__file__).parent / "out"

# ---------------------------------------------------------------- parameters
SPHERE_R      = 60.0      # outer radius (OD 120)
WALL          = 2.5
FACE_R        = 44.0      # flat face OD 88
FACE_Z        = 35.0      # face plane, board-front + 35
TILT          = 15.0      # deg, face tilted up
FOOT_R        = 21.0      # flat foot OD 42 (lets the 6 o'clock button clear the floor)
FLOOR         = 2.5
SPLIT_Z       = -14.5     # front / rear shell split
BACK_Z        = -45.7     # rear shell ends / back plate inner face
BACK_T        = 2.5       # back plate thickness

# reSpeaker XVF3800 (drawing frame: XIAO at 12 o'clock)          VERIFY hole d
RS_R          = 50.0      # bare PCB radius (edge parts to 53.6)
RS_EDGE_R     = 53.6
RS_T          = 1.2
RS_BACK_PARTS = 7.9       # tallest back-side part below PCB front (6.7 + 1.2)
RS_HOLES_DRAW = [(-21.35, 24.5), (21.35, 24.5), (0.0, -34.0)]
RS_ROT        = -90.0     # deg CCW. Mute ("A") is at 9 o'clock seen from the LED side with the
                          # XIAO at the top (confirmed on hardware 1 Nov 2026); -90 puts it at 12.
RS_MIC_R      = 46.67     # mics on the 45 deg diagonals
RS_LED_R      = 40.0
RS_BTN_Z      = -0.6      # side-button centre height (VERIFY)

# CrowPanel 2.1 (from 00-irad-21.stp; C.y = view axis, knob front at C.y=12.4)
KNOB_PROUD    = 7.0
CP_Z0         = FACE_Z + KNOB_PROUD - 12.4     # D.z = C.y + CP_Z0  (= 29.6)
CP_KNOB_R     = 39.5
CP_HOUSING_R  = 38.95
CP_HUB_FACE_Z = -15.0 + CP_Z0                  # 14.6  rear face of Ø16.8 hub
CP_PCB_REAR_Z = -14.5 + CP_Z0                  # 15.1
CP_REAR_Z     = -21.0 + CP_Z0                  # 8.6   connectors end here
CP_SCREWS     = [(-5.15, -2.98), (5.15, -2.98), (0.0, 5.95)]   # D x,y (M3)
# rear 4-pin connector plug keep-outs (D x0,x1,y0,y1)
CP_KEEPOUT    = [(1.6, 8.5, 14.1, 17.8), (-8.5, -1.6, 14.1, 17.8),
                 (10.6, 14.4, -3.5, 3.5)]

# light guide / bezel
LG_RI         = CP_KNOB_R + 0.75               # 40.25 (0.75 knob gap)
LG_RO_FRONT   = 42.5
LG_RO         = 44.0
LG_STEP_Z     = 29.0
SHELL_BORE_R  = LG_RO_FRONT + 0.2
LG_LIP_RI     = 38.6
LG_LED_POCKET = (38.6, 41.4, 1.6)              # ri, ro, height over LEDs
NOTCH_ANG     = -15.0 if RS_ROT > 0 else 195.0 # cable notch (between LEDs)
NOTCH_W, NOTCH_H = 4.5, 4.0

# spider bracket + reSpeaker clamp (hardware = what's in the user's two kits:
#   inserts M2x3xOD3.2, M3x4xOD4.2; screws M2 SHCS 10/12/16/20, M3 SHCS 6/8/12/16/20,
#   M3 button 8/12/16/20; no countersunk, no standoffs)
# reSpeaker holes are d2.2 -> M2 (measured from Seeed's 1:1 drawing).
# Clamp: carrier boss -> board -> printed spacer -> M2 insert in the spider's underside,
# one M2 x 20 per point from the carrier back.
STANDOFF_L    = 5.0       # printed board spacer height (board front -> spider plate)
SPACER_OD     = 6.5
SPIDER_T      = 3.0
SPIDER_PILLAR = 1.5       # boss on top of the plate: closes the insert hole, room for the tip
SPIDER_HUB_R  = 9.6
ARM_W         = 7.0
M2_CLR        = 2.4
M3_CLR        = 3.3
M2_CLAMP_LEN  = 20.0
CARRIER_CB    = 2.0       # M2 SHCS head (d3.8 x 2) sits flush in the carrier boss
# -> tip at -14.5 + 2.0 + 20 = +7.5: 2.5 mm into the 3 mm spider insert (z 5..8)

# carrier
CARRIER_T     = 2.5
CARRIER_FRONT = SPLIT_Z + CARRIER_T            # -12.0
SHELL_LUG_ANG = [120.0, 240.0, 330.0]
SHELL_LUG_R   = 53.4      # inward so the M3 x 6 SHCS heads clear the rear-shell wall
RIM_CB        = (6.0, 1.2)  # carrier-rim counterbore for M3 x 6 SHCS (d5.5 x 3 head)
REAR_RIB_ANG  = [0.0, 150.0, 270.0]    # clear of clamp heads (41/180/319), rim heads (120/240/330)
                                        # and the back-plate lugs (90/210/330) on the driver path
REAR_RIB_R    = 38.0      # inside the back opening -> straight driver access
# heat-set insert holes for the user's kit (OD - ~0.45). insert_coupon brackets these.
M3_INSERT_D   = 4.0       # 3DZWMAN D3 for M3 (OD 4.2 -> hole 4.0, min wall W=1.6)
M3_INSERT_DEPTH = 6.5     # inserts are 4 long; the extra depth is screw-tip room
CARRIER_INSERT_DEPTH = 5.0  # carrier bosses can't grow (board parts)
M2_INSERT_L   = 3.0       # M2 x 3 x OD3.2

# mic channels
MIC_BORE      = 2.0
MIC_LUG_Z0    = 1.1       # lug underside (1/16" = 1.6 mm foam gasket, ~30% squeeze)
MIC_CH_Z      = 3.0

# back plate
BACK_LUG_ANG  = [90.0, 210.0, 330.0]
BACK_SCREW_R  = 37.5
# speaker: 4428 3 W 8 ohm, from ../decive files/speaker_4428_3W8R.step
SPK_STEP      = Path(__file__).parent.parent / "decive files" / "speaker_4428_3W8R.step"
SPK_BODY      = (28.2, 31.0, 15.3)             # body x (ear axis), y, z (back -> diaphragm face)
SPK_EAR_PITCH = 36.7                           # ear hole c-c, holes d2.4 -> M2
SPK_EAR_T     = 2.4
SPK_EAR_FROM_FACE = 15.3 - 6.9                 # diaphragm face -> ear face nearest it (8.4)
SPK_CONE_R    = 13.0                           # diaphragm recess radius
SPK_CY        = 0.0                            # speaker centre, D y (lead exits toward +y)
SPK_GASKET    = 1.1                            # 1/16" (1.6 mm) foam squeezed to 1.1
TPU_WASHER_T  = 1.0                            # isolation washer, one each side of each ear
M2_INSERT_D   = 2.9                            # 3DZWMAN D3 for M2 (OD 3.0 -> hole 2.9, min wall W=1.3)
M2_INSERT_DEPTH = 6.5                          # M2 x 10 passes 2.6 mm beyond the insert
# USB-C inlet: 6-pin breakout with 5.1k CC resistors, measured 3 Nov 2026:
# PCB 21.96 x 13.11 x 1.61, socket on the top face centred on the long (USB) edge,
# socket 3.30 tall, opening overhangs that edge by 1.48. Two holes near the USB edge:
# 18.95 outer-to-outer, hole edge 1.61 from the USB edge (hole d not measured, ~2.5).
# The board stands on its USB edge on the plate; the socket goes through the slot;
# 2x M2 x 10 thread through the board holes into oval holes in a backing wall.
USB_CY        = -27.0
USB_SLOT      = (9.4, 3.6)                     # socket shell ~8.94 x 3.30
USB_RECESS    = (13.5, 8.0, 1.6)               # outside, for the plug overmould
USB_PCB       = (21.96, 13.11, 1.61)           # length (along the USB edge), height, thickness
USB_SOCKET_H  = 3.30
USB_HOLE_D    = 2.5                            # estimate
USB_HOLE_PITCH= 18.95 - USB_HOLE_D             # centre-to-centre (~16.45)
USB_HOLE_Z    = 1.61 + USB_HOLE_D / 2          # hole centre above the plate's inner face

# ---------------------------------------------------------------- derived
C_Z    = FACE_Z - sqrt(SPHERE_R**2 - FACE_R**2)          # sphere centre z (-5.8)
R_IN   = SPHERE_R - WALL
UP_D   = Vector(0, cos(radians(TILT)), sin(radians(TILT)))
CEN    = Vector(0, 0, C_Z)
FOOT_H = CEN.dot(UP_D) - sqrt(SPHERE_R**2 - FOOT_R**2)   # foot plane (along UP_D)
FLOOR_TOP = FOOT_H + FLOOR


def polar(r, ang):
    return (r * cos(radians(ang)), r * sin(radians(ang)))


def rs_holes():
    out = []
    for x, y in RS_HOLES_DRAW:
        a = radians(RS_ROT)
        out.append((x * cos(a) - y * sin(a), x * sin(a) + y * cos(a)))
    return out


def half(n, d, size=800):
    """Half-space {p : p.n >= d}."""
    n = Vector(n).normalized()
    return Plane(origin=n * d, z_dir=n) * Box(size, size, size,
                                              align=(Align.CENTER, Align.CENTER, Align.MIN))


def zslab(z0, z1, size=800):
    return Pos(0, 0, z0) * Box(size, size, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cyl(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def radial_cyl(r, ang, r0, r1, z):
    """Cylinder along the radial direction `ang` (deg) at height z."""
    c = Cylinder(r, r1 - r0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    c = Rot(0, 90, 0) * c                       # axis now +X
    return Rot(0, 0, ang) * (Pos(r0, 0, z) * c)


def radial_cone(r1, r2, ang, r0, r1_pos, z):
    """Truncated cone along radial direction `ang` (deg) at height z."""
    c = Cone(r1, r2, r1_pos - r0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    c = Rot(0, 90, 0) * c
    return Rot(0, 0, ang) * (Pos(r0, 0, z) * c)


def rz_profile(pts, ang, half_w):
    """Polygon in the (r, z) half-plane, extruded +-half_w tangentially, rotated to ang."""
    f = Plane.XZ * Polygon(*pts, align=None)
    return Rot(0, 0, ang) * extrude(f, amount=half_w, both=True)


def sphere_out():
    return Pos(*CEN) * Sphere(SPHERE_R)


def sphere_in():
    return Pos(*CEN) * Sphere(R_IN)


def above_floor(clear=0.3):
    return half(UP_D, FLOOR_TOP + clear)


def body_envelope():
    return sphere_out() & half(UP_D, FOOT_H)


def cavity():
    return sphere_in() & half(UP_D, FLOOR_TOP)


# ---------------------------------------------------------------- parts
def front_shell():
    outer = body_envelope() & zslab(SPLIT_Z, FACE_Z)
    shell = outer - cavity()

    # collar around the light guide (gives the bezel a real bore + seat cone)
    collar = cyl(52, 27.0, FACE_Z) & sphere_out()
    shell = shell + collar
    bore = cyl(SHELL_BORE_R, LG_STEP_Z, FACE_Z + 1) + \
        Pos(0, 0, 27.0) * Cone(SHELL_BORE_R + (LG_STEP_Z - 27.0) + 0.0, SHELL_BORE_R,
                               LG_STEP_Z - 27.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shell = shell - bore - cyl(LG_RO + 0.25, 0, 27.0)

    env = body_envelope()
    # mic boots: wedge lugs on the diagonals, L-shaped channel
    for ang in (45, 135, 225, 315):
        lug = rz_profile([(LG_RO + 0.5, MIC_LUG_Z0), (SPHERE_R + 1, MIC_LUG_Z0),
                          (SPHERE_R + 1, MIC_LUG_Z0 + 20), (LG_RO + 0.5, MIC_LUG_Z0 + 4.5)], ang, 4.5)
        shell = shell + (lug & env)
    for ang in (45, 135, 225, 315):
        x, y = polar(RS_MIC_R, ang)
        shell = shell - cyl(MIC_BORE / 2, -1, MIC_CH_Z + MIC_BORE / 2, x, y)
        shell = shell - radial_cyl(MIC_BORE / 2, ang, RS_MIC_R, SPHERE_R + 5, MIC_CH_Z)

    # carrier lugs with M2.5 heat-set inserts (board edge must pass r > RS_R)
    for ang in SHELL_LUG_ANG:
        lug = rz_profile([(RS_R + 0.6, CARRIER_FRONT), (SPHERE_R + 1, CARRIER_FRONT),
                          (SPHERE_R + 1, CARRIER_FRONT + 17), (RS_R + 0.6, CARRIER_FRONT + 8.0)], ang, 4.5)
        shell = shell + (lug & env & zslab(CARRIER_FRONT, FACE_Z))
        x, y = polar(SHELL_LUG_R, ang)
        shell = shell - cyl(M3_INSERT_D / 2, CARRIER_FRONT - 1, CARRIER_FRONT + M3_INSERT_DEPTH, x, y)

    # 1 mm relief groove in the floor for the 6 o'clock side button on insertion
    groove = Pos(0, -RS_R - 8, SPLIT_Z - 1) * Box(9, 16, (RS_BTN_Z - 4) - SPLIT_Z + 1,
                                                  align=(Align.CENTER, Align.CENTER, Align.MIN))
    shell = shell - (groove & half(UP_D, FLOOR_TOP - 1.0))

    # mute plunger bore at 12 o'clock + counterbore on the outside
    shell = shell - radial_cyl(2.2, 90, RS_R, SPHERE_R + 3, RS_BTN_Z)
    shell = shell - radial_cyl(3.8, 90, SPHERE_R - 1.6, SPHERE_R + 3, RS_BTN_Z)
    return shell


def rear_shell():
    outer = body_envelope() & zslab(BACK_Z, SPLIT_Z)
    shell = outer - cavity() - cyl(SPHERE_R, BACK_Z - 5, BACK_Z + 0.001)  # (open back)
    env = body_envelope() & zslab(BACK_Z, SPLIT_Z)
    # ribs reaching in to r=REAR_RIB_R; M2.5 screws go straight in through the
    # open back into heat-set inserts in the carrier
    for ang in REAR_RIB_ANG:
        rib = rz_profile([(REAR_RIB_R - 4, SPLIT_Z), (SPHERE_R + 1, SPLIT_Z),
                          (SPHERE_R + 1, SPLIT_Z - 40), (REAR_RIB_R - 4, SPLIT_Z - 4.0)], ang, 4.5)
        shell = shell + (rib & env)
        x, y = polar(REAR_RIB_R, ang)
        shell = shell - cyl(M3_CLR / 2, SPLIT_Z - 10, SPLIT_Z + 1, x, y)
        shell = shell - (cyl(3.2, BACK_Z - 5, SPLIT_Z - 4.0, x, y) & sphere_in())   # head + driver path
    for ang in BACK_LUG_ANG:                # back-plate lugs, M3 inserts
        lug = rz_profile([(BACK_SCREW_R - 4, BACK_Z), (SPHERE_R, BACK_Z),
                          (SPHERE_R, BACK_Z + 12), (BACK_SCREW_R - 4, BACK_Z + 8)], ang, 5)
        shell = shell + (lug & env)
        x, y = polar(BACK_SCREW_R, ang)
        shell = shell - cyl(M3_INSERT_D / 2, BACK_Z - 1, BACK_Z + M3_INSERT_DEPTH, x, y)
    # wire exit is through the back plate; nothing else here
    return shell


def back_plate():
    plate = body_envelope() & zslab(BACK_Z - BACK_T, BACK_Z)
    for ang in BACK_LUG_ANG:                # countersunk M3
        x, y = polar(BACK_SCREW_R, ang)
        plate = plate - cyl(M3_CLR / 2, BACK_Z - 5, BACK_Z + 1, x, y)
    # speaker grille: hex hole field inside the diaphragm circle
    pitch, j = 3.0, 0
    gr = SPK_CONE_R - 1.5
    y = -gr
    while y <= gr + 1e-6:
        x = -gr + ((pitch / 2) if j % 2 else 0.0)
        while x <= gr + 1e-6:
            if sqrt(x * x + y * y) <= gr - 0.9:
                plate = plate - cyl(0.9, BACK_Z - BACK_T - 1, BACK_Z + 1, x, SPK_CY + y)
            x += pitch
        y += pitch * 0.866
        j += 1
    # ear bosses with M2 inserts; top sits one TPU washer below the ear
    boss_top = BACK_Z + SPK_GASKET + SPK_EAR_FROM_FACE - TPU_WASHER_T
    for sxn in (-1, 1):
        bx = sxn * SPK_EAR_PITCH / 2
        plate = plate + cyl(3.4, BACK_Z, boss_top, bx, SPK_CY)
        plate = plate - cyl(M2_INSERT_D / 2, boss_top - M2_INSERT_DEPTH, boss_top + 1, bx, SPK_CY)
    # USB-C inlet: slot + outside overmould recess; board stands on edge behind the slot
    rx, ry, rd = USB_RECESS
    plate = plate - Pos(0, USB_CY, BACK_Z - 2) * Box(*USB_SLOT, 6)
    plate = plate - Pos(0, USB_CY, BACK_Z - BACK_T - 0.01) * Box(rx, ry, rd, align=(Align.CENTER, Align.CENTER, Align.MIN))
    L, Hb, T = USB_PCB
    y_pcb_top = USB_CY - USB_SOCKET_H / 2              # PCB face carrying the socket
    y_pcb_bot = y_pcb_top - T - 0.15                   # 0.15 mm fit clearance
    wall_t, wall_h = 4.0, 9.0
    wall = Pos(0, y_pcb_bot - wall_t / 2, BACK_Z) * Box(L + 2 * 2.2, wall_t, wall_h,
                                                        align=(Align.CENTER, Align.CENTER, Align.MIN))
    plate = plate + wall
    for sx in (-1, 1):                                 # end stops locate the board's length
        xs = sx * (L / 2 + 0.2 + 1.0)
        plate = plate + Pos(xs, (y_pcb_bot + y_pcb_top) / 2 + 0.5, BACK_Z) * Box(2.0, T + 1.2, 6.0,
                                                                                align=(Align.CENTER, Align.CENTER, Align.MIN))
    for sx in (-1, 1):                                 # oval M2 holes through the wall (self-tapping)
        hx = sx * USB_HOLE_PITCH / 2
        oval = Pos(hx, y_pcb_bot - wall_t / 2, BACK_Z + USB_HOLE_Z) * Rot(90, 0, 0) * \
            (Box(0.7, 1.8, wall_t + 2) + Pos(-0.35, 0, 0) * Cylinder(0.9, wall_t + 2) + Pos(0.35, 0, 0) * Cylinder(0.9, wall_t + 2))
        plate = plate - oval
    # zip-tie anchor for the speaker lead
    ay = SPK_CY + SPK_BODY[1] / 2 + 10.5
    plate = plate + Pos(0, ay, BACK_Z + 2) * Box(8, 4, 4)
    plate = plate - Pos(0, ay, BACK_Z + 2.4) * Box(10, 2.0, 1.6)
    return plate


def light_guide():
    lg = cyl(LG_RO_FRONT, LG_STEP_Z, FACE_Z) + cyl(LG_RO, 0.0, LG_STEP_Z - 1.5)
    lg = lg + Pos(0, 0, LG_STEP_Z - 1.5) * Cone(LG_RO, LG_RO_FRONT, 1.5,
                                                align=(Align.CENTER, Align.CENTER, Align.MIN))
    lg = lg - cyl(LG_RI, -1, FACE_Z + 1)
    # inward lip over the LEDs (45 deg underside so it prints face-down)
    # (cone: thin at the bore, full at the wall, so the lip is self-supporting
    #  when the guide prints face-down)
    zl = LG_LED_POCKET[2]
    lip = cyl(LG_RI + 0.01, zl, zl + 2.0) - \
        Pos(0, 0, zl) * Cone(LG_LIP_RI, LG_RI + 0.01, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    lg = lg + lip
    lg = lg - (cyl(LG_LED_POCKET[1], -1, LG_LED_POCKET[2]) - cyl(LG_LED_POCKET[0], -2, LG_LED_POCKET[2] + 1))
    # cable notch
    nx, ny = polar(LG_RI + 2, NOTCH_ANG)
    lg = lg - Rot(0, 0, NOTCH_ANG) * Pos(LG_RI + 2, 0, NOTCH_H / 2 - 0.5) * Box(12, NOTCH_W, NOTCH_H + 1)
    return lg


def spider():
    z0, z1 = STANDOFF_L, STANDOFF_L + SPIDER_T
    sp = cyl(SPIDER_HUB_R, z0, CP_HUB_FACE_Z)          # boss up to the CrowPanel hub
    sp = sp + cyl(SPIDER_HUB_R + 1.5, z0, z1)
    for (x, y) in rs_holes():
        ang = degrees(atan2(y, x))
        r = sqrt(x * x + y * y)
        sp = sp + cyl(4.0, z0, z1, x, y)
        sp = sp + cyl(3.5, z1, z1 + SPIDER_PILLAR, x, y)   # closes the insert hole
        path = _route_arm((x, y))
        clr = min(_seg_box_dist(p, q, bx) for p, q in zip(path[:-1], path[1:]) for bx in CP_KEEPOUT)
        w = min(ARM_W, 2 * (clr - 1.0) - 0.1)          # narrow an arm that squeezes between plugs
        assert w >= 5.0, f"spider arm too narrow ({w:.1f} mm)"
        for mid in path[1:-1]:
            sp = sp + cyl(w / 2, z0, z1, *mid)
        for a, b in zip(path[:-1], path[1:]):
            sp = sp + _bar(a, b, w, z0, z1)
        sp = sp - cyl(M2_INSERT_D / 2, z0 - 1, z0 + M2_INSERT_L + 1.0, x, y)   # M2 insert, from below (depth L+1mm)
        sp = sp - cyl(M2_CLR / 2, z0, z1 + SPIDER_PILLAR - 0.6, x, y)        # screw-tip room
    for (x, y) in CP_SCREWS:
        sp = sp - cyl(M3_CLR / 2, z0 - 1, CP_HUB_FACE_Z + 1, x, y)
        sp = sp - cyl(3.1, z0 - 1, z0 + 1.0, x, y)       # shallow head seat
    for b in CP_KEEPOUT:                                 # plug clearance
        x0, x1, y0, y1 = b
        sp = sp - Pos((x0 + x1) / 2, (y0 + y1) / 2, z0 - 1) * Box(x1 - x0 + 2, y1 - y0 + 2, 30,
                                                                  align=(Align.CENTER, Align.CENTER, Align.MIN))
    return sp


def _bar(a, b, w, z0, z1):
    ax, ay = a
    bx, by = b
    L = sqrt((bx - ax) ** 2 + (by - ay) ** 2)
    ang = degrees(atan2(by - ay, bx - ax))
    return Pos(ax, ay, z0) * Rot(0, 0, ang) * Box(L, w, z1 - z0, align=(Align.MIN, Align.CENTER, Align.MIN))


def _seg_box_dist(a, b, box):
    """Euclidean distance between segment a-b and an axis-aligned box (x0, x1, y0, y1)."""
    import numpy as np
    x0, x1, y0, y1 = box
    best = 1e9
    for t in np.linspace(0, 1, 201):
        px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        dx = max(x0 - px, 0, px - x1)
        dy = max(y0 - py, 0, py - y1)
        best = min(best, (dx * dx + dy * dy) ** 0.5)
    return best


def _route_arm(end, need=ARM_W / 2 + 1.0):
    """Hub -> standoff path that keeps every connector plug keep-out clear.
    Tries the straight arm, then one-bend paths; returns the path with the
    most clearance (ties go to the shortest)."""
    from math import hypot
    cands = [[(0.0, 0.0), end]]
    ang0 = degrees(atan2(end[1], end[0]))
    for da in range(-60, 61, 3):
        for r in (14, 16, 18, 20, 22, 24):
            cands.append([(0.0, 0.0), polar(r, ang0 + da), end])

    def clearance(path):
        return min(_seg_box_dist(a, b, bx) for a, b in zip(path[:-1], path[1:]) for bx in CP_KEEPOUT)

    def length(path):
        return sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path[:-1], path[1:]))

    ok = [c for c in cands if clearance(c) >= need]
    if ok:
        return min(ok, key=length)
    return max(cands, key=clearance)


def _seg_hits_box(a, b, pad, box):
    x0, x1, y0, y1 = box
    for i in range(41):
        t = i / 40
        px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        if x0 - pad <= px <= x1 + pad and y0 - pad <= py <= y1 + pad:
            return True
    return False


def carrier():
    z0, z1 = SPLIT_Z, CARRIER_FRONT
    r = sqrt(R_IN ** 2 - (SPLIT_Z - C_Z) ** 2) - 0.4
    c = cyl(r, z0, z1)
    for (x, y) in rs_holes():                           # bosses up to board back
        c = c + cyl(3.25, z1, -RS_T, x, y)
        c = c - cyl(M2_CLR / 2, z0 - 1, 0, x, y)
        c = c - cyl(2.2, z0 - 1, z0 + CARRIER_CB, x, y)  # M2 SHCS head, flush
    for ang in SHELL_LUG_ANG:                           # countersunk M2.5 into front-shell lugs
        x, y = polar(SHELL_LUG_R, ang)
        c = c - cyl(M3_CLR / 2, z0 - 1, z1 + 1, x, y)
        c = c - cyl(RIM_CB[0] / 2, z0 - 1, z0 + RIM_CB[1], x, y)        # M3 x 6 SHCS head
    for ang in REAR_RIB_ANG:                            # inserts for the rear-shell ribs
        x, y = polar(REAR_RIB_R, ang)
        c = c + cyl(4.0, z1, -RS_BACK_PARTS - 0.6, x, y)
        c = c - cyl(M3_INSERT_D / 2, z0 - 1, z0 + CARRIER_INSERT_DEPTH, x, y)  # boss top is pinned by the board parts
    # wire passages: CrowPanel lead at the notch angle, centre hole for the rest
    c = c - Rot(0, 0, NOTCH_ANG) * Pos(r - 3, 0, z0 - 1) * Box(8, 6, 10,
                                                              align=(Align.CENTER, Align.CENTER, Align.MIN))
    c = c - cyl(6.0, z0 - 1, z1 + 1, -12, 0)
    c = c & above_floor()
    return c


def speaker_placed():
    """Vendor speaker, diaphragm face down on the gasket, lead toward +y."""
    from build123d import import_step
    spk = import_step(str(SPK_STEP))
    return Pos(0, SPK_CY, BACK_Z + SPK_GASKET + SPK_BODY[2]) * Rot(0, 180, 0) * spk


def insert_coupon():
    """Test block: 3 hole sizes per insert (M2, M3). Holes marked by 1/2/3 dots."""
    sizes = {"M2": (M2_INSERT_D - 0.2, M2_INSERT_D, M2_INSERT_D + 0.2), "M3": (M3_INSERT_D - 0.2, M3_INSERT_D, M3_INSERT_D + 0.2)}
    blk = Pos(0, 0, 0) * Box(40, 22, 7, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for row, (k, ds) in enumerate(sizes.items()):
        y = -5.5 + row * 11
        for col, d in enumerate(ds):
            x = -12 + col * 12
            blk = blk - cyl(d / 2, 0.8, 8, x, y)
            for dot in range(col + 1):                 # 1, 2, 3 dots = small, nominal, large
                blk = blk - cyl(0.5, 6.6, 8, x - 1.5 + dot * 1.5, y + 4.2)
    for row in range(2):                               # 1 notch = M2 row, 2 = M3 row
        for n in range(row + 1):
            blk = blk - Pos(-19.5, -5.5 + row * 11 + n * 2 - row, 3.5) * Box(2, 1, 8)
    return blk


def board_spacers():
    """3 printed spacers between the reSpeaker front and the spider (replace brass standoffs)."""
    sp = None
    for (x, y) in rs_holes():
        t = cyl(SPACER_OD / 2, 0, STANDOFF_L - 0.05, x, y) - cyl(M2_CLR / 2, -1, STANDOFF_L + 1, x, y)
        sp = t if sp is None else sp + t
    return sp


def tpu_washers():
    """4 isolation washers (2 per ear). Print in TPU; rubber M2 washers also work."""
    w = None
    for k in range(4):
        r = Pos(k * 9.0, 0, 0) * (cyl(3.0, 0, TPU_WASHER_T) - cyl(1.25, -1, TPU_WASHER_T + 1))
        w = r if w is None else w + r
    return w


def plunger():
    """Mute button plunger with snap-fit barb and flexure slot. Modelled in D frame at 12 o'clock."""
    r_btn = RS_EDGE_R + 0.15
    r_out = SPHERE_R + 0.6
    rod = radial_cyl(2.0, 90, r_btn, r_out - 1.2, RS_BTN_Z)
    cap = radial_cyl(3.5, 90, r_out - 1.2 - 0.6, r_out, RS_BTN_Z)   # 0.6 mm travel
    ramp = radial_cone(1.95, 2.35, 90, 55.4, 56.6, RS_BTN_Z)
    back = radial_cone(2.35, 2.0, 90, 56.6, 57.0, RS_BTN_Z)
    barb = ramp + back
    slot = Pos(0, (r_btn - 0.5 + 57.5) / 2, RS_BTN_Z) * Box(0.8, 57.5 - (r_btn - 0.5), 6.0)
    return rod + cap + barb - slot


# ---------------------------------------------------------------- proxies (render/check only)
def proxies():
    p = {}
    p["cp_knob"] = cyl(CP_KNOB_R, -1.6 + CP_Z0, 12.4 + CP_Z0)
    p["cp_glass"] = cyl(33.0, 12.4 + CP_Z0, 12.5 + CP_Z0)
    p["cp_housing"] = cyl(CP_HOUSING_R, -11.1 + CP_Z0, -1.6 + CP_Z0)
    p["cp_pcb"] = cyl(24.0, CP_PCB_REAR_Z, CP_PCB_REAR_Z + 1.0) + cyl(8.4, CP_HUB_FACE_Z, CP_PCB_REAR_Z + 1)
    conn = None
    for (x0, x1, y0, y1) in CP_KEEPOUT:
        b = Pos((x0 + x1) / 2, (y0 + y1) / 2, CP_REAR_Z) * Box(x1 - x0, y1 - y0, CP_PCB_REAR_Z - CP_REAR_Z,
                                                               align=(Align.CENTER, Align.CENTER, Align.MIN))
        conn = b if conn is None else conn + b
    p["cp_conn"] = conn
    rs = cyl(RS_R, -RS_T, 0)
    for ang in (90, 270):
        rs = rs + Rot(0, 0, ang) * Pos(RS_R + 1.8, 0, -RS_T) * Box(3.6, 6, 2.4,
                                                                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    p["rs_pcb"] = rs
    leds = None
    for k in range(12):
        x, y = polar(RS_LED_R, 15 + 30 * k)
        l = Pos(x, y, 0) * Box(2, 2, 0.8, align=(Align.CENTER, Align.CENTER, Align.MIN))
        leds = l if leds is None else leds + l
    p["rs_leds"] = leds
    xiao = Rot(0, 0, RS_ROT) * Pos(0, 39, -RS_T) * Box(18, 22, 4.5, align=(Align.CENTER, Align.CENTER, Align.MAX))
    p["rs_xiao"] = xiao

    p["speaker"] = speaker_placed()
    return p


PRINT_PARTS = {
    "front_shell": front_shell,
    "rear_shell": rear_shell,
    "back_plate": back_plate,
    "light_guide": light_guide,
    "spider": spider,
    "carrier": carrier,
    "mute_plunger": plunger,
    "tpu_washers": tpu_washers,
    "insert_coupon": insert_coupon,
    "board_spacers": board_spacers,
}

# print orientation: rotation applied in D frame before dropping to z=0
PRINT_ROT = {
    "front_shell": Rot(180, 0, 0),     # face down
    "rear_shell": Rot(0, 0, 0),        # back rim down
    "back_plate": Rot(0, 0, 0),        # outer face down
    "light_guide": Rot(180, 0, 0),     # bezel face down
    "spider": Rot(0, 0, 0),            # plate down, hub boss up
    "carrier": Rot(0, 0, 0),           # back face down, bosses up
    "mute_plunger": Rot(-90, 0, 0),    # cap down, rod up
    "tpu_washers": Rot(0, 0, 0),
    "insert_coupon": Rot(0, 0, 0),
    "board_spacers": Rot(0, 0, 0),
}


# parts that get the outer-surface texture (texture.py) and the matching mesh rotations
TEXTURED = ["front_shell", "rear_shell", "back_plate"]
MESH_PRINT_ROT = {"front_shell": [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]}


def to_print(name, part):
    p = PRINT_ROT[name] * part
    bb = p.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * p


def to_world(part):
    """D frame -> world (Y up, Z toward viewer, table at y=0)."""
    w = Rot(-TILT, 0, 0) * part
    return Pos(0, -FOOT_H, 0) * w


if __name__ == "__main__":
    import json, sys
    OUT.mkdir(exist_ok=True)
    built = {}
    for name, fn in PRINT_PARTS.items():
        print("building", name, flush=True)
        built[name] = fn()
        pp = to_print(name, built[name])
        export_stl(pp, str(OUT / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.15)
        export_step(pp, str(OUT / f"{name}.step"))
        bb = pp.bounding_box()
        print(f"  {name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
              f"vol {pp.volume/1000:.1f} cm3", flush=True)
    # assembly (D frame) for checks + render
    prox = proxies()
    asm = Compound(children=list(built.values()) + list(prox.values()))
    export_step(asm, str(OUT / "assembly_D.step"))
    for name, s in list(built.items()) + list(prox.items()):
        export_stl(s, str(OUT / "asm" / f"{name}.stl"), tolerance=0.05, angular_tolerance=0.2) \
            if (OUT / "asm").mkdir(exist_ok=True) is None else None
    # surface texture (mesh level): carve the outer skin, then re-orient for print
    import numpy as np
    import trimesh
    import texture
    for name in TEXTURED:
        raw = OUT / "asm" / f"_{name}_fine.stl"
        export_stl(built[name], str(raw), tolerance=0.02, angular_tolerance=0.1)
        m = trimesh.load(raw)
        raw.unlink()
        t = texture.apply(m)
        # drop zero-volume sliver shells the boolean leaves at near-coincident faces
        bodies = [b for b in t.split(only_watertight=False) if b.is_watertight and b.volume > 1.0]
        assert len(bodies) == 1, (name, len(bodies))
        t = texture.clean(bodies[0])
        assert t.is_watertight and t.volume > 0, name
        # indexed PLY is the hand-off format (STL would weld micron-close vertices)
        t.export(OUT / "asm" / f"{name}.ply")                      # D frame, for render
        p = t.copy()
        p.apply_transform(MESH_PRINT_ROT.get(name, np.eye(4)))
        bb = p.bounds
        p.apply_translation([-(bb[0][0] + bb[1][0]) / 2, -(bb[0][1] + bb[1][1]) / 2, -bb[0][2]])
        p.export(OUT / f"{name}.ply")                               # print orientation (used by make_3mf)
        p.export(OUT / f"{name}.stl")                               # convenience copy
        print(f"  textured {name} ({texture.TEXTURE}, {texture.DEPTH} mm): {len(p.faces)} faces, "
              f"vol {p.volume/1000:.1f} cm3", flush=True)
    print("derived: sphere centre z=%.2f  foot(UP)=%.2f  floor top=%.2f" % (C_Z, FOOT_H, FLOOR_TOP))
