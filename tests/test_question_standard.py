"""The machine-checkable parts of docs/question-standard.md, the provenance guard and the overlap audit."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_overlap import CONTAINMENT_LIMIT, JACCARD_LIMIT, audit, flagged, scores, tokens  # noqa: E402
from src.models import QuestionBank  # noqa: E402
from src.question_lint import LONGEST_KEY_LIMIT, lint_bank, lint_question, longest_key_rate  # noqa: E402

DATA = ROOT / "data"


@pytest.fixture(scope="module")
def bank() -> QuestionBank:
    return QuestionBank.load(DATA)


def test_bank_has_no_lint_errors(bank):
    errors = {qid: [f for f in found if f[0] == "error"] for qid, found in lint_bank(bank.questions).items()}
    errors = {qid: f for qid, f in errors.items() if f}
    assert not errors, f"run python scripts/kb.py lint: {errors}"


def test_longest_option_is_not_a_tell(bank):
    assert longest_key_rate(bank.questions) <= LONGEST_KEY_LIMIT


def test_lint_catches_a_bare_cluster_and_a_bad_key_rationale(bank):
    q = bank.questions[0].model_copy(deep=True)
    q.question = "Pods in the cluster keep restarting after the upgrade, and the team must find out why quickly."
    q.explanation.option_breakdown[q.correct_answer] = "Because it is right."
    codes = {code for _, code, _ in lint_question(q)}
    assert {"bare-cluster", "key-rationale"} <= codes


def test_no_bank_stem_matches_a_guarded_stem(bank):
    """Excluded and removed questions must not come back, verbatim or lightly reworded."""
    guard = json.loads((ROOT / "tests" / "fixtures" / "guarded_stems.json").read_text(encoding="utf-8"))
    salt = guard["salt"]
    guarded = [(g["id"], frozenset(g["tokens"])) for g in guard["stems"]]
    hits = []
    for q in bank.questions:
        mine = frozenset(hashlib.sha256((salt + t).encode()).hexdigest()[:12] for t in tokens(q.question))
        for gid, theirs in guarded:
            j, c = scores(mine, theirs)
            if flagged(j, c):
                hits.append((q.id, gid, round(j, 2), round(c, 2)))
    assert not hits, f"bank stems overlap guarded stems: {hits}"


def test_retired_ids_are_never_in_the_bank(bank):
    retired = set(QuestionBank.retired_ids(DATA))
    assert retired, "data/retired.json should list removed ids"
    assert not retired & {q.id for q in bank.questions}


def test_new_ids_skip_retired_and_gaps(bank):
    domain = bank.questions[0].domain
    retired = QuestionBank.retired_ids(DATA)
    new = bank.next_id(domain, retired)
    assert new not in retired and new not in {q.id for q in bank.questions}


def test_overlap_scores():
    a = tokens("A bucket must move objects to Coldline after ninety days")
    assert scores(a, a) == (1.0, 1.0)
    assert scores(a, frozenset()) == (0.0, 0.0)
    j, c = scores(tokens("Coldline bucket objects"), a)
    assert c == 1.0 and j < 1.0
    assert flagged(JACCARD_LIMIT, 0.0) and flagged(0.0, CONTAINMENT_LIMIT) and not flagged(0.29, 0.54)


def test_audit_flags_a_paraphrase_and_passes_an_unrelated_stem():
    refs = {"ref": [tokens("Worker Pods drain a Pub/Sub subscription and CPU stays low while the backlog grows")]}
    rows = audit([("x", "Worker Pods drain a Pub/Sub subscription; CPU stays low as the backlog grows"),
                  ("y", "Which storage class suits data read once a year?")], refs)
    assert [r["flagged"] for r in rows] == [True, False]
