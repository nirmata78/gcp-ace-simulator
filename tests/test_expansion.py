"""The expansion pipeline behind /expand: the plan, the gates on a candidate, and adding a batch."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import kb  # noqa: E402
from src.blueprint import OBJECTIVES, SECTIONS, SUBTOPICS  # noqa: E402
from src.expansion import (  # noqa: E402
    apportion,
    blind_hash,
    blind_sheet,
    has_quote,
    page_text,
    parse_candidate,
    parse_grow,
    plan,
    preview_notes,
    record_blind,
    rework_plan,
    vet,
)
from src.models import OPTION_KEYS, Question, QuestionBank  # noqa: E402

DATA = Path(os.environ["ACE_BANK_DIR"])  # tests/conftest.py: the bank under test
QUOTE = "Custom roles that you create at the organization level can be granted in any project in that organization"
PAGE = f"<html><body><div class=\"devsite-article-body\"><p>{QUOTE.replace('organization level', '<b>organization</b> level')}.</p></div></body></html>"


@pytest.fixture(scope="module")
def bank() -> QuestionBank:
    return QuestionBank.load(DATA)


def docs(url: str) -> str:
    """A stand-in for the documentation: the quote's page, and a gcloud reference page that lists the flags."""
    if "/sdk/gcloud/reference/" in url:
        return "gcloud iam roles create ROLE_ID --organization=ORGANIZATION --file=FILE --project=PROJECT"
    return page_text(PAGE)


def candidate() -> dict:
    """A well-formed candidate. A fixture only: it is never added to the real bank."""
    return {
        "slot": 1,
        "title": "Fixture: one custom role for forty projects",
        "objective": "4.1",
        "subtopic": "Role Types and Custom Roles",
        "summary": "A custom role made at the organization level is grantable in all of its projects.",
        "tags": ["iam", "custom-roles"],
        "question": "Brightfern Labs keeps 40 projects under a single organization, and adds more each quarter. Its "
                    "auditors need one role holding exactly three list permissions, and the role must be grantable "
                    "in every present and future project without being recreated. Where should an administrator "
                    "create the custom role?",
        "options": {
            "A": "In each project, from one shared YAML role definition file",
            "B": "In the folder that holds the audited production projects",
            "C": "At the organization level, then grant it where it is needed",
            "D": "In a dedicated security project that every auditor can view",
        },
        "correct_answer": "C",
        "explanation": {
            "summary": "A custom role lives at the organization or a project; an organization-level one can be "
                       "granted on any resource under that organization.",
            "option_breakdown": {
                "A": "Forty copies drift apart, and each new project needs the fixture role created again.",
                "B": "Fixture rationale: custom roles cannot be created on a folder, only on an organization or project.",
                "C": "Correct. An organization-level custom role is defined once and granted in any project below it.",
                "D": "Fixture rationale: a project-level custom role can be granted only inside that one project.",
            },
            "gcloud_command": "gcloud iam roles create auditLister --organization=ORG_ID --file=role.yaml",
            "doc_ref": "https://docs.cloud.google.com/iam/docs/creating-custom-roles",
        },
        "standard": 2,
        "decided_by": ["every present and future project", "without being recreated"],
        "step": "Grantable in every project, now and later, means define the role once above them all.",
        "trap": {"option": "B", "why": "A folder looks like the shared parent, but custom roles cannot live on one."},
        "evidence": QUOTE,
    }


def one_slot(**over) -> dict:
    slot = {"slot": 1, "batch": 1, "status": "open", "section": 4, "objective": "4.1",
            "subtopic": "Role Types and Custom Roles", "bullets": ["4.1.3"], "kind": "single", "options": 4,
            "choose": 1, "key": "C", "cross": False, "pair_with": None}
    return {"slots": [{**slot, **over}]}


def codes(found: dict, label: str = "slot 1") -> set:
    return {code for sev, code, _ in found.get(label, []) if sev == "error"}


# -- the plan ---------------------------------------------------------------


