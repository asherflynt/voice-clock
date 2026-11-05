"""Voice Clock enclosure - parametric build123d model (v1: snap-fit shells).

Frame "D" (device frame), used for everything below:
  origin = centre of the reSpeaker PCB *front* face (LED / mic-port side)
  +Z     = toward the viewer (out of the display)
  +Y     = display "up" (before the 15 deg tilt)
  +X     = right, as seen from the front
The whole device is tilted face-up by TILT about X; world "up" in D is UP_D.

v1 layout (5 Nov 2026):
  * The front / rear split sits 1 mm in front of the reSpeaker. The board drops into the
    rear shell from the front onto 4 cradle ribs (centring faces + back pads), so it never
    slides past the floor and the flat base can be wide.
  * The front shell snaps on over the knob (4 hooks on the rear shell, ridges in the front
    shell) and clamps the board through the light guide. No screws, no inserts.
  * The back plate snaps into the rear shell (3 hooks, keyed at 6 o'clock).
  * The mute plunger lives in the rear shell, on the measured BUTA actuator.

Run:  .venv/bin/python voice_clock.py          -> out/ (STL, STEP, checks)
Values marked VERIFY are from vendor CAD/drawings, not calipers yet.
"""
from math import cos, sin, radians, sqrt, atan2, degrees
from pathlib import Path
from build123d import (Sphere, Cylinder, Cone, Box, Pos, Rot, Plane, Polygon,
                       Location, Vector, Align, extrude, export_stl, export_step,
                       Compound, Part)

OUT = Path(__file__).parent / "out"
VENDOR = next((d for d in (Path(__file__).parent / "vendor", Path(__file__).parent.parent / "decive files")
               if (d / "speaker_4428_3W8R.step").exists()), Path(__file__).parent / "vendor")
RS_STEP = next((d / "respeaker_mic_array_xvf3800_1_with-xiao-0820.stp"
                for d in (Path(__file__).parent / "vendor", Path(__file__).parent.parent / "decive files")
                if (d / "respeaker_mic_array_xvf3800_1_with-xiao-0820.stp").exists()), None)

# ---------------------------------------------------------------- parameters
SPHERE_R      = 58.0      # outer radius (OD 116; was 120)
WALL          = 2.5
FACE_R        = 44.0      # flat face OD 88
FACE_Z        = 35.0      # face plane, board-front + 35
TILT          = 15.0      # deg, face tilted up
FOOT_R        = 27.0      # flat base OD 54 (was 42). Limited by the reset button at 6 o'clock.
FLOOR         = 2.5
SPLIT_Z       = 1.0       # front / rear shell split (1 mm in front of the reSpeaker)
BACK_T        = 2.5       # back plate thickness
BACK_LAT      = 45.0      # back plate cut at 45 deg latitude behind the sphere centre

# reSpeaker XVF3800 (measured from respeaker_mic_array_xvf3800_1_with-xiao-0820.stp)
RS_R          = 50.0      # bare PCB radius
RS_EDGE_R     = 53.2      # main USB-C / 3.5 mm jack at 9 o'clock (D) reach r = 53.16
RS_T          = 1.11
RS_BACK_PARTS = 7.9       # tallest back-side part below PCB front (header 6.7 + PCB)
RS_HOLES_DRAW = [(-21.35, 24.5), (21.35, 24.5), (0.0, -34.0)]
RS_ROT        = -90.0     # deg CCW. Mute ("BUTA") is at 9 o'clock seen from the LED side with the
                          # XIAO at the top (confirmed on hardware 1 Nov 2026); -90 puts it at 12.
RS_MIC_R      = 46.67     # mics on the 45 deg diagonals
RS_LED_R      = 40.0      # 12 LEDs at 15 + 30k deg (D)
# side buttons (STEP): body r 46.5-50.6, z -4.79..-1.11 (hangs below the PCB);
# actuator nub 2.9 wide, z -3.75..-2.20
RS_MUTE_TIP_R = 50.23     # BUTA nub at 12 o'clock (D 90 deg)
RS_RST_TIP_R  = 51.58     # reset nub at 6 o'clock (D 270 deg)
RS_BTN_Z      = -2.97     # nub centre height
RS_BTN_BODY   = (46.5, 50.6, -4.79, -1.11)    # r0, r1, z0, z1 (reset body r1 = 50.58)

