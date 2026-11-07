"""Voice Clock enclosure - parametric build123d model (v2: twist locks, keyed stack, light channel).

Frame "D" (device frame), used for everything below:
  origin = centre of the reSpeaker PCB *front* face (LED / mic-port side)
  +Z     = toward the viewer (out of the display)
  +Y     = display "up" (before the 15 deg tilt)
  +X     = right, as seen from the front
  angles = CCW about +Z seen from the front (so "clockwise seen from the front" = decreasing angle)
The whole device is tilted face-up by TILT about X; world "up" in D is UP_D.

v2 (6 Nov 2026), after printing v1 in wood PLA:
  * Front shell <-> rear shell: a 7-lug bayonet. The rear shell's collar rises 5.5 mm past the seam
    inside the front shell; the front shell's blocks slide under its lugs when the front shell turns
    TW_ANGLE clockwise (seen from the front). A bump on each block clicks into a dimple in its lug;
    the mic gaskets keep it pressed in. Flat bearing faces, so it cannot cam apart.
  * Back plate: a 3-lug bayonet into a lip at the back opening, turned BP_TWIST clockwise seen from
    the back, held by 2 in-plane flexure pawls.
  * The stack (CrowPanel + spider + reSpeaker + light ring + carrier) is keyed: the 4 cradle ribs
    run down the rear shell wall and the carrier's notches fit them at 0.2 mm per side, so the stack
    can't turn in the shell while the front shell is off. (The ~5 deg dial offset seen on v1 is fixed
    and is cancelled separately by CP_ROT_TRIM_DEG.)
  * Light ring: a hollow channel (ring_base inner wall + ring_shell sleeve and cap) lined with
    aluminium foil tape. ring_base also carries the 3 board spacers on the clamp screws, so the ring
    is located and keyed by the stack. The ring stands RING_PROUD above the sphere.
  * Front shell prints face-up (seam on the bed); there is no flat face any more: the sphere runs up
    to the ring bore.
  * USB-C breakout and speaker screw into heat-set inserts with >= 2.5 mm of hole below the screw tip.

Run:  .venv/bin/python voice_clock.py          -> out/ (STL, STEP)
Values marked VERIFY are from vendor CAD/drawings, not calipers yet.
"""
from math import cos, sin, radians, sqrt, atan2, degrees, hypot
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
CP_STEP = next((d / "00-irad-21.stp"
                for d in (Path(__file__).parent / "vendor", Path(__file__).parent.parent / "decive files")
                if (d / "00-irad-21.stp").exists()), None)

# ---------------------------------------------------------------- parameters
SPHERE_R      = 58.0      # outer radius (OD 116)
WALL          = 2.5
FACE_R        = 44.0      # v1's flat-face OD 88 at FACE_Z. Only a reference now: it fixes the sphere
FACE_Z        = 35.0      # centre (C_Z) and the CrowPanel position. v2 has no flat face.
TILT          = 15.0      # deg, face tilted up
FOOT_R        = 27.0      # flat base OD 54. Limited by the reset button at 6 o'clock.
FLOOR         = 2.5
SPLIT_Z       = 1.1       # front / rear seam; the front shell's bed face (it prints face-up)
BACK_T        = 2.4       # back plate thickness (on the 0.2 mm layer grid, so the lug gap prints true)
BACK_LAT      = 45.0      # back plate cut at 45 deg latitude behind the sphere centre

# reSpeaker XVF3800 (measured from respeaker_mic_array_xvf3800_1_with-xiao-0820.stp)
RS_R          = 50.0      # bare PCB radius (tabs: 170-190 deg to 52.0, 190-210 to 51.7, 260-280 to 50.77)
RS_EDGE_R     = 53.2      # main USB-C reaches r 53.16; the 3.5 mm jack r 54.8 at 191-210 deg
RS_T          = 1.11
RS_BACK_PARTS = 7.9
RS_HOLES_DRAW = [(-21.35, 24.5), (21.35, 24.5), (0.0, -34.0)]
RS_ROT        = -90.0     # deg CCW. Mute ("BUTA") ends up at 12 o'clock under the plunger.
RS_MIC_R      = 46.67     # mics on the 45 deg diagonals
RS_LED_R      = 40.0      # 12 LEDs at 15 + 30k deg (bodies r 39.01..41.04, z 0.07..0.92)
RS_LED_CAP_R  = (38.08, 38.68)   # a 0402 capacitor sits just inside each LED (z <= 0.58)
RS_MUTE_TIP_R = 50.23     # BUTA nub at 12 o'clock (D 90 deg)
RS_RST_TIP_R  = 51.58     # reset nub at 6 o'clock (D 270 deg)
RS_BTN_Z      = -2.97
RS_BTN_BODY   = (46.5, 50.6, -4.79, -1.11)    # r0, r1, z0, z1

# CrowPanel 2.1 (from 00-irad-21.stp; C.y = view axis, knob front at C.y=12.4)
KNOB_PROUD    = 7.0                            # knob front 7 mm in front of v1's face plane: z 42
CP_Z0         = FACE_Z + KNOB_PROUD - 12.4     # D.z = C.y + CP_Z0  (= 29.6)
CP_KNOB_R     = 39.5      # VERIFY with calipers
CP_KNOB_Z     = (28.0, 42.0)                   # rotating ring. There is NO fixed housing behind it
                                               # (confirmed by Asher 6 Nov 2026 and by the STEP)
CP_HUB_FACE_Z = -15.0 + CP_Z0                  # 14.6: tips of the hub's 2 locating pins (spider seat)
CP_HUB_THREAD_Z = 16.2                         # hub material (thread) starts here
CP_STOCK_TIP_Z  = 18.1                         # tips of Elecrow's own M3 screws (STEP)
CP_PCB_REAR_Z = -14.5 + CP_Z0                  # 15.1
CP_REAR_Z     = -21.0 + CP_Z0                  # 8.6   connectors end here
CP_SCREWS_NOM = [(-5.15, -2.98), (5.15, -2.98), (0.0, 5.95)]   # D x,y (M3), before the trim
CP_KEEPOUT_NOM = [(1.6, 8.5, 14.1, 17.8), (-8.5, -1.6, 14.1, 17.8),
                  (10.6, 14.4, -3.5, 3.5)]     # rear 4-pin plug keep-outs (x0,x1,y0,y1), before the trim
CP_ROT_TRIM_DEG = -5.0    # rotates the CrowPanel (its screws in the spider) about D +Z. The assembled v1
                          # dial sat ~5 deg CCW (one photo, +-2). The CAD chain has no offset of its own
                          # (CrowPanel pattern 90/210/330, reSpeaker holes symmetric, mute button up under
                          # the plunger), so this is a FIXED offset in Elecrow's panel or the print, not
                          # play. The firmware has no trim (75f142a); if 12 sits X deg CCW, add -X.

# light ring: hollow channel lined with aluminium foil tape (ring_base inner wall + ring_shell)
LG_KNOB_GAP   = 0.45                           # radial gap knob -> ring
RING_BORE_R   = 44.4      # front-shell bore around the ring (0.6 mm gap: both parts can sit 0.2-0.3 off-centre)
RING_PROUD    = 2.35      # ring top above the sphere surface at the bore (top stays z 36.88)
RING_SLV_RI, RING_SLV_RO = 42.8, 43.8          # ring_shell sleeve (outer wall of the channel)
RING_CAP_T    = 1.4       # diffuser cap (printed face-down on textured PEI)
RING_CAP_RI   = 41.2      # cap inner edge (0.25 mm round the inner wall's top; crush ribs bite 0.15)
RING_IW_T     = 1.0       # inner wall thickness
RING_IW_R0    = 37.4      # inner wall inner radius, z 0..4.1 (inside the LED capacitors)
RING_IW_R1    = 38.3      # z 5.0..26.35 (clear of the spider pads, r 38.0)
RING_IW_R2    = CP_KNOB_R + LG_KNOB_GAP        # 39.95, z 28.0.. (knob gap)
RING_IW_Z     = (4.1, 5.0, 26.35, 28.0)        # 45 deg transitions between the three radii
RING_CAP_NOTCH = (2.2, 0.8)                    # w, h: notches in the inner wall foot over the capacitors
RING_CABLE_NOTCH = (5.0, 2.0)                  # w, h: CrowPanel lead under both walls at NOTCH_ANG
RING_BOSS_D   = 6.5       # integral board spacers on the 3 clamp screws
RING_BOSS_HOLE = 2.25
RING_WEB_H    = 4.0
RING_KEY_ANG  = [0.0, 200.0]                   # ring_shell tabs -> ring_base slots (unique)
RING_CRUSH_ANG = [60.0, 180.0, 300.0]          # crush ribs under the cap's inner edge
NOTCH_ANG     = 120.0                          # cable notch: between LEDs 105/135, clear of the jack/USB

