"""Build the exam-eve theory recap booklet.

One topic = one page, deliberately. A recall page you can finish before your
attention moves is worth more the night before an exam than a chapter you
abandon halfway, and the fixed shape makes the whole booklet skimmable twice.

The page count is a promise, not an estimate: every section is probed for the
page it actually landed on, and the build reports any section that overflowed
its page. Theory pages are counted against the 15-page budget; the gcloud
appendix is reference material and sits outside it.

Run:  python scripts/recap.py [--open]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from recap_content import PAGES, TITLE, SUBTITLE
from src.paths import ensure_writable_dir, reports_dir

# --------------------------------------------------------------------------
# Palette — the simulator's report palette, unchanged so the three PDFs read
# as one family.
# --------------------------------------------------------------------------
INK = colors.HexColor("#12181f")
MUTED = colors.HexColor("#5b6875")
FAINT = colors.HexColor("#8695a4")
RULE = colors.HexColor("#d6dce3")
BAND = colors.HexColor("#f2f5f8")

GREEN = colors.HexColor("#1a7f4b")
GREEN_BG = colors.HexColor("#e7f4ec")
RED = colors.HexColor("#b3261e")
RED_BG = colors.HexColor("#fdeceb")
AMBER = colors.HexColor("#8a5a00")
AMBER_BG = colors.HexColor("#fff5e0")
BLUE = colors.HexColor("#1a56b0")
BLUE_BG = colors.HexColor("#eaf1fb")
TEAL = colors.HexColor("#0f6b73")
TEAL_BG = colors.HexColor("#e6f3f4")
PURPLE = colors.HexColor("#5b3ea8")
PURPLE_BG = colors.HexColor("#efeafb")
CODE_BG = colors.HexColor("#eef1f5")

ACCENTS = {"blue": BLUE, "teal": TEAL, "green": GREEN, "red": RED,
           "amber": AMBER, "purple": PURPLE, "ink": INK}
TINTS = {"blue": BLUE_BG, "teal": TEAL_BG, "green": GREEN_BG, "red": RED_BG,
         "amber": AMBER_BG, "purple": PURPLE_BG, "ink": BAND}

#: Panel kinds. Each is a (border, background, default label) triple — the
#: label is what makes a colour mean something to a reader who is skimming.
PANELS = {
    "key":   (BLUE, BLUE_BG, "REMEMBER THIS"),
    "trap":  (RED, RED_BG, "EXAM TRAP"),
    "tip":   (GREEN, GREEN_BG, "FAST PATH"),
    "watch": (AMBER, AMBER_BG, "EASY TO CONFUSE"),
    "note":  (TEAL, TEAL_BG, "WORTH KNOWING"),
    "you":   (PURPLE, PURPLE_BG, "YOUR LAST ATTEMPT"),
    "plain": (MUTED, BAND, None),
}

PAGE_W, PAGE_H = LETTER
LM = RM = 14 * mm
TM = 11 * mm
BM = 13 * mm
CONTENT_W = PAGE_W - LM - RM


# --------------------------------------------------------------------------
# Flowables
# --------------------------------------------------------------------------


class PageMark(Flowable):
    """Zero-height probe recording the page a section actually started on."""

    def __init__(self, label: str, sink: List[tuple]):
        super().__init__()
        self.label, self.sink = label, sink
        self.width = self.height = 0

    def draw(self) -> None:
        self.sink.append((self.label, self.canv.getPageNumber()))


class Rule(Flowable):
    def __init__(self, width: float, color=RULE, thickness: float = 0.6):
        super().__init__()
        self.width, self.color, self.thickness = width, color, thickness
        self.height = thickness

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


# --------------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------------


def styles() -> Dict[str, ParagraphStyle]:
    b = getSampleStyleSheet()
    mk = lambda n, **kw: ParagraphStyle(n, parent=b["Normal"], **kw)
    return {
        "cover":   mk("cover", fontName="Helvetica-Bold", fontSize=26, leading=29,
                      textColor=colors.white),
        "coversub": mk("coversub", fontSize=10, leading=14, textColor=colors.white),
        "ptitle":  mk("ptitle", fontName="Helvetica-Bold", fontSize=15, leading=17.5,
                      textColor=colors.white),
        "pkick":   mk("pkick", fontName="Helvetica-Bold", fontSize=7, leading=8.6,
                      textColor=colors.white),
        "pnum":    mk("pnum", fontName="Helvetica-Bold", fontSize=15, leading=17.5,
                      textColor=colors.white, alignment=TA_CENTER),
        "lede":    mk("lede", fontSize=8.6, leading=11.6, textColor=INK),
        "h":       mk("h", fontName="Helvetica-Bold", fontSize=8.0, leading=9.6,
                      textColor=INK, spaceBefore=5, spaceAfter=2.5),
        "body":    mk("body", fontSize=8.0, leading=10.5, textColor=INK, spaceAfter=3),
        "bul":     mk("bul", fontSize=8.0, leading=10.5, textColor=INK,
                      leftIndent=9, bulletIndent=1, spaceAfter=2),
        "cell":    mk("cell", fontSize=7.2, leading=9.1, textColor=INK),
        "cellh":   mk("cellh", fontName="Helvetica-Bold", fontSize=7.0, leading=8.8,
                      textColor=colors.white),
        "code":    mk("code", fontName="Courier", fontSize=7.0, leading=9.2, textColor=INK),
        "codeb":   mk("codeb", fontName="Courier-Bold", fontSize=7.0, leading=9.2,
                      textColor=INK),
        "panel":   mk("panel", fontSize=7.8, leading=10.2, textColor=INK),
        "panelh":  mk("panelh", fontName="Helvetica-Bold", fontSize=6.8, leading=8.4),
        "small":   mk("small", fontSize=7.0, leading=9.0, textColor=MUTED),
        "big":     mk("big", fontName="Helvetica-Bold", fontSize=15, leading=16.5,
                      textColor=INK, alignment=TA_CENTER),
        "biglbl":  mk("biglbl", fontSize=6.4, leading=8.0, textColor=MUTED,
                      alignment=TA_CENTER),
        "acmd":    mk("acmd", fontName="Courier-Bold", fontSize=7.1, leading=9.4,
                      textColor=INK),
        "adesc":   mk("adesc", fontSize=7.1, leading=9.4, textColor=MUTED),
    }


def hx(c) -> str:
    """ReportLab's mini-HTML wants #rrggbb; Color.hexval() yields 0xrrggbb."""
    return c.hexval().replace("0x", "#")


