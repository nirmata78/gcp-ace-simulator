"""Merge two history files, so the Python install and the container share one history.

bin/start.sh and bin/stop.sh run it inside the image:

    python -m src.history_sync /state/history.json < data/history.json > merged.json

It reads the local history on stdin and the state history from the path, writes their union
to the path (only if that adds attempts) and to stdout, and reports on stderr:

    to_local=N to_state=M total=T

Attempts are matched by attempt_id and never removed. Exit status 2 means an input wasn't a
valid history, and nothing was written.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .models import History


def merge(state: History, local: History) -> History:
    """Every attempt in either history, once, oldest first. The state copy wins a tie."""
    seen = {a.attempt_id: a for a in local.attempts}
    seen.update({a.attempt_id: a for a in state.attempts})
    return History(attempts=sorted(seen.values(), key=lambda a: (a.finished_at, a.attempt_id)))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    state_path = Path(argv[0])
    text = sys.stdin.read().strip()
    try:
        local = History.model_validate_json(text) if text else History()
    except ValueError as exc:
        print(f"the local history isn't valid: {exc}", file=sys.stderr)
        return 2
    try:
        state = History.load(state_path)
    except ValueError as exc:
        print(f"the history in the volume isn't valid: {exc}", file=sys.stderr)
        return 2

    merged = merge(state, local)
    state_ids = {a.attempt_id for a in state.attempts}
    local_ids = {a.attempt_id for a in local.attempts}
    to_state = len(local_ids - state_ids)
    to_local = len(state_ids - local_ids)
    if to_state:
        merged.save(state_path)
    sys.stdout.write(merged.model_dump_json(indent=2) + "\n")
    print(f"to_local={to_local} to_state={to_state} total={len(merged.attempts)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
