"""The PDF report for one attempt: a score summary, then a review of each item.

This is the report the app produces on every submission, and the one
``scripts/retrospective.py`` rebuilds from history.

By default it reviews only the items that were **missed** or **flagged**, two
pages each, every item starting on a fresh page. A flagged item answered
correctly is included on purpose: a guess that lands is not knowledge. With
``all_items`` every item on the paper is reviewed, correct ones in green.

    page 1              summary: score, sections, where to study next, timing
    pages 2N, 2N+1      one item: the question with every option explained,
                        then the theory, the command and links to the theory
                        site and the course video
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from . import study_links
from .exam_engine import load_bank
from .models import DOMAIN_SHORT, DOMAINS, PASS_THRESHOLD, Attempt, Question
from .paths import ensure_writable_dir, history_path, reports_dir

# Authored notes are personal: they describe one person's attempts, so the file is gitignored
# and lives in scripts/, which is on sys.path when the app or the script runs.
# Without it, every item falls back to what the bank already says (see bank_notes).
try:
    from retro_content import ATTEMPTS, CONTENT
except ImportError:
    ATTEMPTS, CONTENT = {}, {}

EMPTY_ATTEMPT_NOTES = {"margin": "", "themes": [], "timing": ""}

# --------------------------------------------------------------------------
# Palette — extends the score-report palette with semantic panel colours.
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
CODE_BG = colors.HexColor("#eef1f5")

PAGE_W, PAGE_H = LETTER
LM = RM = 16 * mm
TM = 15 * mm
BM = 16 * mm
CONTENT_W = PAGE_W - LM - RM


# --------------------------------------------------------------------------
# Flowables
# --------------------------------------------------------------------------


class PageMark(Flowable):
    """Zero-height probe that records which page a section actually started on.

    The two-pages-per-item contract is a promise about the printed artefact,
    so it is verified against the real pagination rather than estimated.
    """

    def __init__(self, label: str, sink: List[tuple]):
        super().__init__()
        self.label, self.sink = label, sink
        self.width = self.height = 0

    def draw(self) -> None:
        self.sink.append((self.label, self.canv.getPageNumber()))


class Band(Flowable):
    """Solid colour bar bleeding the full content width — the item header."""

    def __init__(self, width: float, height: float, color, radius: float = 1.5):
        super().__init__()
        self.width, self.height, self.color, self.radius = width, height, color, radius

    def draw(self) -> None:
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height, self.radius, stroke=0, fill=1)


class ScoreBar(Flowable):
    """Proportion bar with the pass threshold marked."""

    def __init__(self, pct: float, width: float, height: float = 8 * mm):
        super().__init__()
        self.pct = max(0.0, min(1.0, pct))
        self.width, self.height = width, height

    def draw(self) -> None:
        c = self.canv
        c.setFillColor(BAND)
        c.setStrokeColor(RULE)
        c.rect(0, 0, self.width, self.height, stroke=1, fill=1)
        c.setFillColor(GREEN if self.pct >= PASS_THRESHOLD else RED)
        c.rect(0, 0, self.width * self.pct, self.height, stroke=0, fill=1)
        x = self.width * PASS_THRESHOLD
        c.setStrokeColor(INK)
        c.setLineWidth(1.2)
        c.setDash(2, 2)
        c.line(x, 0, x, self.height)
        c.setDash()
        # Label sits inside the bar, just right of the threshold line — above it
        # would collide with the stat strip on a page this tightly packed.
        c.setFont("Helvetica-Bold", 6.8)
        c.setFillColor(INK)
        c.drawString(x + 1.6 * mm, self.height / 2 - 2.4,
                     f"pass mark {int(PASS_THRESHOLD * 100)}%")


# --------------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------------


def styles() -> Dict[str, ParagraphStyle]:
    b = getSampleStyleSheet()
    mk = lambda n, **kw: ParagraphStyle(n, parent=b["Normal"], **kw)
    return {
        "title": mk("title", fontName="Helvetica-Bold", fontSize=21, leading=24,
                    textColor=INK, spaceAfter=1),
        "sub": mk("sub", fontSize=9.5, leading=13, textColor=MUTED, spaceAfter=2),
        "h1": mk("h1", fontName="Helvetica-Bold", fontSize=12, leading=15,
                 textColor=INK, spaceBefore=9, spaceAfter=4),
        "sect": mk("sect", fontName="Helvetica-Bold", fontSize=7.4, leading=9,
                   textColor=FAINT, spaceBefore=7, spaceAfter=3),
        "qtitle": mk("qtitle", fontName="Helvetica-Bold", fontSize=13.5, leading=16,
                     textColor=INK, spaceAfter=1),
        "body": mk("body", fontSize=8.7, leading=12.0, textColor=INK, spaceAfter=4),
        "bodyc": mk("bodyc", fontSize=8.7, leading=12.0, textColor=INK),
        "stem": mk("stem", fontSize=9.4, leading=13.2, textColor=INK),
        "small": mk("small", fontSize=7.6, leading=10.2, textColor=MUTED),
        "opt": mk("opt", fontName="Helvetica-Bold", fontSize=8.6, leading=11.2, textColor=INK),
        "optwhy": mk("optwhy", fontSize=7.6, leading=10.0, textColor=MUTED, spaceBefore=1.5),
        "cell": mk("cell", fontSize=7.5, leading=9.8, textColor=INK),
        "cellh": mk("cellh", fontName="Helvetica-Bold", fontSize=7.4, leading=9.6,
                    textColor=colors.white),
        "code": mk("code", fontName="Courier", fontSize=7.3, leading=9.8, textColor=INK),
        "panel": mk("panel", fontSize=8.5, leading=11.6, textColor=INK),
        "panelh": mk("panelh", fontName="Helvetica-Bold", fontSize=7.6, leading=9.6),
        "badge": mk("badge", fontName="Helvetica-Bold", fontSize=8.2, leading=10,
                    textColor=colors.white),
        "hdr": mk("hdr", fontName="Helvetica-Bold", fontSize=8.2, leading=10,
                  textColor=colors.white),
        "letter": mk("letter", fontName="Helvetica-Bold", fontSize=11, leading=13,
                     textColor=colors.white, alignment=TA_CENTER),
        "stat": mk("stat", fontName="Helvetica-Bold", fontSize=17, leading=19,
                   textColor=INK, alignment=TA_CENTER),
        "statl": mk("statl", fontSize=6.8, leading=8.6, textColor=MUTED, alignment=TA_CENTER),
    }


def hx(c) -> str:
    """ReportLab's mini-HTML wants #rrggbb; Color.hexval() yields 0xrrggbb."""
    return c.hexval().replace("0x", "#")