# spider bracket + reSpeaker clamp
STANDOFF_L    = 5.0       # board front -> spider plate (ring_base bosses)
SPIDER_T      = 3.0
SPIDER_PILLAR = 1.5
SPIDER_HUB_R  = 9.6
ARM_W         = 7.0
M2_CLR        = 2.4
M3_CLR        = 3.1       # was 3.3: a closer fit for the CrowPanel screws. Only the last 2 mm; d3.4 below
M2_CLAMP_LEN  = 20.0
CARRIER_CB    = 2.0

# carrier (bulkhead behind the board; hangs on the 3 M2 clamp screws, keyed by the cradle ribs)
CARRIER_Z0    = -14.5
CARRIER_T     = 2.5
CARRIER_FRONT = CARRIER_Z0 + CARRIER_T         # -12.0
CARRIER_R     = 51.0
CARRIER_M2_CLR = 2.2      # tight only in the top 2 mm of each boss (d2.5 below): sets the angle without drag
CARRIER_KEY_CLR = 0.2     # per side, carrier notch on the key rib (+-0.23 deg; 0.12 would bind as printed)

# heat-set inserts (3DZWMAN D3 hole sizes)
M3_INSERT_D   = 4.0       # (insert coupon only)
M2_INSERT_L   = 3.0       # M2 x 3 x OD3.2
M2_INSERT_D   = 2.9
INSERT_CHAMFER = 0.3
SCREW_MARGIN  = 2.5       # free hole below every screw tip (molten plastic from setting the insert)

# cradle + key ribs: the 4 ribs centre the board (r CRADLE_R), carry its back face (pads) and run
# down the wall to KEY_Z0 so the carrier's notches key the whole stack
CRADLE_ANG    = [25.0, 150.0, 255.0, 300.0]
CRADLE_R      = 50.15
CRADLE_PAD_R  = 48.4
CRADLE_W      = 5.0
KEY_Z0        = -16.0

# front <-> rear bayonet (rear collar + lugs, front blocks)
TW_ANGLE      = 10.0      # front shell turns this far CLOCKWISE (seen from the front) to lock
TW_LUGS       = [(345.0, 10.0), (25.0, 10.0), (75.0, 10.0), (100.0, 10.0),
                 (154.5, 9.0), (242.4, 6.4), (305.0, 9.0)]   # (lock angle, lug span) deg
TW_STOPS      = [25.0, 154.5]                  # blocks that land on a stop post
COL_RI, COL_RO = 51.4, 53.2                    # collar (JST header r 51.1, reset button r 51.7 in a gap)
COL_TOP       = 6.6
COL_FLANGE_R  = 56.6                           # flange under the collar, 45 deg underside
LUG_Z0        = 3.3       # lug bearing face (flat)
LUG_FLAT      = 0.8       # flat part of the lug underside (then 45 deg to the tip); <= 0.8 mm overhang
LUG_RO        = 54.7
BLK_RI        = 53.55     # front blocks: SPLIT_Z..BLK_TOP, r BLK_RI..wall (0.35 to the collar: ~0.1 as printed)
BLK_TOP       = 3.1       # 0.2 mm axial clearance under the lugs (the mic gaskets take it up)
TW_GROOVE_R   = 55.05     # front inner wall relieved for the lug tips' sweep
TW_STOP_RO    = 54.8
TW_FINGERS    = [345.0, 25.0, 75.0, 100.0]     # blocks that carry a radial flexure detent finger
FING_T        = 0.9       # finger r BLK_RI..BLK_RI+FING_T, cut free by a kerf to FING_KERF_RO
FING_KERF_RO  = BLK_RI + FING_T + 0.8
FING_LEN      = 6.5       # mm, from the block's CCW (free) end
FING_BUMP_R   = 53.05     # bump apex: rides the collar face (r COL_RO) 0.15 nominal, ~0.35 as printed
COL_GROOVE_R  = 52.75     # V-groove bottom in the collar face (lock and entry positions)
TW_EXCL       = [(162.0, 218.0), (246.0, 296.0), (115.0, 125.0)]   # USB-C/jack, base flat (front floor sweeps it), cable

# back plate bayonet
BP_LIP_T      = 2.0       # lip at the rear shell's back opening (on its bed)
BP_LIP_RI     = 35.0
BP_SPIG_RI, BP_SPIG_RO = 33.0, 34.5            # 0.5 to the lip bore (~0.25 as printed)
BP_LUG_RO     = 35.9
BP_LUG_H      = 2.4
BP_LUGS       = [(90.0, 30.0), (210.0, 22.0), (330.0, 22.0)]   # (lock angle, span): wide lug keys it
BP_TWIST      = 32.0      # plate turns CCW about +Z (= clockwise seen from the back) to lock
BP_NOTCH_RO   = 36.6
BP_SPIG_GAP   = (238.0, 302.0)                 # no spigot round the USB-C wall
BP_PAWLS      = [10.0, 130.0]                  # free-end (tooth) angles of the 2 flexure pawls
BP_PAWL_LEN   = 24.0      # deg (about 14 mm)
BP_PAWL_R     = (33.2, 34.4)                    # arm 1.2 thick; 1.5 mm of room inside it in the slot
BP_PAWL_SLOT  = (31.7, 34.95)                  # 1.3 mm inside the arm: 0.85 mm deflection + margin
BP_COIN       = (20.0, 2.0, 1.5, 27.5)         # coin slot on the outer face: length, width, depth, y

# ballast: a pocket low in the rear shell, behind the carrier, filled with steel shot in epoxy
# (about 180 g) or tungsten putty (about 340 g). Open at the top; fill to 1 mm below the rim.
BAL_ARC       = (200.0, 340.0)
BAL_T         = 1.2
BAL_TOP       = CARRIER_Z0 - 2.0                # -16.5: 2 mm below the carrier
BAL_R_LOW     = 37.5                           # skin radius near the back (clears the back plate's lugs,
BAL_R_HIGH    = 30.0                           # USB-C wall and screw tips while it turns), then 45 deg in
BAL_Z_STEP    = -36.2                          # to r 30 (clear of the speaker and the USB-C board's top)

# grip pads: TPU pads in shallow recesses in the flat base (both shells)
PAD_INSET     = 2.5       # from the edge of the flat
PAD_SEAM_GAP  = 1.5       # each side of the seam
PAD_RECESS    = 0.8
PAD_T         = 1.2       # stands PAD_T - PAD_RECESS = 0.4 mm proud
PAD_CLR       = 0.2
PAD_RESET_NOTCH = (7.5, -8.0)                  # |u| < 7.5, w < -8: the floor under the reset pocket is thin

# mic channels / boots
MIC_BORE      = 2.0
MIC_LUG_Z0    = SPLIT_Z   # boot underside (on the front shell's bed); 1/16" foam 1.6 -> 1.1
MIC_CH_Z      = 3.0
BOOT_RI       = 44.5
BOOT_SLIM_R   = 50.4      # beyond here the boot is a 5 mm bar below BOOT_SLIM_Z (collar gaps)
BOOT_TUBE_W   = 5.0
BOOT_SLIM_Z   = COL_TOP + 0.4

