"""The machine-checkable parts of docs/question-standard.md, the provenance guard and the overlap audit."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_overlap import CONTAINMENT_LIMIT, JACCARD_LIMIT, audit, flagged, scores, tokens  # noqa: E402
from src.models import QuestionBank  # noqa: E402
from src.question_lint import LONGEST_KEY_LIMIT, lint_bank, lint_question, longest_key_rate  # noqa: E402

DATA = Path(os.environ["ACE_BANK_DIR"])  # tests/conftest.py: the bank under test


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
    assert retired, "retired.json should list removed ids"
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


# -- standard 2 ----------------------------------------------------------------


def test_identifiers_outside_backticks_are_found():
    from src.question_lint import bare_identifiers

    found = dict((i, k) for k, i in bare_identifiers(
        "Grant roles/iam.serviceAccountUser, then run gcloud compute instances create with --shielded-secure-boot; "
        "the caller needs iam.serviceAccounts.actAs and storage.googleapis.com enabled."))
    assert found == {"roles/iam.serviceAccountUser": "role ID", "gcloud compute instances create": "command",
                     "--shielded-secure-boot": "flag", "iam.serviceAccounts.actAs": "permission",
                     "storage.googleapis.com": "API name"}
    assert not bare_identifiers("Grant `roles/iam.serviceAccountUser` and run `gcloud compute instances list`.")
    assert not bare_identifiers("Use gcloud and the console; the gcloud CLI is installed. See example.com.")


def test_standard_two_makes_bare_identifiers_an_error(bank):
    from src.identifiers import mark

    q = bank.questions[0].model_copy(deep=True)
    q.question, q.explanation.summary = mark(q.question), mark(q.explanation.summary)
    q.options = {k: mark(v) for k, v in q.options.items()}
    q.explanation.option_breakdown = {k: mark(v) for k, v in q.explanation.option_breakdown.items()}
    q.options["A"] = "Grant roles/viewer on the project"
    assert ("warning", "ident-unformatted") in {(s, c) for s, c, _ in lint_question(q)}
    q.standard = 2
    assert ("error", "ident-unformatted") in {(s, c) for s, c, _ in lint_question(q)}
    q.options["A"] = "Grant `roles/viewer` on the project"
    assert "ident-unformatted" not in {c for _, c, _ in lint_question(q)}


def test_siblings_are_options_from_the_same_family():
    from src.models import Question
    from src.question_lint import siblings

    raw = {"id": "x", "title": "Sibling fixture", "objective": "4.1", "subtopic": "Role Types and Custom Roles",
           "summary": "s", "question": "stem", "correct_answer": "A",
           "options": {"A": "`roles/iam.serviceAccountTokenCreator` on the account",
                       "B": "`roles/iam.serviceAccountUser` on the account",
                       "C": "A new VPC firewall rule for egress", "D": "Cloud Monitoring uptime check alerts"},
           "explanation": {"summary": "s", "option_breakdown": {k: k for k in "ABCD"}}}
    assert siblings(Question.model_validate(raw)) == ["B"]


def test_a_legacy_question_keeps_its_stored_form(bank, tmp_path):
    from src.models import _stored

    q = bank.questions[0]
    assert {"standard", "decided_by", "step", "trap"}.isdisjoint(_stored(q))


# -- identifiers in monospace (#17) -------------------------------------------------


def test_mark_puts_bare_identifiers_in_backticks():
    from src.identifiers import mark

    cases = {
        "Run gcloud compute instances create web-1 --zone=us-central1-a, then grant roles/iam.serviceAccountUser.":
            "Run `gcloud compute instances create web-1 --zone=us-central1-a`, then grant `roles/iam.serviceAccountUser`.",
        "kubectl rollout undo deployment/web restores it; bq load --source_format=CSV appends.":
            "`kubectl rollout undo deployment/web` restores it; `bq load --source_format=CSV` appends.",
        "The caller needs iam.serviceAccounts.actAs and storage.googleapis.com enabled.":
            "The caller needs `iam.serviceAccounts.actAs` and `storage.googleapis.com` enabled.",
        "gcloud sql connect to the instance with --user=admin": "`gcloud sql connect` to the instance with `--user=admin`",
    }
    for raw, want in cases.items():
        assert mark(raw) == want
        assert mark(want) == want, "idempotent"


def test_mark_leaves_prose_alone():
    from src.identifiers import mark

    for prose in ("Use gcloud and the console; the gcloud CLI is installed -- see example.com.",
                  "Grant `roles/viewer` and run `gcloud storage ls`.", "", "Cloud Run, GKE and BigQuery."):
        assert mark(prose) == prose


def test_the_bank_text_survives_marking(bank):
    """Marking only adds backticks: removing them gives the stored text back."""
    from src.identifiers import mark

    for q in bank.questions[:200]:
        for text in [q.question, *q.options.values(), *q.explanation.option_breakdown.values()]:
            assert mark(text).replace("`", "") == text.replace("`", "")
            assert mark(text).count("`") % 2 == 0