# CrowPanel 2.1 (from 00-irad-21.stp; C.y = view axis, knob front at C.y=12.4)
KNOB_PROUD    = 7.0
CP_Z0         = FACE_Z + KNOB_PROUD - 12.4     # D.z = C.y + CP_Z0  (= 29.6)
CP_KNOB_R     = 39.5      # VERIFY with calipers: the knob gap below is only 0.45 mm
CP_HOUSING_R  = 38.95
CP_HOUSING_Z  = (-11.1 + CP_Z0, -1.6 + CP_Z0)  # 18.5 .. 28.0 fixed housing behind the ring
CP_HUB_FACE_Z = -15.0 + CP_Z0                  # 14.6  rear face of Ø16.8 hub
CP_PCB_REAR_Z = -14.5 + CP_Z0                  # 15.1
CP_REAR_Z     = -21.0 + CP_Z0                  # 8.6   connectors end here
CP_SCREWS     = [(-5.15, -2.98), (5.15, -2.98), (0.0, 5.95)]   # D x,y (M3)
# rear 4-pin connector plug keep-outs (D x0,x1,y0,y1)
CP_KEEPOUT    = [(1.6, 8.5, 14.1, 17.8), (-8.5, -1.6, 14.1, 17.8),
                 (10.6, 14.4, -3.5, 3.5)]

# light guide / bezel
LG_KNOB_GAP   = 0.45                           # radial knob gap (was 0.75)
LG_RI         = CP_KNOB_R + LG_KNOB_GAP        # 39.95
LG_LAND_R     = CP_HOUSING_R + 0.25            # 39.2: centres the guide on the fixed housing
LG_LAND_Z     = (20.0, 27.0)                   # inside the housing span 18.5..28.0
LG_RO_FRONT   = 42.5
LG_RO         = 44.0
LG_STEP_Z     = 29.0
SHELL_BORE_R  = LG_RO_FRONT + 0.2
LG_LIP_RI     = 38.6
LG_LED_POCKET = (38.6, 41.8, 1.6)              # ri, ro, height over LEDs (2020 LEDs reach r 41.4)
LG_CRUSH      = 0.25                           # 3 crush nubs on the back face take up print tolerance
NOTCH_ANG     = 120.0                          # cable notch: between LEDs 105/135, clear of the jack/USB
NOTCH_W, NOTCH_H = 4.5, 4.0

# spider bracket + reSpeaker clamp (hardware = what's in the user's two kits:
#   inserts M2x3xOD3.2, M3x4xOD4.2; screws M2 SHCS 10/12/16/20, M3 SHCS 6/8/12/16/20,
#   M3 button 8/12/16/20; no countersunk, no standoffs)
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

# carrier (bulkhead behind the board; now hangs on the 3 clamp screws only)
CARRIER_Z0    = -14.5
CARRIER_T     = 2.5
CARRIER_FRONT = CARRIER_Z0 + CARRIER_T         # -12.0
CARRIER_R     = 51.0      # clear of the snap-hook roots (r >= 52)
# -> clamp screw tip at -14.5 + 2.0 + 20 = +7.5: 2.5 mm into the 3 mm spider insert (z 5..8)

# heat-set inserts (3DZWMAN D3 hole sizes). Only M2 is used now (spider x3, speaker x2).
M3_INSERT_D   = 4.0       # (insert coupon only)
M2_INSERT_L   = 3.0       # M2 x 3 x OD3.2
M2_INSERT_D   = 2.9       # 3DZWMAN D3 for M2 (OD 3.0 -> hole 2.9, min wall W=1.3)
M2_INSERT_DEPTH = 6.5     # M2 x 10 passes 2.6 mm beyond the insert

# cradle: 4 ribs in the rear shell centre the board (r CRADLE_R) and carry its back face
CRADLE_ANG    = [25.0, 150.0, 255.0, 300.0]    # clear of every back-side part at r > 48 (STEP)
CRADLE_R      = 50.15     # PCB is r 50.00
CRADLE_PAD_R  = 48.4
CRADLE_W      = 5.0

