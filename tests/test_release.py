"""The version file and the changelog have to agree, or a release is mislabelled."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# https://semver.org/spec/v2.0.0.html, simplified to the forms this project uses.
SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")


def _version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def test_version_is_semver() -> None:
    assert SEMVER.match(_version())


def test_latest_changelog_entry_matches_version() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    released = re.findall(r"^## \[(\d[^\]]*)\] - \d{4}-\d{2}-\d{2}$", changelog, flags=re.M)
    assert released, "CHANGELOG.md has no dated release"
    assert released[0] == _version()
