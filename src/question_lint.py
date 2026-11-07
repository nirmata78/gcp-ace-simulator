"""Machine-checkable parts of the question standard (docs/question-standard.md).

Each check returns findings as ``(severity, code, message)``. ``error`` findings break the standard outright and the
test suite rejects them; ``warning`` findings are prompts for a reviewer, because a heuristic can't decide them.
No Streamlit imports, so ``kb.py lint`` and the tests can share it.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Iterable, List, Tuple
from urllib.parse import urlparse

from src.models import OPTION_KEYS, Question

Finding = Tuple[str, str, str]

#: Products that own something called a "cluster". A stem that says "cluster" must name one.
CLUSTER_PRODUCTS = re.compile(
    r"\b(GKE|Kubernetes|Autopilot|Dataproc|Bigtable|Memorystore|AlloyDB|Spanner|Redis|Valkey|"
    r"Filestore|Cloud SQL|HPC|Slurm|[Ww]orkstations?|VMware)\b", re.I)
#: A comparative needs a criterion beside it (AC2).
SUPERLATIVE = re.compile(r"\b(best|fastest|optimal|most appropriate|ideal)\b", re.I)
CRITERION = re.compile(
    r"\b(least|lowest|fewest|minimi[sz]|most cost|cheapest|recommended|without|while|so that|only|"
    r"must|requirement|constraint|overhead|cost|secure|availability|quickest)\b", re.I)
#: A multiple-select stem ends with "(Choose two.)", as the exam writes it.
CHOOSE = re.compile(r"\(\s*choose (two|three)\b", re.I)
WORDS = {"two": 2, "three": 3}
ALL_NONE = re.compile(r"\b(all|none) of the above\b", re.I)
CLI = re.compile(r"^\s*(gcloud|gsutil|kubectl|bq|terraform)\b")
FLAG = re.compile(r"(?<!\w)--[a-z][a-z0-9-]*")
DOC_HOSTS = {"cloud.google.com", "docs.cloud.google.com", "kubernetes.io", "developer.hashicorp.com",
             "registry.terraform.io", "support.google.com", "workspace.google.com",
             "antigravity.google", "geminicli.com", "google.github.io", "helm.sh"}


def _google_repo(url: str) -> bool:
    """Google's own GitHub organisations publish the docs for some tools, such as Gemini CLI."""
    u = urlparse(url)
    return u.hostname == "github.com" and u.path.split("/")[1:2] in (["google-gemini"], ["GoogleCloudPlatform"])


def _words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def lint_question(q: Question) -> List[Finding]:
    """Findings for one question, without looking at the rest of the bank."""
    out: List[Finding] = []
    stem = q.question
    if re.search(r"\bclusters?\b", stem, re.I) and not CLUSTER_PRODUCTS.search(stem):
        out.append(("error", "bare-cluster", "the stem says 'cluster' without naming the product (AC2)"))
    if SUPERLATIVE.search(stem) and not CRITERION.search(stem):
        out.append(("warning", "vague-superlative",
                    f"'{SUPERLATIVE.search(stem).group(0)}' without a deciding criterion (AC2)"))
    n = _words(stem)
    if n < 15 or n > 110:
        out.append(("warning", "stem-length", f"stem is {n} words; aim for 25–90 (AC2)"))
    if any(ALL_NONE.search(v) for v in q.options.values()):
        out.append(("error", "all-none", "'all/none of the above' option (AC3)"))

    rationale = q.explanation.option_breakdown
    for k in q.keys:
        starts = rationale[k].lstrip().lower().startswith("correct")
        if k in q.correct_keys and not starts:
            out.append(("error", "key-rationale", f"the key's rationale ({k}) doesn't start with 'Correct.' (AC5)"))
        if k not in q.correct_keys and starts:
            out.append(("error", "key-rationale", f"distractor {k}'s rationale starts with 'Correct' (AC4)"))

    says = CHOOSE.search(stem)
    if q.is_multi and (not says or WORDS.get(says.group(1).lower()) != q.choose):
        out.append(("error", "choose-n", f"a multiple-select stem must end with '(Choose {q.choose}.)' in words (AC6)"))
    if not q.is_multi and says:
        out.append(("error", "choose-n", "a single-answer stem says 'Choose …' (AC6)"))

    cli = [k for k in q.keys if CLI.match(q.options[k])]
    flagged = [k for k in cli if FLAG.search(q.options[k])]
    if len(cli) >= 3 and len(flagged) >= 2:
        out.append(("warning", "cli-syntax", "three or more options are commands and they differ by flags; "
                                             "test the decision, not the spelling (AC1)"))

    lens = {k: len(q.options[k]) for k in q.keys}
    if q.is_multi:
        longest = sorted(lens, key=lens.get, reverse=True)[:q.choose]
        if sorted(longest) == q.correct_keys:
            out.append(("warning", "length-tell", f"the {q.choose} correct options are the {q.choose} longest (AC3)"))
    else:
        others = [lens[k] for k in q.keys if k != q.correct_answer]
        if lens[q.correct_answer] > 1.6 * (sum(others) / 3) and lens[q.correct_answer] == max(lens.values()) \
                and lens[q.correct_answer] > 50:
            out.append(("warning", "length-tell", "the correct option is much the longest (AC3)"))

    ref = q.explanation.doc_ref.strip()
    if not ref:
        out.append(("error", "doc-ref", "no doc_ref (AC5)"))
    elif urlparse(ref).hostname not in DOC_HOSTS and not _google_repo(ref):
        out.append(("warning", "doc-ref", f"doc_ref host {urlparse(ref).hostname} is not official documentation"))
    if not q.explanation.gcloud_command.strip():
        out.append(("warning", "no-command", "no gcloud_command or console path (AC5)"))
    return out


def lint_bank(questions: Iterable[Question]) -> Dict[str, List[Finding]]:
    """Per-question findings, including those that need the whole bank: copied rationales (AC5)."""
    qs = list(questions)
    seen: Counter = Counter()
    for q in qs:
        for k in q.keys:
            if k not in q.correct_keys:
                seen[_norm(q.explanation.option_breakdown[k])] += 1
    out: Dict[str, List[Finding]] = {}
    for q in qs:
        found = lint_question(q)
        shared = [k for k in q.keys
                  if k not in q.correct_keys and seen[_norm(q.explanation.option_breakdown[k])] > 1]
        if shared:
            found.append(("error", "copied-rationale",
                          f"rationale for {', '.join(shared)} also appears in another question (AC5)"))
        if found:
            out[q.id] = found
    return out


def key_spread(questions: Iterable[Question]) -> Dict[str, float]:
    """Share of the single-answer questions keyed on each letter (AC6)."""
    c = Counter(q.correct_answer for q in questions if not q.is_multi)
    total = sum(c.values()) or 1
    return {k: c.get(k, 0) / total for k in OPTION_KEYS}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


#: The share of questions where the longest option is the key must stay near chance (AC3, AC6).
LONGEST_KEY_LIMIT = 0.35


def longest_key_rate(questions: Iterable[Question]) -> float:
    """How often "pick the longest option" would score on single-answer questions. Chance is 0.25."""
    qs = [q for q in questions if not q.is_multi]
    hits = 0
    for q in qs:
        lens = {k: len(q.options[k]) for k in OPTION_KEYS}
        hits += max(lens, key=lens.get) == q.correct_answer
    return hits / len(qs) if qs else 0.0
