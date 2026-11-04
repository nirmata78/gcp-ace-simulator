# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
[RELEASE.md](RELEASE.md) explains what each kind of version bump means here.

## [Unreleased]

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

[Unreleased]: https://github.com/nirmata78/gcp-ace-simulator/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/nirmata78/gcp-ace-simulator/releases/tag/v1.0.0