def esc(t: Any) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def code(t: Any) -> str:
    """Escape bank prose, and render its markdown `code` spans as monospace."""
    return re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', esc(t))


def link(url: str, text: str) -> str:
    return f'<font color="#1a56b0"><link href="{esc(url)}">{esc(text)}</link></font>'


def rich(t: Any) -> str:
    """Content markup is authored with ReportLab's mini-HTML, so pass it through."""
    return str(t)


def _norm(t: str) -> str:
    """Comparison form: lowercase alphanumerics, minus a leading 'Correct.'."""
    t = re.sub(r"^correct[.:]?\s*", "", str(t).strip().lower())
    return re.sub(r"[^a-z0-9 ]", "", t).strip()


def restates(summary: str, option_rationale: str) -> bool:
    """True when the bank's summary just repeats the correct option's rationale.

    Many bank items do, and printing both puts the same sentence twice on one
    page directly under itself.
    """
    a, b = _norm(summary), _norm(option_rationale)
    return bool(a) and (a == b or a in b or b in a)


# --------------------------------------------------------------------------
# Panel helper
# --------------------------------------------------------------------------


def panel(body_html: str, st, *, bg, border, label: Optional[str] = None,
          label_color=None, width: float = CONTENT_W, pad: float = 6) -> Table:
    """A tinted, left-accented info box — the report's main emphasis device."""
    rows = []
    if label:
        rows.append([Paragraph(
            f'<font color="{hx(label_color or border)}">{label}</font>',
            st["panelh"])])
    rows.append([Paragraph(body_html, st["panel"])])
    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, border),
        ("LEFTPADDING", (0, 0), (-1, -1), pad + 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), 4 if label else pad - 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 1),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def code_box(text: str, st, width: float = CONTENT_W) -> Table:
    # Keep runs of spaces, so ASCII diagrams and aligned columns stay aligned.
    lines = [Paragraph(re.sub(r"  +", lambda m: "&nbsp;" * len(m.group(0)), esc(ln)) or "&nbsp;",
                       st["code"]) for ln in text.split("\n")]
    t = Table([[lines]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, MUTED),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def data_table(spec: Dict[str, Any], st, width: float = CONTENT_W) -> Table:
    head = spec["head"]
    rows = spec["rows"]
    n = len(head)
    if n == 2:
        w = [width * 0.34, width * 0.66]
    elif n == 3:
        w = [width * 0.28, width * 0.34, width * 0.38]
    else:
        w = [width * 0.24, width * 0.22, width * 0.27, width * 0.27]
    data = [[Paragraph(rich(h), st["cellh"]) for h in head]]
    for r in rows:
        data.append([Paragraph(rich(c), st["cell"]) for c in r])
    t = Table(data, colWidths=w, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(style))
    return t


# --------------------------------------------------------------------------
# Theory excerpts: the course's own section, fitted to the space left on page 2
# --------------------------------------------------------------------------

PAGE_BODY_H = PAGE_H - TM - BM


_MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def md_inline(t: str) -> str:
    """The theory's inline Markdown, as ReportLab mini-HTML."""
    # Links are cut out before escaping, so link() escapes their text and URL exactly once.
    parts, last = [], 0
    for m in _MD_LINK.finditer(t):
        parts += [esc(t[last:m.start()]), link(m.group(2), m.group(1))]
        last = m.end()
    t = "".join(parts) + esc(t[last:])
    t = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return re.sub(r"(?<![*\w])\*([^*\s][^*]*)\*(?!\w)", r"<i>\1</i>", t)


def md_blocks(text: str) -> List[tuple[str, Any]]:
    """Split a section's Markdown into paragraphs, lists, quotes, sub-headings and tables."""
    blocks: List[tuple[str, Any]] = []
    para: List[str] = []
    table: List[List[str]] = []

    def flush() -> None:
        if para:
            blocks.append(("p", " ".join(para)))
            para.clear()
        if table:
            head, *rows = table
            blocks.append(("table", {"head": head, "rows": rows}))
            table.clear()

    fence: Optional[List[str]] = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            if fence is None:
                flush()
                fence = []
            else:
                blocks.append(("code", "\n".join(fence)))
                fence = None
            continue
        if fence is not None:
            fence.append(raw.rstrip())
            continue
        if raw.startswith("   ") and line and blocks and blocks[-1][0] == "li" and not para and not table:
            blocks[-1] = ("li", blocks[-1][1] + " " + line)  # a list item's continuation line
            continue
        if line.startswith("|"):
            if para:
                blocks.append(("p", " ".join(para)))
                para.clear()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                table.append(cells)
            continue
        if table:
            flush()
        if not line:
            flush()
        elif line.startswith("#"):
            flush()
            blocks.append(("h", line.lstrip("#").strip()))
        elif line.startswith(">"):
            flush()
            body = line.lstrip("> ").strip()
            if blocks and blocks[-1][0] == "quote":
                blocks[-1] = ("quote", blocks[-1][1] + " " + body)
            elif body:
                blocks.append(("quote", body))
        elif re.match(r"^([-*]|\d+\.) ", line):
            flush()
            blocks.append(("li", re.sub(r"^([-*]|\d+\.) ", "", line)))
        else:
            para.append(line)
    flush()
    return blocks


def _height(flowables: List[Any]) -> float:
    total = 0.0
    for f in flowables:
        _, h = f.wrap(CONTENT_W, PAGE_BODY_H)
        total += h + f.getSpaceBefore() + f.getSpaceAfter()
    return total


def theory_excerpt(sec: study_links.Section, st, budget: float) -> List[Any]:
    """As much of the section as fits in ``budget`` points, whole blocks only."""
    head = [Paragraph(f"FROM THE COURSE: §{esc(sec.key)} {esc(sec.title.upper())}", st["sect"])]
    out: List[Any] = list(head)
    used = _height(out)
    for kind, payload in md_blocks(sec.text):
        if kind == "table":
            if not 2 <= len(payload["head"]) <= 4:
                continue
            rows = payload["rows"]
            cand: List[Any] = []
            for n in range(len(rows), 0, -1):
                spec = {"head": [md_inline(h) for h in payload["head"]],
                        "rows": [[md_inline(c) for c in r[:len(payload["head"])]] for r in rows[:n]]}
                cand = [Spacer(1, 2), data_table(spec, st), Spacer(1, 5)]
                if used + _height(cand) <= budget:
                    break
                cand = []
            if not cand:
                continue  # a table that won't fit is skipped; later prose may still fit
        elif kind == "h":
            cand = [Paragraph(f"<b>{md_inline(payload)}</b>", st["bodyc"])]
        elif kind == "quote":
            cand = [panel(md_inline(payload), st, bg=BAND, border=MUTED, pad=5), Spacer(1, 4)]
        elif kind == "code":
            if max(len(ln) for ln in payload.splitlines() or [""]) > 110:
                continue
            cand = [code_box(payload, st), Spacer(1, 5)]
        elif kind == "li":
            cand = [Paragraph(f"•&nbsp; {md_inline(payload)}", st["body"])]
        else:
            cand = [Paragraph(md_inline(payload), st["body"])]
        if not cand or used + _height(cand) > budget:
            break
        out += cand
        used += _height(cand)
    return out if len(out) > len(head) else []


# --------------------------------------------------------------------------
# One item — page 1: the question as it was answered
# --------------------------------------------------------------------------


def item_kind(rec: Dict[str, Any]) -> str:
    """'missed', 'flagged' (correct but flagged) or 'correct'."""
    if rec["selected"] != rec["correct_answer"]:
        return "missed"
    return "flagged" if rec["flagged"] else "correct"


def item_accent(rec: Dict[str, Any]):
    return {"missed": (RED, RED_BG), "flagged": (AMBER, AMBER_BG),
            "correct": (GREEN, GREEN_BG)}[item_kind(rec)]


def item_page_one(idx: int, total: int, rec: Dict[str, Any], q, c: Dict[str, Any],
                  st) -> List[Any]:
    kind = item_kind(rec)
    missed = kind == "missed"
    accent, accent_bg = item_accent(rec)
    status = {"missed": "MISSED", "flagged": "FLAGGED — ANSWERED CORRECTLY",
              "correct": "ANSWERED CORRECTLY"}[kind]

    out: List[Any] = []

    # Header band: item counter left, status badge right.
    hdr = Table(
        [[Paragraph(f"ITEM {idx} OF {total}", st["hdr"]),
          Paragraph(f'<para align="right">{status}</para>', st["badge"])]],
        colWidths=[CONTENT_W * 0.35, CONTENT_W * 0.65], rowHeights=[7.6 * mm])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), accent),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (-1, 0), (-1, 0), 8),
    ]))
    out.append(hdr)
    out.append(Spacer(1, 5))

    out.append(Paragraph(esc(q.title), st["qtitle"]))

    flag = "flagged" if rec["flagged"] else "not flagged"
    meta = (f'<font color="#1a56b0"><b>{esc(DOMAIN_SHORT[q.domain])}</b></font>'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;{esc(q.subtopic)}'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;question {rec["_n"]} on the paper'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;{rec["seconds_spent"]:.0f}s spent'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;{flag}'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;<font face="Courier">{esc(q.id)}</font>')
    out.append(Paragraph(meta, st["small"]))
    out.append(Spacer(1, 7))

    out.append(Paragraph("THE QUESTION", st["sect"]))
    out.append(panel(code(q.question), st, bg=BAND, border=MUTED, pad=7))
    out.append(Spacer(1, 7))

    out.append(Paragraph("THE OPTIONS", st["sect"]))
    rows, style = [], [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i, k in enumerate("ABCD"):
        is_right = k == rec["correct_answer"]
        is_mine = k == rec["selected"]
        if is_right:
            box, bg, tag = GREEN, GREEN_BG, "CORRECT ANSWER"
        elif is_mine:
            box, bg, tag = RED, RED_BG, "YOUR ANSWER"
        else:
            box, bg, tag = FAINT, colors.white, ""
        if is_right and is_mine:
            tag = "CORRECT — AND YOUR ANSWER"

        letter = Table([[Paragraph(k, st["letter"])]],
                       colWidths=[7.2 * mm], rowHeights=[7.2 * mm])
        letter.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), box),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        head = code(q.options[k])
        if tag:
            head += (f'&nbsp;&nbsp;<font size="6.4" color="{hx(box)}">'
                     f'<b>{tag}</b></font>')
        body = [Paragraph(head, st["opt"]),
                Paragraph(code(q.explanation.option_breakdown[k]), st["optwhy"])]

        inner = Table([[letter, body]], colWidths=[9.6 * mm, CONTENT_W - 9.6 * mm])
        inner.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LINEBEFORE", (0, 0), (0, -1), 2.2, box),
            ("LEFTPADDING", (0, 0), (0, 0), 3.4), ("RIGHTPADDING", (0, 0), (0, 0), 0),
            ("LEFTPADDING", (1, 0), (1, 0), 6), ("RIGHTPADDING", (1, 0), (1, 0), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 4.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ]))
        rows.append([inner])
    opts = Table(rows, colWidths=[CONTENT_W])
    opts.setStyle(TableStyle(style))
    out.append(opts)
    out.append(Spacer(1, 7))

    if missed and not rec["selected"]:
        verdict = (f'<b>You left it unanswered</b> &nbsp;·&nbsp; '
                   f'the correct answer is <b>{rec["correct_answer"]}</b>')
    elif missed:
        verdict = (f'<b>You answered {rec["selected"]}</b> &nbsp;·&nbsp; '
                   f'the correct answer is <b>{rec["correct_answer"]}</b>')
    elif kind == "flagged":
        verdict = (f'<b>You answered {rec["selected"]} — correct</b> &nbsp;·&nbsp; '
                   f'but you flagged it, so it is reviewed here as a guess')
    else:
        verdict = (f'<b>You answered {rec["selected"]} — correct</b> &nbsp;·&nbsp; '
                   f'reviewed to confirm the reasoning, not only the letter')
    out.append(panel(verdict, st, bg=accent_bg, border=accent, pad=6))
    out.append(Spacer(1, 7))

    out.append(panel(
        f'<b>{"What decided it" if kind == "correct" else "What went wrong"}:</b> '
        f'{rich(c["root_cause"])}<br/>'
        f'<b>Reading habit to apply:</b> {rich(c["reflex"])}',
        st, bg=accent_bg, border=accent,
        label="WHAT DECIDED IT" if kind == "correct" else "ROOT CAUSE", pad=6))
    out.append(Spacer(1, 7))

    out.append(Paragraph("WHY THE CORRECT ANSWER IS RIGHT", st["sect"]))
    out.append(Paragraph(rich(c["why_right"]), st["body"]))
    if not restates(q.explanation.summary,
                    q.explanation.option_breakdown[rec["correct_answer"]]):
        out.append(Paragraph(code(q.explanation.summary), st["body"]))
    return out


