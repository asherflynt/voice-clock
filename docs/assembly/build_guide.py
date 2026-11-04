"""Build the assembly guide from one source.

python3 docs/assembly/build_guide.py [--fragment out.html]
Writes docs/assembly/index.html (standalone page, GitHub Pages) and docs/assembly/ASSEMBLY.md.
--fragment also writes the page body without the document skeleton (for hosts that add their own).
Callout legends come from img/callouts.json, written by cad/blender/callouts.py.
"""
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEG = json.loads((HERE / "img" / "callouts.json").read_text())

PLATES = [
    ("1", "Front shell, rear shell", "Matte PLA", "5 mm brim, no supports. Shells print face-down and rim-down."),
    ("2", "Carrier, back plate, spider bracket, mute button, 3 spacers, insert test block", "Matte PLA", "Print this plate first. Spider and spacers at 100% infill."),
    ("3", "Light guide", "Clear or natural PETG", "100% infill for an even glow. Bezel face down."),
    ("4", "4 speaker washers (optional)", "TPU", "Or use M2 rubber washers."),
]
HARDWARE = [
    ("3", "M3 × 12 socket head", "Spider to the CrowPanel hub (replaces its 3 rear screws)"),
    ("3", "M2 × 20 socket head", "Carrier through the reSpeaker into the spider"),
    ("3", "M3 × 6 socket head", "Carrier rim to the front shell"),
    ("6", "M3 × 8 button head", "Rear shell to the carrier (3), back plate to the rear shell (3)"),
    ("2", "M2 × 10 socket head", "Speaker"),
    ("9", "M3 heat-set insert (4 × 4.2 mm)", "Front shell 3, carrier 3, rear shell 3"),
    ("5", "M2 heat-set insert (3 × 3.2 mm)", "Spider 3, back plate 2"),
    ("1", "USB-C breakout with 5.1 kΩ CC resistors", "Power inlet, glued into the back plate"),
    ("—", "1/16\" adhesive closed-cell foam", "4 mic gaskets, 1 speaker ring"),
    ("—", "22 and 24 AWG silicone wire, 2-pin JST-SM or JST-XH pair, MX1.25 4-pin pigtail, heat shrink, zip tie, 5-minute epoxy", "Power harness (see docs/wiring/WIRING.md)"),
]
TOOLS = ["Soldering iron with M2 and M3 heat-set tips and a 2 mm chisel tip", "Hex keys 1.5, 2.0 and 2.5 mm, plus a 2.0 mm driver with a 60 mm or longer shaft",
         "Multimeter", "Wire strippers, flush cutters, heat gun or lighter", "Tweezers, craft knife, 5 mm and 2 mm hole punch (or scissors)"]
ELECTRONICS = ["Elecrow CrowPanel 2.1\" rotary display (ESP32-S3)", "Seeed reSpeaker XVF3800 4-mic array with XIAO ESP32-S3",
               "4428 3 W 8 Ω speaker with JST-PH lead", "5 V 3 A USB-C charger"]

