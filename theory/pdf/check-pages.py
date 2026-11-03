#!/usr/bin/env python3
"""check-pages.py --- read the page model back from the built PDF (build-theory.sh gate 9).

Every part opens a page, and every "N.M Part N recall card" starts a page and fits on it: the next part
(or appendix) begins on the very next page. Prints "ok (...)" or the findings; exit 0 / 1.

    ./check-pages.py ACE-Theory-Recap.pdf           the gate
    ./check-pages.py --tails ACE-Theory-Recap.pdf   the parts whose last page holds only a few lines
                                                    (before a recall card or the next part), comma-separated
"""
TAIL_LINES = 12   # a last page with fewer lines of text than this (running head included) is a wasted sheet
import re, subprocess, sys

def pages_of(pdf):
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    n = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    return [subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", pdf, "-"],
                           capture_output=True, text=True).stdout for p in range(1, n + 1)]

def tails(pdf):
    pages = pages_of(pdf)
    out = []
    for i in range(2, len(pages)):
        top = "\n".join([l for l in pages[i].splitlines()[1:] if l.strip()][:3])
        if re.search(r"^\s*(PART \d+|APPENDIX [A-Z])\s*$|Part \d+ recall card", top, re.M):
            prev = pages[i - 1]
            if len([l for l in prev.splitlines() if l.strip()]) < TAIL_LINES:
                m = re.match(r"\s*(PART \d+|APPENDIX [A-Z])", prev)
                if m and m.group(1) not in out: out.append(m.group(1))
    print(",".join(out))
    return 0

def main(pdf):
    pages = pages_of(pdf)
    body = [p.splitlines()[1:] for p in pages]          # line 0 is the running head
    top = ["\n".join([l for l in b if l.strip()][:3]) for b in body]   # the first three lines of text
    opens, cards = [], {}
    for i in range(1, len(pages)):
        if re.search(r"^\s*(PART \d+|APPENDIX [A-Z])\s*$", top[i], re.M):
            opens.append(i)
        for m in re.finditer(r"\d+\.\d+\s+Part (\d+) recall card", "\n".join(body[i])):
            cards.setdefault(int(m.group(1)), i)
    bad = []
    for part, i in sorted(cards.items()):
        if not re.search(r"Part %d recall card" % part, top[i]):
            bad.append(f"Part {part} card does not start page {i + 1}")
        nxt = min([q for q in opens if q > i], default=len(pages))
        if nxt - i > 1:
            bad.append(f"Part {part} card runs {nxt - i} pages (p. {i + 1}-{nxt})")
    print("; ".join(bad) if bad else f"ok ({len(opens)} openers, {len(cards)} cards)")
    return 1 if bad else 0

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--tails":
        sys.exit(tails(args[1] if len(args) > 1 else "ACE-Theory-Recap.pdf"))
    sys.exit(main(args[0] if args else "ACE-Theory-Recap.pdf"))
