"""ReportLab score-report engine, plus the auto-open-in-browser hook.

Produces a Pearson-VUE-flavoured score report: verdict banner, section
breakdown bars (the four sections of the June 2026 exam guide), a per-objective
table, weakest-subtopic table, then a full item-by-item review with
the distractor analysis for anything missed.
"""

from __future__ import annotations

import re
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
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

from .blueprint import OBJECTIVES
from .models import (
    DOMAIN_SHORT,
    PASS_THRESHOLD,
    Attempt,
    Question,
)

# Palette — muted, print-safe; matches the UI shell.
INK = colors.HexColor("#12181f")
MUTED = colors.HexColor("#5b6875")
RULE = colors.HexColor("#d6dce3")
BAND = colors.HexColor("#f2f5f8")
PASS_C = colors.HexColor("#1a7f4b")
FAIL_C = colors.HexColor("#b3261e")
ACCENT = colors.HexColor("#1a56b0")

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


# --------------------------------------------------------------------------
# Custom flowables
# --------------------------------------------------------------------------


class ScoreBar(Flowable):
    """Horizontal proportion bar with the pass threshold marked."""

    def __init__(self, pct: float, width: float, height: float = 7 * mm):
        super().__init__()
        self.pct = max(0.0, min(1.0, pct))
        self.width = width
        self.height = height

    def draw(self) -> None:
        c = self.canv
        c.setFillColor(BAND)
        c.setStrokeColor(RULE)
        c.rect(0, 0, self.width, self.height, stroke=1, fill=1)

        fill = PASS_C if self.pct >= PASS_THRESHOLD else FAIL_C
        c.setFillColor(fill)
        c.setStrokeColor(fill)
        if self.pct > 0:
            c.rect(0, 0, self.width * self.pct, self.height, stroke=0, fill=1)

        # threshold tick
        x = self.width * PASS_THRESHOLD
        c.setStrokeColor(INK)
        c.setLineWidth(1)
        c.setDash(2, 2)
        c.line(x, -1.5 * mm, x, self.height + 1.5 * mm)
        c.setDash()

        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(self.width + 2 * mm, self.height / 2 - 2.5, f"{self.pct * 100:.0f}%")


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


def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontSize=19, leading=23, textColor=INK,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontSize=9.5, leading=13,
            textColor=MUTED, alignment=TA_CENTER, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontSize=12.5, leading=15, textColor=INK,
            spaceBefore=12, spaceAfter=5,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"], fontSize=10, leading=13, textColor=ACCENT,
            spaceBefore=8, spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=9, leading=12.5, textColor=INK,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"], fontSize=8, leading=11, textColor=MUTED,
        ),
        "mono": ParagraphStyle(
            "mono", parent=base["Code"], fontSize=7.8, leading=10.5, textColor=INK,
            backColor=BAND, borderPadding=4, leftIndent=2, spaceBefore=3, spaceAfter=3,
        ),
        "verdict": ParagraphStyle(
            "verdict", parent=base["Normal"], fontSize=22, leading=26,
            alignment=TA_CENTER, spaceBefore=4, spaceAfter=2,
        ),
        "verdict_sub": ParagraphStyle(
            "verdict_sub", parent=base["Normal"], fontSize=10, leading=13,
            alignment=TA_CENTER, textColor=MUTED,
        ),
    }


_CODE_SPAN = re.compile(r"`([^`]+)`")


