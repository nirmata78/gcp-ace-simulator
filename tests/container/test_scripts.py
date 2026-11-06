"""bin/start.sh and bin/stop.sh, run for real: pytest tests/container

They use their own compose project, volume, port, history file and reports folder, so they
never touch your simulator, your ace-state volume or your data/history.json.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "ghcr.io/nirmata78/gcp-ace-simulator:local"
VOLUME = "ace-state-scripts-e2e"

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="needs Docker")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def env(tmp_path: Path) -> Iterator[dict[str, str]]:
    env = {**os.environ, "ACE_PORT": str(_free_port()), "ACE_VOLUME": VOLUME,
           "COMPOSE_PROJECT_NAME": "ace-scripts-e2e",
           "ACE_LOCAL_HISTORY": str(tmp_path / "data" / "history.json"),
           "ACE_LOCAL_REPORTS": str(tmp_path / "reports")}
    subprocess.run(["docker", "compose", "down", "-v"], cwd=ROOT, env=env, capture_output=True)
    yield env
    subprocess.run(["docker", "compose", "down", "-v"], cwd=ROOT, env=env, capture_output=True)


def _script(name: str, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    # /bin/bash on purpose: macOS ships bash 3.2, and the scripts must work with it.
    return subprocess.run(["/bin/bash", str(ROOT / "bin" / name), *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=600)


def _history(attempt_ids: list[str]) -> str:
    """A valid history, written by the image's own models."""
    code = (
        "import json,sys;from src.exam_engine import ExamSession,load_bank;"
        "b=load_bank().questions[:3];out=[];"
        "[out.append(ExamSession(b,mode='certifying').build_attempt().model_copy("
        "update={'attempt_id':i,'finished_at':'2026-11-01T10:00:0'+str(n)}).model_dump(mode='json'))"
        " for n,i in enumerate(sys.argv[1:])];print(json.dumps({'version':1,'attempts':out}))"
    )
    return subprocess.run(["docker", "run", "--rm", IMAGE, "python", "-c", code, *attempt_ids],
                          check=True, capture_output=True, text=True).stdout


def _in_volume(*cmd: str, stdin: str | None = None) -> str:
    return subprocess.run(["docker", "run", "--rm", "-i", "-v", f"{VOLUME}:/state", IMAGE, *cmd],
                          check=True, capture_output=True, text=True, input=stdin).stdout


def test_start_imports_history_and_stop_brings_new_attempts_and_reports_back(env: dict[str, str]) -> None:
    subprocess.run(["docker", "compose", "build", "--quiet"], cwd=ROOT, env=env, check=True)
    local = Path(env["ACE_LOCAL_HISTORY"])
    local.parent.mkdir(parents=True)
    local.write_text(_history(["from-python"]))
    local.chmod(0o644)

    started = _script("start.sh", env, "--no-open")
    assert started.returncode == 0, started.stderr
    assert "Copied 1 into Docker and 0 back" in started.stdout
    assert [a["attempt_id"] for a in json.loads(_in_volume("cat", "/state/history.json"))["attempts"]] == ["from-python"]
    assert not local.with_suffix(".json.bak").exists()

    # An exam sat in Docker: a new attempt and its report land in the volume.
    both = _history(["from-python", "from-docker"])
    _in_volume("sh", "-c", "cat > /state/history.json", stdin=both)
    _in_volume("sh", "-c", "mkdir -p /state/reports && echo %PDF > /state/reports/ACE-report-x.pdf")

    refused = _script("start.sh", env, "--no-open")
    assert refused.returncode != 0 and "--yes" in refused.stderr

    stopped = _script("stop.sh", env, "--yes")
    assert stopped.returncode == 0, stopped.stderr
    assert [a["attempt_id"] for a in json.loads(local.read_text())["attempts"]] == ["from-python", "from-docker"]
    assert local.with_suffix(".json.bak").exists()
    assert local.stat().st_mode & 0o777 == 0o644  # the sync keeps the file's permissions
    assert (Path(env["ACE_LOCAL_REPORTS"]) / "ACE-report-x.pdf").exists()
    ps = subprocess.run(["docker", "compose", "ps", "-q"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert ps.stdout.strip() == ""
    assert subprocess.run(["docker", "volume", "inspect", VOLUME], capture_output=True).returncode == 0


def test_restart_with_yes(env: dict[str, str]) -> None:
    assert _script("start.sh", env, "--no-open").returncode == 0
    again = _script("start.sh", env, "--no-open", "--yes")
    assert again.returncode == 0, again.stderr
    assert "already running" in again.stdout


def test_invalid_local_history_stops_before_anything_changes(env: dict[str, str]) -> None:
    local = Path(env["ACE_LOCAL_HISTORY"])
    local.parent.mkdir(parents=True)
    local.write_text("{not json")
    result = _script("start.sh", env, "--no-open")
    assert result.returncode != 0 and "nothing was changed" in result.stderr
    assert local.read_text() == "{not json"
    assert not list(local.parent.glob("history.json.sync.*"))


def test_misuse_is_refused(env: dict[str, str]) -> None:
    assert "never deletes your history" in _script("stop.sh", env, "-v").stderr
    assert "unknown option" in _script("start.sh", env, "--bogus").stderr
    assert "port number" in _script("start.sh", {**env, "ACE_PORT": "80; rm -rf /"}).stderr
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", int(env["ACE_PORT"])))
        busy.listen()
        assert "already in use" in _script("start.sh", env, "--no-open").stderr
