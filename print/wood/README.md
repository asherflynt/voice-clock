# Voice Clock: turned-wood shells, v2 (Snapmaker U1)

v2 (6 Nov 2026) rebuilds the wood look from research into how wood-grain prints are made. What changed:

- **Tone follows the grain, not the layers.** v1 wandered the nozzle temperature per layer by ±9 °C, which stayed below the point where wood PLA darkens, so nothing showed. Per-layer changes can only ever make horizontal bands anyway. In v2 every head holds **one** temperature for the whole print, and the darker latewood is painted as its own region on a second, **hot** cherry head.
- **Only the skin is wood.** The outer wall is wood PLA; everything under it (inner walls, bayonet lugs, collar, ribs, bosses) is **plain PLA**, so nothing that carries load is brittle.
- **Realistic growth rings.**
  - Ring widths vary from year to year, including runs of lean years.
  - Each ring shades gradually into its latewood, then stops sharply.
  - Walnut cores appear only in the strongest rings.
  - There are broad heartwood streaks and darker end grain.
  - The log runs front to back, so the layers cut across the grain instead of along it.
- **No surface relief.** The back plate's face sits flat on the bed now.

## Load the heads like this

| U1 head | Spool | Temperature | Used for |
|---|---|---|---|
| 1 (T0) | **Plain PLA, brown** (any brown close to cherry) | 215 °C | The core under the skin. It shows only at the seam edge and inside |
| 2 (T1) | **JAYO cherry** | 205 °C | Earlywood (the main tone) |
| 3 (T2) | **JAYO cherry, a second spool** | 230 °C, max 2.5 mm³/s | Latewood. The same wood, scorched a little darker. Set to 230 °C for the first full print (the plan's 235–240 °C is untested above JAYO's range); coupon C1 can raise it later |
| 4 (T3) | JAYO walnut | 212 °C | Ring cores, one gum streak, the mute button |

**Two cherry heads need two cherry spools.** One spool can't feed two heads, so either buy a second cherry spool or rewind about 35 g onto an empty spool. Per print: core PLA about 107 g, cherry 37 g + 30 g, walnut 13 g (about 187 g in total, including the prime tower).

## Optional coupons

The hot-head step and the smallest printable details are measured, not assumed.

1. **C1, tone vs temperature** (`coupons/C1_JAYO_Wood_Cherry_U1.3mf`, 1 h 12 min, cherry on head 1; the sliced `.gcode` sits beside it in the local print folder).
   - **What it is:** three columns at 2.5, 4 and 8 mm³/s outer-wall flow, in four tiers at 205, 220, 235 and 245 °C. Each tier has a vertical wall, a 50° slope and the bed face.
   - **What to do:** photograph it next to a grey card under fixed light.
   - **Pass:** a tier that differs from the 205 °C tier by a clear but gentle step (ΔE00 3–10), with no clogging or rough surface. Use that temperature for head 3 next time (`FILAMENTS` in `CAD/wood_project.py`).
   - **Fail:** if no tier gives a usable step, load walnut in head 3 as well, so the latewood prints in walnut (walnut-only rings).


## Files

- **`VoiceClock_wood_U1.3mf`:** the full Snapmaker Orca project, with printer, process (`0.16mm Turned Wood v2`), the 4 filament presets and the painted model.
- **`renders/`** (local print folder) and `docs/img/wood/` (repo): the v2 Blender renders, from the same paint data the slicer gets.
- **`VoiceClock_wood_U1.gcode`:** sliced, about 16 h 50 min, 315 layers. It is in the local print folder only (46 MB, kept out of git); in the repo, open the 3MF in Snapmaker Orca and slice it. C1 is optional; at 230 °C the hot head stays close to JAYO's range.
- **`VoiceClock_wood_model.3mf`:** the painted model only, for use with your own presets.
- **`presets/`:** the 4 filament presets used (PLA core, cherry, cherry HOT, walnut), the process and the printer. Maple and oak are spare v1 tones, not used. They're also installed in Snapmaker Orca's user presets.
- **`coupons/`:** C1.

## Settings that matter

- **Layers:** 0.16 mm, first layer 0.2.
- **Walls:** 4 walls. Outer wall 40 mm/s, so the cool and hot heads run at the same flow and the step comes from temperature alone.
- **Paint depth 0.5 mm** (`mmu_segmented_region_max_width`). Only the outer wall is wood; the inner walls are core PLA.
- **No post-processing script.** `wood_temps.py` is retired.

## Finishing (recommended: light finish)

1. Mask the bayonet lugs and blocks, the ring bore, the back-plate lip and the mic holes.
2. Scuff the outside with a 320 foam pad along the grain.
3. Wipe on 2–3 thin coats of **satin wipe-on polyurethane**, with 0000 wool or 400 grit between coats.
4. Let it cure for 7 days before assembly.

No stain: gel stain lodges in the layer grooves and makes stripes.

## Decide: which way the log runs

The default (`LOG = "front_back"` in `CAD/wood.py`) runs the log front to back:
- **Front:** arches round a centre below the clock.
- **Sides:** side grain.
- **Top:** ellipses.
- **Back plate:** a log slice.

The alternative, `LOG = "across"`, keeps v1's story with the log across the face, but puts more layer-aligned stripes on the front. Re-run `wood.py` and `wood_project.py` after changing it.
