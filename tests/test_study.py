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


def test_links_are_escaped_once() -> None:
    out = md_inline("[IAM & Admin](https://e.com/?a=1&b=2)")
    assert 'href="https://e.com/?a=1&amp;b=2"' in out and ">IAM &amp; Admin<" in out


def test_a_one_row_table_is_used_and_an_oversized_one_skipped() -> None:
    from src.retrospective import styles, theory_excerpt
    sec = study_links.Section("9.9", "T", 9, SITE, 1, "Intro.\n\n| a | b |\n|--|--|\n| 1 | 2 |\n\nAfter.")
    kinds = [type(f).__name__ for f in theory_excerpt(sec, styles(), 10_000)]
    assert "Table" in kinds and kinds.count("Paragraph") >= 3
    # Room for the heading and one line, not for any table: the table is skipped, the prose kept.
    tight = study_links.Section("9.9", "T", 9, SITE, 1, "| a | b |\n|--|--|\n| x | y |\n\nAfter.")
    kinds = [type(f).__name__ for f in theory_excerpt(tight, styles(), 40)]
    assert "Table" not in kinds and kinds.count("Paragraph") == 2


def test_panel_markdown_leaves_code_blocks_alone() -> None:
    import importlib.util
    src = (ROOT / "app.py").read_text()
    fn = src[src.index("def _md("):src.index("def _section_links")]
    ns: dict = {"re": __import__("re")}
    exec(fn, ns)
    out = ns["_md"]("## Head\ncost $5\n```\n# comment\necho $HOME\n```")
    assert out.splitlines() == ["**Head**", "cost \\$5", "```", "# comment", "echo $HOME", "```"]


def test_unknown_attempt_is_a_clear_error(tmp_path: Path) -> None:
    from src.models import History
    History(attempts=[ExamSession(load_bank().questions[:2], mode="certifying").build_attempt()]).save(
        tmp_path / "history.json")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "retrospective.py"), "--attempt", "typo"],
                       env={**__import__("os").environ, "ACE_STATE_DIR": str(tmp_path)},
                       capture_output=True, text=True)
    assert r.returncode == 1 and "No attempt 'typo'" in r.stderr


def test_study_panel_choice_lasts_between_sessions(practice: AppTest) -> None:
    practice.toggle[0].set_value(False).run()
    next(b for b in practice.button if b.label == "End & Score").click()
    practice.run()
    next(b for b in practice.button if b.label == "Submit now").click()
    practice.run()
    assert practice.session_state.study_panel_pref is False


def test_margin_and_timing_helpers_match_the_pass_line() -> None:
    from src.retrospective import margin_lede, timing_facts
    assert "exactly the 70% threshold" in margin_lede(7, 10)
    assert "2 marks to spare" in margin_lede(9, 10)
    assert "1 mark below" in margin_lede(6, 10)
    att = {"question_count": 2, "duration_seconds": 60, "answers": [
        {"selected": "A", "correct_answer": "A", "seconds_spent": 40},
        {"selected": "B", "correct_answer": "A", "seconds_spent": 10}]}
    assert "1 of your 1 misses" in timing_facts(att)


def test_practice_mode_installs_the_splitter(practice: AppTest) -> None:
    frames = [str(e.proto) for e in practice.get("iframe")]
    assert any("ace-splitter-js" in f and "--ace-split" in f for f in frames)


@pytest.fixture
def results(practice: AppTest) -> AppTest:
    right = practice.session_state.session.current.correct_answer
    practice.radio[0].set_value("B" if right == "A" else "A").run()  # a miss, so there's a review
    next(b for b in practice.button if b.label == "End & Score").click()
    practice.run()
    next(b for b in practice.button if b.label == "Submit now").click()
    return practice.run()


def test_results_show_the_report_in_the_app(results: AppTest) -> None:
    assert not results.exception
    text = " ".join(m.value for m in results.markdown)
    assert "Performance by section" in text and "Where to study next" in text
    assert "youtu.be/wXKv62ONQUw?t=" in text and "Spot it next time" in text
    labels = [e.label for e in results.expander]
    assert any("Q1 ·" in lb for lb in labels)


def test_results_review_scope_switches_to_every_question(results: AppTest) -> None:
    def reviewed(app: AppTest) -> int:
        return sum(1 for e in app.expander if " · Q" in f" {e.label}" or "**Q" in e.label)
    short = reviewed(results)
    results.segmented_control(key="review_scope").set_value("Every question").run()
    assert not results.exception
    assert reviewed(results) == results.session_state.attempt.question_count >= short


def test_full_pdf_download_runs_outside_the_script(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Streamlit calls deferred download data from a server thread, with no session state.
    import threading
    monkeypatch.setenv("ACE_STATE_DIR", str(tmp_path))
    src = (ROOT / "app.py").read_text()
    fn = src[src.index("def _full_report_pdf("):src.index("def render_report_summary(")]
    from src.paths import reports_dir
    from src.retrospective import build_report
    ns: dict = {"Path": Path, "build_report": build_report, "reports_dir": reports_dir}
    exec(fn, ns)
    bank = load_bank().questions[:4]
    attempt = ExamSession(bank, mode="certifying").build_attempt()
    cache: dict = {}
    data = ns["_full_report_pdf"](attempt, bank, "T", cache)
    out: list = []
    t = threading.Thread(target=lambda: out.append(data()))
    t.start()
    t.join()
    assert out[0].startswith(b"%PDF") and cache["path"].name.startswith("ACE-report-full-")
    assert data() == out[0]  # built once, then reused