# mute plunger (rear shell, D 90 deg)
PLG_Z         = -3.3
PLG_ROD_R     = 1.8
PLG_BORE_R    = 2.0
PLG_CAP_R     = 2.8
PLG_CB_R      = 3.1
PLG_GAP       = 0.25
PLG_TRAVEL    = 1.0
PLG_PROUD     = 0.6
PLG_BOSS_R0   = 53.0

# speaker: 4428 3 W 8 ohm, from ../decive files/speaker_4428_3W8R.step
SPK_STEP      = VENDOR / "speaker_4428_3W8R.step"
SPK_BODY      = (28.2, 31.0, 15.3)
SPK_EAR_PITCH = 36.7
SPK_EAR_T     = 2.4
SPK_EAR_FROM_FACE = 15.3 - 6.9
SPK_CONE_R    = 13.0
SPK_CY        = 0.0
SPK_GASKET    = 1.1
TPU_WASHER_T  = 1.0
SPK_SCREW_L   = 10.0      # M2 x 10 (the shortest in the kit)
SPK_HOLE_SKIN = 1.0       # insert hole runs into the plate, leaving this much on the outer face
# USB-C inlet: 6-pin breakout with 5.1k CC resistors (measured 3 Nov 2026)
USB_CY        = -22.0     # moved 5 mm up from v1 so the wall clears the bayonet lip
USB_SLOT      = (9.4, 3.6)
USB_RECESS    = (13.5, 8.0, 1.6)
USB_PCB       = (21.96, 13.11, 1.61)
USB_SOCKET_H  = 3.30
USB_HOLE_D    = 2.5                            # estimate
USB_HOLE_PITCH= 18.95 - USB_HOLE_D
USB_HOLE_Z    = 1.61 + USB_HOLE_D / 2
USB_WALL_T    = 6.0       # backing wall with 2 horizontal M2 inserts (through holes)
USB_WALL_H    = 10.0
USB_SCREW_L   = 10.0

# ---------------------------------------------------------------- derived
C_Z    = FACE_Z - sqrt(SPHERE_R**2 - FACE_R**2)          # sphere centre z (-2.79)
R_IN   = SPHERE_R - WALL
UP_D   = Vector(0, cos(radians(TILT)), sin(radians(TILT)))
CEN    = Vector(0, 0, C_Z)
FOOT_H = CEN.dot(UP_D) - sqrt(SPHERE_R**2 - FOOT_R**2)   # base plane (along UP_D)
FLOOR_TOP = FOOT_H + FLOOR
BACK_Z = C_Z - SPHERE_R * cos(radians(BACK_LAT))         # rear shell ends / back plate inner face
FRONT_EDGE_Z = C_Z + sqrt(SPHERE_R**2 - RING_BORE_R**2)  # sphere meets the ring bore (34.88)
RING_TOP_Z = FRONT_EDGE_Z + RING_PROUD                   # 36.88
BP_LUG_Z0 = BACK_Z + BP_LIP_T + 0.2
_UPv = (UP_D.X, UP_D.Y, UP_D.Z)
FOOT_C = Vector(*[c + (FOOT_H - CEN.dot(UP_D)) * u for c, u in zip((0.0, 0.0, C_Z), _UPv)])   # centre of the flat
FOOT_ET = UP_D.cross(Vector(1, 0, 0))                                   # in-plane axis toward the back
PAD_W_SEAM = (SPLIT_Z - FOOT_C.Z) / FOOT_ET.Z                           # seam line in the flat (w coordinate)
BP_LUG_Z1 = BP_LUG_Z0 + BP_LUG_H


def r_in_at(z):
    """Inner wall radius of the sphere at height z."""
    return sqrt(R_IN ** 2 - (z - C_Z) ** 2)


def r_out_at(z):
    return sqrt(SPHERE_R ** 2 - (z - C_Z) ** 2)


def polar(r, ang):
    return (r * cos(radians(ang)), r * sin(radians(ang)))


def rot2(p, ang):
    a = radians(ang)
    return (p[0] * cos(a) - p[1] * sin(a), p[0] * sin(a) + p[1] * cos(a))


def rs_holes():
    return [rot2(p, RS_ROT) for p in RS_HOLES_DRAW]


def cp_screws():
    return [rot2(p, CP_ROT_TRIM_DEG) for p in CP_SCREWS_NOM]


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
    c = Cone(r1, r2, r1_pos - r0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    c = Rot(0, 90, 0) * c
    return Rot(0, 0, ang) * (Pos(r0, 0, z) * c)


def rz_profile(pts, ang, half_w):
    """Polygon in the (r, z) half-plane, extruded +-half_w tangentially, rotated to ang."""
    f = Plane.XZ * Polygon(*pts, align=None)
    return Rot(0, 0, ang) * extrude(f, amount=half_w, both=True)


def tz_prism(pts, ang, r0, r1):
    """Polygon in the (tangential, z) plane at direction `ang`, extruded radially from r0 to r1."""
    f = Plane.YZ * Polygon(*pts, align=None)
    return Rot(0, 0, ang) * (Pos(r0, 0, 0) * extrude(f, amount=r1 - r0))


def xy_prism(rt_pts, z0, z1):
    """Polygon given as (r, angle deg) points in the XY plane, extruded z0..z1."""
    xy = [polar(r, a) for r, a in rt_pts]
    return Pos(0, 0, z0) * extrude(Polygon(*xy, align=None), amount=z1 - z0, dir=(0, 0, 1))   # winding-proof


def revolve_rz(pts):
    """Solid of revolution of an (r, z) polygon about the Z axis."""
    from build123d import revolve, Axis
    return revolve(Plane.XZ * Polygon(*pts, align=None), Axis.Z)


def sector(pts, a0, a1):
    """(r, z) polygon swept CCW from angle a0 to a1 (deg) about +Z."""
    from build123d import revolve, Axis
    span = (a1 - a0) % 360 or 360
    return Rot(0, 0, a0) * revolve(Plane.XZ * Polygon(*pts, align=None), Axis.Z, revolution_arc=span)


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


def arcs_minus(excl, min_span=4.0):
    """Complement of a list of (a0, a1) angle intervals on the circle, as (a0, a1) arcs >= min_span."""
    ivs = []
    for a0, a1 in excl:
        a0 %= 360
        a1 = a0 + ((a1 - a0) % 360)
        ivs += [(a0, a1)] if a1 <= 360 else [(a0, 360.0), (0.0, a1 - 360)]
    ivs.sort()
    merged = []
    for a0, a1 in ivs:
        if merged and a0 <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], a1))
        else:
            merged.append((a0, a1))
    free, cur = [], 0.0
    for a0, a1 in merged:
        if a0 > cur:
            free.append((cur, a0))
        cur = max(cur, a1)
    if cur < 360:
        free.append((cur, 360.0))
    if len(free) > 1 and free[0][0] == 0.0 and free[-1][1] == 360.0:   # join across 0 deg
        free = [(free[-1][0], free[0][1] + 360)] + free[1:-1]
    return [(a0, a1) for a0, a1 in free if a1 - a0 >= min_span]


def foot_plane():
    """Local frame of the flat base: x = D x, y = toward the back (w), z = into the part (UP_D)."""
    return Plane(origin=FOOT_C, x_dir=(1, 0, 0), z_dir=UP_D)


def pad_shape(side, grow=0.0):
    """2D outline (in the foot plane) of the grip pad on 'front' or 'rear' of the seam."""
    from build123d import Circle, Rectangle
    R = FOOT_R - PAD_INSET + grow
    if side == "rear":
        w0 = PAD_W_SEAM + PAD_SEAM_GAP - grow
        f = Circle(R) & (Pos(0, w0 + 50) * Rectangle(120, 100))
        nu, nw = PAD_RESET_NOTCH
        f = f - (Pos(0, (nw - grow + w0 - 10) / 2) * Rectangle(2 * (nu - grow), (nw - grow) - (w0 - 10)))   # recess: smaller notch
    else:
        w1 = PAD_W_SEAM - PAD_SEAM_GAP + grow
        f = Circle(R) & (Pos(0, w1 - 50) * Rectangle(120, 100))
    return f


