# Question standard (version 2)

What a question in a bank must be before it ships. Every question is reviewed against the seven criteria below,
and a question that fails any of them is rewritten or removed. `python scripts/kb.py lint` checks the parts a
machine can check on the whole bank, and `python scripts/kb.py vet` applies stricter limits to a question before it is
added. The rest is a reviewer's judgement, recorded in the bank's review ledger (`<bank>/reviews/`, outside git).

A wrong key costs more than a missing question: someone decides whether to sit the exam on the strength of these
answers. When a question cannot be made sound, it is left out. **Quality comes before quantity**: a bank of fewer,
harder, sound questions is the goal, and the only floor is three questions per guide bullet.

The exam it prepares for is the Associate Cloud Engineer exam: an engineer who deploys, operates, migrates and
secures workloads on Google Cloud day to day. The bank imitates the *kind* of decision that exam asks for. It never
imitates its items: the no-exam-content rule in [CONTRIBUTING.md](../CONTRIBUTING.md) comes before everything here.

## What changed in version 2, and why

Version 2 comes from the report of a candidate who passed the exam in November 2026. The report describes the
**format and difficulty** of the items, never their content:

| The exam's items | Standard 1 said | Standard 2 says |
|---|---|---|
| used full IAM role IDs and concrete CLI commands with their flags and condition expressions, and knowing the exact name was the decision | options must not differ only by flags; test the decision, not the spelling | **Exact names are fair game** (AC1): options may differ by a role ID, a verb, a flag or a condition, and every one must be real (AC3) |
| mostly tested several areas at once, such as IAM, VPC and BigQuery in one scenario | about a tenth cross-domain, certifying-only | **Multi-topic by default** (AC1): at least 60% of questions set `also_tests`, and they are drawn in every mode |
| were often architecture or migration scenarios: an on-premises setup moving to Compute Engine or GKE | multi-step migrations are Professional-level, out of scope | **Associate-level migration is in scope** (AC1) |
| had options so close that guessing or eliminating by form did not work | distractors plausible, each wrong for its own reason | **Near siblings** (AC3): at least two distractors are close relatives of the key, and the blind solver reports any option it could rule out without the deciding fact (AC4) |
| printed commands and role IDs in a monospace font | (no rule) | **Identifiers in backticks** (AC6), which the app renders in monospace |

Version 2 also gives every question three **problem-first fields** (`decided_by`, `step`, `trap`), so the in-app
reveal, the retrospectives, the theory and the videos all teach from the same source (AC5).

Questions written to version 1 still load and carry `standard: 1` implicitly. `kb.py lint` reports the version 2 rules
on them as warnings. Every new question is written to version 2, which `kb.py vet` enforces, and the bank is reworked
to it over time.

## The seven criteria

### AC1. Associate scope and level

- The question ends on one decision an associate engineer makes at work: which resource, role, setting, command,
  tool or next step. It maps to one guide bullet through its `objective` and `subtopic` (`src/blueprint.py`). With no
  bullet there is no question.
- **One decision, many facts.** A stem that asks for two things is a multiple-select question or two questions. The
  facts that lead to the decision may come from several areas of the guide, and usually should.
- **Multi-topic by default.** At least 60% of a bank's version 2 questions set `also_tests`: the scenario cannot be
  answered without knowledge from another objective, at least one of them in another section. Typical pairings are an
  IAM grant inside a networking or data scenario, a VPC fact that decides a GKE or Cloud Run choice, or a logging or
  billing fact that decides an operations step. `kb.py lint` reports the share.
- **Judgement, not recall.** The reader reasons from the facts in the stem to the answer in about two minutes. A
  question that only asks what a product is, or which name belongs to a definition, is rewritten as a scenario.
- **Exact-name fluency is a decision.** When the guide bullet is about granting access or carrying out a task, knowing
  the exact predefined role, permission, command, flag or condition expression *is* what an associate engineer must
  know. Options may then differ by:
  - a role ID in the same family (`roles/iam.serviceAccountUser` against `roles/iam.serviceAccountTokenCreator`);
  - a verb or group in the same command tree (`gcloud projects add-iam-policy-binding` against
    `gcloud resource-manager folders add-iam-policy-binding`);
  - a flag or a condition expression (`--condition` with a `resource.name.startsWith(...)` expression against one on
    `request.time`).

  Two spellings that both work are not two options, and an option that differs only in argument order is not a
  distractor. The exact command still goes in `gcloud_command` as well, where it teaches.
- **Migration and modernisation at associate level are in scope**: rehosting on-premises VMs on Compute Engine,
  containerising a service onto GKE or Cloud Run, moving files, objects and databases into Google Cloud, and the
  networking, identity and operations work around a cutover. The decision is still an associate one: which service,
  setting, role or step, under constraints the stem gives. Out of scope: org-wide landing-zone design, multi-year
  migration programmes, and trade-offs that need numbers the stem does not give.
