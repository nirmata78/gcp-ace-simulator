"""The question bank stays out of git (banks/README.md)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(), reason="needs a git clone")


def _tracked() -> list[str]:
    return subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.split()


def test_no_bank_folder_is_tracked() -> None:
    assert [f for f in _tracked() if f.startswith("banks/")] == ["banks/README.md"]


def test_git_ignores_any_bank_folder() -> None:
    for path in ("banks/private/sections/section-1-setup.json", "banks/my-bank/register.json"):
        assert subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode == 0, path


def test_no_tracked_json_holds_questions() -> None:
    """A question is a dict with options and an option_breakdown; none may sit in a tracked file."""
    leaks = []
    for name in _tracked():
        if name.endswith(".json") and (ROOT / name).is_file():
            text = (ROOT / name).read_text(encoding="utf-8")
            if '"option_breakdown"' in text or '"correct_answer"' in text:
                leaks.append(name)
    assert not leaks, f"question text in tracked files: {leaks}"


def test_the_default_bank_is_the_ignored_folder(monkeypatch) -> None:
    from src import paths

    monkeypatch.delenv("ACE_BANK_DIR", raising=False)
    assert paths.bank_dir() == ROOT / "banks" / "private"
    monkeypatch.setenv("ACE_BANK_DIR", "/tmp/elsewhere")
    assert paths.bank_dir() == Path("/tmp/elsewhere").resolve()
