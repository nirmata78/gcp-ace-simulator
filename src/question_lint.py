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


# --------------------------------------------------------------------------
# Identifiers (AC6 of standard 2): role IDs, commands, flags, permissions and API names are code
# --------------------------------------------------------------------------

CODE_SPAN = re.compile(r"`([^`]+)`")
#: The first word after each CLI that makes it a command rather than a mention of the tool.
CLI_WORDS = {
    "gcloud": "access-context-manager ai alloydb alpha app apphub artifacts asset auth backup-dr batch beta bigtable "
              "billing builds certificate-manager composer compute config container database-migration dataflow "
              "dataplex dataproc datastore deploy deployment-manager dns domains endpoints eventarc filestore "
              "firestore functions iam iap identity infra-manager init kms logging looker memcache migration ml "
              "monitoring network-connectivity network-management network-security observability organizations "
              "policy-intelligence privateca projects pubsub quotas recommender redis resource-manager run "
              "scheduler scc secrets services source spanner sql storage tasks transfer workflows workstations",
    "kubectl": "annotate api-resources apply attach autoscale auth config cordon cp create delete describe diff drain "
               "edit exec explain expose get kustomize label logs patch port-forward replace rollout run scale set "
               "taint top uncordon wait",
    "bq": "add-iam-policy-binding cancel cp extract get-iam-policy head insert load ls mk mkdef partition query rm "
          "set-iam-policy show update wait",
    "gsutil": "acl autoclass cat compose cors cp defacl du hash iam kms label lifecycle logging ls mb mv "
              "notification rb requesterpays retention rm rsync setmeta signurl stat ubla versioning web",
}
#: Words that end a command written in prose ("gcloud sql connect to the instance").
_STOP = {"and", "or", "to", "the", "a", "an", "with", "for", "in", "on", "at", "of", "is", "are", "then", "again",
         "from", "as", "by", "so", "but", "which", "that", "this", "it", "its", "after", "before", "instead", "only"}
_CLI = re.compile(r"\b(gcloud|kubectl|gsutil|bq)((?:\s+[a-z][a-z0-9-]*){1,5})")
IDENT_PATTERNS = {
    "role ID": re.compile(r"\broles/[A-Za-z][\w.]*[\w]"),
    "flag": re.compile(r"(?<![\w-])--[a-z][a-z0-9-]+"),
    "permission": re.compile(r"\b[a-z][a-z0-9]+\.[a-z][a-zA-Z]*[A-Z][A-Za-z]*\.[a-z][A-Za-z]+\b"
                             r"|\b[a-z][a-z0-9]+\.[a-z]+s\.[a-z][A-Za-z]+\b"),
    "API name": re.compile(r"\b[a-z0-9-]+\.googleapis\.com\b"),
}
_NOT_PERMISSION = re.compile(r"\.(com|org|io|dev|net|app|json|yaml|yml|py|txt|tf)$")


def code_spans(text: str) -> List[str]:
    """The text inside backticks."""
    return CODE_SPAN.findall(text or "")


def bare_identifiers(text: str) -> List[Tuple[str, str]]:
    """``(kind, identifier)`` for each identifier written outside backticks."""
    prose = CODE_SPAN.sub(" ", text or "")
    out = []
    for kind, pattern in IDENT_PATTERNS.items():
        for m in pattern.finditer(prose):
            hit = m.group(0).rstrip(".")
            if kind == "permission" and _NOT_PERMISSION.search(hit):
                continue
            out.append((kind, hit))
    out += [("command", c) for c in commands(prose)]
    return out


def commands(text: str) -> List[str]:
    """CLI commands written in ``text``: the tool, a real group or verb, and the words of the command path."""
    out = []
    for m in _CLI.finditer(text or ""):
        tool, words = m.group(1), m.group(2).split()
        if words[0] not in CLI_WORDS[tool].split():
            continue
        path = []
        for w in words:
            if w in _STOP:
                break
            path.append(w)
        out.append(" ".join([tool] + path))
    return out


