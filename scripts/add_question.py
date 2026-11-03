#!/usr/bin/env python3
"""Deprecated shim — question authoring now lives in ``scripts/kb.py add``.

Kept so the original documented entry point keeps working. It forwards every
argument through, so::

    python scripts/add_question.py --topic "Cloud NAT" --count 2

is exactly::

    python scripts/kb.py add --topic "Cloud NAT" --count 2

Use ``kb.py add`` directly for the full option set (``--file``, ``--domain``,
``--threshold``), and ``kb.py --help`` for everything else the bank can do.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kb import main as kb_main  # noqa: E402

if __name__ == "__main__":
    print(
        "[NOTE] add_question.py is deprecated; use `python scripts/kb.py add` instead.",
        file=sys.stderr,
    )
    sys.argv = [sys.argv[0], "add", *sys.argv[1:]]
    sys.exit(kb_main())