- **No key rests on a volatile number.** A price, a quota value or a limit that Google changes may appear in the
  stem as a given, but the answer never depends on remembering it. A stable documented property that the theory
  teaches, such as a storage class's minimum storage duration, is fair.

### AC2. A complete, self-contained scenario

- The stem gives every fact the answer depends on: what already exists (on premises or in Google Cloud), what has been
  tried, and the constraint that decides, such as cost, overhead, security, availability, time or least privilege.
- **Name the product.** Write "GKE cluster", "Dataproc cluster", "managed instance group" or "Cloud SQL for MySQL
  instance", never a bare "cluster", "group" or "database" when more than one product would fit.
- A comparative word such as "best", "fastest" or "cheapest" appears only together with the criterion that settles it:
  "with the least operational overhead", "at the lowest storage cost for this access pattern" or "following
  Google-recommended practice" (the last only when a documented recommendation exists).
- State access patterns and quantities without double meanings. "Each file is read once, a month after it is written"
  is clear; "read once at the start of each month" can be read two ways.
- Network facts that change the answer are stated: external IP or not, Cloud NAT or not, hybrid connectivity or not,
  and which VPC, region or project.
- The constraint comes first and the stem ends with one direct question. The reader should know what is being asked
  without reading the options.
- **The deciding words are recorded.** `decided_by` quotes, exactly, the one to three phrases of the stem that settle
  the key ("forbids key files on disk", "only the access it needs"). If no phrase settles it, the stem is missing a
  fact.
- Length: about 25–130 words; `kb.py vet` holds a new stem to that range. Architecture and migration scenarios use the
  upper half, and a stem never pads. Use invented company names only.

### AC3. Plausible, technically sound, close distractors

- Each wrong option is a real product, role, permission, setting or command that a reader who has skimmed the docs
  could choose.
- **Near siblings.** At least two distractors are close relatives of the key: the same product family, the next role
  in the same hierarchy, another verb or flag in the same command group, the same feature at another scope (project
  against folder against organization), or the same service in another mode (Autopilot against Standard). The
  reader should need the deciding fact to separate them. `kb.py lint` warns when it finds fewer than two siblings; the
  blind solve is the real test (AC4).
- **The tempting sibling is named.** `trap` names the distractor a half-prepared reader picks and says, in a sentence,
  why it fails *here*. It must be one of the wrong options.
- **No invented flags, commands, roles, permissions or features.** Every identifier in a stem or an option must exist
  as written. `kb.py vet` checks each role ID and permission against the IAM roles reference, and each `gcloud`
  command and flag against the gcloud reference. `kubectl`, `bq` and `gsutil` commands are checked by hand, or by the
  page given in `identifier_refs`.
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
- An option names the choice and stops. It does not argue for itself with "so that…" or "because…": the reasons
  belong in the rationales, and an option that explains itself reads as the key.

### AC4. Exactly one correct answer

- Under the stem's stated facts, exactly one option is right by current Google Cloud documentation. Each other option
  is wrong for a reason that can be stated in the stem's own terms.
- An option that would also work under an assumption the stem does not rule out is a defect. Add the fact that rules
  it out, or replace the option.
