# Excluded questions: review record

104 questions were held out of the public bank before v1.0.0 because their origin couldn't be vouched for. They were
reviewed in [issue #1](https://github.com/nirmata78/gcp-ace-simulator/issues/1). **Their text is not in this directory
any more and never reached a release.**

| File | What it is |
|---|---|
| `decisions.json` | One verdict per question (`drop` or `rewrite`), with the reason and, for a rewrite, the id of the new question |
| `audit.json` | Each question's overlap with the audited public sources, the sources and their commits, the method, and the 2026-11-07 audit of the current bank |

A `rewrite` is a new question written from the guide bullet and current documentation without reading the old stem,
options or scenario; it gets a new id. No question was kept. Removed and excluded ids are listed in
[`data/retired.json`](../../data/retired.json) and are never reused. `tests/test_question_standard.py` keeps them out
of the bank: it compares every stem with salted hashes of their tokens (`tests/fixtures/guarded_stems.json`).

Rerun the audit with `scripts/audit_overlap.py`; keep the reference files locally, never commit them.
If you own text that resembled a question here, open an issue.
