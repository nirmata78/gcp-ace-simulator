#!/usr/bin/env python3
"""Query and grow the question bank.

The bank lives as one JSON file per exam-guide section under ``data/sections/``,
indexed by a generated ``data/register.json``. Every question sits on the
blueprint of the guide live from 30 June 2026 (``src/blueprint.py``): a section,
an objective (1.1 … 4.2) and a subtopic that names the guide bullets it teaches.

    kb.py blueprint                 every guide bullet and how many questions teach it
    kb.py topics                    objectives and subtopics with counts
    kb.py topics --section 2        just Section 2
    kb.py list --objective 2.3      every question title for objective 2.3
    kb.py list --new                only bullets the June 2026 guide introduced
    kb.py list --tag iam            filter by tag
    kb.py show ace-s2-004           one question in full
    kb.py show "resource hierarchy" ...also matches on title
    kb.py search "load balancer"    free-text across titles, stems, tags
    kb.py check                     validate + report restated stems and recycled answer sets
    kb.py add --topic "Cloud NAT"   author a new question with the LLM
    kb.py add --file question.json  add a hand-written question
    kb.py stats                     bank health at a glance

Growing the bank by a planned amount (the /expand skill; docs/question-standard.md, "Growing the bank"):

    kb.py plan 10% --out build/expand/RUN/plan.json   where the new questions go, with every key fixed
    kb.py slots PLAN                what the next batch must contain, and what the bank already asks there
    kb.py doc URL --find "term"     a documentation page as plain text, to quote evidence from
    kb.py vet FILE --plan PLAN      check candidates against the standard, the bank and their slots
    kb.py blind FILE                the candidates without keys, for a blind solver; --answers records the result
    kb.py accept FILE --plan PLAN --ledger LEDGER     add a vetted, blind-solved batch

Every write path re-validates the whole bank and rebuilds the register, so the
index can never drift from the questions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.blueprint import (  # noqa: E402
    BULLET_LIST,
    OBJECTIVES,
    SECTION_LIST,
    SUBTOPIC_LIST,
    bullets_in,
    objectives_in,
    subtopics_in,
)
from src.models import (  # noqa: E402
    DOMAIN_BY_NUMBER,
    DOMAIN_SHORT,
    DOMAINS,
    OPTION_KEYS,
    SHARED_OPTION_LIMIT,
    STEM_OVERLAP_LIMIT,
    Question,
    QuestionBank,
)

DATA_DIR = ROOT / "data"
DEFAULT_MODEL = "claude-sonnet-5-5"

# ANSI, disabled when not a TTY so piping to a file stays clean.
_TTY = sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text


def bold(t: str) -> str:
    return _c(t, "1")


def dim(t: str) -> str:
    return _c(t, "2")


def green(t: str) -> str:
    return _c(t, "32")


def red(t: str) -> str:
    return _c(t, "31")


def yellow(t: str) -> str:
    return _c(t, "33")


def load(data_dir: Path) -> QuestionBank:
    try:
        return QuestionBank.load(data_dir)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


def resolve_domain(value: Optional[str]) -> Optional[str]:
    """Accept ``3``, ``s3`` or a substring of the section title."""
    if not value:
        return None
    if value.isdigit() and int(value) in DOMAIN_BY_NUMBER:
        return DOMAIN_BY_NUMBER[int(value)]
    v = value.casefold().removeprefix("section").removeprefix("s").strip()
    if v.isdigit() and int(v) in DOMAIN_BY_NUMBER:
        return DOMAIN_BY_NUMBER[int(v)]
    for d in DOMAINS:
        if value.casefold() in d.casefold():
            return d
    print(f"[ERROR] unknown section {value!r}; use 1-4 or a title fragment", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------
# Read commands
# --------------------------------------------------------------------------


def cmd_topics(args) -> int:
    bank = load(args.data_dir)
    domain = resolve_domain(args.domain)
    domains = [domain] if domain else DOMAINS

    counts = bank.subtopics()
    width = max(len(s.name) for s in SUBTOPIC_LIST)
    for sec in SECTION_LIST:
        if sec.label not in domains:
            continue
        print(f"\n{bold(sec.short)}  {dim(sec.label)}  —  {bank.counts()[sec.label]} question(s)")
        for obj in objectives_in(sec.number):
            print(f"  {bold(obj.id)} {obj.title}")
            for st in subtopics_in(obj.id):
                n = counts.get(st.name, 0)
                bar = "▪" * min(n, 30)
                warn = red("  ← none") if n == 0 else ""
                print(f"     {st.name.ljust(width)}  {n:>3}  {dim(bar)}{warn}")
    print()
    return 0


def cmd_blueprint(args) -> int:
    """Every bullet of the exam guide, with the number of questions teaching it."""
    bank = load(args.data_dir)
    cov = bank.bullet_coverage()
    weak = 0
    for sec in SECTION_LIST:
        print(f"\n{bold(sec.label)}  {dim(f'~{sec.weight:.0%}')}")
        for obj in objectives_in(sec.number):
            print(f"  {bold(obj.id)} {obj.title}")
            for b in bullets_in(obj.id):
                n = cov[b.id]
                star = yellow("★") if b.new else " "
                colour = red if n == 0 else (yellow if n < args.min else (lambda t: t))
                if n < args.min:
                    weak += 1
                text = b.text if len(b.text) <= 78 else b.text[:77] + "…"
                print(f"   {star} {dim(b.id.ljust(6))} {colour(f'{n:>3}')}  {text}")
    total_new = sum(1 for b in BULLET_LIST if b.new)
    print(f"\n{dim(f'★ = introduced by the June 2026 guide ({total_new} bullets).')}")
    if weak:
        print(yellow(f"{weak} bullet(s) with fewer than {args.min} questions.\n"))
        return 1 if args.strict else 0
    print(green(f"Every bullet has at least {args.min} questions.\n"))
    return 0


def cmd_list(args) -> int:
    bank = load(args.data_dir)
    domain = resolve_domain(args.domain)

    rows = [
        q for q in sorted(bank.questions, key=lambda q: q.id)
        if (domain is None or q.domain == domain)
        and (args.objective is None or q.objective == args.objective)
        and (not args.new or q.is_new)
        and (args.subtopic is None or args.subtopic.casefold() in q.subtopic.casefold())
        and (args.tag is None or args.tag.casefold() in q.tags)
        and (args.source is None or q.source == args.source)
    ]
    if not rows:
        print(dim("No questions match that filter."))
        return 0

    if args.json:
        print(json.dumps(
            [{"id": q.id, "title": q.title, "domain": q.domain, "objective": q.objective,
              "subtopic": q.subtopic,
              "summary": q.summary, "tags": q.tags, "source": q.source} for q in rows],
            indent=2, ensure_ascii=False,
        ))
        return 0

    id_w = max(len(q.id) for q in rows)
    title_w = min(46, max(len(q.title) for q in rows))
    current = None
    for q in rows:
        if q.domain != current:
            current = q.domain
            print(f"\n{bold(DOMAIN_SHORT[q.domain])}")
        title = q.title if len(q.title) <= title_w else q.title[: title_w - 1] + "…"
        star = yellow("★") if q.is_new else " "
        line = f"  {dim(q.id.ljust(id_w))} {star} {title.ljust(title_w)}  {dim(q.objective + ' ' + q.subtopic)}"
        print(line)
        if args.verbose:
            print(f"  {' ' * id_w}  {dim(q.summary)}")
    print(f"\n{len(rows)} question(s)\n")
    return 0


def cmd_show(args) -> int:
    bank = load(args.data_dir)
    q = bank.get(args.needle)
    if q is None:
        matches = bank.find(args.needle)
        if not matches:
            print(f"[ERROR] nothing matches {args.needle!r}", file=sys.stderr)
            return 1
        if len(matches) > 1:
            print(f"{len(matches)} matches — narrow it down or use an id:\n")
            for m in matches[:20]:
                print(f"  {dim(m.id)}  {m.title}")
            return 1
        q = matches[0]

    if args.json:
        print(json.dumps(q.model_dump(mode="json"), indent=2, ensure_ascii=False))
        return 0

    print(f"\n{bold(q.title)}")
    new = "  ·  ★ new in June 2026 guide" if q.is_new else ""
    print(dim(f"{q.id}  ·  {DOMAIN_SHORT[q.domain]}  ·  {q.objective} {OBJECTIVES[q.objective].title}"
              f"  ·  {q.subtopic}  ·  source: {q.source}{new}"))
    if q.tags:
        print(dim("tags: " + ", ".join(q.tags)))
    print(f"\n{textwrap.fill(q.question, 96)}\n")
    for k in q.keys:
        marker = green(" ✓") if k in q.correct_keys else "  "
        body = textwrap.fill(f"{k}. {q.options[k]}", 92, subsequent_indent="     ")
        print(f"{marker} {body}")
    print(f"\n{bold('Why')}  {textwrap.fill(q.explanation.summary, 90, subsequent_indent='     ')}")
    print(f"\n{bold('Option analysis')}")
    for k in q.keys:
        print(textwrap.fill(f"  {k}. {q.explanation.option_breakdown[k]}", 96,
                            subsequent_indent="     "))
    if q.explanation.gcloud_command:
        print(f"\n{bold('Command')}")
        for line in q.explanation.gcloud_command.splitlines():
            print(f"  {dim(line)}")
    if q.explanation.doc_ref:
        print(f"\n{dim(q.explanation.doc_ref)}")
    print()
    return 0


def cmd_search(args) -> int:
    bank = load(args.data_dir)
    matches = bank.find(args.needle)
    if not matches:
        print(dim(f"Nothing matches {args.needle!r}."))
        return 0
    for q in matches:
        print(f"  {dim(q.id)}  {bold(q.title)}")
        print(f"           {dim(DOMAIN_SHORT[q.domain] + ' · ' + q.subtopic)}")
    print(f"\n{len(matches)} match(es)\n")
    return 0


def cmd_stats(args) -> int:
    bank = load(args.data_dir)
    total = len(bank.questions)
    print(f"\n{bold('Bank')}  {total} questions, {len(bank.subtopics())} subtopics\n")

    print(bold("By section"))
    for d in DOMAINS:
        n = bank.counts()[d]
        pct = n / total * 100 if total else 0
        print(f"  {DOMAIN_SHORT[d].ljust(18)} {n:>4}  ({pct:4.1f}%)  {dim('▪' * min(n, 40))}")

    print(f"\n{bold('By objective')}")
    for oid, qs in bank.by_objective().items():
        print(f"  {oid}  {OBJECTIVES[oid].title.ljust(54)} {len(qs):>4}")
    n_new = sum(1 for q in bank.questions if q.is_new)
    print(f"\n  {n_new} question(s) on bullets new in the June 2026 guide")

    print(f"\n{bold('By source')}")
    by_source: dict[str, int] = {}
    for q in bank.questions:
        by_source[q.source] = by_source.get(q.source, 0) + 1
    for src, n in sorted(by_source.items(), key=lambda kv: -kv[1]):
        print(f"  {src.ljust(16)} {n:>4}")

    print(f"\n{bold('Correct-answer spread')}")
    letters = {k: 0 for k in OPTION_KEYS}
    singles = [q for q in bank.questions if not q.is_multi]
    for q in singles:
        letters[q.correct_answer] += 1
    total = len(singles)
    for k, n in letters.items():
        pct = n / total * 100 if total else 0
        flag = "" if 18 <= pct <= 32 else yellow("  ← skewed")
        print(f"  {k}  {n:>4}  ({pct:4.1f}%){flag}")

    print(f"\n{bold('Most common tags')}")
    tags: dict[str, int] = {}
    for q in bank.questions:
        for t in q.tags:
            tags[t] = tags.get(t, 0) + 1
    for t, n in sorted(tags.items(), key=lambda kv: -kv[1])[:12]:
        print(f"  {t.ljust(28)} {n:>3}")
    print()
    return 0


def cmd_check(args) -> int:
    """Validate the bank and report anything a human should look at."""
    bank = load(args.data_dir)
    problems = 0

    print(f"\n{bold('Schema')}  ", end="")
    print(green(f"OK — {len(bank.questions)} questions load and validate"))

    # Thin subtopics make an exam feel repetitive when sampled.
    thin = [(s, n) for s, n in bank.subtopics().items() if n < 2]
    if thin:
        print(f"\n{yellow('Thin subtopics')} (only one question — easy to memorise)")
        for s, n in thin:
            print(f"  {s}")

    dupes = bank.duplicate_pairs(threshold=args.threshold)
    if dupes:
        problems += len(dupes)
        print(f"\n{red('Near-duplicate stems')} (overlap ≥ {args.threshold:.0%})")
        for a, b, score in dupes:
            print(f"  {score:.0%}  {dim(a.id)} {a.title}")
            print(f"       {dim(b.id)} {b.title}")
    else:
        print(f"\n{bold('Near-duplicate stems')}  {green('none')}")

    # Same concept is allowed; a recycled answer set is not.
    collisions = bank.option_collisions()
    if collisions:
        problems += len(collisions)
        print(f"\n{red('Recycled answer sets')} (same correct answer, >{SHARED_OPTION_LIMIT} identical options)")
        for a, b, n in collisions:
            print(f"  {n} shared  {dim(a.id)} {a.title}")
            print(f"            {dim(b.id)} {b.title}\n")
    else:
        print(f"{bold('Recycled answer sets')}    {green('none')}")

    # Coverage against the blueprint: what the sampler will struggle with.
    print(f"\n{bold('Blueprint coverage')} (questions available vs. needed for a 50-question exam)")
    from src.blueprint import objective_weights
    by_obj = bank.by_objective()
    for oid, w in objective_weights().items():
        have = len(by_obj[oid])
        need = max(1, round(w * 50))
        ratio = have / need
        note = green("ample") if ratio >= 3 else (yellow("thin") if ratio >= 1.5 else red("too few"))
        print(f"  {oid}  {OBJECTIVES[oid].title[:44].ljust(44)} have {have:>4}   need ~{need:>2}/exam   {note}")
    uncovered = [b for b, n in bank.bullet_coverage().items() if n == 0]
    if uncovered:
        problems += len(uncovered)
        print(red(f"\n  Guide bullets with no question: {', '.join(uncovered)}  (kb.py blueprint)"))
    else:
        print(f"  {green('every guide bullet has at least one question')}  {dim('(kb.py blueprint for detail)')}")

    print()
    if problems:
        print(yellow(f"{problems} item(s) worth reviewing.\n"))
        return 1 if args.strict else 0
    print(green("Nothing to review.\n"))
    return 0


# --------------------------------------------------------------------------
# Write commands
# --------------------------------------------------------------------------


ADD_PROMPT = """\
You are a Google Cloud Certified Associate Cloud Engineer writing exam-quality practice questions.

