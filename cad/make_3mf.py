"""Pack the printed parts into model-only Snapmaker U1 .3mf plates.

Model-only on purpose: no project_settings.config, so the user's own printer,
process and filament presets stay selected (wrong preset ids in an embedded
config silently create broken derived presets). Part -> extruder assignment
lives in Metadata/model_settings.config.
"""
import zipfile
from pathlib import Path
import numpy as np
import trimesh
import html

OUT = Path(__file__).parent / "out"
BED = 270.0

EXTERNALS_PLA = [
    ("front_shell", 2, 67, 69, 0),
    ("rear_shell", 2, 201, 69, 0),
    ("back_plate", 2, 67, 205, 0),
    ("mute_plunger", 2, 201, 205, 0),
]

SHELLS_ONLY_PLA = [
    ("front_shell", 2, 70, 135, 0),
    ("rear_shell", 2, 200, 135, 0),
]

BACK_PLATE_ONLY_PLA = [
    ("back_plate", 2, 135, 135, 0),
]

# The structural internals (carrier, spider) are PLA: modestly stiffer than PETG (tensile modulus about 1.3x)
# and, more usefully, more accurate for the 0.2 mm key notches and the d2.9 insert holes (less ooze and stringing). Only the light ring stays PETG (the cap must be translucent; the
# crush-rib press fit wants PETG's give), plus a PETG mute button (its snap barb is tougher in PETG).
INTERNALS_PLA = [
    ("carrier", 2, 75, 135, 0),
    ("spider", 2, 195, 135, 0),
]
# Light ring plate, 2 PETG colours (PETG and PLA never share a plate, so slot 2 is free to hold PETG here):
# slot 1 = natural/clear PETG (only the ring shell's cap and the band that stands out of the sphere),
# slot 2 = white PETG (the channel walls reflect the LED light diffusely; no foil tape)
LIGHT_RING_PETG = [
    ("ring_shell_2c", 2, 70, 135, 0),
    ("ring_base", 2, 190, 135, 0),
    ("mute_plunger", 2, 135, 235, 0),
]
# one object printed from several filaments: (part mesh, slot)
MULTI = {"ring_shell_2c": [("ring_shell_natural", 1), ("ring_shell_white", 2)]}
INTERNALS_WITH_BACK_PLATE_PLA = [
    ("carrier", 2, 62, 62, 0),
    ("spider", 2, 200, 62, 0),
    ("back_plate", 2, 135, 195, 0),
]

# name, extruder (U1 slot), bed x, y, rot-z. PLA and PETG never share a plate (different bed temperatures).
PLATES = [
    # filament slots: 1 = natural/clear PETG (the ring's diffuser band), 2 = matte PLA (shells and structural
    # internals) or, for the light-ring plate, white PETG (channel walls, mute button), 4 = TPU (grip pads,
    # speaker washers). Slot 3 is unused.
    ("Externals - PLA slot 2", EXTERNALS_PLA),
    ("Internals - PLA slot 2", INTERNALS_PLA),
    ("Light Ring - PETG slot 1 natural + slot 2 white", LIGHT_RING_PETG),
    ("TPU - grip pads + speaker washers - slot 4", [
        ("foot_pads", 4, 135, 95, 0),
        ("tpu_washers", 4, 135, 200, 0),
    ]),
]
# object-level overrides (independent of the user's preset names)
SETTINGS = {
    "_default": {"wall_loops": "4", "sparse_infill_density": "20%", "enable_support": "0", "brim_type": "no_brim"},
    "front_shell": {"brim_type": "outer_only", "brim_width": "5"},
    "rear_shell": {"brim_type": "outer_only", "brim_width": "5"},
    "spider": {"sparse_infill_density": "100%"},
    "mute_plunger": {"sparse_infill_density": "100%"},
    "ring_base": {"wall_loops": "3", "brim_type": "no_brim"},   # brims were impossible to remove from the thin PETG walls
    "ring_shell": {"wall_loops": "3", "brim_type": "no_brim"},   # brims were impossible to remove from the thin PETG walls
    "ring_shell_2c": {"wall_loops": "3", "brim_type": "no_brim"},
    "tpu_washers": {"sparse_infill_density": "100%", "wall_loops": "2", "brim_type": "outer_only", "brim_width": "3"},
    "foot_pads": {"sparse_infill_density": "100%", "wall_loops": "2"},
}
STRIDE = BED * 1.2          # Orca lays plates out on a grid: stride = bed * (1 + 1/5)


