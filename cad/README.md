# Voice Clock CAD

A parametric [build123d](https://github.com/gumyr/build123d) model of the enclosure described in [`../docs/build-plan.md`](../docs/build-plan.md).

## Setup

```bash
cd cad
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python voice_clock.py   # builds every part -> out/*.stl, *.step, assembly_D.step
.venv/bin/python check.py         # clashes vs the vendor reSpeaker STEP, assembly sweeps, floor, plunger, snaps
.venv/bin/python make_3mf.py      # Snapmaker U1 -> out/VoiceClock_U1.3mf (3 plates) + out/plates/ fallbacks
.venv/bin/python render.py        # quick numpy previews -> out/render_*.png

# photoreal assembly renders (Blender 5.x, free/GPL; flatpak shown)
.venv/bin/python blender/export_scene.py
flatpak run --filesystem=home org.blender.Blender -b -P "$PWD/blender/render_scene.py" -- --samples 160 --res 1800
.venv/bin/python blender/callouts.py ../docs/assembly/img
```

Released print files are in [`../print`](../print); the scripts above regenerate them into `out/`.

Every dimension is a named constant at the top of `voice_clock.py`. Values marked **VERIFY** come from vendor CAD or drawings, not calipers.

### Turned-wood variant

```bash
.venv/bin/python wood.py            # painted, textured wood shells -> out/wood/
.venv/bin/python wood_project.py    # Snapmaker Orca presets + project 3MF + sliced, post-processed G-code
```

See [`../print/wood/README.md`](../print/wood/README.md) for how it works and how to tune the grain.

## Parts and how they print (all without supports)

| Part | Plate | Orientation | Notes |
|---|---|---|---|
| front_shell | 1 → **slot 2 (PLA)** | Face down | Visible; 4 snap ridges inside (45° faces, no supports). 5 mm brim |
| rear_shell | 1 → **slot 2 (PLA)** | Back rim down | Visible; 4 snap hooks rise from the top rim, cradle ribs, mute guide boss. 5 mm brim |
| back_plate | 1 → **slot 2 (PLA)** | Outer face down | Faces the wall; 3 snap hooks, key tab, pry notch |
| mute_plunger | 1 or 2 | Cap down | 100% infill |
| carrier | 2 → **slot 1 (PETG)** | Back face down, bosses up | Internal bulkhead, hangs on the 3 clamp screws |
| spider | 2 → **slot 1 (PETG)** | Plate down, hub boss up | 100% infill |
| board_spacers | 2 → **slot 1 (PETG)** | Flat | 3 × Ø6.5 × 5 (100% infill) |
| insert_coupon | 2 → **slot 1 (PETG)** | Flat | Print first; verifies the M2 insert hole size |
| light_guide | 2 → **slot 1 (PETG)** | Bezel face down | Clear PETG light ring; 100% infill. 3 crush nubs on the back face |
| tpu_washers | 3 → **slot 4 (optional)** | Flat | 4× speaker isolation washers in TPU |

**Suggested U1 settings:**
- **Matte PLA** for the shells and back plate, **PETG** for the internals and the light ring (separate plates because the bed temperatures differ). 0.2 mm layers, 4 walls, 20% gyroid. Set the M2 inserts at about 230–240 °C in PETG. PLA is fine for a bedside clock, but keep it out of sunny windows and hot cars.
- Textured PEI: the face-down bezel comes out with the plate texture.
- `out/VoiceClock_U1.3mf` holds all 3 plates (Plate 1: all externals in PLA; Plate 2: all internals & light ring in PETG; Plate 3: TPU washers). Single-plate project and generic 3MFs are in `out/plates/`.
- The 3MFs are **model-only**. Your own printer, process and filament presets stay selected. Each part is already assigned to a filament slot: 1 = PETG internals and light guide, 2 = matte PLA shells, 4 = TPU washers.

**After opening a 3MF, check:**
1. Printer is still your U1 (not `...(VoiceClock...3mf)`).
2. Filament slots show your material.
3. Plate 1 (shells, back plate) is on slot 2 (PLA), plate 2 (internals, light guide) on slot 1 (PETG), the TPU washers on slot 4.

## Hardware

Sized for common kits: M2 heat-set inserts (3 long × 3.2 OD) and a metric socket-head assortment. No countersunk screws, standoffs or M3 inserts needed. The shells and back plate snap together.

| Qty | Screw | Where | Thread engaged |
|---|---|---|---|
| 3 | M3 × 12 socket head | Spider → CrowPanel hub (replaces the 3 stock rear screws) | 3.4 mm (stock 3.5) |
| 3 | M2 × 20 socket head | Carrier back (head flush) → carrier boss → reSpeaker hole → **printed spacer** → **M2 insert in the spider's underside** | 2.5 mm |
| 2 | M2 × 10 socket head | Speaker ears. Stack: head, TPU washer, ear, TPU washer, boss | 3.0 mm |
| 2 | M2 × 10 socket head | USB-C breakout → oval holes in its backing wall (self-tapping) | — |

| Qty | Insert | Where |
|---|---|---|
| 5 | M2 (hole Ø2.9, depth ≥4.0 mm) | Spider underside ×3, speaker bosses ×2 |

Also needed: the USB-C breakout with 5.1 kΩ CC resistors, 1/16" adhesive closed-cell foam (4 mic gaskets Ø5 with Ø2 hole, speaker-face ring), wire, the MX1.25 pigtail and heat shrink.

**Insert holes:** M2 Ø2.9 (3DZWMAN D3). `insert_coupon` (plate 2) has three sizes per thread (1/2/3 dots = small/nominal/large). Set an insert in each M2 hole and note which fits best. If it isn't the middle one, change `M2_INSERT_D` and rebuild.

**Snap fits:** the hooks flex 0.5 mm over a 12 mm arm (0.7 % strain, fine for PLA). `SNAP_ENG` sets the engagement; lower it to 0.4 if the shells are too hard to pull apart, raise it to 0.6 if they're loose.

**No battery.** No compact USB-C UPS board with ≥2.5 A and a confirmed glitch-free switchover exists, and the seamless 3 A modules (88 × 41 × 22 mm with 2× 18650) don't fit. A flat 103450 pack would fit behind the carrier later if a suitable board turns up.

## Assembly order

Illustrated, step-by-step guide: [`../docs/assembly`](../docs/assembly/ASSEMBLY.md).

1. Fit the 5 M2 heat-set inserts (spider ×3, back plate ×2).
2. Make the power harness and bench-test both boards (`docs/wiring/WIRING.md`).
3. Swap the CrowPanel's 3 rear screws for M3 × 12 through the spider. **Check that the knob still presses and turns.**
4. Fit the light guide from behind (notch at 10 o'clock over the CrowPanel cable) and the 4 mic foam gaskets.
5. Spacers, reSpeaker (mute "A" at 12 o'clock), carrier, 3 × M2 × 20 into the spider. Plug in the speaker lead first.
6. Click the mute plunger into the rear shell from outside. Drop the stack into the rear shell onto the cradle ribs.
7. Snap the front shell on over the knob (the mic boots key it).
8. Speaker and USB-C breakout onto the back plate; snap the back plate in (key at 6 o'clock).

## Still to verify before the full print

- **Mute button (confirmed).** The button marked A is mute, at 9 o'clock seen from the LED side with the XIAO at the top. `RS_ROT = -90` puts it at 12 o'clock under the plunger.
- **Knob diameter.** `CP_KNOB_R` (Ø79.0) comes from Elecrow's STEP and the gap is now 0.45 mm. Measure your knob ring; if it's bigger, raise `LG_KNOB_GAP`.
- **CrowPanel "up".** The model assumes the STEP's +Z is display-up. The screen can also be rotated in firmware.
- **USB-C breakout.** The slot (9.4 × 3.6), outside overmould recess and backing wall are sized for the measured 21.96 × 13.11 mm board.
- **Fit print first:** print the rear shell and a `SPLIT_Z + 10` slice of the front shell. Check the cradle fit on the board, the snap feel and the mute click.
- **Texture:** the shells and back-plate rim get a 0.6 mm knit-stitch relief (`texture.py`; set `TEXTURE = "hex"` or `"none"` to change it). It's applied at mesh level, so the `.stl`/`.ply`/`.3mf` files are textured but the `.step` files are smooth. Never add supports on the shells; the stitch flanks print fine unsupported.
