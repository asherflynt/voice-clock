> Early research notes. The current design is in [build-plan.md](build-plan.md) and [`cad/`](../cad); where they disagree, those win.

# HA Voice Clock: Components and Case Design Notes

A round bedside clock and smart speaker built from three parts:

1. CrowPanel 2.1" ESP32 Rotary Display (the clock face and knob)
2. Seeed reSpeaker XVF3800 4-Mic Array (microphones, LEDs and speaker amp)
3. dweii 3 W 8 Ω Mini Speaker (JST-PH2.0)

The key sizing fact: the mic board is a 100 mm circle and the display is 79 mm across, so the case needs an inside diameter of about 105 mm or more.

---

## 1. Component specs

### CrowPanel 2.1" ESP32 Rotary Display (Elecrow DHE03921D)

| Spec | Value |
|---|---|
| Overall size | **79 × 79 × 30 mm** (round knob housing) |
| Screen | 2.1" round IPS, 480×480, capacitive touch (about 53 mm diagonal) |
| Interaction | Outer ring turns both ways; whole knob presses in like a button |
| Chip | ESP32-S3R8, 8 MB PSRAM, 16 MB flash, Wi-Fi 2.4 GHz, Bluetooth 5 LE |
| Rear connectors | 2× MX1.25 4-pin (UART, I2C) and a 12-pin FPC (power/programming) |
| Buttons | Reset, Boot, knob press |
| Power | 5 V / 1 A, using the included MX1.25-to-USB cable |
| Shell / weight | Aluminum, plastic and acrylic / 80 g |

**CAD:** Elecrow posts a 3D STEP model in the "3D file" folder of its GitHub repo:
https://github.com/Elecrow-RD/CrowPanel-2.1inch-HMI-ESP32-Rotary-Display-480-480-IPS-Round-Touch-Knob-Screen

### Seeed reSpeaker XVF3800 4-Mic Array

