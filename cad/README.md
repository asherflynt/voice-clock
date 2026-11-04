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
.venv/bin/python check.py         # interference, insertion-path, floor and plug-clearance checks
.venv/bin/python make_3mf.py      # Snapmaker U1 -> out/VoiceClock_U1.3mf (4 plates) + out/plates/ fallbacks
.venv/bin/python render.py        # quick numpy previews -> out/render_*.png

# photoreal assembly renders (Blender 5.x, free/GPL; flatpak shown)
.venv/bin/python blender/export_scene.py
flatpak run org.blender.Blender -b -P blender/render_scene.py -- --samples 160 --res 1800
.venv/bin/python blender/callouts.py ../docs/assembly/img
```

Released print files are in [`../print`](../print); the scripts above regenerate them into `out/`.

Every dimension is a named constant at the top of `voice_clock.py`. Values marked **VERIFY** come from vendor CAD or drawings, not calipers.

## Parts and how they print (all without supports)

| Part | Plate | Orientation | Notes |
|---|---|---|---|
| front_shell | 1 → **extruder 2 (PLA)** | Face down | Visible exterior shell (~350 mm² bed contact, **5 mm brim**) |
| rear_shell | 1 → **extruder 2 (PLA)** | Back rim down | Visible exterior shell (5 mm brim recommended) |
| back_plate | 1 → **extruder 2 (PLA)** | Outer face down | Visible exterior back plate (fits on Plate 1 with shells) |
| mute_plunger | 1 → **extruder 2 (PLA)** | Cap down | 100% infill (also on Plate 2 if preferred in PETG) |
| carrier | 2 → **extruder 1 (PETG)** | Back face down, bosses up | Internal non-visible bracket |
| spider | 2 → **extruder 1 (PETG)** | Plate down, hub boss up | Internal non-visible bracket; 100% infill |
| board_spacers | 2 → **extruder 1 (PETG)** | Flat | 3 × Ø6.5 × 5 internal spacers (100% infill) |
| insert_coupon | 2 → **extruder 1 (PETG)** | Flat | Print first; verifies 3DZWMAN insert hole sizes |
| light_guide | 2 → **extruder 1 (PETG)** | Bezel face down | Clear PETG light ring; 100% infill or all walls |
| tpu_washers | 3 → **extruder 4 (optional)** | Flat | 4× speaker isolation washers in TPU |

**Suggested U1 settings:**
- **Matte PLA** for everything except the light guide (clear or natural PETG, on its own plate because the bed temperatures differ). 0.2 mm layers, 4 walls (the heat-set inserts need wall material), 20% gyroid. Set heat-set inserts at about 190–200 °C in PLA. PLA is fine for a bedside clock, but keep it out of sunny windows and hot cars.
- Textured PEI: the face-down bezel comes out with the plate texture.
- `out/VoiceClock_U1.3mf` holds all 3 plates (Plate 1: all externals in PLA; Plate 2: all internals & light ring in PETG; Plate 3: TPU washers). Single-plate project and generic 3MFs are in `out/plates/`.
- The 3MFs are **model-only**. Your own printer, process and filament presets stay selected. Each part is already assigned to a filament slot: 1 = PETG light guide, 2 = matte PLA body, 4 = TPU washers.

**After opening a 3MF, check:**
1. Printer is still your U1 (not `...(VoiceClock...3mf)`).
2. Filament slots show your material.
3. The light guide is on slot 1 (PETG), the TPU washers on slot 4, everything else on slot 2 (PLA).

## Hardware

Sized for common kits: heat-set inserts M2 (3 long × 3.2 OD) and M3 (4 long × 4.2 OD), and a metric M2–M5 socket/button-head assortment (M2 10/12/16/20, M3 6/8/12/16/20). No countersunk screws or standoffs needed.

| Qty | Screw | Where | Thread in insert |
|---|---|---|---|
| 3 | M3 × 12 socket head | Spider → CrowPanel hub (replaces the 3 stock rear screws) | 3.4 mm (stock 3.5) |
| 3 | M2 × 20 socket head | Carrier back (head flush) → carrier boss → reSpeaker hole → **printed spacer** → **M2 insert in the spider's underside** | 2.5 mm |
| 3 | M3 × 6 socket head | Carrier rim (1.2 mm counterbore) → front-shell lugs | 4.0 mm |
| 3 | M3 × 8 button head | Rear-shell ribs → carrier (straight in through the open back) | 4.0 mm |
| 3 | M3 × 8 button head | Back plate → rear shell (heads sit on the wall-facing back) | 4.0 mm |
| 2 | M2 × 10 socket head | Speaker ears. Stack: head, TPU washer, ear, TPU washer, boss | 3.0 mm |

| Qty | Insert | Where |
|---|---|---|
| 9 | M3 (hole Ø4.0, depth ≥5.0 mm) | Front-shell lugs ×3, carrier bosses ×3, rear-shell lugs ×3 |
| 5 | M2 (hole Ø2.9, depth ≥4.0 mm) | Spider underside ×3, speaker bosses ×2 |

Also needed: the USB-C breakout with 5.1 kΩ (glued into the back-plate cage with epoxy), 1/16" adhesive closed-cell foam (4 mic gaskets Ø5 with Ø2 hole, speaker-face ring), wire, JST-PH pigtails and heat shrink.

**Insert holes:** M2 Ø2.8, M3 Ø3.7 (insert OD minus about 0.4–0.5 mm). `insert_coupon` (plate 2) has three sizes per thread (1/2/3 dots = small/nominal/large; 1 notch = M2 row, 2 notches = M3 row). Set an insert in each hole and note which fits best. If it isn't the middle one, change `M2_INSERT_D` / `M3_INSERT_D` and rebuild.

**No battery.** No compact USB-C UPS board with ≥2.5 A and a confirmed glitch-free switchover exists, and the seamless 3 A modules (88 × 41 × 22 mm with 2× 18650) don't fit. A flat 103450 pack would fit behind the carrier later if a suitable board turns up.

## Assembly order

Illustrated, step-by-step guide: [`../docs/assembly`](../docs/assembly/ASSEMBLY.md).

1. Fit the heat-set inserts (PLA: iron about 190–200 °C).
2. Solder the power leads to the reSpeaker (XIAO 5V/GND) and the CrowPanel (bench-test first).
3. Swap the CrowPanel's 3 rear screws for M3 × 12 through the spider. **Check that the knob still presses and turns.**
4. Set the 3 M2 inserts into the spider's underside and the 3 printed spacers on the reSpeaker's front holes.
5. Place the reSpeaker on the spacers, then the carrier behind it, then 3 × M2 × 20 from the back into the spider inserts. Plug in the speaker lead before the carrier goes on.
6. Fit the light guide over the display ring, with its notch at the CrowPanel cable. Fit the mic foam gaskets.
7. Put the mute plunger in the front shell. Slide the stack in from behind (the knob goes through the face). Screw the carrier rim (3 × M3 × 6 socket head).
8. Fit the rear shell (3 × M3 × 8 through the ribs via the open back).
9. Stick the foam ring around the speaker's diaphragm face. Screw the speaker to the back plate, diaphragm toward the round grille and lead toward the top (M2 × 10 through TPU washers). Epoxy the USB-C breakout into its cage and zip-tie the lead. Close up with 3 × M3 × 8 button head.

## Still to verify before the full print

- **Mute button (confirmed).** The button marked A is mute, at 9 o'clock seen from the LED side with the XIAO at the top. `RS_ROT = -90` puts it at 12 o'clock under the plunger; the cable notch and rear-shell rib angles are set for this orientation.
- **CrowPanel "up".** The model assumes the STEP's +Z is display-up. The screen can also be rotated in firmware.
- **USB-C breakout.** The slot (9.4 × 3.6), outside overmould recess and inside cage are sized for the 22.1 × 13 mm board. Check the receptacle reaches the outer face before gluing.
- **Fit print first:** print the spider, the carrier, and a `FACE_Z - 10` slice of the front shell. Check the knob gap, bezel seating, and board clamp.
- **Texture:** the shells and back-plate rim get a 0.6 mm knit-stitch relief (`texture.py`; set `TEXTURE = "hex"` or `"none"` to change it). It's applied at mesh level, so the `.stl`/`.ply`/`.3mf` files are textured but the `.step` files are smooth. Never add supports on the shells; the stitch flanks print fine unsupported.
