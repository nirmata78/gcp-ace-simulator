# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
[RELEASE.md](RELEASE.md) explains what each kind of version bump means here.

## [Unreleased]

### Added

- **`/expand`: grow the bank by a planned amount.** `claude "/expand 10%" --model opus --effort high` plans where the
  new questions go, steering the sections toward the exam weights, and mixes in multiple-select and cross-domain
  questions. Each key is fixed in advance and proven by a sentence quoted from its documentation page; each question
  is answered blind by a second agent before it is added. New commands behind it: `kb.py plan`, `slots`, `doc`, `vet`,
  `blind` and `accept`.

- **69 new questions** (bank 786) on concepts that are often confused: Cloud NAT IP modes and regions, static and
  promoted addresses, DNS forwarding in both directions, BGP and Cloud Router ASNs, dynamic routing mode, GKE Pod
  ranges, implied firewall rules, separate projects and Shared VPC hosts per environment, Assured Workloads, Directory
  Sync and Entra ID provisioning, workforce pool members and sessions, service account undelete, HMAC keys, Cloud
  Scheduler tokens, log-based metrics, sinks, Managed Prometheus, Spot termination, Cloud Run revisions, storage classes
  and `bq load`. Three are cross-domain topology questions (`ace-x-076`…`ace-x-078`).
- **Theory:** five worked network blueprints with their build order and public addresses
  ([§4.13](theory/04-networking.md)), BGP in one page, the dynamic routing mode, secondary ranges and additional GKE Pod
  ranges (up to 170 per subnet), a production/non-production project blueprint, Assured Workloads in depth, GKE cost
  allocation, kubectl version skew, `bq load --replace`, and Spanner instance configurations.
- **Course video sources:** the new theory as slides, ten new diagrams, Cloud Console walkthroughs (`= shot` slides,
  screenshots kept locally in the gitignored `theory/video/shots/`), and a practice section at the end of every part.

### Changed

- **Question standard.** It now says what makes a question distinct (a new decision or a variant, never a
  restatement), requires quoted evidence and a blind solve for questions added in bulk, and adds rules on one decision
  per question, volatile numbers, distractors that each fail for their own reason, and what earns an `also_tests` entry.
- **A key never depends on a Preview feature.** The question standard (AC7) now says so, measured against Google Cloud
  in June 2026; Gemini Cloud Assist, which the guide names, is the one exception. Five questions whose keys relied on
  Preview features were retired and replaced (`ace-s1-043` liens, `ace-s1-047` Gemini in Billing, `ace-s2-085` the
  Gemini Cloud Assist MCP server, `ace-s3-127` Database Center on Compute Engine VMs, `ace-s4-053` Activity Analyzer),
  and the theory now tags those features *Preview*.

### Fixed

- `ace-s3-154` said a stopped VM keeps its IP addresses; it keeps its internal address, and the stem now says so.

## [1.2.0] - 2026-11-07