def test_parse_grow_reads_a_share_and_a_count():
    assert parse_grow("10%", 786) == 79 and parse_grow("25", 786) == 25 and parse_grow("0.01%", 786) == 1
    for bad in ("ten", "-5", "0"):
        with pytest.raises(ValueError):
            parse_grow(bad, 786)


def test_apportion_always_sums():
    assert apportion(7, {"a": 1, "b": 1, "c": 1}) == {"a": 3, "b": 2, "c": 2}
    assert sum(apportion(79, {"a": 0.2, "b": 0.3, "c": 0.3, "d": 0.2}).values()) == 79
    assert apportion(5, {"a": 0, "b": 0}) == {"a": 3, "b": 2}


def test_exam_balance_fills_what_is_below_its_weight_and_never_overshoots(bank):
    p = plan(bank, 79)
    assert len(p["slots"]) == 79
    have = Counter(OBJECTIVES[q.objective].section for q in bank.questions)
    add = Counter(s["section"] for s in p["slots"])
    after = len(bank.questions) + 79
    for n, sec in SECTIONS.items():
        if have[n] >= sec.weight * after:
            assert add[n] == 0, f"section {n} is already at its weight for the bank after the run"
        else:
            assert (have[n] + add[n]) / after <= sec.weight + 0.01
    assert sum(add.values()) == 79


def test_batch_and_current_balances(bank):
    by = lambda p: Counter(s["section"] for s in p["slots"])  # noqa: E731
    assert by(plan(bank, 100, balance="batch")) == {1: 20, 2: 30, 3: 30, 4: 20}
    cur = by(plan(bank, 100, balance="current"))
    have = Counter(OBJECTIVES[q.objective].section for q in bank.questions)
    assert all(abs(cur[n] - 100 * have[n] / len(bank.questions)) <= 1 for n in SECTIONS)


def test_a_plan_can_be_restricted(bank):
    assert {s["section"] for s in plan(bank, 12, sections=[4])["slots"]} == {4}
    assert {s["objective"] for s in plan(bank, 6, objective="2.4")["slots"]} == {"2.4"}


def test_plan_arguments_are_checked(bank):
    assert not [s for s in plan(bank, 40, multi_share=0)["slots"] if s["kind"] == "multi"]
    for bad in (dict(batch_size=0), dict(multi_share=2), dict(subtopics=["Role Types and Custom Roles"], sections=[1])):
        with pytest.raises(ValueError):
            plan(bank, 10, **bad)


def test_a_plan_can_be_aimed_at_subtopics(bank):
    names = ["Role Types and Custom Roles", "Workload Identity Federation"]
    p = plan(bank, 9, subtopics=names)
    assert len(p["slots"]) == 9 and {s["subtopic"] for s in p["slots"]} <= set(names)
    assert all(SUBTOPICS[s["subtopic"]].objective == s["objective"] for s in p["slots"])
    with pytest.raises(ValueError):
        plan(bank, 3, subtopics=["No such subtopic"])


def test_slots_sit_on_the_blueprint_and_thin_subtopics_come_first(bank):
    p = plan(bank, 40)
    for s in p["slots"]:
        assert SUBTOPICS[s["subtopic"]].objective == s["objective"]
    counts = bank.subtopics()
    objective = p["slots"][0]["objective"]
    chosen = [s["subtopic"] for s in p["slots"] if s["objective"] == objective]
    thinnest = min((n for n in SUBTOPICS if SUBTOPICS[n].objective == objective),
                   key=lambda n: counts.get(n, 0) / max(1, len(SUBTOPICS[n].bullets)))
    assert thinnest in chosen