# guide step -> (render id or None, title, instructions, check)
STEPS = [
    ("step_01", "Heat-set inserts",
     ["Print the insert test block from plate 2 first. Set one insert in each hole and note which hole (1, 2 or 3 dots) holds best. The middle one is the default; if another fits better, change the hole size in <code>cad/voice_clock.py</code> and reprint.",
      "Set the iron to 190–200 °C for PLA. Press each insert straight in until it is flush, then hold a flat tool on it for a few seconds while it cools.",
      "Front shell: 3 × M3 in the lugs just inside the split. Carrier: 3 × M3 from the back face (use inserts 5 mm long or shorter here). Rear shell: 3 × M3 in the lugs at the back opening.",
      "Spider: 3 × M2 in the underside at the end of each arm. Back plate: 2 × M2 in the speaker bosses."],
     "Run a screw into each insert by hand. It should start straight and stop on the thread, not on a blob of plastic."),
    (None, "Power harness",
     ["Follow the wiring sheets in <code>docs/wiring/WIRING.md</code> (printable PDF there too). Do their bench checks first.",
      "Solder 10 cm of 22 AWG red and black from the USB-C breakout's VBUS and GND pads to the socket half of a 2-pin JST-SM or JST-XH pair. This lead stays with the back plate.",
      "From the pin half, make a Y splice: one 22 AWG pair to the reSpeaker's 2×10 header (5V row 1 right, GND row 2 left, on the back), and one 24 AWG pair spliced to a spare MX1.25 4-pin pigtail for the CrowPanel's power port. Find the port's 5 V and GND positions with a meter on the supplied USB cable first.",
      "Cover every joint with heat shrink and strain-relieve the solder joints so a tug never loads a pad.",
      "Plug the speaker lead into the reSpeaker's speaker socket. It runs through the carrier's centre hole later."],
     "With a multimeter, confirm 5 V and GND are not shorted. Power both boards on the bench and confirm they boot before anything goes into the case. Never plug a laptop into either board while the USB-C inlet is powered."),
    ("step_02", "Spider bracket onto the CrowPanel",
     ["Remove the three M3 screws from the hub on the back of the CrowPanel.",
      "Fit the spider so its hub sits on the CrowPanel hub. Turn it so its arms run between the three 4-pin connectors; only one of the three screw positions leaves all the connectors uncovered.",
      "Fit 3 × M3 × 12 from the spider side into the hub. Tighten evenly until snug."],
     "The knob still turns and still clicks when pressed, and nothing touches the connectors."),
    ("step_05", "Light guide from behind",
     ["Slide the light guide over the spider from behind and onto the display. Its inner lip is smaller than the knob, so it only goes on this way. It stops when the lip meets the back of the display housing and stays loose for now: the front shell pushes it back onto the reSpeaker in step 7.",
      "Turn it so its cable notch sits over the CrowPanel power wires, lower left seen from the front.",
      "Punch four foam rings (5 mm across with a 2 mm hole) and stick one over each microphone hole on the front of the reSpeaker, on its four diagonals."],
     "The light guide turns freely around the knob ring with an even gap all round."),
    ("step_03", "Spacers and reSpeaker",
     ["Set the three printed spacers on the spider's M2 inserts.",
      "Lay the reSpeaker on the spacers with its LED ring and foam gaskets facing the display. The mute button (marked A) goes at 12 o'clock and the RST button at 6 o'clock; the XIAO module then sits at 3 o'clock seen from the front.",
      "Keep the CrowPanel wires in the light guide's notch."],
     "All three reSpeaker mounting holes line up with the spacers, and no wire is trapped under the light guide."),
    ("step_04", "Carrier and clamp screws",
     ["Feed the speaker lead through the carrier's centre hole.",
      "Set the carrier behind the reSpeaker with its cable notch lined up with the light guide's notch (lower left seen from the front, lower right seen from the back).",
      "Fit 3 × M2 × 20 from the back of the carrier, through the board and spacers, into the spider inserts. Tighten in turn until snug."],
     "The board doesn't rock and no wire is pinched."),
    ("step_06", "Into the front shell",
     ["Drop the mute button into the hole at the top of the front shell, cap outside.",
      "Slide the whole stack into the front shell from behind, knob first. The shell's bezel ring pushes the light guide back until it sits flat on the reSpeaker, lip over the LED ring. Push on until the carrier rim sits on the three lugs.",
      "Fit 3 × M3 × 6 through the carrier rim into the lug inserts."],
     "Pressing the mute button clicks the reSpeaker's mute switch. The knob stands about 7 mm proud of the face and still presses."),
    ("step_07", "Rear shell",
     ["The speaker is still hanging on its lead: pass it out through the rear shell's back opening first.",
      "Fit the rear shell to the front shell so its three inner ribs land on the carrier's inserts.",
      "Reach through the open back with the long 2.0 mm driver and fit 3 × M3 × 8 button head through the ribs."],
     "The seam between the shells closes evenly all the way round."),
    ("step_08", "Speaker and USB-C on the back plate",
     ["Stick a foam ring around the speaker's face.",
      "The speaker stays plugged into the reSpeaker; work with the back plate next to the clock. Set a TPU washer on each speaker boss, place the speaker with its face toward the round grille and its lead toward the top, then add a washer on top of each ear.",
      "Fit 2 × M2 × 10. Snug only: the washers do the isolation, so don't crush them.",
      "Stand the USB-C breakout on its USB edge with the socket in the slot, board against the backing wall, and fit 2 × M2 × 10 through its holes into the wall. Zip-tie the speaker lead to the anchor."],
     "A USB-C cable plugs in fully from outside, and the speaker doesn't touch the plate anywhere except the foam and washers."),
    ("step_09", "Close up",
     ["Plug the inlet's JST lead into the harness and tuck the wires clear of the speaker.",
      "Fit the back plate with the grille over the speaker and the USB-C port at the bottom.",
      "Fit 3 × M3 × 8 button head."],
     "Plug in a 5 V 3 A charger. The clock face comes up and the LED ring lights. Then flash and set up the firmware."),
]


