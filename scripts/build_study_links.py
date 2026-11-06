#!/usr/bin/env python3
"""Build data/study_links.json: where to study each guide bullet.

For every bullet of the exam guide it records the theory sections that teach it (from
theory/appendix-a-guide-map.md), and for every section its title, its live URL on the
theory site, its chapter in the published course video, and its text for the app's
recall panel. The app and the PDF report read the JSON; they never parse the theory.

Run after editing the theory or the guide map:

    python scripts/build_study_links.py                         # keeps existing video times
    python scripts/build_study_links.py --video ACE-Full-Course.mp4   # re-reads chapters (needs ffprobe)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.blueprint import BULLET_LIST  # noqa: E402

OUT = ROOT / "data" / "study_links.json"
THEORY = ROOT / "theory"
SITE = "https://nirmata78.github.io/gcp-ace-simulator/theory/"
VIDEO = {
    "id": "wXKv62ONQUw",
    "title": "Google Cloud Associate Cloud Engineer: Full Course, June 2026 Exam Guide",
    "url": "https://youtu.be/wXKv62ONQUw",
}

#: Subtopics that teach no single guide bullet, and the sections that teach them instead.
SUBTOPIC_SECTIONS = {"gcloud CLI and Configurations": ["1.5"]}

_HEADING = re.compile(r"^## (\d+)\.(\d+) (.+)$")
_ROW = re.compile(r"^\| (?:\*\*(\d+\.\d+)\*\* )?(.+?) \| (.+) \|$")
_REF = re.compile(r"\[§(\d+\.\d+)\]")


def _absolute_links(text: str, page: str) -> str:
    """Rewrite the theory's relative links, so they work in the app and in a PDF."""
    text = re.sub(r"\]\((\d\d-[\w-]+|appendix-[\w-]+|practice-scenarios)\.md(#[\w-]+)?\)",
                  lambda m: f"]({SITE}{m.group(1)}.html{m.group(2) or ''})", text)
    return re.sub(r"\]\((#[\w-]+)\)", lambda m: f"]({SITE}{page}.html{m.group(1)})", text)


def _clean(body: str, page: str) -> str:
    lines = [ln for ln in body.splitlines()
             if not re.match(r"^\{:.*\}\s*$", ln) and not ln.startswith("<a id=")]
    text = "\n".join(lines).strip()
    text = re.sub(r"<mark[^>]*>(.*?)</mark>", r"\1", text, flags=re.S)  # site highlighting only
    return _absolute_links(text, page)


def read_sections() -> dict:
    sections: dict = {}
    for path in sorted(THEORY.glob("[0-9][0-9]-*.md")):
        page = path.stem
        current = None
        buf: list[str] = []

        def flush() -> None:
            if current:
                sections[current]["text"] = _clean("\n".join(buf), page)

        for line in path.read_text(encoding="utf-8").splitlines():
            m = _HEADING.match(line)
            if m or line.startswith("## "):
                flush()
                current, buf = None, []
            if m:
                current = f"{m.group(1)}.{m.group(2)}"
                sections[current] = {
                    "title": m.group(3).strip(),
                    "part": int(m.group(1)),
                    "url": f"{SITE}{page}.html#s{m.group(1)}-{m.group(2)}",
                }
            elif current:
                buf.append(line)
        flush()
    return sections


def _words(text: str) -> set[str]:
    stop = {"a", "an", "and", "the", "of", "on", "in", "to", "for", "or", "with", "from", "using", "based"}
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in stop and len(w) > 1}


def read_guide_map() -> dict:
    """Bullet id -> section numbers. The map sometimes merges bullets into one row, so each
    bullet is matched to the row of its own objective whose wording overlaps it most."""
    rows: dict[str, list[tuple[set[str], list[str]]]] = {}
    objective = None
    for line in (THEORY / "appendix-a-guide-map.md").read_text(encoding="utf-8").splitlines():
        m = _ROW.match(line)
        if not m or "§" not in m.group(3):
            continue
        objective = m.group(1) or objective
        rows.setdefault(objective, []).append((_words(m.group(2)), _REF.findall(m.group(3))))

    mapped: dict[str, list[str]] = {}
    used: set[tuple[str, int]] = set()
    for bullet in BULLET_LIST:
        candidates = rows.get(bullet.objective, [])
        if not candidates:
            raise SystemExit(f"guide map has no rows for objective {bullet.objective}")
        words = _words(bullet.text)
        score = [len(words & w) / len(words | w) for w, _ in candidates]
        best = max(range(len(candidates)), key=score.__getitem__)
        if score[best] == 0:
            raise SystemExit(f"no guide-map row matches bullet {bullet.id} {bullet.text!r}")
        mapped[bullet.id] = candidates[best][1]
        used.add((bullet.objective, best))
    unused = [(o, i) for o, rs in rows.items() for i in range(len(rs)) if (o, i) not in used]
    if unused:
        raise SystemExit(f"guide-map rows no bullet matched: {unused}")
    return mapped


def read_video(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_chapters", "-of", "json", str(path)],
                         check=True, capture_output=True, text=True).stdout
    times = {}
    for ch in json.loads(out)["chapters"]:
        m = re.match(r"^(\d+\.\d+) ", ch["tags"]["title"])
        if m:
            times[m.group(1)] = round(float(ch["start_time"]))
    return times


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", type=Path, help="the full-course MP4, to re-read chapter times")
    args = ap.parse_args()

    sections = read_sections()
    bullets = read_guide_map()
    cited = [s for refs in [*bullets.values(), *SUBTOPIC_SECTIONS.values()] for s in refs]
    unknown = sorted(set(cited) - set(sections))
    if unknown:
        raise SystemExit(f"guide map cites sections the theory doesn't have: {unknown}")

    if args.video:
        times = read_video(args.video)
    else:
        old = json.loads(OUT.read_text(encoding="utf-8"))["sections"] if OUT.exists() else {}
        times = {k: v["video_seconds"] for k, v in old.items() if v.get("video_seconds") is not None}
    for key, sec in sections.items():
        sec["video_seconds"] = times.get(key)

    recall = {str(s["part"]): key for key, s in sections.items() if "recall card" in s["title"].lower()}
    data = {
        "_generated_by": "scripts/build_study_links.py; do not edit by hand",
        "site": SITE,
        "video": VIDEO,
        "recall_cards": recall,
        "bullets": bullets,
        "subtopics": SUBTOPIC_SECTIONS,
        "sections": sections,
    }
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    no_video = [k for k, s in sections.items() if s["video_seconds"] is None]
    print(f"{OUT.relative_to(ROOT)}: {len(bullets)} bullets, {len(sections)} sections, "
          f"{len(recall)} recall cards, {len(no_video)} sections without a video chapter {no_video}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