- Avoid negatives. If one is needed, write it in capitals ("Which option does NOT…") and use it sparingly.
- **The blind-solve test.** A second solver who sees only the stem and the options, without the key, the title or the
  rationales, reaches the same answer and can defend no other option. It also reports every option it could rule out
  **without** the deciding fact, by form, by an absolute word or by general knowledge: such an option is too far from
  the key, and is replaced by a closer sibling. A disagreement is settled from the documentation: the stem gains the
  fact that was missing, or the question goes. The key letter is never moved to match the solver. Every question added
  in bulk passes this test before it enters the bank ([Growing the bank](#growing-the-bank)).

### AC5. An explanation that teaches

- `explanation.summary` states the mechanism that makes the answer right. It does more than repeat the correct option.
- `option_breakdown` has a rationale for every option. The correct one starts with "Correct." and the others say
  specifically why they fail *in this scenario*. A rationale copied from another question, or one written for a
  different scenario, is a defect.
- **The problem-first fields** carry the teaching format that retrospectives, theory and videos use
  ([#18](https://github.com/nirmata78/gcp-ace-simulator/issues/18)):

  | Field | Shown as | Rule |
  |---|---|---|
  | `decided_by` | the stem with those words highlighted | 1–3 exact phrases of the stem |
  | `step` | **Decided by:** the one reasoning step | 20 words or fewer, a question and its answer ("Where does the code run? On Google Cloud, so attach.") |
  | the key | **Answer** | |
  | `trap` | **Tempting sibling:** the option, and why it fails | `{"option": "B", "why": "…"}`, a wrong option |

- `gcloud_command` is a real, current command that carries out the right answer, or a console path written as
  `# Console > …`.
- `doc_ref` links to the current page (`docs.cloud.google.com` or `cloud.google.com`) that proves the answer, and the
  page has been read.
- **Evidence.** A new question is recorded with the sentence on its `doc_ref` page that proves the key, copied word
  for word. `kb.py vet` and `kb.py accept` fetch the page and reject a quote that is not on it. This is what "the page
  has been read" means for a question written by a model: a key that cannot be tied to a sentence is not added.
- Every fact a question relies on is taught in `theory/`. If it is not, the theory page gets it too.

### AC6. Fair form

- **Identifiers are code.** Role IDs, permissions, `gcloud`/`kubectl`/`bq`/`gsutil` commands, flags, condition
  expressions, API names (`compute.googleapis.com`), metric types and resource names are written in backticks in the
  stem, the options and the rationales, as the exam prints them in monospace. Product names ("Cloud Run", "GKE") are
  prose, not code. `kb.py lint` reports a bare identifier (`ident-unformatted`): a warning on a version 1 question, an
  error on a version 2 one.
- The answer key is spread evenly across A–D across the bank: each letter is the key in 20–30% of single-answer
  questions, and no letter is in more than about half of the multiple-select keys. `kb.py lint` reports the spread.
  In a planned run the letter is fixed before the question is written, so the spread does not depend on the
  author's habits.
- No grammatical or wording cues: the stem's articles and plurals fit every option, and only the correct option
  repeats the stem's wording when another option could too.
- No trick wording, double negatives or traps that depend on a detail buried at the end of the stem. A close sibling
  is not a trick: it is separated by a fact the stem states plainly.

### AC7. Original, distinct and current

- Written from the exam guide and product documentation, never from a remembered exam item, a dump or a practice test
  (`CONTRIBUTING.md`). A candidate's report of the exam's *format* (this standard's version 2) is not exam content; a
  recalled scenario, option set or wording is, and is never used. New questions have `source: curated`, and each new
  stem must score below the overlap thresholds of `scripts/audit_overlap.py` against every audited source.
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

## Multiple-select and multi-topic questions

- **Multiple select.** Four or five options, two or three of them correct (`"correct_answer": "A,D"`), and at least
  two wrong. The stem ends with "(Choose two.)" or "(Choose three.)", in words, and only a multiple-select stem says
  it. Each correct option must be needed: if one correct option alone would meet the stem, it's a single-answer
  question. The correct options are separate actions or facts, not two halves of one sentence, and the wrong options
  do not pair off into an obvious couple. "Choose three" needs five options. Every correct option's rationale starts
  with "Correct."; the others say why they fail. A pick scores only when every letter matches, as on the exam.
  Single-answer questions keep exactly four options. About a tenth of a planned run is multiple-select.
- **Multi-topic.** `also_tests` lists the other guide objectives the scenario needs, at least one in another section.
  The question's own `objective` and `subtopic` are the decision it ends on, and it counts in that section's share.
  An objective belongs in `also_tests` only when the reader needs its knowledge to reach the key or to rule out an
  option: a reader who knows the question's own objective alone must not be able to answer. Naming a product from
  another section is not enough.
  - *Version 2*: a multi-topic question is an ordinary question. It keeps a section id (`ace-s3-NNN`) and is drawn in
    Learning mode and in certifying exams by its own objective.
  - *Version 1* (legacy): a cross-domain question is `certifying_only`, has an `ace-x-NNN` id, and five are drawn into
    each 50-question exam from a reserved quota.
- **Ids and GUIDs.** Every question has a readable `id` and a random `uid` (a GUID) that never changes.

## An example of the version 2 form

The fields only. This is an illustration of the form, not a question for any bank:

```json
{
  "standard": 2,
  "objective": "4.2", "subtopic": "Service Account Permissions and Impersonation", "also_tests": ["1.2"],
  "question": "… a developer must run `gcloud` commands as the service account `deployer`, without any key …",
  "options": {"A": "Grant `roles/iam.serviceAccountTokenCreator` to the developer on `deployer`",
              "B": "Grant `roles/iam.serviceAccountUser` to the developer on `deployer`", "C": "…", "D": "…"},
  "correct_answer": "A",
  "decided_by": ["as the service account `deployer`", "without any key"],
  "step": "A person borrowing an identity? Then impersonation, which mints a token.",
  "trap": {"option": "B", "why": "Service Account User attaches the account to a resource but cannot mint a token."}
}
```

## Growing the bank

Questions are added in planned runs (`/expand 10%` in Claude Code, or the `kb.py` commands by hand). The plan and the
gates are code, so that the author, a person or a model, decides only what a question says.

1. **Plan** (`kb.py plan`). The run's size is a count or a share of the bank. By default the new questions go to the
   sections furthest below their exam weight (20/30/30/20), then to the objectives furthest below their share of the
   section, then to the subtopics with the fewest questions per guide bullet. `--balance batch` splits the run itself
   by the exam weights, and `--balance current` grows every section by the same percentage. **60% of a run is
   multi-topic** and a tenth is multiple-select. Each slot fixes the objective, the subtopic, the form and the key
   letter.
2. **Write** to version 2 from the guide bullet and a documentation page read during the run, with the evidence
   sentence (AC5), the problem-first fields, and every identifier in backticks.
3. **Vet** (`kb.py vet`). The schema and the version 2 fields, the slot, the lint rules as errors, the distinctness
   limits of AC7, the evidence quote against the live page, and every role, permission and `gcloud` command against
   its reference page. A page that mentions Preview raises a warning to check against AC7.
4. **Solve blind** (`kb.py blind`). A second solver answers from the stem and options alone (AC4) and reports the
   options it ruled out without the deciding fact (`--by-form`). The record is tied to the wording: an edit to the
   stem or an option voids it.
5. **Accept** (`kb.py accept`). Runs every check again and adds the whole batch or nothing. It mints the ids and
   writes the run's ledger, `<bank>/reviews/expand-YYYY-MM-DD.json`, which stays with the bank, outside git.
6. **Teach.** A fact the theory does not have is added to its page (AC5).

A slot that cannot be filled honestly is skipped with a reason. The run then ends smaller than planned, which is the
intended result: the plan is a target and the gates are the limit.

## Reworking questions

A question is replaced, not reworded (`/rework 50` in Claude Code, or `kb.py rework` and the same commands as an
expansion). This is how a bank moves from version 1 to version 2, and how a question someone has seen comes back
unseen.

- `kb.py rework N` plans one slot for each of the N questions seen longest ago in the local attempt history, or for
  the ids given with `--id`. Only the ids leave the history. A slot keeps the old question's objective and subtopic,
  fixes a key letter other than the old one, and 60% of a run is multi-topic and a tenth multiple-select.
- The replacement is written, vetted, solved blind and accepted exactly as a new question is. `kb.py vet` adds three
  limits against the question it replaces: the correct option is a different one (`rework-answer`), at most one
  option is repeated (`rework-options`), and the stems share less than 33% of their content words (`rework-stem`).
- `kb.py accept` adds the replacement under a new id and, in the same write, removes the old question, lists its id
  in the bank's `retired.json`, and records both in `<bank>/reviews/rework-YYYY-MM-DD.json` (the old one as
  `removed`, with its `replacement_id` and original text). A skipped slot leaves its question in the bank unchanged.
- **Dropping is allowed.** A question that cannot be brought to version 2 may be removed without a replacement, as
  long as every guide bullet keeps three or more questions (`kb.py blueprint --min 3 --strict`).

## How a reviewed question changes

- **Keep the id when the decision tested and the correct option stay the same, under the same letter.** Wording,
  constraints, distractors, rationales, the command, the doc link and the problem-first fields may all change.
- **Mint a new id when the decision or the correct option changes.** Retire the old id rather than reusing it, so
  attempt history never points at a different question. Retired ids are listed in the bank's `retired.json`, and
  `kb.py add` never mints one of them.
- A question that cannot be fixed without becoming a different question is removed, and the subtopic is checked
  against `kb.py blueprint --min 3 --strict`.

## Review record

Every reviewed question gets one entry in a ledger in `<bank>/reviews/`. Ledgers quote the questions, so they stay
with the bank and out of git.

```json
{
  "id": "ace-s2-018",
  "verdict": "pass | revised | restored | removed | new",
  "ac": {"AC1": "pass", "AC2": "fail", "AC3": "pass", "AC4": "fail", "AC5": "pass", "AC6": "pass", "AC7": "pass"},
  "notes": "“Read once at the start of each month” also reads as one read per object, which makes Archive right.",
  "replacement_id": null
}
```

`restored` marks a question that was removed and brought back unchanged in decision and key, so it keeps its id.
An entry written by `kb.py accept` has the verdict `new` and more fields: `standard`, `evidence` (the `doc_ref` and
the quoted sentence) and `blind_solve` (the solver's answer, whether it agreed with the key, and `by_form`).
`scripts/review_report.py` turns a ledger into a readable report.
