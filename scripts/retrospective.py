#!/usr/bin/env python3
"""Rebuild the report for an attempt in your history (src/retrospective.py builds it).

Run:  python scripts/retrospective.py [--attempt ID] [--all] [--open]
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))  # for the private, optional retro_content.py

from src.retrospective import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
