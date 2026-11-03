#!/usr/bin/env python3
"""All sample questions from src/ → ACE-Video-Questions.md: a printable companion, generated from the same source as the slides."""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from course import Chapter, SRC
out = ["# GCP ACE video course: all sample questions\n", "Generated from `src/` by `export_questions.py`. Original questions, not taken from the exam.\n"]
for f in sorted(SRC.glob("ch*.txt")):
    c = Chapter(f.stem[2:]); c.parse(f.read_text(encoding="utf-8"))
    out.append(f"\n## Part {c.n}: {c.title}\n")
    for i, (stem, opts, ans, why) in enumerate(c.questions, 1):
        out.append(f"\n**Q{c.n}.{i}.** {stem}\n")
        out += [f"- **{k}.** {v}" for k, v in opts.items()]
        out.append(f"\n**Answer: {', '.join(ans)}.** " + " ".join(f"*{k}:* {why.get(k,'')}" for k in opts) + "\n")
pathlib.Path(__file__).with_name("ACE-Video-Questions.md").write_text("\n".join(out), encoding="utf-8")
print("questions written")