def pad_recess(side):
    return foot_plane() * (Pos(0, 0, -1.0) * extrude(pad_shape(side, PAD_CLR), amount=1.0 + PAD_RECESS))


def foot_pad_placed(side):
    return foot_plane() * (Pos(0, 0, PAD_RECESS - PAD_T) * extrude(pad_shape(side), amount=PAD_T))


def foot_pads():
    """Both TPU grip pads, flat for printing (front pad beside the rear one)."""
    rear = extrude(pad_shape("rear"), amount=PAD_T)
    front = Pos(0, -FOOT_R - 6, 0) * extrude(pad_shape("front"), amount=PAD_T)
    return rear + front


def ballast_skin():
    """Inner wall of the ballast pocket (r, z polygon swept over BAL_ARC, with end walls)."""
    lo, hi, za, T = BAL_R_LOW, BAL_R_HIGH, BAL_Z_STEP, BAL_T
    zb = za + (lo - hi)
    skin = [(lo, BACK_Z - 0.01), (lo + T, BACK_Z - 0.01), (lo + T, za - 0.5), (hi + T, zb - 0.5), (hi + T, BAL_TOP),
            (hi, BAL_TOP), (hi, zb), (lo, za)]
    end = [(lo, BACK_Z - 0.01), (SPHERE_R, BACK_Z - 0.01), (SPHERE_R, BAL_TOP), (hi, BAL_TOP), (hi, zb), (lo, za)]
    a0, a1 = BAL_ARC
    return sector(skin, a0, a1) + sector(end, a0, a0 + 1.2) + sector(end, a1 - 1.2, a1)


def ballast_pocket():
    """The empty pocket volume (for checks and the fill estimate)."""
    lo, hi, za, T = BAL_R_LOW, BAL_R_HIGH, BAL_Z_STEP, BAL_T
    zb = za + (lo - hi)
    pts = [(lo + T, BACK_Z), (SPHERE_R, BACK_Z), (SPHERE_R, BAL_TOP - 1.0), (hi + T, BAL_TOP - 1.0), (hi + T, zb - 0.5), (lo + T, za - 0.5)]
    a0, a1 = BAL_ARC
    return sector(pts, a0 + 1.2, a1 - 1.2) & cavity()


def boot_gap_half():
    return degrees((BOOT_TUBE_W / 2) / COL_RI) + 1.0


def collar_arcs():
    h = boot_gap_half()
    excl = list(TW_EXCL) + [(d - h, d + TW_ANGLE + h) for d in (45.0, 135.0, 225.0, 315.0)]
    return arcs_minus(excl)


def in_arcs(a0, a1, arcs):
    for b0, b1 in arcs:
        for k in (-360, 0, 360):
            if b0 <= a0 + k and a1 + k <= b1:
                return True
    return False


def block_span(lug_span):
    return lug_span - 1.5


def stop_post_span(a, lug_span):
    bs = block_span(lug_span)
    return a - bs / 2 - 0.2 - 1.6, a - bs / 2 - 0.2


# ---------------------------------------------------------------- parts
def front_shell():
    env = body_envelope()
    shell = (env & zslab(SPLIT_Z, SPHERE_R + 10)) - cavity()
    shell = shell - cyl(RING_BORE_R, 20.0, SPHERE_R + 10)          # light-ring bore
    shell = shell - pad_recess("front")                            # grip-pad recess in the flat base
    ri, ro = r_in_at(SPLIT_Z), r_out_at(SPLIT_Z)                   # elephant's-foot chamfers on the bed rim
    shell = shell - revolve_rz([(ri - 0.01, SPLIT_Z - 0.01), (ri + 0.3, SPLIT_Z - 0.01), (ri - 0.01, SPLIT_Z + 0.31)])
    shell = shell - revolve_rz([(ro - 0.3, SPLIT_Z - 0.01), (ro + 1.0, SPLIT_Z - 0.01), (ro + 1.0, SPLIT_Z + 1.3)])
    # room for the rear lugs' tips to sweep (only where a lug passes)
    for a, span in TW_LUGS:
        shell = shell - sector([(R_IN - 2, LUG_Z0 - 0.15), (TW_GROOVE_R, LUG_Z0 - 0.15),
                                (TW_GROOVE_R, COL_TOP + 0.3), (R_IN - 2, COL_TOP + 0.3)],
                               a - span / 2 - TW_ANGLE - 0.5, a + span / 2 + 0.5)   # front frame: lug goes a-TW -> a
    # mic boots: wedge lugs on the diagonals (underside on the bed), slimmed to a 5 mm bar where
    # they cross the rear collar band, L-shaped channel
    for ang in (45, 135, 225, 315):
        lug = rz_profile([(BOOT_RI, MIC_LUG_Z0), (SPHERE_R + 1, MIC_LUG_Z0),
                          (SPHERE_R + 1, MIC_LUG_Z0 + 20), (BOOT_RI, MIC_LUG_Z0 + 4.5)], ang, 4.5)
        hw = BOOT_TUBE_W / 2
        for s in (-1, 1):                       # 45 deg shoulders so the full-width part self-supports
            t = [(s * hw, SPLIT_Z - 1), (s * 8.0, SPLIT_Z - 1), (s * 8.0, BOOT_SLIM_Z + (8.0 - hw)),
                 (s * hw, BOOT_SLIM_Z)]
            lug = lug - tz_prism(t if s > 0 else t[::-1], ang, BOOT_SLIM_R, SPHERE_R + 2)
        shell = shell + (lug & env)
    for ang in (45, 135, 225, 315):
        x, y = polar(RS_MIC_R, ang)
        shell = shell - cyl(MIC_BORE / 2, -1, MIC_CH_Z + MIC_BORE / 2, x, y)
        shell = shell - radial_cyl(MIC_BORE / 2, ang, RS_MIC_R, SPHERE_R + 5, MIC_CH_Z)
    # bayonet blocks (built up from the bed); 4 of them carry a radial flexure finger whose bump
    # clicks into a V-groove in the collar at the locked angle (the detent has its own spring)
    for a, span in TW_LUGS:
        bs = block_span(span)
        blk = sector([(BLK_RI, SPLIT_Z), (R_IN + 1.0, SPLIT_Z), (R_IN + 1.0, BLK_TOP), (BLK_RI, BLK_TOP)],
                     a - bs / 2, a + bs / 2)
        blk = blk - sector([(BLK_RI - 0.01, SPLIT_Z - 0.01), (BLK_RI + 0.4, SPLIT_Z - 0.01),
                            (BLK_RI - 0.01, SPLIT_Z + 0.41)], a - bs / 2 - 0.1, a + bs / 2 + 0.1)
        if a in TW_FINGERS:
            k0, k1 = finger_span(a, span)
            blk = blk - sector([(BLK_RI + FING_T, SPLIT_Z - 1), (FING_KERF_RO, SPLIT_Z - 1),
                                (FING_KERF_RO, BLK_TOP + 0.01), (BLK_RI + FING_T, BLK_TOP + 0.01)], k0, k1 + 0.5)
            blk = blk + finger_bump(a, span)
        shell = shell + (blk & env)
    return shell


def finger_span(a, span):
    """Angular extent of the flexure finger (and its kerf): from the block's CCW end back FING_LEN."""
    bs = block_span(span)
    return a + bs / 2 - degrees(FING_LEN / (BLK_RI + FING_T / 2)), a + bs / 2


def finger_bump_angle(a, span):
    return a + block_span(span) / 2 - 0.9


def finger_bump(a, span, grow=0.0, z=None):
    """Bump on the finger's inner face: 30 deg lead on the lock (CW) side, 45 deg on the unlock side."""
    tb = finger_bump_angle(a, span)
    r0, r1 = BLK_RI + 0.05 + grow, FING_BUMP_R - grow
    pts = [(r0, tb - 0.15 - 1.0 - grow * 2), (r1, tb - 0.15), (r1, tb + 0.15), (r0, tb + 0.15 + 0.6 + grow * 2)]
    z0, z1 = z if z else (SPLIT_Z + 0.4, BLK_TOP - 0.2)
    return xy_prism(pts, z0, z1)