def esc(t: Any) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------
# Block renderers
# --------------------------------------------------------------------------


def panel(spec: Dict[str, Any], st, width: float = CONTENT_W) -> Table:
    border, bg, deflabel = PANELS[spec.get("kind", "key")]
    label = spec.get("label", deflabel)
    rows = []
    if label:
        rows.append([Paragraph(f'<font color="{hx(border)}">{esc(label)}</font>',
                               st["panelh"])])
    rows.append([Paragraph(spec["text"], st["panel"])])
    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def code_box(text: str, st, width: float = CONTENT_W) -> Table:
    lines = [Paragraph(esc(ln) or "&nbsp;", st["code"]) for ln in text.split("\n")]
    t = Table([[lines]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, MUTED),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def data_table(spec: Dict[str, Any], st, width: float = CONTENT_W,
               accent=TEAL) -> Table:
    head, rows = spec["head"], spec["rows"]
    n = len(head)
    ratios = spec.get("w")
    if ratios:
        w = [width * r / sum(ratios) for r in ratios]
    else:
        w = [width / n] * n
    data = [[Paragraph(h, st["cellh"]) for h in head]]
    for r in rows:
        data.append([Paragraph(c, st["cell"]) for c in r])
    t = Table(data, colWidths=w, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), spec.get("accent_color") or accent),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
        ("TOPPADDING", (0, 0), (-1, -1), 1.4 if spec.get("compact") else 2.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4 if spec.get("compact") else 2.8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(style))
    return t


