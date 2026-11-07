# Voice Clock

An open-source bedside clock and Home Assistant voice satellite: a knit-textured 116 mm sphere with a round knob display on the front.

![Voice Clock](docs/assembly/img/hero_front.jpg)

- **Clock face and controls:** Elecrow CrowPanel 2.1" rotary display (ESP32-S3, 480 × 480 round IPS, turn-and-press knob, touch). Analog clock, timer ring, alarm, night mode and a light/media control page, in ESPHome + LVGL.
- **Voice:** Seeed reSpeaker XVF3800 4-mic array with XIAO ESP32-S3: wake word, echo cancellation, 3 W speaker and the 12-LED ring that lights a foil-lined light channel round the knob.
- **Enclosure:** parametric build123d CAD, every dimension a named parameter, with automated interference and fit checks. Prints without supports. Both shells twist-lock, and a ballast pocket plus TPU grip pads keep it still when you turn the knob.

## Build it

| | |
|---|---|
| **Print** | [`print/`](print): `VoiceClock_U1.3mf` (4 plates, Snapmaker U1, per-part settings embedded), single-plate 3MFs, and STL/STEP for any slicer. Filament slots: 1 = natural or clear PETG (the two light-ring parts), 2 = matte PLA (shells, carrier and spider), 4 = TPU (grip pads and speaker washers). |
| **Wire** | [Wiring and soldering sheets](docs/wiring/WIRING.md) ([printable PDF](docs/wiring/wiring_sheets.pdf)): wiring diagram, exact solder points on each board, cut list, splice details, cable route and a power-up checklist. |
| **Assemble** | [Illustrated assembly guide](docs/assembly/ASSEMBLY.md) ([web version](docs/assembly/index.html)): 11 steps, numbered callouts for every part and fastener. |
| **Flash** | [`firmware/`](firmware): ESPHome config for the CrowPanel clock face. The reSpeaker runs the [formatBCE XVF3800 ESPHome integration](https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration). |
| **Modify** | [`cad/`](cad): `voice_clock.py` (model), `check.py` (fit checks), `make_3mf.py` (print files), `blender/` (photoreal renders and callouts). |

### Parts

| | Part |
|---|---|
| 1 | Elecrow CrowPanel 2.1" HMI ESP32 rotary display |
| 1 | Seeed reSpeaker XVF3800 4-mic array with XIAO ESP32-S3 |
| 1 | 4428 3 W 8 Ω speaker with JST-PH lead (its STEP model is in `cad/vendor/`) |
| 1 | USB-C breakout with 5.1 kΩ CC resistors, and a 5 V 3 A USB-C charger |
| 10 | Screws: 3 × M3 × 12, 3 × M2 × 20, 4 × M2 × 10 (socket head) |
| 7 | Brass M2 heat-set inserts (3 × 3.2 mm) |
| about 160 g | Steel BBs or shot in slow-cure epoxy (or about 300 g tungsten putty) for the ballast pocket |
| | Aluminium foil tape with non-conductive adhesive, 1/16" adhesive closed-cell foam, CA glue, 22 and 24 AWG wire, 2-pin JST-SM or JST-XH pair, MX1.25 4-pin pigtail, heat shrink |

The [build plan](docs/build-plan.md) explains the design decisions: mic-channel acoustics, speaker isolation, power, why the boards are clamped the way they are, and the known risks.

![Side section](docs/img/section-concept.png)

## Variants

| | |
|---|---|
| [![Turned cherry](docs/img/wood/wood_front.jpg)](print/wood/README.md) | **Turned cherry** ([`print/wood`](print/wood/README.md)): the same enclosure printed in JAYO wood PLA on the Snapmaker U1, v2: only the outer skin is wood PLA (the core is plain PLA, so nothing load-bearing is brittle). The growth rings follow the grain in 3D, with the latewood on a second, hotter cherry head and walnut ring cores, at fixed temperatures and with no surface relief, so the bed faces print flat. Snapmaker Orca project, presets and the scripts that generate them. |

## Status

Version 2 (6 Nov 2026), after the v1 print fell apart:

- **Twist-lock shells.** The front shell turns 10° clockwise onto 7 bayonet lugs on the rear shell and clicks into place on 4 flexure detent fingers, with hard stops. The back plate turns 32° on 3 lugs (one wide, so it only fits one way) and clicks on 2 flexure pawls; a coin slot opens it. v1's snap hooks let both pop off.
- **Keyed stack.** The cradle ribs run down the shell wall into notches in the carrier, so the electronics stack can't turn.
- **Light ring that works.** A hollow channel lined with aluminium foil tape (ring base + ring shell, PETG) carries the LED light to a diffuser cap standing 2.35 mm proud of the sphere. v1's solid printed guide passed an estimated 0.4 % of the light.
- **Front shell prints face-up.** The sphere runs right up to the light ring, with no flat face, and no textured face sits on the bed.
- **Inserts everywhere a screw goes.** The USB-C breakout screws into 2 horizontal heat-set inserts; the speaker bosses have room below the screw tips.
- **Weight.** A 30 cm³ ballast pocket in the rear shell (about 160 g of steel shot in epoxy, or 300 g of tungsten putty) and TPU grip pads on the base: about 479 g in all, with the centre of mass 12 mm lower than v1.

`cad/check.py` checks every part against Seeed's reSpeaker STEP (put it in `cad/vendor/`), sweeps both twist locks with the detent fingers and pawls bent, and drops the stack in. v2 has not been printed yet; the tolerances to confirm on the first print are all single parameters in `cad/voice_clock.py` (`BLK_TOP`, `FING_BUMP_R`, `BP_TOOTH_RO`, `CARRIER_KEY_CLR`, `RING_BORE_R`).

The CrowPanel's native top points left (`lvgl: rotation: 90`, see `firmware/README.md`). The v2 spider turns the panel 5° clockwise (`CP_ROT_TRIM_DEG`) to level the dial; check it by eye after assembly.

## License

MIT, see [LICENSE](LICENSE). Product names belong to their owners; this project is not affiliated with Elecrow, Seeed Studio or Home Assistant.
