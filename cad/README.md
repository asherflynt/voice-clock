# Voice Clock CAD

A parametric [build123d](https://github.com/gumyr/build123d) model of the enclosure described in [`../docs/build-plan.md`](../docs/build-plan.md).

**v3 light-sensor variant (13 Nov 2026, UNTESTED: CAD and checks only, not printed).** It's off by default, so the default build is the printed v2. Build it with `VC_LIGHT_SENSOR=1 .venv/bin/python voice_clock.py` (and the same for `check.py`, `make_3mf.py` and the rest). It adds an ambient light sensor: Adafruit's right-angle VEML7700 (#5378, STEP in `vendor/`, MIT) on a pad with 2 M2 inserts at the top of the rear shell, behind the carrier, looking out of a Ø2.4 window (flared to Ø5) 15° behind vertical. A shroud on the inner wall closes the gap between the sensor and the curved wall, and a 5 mm notch in the carrier's rim at 60° carries its lead to the XIAO. All of it is in the `LUX_*` constants; `check.py` has a section for it.

**v2 (6 Nov 2026)** fixes everything the first wood print showed up:
- **Shells twist-lock.** The front and rear shells use a 7-lug bayonet with 4 flexure detent fingers, and the back plate a 3-lug bayonet with two flexure pawls. v1's pull-apart snaps are gone.
- **The board stack is keyed.** It can't turn in the case.
- **New light ring.** It's a hollow channel standing proud of the sphere. The channel walls print in white PETG, which reflects the LED light, so there's no foil to fit; only the glowing band is natural PETG.
- **No flat front face.** The front shell prints face-up.
- **Heat-set inserts** hold the USB-C board and the speaker.
- **New wood-grain process** for the wood variant.

## Setup

```bash
cd cad
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python voice_clock.py   # builds every part -> out/*.stl, *.step, assembly_D.step (about 10 s)
.venv/bin/python check.py         # clashes vs the vendor reSpeaker STEP, both twist locks stepped through, keys, screws (about 4 min)
.venv/bin/python make_3mf.py      # Snapmaker U1 -> out/VoiceClock_U1.3mf (4 plates) + out/plates/ fallbacks
.venv/bin/python render.py        # quick numpy previews -> out/render_*.png
.venv/bin/python fit_tests.py     # draft fit-test set (shell bands at every interface + small parts) -> out/fit_tests/
```

Turned-wood variant (Snapmaker Orca must be installed as a flatpak; set `VOICE_CLOCK_HOME` to your real home if `$HOME` isn't it):

```bash
.venv/bin/python wood.py            # painted wood skin -> out/wood/
.venv/bin/python wood_project.py    # Orca presets + project 3MF + sliced G-code
.venv/bin/python coupons.py         # test coupon C1 (wood tone vs temperature) -> out/wood/coupons/
.venv/bin/python wood.py walnut_fs                  # turned walnut, Full Spectrum (8 tones) -> out/wood_walnut_fs/
.venv/bin/python wood_project.py walnut_fs          # 0.08 mm project + G-code
.venv/bin/python fs_swatch.py walnut_fs             # 8-tone swatch to print first
.venv/bin/python blender/wood_scene.py walnut_fs    # then render the hero_walnut_fs_* scenes
# (wood.py walnut / wood_project.py walnut: the earlier 3-tone walnut with cherry lines, superseded)
```

Every dimension is a named constant at the top of `voice_clock.py`. Values marked **VERIFY** come from vendor CAD or drawings, not calipers.

## Parts and how they print (all without supports)

| Part | Plate / slot | Orientation | Notes |
|---|---|---|---|
| front_shell | 1 → slot 2 (PLA) | **Face up** (seam on the bed) | Sphere runs up to the light-ring bore. 7 bayonet blocks and the 4 mic boots print on the bed. The mic channels (`mic_channel()`) have pointed roofs (a cone up the vertical leg, a 55° ridge on the radial leg), so no ceiling is flatter than 45° and nothing bridges. 5 mm brim |
| rear_shell | 1 → slot 2 (PLA) | Back rim down | Bayonet collar and 7 lugs at the top, 4 full-height key ribs, **ballast pocket** (about 30 cm³, low behind the carrier), grip-pad recess, mute guide boss, back-plate lip at the bed. **v3 variant, untested:** light-sensor pad (flat top, vertical inner face) with 2 M2 inserts, the window (teardrop roof) and its shroud (45° underside), all printable without supports. 5 mm brim |
| back_plate | 1 → slot 2 (PLA) | Outer face down | 3 bayonet lugs, 2 flexure pawls, coin slot, 4 M2 inserts (speaker 2, USB-C 2). The USB-C board's socket side bears on 2 pads (bosses round its holes only); its screws go in from the rim side, where a hex key comes straight in over the plate |
| mute_plunger | 1 (PLA) or 3 (white PETG) | Cap down | 100% infill. Use the PETG one if you have it: its snap barb is tougher |
| ring_base | 3 → slot 2 (white PETG) | Spacers down | Light-channel inner wall (its white face is the inner reflector) plus the 3 board spacers on the clamp screws |
| ring_shell | 3 → slot 1 natural + slot 2 white PETG, one print | Cap down | One object, two colours: natural PETG for the cap and the band above the sphere (z ≥ `RING_SPLIT_Z`), white PETG for the rest of the sleeve. A 1.4 mm diffuser cap (frosted by the textured PEI). The cap spans the whole ring and overlaps the inner wall's top, so there is no gap at the face and no straight view down to the LEDs |
| carrier | 2 → slot 2 (PLA) | Back face down | Bulkhead; its 4 notches key the stack on the rear shell's ribs. **v3 variant, untested:** 5 mm lead notch in the rim at 60° (about 1 o'clock) |
| spider | 2 → slot 2 (PLA) | Plate down | 100% infill. CrowPanel pattern turned by `CP_ROT_TRIM_DEG` |
| foot_pads | 4 → slot 4 (TPU) | Flat | 2 grip pads for the recesses in the flat base (glue in with CA). They stand 0.4 mm proud |
| tpu_washers | 4 → slot 4 (optional) | Flat | 4 speaker isolation washers |

**Suggested U1 settings:**
- **Shells:** matte PLA (or the wood variant). 0.2 mm layers, 4 walls, 20% gyroid.
- **Structural internals (carrier, spider):** the same matte PLA as the shells. PLA is somewhat stiffer than PETG (about 1.3× the tensile modulus) and, more usefully, prints the 0.2 mm key notches and the insert holes more accurately. Inside the sphere the boards should keep it well under PLA's softening point (about 55 °C), and the shells already rely on that.
- **Light ring:** PETG in two colours on plate 3: white in slot 2 for the channel walls (diffuse reflector; v2's foil tape was too fiddly and ate the tolerances) and natural/clear in slot 1 for the diffuser band. The crush-rib press fit likes PETG's give. `slice_ring.py` slices this plate for the U1 (no brim, no skirt). The walls do the work; no special infill is needed. **Not** 100% solid, like v1's ring: in v2 the light travels through air.
- **Inserts:** all 7 M2 inserts now go into PLA (spider and back plate): set the iron to about 190–200 °C.
- **Files:** `out/VoiceClock_U1.3mf` holds all 4 plates (PLA externals, PLA internals, PETG light ring, TPU). The 3MFs are model-only, so your own printer, process and filament presets stay selected.

## Hardware

| Qty | Screw | Where | Engaged |
|---|---|---|---|
| 3 | M3 × 12 socket head | Spider → CrowPanel hub (replaces the 3 stock screws) | 1.8 mm, same depth as Elecrow's own screws |
| 3 | M2 × 20 socket head | Carrier → reSpeaker → ring_base spacer → M2 insert in the spider | 2.5 mm |
| 2 | M2 × 10 socket head | Speaker ears: head, TPU washer, ear, TPU washer, boss insert | 3.0 mm; 4.4 mm of hole below the tip |
| 2 | M2 × 10 socket head | USB-C breakout, from the rim side → M2 inserts at the far face of its 2 pads (through holes) | 3 mm insert, tip 2.4 mm past the pad and 7.8 mm short of the speaker |
| (2) | M2 × 6 socket head | light-sensor variant only: board → M2 inserts in its pad, straight in from the front while the rear shell is empty | 3 mm; 2.5 mm of hole below the tip. M2 × 8 or longer would break through the shell |

| Qty | Insert (M2 × 3 × Ø3.2, hole Ø2.9) | Where |
|---|---|---|
| 7 (+2) | | Spider underside 3, speaker bosses 2, USB-C pads 2 (pressed in horizontally from the pads' speaker-side face); light-sensor variant: pad 2 (vertically, from the front) |

**Also needed:**
- 1/16" adhesive closed-cell foam: 4 mic gaskets Ø5 with a Ø2 hole, stuck **to the front shell's mic boots**, plus a speaker-face ring.
- **Ballast:** about 160 g of steel BBs or shot (4.5 mm airgun BBs are cheap) with **slow-cure (30 min or longer) epoxy**, or about 300 g of tungsten putty. Modelling clay only adds about 55 g.
- **CA glue** for the TPU grip pads.
- Wire, the MX1.25 pigtail and heat shrink.
- **v3 variant, untested:** Adafruit #5378 right-angle VEML7700 board and a 100–150 mm STEMMA QT / Qwiic cable.

## Assembly order

Full steps are in [`../docs/assembly/ASSEMBLY.md`](../docs/assembly/ASSEMBLY.md).

1. Fit the 7 M2 inserts (9 with the light-sensor variant).
2. Make the power harness and bench-test both boards.
3. Swap the CrowPanel's 3 rear screws for M3 × 12 through the spider.
4. **Light ring, part 1.**
   - No foil: the white PETG walls are the reflector. The wall's foot sits inside the LED capacitors, so it has no notches.
   - Slide it over the spider from behind. There is no cable notch: the CrowPanel's lead comes from the reSpeaker's LED side, so it stays inside the ring.
5. reSpeaker (mute "A" at 12 o'clock), carrier, 3 × M2 × 20 into the spider (snug only).
6. **Light ring, part 2.** Press the ring_shell on over the knob: tabs into the slots.
7. **Ballast** (before the stack goes in): stand the rear shell on its back rim and fill the pocket along the bottom of the shell to 1 mm below its rim. Use steel shot stirred into slow-cure epoxy, poured in two layers so the epoxy doesn't heat the PLA (it softens around 55 °C), or press in tungsten putty and skim it with a little epoxy. Let it cure, then glue the 2 TPU grip pads into the recesses in the flat base.
8. Click the mute plunger into the rear shell. **v3 variant, untested:** screw the light-sensor board onto its pad (2 × M2 × 6, straight down through the front opening) and plug in its lead. Drop the stack in: the carrier's notches go over the 4 ribs, and the sensor lead lies in the carrier's rim notch.
9. **Front shell.**
   - Stick the 4 mic gaskets onto the boots.
   - Set the shell on turned 10° anticlockwise (seen from the front), so the base flats are offset by a finger's width.
   - Press it down and turn it **clockwise** until the 4 detent fingers click and the flats line up.
10. USB-C board and speaker onto the back plate, in either order: the USB-C screws go in from the rim side. The speaker sits 6 mm off-centre, away from the USB-C board, so its JST plug and lead have about 16 mm of room.
11. **Back plate.** Set it in with the USB-C at about 5 o'clock and turn it **clockwise (seen from the back)** about 1/11 of a turn until both pawls click and the USB-C sits at 6 o'clock.

**To open:**
- **Back plate:** put a coin in the slot on the back and turn it anticlockwise, seen from the back.
- **Front shell:** turn it anticlockwise, seen from the front, firmly past the detent clicks.

## What check.py verifies

- **Parts and clashes:**
  - every part is one solid
  - no clashes in the locked state
  - nothing touches the real reSpeaker STEP
  - the LEDs and their capacitors clear the light ring
- **Front bayonet:**
  - the stack drops into the rear shell past the already-fitted mute plunger
  - the front shell goes on at its entry angle
  - its rigid parts are clear through the whole twist; the 4 detent fingers ride the collar 0.3 mm deflected and click into V-grooves
  - zero overlap when locked, and the stops work
  - flat (non-camming) bearing of at least 0.6 mm
- **Back plate bayonet:**
  - the plate (with its pawls bent in to clear the lip), speaker and USB screw tips are clear through the 32° twist, and each bent pawl clears its slot wall
  - lugs over the lip, hard stop, pawl strain
- **Keying, base, plunger:**
  - key clearance and the stack's rotation budget
  - base and floor, mute plunger
- **Light ring:**
  - channel width, bore clearance, knob exposure
  - crush ribs and how the ring goes on
- **Screws:** every screw length against its insert, with at least 2.5 mm of hole below each tip.
- **Light sensor (v3 variant, untested):** board clear of the carrier and the reSpeaker STEP; the window open from the sensor face to the outside; the shroud gap; the board drops onto its pad; the insert holes stay inside the shell; a hex key reaches both screws straight in from the front.

## Still to verify on the bench

- **Coupons first:**
  - a 30° wedge of the bayonet, the front shell's bottom 10 mm with the rear shell's top 10 mm: lock feel and detent
  - for the wood variant, coupon C1
- **CrowPanel "up".** The panel's native display top sits at D 180° (viewer's left), opposite its ribbon-cable flat at D 0°, not at the STEP's +Z. The firmware turns the picture with `lvgl: rotation: 90` only (no fine trim).
- **CP_ROT_TRIM_DEG (-2.8°)** cancels the dial offset. One photo of v1 showed 5° anticlockwise (±2°), so v2 printed with -5°; a level photo of v2 (12 Nov 2026, all 12 dial marks fitted) showed the dial 2.2° clockwise, so the real offset is about 2.8° anticlockwise. It is a fixed offset, most likely Elecrow's display sitting slightly turned in its housing or print accuracy: the CAD chain (reSpeaker holes, mute button up under the plunger, spider, CrowPanel screw pattern) has no offset of its own. The firmware no longer has a Face Trim. After assembly, judge the dial by eye: if 12 sits X° anticlockwise, change it by -X° and reprint the spider.
- **Knob diameter.** `CP_KNOB_R` (Ø79.0) gives a 0.45 mm gap; measure your knob ring.
