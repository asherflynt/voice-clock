# v2 draft fit test (about 3 h 20 min in total)

Short, untextured bands of the shells at every interface, plus the small parts at full size. Draft settings: 2 walls, 10 % infill, layer height left at your preset (0.2 mm), so the fits are representative. Print it all in plain PLA, including the ring parts (in the real build only the two ring parts and the PETG mute button are PETG; the carrier and spider are PLA).

| File | Contents | Time (0.2 mm, plain PLA) |
|---|---|---|
| `VoiceClock_v2_fit_plate1` | front band + rear band | 57 min |
| `VoiceClock_v2_fit_plate2` | back plate, back-opening ring, ring-bore band, mute button | 1 h 4 min |
| `VoiceClock_v2_fit_plate3` | ring base, ring shell, carrier, spider | 1 h 21 min |

- **`.3mf`:** model only, with per-part draft settings, so your own U1 presets stay selected.
- **G-code:** not included. Slice the 3MFs with a generic PLA preset (the earlier draft G-code predated the final tolerances and was retired).
- **`VoiceClock_v2_fit_tests.3mf`:** all three plates in one project.

## What to check

1. **Twist lock** (front band on rear band).
   - Set the front band on turned about 10° anticlockwise (seen from its outside). The flat bases are then offset by a finger's width.
   - Push it down, then turn it clockwise about 10°. You should feel 4 clicks together and a hard stop, with the flat bases lined up.
   - It should turn without binding.
   - About 0.2 mm of axial play is expected; the mic gaskets take it up in the real case.
   - To open it, turn it anticlockwise firmly.
2. **Board seat** (rear band).
   - Screw the reSpeaker between the carrier and the ring base with the spider (3 × M2 × 20, snug only). The CrowPanel isn't needed for this.
   - Click the mute button into the rear band first.
   - Lower the stack in. The 4 carrier notches should slide down the 4 ribs without force.
   - The board sits on the pads, can't turn, and pressing the mute button clicks the switch.
3. **Back plate** (back plate in the back-opening ring).
   - Hold it with the USB-C slot at about 5 o'clock (seen from the back). Push it in and turn it clockwise about 1/12 of a turn.
   - You should feel two pawl clicks, then a hard stop, with the USB-C slot at 6 o'clock.
   - A coin in the slot turns it back.
   - Press the 4 M2 inserts in to check the bosses and the USB-C wall. The USB-C inserts go in from the wall's outer face.
4. **Light ring.**
   - Press the ring shell onto the ring base. The tabs go in the slots, and the crush ribs should grip without forcing.
   - Set the ring-bore band over it: there should be an even gap of about 0.6 mm all round.
   - With foil tape fitted, light the LEDs to judge the glow before the real print.
5. **Spider.** The M3 × 12 screws should start in the d3.1 holes by hand and seat on the CrowPanel hub.

If anything binds, note which part and roughly how much, before changing the CAD.