# snap hooks: front shell <-> rear shell (hooks on the rear shell, ridges in the front shell)
SNAP_ANG      = [65.0, 165.0, 240.0, 335.0]    # clear of mic boots, buttons, USB-C / jack, cradle
SNAP_W        = 6.0
SNAP_T        = 1.4       # hook arm thickness (radial)
SNAP_ENG      = 0.5       # barb engagement
SNAP_GAP      = 0.2       # arm -> ridge face clearance
SNAP_R_IN     = 52.0      # arm inner face
SNAP_ROOT_Z   = -7.5      # arm root (free length ~12 mm -> 0.7 % strain)
SNAP_ZC       = 4.5       # ridge / barb contact height
LIP_H, LIP_T  = 2.0, 1.2  # alignment lip on the rear shell rim (keyed by the mic boots)

# snap hooks: back plate -> rear shell
BSNAP_ANG     = [90.0, 210.0, 330.0]
BSNAP_ZC_UP   = 11.5      # contact height above the plate's inner face
BKEY_ANG      = 270.0     # back plate key (slot in the rear rim)
PRY_ANG       = 70.0      # pry notch on the back plate rim

# mic channels
MIC_BORE      = 2.0
MIC_LUG_Z0    = 1.1       # lug underside (1/16" = 1.6 mm foam gasket, ~30% squeeze)
MIC_CH_Z      = 3.0

# mute plunger (rear shell, D 90 deg)
PLG_Z         = -3.3      # axis height: rod d3.6 covers the nub (z -3.75..-2.20)
PLG_ROD_R     = 1.8
PLG_BORE_R    = 2.0
PLG_CAP_R     = 2.8
PLG_CB_R      = 3.1
PLG_GAP       = 0.25      # rod tip -> nub at rest
PLG_TRAVEL    = 1.0       # cap -> counterbore floor (switch travel ~0.25 + tolerance)
PLG_PROUD     = 0.6
PLG_BOSS_R0   = 53.0      # inner end of the guide boss

# speaker: 4428 3 W 8 ohm, from ../decive files/speaker_4428_3W8R.step
SPK_STEP      = VENDOR / "speaker_4428_3W8R.step"
SPK_BODY      = (28.2, 31.0, 15.3)             # body x (ear axis), y, z (back -> diaphragm face)
SPK_EAR_PITCH = 36.7                           # ear hole c-c, holes d2.4 -> M2
SPK_EAR_T     = 2.4
SPK_EAR_FROM_FACE = 15.3 - 6.9                 # diaphragm face -> ear face nearest it (8.4)
SPK_CONE_R    = 13.0                           # diaphragm recess radius
SPK_CY        = 0.0                            # speaker centre, D y (lead exits toward +y)
SPK_GASKET    = 1.1                            # 1/16" (1.6 mm) foam squeezed to 1.1
TPU_WASHER_T  = 1.0                            # isolation washer, one each side of each ear
# USB-C inlet: 6-pin breakout with 5.1k CC resistors, measured 3 Nov 2026:
# PCB 21.96 x 13.11 x 1.61, socket on the top face centred on the long (USB) edge,
# socket 3.30 tall, opening overhangs that edge by 1.48. Two holes near the USB edge:
# 18.95 outer-to-outer, hole edge 1.61 from the USB edge (hole d not measured, ~2.5).
USB_CY        = -27.0
USB_SLOT      = (9.4, 3.6)                     # socket shell ~8.94 x 3.30
USB_RECESS    = (13.5, 8.0, 1.6)               # outside, for the plug overmould
USB_PCB       = (21.96, 13.11, 1.61)           # length (along the USB edge), height, thickness
USB_SOCKET_H  = 3.30
USB_HOLE_D    = 2.5                            # estimate
USB_HOLE_PITCH= 18.95 - USB_HOLE_D             # centre-to-centre (~16.45)
USB_HOLE_Z    = 1.61 + USB_HOLE_D / 2          # hole centre above the plate's inner face

