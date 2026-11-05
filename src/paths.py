"""Where the simulator keeps user data.

The question bank is read-only product data. History and reports belong to the
person using the simulator, so a container can keep them outside the image.

With ``ACE_STATE_DIR`` set, history is ``$ACE_STATE_DIR/history.json`` and reports
are in ``$ACE_STATE_DIR/reports``. Without it, they stay in ``data/history.json``
and ``reports/``. Paths are resolved on each call, so nothing is fixed at import.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"  # holds sections/ and register.json


def state_dir() -> Path | None:
    """The configured state directory, or None for the source-tree locations."""
    value = os.environ.get("ACE_STATE_DIR")
    return Path(value) if value else None


def history_path() -> Path:
    state = state_dir()
    return (state / "history.json") if state else DATA_DIR / "history.json"


def reports_dir() -> Path:
    state = state_dir()
    return (state / "reports") if state else ROOT / "reports"


def ensure_writable_dir(path: Path) -> Path:
    """Create ``path`` if needed, and name the location when that isn't possible."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OSError(f"Cannot create {path}: {exc}. Check ACE_STATE_DIR and its permissions.") from exc
    if not os.access(path, os.W_OK):
        raise OSError(f"{path} is not writable. Check ACE_STATE_DIR and its permissions.")
    return path
