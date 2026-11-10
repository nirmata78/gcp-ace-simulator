# Question standard

What a question in this bank must be before it ships. Every question is reviewed against the seven criteria below,
and a question that fails any of them is rewritten or removed. `python scripts/kb.py lint` checks the parts a
machine can check on the whole bank, and `python scripts/kb.py vet` applies stricter limits to a question before it is
added. The rest is a reviewer's judgement, recorded in a review ledger under `docs/reviews/`.

A wrong key costs more than a missing question: someone decides whether to sit the exam on the strength of these
answers. When a question cannot be made sound, it is left out.

The exam it prepares for is the Associate Cloud Engineer exam: an engineer who deploys, operates and secures
workloads on Google Cloud day to day. The bank imitates the *kind* of decision that exam asks for. It never imitates
its items: the no-exam-content rule in [CONTRIBUTING.md](../CONTRIBUTING.md) comes before everything here.

## The seven criteria

### AC1. Associate scope and level

- The question tests one decision an associate engineer makes at work: which resource, role, setting, tool or
  next step. It maps to one guide bullet through its `objective` and `subtopic` (`src/blueprint.py`).
- **One decision.** A stem that asks for two things is a multiple-select question or two questions.
- **Judgement, not recall.** The reader reasons from the facts in the stem to the answer in about two minutes. A
  question that only asks what a product is, or which name belongs to a definition, is rewritten as a scenario.
- **No key rests on a volatile number.** A price, a quota value or a limit that Google changes may appear in the
  stem as a given, but the answer never depends on remembering it. A stable documented property that the theory
  teaches, such as a storage class's minimum storage duration, is fair.
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
- The constraint comes first and the stem ends with one direct question. The reader should know what is being asked
  without reading the options.
- Length: about 25–90 words; `kb.py vet` holds a new stem to that range. Use invented company names only.

### AC3. Plausible, technically sound distractors

- Each wrong option is a real product, role, setting or command that a reader who has skimmed the docs could choose:
  a neighbouring service, a broader role, the wrong scope, a feature that solves a nearby problem.
- **No invented flags, commands, roles or features.** A made-up option tests memory of a list, not judgement.
- Deprecated or legacy features may be distractors only when the stem makes them wrong, because one that still works
  is a second correct answer.
- **Each distractor fails for its own reason.** Two options that are wrong for the same reason are one distractor
  written twice, and the reader eliminates both at once.
- **Options exclude each other.** No option is a special case, a restatement or the opposite of another, and no
  option is correct "as well" when another is.
- Options are parallel in form and similar in length, and the correct option is not the only long, hedged or specific
  one. Across the bank the longest option is the key in at most 35% of single-answer questions (chance is 25%);
  `kb.py lint` reports the rate. Never use "all of the above" or "none of the above".
- Absolute words ("always", "never", "only", "all") are not used to make an option wrong.

### AC4. Exactly one correct answer

- Under the stem's stated facts, exactly one option is right by current Google Cloud documentation. Each other option
  is wrong for a reason that can be stated in the stem's own terms.
- An option that would also work under an assumption the stem does not rule out is a defect. Add the fact that rules
  it out, or replace the option.