# ---------------------------------------------------------------- derived
C_Z    = FACE_Z - sqrt(SPHERE_R**2 - FACE_R**2)          # sphere centre z (-2.79)
R_IN   = SPHERE_R - WALL
UP_D   = Vector(0, cos(radians(TILT)), sin(radians(TILT)))
CEN    = Vector(0, 0, C_Z)
FOOT_H = CEN.dot(UP_D) - sqrt(SPHERE_R**2 - FOOT_R**2)   # base plane (along UP_D)
FLOOR_TOP = FOOT_H + FLOOR
BACK_Z = C_Z - SPHERE_R * cos(radians(BACK_LAT))         # rear shell ends / back plate inner face


def r_in_at(z):
    """Inner wall radius of the sphere at height z."""
    return sqrt(R_IN ** 2 - (z - C_Z) ** 2)


def r_out_at(z):
    return sqrt(SPHERE_R ** 2 - (z - C_Z) ** 2)


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


def revolve_rz(pts):
    """Solid of revolution of an (r, z) polygon about the Z axis."""
    from build123d import revolve, Axis
    return revolve(Plane.XZ * Polygon(*pts, align=None), Axis.Z)


def radial_box(ang, r0, r1, w, z0, z1):
    """Box from r0 to r1 along direction ang, width w, z0..z1."""
    return Rot(0, 0, ang) * (Pos(r0, 0, z0) * Box(r1 - r0, w, z1 - z0,
                                                  align=(Align.MIN, Align.CENTER, Align.MIN)))


def sphere_out():
    return Pos(*CEN) * Sphere(SPHERE_R)


def sphere_in(dr=0.0):
    return Pos(*CEN) * Sphere(R_IN + dr)


def above_floor(clear=0.3):
    return half(UP_D, FLOOR_TOP + clear)


def body_envelope():
    return sphere_out() & half(UP_D, FOOT_H)


def cavity():
    return sphere_in() & half(UP_D, FLOOR_TOP)


# ---------------------------------------------------------------- snap hooks
def snap_hook(ang, r_in, z_root, z_c, w=SNAP_W, t=SNAP_T, eng=SNAP_ENG, gap=SNAP_GAP):
    """Cantilever hook pointing +z with an outward barb. The mating ridge (snap_ridge) ends up
    below the barb; the hook passes it going +z. 45 deg retention face -> pulls apart by hand."""
    r_out = r_in + t
    r_b = r_out + gap                      # ridge face
    tip = r_b + eng
    z_top = z_c + eng + 0.4 + (tip - r_out) / 0.577 + 0.5
    arm = rz_profile([(r_in, z_root), (r_out, z_root), (r_out, z_top), (r_in, z_top)], ang, w / 2)
    barb = rz_profile([(r_out - 0.01, z_c - gap), (tip, z_c + eng), (tip, z_c + eng + 0.4),
                       (r_out - 0.01, z_c + eng + 0.4 + (tip - r_out) / 0.577)], ang, w / 2)
    return arm + barb


def snap_ridge(ang, r_b, z_c, r_wall, z_lo, z_hi, w=SNAP_W, clr=0.05, flat_top=None):
    """Ridge on the mating wall, below the barb. Retention face 45 deg, lead-in ~40 deg.
    Clipped to z_lo..z_hi so it stays inside its own part."""
    top = [(r_wall, z_c - clr + (r_wall - r_b))]
    if flat_top is not None:                # flat top (rear shell prints it as a top surface)
        top = [(r_b + flat_top, z_c - clr + flat_top), (r_wall, z_c - clr + flat_top)]
    pts = [(r_b, z_c - 0.45), (r_b, z_c - clr)] + top + \
          [(r_wall, z_c - 0.45 - (r_wall - r_b) * 1.2)]
    return rz_profile(pts, ang, w / 2) & zslab(z_lo, z_hi)


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

    # snap ridges for the rear-shell hooks
    r_b = SNAP_R_IN + SNAP_T + SNAP_GAP
    for ang in SNAP_ANG:
        shell = shell + (snap_ridge(ang, r_b, SNAP_ZC, SPHERE_R - 1.0, SPLIT_Z + 0.3, FACE_Z) & env)
    return shell


