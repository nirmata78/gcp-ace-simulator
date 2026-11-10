"""Growing the bank in a controlled way: the plan, the gates and the evidence (the ``/expand`` skill).

Three jobs, each deterministic so that the model writing the questions decides as little as possible:

``plan``   how many questions go where. A run adds ``N`` questions; the plan splits them over sections, objectives and
           subtopics, decides which are multiple-select or cross-domain, and fixes every key letter in advance.
``vet``    whether a candidate meets the machine-checkable parts of ``docs/question-standard.md``, stricter than
           ``question_lint`` is for the existing bank, and whether it is new against the bank and its own batch.
``page``   the documentation page behind a ``doc_ref``, as plain text, so that a key can be tied to a sentence that
           is really on the page.

No Streamlit imports. Only ``fetch_page`` touches the network.
"""

from __future__ import annotations

import hashlib
import html
import itertools
import math
import random
import re
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from src.blueprint import (
    BULLETS,
    OBJECTIVE_LIST,
    OBJECTIVES,
    SECTION_LIST,
    SECTIONS,
    SUBTOPIC_LIST,
    objective_weights,
    subtopics_in,
)
from src.models import OPTION_KEYS, Question, QuestionBank, _normalise, _recycles, _STOPWORDS
from src.question_lint import DOC_HOSTS, lint_question

Finding = Tuple[str, str, str]

BALANCES = ("exam", "batch", "current")
#: Five of a 50-question exam are cross-domain, so a tenth of every run is.
CROSS_SHARE = 0.10
MULTI_SHARE = 0.10
#: One cross-domain slot in three is also multiple-select.
CROSS_MULTI_EVERY = 3
BATCH_SIZE = 8
MULTI_KEYS = [",".join(c) for c in itertools.combinations("ABCDE", 2)]

#: A new stem must be further from every other stem than the bank's own closest pairs are (99% of the bank's
#: questions have no neighbour above 0.36).
NOVEL_STEM_LIMIT = 0.45
NOVEL_STEM_WARN = 0.33
SAME_IDEA_LIMIT = 0.60
STEM_WORDS = (25, 90)
TITLE_LIMIT = 60
EVIDENCE_MIN_WORDS = 8
BATCH_LONGEST_KEY_LIMIT = 0.40
#: Lint findings that are a reviewer's prompt on an old question and a defect on a new one.
PROMOTED = {"length-tell", "cli-syntax", "no-command", "doc-ref", "vague-superlative"}
#: Keys a candidate carries for the pipeline; they are not part of the stored question.
HELPER_KEYS = ("slot", "evidence", "blind", "skip")


# --------------------------------------------------------------------------
# The plan
# --------------------------------------------------------------------------


def parse_grow(text: str, total: int) -> int:
    """``"10%"`` of the bank, or a plain count such as ``"25"``. At least one question."""
    t = text.strip()
    try:
        n = total * float(t[:-1]) / 100 if t.endswith("%") else int(t)
    except ValueError:
        raise ValueError(f"cannot read {text!r}: give a percentage such as 10% or a count such as 25") from None
    if n <= 0:
        raise ValueError("the bank can only grow: give a positive number")
    return max(1, math.floor(n + 0.5))


def apportion(n: int, weights: Dict[str, float]) -> Dict[str, int]:
    """Split ``n`` in proportion to ``weights`` by largest remainder; the parts always sum to ``n``."""
    keys = list(weights)
    total = sum(weights.values())
    shares = {k: (n * weights[k] / total if total else n / len(keys)) for k in keys}
    out = {k: int(shares[k]) for k in keys}
    by_remainder = sorted(keys, key=lambda k: (-(shares[k] - out[k]), keys.index(k)))
    for k in by_remainder[: n - sum(out.values())]:
        out[k] += 1
    return out


def _split(n: int, have: Dict[str, int], weight: Dict[str, float], balance: str) -> Dict[str, int]:
    """``n`` new questions over the keys of ``have``.

    ``exam``     in proportion to how far each key is below its weight after the run, so the bank converges on
                 the published weights and nothing overshoots;
    ``batch``    in proportion to the weights, whatever the bank looks like;
    ``current``  in proportion to what is there, so every key grows by the same percentage.
    """
    if balance == "current" and sum(have.values()):
        return apportion(n, {k: float(v) for k, v in have.items()})
    if balance == "exam":
        after = sum(have.values()) + n
        wsum = sum(weight.values())
        short = {k: max(0.0, weight[k] / wsum * after - have[k]) for k in have}
        if any(short.values()):
            return apportion(n, short)
    return apportion(n, weight)