def rear_shell():
    env = body_envelope()
    shell = (env & zslab(BACK_Z, SPLIT_Z)) - cavity()

    # bayonet collar (rises past the seam inside the front shell) on a 45 deg flange
    prof = [(COL_RI, COL_TOP), (COL_RO, COL_TOP), (COL_RO, SPLIT_Z), (COL_FLANGE_R, SPLIT_Z),
            (COL_FLANGE_R, SPLIT_Z - (COL_FLANGE_R - COL_RI)), (COL_RI, SPLIT_Z)]
    arcs = collar_arcs()
    for a0, a1 in arcs:
        shell = shell + (sector(prof, a0, a1) & env)
    for a, span in TW_LUGS:
        assert in_arcs(a - span / 2, a + span / 2, arcs), f"lug at {a} is off the collar"
        lug = sector([(COL_RO - 0.01, LUG_Z0), (COL_RO + LUG_FLAT, LUG_Z0),
                      (LUG_RO, LUG_Z0 + (LUG_RO - COL_RO - LUG_FLAT)), (LUG_RO, COL_TOP),
                      (COL_RO - 0.01, COL_TOP)], a - span / 2, a + span / 2)
        # lead-in on the edge the block meets first (the lug's CCW end)
        lug = lug - tz_prism([(0.05, LUG_Z0 - 0.05), (-0.8, LUG_Z0 - 0.05), (0.05, LUG_Z0 + 0.8)],
                             a + span / 2, COL_RO - 0.5, LUG_RO + 0.5)
        shell = shell + lug
    for a in TW_FINGERS:                               # V-grooves for the finger bumps: locked + entry
        span = dict(TW_LUGS)[a]
        shell = shell - collar_groove(a, span, 0.0, (SPLIT_Z - 0.5, LUG_Z0 - 0.01))
        shell = shell - collar_groove(a, span, TW_ANGLE, (SPLIT_Z - 0.5, COL_TOP + 1.0))
    for a in TW_STOPS:
        span = dict(TW_LUGS)[a]
        s0, s1 = stop_post_span(a, span)
        assert in_arcs(s0, s1, arcs), f"stop post at {a} is off the collar"
        shell = shell + sector([(COL_RO - 0.01, SPLIT_Z - 1.0), (TW_STOP_RO, SPLIT_Z - 1.0),
                                (TW_STOP_RO, LUG_Z0 + 0.5), (COL_RO - 0.01, LUG_Z0 + 0.5)], s0, s1)

    # cradle + key ribs: centring face r CRADLE_R over the PCB edge, pad under the PCB back, then
    # down the wall to KEY_Z0 where the carrier's notches engage them
    for ang in CRADLE_ANG:
        rw = SPHERE_R
        pts = [(CRADLE_PAD_R, -RS_T), (CRADLE_R, -RS_T), (CRADLE_R, 0.0), (CRADLE_R + 0.6, 0.6),
               (rw, 0.6), (rw, KEY_Z0 - (rw - CRADLE_PAD_R)), (CRADLE_PAD_R, KEY_Z0)]
        shell = shell + (rz_profile(pts, ang, CRADLE_W / 2) & env)

    # mute plunger: guide boss + bore + outside counterbore at 12 o'clock
    boss = radial_cyl(4.0, 90, PLG_BOSS_R0, SPHERE_R - 0.5, PLG_Z) & zslab(-50, SPLIT_Z)
    shell = shell + (boss & env)
    cb_floor = SPHERE_R + PLG_PROUD - 1.5 - PLG_TRAVEL
    shell = shell - radial_cyl(PLG_BORE_R, 90, PLG_BOSS_R0 - 1, SPHERE_R + 3, PLG_Z)
    shell = shell - radial_cyl(PLG_CB_R, 90, cb_floor, SPHERE_R + 3, PLG_Z)

    # floor pocket under the reset button + PCB tab (6 o'clock)
    r0, r1, z0, z1 = RS_BTN_BODY
    pocket = radial_box(270, r0 - 0.5, RS_RST_TIP_R + 1.5, 12.0, z0 - 0.8, SPLIT_Z + 0.5)
    shell = shell - (pocket & half(UP_D, FOOT_H + 0.9))

    # ballast pocket (steel shot in epoxy / tungsten putty), low and behind the carrier
    shell = shell + (ballast_skin() & env & zslab(BACK_Z, BAL_TOP))
    # grip-pad recess in the flat base
    shell = shell - pad_recess("rear")

    # back plate bayonet: lip at the back opening (on the bed) + entry notches + pawl detent notches
    rl = r_in_at(BACK_Z + BP_LIP_T) + 1.0
    lip = revolve_rz([(BP_LIP_RI, BACK_Z), (rl, BACK_Z), (rl, BACK_Z + BP_LIP_T), (BP_LIP_RI, BACK_Z + BP_LIP_T)])
    shell = shell + (lip & sphere_out())
    shell = shell - revolve_rz([(BP_LIP_RI - 0.01, BACK_Z - 0.01), (BP_LIP_RI + 0.3, BACK_Z - 0.01),
                                (BP_LIP_RI - 0.01, BACK_Z + 0.31)])          # elephant's-foot chamfer
    shell = shell - sector([(BP_LIP_RI - 0.01, BACK_Z + BP_LIP_T + 0.01), (BP_LIP_RI + 0.5, BACK_Z + BP_LIP_T + 0.01),
                            (BP_LIP_RI - 0.01, BACK_Z + BP_LIP_T - 0.5)], 223.0, 287.0)   # USB screw tips pass here
    for a, span in BP_LUGS:
        e0, e1 = a - span / 2 - BP_TWIST - 1.5, a + span / 2 - BP_TWIST + 1.5
        shell = shell - sector([(BP_LIP_RI - 1, BACK_Z - 1), (BP_NOTCH_RO, BACK_Z - 1),
                                (BP_NOTCH_RO, BACK_Z + BP_LIP_T + 0.5), (BP_LIP_RI - 1, BACK_Z + BP_LIP_T + 0.5)],
                               e0, e1)
    for t in BP_PAWLS:
        shell = shell - pawl_tooth_xy(t, grow=0.15, z=(BACK_Z - 1, BACK_Z + BP_LIP_T + 1))
    # hard stop: the wide lug's CCW end lands on a post on the lip
    a, span = BP_LUGS[0]
    shell = shell + sector([(BP_LIP_RI, BACK_Z + BP_LIP_T - 0.01), (BP_NOTCH_RO + 0.4, BACK_Z + BP_LIP_T - 0.01),
                            (BP_NOTCH_RO + 0.4, BP_LUG_Z1 + 0.3), (BP_LIP_RI, BP_LUG_Z1 + 0.3)],
                           a + span / 2 + 0.3, a + span / 2 + 2.8)
    return shell


BP_TOOTH_RO = BP_LIP_RI + 0.65                  # tooth apex: 0.65 mm past the lip's inner edge (~0.9 as printed)


def collar_groove(a, span, offset, z):
    tb = finger_bump_angle(a, span) + offset
    pts = [(COL_RO + 0.1, tb - 0.15 - 1.2), (COL_GROOVE_R, tb - 0.3), (COL_GROOVE_R, tb + 0.3), (COL_RO + 0.1, tb + 0.15 + 0.8)]
    return xy_prism(pts, *z)


def pawl_tooth_xy(t, grow=0.0, z=None):
    """Tangential (XY) outline of a pawl tooth at angle t: steep face on the CW side (resists
    unlocking, which turns the plate CW about +Z), gentler ramp on the CCW side."""
    r_lo, r_hi = BP_PAWL_R[1] - 0.1 - grow, BP_TOOTH_RO + grow
    pts = [(r_lo, t - 1.6 - grow * 3), (r_hi, t + 0.5), (r_hi, t + 1.0), (r_lo, t + 3.0 + grow * 3)]   # unlock face ~40 deg
    z0, z1 = z if z else (BACK_Z - 1.0, BACK_Z + 1.9)
    return xy_prism(pts, z0, z1)


