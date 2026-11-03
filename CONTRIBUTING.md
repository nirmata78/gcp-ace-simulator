# Contributing

Thanks for helping make this a better way to prepare for the exam.

## What's most useful

- **Wrong answers and stale facts.** Google Cloud renames and changes things constantly. An item whose answer is
  no longer true, with a link to current documentation, is the most valuable report you can make.
- **New questions on thin topics.** Run `python scripts/kb.py blueprint` and look for the bullets with the fewest
  questions. Section 4 (access and security) holds about 12% of the bank against a 20% exam weight.
- **Theory fixes.** Every page on the [site](https://nirmata78.github.io/gcp-ace-simulator/) has a *Suggest a fix*
  link. Pages are plain Markdown in [`theory/`](theory/README.md).
- **Simulator behaviour.** Anything that differs from a real delivery window in a way that changes how you practise.

## The one rule that cannot bend: no exam content

**Never submit a question from the real exam, from memory or otherwise, or one copied or lightly reworded from a
dump, a paid practice test or Google's own sample form.** Candidates sign a confidentiality agreement, and a
question bank built on leaked items would help nobody and could take this project down.

Write from the [exam guide](https://cloud.google.com/learn/certification/guides/cloud-engineer) and the product
documentation: pick a bullet, pick the fact it tests, and invent your own scenario. If you recognise an item in the
bank from one of those sources, please open an issue. It will be removed.

## Adding a question

1. Find the objective and subtopic: `python scripts/kb.py topics --section 3`. The list is closed, so anything the
   guide does not test has nowhere to go. That is deliberate.
2. Write the JSON (format in the [README](README.md#adding-questions)). Every option needs its own rationale, and
   `doc_ref` should link to the page that proves the answer.
3. `python scripts/kb.py add --file newq.json` previews it, checks overlap with the bank and validates it.
4. Sit it once in Learning mode. Then check that `pytest -q` and `python scripts/kb.py check` are clean.

A good item tests a decision, not a spelling. Every wrong option should be something a reasonable person might try,
and should be wrong for a reason you can state. Avoid flag-name and console-label trivia.

**Keep every id stable.** An id is a permanent key used by people's attempt history. New ids are minted for you.

**If you used an LLM** (including `kb.py add --topic`), you are still the author: check every answer against the
documentation before opening the PR. Models are confidently wrong about recently renamed products.

## Editing the theory

The pages in `theory/` are the source. Their callouts use kramdown syntax:

```markdown
{: .trap }
> The thing people get wrong.

{: .trap-title }
> A custom title
>
> The thing people get wrong.
```

Classes: `key` · `trap` · `tip` · `watch` · `note` · `new`. Write cross-references as links to the section anchor,
such as `[§4.4](04-networking.md#s4-4)`, and use `<mark>` sparingly, for about one fact per section. Avoid `{{` and
`{%`: GitHub Pages treats them as Liquid.

You do not need to build the PDF. It is an optional local output; [`theory/README.md`](theory/README.md) explains it.

## Changing the engine

`src/exam_engine.py` imports nothing from Streamlit, so a full exam can be tested without a browser. Add a test
with any behaviour change. `src/blueprint.py` is a transcription of Google's guide: change it only when the guide
changes, and link the new guide in the PR.

## Ground rules

- **Never commit your own attempts.** `data/history.json`, `reports/` and `private/` are gitignored; don't force-add
  them.
- **No real employer data** in scenarios. Use invented companies.
- Keep PRs to one concern, and say which failure the change fixes.
