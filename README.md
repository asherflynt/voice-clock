# Voice Clock

An open-source bedside clock and Home Assistant voice satellite: a knit-textured 120 mm sphere with a round knob display on the front.

![Voice Clock](docs/assembly/img/hero_front.jpg)

- **Clock face and controls:** Elecrow CrowPanel 2.1" rotary display (ESP32-S3, 480 × 480 round IPS, turn-and-press knob, touch). Analog clock, timer ring, alarm, night mode and a light/media control page, in ESPHome + LVGL.
- **Voice:** Seeed reSpeaker XVF3800 4-mic array with XIAO ESP32-S3: wake word, echo cancellation, 3 W speaker and the 12-LED ring that lights the frosted bezel.
- **Enclosure:** parametric build123d CAD, every dimension a named parameter, with automated interference and fit checks. Prints without supports.

## Build it

| | |
|---|---|
| **Print** | [`print/`](print): `VoiceClock_U1.3mf` (4 plates, Snapmaker U1, per-part settings embedded), single-plate 3MFs, and STL/STEP for any slicer. Matte PLA for the body, clear or natural PETG for the light guide. |
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
| 17 | Screws: M2 × 10 / × 20 and M3 × 6 / × 8 / × 12 (socket and button head) |
| 14 | Brass heat-set inserts: 9 × M3 (4 × 4.2 mm), 5 × M2 (3 × 3.2 mm) |
| | 1/16" adhesive closed-cell foam, 22 and 24 AWG wire, JST-PH 2-pin pair, heat shrink, epoxy |

The [build plan](docs/build-plan.md) explains the design decisions: mic-channel acoustics, speaker isolation, power, why the boards are clamped the way they are, and the known risks.

![Side section](docs/img/section-concept.png)

## Status

Version 0: the CAD passes its automated checks (no part overlaps, board and light-guide insertion paths clear, screw engagement 2.5–4 mm, every M3 insert hole fully enclosed), but the full enclosure has not been printed and assembled yet. Things to confirm on your hardware, all single parameters in `cad/voice_clock.py`:

- Which reSpeaker side button is mute (`RS_ROT`, puts it at 12 o'clock).
- Heat-set insert hole size: print `insert_coupon` first (`M2_INSERT_D`, `M3_INSERT_D`).
- The CrowPanel's display orientation (also fixable in firmware).
- That the light guide's cable notch (`NOTCH_ANG`) falls between two LEDs on your reSpeaker, so the bezel glows evenly.

Vendor CAD for the CrowPanel and reSpeaker is not redistributed here; the model uses measured proxies. Download Seeed's and Elecrow's STEP files from their product pages if you want them for your own checks.

## License

MIT, see [LICENSE](LICENSE). Product names belong to their owners; this project is not affiliated with Elecrow, Seeed Studio or Home Assistant.