def _spaced(count: int, total: int) -> List[int]:
    """``count`` positions spread evenly over ``range(total)``."""
    count = min(count, total)
    return [int((i + 0.5) * total / count) for i in range(count)]


def plan(bank: QuestionBank, grow: int, *, balance: str = "exam", sections: Optional[Iterable[int]] = None,
         objective: Optional[str] = None, cross_share: float = CROSS_SHARE, multi_share: float = MULTI_SHARE,
         batch_size: int = BATCH_SIZE, request: str = "") -> dict:
    """The slots of one run. Deterministic for a given bank and arguments."""
    if balance not in BALANCES:
        raise ValueError(f"balance must be one of {', '.join(BALANCES)}")
    obj_w = objective_weights()
    have_obj = Counter(q.objective for q in bank.questions)
    have_sub = Counter(q.subtopic for q in bank.questions)

    # Sections, then the objectives inside each one, then the thinnest subtopics inside each objective.
    wanted = sorted(set(sections)) if sections else [s.number for s in SECTION_LIST]
    if objective:
        per_obj = {objective: grow}
    else:
        have_sec = {str(n): sum(have_obj[o.id] for o in OBJECTIVE_LIST if o.section == n) for n in wanted}
        per_sec = _split(grow, have_sec, {str(n): SECTIONS[n].weight for n in wanted}, balance)
        per_obj = {}
        for n in wanted:
            ids = [o.id for o in OBJECTIVE_LIST if o.section == n]
            per_obj.update(_split(per_sec[str(n)], {i: have_obj[i] for i in ids}, {i: obj_w[i] for i in ids}, balance))

    slots: List[dict] = []
    for obj in OBJECTIVE_LIST:
        subs = subtopics_in(obj.id)
        filled = {s.name: have_sub[s.name] for s in subs}
        picks: Counter = Counter()
        for _ in range(per_obj.get(obj.id, 0)):
            thin = min(subs, key=lambda s: (filled[s.name] / max(1, len(s.bullets)), subs.index(s)))
            filled[thin.name] += 1
            picks[thin.name] += 1
        for s in subs:
            for _ in range(picks[s.name]):
                slots.append({"section": obj.section, "objective": obj.id, "subtopic": s.name,
                              "bullets": list(s.bullets)})

    # Which slots are cross-domain and which are multiple-select.
    total = len(slots)
    cross = set(_spaced(math.floor(total * cross_share + 0.5), total))
    multi = {i for n, i in enumerate(sorted(cross)) if n % CROSS_MULTI_EVERY == 1}
    rest = [i for i in range(total) if i not in cross]
    more = max(0, math.floor(total * multi_share + 0.5) - len(multi))
    multi |= {rest[p] for p in _spaced(more, len(rest))} if rest else set()

    # Keys are fixed here, so the bank's letter spread does not depend on a model's habits.
    rng = random.Random(len(bank.questions) * 1000 + total)
    single_use = Counter(q.correct_answer for q in bank.questions if not q.is_multi)
    multi_use = Counter(q.correct_answer for q in bank.questions if q.is_multi)
    singles, multis = [], []
    for _ in range(total - len(multi)):
        k = min(OPTION_KEYS, key=lambda x: (single_use[x], x))
        single_use[k] += 1
        singles.append(k)
    for _ in range(len(multi)):
        k = min(MULTI_KEYS, key=lambda x: (multi_use[x], x))
        multi_use[k] += 1
        multis.append(k)
    rng.shuffle(singles)
    rng.shuffle(multis)

    # A cross-domain slot gets a suggested partner objective in another section.
    pairs = Counter((q.objective, o) for q in bank.questions for o in q.also_tests)
    partner_use = Counter(o for q in bank.questions for o in q.also_tests)
    for i, s in enumerate(slots):
        is_multi = i in multi
        s.update(slot=i + 1, batch=i // batch_size + 1, kind="multi" if is_multi else "single",
                 options=5 if is_multi else 4, choose=2 if is_multi else 1,
                 key=(multis if is_multi else singles).pop(), cross=i in cross, pair_with=None, status="open")
        if s["cross"]:
            others = [o.id for o in OBJECTIVE_LIST if o.section != s["section"]]
            # A pairing the bank already has is known to make a natural scenario; prefer the rarest of those.
            known = [o for o in others if pairs[(s["objective"], o)]] or others
            mate = min(known, key=lambda o: (pairs[(s["objective"], o)], partner_use[o], o))
            pairs[(s["objective"], mate)] += 1
            partner_use[mate] += 1
            s["pair_with"] = mate

    order = ("slot", "batch", "status", "section", "objective", "subtopic", "bullets", "kind", "options", "choose",
             "key", "cross", "pair_with")
    return {
        "created": date.today().isoformat(),
        "request": request or str(grow),
        "balance": balance,
        "bank_before": len(bank.questions),
        "grow": total,
        "slots": [{k: s[k] for k in order} for s in slots],
    }


