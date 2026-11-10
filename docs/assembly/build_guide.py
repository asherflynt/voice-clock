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
    ("1", "Front shell, rear shell, back plate, mute button", "Matte PLA, or the wood variant (print/wood/)",
     "5 mm brim on the shells, no supports. Front shell face-up (seam on the bed), rear shell on its back rim."),
    ("2", "Carrier, spider bracket", "The same matte PLA", "A little stiffer than PETG and more accurate for the key notches and insert holes. Spider at 100% infill."),
    ("3", "Ring base, ring shell, mute button", "Natural or clear PETG", "The ring cap must be translucent. No brim on the ring parts: it can't be peeled off their thin walls. Use this mute button rather than the PLA one: its snap barb is tougher in PETG."),
    ("4", "2 grip pads, 4 speaker washers", "TPU", "The grip pads stop the clock turning when you turn the knob."),
]
HARDWARE = [
    ("3", "M3 × 12 socket head", "Spider to the CrowPanel hub (replaces its 3 rear screws)"),
    ("3", "M2 × 20 socket head", "Carrier, through the reSpeaker and the ring base's spacers, into the spider"),
    ("4", "M2 × 10 socket head", "Speaker (2), USB-C breakout (2)"),
    ("7", "M2 heat-set insert (3 × 3.2 mm)", "Spider 3, speaker bosses 2, USB-C pads 2"),
    ("1", "USB-C breakout with 5.1 kΩ CC resistors", "Power inlet on the back plate"),
    ("—", "Aluminium foil tape, about 50 mm wide, non-conductive adhesive", "Lines the light channel"),
    ("—", "1/16\" adhesive closed-cell foam", "4 mic gaskets, 1 speaker ring"),
    ("about 160 g", "Steel BBs or shot (4.5 mm airgun BBs) + slow-cure epoxy, or about 300 g tungsten putty", "Ballast pocket in the rear shell"),
    ("—", "CA (superglue)", "Grip pads"),
    ("—", "22 AWG silicone wire, 2-pin JST-SM or JST-XH pair, MX1.25 4-pin pigtail, heat shrink, zip tie", "Power harness (docs/wiring/WIRING.md)"),
]
TOOLS = ["Soldering iron with an M2 heat-set tip", "Hex keys 1.5 and 2.5 mm", "Multimeter",
         "Wire strippers, flush cutters, heat gun", "Craft knife", "5 mm and 2 mm hole punch"]
ELECTRONICS = ["Elecrow CrowPanel 2.1\" rotary display", "Seeed reSpeaker XVF3800 with XIAO ESP32-S3",
               "4428 3 W 8 Ω speaker", "5 V 3 A USB-C charger"]

