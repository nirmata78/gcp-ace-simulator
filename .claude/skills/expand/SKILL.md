---
name: expand
description: Grow the ACE question bank by a planned amount, such as "/expand 10%" or "/expand 25". Plans where the new questions go (steering sections toward the exam weights), writes single-answer, multiple-select and cross-domain questions from the exam guide and Google Cloud documentation, proves every key with a quoted sentence, has each question solved blind by a second agent, adds the ones that pass, and commits them on a branch. Use only when the user asks to expand, grow or add a batch of questions to the bank.
argument-hint: "<N | N%> [--section N] [--objective X.Y] [--balance exam|batch|current] [--cross-share 0.1] [--multi-share 0.1] [--dry-run]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob, Agent, WebSearch, Bash(.venv/bin/python scripts/kb.py *), Bash(.venv/bin/python scripts/build_study_links.py), Bash(.venv/bin/pytest *), Bash(git status *), Bash(git diff *), Bash(git branch *), Bash(git checkout -b expand/*), Bash(git add *), Bash(git commit *), Bash(date *), Bash(ls *), Bash(mkdir -p build/expand/*)
---

# /expand: grow the question bank

Request: `$ARGUMENTS`

You are adding questions to a practice bank for the Google Cloud Associate Cloud Engineer exam. People use it to
decide whether they are ready for a real exam, so **one wrong answer key does more harm than ten missing questions**.
The tools below make most decisions for you. Your job is to write sound questions and to stop when you cannot.

Use `.venv/bin/python` for every command. If `.venv` is missing, create it as `CLAUDE.md` says.

**One command per Bash call, written as shown here.** No `&&`, `;`, pipes, `head`, redirects or inline Python: the
commands in this file are approved in advance, and anything joined to them needs an approval that an unattended run
cannot get. To look inside the bank use `kb.py search "term"`, `kb.py list --subtopic "name" -v` and `kb.py show ID`;
to look inside the theory use the Grep tool, or a plain `grep -n "term" theory/*.md` if there is no Grep tool. If a command from this file is refused, stop and report which one.

## Five rules that override everything else

1. **No exam content.** Write only from the exam guide bullet and the documentation page you read in this run. Never
   write a question you remember from a real exam, a dump, a practice test, a course quiz or Google's sample
   questions. If a question you are drafting feels remembered rather than built, drop it and build another.
2. **No fact from memory.** Google Cloud changes and your memory of it is out of date. Every key rests on a sentence
   you read with `kb.py doc` in this run. If you cannot find the page or the sentence, skip the slot.
3. **Only `kb.py accept` writes the bank.** Never edit `data/sections/*.json`, `data/register.json`,
   `data/retired.json` or `data/study_links.json` by hand.
4. **Never weaken a gate.** Do not change a planned key, a slot, a blind-solve record, a threshold, a test or the
   standard to get a question through. Do not swap the key letter after a blind solver disagrees. When a question
   cannot pass honestly, skip the slot with a reason. A skipped slot is a normal result.
5. **Private files stay private.** Never read, quote or commit `data/history.json`, `reports/`, `private/` or
   `scripts/retro_content.py`.

## Step 0. Set up the run

1. Read `docs/question-standard.md` from start to end. It is the definition of a good question; this skill is only
   the procedure. Then read `CONTRIBUTING.md`, section "The one rule that cannot bend".
2. Read the request. The first word is the amount: a share of the bank (`10%`) or a count (`25`). `--dry-run` is for
   you (see the end of this file). Every other option goes to `kb.py plan` unchanged. If there is no amount, print the
   usage line from this skill's `argument-hint` and stop.
3. Run `git status --short`. If files under `data/`, `theory/` or `docs/reviews/` are modified, stop and tell the
   user: the run commits those paths and must not mix in someone else's edits.
4. Choose the run directory: `build/expand/<today's date>`, for example `build/expand/2026-11-10`. Call it `RUN`.
   - If `RUN/plan.json` exists, run `.venv/bin/python scripts/kb.py slots RUN/plan.json`. If slots are open, **resume
     that run** from Step 1 and do not plan again. If none are open, use `RUN-2`, `RUN-3`, and so on.
5. Plan:

   ```bash
   .venv/bin/python scripts/kb.py plan 10% --out RUN/plan.json     # the amount and options from the request
   ```

   Show the user the table it prints. Do not ask for confirmation, and do not edit the plan.

The plan lists **slots**. Each slot fixes the objective, the subtopic, the form (single answer, or multiple select),
whether it is cross-domain, and the letter of the correct answer. Slots come in **batches** of eight.

## Step 1. Work one batch at a time

Repeat steps 1.1 to 1.6 until `kb.py slots` says the run is complete. Finish a batch before you start the next.

### 1.1 See the batch

```bash
.venv/bin/python scripts/kb.py slots RUN/plan.json
```

It prints each slot and, for each subtopic, every question the bank already has there: its id, title, what it tests
and its correct option.

### 1.2 Choose what each slot asks

For each slot, choose **one decision an associate engineer makes** under the slot's guide bullet. Compare it with the
"Already in the bank" list:

