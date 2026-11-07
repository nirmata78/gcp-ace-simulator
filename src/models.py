"""Pydantic schemas for the GCP ACE exam simulator.

The question bank is stored as **one JSON file per exam-guide section** under
``data/sections/``, with a generated ``data/register.json`` index carrying a
compact row (id, title, objective, subtopic, summary, tags, fingerprint) for
every question.

Every question is placed on the blueprint of the Associate Cloud Engineer
guide live from 30 June 2026 (``src/blueprint.py``): a section, an objective
and a subtopic from a closed list. A question that fits no subtopic is outside
the exam and cannot be loaded.

Every read and write goes through the models here, so a malformed hand-edit
fails loudly at load time rather than halfway through an exam.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# --------------------------------------------------------------------------
# Taxonomy — the four sections of the June 2026 exam guide
# --------------------------------------------------------------------------
# The code keeps the historical name "domain" for what the guide calls a
# *section*: ``Question.domain`` and ``AnswerRecord.domain`` hold a section
# label such as "Section 3: Ensuring the successful operation of a cloud
# solution". Renaming the field would break every attempt already recorded in
# data/history.json. Everything below is derived from src/blueprint.py, which
# is the only place the exam structure is written down.

from .blueprint import (  # noqa: E402
    OBJECTIVES,
    SECTION_LIST,
    SECTIONS,
    SUBTOPICS,
    is_new_subtopic,
    section_of,
)

DOMAINS: List[str] = [s.label for s in SECTION_LIST]
SECTION_LABELS = DOMAINS

#: Published section weights (20 / 30 / 30 / 20). MUST sum to 1.0.
DOMAIN_WEIGHTS: Dict[str, float] = {s.label: s.weight for s in SECTION_LIST}

#: Short labels for the PDF report and the UI, where the full label is too wide.
DOMAIN_SHORT: Dict[str, str] = {s.label: s.short for s in SECTION_LIST}

#: Slug fragment used when minting new question ids (``ace-s2-004``). Questions
#: authored under the retired five-domain taxonomy keep their ``ace-domN-NNN``
#: ids: an id is a permanent key (history, retrospectives), not a classifier.
DOMAIN_SLUG: Dict[str, str] = {s.label: f"s{s.number}" for s in SECTION_LIST}

#: Filename each section's questions live in, under ``data/sections/``.
DOMAIN_FILE: Dict[str, str] = {s.label: f"section-{s.number}-{s.slug}.json" for s in SECTION_LIST}

#: ``--domain 3`` / ``--section 3`` on the CLI resolves through here.
DOMAIN_BY_NUMBER: Dict[int, str] = {s.number: s.label for s in SECTION_LIST}

#: Where the per-section files live, relative to the data directory.
BANK_DIR = "sections"

#: The retired five-domain labels, mapped to the section that absorbed most of
#: each. Used only to read an attempt recorded before the migration.
LEGACY_DOMAIN_MAP: Dict[str, str] = {
    "Domain 1: Setting up a cloud solution environment": DOMAINS[0],
    "Domain 2: Planning and implementing a cloud solution": DOMAINS[1],
    "Domain 3: Deploying and implementing a cloud solution": DOMAINS[1],
    "Domain 4: Ensuring successful operation of a cloud solution": DOMAINS[2],
    "Domain 5: Configuring access and security": DOMAINS[3],
}

OptionKey = Literal["A", "B", "C", "D"]
OPTION_KEYS: List[str] = ["A", "B", "C", "D"]

EXAM_DURATION_SECONDS = 120 * 60  # 120 minutes
CERTIFYING_QUESTION_COUNT = 50
PASS_THRESHOLD = 0.70  # Google does not publish a cut score; 70% is the community norm.

#: Uniqueness rule (see QuestionBank.duplicate_pairs / option_collisions): stems
#: in one section must overlap below this Jaccard score, and two questions with the
#: same correct answer may not share more than this many identical options.
STEM_OVERLAP_LIMIT = 0.70
#: Removed question ids, relative to the data directory. They are never reused.
RETIRED_FILE = "retired.json"
SHARED_OPTION_LIMIT = 2


# --------------------------------------------------------------------------
# Question bank
# --------------------------------------------------------------------------


class Explanation(BaseModel):
    """Post-answer teaching payload shown in Learning Mode and the PDF report."""

    summary: str = Field(min_length=1)
    option_breakdown: Dict[str, str]
    gcloud_command: str = ""
    doc_ref: str = ""

    @field_validator("option_breakdown")
    @classmethod
    def _all_options_explained(cls, v: Dict[str, str]) -> Dict[str, str]:
        missing = [k for k in OPTION_KEYS if not v.get(k)]
        if missing:
            raise ValueError(f"option_breakdown missing rationale for: {', '.join(missing)}")
        return v


#: Where a question came from. Provenance is tracked so a bank grown by hand
#: and by LLM stays auditable — you can always ask "who wrote this one".
Source = Literal["curated", "official-sample", "user", "llm"]


class Question(BaseModel):
    """One four-option, single-answer scenario question.

    ``title`` and ``summary`` exist for the register: the title is how you refer
    to a question when browsing or adding, and the summary states the single
    idea it tests, so a domain's coverage can be read at a glance without
    opening every scenario.
    """

    id: str = Field(min_length=1)
    title: str = Field(min_length=3, max_length=90)
    domain: str
    objective: str
    subtopic: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    tags: List[str] = Field(default_factory=list)
    source: Source = "curated"
    question: str = Field(min_length=1)
    options: Dict[str, str]
    correct_answer: OptionKey
    explanation: Explanation

    @field_validator("title")
    @classmethod
    def _title_is_a_label_not_a_sentence(cls, v: str) -> str:
        v = v.strip()
        if v.endswith((".", "?")):
            raise ValueError("title should be a short label, not a sentence")
        return v

    @field_validator("tags")
    @classmethod
    def _normalise_tags(cls, v: List[str]) -> List[str]:
        return sorted({t.strip().lower().replace(" ", "-") for t in v if t.strip()})

    @model_validator(mode="before")
    @classmethod
    def _derive_section(cls, data):
        """The section follows from the objective, so it may be omitted."""
        if isinstance(data, dict) and not data.get("domain") and data.get("objective") in OBJECTIVES:
            data = {**data, "domain": section_of(data["objective"]).label}
        return data

    @field_validator("domain")
    @classmethod
    def _known_domain(cls, v: str) -> str:
        if v not in DOMAIN_WEIGHTS:
            raise ValueError(f"unknown domain {v!r}; expected one of {DOMAINS}")
        return v

    @field_validator("objective")
    @classmethod
    def _known_objective(cls, v: str) -> str:
        if v not in OBJECTIVES:
            raise ValueError(f"unknown objective {v!r}; expected one of {sorted(OBJECTIVES)}")
        return v

    @model_validator(mode="after")
    def _consistent_blueprint_placement(self) -> "Question":
        """Section, objective and subtopic must agree with src/blueprint.py.

        The subtopic list is closed: anything the exam guide does not cover has
        no subtopic, and therefore cannot enter the bank.
        """
        if section_of(self.objective).label != self.domain:
            raise ValueError(
                f"objective {self.objective} belongs to {section_of(self.objective).label!r}, "
                f"not {self.domain!r}"
            )
        sub = SUBTOPICS.get(self.subtopic)
        if sub is None:
            raise ValueError(f"unknown subtopic {self.subtopic!r}; see src/blueprint.py SUBTOPICS")
        if sub.objective != self.objective:
            raise ValueError(
                f"subtopic {self.subtopic!r} belongs to objective {sub.objective}, not {self.objective}"
            )
        return self

    @property
    def is_new(self) -> bool:
        """Teaches a bullet the June 2026 guide introduced."""
        return is_new_subtopic(self.subtopic)

    @property
    def bullets(self) -> tuple:
        return SUBTOPICS[self.subtopic].bullets

    @field_validator("options")
    @classmethod
    def _four_distinct_options(cls, v: Dict[str, str]) -> Dict[str, str]:
        missing = [k for k in OPTION_KEYS if not v.get(k)]
        if missing:
            raise ValueError(f"options missing: {', '.join(missing)}")
        extra = sorted(set(v) - set(OPTION_KEYS))
        if extra:
            raise ValueError(f"unexpected option keys: {', '.join(extra)}")
        texts = [v[k].strip().casefold() for k in OPTION_KEYS]
        if len(set(texts)) != len(texts):
            raise ValueError("options must be distinct — duplicate distractor text")
        return v

    @property
    def correct_text(self) -> str:
        return self.options[self.correct_answer]

    @property
    def fingerprint(self) -> str:
        """Stable hash of the normalised stem — catches verbatim re-adds."""
        return hashlib.sha1(_normalise(self.question).encode("utf-8")).hexdigest()[:12]

    def tokens(self) -> set[str]:
        """Content words of the stem, for near-duplicate comparison."""
        return {t for t in _normalise(self.question).split() if t not in _STOPWORDS}

    def similarity(self, other: "Question") -> float:
        """Jaccard overlap of stem content words, 0.0–1.0."""
        a, b = self.tokens(), other.tokens()
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def option_set(self) -> set[str]:
        """The four options in comparison form, for recycled-answer-set detection."""
        return {_normalise(v) for v in self.options.values()}


class QuestionBank(BaseModel):
    """Every question, assembled from the per-domain files under ``data/domains/``."""

    version: int = 2
    generated_at: Optional[str] = None
    questions: List[Question] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_ids_and_titles(self) -> "QuestionBank":
        for field in ("id", "title"):
            seen: set[str] = set()
            dupes: set[str] = set()
            for q in self.questions:
                key = getattr(q, field).casefold()
                (dupes if key in seen else seen).add(key)
            if dupes:
                raise ValueError(f"duplicate question {field}s: {sorted(dupes)[:5]}")
        return self

    def by_domain(self) -> Dict[str, List[Question]]:
        buckets: Dict[str, List[Question]] = {d: [] for d in DOMAINS}
        for q in self.questions:
            buckets[q.domain].append(q)
        return buckets

    def counts(self) -> Dict[str, int]:
        return {d: len(qs) for d, qs in self.by_domain().items()}

    def by_objective(self) -> Dict[str, List[Question]]:
        buckets: Dict[str, List[Question]] = {o: [] for o in OBJECTIVES}
        for q in self.questions:
            buckets[q.objective].append(q)
        return buckets

    def bullet_coverage(self) -> Dict[str, int]:
        """Guide bullet id -> number of questions whose subtopic teaches it."""
        from .blueprint import BULLET_LIST
        out = {b.id: 0 for b in BULLET_LIST}
        for q in self.questions:
            for b in q.bullets:
                out[b] += 1
        return out

    def subtopics(self, domain: Optional[str] = None) -> Dict[str, int]:
        """Subtopic -> question count, optionally scoped to one domain."""
        out: Dict[str, int] = {}
        for q in self.questions:
            if domain is None or q.domain == domain:
                out[q.subtopic] = out.get(q.subtopic, 0) + 1
        return dict(sorted(out.items()))

    def get(self, needle: str) -> Optional[Question]:
        """Look a question up by exact id, then by case-insensitive title match."""
        for q in self.questions:
            if q.id == needle:
                return q
        n = needle.casefold()
        matches = [q for q in self.questions if n in q.title.casefold()]
        return matches[0] if len(matches) == 1 else None

    def find(self, needle: str) -> List[Question]:
        n = needle.casefold()
        return [
            q for q in self.questions
            if n in q.title.casefold() or n in q.question.casefold()
            or n in q.subtopic.casefold() or any(n in t for t in q.tags)
        ]

    def next_id(self, domain: str, retired: Iterable[str] = ()) -> str:
        """Mint a new id in a section (``ace-s2-007``), above every id in use or retired.

        Ids are never reused: attempt history refers to questions by id, so a gap left by a removed
        question must stay a gap (``data/retired.json`` lists them).
        """
        prefix = f"ace-{DOMAIN_SLUG[domain]}-"
        ids = [q.id for q in self.questions] + list(retired)
        used = [int(i[len(prefix):]) for i in ids if i.startswith(prefix) and i[len(prefix):].isdigit()]
        return f"{prefix}{max(used, default=0) + 1:03d}"

    # -- duplicate detection ----------------------------------------------
    #
    # Two questions MAY test the same concept — the exam does, and a second
    # scenario on a weak topic is how it gets learned. What they may not do is
    # repeat each other, which means two things:
    #
    #   * the statement must differ — stem overlap below STEM_OVERLAP_LIMIT;
    #   * the answer options must differ — two questions may not offer the same
    #     answer set (more than SHARED_OPTION_LIMIT identical options) with the
    #     same correct answer, because the second is then answerable from memory
    #     of the first.
    #
    # An enumerated set (the four storage classes, the four hierarchy levels)
    # may recur when the correct answer differs: that is a different question.
    # The rule this replaced forbade the same subtopic + answer + rationale
    # outright, which blocked the repetition-with-variation a thin bullet needs.

    def duplicate_pairs(self, threshold: Optional[float] = None) -> List[tuple[Question, Question, float]]:
        """Question pairs whose stems overlap enough to be restatements.

        Compared within a domain only — two questions in different domains that
        share vocabulary are usually testing genuinely different things.
        """
        threshold = STEM_OVERLAP_LIMIT if threshold is None else threshold
        found: List[tuple[Question, Question, float]] = []
        for group in self.by_domain().values():
            for i, a in enumerate(group):
                for b in group[i + 1:]:
                    score = a.similarity(b)
                    if score >= threshold:
                        found.append((a, b, score))
        return sorted(found, key=lambda r: -r[2])

    def option_collisions(self) -> List[tuple[Question, Question, int]]:
        """Pairs that recycle an answer set: same correct answer, too many identical options."""
        out: List[tuple[Question, Question, int]] = []
        for i, a in enumerate(self.questions):
            for b in self.questions[i + 1:]:
                shared = _recycles(a, b)
                if shared:
                    out.append((a, b, shared))
        return out

    def recycled_options(self, q: "Question") -> Optional[tuple["Question", int]]:
        """An existing question whose answer set ``q`` recycles, if any."""
        for other in self.questions:
            if other.id != q.id:
                shared = _recycles(q, other)
                if shared:
                    return other, shared
        return None

    # -- persistence: one file per domain ---------------------------------

    @classmethod
    def load(cls, root: Path | str) -> "QuestionBank":
        """Assemble the bank from ``<root>/sections/*.json``.

        ``root`` is the data directory. There is no seed script any more: the
        section files are the bank, and a missing directory is a real loss.
        """
        root = Path(root)
        domains_dir = root / BANK_DIR
        if not domains_dir.is_dir():
            raise FileNotFoundError(
                f"{domains_dir} not found — the question bank lives in data/{BANK_DIR}/*.json "
                "and is not generated; restore that directory."
            )

        questions: List[Question] = []
        for domain in DOMAINS:
            path = domains_dir / DOMAIN_FILE[domain]
            if not path.exists():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            for raw in payload.get("questions", []):
                raw.setdefault("domain", domain)
                questions.append(Question.model_validate(raw))
        if not questions:
            raise FileNotFoundError(
                f"no questions found under {domains_dir}."
            )
        return cls(questions=questions)

    @staticmethod
    def retired_ids(root: Path | str) -> List[str]:
        """Ids that were removed from the bank and must never be minted again (``data/retired.json``)."""
        path = Path(root) / RETIRED_FILE
        if not path.exists():
            return []
        return [r["id"] for r in json.loads(path.read_text(encoding="utf-8"))["retired"]]

    def save(self, root: Path) -> None:
        """Write one file per section, plus the register index."""
        domains_dir = root / BANK_DIR
        domains_dir.mkdir(parents=True, exist_ok=True)
        self.generated_at = _now_iso()

        for domain, group in self.by_domain().items():
            group = sorted(group, key=lambda q: q.id)
            payload = {
                "domain": domain,
                "version": self.version,
                "updated_at": self.generated_at,
                "count": len(group),
                "questions": [
                    {k: v for k, v in q.model_dump(mode="json").items() if k != "domain"}
                    for q in group
                ],
            }
            _atomic_write(domains_dir / DOMAIN_FILE[domain], payload)

        _atomic_write(root / "register.json", self.register())

    def register(self) -> dict:
        """The queryable index: one compact row per question, no scenario prose."""
        return {
            "version": self.version,
            "generated_at": self.generated_at or _now_iso(),
            "total": len(self.questions),
            "guide": "Associate Cloud Engineer exam guide, live from 2026-06-30",
            "counts_by_domain": {DOMAIN_SHORT[d]: n for d, n in self.counts().items()},
            "counts_by_objective": {o: len(qs) for o, qs in self.by_objective().items()},
            "subtopics_by_domain": {
                DOMAIN_SHORT[d]: self.subtopics(d) for d in DOMAINS
            },
            "entries": [
                {
                    "id": q.id,
                    "title": q.title,
                    "domain": DOMAIN_SHORT[q.domain],
                    "objective": q.objective,
                    "subtopic": q.subtopic,
                    "new_in_2026": q.is_new,
                    "summary": q.summary,
                    "tags": q.tags,
                    "source": q.source,
                    "fingerprint": q.fingerprint,
                    "file": f"{BANK_DIR}/{DOMAIN_FILE[q.domain]}",
                }
                for q in sorted(self.questions, key=lambda q: q.id)
            ],
        }


# --------------------------------------------------------------------------
# Attempt history
# --------------------------------------------------------------------------


class AnswerRecord(BaseModel):
    """One question as the candidate left it at submission time."""

    question_id: str
    domain: str
    objective: Optional[str] = None
    subtopic: str
    selected: Optional[OptionKey] = None
    correct_answer: OptionKey
    flagged: bool = False
    seconds_spent: float = 0.0

    @field_validator("domain")
    @classmethod
    def _read_legacy_domain(cls, v: str) -> str:
        """An attempt recorded under the retired five-domain taxonomy still loads."""
        return LEGACY_DOMAIN_MAP.get(v, v)

    @property
    def is_correct(self) -> bool:
        return self.selected == self.correct_answer

    @property
    def is_answered(self) -> bool:
        return self.selected is not None


class DomainScore(BaseModel):
    domain: str
    correct: int
    total: int

    @property
    def pct(self) -> float:
        return (self.correct / self.total) if self.total else 0.0


#: Answer-key repairs to the bank, applied once to attempts recorded before them.
#: Twelve questions had the key on a distractor; the fix swapped two option texts so the
#: key letter now names the right answer. An old record's letters still point at the
#: old texts, so the chosen letter is swapped the same way. The correct letter stays, and
#: the attempt is re-scored: a pick that was the right text now counts as correct.
_SWAPPED_KEYS = {
    "ace-dom1-033": ("A", "B"), "ace-dom1-043": ("B", "D"), "ace-dom2-005": ("A", "B"),
    "ace-dom2-007": ("A", "D"), "ace-dom2-021": ("A", "B"), "ace-dom2-043": ("C", "D"),
    "ace-dom2-053": ("A", "B"), "ace-dom2-057": ("B", "C"), "ace-dom3-033": ("A", "B"),
    "ace-dom3-037": ("A", "B"), "ace-dom4-006": ("A", "C"), "ace-dom5-017": ("A", "B"),
}
BANK_KEY_FIXES: Dict[str, Dict[str, tuple]] = {
    "2026-11-06-swapped-keys": _SWAPPED_KEYS,
    # Until 2026-11-07, new attempts were built without bank_fixes, so the repair above also
    # ran on them and flipped answers that were recorded against the already-repaired bank.
    # Swapping again restores those picks; it applies only to attempts finished after the
    # first fix shipped (see BANK_FIX_SINCE).
    "2026-11-07-undo-swap-on-new-attempts": _SWAPPED_KEYS,
}
#: A fix listed here applies only to attempts finished at or after this time (UTC, ISO 8601).
BANK_FIX_SINCE: Dict[str, str] = {
    "2026-11-07-undo-swap-on-new-attempts": "2026-11-06T19:03:01+00:00",
}


def _swap_picks(answers: List[dict], swaps: Dict[str, tuple]) -> None:
    for a in answers:
        pair = swaps.get(a.get("question_id"))
        if pair and a.get("selected") in pair:
            a["selected"] = pair[1] if a["selected"] == pair[0] else pair[0]


def _parse_time(value: str) -> Optional[datetime]:
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


class Attempt(BaseModel):
    """A completed exam, appended to ``data/history.json``."""

    attempt_id: str
    mode: Literal["certifying", "learning"]
    started_at: str
    finished_at: str
    duration_seconds: float
    time_expired: bool = False
    question_count: int
    correct_count: int
    answers: List[AnswerRecord] = Field(default_factory=list)
    report_path: Optional[str] = None
    #: Which BANK_KEY_FIXES this record already reflects, so a repair is never applied twice.
    #: New attempts are recorded against the repaired bank and start with all of them.
    bank_fixes: List[str] = Field(default_factory=lambda: list(BANK_KEY_FIXES))

    @model_validator(mode="before")
    @classmethod
    def _apply_bank_fixes(cls, data):
        """Apply each repair this record does not list yet, once, and record that it did."""
        if not isinstance(data, dict):
            return data
        done = list(data.get("bank_fixes", []))
        pending = [name for name in BANK_KEY_FIXES if name not in done]
        if not pending:
            return data
        data = dict(data)
        answers = [dict(a) if isinstance(a, dict) else a.model_dump() for a in data.get("answers", [])]
        finished = _parse_time(data.get("finished_at", ""))
        for name in pending:
            since = BANK_FIX_SINCE.get(name)
            if since is not None and (finished is None or finished < _parse_time(since)):
                continue  # recorded before this bug existed: nothing to undo
            _swap_picks(answers, BANK_KEY_FIXES[name])
        data["answers"] = answers
        data["correct_count"] = sum(1 for a in answers if a.get("selected") == a.get("correct_answer"))
        data["bank_fixes"] = list(BANK_KEY_FIXES)
        return data

    @property
    def score_pct(self) -> float:
        return (self.correct_count / self.question_count) if self.question_count else 0.0

    @property
    def passed(self) -> bool:
        return self.score_pct >= PASS_THRESHOLD

    def domain_scores(self) -> List[DomainScore]:
        agg: Dict[str, List[int]] = {}
        for a in self.answers:
            bucket = agg.setdefault(a.domain, [0, 0])
            bucket[1] += 1
            if a.is_correct:
                bucket[0] += 1
        return [
            DomainScore(domain=d, correct=agg[d][0], total=agg[d][1])
            for d in DOMAINS
            if d in agg
        ]

    def objective_scores(self) -> List[tuple[str, int, int]]:
        """``(objective, correct, total)`` in guide order, for answers that carry one."""
        agg: Dict[str, List[int]] = {}
        for a in self.answers:
            if a.objective:
                bucket = agg.setdefault(a.objective, [0, 0])
                bucket[1] += 1
                bucket[0] += int(a.is_correct)
        return [(o, agg[o][0], agg[o][1]) for o in OBJECTIVES if o in agg]

    def subtopic_gaps(self, limit: int = 8) -> List[tuple[str, int, int]]:
        """Weakest subtopics as ``(subtopic, correct, total)``, worst first."""
        agg: Dict[str, List[int]] = {}
        for a in self.answers:
            bucket = agg.setdefault(a.subtopic, [0, 0])
            bucket[1] += 1
            if a.is_correct:
                bucket[0] += 1
        rows = [(s, c, t) for s, (c, t) in agg.items() if c < t]
        rows.sort(key=lambda r: (r[1] / r[2], -r[2]))
        return rows[:limit]


class History(BaseModel):
    """The whole of ``data/history.json``."""

    version: int = 1
    attempts: List[Attempt] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "History":
        if not path.exists():
            return cls()
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return cls()
        return cls.model_validate_json(text)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(path)

    def append(self, attempt: Attempt, path: Path) -> None:
        self.attempts.append(attempt)
        self.save(path)

    def rolling_domain_accuracy(self) -> Dict[str, DomainScore]:
        """Domain telemetry across every attempt on record."""
        agg: Dict[str, List[int]] = {d: [0, 0] for d in DOMAINS}
        for att in self.attempts:
            for a in att.answers:
                if a.domain in agg:
                    agg[a.domain][1] += 1
                    if a.is_correct:
                        agg[a.domain][0] += 1
        return {
            d: DomainScore(domain=d, correct=c, total=t)
            for d, (c, t) in agg.items()
            if t
        }


def _recycles(a: Question, b: Question) -> int:
    """Identical options shared by ``a`` and ``b`` when that breaks the rule, else 0."""
    if _normalise(a.correct_text) != _normalise(b.correct_text):
        return 0
    shared = len(a.option_set() & b.option_set())
    return shared if shared > SHARED_OPTION_LIMIT else 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_write(path: Path, payload: dict) -> None:
    """Write via a temp file and rename, so an interrupted write cannot corrupt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


_PUNCT = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")

#: Deliberately small. Scenario prose is formulaic ("you want to", "what should
#: you do"), so stripping only these keeps the signal that distinguishes stems.
_STOPWORDS = frozenset("""
a an the and or of to in on for with by at from as is are was were be been being
you your yours we our they their it its this that these those what which who whom
should would could want wants wanted need needs needed must have has had do does
did will can may might not no nor but if then than so such there here about into
over under between each any all some most more less least own same other another
company organisation organization team engineer cloud google gcp platform want
""".split())


def _normalise(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — the dedupe basis."""
    return _WS.sub(" ", _PUNCT.sub(" ", text.casefold())).strip()
