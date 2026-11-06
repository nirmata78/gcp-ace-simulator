"""Tests for the ACE simulator: schema, sampling, exam state, scoring, PDF.

Run with:  pytest -q
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.exam_engine import ExamSession, weighted_sample, filtered_pool  # noqa: E402
from src.blueprint import BULLET_LIST, objective_weights, objectives_in  # noqa: E402
from src.models import (  # noqa: E402
    BANK_DIR,
    DOMAIN_FILE,
    DOMAIN_WEIGHTS,
    DOMAINS,
    OPTION_KEYS,
    PASS_THRESHOLD,
    Attempt,
    History,
    Question,
    QuestionBank,
)
from src.retrospective import build_report  # noqa: E402

DATA_DIR = ROOT / "data"


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def bank() -> QuestionBank:
    """The bank on disk — data/sections/ is the source of truth."""
    return QuestionBank.load(DATA_DIR)


@pytest.fixture(scope="session")
def small_bank(bank: QuestionBank) -> QuestionBank:
    """Four questions per objective: small, but still on every part of the blueprint."""
    return QuestionBank(questions=[q for qs in bank.by_objective().values() for q in qs[:4]])


def _raw(qid: str = "x", title: str = "Test question", objective: str = "1.1",
         subtopic: str = "Resource Hierarchy", **extra) -> dict:
    """A minimal valid question dict; override any field with keyword arguments."""
    raw = {"id": qid, "title": title, "objective": objective, "subtopic": subtopic,
           "summary": "s", "question": f"stem {qid}",
           "options": {"A": "a", "B": "b", "C": "c", "D": "d"}, "correct_answer": "A",
           "explanation": {"summary": "s",
                           "option_breakdown": {"A": "a", "B": "b", "C": "c", "D": "d"}}}
    raw.update(extra)
    return raw


# --------------------------------------------------------------------------
# Schema and bank integrity
# --------------------------------------------------------------------------


def test_every_domain_has_enough_for_an_exam(bank: QuestionBank) -> None:
    """Each domain must cover its blueprint share of a 50-question exam."""
    counts = bank.counts()
    for domain, weight in DOMAIN_WEIGHTS.items():
        needed = round(weight * 50)
        assert counts[domain] >= needed, f"{domain}: {counts[domain]} < {needed}"


def test_domain_weights_sum_to_one() -> None:
    assert sum(DOMAIN_WEIGHTS.values()) == pytest.approx(1.0)


def test_question_ids_are_unique(bank: QuestionBank) -> None:
    ids = [q.id for q in bank.questions]
    assert len(set(ids)) == len(ids)


def test_question_stems_are_unique(bank: QuestionBank) -> None:
    stems = [q.question for q in bank.questions]
    assert len(set(stems)) == len(stems)


def test_every_question_is_well_formed(bank: QuestionBank) -> None:
    for q in bank.questions:
        assert set(q.options) == set(OPTION_KEYS)
        assert q.correct_answer in q.options
        assert set(q.explanation.option_breakdown) == set(OPTION_KEYS)
        assert all(v.strip() for v in q.options.values())
        assert all(v.strip() for v in q.explanation.option_breakdown.values())
        assert q.explanation.summary.strip()
        # distractors must be genuinely distinct
        assert len({v.strip().casefold() for v in q.options.values()}) == 4


def test_correct_option_is_marked_correct_in_breakdown(bank: QuestionBank) -> None:
    for q in bank.questions:
        assert q.explanation.option_breakdown[q.correct_answer].startswith("Correct")


def test_doc_refs_point_at_google_cloud(bank: QuestionBank) -> None:
    for q in bank.questions:
        if q.explanation.doc_ref:
            assert q.explanation.doc_ref.startswith("https://")


def test_live_only_lifecycle_question_keeps_its_premise(bank: QuestionBank) -> None:
    """A plain age rule also deletes noncurrent versions, so the stem must say isLive."""
    q = next(q for q in bank.questions if q.id == "ace-s3-147")
    assert "isLive is true" in q.question


def test_correct_answers_are_spread_across_letters(bank: QuestionBank) -> None:
    """A bank where the answer is usually 'C' is a bank you can game."""
    counts = {k: 0 for k in OPTION_KEYS}
    for q in bank.questions:
        counts[q.correct_answer] += 1
    for k, n in counts.items():
        assert 0.20 <= n / len(bank.questions) <= 0.30, f"letter {k} skewed: {n}"


def test_every_question_sits_on_the_june_2026_blueprint(bank: QuestionBank) -> None:
    from src.blueprint import SUBTOPICS, section_of
    for q in bank.questions:
        assert SUBTOPICS[q.subtopic].objective == q.objective
        assert section_of(q.objective).label == q.domain


def test_no_question_is_copied_from_googles_sample_form(bank: QuestionBank) -> None:
    """The bank is original work; see CONTRIBUTING.md for the provenance rule."""
    copied = [q.id for q in bank.questions if q.source == "official-sample"]
    assert not copied, copied


def test_every_guide_bullet_is_taught_at_least_twice(bank: QuestionBank) -> None:
    """One question per bullet is memorised after one sitting; two is the floor."""
    thin = {b: n for b, n in bank.bullet_coverage().items() if n < 2}
    assert not thin, thin


def test_every_objective_can_fill_its_exam_share_three_times(bank: QuestionBank) -> None:
    by_obj = bank.by_objective()
    for oid, w in objective_weights().items():
        assert len(by_obj[oid]) >= 3 * max(1, round(w * 50)), oid


def test_schema_rejects_a_subtopic_outside_the_guide() -> None:
    with pytest.raises(ValueError, match="unknown subtopic"):
        Question.model_validate(_raw(subtopic="App Engine Deployments"))


def test_schema_rejects_a_subtopic_from_another_objective() -> None:
    with pytest.raises(ValueError, match="belongs to objective"):
        Question.model_validate(_raw(objective="1.1", subtopic="VPC Design"))


def test_section_is_derived_from_the_objective() -> None:
    q = Question.model_validate(_raw(objective="3.3", subtopic="Cloud DNS and Cloud NAT"))
    assert q.domain == DOMAINS[2]


def test_schema_rejects_a_section_that_contradicts_the_objective() -> None:
    with pytest.raises(ValueError, match="belongs to"):
        Question.model_validate(_raw(domain=DOMAINS[3]))


def test_every_question_has_a_title_and_summary(bank: QuestionBank) -> None:
    for q in bank.questions:
        assert q.title.strip() and not q.title.endswith((".", "?"))
        assert q.summary.strip()
        assert q.tags, f"{q.id} has no tags"


def test_titles_are_unique(bank: QuestionBank) -> None:
    titles = [q.title.casefold() for q in bank.questions]
    assert len(set(titles)) == len(titles)


def test_bank_has_no_near_duplicate_stems(bank: QuestionBank) -> None:
    """Questions may share a concept, never a statement: no two stems restate each other."""
    dupes = bank.duplicate_pairs()
    assert not dupes, "\n".join(f"{a.id}/{b.id} {s:.0%}" for a, b, s in dupes[:5])


def test_bank_does_not_recycle_answer_sets(bank: QuestionBank) -> None:
    """Questions on one concept must still offer different options."""
    collisions = bank.option_collisions()
    assert not collisions, "\n".join(f"{a.id}/{b.id} ({n} shared)" for a, b, n in collisions[:5])


def test_same_concept_with_new_wording_and_options_is_allowed() -> None:
    """The eased rule: same subtopic and correct answer is fine when stem and options differ."""
    a = _raw("a", "Question a", "1.1", "Resource Hierarchy",
             question="Finance wants one grant that covers all its projects, including future ones.")
    b = _raw("b", "Question b", "1.1", "Resource Hierarchy",
             question="A new marketing department will add projects every quarter; access should follow them "
                      "automatically without anyone editing policies per project.")
    b["options"] = {"A": "Bind the role on the department folder.", "B": "Script a nightly binding job.",
                    "C": "Use one shared project for the department.", "D": "Grant the role at the organisation."}
    bank = QuestionBank.model_validate({"questions": [a, b]})
    assert bank.duplicate_pairs() == []
    assert bank.option_collisions() == []


def test_recycled_answer_set_is_rejected() -> None:
    """Same correct answer plus three identical options is a repeat, however the stem is worded."""
    a = _raw("a", "Question a", "1.1", "Resource Hierarchy", question="First scenario about folders.")
    b = _raw("b", "Question b", "2.1", "Managed Instance Groups",
             question="A completely different story about instance groups and zones.")
    b["options"] = dict(a["options"])
    b["options"]["D"] = "Something new."
    bank = QuestionBank.model_validate({"questions": [a, b]})
    assert [(x.id, y.id, n) for x, y, n in bank.option_collisions()] == [("a", "b", 3)]


def test_enumerated_options_with_a_different_answer_are_allowed() -> None:
    """The four storage classes may recur as options when the correct class differs."""
    a = _raw("a", "Question a", "1.1", "Resource Hierarchy", question="First scenario.")
    b = _raw("b", "Question b", "1.1", "Resource Hierarchy", question="Second, unrelated scenario.",
             correct_answer="C")
    bank = QuestionBank.model_validate({"questions": [a, b]})
    assert bank.option_collisions() == []


def test_similarity_detects_a_restatement(bank: QuestionBank) -> None:
    base = bank.questions[0]
    twin = base.model_copy(deep=True)
    twin.id, twin.title = "twin", "A twin"
    assert base.similarity(twin) == 1.0
    assert base.fingerprint == twin.fingerprint


def test_schema_rejects_a_sentence_as_title() -> None:
    with pytest.raises(ValueError, match="short label"):
        Question.model_validate(_raw(title="What should you do?"))


def test_bank_rejects_duplicate_titles() -> None:
    with pytest.raises(ValueError, match="duplicate question titles"):
        QuestionBank.model_validate({"questions": [_raw("a", "Same"), _raw("b", "same")]})


def test_schema_rejects_duplicate_options() -> None:
    with pytest.raises(ValueError, match="distinct"):
        Question.model_validate(_raw(options={"A": "same", "B": "same", "C": "c", "D": "d"}))


def test_schema_rejects_unknown_domain() -> None:
    with pytest.raises(ValueError, match="unknown domain"):
        Question.model_validate(_raw(domain="Domain 9: Nope"))


def test_schema_rejects_incomplete_breakdown() -> None:
    with pytest.raises(ValueError, match="missing rationale"):
        Question.model_validate(_raw(explanation={"summary": "s",
                                                   "option_breakdown": {"A": "a", "B": "b"}}))


def test_domain_files_are_valid_json_and_partition_the_bank(bank: QuestionBank) -> None:
    domains_dir = DATA_DIR / BANK_DIR
    total = 0
    for domain, filename in DOMAIN_FILE.items():
        raw = json.loads((domains_dir / filename).read_text(encoding="utf-8"))
        assert raw["domain"] == domain
        assert raw["count"] == len(raw["questions"])
        total += raw["count"]
    assert total == len(bank.questions)


def test_register_matches_the_questions_on_disk(bank: QuestionBank) -> None:
    register_path = DATA_DIR / "register.json"
    if not register_path.exists():
        pytest.skip("bank not seeded")
    reg = json.loads(register_path.read_text(encoding="utf-8"))
    assert reg["total"] == len(bank.questions)
    assert {e["id"] for e in reg["entries"]} == {q.id for q in bank.questions}
    by_id = {q.id: q for q in bank.questions}
    for entry in reg["entries"]:
        assert entry["fingerprint"] == by_id[entry["id"]].fingerprint
        assert entry["title"] == by_id[entry["id"]].title


# --------------------------------------------------------------------------
# Sampling
# --------------------------------------------------------------------------


def test_weighted_sample_returns_exact_count(bank: QuestionBank) -> None:
    assert len(weighted_sample(bank, 50, random.Random(1))) == 50


def test_weighted_sample_honours_blueprint(bank: QuestionBank) -> None:
    picked = weighted_sample(bank, 50, random.Random(42))
    counts = {d: 0 for d in DOMAINS}
    for q in picked:
        counts[q.domain] += 1
    # 50 * [0.20, 0.30, 0.30, 0.20] — the June 2026 guide's section weights
    assert [counts[d] for d in DOMAINS] == [10, 15, 15, 10]


def test_weighted_sample_splits_each_section_across_its_objectives(bank: QuestionBank) -> None:
    from src.exam_engine import _apportion
    picked = weighted_sample(bank, 50, random.Random(7))
    got = {}
    for q in picked:
        got[q.objective] = got.get(q.objective, 0) + 1
    w = objective_weights()
    for sec_n, sec_count in enumerate([10, 15, 15, 10], start=1):
        objs = {o.id: w[o.id] for o in objectives_in(sec_n)}
        for oid, n in _apportion(sec_count, objs).items():
            assert got.get(oid, 0) == n, (oid, got.get(oid), n)


def test_weighted_sample_prefers_unseen_questions(bank: QuestionBank) -> None:
    first = weighted_sample(bank, 50, random.Random(8))
    second = weighted_sample(bank, 50, random.Random(9), seen={q.id for q in first})
    assert not {q.id for q in first} & {q.id for q in second}


def test_weighted_sample_spreads_across_subtopics(bank: QuestionBank) -> None:
    picked = weighted_sample(bank, 50, random.Random(10))
    assert len({q.subtopic for q in picked}) >= 40


def test_weighted_sample_has_no_duplicates(bank: QuestionBank) -> None:
    picked = weighted_sample(bank, 50, random.Random(3))
    assert len({q.id for q in picked}) == 50


def test_weighted_sample_handles_short_domains(bank: QuestionBank) -> None:
    """A thin bank must still return the requested count, not a short exam."""
    thin = QuestionBank(questions=bank.questions[:60])
    picked = weighted_sample(thin, 50, random.Random(5))
    assert len(picked) == 50
    assert len({q.id for q in picked}) == 50


def test_filtered_pool_narrows_by_domain(bank: QuestionBank) -> None:
    pool = filtered_pool(bank, domains=[DOMAINS[3]])
    assert pool and all(q.domain == DOMAINS[3] for q in pool)


def test_filtered_pool_narrows_by_objective_and_new_bullets(bank: QuestionBank) -> None:
    pool = filtered_pool(bank, objectives=["3.2"], new_only=True)
    assert pool and all(q.objective == "3.2" and q.is_new for q in pool)


def test_filtered_pool_narrows_by_subtopic(bank: QuestionBank) -> None:
    sub = bank.questions[0].subtopic
    pool = filtered_pool(bank, subtopics=[sub])
    assert pool and all(q.subtopic == sub for q in pool)


# --------------------------------------------------------------------------
# Exam session
# --------------------------------------------------------------------------


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


@pytest.fixture
def session(small_bank: QuestionBank) -> ExamSession:
    qs = weighted_sample(small_bank, 10, random.Random(11))
    return ExamSession(qs, mode="certifying", duration_seconds=120 * 60, clock=FakeClock())


def test_empty_exam_is_rejected() -> None:
    with pytest.raises(ValueError):
        ExamSession([], mode="certifying")


def test_navigation_is_clamped(session: ExamSession) -> None:
    assert session.index == 0
    session.prev_question()
    assert session.index == 0
    for _ in range(50):
        session.next_question()
    assert session.index == session.total - 1


def test_goto_ignores_out_of_range(session: ExamSession) -> None:
    session.goto(99)
    assert session.index == 0
    session.goto(-1)
    assert session.index == 0
    session.goto(4)
    assert session.index == 4


def test_answering_and_clearing(session: ExamSession) -> None:
    qid = session.current.id
    session.answer("B")
    assert session.answers[qid] == "B"
    assert session.answered_count == 1
    assert session.unanswered_count == session.total - 1
    session.clear_answer()
    assert session.answered_count == 0


def test_flag_toggles(session: ExamSession) -> None:
    assert session.toggle_flag() is True
    assert session.flagged_count == 1
    assert session.status_of(0) == "flagged"
    assert session.toggle_flag() is False
    assert session.flagged_count == 0


def test_flag_takes_precedence_over_answered_in_palette(session: ExamSession) -> None:
    session.answer("A")
    assert session.status_of(0) == "answered"
    session.toggle_flag()
    assert session.status_of(0) == "flagged"


def test_palette_status_defaults_to_unanswered(session: ExamSession) -> None:
    assert all(session.status_of(i) == "unanswered" for i in range(session.total))


def test_clock_formatting() -> None:
    assert ExamSession.format_clock(7200) == "02:00:00"
    assert ExamSession.format_clock(3661) == "01:01:01"
    assert ExamSession.format_clock(59) == "00:00:59"
    assert ExamSession.format_clock(-5) == "00:00:00"


def test_timer_counts_down_and_expires(session: ExamSession) -> None:
    clock: FakeClock = session._clock  # type: ignore[assignment]
    assert session.remaining_seconds == pytest.approx(7200)
    assert session.check_expiry() is False
    clock.advance(3600)
    assert session.remaining_seconds == pytest.approx(3600)
    assert session.check_expiry() is False
    clock.advance(3600)
    assert session.remaining_seconds == 0
    assert session.check_expiry() is True


def test_learning_mode_never_expires(small_bank: QuestionBank) -> None:
    clock = FakeClock()
    sess = ExamSession(small_bank.questions[:5], mode="learning",
                       duration_seconds=10, clock=clock)
    clock.advance(10_000)
    assert sess.check_expiry() is False
    assert sess.is_timed is False


def test_time_is_attributed_to_the_question_on_screen(session: ExamSession) -> None:
    clock: FakeClock = session._clock  # type: ignore[assignment]
    first = session.current.id
    clock.advance(30)
    session.next_question()
    second = session.current.id
    clock.advance(10)
    attempt = session.build_attempt()
    spent = {a.question_id: a.seconds_spent for a in attempt.answers}
    assert spent[first] == pytest.approx(30, abs=0.5)
    assert spent[second] == pytest.approx(10, abs=0.5)


def test_reveal_is_tracked(small_bank: QuestionBank) -> None:
    sess = ExamSession(small_bank.questions[:3], mode="learning")
    assert sess.is_revealed() is False
    sess.reveal()
    assert sess.is_revealed() is True


# --------------------------------------------------------------------------
# Scoring — deferred grading
# --------------------------------------------------------------------------


def test_grading_counts_correct_answers(session: ExamSession) -> None:
    for i, q in enumerate(session.questions):
        session.answer(q.correct_answer if i < 7 else _wrong(q), q.id)
    attempt = session.build_attempt()
    assert attempt.correct_count == 7
    assert attempt.question_count == 10
    assert attempt.score_pct == pytest.approx(0.7)


def test_unanswered_counts_as_incorrect(session: ExamSession) -> None:
    session.answer(session.questions[0].correct_answer, session.questions[0].id)
    attempt = session.build_attempt()
    assert attempt.correct_count == 1
    assert sum(1 for a in attempt.answers if not a.is_answered) == 9


def test_pass_threshold_boundary(session: ExamSession) -> None:
    for q in session.questions[:7]:
        session.answer(q.correct_answer, q.id)
    attempt = session.build_attempt()
    assert attempt.score_pct == pytest.approx(PASS_THRESHOLD)
    assert attempt.passed is True


def test_below_threshold_fails(session: ExamSession) -> None:
    for q in session.questions[:6]:
        session.answer(q.correct_answer, q.id)
    assert session.build_attempt().passed is False


def test_grading_is_deferred_until_build_attempt(session: ExamSession) -> None:
    session.answer("A")
    assert session.submitted is False
    session.build_attempt()
    assert session.submitted is True


def test_flags_survive_into_the_attempt(session: ExamSession) -> None:
    session.toggle_flag()
    flagged_id = session.questions[0].id
    attempt = session.build_attempt()
    rec = next(a for a in attempt.answers if a.question_id == flagged_id)
    assert rec.flagged is True


def test_domain_scores_partition_the_exam(session: ExamSession) -> None:
    for q in session.questions:
        session.answer(q.correct_answer, q.id)
    attempt = session.build_attempt()
    assert sum(ds.total for ds in attempt.domain_scores()) == attempt.question_count
    assert all(ds.pct == 1.0 for ds in attempt.domain_scores())


def test_subtopic_gaps_lists_only_imperfect_topics(session: ExamSession) -> None:
    for q in session.questions:
        session.answer(q.correct_answer, q.id)
    assert session.build_attempt().subtopic_gaps() == []


def test_expired_exam_is_marked(session: ExamSession) -> None:
    clock: FakeClock = session._clock  # type: ignore[assignment]
    clock.advance(7300)
    session.check_expiry()
    assert session.build_attempt().time_expired is True


def _wrong(q: Question) -> str:
    return next(k for k in OPTION_KEYS if k != q.correct_answer)


# --------------------------------------------------------------------------
# History persistence
# --------------------------------------------------------------------------


def _attempt(session: ExamSession) -> Attempt:
    for q in session.questions[:8]:
        session.answer(q.correct_answer, q.id)
    return session.build_attempt()


def test_history_round_trips(tmp_path: Path, session: ExamSession) -> None:
    path = tmp_path / "history.json"
    history = History()
    history.append(_attempt(session), path)

    reloaded = History.load(path)
    assert len(reloaded.attempts) == 1
    assert reloaded.attempts[0].correct_count == 8


def test_history_load_handles_missing_and_empty(tmp_path: Path) -> None:
    assert History.load(tmp_path / "nope.json").attempts == []
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")
    assert History.load(empty).attempts == []


def test_history_accumulates_domain_telemetry(tmp_path: Path, small_bank: QuestionBank) -> None:
    path = tmp_path / "history.json"
    history = History()
    for _ in range(3):
        sess = ExamSession(weighted_sample(small_bank, 10, random.Random(2)), mode="certifying")
        for q in sess.questions:
            sess.answer(q.correct_answer, q.id)
        history.append(sess.build_attempt(), path)

    rolling = History.load(path).rolling_domain_accuracy()
    assert rolling
    assert sum(ds.total for ds in rolling.values()) == 30
    assert all(ds.pct == 1.0 for ds in rolling.values())


def test_bank_save_round_trips(tmp_path: Path, small_bank: QuestionBank) -> None:
    small_bank.save(tmp_path)
    assert QuestionBank.load(tmp_path).counts() == small_bank.counts()


def test_attempt_scores_by_objective(session: ExamSession) -> None:
    attempt = _attempt(session)
    rows = attempt.objective_scores()
    assert sum(t for _, _, t in rows) == attempt.question_count
    assert sum(c for _, c, _ in rows) == attempt.correct_count


def test_history_recorded_under_the_five_domain_taxonomy_still_loads() -> None:
    from src.models import AnswerRecord
    rec = AnswerRecord(question_id="ace-dom5-001", subtopic="x", correct_answer="A",
                       domain="Domain 5: Configuring access and security")
    assert rec.domain == DOMAINS[3]


# --------------------------------------------------------------------------
# PDF report
# --------------------------------------------------------------------------


def test_pdf_report_is_generated(tmp_path: Path, session: ExamSession) -> None:
    attempt = _attempt(session)
    path = build_report(attempt, session.questions, candidate="Test Candidate",
                        out_dir=tmp_path)
    assert path.exists()
    assert path.suffix == ".pdf"
    assert path.stat().st_size > 5_000
    assert path.read_bytes()[:5] == b"%PDF-"


def test_pdf_handles_a_perfect_score(tmp_path: Path, session: ExamSession) -> None:
    for q in session.questions:
        session.answer(q.correct_answer, q.id)
    path = build_report(session.build_attempt(), session.questions, out_dir=tmp_path)
    assert path.exists()


def test_pdf_handles_an_all_blank_exam(tmp_path: Path, session: ExamSession) -> None:
    """Nothing answered: every item takes the full review path."""
    path = build_report(session.build_attempt(), session.questions, out_dir=tmp_path)
    assert path.exists()


def test_pdf_escaping_handles_markup_and_code_spans() -> None:
    from src.retrospective import code
    assert code("a & b <c>") == "a &amp; b &lt;c&gt;"
    assert code("run `kubectl logs`") == 'run <font face="Courier">kubectl logs</font>'
    # escaping must happen before the code span is wrapped, not after
    assert "&lt;" in code("`a<b>`")


def test_pdf_escapes_reportlab_markup(tmp_path: Path, small_bank: QuestionBank) -> None:
    q = small_bank.questions[0].model_copy(deep=True)
    q.question = "Does <b>a & b</b> break the <parser>?"
    q.options["A"] = "a < b & c > d"
    sess = ExamSession([q], mode="certifying")
    path = build_report(sess.build_attempt(), [q], out_dir=tmp_path)
    assert path.exists()


# --------------------------------------------------------------------------
# Network policy
# --------------------------------------------------------------------------


def test_offline_probe_returns_false_for_unroutable_host() -> None:
    from check_network import is_online
    assert is_online(timeout=1.0, hosts=[("127.0.0.1", 9)]) is False


def test_require_network_exits_with_status_one(monkeypatch) -> None:
    import check_network
    monkeypatch.setattr(check_network, "is_online", lambda **kw: False)
    with pytest.raises(SystemExit) as exc:
        check_network.require_network(quiet=True)
    assert exc.value.code == 1


def test_abort_message_is_the_specified_string() -> None:
    from check_network import ABORT_MESSAGE
    assert ABORT_MESSAGE == (
        "[ERROR] Internet connection required for LLM/Claude Code features. Aborting."
    )


# --------------------------------------------------------------------------
# Register, lookup and split-file persistence
# --------------------------------------------------------------------------


def test_split_save_and_load_round_trips(tmp_path: Path, bank: QuestionBank) -> None:
    bank.save(tmp_path)
    assert (tmp_path / "register.json").exists()
    for filename in DOMAIN_FILE.values():
        assert (tmp_path / BANK_DIR / filename).exists()

    reloaded = QuestionBank.load(tmp_path)
    assert reloaded.counts() == bank.counts()
    assert {q.id for q in reloaded.questions} == {q.id for q in bank.questions}
    assert {q.title for q in reloaded.questions} == {q.title for q in bank.questions}


def test_domain_is_restored_from_the_file_it_lives_in(tmp_path: Path, bank: QuestionBank) -> None:
    """Domain is implied by the filename, so it is not repeated in every record."""
    bank.save(tmp_path)
    raw = json.loads((tmp_path / BANK_DIR / DOMAIN_FILE[DOMAINS[0]]).read_text())
    assert all("domain" not in q for q in raw["questions"])
    assert all(q.domain == DOMAINS[0] for q in QuestionBank.load(tmp_path).by_domain()[DOMAINS[0]])


def test_load_reports_a_missing_bank(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="data/sections"):
        QuestionBank.load(tmp_path)


def test_get_finds_by_id_and_by_title(bank: QuestionBank) -> None:
    target = bank.questions[0]
    assert bank.get(target.id) is target
    assert bank.get(target.title) is target


def test_get_is_none_when_a_title_fragment_is_ambiguous(bank: QuestionBank) -> None:
    assert bank.get("the") is None  # matches many titles


def test_find_searches_titles_stems_subtopics_and_tags(bank: QuestionBank) -> None:
    assert bank.find("iam")
    assert all(
        "iam" in q.title.casefold() or "iam" in q.question.casefold()
        or "iam" in q.subtopic.casefold() or any("iam" in t for t in q.tags)
        for q in bank.find("iam")
    )
    assert bank.find("zzz-nothing-matches-this") == []


def test_subtopics_scope_to_a_domain(bank: QuestionBank) -> None:
    scoped = bank.subtopics(DOMAINS[3])
    assert scoped
    assert sum(scoped.values()) == bank.counts()[DOMAINS[3]]
    assert set(scoped) <= set(bank.subtopics())


def test_next_id_is_unique_and_domain_scoped(bank: QuestionBank) -> None:
    new_id = bank.next_id(DOMAINS[2])
    assert new_id.startswith("ace-s3-")
    assert new_id not in {q.id for q in bank.questions}


def test_next_id_fills_a_gap(bank: QuestionBank) -> None:
    subset = QuestionBank(questions=[
        q for q in bank.questions
        if q.id.startswith("ace-s1-") and not q.id.endswith(("002", "003"))
    ])
    assert subset.next_id(DOMAINS[0]) == "ace-s1-002"


def test_register_carries_a_row_per_question(bank: QuestionBank) -> None:
    reg = bank.register()
    assert reg["total"] == len(bank.questions)
    assert len(reg["entries"]) == len(bank.questions)
    row = reg["entries"][0]
    assert set(row) >= {"id", "title", "objective", "subtopic", "summary", "tags", "source",
                        "fingerprint", "new_in_2026"}
    # the register indexes; it must not carry the scenario prose
    assert "question" not in row and "options" not in row


def test_register_groups_subtopics_by_domain(bank: QuestionBank) -> None:
    reg = bank.register()
    from src.models import DOMAIN_SHORT
    for domain in DOMAINS:
        assert reg["subtopics_by_domain"][DOMAIN_SHORT[domain]] == bank.subtopics(domain)


def test_tags_are_normalised_to_kebab_case() -> None:
    q = Question.model_validate(_raw(tags=["Cloud Storage", "IAM", "iam", " "]))
    assert q.tags == ["cloud-storage", "iam"]


def test_duplicate_detection_is_scoped_within_a_domain() -> None:
    """Shared vocabulary across domains is not a duplicate."""
    stem = "A regional managed instance group spreads instances across zones."

    def make(qid: str, objective: str, subtopic: str) -> dict:
        return _raw(qid, f"Question {qid}", objective, subtopic, question=stem)
    cross = QuestionBank.model_validate(
        {"questions": [make("a", "1.1", "Regions and Zones"), make("b", "2.1", "Managed Instance Groups")]})
    assert cross.duplicate_pairs() == []

    same = QuestionBank.model_validate(
        {"questions": [make("a", "1.1", "Regions and Zones"), make("b", "1.1", "Resource Hierarchy")]})
    assert len(same.duplicate_pairs()) == 1