# guide step -> (render id(s) or None, title, instructions, check)
STEPS = [
    (("step_01", "step_01b"), "Heat-set inserts",
     ["The M2 insert holes are Ø2.9, the size already confirmed on this printer. All 7 inserts go into PLA, so set the iron to about 190–200 °C.",
      "Spider (first picture): 3 inserts in the underside at the end of each arm.",
      "Back plate, speaker bosses (second picture): 2 inserts in the round bosses either side of the grille. The holes run deep on purpose: there is room below the screw tip for the plastic the insert pushes down.",
      "Back plate, USB-C pads: the two small blocks either side of the USB-C slot. Press 1 insert into each <b>horizontally from the side facing the speaker bosses</b> (the face with the lead-in chamfer), flush with that face. The holes sit only 2.9 mm above the plate, so use a slim insert tip and tilt the iron a few degrees up off the plate, or prop the plate on a wedge. Support the pad from the slot side while you press."],
     "Run an M2 screw into each insert by hand. It should start straight and stop on the thread, not on plastic."),
    (None, "Power harness",
     ["Follow <code>docs/wiring/WIRING.md</code>.",
      "Leave about 30 mm of slack in the USB-C lead and the speaker lead: the back plate turns 32° when it locks."],
     "With a multimeter, confirm 5 V and GND are not shorted. Power both boards on the bench and confirm they boot before anything goes into the case."),
    ("step_02", "Spider bracket onto the CrowPanel",
     ["Remove the three M3 screws from the hub on the back of the CrowPanel.",
      "Fit the spider so its arms run between the three 4-pin connectors. Only one position leaves all the connectors clear.",
      "Fit 3 × M3 × 12 and tighten them evenly. The holes are a close fit (Ø3.1), so the screws may need a gentle turn to start."],
     "The knob still turns and clicks, and nothing touches the connectors."),
    ("step_03", "Light ring, part 1 (ring base)",
     ["Wrap aluminium foil tape round the <b>outside</b> of the ring base's tall wall, from 1 mm above the bottom edge up to 2 mm below the top edge. Keep it smooth (it is the channel's mirror) and keep it off the top 2 mm, where the crush ribs and key slots are. Use tape with non-conductive adhesive: the LED capacitors sit just outside the bottom edge.",
      "Plug the CrowPanel lead (the pigtail already soldered to the reSpeaker header) into the panel's power port.",
      "Slide the ring base over the spider <b>from behind</b>, until its three spacers sit under the spider's insert pads. There is no cable notch: the lead stays inside the ring, between the spider arms."],
     "The ring base sits square on the spider pads and the foil is smooth."),
    (("step_04", "step_05"), "reSpeaker and carrier",
     ["Lay the reSpeaker on the ring base's spacers, LED side toward the display, mute button (marked A) at 12 o'clock. The ring base's foot surrounds the LED ring; the CrowPanel lead stays inside it, flat in the gap between the board and the spider.",
      "Feed the speaker lead and the reSpeaker power lead through the carrier's centre hole, the only wire opening. Set the carrier behind the board.",
      "Fit 3 × M2 × 20 from the back of the carrier, through the board and the spacers, into the spider. <b>Snug only</b>: the screws pull the spider's inserts toward their mouths."],
     "The board doesn't rock and no wire is pinched."),
    ("step_06", "Light ring, part 2 (ring shell)",
     ["Line the <b>inside</b> of the ring shell's sleeve with foil tape, from the bottom edge up to about 4 mm below the cap. The part of the sleeve that stands out of the case stays bare so it glows.",
      "Press the ring shell on over the knob, with its two tabs in the ring base's slots. The skirt under its cap slides down round the top of the ring base, the crush ribs hold it, and the cap now covers the ring base's top edge, so no gap shows at the face."],
     "Power the boards on the bench and set the LED ring white. The whole ring should glow evenly, with no bright gap round the knob and no LED visible."),
    ("step_07", "Ballast and grip pads",
     ["Stand the rear shell on its back opening. Inside, along the bottom, a thin curved wall forms a pocket between itself and the shell, open at the top.",
      "<b>Steel shot:</b> mix a small batch of <b>slow-cure</b> epoxy (30 minutes or longer), stir in steel BBs, and spoon it into the pocket. Fill to about 1 mm below the pocket's rim, in two layers a few hours apart. A thick pour of fast epoxy gets hot enough to soften PLA (about 55 °C). <b>Tungsten putty:</b> press it in, then skim the top with a little epoxy so it can't move.",
      "Let it cure fully before the stack goes in: the carrier sits 2 mm above the rim.",
      "Glue the two TPU grip pads into the shallow recesses in the flat base (the large one on the rear shell, the small one on the front shell) with a few drops of CA."],
     "Nothing stands above the pocket's rim, and the pads sit flat in their recesses."),
    ("step_08", "Into the rear shell",
     ["Push the mute button into the hole at the top of the rear shell from outside until its barb clicks.",
      "Stand the rear shell on its back opening and pass the speaker and power leads out through it.",
      "Lower the stack in, display up, mute button (A) under the plunger. The carrier's 4 notches (with lead-in chamfers) slide down over the 4 ribs on the shell wall, and the board edge lands on the rib pads. It only goes in one way."],
     "The stack can't turn at all."),
    ("step_09", "Front shell (twist lock)",
     ["Stick a foam gasket (Ø5 with a Ø2 hole) onto the underside of each of the 4 mic boots inside the front shell, hole over the channel. In v2 the gaskets ride on the shell, not on the board.",
      "Hold the front shell over the knob turned about 10° <b>anticlockwise</b> (seen from the front) from its final position. The base flats are then a finger's width apart. Lower it until the rims meet; it only drops fully in that one position.",
      "Turn it <b>clockwise</b> (seen from the front) about 10° until four small detent fingers click and it stops. The flat bases now line up.",
      "To open it: turn the front shell anticlockwise about 10° (firmly, past the clicks) until the flat bases are offset by a finger's width, and lift it off."],
     "The seam is closed all the way round, the flat bases line up, and the shells don't turn or pull apart by hand."),
    (("step_10", "step_10b"), "USB-C and speaker on the back plate",
     ["Stand the USB-C breakout on its USB edge with the socket down through the slot, socket side against the two pads (the socket sits between them). Its plain back faces the plate's rim.",
      "Fit 2 × M2 × 10 from the <b>rim side</b>: through the board's holes into the pads' inserts. The hex key comes straight in over the plate from its edge, so a short key is easiest. The first picture shows the plate turned round, with the rim at the top.",
      "Stick a foam ring round the speaker's face. Washer, ear, washer on each boss, then 2 × M2 × 10, snug only.",
      "Zip-tie the speaker lead to the anchor.",
      "The USB-C screws stay reachable from the rim, so the board can come off later without removing the speaker.",
      "The speaker sits 6 mm off-centre, toward the anchor, which leaves about 16 mm between the USB-C board and the speaker for the board's JST plug and its lead."],
     "A USB-C cable plugs in fully from outside, and the speaker touches the plate only through the foam and washers."),
    ("step_11", "Back plate (twist lock)",
     ["Plug the inlet's lead into the harness and tuck the wires clear of the speaker.",
      "Hold the plate so the USB-C socket is at about 5 o'clock seen from the back. The three lugs only drop through the lip in that position (the top lug is the wide one).",
      "Push it in and turn it <b>clockwise</b> (seen from the back) about one clock hour, until both pawls click and it stops with the USB-C at 6 o'clock.",
      "To open it: put a coin in the slot on the back and turn it anticlockwise, seen from the back, past the two pawl clicks."],
     "Plug in a 5 V 3 A charger. The clock face comes up and the LED ring lights."),
]

