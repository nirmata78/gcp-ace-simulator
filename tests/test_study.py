"""Study links, the study panel in learning mode, and the report built from them."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src import study_links  # noqa: E402
from src.blueprint import BULLET_LIST, SUBTOPICS  # noqa: E402
from src.exam_engine import ExamSession, load_bank  # noqa: E402
from src.retrospective import EMPTY_ATTEMPT_NOTES, build, build_report, md_blocks, md_inline, verify  # noqa: E402

SITE = "https://nirmata78.github.io/gcp-ace-simulator/theory/"


def test_study_links_are_current() -> None:
    """data/study_links.json must match the theory and the guide map; rebuild it if not."""
    before = (ROOT / "data" / "study_links.json").read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_study_links.py")], check=True,
                   capture_output=True)
    after = (ROOT / "data" / "study_links.json").read_text(encoding="utf-8")
    assert after == before, "run python scripts/build_study_links.py and commit the result"


def test_every_bullet_and_subtopic_has_theory_with_a_video_chapter() -> None:
    data = json.loads((ROOT / "data" / "study_links.json").read_text(encoding="utf-8"))
    assert sorted(data["bullets"]) == sorted(b.id for b in BULLET_LIST)
    for name in SUBTOPICS:
        sections = study_links.sections_for_subtopic(name)
        assert sections, name
        for sec in sections:
            assert sec.url.startswith(SITE) and "#s" in sec.url
            assert sec.video_url and sec.video_url.startswith("https://youtu.be/wXKv62ONQUw?t=")
            assert sec.text and "{:" not in sec.text and "<mark" not in sec.text


def test_theory_links_point_at_the_live_site() -> None:
    for key in ("2.1", "4.4", "9.6"):
        text = study_links.section(key).text
        assert ".md)" not in text and "](#" not in text


def test_markdown_is_converted_for_the_pdf() -> None:
    assert md_inline("**a** `b<c>` [x](https://e.com)") == (
        '<b>a</b> <font face="Courier">b&lt;c&gt;</font> '
        '<font color="#1a56b0"><link href="https://e.com">x</link></font>')
    kinds = [k for k, _ in md_blocks("para\n\n| h | i |\n|--|--|\n| 1 | 2 |\n\n```\ncode\n```\n- item\n   more")]
    assert kinds == ["p", "table", "code", "li"]


def test_report_keeps_two_pages_per_item_and_links_the_course(tmp_path: Path) -> None:
    bank = load_bank().questions[::7]
    sess = ExamSession(bank, mode="certifying")
    for q in bank[: len(bank) // 2]:
        sess.answer("A" if q.correct_answer != "A" else "B", q.id)
    att = sess.build_attempt().model_dump(mode="json")
    path, marks = build(att, {q.id: q for q in bank}, EMPTY_ATTEMPT_NOTES, "T", tmp_path / "r.pdf", True)
    assert verify(marks, len(bank)) == []
    raw = path.read_bytes()
    assert b"youtu.be/wXKv62ONQUw?t=" in raw and SITE.encode() in raw


def test_report_scope_missed_and_flagged_or_everything(tmp_path: Path) -> None:
    bank = load_bank().questions[:10]
    sess = ExamSession(bank, mode="certifying")
    for q in bank:
        sess.answer(q.correct_answer, q.id)
    sess.toggle_flag(bank[0].id)
    attempt = sess.build_attempt()
    short = build_report(attempt, bank, out_dir=tmp_path)
    full = build_report(attempt, bank, out_dir=tmp_path, all_items=True)
    assert short.name.startswith("ACE-report-") and full.name.startswith("ACE-report-full-")
    assert full.stat().st_size > short.stat().st_size


@pytest.fixture
def practice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    monkeypatch.setenv("ACE_STATE_DIR", str(tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    next(b for b in app.button if "Start practice" in b.label).click()
    return app.run()


def test_study_panel_recalls_theory_without_giving_the_answer_away(practice: AppTest) -> None:
    assert not practice.exception
    assert [t.label for t in practice.tabs][-2:] == ["📘 Quick recall", "✅ Why it's right"]
    assert any(e.label.startswith("§") for e in practice.expander)
    assert any("Check answer" in i.value for i in practice.info)


def test_study_panel_explains_the_answer_after_checking(practice: AppTest) -> None:
    practice.radio[0].set_value("A").run()
    next(b for b in practice.button if b.label == "Check answer").click()
    practice.run()
    assert not practice.exception
    text = " ".join(m.value for m in practice.markdown)
    assert "Why the others are wrong" in text and "Spot it next time" in text


def test_study_panel_can_be_closed(practice: AppTest) -> None:
    practice.toggle[0].set_value(False).run()
    assert not practice.exception
    assert "📘 Quick recall" not in [t.label for t in practice.tabs]
