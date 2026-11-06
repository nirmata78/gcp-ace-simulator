"""bin/start.sh and bin/stop.sh merge histories with src/history_sync.py."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import history_sync  # noqa: E402
from src.exam_engine import ExamSession, load_bank  # noqa: E402
from src.models import History  # noqa: E402


def _attempt(n: int):
    bank = load_bank().questions[n : n + 3]
    att = ExamSession(bank, mode="certifying").build_attempt()
    return att.model_copy(update={"attempt_id": f"att{n}", "finished_at": f"2026-11-0{n}T10:00:00"})


def _run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], state: Path, local: str):
    monkeypatch.setattr(sys, "stdin", io.StringIO(local))
    code = history_sync.main([str(state)])
    out = capsys.readouterr()
    return code, out.out, out.err


def test_merge_is_a_union_oldest_first_and_keeps_the_state_copy() -> None:
    a1, a2, a3 = _attempt(1), _attempt(2), _attempt(3)
    state_a2 = a2.model_copy(update={"report_path": "/state/reports/x.pdf"})
    merged = history_sync.merge(History(attempts=[a3, state_a2]), History(attempts=[a2, a1]))
    assert [a.attempt_id for a in merged.attempts] == ["att1", "att2", "att3"]
    assert merged.attempts[1].report_path == "/state/reports/x.pdf"


def test_sync_both_ways(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    state = tmp_path / "history.json"
    History(attempts=[_attempt(2)]).save(state)
    local = History(attempts=[_attempt(1)]).model_dump_json()
    code, out, err = _run(monkeypatch, capsys, state, local)
    assert code == 0
    assert "to_local=1 to_state=1 total=2" in err
    assert [a["attempt_id"] for a in json.loads(out)["attempts"]] == ["att1", "att2"]
    assert len(History.load(state).attempts) == 2


def test_nothing_new_leaves_the_state_file_alone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    state = tmp_path / "history.json"
    History(attempts=[_attempt(1)]).save(state)
    before = state.stat().st_mtime_ns
    code, _, err = _run(monkeypatch, capsys, state, "")
    assert code == 0 and "to_local=1 to_state=0 total=1" in err
    assert state.stat().st_mtime_ns == before


def test_first_run_with_no_history_anywhere(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    code, out, err = _run(monkeypatch, capsys, tmp_path / "history.json", "")
    assert code == 0 and "total=0" in err and json.loads(out)["attempts"] == []
    assert not (tmp_path / "history.json").exists()


@pytest.mark.parametrize("side", ["local", "state"])
def test_invalid_history_changes_nothing(side: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    state = tmp_path / "history.json"
    state.write_text("{not json" if side == "state" else History(attempts=[_attempt(1)]).model_dump_json())
    before = state.read_text()
    code, out, err = _run(monkeypatch, capsys, state, "{not json" if side == "local" else "")
    assert code == 2 and out == "" and "isn't valid" in err
    assert state.read_text() == before