The question review of [issue #1](https://github.com/nirmata78/gcp-ace-simulator/issues/1), question formats the
real exam uses, and the in-app score report. Existing history keeps loading; nothing to migrate.

### Added

- **Multiple-select questions** ("Choose two"), as the real exam has them: checkboxes that lock once you've picked
  enough, scored only when every pick is right, in the app, the PDF report and `kb.py`. 57 in the bank.
- **75 cross-domain questions** (`ace-x-001`…`ace-x-075`) whose scenario needs two or three sections at once. They
  appear only in certifying exams, five in each 50-question exam, counted in their main section's share. The last 25
  are written in the style of Google's sample questions: a scenario, a stated constraint such as least privilege or
  minimal overhead, and options that are actions.
- **Certifying exams avoid questions you have already seen.** Every question of every recorded attempt counts as
  seen; the checkbox (on by default) draws only unseen questions, keeping the section split, and shows how many are
  left. A seen question comes back only when the bank has no unseen one.
- **The score report opens in the app** instead of a browser tab: your score against the pass line, sections, timing,
  where to study next, then each reviewed question with every option explained, the course's theory, the command,
  the tell to spot next time and links to read and rewatch. **Missed and flagged** or **Every question**, with
  **Download PDF report** for the same review as a PDF. A PDF copy is still saved to `reports/` on submission.
- Learning mode: drag the divider between the question and the study panel to resize it. Arrow keys work, a
  double-click resets it, and the browser remembers the width. Below 1000px the panel moves under the question; on a
  phone the navigation buttons show icons only.
- **Every question has a GUID** (`uid`) that never changes, alongside its readable id.
- A written [question standard](docs/question-standard.md), and `python scripts/kb.py lint`, which checks what a
  machine can of it (now also run in CI). `scripts/audit_overlap.py` repeats the provenance audit against local
  reference files.

### Changed

- **Every question was reviewed** against the question standard; 461 were revised and the review is recorded per
  question in `docs/reviews/2026-11-bank-review.json`. Answer options no longer give the answer away by length (the
  longest option was the key in 60% of questions; now 29%, near chance). Stems name the product they mean ("GKE
  cluster", not "cluster"), state the facts the answer depends on, and options describe a decision instead of a
  command line to spell. Template questions that shared distractors now have their own.
- **The 104 excluded questions are settled** (issue #1): 25 were rewritten from scratch as new questions and 79
  dropped. 33 of the 34 questions removed for resembling a public question set are back, each with its own scenario;
  the 34th duplicated another question. 29 new questions filled thin subtopics. The bank has 722 questions; every
  guide bullet still has at least three. Removed ids are never reused (`data/retired.json`).
- The layout fills the window, in Material 3 colours, shapes and type (also set as the Streamlit theme). The header
  and the navigation bar have fixed heights, so nothing is clipped, and the study panel fits between them and scrolls
  on its own. Type grows with the window, as browser zoom would: 16px on small screens, about 20px on a 1728px laptop,
  at most 24px. Answer options are set at the stem's size, stay readable after **Check answer**, and the right option
  (and a wrong pick) is marked in the list.
- Buttons: white on blue for the main action and blue on white for the others, with readable hover, pressed, focus
  and disabled states. The bottom bar's buttons are centred in it, with space between them.
- Downloads are built when you download: a PDF removed from `reports/` is rebuilt, and a failed build shows its error
  instead of an empty file. The review shows 10 questions at a time, with **Show more**.
- Theory: GKE can change a node pool's machine type in place (the nodes are recreated); the restricted and private
  Google API ranges; GKE maintenance-exclusion scopes; Cloud Run secrets as volumes versus environment variables; the
  IAP web-app role; the roles Pub/Sub dead-lettering needs.
- Requires Streamlit 1.66.1 or later (`pyproject.toml`).

### Fixed

- **Answer keys corrected** where a second option was also right or the key was wrong, among them `ace-dom2-021`
  (Coldline was cheaper than the keyed Nearline), `ace-dom2-040` and `ace-dom2-042` (Autopilot also met the stem),
  `ace-dom2-018` (the access pattern read two ways), `ace-dom1-015` (the scenario was impossible) and `ace-dom4-011`
  (BigQuery data-read logs are on by default).
- Twelve questions had the answer key on a distractor whose explanation contradicted it ("Correct." on two options):
  `ace-dom1-033`, `ace-dom1-043`, `ace-dom2-005`, `ace-dom2-007`, `ace-dom2-021`, `ace-dom2-043`, `ace-dom2-053`,
  `ace-dom2-057`, `ace-dom3-033`, `ace-dom3-037`, `ace-dom4-006`, `ace-dom5-017`. The options were swapped so each key
  now points at the right answer and the answer-letter spread is unchanged; a test now allows only the key to be
  called correct. Attempts recorded before that fix are repaired once when history is read: the chosen letter for
  those twelve questions is swapped the same way and the attempt re-scored (`Attempt.bank_fixes` records it, so it
  never applies twice).
- **An answer was recorded wrongly in some new attempts.** After that repair shipped, a new attempt that included one
  of the twelve questions had that answer swapped when it was saved, as if it were an old record. New attempts are now
  saved as answered, and affected attempts (finished after the repair shipped) are corrected once when history is read.
- `kb.py add` gave a cross-domain question (one with `also_tests`) an ordinary section id and left it in learning mode.
  It now mints an `ace-x-` id, and a cross-domain question is always certifying-only.
- The timing summary counted unanswered items as misses "answered in under 25 seconds". It now counts wrong answers
  only and states the unanswered ones separately; the results screen shows **Answered wrongly** beside
  **Unanswered** instead of counting unanswered items twice.
- `ace-dom1-025` said accounts were "already provisioned" without saying where. It now says every employee already has
  a Cloud Identity account, which is what makes SAML SSO, not Workforce Identity Federation, the answer.

## [1.1.0] - 2026-11-06

Docker from a clone, a report that tells you what to study and where, and theory beside every practice question.

### Added

- **`bin/start.sh` and `bin/stop.sh`** run the simulator in Docker with your existing history: start merges
  `data/history.json` in, stop copies new attempts and reports back. Running start again restarts it. Both refuse root,
  a busy port and invalid history, ask before losing an exam in progress, and never delete history.
- **A study panel in learning mode**, sliding in on the right: the course's theory for the question, its recall card and
  links to the theory site and the video chapter, then after checking, why the answer is right and each other option wrong.
- **The report after every exam reviews your missed and flagged questions**, two pages each: every option explained,
  then the course's theory for it and links to read it on the site and rewatch it in the
  [course video](https://youtu.be/wXKv62ONQUw). Page 1 lists the sections behind your misses, most first. Choose
  **every question** on the results page for a full review.
- **Run it with Docker:** `docker compose up` from a clone, with no Python needed. It runs as non-root on a read-only
  filesystem, publishes its port to localhost only, and keeps your history in the `ace-state` volume
  ([#3](https://github.com/nirmata78/gcp-ace-simulator/issues/3)). A ready-made image is planned for 1.2.0
  ([#7](https://github.com/nirmata78/gcp-ace-simulator/issues/7)).
- **`ACE_STATE_DIR`** moves your history and reports out of the source tree. Without it, nothing changes.
- **Pinned dependencies:** `pyproject.toml` declares them, and `requirements.lock` and `requirements-dev.lock` pin them with hashes.

### Changed

- **The review report replaces the old score report.** Its first page keeps the score, the sections and the timing.
  `scripts/retrospective.py` builds the same report from history.
- The results page no longer says the browser failed when a report can't open by itself. It points to the download button.
- If your history can't be saved, for example on a full disk, the results page still shows your score and says what went wrong.

### Fixed

- **The app starts without an internet connection.** It no longer shuts down when offline, because it needs no network.
  `ACE_SKIP_NETWORK_CHECK` is still accepted and does nothing. `kb.py add --topic` and `--stem` still stop when offline.

## [1.0.1] - 2026-11-04

The five questions listed as unverified in 1.0.0 (`ace-s3-144` to `ace-s3-148`) have now been checked against the docs
([#2](https://github.com/nirmata78/gcp-ace-simulator/issues/2)). All five answer keys stand. The other known limitations
of 1.0.0 still apply.

### Fixed

- **`ace-s3-147`:** the scenario couldn't happen as written. A plain `age` rule also deletes noncurrent versions, so the
  rule now has `isLive: true`, and the explanation no longer says a separate rule is always needed. Option D no longer
  offers `numNewerVersions`, which wouldn't clear the newest noncurrent version.
- **`ace-s3-144`, `ace-s3-145`, `ace-s3-146`, `ace-s3-148`:** corrected explanations: when automatic restart applies, the
  permission an organization search needs, what `--lifecycle-file` does, and whether Standard is cheaper for short-lived
  data. `ace-s3-148` now links to the worked early-deletion example.
- **Theory:** added how lifecycle rules treat noncurrent versions, and that a stopped VM is listed as `TERMINATED`.

## [1.0.0] - 2026-11-04

First release, built on Google's June 2026 Associate Cloud Engineer exam guide.

### Added

- **Exam simulator:** 50 questions at the guide's 20/30/30/20 weights, 120 minutes, a question palette, deferred
  grading, a Learning mode and a PDF score report by objective. Runs locally.
- **Question bank:** 591 questions, each tied to a section, objective and subtopic of the guide, with all four options
  explained and a link to the docs. Validation rejects anything outside the guide's closed list of 87 subtopics, and
  every one of the 94 guide bullets has at least three questions.
- **Theory course** on [GitHub Pages](https://nirmata78.github.io/gcp-ace-simulator/theory/), covering all 94 bullets,
  with practice scenarios.
- **`scripts/kb.py`** to query, validate and add to the bank, and optional scripts for a retrospective and a recap PDF.
- Tests, CI, contribution guidelines and this release process.

### Known limitations

- **Five questions are unverified:** the answers to `ace-s3-144` to `ace-s3-148` haven't been checked against the docs
  ([#2](https://github.com/nirmata78/gcp-ace-simulator/issues/2)).
- **Provenance:** 104 questions were held back and are under review
  ([#1](https://github.com/nirmata78/gcp-ace-simulator/issues/1)). The bank was compared with one public dump only, so
  an overlap with another source is possible. Please report anything you recognise.
- **Test coverage is uneven:** `src/` is at 90–99%, while `app.py` and the scripts have no direct tests
  ([#3](https://github.com/nirmata78/gcp-ace-simulator/issues/3)).
- **`kb.py add --topic` and `--stem`** haven't been run against the live API with the current default model.
- **The app needs internet at startup** unless `ACE_SKIP_NETWORK_CHECK=1` is set, even though the exam itself runs
  offline ([#3](https://github.com/nirmata78/gcp-ace-simulator/issues/3)).

[Unreleased]: https://github.com/nirmata78/gcp-ace-simulator/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/nirmata78/gcp-ace-simulator/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/nirmata78/gcp-ace-simulator/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/nirmata78/gcp-ace-simulator/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/nirmata78/gcp-ace-simulator/releases/tag/v1.0.0