def _esc(text: str) -> str:
    """Escape for ReportLab's mini-HTML, then render `code` spans as monospace.

    Question prose carries markdown-style backticks so the Streamlit UI renders
    identifiers as code; the PDF would otherwise print the backticks literally.
    """
    escaped = (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return _CODE_SPAN.sub(r'<font face="Courier">\1</font>', escaped)


# --------------------------------------------------------------------------
# Report builder
# --------------------------------------------------------------------------


def build_report(
    attempt: Attempt,
    questions: List[Question],
    candidate: str = "Candidate",
    out_dir: Path = REPORTS_DIR,
    include_review: bool = True,
) -> Path:
    """Render the score report and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = out_dir / f"ACE-report-{stamp}-{attempt.attempt_id}.pdf"

    st = _styles()
    qmap = {q.id: q for q in questions}

    doc = BaseDocTemplate(
        str(path),
        pagesize=LETTER,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=18 * mm,
        title=f"GCP ACE Practice Score Report — {attempt.attempt_id}",
        author="GCP ACE Exam Simulator",
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_footer)])

    W = doc.width
    story: List[Flowable] = []

    # ---- header ----------------------------------------------------------
    story += [
        Paragraph("Google Cloud — Associate Cloud Engineer", st["title"]),
        Paragraph("Practice Examination · Score Report", st["subtitle"]),
        Rule(W, INK, 1.2),
        Spacer(1, 7 * mm),
    ]

    # ---- verdict ---------------------------------------------------------
    passed = attempt.passed
    verdict_color = PASS_C if passed else FAIL_C
    verdict = "PASS" if passed else "DID NOT PASS"
    story.append(
        Table(
            [[
                Paragraph(
                    f'<font color="{verdict_color.hexval()}"><b>{verdict}</b></font>',
                    st["verdict"],
                ),
            ], [
                Paragraph(
                    f"{attempt.correct_count} of {attempt.question_count} correct "
                    f"&nbsp;·&nbsp; <b>{attempt.score_pct * 100:.1f}%</b> "
                    f"&nbsp;·&nbsp; threshold {PASS_THRESHOLD * 100:.0f}%",
                    st["verdict_sub"],
                ),
            ]],
            colWidths=[W],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BAND),
                ("BOX", (0, 0), (-1, -1), 0.8, RULE),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 9),
            ]),
        )
    )
    story.append(Spacer(1, 6 * mm))

    # ---- session facts ---------------------------------------------------
    mins, secs = divmod(int(attempt.duration_seconds), 60)
    timing = f"{mins}m {secs:02d}s"
    if attempt.time_expired:
        timing += " (time expired)"
    unanswered = sum(1 for a in attempt.answers if not a.is_answered)

    facts = [
        ["Candidate", candidate, "Attempt ID", attempt.attempt_id],
        ["Mode", attempt.mode.capitalize(), "Time used", timing],
        ["Started", attempt.started_at.replace("T", " "), "Unanswered", str(unanswered)],
        ["Finished", attempt.finished_at.replace("T", " "), "Flagged", str(sum(a.flagged for a in attempt.answers))],
    ]
    story.append(
        Table(
            [[Paragraph(f"<b>{_esc(a)}</b>", st["small"]), Paragraph(_esc(b), st["small"]),
              Paragraph(f"<b>{_esc(c)}</b>", st["small"]), Paragraph(_esc(d), st["small"])]
             for a, b, c, d in facts],
            colWidths=[W * 0.16, W * 0.34, W * 0.16, W * 0.34],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]),
        )
    )

    # ---- domain performance ---------------------------------------------
    story += [Paragraph("Performance by exam-guide section", st["h2"])]
    bar_w = W * 0.34
    rows = [[
        Paragraph("<b>Section</b>", st["small"]),
        Paragraph("<b>Score</b>", st["small"]),
        Paragraph("<b>Proportion correct</b>", st["small"]),
    ]]
    for ds in attempt.domain_scores():
        rows.append([
            Paragraph(_esc(DOMAIN_SHORT.get(ds.domain, ds.domain)), st["body"]),
            Paragraph(f"{ds.correct}/{ds.total}", st["body"]),
            ScoreBar(ds.pct, bar_w),
        ])
    story.append(
        Table(
            rows,
            colWidths=[W * 0.30, W * 0.14, W * 0.56],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, 0), BAND),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]),
        )
    )
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "The dashed marker is the 70% practice threshold. Sections below it are where "
        "remediation buys the most score.", st["small"],
    ))

    # ---- objective performance ------------------------------------------
    obj_rows = attempt.objective_scores()
    if obj_rows:
        story += [Paragraph("Performance by objective", st["h2"])]
        orows = [[
            Paragraph("<b>Objective</b>", st["small"]),
            Paragraph("<b>Correct</b>", st["small"]),
            Paragraph("<b>Accuracy</b>", st["small"]),
        ]]
        for oid, corr, tot in obj_rows:
            colour = "#1a7f4b" if corr / tot >= PASS_THRESHOLD else "#b3261e"
            orows.append([
                Paragraph(f"<b>{oid}</b> {_esc(OBJECTIVES[oid].title)}", st["body"]),
                Paragraph(f"{corr}/{tot}", st["body"]),
                Paragraph(f'<font color="{colour}">{corr / tot * 100:.0f}%</font>', st["body"]),
            ])
        story.append(
            Table(
                orows,
                colWidths=[W * 0.62, W * 0.19, W * 0.19],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), BAND),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]),
            )
        )

    # ---- weakest subtopics ----------------------------------------------
    gaps = attempt.subtopic_gaps()
    if gaps:
        story += [Paragraph("Weakest subtopics", st["h2"])]
        grows = [[
            Paragraph("<b>Subtopic</b>", st["small"]),
            Paragraph("<b>Correct</b>", st["small"]),
            Paragraph("<b>Accuracy</b>", st["small"]),
        ]]
        for sub, corr, tot in gaps:
            grows.append([
                Paragraph(_esc(sub), st["body"]),
                Paragraph(f"{corr}/{tot}", st["body"]),
                Paragraph(f"{corr / tot * 100:.0f}%", st["body"]),
            ])
        story.append(
            Table(
                grows,
                colWidths=[W * 0.62, W * 0.19, W * 0.19],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), BAND),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]),
            )
        )

    # ---- item review -----------------------------------------------------
    if include_review:
        story.append(PageBreak())
        story.append(Paragraph("Item review", st["h2"]))
        story.append(Paragraph(
            "Every item in the order presented. Missed and unanswered items carry the "
            "full distractor analysis.", st["small"],
        ))
        story.append(Spacer(1, 3 * mm))

        for n, rec in enumerate(attempt.answers, start=1):
            q = qmap.get(rec.question_id)
            if q is None:
                continue
            story.append(_item_block(n, rec, q, st, W))
            story.append(Spacer(1, 3.5 * mm))

    doc.build(story)
    return path


def _item_block(n: int, rec, q: Question, st, W: float) -> Flowable:
    """One reviewed question, kept on a single page where it fits."""
    if not rec.is_answered:
        mark, mark_c, verdict = "—", MUTED, "Unanswered"
    elif rec.is_correct:
        mark, mark_c, verdict = "✓", PASS_C, "Correct"
    else:
        mark, mark_c, verdict = "✗", FAIL_C, f"Incorrect — you chose {rec.selected}"

    flag = " · flagged" if rec.flagged else ""
    head = Table(
        [[
            Paragraph(
                f'<font color="{mark_c.hexval()}" size="11"><b>{mark}</b></font> '
                f'<b>Q{n}</b> &nbsp; <font color="{MUTED.hexval()}">'
                f"{_esc(DOMAIN_SHORT.get(q.domain, q.domain))} · {q.objective} · {_esc(q.subtopic)}{flag}</font>",
                st["body"],
            ),
            Paragraph(
                f'<para align="right"><font color="{mark_c.hexval()}"><b>{verdict}</b></font>'
                f'<br/><font color="{MUTED.hexval()}" size="7">{rec.seconds_spent:.0f}s</font></para>',
                st["small"],
            ),
        ]],
        colWidths=[W * 0.68, W * 0.32],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]),
    )

    parts: List[Flowable] = [head, Spacer(1, 2 * mm),
                             Paragraph(_esc(q.question), st["body"]), Spacer(1, 1.5 * mm)]

    for key in ("A", "B", "C", "D"):
        text = _esc(q.options[key])
        if key == q.correct_answer:
            line = f'<font color="{PASS_C.hexval()}"><b>{key}. {text} &nbsp;← correct</b></font>'
        elif key == rec.selected:
            line = f'<font color="{FAIL_C.hexval()}">{key}. {text} &nbsp;← your answer</font>'
        else:
            line = f"{key}. {text}"
        parts.append(Paragraph(line, st["body"]))

    if not rec.is_correct:
        parts += [Spacer(1, 2 * mm), Paragraph("Why", st["h3"]),
                  Paragraph(_esc(q.explanation.summary), st["body"]), Spacer(1, 1.5 * mm)]
        for key in ("A", "B", "C", "D"):
            why = q.explanation.option_breakdown.get(key, "")
            if why:
                parts.append(Paragraph(f"<b>{key}.</b> {_esc(why)}", st["small"]))
        if q.explanation.gcloud_command:
            parts += [Spacer(1, 1.5 * mm),
                      Paragraph(_esc(q.explanation.gcloud_command), st["mono"])]
        if q.explanation.doc_ref:
            parts.append(Paragraph(
                f'<link href="{q.explanation.doc_ref}" color="{ACCENT.hexval()}">'
                f"{_esc(q.explanation.doc_ref)}</link>", st["small"],
            ))

    return KeepTogether(parts)


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        doc.leftMargin, 11 * mm,
        "GCP ACE Exam Simulator — practice report. Not affiliated with or endorsed by Google LLC.",
    )
    canvas.drawRightString(doc.leftMargin + doc.width, 11 * mm, f"Page {canvas.getPageNumber()}")
    canvas.setStrokeColor(RULE)
    canvas.line(doc.leftMargin, 14 * mm, doc.leftMargin + doc.width, 14 * mm)
    canvas.restoreState()


# --------------------------------------------------------------------------
# Browser launch
# --------------------------------------------------------------------------


def open_in_browser(path: Path) -> bool:
    """Open the finished report in the default browser.

    Returns False rather than raising — a headless box that cannot open a
    browser must not lose the candidate their score report.
    """
    try:
        return webbrowser.open(path.resolve().as_uri())
    except Exception:
        return False


def generate_and_open(
    attempt: Attempt,
    questions: List[Question],
    candidate: str = "Candidate",
    out_dir: Path = REPORTS_DIR,
    auto_open: bool = True,
) -> tuple[Path, bool]:
    """Build the report and (by default) launch it. Returns ``(path, opened)``."""
    path = build_report(attempt, questions, candidate=candidate, out_dir=out_dir)
    opened = open_in_browser(path) if auto_open else False
    return path, opened
