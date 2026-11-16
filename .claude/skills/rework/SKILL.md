---
name: rework
description: Replace questions the user has already seen with new ones, so they come back into the certifying draw as unseen, such as "/rework 50" or "/rework 3 --id ace-s2-004". Takes the questions seen longest ago from the attempt history, writes for each a new scenario with a different correct answer on the same subtopic (some cross-domain or multiple-select), proves every key with a quoted documentation sentence, has each one solved blind by a second agent, then adds the replacement and retires the old id. Use only when the user asks to rework, refresh, repair or recycle seen questions.
argument-hint: "<N> [--id ID ...] [--cross-share 0.6] [--multi-share 0.1] [--dry-run]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob, Agent, WebSearch, Bash(.venv/bin/python scripts/kb.py *), Bash(.venv/bin/python scripts/build_study_links.py), Bash(.venv/bin/pytest *), Bash(git status *), Bash(git diff *), Bash(git branch *), Bash(git checkout -b rework/*), Bash(git add *), Bash(git commit *), Bash(date *), Bash(ls *), Bash(mkdir -p build/rework/*)
---

# /rework: replace seen questions with new ones

Request: `$ARGUMENTS`

The simulator remembers every question id the user has answered and draws unseen ones first. A question that has been
seen is used up. This skill writes a **replacement** for each such question: same subtopic, new scenario, different
correct answer, new id. The old id is retired, so the replacement is unseen and returns to the draw.

People use this bank to decide whether they are ready for a real exam, so **one wrong answer key does more harm than
ten questions left as they are**. The tools below make most decisions for you. Your job is to write sound questions
and to stop when you cannot.

Use `.venv/bin/python` for every command. If `.venv` is missing, create it as `CLAUDE.md` says.

**One command per Bash call, written as shown here.** No `&&`, `;`, pipes, `head`, redirects or inline Python: the
commands in this file are approved in advance, and anything joined to them needs an approval that an unattended run
cannot get. To look inside the bank use `kb.py search "term"`, `kb.py list --subtopic "name" -v` and `kb.py show ID`;
to look inside the theory use the Grep tool. If a command from this file is refused, stop and report which one.

## Six rules that override everything else

1. **No exam content.** Write only from the exam guide bullet and the documentation page you read in this run. Never
   write a question you remember from a real exam, a dump, a practice test, a course quiz or Google's sample
   questions. If a question you are drafting feels remembered rather than built, drop it and build another.
2. **No fact from memory.** Google Cloud changes and your memory of it is out of date. Every key rests on a sentence
   you read with `kb.py doc` in this run. If you cannot find the page or the sentence, skip the slot.
3. **Only `kb.py accept` writes the bank.** Never edit `<bank>/sections/*.json`, `<bank>/register.json`,
   `<bank>/retired.json` or `data/study_links.json` by hand (`<bank>` is `banks/private/`, or `$ACE_BANK_DIR`). Never remove a question yourself: `accept` retires the old
   one in the same write that adds its replacement.
4. **Never weaken a gate.** Do not change a planned key, a slot, a blind-solve record, a threshold, a test or the
   standard to get a question through. Do not swap the key letter after a blind solver disagrees. When a replacement
   cannot pass honestly, skip the slot with a reason. A skipped slot is a normal result: the old question stays.
5. **Private files stay private.** Never read, quote or commit `data/history.json`, `reports/`, `private/` or
   `scripts/retro_content.py`. `kb.py rework` reads the history for you and gives you question ids only. Do not write
   in any file, commit message or report *why* these questions were chosen beyond "reworked": no dates of attempts, no
   scores, no "the user got this wrong".
6. **A rework is a new question, not a paraphrase.** New company names, new numbers or shuffled options on the same
   scenario are worthless: the user remembers the answer. The tools reject a replacement whose correct option is the
   old one, that reuses more than one old option, or whose stem is close to the old stem.

## Step 0. Set up the run

