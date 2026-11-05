# CLAUDE.md

A local practice simulator for the Google Cloud Associate Cloud Engineer exam, plus its theory site. Read
`CONTRIBUTING.md` first: its **no exam content** rule binds you too. Never write a question from a remembered
exam item, a dump or a practice test.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
streamlit run app.py                           # the simulator
docker compose up                              # the simulator in a container, without Python
pytest -q                                      # must stay green
pytest tests/container                         # the container, in a real browser; needs Docker and Playwright
python scripts/kb.py check                     # bank integrity
python scripts/kb.py blueprint --min 3 --strict  # every guide bullet has 3+ questions
python scripts/kb.py add --file newq.json      # add questions through validation
```

After changing dependencies in `pyproject.toml`, regenerate both lock files with the command at the top of each.

## Releases

`RELEASE.md` is the process and `VERSION` the source of truth, with semantic versioning. Add a line to `CHANGELOG.md` under
`Unreleased` for anything a user would notice. Open work is in the GitHub issues; `docs/plans/` holds machine-readable plans.

## Map

- `src/blueprint.py`: the exam guide as data, and the closed list of subtopics. A question must use one.
- `src/models.py`: schemas, bank persistence and the uniqueness limits. `src/exam_engine.py`: sampling, timer,
  scoring; no Streamlit imports. `src/pdf_generator.py`: score report. `app.py`: the Streamlit shell. `src/paths.py`: the only place that
  says where history and reports go; `ACE_STATE_DIR` moves them.
- `data/sections/*.json`: **the bank, source of truth**. `data/register.json` is generated: run
  `kb.py reindex`, never edit it.
- `theory/*.md`: **the theory, source of truth**, published by GitHub Pages (just-the-docs; config in
  `_config.yml`).
- `theory/pdf/`: optional local PDF build. `assemble.py` generates its input from the pages; do not edit the output.
- `theory/video/`: sources of the narrated course. The build needs a private slide kit that is not in this repo.

## Rules

- Write questions in the voice of the bank: a scenario, one decision, four plausible options, a rationale for each,
  and a `doc_ref` you have actually checked.
- Google Cloud products get renamed. Verify against current documentation rather than memory, and mark volatile
  facts *verify* in the theory.
- If you add a fact to a question that the theory does not teach, add it to the theory page too.
- `data/history.json`, `reports/`, `private/` and `scripts/retro_content.py` hold someone's personal attempts. They
  are gitignored. Never commit them or quote them into a tracked file. `.dockerignore` denies everything by default, so
  add to its allow list only what the image needs.