- Avoid negatives. If one is needed, write it in capitals ("Which option does NOT…") and use it sparingly.
- **The blind-solve test.** A second solver who sees only the stem and the options, without the key, the title or the
  rationales, reaches the same answer and can defend no other option. A disagreement is settled from the
  documentation: the stem gains the fact that was missing, or the question goes. The key letter is never moved to
  match the solver. Every question added in bulk passes this test before it enters the bank
  ([Growing the bank](#growing-the-bank)).

### AC5. An explanation that teaches

- `explanation.summary` states the mechanism that makes the answer right. It does more than repeat the correct option.
- `option_breakdown` has a rationale for every option. The correct one starts with "Correct." and the others say
  specifically why they fail *in this scenario*. A rationale copied from another question, or one written for a
  different scenario, is a defect.
- `gcloud_command` is a real, current command that carries out the right answer, or a console path written as
  `# Console > …`.
- `doc_ref` links to the current page (`docs.cloud.google.com` or `cloud.google.com`) that proves the answer, and the
  page has been read.
- **Evidence.** A new question is recorded with the sentence on its `doc_ref` page that proves the key, copied word
  for word. `kb.py vet` and `kb.py accept` fetch the page and reject a quote that is not on it. This is what "the page
  has been read" means for a question written by a model: a key that cannot be tied to a sentence is not added.
- Every fact a question relies on is taught in `theory/`. If it is not, the theory page gets it too.

### AC6. Fair form

- The answer key is spread evenly across A–D across the bank: each letter is the key in 20–30% of single-answer
  questions, and no letter is in more than about half of the multiple-select keys. `kb.py lint` reports the spread.
  In a planned expansion the letter is fixed before the question is written, so the spread does not depend on the
  author's habits.
- No grammatical or wording cues: the stem's articles and plurals fit every option, and only the correct option
  repeats the stem's wording when another option could too.
- No trick wording, double negatives or traps that depend on a detail buried at the end of the stem.

### AC7. Original, distinct and current

- Written from the exam guide and product documentation, never from a remembered exam item, a dump or a practice test
  (`CONTRIBUTING.md`). New questions have `source: curated`, and each new stem must score below the overlap thresholds
  of `scripts/audit_overlap.py` against every audited source.
- **Distinct within the bank.** Two questions may test the same concept, because a second scenario on a weak topic is
  how it gets learned. They may not repeat each other. A new question is one of two things:
  - *a new decision*: a choice under the guide bullet that no question in the subtopic asks. This is preferred;
  - *a variant*: the same decision as an existing question, settled by a different fact: another constraint, another
    state of the resource, another symptom, or the other direction (troubleshoot what exists, not choose what to
    build). A variant is for a bullet whose decisions are already covered.

  A *restatement* is neither: the same decision and the same deciding fact with another company, other numbers or
  other wording. It is never added. When a subtopic has room for neither a new decision nor a variant, it gets no new
  question.
- The machine limits behind that rule: no two stems in a section share 70% or more of their content words, and a new
  stem shares less than 45% with every stem in the bank and in its own batch; two questions with the same correct
  option share at most two identical options; no distractor rationale appears in two questions; and no stem restates a
  removed question (`tests/fixtures/guarded_stems.json`).
- Product names are current (check the docs, not memory). A fact likely to change is marked *verify* in the theory.
- **No Preview feature as the answer.** The key never depends on a feature that was in Preview (pre-GA) in June 2026,
  the state of Google Cloud the exam guide was written against. A Preview feature may appear as a distractor. Check
  the doc page for a Preview banner, or *(Preview)* beside the feature, before keying it. The one exception is a
  product the guide itself names (Gemini Cloud Assist); its Preview extensions still don't count.

## Multiple-select and cross-domain questions

The exam mixes multiple-choice and multiple-select items, and many of its scenarios need more than one section of the
guide. The bank has both.

- **Multiple select.** Four or five options, two or three of them correct (`"correct_answer": "A,D"`), and at least
  two wrong. The stem ends with "(Choose two.)" or "(Choose three.)", in words, and only a multiple-select stem says
  it. Each correct option must be needed: if one correct option alone would meet the stem, it's a single-answer
  question. The correct options are separate actions or facts, not two halves of one sentence, and the wrong options
  do not pair off into an obvious couple. "Choose three" needs five options. Every correct option's rationale starts
  with "Correct."; the others say why they fail. A pick scores only when every letter matches, as on the exam.
  Single-answer questions keep exactly four options.
- **Cross-domain.** `also_tests` lists the other guide objectives the scenario needs, at least one in another section.
  The question's own `objective` and `subtopic` are the decision it ends on, and it counts in that section's share.
  An objective belongs in `also_tests` only when the reader needs its knowledge to reach the key or to rule out an
  option: a reader who knows the question's own objective alone must not be able to answer. Naming a product from
  another section is not enough.
  Cross-domain questions are `certifying_only` and use ids `ace-x-NNN`; five are drawn into each 50-question exam.
- **Ids and GUIDs.** Every question has a readable `id` and a random `uid` (a GUID) that never changes.

## Growing the bank

Questions are added in planned runs (`/expand 10%` in Claude Code, or the `kb.py` commands by hand). The plan and the
gates are code, so that the author, a person or a model, decides only what a question says.

1. **Plan** (`kb.py plan`). The run's size is a count or a share of the bank. By default the new questions go to the
   sections furthest below their exam weight (20/30/30/20), then to the objectives furthest below their share of the
   section, then to the subtopics with the fewest questions per guide bullet. The bank moves toward the exam's
   proportions and no section overshoots. `--balance batch` splits the run itself by the exam weights, and
   `--balance current` grows every section by the same percentage. A tenth of a run is cross-domain, as in a
   50-question exam, and a tenth is multiple-select, including about a third of the cross-domain questions. Each slot
   fixes the objective, the subtopic, the form and the key letter.
2. **Write** from the guide bullet and a documentation page read during the run, with the evidence sentence (AC5).
3. **Vet** (`kb.py vet`). The schema, the slot, the lint rules as errors, the distinctness limits of AC7, and the
   evidence quote against the live page. A page that mentions Preview raises a warning to check against AC7.
4. **Solve blind** (`kb.py blind`). A second solver answers from the stem and options alone (AC4). The record is tied
   to the wording: an edit to the stem or an option voids it.
5. **Accept** (`kb.py accept`). Runs every check again and adds the whole batch or nothing. It mints the ids and
   writes the run's ledger, `docs/reviews/expand-YYYY-MM-DD.json`.
6. **Teach.** A fact the theory does not have is added to its page (AC5).

A slot that cannot be filled honestly is skipped with a reason. The run then ends smaller than planned, which is the
intended result: the plan is a target and the gates are the limit.

## How a reviewed question changes

- **Keep the id when the decision tested and the correct option stay the same, under the same letter.** Wording,
  constraints, distractors, rationales, the command and the doc link may all change.
- **Mint a new id when the decision or the correct option changes.** Retire the old id rather than reusing it, so
  attempt history never points at a different question. Retired ids are listed in `data/retired.json`, and `kb.py add`
  never mints one of them.
- A question that cannot be fixed without becoming a different question is removed, and the subtopic is checked
  against `kb.py blueprint --min 3 --strict`.

## Review record

Every reviewed question gets one entry in a ledger. The November 2026 review of the whole bank is
`docs/reviews/2026-11-bank-review.json`; each expansion run adds its own `docs/reviews/expand-YYYY-MM-DD.json`.

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
An entry written by `kb.py accept` has the verdict `new` and two more fields: `evidence` (the `doc_ref` and the quoted
sentence) and `blind_solve` (the solver's answer and whether it agreed with the key).
`scripts/review_report.py` turns the ledger into a readable report. For each question that changed, it shows the
original against the refined version, the audit against the seven criteria, and the final question.