def plan_summary(bank: QuestionBank, p: dict) -> List[str]:
    """The plan as a few lines a person can check: where the bank stands and where the run takes it."""
    slots = p["slots"]
    before, after = p["bank_before"], p["bank_before"] + len(slots)
    have = Counter(OBJECTIVES[q.objective].section for q in bank.questions)
    add = Counter(s["section"] for s in slots)
    out = [f"Plan: {before} + {len(slots)} = {after} questions  (request {p['request']}, balance {p['balance']})", ""]
    for sec in SECTION_LIST:
        h, a = have[sec.number], add[sec.number]
        out.append(f"  {sec.short:<18} {h:>4} ({h / before:5.1%})  +{a:<3} -> {h + a:>4} ({(h + a) / after:5.1%})"
                   f"   exam weight {sec.weight:.0%}")
    per_obj = Counter(s["objective"] for s in slots)
    out += ["", "  By objective: " + "  ".join(f"{o} +{n}" for o, n in sorted(per_obj.items()))]
    n_multi = sum(s["kind"] == "multi" for s in slots)
    n_cross = sum(s["cross"] for s in slots)
    both = sum(s["cross"] and s["kind"] == "multi" for s in slots)
    out.append(f"  Mix: {len(slots) - n_multi} single-answer, {n_multi} multiple-select; "
               f"{n_cross} cross-domain ({both} of them multiple-select)")
    out.append(f"  Batches: {max((s['batch'] for s in slots), default=0)}")
    return out


def open_batch(p: dict) -> Optional[int]:
    """The first batch that still has an open slot."""
    return min((s["batch"] for s in p["slots"] if s["status"] == "open"), default=None)


def describe_slots(bank: QuestionBank, p: dict, batch: int) -> List[str]:
    """What to write for one batch, and what the bank already asks on those subtopics."""
    slots = [s for s in p["slots"] if s["batch"] == batch]
    out = [f"Batch {batch}: {len(slots)} slot(s)", ""]
    for s in slots:
        shape = "single answer, options A-D" if s["kind"] == "single" else "multiple select, options A-E, (Choose two.)"
        out.append(f"Slot {s['slot']} [{s['status']}]  objective {s['objective']} {OBJECTIVES[s['objective']].title}")
        out.append(f"  subtopic: {s['subtopic']}")
        for b in s["bullets"]:
            out.append(f"  guide bullet {b}: {BULLETS[b].text}")
        out.append(f"  form: {shape}; correct_answer must be \"{s['key']}\"")
        if s["cross"]:
            mate = s["pair_with"]
            out.append(f"  cross-domain: set also_tests; suggested partner {mate} {OBJECTIVES[mate].title} "
                       "(any objective in another section will do)")
        out.append("")
    for name in dict.fromkeys(s["subtopic"] for s in slots):
        mine = [q for q in bank.questions if q.subtopic == name]
        out.append(f"Already in the bank on \"{name}\" ({len(mine)}): write a different decision or a different "
                   "deciding constraint")
        for q in sorted(mine, key=lambda q: q.id):
            out.append(f"  {q.id}  {q.title} | tests: {q.summary} | key: {q.correct_text}")
        out.append("")
    return out


def mark(p: dict, slot: int, status: str, **extra) -> None:
    for s in p["slots"]:
        if s["slot"] == slot:
            s.update(status=status, **extra)
            return
    raise KeyError(f"no slot {slot} in the plan")


# --------------------------------------------------------------------------
# Documentation pages
# --------------------------------------------------------------------------