def rear_shell():
    outer = body_envelope() & zslab(BACK_Z, SPLIT_Z)
    shell = outer - cavity()
    env = body_envelope()

    # alignment lip above the rim: centres the front shell; the gaps take the mic boots (key)
    lip = ((sphere_in(-0.15) - sphere_in(-0.15 - LIP_T)) & zslab(SPLIT_Z, SPLIT_Z + LIP_H)) + \
          ((sphere_in(0.5) - sphere_in(-0.15 - LIP_T)) & zslab(SPLIT_Z - 1.0, SPLIT_Z))
    lip = lip & above_floor(0.8)      # the front shell's floor rises as it slides on
    for ang in (45, 135, 225, 315):
        lip = lip - radial_box(ang, 30, 70, 9.0 + 1.0, SPLIT_Z - 1, SPLIT_Z + 5)
    for ang in SNAP_ANG:
        lip = lip - radial_box(ang, 30, 70, SNAP_W + 1.0, SPLIT_Z - 1, SPLIT_Z + 5)
    shell = shell + lip

    # cradle: centring face r CRADLE_R over the PCB edge, pad under the PCB back
    for ang in CRADLE_ANG:
        rw = SPHERE_R
        pts = [(CRADLE_PAD_R, -RS_T), (CRADLE_R, -RS_T), (CRADLE_R, 0.0), (CRADLE_R + 0.6, 0.6),
               (rw, 0.6), (rw, -RS_T - 0.8 - (rw - CRADLE_PAD_R)), (CRADLE_PAD_R, -RS_T - 0.8)]
        shell = shell + (rz_profile(pts, ang, CRADLE_W / 2) & env)

    # snap hooks (rise past the rim into the front shell) + root lugs on the wall
    for ang in SNAP_ANG:
        rw = SPHERE_R
        root = rz_profile([(SNAP_R_IN, SNAP_ROOT_Z), (rw, SNAP_ROOT_Z),
                           (rw, SNAP_ROOT_Z - 1.5 - (rw - SNAP_R_IN)), (SNAP_R_IN, SNAP_ROOT_Z - 1.5)],
                          ang, SNAP_W / 2)
        shell = shell + (root & env) + snap_hook(ang, SNAP_R_IN, SNAP_ROOT_Z - 0.5, SNAP_ZC)

    # mute plunger: guide boss + bore + outside counterbore at 12 o'clock
    boss = radial_cyl(4.0, 90, PLG_BOSS_R0, SPHERE_R - 0.5, PLG_Z) & zslab(-50, SPLIT_Z)
    shell = shell + (boss & env)
    cb_floor = SPHERE_R + PLG_PROUD - 1.5 - PLG_TRAVEL
    shell = shell - radial_cyl(PLG_BORE_R, 90, PLG_BOSS_R0 - 1, SPHERE_R + 3, PLG_Z)
    shell = shell - radial_cyl(PLG_CB_R, 90, cb_floor, SPHERE_R + 3, PLG_Z)

    # floor pocket under the reset button + PCB tab (6 o'clock, tab 264-276 deg to r 50.77):
    # keeps >= 0.9 mm floor; runs up to the rim because the button passes it on the way in
    r0, r1, z0, z1 = RS_BTN_BODY
    pocket = radial_box(270, r0 - 0.5, RS_RST_TIP_R + 1.5, 12.0, z0 - 0.8, SPLIT_Z + 0.5)
    shell = shell - (pocket & half(UP_D, FOOT_H + 0.9))

    # back plate: snap ridges near the back opening + key slot in the rim
    r_open = r_in_at(BACK_Z)
    rb = r_open - 1.0
    zc = BACK_Z + BSNAP_ZC_UP
    for ang in BSNAP_ANG:
        shell = shell + (snap_ridge(ang, rb, zc, SPHERE_R - 1.0, BACK_Z + 0.3, SPLIT_Z, flat_top=1.6)
                         & sphere_out())
    shell = shell - radial_box(BKEY_ANG, r_open - 2, r_open + 2.0, 4.6, BACK_Z - 1, BACK_Z + 2.6)
    return shell