| Spec | Value |
|---|---|
| PCB | **Ø100 mm round, 1.2 mm thick** (from Seeed's 2D drawing) |
| Packaged size | 108 × 108 × 18 mm, 64 g |
| Mics | 4 digital mics in a circle, pickup up to 5 m, 360° |
| Audio out | LM48511 Class D amp, **JST speaker connector (up to 5 W)**, 3.5 mm jack |
| LEDs | 12× WS2812 RGB ring, plus mute and reset buttons |
| Power/data | USB-C, 5 V |

The 2D drawing also shows a 66 × 66 mm square pattern. Check the PDF to see whether that's the mounting holes or the mics.

**CAD** (from the Resources section of the Seeed wiki):

- 2D mechanical drawing (PDF): https://files.seeedstudio.com/wiki/respeaker_xvf3800_usb/respeaker_xvf3800_2d_mechanical_drawing.pdf
- Board 3D STEP: https://files.seeedstudio.com/wiki/respeaker_xvf3800_usb/3d/respeaker_mic_array_xvf3800_1_with-xiao-0820.stp
- Seeed's own enclosure, top: https://files.seeedstudio.com/wiki/respeaker_xvf3800_usb/3d/1-up.stp
- Seeed's own enclosure, bottom: https://files.seeedstudio.com/wiki/respeaker_xvf3800_usb/3d/1-down.stp

Seeed's enclosure is a good reference for mic hole and LED light pipe placement. Download them for your own checks (not redistributed here).

### dweii 3 W 8 Ω Mini Speaker (JST-PH2.0)

| Spec | Value |
|---|---|
| Size | **44 × 28 × 15 mm** (enclosed box speaker) |
| Power / impedance | 3 W / 8 Ω |
| Frequency response | 500 Hz–20 kHz |
| Connector | JST-PH2.0 2-pin |

Some sellers list similar speakers at 70 × 30 × 16 mm, so measure yours with calipers before you finalize the speaker pocket.

---

## 2. Case concept

- Round case with the screen on the front, tilted slightly upward.
- The parts stack front to back: **screen → reSpeaker board → speaker**.
- 3D-printed mesh around the reSpeaker and speaker sections, so the mics can hear and the LEDs show through.

### What works

- **The size order is right.** The 79 mm screen sits in front of the 100 mm mic board, so a ring of board about 10 mm wide sticks out around the screen. If the mics sit on that outer edge, a mesh band around the screen bezel exposes them directly.
- **You get an LED halo.** The 12 RGB LEDs glow through a ring around the clock face, which works well as a status light.
- **The speaker is already in its own box**, so you don't need to build a sealed chamber for it.

### What to change

1. **Check where the mics are first.** Open the Seeed 2D drawing or STEP file and confirm that the mic holes fall outside the 79 mm screen footprint and face forward. If the screen covers any of them, pickup and direction-finding get worse.
2. **Don't rely on mesh alone for the mics.** Put an open hole or short channel (about 1.5–2 mm) right over each mic, ideally with a thin foam or TPU gasket so sound doesn't leak around inside the case. Use the decorative mesh everywhere else.
3. **Mount the board upright with care.** The array is designed to lie flat and listen 360° around the room. Standing on its side, it still picks up voices well from the front. It just isn't as good at telling which direction a voice came from, which a bedside clock doesn't really need.
4. **Keep the speaker away from the mic board.** This is the biggest risk. Echo cancellation can remove the speaker's sound from the mics, but it can't remove vibration traveling through the plastic.
   - Put a solid internal wall between the speaker and the mic board.
   - Soft-mount the speaker with TPU or rubber grommets.
   - Fire the speaker down or out the back, never toward the mic board.
   - Use a separate mesh area for the speaker grille, not one continuous band shared with the mics.
5. **Tilt the whole case, not just the screen.** A wedge-shaped foot or flat-bottomed base at 10–15° keeps all three parts lined up and makes the print much simpler.
6. **Leave the knob ring free.** The whole outer ring of the CrowPanel turns, so mount it by its back and leave about 0.5–1 mm of clearance around the ring.
7. **Plan the cables.** Leave room behind the display for its rear connectors and a path to the mic board's USB-C port. Bring a single 5 V USB-C power input out the back.
8. **Make the LEDs dimmable.** At night they'll be bright through an open mesh. A thin white or translucent diffuser ring printed in PETG behind the mesh softens the glow, and the LEDs can be dimmed in software.
9. **Make it easy to open.** Print it as a front shell and a back shell, joined with heat-set inserts and screws. You'll be opening it a lot while you get the firmware working.

### Power and audio

- Both boards run on 5 V. One USB-C supply of 2 A or more plus a small splitter keeps it to a single cable at the bedside.
- The XVF3800 amp can deliver 5 W and the speaker is rated for 3 W, so cap the volume in software.

### Rough size

About **110–115 mm across and 75–90 mm deep**, depending on whether the speaker lies flat against the back or sits underneath the stack. That's about the size of a large alarm clock.

---

## 3. Next steps

- [ ] Download the CrowPanel and XVF3800 STEP files and the XVF3800 2D drawing for your own checks.
- [ ] Confirm the mic positions relative to the 79 mm screen footprint.
- [ ] Measure the speaker with calipers.
- [ ] Draw a cross-section or start a parametric model (done: build123d, see `cad/`) with the clearances above.

---

## Sources

- CrowPi product page: https://www.crowpi.cc/products/crowpanel-2-1inch-hmi-esp32-rotary-display-480-480-ips-round-touch-knob-screen
- Elecrow wiki: https://www.elecrow.com/wiki/CrowPanel_2.1inch-HMI_ESP32_Rotary_Display_480_IPS_Round_Touch_Knob_Screen.html
- Seeed XVF3800 wiki: https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/
- Seeed product page: https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-Mic-Array-p-6488.html
- Botland XVF3800 specs: https://botland.store/microphones-and-sound-detection/28171-respeaker-xmos-xvf3800-4-microphone-usbi2s-array-for-ai-voice-recognition-seeedstudio-101991441-5904422352950.html
- dweii speaker listing: https://www.desertcart.lk/products/493492710