FIRMWARE = ("Flash the clock face with the ESPHome config in <code>firmware/</code>, and the reSpeaker with the formatBCE "
            "XVF3800 integration. Cap the speaker volume (the runaway follow-up loop seen on 6 Nov ran at 100 %). The v2 "
            "spider turns the CrowPanel 5° clockwise to cancel the tilt seen on v1; the firmware has no trim, so check the "
            "dial by eye. If 12 still sits X° anticlockwise, change <code>CP_ROT_TRIM_DEG</code> in "
            "<code>cad/voice_clock.py</code> by -X° and reprint the spider.")


def esc(s):
    s = html.escape(s, quote=False)
    for t in ("code", "b"):
        s = s.replace(f"&lt;{t}&gt;", f"<{t}>").replace(f"&lt;/{t}&gt;", f"</{t}>")
    return s


def md(s):
    return s.replace("<code>", "`").replace("</code>", "`").replace("<b>", "**").replace("</b>", "**")


WIRING_SVG = """<svg class="wiring" viewBox="0 0 720 300" role="img" aria-label="Power wiring: the USB-C inlet feeds a 2-pin disconnect, then the reSpeaker header; the CrowPanel is fed from the header's spare 5V and GND pins through a pigtail into its power port.">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink)"/></marker></defs>
  <g font-family="var(--mono)" font-size="13" fill="var(--ink)">
    <rect x="16" y="112" width="150" height="76" rx="8" fill="var(--panel)" stroke="var(--rule)"/>
    <text x="91" y="142" text-anchor="middle" font-weight="600">USB-C inlet</text>
    <text x="91" y="162" text-anchor="middle" fill="var(--muted)">5.1 kΩ CC, back plate</text>
    <rect x="230" y="122" width="110" height="56" rx="8" fill="var(--panel)" stroke="var(--rule)"/>
    <text x="285" y="148" text-anchor="middle" font-weight="600">2-pin SM/XH</text>
    <text x="285" y="166" text-anchor="middle" fill="var(--muted)">disconnect</text>
    <rect x="470" y="30" width="234" height="76" rx="8" fill="var(--panel)" stroke="var(--rule)"/>
    <text x="587" y="56" text-anchor="middle" font-weight="600">reSpeaker XVF3800</text>
    <text x="587" y="76" text-anchor="middle" fill="var(--muted)">header 5V + GND (back)</text>
    <rect x="470" y="194" width="234" height="76" rx="8" fill="var(--panel)" stroke="var(--rule)"/>
    <text x="587" y="224" text-anchor="middle" font-weight="600">CrowPanel 2.1"</text>
    <text x="587" y="244" text-anchor="middle" fill="var(--muted)">MX1.25 pigtail, power port</text>
    <path d="M166 150 H226" stroke="var(--red)" stroke-width="3" fill="none" marker-end="url(#ah)"/>
    <path d="M340 150 H400 V68 H466" stroke="var(--red)" stroke-width="3" fill="none" marker-end="url(#ah)"/>
    <path d="M587 106 V190" stroke="var(--red)" stroke-width="2" fill="none" marker-end="url(#ah)"/>
    <text x="196" y="138" text-anchor="middle" fill="var(--muted)">22 AWG</text>
    <text x="432" y="58" text-anchor="middle" fill="var(--muted)">22 AWG</text>
    <text x="577" y="146" text-anchor="end" fill="var(--muted)">spare 5V/GND pins</text>
    <text x="577" y="162" text-anchor="end" fill="var(--muted)">MX1.25 pigtail</text>
    <text x="587" y="98" text-anchor="middle" fill="var(--muted)" font-size="11">the speaker plugs in here too</text>
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
        rids = (rid,) if isinstance(rid, str) else (rid or ())
        fig = ("".join(f'<figure><img src="{img_prefix}{r}.jpg" alt="Step {i}: {esc(title)}" loading="lazy" width="1800" height="1350"></figure>'
                       for r in rids) if rids else WIRING_SVG)
        lis = "".join(f"<li>{esc(t)}</li>" for t in todo)
        steps.append(f'''<section class="step" id="step-{i}">
  <header><span class="num">{i:02d}</span><h2>{esc(title)}</h2></header>
  {fig}
  <div class="body">{"".join(legend_html(r) for r in rids) if rids else '<div><h3 class="eyebrow">Parts</h3><ul class="plain"><li>USB-C breakout</li><li>22 AWG wire</li><li>2-pin JST-SM or JST-XH pair</li><li>MX1.25 4-pin pigtail</li><li>Heat shrink</li></ul></div>'}
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
      <p class="lede">A knit-textured 116 mm sphere around a CrowPanel 2.1" knob display, a reSpeaker XVF3800 microphone array and a 3 W speaker. Eleven steps. v2: both shells twist-lock with detent clicks, the electronics stack is keyed so it can't turn, the light ring is a foil-lined channel, and a steel-shot ballast keeps it still when you turn the knob.</p>
      <div class="facts"><span><b>10</b>printed parts</span><span><b>10</b>screws</span><span><b>7</b>heat-set inserts</span><span><b>2</b>twist locks</span></div>
    </div>
    <img src="{img_prefix}hero_front.jpg" alt="The finished Voice Clock: a knit-textured sphere with a round clock display and a glowing light ring" width="1800" height="1350">
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
        <p style="margin-top:18px">{esc(FIRMWARE)}</p>
      </section>
      <footer>Renders are generated from the parametric CAD in <code>cad/</code> with Blender Cycles; the numbered callouts are placed automatically on visible surfaces. Licensed MIT.</footer>
    </main>
  </div>
</div>'''


def markdown():
    out = ["# Voice Clock assembly (v2)", "", "![Finished Voice Clock](img/hero_front.jpg)", "",
           "> **v2, 6 Nov 2026.** The shells twist-lock, the stack is keyed, the light ring is a foil-lined channel, the "
           "USB-C board and speaker screw into heat-set inserts, and a ballast pocket plus TPU grip pads keep the clock "
           "still when you turn the knob. Pictures are rendered from `cad/`; this file is generated by `build_guide.py`.", "",
           "## Before you start", "", "| Plate | Parts | Material | Notes |", "|---|---|---|---|"]
    out += [f"| {p} | {a} | {b} | {c} |" for p, a, b, c in PLATES]
    out += ["", "**Electronics:** " + "; ".join(ELECTRONICS), "", "**Tools:** " + "; ".join(TOOLS), "",
            "| Qty | Part | Where it goes |", "|---|---|---|"]
    out += [f"| {q} | {a} | {b} |" for q, a, b in HARDWARE]
    for i, (rid, title, todo, check) in enumerate(STEPS, 1):
        out += ["", f"## {i}. {title}", ""]
        if rid:
            for r in ((rid,) if isinstance(rid, str) else rid):
                out += [f"![Step {i}](img/{r}.jpg)", ""]
                if LEG.get(r):
                    out += ["In this picture: " + ", ".join(f"**{it['n']}** {it['label']}" for it in LEG[r]), ""]
        else:
            out += ["```mermaid", "flowchart LR", "  A[USB-C inlet, 5.1k CC] -- 22 AWG --> B[2-pin SM/XH disconnect]",
                    "  B -- 22 AWG, carrier centre hole --> C[reSpeaker header 5V + GND]", "  C -- MX1.25 pigtail from the spare 5V + GND pins --> D[CrowPanel power port]", "```", ""]
        out += [f"{k}. {md(t)}" for k, t in enumerate(todo, 1)]
        out += ["", f"> **Check:** {md(check)}"]
    out += ["", "## Finished", "", "![Back](img/hero_back.jpg)", "", "## Firmware", "", md(FIRMWARE)]
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