def plate_origin(i, n):
    v = n ** 0.5
    cols = round(v) + 1 if v > round(v) else round(v)
    return (i % cols) * STRIDE, -(i // cols) * STRIDE


NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
      'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
      'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06"')


def load(name):
    if name in MULTI:                      # several bodies, one object: the union is used for placement
        parts = [(pn, ext, load(pn)) for pn, ext in MULTI[name]]
        m = trimesh.util.concatenate([pm for _, _, pm in parts])
        m.metadata["subparts"] = parts
        return m
    ply = OUT / f"{name}.ply"
    if ply.exists():                       # textured parts: indexed, don't weld
        m = trimesh.load(ply, process=False)
    else:
        m = trimesh.load(OUT / f"{name}.stl")
        m.merge_vertices()
    assert m.is_watertight, f"{name} not watertight"
    assert m.is_winding_consistent, f"{name} winding"
    assert m.volume > 0, f"{name} volume"
    return m


def place(items, ox=0.0, oy=0.0):
    meshes = []
    for name, ext, x, y, rz in items:
        m = load(name)
        subs = m.metadata.get("subparts")
        T = trimesh.transformations.rotation_matrix(np.radians(rz), [0, 0, 1])
        m.apply_transform(T)
        b = m.bounds
        shift = [x - (b[0][0] + b[1][0]) / 2, y - (b[0][1] + b[1][1]) / 2, -b[0][2]]
        m.apply_translation(shift)
        b = m.bounds
        assert b[0][0] >= 2 and b[0][1] >= 2 and b[1][0] <= BED - 2 and b[1][1] <= BED - 2, f"{name} off bed {b}"
        m.apply_translation([ox, oy, 0])
        if subs:
            for _, _, pm in subs:
                pm.apply_transform(T)
                pm.apply_translation(shift)
                pm.apply_translation([ox, oy, 0])
            m.metadata["subparts"] = subs
        meshes.append((name, ext, m))
    # pairwise footprint overlap check (2D bounding boxes + 3 mm gap)
    for i in range(len(meshes)):
        for j in range(i + 1, len(meshes)):
            a, b = meshes[i][2].bounds, meshes[j][2].bounds
            if not (a[1][0] + 3 <= b[0][0] or b[1][0] + 3 <= a[0][0] or a[1][1] + 3 <= b[0][1] or b[1][1] + 3 <= a[0][1]):
                # bounding boxes overlap - fall back to a real footprint test
                pa = trimesh.path.polygons.projected(meshes[i][2], normal=[0, 0, 1])
                pb = trimesh.path.polygons.projected(meshes[j][2], normal=[0, 0, 1])
                assert pa.buffer(1.5).intersection(pb).area < 1e-3, f"{meshes[i][0]} overlaps {meshes[j][0]}"
    return meshes


def paint_code(state):
    """Orca/Bambu TriangleSelector leaf code for an extruder state (1-based), "" = unpainted."""
    if state <= 0:
        return ""
    if state < 3:
        return "%X" % (state * 4)
    n = state - 3
    assert n < 15, "paint states above 17 need the 0xF continuation chunk"   # mixed filaments: 5.. = rows
    return "%X" % n + "C"


