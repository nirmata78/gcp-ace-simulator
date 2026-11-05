"""End-to-end tests of the container: pytest tests/container

Needs Docker, `pip install playwright` and `playwright install chromium`. It uses its own compose project, port and
volume, so it never touches your ace-state volume or a simulator already running on port 8501. It does rebuild the
:local image tag.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import Page, sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "ace-e2e"
VOLUME = "ace-state-e2e"
MARKER = "PLANTED-PERSONAL-DATA-7f3a"

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="needs Docker")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


PORT = _free_port()
ENV = {**os.environ, "ACE_PORT": str(PORT), "ACE_VOLUME": VOLUME}


def _run(*args: str, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=ENV, check=check, capture_output=True, text=True)


def _compose(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run("docker", "compose", "-p", PROJECT, *args, check=check)


def _exec(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _compose("exec", "-T", "simulator", *args, check=check)


@pytest.fixture(scope="module")
def stack() -> Iterator[None]:
    _compose("down", "-v", check=False)
    _compose("up", "-d", "--build", "--wait", "--wait-timeout", "120")
    yield
    _compose("down", "-v", check=False)


def _sit_short_exam(page: Page) -> bytes:
    """Start a 10-question exam, answer one, submit, and return the downloaded report."""
    page.goto(f"http://127.0.0.1:{PORT}")
    page.get_by_role("spinbutton", name="Questions").fill("10")
    page.get_by_role("spinbutton", name="Questions").press("Enter")
    page.get_by_role("button", name="Begin examination").click()
    page.locator('[data-testid="stRadio"] [role="radiogroup"] label').first.click()
    page.get_by_text("1 of 10 answered").wait_for()
    page.get_by_role("button", name="Submit Exam").click()
    page.get_by_role("button", name="Submit now").click()
    with page.expect_download() as download:
        page.get_by_role("button", name="Download PDF report").click()
    return Path(download.value.path()).read_bytes()


def _attempts_on_volume() -> int:
    return len(json.loads(_exec("cat", "/state/history.json").stdout)["attempts"])


def test_sc2_exam_report_and_history_survive_recreating_the_container(stack: None) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context(accept_downloads=True).new_page()
        assert _sit_short_exam(page).startswith(b"%PDF")
        assert _attempts_on_volume() == 1

        _compose("down")  # without -v, as the README says
        _compose("up", "-d", "--wait", "--wait-timeout", "120")

        assert _attempts_on_volume() == 1
        page.goto(f"http://127.0.0.1:{PORT}")
        page.get_by_role("tab", name="History").click()
        page.get_by_text("Rolling accuracy by section").wait_for()
        browser.close()


def test_sc4_runs_as_non_root(stack: None) -> None:
    assert _exec("id", "-u").stdout.strip() != "0"


def test_sc4_root_filesystem_is_read_only(stack: None) -> None:
    assert _exec("touch", "/app/x", check=False).returncode != 0
    assert _exec("touch", "/state/writable").returncode == 0


def test_sc4_port_is_published_to_localhost_only(stack: None) -> None:
    assert _compose("port", "simulator", "8501").stdout.strip() == f"127.0.0.1:{PORT}"


def test_port_in_startup_log_matches_published_port(stack: None) -> None:
    assert f"localhost:{PORT}" in _compose("logs", "simulator").stdout


def test_sc5_starts_with_no_network() -> None:
    _run("docker", "compose", "-p", PROJECT, "build")
    image = "ghcr.io/nirmata78/gcp-ace-simulator:local"
    cid = _run("docker", "run", "-d", "--rm", "--network", "none", image).stdout.strip()
    try:
        deadline = time.time() + 90
        status = ""
        while time.time() < deadline and status != "healthy":
            time.sleep(2)
            status = _run("docker", "inspect", "-f", "{{.State.Health.Status}}", cid).stdout.strip()
        assert status == "healthy"
    finally:
        _run("docker", "rm", "-f", cid, check=False)


def test_sc3_planted_personal_files_stay_out_of_the_image(tmp_path: Path) -> None:
    listed = _run("git", "ls-files", "-co", "--exclude-standard").stdout.splitlines()
    for name in listed:
        source = ROOT / name
        if source.is_file():
            target = tmp_path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for name in ("data/history.json", "private/x", "reports/x.pdf", "scripts/retro_content.py", ".env", "notes.txt",
                 ".streamlit/secrets.toml"):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(MARKER)

    image = "ace-e2e-planted:test"
    _run("docker", "build", "-t", image, ".", cwd=tmp_path)
    try:
        script = (
            f"grep -rl {MARKER} /app /state; "
            "ls -d /app/private /app/reports /app/data/history.json /app/scripts/retro_content.py "
            "/app/.env /app/notes.txt /app/tests /app/theory /app/.streamlit/secrets.toml 2>/dev/null; true"
        )
        assert _run("docker", "run", "--rm", image, "sh", "-c", script).stdout.strip() == ""
    finally:
        _run("docker", "rmi", image, check=False)
