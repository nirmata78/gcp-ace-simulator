# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
[RELEASE.md](RELEASE.md) explains what each kind of version bump means here.

## [Unreleased]

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

[Unreleased]: https://github.com/nirmata78/gcp-ace-simulator/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/nirmata78/gcp-ace-simulator/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/nirmata78/gcp-ace-simulator/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/nirmata78/gcp-ace-simulator/releases/tag/v1.0.0
