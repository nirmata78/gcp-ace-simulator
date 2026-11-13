# Releasing

How this project is versioned and released. It follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
and borrows from Google's published engineering practices: [small changes and code review](https://google.github.io/eng-practices/)
and trunk-based development, testing and release discipline from [Software Engineering at Google](https://abseil.io/resources/swe-book).

## What the version number covers

`VERSION` is the single source of truth. The public API that semver protects is:

1. **The question schema**: the fields and meaning of `data/sections/*.json`
2. **The history format**: an existing `history.json` must keep loading, in `data/` or in `ACE_STATE_DIR`
3. **The `scripts/kb.py` commands**: their names, options and exit codes
4. **How you launch it**: `streamlit run app.py`, `docker compose up`, `bin/start.sh` and `bin/stop.sh` with their
   options, the `ace-state` volume and the documented environment variables

Internal Python modules in `src/` are not public API, so they can change in any release.

| Bump | When | Examples |
|---|---|---|
| **MAJOR** | Something in the list above breaks | History needs a migration you can't skip; a `kb.py` command is removed; a new exam guide replaces the closed list of subtopics |
| **MINOR** | Something is added and nothing breaks | Docker support; new questions; a new theory page; a new `kb.py` command |
| **PATCH** | Something is corrected | A wrong answer key; a replaced or removed question; a stale doc link; a bug fix; a wording fix |

If a release does more than one of these, the largest bump wins.

## Everyday changes

- **`main` is always releasable.** Branches are short-lived, and every change reaches `main` through a pull request.
- **Keep changes small.** One purpose per pull request; a refactor and a behaviour change go in separate ones.
- **Every change gets a review** by someone other than its author. An AI-written change is reviewed by a person or by a
  separate session that didn't write it.
  **Exception for the repository owner:** on the owner's own changes, an AI tool such as Claude Code counts as the
  reviewer and may merge once CI is green, even if it also wrote the change.
- **CI must be green** before merging: `pytest -q`, `python scripts/kb.py check`, `python scripts/kb.py lint`,
  `python scripts/kb.py blueprint --min 3 --strict` and, when the image's inputs change, `pytest tests/container`.
- **Bug fixes and new behaviour come with a test.** If CI doesn't check it, it can break unnoticed.
- **Treat coverage as a signal, not a goal.** Use it to find untested code, and don't chase a number
  ([Google's guidance](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html)).
- **Add a line to `CHANGELOG.md`** under `Unreleased` for anything a user would notice.
- **Question changes follow [the question standard](docs/question-standard.md)**: a new question gets a new id
  (`kb.py add` mints it, `ace-x-NNN` for a cross-domain one), a removed id goes to `data/retired.json` and is never
  reused, and `kb.py lint` must report no errors.

## Cutting a release

Start from an up-to-date `main` with CI green.

1. **Pick the version** from the table above.
2. **Set the version** in a pull request: `VERSION`, and `Unreleased` in `CHANGELOG.md` moved to a new dated heading
   with its compare link at the bottom. It can be the last commit of the feature pull request, or a pull request of
   its own. Merge it once CI passes. A test fails if the two disagree.
3. **Tag the merge commit and publish:**

   ```bash
   git switch main && git pull
   V="$(cat VERSION)"
   git tag -a "v$V" -m "v$V"
   git push origin "v$V"
   awk -v v="$V" 'index($0,"## ["v"]")==1{f=1;next} /^## \[/{f=0} f' CHANGELOG.md > /tmp/notes.md
   gh release create "v$V" --title "v$V" --notes-file /tmp/notes.md --verify-tag
   ```

4. **Check it:** clone the tag somewhere fresh, run the tests and sit a short exam.
5. **A version is released only when its tag and GitHub release exist.** A dated heading in the changelog without a
   tag is not a release: tag the commit that set that version and publish it, as was done late for 1.1.0.

## If a release is bad

Fix forward with a new PATCH release. **Never move or delete a released tag**: people may already depend on it. If a
release must not be used, say so at the top of its release notes and point to the fix.

**Exception for content:** if someone reports text they own or real exam content, remove it from `main` straight away
and release a PATCH, without waiting for anything else.

Only the latest release is supported.

## Roadmap

| Version | What | Tracked in |
|---|---|---|
| **1.0.0** | First release: the simulator, the question bank and the theory course | [Changelog](CHANGELOG.md) |
| 1.0.1 | Corrections from verifying the five newest questions | [#2](https://github.com/nirmata78/gcp-ace-simulator/issues/2) |
| **1.1.0** | Docker from a clone with `bin/start.sh`, the review report with theory and video links, the study panel | [Changelog](CHANGELOG.md) |
| **1.2.0** | The reviewed bank (question standard, the 104 settled), multiple-select and cross-domain questions, draws that avoid seen questions, the in-app score report | [#1](https://github.com/nirmata78/gcp-ace-simulator/issues/1), [Changelog](CHANGELOG.md) |
| **1.3.0** | The bank grown to 927 by `/expand` (quoted evidence, a blind solve), no key on a Preview feature, five network blueprints in the theory | [#11](https://github.com/nirmata78/gcp-ace-simulator/pull/11), [Changelog](CHANGELOG.md) |
| 1.4.0 | A published image anyone can pull in one line, and the rest of the tech debt | [#7](https://github.com/nirmata78/gcp-ace-simulator/issues/7), [#3](https://github.com/nirmata78/gcp-ace-simulator/issues/3), [plan](docs/plans/v1.1.0-docker.yaml) |
