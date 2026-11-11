# Light ring: white + natural PETG, Snapmaker U1

| Head | Filament |
|---|---|
| 1 (T0) | Natural / translucent PETG: the ring shell's cap and the band that stands out of the case |
| 2 (T1) | White PETG: everything else (ring base, the rest of the ring shell's sleeve) |

- `LightRing_PETG_U1.3mf`: full project (printer, process, both filaments). `LightRing_PETG_model.3mf`: model only, so your own presets stay selected.
- `LightRingShell_PETG_U1.*`: the outer ring shell on its own (about 36 min, 3.5 g natural + 16 g white), for when only that piece needs reprinting.
- The ring shell has a retaining collar inside the case: the front shell's inner wall sits 0.3 mm over it once the shell is twisted on, so the ring can't slide out if the clock is tipped. Four notches in the collar let the front shell's mic-boot lugs pass as it goes on. The sleeve sits 0.3 mm inside the front shell's bore.
- No brim and no skirt: a brim can't be peeled off the thin walls. Engineering plate at 70 °C (on textured PEI use 80 °C; it gives the cap a matte face), 250 °C nozzle, 0.2 mm layers, 3 walls.
- Full ring: about 57 min and 30 g (3 g natural, 27 g white).
- No foil tape: the white walls reflect the LED light. Rebuild with `cad/make_3mf.py` then `cad/slice_ring.py`.
- The mute button is on the same plate in `plates/VoiceClock_light_ring_PETG.3mf` (white PETG) if you need one.