_DROP = re.compile(r"(?is)<(script|style|nav|header|footer|svg|devsite-toc|devsite-feedback)\b.*?</\1\s*>")
_BLOCK = re.compile(r"(?i)</?(p|div|li|ul|ol|h[1-6]|tr|table|section|article|pre|br|aside|devsite-[a-z-]+)\b[^>]*>")
_TAG = re.compile(r"<[^>]+>")
_PREVIEW = re.compile(r"Pre-GA Offerings Terms|\(Preview\)|\bis in Preview\b|\bPreview (feature|release|stage)\b|"
                      r"\bin (public |private )?preview\b", re.I)
USER_AGENT = "Mozilla/5.0 (compatible; docs-check)"


def page_text(raw_html: str) -> str:
    """The article of a documentation page as plain text, one block per line."""
    body = raw_html
    start = body.find("devsite-article-body")
    if start >= 0:
        body = body[body.rfind("<", 0, start):]
    body = _BLOCK.sub("\n", _DROP.sub(" ", body).replace("\n", " "))
    lines = (re.sub(r"[ \t\r\f\v\xa0]+", " ", html.unescape(_TAG.sub("", ln))).strip() for ln in body.split("\n"))
    return "\n".join(ln for ln in lines if ln)


def fetch_page(url: str, cache_dir: Optional[Path] = None, timeout: float = 25.0) -> str:
    """Plain text of the page at ``url``, cached per URL so a run fetches each page once."""
    if urlparse(url).scheme != "https":
        raise ValueError(f"not an https URL: {url}")
    cached = cache_dir / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".txt") if cache_dir else None
    if cached and cached.exists():
        return cached.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (https only, checked above)
        text = page_text(resp.read().decode("utf-8", "replace"))
    if cached:
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(text, encoding="utf-8")
    return text


def _flat(text: str) -> str:
    """Letters and digits only, so markup, quotes and spacing cannot hide or fake a match."""
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def has_quote(page: str, quote: str) -> bool:
    """True when ``quote`` appears on the page word for word."""
    q = _flat(quote)
    return bool(q) and f" {q} " in f" {_flat(page)} "


def preview_notes(page: str, width: int = 110) -> List[str]:
    """Places where the page mentions a Preview launch stage, each with some context."""
    one = re.sub(r"\s+", " ", page)
    out = []
    for m in _PREVIEW.finditer(one):
        out.append(one[max(0, m.start() - width): m.end() + width].strip())
        if len(out) == 3:
            break
    return out


def find_in_page(page: str, terms: Iterable[str]) -> List[str]:
    """The lines of a page that mention any of ``terms``, each with the line before and after."""
    lines = page.split("\n")
    wanted = [t.casefold() for t in terms]
    keep = sorted({j for i, ln in enumerate(lines) if any(t in ln.casefold() for t in wanted)
                   for j in (i - 1, i, i + 1) if 0 <= j < len(lines)})
    return [lines[j] for j in keep]


# --------------------------------------------------------------------------
# Vetting candidates
# --------------------------------------------------------------------------


def _label(raw: dict, index: int) -> str:
    return f"slot {raw['slot']}" if "slot" in raw else f"item {index + 1}"


def _words(text: str) -> set:
    return {t for t in _normalise(text).split() if t not in _STOPWORDS}


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def blind_hash(q: Question) -> str:
    """Fingerprint of what a blind solver sees. Any edit to the stem or an option changes it."""
    seen = q.question + "".join(f"|{k}:{q.options[k]}" for k in q.keys)
    return hashlib.sha1(_normalise(seen).encode()).hexdigest()[:12]


def parse_candidate(raw: dict, index: int = 0) -> Question:
    """The question in a candidate, without the pipeline's helper keys."""
    body = {k: v for k, v in raw.items() if k not in HELPER_KEYS}
    body.setdefault("id", f"pending-{raw.get('slot', index + 1)}")
    body.setdefault("source", "curated")
    return Question.model_validate(body)


def blind_sheet(raws: List[dict]) -> str:
    """Stems and options only: no key, title, summary or rationale."""
    out = []
    for i, raw in enumerate(raws):
        if "skip" in raw:
            continue
        q = parse_candidate(raw, i)
        out.append(f"Question {raw.get('slot', i + 1)}\n{q.question}")
        out += [f"  {k}. {q.options[k]}" for k in q.keys]
        out.append("")
    return "\n".join(out)


