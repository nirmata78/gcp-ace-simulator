"""A generated question bank for tests and CI: valid in every structural way, and about nothing.

The real bank is private (``banks/README.md``), so the tests cannot depend on it. This bank has the same shape: every
subtopic of the June 2026 guide, enough questions for each objective's share of three exams, multiple-select and
cross-domain questions, an even key spread and stems that do not overlap. Its text is made of pseudo-words, so it
teaches nothing and can never be mistaken for a question.

    python -m tests.fixture_bank OUT_DIR      write the bank to OUT_DIR (sections/, register.json, retired.json)

Deterministic: the same code always writes the same bank.
"""

from __future__ import annotations

import json
import math
import random
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.blueprint import OBJECTIVE_LIST, SECTION_LIST, objective_weights, section_of, subtopics_in  # noqa: E402
from src.models import RETIRED_FILE, Question, QuestionBank  # noqa: E402

SEED = 20261116
NS = uuid.UUID("6f1c2a52-0d4e-4b8a-9a43-7d1c0e5b2f10")
#: Ids left out of the bank and listed as retired, so the gap and retired-id rules have something to test.
RETIRED = ("ace-s1-004", "ace-s3-010")
#: Cross-domain questions; a certifying exam draws five.
CROSS = 52
MULTI_EVERY = 7


def _vocabulary(rng: random.Random, n: int = 4000) -> list[str]:
    on, nu, co = "bdfgklmnprstvz", "aeiou", "nrstlk"
    words: set[str] = set()
    while len(words) < n:
        words.add("".join(rng.choice(on) + rng.choice(nu) for _ in range(rng.randint(2, 3))) + rng.choice(co))
    return sorted(words)


class _Writer:
    def __init__(self) -> None:
        self.rng = random.Random(SEED)
        self.vocab = _vocabulary(self.rng)
        self.n = 0

    def words(self, k: int) -> str:
        return " ".join(self.rng.sample(self.vocab, k))

    def question(self, qid: str, objective: str, subtopic: str, key: str, also: list[str]) -> dict:
        self.n += 1
        multi = "," in key
        letters = ["A", "B", "C", "D", "E"] if multi else ["A", "B", "C", "D"]
        stem = (f"Fixture scenario {self.n}. The {self.words(1)} team runs {self.words(6)}, and must keep "
                f"{self.words(6)} without extra {self.words(4)}. Which option meets the {self.words(2)} constraint?")
        if multi:
            stem += " (Choose two.)"
        options = {k: f"Use {self.words(3)} with {self.words(2)}" for k in letters}
        keys = key.split(",")
        breakdown = {k: (f"Correct. {self.words(7)}." if k in keys else f"Fails here: {self.words(7)}.")
                     for k in letters}
        return {
            "id": qid, "uid": str(uuid.uuid5(NS, qid)), "title": f"Fixture {self.n} {self.words(2)}",
            "objective": objective, "subtopic": subtopic, "summary": f"Fixture idea {self.words(5)}.",
            "tags": ["fixture"], "source": "curated", "question": stem, "options": options, "correct_answer": key,
            "explanation": {"summary": f"Fixture mechanism {self.words(8)}.", "option_breakdown": breakdown,
                            "gcloud_command": "# Console > Fixture", "doc_ref": "https://docs.cloud.google.com/docs"},
            "also_tests": also,
        }


def build() -> QuestionBank:
    w = _Writer()
    weights = objective_weights()
    singles = iter(["A", "B", "C", "D"] * 400)
    pairs = iter(["A,C", "B,D", "A,E", "C,E", "B,E", "A,D", "B,C", "D,E", "A,B", "C,D"] * 40)
    counters = {s.number: 0 for s in SECTION_LIST}
    raws: list[dict] = []

    def next_id(section: int) -> str:
        while True:
            counters[section] += 1
            qid = f"ace-s{section}-{counters[section]:03d}"
            if qid not in RETIRED:
                return qid

    for obj in OBJECTIVE_LIST:
        subs = subtopics_in(obj.id)
        need = 3 * max(1, round(weights[obj.id] * 50)) + 2
        per = max(3, math.ceil(need / len(subs)))
        for s in subs:
            for _ in range(per):
                multi = (w.n + 1) % MULTI_EVERY == 0
                raws.append(w.question(next_id(obj.section), obj.id, s.name, next(pairs) if multi else next(singles), []))

    for i in range(CROSS):
        obj = OBJECTIVE_LIST[i % len(OBJECTIVE_LIST)]
        other = next(o for o in OBJECTIVE_LIST[i % 3:] if section_of(o.id).number != obj.section)
        key = next(pairs) if i % 4 == 1 else next(singles)
        raws.append(w.question(f"ace-x-{i + 1:03d}", obj.id, subtopics_in(obj.id)[0].name, key, [other.id]))

    return QuestionBank(questions=[Question.model_validate(r) for r in raws])


def write(out: Path) -> Path:
    """Write the fixture bank to ``out`` and return it."""
    out = Path(out)
    build().save(out)
    retired = {"_note": "Fixture: ids left out of the generated bank.",
               "retired": [{"id": i, "date": "2026-11-16", "reason": "fixture gap"} for i in RETIRED]}
    (out / RETIRED_FILE).write_text(json.dumps(retired, indent=1) + "\n", encoding="utf-8")
    # Readable by the container's non-root user when mounted (mkdtemp makes the folder 0700).
    for p in [out, *out.rglob("*")]:
        p.chmod(0o755 if p.is_dir() else 0o644)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(f"fixture bank: {len(build().questions)} questions in {write(Path(sys.argv[1]))}")