- **Best: a decision nobody has asked.** Another product choice, role, setting, tool or next step under the same bullet.
- **Acceptable: a variant.** The same decision as an existing question, but a *different fact decides it*: another
  constraint (cost, not availability), another state of the resource (it exists, or it has failed), another symptom,
  or the other direction (troubleshoot what is there, not choose what to build).
- **Never: a restatement.** The same decision and the same deciding fact with another company name, other numbers or
  other wording.

If the list already covers every decision and every variant you can support with documentation, skip the slot.

### 1.3 Read the documentation first, then write

Find the page that settles the decision. Good starting points, in this order:

1. The `doc_ref` of a neighbouring question: `.venv/bin/python scripts/kb.py show ace-s4-012`.
2. The theory: `Grep` the term in `theory/*.md`. The page teaches the topic and often names the product page.
3. `WebSearch` for the term with `site:docs.cloud.google.com`.

Read the page as plain text, never from memory and never through a summary:

```bash
.venv/bin/python scripts/kb.py doc https://docs.cloud.google.com/iam/docs/creating-custom-roles --find "organization level"
.venv/bin/python scripts/kb.py doc https://docs.cloud.google.com/iam/docs/creating-custom-roles      # the page from the top
```

- Copy **one sentence, word for word,** that proves the correct answer. It is the question's `evidence`. A tool
  checks later that this sentence is on the `doc_ref` page, so do not tidy or shorten it in the middle. Choose the
  sentence that states the deciding fact itself. A sentence that only mentions the feature proves nothing.
- If the command prints `[PREVIEW MENTIONED]`, read that passage. If the feature your key needs is in Preview, choose
  another decision. A Preview feature may be a wrong option, never the answer (AC7).
- If a wrong option depends on a fact you are not sure of, read its page too.

Then write the question **in this order**. The order prevents the usual defects.

1. **The fact:** the evidence sentence, and in your own words what it means.
2. **The decision and the correct option:** short and plain. Name the product, role or action. An option says what
   to do and stops: no "so that…", "because…" or "which lets…" clause. Reasons belong in the rationales.
3. **Three wrong options** (four for a multiple-select slot, which has five options and two correct). Each one is a
   real product, role, setting or command that solves a *neighbouring* problem. For each, write down the fact in the
   scenario that makes it wrong. Each needs its **own** reason; if two fail for the same reason, replace one.
4. **The stem:** an invented company, what exists, what is needed, and every fact from points 2 and 3 that decides the
   answer. 25 to 90 words. The last sentence is one direct question. A multiple-select stem ends with
   `(Choose two.)`.
5. **Place the options** so that the correct one sits on the slot's letter. Then make the four options alike: same
   grammatical form, similar length. The correct option must not be the longest; lengthen a wrong option with a true
   detail rather than padding it.
6. **The explanation:** `summary` states the mechanism. `option_breakdown` has one rationale per option: the correct
   one starts with `Correct.`, each wrong one says why it fails *in this scenario*, in a sentence not used elsewhere.
7. **`gcloud_command`:** a real command that carries out the answer, taken from the documentation, or a console path
   written as `# Console > IAM & Admin > Roles > Create role`. Copy the command or the menu labels from a page you
   read; do not compose them from memory. If the page gives neither, read the product's how-to page for it.
8. **`title`** (under 60 characters, a label, no final full stop), **`summary`** (one sentence: the single idea
   tested), **`tags`** (two to five, lowercase, hyphenated).

**Multiple-select slots.** Five options A to E, two correct, on the letters the slot gives (`"correct_answer": "A,D"`).
The two correct options are two separate actions or facts that are *both* needed; if one alone would satisfy the stem,
the question is broken. Do not write them as two halves of one sentence, and do not let two wrong options pair off as
an obvious couple.

**Cross-domain slots.** The scenario needs knowledge from the slot's objective *and* from an objective in another
section: put those in `"also_tests": ["4.2"]`. The slot's own objective is the decision the question ends on. The
test is this: a reader who knows only the slot's objective cannot rule out every wrong option. Mentioning another
product is not enough. The slot suggests a partner objective; use another one if it gives a more natural scenario.

### 1.4 Check your own work, then write the batch file

Before a question goes into the file, answer these honestly. A "no" means rewrite or skip.

- Could a careful engineer defend a second option under an assumption the stem does not rule out?
- Does the stem state every fact needed, including network facts (external IP, Cloud NAT, which VPC or project)?
- Is every option real? No invented flag, role, command or feature.
- Would the answer survive if the reader had never seen the option list (it tests judgement, not recognition)?
- Does the key avoid resting on a price, a quota value or anything marked *verify* in the theory?

Write `RUN/batch-01.json` (number it as the batch): a JSON list with one object per slot of the batch.

```json
[
  {
    "slot": 3,
    "title": "…",
    "objective": "4.1",
    "subtopic": "Role Types and Custom Roles",
    "summary": "…",
    "tags": ["iam", "custom-roles"],
    "question": "…",
    "options": {"A": "…", "B": "…", "C": "…", "D": "…"},
    "correct_answer": "C",
    "explanation": {
      "summary": "…",
      "option_breakdown": {"A": "…", "B": "…", "C": "Correct. …", "D": "…"},
      "gcloud_command": "…",
      "doc_ref": "https://docs.cloud.google.com/…"
    },
    "evidence": "One sentence copied word for word from the doc_ref page."
  },
  {"slot": 4, "skip": "The bank already asks each decision under bullet 4.1.3 that the documentation supports."}
]
```