def esc(s):
    return html.escape(s, quote=False).replace("&lt;code&gt;", "<code>").replace("&lt;/code&gt;", "</code>")


WIRING_SVG = """<svg class="wiring" viewBox="0 0 720 300" role="img" aria-label="Power wiring: the USB-C inlet feeds a 2-pin disconnect, which splits to the reSpeaker header 5V pin and a pigtail into the CrowPanel power port.">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink)"/></marker></defs>
  <g font-family="var(--mono)" font-size="13" fill="var(--ink)">
    <rect x="16" y="112" width="150" height="76" rx="8" fill="var(--panel)" stroke="var(--rule)"/>
    <text x="91" y="142" text-anchor="middle" font-weight="600">USB-C inlet</text>
    <text x="91" y="162" text-anchor="middle" fill="var(--muted)">5.1 kΩ CC, back plate</text>
    <rect x="230" y="122" width="110" height="56" rx="8" fill="var(--panel)" stroke="var(--rule)"/>
    <text x="285" y="148" text-anchor="middle" font-weight="600">2-pin SM/XH</text>
    <text x="285" y="166" text-anchor="middle" fill="var(--muted)">disconnect</text>
    <rect x="470" y="30" width="234" height="76" rx="8" fill="var(--panel)" stroke="var(--rule)"/>
    <text x="587" y="60" text-anchor="middle" font-weight="600">reSpeaker XVF3800</text>
    <text x="587" y="80" text-anchor="middle" fill="var(--muted)">header 5V + GND (back)</text>
    <rect x="470" y="194" width="234" height="76" rx="8" fill="var(--panel)" stroke="var(--rule)"/>
    <text x="587" y="224" text-anchor="middle" font-weight="600">CrowPanel 2.1"</text>
    <text x="587" y="244" text-anchor="middle" fill="var(--muted)">MX1.25 pigtail, power port</text>
    <path d="M166 150 H226" stroke="var(--red)" stroke-width="3" fill="none" marker-end="url(#ah)"/>
    <path d="M340 150 H400 V68 H466" stroke="var(--red)" stroke-width="3" fill="none" marker-end="url(#ah)"/>
    <path d="M400 150 V232 H466" stroke="var(--red)" stroke-width="2" fill="none" marker-end="url(#ah)"/>
    <text x="196" y="138" text-anchor="middle" fill="var(--muted)">22 AWG</text>
    <text x="432" y="58" text-anchor="middle" fill="var(--muted)">22 AWG</text>
    <text x="432" y="252" text-anchor="middle" fill="var(--muted)">24 AWG</text>
    <text x="587" y="128" text-anchor="middle" fill="var(--muted)">speaker lead plugs in here too</text>
  </g>
</svg>"""

