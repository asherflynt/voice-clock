# Bambu Lab project files

Bambu Studio projects for the standard (PLA) build, with stock Bambu presets: printer, 0.20 mm Standard process, and four filaments.

| File | Printer | Plates |
|---|---|---|
| `VoiceClock_X1C.3mf` | X1 Carbon (also X1 / X1E) | 4 |
| `VoiceClock_P1S.3mf` | P1S (also P1P) | 4 |
| `VoiceClock_A1.3mf` | A1 | 4 |
| `VoiceClock_A1mini.3mf` | A1 mini (180 mm bed: shells on their own plates) | 6 |

Filament slots:

| Slot | Filament | Parts |
|---|---|---|
| 1 | PLA (Bambu PLA Basic) | front and rear shells, back plate, carrier, spider |
| 2 | Translucent PETG (Bambu PETG Translucent) | the light ring's glowing band and cap |
| 3 | White PETG (Bambu PETG HF) | the rest of the light ring, mute button |
| 4 | TPU (Bambu TPU 95A HF) | grip pads, speaker washers. TPU doesn't feed through the AMS: print this plate from the external spool |

- Brims are on the two shells only (5 mm, outer). Never put a brim on the light ring parts: it can't be peeled off the thin walls.
- The light ring plate is the only multi-colour plate (prime tower included).
- Times (X1C): shells 6 h 26 min, internals 42 min, light ring 1 h 11 min, TPU 6 min.
- Rebuild with `cad/voice_clock.py` then `cad/make_bambu.py` (needs the Bambu Studio flatpak).
