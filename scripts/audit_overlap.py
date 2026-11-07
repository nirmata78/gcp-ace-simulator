#!/usr/bin/env python3
"""Score question stems against reference stems, for the provenance audit (issue #1).

    python scripts/audit_overlap.py --stems FILE --ref NAME=REF_FILE [--ref NAME=REF_FILE ...] [--json]

``--stems`` is a bank section file, a list of questions, or a JSON Lines file of questions; only each
question's ``id`` and ``question`` are read. Each ``--ref`` is a plain-text file with one reference stem
per line (blank lines ignored). Reference text is never committed to this repository: keep it locally.

Method (the one recorded in review/excluded-questions/audit.json): the stem is normalised (case-folded,
punctuation stripped), split into tokens, and stop words and tokens shorter than three characters are
dropped. For each reference stem B and audited stem A, Jaccard = |A ∩ B| / |A ∪ B| and
containment = |A ∩ B| / |A|, the share of the audited stem's words found in the reference stem (so a stem
lifted into a longer one still scores high, while a short reference cannot match everything it shares a topic with). A stem is flagged when its best
match in any source has Jaccard >= 0.30 or containment >= 0.55. Exit status 1 means something was flagged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.models import _STOPWORDS, _normalise  # noqa: E402

JACCARD_LIMIT = 0.30
CONTAINMENT_LIMIT = 0.55


def tokens(text: str) -> frozenset[str]:
    """The comparison form of a stem."""
    return frozenset(t for t in _normalise(text).split() if len(t) >= 3 and t not in _STOPWORDS)


def scores(a: frozenset[str], b: frozenset[str]) -> Tuple[float, float]:
    """(Jaccard, containment of ``a`` in ``b``) of two token sets; zero when either is empty."""
    if not a or not b:
        return 0.0, 0.0
    shared = len(a & b)
    return shared / len(a | b), shared / len(a)


def best_match(stem: frozenset[str], refs: Iterable[frozenset[str]]) -> Tuple[float, float, int]:
    """The highest (Jaccard, containment) against any reference, and that reference's index."""
    best = (0.0, 0.0, -1)
    for i, ref in enumerate(refs):
        j, c = scores(stem, ref)
        if (j, c) > best[:2]:
            best = (j, c, i)
    return best


def flagged(jaccard: float, containment: float) -> bool:
    return jaccard >= JACCARD_LIMIT or containment >= CONTAINMENT_LIMIT


def load_stems(path: Path) -> List[Tuple[str, str]]:
    """(id, stem) pairs from a section file, a JSON list of questions, or JSON Lines."""
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(data, dict):
        data = data.get("questions", [])
    return [(q["id"], q["question"]) for q in data]


def load_ref(path: Path) -> List[frozenset[str]]:
    return [tokens(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit(stems: List[Tuple[str, str]], sources: Dict[str, List[frozenset[str]]]) -> List[dict]:
    """One row per stem: its best match in every source and whether any crosses a threshold."""
    rows = []
    for qid, stem in stems:
        t = tokens(stem)
        row = {"id": qid, "sources": {}, "flagged": False}
        for name, refs in sources.items():
            j, c, i = best_match(t, refs)
            row["sources"][name] = {"jaccard": round(j, 3), "containment": round(c, 3), "ref_line": i + 1}
            row["flagged"] |= flagged(j, c)
        rows.append(row)
    return rows


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--stems", type=Path, required=True)
    p.add_argument("--ref", action="append", required=True, metavar="NAME=FILE")
    p.add_argument("--json", action="store_true", help="print rows as JSON")
    args = p.parse_args(argv)
    sources = {}
    for spec in args.ref:
        name, _, file = spec.partition("=")
        if not file:
            p.error(f"--ref needs NAME=FILE, got {spec!r}")
        sources[name] = load_ref(Path(file))
    rows = audit(load_stems(args.stems), sources)
    if args.json:
        print(json.dumps(rows, indent=1))
    else:
        for r in rows:
            worst = max(r["sources"].items(), key=lambda kv: (kv[1]["jaccard"], kv[1]["containment"]))
            mark = "FLAG" if r["flagged"] else "ok  "
            print(f"{mark} {r['id']:<16} worst {worst[0]}: jaccard {worst[1]['jaccard']:.2f}, "
                  f"containment {worst[1]['containment']:.2f}")
        n = sum(r["flagged"] for r in rows)
        print(f"\n{len(rows)} stems, {n} flagged (jaccard >= {JACCARD_LIMIT} or containment >= {CONTAINMENT_LIMIT}), "
              f"against {', '.join(f'{k} ({len(v)})' for k, v in sources.items())}")
    return 1 if any(r["flagged"] for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
