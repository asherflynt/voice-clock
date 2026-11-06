# CrowPanel clock firmware (ESPHome)

Analog clock face + device control page for the **Elecrow CrowPanel 2.1" rotary display** (ESP32-S3, 480×480 round IPS, knob + touch).

- `voice-clock.yaml`: ESPHome config (LVGL clock face, knob / touch, night mode, timer ring, alarm, light + media control page)
- `ha_light.yaml`: package that mirrors one Home Assistant light onto the control page
- `voice_clock.h`: device table for the control page (names + entity IDs, in knob order)
- `secrets.example.yaml`: copy to `secrets.yaml`

## Configure

1. `cp secrets.example.yaml secrets.yaml` and fill it in.
2. In `voice-clock.yaml`, set the three `light.*` entities in `packages:`, `music_player`, and `voice_sat` (the entity prefix of your reSpeaker XVF3800 voice satellite) in `substitutions:`.
3. Keep `voice_clock.h` in sync: same light entities, in the same order, and the names you want on screen.

## Flash

```bash
pip install esphome
esphome run voice-clock.yaml                    # first time over USB
esphome run voice-clock.yaml --device <ip>      # afterwards over Wi-Fi
```

Display init follows Elecrow's ESPHome lessons for this board
([Elecrow repo](https://github.com/Elecrow-RD/CrowPanel-2.1inch-HMI-ESP32-Rotary-Display-480-480-IPS-Round-Touch-Knob-Screen)).
The voice satellite side runs on the reSpeaker XVF3800 + XIAO ESP32-S3 with the
[formatBCE ESPHome integration](https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration).

Hardware notes: knob A/B on GPIO4/42 (swapped so clockwise counts up), knob button on PCF8574 P5,
touch CST816 (unrotated), display ST7701S with the Lesson 05 init sequence.

## Screen orientation in the enclosure

The enclosure mounts the CrowPanel with its native display top pointing left (its ribbon-cable side
faces right). The config fixes that in two steps:

- `lvgl: rotation: 90` turns the UI a quarter turn clockwise in software. LVGL remaps touch to match.
- **Face Trim** (a number entity in Home Assistant, -10° to +10°, positive = clockwise) turns the
  whole UI a few more degrees to cancel the small mounting error from screw-hole and seat play.
  Adjust it live until 12 is straight up; it's saved on the device. 0 turns the trim off entirely.
  It defaults to 5°, measured on the first build, so check yours.

The trim works by wrapping each page's widgets in a transparent `container` (`clock_root`,
`control_root`) and setting LVGL's `transform_rotation` on it. Keep those containers transparent:
this build has no RGB565 transform path, so an opaque transformed object draws garbage on partial
redraws. Any trim other than 0 costs some render time and softens 1 px detail slightly.
Dragging the control-page arc by finger lands the knob trim° clockwise of the finger (LVGL
uses the raw touch angle); the rotary knob is unaffected.
