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

**Final state, 2026-11-07.** The 25 rewrites are in the bank (`replacement_id` in `decisions.json`) and the 79
drops stay out. The same audit had removed 34 current bank questions for sharing a scenario with an earlier public
set; at the owner's decision, 33 of them were restored with their own scenarios, because a public look-alike of a
common exam topic isn't a defect in an original question (the 34th duplicated another question and stays retired).
The 28 topic-only matches listed in `audit.json` stay too.

Rerun the audit with `scripts/audit_overlap.py`; keep the reference files locally, never commit them.
If you own text that resembled a question here, open an issue.