# --------------------------------------------------------------------------
# One item — page 2: the theory
# --------------------------------------------------------------------------


def item_page_two(idx: int, total: int, rec: Dict[str, Any], q, c: Dict[str, Any],
                  st) -> List[Any]:
    accent, _ = item_accent(rec)
    out: List[Any] = []

    strip = Table(
        [[Paragraph(f'<font color="{hx(accent)}"><b>ITEM {idx} OF {total}</b></font>'
                    f'&nbsp;&nbsp;·&nbsp;&nbsp;{esc(q.title)}', st["small"]),
          Paragraph(f'<para align="right">THEORY &amp; REMEDIATION</para>', st["small"])]],
        colWidths=[CONTENT_W * 0.72, CONTENT_W * 0.28])
    strip.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1.0, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    out.append(strip)
    out.append(Spacer(1, 6))

    out.append(Paragraph("THE THEORY", st["sect"]))
    out.append(Paragraph(rich(c["theory_title"]), st["h1"]))

    for kind, payload in c["theory"]:
        if kind == "p":
            out.append(Paragraph(rich(payload), st["body"]))
        elif kind == "table":
            out.append(Spacer(1, 2))
            out.append(data_table(payload, st))
            out.append(Spacer(1, 6))
        elif kind == "code":
            out.append(Spacer(1, 1))
            out.append(code_box(payload, st))
            out.append(Spacer(1, 5))
        elif kind == "calc":
            out.append(Spacer(1, 1))
            out.append(code_box(payload, st))
            out.append(Spacer(1, 5))

    tail: List[Any] = []
    out, tail = tail, out  # collect the rest of the page, then fit the excerpt above it
    cmd = (q.explanation.gcloud_command or "").strip()
    if cmd and not any(k == "code" for k, _ in c["theory"]):
        out.append(Paragraph("COMMAND", st["sect"]))
        out.append(code_box(cmd, st))
        out.append(Spacer(1, 5))

    out.append(Spacer(1, 2))
    out.append(panel(rich(c["spot"]), st, bg=AMBER_BG, border=AMBER,
                     label="SPOT IT NEXT TIME", pad=6))

    if q.explanation.doc_ref:
        out.append(Spacer(1, 5))
        out.append(Paragraph(
            f'Reference &nbsp;{link(q.explanation.doc_ref, q.explanation.doc_ref)}', st["small"]))

    lines = study_lines(study_links.sections_for(q))
    if lines:
        out.append(Spacer(1, 6))
        out.append(panel("<br/>".join(lines), st, bg=BLUE_BG, border=BLUE,
                         label="STUDY NEXT: THE THEORY, AND THE VIDEO TO REWATCH", pad=6))

    head, rest = tail, out
    sections = study_links.sections_for(q)
    excerpt: List[Any] = []
    if sections and c is not CONTENT.get(q.id):
        # 24pt of slack: the measured heights and real pagination differ by a few points.
        budget = PAGE_BODY_H - _height(head) - _height(rest) - 24
        excerpt = theory_excerpt(sections[0], st, budget)
    return head + excerpt + rest