def write(path, plates, paints=None):
    """plates: list of (plate_name, meshes). paints: {object name: per-triangle extruder state}."""
    paints = paints or {}
    meshes = [m for _, ms in plates for m in ms]
    plate = path.stem

    # meshes are written centred on their own origin; placement goes in the build item,
    # the way slicer-saved 3MFs do it
    place_xy = {k: ((m.bounds[0][0] + m.bounds[1][0]) / 2, (m.bounds[0][1] + m.bounds[1][1]) / 2)
                for k, (_, _, m) in enumerate(meshes, 1)}
    def parts_of(name, ext, m):
        return m.metadata.get("subparts") or [(name, ext, m)]
    part_ids, nid = {}, 0                   # object k -> [(mesh object id, part name, slot, mesh)]
    for k, (name, ext, m) in enumerate(meshes, 1):
        part_ids[k] = []
        for pn, pe, pm in parts_of(name, ext, m):
            nid += 1
            part_ids[k].append((nid, pn, pe, pm))
    tmp = OUT / f"_{plate}_object.model"
    with open(tmp, "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n<resources>\n')
        for k, (name, ext, m0) in enumerate(meshes, 1):
          for oid, pname, pext, m in part_ids[k]:
            f.write(f'<object id="{oid}" type="model"><mesh><vertices>\n')
            cx, cy = place_xy[k]
            for v in m.vertices - [cx, cy, 0.0]:
                f.write(f'<vertex x="{v[0]:.6f}" y="{v[1]:.6f}" z="{v[2]:.6f}"/>\n')
            f.write('</vertices><triangles>\n')
            pt = paints.get(name) if len(part_ids[k]) == 1 else None
            codes = [paint_code(int(x)) for x in range(18)]   # 1-4 physical heads, 5-17 Full Spectrum mixes
            for i, t in enumerate(m.faces):
                pc = codes[int(pt[i])] if pt is not None else ""
                if pc:
                    f.write(f'<triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}" paint_color="{pc}"/>\n')
                else:
                    f.write(f'<triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}"/>\n')
            f.write('</triangles></mesh></object>\n')
        f.write('</resources>\n<build/>\n</model>\n')

    root = [f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>',
            '<metadata name="Application">SnapmakerOrca-02.04.00.70</metadata>',
            '<metadata name="BambuStudio:3mfVersion">1</metadata>',
            f'<metadata name="Title">{html.escape(plate)}</metadata>', '<resources>']
    for k, (name, ext, m) in enumerate(meshes, 1):
        comps = "".join(f'<component p:path="/3D/Objects/object_1.model" objectid="{oid}" '
                        f'p:UUID="0001{oid:04d}-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
                        for oid, _, _, _ in part_ids[k])
        root.append(f'<object id="{100 + k}" p:UUID="0000{100 + k:04d}-61cb-4c03-9d28-80fed5dfa1dc" type="model"><components>'
                    f'{comps}</components></object>')
    root.append('</resources>\n<build>')
    for k, _ in enumerate(meshes, 1):
        root.append(f'<item objectid="{100 + k}" transform="1 0 0 0 1 0 0 0 1 {place_xy[k][0]:.4f} {place_xy[k][1]:.4f} 0" printable="1"/>')
    root.append('</build>\n</model>\n')

    ms = ['<?xml version="1.0" encoding="UTF-8"?>\n<config>']
    for k, (name, ext, m) in enumerate(meshes, 1):
        ms += [f'  <object id="{100 + k}">',
               f'    <metadata key="name" value="{name}"/>',
               f'    <metadata key="extruder" value="{ext}"/>']
        for key, val in {**SETTINGS["_default"], **SETTINGS.get(name, {})}.items():
            ms.append(f'    <metadata key="{key}" value="{val}"/>')
        for oid, pname, pext, pm in part_ids[k]:
            ms += [f'    <part id="{oid}" subtype="normal_part">',
                   f'      <metadata key="name" value="{pname}"/>',
                   '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>',
                   f'      <metadata key="extruder" value="{pext}"/>',
                   f'      <mesh_stat face_count="{len(pm.faces)}" edges_fixed="0" degenerate_facets="0" '
                   'facets_removed="0" facets_reversed="0" backwards_edges="0"/>',
                   '    </part>']
        ms += ['  </object>']
    k = 0
    for pi, (pname, pm) in enumerate(plates, 1):
        ms += ['  <plate>', f'    <metadata key="plater_id" value="{pi}"/>', f'    <metadata key="plater_name" value="{html.escape(pname)}"/>',
               '    <metadata key="locked" value="false"/>']
        for _ in pm:
            k += 1
            ms += ['    <model_instance>', f'      <metadata key="object_id" value="{100 + k}"/>',
                   '      <metadata key="instance_id" value="0"/>', f'      <metadata key="identify_id" value="{k}"/>',
                   '    </model_instance>']
        ms += ['  </plate>']
    ms += ['  <assemble>']
    for k, _ in enumerate(meshes, 1):
        ms.append(f'   <assemble_item object_id="{100 + k}" instance_id="0" transform="1 0 0 0 1 0 0 0 1 {place_xy[k][0]:.4f} {place_xy[k][1]:.4f} 0" offset="0 0 0"/>')
    ms += ['  </assemble>', '</config>\n']

    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '<Default Extension="config" ContentType="text/xml"/></Types>\n')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>\n')
    mrels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Target="/3D/Objects/object_1.model" Id="rel-1" '
             'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>\n')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", "\n".join(root))
        z.writestr("3D/_rels/3dmodel.model.rels", mrels)
        z.write(tmp, "3D/Objects/object_1.model")
        z.writestr("Metadata/model_settings.config", "\n".join(ms))
    tmp.unlink()
    return meshes



