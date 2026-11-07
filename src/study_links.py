"""Where to study a question: theory sections, their live pages and the course video.

Reads data/study_links.json, which scripts/build_study_links.py generates from the
theory pages, the guide map and the video's chapters. Nothing here parses Markdown.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Optional

from .blueprint import SUBTOPICS
from .paths import DATA_DIR

STUDY_LINKS_PATH = DATA_DIR / "study_links.json"


@dataclass(frozen=True)
class Section:
    key: str          # "4.4"
    title: str
    part: int
    url: str          # the live theory page, anchored to the section
    video_seconds: Optional[int]
    text: str         # the section's Markdown, links made absolute

    @property
    def label(self) -> str:
        return f"§{self.key} {self.title}"

    @property
    def video_url(self) -> Optional[str]:
        if self.video_seconds is None:
            return None
        return f"{_data()['video']['url']}?t={self.video_seconds}"

    @property
    def video_clock(self) -> str:
        s = self.video_seconds or 0
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


@lru_cache(maxsize=1)
def _data() -> dict:
    return json.loads(STUDY_LINKS_PATH.read_text(encoding="utf-8"))


def video_url() -> str:
    return _data()["video"]["url"]


def video_title() -> str:
    return _data()["video"]["title"]


def site_url() -> str:
    return _data()["site"]


def section(key: str) -> Section:
    raw = _data()["sections"][key]
    return Section(key=key, title=raw["title"], part=raw["part"], url=raw["url"],
                   video_seconds=raw.get("video_seconds"), text=raw["text"])


def recall_card(part: int) -> Optional[Section]:
    key = _data()["recall_cards"].get(str(part))
    return section(key) if key else None


def sections_for_subtopic(subtopic: str) -> List[Section]:
    """The theory sections that teach a subtopic's guide bullets, in guide order."""
    seen: Dict[str, None] = {key: None for key in _data().get("subtopics", {}).get(subtopic, [])}
    for bullet in SUBTOPICS[subtopic].bullets:
        for key in _data()["bullets"].get(bullet, []):
            seen.setdefault(key, None)
    return [section(k) for k in seen]


def sections_for(question) -> List[Section]:
    return sections_for_subtopic(question.subtopic)


def rank_sections(questions: Iterable) -> List[tuple[Section, int]]:
    """Sections ordered by how many of ``questions`` they teach, most first."""
    counts: Counter = Counter()
    for q in questions:
        for s in sections_for(q):
            counts[s.key] += 1
    return [(section(k), n) for k, n in sorted(counts.items(), key=lambda kv: (-kv[1], _order(kv[0])))]


def _order(key: str) -> tuple[int, int]:
    part, num = key.split(".")
    return int(part), int(num)