def test_the_mix_and_the_keys_are_planned(bank):
    p = plan(bank, 80)
    slots = p["slots"]
    cross = [s for s in slots if s["cross"]]
    multi = [s for s in slots if s["kind"] == "multi"]
    assert len(cross) == 48 and len(multi) == 8  # standard 2: most questions are multi-topic
    assert any(s["kind"] == "multi" for s in cross) and any(s["kind"] == "single" for s in cross)
    assert all(s["options"] == 5 and len(s["key"].split(",")) == 2 for s in multi)
    assert all(OBJECTIVES[s["pair_with"]].section != s["section"] for s in cross)
    # Planned keys pull the bank's letter spread together, never apart.
    letters = Counter(q.correct_answer for q in bank.questions if not q.is_multi)
    before = max(letters.values()) - min(letters.values())
    letters.update(s["key"] for s in slots if s["kind"] == "single")
    assert set(letters) == set(OPTION_KEYS) and max(letters.values()) - min(letters.values()) <= max(1, before)
    assert plan(bank, 80) == p, "a plan is deterministic"
    assert [s["batch"] for s in slots][:9] == [1] * 8 + [2]


# -- the gates --------------------------------------------------------------


def test_a_sound_candidate_passes(bank):
    found, parsed = vet(bank, [candidate()], plan=one_slot(), pages=docs)
    assert not codes(found) and "slot 1" in parsed


def test_a_candidate_must_match_its_slot(bank):
    found, _ = vet(bank, [candidate()], plan=one_slot(key="A", subtopic="IAM Policies and Inheritance", cross=True))
    msgs = " ".join(m for _, c, m in found["slot 1"] if c == "slot")
    assert "correct_answer" in msgs and "subtopic" in msgs and "also_tests" in msgs
    found, _ = vet(bank, [candidate()], plan=one_slot(status="filled"))
    assert "slot" in codes(found)
    found, _ = vet(bank, [{**candidate(), "slot": 9}], plan=one_slot())
    assert "slot" in codes(found, "slot 9")


def test_form_defects_are_errors_on_a_new_question(bank):
    c = candidate()
    c["question"] = "Where should an administrator create the custom role?"
    c["decided_by"] = ["create the custom role"]
    c["explanation"]["gcloud_command"] = ""
    c["explanation"]["doc_ref"] = "https://example.com/blog/custom-roles"
    c["options"]["C"] += ", because an organization-level custom role is grantable in every project under it"
    c["source"] = "llm"
    c.pop("evidence")
    found, _ = vet(bank, [c])
    assert {"stem-length", "no-command", "doc-ref", "length-tell", "source", "evidence"} <= codes(found, "item 1") | codes(found)


def test_a_restated_bank_question_is_rejected(bank):
    old = bank.questions[0]
    c = candidate()
    c.update(question=old.question, title=old.title, objective=old.objective, subtopic=old.subtopic,
             decided_by=[old.question[:30]])
    c.pop("slot")
    found, _ = vet(bank, [c])
    assert {"stem-overlap", "title"} <= codes(found, "item 1")


def test_candidates_are_compared_with_each_other(bank):
    twin = {**candidate(), "slot": 2, "title": "Fixture: the same thing again"}
    found, _ = vet(bank, [candidate(), twin])
    assert {"stem-overlap", "recycled-options", "copied-rationale"} <= codes(found, "slot 2")
    assert not codes(found, "slot 1")


def test_schema_errors_are_reported_not_raised(bank):
    c = candidate()
    c["options"].pop("D")
    found, parsed = vet(bank, [c, {"slot": 2, "skip": ""}])
    assert codes(found) == {"schema"} and codes(found, "slot 2") == {"skip"} and not parsed


def test_evidence_must_be_on_the_page_word_for_word(bank):
    text = page_text(PAGE)
    assert has_quote(text, QUOTE) and has_quote(text, QUOTE.upper() + ".")
    assert not has_quote(text, QUOTE.replace("any project", "every project")) and not has_quote(text, "")
    found, _ = vet(bank, [{**candidate(), "evidence": QUOTE.replace("any project", "every single project")}],
                   pages=lambda url: text)
    assert "evidence" in codes(found)

    def down(url):
        raise OSError("offline")

    found, _ = vet(bank, [candidate()], pages=down)
    assert "evidence" in codes(found)


def test_a_preview_mention_is_surfaced(bank):
    text = page_text(PAGE.replace("</p>", " This feature is in Preview.</p>"))
    assert preview_notes(text) and not preview_notes(page_text(PAGE))
    found, _ = vet(bank, [candidate()], pages=lambda url: text)
    assert ("warning", "preview") in {(s, c) for s, c, _ in found["slot 1"]}