def write_generic(path, items):
    """Write a standard generic 3MF where geometry is directly in 3D/3dmodel.model."""
    meshes = place(items)
    root = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
        '<resources>'
    ]
    for k, (name, ext, m) in enumerate(meshes, 1):
        root.append(f'<object id="{k}" name="{name}" type="model"><mesh><vertices>')
        for v in m.vertices:
            root.append(f'<vertex x="{v[0]:.6f}" y="{v[1]:.6f}" z="{v[2]:.6f}"/>')
        root.append('</vertices><triangles>')
        for t in m.faces:
            root.append(f'<triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}"/>')
        root.append('</triangles></mesh></object>')
    root.append('</resources>\n<build>')
    for k, _ in enumerate(meshes, 1):
        root.append(f'<item objectid="{k}" printable="1"/>')
    root.append('</build>\n</model>')

    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>\n')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>\n')

    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', '\n'.join(root))
    return meshes

def verify(path, expect):
    """Re-read the archive and rebuild each part from the raw XML (not trimesh's 3MF loader)."""
    import re
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        for req in ("[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model", "3D/_rels/3dmodel.model.rels",
                    "3D/Objects/object_1.model", "Metadata/model_settings.config"):
            assert req in names, f"missing {req}"
        assert not any(n.startswith("Metadata/project_settings") for n in names)
        obj = z.read("3D/Objects/object_1.model").decode()
        ms = z.read("Metadata/model_settings.config").decode()
    rows = []
    with zipfile.ZipFile(path) as z:
        rootxml = z.read("3D/3dmodel.model").decode()
    for k, (name, ext, m0) in enumerate(expect, 1):
        comp = re.search(rf'<object id="{100 + k}"[^>]*><components>(.*?)</components>', rootxml, re.S).group(1)
        oids = re.findall(r'objectid="(\d+)"', comp)
        subs = m0.metadata.get("subparts") or [(name, ext, m0)]
        assert len(oids) == len(subs), name
        pieces, ext_ok = [], True
        for oid, (pn, pe, _) in zip(oids, subs):
            body = re.search(rf'<object id="{oid}" type="model">(.*?)</object>', obj, re.S).group(1)
            V = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>', body), float)
            F = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"[^/]*/>', body), int)
            pm = trimesh.Trimesh(V, F, process=False)   # index topology, as the slicer reads it
            assert pm.is_watertight, (name, pn)
            pieces.append(pm)
            ext_ok &= f'<part id="{oid}" subtype="normal_part">\n      <metadata key="name" value="{pn}"/>\n      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n      <metadata key="extruder" value="{pe}"/>' in ms
        m = trimesh.util.concatenate(pieces) if len(pieces) > 1 else pieces[0]
        ext_ok &= f'<metadata key="name" value="{name}"/>\n    <metadata key="extruder" value="{ext}"/>' in ms
        rows.append((name, ext, m.is_watertight, round(m.volume / 1000, 2), round(m.bounds[0][2], 3),
                     round(m.bounds[1][2], 1), ext_ok))
    return rows