def study_lines(sections: List[study_links.Section], counts: Optional[Dict[str, int]] = None) -> List[str]:
    """One line per theory section: its page on the site, and its chapter in the video."""
    lines = []
    for sec in sections:
        line = f'<b>§{esc(sec.key)}</b> {link(sec.url, sec.title)}'
        if sec.video_url:
            line += f' &nbsp;·&nbsp; video {link(sec.video_url, sec.video_clock)}'
        if counts:
            n = counts[sec.key]
            line += f' &nbsp;·&nbsp; {n} item{"s" if n != 1 else ""}'
        lines.append(line)
    return lines


# --------------------------------------------------------------------------
# Page 1 — summary, themes and timing
# --------------------------------------------------------------------------

#: Theme colours by name. The themes themselves are written per attempt, in
#: ``retro_content.ATTEMPTS``, because they describe that attempt's misses.
THEME_COLORS = {
    "red": (RED, RED_BG),
    "amber": (AMBER, AMBER_BG),
    "blue": (BLUE, BLUE_BG),
    "teal": (TEAL, TEAL_BG),
}


def summary_page(att: Dict[str, Any], items: List[Dict[str, Any]], notes: Dict[str, Any],
                 candidate: str, st, all_items: bool = False) -> List[Any]:
    out: List[Any] = []
    answers = att["answers"]
    total_q = att["question_count"]
    correct = att["correct_count"]
    pct = correct / total_q if total_q else 0.0
    missed = [a for a in answers if a["selected"] != a["correct_answer"]]
    flagged_ok = [a for a in answers if a["flagged"] and a["selected"] == a["correct_answer"]]

    out.append(Paragraph("Score Report and Review", st["title"]))
    when = datetime.fromisoformat(att["finished_at"]).strftime("%d %B %Y")
    out.append(Paragraph(
        f'{esc(candidate)} &nbsp;·&nbsp; Associate Cloud Engineer, {esc(att["mode"])} mode '
        f'&nbsp;·&nbsp; {when} &nbsp;·&nbsp; '
        f'attempt <font face="Courier">{esc(att["attempt_id"])}</font>', st["sub"]))
    out.append(Spacer(1, 3))

    # -- score strip -------------------------------------------------------
    mins = int(att["duration_seconds"] // 60)
    cells = [
        (f"{correct}/{total_q}", "SCORE"),
        (f"{pct*100:.0f}%", "PERCENT"),
        ("PASS" if pct >= PASS_THRESHOLD else "FAIL", "VERDICT"),
        (str(len(missed)), "MISSED"),
        (str(len(flagged_ok)), "FLAGGED, CORRECT"),
        (f"{mins}m", "TIME USED"),
    ]
    row = [[Paragraph(v, st["stat"]) for v, _ in cells],
           [Paragraph(l, st["statl"]) for _, l in cells]]
    t = Table(row, colWidths=[CONTENT_W / 6.0] * 6)
    vcol = GREEN if pct >= PASS_THRESHOLD else RED
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAND),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("LINEAFTER", (0, 0), (-2, -1), 0.5, RULE),
        ("TEXTCOLOR", (2, 0), (2, 0), vcol),
        ("TEXTCOLOR", (3, 0), (3, 0), RED),
        ("TEXTCOLOR", (4, 0), (4, 0), AMBER),
        ("TOPPADDING", (0, 0), (-1, 0), 5), ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
        ("TOPPADDING", (0, 1), (-1, 1), 1), ("BOTTOMPADDING", (0, 1), (-1, 1), 5),
    ]))
    out.append(t)
    out.append(Spacer(1, 6))
    out.append(ScoreBar(pct, CONTENT_W))
    out.append(Spacer(1, 6))

    # The pass line is a fraction of the paper, so the mark needed is rounded up.
    cut = math.ceil(PASS_THRESHOLD * total_q - 1e-9)
    margin = correct - cut
    if margin == 0:
        lede = (f'You scored <b>exactly the {int(PASS_THRESHOLD*100)}% threshold</b> — '
                f'{correct} of {total_q}, with no mark to spare.')
    elif margin > 0:
        lede = (f'You passed with <b>{margin} mark{"s" if margin != 1 else ""} to spare</b> '
                f'over the {cut}-of-{total_q} line.')
    else:
        lede = (f'You finished <b>{abs(margin)} mark{"s" if margin != -1 else ""} below</b> '
                f'the {cut}-of-{total_q} line.')
    out.append(panel(f'{lede} {rich(notes["margin"])}', st, bg=BLUE_BG, border=BLUE,
                     label="WHERE THE MARGIN ACTUALLY SITS", pad=7))
    out.append(Spacer(1, 6))

    # -- section breakdown -------------------------------------------------
    out.append(Paragraph("BY EXAM-GUIDE SECTION", st["sect"]))
    head = ["Section", "Asked", "Correct", "Score", "In this report"]
    rows = []
    for d in DOMAINS:
        ds = [a for a in answers if a["domain"] == d]
        if not ds:
            continue
        ok = sum(1 for a in ds if a["selected"] == a["correct_answer"])
        p = ok / len(ds)
        col = GREEN if p >= PASS_THRESHOLD else RED
        here = sum(1 for a in ds
                   if all_items or a["flagged"] or a["selected"] != a["correct_answer"])
        rows.append([
            f'<b>{esc(DOMAIN_SHORT[d])}</b>',
            str(len(ds)), str(ok),
            f'<font color="{hx(col)}"><b>{p*100:.0f}%</b></font>',
            f'{here} item{"s" if here != 1 else ""}',
        ])
    data = [[Paragraph(h, st["cellh"]) for h in head]]
    for r in rows:
        data.append([Paragraph(x, st["cell"]) for x in r])
    dt = Table(data, colWidths=[CONTENT_W * 0.30, CONTENT_W * 0.13, CONTENT_W * 0.15,
                                CONTENT_W * 0.17, CONTENT_W * 0.25])
    sty = [("BACKGROUND", (0, 0), (-1, 0), TEAL),
           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("ALIGN", (1, 0), (-1, -1), "CENTER"),
           ("BOX", (0, 0), (-1, -1), 0.5, RULE),
           ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
           ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
           ("LEFTPADDING", (0, 0), (-1, -1), 5)]
    for i in range(1, len(data)):
        if i % 2 == 0:
            sty.append(("BACKGROUND", (0, i), (-1, i), BAND))
    dt.setStyle(TableStyle(sty))
    out.append(dt)
    out.append(Spacer(1, 6))

    # -- themes ------------------------------------------------------------
    if notes["themes"]:
        out.append(Paragraph("WHAT THE MISSES HAVE IN COMMON", st["sect"]))
    for rank, th in enumerate(notes["themes"], 1):
        color, bg = THEME_COLORS[th["color"]]
        num = Table([[Paragraph(str(rank), st["letter"])]],
                    colWidths=[6.6 * mm], rowHeights=[6.6 * mm])
        num.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        nums = sorted(n for n in (items_page_index(items, i) for i in th["ids"])
                      if n is not None)
        pages = ", ".join(f"p{n}" for n in nums)
        body = [
            Paragraph(f'<font color="{hx(color)}"><b>{rich(th["name"])}</b>'
                      f'</font>', st["opt"]),
            Paragraph(rich(th["text"]), st["optwhy"]),
        ]
        if pages:
            body.append(Paragraph(f'<b>Items:</b> {pages}', st["optwhy"]))
        blk = Table([[num, body]], colWidths=[9 * mm, CONTENT_W - 9 * mm])
        blk.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LINEBEFORE", (0, 0), (0, -1), 2.2, color),
            ("LEFTPADDING", (0, 0), (0, 0), 3.4), ("RIGHTPADDING", (0, 0), (0, 0), 0),
            ("LEFTPADDING", (1, 0), (1, 0), 6), ("RIGHTPADDING", (1, 0), (1, 0), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 3.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
        ]))
        out.append(blk)
        out.append(Spacer(1, 3))

    # -- where to study next (when no authored themes) -----------------------
    weak = [it["q"] for it in items if it["rec"]["flagged"]
            or it["rec"]["selected"] != it["rec"]["correct_answer"]]
    if weak and not notes["themes"]:
        ranked = study_links.rank_sections(weak)[:6]
        lines = study_lines([s for s, _ in ranked], {s.key: n for s, n in ranked})
        lines.append(f'Whole course: {link(study_links.video_url(), study_links.video_title())}')
        out.append(Paragraph("WHERE TO STUDY NEXT", st["sect"]))
        out.append(panel("<br/>".join(lines), st, bg=BLUE_BG, border=BLUE,
                         label="THE SECTIONS BEHIND YOUR MISSES AND FLAGS, MOST FIRST", pad=6))
        out.append(Spacer(1, 3))

    # -- timing ------------------------------------------------------------
    fast = [a for a in missed if a["seconds_spent"] < 25]
    ok_t = [a["seconds_spent"] for a in answers if a["selected"] == a["correct_answer"]]
    bad_t = [a["seconds_spent"] for a in missed]
    avg = lambda xs: sum(xs) / len(xs) if xs else 0.0
    facts = (f'<b>{len(fast)} of your {len(missed)} misses were answered in under 25 seconds.</b> '
             f'You used {mins} minutes for {total_q} items ({att["duration_seconds"] / total_q:.0f}s '
             f'per item). Average time on a correct answer was {avg(ok_t):.0f}s; on a miss, '
             f'{avg(bad_t):.0f}s. ')
    out.append(Spacer(1, 3))
    out.append(panel(facts + rich(notes["timing"]), st, bg=AMBER_BG, border=AMBER,
                     label="TIMING — AND THE ONE HABIT TO CHANGE", pad=7))
    out.append(Spacer(1, 3))

    scope = (f'All {total_q} items are here, in paper order: red headers are misses, amber '
             f'are flagged guesses that landed, green are confident correct answers — reviewed '
             f'so the reasoning, not only the letter, is certain.' if all_items else
             f'The {len(flagged_ok)} flagged-but-correct items are here deliberately — a guess '
             f'that lands is not knowledge.')
    out.append(Paragraph(
        f'<b>How to read this.</b> Each item gets two pages: the question with every option '
        f'annotated, then the theory, the tell to look for next time, and links to the theory '
        f'site and the course video. {scope}', st["body"]))
    return out


