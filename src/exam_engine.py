"""Exam state machine: sampling, timing, navigation, flagging and scoring.

Deliberately free of Streamlit imports — the engine is a plain object the UI
holds in session state, which is what makes ``tests/test_simulator.py`` able to
drive a full exam without a browser.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from .blueprint import SECTION_LIST, objective_weights, objectives_in
from .paths import DATA_DIR, history_path
from .models import (
    CERTIFYING_QUESTION_COUNT,
    DOMAIN_WEIGHTS,
    DOMAINS,
    EXAM_DURATION_SECONDS,
    BANK_KEY_FIXES,
    AnswerRecord,
    Attempt,
    History,
    Question,
    QuestionBank,
)



# --------------------------------------------------------------------------
# Sampling
# --------------------------------------------------------------------------


def _apportion(total: int, weights: Dict[str, float]) -> Dict[str, int]:
    """Largest-remainder apportionment: integer shares that sum to ``total`` exactly."""
    wsum = sum(weights.values()) or 1.0
    exact = {k: total * w / wsum for k, w in weights.items()}
    out = {k: int(v) for k, v in exact.items()}
    for k in sorted(exact, key=lambda k: exact[k] - out[k], reverse=True)[: total - sum(out.values())]:
        out[k] += 1
    return out


def _spread_pick(pool: List[Question], n: int, rng: random.Random,
                 seen: Optional[Set[str]] = None) -> List[Question]:
    """Pick ``n`` questions: every unseen one before any seen one, and within
    each group round-robin over shuffled subtopics.

    The round-robin keeps one large subtopic from crowding out the rest of an
    objective — the exam samples breadth.
    """
    seen = seen or set()
    picked: List[Question] = []
    for group in ([q for q in pool if q.id not in seen], [q for q in pool if q.id in seen]):
        by_sub: Dict[str, List[Question]] = {}
        for q in group:
            by_sub.setdefault(q.subtopic, []).append(q)
        for qs in by_sub.values():
            rng.shuffle(qs)
        order = list(by_sub)
        rng.shuffle(order)
        while len(picked) < n and any(by_sub.values()):
            for sub in order:
                if by_sub[sub] and len(picked) < n:
                    picked.append(by_sub[sub].pop())
    return picked


def weighted_sample(
    bank: QuestionBank,
    count: int = CERTIFYING_QUESTION_COUNT,
    rng: Optional[random.Random] = None,
    seen: Optional[Set[str]] = None,
) -> List[Question]:
    """Draw ``count`` questions on the June 2026 blueprint.

    Three levels, each by largest-remainder apportionment so counts are exact:

    1. **Sections** at the published weights — 10 / 15 / 15 / 10 of 50.
    2. **Objectives** inside each section, in proportion to their number of
       guide bullets (the guide publishes no finer weights; breadth is the
       only signal it gives).
    3. **Subtopics** inside each objective, round-robin, so the draw covers as
       many distinct guide bullets as possible.

    ``seen`` (question ids already answered in earlier attempts) moves unseen
    questions to the front at every level, so repeated attempts keep meeting
    new material until the bank is exhausted. A short objective or section
    hands its shortfall to the remaining stock rather than returning a short exam.
    """
    rng = rng or random.Random()
    by_obj = bank.by_objective()
    obj_w = objective_weights()

    picked: List[Question] = []
    section_quota = _apportion(count, {d: DOMAIN_WEIGHTS[d] for d in DOMAINS})
    for sec in SECTION_LIST:
        objs = {o.id: obj_w[o.id] for o in objectives_in(sec.number)}
        for oid, n in _apportion(section_quota[sec.label], objs).items():
            picked.extend(_spread_pick(by_obj.get(oid, []), n, rng, seen))

    shortfall = count - len(picked)
    if shortfall > 0:
        chosen = {q.id for q in picked}
        rest = [q for q in bank.questions if q.id not in chosen]
        picked.extend(_spread_pick(rest, shortfall, rng, seen))

    rng.shuffle(picked)
    return picked


def filtered_pool(
    bank: QuestionBank,
    domains: Optional[List[str]] = None,
    subtopics: Optional[List[str]] = None,
    objectives: Optional[List[str]] = None,
    new_only: bool = False,
) -> List[Question]:
    """Learning-mode pool, narrowed to the sections/objectives/subtopics under study.

    ``new_only`` keeps questions on bullets the June 2026 guide introduced.
    """
    pool = bank.questions
    if domains:
        wanted = set(domains)
        pool = [q for q in pool if q.domain in wanted]
    if objectives:
        wanted_obj = set(objectives)
        pool = [q for q in pool if q.objective in wanted_obj]
    if new_only:
        pool = [q for q in pool if q.is_new]
    if subtopics:
        wanted_sub = set(subtopics)
        pool = [q for q in pool if q.subtopic in wanted_sub]
    return list(pool)


# --------------------------------------------------------------------------
# Exam session
# --------------------------------------------------------------------------


class ExamSession:
    """Live state for one sitting.

    Timing is wall-clock against ``started_monotonic``: the UI re-renders
    constantly and must never be able to add or subtract exam time by doing so.
    """

    def __init__(
        self,
        questions: List[Question],
        mode: str = "certifying",
        duration_seconds: int = EXAM_DURATION_SECONDS,
        clock=None,
    ):
        if not questions:
            raise ValueError("cannot start an exam with zero questions")
        self.attempt_id = uuid.uuid4().hex[:12]
        self.mode = mode
        self.questions = questions
        self.duration_seconds = duration_seconds
        self._clock = clock or (lambda: datetime.now(timezone.utc).timestamp())

        self.started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.started_monotonic = self._clock()

        self.index: int = 0
        self.answers: Dict[str, str] = {}          # question_id -> "A".."D"
        self.flagged: set[str] = set()
        self.revealed: set[str] = set()            # learning mode: feedback shown
        self.seconds_spent: Dict[str, float] = {}
        self._last_tick = self.started_monotonic
        self.submitted = False
        self.time_expired = False

    # -- timing ------------------------------------------------------------

    @property
    def elapsed_seconds(self) -> float:
        return max(0.0, self._clock() - self.started_monotonic)

    @property
    def remaining_seconds(self) -> float:
        return max(0.0, self.duration_seconds - self.elapsed_seconds)

    @property
    def is_timed(self) -> bool:
        return self.mode == "certifying"

    def check_expiry(self) -> bool:
        """True once a timed exam has run out. Learning mode never expires."""
        if self.is_timed and self.remaining_seconds <= 0:
            self.time_expired = True
        return self.time_expired

    @staticmethod
    def format_clock(seconds: float) -> str:
        seconds = int(max(0, seconds))
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

    def _bank_time(self) -> None:
        """Attribute elapsed time since the last interaction to the current question."""
        now = self._clock()
        qid = self.current.id
        self.seconds_spent[qid] = self.seconds_spent.get(qid, 0.0) + (now - self._last_tick)
        self._last_tick = now

    # -- navigation --------------------------------------------------------

    @property
    def current(self) -> Question:
        return self.questions[self.index]

    @property
    def total(self) -> int:
        return len(self.questions)

    def goto(self, index: int) -> None:
        if not 0 <= index < self.total:
            return
        self._bank_time()
        self.index = index

    def next_question(self) -> None:
        self.goto(min(self.index + 1, self.total - 1))

    def prev_question(self) -> None:
        self.goto(max(self.index - 1, 0))

    # -- answering ---------------------------------------------------------

    def answer(self, option: str, question_id: Optional[str] = None) -> None:
        qid = question_id or self.current.id
        self.answers[qid] = option

    def clear_answer(self, question_id: Optional[str] = None) -> None:
        self.answers.pop(question_id or self.current.id, None)

    def toggle_flag(self, question_id: Optional[str] = None) -> bool:
        qid = question_id or self.current.id
        if qid in self.flagged:
            self.flagged.discard(qid)
            return False
        self.flagged.add(qid)
        return True

    def reveal(self, question_id: Optional[str] = None) -> None:
        """Learning mode only — unlock the explanation for this question."""
        self.revealed.add(question_id or self.current.id)

    def is_revealed(self, question_id: Optional[str] = None) -> bool:
        return (question_id or self.current.id) in self.revealed

    # -- palette state -----------------------------------------------------

    def status_of(self, index: int) -> str:
        """``answered`` | ``flagged`` | ``unanswered`` — drives the palette grid."""
        qid = self.questions[index].id
        if qid in self.flagged:
            return "flagged"
        return "answered" if qid in self.answers else "unanswered"

    @property
    def answered_count(self) -> int:
        return len(self.answers)

    @property
    def unanswered_count(self) -> int:
        return self.total - self.answered_count

    @property
    def flagged_count(self) -> int:
        return len(self.flagged)

    # -- scoring -----------------------------------------------------------

    def build_attempt(self, report_path: Optional[str] = None) -> Attempt:
        """Grade the sitting. Deferred grading: nothing is scored until here."""
        self._bank_time()
        self.submitted = True

        records = [
            AnswerRecord(
                question_id=q.id,
                domain=q.domain,
                objective=q.objective,
                subtopic=q.subtopic,
                selected=self.answers.get(q.id),
                correct_answer=q.correct_answer,
                flagged=q.id in self.flagged,
                seconds_spent=round(self.seconds_spent.get(q.id, 0.0), 1),
            )
            for q in self.questions
        ]

        return Attempt(
            attempt_id=self.attempt_id,
            mode=self.mode,
            started_at=self.started_at,
            finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            duration_seconds=round(self.elapsed_seconds, 1),
            time_expired=self.time_expired,
            question_count=self.total,
            correct_count=sum(1 for r in records if r.is_correct),
            answers=records,
            report_path=report_path,
            # Recorded against the current bank, so every repair is already reflected. Without
            # this, the validator would treat the new attempt as an old record and repair it.
            bank_fixes=list(BANK_KEY_FIXES),
        )

    def question_by_id(self, qid: str) -> Optional[Question]:
        return next((q for q in self.questions if q.id == qid), None)


# --------------------------------------------------------------------------
# Convenience loaders used by app.py
# --------------------------------------------------------------------------


def load_bank(data_dir: Path = DATA_DIR) -> QuestionBank:
    """Assemble the bank from the per-section files under ``data/sections/``."""
    return QuestionBank.load(data_dir)


def load_history(path: Optional[Path] = None) -> History:
    return History.load(path or history_path())


def seen_question_ids(path: Optional[Path] = None) -> Set[str]:
    """Every question id answered in any recorded attempt."""
    return {a.question_id for att in History.load(path or history_path()).attempts for a in att.answers}


def record_attempt(attempt: Attempt, path: Optional[Path] = None) -> History:
    path = path or history_path()
    history = History.load(path)
    history.append(attempt, path)
    return history
