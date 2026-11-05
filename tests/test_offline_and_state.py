"""The app needs no network, and user data goes where ACE_STATE_DIR says."""

from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src import paths  # noqa: E402
from src.exam_engine import (  # noqa: E402
    ExamSession,
    load_bank,
    load_history,
    record_attempt,
    seen_question_ids,
    weighted_sample,
)
from src.pdf_generator import generate_and_open  # noqa: E402


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse every outbound connection, including name lookups."""

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise OSError("network blocked by the test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


def _sit_short_exam() -> tuple[ExamSession, list]:
    questions = weighted_sample(load_bank(), 10)
    session = ExamSession(questions, mode="certifying", duration_seconds=600)
    session.answer("A")
    return session, questions


def _tree(path: Path) -> set[str]:
    return {str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()}


def test_offline_exam_is_sampled_scored_and_reported(
    no_network: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACE_STATE_DIR", str(tmp_path))
    session, questions = _sit_short_exam()
    attempt = session.build_attempt()
    report, opened = generate_and_open(attempt, questions, auto_open=False)
    assert report.read_bytes().startswith(b"%PDF")
    assert opened is False
    assert len(record_attempt(attempt).attempts) == 1


def test_offline_app_starts_without_the_skip_variable(
    no_network: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACE_STATE_DIR", str(tmp_path))
    monkeypatch.delenv("ACE_SKIP_NETWORK_CHECK", raising=False)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert any("Begin examination" in b.label for b in app.button)


def test_offline_llm_authoring_still_aborts(no_network: None) -> None:
    import kb

    with pytest.raises(SystemExit) as raised:
        kb._infer(load_bank(), "any brief", 1, "any-model", None)
    assert raised.value.code == 1


def test_paths_stay_in_the_source_tree_without_state_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACE_STATE_DIR", raising=False)
    assert paths.history_path() == ROOT / "data" / "history.json"
    assert paths.reports_dir() == ROOT / "reports"


def test_empty_state_dir_counts_as_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACE_STATE_DIR", "")
    assert paths.history_path() == ROOT / "data" / "history.json"


def test_full_attempt_writes_only_under_state_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "state"
    monkeypatch.setenv("ACE_STATE_DIR", str(state))
    tracked = [ROOT / "data", ROOT / "reports"]
    before = {d: _tree(d) for d in tracked}

    session, questions = _sit_short_exam()
    attempt = session.build_attempt()
    report, _ = generate_and_open(attempt, questions, auto_open=False)
    record_attempt(attempt)

    assert {d: _tree(d) for d in tracked} == before
    assert _tree(state) == {"history.json", f"reports/{report.name}"}
    assert json.loads((state / "history.json").read_text())["attempts"][0]["attempt_id"] == attempt.attempt_id
    assert load_history().attempts[0].attempt_id == attempt.attempt_id
    assert seen_question_ids()


def test_unwritable_state_dir_names_the_location(tmp_path: Path) -> None:
    blocker = tmp_path / "a-file"
    blocker.write_text("")
    with pytest.raises(OSError, match="ACE_STATE_DIR"):
        paths.ensure_writable_dir(blocker / "reports")
