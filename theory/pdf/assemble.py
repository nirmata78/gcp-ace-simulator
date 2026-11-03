#!/usr/bin/env python3
"""Rebuild the booklet source for the local PDF from the published pages.

The pages in ``theory/*.md`` are the single source of truth. They use kramdown callouts
so they render on GitHub Pages; the PDF pipeline (``ace-theory.lua``) reads pandoc fenced
divs. This script is the one-way bridge:

    theory/0*.md + theory/10-*.md + theory/appendix-*.md + header.md  ->  ACE-Theory-Recap.md

Only needed if you build the PDF yourself (``./build-theory.sh``). The site does not use it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
THEORY = HERE.parent
FRONT = re.compile(r"\A---\n.*?\n---\n\n", re.S)
TOC = re.compile(r"^(# .+)\n\{: \.no_toc \}\n\n1\. TOC\n\{:toc\}\n", re.M)
ANCHOR = re.compile(r'<a id="s[0-9AB]+-\d+"></a>')
XREF = re.compile(r"\[(§[0-9AB]+\.\d+)\]\([^)]*\)")
CALLOUT = re.compile(r"^\{: \.([a-z]+)(-title)? \}$")
CODE_SPAN = re.compile(r"(`+)(?:(?!\1).)*?\1")
SEPARATOR = re.compile(r"^\|[:\- |]+\|$")


def undash(text: str) -> str:
    return text.replace("—", "---").replace("–", "--")


def prose(line: str) -> str:
    """Reverse the typography on one line, leaving code spans alone."""
    if SEPARATOR.match(line):
        return line
    out, pos = [], 0
    for m in CODE_SPAN.finditer(line):
        out.append(undash(line[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(undash(line[pos:]))
    return "".join(out).replace('<mark markdown="span">', "==").replace("</mark>", "==")


def page_to_pandoc(text: str) -> str:
    text = TOC.sub(r"\1\n", FRONT.sub("", text))
    text = ANCHOR.sub("", text)
    text = XREF.sub(r"\1", text)
    lines, out, i, fence = text.split("\n"), [], 0, False
    while i < len(lines):
        line = lines[i]
        m = CALLOUT.match(line) if not fence else None
        if m and m.group(1) == "cmds":
            out.append("::: {.cmds}")
            i += 1
            while i < len(lines) and lines[i].startswith("|"):
                out.append(prose(lines[i]))
                i += 1
            out.append(":::")
            continue
        if m:
            i += 1
            body = []
            while i < len(lines) and lines[i].startswith(">"):
                body.append(lines[i][2:] if lines[i].startswith("> ") else "")
                i += 1
            inner, code = [], False
            for b in body:
                if b.startswith("```"):
                    code = not code
                    inner.append(b)
                else:
                    inner.append(b if code else prose(b))
            if m.group(2):  # a titled callout: first paragraph is the title
                title, inner = inner[0], inner[2:]
                out.append(f'::: {{.{m.group(1)} title="{title}"}}')
            else:
                out.append(f"::: {{.{m.group(1)}}}")
            out += inner
            out.append(":::")
            continue
        if line.startswith("```"):
            fence = not fence
            out.append(line)
        else:
            out.append(line if fence else prose(line))
        i += 1
    return "\n".join(out)


def main() -> int:
    pages = sorted(THEORY.glob("[01]*.md")) + sorted(THEORY.glob("appendix-*.md"))
    if len(pages) != 12:
        print(f"expected 12 pages, found {len(pages)}", file=sys.stderr)
        return 1
    body = "".join(page_to_pandoc(p.read_text()) for p in pages)
    # pandoc would read an unescaped name@domain as the start of a citation.
    body = body.replace("Oracle Database@Google Cloud", "Oracle Database\\@Google Cloud")
    (HERE / "ACE-Theory-Recap.md").write_text((HERE / "header.md").read_text() + body)
    print(f"assembled {len(pages)} pages -> theory/pdf/ACE-Theory-Recap.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