`objective` and `subtopic` are the slot's exact strings. Add `"also_tests"` only on a cross-domain slot. Do not add
`id`, `uid`, `domain`, `source` or `blind`; the tools set them.

### 1.5 Vet, then have it solved blind

```bash
.venv/bin/python scripts/kb.py vet RUN/batch-01.json --plan RUN/plan.json
```

- Fix every **error** in the question itself and run it again. If the same question still has errors after three
  rounds, replace it with a skip entry.
- Read every **warning**. `same-decision` and `same-idea` mean an existing question is close: confirm that a different
  fact decides yours, or rewrite. `preview` means the page mentions Preview: confirm the key does not need that feature.
  `stem-overlap` means the scenario resembles another: make it a different situation.

When there are no errors, print the blind sheet:

```bash
.venv/bin/python scripts/kb.py blind RUN/batch-01.json
```

Start **one new agent** with the Agent tool, `subagent_type: ace-blind-solver`. Its prompt is the blind sheet, copied
exactly as printed, and nothing else: no key, no title, no hint, no file path. (If that agent type does not exist in
this session, use a `general-purpose` agent and put the instructions from `.claude/agents/ace-blind-solver.md` above
the sheet.) Wait for its reply. Then record its answers exactly as it gave them:

```bash
.venv/bin/python scripts/kb.py blind RUN/batch-01.json --answers 3:C 5:A,D 6:B
```

A question needs work when the command prints `DISAGREE`, **and also** when the solver's letter matches but its
"Also defensible" or "Problems" line says anything other than "none". Do not argue a report away. If the solver says
the reader must know a fact the stem does not give (a time window, a default, a limit), put that fact in the stem.
For every such question:

1. Read the documentation again with `kb.py doc`. Decide who is right from the page, not from confidence.
2. If your key was wrong, or two options are both right, rewrite the question or skip the slot.
3. If your key was right but the stem let another option through, add the fact that rules it out.
4. Run `kb.py vet` again, then `kb.py blind` with a **new** agent for the changed questions. Recording answers for a
   few slots keeps the earlier records of the others.
5. A second disagreement on the same question means skip it.

Any edit to a stem or an option after a blind solve cancels that question's record, and `accept` will refuse it.

### 1.6 Accept the batch, then teach its facts

```bash
.venv/bin/python scripts/kb.py accept RUN/batch-01.json --plan RUN/plan.json --ledger docs/reviews/expand-2026-11-10.json
```

Use the run's date in the ledger name, and the same ledger for every batch of the run. `accept` checks everything
again, including the evidence quotes against the live pages. It adds all of the batch or none of it, prints the new
ids, and marks the slots filled or skipped.

Then, for each question added: `Grep` the fact behind its key in `theory/*.md`. If no page teaches it, add one or two
sentences to the section of the page where it belongs, in the page's own style. Do not add or rename headings. Mark a
number or a limit that may change with *verify*.

## Step 2. Finish the run

1. Run the four gates. All must pass.

   ```bash
   .venv/bin/pytest -q
   .venv/bin/python scripts/kb.py check --strict
   .venv/bin/python scripts/kb.py lint
   .venv/bin/python scripts/kb.py blueprint --min 3 --strict
   ```

   If one fails, do not edit the bank by hand and do not commit. Report the output and stop.
2. Update the bank size in `README.md` (the badge near the top and the "A question bank of N items" line), and add one
   line under `## [Unreleased]`, `### Added` in `CHANGELOG.md`: how many questions, in which sections, how many
   cross-domain and multiple-select.
3. Commit, and do not push. If the current branch is `main`, first `git checkout -b expand/<date>`. Add only these
   paths: `data/sections`, `data/register.json`, `theory`, `docs/reviews/expand-<date>.json`, `README.md`,
   `CHANGELOG.md`. Commit message: `Bank N: M new questions (/expand <request>)`.
4. Report to the user:
   - the plan table, and the bank size before and after;
   - the new ids, by section, marking cross-domain and multiple-select ones;
   - every skipped slot with its reason;
   - every question that needed a rewrite after the blind solve, and any warning you accepted, with one line on why;
   - which theory pages changed;
   - the branch name, and that nothing was pushed.

## `--dry-run`

Do Steps 0 and 1.1 to 1.5 for the **first batch only**. Then run
`kb.py accept RUN/batch-01.json --plan RUN/plan.json --ledger RUN/ledger.json --dry-run`, which writes nothing. Do not
edit the theory, `README.md` or `CHANGELOG.md`, and do not commit. Report what would have been added.

## If you lose track

The state of a run is in files, not in your memory: `RUN/plan.json` holds every slot's status, and each
`RUN/batch-NN.json` holds the candidates. After a long run or a context reset, read this file again, run
`kb.py slots RUN/plan.json`, and continue with the batch it shows.