def test_table_cells_are_not_glued_together():
    text = page_text("<div class='devsite-article-body'><table><tr><td>Nearline</td><td>30 days</td></tr></table></div>")
    assert "Nearline30" not in text and has_quote(text, "Nearline 30 days")


def test_evidence_is_checked_whatever_the_host(bank):
    c = candidate()
    c["explanation"]["doc_ref"] = "https://github.com/GoogleCloudPlatform/example/blob/main/README.md"
    found, _ = vet(bank, [c], pages=lambda url: "A page that says something else entirely.")
    assert "evidence" in codes(found)


def test_page_text_keeps_the_article_and_drops_chrome():
    raw = ("<html><nav>Menu</nav><div class='devsite-article-body'><h1>Title</h1><p>One&nbsp;<code>two</code> three.</p>"
           "<script>var x = 1;</script></div></html>")
    assert page_text(raw).split("\n") == ["Title", "One two three."]


def test_blind_sheet_hides_everything_but_stem_and_options():
    sheet = blind_sheet([candidate(), {"slot": 2, "skip": "nothing new to ask"}])
    assert "Question 1" in sheet and "C. At the organization level" in sheet
    for leak in ("Correct.", "Fixture", "custom-roles", "correct_answer", "Question 2"):
        assert leak not in sheet


def test_final_vetting_needs_an_agreeing_blind_record_for_the_current_wording(bank):
    c = candidate()
    found, _ = vet(bank, [c], final=True)
    assert "blind" in codes(found)
    assert record_blind([c], {"1": "b"}) == [("slot 1", "C", "B", False)]
    for bad in ({"1": "none"}, {"1": "skipped"}, {"7": "C"}):
        with pytest.raises(ValueError):
            record_blind([c], bad)
    assert "blind" in codes(vet(bank, [c], final=True)[0])
    record_blind([c], {"1": " c "})
    assert "blind" in codes(vet(bank, [c], final=True)[0]), "standard 2 needs the solver's by-form report"
    record_blind([c], {"1": " c "}, {"1": "-"})
    assert c["blind"]["hash"] == blind_hash(parse_candidate(c)) and not codes(vet(bank, [c], final=True)[0])
    c["options"]["A"] = "In each project, by importing one shared role definition"
    assert "blind" in codes(vet(bank, [c], final=True)[0]), "an edit after the blind solve voids it"
    record_blind([c], {"1": "C"})
    c["question"] = c["question"].replace("40 projects", "400 projects").replace("Its ", "its ")
    assert "blind" in codes(vet(bank, [c], final=True)[0]), "so does a change of a digit or of case"


# -- adding a batch -----------------------------------------------------------


def _args(tmp: Path, **over) -> argparse.Namespace:
    base = dict(data_dir=tmp / "data", file=tmp / "batch.json", plan=tmp / "plan.json", ledger=tmp / "ledger.json",
                offline=True, dry_run=False)
    return argparse.Namespace(**{**base, **over})


