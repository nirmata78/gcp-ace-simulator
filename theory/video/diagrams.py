#!/usr/bin/env python3
"""All course diagrams → ./svg/*.svg, in the SD-09 palette and legibility rules (canvas 1600, large type)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/slide-video-kit/scripts"))
import c4svg as c4, seqsvg as sq
OUT = pathlib.Path(__file__).resolve().parent / "svg"; OUT.mkdir(exist_ok=True)
GREEN, GREEN_BG, RED, RED_BG, BLUE, BLUE_BG, AMBER, AMBER_BG = "#2d8a4e", "#e7f4ec", "#c8341f", "#fdecea", "#2f6fb5", "#e8f0fa", "#a86a12", "#fdf3e1"
TONES = {"g": (GREEN, GREEN_BG), "r": (RED, RED_BG), "b": (BLUE, BLUE_BG), "a": (AMBER, AMBER_BG)}

def seq(name, parts, steps, size=22, row=50):
    """steps: ('m'|'a'|'r', from, to, label[, 'hl']) · ('n', a, b, text[, tone]) · ('f', kind, cond) · ('e',)"""
    s = sq.Seq(1500, size=size, row=row, head=66)
    for p in parts: s.part(*p)
    for st in steps:
        k = st[0]; hl = len(st) > 4 and st[4] == "hl"
        if k == "m": s.msg(st[1], st[2], st[3], hl=hl)
        elif k == "a": s.msg(st[1], st[2], st[3], kind="async", hl=hl)
        elif k == "r": s.msg(st[1], st[2], st[3], kind="ret", hl=hl)
        elif k == "n": s.note(st[1], st[2], st[3], *[{"a":"amber","g":"green","r":"red","b":"blue"}[x] for x in st[4:5]])
        elif k == "f": s.frame(st[1], st[2])
        elif k == "e": s.end()
    s.save(OUT / f"{name}.svg")

def row(name, items, note=None, tone="b", arrows=False, focus=None, h=600, size=None, box=340):
    """Row of boxes: (title, type, description[, kind])."""
    d = c4.Diagram(1600, h); n = len(items); gap = 70 if arrows else 36; w = (1520 - (n - 1) * gap) // n
    for i, it in enumerate(items):
        kind = it[3] if len(it) > 3 else ("focus" if i == focus else "container")
        d.node(f"n{i}", 40 + i * (w + gap), 50, w, box, kind, it[0], it[1], it[2], size=size or (34 if n <= 3 else 29 if n == 4 else 25))
    if arrows:
        for i in range(n - 1): d.edge(f"n{i}", f"n{i+1}", "", src="r", dst="l", dashed=False)
    if note: d.note(40, 50 + box + 40, 1520, note, size=28, colour=TONES[tone][0], bg=TONES[tone][1])
    d.save(OUT / f"{name}.svg")

def tree(name, levels, note=None, h=None, size=25):
    """Indented hierarchy: levels = [(depth, title, type, desc, kind)]; drawn with elbows from the parent."""
    rh = 118; h = h or (len(levels) * rh + (110 if note else 30)); d = c4.Diagram(1600, h)
    stack = {}
    for i, (dep, t, ty, de, kind) in enumerate(levels):
        x = 40 + dep * 130; y = 14 + i * rh
        d.node(f"t{i}", x, y, 1520 - dep * 130 if de else 560, rh - 24, kind, t, ty, de, size=size)
        stack[dep] = (i, x)
        if dep:
            pi, px = stack[dep - 1]
            d.edge(f"t{pi}", f"t{i}", "", src="b:0.02" if False else "b", dst="l", via=[(px + 40, y + (rh - 24) / 2)], dashed=False) if False else None
    if note: d.note(40, len(levels) * rh + 14, 1520, note, size=22, colour=AMBER, bg=AMBER_BG)
    d.save(OUT / f"{name}.svg")

def bars(name, groups, h=620):
    """Stacked horizontal bars of percent shares: groups = [(label, [(pct, text, colour)])]."""
    d = c4.Diagram(1600, h); y = 40
    for label, segs in groups:
        d.text(40, y + 26, label, size=27, colour="#1f2328", bold=True); y += 44; x = 40
        for pct, text, col in segs:
            w = 1520 * pct / 100
            d.parts.append(f'<rect x="{x}" y="{y}" width="{w-6}" height="150" rx="8" fill="{col}"/>')
            for i, line in enumerate(c4.wrap(text, w - 26, 23)):
                d.parts.append(f'<text x="{x+w/2-3}" y="{y+52+i*29}" text-anchor="middle" font-family="{c4.FONT}" font-size="23" font-weight="700" fill="#fff">{c4.esc(line)}</text>')
            d.parts.append(f'<text x="{x+w/2-3}" y="{y+134}" text-anchor="middle" font-family="{c4.FONT}" font-size="25" font-weight="800" fill="#fff">{pct}%</text>')
            x += w
        y += 192
    d.save(OUT / f"{name}.svg")

c4.KIND["ask"] = c4.KIND["person"]
B1, B2, B3, B4, B5, G = "#1168bd", "#438dd5", "#c8341f", "#2d8a4e", "#7a5bc2", "#8c8c8c"

# ── Part 1 ─────────────────────────────────────────────────────────────────────────────────
bars("p1-guide-shift", [
    ("The previous guide: five sections", [(20, "Setup", G), (17.5, "Planning", G), (25, "Deploying", G), (20, "Operating", G), (17.5, "Security", G)]),
    ("The guide live since 30 June 2026: four sections", [(20, "1 Setup", B1), (30, "2 Plan and implement", B2), (30, "3 Ensure successful operation", B3), (20, "4 Access and security", B4)]),
], h=520)
row("p1-scope", [
    ("Zonal", "dies with its zone", "VMs · zonal disks · zonal MIGs · zonal clusters · TPU VMs"),
    ("Regional", "survives a zone", "subnets · regional disks · regional MIGs · Cloud SQL · Cloud Run · Cloud NAT · Cloud Router"),
    ("Global", "survives a region", "VPC · firewall rules · routes · images · snapshots · global LBs · Cloud DNS · IAM", "focus"),
], note="A VPC is global, its subnets are regional. Images and snapshots are global, so a disk can be recreated anywhere.", box=360, h=570)
row("p1-available", [
    ("Available?", "catalogue question", "Is the A3 series offered in this zone? machine-types list · accelerator-types list"),
    ("Allowed?", "governance question", "Nobody may create resources outside the EU. gcp.resourceLocations organization policy", "focus"),
], note="Neither answers the other: the catalogue tells you what exists, the policy tells you what is permitted.", box=300, h=500)
d = c4.Diagram(1600, 620)
d.node("cli", 40, 40, 400, 150, "container", "gcloud CLI", "gcloud auth login", "credentials for the command line", size=26)
d.node("adc", 600, 40, 400, 150, "focus", "Your code", "application-default login", "client libraries read ADC", size=26)
d.node("dock", 1160, 40, 400, 150, "container", "Docker daemon", "gcloud auth configure-docker", "credential helper for pushes", size=26)
d.note(40, 240, 1520, "Three clients, three credential stores. Logging in one does not log in the others.", size=25, colour=AMBER, bg=AMBER_BG)
d.note(40, 340, 1520, "The classic symptom: gcloud works on the laptop, but the program says it could not find default credentials. The fix is the middle box.", size=25, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "p1-three-clients.svg")

exec((pathlib.Path(__file__).parent / "diagrams_more.py").read_text()) if (pathlib.Path(__file__).parent / "diagrams_more.py").exists() else None