def pawl_tooth(t):
    """Tooth = XY outline cut to a symmetric 45 deg (r, z) profile: the upper ramp lets the plate be
    pushed straight in (the arm flexes), the lower ramp prints without support."""
    r1 = BP_PAWL_R[1]
    zc = BACK_Z + 0.45
    h = BP_TOOTH_RO - (r1 - 0.2)
    return pawl_tooth_xy(t) & revolve_rz([(r1 - 0.2, zc - h), (BP_TOOTH_RO, zc), (r1 - 0.2, zc + h)])


def back_plate():
    env = body_envelope()
    plate = env & zslab(BACK_Z - BACK_T, BACK_Z)
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
    # ear bosses with M2 inserts; top sits one TPU washer below the ear. The hole runs into the plate.
    boss_top = speaker_boss_top()
    for sxn in (-1, 1):
        bx = sxn * SPK_EAR_PITCH / 2
        plate = plate + cyl(3.4, BACK_Z, boss_top, bx, SPK_CY)
        plate = plate - cyl(M2_INSERT_D / 2, BACK_Z - BACK_T + SPK_HOLE_SKIN, boss_top + 1, bx, SPK_CY)
        plate = plate - Pos(bx, SPK_CY, boss_top - INSERT_CHAMFER) * Cone(
            M2_INSERT_D / 2, M2_INSERT_D / 2 + INSERT_CHAMFER + 0.01, INSERT_CHAMFER + 0.01,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
    # USB-C inlet: slot + outside overmould recess; board stands on edge against a backing wall with
    # 2 horizontal M2 heat-set inserts (through holes, so the screw tip has room)
    rx, ry, rd = USB_RECESS
    plate = plate - Pos(0, USB_CY, BACK_Z - 2) * Box(*USB_SLOT, 6)
    plate = plate - Pos(0, USB_CY, BACK_Z - BACK_T - 0.01) * Box(rx, ry, rd, align=(Align.CENTER, Align.CENTER, Align.MIN))
    L, Hb, T = USB_PCB
    y_top, y_bot = usb_pcb_y()
    wall_l = L + 2 * 2.2
    wall = Pos(0, y_bot - USB_WALL_T / 2, BACK_Z) * Box(wall_l, USB_WALL_T, USB_WALL_H,
                                                       align=(Align.CENTER, Align.CENTER, Align.MIN))
    plate = plate + wall
    for sx in (-1, 1):                                 # end stops locate the board's length
        xs = sx * (L / 2 + 0.2 + 1.0)
        plate = plate + Pos(xs, (y_bot + y_top) / 2 + 0.5, BACK_Z) * Box(2.0, T + 1.2, 6.0,
                                                                        align=(Align.CENTER, Align.CENTER, Align.MIN))
    for sx in (-1, 1):
        hx = sx * USB_HOLE_PITCH / 2
        hz = BACK_Z + USB_HOLE_Z
        hole = Pos(hx, y_bot + 0.5, hz) * Rot(90, 0, 0) * Cylinder(M2_INSERT_D / 2, USB_WALL_T + 1.5,
                                                                   align=(Align.CENTER, Align.CENTER, Align.MIN))
        mouth = Pos(hx, y_bot + 0.01, hz) * Rot(90, 0, 0) * Cone(
            M2_INSERT_D / 2 + INSERT_CHAMFER + 0.01, M2_INSERT_D / 2, INSERT_CHAMFER + 0.01,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        mouth2 = Pos(hx, y_bot - USB_WALL_T - 0.01, hz) * Rot(-90, 0, 0) * Cone(
            M2_INSERT_D / 2 + INSERT_CHAMFER + 0.01, M2_INSERT_D / 2, INSERT_CHAMFER + 0.01,
            align=(Align.CENTER, Align.CENTER, Align.MIN))          # inserts go in from the wall's outer face
        plate = plate - hole - mouth - mouth2
    # zip-tie anchor for the speaker lead
    ay = SPK_CY + SPK_BODY[1] / 2 + 10.5
    plate = plate + Pos(0, ay, BACK_Z + 2) * Box(8, 4, 4)
    plate = plate - Pos(0, ay, BACK_Z + 2.4) * Box(10, 2.0, 1.6)
    # bayonet: spigot ring (centres the plate in the lip) + 3 lugs over the lip
    sp_excl = [BP_SPIG_GAP] + [(t - 2.6, t + BP_PAWL_LEN + 0.2) for t in BP_PAWLS]
    for a0, a1 in arcs_minus(sp_excl, min_span=2.0):
        plate = plate + sector([(BP_SPIG_RI, BACK_Z - 0.01), (BP_SPIG_RO, BACK_Z - 0.01),
                                (BP_SPIG_RO, BP_LUG_Z1), (BP_SPIG_RI, BP_LUG_Z1)], a0, a1)
    for a, span in BP_LUGS:
        plate = plate + sector([(BP_SPIG_RO - 0.01, BP_LUG_Z0), (BP_LIP_RI + 0.5, BP_LUG_Z0),
                                (BP_LUG_RO, BP_LUG_Z0 + (BP_LUG_RO - BP_LIP_RI - 0.5)),
                                (BP_LUG_RO, BP_LUG_Z1), (BP_SPIG_RO - 0.01, BP_LUG_Z1)],
                               a - span / 2, a + span / 2)          # 0.8 mm flat shelf, then 45 deg
    # flexure pawls: an arc arm standing on the bed in a through-slot, root at the CCW end,
    # tooth at the free (CW) end clicks into a notch in the lip at the locked angle
    for t in BP_PAWLS:
        s0, s1 = BP_PAWL_SLOT
        zb = BACK_Z - BACK_T
        plate = plate - sector([(s0, zb - 1), (s1, zb - 1), (s1, BP_LUG_Z1 + 1), (s0, BP_LUG_Z1 + 1)],
                               t - 2.4, t + BP_PAWL_LEN)
        for rr in (s0, s1):                          # elephant's-foot chamfers on the slot walls (plate side)
            d = -0.3 if rr == s0 else 0.3
            plate = plate - sector([(rr, zb - 0.01), (rr + d, zb - 0.01), (rr, zb + 0.3)] if d > 0 else
                                   [(rr + d, zb - 0.01), (rr, zb - 0.01), (rr, zb + 0.3)], t - 2.4, t + BP_PAWL_LEN)
        r0, r1 = BP_PAWL_R
        arm = sector([(r0, zb), (r1, zb), (r1, BACK_Z + BP_LIP_T + 0.6), (r0, BACK_Z + BP_LIP_T + 0.6)],
                     t - 1.6, t + BP_PAWL_LEN + 0.6)
        arm = arm - sector([(r0 - 0.01, zb - 0.01), (r0 + 0.3, zb - 0.01), (r0 - 0.01, zb + 0.31)], t - 1.7, t + BP_PAWL_LEN) \
                  - sector([(r1 - 0.3, zb - 0.01), (r1 + 0.01, zb - 0.01), (r1 + 0.01, zb + 0.31)], t - 1.7, t + BP_PAWL_LEN)
        plate = plate + arm
        plate = plate - sector([(s1 - 0.1, zb - 1), (BP_TOOTH_RO + 0.4, zb - 1),
                                (BP_TOOTH_RO + 0.4, BACK_Z + 0.01), (s1 - 0.1, BACK_Z + 0.01)], t - 2.4, t + 3.6)
        plate = plate + pawl_tooth(t)
    # coin slot on the outer (wall-facing, bed) face: turn the plate with a coin
    gl, gw, gd, gy = BP_COIN
    plate = plate - Pos(0, gy, BACK_Z - BACK_T - 0.01) * Box(gl, gw, gd, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return plate


def speaker_boss_top():
    return BACK_Z + SPK_GASKET + SPK_EAR_FROM_FACE - TPU_WASHER_T


def usb_pcb_y():
    y_top = USB_CY - USB_SOCKET_H / 2                  # PCB face carrying the socket
    return y_top, y_top - USB_PCB[2] - 0.15            # 0.15 mm fit clearance


def ring_iw_pts():
    z1, z2, z3, z4 = RING_IW_Z
    R0, R1, R2, T, zt = RING_IW_R0, RING_IW_R1, RING_IW_R2, RING_IW_T, RING_TOP_Z
    return [(R0, 0.0), (R0 + T, 0.0), (R0 + T, z1), (R1 + T, z2), (R1 + T, z3), (R2 + T, z4), (R2 + T, zt),
            (R2, zt), (R2, z4), (R1, z3), (R1, z2), (R0, z1)]


def ring_base():
    """Inner wall of the light channel + the 3 board spacers on the clamp screws. Natural PETG,
    printed upright (spacers on the bed). Wrap aluminium foil tape round its outer face."""
    zt = RING_TOP_Z
    rb = revolve_rz(ring_iw_pts())
    for k in range(12):                                # notches over the LED capacitors
        rb = rb - radial_box(15 + 30 * k - 0.07, RING_IW_R0 - 1, RING_IW_R0 + RING_IW_T + 1,
                             RING_CAP_NOTCH[0], -1, RING_CAP_NOTCH[1])
    rb = rb - radial_box(NOTCH_ANG, RING_IW_R0 - 1, RING_IW_R0 + RING_IW_T + 1, RING_CABLE_NOTCH[0], -1,
                         RING_CABLE_NOTCH[1])
    for (x, y) in rs_holes():
        ang, r = degrees(atan2(y, x)), hypot(x, y)
        rb = rb + cyl(RING_BOSS_D / 2, 0, STANDOFF_L - 0.05, x, y) + radial_box(ang, r, RING_IW_R0 + 0.5, 3.0, 0, RING_WEB_H)
    for (x, y) in rs_holes():
        rb = rb - cyl(RING_BOSS_HOLE / 2, -1, STANDOFF_L + 1, x, y)
        rb = rb - Pos(x, y, -0.01) * Cone(RING_BOSS_HOLE / 2 + 0.41, RING_BOSS_HOLE / 2, 0.41,
                                          align=(Align.CENTER, Align.CENTER, Align.MIN))   # bed-mouth lead-in
    ro = RING_IW_R2 + RING_IW_T
    for a in RING_KEY_ANG:                             # slots for the ring_shell's tabs
        rb = rb - radial_box(a, ro - 0.5, ro + 1, 1.6, zt - 2.0, zt + 1)
    for a in RING_CRUSH_ANG:                           # crush ribs under the cap's inner edge
        rb = rb + radial_box(a, ro - 0.2, RING_CAP_RI + 0.15, 0.8, zt - RING_CAP_T - 0.3, zt)
    return rb


def ring_shell():
    """Outer wall (sleeve) + diffuser cap of the light channel. Natural/clear PETG, printed cap down.
    Line the sleeve's inside with aluminium foil tape up to the front shell's edge."""
    zt = RING_TOP_Z
    pts = [(RING_SLV_RI, 0.0), (RING_SLV_RO, 0.0), (RING_SLV_RO, zt - 0.6), (RING_SLV_RO - 0.6, zt),
           (RING_CAP_RI, zt), (RING_CAP_RI, zt - RING_CAP_T), (RING_SLV_RI, zt - RING_CAP_T)]
    s = revolve_rz(pts)
    s = s - radial_box(NOTCH_ANG, RING_SLV_RI - 1, RING_SLV_RO + 1, RING_CABLE_NOTCH[0], -1, RING_CABLE_NOTCH[1])
    for a in RING_KEY_ANG:
        s = s + radial_box(a, RING_CAP_RI - 0.45, RING_CAP_RI + 0.2, 1.2, zt - 1.8, zt)
    s = s - revolve_rz([(RING_CAP_RI - 0.01, zt + 0.01), (RING_CAP_RI + 0.3, zt + 0.01), (RING_CAP_RI - 0.01, zt - 0.3)])
    return s


def spider():
    """Built in the CrowPanel's own (untrimmed) frame, where its plugs are axis-aligned, then turned
    by CP_ROT_TRIM_DEG about +Z. The reSpeaker holes are counter-rotated so they stay put."""
    z0, z1 = STANDOFF_L, STANDOFF_L + SPIDER_T
    holes = [rot2(p, -CP_ROT_TRIM_DEG) for p in rs_holes()]
    sp = cyl(SPIDER_HUB_R, z0, CP_HUB_FACE_Z)
    sp = sp + cyl(SPIDER_HUB_R + 1.5, z0, z1)
    for (x, y) in holes:
        sp = sp + cyl(4.0, z0, z1, x, y)
        sp = sp + cyl(3.5, z1, z1 + SPIDER_PILLAR, x, y)
        path = _route_arm((x, y))
        clr = min(_seg_box_dist(p, q, bx) for p, q in zip(path[:-1], path[1:]) for bx in CP_KEEPOUT_NOM)
        w = min(ARM_W, 2 * (clr - 1.0) - 0.1)
        assert w >= 5.0, f"spider arm too narrow ({w:.1f} mm)"
        for mid in path[1:-1]:
            sp = sp + cyl(w / 2, z0, z1, *mid)
        for a, b in zip(path[:-1], path[1:]):
            sp = sp + _bar(a, b, w, z0, z1)
        sp = sp - cyl(M2_INSERT_D / 2, z0 - 1, z1 + SPIDER_PILLAR + 1, x, y)     # through: melt and tip room
        sp = sp - cyl(1.8, z0 - 1, z0 + 0.2, x, y)                                  # melt-ridge relief
        sp = sp - Pos(x, y, z0 + 0.19) * Cone(M2_INSERT_D / 2 + INSERT_CHAMFER, M2_INSERT_D / 2, INSERT_CHAMFER,
                                              align=(Align.CENTER, Align.CENTER, Align.MIN))
    for (x, y) in CP_SCREWS_NOM:
        sp = sp - cyl(1.7, z0 - 1, CP_HUB_FACE_Z - 2.0, x, y) - cyl(M3_CLR / 2, CP_HUB_FACE_Z - 2.01, CP_HUB_FACE_Z + 1, x, y)
        sp = sp - cyl(3.1, z0 - 1, z0 + 1.0, x, y)
    for b in CP_KEEPOUT_NOM:
        x0, x1, y0, y1 = b
        sp = sp - Pos((x0 + x1) / 2, (y0 + y1) / 2, z0 - 1) * Box(x1 - x0 + 2, y1 - y0 + 2, 30,
                                                                  align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Rot(0, 0, CP_ROT_TRIM_DEG) * sp


def _bar(a, b, w, z0, z1):
    ax, ay = a
    bx, by = b
    L = sqrt((bx - ax) ** 2 + (by - ay) ** 2)
    ang = degrees(atan2(by - ay, bx - ax))
    return Pos(ax, ay, z0) * Rot(0, 0, ang) * Box(L, w, z1 - z0, align=(Align.MIN, Align.CENTER, Align.MIN))


def _seg_box_dist(a, b, box):
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
    """Hub -> standoff path that keeps every connector plug keep-out clear (CrowPanel frame)."""
    cands = [[(0.0, 0.0), end]]
    ang0 = degrees(atan2(end[1], end[0]))
    for da in range(-60, 61, 3):
        for r in (14, 16, 18, 20, 22, 24):
            cands.append([(0.0, 0.0), polar(r, ang0 + da), end])

    def clearance(path):
        return min(_seg_box_dist(a, b, bx) for a, b in zip(path[:-1], path[1:]) for bx in CP_KEEPOUT_NOM)

    def length(path):
        return sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path[:-1], path[1:]))

    ok = [c for c in cands if clearance(c) >= need]
    if ok:
        return min(ok, key=length)
    return max(cands, key=clearance)


def carrier():
    z0, z1 = CARRIER_Z0, CARRIER_FRONT
    c = cyl(CARRIER_R, z0, z1)
    for (x, y) in rs_holes():
        c = c + cyl(3.25, z1, -RS_T, x, y)
        c = c - cyl(1.25, z0 - 1, -RS_T - 2.0, x, y) - cyl(CARRIER_M2_CLR / 2, -RS_T - 2.01, 0, x, y)
        c = c - cyl(2.2, z0 - 1, z0 + CARRIER_CB, x, y)
    c = c - Rot(0, 0, NOTCH_ANG) * Pos(CARRIER_R - 3, 0, z0 - 1) * Box(8, 6, 10,
                                                                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    c = c - cyl(6.0, z0 - 1, z1 + 1, -12, 0)
    w = CRADLE_W + 2 * CARRIER_KEY_CLR
    for ang in CRADLE_ANG:                              # key notches on the cradle/key ribs, 0.4 mm lead-ins
        c = c - radial_box(ang, CRADLE_PAD_R - 0.2, 60, w, z0 - 1, z1 + 1)
        for zf, sgn in ((z0, 1), (z1, -1)):
            c = c - tz_prism([(-w / 2 - 0.4, zf - sgn * 0.01), (w / 2 + 0.4, zf - sgn * 0.01),
                              (w / 2, zf + sgn * 0.4), (-w / 2, zf + sgn * 0.4)][::sgn], ang, CRADLE_PAD_R - 0.5, 60)
    c = c - sector([(50.0, z0 - 1), (CARRIER_R + 1, z0 - 1), (CARRIER_R + 1, z1 + 1), (50.0, z1 + 1)], 85.0, 95.0)
    # (relief: the installed mute plunger reaches r 50.48 at 90 deg, and the stack drops past it)
    c = c & above_floor()
    return c


def speaker_placed():
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
            for dot in range(col + 1):
                blk = blk - cyl(0.5, 6.6, 8, x - 1.5 + dot * 1.5, y + 4.2)
    for row in range(2):
        for n in range(row + 1):
            blk = blk - Pos(-19.5, -5.5 + row * 11 + n * 2 - row, 3.5) * Box(2, 1, 8)
    return blk


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
    r_shoulder = PLG_BOSS_R0 - 0.05
    ramp = radial_cone(PLG_ROD_R - 0.05, PLG_BORE_R + 0.15, 90, r_shoulder - 1.3, r_shoulder, PLG_Z)
    slot_r0, slot_r1 = r_tip - 0.5, PLG_BOSS_R0 + 1.6
    slot = Pos(0, (slot_r0 + slot_r1) / 2, PLG_Z) * Box(0.8, slot_r1 - slot_r0, 6.0)
    return rod + cap + ramp - slot


# ---------------------------------------------------------------- proxies (render/check only)
def proxies():
    p = {}
    p["cp_knob"] = cyl(CP_KNOB_R, *CP_KNOB_Z)
    p["cp_glass"] = cyl(33.0, 12.4 + CP_Z0, 12.5 + CP_Z0)
    p["cp_pcb"] = cyl(24.0, CP_PCB_REAR_Z, CP_PCB_REAR_Z + 1.0) + cyl(8.4, CP_HUB_FACE_Z, CP_PCB_REAR_Z + 1)
    conn = None
    for (x0, x1, y0, y1) in CP_KEEPOUT_NOM:
        b = Pos((x0 + x1) / 2, (y0 + y1) / 2, CP_REAR_Z) * Box(x1 - x0, y1 - y0, CP_PCB_REAR_Z - CP_REAR_Z,
                                                               align=(Align.CENTER, Align.CENTER, Align.MIN))
        conn = b if conn is None else conn + b
    p["cp_conn"] = Rot(0, 0, CP_ROT_TRIM_DEG) * conn
    rs = cyl(RS_R, -RS_T, 0)
    r0, r1, z0, z1 = RS_BTN_BODY
    for ang, tip in ((90, RS_MUTE_TIP_R), (270, RS_RST_TIP_R)):
        rs = rs + radial_box(ang, r0, tip - 1.0, 7.8, z0, z1)
        rs = rs + radial_box(ang, tip - 1.0, tip, 2.9, -3.75, -2.20)
    rs = rs + radial_box(180, 44.7, RS_EDGE_R, 9.0, -4.5, -0.24)
    rs = rs + radial_box(197, 40.0, RS_EDGE_R - 0.4, 10.0, -6.4, -0.7)
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
    "ring_base": ring_base,
    "ring_shell": ring_shell,
    "spider": spider,
    "carrier": carrier,
    "mute_plunger": plunger,
    "tpu_washers": tpu_washers,
    "foot_pads": foot_pads,
}   # insert_coupon() is kept for reference; the M2 hole size (d2.9) is confirmed on the printer

# print orientation: rotation applied in D frame before dropping to z=0
PRINT_ROT = {
    "front_shell": Rot(0, 0, 0),       # FACE UP: seam rim, boots and bayonet blocks on the bed
    "rear_shell": Rot(0, 0, 0),        # back rim down (collar and lugs at the top)
    "back_plate": Rot(0, 0, 0),        # outer face down
    "ring_base": Rot(0, 0, 0),         # spacers down
    "ring_shell": Rot(180, 0, 0),      # cap face down (frosted by the textured PEI)
    "spider": Rot(0, 0, 0),
    "carrier": Rot(0, 0, 0),
    "mute_plunger": Rot(-90, 0, 0),
    "tpu_washers": Rot(0, 0, 0),
    "foot_pads": Rot(0, 0, 0),         # already flat (built in the foot plane)
}

# parts that get the outer-surface texture (texture.py) and the matching mesh rotations
TEXTURED = ["front_shell", "rear_shell", "back_plate"]
MESH_PRINT_ROT = {}


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
        if only and name not in only:
            continue
        print("building", name, flush=True)
        built[name] = fn()
        pp = to_print(name, built[name])
        export_stl(pp, str(OUT / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.15)
        export_step(pp, str(OUT / f"{name}.step"))
        bb = pp.bounding_box()
        print(f"  {name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
              f"vol {pp.volume/1000:.1f} cm3, solids {len(pp.solids())}", flush=True)
    if only:
        raise SystemExit(0)
    prox = proxies()
    asm = Compound(children=list(built.values()) + list(prox.values()))
    export_step(asm, str(OUT / "assembly_D.step"))
    (OUT / "asm").mkdir(exist_ok=True)
    for old in ("light_guide", "board_spacers", "cp_housing"):
        for f in (OUT / "asm" / f"{old}.stl", OUT / f"{old}.stl", OUT / f"{old}.step"):
            f.unlink(missing_ok=True)
    for name, s in list(built.items()) + list(prox.items()):
        export_stl(s, str(OUT / "asm" / f"{name}.stl"), tolerance=0.05, angular_tolerance=0.2)
    import numpy as np
    import trimesh
    import texture
    for name in TEXTURED:
        raw = OUT / "asm" / f"_{name}_fine.stl"
        export_stl(built[name], str(raw), tolerance=0.02, angular_tolerance=0.1)
        m = trimesh.load(raw)
        raw.unlink()
        t = texture.apply(m)
        bodies = [b for b in t.split(only_watertight=False) if b.is_watertight and b.volume > 1.0]
        assert len(bodies) == 1, (name, len(bodies))
        t = texture.clean(bodies[0])
        assert t.is_watertight and t.volume > 0, name
        t.export(OUT / "asm" / f"{name}.ply")
        p = t.copy()
        p.apply_transform(MESH_PRINT_ROT.get(name, np.eye(4)))
        bb = p.bounds
        p.apply_translation([-(bb[0][0] + bb[1][0]) / 2, -(bb[0][1] + bb[1][1]) / 2, -bb[0][2]])
        p.export(OUT / f"{name}.ply")
        p.export(OUT / f"{name}.stl")
        print(f"  textured {name} ({texture.TEXTURE}, {texture.DEPTH} mm): {len(p.faces)} faces, "
              f"vol {p.volume/1000:.1f} cm3", flush=True)
    print("derived: sphere centre z=%.2f  base(UP)=%.2f  floor top=%.2f  back z=%.2f  ring top z=%.2f  front edge z=%.2f"
          % (C_Z, FOOT_H, FLOOR_TOP, BACK_Z, RING_TOP_Z, FRONT_EDGE_Z))