CSS = """
/* Layout: a workshop manual. Sticky step index on wide screens, one column of
   figure + parts legend + instructions per step. */
:root{
  --bg:#f8f4f3; --panel:#ffffff; --ink:#2a2224; --muted:#6f6264; --rule:#e5dad8;
  --accent:#7a1830; --pink:#d39b95; --red:#c6372f; --callout:#ff6a13; --check-bg:#f1ebe0; --check-rule:#d9c9ab;
  --display:"Bricolage Grotesque", "Avenir Next", "Segoe UI", system-ui, sans-serif;
  --body:"Instrument Sans", "Segoe UI", system-ui, sans-serif;
  --mono:"IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#171213; --panel:#221b1c; --ink:#f1e9e8; --muted:#b4a5a6; --rule:#3a2f30;
  --accent:#f0a3b2; --pink:#d39b95; --red:#ff7a6e; --check-bg:#2a2420; --check-rule:#5a4a35; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#171213; --panel:#221b1c; --ink:#f1e9e8; --muted:#b4a5a6; --rule:#3a2f30;
  --accent:#f0a3b2; --pink:#d39b95; --red:#ff7a6e; --check-bg:#2a2420; --check-rule:#5a4a35; color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg); color:var(--ink); font-family:var(--body); font-size:16.5px; line-height:1.6; margin:0}
.wrap{max-width:1180px; margin:0 auto; padding-inline:clamp(16px,4vw,40px); padding-block:28px 80px}
h1,h2,h3{font-family:var(--display); text-wrap:balance; line-height:1.1; margin:0}
h1{font-size:clamp(2.4rem,6vw,4.2rem); font-weight:700; letter-spacing:-0.02em}
h2{font-size:clamp(1.6rem,3vw,2.2rem); font-weight:650; letter-spacing:-0.01em}
h3{font-size:1.05rem; font-weight:650}
p{margin:0}
code{font-family:var(--mono); font-size:.88em; background:var(--check-bg); padding:.05em .35em; border-radius:4px}
a{color:var(--accent)}
.eyebrow{font-family:var(--mono); font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; color:var(--muted)}
.hero{display:grid; grid-template-columns:minmax(0,1.05fr) minmax(0,1fr); gap:clamp(20px,4vw,48px); align-items:center; padding-block:12px 36px; border-bottom:1px solid var(--rule)}
.hero .lede{font-size:1.15rem; color:var(--muted); max-width:46ch; margin-top:16px}
.facts{display:flex; flex-wrap:wrap; gap:10px 22px; margin-top:22px; font-family:var(--mono); font-size:.86rem}
.facts span b{font-family:var(--display); font-size:1.5rem; display:block; color:var(--accent); font-weight:700}
.hero img{border-radius:14px; width:100%; height:auto; display:block}
.layout{display:grid; grid-template-columns:200px minmax(0,1fr); gap:44px; margin-top:40px}
nav.toc{position:sticky; top:calc(env(safe-area-inset-top,0px) + 20px); align-self:start; font-size:.92rem}
nav.toc ol{list-style:none; padding:0; margin:12px 0 0; display:grid; gap:6px; counter-reset:t}
nav.toc a{color:var(--ink); text-decoration:none; display:flex; gap:10px}
nav.toc a:hover,nav.toc a:focus-visible{color:var(--accent)}
nav.toc .n{font-family:var(--mono); color:var(--muted); min-width:1.6em}
section{scroll-margin-top:24px}
.prep{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:28px; margin-top:20px}
.card{background:var(--panel); border:1px solid var(--rule); border-radius:12px; padding:20px 22px}
.card h3{margin-bottom:10px}
table{width:100%; border-collapse:collapse; font-size:.92rem}
th,td{text-align:left; padding:7px 8px; border-bottom:1px solid var(--rule); vertical-align:top}
th{font-family:var(--mono); font-size:.74rem; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:500}
td.q{font-family:var(--mono); font-variant-numeric:tabular-nums; white-space:nowrap; color:var(--accent); font-weight:600}
.scroll{overflow-x:auto}
ul.plain{margin:0; padding-left:1.1em; display:grid; gap:4px}
.step{padding-block:44px; border-top:1px solid var(--rule)}
.step header{display:flex; align-items:baseline; gap:16px; margin-bottom:18px}
.step header .num{font-family:var(--display); font-size:3rem; font-weight:700; color:var(--pink); line-height:.9; font-variant-numeric:tabular-nums}
figure{margin:0}
figure img{width:100%; height:auto; display:block; border-radius:12px; border:1px solid var(--rule)}
.body{display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.35fr); gap:28px; margin-top:20px}
ol.legend{list-style:none; margin:0; padding:0; display:grid; gap:8px}
ol.legend li{display:flex; align-items:center; gap:10px; font-size:.95rem}
ol.legend .b{width:26px; height:26px; flex:none; border-radius:50%; background:var(--ink); color:var(--bg); font-family:var(--mono); font-size:.8rem; display:grid; place-items:center; font-weight:600}
ol.do{margin:0; padding-left:1.3em; display:grid; gap:10px}
ol.do li::marker{font-family:var(--mono); color:var(--muted)}
.check{margin-top:18px; background:var(--check-bg); border:1px solid var(--check-rule); border-radius:10px; padding:12px 16px; font-size:.95rem}
.check strong{font-family:var(--mono); font-size:.76rem; letter-spacing:.1em; text-transform:uppercase; display:block; color:var(--muted); margin-bottom:2px}
.wiring{width:100%; height:auto; max-width:720px; display:block; background:var(--panel); border:1px solid var(--rule); border-radius:12px}
.done{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; margin-top:18px}
.done img{width:100%; height:auto; border-radius:12px; border:1px solid var(--rule)}
footer{margin-top:56px; padding-top:20px; border-top:1px solid var(--rule); color:var(--muted); font-size:.9rem}
@media (max-width:900px){
  .hero,.layout,.body,.prep,.done{grid-template-columns:minmax(0,1fr)}
  nav.toc{position:static}
}
"""

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=IBM+Plex+Mono:wght@400;500;600&family=Instrument+Sans:wght@400;600&display=swap">'