def report(path, meshes, plates):
    print(f"\n{path.name}")
    print(f"  {'part':14s} plate ext  watertight  cm3    z0     height  on-plate  extruder-ok")
    plate_indices = [pi for pi, (_, ms) in enumerate(plates) for _ in ms]
    rows = verify(path, meshes)
    for pi, (name, ext, m), r in zip(plate_indices, meshes, rows):
        ox, oy = plate_origin(pi, len(plates))
        b = m.bounds
        on = ox <= b[0][0] and b[1][0] <= ox + BED and oy <= b[0][1] and b[1][1] <= oy + BED
        print(f"  {r[0]:14s} {pi + 1:>5} {r[1]:>3}  {str(r[2]):10s} {r[3]:6.2f} {r[4]:6.3f} {r[5]:6.1f}  {str(on):8s}  {r[6]}")
        assert r[2] and r[4] == 0 and r[6] and on


if __name__ == "__main__":
    # one file, all plates
    placed = []
    for i, (pname, items) in enumerate(PLATES):
        ox, oy = plate_origin(i, len(PLATES))
        placed.append((pname, place(items, ox, oy)))
    path = OUT / "VoiceClock_U1.3mf"
    meshes = write(path, placed)
    report(path, meshes, PLATES)
    # fallback: one file per plate, each at the plate-1 origin
    (OUT / "plates").mkdir(exist_ok=True)
    for i, (pname, items) in enumerate(PLATES, 1):
        pp = OUT / "plates" / f"VoiceClock_plate{i}.3mf"
        write(pp, [(pname, place(items))])
    # Named single-plate convenience files (OrcaSlicer project)
    write(OUT / "plates" / "VoiceClock_externals_PLA.3mf", [(PLATES[0][0], place(EXTERNALS_PLA))])
    write(OUT / "plates" / "VoiceClock_shells_only_PLA.3mf", [("Shells only - PLA slot 2", place(SHELLS_ONLY_PLA))])
    write(OUT / "plates" / "VoiceClock_back_plate_only.3mf", [("Back plate - PLA slot 2", place(BACK_PLATE_ONLY_PLA))])
    write(OUT / "plates" / "VoiceClock_internals_PLA.3mf", [(PLATES[1][0], place(INTERNALS_PLA))])
    write(OUT / "plates" / "VoiceClock_light_ring_PETG.3mf", [(PLATES[2][0], place(LIGHT_RING_PETG))])
    write(OUT / "plates" / "VoiceClock_internals_with_back_plate_PLA.3mf", [("Internals with Back Plate - PLA slot 2", place(INTERNALS_WITH_BACK_PLATE_PLA))])
    # Universal generic 3MFs (raw meshes embedded in 3D/3dmodel.model, works in every slicer & import mode)
    write_generic(OUT / "plates" / "VoiceClock_externals_PLA_generic.3mf", EXTERNALS_PLA)
    write_generic(OUT / "plates" / "VoiceClock_shells_only_PLA_generic.3mf", SHELLS_ONLY_PLA)
    write_generic(OUT / "plates" / "VoiceClock_back_plate_only_generic.3mf", BACK_PLATE_ONLY_PLA)
    write_generic(OUT / "plates" / "VoiceClock_internals_PLA_generic.3mf", INTERNALS_PLA)
    write_generic(OUT / "plates" / "VoiceClock_light_ring_PETG_generic.3mf",      # one body; generic slicers get one colour
                  [("ring_shell" if n == "ring_shell_2c" else n, e, x, y, r) for n, e, x, y, r in LIGHT_RING_PETG])
    write_generic(OUT / "plates" / "VoiceClock_internals_with_back_plate_PLA_generic.3mf", INTERNALS_WITH_BACK_PLATE_PLA)
    for old in OUT.glob("VoiceClock_plate*.3mf"):
        old.unlink()
    for old in ("internals_PETG", "internals_PETG_generic", "internals_with_back_plate_PETG",
                "internals_with_back_plate_PETG_generic"):           # v2 first cut: internals were PETG
        (OUT / "plates" / f"VoiceClock_{old}.3mf").unlink(missing_ok=True)
    print("\nall plates verified")