def fact_strip(items: List[Tuple[str, str]], st, width: float = CONTENT_W,
               accent=BLUE) -> Table:
    cells = []
    for big, label in items:
        inner = Table([[Paragraph(f'<font color="{hx(accent)}">{big}</font>', st["big"])],
                       [Paragraph(label, st["biglbl"])]])
        inner.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (0, 0), 3), ("BOTTOMPADDING", (0, 0), (0, 0), 0),
            ("TOPPADDING", (0, 1), (0, 1), 1), ("BOTTOMPADDING", (0, 1), (0, 1), 4),
        ]))
        cells.append(inner)
    t = Table([cells], colWidths=[width / len(cells)] * len(cells))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAND),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def appendix_table(spec: Dict[str, Any], st, width: float = CONTENT_W) -> Table:
    """Command / meaning pairs — a tighter shape than a generic table."""
    data = []
    for cmd, desc in spec["rows"]:
        data.append([Paragraph(esc(cmd), st["acmd"]), Paragraph(desc, st["adesc"])])
    t = Table(data, colWidths=[width * 0.52, width * 0.48])
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 6), ("LEFTPADDING", (1, 0), (1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, RULE),
    ]
    for i in range(len(data)):
        if i % 2 == 1:
            style.append(("BACKGROUND", (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(style))
    return t


def render_blocks(blocks: List[tuple], st, width: float = CONTENT_W) -> List[Any]:
    out: List[Any] = []
    for kind, payload in blocks:
        if kind == "p":
            out.append(Paragraph(payload, st["body"]))
        elif kind == "lede":
            out.append(panel({"kind": "plain", "text": payload, "label": None}, st, width))
            out.append(Spacer(1, 5))
        elif kind == "h":
            out.append(Paragraph(payload, st["h"]))
        elif kind == "bul":
            for it in payload:
                out.append(Paragraph(it, st["bul"], bulletText="•"))
            out.append(Spacer(1, 2))
        elif kind == "num":
            for i, it in enumerate(payload, 1):
                out.append(Paragraph(it, st["bul"], bulletText=f"{i}."))
            out.append(Spacer(1, 2))
        elif kind == "table":
            out.append(data_table(payload, st, width))
            out.append(Spacer(1, 5))
        elif kind == "cmds":
            out.append(appendix_table(payload, st, width))
            out.append(Spacer(1, 5))
        elif kind == "panel":
            out.append(panel(payload, st, width))
            out.append(Spacer(1, 5))
        elif kind == "code":
            out.append(code_box(payload, st, width))
            out.append(Spacer(1, 5))
        elif kind == "facts":
            out.append(fact_strip(payload, st, width))
            out.append(Spacer(1, 5))
        elif kind == "rule":
            out.append(Spacer(1, 2))
            out.append(Rule(width))
            out.append(Spacer(1, 4))
        elif kind == "gap":
            out.append(Spacer(1, payload))
        elif kind == "cols":
            cols = payload["cols"]
            ratio = payload.get("ratio", (1,) * len(cols))
            gut = payload.get("gutter", 8)
            usable = width - gut * (len(cols) - 1)
            widths = [usable * r / sum(ratio) for r in ratio]
            cells, cw = [], []
            for i, col in enumerate(cols):
                if i:
                    cells.append("")
                    cw.append(gut)
                cells.append(render_blocks(col, st, widths[i]))
                cw.append(widths[i])
            t = Table([cells], colWidths=cw)
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            out.append(t)
        else:
            raise ValueError(f"unknown block kind: {kind}")
    return out


# --------------------------------------------------------------------------
# Page assembly
# --------------------------------------------------------------------------


def page_header(spec: Dict[str, Any], st) -> List[Any]:
    accent = ACCENTS[spec.get("accent", "blue")]
    label = spec.get("label", "")
    num = spec.get("num")
    left = [Paragraph(esc(label).upper(), st["pkick"]),
            Paragraph(esc(spec["title"]), st["ptitle"])]
    cells = [left]
    widths = [CONTENT_W - 13 * mm]
    if num:
        cells.append(Paragraph(str(num), st["pnum"]))
        widths.append(13 * mm)
    else:
        widths = [CONTENT_W]
    t = Table([cells], colWidths=widths)
    style = [
        ("BACKGROUND", (0, 0), (-1, -1), accent),
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ("VALIGN", (-1, 0), (-1, 0), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (0, 0), (0, 0), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
    ]
    if num:
        style += [("BACKGROUND", (-1, 0), (-1, 0), colors.Color(0, 0, 0, 0.14)),
                  ("LEFTPADDING", (-1, 0), (-1, 0), 0),
                  ("RIGHTPADDING", (-1, 0), (-1, 0), 0)]
    t.setStyle(TableStyle(style))
    return [t, Spacer(1, 6)]


def render_page(spec: Dict[str, Any], st) -> List[Any]:
    return page_header(spec, st) + render_blocks(spec["blocks"], st)


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.line(LM, 9.5 * mm, PAGE_W - RM, 9.5 * mm)
    canvas.setFont("Helvetica", 6.6)
    canvas.setFillColor(FAINT)
    canvas.drawString(LM, 6.4 * mm,
                      "GCP ACE exam-eve recap — simulator study material. "
                      "Not affiliated with or endorsed by Google LLC.")
    canvas.drawRightString(PAGE_W - RM, 6.4 * mm, f"{canvas.getPageNumber()}")
    canvas.restoreState()


def build(out_path: Path, candidate: str) -> Tuple[Path, List[tuple]]:
    st = styles()
    marks: List[tuple] = []
    story: List[Any] = []

    for i, spec in enumerate(PAGES):
        if i:
            story.append(PageBreak())
        story.append(PageMark(spec.get("id", spec["title"]), marks))
        story += render_page(spec, st)

    doc = BaseDocTemplate(
        str(out_path), pagesize=LETTER,
        leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
        title=TITLE, author="GCP ACE Exam Simulator", subject=SUBTITLE,
    )
    frame = Frame(LM, BM, CONTENT_W, PAGE_H - TM - BM, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
    doc.build(story)
    return out_path, marks


def verify(marks: List[tuple]) -> List[str]:
    """One section per page is the whole layout contract — check it held."""
    problems = []
    for i, (label, page) in enumerate(marks):
        want = i + 1
        if page != want:
            problems.append(f"'{label}' landed on p{page}, expected p{want} "
                            f"(an earlier section overflowed its page)")
    return problems


def measure() -> None:
    """Report how full each page is, so overflow is found before it happens."""
    st = styles()
    avail = PAGE_H - TM - BM
    print(f"{'page':>4}  {'fill':>6}  section")
    for i, spec in enumerate(PAGES, 1):
        used = 0.0
        for f in render_page(spec, st):
            used += f.wrap(CONTENT_W, avail)[1]
            used += f.getSpaceBefore() + f.getSpaceAfter()
        pct = used / avail * 100
        flag = "  <-- OVERFLOW" if pct > 100 else ("  <-- tight" if pct > 97 else "")
        print(f"{i:>4}  {pct:5.1f}%  {spec['title'][:52]}{flag}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", default="Candidate")
    ap.add_argument("--measure", action="store_true",
                    help="report per-page fill without writing a PDF")
    ap.add_argument("--open", action="store_true")
    args = ap.parse_args()

    if args.measure:
        measure()
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = ensure_writable_dir(reports_dir()) / f"ACE-exam-eve-recap-{stamp}.pdf"
    path, marks = build(out, args.candidate)

    theory = sum(1 for p in PAGES if p.get("part", "theory") == "theory")
    print(f"{path}")
    print(f"  sections: {len(PAGES)}   theory pages: {theory}   "
          f"appendix pages: {len(PAGES) - theory}")
    problems = verify(marks)
    for p in problems:
        print(f"  LAYOUT: {p}")
    if not problems:
        print("  layout: every section occupies exactly one page")

    if args.open:
        import webbrowser
        webbrowser.open(path.resolve().as_uri())
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
