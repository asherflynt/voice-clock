# Voice Clock

An open-source bedside clock and Home Assistant voice satellite: a knit-textured 120 mm sphere with a round knob display on the front.

![Voice Clock](docs/assembly/img/hero_front.jpg)

- **Clock face and controls:** Elecrow CrowPanel 2.1" rotary display (ESP32-S3, 480 × 480 round IPS, turn-and-press knob, touch). Analog clock, timer ring, alarm, night mode and a light/media control page, in ESPHome + LVGL.
- **Voice:** Seeed reSpeaker XVF3800 4-mic array with XIAO ESP32-S3: wake word, echo cancellation, 3 W speaker and the 12-LED ring that lights the frosted bezel.
- **Enclosure:** parametric build123d CAD, every dimension a named parameter, with automated interference and fit checks. Prints without supports.

## Build it

| | |
|---|---|
| **Print** | [`print/`](print): `VoiceClock_U1.3mf` (4 plates, Snapmaker U1, per-part settings embedded), single-plate 3MFs, and STL/STEP for any slicer. Filament slots: 1 = clear or natural PETG (light guide), 2 = matte PLA (body), 4 = TPU (optional washers). |
| **Wire** | [Wiring and soldering sheets](docs/wiring/WIRING.md) ([printable PDF](docs/wiring/wiring_sheets.pdf)): wiring diagram, exact solder points on each board, cut list, splice details, cable route and a power-up checklist. |
| **Assemble** | [Illustrated assembly guide](docs/assembly/ASSEMBLY.md) ([web version](docs/assembly/index.html)): 10 steps, numbered callouts for every part and fastener. |
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
| 5 | Brass M2 heat-set inserts (3 × 3.2 mm) |
| | 1/16" adhesive closed-cell foam, 22 and 24 AWG wire, 2-pin JST-SM or JST-XH pair, MX1.25 4-pin pigtail, heat shrink, epoxy |

The [build plan](docs/build-plan.md) explains the design decisions: mic-channel acoustics, speaker isolation, power, why the boards are clamped the way they are, and the known risks.

![Side section](docs/img/section-concept.png)

## Variants

| | |
|---|---|
| [![Turned cherry](docs/img/wood/wood_front.jpg)](print/wood/README.md) | **Turned cherry** ([`print/wood`](print/wood/README.md)): the same enclosure printed in JAYO wood PLA on the Snapmaker U1, with a continuous 3D growth-ring grain painted onto every outside surface (cherry with walnut rings), a faint open-pore relief, and a post-processing script that drifts each head's temperature so the wood shades naturally. Snapmaker Orca project, presets and the scripts that generate them. |

## Status

Version 1 (5 Nov 2026), after the first full print of v0:

- **Snap-fit shell.** The front shell snaps onto the rear shell (4 hooks) and the back plate snaps in (3 hooks, keyed). Both pull apart by hand. That removed 9 M3 screws and 9 M3 inserts.
- **Smaller, steadier.** The sphere went from 120 to 116 mm, 109 mm tall (was 116), on a 54 mm flat base (was 42).
- **Tighter around the reSpeaker.** Four cradle ribs centre the board to 0.15 mm and carry its back face. The shell split is now 1 mm in front of the board, so the board never slides past the floor.
- **Mute button that reaches.** The plunger is on the measured BUTA actuator (r 50.23, z −3.0) with a 0.25 mm rest gap. In v0 it stopped 3.5 mm short and 2.4 mm too high.
- **Tighter knob gap.** 0.45 mm (was 0.75). The light guide now centres on the CrowPanel's fixed housing, so the knob can't rub.
- **Cable notch moved to 10 o'clock.** At 195° it sat on an LED and over the audio jack.

`cad/check.py` checks every part against Seeed's reSpeaker STEP (put it in `cad/vendor/`), and sweeps the three assembly moves for collisions. Still to confirm on hardware, all single parameters in `cad/voice_clock.py`:

- Heat-set insert hole size: print `insert_coupon` first (`M2_INSERT_D`).
- The knob ring diameter (`CP_KNOB_R`, 79.0 from Elecrow's STEP), since the gap is now only 0.45 mm.
- Snap-hook feel: `SNAP_ENG` (0.5 mm) sets how hard the shells click and pull apart.
- The CrowPanel's display orientation (also fixable in firmware).

## License

MIT, see [LICENSE](LICENSE). Product names belong to their owners; this project is not affiliated with Elecrow, Seeed Studio or Home Assistant.