def _texts(q: Question) -> Dict[str, str]:
    out = {"stem": q.question, "summary": q.explanation.summary}
    out.update({f"option {k}": q.options[k] for k in q.keys})
    out.update({f"rationale {k}": q.explanation.option_breakdown[k] for k in q.keys})
    return out


def _family(text: str) -> set:
    """What makes two options siblings: the same role namespace, command group or API, or shared content words."""
    fam = set()
    for span in code_spans(text) or [text]:
        for m in IDENT_PATTERNS["role ID"].finditer(span):
            fam.add("role:" + m.group(0).split(".")[0])
        for c in commands(span):
            fam.add("cmd:" + " ".join(c.split()[:3]))
        for m in IDENT_PATTERNS["API name"].finditer(span):
            fam.add("api:" + m.group(0))
    return fam


def _content(text: str) -> set:
    return {w for w in re.findall(r"[a-z][a-z0-9.-]{3,}", text.lower())} - {"with", "that", "from", "only", "this"}


#: Two options whose content words overlap this much read as siblings.
SIBLING_OVERLAP = 0.20
#: Standard 2: at least this many distractors are siblings of a key option (AC3).
MIN_SIBLINGS = 2
#: Standard 2 stem length (AC2): architecture and migration scenarios need more room than standard 1 allowed.
STEM_WORDS_V2 = (25, 130)


def siblings(q: Question) -> List[str]:
    """The distractors that are close relatives of a key option (AC3, standard 2)."""
    keys = [q.options[k] for k in q.correct_keys]
    out = []
    for k in q.keys:
        if k in q.correct_keys:
            continue
        d = q.options[k]
        for key in keys:
            a, b = _content(d), _content(key)
            overlap = len(a & b) / len(a | b) if a and b else 0.0
            if (_family(d) & _family(key)) or overlap >= SIBLING_OVERLAP:
                out.append(k)
                break
    return out


def lint_standard_two(q: Question) -> List[Finding]:
    """The rules standard 2 adds. On a standard-1 question they are prompts, on a standard-2 question defects."""
    sev = "error" if q.standard >= 2 else "warning"
    out: List[Finding] = []
    for where, text in _texts(q).items():
        if text.count("`") % 2:
            out.append(("error", "backticks", f"unbalanced backticks in the {where}"))
            continue
        bare = bare_identifiers(text)
        if bare:
            shown = ", ".join(f"{i}" for _, i in bare[:3])
            out.append((sev, "ident-unformatted", f"{where}: write identifiers in backticks: {shown} (AC6)"))
    if q.standard >= 2:
        found = siblings(q)
        if len(found) < MIN_SIBLINGS:
            out.append(("warning", "sibling-count", f"only {len(found)} distractor(s) look like siblings of the key "
                        f"({', '.join(found) or 'none'}); at least {MIN_SIBLINGS} should be close relatives (AC3)"))
        n = _words(q.question)
        if not STEM_WORDS_V2[0] <= n <= STEM_WORDS_V2[1]:
            out.append(("warning", "stem-length", f"stem is {n} words; aim for {STEM_WORDS_V2[0]}–{STEM_WORDS_V2[1]} (AC2)"))
    return out


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
    if q.standard < 2 and (n < 15 or n > 110):
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

    cli = [k for k in q.keys if CLI.match(q.options[k].strip("`"))]
    flagged = [k for k in cli if FLAG.search(q.options[k])]
    if q.standard < 2 and len(cli) >= 3 and len(flagged) >= 2:  # standard 2 tests exact commands on purpose (AC1)
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
    out += lint_standard_two(q)
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


#: Standard 2: the share of questions that also test another objective (AC1).
MULTI_TOPIC_TARGET = 0.60


def multi_topic_share(questions: Iterable[Question]) -> Tuple[float, int]:
    """Share of standard-2 questions that set ``also_tests``, and how many standard-2 questions there are."""
    qs = [q for q in questions if q.standard >= 2]
    return (sum(bool(q.also_tests) for q in qs) / len(qs) if qs else 0.0), len(qs)


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