def record_blind(raws: List[dict], answers: Dict[str, str]) -> List[Tuple[str, str, str, bool]]:
    """Store each blind answer on its candidate; returns ``(label, key, answer, agrees)`` rows."""
    rows = []
    for i, raw in enumerate(raws):
        if "skip" in raw:
            continue
        name = str(raw.get("slot", i + 1))
        if name not in answers:
            continue
        q = parse_candidate(raw, i)
        given = ",".join(sorted(re.findall(r"[A-E]", answers[name].upper())))
        agrees = given == q.correct_answer
        raw["blind"] = {"answer": given, "agrees": agrees, "hash": blind_hash(q)}
        rows.append((_label(raw, i), q.correct_answer, given, agrees))
    return rows


def vet(bank: QuestionBank, raws: List[dict], *, plan: Optional[dict] = None,
        pages: Optional[Callable[[str], str]] = None, final: bool = False,
        ) -> Tuple[Dict[str, List[Finding]], Dict[str, Question]]:
    """Findings for a batch of candidates, by label, and the questions that parsed.

    ``plan``   also check each candidate against its slot.
    ``pages``  a function from URL to page text: also check that the evidence quote is on the ``doc_ref`` page.
    ``final``  also require a blind-solve record that agrees with the key and matches the current wording.
    """
    found: Dict[str, List[Finding]] = {}
    parsed: Dict[str, Question] = {}
    slots = {s["slot"]: s for s in plan["slots"]} if plan else {}
    titles = {q.title.casefold() for q in bank.questions}
    rationales = {_normalise(q.explanation.option_breakdown[k])
                  for q in bank.questions for k in q.keys if k not in q.correct_keys}
    peers: List[Question] = list(bank.questions)
    seen_slots: set = set()

    for i, raw in enumerate(raws):
        label = _label(raw, i)
        out = found.setdefault(label, [])
        slot = slots.get(raw.get("slot"))
        if plan is not None:
            if slot is None:
                out.append(("error", "slot", "no such slot in the plan: every candidate carries its slot number"))
            elif slot["status"] != "open":
                out.append(("error", "slot", f"slot {slot['slot']} is already {slot['status']}"))
            elif slot["slot"] in seen_slots:
                out.append(("error", "slot", f"slot {slot['slot']} appears twice in this file"))
            seen_slots.add(raw.get("slot"))
        if "skip" in raw:
            if not str(raw["skip"]).strip():
                out.append(("error", "skip", "a skipped slot needs a reason"))
            continue
        try:
            q = parse_candidate(raw, i)
        except Exception as exc:  # pydantic's message names the field
            out.append(("error", "schema", " ".join(str(exc).split())))
            continue
        parsed[label] = q

        for sev, code, msg in lint_question(q):
            if code == "stem-length":
                continue
            out.append(("error" if code in PROMOTED else sev, code, msg))
        n = len(q.question.split())
        if not STEM_WORDS[0] <= n <= STEM_WORDS[1]:
            out.append(("error", "stem-length", f"the stem is {n} words; a new stem has {STEM_WORDS[0]}-{STEM_WORDS[1]}"))
        if q.source != "curated":
            out.append(("error", "source", "a new question has source 'curated' (AC7)"))
        if urlparse(q.explanation.doc_ref).scheme != "https":
            out.append(("error", "doc-ref", "doc_ref must be an https link to official documentation (AC5)"))
        if len(q.title) > TITLE_LIMIT:
            out.append(("error", "title", f"the title is {len(q.title)} characters; keep it under {TITLE_LIMIT}"))
        if q.title.casefold() in titles:
            out.append(("error", "title", "another question already has this title"))
        titles.add(q.title.casefold())

        if slot:
            for field, want, got in (("objective", slot["objective"], q.objective),
                                     ("subtopic", slot["subtopic"], q.subtopic),
                                     ("correct_answer", slot["key"], q.correct_answer),
                                     ("number of options", slot["options"], len(q.options))):
                if want != got:
                    out.append(("error", "slot", f"{field} is {got!r}; slot {slot['slot']} needs {want!r}"))
            if slot["cross"] != q.is_cross_domain:
                out.append(("error", "slot", "this slot is cross-domain: set also_tests" if slot["cross"]
                            else "this slot is not cross-domain: remove also_tests"))

        # New against the bank and against the candidates before it.
        near = max(peers, key=q.similarity)
        score = q.similarity(near)
        if score >= NOVEL_STEM_LIMIT:
            out.append(("error", "stem-overlap", f"{score:.0%} of the stem's words match {near.id} ({near.title}); "
                        "write a different scenario, not different wording (AC7)"))
        elif score >= NOVEL_STEM_WARN:
            out.append(("warning", "stem-overlap", f"{score:.0%} stem overlap with {near.id} ({near.title})"))
        for other in peers:
            if _recycles(q, other):
                out.append(("error", "recycled-options", f"same correct option and more than two identical options "
                            f"as {other.id} (AC7)"))
                break
        twins = [o for o in peers if o.subtopic == q.subtopic and _normalise(o.correct_text) == _normalise(q.correct_text)]
        if twins:
            out.append(("warning", "same-decision", f"{twins[0].id} has the same correct option; allowed only if a "
                        "different fact in the stem decides it (AC7)"))
        ideas = [o for o in peers if o.subtopic == q.subtopic
                 and _jaccard(_words(o.summary), _words(q.summary)) >= SAME_IDEA_LIMIT]
        if ideas:
            out.append(("warning", "same-idea", f"the summary reads like {ideas[0].id}'s: {ideas[0].summary}"))
        copied = [k for k in q.keys if k not in q.correct_keys
                  and _normalise(q.explanation.option_breakdown[k]) in rationales]
        if copied:
            out.append(("error", "copied-rationale", f"rationale for {', '.join(copied)} is copied from another "
                        "question (AC5)"))
        rationales.update(_normalise(q.explanation.option_breakdown[k]) for k in q.keys if k not in q.correct_keys)
        peers.append(q)

        # Evidence: a sentence from the doc_ref page that proves the key.
        quote = str(raw.get("evidence", "")).strip()
        if len(quote.split()) < EVIDENCE_MIN_WORDS:
            out.append(("error", "evidence", f"give 'evidence': a sentence of {EVIDENCE_MIN_WORDS}+ words copied from "
                        "the doc_ref page that proves the key (AC5)"))
        elif pages is not None and urlparse(q.explanation.doc_ref).hostname in DOC_HOSTS:
            try:
                page = pages(q.explanation.doc_ref)
            except Exception as exc:
                out.append(("error", "evidence", f"cannot read doc_ref: {exc}"))
            else:
                if not has_quote(page, quote):
                    out.append(("error", "evidence", "the evidence quote is not on the doc_ref page word for word"))
                for note in preview_notes(page):
                    out.append(("warning", "preview", f"the page mentions Preview; the key must not depend on it "
                                f"(AC7): …{note}…"))

        if final:
            blind = raw.get("blind") or {}
            if blind.get("hash") != blind_hash(q):
                out.append(("error", "blind", "no blind-solve record for this wording: run kb.py blind again"))
            elif not blind.get("agrees"):
                out.append(("error", "blind", f"the blind solver answered {blind.get('answer') or 'nothing'}, "
                            f"the key is {q.correct_answer} (AC4)"))

    singles = [q for q in parsed.values() if not q.is_multi]
    if len(singles) >= 5:
        longest = sum(max(q.keys, key=lambda k: len(q.options[k])) == q.correct_answer for q in singles)
        if longest / len(singles) > BATCH_LONGEST_KEY_LIMIT:
            found.setdefault("batch", []).append(
                ("error", "length-tell", f"the key is the longest option in {longest} of {len(singles)} single-answer "
                 "questions; lengthen distractors or tighten keys (AC3)"))
    return {k: v for k, v in found.items() if v}, parsed


def ledger_entry(q: Question, raw: dict, today: Optional[str] = None) -> dict:
    """The review record of a question added by a run."""
    blind = raw.get("blind") or {}
    return {
        "id": q.id,
        "verdict": "new",
        "ac": {f"AC{n}": "pass" for n in range(1, 8)},
        "notes": f"Added by /expand on {today or date.today().isoformat()}, written from the guide bullet and the "
                 "documentation page in doc_ref.",
        "replacement_id": None,
        "evidence": {"doc_ref": q.explanation.doc_ref, "quote": str(raw.get("evidence", "")).strip()},
        "blind_solve": {"answer": blind.get("answer"), "agrees": bool(blind.get("agrees"))},
    }