def items_page_index(items: List[Dict[str, Any]], qid: str) -> Optional[int]:
    for pos, it in enumerate(items):
        if it["q"].id == qid:
            return 2 + pos * 2
    return None


def bank_notes(q) -> Dict[str, Any]:
    """Item notes built from the question bank, used when no authored notes exist."""
    return {
        "root_cause": "Compare your choice with the option analysis on the question page.",
        "reflex": "Name the deciding constraint in the stem before you read the options.",
        "why_right": code(q.explanation.option_breakdown[q.correct_answer]),
        "theory_title": esc(q.subtopic),
        "theory": [("p", code(q.explanation.summary))],
        "spot": code(q.summary),
    }


# --------------------------------------------------------------------------
# Document assembly
# --------------------------------------------------------------------------


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.line(LM, 11.5 * mm, PAGE_W - RM, 11.5 * mm)
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(FAINT)
    canvas.drawString(LM, 8 * mm,
                      "GCP ACE Exam Simulator — score report and review. "
                      "Not affiliated with or endorsed by Google LLC.")
    canvas.drawRightString(PAGE_W - RM, 8 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def build(att: Dict[str, Any], questions: Dict[str, Any], notes: Dict[str, Any], candidate: str,
          out_path: Path, all_items: bool = False) -> tuple[Path, List[tuple]]:
    st = styles()
    marks: List[tuple] = []

    items: List[Dict[str, Any]] = []
    for n, a in enumerate(att["answers"], 1):
        if all_items or a["flagged"] or a["selected"] != a["correct_answer"]:
            rec = dict(a)
            rec["_n"] = n
            items.append({"rec": rec, "q": questions[a["question_id"]]})

    story: List[Any] = []
    story.append(PageMark("summary", marks))
    story += summary_page(att, items, notes, candidate, st, all_items)

    total = len(items)
    for idx, it in enumerate(items, 1):
        c = CONTENT.get(it["q"].id) or bank_notes(it["q"])
        story.append(PageBreak())
        story.append(PageMark(f"{idx}a:{it['q'].id}", marks))
        story += item_page_one(idx, total, it["rec"], it["q"], c, st)
        story.append(PageBreak())
        story.append(PageMark(f"{idx}b:{it['q'].id}", marks))
        story += item_page_two(idx, total, it["rec"], it["q"], c, st)

    doc = BaseDocTemplate(
        str(out_path), pagesize=LETTER,
        leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
        title=f"ACE Score Report and Review — {att['attempt_id']}",
        author="GCP ACE Exam Simulator",
        subject="Full item review" if all_items else "Missed and flagged item review",
    )
    frame = Frame(LM, BM, CONTENT_W, PAGE_H - TM - BM, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
    doc.build(story)
    return out_path, marks


def verify(marks: List[tuple], n_items: int) -> List[str]:
    """Check the two-pages-per-item contract against real pagination."""
    problems = []
    by = dict(marks)
    for idx in range(1, n_items + 1):
        a = [p for lbl, p in marks if lbl.startswith(f"{idx}a:")]
        b = [p for lbl, p in marks if lbl.startswith(f"{idx}b:")]
        if not a or not b:
            problems.append(f"item {idx}: missing page mark")
            continue
        want_a, want_b = 2 + (idx - 1) * 2, 3 + (idx - 1) * 2
        if a[0] != want_a:
            problems.append(f"item {idx} page 1 landed on p{a[0]}, expected p{want_a}")
        if b[0] != want_b:
            problems.append(f"item {idx} page 2 landed on p{b[0]}, expected p{want_b} "
                            f"(page 1 overflowed)")
    return problems


def build_report(attempt: Attempt, questions: Iterable[Question], candidate: str = "Candidate",
                 out_dir: Optional[Path] = None, all_items: bool = False) -> Path:
    """Write the report for ``attempt`` and return its path.

    ``all_items`` reviews every question; otherwise only missed and flagged ones.
    """
    path, _ = _write(attempt.model_dump(mode="json"), {q.id: q for q in questions}, candidate,
                     out_dir, all_items)
    return path


def _write(att: Dict[str, Any], qmap: Dict[str, Any], candidate: str, out_dir: Optional[Path],
           all_items: bool) -> tuple[Path, List[tuple]]:
    """One naming scheme for the app and the script: ACE-report[-full]-<stamp>-<attempt>.pdf."""
    out_dir = ensure_writable_dir(out_dir or reports_dir())
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    kind = "report-full" if all_items else "report"
    out = out_dir / f"ACE-{kind}-{stamp}-{att['attempt_id']}.pdf"
    notes = ATTEMPTS.get(att["attempt_id"], EMPTY_ATTEMPT_NOTES)
    return build(att, qmap, notes, candidate, out, all_items)


def open_in_browser(path: Path) -> bool:
    """Open the report in the default browser.

    Returns False rather than raising: a container or a remote shell that can't open a
    browser must not lose anyone their report.
    """
    try:
        return webbrowser.open(path.resolve().as_uri())
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--attempt", help="attempt id (default: the most recent certifying attempt)")
    ap.add_argument("--candidate", default="Candidate")
    ap.add_argument("--all", action="store_true",
                    help="review every item on the paper, not only missed and flagged ones")
    ap.add_argument("--open", action="store_true", help="open the PDF when done")
    args = ap.parse_args()

    if not history_path().exists():
        print("No attempts yet: sit an exam in the simulator first.", file=sys.stderr)
        return 1
    attempts = json.loads(history_path().read_text())["attempts"]
    certifying = [a for a in attempts if a["mode"] == "certifying"]
    if not args.attempt and not certifying:
        print("No certifying attempt yet: pass --attempt ID or sit one first.", file=sys.stderr)
        return 1
    if args.attempt:
        matches = [a for a in attempts if a["attempt_id"] == args.attempt]
        if not matches:
            print(f"No attempt {args.attempt!r} in {history_path()}.", file=sys.stderr)
            return 1
        att = matches[0]
    else:
        att = certifying[-1]

    questions = {q.id: q for q in load_bank().questions}
    reviewed = [a["question_id"] for a in att["answers"]
                if args.all or a["flagged"] or a["selected"] != a["correct_answer"]]
    n_items = len(reviewed)

    # An attempt that reviewed an item since removed from the bank cannot be rebuilt.
    purged = [q for q in reviewed if q not in questions]
    if purged:
        print(f"ERROR: attempt {att['attempt_id']} reviews items no longer in the bank: "
              f"{', '.join(purged)}", file=sys.stderr)
        print("Its retrospective cannot be rebuilt; use the PDF in reports/ if one was made.",
              file=sys.stderr)
        return 1

    path, marks = _write(att, questions, args.candidate, None, args.all)

    pages = max(p for _, p in marks)
    problems = verify(marks, n_items)
    print(f"{path}")
    print(f"  items: {n_items}   pages recorded up to: {pages}   expected: {1 + n_items * 2}")
    for p in problems:
        print(f"  LAYOUT: {p}")
    if not problems:
        print("  layout: every item starts on a fresh page, two pages each")

    if args.open:
        open_in_browser(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