def test_accept_adds_a_batch_and_records_it(tmp_path, capsys):
    shutil.copytree(DATA / "sections", tmp_path / "data" / "sections")
    shutil.copy(DATA / "retired.json", tmp_path / "data" / "retired.json")
    before = QuestionBank.load(tmp_path / "data")
    p = one_slot()
    p["slots"].append({**p["slots"][0], "slot": 2})
    (tmp_path / "plan.json").write_text(json.dumps(p))
    batch = [candidate(), {"slot": 2, "skip": "the bank already asks every decision on this bullet"}]
    (tmp_path / "batch.json").write_text(json.dumps(batch))

    assert kb.cmd_accept(_args(tmp_path)) == 1, "no blind record yet"
    assert len(QuestionBank.load(tmp_path / "data").questions) == len(before.questions)

    record_blind(batch, {"1": "C"}, {"1": "-"})
    (tmp_path / "batch.json").write_text(json.dumps(batch))
    assert kb.cmd_accept(_args(tmp_path)) == 0
    after = QuestionBank.load(tmp_path / "data")
    new = [q for q in after.questions if q.id not in {o.id for o in before.questions}]
    assert len(new) == 1 and new[0].id.startswith("ace-s4-") and new[0].source == "curated"
    assert new[0].id not in QuestionBank.retired_ids(tmp_path / "data")

    slots = json.loads((tmp_path / "plan.json").read_text())["slots"]
    assert [s["status"] for s in slots] == ["filled", "skipped"] and slots[0]["id"] == new[0].id
    entry = json.loads((tmp_path / "ledger.json").read_text())["entries"][0]
    assert entry["id"] == new[0].id and entry["verdict"] == "new" and entry["evidence"]["quote"] == QUOTE
    assert entry["blind_solve"] == {"answer": "C", "agrees": True, "by_form": []} and entry["standard"] == 2
    assert "slot" not in json.dumps(json.loads((tmp_path / "data/sections/section-4-security.json").read_text())["questions"][-1])

    assert kb.cmd_accept(_args(tmp_path)) == 1, "a filled slot cannot be filled twice"
    capsys.readouterr()


# -- reworking seen questions (/rework) ----------------------------------------


def _old(bank) -> "Question":
    """A single-answer question on the fixture's subtopic, to stand for one somebody has seen."""
    return next(q for q in bank.questions if q.subtopic == "Role Types and Custom Roles"
                and not q.is_multi and not q.is_cross_domain and q.correct_answer != "C")


def test_rework_plan_keeps_the_place_and_moves_the_key(bank):
    ids = [q.id for q in bank.questions[:40]]
    p = rework_plan(bank, ["no-such-id", *ids, ids[0]], 20)
    by_id = {q.id: q for q in bank.questions}
    assert [s["replaces"] for s in p["slots"]] == ids[:20], "the order given, unknown and repeated ids dropped"
    for s in p["slots"]:
        old = by_id[s["replaces"]]
        assert (s["objective"], s["subtopic"]) == (old.objective, old.subtopic)
        assert s["key"] != old.correct_answer and s["status"] == "open"
        assert s["cross"] or not old.is_cross_domain
        assert (s["kind"] == "multi") == (s["options"] == 5) and (s["pair_with"] is not None) == s["cross"]
    assert sum(s["cross"] for s in p["slots"]) >= 4 and sum(s["kind"] == "multi" for s in p["slots"]) >= 2
    assert p == rework_plan(bank, ids, 20)
    with pytest.raises(ValueError):
        rework_plan(bank, ["no-such-id"], 5)


def test_seen_order_is_oldest_first_and_reads_only_ids(tmp_path):
    def attempt(n, started, ids):
        return {"attempt_id": n, "mode": "learning", "started_at": started, "finished_at": started,
                "duration_seconds": 1, "question_count": len(ids), "correct_count": 0,
                "answers": [{"question_id": i, "domain": "x", "subtopic": "y", "correct_answer": "A"} for i in ids]}
    path = tmp_path / "history.json"
    path.write_text(json.dumps({"attempts": [attempt("b", "2026-02-01T10:00:00", ["q3", "q1"]),
                                             attempt("a", "2026-01-01T10:00:00", ["q1", "q2"])]}))
    assert kb.seen_order(path) == ["q1", "q2", "q3"]
    assert kb.seen_order(tmp_path / "missing.json") == []


def test_a_rework_must_leave_the_old_question_behind(bank):
    old = _old(bank)
    p = one_slot(replaces=old.id)
    assert not codes(vet(bank, [candidate()], plan=p)[0])
    same = candidate()
    same["options"]["C"] = old.correct_text
    assert "rework-answer" in codes(vet(bank, [same], plan=p)[0])
    reused = candidate()
    wrong = [old.options[k] for k in old.keys if k not in old.correct_keys]
    reused["options"]["A"], reused["options"]["B"] = wrong[0], wrong[1]
    assert "rework-options" in codes(vet(bank, [reused], plan=p)[0])
    assert "rework" in codes(vet(bank, [candidate()], plan=one_slot(replaces="ace-s4-999"))[0])