def back_plate():
    plate = body_envelope() & zslab(BACK_Z - BACK_T, BACK_Z)
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
    # snap hooks into the rear shell + key + pry notch
    r_open = r_in_at(BACK_Z)
    r_in = r_open - 1.0 - SNAP_GAP - SNAP_T
    for ang in BSNAP_ANG:
        plate = plate + snap_hook(ang, r_in, BACK_Z - 0.5, BACK_Z + BSNAP_ZC_UP)
    plate = plate + radial_box(BKEY_ANG, r_open - 0.6, r_open + 1.7, 4.0, BACK_Z - 0.5, BACK_Z + 2.2)
    plate = plate - radial_box(PRY_ANG, r_out_at(BACK_Z - BACK_T) - 2.0, SPHERE_R, 8.0,
                               BACK_Z - BACK_T - 1, BACK_Z - BACK_T + 1.0)
    return plate


def light_guide():
    lg = cyl(LG_RO_FRONT, LG_STEP_Z, FACE_Z) + cyl(LG_RO, 0.0, LG_STEP_Z - 1.5)
    lg = lg + Pos(0, 0, LG_STEP_Z - 1.5) * Cone(LG_RO, LG_RO_FRONT, 1.5,
                                                align=(Align.CENTER, Align.CENTER, Align.MIN))
    lg = lg - cyl(LG_RI, -1, FACE_Z + 1)
    # centring land on the CrowPanel's fixed housing (45 deg ends so it prints face-down)
    z0, z1 = LG_LAND_Z
    d = LG_RI - LG_LAND_R
    land = revolve_rz([(LG_RI + 0.01, z0), (LG_RI + 0.01, z1), (LG_LAND_R, z1 - d), (LG_LAND_R, z0 + d)])
    lg = lg + land
    # inward lip over the LEDs (cone: thin at the bore, full at the wall, so the lip is
    # self-supporting when the guide prints face-down)
    zl = LG_LED_POCKET[2]
    lip = cyl(LG_RI + 0.01, zl, zl + 2.0) - \
        Pos(0, 0, zl) * Cone(LG_LIP_RI, LG_RI + 0.01, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    lg = lg + lip
    lg = lg - (cyl(LG_LED_POCKET[1], -1, LG_LED_POCKET[2]) - cyl(LG_LED_POCKET[0], -2, LG_LED_POCKET[2] + 1))
    # cable notch
    lg = lg - Rot(0, 0, NOTCH_ANG) * Pos(LG_RI + 2, 0, NOTCH_H / 2 - 0.5) * Box(12, NOTCH_W, NOTCH_H + 1)
    # crush nubs on the back face (between LEDs, away from the notch)
    for ang in (0.0, 240.0, 300.0):
        x, y = polar((LG_LED_POCKET[1] + LG_RO) / 2, ang)
        lg = lg + cyl(0.6, -LG_CRUSH, 0.01, x, y)
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


def carrier():
    z0, z1 = CARRIER_Z0, CARRIER_FRONT
    c = cyl(CARRIER_R, z0, z1)
    for (x, y) in rs_holes():                           # bosses up to board back
        c = c + cyl(3.25, z1, -RS_T, x, y)
        c = c - cyl(M2_CLR / 2, z0 - 1, 0, x, y)
        c = c - cyl(2.2, z0 - 1, z0 + CARRIER_CB, x, y)  # M2 SHCS head, flush
    # wire passages: CrowPanel lead at the notch angle, centre hole for the rest
    c = c - Rot(0, 0, NOTCH_ANG) * Pos(CARRIER_R - 3, 0, z0 - 1) * Box(8, 6, 10,
                                                                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    c = c - cyl(6.0, z0 - 1, z1 + 1, -12, 0)
    for ang in CRADLE_ANG:                              # drops past the cradle pads
        c = c - radial_box(ang, CRADLE_PAD_R - 0.5, 60, CRADLE_W + 1.0, z0 - 1, z1 + 1)
    c = c & above_floor()
    return c


def speaker_placed():
    """Vendor speaker, diaphragm face down on the gasket, lead toward +y."""
    from build123d import import_step
    spk = import_step(str(SPK_STEP))
    return Pos(0, SPK_CY, BACK_Z + SPK_GASKET + SPK_BODY[2]) * Rot(0, 180, 0) * spk


_RS_STEP = None


def respeaker_placed():
    """Vendor reSpeaker STEP in the D frame (580 solids). Used by check.py."""
    global _RS_STEP
    if _RS_STEP is None:
        from build123d import import_step
        s = import_step(str(RS_STEP))
        _RS_STEP = Rot(0, 0, RS_ROT) * (Pos(-150.0, 80.0, -RS_T) * s)
    return _RS_STEP


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


def plunger_rest_tip():
    return RS_MUTE_TIP_R + PLG_GAP


def plunger():
    """Mute plunger: T-shape, split stem with a snap barb that clicks past the inner end of the
    guide boss. Modelled in the D frame at 12 o'clock, at rest (tip PLG_GAP off the BUTA nub)."""
    r_tip = plunger_rest_tip()
    r_cap_top = SPHERE_R + PLG_PROUD
    r_cap_bot = r_cap_top - 1.5
    rod = radial_cyl(PLG_ROD_R, 90, r_tip, r_cap_bot + 0.01, PLG_Z)
    cap = radial_cyl(PLG_CAP_R, 90, r_cap_bot, r_cap_top, PLG_Z)
    r_shoulder = PLG_BOSS_R0 - 0.05                     # barb shoulder rests just inside the boss
    ramp = radial_cone(PLG_ROD_R - 0.05, PLG_BORE_R + 0.15, 90, r_shoulder - 1.3, r_shoulder, PLG_Z)
    barb = ramp
    slot_r0, slot_r1 = r_tip - 0.5, PLG_BOSS_R0 + 1.6
    slot = Pos(0, (slot_r0 + slot_r1) / 2, PLG_Z) * Box(0.8, slot_r1 - slot_r0, 6.0)
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
    # reSpeaker: PCB + the parts that reach past it (positions from the STEP)
    rs = cyl(RS_R, -RS_T, 0)
    r0, r1, z0, z1 = RS_BTN_BODY
    for ang, tip in ((90, RS_MUTE_TIP_R), (270, RS_RST_TIP_R)):
        rs = rs + radial_box(ang, r0, tip - 1.0, 7.8, z0, z1)
        rs = rs + radial_box(ang, tip - 1.0, tip, 2.9, -3.75, -2.20)
    rs = rs + radial_box(180, 44.7, RS_EDGE_R, 9.0, -4.5, -0.24)                 # main USB-C
    rs = rs + radial_box(197, 40.0, RS_EDGE_R - 0.4, 10.0, -6.4, -0.7)           # 3.5 mm jack
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
    only = sys.argv[1:]
    built = {}
    for name, fn in PRINT_PARTS.items():
        print("building", name, flush=True)
        built[name] = fn()
        if only and name not in only:
            continue
        pp = to_print(name, built[name])
        export_stl(pp, str(OUT / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.15)
        export_step(pp, str(OUT / f"{name}.step"))
        bb = pp.bounding_box()
        print(f"  {name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
              f"vol {pp.volume/1000:.1f} cm3, solids {len(pp.solids())}", flush=True)
    # assembly (D frame) for checks + render
    prox = proxies()
    asm = Compound(children=list(built.values()) + list(prox.values()))
    export_step(asm, str(OUT / "assembly_D.step"))
    (OUT / "asm").mkdir(exist_ok=True)
    for name, s in list(built.items()) + list(prox.items()):
        export_stl(s, str(OUT / "asm" / f"{name}.stl"), tolerance=0.05, angular_tolerance=0.2)
    # surface texture (mesh level): carve the outer skin, then re-orient for print
    import numpy as np
    import trimesh
    import texture
    for name in TEXTURED:
        if only and name not in only:
            continue
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
    print("derived: sphere centre z=%.2f  base(UP)=%.2f  floor top=%.2f  back z=%.2f" % (C_Z, FOOT_H, FLOOR_TOP, BACK_Z))
