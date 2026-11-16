"""Identifiers in question text: role IDs, permissions, CLI commands, flags and API names.

The exam prints them in a monospace font, and so does the simulator. Version 2 of the question standard writes them in
backticks (AC6). For questions written before that, ``mark`` finds them at display time and adds the backticks, without
changing the stored text. ``src/question_lint.py`` uses the same detectors to report a bare identifier.

No Streamlit imports.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

CODE_SPAN = re.compile(r"`([^`]+)`")

#: The first word after each CLI that makes it a command rather than a mention of the tool.
CLI_WORDS: Dict[str, set] = {tool: set(words.split()) for tool, words in {
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
}.items()}
#: Words that end a command written in prose ("gcloud sql connect to the instance").
STOP = {"and", "or", "to", "the", "a", "an", "with", "for", "in", "on", "at", "of", "is", "are", "then", "again",
        "from", "as", "by", "so", "but", "which", "that", "this", "it", "its", "after", "before", "instead", "only",
        "if", "when", "while", "can", "cannot", "does", "do", "will", "would", "should", "must", "may", "not"}
#: The longest command path kept after each tool: ``gcloud compute networks subnets update``,
#: ``kubectl rollout undo deployment/web``, ``bq load mydataset.t``, ``gsutil iam ch``.
MAX_PATH = {"gcloud": 4, "kubectl": 3, "bq": 2, "gsutil": 2}

_CLI = re.compile(r"\b(gcloud|kubectl|gsutil|bq)((?:[ \t]+[a-z][a-z0-9-]*(?:/[\w.-]+)?){1,6})")
_FLAGS = re.compile(r"(?:[ \t]+--[a-z][a-z0-9_-]*(?:=[^\s,;)`]+)?)*")
PATTERNS = {
    "role ID": re.compile(r"\broles/[A-Za-z][\w.]*\w"),
    "flag": re.compile(r"(?<![\w-])--[a-z][a-z0-9_-]+(?:=[^\s,;)`]+)?"),
    "permission": re.compile(r"\b[a-z][a-z0-9]+\.[a-z][a-zA-Z]*[A-Z][A-Za-z]*\.[a-z][A-Za-z]+\b"
                             r"|\b[a-z][a-z0-9]+\.[a-z]+s\.[a-z][A-Za-z]+\b"),
    "API name": re.compile(r"\b[a-z0-9-]+\.googleapis\.com\b"),
}
_NOT_PERMISSION = re.compile(r"\.(com|org|io|dev|net|app|json|yaml|yml|py|txt|tf)$")


def code_spans(text: str) -> List[str]:
    """The text inside backticks."""
    return CODE_SPAN.findall(text or "")


def _command_spans(prose: str) -> List[Tuple[int, int, str]]:
    out = []
    for m in _CLI.finditer(prose):
        tool, words = m.group(1), m.group(2).split()
        if words[0] not in CLI_WORDS[tool]:
            continue
        path = []
        for w in words[:MAX_PATH[tool]]:
            if w in STOP:
                break
            path.append(w)
        # The end of the kept path in the original text, then any flags written right after it.
        end = m.start(2)
        for w in path:
            end = prose.index(w, end) + len(w)
        flags = _FLAGS.match(prose, end)
        end = flags.end() if flags else end
        out.append((m.start(), end, "command"))
    return out


def spans(text: str) -> List[Tuple[int, int, str]]:
    """``(start, end, kind)`` of each identifier outside backticks, without overlaps, in order."""
    text = text or ""
    shielded = [(m.start(), m.end()) for m in CODE_SPAN.finditer(text)]
    found = _command_spans(text)
    for kind, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            s, e = m.start(), m.end()
            while e > s and text[e - 1] in ".,;:":
                e -= 1
            if kind == "permission" and _NOT_PERMISSION.search(text[s:e]):
                continue
            found.append((s, e, kind))
    found.sort(key=lambda t: (t[0], -(t[1] - t[0])))
    out: List[Tuple[int, int, str]] = []
    for s, e, kind in found:
        if any(a <= s < b or a < e <= b for a, b in shielded):
            continue
        if out and s < out[-1][1]:  # inside a longer match already kept, such as a flag of a command
            continue
        out.append((s, e, kind))
    return out


def bare(text: str) -> List[Tuple[str, str]]:
    """``(kind, identifier)`` for each identifier written outside backticks."""
    return [(kind, text[s:e]) for s, e, kind in spans(text)]


def mark(text: str) -> str:
    """``text`` with backticks around every identifier that has none, for display. Idempotent."""
    text = text or ""
    out, last = [], 0
    for s, e, _ in spans(text):
        out += [text[last:s], "`", text[s:e], "`"]
        last = e
    out.append(text[last:])
    return "".join(out)
