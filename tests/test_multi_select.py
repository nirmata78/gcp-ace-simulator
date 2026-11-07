"""Multiple-select questions ("Choose two"), cross-domain questions, and question GUIDs."""

from __future__ import annotations

import random
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.exam_engine import ExamSession, filtered_pool, weighted_sample  # noqa: E402
from src.models import AnswerRecord, Question, QuestionBank, answer_keys, answer_str, format_answer  # noqa: E402
from src.question_lint import lint_question  # noqa: E402


@pytest.fixture(scope="module")
def bank() -> QuestionBank:
    return QuestionBank.load(ROOT / "data")


def _multi(bank: QuestionBank) -> Question:
    return next(q for q in bank.questions if q.is_multi and not q.certifying_only)


def test_answers_have_one_canonical_form():
    assert answer_str(["C", "A"]) == answer_str("A,C") == answer_str("ca") == "A,C"
    assert answer_str([]) is None and answer_str(None) is None
    assert answer_keys("B") == ["B"]
    assert format_answer("A,C,E") == "A, C and E"


def test_a_multiple_select_answer_counts_only_when_every_letter_matches():
    rec = dict(question_id="q", domain="Section 1: Setting up a cloud solution environment", subtopic="x",
               correct_answer=["C", "A"])
    assert AnswerRecord(**rec, selected="A,C").is_correct
    assert AnswerRecord(**rec, selected=["C", "A"]).is_correct
    assert not AnswerRecord(**rec, selected="A").is_correct
    assert not AnswerRecord(**rec, selected="A,B,C").is_correct


def test_the_session_scores_a_multiple_select_pick(bank):
    q = _multi(bank)
    sess = ExamSession([q], mode="learning")
    sess.answer(list(reversed(q.correct_keys)))
    assert sess.answers[q.id] == q.correct_answer
    assert sess.build_attempt().correct_count == 1
    sess.answer([])
    assert q.id not in sess.answers


def test_bank_has_multiple_select_and_cross_domain_questions(bank):
    multi = [q for q in bank.questions if q.is_multi]
    cross = [q for q in bank.questions if q.is_cross_domain]
    assert len(multi) >= 40 and len(cross) >= 50
    assert all(q.certifying_only for q in cross)
    assert all(len(q.sections) >= 2 for q in cross)
    assert all(q.id.startswith("ace-x-") for q in cross)


def test_every_question_has_a_unique_guid(bank):
    uids = [q.uid for q in bank.questions]
    assert len(set(uids)) == len(uids)
    assert all(str(uuid.UUID(u)) == u for u in uids)


def test_learning_mode_never_draws_cross_domain_questions(bank):
    assert not any(q.certifying_only for q in filtered_pool(bank))


def test_a_certifying_exam_includes_cross_domain_questions_within_the_section_split(bank):
    picked = weighted_sample(bank, 50, random.Random(3))
    assert sum(q.is_cross_domain for q in picked) == 5
    assert len({q.id for q in picked}) == 50


def test_a_multiple_select_question_must_ask_for_the_right_number(bank):
    raw = _multi(bank).model_dump(mode="json")
    keys = sorted(raw["options"])
    with pytest.raises(ValueError):  # all options correct leaves nothing to rule out
        Question.model_validate({**raw, "correct_answer": ",".join(keys)})
    q = Question.model_validate({**raw, "question": raw["question"].split("(Choose")[0].strip()})
    assert "choose-n" in {code for _, code, _ in lint_question(q)}


def test_a_single_answer_question_has_exactly_four_options(bank):
    raw = next(q for q in bank.questions if not q.is_multi).model_dump(mode="json")
    raw["options"]["E"] = "A fifth option"
    raw["explanation"]["option_breakdown"]["E"] = "Wrong."
    with pytest.raises(ValueError):
        Question.model_validate(raw)