def legend_html(rid):
    items = LEG.get(rid, [])
    if not items:
        return ""
    lis = "".join(f'<li><span class="b">{it["n"]}</span>{esc(it["label"])}</li>' for it in items)
    return f'<div><h3 class="eyebrow">In this picture</h3><ol class="legend">{lis}</ol></div>'


def page(img_prefix="img/"):
    toc = ['<li><a href="#before"><span class="n">0</span>Before you start</a></li>']
    for i, (_, title, _, _) in enumerate(STEPS, 1):
        toc.append(f'<li><a href="#step-{i}"><span class="n">{i}</span>{esc(title)}</a></li>')
    toc.append(f'<li><a href="#done"><span class="n">✓</span>Finished</a></li>')
    plates = "".join(f'<tr><td class="q">{p}</td><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>' for p, a, b, c in PLATES)
    hw = "".join(f'<tr><td class="q">{q}</td><td>{esc(a)}</td><td>{esc(b)}</td></tr>' for q, a, b in HARDWARE)
    steps = []
    for i, (rid, title, todo, check) in enumerate(STEPS, 1):
        fig = (f'<figure><img src="{img_prefix}{rid}.jpg" alt="Step {i}: {esc(title)}" loading="lazy" width="1800" height="1350"></figure>'
               if rid else WIRING_SVG)
        lis = "".join(f"<li>{esc(t)}</li>" for t in todo)
        steps.append(f'''<section class="step" id="step-{i}">
  <header><span class="num">{i:02d}</span><h2>{esc(title)}</h2></header>
  {fig}
  <div class="body">{legend_html(rid) if rid else '<div><h3 class="eyebrow">Parts</h3><ul class="plain"><li>USB-C breakout</li><li>22 and 24 AWG wire</li><li>2-pin JST-SM or JST-XH pair</li><li>MX1.25 4-pin pigtail</li><li>Heat shrink</li></ul></div>'}
    <div><ol class="do">{lis}</ol><div class="check"><strong>Check before moving on</strong>{esc(check)}</div></div>
  </div>
</section>''')
    return f'''<title>Voice Clock Assembly</title>
{FONTS}
<style>{CSS}</style>
<div class="wrap">
  <div class="hero">
    <div>
      <p class="eyebrow">Open-source Home Assistant voice clock · assembly guide</p>
      <h1>Voice Clock assembly</h1>
      <p class="lede">A knit-textured 120 mm sphere around a CrowPanel 2.1" knob display, a reSpeaker XVF3800 microphone array and a 3 W speaker. Ten steps. The only glue is for the USB-C inlet.</p>
      <div class="facts"><span><b>10</b>printed parts</span><span><b>17</b>screws</span><span><b>14</b>heat-set inserts</span><span><b>2</b>thread sizes</span></div>
    </div>
    <img src="{img_prefix}hero_front.jpg" alt="The finished Voice Clock: a pink knit-textured sphere with a round clock display" width="1800" height="1350">
  </div>
  <div class="layout">
    <nav class="toc" aria-label="Steps"><p class="eyebrow">Steps</p><ol>{"".join(toc)}</ol></nav>
    <main>
      <section id="before"><h2>Before you start</h2>
        <div class="prep">
          <div class="card"><h3>Print plates</h3><div class="scroll"><table><thead><tr><th>Plate</th><th>Parts</th><th>Material</th><th>Notes</th></tr></thead><tbody>{plates}</tbody></table></div></div>
          <div class="card"><h3>Electronics</h3><ul class="plain">{"".join(f"<li>{esc(e)}</li>" for e in ELECTRONICS)}</ul><h3 style="margin-top:16px">Tools</h3><ul class="plain">{"".join(f"<li>{esc(t)}</li>" for t in TOOLS)}</ul></div>
        </div>
        <div class="card" style="margin-top:28px"><h3>Hardware</h3><div class="scroll"><table><thead><tr><th>Qty</th><th>Part</th><th>Where it goes</th></tr></thead><tbody>{hw}</tbody></table></div></div>
      </section>
      {"".join(steps)}
      <section class="step" id="done"><header><span class="num">✓</span><h2>Finished</h2></header>
        <div class="done"><img src="{img_prefix}hero_front.jpg" alt="Finished clock, front" loading="lazy"><img src="{img_prefix}hero_back.jpg" alt="Finished clock, back, with the speaker grille and USB-C inlet" loading="lazy"></div>
        <p style="margin-top:18px">Next: flash the clock face with the ESPHome config in <code>firmware/</code>, and the voice satellite on the reSpeaker with the formatBCE XVF3800 ESPHome integration. Cap the speaker volume in ESPHome; the amp can deliver more than the 3 W speaker is rated for.</p>
      </section>
      <footer>Renders are generated from the parametric CAD in <code>cad/</code> with Blender Cycles; the numbered callouts are placed automatically on visible surfaces. Licensed MIT.</footer>
    </main>
  </div>
</div>'''