def test_accepting_a_rework_retires_what_it_replaces(tmp_path, bank, capsys):
    shutil.copytree(DATA / "sections", tmp_path / "data" / "sections")
    shutil.copy(DATA / "retired.json", tmp_path / "data" / "retired.json")
    old = _old(bank)
    (tmp_path / "plan.json").write_text(json.dumps(one_slot(replaces=old.id)))
    batch = [candidate()]
    record_blind(batch, {"1": "C"}, {"1": "-"})
    (tmp_path / "batch.json").write_text(json.dumps(batch))
    assert kb.cmd_accept(_args(tmp_path)) == 0
    after = QuestionBank.load(tmp_path / "data")
    assert len(after.questions) == len(bank.questions) and after.get(old.id) is None
    new_id = json.loads((tmp_path / "plan.json").read_text())["slots"][0]["id"]
    assert after.get(new_id).subtopic == old.subtopic and new_id != old.id
    assert old.id in QuestionBank.retired_ids(tmp_path / "data")
    new, gone = json.loads((tmp_path / "ledger.json").read_text())["entries"]
    assert new["id"] == new_id and old.id in new["notes"]
    assert (gone["id"], gone["verdict"], gone["replacement_id"]) == (old.id, "removed", new_id)
    assert gone["original"]["question"] == old.question
    capsys.readouterr()


# -- standard 2 (docs/question-standard.md) --------------------------------------


def test_a_new_question_must_be_written_to_standard_two(bank):
    c = candidate()
    for key in ("standard", "decided_by", "step", "trap"):
        c.pop(key)
    assert "standard" in codes(vet(bank, [c])[0])


def test_the_problem_first_fields_are_checked(bank):
    for bad in ({"decided_by": ["words that are not in the stem"]}, {"decided_by": []},
                {"step": " ".join(["word"] * 25)}, {"trap": {"option": "C", "why": "C is the key, not a sibling"}},
                {"trap": None}):
        assert "schema" in codes(vet(bank, [{**candidate(), **bad}])[0]), bad


def test_every_named_role_and_command_must_exist(bank):
    c = candidate()
    c["options"]["A"] = "Grant `roles/iam.roleAdmin` in each project and copy the role there"
    c["explanation"]["gcloud_command"] = "gcloud iam roles create auditLister --organization=ORG_ID --made-up-flag"

    def pages(url):
        if url.endswith("roles-permissions/iam"):
            return "roles/iam.roleAdmin Role Administrator"
        if url.endswith("reference/iam/roles/create"):
            return "--organization=ORGANIZATION --file=FILE"
        if "/sdk/gcloud/reference/" in url:
            raise OSError("404")
        return page_text(PAGE)

    msgs = [m for s, code, m in vet(bank, [c], pages=pages)[0]["slot 1"] if code == "identifier"]
    assert len(msgs) == 1 and "--made-up-flag" in msgs[0]
    c["options"]["A"] = "Grant `roles/iam.roleAdministrator` in each project and copy the role there"
    msgs = [m for s, code, m in vet(bank, [c], pages=pages)[0]["slot 1"] if code == "identifier"]
    assert any("roles/iam.roleAdministrator" in m for m in msgs)
    c["explanation"]["gcloud_command"] = "gcloud iam rolez create auditLister"
    msgs = [m for s, code, m in vet(bank, [c], pages=pages)[0]["slot 1"] if code == "identifier"]
    assert any("no gcloud reference page" in m for m in msgs)


def test_a_solver_ruling_an_option_out_by_form_is_a_defect(bank):
    c = candidate()
    record_blind([c], {"1": "C"}, {"1": "D"})
    assert c["blind"]["by_form"] == ["D"] and "by-form" in codes(vet(bank, [c], final=True)[0])
    with pytest.raises(ValueError):
        record_blind([c], {"1": "C"}, {"1": "maybe"})
