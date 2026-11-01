# CrowPanel 2.1" Rotary Display – Programming for Home Assistant

*Researched 31 Oct 2026 for the HA voice clock project.*

## Recommendation: use ESPHome

ESPHome is the best fit for Home Assistant integration, and Elecrow publishes an official 5-lesson ESPHome course with ready-made YAML for this exact board.

### Why ESPHome over the other options

| Option | Fit for HA | Notes |
| --- | --- | --- |
| **ESPHome** | Best | Native HA API, auto-discovery, entities map directly to knob/touch/screen. Built-in LVGL for the round UI. OTA updates after the first USB flash. No C++ required. |
| Arduino / ESP-IDF / PlatformIO | Possible | Full control, but you must build the HA link yourself (e.g. MQTT). Much more work for a smart-home control. |
| MicroPython | Weakest | Driving a 480×480 RGB panel plus LVGL is slower and less well supported. |

## Hardware summary

| Item | Spec |
| --- | --- |
| MCU | ESP32-S3R8, dual-core LX7 @ 240 MHz |
| Memory | 512 KB SRAM, 8 MB PSRAM, 16 MB Flash |
| Display | 2.1" round IPS, 480×480, ST7701S (SPI control + RGB data bus) |
| Touch | CST816 capacitive (I2C 0x15) |
| I/O expander | PCF8574 (I2C 0x21) – controls panel power and reset |
| I2C bus | SDA GPIO38, SCL GPIO39 |
| Rotary encoder | GPIO42 / GPIO4 (plus push button) |
| Backlight | PWM on GPIO6 |
| Wireless | 2.4 GHz Wi-Fi, BLE / Bluetooth 5.0 |
| Expansion | UART, I2C, 12-pin FPC power/programming connector |
| Power | 5 V / 1 A |
| Size / weight | 79 × 79 × 30 mm, 80 g |

**Bring-up is fiddly:** the panel needs power enabled and a reset sequence via the PCF8574 before the ST7701S starts. Start from Elecrow's YAML instead of writing the config from scratch.

## Steps

1. Install the **ESPHome Device Builder** add-on in Home Assistant. The course was tested on ESPHome 2026.7.4 / Device Builder 1.9.2, so match that version or newer.
2. Get the course YAML from [Elecrow's GitHub](https://github.com/Elecrow-RD/CrowPanel-2.1inch-HMI-ESP32-Rotary-Display-480-480-IPS-Round-Touch-Knob-Screen/tree/master/example/esphome). Start with `Lesson02/rotary-screen-21-display.yaml`.
3. Add your Wi-Fi and API key, then do the first flash over USB from your computer:
   - Device Builder → "Plug into this computer" (needs Chrome), **or**
   - `esphome run file.yaml` on your computer.
4. Work through Lessons 03–05 to add the encoder, the brightness arc UI, and touch.
5. Replace the brightness demo with your own HA entities (e.g. `homeassistant.action: light.turn_on` on knob turns).

## Elecrow ESPHome course

| Lesson | Topic | Source file |
| --- | --- | --- |
| [01](https://www.elecrow.com/wiki/2.1_ESPHome_01_Environment_Setup.html) | Install Home Assistant and ESPHome Device Builder | — |
| [02](https://www.elecrow.com/wiki/2.1_ESPHome_02_LVGL_Display_Text.html) | Initialize the PCF8574 and ST7701S, show "Hello World!" | `Lesson02/rotary-screen-21-display.yaml` |
| [03](https://www.elecrow.com/wiki/2.1_ESPHome_03_Rotate_To_Adjust_Brightness.html) | Rotary encoder (GPIO42/4) → backlight PWM (GPIO6) | `Lesson03/21-adjust-screen-brightness.yaml` |
| [04](https://www.elecrow.com/wiki/2.1_ESPHome_04_LVGL_Adjust_Brightness.html) | LVGL brightness meter (image, arc, %) | `Lesson04/21-lvgl-interface.yaml` |
| [05](https://www.elecrow.com/wiki/2.1-ESPHOME-Lesson05-touch.html) | CST816 touch → adjustable LVGL arc | `Lesson05/21-touch.yaml` |

Lesson 04 needs the background image `bj_light_21_1.png`. Do the lessons in order. If a later one fails, go back to the last layer that worked.

## Open question: voice and audio

The board has **no built-in microphone or speaker amp**. Its only expansion is UART, I2C and the FPC connector. Adding a speaker (e.g. the DWEII 3 W 8 Ω units) would need an external I2S amp module (such as a MAX98357A) and free GPIOs. **Spare pin availability has not been confirmed yet.** Check the pinout before buying audio parts.

## Sources

- [Elecrow: RotaryScreen 2.1" ESPHome 5-Lesson Course Guide](https://www.elecrow.com/wiki/RotaryScreen_2.1inch_ESPHome_5_Lesson_Course_Guide.html)
- [Elecrow: Lesson 02, LVGL Display Text](https://www.elecrow.com/wiki/2.1_ESPHome_02_LVGL_Display_Text.html)
- [Elecrow: CrowPanel 2.1" product wiki](https://elecrow.com/wiki/CrowPanel_2.1inch-HMI_ESP32_Rotary_Display_480_IPS_Round_Touch_Knob_Screen.html)
- [espboards.dev: CrowPanel Rotary 2.1 pinout](https://www.espboards.dev/esp32/elecrow-crowpanel-rotary-2-1/)
- [Elecrow GitHub: ESPHome examples](https://github.com/Elecrow-RD/CrowPanel-2.1inch-HMI-ESP32-Rotary-Display-480-480-IPS-Round-Touch-Knob-Screen/tree/master/example/esphome)