def markdown():
    out = ["# Voice Clock assembly", "", "![Finished Voice Clock](img/hero_front.jpg)", "",
           "## Before you start", "", "| Plate | Parts | Material | Notes |", "|---|---|---|---|"]
    out += [f"| {p} | {a} | {b} | {c} |" for p, a, b, c in PLATES]
    out += ["", "**Electronics:** " + "; ".join(ELECTRONICS), "", "**Tools:** " + "; ".join(TOOLS), "",
            "| Qty | Part | Where it goes |", "|---|---|---|"]
    out += [f"| {q} | {a} | {b} |" for q, a, b in HARDWARE]
    for i, (rid, title, todo, check) in enumerate(STEPS, 1):
        out += ["", f"## {i}. {title}", ""]
        if rid:
            out += [f"![Step {i}](img/{rid}.jpg)", ""]
            if LEG.get(rid):
                out += ["In this picture: " + ", ".join(f"**{it['n']}** {it['label']}" for it in LEG[rid]), ""]
        else:
            out += ["```mermaid", "flowchart LR", "  A[USB-C inlet, 5.1k CC] -- 22 AWG --> B[2-pin SM/XH disconnect]",
                    "  B -- 22 AWG --> C[reSpeaker header 5V + GND]", "  B -- 24 AWG + MX1.25 pigtail --> D[CrowPanel power port]", "```", ""]
        out += [f"{k}. {t.replace('<code>', '`').replace('</code>', '`')}" for k, t in enumerate(todo, 1)]
        out += ["", f"> **Check:** {check}"]
    out += ["", "## Finished", "", "![Back](img/hero_back.jpg)", "",
            "Flash the clock face with the ESPHome config in [`firmware/`](../../firmware), and the reSpeaker with the formatBCE XVF3800 ESPHome integration. Cap the speaker volume in ESPHome."]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    body = page()
    (HERE / "index.html").write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
                                     '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
                                     + body.replace("<style>", "<style>img{max-width:100%}", 1).split("<div class=\"wrap\">")[0]
                                     + '</head><body><div class="wrap">' + body.split('<div class="wrap">', 1)[1] + "</body></html>\n")
    (HERE / "ASSEMBLY.md").write_text(markdown())
    if "--fragment" in sys.argv:
        Path(sys.argv[sys.argv.index("--fragment") + 1]).write_text(body)
    print("wrote index.html, ASSEMBLY.md")
