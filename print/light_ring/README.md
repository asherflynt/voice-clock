# Light ring: white + natural PETG, Snapmaker U1

| Head | Filament |
|---|---|
| 1 (T0) | Natural / translucent PETG: the ring shell's cap and the band that stands out of the case |
| 2 (T1) | White PETG: everything else (ring base, the rest of the ring shell's sleeve) |

- `LightRing_PETG_U1.3mf`: full project (printer, process, both filaments). `LightRing_PETG_model.3mf`: model only, so your own presets stay selected.
- No brim and no skirt: a brim can't be peeled off the thin walls. Textured PEI, 80 °C bed, 250 °C nozzle, 0.2 mm layers, 3 walls.
- About 49 min and 25 g (3 g natural, 22 g white); 13 tool changes, all in the first 2.65 mm.
- No foil tape: the white walls reflect the LED light. Rebuild with `cad/make_3mf.py` then `cad/slice_ring.py`.
- The mute button is on the same plate in `plates/VoiceClock_light_ring_PETG.3mf` (white PETG) if you need one.
