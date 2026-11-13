"""The image workflow (T14, decision D7) keeps the promises the plan and RELEASE.md make about published images."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/publish.yml"


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _steps(wf: dict):
    for job in wf["jobs"].values():
        yield from job["steps"]


def test_runs_only_for_release_tags_or_by_hand() -> None:
    triggers = _workflow()[True]  # PyYAML reads the key `on` as a boolean
    assert set(triggers) == {"push", "workflow_dispatch"}
    assert triggers["push"] == {"tags": ["v*.*.*"]}


def test_every_action_is_pinned_to_a_commit() -> None:
    uses = [s["uses"] for s in _steps(_workflow()) if "uses" in s]
    assert uses
    for ref in uses:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", ref), ref


def test_only_the_publish_job_may_write_packages() -> None:
    wf = _workflow()
    assert wf["permissions"] == {"contents": "read"}
    writers = [name for name, job in wf["jobs"].items() if job.get("permissions", {}).get("packages") == "write"]
    assert writers == ["publish"]


def test_both_architectures_and_attestations() -> None:
    build = next(s for s in _steps(_workflow()) if s.get("uses", "").startswith("docker/build-push-action@"))
    assert build["with"]["platforms"] == "linux/amd64,linux/arm64"
    assert build["with"]["provenance"] == "mode=max"
    assert build["with"]["sbom"] is True


def test_the_tag_must_match_the_version_file() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "does not match VERSION" in text


def test_floating_tags_never_move_for_a_prerelease_or_an_older_release() -> None:
    script = next(s for s in _steps(_workflow()) if s.get("id") == "tags")["run"]
    assert 'floating=false' in script
    assert '[ "$PRERELEASE" = false ] && [ "$TAG" = "$highest" ]' in script


def test_registries_match_the_decision() -> None:
    env = _workflow()["env"]
    assert env["GHCR_IMAGE"] == "ghcr.io/nirmata78/gcp-ace-simulator"
    assert env["DOCKERHUB_IMAGE"] == "docker.io/aoreshkevich/gcp-ace-simulator"
