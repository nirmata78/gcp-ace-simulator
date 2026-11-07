# Question standard

What a question in this bank must be before it ships. Every question is reviewed against the seven criteria below,
and a question that fails any of them is rewritten or removed. `python scripts/kb.py lint` checks the parts a
machine can check; the rest is a reviewer's judgement, recorded in the review ledger
(`docs/reviews/2026-11-bank-review.json`).

The exam it prepares for is the Associate Cloud Engineer exam: an engineer who deploys, operates and secures
workloads on Google Cloud day to day. The bank imitates the *kind* of decision that exam asks for. It never imitates
its items: the no-exam-content rule in [CONTRIBUTING.md](../CONTRIBUTING.md) comes before everything here.

## The seven criteria

### AC1. Associate scope and level

- The question tests one decision an associate engineer makes at work: which resource, role, setting, tool or
  next step. It maps to one guide bullet through its `objective` and `subtopic` (`src/blueprint.py`).
- In scope: IAM grants, gcloud and console tasks, GKE and Cloud Run deployment, storage and database choice, networking
  basics, monitoring and logging, billing and quotas, and troubleshooting a single workload.
- Out of scope: Professional-level design, such as multi-step migrations, org-wide landing zones, or trade-offs that need
  numbers the stem does not give.
- **Commands are allowed when the decision is the tool, not the spelling.** An option may name a command group or
  verb (`gcloud storage buckets update`, `kubectl rollout undo`) when choosing it is the decision. Options must not
  differ only by flag names, flag syntax or argument order, and no option may require remembering a flag to rule it out.
  The exact command belongs in `gcloud_command`, where it teaches.

### AC2. A complete, self-contained scenario

- The stem gives every fact the answer depends on: what already exists, what has been tried, and the constraint that
  decides, such as cost, overhead, security, availability, time or least privilege.
- **Name the product.** Write "GKE cluster", "Dataproc cluster", "managed instance group" or "Cloud SQL for MySQL
  instance", never a bare "cluster", "group" or "database" when more than one product would fit.
- A comparative word such as "best", "fastest" or "cheapest" appears only together with the criterion that settles it:
  "with the least operational overhead", "at the lowest storage cost for this access pattern" or "following
  Google-recommended practice" (the last only when a documented recommendation exists).
- State access patterns and quantities without double meanings. "Each file is read once, a month after it is written"
  is clear; "read once at the start of each month" can be read two ways.
- Network facts that change the answer are stated: external IP or not, Cloud NAT or not, and which VPC, region or project.
- Length: about 25–90 words. Use invented company names only.

### AC3. Plausible, technically sound distractors

- Each wrong option is a real product, role, setting or command that a reader who has skimmed the docs could choose:
  a neighbouring service, a broader role, the wrong scope, a feature that solves a nearby problem.
- **No invented flags, commands, roles or features.** A made-up option tests memory of a list, not judgement.
- Deprecated or legacy features may be distractors only when the stem makes them wrong, because one that still works
  is a second correct answer.
- Options are parallel in form and similar in length, and the correct option is not the only long, hedged or specific
  one. Never use "all of the above" or "none of the above".

### AC4. Exactly one correct answer

- Under the stem's stated facts, exactly one option is right by current Google Cloud documentation. Each other option
  is wrong for a reason that can be stated in the stem's own terms.
- An option that would also work under an assumption the stem does not rule out is a defect. Add the fact that rules
  it out, or replace the option.
- Avoid negatives. If one is needed, write it in capitals ("Which option does NOT…") and use it sparingly.

### AC5. An explanation that teaches

- `explanation.summary` states the mechanism that makes the answer right.
- `option_breakdown` has a rationale for every option. The correct one starts with "Correct." and the others say
  specifically why they fail *in this scenario*. A rationale copied from another question, or one written for a
  different scenario, is a defect.
- `gcloud_command` is a real, current command that carries out the right answer, or a console path written as
  `# Console > …`.
- `doc_ref` links to the current page (`docs.cloud.google.com` or `cloud.google.com`) that proves the answer, and the
  page has been read.
- Every fact a question relies on is taught in `theory/`. If it is not, the theory page gets it too.

### AC6. Fair form

- The answer key is spread evenly across A–D across the bank; `kb.py lint` reports the spread.
- No grammatical or wording cues: the stem's articles and plurals fit every option, and only the correct option
  repeats the stem's wording when another option could too.
- No trick wording, double negatives or traps that depend on a detail buried at the end of the stem.

### AC7. Original and current

- Written from the exam guide and product documentation, never from a remembered exam item, a dump or a practice test
  (`CONTRIBUTING.md`). New questions have `source: curated`, and each new stem must score below the overlap thresholds
  of `scripts/audit_overlap.py` against every audited source.
- Product names are current (check the docs, not memory). A fact likely to change is marked *verify* in the theory.

## Multiple-select and cross-domain questions

The exam mixes multiple-choice and multiple-select items, and many of its scenarios need more than one section of the
guide. The bank has both.

- **Multiple select.** Four or five options, two or three of them correct (`"correct_answer": "A,D"`), and at least
  two wrong. The stem ends with "(Choose two.)" or "(Choose three.)", in words, and only a multiple-select stem says
  it. Each correct option must be needed: if one correct option alone would meet the stem, it's a single-answer
  question. Every correct option's rationale starts with "Correct."; the others say why they fail. A pick scores only
  when every letter matches, as on the exam. Single-answer questions keep exactly four options.
- **Cross-domain.** `also_tests` lists the other guide objectives the scenario needs, at least one in another section.
  The question's own `objective` and `subtopic` are the decision it ends on, and it counts in that section's share.
  Cross-domain questions are `certifying_only` and use ids `ace-x-NNN`; five are drawn into each 50-question exam.
- **Ids and GUIDs.** Every question has a readable `id` and a random `uid` (a GUID) that never changes.

## How a reviewed question changes

- **Keep the id when the decision tested and the correct option stay the same, under the same letter.** Wording,
  constraints, distractors, rationales, the command and the doc link may all change.
- **Mint a new id when the decision or the correct option changes.** Retire the old id rather than reusing it, so
  attempt history never points at a different question. Retired ids are listed in `data/retired.json`, and `kb.py add`
  never mints one of them.
- A question that cannot be fixed without becoming a different question is removed, and the subtopic is checked
  against `kb.py blueprint --min 3 --strict`.

## Review record

Every reviewed question gets one entry in the ledger:

```json
{
  "id": "ace-dom2-018",
  "verdict": "pass | revised | restored | removed | new",
  "ac": {"AC1": "pass", "AC2": "fail", "AC3": "pass", "AC4": "fail", "AC5": "pass", "AC6": "pass", "AC7": "pass"},
  "notes": "“Read once at the start of each month” also reads as one read per object, which makes Archive right.",
  "replacement_id": null
}
```

`restored` marks a question that was removed and brought back unchanged in decision and key, so it keeps its id.
`scripts/review_report.py` turns the ledger into a readable report. For each question that changed, it shows the
original against the refined version, the audit against the seven criteria, and the final question.
