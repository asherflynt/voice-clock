# CrowPanel clock firmware (ESPHome)

Analog clock face + device control page for the **Elecrow CrowPanel 2.1" rotary display** (ESP32-S3, 480×480 round IPS, knob + touch).

- `voice-clock.yaml`: ESPHome config (LVGL clock face without a second hand, knob / touch, night mode, timer ring, alarm, mic-muted icon, light + media control page)
- `ha_light.yaml`: package that mirrors one Home Assistant light onto the control page
- `voice_clock.h`: device table for the control page (names + entity IDs, in knob order)
- `secrets.example.yaml`: copy to `secrets.yaml`
- `respeaker-light-sensor.yaml` (v3 light-sensor variant, untested on hardware): package for the **reSpeaker's** ESPHome config that reads the VEML7700 light sensor on the XIAO's I2C bus

## Configure

1. `cp secrets.example.yaml secrets.yaml` and fill it in.
2. In `voice-clock.yaml`, set the three `light.*` entities in `packages:`, `music_player`, `voice_sat` (the entity prefix of your reSpeaker XVF3800 voice satellite) and `lux_sensor` in `substitutions:`.
3. Keep `voice_clock.h` in sync: same light entities, in the same order, and the names you want on screen.

## Light sensor (v3 variant, untested)

Only for the optional light-sensor enclosure variant (`print/v3_light_sensor`). The config compiles, but it hasn't run with the sensor fitted. Without a sensor nothing changes: night mode uses the v2 rule whenever there's no light reading.

1. Copy `respeaker-light-sensor.yaml` next to the reSpeaker's ESPHome config and add it under `packages:` (instructions at the top of the file). It reuses the I2C bus that config already sets up for the XVF3800.
2. Flash the reSpeaker. HA gets a new **Ambient Light** sensor (lux); set `lux_sensor` in `voice-clock.yaml` to its entity ID.
3. Flash the clock. **Night Light Level** (a config number in HA, 3 lx by default) is where night mode starts; it ends above twice that, so it doesn't flicker at dusk. **Force Night Mode** still overrides it. While the sensor isn't reporting, night mode falls back to the old rule: sun down and all three lamps off.

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
faces right). `lvgl: rotation: 90` turns the UI a quarter turn clockwise in software at almost no
cost, and LVGL remaps touch to match.

Any smaller angle has to be fixed in the enclosure, not the firmware. A non-90° turn in LVGL
re-renders the face through a transform, which takes 200-600 ms per redraw on the ESP32-S3 and
makes touch and the knob lag. The CAD's `CP_ROT_TRIM_DEG` turns the CrowPanel's screw pattern in
the spider to level the dial: if 12 sits X° counter-clockwise, rotate it by -X°.

The face has no second hand, and the hands move once a minute.