{brief}

The question must test the Associate Cloud Engineer exam guide live from 30 June 2026 — nothing
outside it. Place it on exactly one objective and one subtopic from this closed list (use the exact
strings; a subtopic belongs to the objective it is listed under, and anything that fits no subtopic
is out of scope and must not be written):
{subtopics}

These questions are already in the bank. You MAY test the same concept as one of them, but your
stem must describe a different scenario in different words, and your four options must differ —
never reuse more than two of an existing question's options:
{existing}

Requirements:
- A concrete scenario, 2-4 sentences, with a clear requirement and enough detail to be decidable.
- Exactly four options; exactly one unambiguously correct.
- Every distractor must be plausible and wrong for a specific, stateable technical reason.
  Never use filler such as "None of the above".
- option_breakdown must explain all of A, B, C and D. The correct one starts with "Correct.".
- title: a short label under 60 characters, no trailing full stop or question mark.
- summary: one sentence stating the single idea the question tests.
- tags: 2-5 lowercase kebab-case tags.
- gcloud_command: a real, runnable gcloud/kubectl/bq command implementing the correct answer.
- doc_ref: a real https://cloud.google.com/... documentation URL.
- Test judgement about a scenario, not recall of a fact.

Return ONLY a JSON array of {count} object(s) — no prose, no markdown fences — shaped exactly:
[{{"objective": "2.3", "subtopic": "...", "title": "...", "summary": "...", "tags": ["..."],
   "question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
   "correct_answer": "A",
   "explanation": {{"summary": "...",
     "option_breakdown": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
     "gcloud_command": "...", "doc_ref": "https://cloud.google.com/..."}}}}]