1. Read `docs/question-standard.md` from start to end. It is the definition of a good question; this skill is only
   the procedure. Then read `CONTRIBUTING.md`, section "The one rule that cannot bend".
2. Read the request. The first word is the count, for example `50`. `--dry-run` is for you (see the end of this
   file). Every other option goes to `kb.py rework` unchanged. If there is no count, print the usage line from this
   skill's `argument-hint` and stop.
3. Look for a run to resume: `ls build/rework`. For the newest directory that has a `plan.json`, run
   `.venv/bin/python scripts/kb.py slots build/rework/<dir>/plan.json`. If slots are open, that directory is `RUN`:
   **resume it** from Step 1, do not plan again, and skip point 4.
4. For a new run only: run `git status --short`. If files under `data/` or `theory/` are modified,
   stop and tell the user. Then choose the run directory `build/rework/<today's date>` and call it `RUN`. If it
   already holds a finished plan, use `RUN-2`, `RUN-3`, and so on.
5. Plan:

   ```bash
   .venv/bin/python scripts/kb.py rework 50 --out RUN/plan.json     # the count and options from the request
   ```

   Show the user the table it prints. Do not ask for confirmation, and do not edit the plan.

The plan lists **slots**, the question seen longest ago first. Each slot names the question it `replaces` and fixes
the objective and subtopic (the old question's), the form (single answer, or multiple select), whether it is
cross-domain, and the letter of the correct answer. Slots come in **batches** of eight.

## Step 1. Work one batch at a time

Repeat steps 1.1 to 1.6 until `kb.py slots` says the run is complete. Accept batches in order.

### 1.1 See the batch

```bash
.venv/bin/python scripts/kb.py slots RUN/plan.json
```

For each slot it prints the old question in full, with `*` on its key, and what it tested. Then, for each subtopic,
every question the bank already has there.

### 1.2 Choose what each replacement asks

Work through these recipes **in this order** and take the first one the documentation supports. All of them keep the
slot's subtopic and guide bullet.

1. **Flip the deciding fact.** Keep the kind of decision the old question asked, and change the one fact that decides
   it, so that *a different option wins*. Often an old wrong option becomes the answer. Example: the old stem needed
   the lowest cost for data read once a year, and Archive won; the new stem reads the data every week for a month
   and then never, and a lifecycle rule to Coldline wins. Reuse at most one old option; write the others new.
2. **Change the direction.** The old question chose what to build: ask what to do when it exists and misbehaves (a
   symptom, an error, a failed rollout). Or the reverse.
3. **Ask the neighbouring decision.** Another choice under the same guide bullet that neither the old question nor
   the "Already in the bank" list asks: another role, setting, tool or next step.
4. **For a multi-topic slot,** take recipe 1, 2 or 3 and build the scenario so that a fact from the partner
   objective is needed to rule out a wrong option (see "Multi-topic slots" below).

Then check the result against the "Already in the bank" list, exactly as for any new question:

- **Good:** a decision nobody asks, or the same decision as an existing question with a *different deciding fact*.
- **Never:** the same decision and the same deciding fact as any existing question, in other words.

Before reading any documentation, run `kb.py search "term"` for the product, role or feature you plan to key. The
"Already in the bank" list shows one subtopic; the same decision often sits in another one, and `vet` will reject
your question for it after you have done the work.

A question retired earlier in this run no longer covers its decision. That decision is open again for a later slot,
but with a new deciding fact: the user has seen the old scenario.

If every recipe leads to a restatement of an existing question, or you cannot find documentation for any of them,
skip the slot.

### 1.3 Read the documentation first, then write

Find the page that settles the decision. Good starting points, in this order:

1. The `doc_ref` of the old question or of a neighbour: `.venv/bin/python scripts/kb.py show ace-s4-012`.
2. The theory: `Grep` the term in `theory/*.md`. The page teaches the topic and often names the product page.
3. `WebSearch` for the term with `site:docs.cloud.google.com`.

Read the page as plain text, never from memory and never through a summary:

```bash
.venv/bin/python scripts/kb.py doc https://docs.cloud.google.com/iam/docs/creating-custom-roles --find "organization level"
.venv/bin/python scripts/kb.py doc https://docs.cloud.google.com/iam/docs/creating-custom-roles      # the page from the top
```

- Copy **one sentence, word for word,** that proves the correct answer. It is the question's `evidence`. A tool
  checks later that this sentence is on the `doc_ref` page, so do not tidy or shorten it in the middle. Copy from one
  printed line only: a quote that runs across two lines, a list item or a table cell will not match. Choose the
  sentence that states the deciding fact itself. A sentence that only mentions the feature proves nothing.
- The old question's explanation is not evidence. Its key was reviewed, but your new key is a different fact: read
  the page for it.
- If the command prints `[PREVIEW MENTIONED]`, read that passage. If the feature your key needs is in Preview, choose
  another decision. A Preview feature may be a wrong option, never the answer (AC7).
- An overview page can describe a Preview feature without saying so. Before keying a feature you have not seen in
  the bank, open that feature's own how-to page and look for a Preview banner at the top.
- If a wrong option depends on a fact you are not sure of, read its page too.
- When the options are IAM roles, read the description of every role you list. A wrong option that also holds the
  needed permission is a second correct answer; replace it.

Write the replacement to **version 2** of `docs/question-standard.md`, whatever the old question's standard: exact
role IDs and commands where the bullet is about access or a task, most scenarios across two or more areas of the
guide, associate-level migration scenarios in scope, close sibling options, and every identifier in backticks. Then
write the question **in this order**. The order prevents the usual defects.

1. **The fact:** the evidence sentence, and in your own words what it means.
2. **The decision and the correct option:** short and plain. Name the product, the exact role ID (`roles/…`), the
   exact command or the action. An option says what to do and stops: no "so that…", "because…" or "which lets…"
   clause. Reasons belong in the rationales.
3. **Three wrong options** (four for a multiple-select slot, which has five options and two correct). Each one is a
   real product, role, permission, setting or command. **At least two are close siblings of the key**: the next role
   in the same family, another verb or flag in the same command group, the same feature at another scope, the same
   service in another mode. The reader must need the stem's deciding fact to separate them. For each, write down the
   fact in the scenario that makes it wrong. Each needs its **own** reason; if two fail for the same reason, replace
   one. Pick the **tempting sibling**: the one a half-prepared reader would choose.
4. **The stem:** a newly invented company (not the old question's), what exists (on premises or in Google Cloud),
   what is needed, and every fact from points 2 and 3 that decides the answer. 25 to 130 words; migration and
   architecture scenarios may use the upper half. The last sentence is one direct question. A multiple-select stem
   ends with `(Choose two.)`.
5. **Do not reuse the old option list.** When the old options are bare product names ("Bigtable", "Spanner"), write
   yours as what the product is used for here ("Bigtable for the order history"); two or more options identical to
   the old ones are rejected.
6. **Place the options** so that the correct one sits on the slot's letter. Then make the options alike: same
   grammatical form, similar length. The correct option must not be the longest; lengthen a wrong option with a true
   detail rather than padding it.
7. **The explanation:** `summary` states the mechanism. `option_breakdown` has one rationale per option: the correct
   one starts with `Correct.`, each wrong one says why it fails *in this scenario*, in a sentence not used elsewhere.
   Do not copy a rationale from the old question.
8. **`gcloud_command`:** a real command that carries out the answer, taken from the documentation, or a console path
   written as `# Console > IAM & Admin > Roles > Create role`. Copy the command or the menu labels from a page you
   read; do not compose them from memory.
9. **`title`** (under 60 characters, a label, no final full stop, different from the old title), **`summary`** (one
   sentence: the single idea tested), **`tags`** (two to five, lowercase, hyphenated).
10. **The problem-first fields:** `"standard": 2`; `decided_by`, the one to three phrases of the stem that settle the
   key, copied exactly; `step`, the one reasoning step in 20 words or fewer, as a question and its answer;
   `trap`, `{"option": "<the tempting sibling's letter>", "why": "<one sentence on why it fails here>"}`.
11. **Backticks:** every role ID, permission, command, flag, condition expression, API name and resource name in the
   stem, the options and the rationales is in backticks. Product names stay prose.

**Multiple-select slots.** Five options A to E, two correct, on the letters the slot gives (`"correct_answer": "A,D"`).
The two correct options are two separate actions or facts that are *both* needed; if one alone would satisfy the stem,
the question is broken. Do not write them as two halves of one sentence, and do not let two wrong options pair off as
an obvious couple.

**Multi-topic slots** (most of a run). The scenario needs knowledge from the slot's objective *and* from an objective
in another section: put those in `"also_tests": ["4.2"]`. The slot's own objective is the decision the question ends on. The
test is this: a reader who knows only the slot's objective cannot rule out every wrong option. Mentioning another
product is not enough. The slot suggests a partner objective; use another one if it gives a more natural scenario.

### 1.4 Check your own work, then write the batch file

Before a question goes into the file, answer these honestly. A "no" means rewrite or skip.

- Would someone who remembers the old question and its answer still have to think? (If they could answer by
  recalling the old key or by avoiding it, rewrite.)
- Could a careful engineer defend a second option under an assumption the stem does not rule out?
- Does the stem state every fact needed, including network facts (external IP, Cloud NAT, which VPC or project)?
- Is every option real? No invented flag, role, permission, command or feature. Every role ID and `gcloud` command
  is spelled exactly as its reference page spells it; `vet` checks them, and a `kubectl`, `bq` or `gsutil` command
  needs its page in `"identifier_refs": {"<command>": "<url>"}`.
- Are at least two distractors close siblings of the key, so that no option falls without the deciding fact?
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
    "standard": 2,
    "decided_by": ["…exact phrase of the stem…"],
    "step": "…the one reasoning step…",
    "trap": {"option": "B", "why": "…why the tempting sibling fails here…"},
    "evidence": "One sentence copied word for word from the doc_ref page."
  },
  {"slot": 4, "skip": "Every decision the documentation supports on this bullet is already asked."}
]
```

`objective` and `subtopic` are the slot's exact strings. Add `"also_tests"` only on a multi-topic slot. Do not add
`id`, `uid`, `domain`, `source`, `replaces` or `blind`; the tools set them.

### 1.5 Vet, then have it solved blind

```bash
.venv/bin/python scripts/kb.py vet RUN/batch-01.json --plan RUN/plan.json
```

- Fix every **error** in the question itself and run it again. If the same question still has errors after three
  rounds, replace it with a skip entry.
- `rework-answer`, `rework-options` and `rework-stem` mean the replacement is too close to the question it replaces:
  go back to step 1.2 and take another recipe. Rewording does not fix them.
- `stem-overlap` with *another* question means the scenario resembles that one: make it a different situation.
- Read every **warning**. `same-decision` and `same-idea` mean an existing question is close: confirm that a different
  fact decides yours, or rewrite. `preview` means the page mentions Preview: confirm the key does not need that feature.

When there are no errors, print the blind sheet:

```bash
.venv/bin/python scripts/kb.py blind RUN/batch-01.json
```

Start **one new agent** with the Agent tool, `subagent_type: ace-blind-solver`. Its prompt is the blind sheet, copied
exactly as printed, and nothing else: no key, no title, no hint, no file path, no mention of the old questions. (If
that agent type does not exist in this session, use a `general-purpose` agent and put the instructions from
`.claude/agents/ace-blind-solver.md` above the sheet.) Wait for its reply. Then record its answers exactly as it gave
them:

```bash
.venv/bin/python scripts/kb.py blind RUN/batch-01.json --answers 3:C 5:A,D 6:B --by-form 3:- 5:- 6:D
```

`--by-form` records the solver's "Ruled out by form" line for every question: its letters, or `-` for none. A
standard-2 question cannot be accepted without it.

A question needs work in four cases: the command prints `DISAGREE`; the solver's "Also defensible" line names an
option; its "Ruled out by form" line names an option (replace that option with a closer sibling of the key); or its "Problems" line says the reader needs a fact the stem does not give, or that an option is not real. Do
not argue such a report away. A remark that is only editorial does not block the question: fix it if the fix is one
phrase, and list the remark in your final report either way. For every question that needs work:

1. Read the documentation again with `kb.py doc`. Decide who is right from the page, not from confidence.
2. If your key was wrong, or two options are both right, rewrite the question or skip the slot.
3. If your key was right but the stem let another option through, add the fact that rules it out.
4. Run `kb.py vet` again, then `kb.py blind` with a **new** agent for the changed questions. Recording answers for a
   few slots keeps the earlier records of the others. To save a round, changed questions may go on the same sheet as
   the next batch's questions.
5. A second disagreement on the same question means skip it.

Any edit to a stem or an option after a blind solve cancels that question's record, and `accept` will refuse it.

### 1.6 Accept the batch, then teach its facts

```bash
.venv/bin/python scripts/kb.py accept RUN/batch-01.json --plan RUN/plan.json
```

The ledger defaults to `<bank>/reviews/<mode>-<plan date>.json`, the same file for every batch of the run. It quotes the questions, so it stays with the bank, outside git. `accept` checks everything
again against the live documentation pages. It adds all of the batch or none of it. For each question added it
removes the question that slot replaces, lists the old id in `<bank>/retired.json`, and records both in the ledger. It
prints the new ids and the retired ids.

Then, for each question added: `Grep` the fact behind its key in `theory/*.md`. If no page teaches it, add one or two
sentences to the section of the page where it belongs, in the page's own style. Do not add or rename headings. Mark a
number or a limit that may change with *verify*. After editing any theory page, run
`.venv/bin/python scripts/build_study_links.py`.

## Step 2. Finish the run

1. Run the four gates. All must pass.

   ```bash
   .venv/bin/pytest -q
   .venv/bin/python scripts/kb.py check --strict
   .venv/bin/python scripts/kb.py lint
   .venv/bin/python scripts/kb.py blueprint --min 3 --strict
   ```

   If one fails, do not edit the bank by hand and do not commit. Report the output and stop.
2. The bank and its ledger are outside git: never `git add` them, and never quote a question into a tracked file.
3. If the run changed `theory/` or `data/study_links.json`, commit those, and do not push. If the current branch is
   `main`, first `git checkout -b rework/<date>`. Add only these paths: `data/study_links.json`, `theory`. Commit
   message: `Theory for /rework <request>`.
4. Report to the user:
   - the plan table;
   - each pair "old id → new id", marking cross-domain and multiple-select replacements, with one phrase on what
     changed (for example "flipped: now the lifecycle rule wins");
   - every skipped slot with its reason (those questions are unchanged and still count as seen);
   - every question that needed a rewrite after the blind solve, and any warning you accepted, with one line on why;
   - which theory pages changed;
   - the branch name, and that nothing was pushed.

## `--dry-run`

Do Steps 0 and 1.1 to 1.5 for the **first batch only**. Then run
`kb.py accept RUN/batch-01.json --plan RUN/plan.json --ledger RUN/ledger.json --dry-run`, which writes nothing. Do not
edit the theory or `CHANGELOG.md`, and do not commit. Report what would have been replaced.

## If you lose track

The state of a run is in files, not in your memory: `RUN/plan.json` holds every slot's status, and each
`RUN/batch-NN.json` holds the candidates. After a long run or a context reset, read this file again, run
`kb.py slots RUN/plan.json`, and continue with the batch it shows.