"""


def cmd_lint(args) -> int:
    """The machine-checkable parts of docs/question-standard.md."""
    from src.question_lint import LONGEST_KEY_LIMIT, key_spread, lint_bank, longest_key_rate

    bank = load(args.data_dir)
    qs = [q for q in bank.questions if not args.ids or q.id in args.ids]
    found = lint_bank(bank.questions)
    errors = warnings = 0
    for q in qs:
        for sev, code, msg in found.get(q.id, []):
            if sev == "warning" and not args.warnings:
                continue
            errors += sev == "error"
            warnings += sev == "warning"
            tag = red("error") if sev == "error" else yellow("warn ")
            print(f"{tag}  {q.id:<14} {code:<18} {msg}")
    rate = longest_key_rate(bank.questions)
    spread = "  ".join(f"{k} {v:.0%}" for k, v in key_spread(bank.questions).items())
    ok = rate <= LONGEST_KEY_LIMIT
    print(f"\n{bold('Key spread')}  {spread}")
    print(f"{bold('Longest option is the key')}  "
          + (green if ok else red)(f"{rate:.0%} (limit {LONGEST_KEY_LIMIT:.0%}, chance 25%)"))
    print(f"{bold('Findings')}  {errors} errors" + (f", {warnings} warnings" if args.warnings else ""))
    return 1 if errors or not ok else 0


def _infer(bank: QuestionBank, brief: str, count: int, model: str,
           domain: Optional[str]) -> List[Question]:
    """Ask the model for fully-formed questions; return the ones that validate."""
    from check_network import require_network

    require_network()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY is not set. Export a key, or use --file to add "
              "a hand-written question.", file=sys.stderr)
        sys.exit(1)
    try:
        from anthropic import Anthropic
    except ImportError:
        print("[ERROR] The anthropic package is missing. Use the Python install from the README; "
              "the Docker image doesn't include it.", file=sys.stderr)
        sys.exit(1)

    scope = [q for q in bank.questions if domain is None or q.domain == domain]
    existing = "\n".join(f"- {q.title}: {q.summary}" for q in scope[:120]) or "(none)"
    subs = "\n".join(
        f"{o.id} {o.title}: " + "; ".join(s.name for s in subtopics_in(o.id))
        for o in OBJECTIVES.values()
        if domain is None or f"Section {o.section}:" in domain
    )

    msg = Anthropic().messages.create(
        model=model,
        max_tokens=8000,
        messages=[{"role": "user", "content": ADD_PROMPT.format(
            brief=brief,
            subtopics=subs,
            existing=existing,
            count=count,
        )}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text[4:] if text.lstrip().startswith("json") else text
        text = text.strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] model did not return valid JSON: {exc}", file=sys.stderr)
        print(text[:600], file=sys.stderr)
        return []

    out: List[Question] = []
    for i, raw in enumerate(payload):
        raw["id"] = "pending"
        raw["source"] = "llm"
        if domain:
            raw["domain"] = domain
        try:
            out.append(Question.model_validate(raw))
        except Exception as exc:
            print(yellow(f"[WARN] dropping generated item {i}: {exc}"), file=sys.stderr)
    return out


def _preview(q: Question) -> None:
    print("\n" + "─" * 90)
    print(f"{bold(q.title)}   {dim(DOMAIN_SHORT[q.domain] + ' · ' + q.subtopic)}")
    print(dim(q.summary))
    print(f"\n{textwrap.fill(q.question, 90)}\n")
    for k in q.keys:
        marker = green("✓") if k in q.correct_keys else " "
        print(textwrap.fill(f"{marker} {k}. {q.options[k]}", 90, subsequent_indent="     "))
    print(f"\n{dim(textwrap.fill(q.explanation.summary, 88))}")


def _report_overlap(bank: QuestionBank, q: Question, threshold: float) -> bool:
    """Warn if the candidate looks like something already in the bank."""
    near = sorted(
        ((other, q.similarity(other)) for other in bank.questions if other.domain == q.domain),
        key=lambda r: -r[1],
    )[:1]
    flagged = False
    if near and near[0][1] >= threshold:
        other, score = near[0]
        print(yellow(f"\n  ⚠ {score:.0%} stem overlap with {other.id} — {other.title}"))
        flagged = True
    recycled = bank.recycled_options(q)
    if recycled:
        other, n = recycled
        print(yellow(f"\n  ⚠ shares {n} identical options with {other.id} — {other.title}"))
        flagged = True
    return flagged


def cmd_add(args) -> int:
    bank = load(args.data_dir)
    before = len(bank.questions)
    domain = resolve_domain(args.domain)

    candidates: List[Question] = []

    if args.file:
        if not args.file.exists():
            print(f"[ERROR] {args.file} not found", file=sys.stderr)
            return 1
        raw_payload = json.loads(args.file.read_text(encoding="utf-8"))
        for raw in (raw_payload if isinstance(raw_payload, list) else [raw_payload]):
            raw.setdefault("id", "pending")
            raw.setdefault("source", "user")
            if domain:
                raw["domain"] = domain
            try:
                candidates.append(Question.model_validate(raw))
            except Exception as exc:
                print(f"[ERROR] {args.file}: {exc}", file=sys.stderr)
                return 1
    else:
        brief = (
            f"Take this raw question stem and turn it into {args.count} complete, polished "
            f"exam question(s), rewriting it into a proper scenario if it is terse.\n\n"
            f"Stem: {args.stem}"
            if args.stem else
            f"Write {args.count} exam question(s) on this topic outline.\n\nTopic: {args.topic}"
        )
        print(dim(f"Generating with {args.model}…"))
        candidates = _infer(bank, brief, args.count, args.model, domain)

    if not candidates:
        print(red("\nNo valid questions produced."), file=sys.stderr)
        return 1

    flagged = 0
    for q in candidates:
        q.id = bank.next_id(q.domain, QuestionBank.retired_ids(args.data_dir), cross=q.is_cross_domain)
        _preview(q)
        if _report_overlap(bank, q, args.threshold):
            flagged += 1
        bank.questions.append(q)  # reserve the id so siblings do not collide

    print("\n" + "─" * 90)
    print(f"{len(candidates)} question(s) ready. Bank: {before} → {len(bank.questions)}.")
    if flagged:
        print(yellow(f"{flagged} flagged for possible overlap — review before accepting."))

    if args.dry_run:
        print(dim("[DRY RUN] nothing written."))
        return 0

    if not args.yes:
        try:
            reply = input("\nWrite to the bank? [y/N] ").strip().lower()
        except EOFError:
            reply = "n"
        if reply not in ("y", "yes"):
            print("Aborted; nothing written.")
            return 0

    bank.save(args.data_dir)
    print(green(f"\n[OK] wrote {len(candidates)} question(s); bank now {len(bank.questions)}."))
    print(dim("     register.json rebuilt."))
    return 0


# --------------------------------------------------------------------------
# Planned expansion (the /expand skill)
# --------------------------------------------------------------------------

EXPAND_DIR = ROOT / "build" / "expand"
GUARD_FILE = ROOT / "tests" / "fixtures" / "guarded_stems.json"


def _read_json(path: Path):
    if not path.exists():
        print(f"[ERROR] {path} not found", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[ERROR] {path} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def _candidates(path: Path) -> list:
    data = _read_json(path)
    return data if isinstance(data, list) else [data]


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _guarded(stem: str) -> Optional[str]:
    """The id of a removed question this stem restates, if any (the guard the test suite applies to the bank)."""
    import hashlib

    from audit_overlap import flagged, scores, tokens

    if not GUARD_FILE.exists():
        return None
    guard = json.loads(GUARD_FILE.read_text(encoding="utf-8"))
    mine = frozenset(hashlib.sha256((guard["salt"] + t).encode()).hexdigest()[:12] for t in tokens(stem))
    for g in guard["stems"]:
        if flagged(*scores(mine, frozenset(g["tokens"]))):
            return g["id"]
    return None


def _vet(bank: QuestionBank, raws: list, plan: Optional[dict], offline: bool, final: bool):
    from src.expansion import fetch_page, vet

    pages = None if offline else (lambda url: fetch_page(url, EXPAND_DIR / "cache"))
    found, parsed = vet(bank, raws, plan=plan, pages=pages, final=final)
    for label, q in parsed.items():
        hit = _guarded(q.question)
        if hit:
            found.setdefault(label, []).append(
                ("error", "guarded", f"the stem restates removed question {hit}; write a different scenario (AC7)"))
    return found, parsed


def _print_findings(found: dict, parsed: dict, raws: list) -> int:
    errors = 0
    for label, items in found.items():
        for sev, code, msg in items:
            errors += sev == "error"
            tag = red("error") if sev == "error" else yellow("warn ")
            print(f"{tag}  {label:<9} {code:<17} {msg}")
    clean = [k for k in parsed if not any(s == "error" for s, _, _ in found.get(k, []))]
    skipped = sum("skip" in r for r in raws)
    print(f"\n{len(raws)} item(s): {len(clean)} without errors, {skipped} skipped, {errors} error(s).")
    return errors


def cmd_plan(args) -> int:
    from src.expansion import parse_grow, plan, plan_summary

    bank = load(args.data_dir)
    try:
        grow = parse_grow(args.grow, len(bank.questions))
        p = plan(bank, grow, balance=args.balance, sections=args.sections, objective=args.objective,
                 cross_share=args.cross_share, multi_share=args.multi_share, batch_size=args.batch_size,
                 request=args.grow)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print("\n".join(plan_summary(bank, p)))
    if args.out:
        if args.out.exists():
            print(f"[ERROR] {args.out} exists; continue that run with 'kb.py slots', or pick another --out",
                  file=sys.stderr)
            return 1
        _write_json(args.out, p)
        print(green(f"\n[OK] wrote {args.out}"))
    else:
        print(dim("\nNothing written; pass --out FILE to start a run."))
    return 0


def cmd_slots(args) -> int:
    from src.expansion import describe_slots, open_batch

    bank = load(args.data_dir)
    p = _read_json(args.plan)
    counts: dict[str, int] = {}
    for s in p["slots"]:
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    print("Run: " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())) + f" of {len(p['slots'])} slots\n")
    batch = args.batch or open_batch(p)
    if batch is None:
        print(green("Every slot is filled or skipped. The run is complete."))
        return 0
    print("\n".join(describe_slots(bank, p, batch)))
    return 0


def cmd_doc(args) -> int:
    from src.expansion import fetch_page, find_in_page, preview_notes

    try:
        text = fetch_page(args.url, EXPAND_DIR / "cache")
    except Exception as exc:
        print(f"[ERROR] cannot read {args.url}: {exc}", file=sys.stderr)
        return 1
    for note in preview_notes(text):
        print(yellow(f"[PREVIEW MENTIONED] …{note}…"))
    if args.find:
        lines = find_in_page(text, args.find)
        print("\n".join(lines) if lines else dim("No line mentions those terms; try others, or read the page whole."))
        return 0
    print(text if args.all or len(text) <= args.max_chars else
          text[: args.max_chars] + f"\n\n[cut at {args.max_chars} of {len(text)} characters; use --find or --all]")
    return 0


def cmd_vet(args) -> int:
    bank = load(args.data_dir)
    raws = _candidates(args.file)
    plan = _read_json(args.plan) if args.plan else None
    found, parsed = _vet(bank, raws, plan, args.offline, args.final)
    return 1 if _print_findings(found, parsed, raws) else 0


def cmd_blind(args) -> int:
    from src.expansion import blind_sheet, record_blind

    raws = _candidates(args.file)
    try:
        if not args.answers:
            print(blind_sheet(raws))
            return 0
        answers = dict(a.split("=", 1) for a in args.answers)
        rows = record_blind(raws, answers)
    except Exception as exc:
        print(f"[ERROR] {' '.join(str(exc).split())}\nRun kb.py vet first; give answers as SLOT=LETTERS.",
              file=sys.stderr)
        return 1
    _write_json(args.file, raws)
    for label, key, given, agrees in rows:
        print(f"{green('agree   ') if agrees else red('DISAGREE')}  {label:<9} key {key:<4} blind {given or '-'}")
    missing = sum("skip" not in r and "blind" not in r for r in raws)
    if missing:
        print(yellow(f"{missing} candidate(s) have no blind answer yet."))
    return 0 if all(r[3] for r in rows) and not missing else 1


def cmd_accept(args) -> int:
    """Add a batch that passes every gate. All or nothing: one error and the bank is untouched."""
    from src.expansion import ledger_entry, mark

    bank = load(args.data_dir)
    raws = _candidates(args.file)
    plan = _read_json(args.plan)
    found, parsed = _vet(bank, raws, plan, args.offline, final=True)
    if _print_findings(found, parsed, raws):
        print(red("\nNothing written. Fix the errors, or mark a slot {\"slot\": N, \"skip\": \"reason\"}."))
        return 1

    retired = QuestionBank.retired_ids(args.data_dir)
    ledger = _read_json(args.ledger) if args.ledger.exists() else {"standard": "docs/question-standard.md",
                                                                  "entries": []}
    added = []
    for i, raw in enumerate(raws):
        if "skip" in raw:
            mark(plan, raw["slot"], "skipped", reason=str(raw["skip"]).strip())
            continue
        q = parsed[f"slot {raw['slot']}"]
        q.id = bank.next_id(q.domain, retired, cross=q.is_cross_domain)
        bank.questions.append(q)
        ledger["entries"].append(ledger_entry(q, raw))
        mark(plan, raw["slot"], "filled", id=q.id)
        raw["id"] = q.id
        added.append(q.id)
    QuestionBank(questions=bank.questions)  # ids, GUIDs and titles still unique

    if args.dry_run:
        print(dim(f"[DRY RUN] would add {len(added)} question(s); nothing written."))
        return 0
    bank.save(args.data_dir)
    _write_json(args.ledger, ledger)
    _write_json(args.plan, plan)
    _write_json(args.file, raws)
    left = sum(s["status"] == "open" for s in plan["slots"])
    print(green(f"\n[OK] added {len(added)}: {' '.join(added)}"))
    print(f"Bank now {len(bank.questions)}. {left} slot(s) still open in the plan.")
    return 0


def cmd_reindex(args) -> int:
    bank = load(args.data_dir)
    bank.save(args.data_dir)
    print(green(f"[OK] rebuilt register.json and rewrote {len(DOMAINS)} section files "
                f"({len(bank.questions)} questions)."))
    return 0


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="kb.py", description="Query and grow the GCP ACE question bank.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__,
    )
    ap.add_argument("--data-dir", type=Path, default=DATA_DIR, help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("blueprint", help="coverage of every exam-guide bullet")
    p.add_argument("--min", type=int, default=2, help="flag bullets with fewer questions (default 2)")
    p.add_argument("--strict", action="store_true", help="exit 1 if any bullet is below --min")
    p.set_defaults(func=cmd_blueprint)

    p = sub.add_parser("topics", help="objectives and subtopics with counts")
    p.add_argument("--section", "--domain", "-d", dest="domain", help="section number 1-4 or title fragment")
    p.set_defaults(func=cmd_topics)

    p = sub.add_parser("list", help="list question titles")
    p.add_argument("--section", "--domain", "-d", dest="domain", help="section number 1-4 or title fragment")
    p.add_argument("--objective", "-o", choices=sorted(OBJECTIVES), help="guide objective, e.g. 2.3")
    p.add_argument("--new", action="store_true", help="only bullets new in the June 2026 guide")
    p.add_argument("--subtopic", "-s", help="subtopic substring")
    p.add_argument("--tag", "-t", help="exact tag")
    p.add_argument("--source", choices=["curated", "official-sample", "user", "llm"])
    p.add_argument("--verbose", "-v", action="store_true", help="also print summaries")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="print one question in full")
    p.add_argument("needle", help="question id or title fragment")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("search", help="free-text search across the bank")
    p.add_argument("needle")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("stats", help="bank health at a glance")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("check", help="validate and report duplicates and gaps")
    p.add_argument("--threshold", type=float, default=STEM_OVERLAP_LIMIT,
                   help=f"stem-overlap threshold for near-duplicates (default {STEM_OVERLAP_LIMIT})")
    p.add_argument("--strict", action="store_true", help="exit 1 if anything is flagged")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("lint", help="check questions against docs/question-standard.md")
    p.add_argument("ids", nargs="*", help="only these ids (default: all)")
    p.add_argument("--warnings", action="store_true", help="also show heuristic warnings")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("add", help="add a question, by LLM or from a file")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--stem", help="raw question stem to expand")
    src.add_argument("--topic", help="topic outline to generate from")
    src.add_argument("--file", type=Path, help="JSON file with one question or a list")
    p.add_argument("--section", "--domain", "-d", dest="domain",
                   help="restrict to a section (otherwise the model places the question)")
    p.add_argument("--count", type=int, default=1, help="questions to generate (default 1)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--threshold", type=float, default=STEM_OVERLAP_LIMIT,
                   help="warn at or above this stem overlap with an existing question")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--yes", "-y", action="store_true", help="skip confirmation")
    p.set_defaults(func=cmd_add)

    from src.expansion import BALANCES, BATCH_SIZE, CROSS_SHARE, MULTI_SHARE

    p = sub.add_parser("plan", help="plan an expansion: where N new questions go")
    p.add_argument("grow", help="how much to add: a share of the bank (10%%) or a count (25)")
    p.add_argument("--balance", choices=BALANCES, default="exam",
                   help="exam: fill what is furthest below the exam weights (default); batch: split the run by "
                        "the exam weights; current: grow every section by the same percentage")
    p.add_argument("--section", dest="sections", type=int, action="append", choices=[1, 2, 3, 4],
                   help="only this section (repeatable)")
    p.add_argument("--objective", "-o", choices=sorted(OBJECTIVES), help="only this objective")
    p.add_argument("--cross-share", type=float, default=CROSS_SHARE,
                   help=f"share of cross-domain questions (default {CROSS_SHARE})")
    p.add_argument("--multi-share", type=float, default=MULTI_SHARE,
                   help=f"share of multiple-select questions (default {MULTI_SHARE})")
    p.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    p.add_argument("--out", type=Path, help="write the plan here and start a run")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("slots", help="what the next batch of a plan must contain")
    p.add_argument("plan", type=Path)
    p.add_argument("--batch", type=int, help="a batch number (default: the first with an open slot)")
    p.set_defaults(func=cmd_slots)

    p = sub.add_parser("doc", help="a documentation page as plain text")
    p.add_argument("url")
    p.add_argument("--find", action="append", help="only lines mentioning this term (repeatable)")
    p.add_argument("--max-chars", type=int, default=12000)
    p.add_argument("--all", action="store_true", help="print the whole page")
    p.set_defaults(func=cmd_doc)

    p = sub.add_parser("vet", help="check candidate questions before they are added")
    p.add_argument("file", type=Path)
    p.add_argument("--plan", type=Path, help="also check each candidate against its slot")
    p.add_argument("--offline", action="store_true", help="skip checking evidence quotes against the doc pages")
    p.add_argument("--final", action="store_true", help="also require an agreeing blind-solve record")
    p.set_defaults(func=cmd_vet)

    p = sub.add_parser("blind", help="candidates without keys, and recording a blind solver's answers")
    p.add_argument("file", type=Path)
    p.add_argument("--answers", nargs="+", metavar="SLOT=LETTERS", help="for example 12=B 13=A,D")
    p.set_defaults(func=cmd_blind)

    p = sub.add_parser("accept", help="add a vetted, blind-solved batch to the bank")
    p.add_argument("file", type=Path)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--ledger", type=Path, required=True, help="review ledger of this run (created if missing)")
    p.add_argument("--offline", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_accept)

    p = sub.add_parser("reindex", help="rewrite section files and rebuild register.json")
    p.set_defaults(func=cmd_reindex)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
